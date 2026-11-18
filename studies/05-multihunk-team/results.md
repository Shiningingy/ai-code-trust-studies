# Study 05 results: sub-agents on two multi-hunk bugs that no agent in the paper fixed

**Status: CLOSURE_STATUS.** Plan: [plan.md](plan.md) (frozen 2026-11-18, Amendment 1 the same night). Counted runs use Sonnet 4.5 (`claude-sonnet-4-5-20250929`, the paper's model) on Claude Code 2.1.289. The first Sonnet 5.5 runs are kept as a labelled pilot, not counted. All run data: `E:\study05\runs\` (4.5 under `sonnet-4-5\`). Hand coding (coding-scheme.md) has not started; it is Allen's.

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

RUN_TABLE

## 4. What Claude reads from these runs (Claude's reading, not Allen's)

OBSERVATIONS

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

**F3. No run recovered from the cut-off.** After "[timed out after N s]" no run asked the tool for more time. Two tried to by putting `timeout 1200` (U2) or `timeout 600` (U1) inside the shell command while leaving the tool's own `timeout` at its 300 s default, so the tool still cut them at 300 s; S1 retried with 60 s. All then judged the fix by the trigger tests alone and reported success. Allen's note: full suites of large projects commonly take 20-30 minutes, so a 13-minute suite is ordinary, and sizing a full-suite run at 5-10 minutes is a general risk, not an artefact of this bug.

**F4. This matches the paper's §5 failure.** The paper reports two new `RenamePrototypesTest` failures from the unmodified third file for its agents; here the same state is reached by S1, U1, U2 (and T2 with more). In this setup the proximate cause is that the agent never saw the full-suite result. Caveat: the paper's runs used a native filesystem where the suite is likely faster, and Claude Code's own Bash tool caps a command at 10 minutes.

**F5. Delegation is not what repaired T1.** T2 (also a team run) failed the same way as the S runs; the deciding step in T1 was the leader's own full-suite run. The U runs used the most sub-agents (4, 5, 10) and the most time (94, 86, 171 min) without a repair.

**F6. The class_graph tool was never called.** 0 calls in all 3 Astropy U runs and all 3 Closure U runs; nothing in any agent's text mentions it. With file locations (arm L, Amendment 2) all 3 Astropy L runs also made 0 calls (tool present in the init event every time; all 3 repaired, 1 sub-agent each, 117-140 s); Closure L results below.

**F7. Two leaders finished while sub-agents were still running (U3, T3).** The CLI stopped the sub-agents at session end; their pending `run` calls (U3: 5, T3: 2) appear in the transcript as "The user doesn't want to proceed with this tool use", which is the stop, not a permission problem. Both runs ended far from the fix (U3: only `CodeGenerator.java` changed, 11/12 trigger tests failing; T3: 5/12 failing).

**F8. Concurrency changes the suite's speed.** With other runs or gradings going at the same time, the Closure full suite took 869-1,044 s instead of 777-790 s. Since the results turn on whether a full-suite run finishes inside the agent's chosen timeout, all Closure runs ran one at a time; the only overlaps were the first night's (5.5 pilot with the first 4.5 Astropy runs) and the 3 Astropy L runs during Closure S3's grading and T3.

**F9. Follow-up arms (Amendments 3 and 4).** H = S + "read `RenamePrototypes.java` first" asks whether naming the file is enough; F = S + "the full suite takes about 13 minutes" asks whether knowing the duration makes the agent wait for it. Both Closure only, 3 runs each, base S (S's frozen result: 0 of 3).

## 5. What failed, was skipped, or differs from the plan

FAILED

## 6. Framing as a case study

FRAMING
