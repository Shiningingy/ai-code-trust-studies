"""Static UML class graph of a Java source tree (PlantUML text), parsed with `javalang` (0.13.0).

Deterministic: files, types and members are sorted by name or source order, nothing is compiled or
executed, no model is involved. Contents per type (class / interface / enum, nested types included as
Outer.Inner): fields with types, constructor and method signatures with visibility, extends (--|>),
implements (..|>), associations (-->, a field whose type, or a type argument of it, is a repo type)
and dependencies (..>, any other use of a repo type: parameter, return, local, cast, `new`, static
call or constant such as Token.STRING).

Usage: python -I uml_java.py <source root, e.g. src> <package>[,<package>...] <out.puml>
       (package "*" = every package under the root)
Library use: build(root, packages) -> (puml text, stats dict); index(root) for name resolution.
"""
import json
import sys
from pathlib import Path

import javalang
from javalang import tree as T

TYPE_DECLS = (T.ClassDeclaration, T.InterfaceDeclaration, T.EnumDeclaration, T.AnnotationDeclaration)
VIS = {"public": "+", "protected": "#", "private": "-"}


def parse_all(root):
    """{path: CompilationUnit} for every .java file under root (sorted)."""
    out = {}
    for p in sorted(Path(root).rglob("*.java")):
        try:
            out[p] = javalang.parse.parse(p.read_text(encoding="utf-8", errors="replace"))
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError, Exception) as e:  # noqa: BLE001
            out[p] = e
    return out


def types_in(cu):
    """[(qualified name, simple dotted name, decl)] including nested types, in source order."""
    pkg = cu.package.name if cu.package else ""
    res = []

    def walk(decl, prefix):
        name = f"{prefix}.{decl.name}" if prefix else decl.name
        res.append((f"{pkg}.{name}" if pkg else name, name, decl))
        for m in (decl.body or []) if not isinstance(decl, T.EnumDeclaration) else (decl.body.declarations or []):
            if isinstance(m, TYPE_DECLS):
                walk(m, name)
    for t in cu.types:
        walk(t, "")
    return pkg, res


def index(units):
    known, by_simple = {}, {}
    for p, cu in units.items():
        if isinstance(cu, Exception):
            continue
        pkg, ts = types_in(cu)
        for q, s, d in ts:
            known[q] = (pkg, s, d, cu)
            by_simple.setdefault(s.split(".")[-1], set()).add(q)
    return known, by_simple


def tstr(t):
    if t is None:
        return "void"
    if isinstance(t, T.BasicType):
        return t.name + "[]" * len(t.dimensions or [])
    name, cur = t.name, t
    args = ""
    if getattr(t, "arguments", None):
        args = "<" + ", ".join(tstr(a.type) if a.type else "?" for a in t.arguments) + ">"
    while getattr(cur, "sub_type", None):
        cur = cur.sub_type
        name += "." + cur.name
    return name + args + "[]" * len(t.dimensions or [])


def ref_names(t):
    """Every reference-type name inside a type, including type arguments."""
    out = []
    if isinstance(t, T.ReferenceType):
        name, cur = t.name, t
        while getattr(cur, "sub_type", None):
            cur = cur.sub_type
            name += "." + cur.name
        out.append(name)
        for a in t.arguments or []:
            if a.type is not None:
                out += ref_names(a.type)
    return out


class Resolver:
    def __init__(self, known, by_simple, cu, own_q):
        self.known, self.by_simple = known, by_simple
        self.pkg = cu.package.name if cu.package else ""
        self.single = {}
        self.wild = []
        for imp in cu.imports:
            if imp.static:
                if not imp.wildcard:  # static import of a member: its class is a dependency
                    self.single.setdefault(imp.path.rsplit(".", 1)[-1], imp.path.rsplit(".", 1)[0])
                continue
            if imp.wildcard:
                self.wild.append(imp.path)
            else:
                self.single[imp.path.rsplit(".", 1)[-1]] = imp.path
        self.own = own_q
        self.outer = own_q.split(".")

    def __call__(self, name):
        head, _, rest = name.partition(".")
        cands = []
        # nested in this type or an enclosing type, then same package, single imports, wildcards
        for i in range(len(self.outer), 0, -1):
            cands.append(".".join(self.outer[:i] + [name]))
        cands.append(f"{self.pkg}.{name}" if self.pkg else name)
        if head in self.single:
            cands.append(self.single[head] + ("." + rest if rest else ""))
        cands += [f"{w}.{name}" for w in self.wild]
        cands.append(name)  # already qualified
        for c in cands:
            if c in self.known:
                return c
        return None


def body_members(decl):
    if isinstance(decl, T.EnumDeclaration):
        return list(decl.body.declarations or [])
    return list(decl.body or [])


