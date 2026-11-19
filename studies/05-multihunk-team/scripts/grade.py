"""Score one patch with the paper's measures (TOSEM 2026, arXiv 2511.11012v3, Section 2.2).

A fresh copy of the base tree gets the patch, then compile and tests run in a no-network container.
- compiled (Eq. 4): non-empty patch that applies and compiles (Java: `defects4j compile`; Python: the patch
  applies and every changed .py file passes `python -m py_compile`).
- failed_after: Java: failing tests reported by `defects4j test` (the paper's runner counts its "  - " lines);
  Python: FAIL_TO_PASS + PASS_TO_PASS tests not PASSED/XFAIL, from the SWE-bench pytest log parser
  (swebench 4.1.0 parse_log_pytest_v2, its astropy parser, re-implemented below because swebench does not import on Windows).
  Before Python tests run, the test files touched by test_patch are reset to HEAD, as the SWE-bench eval does.
- repair (Eq. 5): non-empty patch and failed_after == 0 (Python: all FAIL_TO_PASS and PASS_TO_PASS pass,
  i.e. SWE-bench "resolved"). For astropy-7606 one PASS_TO_PASS name differs from what pytest prints in this
  image (bugs.py test_aliases): `repair` counts it under its printed name, `repair_strict` applies SWE-bench's
  rule (missing = failed), under which even the developer fix is not resolved.
- regression_reduction (Eq. 6): failed_before - failed_after; undefined (None) when compilation fails.
  failed_before is the paper's failed_test_prior (Java: number of trigger tests = 12; Python: 1).
- localization (Eq. 3): 1 if the developer-modified files are a subset of the files the patch modifies,
  else 0; 0 when the patch is empty or does not compile. (The repo's own generate_localization_ability
  scripts use edit accuracy instead; this study uses Eq. 3 as printed. See plan.md.)

Usage: python grade.py <run dir>      (reads agent.diff and run.json there, writes grade.json)
"""
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import env
from bugs import BUGS, DATA, swe_record

STATUSES = ("FAILED", "PASSED", "SKIPPED", "ERROR", "XFAIL")


def parse_log_pytest(log):
    """swebench 4.1.0 parse_log_pytest_v2 (= parse_log_astropy): also reads old pytest's "<test> STATUS" lines."""
    out = {}
    tr = str.maketrans("", "", "".join(chr(c) for c in range(1, 32)))
    for line in log.split("\n"):
        line = re.sub(r"\[(\d+)m", "", line).translate(tr)
        if any(line.startswith(s) for s in STATUSES):
            if line.startswith("FAILED"):
                line = line.replace(" - ", " ")
            parts = line.split()
            if len(parts) >= 2:
                out[parts[1]] = parts[0]
        elif any(line.endswith(s) for s in STATUSES):
            parts = line.split()
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    return out


def patch_files(diff):
    files = []
    for ln in diff.splitlines():
        if ln.startswith("diff --git a/"):
            files.append(ln.split(" b/", 1)[1].strip())
    return sorted(set(files))


