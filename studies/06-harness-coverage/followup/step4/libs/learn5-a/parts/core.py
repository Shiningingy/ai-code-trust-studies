"""Shared vocabulary and the clause-rule base class used by the other parts of this library.

Not a part itself (it defines no named part). Names of people are canonicalised: first names written as initials
are expanded ("N. Reed" -> "Nadia Reed") because every initial maps to one first name in the known roster.
"""
import json
import re
from abc import abstractmethod

from gram import Rule

FIRST = "Amina Ben Carla Dev Elena Farah Gabriel Hana Isaac Jia Kofi Leah Mateo Nadia Omar Priya Quinn Rosa Samir Talia".split()
SURNAMES = ("Avery Bennett Chen Diaz Evans Foster Gupta Haddad Ito Jones Khan Laurent Mensah Novak Ortiz Patel Reed Silva "
            "Tran Usman").split()
INITIAL = {f[0]: f for f in FIRST}

Q = "\"“”"
_NOT_NAME = (r"(?!(?:The|A|An|In|On|At|Org|Organization|Youth|This|That|Elsewhere|Unrelatedly|Meanwhile|Later|During|"
             r"According|Also|Then|Nearby|She|He|They|It)\b)")
# a person name as written: "Nadia Reed" or "N. Reed" (case noise is repaired by a normalizer)
NAME = r"(?:[A-Z]\.|%s[A-Z][a-z]+) [A-Z][a-z]+" % _NOT_NAME
SPEECH = (r"(?:said|says|noted|added|explained|explains|stated|mentioned|replied|remarked|continued|concluded|wrote|"
          r"suggested|recorded|observed|noted|recalled|confirmed|learned|agreed)")
PRON = r"(?:he|she|they)"

REPORT_WORDS = re.compile(r"\b(said|says|noted|notes|explained|stated|states|mentioned|quoted|speaker|according|observer|"
                          r"observed|noticed|saw|remember|recorded|records|reports|reported|shows|showed|transcript)\b", re.I)
HEDGE_WORDS = re.compile(r"\b(reportedly|apparently|allegedly|supposedly|perhaps|maybe|possibly|probably|seems?|believe[sd]?|"
                         r"think|thinks|rumou?r(?:ed)?|might|may|likely|i guess)\b", re.I)

# words that change what a clause means when they follow a fact (time, frequency, negation, state)
TAIL_Q = re.compile(
    r"\b(only in the past|in the past|some time ago|previously|formerly|no longer|not anymore|used to|has since lapsed|"
    r"has since ended|since lapsed|lapsed|never|not|every (?:\w+ )?(?:day|week|month|year|morning|evening|night|weekend|\w+day)|"
    r"on (?:weekends|weekdays|\w+days)|regularly|weekly|daily|monthly|often|sometimes|rarely|occasionally|usually|"
    r"always|now|currently|still|again|once|twice|last (?:week|weekend|month|year|night)|more recently|recently|yesterday|"
    r"today|this (?:week|month|year)|soon|temporarily|in the future|someday|tomorrow)\b", re.I)

START_WORDS = (r"that|says?|said|noted|saw|noticed|observed|remember|states?|shows?|notes?|records?|explained|recorded|"
               r"mentioned|stated|reports|the log|and|while|whereas|though|when|but|added|after|before|because|as|if|so|until|"
               r"once|then|noting|which|where|also noted|also said")
NARR_VERBS = (r"(?:also )?(?:confirmed|learned|took|read|thought|realized|decided|observed|noted|explained|recorded|noticed|saw|stated|remember|remembered|quoted|handed|was|am|"
              r"watched|filed|knew|know|asked|said|mentioned|added|contrasted|found|recalled|wrote|reported|says|states)")


def canon_name(raw):
    """Canonical person name: capitalised, initial expanded to the known first name."""
    first, last = raw.split(" ", 1)
    first = first[0].upper() + first[1:].lower() if len(first) > 1 else first.upper()
    if first.endswith("."):
        first = INITIAL.get(first[0], first)
    return first + " " + last[0].upper() + last[1:]


def org_name(raw):
    return "Organization " + re.search(r"\d+", raw).group()


SUBJ_TOKEN = r"(?:%s|I|He|She|Org(?:anization)? \d+|org(?:anization)? \d+|Youth \d+|Y\d{3}|[Tt]he community roster)" % NAME


def strip_open(clause):
    """Split a clause into (opener_text, rest) where rest starts at the subject (or at the roster phrase)."""
    t = clause.strip()
    for m in re.finditer(r"(?=%s[ ,])" % SUBJ_TOKEN, t):
        i = m.start()
        if i and t[i - 1] not in " " + Q + ",:'":
            continue
        pre = t[:i]
        if re.match(r"(?:I|He|She|They) %s\b" % NARR_VERBS, t[i:]):
            continue
        if re.fullmatch(r"[\s%s]*" % Q, pre) or re.search(
                r"(?:[,:;]|\b(?:%s)|\b(?:I|He|She|They) %s)\s*[%s]?\s*(?:(?:while|and|but)\s+)?$" % (START_WORDS, NARR_VERBS, Q),
                pre, re.I):
            return pre, t[i:]
    return None, t


