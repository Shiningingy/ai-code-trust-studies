import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import ClauseRule  # noqa: E402
from facts_basic import F  # noqa: E402

GROUP = r"(?:the )?(?P<group>[a-z]+ (?:club|group|circle|society))"


class Attends(ClauseRule):
    name = "attends"
    solves = ("a person attends a group; 'only in the past' / 'in the past' / frequency words are kept as qualifiers, "
              "so a lapsed membership is distinguishable from a current one")
    added_by = "learning"
    pred = r"(?:currently )?attends? %s" % GROUP
    examples = [("Leah Avery attends the chess club.",
                 [{"subject": "Leah Avery", "relation": "attends", "object": "chess club", "qualifiers": []}]),
                ("T. Patel attends the walking group only in the past.",
                 [{"subject": "Talia Patel", "relation": "attends", "object": "walking group", "qualifiers": ["only in the past", "past"]}])]

    def build(self, s, g):
        return [F(s, "attends", g["group"])]


class UsedToAttend(ClauseRule):
    name = "used_to_attend"
    solves = ("a person used to attend / previously attended / no longer attends a group (a former member); "
              "qualifiers used to, in the past, no longer")
    added_by = "learning"
    pred = (r"(?:(?:only )?(?P<used>used to) attends?|(?P<prev>previously|formerly|once) attended|attended|(?P<nl>no longer) attends?|"
            r"used to be a member of) %s" % GROUP)
    examples = [("Nadia Tran used to attend the radio society.",
                 [{"subject": "Nadia Tran", "relation": "attends", "object": "radio society", "qualifiers": ["used to", "past"]}]),
                ("Nadia Tran used to attend the radio society, but no longer does.",
                 [{"subject": "Nadia Tran", "relation": "attends", "object": "radio society", "qualifiers": ["used to", "no longer", "past"]}]),
                ("Nadia Tran no longer attends the radio society.",
                 [{"subject": "Nadia Tran", "relation": "attends", "object": "radio society", "qualifiers": ["no longer", "past"]}])]

    def build(self, s, g):
        q = [x for x in (g["used"] or ("used to" if not (g["prev"] or g["nl"]) else ""), g["prev"], g["nl"]) if x]
        return [F(s, "attends", g["group"], q)]
