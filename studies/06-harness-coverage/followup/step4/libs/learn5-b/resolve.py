"""Helpers for later sessions: parse a document with the library and resolve names to person ids.

    from lib.resolve import load_facts, Resolver
    facts = load_facts("train/doc1.md", "train/doc1.manual.jsonl")      # list of facts, each with "line"
    R = Resolver(facts); R.pid("N. Reed")   # -> "P-114"
"""
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_facts(doc, manual=None, lib=None):
    sys.path.insert(0, ROOT)
    from gram.pipeline import parse_text
    text = open(doc, encoding="utf-8").read()
    recs = parse_text(text, lib or os.path.join(ROOT, "lib"), manual if manual and os.path.exists(manual) else None)
    out = []
    for r in recs:
        for c in r["clauses"]:
            for f in c.get("facts", []) or []:
                g = dict(f)
                g["line"] = r["line"]
                out.append(g)
    return out


class Resolver:
    """Names -> P-ids from the roster facts (has_id / alias). Initial+surname forms are unique per roster."""

    def __init__(self, facts):
        self.ids = defaultdict(set)
        for f in facts:
            if f["relation"] == "has_id":
                self.ids[f["subject"]].add(f["object"])
        for f in facts:
            if f["relation"] == "alias":
                self.ids[f["object"]] |= self.ids.get(f["subject"], set())
        # initial+surname keys: every roster name (full or already abbreviated) maps to "X. Surname" -> ids.
        # The first names of a corpus have distinct initials, so an unlisted full name ("Farah Silva") whose roster entry is
        # only abbreviated ("F. Silva") still resolves.
        self.by_init = defaultdict(set)
        for n, s in list(self.ids.items()):
            m = re.fullmatch(r"([A-Za-z])[A-Za-z]*\.? ([A-Z][a-z]+)", n)
            if m:
                self.by_init[m.group(1).upper() + ". " + m.group(2)] |= s

    def pid(self, name):
        s = self.ids.get(name)
        if not s:
            m = re.fullmatch(r"([A-Za-z])[A-Za-z]*\.? ([A-Z][a-z]+)", name)
            s = self.by_init.get(m.group(1).upper() + ". " + m.group(2)) if m else None
        return next(iter(s)) if s and len(s) == 1 else None