W = r"[A-Za-z][\w'-]*(?: [A-Za-z][\w'-]*){0,3}?"          # a short slot of words (lazy)
_STOP = (r"(?:during|in|at|with|to|after|before|for|on|every|last|more|now|still|regularly|and|which|where|as|so|because|"
         r"while|when|that|once|again|today|recently|previously|often|sometimes|since|but|though|only|some|a|an|too|used|instead|"
         r"afterward|afterwards|we|he|she|they|it|I|is|was|who|has|have|had|can|will|always|his|her|their|our|my|also|even|"
         r"just|there|here|nearby|later|together)\b")
WG = r"(?:(?!%s)[A-Za-z][\w'-]*)(?: (?!%s)[A-Za-z][\w'-]*){0,3}" % (_STOP, _STOP)   # greedy slot that stops at tail words
TAIL = r"(?P<tail>[,;]? .+)?"
TITLE_SMALL = {"of", "the", "a", "an", "and", "in"}
TITLES = {t.lower(): t for t in ["Atlas of Clouds", "Quiet Machines", "The Long Orchard", "Copper Harbor"]}


def title_case(s):
    ws = s.split()
    return " ".join(w if (i and w.lower() in TITLE_SMALL) else w[0].upper() + w[1:].lower() for i, w in enumerate(ws))


def topic(raw):
    """Canonical object for a discussed/recommended thing: a known book title, else the lower-case phrase."""
    t = raw.strip()
    low = re.sub(r"^the (?!long orchard)", "", t.lower())
    if low == "long orchard":
        low = "the long orchard"
    if low in TITLES:
        return TITLES[low]
    if t[:1].isupper() and not t.lower().startswith("the "):
        return title_case(t) if len(t.split()) > 1 else t
    return low


def v(stem):
    return stem + r"(?:s|es)?"


def opener_quals(pre, rest):
    quals = []
    if re.search("[%s]" % Q, pre):
        quals.append("quoted")
    if REPORT_WORDS.search(pre):
        quals.append("reported")
    for h in HEDGE_WORDS.findall(pre):
        quals.append("hedged: " + h.lower())
    return quals


def tail_quals(tail):
    out = []
    for m in TAIL_Q.finditer(tail or ""):
        q = m.group(1).lower()
        if q not in out:
            out.append(q)
    return out


_REGISTRY = []


def _parse_as_speaker(speaker, text):
    """Parse a further first-person statement of the same speaker with every rule of the library; None if not exactly one reading."""
    if not speaker:
        return None
    who = speaker if not speaker.startswith("Youth") else speaker
    clause = '%s said, "%s' % (who, text)
    readings = {}
    for cls in _REGISTRY:
        if issubclass(cls, NoFactRule) and not getattr(cls, "__abstractmethods__", None) and cls().parse(text) == []:
            return []
        if getattr(cls, "__abstractmethods__", None):
            continue
        r = cls().parse(clause)
        if r is not None:
            readings[json.dumps(r, sort_keys=True)] = r
    if len(readings) != 1:
        return None
    return list(readings.values())[0]


