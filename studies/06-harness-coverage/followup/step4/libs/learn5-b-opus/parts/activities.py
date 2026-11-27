"""Everyday activities: owning things, recommending and discussing, visiting places, helping at places."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ART, OBJ, SUBJ, TemplateRule, obj_norm  # noqa: E402

_PAST = {"some time ago": "time=past", "in the past": "time=past", "previously": "time=past", "before": "time=past",
         "a while ago": "time=past", "long ago": "time=past", "recently": "time=recent", "lately": "time=recent"}
_WHEN = r"(?: (?P<when>some time ago|in the past|previously|a while ago|long ago|recently|lately))?"


class Owns(TemplateRule):
    name = "owns"
    solves = ("possession clauses '<person> owns a <item>' (also 'own'/'has', 'owns garden tools', '... set'); "
              "a trailing '... set' is kept as qualifier item_detail=set")
    added_by = "learning"
    cores = [SUBJ + r" (?:owns|own|owned|has(?! been\b| \w+ed\b)|have(?! been\b| \w+ed\b)|keeps|keep|possesses) " + ART
             + OBJ]
    examples = [
        ("B. Ito owns a garden tools.", [{"subject": "B. Ito", "relation": "owns", "object": "garden tools",
                                         "qualifiers": []}]),
        ("Mateo Foster owns a telescope, which he often brings to our outdoor events.",
         [{"subject": "Mateo Foster", "relation": "owns", "object": "telescope",
           "qualifiers": ["remark=which he often brings to our outdoor events", "freq=often"]}]),
        ("Ben Ito said she owns a camera.", [{"subject": "Ben Ito", "relation": "owns", "object": "camera",
                                              "qualifiers": ["reported", "reported_by=Ben Ito"]}]),
        ("Rosa Chen owns a garden tools set.", [{"subject": "Rosa Chen", "relation": "owns", "object": "garden tools",
                                                "qualifiers": ["item_detail=set"]}]),
    ]

    def make(self, g):
        o, q = obj_norm(g["obj"]), []
        if o.endswith(" set"):
            o, q = o[:-4], ["item_detail=set"]
        elif o.startswith("set of "):
            o, q = o[7:], ["item_detail=set"]
        return [("owns", o, q)]


class Recommended(TemplateRule):
    name = "recommended"
    solves = "'<person> recommended <title>' (also 'suggested'); the object is the title in lower case without article"
    added_by = "learning"
    cores = [SUBJ + r" (?:recommended|recommends|recommend|suggested|suggests|suggest) " + ART + OBJ]
    examples = [
        ("Hana Ortiz recommended Quiet Machines.", [{"subject": "Hana Ortiz", "relation": "recommended",
                                                     "object": "quiet machines", "qualifiers": []}]),
        ("Ito recommended The Long Orchard to a colleague", None),
        ("K. Ito recommended The Long Orchard to a colleague.",
         [{"subject": "K. Ito", "relation": "recommended", "object": "long orchard",
           "qualifiers": ["remark=to a colleague"]}]),
    ]

    def make(self, g):
        return [("recommended", obj_norm(g["obj"]), [])]


class Discussed(TemplateRule):
    name = "discussed"
    solves = ("'<person> discussed <topic>' with or without article ('discussed the market', 'discussed Atlas of "
              "Clouds', 'discussed market trends'); object is the topic in lower case without article")
    added_by = "learning"
    cores = [SUBJ + r" (?:discussed|discusses|discuss|discussing|talked about|talks about|talking about|spoke about|"
                    r"mentioned) " + ART + OBJ]
    examples = [
        ("O. Diaz discussed library.", [{"subject": "O. Diaz", "relation": "discussed", "object": "library",
                                         "qualifiers": []}]),
        ("T. Avery discussed the market, highlighting its recent changes.",
         [{"subject": "T. Avery", "relation": "discussed", "object": "market",
           "qualifiers": ["remark=highlighting its recent changes"]}]),
    ]

    def make(self, g):
        return [("discussed", obj_norm(g["obj"]), [])]


class Visited(TemplateRule):
    name = "visited"
    solves = ("'<person> visited the <place> [some time ago|in the past|previously|recently]' (also 'went to'); "
              "the time words become time=past / time=recent")
    added_by = "learning"
    cores = [SUBJ + r" (?:visited|visits|visit|visiting|went to|goes to|go to|stopped by|dropped by) " + ART + OBJ + _WHEN]
    examples = [
        ("E. Patel visited the market some time ago.", [{"subject": "E. Patel", "relation": "visited",
                                                         "object": "market", "qualifiers": ["time=past"]}]),
        ("S. Gupta went to the museum, which contrasted with the other activities.",
         [{"subject": "S. Gupta", "relation": "visited", "object": "museum",
           "qualifiers": ["remark=which contrasted with the other activities"]}]),
    ]

    def make(self, g):
        return [("visited", obj_norm(g["obj"]), [_PAST[g["when"].lower()]] if g["when"] else [])]


class Helped(TemplateRule):
    name = "helped"
    solves = ("'<person> helped with <setup|cleanup|registration> at the <place>' (also 'assisted with', 'helping'): "
              "relation helped, object the place, qualifier task=<task>; when the place (or task) is only in a fronted "
              "phrase ('At the riverside park, A. Gupta helped with registration.', 'I was at the library for a "
              "cleanup when K. Mensah helped.') it is taken from there")
    added_by = "learning"
    _VERB = r" (?:helped|helps|help|helping|assisted|assists|assist|assisting)"
    cores = [SUBJ + _VERB + r" with (?:the )?(?P<task>[a-z][\w-]*(?: [a-z][\w-]*)?) at " + ART + OBJ + _WHEN,
             SUBJ + _VERB + r"(?: with (?:the )?(?P<task2>[a-z][\w-]*))?(?P<noplace>)"]
    examples = [
        ("Nadia Patel helped with setup at the market, ensuring everything was ready for the opening.",
         [{"subject": "Nadia Patel", "relation": "helped", "object": "market",
           "qualifiers": ["task=setup", "remark=ensuring everything was ready for the opening"]}]),
        ("H. Reed helped with registration at the museum.", [{"subject": "H. Reed", "relation": "helped",
                                                             "object": "museum", "qualifiers": ["task=registration"]}]),
        ("At the riverside park, a. gupta helped with registration.",
         [{"subject": "A. Gupta", "relation": "helped", "object": "riverside park",
           "qualifiers": ["task=registration", "context=At the riverside park"]}]),
        ("I was at the library for a cleanup when Kofi Mensah helped.",
         [{"subject": "Kofi Mensah", "relation": "helped", "object": "library",
           "qualifiers": ["task=cleanup", "reported", "reported_by=narrator",
                          "context=I was at the library for a cleanup"]}]),
        ("Dev Ito helped with setup there.", None),
    ]

    def make(self, g):
        if "noplace" not in g:
            q = ["task=" + g["task"].lower()]
            if g["when"]:
                q.append(_PAST[g["when"].lower()])
            return [("helped", obj_norm(g["obj"]), q)]
        for c in g["_ctx"]:
            m = re.search(r"\bat (?:the )?([a-z]+(?: [a-z]+)?)(?: for (?:a |the )?([a-z]+))?$", c, re.I)
            task = g["task2"] or (m and m.group(2))
            if m and task:
                return [("helped", obj_norm(m.group(1)), ["task=" + task.lower()])]
        return None
