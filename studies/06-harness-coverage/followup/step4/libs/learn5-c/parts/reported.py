"""Reported speech: a clause that quotes or attributes another clause. The inner claim is parsed by the other rules and
the qualifier 'said' (speaker states it about themself or via he/she) or 'reported' (someone else reports it) is added."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re
from gram import Rule
from common import *

SPEECH = (r"(?:said|says|stated|states|mentioned|noted|notes|suggests|told me|claimed|reported|added|observed|recorded|remarked|explained|explains|"
          r"remember|remembered|recalled|wrote|noticed|state|continued|concluded|agreed|confirmed|saw|quoted the speaker)")
SPEECH_PAST = r"(?:said|says|noted|mentioned|told me|explained|explains|added|remarked|stated|reported|claimed|confirmed)"
Q = "\"“”'"
ASIDE = r"(?:meanwhile|on the other hand|however|in contrast|by contrast|for his part|for her part|for their part|too|in turn)"
_PRES = {"own": "owns", "attend": "attends", "work": "works", "choose": "chooses", "prefer": "prefers", "travel": "travels",
         "like": "likes", "buy": "buys", "serve": "serves", "dislike": "dislikes", "enjoy": "enjoys", "plan": "plans",
         "volunteer": "volunteers", "recommend": "recommends", "visit": "visits", "discuss": "discusses", "help": "helps"}


def first_person(rest, who):
    """'I currently work for Org 3' -> 'Who currently works for Org 3'."""
    rest = re.sub(r",? but I no longer do\b", " but no longer does", rest)
    rest = re.sub(r"\bno longer do\b", "no longer does", rest)
    rest = re.sub(r"^am\b", "is", rest)
    rest = re.sub(r"\bI\b", who, rest)
    m = re.match(r"((?:currently|genuinely|routinely|now|also|still)\s+)?(\w+)\b(.*)", rest)
    if m and m.group(2) in _PRES:
        rest = (m.group(1) or "") + _PRES[m.group(2)] + m.group(3)
    return who + " " + rest


def tag(facts, q):
    if not facts:
        return None
    return [dict(f, qualifiers=list(f.get("qualifiers", [])) + [q]) for f in facts]


class Reported(Rule):
    name = "reported"
    solves = ("reported speech: 'X said, \"I own a camera\"', 'X: \"I ...\"', 'I, X, helped ...', 'X said she owns ...', "
              "'\"...,\" the speaker noted', 'The observer noted that X ...', 'According to the speaker, X ...'; delegates the "
              "inner claim to the other rules and adds qualifier 'said' (speaker about themself) or 'reported' (someone else reports it)")
    added_by = "learning"
    wrapper = True
    examples = [
        ('Amy Roe said, "I own a camera', [fact("Amy Roe", "owns", "camera", ["said"])]),
        ('Amy Roe: "I used to attend the chess club', [fact("Amy Roe", "attends", "chess club", ["past", "said"])]),
        ("Amy Roe said she owns a guitar", [fact("Amy Roe", "owns", "guitar", ["said"])]),
        ('Amy Roe visited the library some time ago," the speaker noted',
         [fact("Amy Roe", "visited", "library", ["past", "reported"])]),
        ("The observer noted that Amy Roe owns a camera", [fact("Amy Roe", "owns", "camera", ["reported"])]),
        ("According to the speaker, Amy Roe owns a camera", [fact("Amy Roe", "owns", "camera", ["reported"])]),
        ("I, Amy Roe, helped with cleanup at the market", [fact("Amy Roe", "helped_with_cleanup", "market", ["said"])]),
        ('Amy Roe said, "I visited the market, and I helped with setup at the museum',
         [fact("Amy Roe", "visited", "market", ["said"]), fact("Amy Roe", "helped_with_setup", "museum", ["said"])]),
    ]

    def parse(self, clause):
        c = clause.strip()
        # speaker said, "I ..." / speaker: "I ..." / speaker wrote in the log, "I ..."
        m = re.fullmatch(r"(?P<s>%s)(?:, %s,)? (?:(?:%s)(?: in (?:the|a|my|our) [a-z ]+?)?,? ?|: ?)[%s]*I (?P<rest>.+)"
                         % (SUBJ, ASIDE, SPEECH, Q), c, re.I)
        if not m:
            m = re.fullmatch(r"(?P<s>%s):\s*[%s]*I (?P<rest>.+)" % (SUBJ, Q), c, re.I)
        if m:
            out = []
            for part in re.split(r",? and I ", m.group("rest")):
                f = delegate(first_person(part, m.group("s")))
                if not f:
                    return None
                out += f
            return tag(out, "said")
        m = re.fullmatch(r"I, (?P<s>%s), (?P<rest>.+)" % SUBJ, c, re.I)
        if m:
            return tag(delegate(m.group("s") + " " + m.group("rest")), "said")
        # speaker said, "<claim about someone>" (no first person)
        m = re.fullmatch(r"(?P<s>%s) (?:%s),? ?[%s]+(?P<rest>(?!I ).+)" % (SUBJ, SPEECH, Q), c, re.I)
        if m:
            f = delegate(re.sub(r"\b(?:me|myself)\b", m.group("s"), m.group("rest")))
            if f:
                return tag(f, "said")
        # speaker said he/she/they ...
        m = re.fullmatch(r"(?P<s>%s)(?:, %s,)? (?:%s) (?:that )?(?:he|she|they) (?P<rest>.+)" % (SUBJ, ASIDE, SPEECH), c, re.I)
        if m:
            return tag(delegate(m.group("s") + " " + m.group("rest")), "said")
        # "<claim>," the speaker noted / she said
        m = re.fullmatch(r"(?P<in>.+?),?[%s]*,? (?:(?:the|a|an|my|our) [a-z ]+?|she|he|they|I|(?P<s2>%s)) (?:%s)" % (Q, SUBJ, SPEECH_PAST), c, re.I)
        if m:
            f = delegate(m.group("in").lstrip(Q))
            same = f and m.group("s2") and all(x["subject"] == subj(m.group("s2")) for x in f)
            return tag(f, "said" if same else "reported")
        # "The observer noted that <claim>", "I noted in the bulletin that <claim>", "According to the speaker, <claim>",
        # "I was filing a form when <claim>", "I quoted the speaker: <claim>"
        m = re.fullmatch(r"(?:[^,\"“]*?\b%s(?: in (?:the|a|my|our) [a-z ]+?)?(?: that)?|According to [^,]+|I quoted the speaker|"
                         r"[^,]*, it was noted that|[^,]*, I noted that|I was [^,]*? when|(?:In|During) [^,]+, I noted(?: that)?),? ?:? ?"
                         r"(?:and that )?(?P<in>.+)" % SPEECH, c, re.I)
        if m:
            return tag(delegate(m.group("in")), "reported")
        return None


class Aside(Rule):
    name = "aside"
    solves = "a clause with an interjection after the subject ('X, meanwhile, visited the library'); the interjection is kept as a qualifier"
    added_by = "learning"
    wrapper = True
    examples = [("Amy Roe, on the other hand, attends the chess club",
                 [fact("Amy Roe", "attends", "chess club", ["on the other hand"])])]

    def parse(self, clause):
        m = re.fullmatch(r"(?P<s>%s), (?P<a>%s),? (?P<rest>.+)" % (SUBJ, ASIDE), clause.strip(), re.I)
        if not m:
            return None
        return tag(delegate(m.group("s") + " " + m.group("rest")), m.group("a").lower())
