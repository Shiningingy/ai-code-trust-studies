"""Base trees, per-run workspaces and Docker boxes (pattern from Study 04's env.py / agent.py).

Every run starts from a copy of the bug's base tree in a neutral folder (E:\\w\\rNN), with the base commit as
HEAD. Harness files (the paper's test scripts, .swebench/ metadata, the arm-U graph, logs, build output) are
untracked and listed in .git/info/exclude, so the captured patch holds only the agent's changes to tracked
files, as the paper's `git diff HEAD` did. Agents edit on the host with file tools; every command runs in a
no-network container with the workspace mounted at /testbed. Repository code never runs on the host.

Usage: python env.py prepare <bug id>      (idempotent; builds the base tree)
       python env.py verify <bug id>       (buggy: failing tests fail; developer fix: they pass)
"""
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

from bugs import BUGS, DATA, SRC, swe_record

WORK = Path(r"E:\w")  # neutral parent; run folders are r01..r18 (no study words in any path the agent sees)
MOUNT = "/testbed"
GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false", "-c", "core.filemode=false",
       "-c", "gc.auto=0", "-c", "maintenance.auto=false", "-c", "core.fsmonitor=false",
       "-c", "user.name=dev", "-c", "user.email=dev@localhost"]

EXCLUDE = {
    "d4j": ["/run_bug_exposing_tests.sh", "/run_all_tests_trace.sh", "*.log", "/build/", "/all_tests",
            "/failing_tests", "/class-graph.puml"],
    "swe": ["/run_failing_tests.sh", "/run_all_tests.sh", "/.swebench/", "/.swebench_test_patch.diff", "*.log",
            "/class-graph.puml"],
}


def git(work, *args, check=True):
    p = subprocess.run([*GIT, *args], cwd=work, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {args[:3]}: {p.stderr.decode('utf-8', 'replace')[-800:]}")
    return p.stdout.decode("utf-8", "replace")


def docker(*args, timeout=None, check=False):
    p = subprocess.run(["docker", *args], capture_output=True, timeout=timeout)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    if check and p.returncode != 0:
        raise RuntimeError(f"docker {args[:2]}: {out[-1500:]}")
    return p.returncode, out


def lf_copy(src, dst, mode=None):
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes().replace(b"\r\n", b"\n"))


def rmtree(path):
    for wait in (0, 5, 15, 30, 60):  # Windows can hold a just-emptied folder briefly (indexer, antivirus)
        if not path.exists():
            return
        time.sleep(wait)
        try:
            shutil.rmtree(path, onerror=lambda f, p, e: (Path(p).chmod(0o666), f(p)))
        except PermissionError:
            continue
    if path.exists():
        raise RuntimeError(f"could not remove {path}")


def write_exclude(tree, kind):
    (tree / ".git" / "info").mkdir(parents=True, exist_ok=True)
    (tree / ".git" / "info" / "exclude").write_text("\n".join(EXCLUDE[kind]) + "\n", encoding="utf-8")


def blank_props(path, keys):
    """D6: keep the keys Defects4J's check.properties needs, but with empty values (no class names)."""
    if not keys:
        return
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        k = ln.split("=", 1)[0]
        out.append(f"{k}=" if k in keys else ln)
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def restore_props(bug, tree):
    """Grading: put back the original defects4j.build.properties (as checked out by Defects4J)."""
    if bug.get("props_blank"):
        shutil.copy2(bug["checkout"] / "defects4j.build.properties", tree / "defects4j.build.properties")


