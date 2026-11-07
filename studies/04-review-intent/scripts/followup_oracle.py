"""Follow-up 6.2: oracle arm O (issue plus the rubric's behaviour items) on the 56 complete main-run PRs.
Calibration only, never a fair comparison: arm O is scored against the text it was given.

Same harness, model, effort and inspectors as the main run; usage guards in llm.py (STUDY_PAUSE_AT, STUDY_WEEK_STOP,
STUDY_STOP_AT). Resumable: state in runs/followup_oracle.json.

Usage: python followup_oracle.py [--max-prs N]     then: python followup_oracle.py --report
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd

import agent
import judge
import llm
from prepare import PRS

STUDY = Path(__file__).resolve().parent.parent
STATE = STUDY / "runs" / "followup_oracle.json"
PR_BUDGET = 15 * 60


def done_prs():
    out = []
    for lang in ("python", "go"):
        out += json.loads((STUDY / "runs" / f"main_state_{lang}.json").read_text(encoding="utf-8"))["done"]
    return sorted(out)


def run(max_prs=None):
    s = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"done": [], "errors": {}}
    n = 0
    for pid in done_prs():
        if pid in s["done"]:
            continue
        if llm.STOP_AT and time.time() + PR_BUDGET > llm.STOP_AT:
            print(time.strftime("%H:%M"), "STOP: stop time", flush=True)
            break
        try:
            r = agent.run(pid, "O")
            judge.inspect(pid, "O")
            s["done"].append(pid)
            print(time.strftime("%H:%M"), "DONE", pid, r["status"], r["seconds"], "s", r["total_tokens"], "tokens",
                  f"({len(s['done'])} complete)", flush=True)
        except Exception as e:  # noqa: BLE001
            s["errors"][pid] = str(e)[:400]
            print(time.strftime("%H:%M"), "ERROR", pid, str(e)[:300], flush=True)
        STATE.write_text(json.dumps(s, indent=1), encoding="utf-8")
        n += 1
        if max_prs and n >= max_prs:
            break
    print("oracle run finished:", len(s["done"]), "complete", flush=True)


def report():
    per = pd.read_csv(STUDY / "results" / "per_pr.csv")
    w = per.pivot(index="pr", columns="arm", values="opus")
    rows = []
    for pid in w.index:
        f = PRS / pid / "arms" / "O" / "inspect_opus.json"
        if f.exists():
            rows.append((pid, json.loads(f.read_text(encoding="utf-8"))["score"]))
    o = pd.Series(dict(rows), name="O")
    w = w.join(o, how="inner")
    gap = w.O.mean() - w.A.mean()
    L = [f"Follow-up 6.2 (oracle arm, exploratory). PRs with arm O scored: {len(w)}",
         "Mean rubric (Opus): " + ", ".join(f"{a} {w[a].mean():.3f}" for a in ("A", "B", "C", "O")),
         f"Gap O - A: {gap:+.3f}; share closed by B: {(w.B.mean() - w.A.mean()) / gap:.2f}; "
         f"by C: {(w.C.mean() - w.A.mean()) / gap:.2f}" if gap > 0 else "Gap O - A not positive",
         f"PRs where O scores below 0.5: {(w.O < 0.5).sum()} (rubric items possibly too strict or not judgeable)"]
    text = "\n".join(L)
    (STUDY / "results" / "followup_oracle.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    if "--report" in sys.argv:
        report()
    else:
        run(int(sys.argv[sys.argv.index("--max-prs") + 1]) if "--max-prs" in sys.argv else None)
