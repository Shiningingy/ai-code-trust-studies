"""Clauses built around other clauses: quoted speech, relative 'who' clauses, coordinated subjects, narrator frames;
and the clauses that carry no facts."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import FamilyRule  # noqa: E402


class ReportedSpeech(FamilyRule):
    name = "reported_speech"
    family = "speech"
    solves = ("quotations: 'NAME said, \"I own a camera. Q. Reed visited the museum.\"' (I = the speaker, every quoted "
              "sentence parsed), 'NAME: \"...\"', '\"...,\" the speaker noted', 'NAME said she owns a X', 'Y012 said, "
              "\"I currently attend ...\"'; every fact gets qualifier 'reported'")
    added_by = "learning"
    examples = [
        ('D. Bennett said, "I recommended Copper Harbor."',
         [{"subject": "D. Bennett", "relation": "recommended", "object": "copper harbor", "qualifiers": ["reported"]}]),
        ('G. Ito said, "I used to attend the chess club. Rosa Chen owns a guitar."',
         [{"subject": "G. Ito", "relation": "attends", "object": "chess club", "qualifiers": ["past", "reported"]},
          {"subject": "Rosa Chen", "relation": "owns", "object": "guitar", "qualifiers": ["reported"]}]),
        ('"T. Novak visited the museum some time ago," T. Novak said',
         [{"subject": "T. Novak", "relation": "visited", "object": "museum",
           "qualifiers": ["some time ago", "reported"]}]),
        ("Quinn Reed said he helped with setup at the library",
         [{"subject": "Quinn Reed", "relation": "helped_with_setup", "object": "library", "qualifiers": ["reported"]}]),
        ('Y045 said, "I currently attend evening_language during the evening."',
         [{"subject": "Y045", "relation": "attends_course", "object": "evening_language",
           "qualifiers": ["currently", "during the evening", "reported"]}]),
    ]


class LinkedClauses(FamilyRule):
    name = "linked_clauses"
    family = "linked"
    solves = ("one clause holding facts about two people: 'X, in contrast to NAME, who visited ...', 'Carla Tran "
              "discussed X, which L. Evans recommended', 'P. Khan and G. Ito both visited ...', 'I visited the museum "
              "with NAME', 'I was at the market when NAME helped with registration', 'NAME owns X, and she explained that Q ...'")
    added_by = "learning"
    examples = [
        ("Priya Foster owns a telescope, and she explained that Leah Silva helped with setup at the riverside park",
         [{"subject": "Priya Foster", "relation": "owns", "object": "telescope", "qualifiers": []},
          {"subject": "Leah Silva", "relation": "helped_with_setup", "object": "riverside park",
           "qualifiers": ["reported"]}]),
        ("Priya Foster volunteered at event-P-016-0 during this-year, which contrasts with Amina Haddad, who visited "
         "the library some time ago",
         [{"subject": "Priya Foster", "relation": "volunteered_at", "object": "event-P-016-0",
           "qualifiers": ["this-year"]},
          {"subject": "Amina Haddad", "relation": "visited", "object": "library", "qualifiers": ["some time ago"]}]),
        ("Carla Tran discussed Atlas of Clouds, which L. Evans recommended",
         [{"subject": "Carla Tran", "relation": "discussed", "object": "atlas of clouds", "qualifiers": []},
          {"subject": "L. Evans", "relation": "recommended", "object": "atlas of clouds", "qualifiers": []}]),
        ("P. Khan and G. Ito both visited the market previously",
         [{"subject": "P. Khan", "relation": "visited", "object": "market", "qualifiers": ["past"]},
          {"subject": "G. Ito", "relation": "visited", "object": "market", "qualifiers": ["past"]}]),
        ("I was at the sports hall when I. Tran helped with registration",
         [{"subject": "I. Tran", "relation": "helped_with_registration", "object": "sports hall", "qualifiers": []}]),
    ]


class Commentary(FamilyRule):
    name = "commentary"
    family = "commentary"
    ignore = True
    solves = ("passage headers and narrator remarks with no fact ('The appointment note recorded a few pieces of "
              "background', 'it was a pleasant outing'): ignored, but only if they hold no predicate word, no name, "
              "no number and no meaning-changing word (no longer, not, used to, ...), so nothing factual is lost")
    added_by = "learning"
    examples = [
        ("The appointment note recorded a few pieces of background", []),
        ("This week's community bulletin collected several unrelated updates", []),
        ("She no longer participates in their weekly meetings", None),
        ("I noticed Gabriel Foster discuss the market with a neighbor", None),
    ]


class ContrastRemark(FamilyRule):
    name = "contrast_remark"
    family = "remark"
    ignore = True
    solves = ("narrator remarks 'The contrast between the former membership and the current ownership was noted': they "
              "only compare entries already stated, so they carry no fact even though they use words like 'former'")
    added_by = "learning"
    examples = [
        ("The contrast between the former membership and the current ownership was noted", []),
        ("The contrast between the past routine and the recent help was clear", []),
    ]
