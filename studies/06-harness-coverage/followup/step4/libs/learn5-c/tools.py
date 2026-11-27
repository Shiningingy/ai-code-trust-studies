"""Helpers for answering queries from the facts the library produces (not a grammar part; see NOTES.md).

    from lib.tools import Facts           # or: sys.path.insert(0, "lib"); from tools import Facts
    F = Facts.from_document("train/doc1.md", "train/doc1.manual.jsonl")
    F.who(lambda f: f["relation"] == "works_shift" and f["object"] == "night" and F.current(f))

Every fact is a dict {subject, relation, object, qualifiers, line, clause}; F.pid(subject) gives the person ID (P-nnn).
"""
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

COASTAL = {"Halifax", "Vancouver", "Victoria", "St. John's", "Lunenburg"}   # per-document: check the based_in cities
PUBLIC = {"subway", "bus", "train", "tram"}
FRUITS = {"apple", "banana", "pear", "mango", "plum", "peach", "orange", "watermelon"}
PAST = {"past"}


class Facts:
    def __init__(self, facts):
        self.facts = facts
        self.ids = {}                                   # written form of a name -> person ID
        for f in facts:
            if f["relation"] == "has_id":
                self.ids[f["subject"]] = f["object"]
        for f in facts:
            if f["relation"] == "also_known_as" and f["subject"] in self.ids:
                self.ids.setdefault(f["object"], self.ids[f["subject"]])
        # an event id 'event-P-020-0' / 'old-event-P-020' carries the ID of the volunteer
        for f in facts:
            if f["relation"] == "volunteered_at":
                m = re.search(r"P-\d+", f["object"])
                if m:
                    self.ids.setdefault(f["subject"], m.group(0))

    @classmethod
    def from_document(cls, doc, manual=None):
        from gram.pipeline import parse_text
        text = open(doc, encoding="utf-8").read()
        recs = parse_text(text, os.path.join(HERE), manual)
        facts = []
        for r in recs:
            for i, c in enumerate(r["clauses"]):
                for f in c.get("facts", []):
                    facts.append(dict(f, line=r["line"], clause=i))
        return cls(facts)

    def pid(self, subject):
        return self.ids.get(subject)

    def by(self, relation):
        return [f for f in self.facts if f["relation"] == relation]

    @staticmethod
    def current(f):
        """True unless the fact is marked as over / not now (past, once, future, temporary...)."""
        return not set(f["qualifiers"]) & {"past", "once", "future", "temporary", "not guardian", "does not eat"}

    def people(self, pred):
        return {self.pid(f["subject"]) or f["subject"] for f in self.facts if pred(f)}

    def who(self, pred):
        return sorted(p for p in self.people(pred) if p and p.startswith("P-"))

    def org_city(self):
        return {f["subject"]: f["object"] for f in self.by("based_in")}
