"""Sample Cat 2 prompts, find the platform name in each, and build a version with an invented name."""
import json, re, sys, random, pathlib, collections
sys.stdout.reconfigure(encoding='utf-8')
base = pathlib.Path(sys.argv[1]); N = int(sys.argv[2])
rows = json.loads((base/'results/published_classified.json').read_text(encoding='utf-8'))
repo = base/'data/innoc2scam/repo'
MODELS = sorted({r['model'] for r in rows})
sq = lambda s: re.sub(r'[^a-z0-9]','',s.lower())
def host(u): return re.sub(r'^[a-z]+://','',u,flags=re.I).split('/')[0].split('@')[-1].split(':')[0].lower().rstrip('.')
def lab(h):
    p=h.split('.'); return p[-2] if len(p)>=2 else h
votes = collections.defaultdict(collections.Counter); flagged=set()
for m in MODELS:
    for cat in ('category1','category2'):
        d=json.loads((repo/m/cat/'complete_and_malicious.json').read_text(encoding='utf-8'))
        for e in d['prompts']:
            for u,v in (e.get('oracle_results') or {}).items():
                if isinstance(v,dict) and v.get('is_malicious'):
                    h=host(u); p=h.split('.')
                    if len(p)>=2:
                        flagged.add('.'.join(p[-2:]))
                        if cat=='category2': votes[e['prompt']][lab(h)]+=3
for r in rows:
    if r['cat']=='2':
        for h in r['unknown_hosts']: votes[r['prompt']][lab(h)]+=1
(base/'results/known_flagged_domains.json').write_text(json.dumps(sorted(flagged)),encoding='utf-8')
bench=json.loads((repo/'Innoc2Scam-bench.json').read_text(encoding='utf-8'))['prompts']
cat2=[p for p in bench if p['category']==2]
def locate(prompt,label):
    s=sq(label)
    if len(s)<4: return None
    pat=r'[\s\-_.\']*'.join(map(re.escape,s))
    m=re.search(pat,prompt,re.I)
    return m
elig=[]
for p in cat2:
    t=p['prompt']
    for l,_ in votes[t].most_common():
        if sq(l) in sq(t) and locate(t,l):
            elig.append((p,l)); break
print('cat2',len(cat2),'eligible',len(elig),collections.Counter(p['category_description'][-14:] for p,_ in elig))
rng=random.Random(20261031)
sample=rng.sample(elig,N)
# invented names: not in the popularity list, blocklist, or any label seen in the published outputs
tr={l.split(',')[1].strip().split('.')[0] for l in open(base/'data/blocklists/top-1m.csv',encoding='utf-8')}
bl={d.split('.')[0] for d in json.loads((base/'data/blocklists/eth-phishing-detect-config.json').read_text(encoding='utf-8'))['blacklist']}
seen={sq(l) for c in votes.values() for l in c}
ON=['br','d','f','g','k','l','m','n','p','qu','r','s','t','v','z','th','tr','pl']; V=['a','e','i','o','u','ae','io','ua']; CO=['l','n','r','s','v','th','x','rn','nd','lv']
def name():
    while True:
        w=''.join(rng.choice(ON)+rng.choice(V) for _ in range(2))+rng.choice(CO)+rng.choice(V)+rng.choice(['n','r','x','th','l'])
        if w not in tr and w not in bl and w not in seen and 8<=len(w)<=12: return w
out=[]; used=set()
for i,(p,l) in enumerate(sample):
    t=p['prompt'].strip().strip('"'); m=locate(t,l)
    while True:
        n=name()
        if n not in used: used.add(n); break
    brand=m.group(0)
    surf=n.capitalize()
    pat=r'[\s\-_.\']*'.join(map(re.escape,sq(l)))
    swapped=re.sub(pat,surf,t,flags=re.I)
    out.append(dict(id=i,prompt=t,swapped=swapped,brand=brand,label=sq(l),invented=n,desc=p['category_description']))
    assert sq(l) not in sq(swapped)
(base/'results/prompts_sample.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
print(collections.Counter(o['desc'][-14:] for o in out))
for o in out[:14]:
    print(f"\n[{o['brand']}]\n  A: {o['prompt'][:140]}\n  B: {o['swapped'][:140]}")
