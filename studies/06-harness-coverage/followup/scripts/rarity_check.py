"""Generic harness-side cue that needs no reading: how rare is each sentence's shape?
Shape = sentence with Capitalised words -> C and digits -> N (case kept, nothing task-specific)."""
import re
import sys
from collections import Counter

TRAPS = ["The community roster records amina foster under identifier p-101",
         "The same account also says that organization 007 is based in Lunenburg",
         "The same account also says that youth 104 currently attends evening_pottery during the evening",
         "currently works for Org 005"]


def sentences(path):
    out = []
    for line in open(path, encoding="utf-8").read().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if len(s.strip()) >= 12]
    return out


def shape(s):
    s = re.sub(r"\b[A-Z][a-zA-Z']*\b", "C", s)
    s = re.sub(r"\d+", "N", s)
    return re.sub(r"(C[ .]*)+", "C ", s).strip()


for path in sys.argv[1:]:
    S = sentences(path)
    cnt = Counter(shape(s) for s in S)
    for k in (1, 2, 5):
        n = sum(1 for s in S if cnt[shape(s)] <= k)
        print("%s: %d sentences, %d shapes; sentences in shapes seen <=%d times: %d" % (path[-16:], len(S), len(cnt), k, n))
    for t in TRAPS:
        for s in S:
            if t in s:
                print("   trap shape count %d: %s" % (cnt[shape(s)], shape(s)[:110]))
                break
