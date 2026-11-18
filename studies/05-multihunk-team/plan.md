# Study 05 plan: do sub-agents help on multi-hunk bugs that no single agent fixed?

**Status: frozen 2026-11-18.** Allen settled all eight decisions on 2026-11-18 (listed under "Decisions (settled 2026-11-18)"; source: the Study 05 handoff in the workspace). The commit that adds this text is the freeze; its hash goes in the Launch log. Changes after it go under Amendments, with a date and a reason. Pre-run checks made before the freeze are under "Pre-run checks".

Set up on 2026-11-18 (Claude Code 2.1.289, model `claude-sonnet-5-5`). The first night runs in overnight mode: pre-checks, the class_graph tool test, one smoke run, the 9 Astropy runs, then ONE Closure run (arm S), then stop; Allen decides the other Closure runs after seeing that run's real cost.

## Source

"Beyond Accuracy: Behavioral Dynamics of Agentic Multi-Hunk Repair" (Nashid, Ding, Gallaba, Hassan, Mesbah; TOSEM 2026; arXiv 2511.11012v3). Replication package: `agentic-se/agentic-multihunk-repair`, commit `5cdb227e3099e7a4044fc6d4c868ae9a20d9f054` (2026-06-07), cloned to `E:\study05\src\agentic-multihunk-repair`. In the paper each coding-agent CLI (Claude Code 2.0.13 on Sonnet 4.5, Codex, Gemini CLI, Qwen Code) runs one trajectory per bug.

## Question

On two multi-hunk bugs that none of the paper's four agents repaired, does a leader that delegates to sub-agents, each returning a short written handoff, do better than one agent working alone? And does giving that leader a static UML class graph of the code help it further?

The comparison Allen cares about most is **U vs T** (graph vs no graph, same delegation design). **S** is the single-agent control. With 3 runs per cell this is a case study: it can show a large, consistent difference or the shape of the failures, not a small effect. A null result is still a result.

## The two bugs

| | Astropy-7606 (HunkSWE) | Closure_157 (Hunk4J) |
|---|---|---|
| Source | SWE-bench Verified `astropy__astropy-7606`, image `swebench/sweb.eval.x86_64.astropy_1776_astropy-7606:v2` pinned by digest `sha256:f4bcd149…a184f` (the digest in the paper's `image_manifest.json`) | Defects4J v2.0.1, Closure 157 buggy (`157b`), Java: Amazon Corretto 8u412 (the JDK the paper's scripts select) |
| Developer fix | 2 hunks, 1 file (`astropy/units/core.py`) | 7 hunks, 3 files (`CodeGenerator.java`, `parsing/IRFactory.java`, `RenamePrototypes.java`) |
| Failing tests | FAIL_TO_PASS `astropy/units/tests/test_units.py::test_unknown_unit3`; 241 PASS_TO_PASS | 12 trigger tests in 6 classes (`CodePrinterTest` ×4, `FunctionNamesTest`, `RenamePropertiesTest` ×2, `SimpleDefinitionFinderTest`, `IRFactoryTest` ×3, `ParserTest`) |
| Paper, Claude Code | repair 0; failed before 1, after 1; RR 0; 170 s; 5,164 output tokens; 720k cache-read tokens | repair 0; localization 0; failed before 12, after 2; RR 10; 1,037 s; 53,104 output; 14.7M cache-read; patch touched 2 of 3 files |
| Paper, all four agents | all localized the file, none repaired (Table 5); all four show failed after = 1 | none localized (Table 5); §5: two new failures in `RenamePrototypesTest` from the unmodified third file |

**Reproduced on this machine (2026-11-18):**

- Astropy-7606: on the buggy tree with test_patch, `test_unknown_unit3` FAILS (`TypeError: None is not a valid Unit`) and 241 pass; with the gold patch, all 242 pass (`E:\study05\astropy-7606\verify.log`, `E:\study05\verify\astropy__astropy-7606\verify.json`).
- Closure_157: on the buggy tree, `defects4j compile` succeeds; the paper's `run_bug_exposing_tests.sh` (6 classes, 12 failures) and the full `defects4j test` (790 s) report exactly the 12 trigger tests failing and nothing else; with the developer fix (Defects4J's `157.src.patch`, reversed: 3 files, +63/−15) it compiles and `defects4j test` reports `Failing tests: 0` (754 s).

