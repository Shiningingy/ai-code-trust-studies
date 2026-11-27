"""Shared grammar pieces for the community-records documents (not a part; imported by the part files).

A clause is read as:   [opener ","] [report frame] SUBJECT PREDICATE [tail]
  opener   discourse marker such as "In a separate update," (no meaning) or "In the past," (adds a qualifier)
  frame    reported speech such as "The record shows that" (adds qualifier "reported")
  SUBJECT  a person name, "Org 014", "Y045", or a self-quote: N said, "I ..." / N said he ... (qualifier
           "self_reported")
  PREDICATE  one of the predicate families defined in the part files (3rd and 1st person forms)
  tail     an elaboration without facts (", which he often brings ..."); it is refused when it carries a word that
           would change the meaning (no longer, not, used to ...) the predicate did not already account for.
"""
import re

STOP_WORD = (r"(?:the|a|an|it|this|that|these|those|which|who|our|my|his|her|their|its|one|some|all|both|each|every|"
             r"he|she|they|we|you|i|me|him|them|and|but|while|whereas|so|then|also|in|on|at|for|with|during|after|"
             r"before|as|to|of|said|says|does|do|did|not|no|has|have|had|was|were|is|are|been|only|still|now|often|"
             r"meanwhile|however|there|here|when|where|what|why|how|very|just|too|well|later|once|from|by)")
# A person name: "Nadia Reed", "N. Reed", "n.reed", "nadia reed" (any case); neither word a function word.
NAME = (r"(?:[A-Za-z]\.\s?(?!%s\b)[A-Za-z][a-z'-]+|(?!%s\s)[A-Za-z][a-z]+\s(?!%s\b)[A-Za-z][a-z'-]+)"
        % (STOP_WORD, STOP_WORD, STOP_WORD))
ORG = r"(?:org|organization|organisation)\.?\s*#?\s*(?P<orgnum>\d+)"
YOUTH = r"(?:youth\s*(?P<ynum>\d+)|y-?(?P<ynum2>\d+))"
PID = r"[Pp]-\d+"
Q = "[\"“”'‘’]"          # quote characters

REPORT_VERB = (r"(?:said|says|say|noted|notes|note|recorded|records|record|shows|show|showed|states|state|stated|"
               r"explained|explains|mentioned|mentions|observed|observes|confirmed|confirms|reported|reports|added|"
               r"adds|indicated|indicates|remembered|remember|recalled|recalls|noticed|saw|wrote|writes|learned|"
               r"heard|told me|tells me|lists|listed|highlighted|highlights|clarified|clarifies|contrasted|"
               r"commented|remarked|continued|replied|shared|documented|documents|captured|captures|logged|logs|"
               r"described|describes|emphasized|pointed out|came up|was noted|is noted|was recorded|is recorded|"
               r"was mentioned|reads|read|knew|found|recorded in|included|includes|summarized|summarizes|"
               r"acknowledged|specified|specifies|referenced|references|quoted the speaker|quoted|noting|watched|know|"
               r"recalling|adding|explaining|mentioning)")


def canon_name(s):
    s = re.sub(r"\s+", " ", s.strip())
    s = re.sub(r"^([A-Za-z])\.\s?", r"\1. ", s)
    return " ".join(w[:1].upper() + w[1:].lower() for w in s.split(" "))


def canon_org(num):
    return "Org %03d" % int(num)


def canon_youth(num):
    return "Y%03d" % int(num)


# ---- openers and frames -------------------------------------------------------------------------------------------

# Openers that say WHEN: they change the meaning, so they become qualifiers.
TIME_OPENERS = [(re.compile(r"(?:in the past|previously|formerly|back then|years ago|some time ago|earlier)$", re.I), "past"),
                (re.compile(r"(?:in the future|next year|soon)$", re.I), "future"),
                (re.compile(r"(?:currently|these days|nowadays|now)$", re.I), None)]

