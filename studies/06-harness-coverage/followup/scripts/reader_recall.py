"""Recall of the small-model reader on the facts that decide the answer (instance 00041).

Gold = every sentence about an answer person (any alias, case-insensitive) or their youth that touches one of the
five conditions, found here with deliberately broad keywords and printed for a human check. Also the known traps.
Usage: python -I reader_recall.py <out_dir of haiku_reader.py>
"""
import json
import os
import re
import sys

d = sys.argv[1]
S = json.load(open(os.path.join(d, "sentences.json"), encoding="utf-8"))
F = set(json.load(open(os.path.join(d, "flagged.json"), encoding="utf-8"))["flagged"])
ANS = {"P-051": None, "P-055": None, "P-057": None, "P-104": None, "P-127": None}
COND = re.compile(r"volunteer|event-|guardian|youth|\by\d{3}\b|evening|train|plane|fly|eat|fruit|dairy|milk|cheese|yogurt|butter", re.I)
roster = {}
for s in S:
    m = re.search(r"records (.+?) under identifier (p-\d+)(?: and also uses the familiar names (.+?))?\.?$", s, re.I)
    if m and m.group(2).upper() in ANS:
        names = [m.group(1)] + ([x.strip() for x in re.split(r",| and ", m.group(3) or "") if x.strip()] if m.group(3) else [])
        roster.setdefault(m.group(2).upper(), set()).update(n.lower().rstrip(".") for n in names)
print("roster:", {k: sorted(v) for k, v in roster.items()})
miss_total = 0
for pid, names in sorted(roster.items()):
    num = pid[2:]
    pat = re.compile(r"\b(" + "|".join(re.escape(n) for n in names) + r")\b|\b(youth " + num + r"|y" + num + r")\b|event-" + pid, re.I)
    rows = [(i, s) for i, s in enumerate(S) if pat.search(s) and COND.search(s)]
    hit = sum(i in F for i, _ in rows)
    miss_total += len(rows) - hit
    print("\n%s: %d of %d condition sentences flagged" % (pid, hit, len(rows)))
    for i, s in rows:
        print("  %s [%d] %s" % ("ok  " if i in F else "MISS", i, s[:150]))
TRAPS = ["youth 104 currently attends evening_pottery", "I genuinely prefer train to plane", "enjoys eating mango in the past"]
print()
for t in TRAPS:
    for i, s in enumerate(S):
        if t in s:
            print("trap %s [%d]: %s" % ("flagged" if i in F else "NOT FLAGGED", i, s[:140]))
print("\nflagged %d of %d sentences; condition-sentence misses for answer people: %d" % (len(F), len(S), miss_total))
