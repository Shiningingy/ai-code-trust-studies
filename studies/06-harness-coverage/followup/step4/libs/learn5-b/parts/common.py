"""Shared fragments and helpers for the library parts (not a part itself; defines no Rule/Splitter/Normalizer).

Parts import it with:  sys.path.insert(0, os.path.dirname(__file__)); from common import ...
"""
import re

# ---------------------------------------------------------------- entities
INITIAL = r"[A-Za-z]\."
FIRST = r"[A-Z][a-z]+"
SURNAME = r"[A-Z][a-z]+"
NAME = r"(?:%s|%s) %s" % (INITIAL, FIRST, SURNAME)          # "E. Patel", "Hana Ortiz" (after the case normalizer)
ORG = r"(?:Org|Organization) \d+"
YOUTH = r"(?:Youth \d+|Y\d+)"
PID = r"[Pp]-\d+"
EVENT = r"(?:old-)?event-[Pp]-\d+(?:-\d+)?|old-event-[Pp]-\d+"

# first words after a person's name that start a predicate; used to find where a name ends in a clause
VERBS = (r"owns|own|recommended|recommend|suggested|discussed|talked|visited|went|attends|attend|attended|helped|volunteered|volunteer|"
         r"currently|works|work|worked|used|plans|routinely|routinely|traveled|travelled|travels|enjoys|enjoy|dislikes|dislike|likes|like|"
         r"genuinely|prefers|prefer|chose|is|am|was|took|buys|buy|serves|serve|previously|says|said|explains|explained|wrote|"
         r"records|keeps|only|also|no|does|did|has|had|likes|skips|avoids|avoid|teaches|taught|participated|joined|"
         r"mentioned|noted|stated|added|continued|remarked|reported|shared|attends")
VERB_RX = r"(?:%s)\b" % VERBS

PLACES = r"market|library|museum|sports hall|riverside park"
CLUBS = r"walking group|history group|chess club|garden circle|radio society"
TRANSIT = r"bus|train|tram|subway"
DAIRY = r"cheese|yogurt|milk|butter"


def canon_name(s):
    """'talia usman' -> 'Talia Usman', 'c. patel' -> 'C. Patel'."""
    return " ".join(w[:1].upper() + w[1:].lower() if not w.endswith(".") else w.upper() for w in s.split())


def canon_org(s):
    """'Organization 007' / 'org 007' -> 'Org 007'."""
    return "Org " + re.search(r"\d+", s).group(0)


def canon_youth(s):
    """'Y037' / 'Youth 037' -> 'Youth 037'."""
    return "Youth " + re.search(r"\d+", s).group(0)


def canon_pid(s):
    return "P-" + re.search(r"\d+", s).group(0)


def fact(subject, relation, obj="", quals=()):
    return {"subject": subject, "relation": relation, "object": obj, "qualifiers": list(quals)}


# a run of words that stops before a preposition/relative word, so descriptive adjuncts are not swallowed into an object
OBJWORDS = r"(?:(?!(?:with|to|for|as|during|in|on|at|after|before|that|which|when|and|but|so|because|by|from|while)(?![A-Za-z']))[A-Za-z']+(?: |(?=$)))+"

THINGS = r"telescope|camera|guitar|sewing kit|garden tools"
BOOKS = r"quiet machines|atlas of clouds|copper harbor|the long orchard"
TITLE = r"[A-Z][a-z']+(?: (?:of|the|and|a|in|on|for|to) [A-Z][a-z']+| [A-Z][a-z']+)*"   # a capitalised title not in the lexicon
