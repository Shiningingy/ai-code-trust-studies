"""Shared grammar pieces: slot patterns, canonical forms, the line splitter logic and the tail classifier.

Every part file imports this module (by plain name, after putting its own folder on sys.path).
"""
import re

# ---------------------------------------------------------------------------------------------------------------
# Slots
# ---------------------------------------------------------------------------------------------------------------

# A person as written: "Nadia Reed", "N. Reed", lowercase variants ("nadia reed", "n. reed"). First word is a
# given name or an initial, second word a family name. Rules match case-insensitively (lines can be lowercased).
NAME = r"(?:[A-Za-z][a-z]+|[A-Za-z]\.) [A-Za-z][a-z]+(?:-[A-Za-z][a-z]+)?"
# Speaker-relative subjects inside quotes: "I", "me" (resolved to the speaker by the reported-speech rule).
SELF = r"(?:I|me)"
SUBJ = r"(?:%s|%s)" % (NAME, SELF)
PID = r"[Pp]-\d+"                                   # person identifier, P-114
ORG = r"(?:[Oo]rganization|[Oo]rg) \d+"            # Organization 010 == Org 010
YOUTH = r"(?:[Yy]outh \d+|Y\d+|y\d+)"                # Youth 073 == Y073

# Words that can never start a person name (so "The community", "In a" ... are not names).
NOT_FIRST = {"the", "a", "an", "in", "on", "at", "it", "he", "she", "they", "we", "i", "this", "that", "his",
             "her", "their", "our", "my", "and", "but", "so", "while", "whereas", "which", "who", "where", "also",
             "elsewhere", "unrelatedly", "organization", "org", "youth", "according", "there", "then", "both",
             "as", "for", "with", "to", "of", "what", "when", "one", "some", "many", "all", "each", "every", "no",
             "not", "later", "today", "yesterday", "recently", "meanwhile", "however", "still", "afterwards"}
NOT_LAST = {"the", "a", "an", "is", "was", "to", "and", "of", "in", "on", "at", "for", "with", "that", "this",
            "it", "by", "under", "be", "has", "had", "have", "said", "says", "who", "which", "update", "note",
            "account", "roster", "record", "also", "are", "were", "did", "does", "do", "not", "no"}


def is_name(text):
    """True if text is a person name in one of its written forms: an initial and a family name ("N. Reed",
    "n. reed"), a known given name and a family name in any case ("nadia reed"), or two capitalised words that
    are not function words ("Nadia Reed")."""
    t = text.strip()
    if not re.fullmatch(NAME, t):
        return False
    a, b = t.split(" ", 1)
    if b.lower() in NOT_LAST:
        return False
    if a.endswith("."):          # an initial: "I. Usman", "a. gupta"
        return True
    if a.lower() in KNOWN_FIRST_LOWER:
        return True
    return a[0].isupper() and b[0].isupper() and a.lower() not in NOT_FIRST


# Given names seen in the documents; with them a lowercased name ("samir laurent") is still recognised. Capitalised
# names need not be listed.
KNOWN_FIRST = {"Talia", "Samir", "Rosa", "Quinn", "Priya", "Omar", "Nadia", "Mateo", "Leah", "Kofi", "Jia", "Isaac",
               "Hana", "Gabriel", "Farah", "Elena", "Dev", "Carla", "Ben", "Amina"}
KNOWN_FIRST_LOWER = {x.lower() for x in KNOWN_FIRST}


def person(text):
    """Canonical written form of a person: each word capitalised ("k. laurent" -> "K. Laurent")."""
    t = re.sub(r"\s+", " ", text.strip())
    if t in ("I", "me", "i", "Me"):
        return "I"
    return " ".join(w[:1].upper() + w[1:].lower() for w in t.split(" "))


def pid(text):
    return "P-" + re.sub(r"\D", "", text)


def org(text):
    """Organization 10 / Org 010 -> "Organization 010"."""
    return "Organization %03d" % int(re.sub(r"\D", "", text))


def youth(text):
    """Youth 73 / Y073 -> "Y073"."""
    return "Y%03d" % int(re.sub(r"\D", "", text))


