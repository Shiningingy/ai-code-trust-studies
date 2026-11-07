"""Stage 1: fail-to-pass and pass-to-pass tests per PR, and the agent's result.

tests.json per PR: test ids that fail (or are missing) at base + the PR's test files and pass in both
merge runs (F2P), ids that pass in all three (P2P), and ids whose two merge runs differ (dropped).
A test counts as passed only if the runner reports it passed: errors, collection or build failures,
skips and absences all count as not passed.

Usage: python -I stage1.py <pr id> [...]   (builds the image if needed, then writes tests.json)
"""
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import env
from prepare import PRS, SNAP

EVAL = Path(r"G:\devwork\eval")
TEST_TIMEOUT = 1800
DEP_FILES = ("requirements", "pyproject.toml", "setup.py", "setup.cfg", "go.mod", "go.sum", "manifest.json",
             "constraints", "package_constraints")


def overlay_tests(work, pid, meta):
    """Copy the PR's test files (merge versions) over a tree; delete the ones the PR deleted."""
    for f in meta["test_files"]:
        src, dst = SNAP / pid / "merge" / f, Path(work) / f
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif dst.exists():
            dst.unlink()


def command(meta):
    if meta["language"] == "Python":
        files = " ".join(f for f in meta["runnable_tests"])
        return (f"rm -f /tmp/junit.xml; {env.recipe(meta).get('pytest', 'python -m pytest')} -p no:cacheprovider "
                f"-o cache_dir=/tmp/pc --junitxml=/tmp/junit.xml -q {files} > /tmp/out.txt 2>&1; "
                "echo \"EXIT=$?\"; tail -c 3000 /tmp/out.txt; echo '@@JUNIT@@'; cat /tmp/junit.xml 2>/dev/null")
    pkgs = sorted({"./" + str(Path(f).parent).replace("\\", "/") for f in meta["runnable_tests"]})
    return (f"go test -json -count=1 -timeout 25m {' '.join(pkgs)} > /tmp/out.json 2>/tmp/err.txt; echo \"EXIT=$?\"; "
            "tail -c 3000 /tmp/err.txt; echo '@@JSON@@'; cat /tmp/out.json")


def parse(meta, out):
    """Map test id -> 'pass' | 'fail' | 'skip'."""
    res = {}
    if meta["language"] == "Python":
        xml = out.split("@@JUNIT@@", 1)[1].strip() if "@@JUNIT@@" in out else ""
        if not xml:
            return res
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return res
        for tc in root.iter("testcase"):
            tid = f"{tc.get('classname', '')}::{tc.get('name', '')}"
            tags = {c.tag for c in tc}
            res[tid] = "fail" if tags & {"failure", "error"} else "skip" if "skipped" in tags else "pass"
        return res
    body = out.split("@@JSON@@", 1)[1] if "@@JSON@@" in out else ""
    for line in body.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("Test") and e.get("Action") in ("pass", "fail", "skip"):
            res[f"{e['Package']}::{e['Test']}"] = e["Action"]
    return res


def run_tests(pid, meta, work, network=False, setup=False):
    box = env.start_box(pid, work, name="eval", network=network)
    try:
        if setup:
            env.exec_box(box, env.recipe(meta)["setup"], timeout=3600)
        code, out = env.exec_box(box, command(meta), timeout=TEST_TIMEOUT)
    finally:
        env.stop_box(box)
    return parse(meta, out), out


def eval_copy(pid, which):
    dst = EVAL / pid / which
    if dst.exists():
        shutil.rmtree(dst, onerror=lambda f, p, e: (Path(p).chmod(0o666), f(p)))
    shutil.copytree(SNAP / pid / which, dst, ignore=shutil.ignore_patterns(".tree-ok"))
    return dst


def prepare_tests(pid):
    d = PRS / pid
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    if (d / "tests.json").exists():
        return json.loads((d / "tests.json").read_text(encoding="utf-8"))
    if not env.build(pid, meta):
        rec = {"ok": False, "reason": "environment did not build"}
        (d / "tests.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
        return rec
    base = eval_copy(pid, "base")
    overlay_tests(base, pid, meta)
    r0, o0 = run_tests(pid, meta, base)
    deps_changed = any(any(k in Path(f).name for k in DEP_FILES) for f in meta["src_files"])
    merge = eval_copy(pid, "merge")
    r1, o1 = run_tests(pid, meta, merge, network=deps_changed, setup=deps_changed)
    r2, o2 = run_tests(pid, meta, merge, network=deps_changed, setup=deps_changed)
    flaky = sorted(t for t in set(r1) | set(r2) if r1.get(t) != r2.get(t))
    stable_pass = {t for t in r1 if r1[t] == "pass" and r2.get(t) == "pass"}
    f2p = sorted(t for t in stable_pass if r0.get(t) != "pass")
    p2p = sorted(t for t in stable_pass if r0.get(t) == "pass")
    rec = {"ok": bool(f2p), "reason": None if f2p else "no fail-to-pass test", "f2p": f2p, "p2p": p2p,
           "flaky_dropped": flaky, "deps_changed": deps_changed,
           "counts": {"base": len(r0), "merge1": len(r1), "merge2": len(r2)}}
    (d / "tests.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    for name, o in (("base", o0), ("merge1", o1), ("merge2", o2)):
        (d / f"tests_{name}.log").write_text(o[:200000], encoding="utf-8")
    shutil.rmtree(EVAL / pid, ignore_errors=True)
    return rec


def score_agent(pid, tag, work):
    d = PRS / pid
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    tests = json.loads((d / "tests.json").read_text(encoding="utf-8"))
    overlay_tests(work, pid, meta)
    res, out = run_tests(pid, meta, work)
    f2p_pass = [t for t in tests["f2p"] if res.get(t) == "pass"]
    p2p_pass = [t for t in tests["p2p"] if res.get(t) == "pass"]
    rec = {"resolved": len(f2p_pass) == len(tests["f2p"]) and len(p2p_pass) == len(tests["p2p"]),
           "f2p_passed": len(f2p_pass), "f2p_total": len(tests["f2p"]),
           "p2p_passed": len(p2p_pass), "p2p_total": len(tests["p2p"]),
           "f2p_failed": [t for t in tests["f2p"] if res.get(t) != "pass"][:50],
           "p2p_failed": [t for t in tests["p2p"] if res.get(t) != "pass"][:50]}
    arm = d / "arms" / tag
    (arm / "stage1.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    (arm / "stage1.log").write_text(out[:200000], encoding="utf-8")
    return rec


if __name__ == "__main__":
    for pid in sys.argv[1:]:
        r = prepare_tests(pid)
        print(pid, r.get("ok"), r.get("reason"), "f2p", len(r.get("f2p", [])), "p2p", len(r.get("p2p", [])),
              "flaky", len(r.get("flaky_dropped", [])), flush=True)
