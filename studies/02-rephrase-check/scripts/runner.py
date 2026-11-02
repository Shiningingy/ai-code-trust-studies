"""Pipeline runner: runs AssertFlip on bugs, one arm at a time, and keeps only valid runs.

Stands in for the authors' scripts/run_parallel.py, which assumes a POSIX shell and
Hugging Face. The container steps and the assertflip command are theirs, in the same
order. What changes is listed in the study's report: environment, one results folder
per arm, done markers, no fix in the instance file, a shared pip cache, and a longer
timeout. Test code runs inside containers only; the host handles text.
"""
import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from slicer import bug_order

HERE = Path(__file__).parent
ROOT = HERE.parent
AUTHORS = ROOT / "vendor" / "AssertFlip"
PIPELINE = HERE / "assertflip"
RUNS = ROOT / "runs"
LEDGER = RUNS / "ledger.jsonl"
REWRITES = ROOT / "rewrites"
DATASET = AUTHORS / "datasets" / "SWT_Verified_Agentless_Test_Source_Skeleton.json"
SERVICE = "http://127.0.0.1:8765"
FROM_CONTAINER = "http://host.docker.internal:8765/v1"

MODEL_LABEL = "openai/gpt-4o"
MAX_ATTEMPTS = 10
REGENERATIONS = 5
RUN_TIMEOUT = 7200
KEEP = ("instance_id", "problem_statement", "localized_code", "line_level_localization")
BAD_OUTPUT = ("Failed to send request", "APIConnectionError", "No response from LLM")
REWRITE_ARMS = ("paraphrase", "stepwise")
MAX_DECLINES = 3  # the batch stops here so a person can look; a declined run is never retried
CURRENT_PROMPT_FROM = 1793586549  # first call without the <think> request; earlier declines stay in the ledger but do not count

REPO_DIRS = {
    "flask": ("src/flask", "tests"), "django": ("django", "tests"),
    "matplotlib": ("lib/matplotlib", "lib/matplotlib/tests"), "pylint": ("pylint", "tests"),
    "pytest": ("src/_pytest", "testing"), "requests": ("requests", "tests"),
    "scikit-learn": ("sklearn", "sklearn/tests"), "seaborn": ("seaborn", "tests"),
    "sphinx": ("sphinx", "tests"), "sympy": ("sympy", "sympy/testing"),
    "astropy": ("astropy", "astropy/tests"), "xarray": ("xarray", "xarray/tests"),
}


