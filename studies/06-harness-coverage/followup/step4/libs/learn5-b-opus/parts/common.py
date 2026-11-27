"""Shared vocabulary and helpers for the community-records grammar (imported by the part files; defines no parts).

A line is cut into sentences and clauses by split_line(). Quoted speech is kept whole (one clause), because the
speaker of 'D. Haddad said, "I helped ... I work the day shift."' must carry over to every sentence inside the quote;
the quoted_speech rule (speech.py) parses the inside with the other rules.

Every other clause has the shape   [opener] [frame] CORE [remark]
  opener  discourse glue with no meaning ("Elsewhere in the note,", "In a separate update,") -> removed; any other
          fronted phrase ("During this-year,", "At the riverside park,") -> qualifier "context=<text>" (+ time words)
  frame   a source or reporter ("A recent personal note mentioned that", "I noticed", "it came up that",
          "Ben Khan said she ...") -> qualifier "reported" (+ "reported_by=<Name>" when a named person speaks, or
          "reported_by=narrator" for the writer's own "I"); "I"/"me"/"he"/"she" in the core then stand for the speaker
  CORE    the template sentence, matched by one TemplateRule subclass
  remark  free elaboration after the core (", which he often brings to events") -> qualifier "remark=<text>", plus
          canonical qualifiers for meaning-changing words in it ("no longer" -> status=former, "every Tuesday" ->
          freq=every tuesday, ...)
"""
import re
from abc import abstractmethod

from gram import Rule

# ---------------------------------------------------------------- entities
_STOP = (r"(?!(?i:the|a|an|it|its|that|this|these|those|which|who|whom|whose|where|when|there|they|them|their|he|"
         r"him|his|she|her|we|us|our|you|your|i|me|my|and|but|so|as|in|on|at|for|to|of|with|is|was|no|not|while|"
         r"whereas|also|then|one|both|each|all|some|many|several|everyone|someone|nobody|nearby|meanwhile|"
         r"[a-z]+ing)\b)")
_W = r"[A-Za-z][a-z]+(?:-[A-Za-z][a-z]+)?"
# A person is written "Nadia Reed", "N. Reed", "nadia reed", "n. reed".
PERSON = r"(?:%s%s|[A-Za-z]\.) %s%s" % (_STOP, _W, _STOP, _W)
YOUTH = r"(?:Y\d{2,4}|[Yy]outh \d{2,4})"
ORG = r"(?:[Oo]rg(?:ani[sz]ation)?\.? \d{1,4})"
PRONOUN = r"(?:I|me|he|she|they|He|She|They)"
PID = r"[Pp]-\d{2,4}"
# Adverbs between subject and verb. Most carry no meaning; previously/recently/still/now become qualifiers.
SUBJ_ADV = (r"(?:,? (?:meanwhile|however|too|also|though|in turn|on the other hand|for (?:her|his|their) part),)?"
            r"(?: (?P<adv>also|simply|too|then|later|indeed|again|meanwhile|still|now|even|similarly|likewise|"
            r"actually|personally|happily|recently|previously|formerly|once|clearly))?"
            r"(?: (?:had|has|have)(?= (?:visited|attended|discussed|recommended|helped|volunteered|worked|used|been|"
            r"traveled|travelled|enjoyed|owned|taken|chosen)\b))?"
            # negation before a base-form verb: 'does not avoid', 'never visited', 'no longer attends'
            r"(?: (?P<sneg>does not|doesn't|did not|didn't|do not|don't|never|no longer))?")
SUBJ = r"(?P<subj>%s|%s|%s|%s)%s" % (PERSON, YOUTH, ORG, PRONOUN, SUBJ_ADV)
_ADV_QUAL = {"recently": ["time=recent"], "previously": ["time=past"], "formerly": ["status=former"],
             "once": ["time=past"], "still": ["status=current"], "now": ["status=current"]}
