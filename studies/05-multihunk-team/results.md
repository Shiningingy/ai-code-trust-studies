# Study 05 results: sub-agents on two multi-hunk bugs that no agent in the paper fixed

**Status: runs complete (2026-11-19 02:38).** 30 counted Sonnet 4.5 runs plus the smoke run. Astropy-7606: 12 of 12 repaired (frozen S/T/U 9/9, arm L 3/3), all `repair_strict` 0 because of the grading artefact in §1(a). Closure_157: 2 of 18 repaired (frozen S 0/3, T 1/3, U 0/3; follow-up arms L 0/3, H 0/3, F 1/3). Hand coding and any further runs are Zili Luo's decisions. Plan: [plan.md](plan.md) (frozen 2026-11-18, Amendment 1 the same night). Counted runs use Sonnet 4.5 (`claude-sonnet-4-5-20250929`, the paper's model) on Claude Code 2.1.289. The first Sonnet 5.5 runs are kept as a labelled pilot, not counted. All run data: `E:\study05\runs\` (4.5 under `sonnet-4-5\`). Hand coding (coding-scheme.md) has not started; it is Zili Luo's.

## 1. Pre-run checks

### (a) Astropy-7606: "unsolved" in the paper is a grading artefact

Before any agent run, Claude Code (Opus 5.5, setting up the harness) ran the developer's gold patch through the paper's pinned image and graded it with the official SWE-bench code (swebench 4.1.0 `get_logs_eval` + `get_eval_tests_report`, the paper's grader `hunk-swe/swe_bench_utils/grader.py` calls the same harness).

| Tree | Official verdict | Failed count (F2P + P2P) |
|---|---|---|
| unfixed (test_patch only) | RESOLVED_NO | 2 |
| gold patch | **RESOLVED_NO** | **1** (`test_compose_roundtrip[]`) |
| each of the paper's four agents (`hunk-poly/*/*_repair_ability.csv`) | not repaired | 1 |

The record's PASS_TO_PASS list names `test_compose_roundtrip[]`; pytest in the pinned image prints `test_compose_roundtrip[unit0]`. SWE-bench counts a test missing from the log as failed, so even the gold patch is "not resolved". The paper's four agents all have exactly the gold patch's failed count, so each made `test_unknown_unit3` pass with no regression and was scored unresolved by the name mismatch alone. Their patches are not published, so this is the tests' verdict, not a reading of their code. Evidence: `E:\study05\precheck\swebench-official\` (`official_grade.py`, `output.txt`).

This study reports both verdicts: `repair` (the case matched by its printed name; primary, D2) and `repair_strict` (SWE-bench's rule, comparable with the paper).

**The planned swap, Astropy-8707, does not reproduce either.** In its pinned image every `TestHeaderFunctions` test errors in setup (pytest 7 turns nose-style `setup(self)` into an error), so the gold patch gets failed count 8, the same as the unfixed tree; official swebench 4.1.0 gives RESOLVED_NO for gold (`E:\study05\precheck\swebench-official-8707\`). The paper's Claude, Codex and Gemini also show 8. So 7606 was kept and flagged.

### (b) The benchmark issue was already reported and fixed upstream

How it was found: the harness set-up found it first, by grading the gold patch (above). Only afterwards did we search GitHub and find it had been reported and fixed. The model doing the set-up may have seen these reports in training, so this is not a blind discovery; what the check shows is that validating the gold patch in the pinned environment exposes it within minutes.

| SWE-bench/SWE-bench | Opened | Closed | What |
|---|---|---|---|
| [#223](https://github.com/SWE-bench/SWE-bench/issues/223) | 2024-09-25 | 2024-10-24 | "nonexistent PASS_TO_PASS test in dataset for astropy__astropy-7606" |
| [#267](https://github.com/SWE-bench/SWE-bench/issues/267) | 2024-11-30 | 2026-08-14 | "5 Instances in Verified Fail for Gold Patch" (7606 and 8707 among them); closed with "500 of 500 on current main" |
| [#341](https://github.com/SWE-bench/SWE-bench/issues/341) | 2025-02-27 | 2025-03-02 | "Task astropy__astropy-7606 Incorrectly Marked as Unresolved" |
| [#342](https://github.com/SWE-bench/SWE-bench/issues/342) | 2025-02-27 | 2026-08-14 | 8707 test set-up failure, found by reading eight top agents' evaluation logs |
| [#530](https://github.com/SWE-bench/SWE-bench/issues/530) | 2026-03-11 | 2026-08-14 | nose tests make `run_evaluation` give the wrong result for 8707 |
| [PR #535](https://github.com/SWE-bench/SWE-bench/pull/535) | 2026-03-11 | 2026-08-10 | dataset fix: 7606 P2P `[]` → `[unit0]` (closed, not merged) |
| [PR #596](https://github.com/SWE-bench/SWE-bench/pull/596) | 2026-06-10 | 2026-08-02 | disable the nose plugin for the Astropy eval harness, fixes #530 (closed, not merged) |

The reporters found the problems by hand (validating gold patches, reading leaderboard evaluation logs); coding agents appear only as authors of the two fix PRs. The first 7606 report predates the paper (arXiv 2511.11012, November 2025) by more than a year.

We used the same benchmark versions as the paper, not the fixed ones: the paper's image digests from its `image_manifest.json`, and the SWE-bench records from the package's own `swe_bench.jsonl`.

### (c) Closure_157: the paper's Claude run read the fixed version from git history

The package's command log for that run (`hunk4j-results/results/claude_code_results/claude_results/tools_count_claude.csv`, lines 1303-1309) contains `git log --oneline | grep "D4J_Closure_157"`, `git diff 3ff39c0b 822acb61 -- …/CodeGenerator.java`, the same for `IRFactory.java`, `git show 822acb61:…/IRFactory.java`, and a checkout of the fixed commit. Our trees have a fresh one-commit history, so our Closure runs are harder than the paper's.

### (d) The class-name hint and the fix data in the container

- `defects4j.build.properties` names the three modified classes. Hiding the file breaks `defects4j compile`/`test`/`export`, so the two keys are kept with empty values during the run and restored for grading (D6). Re-verified after the change: unfixed tree compiled, failed_after 12; developer fix compiled, failed_after 0, repair 1, RR 12, localization 1 (`E:\study05\verify\Closure_157\verify.json`).
- The Defects4J image itself holds the developer's fix (`framework/projects/Closure/patches/`, class lists, the upstream `closure-compiler.git`). For the 4.5 runs these are hidden by empty read-only mounts in the agent's container only (Amendment 1). The 5.5 pilot's Closure run had them readable; its 19 `run` commands contain no access to them.

## 2. Training-data exposure

Three checks, made after the first Sonnet 5.5 runs looked easy (Amendment 1):

1. **Memory probe** (no repository, no tools, `E:\study05\runs\probes\probes.json`). Sonnet 5.5 recalled the Astropy-7606 gold patch almost line for line (`return NotImplemented`, `isinstance(other, type(self))`) and guessed 2 of Closure_157's 3 files (`IRFactory`, `CodeGenerator`). Sonnet 4.5 recalled neither fix. Sonnet 4.5 is still served on this account (one-word call, init model `claude-sonnet-4-5-20250929`).
2. **Patch similarity to gold** (`scripts/similarity.py`, `E:\study05\runs\similarity.json`). All 20 Astropy patches (both models) are the same one-hunk change: wrap `Unit(other)` in `UnrecognizedUnit.__eq__` in try/except and `return False`. None contains the gold's `NotImplemented` or `type(self)` lines, and none touches the gold's second hunk (`UnitBase.__eq__`). So even 5.5, which can recite the gold patch, did not use it. Closure: the Sonnet 4.5 patches share 9-17% of the developer fix's added lines (T1, the one repair: 9%; its `RenamePrototypes` change adds an `isNumericKey` helper where the developer switched to `TokenStream.isJSIdentifier`), the 5.5 pilot 26%. (A first version of the check compared against the buggy side of Defects4J's stored fixed → buggy patch; corrected in Amendment 3.)
3. **Leak paths and leak words.** Fix data hidden for 4.5 (above). Every transcript was scanned for the leak words; the only hits are the CLI's own slash-command list in the init event (`team-onboarding`) and chance matches inside base64 thinking signatures (`team`, once `HUNK4j`). No hit in any prompt or init cwd.

The risk is named, not removed: both developer fixes were public in their upstream repositories long before Sonnet 4.5 was trained, and so were the 2024 SWE-bench reports on 7606, so its failure to recall the fixes does not prove they were not in its data. It only shows the fixes are not readily recalled.

## 3. Runs

Counted runs: Sonnet 4.5. Pilot: Sonnet 5.5 (not counted). `repair` = printed-name verdict; `repair_strict` = SWE-bench's rule (Astropy only). Tokens = the CLI's `modelUsage` (whole run, sub-agents included). Five-hour and weekly readings are the CLI's `rate_limit_event`, in whole percent, read before and after each run; runs from two processes overlapped once on the first night (the 5.5 Closure pilot and the first 4.5 runs), so those readings mix both.

| Model | Bug | Arm | Run | Status | Loc | Comp | Repair | Repair strict | Failed after | RR | Tokens in / cache-create / cache-read / out | Min | 5h before→after | Week before→after | Sub-agents | class_graph calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4.5 | Astropy-7606 | S | smoke | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 185/42,962/558,076/6,014 | 3.0 | 13%→15% | 30%→30% | 0 | - |
| 4.5 | Astropy-7606 | S | run1 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 137/31,271/363,298/3,920 | 1.9 | 15%→16% | 30%→30% | 0 | - |
| 4.5 | Astropy-7606 | T | run1 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 219/52,378/504,116/6,397 | 2.6 | 16%→17% | 30%→31% | 1 | - |
| 4.5 | Astropy-7606 | U | run1 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 179/48,054/358,412/6,838 | 2.5 | 17%→18% | 31%→31% | 1 | 0 |
| 4.5 | Astropy-7606 | T | run2 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 173/37,513/374,853/5,390 | 2.0 | 18%→18% | 31%→31% | 1 | - |
| 4.5 | Astropy-7606 | U | run2 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 171/33,321/383,713/6,025 | 2.3 | 18%→19% | 31%→31% | 1 | 0 |
| 4.5 | Astropy-7606 | S | run2 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 153/25,583/272,214/4,652 | 1.7 | 19%→20% | 31%→31% | 0 | - |
| 4.5 | Astropy-7606 | U | run3 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 179/27,946/391,873/6,368 | 2.5 | 20%→20% | 31%→31% | 1 | 0 |
| 4.5 | Astropy-7606 | S | run3 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 153/18,828/354,006/5,106 | 1.9 | 20%→21% | 31%→31% | 0 | - |
| 4.5 | Astropy-7606 | T | run3 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 147/32,024/294,283/5,842 | 2.1 | 21%→21% | 31%→31% | 1 | - |
| 4.5 | Astropy-7606 | L | run1 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 179/46,571/418,301/6,215 | 2.2 | 6%→7% | 37%→37% | 1 | 0 |
| 4.5 | Astropy-7606 | L | run2 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 157/35,413/362,098/5,302 | 2.0 | 7%→8% | 37%→37% | 1 | 0 |
| 4.5 | Astropy-7606 | L | run3 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 179/34,548/395,020/6,736 | 2.3 | 8%→9% | 37%→37% | 1 | 0 |
| 4.5 | Closure_157 | S | run1 | ok | 0 | 1 | 0 | - | 2 | 10 | 849/122,628/9,281,317/28,340 | 42.6 | 21%→25% | 31%→31% | 0 | - |
| 4.5 | Closure_157 | T | run1 | ok | 1 | 1 | 1 | - | 0 | 12 | 1,151/256,574/8,458,587/57,256 | 53.2 | 25%→1% | 31%→32% | 7 | - |
| 4.5 | Closure_157 | U | run1 | ok | 0 | 1 | 0 | - | 2 | 10 | 1,721/241,510/8,342,163/72,199 | 93.5 | 1%→8% | 32%→32% | 4 | 0 |
| 4.5 | Closure_157 | T | run2 | ok | 0 | 1 | 0 | - | 4 | 8 | 1,517/215,412/8,618,948/67,547 | 60.8 | 8%→15% | 32%→33% | 2 | - |
| 4.5 | Closure_157 | U | run2 | ok | 0 | 1 | 0 | - | 2 | 10 | 2,117/430,560/10,143,155/90,888 | 85.7 | 15%→31% | 33%→34% | 5 | 0 |
| 4.5 | Closure_157 | S | run2 | ok | 0 | 1 | 0 | - | 17 | -5 | 1,249/120,483/11,269,916/42,243 | 49.9 | 31%→7% | 34%→34% | 0 | - |
| 4.5 | Closure_157 | U | run3 | ok | 0 | 1 | 0 | - | 11 | 1 | 4,293/1,028,327/20,266,589/169,689 | 170.8 | 7%→38% | 34%→36% | 10 | 0 |
| 4.5 | Closure_157 | S | run3 | ok | 0 | 1 | 0 | - | 2 | 10 | 841/121,239/8,399,608/39,321 | 76.2 | -→6% | -→37% | 0 | - |
| 4.5 | Closure_157 | T | run3 | ok | 0 | 1 | 0 | - | 8 | 4 | 823/108,192/1,733,164/32,271 | 28.3 | 9%→12% | 37%→37% | 3 | - |
| 4.5 | Closure_157 | L | run1 | ok | 0 | 1 | 0 | - | 13 | -1 | 2,033/296,866/11,902,531/79,845 | 70.9 | 12%→20% | 37%→38% | 12 | 0 |
| 4.5 | Closure_157 | L | run2 | ok | 0 | 1 | 0 | - | 20 | -8 | 1,135/205,758/6,912,585/52,733 | 24.7 | 20%→26% | 38%→39% | 7 | 0 |
| 4.5 | Closure_157 | L | run3 | ok | 0 | 1 | 0 | - | 2 | 10 | 1,173/113,720/3,980,324/50,649 | 73.6 | 26%→0% | 39%→39% | 2 | 0 |
| 4.5 | Closure_157 | H | run1 | ok | 0 | 1 | 0 | - | 2 | 10 | 1,017/100,806/7,317,868/42,160 | 62.0 | 0%→5% | 39%→39% | 0 | - |
| 4.5 | Closure_157 | H | run2 | ok | 0 | 1 | 0 | - | 2 | 10 | 873/123,894/8,654,689/30,626 | 35.6 | 5%→9% | 39%→40% | 0 | - |
| 4.5 | Closure_157 | H | run3 | ok | 1 | 1 | 0 | - | 1 | 11 | 1,377/112,621/11,854,066/57,168 | 78.0 | 9%→16% | 40%→40% | 0 | - |
| 4.5 | Closure_157 | F | run1 | ok | 0 | 1 | 0 | - | 2 | 10 | 769/110,741/6,944,693/26,474 | 38.7 | 16%→19% | 40%→40% | 0 | - |
| 4.5 | Closure_157 | F | run2 | ok | 1 | 1 | 1 | - | 0 | 12 | 1,001/104,488/8,490,544/37,612 | 49.5 | 19%→4% | 40%→41% | 0 | - |
| 4.5 | Closure_157 | F | run3 | ok | 0 | 1 | 0 | - | 14 | -2 | 721/114,308/6,424,186/28,067 | 34.3 | 4%→8% | 41%→41% | 0 | - |
| 5.5 | Astropy-7606 | S | smoke | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 8/7,845/21,041/779 | 0.3 | 10%→11% | 30%→30% | 0 | - |
| 5.5 | Astropy-7606 | S | run1 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 6/1,250/20,249/612 | 0.3 | 11%→11% | 30%→30% | 0 | - |
| 5.5 | Astropy-7606 | T | run1 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 8/9,755/26,768/786 | 0.3 | 11%→11% | 30%→30% | 0 | - |
| 5.5 | Astropy-7606 | U | run1 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 6/9,980/18,407/702 | 0.3 | 11%→11% | 30%→30% | 0 | 0 |
| 5.5 | Astropy-7606 | T | run2 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 28/13,583/101,293/2,623 | 2.1 | 11%→11% | 30%→30% | 1 | - |
| 5.5 | Astropy-7606 | U | run2 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 6/1,813/26,574/662 | 0.3 | 11%→11% | 30%→30% | 0 | 0 |
| 5.5 | Astropy-7606 | S | run2 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 6/1,049/20,064/608 | 0.3 | 11%→11% | 30%→30% | 0 | - |
| 5.5 | Astropy-7606 | U | run3 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 26/14,744/98,467/3,069 | 2.4 | 11%→11% | 30%→30% | 1 | 0 |
| 5.5 | Astropy-7606 | S | run3 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 8/1,156/27,336/786 | 0.5 | 11%→11% | 30%→30% | 0 | - |
| 5.5 | Astropy-7606 | T | run3 | ok | 1 | 1 | 1 | 0 | 0 (strict 1) | 1 | 26/12,896/90,891/2,614 | 2.0 | 11%→12% | 30%→30% | 1 | - |
| 5.5 | Closure_157 | S | run1 | ok | 1 | 1 | 1 | - | 0 | 12 | 44/25,754/407,109/6,565 | 43.6 | 12%→15% | 30%→30% | 0 | - |

Arms: S single agent; T team (leader + sub-agents); U = T + `class_graph`; L = U with file locations (Amendment 2); H = S + read `RenamePrototypes.java` first (Amendment 3); F = S + the full suite takes about 30 minutes (Amendment 4). 4.5 slots: r20 smoke, r21-r38 frozen, r39-r44 L, r45-r47 H, r48-r50 F. Full table with every field: `E:\study05\runs\summary.json` (`scripts/summarize.py`).

## 4. What Claude reads from these runs (Claude's reading, not Zili Luo's)

Five readings from 30 counted runs, three per arm and bug; none is a rate.

1. **On Closure_157 the first gate is whether the agent sees the full suite's result.** Both repairs (T1, F2) followed a finished full-suite run, and none of the 14 runs whose suite was cut off repaired (F16). The bug's last needed change shows only as two new failures in tests that pass before the fix (F12), and they show only in a 13-17-minute suite. The cut-off was each agent's own timeout choice, not a limit it hit: the tool allowed 1800 s throughout.
2. **Telling the agent the duration was enough to change that choice.** All 3 F runs asked for the maximum timeout at once, against 1 of the 15 other runs (F14). The earlier cut-offs came from the agent's guess about the suite's length, not from the tool.
3. **The second gate is how the agent treats a failure outside the trigger list.** F1 named the right file and the right mechanism, then set the failures aside as possibly "pre-existing" without running the suite on the unchanged code; F3 spot-checked a few trigger tests with 14 failing. No run in the study compared against the unchanged code's suite.
4. **The arm structure did not decide the outcome.** T 1/3 (T1 by a generous-timeout habit, F2), U 0/3, L 0/3; the team runs used more time and tokens. `class_graph` got 0 calls in all 12 runs that had it, with or without file locations (F6, F10). Naming the third file first (H) reached it once and repaired nothing (F11, F15). The one arm that changed the outcome (F) changed only what the agent knew about time.
5. **Astropy-7606 says little about multi-hunk repair.** Every run, both models, made the same one-hunk patch, and all were repaired by the printed-name rule; the paper's "unsolved" is a grading artefact (§1a). Closure_157 is the informative case.

### Findings recorded during the runs (2026-11-18, before the batch ended)

Written down as they were found, so nothing depends on memory; the final observations above are drawn from these.

**F1. Closure: the one repair (T1) is the one run whose full test suite finished.** Frozen Sonnet 4.5 Closure result: 1 of 9 repaired (S 0/3, T 1/3, U 0/3). Most runs fixed most or all of the 12 trigger tests in `CodeGenerator`/`IRFactory`. The developer fix also changes `RenamePrototypes.java` (2 of its 7 hunks: after the parser change, quoted numeric keys reach `RenamePrototypes` as string keys and must not be renamed); without it two `RenamePrototypesTest` tests fail, and those show only in the full suite, which takes 777-790 s in this container (grading runs, alone). Every run tried the full suite; only T1's leader gave the `run` tool a timeout long enough (1800 s, the maximum). Its suite reported the two failures at step 113 of 139; it read `RenamePrototypes.java` at step 120, a sub-agent changed it at step 131, and a second 1800 s full run showed 0 failing. No other run saw those failures or opened that file.

| Run | Full-suite timeouts asked (s) | Finished? | At the end (grading) |
|---|---|---|---|
| S1 | 600, 60 | no | trigger 0/12 failing; new: 2 `RenamePrototypesTest` |
| S2 | 600, 320 | no | trigger 8/12 failing; 9 new (RR −5) |
| S3 | default 300, 600 | no | trigger 0/12 failing; new: 2 `RenamePrototypesTest` |
| **T1** | **1800, 1800** | **yes (2 failing → 0)** | **repaired** |
| T2 | default 300, 650 | no | trigger 0/12; new: 2 `RenamePrototypesTest`, 2 `AmbiguatePropertiesTest` (it also edited `RenameProperties.java` and a test file) |
| T3 | 600 | no | trigger 5/12 failing; new: 2 `RenamePrototypesTest`, 1 `CodePrinterTest`; changed `IRFactory.java`, `Parser.java` |
| U1 | 600 (sub-agent), default 300 ×2 | no | trigger 0/12; new: 2 `RenamePrototypesTest` |
| U2 | 600, 300, 300, default 300 | no | trigger 0/12; new: 2 `RenamePrototypesTest` |
| U3 | default 300, 600, 600, 360, 300, 600 | no | trigger 11/12 failing; only `CodeGenerator.java` changed |

So four of the eight failed runs (S1, S3, U1, U2) ended exactly where T1 stood when its suite finished; with that result they would have been one file from T1's position. Whether they would then have fixed it is not known (T1 is the only case).

**F2. Why T1 chose 1800 s is not visible.** Its text before the call is the same as every other run's ("Let's run the full test suite to ensure no regressions"); the thinking blocks in all transcripts are empty (the CLI logs only a signature), and no sub-agent brief mentions timeouts. What differs is a habit: T1's leader gave the 30-second trigger script 600 s every time (6 calls) and the full suite the maximum; the other runs sized timeouts close to what they had seen (default 300 s or 120-240 s for the trigger script) and about 600 s for the full suite. Claude's reading: a sampled habit of generous time budgets, not a reasoned estimate of the suite's length.

**F3. No run recovered from the cut-off.** After "[timed out after N s]" no run asked the tool for more time. Two tried to by putting `timeout 1200` (U2) or `timeout 600` (U1) inside the shell command while leaving the tool's own `timeout` at its 300 s default, so the tool still cut them at 300 s; S1 retried with 60 s. All then judged the fix by the trigger tests alone and reported success. Zili Luo's note: full suites of large projects commonly take 20-30 minutes, so a 13-minute suite is ordinary, and sizing a full-suite run at 5-10 minutes is a general risk, not an artefact of this bug.

**F4. This matches the paper's §5 failure.** The paper reports two new `RenamePrototypesTest` failures from the unmodified third file for its agents; here the same state is reached by S1, U1, U2 (and T2 with more). In this setup the proximate cause is that the agent never saw the full-suite result. Caveat: the paper's runs used a native filesystem where the suite is likely faster, and Claude Code's own Bash tool caps a command at 10 minutes.

**F5. Delegation is not what repaired T1.** T2 (also a team run) failed the same way as the S runs; the deciding step in T1 was the leader's own full-suite run. The U runs used the most sub-agents (4, 5, 10) and the most time (94, 86, 171 min) without a repair.

**F6. The class_graph tool was never called.** 0 calls in all 3 Astropy U runs and all 3 Closure U runs; nothing in any agent's text mentions it. With file locations (arm L, Amendment 2) all 3 Astropy L runs also made 0 calls (tool present in the init event every time; all 3 repaired, 1 sub-agent each, 117-140 s); Closure L results below.

**F7. Two leaders finished while sub-agents were still running (U3, T3).** The CLI stopped the sub-agents at session end; their pending `run` calls (U3: 5, T3: 2) appear in the transcript as "The user doesn't want to proceed with this tool use", which is the stop, not a permission problem. Both runs ended far from the fix (U3: only `CodeGenerator.java` changed, 11/12 trigger tests failing; T3: 5/12 failing).

**F8. Concurrency changes the suite's speed.** With other runs or gradings going at the same time, the Closure full suite took 869-1,044 s instead of 777-790 s. Since the results turn on whether a full-suite run finishes inside the agent's chosen timeout, all Closure runs ran one at a time; the only overlaps were the first night's (5.5 pilot with the first 4.5 Astropy runs) and the 3 Astropy L runs during Closure S3's grading and T3.

**F9. Follow-up arms (Amendments 3 and 4).** H = S + "read `RenamePrototypes.java` first" asks whether naming the file is enough; F = S + "the full suite takes about 30 minutes" (Zili Luo's wording, changed from the measured "13 minutes" before any F run; plan.md Amendment 4) asks whether knowing the duration makes the agent wait for it. Both Closure only, 3 runs each, base S (S's frozen result: 0 of 3).

**F10. Arm L on Closure: 0 of 3, still no tool calls.** L1 RR −1 (71 min, 12 sub-agents), L2 RR −8 (25 min, 7), L3 RR 10 (74 min, 2). `class_graph` was called 0 times in all 6 L runs (Astropy and Closure), so with the 6 U runs: 0 calls in all 12 runs that had the tool. Adding file locations did not change whether the agent calls it. MAPLE's prompt told the agent to query the tool first ("Use Maple proactively"); ours names the tool neutrally. That difference is the most likely reason the paper's agents used their tool and ours did not (untested).

**F11. Arm H (H1, H2): the hint did not reach the defect, and the full suite never finished.** Both changed only `CodeGenerator.java` and `IRFactory.java` (not `RenamePrototypes.java`) and ended at RR 10, the two `RenamePrototypesTest` failures, like S1, S3, U1 and L3. "RenamePrototypes" occurs 2-3 times in each transcript, the prompt included. Full-suite attempts: H1 first ran with the tool default (cut at 300 s), then `timeout 600 defects4j test 2>&1 | tail -50` (run-tool timeout 620); H2 first ran with the default (cut at 300 s), then `timeout 90 defects4j test 2>&1 | tail -50`. In both second attempts the shell `timeout` killed the suite before it printed the failing tests, and the pipe into `tail` turned the exit code into 0, so the result showed "exit code 0" with the output stopping at `Running ant (run.dev.tests)....`. Neither agent noticed the missing failing-tests list. H1 then ran single test classes (`CodePrinterTest`, `IRFactoryTest`, `RenamePropertiesTest`, not `RenamePrototypesTest`) and wrote "All tests pass". H2 relied on the trigger script and also ended "All tests pass".

**F12. The two `RenamePrototypesTest` failures are regressions the fix itself causes (Zili Luo's question, 11-18 night; from the grading records).** `RenamePrototypesTest` passes on the buggy code; it is not among the 12 trigger tests. Every RR-10 run (S1, S3, U1, U2, L3, H1, H2) made all 12 trigger tests pass (`trigger_still_failing` empty) and broke exactly `testRenamePrototypes1` and `testRenamePrototypes2` (`new_failures`); RR 10 = 12 − 2. T2 and T3 broke them too, and T1 is the only run that broke them and then fixed them. So the third file is a knock-on change: once `IRFactory` accepts numeric and quoted keys in get/set, `RenamePrototypes.java` has to change as well (the developer's two hunks there replace a `getType() != Token.NUMBER` check with `TokenStream.isJSIdentifier(...)`). The paper's §5 states the root cause (verified verbatim in the v3 PDF, 2026-11-19): "the modified files change the internal representation of object-literal keys, while the unmodified file still assumes the old representation"; its takeaway: "when new test failures appear in files the agent did not modify, they should be treated as contextual cues of missing edits." The package's command log shows the paper's Claude run ran `testRenamePrototypes1` and `testRenamePrototypes2` individually (`tools_count_claude.csv` lines 1287-1288, 1299; commands only, no output or order), so it likely saw them as well. This corrects how Claude first described them to Zili Luo in conversation ("still failing"): they are new failures, not leftovers of the defect. It also helps explain why arm H did little (F15): at the start `RenamePrototypes.java` has nothing visibly wrong and its tests pass; the file matters only after the main fix, and only the full suite shows that.

**F13. Hypothesis for arm F (Zili Luo, 11-18 night, written before any F run).** The runs that got the trigger tests passing stayed unfixed because the suite's only signal of the regression (the two `RenamePrototypesTest` failures) comes at the end of a 13-17-minute run, and every such run except T1 cut the suite off first (default 300 s or a shorter timeout of its own). T1 let it finish, saw the failures, read and changed `RenamePrototypes.java`, and repaired. It covers the 7 RR-10 runs and T2, not S2, U3, T3, L1 and L2, which did not get the trigger tests passing. Readings of the 3 F runs: (a) the suite finishes, the failures show, the agent fixes them → supports; (b) the suite finishes and the failures show but the agent does not fix them → the feedback is not enough; (c) the suite is still cut off → stating the duration does not make the agent wait. Three runs can support or weaken the idea, not prove it.

### Findings recorded after the last run (2026-11-19, 02:40-03:30)

**F14. Arm F: stating the duration changed the timeout in all 3 runs; 1 of 3 repaired.** Each F run's first full-suite call asked the `run` tool for 1800 s (the maximum); among the 15 other Closure runs only T1 did. All three suites finished.
- **F2 (repaired, RR 12, 50 min):** the suite showed 2 failing (`RenamePrototypesTest`); it read the test, grepped `RenamePrototypes.java` for `Token.NUMBER`, read and edited that file (steps 107-119), and a second 1800 s suite run showed 0 failing.
- **F1 (RR 10, 39 min):** the suite showed the same 2 failing. It ran one alone, read the test, and wrote "the numeric key `2` is being lost/renamed when it shouldn't be. Let me check if RenamePrototypes needs to be aware of numeric string keys." It then listed `defects4j export -p tests.trigger`, concluded "Since these two tests are NOT in the trigger tests list (the tests that should be fixed by this bug fix), they might be pre-existing failures or unrelated tests", reran the trigger tests and reported success. It never ran them on the unchanged code.
- **F3 (RR −2, 34 min):** the suite showed 14 failing. It listed the trigger tests, ran a few single trigger tests that passed, wrote "The main bug-exposing tests are now passing" and finished; 5 trigger tests were still failing at grading.

Against F13: F2 is reading (a), F1 and F3 are reading (b), none is (c).

**F15. H3: the hint led to the third file once, without the suite.** H3 read `RenamePrototypes.java` at step 1, as told. Both of its full-suite attempts were cut (`| head`, tool timeouts 120 s and 300 s). From step 108 on it edited `RenamePrototypes.java` about 20 times; why at that point has not been read in detail. At grading it had no new failures (`RenamePrototypesTest` passes) and localization 1, but one trigger test still failed (`ParserTest::testObjectLiteralDoc1`): RR 11, not repaired. So the hint reached the file in 1 of 3 H runs (H1 and H2: F11) and led to no repair.

**F16. Across all 18 Closure runs.** The full suite finished in 4 runs, all at 1800 s: T1, F1, F2, F3. Both repairs (T1, F2) are among them; none of the 14 runs whose suite was cut off repaired. Of the 4 that saw the result, 2 acted on the failures and 2 set them aside (F1: "not in the trigger list"; F3: a few trigger tests spot-checked). One more way the result got lost: H1, H2 and L3 ran `timeout N defects4j test 2>&1 | tail`, so the shell killed the suite, the pipe returned exit code 0, and the output simply stopped before the failing-tests list; none of them noticed.

## 5. What failed, was skipped, or differs from the plan

- **CLI and tools differ from the paper.** Claude Code 2.1.289, not the paper's 2.0.13; 2.1.289 has no `TodoWrite` tool. Commands ran through this harness's `run` tool (default 300 s, maximum 1800 s), not Claude Code's own Bash (maximum 10 min).
- **Arms L, H and F were added after the frozen 18 runs started** (Amendments 2-4, Zili Luo's decisions during the runs). They are follow-ups, not part of the frozen design. The F wording was changed once before any F run ("about 13 minutes", measured → "about 30 minutes", Zili Luo's wording, more than the measured 13-17 min); the running chain had loaded the old text, so it was stopped after H3 by a placeholder file at F's output path (no F model call made) and F was started again.
- **Three runs per arm and bug.** No rate or arm comparison is claimed.
- **The reason behind a timeout choice is not visible.** Thinking blocks are logged empty (signature only), so findings F2 (T1's 1800 s) and F14 rest on the agents' visible text only.
- **Usage readings are coarse.** Whole-percent five-hour and weekly readings from the CLI's rate-limit event; on the first night the 5.5 pilot and the first 4.5 Astropy runs overlapped, and the Astropy L runs overlapped Closure S3's grading and T3, so those readings mix runs. Concurrency also slowed the Closure suite (F8); every Closure agent run ran alone.
- **Console token figures are wrong.** The per-run console line prints the final turn's usage; the table uses `modelUsage` (whole run, sub-agents included).
- **The first patch-similarity figures were wrong** (compared against the buggy side of Defects4J's fixed → buggy patch); corrected in Amendment 3, figures in §2.
- **Not done:** hand coding (coding-scheme.md, Zili Luo's); a MAPLE-style arm that tells the agent to query the graph tool first (F10; Zili Luo's decision); H3's step-108 reasoning read in detail (F15).
- **Sonnet 5.5 runs are a pilot**, not counted; its Closure run had the image's fix data readable (its commands show no access).
- **Astropy-8707**, the planned swap, was rejected because its gold patch fails in the pinned image (§1a).

## 6. Framing as a case study

This is a case study of two bugs, not a benchmark. What it can say:

- On Closure_157, a three-file Defects4J bug no agent in the paper fixed, Sonnet 4.5 in Claude Code repaired it in 2 of 18 runs, and both repairs came after the agent let the full test suite finish. The fix's third file is needed only because the main fix breaks two tests that pass before it, and only the full suite shows that.
- Most failures were not localisation failures: 8 runs (S1, S3, U1, U2, L3, H1, H2, F1) made all 12 trigger tests pass and stopped two tests short. Seven of them stopped there because the agent gave the full suite a 1-11-minute timeout (at most 650 s) for a 13-17-minute run, or killed it in the shell and read the truncated output as success; F1 let the suite finish, saw the two failures and set them aside (F14).
- Stating the suite's duration made the agent wait every time (3/3) and surfaced the regression every time, but only 1 of 3 then treated it as its own: an agent seeing failures outside the bug's trigger tests can call them "pre-existing" without checking.
- Sub-agents and a UML class-graph tool, as offered here (neutral wording, no instruction to use it), did not change this: the tool was never called.
- Astropy-7606's "unsolved" status in the paper comes from a test-name mismatch in the benchmark record, reported upstream since 2024.

What it cannot say: per-arm rates, anything about other bugs or models, or why an agent chose a given timeout. A possible next step, if Zili Luo wants one: a small set of multi-hunk bugs whose last needed change shows only as a regression in the full suite, with the suite's duration stated and a baseline run available. Zili Luo's addition (11-19): how to make the repair consistent across runs while keeping what is already fixed; the same prompt ended anywhere from repaired to RR −8, and S2, L1, L2 and F3 ended with more failing tests than the buggy code.
