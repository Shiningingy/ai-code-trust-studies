"""Offline tests for the pure parts: leak check, scrub, test-result parsing, tox parsing."""
import json
import os
import subprocess
import sys
from pathlib import Path

import judge
import stage1
import summarise


def test_leak_names_and_grams():
    names, grams = {"fetch_retry_count", "MaxBackoff"}, {tuple("x = foo ( 1 )".split())}
    n, g = summarise.leaks("Use fetch_retry_count wisely; MaxBackoffs is fine.", names, grams)
    assert n == ["fetch_retry_count"] and g == []
    n, g = summarise.leaks("the code x = foo ( 1 ) appears", names, grams)
    assert g == ["x = foo ( 1 )"]


def test_code_name_shapes():
    found = set(summarise.CODE_NAME.findall("retry fetch_data getValue HTTPServer _private Plain parseURL"))
    assert {"fetch_data", "getValue", "_private", "parseURL"} <= found
    assert "retry" not in found and "Plain" not in found


def test_scrub_only_added_comment_lines():
    lines = ["# per review, keep this", "x = 1  # reviewer asked", "y = 2  # plain", "# review of old code"]
    out, n = judge.scrub_lines(lines, added={0, 1, 2}, lang="Python")
    assert out == ["x = 1", "y = 2  # plain", "# review of old code"] and n == 2
    out, n = judge.scrub_lines(["// feedback: done", "z := 3"], added={0, 1}, lang="Go")
    assert out == ["z := 3"] and n == 1


def test_parse_junit():
    meta = {"language": "Python"}
    xml = ('<testsuites><testsuite><testcase classname="tests.a" name="t1"/>'
           '<testcase classname="tests.a" name="t2"><failure/></testcase>'
           '<testcase classname="tests.a" name="t3"><skipped/></testcase>'
           '<testcase classname="" name="tests.b"><error message="collection failure"/></testcase>'
           '</testsuite></testsuites>')
    r = stage1.parse(meta, "EXIT=1\n@@JUNIT@@\n" + xml)
    assert r == {"tests.a::t1": "pass", "tests.a::t2": "fail", "tests.a::t3": "skip", "::tests.b": "fail"}


def test_parse_go_json():
    meta = {"language": "Go"}
    ev = [{"Action": "run", "Package": "p", "Test": "TestA"}, {"Action": "pass", "Package": "p", "Test": "TestA"},
          {"Action": "fail", "Package": "p", "Test": "TestB/sub"}, {"Action": "fail", "Package": "q"}]
    r = stage1.parse(meta, "EXIT=1\n@@JSON@@\n" + "\n".join(json.dumps(e) for e in ev) + "\nnot json")
    assert r == {"p::TestA": "pass", "p::TestB/sub": "fail"}


def test_sentry_extras(tmp_path):
    tox = tmp_path / "tox.ini"
    tox.write_text("[testenv]\ndeps =\n    openai-v1.0.0: openai==1.0.0\n    openai-v2.3.0: openai==2.3.0\n"
                   "    openai: pytest-asyncio\n    langchain-base-latest: langchain==1.4.7\n"
                   "    langchain-base: httpx\n    {py3.8}-django: psycopg2\n")
    script = Path(__file__).parent / "env_helpers" / "sentry_extras.py"
    src = script.read_text().replace('"/work/tox.ini"', repr(str(tox)))
    env = dict(os.environ, PR_TESTS="tests/integrations/openai/test_x.py tests/integrations/langchain/test_y.py "
                                    "tests/integrations/django/test_z.py")
    out = subprocess.run([sys.executable, "-c", src], env=env, capture_output=True, text=True).stdout.split()
    assert out == ["openai==2.3.0", "pytest-asyncio", "langchain==1.4.7", "httpx", "psycopg2"]
