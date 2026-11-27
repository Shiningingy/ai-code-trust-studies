"""Sentences that frame a passage (what kind of note it is) and narrator remarks: they carry no fact."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from gram import Rule  # noqa: E402


class PassageFrame(Rule):
    name = "passage_frame"
    solves = ("ignore-rule for the opening sentence of a passage that says what kind of note follows ('The travel "
              "note included context beyond the submitted expense.', 'This week's community bulletin collected "
              "several unrelated updates.'): it names no person and carries no fact")
    added_by = "learning"
    ignore = True
    RX = re.compile(
        r"(?:The|This|This week's|Our|A|An|My) (?:[A-Za-z'-]+ ){0,4}(?:note|notes|bulletin|newsletter|log|record|"
        r"chat|recap|handoff|interview|profile|meeting|transcript|email|message|summary|report|file|update|"
        r"conversation|account)s? (?:included|collected|recorded|covered|moved|touched|highlights|highlighted|"
        r"contains|contained|mentions|mentioned|lists|listed|gathered|brought|captured|noted|shared|combines|"
        r"combined|spans|spanned|offers|offered|went|ranged)\b[^\"“”]*")
    examples = [("The travel note included context beyond the submitted expense.", []),
                ("This week's community bulletin collected several unrelated updates.", []),
                ("The interview moved across several topics.", [])]

    def parse(self, clause):
        c = clause.strip().rstrip(".!?:").strip()
        if not self.RX.fullmatch(c) or C.slot_in(c):
            return None
        return []
