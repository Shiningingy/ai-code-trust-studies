import re, json, collections
from check_coverage import split_statements, classify_irrelevant

text = open("context.md", encoding="utf8").read()
stmts = split_statements(text)
stmts = stmts[:next(i for i,x in enumerate(stmts) if x.startswith("#") and "Final Query" in x)]
SUR = r"(?:Reed|Silva|Novak|Khan|Bennett|Mensah|Ito|Diaz|Evans|Jones|Laurent|Chen|Tran|Patel|Ortiz|Haddad|Gupta|Foster|Usman|Avery)"
NAME = r"(?P<n>[A-Za-z]+\.? " + SUR + r")"
def norm(n): return re.sub(r"\s+", " ", n.lower())
SP = r"(?:said|explained|added|continued|concluded)"
facts = []
roster = collections.defaultdict(set)
def add(kind, s, **kw): facts.append(dict(kind=kind, statement=s, **kw))

# pass 1: roster
for s in stmts:
    m = re.search(r"records (?P<f>[A-Za-z]+\.? " + SUR + r") under identifier (?P<id>P-\d+) and also uses the familiar names? (?P<a>.+?)\.?\"?$", s, re.I)
    if m:
        pid = m.group("id").upper()
        names = [m.group("f")] + [x.strip() for x in re.split(r",| and ", m.group("a")) if x.strip()]
        for n in names: roster[norm(n.rstrip("."))].add(pid) if False else roster[norm(n)].add(pid)
        add("roster", s, id=pid, names=names)

speaker = None
for s in stmts:
    if s.startswith("#"): speaker = None; continue
    if classify_irrelevant(s) and not re.search(r"familiar names", s): 
        m = re.search(NAME + r" " + SP + r"[,§]? ?\"?(?:I|she|he|they)\b", s, re.I)
        if m: speaker = norm(m.group("n"))
        continue
    who = None
    m = re.search(NAME + r" (?:" + SP + r"[,]? ?\"?(?:she|he|they|I)? ?)?", s, re.I)
    m2 = re.search(NAME + r" " + SP + r",? ?\"?(?:I|she|he|they)\b", s, re.I)
    if m2: speaker = norm(m2.group("n"))
    if "familiar names" in s: continue
    subj = None
    mm = re.search(r"(?:^|[\s\"])" + NAME + r"\b", s, re.I)
    if re.search(r"^\"?I\b", s) and speaker: subj = speaker
    elif mm: subj = norm(mm.group("n"))
    elif speaker: subj = speaker
    got = False
    m = re.search(r"works? for (?:Org|Organization) (\d+)", s, re.I)
    if m: add("works", s, who=subj, org=int(m.group(1))); got = True
    m = re.search(r"(?:Org|Organization) (\d+) is based in (.+?)\.?$", s, re.I)
    if m: add("based", s, org=int(m.group(1)), city=m.group(2).strip()); got = True
    m = re.search(r"volunteered at (event-P-\d+-\d+) during this-year", s, re.I)
    if m: add("event", s, who=subj, event=m.group(1).upper()); got = True
    m = re.search(r"currently chooses? to avoid dairy products", s, re.I)
    if m: add("dairy", s, who=subj); got = True
    m = re.search(r"routinely travels? by (\w+)", s, re.I)
    if m: add("transport", s, who=subj, mode=m.group(1).lower()); got = True
    if not got and re.search(r"(?:Org|Organization) \d+", s) and False: pass

json.dump(dict(roster={k: sorted(v) for k, v in roster.items()}, facts=facts), open("extracted.json", "w", encoding="utf8"), indent=1)
print(len(facts), collections.Counter(f["kind"] for f in facts))

R = roster
CO = {"vancouver","victoria","halifax","st. john's","lunenburg"}
city = {f["org"]: f["city"] for f in facts if f["kind"] == "based"}
def pid(n):
    v = R.get(n, [])
    return next(iter(v)) if len(v) == 1 else None
ev = collections.defaultdict(set); dairy=set(); tr=set(); org=collections.defaultdict(set)
unres=[]
for f in facts:
    if "who" not in f: continue
    p = pid(f["who"])
    if not p: unres.append(f); continue
    if f["kind"]=="event": ev[p].add(f["event"])
    if f["kind"]=="dairy": dairy.add(p)
    if f["kind"]=="transport" and f["mode"] in ("bus","train","subway","tram"): tr.add(p)
    if f["kind"]=="works": org[p].add(f["org"])
print("unresolved", len(unres), unres[:5])
c1={p for p,o in org.items() if any(city.get(x,"").lower() in CO for x in o)}
c2={p for p,e in ev.items() if len(e)>=3}
ans=sorted(c1&c2&dairy&tr)
print(len(c1),len(c2),len(dairy),len(tr),ans)
json.dump({"matches":ans},open("answer.json","w"))
print({p:o for p,o in org.items() if len(o)>1})
for p in ans: print(p, org[p], [city.get(x) for x in org[p]], len(ev[p]))
print("orgs w/o city:", sorted({x for o in org.values() for x in o if x not in city}))