_NEG_QUAL = {"no longer": ["status=former"]}  # any other negation word -> "neg"
# 'is not' / 'is no longer' before the rest of a core: the core is matched without it, the fact gets neg/former
_IS_NEG = re.compile(r"(?P<head>(?:%s|%s|%s|%s)(?: also| still)? (?:is|am|are|was|were)) (?P<neg>not|no longer|never) "
                     % (PERSON, YOUTH, ORG, PRONOUN))

# Words a predicate can start with; a sentence is only cut before "<subject> <one of these>".
PRED_START = (r"owns?|own|attends?|attend|attended|attending|visited|visit|visiting|went|goes|discussed|discuss|"
              r"discussing|recommended|recommend|recommending|suggested|helped|help|helping|assisted|volunteered|"
              r"currently|works?|worked|used|plans?|planned|routinely|ordinarily|usually|regularly|is|was|likes?|"
              r"genuinely|truly|really|chose|prefers?|took|takes|enjoys?|enjoyed|dislikes?|buys?|serves?|said|says|"
              r"explained|added|mentioned|noted|stated|told|reported|confirmed|previously|formerly|no longer|still|"
              r"travels?|traveled|travelled|commutes?|avoids?|skips?|eats?|teaches|taught|joined|participates|"
              r"participated|records|lists|observed|noticed|recalled|shared|loves?|hates?|talked|spoke|keeps?|"
              r"also|simply|recently|agreed|replied|continued|concluded|has|have|had|volunteers?|volunteer")
_CLAUSE_START = r"(?:(?:the )?community roster\b|I, %s, |(?:%s|%s|%s|I)(?:, [a-z ]+,)? (?:%s)\b)" % (
    PERSON, PERSON, YOUTH, ORG, PRED_START)
CLAUSE_START = re.compile(_CLAUSE_START)


def name_form(s):
    """Canonical written form of a mention: 'nadia reed' -> 'Nadia Reed', 'Youth 9' -> 'Y009', 'org 8' ->
    'Organization 008', 'p-66' -> 'P-066'."""
    s = s.strip()
    if re.fullmatch(YOUTH, s):
        return "Y" + re.search(r"\d+", s).group(0).zfill(3)
    if re.fullmatch(ORG, s):
        return "Organization " + re.search(r"\d+", s).group(0).zfill(3)
    if re.fullmatch(PID, s):
        return "P-" + re.search(r"\d+", s).group(0).zfill(3)
    return " ".join(w[:1].upper() + w[1:].lower() for w in s.split())


def obj_norm(s):
    """Canonical object text: lower case, no leading article or possessive, single spaces."""
    s = re.sub(r"\s+", " ", s.strip().lower())
    return re.sub(r"^(?:the|a|an|some|my|his|her|their|our) ", "", s)


# ---------------------------------------------------------------- splitting
# End of a sentence: . ! or ? (optionally followed by a closing quote) before white space or the end.
_SENT_END = re.compile(r"[.!?][\"”']?(?=\s|$)")
# "." that is not a sentence end: a one-letter initial ("N. Reed") or an abbreviation ("St. John's").
_NOT_END = re.compile(r"(?:^|[\s\"“(])(?:[A-Za-z]|St|Mt|Dr|Mr|Ms|Mrs|Prof|Jr|Sr|vs|etc|approx|No)$")
# Connector between two clauses of one sentence; a cut is made only where a new clause starts after it.
CONNECTOR = re.compile(r"(?:\s*[,;:]\s*(?:(?:and that|but that|and then|and also|but also|and|but|while|whereas|so|yet)\s+)?"
                       r"|\s+(?:and|but|while|whereas|and then)\s+)")
DROPPABLE = [r"[,;:]?\s*(?:and|but|while|whereas|so|yet|and then|and also|but also|and that|but that)"]


def quote_mask(line):
    """For each position, True if it lies inside a quotation (an unclosed quote runs to the end of the line)."""
    mask, inside = [], False
    for ch in line:
        if ch == "“":
            inside = True
            mask.append(True)
            continue
        if ch == "”":
            mask.append(True)
            inside = False
            continue
        if ch == '"':
            mask.append(True)
            inside = not inside
            continue
        mask.append(inside)
    return mask