def thing(text):
    """Canonical object: lowercase, single spaces, no leading article ("the market" -> "market")."""
    t = re.sub(r"\s+", " ", text.strip().lower())
    t = re.sub(r"^(?:the|a|an) ", "", t)
    return t


def city(text):
    return " ".join(w[:1].upper() + w[1:] for w in re.sub(r"\s+", " ", text.strip()).split(" "))


def fact(s, rel, obj="", quals=()):
    return {"subject": s, "relation": rel, "object": obj, "qualifiers": list(quals)}


# ---------------------------------------------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------------------------------------------

OPEN_Q = "\"“"
CLOSE_Q = "\"”"
ABBREV = re.compile(r"(?:^|[\s(])(?:[A-Za-z]|St|Mr|Mrs|Ms|Dr|Mt|Jr|Sr)\.$")

# Discourse openers that only join passages of a note or name its source; they carry no fact and no qualifier, so
# the splitter drops them like connectors. Openers that DO carry meaning ("During this-year,", "At the market,",
# "In the quoted speaker's account,", "I observed that", "it came up that") are not here: rules read them.
INTRO = [
    r"In a separate update,", r"Elsewhere in the note,", r"The same account also says that", r"Unrelatedly,",
    r"Also,", r"Separately,", r"In another update,", r"Meanwhile,", r"In addition,", r"Additionally,",
    r"On another note,", r"Later,", r"Nearby,", r"In other news,", r"Besides that,", r"In contrast,", r"Similarly,",
    r"Likewise,", r"Then,", r"Then", r"After that,", r"Finally,", r"Next,", r"Notably,", r"For the record,",
    r"While preparing my travel reimbursement,", r"During an ordinary team conversation,",
    # "In the meeting notes,", "In my event recap,", "During the shift handoff,", "On the handoff,": a source or an
    # occasion of the note, never a time of the fact (those are "During this-year," / "In the past,")
    r"(?:In|On|During|At) (?:the|my|an?|our) (?:[a-z'-]+ ){0,3}(?:recap|transcript|log|bulletin|chat|notes?|file|"
    r"record|profile|interview|email record|handoff|meeting|appointment|conversation|review|shift|trip|visit|"
    r"newsletter|report|update|summary|session),",
]
INTRO_RX = re.compile(r"^(?:%s)\s+" % "|".join(INTRO), re.I)

CONNECTORS = (r"(?:and also|but also|and then|and that|in contrast to|unlike|and|but|while|whereas|yet|though|"
              r"although|so)")
# A connector is not split off when what follows only completes the clause before it: a negation of the same
# predicate ("but no longer does", "but I do not", "but not a guardian", "but does not eat it").
NO_SPLIT_AFTER = re.compile(
    r"^(?:(?:but|and|though|although|yet|so)\s+)?(?:no longer\b|not\b|never\b|does not\b|do not\b|did not\b|doesn't\b|"
    r"don't\b|I do not\b|I don't\b|I no longer\b|she does not\b|he does not\b|they do not\b|"
    r"is not\b|isn't\b)", re.I)

# Verbs that follow the subject of a clause.
VERB = (r"(?:owns?|attends?|attended|visited|visit|visiting|discussed|discuss|recommended|recommend|helped|help|"
        r"helping|went|used|uses|use|routinely|currently|works?|worked|volunteered|volunteer|previously|formerly|"
        r"said|says|noted|notes|added|mentioned|explained|reported|is|was|are|has|had|have|serves?|served|buys?|"
        r"bought|enjoys?|likes?|loves?|dislikes?|eats?|ate|avoids?|took|takes?|teach(?:es)?|taught|prefers?|"
        r"genuinely|plans?|planned|never|no longer|also|often|always|usually|sometimes|regularly|really|only|"
        r"assisted|joined|joins?|chose|chooses?|suggested|talked|travels?|am|still|once|recently|later)\b")