OPENER_RX = re.compile(r"^%s?\s*(?P<op>[A-Za-z][\w'’-]*(?:\s+[\w'’-]+){0,9})\s*,\s+" % Q)
FRAME_RX = re.compile(r"^%s?\s*(?P<src>(?:[\w'’,-]+\s+){0,14}?)%s(?:\s+(?:in|on|to|during|for)\s+[^,\"“]{1,40}?)?"
                      r"(?:\s+that)?\s*[,:]?\s+%s?\s*" % (Q, REPORT_VERB, Q), re.I)
# "I noted in the community bulletin that N ..." : a frame with words between the verb and "that".
FRAME_THAT_RX = re.compile(r"^%s?\s*(?P<src>(?:[\w'’,-]+\s+){0,14}?)%s(?:\s+[^,\"“]{1,60}?)?\s+that\s+%s?\s*"
                           % (Q, REPORT_VERB, Q), re.I)
# The narrator sets a scene, then reports: "I was at the riverside park when N ...", "I filed the reimbursement after
# noting that N ...", "I contrasted this with the past, noting, "N ...", "Then N ...".
NARRATOR_FRAMES = [
    re.compile(r"^%s?\s*I\s+(?:[\w'’-]+\s+){1,12}?(?:when|after|while|as|before)\s+(?:I\s+\w+\s+(?:that\s+)?|"
               r"(?:noting|seeing|hearing|learning)\s+(?:that\s+)?)?" % Q, re.I),
    re.compile(r"^%s?\s*I\s+contrasted\s+this\s+with\s+[^,]{1,40},\s*(?:noting|adding|explaining)\s*(?:that\s*)?,?\s*%s?\s*"
               % (Q, Q), re.I),
    re.compile(r"^(?:then|also|later|meanwhile|next|finally|afterwards|separately)\s+(?=[A-Za-z])", re.I),
]
TIME_WORDS = re.compile(r"\b(?:past|previous|previously|former|formerly|used to|no longer|future|plans?|will|"
                        r"not|never|last year|this year|once)\b", re.I)


def decompositions(clause):
    """Yield (rest, qualifiers) readings of a clause: as is, without its opener, without its report frame, both.
    Each reading is tried in this order; the first one a predicate accepts is used."""
    text = clause.strip()
    seen = set()

    def emit(t, q):
        key = (t, tuple(q))
        if key not in seen:
            seen.add(key)
            out.append((t, q))

    out = []
    emit(text, [])
    queue = [(text, [], 0)]
    while queue:
        t, q, depth = queue.pop(0)
        if depth >= 3:
            continue
        m = OPENER_RX.match(t)
        if m:
            op = m.group("op")
            if not re.search(REPORT_VERB, op, re.I):
                q2 = list(q)
                for rx, tag in TIME_OPENERS:
                    if rx.search(op):
                        if tag:
                            q2.append(tag)
                        break
                else:
                    if TIME_WORDS.search(op):
                        q2 = None          # an opener with a time/negation word we do not know: refuse
                if q2 is not None:
                    emit(t[m.end():], q2)
                    queue.append((t[m.end():], q2, depth + 1))
        for rx in (FRAME_RX, FRAME_THAT_RX):
            m = rx.match(t)
            if m and not TIME_WORDS.search(m.group(0)):
                q2 = q + ["reported"] if "reported" not in q else list(q)
                emit(t[m.end():], q2)
                queue.append((t[m.end():], q2, depth + 1))
        for i, rx in enumerate(NARRATOR_FRAMES):
            m = rx.match(t)
            if m and (i == 1 or not TIME_WORDS.search(m.group(0))):
                q2 = q + ["reported"] if "reported" not in q and i < 2 else list(q)
                emit(t[m.end():], q2)
                queue.append((t[m.end():], q2, depth + 1))
    return out


SELF_VERB = (r"(?:said|says|added|adds|explained|explains|continued|noted|notes|mentioned|mentions|stated|states|"
             r"replied|remarked|recalled|shared|told me|confirmed|wrote|admitted|insisted|clarified|reported|"
             r"concluded|agreed|began|answered|responded|joked|laughed|offered|volunteered that)")

