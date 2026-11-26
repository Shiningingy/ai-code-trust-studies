"""Step 4, phase 1: one learning session (or the reconcile session) on the three training documents.

Usage: python -I run_learn.py learn <label> <model>
       python -I run_learn.py reconcile <label> <model> <lib_a> <lib_b> <lib_c>
Env: LHB_WORK (neutral working folders, default E:/r). Training files: 00000, 00001 (E:/lhb-data), 00041
(E:/lhb-data-hard), shown to the agent as train/doc1.md, doc2.md, doc3.md. The answer keys stay in the hook's
state folder, outside the workspace. The finished library is copied to step4/libs/<label>/, the transcript to
runs/step4/. Exit 3 = usage limit or similar hard error.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

here = os.path.dirname(os.path.abspath(__file__))
fdir = os.path.dirname(here)
sys.path.insert(0, here)
import prompts  # noqa: E402
from merge import diff_libraries  # noqa: E402

CLAUDE_EXE = os.environ.get("CLAUDE_EXE") or os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules", "@anthropic-ai", "claude-code", "bin", "claude.exe")
TRAIN = [("doc1", "E:/lhb-data", "00000"), ("doc2", "E:/lhb-data", "00001"), ("doc3", "E:/lhb-data-hard", "00041")]
TIME_LIMIT_S = 75 * 60


def install_hook(work):
    """Neutral copy of the hook with a pristine gram/ beside it; returns the hook path."""
    hdir = os.path.join(work, "_h", "s4")
    shutil.rmtree(hdir, ignore_errors=True)
    os.makedirs(hdir)
    shutil.copy(os.path.join(here, "hook.py"), os.path.join(hdir, "hook.py"))
    shutil.copytree(os.path.join(here, "gram"), os.path.join(hdir, "gram"))
    return os.path.join(hdir, "hook.py")


def main():
    mode, label, model = sys.argv[1], sys.argv[2], sys.argv[3]
    work = os.environ.get("LHB_WORK", "E:/r")
    ws = os.path.join(work, label)
    state = os.path.join(work, "_s", label)
    for d in (ws, state):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    os.makedirs(os.path.join(ws, "train"))
    keys = {}
    for doc, root, s in TRAIN:
        shutil.copy(os.path.join(root, "contexts", "sample-%s.md" % s), os.path.join(ws, "train", doc + ".md"))
        keys[doc] = sorted(json.load(open(os.path.join(root, "answers", "sample-%s.json" % s), encoding="utf-8"))["matches"])
    json.dump(keys, open(os.path.join(state, "keys.json"), "w"))
    shutil.copytree(os.path.join(here, "gram"), os.path.join(ws, "gram"))
    os.makedirs(os.path.join(ws, "lib", "parts"))
    json.dump({}, open(os.path.join(ws, "lib", "config.json"), "w"))
    if mode == "reconcile":
        libs = dict(zip("abc", sys.argv[4:7]))
        for k, p in libs.items():
            shutil.copytree(p, os.path.join(ws, "lib_" + k))
        groups, md = diff_libraries({k: os.path.join(ws, "lib_" + k) for k in libs},
                                    {d: os.path.join(ws, "train", d + ".md") for d in keys})
        open(os.path.join(ws, "diff.md"), "w", encoding="utf-8").write(md)
        json.dump(sorted(groups), open(os.path.join(state, "groups.json"), "w"))
        prompt = prompts.RECONCILE
    else:
        prompt = prompts.LEARN

    hook = install_hook(work).replace("\\", "/")
    settings = {"autoMemoryEnabled": False, "hooks": {"Stop": [{"hooks": [{"type": "command", "timeout": 300,
                "command": 'python -I "%s" "%s" %s' % (hook, state.replace("\\", "/"), mode)}]}]}}
    sp = os.path.join(work, "_settings", label + ".json")
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    json.dump(settings, open(sp, "w"))
    tmp = os.path.join(work, "_tmp", label)
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    env = dict(os.environ, TEMP=tmp, TMP=tmp, TMPDIR=tmp)
    out_dir = os.path.join(fdir, "runs", "step4")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, label + ".jsonl")
    cmd = [CLAUDE_EXE, "-p", prompt, "--model", model, "--setting-sources", "", "--settings", sp,
           "--tools", "Read,Grep,Glob,Bash,Write,Edit", "--allowedTools", "Read,Grep,Glob,Bash,Write,Edit",
           "--output-format", "stream-json", "--verbose", "--session-id", str(uuid.uuid4())]
    t0, timed_out = time.time(), False
    with open(path, "w", encoding="utf-8") as out, open(path[:-6] + ".err", "w", encoding="utf-8") as err:
        try:
            subprocess.run(cmd, cwd=ws, stdout=out, stderr=err, timeout=TIME_LIMIT_S, encoding="utf-8", env=env)
        except subprocess.TimeoutExpired:
            timed_out = True
    res = {}
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "result":
            res = d
    log = [json.loads(l) for l in open(os.path.join(state, "hook_log.jsonl"), encoding="utf-8")] if os.path.exists(os.path.join(state, "hook_log.jsonl")) else []
    dest = os.path.join(here, "libs", label)
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(os.path.join(ws, "lib"), dest)
    shutil.copy(os.path.join(state, "hook_log.jsonl"), os.path.join(out_dir, label + "-hook.jsonl")) if log else None
    summary = {"label": label, "mode": mode, "model": model, "secs": round(time.time() - t0), "timed_out": timed_out,
               "cost": res.get("total_cost_usd"), "turns": res.get("num_turns"), "is_error": res.get("is_error"),
               "hook_rounds": len(log), "final": {k: log[-1].get(k) for k in ("verdict", "tests", "unresolved", "done")} if log else None}
    with open(os.path.join(fdir, "runs", "step4_summary.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")
    print(json.dumps(summary))
    low = (res.get("result") or "").lower()
    sys.exit(3 if res.get("is_error") and any(w in low for w in ("usage limit", "rate limit", "limit reached", "credit")) else 0)


if __name__ == "__main__":
    main()
