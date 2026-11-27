# Step 4 results: a learned grammar library against plain and plan-first agents (2026-11-26)

Design: [plan.md](plan.md), Step 4 (frozen 2026-11-26, two recorded deviations). Sonnet 5.5, one-pass, first answer only, clean mode. 7 unstudied hard Constraint instances x 3 arms x 3 runs, plus the triage variant 90017 (G and N x 3). Costs are Claude Code's list-price figures; the runs used the subscription.

## 1. Headline

| Arm | Exact first answers | Precision | Recall | Mean cost per session | One-time cost |
|---|---|---|---|---|---|
| N (task prompt only) | 9/21 | 0.984 | 0.895 | $0.20 | - |
| P (plan-first sentence) | 15/21 | 1.000 | 0.924 | $0.26 | - |
| **G (learned grammar library)** | **18/21** | 1.000 | **0.971** | $0.35 | learning $19.63 |

- G was right on every instance except one (00014, 0/3), and all three G misses there are the same person for the same reason (section 3).
- Errors are almost all misses (recall), not false inclusions, in every arm.
- G costs about 1.75 times N per session, plus the learning, which equals about 100 N sessions; it does not pay for itself on 21 sessions. What it buys is accuracy (18 against 9).

## 2. By instance (passes of 3, mean cost)

| Instance | Conditions | N | P | G |
|---|---|---|---|---|
| 00002 | 5 | 3/3 $0.19 | 3/3 $0.28 | 3/3 $0.48 |
| 00014 | 5 | 0/3 $0.24 | 1/3 $0.25 | **0/3** $0.49 |
| 00029 | 5 | 1/3 $0.22 | 2/3 $0.31 | 3/3 $0.29 |
| 00003 | 3 | 1/3 $0.19 | 2/3 $0.26 | 3/3 $0.35 |
| 00021 | 3 | 1/3 $0.21 | 3/3 $0.23 | 3/3 $0.44 |
| 00039 | 3 | 2/3 $0.19 | 1/3 $0.20 | 3/3 $0.21 |
| 00045 | 3 | 1/3 $0.18 | 3/3 $0.25 | 3/3 $0.23 |
| 90017 (variant of 00017) | 5 | 0/3 $0.39 | - | 0/3 $0.74 |

N and P misses vary from run to run (different people missed); G's misses are systematic (the same person in every run), because every G session starts from the same library.

## 3. Why G failed where it did

**00014: a reading rule learned in training, carried by the library's notes.** P-069's train preference is written "I. Usman prefers train to plane when both are available", without "genuinely"; the key counts it. In training document 3 (00041) all five answer people had "genuinely prefers" and the one bare "prefers" belonged to a non-answer person. Of the three learners, A and C counted any train-over-plane preference; B required `genuinely` (its `example_queries.py` and NOTES.md). The reconcile session wrote v0's new query helper and the NOTES.md line with B's strict reading, `genuinely` AND `when both are available` (v0 NOTES.md line 6, tools/query.py line 73). *Correction, 2026-11-26: an earlier version of this section said learner A wrote that rule; A's own helper does not have it.* All three test sessions used that reading. The library parsed P-069's facts correctly (checked with each session's final library); the error is in the query, learned from three labelled examples. The library transfers interpretations as well as grammar, including wrong ones.

Checked afterwards (code, no model): the grammar rule `prefers_over` makes "genuinely" optional and records it as a qualifier, so the parse is right and only the query is wrong. The training key could not decide between the two readings: in 00041 the only person with a bare "prefers" (P-016) also fails three other conditions, so the answer is the same either way, and choosing the strict reading was a guess. Re-running test session 1's own query on its final parse gives its 4 IDs; dropping the `genuinely` check gives exactly the key's 5 (the condition count goes from 50 to 55 people; 00014 has 5 bare "prefers" lines). The benchmark's real near-misses for this condition are "likes train and plane equally" and "chose train over plane only because of a disruption".

How often training could have settled it (code, v0 parse, all 18 of the 50 instances whose query has this condition; contexts SHA-checked against the release): in 5 of them (00011, 00014, 00031, 00032, 00049) an answer person's only train preference is a bare "prefers", so the key decides the reading; in the other 13, 00041 included, it does not (in 00023 v0 found no preference fact for one answer person). A random training set of 3 instances contains a deciding one with probability about 28%; 10 instances, about 69%; 20, about 93%. Containing one is necessary, not sufficient: the learner must still be marked wrong on it and change the reading. Without a library, the N and P sessions on 00014 included P-069 in 4 of 6 runs. The same situation came up for dairy, and v0 decided it the other way: the training query says "currently chooses to avoid dairy products", and every training answer person (00001, 00041) has "currently avoids". Even so, v0's NOTES.md says the bare "avoids dairy products" "means the same", and its query does not require `currently`. With the same evidence, one condition got the loose reading and the other the strict one, so the reading was decided case by case, not from a stated type of modifier.

**90017: an over-broad ignore-rule.** v0's `no_fact_clause` ignores any clause it does not recognise as a fact. The free-text line "Omar Chen never says no to apple; it is a favourite food" (P-095's fruit fact) was ignored by v0, so the test sessions never saw it as an outlier; all three missed P-095. In one run the free-text teacher line was also left ignored (P-113 lost). The stop hook counts an ignored clause as resolved, so this is the silent drop again, moved from "the regex did not match" to "the ignore-rule took it".

The same rule hides the "took part in X class as the teacher" construction, which never occurs in the training documents: v0 alone ignores all 16 such clauses in 00014. Every G session on 00002 and 00014 noticed the family and added a rule or manual entries for it, so this one did not cost answers here.

