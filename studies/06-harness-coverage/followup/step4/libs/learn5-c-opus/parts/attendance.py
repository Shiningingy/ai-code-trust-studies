"""Group membership: 'attends the chess club', '... only in the past', 'used to attend', 'no longer attends'."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402


def _att(extra):
    return lambda g, q: [("attends", lang.canon_obj(g["obj"]), extra + q)]


lang.register("attendance", r"(?P<cur>currently |still |also )?(?:attends|attend) {O}{M}",
              lambda g, q: [("attends", lang.canon_obj(g["obj"]),
                             (["status:current"] if g["cur"].strip() in ("currently", "still") else []) + q)],
              stative=True)
lang.register("attendance", r"(?:only |also )?used to (?:attend|attends|be a member of) {O}{M}",
              _att(["status:former"]), stative=True)
lang.register("attendance", r"(?:previously |formerly |had |only )?attended {O}{M}", _att(["status:former"]),
              stative=True)
lang.register("attendance", r"no longer (?:attends|attend) {O}{M}", _att(["status:former"]), stative=True)


class Attendance(Rule):
    name = "attendance"
    solves = ("group membership clauses -> attends; 'only in the past', 'used to attend', 'previously attended', "
              "'no longer attends' and past remarks in the tail give status:former, 'currently' gives status:current")
    added_by = "learning"
    examples = [
        ("G. Evans attends the chess club.", [lang.fact("G. Evans", "attends", "chess club")]),
        ("T. Patel attends the walking group only in the past.",
         [lang.fact("T. Patel", "attends", "walking group", ["status:former"])]),
        ("K. Mensah used to attend the walking group, but no longer does",
         [lang.fact("K. Mensah", "attends", "walking group", ["status:former"])]),
        ("I observed that elena ito no longer attends the history group",
         [lang.fact("Elena Ito", "attends", "history group", ["status:former", "reported_by:narrator"])]),
        ("Q. Avery attends the garden circle, though only in the past",
         [lang.fact("Q. Avery", "attends", "garden circle", ["status:former"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"attendance"})
