"""Follow-up 6.1 (exploratory): rubric items already present before the first review comment.

Per PR (the 56 complete main-run PRs):
  1. Cut point = earliest created_at over review_B.json + review_C.json (first review comment of either kind).
  2. Pre-review commit = the candidate commit with the latest committedDate strictly before the cut point.
     Candidates are the PR's commits as GitHub lists them now, plus, when the head was force-pushed after the
     cut, the commits of the branch as it stood just before that force-push (GitHub compare base...beforeCommit).
     committedDate is used because GitHub no longer reports a per-commit push time (Commit.pushedDate is
     deprecated and null); the selection scripts' "commit after first human review" rule also used it.
  3. Pre-review diff = git diff merge-base(meta base, pre-review commit)..pre-review commit, non-test files only
     (prepare.TEST_PATH), plus the line-numbered touched non-test files at the pre-review commit (judge.numbered),
     i.e. what an inspector gets for an agent run, minus the stage-1 section. No scrub: the scrub only removes an
     agent's references to its task, and code written before review cannot refer to it.
  4. One Opus call (role "tagger", medium effort) marks each rubric item present / absent / cant_tell.
     No pre-review commit, or an empty non-test pre-review diff: every item is absent, no call.

Writes runs/prs/<id>/prereview.json and runs/followup_prereview.json (resumable).
--report keeps the present items per PR and recomputes each arm's rubric score from the existing Opus verdicts
(arms/<arm>/inspect_opus.json; no new inspections), reruns H1/H2 (+ C vs A) as analyze.py does, and writes
results/followup_prereview.txt and results/prereview_handcheck.md. Everything it prints is EXPLORATORY.

Sensitivity (--early-cut, after the main tagging): cut = the earlier of the B/C cut and the first GitHub review by
a non-author (reviews outside the study's data: bots not among the 16 agents, reviews without inline comments;
recorded as github_reviews_before_cut). Reuses the main tags when the chosen commit is unchanged, otherwise tags
again. Writes runs/prs/<id>/prereview_early.json (never prereview.json) and runs/followup_prereview_early.json.

Usage: python followup_prereview.py [--prs id1,id2] [--max-prs N] [--early-cut]
       then: python followup_prereview.py --report
"""
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import analyze
import llm
from judge import MAX_DIFF, numbered
from prepare import PRS, TEST_PATH, mirror, sh
from summarise import issue_text

STUDY = Path(__file__).resolve().parent.parent
STATE = STUDY / "runs" / "followup_prereview.json"
STATE_EARLY = STUDY / "runs" / "followup_prereview_early.json"  # sensitivity: --early-cut
OUT = STUDY / "results"
HANDCHECK_SEED, HANDCHECK_N = "20261107-prereview", 10
PR_BUDGET = 5 * 60

TAG_SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {
    "type": "array", "items": {"type": "object", "required": ["id", "tag", "evidence"], "properties": {
        "id": {"type": "string"}, "tag": {"type": "string", "enum": ["present", "absent", "cant_tell"]},
        "evidence": {"type": "string"}}}}}}

# INSPECT_PROMPT with the stage-1 section removed and met/not_met renamed present/absent; same standard.
TAG_PROMPT = """You are checking one implementation of a change to the {repo} repository against a rubric.

<issue>
{issue}
</issue>

<rubric>
{rubric}
</rubric>

<implementation_diff>
{diff}
</implementation_diff>

<files_after_change>
{files}
</files_after_change>

For every rubric item decide from the code whether this implementation already meets it: "present" if it does, "absent" if it does not, or "cant_tell" when the code shown is not enough to decide. Give evidence as file:line plus one sentence. Judge behaviour, not names or structure."""

PR_QUERY = """query($o:String!,$n:String!,$p:Int!,$c:String){repository(owner:$o,name:$n){pullRequest(number:$p){
 createdAt headRefOid author{login}
 commits(first:100, after:$c){totalCount pageInfo{hasNextPage endCursor}
   nodes{commit{oid committedDate authoredDate parents{totalCount}}}}
 timelineItems(first:100, itemTypes:[HEAD_REF_FORCE_PUSHED_EVENT]){nodes{... on HeadRefForcePushedEvent{
   createdAt beforeCommit{oid committedDate} afterCommit{oid committedDate}}}}
 reviews(first:100){nodes{createdAt submittedAt state author{login} comments{totalCount}}}}}}"""


