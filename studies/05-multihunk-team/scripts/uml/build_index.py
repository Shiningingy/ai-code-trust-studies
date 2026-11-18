"""Build the arm-U tool's index: the full static UML class graph of one bug's main source tree (tests excluded),
from the BUGGY base tree only (E:\\study05\\base\\<bug>-tree). The gold patch and the fixed version are never read;
no model is involved. Deterministic: same tree, same bytes (--check compares).

This replaces build_uml.py's pre-placed, pre-scoped graph (D7, 2026-11-18): the agent now picks the scope by
calling the class_graph tool (uml_mcp.py), which answers from this index.

Writes E:\\study05\\uml\\<bug>\\index.puml and stats.json, and copies stats.json to the study folder's uml/<bug>/.
Usage: E:\\study05\\venv\\Scripts\\python.exe build_index.py <bug id> [--check]   (javalang 0.13.0 for Java)
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from bugs import BUGS, DATA, STUDY  # noqa: E402


def build(bug_id):
    bug = BUGS[bug_id]
    if bug["kind"] == "d4j":
        import uml_java
        text, stats = uml_java.build(bug["base"] / "src", ["*"])
    else:
        import uml_py
        root, top = bug["base"], bug["package"]
        dirs = sorted({str(p.parent.relative_to(root)).replace("\\", "/") for p in (root / top).rglob("*.py")
                       if "tests" not in p.relative_to(root).parts})
        text, stats = uml_py.build(root, dirs)
    return text, stats


def main(bug_id, check=False):
    text, stats = build(bug_id)
    out = DATA / "uml" / bug_id
    if check:
        print("identical" if (out / "index.puml").read_text(encoding="utf-8") == text else "DIFFERENT")
        return
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.puml").write_text(text, encoding="utf-8", newline="\n")
    stats.update(bug=bug_id, source=str(BUGS[bug_id]["base"]), sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                 types=sum(1 for ln in text.split("\n") if " as " in ln and ln.rstrip().endswith("{")),
                 python=sys.version.split()[0])
    stats.pop("parse_errors", None) if not stats.get("parse_errors") else None
    (out / "stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    dst = STUDY / "uml" / bug_id
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out / "stats.json", dst / "index-stats.json")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], "--check" in sys.argv)
