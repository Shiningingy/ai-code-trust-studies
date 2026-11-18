"""MCP server (stdio) for arm U: one tool, `class_graph`, that returns a UML class graph (PlantUML text) for
the part of the code the agent asks for (D7, Allen 2026-11-18: a Maple-style tool; the agent chooses the scope).

The index is the full static graph of the bug's main source tree (tests excluded), built from the BUGGY base
tree before any run by build_index.py with the same parsers as before (uml_py.py: `ast`; uml_java.py:
`javalang`). Nothing here reads the fix, runs code or calls a model. Answers are a deterministic subset of the
index, so the same question always gets the same text. Every call is logged.

Hand-written JSON-RPC like box_mcp.py (no MCP library). Standard library only.
Usage (from an MCP config): python uml_mcp.py <index .puml> <log file> [<locations .json>]

Amendment 2 (Allen, 2026-11-18): with a locations file (build_locations.py) every answer also lists the file and
line range where each shown class is defined, and the tool description says so, as the paper's MAPLE class
lookups return the defining file. Without it (the frozen arm U) answers and description are byte-identical to
the frozen version.
"""
import json
import re
import sys
import time
from collections import deque

INDEX, LOG = sys.argv[1], sys.argv[2]
LOCS = json.load(open(sys.argv[3], encoding="utf-8")) if len(sys.argv) > 3 else None
CAP = 60000          # characters per answer (~15k tokens); larger answers reduce hops, then drop members
MAX_HOPS = 3
TYPE_RE = re.compile(r'^  (class|interface|enum|annotation|abstract class) "([^"]+)" as (\S+)( <<module>>)? \{$')
EDGE_RE = re.compile(r"^(\S+) (--\|>|\.\.\|>|-->|\.\.>|\+--) (\S+)( : .*)?$")

TOOL = {
    "name": "class_graph",
    "description": (
        "Return a UML class graph (PlantUML text) for part of this project's main source code (tests excluded). "
        "It was produced by a static parser from the code as checked out at the start of the session, so it "
        "does not reflect later edits. `name` is a class name (simple or fully qualified) or a package/module "
        "name; the matching classes are shown with their fields and method signatures. `hops` (default 1, max 3) "
        "also lists, by name only, the classes within that many relationship steps (inheritance, field types, "
        "uses; both directions), with the relationships between all shown classes."
        + (" Every shown class also comes with the file (path from the project root) and the line range where "
           "it is defined." if LOCS is not None else "")),
    "inputSchema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "class name or package/module name"},
            "hops": {"type": "integer", "description": "relationship steps to include, 0-3 (default 1)"},
        },
        "required": ["name"],
    },
}


def load(path):
    types, edges, pkg, cur = {}, [], None, None
    for ln in open(path, encoding="utf-8").read().split("\n"):
        if cur is not None:
            if ln == "  }":
                cur = None
            else:
                types[cur]["body"].append(ln)
            continue
        if ln.startswith("package ") and ln.endswith(" {"):
            pkg = ln[len("package "):-2]
            continue
        m = TYPE_RE.match(ln)
        if m:
            kind, simple, q, mod = m.groups()
            types[q] = {"kind": kind, "simple": simple, "pkg": pkg, "mod": bool(mod), "body": []}
            cur = q
            continue
        m = EDGE_RE.match(ln)
        if m:
            edges.append((m.group(1), m.group(2), m.group(3), ln))
    adj = {}
    for a, _, b, _ in edges:
        if a in types and b in types:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
    return types, edges, adj


TYPES, EDGES, ADJ = load(INDEX)
PKGS = sorted({t["pkg"] for t in TYPES.values()})


def match(name):
    name = name.strip().strip("`").strip()
    if name in TYPES:
        return {name}, "class"
    pk = {q for q, t in TYPES.items() if t["pkg"] == name or t["pkg"].startswith(name + ".")}
    if pk:
        return pk, "package"
    last = name.split(".")[-1]
    simple = {q for q, t in TYPES.items() if t["simple"] == name or t["simple"].split(".")[-1] == last
              and (name == last or q.endswith("." + name))}
    if simple:
        return simple, "class"
    return set(), None


