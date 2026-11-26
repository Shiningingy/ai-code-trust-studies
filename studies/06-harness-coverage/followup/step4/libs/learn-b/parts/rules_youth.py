import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import fact, person, NAME, LEAD_NEUTRAL, LEAD_REPORTED  # noqa: E402
from common_stmt import Stmt, IgnoreBase  # noqa: E402
from gram import Rule  # noqa: E402
from rules_basic import obj  # noqa: E402

YOUTH = r"(?:Youth\s*|Y)\d{3}"


def youth(text):
    """Canonical youth id: 'Youth 075', 'youth075', 'y075' -> 'Y075'."""
    return "Y" + re.search(r"\d+", text).group(0)


class Guardian(Stmt):
    name = "guardian_of"
    solves = "'X is the legal guardian of Youth N / YN': guardianship of a youth (qualifier 'legal')"
    added_by = "learning"
    pred = r"(?:is|am)\s+(?:the\s+)?(?P<legal>legal\s+)?guardian of\s+(?P<y>%s)" % YOUTH
    examples = [("N. Reed is the legal guardian of Y114.",
                 [fact("Nadia Reed", "guardian_of", "Y114", ["legal"])])]

    def facts(self, s, m):
        return [("guardian_of", youth(m.group("y")), ["legal"] if m.group("legal") else [])]


class EmergencyContact(Stmt):
    name = "emergency_contact"
    solves = ("'X is an emergency contact, but not a guardian, for Youth N': an emergency contact who is explicitly not "
              "the guardian (second fact guardian_of with qualifier 'not'); without the 'but not a guardian' part only "
              "the emergency-contact fact")
    added_by = "learning"
    pred = (r"(?:is|am)\s+(?:listed as\s+)?an\s+emergency contact(?P<ng>\s*,?\s*(?:but\s+)?not a guardian\s*,?)?"
            r"(?:\s+for\s+(?P<y>%s))?(?P<ng2>\s*,?\s*(?:but\s+)?not a guardian)?" % YOUTH)
    examples = [("C. Avery is an emergency contact, but not a guardian, for Y123.",
                 [fact("Carla Avery", "emergency_contact_of", "Y123"),
                  fact("Carla Avery", "guardian_of", "Y123", ["not"])])]

    def facts(self, s, m):
        y = youth(m.group("y")) if m.group("y") else ""
        out = [("emergency_contact_of", y, [])]
        if m.group("ng") or m.group("ng2"):
            out.append(("guardian_of", y, ["not"]))
        return out


class Course(Rule):
    name = "attends_course"
    solves = ("'Youth N currently attends evening_pottery during the evening': a youth's course and its time of day "
              "(qualifiers: 'currently', 'during the evening|day'; the course keeps its prefix evening_/daytime_)")
    added_by = "learning"
    examples = [("Y074 currently attends daytime_first_aid during the day.",
                 [fact("Y074", "attends_course", "daytime_first_aid", ["currently", "during the day"])])]
    _rx = re.compile(r'"?(?:(?:%s|%s)[,\s]\s*){0,2}(?P<y>%s)\s+(?:(?:said|says|stated|added)[,:]?\s+"?I\s+)?(?P<cur>currently\s+)?attends?\s+(?P<c>[a-z]+_[a-z_]+)'
                     r'(?:\s+during the (?P<t>evening|day))?[\s.,"]*' % (LEAD_NEUTRAL, LEAD_REPORTED, YOUTH), re.I)

    def parse(self, clause):
        m = self._rx.fullmatch(clause.strip())
        if not m:
            return None
        q = (["currently"] if m.group("cur") else []) + (["during the " + m.group("t").lower()] if m.group("t") else [])
        return [fact(youth(m.group("y")), "attends_course", m.group("c").lower(), q)]


class ServesNotEats(Stmt):
    name = "serves_not_eats"
    solves = "'X serves F to other people but does not eat it': serves a food to others without eating it"
    added_by = "learning"
    pred = r"serves?\s+(?P<obj>[a-z]+(?:\s+[a-z]+)?)\s+to other people(?P<ne>\s*,?\s*but does not eat it)?"
    examples = [("F. Reed serves banana to other people but does not eat it.",
                 [fact("Farah Reed", "serves_to_others", "banana", ["does not eat it"])])]

    def facts(self, s, m):
        return [("serves_to_others", obj(m.group("obj")), ["does not eat it"] if m.group("ne") else [])]


class NamedAttribution(Rule):
    name = "ignore_named_attribution"
    solves = "speaker tags that name the speaker after a quotation ('T. Novak said.', 'M. Gupta explained.')"
    added_by = "learning"
    ignore = True
    examples = [("T. Novak said.", [])]
    _rx = re.compile(r"(?P<n>%s)\s+(?:said|says|explained|added|noted|mentioned|remarked|stated|wrote|concluded|continued|agreed|explains|replied)[.,]?" % NAME, re.I)

    def parse(self, clause):
        return [] if self._rx.fullmatch(clause.strip()) else None
