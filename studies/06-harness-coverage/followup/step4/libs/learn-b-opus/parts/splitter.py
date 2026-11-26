import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram import Splitter

from common import CLAUSE_START, Q

# Sentence ends: . ! ? (optionally followed by a closing quote) then space; not after an initial ("N. Reed") or "St".
SENT_END = re.compile(r"(?<![\s.\"“”‘(][A-Za-z])(?<!^[A-Za-z])(?<!\bSt)[.!?]%s?(?=\s+|$)" % Q)
CONNECTOR = re.compile(r"\s*(?:,\s*\"\s*(?:and|while|but|whereas)|,\s*and that|,\s*and|,\s*while|,\s*but|,\s*whereas|,\s*although|,\s*though|,\s*so|,\s*and then|"
                       r";\s*and|;|,|\s+and|\s+while|\s+but|\s+whereas)\s+")


class SentenceClauseSplitter(Splitter):
    name = "sentence_clause"
    solves = ("cuts a line into sentences (not at initials like 'N. Reed' or 'St. John's'), then cuts each sentence "
              "at connectors (', and', ', while', ', but', ', whereas', ';', ',' or a bare 'and') only where a new "
              "clause starts (a name followed by a predicate verb, an org, a youth, or the community roster), so "
              "elaborations like ', but no longer does' stay with their clause")
    added_by = "learning"
    droppable = [r"(?:,|;)?\s*\"?\s*(?:and|while|but|whereas|although|though|so|and then|and that)?", r"[,;]"]
    examples = [
        ("E. Patel visited the market some time ago. B. Ito owns a garden tools.",
         ["E. Patel visited the market some time ago", "B. Ito owns a garden tools"]),
        ("Kofi Laurent recommended Atlas of Clouds, but Farah Reed used the subway once.",
         ["Kofi Laurent recommended Atlas of Clouds", "Farah Reed used the subway once"]),
        ("O. Foster used to attend the chess club, but no longer does.",
         ["O. Foster used to attend the chess club, but no longer does"]),
        ("Org 013 is based in St. John's.", ["Org 013 is based in St. John's"]),
        ("In a separate update, elena Jones discussed Atlas of Clouds.",
         ["In a separate update, elena Jones discussed Atlas of Clouds"]),
        ('"A. Gupta owns a camera," the speaker said.', ['"A. Gupta owns a camera," the speaker said']),
        ('T. Tran said, "I visited the library." Q. Ortiz owns a camera.',
         ['T. Tran said, "I visited the library', "Q. Ortiz owns a camera"]),
        ("G. Chen visited the museum, while P. Khan and G. Ito visited the market.",
         ["G. Chen visited the museum", "P. Khan and G. Ito visited the market"]),
        ("Priya Foster owns a telescope, and she explained that Leah Silva helped with setup.",
         ["Priya Foster owns a telescope", "she explained that Leah Silva helped with setup"]),
        ('"F. Patel attends the garden circle," F. Patel noted, "while I. Avery owns a garden tools."',
         ['"F. Patel attends the garden circle," F. Patel noted', "I. Avery owns a garden tools"]),
        ("M. Evans likes train and plane equally, and S. Ito owns a camera.",
         ["M. Evans likes train and plane equally", "S. Ito owns a camera"]),
        ("A. Gupta owns a camera, Mateo Evans discussed museum, and S. Khan attends the chess club.",
         ["A. Gupta owns a camera", "Mateo Evans discussed museum", "S. Khan attends the chess club"]),
    ]

    def split(self, line):
        out = []
        pos = 0
        for m in SENT_END.finditer(line):
            out.extend(self._clauses(line[pos:m.start()]))
            pos = m.end()
        out.extend(self._clauses(line[pos:]))
        return [c for c in out if c.strip(" \"“”'")]

    def _clauses(self, sent):
        sent = sent.strip()
        if not sent:
            return []
        cuts = []
        for m in CONNECTOR.finditer(sent):
            if m.start() == 0:
                continue
            if not CLAUSE_START.match(sent, m.end()):
                continue
            # a bare comma or 'and' only joins two clauses, never an opener ("In a separate update, N ...") to its
            # clause or two names ("P. Khan and G. Ito both visited ...")
            prev = sent[cuts[-1][1] if cuts else 0:m.start()]
            if m.group(0).strip() in (",", "and", "while", "but", "whereas") and not CLAUSE_START.search(prev):
                continue
            cuts.append((m.start(), m.end()))
        pieces, pos = [], 0
        for a, b in cuts:
            if a < pos:
                continue
            pieces.append(sent[pos:a])
            pos = b
        pieces.append(sent[pos:])
        return [p.strip() for p in pieces if p.strip()]
