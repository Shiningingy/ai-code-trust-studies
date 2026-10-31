import json, sys, re, os
sys.stdout.reconfigure(encoding='utf-8')
for f in ('req_ours', 'req_default'):
    p = f'G:/Scam2Prompt-Study/results/{f}.json'
    print('=====', f, 'exists', os.path.exists(p))
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding='utf-8'))
    print('top keys', sorted(d.keys()), '| tools', len(d.get('tools') or []), '| thinking', d.get('thinking'), '| temperature', d.get('temperature'))
    sysblocks = d.get('system') or []
    sys_t = sysblocks if isinstance(sysblocks, str) else '\n'.join(b.get('text', '') for b in sysblocks)
    msgs = []
    for m in d['messages']:
        c = m['content']
        msgs.append(c if isinstance(c, str) else '\n'.join(x.get('text', '') for x in c if isinstance(x, dict)))
    msg_t = '\n---\n'.join(msgs)
    print('system chars', len(sys_t), '| messages chars', len(msg_t))
    if f == 'req_ours':
        print('--- SYSTEM ---\n' + sys_t[:1500]); print('--- MESSAGES ---\n' + msg_t[:2500])
    for name, t in (('system', sys_t), ('messages', msg_t)):
        for x in re.finditer(r'[^\n.]*\b(URLs?|verify|verif\w+|guess|hallucinat\w*|fabricat\w*|invent\w*)\b[^\n.]*', t, re.I):
            print(f'  [{name}]', x.group(0).strip()[:220])
