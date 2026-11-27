"""Rules for clauses about one person (subject = a person name, or a Youth id for course attendance).

Every rule shares PersonRule: it finds the subject (plain, or the speaker of a quote such as `X said, "I own a camera"`),
turns first-person wording into third person, and matches the rest against the rule's own patterns.
"""
import os
import re
import sys
from abc import abstractmethod

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (THINGS, BOOKS, TITLE, NAME, YOUTH, PLACES, CLUBS, TRANSIT, DAIRY, EVENT, ORG, canon_name, canon_youth, canon_org, fact)  # noqa: E402
from gram import Rule  # noqa: E402

SUBJ = r"(?:%s|%s)" % (NAME, YOUTH)
SAY = (r"(?:said|says|explains|explained|added|mentioned|noted|stated|continued|recalled|concluded|agreed|replied|answered|confirmed|wrote in the volunteer log|"
       r"wrote in the log)")
QUOTE_OPEN = "[\"“]"

# first person -> third person verb forms (the corpus also contains agreement slips such as "I attends")
FIRST = {
    "own": "owns", "owns": "owns", "attend": "attends", "attends": "attends", "work": "works", "works": "works",
    "travel": "travels", "travels": "travels", "plan": "plans", "plans": "plans", "enjoy": "enjoys", "enjoys": "enjoys",
    "dislike": "dislikes", "dislikes": "dislikes", "like": "likes", "likes": "likes", "buy": "buys", "buys": "buys",
    "serve": "serves", "serves": "serves", "prefer": "prefers", "prefers": "prefers", "choose": "chooses",
    "chooses": "chooses", "volunteer": "volunteered", "am": "is", "is": "is", "go": "goes", "do": "does",
    "keep": "keeps", "discuss": "discussed", "recommend": "recommended", "visit": "visited", "help": "helped",
}
ADV = r"(?:currently|genuinely|also|routinely|only|previously|formerly|temporarily)"


def third_person(rest):
    """'I currently work for Org 007' -> 'currently works for Org 007'; 'I no longer do' -> 'no longer does'."""
    rest = re.sub(r"\bI\b", "SELF", rest)
    rest = re.sub(r"\bmy\b", "their", rest)
    out, i, words = [], 0, rest.split(" ")
    # the first verb (after optional adverbs) and any 'no longer do/go' get third-person forms
    seen_verb = False
    for w in words:
        lw = w.lower().rstrip(",")
        if not seen_verb and re.fullmatch(ADV, lw):
            out.append(w)
            continue
        if not seen_verb and lw in FIRST:
            out.append(FIRST[lw] + w[len(lw):])
            seen_verb = True
            continue
        seen_verb = True
        if lw in ("do", "go") and out and out[-1].rstrip(",") == "longer":
            out.append({"do": "does", "go": "goes"}[lw] + w[len(lw):])
            continue
        out.append(w)
    return " ".join(out).replace("SELF ", "")


ADJUNCT = re.compile(
    r" (?:to|for|after|before|during|on|at|with|as|so|because|when|while|over|that|which|there|used|usually|often|simply|nearby|afterward|instead|too|again|together|here|we|"
    r"last|earlier|later|this|every|each|in the|and (?:bought|picked|checked|mentioned|brought|enjoy|shares|help|helped|"
    r"checked|usually|often|is|was|were|it|they|he|she|we|the|uses|plays|sometimes)).*")
FACT_VERB = re.compile(r"(?<![A-Za-z])(?:owns|recommended|suggested|discussed|visited|attends|attended|volunteered|works|worked|"
                       r"travels|enjoys|dislikes|prefers|chose|buys|serves|avoids|guardian|emergency)(?![A-Za-z])")


