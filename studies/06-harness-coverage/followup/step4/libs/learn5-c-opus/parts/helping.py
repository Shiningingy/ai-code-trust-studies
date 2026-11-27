"""Helping: 'helped with registration at the sports hall', 'assisted with setup at X'."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402


def _build(g, q):
    return [("helped_with", g["task"].lower(), (["at:" + lang.canon_obj(g["obj"])] if g["obj"] else []) + q)]


lang.register("helping", r"(?:also )?(?:helped|helps|help|helping|assisted|assists) with (?:the )?(?P<task>[A-Za-z]+)"
                         r"(?: at {O})?{M}", _build)


class Helping(Rule):
    name = "helping"
    solves = "helping clauses ('helped with setup at the library') -> helped_with <task>, qualifier at:<place>"
    added_by = "learning"
    examples = [
        ("F. Patel helped with registration at the sports hall.",
         [lang.fact("F. Patel", "helped_with", "registration", ["at:sports hall"])]),
        ("Nadia Patel helped with setup at the market, ensuring everything was ready for the opening.",
         [lang.fact("Nadia Patel", "helped_with", "setup", ["at:market"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"helping"})