# Words that can follow a person's name at the start of a clause (predicate verbs and their adverbs).
START_VERB = (r"(?:owns?|own|has|have|keeps?|recommended|recommends|attends?|attended|visited|visits|went|helped|helps|"
              r"assisted|discussed|discusses|mentioned|talked|spoke|used|uses|routinely|plans?|planned|works?|worked|"
              r"currently|chose|chooses|choose|likes?|liked|genuinely|prefers?|preferred|enjoys?|enjoyed|dislikes?|"
              r"disliked|buys?|bought|serves?|served|volunteered|volunteers|also|simply|only|previously|formerly|"
              r"no longer|once|still|now|avoids?|both|"
              r"is (?:the|an?|listed|temporarily|currently|not|no)|was (?:the|an?|listed)|"
              r"%s\s*[,:]?\s*%s|%s\s+(?:that\s+)?(?:he|she|they)\b|:\s*%s)" % (SELF_VERB, Q, SELF_VERB, Q))
# Where a new clause starts: "[she explained that] NAME [and NAME] VERB", an org, a youth, the roster.
_START = (r"\s*%s?\s*(?:\b(?:he|she|they|I|we)\s+(?:also\s+)?%s\s+(?:that\s+)?)?"
          r"(?:\bthe community roster|\b%s\s+(?:is|was)\s+based|\b%s\s+(?:currently\s+)?(?:attends?|said|says)|"
          r"\bI\s*,\s*{N}\s*,|\b{N}(?:\s+and\s+{N})?\s*(?:,\s*(?:meanwhile|on the other hand|however|too|also|"
          r"in turn)\s*,\s*)?\s+%s\b)" % (Q, REPORT_VERB, ORG, YOUTH, START_VERB))
CLAUSE_START = re.compile(_START.replace("{N}", NAME), re.I)
# The same with capitalised names only ("Kofi Patel", "K. Patel"), to find a clause hidden inside a tail without
# taking word pairs like "simple pleasure mentioned" for a name and a verb.
NAME_CAPS = r"(?-i:[A-Z]\.\s?[A-Z][a-z'-]+|[A-Z][a-z]+\s[A-Z][a-z'-]+)"
CLAUSE_IN_TAIL = re.compile(_START.replace("{N}", NAME_CAPS), re.I)

# ---- subjects -----------------------------------------------------------------------------------------------------



def subject_forms(kind):
    """(regex prefix, qualifiers) pairs for the subject part of a clause; the prefix has group 'subj'."""
    if kind == "person":
        # the name may carry an aside: "Priya Gupta, meanwhile, said she ..."
        S = (r"(?P<subj>%s(?:\s*,\s*%s)*(?:\s*,?\s+and\s+%s)?)(?:\s+both|\s+all)?(?:\s*,\s*(?:meanwhile|on the other hand|however|in turn|too|also|for (?:his|her|their) "
             r"part|in contrast|by contrast|likewise|similarly|for example|for instance|in particular)\s*,)?" % (NAME, NAME, NAME))
        return [
            (r"%s?\s*%s\s+" % (Q, S), [], 3),
            (r"%s\s*(?:,\s*)?(?:also\s+)?%s(?:\s+(?:in|on|to|during)\s+[^,\"“]{1,40})?\s*[,:]?\s*%s?\s*I\s+"
             % (S, SELF_VERB, Q), ["self_reported"], 1),
            (r"%s\s*:\s*%s?\s*I\s+" % (S, Q), ["self_reported"], 1),
            (r"%s\s+(?:also\s+)?%s\s+(?:that\s+)?(?:he|she|they)\s+" % (S, SELF_VERB), ["self_reported"], 3),
            (r"%s?\s*I\s*,\s*%s\s*,\s*" % (Q, S), ["self_reported"], 3),
        ]
    if kind == "org":
        return [(r"%s?\s*(?P<subj>%s)\s+" % (Q, ORG), [], 3)]
    if kind == "youth":
        return [(r"%s?\s*(?P<subj>%s)\s+" % (Q, YOUTH), [], 3),
                (r"(?P<subj>%s)\s*(?:,\s*)?%s\s*[,:]?\s*%s?\s*I\s+" % (YOUTH, SELF_VERB, Q), ["self_reported"], 1)]
    raise ValueError(kind)


