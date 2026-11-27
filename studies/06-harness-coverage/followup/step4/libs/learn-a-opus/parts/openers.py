"""Discourse: openers that introduce a clause and framing sentences that carry no fact. All are ignore-rules.

An opener or framing sentence that contains a word changing the meaning of a fact (a time such as 'in the past',
'previously', 'last week', a negation) is never ignored: it falls through as unparsed so it can be looked at.
"""
import re

from gram import Rule

# words that would change the meaning of the clause they introduce; never ignore an opener containing them
MEANINGFUL = re.compile(r"\b(?:past|previous(?:ly)?|former(?:ly)?|no longer|not|never|ago|yesterday|today|tomorrow|"
                        r"last|next|used to|future|currently|now|rumou?r\w*|allegedly|maybe|perhaps|might|"
                        r"unconfirmed|reportedly)\b", re.I)
_SRC = r"[A-Za-z][\w'-]*(?: [A-Za-z][\w'-]*){0,8}?"       # a short noun phrase naming a source ('the volunteer log')
_SAY = (r"(?:says|said|say|noted|notes|note|records|recorded|record|shows|showed|show|states|stated|state|explains|"
        r"explained|explain|mentioned|mentions|reports|reported|report|contrasted|lists|listed|highlights|confirms|"
        r"confirmed|adds|added|observed|observes|indicates|indicated|captured|captures)")
OPENERS = [
    # pure connectives
    r"(?:In a separate update|Elsewhere in the note|Unrelatedly|In contrast|By contrast|Meanwhile|Later|Also|Then|"
    r"Nearby|Separately|Additionally|Similarly|Likewise|On the other hand|According to the speaker|As a direct "
    r"observer|On the handoff),?",
    # "The same account also says that", "The volunteer log noted that", "The appointment note records that"
    r"(?:The|This|A|An|Our|My)? ?%s (?:also )?%s(?: that)?" % (_SRC, _SAY),
    # "In the volunteer log,", "During the meeting,", "While preparing my travel reimbursement,", optionally followed by
    # "it came up that" / "the quoted speaker explained that" / "I noted that"
    r"(?:In|On|At|From|During|For|While preparing|While reviewing|Within) %s,(?: (?:it came up that|it was (?:also )?"
    r"(?:noted|mentioned) that|I (?:also )?(?:noted|observed|recorded) that|the quoted speaker %s that))?" % (_SRC, _SAY),
    # "It was also mentioned that"
    r"It was (?:also )?(?:mentioned|noted|recorded) that",
    # narrator: "I observed that", "I noted in the community bulletin that", "I quoted the speaker:", "I remember"
    r"I (?:also )?(?:observed|noted|noticed|explained|recorded|stated|saw|remember|remembered|heard|learned|"
    r"confirmed|quoted the speaker|wrote)(?: in %s)?(?: that)?:?" % _SRC,
    # narrator scene-setting before a clause: "I filed the reimbursement after", "I was filing ... when",
    # "I handed off the shift with notes:"
    r"I (?:was|filed|handed off|am) %s (?:when(?: I (?:remembered|noted)(?: that)?)?|after(?: noting that)?|notes:|"
    r"with notes:)" % _SRC,
    # a pronoun report cut off after a connector: "..., and she explained that Leah Silva helped ..."
    r"(?:he|she|they|I) (?:also )?(?:(?:explained|said|noted|mentioned|added|confirmed|stated) that|(?:remembered|"
    r"remember|recalled|know|knew)(?: that)?)",
    # a bare leading adverb: "Then Omar Tran recommended ..."
    r"(?:Then|Later|Also|Meanwhile|Nearby|Next|Afterwards|Finally)",
]
_OPENER_RX = [re.compile(r"\"?%s" % p, re.I) for p in OPENERS]
_ENTITY = re.compile(r"\b(?:[A-Z]\. [A-Z][a-z]+|Org(?:anization)? \d+|Youth \d+|Y\d{3}|P-\d+|event-)", re.I)


