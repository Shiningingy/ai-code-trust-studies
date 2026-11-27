"""Helpers for answering queries from the facts the library produces. Not a grammar part (it lives outside parts/).

    python -m gram parse doc.md --lib lib --manual doc.manual.jsonl --out out
    from lib.query import Facts          (or: sys.path.insert(0, "lib"); from query import Facts)
    F = Facts("out/parsed.jsonl")
    F.ids()                              every person id (P-114 ...)
    F.of("P-114", "works_for")           facts about a person (all written forms joined), optionally one relation
    F.current(facts)                     drop past / future / one-off / negated / hearsay-only ... (see below)

Written forms of a person ("Nadia Reed", "N. Reed", "nadia reed", "I" inside her own quote) are joined through the
roster facts (<name> has_id P-114). See NOTES.md for relations and qualifiers.
"""
import collections
import json

FRUITS = {"apple", "banana", "mango", "orange", "peach", "pear", "plum", "watermelon", "grapes", "cherry",
          "strawberry", "kiwi", "lemon", "lime", "apricot", "pineapple", "melon", "blueberry", "raspberry"}
DAIRY = {"milk", "cheese", "butter", "yogurt", "cream", "ice cream", "dairy products", "dairy"}
PUBLIC_TRANSPORT = {"bus", "tram", "train", "subway", "metro", "light rail", "streetcar", "underground", "ferry",
                    "coach"}
# Cities of the documents; coastal = on an ocean (Atlantic/Pacific) coast.
COASTAL = {"Halifax", "Lunenburg", "St. John's", "Vancouver", "Victoria", "Charlottetown", "Saint John",
           "Prince Rupert", "Nanaimo", "Sydney", "Yarmouth", "Gaspé", "Iqaluit"}
INLAND = {"Calgary", "Edmonton", "Ottawa", "Regina", "Winnipeg", "Saskatoon", "Toronto", "Montreal", "Quebec City",
          "Fredericton", "Whitehorse", "Yellowknife", "Kelowna", "Kamloops", "Red Deer", "Lethbridge", "Brandon"}

NOT_NOW = ("time:past", "time:future", "neg", "freq:once")


class Facts:
    def __init__(self, parsed_jsonl):
        self.facts = []
        for line in open(parsed_jsonl, encoding="utf-8"):
            r = json.loads(line)
            for f in r["facts"]:
                f = dict(f, line=r["line"])
                self.facts.append(f)
        self.alias = collections.defaultdict(set)      # written form -> {P-id}
        for f in self.facts:
            if f["relation"] == "has_id":
                self.alias[f["subject"].lower()].add(f["object"])
        self.by_id = collections.defaultdict(list)
        for f in self.facts:
            for i in self.resolve(f["subject"]):
                self.by_id[i].append(f)

    def resolve(self, name):
        """Person ids for a written name (empty if unknown, several if the written form is ambiguous)."""
        if name.startswith("P-"):
            return {name}
        return self.alias.get(name.lower(), set())

    def ids(self):
        return sorted({i for s in self.alias.values() for i in s})

    def of(self, pid, relation=None, obj=None):
        return [f for f in self.by_id.get(pid, []) if (relation is None or f["relation"] == relation)
                and (obj is None or f["object"] == obj)]

    def subject_facts(self, subject, relation=None):
        """Facts whose subject is a non-person entity (Organization 010, Y118)."""
        return [f for f in self.facts if f["subject"] == subject and (relation is None or f["relation"] == relation)]

    @staticmethod
    def current(facts, drop=NOT_NOW):
        """Facts that hold now: without time:past / time:future / neg / freq:once (or the qualifiers given)."""
        return [f for f in facts if not any(q in drop for q in f["qualifiers"])]

    @staticmethod
    def has(f, *quals):
        return all(q in f["qualifiers"] for q in quals)
