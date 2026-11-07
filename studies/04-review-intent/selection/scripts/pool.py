"""Build the candidate pool: merged PRs with >=1 human-started and >=1 agent-started review conversation.
Writes pool.csv (repo, pr_id, first_human_review_at, n_human_conv, n_agent_conv, human_words) and repos.txt.
Usage: python -I pool.py <data_dir> <out_dir>
"""
import sys, os
import pandas as pd

d, out = sys.argv[1], sys.argv[2]
agents = {a.strip().lower().replace("[bot]", "") for a in open(os.path.join(d, "agents.csv")).read().split()[1:]}
df = pd.concat([pd.read_parquet(os.path.join(d, f), columns=["repo", "pr_id", "merged_by", "comments"])
                for f in ("part_000.parquet", "part_001.parquet")], ignore_index=True)

def norm(x):
    return (x or "").lower().replace("[bot]", "")

first = df["comments"].map(lambda cs: cs[0] if len(cs) else {})
df["is_agent"] = first.map(lambda c: norm(c.get("author_login")) in agents)
df["is_human"] = first.map(lambda c: c.get("author_type") == "User") & ~df["is_agent"]
df["first_at"] = first.map(lambda c: c.get("created_at"))
df["words"] = first.map(lambda c: len((c.get("body") or "").split()))
df["merged"] = df["merged_by"].map(lambda m: bool(m) and bool((m or {}).get("merged_at")))

h = df[df.is_human & df.merged].groupby(["repo", "pr_id"]).agg(first_human_review_at=("first_at", "min"),
                                                              n_human_conv=("is_human", "sum"),
                                                              human_words=("words", "sum"))
a = df[df.is_agent & df.merged].groupby(["repo", "pr_id"]).agg(n_agent_conv=("is_agent", "sum"))
pool = h.join(a, how="inner").reset_index()
pool.to_csv(os.path.join(out, "pool.csv"), index=False)
open(os.path.join(out, "repos.txt"), "w").write("\n".join(sorted(pool.repo.unique())))
print("pool PRs", len(pool), "repos", pool.repo.nunique())
print(pool[["n_human_conv", "n_agent_conv", "human_words"]].describe().round(1).to_string())