class DiscourseOpener(Rule):
    name = "discourse_opener"
    ignore = True
    solves = ("discourse openers the splitter cuts off before a clause ('In a separate update,', 'Elsewhere in the "
              "note,', 'The same account also says that', 'I observed that', 'During the meeting,'): they only say "
              "where a statement comes from, so they carry no fact; openers with a time or negation word are not "
              "taken")
    added_by = "learning"
    examples = [("In a separate update,", []), ("The same account also says that", []),
                ("During an ordinary team conversation, it came up that", []), ("I observed that", []),
                ("I was filing a travel reimbursement when", []), ("she explained that", []),
                ("For the travel reimbursement,", []), ("As a direct observer, I noted that", []),
                ("In the past,", None)]

    def parse(self, clause):
        c = clause.strip()
        if MEANINGFUL.search(c) or _ENTITY.search(c) or _PERSONISH.search(c):
            return None
        # openers may be chained: "As a direct observer, I noted that"
        if any(rx.fullmatch(c) for rx in _OPENER_RX):
            return []
        parts = re.split(r"(?<=,) ", c)
        return [] if all(any(rx.fullmatch(p) for rx in _OPENER_RX) for p in parts) else None


# framing sentences: a source and what it contains, or narrator scene-setting, with no person, org or youth
_FRAMING = [
    r"(?:The|This|A|An|Our|My) %s (?:collected|recorded|records|moved|included|includes|include|covered|touched on|"
    r"highlights|shows|show|captured|was|were|is|are|notes|noted|explains|explained|required|stood|contains|lists) "
    r"[^\"]*" % _SRC,
    r"(?:Both|The two) [^\"]*",
    # narrator scene-setting; "I am/was <verb>ing" only for verbs that are not facts ("I am skipping butter" is one)
    r"I (?:was|am) (?!(?:skipping|avoiding|attending|working|volunteering|helping|visiting|planning|eating|serving|"
    r"buying|travell?ing|using|taking|enjoying|owning)\b)[a-z]+ing\b[^\"]*",
    r"I (?:was at|recently|noted a|noted it|had|explained that both|handed off|stated|said|noticed a|plan to read|"
    r"filed|made) [^\"]*",
    r"During %s, I noted [^\"]*" % _SRC,
    r"During %s, I had [^\"]*" % _SRC,
    r"It was [^\"]*",
    r"I (?:said|noted|explained|added|stated|continued|concluded)(?: in %s)?" % _SRC,
]
_FRAMING_RX = [re.compile(r"\"?%s[.!]?\"?" % p, re.I) for p in _FRAMING]
# "The contrast between the past routine and the recent help was clear.": a comment on how two entries differ. Its
# time words ("past", "current") name the entries, they do not qualify a fact, so it is ignored even with them.
_CONTRAST = re.compile(r"The contrast between (?:the |a )?[\w' -]+ and (?:the |a )?[\w' -]+ (?:was|is|made) [\w' -]+[.!]?",
                       re.I)
_PRONOUN_FACT = re.compile(r"^\"?(?:he|she|they|we)\b", re.I)
_PERSONISH = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b|\b[A-Za-z]\. [A-Z][a-z]+\b")


class FramingSentence(Rule):
    name = "framing_sentence"
    ignore = True
    solves = ("sentences that frame a passage and name no person, org or youth ('The appointment note recorded a few "
              "pieces of background.', 'I was filling out the travel reimbursement form and had to explain the "
              "context.'); sentences with a time/negation word or a pronoun subject ('He used to ...') are not taken")
    added_by = "learning"
    examples = [("This week's community bulletin collected several unrelated updates.", []),
                ("The interview moved across several topics.", []),
                ("I am submitting this travel reimbursement for recent activities.", []),
                ("During the shift handoff, I noted a few key points.", []),
                ("I am temporarily skipping butter.", None),
                ("He used to attend the walking group, but only in the past.", None),
                ("The contrast between the two entries is clear in the volunteer log.", []),
                ("The contrast between the past routine and the recent help was clear.", []),
                ("The quoted speaker explained the travel reimbursement context clearly.", [])]

    def parse(self, clause):
        c = clause.strip()
        if _ENTITY.search(c) or _PERSONISH.search(c) or _PRONOUN_FACT.search(c):
            return None
        if _CONTRAST.fullmatch(c):
            return []
        if MEANINGFUL.search(c):
            return None
        return [] if any(rx.fullmatch(c) for rx in _FRAMING_RX) else None
