"""Load the facts gram produced for a document and join them by person.

    python -m gram parse doc.md --lib lib --manual doc.manual.jsonl --out out
    python lib/facts.py out/parsed.jsonl            # prints a summary

    from facts import Facts
    F = Facts("out/parsed.jsonl")
    F.pid("N. Reed")            -> "P-114"   (full names and familiar names, any case)
    F.of("P-114")               -> every fact about that person (subject resolved to the person ID)
    F.find(relation="works_for")  -> facts, filtered by relation/object/qualifier tests
    F.orgs_in()                 -> {"Org 014": "Halifax", ...}
    F.youth_courses()           -> {"Y045": [fact, ...]}

See NOTES.md for the relations and qualifiers.
"""
import collections
import json
import re
import sys


def _key(name):
    s = re.sub(r"\s+", " ", name.strip().lower())
    return re.sub(r"^([a-z])\.\s?", r"\1. ", s)


class Facts:
    def __init__(self, parsed_path):
        self.rows = [json.loads(l) for l in open(parsed_path, encoding="utf-8") if l.strip()]
        self.facts = [dict(f, line=r["line"]) for r in self.rows for f in r["facts"]]
        self.names = {}                      # name key -> person ID
        self.full = {}                       # person ID -> full name
        for f in self.facts:
            if f["relation"] in ("has_name", "has_alias"):
                self.names[_key(f["object"])] = f["subject"]
                if f["relation"] == "has_name":
                    self.full[f["subject"]] = f["object"]
        # a full name also gives its familiar name "N. Reed" when the roster did not list it
        for k, pid in list(self.names.items()):
            parts = k.split(" ")
            if len(parts) == 2 and not parts[0].endswith("."):
                self.names.setdefault(parts[0][0] + ". " + parts[1], pid)
        self.unresolved = collections.Counter()
        for f in self.facts:
            f["pid"] = self.pid(f["subject"])
            if f["pid"] is None and not re.match(r"^(Org \d+|Y\d+|P-\d+)$", f["subject"]):
                self.unresolved[f["subject"]] += 1

    def pid(self, name):
        if re.fullmatch(r"P-\d+", name):
            return name
        k = _key(name)
        if k in self.names:
            return self.names[k]
        # a full name whose roster entry gives only the familiar form ("f. silva" under P-046)
        parts = k.split(" ")
        if len(parts) == 2 and not parts[0].endswith("."):
            return self.names.get(parts[0][0] + ". " + parts[1])
        return None

    def of(self, pid):
        return [f for f in self.facts if f["pid"] == pid]

    def find(self, relation=None, obj=None, has=(), lacks=(), subject_kind=None):
        """Facts with this relation, object (string or callable), all qualifiers in `has`, none in `lacks`."""
        out = []
        for f in self.facts:
            if relation and f["relation"] != relation:
                continue
            if obj is not None and not (obj(f["object"]) if callable(obj) else f["object"] == obj):
                continue
            q = set(f.get("qualifiers", []))
            if not set(has) <= q or set(lacks) & q:
                continue
            out.append(f)
        return out

    def orgs_in(self):
        return {f["subject"]: f["object"] for f in self.find("based_in")}

    def youth_courses(self):
        d = collections.defaultdict(list)
        for f in self.find("attends_course"):
            d[f["subject"]].append(f)
        return dict(d)


if __name__ == "__main__":
    F = Facts(sys.argv[1])
    print("facts:", len(F.facts), "people:", len(F.full))
    print("relations:", collections.Counter(f["relation"] for f in F.facts).most_common())
    print("unresolved subjects:", F.unresolved.most_common(20))
