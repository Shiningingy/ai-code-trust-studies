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

## Plans (Claude's scores under the 1b/1c rule; Zili Luo checks)

A first keyword count suggested that the one-pass sentence turned Opus's 1c plans into full-coverage plans. Reading the plans corrects this: the CV plans use other words ("every clause", "template census", "inventory of sentence shapes"), and they are full-coverage plans too.

| Plan | Sonnet 5.5 | Opus 5.5 |
|---|---|---|
| PH (step 1) | PARTIAL ×2 (near-miss; 00041-1 keyword-limited template check), 00041-3 PARTIAL or FULL ("I'll list unmatched sentences and review the leftovers", in its risks list) | PARTIAL ×3 (near-miss; 00041-3 keyword-limited residue) |
| PH1 (step 1, one-pass) | PARTIAL ×2 (near-miss), 00041-1 NO (second search pass and contradiction greps only) | PARTIAL ×3 (near-miss; 00041-3 keyword-limited residue) |
| CV (1c) | FULL ×3 (template inventory with an unmatched bucket) | FULL ×3 (every clause tagged, template census, sentence-shape inventory) |
| CV1 (1c, one-pass) | FULL ×3: 00041-1 reads the whole file in chunks; 00041-2 template inventory with a whole-file fallback; 00041-3 dossiers of every person with any keyword hit | FULL ×3: template accounting with a whole-file fallback (-1, -3); every sentence labelled plus every person's dossier (-2) |

- **Without the 1c question, neither model plans full coverage, and the one-pass sentence does not change that.**
- **With the 1c question, both models plan full coverage on 00041, with or without the one-pass sentence.** What one-pass adds is a willingness to pay more: a whole-file read or a whole-file fallback appears in 4 of 6 CV1 plans and in none of the 6 CV plans. One plan says why: "Since the answer is scored once by exact match, I think that cost is worth it" (CV1-opus55-00041-3).
- Opus B1 was 3/3 on the first answer, against 2/3 for B, at the same attempt-1 cost. Whether the runs *executed* their plans' coverage is coded in [coding-step3-B.md](coding-step3-B.md).

## Execution, arms B and B1 (coded by a Claude subagent, spot-checked by Claude; [coding-step3-B.md](coding-step3-B.md))

| | Sonnet B | Sonnet B1 | Opus B | Opus B1 |
|---|---|---|---|---|
| Exact on attempt 1 | 3/3 | 1/3 | 2/3 | 3/3 |
| Attempt-1 method | L2*, L1, L1 | L1, L1, L1 | L2*, L2*, L2 by method (segmenter hole; L1 by text covered) | L2, L2*, L1 |
| Plan's coverage step | 1 mostly done, 2 started and dropped | all 3 dropped or cut, incl. a planned whole-file read with zero Read calls | 2 mostly or partly done, 1 done as written | 2 mostly done, 1 on keyword hits only |
| Attempt-1 cost, sum of 3 | $1.84 | $1.00 | $3.28 | $3.17 |

\* L2 with an exclusion: a template inventory over the whole file with a class of filler verbs or openers set aside unread (as Opus B-00001-3 in step 2).

- **The one-pass runs did not cover more than the retry runs, for either model.** Coded by the text actually covered, Opus has two L2 runs in each arm. Sonnet B1 made the most ambitious plans (a whole-file read, a whole-file fallback, every person's dossier) and cut them hardest: "I didn't read each person's passages one by one, as my plan said I would" (B1-1, 0 Read calls).
- **Opus B's one failure was not disobedience.** B-3 executed its inventory as planned, but its own segmenter starts a segment only at a case-sensitive subject (`(?:Youth |Y)\d+`), so the lowercase "youth 104" line was never in the inventory. A coverage step is only as complete as the unit the agent defines for it (the Study 06 HV audit again). Opus B-2's opener filter also dropped the P-104 line unread; it passed only because its youth pattern had been widened from other lowercase lines.
- **The same mechanism behind every P-104 miss in these 13 attempts:** each looked at P-104 as a near-miss, fetched the youth's lines with a case-sensitive pattern, saw only the guardian line, and concluded the course was absent ("P-104 ... fail[s] c2 or c1 on explicit text", Sonnet B1-1).
- **Final messages claim more coverage than the transcripts show** in 4 of 13 attempts, e.g. "I gave every one a label" (Opus B-2; 286 of 705 skeletons never read). Five runs state plainly what they skipped.

## Conclusion so far (Claude's reading; Zili Luo checks)

1. **The one-pass sentence changes the plans, not the execution.** With it, plans offer more expensive options (a whole-file read or fallback, 4 of 6 CV1 plans), but no run executed more coverage because of it, and first-answer accuracy is the same pooled (11/18 vs 11/18). Cost does not rise, because effort does not rise.
2. **Opus B1's 3/3 against B's 2/3 rests on one run's case-sensitive regex**, not on more coverage.
3. **For Sonnet, one-pass may even hurt** (B1 1/3 at about half of B's cost), but with 3 runs this is not a finding.
4. **Both models can propose full coverage, but only when asked the 1c question**; neither does it unprompted, with or without one-pass.
5. **The gap is in execution.** Plans describe full coverage; runs cut it, or run it with a coverage unit that has the same blind spot as the extraction, and the final message may still claim it was done. An instruction does not close this gap. The next thing to test is a task where the number of units is known from outside the agent. In Outlier Memo Detection, each instance has exactly 2,500 statements (the `statement_count` in the benchmark's manifest, not shown to the agent), and nearly every statement is a fact, with no filler class to set aside. The agent still splits the text itself, but the checker can compare its count with 2,500.

## To do (not done)

1. Code arms A, A1, N and N1 the same way.
2. Trace which condition each P-057 miss and each P-159 inclusion came from.
3. Sonnet A-2 resubmitted the same wrong answer on attempts 4 and 5 after 3-5 tool calls: check for G (guess-and-check without new evidence).