def canon_subjects(kind, m):
    """The subjects of a match: one, or several for "P. Khan and G. Ito both ..."."""
    if kind == "person":
        return [canon_name(n) for n in re.split(r"\s*,\s*and\s+|\s*,\s*|\s+and\s+", m.group("subj").strip())]
    if kind == "org":
        return [canon_org(m.group("orgnum"))]
    return [canon_youth(m.group("ynum") or m.group("ynum2"))]


# ---- tails --------------------------------------------------------------------------------------------------------

END_PUNCT = re.compile(r"[\s.!?;:,\"“”'‘’)]*")
# Words in a tail that would change the meaning of the clause.
SIGNALS = [
    ("past", re.compile(r"\b(?:no longer|in the past|former|formerly|used to|has since|have since|anymore|any more|"
                        r"lapsed|previously|stopped|ended)\b", re.I)),
    ("negated", re.compile(r"\b(?:not|never|n't|nor)\b|\bno\b(?! longer)", re.I)),
    ("future", re.compile(r"\b(?:in the future|plans? to|will start|intends? to)\b", re.I)),
]
# Tail openings that start a separate subordinate remark about something else; time and negation words inside them
# do not qualify the main clause.
REMARK_START = re.compile(r"^(?:,\s*|\s+)(?:and\s+|but\s+)?(?:so (?:I|we|the|it|that|there|our|my|he|she|they|his|her|their)\b|which\b|where\b|"
                          r"an? (?:[\w-]+\s+){0,3}?(?:that|which|who|of|for|with|to|from|in)\b|"
                          r"(?:the|it|its|this|that)\s+(?!is in the past)|(?:I|we)\b|"
                          r"as (?:the|a|an|it|they|I|we)\b)", re.I)
# Signals that speak about the subject itself even inside a remark.
SUBJECT_PAST = re.compile(r"\b(?:no longer|anymore|any more|former role|but only)\b", re.I)
REPORT_TAIL = re.compile(r"^\s*[,.]?\s*%s\s*,?\s*(?:the|an?|I|she|he|they|my|our)?\b[\w\s']*\b%s\b.*$" % (Q, REPORT_VERB),
                         re.I)


def tail_ok(tail, quals):
    """Return the extra qualifiers a tail adds, or None if the tail changes the meaning in a way not handled.
    `quals` may hold the pseudo-qualifier "past-compatible" for predicates that are past by nature (a visit)."""
    if END_PUNCT.fullmatch(tail):
        return []
    if not re.match(r"^(?:\s*,|\s*;|\s+|\s*%s)" % Q, tail):
        return None                      # the predicate stopped in the middle of a word
    if REPORT_TAIL.match(tail):
        return ["reported"]
    if CLAUSE_IN_TAIL.search(tail):
        return None                      # a whole clause hides in the tail; the splitter must cut it off
    tags = [tag for tag, rx in SIGNALS if rx.search(tail)]
    if not tags:
        return []
    # the tail repeats what the predicate already says ("only in the past, so she no longer joins ...")
    if ("past" in quals or "past-compatible" in quals) and set(tags) <= {"past", "negated"}:
        return []
    # a remark about something else ("so I made sure not to order anything with milk")
    if REMARK_START.match(tail) and not SUBJECT_PAST.search(tail):
        return []
    return None


# ---- the analyser -------------------------------------------------------------------------------------------------

class Pred:
    """One predicate form: regex (matched right after the subject) and a builder taking the match and returning
    (relation, object, qualifiers) or a list of such triples. person: 3 only after a 3rd-person subject, 1 only
    after "I", 0 both. past_ok: the predicate is past by nature (a visit), so past words in its tail are no news."""

    def __init__(self, rx, build, person=3, past_ok=False):
        self.rx = re.compile(rx, re.I)
        self.build = build
        self.person = person
        self.past_ok = past_ok


