import os,sys,json,re,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from facts_io import *
COAST={"Halifax","Vancouver","Victoria","St. John's","Lunenburg"}
FRUIT={"apple","banana","pear","mango","peach","orange","plum","watermelon"}
PUBLIC={"bus","train","tram","subway"}
def run(d):
    facts=load(d); full,alias=resolver(facts)
    P=collections.defaultdict(lambda: collections.defaultdict(list))
    unres=set()
    for f in facts:
        if f['relation'] in('has_id','has_name','also_called','id_hint'):continue
        if re.match(r'(Y\d|Org |P-)',f['subject']): continue
        ids=resolve(f['subject'],full,alias)
        if not ids: unres.add(f['subject']); continue
        for i in ids: P[i][f['relation']].append(f)
    city={f['subject']:f['object'] for f in facts if f['relation']=='based_in'}
    course={}
    for f in facts:
        if f['relation']=='attends_course': course.setdefault(f['subject'],[]).append(f)
    return P,city,course,facts,full,alias,unres
def ok(f,bad=('no longer','used to','formerly','in a former role','in the past','only in the past','previously')):
    return not any(q in bad for q in f['qualifiers'])
def c_coast(P,city):
    out=set()
    for p,r in P.items():
        for f in r['works_for']:
            if city.get(f['object']) in COAST and ok(f): out.add(p)
    return out
def c_public(P): return {p for p,r in P.items() if any(f['object'] in PUBLIC and ok(f) for f in r['travels_by'] if 'routinely' in f['qualifiers'])}
def c_night(P): return {p for p,r in P.items() if any(f['object']=='night' and ok(f) for f in r['works_shift'])}
def c_vol3(P):
    out=set()
    for p,r in P.items():
        ev={f['object'] for f in r['volunteered_at'] if 'this-year' in f['qualifiers']}
        if len(ev)>=3: out.add(p)
    return out
def c_dairy(P): return {p for p,r in P.items() if any(ok(f) for f in r['avoids'])}
def c_guard(P,course):
    out=set()
    for p,r in P.items():
        for f in r['legal_guardian_of']:
            if any('evening' in c['qualifiers'] and 'currently' in c['qualifiers'] for c in course.get(f['object'],[])): out.add(p)
    return out
def c_train(P): return {p for p,r in P.items() if any(f['object']=='train over plane' for f in r['prefers_over'])}
def c_fruit(P): return {p for p,r in P.items() if any(f['object'] in FRUIT and ok(f) for f in r['enjoys_eating'])}
Q={1:['coast','public','night'],2:['coast','vol3','dairy','public'],3:['vol3','guard','train','fruit','dairy']}
ans={}
for d in (1,2,3):
    P,city,course,facts,full,alias,unres=run(d)
    sets={'coast':c_coast(P,city),'public':c_public(P),'night':c_night(P),'vol3':c_vol3(P),'dairy':c_dairy(P),'guard':c_guard(P,course),'train':c_train(P),'fruit':c_fruit(P)}
    res=set.intersection(*[sets[k] for k in Q[d]])
    print(d,{k:len(sets[k]) for k in Q[d]},len(res),'unresolved names',len(unres))
    ans['doc%d'%d]=sorted(res)
json.dump(ans,open('answers.json','w'))
print(ans)