def split_sentences(line):
    mask = quote_mask(line)
    sents, start = [], 0
    for m in _SENT_END.finditer(line):
        i, e = m.start(), m.end()
        if line[i] == "." and _NOT_END.search(line[start:i]):
            continue
        if e < len(line) and mask[e]:
            continue  # inside a quotation
        sents.append(line[start:e].strip())
        start = e
    if line[start:].strip():
        sents.append(line[start:].strip())
    return [s for s in sents if s]


def split_clauses(sent):
    mask = quote_mask(sent)
    out, pos = [], 0
    for m in CONNECTOR.finditer(sent):
        a, b = m.start(), m.end()
        if a == 0 or b >= len(sent) or a < pos or mask[a] or mask[b]:
            continue
        if not CLAUSE_START.match(sent, b) or not CLAUSE_START.search(sent[pos:a]):
            continue  # no new clause here, or the text before is only an opener such as "In a separate update,"
        out.append(sent[pos:a])
        pos = b
    out.append(sent[pos:])
    return [c for c in out if c.strip()]


def split_line(line):
    return [c for s in split_sentences(line) for c in split_clauses(s)]


# ---------------------------------------------------------------- openers and frames
_KNOWN_OPENERS = (r"elsewhere in the note|in a separate update|unrelatedly|meanwhile|in contrast|by contrast|"
                  r"additionally|also|separately|in addition|furthermore|moreover|similarly|likewise|on another note|"
                  r"on a different note|in other news|later|later on|however|then|finally|lastly|next|besides|"
                  r"otherwise|in turn|as well|nearby|on the other hand|at the same time|in the same note|"
                  r"for (?:his|her|their) part|by the way|incidentally|notably|interestingly")
# Known discourse glue, removed without a qualifier (comma optional for the one-word ones).
OPENER_RX = re.compile(r"(?:%s)\s*,\s*|(?:then|also|meanwhile|later|next|finally|separately|nearby|likewise|"
                       r"similarly|besides)\s+(?=%s)" % (_KNOWN_OPENERS, _CLAUSE_START), re.I)
# Any other fronted phrase before a clause: kept as context ("During this-year,", "At the riverside park,").
CONTEXT_RX = re.compile(r"(?P<ctx>[^,\"“”:]{2,90}?)\s*,\s*(?=%s|(?:it|I|we|he|she|they) |according to |"
                        r"(?:the|a|an|our|my|one) [a-z' -]{1,40}? (?:explained|noted|said|mentioned|stated|added|"
                        r"reported|recorded|observed|shared|confirmed|wrote|notes|says|states|records|mentions))"
                        % _CLAUSE_START)
# Continuation of the passage's own source ("The same account also says that"): no qualifier.
CONTINUE_RX = re.compile(r"the same (?:account|note|record|report|log|source|entry|profile) (?:also )?[a-z]+ that\s+",
                         re.I)
REPORT_VERB = (r"(?:said|says|say|noted|notes|note|mentioned|mentions|mention|stated|states|state|explained|"
               r"explains|explain|added|adds|add|reported|reports|report|recorded|records|observed|observes|"
               r"noticed|notices|confirmed|confirms|confirm|wrote|writes|shared|shares|recalled|recalls|indicated|"
               r"indicates|highlighted|highlights|showed|shows|remarked|remarks|clarified|clarifies|"
               r"pointed out|points out|claimed|claims|recounted|recounts|continued|continues|concluded|concludes|"
               r"told us|tells us|told me|tells me|lists|listed|described|describes|admitted|admits|insisted|"
               r"insists|replied|replies|answered|answers|commented|comments|announced|announces|agreed|agrees|"
               r"was told|heard|learned|contrasted|emphasized|stressed|joked|laughed|recalled|"
               r"mentioned in passing|went on|chimed in)")
