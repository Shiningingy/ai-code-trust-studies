"""Ignore-rules: clauses that carry no facts (framing sentences, narrative filler, speech attributions)."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gram import Rule  # noqa: E402

FACT_WORDS = re.compile(
    r"\b(?:owns?|has|recommended|suggested|discussed|mentioned|talked|visited|went|attends?|attended|helped|assisted|"
    r"volunteered|works?|worked|routinely|travels?\s+by|prefers?|chose|avoid\w*|skipping|buys|serves|enjoys?|dislikes?|"
    r"guardian|contact|roster|based|likes?|plans|used\s+(?:to|the)|identifier|eating)\b"
    r"|\b(?:visit\s+the|discuss\s+the|help\s+with|volunteer\s+at|recommend|buy|serve|skip|prefer|choose|enjoy|dislike|"
    r"attend|own|work\s+for|plan\s+to\s+use|travel\s+by|take\s+the|drink|eat)\b"
    r"|\b(?:org|organization|youth)\s+\d+|\b[yp]-?\d+\b|event-",
    re.I)


class NoFactClause(Rule):
    name = "no_fact_clause"
    solves = ("ignore: framing sentences ('The appointment note recorded a few pieces of background'), speech attributions "
              "('the speaker said') and trailing narrative filler ('a task that was completed efficiently'): clauses with no "
              "fact vocabulary, no organisation/youth/person identifier and no event id")
    added_by = "learning"
    ignore = True
    examples = [
        ("The appointment note recorded a few pieces of background", []),
        ("the speaker said", []),
        ("a task that was completed efficiently", []),
    ]

    def parse(self, clause):
        return None if FACT_WORDS.search(clause) else []


class NarrativeTail(Rule):
    name = "narrative_tail"
    solves = ("ignore: a trailing comment that starts lower-case with a determiner, 'it', 'was/is' or a participle "
              "('the book has since been discussed in several forums', 'was used for the craft session') and names nobody; "
              "it comments on the previous clause and adds no fact")
    added_by = "learning"
    ignore = True
    examples = [
        ("the book has since been discussed in several forums", []),
        ("was used for the stargazing session", []),
    ]
    OPEN = re.compile(r"(?:a|an|the|it|was|were|is|are|ensuring|making|adding|bringing|noting|citing|having|which|this|mentioned|made|shapes|helped me|because)\s")
    NAMED = re.compile(r"[A-Z]|\b(?:org|youth|roster)\b|event-")

    def parse(self, clause):
        if not self.OPEN.match(clause) or self.NAMED.search(clause[1:]):
            return None
        return []


class SpeechTag(Rule):
    name = "speech_tag"
    solves = ("ignore: a bare speech attribution left over after a quote or a statement ('she said', 'the speaker noted', "
              "'she mentioned', 'N. Reed explains'): it carries no fact of its own")
    added_by = "learning"
    ignore = True
    examples = [("she mentioned", []), ("the quoted speaker explained", []), ("N. Reed explains", [])]
    RX = re.compile(r"(?:he|she|they|I|we|the (?:quoted )?speaker|[A-Za-z][A-Za-z'-]*\.?(?:\s+[A-Za-z][A-Za-z'-]*)?)\s+"
                    r"(?:said|says|mentioned|noted|explained|explains|added|concluded|continued|agreed|replied)", re.I)

    def parse(self, clause):
        return [] if self.RX.fullmatch(clause.strip()) else None
