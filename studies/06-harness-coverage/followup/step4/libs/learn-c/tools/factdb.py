"""Query helpers over the facts produced by the grammar library (see lib/NOTES.md).

Usage:
    python -m gram parse train/docN.md --lib lib --manual train/docN.manual.jsonl --out out
    from lib.tools.factdb import DB   (or add lib/tools to sys.path)
    db = DB.from_parsed("out/parsed.jsonl")
    db.facts("P-001")            -> every fact about that person (subject names resolved to person IDs)
    db.has("P-001", "works_for") -> facts of one relation, optionally filtered with qualifiers
"""
import json
import re
from collections import defaultdict

COASTAL_CITIES = {"halifax", "victoria", "vancouver", "st. john's", "lunenburg"}   # world knowledge: cities on a coast
INLAND_CITIES = {"edmonton", "winnipeg", "regina", "calgary", "ottawa"}              # ottawa: river city, not coastal
PUBLIC_TRANSPORT = {"bus", "train", "tram", "subway"}
FRUITS = {"apple", "banana", "mango", "watermelon", "pear", "peach", "plum", "orange", "grape", "cherry", "berry", "strawberry",
          "pineapple", "melon", "kiwi", "lemon", "lime", "papaya", "apricot", "fig"}
DAIRY = {"milk", "cheese", "yogurt", "butter", "cream", "ice cream", "dairy products"}


class DB:
    def __init__(self, facts):
        self.raw = facts
        self.full_id = {}            # 'Nadia Reed' -> 'P-114'
        self.fam = defaultdict(set)  # 'N. Reed' -> {'P-114'}
        for f in facts:
            if f["relation"] == "has_id":
                self.full_id[f["subject"]] = f["object"]
        for f in facts:
            if f["relation"] == "familiar_name" and f["subject"] in self.full_id:
                self.fam[f["object"]].add(self.full_id[f["subject"]])
        # event ids embed the volunteer's person id: event-P-008-2, old-event-P-001
        self.event_id = {}
        for f in facts:
            if f["relation"] == "volunteered_at":
                m = re.search(r"(P-\d+)", f["object"])
                if m:
                    self.event_id.setdefault(f["subject"], set()).add(m.group(1))
        self.by_person = defaultdict(list)
        self.unresolved = defaultdict(list)
        for f in facts:
            if f["relation"] in ("has_id", "familiar_name"):
                continue
            pid = self.resolve(f["subject"])
            (self.by_person[pid] if pid else self.unresolved[f["subject"]]).append(f)
        self.org_city = {}
        for f in facts:
            if f["relation"] == "based_in":
                self.org_city.setdefault(f["subject"], set()).add(f["object"])

    @classmethod
    def from_parsed(cls, path):
        facts = []
        for line in open(path, encoding="utf-8"):
            facts.extend(json.loads(line)["facts"])
        return cls(facts)

    def resolve(self, name):
        if name in self.full_id:
            return self.full_id[name]
        if name in self.fam and len(self.fam[name]) == 1:
            return next(iter(self.fam[name]))
        # a full name and its initial form ('Farah Silva' / 'F. Silva') are the same person
        parts = name.split(" ", 1)
        if len(parts) == 2 and not parts[0].endswith("."):
            ini = parts[0][0].upper() + ". " + parts[1]
            if ini in self.full_id:
                return self.full_id[ini]
            if ini in self.fam and len(self.fam[ini]) == 1:
                return next(iter(self.fam[ini]))
        elif len(parts) == 2:
            cands = {i for n, i in self.full_id.items() if n.split(" ", 1)[-1] == parts[1] and n[0].upper() == parts[0][0].upper()}
            if len(cands) == 1:
                return next(iter(cands))
        ids = self.event_id.get(name)
        if ids and len(ids) == 1:
            return next(iter(ids))
        return None

    def people(self):
        return sorted(set(self.full_id.values()))

    def facts(self, pid):
        return self.by_person.get(pid, [])

    def has(self, pid, relation, obj=None, without=(), with_=()):
        out = []
        for f in self.facts(pid):
            if f["relation"] != relation:
                continue
            if obj is not None and f["object"] not in (obj if isinstance(obj, (set, list, tuple)) else [obj]):
                continue
            q = set(f["qualifiers"])
            if any(w in q for w in without) or not all(w in q for w in with_):
                continue
            out.append(f)
        return out

    # --- the conditions used by the training queries -------------------------------------------------------------
    def works_for_coastal_org(self, pid):
        for f in self.has(pid, "works_for", without=("past",)):
            if self.org_city.get(f["object"], set()) & COASTAL_CITIES:
                return True
        return False

    def uses_public_transport(self, pid):
        """routinely travels by bus/train/tram/subway and has not stopped (no 'no_longer'/'past')."""
        return bool(self.has(pid, "travels_by", PUBLIC_TRANSPORT, without=("past", "no_longer")))

    def works_night_shift(self, pid):
        return bool(self.has(pid, "works_shift", "night", without=("past",)))

    def volunteer_events_this_year(self, pid):
        return {f["object"] for f in self.has(pid, "volunteered_at", with_=("this-year",))}

    def avoids_dairy(self, pid):
        return bool(self.has(pid, "avoids", "dairy products", without=("past",)))

    def guardian_of_evening_course_attendee(self, pid):
        for f in self.has(pid, "legal_guardian_of"):
            y = f["object"]
            for g in self.by_person_youth(y):
                if g["relation"] == "attends_course" and "evening" in g["qualifiers"] and "past" not in g["qualifiers"]:
                    return True
        return False

    def by_person_youth(self, y):
        return self.unresolved.get(y, [])

    def prefers_train(self, pid):
        return bool(self.has(pid, "prefers", "train"))

    def enjoys_fruit(self, pid):
        return bool(self.has(pid, "enjoys_eating", FRUITS, without=("past",)))
