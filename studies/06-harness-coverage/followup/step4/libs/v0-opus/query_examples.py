"""The three training queries answered from parsed facts (not a part; gram does not load it).

    for d in 1 2 3; do python -m gram parse train/doc$d.md --lib lib --manual train/doc$d.manual.jsonl --out out/doc$d; done
    python lib/query_examples.py            # writes answers.json

Each condition is a small function of (Facts, person ID); copy and adapt them for new queries. World knowledge the
documents do not state (coastal cities, fruits, public transport) lives in query.py.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from query import Facts, current, COASTAL_CITIES, PUBLIC_TRANSPORT, FRUITS  # noqa: E402


def coastal_org(fx, p):
    """works for an organization based in a coastal city (current employer; its city may be given only in a quote)"""
    return any(current(f) and any(b["object"] in COASTAL_CITIES for b in fx.about(f["object"], "based_in"))
               for f in fx.of(p, "works_for"))


def public_transport(fx, p):
    """ordinarily travels using public transportation: 'routinely', not past; 'once' and 'plans to use' do not count"""
    return any(current(f) and "routinely" in f["qualifiers"] and f["object"] in PUBLIC_TRANSPORT
               for f in fx.of(p, "travels_by"))


def night_shift(fx, p):
    """currently works a night shift ('in a former role' / 'used to work' are past)"""
    return any(current(f) and f["object"] == "night" for f in fx.of(p, "works_shift"))


def events3(fx, p):
    """has volunteered at three or more distinct events this year (old-event ... last-year does not count)"""
    return len({f["object"] for f in fx.of(p, "volunteered_at") if "this-year" in f["qualifiers"]}) >= 3


def no_dairy(fx, p):
    """currently chooses to avoid dairy products ('skips' cheese temporarily, 'dislikes_eating' milk do not count)"""
    return any(current(f) and f["object"] == "dairy products" for f in fx.of(p, "avoids"))


def guardian_evening(fx, p):
    """is guardian of someone currently attending an evening course (emergency contacts carry a negated guardian_of)"""
    return any(current(f) and any(current(g) and "during the evening" in g["qualifiers"]
                                  for g in fx.about(f["object"], "attends_course"))
               for f in fx.of(p, "guardian_of"))


def prefers_train(fx, p):
    """genuinely prefers train travel to flying: relation 'prefers' ('likes_equally' and 'chose ... because of a
    disruption' are the distractors; 'genuinely' is not always written)"""
    return any(current(f) and f["object"] == "train over plane" for f in fx.of(p, "prefers"))


def fruit(fx, p):
    """enjoys eating something that is a fruit, now ('serves ... but does not eat it' is another relation)"""
    return any(current(f) and f["object"] in FRUITS for f in fx.of(p, "enjoys_eating"))


QUERIES = {1: [coastal_org, public_transport, night_shift],
           2: [coastal_org, events3, no_dairy, public_transport],
           3: [events3, guardian_evening, prefers_train, fruit, no_dairy]}

if __name__ == "__main__":
    ans = {}
    for d, conds in QUERIES.items():
        fx = Facts("out/doc%d/parsed.jsonl" % d)
        ans["doc%d" % d] = sorted(p for p in fx.people() if all(c(fx, p) for c in conds))
    print(ans)
    json.dump(ans, open("answers.json", "w"), indent=1)
