"""How people travel and how they choose between train and plane."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import FamilyRule  # noqa: E402


class TravelMode(FamilyRule):
    name = "travel_mode"
    family = "travel"
    solves = ("travel habits: 'routinely travels by X' (qualifier 'routinely'), '... but no longer does' / 'used to "
              "routinely travel by X' (adds 'past'), 'used the X once' ('once'), 'plans to use the X in the future' "
              "('future', 'planned'); only 'routinely' without 'past' is the ordinary current mode")
    added_by = "learning"
    examples = [
        ("Ben Ortiz routinely travels by subway",
         [{"subject": "Ben Ortiz", "relation": "travels_by", "object": "subway", "qualifiers": ["routinely"]}]),
        ("P. Foster routinely travels by train but no longer does",
         [{"subject": "P. Foster", "relation": "travels_by", "object": "train", "qualifiers": ["routinely", "past"]}]),
        ("S. Ito used the bus once", [{"subject": "S. Ito", "relation": "travels_by", "object": "bus",
                                       "qualifiers": ["once"]}]),
        ("N. Laurent plans to use the tram in the future",
         [{"subject": "N. Laurent", "relation": "travels_by", "object": "tram", "qualifiers": ["future", "planned"]}]),
        ("The speaker mentioned that j. foster used to travel by tram routinely but no longer does",
         [{"subject": "J. Foster", "relation": "travels_by", "object": "tram",
           "qualifiers": ["routinely", "past", "reported"]}]),
    ]


class TravelPreference(FamilyRule):
    name = "travel_preference"
    family = "travel_preference"
    solves = ("train-versus-plane statements, kept apart because only one is a real preference: 'genuinely prefers "
              "train to plane when both are available' (prefers), 'likes train and plane equally' (likes_equally), "
              "'chose train over plane only because of a disruption' (chose, with the reason as qualifier)")
    added_by = "learning"
    examples = [
        ("Rosa Diaz genuinely prefers train to plane when both are available",
         [{"subject": "Rosa Diaz", "relation": "prefers", "object": "train over plane",
           "qualifiers": ["genuinely", "when both are available"]}]),
        ("P. Ito likes train and plane equally",
         [{"subject": "P. Ito", "relation": "likes_equally", "object": "train and plane", "qualifiers": []}]),
        ("Talia Avery chose train over plane only because of a disruption",
         [{"subject": "Talia Avery", "relation": "chose", "object": "train over plane",
           "qualifiers": ["only because of disruption"]}]),
    ]
