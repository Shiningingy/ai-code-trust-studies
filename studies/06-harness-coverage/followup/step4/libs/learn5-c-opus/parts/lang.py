"""Shared grammar engine for the community-records documents (helper module, defines no parts).

A clause is read as
    [opener]* SUBJECT VP (" and " VP)* [modifiers] [tail]
- opener: discourse connectors ("In a separate update,") that carry no meaning, or evidential frames
  ("A recent personal note mentioned that", "Kofi Silva noted that") that become `source:` / `reported_by:` qualifiers
- SUBJECT: a person name (full "Nadia Reed" or initial "N. Reed", any case), "I" (speaker, or "narrator"), a pronoun,
  an organization ("Org 013"), a youth ("Youth 043" / "Y043"), or a roster entry ("the community roster records NAME")
- VP: one predicate from the registry; each family file in parts/ registers its predicates with `register`
- modifiers: time / frequency phrases (kept as qualifiers) and plain prepositional phrases ("to the group", dropped)
- tail: free commentary after a comma or "which/that/so/..." ("which he often brings to our events"). It carries no
  fact, except: past markers ("though only in the past", "but she no longer does") become status:former on stative
  relations, and embedded clauses about another named person ("in contrast to F. Patel, who visited the museum") are
  parsed as extra facts.
Quoted speech is handled by `parse_speech`.
"""
import re

# ---------------------------------------------------------------- names and entities

STOP = ("the|this|that|these|those|it|its|he|she|they|we|i|you|me|us|him|them|a|an|our|my|his|her|their|your|also|then|during|in|"
        "on|at|for|of|and|but|while|whereas|so|as|one|each|every|some|any|no|not|there|here|what|when|where|who|which|"
        "how|both|all|elsewhere|unrelatedly|meanwhile|later|earlier|org|organization|youth|after|before|according|"
        "with|from|to|by|unlike|except|everyone|everything|someone|nobody|people|is|was|were|are|has|had|have|did|do|"
        "does|said|says|owns|own|recommended|discussed|attends|visited|helped|volunteered|works|work|used|plans|took|"
        "currently|routinely|genuinely|likes|chose|buys|dislikes|enjoys|serves|noted|mentioned|explained|added|"
        "observed|recorded|stated|shows|records|notes|only|again|too|well|now|today|yesterday|recently|previously|"
        "community|team|club|group|record|note|newsletter|bulletin|speaker|observer|account|roster|interview|"
        "meeting|event|travel|local|volunteer|appointment|handoff|reimbursement|shift|chat|profile|administrative|"
        "direct|quoted|reported|report|log|entry|entries|details|updates|several|few|other|another|unrelated")
_TOK1 = r"(?:[A-Za-z]\.|[A-Za-z][a-z][A-Za-z'-]*)"
_TOK2 = r"[A-Za-z][A-Za-z'-]*[a-z]"
NAME = r"(?!(?i:(?:%s)) )%s (?!(?i:(?:%s))\b)%s" % (STOP, _TOK1, STOP, _TOK2)
NAME_RX = re.compile(NAME)
ORG = r"(?:[Oo]rg|[Oo]rganization) \d+"
YOUTH = r"(?:[Yy]outh \d+|[Yy]\d+)"
PRONOUNS = {"he", "she", "they"}


def canon_name(s):
    """'elena jones' / 'c. Patel' -> 'Elena Jones' / 'C. Patel'."""
    out = []
    for w in s.split():
        out.append("-".join(p[:1].upper() + p[1:] for p in w.split("-")))
    return " ".join(out)


def canon_org(s):
    return "Org " + "%03d" % int(re.search(r"\d+", s).group())


def canon_youth(s):
    return "Y" + "%03d" % int(re.search(r"\d+", s).group())


def canon_obj(s):
    """Objects (places, items, books, foods, topics): lower case, leading article removed."""
    s = re.sub(r"\s+", " ", s.strip().lower())
    return re.sub(r"^(?:(?:the|a|an) )?(?:(?:set|pair|collection) of )?(?:(?:the|a|an) )?", "", s)


ENTITY_RX = re.compile(r"\b(?:[A-Z][a-z]+ [A-Z][a-z]+|[A-Z]\. [A-Z][a-z]+)\b|(?i:\bp-\d|\b%s\b|\b%s\b|event-)"
                       % (ORG, YOUTH))

