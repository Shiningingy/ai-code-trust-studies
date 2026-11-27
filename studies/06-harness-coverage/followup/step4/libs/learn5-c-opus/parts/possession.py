"""Ownership: 'NAME owns a camera', 'owns garden tools', 'owns a garden tools set', 'has ...', 'I keep my X in the shed'."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402

lang.register("possession", r"(?:also )?(?:owns|own|has|have) (?!(?:been|had|already|just|never|since|also|[a-z]+ed)\b)(?:a |an )?{O}(?: set)?{M}",
              lambda g, q: [("owns", lang.canon_obj(g["obj"]), q)], stative=True)
lang.register("possession", r"(?:mentioned )?(?:keeps|keep|kept|keeping) (?:my|his|her|their|a|an) {O}{M}",
              lambda g, q: [("owns", lang.canon_obj(g["obj"]), q)], stative=True)


class Possession(Rule):
    name = "possession"
    solves = ("ownership clauses ('owns a camera', 'owns garden tools set', 'I keep my X in the shed') -> owns; "
              "trailing commentary such as 'which he uses for stargazing' carries no fact")
    added_by = "learning"
    examples = [
        ("B. Ito owns a garden tools.", [lang.fact("B. Ito", "owns", "garden tools")]),
        ("Mateo Foster owns a telescope, which he often brings to our outdoor events.",
         [lang.fact("Mateo Foster", "owns", "telescope")]),
        ("Elsewhere in the note, a. Avery owns a guitar.", [lang.fact("A. Avery", "owns", "guitar")]),
        ("D. Evans owns a garden tools set, which is always useful for outdoor work.",
         [lang.fact("D. Evans", "owns", "garden tools")]),
        ("Kofi Reed said, \"I keep my garden tools in the shed", None),
        ("Kofi Reed does not own a camera.", [lang.fact("Kofi Reed", "owns", "camera", ["neg"])]),
        ("I was settling into the lounge when J. Khan mentioned keeping a sewing kit nearby for quick repairs.",
         [lang.fact("J. Khan", "owns", "sewing kit")]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"possession"})
