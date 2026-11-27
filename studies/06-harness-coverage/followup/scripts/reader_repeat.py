"""Is the reader's thinking-on/off difference real or chance? Re-ask the same chunks several times each way.

Usage: python -I reader_repeat.py <v2 out_dir of haiku_reader.py> <context.md> <reps> <sentence index> [...]
For each listed sentence, the v2 chunk holding it is re-sent <reps> times with thinking on and <reps> times with it
off (same prompt as haiku_reader.py); prints how often each listed sentence was flagged. Chunks are the v2 ones
(20 per file).
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from haiku_reader import CLAUDE_EXE  # noqa: E402

d, ctx, reps, targets = sys.argv[1], sys.argv[2], int(sys.argv[3]), [int(x) for x in sys.argv[4:]]
S = json.load(open(os.path.join(d, "sentences.json"), encoding="utf-8"))
text = open(ctx, encoding="utf-8").read()
q = text[text.rfind("Final Query"):]
conds = "\n".join(l for l in q.splitlines() if re.match(r"c\d+\.", l.strip()))
size = -(-len(S) // 20)
chunks = sorted({t // size for t in targets})
tally, cost = {}, {"on": 0.0, "off": 0.0}
for c in chunks:
    lo, hi = c * size, min(len(S), (c + 1) * size)
    numbered = "\n".join("[%d] %s" % (i, S[i]) for i in range(lo, hi))
    prompt = ("Below are numbered sentences from a long document. A later question asks for every person who "
              "satisfies all of these conditions:\n" + conds + "\n\n"
              "List the number of every sentence that states or denies any of these conditions for anyone. "
              "When unsure, include it. Reply with the numbers only, separated by commas.\n\n" + numbered)
    for mode in ("on", "off"):
        settings = '{"autoMemoryEnabled": false%s}' % (', "alwaysThinkingEnabled": false' if mode == "off" else "")
        for r in range(reps):
            p = subprocess.run([CLAUDE_EXE, "-p", "--model", "haiku", "--setting-sources", "", "--settings", settings,
                                "--tools", "", "--no-session-persistence", "--output-format", "json"], input=prompt,
                               capture_output=True, text=True, encoding="utf-8", timeout=600, cwd=d)
            try:
                out = json.loads(p.stdout)
            except ValueError:
                out = {}
            nums = {int(x) for x in re.findall(r"\d+", out.get("result") or "") if lo <= int(x) < hi}
            cost[mode] += float(out.get("total_cost_usd") or 0)
            for t in targets:
                if lo <= t < hi:
                    tally.setdefault((t, mode), []).append(t in nums)
            print("chunk %d thinking %s rep %d: %d flagged" % (c, mode, r + 1, len(nums)), flush=True)
print()
for t in targets:
    print("[%d] %s" % (t, S[t][:110]))
    for mode in ("on", "off"):
        v = tally.get((t, mode), [])
        print("    thinking %-3s flagged %d of %d" % (mode, sum(v), len(v)))
print("cost: thinking on $%.3f, off $%.3f" % (cost["on"], cost["off"]))
