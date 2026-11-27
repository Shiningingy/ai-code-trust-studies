import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re  # noqa: E402
from core import ClauseRule, WG, v  # noqa: E402
from facts_basic import F  # noqa: E402

VEH = r"(?:subway|bus|train|tram|plane|metro|ferry|car|bike|bicycle)"


class TravelsBy(ClauseRule):
    name = "travels_by"
    solves = "a person routinely travels by a vehicle; 'but no longer does' is kept as the qualifier 'no longer'"
    added_by = "learning"
    pred = (r"(?P<used>used to )?(?P<rout>routinely )?(?:travel(?:s|ed|led)?|take) (?:by |the )?(?P<veh>%s)(?P<r2> routinely)?"
            r"(?P<nl>,? but no longer (?:does|do))?" % VEH)
    examples = [("Quinn Novak routinely travels by train but no longer does.",
                 [{"subject": "Quinn Novak", "relation": "travels_by", "object": "train", "qualifiers": ["routinely", "no longer", "past"]}]),
                ("Amina Evans routinely travels by tram.",
                 [{"subject": "Amina Evans", "relation": "travels_by", "object": "tram", "qualifiers": ["routinely"]}])]

    def build(self, s, g):
        q = (["used to"] if g["used"] else []) + (["routinely"] if g["rout"] or g["r2"] else []) + (["no longer"] if g["nl"] else [])
        return [F(s, "travels_by", g["veh"], q)]


class UsedOnce(ClauseRule):
    name = "used_once"
    solves = "a person used a vehicle only once (one-off, not a habit)"
    added_by = "learning"
    pred = r"used the (?P<veh>%s) once" % VEH
    examples = [("Farah Reed used the subway once.",
                 [{"subject": "Farah Reed", "relation": "used_transport", "object": "subway", "qualifiers": ["once"]}])]

    def build(self, s, g):
        return [F(s, "used_transport", g["veh"], ["once"])]


class PlansToUse(ClauseRule):
    name = "plans_to_use"
    solves = "a person plans to use a vehicle in the future (not a current habit)"
    added_by = "learning"
    pred = r"plans? to use the (?P<veh>%s) in the future" % VEH
    examples = [("Ben Khan plans to use the bus in the future.",
                 [{"subject": "Ben Khan", "relation": "plans_to_use", "object": "bus", "qualifiers": ["in the future"]}])]

    def build(self, s, g):
        return [F(s, "plans_to_use", g["veh"], ["in the future"])]


class TravelPreference(ClauseRule):
    name = "travel_preference"
    solves = ("train-versus-plane preferences: 'likes A and B equally', 'genuinely prefers A to B when both are available', "
              "'chose A over B only because of a disruption' (the last is not a real preference)")
    added_by = "learning"
    pred = (r"(?:likes? (?P<a1>%s) and (?P<b1>%s) equally|(?P<g>genuinely )?prefers? (?P<a2>%s) to (?P<b2>%s) when both are available|"
            r"chose (?:the )?(?P<a3>%s) over (?:the )?(?P<b3>%s) (?:only )?because of a disruption)" % ((VEH,) * 6))
    examples = [("Nadia Reed likes train and plane equally.",
                 [{"subject": "Nadia Reed", "relation": "likes_equally", "object": "train and plane", "qualifiers": []}]),
                ("Nadia Reed genuinely prefers train to plane when both are available.",
                 [{"subject": "Nadia Reed", "relation": "prefers", "object": "train over plane", "qualifiers": ["genuinely", "when both are available"]}]),
                ("Nadia Reed chose train over plane only because of a disruption.",
                 [{"subject": "Nadia Reed", "relation": "chose", "object": "train over plane", "qualifiers": ["only because of a disruption"]}])]

    def build(self, s, g):
        if g["a1"]:
            return [F(s, "likes_equally", "%s and %s" % (g["a1"], g["b1"]))]
        if g["a2"]:
            return [F(s, "prefers", "%s over %s" % (g["a2"], g["b2"]), (["genuinely"] if g["g"] else []) + ["when both are available"])]
        return [F(s, "chose", "%s over %s" % (g["a3"], g["b3"]), ["only because of a disruption"])]


