"""Shared helpers for the community-records grammar: entity patterns, canonical entity names, and the clause splitter.

This module defines no parts. Part files import it by plain name (see `_here` in each file).
"""
import re

# ---------------------------------------------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------------------------------------------
# A person is written "Nadia Reed", "N. Reed", "nadia Reed", "n. reed", "nadia reed". Surname tokens may contain
# a hyphen or apostrophe. Names are not taken from a fixed list, so new documents with new names still parse.
_TOK = r"[A-Za-z][a-z]*(?:['-][A-Za-z][a-z]+)*"
PERSON = r"(?:[A-Za-z]\.|%s) %s" % (_TOK, _TOK)
ORG = r"(?:[Oo]rg|[Oo]rganization|ORG|ORGANIZATION)\.? ?\d+"
YOUTH = r"(?:[Yy]outh ?\d+|[Yy]-?\d+)"
PID = r"[Pp]-\d+"
# words that look like a two-word name but never are (pronouns, articles, ...): a subject must not start with them
_NOT_FIRST = {"it", "this", "that", "they", "she", "he", "we", "the", "a", "an", "which", "who", "there", "so",
              "then", "and", "but", "while", "i", "our", "my", "his", "her", "their", "its", "everything", "one",
              "both", "each", "all", "some", "in", "on", "at", "for", "of", "to", "with", "as", "no", "not", "also"}
_NOT_LAST = {"is", "was", "were", "are", "has", "had", "did", "does", "said", "says", "also", "and", "of", "the",
             "a", "to", "in", "on", "at", "it", "for", "with", "be", "been", "being", "can", "could", "will"}


# Name pools seen in the training documents. They are only needed for names written all in lowercase
# ("isaac avery"), which cannot otherwise be told apart from ordinary words ("ensuring everything").
# Capitalised names ("Isaac Avery", "I. Avery", "isaac Avery") are recognised without these lists.
FIRST_NAMES = set("""isaac mateo dev omar leah nadia kofi hana carla gabriel jia priya amina elena quinn talia farah
samir ben rosa""".split())
SURNAMES = set("""novak laurent bennett reed mensah khan silva jones diaz haddad tran ortiz evans gupta foster chen
usman patel ito avery""".split())


def is_person(s):
    s = s.strip()
    if not re.fullmatch(PERSON, s):
        return False
    first, last = s.split(" ")
    if len(last) < 2 or last.lower() in _NOT_LAST or (not first.endswith(".") and first.lower() in _NOT_FIRST):
        return False
    if last[0].isupper():
        return True
    # all-lowercase surname: accept only known name words
    return last in SURNAMES or first.rstrip(".") in FIRST_NAMES


def person(s):
    """Canonical person name: 'Nadia Reed' or 'N. Reed' (each token capitalised)."""
    parts = s.strip().split(" ")
    out = []
    for p in parts:
        out.append("-".join("'".join(x[:1].upper() + x[1:].lower() for x in q.split("'")) for q in p.split("-")))
    return " ".join(out)


def org(s):
    """Canonical organisation id: 'Org 027' (from 'Org 027', 'Organization 027', 'org 027')."""
    return "Org " + re.search(r"\d+", s).group(0)


def youth(s):
    """Canonical youth id: 'Y045' (from 'Youth 045', 'Y045', 'youth 045', 'y045')."""
    return "Y" + re.search(r"\d+", s).group(0)


def pid(s):
    return "P-" + re.search(r"\d+", s).group(0)


def entity(s):
    """Canonical form of any subject/object entity mention (person, org, youth)."""
    s = s.strip()
    if re.fullmatch(ORG, s):
        return org(s)
    if re.fullmatch(YOUTH, s):
        return youth(s)
    return person(s)


def fact(subject, relation, obj="", qualifiers=()):
    return {"subject": subject, "relation": relation, "object": obj, "qualifiers": list(qualifiers)}


# ---------------------------------------------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------------------------------------------
# First words of a predicate (after the subject). The splitter only cuts a sentence at a connector when the text
# after it is SUBJECT + one of these, so trailing remarks (", and it was a busy day") stay with their clause.
PRED_HEADS = set("""
owns own owned has have recommended recommend recommends suggested helped help helps assisted visited visit visits went
discussed discuss discusses talked mentioned attends attend attended volunteered volunteer currently works work worked
used uses use routinely plans plan likes like genuinely chose choose enjoys enjoy enjoyed dislikes dislike serves serve
buys buy bought is am was are had previously formerly no also still keeps keep said says added explains explained
continued noted concluded often regularly usually always never sometimes once does did shared
""".split())