**Finding that changes how Astropy-7606 must be scored.** The SWE-bench record's PASS_TO_PASS list names `test_compose_roundtrip[]`, but pytest in the pinned image names that case `test_compose_roundtrip[unit0]`. Under SWE-bench's grading rule (PASS_AND_FAIL: a test missing from the log counts as failed), **even the developer's gold patch is "not resolved"** here: failed after = 1. The paper's four agents all show failed after = 1, which is what this artefact produces for a correct fix. So "no agent repaired Astropy-7606" may be partly or wholly a grading artefact; the paper's published data do not include the HunkSWE patches, so this cannot be checked from the package. This study reports both verdicts: `repair_strict` (SWE-bench's rule, comparable with the paper) and `repair` (the renamed case matched by its printed name, `bugs.py: test_aliases`). Primary Astropy outcome = `repair` (D2). The pre-check below settles what the paper's data show.

## Arms

Same model, CLI version, tools, budget and harness in every arm; the prompts differ only by appended blocks. Exact texts: `scripts/prompts.py`; rendered prompts for both bugs: `prompts/rendered/<bug>_<arm>.txt` (from `python scripts/run_all.py --dry-run --with-control`).

- **S (single agent, control; approved D1):** the paper's prompt template, rendered exactly as the paper's runner renders it (`prompts/paper_hunk4j_prompt.md`, `prompts/paper_hunkswe_prompt.md`, verbatim from the package with line endings normalised), plus one environment note that explains this harness's tools. The sub-agent tool is disabled (`--tools` omits `Agent`). Sonnet 4.5 numbers from the paper are not comparable with Sonnet 5.5 and a newer CLI, so without S there is no baseline for T and U.
- **T (delegation):** S's prompt + a leader block ("How to work"): the leader does not edit source itself; it localizes, plans and decides the next step; it starts one or more sub-agents through the Agent tool (e.g. one per localized file or group of edits, or one to investigate a question); each sub-agent ends with a short written handoff (what it changed, what it verified with which commands, what is still open); the leader decides from the handoffs, may read files and run commands to localize and check, and confirms the final state. Wording is neutral (it avoids the leak-check words, see below) and fixed before any run.
- **U (delegation + class-graph tool; D7):** T's prompt + one neutral block naming the `class_graph` tool: it returns a UML class graph (PlantUML) of the main source code as checked out at the start of the session, for a class or package/module name the agent gives, with related classes within a number of hops. The tool is an MCP server like the paper's MAPLE (which had lookups only). Leader and sub-agents both have it.

The leader's "do not edit source files yourself" is an instruction, not a tool restriction: removing Edit from the leader would remove it from sub-agents too. Compliance is coded by hand (coding scheme, T/U rows).

## Arm U: the class_graph tool (D7, 2026-11-18)

Replaces the setup draft's pre-placed, pre-scoped `class-graph.puml` (that draft, its 50k-token tier rule and the files in `uml/<bug>/graph.puml` are kept for the record but are **not used**). Allen's decision: a Maple-style tool, so the agent chooses the scope; no pre-scoping, no stubs.

1. **Index, built before any run, statically, from the buggy base tree only** (`scripts/uml/build_index.py`, the same parsers as before: `uml_py.py` with the standard-library `ast`; `uml_java.py` with `javalang` 0.13.0). Never from the fixed version or the gold patch, never by a model. The index is the whole main source tree, tests excluded. Re-running gives byte-identical files (`--check`).

   | Bug | Files | Types (incl. Python module boxes) | Chars | ~Tokens | SHA-256 |
   |---|---|---|---|---|---|
   | Astropy-7606 | 391 | 1,226 | 582,307 | 145.6k | `ab3e0ce8…952f5df` |
   | Closure_157 | 377 | 887 | 1,110,264 | 277.6k | `205a37e7…168c4f` |

   Stored at `E:\study05\uml\<bug>\index.puml`; stats in `uml/<bug>/index-stats.json`.
