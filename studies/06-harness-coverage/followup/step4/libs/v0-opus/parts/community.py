"""Volunteering at events, guardianship of youths and the courses youths attend."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import FamilyRule  # noqa: E402


class Volunteering(FamilyRule):
    name = "volunteering"
    family = "volunteering"
    solves = ("'NAME volunteered at event-P-122-1 during this-year' / 'old-event-P-075 during last-year': the event "
              "is the object, the year ('this-year', 'last-year') a qualifier")
    added_by = "learning"
    examples = [
        ("D. Ito volunteered at event-P-144-0 during this-year",
         [{"subject": "D. Ito", "relation": "volunteered_at", "object": "event-P-144-0", "qualifiers": ["this-year"]}]),
        ("Omar Bennett volunteered at old-event-P-075 during last-year",
         [{"subject": "Omar Bennett", "relation": "volunteered_at", "object": "old-event-P-075",
           "qualifiers": ["last-year"]}]),
        ("samir novak volunteered at event-p-021-1 during this year, supporting the logistics team",
         [{"subject": "Samir Novak", "relation": "volunteered_at", "object": "event-P-021-1",
           "qualifiers": ["this-year"]}]),
    ]


class Guardianship(FamilyRule):
    name = "guardianship"
    family = "guardianship"
    solves = ("'NAME is the legal guardian of Y012 / Youth 012' (guardian_of) and 'is an emergency contact, but not a "
              "guardian, for Y012' (emergency_contact_for, plus guardian_of with 'negated')")
    added_by = "learning"
    examples = [
        ("G. Ito is the legal guardian of Y127",
         [{"subject": "G. Ito", "relation": "guardian_of", "object": "Y127", "qualifiers": ["legal"]}]),
        ("Hana Silva is an emergency contact, but not a guardian, for Youth 151",
         [{"subject": "Hana Silva", "relation": "emergency_contact_for", "object": "Y151", "qualifiers": []},
          {"subject": "Hana Silva", "relation": "guardian_of", "object": "Y151", "qualifiers": ["negated"]}]),
        ("K. Reed is an emergency contact for Y040",
         [{"subject": "K. Reed", "relation": "emergency_contact_for", "object": "Y040", "qualifiers": []}]),
    ]


class YouthCourse(FamilyRule):
    name = "youth_course"
    family = "youth_course"
    solves = ("'Y012 / Youth 012 currently attends evening_pottery during the evening': a youth's course, with "
              "'currently' and the time of day ('during the evening') as qualifiers")
    added_by = "learning"
    examples = [
        ("Y114 currently attends evening_pottery during the evening, a commitment that keeps their schedule full",
         [{"subject": "Y114", "relation": "attends_course", "object": "evening_pottery",
           "qualifiers": ["currently", "during the evening"]}]),
        ("youth 035 currently attends daytime_first_aid during the day",
         [{"subject": "Y035", "relation": "attends_course", "object": "daytime_first_aid",
           "qualifiers": ["currently", "during the day"]}]),
    ]
