# Step 2 results: execution with pass/fail feedback (run 2026-11-25, 00:55-03:20)

Design frozen in [plan.md](plan.md) ("Step 2") before any run. 36 runs: 3 arms × 2 models (Sonnet 5.5, Opus 5.5) × 2 public Constraint Solving Search examples × 3. Claude Code 2.1.289, clean mode, tools Read/Grep/Glob/Bash. Feedback after a wrong answer: only "Your answer is incorrect…". Stop at a pass, 5 attempts or 20 minutes.

- **Arm A (RQ1):** the agent's own step-1 plan (near-miss check at best, scored PARTIAL).
- **Arm B (RQ2):** its own step-1c plan (defines a near-miss, then describes full coverage; scored FULL).
- **Arm C (RQ3):** no plan; a critic (same model) sees every proposed tool call and can block it with a reason.

**Cost correction (2026-11-25, after step 3).** With `--resume`, Claude Code reports each attempt's cost as the session's running total, and the runner had added the attempts up. Runs with more than one attempt were over-counted (13 of 72 runs in steps 2 and 3). All costs here are corrected ([scripts/fix_costs.py](scripts/fix_costs.py); the original summary is kept as [data/step2_summary_uncorrected.jsonl](data/step2_summary_uncorrected.jsonl)). Attempt-1 costs were always right.

Numbers: [data/step2_summary.jsonl](data/step2_summary.jsonl) (one line per run; transcripts and critic logs are kept locally under `runs/`, not committed). **Method codes are Claude's proposals, for Zili Luo to check**: [coding-step2-notes.md](coding-step2-notes.md) (Sonnet A and B, plus the coding convention), [coding-step2-opusAB.md](coding-step2-opusAB.md), [coding-step2-armC.md](coding-step2-armC.md). Parts of the Opus and arm-C coding were done by Claude subagents from the transcripts and spot-checked by Claude.

## Result in short

| Model | Arm | Pass | Pass at attempt 1 | Mean cost per run (range) | Mean time | Critic share of cost | Highest method reached |
|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | A: own partial plan | 6/6 | 4/6 | $0.34 (0.24-0.45) | 101 s | - | L1 |
| Sonnet 5.5 | B: own full-coverage plan | 6/6 | 6/6 | $0.36 (0.22-0.55) | 109 s | - | L1 |
| Sonnet 5.5 | C: critic, no plan | 6/6 | 5/6 | $0.67 (0.38-1.38) | 183 s | 51% | L1 |
| Opus 5.5 | A | 6/6 | 6/6 | $0.44 (0.33-0.58) | 131 s | - | L1 |
| Opus 5.5 | B | 6/6 | 5/6 | $0.77 (0.47-0.98) | 199 s | - | L2 (1 run, borderline) |
| Opus 5.5 | C | 6/6 | 4/6 | $2.39 (0.59-4.87) | 545 s | 58% | L1 |

Plans cost extra and are not in the table: Sonnet's six step-1 plans $0.18 and six 1c plans $0.18; Opus's are in [results-step1.md](results-step1.md). Total step-2 spend: Sonnet $8.21, Opus $21.65, both under their caps ($25, $40). No usage-limit stop, no time-outs, no key access.

- **Every run passed within the limits.** 30 of 36 passed on the first answer, 5 on the second and 1 on the fourth.
- **Every wrong answer was a missed person, never a wrong inclusion**, as in Study 06. P-101 was missed in 5 of the 8 wrong answers. Their roster line is in lowercase ("amina foster under identifier p-101"), so case-sensitive patterns never load them; their employer's city line is also lowercase ("organization 007 is based in Lunenburg").
- **Full coverage (L2) was planned often and executed almost never.** Of 44 coded attempts, 1 is L2 (Opus B-00001-3, borderline). The rest are keyword sweeps, near-miss re-reads and pattern fixes (L0/L1).

