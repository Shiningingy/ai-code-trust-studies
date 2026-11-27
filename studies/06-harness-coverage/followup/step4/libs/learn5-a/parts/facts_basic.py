import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import ClauseRule, WG, topic  # noqa: E402

PLACE_WORDS = r"[A-Za-z]+(?: (?:hall|park|center|centre|club|garden|group|circle|society|house|room))?"
PLACE = r"(?:the )?(?P<place>%s)" % PLACE_WORDS


def F(s, rel, obj="", q=()):
    return {"subject": s, "relation": rel, "object": obj, "qualifiers": list(q)}


class Recommended(ClauseRule):
    name = "recommended"
    solves = "a person recommended (or suggested) a book; relation recommended, object the canonical title"
    added_by = "learning"
    pred = r"(?:recommend|suggest)(?:s|ed)? (?P<title>%s)" % WG
    examples = [("Hana Ortiz recommended Quiet Machines.",
                 [{"subject": "Hana Ortiz", "relation": "recommended", "object": "Quiet Machines", "qualifiers": []}]),
                ("In a separate update, Kofi Ito recommended copper harbor.",
                 [{"subject": "Kofi Ito", "relation": "recommended", "object": "Copper Harbor", "qualifiers": []}])]

    def build(self, s, g):
        return [F(s, "recommended", topic(g["title"]))]


class Discussed(ClauseRule):
    name = "discussed"
    solves = ("a person discussed (talked about, mentioned) a topic: a place, a group, a book title or 'X events'; "
              "object is the canonical topic")
    added_by = "learning"
    pred = r"(?:discussed|discuss|talked about|mentioned|spoke about|discusses) (?:the )?(?P<topic>%s)" % WG
    examples = [("Priya Haddad discussed chess club.",
                 [{"subject": "Priya Haddad", "relation": "discussed", "object": "chess club", "qualifiers": []}]),
                ("Omar Diaz discussed the sports hall.",
                 [{"subject": "Omar Diaz", "relation": "discussed", "object": "sports hall", "qualifiers": []}])]

    def build(self, s, g):
        t = topic(g["topic"])
        m = re.fullmatch(r"((?:[a-z]+ (?:club|group|circle|society|hall|park))|market|library|museum)( .+)", t)
        if m:   # 'market trends', 'garden circle plans': the place or group is the topic, the extra word a qualifier
            return [F(s, "discussed", m.group(1), ["about " + m.group(2).strip()])]
        return [F(s, "discussed", t)]


class Owns(ClauseRule):
    name = "owns"
    solves = "a person owns (has, keeps) an item (garden tools, camera, guitar, telescope, sewing kit); article and 'set' dropped"
    added_by = "learning"
    pred = r"(?:owns?|has|have|keeps?) (?:my |his |her |their |a set of |an? )?(?P<item>%s)" % WG
    examples = [("B. Ito owns a garden tools set.",
                 [{"subject": "Ben Ito", "relation": "owns", "object": "garden tools", "qualifiers": []}])]

    def build(self, s, g):
        item = g["item"].lower()
        if item.startswith("garden tools "):
            item = "garden tools"
        return [F(s, "owns", item)]


class Visited(ClauseRule):
    name = "visited"
    solves = ("a person visited (went to) a place; time words (some time ago, in the past, previously, ...) "
              "become qualifiers")
    added_by = "learning"
    pred = r"(?:also )?(?P<pre>previously )?(?:visit(?:s|ed)?|went to|goes to|go to) %s" % PLACE
    examples = [("M. Khan visited the library some time ago.",
                 [{"subject": "Mateo Khan", "relation": "visited", "object": "library", "qualifiers": ["some time ago"]}]),
                ("Kofi Silva visited the market.",
                 [{"subject": "Kofi Silva", "relation": "visited", "object": "market", "qualifiers": []}]),
                ("Kofi Silva previously visited the market.",
                 [{"subject": "Kofi Silva", "relation": "visited", "object": "market", "qualifiers": ["previously"]}])]

    def build(self, s, g):
        return [F(s, "visited", g["place"].lower(), ["previously"] if g.get("pre") else [])]


class Helped(ClauseRule):
    name = "helped_with"
    solves = "a person helped (assisted) with registration/setup/cleanup at a place; relation helped_with_<activity>"
    added_by = "learning"
    pred = (r"(?:helped|helps|help|helping|assisted|assists?|assisting) with (?P<act>registration|setup|cleanup|[a-z]+)"
            r"(?: at (?:the )?(?P<place>[A-Za-z]+(?: (?:hall|park|center|centre|club|garden|group|circle|society|house|room))?))?")
    examples = [("K. Khan helped with setup at the library.",
                 [{"subject": "Kofi Khan", "relation": "helped_with_setup", "object": "library", "qualifiers": []}])]

    def build(self, s, g):
        place = g["place"]
        if not place:
            m = re.search(r"At the (%s)," % PLACE_WORDS, g["_pre"])
            place = m.group(1) if m else ""
        return [F(s, "helped_with_" + g["act"], place.lower())]


class Volunteered(ClauseRule):
    name = "volunteered"
    solves = "a person volunteered at an event id during this-year or last-year (old-event ids are last year's events)"
    added_by = "learning"
    pred = r"volunteer(?:s|ed)? at (?P<ev>[\w-]+)(?: during (?P<per>this-year|last-year|this year|last year))?"
    examples = [("O. Tran volunteered at event-P-015-0 during this-year.",
                 [{"subject": "Omar Tran", "relation": "volunteered_at", "object": "event-P-015-0", "qualifiers": ["this-year"]}])]

    def build(self, s, g):
        return [F(s, "volunteered_at", g["ev"], [g["per"].replace(" ", "-")] if g["per"] else [])]
