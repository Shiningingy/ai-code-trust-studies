# Does human review intent help a coding agent? A three-arm replay on merged pull requests

> **Status: partial draft (2026-11-07).** The main run stopped on schedule after 12 of the 55 runnable PRs. The plan gives no verdict below 30 complete PRs, so every result here is reported as *Inconclusive*, and numbers will change as the run continues. Items marked [check] still need verifying before release.

Zili (Allen) Luo · Independent study, November 2026 · Not peer reviewed · DRAFT: results sections are placeholders

## Abstract

Coding agents are usually judged by tests that confirm what was built, not what was asked. Human code review often says what a change should do and why. This study asks whether that intent, given to a coding agent before it writes anything, moves its fix closer to what the project accepted. Each merged pull request (PR) from the AgentReviewChat dataset is replayed from the commit just before it, three times, with Claude Sonnet 5.5 in Claude Code: with the linked issue only (A), with the issue plus a summary of the human review (B), and with the issue plus the same kind of summary of AI-agent review (C). Results are scored by the PR's own fail-to-pass tests and by a behaviour rubric written from the issue and the merged PR, never from the review, and checked by two blind model inspectors. The analysis plan was frozen before any agent run. In this partial report, on 12 complete PRs from 10 repositories, the mean rubric score was 0.49 in arm A, 0.72 in arm B and 0.56 in arm C. B against A differed by +0.23 (95% bootstrap CI +0.09 to +0.39; Holm-adjusted p = 0.031), and B against C by +0.16 (CI +0.02 to +0.33; adjusted p = 0.063). The plan needs 30 complete PRs before giving a verdict, so both comparisons are inconclusive for now. Few runs passed the PR's own tests (1, 0 and 2 of 12), mostly because the tests call internal names the issue never gives. Arm B used a median of 171k tokens per run, against 85k in A and 98k in C.

## 1. Introduction

When a project reviews a pull request, reviewers often state what the change is meant to do and why. That information is rarely in the issue, and an agent that works from the issue alone has to guess it. The usual check on an agent's patch does not help here: tests confirm that the code does what its author built, which is not the same as what was asked. Human review is one of the few places where the "what and why" is written down by someone who knows the project.

This study asks one question. Does the intent in human code review (what the change should do and why, with code removed), given to a coding agent up front, move the agent's fix closer to what the project accepted? Two comparisons make the question precise. B against A asks whether review intent beats the issue alone. B against C asks whether human review intent differs from the same kind of summary made from AI-agent review. Arm C also controls for length: if B beats A only because it carries more text, C should beat A too.

The contribution is a three-arm replay design on real merged PRs, a scoring scheme that never builds its checklist from the review text, and a result, whichever way it comes out. A negative result is a result. The study is small and pre-registered: the plan was committed to a public repository before the pilot's first agent run, later changes are listed as dated amendments, and every model call ran on a personal Claude subscription rather than a funded API budget. It supports claims about these 22 repositories, these two languages and this agent, and no wider claims.

## 2. Related work

The nearest published work found is c-CRAB, a code review agent benchmark (arXiv 2603.23448; authors [check]). Review tools comment on a PR patch, and Claude Code (Sonnet 4.6) revises the patch from the PR head; hidden tests built from human review score the revision. Tools pass 20.1-32.1% of the tests, and human review passes all by construction. This study differs in three ways: it starts from the base commit, not the PR patch; review is up-front intent, not revision input; and it has an issue-only arm.

SWE-Review (arXiv 2607.06065; [check] details) feeds AI reviewer feedback to one revision and ablates no review, a bare reject and full feedback. It covers AI review only, and only after a patch exists. The closest precedent for "human discussion helps" is the MASAI ablation (arXiv 2406.11638), whose Table 1 reports that OpenDevin on SWE-bench Lite resolves 25.00% of tasks with the benchmark's `hints_text` and 16.00% without [check: figures from a background read, not re-verified]. Those hints are issue-thread comments, not review.