def walk_no_nested(node):
    """Yield every node under `node` without entering nested type declarations."""
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        kids = []
        for c in (n.children if isinstance(n, T.Node) else n):
            if isinstance(c, TYPE_DECLS):
                continue
            if isinstance(c, (T.Node, list, tuple)):
                kids.append(c)
        stack.extend(reversed(kids))


def build(root, packages, units=None):
    units = units or parse_all(root)
    known, by_simple = index(units)
    want_all = packages == ["*"]
    lines = ["@startuml", "' generated by uml_java.py (javalang) from the buggy checkout; static parse only"]
    edges = set()
    n_types = n_members = 0
    errors = [str(p) for p, cu in units.items() if isinstance(cu, Exception)]
    by_pkg = {}
    for q, (pkg, s, d, cu) in known.items():
        if want_all or pkg in packages:
            by_pkg.setdefault(pkg, []).append(q)
    for pkg in sorted(by_pkg):
        lines.append(f"package {pkg} {{")
        for q in sorted(by_pkg[pkg]):
            _, s, d, cu = known[q]
            res = Resolver(known, by_simple, cu, q)
            kind = ("interface" if isinstance(d, T.InterfaceDeclaration) else "enum" if isinstance(d, T.EnumDeclaration)
                    else "annotation" if isinstance(d, T.AnnotationDeclaration) else
                    "abstract class" if "abstract" in (d.modifiers or set()) else "class")
            n_types += 1
            lines.append(f'  {kind} "{s}" as {q} {{')
            if isinstance(d, T.EnumDeclaration):
                for c in d.body.constants or []:
                    lines.append(f"    {c.name}")
                    n_members += 1
            assoc, deps = set(), set()
            for m in body_members(d):
                mods = getattr(m, "modifiers", None) or set()
                v = next((VIS[x] for x in ("public", "protected", "private") if x in mods), "~")
                st = "{static} " if "static" in mods else ""
                ab = "{abstract} " if "abstract" in mods else ""
                if isinstance(m, T.FieldDeclaration):
                    for dec in m.declarators:
                        lines.append(f"    {v} {st}{dec.name} : {tstr(m.type)}")
                        n_members += 1
                    for nm in ref_names(m.type):
                        r = res(nm)
                        if r and r != q:
                            assoc.add(r)
                elif isinstance(m, (T.MethodDeclaration, T.ConstructorDeclaration)):
                    ps = ", ".join(f"{tstr(p.type)}{'...' if p.varargs else ''} {p.name}" for p in m.parameters)
                    ret = "" if isinstance(m, T.ConstructorDeclaration) else f" : {tstr(m.return_type)}"
                    lines.append(f"    {v} {st}{ab}{m.name}({ps}){ret}")
                    n_members += 1
            for x in walk_no_nested(d):
                names = []
                if isinstance(x, T.ReferenceType):
                    names = ref_names(x)
                elif isinstance(x, (T.MethodInvocation, T.MemberReference)) and x.qualifier:
                    names = [x.qualifier]
                for nm in names:
                    r = res(nm)
                    if r and r != q:
                        deps.add(r)
            lines.append("  }")
            sup = []
            if isinstance(d, T.ClassDeclaration) and d.extends is not None:
                sup = [(d.extends, "--|>")]
            elif isinstance(d, T.InterfaceDeclaration):
                sup = [(e, "--|>") for e in d.extends or []]
            impls = [(i, "..|>") for i in (getattr(d, "implements", None) or [])]
            linked = set()
            for t, arrow in sup + impls:
                r = res(ref_names(t)[0])
                if r:
                    edges.add(f"{q} {arrow} {r}")
                    linked.add(r)
            for r in sorted(assoc - linked):
                edges.add(f"{q} --> {r}")
            for r in sorted(deps - assoc - linked):
                edges.add(f"{q} ..> {r}")
            if "." in s:  # nested type: show its owner
                edges.add(f"{q.rsplit('.', 1)[0]} +-- {q}")
        lines.append("}")
    lines += sorted(edges)
    lines.append("@enduml")
    text = "\n".join(lines) + "\n"
    stats = {"files": sum(1 for p, cu in units.items() if not isinstance(cu, Exception)
                          and (want_all or (cu.package.name if cu.package else "") in packages)),
             "parse_errors": errors, "types": n_types, "members": n_members, "edges": len(edges),
             "lines": len(lines), "chars": len(text), "approx_tokens": len(text) // 4}
    return text, stats


if __name__ == "__main__":
    text, stats = build(Path(sys.argv[1]), sys.argv[2].split(","))
    Path(sys.argv[3]).write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(stats))
