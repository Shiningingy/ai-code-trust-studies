"""Form repairs applied to every clause before the rules."""
import re

from gram import Normalizer

_VERBS = (r"attends|visits|works|plans|travels|enjoys|likes|dislikes|buys|serves|volunteers|recommends|discusses|"
          r"helps|avoids|chooses|prefers|takes|uses|routinely travels")
_AGREE = re.compile(r"\b(used to|I|to)((?: (?:routinely|usually|also|still|regularly|currently|genuinely))?) "
                    r"(attends|visits|works|plans|travels|enjoys|likes|dislikes|buys|serves|volunteers|recommends|"
                    r"discusses|helps|avoids|chooses|prefers|takes|uses)\b")


def _base(v):
    if v.endswith(("sses", "shes", "ches")) or v == "discusses":
        return v[:-2]
    return v[:-1]


class VerbAgreement(Normalizer):
    name = "verb_agreement"
    solves = ("repairs a third-person verb after 'used to', 'to' or 'I' ('used to attends', 'I attends', 'I plans "
              "to use') back to the base form, a frequent agreement slip in quoted and past-tense clauses")
    added_by = "learning"
    examples = [
        ("Elena Novak used to attends the history group in the past.",
         "Elena Novak used to attend the history group in the past."),
        ('Farah Avery said, "I attends the radio society only in the past."',
         'Farah Avery said, "I attend the radio society only in the past."'),
        ("Ben Ito attends the chess club.", "Ben Ito attends the chess club."),
    ]

    def apply(self, clause):
        return _AGREE.sub(lambda m: "%s%s %s" % (m.group(1), m.group(2), _base(m.group(3))), clause)


class StripGarbage(Normalizer):
    name = "strip_garbage"
    solves = ("removes replacement characters and control characters left by broken encodings ('��N. Reed "
              "routinely travels by train.'), which are not words")
    added_by = "learning"
    examples = [("��N. Reed routinely travels by train.", "N. Reed routinely travels by train.")]

    def apply(self, clause):
        return re.sub(r"[�\x00-\x08\x0b-\x1f​﻿]", "", clause)
