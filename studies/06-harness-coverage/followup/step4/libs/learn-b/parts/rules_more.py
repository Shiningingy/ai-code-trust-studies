import os
import json
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import fact, person, NAME, LEAD_NEUTRAL, LEAD_REPORTED  # noqa: E402
from common_stmt import Stmt  # noqa: E402
from gram import Rule  # noqa: E402
from rules_basic import obj  # noqa: E402

VEH = r"(?:train|bus|tram|subway|plane|ferry|bike|car)"


class Shift(Stmt):
    name = "works_shift"
    solves = ("'X works the day/night shift', also 'used to work/worked ... in a former role' (qualifier 'former role', "
              "'past' for used-to/worked)")
    added_by = "learning"
    pred = (r"(?P<past>used to\s+)?(?:works?|worked)\s+the\s+(?P<obj>day|night|evening|morning)\s+shift"
            r"(?P<former>\s+in a former role)?")
    examples = [("Hana Novak works the night shift in a former role.",
                 [fact("Hana Novak", "works_shift", "night", ["former role"])]),
                ("K. Laurent works the day shift.", [fact("Kofi Laurent", "works_shift", "day")])]

    def facts(self, s, m):
        q = []
        if m.group("past") or re.search(r"\bworked\b", m.string, re.I):
            q.append("past")
        if m.group("former"):
            q.append("former role")
        return [("works_shift", m.group("obj").lower(), q)]


class Travel(Stmt):
    name = "travels_by"
    solves = ("habitual travel 'X routinely travels by V' (also 'used to routinely travel by V but no longer does'; "
              "qualifiers 'routinely', 'past')")
    added_by = "learning"
    pred = (r"(?P<used>used to\s+)?(?:routinely\s+)?(?:travel|travels|travelled|traveled)\s+(?:by\s+)?(?P<obj>%s)"
            r"(?:\s+routinely)?(?P<nolonger>\s*,?\s*(?:but\s+)?(?:they\s+|he\s+|she\s+)?no longer (?:do|does))?"
            r"(?:\s+to work)?" % VEH)
    examples = [("Talia Usman routinely travels by bus.", [fact("Talia Usman", "travels_by", "bus", ["routinely"])]),
                ("Ben Ito routinely travels by tram but no longer does.",
                 [fact("Ben Ito", "travels_by", "tram", ["routinely", "past"])])]

    def facts(self, s, m):
        q = ["routinely"]
        if m.group("used") or m.group("nolonger"):
            q.append("past")
        return [("travels_by", m.group("obj").lower(), q)]


class UsedOnce(Stmt):
    name = "used_once"
    solves = "'X used the V once': a single use of a vehicle (qualifier 'once')"
    added_by = "learning"
    pred = r"used\s+the\s+(?P<obj>%s)\s+once" % VEH
    examples = [("Ben Ito used the tram once.", [fact("Ben Ito", "used", "tram", ["once"])])]

    def facts(self, s, m):
        return [("used", m.group("obj").lower(), ["once"])]


class PlansUse(Stmt):
    name = "plans_to_use"
    solves = "'X plans to use the V in the future': a plan, not a habit (qualifier 'future')"
    added_by = "learning"
    pred = r"plans? to use\s+the\s+(?P<obj>%s)\s+in the future" % VEH
    examples = [("Ben Khan plans to use the bus in the future.", [fact("Ben Khan", "plans_to_use", "bus", ["future"])])]

    def facts(self, s, m):
        return [("plans_to_use", m.group("obj").lower(), ["future"])]


class LikesEqually(Stmt):
    name = "likes_equally"
    solves = "'X likes V1 and V2 equally': no preference between two transport modes"
    added_by = "learning"
    pred = r"likes?\s+(?P<a>%s)\s+and\s+(?P<b>%s)\s+equally" % (VEH, VEH)
    examples = [("Isaac Reed likes train and plane equally.",
                 [fact("Isaac Reed", "likes_equally", "train", ["and plane"]),
                  fact("Isaac Reed", "likes_equally", "plane", ["and train"])])]

    def facts(self, s, m):
        a, b = m.group("a").lower(), m.group("b").lower()
        return [("likes_equally", a, ["and " + b]), ("likes_equally", b, ["and " + a])]


