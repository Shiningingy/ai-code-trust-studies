"""Study 06 follow-up, step 4, arms L / PL / LC: Stop hook that checks the read ledger once before the answer counts.

Invoked by Claude Code as:  python -I ledger_hook.py <state_dir> <mode>     mode = list | count | parse
stdin: the Stop-hook JSON (transcript_path, cwd, stop_hook_active, ...).

The ledger is computed from the transcript at stop time: a sentence of context.md is SEEN when its exact text appears
in any tool result returned to the model (same rule as ledger.py). No PostToolUse hook is needed for that.
- list:  show the reader-flagged sentences (state_dir/flagged.json, from haiku_reader.py) that were never SEEN.
- count: show only how many sentences of context.md were never SEEN.
- parse (arm D): every non-empty, non-heading line of context.md before the final query must appear in the agent's
  parsed.jsonl ({"line": n, ...}); the missing line numbers are named. Checks presence only, not parse quality.
Blocks once per run (JSON decision "block" on stdout, whose reason Claude Code returns to the agent); every later stop is
allowed.
Writes state_dir/ledger_check.json: what was shown, and the answer text the agent had given when it was blocked.
"""
import json
import os
import re
import sys

LIST_MSG = ("Before your answer is final: these lines may be relevant and were never shown to you. "
            "Check them, then give your final answer.")
COUNT_MSG = ("Before your answer is final: {u} of the {t} sentences in the context were never shown to you. "
             "Check whether any of them matter, then give your final answer.")
PARSE_MSG = ("Before your answer is final: these lines of context.md are not in parsed.jsonl: {lines}. "
             "Parse them or mark them as outliers, then give your final answer.")
PARSE_NOFILE_MSG = ("Before your answer is final: parsed.jsonl was not found. Create it as instructed, "
                    "then give your final answer.")
SPLIT = re.compile(r"(?<=[.!?])(?<!\b[A-Z]\.)\s+")  # sentence ends, but not after an initial such as "D."


def sentences(text):
    """(line number, sentence) for every sentence of the documents, the final query excluded."""
    i = text.rfind("Final Query")
    body = text[:i] if i >= 0 else text
    out = []
    for n, line in enumerate(body.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out += [(n, s.strip()) for s in SPLIT.split(line) if len(s.strip()) >= 12]
    return out


def content_lines(text):
    """Line numbers (1-based) of the non-empty, non-heading lines before the final query."""
    i = text.rfind("Final Query")
    body = text[:i] if i >= 0 else text
    return {n for n, line in enumerate(body.splitlines(), 1) if line.strip() and not line.strip().startswith("#")}


def parsed_lines(path):
    """(lines present, lines marked outlier, unreadable rows) from the agent's parsed.jsonl; (None, None, 0) if absent."""
    if not os.path.exists(path):
        return None, None, 0
    got, outl, bad = set(), set(), 0
    for row in open(path, encoding="utf-8", errors="replace"):
        row = row.strip()
        if not row:
            continue
        try:
            d = json.loads(row)
            n = int(d["line"])
        except (ValueError, KeyError, TypeError):
            bad += 1
            continue
        got.add(n)
        if d.get("outlier"):
            outl.add(n)
    return got, outl, bad


def ranges(nums):
    """[3,4,5,9] -> '3-5, 9' (at most 200 ranges, then a count)."""
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(str(start) if start == prev else "%d-%d" % (start, prev))
            start = prev = n
    if start is not None:
        out.append(str(start) if start == prev else "%d-%d" % (start, prev))
    return ", ".join(out[:200]) + (" and %d more ranges" % (len(out) - 200) if len(out) > 200 else "")


def transcript(path):
    """All tool-result text returned to the model, and the last assistant text."""
    outs, last = [], ""
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        msg = d.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        texts = []
        for c in content:
            if c.get("type") == "tool_result":
                r = c.get("content")
                if isinstance(r, list):
                    r = "\n".join(x.get("text", "") for x in r if isinstance(x, dict))
                outs.append(str(r))
            elif c.get("type") == "text" and msg.get("role") == "assistant":
                texts.append(c.get("text", ""))
        if texts:
            last = "\n".join(texts)
    return "\n".join(outs), last


def main():
    state_dir, mode = sys.argv[1], sys.argv[2]
    hook = json.loads(sys.stdin.read() or "{}")
    done = os.path.join(state_dir, "ledger_check.json")
    if hook.get("stop_hook_active") or os.path.exists(done):
        sys.exit(0)
    text = open(os.path.join(hook.get("cwd") or os.getcwd(), "context.md"), encoding="utf-8").read()
    S = sentences(text)
    blob, last = transcript(hook.get("transcript_path", ""))
    unseen = [i for i, (_, s) in enumerate(S) if s not in blob]
    rec = {"mode": mode, "sentences": len(S), "unseen": len(unseen), "answer_before_check": last[-2000:]}
    if mode == "parse":
        need = content_lines(text)
        got, outl, bad = parsed_lines(os.path.join(hook.get("cwd") or os.getcwd(), "parsed.jsonl"))
        rec.update(content_lines=len(need), parsed=len(got - outl) if got is not None else None,
                   outliers=len(outl) if got is not None else None, bad_rows=bad)
        if got is None:
            message = PARSE_NOFILE_MSG
            rec["missing"] = len(need)
        else:
            missing = sorted(need - got)
            rec["missing"] = len(missing)
            if not missing:
                rec["note"] = "every content line accounted for; not blocked"
                json.dump(rec, open(done, "w", encoding="utf-8"))
                sys.exit(0)
            message = PARSE_MSG.format(lines=ranges(missing))
    elif mode == "count":
        if not unseen:
            rec["note"] = "every sentence seen; not blocked"
            json.dump(rec, open(done, "w", encoding="utf-8"))
            sys.exit(0)
        message = COUNT_MSG.format(u=len(unseen), t=len(S))
    else:
        flagged = json.load(open(os.path.join(state_dir, "flagged.json"), encoding="utf-8"))["flagged_text"]
        fl = set(flagged)
        show = [(n, s) for (n, s) in S if s in fl and s not in blob]
        rec.update(flagged=len(fl), shown=len(show))
        if not show:
            rec["note"] = "no flagged sentence left unseen; not blocked"
            json.dump(rec, open(done, "w", encoding="utf-8"))
            sys.exit(0)
        message = LIST_MSG + "\n\n" + "\n".join("line %d: %s" % (n, s) for n, s in show)
    rec["message_chars"] = len(message)
    json.dump(rec, open(done, "w", encoding="utf-8"))
    print(json.dumps({"decision": "block", "reason": message}))
    sys.exit(0)


if __name__ == "__main__":
    main()