_PERCEIVE = (r"(?:observed|noticed|saw|watched|remember|remembered|heard|recall|recalled|noted|learned|found|"
             r"realized|mentioned|stated|explained|said|added|wrote|recorded|was told|confirmed|reported|"
             r"can confirm|believe|know|knew|think)")
# 'I, Ben Khan, helped ...' -> subject Ben Khan, speaking about themself.
I_APPOS_RX = re.compile(r"I, (?P<src>%s), (?=(?:%s)\b)" % (PERSON, PRED_START))
# 'I, Ben Khan, can confirm (that) ...'
CONFIRM_RX = re.compile(r"I, (?P<src>%s), (?:can |would like to |want to |must )?%s(?: that)?\s+"
                        % (PERSON, REPORT_VERB), re.I)
# 'it came up that', 'it was noted that', 'It reminded me that'
IMPERSONAL_RX = re.compile(r"it (?:was |has been |had been |is )?(?:also )?(?:noted|mentioned|reported|said|observed|"
                           r"recorded|confirmed|shared|added|stated|came up|emerged|turned out|reminded (?:me|us)|"
                           r"was clear|appears|seems)(?: [a-z ]{0,30}?)? that\s+", re.I)
ACCORDING_RX = re.compile(r"according to (?P<src>%s|the [a-z ]{1,40}?|[a-z]+),\s*" % PERSON, re.I)
# 'I noticed ...', 'He also mentioned that ...', 'I remember ...'
PERCEIVE_RX = re.compile(r"(?P<src>I|we|he|she|they)(?: also| later| then)? %s(?: that| how)?\s+(?=%s)"
                         % (_PERCEIVE, _CLAUSE_START), re.I)
# 'Ben Khan said she ...', 'Ben Khan noted that M. Reed ...', 'A recent personal note mentioned that ...'
_SRC = (r"(?:%s|%s|I|we|(?:the|a|an|our|this|that|my|one) [a-z' -]{1,60}?|[A-Za-z][a-z]+(?: [a-z]+){0,4}?)"
        % (PERSON, YOUTH))
REPORT_RX = re.compile(r"(?!(?:the )?community roster)(?P<src>%s)(?:, [a-z ]+,)? (?:also |then |later )?%s"
                       r"(?: [a-z' ]{1,40}?)?(?: that\s+|,\s+|\s+(?=(?:he|she|they|I) )|\s+(?=%s))"
                       % (_SRC, REPORT_VERB, _CLAUSE_START), re.I)
# 'The club newsletter states o. tran ...', 'My meeting notes record j. diaz ...'
DOC_RX = re.compile(r"(?!(?:the )?community roster)(?:the|this|my|our|a|an|one) [\w' -]{1,60}? (?:notes?|records?|shows?|states?|noted|mentions?|"
                    r"lists?|recorded|stated|showed|says|said|contrasted|confirms?|confirmed|indicates?|indicated|"
                    r"reports?|reported|explains?|explained|adds?|added|lists?)(?: that)?\s+(?=%s)"
                    % _CLAUSE_START, re.I)
# 'I handed off the notes: Farah Patel ...'
COLON_RX = re.compile(r"(?P<ctx>[^:\"“”]{2,100}):\s+(?=%s)" % _CLAUSE_START)
# 'I was filing a travel reimbursement when Priya Jones ...', 'I filed the reimbursement after noting that ...'
NARRATIVE_RX = re.compile(r"(?P<ctx>(?:I|we)\b[^\"“”]{2,120}?) (?:when|after|before|while|as|because|since|and)"
                          r"(?: (?:I |we )?(?:remembered|noticed|noted|noting|saw|recalled|realized|heard|learned|"
                          r"remembering|seeing|hearing|learning)(?: that)?)?\s+(?=%s)" % _CLAUSE_START)