# Facts the speaker states about themself ("I own a camera"), as opposed to the narrator's remarks ("I explained").
SELF_VERB = (r"(?:own|owns|attend|attends|attended|visited|discussed|recommended|helped|went|used|use|routinely|"
             r"currently|work|works|worked|volunteered|previously|formerly|serve|buy|enjoy|like|dislike|eat|avoid|"
             r"took|teach|taught|prefer|genuinely|plan|chose|choose|am|was|also|no longer|never|do not|suggested|"
             r"talked)\b")
# Openers that tell how a fact is known ("it came up that ...", "The record notes that ...", "I recorded that ...").
# They stay in the clause; the fact rules turn them into a qualifier (see evidence()).
_SRC_NP = (r"(?:(?:The|This|My|Our|An?|Their)(?! community roster)(?: [A-Za-z'-]+){1,8}?|"
           r"(?:Meeting|Shift|Volunteer|Travel|Event|Interview|Handoff) [a-z]+(?: [a-z]+)?)")
_SRC_VERB = (r"(?:notes|noted|note|records|recorded|record|states|stated|state|shows|showed|show|explains|explained|"
             r"mentions|mentioned|confirms|confirmed|says|said|reports|reported|indicates|indicated|lists|listed|"
             r"contrasted|adds|added|includes|included|recalls|recalled|describes|described|clarifies|clarified)")
_NARR_VERB = (r"(?:noted|recorded|stated|confirmed|observed|noticed|saw|remember|remembered|recall|recalled|"
              r"explained|heard|wrote|learned|found|logged|documented|watched|can confirm|know|knew|was told)")
EVIDENCE_QUALS = [
    (r"it came up that", "evidence:it came up"),
    (r"it was (?:also )?(?:noted|mentioned|reported|recorded|said|observed) that", "evidence:it was noted"),
    (r"As a direct observer, I (?:noted|observed|saw)(?: that)?", "evidence:narrator"),
    (r"I quoted the speaker:", "reported_by:the speaker"),
    (r"In the quoted speaker's account,|According to the speaker,", "reported_by:the speaker"),
    (r"I handed off (?:the (?:shift|notes)(?: with)?|(?:the )?(?:shift )?with)?(?: a few)?(?: notes)?:",
     "evidence:narrator"),
    (r"I was [a-z' ]+? when(?: I (?:remembered|recalled|noticed|saw|heard|learned|noted)(?: that)?)?",
     "evidence:narrator"),
    (r"I (?:filed|submitted|wrote|prepared) (?:the|a|my) [a-z ]*?(?:reimbursement|report|note|form)s? after"
     r"(?: noting that)?", "evidence:narrator"),
    (r"It reminded me that|I was reminded that", "evidence:narrator"),

    (r"I (?:also )?%s in (?:the|my|our) [a-z' ]+? that" % _NARR_VERB, "evidence:narrator"),
    (r"I (?:also )?%s(?: that)?,?" % _NARR_VERB, "evidence:narrator"),
    (r"%s(?: speaker| quoted speaker)(?: [A-Za-z'-]+){0,5}? %s(?: that)?:?" % (r"(?:The|This)", _SRC_VERB),
     "reported_by:the speaker"),
    (r"%s %s(?: that)?:?" % (_SRC_NP, _SRC_VERB), "evidence:record"),
    (r"Reportedly,", "hedge:reportedly"),
    (r"Apparently,", "hedge:apparently"),
]
EVIDENCE = r"(?:%s)" % "|".join(e for e, _ in EVIDENCE_QUALS)

# A subject: one or more persons ("P. Khan and G. Ito both"), "I, Omar Foster," (the narrator naming themself), or
# I/me; it may carry a parenthetical (", meanwhile,") or open a relative clause ("Farah Patel, who ...").
SUBJECTS = (r"(?:I, %s,|%s(?:(?:,| and|, and) %s)*(?: both| too| also)?|I|me)"
            r"(?:, (?:meanwhile|on the other hand|however|too|also|in turn|for (?:his|her|their) part|in contrast),)?"
            r"(?:,? who)?" % (NAME, NAME, NAME))


