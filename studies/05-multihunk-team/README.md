# Study 05: do sub-agents help on the multi-hunk bugs no single agent fixed?

**Status: complete (runs ended 2026-11-19).** 30 counted runs on Sonnet 4.5 (the paper's model) in Claude Code 2.1.289, plus a smoke run; the first Sonnet 5.5 runs are kept as a labelled pilot. Report: [results.md](results.md). Hand coding (coding-scheme.md) has not been done.

## Result in short

- **Astropy-7606: 12 of 12 repaired**, every run with the same one-hunk patch. The paper's "unsolved" for this bug is a grading artefact: one PASS_TO_PASS test is printed under a different parameter name, so even the developer's patch fails SWE-bench's rule (reported upstream since 2024).
- **Closure_157: 2 of 18 repaired** (frozen S 0/3, T 1/3, U 0/3; follow-up arms L 0/3, H 0/3, F 1/3). The main fix makes two `RenamePrototypesTest` tests fail that pass on the buggy code, and only the full suite (13-17 min here) shows them. Both repairs came from runs that let the full suite finish; none of the 14 runs that cut it off repaired. Stating the suite's duration (arm F) made the agent wait in 3 of 3 runs, but only 1 of 3 then fixed the new failures; one called them "pre-existing" without checking.
- Sub-agents did not decide the outcome, and the `class_graph` tool was called 0 times in all 12 runs that had it.

Three runs per arm and bug: the report describes patterns and cases, not rates.

## The question

"Beyond Accuracy: Behavioral Dynamics of Agentic Multi-Hunk Repair" (TOSEM 2026, arXiv 2511.11012v3) ran four coding-agent CLIs, one trajectory per bug, with no planner or sub-agents. Two bugs that none of them repaired are replayed here with Claude Code, three times per arm:

- **S**: the paper's own prompt, one agent, sub-agent tool off (the control);
- **T**: S plus a leader block: the leader localizes and plans, sub-agents edit and test, each returns a short written handoff;
- **U**: T plus a `class_graph` tool (MCP) that returns a static UML class graph of the buggy code;
- follow-ups added during the runs (plan.md Amendments 2-4): **L** = U whose graph also gives each class's file and line range; **H** = S plus "read `RenamePrototypes.java` first"; **F** = S plus "the full suite takes about 30 minutes" (H and F on Closure only).

Bugs: **Astropy-7606** (SWE-bench Verified; all four agents found the file, none repaired it) and **Closure_157** (Defects4J; none localized it; the paper's Section 5 traces two new failures to an unmodified third file).

## Layout

- [results.md](results.md): pre-run checks, training-data exposure, the run table, readings, findings F1-F16, what failed or differs from the plan, framing.
- [plan.md](plan.md): question, arms, measures, harness differences from the paper, amendments, launch log.
- [coding-scheme.md](coding-scheme.md): the hand-coding table for trajectories, fixed before any run.
- [prompts/](prompts/): the paper's two templates (verbatim) and `rendered/<bug>_<arm>.txt`, the exact prompt each arm got.
- [uml/](uml/): the graphs the `class_graph` tool served (`graph.puml`), their sizes and the commands that built them.
- [scripts/](scripts/): `bugs.py` (bug definitions, paper prompt rendering), `prompts.py` (arm texts), `env.py` (base trees, workspaces, containers, `verify`), `agent.py` (one run), `run_all.py` (run order and modes), `grade.py` (the paper's measures), `check_leaks.py`, `similarity.py` (patch vs developer fix), `summarize.py` (the run table), `llm.py` and `box_mcp.py` (from Study 04, adapted); `uml/` (`uml_py.py`, `uml_java.py`, `build_uml.py`, `build_index.py`, `build_locations.py`, `uml_mcp.py`); `docker/d4j/Dockerfile` (Defects4J v2.0.1 on Corretto 8u412).

Run data (transcripts, patches, gradings, about 2 GB) is not in the repository.

## Running it

Everything large lives on E: (`E:\study05`: replication package clone, base trees, venv, runs; Docker data on E:). Agents run in neutral folders `E:\w\rNN`.

```
docker build -t study05/d4j:2.0.1 scripts/docker/d4j
docker pull swebench/sweb.eval.x86_64.astropy_1776_astropy-7606@sha256:f4bcd149eb4cfcd9017d798f2b5b40a0b4c85c62390667f2b2f751cff29a184f
git clone https://github.com/agentic-se/agentic-multihunk-repair E:\study05\src\agentic-multihunk-repair   # then checkout 5cdb227
cd scripts
python env.py prepare Closure_157          # base trees (idempotent)
python env.py prepare astropy__astropy-7606
python env.py verify astropy__astropy-7606 # buggy fails, developer fix passes (no model call)
python env.py verify Closure_157
E:\study05\venv\Scripts\python.exe uml\build_uml.py Closure_157 ..\uml\Closure_157   # needs javalang 0.13.0
python run_all.py --plan                   # the run order
python run_all.py --dry-run                # every prompt and command, no model call
python run_all.py --go                     # the frozen 18 runs; --extra for arms L, H, F
python summarize.py                        # the run table
```
