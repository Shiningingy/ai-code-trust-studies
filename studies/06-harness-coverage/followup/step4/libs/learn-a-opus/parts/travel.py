"""Travel: how people travel (routinely, once, planned) and train-versus-plane preferences."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import F, SUBJ, lead, slot  # noqa: E402

Q = ""
T = r"(?P<tail>.*)"
MODE = slot("mode", C.MODES)


class RoutinelyTravels(C.Core):
    name = "routinely_travels"
    solves = ("'X routinely travels by <mode>' -> travels_by with qualifier routinely; the past forms ('..., but no "
              "longer does', 'used to routinely travel by', 'used to travel by', 'routinely traveled') add past")
    added_by = "learning"
    pattern = (Q + SUBJ + r" (?:(?P<past>used to (?:routinely )?travel|routinely traveled|routinely travelled)|"
               r"routinely travels|routinely travel|(?P<plain>travels|travel)) by " + MODE + T)
    examples = [
        ("Ben Laurent routinely travels by subway.", [F("Ben Laurent", "travels_by", "subway", "routinely")]),
        ("Quinn Novak routinely travels by train but no longer does.",
         [F("Quinn Novak", "travels_by", "train", "routinely", "past")]),
        ("I used to routinely travel by subway but no longer do.",
         [F("I", "travels_by", "subway", "routinely", "past")]),
    ]

    def make(self, s, g, q):
        return [F(s, "travels_by", C.obj(g["mode"]), [] if g["plain"] else ["routinely"], lead(g, "past", "past"), q)]


class UsedOnce(C.Core):
    name = "used_transport_once"
    solves = ("'X used the <mode> once' (also 'took the <mode> once') -> travels_by with qualifier once (a single "
              "trip, not a habit)")
    added_by = "learning"
    pattern = Q + SUBJ + r" (?:used|took|rode) " + MODE + r" once" + T
    examples = [("Farah Reed used the subway once.", [F("Farah Reed", "travels_by", "subway", "once")])]

    def make(self, s, g, q):
        return [F(s, "travels_by", C.obj(g["mode"]), "once", q)]


class UsedToTake(C.Core):
    name = "used_to_take_transport"
    solves = "'X used to take the <mode>' -> travels_by with qualifier past (a former habit)"
    added_by = "learning"
    pattern = Q + SUBJ + r" used to (?:take|ride|use) " + MODE + T
    examples = [("O. Usman used to take the tram.", [F("O. Usman", "travels_by", "tram", "past")])]

    def make(self, s, g, q):
        return [F(s, "travels_by", C.obj(g["mode"]), "past", q)]


class PlansToUse(C.Core):
    name = "plans_to_use_transport"
    solves = "'X plans to use the <mode> in the future' -> travels_by with qualifier future (not yet a habit)"
    added_by = "learning"
    pattern = Q + SUBJ + r" (?:plans|plan|intends|intend) to (?:use|take) " + MODE + r"(?: in the future)?" + T
    examples = [("Ben Khan plans to use the bus in the future.", [F("Ben Khan", "travels_by", "bus", "future")])]

    def make(self, s, g, q):
        return [F(s, "travels_by", C.obj(g["mode"]), "future", q)]


class GenuinelyPrefers(C.Core):
    name = "prefers_mode"
    solves = ("'X genuinely prefers train to plane when both are available' -> prefers train, qualifiers over:plane, "
              "genuinely, when both are available")
    added_by = "learning"
    pattern = (Q + SUBJ + r" (?:(?P<gen>genuinely) )?(?:prefers|prefer) " + slot("a", C.MODES) + r" (?:to|over) "
               + slot("b", C.MODES) + r"(?P<both> when both are available)?" + T)
    examples = [("Quinn Ortiz genuinely prefers train to plane when both are available.",
                 [F("Quinn Ortiz", "prefers", "train", "over:plane", "genuinely", "when both are available")])]

    def make(self, s, g, q):
        return [F(s, "prefers", C.obj(g["a"]), "over:" + C.obj(g["b"]), lead(g, "gen", "genuinely"),
                  lead(g, "both", "when both are available"), q)]


class LikesEqually(C.Core):
    name = "likes_modes_equally"
    solves = "'X likes train and plane equally' -> likes_equally 'train and plane' (no preference between the two)"
    added_by = "learning"
    pattern = Q + SUBJ + r" (?:likes|like) " + slot("a", C.MODES) + r" and " + slot("b", C.MODES) + r" equally" + T
    examples = [("Farah Reed likes train and plane equally.", [F("Farah Reed", "likes_equally", "train and plane")]),
                ("Jia Diaz likes train and plane equally, so we could go either way.",
                 [F("Jia Diaz", "likes_equally", "train and plane", "note:so we could go either way")])]

    def make(self, s, g, q):
        return [F(s, "likes_equally", C.obj(g["a"]) + " and " + C.obj(g["b"]), q)]


class ChoseOver(C.Core):
    name = "chose_mode_over"
    solves = ("'X chose train over plane only because of a disruption' -> chose train, qualifiers over:plane and the "
              "reason (a forced choice, not a preference)")
    added_by = "learning"
    pattern = (Q + SUBJ + r" (?:chose|choose|picked) " + slot("a", C.MODES) + r" (?:over|instead of) "
               + slot("b", C.MODES) + r"(?: (?P<why>only because of [a-z ]+?|because of [a-z ]+?))?" + C.TAIL_START + T)
    examples = [("Ben Haddad chose train over plane only because of a disruption.",
                 [F("Ben Haddad", "chose", "train", "over:plane", "reason:only because of a disruption")])]

    def make(self, s, g, q):
        return [F(s, "chose", C.obj(g["a"]), "over:" + C.obj(g["b"]),
                  ["reason:" + g["why"].lower()] if g["why"] else [], q)]
