import re, json
from check_coverage import split_statements
FIRST = "Amina Ben Carla Dev Elena Farah Gabriel Hana Isaac Jia Kofi Leah Mateo Nadia Omar Priya Quinn Rosa Samir Talia".split()
text = open('context.md', encoding='utf8').read()
stm = split_statements(text)
# roster: full name -> id ; (initial, surname) -> id
ids = {}
for m in re.finditer(r'roster records (\w+) (\w+) under identifier P-(\d+)', text, re.I):
    ids[(m.group(1)[0].lower(), m.group(2).lower())] = m.group(3)
for m in re.finditer(r'(\w)\w*\.?\s+(\w+) volunteer(?:ed)? at event-P-(\d+)-\d+ during this-year', text, re.I):
    k = (m.group(1).lower(), m.group(2).lower())
    if k[1] in ('she','he','they'): continue
    if k in ids and ids[k] != m.group(3): print('CONFLICT', k, ids[k], m.group(3))
    ids.setdefault(k, m.group(3))
SUR = sorted({k[1] for k in ids}, key=len, reverse=True)
NAME = r'(?:(?:%s)\s+|[A-Za-z]\.\s+)(?:%s)' % ('|'.join(FIRST), '|'.join(s.capitalize() for s in SUR))
NAME_RE = r"(%s|(?<![A-Za-z])I(?![A-Za-z.]))(?: (?:said|says|noted|mentioned) (?:she|he|they))?" % NAME
def pid(n):
    n = n.strip()
    a, b = re.match(r'(\w)\w*\.?\s+(\w+)', n).groups()
    return ids.get((a.lower(), b.lower()), 'UNK:' + a.lower() + b.lower())
FACTS = [
 ('org', r'%s (?:currently )?works? for (?:Organization|Org) (\d+)' % NAME_RE),
 ('dairy', r'%s currently chooses? to avoid dairy products' % NAME_RE),
 ('transit', r'%s routinely travels? by (bus|train|subway|tram)(?! but no longer)' % NAME_RE),
 ('event', r'%s volunteer(?:ed)? at event-P-(\d+)-(\d+) during this-year' % NAME_RE),
 ('city', r'(?:Organization|Org) (\d+) is based in (St\. John\'s|\w+)'),
]
IRR = [r'mentioned the|mentioned Quiet|suggested ', r'I own ', r'"[A-Z][a-z]+ [A-Z][a-z]+ mentioned',
       r'talked about', r'^[^.]{0,40}(?:mentioned|suggested)', r'went to', r'attended the', r'keeps a set', r'(?:owns|has) garden tools', r'^I (?:was|handed|saw|watched|filed)',
       r'^(?:The event recap|The handoff|The club newsletter|Both topics|The reimbursement|The local profile|The contrast)', r'^(?:works for an organization|has volunteered at three|currently chooses to avoid dairy products$|ordinarily travels)',
r'owns an? ', r'recommended ', r'attends? the ', r'visited the ', r'helped with ', r'assisted with ', r'discussed ',
       r'volunteered at old-event', r'used to ', r'only in the past', r'previously attended', r'formerly ', r'visited .*(?:ago|previously|in the past)',
       r'used the (?:bus|train|tram|subway) once', r'plans to use', r'no longer', r'temporarily skipping', r'dislikes eating', r'buys \w+ for other',
       r'under identifier', r'^#', r'^Identify every', r'^c\d\.', r'^Return only', r'^`matches`', r'^Sort the',
       r'^(?:This week|The appointment|A local profile|The interview|The volunteer log|A recent personal|The travel|The meeting|In the (?:event|personal)|The administrative|As a direct|On the handoff|I noticed|I observed|I noted)',
       r'^(?:In a separate update|Elsewhere in the note|The same account|Unrelatedly)', r'\bsaid\b|\badded\b|\bexplained\b']
# context speaker tracking
speaker = None
facts, irr, unk = [], [], []
for i, s in enumerate(stm):
    m = re.search(r'(%s) (?:said|says|added|explained|continued|concluded|mentioned)\s*,?\s*["\u201d]' % NAME, s, re.I)
    if m: speaker = pid(m.group(1))
    hit = False
    for typ, rx in FACTS:
        for m in re.finditer(rx, s, re.I):
            g = m.groups()
            if typ == 'city':
                facts.append(dict(stmt=i, text=s, type='city', org=g[0], city=g[1]))
            else:
                who = pid(g[0]) if g[0].strip() != 'I' and g[0].strip().lower() != 'i' else speaker
                f = dict(stmt=i, text=s, type=typ, person=who)
                if typ == 'org': f['org'] = g[1]
                if typ == 'transit': f['mode'] = g[1]
                if typ == 'event': f['event'] = 'P-%s-%s' % (g[1], g[2]); f['event_owner'] = g[1]
                facts.append(f)
            hit = True
    if not hit:
        reason = next((r for r in IRR if re.search(r, s, re.I)), None)
        if reason: irr.append(dict(stmt=i, text=s, reason=reason))
        else: unk.append((i, s))
json.dump(dict(facts=facts, irrelevant=irr), open('extracted.json', 'w', encoding='utf8'), indent=0)
print(len(facts), len(irr), len(unk))
for u in unk[:60]: print(u)
