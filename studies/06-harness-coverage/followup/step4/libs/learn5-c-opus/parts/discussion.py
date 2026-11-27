"""Discussion: 'NAME discussed library', 'discussed the market', 'discussed market trends', 'talked about X'."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402

# a trailing noun that names an aspect of the place or group discussed ('market trends' -> market, aspect:trends)
ASPECTS = {"plans", "trends", "activities", "events", "matters", "hours", "visits", "conditions", "renovations",
           "schedules", "routes", "availability", "experience", "meeting", "news", "updates", "schedule",
           "membership", "rules", "strategies", "initiatives", "maintenance", "attendance", "expenses", "operations",
           "programs", "resources", "services", "logistics", "needs", "prices", "exhibits", "improvements", "access",
           "arrangements", "programming", "work", "projects", "funding", "budget", "volunteers", "facilities"}


def _build(g, q):
    obj = lang.canon_obj(g["obj"])
    words = obj.split()
    if len(words) > 1 and words[-1] in ASPECTS:
        return [("discussed", " ".join(words[:-1]), q + ["aspect:" + words[-1]])]
    return [("discussed", obj, q)]


lang.register("discussion", r"(?:also )?(?:discussed|discusses|discuss|talked about|talks about|mentioned) "
                            r"(?!(?:that|it|this|them|how|what|with|in|to|both)\b|keeping\b){O}{M}",
              _build)


class Discussion(Rule):
    name = "discussion"
    solves = ("discussion clauses ('discussed riverside park', 'discussed the market', 'talked about X', "
              "'discussed market trends' -> object market + aspect:trends) -> discussed")
    added_by = "learning"
    examples = [
        ("Priya Haddad discussed chess club.", [lang.fact("Priya Haddad", "discussed", "chess club")]),
        ("T. Avery discussed the market, highlighting its recent changes.",
         [lang.fact("T. Avery", "discussed", "market")]),
        ("H. Laurent discussed market trends during the last meeting",
         [lang.fact("H. Laurent", "discussed", "market", ["aspect:trends"])]),
        ("Hana Jones talked about the chess club, which was a nice change of pace.",
         [lang.fact("Hana Jones", "discussed", "chess club")]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"discussion"})
