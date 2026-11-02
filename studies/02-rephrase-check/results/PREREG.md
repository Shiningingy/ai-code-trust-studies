# Pretest plan, fixed before reading any F→P label

Written 2026-11-01, after the scorer's tests passed and before `run_pretest.py` touched `evaluation_results_on_SWT_Bench`. Only the prediction files had been read.

**Question.** On the authors' own runs, does the scorer's disagreement predict that an accepted baseline test is wrong? If it shows nothing, rethink before spending any usage.

**Data.** Authors' repo at commit `a5cd619`. Baseline: `assertflip-default-preds.jsonl`, 326 accepted tests. Other runs: perfect localization, no planner, no validator, 5 regenerations. Label: wrong = the bug is in `unresolved_ids` of `assertFlip_default_run.json`. Variant labels are never used.

**Primary score.** `score(baseline, others)`: mean definition-B distance from the baseline test to each other run's test, over the runs that emitted one. Tests with no other emitted run are dropped from the primary test and counted.

**Primary test.** AUROC for wrong tests, stratified by repository (only wrong/right pairs within one repo count), because repo strongly predicts F→P. 95% CI by bootstrap within repo, 5,000 draws, seed 20261101.

**Gate.** PASS if the lower CI bound is above 0.50. Otherwise FAIL: stop and rethink before Docker.

**Reported, cannot change the gate.**

1. Median split, set without labels: precision in the agree and disagree groups, Fisher's exact test, and correct tests lost.
2. Unstratified AUROC.
3. Each other run alone, and the mean over all six pairs of runs, as the nearest match to two rewrites.
4. Stratified by repo and test size together (size = token count, terciles).
5. Comparators: number of silent runs, the primary score with a silent run counted as distance 1, and plain text distance (1 − difflib ratio on source with comments removed). If a simpler signal does as well, say so.

**What this cannot show.**

- Only the static half of B. The public package has no failure output, so expected values come from the source and actual values are missing.
- The other runs differ in configuration, not in issue wording, so this is not evidence about rephrasing.
- 5 regenerations is the nearest thing to a repeat run, but it is one run, so RQ2 is untouched.
- The model is GPT-4o, not Sonnet 5.5.
- A PASS justifies spending on the pilot. It does not show the study will work.

**Threshold for the main study.** Not set here. The agree/disagree cut in the main study will be the median of that study's own baseline scores, set without labels.