2. **Tool** (`scripts/uml/uml_mcp.py`, stdio MCP, standard library only, copied with the index to `E:\w\tools` for each run): `class_graph(name, hops=1)`. `name` = a class (simple or qualified) or a package/module (prefix match). The matched classes are shown with fields and method signatures; classes within `hops` (0-3) relationship steps in either direction (inheritance, implements, field types, uses, nesting) are shown by name only, with every edge among the shown classes. Answers are capped at 60,000 characters: over the cap, hops are reduced step by step (the answer says so), then members are dropped. No match returns similar class and package names. Deterministic: the same call always gives the same text.
3. **Static, not live:** the index reflects the code at session start; the tool description says so. It does not see the agent's edits.
4. **Logged:** every call (name, hops asked/used, classes matched/related, characters) goes to the run's `uml.jsonl`; `run.json` counts `uml_calls` from the transcript.
5. Tested before any run on both bugs with no model call (calls such as `UnitBase`, `astropy.units.core`, `CodeGenerator`, `IRFactory`, `RenamePrototypes`, `Node` hops 2 → reduced to 0, an unknown name); no leak-check word in any answer.
6. Coding scheme rows U1-U3 now read "first call of the class_graph tool" instead of "first opened class-graph.puml".

## Design and order (D8)

2 bugs × 3 arms × 3 runs = **18 runs**, one at a time. Within a bug, the arm order rotates per round: k=1 **S T U**, k=2 **T U S**, k=3 **U S T**. Slots: `E:\w\r00` = the smoke run (Astropy, arm S; checks the harness and measures time and quota; **not counted**), `r01`-`r09` Astropy, `r10`-`r18` Closure (`run_all.py --plan`). Each run folder is kept for hand coding.

Steps: (1) pre-checks; (2) build and test the class_graph tool, no model call; (3) the smoke run, then a self-check (prompt arrived as rendered, agent ran only in the workspace and container, both verdicts graded, tokens/time/five-hour reading logged, leak grep clean); (4) the 9 Astropy runs; (5) checkpoint: Allen reads 1-2 Astropy trajectories and tries the coding scheme; (6) Closure: ONE run first (arm S, slot r10), measure its real cost, then Allen decides how many more and which arms. On the first night steps 1-4 and the one Closure run run unattended (`run_all.py --smoke`, then `--overnight`); step 5 moves to the morning.

No replacements: a run that times out or refuses is scored as it stands. A run cut off by a usage limit is logged as interrupted and repeated whole from a fresh tree (never resumed, never counted); an infrastructure error is repeated up to twice.

## Harness (reused from Study 04) and how it differs from the paper

Pattern from Study 04 (`studies/04-review-intent/scripts/agent.py`, `env.py`, `llm.py`, `box_mcp.py`): `claude -p` on the subscription, isolated from the local setup (no settings sources, user CLAUDE.md excluded, auto-memory off, CLAUDE*/ANTHROPIC* env vars dropped); the agent edits a host copy with file tools and runs every command through one MCP tool, `run`, inside a per-bug Docker container with no network and the tree mounted at `/testbed`; a ledger row per call; usage guards; full stream-json transcripts.

