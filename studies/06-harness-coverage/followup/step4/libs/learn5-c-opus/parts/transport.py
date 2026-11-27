"""Transport: habitual travel ('routinely travels by subway [but no longer does]'), single uses ('used the tram once'),
plans ('plans to use the bus in the future'), and travel preferences ('genuinely prefers train to plane when both are
available', 'likes train and plane equally', 'chose train over plane only because of a disruption')."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402

_NOLONGER = r"(?P<nl>,? but (?:I |he |she |they )?no longer (?:does|do))?"


def _travel(base):
    def build(g, q):
        out = list(base)
        if g.get("r") or g.get("r2"):
            out.append("freq:routinely")
        if g.get("nl"):
            out.append("status:former")
        return [("travels_by", g["veh"].lower(), out + q)]
    return build


lang.register("transport", r"(?P<r>routinely )?(?:travels|travel) by (?:the )?(?P<veh>[a-z]+)(?P<r2> routinely)?"
                           r"(?: to work)?" + _NOLONGER + "{M}", _travel([]), stative=True)
lang.register("transport", r"(?P<r>routinely )?(?:traveled|travelled) by (?:the )?(?P<veh>[a-z]+)(?P<r2> routinely)?"
                           r"(?: to work)?" + _NOLONGER + "{M}", _travel(["status:former"]), stative=True)
lang.register("transport", r"used to (?P<r>routinely )?(?:travel by|take|ride|use) (?:the )?(?P<veh>[a-z]+)"
                           r"(?P<r2> routinely)?" + _NOLONGER + "{M}", _travel(["status:former"]), stative=True)
# a closed class: "took the advice" is not travel
VEH = r"(?P<veh>bus|tram|train|subway|metro|ferry|car|bike|bicycle|taxi|plane|coach|streetcar|trolley|underground)"
lang.register("transport", r"(?:used|took|rode) the " + VEH + "{M}", _travel([]))
lang.register("transport", r"(?:plans|plan|intends|intend) to (?:use|take|ride) the " + VEH + "{M}",
              _travel(["status:planned"]))


def _pref(g, q):
    return [("prefers", g["a"].lower(), (["genuine"] if g["g"] else []) + ["over:" + g["b"].lower()] + q)]


lang.register("travel_preference", r"(?P<g>genuinely |really |truly )?(?:prefers|prefer) (?:the )?(?P<a>[a-z]+)(?: travel)? "
                                   r"(?:to|over) (?:the )?(?P<b>[a-z]+)(?: travel)?(?: when both are available)?{M}",
              _pref, stative=True)
lang.register("travel_preference", r"(?:likes|like) (?P<a>[a-z]+) and (?P<b>[a-z]+) equally{M}",
              lambda g, q: [("likes_equally", g["a"].lower(), ["and:" + g["b"].lower()] + q)], stative=True)
lang.register("travel_preference", r"(?:chose|chooses|choose) (?:the )?(?P<a>[a-z]+) over (?:the )?(?P<b>[a-z]+)(?P<only> only)? "
                                   r"because of (?:a |an |the )?(?P<why>[a-z]+){M}",
              lambda g, q: [("chose_over", g["a"].lower(), ["over:" + g["b"].lower(), "reason:" + g["why"]]
                             + (["only_because"] if g["only"] else []) + q)])


class Transport(Rule):
    name = "transport"
    solves = ("travel-mode clauses -> travels_by <vehicle>; 'routinely' gives freq:routinely, 'once' freq:once, "
              "'plans to use ... in the future' status:planned, 'but no longer does' / 'used to' status:former")
    added_by = "learning"
    examples = [
        ("Nadia Mensah routinely travels by subway but no longer does.",
         [lang.fact("Nadia Mensah", "travels_by", "subway", ["freq:routinely", "status:former"])]),
        ("E. Novak routinely travels by tram", [lang.fact("E. Novak", "travels_by", "tram", ["freq:routinely"])]),
        ("Farah Reed used the subway once", [lang.fact("Farah Reed", "travels_by", "subway", ["freq:once"])]),
        ("A. Diaz plans to use the tram in the future.",
         [lang.fact("A. Diaz", "travels_by", "tram", ["status:planned"])]),
        ("Omar Diaz said he used the bus once.",
         [lang.fact("Omar Diaz", "travels_by", "bus", ["freq:once", "reported_by:Omar Diaz"])]),
        ("Leah Usman used to take the tram most weekdays, but she no longer does",
         [lang.fact("Leah Usman", "travels_by", "tram", ["status:former", "when:most weekdays"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"transport"})


class TravelPreference(Rule):
    name = "travel_preference"
    solves = ("travel preference clauses: 'genuinely prefers A to B' -> prefers A [genuine, over:B]; 'likes A and B "
              "equally' -> likes_equally A [and:B]; 'chose A over B only because of a disruption' -> chose_over A "
              "[over:B, reason:disruption, only_because] (a forced choice, not a preference)")
    added_by = "learning"
    examples = [
        ("D. Chen genuinely prefers train to plane when both are available.",
         [lang.fact("D. Chen", "prefers", "train", ["genuine", "over:plane"])]),
        ("Isaac Reed likes train and plane equally.",
         [lang.fact("Isaac Reed", "likes_equally", "train", ["and:plane"])]),
        ("K. Khan chose train over plane only because of a disruption.",
         [lang.fact("K. Khan", "chose_over", "train", ["over:plane", "reason:disruption", "only_because"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"travel_preference"})
