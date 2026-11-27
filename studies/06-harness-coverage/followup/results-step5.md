# Step 5 results: the whole Constraint task (2026-11-26/27)

Design: [plan.md](plan.md), Step 5 (frozen 2026-11-26, before any run; no deviations). Four training documents (00000, 00001, 00041, 00020; together they cover all 9 query conditions). Sonnet 5.5 learners + reconcile → library v5; Opus 5.5 learners + reconcile → v5-opus. Test: the other 46 Constraint instances, one run each, Sonnet 5.5, one pass, first answer, in four arms (N1 plain, P1 plan-first sentence, G1 with v5, GO1 with v5-opus); then the variant 90017, G1 and GO1 × 3. Changes from step 4b: the prompts say "four documents", and the stop hook gets the workspace path (the cwd bug in [results-step4b.md](results-step4b.md), section 4). No check on ignored clauses was added. Costs are Claude Code's list-price figures; the runs used the subscription.

Data: [data/step5_summary.jsonl](data/step5_summary.jsonl) (190 test runs), [data/step5_learning.jsonl](data/step5_learning.jsonl), [data/step5_by_instance.csv](data/step5_by_instance.csv), [data/step5_why_missed.jsonl](data/step5_why_missed.jsonl), [data/step5_library_only.jsonl](data/step5_library_only.jsonl), [data/step5_variant_triage.txt](data/step5_variant_triage.txt).

## 1. Headline (46 instances × 1 run, first answer)

| Arm | Exact | Precision | Recall | Mean cost per session | Mean time | One-time learning |
|---|---|---|---|---|---|---|
| N1 (task prompt only) | 27/46 (59%) | 0.975 | 0.861 | $0.21 | 105 s | - |
| P1 (plan-first sentence) | 28/46 (61%) | 1.000 | 0.883 | $0.25 | 144 s | - |
| **G1 (library v5, learned by Sonnet)** | **36/46 (78%)** | 0.836 | **0.952** | $0.33 | 107 s | $24.03 |
| GO1 (library v5-opus, learned by Opus) | 35/46 (76%) | 1.000 | 0.939 | $0.58 | 175 s | $29.27 |

G1's precision comes from two sessions (section 3): one answered only one of the four conditions (37 extra people), one had 6 extras.

Paired on the same instances (exact McNemar, two-sided):

| Pair | Only the first passed | Only the second passed | p |
|---|---|---|---|
| G1 vs N1 | 13 | 4 | 0.049 |
| G1 vs P1 | 11 | 3 | 0.057 |
| GO1 vs N1 | 13 | 5 | 0.096 |
| GO1 vs P1 | 11 | 4 | 0.12 |
| P1 vs N1 | 8 | 7 | 1.0 |
| G1 vs GO1 | 2 | 1 | 1.0 |

By subset:

| Subset | Instances | N1 | P1 | G1 | GO1 |
|---|---|---|---|---|---|
| Untouched before step 5 | 24 | 15 | 14 | 20 | 18 |
| Scanned in step 4 for the "genuinely" count | 14 | 7 | 9 | 9 | 10 |
| Earlier test instances (steps 4/4b) + 00017 | 8 | 5 | 5 | 7 | 7 |
| The 5 where an answer person's only train preference lacks "genuinely" | 5 | 2 | 2 | **0** | **0** |
| The other 41 | 41 | 25 | 26 | 36 | 35 |

Variant 90017: **G1 3/3, GO1 3/3** (steps 4 and 4b: 0/3 each). Section 4.

## 2. Learning

| Session | Model | Minutes | Cost | Hook rounds | Result |
|---|---|---|---|---|---|
| learn5-a | Sonnet | 22 | $5.45 | 1 | 4/4 training answers, 0 unresolved, tests pass |
| learn5-b | Sonnet | 24 | $7.09 | 1 | same |
| learn5-c | Sonnet | 23 | $7.85 | 1 | same |
| reconcile v5 | Sonnet | 14 | $3.64 | 2 | same |
| learn5-a-opus | Opus | 29 | $8.38 | 1 | same |
| learn5-b-opus | Opus | 37 | $9.18 | 1 | same |
| learn5-c-opus | Opus | 28 | $7.76 | 1 | same |
| reconcile v5-opus | Opus | 12 | $3.95 | 1 | same |

Learning total $53.28; tests $69.22 (190 sessions); step 5 total $122.50. No usage-limit waits, errors, time-outs or recovered runs.

**How learning went (transcripts and hook logs).** Every learner started from an empty library and worked through the parser's list of unresolved clauses until none was left; the first parse summaries in the transcripts show up to 87% of clauses unresolved (learn5-a), and every session ended at 0. All eight sessions had all four training answers right at their first stop; the only block was the Sonnet reconcile session, which had not yet recorded five disagreement groups (R20-R24). Coverage in learning was complete and enforced by the hook (it re-parses with a pristine framework), not self-certified. The open route is the ignore rule: an ignored clause counts as resolved, and the only check on it is that the training answers stay right. Share of training clauses ignored (final libraries): learn5-a 3.1%, learn5-b 5.8%, learn5-c 3.1%, v5 3.1%; learn5-a-opus 3.2%, learn5-b-opus 3.2%, learn5-c-opus 11.2%, v5-opus 3.2%. Manual entries: 2 to 114 per library (learn5-b 114). Without its manual entries, v5 still leaves 0 training clauses unresolved; v5-opus leaves 1 in each of two documents.

