# Study 04 plan, fixed before any agent run

**Status: frozen 2026-11-07, before the pilot's first agent run. The commit that adds this file is the freeze; its hash goes in the Launch log at the end. Changes after that are listed under Amendments with a date and a reason.**

Designed with Allen Luo on 2026-11-06/07. The data and the question come from "Human-AI Synergy in Agentic Code Review" (arXiv 2603.15911 v2), which published AgentReviewChat (Hugging Face `Suzhen/AgentReviewChat`, MIT): inline review conversations on GitHub PRs, each started by a human or by an AI review agent.

## Question

Does the *intent* in human code review (what the change should do and why, with code removed), given to a coding agent up front, move the agent's fix closer to what the project accepted? Compared with the issue alone, and with the same kind of summary made from AI-agent review.

A negative result is still a result.

## Arms

All three run on the same PR, from the same base commit, with the same model, tools, budget and prompt. They differ only in one block of text.

- **A**: the issue.
- **B**: the issue + a summary of the human review on that PR.
- **C**: the issue + a summary of the AI-agent review on that PR. C controls for "more text": if B beats A only because it is longer, C should beat A too.

The block in B and C has the same header, which does not say where it came from.

## Data and selection

**Pool.** Merged PRs in AgentReviewChat with at least one human-started and at least one agent-started review conversation: 15,409 PRs, 277 repos (`selection/scripts/pool.py`). "Human-started" and "agent-started" follow the paper's rule (first commenter of the conversation), which reproduces its Table I (`selection/scripts/overlap.py`). Agents are the 16 accounts in the paper's list (`selection/out/agents.csv`).

**Languages.** Python and Go, by the repo's primary language on GitHub (`selection/scripts/langs.py`).

**Eligible** (`selection/scripts/eligible.py`, one GitHub pass over every Python and Go pool PR):

1. links at least one closing issue;
2. changes at least one runnable test file (Python `test_*.py` or `*_test.py`; Go `*_test.go`);
3. has a commit pushed after the first human review (so the review could have changed the code);
4. changes at most 100 files, and has a merge commit.

This rule differs from the 2026-11-06 sampled checks in two ways, both fixed here before any agent run: rule 2 now needs a runnable test file (stage 1 needs tests it can run), and the regex escapes that a copy of the Go script lost are restored. Result of the full pass (2026-11-07): Python 238 eligible PRs in 16 repos, Go 125 in 16 (the sampled checks had estimated 264 and 136 under the looser rule).

**Excluded repos.** ray-project/ray, lablup/backend.ai, ansys/pymapdl (needs licensed ANSYS), apache/tvm: environments too heavy or impossible to build here.

**Draw.** Seed 20261107. Eligible PRs are shuffled with that seed within each language; walking the shuffled list, a PR is taken if its repo has fewer than 6 taken, until 35 per language (70). Pilot PRs are removed first. No replacements: a drawn PR that later fails a build check is excluded and counted.

**Build checks, in order, each exclusion counted:**

1. The merge commit's diff against its first parent has the same file set as the PR (otherwise the base is not "the repo just before this PR").
2. The project environment builds at the base commit.
3. At least one fail-to-pass test exists (see Stage 1).
4. Both summaries exist (each side has at least one comment left after the rules below).

The draw (`selection/scripts/draw.py`, run 2026-11-07 before this plan was frozen; only PR identities were looked at) took 70 PRs from 22 repositories (`selection/out/main_walk.csv`). Expected: 50-60 usable PRs.

## Inputs to the agent

**Issue.** Title and body of each closing issue, fetched from GitHub at build time. Comments on the issue are not included.

**Review material.** From AgentReviewChat only, so these are inline review conversations, not top-level PR comments.

- B: every comment in a human-started conversation written by a human other than the PR author.
- C: every comment in an agent-started conversation written by one of the 16 agent accounts.
- Each comment comes with its file path and diff hunk. GitHub suggestion blocks are removed from comment bodies before summarising.

**Summaries.** One summariser call per side per PR, same prompt for both sides: Opus 5.5, medium effort, no tools. At most 150 words, what the change should do and why, never how; no code. Lengths are logged and reported per arm.

