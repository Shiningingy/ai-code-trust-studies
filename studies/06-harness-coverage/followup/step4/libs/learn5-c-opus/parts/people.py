"""Classes, guardianship, youth courses and the community roster.

- 'took part in repair class as the teacher this year' -> took_part_in 'repair class' [role:teacher, when:this year]
- 'is the legal guardian of Youth 043' -> guardian_of Y043
- 'is an emergency contact, but not a guardian, for Y113' -> emergency_contact_for Y113 [neg:guardian]
- 'Youth 151 currently attends evening_language during the evening' -> Y151 attends_course evening_language
- 'The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed'
  -> P-114 has_name 'Nadia Reed', P-114 has_alias 'N. Reed'
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402

lang.register("classes", r"(?:also )?(?:took|takes|take) part in (?:the |a )?(?P<c>[a-z_ ]+? (?:class|course|workshop)) "
                         r"as (?:the |a |an )?(?P<role>[a-z]+){M}",
              lambda g, q: [("took_part_in", g["c"], ["role:" + g["role"]] + q)])
lang.register("classes", r"(?:also )?(?:taught|teaches|teach) (?:the |a )?(?P<c>[a-z_ ]+? (?:class|course|workshop)){M}",
              lambda g, q: [("took_part_in", g["c"], ["role:teacher"] + q)])

lang.register("guardianship", r"(?:is|am)(?: listed as| named as)? (?:the |a )?(?:legal )?guardian (?:of|for) (?P<y>{YOUTH}){M}",
              lambda g, q: [("guardian_of", lang.canon_youth(g["y"]), q)], stative=True)
lang.register("guardianship", r"(?:is|am)(?: listed as| named as)? (?:an |the )?emergency contact,? (?:but )?not (?:a |the )?(?:legal )?guardian,? "
                              r"for (?P<y>{YOUTH}){M}",
              lambda g, q: [("emergency_contact_for", lang.canon_youth(g["y"]), ["neg:guardian"] + q)], stative=True)
lang.register("guardianship", r"(?:is|am)(?: listed as| named as)? (?:an |the )?emergency contact for (?P<y>{YOUTH})"
                              r"(?P<ng>,? but not (?:a |the )?(?:legal )?guardian)?{M}",
              lambda g, q: [("emergency_contact_for", lang.canon_youth(g["y"]), (["neg:guardian"] if g["ng"] else [])
                             + q)], stative=True)

lang.register("youth_course", r"(?P<cur>currently )?(?:attends|attend|is attending|attended) (?P<c>[A-Za-z_]+)"
                              r"(?: during the (?P<w>[a-z]+))?{M}",
              lambda g, q: [("attends_course", g["c"].lower(), (["status:current"] if g["cur"] else [])
                             + (["during:" + g["w"]] if g["w"] else []) + q)], subj=("youth",), stative=True)

_ALIAS = re.compile(lang.NAME)


def _roster(g, q):
    pid = g["pid"].upper()
    out = [(pid, "has_name", "{S}", q)]
    for a in _ALIAS.findall(g["al"]):
        out.append((pid, "has_alias", lang.canon_name(a), q))
    return out


lang.register("roster", r"under identifier (?P<pid>[Pp]-\d+)(?: and also uses the familiar names? "
                        r"(?P<al>{NAME}(?:(?:,| and|, and) {NAME})*))?{M}", _roster, subj=("roster",))


class Classes(Rule):
    name = "classes"
    solves = "class participation clauses -> took_part_in '<x> class' with role:<role> and the time phrase"
    added_by = "learning"
    examples = [
        ("Omar Diaz took part in repair class as the teacher this year.",
         [lang.fact("Omar Diaz", "took_part_in", "repair class", ["role:teacher", "when:this year"])]),
        ("S. Mensah took part in the language class as the observer this year",
         [lang.fact("S. Mensah", "took_part_in", "language class", ["role:observer", "when:this year"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"classes"})


class Guardianship(Rule):
    name = "guardianship"
    solves = ("guardian / emergency-contact clauses -> guardian_of Y### or emergency_contact_for Y### [neg:guardian]; "
              "'Youth 043' and 'Y043' are the same youth")
    added_by = "learning"
    examples = [
        ("Ben Usman is the legal guardian of Youth 18.", [lang.fact("Ben Usman", "guardian_of", "Y018")]),
        ("R. Silva is an emergency contact, but not a guardian, for Y134.",
         [lang.fact("R. Silva", "emergency_contact_for", "Y134", ["neg:guardian"])]),
        ("K. Silva is an emergency contact, not a guardian, for Youth 151",
         [lang.fact("K. Silva", "emergency_contact_for", "Y151", ["neg:guardian"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"guardianship"})


class YouthCourse(Rule):
    name = "youth_course"
    solves = ("course attendance of a youth ('Youth 151 currently attends evening_language during the evening') -> "
              "Y151 attends_course evening_language [status:current, during:evening]")
    added_by = "learning"
    examples = [
        ("Youth 151 currently attends evening_language during the evening, a course that is well attended.",
         [lang.fact("Y151", "attends_course", "evening_language", ["status:current", "during:evening"])]),
        ("Y018 currently attends daytime_first_aid during the day",
         [lang.fact("Y018", "attends_course", "daytime_first_aid", ["status:current", "during:day"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"youth_course"})


class Roster(Rule):
    name = "roster"
    solves = ("community roster entries -> P-### has_name <full name> and P-### has_alias <each familiar name>; "
              "this is how every written form of a person is joined to one person ID")
    added_by = "learning"
    examples = [
        ("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed.",
         [lang.fact("P-114", "has_name", "Nadia Reed"), lang.fact("P-114", "has_alias", "N. Reed")]),
        ("the community roster records Elena Patel under identifier p-006.",
         [lang.fact("P-006", "has_name", "Elena Patel")]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"roster"})