def split_subject(clause):
    """Return (subject, rest, extra_qualifiers) or None. rest is third-person wording."""
    t = clause.strip().strip("\"“”").rstrip(".").strip()
    m = re.fullmatch(r"(%s),? %s,? ?%s?\s*I (.*)" % (SUBJ, SAY, QUOTE_OPEN), t)
    if not m:
        m = re.fullmatch(r"(%s): ?%s?I (.*)" % (SUBJ, QUOTE_OPEN), t)
    if m:
        return subj_canon(m.group(1)), third_person(m.group(2)), ["quoted"]
    m = re.fullmatch(r"(%s),? %s(?: that)? (?:he|she|they) (.*)" % (SUBJ, SAY), t)
    if m:
        return subj_canon(m.group(1)), m.group(2), ["quoted"]
    m = re.fullmatch(r"(%s),? %s that (%s) (.*)" % (SUBJ, SAY, SUBJ), t)
    if m:
        return subj_canon(m.group(2)), m.group(3), ["reported"]
    m = re.fullmatch(r"I, ((?:[A-Za-z]\.|[A-Za-z]{2,}) [A-Za-z]{2,}), (.*)", t)
    if m:
        return subj_canon(m.group(1)), m.group(2), []
    m = re.fullmatch(r"(%s) (.*)" % SUBJ, t)
    if m:
        return subj_canon(m.group(1)), m.group(2), []
    return None


def subj_canon(s):
    return canon_youth(s) if re.fullmatch(YOUTH, s) else canon_name(s)


def low(s):
    return s.strip().lower()


class PersonRule(Rule):
    """Base: subclasses list `patterns` (regexes over the third-person rest) and implement build(m, subject)."""
    patterns = []
    _rxs = None

    def parse(self, clause):
        sp = split_subject(clause)
        if not sp:
            return None
        subj, rest, extra = sp
        rest = re.sub(r"^also ", "", rest)
        if self._rxs is None:
            type(self)._rxs = [re.compile(p) for p in self.patterns]
        # the whole rest is the core wording, or a core followed by a descriptive adjunct ("to pick up supplies")
        cuts = [(len(rest), "")] + [(i, rest[i:]) for i in range(len(rest) - 1, 0, -1)
                                    if rest[i] == " " and ADJUNCT.fullmatch(rest[i:]) and not FACT_VERB.search(rest[i:])]
        for i, adj in cuts:
            core = rest[:i]
            for rx in self._rxs:
                m = rx.fullmatch(core)
                if not m:
                    continue
                facts = self.build(m.groupdict(""), subj)
                if facts is None:
                    return None
                for f in facts:
                    for q in extra + (["detail:" + adj] if adj else []):
                        if q not in f["qualifiers"]:
                            f["qualifiers"].append(q)
                return facts
        return None

    @abstractmethod
    def build(self, g, subj):
        """Return the facts for a matched clause."""


# decorations that carry no fact (who was told, where it was said); matched as fixed wording
DECOR = (r"(?: (?:to (?:the group|me|a friend|a colleague|the team|several people|everyone|us)|for the (?:next outing|reading list)|"
         r"as a good read|as well|too|also|with the (?:team|group)|in the (?:group chat|team chat|volunteer log)|"
         r"during the (?:meeting|shift handoff|volunteer log|conversation|interview)|after the event|over lunch))?")
PAST_TAIL = (r"(?: (?P<t>some time ago|in the past|previously|recently|more recently|last week|last weekend|yesterday|"
             r"this morning|earlier|lately|on (?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)|"
             r"later that (?:day|afternoon)|that same (?:afternoon|week)))?(?: (?:nearby|instead|too|as well))?")
FREQ = (r"(?: (?P<f>every (?:Tuesday|Monday|Wednesday|Thursday|Friday|Saturday|Sunday|week|morning|evening|day)|on weekends|"
        r"on (?:Mondays|Tuesdays|Wednesdays|Thursdays|Fridays|Saturdays|Sundays)|regularly|now|weekly|daily))?")


def time_quals(t):
    t = (t or "").strip()
    if not t:
        return []
    if t in ("some time ago", "in the past", "previously", "lately", "earlier", "yesterday", "last week", "last weekend"):
        return ["past", t] if t != "past" else ["past"]
    return [t]


class Owns(PersonRule):
    name = "owns_item"
    solves = "a person owns an item ('owns a camera', 'owns a garden tools set', 'has a guitar', 'I own ...')"
    added_by = "learning"
    patterns = [r"(?:owns|has|keeps) (?:an? |a set of |my )?(?P<obj>(?i:%s))(?: set| kit| collection)?(?: (?P<x>as well|too))?(?: for repairs)?" % THINGS,
                r"(?:owns|has|keeps) (?P<obj>(?i:%s))" % THINGS]
    examples = [
        ("B. Ito owns a garden tools.", [fact("B. Ito", "owns", "garden tools")]),
        ('A. Haddad said, "I own a telescope', [fact("A. Haddad", "owns", "telescope", ["quoted"])]),
    ]

    def build(self, g, s):
        return [fact(s, "owns", low(g["obj"]))]


