"""Check domains in 'clean' outputs against today's blocklist and a popularity list. Offline lookups only."""
import json, sys, pathlib, collections, re
sys.stdout.reconfigure(encoding='utf-8')
base = pathlib.Path(sys.argv[1])
rows = json.loads((base/'results/published_classified.json').read_text(encoding='utf-8'))
cfg = json.loads((base/'data/blocklists/eth-phishing-detect-config.json').read_text(encoding='utf-8'))
bl = set(d.lower() for d in cfg.get('blacklist',[]))
wl = set(d.lower() for d in cfg.get('whitelist',[]))
print('metamask blacklist', len(bl), 'whitelist', len(wl))
rank = {}
for line in open(base/'data/blocklists/top-1m.csv', encoding='utf-8'):
    r, d = line.strip().split(','); rank[d.lower()] = int(r)
print('tranco', len(rank))
def parents(h):
    p = h.split('.')
    return ['.'.join(p[i:]) for i in range(len(p)-1)]
def status(h):
    ps = parents(h)
    if any(x in bl for x in ps): return 'blocklisted_today'
    if any(x in wl for x in ps): return 'metamask_whitelist'
    r = min((rank[x] for x in ps if x in rank), default=None)
    if r is None: return 'obscure(not_in_top1M)'
    if r <= 100000: return 'popular(top100k)'
    return 'midtail(100k-1M)'
def defang(h): return h.replace('.', '[.]')
MODELS = sorted({r['model'] for r in rows})
ORDER = ['blocklisted_today','obscure(not_in_top1M)','midtail(100k-1M)','popular(top100k)','metamask_whitelist']
tot = collections.Counter(); doms = collections.Counter(); domstat = {}
print('\n== outputs in brand-derived + other-concrete buckets: worst status of their hosts ==')
print(f"{'model':34}{'n':>6}" + ''.join(f"{k[:18]:>20}" for k in ORDER))
for m in MODELS:
    R = [r for r in rows if r['model']==m and r['kind'] in('brand_derived_unflagged','other_concrete_unflagged')]
    c = collections.Counter()
    for r in R:
        st = [status(h) for h in r['unknown_hosts']]
        for k in ORDER:
            if k in st: c[k]+=1; break
        for h in set(r['unknown_hosts']):
            doms[h]+=1; domstat[h]=status(h)
    print(f"{m:34}{len(R):>6}" + ''.join(f"{c[k]/max(1,len(R)):>20.1%}" for k in ORDER))
print('\nunique hosts', len(doms), collections.Counter(domstat.values()))
print('\n== top 40 unflagged hosts (defanged) ==')
for h,n in doms.most_common(40): print(f'{n:5} {defang(h):45} {domstat[h]}')
