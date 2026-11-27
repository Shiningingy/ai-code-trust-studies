"""Group membership, volunteering at events, and taking part in classes."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OBJ, SUBJ, TemplateRule, obj_norm  # noqa: E402

_YEAR = {"this-year": "time=this_year", "this year": "time=this_year", "last-year": "time=last_year",
         "last year": "time=last_year", "next year": "time=next_year", "next-year": "time=next_year"}


class AttendsGroup(TemplateRule):
    name = "attends_group"
    solves = ("membership clauses: '<person> attends the <group>' / 'is a member of the <group>' (current) and the "
              "past forms 'attends the <group> only in the past', 'used to attend the <group> [in the past]', "
              "'previously attended', 'attended the <group> in the past', 'used to be a member of' -> status=former")
    added_by = "learning"
    cores = [
        SUBJ + r" (?P<now>attends|attend|is attending|am attending|still attends|is a member of|am a member of|"
               r"is a regular member of) the " + OBJ +
        r"(?P<past> only in the past| in the past| previously| formerly)?",
        SUBJ + r" (?:used to attend|previously attended|formerly attended|once attended|attended|has attended|"
               r"had attended|stopped attending|no longer attends|no longer attend|used to be a member of|"
               r"used to be a regular member of|was a member of|was once a member of|is no longer a member of|"
               r"am no longer a member of) the " + OBJ +
        r"(?: only in the past| in the past| previously| before)?",
    ]
    examples = [
        ("G. Evans attends the chess club.", [{"subject": "G. Evans", "relation": "attends", "object": "chess club",
                                               "qualifiers": []}]),
        ("T. Patel attends the walking group only in the past.",
         [{"subject": "T. Patel", "relation": "attends", "object": "walking group", "qualifiers": ["status=former"]}]),
        ("J. Haddad used to attend the walking group, but no longer does.",
         [{"subject": "J. Haddad", "relation": "attends", "object": "walking group",
           "qualifiers": ["status=former", "remark=but no longer does"]}]),
        ("Leah Avery attends the radio society on Fridays.",
         [{"subject": "Leah Avery", "relation": "attends", "object": "radio society",
           "qualifiers": ["remark=on Fridays", "freq=on fridays"]}]),
    ]

    def make(self, g):
        former = not g.get("now") or bool(g.get("past"))
        return [("attends", obj_norm(g["obj"]), ["status=former"] if former else [])]


class Volunteered(TemplateRule):
    name = "volunteered"
    solves = ("'<person> volunteered at <event-id> during this-year|last-year': relation volunteered, object the "
              "event id, qualifier time=this_year / time=last_year")
    added_by = "learning"
    cores = [SUBJ + r" (?:volunteered|volunteer|volunteers|has volunteered|have volunteered) at (?:the )?"
                    r"(?P<obj>[\w-]*event[\w-]*)(?: (?:during|in) (?P<year>this-year|last-year|this year|last year|"
                    r"next year|next-year))?"]
    examples = [
        ("Ben Ito volunteered at event-P-114-0 during this-year.",
         [{"subject": "Ben Ito", "relation": "volunteered", "object": "event-P-114-0",
           "qualifiers": ["time=this_year"]}]),
        ("K. Khan volunteered at old-event-P-030 during last-year.",
         [{"subject": "K. Khan", "relation": "volunteered", "object": "old-event-P-030",
           "qualifiers": ["time=last_year"]}]),
    ]

    def make(self, g):
        obj = re.sub(r"(?i)\bp-", "P-", g["obj"])
        return [("volunteered", obj, [_YEAR[g["year"].lower()]] if g["year"] else [])]


class TookPartClass(TemplateRule):
    name = "took_part_class"
    solves = ("'<person> took part in <x> class as the <role> this year': relation took_part_in, object '<x> class', "
              "qualifiers role=<teacher|student|observer|organizer> and the year; '<person> taught <x> class' -> role=teacher")
    added_by = "learning"
    cores = [SUBJ + r" (?:took part in|takes part in|take part in|participated in|joined|attended) (?:the |a )?"
                    r"(?P<obj>[\w-]+(?: [\w-]+)? class) as (?:the |a |an )?(?P<role>[a-z]+)"
                    r"(?: (?P<year>this year|last year|this-year|last-year))?",
             SUBJ + r" (?P<taught>taught|teaches|teach|led|leads|instructed|instructs|ran|runs) (?:the |a )?"
                    r"(?P<obj>[\w-]+(?: [\w-]+)? class)(?: (?P<year>this year|last year|this-year|last-year))?"]
    examples = [
        ("Ben Ito took part in repair class as the teacher this year.",
         [{"subject": "Ben Ito", "relation": "took_part_in", "object": "repair class",
           "qualifiers": ["role=teacher", "time=this_year"]}]),
    ]

    def make(self, g):
        q = ["role=" + (g["role"].lower() if g.get("role") else "teacher")]
        if g["year"]:
            q.append(_YEAR[g["year"].lower()])
        return [("took_part_in", obj_norm(g["obj"]), q)]
