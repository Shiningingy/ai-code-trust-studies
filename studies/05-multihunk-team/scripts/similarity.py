"""Patch similarity to the gold fix (training-data exposure check 3, plan.md Amendment 1).

For every run (5.5 pilot and 4.5) compares agent.diff with the gold patch on changed lines, whitespace-normalised:
- files: files both patches touch / files the gold touches;
- gold_added_found: share of the gold's non-trivial added lines that also appear among the agent's added lines;
- jaccard: |A & G| / |A | G| over the sets of changed lines (added '+' and removed '-' kept apart).
A high gold_added_found with a different approach elsewhere would point to recall; low values point to a fix of
its own. Trivial lines (blank, braces, 'else', 'return;') are left out so they do not inflate the overlap.

Gold: Astropy-7606 = E:\\study05\\astropy-7606\\gold.diff; Closure_157 = the buggy->fixed diff used in
verification (E:\\study05\\verify\\Closure_157\\fixed\\graded.diff). That file is Defects4J's src patch as stored,
fixed -> buggy (grading applies it with reverse=True), so its + and - sides are swapped here (REVERSED).
Writes E:\\study05\\runs\\similarity.json and prints a table.

Usage: python similarity.py
"""
import json
import re
from pathlib import Path

import llm

GOLD = {"astropy__astropy-7606": Path(r"E:\study05\astropy-7606\gold.diff"),
        "Closure_157": Path(r"E:\study05\verify\Closure_157\fixed\graded.diff")}
REVERSED = {"Closure_157"}  # gold stored fixed -> buggy
TRIVIAL = {"", "{", "}", "};", "else", "else {", "} else {", "return;", "pass", ")", "(", "*/", "/*", "*", "//"}


def changed(diff_text):
    files, plus, minus = set(), set(), set()
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            files.add(line[4:].removeprefix("b/").strip())
        elif line.startswith("--- "):
            continue
        elif line.startswith(("+", "-")):
            norm = re.sub(r"\s+", " ", line[1:]).strip()
            if norm in TRIVIAL:
                continue
            (plus if line[0] == "+" else minus).add(norm)
    files.discard("/dev/null")
    return files, plus, minus


def compare(agent_text, gold_text, reversed_gold=False):
    af, ap, am = changed(agent_text)
    gf, gp, gm = changed(gold_text)
    if reversed_gold:
        gp, gm = gm, gp
    a = {("+", x) for x in ap} | {("-", x) for x in am}
    g = {("+", x) for x in gp} | {("-", x) for x in gm}
    return {"files_shared": sorted(af & gf), "files_gold": len(gf),
            "gold_added_found": round(len(ap & gp) / len(gp), 2) if gp else None,
            "gold_added_lines": len(gp), "agent_added_lines": len(ap),
            "jaccard": round(len(a & g) / len(a | g), 2) if a | g else None}


def main():
    rows = []
    for model, sub in llm.MODEL_DIR.items():
        root = llm.RUNS / sub if sub else llm.RUNS
        for bug, gold in GOLD.items():
            gold_text = gold.read_text(encoding="utf-8")
            for diff in sorted((root / bug).glob("*/*/agent.diff")):
                arm, run = diff.parent.parent.name, diff.parent.name
                rows.append({"model": model, "bug": bug, "arm": arm, "run": run,
                             **compare(diff.read_text(encoding="utf-8"), gold_text, bug in REVERSED)})
    (llm.RUNS / "similarity.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{'model':<28}{'bug':<24}{'arm':<4}{'run':<7}{'files':<7}{'gold+found':<12}{'jaccard':<8}")
    for r in rows:
        print(f"{r['model']:<28}{r['bug']:<24}{r['arm']:<4}{r['run']:<7}"
              f"{len(r['files_shared'])}/{r['files_gold']:<5}{str(r['gold_added_found']):<12}{str(r['jaccard']):<8}")


if __name__ == "__main__":
    main()