def prepare_d4j(bug):
    """Defects4J checkout (made in the image: defects4j checkout -p Closure -v 157b) minus its .git, which
    holds the fixed version as the parent commit; fresh git with one commit; the paper's two scripts beside it."""
    base, co = bug["base"], bug["checkout"]
    if (base / ".ready").exists():
        return base
    if not co.exists():
        code, out = docker("run", "--rm", "--network", "none", "-v", f"{co.parent}:/out", bug["image"], "bash", "-c",
                           f"defects4j checkout -p Closure -v 157b -w /tmp/c && cp -a /tmp/c /out/{co.name}",
                           timeout=1800)
        if code:
            raise RuntimeError(out[-1500:])
    rmtree(base)
    shutil.copytree(co, base, ignore=shutil.ignore_patterns(".git"))
    blank_props(base / "defects4j.build.properties", bug.get("props_blank", []))
    git(base, "init", "-q")
    git(base, "config", "core.filemode", "false")
    git(base, "config", "core.autocrlf", "false")
    git(base, "add", "-A", "-f")
    git(base, "commit", "-q", "-m", "base")
    write_exclude(base, "d4j")
    for s in bug["harness_files"]:
        lf_copy(SRC / "agentic_ai" / s, base / s)
    (base / ".ready").write_text(git(base, "rev-parse", "HEAD").strip(), encoding="utf-8")
    return base


def prepare_swe(bug):
    """/testbed from the pinned image (history ends at base_commit, so the fix is not reachable), then what the
    paper's setup_container does: test_patch committed as HEAD, .swebench/ metadata, the two test scripts."""
    base, co = bug["base"], bug["checkout"]
    if (base / ".ready").exists():
        return base
    if not co.exists():
        _, cid = docker("create", bug["image"], check=True)
        cid = cid.strip().splitlines()[-1]
        docker("cp", f"{cid}:/testbed", str(co), check=True)
        docker("rm", cid)
    rmtree(base)
    shutil.copytree(co, base, symlinks=True)
    git(base, "config", "core.filemode", "false")
    git(base, "config", "core.autocrlf", "false")
    r = swe_record(bug["id"])
    (base / ".swebench_test_patch.diff").write_text(r["test_patch"], encoding="utf-8", newline="\n")
    git(base, "apply", ".swebench_test_patch.diff")
    (base / ".swebench_test_patch.diff").unlink()
    git(base, "add", "-A")
    git(base, "commit", "--no-verify", "-q", "-m", "swe-bench: apply test_patch")
    write_exclude(base, "swe")
    meta = base / ".swebench"
    meta.mkdir(exist_ok=True)
    f2p = json.loads(r["FAIL_TO_PASS"]) if isinstance(r["FAIL_TO_PASS"], str) else r["FAIL_TO_PASS"]
    p2p = json.loads(r["PASS_TO_PASS"]) if isinstance(r["PASS_TO_PASS"], str) else r["PASS_TO_PASS"]
    files = {"problem_statement.md": r.get("problem_statement", ""),
             "FAIL_TO_PASS.json": json.dumps(f2p, indent=2), "PASS_TO_PASS.json": json.dumps(p2p, indent=2),
             "instance_metadata.json": json.dumps({k: v for k, v in r.items() if k != "patch"}, indent=2, default=str),
             "test_cwd": MOUNT + "\n", "test_cmd": bug["test_cmd"] + "\n", "test_directives": bug["test_directives"] + "\n"}
    if (r.get("hints_text") or "").strip():
        files["hints.md"] = r["hints_text"].strip()
    for n, t in files.items():
        (meta / n).write_text(t, encoding="utf-8", newline="\n")
    for s in ("run_failing_tests.sh", "run_all_tests.sh"):
        lf_copy(SRC / "hunk-swe" / "swe_bench_utils" / "scripts" / s, base / s)
    (base / ".ready").write_text(git(base, "rev-parse", "HEAD").strip(), encoding="utf-8")
    return base


def prepare(bug_id):
    bug = dict(BUGS[bug_id], id=bug_id)
    return prepare_d4j(bug) if bug["kind"] == "d4j" else prepare_swe(bug)


def base_commit(bug_id):
    return (BUGS[bug_id]["base"] / ".ready").read_text(encoding="utf-8").strip()


