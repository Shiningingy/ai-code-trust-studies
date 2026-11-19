"""The runs in the fixed order of plan.md (D8, 2026-11-18), one at a time.

Bugs: Astropy-7606 (kept after the pre-check; the planned swap 8707 does not reproduce, plan.md Amendments)
and Closure_157. Within a bug the arms rotate per
round: k=1 S T U, k=2 T U S, k=3 U S T. Slots: r00 = smoke run (Astropy, arm S, not counted), r01-r09 Astropy,
r10-r18 Closure. Each slot E:\\w\\rNN is kept after its run for hand coding. Done runs are skipped, so a rerun
resumes.

Usage: python run_all.py --plan                  (print the full order)
       python run_all.py --dry-run               (write and print every prompt and command; no model call)
       python run_all.py --smoke                 (the smoke run only)
       python run_all.py --overnight             (9 Astropy runs, then Closure run 1 = arm S, then stop)
       python run_all.py --go                    (every run not yet done)
       python run_all.py --arm-l                 (Amendment 2: arm L, 3 Astropy then 3 Closure runs)
       python run_all.py --arm-h                 (Amendment 3: arm H, 3 Closure runs)
       python run_all.py --arm-f                 (Amendment 4: arm F, 3 Closure runs)
       python run_all.py --extra                 (arms L, H, F in that order; done runs skipped)
"""
import json
import sys
import time

import agent
import env
import llm
from bugs import STUDY

ASTROPY, CLOSURE = "astropy__astropy-7606", "Closure_157"
BUG_ORDER = [ASTROPY, CLOSURE]
ROTATION = {1: ["S", "T", "U"], 2: ["T", "U", "S"], 3: ["U", "S", "T"]}
BASE = llm.SLOT_BASE[llm.SONNET]  # Amendment 1: Sonnet 4.5 runs use slots r20 (smoke), r21-r38
SMOKE = {"k": 0, "bug": ASTROPY, "arm": "S", "slot": BASE}


def schedule():
    rows, slot = [], BASE
    for bug in BUG_ORDER:
        for k in (1, 2, 3):
            for arm in ROTATION[k]:
                slot += 1
                rows.append({"k": k, "bug": bug, "arm": arm, "slot": slot})
    return rows


def schedule_l():
    """Amendment 2 (Allen, 2026-11-18): arm L after the frozen 18 runs; Astropy first (cheap, it shakes out the
    harness), then Closure. Slots continue after the frozen schedule's last one (Sonnet 4.5: r39-r44)."""
    rows, slot = [], BASE + 18
    for bug in BUG_ORDER:
        for k in (1, 2, 3):
            slot += 1
            rows.append({"k": k, "bug": bug, "arm": "L", "slot": slot})
    return rows


def schedule_h():
    """Amendment 3 (Allen, 2026-11-18): arm H (S + read RenamePrototypes.java first), Closure only, 3 runs,
    after arm L. Slots r45-r47 (Sonnet 4.5)."""
    return [{"k": k, "bug": CLOSURE, "arm": "H", "slot": BASE + 24 + k} for k in (1, 2, 3)]


def schedule_f():
    """Amendment 4 (Allen, 2026-11-18): arm F (S + the full suite takes about 13 minutes), Closure only, 3 runs,
    after arm H. Slots r48-r50 (Sonnet 4.5)."""
    return [{"k": k, "bug": CLOSURE, "arm": "F", "slot": BASE + 27 + k} for k in (1, 2, 3)]


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
    for b in {r["bug"] for r in rows}:
        env.prepare(b)
    for r in rows:
        print(time.strftime("%H:%M"), "START", r["bug"], r["arm"], r["k"], "slot", r["slot"], "rate", llm.read_rate(),
              flush=True)
        rec = agent.run(r["bug"], r["arm"], r["k"], r["slot"])
        g = rec.get("grade") or {}
        print(time.strftime("%H:%M"), "DONE", r["bug"], r["arm"], r["k"], rec["status"], rec["seconds"], "s",
              rec["total_tokens"], "tokens", "repair", g.get("repair"), "LS", g.get("localization"),
              "RR", g.get("regression_reduction"), "subagents", rec.get("subagents"), "uml", rec.get("uml_calls"),
              "rate_after", rec.get("rate_after"), flush=True)


if __name__ == "__main__":
    rows = schedule()
    if "--plan" in sys.argv:
        for r in [SMOKE] + rows + schedule_l() + schedule_h() + schedule_f():
            print(r)
    elif "--dry-run" in sys.argv:
        dry_run(rows + schedule_l() + schedule_h() + schedule_f())
    elif "--extra" in sys.argv:  # amendments 2-4 in order: arm L (Astropy runs done earlier are skipped), H, F
        go(schedule_l() + schedule_h() + schedule_f())
    elif "--arm-f" in sys.argv:
        go(schedule_f())
    elif "--arm-l" in sys.argv:
        go(schedule_l())
    elif "--arm-h" in sys.argv:
        go(schedule_h())
    elif "--smoke" in sys.argv:
        go([SMOKE])
    elif "--overnight" in sys.argv:
        go([r for r in rows if r["bug"] == ASTROPY] + [r for r in rows if r["bug"] == CLOSURE and r["arm"] == "S"
                                                       and r["k"] == 1])
    elif "--astropy" in sys.argv:
        go([r for r in rows if r["bug"] == ASTROPY])
    elif "--closure1" in sys.argv:
        go([r for r in rows if r["bug"] == CLOSURE and r["arm"] == "S" and r["k"] == 1])
    elif "--go" in sys.argv:
        go(rows)
    else:
        raise SystemExit(__doc__)
