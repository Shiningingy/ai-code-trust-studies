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
