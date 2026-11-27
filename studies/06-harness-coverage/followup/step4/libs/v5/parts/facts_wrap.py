import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import NAME, Q, _read_as, canon_name  # noqa: E402
from facts_basic import F  # noqa: E402
from gram import Rule  # noqa: E402


class DidWhen(Rule):
    name = "did_when"
    solves = ("'... what NAME did when she visited the museum': the fragment names a person and, after 'when she', a "
              "claim about them; read the claim as if it were a plain clause of that person")
    added_by = "reconcile"
    examples = [("Elena Patel did when she visited the museum some time ago.",
                 [{"subject": "Elena Patel", "relation": "visited", "object": "museum",
                   "qualifiers": ["some time ago", "past"]}])]

    def parse(self, clause):
        m = re.fullmatch(r"(?:what )?(%s) did when (?:she|he|they) (.+?)[.]?[%s]?" % (NAME, Q), clause.strip())
        return _read_as(m.group(1), m.group(2)) if m else None


class DifferentFrom(Rule):
    name = "different_from"
    solves = ("'That is different from NAME, who visited the market.': a contrast opener followed by a relative clause "
              "about another person; the relative clause is that person's claim")
    added_by = "reconcile"
    examples = [("That is different from Quinn Tran, who visited the market.",
                 [{"subject": "Quinn Tran", "relation": "visited", "object": "market", "qualifiers": []}])]

    def parse(self, clause):
        m = re.fullmatch(r"That is different from (%s), who (.+?)[.]?[%s]?" % (NAME, Q), clause.strip())
        return _read_as(m.group(1), m.group(2)) if m else None


class HelpedWhen(Rule):
    name = "helped_when"
    solves = ("first-person scene 'I was at the library for a cleanup when NAME helped.': the person named helped with "
              "that activity at that place")
    added_by = "reconcile"
    examples = [("I was at the library for a cleanup when Kofi Mensah helped.",
                 [{"subject": "Kofi Mensah", "relation": "helped_with_cleanup", "object": "library", "qualifiers": []}])]

    def parse(self, clause):
        m = re.fullmatch(r"I was at the ([a-z]+(?: (?:hall|park))?) for a (registration|setup|cleanup) when (%s) helped[.]?"
                         % NAME, clause.strip())
        return [F(canon_name(m.group(3)), "helped_with_" + m.group(2), m.group(1))] if m else None
