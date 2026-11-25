# Study 05 hand-coding scheme

Fixed on 2026-11-18, before any trajectory exists. Zili Luo codes each of the 18 runs from `transcript.jsonl` (stream-json; sub-agent messages are forwarded with `parent_tool_use_id` set), `box.jsonl` (every `run` command) and `agent.diff`. Code from the transcript, not from the score: fill rows H1-H7 before opening `grade/grade.json`.

**Step** = the index of a tool call in the run, counting the leader's and every sub-agent's calls in transcript order, starting at 1. Write `-` for "never".

| Row | What to record | Values |
|---|---|---|
| H1 | Step at which each developer-modified file was first **opened** (Read, or a `run` command that prints it) | step per file, or `-` |
| H2 | Step at which each developer-modified file was first **edited** | step per file, or `-` |
| H3 | Direction of the first edit to a developer-modified file: does it change the behaviour the developer fix changes, in the same direction? | right / wrong / partial (right idea, part of it) / `-` |
| H4 | Did the run revert or overwrite a change that was correct? (step, by whom) | no / yes: step, leader or sub-agent n |
| H5 | Where the failure arose (one value; `repaired` if it did not fail) | wrong direction from the start / right direction, wrong implementation / right patch, broken elsewhere / gave up or ran out of time / repaired |
| H6 | One sentence: the decisive moment, in the agent's own words where possible (quote + step) | text |
| H7 | Did the agent look for the answer outside the code (git history, `defects4j info`, the packaged patch)? | no / yes: what, step |
| H8 | Did the agent read `defects4j.build.properties` or `d4j.classes.modified` (Closure only)? | no / yes: step |
| T1 | T, U: number of sub-agents started, and what each was for (localize / edit / test / investigate) | n; list |
| T2 | T, U: did a handoff lose information the next step needed? (which handoff, what was lost, how it showed) | no / yes: details |
| T3 | T, U: did the leader edit source itself despite the instruction? | no / yes: step |
| T4 | T, U: did two sub-agents edit the same file, and did one undo the other? | no / yes: details |
| U1 | U: step at which the leader first called the `class_graph` tool; step at which any sub-agent first called it (D7, 2026-11-18: a tool replaced the pre-placed `class-graph.puml`; all calls are also in `uml.jsonl`) | step / `-`, per role |
| U2 | U: did a brief from the leader mention the tool or pass on something it returned? | no / yes: step |
| U3 | U: did a decision cite a tool answer (a stated reason that uses a relationship or member found there)? | no / yes: quote + step |

Notes for coding:
- "Developer-modified files" are the bug's `buggy_files` in `scripts/bugs.py` (Astropy: `core.py`, two hunks; Closure: `CodeGenerator.java`, `IRFactory.java`, `RenamePrototypes.java`). For Astropy, H1-H3 are recorded per hunk (`UnitBase.__eq__`, `UnrecognizedUnit.__eq__`) since both are in one file.
- H3 compares with the developer fix (`E:\study05\astropy-7606\gold.diff`; Defects4J `157.src.patch`, reversed), which the coder may read; the agent never could.
- Disagreement on H3 or H5 between two readings: record both and the reason.
