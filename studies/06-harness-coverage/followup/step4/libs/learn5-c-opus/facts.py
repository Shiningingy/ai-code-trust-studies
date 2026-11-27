"""Query helper for facts produced by `python -m gram parse <doc> --lib lib --out <dir>` (not a grammar part).

    from facts import Facts
    F = Facts("out/doc1/parsed.jsonl")
    F.pid("N. Reed")                       -> "P-114"
    F.of("P-114", "works_for")             -> facts about that person with that relation
    F.current(f)                           -> False for status:former / planned / temporary, freq:once
See NOTES.md for the relations and qualifiers.
"""
import json
import re
from collections import defaultdict

PRONOUNS = {"he", "she", "they"}


class Facts:
    def __init__(self, parsed_path):
        self.rows = [json.loads(l) for l in open(parsed_path, encoding="utf-8") if l.strip()]
        self.facts = []
        for r in self.rows:
            last = None
            for f in r["facts"]:
                f = dict(f, line=r["line"])
                # a pronoun subject left unresolved by the grammar refers to the last named person before it
                if f["subject"] in PRONOUNS and "coref:pronoun" in f["qualifiers"] and last:
                    f["subject"] = last
                elif re.match(r"[A-Z]", f["subject"]) and " " in f["subject"]:
                    last = f["subject"]
                self.facts.append(f)
        self.name_to_pid = defaultdict(set)
        for f in self.facts:
            if f["relation"] in ("has_name", "has_alias"):
                self.name_to_pid[f["object"]].add(f["subject"])
        self.by_pid = defaultdict(list)
        self.unresolved = defaultdict(list)
        for f in self.facts:
            p = self.pid(f["subject"])
            if p:
                self.by_pid[p].append(f)
            else:
                self.unresolved[f["subject"]].append(f)

    def pid(self, name):
        """Person ID for any written form of a name (full, initial, any case); None if unknown or ambiguous."""
        if re.fullmatch(r"P-\d+", name):
            return name
        ids = self.name_to_pid.get(name, set())
        if not ids:
            ids = self._by_initial(name)
        return next(iter(ids)) if len(ids) == 1 else None

    def _by_initial(self, name):
        """'Farah Silva' <-> 'F. Silva' when the roster only gives the other form: same first initial and surname,
        and only one person ID among all roster names of that shape."""
        m = re.fullmatch(r"([A-Z])[a-z.'-]* (\S+)", name)
        if not m:
            return set()
        ids = set()
        for n, ps in self.name_to_pid.items():
            k = re.fullmatch(r"([A-Z])[a-z.'-]* (\S+)", n)
            if k and k.groups() == m.groups():
                full_a, full_b = not name[1:2] == ".", not n[1:2] == "."
                if full_a and full_b and n != name:
                    continue  # two different full first names (Farah / Fatima) are different people
                ids |= ps
        return ids

    def persons(self):
        return sorted(p for p in self.by_pid if re.fullmatch(r"P-\d+", p))

    def of(self, pid, relation, obj=None):
        return [f for f in self.by_pid.get(pid, []) if f["relation"] == relation and (obj is None or f["object"] == obj)]

    def about(self, subject, relation):
        """Facts about a non-person subject (an organization 'Org 013' or a youth 'Y043')."""
        return [f for f in self.facts if f["subject"] == subject and f["relation"] == relation]

    @staticmethod
    def has(f, *quals):
        return all(q in f["qualifiers"] for q in quals)

    @staticmethod
    def current(f):
        """True unless the fact is negated, or marked former, planned, temporary or a one-off."""
        bad = {"neg", "status:former", "status:planned", "status:temporary", "freq:once"}
        return not bad.intersection(f["qualifiers"])