## RQ1: from a partial plan, with pass/fail only, does the agent reach full coverage?

**No, and it did not need to.** All 12 runs passed (Sonnet 4/6 and Opus 6/6 on the first answer). No run went beyond L1. Both Sonnet runs that failed first fixed the cause on attempt 2 with narrow pattern work:
- A-Sonnet-00001-1 missed P-091, whose employer appears only in a quote with a grammar slip: "My regex missed that phrasing" ("I currently works for Org 005"). The fix came from a phrasing census of first-person sentences (L1).
- A-Sonnet-00001-2 found 2 of 5: "my bus-only pattern was too narrow" (tram/train/subway), plus a "St. John's" → "St" city parse bug. Pattern widening (L0).

Cost: $0.34 per run for Sonnet and $0.44 for Opus. Sonnet's is about 2.5 times Study 06's H arm ($0.14, no plan) and below its HV arm ($0.48, imposed coverage check). The plan in the prompt makes the agent do more checking than the bare task does (but Study 06 used `--safe-mode`, so the harness settings differ; see Limits).

## RQ2: from a plan that describes full coverage, at which attempt does L2/L3 appear?

**Almost never, because failure was rare and the plan's coverage step was cut short on the first attempt.** 11 of 12 runs passed on attempt 1. The one failure (Opus B-00000-2, missed P-101) was fixed on attempt 2 by re-parsing the roster case-insensitively (L1), not by switching to coverage.

The step-1c plans all scored FULL, but in execution:
- **Sonnet:** 0 of 6 ran the full-coverage step. Several tried a template inventory and dropped it: "Too many templates, because the name normalisation is loose. I'll look at the sentences that touch the three conditions instead" (B-00000-2). "I did not run the full template profiling and 'other' passage review from the plan" (B-00001-2).
- **Opus:** 1 of 6 mostly ran it (B-00001-3: template inventory over all passages, 1,612 shapes, then filler verb classes set aside unread, which is why it is borderline). 4 ran it in part, on keyword hits only. 1 dropped it: "I didn't label all ~1,200 sentence templates one by one" (B-00001-2).

Cost: Sonnet B $0.36 (about the same as its arm A), Opus B $0.77 (1.7 times its arm A).

## RQ3: no plan, with a step-by-step critic

**All 12 passed (9 on the first answer), but by the same L0/L1 methods, at 2 to 5 times the cost.** The critic never led to L2 or L3. Four challenges asked for more coverage; both workers answered with narrower keyword filters.