# ---------------------------------------------------------------- modifiers

DAYS = r"(?i:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
TIME = [r"some time ago", r"a while ago", r"long ago", r"also only in the past", r"only in the past", r"in the past",
        r"previously", r"formerly", r"more recently", r"recently", r"earlier(?: that day| today| this week)?",
        r"later(?: that (?:day|afternoon|evening|week|morning))?", r"that same (?:day|afternoon|evening|week|morning)",
        r"yesterday", r"today", r"this (?:morning|afternoon|evening|week|weekend|month|year)",
        r"last (?:week|weekend|month|year|night|spring|summer|fall|winter)", r"on (?:a )?%s" % DAYS,
        r"on (?:her|his|their|my|our) day off", r"in the (?:morning|afternoon|evening)",
        r"(?:before|after) the [a-z ]+", r"in a former role", r"in the future", r"now", r"at the moment",
        r"these days", r"most weekdays", r"once", r"twice", r"not recently"]
FREQ = [r"regularly", r"routinely",
        r"every (?:day|week|month|morning|evening|weekend|%s)(?: (?:morning|afternoon|evening|night))?" % DAYS,
        r"daily", r"weekly", r"often", r"sometimes", r"usually", r"occasionally", r"again",
        r"on (?:the )?weekends?", r"on %ss" % DAYS]
_PP_WORD = r"(?:[a-z0-9][a-z0-9'-]*|%s)" % NAME
MISC = [r"too", r"as well", r"also", r"nearby", r"together", r"instead", r"there", r"first", r"afterwards?",
        r"(?:to|with|for|during|in|at|from|as|on|near|about|around|into|after|before|over|without) "
        r"%s(?: %s){0,9}" % (_PP_WORD, _PP_WORD)]
TIME_RX = re.compile(r"\b(?:%s)\b" % "|".join(TIME))
FREQ_RX = re.compile(r"\b(?:%s)\b" % "|".join(FREQ))
M = r"(?P<mods>(?: (?:%s))*)" % "|".join(TIME + FREQ + MISC)
PAST_RX = re.compile(r"\b(?:only in the past|in the past|previously|formerly|in a former role|no longer|"
                     r"not a member|used to|has since (?:lapsed|ended|faded|left|stopped)|former (?:role|activity|membership)|"
                     r"not anymore|any ?more|having (?:left|stopped|quit)|stopped (?:going|attending))\b")


def mod_quals(mods, stative):
    """Qualifiers from a modifier string: when:/freq: phrases, and status:former for past markers on states."""
    q = []
    if not mods:
        return q
    for m in TIME_RX.finditer(mods):
        p = m.group().lower()
        if p in ("only in the past", "also only in the past", "in a former role"):
            q.append("status:former")
        elif p in ("once", "twice"):
            q.append("freq:" + p)
        elif p in ("now", "at the moment", "these days"):
            q.append("status:current")
        elif p == "in the future":
            q.append("status:planned")
        elif stative and p in ("in the past", "previously", "formerly"):
            q.append("status:former")
        else:
            q.append("when:" + p)
    for m in FREQ_RX.finditer(mods):
        q.append("freq:" + m.group().lower())
    return q


# ---------------------------------------------------------------- predicate registry

_OBJ_STOP = (r"(?:and|which|that|who|where|but|while|so|because|when|though|whereas|whom|whose|we|i|he|she|they|"
             r"used|is|was|were)")
OBJ = r"(?P<obj>[A-Za-z0-9][\w'.-]*(?: (?!%s\b)[\w'.-]+){0,6}?)" % _OBJ_STOP


class Pred:
    def __init__(self, family, pattern, build, subj=("person",), stative=False):
        self.family, self.build, self.subj, self.stative = family, build, subj, stative
        self.rx = re.compile(pattern.replace("{O}", OBJ).replace("{M}", M).replace("{NAME}", NAME)
                             .replace("{ORG}", ORG).replace("{YOUTH}", YOUTH))


REGISTRY = []


def register(family, pattern, build, subj=("person",), stative=False):
    """build(groups, quals) -> list of (relation, object, qualifiers); quals already holds the modifier qualifiers."""
    REGISTRY.append(Pred(family, pattern, build, subj, stative))
    _CACHE.clear()