| | Paper (Claude Code) | This study |
|---|---|---|
| CLI / model | 2.0.13 / Sonnet 4.5 (`claude-sonnet-4-5-20250929`; the HunkSWE runner documents `--model` but its command line does not pass it); no effort or thinking flag | **2.1.289 pinned** (`llm.PIN`; a different installed version stops the run) / `--model claude-sonnet-5-5` passed explicitly; **no `--effort` flag** (D4: as the paper; the CLI default applies and is recorded) |
| Prompt delivery | template written to `CLAUDE.md`, `-p "Read and execute the instructions listed in CLAUDE.md."` | the same rendered text sent as the prompt itself; no CLAUDE.md (D3), so sub-agents do not inherit the whole task and the leader block |
| Tools | everything, `--dangerously-skip-permissions`; Bash in the environment (Hunk4J: on the host; HunkSWE: inside the container, network on). Claude used Bash, Edit, Glob, Grep, Read, TodoWrite; no sub-agent calls in the published Closure_157 counts | Read, Edit, Write, Glob, Grep, TodoWrite + `run` (bash in the no-network container); `Agent` added in T/U only; no host Bash, no web. The init event is checked live: wrong tool set → process killed before the model is called |
| Git history | Defects4J checkout keeps the fixed version as the parent commit; the paper's Claude Closure_157 run used it (`git log | grep D4J_Closure_157`, `git diff 822acb61 3ff39c0b -- …IRFactory.java`, `git show`) | **removed**: the Closure tree is the checkout without `.git`, in a fresh one-commit repo. SWE-bench's `/testbed` history ends at the base commit (checked), so it is kept, with test_patch committed as HEAD as the paper's harness does. Our runs are therefore harder than the paper's on Closure |
| Localization hint | `defects4j.build.properties` in the checkout names the 3 modified classes (`d4j.classes.modified`) | **blanked** (D6): in the run tree `d4j.classes.modified=` and `d4j.classes.relevant=` are kept with empty values; grading restores Defects4J's original file. The plan was to hide the file, but without it Defects4J's `check.properties` target fails, so `defects4j compile`, `test` and every `export` (which the paper's test scripts call) break; with the keys present but empty all of them work (checked 2026-11-18: compile OK, the trigger script reports the same 12 failures). No other file in the tree names the modified classes (`.defects4j.config` holds only pid/vid). Same in every arm. Coding row H8 records whether an agent read the file |
| Test scripts | `run_bug_exposing_tests.sh`, `run_all_tests_trace.sh` (Hunk4J); `run_failing_tests.sh`, `run_all_tests.sh` + `.swebench/` (HunkSWE) | the same files (line endings normalised to LF; `sdk use java …` is a no-op in the image, which has only Corretto 8u412) |
| Time limit | HunkSWE runner: `--duration-min` default 30; Hunk4J wrapper: no timeout | **the same** (D5): Astropy 30 min wall clock, Closure no cap, every arm; longest single `run` command 30 min |
| Runs per bug | 1 | 3 per arm |

## Measures (fixed before any run)

Paper's own (Section 2.2; equation numbers as in v3 HTML, where regression reduction is Eq. 6, not Eq. 5), implemented in `scripts/grade.py` on a fresh copy of the base tree with the captured patch, in a no-network container:

- **Localization (Eq. 3):** 1 if the developer-modified files ⊆ the files the agent's patch modifies; 0 otherwise, and 0 if the patch is empty or does not compile. (The package's own `generate_localization_ability_*.py` computes it from edit accuracy instead; this study uses Eq. 3 as printed.)
- **Compilation (Eq. 4):** non-empty patch that applies and compiles. Java: `defects4j compile`. Python: patch applies and every changed `.py` file passes `py_compile`.
- **Repair accuracy (Eq. 5):** non-empty patch and no failing test afterwards. Java: `defects4j test` reports 0 failing tests (the buggy version's only failures are the 12 trigger tests, so this equals "trigger tests pass and no previously passing test fails"). Python: all FAIL_TO_PASS and PASS_TO_PASS pass (SWE-bench "resolved"), test files reset to test_patch first as SWE-bench does; reported as `repair` (aliased name, primary) and `repair_strict`.
- **Regression reduction (Eq. 6):** failed_before − failed_after, undefined if compilation fails; failed_before as in the paper's data (Closure 12 = number of trigger tests; Astropy 1).
- **Tokens:** from the run's `result` event: input, cache creation, cache read, output (the paper's `token_and_duration` columns), plus `modelUsage` per model (covers sub-agents) and `total_cost_usd` as the CLI reports it.
- **Runtime:** wall clock of the `claude -p` process, and the CLI's `duration_ms`.
- **Usage:** five-hour and seven-day utilization read from the CLI's `rate_limit_event` before and after every run (`rate_before`, `rate_after` in `run.json`).
- **Delegation and tool use:** number of sub-agent (`Agent`) calls and of `class_graph` calls per run, counted from the transcript.

