"""Study 06 follow-up, step 2, arm C: PreToolUse hook that asks a critic model to APPROVE or CHALLENGE each tool call.

Invoked by Claude Code as:  python -I critic_hook.py <state_dir> <model>
stdin: the hook JSON (tool_name, tool_input, transcript_path, cwd, ...).
Exit 0 = allow. Exit 2 with a reason on stderr = block; Claude Code shows the reason to the worker.
After MAX_CHALLENGES consecutive challenges the next call is allowed, so the pair cannot deadlock.
The critic runs with no tools and no settings sources, so this hook never fires for the critic itself.
"""
import json
import os
import subprocess
import sys
import time

CLAUDE_EXE = os.environ.get("CLAUDE_EXE") or os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules", "@anthropic-ai", "claude-code", "bin", "claude.exe")

MAX_CHALLENGES = 3
TAIL_CHARS = 7000
CLEAN_SETTINGS = '{"autoMemoryEnabled": false}'


def final_query(cwd):
    try:
        text = open(os.path.join(cwd, "context.md"), encoding="utf-8").read()
    except OSError:
        return "(query not found)"
    i = text.rfind("Final Query")
    return text[i:][:3000] if i >= 0 else text[-2000:]


def transcript_tail(path):
    """Recent assistant text, tool calls and (truncated) tool results, newest last."""
    items = []
    try:
        for line in open(path, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            msg = d.get("message") or {}
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for c in content:
                t = c.get("type")
                if t == "text" and msg.get("role") == "assistant":
                    items.append("AGENT: " + c.get("text", "")[:600])
                elif t == "tool_use":
                    items.append("TOOL CALL: " + json.dumps(c.get("input", {}))[:600])
                elif t == "tool_result":
                    r = c.get("content")
                    if isinstance(r, list):
                        r = " ".join(x.get("text", "") for x in r if isinstance(x, dict))
                    items.append("RESULT: " + str(r)[:500])
    except OSError:
        return "(no transcript)"
    out, n = [], 0
    for s in reversed(items):
        if n + len(s) > TAIL_CHARS:
            break
        out.append(s)
        n += len(s)
    return "\n".join(reversed(out)) or "(no steps yet)"


def main():
    state_dir, model = sys.argv[1], sys.argv[2]
    os.makedirs(state_dir, exist_ok=True)
    hook = json.loads(sys.stdin.read() or "{}")
    cwd = hook.get("cwd") or os.getcwd()
    counter_path = os.path.join(state_dir, "consecutive_challenges.txt")
    attempts_path = os.path.join(state_dir, "attempts.txt")
    log_path = os.path.join(state_dir, "critic_log.jsonl")
    consecutive = int(open(counter_path).read().strip() or 0) if os.path.exists(counter_path) else 0
    history = open(attempts_path, encoding="utf-8").read().strip() if os.path.exists(attempts_path) else "No answer submitted yet."

    proposed = json.dumps({"tool": hook.get("tool_name"), "input": hook.get("tool_input")})[:1500]
    prompt = (
        "You are reviewing another agent's work, one step at a time. The agent is answering the query below "
        "from a long text file, context.md, and must return the exact set of person IDs that meet every condition.\n\n"
        "QUERY:\n" + final_query(cwd) + "\n\n"
        "ANSWER HISTORY:\n" + history + "\n\n"
        "THE AGENT'S RECENT STEPS:\n" + transcript_tail(hook.get("transcript_path", "")) + "\n\n"
        "PROPOSED NEXT STEP:\n" + proposed + "\n\n"
        "Decide whether this next step should go ahead. Reply on one line: either APPROVE, or CHALLENGE: followed by "
        "one or two sentences saying what is wrong with the step or what the agent should do instead."
    )
    if consecutive >= MAX_CHALLENGES:
        decision, reason, cost = "APPROVE", "auto-approved after %d consecutive challenges" % consecutive, 0.0
    else:
        t0 = time.time()
        p = subprocess.run(
            [CLAUDE_EXE, "-p", prompt, "--model", model, "--setting-sources", "", "--settings", CLEAN_SETTINGS,
             "--no-session-persistence", "--tools", "", "--output-format", "json"],
            capture_output=True, text=True, encoding="utf-8", timeout=180,
        )
        try:
            d = json.loads(p.stdout)
            text, cost = (d.get("result") or "").strip(), float(d.get("total_cost_usd") or 0)
        except ValueError:
            text, cost = "", 0.0
        first = text.splitlines()[0].strip() if text else ""
        if first.upper().startswith("CHALLENGE"):
            decision, reason = "CHALLENGE", first.split(":", 1)[1].strip() if ":" in first else text[:300]
        else:
            decision, reason = "APPROVE", first[:200]
        if not text:
            decision, reason = "APPROVE", "critic returned no text (error); allowed"
    consecutive = consecutive + 1 if decision == "CHALLENGE" else 0
    open(counter_path, "w").write(str(consecutive))
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.time(), "tool": hook.get("tool_name"), "decision": decision,
                            "reason": reason, "cost": cost}) + "\n")
    if decision == "CHALLENGE":
        sys.stderr.write("A reviewer challenged this step: " + reason +
                         " Address the challenge (change the step or explain why it is right), then continue.")
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