_NEG = re.compile(r"(?:does not|doesn't|do not|don't|did not|didn't|never|is not|isn't|am not|was not|wasn't) ")


def match_vp(text, stype):
    """(predicate, facts) for a VP; 'does not / never / is not' + VP gives the VP's facts with qualifier neg."""
    m = _NEG.match(text)
    if m:
        r = _match_vp(text[m.end():], stype) or _match_vp("is " + text[m.end():], stype)
        if r:
            return r[0], [(s, rel, obj, q + ["neg"]) for s, rel, obj, q in r[1]]
        return None
    return _match_vp(text, stype)


def _match_vp(text, stype):
    for p in REGISTRY:
        if stype not in p.subj:
            continue
        m = p.rx.fullmatch(text)
        if m:
            g = {k: (v or "") for k, v in m.groupdict().items()}
            facts = p.build(g, mod_quals(g.get("mods", ""), p.stative))
            if facts is not None:
                return p, [f if len(f) == 4 else (None,) + tuple(f) for f in facts]
    return None


_CUT_RX = re.compile(r",|;| (?:and|which|that|who|where|so|while|because|but|though|when|whereas|whom|"
                     r"having|making|ensuring|adding|meaning|used|we|I|he|she|they) ")


def _cuts(s):
    return sorted({len(s)} | {m.start() for m in _CUT_RX.finditer(s)}, reverse=True)


def parse_vp_seq(s, stype):
    """Longest VP first; ' and VP' coordinates; anything else left over is the tail. -> ([(pred, facts)], tail)"""
    for c in _cuts(s):
        r = match_vp(s[:c], stype)
        if r is None:
            continue
        rest = s[c:]
        if rest.startswith(" and "):
            sub = parse_vp_seq(rest[5:], stype)
            if sub:
                return [r] + sub[0], sub[1]
        return [r], rest
    return None


# ---------------------------------------------------------------- openers and subjects

# discourse openers carry no meaning and are dropped
_DISC_WORDS = re.compile(r"(?:in a separate update|elsewhere in the note|unrelatedly|meanwhile|also|in addition|"
                         r"additionally|separately|in contrast|by contrast|on the other hand|finally|next|later|then|"
                         r"and|nearby|while|whereas|but)(?:, | )", re.I)
_DISC_PP = re.compile(r"(?:in|during|at|on|after|before|within|throughout|from|while|as|for|when|upon|over|with) "
                      r"[^,\"]{1,60}?, ", re.I)
_DISC_NARR = re.compile(r"i (?:was|am|were) [^,\"]{1,80}? when |"
                        r"i (?:[a-z]+ ){1,8}?(?:after|when|because|before|once) (?:noting that )?", re.I)
DISCOURSE = [_DISC_WORDS, _DISC_PP, _DISC_NARR]
# evidential frames ("the record shows that", "Kofi Silva noted that") become source:/reported_by: qualifiers
_RVERB = (r"(?:noted|notes|note|says|said|say|shows|show|states|stated|state|recorded|records|record|mentioned|"
          r"mentions|explained|explains|observed|observe|remember|remembered|came up|added|adds|confirmed|confirms|"
          r"confirm|reported|reports|wrote|writes|indicated|indicates|recalled|recalls|highlighted|"
          r"quoted the speaker|claimed|claims|told me|heard|learned|noticed|notice|saw|see|watched|concluded|"
          r"contrasted|know|knew|reminded me|reminds me|lists|listed|documents|documented|shared)")
_RV_RX = re.compile(r"\b%s\b" % _RVERB, re.I)
_EV_AFTER = re.compile(r"(?: in [^,\"]{1,40}?(?= that ))?(?: that)?(?::|,)? ", re.I)
_EV_SRC_OK = re.compile(r"(?:according to [^,\"]{1,60}|[^,\":]{0,100}|%s, (?:meanwhile|however|too|also|in turn), "
                        r"[^,\":]{0,30}|I, %s, [^,\":]{0,30})" % (NAME, NAME), re.I)
