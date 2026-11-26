"""Shared helpers for the parts of this library (not a part itself): vocabulary regexes and canonical forms."""
import re

# ---- surface vocabulary -------------------------------------------------------------------------------------
PRON = r"(?:I|we|he|she|they)"
# a person written as "First Last", "F. Last" (any case); never an org / youth identifier
NAME = r"(?!(?:org|organization|youth|the|a|an|in|i|he|she|they|we|it|this|that|then|there|so|and|but|who|which|what|when|where|after|before|while|my|our|his|her|their|its|later|also|both|as|at|on|for|during|one|said|says|because|does|did|not|is|are|was|were|has|have|had|will|would|can|could|should|may|might|must|if|since|until|though|although|than|with|without|of|to|by|from|about|into|over|under|no|never|often|still|just|simply|all|each|some|many|several)\s)[A-Za-z][\w'-]*\.?\s+[A-Za-z][\w'-]*"
YOUTH = r"(?:[Yy]outh\s+|[Yy])\d+"
ORG = r"(?:[Oo]rg(?:anization)?)\s+\d+"
SUBJ = r"(?:%s|%s|%s)" % (YOUTH, NAME, PRON)

# words that mark the start of a fact; used to refuse "ignore" and to detect clause starts
ANCHOR = (r"(?:owns?|recommended|discussed|talked|visited|went|attend\w*|helped|help|assisted|volunteered|works?|worked|"
          r"used|routinely|travels?|plans?|prefers?|chose|likes?|enjoys?|dislikes?|avoids?|avoid|skipping|buys|serves|"
          r"guardian|emergency|roster|based|currently|no longer|genuinely|only|is|are|was|chooses?|choose)")

CITY_ABBR = ("st.", "mt.", "ft.")


def canon_name(s):
    return " ".join(w[:1].upper() + w[1:].lower() for w in s.split())


def canon_youth(s):
    return "Y" + re.search(r"\d+", s).group(0)


def canon_org(s):
    return "Org " + re.search(r"\d+", s).group(0)


def canon_pid(s):
    return "P-" + re.search(r"\d+", s).group(0)


def canon_subject(s):
    if re.fullmatch(YOUTH, s.strip()):
        return canon_youth(s)
    return canon_name(s.strip())


def low(s):
    s = re.sub(r"\s+", " ", s.strip().lower())
    return re.sub(r"^(?:the|a|an)\s+", "", s)


# Entities seen in the training documents. A noun-phrase object that starts with one of these (e.g. "museum exhibits",
# "atlas of clouds afterward") is reduced to the entity, so facts about the same thing join. Unknown objects stay as written.
KNOWN_ENTITIES = [
    "market", "museum", "library", "sports hall", "riverside park",
    "walking group", "chess club", "history group", "garden circle", "radio society",
    "quiet machines", "copper harbor", "atlas of clouds", "the long orchard", "long orchard",
    "camera", "telescope", "garden tools", "guitar", "sewing kit",
]


def ent(s):
    s = low(s)
    for e in sorted(KNOWN_ENTITIES, key=len, reverse=True):
        e = low(e)
        if s == e or s.startswith(e + " "):
            return e
    return s


def who(g):
    """Subject of a clause: the named person, or the speaker when the clause says I / he / she."""
    if g.get("ap"):
        return canon_subject(g["ap"])
    s = g.get("s", "").strip()
    if re.fullmatch(PRON, s, re.I):
        sp = g.get("sp", "").strip()
        return canon_subject(sp) if sp else None
    return canon_subject(s)


