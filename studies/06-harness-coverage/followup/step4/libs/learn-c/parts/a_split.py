"""Splitter and normalizers: cut a line into sentences and clauses, repair case/quote form."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from gram import Splitter, Normalizer
from gcommon import SUBJ_RX, PRED_START, STOP, fact_shape, MARKER_WORDS

# fixed opening phrases that only introduce a clause (they carry no facts of their own)
LEAD = (r"(?:In a separate update,?|Elsewhere in the note,?|Unrelatedly,?|Meanwhile,?|Later,?|Then|Nearby,?|In contrast,?|"
        r"The same account also says that|A recent personal note mentioned that|"
        r"During an ordinary team conversation, it came up that)")
# free-form framing prefix: 'The club newsletter records that', 'I noted in the bulletin that', 'I remember', 'During the meeting,'
FRAME_OPEN = r"(?:The|My|This|Our|I|It|During|In|At|According|As|While|He|She|A|An|Also|And|Then)\b"
FRAME_END_WORD = (r"(?:\bthat|:|\bwhen|,|\brecords?|\bnoted|\bstates?|\bstated|\bshows?|\bremember|\bsaid|\bnotes?|\bexplained|"
                  r"\bexplains|\bobserved|\bnoticed|\bcontrasted|\bafter|\blists)")
FRAME = r"(?:%s[^.;:\"]*?%s)" % (FRAME_OPEN, FRAME_END_WORD)
CONNECT = r"(?:\s*;\s*|\s*,\s*(?:and|while|whereas|but|so)\s+|\s*,\s+|\s+and\s+|\s+while\s+|\s+but\s+)"
CLAUSE_START = (r'["“]?(?:%s)\s+(?:(?:also|simply|just|still|even)\s+)?%s\b|["“]?(?:the )?community roster records\b' % (SUBJ_RX, PRED_START))
ELAB = (r"\s*,\s*(?:and\s+)?(?!the community roster)(?=(?:which|a|an|where|ensuring|so|showing|highlighting|noting|adding|bringing|"
        r"providing|making|having|though|[a-z]+ing|before|during|both|another|kept|meaning|he|she|they|it|the|I|his|her|their)\b)")
# commentary that changes the meaning of the clause before it stays attached to that clause
KEEP = MARKER_WORDS
FRAME_END = re.compile(r"(?:said|says|added|mentioned|explained|explains|wrote in the volunteer log|wrote|concluded|continued|stated|noted)$", re.I)
I_VERBS = (r'I (?:also |currently |used |am |own|attend|work|visited|helped|recommended|discussed|volunteered|routinely|plan|like|'
           r'enjoy|dislike|buy|serve|chose|choose|genuinely)')


def _first_ok(rest):
    """True if `rest` begins a new 'SUBJECT PREDICATE' clause."""
    m = re.match(r'["“]?([A-Za-z]+)', rest)
    if not m:
        return False
    if re.match(r'["“]?the community roster records\b', rest, re.I):
        return True
    w = m.group(1).lower()
    if re.match(r'["“]?[A-Za-z]\.', rest):
        return bool(re.match(CLAUSE_START, rest, re.I))
    if w == "i":
        return bool(re.match(r'["“]?' + I_VERBS, rest))
    return w not in STOP and bool(re.match(CLAUSE_START, rest, re.I))


def lead_len(t):
    """Length of an introducing phrase at the start of t (0 if none)."""
    m = re.match(LEAD + r"\s*", t)
    if m and m.end() < len(t):
        return m.end()
    if not re.match(FRAME_OPEN, t):
        return 0
    for m in re.finditer(FRAME_END_WORD + r"\s+", t[:240]):
        pre = t[:m.end()]
        if re.search(r'[.;"]', pre):
            break
        if m.end() < len(t) and not fact_shape(pre) and _first_ok(t[m.end():]):
            return m.end()
    return 0


class ClauseSplitter(Splitter):
    name = "clause_splitter"
    solves = ("cuts a line into sentences, then into clauses at connectors (', and', ', while', ', whereas', ', but', ';', "
              "', ') that are followed by a new 'SUBJECT PREDICATE'; drops lead-in phrases such as 'In a separate update,' or "
              "'The club newsletter records that'; cuts trailing commentary (', which ...', ', a task that ...') into its own clause "
              "unless it changes the meaning (past / no longer), in which case it stays with its clause")
    added_by = "learning"
    droppable = [LEAD + r"[\s,]*", FRAME + r"[\s,]*",
                 r"[\s,;]*(?:(?:and|while|whereas|but|so)\s+)?(?:" + LEAD + "|" + FRAME + r")[\s,]*", r"\s*;\s*", r"\s*,?\s*(?:and|while|whereas|but|so)?\s*",
                 r"[\s,.;:\"“”]*"]
    examples = [
        ("Dev Evans owns a telescope, and Rosa Diaz visited the library.",
         ["Dev Evans owns a telescope", "Rosa Diaz visited the library."]),
        ("In a separate update, gabriel Haddad currently works for Org 027. Elsewhere in the note, h. Mensah visited the museum.",
         ["gabriel Haddad currently works for Org 027.", "h. Mensah visited the museum."]),
        ("Leah Tran likes train and plane equally.", ["Leah Tran likes train and plane equally."]),
        ("The club newsletter records that Dev Gupta owns a camera, and the community roster records Dev Gupta under identifier P-001.",
         ["Dev Gupta owns a camera", "the community roster records Dev Gupta under identifier P-001."]),
        ("Ben Khan visited the market, a task that was fine.", ["Ben Khan visited the market", "a task that was fine."]),
    ]

    def sentences(self, line):
        out, start, n = [], 0, len(line)
        for m in re.finditer(r'[.!?]["”]?(?=\s+["“]?[A-Za-z])', line):
            end = m.end()
            before = line[start:m.start() + 1]
            lastw = re.search(r"(\S+)$", before).group(1)
            if re.fullmatch(r"(?:.*[\s\"“(])?[A-Za-z]\.", lastw) or lastw in ("St.",):
                continue
            out.append((start, end))
            start = end
            while start < n and line[start].isspace():
                start += 1
        if start < n:
            out.append((start, n))
        return out

    def split(self, line):
        clauses = []
        for (a, b) in self.sentences(line):
            sent = line[a:b]
            spans = []            # connector / lead-in text to drop: (start, end)
            k = lead_len(sent)
            if k:
                spans.append((0, k))
            for m in re.finditer(CONNECT, sent):
                if m.start() > 0 and (_first_ok(sent[m.end():]) or lead_len(sent[m.end():])) and not FRAME_END.search(sent[:m.start()]):
                    spans.append((m.start(), m.end()))
            for m in re.finditer(ELAB, sent):
                nxt = re.search(r"[.;]|, (?:and|while|whereas|but) [A-Z]", sent[m.end():])
                tail = sent[m.end():m.end() + nxt.start()] if nxt else sent[m.end():]
                if not re.search(KEEP, tail) and not FRAME_END.search(sent[:m.start()]):
                    spans.append((m.start(), m.end()))
            spans.sort(key=lambda t: (t[0], -t[1]))
            pos = 0
            for (x, y) in spans:
                if x < pos:
                    continue
                if sent[pos:x].strip():
                    clauses.append(sent[pos:x].strip())
                pos = y
                k = lead_len(sent[pos:])
                pos += k
            if sent[pos:].strip():
                clauses.append(sent[pos:].strip())
        return clauses


class StraightQuotes(Normalizer):
    name = "straight_quotes"
    solves = "turns curly quotes and broken (replacement-character) quotes into straight ones so rules see one quote form"
    added_by = "learning"
    examples = [("“I own a camera.”", '"I own a camera."'), ("�I own a camera.�", '"I own a camera."')]

    def apply(self, clause):
        return clause.replace("�", '"').replace("“", '"').replace("”", '"').replace("’", "'")