def subjects(text):
    """The persons of a SUBJECTS match, in canonical form."""
    t = re.sub(r",? who$", "", text.strip())
    t = re.sub(r", (?:meanwhile|on the other hand|however|too|also|in turn|for (?:his|her|their) part|in contrast),$",
               "", t)
    t = re.sub(r" (?:both|too|also)$", "", t)
    m = re.fullmatch(r"I, (%s)," % NAME, t)
    if m:
        return [person(m.group(1))] if is_name(m.group(1)) else None
    if re.fullmatch(SELF, t):
        return ["I"]
    parts = [x for x in re.split(r",? and |, ", t) if x]
    if not all(is_name(x) for x in parts):
        return None
    return [person(x) for x in parts]


SUBJECT_START = re.compile(
    r"^(?:%s\s+)?(?:(?P<name>%s) (?:[a-z]+ly )?%s|[Tt]he community roster\b|(?:%s) is\b|(?:%s) |I %s|I, (?:%s),|"
    r"I was at the\b|At the [a-z ]+, |(?:he|she|they) (?:also )?(?:said|says|noted|explained|mentioned|added) that)"
    % (EVIDENCE, SUBJECTS, VERB, ORG, YOUTH, SELF_VERB, NAME), re.I)


def starts_clause(rest):
    """True if `rest` begins a new clause with its own subject (so a connector before it separates two clauses)."""
    m = SUBJECT_START.match(rest)
    if not m:
        return False
    return not m.group("name") or subjects(m.group("name")) is not None


def _opener_only(left):
    """True for a piece that is only an opener of the clause after it ("At the riverside park", "According to the
    speaker", "Priya Gupta, meanwhile"): it has no verb, so the comma after it does not end a clause."""
    return len(left.split()) <= 8 and not re.search(r"\b%s" % VERB, left, re.I)


def _sentences(line):
    """Cut a line into sentence units; a quotation (with its speaker and attribution) stays one unit."""
    units, start, i, inq, n = [], 0, 0, False, len(line)
    while i < n:
        ch = line[i]
        if not inq and ch in OPEN_Q:
            inq = True
        elif inq and ch in CLOSE_Q:
            inq = False
            # A quotation closing on final punctuation ends the unit: Ben said, "I own a camera." Next...
            if line[i - 1] in ".!?":
                units.append(line[start:i + 1])
                start = i + 1
        elif not inq and ch in ".!?" and (i + 1 == n or line[i + 1] == " "):
            if not ABBREV.search(line[start:i + 1]) or i + 1 == n:
                units.append(line[start:i + 1])
                start = i + 1
            else:
                # an initial ("N. Reed") or an abbreviation ("St. John's"): not the end of a sentence
                pass
        i += 1
    if line[start:].strip():
        units.append(line[start:])
    return [u.strip() for u in units if u.strip()]


def _is_quote_unit(u):
    return any(q in u for q in OPEN_Q + CLOSE_Q)


def _split_connectors(s):
    """Split one sentence at connectors (", and", ", but", ", while", "; ", list commas, bare "and") where a new
    clause with its own subject follows. Anything else after a comma is an elaboration of the same clause and stays
    with it (rules read it as the clause's tail)."""
    out, start = [], 0
    pat = re.compile(r"(;\s+|,\s+(?:%s\s+)?|\s+(?:and|but|while|whereas)\s+)" % CONNECTORS, re.I)
    for m in pat.finditer(s):
        if m.start() < start:
            continue
        rest, sep = s[m.end():], m.group(1).strip(" ,;")
        if NO_SPLIT_AFTER.match((sep + " " + rest) if sep else rest):
            continue
        if not sep and "," in m.group(1) and _opener_only(s[start:m.start()]):
            continue
        if re.search(r"(?:^|, )(?:%s)(?:, (?:%s))*$" % (NAME, NAME), s[start:m.start()].strip()) and \
                subjects(s[start:m.start()].strip().split(", ")[-1]) and not re.search(VERB, s[start:m.start()]):
            continue
        if starts_clause(rest):
            out.append(s[start:m.start()])
            start = m.end()
    out.append(s[start:])
    return [c for c in out if c.strip()]


