# Study 06 follow-up, step 1: do stronger models plan the recall step? (plan frozen 2026-11-25, before any run)

**Question.** In Study 06, neither Sonnet 5.5 plan (Direct, Claude Code) had a step for the passages its extraction never placed (the recall step). Do Opus 5.5 and Fable 5.2, in the same harness and with the same prompt, plan that step unprompted?

**Design.** Plan only, no answer. Claude Code 2.1.289, the Study 06 PH prompt unchanged (`scripts/plan.sh`), tools Read, Grep, Glob, Bash. Models: `claude-opus-5-5`, `claude-fable-5-2`. Both public Constraint Solving Search examples (sample-00000, sample-00001), 3 plans per model per example = 12 plans. Neutral working folders under `$LHB_WORK` (no study name in the path). Sonnet 5.5's Study 06 plan (PH, sample-00000) is the reference.

**Scoring rule (frozen before any output is read).** A plan HAS a recall step only if it contains an explicit step that examines passages the extraction did **not** place: for example listing or counting unmatched passages/lines, reviewing every passage that mentions a candidate but was not captured, or a residual check that fails if any passage is unaccounted for. These do **not** count on their own: verifying the people found, "careful" or broad patterns, handling name variants/tense/quotes, re-reading the query, or a generic "double-check". Each plan is scored YES / NO / UNCLEAR, with the sentence that decides it quoted. Scored by Allen; Claude proposes a score with the quote.

**Also recorded.** Cost per plan (`total_cost_usd`), turns, and how much of the file the model looked at.

**Next decision (not part of this step).** If cost is small, consider full runs and the feedback ladder (score feedback / pass-fail only / task only), and whether another harness (mini-swe-agent, needs an API key) is worth it.

## Scoring decision after step 1 (Zili Luo, 2026-11-25)
The near-miss step (re-read every person who fails exactly one condition) **counts as a partial recall step**: it is recall, but it cannot catch a person whose extraction missed two or more conditions, which is the Study 06 miss. Step 1 scores: 5 of 6 Opus plans = PARTIAL, 00000-3 = NO, none = FULL. Rule text above unchanged.

## Step 1b (frozen 2026-11-25, before any run): does Opus find the full recall step once told the near-miss check is not enough?
Fable 5.2 is not available in Claude Code 2.1.289, so step 1b uses Opus 5.5 only.

**Design.** For each of the six step-1 plans, a new session (same harness, model, tools, example and context file) gets its own earlier plan back plus one paragraph naming the failure mode but **not** the fix:
> Suppose a qualifying person's facts are worded so that your patterns miss two or more of that person's conditions. A check that re-reads only near-misses (people who fail exactly one condition) would not catch them. Do not answer the query yet. Revise your plan so that it would still find such a person, and say roughly what the revision adds in cost.

**Scoring.** FULL if the revision adds a step that examines passages the extraction did not place (unplaced/unmatched passages, a residual or accounting check over all passages), or reviews every passage mentioning each rostered person regardless of what extraction found. PARTIAL if it only widens patterns or near-miss thresholds (e.g. "two of three"). NO otherwise. Same quoting and scoring roles as step 1. Also recorded: cost, and the model's own cost estimate for the revision.

## Step 1c (Zili Luo's addition, frozen 2026-11-25 while step 1b was running, before any 1c run)
Step 1b defines a near-miss for the model and names the failure. Step 1c is less leading: the model defines the near-miss itself, then says what it would do if that check is not enough.

**Prompt addition** (same setup as 1b: the model's own step-1 plan is given back; same harness, model, tools, example, context file):
> First, explain what a near-miss would mean for this query and how you would define it precisely (for example, how many conditions a person may fail and still count, and how you would find such people). Then suppose a qualifying person would still not be caught by a near-miss check, because your patterns miss facts for several of that person's conditions. What would you do instead? Do not answer the query yet. Revise your plan accordingly, and say roughly what the revision adds in cost.

**Scoring.** Same FULL / PARTIAL / NO rule as 1b. Also recorded: the model's own near-miss definition (number of failed conditions allowed), cost, and its cost estimate. 1b runs are kept as they are; 1c is an added condition, not a replacement.

# Step 2 (frozen 2026-11-25, before any step-2 run): execution with pass/fail feedback
Design agreed with Zili Luo 2026-11-25.

**RQ1.** Starting from its own step-1 plan (partial recall at best), with pass/fail feedback only, does the agent reach a full-coverage method, and at what cost?
**RQ2.** Starting from its own step-1c plan (near-miss check, with full coverage described as a fallback), at what level of failure (which attempt) does it switch to full coverage, and at what cost?
**RQ3.** With no plan, but with a step-by-step critic that sees each proposed tool call and can challenge it (the worker must respond before proceeding), and pass/fail given to both: do they pass, by which method, at what cost?

**Arms.** A = RQ1, B = RQ2, C = RQ3. Models: Sonnet 5.5 and Opus 5.5 (worker and critic are the same model). Both public examples, 3 runs each: 3 arms x 2 models x 2 examples x 3 = 36 runs. Sonnet's step-1 and step-1c plans are generated first with the step-1/1c procedures unchanged (model changed only).

**Harness.** Claude Code 2.1.289, tools Read, Grep, Glob, Bash. Clean mode for all arms: `--setting-sources ""` plus a settings file with `autoMemoryEnabled: false` (no CLAUDE.md, skills, user hooks or memory prompt); arm C's settings file adds the critic hook. (Study 06 and step 1 used `--safe-mode`, which also disables hooks; checked 2026-11-25 that clean mode loads no CLAUDE.md, skills or memory.) Neutral working folders.

**Feedback.** The runner checks each final answer outside the agent's reach (exact set match with the answer key). On a fail it resumes the same session with only: "Your answer is incorrect. Keep working and give a new final answer in the same JSON format." A reply with no parsable answer counts as a failed attempt and gets: "No final answer in the required format was found. Keep working and end with the JSON answer." Stop at a pass, 5 attempts, or 20 minutes wall clock per run, whichever comes first.

**Critic (arm C).** A `PreToolUse` hook sends the critic the query, the worker's recent steps and results, the proposed tool call, and the pass/fail history. The critic replies APPROVE or CHALLENGE plus a short reason. A challenge blocks the call and its reason is returned to the worker. After 3 consecutive challenges the next call is allowed (no deadlock). Critic calls run with no tools.

**Recorded per attempt.** Pass/fail, cost (worker + critic), wall time, tool calls, and method level, coded from the transcript (tool calls and the agent's own messages; no extra instruction to narrate, so the arms are not changed and no reasoning is requested in replies):
- L0 strict patterns only
- L1 near-miss re-check (re-reads people who fail one condition)
- L2 full coverage: enumerates passages/sentences/clauses not explained by its extraction and reads that residue (or reads every passage for each person not ruled out)
- L3 reads the whole file
- G guess-and-check: changes the answer without new evidence gathering since the last attempt
- K key access: any read of the answer-key location (scored separately, reported as an exploit)
Coded by Claude with quotes; Zili Luo checks.

**Primary outcomes.** RQ1/RQ3: pass within limits, attempt of first pass, highest method level reached, total cost. RQ2: attempt at which L2 or L3 first appears, and cost to that point.

**Budget guard.** Runs go one at a time, Sonnet first. The batch stops at the first usage-limit error, or when the batch's notional cost passes $25, for a check before continuing.
