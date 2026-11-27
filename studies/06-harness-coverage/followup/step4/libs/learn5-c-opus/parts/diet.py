"""Food and diet: 'currently chooses to avoid dairy products', 'is temporarily skipping cheese', 'buys milk for other
people', 'dislikes eating yogurt', 'enjoys eating mango [in the past]', 'serves pear to other people but does not eat it'."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402


def _rel(rel, extra=()):
    return lambda g, q: [(rel, lang.canon_obj(g["obj"]), list(extra) + q)]


lang.register("diet", r"(?P<cur>currently )?(?:chooses|choose) to avoid {O}{M}",
              lambda g, q: [("avoids", lang.canon_obj(g["obj"]), (["status:current"] if g["cur"] else []) + q)],
              stative=True)
lang.register("diet", r"(?P<cur>currently )?(?:avoids|avoid) {O}{M}",
              lambda g, q: [("avoids", lang.canon_obj(g["obj"]), (["status:current"] if g["cur"] else []) + q)],
              stative=True)
lang.register("diet", r"(?:is|am|are) temporarily (?:skipping|avoiding) {O}{M}", _rel("avoids", ["status:temporary"]),
              stative=True)
lang.register("diet", r"(?:buys|buy|bought) {O} for (?:other people|others){M}", _rel("buys_for_others"))
lang.register("diet", r"(?:dislikes|dislike) eating {O}{M}", _rel("dislikes_eating"), stative=True)
lang.register("diet", r"(?:enjoys|enjoy|likes|like) eating {O}{M}", _rel("enjoys_eating"), stative=True)
lang.register("diet", r"(?:used to (?:enjoy|like)|enjoyed|liked) eating {O}{M}", _rel("enjoys_eating", ["status:former"]),
              stative=True)
lang.register("diet", r"(?:serves|serve) {O} to (?:other people|others) but (?:does|do) not eat (?:it|them){M}",
              _rel("serves_to_others", ["neg:eats"]), stative=True)


class Diet(Rule):
    name = "diet"
    solves = ("food clauses -> avoids / buys_for_others / dislikes_eating / enjoys_eating / serves_to_others; "
              "'currently' status:current, 'temporarily' status:temporary, 'in the past' / 'used to' status:former, "
              "'but does not eat it' neg:eats")
    added_by = "learning"
    examples = [
        ("G. Chen currently chooses to avoid dairy products.",
         [lang.fact("G. Chen", "avoids", "dairy products", ["status:current"])]),
        ("Omar Ito is temporarily skipping cheese.",
         [lang.fact("Omar Ito", "avoids", "cheese", ["status:temporary"])]),
        ("L. Usman buys butter for other people.", [lang.fact("L. Usman", "buys_for_others", "butter")]),
        ("Kofi Reed enjoys eating pear in the past.",
         [lang.fact("Kofi Reed", "enjoys_eating", "pear", ["status:former"])]),
        ("R. Silva serves orange to other people but does not eat it",
         [lang.fact("R. Silva", "serves_to_others", "orange", ["neg:eats"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"diet"})