# 'Ben Khan, who currently works for Org 8, mentioned it during our chat.'
APPOSITIVE_RX = re.compile(r"(?P<subj>%s), who (?P<pred>[^,]+),\s*(?P<rest>.+)" % PERSON)
# 'S. Laurent, who helped with registration at the riverside park' (inside a remark) -> 'S. Laurent helped ...'
WHO_RX = re.compile(r"(?P<subj>%s), who (?P<pred>[^,]+)" % PERSON)
# 'That is different from Quinn Tran, who visited the market.' -> 'Quinn Tran visited the market'
COMPARE_RX = re.compile(r"[^,\"“”]{0,60}?\b(?:from|unlike|like|than|with|as|to) (?P<subj>%s), who (?P<pred>.+)"
                        % PERSON)
# a named subject followed by a predicate: such a clause has no frame in front of it
_STARTS_CLAUSE = re.compile(r"(?:%s|%s|%s)%s (?:%s)\b" % (PERSON, YOUTH, ORG, SUBJ_ADV, PRED_START))
_STARTS_REPORT = re.compile(r"%s(?:, [a-z ]+,)? (?:also |then |later )?%s\b" % (_SRC, REPORT_VERB), re.I)
# any subject, pronouns included, followed by a predicate
_STARTS_ANY = re.compile(r"%s (?:%s)\b" % (SUBJ, PRED_START))


def strip_end(s):
    s = re.sub(r"^[\s\"“”']+", "", s)
    return re.sub(r"[\s.!?\"“”']+$", "", s)


def _source(src, quals, speaker):
    """Record a source; return the new speaker (a named person, the narrator 'I', or the previous speaker)."""
    if "reported" not in quals:
        quals.append("reported")
    if re.fullmatch(PERSON, src) or re.fullmatch(YOUTH, src):
        quals.append("reported_by=" + name_form(src))
        return name_form(src)
    if src.lower() == "i" and speaker is None:
        quals.append("reported_by=narrator")
    return speaker


def context_quals(text):
    """Qualifiers for a fronted context phrase."""
    q = ["context=" + text.strip()]
    q += [t for t in keyword_quals(text) if not t.startswith("remark_negated")]
    return q


def peel(clause, speaker=None):
    """Strip openers and frames off a clause. Returns (core, qualifiers, speaker or None, [context texts])."""
    s = strip_end(clause.strip())
    quals, ctx = [], []
    for _ in range(10):
        before = s
        m = OPENER_RX.match(s)
        if m and m.end() < len(s):
            s = s[m.end():]
            continue
        m = CONTINUE_RX.match(s)
        if m:
            s = s[m.end():]
            continue
        m = I_APPOS_RX.match(s)
        if m:
            speaker = _source(m.group("src"), quals, speaker)
            s = m.group("src") + " " + s[m.end():]
            continue
        m = CONFIRM_RX.match(s)
        if m:
            speaker = _source(m.group("src"), quals, speaker)
            s = s[m.end():]
            continue
        m = IMPERSONAL_RX.match(s) or ACCORDING_RX.match(s)
        if m:
            quals.append("reported") if "reported" not in quals else None
            s = s[m.end():]
            continue
        m = PERCEIVE_RX.match(s)
        if m:
            speaker = _source(m.group("src"), quals, speaker)
            s = s[m.end():]
            continue
        m = REPORT_RX.match(s)
        # "<person> <ordinary verb> ..." is a clause, not a frame, unless that verb is a speech verb
        if m and (not _STARTS_CLAUSE.match(s) or _STARTS_REPORT.match(s)):
            speaker = _source(m.group("src"), quals, speaker)
            s = s[m.end():]
            continue
        m = DOC_RX.match(s)
        if m and not _STARTS_CLAUSE.match(s):
            quals.append("reported") if "reported" not in quals else None
            s = s[m.end():]
            continue
        m = COLON_RX.match(s) or NARRATIVE_RX.match(s)
        if m and not _STARTS_CLAUSE.match(s):
            quals.append("reported") if "reported" not in quals else None
            if m.group("ctx").split()[0].lower() == "i" and speaker is None:
                quals.append("reported_by=narrator")
            ctx.append(m.group("ctx"))
            quals += context_quals(m.group("ctx"))
            s = s[m.end():]
            continue
        m = APPOSITIVE_RX.fullmatch(s)
        if m:
            s = "%s %s, %s" % (m.group("subj"), m.group("pred"), m.group("rest"))
            continue
        m = CONTEXT_RX.match(s)
        if m and not _STARTS_ANY.match(s):
            ctx.append(m.group("ctx"))
            quals += context_quals(m.group("ctx"))
            s = s[m.end():]
            continue
        m = WHO_RX.fullmatch(s)
        if m:
            s = "%s %s" % (m.group("subj"), m.group("pred"))
            continue
        m = COMPARE_RX.fullmatch(s)
        if m and not _STARTS_CLAUSE.match(s):
            s = "%s %s" % (m.group("subj"), m.group("pred"))
        if s == before:
            break
    return strip_end(s), list(dict.fromkeys(quals)), speaker, ctx


