"""One agent run: fresh checkout of the base tree in a neutral folder, a no-network container,
`claude -p` with file tools + the container's `run` tool, then the diff and stage 1.

Writes runs/prs/<id>/arms/<arm>/: prompt.txt, transcript.jsonl, box.jsonl, run.json, agent.diff,
after/ (touched files after the run), stage1.json.

Usage: python -I agent.py <pr id> <arm: A|B|C> [--model opus]
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import env
import llm
import stage1
from prepare import PRS, SNAP
from summarise import issue_text

DEVWORK = Path(r"G:\devwork")
TIME_LIMIT = 45 * 60
ATTEMPTS = 3  # first run + up to two reruns for limit or infrastructure failures

PROMPT = """You are working in a checkout of the {repo} repository (the current directory). Resolve the issue below by changing the code.

<issue>
{issue}
</issue>
{guidance}
Notes:
- The `run` tool executes shell commands in the project's Linux environment, in this same directory (inside that environment it appears as /work). Use it for tests, linters and scripts. There is no network access.
- The file tools (Read, Edit, Write, Glob, Grep) take this directory's own paths, absolute or relative. They cannot open /work paths: when a command's output names a file under /work, open the same relative path here.
- Do not commit. Leave your changes in the working tree.
- Do not refer to this task or its instructions in code, comments or docs."""

GUIDANCE = """
<guidance>
Guidance on this change (what it should do and why):
{summary}
</guidance>
"""


def build_prompt(pid, arm):
    d = PRS / pid
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    guidance = ""
    if arm in ("B", "C"):
        s = json.loads((d / f"summary_{arm}.json").read_text(encoding="utf-8"))
        if not s.get("text"):
            raise RuntimeError(f"{pid}: no summary for {arm}")
        guidance = GUIDANCE.format(summary=s["text"])
    return meta, PROMPT.format(repo=meta["repo"], issue=issue_text(meta), guidance=guidance)


def git(work, *args, check=True):
    p = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false", "-c", "gc.auto=0",
                        "-c", "maintenance.auto=false", "-c", "core.fsmonitor=false", *args], cwd=work,
                       capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {args[:3]}: {p.stderr.decode('utf-8', 'replace')[-800:]}")
    return p.stdout.decode("utf-8", "replace")


def fresh_checkout(pid, meta):
    work = DEVWORK / meta["repo"].split("/", 1)[1]
    if work.exists():
        shutil.rmtree(work, onerror=lambda f, p, e: (Path(p).chmod(0o666), f(p)))
    shutil.copytree(SNAP / pid / "base", work, ignore=shutil.ignore_patterns(".tree-ok"))
    git(work, "init", "-q")
    git(work, "config", "user.name", "dev")
    git(work, "config", "user.email", "dev@localhost")
    git(work, "config", "core.longpaths", "true")
    git(work, "add", "-A", "-f")
    git(work, "commit", "-q", "-m", "base")
    return work


def capture(work, out, meta):
    git(work, "add", "-A")
    diff = git(work, "diff", "--cached", "--no-renames", "--binary")
    (out / "agent.diff").write_text(diff, encoding="utf-8")
    names = git(work, "diff", "--cached", "--name-only", "--no-renames").split()
    after = out / "after"
    if after.exists():
        shutil.rmtree(after)
    for n in names:
        src = work / n
        if src.is_file():
            dst = after / n
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return names


def run(pid, arm, model=llm.SONNET):
    tag = arm if model == llm.SONNET else f"{arm}-opus"
    out = PRS / pid / "arms" / tag
    if (out / "run.json").exists() and json.loads((out / "run.json").read_text())["status"] in ("ok", "timeout", "refusal"):
        return json.loads((out / "run.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    meta, prompt = build_prompt(pid, arm)
    (out / "prompt.txt").write_text(prompt, encoding="utf-8")
    attempt, limits = 0, 0
    while attempt < ATTEMPTS:
        attempt += 1
        work = fresh_checkout(pid, meta)
        box = env.start_box(pid, work, name=f"box-{tag}")  # runs the recipe's prepare (generated files)
        git(work, "add", "-A")  # generated files that are not git-ignored join the baseline, not the diff
        git(work, "commit", "-q", "--allow-empty", "-m", "generated")
        try:
            mcp = {"mcpServers": {"box": {"command": sys.executable,
                                          "args": [str(Path(__file__).parent / "box_mcp.py"), box,
                                                   str(out / "box.jsonl")]}}}
            extra = ["--tools", "Read,Edit,Write,Glob,Grep", "--mcp-config", json.dumps(mcp), "--strict-mcp-config",
                     "--allowedTools", "mcp__box__run", "--permission-mode", "acceptEdits",
                     "--permission-prompts", "none"]
            r = llm.call(prompt, retry_on_limit=False, role="agent", pr=pid, tag=tag, model=model, effort="medium",
                         cwd=work, extra=extra, timeout=TIME_LIMIT, transcript=out / "transcript.jsonl")
        finally:
            env.stop_box(box)
        rec = {"pr": pid, "arm": arm, "tag": tag, "model": model, "effort": "medium", "attempt": attempt,
               "status": r["status"], "seconds": r["seconds"], "num_turns": r["num_turns"], "usage": r["usage"],
               "total_tokens": llm.total_tokens(r["usage"]), "init_model": r["init"].get("model"),
               "init_tools": r["init"].get("tools"), "cc_version": r["init"].get("claude_code_version")}
        if r["status"] == "limit":  # discarded; rerun from a fresh tree after the reset, not counted
            limits += 1
            with open(out / "limit_hits.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
            if limits > 3:
                raise SystemExit(f"usage limit hit 4 times on {pid} {tag}; stopping")
            attempt -= 1
            llm.pause_after_limit()
            continue
        if r["status"] == "error" and attempt < ATTEMPTS:
            continue
        rec["changed_files"] = capture(work, out, meta)
        (out / "run.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
        if r["status"] in ("ok", "timeout", "refusal"):
            stage1.score_agent(pid, tag, work)
        return rec


if __name__ == "__main__":
    model = llm.OPUS if "--model" in sys.argv and sys.argv[sys.argv.index("--model") + 1] == "opus" else llm.SONNET
    print(json.dumps(run(sys.argv[1], sys.argv[2], model), indent=1))
