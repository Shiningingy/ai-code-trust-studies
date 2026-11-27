"""Stmt: shared base class for 'SUBJECT predicate' rules (not itself a part)."""
import os
import re
import sys
from abc import abstractmethod

sys.path.insert(0, os.path.dirname(__file__))
from common import NAME, LEAD_NEUTRAL, LEAD_REPORTED, fact, person  # noqa: E402
from gram import Rule  # noqa: E402

ADJ = (r"(?:with|during|in|at|for|after|before|on|as|to|last|every|this|later|nearby|too|regularly|often|today|"
       r"yesterday|again|well|that|which|and also|though|instead|simply|now|only|recently|earlier|more recently)\b[^,;]*|regularly|often|too|nearby|previously|also|recently|earlier|more recently")
STOP = r"(?!(?:the|a|an|then|also|i|it|we|he|she|they|which|who|that|this|there|in|on|at|during|my|our|their|his|her|its)\b(?!\.))"


class Stmt(Rule):
    """Base for rules about 'SUBJECT predicate' clauses.

    The clause is [quote] [lead-in] SUBJECT [said/says + I/he/she] [also] [no longer] PREDICATE [adjunct].
    Subclasses set `pred` (regex, matched after the subject) and implement `facts(subject, m)` which returns
    a list of (relation, object, qualifiers).  Words of the wrapper become qualifiers: "reported" (quoted or
    reported speech), "no longer", and the adjunct text (frequency, time, manner) lower-cased.
    """
    pred = ""
    _rx = None
    registry = []

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        Stmt.registry.append(cls)

    @abstractmethod
    def facts(self, subject, m):
        """Return [(relation, object, qualifiers)]."""

    def parse(self, clause):
        cls = type(self)
        if cls._rx is None:
            cls._rx = re.compile(
                r'^(?P<q1>")?\s*(?:(?P<lead>%s|%s)[,\s]\s*"?){0,2}(?:I,\s+)?%s(?P<subj>%s),?'
                r'(?:(?:\s+(?P<said>said|says|stated|added|mentioned|explained|explains|noted|remarked|wrote(?: in [a-z ]+?)?|shared|continued|concluded|agreed|replied)[,:]?|:)\s+(?:that\s+)?"?(?:I|he|she|they)\s+|\s+)'
                r'(?:also\s+)?(?P<nl>no longer\s+)?(?:%s)(?:\s*,?\s*(?P<adj>%s))?[\s.,"]*$'
                % (LEAD_NEUTRAL, LEAD_REPORTED, STOP, NAME, self.pred, ADJ), re.I)
        m = cls._rx.match(clause.strip())
        if not m:
            return None
        quals = []
        if m.group("q1") or m.group("said") or (m.group("lead") and re.match(LEAD_REPORTED, m.group("lead"), re.I)):
            quals.append("reported")
        if m.group("nl"):
            quals.append("no longer")
        if m.group("adj"):
            adj = re.sub(r"\s+", " ", m.group("adj").strip(' .,"”').lower())
            if re.search(r"\b(?:in the past|no longer|previously|formerly|some time ago|used to)\b", adj):
                quals.append("past")
            quals.append(adj)
        subj = person(m.group("subj"))
        return [fact(subj, rel, obj, quals + list(q)) for rel, obj, q in self.facts(subj, m)]


class IgnoreBase(Rule):
    """Base for ignore rules: the clause must contain no person, id or organization and fully match `rx`."""
    ignore = True
    has_name = re.compile(r"\b(?:%s)\b|\b[A-Za-z]\.\s+[A-Z][a-z]+|\bP-\d+|\bOrg(?:anization)?\s+\d+|\bY(?:outh)?\s*\d{3}\b|event-P|_"
                          % "|".join(__import__("common").FIRST), re.I)

    @property
    @abstractmethod
    def rx(self):
        """compiled regex that must match the whole clause"""

    def parse(self, clause):
        t = clause.strip()
        if self.has_name.search(t):
            return None
        return [] if self.rx.fullmatch(t) else None
