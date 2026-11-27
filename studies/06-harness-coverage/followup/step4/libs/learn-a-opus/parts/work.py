"""Work: employers, shifts, and where organisations are based."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import F, SUBJ, lead  # noqa: E402

Q = ""
T = r"(?P<tail>.*)"
CITIES = ["St. John's", "Halifax", "Edmonton", "Winnipeg", "Victoria", "Vancouver", "Regina", "Ottawa", "Lunenburg",
          "Calgary", "Toronto", "Montreal"]


class WorksFor(C.Core):
    name = "works_for"
    solves = ("'X (currently) works for Org 019 / Organization 019' and past forms ('used to work for', 'worked for', "
              "'previously worked for'); the org id is canonical 'Org 019'")
    added_by = "learning"
    pattern = (Q + SUBJ + r" (?:also )?(?:(?P<cur>currently) )?(?:(?P<past>used to work|previously worked|formerly "
               r"worked|worked)|works|work) for (?P<org>%s)" % C.ORG + T)
    examples = [
        ("Isaac Avery currently works for Org 019, which explains his schedule.",
         [F("Isaac Avery", "works_for", "Org 019", "current", "note:which explains his schedule")]),
        ("N. Ortiz works for Organization 002.", [F("N. Ortiz", "works_for", "Org 002")]),
    ]

    def make(self, s, g, q):
        return [F(s, "works_for", C.org(g["org"]), lead(g, "cur", "current"), lead(g, "past", "past"), q)]


class WorksShift(C.Core):
    name = "works_shift"
    solves = ("'X works the night/day shift' and its past forms ('in a former role', 'used to work', 'worked ... in a "
              "former role') -> relation works_shift, object night/day, past forms get qualifier past")
    added_by = "learning"
    pattern = (Q + SUBJ + r" (?:also )?(?:(?P<cur>currently) )?(?:(?P<past>used to work|previously worked|formerly "
               r"worked|worked)|works|work) (?:the |a )?(?P<shift>[a-z]+) shifts?" + T)
    examples = [
        ("Amina Chen works the night shift.", [F("Amina Chen", "works_shift", "night")]),
        ("i. Usman works the night shift in a former role.", [F("I. Usman", "works_shift", "night", "past")]),
        ("T. Patel used to work the night shift.", [F("T. Patel", "works_shift", "night", "past")]),
    ]

    def make(self, s, g, q):
        return [F(s, "works_shift", g["shift"].lower(), lead(g, "cur", "current"), lead(g, "past", "past"), q)]


class OrgBasedIn(C.Core):
    name = "org_based_in"
    solves = "'Org 027 is based in Lunenburg' -> where an organisation is based (the city, title-cased)"
    added_by = "learning"
    subject_kind = "any"
    pattern = (Q + r"(?P<subj>%s) is (?:based|located|headquartered) in (?P<city>(?:%s)%s|[A-Za-z][A-Za-z'-]*"
               r"(?: [A-Za-z][A-Za-z'-]*){0,2}?%s)" % (C.ORG, "|".join(re.escape(c) for c in CITIES), C.TAIL_START,
                                                      C.TAIL_START) + T)
    examples = [
        ("Org 027 is based in Lunenburg.", [F("Org 027", "based_in", "Lunenburg")]),
        ("organization 013 is based in st. john's.", [F("Org 013", "based_in", "St. John's")]),
        ("Organization 025 is based in Victoria, which gives the area a distinct administrative flavor.",
         [F("Org 025", "based_in", "Victoria", "note:which gives the area a distinct administrative flavor")]),
    ]

    def make(self, s, g, q):
        if not s.startswith("Org "):
            return None
        city = " ".join(w[:1].upper() + w[1:].lower() for w in g["city"].split(" "))
        return [F(s, "based_in", city, q)]