class Prefers(Stmt):
    name = "prefers"
    solves = "'X genuinely prefers V1 to V2 when both are available': a real preference for V1 over V2"
    added_by = "learning"
    pred = r"(?P<g>genuinely\s+)?prefers?\s+(?P<a>%s)\s+(?:to|over)\s+(?P<b>%s)(?P<w>\s+when both are available)?" % (VEH, VEH)
    examples = [("Omar Tran genuinely prefers train to plane when both are available.",
                 [fact("Omar Tran", "prefers", "train", ["genuinely", "over plane", "when both are available"])])]

    def facts(self, s, m):
        q = (["genuinely"] if m.group("g") else []) + ["over " + m.group("b").lower()]
        if m.group("w"):
            q.append("when both are available")
        return [("prefers", m.group("a").lower(), q)]


class Chose(Stmt):
    name = "chose"
    solves = "'X chose V1 over V2 only because of a disruption': a one-off forced choice, not a preference"
    added_by = "learning"
    pred = r"chose\s+(?:the\s+)?(?P<a>%s)\s+over\s+(?:the\s+)?(?P<b>%s)(?P<w>\s+(?:only\s+)?because of a disruption)?" % (VEH, VEH)
    examples = [("Omar Tran chose train over plane only because of a disruption.",
                 [fact("Omar Tran", "chose", "train", ["over plane", "only because of a disruption"])])]

    def facts(self, s, m):
        q = ["over " + m.group("b").lower()] + (["only because of a disruption" if "only" in m.group("w") else "because of a disruption"] if m.group("w") else [])
        return [("chose", m.group("a").lower(), q)]


DAIRY = r"(?:cheese|butter|milk|yogurt|yoghurt|cream|ice cream|kefir)"


class AvoidsDairy(Stmt):
    name = "avoids_dairy"
    solves = "'X currently chooses to avoid dairy products': an ongoing dietary avoidance (qualifier 'currently')"
    added_by = "learning"
    pred = r"(?P<cur>currently\s+)?(?:chooses? to avoid|avoids?)\s+(?P<obj>dairy products)"
    examples = [("Ben Ito currently chooses to avoid dairy products.",
                 [fact("Ben Ito", "avoids", "dairy products", ["currently"])])]

    def facts(self, s, m):
        return [("avoids", "dairy products", ["currently"] if m.group("cur") else [])]


class SkipsDairy(Stmt):
    name = "skips_dairy"
    solves = "'X is temporarily skipping cheese': a temporary avoidance of one dairy item (qualifier 'temporarily')"
    added_by = "learning"
    pred = r"(?:is|am) temporarily skipping\s+(?P<obj>%s)" % DAIRY
    examples = [("Amina Bennett is temporarily skipping cheese.",
                 [fact("Amina Bennett", "skips", "cheese", ["temporarily"])])]

    def facts(self, s, m):
        return [("skips", m.group("obj").lower(), ["temporarily"])]


class DislikesEating(Stmt):
    name = "dislikes_eating"
    solves = "'X dislikes eating F': a taste dislike (not a dietary avoidance)"
    added_by = "learning"
    pred = r"dislikes?\s+eating\s+(?P<obj>[a-z]+(?:\s+[a-z]+)?)"
    examples = [("Ben Ito dislikes eating milk.", [fact("Ben Ito", "dislikes_eating", "milk")])]

    def facts(self, s, m):
        return [("dislikes_eating", obj(m.group("obj")), [])]


class EnjoysEating(Stmt):
    name = "enjoys_eating"
    solves = "'X enjoys eating F' (F is a food; fruit names are not tagged here)"
    added_by = "learning"
    pred = r"(?P<past>used to\s+)?(?:simply\s+)?(?P<en>enjoy(?:s|ed)?)(?P<q>\s+eating)\s+(?P<obj>[a-z]+(?:\s+[a-z]+)?)"
    examples = [("Ben Ito enjoys eating pear.", [fact("Ben Ito", "enjoys_eating", "pear")])]

    def facts(self, s, m):
        return [("enjoys_eating", obj(m.group("obj")), ["past"] if (m.group("past") or m.group("en").lower() == "enjoyed") else [])]