# ---------------------------------------------------------------- remarks after the core
REMARK_START = (r"which|who|whom|whose|where|when|that|to|for|with|during|in|on|at|as|and|but|so|because|since|"
                r"after|before|while|every|each|last|this|next|recently|regularly|often|usually|occasionally|"
                r"sometimes|nearby|again|together|too|also|though|although|despite|from|by|about|around|near|"
                r"along|over|under|into|until|without|whenever|weekly|daily|monthly|then|now|still|once|twice|"
                r"lately|yesterday|today|earlier|afterwards|later|alone|herself|himself|themselves|"
                r"there|here|almost|always|frequently|rarely|seldom|happily|eagerly|enthusiastically|"
                r"personally|first|just|quite|very|really|both|one|some|having|being|showing|highlighting|"
                r"ensuring|adding|offering|sharing|making|bringing|helping|managing|leading|giving|providing|"
                r"keeping|taking|noting|explaining|saying|mentioning|including|like|unlike|even|only|"
                r"probably|perhaps|maybe|possibly|most|how|what|why|whether|previously|instead|afterward|afterwards|more|"
                r"ago|a|an|the|it|its|he|she|they|his|her|their|we|our|i|my")
_REST_RX = re.compile(r"(?:\s*,\s*|\s*;\s*|\s+(?=(?:%s)\b)|\s*[\-–—]+\s*|\s*\(\s*)(?P<remark>.+)" % REMARK_START, re.I)

_FORMER = re.compile(r"\b(?:no longer|not anymore|any ?more|has since ended|since ended|ended|former|formerly|"
                     r"in the past|previously|not a member now|stopped|quit|discontinued|gave up|"
                     r"not currently|past)\b", re.I)
_FREQ = re.compile(r"\b(?:every (?:other )?(?:day|week|weekend|month|year|morning|evening|night|"
                   r"(?:mon|tues|wednes|thurs|fri|satur|sun)day)s?|on (?:mon|tues|wednes|thurs|fri|satur|sun)days|"
                   r"most (?:weekdays|days|weeks|mornings|evenings)|weekly|daily|monthly|regularly|often|usually|"
                   r"routinely|occasionally|frequently|sometimes|rarely|seldom|once|twice|always|never)\b", re.I)
_TIME = re.compile(r"\b(?:this[- ]year|last[- ]year|next[- ]year|this week|last week|next week|this month|"
                   r"last month|recently|lately|yesterday|today|in the future|soon|tomorrow)\b", re.I)
_NEG = re.compile(r"\b(?:not|never|no|nobody|nothing|neither|nor)\b|n't\b", re.I)


def keyword_quals(text):
    q = []
    if _FORMER.search(text):
        q.append("status=former")
    for f in _FREQ.finditer(text):
        q.append("freq=" + f.group(0).lower())
    for t in _TIME.finditer(text):
        q.append("time=" + t.group(0).lower().replace(" ", "_").replace("-", "_"))
    if _NEG.search(text) and "status=former" not in q:
        q.append("remark_negated")
    return q


