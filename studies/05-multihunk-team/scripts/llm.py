"""The one place that knows how a model is reached: `claude -p` on the subscription.

Copied from Study 04 (scripts/llm.py) with these changes only:
- ledger and rate readings live under E:\\study05\\runs (all run data on E:);
- the CLI runs under Popen and its stream is read live, so the init event can be checked before the model
  spends anything: if the tool list is not the one the arm needs (e.g. the sub-agent tool missing in T/U, or
  present in S), the process is killed and the run is recorded as 'tool_mismatch' (not counted, not rerun);
- the CLI version is checked against PIN before every call.

Isolation as in Study 04: no settings sources, user CLAUDE.md excluded, auto-memory off, CLAUDE*/ANTHROPIC*
env vars dropped. Usage guards: pause at PAUSE_AT five-hour utilization, stop at WEEK_STOP seven-day.

2026-11-18 decisions: no --effort flag (D4: the paper passed none; the CLI default is recorded); the weekly stop
is set near 0.99 only to catch a real limit (weekly is not a concern for Study 05); the five-hour check runs
once per agent run, before it starts (each run is one `claude -p` call), never inside a run.
"""
import json
import os
import subprocess
import threading
import time
from pathlib import Path

CLAUDE = os.environ.get("STUDY_CLAUDE_EXE", str(Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" /
                                                "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"))
PIN = "2.1.289"  # Claude Code version recorded at setup (2026-11-18); a different version stops the run
RUNS = Path(r"E:\study05\runs")
LEDGER = RUNS / "ledger.jsonl"
ISOLATION = {"claudeMdExcludes": [(Path.home() / ".claude" / "CLAUDE.md").as_posix(), "**/.claude/CLAUDE.md"],
             "autoMemoryEnabled": False}
LIMIT_WORDS = ("usage limit", "rate limit", "limit reached", "limit will reset", "out of extra usage", "overloaded")

SONNET = "claude-sonnet-5-5"

RATE = RUNS / "ratelimit.json"
PAUSE_AT = float(os.environ.get("STUDY_PAUSE_AT", "0.80"))
WEEK_STOP = float(os.environ.get("STUDY_WEEK_STOP", "0.99"))


def clean_env():
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("CLAUDE", "ANTHROPIC"))}
    env["DISABLE_NON_ESSENTIAL_MODEL_CALLS"] = "1"
    return env


def cli_version():
    p = subprocess.run([CLAUDE, "--version"], capture_output=True, env=clean_env())
    return p.stdout.decode("utf-8", "replace").split()[0] if p.stdout else None


def base_cmd(model, effort=None):
    """effort None = no --effort flag (the CLI default), as the paper's runs."""
    return [CLAUDE, "-p", "--setting-sources", "", "--settings", json.dumps(ISOLATION),
            "--model", model, *(["--effort", effort] if effort else []), "--no-session-persistence",
            "--output-format", "stream-json", "--verbose"]


def read_rate():
    return json.loads(RATE.read_text(encoding="utf-8")) if RATE.exists() else None


def classify(code, result, stderr, timed_out):
    """ok | limit | refusal | timeout | error. Only 'limit' and 'error' are rerun."""
    if timed_out:
        return "timeout"
    text = " ".join(str(x) for x in (result.get("result"), stderr, result.get("subtype"))).lower()
    if result.get("is_error") or code != 0 or not result:
        return "limit" if any(w in text for w in LIMIT_WORDS) else "error"
    if result.get("stop_reason") == "refusal":
        return "refusal"
    return "ok"


def note_rate(events):
    infos = [e.get("rate_limit_info") or {} for e in events if e.get("type") == "rate_limit_event"]
    if not infos:
        return
    w = infos[-1].get("unifiedWindows") or {}
    rec = {"t": time.time(), "five_hour": (w.get("five_hour") or {}).get("utilization"),
           "five_hour_resets": (w.get("five_hour") or {}).get("resetsAt"),
           "seven_day": (w.get("seven_day") or {}).get("utilization"), "status": infos[-1].get("status")}
    RUNS.mkdir(parents=True, exist_ok=True)
    RATE.write_text(json.dumps(rec), encoding="utf-8")