def split_text(text):
    """Clauses of a piece of text (a line, or the inside of a quotation)."""
    clauses = []
    for u in _sentences(text):
        if _is_quote_unit(u):
            clauses.append(u)
            continue
        while True:
            m = INTRO_RX.match(u)
            if not m:
                break
            u = u[m.end():]
        clauses.extend(_split_connectors(u))
    return [c.strip() for c in clauses if c.strip()]


DROPPABLE = [r"(?:%s\s*)+" % "|".join(INTRO), r"[,;]?\s*(?:%s)?" % CONNECTORS, r"and|but|while|whereas"]


# ---------------------------------------------------------------------------------------------------------------
# Clause grammar:  [EVIDENCE] [CONTEXT,] SUBJECT [ADVERBS] VERB-PHRASE [TAIL]
# ---------------------------------------------------------------------------------------------------------------
# Qualifier vocabulary (see NOTES.md):
#   time:past  time:current  time:future  time:this-year  time:last-year  time:some time ago  time:recently ...
#   freq:routinely  freq:once  freq:regular      neg      temporarily      genuinely      reason:<...>
#   evidence:<source>      reported_by:<speaker>

# Words before the verb. Each maps to qualifiers (or none).
ADVERBS = [
    (r"only used to|used to|formerly|previously|once used to", ["time:past"]),
    (r"no longer", ["time:past"]),
    (r"currently|now|still", ["time:current"]),
    (r"routinely|ordinarily|usually|normally|regularly", ["freq:routinely"]),
    (r"temporarily", ["temporarily"]),
    (r"genuinely|really|truly", ["genuinely"]),
    (r"plans to|plan to|planned to|is planning to|am planning to|intends to|intend to|will", ["time:future"]),
    (r"never", ["neg"]),
    (r"also|often|sometimes|always|just|recently|occasionally|simply|actually|had|has|have|both|too", []),
]
ADV_RX = re.compile(r"(?:%s)\b" % "|".join(a for a, _ in ADVERBS), re.I)


def adverb_quals(text):
    out = []
    for a in re.findall(ADV_RX.pattern, text, re.I):
        for rx, q in ADVERBS:
            if re.fullmatch(rx, a, re.I):
                out += [x for x in q if x not in out]
                break
    return out


# Phrases in the tail (after the verb phrase) that change the meaning of the clause.
TAIL_QUALS = [
    (r"\b(?:only )?in the past\b|\bpreviously\b|\bformerly\b|\bin a former role\b|\bhas since (?:lapsed|ended)\b|"
     r"\bno longer\b|\bformer (?:activity|role|member|membership)\b|\bused to\b|\bis over\b|\bhaving stopped\b|"
     r"\bstopped (?:attending|going|participating)\b|\b(?:does|do|did) not (?:attend|go|participate|join)"
     r"(?: now| anymore| any more)?\b|\b(?:is|am|are) not (?:a member|involved|active)(?: now| anymore)?\b|"
     r"\b(?:does|do) not now\b|\bbut not now\b", "time:past"),
    (r"\bsome time ago\b", "time:some time ago"),
    (r"\bin the future\b|\bsoon\b|\bnext (?:week|month|year)\b", "time:future"),
    (r"\bthis-year\b|\bthis year\b", "time:this-year"),
    (r"\blast-year\b|\blast year\b", "time:last-year"),
    (r"\ba current fact\b|\bcurrently\b|\bnowadays\b|\bat present\b|\bthese days\b|\bnow\b", "time:current"),
    (r"\brecently\b", "time:recently"),
    (r"\blast weekend\b", "time:last weekend"),
    (r"\blast week\b", "time:last week"),
    (r"\bthis morning\b", "time:this morning"),
    (r"\bonce\b", "freq:once"),
    (r"\bevery (?:week|weekend|morning|evening|day|month|tuesday|monday|wednesday|thursday|friday|saturday|"
     r"sunday)(?: (?:morning|evening|afternoon))?\b|\bweekly\b|\bregularly\b|\bon weekends\b|\bon (?:mon|tues|wednes|"
     r"thurs|fri|satur|sun)days\b|\bdaily\b", "freq:regular"),
    (r"\bduring the evening\b|\bin the evenings?\b", "during:evening"),
    (r"\bduring the day\b|\bin the daytime\b", "during:day"),
]
# Words that, left over in a tail after the phrases above, may change its meaning: such a tail is not accepted as
# mere elaboration (the clause stays unparsed until a rule or a phrase above covers it).
RED_FLAG = re.compile(r"\b(?:not|never|n't|nor|stopped|quit|anymore|no|instead of|rather than|except|unless|"
                      r"cancel\w*|refused|denied|false|untrue|mistaken|rumou?r\w*|allegedly|supposedly|maybe|"
                      r"perhaps|might|possibly|unclear|unconfirmed)\b", re.I)
