"""EXPLORATORY, raised by Allen after labels were seen, not in analysis-plan.md.

Is there too little room to rephrase, and does wording move outcomes more than re-running does?
Reads issues and rewrites as text. No model call: rewriter is imported for its masking rule only.
"""
import difflib
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

import analyze as an

sys.path.insert(0, str(an.ROOT / "pipeline"))
from rewriter import protect  # noqa: E402

DATASET = an.ROOT / "vendor" / "AssertFlip" / "datasets" / "SWT_Verified_Agentless_Test_Source_Skeleton.json"
REWRITES = an.ROOT / "rewrites"
TOKEN = re.compile(r"\[\[KEEP\d+\]\]")
DRAWS = 5000


def changed(a, b):
    return 1 - difflib.SequenceMatcher(None, a.split(), b.split(), autojunk=False).ratio()


def prose(text):
    """Words the rewriter was free to change."""
    return TOKEN.sub(" ", protect(text)[0])


def flip(a, b, bugs, labels):
    return np.array([labels[a][x] != labels[b][x] for x in bugs], float)


def main():
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    issues = {d["instance_id"]: d["problem_statement"] for d in data}
    labels = {a: an.labels(a)[0] for a in an.ARMS}
    bugs = sorted(b for b in labels["baseline"] if all(b in labels[a] for a in an.ARMS))

    words, free, moved = [], [], {"paraphrase": [], "stepwise": []}
    for b in bugs:
        words.append(len(issues[b].split()))
        free.append(len(prose(issues[b]).split()))
        kinds = json.loads((REWRITES / f"{b}.json").read_text(encoding="utf-8"))
        for k in moved:
            moved[k].append(changed(prose(issues[b]), prose(kinds[k])))
    words, free = np.array(words), np.array(free)
    print(f"{len(bugs)} bugs. Issue words: median {np.median(words):.0f}, quartiles {np.percentile(words, 25):.0f} to {np.percentile(words, 75):.0f}")
    print(f"Prose free to reword: median {np.median(free):.0f} words, quartiles {np.percentile(free, 25):.0f} to {np.percentile(free, 75):.0f}; under 30 words on {int((free < 30).sum())} bugs, under 15 on {int((free < 15).sum())}")
    print(f"Share of issue words free to reword: median {np.median(free / words):.0%}")
    for k, v in moved.items():
        print(f"{k}: prose changed, word-level, median {np.median(v):.2f}, quartiles {np.percentile(v, 25):.2f} to {np.percentile(v, 75):.2f}, minimum {min(v):.2f}")

    print("\nOutcome flips against T0 (right on one run, wrong on the other)")
    rw = (flip("baseline", "paraphrase", bugs, labels) + flip("baseline", "stepwise", bugs, labels)) / 2
    rp = (flip("baseline", "repeat1", bugs, labels) + flip("baseline", "repeat2", bugs, labels)) / 2
    for a in an.ARMS[1:]:
        print(f"   T0 vs {a:10} {int(flip('baseline', a, bugs, labels).sum())} of {len(bugs)}")
    print(f"   repeat1 vs repeat2    {int(flip('repeat1', 'repeat2', bugs, labels).sum())}; paraphrase vs stepwise {int(flip('paraphrase', 'stepwise', bugs, labels).sum())}")
    rng = np.random.default_rng(an.SEED)
    d = [(rw - rp)[rng.integers(0, len(bugs), len(bugs))].mean() for _ in range(DRAWS)]
    print(f"   mean flip rate rewrites {rw.mean():.3f}, repeats {rp.mean():.3f}, difference {rw.mean() - rp.mean():.3f}, 95% CI [{np.percentile(d, 2.5):.3f}, {np.percentile(d, 97.5):.3f}]")

    right = np.array([sum(not labels[a][b] for a in an.ARMS) for b in bugs])
    mixed = (right > 0) & (right < 5)
    print("\nRoom against outcome")
    print(f"   prose words vs runs right: Spearman {spearmanr(free, right)[0]:.3f}, p {spearmanr(free, right)[1]:.3f}")
    print(f"   prose words vs mixed bug: Spearman {spearmanr(free, mixed)[0]:.3f}, p {spearmanr(free, mixed)[1]:.3f}")
    print(f"   amount reworded vs flip: Spearman {spearmanr(np.mean(list(moved.values()), axis=0), rw)[0]:.3f}, p {spearmanr(np.mean(list(moved.values()), axis=0), rw)[1]:.3f}")
    cut = np.percentile(free, [100 / 3, 200 / 3])
    for name, g in (("short", free <= cut[0]), ("middle", (free > cut[0]) & (free <= cut[1])), ("long", free > cut[1])):
        print(f"   {name:6} prose (n={int(g.sum())}): right rate {right[g].mean() / 5:.1%}, mixed {mixed[g].mean():.1%}, unanimous wrong {int((right[g] == 0).sum())}")
    print("\nEXPLORATORY: not in the frozen plan, post hoc.")


if __name__ == "__main__":
    main()
