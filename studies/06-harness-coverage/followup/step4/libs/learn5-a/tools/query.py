"""Helpers for answering questions from parsed facts (see lib/NOTES.md).

Usage:  python lib/tools/query.py            -> parses train/doc1..4 and writes answers.json
Functions: load_facts(parsed_jsonl), Index(facts) with .person_id(name), .holds(...), .ids_where(...).
"""
import json
import os
import subprocess
import sys
from collections import defaultdict

COASTAL = {"Halifax", "Vancouver", "Lunenburg", "Victoria", "St. John's"}
PUBLIC = {"bus", "train", "subway", "tram", "metro"}
FRUIT = {"apple", "banana", "mango", "orange", "peach", "pear", "plum", "watermelon", "grape", "cherry", "berry", "melon",
         "strawberry", "pineapple", "lemon", "kiwi", "apricot", "fig"}
PAST = {"used to", "formerly", "previously", "no longer", "in the past", "only in the past", "in a former role",
        "has since lapsed", "has since ended", "since lapsed", "lapsed", "last-year", "last year"}


def load_facts(path):
    facts = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        for f in r["facts"]:
            facts.append(dict(f, line=r["line"]))
    return facts


class Index:
    def __init__(self, facts):
        self.facts = facts
        self.by_rel = defaultdict(list)
        for f in facts:
            self.by_rel[f["relation"]].append(f)
        self.ids = {}
        for f in self.by_rel["has_id"]:
            self.ids[f["subject"]] = f["object"]

    def person_id(self, name):
        return self.ids.get(name)

    def select(self, relation, obj=None, require=(), forbid=(), subject=None):
        """Facts of a relation whose qualifiers contain all of `require` and none of `forbid`."""
        out = []
        for f in self.by_rel[relation]:
            q = set(f["qualifiers"])
            if obj is not None and not (f["object"] in obj if isinstance(obj, (set, list, tuple)) else f["object"] == obj):
                continue
            if subject is not None and f["subject"] != subject:
                continue
            if set(require) - q or q & set(forbid):
                continue
            out.append(f)
        return out

    def subjects(self, *a, **k):
        return {f["subject"] for f in self.select(*a, **k)}


def answer(idx, doc_no):
    """The query of each training document, phrased on the parsed facts."""
    S = {}
    orgs_coastal = {f["subject"] for f in idx.by_rel["based_in"] if f["object"] in COASTAL}
    S["coastal_org"] = {f["subject"] for f in idx.select("works_for", forbid=PAST) if f["object"] in orgs_coastal}
    S["public_transport"] = idx.subjects("travels_by", obj=PUBLIC, forbid=PAST)
    S["night_shift"] = idx.subjects("works_shift", obj="night", forbid=PAST)
    ev = defaultdict(set)
    for f in idx.select("volunteered_at", require=["this-year"]):
        ev[f["subject"]].add(f["object"])
    S["volunteer3"] = {p for p, e in ev.items() if len(e) >= 3}
    S["no_dairy"] = idx.subjects("avoids", obj="dairy products", require=["currently"], forbid=PAST)
    S["taught"] = idx.subjects("took_part_in", require=["as the teacher"], forbid=["last year"])
    evening = {f["subject"] for f in idx.select("attends_course", require=["currently", "during the evening"])}
    S["guardian_evening"] = {f["subject"] for f in idx.select("guardian_of", forbid=["not a guardian"]) if f["object"] in evening}
    S["prefers_train"] = idx.subjects("prefers", obj="train over plane", require=["genuinely"])
    S["fruit"] = idx.subjects("enjoys_eating", obj=FRUIT, forbid=PAST)
    conds = {1: ["coastal_org", "public_transport", "night_shift"],
             2: ["coastal_org", "volunteer3", "no_dairy", "public_transport"],
             3: ["volunteer3", "guardian_evening", "prefers_train", "fruit", "no_dairy"],
             4: ["volunteer3", "taught", "night_shift", "coastal_org", "public_transport"]}[doc_no]
    people = set.intersection(*(S[c] for c in conds))
    return sorted(idx.person_id(p) for p in people if idx.person_id(p)), {c: len(S[c]) for c in conds}, \
        [p for p in people if not idx.person_id(p)]


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    out = os.environ.get("TMP", "out")
    res = {}
    for i in range(1, 5):
        manual = "%s/train/doc%d.manual.jsonl" % (root, i)
        subprocess.run([sys.executable, "-m", "gram", "parse", "%s/train/doc%d.md" % (root, i), "--lib", "%s/lib" % root,
                        "--manual", manual, "--out", "%s/o%d" % (out, i)], capture_output=True, cwd=root)
        idx = Index(load_facts("%s/o%d/parsed.jsonl" % (out, i)))
        ids, sizes, unresolved = answer(idx, i)
        print(i, ids, sizes, "no id:", unresolved)
        res["doc%d" % i] = ids
    json.dump(res, open(os.path.join(root, "answers.json"), "w"))