## 3. Why the library arms failed

For each failed G1/GO1 run: re-parse with the session's final library and manual.jsonl, evaluate each query condition separately with the base library's own condition code, and list which condition each missed person fails ([step4/why_missed.py](step4/why_missed.py)). In 19 of 21 failed runs, that code on the session's final parse gives exactly the session's answer, so the session followed the library's reading.

| Cause | G1 | GO1 | Instances |
|---|---|---|---|
| **Query reading: `genuinely` required** ("genuinely prefers train travel to flying"; the key also counts a plain "prefers train to plane") | 5 | 5 | 00011*, 00014, 00031, 00032, 00049 |
| **Query reading: `currently` required on the youth's course** ("guardian of someone currently attending an evening course"; the key also counts "Youth 002 attends evening_pottery during the evening") | 3* | 4* | 00006*, 00027, 00048 (+ 00036 GO1) |
| A fact not extracted (parse) | 0 | 2 | 00016 (volunteering, P-118), 00022 (coastal employer, P-129, P-139) |
| The session's own query was wrong; the code on its final parse was right | 1 | 0 | 00019: answered only the last of four conditions (42 people) |
| Session query and parse both off | 1 | 0 | 00022: 6 extras (public transport) and 1 miss (volunteering) |

\* 00011 also has one dairy miss (P-149) in both arms, and in GO1 P-092 also fails the coastal-employer and fruit conditions; 00006 also has a public-transport miss (P-025) in both arms; 00036 (GO1) is counted under the course reading by the per-condition check, not confirmed by hand.

**Both readings are the literal reading of the query word, and training could not decide either.** All four training documents are answered correctly under the strict and the loose reading (checked with code: both libraries, both readings, all four documents). The two libraries made the same choice independently.
- v5: query helper `require=["genuinely"]` and `require=["currently", "during the evening"]`; NOTES.md: "`prefers` with `genuinely` is a real preference", "`attends_course` (Youth) with `currently`". Dairy got the loose reading again ("`avoids` `dairy products` (`currently` or plain)"), as in step 4.
- v5-opus: training predicates `F.has(f, "over:plane", "genuinely")` and `F.has(c, "time:current")`. Its NOTES.md recipe for the train condition does **not** list `genuinely` ("`prefers_over` `train` with `over:plane`"), and its general rule says "currently X: use `Facts.current()`" (drops past/future/negated). The code is stricter than its own notes.
- In step 4b, the Opus reconcile session took the loose "genuinely" reading with a counterexample from training. This time neither reconcile session did. One learning run per model cannot say why.

## 4. The variant 90017: solved in every run

[step4/score_variant.py](step4/score_variant.py) with `S4_BASE=v5` / `v5-opus`:

| Kind (expected) | Changes | v5 alone | G1 sessions 1/2/3 | v5-opus alone | GO1 sessions 1/2/3 |
|---|---|---|---|---|---|
| 2 new construction (rule) | 22 | 18 unresolved, 4 v5 | rule 17/17/18, manual 1/1/0 | 18 unresolved, 4 v5-opus | rule 17/16/16, manual 0/1/1 |
| 3 free text (manual) | 6 | **6 unresolved, 0 ignored** | rule 6/6/6 | **6 unresolved, 0 ignored** | rule 6/6/6 |
| 4 noise (ignored) | 8 | 7 unresolved | manual 7 each | 7 ignored | 7 ignored |

(1 noise line not located by the scorer, as before. Kind 1 form breaks: [data/step5_variant_triage.txt](data/step5_variant_triage.txt).)

In steps 4 and 4b the decisive free-text lines were taken by an over-broad ignore rule, so the stop hook never showed them. In step 5 neither library ignored any free-text change: they stayed unresolved, every session wrote a rule for each, and all six runs were exact. The ignore rules now guard against names:
- v5 `NoFactRule`: only a whole-clause match on one of its filler frames, and only if the clause names no person or ID (full names, initial forms, first names, `Y`/`Youth` numbers);
- v5-opus `narration`: no quotation, no name slot, not a he/she/they + verb sentence, and no fact rule reads it.

Nothing in the prompts asked for this. Whether the fourth training document or chance made the difference cannot be told from one learning run per model.

## 5. The libraries alone, with no model (code only)

[step4/library_only.py](step4/library_only.py): parse each instance with the library as the learners left it (no manual.jsonl), then answer its query with the library's own condition code from training. The nine condition sentences are identical in every query, so a nine-line table maps each one to the library's predicate for it; the only edit to the learners' code is that v5's `answer()` takes a condition list instead of a training-document number. About 5 s per instance, $0.