def remark_text(rest):
    """The remark after a core ("" if none), or None if that text cannot be a remark."""
    if not rest.strip(" ,;"):
        return ""
    m = _REST_RX.fullmatch(rest)
    if not m:
        return None
    return strip_end(m.group("remark")).strip(" ,;)")


_BARE_CONNECTOR = re.compile(r"(?:and|but|while|whereas|so|yet|then|in contrast to|unlike|compared to|compared with|"
                             r"as well as|just like|like|than|along with)", re.I)


def remark_quals(text):
    if not text or _BARE_CONNECTOR.fullmatch(text):
        return []  # only the connector in front of an embedded clause is left
    return ["remark=" + text] + keyword_quals(text)


# Inside a remark, a clause about a written name ("noting that A. Evans attends the walking group") is parsed too.
_STRICT_NAME = r"(?:[A-Z][a-z]+ [A-Z][a-z]+|[A-Za-z]\. [A-Za-z][a-z]+)"
_NAMED_CLAUSE = re.compile(r"\b(?:%s|%s|%s)(?:,? and %s)?(?: (?:also|still|now|too|had|has|both|each))? (?:%s)\b"
                           r"|\b%s, who (?:%s)\b" % (_STRICT_NAME, YOUTH, ORG, _STRICT_NAME, PRED_START, _STRICT_NAME,
                                                     PRED_START))
# 'P. Khan and G. Ito both visited the market' -> one clause per person
_COMPOUND = re.compile(r"(?P<a>%s),? and (?P<b>%s)(?: both| each| also| too)? (?P<rest>(?:%s)\b.*)"
                       % (PERSON, PERSON, PRED_START))
# '..., and discussed radio society' / '... and then visited the museum': a second predicate for the same subject
_COORD = re.compile(r"(?:and|but|and then|then|and also|but also|before|after) (?P<pred>(?:%s)\b.*)" % PRED_START)
# '..., which L. Evans recommended': the same object, another subject
_WHICH = re.compile(r"which (?P<who>%s) (?P<verb>[a-z]+)(?P<tail>(?:[ ,].*)?)" % _STRICT_NAME)


def parse_any(clause, speaker=None, outer_quals=()):
    """Facts for a clause from whichever template rule parses it; None unless exactly one distinct reading."""
    got = {}
    for r in template_rules():
        f = r.parse_in(clause, speaker, outer_quals)
        if f is not None:
            got[repr(f)] = f
    return next(iter(got.values())) if len(got) == 1 else None


# ---------------------------------------------------------------- slot patterns for rule cores
# A free object (item, title, topic, place): 1-5 words, none of which can start a remark, so "discussed market
# trends with the team" gives the object "market trends" and the remark "with the team".
_OW = r"(?!(?:%s)\b)[A-Za-z][\w'-]*" % REMARK_START
OBJ = r"(?P<obj>%s(?: %s){0,4})" % (_OW, _OW)
ART = r"(?:(?:the|a|an|some|my|his|her|their|our) )?"


