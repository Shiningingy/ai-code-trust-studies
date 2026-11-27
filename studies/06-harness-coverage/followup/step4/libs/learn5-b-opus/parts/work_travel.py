"""Employment (employer, where the employer is based, shifts) and travel (modes of transport, train vs plane)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ORG, SUBJ, TemplateRule, name_form  # noqa: E402

_MODE = r"(?:the |a )?(?P<obj>bus|tram|subway|train|metro|ferry|bike|bicycle|car|plane|taxi|underground|streetcar|" \
        r"light rail|coach|boat|scooter|motorbike|[a-z]+)"


class WorksFor(TemplateRule):
    name = "works_for"
    solves = ("'<person> currently works for Organization 030' / 'Org 30' / 'used to work for ...': relation works_for, "
              "object 'Organization NNN' (all spellings joined), status=current or status=former")
    added_by = "learning"
    cores = [SUBJ + r" (?P<cur>currently |now |still )?(?:works|work|is working|am working|is employed|am employed) (?:for|at|with|by) "
                    r"(?P<org>" + ORG + ")",
             SUBJ + r" (?P<former>used to work|previously worked|formerly worked|worked|once worked|no longer works)"
                    r" (?:for|at|with) (?P<org>" + ORG + ")"]
    examples = [
        ("Ben Ito currently works for Org 30.", [{"subject": "Ben Ito", "relation": "works_for",
                                                  "object": "Organization 030", "qualifiers": ["status=current"]}]),
        ("usman works for organization 025", None),
        ("K. Usman used to work for Organization 025.",
         [{"subject": "K. Usman", "relation": "works_for", "object": "Organization 025",
           "qualifiers": ["status=former"]}]),
    ]

    def make(self, g):
        q = ["status=former"] if g.get("former") else (["status=current"] if g.get("cur") else [])
        return [("works_for", name_form(g["org"]), q)]


class BasedIn(TemplateRule):
    name = "based_in"
    solves = "'Organization 031 is based in Halifax' (also 'Org 31', 'located in'): relation based_in, object the city"
    added_by = "learning"
    cores = [SUBJ + r" (?:is|was) (?:based|located|headquartered|situated) in (?P<city>[A-Z][\w'.-]*(?: [A-Z][\w'.-]*){0,3})"]
    examples = [
        ("Organization 031 is based in Halifax.", [{"subject": "Organization 031", "relation": "based_in",
                                                    "object": "Halifax", "qualifiers": []}]),
        ("org 8 is based in St. John's.", [{"subject": "Organization 008", "relation": "based_in",
                                            "object": "St. John's", "qualifiers": []}]),
    ]

    def make(self, g):
        return [("based_in", " ".join(w[:1].upper() + w[1:] for w in g["city"].split()), [])]


class WorksShift(TemplateRule):
    name = "works_shift"
    solves = ("'<person> works the night|day shift' and the past forms 'works the night shift in a former role', "
              "'used to work the night shift', 'worked the night shift' -> status=former")
    added_by = "learning"
    cores = [SUBJ + r" (?P<cur>currently |now |still )?(?:works|work|is working|am working) (?:the |a |on the )?"
                    r"(?P<obj>night|day|evening|morning|late|early|weekend|afternoon) shifts?(?P<former> in a former role)?",
             SUBJ + r" (?P<former2>used to work|previously worked|formerly worked|worked|no longer works|stopped working|"
                    r"quit working|no longer working) (?:the |a |on the )?"
                    r"(?P<obj>night|day|evening|morning|late|early|weekend|afternoon) shifts?(?: in a former role)?"]
    examples = [
        ("Samir Laurent works the day shift.", [{"subject": "Samir Laurent", "relation": "works_shift",
                                                 "object": "day", "qualifiers": []}]),
        ("Samir Laurent works the night shift in a former role.",
         [{"subject": "Samir Laurent", "relation": "works_shift", "object": "night", "qualifiers": ["status=former"]}]),
    ]

    def make(self, g):
        if g.get("former") or g.get("former2"):
            q = ["status=former"]
        else:
            q = ["status=current"] if g.get("cur") else []
        return [("works_shift", g["obj"].lower(), q)]


class Travels(TemplateRule):
    name = "travels_by"
    solves = ("mode-of-transport clauses: 'routinely travels by <mode>' (freq=routine), '... but no longer does' "
              "(status=former), 'used to travel by <mode> routinely', 'used the <mode> once' (freq=once), 'plans to "
              "use the <mode> in the future' (time=future)")
    added_by = "learning"
    cores = [
        SUBJ + r" (?P<routine>routinely|usually|ordinarily|regularly|typically|normally|always|often|daily) "
               r"(?:travels|travel|traveled|travelled|commutes|commute|commuted|goes|go|gets around|rides|ride) by " + _MODE,
        SUBJ + r" (?P<routine2>routinely|usually|ordinarily|regularly|typically|normally|always|often|daily) "
               r"(?:takes|take|uses|use|rides|ride) the " + _MODE,
        SUBJ + r" (?:used to|previously would|formerly would) (?P<r3>routinely |usually |regularly )?(?:travel|commute|go)"
               r" by " + _MODE + r"(?P<r4> routinely| regularly| every day| daily)?",
        SUBJ + r" (?:used to|previously would) (?P<r5>routinely |usually |regularly )?(?:take|use|ride) the " + _MODE +
        r"(?P<r6> routinely| regularly| every day| daily)?",
        SUBJ + r" (?:used|took|rode|tried) the " + _MODE + r" (?P<once>once)",
        SUBJ + r" (?:plans|plan|intends|intend|is planning|am planning|wants|want) to (?:use|take|ride|travel by|try)"
               r" (?:the )?" + _MODE[len("(?:the |a )?"):] + r"(?P<future> in the future| soon| later| next year)?",
        SUBJ + r" (?:travels|travel|traveled|travelled|commutes|commute) by " + _MODE,
        SUBJ + r" (?:takes|take|rides|ride|uses|use|catches|catch) the " + _MODE[len("(?:the |a )?"):] +
        r" (?P<habit>every day|daily|most days|most weekdays|every weekday|every morning|to work|each day|regularly)",
    ]
    examples = [
        ("Ben Ito routinely travels by subway but no longer does.",
         [{"subject": "Ben Ito", "relation": "travels_by", "object": "subway",
           "qualifiers": ["freq=routine", "remark=but no longer does", "status=former"]}]),
        ("Farah Reed used the subway once.", [{"subject": "Farah Reed", "relation": "travels_by", "object": "subway",
                                               "qualifiers": ["freq=once"]}]),
        ("Ben Khan plans to use the bus in the future.", [{"subject": "Ben Khan", "relation": "travels_by",
                                                           "object": "bus", "qualifiers": ["time=future"]}]),
        ("foster used to travel by train routinely but no longer does", None),
        ("C. Foster used to travel by train routinely but no longer does.",
         [{"subject": "C. Foster", "relation": "travels_by", "object": "train",
           "qualifiers": ["freq=routine", "status=former", "remark=but no longer does"]}]),
    ]

    def make(self, g):
        if g.get("once"):
            q = ["freq=once"]
        elif "future" in g:
            q = ["time=future"]
        elif any(k in g for k in ("r3", "r5")):
            q = ["freq=routine", "status=former"]
        elif g.get("routine") or g.get("routine2") or g.get("habit"):
            q = ["freq=routine"]
        else:
            q = []
        return [("travels_by", g["obj"].lower(), q)]


class TrainVsPlane(TemplateRule):
    name = "train_vs_plane"
    solves = ("train-or-plane preference clauses: 'genuinely prefers train to plane when both are available' "
              "(relation prefers, object 'train over plane', qualifier genuine), 'chose train over plane only because "
              "of a disruption' (relation chose, qualifier reason=disruption), 'likes train and plane equally' "
              "(relation likes_equally, object 'train and plane')")
    added_by = "learning"
    cores = [
        SUBJ + r" (?P<pref>(?P<genuine>genuinely |truly |really |honestly |sincerely )?(?:prefers|prefer|preferred) "
               r"(?:the )?(?P<a>train|plane|bus|car) (?:to|over) (?:the )?(?P<b>train|plane|bus|car|flying)"
               r"(?P<both> when both are available| if both are available| whenever both are available)?)",
        SUBJ + r" (?P<chose>(?:chose|chooses|choose|picked|took) (?:the )?(?P<a2>train|plane) over (?:the )?"
               r"(?P<b2>train|plane)(?P<disr> only because of a disruption| because of a disruption| due to a disruption)?)",
        SUBJ + r" (?P<eq>(?:likes|like|enjoys|enjoy) (?:the )?(?P<a3>train|plane) and (?:the )?(?P<b3>train|plane) equally)",
    ]
    examples = [
        ("Ben Ito genuinely prefers train to plane when both are available.",
         [{"subject": "Ben Ito", "relation": "prefers", "object": "train over plane",
           "qualifiers": ["genuine", "when_both_available"]}]),
        ("Ben Ito chose train over plane only because of a disruption.",
         [{"subject": "Ben Ito", "relation": "chose", "object": "train over plane",
           "qualifiers": ["reason=disruption", "only_because"]}]),
        ("Ben Ito likes train and plane equally.", [{"subject": "Ben Ito", "relation": "likes_equally",
                                                     "object": "train and plane", "qualifiers": []}]),
    ]

    def make(self, g):
        if g.get("pref"):
            q = (["genuine"] if g["genuine"] else []) + (["when_both_available"] if g["both"] else [])
            return [("prefers", "%s over %s" % (g["a"].lower(), g["b"].lower()), q)]
        if g.get("chose"):
            q = []
            if g["disr"]:
                q = ["reason=disruption"] + (["only_because"] if "only" in g["disr"] else [])
            return [("chose", "%s over %s" % (g["a2"].lower(), g["b2"].lower()), q)]
        return [("likes_equally", "%s and %s" % (g["a3"].lower(), g["b3"].lower()), [])]
