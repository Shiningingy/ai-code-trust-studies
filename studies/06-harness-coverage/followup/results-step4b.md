# Step 4b results: the same learning pipeline run by Opus 5.5 (2026-11-26)

Design: [plan.md](plan.md), Step 4b (frozen 2026-11-26, before any run; no deviations). Only the model in the four learning sessions changed (claude-opus-5-5). Prompts, framework, hook, test model (Sonnet 5.5), test instances and the variant are as in [step 4](results-step4.md). The decision to try Opus was made after seeing step 4's results. Costs are Claude Code's list-price figures; the runs used the subscription.

## 1. Headline (7 unstudied instances x 3 runs, Sonnet 5.5, one pass, first answer)

| Arm | Library learned by | Exact first answers | Precision | Recall | Mean cost per session | One-time learning |
|---|---|---|---|---|---|---|
| N (task prompt only) | - | 9/21 | 0.979 | 0.895 | $0.20 | - |
| P (plan-first sentence) | - | 15/21 | 1.000 | 0.924 | $0.26 | - |
| G | Sonnet 5.5 (v0) | 18/21 | 1.000 | 0.971 | $0.35 | $19.63 |
| **GO** | **Opus 5.5 (v0-opus)** | **21/21** | 1.000 | **1.000** | $0.37 | $26.86 |

N, P and G are step 4's runs. Variant 90017: GO 0/3, the same three people missed in every run (section 3).

By instance (passes of 3, mean cost per session):

| Instance | N | P | G | GO |
|---|---|---|---|---|
| 00002 | 3/3 $0.19 | 3/3 $0.28 | 3/3 $0.48 | 3/3 $0.37 |
| 00014 | 0/3 $0.24 | 1/3 $0.25 | 0/3 $0.49 | **3/3** $0.71 |
| 00029 | 1/3 $0.22 | 2/3 $0.31 | 3/3 $0.29 | 3/3 $0.32 |
| 00003 | 1/3 $0.19 | 2/3 $0.26 | 3/3 $0.35 | 3/3 $0.42 |
| 00021 | 1/3 $0.21 | 3/3 $0.23 | 3/3 $0.44 | 3/3 $0.27 |
| 00039 | 2/3 $0.19 | 1/3 $0.20 | 3/3 $0.21 | 3/3 $0.24 |
| 00045 | 1/3 $0.18 | 3/3 $0.25 | 3/3 $0.23 | 3/3 $0.30 |
| 90017 (variant) | 0/3 $0.39 | - | 0/3 $0.74 | 0/3 $0.74 |

In all 21 GO runs on the real instances, the answer given before the stop hook spoke was already correct. The hook blocked in 5 of them, and only because of the hook bug in section 4. The gain over G comes from the library, not from the completeness check.

## 2. Learning

| Session | Minutes | Cost | Hook rounds | Result |
|---|---|---|---|---|
| learn-a-opus | 41 | $9.09 | 1 | 3/3 training answers, 0 unresolved, tests pass |
| learn-b-opus | 35 | $7.26 | 1 | same |
| learn-c-opus | 30 | $6.98 | 1 | same |
| reconcile v0-opus | 12 | $3.53 | 2 (34 groups not yet recorded at the first stop) | same |

**The "genuinely" reading.** The Opus learners split 1 to 2, as the Sonnet learners did, but the other way round: A required `genuinely` (its `prefers_train`), B dropped the word altogether (one relation, `prefers_train_to_plane`), and C kept it as an optional qualifier. The reconcile session took the loose reading and gave a reason in RECONCILE.md (G25) and NOTES.md: "Do not require the `genuinely` qualifier: 'P. Foster prefers train to plane when both are available' (doc3 line 8193) is a real preference without the word." In step 4 the Sonnet reconcile session took the strict, minority reading. Dairy is read loosely as well, so the two conditions are now consistent.

**Qualifiers.** v0-opus maps time and negation words onto a small set of categories (`past`, `currently`, `future`, `planned`, `once`, `negated`, ...), and one function `current(f)` says which of them cancel a fact. Emphasis ("genuinely") and condition ("when both are available") stay as literal words. That is partly the typing discussed after step 4, for time and negation only, without being asked.

