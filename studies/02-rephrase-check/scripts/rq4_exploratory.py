"""EXPLORATORY, added by Allen after labels were seen, not in analysis-plan.md.

RQ4: when the baseline test T0 is far from T1 and T2, are T1 and T2 correct?
Uses the frozen scorer, the frozen median split and each arm's own harness label.
"""
from collections import Counter

import analyze as an


def outcome(label, bug):
    """right, wrong, or none when that run has no harness result or no test."""
    if bug not in label:
        return "none"
    return "wrong" if label[bug] else "right"


def tally(rows, others, labels):
    """For each T0 cell, how many of the two other tests are right."""
    table = Counter()
    for r in rows:
        results = [outcome(labels[a], r["id"]) for a in others]
        t0 = "T0 wrong" if r["wrong"] else "T0 right"
        kind = f"{results.count('right')} of {sum(x != 'none' for x in results)} right"
        table[(t0, kind)] += 1
    return table


def show(name, rows, others, labels):
    print(f"\n{name}, {len(rows)} bugs")
    table = tally(rows, others, labels)
    for t0 in ("T0 right", "T0 wrong"):
        cells = {k[1]: v for k, v in table.items() if k[0] == t0}
        got = [outcome(labels[a], r["id"]) for r in rows if r["wrong"] == (t0 == "T0 wrong") for a in others]
        right, known = got.count("right"), sum(x != "none" for x in got)
        share = f"{right / known:.1%}" if known else "n/a"
        print(f"   {t0}: {sum(cells.values())} bugs; {dict(sorted(cells.items()))}; other tests right {right} of {known} ({share})")


def main():
    labels = {a: an.labels(a)[0] for a in an.ARMS}
    rows = [an.row_for(b, w) for b, w in sorted(labels["baseline"].items())]
    rows = [r for r in rows if r["S"] is not None]
    for name, key, others in (("rewrites, T1 and T2 = paraphrase and stepwise", "S", an.REWRITES),
                              ("repeats, T1 and T2 = repeat1 and repeat2", "R", an.REPEATS)):
        med, agree, dis = an.split(rows, key)
        print(f"\n=== {name}, median {med:.3f}")
        show("Disagree: T0 far from T1 and T2", dis, others, labels)
        show("Agree: T0 close to T1 and T2", agree, others, labels)
    print("\nEXPLORATORY: not in the frozen plan, no test applied.")


if __name__ == "__main__":
    main()
