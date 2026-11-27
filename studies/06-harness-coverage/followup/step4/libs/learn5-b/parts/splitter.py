import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram import Splitter  # noqa: E402

CONN = r"and|but|while|whereas|so|then|though|although|yet|also"

REPORT_VERBS = (r"observed|noted|explained|recorded|stated|noticed|saw|watched|remember(?:ed)?|mentioned|said|says|states|records|"
                r"notes|shows|added|continued|reported|remarked|recalled|wrote|confirmed|contrasted|explains|lists|state|reports?(?! [a-z]+ that)|record(?!\s+(?:explains|notes|shows|states|reports|says|lists))|learned|reminded me|confirm|noting|explaining|also says")
SOURCE = (r"(?:the )?(?:quoted |direct )?(?:observer|speaker|record|[a-z ]*?(?:note|notes|log|recap|transcript|newsletter|bulletin|"
          r"chat|handoff|record|profile|conversation|report|reimbursement|form|email))")

# opening phrases that introduce a clause without changing what it says
INTRO_ALT = [
    r"in a separate update", r"elsewhere in the note", r"unrelatedly", r"meanwhile", r"in contrast", r"later", r"then",
    r"on the other hand", r"in the (?:team chat|community bulletin|volunteer log|event recap|interview transcript)",
    r"during (?:an ordinary team conversation|the appointment|my shift|my recent trip|the shift handoff)",
    r"as a direct observer", r"according to the speaker", r"the same account also says that",
    r"a recent personal note mentioned that", r"during an ordinary team conversation, it came up that",
    r"(?:i|we|it|he|she|they) (?:also )?(?:%s)(?: that)?" % REPORT_VERBS,
    r"(?:noting|explaining) that",
    r"it (?:came up|was (?:also )?(?:noted|mentioned|said)) that",
    r"(?:my|our) [a-z ]+? (?:%s)(?: that)?" % REPORT_VERBS,
    r"%s (?:%s)(?: that)?" % (SOURCE, REPORT_VERBS),
    r"i quoted the speaker",
    r"i (?:was|filed|am|handed|had)(?![A-Za-z])[^.:]*?(?: when| after|:)(?: i (?:remembered|noted|noticed)(?: that)?)?(?: noting that)?",
    r"(?:records?|states?|notes?|reports?|confirms?)(?= that| [A-Za-z.]+ [A-Za-z]+ )(?: that)?",
    r"i",
]
INTRO_RX = re.compile(r"(?:(?:%s)\W*)+" % "|".join(INTRO_ALT), re.I)
INTRO_START = re.compile(r"(?:(?:%s)(?:\s*[,:]\s*|\s+that\s+|\s+(?=[\"“]))?)" % "|".join(INTRO_ALT[:-1]), re.I)

ANCHOR = (r"(?:(?:[A-Za-z]\.|[A-Za-z]{2,}) [A-Za-z]{2,} (?:owns|own|recommended|suggested|discussed|talked|visited|went|attends|attended|"
          r"helped|volunteered|volunteer|currently|works|worked|used|plans|routinely|traveled|enjoys|dislikes|likes|genuinely|"
          r"prefers|chose|is|took|buys|serves|previously|says|said|only|also|no|did|has|had|keeps|mentioned)\b"
          r"|(?:Org|Organization) \d+|Youth \d+|Y\d+\b|I (?!noted|observed|made|remember))")
CUT = re.compile(
    r"[,;][\"”]?\s+|"
    r"(?:(?<=[a-z0-9']{2}\.)|(?<=[a-z0-9']{2}\.[\"”]))(?<![^A-Za-z][Ss]t\.)\s+|"
    r"\s+(?:%s)\s+(?=%s)" % (CONN, ANCHOR), re.I)
