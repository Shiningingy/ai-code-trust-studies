"""Run pytest once per package and merge the junit reports (azure-sdk PRs whose tests span several packages).

Usage: python /opt/py_pytest_per_package.py [pytest options] --junitxml=PATH [options] test files...

The packages' test folders share module and package names (test_helpers_async, settings.testcase) and have no
__init__.py, so one pytest session imports the first package's copies for all of them ("import file mismatch").
Each package (sdk/<service>/<package>, from the file path) gets its own session with the same options and
--rootdir=/work, so test ids are the ones a single session would give; the reports are merged into PATH.
The exit code is the largest of the sessions' exit codes.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET

args = sys.argv[1:]
junit = next((a.split("=", 1)[1] for a in args if a.startswith("--junitxml=")), "/tmp/junit.xml")
opts = [a for a in args if not a.endswith(".py") and not a.startswith("--junitxml=")]
groups = {}
for f in (a for a in args if a.endswith(".py")):
    groups.setdefault("/".join(f.split("/")[:3]), []).append(f)

merged, code = ET.Element("testsuites"), 0
for i, (pkg, files) in enumerate(sorted(groups.items())):
    part = f"{junit}.{i}"
    print(f"=== {pkg}", flush=True)
    rc = subprocess.call([sys.executable, "-m", "pytest", *opts, "--rootdir=/work", f"--junitxml={part}", *files])
    code = max(code, rc)
    try:
        root = ET.parse(part).getroot()
    except (OSError, ET.ParseError):
        continue
    for suite in ([root] if root.tag == "testsuite" else list(root)):
        merged.append(suite)
ET.ElementTree(merged).write(junit, encoding="utf-8", xml_declaration=True)
sys.exit(code)