_PERSON_SRC = re.compile(r"(?:I, )?(?P<n>%s|I)(?:, (?:meanwhile|however|too|also|in turn))?,?(?: also| then| can)? %s"
                         % (NAME, _RVERB), re.I)
_ACCORDING = re.compile(r"according to [^,\"]{1,60}?, ", re.I)


def _evidential(t):
    """Every (source text, rest) where t starts with an evidential frame ending in a reporting verb, longest first
    (so 'A recent personal note mentioned that' wins over 'A recent personal note')."""
    m = _ACCORDING.match(t)
    if m:
        yield t[:m.end()].rstrip(", "), t[m.end():]
    found = []
    for v in _RV_RX.finditer(t, 0, min(len(t), 140)):
        src = t[:v.end()]
        if not _EV_SRC_OK.fullmatch(src):
            continue
        a = _EV_AFTER.match(t, v.end())
        if a and a.end() < len(t):
            found.append((src, t[a.end():]))
    yield from reversed(found)


def opener_options(t, depth=0, evidential=True):
    """Yield (rest, qualifiers, reporter) for every way of peeling openers off the front, openers first."""
    if depth < 3:
        for rx in DISCOURSE:
            m = rx.match(t)
            if m and m.end() < len(t):
                yield from opener_options(t[m.end():], depth + 1, evidential)
        for src, rest in (_evidential(t) if evidential else ()):
            pm = _PERSON_SRC.fullmatch(src)
            if pm:
                who = "narrator" if pm.group("n").lower() == "i" else canon_name(pm.group("n"))
                q, rep = ["reported_by:" + who], who
            else:
                q, rep = ["source:" + src.lower()], None
            for rest2, q2, rep2 in opener_options(rest, depth + 1):
                yield rest2, q + q2, rep2 or rep
    yield t, [], None


_SUBJ_IAPPOS = re.compile(r"i, (%s), " % NAME, re.I)
_SUBJ_PAIR = re.compile(r"(%s) and (%s)(?: both)? " % (NAME, NAME))
_SUBJ_ASIDE = re.compile(r"(%s), (?:meanwhile|on the other hand|however|too|also|in turn|for (?:her|his|their) part), "
                         % NAME)
_SUBJ_NAME = re.compile(r"(%s) " % NAME)
_SUBJ_PRON = re.compile(r"(he|she|they) ", re.I)
_SUBJ_I = re.compile(r"i ", re.I)
_SUBJ_ORG = re.compile(r"(%s) " % ORG)
_SUBJ_YOUTH = re.compile(r"(%s) " % YOUTH)
_SUBJ_ROSTER = re.compile(r"the community roster (?:records|lists|has|shows) (me|%s) " % NAME, re.I)


def subject_options(t, speaker, reporter):
    """Yield (subjects, subject type, qualifiers, rest)."""
    m = _SUBJ_ROSTER.match(t)
    if m:
        who = (speaker or reporter or "narrator") if m.group(1).lower() == "me" else canon_name(m.group(1))
        yield [who], "roster", [], t[m.end():]
    m = _SUBJ_IAPPOS.match(t)
    if m:
        yield [canon_name(m.group(1))], "person", [], t[m.end():]
    m = _SUBJ_I.match(t)
    if m:
        youth = bool(speaker and re.fullmatch(r"Y\d+", speaker))
        yield [speaker or "narrator"], "youth" if youth else "person", [], t[m.end():]
    m = _SUBJ_PAIR.match(t)
    if m:
        yield [canon_name(m.group(1)), canon_name(m.group(2))], "person", [], t[m.end():]
    m = _SUBJ_ASIDE.match(t)
    if m:
        yield [canon_name(m.group(1))], "person", [], t[m.end():]
    m = _SUBJ_NAME.match(t)
    if m:
        yield [canon_name(m.group(1))], "person", [], t[m.end():]
    m = _SUBJ_PRON.match(t)
    if m:
        if reporter:
            yield [reporter], "person", [], t[m.end():]
        else:
            yield [m.group(1).lower()], "person", ["coref:pronoun"], t[m.end():]
    m = _SUBJ_ORG.match(t)
    if m:
        yield [canon_org(m.group(1))], "org", [], t[m.end():]
    m = _SUBJ_YOUTH.match(t)
    if m:
        yield [canon_youth(m.group(1))], "youth", [], t[m.end():]


