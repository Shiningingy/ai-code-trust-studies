"""Disagreement scorer (definition B): failure signature plus setup.

A test is reduced to the set of things it builds, calls and expects, with
local names, comments and import style removed. Two tests disagree by the
Jaccard distance between those sets. Pure functions: no model, no Docker,
and test source is parsed, never executed.

Two kinds of noise are removed: a value the test chose itself and then checks
is an arbitrary echo, and a shorter public path to a name is the same name.
"""
import ast
from dataclasses import dataclass
from typing import Optional

NOT_SETUP = {
    "print", "len", "str", "int", "float", "bool", "list", "dict", "set", "tuple",
    "range", "isinstance", "issubclass", "repr", "sorted", "enumerate", "zip", "map",
    "filter", "any", "all", "min", "max", "sum", "abs", "type", "getattr", "setattr",
    "hasattr", "super", "open", "iter", "next", "format", "round", "bytes",
}
EXPECT_RAISE = ("raises", "warns", "assertRaises", "assertRaisesRegex", "assertRaisesMessage",
                "assertWarns", "assertWarnsRegex", "assertRaisesRegexp")
TEST_BASES = ("TestCase", "SimpleTestCase", "TransactionTestCase", "LiveServerTestCase")


@dataclass(frozen=True)
class Run:
    source: str
    failure: Optional[tuple] = None  # (actual, expected) from the failing assertion, once runs exist


def _imports(tree):
    names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                names[a.asname or a.name] = f"{node.module or ''}.{a.name}"
    return names


def _dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return parts[::-1]
    return [None] + parts[::-1]


def _is_test_class(node):
    if node.name.startswith("Test") or node.name.endswith("Test") or node.name.endswith("Tests"):
        return True
    return any(_dotted(b)[-1] in TEST_BASES for b in node.bases)


class _Resolver:
    def __init__(self, tree):
        self.imports = _imports(tree)
        self.classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name != "Meta" and not _is_test_class(node):
                self.classes[node.name] = node

    def name(self, node, seen=()):
        """Stable name for a callable: imported path, or what a local class derives from."""
        parts = _dotted(node)
        root = parts[0]
        if root in self.classes and root not in seen:
            bases = sorted(self.name(b, seen + (root,)) or "object" for b in self.classes[root].bases)
            return "subclass(" + ",".join(bases) + ")" + "".join("." + p for p in parts[1:])
        if root in self.imports:
            return ".".join([self.imports[root]] + parts[1:])
        if parts == [None]:
            return None
        if root in (None, "self", "cls") or len(parts) > 1:
            return "." + parts[-1]
        return None if root in NOT_SETUP else root


def _checked(tree):
    """The expressions a test asserts on."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            yield node.test
        elif isinstance(node, ast.Call):
            last = _dotted(node.func)[-1]
            if last and last.lower().startswith("assert") and last not in EXPECT_RAISE:
                yield from list(node.args) + [k.value for k in node.keywords]


def _chosen(tree):
    """Values set up outside any assertion. True, False and None are never arbitrary."""
    inside = {id(n) for part in _checked(tree) for n in ast.walk(part)}
    return {repr(n.value) for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and id(n) not in inside and not isinstance(n.value, (bool, type(None)))}


def _literals(node, chosen):
    for n in ast.walk(node):
        if isinstance(n, ast.Constant):
            yield f"echo:{n.value!r}" if repr(n.value) in chosen else f"expect:{n.value!r}"


def tokens(run):
    tree = ast.parse(run.source)
    resolve = _Resolver(tree)
    chosen = _chosen(tree)
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            out.update(_literals(node.test, chosen))
        elif isinstance(node, ast.ClassDef) and node.name in resolve.classes:
            out.add(resolve.name(ast.Name(node.name)))
        elif isinstance(node, ast.Call):
            path = _dotted(node.func)
            last = path[-1]
            if last in EXPECT_RAISE:
                if node.args:
                    out.add("expect:raises:" + str(resolve.name(node.args[0])))
            elif last and last.lower().startswith("assert"):
                for arg in list(node.args) + [k.value for k in node.keywords]:
                    out.update(_literals(arg, chosen))
            elif "patch" in path:
                first = node.args[0] if node.args else None
                out.add("patch:" + str(first.value if isinstance(first, ast.Constant) else first and resolve.name(first)))
            else:
                n = resolve.name(node.func)
                if n:
                    out.add(n)
    if run.failure:
        out.add("failure:" + "|".join(map(str, run.failure)))
    return out


def _is_name(token):
    return token.startswith("expect:raises:") or ":" not in token


def _alias(a, b):
    """True if one path is the other with modules left out, as a public re-export is."""
    short, long = sorted((a.split("."), b.split(".")), key=len)
    if short[0] != long[0] or short[-1] != long[-1]:
        return False
    rest = iter(long)
    return all(part in rest for part in short)


def _unify(x, y):
    """y with each name that is only another path to one of x's written as x's."""
    out = set(y)
    for t in filter(_is_name, y - x):
        match = next((s for s in filter(_is_name, x - y) if _alias(s, t)), None)
        if match:
            out = out - {t} | {match}
    return out


def _settle(x, y):
    """A value both tests check agrees as it stands; an echo only one checks is just an input."""
    def values(s):
        return {t.split(":", 1)[1] for t in s if t.startswith(("echo:", "expect:"))}

    both = values(x) & values(y)

    def plain(s):
        return {t if not t.startswith("echo:") else "expect:" + (t[5:] if t[5:] in both else "input") for t in s}

    return plain(x), plain(y)


def distance(a, b):
    x, y = _settle(tokens(a), tokens(b))
    y = _unify(x, y)
    return 1 - len(x & y) / len(x | y) if x | y else 0.0


def score(baseline, others):
    """Mean distance from the accepted baseline test to each other run's test."""
    return sum(distance(baseline, o) for o in others) / len(others) if others else None
