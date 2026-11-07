# Does human review intent help a coding agent? A three-arm replay on merged pull requests

> **Status: draft with final results (2026-11-07).** All 56 runnable PRs are complete. One item marked [check] waits on the author's spot-check of two PRs.

Zili (Allen) Luo · Independent study, November 2026 · Not peer reviewed · DRAFT: results sections are placeholders

## Abstract

Coding agents are usually judged by tests that confirm what was built, not what was asked. Human code review often says what a change should do and why. This study asks whether that intent, given to a coding agent before it writes anything, moves its fix closer to what the project accepted. Each merged pull request (PR) from the AgentReviewChat dataset is replayed from the commit just before it, three times, with Claude Sonnet 5.5 in Claude Code: with the linked issue only (A), with the issue plus a summary of the human review (B), and with the issue plus the same kind of summary of AI-agent review (C). Results are scored by the PR's own fail-to-pass tests and by a behaviour rubric written from the issue and the merged PR, never from the review, and checked by two blind model inspectors. The analysis plan was frozen before any agent run. On 56 PRs from 22 repositories (29 Python, 27 Go), the mean rubric score was 0.47 in arm A, 0.63 in arm B and 0.56 in arm C. Arm B scored higher than arm A by +0.16 (95% bootstrap CI +0.07 to +0.25; Holm-adjusted p = 0.003), the pre-registered "Signal" verdict, and the result holds with the second inspector and with repository-clustered intervals. Arm B against arm C differed by +0.07 (CI -0.02 to +0.15; adjusted p = 0.15): no large effect. Few runs passed the PR's own tests (5, 8 and 8 of 56), mostly because the tests call internal names the issue never gives. Arm B's runs used a median of 51% more tokens than arm A's.

## 1. Introduction

When a project reviews a pull request, reviewers often state what the change is meant to do and why. That information is rarely in the issue, and an agent that works from the issue alone has to guess it. The usual check on an agent's patch does not help here: tests confirm that the code does what its author built, which is not the same as what was asked. Human review is one of the few places where the "what and why" is written down by someone who knows the project.

This study asks one question. Does the intent in human code review (what the change should do and why, with code removed), given to a coding agent up front, move the agent's fix closer to what the project accepted? Two comparisons make the question precise. B against A asks whether review intent beats the issue alone. B against C asks whether human review intent differs from the same kind of summary made from AI-agent review. Arm C also controls for length: if B beats A only because it carries more text, C should beat A too.

The contribution is a three-arm replay design on real merged PRs, a scoring scheme that never builds its checklist from the review text, and a result, whichever way it comes out. A negative result is a result. The study is small and pre-registered: the plan was committed to a public repository before the pilot's first agent run, later changes are listed as dated amendments, and every model call ran on a personal Claude subscription rather than a funded API budget. It supports claims about these 22 repositories, these two languages and this agent, and no wider claims.

## 2. Related work

The nearest published work found is c-CRAB, a code review agent benchmark (Zhang et al., arXiv 2603.23448). Review tools comment on a PR's patch, and Claude Code (Sonnet 4.6) then revises the patch, starting from the PR head. Hidden tests written from the human review score the revision. Revisions guided by the tools pass 20.1-32.1% of the tests (Table 5), and the human review's own fix passes all of them, which follows from how the tests were validated. This study differs in three ways: it starts from the base commit, not from an existing patch; review is given as intent before any code is written, not as input to a revision; and it has an issue-only arm.

The closest work on what an agent is told up front is "What Makes a Good Bug Report for an AI Agent?" (Khatib et al., arXiv 2607.07593). It removes parts of the problem statement (suggested fixes, localization, expected behaviour) on SWE-bench Pro and measures the effect. That content comes from the issue, not from review, and it has no human-versus-AI comparison. "Intention is All You Need" (Guo et al., arXiv 2502.08172) extracts a reviewer's intent from review comments, but uses it to refine existing code rather than to write the change from the base commit.