def neighbours(seeds, hops):
    dist = {s: 0 for s in seeds}
    dq = deque(seeds)
    while dq:
        x = dq.popleft()
        if dist[x] >= hops:
            continue
        for y in sorted(ADJ.get(x, ())):
            if y not in dist:
                dist[y] = dist[x] + 1
                dq.append(y)
    return {q for q, d in dist.items() if d > 0}


def render(name, seeds, near, hops, full_members, note):
    shown = seeds | near
    out = ["@startuml",
           f"' class_graph name={name!r} hops={hops}: {len(seeds)} matching classes"
           + (" with fields and methods" if full_members else " (names only, see below)")
           + f", {len(near)} related classes by name only",
           "' arrows: A --|> B extends, A ..|> B implements, A --> B has a field of type B, A ..> B uses B, "
           "A +-- B nested in A"]
    if note:
        out.append("' " + note)
    if LOCS is not None:
        out.append("' defined in (file:first-last line):")
        for q in sorted(shown):
            f, a, b = LOCS.get(q) or ("?", None, None)
            out.append(f"'   {q}  {f}" + (f":{a}-{b}" if a is not None else ""))
    by_pkg = {}
    for q in shown:
        by_pkg.setdefault(TYPES[q]["pkg"], []).append(q)
    for p in sorted(by_pkg):
        out.append(f"package {p} {{")
        for q in sorted(by_pkg[p]):
            t = TYPES[q]
            head = f'  {t["kind"]} "{t["simple"]}" as {q}' + (" <<module>>" if t["mod"] else "")
            if q in seeds and full_members:
                out.append(head + " {")
                out += t["body"]
                out.append("  }")
            else:
                out.append(head)
        out.append("}")
    out += [ln for a, _, b, ln in EDGES if a in shown and b in shown]
    out.append("@enduml")
    return "\n".join(out) + "\n"


def answer(name, hops):
    try:
        hops = max(0, min(int(hops if hops is not None else 1), MAX_HOPS))
    except (TypeError, ValueError):
        hops = 1
    seeds, how = match(name or "")
    if not seeds:
        low = (name or "").strip().lower()
        sims = sorted({t["simple"] for t in TYPES.values() if low and low in t["simple"].lower()})[:30]
        pk = [p for p in PKGS if low and low in p.lower()][:15]
        return (f"No class or package named {name!r} in the graph.\n"
                + (f"Classes with similar names: {', '.join(sims)}\n" if sims else "")
                + (f"Packages/modules with similar names: {', '.join(pk)}\n" if pk else "")), 0, 0, hops
    asked = hops
    for h in range(hops, -1, -1):
        near = neighbours(seeds, h)
        note = f"hops reduced from {asked} to {h} to fit the output limit" if h < asked else ""
        text = render(name, seeds, near, h, True, note)
        if len(text) <= CAP:
            return text, len(seeds), len(near), h
    text = render(name, seeds, set(), 0, False,
                  f"{len(seeds)} classes match; too large to show their members. Ask for one class or a smaller "
                  "package/module.")
    if len(text) > CAP:
        text = text[:CAP] + "\n[... cut: ask for a narrower name ...]\n"
    return text, len(seeds), 0, 0


def log(row):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def reply(id_, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        req = json.loads(line)
        method, id_ = req.get("method"), req.get("id")
        if id_ is None:
            continue
        if method == "initialize":
            reply(id_, {"protocolVersion": req["params"].get("protocolVersion", "2024-11-05"),
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "uml", "version": "1" if LOCS is None else "2"}})
        elif method == "tools/list":
            reply(id_, {"tools": [TOOL]})
        elif method == "tools/call":
            args = req["params"].get("arguments") or {}
            t0 = time.time()
            text, n_seed, n_near, h = answer(args.get("name"), args.get("hops"))
            log({"t": t0, "name": args.get("name"), "hops_asked": args.get("hops"), "hops_used": h,
                 "matched": n_seed, "related": n_near, "chars": len(text)})
            reply(id_, {"content": [{"type": "text", "text": text}]})
        elif method == "ping":
            reply(id_, {})
        else:
            reply(id_, error={"code": -32601, "message": f"no method {method}"})


if __name__ == "__main__":
    main()