Leakage is a standing risk when human text is given to an agent. SWE-Bench+ (arXiv 2410.06992) reports that 32.67% of resolved instances had the fix spelled out in the issue or its comments [check]. This study answers with a leak check on every summary (Section 4.2) and a rubric that avoids required names and structure.

Work on missing intent in coding tasks is related background: Ambig-SWE (arXiv 2502.13069; reported at ICLR 2026 [check]) and the clarification papers "Ask or Assume?" (2603.26233) and CLARITI (2604.14624). They study an agent asking for what the task leaves out. Here the missing information is supplied up front from review. For scoring, Google's work on rubric judging (arXiv 2511.10865) uses LLM-drafted, human-refined rubrics; it reports 96% of patches passing reproduction tests against 80% judged valid by the rubric [check: what each figure measures]. The rubrics here are model-drafted and not human-refined, which Section 7 states as a limit.

The data come from "Human-AI Synergy in Agentic Code Review" (arXiv 2603.15911 v2), which published AgentReviewChat (Hugging Face `Suzhen/AgentReviewChat`, MIT): inline review conversations on GitHub PRs, each started by a human or by an AI review agent. That paper is observational. A search on 2026-11-07 found no published study with this three-arm design (issue; issue plus human-review intent; issue plus agent-review intent) on merged PRs from the base commit. The search was short and read abstracts, so "not found" is the claim. [check: re-search before release; c-CRAB and SWE-Review are recent.]

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

Anything else is exploratory and labelled so. Rubrics and inspections were not validated against human labels; two were spot-checked by the author. [check: confirm this sentence still holds when the report is finalised.]

### 4.7 Pilot

A pilot of ten PRs, not counted in the results and removed from the main draw, was drawn with seed 20261107 from the eligible PRs of four repositories: three from home-assistant/core, two from getsentry/sentry-python, three from gruntwork-io/terragrunt and two from zitadel/zitadel. It ran all three arms with Sonnet 5.5, and arm A once more with Opus 5.5 at medium effort as the agent. The pilot looked at whether each PR builds and has F2P tests, at plumbing (empty runs, crashes, timeouts, leak hits, scrubs), at every summary read by hand for how-level content, and at usage per role and model, which set the main run's pace. For the ceiling check it looked at arm A alone, Sonnet against Opus. Scores for arms B and C were computed to test the pipeline but not printed or read, and no comparison between arms was made on pilot data. The ceiling rule said that if Sonnet in arm A resolved at least 8 of 10 PRs with a mean rubric score of at least 0.9, the selection would be tightened before the main draw. Nine of the ten pilot PRs got runs; zitadel #11009 got none because of an orchestration error (two processes ran it into one folder). The pilot found one harness fault: the prompt said the checkout "is mounted at /work", and in 21 of 36 pilot runs the agent passed /work paths to its file tools at least once. Those calls were denied, and several runs then stopped without changing anything. Amendment 3 changed the wording before any main-run agent run, the same in every arm, and a check run after the change had no denials. The ceiling rule did not fire: in arm A, Sonnet resolved 1 of 9 piloted PRs with a mean rubric score of 0.48, and Opus resolved 3 of 9 with 0.76. Both figures are depressed by the /work fault, so Section 5 also reports arm A's resolved rate against the rule. Usage per run set the main run's pace: Sonnet agent runs used about 2.2 million tokens over 27 calls, and the main run paused new calls when the five-hour usage window passed 80%.

## 5. Results

### 5.1 Selection and exclusions
Of the 70 drawn PRs, 14 were excluded at the build checks. Four failed check 1 (the merge commit's file set differs from the PR's; all four from zeta-chain/node). Two failed check 2 (environment): their tests need network services at test time (the Azure SDK test proxy with its recordings, and a live Cosmos DB emulator). Six failed check 3 (no fail-to-pass test). Two failed check 4 (no human review conversation left to summarise). One PR, Azure/azure-cli #32298, is undecided: its tests run longer than the 30-minute stage-1 limit. That left 55 runnable PRs (28 Python, 27 Go).

