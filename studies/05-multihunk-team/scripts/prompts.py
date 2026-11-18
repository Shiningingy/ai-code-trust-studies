"""The three arms' prompts. Fixed before any run (plan.md, "Arms"); a change after the freeze is an amendment.

S = the paper's prompt + ENV_NOTE
T = S + LEADER
U = T + GRAPH_NOTE   (the class_graph tool)
L = T + GRAPH_NOTE_LOC (Amendment 2: the class_graph tool with file locations)

ENV_NOTE is the same in every arm: it only explains this harness's tools (the paper's agents had a Bash tool
inside the environment; here commands go through the `run` tool, as in Study 04). LEADER and GRAPH_NOTE avoid
the words the leak check greps for (see check_leaks.py), so a hit in a transcript is the agent's own word.
"""
from bugs import render_paper_prompt

ENV_NOTE = """### Environment notes

- Shell commands, including the scripts and commands named above, run through the `run` tool: it executes bash in the project's Linux environment, with this repository mounted as the working directory (/testbed). There is no network access.
- The file tools (Read, Edit, Write, Glob, Grep) take this directory's own paths, absolute or relative. They cannot open /testbed paths: when a command's output names a file under /testbed, open the same relative path here."""

LEADER = """### How to work

You lead this task and coordinate sub-agents through the Agent tool. Do not edit source files yourself. Your role is to localize the defect, plan the change, and decide each next step. For each step, start one or more sub-agents: for example, one per file or group of related edits you have localized, or one to investigate an open question. Give each sub-agent a self-contained brief: the goal, the relevant files and findings so far, and what to verify. Ask each sub-agent to end its work with a short written handoff: what it changed, what it verified (the commands it ran and their results), and what is still open. Decide the next step from the handoffs. You may read files and run commands yourself to localize the defect and to check results. When the work is complete, confirm the final state and finish."""

GRAPH_NOTE = """### Reference material

The `class_graph` tool returns a UML class graph (PlantUML text) of this project's main source code, produced by a static parser from the code as checked out at the start of the session. Give it a class name or a package/module name, and optionally a number of hops: it shows the matching classes with their fields and method signatures, plus the classes related to them within that many steps (inheritance, field types, uses), with the relationships between them."""

# Amendment 2 (Allen, 2026-11-18): arm L = U whose tool also gives each class's file and line range; one sentence
# added, the same neutral wording otherwise (no instruction to use the tool).
GRAPH_NOTE_LOC = GRAPH_NOTE + " Every class shown also comes with the file (path from the project root) and the line range where it is defined."

# Amendment 3 (Allen, 2026-11-18): arm H = S + a starting instruction naming the third developer-modified file,
# the one no frozen run except T1 found (its two RenamePrototypesTest failures show only in the full suite).
# Closure_157 only. It names the file, not the change.
HINT = {"Closure_157": "src/com/google/javascript/jscomp/RenamePrototypes.java"}
HINT_NOTE = """### Starting point

Before you start, read `{path}`: it is relevant to this defect."""

# Amendment 4 (Allen, 2026-11-18): arm F = S + the full suite's measured duration in this environment (grading
# runs of the 4.5 Closure runs: 777-790 s alone). It states the duration only; the `run` tool's own description
# already gives its timeout default (300 s) and maximum (1800 s). Closure_157 only.
SUITE_NOTE = {"Closure_157": """### Test durations

In this environment the full test suite (`defects4j test`) takes about 13 minutes to run; `./run_bug_exposing_tests.sh` takes about 30 seconds."""}

ARMS = ("S", "T", "U", "L", "H", "F")


def build(bug_id, arm):
    parts = [render_paper_prompt(bug_id).rstrip("\n"), ENV_NOTE]
    if arm in ("T", "U", "L"):
        parts.append(LEADER)
    if arm == "U":
        parts.append(GRAPH_NOTE)
    if arm == "L":
        parts.append(GRAPH_NOTE_LOC)
    if arm == "H":
        parts.append(HINT_NOTE.format(path=HINT[bug_id]))
    if arm == "F":
        parts.append(SUITE_NOTE[bug_id])
    return "\n\n".join(parts) + "\n"
