"""Step 4: compare independently written grammar libraries on the training documents (code, no model).

Libraries name subjects, relations and qualifiers differently (one writes "P-104", another "Dev Gupta"), so facts
are not compared word by word. Two things are compared exactly, over each stretch of text (a clause of the base
library, matched to the other libraries' clauses by character overlap, since the splitters may cut differently):
  CARRY  does the text yield facts, yield nothing (ignored), or stay unresolved?
  QUAL   do the facts keep a qualifier (time, negation, frequency...) in one library but none in another?
Disagreements are grouped by kind and clause shape (names, IDs and numbers masked); the 40 largest groups get IDs
G01... and must be decided in RECONCILE.md. Then, for each rule of the base library, one sample clause with every
library's facts side by side (IDs R01...), so the reconcile session can compare the schemas; these too must be
decided (which naming to keep). Manual files are not used here.
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram.pipeline import LibraryError, parse_text  # noqa: E402

MAX_GROUPS = 40


def shape(clause):
    c = re.sub(r"(?i)\b(?:youth\s*|y)\d+\b", "<Y>", clause)
    c = re.sub(r"(?i)\bevent-p-\d+-\d+\b", "<E>", c)
    c = re.sub(r"(?i)\bp-\d+\b", "<P>", c)
    c = re.sub(r"\b[A-Z]\.\s*[A-Z][a-z]+\b|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", "<N>", c)
    return re.sub(r"\d+", "<D>", c).strip()


def spans(line, clauses):
    out, pos = [], 0
    for c in clauses:
        j = line.find(c["text"], pos)
        if j < 0:
            j = line.find(c["text"])
        if j < 0:
            j, e = 0, len(line)
        else:
            e = j + len(c["text"])
            pos = e
        out.append((j, e, c))
    return out


def carry(cs):
    if any(c["status"] not in ("parsed", "ignored", "manual") for c in cs):
        return "unresolved"
    return "facts" if any(c.get("facts") for c in cs) else "nothing"


def has_qual(cs):
    return any(f.get("qualifiers") for c in cs for f in c.get("facts", []))


def diff_libraries(libs, docs):
    per, errors = {}, {}
    for k, lib in libs.items():
        per[k] = {}
        for d, path in docs.items():
            try:
                for r in parse_text(open(path, encoding="utf-8").read(), lib):
                    per[k][(d, r["line"])] = r
            except LibraryError as e:
                errors[k] = str(e)
                break
    ok = [k for k in libs if k not in errors]
    base = ok[0] if ok else None
    groups, samples = defaultdict(list), {}
    if base:
        text_of = {}
        for (d, n), r in per[base].items():
            line = " ".join(c["text"] for c in r["clauses"])
            text_of[(d, n)] = line
        for key, rb in per[base].items():
            d, n = key
            raw = open(docs[d], encoding="utf-8").read().splitlines()[n - 1]
            sp = {k: spans(raw, per[k][key]["clauses"]) for k in ok if key in per[k]}
            for (b0, b1, cb) in sp[base]:
                view = {}
                for k in ok:
                    view[k] = [c for (s0, s1, c) in sp.get(k, []) if s0 < b1 and b0 < s1]
                kinds = []
                if len({carry(v) for v in view.values()}) > 1:
                    kinds.append("CARRY")
                elif all(carry(v) == "facts" for v in view.values()) and len({has_qual(v) for v in view.values()}) > 1:
                    kinds.append("QUAL")
                for kind in kinds:
                    groups[(kind, shape(cb["text"]))].append((d, n, cb["text"], view))
                for rule in (cb.get("by") or [])[:1]:
                    if rule not in samples and all(carry(v) != "unresolved" for v in view.values()):
                        samples[rule] = (d, n, cb["text"], view)
    ordered = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    ids, out = [], ["# Disagreements between the libraries on the training documents", ""]
    for k, e in errors.items():
        out.append("**Library %s did not load: %s**" % (k, e))
    out.append("Base library for clause boundaries: lib_%s. %d disagreement groups, %d clauses.\n" %
               (base, len(ordered), sum(len(v) for _, v in ordered)))

    def show(view):
        rows = []
        for k, cs in view.items():
            if not cs:
                rows.append("  - lib_%s: (no clause here)" % k)
            for c in cs:
                rows.append("  - lib_%s: `%s` %s %s" % (k, c["text"][:120], c["status"], json.dumps(c.get("facts", []))[:350]))
        return rows

    out.append("## Part 1: what the text carries (CARRY) and whether qualifiers survive (QUAL)\n")
    for n, ((kind, sh), items) in enumerate(ordered, 1):
        if n > MAX_GROUPS:
            if n == MAX_GROUPS + 1:
                out.append("### Smaller groups (no ID; decide where you can)\n")
            out.append("- %s (%d clauses) shape: %s; e.g. `%s`" % (kind, len(items), sh, items[0][2][:150]))
            continue
        gid = "G%02d" % n
        ids.append(gid)
        out.append("### %s  %s  (%d clauses)  shape: %s\n" % (gid, kind, len(items), sh))
        for d, line, text, view in items[:3]:
            out.append("- %s line %d: `%s`" % (d, line, text[:200]))
            out += show(view)
        out.append("")
    out.append("## Part 2: one sample per rule of lib_%s, every library's facts side by side\n" % base)
    for n, (rule, (d, line, text, view)) in enumerate(sorted(samples.items()), 1):
        rid = "R%02d" % n
        ids.append(rid)
        out.append("### %s  rule %s: %s line %d: `%s`" % (rid, rule, d, line, text[:200]))
        out += show(view)
        out.append("")
    return ids, "\n".join(out)


if __name__ == "__main__":
    libs = dict(zip("abc", sys.argv[1:4]))
    ids, md = diff_libraries(libs, {"doc%d" % i: p for i, p in enumerate(sys.argv[4:7], 1)})
    print(md)
