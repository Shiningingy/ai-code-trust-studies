"""Query helper for facts parsed with this library (not a part; gram does not load it).

    python -m gram parse train/doc1.md --lib lib --manual train/doc1.manual.jsonl --out out/doc1
    python -c "import sys; sys.path.insert(0, 'lib'); import kb; k = kb.KB('out/doc1/parsed.jsonl'); ..."

KB joins every way a person is written ("Nadia Reed", "N. Reed", "nadia reed" -> all canonicalised by the rules to
"Nadia Reed" / "N. Reed") to the person id from the roster (has_id, also_known_as). See lib/NOTES.md.
"""
import json
import re
from collections import defaultdict

# qualifiers that make a fact not a present, ongoing state
NOT_CURRENT = {"past", "future", "once", "negated"}


class KB:
    def __init__(self, parsed_path):
        self.facts = []
        for line in open(parsed_path, encoding="utf-8"):
            r = json.loads(line)
            for f in r["facts"]:
                f = dict(f, line=r["line"])
                f.setdefault("object", "")
                f.setdefault("qualifiers", [])
                self.facts.append(f)
        self.name_to_pid = {}
        for f in self.facts:
            if f["relation"] == "has_id":
                self.name_to_pid[f["subject"]] = f["object"]
        for f in self.facts:
            if f["relation"] == "also_known_as" and f["subject"] in self.name_to_pid:
                self.name_to_pid.setdefault(f["object"], self.name_to_pid[f["subject"]])
        # a full name also stands for its initial form ("Nadia Reed" -> "N. Reed") when that is unambiguous
        derived = defaultdict(set)
        for name, pid in list(self.name_to_pid.items()):
            m = re.fullmatch(r"([A-Z])[a-z'-]+ (\S+)", name)
            if m:
                derived["%s. %s" % (m.group(1), m.group(2))].add(pid)
        for alias, pids in derived.items():
            if len(pids) == 1:
                self.name_to_pid.setdefault(alias, next(iter(pids)))
        self.by_pid = defaultdict(list)
        self.by_entity = defaultdict(list)
        for f in self.facts:
            self.by_entity[f["subject"]].append(f)
            pid = self.name_to_pid.get(f["subject"])
            if pid:
                self.by_pid[pid].append(f)

    def pid(self, name):
        return self.name_to_pid.get(name)

    def people(self):
        return sorted(set(self.name_to_pid.values()))

    def of(self, pid, relation=None, obj=None):
        """Facts about a person id, optionally filtered by relation and object."""
        return [f for f in self.by_pid.get(pid, []) if (relation is None or f["relation"] == relation)
                and (obj is None or f["object"] == obj)]

    def entity(self, subject, relation=None):
        """Facts about a non-person entity ('Org 027', 'Y045')."""
        return [f for f in self.by_entity.get(subject, []) if relation is None or f["relation"] == relation]

    @staticmethod
    def current(f):
        """True if a fact describes the present: no past/future/once/negated qualifier."""
        return not (NOT_CURRENT & set(f["qualifiers"]))

    @staticmethod
    def has(f, q):
        return q in f["qualifiers"]

    @staticmethod
    def qual(f, prefix):
        """Value of the first qualifier 'prefix:value', or None."""
        for q in f["qualifiers"]:
            if q.startswith(prefix + ":"):
                return q[len(prefix) + 1:]
        return None
