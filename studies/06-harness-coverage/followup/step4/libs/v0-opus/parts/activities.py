"""Everyday activities: owning, recommending, discussing, attending groups, visiting places, helping out."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import FamilyRule  # noqa: E402


class Ownership(FamilyRule):
    name = "ownership"
    family = "ownership"
    solves = ("'NAME owns a camera' and its variants ('has a', 'keeps a set of X in the shed', 'mentioned keeping a X'); "
              "object lower case without article, a trailing 'set' dropped")
    added_by = "learning"
    examples = [
        ("Gabriel Jones owns a telescope, which he used to show us the stars",
         [{"subject": "Gabriel Jones", "relation": "owns", "object": "telescope", "qualifiers": []}]),
        ("S. Ito owns a camera", [{"subject": "S. Ito", "relation": "owns", "object": "camera", "qualifiers": []}]),
        ("Elsewhere in the note, l. Usman owns a garden tools set, which is always in good condition",
         [{"subject": "L. Usman", "relation": "owns", "object": "garden tools", "qualifiers": []}]),
        ("D. Evans keeps a set of garden tools in the shed",
         [{"subject": "D. Evans", "relation": "owns", "object": "garden tools", "qualifiers": []}]),
    ]


class Recommendation(FamilyRule):
    name = "recommendation"
    family = "recommendation"
    solves = ("'NAME recommended/suggested TITLE (to the group ...)': the title is stored lower case without a "
              "leading article ('The Long Orchard' -> 'long orchard') so it joins with 'discussed'")
    added_by = "learning"
    examples = [
        ("P. Ito recommended Copper Harbor", [{"subject": "P. Ito", "relation": "recommended", "object": "copper harbor",
                                               "qualifiers": []}]),
        ("I observed that b. ortiz recommended the long orchard",
         [{"subject": "B. Ortiz", "relation": "recommended", "object": "long orchard", "qualifiers": ["reported"]}]),
        ("Leah Chen recommended Quiet Machines to the group, a suggestion that was well-received",
         [{"subject": "Leah Chen", "relation": "recommended", "object": "quiet machines", "qualifiers": []}]),
    ]


class Discussion(FamilyRule):
    name = "discussion"
    family = "discussion"
    solves = ("'NAME discussed (the) TOPIC (plans|trends|...)' / 'talked about' / 'mentioned': topic lower case without "
              "article; the aspect word after a topic ('market trends') is kept as qualifier 'aspect:trends'")
    added_by = "learning"
    examples = [
        ("S. Laurent discussed market trends",
         [{"subject": "S. Laurent", "relation": "discussed", "object": "market", "qualifiers": ["aspect:trends"]}]),
        ("J. Ito discussed market", [{"subject": "J. Ito", "relation": "discussed", "object": "market",
                                      "qualifiers": []}]),
        ("The same account also says that h. Laurent discussed The Long Orchard",
         [{"subject": "H. Laurent", "relation": "discussed", "object": "long orchard", "qualifiers": ["reported"]}]),
        ("Carla Silva discussed garden circle plans with the team",
         [{"subject": "Carla Silva", "relation": "discussed", "object": "garden circle", "qualifiers": ["aspect:plans"]}]),
    ]


class Attendance(FamilyRule):
    name = "attendance"
    family = "attendance"
    solves = ("group membership: 'attends the chess club' (current), with 'only in the past', 'used to attend', "
              "'previously/formerly attended', 'no longer attends', 'used to be a member of', or a tail like ', but no "
              "longer does' / ', a membership that has since lapsed' all giving qualifier 'past'; frequencies kept")
    added_by = "learning"
    examples = [
        ("P. Ito attends the chess club", [{"subject": "P. Ito", "relation": "attends", "object": "chess club",
                                            "qualifiers": []}]),
        ("Rosa Avery attends the garden circle only in the past",
         [{"subject": "Rosa Avery", "relation": "attends", "object": "garden circle", "qualifiers": ["past"]}]),
        ("K. Mensah used to attend the walking group, but no longer does",
         [{"subject": "K. Mensah", "relation": "attends", "object": "walking group", "qualifiers": ["past"]}]),
        ("Hana Reed attends the history group, a membership that has since lapsed",
         [{"subject": "Hana Reed", "relation": "attends", "object": "history group", "qualifiers": ["past"]}]),
        ("O. Usman, on the other hand, attends the radio society every morning",
         [{"subject": "O. Usman", "relation": "attends", "object": "radio society", "qualifiers": ["every morning"]}]),
    ]


class Visit(FamilyRule):
    name = "visit"
    family = "visit"
    solves = ("'NAME visited/went to the PLACE' with time words kept: 'some time ago', 'in the past'/'previously' "
              "('past'), 'recently', 'last week', ...")
    added_by = "learning"
    examples = [
        ("Jia Foster visited the sports hall some time ago, and she mentioned the new equipment",
         [{"subject": "Jia Foster", "relation": "visited", "object": "sports hall", "qualifiers": ["some time ago"]}]),
        ("R. Gupta visited the riverside park some time ago, and mentioned how the path had changed",
         [{"subject": "R. Gupta", "relation": "visited", "object": "riverside park", "qualifiers": ["some time ago"]}]),
        ("S. Ito visited the market", [{"subject": "S. Ito", "relation": "visited", "object": "market",
                                        "qualifiers": []}]),
        ("E. Patel visited the market some time ago",
         [{"subject": "E. Patel", "relation": "visited", "object": "market", "qualifiers": ["some time ago"]}]),
        ("Kofi Mensah visited the riverside park previously",
         [{"subject": "Kofi Mensah", "relation": "visited", "object": "riverside park", "qualifiers": ["past"]}]),
    ]


class Helping(FamilyRule):
    name = "helping"
    family = "helping"
    solves = ("'NAME helped/assisted with setup|registration|cleanup at the PLACE' (relation helped_with_<task>); the "
              "place may also come from 'At the market, NAME helped with registration'")
    added_by = "learning"
    examples = [
        ("D. Ito helped with setup at the museum",
         [{"subject": "D. Ito", "relation": "helped_with_setup", "object": "museum", "qualifiers": []}]),
        ("At the market, a. gupta helped with registration",
         [{"subject": "A. Gupta", "relation": "helped_with_registration", "object": "market", "qualifiers": []}]),
        ("P. Foster assisted with registration at the riverside park, making the process smooth for everyone",
         [{"subject": "P. Foster", "relation": "helped_with_registration", "object": "riverside park",
           "qualifiers": []}]),
    ]
