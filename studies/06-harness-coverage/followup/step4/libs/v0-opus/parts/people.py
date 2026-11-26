"""Who is who, where organisations are, who works where and when."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import FamilyRule  # noqa: E402


class Roster(FamilyRule):
    name = "roster"
    family = "identity"
    solves = ("'The community roster records/lists NAME under identifier P-123 and also uses the familiar names ALIAS': "
              "ties a person ID to a full name and its aliases, the only way to join name forms to IDs")
    added_by = "learning"
    examples = [
        ("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed",
         [{"subject": "P-114", "relation": "has_name", "object": "Nadia Reed", "qualifiers": []},
          {"subject": "P-114", "relation": "has_alias", "object": "N. Reed", "qualifiers": []}]),
        ("In a separate update, the community roster records f. patel under identifier p-006",
         [{"subject": "P-006", "relation": "has_name", "object": "F. Patel", "qualifiers": []}]),
        ("The appointment note records that the community roster lists Amina Haddad under identifier P-061",
         [{"subject": "P-061", "relation": "has_name", "object": "Amina Haddad", "qualifiers": ["reported"]}]),
    ]


class OrgLocation(FamilyRule):
    name = "org_location"
    family = "org_location"
    solves = "'Org 014 / Organization 014 is based in CITY': where an organisation is (subject 'Org 014')"
    added_by = "learning"
    examples = [
        ("Org 014 is based in Regina", [{"subject": "Org 014", "relation": "based_in", "object": "Regina",
                                         "qualifiers": []}]),
        ("Organization 031 is based in St. John's, which made the location easy to reference",
         [{"subject": "Org 031", "relation": "based_in", "object": "St. John's", "qualifiers": []}]),
        ("The same account also says that organization 007 is based in lunenburg",
         [{"subject": "Org 007", "relation": "based_in", "object": "Lunenburg", "qualifiers": ["reported"]}]),
    ]


class Employment(FamilyRule):
    name = "employment"
    family = "employment"
    solves = ("'NAME (currently) works for Org 012 / Organization 012' and its first-person / past forms ('used to work for', 'worked "
              "for'): employer, with 'currently' or 'past' kept as qualifiers")
    added_by = "learning"
    examples = [
        ("S. Gupta currently works for Org 025",
         [{"subject": "S. Gupta", "relation": "works_for", "object": "Org 025", "qualifiers": ["currently"]}]),
        ("kofi reed works for Org 003", [{"subject": "Kofi Reed", "relation": "works_for", "object": "Org 003",
                                          "qualifiers": []}]),
        ("Elsewhere in the note, ben Novak currently works for Organization 020, a role that keeps her schedule full",
         [{"subject": "Ben Novak", "relation": "works_for", "object": "Org 020", "qualifiers": ["currently"]}]),
    ]


class Shift(FamilyRule):
    name = "shift"
    family = "shift"
    solves = ("'NAME works the day/night shift', 'works the night shift in a former role', 'used to work the night "
              "shift': shift pattern, with the former-role forms marked 'past'")
    added_by = "learning"
    examples = [
        ("E. Ito works the day shift", [{"subject": "E. Ito", "relation": "works_shift", "object": "day",
                                         "qualifiers": []}]),
        ("G. Chen works the night shift in a former role",
         [{"subject": "G. Chen", "relation": "works_shift", "object": "night", "qualifiers": ["past"]}]),
        ("p. khan used to work the night shift", [{"subject": "P. Khan", "relation": "works_shift", "object": "night",
                                                   "qualifiers": ["past"]}]),
    ]
