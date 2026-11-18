"""Leak check: words that would tell the agent it is in a study of this paper.

`claude -p` puts the working directory's path into the model's context (Study 04 finding), so run folders
are E:\\w\\rNN and the prompts avoid these words. After each run the prompt, the init event (cwd, memory
paths) and the whole transcript are scanned; hits are listed with context for hand review (a hit in the
agent's own text, e.g. "team", is not by itself a leak).

Usage: python check_leaks.py <run dir>
"""
import json
import re
import sys
from pathlib import Path

WORDS = ["study", "multihunk", "multi-hunk", "beyond accuracy", "polyhunk", "hunk4j", "hunkswe", "hunk-swe",
         "team", "paper", "nashid", "mesbah", "gallaba", "hassan", "agentic-se", "tosem", "2511.11012",
         "study05", "s05"]
PAT = re.compile("|".join(re.escape(w) for w in WORDS), re.I)


def scan_text(text):
    return sorted({m.group(0).lower() for m in PAT.finditer(text)})


def scan_run(run_dir):
    run_dir = Path(run_dir)
    hits = []
    prompt = (run_dir / "prompt.txt").read_text(encoding="utf-8")
    for w in scan_text(prompt):
        hits.append({"where": "prompt", "word": w})
    tr = run_dir / "transcript.jsonl"
    if tr.exists():
        for i, line in enumerate(tr.read_text(encoding="utf-8").splitlines()):
            for m in PAT.finditer(line):
                s = max(0, m.start() - 80)
                hits.append({"where": f"transcript line {i + 1}", "word": m.group(0).lower(),
                             "context": line[s:m.end() + 80]})
            if '"subtype":"init"' in line.replace(" ", ""):
                ev = json.loads(line)
                for k in ("cwd", "memory_paths"):
                    for w in scan_text(json.dumps(ev.get(k))):
                        hits.append({"where": f"init {k}", "word": w})
    (run_dir / "leaks.json").write_text(json.dumps(hits, indent=1), encoding="utf-8")
    return {"hits": len(hits), "words": sorted({h["word"] for h in hits}),
            "in_prompt_or_init": [h for h in hits if not h["where"].startswith("transcript")]}


if __name__ == "__main__":
    print(json.dumps(scan_run(sys.argv[1]), indent=1))
