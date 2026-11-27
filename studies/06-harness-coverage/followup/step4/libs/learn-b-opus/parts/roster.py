import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram import Rule

from common import NAME, decompositions, canon_name, tail_ok

ROSTER = re.compile(
    r"\s*[\"“”]?\s*(?:(?P<self>%s)\s*,?\s*(?:says|said|added|explained|noted)\s*[,:]?\s*[\"“]?\s*)?"
    r"the\s+community\s+roster\s+(?:records|lists|shows|has)\s+(?P<name>me|%s)\s+under\s+"
    r"(?:the\s+)?identifier\s+(?P<pid>[Pp]-\d+)"
    r"(?:\s*,?\s*and\s+also\s+uses\s+the\s+familiar\s+names?\s+(?P<aliases>%s(?:\s*(?:,\s*and|,|and)\s+%s)*))?"
    % (NAME, NAME, NAME, NAME), re.I)


class Roster(Rule):
    name = "roster"
    solves = ("the identity statement that ties a person's full name and familiar names to a person ID: 'The "
              "community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed'; "
              "facts: P-114 has_name 'Nadia Reed', P-114 has_alias 'N. Reed'")
    added_by = "learning"
    examples = [
        ("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed",
         [{"subject": "P-114", "relation": "has_name", "object": "Nadia Reed", "qualifiers": []},
          {"subject": "P-114", "relation": "has_alias", "object": "N. Reed", "qualifiers": []}]),
        ('Priya Ito says, "The community roster records me under identifier P-076 and also uses the familiar names P. Ito',
         [{"subject": "P-076", "relation": "has_name", "object": "Priya Ito", "qualifiers": ["self_reported"]},
          {"subject": "P-076", "relation": "has_alias", "object": "P. Ito", "qualifiers": ["self_reported"]}]),
        ("The appointment note records that the community roster lists f. patel under identifier p-006",
         [{"subject": "P-006", "relation": "has_name", "object": "F. Patel", "qualifiers": ["reported"]}]),
    ]

    def parse(self, clause):
        for rest, quals in decompositions(clause):
            m = ROSTER.match(rest)
            if not m:
                continue
            extra = tail_ok(rest[m.end():], [])
            if extra is None:
                continue
            q = quals + [x for x in extra if x not in quals]
            pid = m["pid"].upper()
            if m["name"].lower() == "me":
                if not m["self"]:
                    continue
                name, q = m["self"], q + ["self_reported"]
            else:
                name = m["name"]
            facts = [{"subject": pid, "relation": "has_name", "object": canon_name(name), "qualifiers": list(q)}]
            if m["aliases"]:
                for a in re.split(r"\s*(?:,\s*and|,|\band)\s+", m["aliases"]):
                    facts.append({"subject": pid, "relation": "has_alias", "object": canon_name(a),
                                  "qualifiers": list(q)})
            return facts
        return None
