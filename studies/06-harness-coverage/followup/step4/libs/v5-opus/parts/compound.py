"""Clauses that contain other clauses: relative clauses about a second person ('..., in contrast to Farah Patel,
who visited ...'), reported asides ('..., noting that ...'), contrasts ('..., which is different from how ...'),
and the narrator doing something with a person ('I visited the museum with A. Foster'). Each inner clause is parsed
with the library's other rules."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import fact  # noqa: E402
from gram import Rule  # noqa: E402

N = C.NAME
SAY = r"(?:noted|mentioned|said|explained|added|reported|stated|observed|confirmed)"
# words between a clause and the person a relative clause is about
BRIDGE = (r"(?:which (?:is|was) (?:a (?:bit |nice |clear |sharp )?)?(?:contrast|different|in contrast)(?: to| from| with)?|"
          r"which contrasts with|which contrasted with|in contrast to|unlike|where the conversation turned to|"
          r"as did|along with|together with|with|like|and)")
CONTRAST = (r"(?:which|this|that|it) (?:is|was) (?:a bit |quite |very |rather |clearly )?(?:different from|in contrast "
            r"to|a contrast to|unlike)(?: how| the fact that| what| when)?")


def _rest_ok(text):
    """Text after a relative clause that adds no fact ('mentioned it during our chat')."""
    return not C.slot_in(text) and C.tail_quals(text) is not None


class RelativeWho(Rule):
    name = "relative_who"
    solves = ("a clause carrying a relative clause about a person: '<clause> <bridge> <person>, who <verb phrase>' "
              "(bridges: 'in contrast to', 'which contrasts with', 'which is a nice contrast to', 'with', 'where the "
              "conversation turned to') and '<person>, who <verb phrase>, noted that <clause> and that <clause>'; "
              "every clause is parsed by the other rules (what the person said gets reported_by)")
    added_by = "learning"
    RX_MAIN = re.compile(r"(?P<main>.+?),? (?:%s) (?P<n>%s|%s), who (?P<vp>.+)" % (BRIDGE, N, C.YOUTH), re.S)
    RX_LEAD = re.compile(r"(?:(?:That|This|It) (?:is|was) (?:different from|in contrast to|unlike) )?(?P<n>%s), who "
                         r"(?P<vp>[^,]+?)(?:, (?P<rest>.+))?" % N, re.S)
    examples = [
        ("Talia Patel discussed library matters with R. Bennett, who recommended The Long Orchard.",
         [fact("Talia Patel", "discussed", "library", ["aspect:matters"]),
          fact("R. Bennett", "recommended", "The Long Orchard")]),
        ("Ben Ito, who works for Org 018, noted that Isaac Reed visited the sports hall and that Talia Novak attends "
         "the chess club.",
         [fact("Ben Ito", "works_for", "Organization 018"),
          fact("Isaac Reed", "visited", "sports hall", ["reported_by:Ben Ito"]),
          fact("Talia Novak", "attends", "chess club", ["reported_by:Ben Ito"])]),
        ("Amina Evans, who currently works for Organization 018, mentioned it during our chat.",
         [fact("Amina Evans", "works_for", "Organization 018", ["time:current"])]),
        ("That is different from Quinn Tran, who visited the market.", [fact("Quinn Tran", "visited", "market")]),
    ]

    def parse(self, clause):
        c = clause.strip().rstrip(".!?").strip()
        m = self.RX_LEAD.fullmatch(c)
        if m and C.is_name(m.group("n")):
            first = C.parse_clause("%s %s" % (m.group("n"), m.group("vp")), skip=(RelativeWho,))
            if first is not None:
                rest = (m.group("rest") or "").strip()
                if not rest:
                    return first
                sm = re.fullmatch(r"(?:and )?%s that (?P<sub>.+)" % SAY, rest)
                if sm:
                    subs = [C.parse_clause(x, skip=(RelativeWho,))
                            for x in re.split(r",? and that ", sm.group("sub"))]
                    if all(s is not None for s in subs):
                        who = C.person(m.group("n"))
                        return first + [dict(f, qualifiers=C.add(f["qualifiers"], "reported_by:" + who))
                                        for s in subs for f in s]
                elif _rest_ok(rest):
                    return first
        m = self.RX_MAIN.fullmatch(c)
        if m and (C.is_name(m.group("n")) or re.fullmatch(C.YOUTH, m.group("n"))):
            main = C.parse_clause(m.group("main"), skip=(RelativeWho,))
            rel = C.parse_clause("%s %s" % (m.group("n"), m.group("vp")), skip=(RelativeWho,))
            if main is not None and rel is not None:
                return main + rel
        return None


C.register(RelativeWho)


class AsideThat(Rule):
    name = "aside_that"
    solves = ("a clause followed by what its subject said or what it contrasts with: '<clause>, noting/explaining/"
              "adding that <clause>' (the second clause gets reported_by:<subject>) and '<clause>, which is "
              "different from how/the fact that <clause>' (both are facts)")
    added_by = "learning"
    RX_SAY = re.compile(r"(?P<main>.+?), (?:noting|explaining|adding|saying|mentioning|observing|remarking) that "
                        r"(?P<sub>.+)", re.S)
    RX_CON = re.compile(r"(?P<main>.+?), %s (?P<sub>.+)" % CONTRAST, re.S)
    examples = [
        ("Mateo Haddad discussed walking group, noting that A. Evans attends the walking group only in the past.",
         [fact("Mateo Haddad", "discussed", "walking group"),
          fact("A. Evans", "attends", "walking group", ["time:past", "reported_by:Mateo Haddad"])]),
        ("Quinn Reed owns a guitar, which is different from how Kofi Patel discussed Copper Harbor.",
         [fact("Quinn Reed", "owns", "guitar"), fact("Kofi Patel", "discussed", "Copper Harbor")]),
    ]

    def parse(self, clause):
        c = clause.strip().rstrip(".!?").strip()
        for rx, reported in ((self.RX_SAY, True), (self.RX_CON, False)):
            m = rx.fullmatch(c)
            if not m or not C.starts_clause(m.group("sub")):
                continue
            main = C.parse_clause(m.group("main"), skip=(AsideThat,))
            sub = C.parse_clause(m.group("sub"), skip=(AsideThat,))
            if main is None or sub is None or not main:
                continue
            if reported:
                who = main[0]["subject"]
                sub = [dict(f, qualifiers=C.add(f["qualifiers"], "reported_by:" + who)) for f in sub]
            return main + sub
        return None


C.register(AsideThat)


class ObjectRelative(Rule):
    name = "object_relative"
    solves = ("'<clause about a book or place>, which <person> recommended/discussed/suggested': the second person "
              "did the same thing to that object")
    added_by = "learning"
    RX = re.compile(r"(?P<main>.+?), which (?P<n>%s) (?P<v>recommended|discussed|suggested|mentioned|visited)" % N)
    examples = [("Carla Tran discussed Atlas of Clouds, which L. Evans recommended.",
                 [fact("Carla Tran", "discussed", "Atlas of Clouds"), fact("L. Evans", "recommended",
                                                                           "Atlas of Clouds")])]

    def parse(self, clause):
        c = clause.strip().rstrip(".!?").strip()
        m = self.RX.fullmatch(c)
        if not m or not C.is_name(m.group("n")):
            return None
        main = C.parse_clause(m.group("main"), skip=(ObjectRelative,))
        if not main or not main[0]["object"]:
            return None
        o = main[0]["object"]
        art = "the " if C.thing(o) in C.PLACES else ""
        rel = C.parse_clause("%s %s %s%s" % (m.group("n"), m.group("v"), art, o), skip=(ObjectRelative,))
        if rel is None:
            return None
        return main + rel


C.register(ObjectRelative)


class WithNarrator(Rule):
    name = "with_narrator"
    solves = ("'I <verb phrase> with <person>' (the narrator did something together with a person, e.g. 'I visited "
              "the museum with A. Foster'): the person did it too (qualifier with:narrator)")
    added_by = "learning"
    RX = re.compile(r"I (?P<vp>(?:visited|discussed|attended|helped with|recommended|went to)[^,]*?) with "
                    r"(?P<n>%s)(?P<tail>.*)" % N, re.S)
    examples = [("I visited the museum with A. Foster, and we spent a while looking at the exhibits.",
                 [fact("A. Foster", "visited", "museum", ["with:narrator"])])]

    def parse(self, clause):
        c = clause.strip().rstrip(".!?").strip()
        m = self.RX.fullmatch(c)
        if not m or not C.is_name(m.group("n")) or C.slot_in(m.group("tail")):
            return None
        tq = C.tail_quals(m.group("tail"))
        if tq is None:
            return None
        f = C.parse_clause("%s %s" % (m.group("n"), m.group("vp")), skip=(WithNarrator,))
        if f is None:
            return None
        return [dict(x, qualifiers=C.add(x["qualifiers"], *tq) + ["with:narrator"]) for x in f]


C.register(WithNarrator)


class Narration(Rule):
    name = "narration"
    solves = ("ignore-rule for the narrator's own remarks and scene-setting ('I noted a few key points.', 'It was a "
              "quiet afternoon, ...', 'The contrast between the two was evident in the notes.'): they name no "
              "person, id, organisation or youth and no fact rule reads them; a sentence opened by he/she/they plus "
              "a verb is NOT taken (it states a fact about someone named earlier)")
    added_by = "learning"
    ignore = True
    examples = [("I noted a few key points.", []), ("The two entries stood in contrast, one about ongoing "
                                                    "participation and the other about a specific suggestion.", []),
                ("He used to attend the walking group, but only in the past.", None)]

    def parse(self, clause):
        c = clause.strip()
        if re.search(r"[\"“”]", c) or C.slot_in(c):
            return None
        if re.match(r"(?:he|she|they|his|her|their)\b(?: \w+ly)? (?!(?:%s)\b)(?:%s|\w+s\b|\w+ed\b)"
                    % (SAY, C.VERB), c, re.I):
            return None
        if C.parse_clause(c, skip=(Narration,)) is not None:
            return None
        return []


C.register(Narration)


class DifferentFromWhat(Rule):
    name = "different_from_what"
    solves = ("'<clause>, but that is different from what <person> did when she/he <verb phrase>': both the clause "
              "and what the person did are facts")
    added_by = "learning"
    RX = re.compile(r"(?P<main>.+?),? (?:but )?(?:which|this|that|it) (?:is|was) (?:quite |very )?different from what "
                    r"(?P<n>%s) did when (?:he|she|they) (?P<vp>.+)" % N, re.S)
    examples = [("I helped with registration at the market, but that is different from what Elena Patel did when she "
                 "visited the museum some time ago",
                 [fact("I", "helped_with", "registration", ["at:market"]),
                  fact("Elena Patel", "visited", "museum", ["time:some time ago"])])]

    def parse(self, clause):
        m = self.RX.fullmatch(clause.strip().rstrip(".!?").strip())
        if not m or not C.is_name(m.group("n")):
            return None
        main = C.parse_clause(m.group("main"), skip=(DifferentFromWhat,))
        sub = C.parse_clause("%s %s" % (m.group("n"), m.group("vp")), skip=(DifferentFromWhat,))
        if main is None or sub is None:
            return None
        return main + sub


C.register(DifferentFromWhat)


class BareMention(Rule):
    name = "bare_mention"
    solves = ("ignore-rule for the narrator merely remembering or meeting a person, with nothing said about them "
              "('I was filling out a travel reimbursement form when I remembered Samir Jones.'): no fact; what "
              "follows about that person comes in the next sentence")
    added_by = "learning"
    ignore = True
    RX = re.compile(r"(?:I was [a-z' ]+? when )?I (?:remembered|recalled|thought of|met|ran into|saw|bumped into) "
                    r"(?P<n>%s)" % N)
    examples = [("I was filling out a travel reimbursement form when I remembered Samir Jones.", [])]

    def parse(self, clause):
        m = self.RX.fullmatch(clause.strip().rstrip(".!?").strip())
        if not m or not C.is_name(m.group("n")):
            return None
        return []
