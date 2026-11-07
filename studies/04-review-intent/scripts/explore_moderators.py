"""Exploratory (not in the plan): which PR features go with larger gains? Per-PR features from the run files, task
type from tasktype.py, Spearman correlations and median splits against the per-PR rubric differences.

Usage: python explore_moderators.py  -> results/pr_features.csv, results/explore_moderators.txt
"""
import json
import re
from pathlib import Path

import pandas as pd
from scipy import stats

from prepare import PRS

STUDY = Path(__file__).resolve().parent.parent
TEST = re.compile(r"(^|/)(tests?|testing|testdata)/|_test\.(py|go)$|(^|/)test_[^/]*\.py$|conftest\.py$")
FEATS = ["src_lines", "src_files", "items", "human_comments", "agent_comments", "issue_words"]


def features():
    d = pd.read_csv(STUDY / "results" / "per_pr.csv")
    w = d.pivot(index="pr", columns="arm", values="opus")
    tt = pd.read_csv(STUDY / "results" / "pr_tasktype.csv").set_index("pr")["type"]
    rows = []
    for pid in w.index:
        m = json.loads((PRS / pid / "meta.json").read_text(encoding="utf-8"))
        lines, f, files = 0, None, set()
        for line in (PRS / pid / "merged.diff").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("diff --git"):
                f = line.split(" b/")[-1]
                if not TEST.search(f):
                    files.add(f)
            elif f and not TEST.search(f) and line[:1] in "+-" and not line.startswith(("+++", "---")):
                lines += 1
        rb = json.loads((PRS / pid / "review_B.json").read_text(encoding="utf-8"))
        rc = json.loads((PRS / pid / "review_C.json").read_text(encoding="utf-8"))
        items = len(json.loads((PRS / pid / "rubric.json").read_text(encoding="utf-8"))["items"])
        issue = " ".join(i.get("title", "") + " " + (i.get("body") or "") for i in m.get("issues", []))
        rows.append(dict(pr=pid, lang=m["language"], type=tt.get(pid), src_lines=lines, src_files=len(files),
                         items=items, human_comments=len(rb), agent_comments=len(rc), issue_words=len(issue.split()),
                         BA=w.B[pid] - w.A[pid], BC=w.B[pid] - w.C[pid], CA=w.C[pid] - w.A[pid]))
    return pd.DataFrame(rows)


def main():
    f = features()
    f.to_csv(STUDY / "results" / "pr_features.csv", index=False)
    L = ["EXPLORATORY, not in the plan. 18 correlations below; no correction for multiple tests.",
         "Feature ranges (min / median / max): " + "; ".join(
             f"{c} {f[c].min():.0f}/{f[c].median():.0f}/{f[c].max():.0f}" for c in FEATS), ""]
    for c in FEATS:
        parts = []
        for t in ("BA", "BC", "CA"):
            r, p = stats.spearmanr(f[c], f[t])
            parts.append(f"{t} rho {r:+.2f} p {p:.3f}")
        med = f[c].median()
        lo, hi = f[f[c] <= med], f[f[c] > med]
        L.append(f"{c}: " + " | ".join(parts) + f" | median split (<= {med:.0f} / >): BA {lo.BA.mean():+.3f}/{hi.BA.mean():+.3f}, "
                 f"BC {lo.BC.mean():+.3f}/{hi.BC.mean():+.3f} (n {len(lo)}/{len(hi)})")
    L.append("")
    for lang, g in f.groupby("lang"):
        r, p = stats.spearmanr(g.human_comments, g.BC)
        L.append(f"human_comments vs BC within {lang}: rho {r:+.2f} p {p:.3f} (n {len(g)})")
    L.append("")
    L.append("By task type (n, mean BA, mean CA, mean BC):")
    for t, g in f.groupby("type"):
        L.append(f"   {t}: n {len(g)}, BA {g.BA.mean():+.3f}, CA {g.CA.mean():+.3f}, BC {g.BC.mean():+.3f}")
    L.append(f"Kruskal-Wallis across types: BA p {stats.kruskal(*[g.BA for _, g in f.groupby('type')]).pvalue:.3f}, "
             f"BC p {stats.kruskal(*[g.BC for _, g in f.groupby('type')]).pvalue:.3f}, "
             f"CA p {stats.kruskal(*[g.CA for _, g in f.groupby('type')]).pvalue:.3f}")
    text = "\n".join(L)
    (STUDY / "results" / "explore_moderators.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