# ---------------------------------------------------------------- tails

# inside a tail only capitalised names count, so commentary like "a simple pleasure mentioned ..." is not a person
CAP_NAME = r"(?!(?i:(?:%s)) )(?:[A-Z]\.|[A-Z][a-z][A-Za-z'-]*) (?!(?i:(?:%s))\b)[A-Z][A-Za-z'-]*[a-z]" % (STOP, STOP)
_EMBED_RX = re.compile(r"(?<![\w.])(%s)(?:,? who | )" % CAP_NAME)
# "..., and she also visited the museum": a pronoun clause in the tail is about the clause's own subject
_PRON_TAIL = re.compile(r"(?:^|[,;]) ?(?:and |but |while |then )?(?:he|she|they) (?=\S)")


def _tail_facts(seg, who, out):
    """Parse a VP sequence at the start of seg for subject(s) `who`; append facts; return the unparsed rest or None."""
    r = parse_vp_seq(seg, "person")
    if not r:
        return None
    for p, fs in r[0]:
        for w in who:
            for s, rel, obj, q in fs:
                out.append(fact(s or w, rel, obj, q))
    return r[1]


def parse_tail(tail, subjects=()):
    """-> (status qualifiers for stative facts, embedded facts), or None if the tail cannot be commentary."""
    if not tail:
        return [], []
    if re.search(r"[\"“”]", tail):
        return None
    quals = ["status:former"] if PAST_RX.search(tail) else []
    facts = []
    if subjects:
        m = _PRON_TAIL.search(tail)
        if m and m.start() == 0:
            rest = _tail_facts(tail[m.end():], subjects, facts)
            if rest is not None:
                tail = rest
    pos = 0
    while True:
        m = _EMBED_RX.search(tail, pos)
        if not m:
            break
        pos = m.end()
        rest = _tail_facts(tail[m.end():], [canon_name(m.group(1))], facts)
        if rest is not None:
            pos = len(tail) - len(rest)
    return quals, facts


# ---------------------------------------------------------------- clauses

def fact(subject, relation, obj="", qualifiers=()):
    seen = []
    for q in qualifiers:
        if q not in seen:
            seen.append(q)
    return {"subject": subject, "relation": relation, "object": obj, "qualifiers": seen}


class Result:
    def __init__(self, kind, facts, families=()):
        self.kind, self.facts, self.families = kind, facts, set(families)


_CACHE = {}


def clean(text):
    t = re.sub(r"\s+", " ", text.strip())
    return re.sub(r"[\s.,;:!?]+$", "", t)


def parse_clause(text, speaker=None, extra=()):
    """Parse one plain (unquoted) clause. -> Result("simple", facts, families) or None."""
    key = (text, speaker, tuple(extra))
    if key not in _CACHE:
        _CACHE[key] = _parse_clause(text, speaker, list(extra))
    return _CACHE[key]


def _parse_clause(text, speaker, extra):
    t = clean(text)
    if not t or re.search(r"[\"“”]", t):
        return None
    for rest, oq, rep in opener_options(t):
        for subs, stype, sq, rest2 in subject_options(rest, speaker, rep):
            r = parse_vp_seq(rest2, stype)
            if not r:
                continue
            tl = parse_tail(r[1], subs if stype == "person" else ())
            if tl is None:
                continue
            tq, efacts = tl
            out, fams = [], set()
            for p, fs in r[0]:
                fams.add(p.family)
                for s in subs:
                    for s2, rel, obj, q in fs:
                        quals = q + (tq if p.stative else []) + sq + oq + extra
                        out.append(fact(s2 or s, rel, s if obj == "{S}" else obj, quals))
            for f in efacts:
                f["qualifiers"] = list(dict.fromkeys(f["qualifiers"] + oq + extra))
            return Result("simple", out + efacts, fams)
    return None


def is_filler(text):
    """A clause with no entity (person name, ID, organization, youth, event) that no predicate parses."""
    t = clean(text)
    if not t or ENTITY_RX.search(t) or parse_clause(text) is not None:
        return False
    return not re.search(r"[\"“”]", t) or parse_speech(text) is None


# ---------------------------------------------------------------- splitting