Also recorded: changed files, new untracked files (not part of the patch, as in the paper's `git diff HEAD`), trigger tests still failing, new failures, number of turns, every `run` command (`box.jsonl`).

**Hand coding** (Allen, per trajectory, scheme in `coding-scheme.md`, defined before any transcript exists): first open and first edit of each developer-modified file (step index), direction of the first edit, reverts of a correct change, where the failure arose, and for T/U the number of sub-agents, handoff information loss and leader compliance; for U, graph use.

**Analysis:** descriptive. Per-run table (18 rows) and per-cell counts out of 3 for repair, localization and compilation; medians of RR, tokens and runtime. A difference is called "consistent" only if it holds in at least 2 of 3 runs per bug; no significance tests at n = 3.

## Leak check

`claude -p` puts the working directory's path into the model's context (Study 04). Run folders are `E:\w\rNN`; the MCP server script and its log are copied to `E:\w\tools` so no study path appears even in a process argument. The prompts contain none of the checked words; `check_leaks.py` scans prompt, init event (cwd, memory paths) and transcript after every run for: study, multihunk, multi-hunk, beyond accuracy, polyhunk, hunk4j, hunkswe, hunk-swe, team, paper, nashid, mesbah, gallaba, hassan, agentic-se, tosem, 2511.11012, study05, s05. Transcript hits are reviewed by hand (code the agent reads may contain "paper" or "team" legitimately); a hit in the prompt or init event stops the study.

## Budget, time and disk (estimates; measured values go in the Launch log)

- **Disk (measured 2026-11-18):** see README "Disk". All data on E: (Docker images, clone, base trees, run folders); G: holds only this folder.
- **Time per run:** Astropy, paper's Claude 170 s; expect 5-15 min for S and 10-30 min for T/U. Closure, paper's Claude 17 min with a native filesystem; here one full suite takes about 13 min and the trigger script about 3 min (compile included), so expect 30-60 min for S and up to the 90-min limit for T/U. All 18 runs: roughly 12-20 hours, spread over several five-hour windows.
- **Quota:** from Study 04's ledger, a Sonnet 5.5 agent run used about 4.4% of the five-hour window per million total tokens. Paper-sized runs: Astropy ~0.9M tokens → ~4% of a five-hour window; Closure ~15M tokens → up to ~60% of a five-hour window and ~6% of the week per run. **Guard (Allen 2026-11-18): the five-hour window only, checked between runs, never inside one.** Before each run the harness reads the last five-hour reading and starts only below 80% (Astropy) or 35% (Closure); otherwise it waits for the reset + 2 min, so nothing is lost. The weekly stop is set at 0.99 only to catch a real limit (weekly is not a concern: a whole five-hour session is about 9% of the week). No hard stop time is set.

## Decisions (settled 2026-11-18)

1. **D1** Arm S is included as the control, on both bugs.
2. **D2** Follow the paper's metrics, reported both ways: Astropy primary = `repair` (the test name pytest prints, `[unit0]`); `repair_strict` (SWE-bench's recorded `[]`) beside it.
3. **D3** The prompt is passed directly, not via CLAUDE.md.
4. **D4** Effort as the paper: no effort or thinking flag; `--model claude-sonnet-5-5` passed explicitly.
5. **D5** Time limit as the paper: Astropy 30 min, Closure no cap, every arm.
6. **D6** Remove the class-name hint in `defects4j.build.properties` during the run, restore it before grading, every arm (implemented as blanked keys, see the harness table).
7. **D7** Arm U = team + a Maple-style class_graph tool (section "Arm U").
8. **D8** Order: pre-checks → tool test → smoke run → 9 Astropy runs (rotated) → checkpoint → ONE Closure run, then Allen decides.

## Pre-run checks (2026-11-18, before the freeze)

