"""Pilot driver (plan.md, Pilot). Stages, each resumable:

  setup     prepare PRs in pilot order per repo, build environments and F2P tests, until each repo
            has its quota of PRs passing the build checks (later ones in the order replace failures)
  texts     summaries (B, C) and rubric for each pilot PR
  runs      agent runs: arms A, B, C with Sonnet in a per-PR shuffled order, then A with Opus
  inspect   scrub + two inspectors for every run
  report    only what the plan lets the pilot look at (no B or C scores are printed)

Usage: python -I pilot.py <stage>
"""
import json
import random
import sys
from pathlib import Path

import pandas as pd

import llm
from prepare import PRS, load_agents, pr_id, prepare

SEED = 20261107
STUDY = Path(__file__).resolve().parent.parent
ORDER = STUDY / "selection" / "out" / "pilot_order.csv"
QUOTA = {"home-assistant/core": 3, "getsentry/sentry-python": 2, "gruntwork-io/terragrunt": 3, "zitadel/zitadel": 2}
STATE = STUDY / "runs" / "pilot.json"


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"pilot": [], "excluded": {}}


def save(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))


def setup():
    import stage1
    s, agents = state(), load_agents()
    order = pd.read_csv(ORDER).sort_values(["repo", "rank"])
    for repo, quota in QUOTA.items():
        for r in order[order.repo == repo].itertuples():
            pid = pr_id(repo, r.pr)
            have = [p for p in s["pilot"] if p.startswith(repo.replace("/", "__") + "-")]
            if len(have) >= quota:
                break
            if pid in s["pilot"] or pid in s["excluded"]:
                continue
            try:
                _, checks = prepare(repo, int(r.pr), r.language, agents)
            except Exception as e:  # noqa: BLE001
                s["excluded"][pid] = f"prepare failed: {str(e)[:300]}"
                save(s)
                continue
            why = None
            if not checks["files_match"]:
                why = "check 1: merge diff file set differs from the PR"
            elif not checks["B_comments"] or not checks["C_comments"]:
                why = "check 4: no comments on one side"
            else:
                t = stage1.prepare_tests(pid)
                if not t["ok"]:
                    why = f"check 2/3: {t['reason']}"
            if why:
                s["excluded"][pid] = why
            else:
                s["pilot"].append(pid)
            save(s)
            print(pid, "OK" if not why else why, flush=True)
    print("pilot:", s["pilot"])
    print("excluded:", json.dumps(s["excluded"], indent=1))


def texts():
    import judge
    import summarise
    for pid in state()["pilot"]:
        for side in ("B", "C"):
            r = summarise.summarise(pid, side)
            print(pid, side, r.get("words"), "leak_first", r.get("leak_first"), "masked", r.get("masked"), flush=True)
        judge.rubric(pid)
        print(pid, "rubric ok", flush=True)


def arm_order(pid):
    arms = ["A", "B", "C"]
    random.Random(f"{SEED}-{pid}").shuffle(arms)
    return arms


def runs():
    import agent
    for pid in state()["pilot"]:
        for arm in arm_order(pid):
            r = agent.run(pid, arm)
            print(pid, arm, r["status"], r["seconds"], "s", r["total_tokens"], "tokens", flush=True)
        r = agent.run(pid, "A", llm.OPUS)
        print(pid, "A-opus", r["status"], r["seconds"], "s", r["total_tokens"], "tokens", flush=True)


def inspect():
    import judge
    for pid in state()["pilot"]:
        for tag in ("A", "B", "C", "A-opus"):
            if (PRS / pid / "arms" / tag / "stage1.json").exists():
                judge.inspect(pid, tag)
                print(pid, tag, "inspected", flush=True)


def report():
    """Allowed: build/F2P, plumbing, usage by role and model, summaries (read by hand), arm A Sonnet vs Opus."""
    s = state()
    print("PILOT PRs", len(s["pilot"]), "excluded", len(s["excluded"]))
    for k, v in s["excluded"].items():
        print("  excluded", k, "-", v)
    rows = []
    for pid in s["pilot"]:
        d = PRS / pid
        t = json.loads((d / "tests.json").read_text())
        row = {"pr": pid, "f2p": len(t["f2p"]), "p2p": len(t["p2p"]), "flaky": len(t["flaky_dropped"])}
        for side in ("B", "C"):
            sm = json.loads((d / f"summary_{side}.json").read_text()) if (d / f"summary_{side}.json").exists() else {}
            row[f"words_{side}"] = sm.get("words")
            row[f"leak_{side}"] = sm.get("leak_first")
        for tag in ("A", "B", "C", "A-opus"):
            a = d / "arms" / tag
            run = json.loads((a / "run.json").read_text()) if (a / "run.json").exists() else {}
            row[f"status_{tag}"] = run.get("status")
            row[f"files_{tag}"] = len(run.get("changed_files") or [])
            sc = a / "scrub.json"
            row[f"scrub_{tag}"] = json.loads(sc.read_text())["scrubbed_lines"] if sc.exists() else None
        for tag in ("A", "A-opus"):  # ceiling check only: arm A
            a = d / "arms" / tag
            s1 = json.loads((a / "stage1.json").read_text()) if (a / "stage1.json").exists() else {}
            io = json.loads((a / "inspect_opus.json").read_text()) if (a / "inspect_opus.json").exists() else {}
            row[f"resolved_{tag}"] = s1.get("resolved")
            row[f"rubric_{tag}"] = io.get("score")
        rows.append(row)
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    print(df.to_string(index=False))
    if len(df):
        a = df["resolved_A"].dropna()
        print(f"\nCEILING CHECK (arm A, Sonnet): resolved {int(a.sum())}/{len(a)}, mean rubric "
              f"{df['rubric_A'].mean():.2f}; Opus: resolved {int(df['resolved_A-opus'].dropna().sum())}/"
              f"{df['resolved_A-opus'].notna().sum()}, mean rubric {df['rubric_A-opus'].mean():.2f}")
        print("Ceiling rule triggers if Sonnet A resolved >= 8/10 and mean rubric >= 0.9.")
    led = pd.read_json(llm.LEDGER, lines=True)
    led = led[led.pr.isin(s["pilot"])]
    u = pd.json_normalize(led["usage"]).fillna(0)
    led = led.reset_index(drop=True).join(u)
    led["total"] = u.sum(axis=1)
    print("\nUSAGE by role and model (all pilot calls, including reruns)")
    print(led.groupby(["role", "model", "status"]).agg(calls=("total", "size"), total_tokens=("total", "sum"),
                                                        output=("output_tokens", "sum"),
                                                        seconds=("seconds", "sum")).to_string())
    print("\nUSAGE per PR (all roles)")
    print(led.groupby("pr").agg(calls=("total", "size"), total_tokens=("total", "sum"),
                                output=("output_tokens", "sum")).to_string())


if __name__ == "__main__":
    {"setup": setup, "texts": texts, "runs": runs, "inspect": inspect, "report": report}[sys.argv[1]]()
