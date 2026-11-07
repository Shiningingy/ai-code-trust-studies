"""Figures 2-5 of the report, from results/per_pr.csv and the run files (same data as analyze.py).

Usage: python figures.py   -> figures/fig2_effects.svg, fig3_per_pr.svg, fig4_stage1.svg, fig5_language.svg
"""
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyze import BOOT, SEED, boot_ci  # noqa: E402
from prepare import PRS  # noqa: E402

STUDY = Path(__file__).resolve().parent.parent
FIG = STUDY / "figures"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
HUMAN, AGENT, AQUA, BASE = "#2a78d6", "#eb6834", "#1baf7a", "#8a939b"
NAME = {"A": "Baseline", "B": "+HumanReview", "C": "+AgentReview"}

plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "svg.fonttype": "none",
                     "axes.spines.top": False, "axes.spines.right": False})


def data():
    df = pd.read_csv(STUDY / "results" / "per_pr.csv")
    return df


def wide(df, col):
    return df.pivot(index="pr", columns="arm", values=col)


def fig2(df):
    W, S, N = wide(df, "opus"), wide(df, "sonnet"), wide(df, "opus_no_ct")
    repo = df.drop_duplicates("pr").set_index("pr").loc[W.index, "repo"].values
    keep = [p for p in W.index if p not in ("ava-labs__avalanchego-4147", "grafana__mimir-12752")]
    rng = np.random.default_rng(SEED)  # same draw order as analyze.py, so the CIs match the report
    ci = {"BA": boot_ci((W.B - W.A).values, rng), "BC": boot_ci((W.B - W.C).values, rng)}
    ci["CA"] = boot_ci((W.C - W.A).values, rng)
    ci["BA_cl"] = boot_ci((W.B - W.A).values, rng, groups=repo)
    ci["BC_cl"] = boot_ci((W.B - W.C).values, rng, groups=repo)
    rng2 = np.random.default_rng(SEED + 1)  # extra rows, not reported as intervals in the text
    rows = []
    for g, (x, y), col in (("H1: +HumanReview vs Baseline", ("B", "A"), HUMAN),
                           ("H2: +HumanReview vs +AgentReview", ("B", "C"), HUMAN),
                           ("+AgentReview vs Baseline (secondary)", ("C", "A"), AGENT)):
        d = W[x] - W[y]
        k = x + y
        rows.append((g, "Opus inspector (primary)", d.mean(), *ci[k], True, col))
        if g.startswith("H"):
            rows.append((g, "clustered by repository", d.mean(), *ci[k + "_cl"], False, col))
            ds = S[x] - S[y]
            rows.append((g, "Sonnet inspector", ds.mean(), *boot_ci(ds.values, rng2), False, col))
            dn = (N[x] - N[y]).dropna()
            rows.append((g, "can't-tell items left out", dn.mean(), *boot_ci(dn.values, rng2), False, col))
            de = d.loc[keep]
            rows.append((g, "without the 2 empty-diff PRs", de.mean(), *boot_ci(de.values, rng2), False, col))
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    ypos, y, labels, groups = [], 0, [], []
    for i, r in enumerate(rows):
        if i == 0 or r[0] != rows[i - 1][0]:
            y += 0.9
            groups.append((y - 0.45, r[0]))
        ypos.append(y)
        labels.append(r[1])
        y += 1
    ypos = -np.array(ypos)
    for (g, lab, m, lo, hi, prim, col), yy in zip(rows, ypos):
        ax.plot([lo, hi], [yy, yy], color=col if prim else MUTED, lw=2.4 if prim else 1.6, solid_capstyle="round")
        ax.plot(m, yy, "o", ms=8 if prim else 6, color=col if prim else "white", mec=col if prim else MUTED, mew=1.6)
        ax.text(hi + 0.012, yy, f"{m:+.3f} [{lo:+.3f}, {hi:+.3f}]", va="center", fontsize=8.5, color=INK2)
    for gy, g in groups:
        ax.text(-0.12, -gy + 0.05, g, fontsize=10, fontweight="bold", color=INK, va="bottom")
    ax.axvline(0, color=INK2, lw=1, ls=(0, (4, 3)))
    ax.set_yticks(ypos, labels, fontsize=9)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-0.12, 0.42)
    ax.set_ylim(ypos.min() - 0.8, 0.6)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Mean paired difference in rubric score (95% bootstrap CI)")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_effects.svg")
    plt.close(fig)


