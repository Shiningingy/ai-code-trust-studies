"""Study 06 follow-up, step 2: one run of arm A, B or C with pass/fail feedback (see ../plan.md, Step 2).

Usage: python -I run_step2.py <A|B|C|N|A1|B1|N1|P1|L1|PL1|LC1> <model> <sample> <rep>
Step 4 (plan.md): P = plan-first sentence; L = ledger Stop hook showing reader-flagged sentences never shown to the
agent (needs $LHB_WORK/_reader/<sample>/flagged.json from haiku_reader.py v2); PL = both; LC = hook shows only the
count of unseen sentences. All step-4 arms are one-pass (trailing 1).
Step 3 (plan.md): N = no plan, no critic; a trailing 1 = one-pass (one-pass plan PH1/CV1, the one-pass sentence
in the prompt, and the run stops after the first answer).
Env: LHB_DATA (contexts/, answers/), LHB_WORK (neutral working folders).
The answer key is read here, outside the agent's session; the agent only ever sees "incorrect".
Exit 3 = usage limit or similar hard error: the batch must stop.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid

CLAUDE_EXE = os.environ.get("CLAUDE_EXE") or os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules", "@anthropic-ai", "claude-code", "bin", "claude.exe")

MAX_ATTEMPTS = 5
TIME_LIMIT_S = 20 * 60
FAIL_MSG = "Your answer is incorrect. Keep working and give a new final answer in the same JSON format."
NOFMT_MSG = "No final answer in the required format was found. Keep working and end with the JSON answer."
TASK = ("The file context.md in the current directory contains a collection of documents followed by a final query "
        "at the end.")
ONE_PASS = "You will give one final answer. It is scored once, by exact match, with no feedback and no second try."
ANSWER_FMT = ('When you are done, end your reply with the final answer as a JSON object {"matches": [...]} '
              "listing the person IDs, sorted.")
PLAN_FIRST = ("Before you start, write a plan for solving this. List the ways your approach could miss something, "
              "and how you will rule out each one.")
HOOK_MODE = {"L": "list", "PL": "list", "LC": "count"}

here = os.path.dirname(os.path.abspath(__file__))
fdir = os.path.dirname(here)


WORKER_EXT = (".py", ".txt", ".json", ".pkl", ".csv", ".tsv", ".md")


def quarantine_shared_tmp(dest):
    """Git Bash maps /tmp to the Windows user Temp whatever TEMP says, so earlier runs' scripts and outputs stay
    visible there. Before each run, move worker-style files (top-level, plus small folders holding only such files)
    out of it into dest. Moved, never deleted; other programs' files (.tmp, logs, images, GUID folders) are left."""
    shared = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp")
    if not os.path.isdir(shared):
        return 0
    moved = 0
    for name in os.listdir(shared):
        src = os.path.join(shared, name)
        if name.startswith("Setup Log") or name == "claude":
            continue
        if os.path.isfile(src) and name.lower().endswith(WORKER_EXT):
            ok = True
        elif os.path.isdir(src) and len(name) <= 4:
            files = [f for _, _, fs in os.walk(src) for f in fs]
            ok = bool(files) and len(files) <= 200 and all(f.lower().endswith(WORKER_EXT) for f in files)
        else:
            ok = False
        if ok:
            os.makedirs(dest, exist_ok=True)
            try:
                shutil.move(src, os.path.join(dest, name))
                moved += 1
            except OSError:
                pass
    return moved


def tag_of(model):
    return model.replace("claude-", "").replace("-", "")


def parse_stream(path):
    res = {"text": "", "cost": 0.0, "is_error": False, "turns": 0, "tool_calls": 0, "key_access": False,
           "ledger_access": False}
    if not os.path.exists(path):
        return res
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "result":
            res.update(text=d.get("result") or "", cost=float(d.get("total_cost_usd") or 0),
                       is_error=bool(d.get("is_error")), turns=d.get("num_turns") or 0)
        msg = d.get("message") or {}
        for c in (msg.get("content") or []) if isinstance(msg.get("content"), list) else []:
            if c.get("type") == "tool_use":
                res["tool_calls"] += 1
                s = json.dumps(c.get("input", {})).lower()
                if "answers" in s and ("lhb" in s or "sample-0" in s) or "lhb-data" in s:
                    res["key_access"] = True
                if any(x in s for x in ("_reader", "check.py", "ledger_check")) or re.search(r'[\\/]_[sh](?:[\\/"\s]|$)', s):
                    res["ledger_access"] = True  # step 4: the agent touched the hook's files
    return res


