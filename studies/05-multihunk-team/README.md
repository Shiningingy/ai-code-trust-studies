# Study 05: do sub-agents help on the multi-hunk bugs no single agent fixed?

**Status: setup only. No agent run has been made.** The plan ([plan.md](plan.md)) is a draft waiting for Allen's decisions and approval; runs spend his Claude quota and start only after that.

## The question

"Beyond Accuracy: Behavioral Dynamics of Agentic Multi-Hunk Repair" (TOSEM 2026, arXiv 2511.11012v3) ran four coding-agent CLIs, one trajectory per bug, with no planner or sub-agents. Two bugs that none of them repaired are replayed here with Claude Code on Sonnet 5.5, three times each, in three arms:

- **S**: the paper's own prompt, one agent, sub-agent tool off (recommended control, pending Allen's OK);
- **T**: the same prompt plus a leader block: the leader localizes and plans, sub-agents edit and test, each returns a short written handoff;
- **U**: T plus a static UML class graph of the buggy code in the workspace.

Bugs: **Astropy-7606** (SWE-bench Verified; all four agents found the file, none repaired it) and **Closure_157** (Defects4J; none localized it; the paper's Section 5 traces two new failures to an unmodified third file).

## Setup findings worth knowing before any run

- Astropy-7606: with the developer's own patch, SWE-bench's grading rule still says "not resolved" in the pinned image, because one PASS_TO_PASS test is printed under a different parameter name (`[unit0]` vs the record's `[]`). The paper's four agents all show exactly the failure count this artefact produces. Both verdicts are reported (plan.md, "The two bugs").
- Closure_157: the Defects4J checkout's git history contains the fixed version, and the paper's Claude Code run read parts of it (`git diff` between the Defects4J commits). This study's trees have a fresh history, so its runs are harder than the paper's.

## Layout

- [plan.md](plan.md): question, arms, measures, harness differences from the paper, budget, decisions for Allen, launch log.
- [coding-scheme.md](coding-scheme.md): the hand-coding table for trajectories, fixed before any run.
- [prompts/](prompts/): the paper's two templates (verbatim) and `rendered/<bug>_<arm>.txt`, the exact prompts each arm gets.
- [uml/](uml/): the arm-U graphs (`graph.puml`), their sizes per scoping tier and the command that built them.
- [scripts/](scripts/):
  - `bugs.py` (bug definitions, paper prompt rendering), `prompts.py` (arm texts), `env.py` (base trees, workspaces, containers, `verify`), `agent.py` (one run), `run_all.py` (the 18 runs, `--plan`, `--dry-run`, `--go`), `grade.py` (the paper's measures), `check_leaks.py`, `llm.py` and `box_mcp.py` (from Study 04, adapted);
  - `uml/` (`uml_py.py`, `uml_java.py`, `build_uml.py` with the scope rule);
  - `docker/d4j/Dockerfile` (Defects4J v2.0.1 on Corretto 8u412).

## Running it

Everything large lives on E: (`E:\study05`: replication package clone, base trees, venv, runs; Docker data disk at `E:\DockerDesktopWSL`). Agents run in neutral folders `E:\w\r01`..`r18`.

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
python run_all.py --dry-run --with-control # every prompt and command, no model call
python run_all.py --go --with-control      # ONLY after Allen approves plan.md
```

## Disk (measured 2026-11-18)

`E:\study05` 0.97 GB (clone 147 MB, base trees 391 MB, venv 369 MB, scratch 60 MB); Docker images 7.9 GB (Astropy 3.88 GB, Defects4J 4.05 GB), on E:. This folder on G: is under 1 MB. Each run folder adds about 120 MB (Astropy) or 80 MB (Closure, with build output): about 1.8 GB for all 18.