**Leak check.** A summary leaks if it contains (a) a name added by the merged PR, i.e. an identifier in an added line of the merged diff that appears neither in the base versions of the touched files nor in the issue, or (b) six or more consecutive code tokens from an added line of the merged diff. A leaking summary is regenerated once with the flagged names listed as forbidden. If it still leaks, each flagged name is replaced with "[a new name]". The same procedure applies to both sides; hits are counted per arm.

## Agent run

- **Model:** Sonnet 5.5 (`claude-sonnet-5-5`), `--effort medium`, through `claude -p` on Allen's Claude subscription. Model, flags and Claude Code version are logged per run.
- **Tools:** Read, Edit, Write, Glob, Grep, and one MCP tool, `run`, that executes a shell command inside the PR's Docker container (`scripts/box_mcp.py`). The container has no network. No host shell, no web tools, no subagents.
- **Isolation:** no user, project or local Claude Code settings; the user-level CLAUDE.md is excluded and auto-memory is off; project instruction files inside the checked-out repository load as they would for any developer. The checkout sits in a neutral folder named after the repository, with a fresh one-commit git history, so later commits do not exist anywhere the agent can reach.
- **Prompt:** the same text in every arm, with the review block present only in B and C. It asks the agent to resolve the issue, to use `run` for commands, not to commit, and not to refer to the task or its instructions in code, comments or docs.
- **Budget:** one run per arm per PR, 45 minutes wall clock. A run that hits the time limit is scored on whatever diff it left.
- **Order:** the three arms of a PR run back to back, in an order shuffled per PR with seed 20261107.
- **Failures:** a run cut off by a usage limit, or one that fails for an infrastructure reason (CLI error, container crash), is discarded and rerun, up to two times. A model refusal is scored as it stands. A PR without a valid run in all three arms leaves every comparison (complete cases only), and is counted.

Every call logs its usage from `claude -p --output-format stream-json` (input, cache and output tokens, turns, duration) by role (agent, summary, rubric, inspector) and model.

## Scoring

**Scrub.** Before anything is scored, added comment lines that mention review, reviewer, guidance or feedback are removed from the agent's diff in every arm. Scrubs are counted per arm.

**Stage 1, tests.** Test files are the PR's changed files that match the language's test paths (Python: under `tests/`, `test/` or `testing/`, or `test_*.py`, `*_test.py`, `conftest.py`; Go: `*_test.go` or under `testdata/`). Tests run are the runnable test files among them (Python), or the packages that contain them (Go).

- **Fail-to-pass (F2P):** tests that fail (or error, or do not compile or collect) at base + the PR's test files, and pass at the merge commit. The merge commit is run twice; a test whose result differs between the two is dropped.
- **Pass-to-pass (P2P):** tests in the same files or packages that pass at both.
- **Agent result:** the PR's test files are copied over the agent's tree, then the same tests run. **Resolved** = every F2P test passes and every P2P test still passes.

**Stage 2, rubric.** Never built from review text: B was given those points, so a checklist from them would favour B by construction.

1. **Rubric writer:** Opus 5.5, medium effort, no tools, once per PR. Sees the issue, the PR title and description, and the merged diff. Never sees review text or any agent output. Writes 3-8 *behaviour* items that a different correct implementation could also meet: no required names, file locations or code structure unless the issue asks for them. Tests are not rubric items (stage 1 covers them).
2. **Inspectors:** two per implementation, each one call with no tools. **Opus 5.5 medium gives the main score; Sonnet 5.5 medium gives agreement and robustness.** Each sees the issue, the rubric, the scrubbed diff, the full touched non-test files after the change, and the stage-1 result, and returns met / not met / can't tell for each item, with file:line evidence. Inspectors are blind to the arm and to each other. No tie-breaker, no averaging.
3. **Rubric score** = share of items met. Can't tell counts as not met. An empty diff scores 0 without an inspector call.

## Analysis

The unit is a PR with all three arms scored.

**Primary outcome:** rubric score from the Opus inspector.

