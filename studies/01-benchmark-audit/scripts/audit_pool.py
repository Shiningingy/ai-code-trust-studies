"""Full-audit reports for 2024 models: is each flagged domain spelled in the prompt? Then registry dates for a
random sample of GPT-4o's flagged domains. Text analysis plus registry lookups only; scam sites are never contacted."""
import json, re, sys, glob, random, time, collections, urllib.request, urllib.error, urllib.parse, concurrent.futures as cf
sys.stdout.reconfigure(encoding='utf-8')
base = 'G:/Scam2Prompt-Study/'
MULTI = {'co.uk', 'com.au', 'co.in', 'co.za', 'com.br', 'web.app', 'github.io', 'vercel.app', 'netlify.app', 'pages.dev', 'herokuapp.com', 'firebaseapp.com', 'com.ng', 'co.id', 'com.tr', 'edu.in', 'com.pk'}
SHARED = {'web.app', 'github.io', 'vercel.app', 'netlify.app', 'pages.dev', 'herokuapp.com', 'firebaseapp.com'}
sq = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
def host(u): return re.sub(r'^[a-z]+://', '', u, flags=re.I).split('/')[0].split('?')[0].split('#')[0].split('@')[-1].split(':')[0].lower().rstrip('.')
def reg(h):
    p = h.split('.')
    if len(p) >= 3 and '.'.join(p[-2:]) in MULTI: return '.'.join(p[-3:]), p[-3]
    return ('.'.join(p[-2:]), p[-2]) if len(p) >= 2 else (h, h)
def load(f):
    t = open(f, encoding='utf-8').read()
    t, n = re.subn(r'("prompt": )(?!")(.+?)(,?)$', lambda m: m[1] + json.dumps(m[2]) + m[3], t, flags=re.M)
    if n: print('  repaired unquoted prompts:', n)
    return json.loads(t)
gpt = None
for f in sorted(glob.glob(base + 'data/artifact/analysis_report_*.json')):
    d = load(f); M = d['detailed_reports']['all_malicious_urls']
    c = collections.Counter(); ex = []
    for e in M:
        h = host(e['malicious_url'])
        if '.' not in h: continue
        _, lab = reg(h); p = sq(e['prompt'])
        same_seed = reg(h)[0] == reg(host(e.get('original_url') or ''))[0]
        k = 'in_prompt' if sq(lab) in p else 'not_in_prompt'
        c[k] += 1; c['seed_same' if same_seed else 'seed_diff'] += 1
        if k == 'not_in_prompt': c['notprompt_seed_same' if same_seed else 'notprompt_seed_diff'] += 1; ex.append((h, e['prompt'][:100]))
    n = c['in_prompt'] + c['not_in_prompt']; name = f.split('analysis_report_')[-1][:60]
    print(f"{name}\n  flagged URLs {n}: in prompt {c['in_prompt']/n:.1%}, not in prompt {c['not_in_prompt']/n:.1%} (of those, seed domain {c['notprompt_seed_same']}, other {c['notprompt_seed_diff']})")
    random.seed(2)
    for h, p in random.sample(ex, min(4, len(ex))): print('    ', h.replace('.', '[.]'), '<-', p)
    if 'azure_gpt-4o_to_azure_gpt-4o_' in f: gpt = M
print(json.dumps({}), flush=True)
doms = sorted({reg(host(e['malicious_url']))[0] for e in gpt if '.' in host(e['malicious_url']) and '.'.join(host(e['malicious_url']).split('.')[-2:]) not in SHARED})
print('GPT-4o unique flagged domains', len(doms), flush=True)
random.seed(20261031); sample = random.sample(doms, min(400, len(doms)))
def url(d):
    t = d.rsplit('.', 1)[-1]
    return f'https://rdap.verisign.com/{t}/v1/domain/{d}' if t in ('com', 'net') else f'https://rdap.org/domain/{d}'
def look(d):
    for i in range(3):
        try:
            r = urllib.request.Request(url(d), headers={'User-Agent': 'research-rdap/1.0', 'Accept': 'application/rdap+json'})
            j = json.load(urllib.request.urlopen(r, timeout=20))
            return d, {x.get('eventAction'): x.get('eventDate') for x in j.get('events', [])}.get('registration'), 'ok'
        except urllib.error.HTTPError as e:
            if e.code == 404: return d, None, 'gone'
            time.sleep(2 + 3 * i)
        except Exception:
            time.sleep(2 + 3 * i)
    return d, None, 'error'
out = {}
with cf.ThreadPoolExecutor(5) as ex:
    for d, c, s in ex.map(look, sample): out[d] = dict(created=c, status=s)
print('rdap', collections.Counter(v['status'] for v in out.values()), flush=True)
win = [d for d, v in out.items() if v['created'] and '2023-11' <= v['created'][:7] <= '2025-06']
print('candidates: registered after Oct 2023 cutoff, by June 2025 run:', len(win), flush=True)
win = random.sample(win, min(45, len(win)))
for d in win:
    q = urllib.parse.urlencode({'url': d, 'matchType': 'domain', 'limit': 1, 'fl': 'timestamp', 'output': 'json', 'from': '1996'})
    for a in range(2):
        try:
            x = json.load(urllib.request.urlopen(urllib.request.Request('https://web.archive.org/cdx/search/cdx?' + q, headers={'User-Agent': 'research-cdx/1.0'}), timeout=40))
            out[d]['first_capture'] = x[1][0] if len(x) > 1 else None; break
        except Exception:
            out[d]['first_capture'] = 'error'; time.sleep(5)
    time.sleep(1.5)
json.dump(out, open(base + 'results/gpt4o_domain_ages.json', 'w', encoding='utf-8'))
print('done', flush=True)
