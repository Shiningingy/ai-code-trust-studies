"""Rebuild the summary of a one-pass step-4 run whose session finished but whose runner crashed afterwards
(2026-11-26: S2G1sonnet55000211, parse_stream met a plain-text "message"; fixed in run_step2.py).
Uses run_step2's own parse_stream / extract_answer on the saved transcript; no model call.
Usage: python -I recover_run.py <arm> <model> <sample> <rep>"""
import json
import os
import shutil
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import run_step2 as r  # noqa: E402

arm, model, s, rep = sys.argv[1:5]
work = os.environ.get("LHB_WORK", "E:/r")
data = os.environ.get("LHB_DATA", "E:/lhb-data-hard")
run_id = "%s%s%s%s%s" % (os.environ.get("LHB_RUN_PREFIX", "S2"), arm, r.tag_of(model), s, rep)
out_dir = os.path.join(r.fdir, "runs", "step2")
key = sorted(json.load(open(os.path.join(data, "answers", "sample-%s.json" % s), encoding="utf-8"))["matches"])
p = r.parse_stream(os.path.join(out_dir, run_id + "-a1.jsonl"))
ans = r.extract_answer(p["text"])
attempts = [{"attempt": 1, "pass": ans == key, "answer": ans, "cost": round(p["cost"], 4), "cum_cost": round(p["cost"], 4),
             "secs": None, "turns": p["turns"], "tool_calls": p["tool_calls"], "timed_out": False,
             "is_error": p["is_error"], "key_access": p["key_access"], "ledger_access": p["ledger_access"]}]
ledger_check = None
ldir = os.path.join(work, "_s", run_id)
log = os.path.join(ldir, "hook_log.jsonl")
if arm.rstrip("1") in ("G", "GO") and os.path.exists(log):
    ledger_check = json.loads(open(log, encoding="utf-8").readline())
    pre = r.extract_answer(ledger_check.pop("answer_text", ""))
    ledger_check.update(answer_before=pre, pass_before=pre == key)
    shutil.copy(log, os.path.join(out_dir, run_id + "-hook.jsonl"))
    ws = os.path.join(work, run_id)
    shutil.copytree(os.path.join(ws, "lib"), os.path.join(out_dir, run_id + "-lib"), dirs_exist_ok=True)
    if os.path.exists(os.path.join(ws, "manual.jsonl")):
        shutil.copy(os.path.join(ws, "manual.jsonl"), os.path.join(out_dir, run_id + "-manual.jsonl"))
summary = {"run": run_id, "arm": arm, "model": model, "sample": s, "rep": rep, "pass": ans == key,
           "first_pass_attempt": 1 if ans == key else None, "attempts": attempts, "worker_cost": round(p["cost"], 4),
           "critic_cost": 0.0, "critic_calls": 0, "challenges": 0, "total_cost": round(p["cost"], 4), "secs": None,
           "session": None, "stopped_on_error": False, "recovered": True,
           "ledger_check": {k: v for k, v in (ledger_check or {}).items() if k != "answer_before_check"} or None}
with open(os.path.join(r.fdir, "runs", "step2_summary.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps(summary) + "\n")
print(json.dumps({k: summary[k] for k in ("run", "pass", "total_cost")}), attempts[0]["answer"])
