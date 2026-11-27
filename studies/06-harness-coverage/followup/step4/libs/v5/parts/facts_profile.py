import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import ClauseRule, NAME, W, canon_name, v  # noqa: E402
from facts_basic import F  # noqa: E402


class Roster(ClauseRule):
    name = "roster"
    solves = ("'the community roster records NAME under identifier P-nnn and also uses the familiar names ALIAS': "
              "joins a person's full name to the person id and lists the alias spellings")
    added_by = "learning"
    subject = "roster"
    pred = (r"(?:records|lists) (?P<name>%s|me) under identifier (?P<pid>P-\d+)"
            r"(?: and also uses the familiar names? (?P<alias>%s(?:(?:,| and) %s)*))?" % (NAME, NAME, NAME))
    examples = [("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed.",
                 [{"subject": "Nadia Reed", "relation": "has_id", "object": "P-114", "qualifiers": []},
                  {"subject": "Nadia Reed", "relation": "also_known_as", "object": "N. Reed", "qualifiers": []}])]

    def build(self, s, g):
        import re
        n = s if g["name"] == "me" else canon_name(g["name"])
        out = [F(n, "has_id", g["pid"])]
        for a in re.findall(NAME, g["alias"] or ""):
            out.append(F(n, "also_known_as", a[0].upper() + a[1:]))
        return out


class WorksFor(ClauseRule):
    name = "works_for"
    solves = "a person works for an organisation (Org 030 / Organization 030 -> 'Organization 030'); 'currently' kept as qualifier"
    added_by = "learning"
    pred = r"(?P<cur>currently )?(?:works|work|worked) for (?P<org>[Oo]rg(?:anization)? \d+)"
    examples = [("B. Mensah currently works for Org 030.",
                 [{"subject": "Ben Mensah", "relation": "works_for", "object": "Organization 030", "qualifiers": ["currently"]}])]

    def build(self, s, g):
        import re
        return [F(s, "works_for", "Organization " + re.search(r"\d+", g["org"]).group(), ["currently"] if g["cur"] else [])]


class OrgBasedIn(ClauseRule):
    name = "org_based_in"
    solves = "an organisation is based in a city (e.g. St. John's); city is the object"
    added_by = "learning"
    subject = "org"
    pred = r"is based in (?P<city>St\. [A-Z][a-z']+|[A-Z][a-z]+(?: [A-Z][a-z]+)?)"
    examples = [("Org 003 is based in St. John's.",
                 [{"subject": "Organization 003", "relation": "based_in", "object": "St. John's", "qualifiers": []}])]

    def build(self, s, g):
        return [F(s, "based_in", g["city"])]


class Shift(ClauseRule):
    name = "works_shift"
    solves = "a person works the day or night shift; 'in a former role' / 'used to' mark a past shift (qualifiers kept)"
    added_by = "learning"
    pred = r"(?P<used>used to )?(?:works?|worked) the (?P<shift>day|night|evening|morning) shift(?P<former> in a former role)?"
    examples = [("Talia Silva works the night shift in a former role.",
                 [{"subject": "Talia Silva", "relation": "works_shift", "object": "night", "qualifiers": ["in a former role", "past"]}]),
                ("Samir Laurent works the day shift.",
                 [{"subject": "Samir Laurent", "relation": "works_shift", "object": "day", "qualifiers": []}])]

    def build(self, s, g):
        q = (["used to"] if g["used"] else []) + (["in a former role"] if g["former"] else [])
        return [F(s, "works_shift", g["shift"], q)]