# Elaborations that contain such words but do not touch the fact (they talk about something else).
HARMLESS = [
    r"made sure not to order anything with \w+", r"(?:are|is) not available for the next shift",
    r"no one else", r"not only\b", r"whether or not", r"but not recently", r"(?:was|were) not present",
]

# Where an elaboration of the tail starts: a comma or a word opening a new predication.
ELABORATION = re.compile(r",|(?:^|\s)(?:and|which|that|who|so|as an?|for)\b", re.I)
# An appositive that names the fact itself rather than its object (", a trip that ...", ", a current fact ...").
FACT_APPOSITIVE = re.compile(r",?\s*(?:an?|the) (?:[a-z-]+ ){0,2}(?:fact|stop|trip|visit|outing|membership|"
                             r"participation|habit|routine|role|commitment|event|experience|activity|detail|"
                             r"memory)\b", re.I)


def slot_in(text):
    """True if text contains a fact slot (a person, id, organisation, youth, event): it is a clause, not a tail."""
    if re.search(r"\b%s\b|\b%s\b|\b%s\b|event-P-\d+|\bthe community roster\b" % (PID, ORG, YOUTH), text, re.I):
        return True
    t = text
    for b in BOOKS:
        t = re.sub(re.escape(b), " ", t, flags=re.I)
    for m in re.finditer(r"(?<![A-Za-z.])(?=(%s)(?![a-z'\u2019]))" % NAME, t):  # "Farah Usman's habits": no slot
        if is_name(m.group(1)):
            return True
    return False


def tail_quals(tail):
    """Qualifiers carried by the tail of a clause, or None if the tail may change the meaning in a way no phrase
    covers (then the clause is left unparsed rather than misread)."""
    t = tail.strip(" ,;.!?")
    if not t:
        return []
    if slot_in(t):
        return None
    out, rest = [], t
    for h in HARMLESS:
        rest = re.sub(h, " ", rest, flags=re.I)
    # The head of the tail ("only in the past", "every Tuesday") modifies the fact. An elaboration after it
    # (", a group that meets weekly", " and plays it on weekends", ", which he used to show us the stars") talks
    # about something else: from it only a past status of the fact itself counts ("but he no longer does",
    # ", a membership that has since lapsed"), unless it is an appositive naming the fact (", a trip that ...").
    m = None if FACT_APPOSITIVE.match(rest) else ELABORATION.search(rest)
    parts = [(rest, True)] if not m else [(rest[:m.start()], True), (rest[m.start():], bool(FACT_APPOSITIVE.match(
        rest[m.start():])))]
    left = []
    for part, full in parts:
        if not full:
            part = re.sub(r"\bused to\b", " ", part, flags=re.I)     # purpose: "which I used to document the trip"
        for rx, q in TAIL_QUALS:
            if re.search(rx, part, re.I):
                if (full or q == "time:past") and q not in out:
                    out.append(q)
                part = re.sub(rx, " ", part, flags=re.I)
        left.append(part)
    rest = " , ".join(left)
    if "time:past" in out and "time:current" in out:     # "but that is in the past now", "a trip that is now in the past"
        out.remove("time:current")
    rest = re.split(r"(?:^|[ ,])(?:so|so that|which is why|because)\b", rest, maxsplit=1, flags=re.I)[0]
    if RED_FLAG.search(rest):
        return None
    return out


