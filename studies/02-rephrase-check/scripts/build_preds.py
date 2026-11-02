"""One SWT-Bench predictions file per arm, as the authors' generate_preds_phases.py makes them.

make_patch and rewrite_patch_as_new_file are theirs. Their script loads the dataset at import,
so the two are copied here, with two changes that do not alter a patch: bytes are written so that
Windows cannot add carriage returns, and split("\n") replaces splitlines(), which also splits on
form feeds. Tests are text here: nothing from them is executed.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
RUNS = HERE.parent / "runs"
ARMS = ("baseline", "paraphrase", "stepwise", "repeat1", "repeat2")
REPO_TO_PREFIX = {
    "astropy": "astropy/tests/test_assertflip_",
    "django": "tests/test_assertflip_",
    "matplotlib": "lib/matplotlib/tests/test_assertflip_",
    "pallets": "tests/test_assertflip_",
    "mwaskom_seaborn": "tests/test_assertflip_",
    "psf": "test_assertflip_",
    "pydata": "xarray/tests/test_assertflip_",
    "pylint-dev": "tests/test_assertflip_",
    "pytest-dev": "testing/test_assertflip_",
    "scikit-learn": "sklearn/tests/test_assertflip_",
    "sphinx-doc": "tests/test_assertflip_",
    "sympy": "sympy/polys/tests/test_assertflip_",
}


def target_path(bug):
    return f"{REPO_TO_PREFIX.get(bug.split('__')[0], 'tests/test_assertflip_')}{bug}.py"


def rewrite_patch_as_new_file(raw_patch, target):
    out = []
    for line in raw_patch.split("\n"):
        if line.startswith("diff --git"):
            out += [f"diff --git a/dev/null b/{target}", "new file mode 100644"]
        elif line.startswith("---"):
            out.append("--- /dev/null")
        elif line.startswith("+++"):
            out.append(f"+++ b/{target}")
        else:
            out.append(line)
    return "\n".join(out)


def make_patch(test_code, bug):
    with tempfile.TemporaryDirectory() as tmp:
        old, new = Path(tmp) / f"{bug}_empty.py", Path(tmp) / f"{bug}_test.py"
        old.write_bytes(b"")
        new.write_bytes(test_code.encode("utf-8"))
        result = subprocess.run(["git", "diff", "--no-index", "--minimal", str(old), str(new)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode("utf-8").strip()


def added_lines(patch):
    """The test as a reader of the patch gets it back."""
    return [x[1:] for x in patch.split("\n") if x.startswith("+") and not x.startswith("+++")]


def final_test(arm, bug):
    """The accepted test, or None for a silent run. Must match the stored test file."""
    attempts = json.loads((RUNS / arm / f"attempts_{bug}.json").read_text(encoding="utf-8"))
    last = next((a for a in attempts if a.get("phase") == "terminating" and "final_test" in a), None)
    if last is None:
        return None
    stored = (RUNS / arm / f"test_assertflip_{bug}.py").read_text(encoding="utf-8")
    assert stored.strip() == last["final_test"].strip(), (arm, bug)
    return last["final_test"]


def predictions(arm):
    done = sorted(p.stem for p in (RUNS / arm / "done").glob("*.json"))
    preds, silent = [], []
    for bug in done:
        test = final_test(arm, bug)
        if test is None:
            silent.append(bug)
            continue
        patch = rewrite_patch_as_new_file(make_patch(test, bug), target_path(bug))
        assert added_lines(patch) == test.rstrip("\n").split("\n"), (arm, bug)
        preds.append({"instance_id": bug, "model_name_or_path": f"assertflip-{arm}", "model_patch": patch})
    return preds, silent


def main():
    for arm in ARMS:
        preds, silent = predictions(arm)
        with open(HERE / "preds" / f"{arm}.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for p in preds:
                f.write(json.dumps(p) + "\n")
        print(arm, len(preds), "tests, silent", silent)


if __name__ == "__main__":
    sys.exit(main())
