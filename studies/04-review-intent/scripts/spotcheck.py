"""Draw two complete main-run PRs (seed 20261107) and one arm each, and write a sheet for a human to check
the rubric items and the Opus inspector's verdicts against the agent's code.

Usage: python spotcheck.py   -> spot-check/spot-check.md
"""
import json
import random
from pathlib import Path

from prepare import PRS
from summarise import issue_text

STUDY = Path(__file__).resolve().parent.parent
OUT = STUDY / "spot-check"


def main():
    done = []
    for lang in ("python", "go"):
        done += json.loads((STUDY / "runs" / f"main_state_{lang}.json").read_text(encoding="utf-8"))["done"]
    rng = random.Random("20261107-spotcheck")
    picks = [(pid, rng.choice("ABC")) for pid in rng.sample(sorted(done), 2)]
    L = ["# Spot-check: rubric items and inspector verdicts", "",
         "Two PRs and one arm each, drawn with seed `20261107-spotcheck` from the 56 complete PRs (`scripts/spotcheck.py`).",
         "", "For each PR:",
         "1. Read the issue and the rubric items. Mark each item: is it a fair behaviour the issue + merged PR call for "
         "(not a name or code structure the issue never gives)? Write **fair** / **unfair** + a few words.",
         "2. Open the agent's changed files (`after/` folder, path below) at the lines the inspector cites. Do you agree "
         "with its verdict? Write **agree** / **disagree** + a few words.",
         "3. One line at the end: anything that surprised you.", "",
         "The arm is shown so you can find the files; it does not matter for the check.", ""]
    for n, (pid, arm) in enumerate(picks, 1):
        d = PRS / pid
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        rubric = json.loads((d / "rubric.json").read_text(encoding="utf-8"))["items"]
        insp = {i["id"]: i for i in json.loads((d / "arms" / arm / "inspect_opus.json").read_text(encoding="utf-8"))["items"]}
        run = json.loads((d / "arms" / arm / "run.json").read_text(encoding="utf-8"))
        issue = issue_text(meta)
        L += [f"## PR {n}: {meta['repo']} #{meta['pr']} (arm {arm})", "",
              f"- PR: https://github.com/{meta['repo']}/pull/{meta['pr']}  (merged diff: `runs/prs/{pid}/merged.diff`)",
              f"- Agent's changed files: `runs/prs/{pid}/arms/{arm}/after/` ({', '.join(run.get('changed_files', []))})",
              f"- Agent's full diff: `runs/prs/{pid}/arms/{arm}/agent.diff`", "",
              "### Issue", "", "> " + (issue[:2500] + (" [...]" if len(issue) > 2500 else "")).replace("\n", "\n> "), ""]
        for it in rubric:
            v = insp.get(it["id"], {})
            L += [f"### {it['id']}", "", f"**Behaviour:** {it['behaviour']}", "",
                  f"**How to check (rubric):** {it.get('check', '')}", "",
                  f"**Inspector (Opus):** {v.get('verdict', '?')}. {v.get('evidence', '')}", "",
                  "- Item fair? ", "- Agree with verdict? ", ""]
        L += ["### Surprises", "", "- ", ""]
    OUT.mkdir(exist_ok=True)
    (OUT / "spot-check.md").write_text("\n".join(L), encoding="utf-8")
    print(picks)


if __name__ == "__main__":
    main()
