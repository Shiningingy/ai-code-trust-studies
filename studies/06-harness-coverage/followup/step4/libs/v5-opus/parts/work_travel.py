"""Work (employer, shift), where organisations are based, and how people travel."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import FactRule, add, fact  # noqa: E402
from gram import Rule  # noqa: E402


class WorksFor(FactRule, Rule):
    name = "works_for"
    solves = ("employment: '<person> (currently) works for Organization 010 / Org 010' and the past forms "
              "('used to work for', 'worked for ... in a former role')")
    added_by = "learning"
    phrases = [r"(?P<v>works|work|worked|is employed|was employed|is working|am working) (?:for|at|by) "
               r"(?P<o>%s)" % C.ORG]
    examples = [
        ("Omar Usman currently works for Organization 010.",
         [fact("Omar Usman", "works_for", "Organization 010", ["time:current"])]),
        ("Quinn Tran currently works for Org 024", [fact("Quinn Tran", "works_for", "Organization 024",
                                                         ["time:current"])]),
        ("I. Usman works for Org 022.", [fact("I. Usman", "works_for", "Organization 022")]),
    ]

    def facts(self, s, g, q):
        if g["v"].lower() in ("worked", "was employed"):
            q = add(q, "time:past")
        return [fact(s, "works_for", C.org(g["o"]), q)]


class WorksShift(FactRule, Rule):
    name = "works_shift"
    solves = ("shift work: '<person> works the night/day shift', with the past forms 'in a former role', 'used to "
              "work', 'worked'")
    added_by = "learning"
    phrases = [r"(?P<v>works|work|worked|is working|am working|is on|am on|was on) (?:the |a |an )?"
               r"(?P<o>night|day|evening|morning|early|late|weekend|overnight)[ -]shifts?"]
    examples = [
        ("Leah Avery works the night shift.", [fact("Leah Avery", "works_shift", "night")]),
        ("Ben Ito works the night shift in a former role.",
         [fact("Ben Ito", "works_shift", "night", ["time:past"])]),
        ("I used to work the night shift", [fact("I", "works_shift", "night", ["time:past"])]),
    ]

    def facts(self, s, g, q):
        if g["v"].lower() in ("worked", "was on"):
            q = add(q, "time:past")
        return [fact(s, "works_shift", g["o"].lower(), q)]


class BasedIn(FactRule, Rule):
    name = "based_in"
    solves = "where an organisation is: 'Organization 009 is based in Vancouver' (also 'Org 023', 'St. John's')"
    added_by = "learning"
    subject = C.ORG
    person_subject = False
    phrases = [r"(?:is|was) (?:based|located|headquartered) in (?P<o>[A-Z][A-Za-z'.-]*(?: [A-Z][A-Za-z'.-]*)*)"]
    examples = [
        ("Organization 009 is based in Vancouver.", [fact("Organization 009", "based_in", "Vancouver")]),
        ("Org 023 is based in St. John's", [fact("Organization 023", "based_in", "St. John's")]),
        ("organization 001 is based in Halifax", [fact("Organization 001", "based_in", "Halifax")]),
    ]

    def facts(self, s, g, q):
        return [fact(C.org(s), "based_in", C.city(g["o"]), q)]


class Travels(FactRule, Rule):
    name = "travels_by"
    solves = ("how a person travels: 'routinely travels by <mode>' (habit), '... but no longer does' and 'used to "
              "routinely travel' (past habit), 'used the <mode> once' (one-off), 'plans to use the <mode> in the "
              "future' (future); the frequency and time words become qualifiers")
    added_by = "learning"
    phrases = [r"(?P<v>travels|travel|traveled|travelled|commutes|commute|commuted|gets around|get around|rides|"
               r"ride|rode|takes|take|took|uses|use|used) (?:by |on |with )?(?:the |a )?(?P<o>%s)(?= |$|,)"
               r"(?: (?P<adv2>routinely|regularly|daily|every day))?" % C.MODE]
    examples = [
        ("S. Haddad routinely travels by bus.", [fact("S. Haddad", "travels_by", "bus", ["freq:routinely"])]),
        ("Kofi Patel used to routinely travel by tram but no longer does.",
         [fact("Kofi Patel", "travels_by", "tram", ["time:past", "freq:routinely"])]),
        ("A. Gupta routinely travels by bus but no longer does.",
         [fact("A. Gupta", "travels_by", "bus", ["freq:routinely", "time:past"])]),
        ("J. Evans used the tram once.", [fact("J. Evans", "travels_by", "tram", ["freq:once"])]),
        ("Farah Reed plans to use the bus in the future.",
         [fact("Farah Reed", "travels_by", "bus", ["time:future"])]),
        ("N. Lee used to travel by train routinely, but no longer does.",
         [fact("N. Lee", "travels_by", "train", ["time:past", "freq:routinely"])]),
    ]

    def facts(self, s, g, q):
        v = g["v"].lower()
        if g["adv2"]:
            q = add(q, "freq:routinely")
        if v in ("traveled", "travelled", "commuted", "rode", "took") and "freq:routinely" in q:
            q = add(q, "time:past")
        if v == "used" and "time:past" not in q and "freq:once" not in q and "freq:routinely" not in q:
            return None
        return [fact(s, "travels_by", g["o"].lower(), q)]


class TravelPreference(FactRule, Rule):
    name = "travel_preference"
    solves = ("preferences between two modes: 'genuinely prefers <mode> to <mode> when both are available' "
              "(relation prefers_over), 'likes <mode> and <mode> equally' (likes_equally), 'chose <mode> over "
              "<mode> (only) because of a disruption' (chose_over, reason:disruption)")
    added_by = "learning"
    phrases = [
        r"(?P<v>prefers|prefer|preferred) (?:the )?(?P<a>%s) (?:to|over) (?:the )?(?P<b>%s)"
        r"(?P<both> when both are available)?" % (C.MODE, C.MODE),
        r"(?P<v>likes|like|liked|enjoys|enjoy) (?:the )?(?P<a>%s) and (?:the )?(?P<b>%s) (?P<eq>equally)"
        % (C.MODE, C.MODE),
        r"(?P<v>chose|chooses|choose|picked|took) (?:the )?(?P<a>%s) over (?:the )?(?P<b>%s)"
        r"(?P<why>(?: only)? because of (?:a |the )?(?P<r>[a-z]+(?: [a-z]+)?))?" % (C.MODE, C.MODE),
    ]
    examples = [
        ("Ben Ito genuinely prefers train to plane when both are available.",
         [fact("Ben Ito", "prefers_over", "train", ["over:plane", "genuinely", "when both are available"])]),
        ("Ben Ito likes train and plane equally.", [fact("Ben Ito", "likes_equally", "train", ["and:plane"]),
                                                    fact("Ben Ito", "likes_equally", "plane", ["and:train"])]),
        ("Ben Ito chose train over plane only because of a disruption.",
         [fact("Ben Ito", "chose_over", "train", ["over:plane", "reason:disruption", "only because"])]),
    ]

    def facts(self, s, g, q):
        a, b = g["a"].lower(), g["b"].lower()
        if g.get("eq"):
            return [fact(s, "likes_equally", a, add(["and:" + b], *q)), fact(s, "likes_equally", b, add(["and:" + a], *q))]
        if g["v"].lower().startswith("pref"):
            return [fact(s, "prefers_over", a, add(["over:" + b], *q) + (["when both are available"] if g["both"] else []))]
        extra = []
        if g.get("why"):
            extra.append("reason:" + g["r"].lower())
            if "only" in g["why"]:
                extra.append("only because")
        return [fact(s, "chose_over", a, add(["over:" + b], *q) + extra)]
