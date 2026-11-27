"""Reported speech: quoted spans with their speaker, 'X said he ...', and first-person self-introductions.

These rules are composite: they parse the inner clauses with the clause rules of the other part files, replace the
first person 'I' by the speaker, and add the qualifier said_by:<speaker> to every fact.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import F  # noqa: E402

import activities, family, food, openers, roster, travel, work  # noqa: E402,E401

from gram import Rule  # noqa: E402

_INNER = []
for _m in (activities, family, food, openers, roster, travel, work):
    for _o in vars(_m).values():
        if (isinstance(_o, type) and issubclass(_o, Rule) and _o.__module__ == _m.__name__
                and not getattr(_o, "__abstractmethods__", None)):
            _INNER.append(_o())


def parse_inner(text):
    """Facts for one clause from the clause rules ([] for an ignore-rule), or None if no rule or rules disagree."""
    results = []
    for r in _INNER:
        f = r.parse(text)
        if f is not None:
            results.append(f)
    if not results:
        return None
    first = results[0]
    if any(x != first for x in results[1:]):
        return None
    return first


def parse_text(text):
    """Facts for a run of sentences (split like a line), or None if any clause fails."""
    out = []
    for cl in C.split_line(text):
        f = parse_inner(cl)
        if f is None:
            return None
        out.extend(f)
    return out


def attribute(facts, speaker):
    """Replace subject 'I' by the speaker and mark every fact as said by the speaker."""
    out = []
    for f in facts:
        if f["subject"] == "I":
            if speaker is None:
                return None
            f = dict(f, subject=speaker)
        tag = "said_by:" + (speaker or "unknown")
        out.append(dict(f, qualifiers=list(f["qualifiers"]) + ([tag] if tag not in f["qualifiers"] else [])))
    return out


_VERB = (r"(?:said|says|say|added|adds|explains|explained|continued|continues|mentioned|mentions|noted|notes|"
         r"concluded|stated|states|replied|recalled|remarked|commented|shared|recounted|reported|confirmed|agreed|"
         r"echoed|insisted|observed|wrote|told (?:me|us))")
_SPK = r"(?P<spk>%s|%s|I|the (?:quoted )?speaker|the report|the record|the note|the log|he|she|they)" % (C.PERSON, C.YOUTH)
# before the quote: an optional opener ("During the meeting,"), the speaker, an optional parenthetical, the verb, an
# optional short phrase ("in the volunteer log"); or "I contrasted this with <...>, noting,"
_FRAME_BEFORE = re.compile(r"(?:(?P<op>[A-Z][^\"]*?,) )?(?:%s(?::|%s (?:also )?%s(?: [a-z]+(?: [a-z]+){0,5}?)?[,:]?)|"
                           r"I contrasted this with [a-z ]+, noting,)" % (_SPK, C.PAREN, _VERB), re.I)
_FRAME_AFTER = re.compile(r"%s (?:also )?%s(?: (?:in|to|during|for) [a-z' ]+)?[.!]?" % (_SPK, _VERB), re.I)
# a quote may begin with the connector that joined it to the frame: 'F. Patel noted, "while I. Avery owns ..."'
_LEAD_CONN = re.compile(r"^(?:and|but|while|whereas|also),? ", re.I)


def speaker_of(text):
    """Canonical speaker from a frame's speaker group, or None if it is not a known person/youth/I."""
    if text is None:
        return "I"          # "I contrasted this with ..., noting,"
    if re.fullmatch(C.YOUTH, text):
        return C.youth(text)
    return C.subject(text)


