"""Worked example: the three training queries answered from parsed facts (not a part; gram does not load it).

    for d in 1 2 3; do python -m gram parse train/doc$d.md --lib lib --manual train/doc$d.manual.jsonl --out out/doc$d; done
    python lib/query_examples.py            # writes answers.json

Each condition is a small function over kb.KB; copy and adapt them for new queries. World knowledge that the
documents do not state (which cities are coastal, which foods are fruits, which modes are public transport) lives in
the constants below and must be checked against each new query.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb  # noqa: E402

COASTAL = {"Halifax", "Vancouver", "Victoria", "St. John's", "Lunenburg"}   # inland: Calgary Edmonton Winnipeg Regina Ottawa
PUBLIC = {"bus", "subway", "tram", "train"}
FRUIT = {"watermelon", "banana", "pear", "peach", "mango", "apple", "orange", "plum"}   # not: lentils bread rice, dairy
K = kb.KB


def coastal_org(k, p):
    """works for an organization based in a coastal city"""
    for f in k.of(p, "works_for"):
        if K.current(f) and any(g["object"] in COASTAL for g in k.entity(f["object"], "based_in")):
            return True
    return False


def public_transport(k, p):
    """ordinarily travels using public transportation (routinely, not past; 'once' and 'future' do not count)"""
    return any(K.current(f) and K.has(f, "routinely") and f["object"] in PUBLIC for f in k.of(p, "travels_by"))


def night_shift(k, p):
    """currently works a night shift ('in a former role' / 'used to' are past)"""
    return any(K.current(f) and f["object"] == "night" for f in k.of(p, "works_shift"))


def events3(k, p):
    """has volunteered at three or more distinct events this year"""
    return len({f["object"] for f in k.of(p, "volunteered_at") if K.has(f, "period:this-year")}) >= 3


def no_dairy(k, p):
    """currently chooses to avoid dairy products ('temporarily skipping cheese', 'dislikes eating milk' do not count)"""
    return any(K.current(f) and f["object"] == "dairy products" for f in k.of(p, "avoids"))


def guardian_evening(k, p):
    """is guardian of someone currently attending an evening course (an emergency contact is not a guardian)"""
    for f in k.of(p, "guardian_of"):
        if K.current(f) and any(K.current(g) and (g["object"].startswith("evening_") or K.has(g, "during:evening"))
                                for g in k.entity(f["object"], "attends_course")):
            return True
    return False


def prefers_train(k, p):
    """genuinely prefers train travel to flying ('likes equally' and 'chose ... because of a disruption' do not count)"""
    return any(K.current(f) and f["object"] == "train" and K.has(f, "genuinely") for f in k.of(p, "prefers"))


def fruit(k, p):
    """enjoys eating something that is a fruit (now; 'serves ... but does not eat it' does not count)"""
    return any(K.current(f) and f["object"] in FRUIT for f in k.of(p, "enjoys_eating"))


QUERIES = {1: [coastal_org, public_transport, night_shift],
           2: [coastal_org, events3, no_dairy, public_transport],
           3: [events3, guardian_evening, prefers_train, fruit, no_dairy]}

if __name__ == "__main__":
    ans = {}
    for d, conds in QUERIES.items():
        k = kb.KB("out/doc%d/parsed.jsonl" % d)
        ans["doc%d" % d] = sorted(p for p in k.people() if all(c(k, p) for c in conds))
    print(ans)
    json.dump(ans, open("answers.json", "w"), indent=1)
