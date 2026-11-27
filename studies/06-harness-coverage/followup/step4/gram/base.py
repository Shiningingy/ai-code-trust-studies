"""Parts of a grammar library: Splitter, Normalizer, Rule.

A library is a folder of Python files defining subclasses of these parts, plus a config.json that selects which
parts are used. Every part says what it handles (`solves`), who added it (`added_by`) and carries examples, which
run as tests. See README.md.
"""
import re
from abc import ABC, abstractmethod


class Part(ABC):
    name = ""        # unique within the library
    kind = ""        # set by the subclasses below
    solves = ""      # one sentence: what this part handles, and why it exists
    added_by = ""    # who wrote it (a session label)
    examples = []    # test cases, format depends on the kind


class Splitter(Part):
    """Cuts one line of text into clauses.

    `droppable` lists regexes for connector text the splitter may remove between clauses (for example ", and").
    Every word of the line must end up either in a clause or in a span matching one of these regexes; anything else
    is reported as a dropped-word error. examples: [(line, [clause, ...]), ...]
    """
    kind = "splitter"
    droppable = []

    @abstractmethod
    def split(self, line):
        """Return the list of clauses for this line."""


class Normalizer(Part):
    """Repairs the form of a clause before rules see it: case, punctuation, spacing, small typos.

    It must not change what the clause says. Checked in code on every use: the clause must keep the same number of
    words, and each word must stay the same up to case or be a small typo fix (edit distance at most 2, words of 4+
    letters). Anything bigger is a Rule's job. examples: [(before, after), ...]
    """
    kind = "normalizer"

    @abstractmethod
    def apply(self, clause):
        """Return the repaired clause (or the clause unchanged)."""


class Rule(Part):
    """Parses one kind of clause into facts.

    parse() returns None if the clause is not this rule's kind, otherwise a list of facts. A fact is a dict with at
    least "subject" and "relation" (strings); "object" (string) and "qualifiers" (list of strings, for words such as
    a time or a negation that change the meaning) are optional. A rule must account for the whole clause: every word
    either goes into a fact or is part of the rule's fixed wording. Set `ignore = True` (with a reason in `solves`)
    for clauses that carry no facts; such a rule returns [].
    examples: [(clause, [fact, ...]), ...]
    """
    kind = "rule"
    ignore = False

    @abstractmethod
    def parse(self, clause):
        """Return None (not mine) or a list of facts."""


class PatternRule(Rule):
    """A Rule defined by one regular expression that must match the WHOLE clause (re.fullmatch).

    Subclasses set `pattern` (named groups) and implement build(groups) -> list of facts. `flags` defaults to 0.
    """
    pattern = ""
    flags = 0
    _rx = None

    def parse(self, clause):
        if self._rx is None:
            type(self)._rx = re.compile(self.pattern, self.flags)
        m = self._rx.fullmatch(clause.strip())
        if not m:
            return None
        return self.build({k: (v or "") for k, v in m.groupdict().items()})

    @abstractmethod
    def build(self, groups):
        """Return the list of facts for a matched clause."""


WORD = re.compile(r"[a-z0-9_]+(?:['-][a-z0-9_]+)*")


def words(text):
    return WORD.findall(text.lower())


def edit_distance(a, b, cap=3):
    if abs(len(a) - len(b)) >= cap:
        return cap
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return min(prev[-1], cap)


def same_meaning_form(before, after):
    """True if `after` only repairs the form of `before` (see Normalizer)."""
    a, b = words(before), words(after)
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x != y and not (min(len(x), len(y)) >= 4 and edit_distance(x, y) <= 2):
            return False
    return True


def check_fact(f):
    return (isinstance(f, dict) and isinstance(f.get("subject"), str) and f["subject"].strip()
            and isinstance(f.get("relation"), str) and f["relation"].strip()
            and isinstance(f.get("object", ""), str)
            and isinstance(f.get("qualifiers", []), list) and all(isinstance(q, str) for q in f.get("qualifiers", [])))
