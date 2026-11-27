import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram import Rule

from common import PAST_TAIL, Pred, analyze, clean, slot, v


def _item(s):
    """'garden tools set' and 'a set of garden tools' name the same item as 'garden tools'."""
    return re.sub(r"^set of |\s+set$", "", clean(s))


def _past(m, *names):
    return any(m.groupdict().get(n) for n in names)


class Owns(Rule):
    name = "owns"
    solves = ("a person owns an item ('N owns a camera', 'I own a guitar', 'N has garden tools', 'N keeps a set of "
              "garden tools in the shed'), also as a past ownership ('used to own', qualifier past)")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+|still\s+)?(?:%s|(?:has|have)(?!\s+(?:since|been|already|never|always|no|not|to|a\s+habit)\b))\s+%s"
             % (v("own"), slot("obj")),
             lambda m: ("owns", _item(m["obj"]), []), 0),
        Pred(r"(?:used to own|previously owned|owned)\s+%s%s" % (slot("obj"), PAST_TAIL),
             lambda m: ("owns", _item(m["obj"]), ["past"]), 0),
        Pred(r"no longer %s\s+%s" % (v("own"), slot("obj")), lambda m: ("owns", _item(m["obj"]), ["past"]), 0),
        # keeping an item is owning it: "keeps a set of garden tools in the shed", "I keep my garden tools"
        Pred(r"(?:also\s+)?(?:mentioned\s+)?(?:keeps|keep|keeping)\s+(?:my\s+|his\s+|her\s+|their\s+|a\s+set\s+of\s+)?%s"
             % slot("obj"), lambda m: ("owns", _item(m["obj"]), []), 0),
    ]
    examples = [
        ("B. Ito owns a garden tools",
         [{"subject": "B. Ito", "relation": "owns", "object": "garden tools", "qualifiers": []}]),
        ("Mateo Foster owns a telescope, which he often brings to our outdoor events",
         [{"subject": "Mateo Foster", "relation": "owns", "object": "telescope", "qualifiers": []}]),
        ("D. Evans keeps a set of garden tools in the shed",
         [{"subject": "D. Evans", "relation": "owns", "object": "garden tools", "qualifiers": []}]),
        ("S. Gupta owns a garden tools set",
         [{"subject": "S. Gupta", "relation": "owns", "object": "garden tools", "qualifiers": []}]),
        ('P. Khan said, "I own a sewing kit',
         [{"subject": "P. Khan", "relation": "owns", "object": "sewing kit", "qualifiers": ["self_reported"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class Recommended(Rule):
    name = "recommended"
    solves = "a person recommended a book or album ('N recommended Atlas of Clouds', 'I recommended ...')"
    added_by = "learning"
    preds = [Pred(r"(?:also\s+)?(?:recommended|recommends|recommend|suggested)\s+%s" % slot("obj", article=False),
                  lambda m: ("recommended", clean(m["obj"]), []), 0)]
    examples = [
        ("Hana Ortiz recommended Quiet Machines",
         [{"subject": "Hana Ortiz", "relation": "recommended", "object": "quiet machines", "qualifiers": []}]),
        ("In a separate update, elena Jones recommended the long orchard to the group",
         [{"subject": "Elena Jones", "relation": "recommended", "object": "long orchard", "qualifiers": []}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class Discussed(Rule):
    name = "discussed"
    solves = ("a person discussed a topic (a place, a group or a book): 'N discussed market', 'N mentioned quiet "
              "machines', 'N discussed the garden circle plans'; the topic is kept as written, lower case")
    added_by = "learning"
    preds = [Pred(r"(?:also\s+)?(?:discussed|discusses|discuss|mentioned|talked about|spoke about)\s+"
                  r"(?!(?:that|he|she|they|I|how|what|keeping|having|being)\b)%s" % slot("obj"),
                  lambda m: ("discussed", clean(m["obj"]), []), 0)]
    examples = [
        ("Priya Haddad discussed chess club",
         [{"subject": "Priya Haddad", "relation": "discussed", "object": "chess club", "qualifiers": []}]),
        ("C. Silva discussed Atlas of Clouds, a book that has been generating a lot of interest",
         [{"subject": "C. Silva", "relation": "discussed", "object": "atlas of clouds", "qualifiers": []}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class AttendsGroup(Rule):
    name = "attends_group"
    solves = ("a person attends a club or group now ('N attends the chess club') or only in the past ('attends the "
              "radio society only in the past', 'used to attend ..., but no longer does', 'previously attended')")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+)?(?P<only>only\s+)?%s\s+%s(?P<ago>\s+only in the past|\s+in the past)?%s"
             % (v("attend"), slot("obj"), PAST_TAIL),
             lambda m: ("attends", clean(m["obj"]), ["past"] if _past(m, "ago", "past_tail") else []), 0),
        Pred(r"(?:only\s+)?(?:used to attend|previously attended|attended|formerly attended)\s+%s"
             r"(?:\s+only in the past|\s+in the past)?%s" % (slot("obj"), PAST_TAIL),
             lambda m: ("attends", clean(m["obj"]), ["past"]), 0),
        Pred(r"no longer %s\s+%s" % (v("attend"), slot("obj")), lambda m: ("attends", clean(m["obj"]), ["past"]), 0),
        Pred(r"(?:also\s+)?(?P<was>(?:used to be|was|were|is no longer|are no longer|am no longer|"
             r"previously was|was previously)|%s)\s+(?:a\s+|an\s+)?(?:active\s+)?member\s+of\s+%s"
             r"(?:\s+in the past)?%s" % (v("is"), slot("obj"), PAST_TAIL),
             lambda m: ("attends", clean(m["obj"]), ["past"] if re.match(r"used|was|were|previously|.*no longer",
                                                                         m["was"], re.I) or m["past_tail"] else []), 0),
    ]
    examples = [
        ("Samir Ito attends the history group",
         [{"subject": "Samir Ito", "relation": "attends", "object": "history group", "qualifiers": []}]),
        ("T. Patel attends the walking group only in the past",
         [{"subject": "T. Patel", "relation": "attends", "object": "walking group", "qualifiers": ["past"]}]),
        ("g. gupta used to be a member of the history group",
         [{"subject": "G. Gupta", "relation": "attends", "object": "history group", "qualifiers": ["past"]}]),
        ("O. Foster used to attend the chess club, but no longer does",
         [{"subject": "O. Foster", "relation": "attends", "object": "chess club", "qualifiers": ["past"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class Visited(Rule):
    name = "visited"
    solves = ("a person visited a place ('N visited the market'), with its time kept: 'some time ago', 'in the "
              "past' / 'previously' (qualifier past)")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+)?(?P<prev>previously\s+)?(?:visited|went to|visit)\s+%s(?P<ago>\s+some time ago)?"
             r"(?P<past>\s+in the past|\s+previously)?" % slot("obj"),
             lambda m: ("visited", clean(m["obj"]),
                        (["some time ago"] if m["ago"] else []) + (["past"] if m["prev"] or m["past"] else [])), 0,
             past_ok=True),
    ]
    examples = [
        ("E. Patel visited the market some time ago",
         [{"subject": "E. Patel", "relation": "visited", "object": "market", "qualifiers": ["some time ago"]}]),
        ("P. Khan visited the museum previously",
         [{"subject": "P. Khan", "relation": "visited", "object": "museum", "qualifiers": ["past"]}]),
        ("S. Mensah visited the market some time ago, a trip he no longer makes",
         [{"subject": "S. Mensah", "relation": "visited", "object": "market", "qualifiers": ["some time ago"]}]),
        ("P. Khan and G. Ito both visited the market previously",
         [{"subject": "P. Khan", "relation": "visited", "object": "market", "qualifiers": ["past"]},
          {"subject": "G. Ito", "relation": "visited", "object": "market", "qualifiers": ["past"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class Helped(Rule):
    name = "helped"
    solves = ("a person helped with a task (setup, registration, cleanup) at a place: relation helped_with_<task>, "
              "object the place ('' when no place is given)")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+)?(?:helped|helps|help|assisted|assists)\s+(?:out\s+)?with\s+(?:the\s+)?(?P<task>set-?up|registration|clean-?up)"
             r"(?:\s+at\s+%s)?" % slot("obj"),
             lambda m: ("helped_with_" + m["task"].lower().replace("-", ""), clean(m["obj"] or ""), []), 0),
    ]
    examples = [
        ("K. Khan helped with setup at the library",
         [{"subject": "K. Khan", "relation": "helped_with_setup", "object": "library", "qualifiers": []}]),
        ("G. Gupta helped with setup at the sports hall, which was a key task",
         [{"subject": "G. Gupta", "relation": "helped_with_setup", "object": "sports hall", "qualifiers": []}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class Volunteered(Rule):
    name = "volunteered"
    solves = ("a person volunteered at an event during a year: 'N volunteered at event-P-139-0 during this-year' "
              "(object the event id, qualifier 'during this-year' / 'during last-year')")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+)?(?:volunteered|volunteers|volunteer)\s+at\s+(?P<ev>(?:old-)?event-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)"
             r"(?:\s+during\s+(?:the\s+)?(?P<yr>this[- ]year|last[- ]year|next[- ]year|\d{4}))?",
             lambda m: ("volunteered_at", re.sub(r"(?i)event-p-", "event-P-", m["ev"]),
                        ["during " + m["yr"].lower().replace(" ", "-")] if m["yr"] else []), 0),
    ]
    examples = [
        ("S. Mensah volunteered at event-P-139-0 during this-year",
         [{"subject": "S. Mensah", "relation": "volunteered_at", "object": "event-P-139-0",
           "qualifiers": ["during this-year"]}]),
        ("Omar Bennett volunteered at old-event-P-075 during last-year",
         [{"subject": "Omar Bennett", "relation": "volunteered_at", "object": "old-event-P-075",
           "qualifiers": ["during last-year"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)
