import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram import Rule

from common import YOUTH, Pred, analyze, canon_youth, v


def _y(m):
    return canon_youth(m["ynum"] or m["ynum2"])


class Guardian(Rule):
    name = "guardian"
    solves = ("a person's tie to a youth: 'is the legal guardian of Youth 045' (guardian_of), 'is (listed as) an "
              "emergency contact, but not a guardian, for Y011' (emergency_contact_for, qualifier 'not a guardian'; "
              "without that phrase no qualifier: an emergency contact is still not a guardian); "
              "youth ids normalised to 'YNNN'")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+)?%s\s+(?:the\s+|a\s+)?(?:legal\s+)?guardian\s+(?:of|for)\s+%s" % (v("is"), YOUTH),
             lambda m: ("guardian_of", _y(m), []), 0),
        Pred(r"%s\s+(?:listed\s+as\s+)?an\s+emergency\s+contact\s*,?\s*(?:but\s+)?not\s+(?:a\s+|the\s+)?"
             r"(?:legal\s+)?guardian\s*,?\s*(?:for|of)\s+%s" % (v("is"), YOUTH),
             lambda m: ("emergency_contact_for", _y(m), ["not a guardian"]), 0),
        Pred(r"%s\s+(?:listed\s+as\s+)?an\s+emergency\s+contact\s+(?:for|of)\s+%s\s*,?\s*(?:but\s+)?not\s+(?:a\s+|the\s+)?"
             r"(?:legal\s+)?guardian" % (v("is"), YOUTH),
             lambda m: ("emergency_contact_for", _y(m), ["not a guardian"]), 0),
        Pred(r"%s\s+(?:listed\s+as\s+)?an\s+emergency\s+contact\s+(?:for|of)\s+%s" % (v("is"), YOUTH),
             lambda m: ("emergency_contact_for", _y(m), []), 0),
    ]
    examples = [
        ("Samir Novak is the legal guardian of Youth 159",
         [{"subject": "Samir Novak", "relation": "guardian_of", "object": "Y159", "qualifiers": []}]),
        ("Kofi Khan is an emergency contact, not a guardian, for Y011",
         [{"subject": "Kofi Khan", "relation": "emergency_contact_for", "object": "Y011",
           "qualifiers": ["not a guardian"]}]),
        ("Talia Usman is an emergency contact for Y140, but not a guardian",
         [{"subject": "Talia Usman", "relation": "emergency_contact_for", "object": "Y140",
           "qualifiers": ["not a guardian"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class YouthCourse(Rule):
    name = "youth_course"
    solves = ("a youth attends a course at a time of day: 'Youth 159 currently attends evening_pottery during the "
              "evening' (subject YNNN, relation attends_course, object the course id, qualifier 'during the evening' "
              "or 'during the day'; 'used to attend' gives past)")
    added_by = "learning"
    preds = [
        Pred(r"(?:currently\s+|now\s+|still\s+)?%s\s+(?P<c>[a-z]+(?:_[a-z]+)+)(?:\s+(?P<t>during the (?:evening|day)))?"
             % v("attend"),
             lambda m: ("attends_course", m["c"].lower(), [m["t"].lower()] if m["t"] else []), 0),
        Pred(r"(?:used to attend|previously attended|attended)\s+(?P<c>[a-z]+(?:_[a-z]+)+)"
             r"(?:\s+(?P<t>during the (?:evening|day)))?",
             lambda m: ("attends_course", m["c"].lower(), ([m["t"].lower()] if m["t"] else []) + ["past"]), 0),
    ]
    examples = [
        ("Youth 159 currently attends evening_pottery during the evening, a class that runs late",
         [{"subject": "Y159", "relation": "attends_course", "object": "evening_pottery",
           "qualifiers": ["during the evening"]}]),
        ('Y144 said, "I currently attend evening_language during the evening',
         [{"subject": "Y144", "relation": "attends_course", "object": "evening_language",
           "qualifiers": ["during the evening", "self_reported"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "youth", self.preds)
