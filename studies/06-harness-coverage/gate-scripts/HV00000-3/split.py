import re

def statements(path='context.md'):
    """Split context.md into atomic statements (clauses), tagged with passage id."""
    t = open(path, encoding='utf8').read()
    body = t.split('### Final Query')[0]
    out = []
    pid = None
    for blk in re.split(r'\n\s*\n', body):
        blk = blk.strip()
        if not blk:
            continue
        m = re.match(r'### Passage (\S+)', blk)
        if m:
            pid = m.group(1); continue
        if blk.startswith('#'):
            continue
        blk = blk.replace('St. John', 'St~ John')
        sents = re.split(r"(?<!(?<![A-Za-z'])[A-Za-z])\.\s+|\.$", blk)
        for s in sents:
            s = s.strip()
            if not s:
                continue
            for c in re.split(r'(?:,|;)\s+(?!no longer)(?:and |but |while )?|\s+(?:and|but|while)\s+(?=[A-Za-z.]+ [A-Za-z]+ (?:works|attends|visited|owns|helped|discussed|recommended|used|plans|routinely|currently|went|said)\b)', s):
                c = c.strip().replace('St~ John', 'St. John')
                if c:
                    out.append((pid, c))
    return out