The run was paced to stop before a fixed time and stopped after 12 complete PRs (4 Python, 8 Go) from 10 repositories. No PR was left with an incomplete set of arms. No run hit a usage limit, timed out or was refused. The 12 are the first ready PRs in draw order in each language, so they are not a random subset of the 55. Go is over-represented because its environments were ready sooner.

### 5.2 Primary: rubric score
| | A | B | C |
|---|---|---|---|
| Mean rubric score (Opus inspector), n = 12 | 0.494 | 0.720 | 0.564 |

| Comparison | Mean paired difference | 95% bootstrap CI | Wilcoxon p (non-zero pairs) | Holm-adjusted p | Verdict |
|---|---|---|---|---|---|
| H1: B vs A | +0.226 | +0.087 to +0.385 | 0.016 (7) | 0.031 | Inconclusive (fewer than 30 PRs) |
| H2: B vs C | +0.156 | +0.017 to +0.327 | 0.063 (8) | 0.063 | Inconclusive (fewer than 30 PRs) |

B never scored below A on any PR. Five of the 12 PRs scored the same in A and B. The gain over A comes from seven PRs, four of them by more than 0.25: google-cloud-go #13290 (+0.71), atmos #1225 (+0.67), azure-sdk-for-go #24702 (+0.57) and avalanchego #4147 (+0.29). In google-cloud-go, arm A changed a different file from the one the PR changed, and arms B and C both changed the same area as the PR.

### 5.3 Stage 1: tests
| | A | B | C |
|---|---|---|---|
| Resolved (all F2P pass, no P2P breaks) | 1/12 | 0/12 | 2/12 |

Exact McNemar: B against A, 0 B-only and 1 A-only (p = 1.0); B against C, 0 B-only and 2 C-only (p = 0.5).

Most stage-1 failures are not about behaviour. In 24 of the 33 unresolved runs, the PR's tests did not compile or import against the agent's code. They call names that only the merged PR introduced: unexported Go identifiers (`undefined: docURL`), private attributes (`_sync_credential`) and new constants (`CONF_SITE`). An agent that does not happen to pick the same internal names fails every F2P test in that file, whatever its fix does. This affects 8 of the 12 PRs and every arm alike. Stage 1 here mostly measures whether the agent guessed the project's internal names, which is why the plan made the rubric the primary outcome. In the one PR where B was the only unresolved arm (Weblate #16322), B broke one pass-to-pass test.

### 5.4 Inspector agreement and robustness
The two inspectors agreed closely on the 246 rubric items: Cohen's kappa 0.950 with two classes (met vs not) and 0.889 with three. On Sonnet's scores, H1 is +0.238 (Holm-adjusted p = 0.063) and H2 +0.140 (p = 0.195). Both are still inconclusive, so no verdict depends on the inspector. Intervals clustered by repository are +0.088 to +0.409 for H1 and +0.015 to +0.356 for H2. With can't-tell items left out, the scores are A 0.509, B 0.724 and C 0.582 (B-A +0.215, B-C +0.143).

### 5.5 Token efficiency
| Median per run | A | B | C | Wilcoxon B vs A | B vs C |
|---|---|---|---|---|---|
| Total tokens | 85,488 | 170,596 | 97,972 | p = 0.13 | p = 0.62 |
| Turns | 14 | 18 | 14 | p = 0.32 | p = 0.37 |
| Seconds | 50 | 103 | 50 | p = 0.62 | p = 0.73 |

Arm B's median run used about twice the tokens of A, but on 12 PRs the difference is not distinguishable from noise.

### 5.6 Other reported items
C against A: +0.070 (CI -0.127 to +0.274; Wilcoxon p = 0.57).

By language (descriptive): in Go (n = 8), rubric scores were A 0.476, B 0.795, C 0.585. In Python (n = 4), they were A 0.530, B 0.571, C 0.524. Nearly all of the B-A gain so far is in Go PRs.

Summaries: the median length was 144 words for B and 138 for C. The leak check fired on one first answer (B). The rule check (code spans or length) fired on 5 first answers in B and 4 in C. After regeneration, 3 B and 2 C summaries were cut to 150 words. The comment scrub removed 2 lines, both in arm B. There were no timeouts and no refusals.

