"""Step 4: compare independently written grammar libraries on the training documents (code, no model).

Each library parses every clause; a clause's signature is its status plus the bag of words in its facts' subjects,
objects and qualifiers (relation names are left out, since libraries name relations differently). Clauses whose
signatures differ between libraries are grouped by clause shape (names, IDs and numbers masked) and written to
diff.md, with up to three example clauses per group and each library's facts. The 40 largest groups get IDs
(G01...); smaller ones are listed by shape only. Manual files are not used here.
"""
import json
import re
import sys
from collections import defaultdict

from gram.base import words
from gram.pipeline import LibraryError, parse_text

MAX_GROUPS = 40  # the largest groups get IDs and must be decided in RECONCILE.md


def shape(clause):
    c = re.sub(r"(?i)\b(?:youth\s*|y)\d+\b", "<Y>", clause)
    c = re.sub(r"(?i)\bevent-p-\d+-\d+\b", "<E>", c)
    c = re.sub(r"(?i)\bp-\d+\b", "<P>", c)
    c = re.sub(r"\b[A-Z]\.\s*[A-Z][a-z]+\b|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", "<N>", c)
    return re.sub(r"\d+", "<D>", c).strip()


def signature(c):
    bag = sorted(w for f in c.get("facts", []) for v in [f.get("subject", ""), f.get("object", "")] + list(f.get("qualifiers", [])) for w in words(v))
    return (c["status"] if c["status"] in ("parsed", "ignored") else "unresolved", tuple(bag))


def diff_libraries(libs, docs):
    per = {}
    for k, lib in libs.items():
        per[k] = {}
        for d, path in docs.items():
            try:
                recs = parse_text(open(path, encoding="utf-8").read(), lib)
            except LibraryError as e:
                recs = []
                per[k]["_error"] = str(e)
            for r in recs:
                for i, c in enumerate(r["clauses"]):
                    per[k][(d, r["line"], i, c["text"])] = c
    keys = set().union(*[set(x) for x in per.values()]) - {"_error"}
    groups = defaultdict(list)
    for key in sorted(keys, key=lambda x: (x[0], x[1], x[2])):
        sigs = {k: signature(per[k][key]) if key in per[k] else ("missing", ()) for k in libs}
        if len(set(sigs.values())) > 1:
            groups[shape(key[3])].append((key, {k: per[k].get(key) for k in libs}))
    ordered = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    ids, out = [], ["# Disagreements between the libraries on the training documents", ""]
    for k in libs:
        if "_error" in per[k]:
            out.append("Library %s did not load: %s" % (k, per[k]["_error"]))
    out.append("%d groups, %d clauses in all. Each group: clause shape, count, up to 3 examples with each library's "
               "status and facts.\n" % (len(ordered), sum(len(v) for _, v in ordered)))
    for n, (sh, items) in enumerate(ordered, 1):
        if n > MAX_GROUPS:
            if n == MAX_GROUPS + 1:
                out.append("## Smaller groups (no ID; decide where you can)\n")
            out.append("- (%d clauses) shape: %s; e.g. `%s`" % (len(items), sh, items[0][0][3][:150]))
            continue
        gid = "G%02d" % n
        ids.append(gid)
        out.append("## %s  (%d clauses)  shape: %s\n" % (gid, len(items), sh))
        for (d, line, _, text), res in items[:3]:
            out.append("- %s line %d: `%s`" % (d, line, text))
            for k, c in res.items():
                if c is None:
                    out.append("  - lib_%s: (clause not produced by its splitter)" % k)
                else:
                    out.append("  - lib_%s: %s %s" % (k, c["status"], json.dumps(c.get("facts", []))[:400]))
        out.append("")
    return ids, "\n".join(out)


if __name__ == "__main__":
    libs = dict(zip("abc", sys.argv[1:4]))
    ids, md = diff_libraries(libs, {"doc%d" % i: p for i, p in enumerate(sys.argv[4:7], 1)})
    print(md)