_ROSTER_START = re.compile(r"[\"“]?the community roster (?:records|lists)\b", re.I)
# a parenthetical between subject and predicate: "O. Usman, on the other hand, attends ..."
PAREN = r"(?:, (?:on the other hand|meanwhile|however|in turn|too|also|in contrast|by contrast|for (?:his|her|their) part),)?"
_SUBJ_FORMS = [
    re.compile(r"[\"“]?(?P<p>%s)(?: and (?P<p2>%s))?%s(?= )" % (PERSON, PERSON, PAREN)),
    re.compile(r"[\"“]?(?:%s|%s)(?= )" % (ORG, YOUTH)),
    re.compile(r"[\"“]?(?P<i>I)(?= )"),
]
# after "I", these verbs introduce a report ("I noted that ...", "I remember X ...") rather than a fact about me
I_REPORT = set("""noted explained said observed added continued concluded stated mentioned remember remembered saw
noticed recorded confirmed watched heard quoted contrasted wrote filed handed was""".split())
_BARE_TAIL = re.compile(r" (?:no longer|don't|do not|does not|did not) ?(?:do|does|go|goes|go there)?\W*$", re.I)


def starts_clause(text):
    """True if `text` begins with a subject (person, 'A and B', org, youth, "I") followed by a predicate head word,
    or with a roster record."""
    if _ROSTER_START.match(text):
        return True
    for rx in _SUBJ_FORMS:
        m = rx.match(text)
        if not m:
            continue
        g = m.groupdict()
        if g.get("p") and not is_person(g["p"]) or g.get("p2") and not is_person(g["p2"]):
            continue
        rest = text[m.end():]
        if _BARE_TAIL.fullmatch(rest):
            continue
        w = re.match(r"(?: (?:both|also))? ([A-Za-z']+)", rest)
        if not w:
            continue
        head = w.group(1).lower()
        if g.get("i") and head in I_REPORT:
            continue
        if head in PRED_HEADS:
            return True
    return False


# connectors between clauses of one sentence
CONNECTORS = [r", and then ", r", and that ", r", and ", r", while ", r", but ", r", whereas ", r"; and ", r"; ", r", ", r" and ",
              r" while ", r" but ", r" whereas ", r": "]
_CONN = re.compile("|".join("(?:%s)" % c for c in CONNECTORS))
# after a connector, a pronoun report may introduce the next clause: ", and she explained that Leah Silva ..."
_PRONOUN_REPORT = re.compile(r"(?:he|she|they|I) (?:also )?(?:(?:explained|said|noted|mentioned|added|confirmed|"
                             r"stated) that|(?:remembered|remember|recalled|know|knew)(?: that)?) ")

QUOTE_CHARS = '"“”'


def _sentence_ends(text):
    """Indices just after each sentence end in text (quotes handled by the caller)."""
    ends = []
    for m in re.finditer(r"[.!?]['\"”]?(?=\s+\S|\s*$)", text):
        i = m.start()
        before = text[:i + 1]
        # initials ("N." in "N. Reed") and "St." in place names are not sentence ends
        if re.search(r"(?:^|[\s\"“(,])[A-Za-z]\.$", before) or re.search(r"\bSt\.$", before):
            continue
        ends.append(m.end())
    return ends


def quote_spans(line):
    """[(start, end)] of quoted spans; end is just after the closing quote (or the end of the line if unclosed)."""
    spans, i, n = [], 0, len(line)
    while i < n:
        ch = line[i]
        if ch in '"“':
            j = i + 1
            while j < n and line[j] not in '"”':
                j += 1
            spans.append((i, min(j + 1, n)))
            i = j + 1
        else:
            i += 1
    return spans


# the frame after a quote: `"...," the speaker explains.` / `"...," Talia Avery said.`
_AFTER_FRAME = re.compile(r"\s*(?:[a-z]+(?: [a-z]+){0,3}|I|%s) (?:also )?[a-z]+(?: (?:in|to|during|for) [a-z' ]+)?"
                          r"[.!?]?(?=\s|$)" % PERSON)


