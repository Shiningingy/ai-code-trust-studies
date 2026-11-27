"""Wrapper rules: clauses whose fact sits inside some other wording. Each finds the inner clause and delegates it to the
ordinary rules (see common.delegate), so a construction is only ever defined once."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re
from gram import Rule
from common import *

CUE = (r"\b(?:owns?|has|keeps?|attends?|attended|visited|visits?|recommended|suggested|discussed|helped|helping|volunteered|"
       r"works|worked|travels|travelled|traveled|enjoys|avoids?|guardian|contact|skipping|dislikes|buys|serves|prefers|likes|chose|"
       r"plans to|took part|roster|based in|member|subway|tram|train|shift|currently|used to|no longer)\b")
SAYING = (r"\b(?:said|says|noted|explained|explains|stated|states|mentioned|saw|noticed|observed|remember(?:ed)?|records?|"
          r"shows?|reports?|confirmed|learned|watched|continued|concluded|added|agreed|wrote|told|heard|recalled)\b")


def tag(facts, q):
    if not facts:
        return None
    return [dict(f, qualifiers=list(f.get("qualifiers", [])) + ([q] if q else [])) for f in facts]


class Embedded(Rule):
    name = "embedded"
    solves = ("a claim introduced by narration or attribution ('I saw X visit the library', 'The record shows that X ...', "
              "'I was filing a form when X ...'); the inner clause is parsed normally, 'reported' is added when the opening names a source")
    added_by = "learning"
    wrapper = True
    examples = [("Then Amy Roe recommended Quiet Machines", [fact("Amy Roe", "recommended", "quiet machines")]),
                ("I, Quinn Silva, can confirm the community roster records me under identifier P-117",
                 [fact("Quinn Silva", "has_id", "P-117", ["reported"])])]

    def parse(self, clause):
        c = clause.strip()
        m = re.fullmatch(r"I, (?P<s>%s), (?:can )?(?:confirm|state|say|attest)s? (?:that )?(?P<in>.+)" % SUBJ, c, re.I)
        if m:
            inner = re.sub(r"\b(?:me|myself)\b", m.group("s"), m.group("in"))
            return tag(delegate(inner), "reported")
        if delegate(c) is not None or any(w.parse(c) is not None for w in other_wrappers(self.name)):
            return None
        for mm in re.finditer(r"(?<=[ \"“”'])(?=\S)", c):
            k = mm.end()
            pre, cand = c[:k], c[k:].lstrip("\"“”'")
            if not pre.strip() or re.search(CUE, pre, re.I):
                continue
            if not re.match(r"(?:I|The|This|Our|My|Meeting|Then|Also|Later|Meanwhile|Afterwards|In|During|While|For|At|After|According|It|"
                            r"Both|Unlike|That|Nearby|Additionally)\b", pre):
                continue
            f = delegate(cand)
            if f:
                return tag(f, "reported" if re.search(SAYING, pre, re.I) else None)
        return None


class SharedSubject(Rule):
    name = "shared_subject"
    solves = "'X visited the museum and owns a guitar' / 'X and Y both visited the market': one subject for two predicates, or two subjects for one"
    added_by = "learning"
    wrapper = True
    examples = [("Amy Roe visited the museum and owns a guitar",
                 [fact("Amy Roe", "visited", "museum"), fact("Amy Roe", "owns", "guitar")]),
                ("Amy Roe and Ben Lee both visited the market previously",
                 [fact("Amy Roe", "visited", "market", ["past"]), fact("Ben Lee", "visited", "market", ["past"])])]

    def parse(self, clause):
        c = clause.strip()
        m = re.fullmatch(r"(?P<s1>%s) and (?P<s2>%s) both (?P<rest>.+)" % (SUBJ, SUBJ), c, re.I)
        if m:
            a, b = delegate(m.group("s1") + " " + m.group("rest")), delegate(m.group("s2") + " " + m.group("rest"))
            return (a + b) if a and b else None
        m = re.match(r"(?P<s>%s) " % SUBJ, c, re.I)
        if not m:
            return None
        for sp in re.finditer(r",? and (?:(?:she|he|they) )?(?:also |later |then )?(?=(?:owns|has|visited|attends|helped|discussed|recommended|works|"
                              r"volunteered|enjoys|used to|no longer|took part|currently|routinely|chose|likes|prefers)\b)", c):
            a, b = delegate(c[:sp.start()]), delegate(m.group("s") + " " + c[sp.end():])
            if a and b:
                return a + b
        return None


class Relative(Rule):
    name = "relative"
    solves = "'X, who works for Org 3, mentioned it' / 'X who owns a guitar': a relative clause carrying a claim about X"
    added_by = "learning"
    wrapper = True
    examples = [("Amy Roe, who currently works for Org 018, mentioned it during our chat",
                 [fact("Amy Roe", "works_for", "Org 018", ["current"])])]

    def parse(self, clause):
        m = re.fullmatch(r"(?:[A-Za-z ]+? (?:from|to|with|unlike) )?(?P<s>%s),? who (?P<rest>[^,]+?)(?:,.*)?" % SUBJ, clause.strip(), re.I)
        if not m:
            return None
        return tag(delegate(m.group("s") + " " + m.group("rest")), "contrast" if False else None)
