"""Community activities: recommending and discussing things, owning items, helping at and visiting places, attending
groups, volunteering at events."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import F, SUBJ, lead, slot  # noqa: E402

Q = ""
ALSO = r"(?:(?P<also>also|both) )?"
T = r"(?P<tail>.*)"


class Recommended(C.Core):
    name = "recommended"
    solves = ("'X recommended <title>' (also 'suggested', 'recommends'), with any tail such as 'to the group' or a "
              "remark; the recommendation clause is one of the most common in the passages")
    added_by = "learning"
    pattern = Q + SUBJ + " " + ALSO + r"(?:recommended|recommends|recommend|suggested|suggests) " + slot("o", C.TITLES) + T
    examples = [
        ("Priya Jones recommended Quiet Machines.",
         [F("Priya Jones", "recommended", "quiet machines")]),
        ("e. laurent recommended the long orchard to the group.",
         [F("E. Laurent", "recommended", "long orchard", "note:to the group")]),
    ]

    def make(self, s, g, q):
        return [F(s, "recommended", C.obj(g["o"]), q)]


class Discussed(C.Core):
    name = "discussed"
    solves = ("'X discussed <topic>' (also 'talked about', 'mentioned'); the topic is a title, place or group, "
              "optionally with an aspect word ('market trends' -> topic market, qualifier aspect:trends)")
    added_by = "learning"
    pattern = (Q + SUBJ + " " + ALSO + r"(?:discussed|discusses|discuss|talked about|talks about|mentioned) "
               + slot("o", C.TITLES + C.PLACES + C.GROUPS) + r"(?: (?P<aspect>%s))?" % C.ASPECT + T)
    examples = [
        ("Omar Diaz discussed sports hall.", [F("Omar Diaz", "discussed", "sports hall")]),
        ("H. Laurent discussed market trends during the last meeting.",
         [F("H. Laurent", "discussed", "market", "aspect:trends", "note:during the last meeting")]),
        ("N. Reed discussed radio society membership updates.",
         [F("N. Reed", "discussed", "radio society", "aspect:membership updates")]),
        ("C. Silva discussed Atlas of Clouds, a book that has been generating a lot of interest.",
         [F("C. Silva", "discussed", "atlas of clouds", "note:a book that has been generating a lot of interest")]),
    ]

    def make(self, s, g, q):
        t, aspect = C.topic(g["o"])
        aspect = g["aspect"].lower() or aspect
        return [F(s, "discussed", t, ["aspect:" + aspect] if aspect else [], q)]


class Owns(C.Core):
    name = "owns"
    solves = ("'X owns a <item>' (also 'own', 'has', 'keeps'; 'a garden tools', 'garden tools set' are the same item "
              "'garden tools'), with an optional remark about the item")
    added_by = "learning"
    pattern = Q + SUBJ + " " + ALSO + r"(?:owns|own|has|have|keeps|keep) " + slot("o", C.ITEMS) + T
    examples = [
        ("B. Ito owns a garden tools.", [F("B. Ito", "owns", "garden tools")]),
        ("Mateo Foster owns a telescope, which he often brings to our outdoor events.",
         [F("Mateo Foster", "owns", "telescope", "note:which he often brings to our outdoor events")]),
        ("I own a camera.", [F("I", "owns", "camera")]),
    ]

    def make(self, s, g, q):
        return [F(s, "owns", C.obj(g["o"]), q)]


class HelpedWith(C.Core):
    name = "helped_with"
    solves = ("'X helped with <task> at <place>' (task registration/setup/cleanup; also 'assisted with', 'help with'); "
              "the place may be missing")
    added_by = "learning"
    pattern = (Q + SUBJ + " " + ALSO + r"(?:helped|helps|help|assisted|assists) with " + slot("task", C.TASKS, False)
               + r"(?: at " + slot("o", C.PLACES) + ")?" + T)
    examples = [
        ("Nadia Patel helped with setup at the market, ensuring everything was ready for the opening.",
         [F("Nadia Patel", "helped_with", "setup", "at:market", "note:ensuring everything was ready for the opening")]),
        ("F. Patel helped with registration at the sports hall.",
         [F("F. Patel", "helped_with", "registration", "at:sports hall")]),
    ]

    def make(self, s, g, q):
        return [F(s, "helped_with", C.obj(g["task"]), ["at:" + C.obj(g["o"])] if g["o"] else [], q)]


class Visited(C.Core):
    name = "visited"
    solves = ("'X visited <place>' (also 'went to', 'previously visited'), with time modifiers ('some time ago', "
              "'in the past', 'previously' -> past; 'on Saturday' -> time) and remarks")
    added_by = "learning"
    pattern = (Q + SUBJ + " " + ALSO + r"(?:(?P<prev>previously|formerly) )?(?:visited|visits|visit|went to|goes to|"
               r"(?P<had>had visited)) " + slot("o", C.PLACES) + T)
    examples = [
        ("E. Patel visited the market some time ago.", [F("E. Patel", "visited", "market", "past")]),
        ("Omar Diaz visited the sports hall, and it was a notable visit.",
         [F("Omar Diaz", "visited", "sports hall", "note:and it was a notable visit")]),
        ("S. Gupta went to the museum previously.", [F("S. Gupta", "visited", "museum", "past")]),
    ]

    def make(self, s, g, q):
        return [F(s, "visited", C.obj(g["o"]), lead(g, "prev", "past"), lead(g, "had", "past"), q)]


class AttendsGroup(C.Core):
    name = "attends_group"
    solves = ("'X attends the <group>' and its past forms: 'only in the past', 'used to attend', 'previously "
              "attended', 'attended ... in the past', 'no longer attends', 'used to be a member of', '..., but no longer "
              "does'; every past form gets the qualifier past, the plain present form none")
    added_by = "learning"
    pattern = (Q + SUBJ + " " + ALSO + r"(?:(?P<cur>currently) )?(?:(?P<past>used to attends?|used to be a member of|"
               r"only used to attend|previously attended|formerly attended|attended|no longer attends?|no longer "
               r"participates? in)|attends|attend) " + slot("o", C.GROUPS) + T)
    examples = [
        ("Samir Ito attends the history group.", [F("Samir Ito", "attends", "history group")]),
        ("T. Patel attends the walking group only in the past.", [F("T. Patel", "attends", "walking group", "past")]),
        ("K. Mensah used to attend the walking group, but no longer does.",
         [F("K. Mensah", "attends", "walking group", "past")]),
        ("Isaac Bennett attends the walking group every morning.",
         [F("Isaac Bennett", "attends", "walking group", "frequency:every morning")]),
    ]

    def make(self, s, g, q):
        if "_" in g["o"]:
            return None     # a course ('evening_pottery'), see youth_attends_course
        return [F(s, "attends", C.obj(g["o"]), lead(g, "cur", "current"), lead(g, "past", "past"), q)]


class Volunteered(C.Core):
    name = "volunteered"
    solves = ("'X volunteered at <event id> during this-year/last-year' ('event-P-027-1', 'old-event-P-061'); the "
              "period is kept as qualifier period:this-year or period:last-year")
    added_by = "learning"
    pattern = (Q + SUBJ + " " + ALSO + r"(?:volunteered|volunteers|volunteer) at (?P<ev>(?:old-)?event-[A-Za-z0-9-]+?)"
               r" during (?P<per>this[- ]year|last[- ]year)" + T)
    examples = [
        ("Omar Bennett volunteered at old-event-P-075 during last-year.",
         [F("Omar Bennett", "volunteered_at", "old-event-P-075", "period:last-year")]),
        ("S. Mensah volunteered at event-p-139-0 during this year.",
         [F("S. Mensah", "volunteered_at", "event-P-139-0", "period:this-year")]),
    ]

    def make(self, s, g, q):
        ev = g["ev"].lower().replace("-p-", "-P-")
        return [F(s, "volunteered_at", ev, "period:" + g["per"].lower().replace(" ", "-"), q)]