**Primary comparisons:** H1, B against A; H2, B against C. Each is a two-sided Wilcoxon signed-rank test on the per-PR differences (zero differences dropped, scipy's default), with Holm correction across the two at 0.05. Each is reported with the mean paired difference and a 95% bootstrap interval (10,000 resamples of PRs, seed 20261107).

For each comparison:

- **Signal:** adjusted p below 0.05, B higher.
- **Reversed:** adjusted p below 0.05, B lower. Reported as that.
- **No large effect:** adjusted p at or above 0.05. This is not "no effect". With 55 PRs, a standardised paired effect of about 0.4 is detected about 80% of the time at the Holm-adjusted level; smaller effects often are not. A null rules out a large effect and says little about a modest one.
- **Inconclusive:** fewer than 30 complete PRs.

**Reported, cannot change a verdict:**

1. Stage 1: resolved rate per arm; exact McNemar test for B against A and B against C.
2. C against A, with the same test as the primary comparisons.
3. Inspector agreement: Cohen's kappa at item level between Opus and Sonnet (met against not met, can't tell counted as not met), and the 3-class kappa. H1 and H2 rerun on Sonnet's scores; if a verdict changes, the report says the result depends on the inspector.
4. H1 and H2 bootstrap intervals with resampling clustered by repository.
5. Rubric score with can't-tell items left out of the denominator.
6. **Token efficiency (secondary, fixed here because papers often report it):** per run, total tokens (input + cache read + cache write + output), turns and wall-clock time; median per arm; Wilcoxon signed-rank for B against A and B against C. The question is whether up-front intent also makes the agent cheaper.
7. Each result split by language (Python, Go), descriptive only.
8. Summary lengths, leak-check hits, scrubs, timeouts and refusals per arm.

Anything else is exploratory and labelled so.

**Human checking.** Allen had no time to label a sample. After the experiment he spot-checks one or two rubrics and their inspections. The report says: "Rubrics and inspections were not validated against human labels; two were spot-checked by the author."

## Pilot

Ten PRs, not counted in the results and removed from the main draw: drawn with seed 20261107 from the eligible PRs of four repositories, 3 from home-assistant/core, 2 from getsentry/sentry-python, 3 from gruntwork-io/terragrunt, 2 from zitadel/zitadel. If a repository has too few that pass the build checks, the next one in the same shuffled list is taken.

The pilot runs all three arms with Sonnet 5.5, and arm A once more with Opus 5.5 medium as the agent.

**What the pilot may look at:** whether every PR builds and has F2P tests; plumbing (empty runs, crashes, timeouts, leak hits, scrubs); every summary, read by hand for how-level content; usage per role and model per PR, which Allen uses to set the main run's pace; and for the ceiling check, arm A alone, Sonnet against Opus. **Arm B and C scores are computed (to test the pipeline) but not printed or read.** No comparison between arms is made on pilot data.

**Ceiling rule.** If Sonnet in arm A is resolved on at least 8 of 10 PRs and its mean rubric score is at least 0.9, there is little room for B to beat A. Then, before the main draw, the selection is tightened (for example, a minimum number of changed non-test lines), written in Amendments with the numbers that triggered it.

**May change after the pilot (logged as amendments before the main run):** container recipes, the time budget, harness bugs, prompt wording that broke the harness, output formats, and the run rate. **May not change:** the question, the arms, the summary and leak rules, the outcomes, the primary comparisons and their tests, and the selection rule except under the ceiling rule.

## What this cannot show

- Why intent helps or not. It measures closeness to what the project accepted, not code quality in general.
- The rubric comes from the merged PR, so "closer to what was accepted" is the outcome by definition; a different good fix can still lose items.
- Rubrics and inspections are model-made and not validated against human labels.
- The agent may have seen these repositories, or even these PRs, in training. This affects all three arms alike but can lift every score.
- Review is summarised once by one model; a different summariser may carry different intent.
- Only inline review conversations are in the data; top-level PR comments and discussion elsewhere are not.
- Issues are fetched now and may have been edited after the PR.
- One run per arm per PR, so run-to-run noise is in the comparisons, not measured separately.
- Two languages, 22 repositories, and AI review from the agents in one dataset. Results may not carry to other projects or agents.

## Amendments

None yet.

## Launch log

- Plan frozen: commit `<hash>` (2026-11-07).
