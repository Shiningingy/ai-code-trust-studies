"""Study 06 follow-up: correct worker costs in runs/step2_summary.jsonl (found 2026-11-25, after step 3).

With --resume, Claude Code's result `total_cost_usd` (and `modelUsage`) is the cumulative cost of the whole session,
not of that invocation. run_step2.py summed the attempts, so every run with more than one attempt was over-counted.
Correct values: an attempt's own cost = its cumulative cost minus the previous attempt's; a run's worker cost = the
last attempt's cumulative cost. Attempt-1 costs and single-attempt runs are unchanged. Critic calls are separate
sessions and were already right.

Usage: python -I fix_costs.py   (keeps the original as runs/step2_summary_uncorrected.jsonl; idempotent)
"""
import json
import os
import shutil

here = os.path.dirname(os.path.abspath(__file__))
runs = os.path.join(os.path.dirname(here), "runs")
src = os.path.join(runs, "step2_summary.jsonl")
orig = os.path.join(runs, "step2_summary_uncorrected.jsonl")
if not os.path.exists(orig):
    shutil.copy(src, orig)
out = []
for line in open(orig, encoding="utf-8"):
    r = json.loads(line)
    prev = 0.0
    for a in r["attempts"]:
        a["cum_cost"] = a["cost"]
        a["cost"] = round(a["cum_cost"] - prev, 4)
        prev = a["cum_cost"]
    r["worker_cost"] = round(prev, 4)
    r["total_cost"] = round(prev + r["critic_cost"], 4)
    r["cost_note"] = "corrected 2026-11-25: attempt costs from cumulative session totals"
    out.append(json.dumps(r))
open(src, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("rewrote %d runs" % len(out))
