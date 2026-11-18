"""The three arms' prompts. Fixed before any run (plan.md, "Arms"); a change after the freeze is an amendment.

S = the paper's prompt + ENV_NOTE
T = S + LEADER
U = T + GRAPH_NOTE   (and class-graph.puml in the workspace)

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

The file `class-graph.puml` in this directory is a UML class graph (PlantUML text) of part of this project's code as checked out; its first lines state the scope. It lists classes with their fields and method signatures, inheritance, and which classes use which. A static analysis tool generated it."""

ARMS = ("S", "T", "U")


def build(bug_id, arm):
    parts = [render_paper_prompt(bug_id).rstrip("\n"), ENV_NOTE]
    if arm in ("T", "U"):
        parts.append(LEADER)
    if arm == "U":
        parts.append(GRAPH_NOTE)
    return "\n\n".join(parts) + "\n"
