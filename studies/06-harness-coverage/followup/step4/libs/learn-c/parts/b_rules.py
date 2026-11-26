"""Fact rules for the 'SUBJECT PREDICATE' clause families (see NOTES.md for relation names)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from gcommon import Pred, canon_name, obj, fact, ORG

_NOT = r"(?!(?:and|but|with|from|that|which|who|while|because|so|though|although|during|after|before|when|where|as|to|for|by|at|in|on|often|nearby|also|too|now|not)\b)"
OBJW = _NOT + r"[A-Za-z']+"
OBJ = OBJW + r"(?: (?:of )?" + OBJW + r"){0,3}?"          # 1-4 plain words ('atlas of clouds' allowed), no connectors
TIME = r"(?P<t>\s+some time ago|\s+in the past|\s+previously|\s+last weekend)?"
PLACE = r"(?:the )?(?P<o>" + OBJ + r")"
FOOD = r"(?P<o>" + OBJ + r")"
VEH = r"(?:train|bus|tram|subway)"


def tq(g, quals):
    if (g.get("t") or "").strip() and "past" not in quals:
        quals.append("past")
    return quals


class Visited(Pred):
    name = "visited"
    solves = "'X visited the P' (optionally 'some time ago' / 'in the past' / 'previously' = past), also 'went to'; the place visited"
    added_by = "learning"
    body = r"(?P<pre>previously )?(?:had )?(?:visited|went to) " + PLACE + TIME
    examples = [("Omar Diaz visited the museum some time ago.",
                 [{"subject": "Omar Diaz", "relation": "visited", "object": "museum", "qualifiers": ["past"]}]),
                ('Farah Avery said, "I visited the market."',
                 [{"subject": "Farah Avery", "relation": "visited", "object": "market", "qualifiers": ["said"]}])]

    def facts(self, s, g, q):
        if g.get("pre"):
            q.append("past")
        return [fact(s, "visited", obj(g["o"]), tq(g, q))]


class HelpedWith(Pred):
    name = "helped_with"
    solves = "'X helped with setup|cleanup|registration at the P'; relation helped_with_<task>, object = place"
    added_by = "learning"
    body = r"(?:helped|help|assisted) with (?P<task>setup|cleanup|registration)(?: at " + PLACE + r")?" + TIME
    examples = [("K. Khan helped with setup at the library.",
                 [{"subject": "K. Khan", "relation": "helped_with_setup", "object": "library", "qualifiers": []}])]

    def facts(self, s, g, q):
        return [fact(s, "helped_with_" + g["task"].lower(), obj(g.get("o", "")), tq(g, q))]


class Owns(Pred):
    name = "owns"
    solves = "'X owns a camera|telescope|guitar|sewing kit|garden tools'; the item owned"
    added_by = "learning"
    body = r"(?:owns|own|has|have) (?:an? )?(?P<o>" + OBJ + r")" + TIME
    examples = [("B. Ito owns a garden tools.",
                 [{"subject": "B. Ito", "relation": "owns", "object": "garden tools", "qualifiers": []}])]

    def facts(self, s, g, q):
        return [fact(s, "owns", obj(g["o"]), tq(g, q))]


class Recommended(Pred):
    name = "recommended"
    solves = "'X recommended <title>'; the title recommended (lowercased, e.g. 'quiet machines')"
    added_by = "learning"
    body = r"(?:also )?(?:recommended|recommend|suggested) (?P<o>" + OBJ + r")" + TIME
    examples = [("Hana Ortiz recommended Quiet Machines.",
                 [{"subject": "Hana Ortiz", "relation": "recommended", "object": "quiet machines", "qualifiers": []}])]

    def facts(self, s, g, q):
        return [fact(s, "recommended", obj(g["o"]), tq(g, q))]


class Discussed(Pred):
    name = "discussed"
    solves = "'X discussed <topic>' / 'mentioned <topic>' / 'talked about <topic>': a book title, place or group discussed"
    added_by = "learning"
    body = r"(?:also )?(?:discussed|discuss|mentioned|talked about) (?:the )?(?P<o>" + OBJ + r")" + TIME
    examples = [("Priya Haddad discussed chess club.",
                 [{"subject": "Priya Haddad", "relation": "discussed", "object": "chess club", "qualifiers": []}])]

    def facts(self, s, g, q):
        return [fact(s, "discussed", obj(g["o"]), tq(g, q))]


class Attends(Pred):
    name = "attends"
    solves = ("group membership: 'attends the G'; past forms 'only in the past', 'used to attend', 'previously attended', "
              "'no longer attends', 'but no longer does' all give qualifier past (plus no_longer when said)")
    added_by = "learning"
    body = (r"(?P<pre>used to attend|used to be a member of|previously attended|formerly attended|attended|no longer attends?|attends?) (?:the )?(?P<o>" + OBJ + r")"
            r"(?P<post>,? only in the past|,? in the past|,? but (?:I |he |she |they )?no longer (?:does|do|goes|go)|,? though (?:he|she|they) no longer does|,? but that is in the past now"
            r"|,? but (?:that|this) (?:is|was) in the past|,? but only in the past)?")
    examples = [("T. Patel attends the walking group only in the past.",
                 [{"subject": "T. Patel", "relation": "attends", "object": "walking group", "qualifiers": ["past"]}]),
                ("Carla Tran used to attend the history group.",
                 [{"subject": "Carla Tran", "relation": "attends", "object": "history group", "qualifiers": ["past"]}]),
                ("Leah Avery attends the chess club.",
                 [{"subject": "Leah Avery", "relation": "attends", "object": "chess club", "qualifiers": []}])]

    def facts(self, s, g, q):
        pre, post = g["pre"].lower(), (g.get("post") or "").lower()
        if pre.startswith(("used", "previously", "attended", "no longer")) or post:
            q.append("past")
        if "no longer" in pre or "no longer" in post:
            q.append("no_longer")
        return [fact(s, "attends", obj(g["o"]), q)]


class Volunteered(Pred):
    name = "volunteered"
    solves = "'X volunteered at <event-id> during this-year|last-year'; object = event id, qualifier = the year word"
    added_by = "learning"
    body = r"(?:also )?(?:volunteered|volunteer) at (?P<e>[\w-]+) during (?P<y>this[- ]year|last[- ]year)"
    examples = [("Q. Usman volunteered at event-D-02567-0 during this-year.",
                 [{"subject": "Q. Usman", "relation": "volunteered_at", "object": "event-D-02567-0", "qualifiers": ["this-year"]}])]

    def facts(self, s, g, q):
        return [fact(s, "volunteered_at", g["e"], q + [g["y"].lower().replace(" ", "-")])]


class WorksFor(Pred):
    name = "works_for"
    solves = "'X (currently) works for Org NNN'; object = canonical 'Org NNN'; qualifier current when 'currently' is said"
    added_by = "learning"
    body = r"(?P<cur>currently )?(?:works|work) for (?P<org>%s)" % ORG
    examples = [("Dev Foster currently works for Org 027.",
                 [{"subject": "Dev Foster", "relation": "works_for", "object": "Org 027", "qualifiers": ["current"]}])]

    def facts(self, s, g, q):
        if g.get("cur"):
            q.append("current")
        return [fact(s, "works_for", canon_name(g["org"]), q)]


class OrgBased(Pred):
    name = "org_based_in"
    solves = "'Org NNN is based in <City>': the city of an organization"
    added_by = "learning"
    body = r"is based in (?P<c>[A-Za-z.' ]+?)"
    examples = [("Org 027 is based in St. John's.",
                 [{"subject": "Org 027", "relation": "based_in", "object": "st. john's", "qualifiers": []}])]

    def facts(self, s, g, q):
        if not s.startswith("Org "):
            return None
        return [fact(s, "based_in", obj(g["c"]), q)]


class Shift(Pred):
    name = "shift"
    solves = "'X works the day|night shift' (also 'used to work', 'worked', 'in a former role' = past)"
    added_by = "learning"
    body = r"(?P<v>used to work|worked|works|work) the (?P<sh>day|night) shift(?P<f> in a former role)?"
    examples = [("Mateo Foster works the night shift in a former role.",
                 [{"subject": "Mateo Foster", "relation": "works_shift", "object": "night", "qualifiers": ["past"]}])]

    def facts(self, s, g, q):
        if g["v"].lower() in ("used to work", "worked") or g.get("f"):
            q.append("past")
        return [fact(s, "works_shift", g["sh"].lower(), q)]


class Avoids(Pred):
    name = "avoids_dairy"
    solves = "'X (currently) chooses to avoid dairy products': deliberate avoidance of dairy"
    added_by = "learning"
    body = r"(?P<cur>currently )?(?:chooses|choose|avoids|avoid) (?:to avoid )?dairy products"
    examples = [("Nadia Reed currently chooses to avoid dairy products.",
                 [{"subject": "Nadia Reed", "relation": "avoids", "object": "dairy products", "qualifiers": ["current"]}])]

    def facts(self, s, g, q):
        if g.get("cur"):
            q.append("current")
        return [fact(s, "avoids", "dairy products", q)]


class Skipping(Pred):
    name = "temporarily_skipping"
    solves = "'X is temporarily skipping <food>': a temporary skip (qualifier temporary), not a lasting avoidance"
    added_by = "learning"
    body = r"(?:is|am) temporarily skipping " + FOOD
    examples = [("Ben Khan is temporarily skipping cheese.",
                 [{"subject": "Ben Khan", "relation": "skips", "object": "cheese", "qualifiers": ["temporary"]}])]

    def facts(self, s, g, q):
        return [fact(s, "skips", obj(g["o"]), q + ["temporary"])]


class BuysForOthers(Pred):
    name = "buys_for_others"
    solves = "'X buys <food> for other people': buys it for others (says nothing about eating it)"
    added_by = "learning"
    body = r"(?:buys|buy) " + FOOD + r" for other people"
    examples = [("Rosa Diaz buys milk for other people.",
                 [{"subject": "Rosa Diaz", "relation": "buys_for_others", "object": "milk", "qualifiers": []}])]

    def facts(self, s, g, q):
        return [fact(s, "buys_for_others", obj(g["o"]), q)]


class ServesNotEats(Pred):
    name = "serves_not_eat"
    solves = "'X serves <food> to other people but does not eat it': serves_to_others plus eats with qualifier not"
    added_by = "learning"
    body = r"(?:serves|serve) " + FOOD + r" to other people but (?:does|do) not eat it"
    examples = [("Amina Evans serves pear to other people but does not eat it.",
                 [{"subject": "Amina Evans", "relation": "serves_to_others", "object": "pear", "qualifiers": []},
                  {"subject": "Amina Evans", "relation": "eats", "object": "pear", "qualifiers": ["not"]}])]

    def facts(self, s, g, q):
        o = obj(g["o"])
        return [fact(s, "serves_to_others", o, q), fact(s, "eats", o, q + ["not"])]


class EnjoysEating(Pred):
    name = "enjoys_eating"
    solves = "'X enjoys eating <food>' (also 'used to enjoy', 'in the past' = past); relation enjoys_eating"
    added_by = "learning"
    body = r"(?P<v>used to enjoy|enjoyed|enjoys|enjoy) eating " + FOOD + r"(?P<t>\s+in the past)?"
    examples = [("Dev Gupta enjoys eating banana in the past.",
                 [{"subject": "Dev Gupta", "relation": "enjoys_eating", "object": "banana", "qualifiers": ["past"]}])]

    def facts(self, s, g, q):
        if g["v"].lower().startswith("used") or g["v"].lower() == "enjoyed":
            q.append("past")
        return [fact(s, "enjoys_eating", obj(g["o"]), tq(g, q))]


class DislikesEating(Pred):
    name = "dislikes_eating"
    solves = "'X dislikes eating <food>'"
    added_by = "learning"
    body = r"(?:dislikes|dislike) eating " + FOOD + TIME
    examples = [("Q. Silva dislikes eating milk.",
                 [{"subject": "Q. Silva", "relation": "dislikes_eating", "object": "milk", "qualifiers": []}])]

    def facts(self, s, g, q):
        return [fact(s, "dislikes_eating", obj(g["o"]), tq(g, q))]


class TravelsBy(Pred):
    name = "travels_by"
    solves = "routine transport: 'routinely travels by V', 'used to routinely travel by V but no longer does' (past, no_longer)"
    added_by = "learning"
    body = (r"(?:(?P<used>used to) )?(?:routinely (?:travels|travel|traveled|travelled) by (?P<v>%s)(?: routinely)?(?: to work)?"
            r"|travel by (?P<v2>%s) routinely)(?P<nl>,? but no longer (?:does|do))?" % (VEH, VEH))
    examples = [("Priya Jones routinely travels by bus.",
                 [{"subject": "Priya Jones", "relation": "travels_by", "object": "bus", "qualifiers": ["routinely"]}]),
                ("A. Bennett used to routinely travel by train but no longer does.",
                 [{"subject": "A. Bennett", "relation": "travels_by", "object": "train", "qualifiers": ["routinely", "past", "no_longer"]}])]

    def facts(self, s, g, q):
        v = g.get("v") or g.get("v2")
        q.append("routinely")
        if g.get("used") or g.get("nl"):
            q += ["past", "no_longer"]
        return [fact(s, "travels_by", v.lower(), q)]


class UsedOnce(Pred):
    name = "used_once"
    solves = "'X used the train|bus|tram|subway once': a single past use, not a routine"
    added_by = "learning"
    body = r"used the (?P<v>%s) once" % VEH
    examples = [("Hana Ortiz used the subway once.",
                 [{"subject": "Hana Ortiz", "relation": "used_transport", "object": "subway", "qualifiers": ["once", "past"]}])]

    def facts(self, s, g, q):
        return [fact(s, "used_transport", g["v"].lower(), q + ["once", "past"])]


class PlansToUse(Pred):
    name = "plans_to_use"
    solves = "'X plans to use the V in the future': a future plan, not current travel"
    added_by = "learning"
    body = r"(?:plans|plan) to use the (?P<v>%s) in the future" % VEH
    examples = [("Ben Khan plans to use the bus in the future.",
                 [{"subject": "Ben Khan", "relation": "plans_to_use", "object": "bus", "qualifiers": ["future"]}])]

    def facts(self, s, g, q):
        return [fact(s, "plans_to_use", g["v"].lower(), q + ["future"])]


class LikesEqually(Pred):
    name = "likes_equally"
    solves = "'X likes train and plane equally': no preference between train and plane"
    added_by = "learning"
    body = r"(?:likes|like) train and plane equally"
    examples = [("Leah Tran likes train and plane equally.",
                 [{"subject": "Leah Tran", "relation": "likes_equally", "object": "train and plane", "qualifiers": []}])]

    def facts(self, s, g, q):
        return [fact(s, "likes_equally", "train and plane", q)]


class PrefersTrain(Pred):
    name = "prefers_train"
    solves = "'X genuinely prefers train to plane when both are available': a real preference for train over flying"
    added_by = "learning"
    body = r"(?P<gen>genuinely )?(?:prefers|prefer) train to plane when both are available"
    examples = [("Leah Tran genuinely prefers train to plane when both are available.",
                 [{"subject": "Leah Tran", "relation": "prefers", "object": "train", "qualifiers": ["genuinely", "over plane"]}])]

    def facts(self, s, g, q):
        return [fact(s, "prefers", "train", q + (["genuinely"] if g.get("gen") else []) + ["over plane"])]


class ChoseTrain(Pred):
    name = "chose_train_disruption"
    solves = "'X chose train over plane (only) because of a disruption': one-off choice forced by a disruption, not a preference"
    added_by = "learning"
    body = r"(?:chose|choose) (?:the )?train over (?:the )?plane (?P<only>only )?because of a disruption"
    examples = [("Jia Gupta chose train over plane only because of a disruption.",
                 [{"subject": "Jia Gupta", "relation": "chose", "object": "train", "qualifiers": ["over plane", "only because of disruption"]}])]

    def facts(self, s, g, q):
        return [fact(s, "chose", "train", q + ["over plane", "only because of disruption" if g.get("only") else "because of disruption"])]


class LegalGuardian(Pred):
    name = "legal_guardian"
    solves = "'X is the legal guardian of Youth NNN'"
    added_by = "learning"
    body = r"(?:is|am) the legal guardian of (?P<y>[Yy](?:outh )?\d+)"
    examples = [("Omar Bennett is the legal guardian of Youth 075.",
                 [{"subject": "Omar Bennett", "relation": "legal_guardian_of", "object": "Y075", "qualifiers": []}])]

    def facts(self, s, g, q):
        return [fact(s, "legal_guardian_of", canon_name(g["y"]), q)]


class EmergencyContact(Pred):
    name = "emergency_contact"
    solves = "'X is an emergency contact (, but not a guardian,) for Youth NNN': contact only, explicitly not the guardian"
    added_by = "learning"
    body = (r"(?:is|am) (?:listed as )?an emergency contact(?P<n1>,? (?:but )?not a guardian,?)? for (?P<y>[Yy](?:outh )?\d+)"
            r"(?P<n2>,? but not a guardian)?")
    examples = [("R. Bennett is an emergency contact, but not a guardian, for Youth 058.",
                 [{"subject": "R. Bennett", "relation": "emergency_contact_of", "object": "Y058", "qualifiers": ["not guardian"]}])]

    def facts(self, s, g, q):
        if g.get("n1") or g.get("n2"):
            q.append("not guardian")
        return [fact(s, "emergency_contact_of", canon_name(g["y"]), q)]


class YouthCourse(Pred):
    name = "youth_course"
    solves = "'Youth NNN (currently) attends <course> during the evening|day'; relation attends_course with the daypart as qualifier"
    added_by = "learning"
    body = r"(?P<cur>currently )?(?:attends|attend) (?P<c>[a-z]+_[a-z_]+) during the (?P<d>evening|day)"
    examples = [("Youth 077 currently attends evening_carpentry during the evening.",
                 [{"subject": "Y077", "relation": "attends_course", "object": "evening_carpentry", "qualifiers": ["current", "evening"]}])]

    def facts(self, s, g, q):
        if g.get("cur"):
            q.append("current")
        return [fact(s, "attends_course", g["c"], q + [g["d"]])]
