"""Eligibility for every Python and Go PR in pool.csv, from the GitHub GraphQL API (gh CLI).

Replaces the sampled checks in sample_filters*.py with one full pass and a corrected test-file rule:
a PR counts as having tests only if it changes a runnable test file
(Python: test_*.py or *_test.py; Go: *_test.go), since stage 1 needs tests it can run.

Writes prs.jsonl (one GitHub record per PR) and eligible.csv.
Usage: python -I eligible.py <out_dir>
"""
import json
import os
import re
import subprocess
import sys
import time

import pandas as pd

out = sys.argv[1]
RUNNABLE = {"Python": re.compile(r"(^|/)test_[^/]*\.py$|_test\.py$"), "Go": re.compile(r"_test\.go$")}
FIELDS = ("number author { login } mergedAt baseRefName "
          "mergeCommit { oid parents(first: 2) { nodes { oid } } } "
          "closingIssuesReferences(first: 5) { totalCount nodes { number repository { nameWithOwner } } } "
          "files(first: 100) { totalCount nodes { path additions deletions } } "
          "commits(last: 100) { totalCount nodes { commit { committedDate } } }")

p = pd.read_csv(os.path.join(out, "pool.csv")).merge(pd.read_csv(os.path.join(out, "langs.csv")), on="repo")
p = p[p.language.isin(RUNNABLE)].reset_index(drop=True)
path = os.path.join(out, "prs.jsonl")
done = set()
if os.path.exists(path):
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        done.add((r["repo"], r["pr"]))
todo = p[[(r, int(n)) not in done for r, n in zip(p.repo, p.pr_id)]]
print("pool", len(p), "already fetched", len(done), "to fetch", len(todo), flush=True)

with open(path, "a", encoding="utf-8") as f:
    for i in range(0, len(todo), 10):
        chunk = todo.iloc[i:i + 10]
        parts = []
        for j, r in enumerate(chunk.itertuples()):
            o, nm = r.repo.split("/", 1)
            parts.append(f'p{j}: repository(owner: {json.dumps(o)}, name: {json.dumps(nm)}) '
                         f'{{ pullRequest(number: {int(r.pr_id)}) {{ {FIELDS} }} }}')
        q = "query {" + " ".join(parts) + "}"
        for attempt in range(4):
            res = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}"], capture_output=True, text=True,
                                 encoding="utf-8")
            data = (json.loads(res.stdout or "{}").get("data")) if res.stdout else None
            if data:
                break
            time.sleep(20 * (attempt + 1))
        data = data or {}
        for j, r in enumerate(chunk.itertuples()):
            pr = (data.get(f"p{j}") or {}).get("pullRequest")
            f.write(json.dumps({"repo": r.repo, "pr": int(r.pr_id), "language": r.language,
                                "first_human_review_at": r.first_human_review_at, "gh": pr}) + "\n")
        if i % 200 == 0:
            print(i, flush=True)

rows = []
for line in open(path, encoding="utf-8"):
    r = json.loads(line)
    pr = r["gh"]
    if not pr:
        rows.append(dict(repo=r["repo"], pr=r["pr"], language=r["language"], readable=False))
        continue
    paths = [x["path"] for x in pr["files"]["nodes"]]
    dates = [c["commit"]["committedDate"] for c in pr["commits"]["nodes"]]
    mc = pr.get("mergeCommit") or {}
    rows.append(dict(
        repo=r["repo"], pr=r["pr"], language=r["language"], readable=True,
        issue=pr["closingIssuesReferences"]["totalCount"] > 0,
        tests=any(RUNNABLE[r["language"]].search(x) for x in paths),
        after=any(d > r["first_human_review_at"] for d in dates),
        files=pr["files"]["totalCount"], files_complete=pr["files"]["totalCount"] <= 100,
        merge_commit=mc.get("oid"), merge_parents=len((mc.get("parents") or {}).get("nodes") or []),
        author=(pr.get("author") or {}).get("login")))
df = pd.DataFrame(rows)
df["eligible"] = df.readable & df.issue & df.tests & df.after & df.files_complete & df.merge_commit.notna()
df.to_csv(os.path.join(out, "eligible.csv"), index=False)
for lang, g in df.groupby("language"):
    ok = g[g.readable]
    print(lang, "readable", len(ok), "issue", int(ok.issue.sum()), "tests", int(ok.tests.sum()),
          "after", int(ok.after.sum()), "eligible", int(g.eligible.sum()), "repos", g[g.eligible].repo.nunique())