SWE-Review (Wang et al., arXiv 2607.06065) has a reviewer agent judge an AI-generated patch on SWE-bench Verified and send feedback for one revision. Its Table 1(b) compares no review, a decision only, a teacher review and an oracle review (3%, 8%, 21% and 32% resolved after revision, on 100 instances). It covers AI review only, and only after a patch exists. The closest precedent for "human discussion helps" is a pair of baseline rows in MASAI's Table 1 (Arora et al., arXiv 2406.11638): OpenDevin resolves 25.00% of SWE-bench Lite with the benchmark's `hints_text` and 16.00% without. These rows appear to be different OpenDevin versions, so the gap is not a clean ablation. Those hints are issue-thread comments, not review.

Leakage is a standing risk when human text is given to an agent. SWE-Bench+ (Aleithan et al., arXiv 2410.06992) reports that in 32.67% of SWE-Agent + GPT-4's successful patches the solution was given directly in the issue report or its comments. This study answers with a leak check on every summary (Section 4.2) and a rubric that avoids required names and structure.

Work on missing intent in coding tasks is related background: Ambig-SWE (Vijayvargiya et al., arXiv 2502.13069; accepted at ICLR 2026), "Ask or Assume?" (Edwards and Schuster, arXiv 2603.26233) and CLARITI (Vijayvargiya et al., arXiv 2604.14624). They study an agent asking for what an underspecified task leaves out. Here the missing information is supplied up front, from review. For scoring, Shi et al. (arXiv 2511.10865) have an LLM draft a rubric per bug, which developers then refine. They report that at k=20, 96% of patches passed reproduction tests while 80% were judged valid by the rubric-based LLM judge, and that of 504 patches that passed reproduction tests, the judge rated 219 (43.5%) invalid. The rubrics here are model-drafted and not human-refined, which Section 7 states as a limit.

The data come from "Human-AI Synergy in Agentic Code Review" (Zhong et al., arXiv 2603.15911 v2), whose dataset is on Hugging Face as AgentReviewChat (`Suzhen/AgentReviewChat`, MIT): 278,790 inline review conversations on GitHub PRs, each labelled by whether a human or an AI review agent made the first comment. That paper is observational. A search on 2026-11-07 found no published study with this three-arm design (issue; issue plus human-review intent; issue plus agent-review intent) on merged PRs replayed from the base commit. The search was short and read abstracts, so "not found" is the claim.

## 3. Research questions and hypotheses

The primary outcome is the rubric score from the Opus inspector (Section 4.5).

- **H1.** Rubric scores in arm B differ from arm A.
- **H2.** Rubric scores in arm B differ from arm C.

Both are two-sided. Secondary questions are reported but cannot change a verdict: the stage-1 resolved rate, C against A, inspector agreement, and token efficiency.

## 4. Method

### 4.1 Data and selection

The pool is the merged PRs in AgentReviewChat with at least one human-started and at least one agent-started review conversation: 15,409 PRs in 277 repositories. "Human-started" and "agent-started" follow the dataset paper's rule (the first commenter of the conversation), which reproduces that paper's Table I. Agents are the 16 accounts in the paper's list.

Languages are Python and Go, by each repository's primary language on GitHub. A PR is eligible if it (1) links at least one closing issue; (2) changes at least one runnable test file (Python `test_*.py` or `*_test.py`; Go `*_test.go`); (3) has a commit pushed after the first human review, so the review could have changed the code; and (4) changes at most 100 files and has a merge commit. One GitHub pass over every Python and Go pool PR found 238 eligible PRs in 16 repositories for Python and 125 in 16 for Go. Four repositories were excluded because their environments are too heavy or impossible to build here: ray-project/ray, lablup/backend.ai, ansys/pymapdl (it needs licensed ANSYS) and apache/tvm.

The draw used seed 20261107. Eligible PRs are shuffled within each language; walking the shuffled list, a PR is taken if its repository has fewer than six taken, until 35 per language. Pilot PRs are removed first. The draw took 70 PRs from 22 repositories. There are no replacements: a drawn PR that later fails a build check is excluded and counted. The build checks, in order, are: the merge commit's diff against its first parent has the same file set as the PR; the project environment builds at the base commit; at least one fail-to-pass test exists; and both summaries exist. The plan expected 50-60 usable PRs.

### 4.2 Arms and summaries

All three arms run on the same PR, from the same base commit, with the same model, tools, budget and prompt. They differ in one block of text. A gets the issue (title and body of each closing issue, fetched at build time; issue comments are not included). B adds a summary of the human review. C adds a summary of the AI-agent review. The block has the same header in B and C and does not say where it came from.

