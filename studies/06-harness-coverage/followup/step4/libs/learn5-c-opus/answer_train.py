"""Worked example: answers the four training queries from out/docN/parsed.jsonl (run from the project root
after `python -m gram parse train/docN.md --lib lib --manual train/docN.manual.jsonl --out out/docN`)."""
import json
import sys

sys.path.insert(0, "lib")
from facts import Facts  # noqa: E402

COASTAL = {"Halifax", "St. John's", "Vancouver", "Victoria", "Lunenburg"}
TRANSIT = {"bus", "tram", "subway", "train", "metro", "streetcar", "ferry"}
FRUIT = {"apple", "banana", "mango", "orange", "peach", "pear", "plum", "watermelon", "grape", "cherry", "kiwi",
         "strawberry", "lemon", "pineapple"}


def conds(F):
    def coastal(p):
        orgs = {f["object"] for f in F.of(p, "works_for") if F.current(f)}
        return any(c["object"] in COASTAL for o in orgs for c in F.about(o, "based_in"))

    def transit(p):
        return any(f["object"] in TRANSIT and F.has(f, "freq:routinely") and F.current(f) for f in F.of(p, "travels_by"))

    def night(p):
        return any(f["object"] == "night" and F.current(f) for f in F.of(p, "works_shift"))

    def events3(p):
        return len({f["object"] for f in F.of(p, "volunteered_at") if F.has(f, "when:this year")}) >= 3

    def dairy(p):
        return any(f["object"] == "dairy products" and F.current(f) for f in F.of(p, "avoids"))

    def guardian_evening(p):
        for g in F.of(p, "guardian_of"):
            for c in F.about(g["object"], "attends_course"):
                if F.current(c) and ("during:evening" in c["qualifiers"] or c["object"].startswith("evening")):
                    return True
        return False

    def train(p):
        return any(f["object"] == "train" and F.has(f, "genuine") and F.current(f) for f in F.of(p, "prefers"))

    def fruit(p):
        return any(f["object"] in FRUIT and F.current(f) for f in F.of(p, "enjoys_eating"))

    def taught(p):
        return any(F.has(f, "role:teacher", "when:this year") for f in F.of(p, "took_part_in"))

    return dict(coastal=coastal, transit=transit, night=night, events3=events3, dairy=dairy,
                guardian_evening=guardian_evening, train=train, fruit=fruit, taught=taught)


Q = {1: ["coastal", "transit", "night"], 2: ["coastal", "events3", "dairy", "transit"],
     3: ["events3", "guardian_evening", "train", "fruit", "dairy"], 4: ["events3", "taught", "night", "coastal", "transit"]}
out = {}
for i, cs in Q.items():
    F = Facts("out/doc%d/parsed.jsonl" % i)
    C = conds(F)
    out["doc%d" % i] = sorted(p for p in F.persons() if all(C[c](p) for c in cs))
    print(i, out["doc%d" % i], {c: sum(C[c](p) for p in F.persons()) for c in cs},
          "unresolved person-like subjects:", sum(1 for s in F.unresolved if " " in s and s[0].isupper()))
json.dump(out, open("answers.json", "w"), indent=1)