class Recommended(PersonRule):
    name = "recommended_book"
    solves = "a person recommended (or suggested) a book, with optional recipient wording"
    added_by = "learning"
    patterns = [r"(?:also )?(?:recommended|suggested) (?P<obj>(?i:%s)|%s)" % (BOOKS, TITLE) + DECOR]
    examples = [
        ("Hana Ortiz recommended Quiet Machines.", [fact("Hana Ortiz", "recommended", "quiet machines")]),
        ("N. Silva suggested The Long Orchard", [fact("N. Silva", "recommended", "the long orchard")]),
    ]

    def build(self, g, s):
        o = low(g["obj"])
        return [fact(s, "recommended", o)]


class Discussed(PersonRule):
    name = "discussed_topic"
    solves = "a person discussed (talked about, mentioned) a place, a club or a book"
    added_by = "learning"
    patterns = [r"(?:discussed|talked about|mentioned) (?:the )?(?P<obj>(?i:%s|%s|%s)|%s)"
                r"(?: (?!(?:and|but|with|to|for|as|during|in|on|at|after|before|that|which|when|so|because|nearby|too|again|afterward|instead)(?![A-Za-z']))[a-z]+){0,2}%s" % (PLACES, CLUBS, BOOKS, TITLE, DECOR)]

    examples = [
        ("Priya Haddad discussed chess club.", [fact("Priya Haddad", "discussed", "chess club")]),
        ("Nadia Mensah discussed the riverside park trends", [fact("Nadia Mensah", "discussed", "riverside park")]),
    ]

    def build(self, g, s):
        return [fact(s, "discussed", low(g["obj"]))]


class Visited(PersonRule):
    name = "visited_place"
    solves = "a person visited (went to) a place, with a time wording such as 'some time ago', 'in the past', 'previously'"
    added_by = "learning"
    patterns = [r"(?:(?P<pre>previously|formerly|also) )?(?:had )?(?:visited|visit|went to) the (?P<obj>(?i:%s))%s" % (PLACES, PAST_TAIL),
                r"(?:(?P<pre>previously|formerly) )?(?:visited|went to) the (?P<obj>(?i:%s)) (?P<t>some time ago) in the past" % PLACES]
    examples = [
        ("M. Khan visited the library some time ago.", [fact("M. Khan", "visited", "library", ["past", "some time ago"])]),
        ("O. Bennett visited the riverside park", [fact("O. Bennett", "visited", "riverside park")]),
        ("Ben Haddad previously visited the market", [fact("Ben Haddad", "visited", "market", ["past", "previously"])]),
    ]

    def build(self, g, s):
        t = g.get("t") or (g.get("pre") if g.get("pre") != "also" else "")
        return [fact(s, "visited", low(g["obj"]), time_quals(t))]


class Helped(PersonRule):
    name = "helped_with_task"
    solves = "a person helped (assisted) with registration, setup or cleanup at a place"
    added_by = "learning"
    patterns = [r"(?:helped|assisted) with (?P<task>registration|setup|cleanup) at the (?P<obj>(?i:%s))%s(?: after the event)?" % (PLACES, PAST_TAIL)]
    examples = [
        ("Nadia Patel helped with setup at the market", [fact("Nadia Patel", "helped_with_setup", "market")]),
    ]

    def build(self, g, s):
        return [fact(s, "helped_with_" + g["task"], low(g["obj"]), time_quals(g.get("t")))]


