"""Predicates over the parsed facts that answer the usual conditions of the final queries (see NOTES.md).

    from lib.queries import Db
    db = Db("train/doc1.md", "train/doc1.manual.jsonl")
    sorted(p for p in db.people if db.coastal_employee(p) and db.public_transit(p) and db.night_shift(p))
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.resolve import Resolver, load_facts  # noqa: E402

COASTAL = {"Halifax", "Vancouver", "Victoria", "St. John's", "Lunenburg"}   # world knowledge: cities on a coast
PUBLIC = {"bus", "train", "tram", "subway"}
FRUITS = {"apple", "banana", "pear", "plum", "mango", "orange", "watermelon", "peach", "cherry", "grape", "lemon", "kiwi",
          "strawberry", "melon", "pineapple", "apricot", "papaya"}
PAST_Q = {"past", "former", "no longer", "used to", "once", "future", "negated", "temporarily"}


class Db:
    def __init__(self, doc, manual=None):
        self.facts = load_facts(doc, manual)
        self.R = Resolver(self.facts)
        self.by = defaultdict(lambda: defaultdict(list))        # person id (or Org/Youth id) -> relation -> facts
        for f in self.facts:
            s = f["subject"]
            key = s if s.startswith(("Org ", "Youth ")) else self.R.pid(s)
            if key:
                self.by[key][f["relation"]].append(f)
        self.people = sorted({k for k in self.by if k.startswith("P-")} |
                             {i for ids in self.R.ids.values() for i in ids})
        self.city = {f["subject"]: f["object"] for f in self.facts if f["relation"] == "based_in"}

    def rel(self, p, r):
        return self.by[p][r] if p in self.by else []

    @staticmethod
    def current(f):
        return not (set(f["qualifiers"]) & PAST_Q)

    def coastal_employee(self, p):
        return any(self.city.get(f["object"]) in COASTAL for f in self.rel(p, "works_for") if self.current(f))

    def public_transit(self, p):
        return any(f["object"] in PUBLIC and self.current(f) for f in self.rel(p, "travels_by"))

    def night_shift(self, p):
        return any(f["object"] == "night" and self.current(f) for f in self.rel(p, "works_shift"))

    def events_this_year(self, p):
        return len({f["object"] for f in self.rel(p, "volunteered_at") if "this year" in f["qualifiers"]})

    def avoids_dairy(self, p):
        return any(f["object"] == "dairy products" and self.current(f) for f in self.rel(p, "avoids"))

    def taught(self, p):
        return any("as teacher" in f["qualifiers"] and "this year" in f["qualifiers"] for f in self.rel(p, "took_part_in"))

    def guardian_of_evening(self, p):
        for f in self.rel(p, "guardian_of"):
            for c in self.rel(f["object"], "attends_course"):
                if "evening" in c["qualifiers"] and "currently" in c["qualifiers"]:
                    return True
        return False

    def prefers_train(self, p):
        return any(f["object"] == "train over plane" and "genuinely" in f["qualifiers"] for f in self.rel(p, "prefers"))

    def enjoys_fruit(self, p):
        return any(f["object"] in FRUITS and self.current(f) for f in self.rel(p, "enjoys_eating"))
