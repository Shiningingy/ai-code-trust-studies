"""Helpers for querying the facts produced by `python -m gram parse <doc> --lib lib --out <dir>`.

    from lib.query import Facts
    fx = Facts.from_parsed("out/parsed.jsonl")      # or Facts.from_document("doc.md", lib="lib")
    for pid in fx.people():
        fx.of(pid, "works_for")                     # facts about that person, any name form
    fx.org_city("Organization 031")                 # 'Halifax'

Names are joined to person IDs through the roster facts (<name> has_id P-114, aliases included). A mention not in
the roster ("N. Reed" when only "Nadia Reed" is listed) is matched by initial + surname when that is unique.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict


class Facts:
    def __init__(self, facts):
        self.facts = facts
        self.ids = {}                       # lower-case name form -> person ID
        for f in facts:
            if f["relation"] == "has_id":
                self.ids[f["subject"].lower()] = f["object"]
        by_initial = defaultdict(set)
        for name, pid in self.ids.items():
            parts = name.split()
            if len(parts) == 2:
                by_initial[(parts[0][0], parts[1])].add(pid)
        self._by_initial = by_initial
        self.by_person = defaultdict(list)  # person ID (or entity name) -> facts with that subject
        for f in facts:
            if f["relation"] != "has_id":
                self.by_person[self.resolve(f["subject"])].append(f)

    @classmethod
    def from_parsed(cls, path):
        facts = []
        for line in open(path, encoding="utf-8"):
            facts.extend(json.loads(line)["facts"])
        return cls(facts)

    @classmethod
    def from_document(cls, doc, lib="lib", manual=None):
        out = tempfile.mkdtemp()
        cmd = [sys.executable, "-m", "gram", "parse", doc, "--lib", lib, "--out", out]
        if manual:
            cmd += ["--manual", manual]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        return cls.from_parsed(os.path.join(out, "parsed.jsonl"))

    def resolve(self, subject):
        """Person ID for a written name; other entities (Y055, Organization 031) are returned unchanged."""
        s = subject.lower()
        if s in self.ids:
            return self.ids[s]
        m = re.fullmatch(r"([a-z])[a-z]*\.? ([a-z][a-z-]+)", s)
        if m:
            cand = self._by_initial.get((m.group(1), m.group(2)), set())
            if len(cand) == 1:
                return next(iter(cand))
        return subject

    def people(self):
        return sorted(set(self.ids.values()))

    def of(self, who, relation=None):
        return [f for f in self.by_person.get(who, []) if relation is None or f["relation"] == relation]

    def org_city(self, org):
        for f in self.of(org, "based_in"):
            return f["object"]
        return None


def has(f, *quals):
    return all(q in f["qualifiers"] for q in quals)


def current(f):
    """Not marked as a former state (status=former), not negated, not a temporary or one-off/future case."""
    q = f["qualifiers"]
    return not any(x in q for x in ("status=former", "neg", "temporary", "freq=once", "time=future"))


# ---------------------------------------------------------------- world knowledge and common conditions
# Cities seen in the training documents; coastal ones are on an ocean coast.
COASTAL_CITIES = {"Halifax", "St. John's", "Vancouver", "Lunenburg", "Victoria"}
INLAND_CITIES = {"Edmonton", "Calgary", "Ottawa", "Regina", "Winnipeg"}
PUBLIC_TRANSIT = {"bus", "tram", "subway", "train", "metro", "streetcar", "light rail", "ferry"}
FRUITS = {"apple", "banana", "mango", "orange", "peach", "pear", "plum", "watermelon", "grape", "grapes", "cherry",
          "cherries", "strawberry", "strawberries", "kiwi", "pineapple", "lemon", "lime", "apricot", "melon"}
DAIRY = {"milk", "cheese", "butter", "yogurt", "cream", "dairy products"}


def works_for_coastal_org(fx, p):
    """Current employer (works_for without status=former) is based in a coastal city."""
    return any(current(f) and fx.org_city(f["object"]) in COASTAL_CITIES for f in fx.of(p, "works_for"))


def ordinarily_public_transit(fx, p):
    """Routinely travels by a public mode now (not 'but no longer does', not 'used ... once', not 'plans to')."""
    return any(f["object"] in PUBLIC_TRANSIT and has(f, "freq=routine") and current(f) for f in fx.of(p, "travels_by"))


def current_shift(fx, p, shift):
    return any(f["object"] == shift and current(f) for f in fx.of(p, "works_shift"))


def events_this_year(fx, p):
    """Distinct event ids volunteered at this year."""
    return {f["object"] for f in fx.of(p, "volunteered") if has(f, "time=this_year")}


def avoids_dairy_now(fx, p):
    """'currently chooses to avoid dairy products' (not 'temporarily skipping cheese', not 'buys cheese for others')."""
    return any(f["object"] == "dairy products" and current(f) for f in fx.of(p, "avoids"))


def taught_class_this_year(fx, p):
    return any(has(f, "role=teacher", "time=this_year") for f in fx.of(p, "took_part_in"))


def guardian_of_current_evening_course(fx, p):
    for g in fx.of(p, "guardian_of"):
        if current(g):
            if any(a["object"].startswith("evening_") and current(a) for a in fx.of(g["object"], "attends")):
                return True
    return False


def genuinely_prefers_train(fx, p):
    """'genuinely prefers train to plane when both are available' (not 'chose train ... only because of a
    disruption', not 'likes train and plane equally')."""
    return any(f["object"] == "train over plane" and has(f, "genuine") for f in fx.of(p, "prefers"))


def enjoys_fruit(fx, p):
    return any(f["object"] in FRUITS and current(f) for f in fx.of(p, "enjoys_eating"))
