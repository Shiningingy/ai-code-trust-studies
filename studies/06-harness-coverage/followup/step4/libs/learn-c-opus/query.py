"""Load the facts of a parsed document and join them to person IDs.  (Not a grammar part; see NOTES.md.)

    from query import Facts
    fx = Facts("out/doc1/parsed.jsonl")
    fx.people()                          # every person ID of the roster
    fx.of("P-114", "works_for")          # that person's facts with relation works_for
    fx.about("Organization 012", "based_in")
    fx.pid("N. Reed")                     # name form -> ID (None if unknown or ambiguous)

Name forms: the roster ("The community roster records Nadia Reed under identifier P-114 and also uses the familiar
names N. Reed") gives has_name / has_alias.  A mention resolves to an ID through those, or, failing that, through
initial + surname when exactly one roster person fits ("n. reed" -> "N. Reed" -> P-114).
"""
import json
import re
from collections import defaultdict

PUBLIC_TRANSPORT = {"bus", "train", "tram", "subway", "metro", "streetcar", "light rail", "ferry"}
COASTAL_CITIES = {"Halifax", "Vancouver", "Victoria", "St. John's", "Lunenburg", "Charlottetown", "Saint John",
                  "Sydney", "Yarmouth", "Prince Rupert", "Nanaimo", "Gaspe", "Rimouski", "Corner Brook"}
INLAND_CITIES = {"Edmonton", "Calgary", "Ottawa", "Regina", "Winnipeg", "Saskatoon", "Toronto", "Montreal",
                 "Fredericton"}
FRUITS = {"apple", "banana", "pear", "peach", "mango", "orange", "plum", "watermelon", "grape", "grapes", "cherry",
          "cherries", "strawberry", "strawberries", "blueberry", "blueberries", "kiwi", "pineapple", "lemon", "lime",
          "apricot", "melon", "papaya", "fig", "raspberry", "raspberries"}
DAIRY = {"dairy products", "dairy", "milk", "cheese", "butter", "yogurt", "cream", "ice cream"}


def short(name):
    """'Nadia Reed' -> 'N. Reed'."""
    p = name.split()
    return "%s. %s" % (p[0][0].upper(), p[-1]) if len(p) >= 2 else name


class Facts:
    def __init__(self, parsed_path):
        self.facts = []
        for row in open(parsed_path, encoding="utf-8"):
            r = json.loads(row)
            for f in r["facts"]:
                f = dict(f, line=r["line"])
                f.setdefault("object", "")
                f.setdefault("qualifiers", [])
                self.facts.append(f)
        self.names = defaultdict(set)          # name form -> IDs
        self.full = {}                         # ID -> full name
        for f in self.facts:
            if f["relation"] in ("has_name", "has_alias"):
                self.names[f["object"].lower()].add(f["subject"])
                if f["relation"] == "has_name":
                    self.full.setdefault(f["subject"], f["object"])
        for pid, n in self.full.items():
            if "." not in n.split()[0]:
                self.names.setdefault("@" + short(n).lower(), set()).add(pid)
        self.by_subject = defaultdict(list)
        for f in self.facts:
            if f["relation"] in ("has_name", "has_alias"):
                continue
            key = self.pid(f["subject"]) or f["subject"]
            self.by_subject[key].append(f)

    def pid(self, name):
        """Person ID for a name form, or None."""
        if re.fullmatch(r"P-\d+", name):
            return name
        ids = self.names.get(name.lower())
        if not ids and "." in name.split()[0]:
            # 'N. Reed' for a roster person registered as 'Nadia Reed'
            ids = self.names.get("@" + short(name).lower())
        if not ids and "." not in name.split()[0]:
            # 'Farah Silva' for a roster person registered only as 'F. Silva'
            ids = {i for i in self.names.get(short(name).lower(), set())
                   if "." in self.full.get(i, ".").split()[0]}
        return next(iter(ids)) if ids and len(ids) == 1 else None

    def people(self):
        return sorted(self.full)

    def of(self, subject, relation=None):
        """Facts about a person ID (any name form joined) or any other subject ('Organization 012', 'Youth 040')."""
        return [f for f in self.by_subject.get(subject, []) if relation is None or f["relation"] == relation]

    about = of


def current(f):
    """True unless the fact is marked as past, planned, one-off or negated."""
    return not {"past", "future", "planned", "once", "negated"} & set(f["qualifiers"])
