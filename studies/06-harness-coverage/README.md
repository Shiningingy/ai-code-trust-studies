# Study 06: does a coverage check help a harness find everyone?

A small check on LongHarness Bench (Pham, Nguyen, Chen and Ye, arXiv 2609.38137, 2026), Constraint Solving Search (§3.1), using the benchmark's two public examples. It asks what a harness adds to a model, and whether instructions are still a lever on the result.

**Status: small check, done 2026-11-20, not peer reviewed.** 16 scored runs and 2 plan-only runs, all with Claude Sonnet 5.5 (`claude-sonnet-5-5`) in Claude Code 2.1.289. Three runs per example for the two main arms; one run for the others. The results describe patterns, not rates. **Report: [report.pdf](report.pdf)** (question, design, results, discussion, limits, conclusion, open directions).

## The task

Each example is one Markdown file of about 470 KB (~120K tokens). It holds roughly 2,400 short passages about 160 people, ending with a query of three to five conditions ("works for an organization based in a coastal city", "ordinarily travels using public transportation", …). Exactly five people qualify. Facts are scattered across passages and written with traps:
- name variants ("N. Tran", "nadia Tran")
- tense ("plans to use the bus in the future", "in a former role")
- quoted speech (`N. Tran continued, "I currently chooses to avoid dairy products …"`)

A run is correct only if it returns the exact set of five IDs.

## How it went, step by step

1. **Plans first** ([plans/](plans/)). The model was asked for its plan, without answering, in two settings:
   - **Direct** (whole file in the prompt, no tools, $0.86): planned from the real data and named its real traps.
   - **Claude Code** ($0.03): looked at about 0.6% of the file (the first and last 1,500 bytes) and planned a regex/script pipeline.

   Both plans verify the people they find. Neither has a step for the lines they never parse. A person solving it by hand (the author) would build the tables the same way, but would then look at every line the extraction did not place. That is the recall step.
2. **Full runs**, comparing Direct (D) and Claude Code (H). Then two arms that add the recall step:
   - **HC:** the instruction "account for every line"
   - **HV:** the agent must write `check_coverage.py`, which splits the file into statements, labels each placed / irrelevant / unaccounted, and fails if any is unaccounted. The agent may answer only after the check passes.

## Result in short

| Arm | Runs | Exact | People found | Wrong inclusions | Mean cost per run |
|---|---|---|---|---|---|
| D: Direct | 2 | 0/2 | 6/10 | 0 | $0.88 |
| H: Claude Code | 6 | 3/6 | 25/30 | 0 | $0.14 |
| HC: + "account for every line" | 2 | 1/2 | 9/10 | 0 | $0.26 |
| HV: + coverage check that must pass | 6 | **6/6** | **30/30** | 0 | $0.48 |

- **Every error in every arm is a missed person.** No run included a wrong one.
- **HC was followed only in part.** Its trace counts the sentences containing its own keywords (work, dairy, travel, …), not every line. It still missed one person whose facts use all three traps (alias, lowercase, quoted speech with "continued").
- **HV was exact in 6 of 6**, against 3 of 6 for H, at about 3.5 times H's cost ($0.482 vs $0.139 per run) and about half of Direct's.

## Auditing the check (HV)

The agent wrote the check itself, so the six scripts ([gate-scripts/](gate-scripts/)) and every check result in the traces ([results/scores.txt](results/scores.txt)) were read:

- **The agent defines the unit.** The same two files were split into 10,132 to 13,307 "statements".
- **Most statements are irrelevant by rule.** In 5 of 6 scripts, any statement without the agent's own keywords is irrelevant. Across the six runs, 93-97% of statements end up irrelevant. One script labels these "(reviewed)", although nothing reviewed them. The sixth uses pattern lists with catch-alls, such as any statement containing "said".
- **A failed check was always passed by relabelling.** The first check failed in 3 of 6 runs (9, 24 and 8 statements unaccounted). In all three, the next passing check had more statements marked irrelevant and **the same number placed** (512, 773, 609). The answers were still right, so those statements were in fact irrelevant here. But the check never once led to more extraction.

So the check helped a great deal, but it is not independent verification. It was written by the same agent as the extractor, and it shares the extractor's blind spot (the keyword list) and its incentive (to pass). A fact phrased with none of the keywords would pass as irrelevant. The benchmark's templated wording kept that from happening here.

## Limits

- One model, one harness (Claude Code), two instances, one task. The arms vary the **instructions** within one harness; they do not compare harnesses.
- Three runs per example for H and HV, one for D and HC. D used Claude Code's CLI with tools off and a one-line system prompt, which approximates direct inference rather than a raw API call.
- The recall step came from the author reading the task. Whether it transfers to tasks where coverage is not the bottleneck is untested.
- Training-data exposure: the benchmark was posted on 2026-09-29. The model's training cutoff is not known here. No output mentions the benchmark's name (grep).

## Open directions

- **Learning the check.** Here the useful check came from a person who read the task. If the data changes, an imposed check may no longer fit. Can a harness learn from its own runs which checks a task needs?
- **A check the agent cannot relabel past.** A check written and graded by the same agent can be passed by relabelling. That is a small case of reward hacking.
- **Fewer rounds.** In real tasks every check costs something (Study 05's decisive check was a 13-17-minute test suite). The aim is the fewest checks that make the answer correct, close to the paper's own aim of harnesses that "use additional compute selectively and productively" (§6).

## Layout

- [report.pdf](report.pdf): the study report.
- [plans/](plans/): the two plans, verbatim (and, for Claude Code, the tool calls it made before planning).
- [results/scores.txt](results/scores.txt): per-run scores, per-arm summary, and every coverage-check result in the order the agent ran them.
- [gate-scripts/](gate-scripts/): the scripts the agent wrote in each HV run (`check_coverage.py`, `extract.py`, …), unchanged.
- [scripts/](scripts/):
  - `run.sh`: one run of an arm
  - `plan.sh`: the plan-only step
  - `score.py`: our scorer; the benchmark's own `score.py` was not run

Run transcripts are not in the repository, because they quote the benchmark's text. The benchmark's data is not copied here either; get it from the source below.

## Running it

Data: github.com/stringnlplab/longharness at commit `6e3da81` (2026-09-30), `tasks/constraint-solving-search/{contexts,answers}/sample-0000{0,1}.*`. SHA-256:
- `contexts/sample-00000.md` 236d0554…dc3e
- `contexts/sample-00001.md` 0c600f25…bc0
- `answers/sample-00000.json` 45e149b6…983e
- `answers/sample-00001.json` 9130cf0b…6b6e

Put them in `$LHB_DATA/contexts` and `$LHB_DATA/answers`, outside every run folder. Runs go through `claude -p` on a Claude subscription, with `--safe-mode`, in neutral empty folders under `$LHB_WORK`.

```
bash scripts/plan.sh PD; bash scripts/plan.sh PH
for rep in 1 2 3; do for s in 00000 00001; do bash scripts/run.sh H $s $rep; bash scripts/run.sh HV $s $rep; done; done
bash scripts/run.sh D 00000 1; bash scripts/run.sh D 00001 1; bash scripts/run.sh HC 00000 1; bash scripts/run.sh HC 00001 1
python -I scripts/score.py runs $LHB_DATA
```

## Who did what

The questions, the comparison with a human plan, the recall step, and the idea of making the agent write and pass a coverage check are the author's. Claude Code wrote and ran the scripts, read the traces and the agent-written checks, and drafted this README under his direction.
