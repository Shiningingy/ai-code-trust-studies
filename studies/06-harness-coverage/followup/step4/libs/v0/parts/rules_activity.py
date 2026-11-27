"""Rules for everyday activity clauses: visits, discussions, recommendations, possessions, group membership, helping."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gram import PatternRule  # noqa: E402
from common import pat, TAIL, mk, low, ent, fact, canon_subject, who, fact, quals_of, tail_ok  # noqa: E402


def F(s, rel, obj="", q=()):
    return {"subject": s, "relation": rel, "object": obj, "qualifiers": list(q)}


class Visited(PatternRule):
    name = "visited"
    solves = "'X visited the PLACE' (also 'went to', 'previously visited'): a visit, with time qualifiers such as 'some time ago'"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?:(?P<adv>previously|formerly|also|recently)\s+)?(?:visited|visit|had visited|went to|visits)\s+(?:the\s+)?(?P<o>.+?)" + TAIL)
    examples = [
        ("Ben Jones visited the sports hall some time ago", [F("Ben Jones", "visited", "sports hall", ["some time ago"])]),
        ("T. Tran said, \"I visited the library", [F("T. Tran", "visited", "library")]),
        ("Mateo Laurent previously visited the market", [F("Mateo Laurent", "visited", "market", ["previously"])]),
    ]

    def build(self, g):
        return mk(g, "visited", ent(g["o"]), *([g["adv"].lower()] if g["adv"] and g["adv"].lower() not in ("also",) else []))


class Discussed(PatternRule):
    name = "discussed"
    solves = "'X discussed Y' (also 'talked about', 'mentioned'): X talked about a place, group or book Y"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?:also\s+)?(?:had\s+)?(?:discussed|discuss|talked about|mentioned)\s+(?:the\s+)?(?!(?:that|keeping)\b)(?P<o>.+?)" + TAIL)
    examples = [
        ("Priya Haddad discussed chess club", [F("Priya Haddad", "discussed", "chess club")]),
        ("elena Jones discussed Atlas of Clouds", [F("Elena Jones", "discussed", "atlas of clouds")]),
        ("M. Gupta discussed radio society activities", [F("M. Gupta", "discussed", "radio society")]),
    ]

    def build(self, g):
        return mk(g, "discussed", ent(g["o"]))


class Recommended(PatternRule):
    name = "recommended"
    solves = "'X recommended BOOK' (also 'suggested'): X recommends a book or destination"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?:also\s+)?(?:recommended|recommend|suggested)\s+(?P<o>.+?)" + TAIL)
    examples = [
        ("Hana Ortiz recommended Quiet Machines", [F("Hana Ortiz", "recommended", "quiet machines")]),
        ("N. Reed recommended Atlas of Clouds to the group", [F("N. Reed", "recommended", "atlas of clouds")]),
    ]

    def build(self, g):
        return mk(g, "recommended", ent(g["o"]))


class Owns(PatternRule):
    name = "owns"
    solves = "'X owns a THING' (also 'I own', 'has'): X possesses an item"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?:also\s+)?(?:owns?|has)\s+(?:an?\s+|the\s+)?(?P<o>.+?)" + TAIL)
    examples = [
        ("B. Ito owns a garden tools", [F("B. Ito", "owns", "garden tools")]),
        ("N. Tran said, \"I own a camera", [F("N. Tran", "owns", "camera")]),
        ("Sam Reed owns a sewing kit set for the garden", [F("Sam Reed", "owns", "sewing kit")]),
    ]

    def build(self, g):
        return mk(g, "owns", ent(g["o"]))


class Attends(PatternRule):
    name = "attends"
    solves = ("group membership: 'attends the G', 'used to attend', 'no longer attends', 'previously attended', "
              "'attends G only in the past'; the past/no-longer wording is kept as a qualifier")
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?P<pre>(?:currently\s+|also\s+|only\s+)?(?:used to\s+|previously\s+|formerly\s+|no longer\s+)?)"
                  r"(?:attends?|attended|(?P<mem>(?:used to be|is|was)\s+a member of))\s+(?:the\s+)?(?P<o>.+?)" + TAIL)
    examples = [
        ("G. Evans attends the chess club", [F("G. Evans", "attends", "chess club")]),
        ("T. Patel attends the walking group only in the past", [F("T. Patel", "attends", "walking group", ["only in the past"])]),
        ("Rosa Diaz no longer attends the radio society", [F("Rosa Diaz", "attends", "radio society", ["no longer"])]),
        ("Kofi Khan used to attend the history group, but no longer does", [F("Kofi Khan", "attends", "history group", ["used to", "no longer"])]),
    ]

    def build(self, g):
        if re.search(r"\bduring the\b", g["o"] + g["tail"], re.I):
            return None  # a youth's course, see youth_course
        q = [w for w in ("used to", "previously", "formerly", "no longer", "currently") if w in (g["pre"] + g["mem"]).lower()]
        return mk(g, "attends", ent(g["o"]), *q)


class Helped(PatternRule):
    name = "helped"
    solves = "'X helped with setup/cleanup/registration at PLACE': relation is helped_with_<task>, object the place"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?:also\s+)?(?:helped|assisted|help|assist)\s+with\s+(?P<task>\w+)(?:\s+at\s+(?:the\s+)?(?P<o>.+?)|\s+there)?" + TAIL)
    examples = [
        ("K. Khan helped with setup at the library", [F("K. Khan", "helped_with_setup", "library")]),
        ("Quinn Reed helped with cleanup at the riverside park", [F("Quinn Reed", "helped_with_cleanup", "riverside park")]),
    ]

    def build(self, g):
        return mk(g, "helped_with_" + g["task"].lower(), ent(g["o"]))


class Volunteered(PatternRule):
    name = "volunteered"
    solves = "'X volunteered at event-ID during this-year/last-year': one volunteering record; the period is a qualifier"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?:also\s+)?volunteer(?:ed)? at\s+(?P<e>(?:old-)?event-\S+?)\s+during\s+(?P<p>(?:this|last)[- ]year)" + TAIL)
    examples = [
        ("Rosa Evans volunteered at event-P-118-0 during this-year", [F("Rosa Evans", "volunteered_at", "event-P-118-0", ["this-year"]),
                                                                         F("Rosa Evans", "id_hint", "P-118", ["from event id"])]),
        ("Dev Haddad volunteered at old-event-P-124 during last-year", [F("Dev Haddad", "volunteered_at", "old-event-P-124", ["last-year"]),
                                                                         F("Dev Haddad", "id_hint", "P-124", ["from event id"])]),
    ]

    def build(self, g):
        e = re.sub(r"(?i)^(old-)?event-p-", lambda m: (m.group(1) or "").lower() + "event-P-", g["e"])
        out = mk(g, "volunteered_at", e, g["p"].lower().replace(" ", "-"))
        pid = re.search(r"P-(\d+)", e)
        if out and pid:   # event ids embed the volunteer's person id: keep it as an identity hint for joining names
            out.append(fact(out[0]["subject"], "id_hint", "P-" + pid.group(1), ["from event id"]))
        return out
