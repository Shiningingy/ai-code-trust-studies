"""Earliest Internet Archive capture per domain, to catch re-registered domains. Queries archive.org only."""
import json, time, urllib.request, urllib.parse, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
base = 'G:/Scam2Prompt-Study/'; f = base + 'results/rdap_flagged.json'
J = json.load(open(f, encoding='utf-8')); R = J['domains']
def rdap(d):
    t = d.rsplit('.', 1)[-1]
    u = f'https://rdap.verisign.com/{t}/v1/domain/{d}' if t in ('com', 'net') else f'https://rdap.org/domain/{d}'
    r = urllib.request.Request(u, headers={'User-Agent': 'research-rdap/1.0', 'Accept': 'application/rdap+json'})
    j = json.load(urllib.request.urlopen(r, timeout=25))
    return {x.get('eventAction'): x.get('eventDate') for x in j.get('events', [])}.get('registration')
fixed = 0
for d, v in R.items():
    if v['status'] == 'error':
        try:
            c = rdap(d); v.update(created=c, status='ok'); fixed += 1
        except Exception as e:
            if '404' in str(e): v.update(status='not_registered_now')
        time.sleep(1.2)
print('retried errors fixed', fixed, flush=True)
win = [d for d, v in R.items() if v.get('created') and '2024-01' <= v['created'][:7] <= '2025-09']
print('domains to check', len(win), flush=True)
def first(d):
    q = urllib.parse.urlencode({'url': d, 'matchType': 'domain', 'limit': 1, 'fl': 'timestamp', 'output': 'json', 'from': '1996'})
    r = urllib.request.Request('https://web.archive.org/cdx/search/cdx?' + q, headers={'User-Agent': 'research-cdx/1.0'})
    x = json.load(urllib.request.urlopen(r, timeout=45))
    return x[1][0] if len(x) > 1 else None
for i, d in enumerate(win):
    for a in range(3):
        try:
            R[d]['first_capture'] = first(d); break
        except Exception as e:
            R[d]['first_capture'] = 'error'; time.sleep(4 + 4 * a)
    time.sleep(1.5)
json.dump(J, open(f, 'w', encoding='utf-8'))
print('done', sum(1 for d in win if R[d].get('first_capture') == 'error'), 'errors of', len(win))