class Attends(PersonRule):
    name = "attends_club"
    solves = ("a person attends a club, including 'only in the past', 'used to attend ... but no longer does', "
              "'previously attended', 'no longer attends' (all marked past) and frequency words ('every Tuesday')")
    added_by = "learning"
    C = r"the (?P<obj>(?i:%s))" % CLUBS
    NL = (r"(?:,? (?:but|and) (?:(?:he|she|they) )?(?:no longer (?:does|goes|attends|participates in (?:their|his|her) weekly \w+)|"
          r"(?:that is|which is) in the past(?: now)?|that is past|does not attend now|does not attend)|, but only in the past"
          r"|, but (?:he|she|they) no longer does)")
    patterns = [
        r"attends " + C + r"(?: (?P<p>only in the past|in the past))?" + FREQ + r"(?: as well)?(?P<nl>" + NL + r")?",
        r"(?P<p>no longer) attends " + C,
        r"(?P<u>used to attends?|previously attended|formerly attended|attended|used to be a member of) " + C
        + r"(?: (?P<p2>only in the past|in the past))?(?P<nl>" + NL + r")?",
        r"used to (?:attend|be a member of) " + C + r" only in the past",
    ]
    examples = [
        ("Leah Avery attends the chess club.", [fact("Leah Avery", "attends", "chess club")]),
        ("T. Patel attends the walking group only in the past", [fact("T. Patel", "attends", "walking group", ["past", "only in the past"])]),
        ("Priya Khan used to attend the chess club, but no longer does", [fact("Priya Khan", "attends", "chess club", ["past", "used to", "no longer"])]),
        ("Ben Novak attends the history group every Tuesday", [fact("Ben Novak", "attends", "history group", ["every Tuesday"])]),
    ]

    def build(self, g, s):
        q = []
        u = g.get("u", "")
        if u:
            q += ["past", {"used to attend": "used to", "used to attends": "used to", "used to be a member of": "used to", "previously attended": "previously",
                           "formerly attended": "formerly", "attended": "attended"}[u]]
        if g.get("p") == "no longer":
            q += ["past", "no longer"]
        elif g.get("p"):
            q += ["past", g["p"]]
        if g.get("p2"):
            q += [g["p2"]]
        if g.get("nl"):
            q += ["past", "no longer"]
        if g.get("f"):
            q += [g["f"]]
        out = []
        for x in q:
            if x not in out:
                out.append(x)
        return [fact(s, "attends", low(g["obj"]), out)]


class Volunteered(PersonRule):
    name = "volunteered_at_event"
    solves = "a person volunteered at an event id during this year or last year (object keeps the event id as written)"
    added_by = "learning"
    patterns = [r"(?:also )?volunteer(?:ed)? at (?P<ev>%s) during (?P<p>this[- ]year|last[- ]year)" % EVENT]
    examples = [
        ("Kofi Khan volunteered at event-P-151-0 during this-year", [fact("Kofi Khan", "volunteered_at", "event-P-151-0", ["this year"])]),
        ("Q. Reed volunteered at old-event-P-141 during last-year", [fact("Q. Reed", "volunteered_at", "old-event-P-141", ["last year"])]),
    ]

    def build(self, g, s):
        return [fact(s, "volunteered_at", g["ev"].replace("p-", "P-"), [g["p"].replace("-", " ")])]


class WorksFor(PersonRule):
    name = "works_for_org"
    solves = "a person works for an organization ('currently works for Org 007', 'works for Organization 018')"
    added_by = "learning"
    patterns = [r"(?:(?P<c>currently) )?works for (?P<org>%s)" % ORG]
    examples = [
        ("Nadia Novak works for organization 025", None),
        ("B. Ito currently works for Org 007", [fact("B. Ito", "works_for", "Org 007", ["currently"])]),
    ]

    def build(self, g, s):
        return [fact(s, "works_for", canon_org(g["org"]), ["currently"] if g["c"] else [])]


class Shift(PersonRule):
    name = "works_shift"
    solves = "a person works (or used to work) the day or night shift; 'in a former role' / 'used to' mark a former shift"
    added_by = "learning"
    patterns = [r"(?:(?P<c>currently) )?works the (?P<s>day|night) shift(?P<former> in a former role)?",
                r"(?P<u>used to work|worked) the (?P<s>day|night) shift(?P<former> in a former role)?"]
    examples = [
        ("Samir Laurent works the day shift", [fact("Samir Laurent", "works_shift", "day")]),
        ("L. Silva works the night shift in a former role", [fact("L. Silva", "works_shift", "night", ["former", "in a former role"])]),
        ("Kofi Khan used to work the night shift", [fact("Kofi Khan", "works_shift", "night", ["former", "used to"])]),
    ]

    def build(self, g, s):
        q = []
        if g.get("c"):
            q.append("currently")
        if g.get("u"):
            q += ["former", "used to" if g["u"] == "used to work" else "worked"]
        if g.get("former"):
            q += ["former", "in a former role"]
        out = []
        for x in q:
            if x not in out:
                out.append(x)
        return [fact(s, "works_shift", g["s"], out)]


