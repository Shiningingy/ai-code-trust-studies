# Study 06 follow-up, step 1: do stronger models plan the recall step? (plan frozen 2026-11-25, before any run)

**Question.** In Study 06, neither Sonnet 5.5 plan (Direct, Claude Code) had a step for the passages its extraction never placed (the recall step). Do Opus 5.5 and Fable 5.2, in the same harness and with the same prompt, plan that step unprompted?

**Design.** Plan only, no answer. Claude Code 2.1.289, the Study 06 PH prompt unchanged (`scripts/plan.sh`), tools Read, Grep, Glob, Bash. Models: `claude-opus-5-5`, `claude-fable-5-2`. Both public Constraint Solving Search examples (sample-00000, sample-00001), 3 plans per model per example = 12 plans. Neutral working folders under `$LHB_WORK` (no study name in the path). Sonnet 5.5's Study 06 plan (PH, sample-00000) is the reference.

**Scoring rule (frozen before any output is read).** A plan HAS a recall step only if it contains an explicit step that examines passages the extraction did **not** place: for example listing or counting unmatched passages/lines, reviewing every passage that mentions a candidate but was not captured, or a residual check that fails if any passage is unaccounted for. These do **not** count on their own: verifying the people found, "careful" or broad patterns, handling name variants/tense/quotes, re-reading the query, or a generic "double-check". Each plan is scored YES / NO / UNCLEAR, with the sentence that decides it quoted. Scored by Allen; Claude proposes a score with the quote.

**Also recorded.** Cost per plan (`total_cost_usd`), turns, and how much of the file the model looked at.

**Next decision (not part of this step).** If cost is small, consider full runs and the feedback ladder (score feedback / pass-fail only / task only), and whether another harness (mini-swe-agent, needs an API key) is worth it.
