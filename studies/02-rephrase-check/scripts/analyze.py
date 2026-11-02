"""Study 02 analysis, as fixed in analysis-plan.md. Run from this folder once labels exist.

Tests are read as text and parsed with ast; nothing from them is executed.
"""
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import fisher_exact

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT / "pretest"), str(ROOT / "pipeline")]
from disagreement import Run, distance, score, tokens  # noqa: E402
from failure_values import failure_of  # noqa: E402
from run_pretest import DRAWS, SEED, auc, boot_ci, repo, stratified_auc, text_distance  # noqa: E402

RUNS = ROOT / "runs"
RESULTS = Path("E:/swt-scoring")
ARMS = ("baseline", "paraphrase", "stepwise", "repeat1", "repeat2")
REWRITES = ("paraphrase", "stepwise")
REPEATS = ("repeat1", "repeat2")
MIN_CLASS = 20


def source(arm, bug):
    """The accepted test of a run with a done marker, else None."""
    test = RUNS / arm / f"test_assertflip_{bug}.py"
    if not (RUNS / arm / "done" / f"{bug}.json").exists() or not test.exists():
        return None
    return test.read_text(encoding="utf-8", errors="replace")


def labels(arm):
    """Right or wrong per bug, plus the bugs the harness gave no result for."""
    path = RESULTS / "evaluation_results" / f"assertflip-{arm}.study02-{arm}.json"
    r = json.loads(path.read_text(encoding="utf-8"))
    return {**{b: False for b in r["resolved_ids"]}, **{b: True for b in r["unresolved_ids"]}}, r["error_ids"]


def added_f2p(arm, bug):
    path = RESULTS / "run_instance_swt_logs" / f"study02-{arm}" / f"assertflip-{arm}" / bug / "report.json"
    return json.loads(path.read_text(encoding="utf-8"))[bug].get("added_f2p", 0) > 0


def mean_or_none(values):
    return float(np.mean(values)) if values else None


def row_for(bug, wrong):
    src = {a: source(a, bug) for a in ARMS}
    base = Run(src["baseline"])
    fail = lambda a: failure_of(RUNS / a / f"attempts_{bug}.json")
    plain = {a: Run(src[a]) for a in ARMS[1:] if src[a]}
    timed = {a: Run(src[a], fail(a)) for a in ARMS[1:] if src[a]}
    base_timed = Run(src["baseline"], fail("baseline"))
    rw, rp = [a for a in REWRITES if a in plain], [a for a in REPEATS if a in plain]
    return dict(
        id=bug, wrong=wrong, size=len(tokens(base)), has_rewrites=len(rw) == 2,
        S=score(base, [plain[a] for a in rw]) if len(rw) == 2 else None,
        R=score(base, [plain[a] for a in rp]),
        R_silent1=(sum(distance(base, plain[a]) for a in rp) + 2 - len(rp)) / 2,
        S_runtime=score(base_timed, [timed[a] for a in rw]) if len(rw) == 2 else None,
        R_runtime=score(base_timed, [timed[a] for a in rp]),
        text=mean_or_none([text_distance(src["baseline"], src[a]) for a in rw]) if len(rw) == 2 else None,
    )


def split(rows, key):
    """Agree is at or below the median, as in the pretest."""
    med = float(np.median([r[key] for r in rows]))
    return med, [r for r in rows if r[key] <= med], [r for r in rows if r[key] > med]


def table(agree, dis):
    return [[sum(not r["wrong"] for r in agree), sum(r["wrong"] for r in agree)],
            [sum(not r["wrong"] for r in dis), sum(r["wrong"] for r in dis)]]


def wilson(k, n, z=1.959964):
    p, d = k / n, 1 + z * z / n
    mid, half = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return mid - half, mid + half


