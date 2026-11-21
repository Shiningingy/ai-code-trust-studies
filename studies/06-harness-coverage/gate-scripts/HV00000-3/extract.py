"""Extract roster / org / employment / shift / travel facts from context.md and answer the query.
Writes extracted.json (placed statements + derived data). Also exposes classify() used by check_coverage.py."""
import re, json, collections
from split import statements

NAME = r"(?:[A-Za-z]\.|[A-Za-z]{2,}) [A-Za-z]{2,}"
PREFIX = re.compile(r"^(?:The same account also says that|A recent personal note mentioned that|Elsewhere in the note,|In a separate update,|Unrelatedly,|I noted that|I remember|Also,)\s+", re.I)
TRANSPORT = r"(subway|bus|train|tram)"

def norm(n):
    a, b = n.split(' ')
    return (a[0].upper() + a[1:].lower()) + ' ' + b.capitalize()

def clean(s):
    s = s.strip().strip('"“”').strip()
    s = re.sub(r'^[“”"]+|[“”"]+$|^\W\W(?=I )', '', s).strip()
    s = s.replace('��', '').strip()
    prev = None
    while prev != s:
        prev = s
        s = PREFIX.sub('', s)
    return s

def classify(S):
    """Return list of (idx, kind, detail) per statement; kind in placed:* / irrelevant / unaccounted."""
    res = []
    for i, (pid, raw) in enumerate(S):
        s = clean(raw)
        prev = S[i-1][1] if i else ''
        m = None
        if (m := re.search(rf"community roster (?:records|lists) ({NAME}) under identifier (P-\d+)(?: and also uses the familiar names ({NAME}))?", s, re.I)):
            res.append((i, 'placed:roster', dict(name=norm(m[1]), id=m[2].upper(), alias=norm(m[3]) if m[3] else None))); continue
        if (m := re.search(r"\b(?:Org|Organization) (\d+) is based in ([A-Za-z.' ]+?)$", s, re.I)):
            res.append((i, 'placed:orgcity', dict(org=m[1], city=m[2]))); continue
        if (m := re.search(rf"\b(I|{NAME}) (?:currently )?works? for (?:Org|Organization) (\d+)$", s, re.I)):
            who = m[1]
            if who == 'I':
                pm = re.search(rf"({NAME}) (?:said|says|explains)$", prev)
                who = pm[1] if pm else None
            res.append((i, 'placed:employ', dict(who=norm(who) if who else None, org=m[2]))); continue
        if re.search(r"night shift", s, re.I):
            if re.search(r"former role|used to work|worked", s, re.I):
                res.append((i, 'placed:night_former', {})); continue
            if (m := re.search(rf"({NAME}) works the night shift$", s, re.I)):
                res.append((i, 'placed:night', dict(who=norm(m[1])))); continue
            res.append((i, 'unaccounted', s)); continue
        if re.search(r"routinely travel|used to (?:routinely )?travel|travel by \w+ routinely", s, re.I):
            if re.search(r"no longer|used to", s, re.I):
                res.append((i, 'placed:travel_former', {})); continue
            if (m := re.search(rf"({NAME}) routinely travels by {TRANSPORT}(?: to work)?(?:,.*)?$", s, re.I)):
                res.append((i, 'placed:travel', dict(who=norm(m[1])))); continue
            res.append((i, 'unaccounted', s)); continue
        if re.fullmatch(r"(?:though |but )?(?:he |she |they |I )?no longer do(?:es)?\.?", s, re.I):
            res.append((i, 'irrelevant', s)); continue
        if re.search(r"\b(?:works? for|based in|roster|routinely|commut)", s, re.I):
            res.append((i, 'unaccounted', s)); continue
        res.append((i, 'irrelevant', s))
    return res
