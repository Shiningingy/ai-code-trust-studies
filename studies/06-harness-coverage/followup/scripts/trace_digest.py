"""Study 06 follow-up, step 2: compact digest of one run's attempts, for method coding (L0-L3/G/K).

Usage: python -I trace_digest.py <run_id> [max_chars_per_item]
Prints, per attempt: the agent's text messages and its tool calls (Bash commands, Grep patterns, Read ranges),
plus for arm C the critic decisions. Read only; nothing is changed.
"""
import glob
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
step2 = os.path.join(os.path.dirname(here), "runs", "step2")


def items(path, cap):
    out = []
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        msg = d.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            t = c.get("type")
            if t == "text" and msg.get("role") == "assistant":
                s = c.get("text", "").strip().replace("\n", " | ")
                if s:
                    out.append("  SAY: " + s[:cap])
            elif t == "tool_use":
                i = c.get("input", {})
                name = c.get("name")
                if name == "Bash":
                    s = i.get("command", "")
                elif name == "Grep":
                    s = "pattern=%r %s" % (i.get("pattern"), {k: v for k, v in i.items() if k not in ("pattern",)})
                elif name == "Read":
                    s = "%s offset=%s limit=%s" % (os.path.basename(i.get("file_path", "")), i.get("offset"), i.get("limit"))
                else:
                    s = json.dumps(i)
                out.append("  %s: %s" % (name, s.replace("\n", " \\n ")[:cap]))
            elif t == "tool_result":
                r = c.get("content")
                if isinstance(r, list):
                    r = " ".join(x.get("text", "") for x in r if isinstance(x, dict))
                r = str(r)
                if "challenged" in r:
                    out.append("  [BLOCKED] " + r.replace("\n", " ")[:cap])
    return out


def main():
    run_id = sys.argv[1]
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    for p in sorted(glob.glob(os.path.join(step2, run_id + "-a*.jsonl"))):
        print("=== " + os.path.basename(p))
        for s in items(p, cap):
            print(s)
    crit = os.path.join(step2, run_id + "-critic.jsonl")
    if os.path.exists(crit):
        print("=== critic")
        for line in open(crit, encoding="utf-8"):
            d = json.loads(line)
            print("  %s %s: %s" % (d["decision"], d["tool"], d["reason"][:cap]))


if __name__ == "__main__":
    main()
