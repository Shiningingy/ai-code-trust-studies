"""Shared helpers for the grammar library (not a part itself): name/ID forms, qualifier words, Pred rule base."""
import re
from abc import abstractmethod
from gram import Rule

STOP = {"the", "a", "an", "this", "that", "it", "he", "she", "they", "we", "i", "my", "our", "his", "her", "their",
        "which", "who", "where", "was", "were", "is", "are", "so", "as", "if", "when", "while", "what", "how", "not", "there",
        "though", "although", "whereas", "because", "since", "unless", "until", "yet", "another", "meaning", "previously",
        "kept", "both", "in", "at", "on", "during", "later", "then", "also", "both", "one", "two", "for", "of", "with", "and", "but"}
INIT = r"[A-Za-z]\."
WORD = r"[A-Za-z][A-Za-z']+"
PERSON = r"(?:%s|(?!(?:%s)\b)[A-Za-z][a-z]+) [A-Za-z][A-Za-z'-]+" % (INIT, "|".join(sorted(STOP)))      # "N. Reed", "Nadia Reed", "nadia reed"
YOUTH = r"(?:[Yy]outh \d+|[Yy]\d+)"
ORG = r"(?:[Oo]rg(?:anization)? \d+)"
SUBJ_RX = r"(?:%s|%s|%s)" % (YOUTH, ORG, PERSON)
PERSON_CAP = r"(?:[A-Z]\.|[A-Z][a-z]+) [A-Z][A-Za-z'-]+"
PERSON_ANY = r"(?:[A-Za-z]\.|[A-Za-z]+) [A-Za-z'-]+"
# words that open a predicate: used to recognise where a new clause begins
PRED_START = (r"(?:visited|helped|recommended|owns|discussed|attends|attended|volunteered|currently|works|worked|used|"
              r"routinely|plans|likes|genuinely|chose|chooses|is|dislikes|enjoys|buys|serves|no longer|previously|"
              r"said|says|added|mentioned|noted|wrote|went|talked|attend|own|currently|suggested|assisted|had|explains|explained|has|formerly)")
SPEECH = r"said|says|added|mentioned|noted|wrote|talked|explains|explained"


FACT_PRED = PRED_START.replace("said|says|added|mentioned|noted|wrote|", "").replace("|explains|explained", "")


def fact_shape(clause):
    """True if the clause contains a 'NAME PREDICATE' stretch, i.e. may carry a fact about someone."""
    for m in re.finditer(r"(?<![A-Za-z])(%s) %s\b" % (PERSON_CAP, FACT_PRED), clause):
        w0 = m.group(1).split()[0]
        if w0.lower() not in STOP or w0.endswith("."):
            return True
    if re.match(r"I, ", clause):
        return True
    return bool(re.search(r"(?i)(?:%s|%s) " % (YOUTH, ORG), clause)) or bool(re.search(r"(?i)community roster", clause))


def canon_name(s):
    """Canonical written form of a person/ID: 'c. bennett' -> 'C. Bennett'; 'youth 077'/'Y077' -> 'Y077'."""
    s = " ".join(s.split())
    m = re.fullmatch(r"(?i)(?:youth )?y?\s?(\d+)", s)
    if m and re.match(r"(?i)y", s):
        return "Y" + m.group(1)
    m = re.fullmatch(r"(?i)org(?:anization)? (\d+)", s)
    if m:
        return "Org " + m.group(1)
    return " ".join(w[:1].upper() + w[1:] for w in s.split(" "))


def obj(s):
    """Canonical object text: lowercase, no leading article."""
    s = " ".join(s.split()).lower()
    return re.sub(r"^(?:the|a|an) ", "", s)


def fact(s, r, o="", q=None):
    return {"subject": s, "relation": r, "object": o, "qualifiers": list(q or [])}


MARKER_WORDS = r"\b(?:no longer|in the past|lapsed|ended|as past|concluded|faded|stepped back|not now|previously|former|formerly|used to|since stepped)\b"
PAST_TAIL = (r'(?P<tail>,?\s+(?:a|an|and|so|though|which|also|the|it|he|she|they|his|her|their)\b[^"]*?'
             + MARKER_WORDS + r'[^"]*?)')
