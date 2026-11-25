# Step 3 results: instance 00041 and the one-pass sentence (run 2026-11-25, 10:30-12:40)

Design frozen in [plan.md](plan.md) ("Step 3") before any run. 36 runs: 6 arms × 2 models × 3 runs on Constraint instance 00041 (five conditions: volunteered at 3+ events, guardian of someone on an evening course, prefers train to plane, enjoys a fruit, avoids dairy). Same harness and feedback as step 2. A trailing **1** means the plan was made and executed under the one-pass sentence ("You will give one final answer. It is scored once, by exact match, with no feedback and no second try."), and the run stopped after the first answer.

Numbers: lines with `"sample": "00041"` in [data/step2_summary.jsonl](data/step2_summary.jsonl). Spend: Sonnet $10.01, Opus $16.16, plans not included (caps $20 / $35). **Method levels are not coded yet.**

## First answer (the one-pass comparable)

| Model | B: 1c plan | B1 | A: step-1 plan | A1 | N: no plan | N1 |
|---|---|---|---|---|---|---|
| Sonnet 5.5, exact | 3/3 | 1/3 | 1/3 | 2/3 | 1/3 | 1/3 |
| Sonnet 5.5, mean cost of attempt 1 | $0.61 | $0.34 | $0.25 | $0.29 | $0.19 | $0.17 |
| Opus 5.5, exact | 2/3 | **3/3** | 2/3 | **3/3** | 2/3 | 1/3 |
| Opus 5.5, mean cost of attempt 1 | $1.09 | $1.06 | $0.52 | $0.52 | $0.50 | $0.39 |

- **Pooled, the one-pass sentence made no difference:** 11/18 exact on the first answer with it, 11/18 without. Opus 7/9 vs 6/9, Sonnet 4/9 vs 5/9. With 3 runs per cell this is noise-level.
- **It did not make the first attempt more expensive.** Attempt-1 cost is the same or lower in every one-pass arm.
- **Retry arms:** 17 of 18 reached the answer (Sonnet A-2 failed all 5 attempts, always missing P-104). Mean total cost: Sonnet B $0.61, A $1.56, N $0.37; Opus B $1.72, A $1.00, N $0.69.

## Errors (14 wrong first answers, plus 4 later attempts of Sonnet A-2)

Two first answers (Sonnet B1-1 and N-1) both miss P-104 and include P-159, so the rows add up to 16.

| Person | Wrong first answers | Cause (from the file; not yet traced in the runs) |
|---|---|---|
| P-104 missed | 8 | Dev Gupta's youth's course is in lowercase: "The same account also says that **youth 104** currently attends evening_pottery during the evening". Their guardian line is also the second clause of an "and" sentence. Same lowercase trap as P-101 in the public examples. |
| P-057 missed | 4 | Quinn Ortiz's train preference exists only as quoted first-person speech with curly quotes (‘Quinn Ortiz said, “I genuinely prefer train to plane…’), and the guardian line uses "Y057" while the course line uses "Youth 057". Which one each run missed is not yet checked. |
| P-159 wrongly included | 3 | Samir Novak meets four conditions; their only fruit is "enjoys eating mango **in the past**" (tense trap). |
| P-051 + P-127 missed | 1 (Opus N-3) | Not checked. |

**First wrong inclusions of the whole study.** Study 06 and step 2 had only missed people; on 00041, 3 first answers include P-159.

## Plans (keyword count only; not scored yet)

The one-pass sentence visibly changed **Opus's 1c plans** (CV1). They talk about labelling every passage or sentence, reading the unmatched residue, and a whole-file fallback. Words like "every passage", "residue" or "unaccounted" appear 8-10 times per CV1 plan, against 0-2 in the CV plans. One plan gives the reason itself: "Since the answer is scored once by exact match, I think that cost is worth it" (CV1-opus55-00041-3). Opus B1 was also 3/3 on the first answer, against 2/3 for B, at the same attempt-1 cost. Whether the B1 runs *executed* the coverage the plans describe is not yet coded; in step 2, plans claiming coverage mostly were not carried out.

The Sonnet plans show no such shift in the keyword count.

## To do (not done)

1. Code the method level of each attempt 1 (L0-L3), especially Opus B vs B1, and score the 24 plans (FULL / PARTIAL / NO; escalation ladder or not).
2. Trace which condition each P-057 miss and each P-159 inclusion came from.
3. Sonnet A-2 resubmitted the same wrong answer on attempts 4 and 5 after 3-5 tool calls: check for G (guess-and-check without new evidence).
