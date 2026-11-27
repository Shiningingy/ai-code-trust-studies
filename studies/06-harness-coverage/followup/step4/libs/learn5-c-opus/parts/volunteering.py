"""Volunteering: 'volunteered at event-P-051-0 during this-year', 'volunteered at old-event-P-145 during last-year'."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402


def _build(g, q):
    when = ["when:" + g["per"].lower().replace("-", " ")] if g["per"] else []
    return [("volunteered_at", g["ev"], when + q)]


lang.register("volunteering", r"(?:also )?(?:volunteered|volunteers|volunteer) at (?P<ev>[\w-]*event[\w-]*)(?: during "
                              r"(?P<per>this[- ]year|last[- ]year))?{M}", _build)


class Volunteering(Rule):
    name = "volunteering"
    solves = ("volunteering clauses -> volunteered_at <event id>, qualifier when:this year / when:last year "
              "(from 'during this-year' / 'during last-year')")
    added_by = "learning"
    examples = [
        ("C. Silva volunteered at event-P-051-0 during this-year.",
         [lang.fact("C. Silva", "volunteered_at", "event-P-051-0", ["when:this year"])]),
        ("Ben Ito volunteered at old-event-P-145 during last-year, a role that required a lot of coordination.",
         [lang.fact("Ben Ito", "volunteered_at", "old-event-P-145", ["when:last year"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"volunteering"})