class BuysFor(Stmt):
    name = "buys_for_others"
    solves = "'X buys cheese for other people': buying a dairy item for others, not eating it"
    added_by = "learning"
    pred = r"buys?\s+(?P<obj>[a-z]+(?:\s+[a-z]+)?)\s+for other people"
    examples = [("Ben Ito buys milk for other people.", [fact("Ben Ito", "buys_for_others", "milk")])]

    def facts(self, s, m):
        return [("buys_for_others", obj(m.group("obj")), [])]


class Went(Stmt):
    name = "went_to"
    solves = "'X went to the P (previously)': same as visited"
    added_by = "learning"
    pred = r"went to\s+the\s+(?P<obj>[a-z]+(?:\s+[a-z]+)?)(?:\s+(?P<t>some time ago|in the past|previously))?"
    examples = [("S. Gupta went to the museum.", [fact("Samir Gupta", "visited", "museum")])]

    def facts(self, s, m):
        return [("visited", obj(m.group("obj")), ["past"] if m.group("t") else [])]


class TalkedAbout(Stmt):
    name = "talked_about"
    solves = "'X talked about / mentioned T': same as discussed"
    added_by = "learning"
    pred = r"(?:talked about|mentioned)\s+(?!that\b|he\b|she\b|they\b)(?P<obj>[a-z]+(?:\s+[a-z]+){0,3})"
    examples = [("Ben Ito talked about the chess club.", [fact("Ben Ito", "discussed", "chess club")])]

    def facts(self, s, m):
        return [("discussed", obj(m.group("obj")), [])]


class Roster(Rule):
    name = "roster"
    solves = ("'the community roster records X under identifier P-n and also uses the familiar names Y': "
              "links a person's full name, person id and alias (join key for initials)")
    added_by = "learning"
    examples = [("The community roster records Mateo Laurent under identifier P-153 and also uses the familiar names M. Laurent.",
                 [fact("Mateo Laurent", "has_id", "P-153"), fact("Mateo Laurent", "also_known_as", "M. Laurent")])]
    _rx = re.compile(r'"?(?:(?:%s|%s)[,\s]\s*"?){0,2}the community roster (?:records|lists)\s+(?P<n>%s)\s+under identifier\s+'
                     r'(?P<id>P-\d+)(?:\s+and also uses the familiar names?\s+(?P<a>.+?))?[\s.,"]*' % (LEAD_NEUTRAL, LEAD_REPORTED, NAME), re.I)

    def parse(self, clause):
        m = self._rx.fullmatch(clause.strip())
        if not m:
            return None
        s = person(m.group("n"))
        out = [fact(s, "has_id", m.group("id").upper())]
        for a in re.split(r"\s*(?:,|\band\b)\s*", m.group("a") or ""):
            if a.strip():
                out.append(fact(s, "also_known_as", re.sub(r"\s+", " ", a.strip()).title()))
        return out


class Conjoined(Rule):
    name = "conjoined_predicates"
    solves = ("one subject with two predicates joined by 'and' ('X visited the museum and owns a guitar'): each half is "
              "parsed as its own clause with the same subject and lead-in")
    added_by = "learning"
    examples = [("Ben Ortiz visited the museum and owns a guitar.",
                 [fact("Ben Ortiz", "visited", "museum"), fact("Ben Ortiz", "owns", "guitar")])]
    _head = re.compile(r'^((?:"?\s*(?:%s|%s)[,\s]\s*"?){0,2}%s)\s+' % (LEAD_NEUTRAL, LEAD_REPORTED, NAME), re.I)

    def _one(self, text):
        from common_stmt import Stmt
        res = []
        for cls in Stmt.registry:
            f = cls().parse(text)
            if f:
                res.append(f)
        return res[0] if len({json.dumps(r, sort_keys=True) for r in res}) == 1 else None

    def parse(self, clause):
        text = clause.strip()
        h = self._head.match(text)
        if not h or " and " not in text:
            return None
        head = h.group(1)
        for m in re.finditer(r"\s+and\s+", text):
            left, right = text[:m.start()], text[m.end():]
            if not re.match(r"(?:visited|owns|attends|discussed|recommended|helped|works|enjoys|buys|volunteered|travels)", right, re.I):
                continue
            a, b = self._one(left), self._one(head + " " + right)
            if a and b:
                return a + b
        return None