## 3. The variant 90017: the same failure mode again

All three GO runs missed P-010, P-113 and P-140, and run 2 also included P-018 and P-102 (not examined). For each missed person, v0-opus's ignore rule `commentary` took the decisive clause, and no session changed it:

| Person | Change (kind) | Clause | v0-opus |
|---|---|---|---|
| P-010 | free text (3) | "If you call Jia Diaz at noon you will wake them up, because Jia Diaz works nights" | ignored (`commentary`) |
| P-113 | free text (3) | "The repair class this year was run by Mateo Jones, who stood at the front as its teacher" | ignored (`commentary`) |
| P-140 | new construction (2) | "Eating watermelon is something Talia Usman enjoys" | ignored (`commentary`) |

The rule's own `solves` line says it ignores remarks "only if they hold no predicate word, no name, no number and no meaning-changing word ... so nothing factual is lost". The code (`is_commentary` in parts/common.py) checks a list of fact words, numbers, meaning words and **initial-form names only** ("J. Diaz"); a full name ("Jia Diaz") passes. The guard is narrower than the claim, and its examples do not test a full-name remark. Step 4's v0 failed on the same variant through an over-broad ignore rule as well (`no_fact_clause`). The cheap check from step 4, listing ignored clauses that mention a person, would have shown all three clauses.

v0-opus did not ignore step 4's decisive fruit line ("Omar Chen never says no to apple; ..."): it was left unresolved, and every session wrote a rule for it.

Triage (code, [step4/score_variant.py](step4/score_variant.py) with `S4_BASE=v0-opus`; full output [data/step4b_variant_triage.txt](data/step4b_variant_triage.txt)): of the 22 new constructions, v0-opus alone left 16 unresolved and ignored 6; the sessions resolved 16/16/17 by a new rule, ignored 5/5/4. Of the 6 free-text changes, the sessions resolved 4 by a new rule in all three runs and left 2 ignored in all three (the two rows above). Unlike step 4, the three sessions resolved every free-text change the same way.

## 4. Harness bug found: the stop hook used the agent's current folder

**Cause of "library does not load ... found 0 splitter" (step 4: 6 G runs; step 4b: 5 GO runs).** Claude Code's Bash tool keeps the working folder between calls. When a session's last command before stopping was, for example, `cd lib && python ...`, the hook received `cwd` = `<workspace>/lib`, looked for `<workspace>/lib/lib`, found no parts, and reported every v0 file as changed. Checked on all 48 G and GO transcripts: all 11 runs with the error had left the shell inside a subfolder at their first stop; no run without such a `cd` had it. (A first count showed 4 more runs with a `cd` but no error; in all 4 the `cd` was `..`, `../..` or `.`, which went back to the workspace root, so these were miscounts by the check.) Effect: in those runs the completeness check did not run at the first stop; the sessions fixed their folder and answered. In some of them the agent then ran the hook command itself, which it found from the error notice (4 GO runs touched the hook's folder; in test mode it holds no answers). Fix for any later step: give the hook the workspace path as an argument instead of reading `cwd`.

## 5. What this suggests (Claude's reading; Zili Luo decides)

- With the prompt unchanged, a stronger learner fixed the error that cost G an instance: the library learned by Opus gave Sonnet test sessions 21/21 on the unstudied instances, against 18/21 with the Sonnet-learned library, for $7 more one-time learning and about the same cost per session.
- The fix came from the reconcile step, not from all learners agreeing: one Opus learner still made the strict reading. The reconcile session's written reason (a counterexample line from the training data) is what decided it.
- The over-broad ignore rule did not go away. It changed form: from a missing guard (step 4) to a guard that is narrower than its own description (4b). It cost the variant in both steps. This is the failure a code check can catch (list ignored clauses that name a person), and it is independent of which model learns.
- Small sample: 7 instances x 3 runs, one learning run per model. 21/21 against 18/21 is three runs, all on one instance.
