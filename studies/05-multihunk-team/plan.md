# Study 05 plan: do sub-agents help on multi-hunk bugs that no single agent fixed?

**Status: draft, setup only. No agent run has been made.** The plan freezes when Allen approves it; the commit that records his approval is the freeze, and its hash goes in the Launch log at the end. Changes after that go under Amendments, with a date and a reason.

Set up on 2026-11-18 (Claude Code 2.1.289, model `claude-sonnet-5-5`). Items marked **[Allen]** need his decision before the freeze (collected in "Decisions for Allen").

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

**Finding that changes how Astropy-7606 must be scored.** The SWE-bench record's PASS_TO_PASS list names `test_compose_roundtrip[]`, but pytest in the pinned image names that case `test_compose_roundtrip[unit0]`. Under SWE-bench's grading rule (PASS_AND_FAIL: a test missing from the log counts as failed), **even the developer's gold patch is "not resolved"** here: failed after = 1. The paper's four agents all show failed after = 1, which is what this artefact produces for a correct fix. So "no agent repaired Astropy-7606" may be partly or wholly a grading artefact; the paper's published data do not include the HunkSWE patches, so this cannot be checked from the package. This study reports both verdicts: `repair_strict` (SWE-bench's rule, comparable with the paper) and `repair` (the renamed case matched by its printed name, `bugs.py: test_aliases`). **[Allen]** confirm `repair` (aliased) as the primary Astropy outcome.

## Arms

Same model, CLI version, tools, budget and harness in every arm; the prompts differ only by appended blocks. Exact texts: `scripts/prompts.py`; rendered prompts for both bugs: `prompts/rendered/<bug>_<arm>.txt` (from `python scripts/run_all.py --dry-run --with-control`).

