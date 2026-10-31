import json, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
J = json.load(open('G:/Scam2Prompt-Study/results/gpt4o_domain_ages.json', encoding='utf-8'))
print('sampled', len(J), collections.Counter(v['status'] for v in J.values()))
dated = {d: v for d, v in J.items() if v.get('created')}
print('dated', len(dated), 'by Oct 2023 or earlier:', sum(v['created'][:7] <= '2023-10' for v in dated.values()),
      '| after run (certain re-registration):', sum(v['created'][:7] > '2025-07' for v in dated.values()))
chk = [v for v in dated.values() if 'first_capture' in v]
ok = [v for v in chk if v['first_capture'] != 'error']
clean = [v for v in ok if v['first_capture'] is None or v['first_capture'][:4] + '-' + v['first_capture'][4:6] >= v['created'][:7]]
print('archive-checked', len(chk), 'errors', len(chk) - len(ok), 'no older history (clean new):', len(clean), 'older history:', len(ok) - len(clean))
cand = sum('2023-11' <= v['created'][:7] <= '2025-06' for v in dated.values())
old = sum(v['created'][:7] <= '2023-10' for v in dated.values())
rate = len(clean) / max(1, len(ok))
print(f'candidates {cand}; estimated clean new {cand*rate:.0f}; share of datable within window ~ {cand*rate/max(1,cand*rate+old+cand*(1-rate)):.1%}')
print('clean new years', collections.Counter(v['created'][:4] for v in clean))