def load_constants():
    spec = importlib.util.spec_from_file_location("assertflip_constants", AUTHORS / "scripts" / "constants.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MAP_REPO_VERSION_TO_SPECS, mod.CUSTOM_INSTRUCTIONS


def tests_dir(inst):
    """The authors' get_test_dir, reading the test patch from the dataset file."""
    repo = inst["repo"].split("/")[-1]
    if inst["instance_id"] in ("psf__requests-1142", "psf__requests-1921", "psf__requests-2931"):
        return "."
    if repo == "sympy":
        for part in re.split(r"(?m)^(?=diff --git )", inst["test_patch"]):
            m = re.match(r"diff --git a/\S+ b/(\S+)", part)
            if m and m.group(1).endswith(".py") and "\nnew file mode" not in part.split("@@")[0]:
                return str(Path(m.group(1)).parent.as_posix())
    return REPO_DIRS[repo][1]


def container_instance(inst, issue):
    """Only what AssertFlip reads. The fix and the benchmark's tests stay out of the container."""
    return {**{k: inst[k] for k in KEEP}, "problem_statement": issue}


def run_problem(exit_code, timed_out, output, calls):
    """None if the run counts, otherwise why not. The ledger decides, not AssertFlip."""
    if not calls:
        return "no calls in the ledger"
    bad = [c for c in calls if c["outcome"] != "ok"]
    if bad:
        return f"{len(bad)} failed or refused calls"
    if timed_out:
        return None
    if exit_code != 0:
        return f"exit {exit_code}"
    for text in BAD_OUTPUT:
        if text in output:
            return f"output contains {text!r}"
    return None


def was_declined(calls):
    return any(c["outcome"] == "model_declined" for c in calls)


def ledger_rows():
    if not LEDGER.exists():
        return []
    return [json.loads(x) for x in open(LEDGER, encoding="utf-8")]


def calls_for(token):
    return [r for r in ledger_rows() if r.get("token") == token]


def declines_so_far():
    return sum(r["outcome"] == "model_declined" and r["t"] >= CURRENT_PROMPT_FROM for r in ledger_rows())


def service_status():
    with urllib.request.urlopen(SERVICE + "/status", timeout=10) as r:
        return json.load(r)


def service_reset():
    urllib.request.urlopen(urllib.request.Request(SERVICE + "/reset", method="POST"), timeout=10).read()


def docker(*args, **kw):
    return subprocess.run(["docker", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def bash_command(inst, specs, instance_file):
    repo = inst["repo"].split("/")[-1]
    source_dir = REPO_DIRS[repo][0]
    version = str(inst["version"])
    table = specs[inst["repo"]]
    spec = table[version] if version in table else table[version + "0"]
    test_cmd = spec["test_cmd"]
    if isinstance(test_cmd, list):
        test_cmd = test_cmd[-1]
    evals = spec.get("eval_commands", [])
    env_export = "export PYTHONWARNINGS=ignore::UserWarning,ignore::SyntaxWarning && " if repo == "sympy" else ""
    if repo == "sympy":
        test_cmd = "/testbed/bin/test -C --verbose"
    quoted = "'" + test_cmd.replace("'", "'\\''") + "'"
    eval_str = " && ".join(evals) + " && " if evals else ""
    return (
        f"{env_export}{eval_str}pip install /assertflip && pip install hypothesis && "
        f"assertflip --test-cmd {quoted} --source-dir {source_dir} --tests-dir {tests_dir(inst)} "
        f"--max-attempts {MAX_ATTEMPTS} --dataset /results/{instance_file} --model {MODEL_LABEL} "
        f"--phase pass_then_invert --max-generation-retries {REGENERATIONS} --max-attempts {MAX_ATTEMPTS} "
    )


def run_files(folder, bug):
    names = [f"attempts_{bug}.json", f"llm_calls_{bug}.jsonl", f"llm_calls_{bug}-validation.jsonl",
             f"test_assertflip_{bug}.py", f"{bug}.json", f"{bug}.log"]
    return [folder / n for n in names if (folder / n).exists()]


def process(inst, arm, issue, specs, custom):
    bug = inst["instance_id"]
    folder = RUNS / arm
    done = folder / "done" / f"{bug}.json"
    if done.exists():
        return bug, "skipped"
    if service_status()["tripped"] or declines_so_far() >= MAX_DECLINES:
        return bug, "stopped"

    token = f"run-{arm}-{bug}-{uuid.uuid4().hex[:8]}"
    image = "swebench/sweb.eval.x86_64." + bug.replace("__", "_1776_")
    repo = inst["repo"].split("/")[-1]
    (folder / f"{bug}.json").write_text(json.dumps(container_instance(inst, issue), indent=1), encoding="utf-8")
    started = time.time()
    if not docker("images", "-q", image).stdout.strip():
        pulled = docker("pull", image)
        if pulled.returncode:
            return bug, f"pull failed: {pulled.stderr[-300:]}"
    pull_seconds = round(time.time() - started, 1)

    env = ["-e", f"OPENAI_API_KEY={token}", "-e", f"OPENAI_API_BASE={FROM_CONTAINER}", "-e", f"PROJECT_NAME={repo}"]
    if custom.get(repo):
        env += ["-e", f"CUSTOM_INSTRUCTIONS={custom[repo]}"]
    name = f"af-{uuid.uuid4().hex[:10]}"
    run = docker("run", "-d", "--name", name, *env, "--add-host", "host.docker.internal:host-gateway",
                 "-v", f"{folder.resolve()}:/results", "-v", "af-pip-cache:/root/.cache/pip", image, "sleep", "infinity")
    if run.returncode:
        return bug, f"docker run failed: {run.stderr[-300:]}"
    output, exit_code, timed_out = "", None, False
    try:
        docker("cp", str(PIPELINE), f"{name}:/assertflip")
        prep = "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed && python -m pip install coverage"
        docker("exec", name, "bash", "-c", prep)
        try:
            p = docker("exec", name, "bash", "-c", bash_command(inst, specs, f"{bug}.json"), timeout=RUN_TIMEOUT)
            output, exit_code = p.stdout + p.stderr, p.returncode
        except subprocess.TimeoutExpired as e:
            output, timed_out = str(e.stdout or "") + str(e.stderr or ""), True
        generated = f"/testbed/{tests_dir(inst)}/test_assertflip_{bug}.py"
        if docker("exec", name, "test", "-f", generated).returncode == 0:
            docker("cp", f"{name}:{generated}", str(folder / f"test_assertflip_{bug}.py"))
    finally:
        docker("rm", "-f", name)

    (folder / f"{bug}.log").write_text(output, encoding="utf-8")
    calls = calls_for(token)
    gone = was_declined(calls)
    problem = None if gone else run_problem(exit_code, timed_out, output, calls)
    if problem:
        aside = folder / "rejected" / f"{bug}-{token[-8:]}"
        aside.mkdir(parents=True)
        for f in run_files(folder, bug):
            shutil.move(str(f), aside / f.name)
        (aside / "why.txt").write_text(problem, encoding="utf-8")
        return bug, f"rejected: {problem}"

    record = {"bug": bug, "arm": arm, "token": token, "exit": exit_code, "timed_out": timed_out,
              "seconds": round(time.time() - started, 1), "pull_seconds": pull_seconds, "calls": len(calls),
              "emitted": (folder / f"test_assertflip_{bug}.py").exists() and not gone, "declined": gone,
              "cost_estimate_usd": round(sum(c.get("total_cost_usd") or 0 for c in calls), 4)}
    done.write_text(json.dumps(record, indent=1), encoding="utf-8")
    if gone:
        return bug, "declined"
    return bug, "emitted" if record["emitted"] else "silent"


def issue_for(inst, arm):
    if arm in REWRITE_ARMS:
        return json.loads((REWRITES / f"{inst['instance_id']}.json").read_text(encoding="utf-8"))[arm]
    return inst["problem_statement"]


def with_rewrites(ids, arm):
    """A bug whose rewrite failed the screen three times gets no rewrite arms."""
    if arm not in REWRITE_ARMS:
        return ids
    kept = [i for i in ids if (REWRITES / f"{i}.json").exists()]
    for i in ids:
        if i not in kept:
            print(f"{i}: no screened rewrite, skipped", flush=True)
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--first", type=int, help="first N bugs of the slice order")
    ap.add_argument("--bugs", nargs="*", help="exact bug ids, for tests")
    ap.add_argument("--accepted-in", help="keep only bugs where this arm emitted a test")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    a = ap.parse_args()
    globals()["LEDGER"] = a.ledger

    bugs = json.load(open(DATASET, encoding="utf-8"))
    by_id = {b["instance_id"]: b for b in bugs}
    ids = a.bugs or bug_order(bugs)[:a.first]
    if a.accepted_in:
        marks = (json.loads((RUNS / a.accepted_in / "done" / f"{i}.json").read_text()) for i in ids
                 if (RUNS / a.accepted_in / "done" / f"{i}.json").exists())
        ids = [m["bug"] for m in marks if m["emitted"]]
    ids = with_rewrites(ids, a.arm)
    specs, custom = load_constants()
    (RUNS / a.arm / "done").mkdir(parents=True, exist_ok=True)
    service_reset()

    outcomes = {}
    with ThreadPoolExecutor(a.workers) as pool:
        jobs = {i: pool.submit(process, by_id[i], a.arm, issue_for(by_id[i], a.arm), specs, custom) for i in ids}
        for i, job in jobs.items():
            bug, outcome = job.result()
            outcomes[bug] = outcome
            print(f"{bug}: {outcome}", flush=True)
    counts = {}
    for o in outcomes.values():
        k = o.split(":")[0]
        counts[k] = counts.get(k, 0) + 1
    print(a.arm, counts, flush=True)
    sys.exit(0 if not (set(counts) - {"skipped", "emitted", "silent", "declined"}) else 1)


if __name__ == "__main__":
    main()
