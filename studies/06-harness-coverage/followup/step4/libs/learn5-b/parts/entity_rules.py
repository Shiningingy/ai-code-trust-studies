"""Rules for clauses about identifiers and organizations: the roster and 'Org N is based in C'."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import NAME, ORG, PID, canon_name, canon_org, canon_pid, fact  # noqa: E402
from gram import PatternRule  # noqa: E402


class Roster(PatternRule):
    name = "roster_identifier"
    solves = ("roster line giving a person's identifier and the familiar (short) names they are also written as; "
              "this is the only place that links written names to P-ids")
    added_by = "learning"
    pattern = (r"[Tt]he community roster (?:records|lists) (?P<n>%s) under identifier (?P<id>%s)"
               r"(?: and also uses the familiar names? (?P<al>%s(?:(?:,| and|, and) %s)*))?\.?" % (NAME, PID, NAME, NAME))
    examples = [
        ("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed.",
         [fact("Nadia Reed", "has_id", "P-114"), fact("Nadia Reed", "alias", "N. Reed")]),
        ("the community roster records Nadia Reed under identifier P-114",
         [fact("Nadia Reed", "has_id", "P-114")]),
    ]

    def build(self, g):
        n = canon_name(g["n"])
        out = [fact(n, "has_id", canon_pid(g["id"]))]
        for a in re.findall(NAME, g["al"]):
            out.append(fact(n, "alias", canon_name(a)))
        return out


class OrgBase(PatternRule):
    name = "org_based_in"
    solves = "an organization is based in a city ('Org 007 is based in Halifax'); the object is the city as written"
    added_by = "learning"
    pattern = r"(?P<o>%s) is based in (?P<c>[A-Z][A-Za-z.' ]*[A-Za-z'])\.?" % ORG
    examples = [("Organization 031 is based in Halifax.", [fact("Org 031", "based_in", "Halifax")]),
                ("Org 013 is based in St. John's", [fact("Org 013", "based_in", "St. John's")])]

    def build(self, g):
        return [fact(canon_org(g["o"]), "based_in", g["c"].strip())]
