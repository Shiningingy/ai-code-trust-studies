import re
from gram import Splitter

# a clause start: a person (or youth, or the roster phrase) followed by a verb of the grammar
_VERB = (r"(?:owns?|recommended|attends?|attended|visited|went|helped|assisted|discussed|talked|works?|worked|used|routinely|"
         r"likes|genuinely|chose|plans|currently|is|buys|serves|dislikes|enjoys|previously|formerly|took|volunteer(?:ed|s)?|"
         r"mentioned|says?|said|explains?|explained|wrote|travels?|traveled|prefers?|no longer|has)")
_NOT_NAME = r"(?!(?:that|which|it|she|he|they|this|there|who|and|but|the|a|an|his|her|their|we|I|its|our|my|so|then|though|although|because|since|said|says|also|later|then|afterwards|often|noted|explained|mentioned|meanwhile|only|still|both|now|does|did|do|is|was|were|are|has|have|had|been|being|be|can|could|will|would|meaning|as|with|for|to|in|at|by|if|when|where|whom|whose|why|how|what|unlike)\b(?!\.))"
_START = (_NOT_NAME + r"(?:[A-Za-z]\. [A-Za-z]+|[A-Za-z]+(?: [A-Za-z]+)?|[Yy]outh \d+|[Yy]\d+) (?:(?:also|simply|just|only|still|even) )?" + _VERB
          + r"\b|(?:the community roster records|(?:Org|Organization) \d+ is based)\b")
_WHO = r"(?:[A-Za-z]\. [A-Za-z]+|[A-Za-z]+ [A-Za-z]+),? who\b"
_CONNECT = (r"and|while|but|whereas|noting|explaining|adding|saying|observing|remarking|mentioning|showing|that|"
            r"(?:and|but) I (?:also )?(?:learned|saw|noticed|remember|remembered|heard|observed|noted)(?: that)?|unlike|in contrast to|rather than|compared (?:to|with)|"
            r"which is different from(?: the fact that)?|which is a (?:nice )?contrast to|which contrasts with|a contrast to|"
            r"that is different from|and that")
_JOIN = re.compile(r"(?:,? (?:%s) (?:that )?|[,;] )(?=%s|%s)" % (_CONNECT, _START, _WHO), re.I)

# opening phrases that only set the scene (they never change what the clause says)
_INTRO = (r"(?:In a separate update|Elsewhere in the note|The same account also says that|Unrelatedly|"
          r"A recent personal note mentioned that|During an ordinary team conversation, it came up that|"
          r"In an event recap|I stated that|The speaker noted that|The speaker mentioned that|The record shows that|"
          r"It was also mentioned that|The club newsletter records that|My meeting notes record|"
          r"(?:In|During|At|Within|Throughout|Over|Across|After|Before|On|Per|From) (?:the|a|an|my|our|this|that) [a-z' -]+|"
          r"Nearby|Meanwhile|Later|Also|Separately|Additionally|In contrast|By contrast|However|Still|Overall|Elsewhere|Otherwise)")
_INTRO_RX = re.compile(r"(?:%s),?\s+(?=%s)" % (_INTRO, _START), re.I)

# attribution openings ("According to the speaker, ...", "I noted in the bulletin that ...") are meaningful: keep them
_ATTRIB_RX = re.compile(r"(?:During (?:this|last)[- ]year,\s+|According to [^,]+,\s+|[^,\"“.]*\b(?:noted|said|explained|remembered?|observed|stated|states|notes|recalled|recorded|records?|shows?|showed|reports?|reported|confirmed|learned|saw|noticed|continued|concluded|added|agreed|wrote|writes|heard|contrasted)\b"
                        r"(?: in (?:the|a|my|our) [a-z ]+?)?(?: that)?\s+|[^,]*, I noted that\s+|I was [^,]*? when\s+)", re.I)


class SentenceClause(Splitter):
    name = "sentence_clause"
    solves = ("cuts a passage line into sentences (not after initials like 'E.' or 'St.'), strips scene-setting opening "
              "phrases and quote marks, and cuts compound sentences at ', and' / ', while' / ', but' / ', ' when a new "
              "subject+verb follows (speech-introducing openings such as 'The observer noted that' stay in the clause)")
    added_by = "learning"
    droppable = [r"[\s.,;:\"“”']*", r"[\s.,;:\"“”']*(?:%s)?(?: that)?[\s.,;:\"“”']*" % _CONNECT,
                 r"[\s.,;:\"“”']*(?:%s),?[\s\"“”']*" % _INTRO]
    examples = [
        ("E. Patel visited the market. B. Ito owns a garden tools.",
         ["E. Patel visited the market", "B. Ito owns a garden tools"]),
        ("F. Avery discussed history group, and K. Patel owns a camera.",
         ["F. Avery discussed history group", "K. Patel owns a camera"]),
        ("Elsewhere in the note, c. Patel visited the library some time ago.",
         ["c. Patel visited the library some time ago"]),
        ("Org 003 is based in St. John's. Kofi Khan attends the history group.",
         ["Org 003 is based in St. John's", "Kofi Khan attends the history group"]),
        ("B. Mensah discussed chess club activities, and the group is very active.",
         ["B. Mensah discussed chess club activities, and the group is very active"]),
    ]

    def split(self, line):
        sents, start = [], 0
        for m in re.finditer(r"([.!?][\"”’]?)(\s+)", line):
            j = m.start()
            prev = re.search(r"(\S+)$", line[:j])
            tok = prev.group(1) if prev else ""
            if re.fullmatch(r"[\"“(]?[A-Za-z]", tok) or tok in ("St", "Mt", "Ste"):
                continue
            sents.append(line[start:j])
            start = m.end()
        sents.append(line[start:])
        out = []
        for s in sents:
            s = s.strip()
            if not s:
                continue
            m = _INTRO_RX.match(s)
            if m:
                s = s[m.end():]
            s = s.lstrip("\"“ ").rstrip(".\"” ")
            pre = _ATTRIB_RX.match(s)
            base = pre.end() if pre else 0       # an attribution opening stays attached to the first clause
            pos = 0
            for jm in _JOIN.finditer(s, base):
                if re.search(r"\b(?:said|says|added|noted|confirmed|explained|explains|mentioned|stated|continued|concluded|agreed|wrote|states|"
                             r"observed|remarked|reported)$", s[pos:jm.start()]):
                    continue     # 'X added, "Y ..."': the quote belongs to the speech clause
                out.append(s[pos:jm.start()])
                pos = jm.end()
            out.append(s[pos:])
        return [c for c in out if c.strip()]