def load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def done_prs():
    out = []
    for lang in ("python", "go"):
        out += json.loads((STUDY / "runs" / f"main_state_{lang}.json").read_text(encoding="utf-8"))["done"]
    return sorted(out)


def gh_json(args):
    return json.loads(sh(["gh", "api", *args]))


def pr_history(repo, pr):
    o, n = repo.split("/", 1)
    commits, cursor, first = [], None, None
    while True:
        args = ["graphql", "-f", f"query={PR_QUERY}", "-F", f"o={o}", "-F", f"n={n}", "-F", f"p={pr}"]
        if cursor:
            args += ["-f", f"c={cursor}"]
        g = gh_json(args)["data"]["repository"]["pullRequest"]
        first = first or g
        page = g["commits"]
        commits += [dict(oid=x["commit"]["oid"], committed=x["commit"]["committedDate"],
                         authored=x["commit"]["authoredDate"], parents=x["commit"]["parents"]["totalCount"],
                         source="pr_commits") for x in page["nodes"]]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    first["commit_list"] = commits
    return first


def compare(repo, base, head):
    """GitHub compare base...head: merge base and the commits on head's side (up to 250)."""
    r = gh_json([f"repos/{repo}/compare/{base}...{head}"])
    return r["merge_base_commit"]["sha"], [
        dict(oid=c["sha"], committed=c["commit"]["committer"]["date"], authored=c["commit"]["author"]["date"],
             parents=len(c["parents"]), source=f"before_force_push:{head[:10]}") for c in r["commits"]]


def ensure(d, oid):
    if sh(["git", "cat-file", "-t", oid], cwd=d, check=False).strip() != "commit":
        sh(["git", "fetch", "-q", "--depth", "1", "origin", oid], cwd=d)


def cut_point(d):
    stamps = []
    for side in ("B", "C"):
        for c in load(d / f"review_{side}.json") or []:
            if c.get("created_at"):
                stamps.append((c["created_at"], side, c.get("author")))
    return min(stamps) if stamps else None


def pre_review_code(pid, meta, cut=None):
    """Everything up to the tagging call: cut point, chosen commit, merge base, non-test diff and files.
    cut = (iso time, side, author) overrides the B/C cut (sensitivity run)."""
    d = PRS / pid
    cut = cut or cut_point(d)
    if cut is None:
        raise RuntimeError("no review comments in review_B/C")
    cut_at = ts(cut[0])
    h = pr_history(meta["repo"], meta["pr"])
    cands = list(h["commit_list"])
    forced = [e for e in h["timelineItems"]["nodes"] if e]
    forced_after = sorted((e for e in forced if ts(e["createdAt"]) >= cut_at), key=lambda e: e["createdAt"])
    notes = []
    if forced_after and forced_after[0].get("beforeCommit"):
        before = forced_after[0]["beforeCommit"]["oid"]
        try:
            _, extra = compare(meta["repo"], meta["base"], before)
            known = {c["oid"] for c in cands}
            cands += [c for c in extra if c["oid"] not in known]
            notes.append(f"head force-pushed after the cut ({forced_after[0]['createdAt']}); added "
                         f"{len(extra)} commits of the branch before that push ({before[:10]}) as candidates")
        except Exception as e:  # noqa: BLE001 - the rewritten-away commits may no longer be on GitHub
            notes.append(f"head force-pushed after the cut; commits before that push not retrievable: {str(e)[:200]}")
    pre = [c for c in cands if ts(c["committed"]) < cut_at]
    # list order breaks ties; the latest committedDate wins
    order = {c["oid"]: i for i, c in enumerate(cands)}
    chosen = max(pre, key=lambda c: (ts(c["committed"]), order[c["oid"]])) if pre else None
    pr_list = h["commit_list"]
    if chosen and chosen["source"] == "pr_commits":
        later_in_list = pr_list[order[chosen["oid"]] + 1:]
        if any(ts(c["committed"]) < cut_at for c in later_in_list) or any(
                ts(c["committed"]) >= cut_at for c in pr_list[:order[chosen["oid"]]]):
            notes.append("committedDate is not monotone along the PR's commit list around the cut")
    author = (h.get("author") or {}).get("login")
    reviews = [r for r in h["reviews"]["nodes"] if r and (r.get("author") or {}).get("login") != author]
    early = sorted(({"at": r["submittedAt"] or r["createdAt"], "author": (r.get("author") or {}).get("login"),
                     "state": r.get("state"), "inline_comments": (r.get("comments") or {}).get("totalCount")}
                    for r in reviews if ts(r["submittedAt"] or r["createdAt"]) < cut_at), key=lambda r: r["at"])
    first_review = min((r["submittedAt"] or r["createdAt"] for r in reviews), default=None)
    rec = {"pr": pid, "repo": meta["repo"], "number": meta["pr"], "language": meta["language"],
           "cut_point": cut[0], "cut_side": cut[1], "cut_author": cut[2],
           "first_github_review_by_non_author": first_review,
           "github_review_before_cut": bool(early), "github_reviews_before_cut": early[:10],
           "pr_created_at": h["createdAt"], "meta_base": meta["base"], "merge": meta["merge"],
           "merge_parents": meta.get("merge_parents"), "pr_commits_total": len(pr_list),
           "pr_commits_before_cut": sum(ts(c["committed"]) < cut_at for c in pr_list),
           "force_pushes": forced, "force_pushes_after_cut": len(forced_after),
           "pre_review_oid": chosen["oid"] if chosen else None,
           "pre_review_committed": chosen["committed"] if chosen else None,
           "pre_review_source": chosen["source"] if chosen else None, "notes": notes}
    if not chosen:
        rec.update(merge_base=None, diff_files=[], diff_chars=0, files={})
        return rec, "", {}
    mb, _ = compare(meta["repo"], meta["base"], chosen["oid"])
    rec["merge_base"] = mb
    rec["branch_base_differs_from_meta_base"] = mb != meta["base"]
    m = mirror(meta["repo"])
    ensure(m, mb)
    ensure(m, chosen["oid"])
    names = sh(["git", "diff", "--name-only", "--no-renames", mb, chosen["oid"]], cwd=m).split()
    src = [n for n in names if not TEST_PATH[meta["language"]].search(n)]
    diff = sh(["git", "diff", "--no-renames", mb, chosen["oid"], "--", *src], cwd=m) if src else ""
    present_at = set(sh(["git", "ls-tree", "-r", "--name-only", chosen["oid"], "--", *src], cwd=m).split()) if src else set()
    files = {n: sh(["git", "show", f"{chosen['oid']}:{n}"], cwd=m) for n in src if n in present_at}
    rec.update(diff_files=src, test_files_skipped=len(names) - len(src), diff_chars=len(diff),
               merged_src_files=meta.get("src_files"))
    return rec, diff, files