EVIDENCE_RX = re.compile(r"^(%s)\s+" % "|".join(e for e, _ in EVIDENCE_QUALS))

# Context openers that carry meaning: a time ("During this-year,") or a place ("At the market,").
CONTEXT_RX = re.compile(r"^(?:During (?P<year>this-year|last-year),|At the (?P<place>[a-z][a-z ]*?),)\s+", re.I)

REGISTRY = []   # every FactRule subclass, for the reported-speech rule


_EVIDENCE_RXS = [(re.compile(r"(?:%s)\s+" % e, re.I), q) for e, q in EVIDENCE_QUALS]
_RECORD_RX = re.compile(r"%s %s(?: that)?:?" % (_SRC_NP, _SRC_VERB), re.I)


def evidence_candidates(c):
    """Possible readings of the start of a clause as an evidence opener: [(qualifiers, rest), ...], best first,
    ending with the reading without opener. "The administrative record notes that ..." is tried at every verb
    ("record", "notes"), since the source's own words can look like verbs."""
    out = []
    for rx, q in _EVIDENCE_RXS:
        if q in ("evidence:record", "reported_by:the speaker"):
            continue
        m = rx.match(c)
        if m:
            out.append(([q], c[m.end():]))
    for m in re.finditer(r"\b%s(?: that)?:?\s+" % _SRC_VERB, c[:160], re.I):
        head = c[:m.end()].strip()
        if _RECORD_RX.fullmatch(head):
            q = "reported_by:the speaker" if re.search(r"\bspeaker\b", head) else "evidence:record"
            out.append(([q], c[m.end():]))
    for rx, q in _EVIDENCE_RXS:
        if q == "reported_by:the speaker":
            m = rx.match(c)
            if m:
                out.append(([q], c[m.end():]))
    out.append(([], c))
    return out


def evidence(c):
    """(qualifiers, rest) for the first evidence reading of a clause (see evidence_candidates)."""
    return evidence_candidates(c)[0]


class FactRule:
    """Mixin for rules written as  SUBJECT [ADVERBS] <verb phrase> [TAIL].

    Subclasses set `phrases`: a list of regexes for the verb phrase (named groups for slots), and implement
    facts(subject, groups, quals). The subject, adverbs, evidence opener and tail are handled here.
    `subject` is a regex for the subject (default: a person or I/me); set `person_subject = False` for others.
    """
    phrases = []
    subject = SUBJ
    person_subject = True
    allow_context = False
    _compiled = None

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        REGISTRY.append(cls)

    def _rxs(self):
        if type(self).__dict__.get("_compiled") is None:
            subj = SUBJECTS if self.person_subject else self.subject
            type(self)._compiled = [
                re.compile(r"(?P<_s>%s)(?P<_adv>(?: (?:%s))*) (?:%s)(?=$|[ ,;:])" % (subj, ADV_RX.pattern, p), re.I)
                for p in self.phrases]
        return type(self)._compiled

    def parse(self, clause):
        c0 = clause.strip().rstrip(".!?").strip()
        for quals, c in evidence_candidates(c0):
            out = self._parse(list(quals), c)
            if out is not None:
                return out
        return None

    def _parse(self, quals, c):
        ctx = {}
        m = CONTEXT_RX.match(c)
        if m:
            if m.group("year"):
                quals.append("time:" + m.group("year").lower())
            else:
                if not self.allow_context:
                    return None
                ctx["place"] = m.group("place")
            c = c[m.end():]
        for rx in self._rxs():
            m = rx.match(c)
            if not m:
                continue
            s = m.group("_s")
            who = subjects(s) if self.person_subject else [s]
            if not who:
                continue
            tq = tail_quals(c[m.end():])
            if tq is None:
                continue
            g = {k: (v or "") for k, v in m.groupdict().items()}
            g.update(ctx)
            q = add(quals, *adverb_quals(g["_adv"]))
            q = add(q, *tq)
            out = []
            for w in who:
                f = self.facts(w, g, q)
                if f is None:
                    out = None
                    break
                out += f
            if out is not None:
                return out
        return None

    def facts(self, s, g, quals):
        raise NotImplementedError


