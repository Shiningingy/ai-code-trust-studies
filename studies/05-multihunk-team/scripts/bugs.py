"""The two bugs, as the paper's replication package defines them (agentic-se/agentic-multihunk-repair @ 5cdb227).

Everything the agent sees comes from that package: the prompt templates (vendored verbatim in ../prompts/,
line endings normalised to LF), the bug report fields, and the test-trace scripts. Fields used only for
scoring (buggy files, gold patch) are marked SCORING ONLY and never reach a prompt or a workspace.
"""
import json
from pathlib import Path

STUDY = Path(__file__).resolve().parent.parent
PROMPTS = STUDY / "prompts"
DATA = Path(r"E:\study05")
SRC = DATA / "src" / "agentic-multihunk-repair"  # clone of the replication package
BASE = DATA / "base"

# Closure-157: Hunk4J config/multihunk.json -> bug_report (title is empty; the paper's runner substitutes
# "title unavailable"). Trigger tests: Defects4J v2.0.1 tests.trigger (identical to the config's 12).
CLOSURE_TRIGGER = [
    "com.google.javascript.jscomp.CodePrinterTest::testObjectLit2",
    "com.google.javascript.jscomp.CodePrinterTest::testObjectLit3",
    "com.google.javascript.jscomp.CodePrinterTest::testGetter",
    "com.google.javascript.jscomp.CodePrinterTest::testSetter",
    "com.google.javascript.jscomp.FunctionNamesTest::testFunctionsNamesAndIds",
    "com.google.javascript.jscomp.RenamePropertiesTest::testPrototypePropertiesAsObjLitKeys2",
    "com.google.javascript.jscomp.RenamePropertiesTest::testPrototypePropertiesAsObjLitKeys3",
    "com.google.javascript.jscomp.SimpleDefinitionFinderTest::testDefineNumber",
    "com.google.javascript.jscomp.parsing.IRFactoryTest::testObjectLiteral6",
    "com.google.javascript.jscomp.parsing.IRFactoryTest::testObjectLiteral7",
    "com.google.javascript.jscomp.parsing.IRFactoryTest::testObjectLiteral8",
    "com.google.javascript.jscomp.parsing.ParserTest::testObjectLiteralDoc1",
]


def swe_record(bug_id):
    return json.loads((BUGS[bug_id]["data"] / "record.json").read_text(encoding="utf-8"))


