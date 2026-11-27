"""Everyday activities: owning things, recommending and discussing, attending groups, visiting places, helping at
places, volunteering at events, taking part in classes."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import FactRule, add, fact  # noqa: E402
from gram import Rule  # noqa: E402


class Owns(FactRule, Rule):
    name = "owns"
    solves = ("'<person> owns a <item>' with its variants (own/owned, 'a garden tools set', 'owns camera', 'keeps a "
              "set of garden tools', 'mentioned keeping a sewing kit') and any elaboration after it; 'but I do not' "
              "inside a quote negates the speaker's own ownership")
    added_by = "learning"
    phrases = [r"(?P<v>owns|own|owned|has|have) (?:a |an |the )?(?P<o>%s)(?: set)?(?P<neg>, but I do not)?" % C.ITEM,
               r"(?P<v>keeps|keep|kept|mentioned keeping) (?:a set of |my |his |her |their |a |an |the )?"
               r"(?P<o>%s)(?: set)?" % "|".join(C.ITEMS)]
    examples = [
        ("B. Ito owns a garden tools.", [fact("B. Ito", "owns", "garden tools")]),
        ("Kofi Ortiz owns a guitar and plays it on weekends.", [fact("Kofi Ortiz", "owns", "guitar")]),
        ("B. Ortiz owns a telescope, which he used to show us the stars.", [fact("B. Ortiz", "owns", "telescope")]),
        ("Mateo Foster owns a telescope, which he often brings to our outdoor events.",
         [fact("Mateo Foster", "owns", "telescope")]),
        ("Leah Bennett owns a garden tools set for her backyard.", [fact("Leah Bennett", "owns", "garden tools")]),
        ("k. laurent owns a guitar", [fact("K. Laurent", "owns", "guitar")]),
        ("Ben Novak owns a camera, but I do not",
         [fact("Ben Novak", "owns", "camera"), fact("I", "owns", "camera", ["neg"])]),
    ]

    def facts(self, s, g, q):
        if g["v"].lower() == "mentioned keeping":
            q = add(q, "reported_by:" + s)
        if g["v"].lower() in ("has", "have", "keeps", "keep", "kept") and C.thing(g["o"]) not in C.ITEMS:
            return None
        q = add(q, "time:past") if g["v"].lower() == "owned" else q
        out = [fact(s, "owns", C.thing(g["o"]), q)]
        if g.get("neg"):
            out.append(fact("I", "owns", C.thing(g["o"]), add([x for x in q if x != "time:past"], "neg")))
        return out


class Recommended(FactRule, Rule):
    name = "recommended"
    solves = "'<person> recommended <book>' (also 'suggested'), with any elaboration ('to the group', 'as a good read')"
    added_by = "learning"
    phrases = [r"(?:recommended|recommends|recommend|suggested|suggests) (?P<o>%s)" % C.BOOK]
    examples = [
        ("Hana Ortiz recommended Quiet Machines.", [fact("Hana Ortiz", "recommended", "Quiet Machines")]),
        ("Jia Gupta recommended The Long Orchard, and we plan to check it out soon.",
         [fact("Jia Gupta", "recommended", "The Long Orchard")]),
        ("gabriel evans recommended the long orchard", [fact("Gabriel Evans", "recommended", "The Long Orchard")]),
        ("Rosa Usman recommended Quiet Machines as a good listen.",
         [fact("Rosa Usman", "recommended", "Quiet Machines")]),
    ]

    def facts(self, s, g, q):
        return [fact(s, "recommended", C.book(g["o"]), q)]


class Discussed(FactRule, Rule):
    name = "discussed"
    solves = ("'<person> discussed <topic>' where the topic is a book, group or place, with or without 'the' "
              "('talked about' too; 'mentioned' only with a known topic) and any elaboration ('market trends', "
              "'with the team'); a noun after a group or place ('market trends', 'library hours') is the aspect "
              "discussed: object 'market', qualifier 'aspect:trends'")
    added_by = "learning"
    phrases = [r"(?:discussed|discusses|discuss|discussing|talked about|talks about) (?:(?P<b>%s)|(?:the )?(?P<o>%s|%s)"
               r"(?: (?P<asp>%s))?)" % ("|".join(C.BOOKS), C.GROUP, C.PLACE, C.ASPECT),
               # "mentioned" also introduces other things ("mentioned keeping a sewing kit"): known topics only
               r"(?:mentioned|mentions) (?:(?P<b>%s)|(?:the )?(?P<o>%s))"
               % ("|".join(C.BOOKS), "|".join(C.GROUPS + C.PLACES))]
    examples = [
        ("Priya Haddad discussed chess club.", [fact("Priya Haddad", "discussed", "chess club")]),
        ("Rosa Avery discussed garden circle, a group that meets weekly.",
         [fact("Rosa Avery", "discussed", "garden circle")]),
        ("elena Jones discussed Atlas of Clouds.", [fact("Elena Jones", "discussed", "Atlas of Clouds")]),
        ("T. Avery discussed the market, highlighting its recent changes.", [fact("T. Avery", "discussed", "market")]),
        ("A recent personal note mentioned that C. Silva discussed Copper Harbor.",
         [fact("C. Silva", "discussed", "Copper Harbor", ["evidence:record"])]),
        ("S. Laurent discussed market trends.",[fact("S. Laurent", "discussed", "market", ["aspect:trends"])]),
        ("Jia Ito discussed sports hall during the shift handoff.", [fact("Jia Ito", "discussed", "sports hall")]),
        ("H. Novak discussed history group activities with the team.",
         [fact("H. Novak", "discussed", "history group", ["aspect:activities"])]),
        ("O. Foster discussed The Long Orchard, and it made me think", [fact("O. Foster", "discussed",
                                                                            "The Long Orchard")]),
        ("Farah Tran mentioned riverside park", [fact("Farah Tran", "discussed", "riverside park")]),
    ]

    def facts(self, s, g, q):
        if g["b"]:
            return [fact(s, "discussed", C.book(g["b"]), q)]
        if g.get("asp"):
            q = C.add(q, "aspect:" + g["asp"].lower())
        return [fact(s, "discussed", C.thing(g["o"]), q)]


class Attends(FactRule, Rule):
    name = "attends"
    solves = ("membership of a group: 'attends the <group>' with time variants ('only in the past', 'used to "
              "attend', 'previously/formerly attended', 'no longer attends', 'used to be a member of', 'but no "
              "longer does') and frequency ('every week', 'regularly')")
    added_by = "learning"
    phrases = [r"(?P<v>attends|attend|attended|attending|is a member of|am a member of|was a member of|"
               r"be a member of|joined|joins|goes to) the (?P<o>%s)" % C.GROUP]
    examples = [
        ("Samir Ito attends the history group.", [fact("Samir Ito", "attends", "history group")]),
        ("T. Patel attends the walking group only in the past.",
         [fact("T. Patel", "attends", "walking group", ["time:past"])]),
        ("R. Avery attends the garden circle, usually on Saturdays.",
         [fact("R. Avery", "attends", "garden circle", ["freq:regular"])]),
        ("Ben Ito attends the chess club only in the past, and he no longer participates in their weekly meetings.",
         [fact("Ben Ito", "attends", "chess club", ["time:past"])]),
        ("D. Chen used to attend the history group in the past.",
         [fact("D. Chen", "attends", "history group", ["time:past"])]),
        ("J. Jones used to attend the walking group, but no longer does.",
         [fact("J. Jones", "attends", "walking group", ["time:past"])]),
        ("Elena Ito attends the chess club every week.",
         [fact("Elena Ito", "attends", "chess club", ["freq:regular"])]),
        ("Ben Laurent previously attended the chess club.",
         [fact("Ben Laurent", "attends", "chess club", ["time:past"])]),
    ]

    def facts(self, s, g, q):
        v = g["v"].lower()
        if v in ("attended", "was a member of"):
            q = add(q, "time:past")
        return [fact(s, "attends", C.thing(g["o"]), [x for x in q if x != "neg" or "time:past" not in q])]


class Visited(FactRule, Rule):
    name = "visited"
    solves = ("'<person> visited the <place>' with its time ('some time ago', 'in the past', 'previously', "
              "'recently', 'last weekend'); also 'went to the <place>' and the bare forms after 'I observed' "
              "('visit', 'visiting')")
    added_by = "learning"
    phrases = [r"(?:visited|visits|visit|visiting|went to) the (?P<o>%s)" % C.PLACE]
    examples = [
        ("E. Patel visited the market some time ago.",
         [fact("E. Patel", "visited", "market", ["time:some time ago"])]),
        ("Kofi Silva visited the market.", [fact("Kofi Silva", "visited", "market")]),
        ("D. Ito visited the library, a stop that was made recently.",
         [fact("D. Ito", "visited", "library", ["time:recently"])]),
        ("O. Avery visited the museum some time ago, a habit he no longer keeps.",
         [fact("O. Avery", "visited", "museum", ["time:some time ago", "time:past"])]),
        ("Omar Diaz visited the sports hall, and it was a notable visit.",
         [fact("Omar Diaz", "visited", "sports hall")]),
        ("I observed Nadia Reed visit the library some time ago",
         [fact("Nadia Reed", "visited", "library", ["evidence:narrator", "time:some time ago"])]),
    ]

    def facts(self, s, g, q):
        return [fact(s, "visited", C.thing(g["o"]), q)]


class HelpedWith(FactRule, Rule):
    name = "helped_with"
    solves = ("'<person> helped with <task> at the <place>' (task: setup, cleanup, registration; also 'assisted "
              "with', 'helping with'), and the place-first forms 'At the <place>, <person> helped with <task>' and "
              "'I was at the <place> when <person> helped with <task>'")
    added_by = "learning"
    allow_context = True
    phrases = [r"(?:helped|helps|help|helping|assisted|assists) with (?P<t>[a-z]+) at the (?P<o>%s)" % C.PLACE,
               r"(?:helped|helps|help|helping|assisted|assists) with (?P<t>setup|cleanup|registration)"]
    examples = [
        ("F. Patel helped with registration at the sports hall.",
         [fact("F. Patel", "helped_with", "registration", ["at:sports hall"])]),
        ("Nadia Patel helped with setup at the market, ensuring everything was ready for the opening.",
         [fact("Nadia Patel", "helped_with", "setup", ["at:market"])]),
        ("At the riverside park, a. gupta helped with registration.",
         [fact("A. Gupta", "helped_with", "registration", ["at:riverside park"])]),
    ]

    def facts(self, s, g, q):
        place = g.get("o") or g.get("place")
        if not place:
            return None
        return [fact(s, "helped_with", g["t"].lower(), add(["at:" + C.thing(place)], *q))]


class HelpedWhenThere(Rule):
    name = "helped_when_there"
    solves = ("'I was at the <place> when <person> helped with <task>' and 'I was at the <place> for a <task> when "
              "<person> helped': the narrator saw a person help at a place")
    added_by = "learning"
    examples = [("I was at the riverside park when O. Foster helped with registration.",
                 [fact("O. Foster", "helped_with", "registration", ["at:riverside park", "evidence:narrator"])]),
                ("I was at the library for a cleanup when Kofi Mensah helped.",
                 [fact("Kofi Mensah", "helped_with", "cleanup", ["at:library", "evidence:narrator"])])]

    def parse(self, clause):
        import re
        m = re.fullmatch(r"I was at the (?P<o>%s) when (?P<s>%s) (?:helped|was helping|assisted) with "
                         r"(?P<t>[a-z]+)(?P<tail>.*?)[.!?]?" % (C.PLACE, C.NAME), clause.strip(), re.I)
        if not m:
            m = re.fullmatch(r"I was at the (?P<o>%s) for (?:a|the) (?P<t>setup|cleanup|registration) when (?P<s>%s) "
                             r"(?:helped|was helping|assisted)(?P<tail>.*?)[.!?]?" % (C.PLACE, C.NAME), clause.strip(),
                             re.I)
        if not m or not C.is_name(m.group("s")):
            return None
        tq = C.tail_quals(m.group("tail"))
        if tq is None:
            return None
        return [fact(C.person(m.group("s")), "helped_with", m.group("t").lower(),
                     add(["at:" + C.thing(m.group("o")), "evidence:narrator"], *tq))]


class Volunteered(FactRule, Rule):
    name = "volunteered"
    solves = ("'<person> volunteered at <event> during this-year/last-year' (event ids 'event-P-139-0' and "
              "'old-event-P-075'); the year can also open the sentence ('During this-year, ...')")
    added_by = "learning"
    phrases = [r"(?:volunteered|volunteers|volunteer|helped out) at (?P<o>(?:old-)?event-[A-Za-z]-?[\w-]+)"
               r"(?: during (?P<y>this-year|last-year|this year|last year))?"]
    examples = [
        ("S. Mensah volunteered at event-P-139-0 during this-year.",
         [fact("S. Mensah", "volunteered_at", "event-P-139-0", ["time:this-year"])]),
        ("Omar Bennett volunteered at old-event-P-075 during last-year.",
         [fact("Omar Bennett", "volunteered_at", "old-event-P-075", ["time:last-year"])]),
        ("During this-year, I. Usman volunteered at event-P-069-0.",
         [fact("I. Usman", "volunteered_at", "event-P-069-0", ["time:this-year"])]),
    ]

    def facts(self, s, g, q):
        ev = g["o"]
        ev = ev[:ev.lower().index("event-") + 6].lower() + ev[ev.lower().index("event-") + 6:].upper()
        y = ("time:" + g["y"].lower().replace(" ", "-")) if g["y"] else None
        return [fact(s, "volunteered_at", ev, add([y] if y else [], *q))]


class TookPartInClass(FactRule, Rule):
    name = "took_part_in_class"
    solves = ("'<person> took part in <subject> class as the <role> this year' (role: teacher, student, observer, "
              "organizer): who taught, learned, watched or organised a class")
    added_by = "learning"
    phrases = [r"(?:took|takes|take) part in (?:a |the )?(?P<c>[a-z]+(?: [a-z]+)?) class as (?:the |a |an )?"
               r"(?P<r>teacher|student|observer|organizer|organiser|assistant|instructor|[a-z]+)"]
    examples = [
        ("Farah Bennett took part in language class as the teacher this year.",
         [fact("Farah Bennett", "took_part_in_class", "language", ["role:teacher", "time:this-year"])]),
        ("I took part in pottery class as the student this year",
         [fact("I", "took_part_in_class", "pottery", ["role:student", "time:this-year"])]),
    ]

    def facts(self, s, g, q):
        return [fact(s, "took_part_in_class", g["c"].lower(), add(["role:" + g["r"].lower()], *q))]


C.register(HelpedWhenThere)