- **S (single agent, recommended control, pending Allen's OK):** the paper's prompt template, rendered exactly as the paper's runner renders it (`prompts/paper_hunk4j_prompt.md`, `prompts/paper_hunkswe_prompt.md`, verbatim from the package with line endings normalised), plus one environment note that explains this harness's tools. The sub-agent tool is disabled (`--tools` omits `Agent`). Sonnet 4.5 numbers from the paper are not comparable with Sonnet 5.5 and a newer CLI, so without S there is no baseline for T and U. **[Allen]** approve S.
- **T (delegation):** S's prompt + a leader block ("How to work"): the leader does not edit source itself; it localizes, plans and decides the next step; it starts one or more sub-agents through the Agent tool (e.g. one per localized file or group of edits, or one to investigate a question); each sub-agent ends with a short written handoff (what it changed, what it verified with which commands, what is still open); the leader decides from the handoffs, may read files and run commands to localize and check, and confirms the final state. Wording is neutral (it avoids the leak-check words, see below) and fixed before any run.
- **U (delegation + class graph):** T's prompt + one neutral block saying that `class-graph.puml` in the directory is a UML class graph (PlantUML) of part of the code as checked out, with its scope in its first lines, listing classes, fields, method signatures, inheritance and which classes use which, generated by a static analysis tool. The file is placed in the workspace root, untracked and excluded from the patch.

The leader's "do not edit source files yourself" is an instruction, not a tool restriction: removing Edit from the leader would remove it from sub-agents too. Compliance is coded by hand (coding scheme, T/U rows).

## Arm U: the class graph

Rules (Allen, 2026-11-18):

1. **Built deterministically by a static tool from the buggy checkout only**, never from the fixed version or the gold patch, and never by a model. Python: `scripts/uml/uml_py.py` (standard-library `ast`; pyreverse was not used so that the output format and the scope rule are the same for both languages). Java: `scripts/uml/uml_java.py` (`javalang` 0.13.0). Output: PlantUML text. Re-running gives byte-identical files (`build_uml.py --check`; SHA-256 in `stats.json`).
2. **Contents:** classes (Python: plus one `<<module>>` box per module listing its top-level functions), fields, method signatures with visibility, inheritance/implements, associations (a field whose type, or Python: whose assigned constructor, is a repo class) and dependencies (any other use of a repo class: parameters, returns, locals, `new`, static calls, constants such as `Token.STRING`). Relationships are the point: the paper's MAPLE tool had lookups only.
3. **Scope rule**, fixed here (`scripts/uml/build_uml.py`). Budget: **50,000 approximate tokens** (characters / 4; the Read tool returns about 25k tokens per call, so the graph is at most two reads and is greppable). Take the first tier that fits:
   1. the whole main source tree (tests excluded);
   2. the package(s) holding the failing tests' classes (Java: the test class's package; Python: the package holding the test module's `tests/` directory), non-recursive;
   3. the repo types named in the failing test source files, plus one hop (their supertypes, field types and every repo type they use);
   4. the repo types named in the failing test source files only.

   The rule reads only the buggy tree and the failing-test names. **Leak note:** a test-derived scope points at code near the failing tests, which is a localization hint. It is limited to what the agent already has or gets in one step: SWE-bench's prompt lists the FAIL_TO_PASS test, and for Defects4J the paper's `run_bug_exposing_tests.sh` prints the failing test classes on its first run; the rule never looks at the gold patch's file list. Whether the developer-modified files fall inside the scope was checked only after the rule was fixed and the graphs built, and is reported below for transparency; the rule was not changed after that check.
4. **Same graph for all three U runs of a bug**, stored at `uml/<bug>/graph.puml` with `stats.json` (every tier's size, the tier chosen, SHA-256) and `command.txt`.
5. Coding scheme rows U1-U3 record whether and when the leader or a sub-agent opened the graph and whether a decision cited it.

**Graphs built (2026-11-18):**

| Bug | Tier 1 (whole tree) | Tier 2 (test packages) | Tier 3 (named + 1 hop) | Tier 4 (named only) | Chosen |
|---|---|---|---|---|---|
| Astropy-7606 | 1,226 boxes, 582k chars, ~146k tokens | `astropy.units`: 22 classes + 11 module boxes, 489 lines, 18k chars, **~4.5k tokens** | (not needed) ~6.1k tokens | n/a | **tier 2** |
| Closure_157 | 887 types, 17,277 lines, 1.11M chars, ~278k tokens | `jscomp` + `jscomp.parsing`: 679 types, ~214k tokens | 267 types, ~107k tokens | 33 types, 1,747 lines, 78k chars, **~19.5k tokens** | **tier 4** |

After-the-fact coverage (developer-modified files inside the graph): Astropy, `core.py` yes (both buggy classes, `UnitBase` and `UnrecognizedUnit`, are in it); Closure, `IRFactory` yes, `CodeGenerator` and `RenamePrototypes` no (edges to types outside the scope are dropped, so `CodePrinter ..> CodeGenerator` does not appear). **[Allen]** A variant that keeps edges from in-scope types to out-of-scope types as name-only stubs would show those two classes; I saw the coverage before thinking of it, so adopting it would be a post-hoc change and should be your call, recorded as such.

## Design and order

2 bugs × 3 arms × 3 runs = **18 runs** (12 without S). One run at a time. Rounds k = 1, 2, 3; in each round Astropy first, then Closure; within a bug the arms in an order shuffled with seed 20261118 + k (`run_all.py --plan`):

k=1: Astropy U, S, T; Closure U, S, T · k=2: Astropy S, U, T; Closure S, U, T · k=3: Astropy T, S, U; Closure T, S, U.

Each run gets its own neutral folder `E:\w\r01` … `E:\w\r18`, kept afterwards for hand coding. No replacements: a run that times out or refuses is scored as it stands. A run cut off by a usage limit is discarded and repeated from a fresh tree (not counted); an infrastructure error is repeated up to twice.

## Harness (reused from Study 04) and how it differs from the paper

Pattern from Study 04 (`studies/04-review-intent/scripts/agent.py`, `env.py`, `llm.py`, `box_mcp.py`): `claude -p` on the subscription, isolated from the local setup (no settings sources, user CLAUDE.md excluded, auto-memory off, CLAUDE*/ANTHROPIC* env vars dropped); the agent edits a host copy with file tools and runs every command through one MCP tool, `run`, inside a per-bug Docker container with no network and the tree mounted at `/testbed`; a ledger row per call; usage guards; full stream-json transcripts.

| | Paper (Claude Code) | This study |
|---|---|---|
| CLI / model | 2.0.13 / Sonnet 4.5 (`claude-sonnet-4-5-20250929`; the HunkSWE runner documents `--model` but its command line does not pass it) | **2.1.289 pinned** (`llm.PIN`; a different installed version stops the run) / `claude-sonnet-5-5`, effort `medium` **[Allen]** |
| Prompt delivery | template written to `CLAUDE.md`, `-p "Read and execute the instructions listed in CLAUDE.md."` | the same rendered text sent as the prompt itself; no CLAUDE.md. Reason: sub-agents may load a CLAUDE.md, which would hand every sub-agent the whole task and the leader block, against the context-hygiene point of T/U. **[Allen]** |
| Tools | everything, `--dangerously-skip-permissions`; Bash in the environment (Hunk4J: on the host; HunkSWE: inside the container, network on). Claude used Bash, Edit, Glob, Grep, Read, TodoWrite; no sub-agent calls in the published Closure_157 counts | Read, Edit, Write, Glob, Grep, TodoWrite + `run` (bash in the no-network container); `Agent` added in T/U only; no host Bash, no web. The init event is checked live: wrong tool set → process killed before the model is called |
| Git history | Defects4J checkout keeps the fixed version as the parent commit; the paper's Claude Closure_157 run used it (`git log | grep D4J_Closure_157`, `git diff 822acb61 3ff39c0b -- …IRFactory.java`, `git show`) | **removed**: the Closure tree is the checkout without `.git`, in a fresh one-commit repo. SWE-bench's `/testbed` history ends at the base commit (checked), so it is kept, with test_patch committed as HEAD as the paper's harness does. Our runs are therefore harder than the paper's on Closure |
| Localization hint | `defects4j.build.properties` in the checkout names the 3 modified classes (`d4j.classes.modified`) | kept (Defects4J's commands read the file; the paper's agents had it). Coding row H8 records whether an agent read it **[Allen]** |
| Test scripts | `run_bug_exposing_tests.sh`, `run_all_tests_trace.sh` (Hunk4J); `run_failing_tests.sh`, `run_all_tests.sh` + `.swebench/` (HunkSWE) | the same files (line endings normalised to LF; `sdk use java …` is a no-op in the image, which has only Corretto 8u412) |
| Time limit | not stated in the paper; HunkSWE runner default 30 min | **90 min** wall clock, every arm (Closure's full suite takes about 13 min on the Windows bind mount); longest single `run` command 30 min **[Allen]** |
| Runs per bug | 1 | 3 per arm |

## Measures (fixed before any run)

Paper's own (Section 2.2; equation numbers as in v3 HTML, where regression reduction is Eq. 6, not Eq. 5), implemented in `scripts/grade.py` on a fresh copy of the base tree with the captured patch, in a no-network container:

- **Localization (Eq. 3):** 1 if the developer-modified files ⊆ the files the agent's patch modifies; 0 otherwise, and 0 if the patch is empty or does not compile. (The package's own `generate_localization_ability_*.py` computes it from edit accuracy instead; this study uses Eq. 3 as printed.)
- **Compilation (Eq. 4):** non-empty patch that applies and compiles. Java: `defects4j compile`. Python: patch applies and every changed `.py` file passes `py_compile`.
- **Repair accuracy (Eq. 5):** non-empty patch and no failing test afterwards. Java: `defects4j test` reports 0 failing tests (the buggy version's only failures are the 12 trigger tests, so this equals "trigger tests pass and no previously passing test fails"). Python: all FAIL_TO_PASS and PASS_TO_PASS pass (SWE-bench "resolved"), test files reset to test_patch first as SWE-bench does; reported as `repair` (aliased name, primary) and `repair_strict`.
- **Regression reduction (Eq. 6):** failed_before − failed_after, undefined if compilation fails; failed_before as in the paper's data (Closure 12 = number of trigger tests; Astropy 1).
- **Tokens:** from the run's `result` event: input, cache creation, cache read, output (the paper's `token_and_duration` columns), plus `modelUsage` per model (covers sub-agents) and `total_cost_usd` as the CLI reports it.
- **Runtime:** wall clock of the `claude -p` process, and the CLI's `duration_ms`.

Also recorded: changed files, new untracked files (not part of the patch, as in the paper's `git diff HEAD`), trigger tests still failing, new failures, number of turns, every `run` command (`box.jsonl`).

**Hand coding** (Allen, per trajectory, scheme in `coding-scheme.md`, defined before any transcript exists): first open and first edit of each developer-modified file (step index), direction of the first edit, reverts of a correct change, where the failure arose, and for T/U the number of sub-agents, handoff information loss and leader compliance; for U, graph use.

**Analysis:** descriptive. Per-run table (18 rows) and per-cell counts out of 3 for repair, localization and compilation; medians of RR, tokens and runtime. A difference is called "consistent" only if it holds in at least 2 of 3 runs per bug; no significance tests at n = 3.

## Leak check

`claude -p` puts the working directory's path into the model's context (Study 04). Run folders are `E:\w\rNN`; the MCP server script and its log are copied to `E:\w\tools` so no study path appears even in a process argument. The prompts contain none of the checked words; `check_leaks.py` scans prompt, init event (cwd, memory paths) and transcript after every run for: study, multihunk, multi-hunk, beyond accuracy, polyhunk, hunk4j, hunkswe, hunk-swe, team, paper, nashid, mesbah, gallaba, hassan, agentic-se, tosem, 2511.11012, study05, s05. Transcript hits are reviewed by hand (code the agent reads may contain "paper" or "team" legitimately); a hit in the prompt or init event stops the study.

## Budget, time and disk (estimates; measured values go in the Launch log)

- **Disk (measured 2026-11-18):** see README "Disk". All data on E: (Docker images, clone, base trees, run folders); G: holds only this folder.
- **Time per run:** Astropy, paper's Claude 170 s; expect 5-15 min for S and 10-30 min for T/U. Closure, paper's Claude 17 min with a native filesystem; here one full suite takes about 13 min and the trigger script about 3 min (compile included), so expect 30-60 min for S and up to the 90-min limit for T/U. All 18 runs: roughly 12-20 hours, spread over several five-hour windows.
- **Quota:** from Study 04's ledger, a Sonnet 5.5 agent run used about 4.4% of the five-hour window and 0.40% of the seven-day window per million total tokens (an upper bound: parallel streams inflate it). Paper-sized runs: Astropy ~0.9M tokens → ~4% five-hour, ~0.4% weekly; Closure ~15M tokens → up to ~60% of a five-hour window and ~6% of the week per run, more if sub-agents re-read code. Nine Closure runs could approach half a week's quota. Guards: stop at 75% seven-day (`STUDY_WEEK_STOP`), start an Astropy run only below 80% five-hour and a Closure run only below 35%. **Recommendation:** run the 9 Astropy runs first, read the measured per-run usage off the ledger (runs are sequential, so the readings are clean), then decide on Closure.

## Decisions for Allen (before the freeze)

1. Approve arm S as the control (recommended).
2. Astropy primary outcome = `repair` with the test-name alias; `repair_strict` reported alongside.
3. Prompt sent directly instead of via CLAUDE.md.
4. Effort `medium` (Study 04) vs the CLI default.
5. Time limit 90 min for every arm.
6. Keep `defects4j.build.properties` (paper-faithful, a localization hint) or strip its `d4j.classes.*` lines.
7. Closure graph: keep tier 4 as built, or adopt the stub-edge variant (post-hoc, see Arm U).
8. Run Astropy first and decide Closure after seeing measured quota.

## Amendments

(none)

## Launch log

- 2026-11-18: setup. Claude Code 2.1.289; Docker 27.2.0; images `swebench/sweb.eval.x86_64.astropy_1776_astropy-7606:v2` (3.88 GB), `study05/d4j:2.0.1` (4.05 GB, Ubuntu 22.04, Corretto 8u412, Defects4J v2.0.1). Graph SHA-256: Astropy `8a28ea8e…16f7e3`, Closure `ed608cf3…dd1339`. No agent run.
- 2026-11-18: grader checked end to end (`python env.py verify <bug>`, results in `E:\study05\verify\<bug>\verify.json`). Astropy: buggy repair 0, failed_after 1 (strict 2), RR 0; gold repair 1 (strict 0), RR 1, localization 1, ~10 s per grading. Closure: buggy compiled, failed_after 12, RR 0; developer fix compiled, failed_after 0, repair 1, RR 12, localization 1; 810 s and 930 s per grading (one full suite each).
