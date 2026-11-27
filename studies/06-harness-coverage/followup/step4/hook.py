"""Step 4 Stop hook for the grammar sessions. Runs from a neutral copy with a pristine copy of gram/ beside it,
so a session that edits its own gram/ cannot change what is checked.

  python -I hook.py <state_dir> learn       learning session: feedback on the training answers, the library's tests
                                            and unresolved clauses; blocks up to MAX_ROUNDS times
  python -I hook.py <state_dir> reconcile   as learn, and lib/RECONCILE.md must name every disagreement group
  python -I hook.py <state_dir> test        test session: blocks once if clauses of context.md are unresolved or the
                                            library's tests fail; names up to 50 clauses
  An optional third argument gives the workspace. Without it the hook uses the cwd Claude Code reports, which is the
  agent's current folder and can be a subfolder after a `cd` in Bash (the step-4 "library does not load" runs);
  step 5 always passes it.

state_dir holds keys.json (learn/reconcile; never in the workspace), groups.json (reconcile), v0_hashes.json (test).
Every call appends to state_dir/hook_log.jsonl.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram.pipeline import LibraryError, parse_text, run_tests, summary  # noqa: E402

MAX_ROUNDS = 6
LIST_MAX = 50

LEARN_MSG = ("Not finished yet. Training answers: {answers}. Library tests: {tests}. Unresolved clauses: {unres}. "
             "Keep working, then stop again.")
RECON_EXTRA = " Disagreement groups not yet recorded in lib/RECONCILE.md: {groups}."
TEST_MSG = ("Before your answer is final: the library does not resolve everything in context.md. {tests}{n} clauses "
            "are unresolved:\n{lst}\nResolve them as instructed, then give your final answer.")


def last_text(transcript_path):
    last = ""
    try:
        for line in open(transcript_path, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            msg = d.get("message") or {}
            if not isinstance(msg, dict):
                continue
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                t = "\n".join(c.get("text", "") for c in msg["content"] if c.get("type") == "text")
                if t:
                    last = t
    except OSError:
        pass
    return last[-2000:]


def lib_hashes(lib):
    out = {}
    root = os.path.join(lib, "parts")
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".py"):
                p = os.path.join(dp, f)
                out[os.path.relpath(p, lib).replace("\\", "/")] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out


def check_lib(cwd, docs):
    """(tests message, n failing or None if the library does not load, {doc: unresolved}, {doc: summary})."""
    lib = os.path.join(cwd, "lib")
    try:
        fails = run_tests(lib)
    except LibraryError as e:
        return "library does not load (%s)" % e, None, {d: None for d in docs}, {}
    unres, sums = {}, {}
    for d, (path, manual) in docs.items():
        try:
            recs = parse_text(open(path, encoding="utf-8").read(), lib, manual)
        except LibraryError as e:
            return "library does not load (%s)" % e, None, {d: None for d in docs}, {}
        sums[d] = summary(recs)
        unres[d] = sum(1 for r in recs for c in r["clauses"] if c["status"] not in ("parsed", "ignored", "manual"))
    return ("all pass" if not fails else "%d failing" % len(fails)), len(fails), unres, sums


def main():
    state, mode = sys.argv[1], sys.argv[2]
    hook = json.loads(sys.stdin.read() or "{}")
    cwd = sys.argv[3] if len(sys.argv) > 3 else (hook.get("cwd") or os.getcwd())
    rounds_path = os.path.join(state, "rounds.txt")
    rounds = int(open(rounds_path).read()) if os.path.exists(rounds_path) else 0
    rec = {"mode": mode, "round": rounds + 1, "answer_text": last_text(hook.get("transcript_path", ""))}
    block, msg = False, ""

    if mode in ("learn", "reconcile"):
        keys = json.load(open(os.path.join(state, "keys.json"), encoding="utf-8"))
        docs = {d: (os.path.join(cwd, "train", d + ".md"), os.path.join(cwd, "train", d + ".manual.jsonl")) for d in keys}
        tests, nfail, unres, sums = check_lib(cwd, docs)
        try:
            ans = json.load(open(os.path.join(cwd, "answers.json"), encoding="utf-8"))
        except (OSError, ValueError):
            ans = {}
        verdict = {d: ("not given" if d not in ans else ("correct" if sorted(ans[d]) == sorted(keys[d]) else "incorrect"))
                   for d in keys}
        rec.update(tests=tests, unresolved=unres, verdict=verdict, summaries=sums)
        done = (nfail == 0 and all(v == 0 for v in unres.values()) and all(v == "correct" for v in verdict.values()))
        missing = []
        if mode == "reconcile":
            groups = json.load(open(os.path.join(state, "groups.json"), encoding="utf-8"))
            notes_path = os.path.join(cwd, "lib", "RECONCILE.md")
            notes = open(notes_path, encoding="utf-8").read() if os.path.exists(notes_path) else ""
            missing = [g for g in groups if g not in notes]
            done = done and not missing
            rec["groups_missing"] = missing
        if not done and rounds < MAX_ROUNDS:
            block = True
            msg = LEARN_MSG.format(answers=", ".join("%s %s" % kv for kv in verdict.items()), tests=tests,
                                   unres=", ".join("%s %s" % (d, "?" if u is None else u) for d, u in unres.items()))
            if missing:
                msg += RECON_EXTRA.format(groups=", ".join(missing[:40]) + (" ..." if len(missing) > 40 else ""))
        rec["done"] = done
    else:  # test
        if rounds >= 1:
            sys.exit(0)
        lib = os.path.join(cwd, "lib")
        v0 = json.load(open(os.path.join(state, "v0_hashes.json"), encoding="utf-8"))
        now = lib_hashes(lib)
        rec["edited_v0_parts"] = sorted(k for k in v0 if now.get(k) != v0[k])
        rec["new_parts"] = sorted(k for k in now if k not in v0)
        try:
            fails = run_tests(lib)
            recs = parse_text(open(os.path.join(cwd, "context.md"), encoding="utf-8").read(), lib,
                              os.path.join(cwd, "manual.jsonl"))
            bad = [(r["line"], c) for r in recs for c in r["clauses"] if c["status"] not in ("parsed", "ignored", "manual")]
            rec.update(tests_failing=len(fails), unresolved=len(bad), summary=summary(recs))
            tests = "" if not fails else "%d of the library's tests fail. " % len(fails)
        except LibraryError as e:
            bad, fails = [], ["load"]
            rec.update(library_error=str(e))
            tests = "The library does not load (%s). " % e
        if bad or fails:
            block = True
            lst = "\n".join("line %d: %s (%s)" % (n, c["text"][:200], c["status"]) for n, c in bad[:LIST_MAX])
            if len(bad) > LIST_MAX:
                lst += "\n... and %d more" % (len(bad) - LIST_MAX)
            msg = TEST_MSG.format(tests=tests, n=len(bad), lst=lst or "(none)")

    rec["blocked"] = block
    with open(os.path.join(state, "hook_log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    if block:
        open(rounds_path, "w").write(str(rounds + 1))
        print(json.dumps({"decision": "block", "reason": msg}))
    elif mode == "test":
        open(rounds_path, "w").write(str(rounds + 1))
    sys.exit(0)


if __name__ == "__main__":
    main()
