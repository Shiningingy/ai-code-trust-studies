import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import VERBS  # noqa: E402
from gram import Normalizer  # noqa: E402


def _cap(a):
    return a.upper() if a.endswith(".") else a.capitalize()


class SubjectCase(Normalizer):
    name = "subject_case"
    solves = ("person names written in lower case at the start of a clause ('talia usman visited ...', 'c. patel owns ...') "
              "and lower-case 'org 007' / 'youth 037' subjects")
    added_by = "learning"
    examples = [("talia usman visited the market", "Talia Usman visited the market"),
                ("c. patel owns a camera", "C. Patel owns a camera"),
                ("org 029 is based in Vancouver", "Org 029 is based in Vancouver"),
                ('rosa avery said, "I own a camera', 'Rosa Avery said, "I own a camera')]
    rx = re.compile(r"^([\"“]?)(?!(?:which|where|who|she|he|they|their|his|her|its|it|the|a|an|and|but|because|said|so|as|that|this|when|while|[a-z]+ing)(?![A-Za-z.]))([A-Za-z]\.|[A-Za-z]{2,}) ([A-Za-z]{2,})(?= (?:%s)(?![A-Za-z]))" % VERBS)
    rx2 = re.compile(r"^([\"“]?)(org|organization|youth) (\d+)", re.I)

    def apply(self, clause):
        m = self.rx2.match(clause)
        if m:
            return clause[:m.start(2)] + m.group(2).capitalize() + clause[m.end(2):]
        m = self.rx.match(clause)
        if not m:
            return clause
        return m.group(1) + _cap(m.group(2)) + " " + m.group(3).capitalize() + clause[m.end():]


class RosterCase(Normalizer):
    name = "roster_case"
    solves = "roster lines with lower-case names, ids or first word ('the community roster records f. patel under identifier p-101')"
    added_by = "learning"
    examples = [("the community roster records f. patel under identifier p-101 and also uses the familiar names f. patel",
                 "The community roster records F. Patel under identifier P-101 and also uses the familiar names F. Patel")]
    rx = re.compile(r"^(?:the )?community roster (?:records|lists) ", re.I)

    def apply(self, clause):
        if not self.rx.match(clause):
            return clause

        def cap(m):
            return _cap(m.group(1)) + " " + m.group(2).capitalize()
        c = re.sub(r"(?<=records )([A-Za-z]\.|[A-Za-z]{2,}) ([A-Za-z]{2,})", cap, clause)
        c = re.sub(r"(?<=lists )([A-Za-z]\.|[A-Za-z]{2,}) ([A-Za-z]{2,})", cap, c)
        c = re.sub(r"(?<=names )([A-Za-z]\.|[A-Za-z]{2,}) ([A-Za-z]{2,})", cap, c)
        c = re.sub(r"(?<![A-Za-z])p-(\d+)", r"P-\1", c)
        return c[:1].upper() + c[1:]


class IdCase(Normalizer):
    name = "id_case"
    solves = "organization / youth / person identifiers written in lower case inside a clause ('works for org 025', 'Y037')"
    added_by = "learning"
    examples = [("nadia patel works for organization 025", "nadia patel works for Organization 025"),
                ("Ben Ito is the legal guardian of youth 037", "Ben Ito is the legal guardian of Youth 037")]

    def apply(self, clause):
        c = re.sub(r"(?<![A-Za-z])(org|organization|youth) (\d+)", lambda m: m.group(1).capitalize() + " " + m.group(2), clause)
        return re.sub(r"(?<![A-Za-z])y(\d{3})(?![0-9])", r"Y\1", c)


class BareVerb(Normalizer):
    name = "bare_verb_past"
    solves = "a past-tense verb written without its ending after a name ('Gabriel Foster discuss the market', 'Haddad help with setup')"
    added_by = "learning"
    examples = [("Gabriel Foster discuss the market with a neighbor", "Gabriel Foster discussed the market with a neighbor"),
                ("Gabriel Haddad help with registration at the library", "Gabriel Haddad helped with registration at the library")]
    rx = re.compile(r"^((?:[A-Z]\.|[A-Z][a-z]+) [A-Z][a-z]+) (discuss|help|recommend|visit)(?= )")

    def apply(self, clause):
        m = self.rx.match(clause)
        return clause if not m else m.group(1) + " " + m.group(2) + "ed" + clause[m.end():]