def fig3(df):
    W = wide(df, "opus")
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.4), sharey=True)
    for ax, (x, y), title in ((axes[0], ("B", "A"), "+HumanReview − Baseline"), (axes[1], ("B", "C"), "+HumanReview − +AgentReview")):
        d = (W[x] - W[y]).sort_values(ascending=False).values
        cols = [HUMAN if v > 0 else (AGENT if v < 0 else MUTED) for v in d]
        hts = [v if v != 0 else 0.012 for v in d]
        ax.bar(np.arange(len(d)), hts, color=cols, width=0.8, edgecolor="white", linewidth=0.5)
        ax.axhline(0, color=INK2, lw=0.8)
        up, same, down = (d > 0).sum(), (d == 0).sum(), (d < 0).sum()
        ax.set_title(f"{title}\n{up} higher · {same} same · {down} lower; mean {d.mean():+.3f}, median {np.median(d):+.3f}",
                     fontsize=9.5, color=INK, loc="left")
        ax.set_xticks([])
        ax.set_xlabel("56 PRs, sorted by difference")
        ax.yaxis.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Difference in rubric score")
    fig.tight_layout()
    fig.savefig(FIG / "fig3_per_pr.svg")
    plt.close(fig)


def fig4(df):
    bad = re.compile(r'"Action":"build-fail"|undefined: |ImportError|has no attribute|cannot import name')
    counts = {}
    for a in "ABC":
        g = df[df.arm == a]
        res = int(g.resolved.sum())
        comp = sum(bool(bad.search((PRS / r.pr / "arms" / a / "stage1.log").read_text(encoding="utf-8", errors="replace")))
                   for r in g[~g.resolved].itertuples())
        counts[a] = (res, comp, len(g) - res - comp)
    fig, ax = plt.subplots(figsize=(7.6, 2.4))
    segs = (("resolved", AQUA), ("tests did not compile or import", AGENT), ("other failures", "#c9c8c2"))
    for i, a in enumerate("CBA"):
        left = 0
        for (lab, col), v in zip(segs, counts[a]):
            ax.barh(i, v, left=left, color=col, edgecolor="white", linewidth=2, height=0.62)
            if v >= 4:
                ax.text(left + v / 2, i, str(v), ha="center", va="center", fontsize=9,
                        color="white" if col == AGENT else INK)
            left += v
    ax.set_yticks(range(3), [NAME[a] for a in "CBA"])
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 56)
    ax.set_xlabel("PRs (of 56)")
    ax.spines["left"].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, c in segs]
    ax.legend(handles, [l for l, _ in segs], ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.32), fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_stage1.svg")
    plt.close(fig)
    return counts


def fig5(df):
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    series = (("Go (n = 27)", df[df.language == "Go"], AQUA, "o"), ("Python (n = 29)", df[df.language == "Python"], "#6250d6", "s"),
              ("All (n = 56)", df, INK2, "D"))
    xs = np.arange(3)
    for lab, g, col, mk in series:
        m = [g[g.arm == a].opus.mean() for a in "ABC"]
        ax.plot(xs, m, color=col, lw=2, marker=mk, ms=7, mec="white", mew=1.2)
        ax.text(2.08, m[2], lab, va="center", fontsize=9, color=INK2)
        dy = {"Go": -0.032, "Pyt": 0.016, "All": 0.016}[lab.split()[0][:3]]
        for x_, v in zip(xs, m):
            if x_ == 1:  # three series meet here: Python above, All to the left, Go below
                off = {"Go": (0, -0.034), "Pyt": (0, 0.016), "All": (-0.2, 0.012)}[lab.split()[0][:3]]
                ax.text(x_ + off[0], v + off[1], f"{v:.2f}", ha="center", fontsize=8, color=INK2)
            else:
                ax.text(x_, v + dy, f"{v:.2f}", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(xs, [NAME[a] for a in "ABC"])
    ax.set_xlim(-0.3, 2.75)
    ax.set_ylim(0.3, 0.72)
    ax.set_ylabel("Mean rubric score (Opus)")
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIG / "fig5_language.svg")
    plt.close(fig)


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    df = data()
    fig2(df)
    fig3(df)
    print("stage-1 counts (resolved, compile/import, other):", fig4(df))
    fig5(df)
    print("bootstrap draws", BOOT)
