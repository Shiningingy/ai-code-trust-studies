"""Food (avoiding, skipping, liking, buying or serving food) and family ties (guardians, emergency contacts, the
courses young people attend)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OBJ, SUBJ, YOUTH, TemplateRule, name_form, obj_norm  # noqa: E402


class AvoidsFood(TemplateRule):
    name = "avoids_food"
    solves = ("'<person> currently chooses to avoid dairy products' (relation avoids, status=current) and "
              "'<person> is temporarily skipping cheese' (relation avoids, qualifier temporary)")
    added_by = "learning"
    cores = [SUBJ + r" (?P<cur>currently |now |still )?(?:chooses|choose|chose|has chosen|decided|decides) to avoid " + OBJ,
             SUBJ + r" (?P<cur2>currently |now )?(?:avoids|avoid|is avoiding|am avoiding) (?:eating )?" + OBJ,
             SUBJ + r" (?:is|am|has been) (?P<temp>temporarily |currently )?(?:skipping|avoiding|cutting out|"
                    r"giving up|off) " + OBJ]
    examples = [
        ("Ben Ito currently chooses to avoid dairy products.",
         [{"subject": "Ben Ito", "relation": "avoids", "object": "dairy products", "qualifiers": ["status=current"]}]),
        ("Ben Ito is temporarily skipping cheese.", [{"subject": "Ben Ito", "relation": "avoids", "object": "cheese",
                                                      "qualifiers": ["temporary"]}]),
    ]

    def make(self, g):
        if "temp" in g:
            q = ["temporary"] if g["temp"].strip().lower() == "temporarily" else (["status=current"] if g["temp"] else [])
        else:
            q = ["status=current"] if (g.get("cur") or g.get("cur2")) else []
        return [("avoids", obj_norm(g["obj"]), q)]


class EatingTaste(TemplateRule):
    name = "eating_taste"
    solves = ("'<person> enjoys eating <food>' (relation enjoys_eating), 'used to enjoy eating' (status=former), "
              "'dislikes eating <food>' (relation dislikes_eating); past tense 'enjoyed eating' -> status=former")
    added_by = "learning"
    cores = [SUBJ + r" (?P<v>enjoys|enjoy|enjoyed|likes|like|liked|loves|love|loved|dislikes|dislike|disliked|hates|hate|hated|"
                    r"used to enjoy|used to like|"
                    r"used to dislike) eating " + OBJ]
    examples = [
        ("Ben Ito enjoys eating watermelon.", [{"subject": "Ben Ito", "relation": "enjoys_eating",
                                                "object": "watermelon", "qualifiers": []}]),
        ("Ben Ito dislikes eating milk.", [{"subject": "Ben Ito", "relation": "dislikes_eating", "object": "milk",
                                            "qualifiers": []}]),
        ("Ben Ito used to enjoy eating pear.", [{"subject": "Ben Ito", "relation": "enjoys_eating", "object": "pear",
                                                 "qualifiers": ["status=former"]}]),
    ]

    def make(self, g):
        v = g["v"].lower()
        rel = "dislikes_eating" if ("dislike" in v or "hate" in v) else "enjoys_eating"
        former = v.startswith("used to") or v.endswith("ed")
        return [(rel, obj_norm(g["obj"]), ["status=former"] if former else [])]


class FoodForOthers(TemplateRule):
    name = "food_for_others"
    solves = ("'<person> buys <food> for other people' (relation buys_for_others) and '<person> serves <food> to "
              "other people but does not eat it' (relation serves_to_others, plus eats <food> with qualifier neg)")
    added_by = "learning"
    cores = [SUBJ + r" (?:buys|buy|bought|purchases) " + OBJ + r" for (?:other people|others)",
             SUBJ + r" (?:serves|serve|served|cooks|cook|makes) " + OBJ + r" (?:to|for) (?:other people|others)"
                    r"(?P<neg>,? but does not eat it|,? but doesn't eat it|,? but never eats it|,? but do not eat it)?"]
    examples = [
        ("Ben Ito buys cheese for other people.", [{"subject": "Ben Ito", "relation": "buys_for_others",
                                                    "object": "cheese", "qualifiers": []}]),
        ("Ben Ito serves apple to other people but does not eat it.",
         [{"subject": "Ben Ito", "relation": "serves_to_others", "object": "apple", "qualifiers": []},
          {"subject": "Ben Ito", "relation": "eats", "object": "apple", "qualifiers": ["neg"]}]),
    ]

    def make(self, g):
        o = obj_norm(g["obj"])
        if "neg" not in g:
            return [("buys_for_others", o, [])]
        out = [("serves_to_others", o, [])]
        if g["neg"]:
            out.append(("eats", o, ["neg"]))
        return out


class Guardian(TemplateRule):
    name = "guardian"
    solves = ("'<person> is the legal guardian of Y055' (relation guardian_of) and '<person> is an emergency contact, "
              "but not a guardian, for Y007' / '... for Y140, but not a guardian' (relation emergency_contact_for, "
              "plus guardian_of with qualifier neg)")
    added_by = "learning"
    cores = [SUBJ + r" (?:is|am|was|remains) (?:the |a )?(?:legal )?guardian (?:of|for) (?P<y>" + YOUTH + ")",
             SUBJ + r" (?:is|am) (?:listed as |named as |registered as )?(?:an|the) emergency contact"
                    r"(?P<neg1>,? (?:but )?not (?:a|the) (?:legal )?guardian,?)? "
                    r"(?:for|of) (?P<y2>" + YOUTH + r")(?P<neg2>,? (?:but )?not (?:a|the|their|his|her) (?:legal )?guardian)?"]
    examples = [
        ("Ben Ito is the legal guardian of Y055.", [{"subject": "Ben Ito", "relation": "guardian_of",
                                                     "object": "Y055", "qualifiers": []}]),
        ("Ben Ito is an emergency contact, but not a guardian, for Y007.",
         [{"subject": "Ben Ito", "relation": "emergency_contact_for", "object": "Y007", "qualifiers": []},
          {"subject": "Ben Ito", "relation": "guardian_of", "object": "Y007", "qualifiers": ["neg"]}]),
    ]

    def make(self, g):
        if "y" in g:
            return [("guardian_of", name_form(g["y"]), [])]
        y = name_form(g["y2"])
        out = [("emergency_contact_for", y, [])]
        if g["neg1"] or g["neg2"]:
            out.append(("guardian_of", y, ["neg"]))
        return out


class YouthCourse(TemplateRule):
    name = "youth_course"
    solves = ("'Y055 currently attends evening_language during the evening' (also 'Youth 9'): relation attends, "
              "object the course id, qualifiers status=current and when=evening|day")
    added_by = "learning"
    cores = [SUBJ + r" (?P<cur>currently |now |still )?(?:attends|attend|is attending|am attending|takes|is taking|"
                    r"is enrolled in|am enrolled in|is (?:currently )?enrolled in) "
                    r"(?:the )?(?P<obj>[a-z]+_[a-z_]+)(?: (?:class|course))?(?: (?:during|in) the (?P<when>evening|day|"
                    r"morning|afternoon|daytime|night))?"]
    examples = [
        ("Y055 currently attends evening_language during the evening.",
         [{"subject": "Y055", "relation": "attends", "object": "evening_language",
           "qualifiers": ["status=current", "when=evening"]}]),
    ]

    def make(self, g):
        q = (["status=current"] if g["cur"] else []) + (["when=" + g["when"].lower()] if g["when"] else [])
        return [("attends", g["obj"].lower(), q)]
