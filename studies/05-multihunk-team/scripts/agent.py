"""One agent run (pattern from Study 04's agent.py): fresh copy of the base tree in a neutral folder, a
no-network container, `claude -p` with file tools + the container's `run` tool (+ the Agent tool in T/U),
then the patch, the paper's measures (grade.py) and the leak check.

Writes E:\\study05\\runs\\<bug>\\<arm>\\run<k>\\: prompt.txt, command.json, transcript.jsonl (stream-json, with
sub-agent messages forwarded), box.jsonl (every `run` command), run.json, agent.diff, after/, grade/, leaks.json.

Usage: python agent.py <bug id> <S|T|U> <k> <slot> --dry-run | --go
"""
import json
import shutil
import sys
import time
from pathlib import Path

import check_leaks
import env
import grade
import llm
import prompts
from bugs import BUGS, STUDY

TIME_LIMIT = 90 * 60  # wall clock per run, same for every arm (Closure's full suite takes ~13 min on the bind mount)
EFFORT = "medium"     # as Study 04; pinned so arms and runs match
ATTEMPTS = 3          # first run + up to two reruns for infrastructure errors (limit hits are not counted)
START_BELOW = {"astropy__astropy-7606": 0.80, "Closure_157": 0.35}  # five-hour utilization bar to start a run
FILE_TOOLS = "Read,Edit,Write,Glob,Grep,TodoWrite"  # the paper's Claude runs used TodoWrite (tools_count_claude.csv)


def graph_path(bug_id):
    return STUDY / "uml" / bug_id / "graph.puml"


def tools_for(arm):
    return FILE_TOOLS + (",Agent" if arm in ("T", "U") else "")


def expect_tools(arm):
    def check(tools):
        if "mcp__box__run" not in tools:
            return "run tool missing"
        if "Bash" in tools:
            return "Bash present"
        has_agent = "Agent" in tools or "Task" in tools
        if arm in ("T", "U") and not has_agent:
            return "sub-agent tool missing"
        if arm == "S" and has_agent:
            return "sub-agent tool present in S"
        return None
    return check


def neutral_box_server(slot):
    r"""The MCP server script and its log sit under E:\w too, so no study path appears even in the server's argv."""
    d = env.WORK / "tools"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).parent / "box_mcp.py", d / "box_mcp.py")
    return d / "box_mcp.py", d / f"box-r{slot:02d}.jsonl"


def extra_args(arm, box, box_log, server=Path("box_mcp.py")):
    mcp = {"mcpServers": {"box": {"command": sys.executable, "args": [str(server), box, str(box_log)]}}}
    return ["--tools", tools_for(arm), "--mcp-config", json.dumps(mcp), "--strict-mcp-config",
            "--allowedTools", "mcp__box__run", "--permission-mode", "acceptEdits", "--permission-prompts", "none",
            "--forward-subagent-text"]


def out_dir(bug_id, arm, k):
    return llm.RUNS / bug_id / arm / f"run{k}"


def capture(work, out, base):
    """Tracked changes against the base commit (the paper's `git diff HEAD`, robust to agent commits);
    new untracked files are listed but are not part of the patch, as in the paper."""
    diff = env.git(work, "diff", base, "--no-renames", "--binary")
    (out / "agent.diff").write_text(diff, encoding="utf-8", newline="\n")
    names = env.git(work, "diff", base, "--name-only", "--no-renames").split()
    untracked = env.git(work, "ls-files", "--others", "--exclude-standard").split()
    after = out / "after"
    if after.exists():
        shutil.rmtree(after)
    for n in names:
        src = work / n
        if src.is_file():
            dst = after / n
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return names, untracked


