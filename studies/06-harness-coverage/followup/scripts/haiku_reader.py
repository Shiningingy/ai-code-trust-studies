"""Study 06 follow-up: can a small model read every sentence and flag the ones that matter? (offline test, no agent)

The harness numbers every sentence of context.md (the ledger's index), cuts them into chunks, and asks a small model,
chunk by chunk with no tools, which numbered sentences state or deny any of the query's conditions for anyone.
Prompt wording agreed with Zili Luo 2026-11-25: the query's conditions verbatim, plus "when unsure, include it";
no hints about traps.

Usage: python -I haiku_reader.py <context.md> <out_dir> [model=haiku] [chunks=20]
Writes out_dir/sentences.json (index -> sentence), out_dir/chunk-NN.json (raw replies), out_dir/flagged.json.
"""
import json
import os
import re
import subprocess
import sys

CLAUDE_EXE = os.environ.get("CLAUDE_EXE") or os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules", "@anthropic-ai", "claude-code", "bin", "claude.exe")


def sentences(text):
    out = []
    body = text[:text.rfind("Final Query")] if "Final Query" in text else text
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]
    return out


def main():
    ctx, out_dir = sys.argv[1], sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "haiku"
    n_chunks = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    os.makedirs(out_dir, exist_ok=True)
    text = open(ctx, encoding="utf-8").read()
    S = sentences(text)
    json.dump(S, open(os.path.join(out_dir, "sentences.json"), "w", encoding="utf-8"))
    q = text[text.rfind("Final Query"):]
    conds = "\n".join(l for l in q.splitlines() if re.match(r"c\d+\.", l.strip()))
    size = -(-len(S) // n_chunks)
    flagged, cost = set(), 0.0
    for c in range(n_chunks):
        lo, hi = c * size, min(len(S), (c + 1) * size)
        if lo >= hi:
            break
        numbered = "\n".join("[%d] %s" % (i, S[i]) for i in range(lo, hi))
        prompt = ("Below are numbered sentences from a long document. A later question asks for every person who "
                  "satisfies all of these conditions:\n" + conds + "\n\n"
                  "List the number of every sentence that states or denies any of these conditions for anyone. "
                  "When unsure, include it. Reply with the numbers only, separated by commas.\n\n" + numbered)
        p = subprocess.run([CLAUDE_EXE, "-p", "--model", model, "--setting-sources", "", "--settings",
                            '{"autoMemoryEnabled": false}', "--tools", "", "--no-session-persistence",
                            "--output-format", "json"], input=prompt, capture_output=True, text=True,
                           encoding="utf-8", timeout=600, cwd=out_dir)
        try:
            d = json.loads(p.stdout)
        except ValueError:
            d = {"result": "", "error": p.stderr[-500:]}
        json.dump(d, open(os.path.join(out_dir, "chunk-%02d.json" % c), "w", encoding="utf-8"))
        nums = {int(x) for x in re.findall(r"\d+", d.get("result") or "") if lo <= int(x) < hi}
        flagged |= nums
        cost += float(d.get("total_cost_usd") or 0)
        print("chunk %02d [%d-%d]: %d flagged, $%.4f" % (c, lo, hi - 1, len(nums), float(d.get("total_cost_usd") or 0)), flush=True)
    json.dump({"model": model, "sentences": len(S), "flagged": sorted(flagged), "cost": round(cost, 4)},
              open(os.path.join(out_dir, "flagged.json"), "w", encoding="utf-8"))
    print("total: %d of %d sentences flagged, $%.4f" % (len(flagged), len(S), cost))


if __name__ == "__main__":
    main()
