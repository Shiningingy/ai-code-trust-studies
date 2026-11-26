"""Roster (identity) rule, case normalizer, and ignore-rules for clauses without facts."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from gram import Normalizer, PatternRule, Rule
from gcommon import canon_name, fact, fact_shape, MARKER, PERSON, PRED_START, STOP


class Roster(PatternRule):
    name = "roster"
    solves = ("identity: 'The community roster records <Full Name> under identifier P-NNN (and also uses the familiar names <N. Name>)'; "
              "gives has_id and familiar_name facts, the only way to join initial-form mentions to person IDs")
    added_by = "learning"
    flags = re.I
    pattern = (r"[\"]?(?:the )?community roster (?:records|lists) (?P<n>%s) under identifier (?P<id>P-\d+)"
               r"(?: and also uses the familiar names? (?P<f>%s(?:(?:,| and) %s)*))?[.,]?\"?(?:,? the (?:quoted )?speaker (?:said|noted|explained))?[.]?" % (PERSON, PERSON, PERSON))
    examples = [("The community roster records Nadia Reed under identifier P-114 and also uses the familiar names N. Reed.",
                 [{"subject": "Nadia Reed", "relation": "has_id", "object": "P-114", "qualifiers": []},
                  {"subject": "Nadia Reed", "relation": "familiar_name", "object": "N. Reed", "qualifiers": []}])]

    def build(self, g):
        n = canon_name(g["n"])
        out = [fact(n, "has_id", g["id"].upper())]
        for f in re.split(r",| and ", g["f"]) if g["f"] else []:
            if f.strip():
                out.append(fact(n, "familiar_name", canon_name(f.strip())))
        return out


class UsedToVerb(Normalizer):
    name = "used_to_verb"
    solves = "repairs the typo 'used to attends' (a stray third-person -s after 'used to')"
    added_by = "learning"
    examples = [("Elena Novak used to attends the history group in the past.", "Elena Novak used to attend the history group in the past.")]

    def apply(self, clause):
        return re.sub(r"\bused to (attend|visit|own|work|enjoy)s\b", r"used to \1", clause)


class CaseFix(Normalizer):
    name = "name_case"
    solves = "capitalises a lower-case leading 'first last' / 'f. last' name that starts a clause (e.g. 'c. bennett owns ...')"
    added_by = "learning"
    examples = [("c. bennett owns a camera", "C. Bennett owns a camera"),
                ("isaac usman used to attend the radio society", "Isaac Usman used to attend the radio society")]

    def apply(self, clause):
        m = re.match(r'(["]?)([A-Za-z]\.|[A-Za-z]+) ([A-Za-z][A-Za-z\'-]+)(?= %s\b)' % PRED_START, clause)
        if not m or m.group(2) in STOP or m.group(3) in STOP or (m.group(2)[0].isupper() and m.group(3)[0].isupper()):
            return clause
        a, b = m.group(2), m.group(3)
        return clause[:m.start(2)] + a[:1].upper() + a[1:] + " " + b[:1].upper() + b[1:] + clause[m.end():]


class Background(Rule):
    name = "background_sentence"
    solves = ("ignore: scene-setting sentences with no person fact ('The appointment note recorded a few pieces of background.', "
              "'During the shift handoff', 'I handed off the shift with a few notes.'); only taken when the clause has no 'NAME PREDICATE' shape")
    added_by = "learning"
    ignore = True
    examples = [("The appointment note recorded a few pieces of background.", []),
                ("I handed off the shift with a few notes.", []),
                ("During the meeting", [])]

    def parse(self, clause):
        c = clause.strip()
        if not re.match(r"(?:The|A|An|This|Our|My|It|I|During|According|Also|Both|Two|One|There|For|On|At|While|Meeting)\b(?!\.)", c):
            return None
        if fact_shape(c) or MARKER.search(c):
            return None
        if re.match(r'["“]?I (?:also |currently |used |am |own|attend|work|visited|helped|recommended|discussed|volunteered|'
                    r'routinely|plan|like|enjoy|dislike|buy|serve|chose|choose|genuinely|keep|recommend)', c):
            return None     # a first-person statement: its speaker is only known from context, so never ignore it
        return []


class Commentary(Rule):
    name = "commentary_tail"
    solves = ("ignore: trailing commentary cut off a fact clause (', which was a key task', ', a task that took several hours', "
              "', ensuring everything was ready'); carries no fact and no time/negation word")
    added_by = "learning"
    ignore = True
    examples = [("which was a key task.", []), ("ensuring everything was ready for the opening.", []),
                ("a book that has been generating a lot of interest.", [])]

    def parse(self, clause):
        c = clause.strip().strip('"')
        if not re.match(r"[a-z]+\b(?!\.)", c):
            return None
        if fact_shape(c) or MARKER.search(c):
            return None
        return []
