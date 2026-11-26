# Usage: python -m gram parse train/docN.md --lib lib --manual train/docN.manual.jsonl --out out/docN ; python lib/example_queries.py
import json,sys,collections
S='out/doc'
COASTAL={'Halifax','Victoria','Vancouver',"St. John's",'Lunenburg'}
FRUIT={'watermelon','banana','pear','apple','mango','plum','peach','orange','grape','cherry','strawberry','kiwi','lemon','apricot','melon','pineapple','blueberry','papaya','fig'}
PUBLIC={'bus','train','tram','subway'}
def load(d):
    F=[]
    for l in open('out/doc%d/parsed.jsonl'%d,encoding='utf8'):
        r=json.loads(l)
        for f in r.get('facts',[]) or []: F.append(f)
    return F
def run(d):
    F=load(d)
    ids={}; 
    for f in F:
        if f['relation']=='has_id': ids[f['subject']]=f['object']
    objs=collections.Counter(f['object'] for f in F if f['relation']=='enjoys_eating')
    print(d,'enjoys',dict(objs))
    base={}
    for f in F:
        if f['relation']=='based_in': base[f['subject']]=f['object']
    print(d,'cities',collections.Counter(base.values()))
    return F,ids,base
def who(F,rel,cond):
    return {f['subject'] for f in F if f['relation']==rel and cond(f)}
def past(f): return any(q in ('past','no longer','former role','future','once') for q in f['qualifiers'])
res={}
for d in (1,2,3):
    F,ids,base=run(d)
    c={}
    c['works_coastal']={f['subject'] for f in F if f['relation']=='works_for' and base.get(f['object']) in COASTAL}
    c['public']=who(F,'travels_by',lambda f:f['object'] in PUBLIC and not past(f))
    c['night']=who(F,'works_shift',lambda f:f['object']=='night' and not past(f))
    ev=collections.defaultdict(set)
    for f in F:
        if f['relation']=='volunteered_at' and 'this-year' in f['qualifiers']: ev[f['subject']].add(f['object'])
    c['vol3']={p for p,e in ev.items() if len(e)>=3}
    c['nodairy']=who(F,'avoids',lambda f:'currently' in f['qualifiers'] and f['object']=='dairy products')
    ys={f['subject'] for f in F if f['relation']=='attends_course' and 'currently' in f['qualifiers'] and f['object'].startswith('evening') and 'during the evening' in f['qualifiers']}
    c['guardian_evening']={f['subject'] for f in F if f['relation']=='guardian_of' and f['object'] in ys and 'not' not in f['qualifiers']}
    c['train_pref']=who(F,'prefers',lambda f:f['object']=='train' and 'genuinely' in f['qualifiers'])
    c['fruit']=who(F,'enjoys_eating',lambda f:f['object'] in FRUIT and not past(f))
    qs={1:['works_coastal','public','night'],2:['works_coastal','vol3','nodairy','public'],3:['vol3','guardian_evening','train_pref','fruit','nodairy']}[d]
    sets=[c[k] for k in qs]
    inter=set.intersection(*sets)
    print(d,{k:len(c[k]) for k in qs}, len(inter))
    notid=[p for p in inter if p not in ids]
    print(' no id:',notid)
    res['doc%d'%d]=sorted(ids.get(p,p) for p in inter)
    print(res['doc%d'%d])
json.dump(res,open('answers.json','w'))
