"""Night run of 2026-11-08: oracle arm O (H.2), then Opus-agent replication (H.4), on one stream of repositories.

Streams never share a repository (the agent's work folder is per repository), so several can run at once.
PRs in a fixed random order (seed 4). Per stream: pass 0 = O, pass 1 = A-opus + B-opus, pass 2 = C-opus.
Done = arms/<tag>/inspect_sonnet.json exists, so reruns skip finished work. Usage guards in llm.py apply.

Usage: python followup_night.py --stream K --of N      (K = 0..N-1)
       python followup_night.py --plan --of N          (print the split, no runs)
"""
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import agent
import judge
import llm
from prepare import PRS

STUDY = Path(__file__).resolve().parent.parent
ARM_BUDGET = 15 * 60


def all_prs():
    out = []
    for lang in ("python", "go"):
        out += json.loads((STUDY / "runs" / f"main_state_{lang}.json").read_text(encoding="utf-8"))["done"]
    return sorted(out)


def repo_of(pid):
    return json.loads((PRS / pid / "meta.json").read_text(encoding="utf-8"))["repo"]


def split(n):
    by_repo = defaultdict(list)
    for p in all_prs():
        by_repo[repo_of(p)].append(p)
    streams = [[] for _ in range(n)]
    for repo in sorted(by_repo, key=lambda r: (-len(by_repo[r]), r)):  # greedy balance by PR count
        min(streams, key=len).extend(by_repo[repo])
    order = all_prs()
    random.Random(4).shuffle(order)
    rank = {p: i for i, p in enumerate(order)}
    return [sorted(s, key=rank.get) for s in streams]


def done(pid, tag):
    return (PRS / pid / "arms" / tag / "inspect_sonnet.json").exists()


def one(pid, arm, model):
    tag = arm if model == llm.SONNET else f"{arm}-opus"
    if done(pid, tag):
        return
    if llm.STOP_AT and time.time() + ARM_BUDGET > llm.STOP_AT:
        print(time.strftime("%H:%M"), "STOP: stop time", flush=True)
        raise SystemExit(0)
    arm_dir = PRS / pid / "arms" / tag
    if (arm_dir / "run.json").exists() and not (arm_dir / "stage1.json").exists():
        # run interrupted between the agent and stage 1 (process restart): set it aside and rerun from scratch
        aside = arm_dir.with_name(f"{tag}.interrupted-{time.strftime('%H%M%S')}")
        arm_dir.rename(aside)
        print(time.strftime("%H:%M"), "RERUN", pid, tag, "interrupted run moved to", aside.name, flush=True)
    try:
        r = agent.run(pid, arm, model)
        judge.inspect(pid, tag)
        print(time.strftime("%H:%M"), "DONE", pid, tag, r["status"], r["seconds"], "s", r["total_tokens"], "tokens",
              flush=True)
    except Exception as e:  # noqa: BLE001
        print(time.strftime("%H:%M"), "ERROR", pid, tag, str(e)[:300], flush=True)


def run(k, n):
    mine = split(n)[k]
    print(time.strftime("%H:%M"), f"stream {k}/{n}: {len(mine)} PRs, repos {sorted({repo_of(p) for p in mine})}",
          flush=True)
    for pid in mine:
        one(pid, "O", llm.SONNET)
    print(time.strftime("%H:%M"), "pass 0 (oracle) finished", flush=True)
    for pid in mine:
        one(pid, "A", llm.OPUS)
        one(pid, "B", llm.OPUS)
    print(time.strftime("%H:%M"), "pass 1 (A-opus, B-opus) finished", flush=True)
    for pid in mine:
        one(pid, "C", llm.OPUS)
    print(time.strftime("%H:%M"), "pass 2 (C-opus) finished", flush=True)


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--of") + 1])
    if "--plan" in sys.argv:
        for i, s in enumerate(split(n)):
            print(i, len(s), sorted({repo_of(p) for p in s}))
    else:
        run(int(sys.argv[sys.argv.index("--stream") + 1]), n)
