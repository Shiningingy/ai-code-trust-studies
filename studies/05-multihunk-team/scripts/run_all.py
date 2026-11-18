"""The 18 runs (2 bugs x 3 arms x 3 runs) in the fixed order of plan.md, one at a time.

Order: rounds k = 1, 2, 3; in each round astropy first, then Closure; within a bug the three arms in an order
shuffled with seed 20261118 + k (so no arm always runs first or last). Each run has its own folder slot
E:\\w\\r01..r18, kept after the run for hand coding. Done runs are skipped, so a rerun resumes.
S runs only with --with-control (it is the recommended control, pending Allen's OK).

Usage: python run_all.py --plan                 (print the order)
       python run_all.py --dry-run [--with-control]   (write and print every prompt and command; no model call)
       python run_all.py --go [--with-control]        (real runs; only after Allen approves plan.md)
"""
import json
import random
import sys
import time

import agent
import env
import llm
from bugs import STUDY

BUG_ORDER = ["astropy__astropy-7606", "Closure_157"]


def schedule(with_control=True):
    rows, slot = [], 0
    for k in (1, 2, 3):
        for bug in BUG_ORDER:
            arms = ["S", "T", "U"]
            random.Random(20261118 + k).shuffle(arms)
            for arm in arms:
                slot += 1
                if arm == "S" and not with_control:
                    continue
                rows.append({"k": k, "bug": bug, "arm": arm, "slot": slot})
    return rows


def dry_run(rows):
    out = STUDY / "prompts" / "rendered"
    out.mkdir(parents=True, exist_ok=True)
    seen = set()
    for r in rows:
        d = agent.dry_run(r["bug"], r["arm"], r["k"], r["slot"])
        key = (r["bug"], r["arm"])
        if key not in seen:
            (out / f"{r['bug']}_{r['arm']}.txt").write_text(d["prompt"], encoding="utf-8", newline="\n")
            print(f"===== PROMPT {r['bug']} arm {r['arm']} ({len(d['prompt'])} chars) =====")
            print(d["prompt"])
            seen.add(key)
        print(json.dumps({x: y for x, y in d.items() if x != "prompt"}))
    print(f"{len(rows)} runs; prompts written to {out}")


def go(rows):
    print(time.strftime("%Y-%m-%d %H:%M"), "Claude Code", llm.cli_version(), "pinned", llm.PIN, flush=True)
    for b in BUG_ORDER:
        env.prepare(b)
    for r in rows:
        rec = agent.run(r["bug"], r["arm"], r["k"], r["slot"])
        g = rec.get("grade") or {}
        print(time.strftime("%H:%M"), "DONE", r["bug"], r["arm"], r["k"], rec["status"], rec["seconds"], "s",
              rec["total_tokens"], "tokens", "repair", g.get("repair"), "LS", g.get("localization"),
              "RR", g.get("regression_reduction"), flush=True)


if __name__ == "__main__":
    rows = schedule("--with-control" in sys.argv or "--plan" in sys.argv)
    if "--plan" in sys.argv:
        for r in rows:
            print(r)
    elif "--dry-run" in sys.argv:
        dry_run(rows)
    elif "--go" in sys.argv:
        go(rows)
    else:
        raise SystemExit(__doc__)
