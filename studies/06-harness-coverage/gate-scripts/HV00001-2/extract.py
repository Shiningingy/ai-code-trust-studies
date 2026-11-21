import re, json, collections
t = open('context.md', encoding='utf8').read()
COASTAL = {'halifax', 'lunenburg', 'vancouver', 'victoria', "st. john's"}
ALIAS = collections.defaultdict(set)
facts = []  # dicts: kind, line (1-based), start, end (offsets in line), + payload
lines = t.split('\n')
NAME = r"(?:[A-Za-z]\.|[A-Za-z]+) [A-Za-z]+"
SPEAK = re.compile(r"(%s) (?:said|added|explained|continued|concluded|mentioned|noted)\b" % NAME)
ROSTER = re.compile(r"records (%s) under identifier (P-\d+) and also uses the familiar names? (%s)" % (NAME, NAME), re.I)
for ln, l in enumerate(lines, 1):
    for m in ROSTER.finditer(l):
        pid = m.group(2).upper()
        ALIAS[m.group(1).lower()].add(pid); ALIAS[m.group(3).lower()].add(pid)
        facts.append(dict(kind='alias', line=ln, start=m.start(), end=m.end(), id=pid))

def subject(l, pos):
    pre = l[:pos]
    if re.search(r"\b(?:I|he|she) $", pre):
        sp = list(SPEAK.finditer(pre))
        return sp[-1].group(1) if sp else None
    m = re.search(r"(%s) $" % NAME, pre)
    return m.group(1) if m else None

def resolve(n):
    if n is None: return None
    s = ALIAS.get(n.lower().strip(), set())
    return next(iter(s)) if len(s) == 1 else None

unresolved = []
def add(kind, ln, l, m, **kw):
    n = subject(l, m.start())
    pid = kw.pop('pid', None) or resolve(n)
    if pid is None: unresolved.append((ln, n, l[m.start():m.end()]))
    facts.append(dict(kind=kind, line=ln, start=m.start(), end=m.end(), id=pid, subject=n, **kw))

P = {
 'dairy': r"(?:currently )?chooses? to avoid dairy products",
 'works': r"(?:currently )?works? for (?:Org|Organization) (\d+)",
 'travel': r"routinely travels by (\w+)(?: to get around the city)?( but no longer does)?",
 'vol': r"volunteered at (old-)?event-(P-\d+)(?:-(\d+))? during (this|last)-year",
 'based': r"(?:Org|Organization) (\d+) is based in (St\. John's|[A-Z][a-z]+)",
}
QSTART = next(i for i, l in enumerate(lines, 1) if l.startswith('### Final Query'))
for ln, l in enumerate(lines, 1):
    if ln >= QSTART: break
    for m in re.finditer(P['dairy'], l, re.I): add('dairy', ln, l, m)
    for m in re.finditer(P['works'], l, re.I): add('works', ln, l, m, org=m.group(1))
    for m in re.finditer(P['travel'], l, re.I):
        add('travel', ln, l, m, mode=m.group(1).lower(), current=not m.group(2))
    for m in re.finditer(P['vol'], l, re.I):
        pid = m.group(2).upper()
        add('vol', ln, l, m, pid=pid, event=m.group(0).split(' during')[0].split('volunteered at ')[1], period=m.group(4).lower())
    for m in re.finditer(P['based'], l, re.I):
        facts.append(dict(kind='based', line=ln, start=m.start(), end=m.end(), org=m.group(1), city=m.group(2).strip()))

city = collections.defaultdict(set)
for f in facts:
    if f['kind'] == 'based': city[f['org']].add(f['city'].lower())
print('unresolved', unresolved)
print('org cities', {k: v for k, v in sorted(city.items())})
print('modes', collections.Counter(f['mode'] for f in facts if f['kind'] == 'travel'))
dairy = {f['id'] for f in facts if f['kind'] == 'dairy' and f['id']}
trav = collections.defaultdict(list)
for f in facts:
    if f['kind'] == 'travel': trav[f['id']].append(f['current'])
work = collections.defaultdict(set)
for f in facts:
    if f['kind'] == 'works': work[f['id']].add(f['org'])
evs = collections.defaultdict(set)
for f in facts:
    if f['kind'] == 'vol' and f['period'] == 'this': evs[f['id']].add(f['event'])
print('multi-org', {k: v for k, v in work.items() if len(v) > 1})
print('multi-trav', {k: v for k, v in trav.items() if len(set(v)) > 1})
matches = []
for pid in sorted(set(f['id'] for f in facts if f.get('id'))):
    c1 = any(city.get(o) and city[o] & COASTAL for o in work.get(pid, ()))
    c2 = len(evs.get(pid, ())) >= 3
    c3 = pid in dairy
    c4 = any(trav.get(pid, [])) 
    if c1 and c2 and c3 and c4: matches.append(pid)
    if sum([c1, c2, c3, c4]) >= 3: print(pid, c1, c2, c3, c4)
print(matches)
json.dump(dict(facts=facts, alias={k: sorted(v) for k, v in ALIAS.items()}, org_city={k: sorted(v) for k, v in city.items()}, matches=matches), open('extracted.json', 'w'), indent=1)
