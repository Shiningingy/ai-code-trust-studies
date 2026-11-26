import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import FIRST  # noqa: E402
from gram import Splitter, Normalizer  # noqa: E402

# meaning-bearing tails that must stay inside the clause they belong to
TAIL = (r"(?:(?:but |though |also )?(?:only )?(?:no longer do(?:es)?|that is in the past|which was in the past|"
        r"which is in the past|in the past|only in the past|that was in the past|(?:he |she |they |i )?no longer (?:do|does))|"
        r"a membership that has since lapsed|(?:but )?(?:that|it) is (?:in the past now|no longer the case)|but does not attend now|that is a current commitment|not a guardian|for (?:youth\s*|y)\d+)")
# introductory phrases that only set a scene; they are dropped as connectors
INTRO = (r"(?:in contrast|meanwhile|later|earlier|afterwards|nearby|also|then|additionally|however|elsewhere[^,.;]{0,40}|unrelatedly|separately|"
         r"(?:in|during|at|after|before|on|by|within)\b[^,.;]{0,70})\s*,?")
NAMEISH = r"(?:(?:%s)|[A-Za-z]\.)\s+[A-Za-z]{2,}" % "|".join(FIRST)
SAYING = r".*\b(?:said|says|stated|noted|explained|added|wrote|remarked|mentioned|shared|recalled|replied|continued|concluded|agreed|observed|explains|explain|wrote in [a-z ]+)[,:]?"


class ClauseSplitter(Splitter):
    name = "clause_splitter"
    solves = ("cuts a line into sentences, then into clauses at commas, semicolons and ' and <Name>'; drops the connectors "
              "and/while/but/whereas/so and scene-setting intros ('In contrast,'), keeps lead-ins like 'The same account "
              "also says that' and meaning-bearing tails ('but no longer does') inside their clause")
    added_by = "learning"
    droppable = [r"[,;:\s]*(?:(?:and|while|but|whereas|so)\b[,\s]*)?", INTRO + r"[,;:\s]*"]
    examples = [("A. Owns owns a camera, and B. Owns visited the market.",
                 ["A. Owns owns a camera", "B. Owns visited the market."]),
                ("In contrast, Ben Ito used to attend the chess club, but no longer does.",
                 ["Ben Ito used to attend the chess club, but no longer does."])]

    def split(self, line):
        cuts = []
        prot = [(m.start(), m.end()) for m in re.finditer(r"\bI,\s+%s,\s" % NAMEISH, line, re.I)]
        for m in re.finditer(r'(?<=[.!?])["”]?\s+|(?<=[,;])["”]?\s+|,["”]\s+|'
                             r'\s+and\s+(?=%s\b)' % NAMEISH, line, re.I):
            s = m.start()
            if any(a < s < b for a, b in prot):
                continue
            if re.search(r"(?:^|[\s\"“(])(?:[A-Za-z]|St)\.$", line[:s]) and line[s - 1] == ".":
                continue
            if line[s:m.end()][:1] in ('"', "”"):
                s += 1
            cuts.append((s, m.end()))
        pieces, start = [], 0
        for s, e in cuts:
            pieces.append((start, s))
            start = e
        pieces.append((start, len(line)))
        pieces = [(a, b) for a, b in pieces if line[a:b].strip(" ,;")]
        out = []
        for a, b in pieces:
            t = line[a:b]
            body = re.sub(r"^(?:and|while|but|whereas|so)\s+", "", t, flags=re.I)
            if out:
                pa, pb = out[-1]
                prev = line[pa:pb].strip()
                if re.fullmatch(TAIL + r"[\s.,\"”]*", t.strip(), re.I) or re.fullmatch(TAIL + r"[\s.,\"”]*", body.strip(), re.I):
                    out[-1] = (pa, b)
                    continue
                if (re.fullmatch(SAYING, prev, re.I) and not re.search(r"[.!?]\"?$", prev)) or \
                        re.fullmatch(r"according to [a-z ]+,?", prev, re.I):
                    out[-1] = (pa, b)
                    continue
            out.append((a, b))
        res = []
        for a, b in out:
            t = line[a:b]
            if re.fullmatch(INTRO, t.strip(), re.I) and t.strip().endswith(",") and not re.match(r"according", t, re.I):
                continue
            m = re.match(r"(?:and|while|but|whereas|so)\s+", t, re.I)
            if m:
                a += m.end()
            res.append(line[a:b])
        return [c.rstrip(" ,;") if c.rstrip(" ,;") else c for c in res]


class StraightQuotes(Normalizer):
    name = "straight_quotes"
    solves = "replaces curly quotes and apostrophes by straight ones so rules see one quote form"
    added_by = "learning"
    examples = [("“A owns a camera,”", '"A owns a camera,"')]

    def apply(self, clause):
        return clause.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