def units(line):
    """Cut a line into units: plain sentences, and quote units (a quoted span with its speaker frame).

    Returns [(text, is_quote)]. Units are consecutive pieces of the line separated by whitespace.
    """
    spans = quote_spans(line)
    out = []
    pos = 0
    for qs, qe in spans:
        # plain text before the quote: sentences; the last (unfinished) piece is the quote's leading frame
        pre = line[pos:qs]
        start = 0
        for e in _sentence_ends(pre):
            s = pre[start:e].strip()
            if s:
                out.append((s, False))
            start = e
        frame_start = pos + start
        end = qe
        quoted = line[qs:qe]
        m = _AFTER_FRAME.match(line[qe:])
        if quoted.rstrip('"”').rstrip().endswith(",") and m:
            end = qe + m.end()
        out.append((line[frame_start:end].strip(), True))
        pos = end
    rest = line[pos:]
    start = 0
    for e in _sentence_ends(rest) + [len(rest)]:
        s = rest[start:e].strip()
        if s:
            out.append((s, False))
        start = e
    return out


# Openers: discourse phrases that introduce a clause. The splitter cuts them off as their own clause (an ignore-rule
# takes the known ones). An opener is text before a clause start that ends with ", ", " that ", ": ", " when ", a
# reporting verb ("The log notes X ...", "I remember X ..."), or is a leading adverb ("Then X ...").
_SAYS = ("records|record|recorded|lists|listed|notes|note|noted|shows|show|showed|states|state|stated|observed|noticed|"
         "remember|remembered|saw|explains|explained|reports|reported|mentions|mentioned|says|said|confirms|confirmed")
_OPENER_END = re.compile(r"(?:, | that | when | after | noting that |: | (?:%s) |^(?:Then|Later|Also|Meanwhile|Nearby|"
                         r"Next|Afterwards|Finally) )" % _SAYS)


def split_opener(sentence):
    """(opener, rest) if the sentence starts with an opener before a clause, else (None, sentence)."""
    if starts_clause(sentence):
        return None, sentence
    for m in re.finditer(r"(?=%s)" % _OPENER_END.pattern, sentence):
        end = _OPENER_END.match(sentence, m.start()).end()
        rest = sentence[end:]
        if sentence[:end].strip() == "I,":     # "I, omar foster, helped ...": a self-introduction
            return None, sentence
        if starts_clause(rest):
            return sentence[:end].rstrip(), rest
    return None, sentence


def split_clauses(sentence):
    """Cut one sentence into clauses at connectors that are followed by a new clause."""
    opener, body = split_opener(sentence)
    out = [opener] if opener else []
    pieces, last = [], 0
    for m in _CONN.finditer(body):
        if m.start() < last:
            continue
        after = body[m.end():]
        if re.fullmatch(PERSON, body[last:m.start()].strip()):
            continue        # "P. Khan and G. Ito both visited ...": a compound subject, not two clauses
        if starts_clause(after):
            pieces.append(body[last:m.start()])
            last = m.end()
            continue
        r = _PRONOUN_REPORT.match(after)
        if r and starts_clause(after[r.end():]):
            pieces.append(body[last:m.start()])
            pieces.append(after[:r.end()].strip())
            last = m.end() + r.end()
    pieces.append(body[last:])
    out.extend(p for p in pieces if p.strip())
    return out


def split_line(line):
    out = []
    for text, is_quote in units(line):
        if is_quote:
            out.append(text)
        else:
            out.extend(split_clauses(text))
    return out


# ---------------------------------------------------------------------------------------------------------------
# Slots: the objects of clauses. Each slot knows the values seen in training; an unseen value still matches if it
# is a short run of words followed by the start of a tail (so new content does not break the grammar).
# ---------------------------------------------------------------------------------------------------------------
PLACES = ["sports hall", "riverside park", "market", "library", "museum"]
GROUPS = ["walking group", "chess club", "history group", "garden circle", "radio society"]
TITLES = ["The Long Orchard", "Atlas of Clouds", "Quiet Machines", "Copper Harbor"]
ITEMS = ["set of garden tools", "garden tools set", "garden tools kit", "garden tools", "sewing kit", "guitar", "camera", "telescope"]
TASKS = ["registration", "setup", "cleanup"]
MODES = ["bus", "subway", "tram", "train", "plane", "car", "bike", "bicycle", "ferry"]
FOODS = ["watermelon", "banana", "pear", "peach", "mango", "apple", "orange", "plum", "lentils", "bread", "rice",
         "yogurt", "milk", "butter", "cheese"]
# words that may follow a discussed topic and name an aspect of it ("market trends", "chess club rules")
ASPECTS = ["trends", "plans", "activities", "rules", "hours", "events", "availability", "conditions", "matters",
           "visits", "exhibits", "schedules", "routes", "improvements", "access", "programming", "membership",
           "strategies", "renovations", "arrangements", "logistics", "operations", "initiatives", "maintenance",
           "attendance", "prices", "needs", "experience", "news", "schedule", "updates", "projects", "history"]

