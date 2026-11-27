"""Who is who: the community roster ties a written name to a person ID and lists the person's familiar names."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import PERSON, PID, TemplateRule, name_form  # noqa: E402

_ALIASES = r"(?P<aliases>%s(?:(?:,? and |, ?|; ?| or )%s)*)" % (PERSON, PERSON)


class Roster(TemplateRule):
    name = "roster"
    solves = ("identity clauses 'the community roster records <name> under identifier P-114 [and also uses the "
              "familiar names N. Reed]' (also 'lists', 'records me' in speech): one fact <name> has_id P-114, and one "
              "fact per familiar name with qualifier alias")
    added_by = "learning"
    cores = [r"(?:the )?community roster (?:records|lists|has|shows) (?P<subj>%s|me) under (?:the )?identifier "
             r"(?P<pid>%s)(?: and (?:also )?(?:uses|lists|records) the familiar names? %s)?" % (PERSON, PID, _ALIASES)]
    examples = [
        ("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed.",
         [{"subject": "Nadia Reed", "relation": "has_id", "object": "P-114", "qualifiers": []},
          {"subject": "N. Reed", "relation": "has_id", "object": "P-114", "qualifiers": ["alias"]}]),
        ("The community roster records amina haddad under identifier p-141.",
         [{"subject": "Amina Haddad", "relation": "has_id", "object": "P-141", "qualifiers": []}]),
    ]

    def make(self, g):
        pid = name_form(g["pid"])
        self._aliases = [name_form(a) for a in re.findall(PERSON, g.get("aliases") or "")]
        return [("has_id", pid, [])]

    def parse(self, clause):
        facts = super().parse(clause)
        if facts:
            base = facts[0]
            for a in self._aliases:
                facts.append(dict(base, subject=a, qualifiers=["alias"] + base["qualifiers"]))
        return facts
