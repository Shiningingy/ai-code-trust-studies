"""Build extracted.json from context.md and compute the answer."""
import json, collections
from split import statements
from extract import classify

COASTAL = {'Halifax', 'Lunenburg', 'Vancouver', 'Victoria', "St. John's"}

def build():
    S = statements()
    R = classify(S)
    full = {}; alias = collections.defaultdict(set)
    for i, k, d in R:
        if k == 'placed:roster':
            full.setdefault(d['name'], set()).add(d['id'])
            alias[d['alias'] or ''].add(d['id'])
    # every roster person also resolvable by "Initial Surname"
    for n, ids in list(full.items()):
        a = n.split()[0][0] + '. ' + n.split()[1]
        alias[a] |= ids
    def resolve(n):
        ids = full.get(n) or alias.get(n)
        return sorted(ids) if ids else []
    orgcity = {}
    for i, k, d in R:
        if k == 'placed:orgcity':
            c = d['city'].strip()
            orgcity.setdefault(d['org'], set()).add(c)
    emp = collections.defaultdict(set); night = set(); travel = set(); issues = []
    for i, k, d in R:
        if k in ('placed:employ', 'placed:night', 'placed:travel'):
            if not d['who']: issues.append(('nowho', S[i])); continue
            ids = resolve(d['who'])
            if len(ids) != 1: issues.append(('resolve', d, ids, S[i])); continue
            p = ids[0]
            if k == 'placed:employ': emp[p].add(d['org'])
            elif k == 'placed:night': night.add(p)
            else: travel.add(p)
    return S, R, full, alias, orgcity, emp, night, travel, issues

if __name__ == '__main__':
    S, R, full, alias, orgcity, emp, night, travel, issues = build()
    print(issues)
    print({k: v for k, v in orgcity.items() if len(v) > 1}, len(orgcity))
    print({p: o for p, o in emp.items() if len(o) > 1})
    print({n: i for n, i in full.items() if len(i) > 1}, len({i for s in full.values() for i in s}))
    print(night, travel)
    for p in sorted(night | travel):
        print(p, p in night, p in travel, [(o, orgcity.get(o)) for o in emp.get(p, [])])

    placed = [dict(index=i, passage=S[i][0], text=S[i][1], kind=k, data=d) for i, k, d in R if k.startswith('placed:')]
    matches = sorted(p for p in night & travel if any(orgcity.get(o, set()) & COASTAL for o in emp.get(p, [])))
    json.dump(dict(placed=placed, matches=matches, coastal_cities=sorted(COASTAL),
                   org_city={k: sorted(v) for k, v in orgcity.items()}), open('extracted.json', 'w', encoding='utf8'), indent=1)
    print(matches)
