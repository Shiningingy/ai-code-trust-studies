"""Free pretest: does disagreement among the authors' variant runs predict wrong baseline tests?

The plan is fixed in PREREG.md. Run from this folder. Prediction files are read as
text and parsed with ast; nothing from them is executed.
"""
import ast
import difflib
import hashlib
import io
import json
import random
import tokenize as tk
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.stats import fisher_exact, rankdata

from disagreement import Run, distance, score, tokens

HERE = Path(__file__).parent
PKG = HERE.parent / "vendor" / "AssertFlip"
PREDS = PKG / "preds_files"
OTHERS = {
    "perfloc": "ablation-perfect-localization-preds.jsonl",
    "noplan": "ablation-no-planning-preds.jsonl",
    "noval": "ablation-no-validation-preds.jsonl",
    "regen5": "5-regeneration-attempts-preds.jsonl",
}
SEED = 20261101
DRAWS = 5000


def load(name):
    runs = {}
    for line in open(PREDS / name, encoding="utf-8"):
        r = json.loads(line)
        lines = r["model_patch"].splitlines()
        runs[r["instance_id"]] = "\n".join(x[1:] for x in lines if x.startswith("+") and not x.startswith("+++")) + "\n"
    return runs


def no_comments(src):
    return ast.unparse(ast.parse(src))


def text_distance(a, b):
    return 1 - difflib.SequenceMatcher(None, no_comments(a).split(), no_comments(b).split(), autojunk=False).ratio()


def auc(wrong_scores, right_scores):
    """Rank AUROC for one stratum, returned as (wins, pairs)."""
    n1, n0 = len(wrong_scores), len(right_scores)
    if not n1 or not n0:
        return 0.0, 0
    ranks = rankdata(np.concatenate([wrong_scores, right_scores]))
    return ranks[:n1].sum() - n1 * (n1 + 1) / 2, n1 * n0


def stratified_auc(rows, key, strata):
    wins = pairs = 0
    for s in {strata(r) for r in rows}:
        g = [r for r in rows if strata(r) == s and r[key] is not None]
        w, p = auc(np.array([r[key] for r in g if r["wrong"]], float), np.array([r[key] for r in g if not r["wrong"]], float))
        wins += w
        pairs += p
    return wins / pairs if pairs else float("nan"), pairs


def boot_ci(rows, key, strata):
    rng = np.random.default_rng(SEED)
    by = defaultdict(list)
    for r in rows:
        if r[key] is not None:
            by[strata(r)].append((r[key], r["wrong"]))
    groups = [(np.array([v for v, _ in g], float), np.array([y for _, y in g], bool)) for g in by.values()]
    out = []
    for _ in range(DRAWS):
        wins = pairs = 0
        for v, y in groups:
            i = rng.integers(0, len(v), len(v))
            vv, yy = v[i], y[i]
            w, p = auc(vv[yy], vv[~yy])
            wins += w
            pairs += p
        out.append(wins / pairs)
    return np.percentile(out, [2.5, 97.5])


def repo(r):
    return r["id"].split("-")[0]


