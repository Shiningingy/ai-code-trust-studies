import json,collections,re
def load(d):
    facts=[]
    for l in open(f'work/out{d}/parsed.jsonl',encoding='utf-8'):
        r=json.loads(l)
        for f in r['facts']: f['line']=r['line']; facts.append(f)
    return facts
def resolver(facts):
    return resolver2(facts)
def resolver_old(facts):
    full={}; alias=collections.defaultdict(set)
    for f in facts:
        if f['relation']=='has_id': full[f['subject']]=f['object']
    for f in facts:
        if f['relation']=='also_called':
            alias[f['object']].add(full[f['subject']])
    return full,alias
def resolve(name,full,alias):
    if name in full: return {full[name]}
    return set(alias.get(name,()))
if __name__=='__main__':
    import sys
    for d in (1,2,3):
        facts=load(d); full,alias=resolver(facts)
        print(d,len(full),'persons; ambiguous aliases:',[a for a,s in alias.items() if len(s)>1][:10])
        names=set(f['subject'] for f in facts if f['relation'] not in('has_name','has_id','also_called') and not re.match(r'(Y\d|Org|P-)',f['subject']))
        unres=[n for n in names if not resolve(n,full,alias)]
        print(' names',len(names),'unresolved',len(unres),unres[:10])
        fullnames=[n for n in names if n in full]; print(' full-name mentions',len(fullnames))

def resolver2(facts):
    """returns (full, alias) where full: name->pid (dict) for every person name that can be resolved, alias: name->set(pid)"""
    idof=collections.defaultdict(set)
    names=set()
    for f in facts:
        if f['relation'] in ('has_id','id_hint'): idof[f['subject']].add(f['object'])
        elif f['relation']=='also_called': pass
        if not re.match(r'(Y\d|Org |P-|narrator)',f['subject']) and f['relation'] not in('has_name',): names.add(f['subject'])
    for f in facts:
        if f['relation']=='also_called':
            names.add(f['object']); idof[f['object']] |= idof.get(f['subject'],set())
    # also_called after has_id for all
    for f in facts:
        if f['relation']=='also_called': idof[f['object']] |= idof[f['subject']]; idof[f['subject']] |= set()
    groups=collections.defaultdict(set)
    for n in names:
        m=re.match(r"([A-Za-z])[\w'-]*\.? ([\w'-]+)$",n)
        if m: groups[(m.group(1).upper(),m.group(2))].add(n)
    for key,g in groups.items():
        fulls=[n for n in g if not re.match(r'[A-Z]\. ',n)]
        if len(fulls)==1:
            ids=set().union(*[idof.get(n,set()) for n in g])
            for n in g: idof[n]|=ids
    full={n:next(iter(i)) for n,i in idof.items() if len(i)==1}
    conflict=[n for n,i in idof.items() if len(i)>1]
    if conflict: print('CONFLICT',conflict[:5])
    return full,{}
