"""Where each class in the class_graph index is defined: file (path from the project root, as the agent sees it)
and line range. Amendment 2 (Allen, 2026-11-18): the tool was meant to give structure context like the paper's
MAPLE, whose class lookups return the defining file; the first index had names, members and relations only.

Built from the BUGGY base tree only, like build_index.py; no model, deterministic (--check compares).
Keys are the index's qualified names (uml_java.py / uml_py.py naming). Values: [file, first line, last line];
Python module-function boxes (<module>.__module__) give the module file with lines null.
Java line ranges: from the declaration's first token (annotations and modifiers included) to its closing brace,
found with javalang's tokenizer (comments and strings are not tokens, so braces inside them do not count).
Python: first decorator line (or the `class` line) to end_lineno.

Writes E:\\study05\\uml\\<bug>\\locations.json; copies its stats to uml/<bug>/locations-stats.json.
Usage: E:\\study05\\venv\\Scripts\\python.exe build_locations.py <bug id> [--check]
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from bugs import BUGS, DATA, STUDY  # noqa: E402


def java_locations(base):
    import javalang
    import uml_java
    out = {}
    for path, cu in uml_java.parse_all(base / "src").items():
        if isinstance(cu, Exception):
            continue
        rel = path.relative_to(base).as_posix()
        toks = list(javalang.tokenizer.tokenize(path.read_text(encoding="utf-8", errors="replace")))
        _, types = uml_java.types_in(cu)
        for q, _, decl in types:
            start = decl.position.line if decl.position else None
            kw = {"ClassDeclaration": "class", "InterfaceDeclaration": "interface", "EnumDeclaration": "enum",
                  "AnnotationDeclaration": "interface"}[type(decl).__name__]
            # the declaring keyword followed by the type's name, at or after the declaration's position
            i = next((k for k in range(len(toks) - 1)
                      if toks[k].value == kw and toks[k + 1].value == decl.name
                      and (start is None or toks[k].position.line >= start)), None)
            if i is None:
                out[q] = [rel, start, None]
                continue
            first = start or toks[i].position.line
            for a in (getattr(decl, "annotations", None) or []):
                if a.position:
                    first = min(first, a.position.line)
            depth, end = 0, None
            for t in toks[i:]:
                if t.value == "{":
                    depth += 1
                elif t.value == "}":
                    depth -= 1
                    if depth == 0:
                        end = t.position.line
                        break
            out[q] = [rel, first, end]
    return out


def py_locations(base, top):
    import uml_py
    out = {}
    dirs = sorted({str(p.parent.relative_to(base)).replace("\\", "/") for p in (base / top).rglob("*.py")
                   if "tests" not in p.relative_to(base).parts})
    for p in uml_py.py_files(base, dirs):
        m = uml_py.mod_name(base, p)
        rel = p.relative_to(base).as_posix()
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"), str(p))
        for n in tree.body:
            if isinstance(n, ast.ClassDef):
                first = min([n.lineno] + [d.lineno for d in n.decorator_list])
                out[f"{m}.{n.name}"] = [rel, first, n.end_lineno]
        if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in tree.body):
            out[f"{m}.__module__"] = [rel, None, None]
    return out


def build(bug_id):
    bug = BUGS[bug_id]
    loc = java_locations(bug["base"]) if bug["kind"] == "d4j" else py_locations(bug["base"], bug["package"])
    return json.dumps(dict(sorted(loc.items())), indent=0, ensure_ascii=False) + "\n", loc


def main(bug_id, check=False):
    text, loc = build(bug_id)
    out = DATA / "uml" / bug_id
    if check:
        print("identical" if (out / "locations.json").read_text(encoding="utf-8") == text else "DIFFERENT")
        return
    (out / "locations.json").write_text(text, encoding="utf-8", newline="\n")
    index_names = {ln.split(" as ")[1].split()[0] for ln in (out / "index.puml").read_text(encoding="utf-8").split("\n")
                   if ln.startswith("  ") and " as " in ln and ln.rstrip().endswith("{")}
    stats = {"bug": bug_id, "source": str(BUGS[bug_id]["base"]), "entries": len(loc),
             "index_types": len(index_names), "index_types_without_location": sorted(index_names - set(loc))[:50],
             "without_line_range": sum(1 for v in loc.values() if v[1] is None and not v[0].endswith(".py")
                                       or (v[1] is not None and v[2] is None)),
             "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    dst = STUDY / "uml" / bug_id
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "locations-stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], "--check" in sys.argv)
