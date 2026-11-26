import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram import Rule

from common import ORG, PAST_TAIL, Pred, analyze, canon_org, v


class WorksFor(Rule):
    name = "works_for"
    solves = ("a person works for an organization: 'N currently works for Org 014', 'N works for organization 025', "
              "'I work for Org 014'; object normalised to 'Org NNN'; 'used to work for' gives qualifier past")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+)?(?:currently\s+|still\s+|now\s+)?%s\s+(?:for|at)\s+%s" % (v("work"), ORG),
             lambda m: ("works_for", canon_org(m["orgnum"]), []), 0),
        Pred(r"(?:used to work|previously worked|formerly worked|worked)\s+(?:for|at)\s+%s%s" % (ORG, PAST_TAIL),
             lambda m: ("works_for", canon_org(m["orgnum"]), ["past"]), 0),
        Pred(r"no longer %s\s+(?:for|at)\s+%s" % (v("work"), ORG),
             lambda m: ("works_for", canon_org(m["orgnum"]), ["past"]), 0),
    ]
    examples = [
        ("Quinn Silva currently works for Organization 018",
         [{"subject": "Quinn Silva", "relation": "works_for", "object": "Org 018", "qualifiers": []}]),
        ('Talia Tran said, “I work for Org 014',
         [{"subject": "Talia Tran", "relation": "works_for", "object": "Org 014", "qualifiers": ["self_reported"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class WorksShift(Rule):
    name = "works_shift"
    solves = ("a person works the night or day shift: 'N works the night shift' (current), 'N works the night shift "
              "in a former role' / 'used to work the night shift' / 'worked ...' (qualifier past); object night|day")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+)?(?:currently\s+|still\s+|now\s+)?%s\s+(?:the|a|on the)\s+(?P<s>night|day|evening|morning)"
             r"\s+shifts?%s" % (v("work"), PAST_TAIL),
             lambda m: ("works_shift", m["s"].lower(), ["past"] if m["past_tail"] else []), 0),
        Pred(r"(?:used to work|previously worked|formerly worked|worked)\s+(?:the|a|on the)\s+"
             r"(?P<s>night|day|evening|morning)\s+shifts?%s" % PAST_TAIL,
             lambda m: ("works_shift", m["s"].lower(), ["past"]), 0),
        Pred(r"no longer %s\s+(?:the|a|on the)\s+(?P<s>night|day|evening|morning)\s+shifts?" % v("work"),
             lambda m: ("works_shift", m["s"].lower(), ["past"]), 0),
    ]
    examples = [
        ("Quinn Novak works the night shift, so we adjusted our schedule accordingly",
         [{"subject": "Quinn Novak", "relation": "works_shift", "object": "night", "qualifiers": []}]),
        ("Talia Silva works the night shift in a former role",
         [{"subject": "Talia Silva", "relation": "works_shift", "object": "night", "qualifiers": ["past"]}]),
        ("Mateo Foster works the night shift in a former role, and Amina Foster owns a camera", None),
        ("R. Chen used to work the night shift in a former role",
         [{"subject": "R. Chen", "relation": "works_shift", "object": "night", "qualifiers": ["past"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class OrgBasedIn(Rule):
    name = "org_based_in"
    solves = ("an organization is based in a city: 'Organization 031 is based in Halifax', 'org 013 is based in St. "
              "John's'; subject 'Org NNN', object the city as written")
    added_by = "learning"
    preds = [
        Pred(r"(?:is|was)\s+(?:currently\s+)?(?:based|located|headquartered)\s+in\s+"
             r"(?P<city>St\.?\s+[A-Z][\w'’]+|[A-Z][\w'’-]*(?:\s+[A-Z][\w'’-]*)*)",
             lambda m: ("based_in", re.sub(r"\s+", " ", m["city"].replace("’", "'")), []), 3),
    ]
    examples = [
        ("Organization 031 is based in Halifax",
         [{"subject": "Org 031", "relation": "based_in", "object": "Halifax", "qualifiers": []}]),
        ("Org 013 is based in St. John's",
         [{"subject": "Org 013", "relation": "based_in", "object": "St. John's", "qualifiers": []}]),
        ("The same account also says that org 029 is based in Vancouver",
         [{"subject": "Org 029", "relation": "based_in", "object": "Vancouver", "qualifiers": ["reported"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "org", self.preds)
