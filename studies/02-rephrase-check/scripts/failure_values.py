"""The runtime half of definition B: one line saying how an accepted test failed.

Read from the last failing run AssertFlip logged. Text only, nothing is executed.
"""
import json
import re

ANSI = re.compile(r"\x1b\[[0-9;]*m")
EXCEPTION = re.compile(r"^[\w.]*(Error|Exception|Warning|Failure|Failed)\b")


def failure_line(output):
    """pytest's first E line, else the last exception line of a unittest or sympy run."""
    lines = ANSI.sub("", output).splitlines()
    marked = [x[1:].strip() for x in lines if re.match(r"^E\s", x)]
    if marked:
        return marked[0]
    found = [x.strip() for x in lines if EXCEPTION.match(x.strip())]
    return found[-1] if found else None


def normalise(line):
    """Drop what changes between identical failures: addresses, temp paths, the run's file name."""
    line = re.sub(r"0x[0-9a-f]+", "0xX", line)
    line = re.sub(r"\btest_[a-z0-9]{8}\b", "test_FILE", line)
    line = re.sub(r"/tmp/\S+", "/tmp/X", line)
    return re.sub(r"\s+", " ", line).strip()


def failure_of(attempts_path):
    """A value for Run.failure, or None if the run logged no failure line."""
    with open(attempts_path, encoding="utf-8") as f:
        attempts = json.load(f)
    logged = [a for a in attempts if a.get("phase") == "invert_to_failing" and "error" in a]
    line = failure_line(str(logged[-1]["error"])) if logged else None
    return (normalise(line),) if line else None
