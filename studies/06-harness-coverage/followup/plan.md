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

# Step 4 (frozen 2026-11-26, before any step-4 run): learn a grammar once, reuse it, patch it
Decisions with Zili Luo 2026-11-25/26: train/test split; Sonnet 5.5 only; reader arms L/PL/LC dropped (built, never run on the benchmark; the ledger result is an observation, not an intervention); D-from-scratch replaced by G (Zili Luo's design): learning sessions write a grammar library once, test sessions reuse it and patch it. All model-facing texts are in [step4/DRAFTS.md](step4/DRAFTS.md) (generated from the code) for Zili Luo's approval.

**Instances (10 + 1 variant).** Train: 00000, 00001 (public examples), 00041 (studied), shown as train/doc1-3.md. Test (7, unstudied): five-condition 00002, 00014, 00029; three-condition relation + fruit 00003, 00021, 00039, 00045. All fetched from the HF release and checked against its manifest (SHA-256). The generator is not released, so the grammar is reverse-engineered from the text. The grammar covers every statement, not only the query's conditions, so it is query-independent (test queries 00002 and 00014 ask about "taught a class this year", which no training query does).

**Phase 1: learning (G only).**
- Three independent learning sessions (same prompt, fresh sessions, Write/Edit allowed) on the three training documents, each producing a library (step4/libs/learn-a, -b, -c). Up to 6 rounds of Stop-hook feedback: which training answers are correct (keys stay outside the workspace), whether the library's tests pass, how many clauses are unresolved. Labels are used in training only. Time limit 75 minutes each.
- [step4/merge.py](step4/merge.py) (code) compares the three libraries clause by clause on the training documents (signature: status + words of subjects, objects and qualifiers; relation names ignored) and groups disagreements by clause shape; the 40 largest groups get IDs.
- One reconcile session builds v0 from the three, records a decision per group in lib/RECONCILE.md, and must meet the same requirements (tests pass, nothing unresolved, training answers correct). Purpose (Zili Luo): avoid a one-time error of a single learner.

**Phase 2: test sessions (one-pass, first answer only, clean mode; tools Read, Grep, Glob, Bash for all arms).**
- **N** task prompt only (runner arm N1).
- **P** plan-first sentence (runner arm P1).
- **G** (runner arm G1): workspace gets context.md, gram/ and a fresh copy of v0. **No patches travel between test sessions** (Zili Luo): every test session starts from v0, so sessions are independent; their patches are kept for analysis only. The session runs the library, triages each unresolved clause (Normalizer / Rule / manual.jsonl), must not edit v0's parts, answers with a query over the facts. Stop hook ([step4/hook.py](step4/hook.py), test mode): re-parses context.md itself with a pristine copy of gram (a session that edits its own gram/ cannot change the check) and blocks once, naming up to 50 unresolved clauses, if any remain or tests fail. Recorded: edited v0 parts, new parts, unresolved count, answer before and after the check.

**Framework ([step4/gram/](step4/gram/), harness-provided, task-agnostic).** Splitter / Normalizer / Rule (+ PatternRule, whole-clause regex), each with `name`, `solves`, `added_by`, `examples` (run as tests); a config selects parts; rules are auto-discovered. Enforced in code: a splitter may drop only text matching its declared connector patterns; a normalizer must keep every word (same word count; each word the same up to case or a typo fix of edit distance at most 2 on words of 4+ letters), so a "data fix" cannot delete meaning such as "in the past"; two rules giving different facts is reported as ambiguous; facts must have subject and relation. Checked offline with a toy library ([step4/tests/test_offline.py](step4/tests/test_offline.py)).

**Outlier triage (Zili Luo).** Broken form -> Normalizer; missing construction -> Rule; free text no grammar should cover -> manual.jsonl with facts or "ignore" and a reason.

**Triage test (Zili Luo): a variant with known changes.** [step4/make_variants.py](step4/make_variants.py) builds sample 90017 from test-pool instance 00017 (five conditions, unused elsewhere; seed 17): 40 form breaks (typo, case, spacing) -> expected Normalizer; 22 facts rewritten in constructions the generator never uses (4 per relation) -> expected Rule; 6 decisive facts of answer people rewritten once as free text -> expected manual; 8 inserted garbled passages -> expected ignored. Every change keeps the facts, so 00017's key still holds; 45 changes touch answer people. Manifest: step4/variants/90017-manifest.jsonl. Arms G and N, 3 runs each. Scored: answer, and per change how it was resolved against the expected kind (scoring script to be written after the runs).

**Runs and budget (estimate).** 3 runs per cell, as in steps 2-3 (Zili Luo, for consistency): learning 3 x ~$3 + reconcile ~$2 = ~$11; test 7 instances x 3 runs x 3 arms = 63 sessions ~$37; variant G and N x 3 = 6 sessions ~$4. About $52; cap $60 (learning phase checked separately: stop if it passes $15). Budget approved by Zili Luo 2026-11-26: runs use the subscription, so dollar figures are notional list-price costs; the caps stay as guards against runaway sessions and the session limit.

**Outcomes.** First-answer exact match and cost per arm; G: learning cost (once), cost per test session, patches by kind, unresolved before the hook, edits to v0 (should be none), answer before vs after the hook; variant: triage accuracy by kind. **Patch consistency (Zili Luo):** test sessions are independent (each starts from v0), so for every clause v0 leaves unresolved, compare across sessions whether it was triaged the same way (normalizer / rule / manual) and resolved to the same facts; compared by behaviour, not code, with merge.py's clause signatures.

**Frozen.** Zili Luo approved the drafts and said to start the runs (2026-11-26). Run order ([step4/run_step4.sh](step4/run_step4.sh)): learners a, b, c one at a time, then reconcile (v0), then the test sessions rep by rep (each rep: every instance, arms N1, P1, G1), then the variant (G1, N1 x 3). One session at a time, because parallel sessions share Git Bash's /tmp. On a usage-limit error the batch waits 30 minutes and retries the same session (Zili Luo: never exceed the session limit, wait for the reset); a retried session leaves an extra summary line, and the last line per run ID counts. The batch stops if a learning session ends in a non-limit error or produces no parts, if learning passes $15, or if step 4 passes $60.

**Deviation during step 4 (2026-11-26, 01:40).** Learner A finished in 21 minutes and one hook round (all three training answers correct, nothing unresolved, tests pass) but cost $6.56, against the $3 estimated. The batch then stopped on a path bug in its cost check (Git Bash /g/... path given to Windows Python; fixed with `pwd -W`). Since the runs use the subscription (Zili Luo, 2026-11-26), the guards were raised, not the design changed: learning stop at $25 (was $15), step 4 at $75 (was $60). New estimate about $68. Learner A's library is kept.

**Deviation 2 (2026-11-26, 02:50): the library diff, before the reconcile session ran.** All three learners passed (A $6.56 1 round; B $5.18 2 rounds; C $7.13 1 round; each: three training answers correct, nothing unresolved, tests pass). The first reconcile session was stopped after a few minutes, unused, because its diff was wrong for two reasons: (1) all three libraries import a helper by plain module name (`common`), so in one process library b loaded library a's helper and "did not load"; fixed in `gram.pipeline.load` (each library's helper modules are dropped from `sys.modules` before and after it loads); (2) the frozen signature (words of subjects, objects, qualifiers) flags almost every clause, because the libraries canonicalise differently ("H. Khan" vs "Hana Khan" vs "P-..."). Redesigned [step4/merge.py](step4/merge.py) to compare, over character-overlapping stretches of text, only what can be compared exactly: CARRY (facts / nothing / unresolved) and QUAL (a qualifier kept in one library, none in another); plus one side-by-side sample per base-library rule (R01...). On the training documents: 1,055 groups over 1,971 clauses; G01-G40 and R01-R28 must be decided in RECONCILE.md. Reconcile prompt unchanged.
