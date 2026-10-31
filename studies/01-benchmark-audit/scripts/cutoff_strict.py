"""Strict domain-age test. A domain counts as new only if registered after the cutoff and by Sept 2025,
with no archive capture before registration. Uses saved registry and archive records only."""
import json, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
base = 'G:/Scam2Prompt-Study/'; repo = base + 'data/innoc2scam/repo/'
R = json.load(open(base + 'results/rdap_flagged.json', encoding='utf-8'))['domains']
MODELS = ['google_gemini-2.5-pro', 'openai_gpt-5', 'anthropic_claude-sonnet-4', 'x-ai_grok-code-fast-1', 'google_gemini-2.5-flash', 'qwen_qwen3-coder', 'deepseek_deepseek-chat-v3.1']
CUT = {'google_gemini-2.5-pro': '2025-01', 'google_gemini-2.5-flash': '2025-01', 'anthropic_claude-sonnet-4': '2025-03'}
OLD = {'GPT-4o, Oct 2023': '2023-10', 'DeepSeek-V3, Jul 2024': '2024-07', 'Llama-4-Scout, Aug 2024': '2024-08'}
MULTI = {'co.uk', 'com.au', 'co.in', 'co.za', 'com.br', 'web.app', 'github.io', 'vercel.app', 'netlify.app', 'pages.dev', 'herokuapp.com', 'firebaseapp.com', 'com.ng', 'co.id', 'com.tr', 'edu.in', 'com.pk'}
def host(u): return re.sub(r'^[a-z]+://', '', u, flags=re.I).split('/')[0].split('?')[0].split('#')[0].split('@')[-1].split(':')[0].lower().rstrip('.')
def reg(h):
    p = h.split('.')
    if len(p) >= 3 and '.'.join(p[-2:]) in MULTI: return '.'.join(p[-3:])
    return '.'.join(p[-2:]) if len(p) >= 2 else h
def state(d, c):
    """old = existed by cutoff; new = clean post-cutoff; bad = cannot be used."""
    v = R.get(d) or {}
    cr = (v.get('created') or '')[:7]
    if not cr: return 'unknown'
    if cr <= c: return 'old'
    if cr > '2025-09': return 'rereg'
    fc = v.get('first_capture', 'missing')
    if fc in ('error', 'missing'): return 'unknown'
    if fc is None: return 'new'
    return 'new' if fc[:4] + '-' + fc[4:6] >= cr else 'rereg'
print('status', collections.Counter(v['status'] for v in R.values()))
win = [v for v in R.values() if 'first_capture' in v]
print('archive-checked', len(win), '| errors', sum(v['first_capture'] == 'error' for v in win), '| never captured', sum(v['first_capture'] is None for v in win))
print('pre-registration capture (older history):', sum(isinstance(v['first_capture'], str) and v['first_capture'] != 'error' and v['first_capture'][:4] + '-' + v['first_capture'][4:6] < v['created'][:7] for v in win))
print('after Sept 2025 (certain re-registration):', sum((v.get('created') or '')[:7] > '2025-09' for v in R.values()))
outs = []; pd = collections.defaultdict(set)
for m in MODELS:
    for cat in ('category1', 'category2'):
        for b in ('complete_and_malicious', 'complete_but_not_malicious', 'content_filtered', 'others'):
            for e in json.load(open(repo + f'{m}/{cat}/{b}.json', encoding='utf-8'))['prompts']:
                ds = sorted({reg(host(u)) for u, v in (e.get('oracle_results') or {}).items() if isinstance(v, dict) and v.get('is_malicious')}) if b == 'complete_and_malicious' else []
                ds = [d for d in ds if d in R]
                outs.append((m, cat, b, e['prompt'], ds)); pd[e['prompt']].update(ds)
print('\n== strict: flagged outputs whose flagged domains are ALL too new for the model ==')
for m, c in CUT.items():
    F = [o for o in outs if o[0] == m and o[2] == 'complete_and_malicious' and o[4]]
    st = [[state(d, c) for d in o[4]] for o in F]
    known = [s for s in st if all(x in ('old', 'new') for x in s)]
    new = [s for s in known if all(x == 'new' for x in s)]
    print(f'{m:30} cutoff {c}: {len(new)}/{len(known)} = {len(new)/max(1,len(known)):.1%} of datable ({len(F)} flagged in total)')
print('\n== strict: flagged rate by domain age (Cat 2) ==')
for m, c in CUT.items():
    g = collections.defaultdict(lambda: [0, 0])
    for o in outs:
        if o[0] != m or o[1] != 'category2' or not pd[o[3]]: continue
        s = {state(d, c) for d in pd[o[3]]}
        if s == {'old'}: k = 'domain old enough'
        elif s == {'new'}: k = 'domain too new'
        else: continue
        g[k][1] += 1; g[k][0] += o[2] == 'complete_and_malicious'
    print(f'{m:30}', {k: f'{a}/{n} = {a/n:.1%}' for k, (a, n) in sorted(g.items())})
print('\n== strict: benchmark prompts whose flagged domains are all too new for a 2024 model ==')
for k, c in OLD.items():
    P = [p for p, ds in pd.items() if ds and all(state(d, c) in ('old', 'new') for d in ds)]
    n = sum(all(state(d, c) == 'new' for d in pd[p]) for p in P)
    print(f'  {k}: {n}/{len(P)} = {n/max(1,len(P)):.1%}')
json.dump({d: {k: v.get(k) for k in ('created', 'status', 'first_capture')} for d, v in R.items()}, open(base + 'results/domain_ages.json', 'w', encoding='utf-8'))
