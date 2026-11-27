# Study 06 follow-up: from a coverage check to a learned grammar (2026-11-25 to 11-27)

Follow-up to [Study 06](../README.md), on LongHarness Bench (Pham, Nguyen, Chen and Ye, 2026), Constraint Solving Search. Zili Luo designed the steps and made every decision; Claude Code ran the sessions and drafted the analysis. Each step's design was frozen in [plan.md](plan.md) before its runs. All runs: Claude Code 2.1.289, clean mode, tools Read/Grep/Glob/Bash, on a subscription (costs are Claude Code's list-price figures). **Not peer reviewed; one person's study.**

## The question

Study 06 found that every wrong answer was a missed person, and that an agent can be pushed to full coverage only at about 3.5 times the cost. The benchmark reports cost next to accuracy, and solving the task fully and cheaply is the hard part. So the follow-up asks: what makes a harness solve this task fully, at what cost, and what carries over to new instances?

## Steps

| Step | What changed | Result | Write-up |
|---|---|---|---|
| 1, 1b, 1c | Plans only, Opus 5.5 | No plan had the full recall step unprompted (5 of 6 partial: a near-miss re-read); 12/12 planned it once the gap was named | [results-step1.md](results-step1.md) |
| 2 | Execute own plans with pass/fail feedback; a step-by-step critic | 36/36 passed in the end, 30 on the first answer; full coverage was planned often and executed in 1 of 44 attempts; the critic cost 2 to 5 times as much | [results-step2.md](results-step2.md) |
| 3 | A harder instance; "one final answer" sentence | The sentence changed plans, not execution (11/18 vs 11/18) | [results-step3.md](results-step3.md) |
| Ledger | Which lines the model actually saw | 6-20% of sentences in every arm; all 12 trap misses were lines never shown to the model (0 misses of 22 shown) | [results-ledger.md](results-ledger.md) |
| 4 | A learned grammar library: three learner sessions write parsing code on three labelled documents, a fourth reconciles them; test sessions start from that library, and a stop hook checks that every clause is parsed or explicitly ignored | First answers on 7 unseen instances × 3: library 18/21, plan-first 15/21, plain 9/21 | [results-step4.md](results-step4.md) |
| 4b | The same learning run by Opus 5.5 | 21/21; the gain came from one reconcile decision | [results-step4b.md](results-step4b.md) |
| 5 | Four training documents (all 9 conditions); the other 46 instances, one run each | Library (Sonnet-learned) 36/46, (Opus-learned) 35/46, plan-first 28/46, plain 27/46; **the library code alone, with no model, 34/46** | [results-step5.md](results-step5.md) |

## Main findings (Claude's reading; Zili Luo decides)

1. **The gain came from posing the problem differently, not from more checking.** A plan-first sentence did nothing on 46 instances (28 vs 27). A critic cost more without finding more. What helped was turning "search this document" into "learn the language these documents are written in, then query it".
2. **Structure transfers; interpretation does not.** Parsing code learned from four documents answered 34 of 46 new instances exactly with no model at all, at no cost per instance. Every systematic error in steps 4 to 5 was a judgment about meaning that the model wrote freely: an emphasis word read as a requirement ("genuinely prefers"), a time word read as a requirement ("currently attending"), or a "this carries no fact" rule that was too broad. The training documents could not tell the readings apart, and the test sessions followed the library's reading in 19 of 21 failures.
3. **Every error, in every arm and step, is mostly a miss, not a wrong inclusion**, as in Study 06.
4. **A cascade is the cheap way to solve it fully.** No instance was fully covered by the code (6 to 65 unresolved clauses each), but the unresolved clauses rarely matter for the query. Run the code; call a model only for clauses that touch the query. Not yet measured.

## Limits

- One run per instance in step 5, one learning run per model, 46 instances: the library's lead over the plain agent is borderline (paired exact test p = 0.049 for the Sonnet-learned library, 0.096 for the Opus-learned one).
- The benchmark's statements come from templates; the learners recovered that generator's grammar, not English. One variant with six free-text lines is the only probe beyond it.
- The library arms had pass/fail feedback on four labelled documents during learning; the paper's harnesses get no labels. Different model from the paper.

## Open direction

The harness question this leaves: can a harness make a model first widen (several ways to pose a task: answer directly, answer and check, build a reusable parser), then choose by the workload (one instance or thousands; how much inputs vary; what an error costs)? On a one-off instance, answer-and-check is enough; on thousands a day, the reusable parser plus a cascade is cheaper and more accurate. Related work to compare with: Self-Discover (Zhou et al., 2024), Large Language Models as Tool Makers (Cai et al., 2023), skill libraries as in Voyager (Wang et al., 2023).
