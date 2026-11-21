"""Study 06 scorer (own code; the benchmark's score.py is not run).
Exact = the predicted person-ID set equals the answer-key set (the benchmark's primary metric).
Also prints a per-condition summary and, for HV runs, every coverage-check result the agent saw.
Usage: python -I score.py [runs_dir] [data_dir]   (defaults: ../runs and E:/lhb-data)
"""
import json, re, sys, pathlib, collections
sys.stdout.reconfigure(encoding="utf-8")
here = pathlib.Path(__file__).resolve().parent
runs = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here.parent / "runs"
data = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("E:/lhb-data")
keys = {s: set(json.load(open(data / "answers" / f"sample-{s}.json"))["matches"]) for s in ("00000", "00001")}
CHECK = re.compile(r"total statements:\s*(\d+)\s+placed:\s*(\d+)\s+irrelevant:\s*(\d+)\s+unaccounted:\s*(\d+)", re.I)

def read_run(p):
    if p.suffix == ".json":
        r = json.loads(p.read_text(encoding="utf-8"))
        return r.get("result", ""), r, 0, []
    result, tools, checks = None, 0, []
    for line in p.read_text(encoding="utf-8").splitlines():
        try: ev = json.loads(line)
        except Exception: continue
        if ev.get("type") == "assistant":
            tools += sum(1 for c in ev["message"].get("content", []) if c.get("type") == "tool_use")
        if ev.get("type") == "user" and isinstance(ev["message"].get("content"), list):
            for c in ev["message"]["content"]:
                if c.get("type") == "tool_result":
                    t = c.get("content")
                    t = t if isinstance(t, str) else " ".join(x.get("text", "") for x in t if isinstance(x, dict))
                    checks += [tuple(map(int, m)) + (bool(c.get("is_error")),) for m in CHECK.findall(t)]
        if ev.get("type") == "result": result = ev
    return (result or {}).get("result", ""), (result or {}), tools, checks

rows, gate = [], {}
for p in sorted(list(runs.glob("*.json")) + list(runs.glob("*.jsonl"))):
    m = re.match(r"([A-Z]+)(\d{5})-(\d+)$", p.stem)
    if not m: continue
    cond, s, rep = m.groups()
    text, r, tools, checks = read_run(p)
    found = re.findall(r"\{[^{}]*\"matches\"[^{}]*\}", text or "")
    pred = set(json.loads(found[-1])["matches"]) if found else set()
    k = keys[s]
    rows.append(dict(run=p.stem, cond=cond, exact=pred == k, hits=len(pred & k), extra=sorted(pred - k),
                     missed=sorted(k - pred), tools=tools, turns=r.get("num_turns"), cost=r.get("total_cost_usd") or 0))
    if cond == "HV": gate[p.stem] = checks

print("run | exact | found/5 | wrong inclusions | missed | tool calls | turns | cost $")
for x in rows:
    print(f"{x['run']} | {x['exact']} | {x['hits']} | {x['extra'] or '-'} | {x['missed'] or '-'} | {x['tools']} | {x['turns']} | {x['cost']:.3f}")
print("\ncondition | runs | exact | found | wrong inclusions | mean cost $")
by = collections.defaultdict(list)
for x in rows: by[x["cond"]].append(x)
for c in ("D", "H", "HC", "HV"):
    xs = by.get(c, [])
    if xs:
        print(f"{c} | {len(xs)} | {sum(x['exact'] for x in xs)}/{len(xs)} | {sum(x['hits'] for x in xs)}/{5*len(xs)} | "
              f"{sum(len(x['extra']) for x in xs)} | {sum(x['cost'] for x in xs)/len(xs):.3f}")
print("\nHV coverage checks, in the order the agent ran them (total, placed, irrelevant, unaccounted, failed):")
for run, cs in gate.items():
    print(run, "|", "  ->  ".join(f"{t}/{p}/{i}/{u}{' FAIL' if (u or e) else ''}" for t, p, i, u, e in cs))
