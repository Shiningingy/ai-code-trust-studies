"""Fingerprints of memory in flagged URLs: details the prompt does not supply. Offline text analysis."""
import json, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
repo = 'G:/Scam2Prompt-Study/data/innoc2scam/repo/'
MODELS = ['google_gemini-2.5-pro','openai_gpt-5','anthropic_claude-sonnet-4','x-ai_grok-code-fast-1','google_gemini-2.5-flash','qwen_qwen3-coder','deepseek_deepseek-chat-v3.1']
COMMON_TLD = {'com','io','net','org','ai','co','app','dev'}
GENERIC = re.compile(r'^/?(api|v\d+|rest|public|private|graphql|ws|socket|auth|login|token|account|accounts|balance|balances|user|users|market|markets|price|prices|trade|trades|order|orders|ticker|data|status|health|wallet|wallets|transactions?|deposit|withdraw|plans?|invest\w*|signals?|mine|mining|portfolio)?(/|$)', re.I)
def parts(u):
    s = re.sub(r'^[a-z]+://', '', u, flags=re.I); h = s.split('/')[0].split(':')[0].lower().rstrip('.')
    p = '/' + s.split('/', 1)[1].split('?')[0] if '/' in s else '/'
    return h, p
sq = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
tld = collections.Counter(); rare = []; byhost = collections.defaultdict(lambda: collections.defaultdict(set)); tot = 0
ct = collections.Counter()
for m in MODELS:
    for cat in ('category1','category2'):
        for e in json.load(open(repo + f'{m}/{cat}/complete_and_malicious.json', encoding='utf-8'))['prompts']:
            pr = e['prompt'].lower()
            for u, v in (e.get('oracle_results') or {}).items():
                if not (isinstance(v, dict) and v.get('is_malicious')): continue
                h, p = parts(u)
                if '.' not in h or re.search(r'[{<$]', h): continue
                tot += 1; t = h.rsplit('.', 1)[-1]; tld[t] += 1
                in_prompt = ('.' + t) in pr
                ct['tld_in_prompt' if in_prompt else 'tld_not_in_prompt'] += 1
                if not in_prompt:
                    ct['com_not_in_prompt' if t == 'com' else ('common_noncom_not_in_prompt' if t in COMMON_TLD else 'rare_tld_not_in_prompt')] += 1
                    if t not in COMMON_TLD: rare.append((m[:12], cat[-1], h.replace('.', '[.]'), e['prompt'][:90]))
                deep = [x for x in p.split('/') if x]
                specific = len(deep) >= 3 or any(len(x) > 14 or re.search(r'\d{3,}', x) for x in deep)
                if cat == 'category2': byhost[(e['prompt'], h)][p.rstrip('/')].add(m)
                ct['path_specific' if specific else 'path_generic'] += 1
print('flagged URL rows', tot); print(dict(ct)); print('top TLDs', tld.most_common(10))
print('\nrare TLD not spelled in prompt (sample):')
for r in rare[:10]: print(' ', r)
same = diff = 0; multi = 0
for k, paths in byhost.items():
    ms = set().union(*paths.values())
    if len(ms) >= 3:
        multi += 1
        best = max(len(v) for pth, v in paths.items() if pth)if any(pth for pth in paths) else 0
        same += best >= 3
print(f'\nCat 2 prompt+host pairs with 3+ models: {multi}; same non-empty path shared by 3+ models: {same}')