def verdict_rq1(right, wrong, p, gap):
    if right < MIN_CLASS or wrong < MIN_CLASS:
        return "INCONCLUSIVE: too few tests of one class for the gap the study was sized for"
    if p >= 0.05:
        return "NO LARGE EFFECT (not 'no effect')"
    return "SIGNAL" if gap > 0 else "REVERSED"


def boot_diff(rows, a, b):
    """Paired interval for AUROC(a) - AUROC(b): the same resampled bugs feed both."""
    rng = np.random.default_rng(SEED)
    by = defaultdict(list)
    for r in rows:
        by[repo(r)].append((r[a], r[b], r["wrong"]))
    groups = [tuple(np.array(c, float) for c in zip(*g)) for g in by.values()]
    out = []
    for _ in range(DRAWS):
        wa = pa = wb = pb = 0
        for x, y, w in groups:
            i = rng.integers(0, len(x), len(x))
            xx, yy, ww = x[i], y[i], w[i].astype(bool)
            s, n = auc(xx[ww], xx[~ww])
            wa, pa = wa + s, pa + n
            s, n = auc(yy[ww], yy[~ww])
            wb, pb = wb + s, pb + n
        out.append(wa / pa - wb / pb)
    return np.percentile(out, [2.5, 97.5])


def verdict_rq2(diff, lo, hi):
    if lo > 0:
        return "REWRITES STRONGER"
    if hi < 0:
        return "REPEATS STRONGER"
    return "NOT SHOWN STRONGER" + ("; plain re-running did as well here" if diff <= 0 else "")


def split_line(name, rows, key):
    med, agree, dis = split(rows, key)
    t = table(agree, dis)
    pa, pd = t[0][0] / len(agree), t[1][0] / len(dis)
    p = fisher_exact(t)[1]
    print(f"{name}: median {med:.3f}; agree {t[0]} precision {pa:.3f}; disagree {t[1]} precision {pd:.3f}; gap {pa - pd:.3f}; Fisher p {p:.2e}")
    return t, pa, pd, p


def discard_line(name, rows, key):
    _, agree, dis = split(rows, key)
    t = table(agree, dis)
    right = t[0][0] + t[1][0]
    lo0, hi0 = wilson(right, len(rows))
    lo1, hi1 = wilson(t[0][0], len(agree))
    print(f"{name}: precision {right / len(rows):.3f} [{lo0:.3f}, {hi0:.3f}] of {len(rows)} -> {t[0][0] / len(agree):.3f} [{lo1:.3f}, {hi1:.3f}] of {len(agree)}; correct lost {t[1][0]} of {right} ({t[1][0] / right:.1%})")


def auc_line(name, rows, key):
    v, _ = stratified_auc(rows, key, repo)
    lo, hi = boot_ci(rows, key, repo)
    print(f"{name}: n={sum(r[key] is not None for r in rows)} AUROC {v:.3f} CI [{lo:.3f}, {hi:.3f}]")
    return v, lo, hi