# ---------------------------------------------------------------- base rule
class TemplateRule(Rule):
    """A rule for one family of core templates. Subclasses set `cores` (regexes over the core, each with a
    (?P<subj>) group; a core must match a prefix of the clause and the rest must be a remark) and implement
    make(groups) -> list of (relation, object, [qualifiers]) or None. Clauses with quotation marks are left to the
    quoted_speech rule, which calls parse_in() with the speaker. Abstract: defines no part itself."""
    cores = []
    _compiled = None

    @abstractmethod
    def make(self, g):
        """Facts for a matched core, as (relation, object, qualifiers) triples; None to decline. g["_ctx"] holds the
        clause's fronted context phrases."""

    def parse(self, clause):
        if re.search(r"[\"“”]", clause):
            return None
        return self.parse_in(clause)

    def parse_in(self, clause, speaker=None, outer_quals=()):
        if type(self)._compiled is None:
            type(self)._compiled = [re.compile(c, re.I) for c in self.cores]
        core, quals, speaker, ctx = peel(clause, speaker)
        c = _COMPOUND.fullmatch(core)
        if c:
            q = list(outer_quals) + quals
            fa, fb = (self.parse_in(c.group(x) + " " + c.group("rest"), speaker, q) for x in ("a", "b"))
            return fa + fb if fa is not None and fb is not None else None
        negq = []
        n = _IS_NEG.match(core)
        if n:
            core, negq = n.group("head") + " " + core[n.end():], _NEG_QUAL.get(n.group("neg").lower(), ["neg"])
        for rx in self._compiled:
            for m in _prefix_matches(rx, core):
                text = remark_text(core[m.end():])
                if text is None:
                    continue
                g = {k: (v or "") for k, v in m.groupdict().items()}
                subj = resolve_subject(g.get("subj", ""), speaker)
                if subj is None:
                    continue
                g["_ctx"] = ctx
                made = self.make(g)
                if made is None:
                    continue
                text, nested = self._nested(text, m, speaker, list(outer_quals) + quals)
                if nested is None:
                    continue
                rq = remark_quals(text)
                adv = _ADV_QUAL.get(g.get("adv", "").lower(), []) + negq
                if g.get("sneg"):
                    adv = adv + _NEG_QUAL.get(g["sneg"].lower(), ["neg"])
                return [{"subject": subj, "relation": rel, "object": obj,
                         "qualifiers": list(dict.fromkeys(q + adv + list(outer_quals) + quals + rq))}
                        for rel, obj, q in made] + nested
        return None

    def _nested(self, text, m, speaker, quals):
        """Split clauses hidden in a remark off it. Returns (remaining remark text, nested facts) or (text, None)
        when the remark holds a clause that cannot be parsed."""
        if not text:
            return text, []
        c = _COORD.fullmatch(text)
        if c:  # same subject, second predicate
            f = parse_any(m.group("subj") + " " + c.group("pred"), speaker, quals)
            if f is not None:
                return "", f
        w = _WHICH.fullmatch(text)
        if w and "obj" in m.groupdict() and m.group("obj"):  # same object, another subject
            f = parse_any("%s %s %s%s" % (w.group("who"), w.group("verb"), m.group("obj"), w.group("tail")),
                          speaker, quals)
            if f is not None:
                return "", [dict(x, qualifiers=list(dict.fromkeys(x["qualifiers"] + ["embedded"]))) for x in f]
        n = _NAMED_CLAUSE.search(text)
        if not n:
            return text, []
        f = parse_any(text[n.start():], speaker, quals)
        if f is None:
            return text, None
        return text[:n.start()].strip(" ,;"), [dict(x, qualifiers=list(dict.fromkeys(x["qualifiers"] + ["embedded"])))
                                              for x in f]


def _prefix_matches(rx, s):
    """Matches of rx over a prefix of s ending before a space/comma/bracket (or over all of s), longest first."""
    out = []
    m = rx.fullmatch(s)
    if m:
        out.append(m)
    for i in range(len(s) - 1, 0, -1):
        if s[i] in " ,;(-–—" and s[i - 1] != " ":
            m = rx.fullmatch(s, 0, i)
            if m:
                out.append(m)
    return out


def resolve_subject(subj, speaker):
    if not subj:
        return None
    if re.fullmatch(PRONOUN, subj):
        return speaker if speaker and speaker != "narrator" else None
    return name_form(subj)


def template_rules():
    """One instance of every TemplateRule subclass loaded in this library."""
    seen, out, todo = set(), [], list(TemplateRule.__subclasses__())
    while todo:
        c = todo.pop(0)
        todo.extend(c.__subclasses__())
        if c.name and c.name not in seen and not getattr(c, "__abstractmethods__", None):
            seen.add(c.name)
            out.append(c())
    return out