- **Cost:** the critic is about half or more of every arm-C run ($10.31 of $18.38). Opus C averaged $2.39 and 545 s per run against $0.44 and 131 s for arm A. In the two longest runs (918 s and 1,139 s), about half the wall time was waiting for the critic, and 34% and 49% of tool calls were blocked, each needing a rewrite turn.
- **Quality of challenges** (91 in total, Claude's classification): 39 correct and useful (a real bug or a better step), 29 based on a false claim about the file or the state, 23 about process or form.
- **Helped:** twice a challenge pointed at the fix for a failed attempt, for example Opus C-00000-3 challenge #16, which found P-101.
- **Hurt:** false claims steered workers away from the answer. In Sonnet C-00000-1 the critic said four times that P-101 "never appear[s] anywhere in context.md"; P-101 is one of the answers. That run took 4 attempts and $1.38.

## Compared with Study 06 (Sonnet 5.5, same two examples)

| | Exact on first answer | Cost per run |
|---|---|---|
| Study 06 H: Claude Code, no check | 3/6 | $0.14 |
| Study 06 HV: + coverage check that must pass | 6/6 | $0.48 |
| Step 2 A: + its own near-miss plan | 4/6 (6/6 with retries) | $0.34 |
| Step 2 B: + its own full-coverage plan | 6/6 | $0.36 |
| Step 2 C: + critic | 5/6 (6/6 with retries) | $0.67 |

The first-answer column is the one comparable with the benchmark's own scoring, which is one answer per instance, scored once (paper §4.1). Retries use a pass/fail signal from the answer key, which the benchmark never gives; they show what reaching a correct answer costs when a perfect checker exists.

## Reading (Claude's, not Zili Luo's)

- **On these two examples, a better plan matters more than a check.** A written plan, even a partial one, lifts Sonnet from 3/6 to 4/6-6/6 on the first answer, at about HV's cost. Pass/fail feedback then closes the gap within one or two retries, cheaply.
- **Plans claim coverage; executions do not deliver it.** This is the step-2 version of Study 06's audit, where a self-written check was passed by relabelling: here the self-written plan is passed by doing a cheaper keyword sweep and saying so. On these examples the shortcut works, because the generator's facts use a small set of templates. A fact worded with none of the agent's keywords would still be missed.
- **A same-model critic is expensive and noisy.** About a third of its challenges were false, and it never moved the method beyond L1. Its useful challenges were mostly code-level bug catches.
- **The two public examples are too easy to separate the arms.** Every arm reaches 6/6; only cost differs. This fits the first author's remark that the task's point is cost, but it means the question "does the method change when it must?" is untested. Harder instances are needed (below).

## Limits

- Two examples, 3 runs per cell, one task. All differences are small-sample.
- Harness differs from Study 06: clean mode here, `--safe-mode` there (both load no CLAUDE.md, skills or memory; clean mode allows the arm-C hook).
- The pass/fail feedback comes from the answer key. No deployed agent has that signal.
- Method codes are from transcripts, proposed by Claude (partly by subagents), and depend on the convention that a keyword-limited residue is L1. They need Zili Luo's check.

**Harness fixes made during the run** (details in [plan.md](plan.md), "Implementation fixes"): the critic first saw the call it was judging as an earlier step, and runs shared a temp folder. Both were fixed at 01:30, and arm C was rerun. The 3 affected arm-C runs are in `runs/step2_v1_excluded/` and not counted. Arms A and B were audited and kept.

**Critic limitations still present** (found while coding arm C; not fixed, because arm C was already complete):
1. The hook reads its input with the Windows code page (GBK), so curly quotes reach the critic garbled. Four Sonnet calls containing curly quotes have no critic log entry and probably ran unreviewed, because the hook exited with an error (inferred from timing, not proven).
2. The critic sees each tool result cut to 500 characters, so it cannot see most of an output. Several false claims ("output was cut off", "never shown") follow from this.
3. Fix 1 also hides sibling calls issued in the same turn.
4. The critic gets its own session scratchpad path, not the worker's, and challenged correct worker paths.

These would need fixing before any further arm-C runs.

## Decisions for Zili Luo

1. **Coding convention:** count a keyword-limited residue as L1 (as coded), or as a partial L2?
2. **Opus B-00001-3:** L2 (template inventory over all passages, with whole verb classes set aside unread), or L1?
3. **Step-1c scoring vs execution:** several 1c plans scored FULL for steps their own runs then shortened to keyword sweeps. Keep the plan scores as they are (they score plans, not runs)?
4. **The two harness fixes and the exclusion of arm C v1:** accept?
5. **Next step.** The full suite (4 tasks × 50 instances; the full-suite check is a local note outside this repo, `longharness-check/full-suite-hardest-tasks.md`) offers:
   - (a) Constraint instances 2, 14, 29 and 41: five conditions each, with condition types the two public examples never had (guardian of someone on an evening course, prefers train to flying, enjoys a fruit). Staged at `E:\lhb-data-hard`, checksums verified. Arms A and B need plans generated first. Rough cost at tonight's rates: about $25-35 for A and B on both models.
   - (b) Outlier Memo Detection: the benchmark fixes the statement count at 2,500, so a coverage check there has a denominator the agent cannot choose.
   - (c) Fix the four critic issues and rerun arm C on the hard instances.
