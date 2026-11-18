"""Per-run table for results.md, from E:\\study05\\runs\\<bug>\\<arm>\\<run>\\run.json (+ grade, leaks).

Usage: python summarize.py            (prints a Markdown table and writes E:\\study05\\runs\\summary.json)
"""
import json
from pathlib import Path

import llm


def pct(r, k):
    v = (r or {}).get(k)
    return "-" if v is None else f"{v * 100:.0f}%"


def rows():
    out = []
    for p in sorted(list(llm.RUNS.glob("*/*/*/run.json")) + list(llm.RUNS.glob("sonnet-4-5/*/*/*/run.json"))):
        r = json.loads(p.read_text(encoding="utf-8"))
        g = r.get("grade") or {}
        # tokens = the CLI's modelUsage (whole run, sub-agents included, summed over models); the result event's
        # `usage` covers only the final turn, so it is not used for the table
        mu = r.get("model_usage") or {}
        u = {"input_tokens": sum(m.get("inputTokens", 0) for m in mu.values()),
             "cache_creation_input_tokens": sum(m.get("cacheCreationInputTokens", 0) for m in mu.values()),
             "cache_read_input_tokens": sum(m.get("cacheReadInputTokens", 0) for m in mu.values()),
             "output_tokens": sum(m.get("outputTokens", 0) for m in mu.values())}
        cost = round(sum(m.get("costUSD", 0) for m in mu.values()), 3)
        lk = r.get("leaks") or {}
        out.append({
            "model": r.get("model"), "bug": r["bug"], "arm": r["arm"], "run": p.parent.name, "slot": r.get("slot"), "status": r["status"],
            "started": r.get("started"), "localization": g.get("localization"), "compiled": g.get("compiled"),
            "repair": g.get("repair"), "repair_strict": g.get("repair_strict"), "failed_after": g.get("failed_after"),
            "failed_after_strict": g.get("failed_after_strict"), "rr": g.get("regression_reduction"),
            "new_failures": g.get("new_failures"), "files": g.get("files"),
            "input": u.get("input_tokens"), "cache_create": u.get("cache_creation_input_tokens"),
            "cache_read": u.get("cache_read_input_tokens"), "output": u.get("output_tokens"),
            "total_tokens": sum(u.values()), "cost_usd_list": cost, "minutes": round(r["seconds"] / 60, 1) if r.get("seconds") else None,
            "turns": r.get("num_turns"), "five_before": pct(r.get("rate_before"), "five_hour"),
            "five_after": pct(r.get("rate_after"), "five_hour"), "week_before": pct(r.get("rate_before"), "seven_day"),
            "week_after": pct(r.get("rate_after"), "seven_day"), "subagents": r.get("subagents"),
            "uml_calls": r.get("uml_calls"), "leak_hits": lk.get("hits"), "leak_words": lk.get("words"),
            "leak_prompt_or_init": len(lk.get("in_prompt_or_init") or []),
            "models": sorted((r.get("model_usage") or {}).keys())})
    order = {"smoke": 0}
    out.sort(key=lambda x: (x["model"] or "", x["bug"] != "astropy__astropy-7606", order.get(x["run"], 1), x["slot"] or 0))
    return out


def table(rs):
    h = ("| Model | Bug | Arm | Run | Status | Loc | Comp | Repair | Repair strict | Failed after | RR | Tokens in / cache-create / "
         "cache-read / out | Min | 5h before→after | Week before→after | Sub-agents | class_graph calls |")
    lines = [h, "|" + "|".join(["---"] * (h.count("|") - 1)) + "|"]
    for x in rs:
        b = "Astropy-7606" if x["bug"].startswith("astropy") else "Closure_157"
        fa = x["failed_after"] if x["failed_after_strict"] is None else f'{x["failed_after"]} (strict {x["failed_after_strict"]})'
        tok = "/".join(f"{v:,}" if isinstance(v, int) else "-" for v in (x["input"], x["cache_create"], x["cache_read"],
                                                                          x["output"]))
        lines.append(f'| {"5.5" if "5-5" in (x["model"] or "") else "4.5"} | {b} | {x["arm"]} | {x["run"]} | {x["status"]} | {x["localization"]} | {int(bool(x["compiled"]))} '
                     f'| {x["repair"]} | {"-" if x["repair_strict"] is None else x["repair_strict"]} | {fa} | {x["rr"]} '
                     f'| {tok} | {x["minutes"]} | {x["five_before"]}→{x["five_after"]} | {x["week_before"]}→{x["week_after"]} '
                     f'| {x["subagents"]} | {x["uml_calls"] if x["arm"] == "U" else "-"} |')
    return "\n".join(lines)


if __name__ == "__main__":
    rs = rows()
    (llm.RUNS / "summary.json").write_text(json.dumps(rs, indent=1), encoding="utf-8")
    print(table(rs))
    for x in rs:
        print(x["bug"], x["arm"], x["run"], "files", x["files"], "new_failures", x["new_failures"], "leaks", x["leak_hits"],
              x["leak_words"], "prompt/init", x["leak_prompt_or_init"], "models", x["models"])