# words a predicate (or a speech verb) can start with: a name followed by one of these begins a new clause
VSTART = (r"(?:owns|own|has|have|keeps|keep|kept|recommended|recommends|suggested|discussed|talked|mentioned|attends|"
          r"attend|attended|used|visited|went|had|helped|assisted|volunteered|volunteer|works|work|worked|travels|"
          r"travel|traveled|plans|prefers|genuinely|likes|chose|chooses|currently|is|am|was|buys|dislikes|enjoys|"
          r"serves|took|taught|said|says|explained|explains|added|noted|routinely|also|previously|formerly|no|only|"
          r"later|then|still)\b")
_SPLIT_START = (r"(?:%s(?: and %s both)? %s|%s and %s both\b|the community roster\b|%s\b|%s\b)"
                % (NAME, NAME, VSTART, NAME, NAME, ORG, YOUTH))
_SPLIT_PRON = r"(?:(?:I|we|it)\b(?! no longer\b)|the [a-z]+ (?:was|were|is|are|went|ran|looked)\b)"
_CONN_RX = re.compile(r"(?:, (?:and|but|while|whereas) (?=%s|%s)|; (?:and |but )?(?=\S)|, (?=%s)|"
                      r" (?:and|while|whereas) (?=%s))" % (_SPLIT_START, _SPLIT_PRON, _SPLIT_START, _SPLIT_START))
DROPPABLE = [r",", r";", r",? ?(?:and|but|while|whereas)", r"; (?:and|but)"]


def _quote_mask(line):
    """inq[i] is True when line[i] is inside quotation marks (an unclosed quote runs to the end of the line)."""
    inq, state = [], False
    for ch in line:
        if ch == "“":
            state = True
            inq.append(True)
            continue
        if ch == "”":
            inq.append(True)
            state = False
            continue
        if ch == '"':
            inq.append(True)
            state = not state
            continue
        inq.append(state)
    return inq


def sentences(line):
    inq = _quote_mask(line)
    out, start, n = [], 0, len(line)
    for i, ch in enumerate(line):
        end = None
        if ch in ".!?" and not inq[i]:
            end = i + 1
        elif ch in '"”' and i > 0 and line[i - 1] in ".!?" and (i + 1 == n or not inq[i + 1] or line[i] == "”"):
            end = i + 1
        if end is None or (end < n and line[end] != " "):
            continue
        if ch == "." and re.search(r"(?:^|[\s(])(?:[A-Za-z]|St|Mr|Mrs|Ms|Dr|Jr)\.$", line[:end]):
            continue
        seg = line[start:end].strip()
        if seg:
            out.append(seg)
        start = end
    seg = line[start:].strip()
    if seg:
        out.append(seg)
    return out


def split_clauses(line):
    """Sentences, then connectors outside quotes (', and NAME ...', '; ', ', NAME ...', ' and NAME ...')."""
    out = []
    for s in sentences(line):
        inq = _quote_mask(s)
        pos = 0
        for m in _CONN_RX.finditer(s):
            if inq[m.start()] or m.start() == 0:
                continue
            if m.start() < pos:
                continue
            piece = s[pos:m.start()]
            if piece.strip():
                out.append(piece.strip())
            pos = m.end()
        piece = s[pos:]
        if piece.strip():
            out.append(piece.strip())
    return out


# ---------------------------------------------------------------- reported speech

_SAY = (r"(?:said|says|explained|explains|added|adds|mentioned|mentions|agreed|agrees|noted|notes|continued|stated|"
        r"states|replied|replies|recalled|remarked|told me|wrote|writes|shared|confirmed|concluded|concludes|"
        r"insisted|answered|noting|adding|saying|explaining)")
