"""Visits: 'visited the museum [some time ago | previously | in the past | on Saturday]', 'went to X'."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402

lang.register("visit", r"(?:also |had |previously |later |then )?(?:visited|visits|visit|went to) {O}{M}",
              lambda g, q: [("visited", lang.canon_obj(g["obj"]), q)])


class Visit(Rule):
    name = "visit"
    solves = ("visit clauses ('visited the library some time ago', 'went to the museum') -> visited, with the time "
              "phrase kept as when:<phrase>")
    added_by = "learning"
    examples = [
        ("E. Patel visited the market some time ago.",
         [lang.fact("E. Patel", "visited", "market", ["when:some time ago"])]),
        ("Kofi Silva visited the market.", [lang.fact("Kofi Silva", "visited", "market")]),
        ("A. Foster visited the riverside park on Saturday.",
         [lang.fact("A. Foster", "visited", "riverside park", ["when:on saturday"])]),
        ("E. Laurent visited the market, where she purchased some supplies.",
         [lang.fact("E. Laurent", "visited", "market")]),
        ("Leah Usman recommended Copper Harbor, and she also visited the museum.", None),
        ("P. Khan and G. Ito both visited the market previously.",
         [lang.fact("P. Khan", "visited", "market", ["when:previously"]),
          lang.fact("G. Ito", "visited", "market", ["when:previously"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"visit"})
