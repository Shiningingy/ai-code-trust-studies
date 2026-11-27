"""Food habits, guardianship and emergency contacts, and the courses young people attend."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import FactRule, add, fact  # noqa: E402
from gram import Rule  # noqa: E402


class Avoids(FactRule, Rule):
    name = "avoids_food"
    solves = ("dietary choices: 'currently chooses to avoid dairy products' (relation avoids, a lasting choice) "
              "versus 'is temporarily skipping <food>' (relation skips, qualifier temporarily)")
    added_by = "learning"
    phrases = [r"(?P<v>chooses to avoid|choose to avoid|chose to avoid|avoids|avoid|avoided|is avoiding|"
               r"am avoiding|does not eat|do not eat|doesn't eat|don't eat|never eats) (?P<o>dairy products|dairy|"
               r"meat|gluten|sugar|%s)" % C.FOOD,
               r"(?:is|am|was) (?P<tmp>temporarily )?(?P<v>skipping|avoiding|cutting out|giving up) (?P<o>%s|dairy "
               r"products|dairy)" % C.FOOD]
    examples = [
        ("Elena Jones currently chooses to avoid dairy products.",
         [fact("Elena Jones", "avoids", "dairy products", ["time:current", "choice"])]),
        ("N. Silva is temporarily skipping milk.", [fact("N. Silva", "skips", "milk", ["temporarily"])]),
    ]

    def facts(self, s, g, q):
        v = g["v"].lower()
        o = g["o"].lower()
        if v in ("skipping", "cutting out", "giving up"):
            return [fact(s, "skips", o, add(q, "temporarily" if g.get("tmp") else None))]
        if g.get("tmp"):
            return [fact(s, "skips", o, add(q, "temporarily"))]
        if "eat" in v:
            return [fact(s, "eats", o, add(q, "neg"))]
        extra = ["choice"] if "choose" in v or "chose" in v else []
        if v in ("chose to avoid", "avoided"):
            extra.append("time:past")
        return [fact(s, "avoids", o, add(q, *extra))]


class EatingHabits(FactRule, Rule):
    name = "eating_habits"
    solves = ("likes and dislikes of food: 'enjoys eating <food>' (enjoys_eating; 'used to enjoy', 'enjoyed ... in "
              "the past' are past), 'dislikes eating <food>', 'buys <food> for other people' (buys_for_others, "
              "not eating), 'serves <food> to other people but does not eat it' (serves_to_others + eats neg)")
    added_by = "learning"
    phrases = [
        r"(?P<v>enjoys|enjoy|enjoyed|likes|like|liked|loves|love|loved) (?:eating (?P<o>%s)|(?P<o2>%s))(?= |$|,)"
        % (C.FOOD, "|".join(C.FOODS)),
        r"(?P<v>dislikes|dislike|disliked|hates|hate) (?:eating )?(?P<o>%s)" % C.FOOD,
        r"(?P<v>buys|buy|bought|purchases) (?P<o>%s) for (?:other people|others)" % C.FOOD,
        r"(?P<v>serves|serve|served|cooks|cook|prepares) (?P<o>%s) (?:to|for) (?:other people|others)"
        r"(?P<neg>,? but (?:does not|do not|doesn't|don't|never) eat (?:it|them))?" % C.FOOD,
        r"(?P<v>eats|eat|ate) (?P<o>%s)(?= |$|,)" % C.FOOD,
    ]
    examples = [
        ("Ben Ito enjoys eating banana.", [fact("Ben Ito", "enjoys_eating", "banana")]),
        ("Ben Ito used to enjoy eating pear.", [fact("Ben Ito", "enjoys_eating", "pear", ["time:past"])]),
        ("Ben Ito enjoyed eating pear in the past.", [fact("Ben Ito", "enjoys_eating", "pear", ["time:past"])]),
        ("Nadia Laurent buys cheese for other people.", [fact("Nadia Laurent", "buys_for_others", "cheese")]),
        ("Omar Chen serves mango to other people but does not eat it",
         [fact("Omar Chen", "serves_to_others", "mango"), fact("Omar Chen", "eats", "mango", ["neg"])]),
        ("Ben Ito dislikes eating yogurt, so he rarely buys it.", [fact("Ben Ito", "dislikes_eating", "yogurt")]),
    ]

    def facts(self, s, g, q):
        v, o = g["v"].lower(), (g["o"] or g.get("o2", "")).lower()
        past = v.endswith("ed") or v in ("bought", "ate")
        q = add(q, "time:past") if past and v not in ("served", "bought") else q
        if v.startswith(("enjoy", "lik", "lov")):
            return [fact(s, "enjoys_eating", o, q)]
        if v.startswith(("dislik", "hat")):
            return [fact(s, "dislikes_eating", o, q)]
        if v.startswith(("buy", "bought", "purchas")):
            return [fact(s, "buys_for_others", o, q)]
        if v.startswith(("serv", "cook", "prepar")):
            out = [fact(s, "serves_to_others", o, q)]
            if g.get("neg"):
                out.append(fact(s, "eats", o, add(q, "neg")))
            return out
        return [fact(s, "eats", o, q)]


class Guardian(FactRule, Rule):
    name = "guardian"
    solves = ("guardianship: 'is the legal guardian of Y118 / Youth 118' (guardian_of) versus 'is an emergency "
              "contact, but not a guardian, for Y118' (emergency_contact_for, plus guardian_of with neg)")
    added_by = "learning"
    phrases = [
        r"(?:is|am|was|are) (?:the |a )?(?P<legal>legal )?guardian (?:of|for) (?P<y>%s)" % C.YOUTH,
        r"(?:is|am|was|are) (?:listed as )?(?:an |the )?emergency contact(?P<n1>,? (?:but )?not (?:a |the )?"
        r"(?:legal )?guardian,?)? for (?P<y>%s)(?P<n2>,? but not (?:a |the )?(?:legal )?guardian)?" % C.YOUTH,
    ]
    examples = [
        ("Ben Ito is the legal guardian of Y118.", [fact("Ben Ito", "guardian_of", "Y118", ["legal"])]),
        ("Rosa Evans is an emergency contact, but not a guardian, for Y118, a distinction that was important",
         [fact("Rosa Evans", "emergency_contact_for", "Y118"), fact("Rosa Evans", "guardian_of", "Y118", ["neg"])]),
        ("Talia Usman is an emergency contact for Youth 140, but not a guardian",
         [fact("Talia Usman", "emergency_contact_for", "Y140"), fact("Talia Usman", "guardian_of", "Y140",
                                                                     ["neg"])]),
    ]

    def facts(self, s, g, q):
        y = C.youth(g["y"])
        if "n1" not in g:
            return [fact(s, "guardian_of", y, add(q, "legal" if g["legal"] else None))]
        out = [fact(s, "emergency_contact_for", y, q)]
        if g["n1"] or g["n2"]:
            out.append(fact(s, "guardian_of", y, add(q, "neg")))
        return out


class YouthCourse(FactRule, Rule):
    name = "youth_course"
    solves = ("courses young people attend: 'Y150 currently attends evening_pottery during the evening' (relation "
              "attends_course, object the course id, qualifiers time:current and during:evening/day)")
    added_by = "learning"
    subject = r"(?:%s|I)" % C.YOUTH
    person_subject = False
    phrases = [r"(?P<v>attends|attend|attended|is attending|is enrolled in|takes|took) (?:the )?(?P<o>[a-z]+_[a-z_]+)"]
    examples = [
        ("Y150 currently attends daytime_first_aid during the day.",
         [fact("Y150", "attends_course", "daytime_first_aid", ["time:current", "during:day"])]),
        ("youth 096 currently attends evening_language during the evening",
         [fact("Y096", "attends_course", "evening_language", ["time:current", "during:evening"])]),
    ]

    def facts(self, s, g, q):
        if g["v"].lower() in ("attended", "took"):
            q = add(q, "time:past")
        return [fact(C.youth(s) if s != "I" else "I", "attends_course", g["o"].lower(), q)]


class Roster(Rule):
    name = "roster"
    solves = ("the identity sentence 'The community roster records <full name> under identifier P-114 and also uses "
              "the familiar names <short name>': every written form of the person gets has_id -> P-114 (the "
              "familiar names with qualifier 'alias'); 'records me' inside a quote is the speaker")
    added_by = "learning"
    RX = re.compile(r"(?:I, (?P<self>%s), can confirm (?:that )?)?(?:the community roster|the roster) (?:records|lists|has) (?P<s>%s|me) under (?:the )?"
                    r"identifier (?P<id>%s)(?: and also uses the familiar names? (?P<al>%s(?:(?:,| and|, and) %s)*))?"
                    r"(?P<tail>.*)" % (C.NAME, C.NAME, C.PID, C.NAME, C.NAME), re.I)
    examples = [
        ("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed.",
         [fact("Nadia Reed", "has_id", "P-114"), fact("N. Reed", "has_id", "P-114", ["alias"])]),
        ("the community roster records f. patel under identifier p-006",
         [fact("F. Patel", "has_id", "P-006")]),
        ("The community roster records me under identifier P-076 and also uses the familiar names P. Ito",
         [fact("I", "has_id", "P-076"), fact("P. Ito", "has_id", "P-076", ["alias"])]),
    ]

    def parse(self, clause):
        for q, c in C.evidence_candidates(clause.strip().rstrip(".!?").strip()):
            out = self._parse(q, c)
            if out is not None:
                return out
        return None

    def _parse(self, q, c):
        m = self.RX.fullmatch(c)
        if not m:
            return None
        if m.group("s").lower() != "me" and not C.is_name(m.group("s")):
            return None
        tq = C.tail_quals(m.group("tail"))
        if tq is None:
            return None
        q = C.add(q, *tq)
        i = C.pid(m.group("id"))
        s = m.group("s")
        if s.lower() == "me" and m.group("self"):
            s = m.group("self")
        out = [fact(C.person(s), "has_id", i, q)]
        for a in re.split(r",? and |, ", m.group("al") or ""):
            if a.strip():
                out.append(fact(C.person(a), "has_id", i, C.add(q, "alias")))
        return out


C.register(Roster)
