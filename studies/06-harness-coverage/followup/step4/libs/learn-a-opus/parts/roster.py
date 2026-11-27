"""The community roster: person ids and the other names a person goes by."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import F  # noqa: E402

from gram import PatternRule  # noqa: E402


class RosterRecord(PatternRule):
    name = "roster_record"
    solves = ("'The community roster records <full name> under identifier P-114 and also uses the familiar names "
              "<alias>[, <alias> ...]' (also 'lists'; 'me' inside a quote = the speaker) -> has_id P-114 and one "
              "also_known_as fact per alias; this is the only place person ids appear, so every query answer is "
              "joined through it")
    added_by = "learning"
    flags = re.I
    pattern = (r"(?:the )?community roster (?:records|lists) (?P<name>%s|me) under (?:the )?identifier (?P<pid>%s)"
               r"(?: and also uses the familiar names? (?P<aliases>%s(?:(?:,| and| or),? %s)*?))?(?P<tail>(?:,|\.|$).*)"
               % (C.PERSON, C.PID, C.PERSON, C.PERSON))
    examples = [
        ("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed.",
         [F("Nadia Reed", "has_id", "P-114"), F("Nadia Reed", "also_known_as", "N. Reed")]),
        ("the community roster records farah tran under identifier p-020 and also uses the familiar names f. tran",
         [F("Farah Tran", "has_id", "P-020"), F("Farah Tran", "also_known_as", "F. Tran")]),
        ("The community roster records f. patel under identifier P-031", [F("F. Patel", "has_id", "P-031")]),
        ("The community roster records Jia Jones under identifier P-130 and also uses the familiar names J. Jones, a "
         "detail that is kept for reference.",
         [F("Jia Jones", "has_id", "P-130", "note:a detail that is kept for reference"),
          F("Jia Jones", "also_known_as", "J. Jones", "note:a detail that is kept for reference")]),
    ]

    def parse(self, clause):
        if re.search("[\"“”]", clause):
            return None     # quoted: the speech rules parse it
        return super().parse(clause)

    def build(self, g):
        if g["name"].lower() == "me":
            name = "I"
        elif C.is_person(g["name"]):
            name = C.person(g["name"])
        else:
            return None
        q = C.tail(g["tail"])
        if q is None:
            return None
        out = [F(name, "has_id", C.pid(g["pid"]), q)]
        if g["aliases"]:
            for a in re.split(r"(?:,| and| or),? ", g["aliases"]):
                if not C.is_person(a):
                    return None
                out.append(F(name, "also_known_as", C.person(a), q))
        return out