def add(quals, *extra):
    out = list(quals)
    for e in extra:
        if e and e not in out:
            out.append(e)
    return out


# ---------------------------------------------------------------------------------------------------------------
# Object vocabularies (known values first; a generic fallback keeps new values parseable)
# ---------------------------------------------------------------------------------------------------------------
PLACES = ["sports hall", "riverside park", "museum", "market", "library"]
GROUPS = ["walking group", "history group", "chess club", "garden circle", "radio society"]
BOOKS = ["The Long Orchard", "Quiet Machines", "Atlas of Clouds", "Copper Harbor"]
ITEMS = ["garden tools", "sewing kit", "camera", "telescope", "guitar"]
MODES = ["bus", "tram", "train", "subway", "metro", "plane", "car", "bike", "bicycle", "ferry", "coach", "taxi",
         "light rail", "streetcar", "underground", "airplane", "flight"]
FOODS = ["banana", "watermelon", "pear", "peach", "mango", "apple", "plum", "orange", "grapes", "cherry",
         "strawberry", "yogurt", "milk", "butter", "cheese", "cream", "ice cream", "lentils", "bread", "rice",
         "pasta", "eggs", "fish", "chicken", "beef", "tofu", "beans", "carrot", "potato"]


def alt(words, fallback):
    return r"(?:%s|%s)" % ("|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)), fallback)


# a content word (not a function word), for the generic fallbacks
WORD = (r"(?!(?:that|this|he|she|it|they|we|i|his|her|their|a|an|the|to|with|about|and|but|or|of|for|in|on|at|"
        r"by|from|as|so|who|which|me|my|our|is|was|be)\b)[a-z][a-z'-]*")
PLACE = alt(PLACES, r"%s(?: %s)?" % (WORD, WORD))
GROUP = alt(GROUPS, r"%s (?:group|club|circle|society|team|choir|league)" % WORD)
BOOK = alt(BOOKS, r"[A-Z][a-z]+(?: (?:of|the|and|[A-Z][a-z]+))*")
ITEM = alt(ITEMS, r"%s(?: %s)?" % (WORD, WORD))
MODE = alt(MODES, r"(?!x)x")   # known modes only: "used to ..." must not read "to" as a mode
FOOD = alt(FOODS, WORD)
# the aspect of a discussed group or place: "market trends", "library hours" (a noun, not an adverb or connector)
ASPECT = (r"(?!(?:during|instead|together|too|again|also|often|once|recently|today|yesterday|later|last|this|"
          r"every|only|though|while|whereas|yet|since|because|before|after|until|now|here|there|then|both)\b)"
          r"%s" % WORD)


def book(text):
    for b in BOOKS:
        if b.lower() == text.strip().lower():
            return b
    return " ".join(w if w in ("of", "the", "and") else w[:1].upper() + w[1:] for w in text.strip().split(" "))


# ---------------------------------------------------------------------------------------------------------------
# Parsing a piece of text with the whole library (for rules that contain other clauses)
# ---------------------------------------------------------------------------------------------------------------
_instances = {}


def register(cls):
    """Make a non-FactRule rule available to parse_clause (quotations, compound clauses)."""
    REGISTRY.append(cls)
    return cls


def parse_clause(text, skip=()):
    """Facts of one clause by the library's rules (exactly one reading), or None."""
    import json
    got = []
    for cls in REGISTRY:
        if cls in skip:
            continue
        r = _instances.get(cls) or _instances.setdefault(cls, cls())
        f = r.parse(text)
        if f is not None:
            got.append(f)
    if not got or len({json.dumps(f, sort_keys=True) for f in got}) > 1:
        return None
    return got[0]


def parse_text_facts(text, skip=()):
    """Facts of a piece of text (split into clauses, each parsed by parse_clause), or None if any clause fails."""
    out = []
    for cl in split_text(text):
        f = parse_clause(cl, skip)
        if f is None:
            return None
        out.extend(f)
    return out