def fresh_workspace(bug_id, slot, graph=None):
    """Copy of the base tree at E:\\w\\r<slot>; for arm U the class graph is copied in as class-graph.puml."""
    work = WORK / f"r{slot:02d}"
    rmtree(work)
    WORK.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BUGS[bug_id]["base"], work, symlinks=True, ignore=shutil.ignore_patterns(".ready"))
    if graph is not None:
        shutil.copy2(graph, work / "class-graph.puml")
    if git(work, "status", "--porcelain").strip():
        raise RuntimeError(f"{work}: tree not clean after copy")
    return work


D4J = "/opt/defects4j"
EMPTY_DIR, EMPTY_FILE = DATA / "empty", DATA / "empty-file"
# Amendment 1 (Zili Luo, 2026-11-18): in the AGENT's container, hide what reveals the fix: the framework's fix and
# test patches, the modified/loaded class lists, and the upstream git history (Closure repo + the repos zip).
# Defects4J's own startup check needs only project_repos/README, which stays. compile, test, export and the
# paper's trigger script were checked to work with these hidden (same 12 failures). The grading container is
# unchanged.
HIDE_D4J_DIRS = [f"{D4J}/framework/projects/Closure/patches", f"{D4J}/framework/projects/Closure/modified_classes",
                 f"{D4J}/framework/projects/Closure/loaded_classes", f"{D4J}/project_repos/closure-compiler.git"]
HIDE_D4J_FILES = [f"{D4J}/project_repos/defects4j-repos.zip"]


def start_box(bug_id, work, name, hide=False):
    """hide=True (agent runs only): mount empty placeholders over the fix-revealing Defects4J data."""
    cname = f"{name}-{uuid.uuid4().hex[:6]}"
    mounts = []
    if hide and BUGS[bug_id]["kind"] == "d4j":
        EMPTY_DIR.mkdir(parents=True, exist_ok=True)
        EMPTY_FILE.touch(exist_ok=True)
        for d in HIDE_D4J_DIRS:
            mounts += ["-v", f"{EMPTY_DIR}:{d}:ro"]
        for f in HIDE_D4J_FILES:
            mounts += ["-v", f"{EMPTY_FILE}:{f}:ro"]
    docker("run", "-d", "--name", cname, "--network", "none", "-v", f"{work}:{MOUNT}", "-w", MOUNT, *mounts,
           BUGS[bug_id]["image"], "sleep", "infinity", check=True)
    # the bind-mounted tree is owned by another uid; without this, git in the box refuses to read it
    docker("exec", cname, "git", "config", "--global", "--add", "safe.directory", "*")
    return cname


def exec_box(cname, command, timeout=1800):
    try:
        return docker("exec", "-w", MOUNT, cname, "bash", "-lc", command, timeout=timeout + 60)
    except subprocess.TimeoutExpired:
        return 124, "[timed out]"


def stop_box(cname):
    docker("rm", "-f", cname)


def verify(bug_id):
    """Buggy tree: the failing tests fail. Developer fix applied in a scratch copy: they pass, nothing else fails."""
    import grade
    bug = BUGS[bug_id]
    prepare(bug_id)
    out = DATA / "verify" / bug_id
    out.mkdir(parents=True, exist_ok=True)
    empty = grade.grade_patch(bug_id, "", out / "buggy")
    if bug["kind"] == "d4j":
        fix = docker("run", "--rm", "--network", "none", bug["image"], "bash", "-c",
                     "cd /opt/defects4j/framework/projects/Closure && cat patches/157.src.patch", check=True)[1]
        fixed = grade.grade_patch(bug_id, fix, out / "fixed", reverse=True, force=True)  # D4J stores fixed->buggy
    else:
        fixed = grade.grade_patch(bug_id, swe_record(bug_id)["patch"], out / "fixed", force=True)
    rec = {"bug": bug_id, "buggy": empty, "fixed": fixed}
    (out / "verify.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        print(prepare(sys.argv[2]))
    elif sys.argv[1] == "verify":
        verify(sys.argv[2])
