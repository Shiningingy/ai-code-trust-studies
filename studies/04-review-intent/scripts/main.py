"""Main-run driver (plan.md). PR by PR, in draw order alternating Python and Go: summaries (B, C),
rubric, the three arms in a per-PR shuffled order (seed 20261107), then scrub + inspectors. Each PR
finishes before the next starts, so a run stopped early leaves complete units. PRs become ready when
the environment build marks them ok (runs/main_setup_<lang>.json); the driver waits for the rest.
Usage-limit pacing is in llm.py (pauses at STUDY_PAUSE_AT five-hour utilization, default 0.80).

Usage: python main.py [--max-prs N]
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd

import agent
import judge
import summarise
from pilot import arm_order
from prepare import PRS, pr_id

STUDY = Path(__file__).resolve().parent.parent
RUNS = STUDY / "runs"
STATE = RUNS / "main_state.json"


def order():
    w = pd.read_csv(STUDY / "selection" / "out" / "main_walk.csv")
    w = w[w.drawn].sort_values("rank")
    py, go = [pr_id(r.repo, r.pr) for r in w[w.language == "Python"].itertuples()], \
             [pr_id(r.repo, r.pr) for r in w[w.language == "Go"].itertuples()]
    out = []
    for i in range(max(len(py), len(go))):
        out += ([py[i]] if i < len(py) else []) + ([go[i]] if i < len(go) else [])
    return out


def setup_status():
    ok, excluded = set(), {}
    for lang in ("python", "go"):
        f = RUNS / f"main_setup_{lang}.json"
        if f.exists():
            s = json.loads(f.read_text(encoding="utf-8-sig"))
            ok |= set(s.get("ok", []))
            excluded.update(s.get("excluded", {}))
    return ok, excluded


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"done": [], "excluded": {}}


def save(s):
    STATE.write_text(json.dumps(s, indent=1))


def process(pid, s):
    for side in ("B", "C"):
        r = summarise.summarise(pid, side)
        if not r.get("text"):
            s["excluded"][pid] = f"check 4: no summary for {side} ({r.get('reason')})"
            return False
    judge.rubric(pid)
    for arm in arm_order(pid):
        r = agent.run(pid, arm)
        print(time.strftime("%H:%M"), pid, arm, r["status"], r["seconds"], "s", r["total_tokens"], "tokens", flush=True)
    for arm in ("A", "B", "C"):
        if (PRS / pid / "arms" / arm / "stage1.json").exists():
            judge.inspect(pid, arm)
    return True


def main(max_prs=None):
    s = state()
    todo = [p for p in order() if p not in s["done"] and p not in s["excluded"]]
    n = 0
    while todo:
        ok, excluded = setup_status()
        progressed = False
        for pid in list(todo):
            if pid in excluded:
                todo.remove(pid)
                continue
            if pid not in ok:
                continue
            try:
                if process(pid, s):
                    s["done"].append(pid)
                    n += 1
                    print(time.strftime("%H:%M"), "DONE", pid, f"({len(s['done'])} complete)", flush=True)
            except Exception as e:  # noqa: BLE001 - record and move on; the PR can be retried later
                print(time.strftime("%H:%M"), "ERROR", pid, str(e)[:400], flush=True)
                s.setdefault("errors", {})[pid] = str(e)[:400]
            save(s)
            todo.remove(pid)
            progressed = True
            if max_prs and n >= max_prs:
                return
            break  # re-read setup status after each PR, keeping draw order
        if not progressed:
            if all(p in excluded for p in todo):
                break
            time.sleep(120)
    print("main run finished:", len(s["done"]), "complete,", len(s["excluded"]), "excluded here", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[sys.argv.index("--max-prs") + 1]) if "--max-prs" in sys.argv else None)