_SPK = r"(?:%s|I|the (?:quoted )?speaker|[A-Za-z][^,\":]{0,60}?)" % NAME
_Q_OPEN = r"[\"“]"
_Q_CLOSE = r"[\"”]"
_IN = r"(?P<inner>[^\"“”]*)"
_SPEECH = [
    # NAME said, "..."   /   I contrasted this with the past, noting, "..."
    re.compile(r"(?P<spk>%s),?(?: also)? %s(?: [^,\":]{1,40})?(?:,|:)? %s%s%s?" % (_SPK, _SAY, _Q_OPEN, _IN, _Q_CLOSE)),
    # NAME: "..."
    re.compile(r"(?P<spk>%s): %s%s%s?" % (_SPK, _Q_OPEN, _IN, _Q_CLOSE)),
    # "...," the speaker said [in the handoff]
    re.compile(r"%s%s%s,? (?P<spk>%s) %s(?: [^\"“”]{1,40})?" % (_Q_OPEN, _IN, _Q_CLOSE, _SPK, _SAY)),
    # "...," NAME noted, "..."
    re.compile(r"%s(?P<inner>[^\"“”]*)%s,? (?P<spk>%s) %s,? %s(?P<inner2>[^\"“”]*)%s?"
               % (_Q_OPEN, _Q_CLOSE, _SPK, _SAY, _Q_OPEN, _Q_CLOSE)),
    # a bare quotation
    re.compile(r"%s%s%s?" % (_Q_OPEN, _IN, _Q_CLOSE)),
]


def speaker_id(spk):
    """-> (who 'I' refers to inside the quotation, reported_by label)."""
    if spk is None:
        return None, "unknown"
    s = spk.strip()
    if NAME_RX.fullmatch(s):
        n = canon_name(s)
        return n, n
    if re.fullmatch(YOUTH, s):
        n = canon_youth(s)
        return n, n
    if s.lower() == "i" or s.lower().startswith("i "):
        return "narrator", "narrator"
    return None, s.lower()


def parse_inner(inner, speaker, quals):
    facts = []
    for c in split_clauses(inner):
        r = parse_clause(c, speaker, quals)
        if r is not None:
            facts += r.facts
        elif not is_filler(c):
            return None
    return facts


def parse_speech(text):
    """`NAME said, "..."`, `NAME: "..."`, `"...," the speaker said`, or a bare quotation. -> Result("speech") or None."""
    t = re.sub(r"\s+", " ", text.strip())
    t = re.sub(r"[.!?]+$", "", t) if not re.search(r"[.!?][\"”]$", t) else t
    if not re.search(r"[\"“”]", t):
        return None
    for rest, oq, rep in opener_options(t, evidential=False):
        for i, rx in enumerate(_SPEECH):
            m = rx.fullmatch(rest)
            if not m:
                continue
            spk = m.groupdict().get("spk")
            subj, label = speaker_id(spk)
            inner = m.group("inner")
            if m.groupdict().get("inner2"):
                inner = inner.rstrip(", ") + ". " + m.group("inner2")
            facts = parse_inner(inner, subj, oq + ["reported_by:" + label])
            if facts:
                return Result("speech", facts)
    return None


def family_parse(clause, families):
    """Facts if `clause` is a plain clause whose main predicates all belong to `families`, else None."""
    r = parse_clause(clause)
    if r is None or not r.families or not r.families <= set(families):
        return None
    if len(r.families) > 1 and len(families) == 1:
        return None
    return r.facts


# ---------------------------------------------------------------- relative clauses

_REL_SUBJ = re.compile(r"(%s), who (.+?), (.+)" % NAME)
_REL_ONLY = re.compile(r"([^\"]*?)\b(%s), who (.+)" % CAP_NAME)


def _vp_facts(who, text):
    r = parse_vp_seq(text, "person")
    if not r or parse_tail(r[1]) is None:
        return None
    return [fact(s or who, rel, obj, q) for p, fs in r[0] for s, rel, obj, q in fs]


def parse_relative(text):
    """'NAME, who VP, <rest of clause>' and 'That is different from NAME, who VP' -> facts, or None."""
    t = clean(text)
    if re.search(r"[\"“”]", t) or parse_clause(text) is not None:
        return None
    m = _REL_SUBJ.fullmatch(t)
    if m:
        who = canon_name(m.group(1))
        facts = _vp_facts(who, m.group(2))
        if facts is None:
            return None
        r2 = parse_clause(m.group(1) + " " + m.group(3))
        if r2 is not None:
            return facts + r2.facts
        return facts if not ENTITY_RX.search(m.group(3)) else None
    m = _REL_ONLY.fullmatch(t)
    if m and not ENTITY_RX.search(m.group(1)):
        return _vp_facts(canon_name(m.group(2)), m.group(3))
    return None