def main():
    base = load("assertflip-default-preds.jsonl")
    others = {k: load(v) for k, v in OTHERS.items()}
    labels = json.load(open(PKG / "evaluation_results_on_SWT_Bench" / "assertFlip_default_run.json", encoding="utf-8"))
    good, bad = set(labels["resolved_ids"]), set(labels["unresolved_ids"])
    assert set(base) == good | bad and not good & bad

    rows = []
    for i, src in base.items():
        b = Run(src)
        emitted = {k: Run(v[i]) for k, v in others.items() if i in v}
        row = dict(id=i, wrong=i in bad, size=len(tokens(b)), silent=4 - len(emitted))
        row["S"] = score(b, list(emitted.values()))
        row["S_silent1"] = (sum(distance(b, o) for o in emitted.values()) + row["silent"]) / 4
        row["text"] = np.mean([text_distance(src, o.source) for o in emitted.values()]) if emitted else None
        for k in OTHERS:
            row["d_" + k] = distance(b, emitted[k]) if k in emitted else None
        for x, y in combinations(OTHERS, 2):
            pair = [emitted[k] for k in (x, y) if k in emitted]
            row[f"p_{x}_{y}"] = score(b, pair) if len(pair) == 2 else None
        rows.append(row)

    usable = [r for r in rows if r["S"] is not None]
    wrong = sum(r["wrong"] for r in usable)
    print(f"baseline tests {len(rows)}, usable {len(usable)}, wrong {wrong}, right {len(usable) - wrong}, base precision {1 - wrong / len(usable):.3f}")
    print("repos", Counter(repo(r) for r in usable).most_common())
    print("S quartiles", np.round(np.percentile([r["S"] for r in usable], [25, 50, 75]), 3))

    a, n = stratified_auc(usable, "S", repo)
    lo, hi = boot_ci(usable, "S", repo)
    print(f"\nPRIMARY repo-stratified AUROC {a:.3f} CI [{lo:.3f}, {hi:.3f}] pairs {n}")
    print("GATE:", "PASS" if lo > 0.5 else "FAIL")

    med = float(np.median([r["S"] for r in usable]))
    agree = [r for r in usable if r["S"] <= med]
    dis = [r for r in usable if r["S"] > med]
    t = [[sum(not r["wrong"] for r in agree), sum(r["wrong"] for r in agree)], [sum(not r["wrong"] for r in dis), sum(r["wrong"] for r in dis)]]
    print(f"\n1. median split at {med:.3f}: agree {t[0]} precision {t[0][0] / len(agree):.3f}; disagree {t[1]} precision {t[1][0] / len(dis):.3f}; gap {t[0][0] / len(agree) - t[1][0] / len(dis):.3f}; Fisher p {fisher_exact(t)[1]:.2e}")
    print(f"   discard disagree: precision {t[0][0] / len(agree):.3f} vs {1 - wrong / len(usable):.3f}; correct lost {t[1][0]} of {t[0][0] + t[1][0]}")

    print(f"\n2. unstratified AUROC {stratified_auc(usable, 'S', lambda r: 0)[0]:.3f}")

    print("\n3. single runs (repo-stratified)")
    for k in OTHERS:
        g = [r for r in usable if r["d_" + k] is not None]
        print(f"   {k:8} n={len(g)} AUROC {stratified_auc(g, 'd_' + k, repo)[0]:.3f}")
    pair_keys = [f"p_{x}_{y}" for x, y in combinations(OTHERS, 2)]
    vals = [stratified_auc(usable, k, repo)[0] for k in pair_keys]
    for k, v in zip(pair_keys, vals):
        print(f"   {k:20} AUROC {v:.3f}")
    print(f"   mean over six pairs {np.mean(vals):.3f}")

    cut = np.percentile([r["size"] for r in usable], [100 / 3, 200 / 3])
    print(f"\n4. repo x size tercile (cuts {cut}) AUROC {stratified_auc(usable, 'S', lambda r: (repo(r), int(np.searchsorted(cut, r['size']))))[0]:.3f}")
    print(f"   size alone, repo-stratified {stratified_auc(usable, 'size', repo)[0]:.3f}")

    print("\n5. comparators (repo-stratified, all with CI)")
    for k in ("silent", "S_silent1", "text"):
        g = [r for r in rows if r[k] is not None]
        v, _ = stratified_auc(g, k, repo)
        l, h = boot_ci(g, k, repo)
        print(f"   {k:10} n={len(g)} AUROC {v:.3f} CI [{l:.3f}, {h:.3f}]")
    print("   silent count by wrong rate", sorted((s, sum(r['wrong'] for r in rows if r['silent'] == s), sum(r['silent'] == s for r in rows)) for s in {r['silent'] for r in rows}))

    print("\nper-repo AUROC")
    for name, n in Counter(repo(r) for r in usable).most_common():
        g = [r for r in usable if repo(r) == name]
        w, p = auc(np.array([r["S"] for r in g if r["wrong"]]), np.array([r["S"] for r in g if not r["wrong"]]))
        print(f"   {name:28} n={n:3} wrong={sum(r['wrong'] for r in g):3} AUROC {w / p if p else float('nan'):.3f}")

    case = next(r for r in usable if r["id"] == "django__django-16333")
    print("\ncase 2 score", round(case["S"], 3), "wrong", case["wrong"], "percentile", round(np.mean([r["S"] <= case["S"] for r in usable]), 3))

    # hand-read sample, outcome-stratified, seeded
    rng = random.Random(SEED)
    picks = {}
    for name, g in (("wrong, agreed", [r for r in dis + agree if r["wrong"] and r["S"] <= med]),
                    ("right, disagreed", [r for r in dis + agree if not r["wrong"] and r["S"] > med]),
                    ("wrong, disagreed", [r for r in dis + agree if r["wrong"] and r["S"] > med]),
                    ("right, agreed", [r for r in dis + agree if not r["wrong"] and r["S"] <= med])):
        picks[name] = [(r["id"], round(r["S"], 3)) for r in rng.sample(sorted(g, key=lambda r: r["id"]), 3)]
    print("\nhand-read sample", json.dumps(picks, indent=1))

    for f in ("PREREG.md", "disagreement.py", "run_pretest.py"):
        print(f, hashlib.sha256((HERE / f).read_bytes()).hexdigest()[:16])
    json.dump([{k: (float(v) if isinstance(v, np.floating) else v) for k, v in r.items()} for r in rows], open(HERE / "scores.json", "w"), indent=0)


if __name__ == "__main__":
    main()
