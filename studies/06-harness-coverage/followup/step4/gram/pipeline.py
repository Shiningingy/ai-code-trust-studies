"""Load a grammar library, parse a document with it, run its tests.

A content line is any non-empty line that does not start with "#" and comes before the last "Final Query" heading.
Each content line is split into clauses; each clause is normalised, then given to every selected rule.
A clause is RESOLVED when exactly one rule parses it (or several rules give the same facts), when an ignore-rule
takes it, or when manual.jsonl covers it. Everything else is an outlier, with the reason.
"""
import importlib.util
import json
import os
import re

from .base import Normalizer, Rule, Splitter, check_fact, same_meaning_form, words


class LibraryError(Exception):
    pass


def content_lines(text):
    i = text.rfind("Final Query")
    body = text[:i] if i >= 0 else text
    lines = body.splitlines()
    if i >= 0 and lines and lines[-1].lstrip().startswith("#"):
        lines = lines[:-1]
    return [(n, l) for n, l in enumerate(lines, 1) if l.strip() and not l.strip().startswith("#")]


def load(lib_dir):
    """Return (splitter, [normalizers], [rules], all_parts) as selected by lib_dir/config.json."""
    parts = {}
    root = os.path.join(lib_dir, "parts")
    for dirpath, _, files in os.walk(root):
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            path = os.path.join(dirpath, f)
            modname = "gramlib_" + re.sub(r"\W", "_", os.path.relpath(path, root))
            spec = importlib.util.spec_from_file_location(modname, path)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:  # noqa: BLE001 - report any import error with its file
                raise LibraryError("cannot import %s: %s: %s" % (os.path.relpath(path, lib_dir), type(e).__name__, e))
            for obj in vars(mod).values():
                if (isinstance(obj, type) and issubclass(obj, (Splitter, Normalizer, Rule)) and obj.__module__ == modname
                        and not getattr(obj, "__abstractmethods__", None)):
                    if not obj.name:
                        raise LibraryError("%s in %s has no name" % (obj.__name__, os.path.relpath(path, lib_dir)))
                    if obj.name in parts:
                        raise LibraryError("duplicate part name %r" % obj.name)
                    inst = obj()
                    inst._file = os.path.relpath(path, lib_dir)
                    parts[obj.name] = inst
    cfg_path = os.path.join(lib_dir, "config.json")
    cfg = json.load(open(cfg_path, encoding="utf-8")) if os.path.exists(cfg_path) else {}

    def pick(names, kind):
        if names in (None, "all"):
            return [p for p in parts.values() if p.kind == kind]
        out = []
        for n in names:
            if n not in parts or parts[n].kind != kind:
                raise LibraryError("config names %r, which is not a %s in the library" % (n, kind))
            out.append(parts[n])
        return out

    splitters = pick([cfg["splitter"]] if cfg.get("splitter") else None, "splitter")
    if len(splitters) != 1:
        raise LibraryError("exactly one splitter must be selected (config.json \"splitter\"); found %d" % len(splitters))
    return splitters[0], pick(cfg.get("normalizers", []), "normalizer"), pick(cfg.get("rules", "all"), "rule"), parts


def _split_checked(splitter, line):
    """Clauses of a line, plus an error string if the splitter lost words or changed the text."""
    try:
        clauses = splitter.split(line)
    except Exception as e:  # noqa: BLE001
        return [], "splitter raised %s: %s" % (type(e).__name__, e)
    pos, gaps = 0, []
    for c in clauses:
        j = line.find(c, pos)
        if j < 0:
            return clauses, "splitter changed the text of clause %r (clauses must be pieces of the line)" % c[:80]
        gaps.append(line[pos:j])
        pos = j + len(c)
    gaps.append(line[pos:])
    for g in gaps:
        if words(g) and not any(re.fullmatch(rx, g.strip(), re.I) for rx in splitter.droppable):
            return clauses, "splitter dropped words %r that match none of its droppable patterns" % g.strip()[:80]
    return clauses, None


def load_manual(path):
    """manual.jsonl rows: {"line": n, "clause": text or null (whole line), "facts": [...] | "ignore": true, "reason": "..."}"""
    out = {}
    if path and os.path.exists(path):
        for row in open(path, encoding="utf-8"):
            row = row.strip()
            if not row:
                continue
            d = json.loads(row)
            out[(int(d["line"]), d.get("clause"))] = d
    return out