| | Exact (46) | Instances with 0 unresolved clauses |
|---|---|---|
| **v5 code alone** | **34** | 0 |
| v5-opus code alone | 29 | 0 |
| G1 sessions (v5 + Sonnet) | 36 | (every session resolved all) |
| GO1 sessions (v5-opus + Sonnet) | 35 | (every session resolved all) |
| N1 (plain Claude Code) | 27 | - |

- No instance is fully covered: 6 to 55 unresolved clauses per instance under v5, 6 to 65 under v5-opus. They are mostly one-off wordings that no condition needs (quote fragments such as "NAME adds", narrator remarks such as "I passed the title along"); a few are relevant ("NAME prefers train to plane.", "NAME likes train and plane equally ...").
- The answers are still right in 34 of 46 (v5): what is unresolved rarely matters for the query. Every code-only error is a miss; neither library includes a wrong person.
- The sessions add 2 instances to v5's code and 6 to v5-opus's, at $0.33 and $0.58 per instance. Every G1 and GO1 session added new parts (46/46 each), so "0 unresolved" was reached by work on every instance.
- **Counterfactuals (labelled; not results):** without the `genuinely` requirement, v5 code alone gets 38/46 and v5-opus 33/46; without the `currently` requirement on the youth's course as well, 40/46 and 35/46. Still wrong for v5 then: 00005, 00006, 00011, 00013, 00022, 00023.

## 6. Harness notes

- **The hook fix worked.** The stop hook received the workspace path; no "library does not load" error in any of the 98 G1/GO1 runs. It never blocked at the first stop: every session had resolved every clause and passed the tests before stopping.
- No run read an answer key or the hook's state folder (`key_access` and `ledger_access` false in all 190).
- G1 00019: the session parsed everything, then wrote a query for only the last condition and answered 42 people. The library's code on the session's own parse gives the right 5.

## 7. Next to the paper's Constraint results (rough; not like-for-like)

Paper Table 2 (50 instances, one run): GLM-5.3 + mini-swe-agent 66% ($1.55), the best; GPT-5.6-sol Direct 58% ($0.690), OpenCode 56% ($1.72). Here, on 46 of the 50: N1 59% ($0.21), G1 78% ($0.33 per session; with learning spread over the 46, about $0.85), v5 code alone 74% ($0 per instance after the $24 learning). Different model; the four training instances are left out; G and the code had pass/fail feedback on four labelled documents during learning, which the paper's harnesses do not get.

## 8. What this suggests (Claude's reading; Zili Luo decides)

- **What transfers well is structure; what transfers wrongly is interpretation.** The parsing learned from four documents carried to 46 new ones: 34 exact with no model at all. Every systematic library error in steps 4 to 5 was a judgment about meaning: an emphasis word read as a requirement ("genuinely"), a time word read as a requirement ("currently"), or (steps 4, 4b) a "carries no fact" rule that was too broad. These are the parts of the library the model wrote freely, with no definition to check against.
- **The model in the test session mostly followed the library.** In 19 of 21 failures the session's answer is what the library's own reading gives. The sessions fixed coverage (they resolved every clause), not readings.
- **Plan-first did nothing on 46 instances** (28 vs 27). Step 4's P lead (15 vs 9 runs on 7 instances) did not hold. Changing how the problem was posed (learn the documents' language once, then query it) helped; asking the model to plan did not.
- **Opus as learner: no gain this time** (35 vs 36; they differ on 3 instances). Its library is weaker as code (29 vs 34) and its sessions cost more ($0.58 vs $0.33), because they had more to fix. Step 4b's Opus gain came from one reconcile decision that was not repeated.
- **The cost point.** On this task the reusable part is code that runs for free. A cascade (run the code; call a model only for unresolved clauses that touch the query's people or conditions) would cost a fraction of a session per instance. How many instances it could close without a model, and whether those are right, can be measured from these files.

## 9. Limits and directions

- One run per instance per arm; one learning run per model. The paired tests are borderline at 46 instances, and the Constraint task has only 50.
- The benchmark's statements are generated from templates. What the learners recovered is the generator's grammar, not English; the variant (6 free-text lines) is the only probe beyond it.
- "Grammar" is defined here only by its shape (clauses → facts with a relation and qualifiers). What a qualifier means is left to the model. Typed qualifiers from linguistics (whether a word changes the truth of the statement: emphasis does not, negation and tense do; e.g. FactBank's factuality values) would decide "genuinely" in a principled way, but that is added domain knowledge, a separate experiment, not a harness result.
- The harness question this leaves (Zili Luo's framing): the gain came from the problem being posed differently, not from more checking or planning. Can a harness make the model first widen (several ways to pose the task: answer directly; answer and check; build a reusable parser) and then choose by the workload (one instance or thousands; how much the inputs vary; what an error costs)? To check against prior work first: Self-Discover (Zhou et al., 2024), LLMs as Tool Makers (Cai et al., 2023), Voyager-style skill libraries.
