"""Study 06 follow-up: read ledger, computed after the fact from run transcripts (Zili Luo's idea, 2026-11-25).

Every sentence of the run's context.md starts as UNREAD. A sentence becomes SEEN when its exact text appears in
any tool result returned to the model (Read output, Grep hits, printed script output). A masked or transformed
version (e.g. a template "<P> enjoys eating <FOOD>") does not count. PART = only a 30-character middle chunk of
the sentence appeared (grep -o windows, cut -c, truncated prints).
Also reports where the run's tokens went (from the "result" usage of each invocation).

Usage: python -I ledger.py <context.md> <out.jsonl> <label> <transcript.jsonl> [<transcript.jsonl> ...]
Several transcripts = several attempts of one run (the ledger is their union; attempt 1 is reported too).
Read only; appends one JSON line per run to out.jsonl.
"""
import json
import re
import sys

TRAPS = {  # decisive sentences behind the misses seen in Study 06 and the follow-up
    "p101_roster": "The community roster records amina foster under identifier p-101",
    "org007_city": "The same account also says that organization 007 is based in Lunenburg",
    "youth104_course": "The same account also says that youth 104 currently attends evening_pottery during the evening",
}


def sentences(path):
    text = open(path, encoding="utf-8").read()
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for s in re.split(r"(?<=[.!?])\s+", line):
            s = s.strip()
            if len(s) >= 12:
                out.append(s)
    return out


def tool_outputs_and_usage(path):
    outs, usage, cost, turns, calls, out_chars, mu = [], {}, 0.0, 0, 0, 0, {}
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "result":
            u = d.get("usage") or {}
            for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"):
                usage[k] = usage.get(k, 0) + (u.get(k) or 0)
            usage["thinking_tokens"] = usage.get("thinking_tokens", 0) + ((u.get("output_tokens_details") or {}).get("thinking_tokens") or 0)
            cost += float(d.get("total_cost_usd") or 0)
            turns += d.get("num_turns") or 0
            mu = d.get("modelUsage") or mu
        msg = d.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if c.get("type") == "tool_result":
                r = c.get("content")
                if isinstance(r, list):
                    r = "\n".join(x.get("text", "") for x in r if isinstance(x, dict))
                outs.append(str(r))
            elif c.get("type") == "tool_use":
                calls += 1
                out_chars += len(json.dumps(c.get("input", {})))
    return outs, usage, cost, turns, calls, out_chars, mu


def ledger(sents, blob):
    seen = part = 0
    for s in sents:
        if s in blob:
            seen += 1
        else:
            m = len(s) // 2
            if len(s) >= 40 and s[m - 15:m + 15] in blob:
                part += 1
    return seen, part


def main():
    ctx, out_path, label, paths = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    sents = sentences(ctx)
    ctx_text = open(ctx, encoding="utf-8").read()
    rec = {"run": label, "sentences": len(sents), "attempts": len(paths)}
    blobs, tot_usage, tot = [], {}, {"cost": 0.0, "turns": 0, "calls": 0, "script_chars": 0, "result_chars": 0}
    for i, p in enumerate(paths):
        outs, usage, cost, turns, calls, oc, mu = tool_outputs_and_usage(p)
        rec["model_usage"] = mu or rec.get("model_usage", {})  # cumulative: the last attempt holds the run total
        blob = "\n".join(outs)
        blobs.append(blob)
        for k, v in usage.items():
            tot_usage[k] = tot_usage.get(k, 0) + v
        tot["cost"] = cost or tot["cost"]  # cumulative across resumed attempts: the last one is the run's cost
        tot["turns"] += turns; tot["calls"] += calls
        tot["script_chars"] += oc; tot["result_chars"] += len(blob)
        if i == 0:
            s1, p1 = ledger(sents, blob)
            rec.update(a1_seen=s1, a1_part=p1, a1_cost=round(cost, 4))
    allb = "\n".join(blobs)
    s, pt = ledger(sents, allb)
    rec.update(seen=s, part=pt, unread=len(sents) - s - pt, seen_pct=round(100.0 * s / len(sents), 1))
    rec["traps"] = {k: ("seen" if v in allb else "unread") for k, v in TRAPS.items() if v in ctx_text}
    rec.update(tot, usage=tot_usage)
    rec["cost"] = round(rec["cost"], 4)
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps({k: rec[k] for k in ("run", "sentences", "seen_pct", "unread", "cost")}), rec["traps"])


if __name__ == "__main__":
    main()
