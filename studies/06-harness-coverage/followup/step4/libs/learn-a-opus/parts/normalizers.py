import re

from gram import Normalizer


class StraightQuotes(Normalizer):
    name = "straight_quotes"
    solves = "curly quotation marks (“ ”) written instead of straight ones, so rules only need to know '\"'"
    added_by = "learning"
    examples = [("Quinn Ortiz said, “I recommended Quiet Machines.”",
                 'Quinn Ortiz said, "I recommended Quiet Machines."')]

    def apply(self, clause):
        return clause.replace("“", '"').replace("”", '"')


class SpacingRepair(Normalizer):
    name = "spacing_repair"
    solves = "doubled spaces and spaces before punctuation, a form slip that would make fixed wording not match"
    added_by = "learning"
    examples = [("N. Reed  owns a camera .", "N. Reed owns a camera.")]

    def apply(self, clause):
        c = re.sub(r" {2,}", " ", clause)
        return re.sub(r" +([,.;:!?])", r"\1", c).strip()