The review material comes from AgentReviewChat only, so it is inline review conversations. For B it is every comment in a human-started conversation written by a human other than the PR author. For C it is every comment in an agent-started conversation written by one of the 16 agent accounts. Each comment comes with its file path and diff hunk, and GitHub suggestion blocks are removed before summarising.

One summariser call per side per PR uses the same prompt for both sides: Opus 5.5, medium effort, no tools, at most 150 words, saying what the change should do and why, never how, with no code. A leak check then runs. A summary leaks if it contains (a) a name added by the merged PR, meaning an identifier in an added line of the merged diff that appears neither in the base versions of the touched files nor in the issue, or (b) six or more consecutive code tokens from an added line of the merged diff. A leaking summary is regenerated once with the flagged names listed as forbidden. If it still leaks, each flagged name is replaced with "[a new name]". The procedure is the same on both sides, and hits are counted per arm.

**Amendment 1** (2026-11-07, before any agent run). Reading the first pilot PR's two summaries by hand (home-assistant/core #148639) found one that quoted a code fragment from the draft, which the leak check does not catch, and one at 159 words, over the cap. Both broke rules already in the plan, so the plan enforced them rather than changed them. The prompt now asks for requirements for the finished change, not edits to a draft the developer never saw, and forbids backticks. An automatic check for code spans and length folds into the one regeneration. If the second answer still breaks a rule, backticks are removed and the text is cut at the last whole bullet or sentence within 150 words. Both sides get the same procedure, and first-answer rule breaks, regenerations and cuts are counted per arm.

### 4.3 Agent setup

The agent is Sonnet 5.5 (`claude-sonnet-5-5`) at medium effort, run through `claude -p` on a Claude subscription. Model, flags and Claude Code version are logged per run. Tools are Read, Edit, Write, Glob, Grep and one MCP tool, `run`, which executes a shell command inside the PR's Docker container. The container has no network. There is no host shell, no web tool and no subagent.

Claude Code runs without user, project or local settings; the user-level CLAUDE.md is excluded and auto-memory is off. Project instruction files inside the checked-out repository load as they would for any developer. The checkout sits in a neutral folder named after the repository, with a fresh one-commit git history, so later commits do not exist anywhere the agent can reach. The prompt is the same in every arm, with the review block present only in B and C. It asks the agent to resolve the issue, to use `run` for commands, not to commit, and not to refer to the task or its instructions in code, comments or docs.

The budget is one run per arm per PR with 45 minutes of wall clock. A run that hits the time limit is scored on the diff it left. The three arms of a PR run back to back in an order shuffled per PR with seed 20261107. A run cut off by a usage limit, or one that fails for an infrastructure reason, is discarded and rerun, up to two times. A model refusal is scored as it stands. A PR without a valid run in all three arms leaves every comparison and is counted. Every call logs its usage (input, cache and output tokens, turns, duration) by role and model.

### 4.4 Stage 1: tests

Before scoring, added comment lines that mention review, reviewer, guidance or feedback are removed from the agent's diff in every arm. Scrubs are counted per arm.

Test files are the PR's changed files that match the language's test paths. For Python these sit under `tests/`, `test/` or `testing/`, or match `test_*.py`, `*_test.py` or `conftest.py`; for Go they match `*_test.go` or sit under `testdata/`. The tests run are the runnable changed test files (Python) or, by Amendment 2, the test functions defined in the changed `_test.go` files, inside their packages (Go). Fail-to-pass (F2P) tests fail, error, or do not compile or collect at the base commit plus the PR's test files, and pass at the merge commit. The merge commit runs twice, and a test whose result differs between runs is dropped. Pass-to-pass (P2P) tests are run tests that pass at both. To score an agent, the PR's test files are copied over its tree and the same tests run. A run is resolved if every F2P test passes and every P2P test still passes.

### 4.5 Stage 2: rubric and inspectors

The rubric is never built from review text. B was given those points, so a checklist drawn from them would favour B by construction. A rubric writer (Opus 5.5, medium effort, no tools, once per PR) sees the issue, the PR title and description, and the merged diff, and never sees review text or any agent output. It writes 3-8 behaviour items that a different correct implementation could also meet, with no required names, file locations or code structure unless the issue asks for them. Tests are not rubric items.

