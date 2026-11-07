"""Summaries for arms B and C, with the leak check from plan.md.

Same prompt and model for both sides. A summary leaks if it contains (a) a code-shaped name
added by the merged PR (in an added line of merged.diff, absent from the base versions of the
touched files and from the issue), or (b) six consecutive code tokens from an added line, at least
two of them symbols. Leak -> one regeneration with the names forbidden -> still leaking -> mask.

Usage: python -I summarise.py <pr id> [<pr id> ...]
"""
import json
import re
import sys
from pathlib import Path

import llm
from prepare import PRS, SNAP

MAX_WORDS = 150
HUNK_LINES = 20
CODE_NAME = re.compile(r"\b(?:[A-Za-z]\w*_\w+|_\w+|[a-z]+[A-Z]\w*|[A-Z][a-z0-9]+[A-Z]\w*)\b")
TOKEN = re.compile(r"\w+|[^\w\s]")

PROMPT = """Below are inline code-review comments left on a pull request in the repository {repo}. Each comment comes with the file path and the end of the diff hunk it refers to. The pull request resolves this issue:

<issue>
{issue}
</issue>

<comments>
{comments}
</comments>

Write guidance for a developer who will implement this change from scratch, without seeing the pull request or these comments. Say what the comments ask the change to do, and why, as their authors saw it. Rules:
- At most {max_words} words, plain sentences or short bullet points.
- What and why only, never how: no code, no snippets, no names of functions, variables, classes, files or settings that the pull request itself introduces.
- Do not mention comments, reviewers, review or the pull request. Write it as guidance about the change itself.
- If the comments only raise minor points, summarise those briefly.{forbidden}

Reply with the guidance only."""


def issue_text(meta):
    return "\n\n".join(f"#{i['number']} {i['title']}\n\n{i['body']}".strip() for i in meta["issues"])


def render_comments(items):
    out = []
    for n, c in enumerate(items, 1):
        hunk = "\n".join((c.get("diff_hunk") or "").splitlines()[-HUNK_LINES:])
        out.append(f"[{n}] file: {c['path']}\nhunk:\n{hunk}\ncomment:\n{c['body']}")
    return "\n\n".join(out)


def added_lines(diff):
    return [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]


def base_text(pid, meta):
    parts = []
    for f in meta["files"]:
        p = SNAP / pid / "base" / f
        if p.is_file():
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def leak_targets(pid, meta, diff):
    adds = added_lines(diff)
    known = base_text(pid, meta) + "\n" + issue_text(meta)
    known_names = set(CODE_NAME.findall(known))
    new_names = {n for l in adds for n in CODE_NAME.findall(l)} - known_names
    grams = set()
    for l in adds:
        t = TOKEN.findall(l)
        for i in range(len(t) - 5):
            g = tuple(t[i:i + 6])
            if sum(1 for x in g if not re.match(r"\w", x)) >= 2:
                grams.add(g)
    return new_names, grams


def leaks(text, new_names, grams):
    names = sorted(n for n in new_names if re.search(rf"(?<!\w){re.escape(n)}(?!\w)", text))
    t = TOKEN.findall(text)
    hit = [" ".join(t[i:i + 6]) for i in range(len(t) - 5) if tuple(t[i:i + 6]) in grams]
    return names, hit


def summarise(pid, side):
    d = PRS / pid
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    items = json.loads((d / f"review_{side}.json").read_text(encoding="utf-8"))
    out = d / f"summary_{side}.json"
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    if not items:
        rec = {"side": side, "text": None, "reason": "no comments"}
        out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
        return rec
    diff = (d / "merged.diff").read_text(encoding="utf-8")
    new_names, grams = leak_targets(pid, meta, diff)
    base = dict(repo=meta["repo"], issue=issue_text(meta), comments=render_comments(items), max_words=MAX_WORDS)
    rec = {"side": side, "comments": len(items), "attempts": []}
    forbidden = ""
    for attempt in range(2):
        r = llm.call(PROMPT.format(**base, forbidden=forbidden), role="summary", pr=pid, tag=side,
                     model=llm.OPUS, effort="medium", timeout=600)
        if r["status"] != "ok":
            rec.update(text=None, reason=f"call {r['status']}")
            out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
            return rec
        text = (r["result"] or "").strip()
        names, grams_hit = leaks(text, new_names, grams)
        rec["attempts"].append({"text": text, "leak_names": names, "leak_grams": grams_hit})
        if not names and not grams_hit:
            break
        forbidden = ("\n- These names must not appear: " + ", ".join(names)) if names else ""
        if grams_hit:
            forbidden += "\n- Do not quote code from the change."
    text = rec["attempts"][-1]["text"]
    masked = []
    for n in rec["attempts"][-1]["leak_names"]:
        text = re.sub(rf"(?<!\w){re.escape(n)}(?!\w)", "[a new name]", text)
        masked.append(n)
    rec.update(text=text, words=len(text.split()), regenerated=len(rec["attempts"]) > 1, masked=masked,
               leak_first=bool(rec["attempts"][0]["leak_names"] or rec["attempts"][0]["leak_grams"]),
               gram_leak_final=bool(rec["attempts"][-1]["leak_grams"]))
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


if __name__ == "__main__":
    for pid in sys.argv[1:]:
        for side in ("B", "C"):
            r = summarise(pid, side)
            print(pid, side, r.get("words"), "leak_first", r.get("leak_first"), "masked", r.get("masked"),
                  r.get("reason", ""), flush=True)
