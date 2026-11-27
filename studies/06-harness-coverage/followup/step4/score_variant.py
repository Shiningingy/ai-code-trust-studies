"""Step 4: how did each G session resolve the variant's known changes? (code, no model)

For every change in variants/90017-manifest.jsonl, re-parse the variant with the session's final library and
manual.jsonl (pristine gram) and record how the changed text was resolved: by a v0 part, by a part the session added
(normalizer / rule), by manual.jsonl, ignored, or left unresolved; and whether facts came out. Compared with the
expected kind (1 normalizer, 2 rule, 3 manual, 4 ignored). Also: how v0 alone resolves each change.
Usage: [S4_BASE=v0-opus] python -I score_variant.py <runs/step2 dir> <run id> [<run id> ...]
"""
import collections
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from gram.pipeline import load, parse_text  # noqa: E402

VAR = "E:/lhb-data-hard/contexts/sample-90017.md"
EXPECT = {1: "normalizer", 2: "rule", 3: "manual", 4: "ignored"}


def resolve(recs, ch, v0_names, lib_parts):
    rec = next((r for r in recs if r["line"] == ch["line"]), None)
    if rec is None:
        return "line not found", False
    target = ch["after"]
    cs = [c for c in rec["clauses"] if c["text"] and (c["text"] in target or target[:40] in c["text"] or c["text"][:40] in target)]
    if ch["kind"] == 1:  # whole-line change: look at every clause of the line
        cs = rec["clauses"]
    if not cs:
        return "no clause matched", False
    how, facts = set(), False
    for c in cs:
        st = c["status"]
        if st == "manual":
            how.add("manual")
        elif st == "ignored":
            how.add("ignored")
        elif st != "parsed":
            how.add("unresolved")
        else:
            by = c.get("by") or []
            new_rule = any(b not in v0_names for b in by)
            new_norm = any(n not in v0_names for n in c.get("normalizers", []))
            how.add("rule" if new_rule else ("normalizer" if new_norm else "v0"))
        facts = facts or bool(c.get("facts"))
    for k in ("unresolved", "manual", "rule", "normalizer", "ignored", "v0"):
        if k in how:
            return k, facts
    return "?", facts


def main():
    out_dir, runs = sys.argv[1], sys.argv[2:]
    man = [json.loads(l) for l in open(os.path.join(here, "variants", "90017-manifest.jsonl"), encoding="utf-8")]
    text = open(VAR, encoding="utf-8").read()
    v0 = os.path.join(here, "libs", os.environ.get("S4_BASE", "v0"))  # S4_BASE=v0-opus for step 4b
    v0_names = set(load(v0)[3])
    libs = {os.path.basename(v0) + " alone": (v0, None)}
    for r in runs:
        libs[r] = (os.path.join(out_dir, r + "-lib"), os.path.join(out_dir, r + "-manual.jsonl"))
    table = {}
    for name, (lib, manual) in libs.items():
        recs = parse_text(text, lib, manual if manual and os.path.exists(manual) else None)
        parts = load(lib)[3]
        table[name] = [resolve(recs, ch, v0_names, parts) for ch in man]
    print("how each change was resolved (expected: 1 normalizer, 2 rule, 3 manual, 4 ignored)\n")
    for kind in (1, 2, 3, 4):
        idx = [i for i, c in enumerate(man) if c["kind"] == kind]
        print("kind %d (%s), %d changes, %d about answer people" % (kind, EXPECT[kind], len(idx), sum(man[i]["answer_person"] for i in idx)))
        for name in libs:
            cnt = collections.Counter(table[name][i][0] for i in idx)
            nofacts = sum(1 for i in idx if kind != 4 and not table[name][i][1])
            print("   %-22s %s%s" % (name, dict(cnt), ("   no facts from %d" % nofacts) if nofacts else ""))
    print("\nkind 3 (free text), each change:")
    for i, c in enumerate(man):
        if c["kind"] == 3:
            print("  [%s] %s" % (c["relation"], c["after"][:90]))
            for name in libs:
                print("     %-22s %s, facts=%s" % (name, *table[name][i]))


if __name__ == "__main__":
    main()