# words that can start the tail after an object (a modifier or a remark)
_TAIL_WORDS = ("some|in|on|at|previously|formerly|recently|once|twice|last|yesterday|today|earlier|later|that|this|"
               "every|only|but|and|to|with|for|during|as|before|after|too|again|also|which|who|where|while|so|"
               "because|when|from|near|nearby|over|about|by|since|until|without|together|there|here|now|lately|instead|"
               "afterwards?|more|used|most|kept|left|which|whose|though|although|even|still|just")
TAIL_START = r"(?=\s*$|[,.;:!?\"”)]| (?:%s)\b| [a-z]+(?:ing|ly)\b)" % _TAIL_WORDS
# a generic value never starts with an -ing word ("mentioned keeping a sewing kit" is not a topic)
# an aspect after a known topic ("market trends", "radio society membership updates"): one or two plain words that
# are not the start of a tail
_PLAIN = r"(?!(?:%s)\b)(?![a-z]+(?:ing|ly)\b)[a-z]+" % _TAIL_WORDS
ASPECT = r"%s(?: %s)?%s" % (_PLAIN, _PLAIN, TAIL_START)
_GENERIC = r"(?![a-z]+ing\b)[A-Za-z][A-Za-z'-]*(?: [A-Za-z][A-Za-z'-]*){0,3}?"


def slot(name, vocab, article=True):
    """Regex for an object slot: optional article, then a known value or a short generic phrase."""
    known = "|".join(re.escape(v) for v in sorted(vocab, key=len, reverse=True))
    art = r"(?:(?:the|a|an|my|his|her|their|our) )?" if article else ""
    # a known value wins at any word end; the tail parser then decides whether what follows is a tail
    return r"%s(?P<%s>(?:%s)(?![\w'-])|%s%s)" % (art, name, known, _GENERIC, TAIL_START)


def obj(text):
    """Canonical object: lowercase, leading article removed, spaces collapsed ('The Long Orchard' -> 'long orchard')."""
    t = re.sub(r"\s+", " ", text.strip().lower())
    t = re.sub(r"^(?:the|a|an|my|his|her|their|our) ", "", t)
    if t in ("garden tools set", "garden tools kit", "set of garden tools"):
        t = "garden tools"
    return t


def topic(text):
    """(topic, aspect) for a discussed thing: 'market trends' -> ('market', 'trends')."""
    t = obj(text)
    words_ = t.split(" ")
    if len(words_) > 1 and words_[-1] in ASPECTS:
        return " ".join(words_[:-1]), words_[-1]
    return t, ""


# ---------------------------------------------------------------------------------------------------------------
# Tails: what follows the object of a clause. Modifiers become qualifiers; anything else must be a remark
# (", which was a busy day", " to the group"), kept as a "note:" qualifier.
# ---------------------------------------------------------------------------------------------------------------
_DAYS = "monday|tuesday|wednesday|thursday|friday|saturday|sunday"
MODIFIERS = [
    (r",? but (?:only )?in the past", ["past"]),
    (r",? but (?:he |she |they |i )?(?:no longer|not anymore|does not attend now|doesn't anymore)"
     r"(?: (?:does|do|attends?|goes|go))?", ["past"]),
    (r",? but (?:does|do) not (?:attend|go) (?:now|anymore)", ["past"]),
    (r" only in the past", ["past"]),
    (r" in the past", ["past"]),
    (r" some time ago", ["past"]),
    (r" a while ago", ["past"]),
    (r" long ago", ["past"]),
    (r" previously", ["past"]),
    (r" formerly", ["past"]),
    (r" in a former role", ["past"]),
    (r" no longer", ["past"]),
    (r" recently", ["time:recently"]),
    (r" (?:yesterday|today|earlier|lately|this morning|this afternoon|this evening|that morning|that afternoon|"
     r"that evening|that day|later that day|later|(?:last|next|this) (?:week|weekend|month|night|year|spring|summer|"
     r"fall|winter)|tomorrow|soon|on (?:%s)|in the (?:morning|afternoon|evening))" % _DAYS, ["time:{m}"]),
    (r" (?:every (?:morning|evening|afternoon|day|week|weekend|month|%s)|on weekends|on (?:%s)s|daily|weekly|"
     r"regularly|often|sometimes|occasionally|twice a (?:week|month)|once a (?:week|month)|most (?:weekdays|days|"
     r"mornings|evenings|weekends)|on the (?:first|second|third|last) (?:%s) of (?:each|every) month)"
     % (_DAYS, _DAYS, _DAYS),
     ["frequency:{m}"]),
    (r" (?:too|as well|again|also)", []),
]
_MODS = [(re.compile(rx, re.I), q) for rx, q in MODIFIERS]
# a remark mentioning these words says the fact is no longer true
_PAST_SIGNALS = re.compile(r"\b(?:no longer|only in the past|has since (?:concluded|ended|stopped)|not anymore|"
                           r"former(?:ly)?|does not (?:attend|go) (?:now|anymore))\b", re.I)
