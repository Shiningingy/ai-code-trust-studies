# Study 02 analysis plan, fixed before any F→P label exists

**Status: frozen 2026-11-02 after Allen's read, before any label existed. The hash is in the Launch log.**

Written 2026-11-02. No F→P label exists for any Sonnet output, and no rewrite arm has been compared with anything. The only distances seen are on repeat pairs (baseline, repeat1, repeat2), for the runtime check below. Everything here is settled by this text; `scoring/analyze.py` carries it out. Anything added after labels exist is exploratory and labelled so.

**Data.** Runs in `runs/<arm>/` with a done marker, 130 bugs, 5 arms, 647 tests. Never used: `runs/baseline-original-prompt`, `runs/old-retry-label`, `runs/forced-test`, `runs/repeat1/rejected/`, `rewrites-v1-discarded`.

**Label.** A test is right if SWT-Bench lists its bug in `resolved_ids`, otherwise wrong. This is the label the pretest used and the one behind AssertFlip's published figures. It is stricter than plain F→P: the test must go fail-to-pass and must add no new failing test. The spec says "F→P" loosely, so the report must say which is meant. Reported beside it, unable to change a verdict: `added_f2p > 0` from `report.json`. Harness settings: unit test mode, the authors' `generate_preds_phases.py` path map, default coverage and timeout. Tests are judged on baseline only for RQ1 and RQ2.

**A test the harness cannot run** (listed in `error_ids`, no output) gets one retry. If it still has no result it is left out and reported by bug and arm. Any such baseline test is also counted as wrong in one sensitivity line. A test that ran and failed to apply or crashed is simply wrong.

**Score.** `score(baseline, others)` from `pretest/disagreement.py`, sha256 `240514266ec6fc39`, unchanged: mean definition-B distance from the baseline test to each other test.

- Rewrite score: others = paraphrase, stepwise.
- Repeat score: others = repeat1, repeat2.

**The runtime half of B is secondary, not primary.** The primary score is the static half, the only form the pretest tested. On the 388 repeat pairs, the failure text matched exactly in 181 pairs, and among the 91 pairs with static distance at or below 0.25, 31 did not match. Of 10 of those read by hand, about six were the same failure phrased differently (`<class 'tuple'> != <class 'list'>` against `is not`) or arbitrary values (`{'foo': 'bar'}` against `{'attr_1': ...}`), and about four really differ (`TypeError` against `AssertionError`), two of them on one bug. Median distance rose from 0.444 to 0.476. So exact failure text carries some real difference, but more assertion style than signal, and it has never been tested against labels. The secondary score feeds one normalised line from `pipeline/failure_values.py` through the existing `Run.failure` field. `disagreement.py` is not edited, so its hash stands. This departs from the Launch log's "the failing assertion's values join that set", and the report says so.

**Silent run.** `sympy-17318` in repeat1: the mean is taken over emitted tests, as in the pretest, so that bug's repeat score uses repeat2 alone. Sensitivity line: count the silent run as distance 1.

**`django-14580`.** It has no rewrite arms, so it is out of RQ1, RQ2 and RQ3, which all run on 129 bugs. One sensitivity line gives repeat-only results on all 130.

**Agree and disagree.** Median of the 129 baseline rewrite scores, set without labels. Agree is a score at or below the median, disagree is above it, as in the pretest. The repeat score and each comparator use their own median, the same way.

**RQ1, primary test.** Precision in agree against precision in disagree, Fisher's exact test, two-sided, 0.05.

- **Signal:** p below 0.05 with precision higher in agree.
- **Reversed:** p below 0.05 with precision higher in disagree. Reported as that.
- **No large effect:** p at or above 0.05. This is not "no effect". At 129 bugs a 30-point gap is detected about 92% to 100% of the time across plausible precision, a 20-point gap only about 58% to 91%, so a null rules out a large gap and says little about a modest one.
- **Inconclusive:** fewer than 20 wrong or fewer than 20 right tests among the 129. With a split near 65/64 a 30-point gap needs about 20 tests of the smaller class, so below that the gap the study was sized for cannot occur.

Fisher ignores repo, which strongly predicts F→P. **Secondary:** AUROC for wrong tests, stratified by repo, bootstrap within repo, 5,000 draws, seed 20261101, as in the pretest. If Fisher shows a signal but this interval includes 0.50, report that the signal may be a repo effect.

**RQ2.** Repo-stratified AUROC of the rewrite score minus that of the repeat score, on the same 129 bugs, with a paired 95% bootstrap interval (same draws for both, same seed).

- **Rewrites stronger:** lower bound above 0.
- **Repeats stronger:** upper bound below 0.
- **Otherwise, not shown stronger.** If the point estimate is at or below 0, also say plain re-running did as well here, so rephrasing earned nothing.

The precision split for repeats is shown beside it. AUROC is the test because it uses every bug and not one cut. This interval will be wide at 129 bugs, and a small difference cannot be seen.

**RQ3.** No test. Discarding the disagree group: precision before and after with counts and 95% Wilson intervals, tests kept, and correct tests lost as a count and a share of all correct tests. Same line for repeats and for text distance. A user who discarded half at random would gain nothing, so the gain is read against zero.

**Reported, cannot change a verdict.**

1. Plain text distance beside the rewrite score throughout, as in the pretest: 1 − difflib ratio on source with comments removed, to the same two tests, with split, AUROC and the paired difference from the rewrite score. If it does as well, say so.
2. The runtime-half score, the same way.
3. Repo-by-size-tercile stratified AUROC, and size alone, per-repo AUROC.
4. The sensitivity lines above.
5. Right rate per arm. Descriptive only: this study does not ask whether rewrites make better tests.

**Hand read.** Before trusting any rate, read 3 tests from each of the four cells (right or wrong, agree or disagree), seeded with 20261101, with their issue and failure. A finding here is reported. It does not change a label, a test, the harness or the scorer.

**What this cannot show.**

- Agreement cannot catch an error every run repeats.
- Disagreement means runs differ, not that the baseline is the wrong one.
- No hand-labelled failure kinds, so it shows whether the signal works, not why.
- Any look at why is exploratory and labelled so. Scoring adds no slices. One analysis.
