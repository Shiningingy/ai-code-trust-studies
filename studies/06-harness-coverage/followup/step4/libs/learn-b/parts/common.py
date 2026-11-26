"""Shared helpers for the parts in this library (not a part itself)."""
import re
from abc import abstractmethod

from gram import Rule

FIRST = ["Amina", "Ben", "Carla", "Dev", "Elena", "Farah", "Gabriel", "Hana", "Isaac", "Jia", "Kofi", "Leah",
         "Mateo", "Nadia", "Omar", "Priya", "Quinn", "Rosa", "Samir", "Talia"]
INITIAL = {}
for _f in FIRST:
    INITIAL.setdefault(_f[0].upper(), []).append(_f)

# a person is "First Last" or "X. Last"; case may be broken (elena Jones, d. bennett)
NAME = r"(?:[A-Za-z]\.|[A-Za-z]{2,})\s+[A-Za-z]{2,}"
ORG = r"(?:Org|Organization)\s+\d+"

# lead-in phrases that carry no meaning
LEAD_NEUTRAL = (r"(?:In a separate update|Elsewhere in the note|Unrelatedly|The same account also says that|"
                r"A recent personal note mentioned that|it came up that|Then|Meanwhile|Later|Also|"
                r"I (?:was|filed)\b[a-z' ]{0,60}?\b(?:when|after))")
# lead-in phrases that report somebody's words (the clause gets qualifier "reported")
LEAD_REPORTED = (r"(?:(?:According to [a-z ]+)|"
                 r"(?:(?:the|my|it was also|i|it was)\s+)?(?:[a-z]+\s+){0,8}?"
                 r"(?:noted|mentioned|observed|explained|stated|recorded|said|says|notes|records?|shows|remember|"
                 r"remembered|reported|wrote|added|quoted|recalled|heard|told|state|states|explains|noticed|saw|know|filed|concluded|agreed|confirmed|contrasted|lists|continued|replied|observes|reports)(?:\s+in [a-z ]+?)?(?:\s+(?:that|the speaker))?\s*[:,]?)")

def person(text):
    """Canonical person name: title case; a lone initial is expanded to the first name when unambiguous."""
    a, b = re.split(r"\s+", text.strip(), maxsplit=1)
    b = b.title()
    if re.fullmatch(r"[A-Za-z]\.", a):
        c = INITIAL.get(a[0].upper(), [])
        a = c[0] if len(c) == 1 else a[0].upper() + "."
    else:
        a = a.title()
    return a + " " + b


def org(text):
    n = re.search(r"\d+", text).group(0)
    return "Org " + n


def fact(s, r, o="", q=None):
    return {"subject": s, "relation": r, "object": o, "qualifiers": list(q or [])}


