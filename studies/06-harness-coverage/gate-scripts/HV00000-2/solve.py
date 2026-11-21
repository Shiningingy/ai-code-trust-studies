import json, re, collections
d = json.load(open('extracted_statements.json', encoding='utf8'))
def key(n):
    a, b = n.lower().split()
    return (a[0], b)
roster = {}
for o in d:
    if o['status'] != 'placed': continue
    for f in o['detail']:
        if f[0] == 'roster':
            pid = f[2].upper()
            for n in (f[1], f[3]):
                if n:
                    k = key(n)
                    assert roster.get(k, pid) == pid, (k, roster[k], pid)
                    roster[k] = pid
city = {}
for o in d:
    if o['status'] != 'placed': continue
    for f in o['detail']:
        if f[0] == 'orgcity':
            c = f[2].strip(" .'") if False else f[2].strip()
            assert city.get(int(f[1]), c) == c; city[int(f[1])] = c
COAST = {'Halifax', "St. John's", 'Lunenburg', 'Vancouver', 'Victoria'}
works = collections.defaultdict(set); trans = collections.defaultdict(list); shift = collections.defaultdict(list)
unres = set()
for o in d:
    if o['status'] != 'placed': continue
    for f in o['detail']:
        k = f[0]
        if k in ('works', 'fp_works'): who, org = f[1], int(f[3])
        elif k == 'transport': who = f[1]; trans[who and key(who)].append((f[2].lower(), bool(f[3])))
        elif k == 'fp_transport': trans[key(f[1])].append((f[3].lower(), bool(f[2]) or bool(f[4])))
        elif k == 'transport_past': trans[key(f[1])].append((f[2], True))
        elif k == 'shift': shift[key(f[1])].append((f[2].lower(), bool(f[3])))
        elif k == 'fp_shift': shift[key(f[1])].append((f[3].lower(), 'used' in f[2] or bool(f[4])))
        elif k == 'shift_past': shift[key(f[1])].append(('night', True))
        if k in ('works', 'fp_works'): works[key(who)].add(org)
PUB = {'bus', 'train', 'tram', 'subway'}
res = []
for k in sorted(set(works) | set(trans) | set(shift)):
    if k not in roster: unres.add(k); continue
pid_of = roster
out = []
for k, orgs in works.items():
    if k not in roster: continue
    ok1 = any(city.get(o) in COAST for o in orgs)
    ok2 = any(m in PUB and not past for m, past in trans.get(k, []))
    ok3 = any(s == 'night' and not past for s, past in shift.get(k, []))
    if ok1 and ok2 and ok3: out.append(roster[k])
    if len(orgs) > 1: print('multi-org', k, orgs)
for k in trans:
    if len({(m, p) for m, p in trans[k]}) > 1: print('trans conflict', k, trans[k])
for k in shift:
    if len({(m, p) for m, p in shift[k]}) > 1: print('shift conflict', k, shift[k])
print('unresolved', unres, 'orgs without city', [o for s in works.values() for o in s if o not in city])
res = sorted(set(out))
json.dump({'matches': res}, open('answer.json', 'w'))
print(res)
print(sorted(set(city.values())))
inv = {v: k for k, v in roster.items()}
for p in res:
    k = inv[p]; print(p, k, works[k], trans[k], shift[k])