# ---- qualifiers --------------------------------------------------------------------------------------------
TIME_Q = [
    r"some time ago", r"only in the past", r"in the past", r"previously", r"recently", r"more recently",
    r"last week", r"last weekend", r"last year", r"later that day", r"formerly", r"once", r"no longer",
    r"regularly", r"every week", r"every \w+ (?:evening|morning)", r"every \w+day", r"on \w+days", r"on weekends",
    r"weekly", r"daily", r"often", r"occasionally", r"sometimes", r"too", r"as well", r"in a former role",
    r"as past", r"lapsed", r"since ended", r"former", r"currently", r"temporarily", r"in the future", r"only because of a disruption", r"because of a disruption",
    r"but only in the past", r"also only in the past", r"no longer does", r"but no longer does",
]
TIME_RX = re.compile(r"\b(" + "|".join(TIME_Q) + r")\b", re.I)
QUAL_KEEP = {"some time ago", "only in the past", "in the past", "previously", "recently", "more recently", "last week",
             "last weekend", "last year", "later that day", "formerly", "once", "no longer", "regularly", "every week",
             "weekly", "daily", "often", "occasionally", "sometimes", "on weekends", "in a former role", "currently",
             "temporarily", "in the future", "only because of a disruption"}


def tail_quals(text):
    """Qualifier words found in free text, normalised (lower case, no duplicates, order of appearance)."""
    out = []
    for m in TIME_RX.finditer(text or ""):
        q = m.group(1).lower()
        if q in ("but only in the past", "also only in the past"):
            q = "only in the past"
        if q in ("no longer does", "but no longer does"):
            q = "no longer"
        if q == "because of a disruption":
            q = "only because of a disruption"
        if q in ("as past", "lapsed", "since ended"):
            q = "no longer" if q != "as past" else "in the past"
        if q == "former":
            q = "formerly"
        if q in ("too", "as well"):
            continue
        if q == "in the past" and "only in the past" in out:
            continue
        if q not in out:
            out.append(q)
    return out


def has_fact_words(text):
    return bool(re.search(r"\b" + ANCHOR + r"\b", text or "", re.I))


def fact(s, rel, obj="", quals=()):
    return {"subject": s, "relation": rel, "object": obj, "qualifiers": list(quals)}


# ---- pattern building blocks ----------------------------------------------------------------------------------
QCH = "\"“”�"
SAY = r"(?:said|says|mentioned|concluded|continued|explained|explains|added|stated|replied|noted|agreed|answered|remarked|commented|responded|wrote[^%s,]*|told[^%s,]*)" % (QCH, QCH)
# optional quote introduction: 'T. Tran said, "' / 'Y023 said, "' / 'N. Reed: "' (the speaker is group sp)
PRE = r"(?:(?P<sp>%s)\s*(?:%s\s*[,:]?|:)\s*(?:that\s+)?[%s]*\s*)?" % (SUBJ, SAY, QCH)

STARTERS = (r"some time ago|in|previously|recently|last|later|too|also|as|to|for|with|during|after|before|at|on|every|"
            r"regularly|weekly|daily|nearby|now|again|set|but|only|so|that|which|where|and|though|since|because|when|"
            r"while|once|often|occasionally|sometimes|formerly|from|about|together|early|this|yesterday|today|"
            r"activities|events|trends|conditions|plans|visits|schedules|matters|hours|improvements|operations|"
            r"logistics|routes|access")
TAIL = r"(?P<tail>(?:(?:\s*,\s*|\s+)(?:%s)\b.*)?)" % STARTERS

BLOCK = re.compile(r"\b(?:owns?|recommended|discussed|visited|attend\w*|helped|volunteered|works?\s+(?:for|the|a)|"
                   r"routinely|prefers?|avoid\w*|skipping|buys|guardian|chose)\b", re.I)


def pat(body):
    return PRE + r"(?:(?P<s>%s)|(?P<s0>I),\s*(?P<ap>%s),)\s+" % (SUBJ, NAME) + body


def quals_of(g, *extra):
    q = list(extra)
    for x in tail_quals(g.get("tail", "")):
        if x not in q:
            q.append(x)
    return q


def tail_ok(g):
    return not BLOCK.search(g.get("tail", ""))


def mk(g, rel, obj="", *extra):
    s = who(g)
    if s is None or not tail_ok(g):
        return None
    return [fact(s, rel, obj, quals_of(g, *extra))]
