"""Work: employers ('currently works for Org 019', 'works for Organization 025'), organization locations
('Org 013 is based in St. John's') and shifts ('works the night shift [in a former role]', 'used to work the night shift')."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402


def _cur(g):
    return ["status:current"] if g.get("cur") else []


lang.register("employment", r"(?P<cur>currently )?(?:also )?(?:works|work) for (?P<org>{ORG}){M}",
              lambda g, q: [("works_for", lang.canon_org(g["org"]), _cur(g) + q)], stative=True)
lang.register("employment", r"(?:used to work|worked|formerly worked|previously worked) for (?P<org>{ORG}){M}",
              lambda g, q: [("works_for", lang.canon_org(g["org"]), ["status:former"] + q)], stative=True)
lang.register("employment", r"(?P<cur>currently )?(?:works|work) (?:the |a |an )?(?P<s>[a-z]+) shift{M}",
              lambda g, q: [("works_shift", g["s"], _cur(g) + q)], stative=True)
lang.register("employment", r"(?:used to work|worked|formerly worked|previously worked) (?:the |a |an )?(?P<s>[a-z]+) "
                            r"shift{M}",
              lambda g, q: [("works_shift", g["s"], ["status:former"] + q)], stative=True)
lang.register("org_location", r"(?:is|was) (?:based|located|headquartered) in "
                              r"(?P<city>[A-Za-z][\w'.-]*(?: [A-Z][\w'.-]*)*){M}",
              lambda g, q: [("based_in", lang.canon_name(g["city"]), q)], subj=("org",), stative=True)


class Employment(Rule):
    name = "employment"
    solves = ("employer and shift clauses -> works_for <Org NNN> / works_shift <night|day>; 'currently' gives "
              "status:current, 'in a former role' / 'used to' / 'worked' give status:former")
    added_by = "learning"
    examples = [
        ("Rosa Chen currently works for Org 001.", [lang.fact("Rosa Chen", "works_for", "Org 001", ["status:current"])]),
        ("Gabriel Gupta works for Organization 018", [lang.fact("Gabriel Gupta", "works_for", "Org 018")]),
        ("L. Silva works the night shift in a former role.",
         [lang.fact("L. Silva", "works_shift", "night", ["status:former"])]),
        ("Quinn Novak works the night shift, so we adjusted our schedule accordingly.",
         [lang.fact("Quinn Novak", "works_shift", "night")]),
        ("T. Patel used to work the night shift.", [lang.fact("T. Patel", "works_shift", "night", ["status:former"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"employment"})


class OrgLocation(Rule):
    name = "org_location"
    solves = "organization location clauses ('Org 013 is based in St. John's') -> Org NNN based_in <City>"
    added_by = "learning"
    examples = [
        ("Org 013 is based in St. John's.", [lang.fact("Org 013", "based_in", "St. John's")]),
        ("In a separate update, organization 7 is based in Lunenburg.",
         [lang.fact("Org 007", "based_in", "Lunenburg")]),
        ("Org 027 is based in Lunenburg, which made the location easy to reference.",
         [lang.fact("Org 027", "based_in", "Lunenburg")]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"org_location"})
