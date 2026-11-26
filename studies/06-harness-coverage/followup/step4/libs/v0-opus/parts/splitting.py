import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gram import Normalizer, Splitter  # noqa: E402

import common  # noqa: E402


class SentenceClauseSplitter(Splitter):
    name = "sentence_clause"
    solves = ("cuts a line into sentences (not inside quotations, not after an initial like 'N.' or 'St.') and each "
              "sentence into clauses at ', and' / ', but' / ', while' / ', whereas' / ';' / ',' / ' and ' only where a new "
              "clause starts after the connector (a name with a predicate verb, 'the community roster', 'Org 012', "
              "'Y034'), so commentary tails and quoted speech stay with the clause they belong to")
    added_by = "learning"
    droppable = common.DROPPABLE
    examples = [
        ("Kofi Laurent recommended Atlas of Clouds, but Farah Reed used the subway once. B. Khan owns a sewing kit.",
         ["Kofi Laurent recommended Atlas of Clouds", "Farah Reed used the subway once", "B. Khan owns a sewing kit"]),
        ("Omar Diaz visited the sports hall, and it was a notable visit. Org 031 is based in St. John's.",
         ["Omar Diaz visited the sports hall, and it was a notable visit", "Org 031 is based in St. John's"]),
        ('G. Ito said, "I own a camera. Rosa Chen discussed museum." The community roster records Nadia Reed under '
         'identifier P-114 and also uses the familiar names N. Reed.',
         ['G. Ito said, "I own a camera. Rosa Chen discussed museum."',
          "The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed"]),
        ("At the market, a. gupta helped with registration, while P. Khan and G. Ito both visited the museum.",
         ["At the market, a. gupta helped with registration", "P. Khan and G. Ito both visited the museum"]),
        ("J. Ito is an emergency contact, but not a guardian, for Y110.",
         ["J. Ito is an emergency contact, but not a guardian, for Y110"]),
    ]

    def split(self, line):
        return common.split_clauses(line)


class StraightQuotes(Normalizer):
    name = "straight_quotes"
    solves = ("curly quotation marks become straight ones, so quotation frames have one form (apostrophes are left "
              "alone: changing them would change how words are counted)")
    added_by = "learning"
    examples = [("“Jia Diaz owns a sewing kit.”", '"Jia Diaz owns a sewing kit."'),
                ("K. Reed said, “I own a guitar.”", 'K. Reed said, "I own a guitar."')]

    def apply(self, clause):
        return clause.replace("“", '"').replace("”", '"')


class SquashSpaces(Normalizer):
    name = "squash_spaces"
    solves = "runs of spaces or tabs inside a clause become one space, so fixed wording matches"
    added_by = "learning"
    examples = [("K. Reed  owns a\tcamera", "K. Reed owns a camera")]

    def apply(self, clause):
        return " ".join(clause.split())


class NameCase(Normalizer):
    name = "name_case"
    solves = ("a person name whose first part lost its capital ('elena Jones', 'c. Patel') gets it back, so names "
              "join with their correctly written mentions; fully lower-case names are handled by the rules")
    added_by = "learning"
    examples = [("In a separate update, elena Jones discussed Atlas of Clouds",
                 "In a separate update, Elena Jones discussed Atlas of Clouds"),
                ("Elsewhere in the note, c. Patel visited the library", "Elsewhere in the note, C. Patel visited the library"),
                ("the group met in the Long Orchard room", "the group met in the Long Orchard room")]

    # only a name followed by a predicate verb or a comma, so book titles and ordinary words are never touched
    _rx = common.re.compile(r"\b%s([a-z])([a-z]+|\.)(?= [A-Z][a-z]+(?: (?:%s)\b|,))" % (common._NOT_NAME, common._VERBS2))

    def apply(self, clause):
        return self._rx.sub(lambda m: m.group(1).upper() + m.group(2), clause)
