"""Splitter: cuts a content line into clauses (one fact-bearing statement each)."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gram import Splitter  # noqa: E402
from common import NAME, YOUTH, ORG, PRON  # noqa: E402

Q = "\"“”�"          # quote characters (U+FFFD is how the source garbled curly quotes)
EDGE = r"[\s%s.,;:!?]" % Q

ANCH_START = (r"(?:owns?|recommended|discussed|talked|visited|visit|went|attend\w*|helped|assisted|volunteered|works?|worked|discuss|recommend|own|"
              r"used|routinely|travels?|plans?|prefers?|chose|likes?|enjoys?|dislikes?|avoids?|skipping|is|buys|serves|"
              r"no longer|currently|genuinely|also(?!\s+(?:said|added|noted|explained|mentioned|stated|confirmed))|only|chooses?|choose|has|had|assists?|help|never)")
CLAUSE_START = re.compile(
    r"^[%s]*(?:(?:%s|%s|%s|%s)\s+%s\b|the community roster\b|Org\w* \d+ is\b|%s\s+(?:is|are|was)\b|%s\s*(?::|(?:said|says|mentioned|explains?|explained|added|concluded|continued|noted|wrote|stated|replied|agreed|answered|remarked|commented|responded)\b))"
    % (Q, ORG, YOUTH, NAME, PRON, ANCH_START, NAME, NAME), re.I)

WRAP_GUARD = re.compile(r"\b(?:owns?|recommended|discussed|visited|attend\w*|helped|volunteered|works?|roster|travels?\s+by|"
                        r"identifier|based)\b", re.I)
SPEAKS = re.compile(r"(?:\b(?:said|says|mentioned|concluded|continued|explains?|explained|added|stated|replied|noted|wrote|agreed|answered|remarked|commented|responded)|:)\s*$", re.I)
CUT = re.compile(r",[%s]*\s+|\s+(?:that|when|after|before|while|because)\s+|:\s+|"
                 r"\s+(?:notes|noted|states?|records?|recorded|lists|reports?|explains|explained|says|shows|mentioned|confirmed|confirms|know|knew)\s+(?:that\s+)?" % Q)
WRAP2 = re.compile(r"^((?:then|that|it was noted that|it came up that|(?:I|she|he|they|we) (?:also )?(?:noticed|remember(?:ed)?|observed|saw|noted|recorded|confirmed|recall(?:ed)?)"
                   r"(?: that)?|I was [^,]*? when)\s+)", re.I)
ATTACH = re.compile(r"^(?:not|for)\b", re.I)
PRON_QUAL = re.compile(r"^(?:I|he|she|they)\s+(?:am |is |are )?no longer", re.I)

BOUNDARY = re.compile(r"(?:\s*[,;][%s]*\s*(?:(?:and|while|whereas|but|though|so|which|where)\s+)?|\s+(?:and|while|whereas|but)\s+)" % Q)
SPEECH = re.compile(r"\b(?:said|says|mentioned|concluded|continued|explains?|explained|added|noted|wrote[^,]*|stated|replied|recalled|agreed|answered|remarked|commented|responded)\s*$", re.I)
QUAL_TAIL = re.compile(r"\b(?:in the past|no longer|former|lapsed|since ended|as past)\b", re.I)
AND_CLAUSE = re.compile(r"^(?:we|it|the|his|her|their|later|mentioned|picked|shared|purchased|she|he|they|I)\b")


def _all_cuts(text):
    """Every possible wrapper cut (overlapping matches included), leftmost first."""
    pos = 0
    while True:
        m = CUT.search(text, pos)
        if not m:
            return
        yield m
        pos = m.start() + 1


def _sentences(line):
    out, pos = [], 0
    for m in re.finditer(r"[.!?][%s]*\s+" % Q, line):
        before = line[pos:m.start()]
        w = re.search(r"(?:^|(?<=[\s%s]))([A-Za-z]+)$" % Q, before)
        if w and (len(w.group(1)) == 1 or w.group(1) in ("St", "Mt", "Ft", "Dr")) and line[m.start()] == ".":
            continue
        out.append((pos, m.end()))
        pos = m.end()
    out.append((pos, len(line)))
    return out


class Cutter(Splitter):
    name = "clause_cutter"
    solves = ("cuts a line into sentences and then at ', and' / ', while' / ';' / bare 'and' before a new clause, drops "
              "framing wrappers ('In a separate update,', 'I noted that') and connectors, keeps quote-intro and "
              "qualifier tails ('but only in the past') inside their clause, and emits trailing filler as its own clause")
    added_by = "learning"
    droppable = [
        r"[\s%s.,;:!?]*(?:(?:and|while|whereas|but|though|so|which|where|also)\b[\s%s.,;:!?]*)*" % (Q, Q),
        r"[\s%s.,;:!?]*[^.;]*?(?:,|\bthat)[\s%s]*" % (Q, Q),
        # a short framing phrase ('I remember', 'I saw', 'Then', 'The club newsletter states') with no fact vocabulary
        r"[\s%s.,;:!?]*(?:(?:and|while|whereas|but|though|so)\s+)?(?!.*\b(?:owns?|recommended|discussed|visited|attend\w*|"
        r"helped|volunteered|works?|roster|routinely|used)\b)[^.;]{1,100}" % Q,
    ]
    examples = [
        ('In a separate update, elena Jones discussed Atlas of Clouds. Elsewhere in the note, c. Patel visited the library some time ago.',
         ['elena Jones discussed Atlas of Clouds', 'c. Patel visited the library some time ago']),
        ('Priya Khan discussed the chess club, and Amina Chen discussed The Long Orchard.',
         ['Priya Khan discussed the chess club', 'Amina Chen discussed The Long Orchard']),
        ('T. Tran said, "I visited the library." The community roster records Amina Bennett under identifier P-021 and also uses the familiar names A. Bennett.',
         ['T. Tran said, "I visited the library',
          'The community roster records Amina Bennett under identifier P-021 and also uses the familiar names A. Bennett']),
        ('T. Patel attends the walking group, but only in the past, and R. Ito owns a guitar, a detail that was noted.',
         ['T. Patel attends the walking group, but only in the past', 'R. Ito owns a guitar', 'a detail that was noted']),
        ('I, omar foster, helped with registration at the library. I observed that elena ito no longer attends the history group, gabriel evans helped with cleanup at the market.',
         ['I, omar foster, helped with registration at the library', 'elena ito no longer attends the history group',
          'gabriel evans helped with cleanup at the market']),
        ('N. Tran explains, "I used to attend the garden circle, but I no longer do. Ben Haddad visited the library."',
         ['N. Tran explains, "I used to attend the garden circle, but I no longer do', 'Ben Haddad visited the library']),
        ("Org 003 is based in St. John's. Elsewhere in the note, Mia Ito owns a guitar, which he uses for stargazing.",
         ["Org 003 is based in St. John's", 'Mia Ito owns a guitar', 'he uses for stargazing']),
        ('D. Haddad likes train and plane equally, Q. Silva dislikes eating milk.',
         ['D. Haddad likes train and plane equally', 'Q. Silva dislikes eating milk']),
    ]

    def split(self, line):
        clauses = []
        for s0, s1 in _sentences(line):
            clauses.extend(self._sentence(line, s0, s1))
        return clauses

    def _trim(self, line, a, b):
        while a < b and re.match(EDGE, line[a]):
            a += 1
        while b > a and re.match(EDGE, line[b - 1]) and not (line[b - 1] == "." and re.search(r"\b(?:St|Mt|Ft)$", line[a:b - 1])):
            b -= 1
        return a, b

    def _strip_wrapper(self, line, a, b):
        for _ in range(3):
            text = line[a:b]
            m = WRAP2.match(text)
            if m and text[m.end():].strip():
                a += m.end()
                continue
            if CLAUSE_START.match(text):
                break
            for m in _all_cuts(text):
                prefix, rest = text[:m.start()], text[m.end():]
                if SPEAKS.search(prefix) and re.match(r"[%s]*(?:I(?!\.)|he|she|they|we)\b" % Q, rest, re.I):
                    continue  # 'X said that she ...' / 'X: "I ...': the speaker belongs to the clause
                if len(prefix.split()) <= 18 and not WRAP_GUARD.search(prefix) and CLAUSE_START.match(rest):
                    a += m.end()
                    break
            else:
                break
        return a

    def _sentence(self, line, s0, s1):
        a, b = self._trim(line, s0, s1)
        if a >= b:
            return []
        a = self._strip_wrapper(line, a, b)
        # boundaries inside the sentence
        pieces, start = [], a
        for m in BOUNDARY.finditer(line, a, b):
            if m.start() < start:
                continue
            head = line[start:m.start()]
            if SPEECH.search(head) and m.group(0).strip().startswith(",") and re.match(
                    r"[%s]|(?:I(?!\.)|he|she|they|we|that)\b" % Q, line[m.end():b], re.I):
                continue
            if re.fullmatch(r"I(?:,\s*%s)?" % NAME, head.strip()) and m.group(0).strip().startswith(","):
                continue  # 'I, omar foster, helped ...': the speaker names themself
            pieces.append((start, m.start(), m.end(), m.group(0)))
            start = m.end()
        pieces.append((start, b, b, ""))
        # re-cut: decide for each boundary whether it separates clauses
        clauses = []          # list of [a, b]
        cur = None
        prev_sep = ""
        for (p0, p1, nxt, sep) in pieces:
            frag_a = p0
            if cur is None:
                cur = [p0, p1]
            else:
                text = line[p0:p1]
                text_w = line[self._strip_wrapper(line, p0, p1):p1]
                comma = prev_sep.strip().startswith((",", ";"))
                if ATTACH.match(text) or PRON_QUAL.match(text):
                    cur[1] = p1
                elif CLAUSE_START.match(text) or CLAUSE_START.match(text_w):
                    clauses.append(cur)
                    cur = [self._strip_wrapper(line, p0, p1), p1]
                elif QUAL_TAIL.search(text):
                    cur[1] = p1
                elif comma or AND_CLAUSE.match(text):
                    clauses.append(cur)
                    cur = [p0, p1]
                else:
                    cur[1] = p1
            prev_sep = sep
        clauses.append(cur)
        out = []
        for x, y in clauses:
            x, y = self._trim(line, x, y)
            if x < y:
                out.append(line[x:y])
        return out