NO_LONGER = r"(?:,? but (?:(?:he|she|they) )?no longer (?:does|do|goes))"


class TravelsBy(PersonRule):
    name = "travels_by_transit"
    solves = ("a person routinely travels by bus/train/tram/subway; 'but no longer does' / 'used to' mark a former habit "
              "(qualifiers 'routinely', 'past', 'no longer')")
    added_by = "learning"
    patterns = [r"routinely (?:travels|traveled|travelled) by (?P<m>%s)(?P<nl>%s)?" % (TRANSIT, NO_LONGER),
                r"(?P<u>used to) (?:(?P<r>routinely) )?travel by (?P<m>%s)(?: (?P<r2>routinely))?(?P<nl>%s)" % (TRANSIT, NO_LONGER),
                r"(?P<u>used to) take the (?P<m>%s) (?P<r>most weekdays)(?P<nl>%s)" % (TRANSIT, NO_LONGER)]
    examples = [
        ("N. Silva routinely travels by subway", [fact("N. Silva", "travels_by", "subway", ["routinely"])]),
        ("Ben Khan routinely travels by bus but no longer does", [fact("Ben Khan", "travels_by", "bus", ["routinely", "past", "no longer"])]),
        ("Leah Usman used to take the tram most weekdays, but no longer does",
         [fact("Leah Usman", "travels_by", "tram", ["used to", "most weekdays", "past", "no longer"])]),
    ]

    def build(self, g, s):
        q = []
        if g.get("u"):
            q.append("used to")
        r = g.get("r") or g.get("r2")
        if r:
            q.append(r)
        elif not g.get("u"):
            q.append("routinely")
        if g.get("nl"):
            q += ["past", "no longer"]
        return [fact(s, "travels_by", g["m"], q)]


class UsedOnce(PersonRule):
    name = "used_transit_once"
    solves = "a person used a bus/train/tram/subway once (a one-off, not a habit)"
    added_by = "learning"
    patterns = [r"used the (?P<m>%s) once" % TRANSIT]
    examples = [("A. Haddad used the tram once", [fact("A. Haddad", "used_transit", "tram", ["once"])])]

    def build(self, g, s):
        return [fact(s, "used_transit", g["m"], ["once"])]


class PlansTransit(PersonRule):
    name = "plans_to_use_transit"
    solves = "a person plans to use a bus/train/tram/subway in the future (a plan, not a habit)"
    added_by = "learning"
    patterns = [r"plans to use the (?P<m>%s) in the future" % TRANSIT]
    examples = [("N. Laurent plans to use the tram in the future", [fact("N. Laurent", "plans_to_use", "tram", ["future"])])]

    def build(self, g, s):
        return [fact(s, "plans_to_use", g["m"], ["future"])]


class AvoidsDairy(PersonRule):
    name = "avoids_dairy"
    solves = "a person avoids dairy ('currently chooses to avoid dairy products') or is temporarily skipping a dairy item"
    added_by = "learning"
    patterns = [r"(?:(?P<c>currently) )?(?:chooses to avoid|avoids) (?P<o>dairy products)",
                r"is (?P<c>temporarily) skipping (?P<o>%s)" % DAIRY]
    examples = [
        ("G. Chen currently chooses to avoid dairy products", [fact("G. Chen", "avoids", "dairy products", ["currently"])]),
        ("Ben Ito is temporarily skipping cheese", [fact("Ben Ito", "avoids", "cheese", ["temporarily"])]),
    ]

    def build(self, g, s):
        return [fact(s, "avoids", g["o"], [g["c"]] if g["c"] else [])]


