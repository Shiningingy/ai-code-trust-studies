# Study 04: does human review intent help a coding agent?

**Status: complete (November 2026).** Report: [report.pdf](report.pdf). Analysis plan, frozen before any agent run: [plan.md](plan.md).

## The question

When a project reviews a pull request, the reviewers often say what the change should do and why. If a coding agent gets that intent up front, before it writes anything, does its fix land closer to what the project accepted? And is human review intent different from the same kind of summary made from AI-agent review?

The data comes from AgentReviewChat, published with "Human-AI Synergy in Agentic Code Review" (arXiv 2603.15911): inline review conversations on GitHub PRs, each started by a human or by an AI review agent.

## Design

Each of 56 merged PRs (22 repositories, Python and Go) is replayed from the commit just before it, three times, with the same agent (Claude Sonnet 5.5 in Claude Code) and the same tools: **Baseline** gets the linked issue; **+HumanReview** gets the issue plus a 150-word summary of the human review ("what and why, never how", no code); **+AgentReview** gets the issue plus the same kind of summary of the AI-agent review. The primary outcome is a rubric of behaviours written from the issue and the merged PR, never from the review, rated by two blind model inspectors; the PR's own tests are a secondary outcome. In the data files and scripts the arms are labelled A, B and C.

## Key findings

- +HumanReview raised the mean rubric score from 0.47 (Baseline) to 0.63 (+0.16, 95% CI +0.07 to +0.25; Holm-adjusted p = 0.003). The result holds with a second inspector and with repository-clustered intervals.
- The gain is uneven: 27 PRs gained, 16 tied, 13 lost; the median change is zero.
- +HumanReview was not shown to beat +AgentReview (+0.07, CI −0.02 to +0.15); +AgentReview itself gained +0.09 over Baseline. Exploratory: the gap was +0.12 in Go and near zero in Python, and appeared only when human reviewers left more than four comments.
- The PRs' own tests rarely pass (5-8 of 56 per arm): in 87 of 147 failures the tests do not compile or import, because they call internal names that only the merged PR introduced.

Limits (one agent and harness, model-made rubrics, the merged code reflecting review requests) and planned follow-ups are in the report, Sections 6-7.

## Layout

- [plan.md](plan.md): the frozen plan and its dated amendments.
- [selection/](selection/): eligibility and draw scripts and their outputs.
- [scripts/](scripts/): the pipeline (`main.py`, `agent.py`, `stage1.py`, `judge.py`, `analyze.py`), the exploratory analyses, and the planned follow-ups (`followup_*.py`).
- [results/](results/): `results.txt` and `per_pr.csv` from `analyze.py`, plus the exploratory outputs.

## Running it

All model calls go through `claude -p` on a Claude subscription (no API key), isolated from the local Claude Code setup. Agents edit files on the host but run every command inside a per-PR Docker container with no network. The AgentReviewChat parquet files go in `data/raw/agentreviewchat/` (from Hugging Face `Suzhen/AgentReviewChat`) together with the agent list `selection/out/agents.csv`.

```
python -I selection/scripts/eligible.py selection/out
python -I selection/scripts/draw.py selection/out
cd scripts
python pilot.py setup              # pilot: trees, environments, fail-to-pass tests
python pilot.py texts              # pilot: review summaries and rubrics
python pilot.py runs               # pilot: agent runs
python pilot.py inspect            # pilot: scrub and inspectors
python main.py --lang python       # main run (one process per language)
python main.py --lang go
python analyze.py                  # results/results.txt, results/per_pr.csv
```