Two inspectors judge each implementation, each in one call with no tools. Opus 5.5 at medium effort gives the main score; Sonnet 5.5 at medium effort gives agreement and robustness. Each sees the issue, the rubric, the scrubbed diff, the full touched non-test files after the change and the stage-1 result, and returns met, not met or can't tell for each item, with file and line evidence. Inspectors are blind to the arm and to each other. There is no tie-breaker and no averaging. The rubric score is the share of items met; can't tell counts as not met, and an empty diff scores 0 without an inspector call.

### 4.6 Analysis

The unit is a PR with all three arms scored. The primary outcome is the rubric score from the Opus inspector. H1 (B against A) and H2 (B against C) are each a two-sided Wilcoxon signed-rank test on the per-PR differences, with zero differences dropped (scipy's default), and Holm correction across the two at 0.05. Each comparison is reported with the mean paired difference and a 95% bootstrap interval (10,000 resamples of PRs, seed 20261107).

The verdict rules are fixed. Signal means adjusted p below 0.05 with B higher. Reversed means adjusted p below 0.05 with B lower, and it is reported as that. No large effect means adjusted p at or above 0.05; this is not "no effect". Inconclusive means fewer than 30 complete PRs. On power: with 55 PRs, a standardised paired effect of about 0.4 is detected about 80% of the time at the Holm-adjusted level, and smaller effects often are not. A null rules out a large effect and says little about a modest one.

The following are reported and cannot change a verdict.

1. Stage 1: resolved rate per arm, with an exact McNemar test for B against A and B against C.
2. C against A, with the same test as the primary comparisons.
3. Inspector agreement: Cohen's kappa at item level between Opus and Sonnet (met against not met), and the 3-class kappa. H1 and H2 are rerun on Sonnet's scores; if a verdict changes, the report says the result depends on the inspector.
4. H1 and H2 bootstrap intervals with resampling clustered by repository.
5. Rubric score with can't-tell items left out of the denominator.
6. Token efficiency: per run, total tokens (input, cache read, cache write and output), turns and wall-clock time; the median per arm; a Wilcoxon signed-rank test for B against A and B against C. The question is whether up-front intent also makes the agent cheaper. It was fixed in the plan before any run because papers often report it.
7. Each result split by language, descriptive only.
8. Summary lengths, leak-check hits, scrubs, timeouts and refusals per arm.

Anything else is exploratory and labelled so. Rubrics and inspections were not validated against human labels. [check: the author's spot-check of two PRs is pending; update this sentence and Section 7 when it is done.]

### 4.7 Pilot

A pilot of ten PRs, not counted in the results and removed from the main draw, was drawn with seed 20261107 from the eligible PRs of four repositories: three from home-assistant/core, two from getsentry/sentry-python, three from gruntwork-io/terragrunt and two from zitadel/zitadel. It ran all three arms with Sonnet 5.5, and arm A once more with Opus 5.5 at medium effort as the agent. The pilot looked at whether each PR builds and has F2P tests, at plumbing (empty runs, crashes, timeouts, leak hits, scrubs), at every summary read by hand for how-level content, and at usage per role and model, which set the main run's pace. For the ceiling check it looked at arm A alone, Sonnet against Opus. Scores for arms B and C were computed to test the pipeline but not printed or read, and no comparison between arms was made on pilot data. The ceiling rule said that if Sonnet in arm A resolved at least 8 of 10 PRs with a mean rubric score of at least 0.9, the selection would be tightened before the main draw. Nine of the ten pilot PRs got runs; zitadel #11009 got none because of an orchestration error (two processes ran it into one folder). The pilot found one harness fault: the prompt said the checkout "is mounted at /work", and in 21 of 36 pilot runs the agent passed /work paths to its file tools at least once. Those calls were denied, and several runs then stopped without changing anything. Amendment 3 changed the wording before any main-run agent run, the same in every arm, and a check run after the change had no denials. The ceiling rule did not fire: in arm A, Sonnet resolved 1 of 9 piloted PRs with a mean rubric score of 0.48, and Opus resolved 3 of 9 with 0.76. Both figures are depressed by the /work fault, so Section 5 also reports arm A's resolved rate against the rule. Usage per run set the main run's pace: Sonnet agent runs used about 2.2 million tokens over 27 calls, and the main run paused new calls when the five-hour usage window passed 80%.

## 5. Results

### 5.1 Selection and exclusions

Of the 70 drawn PRs, 14 were excluded at the build checks. Four failed check 1: the merge commit's file set differs from the PR's (all four from zeta-chain/node). One failed check 2 (environment): its tests need a live Cosmos DB database. Seven failed check 3 (no fail-to-pass test); for six of them the PR's tests ran and passed both before and after the change, and one has only a browser screenshot test. Two failed check 4: no human-started review conversation to summarise. Appendix A lists each exclusion with its cause. Two PRs were repaired after a setup fault, as Appendix A describes: azure-cli #32298, whose tests ran past the 30-minute limit until the same tests were run in eight parallel workers, joined the run; azure-sdk-for-python #40615 moved from check 2 to check 3 once its recorded tests replayed offline. That left 56 complete PRs (29 Python, 27 Go) from 22 repositories (10 Python, 12 Go). No PR has an incomplete set of arms. No run hit a usage limit, timed out or was refused.

### 5.2 Primary: rubric score

| | A | B | C |
|---|---|---|---|
| Mean rubric score (Opus inspector), n = 56 | 0.465 | 0.626 | 0.560 |

| Comparison | Mean paired difference | 95% bootstrap CI | Wilcoxon p (non-zero pairs) | Holm-adjusted p | Verdict |
|---|---|---|---|---|---|
| H1: B vs A | +0.160 | +0.070 to +0.252 | 0.0015 (40) | 0.0030 | Signal (B higher) |
| H2: B vs C | +0.066 | -0.015 to +0.147 | 0.154 (42) | 0.154 | No large effect |

B scored higher than A on 27 PRs, lower on 13 and the same on 16. The median paired difference is zero: the mean gain comes from PRs where B helped a lot, not from a small gain on every PR. B scored higher than C on 27 PRs, lower on 15 and the same on 14. Arm A was far from the ceiling (mean 0.465, 5 of 56 resolved), so the ceiling rule from the pilot did not apply.

### 5.3 Stage 1: tests

| | A | B | C |
|---|---|---|---|
| Resolved (all F2P pass, no P2P breaks) | 5/56 | 8/56 | 8/56 |

Exact McNemar: B against A, 4 B-only and 1 A-only (p = 0.375); B against C, 3 B-only and 3 C-only (p = 1.0).

Most stage-1 failures are not about behaviour. In 87 of the 147 unresolved runs (31 of the 56 PRs), the PR's tests did not compile or import against the agent's code. They call names that only the merged PR introduced: unexported Go identifiers (`undefined: docURL`), private attributes (`_sync_credential`) and new constants (`CONF_SITE`). An agent that does not pick the same internal names fails every F2P test in that file, whatever its fix does. This affects every arm alike. Stage 1 here mostly measures whether the agent guessed the project's internal names, which is why the plan made the rubric the primary outcome. Adapting the tests to the agent's names with a model was considered and not done: it would add a third model step that could bend the tests, for an outcome that cannot change a verdict.

### 5.4 Inspector agreement and robustness

The two inspectors agreed closely on the 1,164 rubric items: Cohen's kappa 0.861 with two classes (met vs not) and 0.814 with three. On Sonnet's scores, H1 is +0.189 (Holm-adjusted p = 0.0002, Signal) and H2 +0.057 (p = 0.157, no large effect), so neither verdict depends on the inspector. Intervals clustered by repository are +0.075 to +0.236 for H1 and -0.014 to +0.142 for H2. With can't-tell items left out, the scores are A 0.469, B 0.633 and C 0.569 (B-A +0.164, B-C +0.064).

### 5.5 Token efficiency

| Median per run | A | B | C | Wilcoxon B vs A | B vs C |
|---|---|---|---|---|---|
| Total tokens | 85,488 | 129,164 | 110,858 | p < 0.001 | p = 0.17 |
| Turns | 12 | 16 | 14 | p = 0.002 | p = 0.50 |
| Seconds | 43 | 68 | 63 | p = 0.005 | p = 0.34 |

With human-review intent the agent did more: a median of 51% more tokens than with the issue alone, more turns and more time. B and C do not differ clearly.

### 5.6 Other reported items

C against A: +0.094 (bootstrap CI +0.010 to +0.183; Wilcoxon p = 0.080). Agent-review intent may also help, but the evidence is weaker than for human review, and this comparison was reported, not tested.

By language (descriptive): in Go (n = 27), rubric scores were A 0.398, B 0.608, C 0.488; in Python (n = 29), A 0.528, B 0.642, C 0.626. B is above A in both languages. Agent-review intent comes close to human-review intent in Python but not in Go.

Summaries: the median length was 142 words for B and 140 for C. The leak check fired on 8 first answers in B and 6 in C. The rule check (code spans or length) fired on 32 first answers in B and 21 in C; after the one regeneration, 25 B and 16 C summaries were cut to 150 words. B summaries broke the rules and were cut more often than C summaries; both sides followed the same procedure. The comment scrub removed 2 lines, both in arm B. There were no timeouts and no refusals.

## 6. Discussion

H1 holds: on these 56 PRs, a summary of human review given before the agent starts moved its fix closer to what the project merged, by 0.16 of the rubric on average, under both inspectors. H2 does not: human-review intent was not shown to beat agent-review intent; the difference was 0.07 and its interval includes zero.

What each outcome would mean was stated before the data were read. If B beats A and B beats C, the intent in human review carries something that the issue and AI review do not, on these PRs and for this agent. If B beats A and C does too, with B and C close, the gain may come from any added statement of intent or from added text, and this design cannot separate the two. If B beats A but not C, human review is not shown to differ from agent review as a source of intent. If neither B nor C beats A, a summary of review given up front does not help this agent on these tasks, at a size this study can detect. If B scores lower than A, the summary may mislead or distract, and the paired differences will show which PRs drive it. In every case a null result rules out a large effect, not a modest one (Section 4.6).

The third case occurred: B beats A, and B is not shown to beat C. C's own gain over A (+0.09, reported only) sits between the two, so the data also fit the second case, where any statement of intent helps and its source matters less. A study with more PRs, or one that varies the AI review agent, could tell these apart. The gain is uneven: about half the PRs gain, and nearly a third score the same in A and B. Which PRs gain, and why, is not analysed here. The cost is real: the agent spent about half again as many tokens with human-review intent. Whether the gap between human and agent review is real but small, or depends on which review agent wrote the comments, is the clearest open question.

## 7. Threats to validity

The study cannot show why intent helps or not. It measures closeness to what the project accepted, not code quality in general. The rubric comes from the merged PR, so "closer to what was accepted" is the outcome by definition, and a different good fix can still lose items. Rubrics and inspections are model-made and were not validated against human labels. The agent may have seen these repositories, or these PRs, in training. That affects all three arms alike, but it can lift every score and leave less room for B to differ.

Review is summarised once by one model, and a different summariser may carry different intent. Only inline review conversations are in the data; top-level PR comments and discussion elsewhere are not. Review comments respond to a draft the agent never sees, so some intent arrives as advice about code that does not exist in the agent's run. Issues are fetched now and may have been edited after the PR. Each PR has one run per arm, so run-to-run noise is in the comparisons and is not measured separately. The study covers two languages, 22 repositories, and AI review from the agents in one dataset, and results may not carry to other projects or agents. The summary and leak rules reduce the risk that a summary hands the agent the answer, but they do not remove it, and Amendment 1 shows that the first rules missed a code fragment.

Operational events during the main run are disclosed here. Each language ran as one process, paused overnight by a planned stop and resumed in the morning. Three further restarts happened: the Go process after Windows briefly locked a work folder and two PRs were skipped before any of their runs; the Python process to load the fix for that lock, while one PR's summaries were being written and before any of its arms ran; and the Python process again to load the repaired recipe for azure-cli #32298. No agent run was cut short, and the skipped PRs were run after the restart. Several fixes were made before the runs they affect. Container recipes (not part of the plan) were fixed during pilot setup: Python dependencies resolved as of the PR's merge time with the project's own constraints, generated files that projects keep out of git (Home Assistant translations, zitadel's protobuf code) produced in every container, and OpenTofu installed for terragrunt. Amendment 2 limited Go stage 1 to the PR's changed test functions. The eligibility rule differs from the earlier sampled checks in two ways, both fixed before any agent run: it now needs a runnable test file, and regex escapes that a copied script had lost were restored. Amendment 3, made after the pilot and before any main-run agent run, changed one line of the agent prompt so the file tools are given the checkout's own paths rather than /work paths (Section 4.7).

## 8. Reproducibility

The study lives in `studies/04-review-intent` of the public repository github.com/Shiningingy/ai-code-trust-studies. The frozen plan is `plan.md`; it was frozen in commit `21592ab` on 2026-11-07, before the pilot's first agent run, and its Amendments section lists every later change. Selection scripts and outputs are in `selection/` (`pool.py`, `overlap.py`, `langs.py`, `eligible.py`, `draw.py`; outputs `eligible.csv`, `main_walk.csv`, `agents.csv`). The pipeline is in `scripts/`, and `scripts/analyze.py` carries out Section 4.6. The seed for the draw, the order of arms and the bootstrap is 20261107. All model calls ran through `claude -p` on a Claude subscription, with model, flags, Claude Code version and usage logged per run. The AgentReviewChat parquet files come from Hugging Face `Suzhen/AgentReviewChat` and are not copied into the repository.

## Appendix A. Audit of excluded PRs

Every exclusion was checked for whether it came from the PR itself or from this study's setup. A PR excluded because of the setup (a container recipe, a time limit) may be repaired and run. That is a correction, not a replacement, which the plan forbids. The same test applies to all 14 exclusions, and none of them had any agent run, so no result can bias which ones are repaired. Any repair is listed in the plan's Amendments.

| PR | Check failed | Reason | Cause | Repairable |
|---|---|---|---|---|
| zeta-chain/node #4153, #4192, #4203, #4330 | 1 | The merge commit's file set differs from the PR's files, so the base commit would not match the PR | PR history | No |
| getsentry/sentry-python #4873 | 4 | No human-started review conversation to summarise (arm B impossible) | PR | No |
| pingcap/tidb #60776 | 4 | No human-started review conversation to summarise (arm B impossible) | PR | No |
| Azure/azure-cli #32115 | 3 | PR tests ran (171 passed on base and merge); none fails before the change | PR | No |
| ava-labs/avalanchego #4259 | 3 | PR tests ran (96 pass on base and merge); none fails before the change | PR | No |
| pingcap/tidb #63878 | 3 | PR tests ran (13 pass on base and merge); none fails before the change | PR | No |
| streamlit/streamlit #12074 | 3 | PR tests ran (56 passed on base and merge); none fails before the change | PR | No |
| volcano-sh/volcano #4354 | 3 | PR tests ran (24 pass on base and merge); none fails before the change | PR | No |
| streamlit/streamlit #11690 | 3 | The only changed test is a browser end-to-end test with pixel-exact screenshots (Playwright); pytest collected no tests | Setup, in principle | Not attempted: needs browsers in the container, and pixel-exact screenshots are unlikely to match across machines |
| Azure/azure-sdk-for-python #40615 | 2, then 3 | Tests replay recorded HTTP traffic through the Azure SDK test proxy; without the proxy every test failed. Repaired: the recordings now replay offline, but the tests that exercise the bug are live-test-only | Setup, then PR | Repaired; still excluded (no fail-to-pass test offline) |
| Azure/azure-sdk-for-python #41742 | 2 | Tests need a live Cosmos DB account or emulator (the test setup connects on import) | Setup | Not attempted: needs a full database emulator inside the container |

Azure/azure-cli #32298 passed the build checks, but its tests ran longer than the 30-minute stage-1 limit (a setup cause).

Outcome: #32298 was repaired by running the same tests in eight parallel workers (pytest-xdist); one pass then took about 6 minutes, and the PR yielded 9 fail-to-pass and 284 pass-to-pass tests and joined the run. #40615's recorded tests now replay offline through the test proxy (457 pass-to-pass, none flaky), but the only tests that exercise the bug are marked live-test-only and have no recordings, so it moved from check 2 to check 3 and stays excluded. Neither repair changed any other PR's environment.