TAIL_LOG = None        # set to a list to collect the tails analyze() accepts (for auditing a library)


def analyze(clause, kind, preds):
    """Return the facts of a clause for these predicates, or None."""
    forms = [(re.compile(p, re.I), q, person) for p, q, person in subject_forms(kind)]
    for rest, quals in decompositions(clause):
        for frx, fq, fperson in forms:
            m = frx.match(rest)
            if not m:
                continue
            after = rest[m.end():]
            for p in preds:
                if p.person and p.person != fperson:
                    continue
                pm = p.rx.match(after)
                if not pm:
                    continue
                triples = p.build(pm)
                if isinstance(triples, tuple):
                    triples = [triples]
                pq = sorted({q for t in triples for q in t[2]}) + (["past-compatible"] if p.past_ok else [])
                extra = tail_ok(after[pm.end():], pq + quals)
                if extra is None:
                    continue
                if TAIL_LOG is not None:
                    TAIL_LOG.append(after[pm.end():])
                facts = []
                for subj in canon_subjects(kind, m):
                    for rel, obj, q in triples:
                        allq = []
                        for x in list(q) + quals + fq + extra:
                            if x not in allq:
                                allq.append(x)
                        facts.append({"subject": subj, "relation": rel, "object": obj, "qualifiers": allq})
                return facts
    return None


def v(base):
    """Regex for a verb in 3rd or 1st person: v('own') -> 'owns?'; irregular forms are written out."""
    return {"is": "(?:is|am|are)", "has": "(?:has|have)", "does": "(?:does|do)"}.get(base, base + "s?")


# ---- slot helpers -------------------------------------------------------------------------------------------------

# Where a free slot (an item, a place, a book) ends: end of clause, punctuation, or a word that starts a tail.
BOUNDARY = (r"(?=\s*$|\s*[,;.!?:\"“”)]|\s+(?:to|with|for|as|after|at|on|during|in|every|regularly|too|"
            r"which|because|since|from|before|when|while|and|but|so|where|who|that|this|last|each|most|again|"
            r"recently|yesterday|today|together|alone|often|sometimes|always|usually|daily|weekly|only|some|"
            r"previously|once|then|now|whenever|around|near|about|over|under|by|through|into|like|just|even|"
            r"here|there|well|almost|nearly|mostly|both|either|via|or|without|although|though|until|throughout|later|"
            r"earlier|instead|nearby|afterward|afterwards|more|used|whose|whom|if|despite|among|regarding)\b)")


def slot(name, article=True):
    art = r"(?:the\s+|a\s+|an\s+)?" if article else ""
    return r"%s(?P<%s>[^\s,;.!?:\"“”][^,;.!?:\"“”]*?)%s" % (art, name, BOUNDARY)


def clean(s):
    """Slot text as an object: lower case, single spaces, without a leading article ('The Long Orchard' ->
    'long orchard', 'the market' -> 'market')."""
    return re.sub(r"^(?:the|a|an) ", "", re.sub(r"\s+", " ", s.strip()).lower())


PAST_TAIL = (r"(?P<past_tail>,?\s*(?:but\s+|though\s+|although\s+|also\s+)?(?:only\s+)?in the past|"
             r",?\s*but\s+(?:I\s+|he\s+|she\s+|they\s+)?no longer (?:does|do)|,?\s*but that is in the past|"
             r",?\s*but\s+(?:I\s+|he\s+|she\s+|they\s+)?(?:does|do)(?: not|n't) (?:attend|go|participate)(?: now| anymore)?|"
             r",?\s*(?:but|though|although)\s+(?:he|she|they|I)\s+(?:is|are|am)\s+no longer\s+(?:a\s+|an\s+active\s+)?member|"
             r"\s+in a former role|,?\s*but\s+(?:I\s+|he\s+|she\s+|they\s+)?(?:don't|doesn't|do not|does not) anymore)?")
