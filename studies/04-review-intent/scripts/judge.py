"""Stage 2: rubric (once per PR), scrub, and the two blind inspectors (per implementation).

The rubric writer sees the issue and the merged PR only, never review text or agent output.
Inspectors see the issue, the rubric, the scrubbed diff, the scrubbed touched non-test files after
the change (line-numbered) and the stage-1 result, never the arm or each other.

Usage: python -I judge.py rubric <pr id> | inspect <pr id> <tag>
"""
import difflib
import json
import re
import sys

import llm
from prepare import PRS, SNAP, TEST_PATH
from summarise import issue_text

MAX_DIFF = 120_000
MAX_FILE = 60_000
MAX_FILES_TOTAL = 200_000
MENTION = re.compile(r"review|reviewer|guidance|feedback", re.I)
COMMENT = {"Python": re.compile(r"^(\s*)#"), "Go": re.compile(r"^(\s*)//")}
TRAILING = {"Python": re.compile(r"\s+#.*$"), "Go": re.compile(r"\s+//.*$")}

RUBRIC_SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {
    "type": "array", "minItems": 3, "maxItems": 8, "items": {
        "type": "object", "required": ["id", "behaviour"],
        "properties": {"id": {"type": "string"}, "behaviour": {"type": "string"},
                       "check": {"type": "string"}}}}}}

RUBRIC_PROMPT = """You are writing a grading rubric for implementations of a change to the {repo} repository. Below are the issue the change resolves and the pull request the project merged for it.

<issue>
{issue}
</issue>

<pull_request>
title: {title}

description:
{body}

diff:
{diff}
</pull_request>

Write 3 to 8 rubric items. Each item is one behaviour that a correct resolution of this issue should have, as the merged change shows it. Rules:
- Describe behaviour that can be checked by reading an implementation's code: what happens in which situation (inputs, outputs, errors, side effects, configuration, compatibility).
- A different correct implementation must be able to meet every item. Do not require particular names, files, code structure or wording unless the issue itself requires them.
- Tests, documentation and code style are not items.
- Order items from most to least central to the issue. Give ids R1, R2, ...
- In "check", say briefly what to look for in an implementation to decide the item."""

INSPECT_SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {
    "type": "array", "items": {"type": "object", "required": ["id", "verdict", "evidence"], "properties": {
        "id": {"type": "string"}, "verdict": {"type": "string", "enum": ["met", "not_met", "cant_tell"]},
        "evidence": {"type": "string"}}}}}}

INSPECT_PROMPT = """You are checking one implementation of a change to the {repo} repository against a rubric.

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

<test_result>
{tests}
</test_result>

For every rubric item decide from the code whether this implementation meets it: "met", "not_met", or "cant_tell" when the code shown is not enough to decide. Give evidence as file:line plus one sentence. Judge behaviour, not names or structure."""


def scrub_lines(lines, added, lang):
    out, n = [], 0
    for i, line in enumerate(lines):
        if i in added and MENTION.search(line):
            if COMMENT[lang].match(line):
                n += 1
                continue
            m = TRAILING[lang].search(line)
            if m and MENTION.search(m.group(0)):
                line = line[:m.start()]
                n += 1
        out.append(line)
    return out, n


def scrub(pid, tag):
    """Scrubbed diff and touched non-test files; returns (diff, {path: text}, count)."""
    d = PRS / pid
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    arm = d / "arms" / tag
    lang, count = meta["language"], 0
    diff_lines = (arm / "agent.diff").read_text(encoding="utf-8").splitlines()
    added = {i for i, l in enumerate(diff_lines) if l.startswith("+") and not l.startswith("+++")}
    plain = [l[1:] if i in added else l for i, l in enumerate(diff_lines)]
    kept, n = scrub_lines(plain, added, lang)
    count += n
    # rebuild with '+' markers: scrub_lines keeps order and drops whole lines only
    diff_out, j = [], 0
    for i, l in enumerate(diff_lines):
        if i in added:
            new = plain[i]
            if COMMENT[lang].match(new) and MENTION.search(new):
                continue
            m = TRAILING[lang].search(new)
            if m and MENTION.search(m.group(0)):
                new = new[:m.start()]
            diff_out.append("+" + new)
        else:
            diff_out.append(l)
    files = {}
    after = arm / "after"
    for p in sorted(after.rglob("*")) if after.exists() else []:
        rel = p.relative_to(after).as_posix()
        if not p.is_file() or TEST_PATH[lang].search(rel):
            continue
        text = p.read_text(encoding="utf-8", errors="replace").splitlines()
        basef = SNAP / pid / "base" / rel
        base = basef.read_text(encoding="utf-8", errors="replace").splitlines() if basef.is_file() else []
        sm = difflib.SequenceMatcher(None, base, text, autojunk=False)
        new_idx = {k for tag_, a1, a2, b1, b2 in sm.get_opcodes() if tag_ in ("replace", "insert")
                   for k in range(b1, b2)}
        lines, n = scrub_lines(text, new_idx, lang)
        count += n
        files[rel] = "\n".join(lines)
    return "\n".join(diff_out), files, count


