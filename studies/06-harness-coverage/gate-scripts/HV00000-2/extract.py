import re, json, stmts

N = r"((?:[A-Za-z]\.|[A-Za-z]+) [A-Za-z']+)"
Q = "[\"\u201c\u201d]"
FACT = [
 ('roster', re.compile(r"(?:records|lists) "+N+r" under identifier (P-\d+)(?: and also uses the familiar names "+N+")?", re.I)),
 ('orgcity', re.compile(r"org(?:anization)? (\d+) is based in ((?:St\. )?[A-Za-z' ]+?)\s*(?:[.,;]|$)", re.I)),
 ('works', re.compile(N+r" (currently )?works for org(?:anization)? (\d+)", re.I)),
 ('transport', re.compile(N+r" routinely travels by (\w+)( but no longer does)?", re.I)),
 ('transport_past', re.compile(N+r" used to (?:routinely )?travel by (\w+)", re.I)),
 ('shift', re.compile(N+r" works the (day|night) shift( in a former role)?", re.I)),
 ('shift_past', re.compile(N+r" (?:used to work|worked) the night shift", re.I)),
 ('fp_works', re.compile(N+r"[^\"\u201c\u201d]*"+Q+r"\s*I (currently )?work for org(?:anization)? (\d+)", re.I)),
 ('fp_shift', re.compile(N+r"[^\"\u201c\u201d]*"+Q+r"\s*I (work the|used to work the) (day|night) shift( in a former role)?", re.I)),
 ('fp_transport', re.compile(N+r"[^\"\u201c\u201d]*"+Q+r"\s*I (used to )?routinely travel by (\w+)( but no longer do)?", re.I)),
]
KEY = re.compile(r"org(anization)?\b|work|employ|travel|commut|shift|identifier|familiar|based|city|\b(bus|train|tram|subway|metro|transit|ride|rides)\b", re.I)
CONN = re.compile(r"(In a separate update|Elsewhere in the note|Unrelatedly|The same account also says that|Meanwhile)", re.I)

def classify(s):
    if s.startswith('#'):
        return 'irrelevant', 'structural heading'
    facts = []
    for kind, rx in FACT:
        for m in rx.finditer(s):
            facts.append([kind] + [g for g in m.groups()])
    if facts:
        return 'placed', facts
    if re.match(r'Return only|c\d\.|Identify every|`matches`|works for an organization|ordinarily travels|currently works a night', s):
        return 'irrelevant', 'query text'
    if CONN.fullmatch(s.strip(' ,.')):
        return 'irrelevant', 'connective phrase'
    if not KEY.search(s):
        return 'irrelevant', 'no organization/transport/shift/identity content'
    if re.search(r"(used the \w+ once|plans to use the \w+ in the future|visited|attends|owns|discussed|recommended|helped with)", s):
        return 'irrelevant', 'distractor: non-habitual transport or unrelated activity/ownership'
    if re.search(r"travel (note|reimbursement)|expenses|shift handoff|handed off the shift|volunteer shift|my shift|next shift|I recently traveled", s):
        return 'irrelevant', 'framing/narrative sentence with no qualifying fact'
    return None, None

if __name__ == '__main__':
    t = open('context.md', encoding='utf8').read()
    out = []
    for i, s in enumerate(stmts.split_statements(t)):
        st, d = classify(s)
        if st is None:
            st = 'unaccounted'
        out.append({'i': i, 'text': s, 'status': st, 'detail': d})
    json.dump(out, open('extracted_statements.json', 'w', encoding='utf8'), indent=0)
    from collections import Counter
    print(Counter(o['status'] for o in out))
    for o in [o for o in out if o['status'] == 'unaccounted']: print(ascii(o['text']))
