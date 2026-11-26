"""Rules for personal-profile clauses: employer, organisation city, shifts, travel habits, diet, roster identity, youth."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gram import PatternRule  # noqa: E402
from common import (pat, PRE, who, TAIL, mk, canon_org, canon_pid, canon_name, canon_youth,  # noqa: E402
                    quals_of, tail_ok, ORG, YOUTH, NAME)


def F(s, rel, obj="", q=()):
    return {"subject": s, "relation": rel, "object": obj, "qualifiers": list(q)}


class WorksFor(PatternRule):
    name = "works_for"
    solves = "'X (currently) works for Org NNN' (Org / Organization, any case): employer; 'currently' kept as qualifier"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?P<cur>currently\s+)?(?:works?|worked)\s+for\s+(?P<o>%s)" % ORG + TAIL)
    examples = [
        ("E. Mensah currently works for Org 020", [F("E. Mensah", "works_for", "Org 020", ["currently"])]),
        ("G. Foster works for Organization 011", [F("G. Foster", "works_for", "Org 011")]),
    ]

    def build(self, g):
        return mk(g, "works_for", canon_org(g["o"]), *(["currently"] if g["cur"] else []))


class BasedIn(PatternRule):
    name = "based_in"
    solves = "'Org NNN is based in CITY': the city an organisation is based in (city names may contain 'St. John's')"
    added_by = "learning"
    flags = re.I
    pattern = r"(?P<o>%s)\s+is based in\s+(?P<c>[A-Za-z][\w.' -]*?)" % ORG + TAIL
    examples = [
        ("Org 026 is based in Calgary", [F("Org 026", "based_in", "Calgary")]),
        ("org 003 is based in St. John's", [F("Org 003", "based_in", "St. John's")]),
    ]

    def build(self, g):
        if not tail_ok(g):
            return None
        return [F(canon_org(g["o"]), "based_in", " ".join(w[:1].upper() + w[1:] for w in g["c"].split()), quals_of(g))]


class Shift(PatternRule):
    name = "shift"
    solves = "work shift: 'works the day/night shift', 'worked/used to work the night shift in a former role'"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?P<pre>(?:currently\s+)?(?:used to\s+)?)(?P<v>works?|worked)\s+(?:the\s+|a\s+)?(?P<sh>\w+)\s+shift" + TAIL)
    examples = [
        ("P. Foster works the day shift", [F("P. Foster", "works_shift", "day")]),
        ("Samir Mensah works the night shift in a former role", [F("Samir Mensah", "works_shift", "night", ["in a former role"])]),
        ("Ben Ito used to work the night shift", [F("Ben Ito", "works_shift", "night", ["used to"])]),
    ]

    def build(self, g):
        q = [w for w in ("currently", "used to") if w in g["pre"].lower()]
        if g["v"].lower() == "worked":
            q.append("formerly")
        return mk(g, "works_shift", g["sh"].lower(), *q)


class RoutineTravel(PatternRule):
    name = "routine_travel"
    solves = "'X routinely travels by M' (also 'used to routinely travel by M but no longer does'): habitual transport"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?P<pre>used to\s+)?(?:routinely\s+travel(?:s|ed)?\s+by\s+(?P<m>\w+)|travels?\s+by\s+(?P<m2>\w+)\s+routinely)" + TAIL)
    examples = [
        ("Talia Reed routinely travels by tram", [F("Talia Reed", "travels_by", "tram", ["routinely"])]),
        ("Dev Chen routinely travels by subway but no longer does", [F("Dev Chen", "travels_by", "subway", ["routinely", "no longer"])]),
        ("Ana Diaz used to routinely travel by bus but no longer does", [F("Ana Diaz", "travels_by", "bus", ["used to", "routinely", "no longer"])]),
    ]

    def build(self, g):
        return mk(g, "travels_by", (g["m"] or g["m2"]).lower(), *((["used to"] if g["pre"] else []) + ["routinely"]))


class PlansTravel(PatternRule):
    name = "plans_travel"
    solves = "'X plans to use the M in the future': intended, not current, transport"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"plans to use\s+(?:the\s+)?(?P<m>\w+)" + TAIL)
    examples = [("Q. Silva plans to use the bus in the future", [F("Q. Silva", "plans_to_use", "bus", ["in the future"])])]

    def build(self, g):
        return mk(g, "plans_to_use", g["m"].lower())


class UsedOnce(PatternRule):
    name = "used_once"
    solves = "'X used the M once': a single past use of a transport mode (not a habit)"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"used\s+(?:the\s+)?(?P<m>\w+)\s+once" + TAIL)
    examples = [("Elena Khan used the tram once", [F("Elena Khan", "used", "tram", ["once"])])]

    def build(self, g):
        return mk(g, "used", g["m"].lower(), "once")


class LikesEqually(PatternRule):
    name = "likes_equally"
    solves = "'X likes train and plane equally': no preference between two transport modes"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"likes?\s+(?P<a>\w+)\s+and\s+(?P<b>\w+)\s+equally" + TAIL)
    examples = [("D. Haddad likes train and plane equally", [F("D. Haddad", "likes_equally", "train and plane")])]

    def build(self, g):
        return mk(g, "likes_equally", "%s and %s" % (g["a"].lower(), g["b"].lower()))


class PrefersOver(PatternRule):
    name = "prefers_over"
    solves = "'X genuinely prefers train to plane when both are available': a real preference between two modes"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?P<g>genuinely\s+)?prefers?\s+(?P<a>\w+)\s+to\s+(?P<b>\w+)(?P<w>\s+when both are available)?" + TAIL)
    examples = [("A. Chen genuinely prefers train to plane when both are available",
                 [F("A. Chen", "prefers_over", "train over plane", ["genuinely", "when both are available"])])]

    def build(self, g):
        q = (["genuinely"] if g["g"] else []) + (["when both are available"] if g["w"] else [])
        return mk(g, "prefers_over", "%s over %s" % (g["a"].lower(), g["b"].lower()), *q)


class ChoseOver(PatternRule):
    name = "chose_over"
    solves = "'X chose train over plane (only) because of a disruption': a one-off forced choice, not a preference"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"chose\s+(?:the\s+)?(?P<a>\w+)\s+over\s+(?:the\s+)?(?P<b>\w+)(?P<why>\s+(?:only\s+)?because of a disruption)?" + TAIL)
    examples = [("N. Foster chose train over plane only because of a disruption",
                 [F("N. Foster", "chose_over", "train over plane", ["only because of a disruption"])])]

    def build(self, g):
        return mk(g, "chose_over", "%s over %s" % (g["a"].lower(), g["b"].lower()),
                  *(["only because of a disruption"] if g["why"] else []))


class AvoidsDairy(PatternRule):
    name = "avoids_dairy"
    solves = "'X currently chooses to avoid dairy products' (also 'I currently choose'): a current dietary avoidance"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?P<cur>currently\s+)?(?:(?:chooses?|choosing)\s+to\s+avoid|avoids?)\s+(?P<o>dairy products)" + TAIL)
    examples = [("Nadia Ortiz currently chooses to avoid dairy products",
                 [F("Nadia Ortiz", "avoids", "dairy products", ["currently"])])]

    def build(self, g):
        return mk(g, "avoids", "dairy products", *(["currently"] if g["cur"] else []))


class Skipping(PatternRule):
    name = "skipping"
    solves = "'X is temporarily skipping cheese': a temporary avoidance of one dairy item"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?:is|am|are)\s+(?P<t>temporarily\s+)?skipping\s+(?P<o>\w+)" + TAIL)
    examples = [("J. Foster is temporarily skipping butter", [F("J. Foster", "skips", "butter", ["temporarily"])])]

    def build(self, g):
        return mk(g, "skips", g["o"].lower(), *(["temporarily"] if g["t"] else []))


class BuysForOthers(PatternRule):
    name = "buys_for_others"
    solves = "'X buys cheese for other people': buys a food only for others (does not imply eating it)"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"buys?\s+(?P<o>\w+)\s+for other people" + TAIL)
    examples = [("Ana Reed buys milk for other people", [F("Ana Reed", "buys_for_others", "milk")])]

    def build(self, g):
        return mk(g, "buys_for_others", g["o"].lower())


class ServesOthers(PatternRule):
    name = "serves_others"
    solves = "'X serves banana to other people but does not eat it': serves a food to others and does not eat it"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"serves\s+(?P<o>\w+)\s+to other people but does not eat it" + TAIL)
    examples = [("F. Reed serves banana to other people but does not eat it",
                 [F("F. Reed", "serves_to_others", "banana", ["does not eat it"])])]

    def build(self, g):
        return mk(g, "serves_to_others", g["o"].lower(), "does not eat it")


class Eating(PatternRule):
    name = "eating"
    solves = "'X enjoys eating FOOD' / 'dislikes eating FOOD' (also 'used to enjoy', '... in the past')"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?P<used>used to\s+)?(?:simply\s+)?(?P<v>enjoys?|enjoyed|dislikes?|disliked)\s+eating\s+(?P<o>\w+)" + TAIL)
    examples = [
        ("F. Avery enjoys eating banana", [F("F. Avery", "enjoys_eating", "banana")]),
        ("Q. Silva dislikes eating milk", [F("Q. Silva", "dislikes_eating", "milk")]),
        ("Lia Haddad enjoys eating pear in the past", [F("Lia Haddad", "enjoys_eating", "pear", ["in the past"])]),
        ("Lia Haddad used to enjoy eating mango", [F("Lia Haddad", "enjoys_eating", "mango", ["used to"])]),
    ]

    def build(self, g):
        v = g["v"].lower()
        rel = "enjoys_eating" if v.startswith("enjoy") else "dislikes_eating"
        return mk(g, rel, g["o"].lower(), *(["used to"] if g["used"] else []) + (["formerly"] if v.endswith("ed") else []))


class Roster(PatternRule):
    name = "roster"
    solves = ("'the community roster records NAME under identifier P-NNN and also uses the familiar names ALIAS': identity "
              "facts that join the person's written forms (full name, initial form, P-id)")
    added_by = "learning"
    flags = re.I
    pattern = PRE + (r"the community roster (?:records|lists)\s+(?P<n>%s|me)\s+under identifier\s+(?P<id>p-\d+)(?:\s+and also uses the "
               r"familiar names?\s+(?P<a>.+?))?" % NAME) + TAIL
    examples = [("The community roster records Amina Bennett under identifier P-021 and also uses the familiar names A. Bennett",
                 [F("Amina Bennett", "has_id", "P-021"), F("P-021", "has_name", "Amina Bennett"),
                  F("Amina Bennett", "also_called", "A. Bennett")])]

    def build(self, g):
        n, pid = (who({"s": "I", "sp": g["sp"]}) if g["n"].lower() == "me" else canon_name(g["n"])), canon_pid(g["id"])
        if n is None:
            return None
        out = [F(n, "has_id", pid), F(pid, "has_name", n)]
        for a in re.split(r"\s*(?:,|\band\b)\s*", g["a"]) if g["a"] else []:
            if a.strip():
                out.append(F(n, "also_called", canon_name(a)))
        return out


class YouthCourse(PatternRule):
    name = "youth_course"
    solves = "'Y028 currently attends COURSE during the evening/day': the course a youth attends and when it is held"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?P<cur>currently\s+)?attends?\s+(?P<c>\w+)\s+during the\s+(?P<t>\w+)" + TAIL)
    examples = [("Youth 077 currently attends evening_carpentry during the evening",
                 [F("Y077", "attends_course", "evening_carpentry", ["currently", "evening"])])]

    def build(self, g):
        return mk(g, "attends_course", g["c"].lower(), *((["currently"] if g["cur"] else []) + [g["t"].lower()]))


class Guardian(PatternRule):
    name = "guardian"
    solves = "'X is the legal guardian of Y028': guardianship of a youth"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?:is|am|are)\s+(?:the\s+)?legal guardian of\s+(?P<y>%s)" % YOUTH + TAIL)
    examples = [("Omar Bennett is the legal guardian of Youth 075", [F("Omar Bennett", "legal_guardian_of", "Y075")])]

    def build(self, g):
        return mk(g, "legal_guardian_of", canon_youth(g["y"]))


class EmergencyContact(PatternRule):
    name = "emergency_contact"
    solves = "'X is an emergency contact (, but not a guardian,) for Y028': a contact who may explicitly not be a guardian"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"(?:is|am|are)\s+(?:listed as\s+)?an?\s+emergency contact(?P<ng>,?\s*(?:but )?not a guardian,?)?\s+for\s+(?P<y>%s)(?P<ng2>,?\s*(?:but )?not a guardian)?" % YOUTH + TAIL)
    examples = [("R. Bennett is an emergency contact, but not a guardian, for Youth 058",
                 [F("R. Bennett", "emergency_contact_of", "Y058", ["not a guardian"])]),
                ("M. Ito is an emergency contact for Y012", [F("M. Ito", "emergency_contact_of", "Y012")])]

    def build(self, g):
        return mk(g, "emergency_contact_of", canon_youth(g["y"]), *(["not a guardian"] if g["ng"] or g["ng2"] else []))


class UsedToTake(PatternRule):
    name = "used_to_take"
    solves = "'X used to take the M most weekdays': a past habitual use of a transport mode (frequency kept as qualifier)"
    added_by = "learning"
    flags = re.I
    pattern = pat(r"used to take\s+(?:the\s+)?(?P<m>\w+)(?P<f>\s+most weekdays)?" + TAIL)
    examples = [("Leah Usman said, \"I used to take the tram most weekdays",
                 [F("Leah Usman", "travels_by", "tram", ["used to", "most weekdays"])])]

    def build(self, g):
        return mk(g, "travels_by", g["m"].lower(), "used to", *(["most weekdays"] if g["f"] else []))
