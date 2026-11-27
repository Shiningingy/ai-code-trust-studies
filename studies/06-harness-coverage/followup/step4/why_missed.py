"""Step 5: for each failed G1/GO1 test run, which query condition the missed (or extra) people fail. Code, no model.

Re-parses the instance with the session's FINAL library and manual.jsonl (pristine gram), evaluates every query
condition separately with the base library's own condition code (library_only.py), and lists, for each missed
person, the conditions that the facts do not satisfy, plus whether dropping the `genuinely` requirement would
include them. Also: does the base library's code on the session's final parse reproduce the session's answer?
Usage: python -I why_missed.py <runs/step2 dir> <summary jsonl>
"""
import json
import os
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import library_only as LO  # noqa: E402
from gram.pipeline import parse_text  # noqa: E402


def main():
    out_dir, summ = sys.argv[1], sys.argv[2]
    queries = {s.split("-")[1]: cs for s, _, cs in json.load(open(LO.QUERIES, encoding="utf-8"))}
    last = {}
    for l in open(summ, encoding="utf-8"):
        d = json.loads(l)
        if d["run"].startswith(("S5G1", "S5GO1")) and "90017" not in d["run"]:
            last[d["run"]] = d
    tmp = tempfile.mkdtemp()
    for run, d in sorted(last.items()):
        a = d["attempts"][0]
        if a["pass"]:
            continue
        s = d["sample"]
        base = "v5-opus" if run.startswith("S5GO1") else "v5"
        make = LO.v5opus_answerer if base == "v5-opus" else LO.v5_answerer
        strict, loose = make(False), make(True)
        key = sorted(json.load(open(os.path.join(LO.DATA, "answers", "sample-%s.json" % s), encoding="utf-8"))["matches"])
        text = open(os.path.join(LO.DATA, "contexts", "sample-%s.md" % s), encoding="utf-8").read()
        lib = os.path.join(out_dir, run + "-lib")
        manual = os.path.join(out_dir, run + "-manual.jsonl")
        recs = parse_text(text, lib, manual if os.path.exists(manual) else None)
        path = os.path.join(tmp, run + ".jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps({"line": r["line"], "facts": [x for c in r["clauses"] for x in c.get("facts") or []]}) + "\n")
        got = a["answer"] or []
        code = strict(path, queries[s])
        missed, extra = sorted(set(key) - set(got)), sorted(set(got) - set(key))
        per = {c: set(strict(path, [c])) for c in queries[s]}
        per_loose = {c: set(loose(path, [c])) for c in queries[s]}
        row = {"run": run, "sample": s, "missed": missed, "extra": extra, "code_on_final_parse_matches_session": code == sorted(got),
               "code_on_final_parse_correct": code == key, "loose_correct": loose(path, queries[s]) == key, "why": {}}
        for p in missed + extra:
            fails = [c for c in queries[s] if p not in per[c]]
            row["why"][p] = {"fails": fails, "passes_if_genuinely_dropped": [c for c in fails if p in per_loose[c]]}
        print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
