import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import FIRST, INITIAL, SURNAMES  # noqa: E402
from gram import Normalizer  # noqa: E402


class StraightQuotes(Normalizer):
    name = "straight_quotes"
    solves = "curly quotes (U+201C/U+201D) written for speech are replaced by plain double quotes so rules see one form"
    added_by = "learning"
    examples = [("“I own a guitar.”", '"I own a guitar."')]

    def apply(self, clause):
        return clause.replace("“", '"').replace("”", '"')


_SUR = "|".join(SURNAMES)
_FIR = "|".join(FIRST)
_NAME_LOWER = re.compile(r"(?<![\w.])(?:(?i:%s)|[A-Za-z]\.) (?i:%s)(?![\w])" % (_FIR, _SUR))


class NameCase(Normalizer):
    name = "name_case"
    solves = "person names written with wrong capitals ('elena Jones', 'j. foster', 'rosa avery') get a capital on both parts"
    added_by = "learning"
    examples = [("j. foster owns a camera.", "J. Foster owns a camera."),
                ("In a separate update, rosa avery visited the market.", "In a separate update, Rosa Avery visited the market.")]

    def apply(self, clause):
        def fix(m):
            first, last = m.group(0).split(" ", 1)
            return first[0].upper() + first[1:] + " " + last[0].upper() + last[1:]
        return _NAME_LOWER.sub(fix, clause)


class SentenceCase(Normalizer):
    name = "sentence_initial_case"
    solves = "a clause that starts with a lower-case letter (after a split) gets its first letter capitalised"
    added_by = "learning"
    examples = [("the community roster records Q. Novak under identifier P-037 and also uses the familiar names Q. Novak.",
                 "The community roster records Q. Novak under identifier P-037 and also uses the familiar names Q. Novak.")]

    def apply(self, clause):
        return clause[:1].upper() + clause[1:] if clause[:1].islower() else clause


_ID = re.compile(r"(?<![\w-])(?:p-\d+|y\d{3}|youth \d+|org \d+|organization \d+|org-\d+)(?![\w-])")


class IdCase(Normalizer):
    name = "id_case"
    solves = "identifiers written in lower case ('p-066', 'y048', 'youth 007', 'org 016') get their canonical capitals"
    added_by = "learning"
    examples = [("the community roster records f. silva under identifier p-046", "the community roster records f. silva under identifier P-046"),
                ("In a separate update, youth 007 currently attends evening_pottery", "In a separate update, Youth 007 currently attends evening_pottery"),
                ("org 016 is based in Calgary.", "Org 016 is based in Calgary.")]

    def apply(self, clause):
        def fix(m):
            t = m.group(0)
            return t[0].upper() + t[1:]
        return _ID.sub(fix, clause)
