"""Youths: guardianship, emergency contacts, and the courses youths attend."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import F, SUBJ, lead  # noqa: E402

Q = ""
T = r"(?P<tail>.*)"
Y = r"(?P<y>%s)" % C.YOUTH


class LegalGuardian(C.Core):
    name = "legal_guardian"
    solves = "'X is the legal guardian of Youth 045 / Y045' -> guardian_of Y045, qualifier legal"
    added_by = "learning"
    pattern = Q + SUBJ + r" (?:is|am) (?:the |a )?(?P<legal>legal )?guardian (?:of|for) " + Y + T
    examples = [("Kofi Patel is the legal guardian of Y111.", [F("Kofi Patel", "guardian_of", "Y111", "legal")]),
                ("D. Khan is the legal guardian of Youth 045.", [F("D. Khan", "guardian_of", "Y045", "legal")])]

    def make(self, s, g, q):
        return [F(s, "guardian_of", C.youth(g["y"]), lead(g, "legal", "legal"), q)]


class EmergencyContact(C.Core):
    name = "emergency_contact"
    solves = ("'X is (listed as) an emergency contact, (but) not a guardian, for Y102' -> emergency_contact_for Y102 with "
              "qualifier 'not guardian' (this is NOT guardianship)")
    added_by = "learning"
    pattern = (Q + SUBJ + r" (?:is|am) (?:listed as |named as )?(?:an |the )?emergency contact(?P<ng>,? (?:but )?not "
               r"(?:a |the )?guardian,?)? (?:for|of) " + Y + T)
    examples = [("Isaac Tran is an emergency contact, but not a guardian, for Y049.",
                 [F("Isaac Tran", "emergency_contact_for", "Y049", "not guardian")]),
                ("J. Ito is listed as an emergency contact, but not a guardian, for Y110.",
                 [F("J. Ito", "emergency_contact_for", "Y110", "not guardian")]),
                ("Kofi Khan is an emergency contact, not a guardian, for Youth 011.",
                 [F("Kofi Khan", "emergency_contact_for", "Y011", "not guardian")])]

    def make(self, s, g, q):
        return [F(s, "emergency_contact_for", C.youth(g["y"]), lead(g, "ng", "not guardian"), q)]


class YouthAttendsCourse(C.Core):
    name = "youth_attends_course"
    solves = ("'Y045 currently attends evening_pottery during the evening' -> attends_course evening_pottery, "
              "qualifiers current and during:evening (the course time)")
    added_by = "learning"
    subject_kind = "any"
    pattern = (Q + r"(?P<subj>%s|I) (?:(?P<cur>currently) )?(?:(?P<past>used to attend|attended)|attends|attend) "
               r"(?P<course>[a-z]+_[a-z_]+)(?: during the (?P<when>day|evening|morning|afternoon|night))?" % C.YOUTH + T)
    examples = [("Y002 currently attends daytime_first_aid during the day.",
                 [F("Y002", "attends_course", "daytime_first_aid", "current", "during:day")]),
                ("youth 152 currently attends evening_language during the evening.",
                 [F("Y152", "attends_course", "evening_language", "current", "during:evening")])]

    def make(self, s, g, q):
        if s != "I" and not s.startswith("Y"):
            return None
        return [F(s, "attends_course", g["course"].lower(), lead(g, "cur", "current"), lead(g, "past", "past"),
                  ["during:" + g["when"].lower()] if g["when"] else [], q)]
