"""Prepare PRs: metadata, base and merge trees, merged diff, test files, review material.

For each PR writes runs/prs/<id>/:
  meta.json      repo, pr, language, base/merge oids, PR title/body/author, issues, files, test files
  merged.diff    git diff base..merge
  review_B.json  comments for arm B (human-started conversations, humans other than the PR author)
  review_C.json  comments for arm C (agent-started conversations, agent accounts only)
  checks.json    build check 1 (file sets) and anything that stops the PR
Trees are written to G:\\devwork\\snap\\<id>\\{base,merge} (outside the repo; large).

Usage: python -I prepare.py <csv with repo,pr[,language]> [--only-meta]
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

STUDY = Path(__file__).resolve().parent.parent
PRS = STUDY / "runs" / "prs"
DATA = STUDY.parent.parent / "data" / "raw" / "agentreviewchat"
MIRRORS = Path(r"G:\devwork\mirrors")
SNAP = Path(r"G:\devwork\snap")

TEST_PATH = {"Python": re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$"),
             "Go": re.compile(r"_test\.go$|(^|/)testdata/")}
RUNNABLE = {"Python": re.compile(r"(^|/)test_[^/]*\.py$|_test\.py$"), "Go": re.compile(r"_test\.go$")}
SUGGESTION = re.compile(r"```suggestion[^\n]*\n.*?```", re.DOTALL)


def pr_id(repo, pr):
    return f"{repo.replace('/', '__')}-{pr}"


def sh(args, cwd=None, env=None, check=True):
    p = subprocess.run(args, cwd=cwd, env=env, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"{args[:4]} exit {p.returncode}: {p.stderr.decode('utf-8', 'replace')[-1500:]}")
    return p.stdout.decode("utf-8", "replace")


def gh_pr(repo, pr):
    o, n = repo.split("/", 1)
    q = ("query($o:String!,$n:String!,$p:Int!){repository(owner:$o,name:$n){pullRequest(number:$p){"
         "title body author{login} mergedAt "
         "mergeCommit{oid parents(first:2){nodes{oid}}} "
         "files(first:100){totalCount nodes{path}} "
         "closingIssuesReferences(first:5){nodes{number title body repository{nameWithOwner}}}}}}")
    raw = sh(["gh", "api", "graphql", "-f", f"query={q}", "-F", f"o={o}", "-F", f"n={n}", "-F", f"p={pr}"])
    return json.loads(raw)["data"]["repository"]["pullRequest"]


def mirror(repo):
    d = MIRRORS / repo.replace("/", "__")
    if not (d / ".git").exists():
        d.mkdir(parents=True, exist_ok=True)
        sh(["git", "init", "-q"], cwd=d)
        sh(["git", "config", "core.autocrlf", "false"], cwd=d)
        sh(["git", "config", "core.symlinks", "false"], cwd=d)
        sh(["git", "config", "core.longpaths", "true"], cwd=d)
        sh(["git", "remote", "add", "origin", f"https://github.com/{repo}.git"], cwd=d)
    return d


def fetch(d, sha):
    sh(["git", "fetch", "-q", "--depth", "2", "origin", sha], cwd=d)


def export_tree(d, sha, dest):
    """Write the tree at sha into dest, using a throwaway index so the mirror is untouched."""
    dest = Path(dest)
    if (dest / ".tree-ok").exists():
        return
    dest.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_INDEX_FILE=str(dest.parent / f".index-{dest.name}"))
    sh(["git", f"--work-tree={dest}", "-c", "core.autocrlf=false", "-c", "core.symlinks=false",
        "-c", "core.longpaths=true", "checkout", "-f", sha, "--", "."], cwd=d, env=env)
    os.remove(env["GIT_INDEX_FILE"])
    (dest / ".tree-ok").write_text(sha)


def review_material(repo, pr, author, agents):
    cols = ["repo", "pr_id", "path", "diff_hunk", "comments"]
    frames = []
    for f in ("part_000.parquet", "part_001.parquet"):
        frames.append(pd.read_parquet(DATA / f, columns=cols, filters=[("repo", "==", repo), ("pr_id", "==", pr)]))
    df = pd.concat(frames, ignore_index=True)

    def norm(x):
        return (x or "").lower().replace("[bot]", "")

    B, C = [], []
    for row in df.itertuples():
        cs = list(row.comments)
        if not cs:
            continue
        first = cs[0]
        agent_started = norm(first.get("author_login")) in agents
        human_started = first.get("author_type") == "User" and not agent_started
        for c in cs:
            login = norm(c.get("author_login"))
            body = SUGGESTION.sub("[suggested code removed]", c.get("body") or "").strip()
            item = {"path": row.path, "diff_hunk": row.diff_hunk, "author": c.get("author_login"),
                    "created_at": c.get("created_at"), "body": body}
            if human_started and c.get("author_type") == "User" and login not in agents and login != norm(author):
                B.append(item)
            if agent_started and login in agents:
                C.append(item)
    key = lambda x: x["created_at"] or ""
    return sorted(B, key=key), sorted(C, key=key), len(df)


def prepare(repo, pr, language, agents, only_meta=False):
    pid = pr_id(repo, pr)
    out = PRS / pid
    out.mkdir(parents=True, exist_ok=True)
    checks = {}
    g = gh_pr(repo, pr)
    mc = g["mergeCommit"]
    merge, base = mc["oid"], mc["parents"]["nodes"][0]["oid"]
    issues = [{"repo": i["repository"]["nameWithOwner"], "number": i["number"], "title": i["title"],
               "body": i["body"] or ""} for i in g["closingIssuesReferences"]["nodes"]]
    d = mirror(repo)
    fetch(d, merge)
    names = sh(["git", "diff", "--name-only", "--no-renames", base, merge], cwd=d).split()
    pr_files = sorted(x["path"] for x in g["files"]["nodes"])
    checks["files_match"] = sorted(set(names)) == sorted(set(pr_files))
    if not checks["files_match"]:
        checks["files_only_in_merge_diff"] = sorted(set(names) - set(pr_files))[:50]
        checks["files_only_in_pr"] = sorted(set(pr_files) - set(names))[:50]
    tests = [f for f in names if TEST_PATH[language].search(f)]
    meta = {"id": pid, "repo": repo, "pr": pr, "language": language, "base": base, "merge": merge,
            "merge_parents": len(mc["parents"]["nodes"]), "title": g["title"], "body": g["body"] or "",
            "author": (g["author"] or {}).get("login"), "merged_at": g["mergedAt"], "issues": issues,
            "files": names, "test_files": tests, "runnable_tests": [f for f in tests if RUNNABLE[language].search(f)],
            "src_files": [f for f in names if f not in tests]}
    (out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    (out / "merged.diff").write_text(sh(["git", "diff", "--no-renames", base, merge], cwd=d), encoding="utf-8")
    B, C, nconv = review_material(repo, pr, meta["author"], agents)
    (out / "review_B.json").write_text(json.dumps(B, indent=1), encoding="utf-8")
    (out / "review_C.json").write_text(json.dumps(C, indent=1), encoding="utf-8")
    checks.update({"conversations": nconv, "B_comments": len(B), "C_comments": len(C),
                   "issue_count": len(issues), "issue_chars": sum(len(i["body"]) + len(i["title"]) for i in issues)})
    if not only_meta:
        export_tree(d, base, SNAP / pid / "base")
        export_tree(d, merge, SNAP / pid / "merge")
        checks["trees"] = True
    (out / "checks.json").write_text(json.dumps(checks, indent=1), encoding="utf-8")
    return pid, checks


def load_agents():
    raw = (DATA / "agents.csv").read_text().split()[1:]
    return {a.strip().lower().replace("[bot]", "") for a in raw}


if __name__ == "__main__":
    lst = pd.read_csv(sys.argv[1])
    agents = load_agents()
    for r in lst.itertuples():
        try:
            pid, checks = prepare(r.repo, int(r.pr), r.language, agents, only_meta="--only-meta" in sys.argv)
            print(pid, json.dumps({k: v for k, v in checks.items() if not k.startswith("files_only")}), flush=True)
        except Exception as e:  # noqa: BLE001 - record and continue with the next PR
            print(pr_id(r.repo, int(r.pr)), "FAILED", str(e)[:500], flush=True)
