"""Composite constructions: one clause that holds facts about several people. Each rule cuts the clause into simple
clauses and parses them with the clause rules (through speech.parse_inner)."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import F  # noqa: E402
import speech  # noqa: E402

from gram import Rule  # noqa: E402

_ENT = r"(?:%s|%s|%s)" % (C.PERSON, C.YOUTH, C.ORG)


class CompoundSubject(Rule):
    name = "compound_subject"
    solves = ("two people sharing one predicate: 'P. Khan and G. Ito both visited the market previously' -> the "
              "predicate's facts for each person")
    added_by = "learning"
    _rx = re.compile(r"(?P<a>%s) and (?P<b>%s) (?:both )?(?P<rest>.+)" % (C.PERSON, C.PERSON), re.I)
    examples = [("P. Khan and G. Ito both visited the market previously.",
                 [F("P. Khan", "visited", "market", "past"), F("G. Ito", "visited", "market", "past")])]

    def parse(self, clause):
        m = self._rx.fullmatch(clause.strip())
        if not m or not (C.is_person(m.group("a")) and C.is_person(m.group("b"))):
            return None
        out = []
        for who in (m.group("a"), m.group("b")):
            f = speech.parse_inner(C.person(who) + " " + m.group("rest"))
            if not f:
                return None
            out.extend(f)
        return out


class EmbeddedWho(Rule):
    name = "embedded_who_clause"
    solves = ("a clause whose remark names other people with their own predicate: 'F. Reed recommended Atlas of "
              "Clouds, in contrast to Farah Patel, who visited the sports hall previously, and S. Laurent, who helped "
              "...', 'Talia Patel discussed library matters with R. Bennett, who recommended ...', '..., which is "
              "different from how Kofi Patel discussed Copper Harbor' -> the main clause's facts plus one set of facts "
              "per embedded person; the connecting words and the first embedded person are kept as a note on the main facts")
    added_by = "learning"
    _who = re.compile(r"(?P<e>%s), who (?P<p>.+?)(?=,? and %s, who |$)" % (_ENT, _ENT), re.I)
    _how = re.compile(r"(?P<glue>.*?\bhow) (?P<e>%s) (?P<p>.+)" % C.PERSON, re.I)
    examples = [
        ("Talia Patel discussed library matters with R. Bennett, who recommended The Long Orchard.",
         [F("Talia Patel", "discussed", "library", "aspect:matters", "note:with R. Bennett"),
          F("R. Bennett", "recommended", "long orchard")]),
        ("F. Reed recommended Atlas of Clouds, in contrast to Farah Patel, who visited the sports hall previously, "
         "and S. Laurent, who helped with registration at the riverside park.",
         [F("F. Reed", "recommended", "atlas of clouds", "note:in contrast to Farah Patel"),
          F("Farah Patel", "visited", "sports hall", "past"),
          F("S. Laurent", "helped_with", "registration", "at:riverside park")]),
        ("Quinn Reed owns a guitar, which is different from how Kofi Patel discussed Copper Harbor.",
         [F("Quinn Reed", "owns", "guitar", "note:which is different from how Kofi Patel"),
          F("Kofi Patel", "discussed", "copper harbor")]),
    ]

    def parse(self, clause):
        c = C.strip_end(clause.strip())
        for m in re.finditer(r", | with ", c):
            main = speech.parse_inner(c[:m.start()])
            if not main:
                continue
            remark = c[m.start():].lstrip(", ")
            embedded = self._embedded(remark)
            if embedded is None:
                continue
            glue, facts = embedded
            note = "note:" + glue.strip(" ,") if glue.strip(" ,") else ""
            return [F(f["subject"], f["relation"], f["object"], f["qualifiers"], note) for f in main] + facts
        return None

    def _embedded(self, remark):
        """(glue text, facts) if the remark is glue words followed by embedded clauses, else None."""
        hits = list(self._who.finditer(remark))
        if hits:
            glue = remark[:hits[0].end("e")]
            if C.hidden_clause(glue):
                return None
            facts, pos = [], hits[0].start()
            for h in hits:
                if remark[pos:h.start()].strip(" ,") not in ("", "and"):
                    return None
                f = speech.parse_inner(C.entity(h.group("e")) + " " + h.group("p"))
                if not f:
                    return None
                facts.extend(f)
                pos = h.end()
            return glue, facts
        m = self._how.fullmatch(remark)
        if m and not C.hidden_clause(m.group("glue")) and C.is_person(m.group("e")):
            f = speech.parse_inner(C.person(m.group("e")) + " " + m.group("p"))
            if f:
                return m.group("glue") + " " + m.group("e"), f
        return None


class WhichOtherDid(Rule):
    name = "which_other_did"
    solves = ("'Carla Tran discussed Atlas of Clouds, which L. Evans recommended.' -> the main facts plus the other "
              "person's fact about the same object")
    added_by = "learning"
    _rx = re.compile(r"(?P<main>.+?), which (?P<e>%s) (?P<v>recommended|discussed|mentioned|suggested|visited|owns|"
                     r"attends)" % C.PERSON, re.I)
    examples = [("Carla Tran discussed Atlas of Clouds, which L. Evans recommended.",
                 [F("Carla Tran", "discussed", "atlas of clouds"), F("L. Evans", "recommended", "atlas of clouds")])]

    def parse(self, clause):
        m = self._rx.fullmatch(C.strip_end(clause.strip()))
        if not m or not C.is_person(m.group("e")):
            return None
        main = speech.parse_inner(m.group("main"))
        if not main or len(main) != 1:
            return None
        other = speech.parse_inner("%s %s the %s" % (C.person(m.group("e")), m.group("v"), main[0]["object"]))
        if not other:
            return None
        return main + other


_BARE = {"recommend": "recommended", "help": "helped", "discuss": "discussed", "visit": "visited",
         "attend": "attends", "own": "owns", "volunteer": "volunteered", "talk": "talked", "mention": "mentioned",
         "suggest": "suggested", "assist": "assisted"}


class WitnessedDoing(Rule):
    name = "witnessed_doing"
    solves = ("the narrator watching someone act, with a bare verb: 'I watched Talia Reed recommend Quiet Machines to "
              "a new volunteer', 'I saw Gabriel Haddad help with registration at the library' -> that person's fact, "
              "qualifier observed_by:I")
    added_by = "learning"
    _rx = re.compile(r"I (?:also )?(?:watched|saw|noticed|heard|observed) (?P<e>%s) (?P<v>%s)\b(?P<rest>.*)"
                     % (C.PERSON, "|".join(_BARE)), re.I)
    examples = [("I watched Talia Reed recommend Quiet Machines to a new volunteer.",
                 [F("Talia Reed", "recommended", "quiet machines", "note:to a new volunteer", "observed_by:I")]),
                ("I saw Gabriel Haddad help with registration at the library.",
                 [F("Gabriel Haddad", "helped_with", "registration", "at:library", "observed_by:I")])]

    def parse(self, clause):
        m = self._rx.fullmatch(clause.strip())
        if not m or not C.is_person(m.group("e")):
            return None
        f = speech.parse_inner(C.person(m.group("e")) + " " + _BARE[m.group("v").lower()] + m.group("rest"))
        if not f:
            return None
        return [F(x["subject"], x["relation"], x["object"], x["qualifiers"], "observed_by:I") for x in f]


class SceneWhen(Rule):
    name = "scene_when"
    solves = ("'I was at the riverside park when O. Foster helped with registration.' -> the inner clause's facts; a "
              "help without a place gets the scene's place (at:<place>)")
    added_by = "learning"
    _rx = re.compile(r"I was at (?:the )?(?P<place>%s) when (?P<rest>.+)" % "|".join(C.PLACES), re.I)
    examples = [("I was at the riverside park when O. Foster helped with registration.",
                 [F("O. Foster", "helped_with", "registration", "at:riverside park")])]

    def parse(self, clause):
        m = self._rx.fullmatch(clause.strip())
        if not m:
            return None
        f = speech.parse_inner(m.group("rest"))
        if not f:
            return None
        place = "at:" + C.obj(m.group("place"))
        out = []
        for x in f:
            q = list(x["qualifiers"])
            if x["relation"] == "helped_with" and not any(s.startswith("at:") for s in q):
                q.insert(0, place)
            out.append(F(x["subject"], x["relation"], x["object"], q))
        return out


# modifiers written between the subject and the verb, and the qualifier each one adds (put first, before the clause's
# own qualifiers)
_PREMODS = [
    (r"no longer", "past"),
    (r"(?:does not|do not|doesn't|don't|did not|didn't|never)", "negated"),
    (r"(?:will|is going to|are going to|am going to)", "future"),
    (r"(?:usually|often|regularly|sometimes|always|rarely|occasionally|frequently|seldom)", "frequency:{m}"),
    (r"(?:reportedly|apparently|allegedly|supposedly|probably|possibly|may|might|seems to|appears to)", "hedge:{m}"),
]
_PREMOD_RX = re.compile(r"(?P<subj>I(?= )|%s) (?P<be>(?:is|am|are) )?(?P<mod>%s) (?P<rest>.+)"
                        % (C.PERSON, "|".join("(?:%s)" % p for p, _ in _PREMODS)), re.I)
_STOPPED_RX = re.compile(r"(?P<subj>I(?= )|%s) (?:stopped|quit) (?P<verb>[a-z]+)ing (?P<rest>.+)" % C.PERSON, re.I)


class PreVerbModifier(Rule):
    name = "pre_verb_modifier"
    solves = ("a negation, 'no longer', future, frequency or hedge word between subject and verb ('Omar Diaz does not "
              "own a camera', 'T. Ito no longer routinely travels by bus', 'Hana Khan is no longer the legal guardian "
              "of Y003', 'Jia Ito usually attends ...', 'Isaac Tran reportedly owns ...', 'Leah Ito stopped attending "
              "...') -> the plain clause's facts with the qualifier negated / past / future / frequency:<w> / "
              "hedge:<w> first")
    added_by = "learning"
    examples = [
        ("Omar Diaz does not own a camera.", [F("Omar Diaz", "owns", "camera", "negated")]),
        ("T. Ito no longer routinely travels by bus.", [F("T. Ito", "travels_by", "bus", "past", "routinely")]),
        ("Hana Khan is no longer the legal guardian of Y003.", [F("Hana Khan", "guardian_of", "Y003", "past", "legal")]),
        ("Jia Ito usually attends the history group.",
         [F("Jia Ito", "attends", "history group", "frequency:usually")]),
        ("Isaac Tran reportedly owns a telescope.", [F("Isaac Tran", "owns", "telescope", "hedge:reportedly")]),
        ("Leah Ito stopped attending the chess club.", [F("Leah Ito", "attends", "chess club", "past")]),
        ("Rosa Chen will visit the library next week.",
         [F("Rosa Chen", "visited", "library", "future", "time:next week")]),
    ]

    def parse(self, clause):
        c = clause.strip()
        if re.search("[\"“”]", c):
            return None
        m = _PREMOD_RX.fullmatch(c)
        if m and (m.group("subj") == "I" or C.is_person(m.group("subj"))):
            mod = m.group("mod").lower()
            tag = next(t for p, t in _PREMODS if re.fullmatch(p, mod, re.I)).replace("{m}", mod)
            inner = m.group("subj") + " " + ("is " if m.group("be") else "") + m.group("rest")
        else:
            m = _STOPPED_RX.fullmatch(c)
            if not m or not (m.group("subj") == "I" or C.is_person(m.group("subj"))):
                return None
            tag, inner = "past", "%s %s %s" % (m.group("subj"), m.group("verb"), m.group("rest"))
        facts = speech.parse_inner(inner)
        if not facts:
            return None
        return [F(f["subject"], f["relation"], f["object"], tag, f["qualifiers"]) for f in facts]