# a comma that does NOT end a clause: what follows still belongs to the same statement
NOCUT = re.compile(
    r"(?:but |and )?(?:(?:he|she|they|I|we) )?(?:no longer|does not|do not|don't|only in the past|that is in the past|that is past|only used)"
    r"|but only|(?:but )?not a guardian|for (?:Youth \d|Y\d)|in the past(?![A-Za-z])", re.I)
SAID_BEFORE = re.compile(r"(?:said|says|explains|explained|wrote|noted|stated|added|continued|mentioned|recalled|concluded|agreed|replied|answered|confirmed)(?: in the [a-z ]+)?$", re.I)

APPOS = re.compile(r"(?:^|[ \"“])I(?:, [A-Za-z.]+ [A-Za-z]+)?$")


# a pronoun subject that starts another statement about the same person ("..., and she also visited the museum")
PRONOUN_FACT = re.compile(r"(?:(?:and|but|while|whereas|so) )?(?:he|she|they) (?:also |currently |no longer |previously |only )?"
                          r"(?:visited|went|recommended|suggested|discussed|owns|attends|attended|used to|helped|volunteered|works|"
                          r"worked|routinely|plans|enjoys|dislikes|avoids|chose|likes|prefers|took|buys|serves)(?![A-Za-z])", re.I)


class MainSplitter(Splitter):
    name = "comma_and"
    solves = ("cuts a passage line into clauses at sentence ends, commas, semicolons and 'and/but/while' before a new "
              "subject; opening phrases ('In a separate update,', 'The same account also says that', 'I noted that') and "
              "connectors are dropped as droppable text; quote marks and end punctuation are trimmed")
    added_by = "learning"
    droppable = [r"[\W]*(?:(?:%s)(?![A-Za-z])\W*)*(?:(?:%s)(?![A-Za-z])\W*)*" % (CONN, "|".join(INTRO_ALT))]
    examples = [
        ("Elsewhere in the note, E. Patel visited the market some time ago, and B. Ito owns a camera.",
         ["E. Patel visited the market some time ago", "B. Ito owns a camera"]),
        ("The same account also says that leah Avery visited the museum some time ago.",
         ["leah Avery visited the museum some time ago"]),
        ("Priya Khan used to attend the chess club, but no longer does.",
         ["Priya Khan used to attend the chess club, but no longer does"]),
        ('A. Haddad said, "I own a telescope." Org 027 is based in St. John\'s.',
         ['A. Haddad said, "I own a telescope', "Org 027 is based in St. John's"]),
    ]

    def split(self, line):
        cuts = []
        for m in CUT.finditer(line):
            before, after = line[:m.start()], line[m.end():]
            if m.group(0)[:1] in (",", ";"):
                if PRONOUN_FACT.match(after):
                    continue
                head = re.split(r"(?<=[a-z0-9']{2}\.)\s", before)[-1].strip()
                if NOCUT.match(after) or SAID_BEFORE.search(head) or APPOS.search(head):
                    continue
            cuts.append((m.start(), m.end()))
        pieces, pos = [], 0
        for s, e in cuts:
            pieces.append((pos, s))
            pos = e
        pieces.append((pos, len(line)))
        out = []
        for s, e in pieces:
            seg = line[s:e]
            lead = len(seg) - len(seg.lstrip(" \"“”'"))
            seg = seg[lead:]
            s += lead
            while True:
                ls = len(seg) - len(seg.lstrip())
                seg, s = seg[ls:], s + ls
                m = INTRO_START.match(seg) or re.match(r"(?:%s)\s+" % CONN, seg, re.I)
                if not m or not m.group(0).strip() or m.end() >= len(seg):
                    break
                seg = seg[m.end():]
                s += m.end()
            seg = seg.rstrip(" .,;:\"“”")
            if INTRO_RX.fullmatch(seg):
                continue
            if seg and (words_in(seg)):
                out.append(line[s:s + len(seg)])
        return out


def words_in(t):
    return re.search(r"[A-Za-z0-9]", t) is not None