BUGS = {
    "Closure_157": {
        "kind": "d4j",
        "image": "study05/d4j:2.0.1",
        "checkout": BASE / "closure-157",       # defects4j checkout -p Closure -v 157b (its .git holds the fix: never copied)
        "base": BASE / "closure-157-tree",      # the tree every run starts from (fresh git, see env.prepare_d4j)
        "template": PROMPTS / "paper_hunk4j_prompt.md",
        "title": "",
        "description": "Numbers and quoted property names reject for get and set properties.",
        "failing_tests": CLOSURE_TRIGGER,
        "failed_before": 12,                    # the paper's failed_test_prior = number of triggered tests
        "harness_files": ["run_bug_exposing_tests.sh", "run_all_tests_trace.sh"],
        # D6 (2026-11-18): these defects4j.build.properties keys name the developer-modified classes. The file
        # cannot be removed (Defects4J's check.properties target fails without it, so compile/test/export break),
        # so in the run tree the keys are kept but emptied; grading restores the original file.
        "props_blank": ["d4j.classes.modified", "d4j.classes.relevant"],
        # SCORING ONLY
        "buggy_files": ["src/com/google/javascript/jscomp/CodeGenerator.java",
                        "src/com/google/javascript/jscomp/parsing/IRFactory.java",
                        "src/com/google/javascript/jscomp/RenamePrototypes.java"],
    },
    "astropy__astropy-7606": {
        "kind": "swe",
        "image": "swebench/sweb.eval.x86_64.astropy_1776_astropy-7606:v2",
        "image_digest": "sha256:f4bcd149eb4cfcd9017d798f2b5b40a0b4c85c62390667f2b2f751cff29a184f",
        "data": DATA / "astropy-7606",
        "checkout": BASE / "astropy-7606",      # /testbed copied out of the image (history ends at base_commit)
        "base": BASE / "astropy-7606-tree",     # + test_patch committed as HEAD, as the paper's harness does
        "template": PROMPTS / "paper_hunkswe_prompt.md",
        "package": "astropy",
        "failing_tests": ["astropy/units/tests/test_units.py::test_unknown_unit3"],
        "test_cmd": "pytest -rA -vv -o console_output_style=classic --tb=no",  # swebench 4.1.0 TEST_ASTROPY_PYTEST
        "test_directives": "astropy/units/tests/test_units.py",
        "failed_before": 1,                     # the paper's failed_test_prior (claude_repair_ability.csv)
        # The record's PASS_TO_PASS names test_compose_roundtrip[] but pytest in this image names that case
        # [unit0]; under SWE-bench's PASS_AND_FAIL rule the missing name counts as failed, so even the gold patch
        # is "not resolved" (verified 2026-11-18). grade.py reports both the strict verdict and the aliased one.
        "test_aliases": {"astropy/units/tests/test_units.py::test_compose_roundtrip[]":
                         "astropy/units/tests/test_units.py::test_compose_roundtrip[unit0]"},
        "harness_files": ["run_failing_tests.sh", "run_all_tests.sh", ".swebench/"],
        # SCORING ONLY
        "buggy_files": ["astropy/units/core.py"],
        # Pre-check 2026-11-18 (results.md): with the official swebench 4.1.0 grader the gold patch is
        # "not resolved" here (failed count 1, the [] name); the paper's four agents all have failed count 1,
        # i.e. each made the failing test pass with no regression. The planned swap (astropy-8707) does not
        # reproduce either (below), so 7606 is KEPT and flagged, as the overnight rule says.
    },
    # NOT USED. The other HunkSWE bug all four agents localized and none repaired (Table 5). Set up 2026-11-18 as the
    # planned swap, but in its pinned image the gold patch also fails (all TestHeaderFunctions tests ERROR in setup:
    # pytest turns the nose-style setup() deprecation warning into an error), failed count 8 = buggy = the paper's
    # Claude/Codex/Gemini count; official swebench 4.1.0 gives RESOLVED_NO for gold. So it cannot be repaired here.
    "astropy__astropy-8707": {
        "kind": "swe",
        "image": "swebench/sweb.eval.x86_64.astropy_1776_astropy-8707:v2",
        "image_digest": "sha256:55e63ac83d4ab4a2e1e584adbd7b47f5a2fd43d131fe26d0e12103024915f13b",
        "data": DATA / "astropy-8707",          # record.json from the package's swe_bench.jsonl, gold.diff, test.diff
        "checkout": BASE / "astropy-8707",
        "base": BASE / "astropy-8707-tree",
        "template": PROMPTS / "paper_hunkswe_prompt.md",
        "package": "astropy",
        "failing_tests": ["astropy/io/fits/tests/test_header.py::TestHeaderFunctions::test_card_from_bytes"],
        "test_cmd": "pytest -rA -vv -o console_output_style=classic --tb=no",
        "test_directives": "astropy/io/fits/tests/test_header.py",
        "failed_before": 1,                     # the paper's failed_test_prior (claude_repair_ability.csv)
        "test_aliases": {},
        "harness_files": ["run_failing_tests.sh", "run_all_tests.sh", ".swebench/"],
        # SCORING ONLY
        "buggy_files": ["astropy/io/fits/card.py", "astropy/io/fits/header.py"],
    },
}


def render_paper_prompt(bug_id):
    """The paper's own prompt, rendered exactly as its runner does."""
    b = BUGS[bug_id]
    tpl = b["template"].read_text(encoding="utf-8").replace("\r\n", "\n")
    if b["kind"] == "d4j":  # claude-cli-automation/automated_claude_cli.py: read_base_prompt_and_inject
        return (tpl.replace("{{bug_title}}", b["title"] or "title unavailable")
                   .replace("{{bug_description}}", (b["description"] or "").strip()))
    r = swe_record(bug_id)  # hunk-swe/swe_bench_utils/config.py: render_prompt
    f2p = json.loads(r["FAIL_TO_PASS"]) if isinstance(r["FAIL_TO_PASS"], str) else r["FAIL_TO_PASS"]
    hints = (r.get("hints_text") or "").strip()
    hints_section = f"**Additional Hints**:\n{hints}\n" if hints else ""
    return (tpl.replace("{{problem_statement}}", r.get("problem_statement", ""))
               .replace("{{fail_to_pass}}", "\n".join(f2p))
               .replace("{{hints_section}}", hints_section))
