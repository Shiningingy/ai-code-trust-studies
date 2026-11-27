"""How lines are built: the splitter, form repairs, reported speech, mixed coordination, and filler sentences."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Normalizer, Rule, Splitter  # noqa: E402


class SentenceClauses(Splitter):
    name = "sentence_clauses"
    solves = ("cuts a line into sentences (not after initials like 'N.' or 'St.', never inside quotation marks), "
              "then at ', and' / ', but' / ', while' / ', whereas' / ';' / ',' / ' and ' when a new subject follows")
    added_by = "learning"
    droppable = lang.DROPPABLE
    examples = [
        ("F. Avery discussed history group, and K. Patel owns a camera.",
         ["F. Avery discussed history group", "K. Patel owns a camera."]),
        ("Org 013 is based in St. John's. N. Reed owns a guitar.",
         ["Org 013 is based in St. John's.", "N. Reed owns a guitar."]),
        ('S. Laurent said, "I helped with registration at the library. Dev Evans recommended Copper Harbor." '
         'Ben Ito owns a camera.',
         ['S. Laurent said, "I helped with registration at the library. Dev Evans recommended Copper Harbor."',
          "Ben Ito owns a camera."]),
        ("A. Chen owns a telescope, Farah Chen owns a guitar; G. Chen visited the museum some time ago, while P. Khan "
         "and G. Ito both visited the market previously.",
         ["A. Chen owns a telescope", "Farah Chen owns a guitar", "G. Chen visited the museum some time ago",
          "P. Khan and G. Ito both visited the market previously."]),
        ("K. Mensah used to attend the walking group, but no longer does.",
         ["K. Mensah used to attend the walking group, but no longer does."]),
    ]

    def split(self, line):
        return lang.split_clauses(line)


class StraightQuotes(Normalizer):
    name = "straight_quotes"
    solves = "curly quotation marks are written as straight ones so one set of rules reads both"
    added_by = "learning"
    examples = [("Ben said, “I own a camera.”", 'Ben said, "I own a camera."')]

    def apply(self, clause):
        return clause.replace("“", '"').replace("”", '"')


_AGREE = re.compile(r"\b((?:I|i)(?: currently| also| routinely| only| still)?|used to|to) (attends|works|travels|"
                    r"chooses|prefers|enjoys|dislikes|serves|volunteers)\b")
_VOLUNTEER = re.compile(r"(?<=[a-z]) volunteer at (?=\S*event)")


class VerbAgreement(Normalizer):
    name = "verb_agreement"
    solves = ("agreement slips in the templates: 'I attends' / 'I currently works' / 'used to attends' lose the -s, "
              "and 'NAME volunteer at event-...' is the past tense 'volunteered'")
    added_by = "learning"
    examples = [('T. Ortiz said, "I attends the chess club only in the past', 'T. Ortiz said, "I attend the chess club only in the past'),
                ("Q. Reed used to attends the garden circle", "Q. Reed used to attend the garden circle"),
                ("Ben Ito volunteer at event-P-051-0 during this-year", "Ben Ito volunteered at event-P-051-0 during this-year")]

    def apply(self, clause):
        clause = _AGREE.sub(lambda m: m.group(1) + " " + m.group(2)[:-1], clause)
        return _VOLUNTEER.sub(" volunteered at ", clause)


class ReportedSpeech(Rule):
    name = "reported_speech"
    solves = ("quoted speech ('NAME said, \"I ...\"', 'NAME: \"...\"', '\"...,\" the speaker said', a bare quotation): "
              "the quotation is parsed with the whole grammar, 'I' is the speaker, every fact gets reported_by:<speaker>")
    added_by = "learning"
    examples = [
        ('S. Laurent said, "I helped with registration at the library. Dev Evans recommended Copper Harbor."',
         [lang.fact("S. Laurent", "helped_with", "registration", ["at:library", "reported_by:S. Laurent"]),
          lang.fact("Dev Evans", "recommended", "copper harbor", ["reported_by:S. Laurent"])]),
        ('I. Usman: "I recommended Quiet Machines.',
         [lang.fact("I. Usman", "recommended", "quiet machines", ["reported_by:I. Usman"])]),
        ('"Gabriel Gupta took part in language class as the teacher this year," the speaker said.',
         [lang.fact("Gabriel Gupta", "took_part_in", "language class",
                    ["role:teacher", "when:this year", "reported_by:the speaker"])]),
        ('O. Diaz said, "I used to attend the radio society, but I no longer do."',
         [lang.fact("O. Diaz", "attends", "radio society", ["status:former", "reported_by:O. Diaz"])]),
    ]

    def parse(self, clause):
        r = lang.parse_speech(clause)
        return r.facts if r else None


class MixedCoordination(Rule):
    name = "mixed_coordination"
    solves = ("one subject with predicates of different families joined by 'and' ('Ben Ortiz visited the museum and "
              "owns a guitar'); the family rules take single-family clauses")
    added_by = "learning"
    examples = [
        ("Ben Ortiz visited the museum and owns a guitar.",
         [lang.fact("Ben Ortiz", "visited", "museum"), lang.fact("Ben Ortiz", "owns", "guitar")]),
    ]

    def parse(self, clause):
        r = lang.parse_clause(clause)
        if r is None or len(r.families) < 2:
            return None
        return r.facts


class Filler(Rule):
    name = "filler"
    ignore = True
    solves = ("narrative sentences that name no person, ID, organization, youth or event and match no predicate "
              "('The club newsletter included several brief member updates.', 'it was a busy day'): no facts")
    added_by = "learning"
    examples = [("This week's community bulletin collected several unrelated updates.", []),
                ("it was a busy day", []),
                ("Kofi Silva visited the market.", None)]

    def parse(self, clause):
        return [] if lang.is_filler(clause) else None


class RelativeClause(Rule):
    name = "relative_clause"
    solves = ("facts stated in a 'who' relative clause that the plain grammar cannot reach: 'Ben Ito, who works for "
              "Org 018, noted that ...' (both parts parsed) and 'That is different from Quinn Tran, who visited the "
              "market.' (the relative clause is the only fact)")
    added_by = "learning"
    examples = [
        ("Amina Evans, who currently works for Organization 018, mentioned it during our chat.",
         [lang.fact("Amina Evans", "works_for", "Org 018", ["status:current"])]),
        ("That is different from Quinn Tran, who visited the market.", [lang.fact("Quinn Tran", "visited", "market")]),
        ("Kofi Silva visited the market.", None),
    ]

    def parse(self, clause):
        return lang.parse_relative(clause)
