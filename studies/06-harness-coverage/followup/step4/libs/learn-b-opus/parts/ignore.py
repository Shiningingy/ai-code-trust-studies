import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram import Rule

from common import ORG, YOUTH

# Anything that could carry a fact: a predicate word, an id, or a capitalised name pair.
FACT_WORDS = re.compile(
    r"\b(?:owns?|owned|recommended|recommends|attends?|attended|visited|helped|assisted|discussed|mentioned|"
    r"talked|spoke|volunteered at|works?|worked|routinely|travels? by|traveled by|bus|tram|subway|train|plane|"
    r"avoids?|dairy|eating|eat|skipping|buys?|serves?|guardian|emergency|roster|identifier|based|enjoys?|"
    r"dislikes?|prefers?|chose|likes?|plans?|used|keeps?|keeping|has|have|went|member of)\b|" + ORG + "|" + YOUTH + r"|\b[Pp]-\d+|event-", re.I)
NAME_PAIR = re.compile(r"\b(?!(?:The|This|That|A|An|Our|My|In|On|At|During|For|While|After|Before|Then|I)\b)"
                       r"[A-Z][a-z]+ [A-Z][a-z]+\b|\b[A-Z]\. ?[A-Z][a-z]+")


class FactFreeRemark(Rule):
    name = "fact_free_remark"
    solves = ("framing sentences that introduce or close a passage ('This week's community bulletin collected "
              "several unrelated updates', 'The interview moved across several topics'): they name no person, id "
              "or predicate, so they carry no fact; ignored")
    added_by = "learning"
    ignore = True
    examples = [
        ("This week's community bulletin collected several unrelated updates", []),
        ("The appointment note recorded a few pieces of background", []),
        ("The team chat was lively with various updates", []),
        ("The volunteer log included some incidental personal information", []),
        ("I handed off the shift with a few notes", []),
        ("The club newsletter included several brief member updates", []),
        ("rosa avery talked about quiet machines", None),
        ("Nadia Reed owns a camera", None),
        ("He used to attend the walking group, but only in the past", None),
    ]

    def parse(self, clause):
        if FACT_WORDS.search(clause) or NAME_PAIR.search(clause):
            return None
        return []