class QuotedSpeech(Rule):
    name = "quoted_speech"
    solves = ("a quoted span with its speaker: 'X said, \"...\"', 'X: \"...\"', '\"...,\" the speaker explains.' The "
              "quote may hold several sentences and other people's facts; each inner clause is parsed by the clause "
              "rules, 'I' becomes the speaker, and every fact gets said_by:<speaker> (said_by:unknown if the speaker "
              "is not named)")
    added_by = "learning"
    examples = [
        ('Hana Ortiz said, "I visited the sports hall, and Samir Mensah owns a sewing kit."',
         [F("Hana Ortiz", "visited", "sports hall", "said_by:Hana Ortiz"),
          F("Samir Mensah", "owns", "sewing kit", "said_by:Hana Ortiz")]),
        ('I. Usman: "I used to routinely travel by subway but no longer do.',
         [F("I. Usman", "travels_by", "subway", "routinely", "past", "said_by:I. Usman")]),
        ('"P. Mensah visited the market, and T. Patel visited the sports hall," the report noted.',
         [F("P. Mensah", "visited", "market", "said_by:unknown"), F("T. Patel", "visited", "sports hall", "said_by:unknown")]),
        ('During the meeting, Farah Chen said, "I volunteered at event-P-146-1 during this year."',
         [F("Farah Chen", "volunteered_at", "event-P-146-1", "period:this-year", "said_by:Farah Chen")]),
        ('"Talia Reed owns a camera," Talia Avery explained.',
         [F("Talia Reed", "owns", "camera", "said_by:Talia Avery")]),
        ('O. Diaz said, "I used to attend the radio society, but I no longer do."',
         [F("O. Diaz", "attends", "radio society", "past", "said_by:O. Diaz")]),
    ]

    def parse(self, clause):
        c = clause.strip()
        qs = re.search(r"[\"“]", c)
        if not qs:
            return None
        q0 = qs.start()
        close = re.search(r"[\"”]", c[q0 + 1:])
        q1 = q0 + 1 + close.start() if close else len(c)
        content = c[q0 + 1:q1]
        after = c[q1 + 1:].strip() if close else ""
        before = c[:q0].strip()
        speaker = None
        if before:
            m = _FRAME_BEFORE.fullmatch(before)
            if not m or (m.group("op") and parse_inner(m.group("op")) != []):
                return None
            speaker = speaker_of(m.group("spk"))
            if after:
                return None
        elif after:
            m = _FRAME_AFTER.fullmatch(after)
            if not m:
                return None
            speaker = speaker_of(m.group("spk"))
        facts = parse_text(_LEAD_CONN.sub("", content.strip()).rstrip(", "))
        if facts is None:
            return None
        return attribute(facts, speaker)
class SaidHeDid(Rule):
    name = "said_pronoun_clause"
    solves = ("indirect self-report: 'X said he volunteered at ...', 'X mentioned that she attends ...', 'X, meanwhile, "
              "said she owns ...' -> the clause after the pronoun is parsed with X as subject, plus said_by:X")
    added_by = "learning"
    _rx = re.compile(r"\"?(?P<subj>%s)(?:, (?:meanwhile|then|later|also),)? (?:also )?%s(?: that)? (?:he|she|they) "
                     r"(?P<rest>.+)" % (C.PERSON, _VERB), re.I)
    examples = [("Omar Diaz said he used the bus once.",
                 [F("Omar Diaz", "travels_by", "bus", "once", "said_by:Omar Diaz")]),
                ("Amina Diaz said she volunteered at old-event-P-061 during last-year.",
                 [F("Amina Diaz", "volunteered_at", "old-event-P-061", "period:last-year", "said_by:Amina Diaz")])]

    def parse(self, clause):
        m = self._rx.fullmatch(clause.strip())
        if not m or not C.is_person(m.group("subj")):
            return None
        s = C.person(m.group("subj"))
        facts = parse_inner(s + " " + m.group("rest"))
        if not facts:
            return None
        return attribute(facts, s)


class SelfIntroduction(Rule):
    name = "self_introduction"
    solves = ("first-person narration with the narrator named: 'I, omar foster, helped with registration at the "
              "library.' -> the clause with the named person as subject, plus said_by:<person>")
    added_by = "learning"
    _rx = re.compile(r"\"?I, (?P<subj>%s), (?P<rest>.+)" % C.PERSON, re.I)
    examples = [("I, omar foster, helped with registration at the library.",
                 [F("Omar Foster", "helped_with", "registration", "at:library", "said_by:Omar Foster")])]

    def parse(self, clause):
        m = self._rx.fullmatch(clause.strip())
        if not m or not C.is_person(m.group("subj")):
            return None
        s = C.person(m.group("subj"))
        facts = parse_inner(s + " " + m.group("rest"))
        if not facts:
            return None
        return attribute(facts, s)
