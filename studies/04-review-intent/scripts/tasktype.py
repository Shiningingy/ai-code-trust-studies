"""Exploratory: label each complete main-run PR's task type from its issue and PR title (one Sonnet call per PR).
Writes runs/prs/<id>/tasktype.json and results/pr_tasktype.csv.  Usage: python tasktype.py
"""
import json
from pathlib import Path

import pandas as pd

import llm
from prepare import PRS
from summarise import issue_text

STUDY = Path(__file__).resolve().parent.parent
TYPES = ["bug fix", "new feature", "enhancement of existing behaviour", "refactor or maintenance"]
SCHEMA = {"type": "object", "required": ["type", "reason"], "properties": {
    "type": {"type": "string", "enum": TYPES}, "reason": {"type": "string"}}}
PROMPT = """Classify the task described by this issue and pull-request title from the {repo} repository.

PR title: {title}

<issue>
{issue}
</issue>

Types: "bug fix" (existing behaviour is wrong), "new feature" (a capability that did not exist), "enhancement of existing behaviour" (existing behaviour works but is extended or improved, e.g. better errors, new option), "refactor or maintenance" (no change in behaviour intended). Pick one, with a one-sentence reason."""


def main():
    done = []
    for lang in ("python", "go"):
        done += json.loads((STUDY / "runs" / f"main_state_{lang}.json").read_text(encoding="utf-8"))["done"]
    rows = []
    for pid in sorted(done):
        out = PRS / pid / "tasktype.json"
        if not out.exists():
            meta = json.loads((PRS / pid / "meta.json").read_text(encoding="utf-8"))
            r = llm.call(PROMPT.format(repo=meta["repo"], title=meta["title"], issue=issue_text(meta)[:6000]),
                         role="tasktype", pr=pid, model=llm.SONNET, effort="low", schema=SCHEMA, timeout=300)
            if r["status"] != "ok" or not r["structured"]:
                print("ERROR", pid, r["status"], flush=True)
                continue
            out.write_text(json.dumps(r["structured"], indent=1), encoding="utf-8")
        rows.append(dict(pr=pid, **json.loads(out.read_text(encoding="utf-8"))))
    pd.DataFrame(rows).to_csv(STUDY / "results" / "pr_tasktype.csv", index=False)
    print(pd.DataFrame(rows).type.value_counts().to_string())


if __name__ == "__main__":
    main()