class DairyOthers(PersonRule):
    name = "buys_for_others"
    solves = "a person buys a dairy item for other people (does not say they consume it)"
    added_by = "learning"
    patterns = [r"buys (?P<o>%s) for other people" % DAIRY]
    examples = [("Ben Ito buys milk for other people", [fact("Ben Ito", "buys_for_others", "milk")])]

    def build(self, g, s):
        return [fact(s, "buys_for_others", g["o"])]


class Dislikes(PersonRule):
    name = "dislikes_eating"
    solves = "a person dislikes eating a food (dairy item or fruit)"
    added_by = "learning"
    patterns = [r"dislikes eating (?P<o>[a-z]+)"]
    examples = [("Ben Ito dislikes eating yogurt", [fact("Ben Ito", "dislikes_eating", "yogurt")])]

    def build(self, g, s):
        return [fact(s, "dislikes_eating", g["o"])]


class EnjoysEating(PersonRule):
    name = "enjoys_eating"
    solves = "a person enjoys eating a food; 'in the past' / 'used to enjoy' / 'enjoyed ... in the past' mark a former taste"
    added_by = "learning"
    patterns = [r"(?:simply )?enjoys eating (?P<o>[a-z]+)(?P<p> in the past)?",
                r"(?P<u>used to enjoy|enjoyed) eating (?P<o>[a-z]+)(?P<p> in the past)?"]
    examples = [
        ("Ben Ito enjoys eating mango", [fact("Ben Ito", "enjoys_eating", "mango")]),
        ("Ben Ito used to enjoy eating apple", [fact("Ben Ito", "enjoys_eating", "apple", ["past", "used to"])]),
        ("Ben Ito enjoys eating banana in the past", [fact("Ben Ito", "enjoys_eating", "banana", ["past", "in the past"])]),
    ]

    def build(self, g, s):
        q = []
        if g.get("u"):
            q += ["past", "used to" if g["u"].startswith("used") else "enjoyed"]
        if g.get("p"):
            q += ["past", "in the past"]
        out = []
        for x in q:
            if x not in out:
                out.append(x)
        return [fact(s, "enjoys_eating", g["o"], out)]


class ServesNotEats(PersonRule):
    name = "serves_but_does_not_eat"
    solves = "a person serves a food to other people but does not eat it themself"
    added_by = "learning"
    patterns = [r"serves (?P<o>[a-z]+) to other people but does not eat it"]
    examples = [("Ben Ito serves mango to other people but does not eat it",
                 [fact("Ben Ito", "serves_to_others", "mango"), fact("Ben Ito", "eats", "mango", ["negated"])])]

    def build(self, g, s):
        return [fact(s, "serves_to_others", g["o"]), fact(s, "eats", g["o"], ["negated"])]


class TravelPreference(PersonRule):
    name = "travel_preference"
    solves = ("travel preference between train and plane: 'genuinely prefers X to Y when both are available', "
              "'likes X and Y equally', 'chose X over Y only because of a disruption'")
    added_by = "learning"
    M = r"(?:train|plane|bus|tram|subway|car)"
    patterns = [r"(?P<g>genuinely )?prefers (?P<a1>%s) to (?P<b1>%s) when both are available" % (M, M),
                r"likes (?P<a2>%s) and (?P<b2>%s) equally(?: for travel)?" % (M, M),
                r"chose (?:the )?(?P<a3>%s) over (?:the )?(?P<b3>%s)(?P<d> only)? because of a disruption" % (M, M)]
    examples = [
        ("A. Reed genuinely prefers train to plane when both are available",
         [fact("A. Reed", "prefers", "train over plane", ["genuinely", "when both are available"])]),
        ("A. Reed likes train and plane equally", [fact("A. Reed", "likes_equally", "train and plane")]),
        ("A. Reed chose train over plane only because of a disruption",
         [fact("A. Reed", "chose", "train over plane", ["only because of a disruption"])]),
    ]

    def build(self, g, s):
        if g.get("a1"):
            return [fact(s, "prefers", "%s over %s" % (g["a1"], g["b1"]), (["genuinely"] if g.get("g") else []) + ["when both are available"])]
        if g.get("a2"):
            return [fact(s, "likes_equally", "%s and %s" % (g["a2"], g["b2"]))]
        return [fact(s, "chose", "%s over %s" % (g["a3"], g["b3"]),
                     ["only because of a disruption" if g.get("d") else "because of a disruption"])]


