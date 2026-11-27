"""Answers the final queries of the four training documents from parsed facts. Not a grammar part.

    python -m gram parse train/docN.md --lib lib --manual train/docN.manual.jsonl --out out/docN   (N = 1..4)
    python lib/answer_train.py out            -> prints answers.json content

Each condition is a predicate on a person id; copy and adapt them for new queries (see NOTES.md, "Query recipes").
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from query import Facts, FRUITS, PUBLIC_TRANSPORT, COASTAL  # noqa: E402


def coastal_employer(F, p):
    for f in F.current(F.of(p, "works_for")):
        if any(b["object"] in COASTAL for b in F.subject_facts(f["object"], "based_in")):
            return True
    return False


def public_transport(F, p):
    return any(f["object"] in PUBLIC_TRANSPORT and F.has(f, "freq:routinely")
               for f in F.current(F.of(p, "travels_by")))


def night_shift(F, p):
    return any(f["object"] == "night" for f in F.current(F.of(p, "works_shift")))


def events_this_year(F, p, n=3):
    return len({f["object"] for f in F.of(p, "volunteered_at") if F.has(f, "time:this-year")}) >= n


def avoids_dairy(F, p):
    return any(f["object"] == "dairy products" for f in F.current(F.of(p, "avoids")))


def guardian_evening(F, p):
    for g in F.current(F.of(p, "guardian_of")):
        for c in F.current(F.subject_facts(g["object"], "attends_course")):
            if c["object"].startswith("evening_") and F.has(c, "time:current"):
                return True
    return False


def prefers_train(F, p):
    return any(f["object"] == "train" and F.has(f, "over:plane", "genuinely")
               for f in F.current(F.of(p, "prefers_over")))


def taught_this_year(F, p):
    return any(F.has(f, "role:teacher", "time:this-year") for f in F.current(F.of(p, "took_part_in_class")))


def enjoys_fruit(F, p):
    return any(f["object"] in FRUITS for f in F.current(F.of(p, "enjoys_eating")))


QUERIES = {
    "doc1": [coastal_employer, public_transport, night_shift],
    "doc2": [coastal_employer, events_this_year, avoids_dairy, public_transport],
    "doc3": [events_this_year, guardian_evening, prefers_train, enjoys_fruit, avoids_dairy],
    "doc4": [events_this_year, taught_this_year, night_shift, coastal_employer, public_transport],
}


def answer(parsed, conds):
    F = Facts(parsed)
    return sorted(p for p in F.ids() if all(c(F, p) for c in conds))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "out"
    print(json.dumps({d: answer(os.path.join(out, d, "parsed.jsonl"), c) for d, c in QUERIES.items()}, indent=1))
