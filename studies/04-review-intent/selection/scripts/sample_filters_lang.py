"""For a random sample of Python pool PRs, check: linked closing issue, test files changed, commits pushed after the first human review.
Usage: python -I sample_filters.py <out_dir> <n> <seed>
"""
import sys, os, json, subprocess, re
import pandas as pd

out, n, seed, LANG = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
p = pd.read_csv(os.path.join(out, "pool.csv")).merge(pd.read_csv(os.path.join(out, "langs.csv")), on="repo")
s = p[p.language == LANG].sample(n=n, random_state=seed).reset_index(drop=True)
TEST = re.compile(r"(^|/)(tests?|testing|testdata)/|(^|/)test_[^/]*.py$|_test.(py|go)$|(^|/)conftest.py$")
rows = []
for i in range(0, len(s), 10):
    chunk = s.iloc[i:i + 10]
    parts = []
    for j, r in enumerate(chunk.itertuples()):
        o, nm = r.repo.split("/", 1)
        parts.append(f'p{j}: repository(owner: {json.dumps(o)}, name: {json.dumps(nm)}) {{ pullRequest(number: {int(r.pr_id)}) {{ '
                     'closingIssuesReferences(first: 3) { totalCount } '
                     'files(first: 100) { totalCount nodes { path } } '
                     'commits(last: 100) { nodes { commit { committedDate } } } } }')
    q = "query {" + " ".join(parts) + "}"
    res = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}"], capture_output=True, text=True, encoding="utf-8")
    data = json.loads(res.stdout or "{}").get("data") or {}
    for j, r in enumerate(chunk.itertuples()):
        pr = ((data.get(f"p{j}") or {}).get("pullRequest")) or {}
        if not pr:
            rows.append(dict(repo=r.repo, pr=r.pr_id, ok=False)); continue
        paths = [f["path"] for f in pr["files"]["nodes"]]
        dates = [c["commit"]["committedDate"] for c in pr["commits"]["nodes"]]
        rows.append(dict(repo=r.repo, pr=r.pr_id, ok=True,
                         issue=pr["closingIssuesReferences"]["totalCount"] > 0,
                         tests=any(TEST.search(x) for x in paths),
                         files=pr["files"]["totalCount"],
                         after=any(dt > r.first_human_review_at for dt in dates)))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(out, f"sample_filters_{LANG}_{seed}.csv"), index=False)
ok = df[df.ok]
print("sampled", len(df), "readable", len(ok))
for c in ["issue", "tests", "after"]:
    print(f"{c}: {int(ok[c].sum())} ({ok[c].mean():.0%})")
allc = ok.issue & ok.tests & ok.after
print(f"all three: {int(allc.sum())} ({allc.mean():.0%})  -> est. Python pool {allc.mean() * (p.language == LANG).sum():.0f}")
print("repos among all-three:", ok[allc].repo.nunique())
