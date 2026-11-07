"""Count PRs in AgentReviewChat that carry BOTH a human-started and an AI-agent-started review conversation.
Usage: python -I overlap.py <data_dir>
"""
import sys, os
import pandas as pd

d = sys.argv[1]
agents = {a.strip().lower().replace("[bot]", "") for a in open(os.path.join(d, "agents.csv")).read().split()[1:]}
df = pd.concat([pd.read_parquet(os.path.join(d, f), columns=["repo", "pr_id", "author_login", "author_type", "merged_by", "comments"])
                for f in ("part_000.parquet", "part_001.parquet")], ignore_index=True)
print("rows", len(df))

def norm(login):
    return (login or "").lower().replace("[bot]", "")

def is_agent(login):
    return norm(login) in agents

first = df["comments"].map(lambda cs: cs[0] if len(cs) else {})
df["reviewer_login"] = first.map(lambda c: c.get("author_login"))
df["reviewer_type"] = first.map(lambda c: c.get("author_type"))
df["reviewer_is_agent"] = df["reviewer_login"].map(is_agent)
df["reviewer_is_human"] = (df["reviewer_type"] == "User") & ~df["reviewer_is_agent"]
df["code_is_agent"] = df["author_login"].map(is_agent)
def has_sug(c):
    s = c.get("suggestion")
    if s is None:
        return False
    if isinstance(s, str):
        return s not in ("None", "")
    return len(s) > 0

df["has_suggestion"] = first.map(has_sug)
df["merged"] = df["merged_by"].map(lambda m: bool(m) and bool((m or {}).get("merged_at")))

# sanity check against the paper's Table I (HRH 116,874 / HRA 6,519 / ARH 154,469 / ARA 928)
cat = (df["reviewer_is_agent"].map({True: "AR", False: "HR"}) + df["code_is_agent"].map({True: "A", False: "H"}))
print("category counts (first commenter = reviewer):", cat.value_counts().to_dict())
print("first commenter neither agent nor human User (other bots):", int((~df.reviewer_is_agent & ~df.reviewer_is_human).sum()))

g = df.groupby(["repo", "pr_id"]).agg(
    human=("reviewer_is_human", "sum"),
    agent=("reviewer_is_agent", "sum"),
    merged=("merged", "max"),
    code_agent=("code_is_agent", "max"),
)
print("PRs total", len(g))
both = g[(g.human > 0) & (g.agent > 0)]
print("PRs with >=1 human AND >=1 agent review conversation:", len(both))
print("  of which merged:", int(both.merged.sum()))
print("  of which agent-written code:", int(both.code_agent.sum()))
print("  repos covered (merged):", both[both.merged].reset_index().repo.nunique())
print("PRs merged with human review only:", int(((g.human > 0) & (g.agent == 0) & g.merged).sum()))
print("PRs merged with agent review only:", int(((g.human == 0) & (g.agent > 0) & g.merged).sum()))
# human review conversations without a code suggestion (pure text -> intent)
hm = df[df.reviewer_is_human]
print("human-started conversations:", len(hm), " without a code suggestion:", int((~hm.has_suggestion).sum()))
