import re, json, sys

def split_statements(text):
    """Split context.md into statements: one per line/heading, then per sentence."""
    out = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            out.append(line)
            continue
        s = line.replace("St. John's", "St_John's")
        parts, start, i = [], 0, 0
        for m in re.finditer(r'[.!?]["\u201d]?(?=\s+|$)', s):
            end = m.end()
            before = s[start:m.start() + 1]
            # do not split after a single-letter initial ("E. Novak", "update, a. Bennett")
            if re.search(r'(?:^|[\s"(])[A-Za-z]\.$', before) and s[m.start()] == '.':
                continue
            parts.append(s[start:end].strip())
            start = end
        if s[start:].strip():
            parts.append(s[start:].strip())
        out.extend(p.replace("St_John's", "St. John's") for p in parts)
    return out

def main():
    text = open('context.md', encoding='utf8').read()
    stm = split_statements(text)
    data = json.load(open('extracted.json', encoding='utf8'))
    placed_ids = {f['stmt'] for f in data['facts']}
    placed_txt = {f['stmt']: f['text'] for f in data['facts']}
    irr = {x['stmt']: x['text'] for x in data['irrelevant']}
    placed = irrel = unacc = 0
    bad = []
    for i, s in enumerate(stm):
        if i in placed_ids and placed_txt[i] == s:
            placed += 1
        elif i in irr and irr[i] == s and i not in placed_ids:
            irrel += 1
        else:
            unacc += 1
            bad.append((i, s))
    print('total statements:', len(stm))
    print('placed:', placed)
    print('irrelevant:', irrel)
    print('unaccounted:', unacc)
    for i, s in bad[:40]:
        print('  UNACCOUNTED', i, s[:200])
    sys.exit(1 if unacc else 0)

if __name__ == '__main__':
    main()