def wait_for_room(pause_at=None):
    """pause_at: start only below this five-hour utilization (run_all uses a lower bar before a long Closure run,
    so a run is not cut off by the limit halfway and discarded)."""
    if not RATE.exists():
        return
    pause_at = PAUSE_AT if pause_at is None else pause_at
    r = json.loads(RATE.read_text(encoding="utf-8"))
    if (r.get("seven_day") or 0) >= WEEK_STOP:
        raise SystemExit(f"[stop] seven-day utilization {r['seven_day']:.2f} >= {WEEK_STOP}; stopping cleanly")
    if (r.get("five_hour") or 0) >= pause_at and r.get("five_hour_resets"):
        wake = r["five_hour_resets"] + 120
        while time.time() < wake:
            print(f"[pause] five-hour utilization {r['five_hour']:.2f}; sleeping until "
                  f"{time.strftime('%H:%M', time.localtime(wake))}", flush=True)
            time.sleep(min(600, max(5, wake - time.time())))
        RATE.unlink(missing_ok=True)


def pause_after_limit():
    r = json.loads(RATE.read_text(encoding="utf-8")) if RATE.exists() else {}
    resets = r.get("five_hour_resets") or 0
    if resets < time.time():
        resets = time.time() + 1800
    RATE.write_text(json.dumps({"t": time.time(), "five_hour": 1.0, "five_hour_resets": resets,
                                "status": "limit hit"}), encoding="utf-8")
    wait_for_room()


def ledger(row):
    RUNS.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def total_tokens(usage):
    return sum(usage.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                            "cache_read_input_tokens", "output_tokens"))


def call(prompt, *, role, bug, tag, model, effort, cwd, extra, timeout, transcript, expect_tools=None, pause_at=None):
    """Run one `claude -p`. expect_tools(init_tools) -> error string or None, checked on the init event.
    Returns dict(status, result, usage, init, seconds, num_turns, model_usage, events)."""
    v = cli_version()
    if v != PIN:
        raise SystemExit(f"[stop] Claude Code {v} is installed, the plan pins {PIN}")
    cmd = base_cmd(model, effort) + list(extra)
    Path(cwd).mkdir(parents=True, exist_ok=True)
    wait_for_room(pause_at)
    started = time.time()
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=cwd, env=clean_env())
    lines, err, mismatch = [], [], {}

    def read_out():
        for raw in p.stdout:
            line = raw.decode("utf-8", "replace")
            lines.append(line)
            if expect_tools and not mismatch and line.startswith("{") and '"subtype":"init"' in line.replace(" ", ""):
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                problem = expect_tools(ev.get("tools") or [])
                if problem:
                    mismatch["why"] = problem
                    p.kill()

    t_out = threading.Thread(target=read_out, daemon=True)
    t_err = threading.Thread(target=lambda: err.append(p.stderr.read().decode("utf-8", "replace")), daemon=True)
    t_out.start()
    t_err.start()
    p.stdin.write(prompt.encode("utf-8"))
    p.stdin.close()
    timed_out = False
    try:
        p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        p.kill()
        p.wait()
    t_out.join(30)
    t_err.join(30)
    seconds = round(time.time() - started, 1)
    out = "".join(lines)
    events = []
    for line in out.splitlines():
        if line.strip().startswith("{"):
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    note_rate(events)
    stderr = "".join(err)
    status = "tool_mismatch" if mismatch else classify(p.returncode, result, stderr, timed_out)
    Path(transcript).parent.mkdir(parents=True, exist_ok=True)
    Path(transcript).write_text(out, encoding="utf-8")
    usage = result.get("usage") or {}
    row = {"t": started, "seconds": seconds, "role": role, "bug": bug, "tag": tag, "model": model, "effort": effort,
           "status": status, "exit": p.returncode, "num_turns": result.get("num_turns"),
           "usage": {k: usage.get(k) for k in ("input_tokens", "cache_creation_input_tokens",
                                               "cache_read_input_tokens", "output_tokens")},
           "modelUsage": result.get("modelUsage"), "duration_ms": result.get("duration_ms"),
           "duration_api_ms": result.get("duration_api_ms"), "total_cost_usd": result.get("total_cost_usd"),
           "init_model": init.get("model"), "cc_version": init.get("claude_code_version"),
           "init_cwd": init.get("cwd"), "init_tools": init.get("tools"), "init_agents": init.get("agents"),
           "init_memory_paths": init.get("memory_paths"), "permission_mode": init.get("permissionMode"),
           "mismatch": mismatch.get("why"),
           "rate": json.loads(RATE.read_text(encoding="utf-8")) if RATE.exists() else None}
    if status != "ok":
        row["stderr"] = stderr[-2000:]
        row["result_text"] = str(result.get("result"))[:2000]
    ledger(row)
    return {"status": status, "result": result.get("result"), "usage": row["usage"], "num_turns": row["num_turns"],
            "model_usage": result.get("modelUsage"), "init": init, "seconds": seconds, "events": events,
            "mismatch": mismatch.get("why")}
