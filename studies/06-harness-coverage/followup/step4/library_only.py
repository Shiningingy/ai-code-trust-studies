"""Step 5 follow-up: the learned libraries alone, no model (code only).

For each of the 50 Constraint instances and each library (v5, v5-opus): parse the context with the pristine gram and
the library as the learners left it (no manual.jsonl), count clauses the library could not resolve, then answer the
instance's query with the library's OWN condition code (v5: tools/query.py answer(); v5-opus: answer_train.py
predicates). Each query condition string is mapped to that library's predicate for it; the 9 strings all occur in
the four training queries, so every predicate was written by the learners. The only edit to their code: v5's
answer() picks its conditions by training-document number, so that one line is replaced to take a condition list.

Also reported as counterfactuals (labelled, not results): correct_loose = the `genuinely` requirement removed;
correct_loose2 = also the `currently` requirement on the youth's evening course removed.
Usage: python -I library_only.py [instance ...]     (default: all 50)
"""
import importlib.util
import json
import os
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from gram.pipeline import parse_text  # noqa: E402

DATA = "E:/lhb-final"
QUERIES = "E:/lhb-full/hf-css-queries/queries.json"
TRAIN = {"00000", "00001", "00041", "00020"}
COND = {  # query condition -> (v5 key in answer(), v5-opus predicate name)
    "works for an organization based in a coastal city": ("coastal_org", "coastal_employer"),
    "ordinarily travels using public transportation": ("public_transport", "public_transport"),
    "currently works a night shift": ("night_shift", "night_shift"),
    "has volunteered at three or more distinct events this year": ("volunteer3", "events_this_year"),
    "currently chooses to avoid dairy products": ("no_dairy", "avoids_dairy"),
    "genuinely prefers train travel to flying when both are available": ("prefers_train", "prefers_train"),
    "is guardian of someone currently attending an evening course": ("guardian_evening", "guardian_evening"),
    "has personally taught a class this year": ("taught", "taught_this_year"),
    "enjoys eating something that is a fruit": ("fruit", "enjoys_fruit"),
}
OK = ("parsed", "ignored", "manual")


def load_module(path, name, edits=()):
    src = open(path, encoding="utf-8").read()
    for old, new in edits:
        assert src.count(old) == 1, (path, old)
        src = src.replace(old, new)
    mod = type(sys)(name)
    mod.__file__ = path
    sys.path.insert(0, os.path.dirname(path))
    exec(compile(src, path, "exec"), mod.__dict__)
    sys.path.pop(0)
    return mod


def v5_answerer(loose):
    edits = [('    conds = {1: ["coastal_org", "public_transport", "night_shift"],', '    conds = doc_no\n    _unused = {1: ["coastal_org", "public_transport", "night_shift"],'),
             ('"public_transport"]}[doc_no]', '"public_transport"]}')]
    if loose:
        edits.append(('obj="train over plane", require=["genuinely"])', 'obj="train over plane")'))
    if loose == 2:
        edits.append(('require=["currently", "during the evening"]', 'require=["during the evening"]'))
    m = load_module(os.path.join(here, "libs", "v5", "tools", "query.py"), "q_v5", edits)

    def ans(parsed, conds):
        ids, _, _ = m.answer(m.Index(m.load_facts(parsed)), [COND[c][0] for c in conds])
        return ids
    return ans


def v5opus_answerer(loose):
    lib = os.path.join(here, "libs", "v5-opus")
    edits = [('F.has(f, "over:plane", "genuinely")', 'F.has(f, "over:plane")')] if loose else []
    if loose == 2:
        edits.append(('c["object"].startswith("evening_") and F.has(c, "time:current")', 'c["object"].startswith("evening_")'))
    sys.modules.pop("query", None)
    m = load_module(os.path.join(lib, "answer_train.py"), "a_v5opus", edits)

    def ans(parsed, conds):
        return m.answer(parsed, [getattr(m, COND[c][1]) for c in conds])
    return ans


def main():
    queries = {s.split("-")[1]: cs for s, _, cs in json.load(open(QUERIES, encoding="utf-8"))}
    want = sys.argv[1:] or sorted(queries)
    tmp = tempfile.mkdtemp()
    libs = {"v5": v5_answerer, "v5-opus": v5opus_answerer}
    rows = []
    for s in want:
        text = open(os.path.join(DATA, "contexts", "sample-%s.md" % s), encoding="utf-8").read()
        key = sorted(json.load(open(os.path.join(DATA, "answers", "sample-%s.json" % s), encoding="utf-8"))["matches"])
        row = {"sample": s, "train": s in TRAIN, "conditions": len(queries[s])}
        for name, make in libs.items():
            recs = parse_text(text, os.path.join(here, "libs", name))
            bad = [c for r in recs for c in r["clauses"] if c["status"] not in OK]
            path = os.path.join(tmp, "%s-%s.jsonl" % (name, s))
            with open(path, "w", encoding="utf-8") as f:
                for r in recs:
                    f.write(json.dumps({"line": r["line"], "facts": [x for c in r["clauses"] for x in c.get("facts") or []]}) + "\n")
            got = make(False)(path, queries[s])
            loose = make(1)(path, queries[s])
            loose2 = make(2)(path, queries[s])
            row[name] = {"unresolved": len(bad), "correct": got == key, "correct_loose": loose == key, "correct_loose2": loose2 == key,
                         "missed": sorted(set(key) - set(got)), "extra": sorted(set(got) - set(key))}
        rows.append(row)
        print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