def dry_run(bug_id, arm, k, slot):
    prompt = prompts.build(bug_id, arm)
    work = env.WORK / f"r{slot:02d}"
    cmd = llm.base_cmd(llm.SONNET, EFFORT) + extra_args(arm, "<container>", "<box.jsonl>")
    return {"bug": bug_id, "arm": arm, "k": k, "slot": slot, "cwd": str(work),
            "graph_file": str(graph_path(bug_id)) if arm == "U" else None,
            "timeout_s": TIME_LIMIT, "command": cmd, "prompt": prompt,
            "leak_words_in_prompt": check_leaks.scan_text(prompt) + check_leaks.scan_text(str(work))}


def run(bug_id, arm, k, slot):
    out = out_dir(bug_id, arm, k)
    if (out / "run.json").exists() and json.loads((out / "run.json").read_text())["status"] in ("ok", "timeout", "refusal"):
        return json.loads((out / "run.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    prompt = prompts.build(bug_id, arm)
    if check_leaks.scan_text(prompt):
        raise SystemExit(f"leak words in the {arm} prompt: {check_leaks.scan_text(prompt)}")
    (out / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    base = env.base_commit(bug_id)
    attempt, limits = 0, 0
    while attempt < ATTEMPTS:
        attempt += 1
        work = env.fresh_workspace(bug_id, slot, graph_path(bug_id) if arm == "U" else None)
        box = env.start_box(bug_id, work, name=f"box-{arm}{k}")
        started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        try:
            server, box_log = neutral_box_server(slot)
            box_log.unlink(missing_ok=True)
            extra = extra_args(arm, box, box_log, server)
            (out / "command.json").write_text(json.dumps(llm.base_cmd(llm.SONNET, EFFORT) + extra, indent=1),
                                              encoding="utf-8")
            r = llm.call(prompt, role="agent", bug=bug_id, tag=f"{arm}{k}", model=llm.SONNET, effort=EFFORT,
                         cwd=work, extra=extra, timeout=TIME_LIMIT, transcript=out / "transcript.jsonl",
                         expect_tools=expect_tools(arm), pause_at=START_BELOW[bug_id])
        finally:
            env.stop_box(box)
            if box_log.exists():
                shutil.move(str(box_log), str(out / "box.jsonl"))
        rec = {"bug": bug_id, "arm": arm, "k": k, "slot": slot, "cwd": str(work), "started": started,
               "model": llm.SONNET, "effort": EFFORT, "attempt": attempt, "status": r["status"],
               "seconds": r["seconds"], "num_turns": r["num_turns"], "usage": r["usage"],
               "total_tokens": llm.total_tokens(r["usage"]), "model_usage": r["model_usage"],
               "init_model": r["init"].get("model"), "init_tools": r["init"].get("tools"),
               "init_cwd": r["init"].get("cwd"), "cc_version": r["init"].get("claude_code_version"),
               "mismatch": r["mismatch"]}
        if r["status"] == "tool_mismatch":
            (out / "run.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
            raise SystemExit(f"tool check failed on {bug_id} {arm}{k}: {r['mismatch']}; fix the harness first")
        if r["status"] == "limit":
            limits += 1
            with open(out / "limit_hits.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            if limits > 3:
                raise SystemExit(f"usage limit hit 4 times on {bug_id} {arm}{k}; stopping")
            attempt -= 1
            llm.pause_after_limit()
            continue
        if r["status"] == "error" and attempt < ATTEMPTS:
            continue
        rec["changed_files"], rec["untracked_new"] = capture(work, out, base)
        (out / "run.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
        if r["status"] in ("ok", "timeout", "refusal"):
            rec["grade"] = grade.grade_run(out)
            rec["leaks"] = check_leaks.scan_run(out)
            (out / "run.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
        return rec


if __name__ == "__main__":
    b, a, k, s = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    if "--dry-run" in sys.argv:
        d = dry_run(b, a, k, s)
        print(d["prompt"])
        print(json.dumps({x: y for x, y in d.items() if x != "prompt"}, indent=1))
    elif "--go" in sys.argv:  # a real run spends Allen's quota: only after he approves plan.md
        print(json.dumps(run(b, a, k, s), indent=1))
    else:
        raise SystemExit("add --dry-run to print the prompt, or --go (after Allen's approval) to run")
