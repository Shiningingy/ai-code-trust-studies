import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import fact, person, org, NAME, ORG, LEAD_NEUTRAL, LEAD_REPORTED  # noqa: E402
from common_stmt import Stmt  # noqa: E402
from gram import Rule  # noqa: E402

_PAST_ALT = (r"only in the past,? a membership that has since lapsed|only in the past|in the past now|in the past|previously|"
             r"some time ago in the past|which was in the past|that is in the past now|that is in the past|that was in the past|"
             r"that is no longer the case|does not attend now|(?:he |she |they |I )?no longer (?:do|does)|"
             r"a membership that has since lapsed")
# one or more past markers, optionally followed by 'and that is a current commitment'
PAST = (r"(?:\s*,?\s*(?:but\s+)?(?:also\s+)?(?P<past>(?:%s)(?:\s*,?\s*(?:but\s+)?(?:%s))*))" % (_PAST_ALT, _PAST_ALT))


def obj(text):
    t = re.sub(r"\s+", " ", text.strip().lower())
    return re.sub(r"^(?:the|a|an) ", "", t)


class Owns(Stmt):
    name = "owns"
    solves = "'X owns a camera' (also 'owns garden tools', 'owns a garden tools set'): possession of an item"
    added_by = "learning"
    pred = r"(?:owns?|has|have)\s+(?:an?\s+)?(?P<obj>garden tools|sewing kit|camera|telescope|guitar|[a-z]+(?:\s+[a-z]+)??)(?P<set>\s+(?:set|kit))?"
    examples = [("Ben Ito owns a garden tools.", [fact("Ben Ito", "owns", "garden tools")]),
                ("B. Ito owns a camera.", [fact("Ben Ito", "owns", "camera")])]

    def facts(self, s, m):
        return [("owns", obj(m.group("obj")), [])]


class Recommended(Stmt):
    name = "recommended"
    solves = "'X recommended <book>' with optional 'to the group' / 'for the reading list'"
    added_by = "learning"
    pred = r"(?:recommended|suggested|recommend|recommends)\s+(?P<obj>[a-z]+(?:\s+[a-z]+){0,2}?)(?P<to>\s+to the group|\s+for the reading list)?"
    examples = [("Hana Ortiz recommended Quiet Machines.", [fact("Hana Ortiz", "recommended", "quiet machines")])]

    def facts(self, s, m):
        return [("recommended", obj(m.group("obj")), [m.group("to").strip()] if m.group("to") else [])]


class Discussed(Stmt):
    name = "discussed"
    solves = "'X discussed <topic>' where the topic is a book, group or place, with optional 'activities'/'trends'"
    added_by = "learning"
    pred = r"discuss(?:ed|es)?\s+(?P<obj>[a-z]+(?:\s+[a-z]+){0,3}?)(?P<asp>\s+activities|\s+trends)?"
    examples = [("Priya Haddad discussed chess club.", [fact("Priya Haddad", "discussed", "chess club")]),
                ("Priya Haddad discussed the market trends.", [fact("Priya Haddad", "discussed", "market", ["trends"])])]

    def facts(self, s, m):
        return [("discussed", obj(m.group("obj")), [m.group("asp").strip()] if m.group("asp") else [])]


class Attends(Stmt):
    name = "attends"
    solves = ("membership of a group: 'attends the G', with past markers ('only in the past', 'used to attend', "
              "'previously attended', 'but no longer does') kept as qualifier 'past'")
    added_by = "learning"
    pred = (r"(?:(?P<used>used to\s+)?attend(?:s|ed)?\s+(?:the\s+)?(?P<obj>[a-z]+\s+[a-z]+)|"
            r"(?P<used3>used to be|was)\s+a member of\s+(?:the\s+)?(?P<obj3>[a-z]+\s+[a-z]+)|"
            r"(?:previously|formerly) attended\s+(?:the\s+)?(?P<obj2>[a-z]+\s+[a-z]+))" + PAST + "?"
            r"(?P<cur>\s*,?\s*and that is a current commitment)?")
    examples = [("T. Patel attends the walking group only in the past.",
                 [fact("Talia Patel", "attends", "walking group", ["past"])]),
                ("Farah Tran used to attend the chess club, but no longer does.",
                 [fact("Farah Tran", "attends", "chess club", ["past"])]),
                ("Omar Tran attends the chess club.", [fact("Omar Tran", "attends", "chess club")])]

    def facts(self, s, m):
        past = m.group("past") or m.group("used") or m.group("used3") or re.search(r"(?:previously|formerly) attended", m.string, re.I)
        return [("attends", obj(m.group("obj") or m.group("obj2") or m.group("obj3")),
                 (["past"] if past else []) + (["current"] if m.group("cur") else []))]