def analyze(rows):
    """Everything the plan reports, on rows with id, wrong, size and the scores."""
    main_rows = [r for r in rows if r["S"] is not None]
    right, wrong = sum(not r["wrong"] for r in main_rows), sum(r["wrong"] for r in main_rows)
    print(f"bugs in RQ1-3 {len(main_rows)}, right {right}, wrong {wrong}, precision {right / len(main_rows):.3f}")

    print("\nRQ1")
    _, pa, pd, p = split_line("rewrite score", main_rows, "S")
    print("VERDICT:", verdict_rq1(right, wrong, p, pa - pd))
    _, lo, hi = auc_line("secondary, repo-stratified", main_rows, "S")
    if p < 0.05 and lo <= 0.5 <= hi:
        print("NOTE: the Fisher signal may be a repo effect; the stratified interval includes 0.50")

    print("\nRQ2")
    a = stratified_auc(main_rows, "S", repo)[0]
    b = stratified_auc(main_rows, "R", repo)[0]
    lo, hi = boot_diff(main_rows, "S", "R")
    print(f"rewrite AUROC {a:.3f}, repeat AUROC {b:.3f}, difference {a - b:.3f} CI [{lo:.3f}, {hi:.3f}]")
    print("VERDICT:", verdict_rq2(a - b, lo, hi))
    split_line("repeat score", main_rows, "R")

    print("\nRQ3, discarding the disagree group")
    discard_line("rewrites", main_rows, "S")
    discard_line("repeats", main_rows, "R")
    discard_line("text distance", main_rows, "text")

    print("\nReported, cannot change a verdict")
    for name, key in (("text distance", "text"), ("runtime half", "S_runtime")):
        split_line(name, main_rows, key)
        auc_line(name, main_rows, key)
        v = stratified_auc(main_rows, key, repo)[0]
        lo, hi = boot_diff(main_rows, "S", key)
        print(f"   rewrite score minus {name}: {a - v:.3f} CI [{lo:.3f}, {hi:.3f}]")
    split_line("repeat, runtime half", main_rows, "R_runtime")
    auc_line("repeat, silent run as distance 1", main_rows, "R_silent1")
    auc_line("repeat only, all bugs", rows, "R")
    cut = np.percentile([r["size"] for r in main_rows], [100 / 3, 200 / 3])
    v = stratified_auc(main_rows, "S", lambda r: (repo(r), int(np.searchsorted(cut, r["size"]))))[0]
    print(f"repo x size tercile AUROC {v:.3f}; size alone {stratified_auc(main_rows, 'size', repo)[0]:.3f}")
    print("per-repo AUROC")
    for name in sorted({repo(r) for r in main_rows}):
        g = [r for r in main_rows if repo(r) == name]
        w, n = auc(np.array([r["S"] for r in g if r["wrong"]]), np.array([r["S"] for r in g if not r["wrong"]]))
        print(f"   {name:26} n={len(g):3} wrong={sum(r['wrong'] for r in g):3} AUROC {w / n if n else float('nan'):.3f}")
    return main_rows


def hand_sample(rows):
    med, agree, dis = split(rows, "S")
    rng = random.Random(SEED)
    cells = (("wrong, agree", agree, True), ("right, disagree", dis, False), ("wrong, disagree", dis, True), ("right, agree", agree, False))
    return {name: [(r["id"], round(r["S"], 3)) for r in rng.sample(sorted((x for x in g if x["wrong"] == w), key=lambda x: x["id"]), 3)]
            for name, g, w in cells}


def main():
    label = {a: labels(a) for a in ARMS}
    rows = []
    for bug, wrong in sorted(label["baseline"][0].items()):
        rows.append(row_for(bug, wrong))
    print("no harness result:", {a: label[a][1] for a in ARMS})
    main_rows = analyze(rows)

    print("\nSensitivity: label is added_f2p > 0")
    alt = [{**r, "wrong": not added_f2p("baseline", r["id"])} for r in main_rows]
    split_line("rewrite score", alt, "S")
    stuck = label["baseline"][1]
    if stuck:
        print("Sensitivity: baseline tests with no harness result counted as wrong")
        extra = [row_for(b, True) for b in stuck]
        split_line("rewrite score", main_rows + [r for r in extra if r["S"] is not None], "S")

    print("\nRight rate per arm, descriptive only")
    for a in ARMS:
        got, err = label[a]
        print(f"   {a:11} {sum(not w for w in got.values())} of {len(got)} ({sum(not w for w in got.values()) / len(got):.1%}); no result {len(err)}")

    print("\nhand-read sample", json.dumps(hand_sample(main_rows), indent=1))
    for f in ("analysis-plan.md", "pretest/disagreement.py", "pipeline/failure_values.py", "pretest/run_pretest.py", "scoring/analyze.py", "scoring/build_preds.py"):
        print(f, hashlib.sha256((ROOT / f).read_bytes()).hexdigest()[:16])
    json.dump(rows, open(HERE / "scores.json", "w"), indent=0)


if __name__ == "__main__":
    main()
