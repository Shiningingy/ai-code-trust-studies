import json, collections
r = json.load(open("extracted.json", encoding="utf8"))["statements"]
P = [x for x in r if x["class"] == "placed"]
def norm(n): return " ".join(n.lower().split())
name2id = {}
for x in P:
    if x["fact"] == "roster":
        a = x["args"]; pid = a["id"].upper()
        name2id[norm(a["full"])] = pid
        if a["fam"]: name2id[norm(a["fam"])] = pid
city = {}
for x in P:
    if x["fact"] == "org_city": city[x["args"]["o"]] = x["args"]["c"]
print(city)
import sys
COAST = {"halifax", "st. john's", "vancouver", "lunenburg", "victoria", "charlottetown", "saint john"}
works = collections.defaultdict(set); night = set(); trav = set(); miss = []
for x in P:
    a = x["args"]
    if x["fact"] in ("works_for", "night", "travel"):
        pid = name2id.get(norm(a["n"]))
        if not pid: miss.append(x["text"]); continue
        if x["fact"] == "works_for": works[pid].add(a["o"])
        elif x["fact"] == "night": night.add(pid)
        else: trav.add(pid)
print("unresolved", miss)
res = sorted(p for p in night & trav if any(city.get(o, "").lower() in COAST for o in works.get(p, ())))
print(len(night), len(trav), len(works), res)
json.dump({"matches": res}, open("answer.json", "w"))