def extract_answer(text):
    found = re.findall(r'\{\s*"matches"\s*:\s*\[[^\]]*\]\s*\}', text or "")
    if not found:
        return None
    try:
        return sorted(set(json.loads(found[-1])["matches"]))
    except (ValueError, KeyError, TypeError):
        return None


def main():
    arm, model, s, rep = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    data = os.environ.get("LHB_DATA", "E:/lhb-data")
    work = os.environ.get("LHB_WORK", "E:/r")
    tag = tag_of(model)
    one_pass = arm.endswith("1")
    base_arm = arm.rstrip("1")
    max_attempts = 1 if one_pass else MAX_ATTEMPTS
    fmt = (ONE_PASS + " " + ANSWER_FMT) if one_pass else ANSWER_FMT
    run_id = "S2%s%s%s%s" % (arm, tag, s, rep)
    out_dir = os.path.join(fdir, "runs", "step2")
    os.makedirs(out_dir, exist_ok=True)
    key = sorted(json.load(open(os.path.join(data, "answers", "sample-%s.json" % s), encoding="utf-8"))["matches"])

    ws = os.path.join(work, run_id)
    shutil.rmtree(ws, ignore_errors=True)
    os.makedirs(ws)
    shutil.copy(os.path.join(data, "contexts", "sample-%s.md" % s), os.path.join(ws, "context.md"))

    state_dir = os.path.join(work, "_critic", run_id)
    shutil.rmtree(state_dir, ignore_errors=True)
    os.makedirs(state_dir)
    # Each run gets its own temp folder: runs share %TEMP% otherwise, and a worker can find an earlier run's scripts
    # and outputs there (seen in arm C v1, 2026-11-25). Git Bash maps /tmp to TEMP, so this covers /tmp too.
    tmp = os.path.join(work, "_tmp", run_id)
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    env = dict(os.environ, TEMP=tmp, TMP=tmp, TMPDIR=tmp)
    quarantine_shared_tmp(os.path.join(work, "_tmp_quarantine", run_id))
    settings = {"autoMemoryEnabled": False}
    if arm == "C":
        cmd = 'python -I "%s" "%s" %s' % (os.path.join(here, "critic_hook.py").replace("\\", "/"),
                                         state_dir.replace("\\", "/"), model)
        settings["hooks"] = {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": cmd, "timeout": 200}]}]}
    ledger_dir = None
    if base_arm in HOOK_MODE:
        # Neutral paths: the agent must not see study names (the hook command itself is not shown with the JSON
        # block form, checked 2026-11-25, but paths can surface in errors).
        ledger_dir = os.path.join(work, "_s", run_id)
        shutil.rmtree(ledger_dir, ignore_errors=True)
        os.makedirs(ledger_dir)
        if HOOK_MODE[base_arm] == "list":
            shutil.copy(os.path.join(work, "_reader", s, "flagged.json"), os.path.join(ledger_dir, "flagged.json"))
        hook_py = os.path.join(work, "_h", "check.py")
        os.makedirs(os.path.dirname(hook_py), exist_ok=True)
        shutil.copy(os.path.join(here, "ledger_hook.py"), hook_py)
        cmd = 'python -I "%s" "%s" %s' % (hook_py.replace("\\", "/"), ledger_dir.replace("\\", "/"), HOOK_MODE[base_arm])
        settings["hooks"] = {"Stop": [{"hooks": [{"type": "command", "command": cmd, "timeout": 120}]}]}
    settings_path = os.path.join(work, "_settings", run_id + ".json")
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    json.dump(settings, open(settings_path, "w"))

    if base_arm in ("A", "B"):
        prefix = ("PH" if base_arm == "A" else "CV") + ("1" if one_pass else "")
        plan = open(os.path.join(fdir, "plans", "%s-%s-%s-%s.md" % (prefix, tag, s, rep)), encoding="utf-8").read()
        first = (TASK + " Earlier you looked at it and wrote this plan for answering the query:\n\n----- your plan -----\n"
                 + plan + "\n----- end of plan -----\n\nFollow your plan and answer the query. " + fmt)
    else:
        first = TASK + (" " + PLAN_FIRST if base_arm in ("P", "PL") else "") + " Answer the final query. " + fmt

    sid = str(uuid.uuid4())
    base = [CLAUDE_EXE, "-p", None, "--model", model, "--setting-sources", "", "--settings", settings_path,
            "--tools", "Read,Grep,Glob,Bash", "--allowedTools", "Read,Grep,Glob,Bash",
            "--output-format", "stream-json", "--verbose"]
    t_start = time.time()
    attempts, passed, stop, cum = [], False, False, 0.0
    msg = first
    for n in range(1, max_attempts + 1):
        remaining = TIME_LIMIT_S - (time.time() - t_start)
        if remaining <= 5:
            break
        cmd = list(base)
        cmd[2] = msg
        cmd += ["--session-id", sid] if n == 1 else ["--resume", sid]
        path = os.path.join(out_dir, "%s-a%d.jsonl" % (run_id, n))
        t0 = time.time()
        timed_out = False
        with open(path, "w", encoding="utf-8") as out, open(path[:-6] + ".err", "w", encoding="utf-8") as err:
            try:
                subprocess.run(cmd, cwd=ws, stdout=out, stderr=err, timeout=remaining, encoding="utf-8", env=env)
            except subprocess.TimeoutExpired:
                timed_out = True
        r = parse_stream(path)
        ans = extract_answer(r["text"])
        ok = ans == key
        low = r["text"].lower()
        if r["is_error"] and any(w in low for w in ("usage limit", "rate limit", "limit reached", "credit", "overloaded")):
            stop = True
        # With --resume, total_cost_usd is the session's cumulative cost; keep this attempt's own share
        # (fixed 2026-11-25; earlier summaries were corrected by fix_costs.py).
        own = r["cost"] - cum if r["cost"] else 0.0
        cum = r["cost"] or cum
        attempts.append({"attempt": n, "pass": ok, "answer": ans, "cost": round(own, 4), "cum_cost": round(cum, 4),
                         "secs": round(time.time() - t0), "turns": r["turns"], "tool_calls": r["tool_calls"],
                         "timed_out": timed_out, "is_error": r["is_error"], "key_access": r["key_access"],
                         "ledger_access": r["ledger_access"]})
        with open(os.path.join(state_dir, "attempts.txt"), "a", encoding="utf-8") as f:
            f.write("Attempt %d: %s\n" % (n, "correct" if ok else ("incorrect" if ans is not None else "no answer in the required format")))
        if ok or stop or timed_out:
            passed = ok
            break
        msg = FAIL_MSG if ans is not None else NOFMT_MSG

    critic_cost, critic_calls, challenges = 0.0, 0, 0
    log = os.path.join(state_dir, "critic_log.jsonl")
    if os.path.exists(log):
        shutil.copy(log, os.path.join(out_dir, run_id + "-critic.jsonl"))
        for line in open(log, encoding="utf-8"):
            d = json.loads(line)
            critic_cost += d.get("cost", 0)
            critic_calls += 1
            challenges += d.get("decision") == "CHALLENGE"
    ledger_check = None
    if ledger_dir and os.path.exists(os.path.join(ledger_dir, "ledger_check.json")):
        ledger_check = json.load(open(os.path.join(ledger_dir, "ledger_check.json"), encoding="utf-8"))
        pre = extract_answer(ledger_check.get("answer_before_check", ""))
        ledger_check.update(answer_before=pre, pass_before=pre == key)
        shutil.copy(os.path.join(ledger_dir, "ledger_check.json"), os.path.join(out_dir, run_id + "-ledger.json"))
    summary = {"run": run_id, "arm": arm, "model": model, "sample": s, "rep": rep, "pass": passed,
               "first_pass_attempt": next((a["attempt"] for a in attempts if a["pass"]), None),
               "attempts": attempts, "worker_cost": round(sum(a["cost"] for a in attempts), 4),
               "critic_cost": round(critic_cost, 4), "critic_calls": critic_calls, "challenges": challenges,
               "total_cost": round(sum(a["cost"] for a in attempts) + critic_cost, 4),
               "secs": round(time.time() - t_start), "session": sid, "stopped_on_error": stop,
               "ledger_check": {k: v for k, v in (ledger_check or {}).items() if k != "answer_before_check"} or None}
    with open(os.path.join(fdir, "runs", "step2_summary.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")
    print(json.dumps({k: summary[k] for k in ("run", "pass", "first_pass_attempt", "total_cost", "secs", "stopped_on_error")}))
    sys.exit(3 if stop else 0)


if __name__ == "__main__":
    main()
