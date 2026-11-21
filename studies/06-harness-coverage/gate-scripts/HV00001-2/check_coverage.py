"""Split context.md into statements; verify each is placed (overlaps an extracted fact
in extracted.json) or explicitly irrelevant to the query. Exit 1 if any is unaccounted."""
import json, re, sys, collections

lines = open('context.md', encoding='utf8').read().split('\n')
facts = json.load(open('extracted.json'))['facts']
by_line = collections.defaultdict(list)
for f in facts:
    by_line[f['line']].append(f)

# Query-relevant vocabulary: a statement mentioning any of these must be placed.
RELEVANT = re.compile(
    r"identifier P-|familiar names?|works? for (?:Org|Organization)|is based in|"
    r"travels by|avoid dairy|volunteered at", re.I)
# Statements that look related but are explicitly not evidence for c1-c4.
DECOY = re.compile(
    r"buys \w+ for other people|dislikes eating|temporarily skipping|"
    r"used the \w+ once|plans to use the \w+ in the future", re.I)

def statements(lines):
    for ln, l in enumerate(lines, 1):
        if not l.strip(): continue
        # sentence split (not after a single-letter initial), then clause split at commas
        pos = 0
        for sm in re.finditer(r'.+?(?:(?<![\s"“][A-Za-z])[.!?]["”]?(?=\s|$)|$)', l):
            sent = sm.group(0)
            if not sent.strip(): continue
            for cm in re.finditer(r'[^,]+(?:,|$)', sent):
                s, e = sm.start() + cm.start(), sm.start() + cm.end()
                if l[s:e].strip(): yield ln, s, e

total = placed = irrelevant = 0
unaccounted = []
qstart = next(i for i, l in enumerate(lines, 1) if l.startswith('### Final Query'))
for ln, s, e in statements(lines):
    total += 1
    text = lines[ln - 1][s:e]
    if ln >= qstart or lines[ln - 1].startswith('#'):
        irrelevant += 1                       # headings, query text
    elif any(f['start'] < e and f['end'] > s for f in by_line[ln]):
        placed += 1
    elif not RELEVANT.search(text) or DECOY.search(text):
        irrelevant += 1
    else:
        unaccounted.append((ln, text))
print('total statements:', total)
print('placed:', placed)
print('irrelevant:', irrelevant)
print('unaccounted:', len(unaccounted))
for u in unaccounted[:30]: print('  ', u)
sys.exit(1 if unaccounted else 0)