class ClauseRule(Rule):
    """A rule on one clause: [opener] SUBJECT PREDICATE [tail], with opener and tail turned into qualifiers.

    Subclasses set `subject` ("person", "org", "youth", "roster", "any") and `pred` (regex for the text after the
    subject; a `(?P<tail>..)` group is appended and read for time / frequency / negation words) and implement build().
    """
    subject = "person"
    pred = ""
    tail = TAIL

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        _REGISTRY.append(cls)

    def prepare(self, clause):
        pre, rest = strip_open(clause)
        if pre is None:
            return None
        quals = opener_quals(pre, rest)
        rest = rest.strip()
        # trailing closing quote and attribution: '..." the speaker noted.'
        am = re.search(r"[.,]?[%s]\s*(?:,? ?(?:the |a )?[\w ]{0,40}?%s\b)?[.,]?$" % (Q, SPEECH), rest)
        if am:
            rest = rest[:am.start()]
            if "quoted" not in quals:
                quals.append("quoted")
        rest = rest.rstrip(" .,;")
        speaker = None
        # "NAME said, "I ..." / "NAME said he ...": the speaker is the subject of the reported statement
        sm = re.match(r"(%s|Y\d{3}|Youth \d+) %s,? [%s]?(?=I |[Tt]he community roster (?:records|lists) me )" % (NAME, SPEECH, Q), rest)
        if sm:
            speaker = canon_name(sm.group(1)) if re.fullmatch(NAME, sm.group(1)) else "Youth " + re.search(r"\d+", sm.group(1)).group()
            rest = rest[sm.end():]
            quals += ["quoted", "said"]
        else:
            sm = re.match(r"(%s) %s(?: that)?,? [%s]?%s " % (NAME, SPEECH, Q, PRON), rest)
            if sm:
                rest = sm.group(1) + " " + rest[sm.end():]
                quals += ["reported", "said"]
        sm = re.match(r"(?:%s|I) (?:also )?(?:%s|%s)(?: that)?,? [%s]?(?:(?:while|and|but) )?(?=(?:%s|[Oo]rg(?:anization)? \d+|Youth \d+|Y\d{3}|[Tt]he community roster) )" % (NAME, SPEECH, NARR_VERBS, Q, NAME), rest)
        if sm:
            rest = rest[sm.end():]
            quals += ["reported"]
        sm = re.match(r"I, (%s),? " % NAME, rest)
        if sm:
            rest = sm.group(1) + " " + rest[sm.end():]
        elif re.match(r"%s, " % NAME, rest) and pre.strip() == "I,":
            rest = re.sub(r"^(%s), " % NAME, lambda m: m.group(1) + " ", rest)
        rest = re.sub(r"^(%s|I),? (?:meanwhile|on the other hand|however|too),? (?:%s )?(?:%s )?" % (NAME, SPEECH, PRON), lambda m: m.group(1) + " ", rest)
        return quals, rest, speaker, pre

    def parse(self, clause):
        p = self.prepare(clause)
        if not p:
            return None
        quals, rest, speaker, pre = p
        both = re.match(r"(%s) and (%s) both (.*)" % (NAME, NAME), rest)
        if both:   # "A and B both visited the market": the same predicate for two people
            out = []
            for who in (both.group(1), both.group(2)):
                r = self._parse_rest(quals, "%s %s" % (who, both.group(3)), speaker, pre)
                if r is None:
                    return None
                out += r
            return out
        return self._parse_rest(quals, rest, speaker, pre)

    def _parse_rest(self, quals, rest, speaker, pre):
        if self.subject == "roster":
            m = re.fullmatch(r"(?i:the community roster) " + self.pred + self.tail, rest)
            if not m:
                return None
            return self.finish(self.build(speaker, dict(m.groupdict(), _pre=pre)), quals + tail_quals(m.group("tail")))
        sm = re.match(r"(?P<s>%s|I|He|She|Org(?:anization)? \d+|org(?:anization)? \d+|Youth \d+|Y\d{3})(?:,? who)? (?P<p>.*)" % NAME, rest)
        if not sm:
            return None
        raw, pred = sm.group("s"), sm.group("p")
        pred = re.sub(r"^(?:also|then|later|had) ", "", pred)
        if re.fullmatch(NAME, raw):
            kind, subj = "person", canon_name(raw)
        elif raw in ("I", "He", "She"):
            kind, subj = ("youth" if (speaker or "").startswith("Youth") else "person"), (speaker or ("narrator" if raw == "I" else raw))
            if not speaker and raw == "I":
                quals = quals + ["speaker not named"]
        elif raw[0] in "Oo":
            kind, subj = "org", org_name(raw)
        else:
            kind, subj = "youth", "Youth " + re.search(r"\d+", raw).group()
        if self.subject not in ("any", kind):
            return None
        m = re.fullmatch(self.pred + self.tail, pred)
        if not m:
            return None
        tail = m.group("tail") or ""
        more = re.match(r"[,;]? (?:and|but) (I .*)", tail)
        second = []
        if more and raw == "I":      # '"I visited X, and I helped with Y"': one speaker, several statements
            nl = re.fullmatch(r"I no longer (?:do|go)(?: there)?[.,]?", more.group(1))
            if nl:
                quals = quals + ["no longer"]
            else:
                second = _parse_as_speaker(speaker, more.group(1))
                if second is None:
                    return None
            tail = ""
        return self.finish(self.build(subj, dict(m.groupdict(), _pre=pre)), quals + tail_quals(tail)) + second

    def finish(self, facts, quals):
        out = []
        for f in facts:
            f = dict(f)
            f.setdefault("object", "")
            own = list(f.get("qualifiers", []))
            f["qualifiers"] = own + [q for q in quals if q not in own]
            out.append(f)
        return out

    @abstractmethod
    def build(self, subject, g):
        """Return the list of facts (without the qualifiers of opener and tail) for the matched predicate."""


_PERSON = re.compile(NAME + r"|\b(?:%s)\b|Org(?:anization)? \d|P-\d|Youth \d|Y\d{3}" % "|".join(FIRST))


class NoFactRule(Rule):
    """Base of ignore-rules for filler sentences: whole clause matches one of `frames` and names no person or id."""
    ignore = True
    frames = []

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        _REGISTRY.append(cls)

    @abstractmethod
    def describe(self):
        """Why these clauses carry no fact (returns the `solves` text)."""

    def parse(self, clause):
        t = clause.strip().strip(Q).strip()
        if _PERSON.search(t):
            return None
        for rx in self.frames:
            if re.fullmatch(rx, t):
                return []
        return None