def rubric(pid):
    d = PRS / pid
    out = d / "rubric.json"
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    diff = (d / "merged.diff").read_text(encoding="utf-8")
    if len(diff) > MAX_DIFF:
        diff = diff[:MAX_DIFF] + f"\n[... diff cut, {len(diff) - MAX_DIFF} more characters ...]"
    r = llm.call(RUBRIC_PROMPT.format(repo=meta["repo"], issue=issue_text(meta), title=meta["title"],
                                      body=meta["body"] or "(none)", diff=diff),
                 role="rubric", pr=pid, model=llm.OPUS, effort="medium", schema=RUBRIC_SCHEMA, timeout=900)
    if r["status"] != "ok" or not r["structured"]:
        raise RuntimeError(f"rubric call {r['status']} for {pid}")
    out.write_text(json.dumps(r["structured"], indent=1), encoding="utf-8")
    return r["structured"]


def numbered(files):
    parts, total = [], 0
    for path, text in files.items():
        lines = text.splitlines()
        body = "\n".join(f"{i + 1:>5}  {l}" for i, l in enumerate(lines))
        if len(body) > MAX_FILE:
            body = body[:MAX_FILE] + "\n[... file cut ...]"
        if total + len(body) > MAX_FILES_TOTAL:
            parts.append(f"=== {path} (omitted: size limit) ===")
            continue
        total += len(body)
        parts.append(f"=== {path} ===\n{body}")
    return "\n\n".join(parts) or "(no non-test files changed)"


def inspect(pid, tag):
    d = PRS / pid
    arm = d / "arms" / tag
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    rub = rubric(pid)
    s1 = json.loads((arm / "stage1.json").read_text(encoding="utf-8"))
    diff, files, scrubs = scrub(pid, tag)
    (arm / "scrub.json").write_text(json.dumps({"scrubbed_lines": scrubs}), encoding="utf-8")
    ids = [i["id"] for i in rub["items"]]
    results = {}
    for who, model in (("opus", llm.OPUS), ("sonnet", llm.SONNET)):
        out = arm / f"inspect_{who}.json"
        if out.exists():
            results[who] = json.loads(out.read_text(encoding="utf-8"))
            continue
        if not diff.strip():
            rec = {"empty_diff": True, "items": [{"id": i, "verdict": "not_met", "evidence": "empty diff"} for i in ids]}
        else:
            tests = (f"The project's own tests for this change were run on this implementation. Resolved: "
                     f"{'yes' if s1['resolved'] else 'no'}. Target tests passed: {s1['f2p_passed']} of "
                     f"{s1['f2p_total']}. Existing tests still passing: {s1['p2p_passed']} of {s1['p2p_total']}.")
            if s1["f2p_failed"]:
                tests += "\nTarget tests not passing: " + ", ".join(s1["f2p_failed"][:20])
            rtext = "\n".join(f"{i['id']}: {i['behaviour']}" + (f"\n    check: {i['check']}" if i.get("check") else "")
                              for i in rub["items"])
            dd = diff if len(diff) <= MAX_DIFF else diff[:MAX_DIFF] + "\n[... diff cut ...]"
            r = llm.call(INSPECT_PROMPT.format(repo=meta["repo"], issue=issue_text(meta), rubric=rtext, diff=dd,
                                               files=numbered(files), tests=tests),
                         role="inspector", pr=pid, tag=f"{tag}/{who}", model=model, effort="medium",
                         schema=INSPECT_SCHEMA, timeout=900)
            if r["status"] != "ok" or not r["structured"]:
                raise RuntimeError(f"inspector {who} {r['status']} for {pid} {tag}")
            got = {i["id"]: i for i in r["structured"]["items"]}
            rec = {"items": [got.get(i, {"id": i, "verdict": "cant_tell", "evidence": "item not returned"})
                             for i in ids]}
        rec["score"] = sum(i["verdict"] == "met" for i in rec["items"]) / len(ids)
        out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
        results[who] = rec
    return results


if __name__ == "__main__":
    if sys.argv[1] == "rubric":
        print(json.dumps(rubric(sys.argv[2]), indent=1))
    else:
        r = inspect(sys.argv[2], sys.argv[3])
        print({k: v["score"] for k, v in r.items()})