**A cheap code check for this (not run as an arm).** Under v0, ignored clauses that mention a person or an ID number about 150 per file in 00002, 00014 and 90017 (15 in 00029), and most belong to one construction family ("took part in ... class as the ..."). A stop hook that lists ignored clauses mentioning an entity would have put both decisive lines in front of the sessions.

## 4. Triage on the variant ([step4/score_variant.py](step4/score_variant.py))

How each known change was resolved by v0 alone and by each G session's final library:

| Kind (expected) | Changes | v0 alone | Sessions 1 / 2 / 3 |
|---|---|---|---|
| 2 new construction (rule) | 22 | 18 unresolved, 4 ignored | rule 14/17/17, manual 4/5/5, ignored 4/0/0 |
| 3 free text (manual) | 6 | 4 unresolved, 2 ignored | rule 3/3/2, manual 1/2/3, ignored 2/1/1 |
| 4 noise (ignored) | 8 | 6 ignored | 6 ignored + 1 manual each (1 line not located by the scorer) |

Kind 1 (form breaks) is not scored cleanly: its unit is a whole line, which usually also holds legitimate filler. Everything v0 reported as unresolved was resolved with facts; the failures are all clauses v0 had already ignored. Free text was often handled by a new rule instead of manual.jsonl; that parses it, but a one-off rule is not reusable.

**Consistency across the three independent sessions (free-text changes):** same resolution in 4 of 6 (night shift: rule x3; course: rule x3; guardian: manual x3; fruit: ignored x3, consistently wrong); different in 2 (volunteering: rule, rule, manual; teaching: ignored, manual, manual).

## 5. Learning

| Session | Cost | Hook rounds | Result |
|---|---|---|---|
| Learner A | $6.56 | 1 | 3/3 training answers, 0 unresolved, tests pass |
| Learner B | $5.18 | 2 | same |
| Learner C | $7.13 | 1 | same |
| Reconcile (v0) | $0.76 | 2 | same; base = A; 68 decisions in RECONCILE.md |

v0 is learner A's library with one word added to a name pattern, plus a query helper and notes. The reconcile session's decisions are reasoned (e.g. one relation `legal_guardian_of`, "previously" kept as a qualifier), but the three-learner cross-check confirmed A rather than corrected it. It also introduced the one error that mattered: the learners disagreed on the "genuinely" reading (A and C loose, B strict), the diff did not show it because it compares parses, not query interpretations, and the reconcile session's new query helper took the minority reading.

## 6. Harness notes

- **Summariser crash, recovered.** One G session (00021, rep 1) hit a Claude Code safety refusal (an `rm` of a temp file); the refusal is a transcript event with a plain-text `message`, which crashed run_step2's parser after the session had finished. Fixed; the run's result was rebuilt from its saved transcript with the runner's own functions ([scripts/recover_run.py](scripts/recover_run.py)), marked `recovered`: pass, $0.64.
- **Library not loadable at the first stop, 6 G runs (unexplained).** In 00003-1, 00014-2, 00029-1, 00029-2, 00039-3 and 00045-1 the hook reported "exactly one splitter must be selected; found 0" and all six v0 files changed, so it blocked; the sessions then fixed their library and answered. Every final library is v0's content plus added files (checked ignoring line endings) and loads. In five of these runs the session, debugging the hook's message, listed or read the hook's state folder (flagged `ledger_access`); in test mode that folder holds only the hook's log and v0's file hashes, no answers. *Explained 2026-11-26 ([results-step4b.md](results-step4b.md), section 4): the hook used the agent's current folder, and these sessions had left the shell inside a subfolder (for example `cd lib`) when they stopped.*
- No run read an answer key (`key_access` false in all runs).

## 7. What this suggests (Claude's reading; Zili Luo decides)

- A learned, query-independent grammar plus a completeness check beat both plain and plan-first agents on unseen instances (18/21 against 15/21 and 9/21), at about 1.75 times N's per-session cost plus a one-time learning cost.
- Its two failure modes are both **transfer of a wrong judgment**: a too-broad "carries no fact" rule and a too-strict reading rule, each learned from three training documents and then applied consistently. Neither is a coverage failure the current hook can see.
- Both are checkable. Ignored clauses that mention an entity can be listed by code. Reading rules in NOTES/query helpers could be tested against near-miss variants, or kept out of the library (grammar only, each session interprets the query itself).

## 8. Next to the paper's Constraint results (rough; not a like-for-like comparison)

The paper's Table 2 gives exact accuracy and USD per instance on all 50 Constraint instances, one run each. For example: GLM-5.3 mini-swe-agent 66% ($1.55), the best; GPT-5.6-sol Direct 58% ($0.690), OpenCode 56% ($1.72), mini-swe-agent 42% ($0.320); Gemini 3.8 Flash at most 20%. Here: N 43% ($0.20), P 71% ($0.26), G 86% ($0.35 per session; with learning spread over 50 instances about $0.74, over these 21 sessions about $1.28).

Why it is not like-for-like:
- **Different model.** Sonnet 5.5 is not in the paper. N (plain Claude Code) at 43% for $0.20 is a model-plus-harness point, not a harness result.
- **G was supervised.** Its learning sessions saw pass/fail feedback against three training answer keys. The paper's harnesses get no labels.
- **Sample.** 7 instances × 3 runs against the paper's 50 × 1. Costs here are Claude Code's list-price figures for runs that used a subscription.