class Diet(ClauseRule):
    name = "diet"
    solves = ("food and drink habits: avoids dairy products (currently), temporarily skipping X, buys X for other people, "
              "dislikes eating X, enjoys eating X")
    added_by = "learning"
    pred = (r"(?:(?P<cur>currently )?(?:chooses? to avoid|avoids) (?P<av>%s)|(?:is|am) temporarily skipping (?P<sk>%s)|buys? (?P<bu>%s) for other people|"
            r"dislikes eating (?P<di>%s)|(?:simply )?(?P<ue>used to )?(?:enjoys?|enjoyed) eating (?P<en>%s))" % ((WG,) * 5))
    examples = [("Omar Foster currently chooses to avoid dairy products.",
                 [{"subject": "Omar Foster", "relation": "avoids", "object": "dairy products", "qualifiers": ["currently"]}]),
                ("Talia Patel is temporarily skipping cheese.",
                 [{"subject": "Talia Patel", "relation": "skips", "object": "cheese", "qualifiers": ["temporarily"]}]),
                ("Talia Patel buys milk for other people.",
                 [{"subject": "Talia Patel", "relation": "buys_for_others", "object": "milk", "qualifiers": []}]),
                ("Talia Patel dislikes eating yogurt.",
                 [{"subject": "Talia Patel", "relation": "dislikes_eating", "object": "yogurt", "qualifiers": []}]),
                ("Talia Patel enjoys eating mango.",
                 [{"subject": "Talia Patel", "relation": "enjoys_eating", "object": "mango", "qualifiers": []}])]

    def build(self, s, g):
        if g["av"]:
            return [F(s, "avoids", g["av"].lower(), ["currently"] if g["cur"] else [])]
        if g["sk"]:
            return [F(s, "skips", g["sk"].lower(), ["temporarily"])]
        if g["bu"]:
            return [F(s, "buys_for_others", g["bu"].lower())]
        if g["di"]:
            return [F(s, "dislikes_eating", g["di"].lower())]
        return [F(s, "enjoys_eating", g["en"].lower(), ["used to"] if g["ue"] else [])]


class ClassRole(ClauseRule):
    name = "class_role"
    solves = "a person took part in a class (language, repair, pottery, ...) in a role (teacher, student, observer, organizer) this year"
    added_by = "learning"
    pred = r"took part in (?:the )?(?P<cls>[a-z]+) class as the (?P<role>[a-z]+)(?P<when> this year| last year)?"
    examples = [("G. Jones took part in language class as the observer this year.",
                 [{"subject": "Gabriel Jones", "relation": "took_part_in", "object": "language class", "qualifiers": ["as the observer", "this year"]}])]

    def build(self, s, g):
        return [F(s, "took_part_in", g["cls"] + " class", ["as the " + g["role"]] + ([g["when"].strip()] if g["when"] else []))]


class Serves(ClauseRule):
    name = "serves_not_eats"
    solves = "a person serves a food to other people but does not eat it themselves"
    added_by = "learning"
    pred = r"serves (?P<food>%s) to other people but does not eat it" % WG
    examples = [("Farah Reed serves banana to other people but does not eat it.",
                 [{"subject": "Farah Reed", "relation": "serves_to_others", "object": "banana", "qualifiers": ["does not eat it"]}])]

    def build(self, s, g):
        return [F(s, "serves_to_others", g["food"].lower(), ["does not eat it"])]


class Guardian(ClauseRule):
    name = "guardian"
    solves = ("a person is the legal guardian of a youth, or only an emergency contact 'but not a guardian' for a youth; "
              "youth ids written Youth 024 / Y024 are one entity 'Youth 024'")
    added_by = "learning"
    pred = (r"(?:(?:is|am) the (?P<legal>legal )?guardian of (?P<y1>Youth \d+|Y\d{3})|"
            r"(?:is|am) (?:listed as )?an emergency contact,? (?:but )?(?P<ng>not a guardian),? for (?P<y2>Youth \d+|Y\d{3})|"
            r"(?:is|am) (?:listed as )?an emergency contact for (?P<y3>Youth \d+|Y\d{3})(?:,? (?:but )?(?P<ng3>not a guardian))?)")
    examples = [("Omar Bennett is the legal guardian of Youth 075.",
                 [{"subject": "Omar Bennett", "relation": "guardian_of", "object": "Youth 075", "qualifiers": ["legal"]}]),
                ("Isaac Avery is an emergency contact, but not a guardian, for Y089.",
                 [{"subject": "Isaac Avery", "relation": "emergency_contact_of", "object": "Youth 089", "qualifiers": ["not a guardian"]}]),
                ("Leah Diaz is an emergency contact for Y132.",
                 [{"subject": "Leah Diaz", "relation": "emergency_contact_of", "object": "Youth 132", "qualifiers": []}])]

    def build(self, s, g):
        y = "Youth " + re.search(r"\d+", g["y1"] or g["y2"] or g["y3"]).group()
        if g["y2"] or g["y3"]:    # an emergency contact is not a guardian, whether or not the text says so
            return [F(s, "emergency_contact_of", y, ["not a guardian"] if g["ng"] or g["ng3"] else [])]
        return [F(s, "guardian_of", y, ["legal"] if g["legal"] else [])]


class YouthCourse(ClauseRule):
    name = "youth_course"
    solves = "a youth currently attends a course (evening_pottery, daytime_first_aid, ...) during the evening or the day"
    added_by = "learning"
    subject = "youth"
    pred = r"(?P<cur>currently )?attends? (?P<course>[\w]+) during the (?P<tod>evening|day|morning|afternoon)"
    examples = [("Y114 currently attends evening_pottery during the evening.",
                 [{"subject": "Youth 114", "relation": "attends_course", "object": "evening_pottery",
                   "qualifiers": ["currently", "during the evening"]}])]

    def build(self, s, g):
        return [F(s, "attends_course", g["course"], (["currently"] if g["cur"] else []) + ["during the " + g["tod"]])]