def parse_line(n, line, splitter, normalizers, rules, manual):
    rec = {"line": n, "clauses": []}
    whole = manual.get((n, None))
    if whole:
        rec["clauses"].append({"text": line, "status": "manual", "facts": whole.get("facts", []), "by": "manual"})
        rec["status"] = "ok"
        return rec
    clauses, err = _split_checked(splitter, line)
    if err:
        rec["status"] = "outlier"
        rec["clauses"].append({"text": line, "status": "split_error", "detail": err})
        return rec
    for c in clauses:
        cr = {"text": c}
        m = manual.get((n, c))
        if m:
            cr.update(status="manual", facts=[] if m.get("ignore") else m.get("facts", []), by="manual")
            rec["clauses"].append(cr)
            continue
        norm, used = c, []
        for nz in normalizers:
            try:
                new = nz.apply(norm)
            except Exception as e:  # noqa: BLE001
                cr.update(status="error", detail="normalizer %s raised %s" % (nz.name, e))
                break
            if new != norm:
                if not same_meaning_form(norm, new):
                    cr.update(status="normalizer_changed_words", detail="%s: %r -> %r" % (nz.name, norm[:80], new[:80]))
                    break
                used.append(nz.name)
                norm = new
        if "status" in cr:
            rec["clauses"].append(cr)
            continue
        cr["normalized"] = norm if used else None
        cr["normalizers"] = used
        hits = []
        for r in rules:
            try:
                facts = r.parse(norm)
            except Exception as e:  # noqa: BLE001
                hits.append((r, "error: %s" % e))
                continue
            if facts is not None:
                hits.append((r, facts))
        good = [(r, f) for r, f in hits if isinstance(f, list)]
        if not good:
            cr.update(status="unparsed")
        elif len({json.dumps(f, sort_keys=True) for _, f in good}) > 1:
            cr.update(status="ambiguous", rules=[r.name for r, _ in good])
        else:
            r, facts = good[0]
            if facts and not all(check_fact(f) for f in facts):
                cr.update(status="bad_facts", rules=[r.name], detail=json.dumps(facts)[:200])
            elif not facts and not r.ignore:
                cr.update(status="bad_facts", rules=[r.name], detail="returned [] but is not an ignore-rule")
            else:
                cr.update(status="ignored" if r.ignore else "parsed", by=[x.name for x, _ in good], facts=facts)
        rec["clauses"].append(cr)
    rec["status"] = "ok" if all(c["status"] in ("parsed", "ignored", "manual") for c in rec["clauses"]) else "outlier"
    return rec


def parse_text(text, lib_dir, manual_path=None):
    splitter, normalizers, rules, _ = load(lib_dir)
    manual = load_manual(manual_path)
    return [parse_line(n, l, splitter, normalizers, rules, manual) for n, l in content_lines(text)]


def run_tests(lib_dir):
    """Return a list of failure strings for every part's examples."""
    _, _, _, parts = load(lib_dir)
    fails = []
    for p in parts.values():
        for ex in p.examples:
            try:
                if p.kind == "splitter":
                    got = p.split(ex[0])
                    ok = got == ex[1]
                elif p.kind == "normalizer":
                    got = p.apply(ex[0])
                    ok = got == ex[1] and same_meaning_form(ex[0], got)
                else:
                    got = p.parse(ex[0])
                    ok = json.dumps(got, sort_keys=True) == json.dumps(ex[1], sort_keys=True)
            except Exception as e:  # noqa: BLE001
                got, ok = "raised %s: %s" % (type(e).__name__, e), False
            if not ok:
                fails.append("%s (%s): input %r expected %r got %r" % (p.name, p._file, str(ex[0])[:80], ex[1], got))
        if not p.examples:
            fails.append("%s (%s): has no examples" % (p.name, p._file))
    return fails


def summary(records):
    st = {}
    for r in records:
        for c in r["clauses"]:
            st[c["status"]] = st.get(c["status"], 0) + 1
    return {"lines": len(records), "lines_ok": sum(r["status"] == "ok" for r in records), "clauses": st}
