import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import FIRST, SURNAMES  # noqa: E402
from gram import Splitter  # noqa: E402

Q = r"[\"“”]"
NQ = r"[^\s\"“”]"
WHO = r"(?: [a-z]|,? who )"
# a clause starts with a person, "I", the roster phrase, an org or a youth id
KNOWN = r"(?i:(?:%s|[a-z]\.) (?:%s))(?:(?-i: [a-z])|,? who )" % ("|".join(FIRST), "|".join(SURNAMES))
_STARTS = [r"(?:[A-Za-z]\.|[A-Z][a-z]+) [A-Z][a-z]+" + WHO, KNOWN, r"I[ ,](?!was )", r"[Tt]he community roster",
           r"[Oo]rg(?:anization)? \d", r"Youth \d", r"Y\d{3}"]
START = "(?:" + "|".join(Q + "?" + x for x in _STARTS) + ")"
# a person that starts a new statement right after a linking phrase inside a sentence
LINK = (r"(?:(?:in )?contrast to|different from(?: how| the fact that| what)?|unlike|noting that|explaining that|"
        r"explained that|turned to|and that) ")
SENT = re.compile(r"(?<=[.!?])(?<!\bSt\.)(?<!(?<!%s)[A-Za-z]\.)%s? +(?=%s?[A-Za-z])|(?<=[.!?]%s) +(?=[A-Za-z\"“])" % (NQ, Q, Q, Q))
COMMA = re.compile(r"(?:[,;]%s? (?:(?:and|but|while|whereas|though) (?:that )?)?| and )(?=(?!\S+ \S+ both )%s)" % (Q, START))
LINKED = re.compile(r"%s(?=%s)" % (LINK, START))
WHO_NAME = re.compile(r"(?<= )(?=%s?(?:[A-Za-z]\.|[A-Z][a-z]+) [A-Z][a-z]+,? who )" % Q)
QUOTE = "[\"“”]"


class SentenceClauseSplitter(Splitter):
    name = "sentence_clause"
    solves = ("cuts a line into sentences and into the clauses joined by ', and' / ', but' / ';' / commas in a list, and "
              "before a person introduced by a linking phrase ('in contrast to X, who ...', 'noting that X ...'); each "
              "clause starts with a person, 'I', the roster phrase or an org/youth mention. Openers such as "
              "'In a separate update,' stay inside the clause (rules read them as qualifiers). Inside a quotation "
              "', and I ...' is not cut, so the speaker stays attached.")
    added_by = "learning"
    droppable = [r"[,;\s]*(?:(?:and|but|while|whereas|though)\s*)?(?:that\s*)?", r"[\"“”,\s]*(?:(?:and|but|while|whereas|though)\s*)?"]
    examples = [
        ("Priya Jones recommended Copper Harbor, and D. Diaz helped with cleanup at the museum.",
         ["Priya Jones recommended Copper Harbor", "D. Diaz helped with cleanup at the museum."]),
        ("Org 003 is based in St. John's. Hana Ortiz owns a camera.",
         ["Org 003 is based in St. John's.", "Hana Ortiz owns a camera."]),
        ("In a separate update, j. Foster owns a garden tools. Elsewhere in the note, nadia Ortiz visited the market.",
         ["In a separate update, j. Foster owns a garden tools.", "Elsewhere in the note, nadia Ortiz visited the market."]),
        ("L. Evans owns a guitar, which is a nice contrast to Q. Patel, who attends the walking group.",
         ["L. Evans owns a guitar, which is a nice contrast to ", "Q. Patel, who attends the walking group."]),
    ]

    def split(self, line):
        sents, pos = [], 0
        for m in SENT.finditer(line):
            sents.append(line[pos:m.start()])
            pos = m.end()
        sents.append(line[pos:])
        out = []
        parity = 0       # 1 while inside an open quotation
        for s in sents:
            start_parity = parity
            parity = (parity + len(re.findall(QUOTE, s))) % 2
            cuts = []    # (start of the dropped connector, end of it)
            for m in COMMA.finditer(s):
                inside = (start_parity + len(re.findall(QUOTE, s[:m.start()]))) % 2
                nxt = s[m.end():]
                if inside and re.match(r"I (?!(?:also )?(?:remember|know|noted|noticed|saw|learned|confirmed)\b)", nxt):
                    continue    # ', and I ...' inside a quotation keeps the speaker: the rules read both parts
                cuts.append((m.start(), m.end()))
            for m in LINKED.finditer(s):
                cuts.append((m.end(), m.end()))
            for m in WHO_NAME.finditer(s):
                cuts.append((m.start(), m.start()))
            cuts.sort()
            p = 0
            for a, b in cuts:
                prefix = s[p:a]
                if not re.search(START, prefix) or re.search(
                        r"\b(?:said|says|noted|added|explained|explains|stated|mentioned|replied|remarked|wrote|continued|"
                        r"concluded|recalled|suggested)$", prefix) and (re.search(QUOTE, s[a:b + 1]) or s[a:b] in (", ", "; ")):
                    continue
                out.append(prefix)
                p = b
            out.append(s[p:])
        return [c for c in out if c.strip()]
