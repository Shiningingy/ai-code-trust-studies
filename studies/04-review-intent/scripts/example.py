"""Write a worked example for the report: one complete main-run PR drawn with seed "20261107-example"
(the two spot-check PRs left out), showing the issue, both summaries, the rubric and each arm's verdicts.

Usage: python example.py  -> results/example.md
"""
import json
import random
from pathlib import Path

from prepare import PRS
from summarise import issue_text

STUDY = Path(__file__).resolve().parent.parent
SPOT = {"Azure__azure-sdk-for-go-24864", "Azure__azure-sdk-for-go-25193"}


def main():
    done = []
    for lang in ("python", "go"):
        done += json.loads((STUDY / "runs" / f"main_state_{lang}.json").read_text(encoding="utf-8"))["done"]
    pid = random.Random("20261107-example").choice(sorted(set(done) - SPOT))
    d = PRS / pid
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    rubric = json.loads((d / "rubric.json").read_text(encoding="utf-8"))["items"]
    issue = issue_text(meta)
    L = [f"Drawn with seed `20261107-example` from the 56 complete PRs, leaving out the two spot-check PRs "
         f"(`scripts/example.py`): **{meta['repo']} #{meta['pr']}** ({meta['language']}).", "",
         "**Issue given to every arm** (shortened here):", "",
         "> " + (issue[:1200] + (" [...]" if len(issue) > 1200 else "")).replace("\n", "\n> "), ""]
    for side, name in (("B", "human review"), ("C", "agent review")):
        s = json.loads((d / f"summary_{side}.json").read_text(encoding="utf-8"))
        L += [f"**Summary of {name} (arm {side}, {s.get('words')} words):**", "",
              "> " + s["text"].replace("\n", "\n> "), ""]
    verdicts = {}
    for arm in "ABC":
        f = d / "arms" / arm / "inspect_opus.json"
        j = json.loads(f.read_text(encoding="utf-8"))
        verdicts[arm] = ({i["id"]: i["verdict"] for i in j["items"]}, j.get("score"))
    L += ["**Rubric and Opus verdicts per arm** (met / not_met / cant_tell):", "",
          "| Item | Behaviour | A | B | C |", "|---|---|---|---|---|"]
    for it in rubric:
        beh = it["behaviour"].replace("|", "/").replace("\n", " ")
        L.append(f"| {it['id']} | {beh} | " + " | ".join(verdicts[a][0].get(it["id"], "-") for a in "ABC") + " |")
    L += ["", "Rubric score: " + ", ".join(f"{a} {verdicts[a][1]:.2f}" for a in "ABC") + "."]
    (STUDY / "results" / "example.md").write_text("\n".join(L), encoding="utf-8")
    print(pid)


if __name__ == "__main__":
    main()