PLACES = r"(?:market|museum|library|sports hall|riverside park)"


class Visited(Stmt):
    name = "visited"
    solves = "'X visited the P' with optional time words 'some time ago', 'in the past', 'previously' (qualifier 'past')"
    added_by = "learning"
    pred = r"(?P<pre>previously\s+)?(?:had\s+)?visit(?:ed|s)?\s+the\s+(?P<obj>[a-z]+(?:\s+[a-z]+)?)(?:\s+(?P<t>some time ago|in the past|previously))?" + \
           r"(?:\s*,?\s*(?P<t2>in the past|which was in the past|which is in the past))?"
    examples = [("Kofi Silva visited the market some time ago.", [fact("Kofi Silva", "visited", "market", ["past"])]),
                ("Kofi Silva visited the market.", [fact("Kofi Silva", "visited", "market")])]

    def facts(self, s, m):
        return [("visited", obj(m.group("obj")), ["past"] if (m.group("t") or m.group("t2") or m.group("pre")) else [])]


class Helped(Stmt):
    name = "helped"
    solves = "'X helped with registration/setup/cleanup at P'; relation helped_with_<task>, object the place"
    added_by = "learning"
    pred = r"(?:helped|assisted|help|helps)\s+with\s+(?P<task>registration|setup|cleanup)\s+at\s+the\s+(?P<obj>[a-z]+(?:\s+[a-z]+)?)"
    examples = [("K. Khan helped with setup at the library.",
                 [fact("Kofi Khan", "helped_with_setup", "library")])]

    def facts(self, s, m):
        return [("helped_with_" + m.group("task").lower(), obj(m.group("obj")) if m.group("obj") else "", [])]


class Volunteered(Stmt):
    name = "volunteered"
    solves = "'X volunteered at <event-id> during this-year|last-year'; the period is a qualifier"
    added_by = "learning"
    pred = r"volunteer(?:ed|s)?\s+at\s+(?P<obj>(?:old-)?event-P-\d+(?:-\d+)?)\s+during\s+(?P<per>this[- ]year|last[- ]year)"
    examples = [("B. Novak volunteered at event-P-122-1 during this-year.",
                 [fact("Ben Novak", "volunteered_at", "event-P-122-1", ["this-year"])])]

    def facts(self, s, m):
        return [("volunteered_at", m.group("obj"), [m.group("per").lower().replace(" ", "-")])]


class WorksFor(Stmt):
    name = "works_for"
    solves = "'X (currently) works for Org N'"
    added_by = "learning"
    pred = r"(?P<cur>currently\s+)?works? for\s+(?P<obj>%s)" % ORG
    examples = [("h. Patel currently works for Org 004.",
                 [fact("Hana Patel", "works_for", "Org 004", ["currently"])])]

    def facts(self, s, m):
        return [("works_for", org(m.group("obj")), ["currently"] if m.group("cur") else [])]


class OrgBase(Rule):
    name = "org_based_in"
    solves = "'Org N is based in <city>' (cities such as St. John's keep their dot)"
    added_by = "learning"
    examples = [("Organization 009 is based in Vancouver.", [fact("Org 009", "based_in", "Vancouver")])]
    _rx = re.compile(r"\"?(?:(?:%s|%s)[,\s]\s*)?(?P<o>%s)\s+is based in\s+(?P<c>[A-Za-z.' ]+?)[.\"]*" % (LEAD_NEUTRAL, LEAD_REPORTED, ORG), re.I)

    def parse(self, clause):
        m = self._rx.fullmatch(clause.strip())
        if not m:
            return None
        return [fact(org(m.group("o")), "based_in", m.group("c").strip().title().replace("'S", "'s"))]