ADJ = (r'(?P<adj>,?\s+(?:to|with|for|as|on|at|in|during|every|each|after|before|from|by|near|nearby|last|this|next|that|later|'
       r'and (?!the community)|but|always|probably|before)\b[^,.;"]*'
       r'|,?\s+too|\s+as well|\s+also|\s+now)')
ATTRIB = (r'(?P<att>"?,?"?\s+(?:I|she|he|they|%s|the (?:quoted )?speaker|the report|the observer)(?: in the [a-z ]+)? '
          r'(?:said|noted|added|explained|explains|says|stated|notes)(?: in the [a-z ]+)?\.?)').replace("%s", SUBJ_RX)
MARKER = re.compile(MARKER_WORDS)


NAME_LOOSE = r"(?!(?:he|she|they|it|his|her|their|the|a|an|that|this|we|i)\b)[A-Za-z]+\.? [A-Za-z']+"


def hidden_fact(text):
    """True if adjunct text seems to hide a further fact ('and owns a guitar', 'and that isaac usman used to attend ...')."""
    t = text.strip(" ,")
    if re.match(r"(?i)and\s+(?:that\s+)?(?:%s\s+)?%s\b" % (NAME_LOOSE, PRED_START.replace("|is|", "|").replace("|had|", "|")), t):
        return True
    for m in re.finditer(r"(?<![A-Za-z])(%s) %s\b" % (PERSON_CAP, FACT_PRED), t):
        w0 = m.group(1).split()[0]
        if w0.lower() not in STOP or w0.endswith("."):
            return True
    return False


class Pred(Rule):
    """A rule for 'SUBJECT <predicate>' clauses. Subclasses set `body` (regex for what follows the subject, with
    named groups) and implement facts(subject, g, quals).
    The wrapper accepts an optional speaker frame:  X said, "I <body>"   X said he <body>   X: "I <body>"
    and 'I, X, <body>', a trailing attribution (', the speaker noted.') and a trailing commentary that
    changes the meaning (', a membership that has since lapsed', ', though she is no longer a member')."""
    subj = SUBJ_RX
    body = ""
    _rx = None
    frame_words = (r"said|says|added|mentioned|wrote in the volunteer log|wrote|stated|explained|explains|noted|concluded|continued|"
                   r"agreed|replied|remarked|reported|recalled|notes|states")

    def _compile(self):
        cls = type(self)
        if cls._rx is None:
            S = self.subj
            cls._rx = re.compile(
                r'["]?(?:(?P<sp>%s)(?: (?:%s)(?: that)?,?|:) ["]?(?:I|he|she|they) |(?P<s0>%s) (?:(?:also|simply|just|still|even) )?|I, (?P<s1>%s), )'
                r'(?:%s)(?:%s)?(?:%s)?[.,]?["]?(?:%s)?' % (S, self.frame_words, S, S, self.body, ADJ, PAST_TAIL, ATTRIB), 0)
        return cls._rx

    def parse(self, clause):
        rx = self._compile()
        m = rx.fullmatch(clause.strip())
        if not m:
            return None
        g = {k: v for k, v in m.groupdict().items() if v}
        quals = []
        if g.get("sp"):
            subj = canon_name(g["sp"])
            quals.append("said")
        elif g.get("s0"):
            subj = canon_name(g["s0"])
        elif g.get("s1"):
            subj = canon_name(g["s1"])
        else:
            return None
        if g.get("att"):
            quals.append("said")
        if g.get("adj") and hidden_fact(g["adj"]):
            return None
        if g.get("tail") and hidden_fact(g["tail"]):
            return None
        out = self.facts(subj, g, quals)
        if out and g.get("adj"):
            for f in out:
                f["qualifiers"].append("detail: " + " ".join(g["adj"].split()))
                if MARKER.search(g["adj"]) and "past" not in f["qualifiers"]:
                    f["qualifiers"].append("past")
        if out and g.get("tail") and MARKER.search(g["tail"]):
            for f in out:
                for w in (["past"] + (["no_longer"] if "no longer" in g["tail"] else [])):
                    if w not in f["qualifiers"]:
                        f["qualifiers"].append(w)
        return out

    @abstractmethod
    def facts(self, subj, g, quals):
        """Facts for the matched clause."""
