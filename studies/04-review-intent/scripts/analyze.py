"""Analysis exactly as fixed in plan.md (Analysis). Unit = a main-run PR with all three arms scored.

Writes results/results.txt and results/per_pr.csv. Usage: python analyze.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from prepare import PRS

STUDY = Path(__file__).resolve().parent.parent
OUT = STUDY / "results"
SEED, BOOT = 20261107, 10_000
ARMS = ("A", "B", "C")


def load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def collect():
    done = []
    for name in ("main_state.json", "main_state_python.json", "main_state_go.json"):
        done += (load(STUDY / "runs" / name) or {}).get("done", [])
    rows, items = [], []
    for pid in done:
        d = PRS / pid
        meta = load(d / "meta.json")
        for arm in ARMS:
            a = d / "arms" / arm
            run, s1 = load(a / "run.json"), load(a / "stage1.json")
            io, isn = load(a / "inspect_opus.json"), load(a / "inspect_sonnet.json")
            sm = load(d / f"summary_{arm}.json") if arm != "A" else None
            if not (run and s1 and io and isn):
                continue
            ct = sum(i["verdict"] == "cant_tell" for i in io["items"])
            met = sum(i["verdict"] == "met" for i in io["items"])
            rows.append(dict(pr=pid, repo=meta["repo"], language=meta["language"], arm=arm,
                             opus=io["score"], sonnet=isn["score"], resolved=bool(s1["resolved"]),
                             opus_no_ct=met / (len(io["items"]) - ct) if len(io["items"]) > ct else np.nan,
                             tokens=run["total_tokens"], turns=run.get("num_turns"), seconds=run["seconds"],
                             status=run["status"], scrubs=(load(a / "scrub.json") or {}).get("scrubbed_lines"),
                             words=(sm or {}).get("words"), leak_first=(sm or {}).get("leak_first"),
                             rule_break_first=(sm or {}).get("rule_break_first"),
                             cut=(sm or {}).get("cut_to_length")))
            for x, y in zip(io["items"], isn["items"]):
                items.append(dict(pr=pid, arm=arm, id=x["id"], opus=x["verdict"], sonnet=y["verdict"]))
    df = pd.DataFrame(rows)
    complete = df.groupby("pr").arm.nunique()
    df = df[df.pr.isin(complete[complete == 3].index)]
    it = pd.DataFrame(items)
    if len(it):
        it = it[it.pr.isin(df.pr.unique())]
    return df, it


def wide(df, col):
    return df.pivot(index="pr", columns="arm", values=col)


def wilcoxon(x, y):
    d = (x - y).dropna()
    if (d != 0).sum() == 0:
        return np.nan, int((d != 0).sum())
    return stats.wilcoxon(d).pvalue, int((d != 0).sum())


def boot_ci(d, rng, groups=None):
    d = np.asarray(d)
    if groups is None:
        idx = rng.integers(0, len(d), (BOOT, len(d)))
        means = d[idx].mean(axis=1)
    else:
        g = pd.Series(d).groupby(np.asarray(groups)).apply(list)
        keys = list(g.index)
        means = []
        for _ in range(BOOT):
            pick = rng.integers(0, len(keys), len(keys))
            vals = [v for k in pick for v in g[keys[k]]]
            means.append(np.mean(vals))
        means = np.array(means)
    return np.percentile(means, [2.5, 97.5])


def holm(ps):
    order = np.argsort(ps)
    adj, running = [None] * len(ps), 0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def verdict(adj_p, mean_diff, n):
    if n < 30:
        return "Inconclusive (fewer than 30 complete PRs)"
    if adj_p < 0.05:
        return "Signal (B higher)" if mean_diff > 0 else "Reversed (B lower)"
    return "No large effect (not 'no effect'; see power note)"


def mcnemar(x, y):
    b = int(((x == 1) & (y == 0)).sum())
    c = int(((x == 0) & (y == 1)).sum())
    p = stats.binomtest(b, b + c, 0.5).pvalue if b + c else np.nan
    return b, c, p


def kappa(a, b, labels):
    a, b = list(a), list(b)
    n = len(a)
    if not n:
        return np.nan
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def main():
    OUT.mkdir(exist_ok=True)
    df, it = collect()
    df.to_csv(OUT / "per_pr.csv", index=False)
    L = []
    p = L.append
    n = df.pr.nunique()
    p(f"Study 04 results. Complete PRs (all three arms scored): {n}; repositories: {df.repo.nunique()}; "
      f"Python {df[df.language == 'Python'].pr.nunique()}, Go {df[df.language == 'Go'].pr.nunique()}.")
    if n == 0:
        (OUT / "results.txt").write_text("\n".join(L), encoding="utf-8")
        print("\n".join(L))
        return
    rng = np.random.default_rng(SEED)
    W = wide(df, "opus")
    repo = df.drop_duplicates("pr").set_index("pr").loc[W.index, "repo"]

    p("\n== Primary: rubric score (Opus inspector), share of items met ==")
    p("Mean per arm: " + ", ".join(f"{a} {W[a].mean():.3f}" for a in ARMS))
    res = {}
    for name, (x, y) in {"H1 B vs A": ("B", "A"), "H2 B vs C": ("B", "C")}.items():
        pval, nz = wilcoxon(W[x], W[y])
        d = W[x] - W[y]
        res[name] = (pval, d.mean(), boot_ci(d, rng), nz)
    adj = holm([res[k][0] for k in res])
    for (name, (pval, md, ci, nz)), ap in zip(res.items(), adj):
        p(f"{name}: mean diff {md:+.3f} (95% bootstrap CI {ci[0]:+.3f} to {ci[1]:+.3f}); Wilcoxon p={pval:.4f} "
          f"(non-zero pairs {nz}), Holm-adjusted p={ap:.4f} -> {verdict(ap, md, n)}")
    p("Power note (plan): with ~55 PRs a standardised paired effect of about 0.4 is detected ~80% of the time "
      "at the Holm-adjusted level; smaller effects often are not.")

    p("\n== Reported, cannot change a verdict ==")
    R = wide(df, "resolved").astype(int)
    p("1. Stage 1 resolved rate: " + ", ".join(f"{a} {R[a].mean():.3f} ({R[a].sum()}/{len(R)})" for a in ARMS))
    for x, y in (("B", "A"), ("B", "C")):
        b, c, pv = mcnemar(R[x], R[y])
        p(f"   McNemar exact {x} vs {y}: {x}-only {b}, {y}-only {c}, p={pv:.4f}")
    pval, nz = wilcoxon(W["C"], W["A"])
    d = W["C"] - W["A"]
    ci = boot_ci(d, rng)
    p(f"2. C vs A: mean diff {d.mean():+.3f} (CI {ci[0]:+.3f} to {ci[1]:+.3f}), Wilcoxon p={pval:.4f}")
    if len(it):
        two = lambda v: "met" if v == "met" else "not"
        k2 = kappa(it.opus.map(two), it.sonnet.map(two), ["met", "not"])
        k3 = kappa(it.opus, it.sonnet, ["met", "not_met", "cant_tell"])
        p(f"3. Inspector agreement, item level (n={len(it)}): kappa 2-class {k2:.3f}, 3-class {k3:.3f}")
    S = wide(df, "sonnet")
    sres = {}
    for name, (x, y) in {"H1 B vs A": ("B", "A"), "H2 B vs C": ("B", "C")}.items():
        pv, _ = wilcoxon(S[x], S[y])
        sres[name] = (pv, (S[x] - S[y]).mean())
    sadj = holm([sres[k][0] for k in sres])
    for (name, (pv, md)), ap, (pname, prim) in zip(sres.items(), sadj, zip(res, adj)):
        same = verdict(ap, md, n) == verdict(prim, res[pname][1], n)
        p(f"   On Sonnet scores, {name}: mean diff {md:+.3f}, Holm p={ap:.4f} -> {verdict(ap, md, n)}"
          + ("" if same else "  [VERDICT DIFFERS: result depends on the inspector]"))
    for name, (x, y) in {"H1 B vs A": ("B", "A"), "H2 B vs C": ("B", "C")}.items():
        ci = boot_ci((W[x] - W[y]).values, rng, groups=repo.values)
        p(f"4. {name}, CI clustered by repository: {ci[0]:+.3f} to {ci[1]:+.3f}")
    N = wide(df, "opus_no_ct")
    p("5. Rubric score without can't-tell items: " + ", ".join(f"{a} {N[a].mean():.3f}" for a in ARMS)
      + f"; B-A {(N['B'] - N['A']).mean():+.3f}, B-C {(N['B'] - N['C']).mean():+.3f}")
    p("6. Token efficiency (secondary):")
    for col in ("tokens", "turns", "seconds"):
        T = wide(df, col).astype(float)
        meds = ", ".join(f"{a} {T[a].median():,.0f}" for a in ARMS)
        pa, _ = wilcoxon(T["B"], T["A"])
        pc, _ = wilcoxon(T["B"], T["C"])
        p(f"   {col}: median {meds}; Wilcoxon B vs A p={pa:.4f}, B vs C p={pc:.4f}")
    p("7. By language (descriptive):")
    for lang, g in df.groupby("language"):
        w = wide(g, "opus")
        r = wide(g, "resolved").astype(int)
        p(f"   {lang} (n={len(w)}): rubric " + ", ".join(f"{a} {w[a].mean():.3f}" for a in ARMS)
          + "; resolved " + ", ".join(f"{a} {r[a].mean():.3f}" for a in ARMS))
    p("8. Per arm: summary words (median), leak on first answer, rule break on first answer, cut, scrubs, "
      "timeouts, refusals")
    for a in ARMS:
        g = df[df.arm == a]
        p(f"   {a}: words {g.words.median() if a != 'A' else '-'}, leak_first {int(g.leak_first.fillna(False).sum())}, "
          f"rule_break_first {int(g.rule_break_first.fillna(False).sum())}, cut {int(g.cut.fillna(False).sum())}, "
          f"scrubbed lines {int(g.scrubs.fillna(0).sum())}, timeouts {int((g.status == 'timeout').sum())}, "
          f"refusals {int((g.status == 'refusal').sum())}")
    ex = {}
    for name in ("main_state.json", "main_state_python.json", "main_state_go.json"):
        ex.update((load(STUDY / "runs" / name) or {}).get("excluded", {}))
    for lang in ("python", "go"):
        s = load(STUDY / "runs" / f"main_setup_{lang}.json") or {}
        ex.update(s.get("excluded", {}))
    p(f"\nExcluded PRs ({len(ex)}):")
    for k, v in sorted(ex.items()):
        p(f"   {k}: {v}")
    text = "\n".join(L)
    (OUT / "results.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
