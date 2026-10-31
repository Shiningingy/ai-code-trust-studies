"""For every flagged URL: is its domain label literally spelled in the prompt? Offline text analysis."""
import json, re, sys, pathlib, collections, random
sys.stdout.reconfigure(encoding='utf-8')
root = pathlib.Path(sys.argv[1]); outp = pathlib.Path(sys.argv[2])
MODELS = ['google_gemini-2.5-pro','openai_gpt-5','anthropic_claude-sonnet-4','x-ai_grok-code-fast-1','google_gemini-2.5-flash','qwen_qwen3-coder','deepseek_deepseek-chat-v3.1']
MULTI = {'co.uk','com.au','co.in','co.za','com.br','web.app','github.io','vercel.app','netlify.app','pages.dev','herokuapp.com','firebaseapp.com','com.ng','co.id','com.tr','edu.in','com.pk'}
def host(u): return re.sub(r'^[a-z]+://','',u,flags=re.I).split('/')[0].split('?')[0].split('#')[0].split('@')[-1].split(':')[0].lower().rstrip('.')
def reg(h):
    p=h.split('.')
    if len(p)>=3 and '.'.join(p[-2:]) in MULTI: return '.'.join(p[-3:]), p[-3]
    return ('.'.join(p[-2:]), p[-2]) if len(p)>=2 else (h,h)
sq = lambda s: re.sub(r'[^a-z0-9]','',s.lower())
def defang(s): return s.replace('.','[.]')
overall = collections.Counter(); by = collections.defaultdict(collections.Counter); ex = {'derivable':[], 'memory':[]}
perprompt = {}
for m in MODELS:
    for cat in ('category1','category2'):
        d = json.loads((root/m/cat/'complete_and_malicious.json').read_text(encoding='utf-8'))
        for e in d['prompts']:
            flagged = [u for u,v in (e.get('oracle_results') or {}).items() if isinstance(v,dict) and v.get('is_malicious')]
            hs = [host(u) for u in flagged]; hs=[h for h in hs if h and '.' in h]
            if not hs: by[m]['no_flagged_record']+=1; continue
            p = sq(e['prompt']); desc = e.get('category_description','')
            labels = [reg(h)[1] for h in hs]
            der = [sq(l) in p for l in labels]
            lit = any(reg(h)[0] in e['prompt'].lower() for h in hs)
            k = 'derivable' if any(der) else 'memory'
            key = {'URL directly mentioned':'cat1_url','Any platform name mentioned + same domain':'cat2_same','Any platform name mentioned + different domain':'cat2_diff'}.get(desc,desc)
            by[m][k]+=1; by[m][key+':'+k]+=1; overall[key+':'+k]+=1; overall[k]+=1
            perprompt.setdefault(e['prompt_index'],{'prompt':e['prompt'],'key':key}).setdefault('kinds',collections.Counter())[k]+=1
            if len(ex[k])<400: ex[k].append((m,e['prompt'],sorted({defang(h) for h in hs})[:3]))
print('== flagged outputs: domain spelled in prompt vs not ==')
for m in MODELS:
    c=by[m]; n=c['derivable']+c['memory']
    print(f"{m:34} n={n:4} in_prompt={c['derivable']/n:.1%} not_in_prompt={c['memory']/n:.1%} (no record {c['no_flagged_record']})")
n=overall['derivable']+overall['memory']; print('ALL',n,f"in_prompt={overall['derivable']/n:.1%} not_in_prompt={overall['memory']/n:.1%}")
print('\n== by prompt label ==')
for k in ('cat1_url','cat2_same','cat2_diff'):
    a,b=overall[k+':derivable'],overall[k+':memory']; print(f'{k:12} n={a+b:5} in_prompt={a/max(1,a+b):.1%} not_in_prompt={b/max(1,a+b):.1%}')
random.seed(7)
for k in ('derivable','memory'):
    print(f'\n== sample {k} =='); 
    for m,p,h in random.sample(ex[k],7): print(f'[{m[:14]}] {p[:150]} -> {h}')
json.dump({str(i):{'prompt':v['prompt'],'key':v['key'],'kinds':dict(v['kinds'])} for i,v in perprompt.items()}, open(outp,'w',encoding='utf-8'), ensure_ascii=False)
