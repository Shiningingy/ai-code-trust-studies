"""Registration dates for flagged domains, from public registries (RDAP). Never contacts the domains themselves."""
import json, re, sys, time, urllib.request, urllib.error, concurrent.futures as cf, collections
sys.stdout.reconfigure(encoding='utf-8')
base = 'G:/Scam2Prompt-Study/'; repo = base + 'data/innoc2scam/repo/'
MODELS = ['google_gemini-2.5-pro','openai_gpt-5','anthropic_claude-sonnet-4','x-ai_grok-code-fast-1','google_gemini-2.5-flash','qwen_qwen3-coder','deepseek_deepseek-chat-v3.1']
MULTI = {'co.uk','com.au','co.in','co.za','com.br','web.app','github.io','vercel.app','netlify.app','pages.dev','herokuapp.com','firebaseapp.com','com.ng','co.id','com.tr','edu.in','com.pk'}
SHARED = {'web.app','github.io','vercel.app','netlify.app','pages.dev','herokuapp.com','firebaseapp.com'}
def host(u): return re.sub(r'^[a-z]+://','',u,flags=re.I).split('/')[0].split('?')[0].split('#')[0].split('@')[-1].split(':')[0].lower().rstrip('.')
def reg(h):
    p = h.split('.')
    if len(p) >= 3 and '.'.join(p[-2:]) in MULTI: return '.'.join(p[-3:])
    return '.'.join(p[-2:]) if len(p) >= 2 else h
doms = collections.Counter()
for m in MODELS:
    for cat in ('category1','category2'):
        for e in json.load(open(repo + f'{m}/{cat}/complete_and_malicious.json', encoding='utf-8'))['prompts']:
            for u, v in (e.get('oracle_results') or {}).items():
                if isinstance(v, dict) and v.get('is_malicious'):
                    h = host(u)
                    if '.' in h and not re.search(r'[{<$]', h) and '.'.join(h.split('.')[-2:]) not in SHARED: doms[reg(h)] += 1
print('unique registrable domains', len(doms)); sys.stdout.flush()
def url(d):
    t = d.rsplit('.', 1)[-1]
    if t in ('com', 'net'): return f'https://rdap.verisign.com/{t}/v1/domain/{d}'
    return f'https://rdap.org/domain/{d}'
def look(d):
    for i in range(3):
        try:
            r = urllib.request.Request(url(d), headers={'User-Agent': 'research-rdap/1.0', 'Accept': 'application/rdap+json'})
            j = json.load(urllib.request.urlopen(r, timeout=20))
            ev = {x.get('eventAction'): x.get('eventDate') for x in j.get('events', [])}
            return d, {'created': ev.get('registration'), 'status': 'ok'}
        except urllib.error.HTTPError as e:
            if e.code == 404: return d, {'created': None, 'status': 'not_registered_now'}
            time.sleep(2 + i * 3)
        except Exception:
            time.sleep(2 + i * 3)
    return d, {'created': None, 'status': 'error'}
res = {}
with cf.ThreadPoolExecutor(6) as ex:
    for k, (d, r) in enumerate(ex.map(look, sorted(doms))):
        res[d] = r
        if k % 200 == 0: print(k, flush=True)
json.dump({'domains': res, 'counts': doms}, open(base + 'results/rdap_flagged.json', 'w', encoding='utf-8'))
print('finished', collections.Counter(r['status'] for r in res.values()))
