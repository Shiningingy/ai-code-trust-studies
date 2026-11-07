"""Follow-up 8.3: how much of the rubric each review summary covers (exploratory, no agent runs).

For each complete main-run PR and each summary (B = +HumanReview, C = +AgentReview), one Opus call marks which rubric
items the summary states or clearly implies. Writes runs/prs/<id>/coverage.json; state runs/followup_coverage.json.

Usage: python followup_coverage.py [--prs id1,id2] [--max-prs N]     then: python followup_coverage.py --report
"""
import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import llm
from prepare import PRS
from summarise import issue_text

STUDY = Path(__file__).resolve().parent.parent
STATE = STUDY / "runs" / "followup_coverage.json"
OUT = STUDY / "results"

SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {
    "type": "array", "items": {"type": "object", "required": ["id", "covered", "evidence"], "properties": {
        "id": {"type": "string"}, "covered": {"type": "string", "enum": ["yes", "no"]},
        "evidence": {"type": "string"}}}}}}

PROMPT = """Below are an issue in the {repo} repository, a rubric of behaviours that a resolution of the issue should have, and a short guidance text written for a developer before they implement the change.

<issue>
{issue}
</issue>

<rubric>
{rubric}
</rubric>

<guidance>
{summary}
</guidance>

For every rubric item decide whether the guidance states the behaviour or clearly implies it, so that a developer following the guidance would be led to it: "yes" or "no". The issue alone does not count; only what the guidance adds or repeats. Give evidence as a short quote from the guidance (for "yes") or one sentence (for "no")."""


def done_prs():
    out = []
    for lang in ("python", "go"):
        out += json.loads((STUDY / "runs" / f"main_state_{lang}.json").read_text(encoding="utf-8"))["done"]
    return sorted(out)


def tag(pid):
    d = PRS / pid
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    items = json.loads((d / "rubric.json").read_text(encoding="utf-8"))["items"]
    rtext = "\n".join(f"{i['id']}: {i['behaviour']}" for i in items)
    rec = {}
    for side in ("B", "C"):
        s = json.loads((d / f"summary_{side}.json").read_text(encoding="utf-8"))
        r = llm.call(PROMPT.format(repo=meta["repo"], issue=issue_text(meta), rubric=rtext, summary=s["text"]),
                     role="coverage", pr=pid, tag=side, model=llm.OPUS, effort="medium", schema=SCHEMA, timeout=600)
        if r["status"] != "ok" or not r["structured"]:
            raise RuntimeError(f"coverage {side} {r['status']} for {pid}")
        got = {i["id"]: i for i in r["structured"]["items"]}
        rec[side] = [got.get(i["id"], {"id": i["id"], "covered": "no", "evidence": "item not returned"}) for i in items]
    (d / "coverage.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")


def run(prs=None, max_prs=None):
    s = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"done": [], "errors": {}}
    n = 0
    for pid in prs or done_prs():
        if pid in s["done"]:
            continue
        try:
            tag(pid)
            s["done"].append(pid)
            print("DONE", pid, f"({len(s['done'])})", flush=True)
        except Exception as e:  # noqa: BLE001
            s["errors"][pid] = str(e)[:400]
            print("ERROR", pid, str(e)[:300], flush=True)
        STATE.write_text(json.dumps(s, indent=1), encoding="utf-8")
        n += 1
        if max_prs and n >= max_prs:
            break
    print("coverage run finished:", len(s["done"]), "PRs", flush=True)


def report():
    rows, items = [], []
    for pid in done_prs():
        f = PRS / pid / "coverage.json"
        if not f.exists():
            continue
        cov = json.loads(f.read_text(encoding="utf-8"))
        verdicts = {a: {i["id"]: i["verdict"] for i in json.loads(
            (PRS / pid / "arms" / a / "inspect_opus.json").read_text(encoding="utf-8"))["items"]} for a in "ABC"}
        cb = {i["id"]: i["covered"] == "yes" for i in cov["B"]}
        cc = {i["id"]: i["covered"] == "yes" for i in cov["C"]}
        ids = list(cb)
        score = {a: sum(verdicts[a][i] == "met" for i in ids) / len(ids) for a in "ABC"}
        rows.append(dict(pr=pid, covB=np.mean(list(cb.values())), covC=np.mean(list(cc.values())),
                         sB=score["B"], sC=score["C"], sA=score["A"]))
        for i in ids:
            for a in "ABC":
                items.append(dict(pr=pid, id=i, arm=a, covB=cb[i], covC=cc[i], met=verdicts[a][i] == "met"))
    df, it = pd.DataFrame(rows), pd.DataFrame(items)
    L = [f"Follow-up 8.3 (summary coverage of rubric items, EXPLORATORY). PRs: {len(df)}"]
    if len(df):
        d = df.covB - df.covC
        nz = d[d != 0]
        p = stats.wilcoxon(nz).pvalue if len(nz) else float("nan")
        L.append(f"Mean coverage: +HumanReview summary {df.covB.mean():.3f}, +AgentReview summary {df.covC.mean():.3f}; "
                 f"paired difference {d.mean():+.3f}, Wilcoxon p={p:.4f} (non-zero {len(nz)})")
        if len(df) > 2:
            rho, pr = stats.spearmanr(d, df.sB - df.sC)
            L.append(f"Coverage difference vs score difference (+HumanReview - +AgentReview): Spearman rho {rho:+.3f}, p={pr:.4f}")
        L.append("Share of items met, by arm and by whether the arm's own summary covered the item "
                 "(Baseline: by +HumanReview coverage, as a difficulty control):")
        for a, col in (("A", "covB"), ("B", "covB"), ("C", "covC")):
            g = it[it.arm == a]
            m1, m0 = g[g[col]].met.mean(), g[~g[col]].met.mean()
            L.append(f"   {a}: covered {m1:.3f} (n={int(g[col].sum())}), not covered {m0:.3f} (n={int((~g[col]).sum())})")
        rng = random.Random("20261107-coverage")
        pick = rng.sample([(r.pr, s) for r in df.itertuples() for s in "BC"], min(10, 2 * len(df)))
        H = ["# Hand check: summary coverage tags", "", "Seed `20261107-coverage`. For each, read the summary and mark agree/disagree per item.", ""]
        for pid, side in pick:
            cov = json.loads((PRS / pid / "coverage.json").read_text(encoding="utf-8"))[side]
            summ = json.loads((PRS / pid / f"summary_{side}.json").read_text(encoding="utf-8"))["text"]
            rub = {i["id"]: i["behaviour"] for i in json.loads((PRS / pid / "rubric.json").read_text(encoding="utf-8"))["items"]}
            H += [f"## {pid}, {'+HumanReview' if side == 'B' else '+AgentReview'} summary", "", "> " + summ.replace("\n", "\n> "), ""]
            H += [f"- {c['id']} **{c['covered']}** — {rub.get(c['id'], '')[:200]} — _{c['evidence'][:200]}_ — agree? " for c in cov]
            H.append("")
        (OUT / "coverage_handcheck.md").write_text("\n".join(H), encoding="utf-8")
    text = "\n".join(L)
    (OUT / "followup_coverage.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    if "--report" in sys.argv:
        report()
    else:
        prs = sys.argv[sys.argv.index("--prs") + 1].split(",") if "--prs" in sys.argv else None
        run(prs, int(sys.argv[sys.argv.index("--max-prs") + 1]) if "--max-prs" in sys.argv else None)
