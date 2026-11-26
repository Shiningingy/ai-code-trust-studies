import re

from gram import Normalizer


class StraightQuotes(Normalizer):
    name = "straight_quotes"
    solves = ("curly double quotes (“ ”) and curly single quotes used as quote marks become straight ones, so "
              "one quote class serves every rule; an apostrophe inside a word (John’s) is left alone, as the "
              "word check would read it as two words")
    added_by = "learning"
    examples = [("Talia Tran said, “I work for Org 014", 'Talia Tran said, "I work for Org 014'),
                ("‘N. Reed owns a camera’", "'N. Reed owns a camera'")]

    def apply(self, clause):
        clause = clause.replace("“", '"').replace("”", '"')
        return re.sub(r"‘|(?<![A-Za-z])’|’(?![A-Za-z])", "'", clause)


class CollapseSpaces(Normalizer):
    name = "collapse_spaces"
    solves = "runs of spaces or tabs inside a clause become one space (a spacing slip, not a new construction)"
    added_by = "learning"
    examples = [("Nadia Reed  owns a camera", "Nadia Reed owns a camera")]

    def apply(self, clause):
        return re.sub(r"[ \t]{2,}", " ", clause)


class BaseVerbAfterTo(Normalizer):
    name = "base_verb_after_to"
    solves = ("a verb after 'used to' / 'plans to' wrongly carrying the 3rd-person -s ('used to attends the history "
              "group') is put back in its base form, a small grammar slip")
    added_by = "learning"
    examples = [("Elena Novak used to attends the history group in the past",
                 "Elena Novak used to attend the history group in the past")]
    VERBS = r"attends|owns|works|travels|visits|enjoys|recommends|uses|takes|helps"

    def apply(self, clause):
        return re.sub(r"\b((?:used|plans?|planned) to )(%s)\b" % self.VERBS, lambda m: m.group(1) + m.group(2)[:-1],
                      clause, flags=re.I)