def tag(pid, early=False):
    d = PRS / pid
    meta = load(d / "meta.json")
    rub = load(d / "rubric.json")
    ids = [i["id"] for i in rub["items"]]
    main = None
    if early:  # sensitivity: cut = earliest non-author GitHub review before the B/C cut, if any
        main = load(d / "prereview.json")
        if main is None:
            raise RuntimeError("no prereview.json: run the main tagging first")
        before = main.get("github_reviews_before_cut") or []
        if before:
            rec, diff, files = pre_review_code(pid, meta, (before[0]["at"], "github_review", before[0]["author"]))
        else:
            rec, diff, files = dict(main), None, None
        rec.update(main_cut_point=main["cut_point"], main_pre_review_oid=main["pre_review_oid"],
                   cut_moved=bool(before), commit_changed=rec["pre_review_oid"] != main["pre_review_oid"])
        if not rec["commit_changed"]:  # same code as the main tag: reuse it, no model call
            rec.update(tags=main["tags"], call=None, tags_reused=True)
            rec["counts"] = {k: sum(t["tag"] == k for t in rec["tags"]) for k in ("present", "absent", "cant_tell")}
            (d / "prereview_early.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
            return rec
        rec["tags_reused"] = False
    else:
        rec, diff, files = pre_review_code(pid, meta)
    if not rec["pre_review_oid"] or not diff.strip():
        why = "no commit before the cut point" if not rec["pre_review_oid"] else "no non-test change before the cut"
        rec["tags"] = [{"id": i, "tag": "absent", "evidence": why} for i in ids]
        rec["call"] = None
    else:
        rtext = "\n".join(f"{i['id']}: {i['behaviour']}" + (f"\n    check: {i['check']}" if i.get("check") else "")
                          for i in rub["items"])
        dd = diff if len(diff) <= MAX_DIFF else diff[:MAX_DIFF] + "\n[... diff cut ...]"
        r = llm.call(TAG_PROMPT.format(repo=meta["repo"], issue=issue_text(meta), rubric=rtext, diff=dd,
                                       files=numbered(files)),
                     role="tagger", pr=pid, tag="prereview_early/opus" if early else "prereview/opus",
                     model=llm.OPUS, effort="medium",
                     schema=TAG_SCHEMA, timeout=900)
        if r["status"] != "ok" or not r["structured"]:
            raise RuntimeError(f"tagger {r['status']} for {pid}")
        got = {i["id"]: i for i in r["structured"]["items"]}
        rec["tags"] = [got.get(i, {"id": i, "tag": "cant_tell", "evidence": "item not returned"}) for i in ids]
        rec["call"] = {"seconds": r["seconds"], "usage": r["usage"], "total_tokens": llm.total_tokens(r["usage"])}
    rec["counts"] = {k: sum(t["tag"] == k for t in rec["tags"]) for k in ("present", "absent", "cant_tell")}
    (d / ("prereview_early.json" if early else "prereview.json")).write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


def run(only=None, max_prs=None, early=False):
    state = STATE_EARLY if early else STATE
    s = load(state) or {"done": [], "errors": {}}
    n = 0
    for pid in only or done_prs():
        if pid in s["done"]:
            continue
        if llm.STOP_AT and time.time() + PR_BUDGET > llm.STOP_AT:
            print(time.strftime("%H:%M"), "STOP: stop time", flush=True)
            break
        try:
            r = tag(pid, early)
            s["done"].append(pid)
            s["errors"].pop(pid, None)
            extra = (f" cut moved {r['cut_moved']}, commit changed {r['commit_changed']}, reused {r['tags_reused']}"
                     if early else "")
            print(time.strftime("%H:%M"), "DONE", pid, r["counts"], "pre-review", (r["pre_review_oid"] or "-")[:10],
                  (r["call"] or {}).get("total_tokens", 0), "tokens" + extra, flush=True)
        except Exception as e:  # noqa: BLE001
            s["errors"][pid] = str(e)[:400]
            print(time.strftime("%H:%M"), "ERROR", pid, str(e)[:300], flush=True)
        state.write_text(json.dumps(s, indent=1), encoding="utf-8")
        n += 1
        if max_prs and n >= max_prs:
            break
    print("prereview tagging finished:", len(s["done"]), "tagged,", len(s["errors"]), "errors", flush=True)


def scores(recs, keep):
    """Per PR and arm: share of kept items with Opus verdict met. keep(tag) decides which items stay."""
    rows, dropped = [], []
    for pid, rec in recs.items():
        ids = [t["id"] for t in rec["tags"] if keep(t["tag"])]
        if not ids:
            dropped.append(pid)
            continue
        row = {"pr": pid, "repo": rec["repo"], "language": rec["language"], "n_items": len(ids)}
        for arm in analyze.ARMS:
            io = load(PRS / pid / "arms" / arm / "inspect_opus.json")
            v = {i["id"]: i["verdict"] for i in io["items"]}
            row[arm] = sum(v.get(i) == "met" for i in ids) / len(ids)
            row[f"{arm}_full"] = io["score"]
        rows.append(row)
    return pd.DataFrame(rows).set_index("pr") if rows else pd.DataFrame(), dropped


def compare_block(W, p, rng, label):
    n = len(W)
    p("Mean per arm: " + ", ".join(f"{a} {W[a].mean():.3f}" for a in analyze.ARMS))
    res = {}
    for name, (x, y) in {"H1 B vs A": ("B", "A"), "H2 B vs C": ("B", "C")}.items():
        pval, nz = analyze.wilcoxon(W[x], W[y])
        d = W[x] - W[y]
        res[name] = (pval, d.mean(), analyze.boot_ci(d, rng), nz)
    ps = [res[k][0] for k in res]
    adj = analyze.holm(ps) if not any(np.isnan(ps)) else [np.nan, np.nan]
    for (name, (pval, md, ci, nz)), ap in zip(res.items(), adj):
        p(f"{name} [{label}]: mean diff {md:+.3f} (95% bootstrap CI {ci[0]:+.3f} to {ci[1]:+.3f}); Wilcoxon "
          f"p={pval:.4f} (non-zero pairs {nz}), Holm-adjusted p={ap:.4f} -> {analyze.verdict(ap, md, n)}")
    pval, nz = analyze.wilcoxon(W["C"], W["A"])
    d = W["C"] - W["A"]
    ci = analyze.boot_ci(d, rng)
    p(f"C vs A [{label}]: mean diff {d.mean():+.3f} (CI {ci[0]:+.3f} to {ci[1]:+.3f}), Wilcoxon p={pval:.4f} "
      f"(non-zero pairs {nz})")
    for x, y in (("B", "A"), ("B", "C"), ("C", "A")):
        d = W[x] - W[y]
        p(f"   {x} vs {y}: {x} higher {(d > 0).sum()}, lower {(d < 0).sum()}, same {(d == 0).sum()}")


def report():
    OUT.mkdir(exist_ok=True)
    s = load(STATE) or {"done": [], "errors": {}}
    recs = {pid: load(PRS / pid / "prereview.json") for pid in s["done"] if (PRS / pid / "prereview.json").exists()}
    L = []
    p = L.append
    p("Follow-up 6.1: rubric items present before the first review comment. EXPLORATORY: not part of the frozen "
      "analysis, cannot change a verdict.")
    p(f"PRs tagged: {len(recs)} of {len(done_prs())} complete main-run PRs; tagging errors: {len(s['errors'])}")
    if not recs:
        (OUT / "followup_prereview.txt").write_text("\n".join(L), encoding="utf-8")
        print("\n".join(L))
        return
    allt = [t["tag"] for r in recs.values() for t in r["tags"]]
    p(f"Items tagged: {len(allt)}; present {allt.count('present')}, absent {allt.count('absent')}, "
      f"cant_tell {allt.count('cant_tell')} (cant_tell counts as absent below)")
    no_commit = [k for k, r in recs.items() if not r["pre_review_oid"]]
    no_diff = [k for k, r in recs.items() if r["pre_review_oid"] and r.get("call") is None]
    p(f"PRs with no commit before the cut: {len(no_commit)}" + (f" ({', '.join(no_commit)})" if no_commit else ""))
    p(f"PRs with a pre-review commit but no non-test change: {len(no_diff)}" + (f" ({', '.join(no_diff)})" if no_diff else ""))
    p(f"PRs whose head was force-pushed after the cut: {sum(r['force_pushes_after_cut'] > 0 for r in recs.values())}; "
      f"a GitHub review by a non-author before the cut (cut may be late): "
      f"{sum(r['github_review_before_cut'] for r in recs.values())}; branch base differs from meta base: "
      f"{sum(bool(r.get('branch_base_differs_from_meta_base')) for r in recs.values())}")
    sides = pd.Series([r["cut_side"] for r in recs.values()]).value_counts().to_dict()
    gap = pd.Series([(ts(r["cut_point"]) - ts(r["pr_created_at"])).total_seconds() / 3600 for r in recs.values()])
    p(f"Cut point set by: {sides} (B = human review comment, C = agent review comment); hours from PR creation "
      f"to cut: median {gap.median():.1f}, min {gap.min():.1f}, max {gap.max():.1f}")
    per = pd.Series({k: sum(t["tag"] == "present" for t in r["tags"]) for k, r in recs.items()})
    tot = pd.Series({k: len(r["tags"]) for k, r in recs.items()})
    p(f"Present items per PR: mean {per.mean():.2f} of {tot.mean():.2f}, median {per.median():.0f}, "
      f"min {per.min()}, max {per.max()}; distribution {dict(sorted(per.value_counts().items()))}")

    rng = np.random.default_rng(analyze.SEED)
    W, dropped = scores(recs, lambda t: t == "present")
    p(f"\n== Main recomputation: present items only (Opus verdicts from the main run) ==")
    p(f"PRs kept: {len(W)}; dropped (no present item): {len(dropped)}" + (f" ({', '.join(sorted(dropped))})" if dropped else ""))
    if len(W):
        compare_block(W, p, rng, "present items")
        p("Same PRs, full rubric (for comparison): " + ", ".join(f"{a} {W[a + '_full'].mean():.3f}" for a in analyze.ARMS)
          + f"; B-A {(W.B_full - W.A_full).mean():+.3f}, B-C {(W.B_full - W.C_full).mean():+.3f}")
        p("By language (descriptive): " + "; ".join(
            f"{lang} (n={len(g)}) " + ", ".join(f"{a} {g[a].mean():.3f}" for a in analyze.ARMS)
            for lang, g in W.groupby("language")))
    W2, dropped2 = scores(recs, lambda t: t in ("present", "cant_tell"))
    p(f"\n== Sensitivity: cant_tell counted as present ==")
    p(f"PRs kept: {len(W2)}; dropped: {len(dropped2)}")
    if len(W2):
        compare_block(W2, p, np.random.default_rng(analyze.SEED), "present + cant_tell")
    se = load(STATE_EARLY) or {"done": [], "errors": {}}
    early = {pid: load(PRS / pid / "prereview_early.json") for pid in se["done"]
             if (PRS / pid / "prereview_early.json").exists()}
    if early:
        p("\n== SENSITIVITY: early cut (cut = earlier of the first B/C review comment and the first GitHub review "
          "by a non-author; covers review outside the study's data) ==")
        moved = [k for k, r in early.items() if r["cut_moved"]]
        changed = [k for k, r in early.items() if r["commit_changed"]]
        p(f"PRs: {len(early)}; tagging errors: {len(se['errors'])}; cut moved earlier: {len(moved)}; pre-review commit "
          f"changed (tagged again): {len(changed)}" + (f" ({', '.join(sorted(changed))})" if changed else "")
          + f"; tags reused unchanged: {sum(r['tags_reused'] for r in early.values())}")
        p(f"PRs with no commit before the early cut: {sum(not r['pre_review_oid'] for r in early.values())}")
        et = [t["tag"] for r in early.values() for t in r["tags"]]
        p(f"Items tagged: {len(et)}; present {et.count('present')}, absent {et.count('absent')}, "
          f"cant_tell {et.count('cant_tell')} (cant_tell counts as absent)")
        WE, droppedE = scores(early, lambda t: t == "present")
        p(f"PRs kept: {len(WE)}; dropped (no present item): {len(droppedE)}"
          + (f" ({', '.join(sorted(droppedE))})" if droppedE else ""))
        if len(WE):
            compare_block(WE, p, np.random.default_rng(analyze.SEED), "sensitivity: early cut, present items")
            p("Same PRs, full rubric (for comparison): " + ", ".join(f"{a} {WE[a + '_full'].mean():.3f}"
                                                                     for a in analyze.ARMS))
    text = "\n".join(L)
    (OUT / "followup_prereview.txt").write_text(text, encoding="utf-8")
    print(text)
    handcheck(recs)


def handcheck(recs):
    pool = []
    for pid in sorted(recs):
        rec = recs[pid]
        items = {i["id"]: i for i in load(PRS / pid / "rubric.json")["items"]}
        for t in rec["tags"]:
            pool.append((pid, rec, items[t["id"]], t))
    pick = random.Random(HANDCHECK_SEED).sample(pool, min(HANDCHECK_N, len(pool)))
    L = ["# Pre-review tags: hand check", "",
         f"{len(pick)} tags drawn at random (seed `{HANDCHECK_SEED}`) from {len(pool)} tags on {len(recs)} PRs. "
         "For each, open the pre-review commit and decide whether the item's behaviour is already there "
         "(present = an inspector would mark it met). EXPLORATORY.", ""]
    for k, (pid, rec, item, t) in enumerate(pick, 1):
        repo, oid = rec["repo"], rec["pre_review_oid"]
        L += [f"## {k}. {pid} {t['id']}", "",
              f"- PR: https://github.com/{repo}/pull/{rec['number']}",
              f"- Cut point (first review comment, arm {rec['cut_side']} side): {rec['cut_point']}"]
        if oid:
            L += [f"- Pre-review commit: https://github.com/{repo}/commit/{oid} (committed {rec['pre_review_committed']})",
                  f"- Pre-review diff: https://github.com/{repo}/compare/{rec['merge_base']}...{oid}"]
            links = []
            for path, line in re.findall(r"([\w./-]+\.\w+):(\d+)", t["evidence"]):
                full = next((f for f in rec["diff_files"] if f == path or f.endswith("/" + path)), None)
                if full:
                    links.append(f"https://github.com/{repo}/blob/{oid}/{full}#L{line}")
            if links:
                L.append("- Evidence lines: " + " ".join(dict.fromkeys(links)))
        else:
            L.append("- Pre-review commit: none (no commit before the cut point)")
        L += [f"- Item: {item['behaviour']}"]
        if item.get("check"):
            L.append(f"- Check: {item['check']}")
        L += [f"- Tag: **{t['tag']}**", f"- Evidence: {t['evidence']}", "- Human: agree / disagree / unsure. Note:", ""]
    (OUT / "prereview_handcheck.md").write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {OUT / 'prereview_handcheck.md'} ({len(pick)} tags)")


if __name__ == "__main__":
    if "--report" in sys.argv:
        report()
    else:
        only = sys.argv[sys.argv.index("--prs") + 1].split(",") if "--prs" in sys.argv else None
        run(only, int(sys.argv[sys.argv.index("--max-prs") + 1]) if "--max-prs" in sys.argv else None,
            early="--early-cut" in sys.argv)