**(a) Astropy-7606 vs the paper's per-instance data.** The package has no HunkSWE patches or test logs; it has per-agent `failed_test_after` (`hunk-poly/*/*_repair_ability.csv`) and the grader (`hunk-swe/swe_bench_utils/grader.py`): the official `swebench.harness.run_evaluation`, with `failed_tests` = FAIL_TO_PASS failures + PASS_TO_PASS failures. Our gold-patch and buggy pytest logs (pinned image, SWE-bench's own test command) graded with the official swebench 4.1.0 code (`get_logs_eval`, `get_eval_tests_report`, run in a python:3.11 container; `E:\study05\precheck\swebench-official\`): **gold → RESOLVED_NO, failed count 1** (only `test_compose_roundtrip[]`, absent from the log, which prints `[unit0]`); **unfixed tree → failed count 2**. All four of the paper's agents have failed count 1. So each of the four made `test_unknown_unit3` pass with no PASS_TO_PASS regression, and was marked unresolved by the test-name artefact alone. "No agent repaired Astropy-7606" is a grading artefact in the paper's own harness (the tests' verdict, not a reading of their patches, which are not published).

The overnight rule said: swap to **Astropy-8707** if it reproduces within about an hour. Set up (image pinned by the paper's digest `sha256:55e63ac8…915f13b`, record from the package's `swe_bench.jsonl`): it **does not reproduce**. In its pinned image all `TestHeaderFunctions` tests ERROR in setup (pytest turns the nose-style `setup(self)` deprecation warning into an error), so the gold patch also gets failed count 8, the same as the unfixed tree; official swebench 4.1.0 gives RESOLVED_NO for gold (`E:\study05\precheck\swebench-official-8707\`). The paper's Claude, Codex and Gemini all show failed count 8 there too (Qwen 1). So **7606 is kept** and flagged: with the `repair` verdict (printed name) a correct fix is scored as repaired, which is what the paper's four agents appear to have produced; Astropy runs can therefore show only whether S/T/U reach the fix and at what cost, not a gain over "unsolved". 8707 stays in `bugs.py`, marked not used.

**(b) Closure_157: the paper's Claude run read the fixed version from git history.** The package's command log for that run (`hunk4j-results/results/claude_code_results/claude_results/tools_count_claude.csv`, lines 1303-1309) contains `git log --oneline | grep "D4J_Closure_157"`, `git diff 3ff39c0b 822acb61 -- …/CodeGenerator.java`, the same for `IRFactory.java` (three times), `git show 822acb61:…/IRFactory.java | grep -A 20 "transformAsString"`, and `git stash && git checkout 822acb61 && defects4j test -t …RenamePropertiesTest::testRenamePrototypes1`. Our trees have a fresh one-commit history, so our Closure runs are harder than the paper's (description only, as decided).

**(c) `defects4j.build.properties`:** see the harness table (blanked keys; hiding the file breaks Defects4J).

## Amendments

### Amendment 1 (Allen, 2026-11-18, night): Sonnet 4.5 for the counted runs; hide the fix data in the Defects4J container

**Why.** After the first Sonnet 5.5 runs, three training-exposure checks were made (results.md, "Training-data exposure"): (1) every 5.5 Astropy patch was compared with the gold patch; (2) a memory probe asked each model, with no repository and no tools, what the developer's fix was; (3) the Defects4J image was searched for fix-revealing data. Sonnet 5.5 reproduced the Astropy-7606 gold patch almost line for line from memory (`return NotImplemented`, `isinstance(other, type(self))`) and guessed 2 of Closure_157's 3 files; Sonnet 4.5 recalled neither fix. Sonnet 4.5 (`claude-sonnet-4-5-20250929`, the paper's model) is still available on this account (checked by a one-word call). The 5.5 probe also pointed at `defects4j info`, which exposed that the agent's container held the developer's fix.

**Changes.**
1. **Model:** every counted run uses `claude-sonnet-4-5-20250929` (`llm.SONNET`, overridable with `STUDY_MODEL`). CLI stays 2.1.289 (the harness relies on its flags); the paper's CLI was 2.0.13, a recorded difference. 4.5 runs live in `E:\study05\runs\sonnet-4-5\` and use slots `E:\w\r20` (smoke) and `r21`-`r38`.
2. **The Sonnet 5.5 runs already made are kept as a labelled pilot, not counted:** smoke + 9 Astropy runs (slots r00-r09) and one Closure_157 arm-S run (slot r10). Sonnet 5.5 is not used for any further Closure run.
3. **Hidden in the agent's container (Closure only; the grading container unchanged):** `framework/projects/Closure/patches/` (the developer's fix and test patches), `modified_classes/` and `loaded_classes/` (class lists, as the blanked properties keys), `project_repos/closure-compiler.git` (the upstream history, fix commit `41acde3e` included) and `project_repos/defects4j-repos.zip`, by empty read-only mounts (`env.start_box(hide=True)`). Defects4J's startup check needs only `project_repos/README`, which stays. Checked 2026-11-18: `defects4j compile`, `test -t`, `export -p tests.trigger`/`cp.test` and the paper's trigger script work, same 12 failures; `defects4j info` shows no bug details. The 5.5 pilot's Closure run had these files readable; its command log is checked for any access (coding row H7).
4. **Harness:** the five-hour readings file is read and written retry-safe (two runner processes overlapped once, the 4.5 runs starting while the 5.5 Closure pilot finished); token columns use the CLI's `modelUsage` (whole run, sub-agents included) instead of the result event's final-turn `usage`.
5. **First-night scope with 4.5 (Allen):** smoke run, the 9 Astropy runs, ONE Closure run (arm S); then Allen decides the remaining Closure runs.

**Not changed:** prompts, arms, measures, coding scheme, time limits, run order.

### Amendment 2 (Allen, 2026-11-18, morning): arm L = U with file locations in the class_graph answers

**Why.** Allen meant the class graph to give structure context like the paper's MAPLE, whose class lookups return the file (and line range) where a class is defined. The D7 index had class names, members and relations only, no file locations. In the frozen U runs so far (3 Astropy, Closure U1) the tool was never called, so no agent ever saw its content; those runs show only that a described, unused tool without locations is ignored.

**Changes.**
1. **Location table** (`scripts/uml/build_locations.py`): for every class in the index, its file (path from the project root, as the agent sees it) and first-last line, from the buggy base tree only; Java ranges by javalang's tokenizer (declaration to closing brace), Python by `ast` (first decorator to `end_lineno`); module-function boxes give the file only. All 887 Closure and 1,226 Astropy index types have an entry; deterministic (`--check`); spot-checked against the source; no leak-check word. Stored at `E:\study05\uml\<bug>\locations.json`, stats in `uml/<bug>/locations-stats.json` (SHA-256 Closure `673173b2…c421`, Astropy `a6ff7ff3…5eba`).
2. **Tool** (`uml_mcp.py`): an optional third argument loads the table; each answer then opens with a "defined in (file:first-last line)" list for every class shown, and the tool description gains one sentence saying so. Without the argument (arm U) the answers, description and server info are byte-identical to the frozen version (checked on 11 calls over both bugs), so the frozen U runs still to come (Closure U2, U3) are unaffected.
3. **Arm L** = U's prompt + the same one sentence (`prompts.GRAPH_NOTE_LOC`; rendered in `prompts/rendered/<bug>_L.txt`); otherwise identical to U: leader block, Agent tool, class_graph tool, neutral wording with no instruction to use the tool (MAPLE's prompt said "use Maple proactively… query Maple first"; that push is a separate question and not part of L).
4. **Runs:** after the frozen 18, `run_all.py --arm-l`: Astropy L k=1-3 (slots r39-r41), then Closure L k=1-3 (r42-r44), Sonnet 4.5, same guards and time limits. Coding rows U1-U3 apply to L.

**Not changed:** the frozen 18 runs, their prompts, tool behaviour and order; measures; time limits.

## Launch log

- 2026-11-18: setup. Claude Code 2.1.289; Docker 27.2.0; images `swebench/sweb.eval.x86_64.astropy_1776_astropy-7606:v2` (3.88 GB), `study05/d4j:2.0.1` (4.05 GB, Ubuntu 22.04, Corretto 8u412, Defects4J v2.0.1). Graph SHA-256: Astropy `8a28ea8e…16f7e3`, Closure `ed608cf3…dd1339`. No agent run.
- 2026-11-18: grader checked end to end (`python env.py verify <bug>`, results in `E:\study05\verify\<bug>\verify.json`). Astropy: buggy repair 0, failed_after 1 (strict 2), RR 0; gold repair 1 (strict 0), RR 1, localization 1, ~10 s per grading. Closure: buggy compiled, failed_after 12, RR 0; developer fix compiled, failed_after 0, repair 1, RR 12, localization 1; 810 s and 930 s per grading (one full suite each).
- 2026-11-18 (freeze, overnight session): pre-checks above; Astropy-8707 set up and rejected (gold fails in its image); Closure base tree rebuilt with the blanked properties keys (new base commit `234e014d`; re-verify of buggy and developer fix started before the freeze, result logged below); class_graph indexes built and the tool tested; plan frozen. Runs: `run_all.py --smoke`, then `--overnight`. Results in `results.md`.