## 6. Discussion

With 12 of the planned 30 or more PRs, neither hypothesis has a verdict. H1 (B beats A) has the clearer pattern so far: B was never below A, its interval excludes zero, and it passes the Holm threshold, though the plan does not allow a verdict yet. H2 (B beats C) is weaker: B was above C on six PRs and below on two, and the adjusted p is 0.063. The numbers are given as a progress report, not as findings.

What each outcome would mean is stated here before the data are read. If B beats A and B beats C, the intent in human review carries something that the issue and AI review do not, on these PRs and for this agent. If B beats A and C does too, with B and C close, the gain may come from any added statement of intent or from added text, and this design cannot separate the two. If B beats A but not C, human review is not shown to differ from agent review as a source of intent. If neither B nor C beats A, a summary of review given up front does not help this agent on these tasks, at a size this study can detect. If B scores lower than A, the summary may mislead or distract, and the paired differences will show which PRs drive it. In every case a null result rules out a large effect, not a modest one (Section 4.6). No case can be named yet. So far the data look most like the first case (B beats both A and C), driven by Go PRs. The Python PRs show almost no difference between arms. With 4 Python PRs, that may be noise, or it may be a real difference between languages or repositories. The remaining 43 runnable PRs will decide which.

## 7. Threats to validity

The study cannot show why intent helps or not. It measures closeness to what the project accepted, not code quality in general. The rubric comes from the merged PR, so "closer to what was accepted" is the outcome by definition, and a different good fix can still lose items. Rubrics and inspections are model-made and were not validated against human labels; the author spot-checked two. The agent may have seen these repositories, or these PRs, in training. That affects all three arms alike, but it can lift every score and leave less room for B to differ.

Review is summarised once by one model, and a different summariser may carry different intent. Only inline review conversations are in the data; top-level PR comments and discussion elsewhere are not. Review comments respond to a draft the agent never sees, so some intent arrives as advice about code that does not exist in the agent's run. Issues are fetched now and may have been edited after the PR. Each PR has one run per arm, so run-to-run noise is in the comparisons and is not measured separately. The study covers two languages, 22 repositories, and AI review from the agents in one dataset, and results may not carry to other projects or agents. The summary and leak rules reduce the risk that a summary hands the agent the answer, but they do not remove it, and Amendment 1 shows that the first rules missed a code fragment.

Several fixes were made before the runs they affect and are disclosed here. Container recipes (not part of the plan) were fixed during pilot setup: Python dependencies resolved as of the PR's merge time with the project's own constraints, generated files that projects keep out of git (Home Assistant translations, zitadel's protobuf code) produced in every container, and OpenTofu installed for terragrunt. Amendment 2 limited Go stage 1 to the PR's changed test functions. The eligibility rule differs from the earlier sampled checks in two ways, both fixed before any agent run: it now needs a runnable test file, and regex escapes that a copied script had lost were restored. Amendment 3, made after the pilot and before any main-run agent run, changed one line of the agent prompt so the file tools are given the checkout's own paths rather than /work paths (Section 4.7).

## 8. Reproducibility

The study lives in `studies/04-review-intent` of the public repository github.com/Shiningingy/ai-code-trust-studies. The frozen plan is `plan.md`; it was frozen in commit `21592ab` on 2026-11-07, before the pilot's first agent run, and its Amendments section lists every later change. Selection scripts and outputs are in `selection/` (`pool.py`, `overlap.py`, `langs.py`, `eligible.py`, `draw.py`; outputs `eligible.csv`, `main_walk.csv`, `agents.csv`). The pipeline is in `scripts/`, and `scripts/analyze.py` carries out Section 4.6. The seed for the draw, the order of arms and the bootstrap is 20261107. All model calls ran through `claude -p` on a Claude subscription, with model, flags, Claude Code version and usage logged per run. The AgentReviewChat parquet files come from Hugging Face `Suzhen/AgentReviewChat` and are not copied into the repository.
