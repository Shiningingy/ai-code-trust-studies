# Study 04: does human review intent help a coding agent?

**Status: plan frozen 2026-11-07; pilot (10 PRs) being built. No results yet.**

## The question

When a project reviews a pull request, the reviewers often say what the change should do and why. If a coding agent gets that intent up front, before it writes anything, does its fix land closer to what the project accepted? And is human review intent different from the same kind of summary made from AI-agent review?

The data comes from AgentReviewChat, published with "Human-AI Synergy in Agentic Code Review" (arXiv 2603.15911): inline review conversations on GitHub PRs, each started by a human or by an AI review agent.

## Design in one paragraph

Each merged PR is replayed from the commit just before it, three times, with the same agent (Claude Sonnet 5.5 in Claude Code) and the same tools: **A** gets the linked issue; **B** gets the issue plus a summary of the human review ("what and why, never how", no code); **C** gets the issue plus the same kind of summary of the AI-agent review. Each result is scored twice: by the PR's own tests (fail-to-pass), and by a rubric of behaviours written from the issue and the merged PR, never from the review, checked by two blind model inspectors.

The full plan, fixed before any agent run, is in [plan.md](plan.md). The selection scripts and their outputs are in [selection/](selection/); the pipeline is in [scripts/](scripts/).

## Running it

All model calls go through `claude -p` on a Claude subscription (no API key), isolated from the local Claude Code setup. Agents edit files on the host but run every command inside a per-PR Docker container with no network. The AgentReviewChat parquet files go in `data/raw/agentreviewchat/` (from Hugging Face `Suzhen/AgentReviewChat`) together with the agent list `selection/out/agents.csv`.

```
python -I selection/scripts/eligible.py selection/out
python -I selection/scripts/draw.py selection/out
cd scripts
python pilot.py setup     # trees, environments, fail-to-pass tests
python pilot.py texts     # review summaries and rubrics
python pilot.py runs      # agent runs
python pilot.py inspect   # scrub and inspectors
python pilot.py report
```
