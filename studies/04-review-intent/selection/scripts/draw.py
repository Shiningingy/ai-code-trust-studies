"""Pilot and main draws, as fixed in plan.md. Seed 20261107.

Shuffle = eligible rows sorted by (repo, pr), then pandas sample(frac=1, random_state=SEED).
Pilot: per pilot repo, its shuffled eligible PRs in order (the first N are the pilot; later ones
are replacements if a pilot PR fails a build check).
Main: pilot PRs and excluded repos removed; per language, walk the shuffled list, take a PR if its
repo has fewer than CAP taken, until PER_LANG. The full walk order is written too, for the record.

Usage: python -I draw.py <out_dir>
"""
import os
import sys

import pandas as pd

SEED, CAP, PER_LANG = 20261107, 6, 35
PILOT = {"home-assistant/core": 3, "getsentry/sentry-python": 2, "gruntwork-io/terragrunt": 3, "zitadel/zitadel": 2}
EXCLUDED = {"ray-project/ray", "lablup/backend.ai", "ansys/pymapdl", "apache/tvm"}

out = sys.argv[1]
e = pd.read_csv(os.path.join(out, "eligible.csv"))
e = e[e.eligible].sort_values(["repo", "pr"]).reset_index(drop=True)

rows = []
for repo, n in PILOT.items():
    s = e[e.repo == repo].sample(frac=1, random_state=SEED).reset_index(drop=True)
    for i, r in s.iterrows():
        rows.append(dict(repo=repo, pr=int(r.pr), language=r.language, rank=i, pilot=i < n))
pilot = pd.DataFrame(rows)
pilot.to_csv(os.path.join(out, "pilot_order.csv"), index=False)
print("pilot:", pilot[pilot.pilot][["repo", "pr"]].to_string(index=False))

pilot_ids = set(zip(pilot[pilot.pilot].repo, pilot[pilot.pilot].pr))
m = e[~e.repo.isin(EXCLUDED) & ~pd.Series([(a, b) in pilot_ids for a, b in zip(e.repo, e.pr)], index=e.index)]
walk = []
for lang in ("Python", "Go"):
    s = m[m.language == lang].sample(frac=1, random_state=SEED).reset_index(drop=True)
    taken, per_repo = 0, {}
    for i, r in s.iterrows():
        ok = taken < PER_LANG and per_repo.get(r.repo, 0) < CAP
        if ok:
            taken += 1
            per_repo[r.repo] = per_repo.get(r.repo, 0) + 1
        walk.append(dict(repo=r.repo, pr=int(r.pr), language=lang, rank=i, drawn=ok))
walk = pd.DataFrame(walk)
walk.to_csv(os.path.join(out, "main_walk.csv"), index=False)
d = walk[walk.drawn]
print("main drawn", len(d), d.groupby("language").size().to_dict(), "repos", d.repo.nunique())
print(d.groupby(["language", "repo"]).size().to_string())
