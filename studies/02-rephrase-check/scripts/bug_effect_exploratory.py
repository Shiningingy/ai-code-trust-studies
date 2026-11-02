"""EXPLORATORY, raised by Allen after labels were seen, not in analysis-plan.md.

Does right or wrong depend mainly on the bug? And when T0 is wrong, does another run get it right?
Labels only: no test source is read for the first question.
"""
from collections import Counter

import numpy as np
from scipy.stats import fisher_exact

import analyze as an

DRAWS = 10000


def matrix(labels):
    """Bugs with a result in all five arms, as a bugs-by-arms array where 1 means right."""
    bugs = sorted(b for b in labels["baseline"] if all(b in labels[a] for a in an.ARMS))
    return bugs, np.array([[not labels[a][b] for a in an.ARMS] for b in bugs], int)


def icc(m):
    """Share of the variation in right or wrong that lies between bugs (one-way ANOVA estimator)."""
    n, k = m.shape
    means = m.mean(axis=1)
    between = k * ((means - m.mean()) ** 2).sum() / (n - 1)
    within = ((m - means[:, None]) ** 2).sum() / (n * (k - 1))
    return (between - within) / (between + (k - 1) * within)


def shuffled(m, rng, groups=None):
    """Each arm's labels shuffled across bugs, so arm rates hold and bug identity is broken."""
    out = m.copy()
    for arm in range(m.shape[1]):
        if groups is None:
            out[:, arm] = rng.permutation(m[:, arm])
        else:
            for g in set(groups):
                i = np.flatnonzero(np.array(groups) == g)
                out[i, arm] = rng.permutation(m[i, arm])
    return out


def unanimous(m):
    s = m.sum(axis=1)
    return int(((s == 0) | (s == m.shape[1])).sum())


def null(m, groups=None):
    rng = np.random.default_rng(an.SEED)
    draws = [shuffled(m, rng, groups) for _ in range(DRAWS)]
    u, i = np.array([unanimous(d) for d in draws]), np.array([icc(d) for d in draws])
    return u, i


def main():
    labels = {a: an.labels(a)[0] for a in an.ARMS}
    bugs, m = matrix(labels)
    print(f"bugs with all five results {len(bugs)}; right rate {m.mean():.3f}")
    print("runs right of 5, bugs:", dict(sorted(Counter(m.sum(axis=1).tolist()).items())))
    print(f"unanimous {unanimous(m)} of {len(bugs)}; ICC {icc(m):.3f}")
    for name, groups in (("shuffled across all bugs", None), ("shuffled within repo", [b.split("-")[0] for b in bugs])):
        u, i = null(m, groups)
        print(f"{name}: unanimous mean {u.mean():.1f}, 95% range [{np.percentile(u, 2.5):.0f}, {np.percentile(u, 97.5):.0f}]; "
              f"ICC mean {i.mean():.3f}; draws at or above observed: unanimous {int((u >= unanimous(m)).sum())}, ICC {int((i >= icc(m)).sum())} of {DRAWS}")

    rows = [an.row_for(b, w) for b, w in sorted(labels["baseline"].items())]
    rows = [r for r in rows if r["S"] is not None]
    med = an.split(rows, "S")[0]
    print(f"\nT0 wrong, did another run get it right? median {med:.3f}")
    table = {}
    for name, group in (("far", [r for r in rows if r["wrong"] and r["S"] > med]),
                        ("close", [r for r in rows if r["wrong"] and r["S"] <= med])):
        for arms, tag in ((an.REWRITES, "T1 or T2"), (an.ARMS[1:], "any of four")):
            hit = sum(any(labels[a].get(r["id"]) is False for a in arms) for r in group)
            table[(tag, name)] = (hit, len(group))
            print(f"   {name:5} {tag:11} {hit} of {len(group)} ({hit / len(group):.0%})")
    for tag in ("T1 or T2", "any of four"):
        (a, n), (b, k) = table[(tag, "far")], table[(tag, "close")]
        print(f"   {tag}: far vs close, Fisher p {fisher_exact([[a, n - a], [b, k - b]])[1]:.3f}")
    total = [r for r in rows if r["wrong"]]
    print(f"   all wrong T0: any of four right {sum(any(labels[a].get(r['id']) is False for a in an.ARMS[1:]) for r in total)} of {len(total)}")
    print("\nEXPLORATORY: not in the frozen plan, post hoc, small counts.")


if __name__ == "__main__":
    main()
