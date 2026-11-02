"""Rewriter: issue text in, screened rewrites out. Sees no code.

Code, stack traces and exact values are swapped for placeholders before the model
sees the issue and swapped back after, so a rewrite cannot change them. A separate
call then screens each rewrite for drift in meaning.
"""
import json
import re
import sys
import time
from pathlib import Path

from model_service import claude_backend, judge

KINDS = {
    "paraphrase": "Rewrite this bug report in your own words. Keep every fact, and add nothing.",
    "stepwise": "Rewrite this bug report as a numbered list of steps: what is set up, what is done, "
                "what happens, and, only if the report states it, what should happen instead. "
                "Keep every fact, and add nothing. Leave out any step the report gives no facts for.",
}
RULES = """You rewrite bug reports. You have not seen the code and must not guess at it.

Rules:
- Tokens like [[KEEP0]] stand for code or exact values. Keep every token exactly as written, once each, in any sensible place.
- Do not suggest a cause or a fix unless the report already does.
- Do not add examples, details or expected behaviour the report does not state.
- Reply with the rewritten report only."""
SCREEN = """Two bug reports follow. Tokens like [[KEEP0]] stand for identical code or values.

Decide whether B describes the same bug as A: same setup, same behaviour, same expected result. B must not add a fact, drop a fact or change a fact. Wording and order may differ.

<A>
{a}
</A>

<B>
{b}
</B>"""
SCREEN_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["reason", "same"],
                 "properties": {"reason": {"type": "string"}, "same": {"type": "boolean"}}}
TRIES = 3

KEEP = re.compile(
    r"```.*?```"                                     # fenced code
    r"|~~~.*?~~~"
    r"|^Traceback \(most recent call last\):.*?(?=\n\s*\n|\Z)"   # stack traces
    r"|^(?: {4}|\t)[ \t]*\S[^\n]*(?:\n(?: {4}|\t)[^\n]*)*"   # indented code, not blank lines
    r"|^>>> [^\n]*(?:\n(?!\s*\n)[^\n]*)*"            # doctest sessions
    r"|`[^`\n]+`"                                    # inline code
    r"|\"[^\"\n]{1,200}\""                           # quoted values
    r"|(?<!\w)'[^'\n]{2,200}'(?!\w)"
    r"|https?://\S+"
    r"|\b\d+(?:\.\d+)+\b",                           # versions and decimals
    re.DOTALL | re.MULTILINE,
)


def protect(issue):
    kept = []

    def swap(m):
        kept.append(m.group(0))
        return f"[[KEEP{len(kept) - 1}]]"

    return KEEP.sub(swap, issue), kept


def restore(text, kept):
    for i, value in enumerate(kept):
        text = text.replace(f"[[KEEP{i}]]", value)
    return text


def placeholders_intact(text, kept):
    """Every masked item must appear; a numbered rewrite may mention one twice."""
    found = re.findall(r"\[\[KEEP(\d+)\]\]", text)
    return set(map(int, found)) == set(range(len(kept)))


def rewrite(issue, kind, backend=claude_backend):
    """Returns (rewritten issue or None, log of tries)."""
    masked, kept = protect(issue)
    log = []
    for _ in range(TRIES):
        code, raw = backend(RULES, f"{KINDS[kind]}\n\n<REPORT>\n{masked}\n</REPORT>", None)
        why = judge(code, raw, None)
        if why:
            raise RuntimeError(f"rewrite call failed: {why}")
        text = json.loads(raw)["result"].strip()
        if not placeholders_intact(text, kept):
            log.append({"kind": kind, "verdict": "placeholders changed"})
            continue
        code, raw = backend("You compare bug reports.", SCREEN.format(a=masked, b=text), SCREEN_SCHEMA)
        why = judge(code, raw, SCREEN_SCHEMA)
        if why:
            raise RuntimeError(f"screen call failed: {why}")
        verdict = json.loads(raw)["structured_output"]
        log.append({"kind": kind, "verdict": "same" if verdict["same"] else "drift", "reason": verdict["reason"]})
        if verdict["same"]:
            return restore(text, kept), log
    return None, log


def logged_backend(ledger):
    def call(system, prompt, schema):
        started = time.time()
        code, raw = claude_backend(system, prompt, schema)
        row = {"t": started, "seconds": round(time.time() - started, 1), "token": "rewriter",
               "outcome": "failed" if judge(code, raw, schema) else "ok"}
        if row["outcome"] == "ok":
            data = json.loads(raw)
            row.update({k: data.get(k) for k in ("usage", "modelUsage", "total_cost_usd")})
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        return code, raw

    return call


def main():
    sys.path.insert(0, str(Path(__file__).parent))
    from runner import DATASET, LEDGER, REWRITES, RUNS

    arm = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    backend = logged_backend(LEDGER)
    bugs = {b["instance_id"]: b for b in json.load(open(DATASET, encoding="utf-8"))}
    REWRITES.mkdir(exist_ok=True)
    failed_file = RUNS / "screen-failed.txt"  # three tries is final: a later pass must not re-roll these
    failed = set(failed_file.read_text().split()) if failed_file.exists() else set()
    for mark in sorted((RUNS / arm / "done").glob("*.json")):
        record = json.loads(mark.read_text())
        out = REWRITES / f"{record['bug']}.json"
        if not record["emitted"] or out.exists() or record["bug"] in failed:
            continue
        issue = bugs[record["bug"]]["problem_statement"]
        result, tries = {}, []
        for kind in KINDS:
            text, log = rewrite(issue, kind, backend)
            tries += log
            if text is None:
                print(record["bug"], kind, "no rewrite passed the screen", flush=True)
                with open(failed_file, "a") as f:
                    f.write(record["bug"] + "\n")
                break
            result[kind] = text
        else:
            out.write_text(json.dumps({**result, "tries": tries}, indent=1), encoding="utf-8")
            print(record["bug"], "ok", len(tries), "tries", flush=True)


if __name__ == "__main__":
    main()
