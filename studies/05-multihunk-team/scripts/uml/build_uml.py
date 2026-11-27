"""Build the arm-U class graph for one bug, applying the scoping rule fixed in plan.md (section "Arm U: the class graph").

Inputs are the BUGGY base tree and the failing-test names the agent is also given (SWE-bench FAIL_TO_PASS)
or can list with one script run (Defects4J tests.trigger). The gold patch and the fixed version are never read.

Rule: budget B = 50,000 approximate tokens (characters / 4). Take the first tier whose graph fits:
  1. the whole main source tree (tests excluded);
  2. the package(s) holding the failing tests' classes (Java: the test class's package; Python: the package
     that holds the test module's tests/ directory), non-recursive;
  3. the repo types named in the failing test source files, plus one hop: their supertypes, field types and
     every repo type they use;
  4. the repo types named in the failing test source files only.

Writes <out>/graph.puml (the file placed in arm-U workspaces), <out>/stats.json (every tier's size, the tier
chosen) and <out>/command.txt. Deterministic: same input, same bytes (check with --check).

Usage: python build_uml.py <bug id> <out dir> [--check]
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import uml_java  # noqa: E402
import uml_py  # noqa: E402
from bugs import BUGS  # noqa: E402

BUDGET = 50_000


def tokens(text):
    return len(text) // 4


def header(text, scope_note):
    lines = text.split("\n")
    return "\n".join(lines[:1] + [f"' Scope: {scope_note}"] + lines[1:])


# ---------------------------------------------------------------- Java (Defects4J)

def java_tiers(bug):
    base = bug["base"]
    src, test = base / "src", base / "test"
    units = uml_java.parse_all(src)
    known, by_simple = uml_java.index(units)
    classes = sorted({t.split("::")[0] for t in bug["failing_tests"]})
    pkgs = sorted({c.rsplit(".", 1)[0] for c in classes})
    seed = set()
    for c in classes:
        p = test / (c.replace(".", "/") + ".java")
        cu = uml_java.javalang.parse.parse(p.read_text(encoding="utf-8", errors="replace"))
        res = uml_java.Resolver(known, by_simple, cu, c)
        for _, node in cu:
            names = []
            if isinstance(node, uml_java.T.ReferenceType):
                names = uml_java.ref_names(node)
            elif isinstance(node, (uml_java.T.MethodInvocation, uml_java.T.MemberReference)) and node.qualifier:
                names = [node.qualifier]
            elif isinstance(node, uml_java.T.ClassDeclaration) and node.extends is not None:
                names = uml_java.ref_names(node.extends)
            for nm in names:
                r = res(nm)
                if r:
                    seed.add(r)
    seed = {s for s in seed if s in known}

    def graph_of(types):
        # the full graph restricted to `types`: same member lines, only edges between kept types
        text, _ = uml_java.build(src, ["*"], units)
        keep = []
        cur = None
        for ln in text.split("\n"):
            s = ln.strip()
            if s.startswith(("class ", "interface ", "enum ", "abstract class ", "annotation ")) and " as " in s:
                cur = s.split(" as ")[1].split(" ")[0]
                if cur in types:
                    keep.append(ln)
                continue
            if cur is not None:
                if cur in types:
                    keep.append(ln)
                if s == "}" and ln.startswith("  }"):
                    cur = None
                continue
            if s.startswith("package "):
                keep.append(ln)
            elif s == "}":
                keep.append(ln)
            elif any(a in s for a in (" --|> ", " ..|> ", " --> ", " ..> ", " +-- ")):
                a, _, b = s.split(" ")[:3]
                if a in types and b in types:
                    keep.append(ln)
            else:
                keep.append(ln)
        # drop empty packages
        out, i = [], 0
        while i < len(keep):
            if keep[i].startswith("package ") and i + 1 < len(keep) and keep[i + 1] == "}":
                i += 2
                continue
            out.append(keep[i])
            i += 1
        return "\n".join(out)

    def neighbours(types):
        full, _ = uml_java.build(src, ["*"], units)
        out = set(types)
        for ln in full.split("\n"):
            s = ln.strip()
            if any(a in s for a in (" --|> ", " ..|> ", " --> ", " ..> ")):
                a, _, b = s.split(" ")[:3]
                if a in types:
                    out.add(b)
        return out

    t1, _ = uml_java.build(src, ["*"], units)
    t2, _ = uml_java.build(src, pkgs, units)
    one_hop = neighbours(seed)
    t3 = graph_of(one_hop)
    t4 = graph_of(seed)
    return [
        ("1", "the whole main source tree", t1),
        ("2", "all types in packages " + ", ".join(pkgs), t2),
        ("3", f"{len(one_hop)} types from packages " + ", ".join(sorted({known[t][0] for t in one_hop})), t3),
        ("4", f"{len(seed)} types from packages " + ", ".join(sorted({known[t][0] for t in seed})), t4),
    ]


# ---------------------------------------------------------------- Python (SWE-bench)

def py_dirs(root, top):
    return sorted({str(p.parent.relative_to(root)).replace("\\", "/") for p in (root / top).rglob("*.py")
                   if "tests" not in p.relative_to(root).parts})


def py_tiers(bug):
    root = bug["base"]
    top = bug["package"]
    files = sorted({t.split("::")[0] for t in bug["failing_tests"]})
    pkgs = sorted({str(Path(f).parent.parent).replace("\\", "/") for f in files})  # .../tests/test_x.py -> ...
    t1, _ = uml_py.build(root, py_dirs(root, top))
    t2, _ = uml_py.build(root, pkgs)
    # tiers 3-4 (only reached if tier 2 is too big): modules imported by the failing test files
    mods = set()
    for f in files:
        t = ast.parse((root / f).read_text(encoding="utf-8"))
        for n in ast.walk(t):
            if isinstance(n, ast.ImportFrom) and n.module and n.level == 0 and n.module.startswith(top):
                mods.add(n.module)
            elif isinstance(n, ast.ImportFrom) and n.level:
                base = Path(f).parent
                for _ in range(n.level - 1):
                    base = base.parent
                mods.add(".".join(base.parts) + (f".{n.module}" if n.module else ""))
    dirs = sorted({m.replace(".", "/") if (root / m.replace(".", "/")).is_dir()
                   else str(Path(m.replace(".", "/")).parent).replace("\\", "/") for m in mods})
    t3, _ = uml_py.build(root, dirs)
    return [("1", f"the whole {top} package", t1), ("2", "package(s) " + ", ".join(p.replace('/', '.') for p in pkgs), t2),
            ("3", "packages imported by the failing test modules: " + ", ".join(d.replace('/', '.') for d in dirs), t3)]


def main(bug_id, out, check=False):
    bug = BUGS[bug_id]
    tiers = java_tiers(bug) if bug["kind"] == "d4j" else py_tiers(bug)
    chosen = next((t for t in tiers if tokens(t[2]) <= BUDGET), None)
    if chosen is None:
        raise SystemExit("no tier fits the budget; the rule says stop and ask Zili Luo")
    text = header(chosen[2], chosen[1]).rstrip("\n") + "\n"
    stats = {"bug": bug_id, "budget_tokens": BUDGET, "chosen_tier": chosen[0], "scope": chosen[1],
             "tiers": [{"tier": n, "scope": d, "lines": t.count("\n") + 1, "chars": len(t),
                        "approx_tokens": tokens(t),
                        "types": sum(1 for ln in t.split("\n") if " as " in ln and ln.rstrip().endswith("{"))}
                       for n, d, t in tiers],
             "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    out = Path(out)
    if check:
        old = (out / "graph.puml").read_text(encoding="utf-8")
        print("identical" if old == text else "DIFFERENT")
        return
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.puml").write_text(text, encoding="utf-8", newline="\n")
    (out / "stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    (out / "command.txt").write_text(f"python scripts/uml/build_uml.py {bug_id} {out.as_posix()}\n"
                                     f"(javalang 0.13.0 for Java; Python {sys.version.split()[0]} ast for Python)\n",
                                     encoding="utf-8")
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--check" in sys.argv)
