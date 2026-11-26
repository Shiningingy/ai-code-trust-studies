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

## Implementation fixes during step 2 (2026-11-25, 01:30; design unchanged)
Found by Claude while coding the first arm-C traces; the batch was halted, fixed and relaunched. Recorded for Zili Luo to review.
1. **Critic saw the call it was judging as an earlier step.** At `PreToolUse` time Claude Code has already written the pending tool call to the transcript, so the critic's "recent steps" ended with the very call shown as "proposed next step". In arm C v1, 5 of 7 challenges in one run said the call "is identical to the one the agent just issued". Fix: the transcript tail drops trailing calls that have no result yet (checked live with a probe hook). This is what the frozen design specifies (recent steps + the proposed call); the critic prompt text is unchanged.
2. **Runs shared a temp folder.** Workers write scripts to `$TEMP` or `/tmp`, and Git Bash maps `/tmp` to the Windows user Temp whatever `TEMP` says, so later runs could see earlier runs' scripts and outputs. In arm C v1 a blocked write left a worker running an older run's `a.py`. Fix: each run gets its own `TEMP`/`TMP`, and before each run the runner moves worker-style files (`.py/.txt/.json/.pkl/.csv/.tsv/.md` at the top of the user Temp, and small folders holding only such files) to `$LHB_WORK/_tmp_quarantine/<run>/` (moved, not deleted). An audit of arms A and B found no command that used a temp file the run had not written itself (no calls were blocked in those arms), so they are kept.
3. Arm C v1 (Sonnet, 3 runs, the third cut off) is kept in `runs/step2_v1_excluded/` and not counted. Arm C is rerun with the fixes; Opus runs all use the fixed harness.

# Step 3 (frozen 2026-11-25, before any step-3 run): a harder instance, and telling the agent it has one answer
Design agreed with Zili Luo 2026-11-25 (morning): run on Constraint instance **00041**, keep the step-2 arms, and add a one-pass condition.

**Why.** The two public examples did not separate the arms (all reached 6/6). Instance 00041 has five conditions; two are known from the public examples (volunteered 3+, avoids dairy), three are new (guardian of someone on an evening course, prefers train to plane, enjoys a fruit). **One-pass (Zili Luo's addition):** an agent that assumes it can retry may plan a gradual ladder (direct, check, near-miss, check, full coverage) instead of choosing its method at the start. Note: in step 2 the agent was never told retries existed before its first answer, but the 1c prompt itself frames full coverage as a fallback.

**Arms** (instance 00041, Sonnet 5.5 and Opus 5.5, 3 runs each; same harness, clean mode, tools, limits and feedback text as step 2):
- **B** own 1c plan, pass/fail retries (as step 2). **B1** the same, but the plan is made and executed under the one-pass sentence, and the run stops after the first answer.
- **A** own step-1 plan, retries. **A1** one-pass version.
- **N** no plan, no critic, retries (task prompt only). **N1** one-pass version.
- Arm C is not run in step 3: the four critic issues in results-step2.md are not fixed yet.

Run order per model: B, B1, A, A1, N, N1; Sonnet first. Plans for 00041 come first, with the step-1 and 1c procedures unchanged (`--safe-mode`, same prompts); the one-pass plans (PH1, CV1) differ only by the one-pass sentence, and CV1 is revised from the model's own PH1 plan.

**One-pass sentence** (added to the plan prompt, and to the execution prompt of arms A1, B1, N1, just before the answer-format line):
> You will give one final answer. It is scored once, by exact match, with no feedback and no second try.

In the one-pass arms this is true: there is no feedback and no second attempt.

**Outcomes.** First-answer exact match, cost and time to first answer, method level of the first attempt (L0-L3/G/K, same codes), and for the retry arms the attempt of first pass and cost to first correct answer. The comparison of interest is X vs X1 on attempt 1. Plans are also scored FULL / PARTIAL / NO with the 1b/1c rule, and whether a plan is staged as an escalation ladder is noted.

**Budget guard.** Step-3 spend counted separately (sample 00041 only): stop at $20 for Sonnet, $35 for Opus, or at the first usage-limit error.

# Step 4 (DRAFT 2026-11-25 evening, not frozen; nothing run yet): shaping vs checking on unstudied instances
Decisions with Zili Luo 2026-11-25: test whether a harness-side coverage check generalises beyond the instances it was designed on; plan-first as a second factor; Sonnet 5.5 only (Opus dropped: both models already showed the silent-drop weakness in steps 2-3; Opus may be added later only if Sonnet's result is positive).

**Instances.** Hard Constraint 00002, 00014, 00029 (not studied in steps 2-3). Memo later, as a second task type.

**Arms** (all one-pass, with the step-3 one-pass sentence; first answer only; clean mode, same tools and limits):
- **N** task prompt only (runner arm N1).
- **P** plan-first sentence (below) before the task.
- **L** ledger hook: before the runs, the Haiku reader (thinking off) flags sentences once per instance; during the run a PostToolUse hook marks sentences SEEN when their text comes back in a tool result; when the agent first tries to finish, a Stop hook blocks once and shows the flagged-but-unseen sentences; the next final answer is scored.
- **PL** both.
- **LC** ledger count (added by Zili Luo): same SEEN tracking, no reader; when the agent first tries to finish, the Stop hook blocks once and shows only the number of sentences never shown to it, no content. Tests whether the agent's belief that it covered everything changes with a hard number alone.
  LC message (Claude's draft, for Zili Luo to confirm before freezing):
  > Before your answer is final: <U> of the <T> sentences in the context were never shown to you. Check whether any of them matter, then give your final answer.

**Plan-first sentence** (Zili Luo chose Claude's tightened version):
> Before you start, write a plan for solving this. List the ways your approach could miss something, and how you will rule out each one.

**Stop-hook message** (agreed), followed by the sentences:
> Before your answer is final: these lines may be relevant and were never shown to you. Check them, then give your final answer.

**Runs and budget.** 5 arms (N, P, L, PL, LC) x 3 instances x 2 runs = 30 Sonnet runs, about $19 (estimate) plus about $2 for the reader; cap $25.

**Implementation (built 2026-11-25 evening; tested on a 61-sentence dummy file with Haiku, not on a benchmark instance).**
- Runner arms: `N1` (= step-3 N1), `P1`, `L1`, `PL1`, `LC1` in [scripts/run_step2.py](scripts/run_step2.py). P adds the plan-first sentence after the task sentence.
- [scripts/ledger_hook.py](scripts/ledger_hook.py) is a Stop hook only. The ledger is computed from the transcript when the agent first tries to finish (same SEEN rule as ledger.py), so no PostToolUse hook is needed. It blocks once with Claude Code's JSON form (`{"decision": "block", "reason": ...}`); the agent then sees "Stop hook feedback:" followed by the message. With the exit-2 form the agent also saw the hook's command line, which named the study folder, so that form is not used. The hook runs from a neutral copy (`$LHB_WORK/_h/check.py`, state in `$LHB_WORK/_s/<run>`).
- Flagged sentences are shown as `line <n>: <sentence>` (line number in context.md).
- The answer the agent gave before the check is saved too (`runs/step2/<run>-ledger.json`), so each L/PL/LC run gives a before/after pair; the scored answer is the one after.
- Hooks passed with `--settings` work under `--setting-sources ""` (arm C used this; Stop confirmed in the dummy test).
- Reader: [scripts/haiku_reader.py](scripts/haiku_reader.py) with `v2` = the hook's sentence splitter (no split after initials such as "D.") and `alwaysThinkingEnabled: false` (thinking tokens 0 in the dummy test). Checked first on 00041 against the thinking-on result before use.
