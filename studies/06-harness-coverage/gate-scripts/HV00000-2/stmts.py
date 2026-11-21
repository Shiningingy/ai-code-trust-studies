import re

SENT = re.compile(r'(?<=[a-z0-9)\'"\u201d])(?<!\b[A-Za-z])[.!?]["\u201d]?\s+|;\s+')
CLAUSE = re.compile(
    r',\s+(?:and |while |but |whereas )?(?=(?:[A-Za-z]\.|[A-Za-z]+) [A-Za-z]+ '
    r'(?:visited|attends|owns|discussed|recommended|helped|works|currently|routinely|used|plans|said|is based|went)'
    r'|org(?:anization)? \d+)', re.I)


def split_statements(text):
    """Split context.md into statements: headings, then sentences, then clauses."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            out.append(line)
            continue
        line = line.replace('St. John', 'St_ John')
        for p in SENT.split(line):
            for c in CLAUSE.split(p):
                c = c.strip().replace('St_ John', 'St. John')
                if c:
                    out.append(c)
    return out