# ("used to" is not a signal in a remark: "a camera, which I used to document the trip")
_REMARK_START = re.compile(r"(?:,|;|:| (?:%s)\b| [a-z]+ing\b| [a-z]+ly\b)" % _TAIL_WORDS, re.I)
_END = re.compile(r"[\s.!?,;:\"'“”]*$")


def strip_end(text):
    return _END.sub("", text)


_HIDDEN = re.compile(r"(?<![\w.])(?=(?P<e>%s|%s|%s)(?P<after>, who\b|(?: (?:both|also|had|simply|only))? "
                     r"(?P<w>[A-Za-z']+)))" % (PERSON, ORG, YOUTH))


def hidden_clause(text):
    """True if a remark contains what looks like another clause: a person/org/youth followed by a predicate head
    word or by ', who'. Such a remark may carry a fact and must not be swallowed as a note."""
    for m in _HIDDEN.finditer(text):
        e = m.group("e")
        if re.fullmatch(PERSON, e) and not is_person(e):
            continue
        if m.group("after").startswith(", who") or (m.group("w") or "").lower() in PRED_HEADS:
            return True
    return False


def tail(text):
    """Qualifiers for the tail of a clause, or None if the tail is not a modifier/remark sequence."""
    rest = strip_end(text)
    quals = []
    while rest:
        for rx, q in _MODS:
            m = rx.match(rest)
            if m and (m.end() == len(rest) or not rest[m.end()].isalnum()):
                quals.extend(x.replace("{m}", m.group(0).strip(" ,").lower()) for x in q)
                rest = rest[m.end():]
                break
        else:
            break
    if rest:
        if not _REMARK_START.match(rest) or hidden_clause(rest):
            return None
        note = rest.strip(" ,;:")
        if _PAST_SIGNALS.search(note) and "past" not in quals:
            quals.append("past")
        quals.append("note:" + note)
    out = []
    for q in quals:
        if q not in out:
            out.append(q)
    return out


SUBJ = r"(?P<subj>I(?= )|%s)%s" % (PERSON, PAREN)


def subject(text):
    """Canonical subject or None if the text is not a subject. 'I' stays 'I' (the composite speech rules replace it
    with the speaker)."""
    text = text.strip().lstrip("\"“")
    if text in ("I", "i"):
        return "I"
    if is_person(text):
        return person(text)
    return None


# ---------------------------------------------------------------------------------------------------------------
# Base class for clause rules: SUBJECT + fixed wording with slots + tail. Abstract (no make()), so the loader does
# not register it as a part.
# ---------------------------------------------------------------------------------------------------------------
from abc import abstractmethod  # noqa: E402

from gram import PatternRule  # noqa: E402


class Core(PatternRule):
    """A clause rule. `pattern` must contain (?P<subj>...) (use SUBJ) and end with (?P<tail>.*).
    make(subject, groups, qualifiers) returns the facts; qualifiers already hold the tail's modifiers."""
    flags = re.I
    subject_kind = "person"      # "person" (or I) | "any" (person, org, youth, I)

    def parse(self, clause):
        # quoted text belongs to the speech rules, which parse its inner clauses with these rules (quotes removed)
        if re.search("[\"“”]", clause):
            return None
        return super().parse(clause)

    def build(self, g):
        if self.subject_kind == "any":
            s = subject(g["subj"]) or (entity(g["subj"]) if re.fullmatch("(?:%s|%s)" % (ORG, YOUTH), g["subj"]) else None)
        else:
            s = subject(g["subj"])
        if s is None:
            return None
        q = tail(g.get("tail", ""))
        if q is None:
            return None
        return self.make(s, g, q)

    @abstractmethod
    def make(self, s, g, q):
        """Return the facts for a matched clause."""


def F(s, rel, o, *quals):
    """fact helper: quals are lists/strings, flattened, empty strings dropped, order kept, no duplicates."""
    out = []
    for q in quals:
        for x in ([q] if isinstance(q, str) else q):
            if x and x not in out:
                out.append(x)
    return {"subject": s, "relation": rel, "object": o, "qualifiers": out}


def lead(g, key, tag):
    """[tag] if the optional group `key` matched, else []."""
    return [tag] if g.get(key) else []
