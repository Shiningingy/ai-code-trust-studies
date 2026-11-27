"""Shared vocabulary and helpers for the library's parts (not a part itself)."""
import re

# person written as "Hana Ortiz", "H. Ortiz", "hana ortiz", "ortiz" (case and first-name drift occur)
_STOP = (r"I|we|he|she|they|it|the|this|that|then|there|also|later|only|used|simply|still|just|who|which|and|but|so|as|when|"
         r"while|where|his|her|their|its|a|an|both|each|every|one|some|many|another|afterwards|meanwhile|too|even|please")
PERSON = (r"(?:[A-Za-z]\. [A-Za-z]+(?:-[A-Za-z]+)?|[A-Za-z]+ (?!(?:only|simply|also|just|still|used|later|even|who|and|but|then)\b)[A-Za-z]+|[A-Za-z]+)")
CAPPERSON = r"(?:[A-Z]\.? [A-Z][a-z]+|[A-Z][a-z]+ [A-Z][a-z]+)"
YOUTH = r"(?:[Yy]outh \d+|[Yy]\d+)"
SUBJ = r"(?:%s|(?!(?:%s)\b(?!\.))%s)" % (YOUTH, _STOP, PERSON)

PLACES = r"market|library|museum|riverside park|sports hall"
GROUPS = r"walking group|chess club|history group|radio society|garden circle"
ITEMS = r"camera|garden tools|telescope|guitar|sewing kit"
MODES = r"subway|bus|train|tram|plane|car|bicycle|bike|ferry|metro|taxi"
FRUITS = "apple banana pear mango plum peach orange watermelon".split()
DAIRY = "milk cheese butter yogurt".split()

ADV = (r"every \w+|regularly|on (?:mon|tues|wednes|thurs|fri|satur|sun)days?|on weekends?|on weekdays|on (?:monday|tuesday|wednesday|"
       r"thursday|friday|saturday|sunday)|now|recently|last (?:week|month|year|weekend|night|time)|too|yesterday|instead|more recently|"
       r"as well|today|again|this (?:morning|week|month|afternoon|evening)|often|usually|sometimes|each (?:day|week|month|morning)|"
       r"daily|weekly|nearby|earlier|later(?: that \w+)?")
FACTVERB = r"(?:owns?|attends?|visited|recommended|discussed|helped|volunteered|works|worked|travels|enjoys)"
_SPEECH_END = r"(?!.*(?<![-\w])(?:said|told me|mentioned|noted|explained|explains|says|stated|added|confirmed|claimed|reported|remarked)\s*$)"
_AUX = r"(?:we|us|I|which|who|that|it|now|have|has|been|was|were|is|ever|had|are|well|kept|since)"
_NOFACT = r"(?!.*\b(?!" + _AUX + r"\b)\w+ " + FACTVERB + r"\b)"


def person(s):
    """Canonical text of a person: title case, initials as 'H. Ortiz'."""
    s = s.strip()
    m = re.fullmatch(r"([A-Za-z])\. (.+)", s)
    if m:
        return "%s. %s" % (m.group(1).upper(), m.group(2).title())
    return " ".join(w[:1].upper() + w[1:].lower() for w in s.split())


def youth(s):
    m = re.search(r"(\d+)", s)
    return "Youth %d" % int(m.group(1))


def subj(s):
    return youth(s) if re.fullmatch(YOUTH, s.strip()) else person(s)


def org(s):
    return "Org %s" % re.search(r"\d+", s).group(0)


def fact(s, r, o="", q=None):
    return {"subject": s, "relation": r, "object": o, "qualifiers": list(q or [])}


def all_rules():
    """Every concrete Rule in this library's loaded modules except the delegating wrappers (name -> instance)."""
    from gram import Rule
    seen, stack, out = set(), list(Rule.__subclasses__()), {}
    while stack:
        c = stack.pop()
        stack.extend(c.__subclasses__())
        if (c.__module__.startswith("gramlib_") and c.name and not getattr(c, "wrapper", False)
                and not getattr(c, "__abstractmethods__", None) and c.name not in seen):
            seen.add(c.name)
            out[c.name] = c()
    return list(out.values())


_CACHE = {}


def delegate(clause):
    """Parse `clause` with the non-wrapper rules; returns the facts if exactly one distinct reading, else None."""
    import json
    if not _CACHE.get("rules"):
        _CACHE["rules"] = all_rules()
    res = {}
    for r in _CACHE["rules"]:
        f = r.parse(clause)
        if f is not None:
            res[json.dumps(f, sort_keys=True)] = f
    return next(iter(res.values())) if len(res) == 1 else None


def advq(tail):
    """Qualifier for a short time/frequency adverb at the start of a clause's trailing words (e.g. 'every Tuesday')."""
    if not tail:
        return []
    m = re.match(r"(%s)\b" % ADV, tail.strip(" ,;-"), re.I)
    return [m.group(1).lower()] if m else []


def tailq(tail):
    """advq plus 'past' when the trailing words say the thing is over (in the past, lapsed, no longer, not a member)."""
    if not tail:
        return []
    q = advq(tail)
    if re.search(r"\b(?:in the past|lapsed|no longer|since ended|has ended|not a member|some time ago|formerly)\b", tail, re.I):
        q = ["past"] + q
    return q


TAIL = (r"(?P<tail>(?:(?:,|;|\s+-)\s*" + _SPEECH_END + _NOFACT + r".+|"
        r"\s+" + _SPEECH_END + _NOFACT +
        r"(?:(?:" + ADV + r")\b.*|(?:which|where|so|though|having|while|ensuring|highlighting|that|because|since|bringing|adding|"
        r"including|noting|making|offering|sharing|showing|leaving|then|but|only|also|outlining|providing|guiding|meaning|"
        r"previously|another|who|many|rather|unlike|and (?:she|he|they|it|we|I|the|his|her|their)|"
        r"(?:a|an|the|one|his|her|their|it|this) (?:[a-z]+ ){0,3}(?:that|which|who|where|of)|"
        r"(?:in|at|for|during|with|to) (?:the|a|an|my|our) [a-z ]+|to work|as (?:a|an) [a-z -]+)\b.*)))?")


TAILX = (r"(?P<tail>(?:(?:,|;|\s+-)\s*" + _SPEECH_END + _NOFACT + r".+|"
         r"\s+" + _SPEECH_END + _NOFACT + r".+))?")
# TAIL: for rules whose object is open vocabulary (book titles, items): only recognisable flavour openers may follow it.
# TAILX: for rules whose object is a closed vocabulary (place, group, org, mode...): any trailing words may follow.


# EXTRA: a short adjunct after an open-vocabulary object ("... to anyone looking", "... for reading", "... and plays it")
EXTRA = r"(?P<x> (?:to|for|with|afterward|used|and|we|at|in|on|during|after|before|because)\b" + _SPEECH_END + _NOFACT + r".*)?"


def other_wrappers(me):
    """Instances of the wrapper rules other than `me` (a wrapper that is only a fallback defers to them)."""
    from gram import Rule
    out, stack, seen = [], list(Rule.__subclasses__()), set()
    while stack:
        c = stack.pop()
        stack.extend(c.__subclasses__())
        if (c.__module__.startswith("gramlib_") and getattr(c, "wrapper", False) and c.name and c.name != me
                and c.name not in seen and not getattr(c, "__abstractmethods__", None)):
            seen.add(c.name)
            out.append(c())
    return out
