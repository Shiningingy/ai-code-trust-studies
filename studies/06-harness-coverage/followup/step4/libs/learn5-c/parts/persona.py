"""Rules for personal attributes: organization, shift, transport, diet, classes, volunteering, guardianship, roster."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re
from gram import PatternRule
from common import *

ORG = r"(?:Org|Organization)\s+\d+"
YEARQ = {"this": "this year", "last": "last year"}


class Roster(PatternRule):
    name = "roster"
    solves = "roster lines tying a person to an identifier (P-nnn) and to other written forms (familiar names) of the same person"
    added_by = "learning"
    flags = re.I
    pattern = (r"the community roster (?:records|lists) (?P<n>%s) under identifier (?P<id>P-\d+)(?: and also uses the familiar names? "
               r"(?P<al>(?-i:%s)(?:(?:,| and|, and) (?-i:%s))*))?%s" % (PERSON, CAPPERSON, CAPPERSON, TAILX))
    examples = [("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed",
                 [fact("Nadia Reed", "has_id", "P-114"), fact("Nadia Reed", "also_known_as", "N. Reed")])]

    def build(self, g):
        n = person(g["n"])
        out = [fact(n, "has_id", g["id"].upper())]
        for a in re.split(r",\s*(?:and\s+)?|\s+and\s+", g["al"]):
            if a.strip():
                out.append(fact(n, "also_known_as", person(a)))
        return out


class Volunteered(PatternRule):
    name = "volunteered"
    solves = "'X volunteered at event-P-nnn-k during this-year' (or old-event-... during last-year); one fact per event"
    added_by = "learning"
    flags = re.I
    pattern = (r"(?:During (?P<y0>this|last)[- ]year, )?(?P<s>%s) (?:(?:also|simply|just|still|even|only) )?(?:also )?(?:volunteered|volunteers?) at (?P<e>(?:old-)?event-P-\d+(?:-\d+)?)"
               r"(?: during (?P<y>this|last)[- ]year)?%s" % (SUBJ, TAILX))
    examples = [("Ana Gupta volunteered at event-P-070-0 during this-year",
                 [fact("Ana Gupta", "volunteered_at", "event-P-070-0", ["this year"])])]

    def build(self, g):
        return [fact(subj(g["s"]), "volunteered_at", g["e"].lower().replace("p-", "P-"), [YEARQ[(g["y"] or g["y0"]).lower()]] if (g["y"] or g["y0"]) else [])]


class WorksFor(PatternRule):
    name = "works_for"
    solves = "'X currently works for Org nnn' (also 'Organization nnn'); object canonical 'Org nnn'; former employment marked past"
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:(?:also|simply|just|still|even|only) )?(?P<v>currently works for|works for|used to work for|worked for|previously worked for|"
               r"formerly worked for) (?P<o>%s)%s" % (SUBJ, ORG, TAILX))
    examples = [("Kofi Khan currently works for Organization 030", [fact("Kofi Khan", "works_for", "Org 030", ["current"])]),
                ("Kofi Khan works for Org 030", [fact("Kofi Khan", "works_for", "Org 030")])]

    def build(self, g):
        v = g["v"].lower()
        q = ["current"] if v.startswith("currently") else (["past"] if re.search(r"used|worked", v) else [])
        return [fact(subj(g["s"]), "works_for", org(g["o"]), q + advq(g["tail"]))]


class OrgBased(PatternRule):
    name = "org_based"
    solves = "'Org nnn is based in <city>' (city may be 'St. John's')"
    added_by = "learning"
    flags = re.I
    pattern = r"(?P<o>%s) is based in (?P<c>[A-Za-z.' ]+?)%s" % (ORG, TAIL)
    examples = [("Org 003 is based in St. John's", [fact("Org 003", "based_in", "St. John's")])]

    def build(self, g):
        return [fact(org(g["o"]), "based_in", " ".join(w.capitalize() if w.lower() != "st." else "St." for w in g["c"].split()))]


class Shift(PatternRule):
    name = "shift"
    solves = "'X works the day/night shift' (current), 'in a former role' / 'used to work' (past)"
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:(?:also|simply|just|still|even|only) )?(?P<v>currently works|works|used to work|worked|previously worked|formerly worked) the "
               r"(?P<o>day|night|evening|morning) shift(?P<q> in a former role)?%s" % (SUBJ, TAILX))
    examples = [("A. Lee works the night shift in a former role", [fact("A. Lee", "works_shift", "night", ["past"])]),
                ("A. Lee works the day shift", [fact("A. Lee", "works_shift", "day")])]

    def build(self, g):
        past = bool(g["q"]) or bool(re.search("used|worked|previously|formerly", g["v"], re.I))
        q = ["past"] if past else (["current"] if g["v"].lower().startswith("currently") else [])
        return [fact(subj(g["s"]), "works_shift", g["o"].lower(), q + tailq(g["tail"]) * (not past))]


class AvoidDairy(PatternRule):
    name = "avoid_dairy"
    solves = "'X currently chooses to avoid dairy products' (a diet choice, not an allergy)"
    added_by = "learning"
    flags = re.I
    pattern = r"(?P<s>%s) (?:(?:also|simply|just|still|even|only) )?(?P<c>currently )?(?:chooses to avoid|avoids) dairy products%s" % (SUBJ, TAILX)
    examples = [("N. Ortiz currently chooses to avoid dairy products", [fact("N. Ortiz", "avoids", "dairy products", ["current"])])]

    def build(self, g):
        return [fact(subj(g["s"]), "avoids", "dairy products", ["current"] if g["c"] else [])]


class FoodAttitude(PatternRule):
    name = "food_attitude"
    solves = ("food sentences: 'enjoys eating X' (+'in the past', 'used to enjoy'), 'dislikes eating X', 'is temporarily skipping X', "
              "'buys X for other people', 'serves X to other people but does not eat it'")
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:(?:also|simply|just|still|even|only) )?(?:(?P<enj>enjoys eating|enjoyed eating|used to enjoy eating)|(?P<dis>dislikes eating)|(?P<skip>is temporarily skipping)|"
               r"(?P<buy>buys)|(?P<serve>serves)) (?P<o>[a-z]+)(?P<q> in the past| for other people| to other people but does not eat it)?%s"
               % (SUBJ, TAILX))
    examples = [("Q. Silva dislikes eating milk", [fact("Q. Silva", "dislikes_eating", "milk")]),
                ("J. Roe is temporarily skipping cheese", [fact("J. Roe", "skips", "cheese", ["temporary"])]),
                ("J. Roe buys butter for other people", [fact("J. Roe", "buys_for_others", "butter")]),
                ("J. Roe serves pear to other people but does not eat it",
                 [fact("J. Roe", "serves_to_others", "pear", ["does not eat"])]),
                ("J. Roe enjoys eating banana in the past", [fact("J. Roe", "enjoys_eating", "banana", ["past"])])]

    def build(self, g):
        s, o = subj(g["s"]), g["o"].lower()
        if g["enj"]:
            past = g["enj"].lower().startswith(("used", "enjoyed")) or "past" in g["q"].lower() or bool(tailq(g["tail"]))
            return [fact(s, "enjoys_eating", o, ["past"] if past else [])]
        if g["dis"]:
            return [fact(s, "dislikes_eating", o)]
        if g["skip"]:
            return [fact(s, "skips", o, ["temporary"])]
        if g["buy"]:
            return [fact(s, "buys_for_others", o)]
        return [fact(s, "serves_to_others", o, ["does not eat"])]


class Transport(PatternRule):
    name = "transport"
    solves = ("travel habits: 'routinely travels by M' (ordinary), '... but no longer does' / 'used to routinely travel' (past), "
              "'used the M once' (once), 'plans to use the M in the future' (future)")
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:(?:also|simply|just|still|even|only) )?(?:(?P<hab>(?:(?:used to )?routinely (?:travels|travel|traveled|travelled) by|(?:used to )?take|takes|took) (?:the )?(?P<m1>%s))(?: most weekdays| every day)?(?P<neg>,? but (?:he |she |they |I )?no longer does?)?"
               r"|(?P<hab2>used to travel by (?P<m4>%s) routinely)(?P<neg2> but no longer does)?"
               r"|(?P<once>used the (?P<m2>%s) once)|(?P<fut>plans to use the (?P<m3>%s) in the future))%s"
               % (SUBJ, MODES, MODES, MODES, MODES, TAILX))
    examples = [("A. Lee routinely travels by subway", [fact("A. Lee", "travels_by", "subway", ["routinely"])]),
                ("A. Lee routinely travels by bus but no longer does", [fact("A. Lee", "travels_by", "bus", ["routinely", "past"])]),
                ("A. Lee used the tram once", [fact("A. Lee", "travels_by", "tram", ["once"])]),
                ("A. Lee plans to use the train in the future", [fact("A. Lee", "travels_by", "train", ["future"])])]

    def build(self, g):
        s = subj(g["s"])
        if g["hab"] or g["hab2"]:
            m = (g["m1"] or g["m4"]).lower()
            q = ["routinely"]
            if g["neg"] or g["neg2"] or (g["hab"] or "").lower().startswith("used"):
                q.append("past")
            return [fact(s, "travels_by", m, q + tailq(g["tail"]) * (len(q) == 1))]
        if g["once"]:
            return [fact(s, "travels_by", g["m2"].lower(), ["once"])]
        return [fact(s, "travels_by", g["m3"].lower(), ["future"])]


class Preference(PatternRule):
    name = "transport_preference"
    solves = "'likes A and B equally', 'genuinely prefers A to B when both are available', 'chose A over B (only) because of a disruption'"
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:(?:also|simply|just|still|even|only) )?(?:(?P<eq>likes (?P<a1>%s) and (?P<b1>%s) equally)|(?P<pref>(?P<gen>genuinely )?prefers (?P<a2>%s) to (?P<b2>%s) when both are available)"
               r"|(?P<chose>chose (?:the )?(?P<a3>%s) over (?:the )?(?P<b3>%s) (?:only )?because of a disruption))%s"
               % (SUBJ, MODES, MODES, MODES, MODES, MODES, MODES, TAILX))
    examples = [("A. Lee genuinely prefers train to plane when both are available",
                 [fact("A. Lee", "prefers", "train", ["over plane", "genuine"])]),
                ("A. Lee likes train and plane equally", [fact("A. Lee", "likes_equally", "train", ["and plane"])]),
                ("A. Lee chose train over plane only because of a disruption",
                 [fact("A. Lee", "chose", "train", ["over plane", "because of a disruption"])])]

    def build(self, g):
        s = subj(g["s"])
        if g["eq"]:
            return [fact(s, "likes_equally", g["a1"].lower(), ["and " + g["b1"].lower()])]
        if g["pref"]:
            return [fact(s, "prefers", g["a2"].lower(), ["over " + g["b2"].lower()] + (["genuine"] if g["gen"] else []))]
        return [fact(s, "chose", g["a3"].lower(), ["over " + g["b3"].lower(), "because of a disruption"])]


class ClassRole(PatternRule):
    name = "class_role"
    solves = "'X took part in <subject> class as the <role> this year' (role: teacher, student, organizer, observer)"
    added_by = "learning"
    flags = re.I
    pattern = r"(?P<s>%s) (?:(?:also|simply|just|still|even|only) )?took part in (?:the )?(?P<c>[a-z]+) class as the (?P<r>[a-z]+) this year%s" % (SUBJ, TAILX)
    examples = [("A. Lee took part in repair class as the teacher this year",
                 [fact("A. Lee", "class_role_teacher", "repair class", ["this year"])])]

    def build(self, g):
        return [fact(subj(g["s"]), "class_role_" + g["r"].lower(), g["c"].lower() + " class", ["this year"])]


class Guardian(PatternRule):
    name = "guardian"
    solves = "'X is the legal guardian of Youth n' (guardian) or 'is an emergency contact, but not a guardian, for Youth n' (not guardian)"
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:(?:also|simply|just|still|even|only) )?(?:is (?P<g>the legal guardian of)|is (?P<e>(?:listed as )?an emergency contact(?:,? (?:but )?not a guardian,?)? for)) (?P<y>%s)(?P<ng>,? but not a guardian)?%s"
               % (SUBJ, YOUTH, TAILX))
    examples = [("H. Khan is the legal guardian of Y028", [fact("H. Khan", "guardian_of", "Youth 28")]),
                ("R. Bennett is an emergency contact, but not a guardian, for Youth 058",
                 [fact("R. Bennett", "emergency_contact_of", "Youth 58", ["not guardian"])])]

    def build(self, g):
        y = youth(g["y"])
        if g["g"]:
            return [fact(subj(g["s"]), "guardian_of", y)]
        return [fact(subj(g["s"]), "emergency_contact_of", y, ["not guardian"] if "not" in g["e"] or g["ng"] else [])]


class YouthCourse(PatternRule):
    name = "youth_course"
    solves = "'Youth n currently attends <course> during the evening/day' (course names like evening_pottery, daytime_first_aid)"
    added_by = "learning"
    flags = re.I
    pattern = r"(?P<y>%s) (?P<cur>currently )?attends (?P<c>[a-z_]+) during the (?P<t>evening|day)%s" % (YOUTH, TAILX)
    examples = [("Y114 currently attends evening_pottery during the evening",
                 [fact("Youth 114", "attends_course", "evening_pottery", ["current", "during the evening"])])]

    def build(self, g):
        return [fact(youth(g["y"]), "attends_course", g["c"].lower(), (["current"] if g["cur"] else []) + ["during the " + g["t"].lower()])]
