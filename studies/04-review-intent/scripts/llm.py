"""The one place that knows how a model is reached: `claude -p` on the subscription.

Every call is isolated from the user's own Claude Code setup (no settings sources, user
CLAUDE.md excluded, auto-memory off, CLAUDE*/ANTHROPIC* env vars dropped) and logs one ledger
row with usage by role and model. Stream-json transcripts of agent runs are kept in full.
"""
import json
import os
import subprocess
import time
from pathlib import Path

# The real executable, not the npm .cmd/.ps1 shim (a shim mangles JSON arguments on Windows).
CLAUDE = os.environ.get("STUDY_CLAUDE_EXE", str(Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" /
                                                "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"))
STUDY = Path(__file__).resolve().parent.parent
RUNS = STUDY / "runs"
LEDGER = RUNS / "ledger.jsonl"
NEUTRAL = Path(r"G:\devwork\app")  # cwd for no-tool calls; a name that says nothing about the study
ISOLATION = {"claudeMdExcludes": [(Path.home() / ".claude" / "CLAUDE.md").as_posix(), "**/.claude/CLAUDE.md"],
             "autoMemoryEnabled": False}
LIMIT_WORDS = ("usage limit", "rate limit", "limit reached", "limit will reset", "out of extra usage", "overloaded")

SONNET, OPUS = "claude-sonnet-5-5", "claude-opus-5-5"


def clean_env():
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("CLAUDE", "ANTHROPIC"))}
    env["DISABLE_NON_ESSENTIAL_MODEL_CALLS"] = "1"
    return env


def base_cmd(model, effort):
    return [CLAUDE, "-p", "--setting-sources", "", "--settings", json.dumps(ISOLATION),
            "--model", model, "--effort", effort, "--no-session-persistence",
            "--output-format", "stream-json", "--verbose"]


def parse_stream(text):
    events = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    return events, init, result


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


def ledger(row):
    RUNS.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def call(prompt, *, role, pr, model, effort="medium", schema=None, system=None, cwd=None, extra=(),
         timeout=900, transcript=None, tag=None):
    """Run one `claude -p`. Returns dict(status, result, structured, usage, init, seconds)."""
    cmd = base_cmd(model, effort) + list(extra)
    if not extra:
        cmd += ["--tools", ""]
    if schema:
        cmd += ["--json-schema", json.dumps(schema)]
    if system:
        cmd += ["--append-system-prompt", system]
    cwd = Path(cwd or NEUTRAL)
    cwd.mkdir(parents=True, exist_ok=True)
    started = time.time()
    timed_out = False
    try:
        p = subprocess.run(cmd, input=prompt.encode("utf-8"), capture_output=True, cwd=cwd, env=clean_env(),
                           timeout=timeout)
        code, out, err = p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired as e:
        timed_out = True
        code, out, err = -1, (e.stdout or b"").decode("utf-8", "replace"), (e.stderr or b"").decode("utf-8", "replace")
    seconds = round(time.time() - started, 1)
    events, init, result = parse_stream(out)
    status = classify(code, result, err, timed_out)
    if transcript:
        Path(transcript).parent.mkdir(parents=True, exist_ok=True)
        Path(transcript).write_text(out, encoding="utf-8")
    usage = result.get("usage") or {}
    row = {"t": started, "seconds": seconds, "role": role, "pr": pr, "tag": tag, "model": model, "effort": effort,
           "status": status, "exit": code, "num_turns": result.get("num_turns"),
           "usage": {k: usage.get(k) for k in ("input_tokens", "cache_creation_input_tokens",
                                               "cache_read_input_tokens", "output_tokens")},
           "modelUsage": result.get("modelUsage"), "duration_api_ms": result.get("duration_api_ms"),
           "init_model": init.get("model"), "cc_version": init.get("claude_code_version"),
           "init_tools": init.get("tools"), "init_plugins": init.get("plugins"),
           "init_memory_paths": init.get("memory_paths"), "permission_mode": init.get("permissionMode")}
    if status != "ok":
        row["stderr"] = err[-2000:]
        row["result_text"] = str(result.get("result"))[:2000]
    ledger(row)
    return {"status": status, "result": result.get("result"), "structured": result.get("structured_output"),
            "usage": row["usage"], "num_turns": row["num_turns"], "init": init, "seconds": seconds,
            "events": events}


def total_tokens(usage):
    return sum(usage.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                            "cache_read_input_tokens", "output_tokens"))
