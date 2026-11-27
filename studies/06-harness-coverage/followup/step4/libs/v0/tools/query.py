"""Answers the three final queries from parse output.
Usage: python lib/tools/query.py OUTDIR1 OUTDIR2 OUTDIR3 > answers.json   (OUTDIRn = `gram parse --out` dir of docN)
Joins names to person IDs by union-find: has_id, id_hint (event ids), also_called, and unique (initial, surname)."""
import collections, json, re, sys

COAST = {"Halifax", "Vancouver", "Victoria", "St. John's", "Lunenburg"}
FRUIT = {"apple", "banana", "pear", "mango", "peach", "orange", "plum", "watermelon"}
PUBLIC = {"bus", "train", "tram", "subway"}
PAST = {"no longer", "used to", "formerly", "in a former role", "in the past", "only in the past", "previously"}


def load(d):
    facts = []
    for l in open(d + "/parsed.jsonl", encoding="utf-8"):
        r = json.loads(l)
        facts += r["facts"]
    return facts


def people(facts):
    ids = collections.defaultdict(set)
    names = set()
    for f in facts:
        s = f["subject"]
        if f["relation"] in ("has_id", "id_hint"):
            ids[s].add(f["object"])
        if f["relation"] == "also_called":
            ids[f["object"]] |= set()
            names.add(f["object"])
        if not re.match(r"(Y\d|Org |P-|narrator)", s):
            names.add(s)
    for f in facts:
        if f["relation"] == "also_called":
            ids[f["object"]] |= ids[f["subject"]]
    groups = collections.defaultdict(set)
    for n in names:
        m = re.match(r"(\w)[\w'-]*\.? ([\w'-]+)$", n)
        if m:
            groups[(m.group(1).upper(), m.group(2))].add(n)
    for g in groups.values():
        fulls = [n for n in g if not re.match(r"\w\. ", n)]
        if len(fulls) == 1:
            u = set().union(*[ids[n] for n in g])
            for n in g:
                ids[n] |= u
    return {n: next(iter(i)) for n, i in ids.items() if len(i) == 1}, names


def cur(f):
    return not PAST & set(f["qualifiers"])


def answer(d):
    facts = load(d)
    pid, names = people(facts)
    P = collections.defaultdict(lambda: collections.defaultdict(list))
    for f in facts:
        if f["subject"] in pid:
            P[pid[f["subject"]]][f["relation"]].append(f)
    city = {f["subject"]: f["object"] for f in facts if f["relation"] == "based_in"}
    course = collections.defaultdict(list)
    for f in facts:
        if f["relation"] == "attends_course":
            course[f["subject"]].append(f)
    C = {
        "coast": lambda r: any(city.get(f["object"]) in COAST and cur(f) for f in r["works_for"]),
        "public": lambda r: any(f["object"] in PUBLIC and "routinely" in f["qualifiers"] and cur(f) for f in r["travels_by"]),
        "night": lambda r: any(f["object"] == "night" and cur(f) for f in r["works_shift"]),
        "vol3": lambda r: len({f["object"] for f in r["volunteered_at"] if "this-year" in f["qualifiers"]}) >= 3,
        "dairy": lambda r: any(cur(f) for f in r["avoids"]),
        "guard": lambda r: any("evening" in c["qualifiers"] and "currently" in c["qualifiers"]
                               for f in r["legal_guardian_of"] for c in course[f["object"]]),
        "train": lambda r: any(f["object"] == "train over plane" and "genuinely" in f["qualifiers"]
                               and "when both are available" in f["qualifiers"] for f in r["prefers_over"]),
        "fruit": lambda r: any(f["object"] in FRUIT and cur(f) for f in r["enjoys_eating"]),
    }
    unresolved = {f["subject"] for f in facts if f["subject"] in names and f["subject"] not in pid}
    return P, C, unresolved


Q = {1: ["coast", "public", "night"], 2: ["coast", "vol3", "dairy", "public"], 3: ["vol3", "guard", "train", "fruit", "dairy"]}

if __name__ == "__main__":
    out = {}
    for i, d in enumerate(sys.argv[1:4], 1):
        P, C, un = answer(d)
        res = sorted(p for p, r in P.items() if all(C[k](r) for k in Q[i]))
        print("doc%d" % i, {k: sum(C[k](r) for r in P.values()) for k in Q[i]}, len(res), "unresolved names:", len(un), file=sys.stderr)
        out["doc%d" % i] = res
    print(json.dumps(out))