class ClassRole(PersonRule):
    name = "class_role"
    solves = "a person took part in a class (language/repair/pottery) as student, teacher, observer or organizer this year"
    added_by = "learning"
    patterns = [r"took part in (?:the )?(?P<c>[a-z]+) class as the (?P<r>[a-z]+) (?P<y>this year|last year)"]
    examples = [("Ben Ito took part in repair class as the teacher this year",
                 [fact("Ben Ito", "took_part_in", "repair class", ["as teacher", "this year"])])]

    def build(self, g, s):
        return [fact(s, "took_part_in", g["c"] + " class", ["as " + g["r"], g["y"]])]


class Guardian(PersonRule):
    name = "guardian_of_youth"
    solves = "a person is the legal guardian of a youth, or an emergency contact (explicitly not a guardian)"
    added_by = "learning"
    Y = r"(?:Youth \d+|Y\d+)"
    patterns = [r"is the legal guardian of (?P<g>%s)" % Y,
                r"is (?:listed as )?an emergency contact(?:,? but not a guardian,?)? for (?P<e>%s)" % Y,
                r"is (?:listed as )?an emergency contact for (?P<e>%s)(?:,? but not a guardian)" % Y,
                r"is (?:listed as )?an emergency contact,? not a guardian,? for (?P<e>%s)" % Y]
    examples = [
        ("Omar Usman is the legal guardian of Y035", [fact("Omar Usman", "guardian_of", "Youth 035")]),
        ("Kofi Khan is an emergency contact, but not a guardian, for Y011",
         [fact("Kofi Khan", "emergency_contact_of", "Youth 011", ["not a guardian"])]),
    ]

    def build(self, g, s):
        if g.get("g"):
            return [fact(s, "guardian_of", canon_youth(g["g"]))]
        return [fact(s, "emergency_contact_of", canon_youth(g["e"]), ["not a guardian"])]


class YouthCourse(PersonRule):
    name = "youth_course"
    solves = "a youth currently attends a course during the day or the evening"
    added_by = "learning"
    patterns = [r"(?:(?P<c>currently) )?attends (?P<course>[a-z]+(?:_[a-z]+)+) during the (?P<d>day|evening)"]
    examples = [("Youth 037 currently attends evening_language during the evening",
                 [fact("Youth 037", "attends_course", "evening_language", ["currently", "evening"])])]

    def build(self, g, s):
        if not s.startswith("Youth"):
            return None
        return [fact(s, "attends_course", g["course"], (["currently"] if g["c"] else []) + [g["d"]])]


class PronounCoordination(Rule):
    name = "pronoun_coordination"
    solves = ("two statements about the same person joined by a pronoun subject ('Leah recommended X, and she also visited "
              "the museum'); the pronoun is replaced by the first clause's subject and both halves parsed by the person rules")
    added_by = "learning"
    rx = re.compile(r"(?P<left>.+?),? (?:and|but|while|whereas|so) (?:he|she|they) (?P<right>.+)")
    examples = [("Leah Usman recommended Copper Harbor, and she also visited the museum",
                 [fact("Leah Usman", "recommended", "copper harbor"), fact("Leah Usman", "visited", "museum")])]
    _parts = None

    def _rules(self):
        if PronounCoordination._parts is None:
            PronounCoordination._parts = [c() for c in globals().values()
                                          if isinstance(c, type) and issubclass(c, PersonRule) and c is not PersonRule
                                          and not getattr(c, "__abstractmethods__", None)]
        return PronounCoordination._parts

    def _one(self, clause):
        got = None
        for r in self._rules():
            f = r.parse(clause)
            if f is not None:
                if got is not None and got != f:
                    return None
                got = f
        return got

    def parse(self, clause):
        m = self.rx.fullmatch(clause.strip())
        if not m:
            return None
        sp = split_subject(m.group("left"))
        if not sp:
            return None
        left = self._one(m.group("left"))
        if not left:
            return None
        right_clause = "%s %s" % (sp[0], m.group("right"))
        right = self._one(right_clause) or self.parse(right_clause)
        if not right:
            return None
        return left + right