def grade_patch(bug_id, diff, out, reverse=False, force=False):
    """force: grade an empty or reference patch too (used by env.verify)."""
    bug = BUGS[bug_id]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "graded.diff").write_text(diff, encoding="utf-8", newline="\n")
    tree = DATA / "gradework" / uuid.uuid4().hex[:8]
    tree.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(bug["base"], tree, symlinks=True, ignore=shutil.ignore_patterns(".ready"))
    started = time.time()
    rec = {"bug": bug_id, "nonempty": bool(diff.strip()), "files": patch_files(diff), "reverse": reverse}
    box = None
    try:
        if diff.strip():
            p = subprocess.run([*env.GIT, "apply", "--whitespace=nowarn", *(["-R"] if reverse else []),
                                str(out / "graded.diff")], cwd=tree, capture_output=True)
            rec["applied"] = p.returncode == 0
            rec["apply_error"] = p.stderr.decode("utf-8", "replace")[-1000:] if p.returncode else ""
        else:
            rec["applied"] = True
        if not rec["applied"]:
            rec.update(compiled=False, failed_after=None, repair=0, regression_reduction=None, localization=0)
            return rec
        if bug["kind"] == "d4j":
            env.restore_props(bug, tree)
        box = env.start_box(bug_id, tree, "grade")
        if bug["kind"] == "d4j":
            code, log = env.exec_box(box, "defects4j compile", timeout=1200)
            (out / "compile.log").write_text(log, encoding="utf-8")
            rec["compiled"] = code == 0
            if rec["compiled"]:
                code, log = env.exec_box(box, "defects4j test", timeout=3600)
                (out / "test.log").write_text(log, encoding="utf-8")
                failing = sorted({ln.strip()[2:] for ln in log.splitlines() if ln.strip().startswith("- ")})
                rec["test_exit"] = code
                rec["failing"] = failing
                rec["failed_after"] = len(failing)
                rec["trigger_still_failing"] = sorted(set(failing) & set(bug["failing_tests"]))
                rec["new_failures"] = sorted(set(failing) - set(bug["failing_tests"]))
        else:
            r = swe_record(bug_id)
            test_files = sorted({ln.split(" b/", 1)[1].strip() for ln in r["test_patch"].splitlines()
                                 if ln.startswith("diff --git a/")})
            env.git(tree, "checkout", "HEAD", "--", *test_files)
            py = [f for f in rec["files"] if f.endswith(".py") and (tree / f).exists()]
            code, log = (env.exec_box(box, "python -m py_compile " + " ".join(py), timeout=300) if py else (0, ""))
            (out / "compile.log").write_text(log, encoding="utf-8")
            rec["compiled"] = code == 0
            if rec["compiled"]:
                code, log = env.exec_box(box, f"cd /testbed && {bug['test_cmd']} {bug['test_directives']}", timeout=3600)
                (out / "test.log").write_text(log, encoding="utf-8")
                st = parse_log_pytest(log)
                f2p = json.loads(r["FAIL_TO_PASS"]) if isinstance(r["FAIL_TO_PASS"], str) else r["FAIL_TO_PASS"]
                p2p = json.loads(r["PASS_TO_PASS"]) if isinstance(r["PASS_TO_PASS"], str) else r["PASS_TO_PASS"]
                ok = ("PASSED", "XFAIL")
                al = bug.get("test_aliases", {})
                strict = [t for t in f2p + p2p if st.get(t) not in ok]  # SWE-bench rule: a missing name fails
                rec["failed_after_strict"] = len(strict)
                rec["repair_strict"] = int(bool(rec["nonempty"] or force) and not strict)
                rec["f2p_failing"] = [t for t in f2p if st.get(al.get(t, t)) not in ok]
                rec["p2p_failing"] = [t for t in p2p if st.get(al.get(t, t)) not in ok]
                rec["failing"] = rec["f2p_failing"] + rec["p2p_failing"]
                rec["failed_after"] = len(rec["failing"])
                rec["new_failures"] = rec["p2p_failing"]
        nonempty = rec["nonempty"] or force
        rec["repair"] = int(bool(nonempty and rec["compiled"] and rec.get("failed_after") == 0))
        rec["regression_reduction"] = bug["failed_before"] - rec["failed_after"] if rec["compiled"] else None
        rec["localization"] = int(bool(rec["nonempty"] and rec["compiled"]
                                       and set(bug["buggy_files"]) <= set(rec["files"])))
        return rec
    finally:
        rec["seconds"] = round(time.time() - started, 1)
        if box:
            env.stop_box(box)
        env.rmtree(tree)
        (out / "grade.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")


def grade_run(run_dir):
    run_dir = Path(run_dir)
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    diff = (run_dir / "agent.diff").read_text(encoding="utf-8")
    return grade_patch(run["bug"], diff, run_dir / "grade")


if __name__ == "__main__":
    print(json.dumps(grade_run(sys.argv[1]), indent=1))
