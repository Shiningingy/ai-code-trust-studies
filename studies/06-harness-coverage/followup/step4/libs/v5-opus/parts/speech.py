"""Reported speech: quotations and 'X said (that) ...'. The quoted text is parsed with the library's other rules;
every fact gets the qualifier reported_by:<speaker>, and 'I'/'me' inside the quote becomes the speaker."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import fact  # noqa: E402
from gram import Rule  # noqa: E402

SAY = (r"(?:said|says|say|explained|explains|added|adds|mentioned|mentions|noted|notes|reported|reports|stated|"
       r"states|remarked|remarks|recalled|recalls|told us|told me|wrote|writes|shared|shares|confirmed|confirms|"
       r"replied|answered|commented|observed|insisted|claimed|claims|admitted|continued|went on|concluded|"
       r"concludes|agreed|agrees|recounted|described|clarified|emphasized|pointed out|joked|laughed|recorded)"
       r"(?: in (?:the|my|our|a|an|his|her|their) [a-z' ]+)?")
PAREN = r"(?:, (?:meanwhile|on the other hand|however|too|also|in turn|for (?:his|her|their) part|in contrast),)?"
SOURCE = r"(?:the|this|our|my) (?:[a-z'-]+ ){0,4}?(?:record|observer|note|notes|log|newsletter|bulletin|transcript|report)"
SPEAKER = r"(?:%s|%s|I|the speaker|the quoted speaker|the narrator|she|he|they|%s)" % (C.NAME, C.YOUTH, SOURCE)
OQ, CQ = "[\"“]", "[\"”]"

def parse_inner(text):
    """Facts of a quoted text, parsed with the library's rules; None if any clause of it is not resolved."""
    return C.parse_text_facts(text, skip=(Speech,))


def ok_speaker(sp):
    return bool(re.fullmatch(r"I|the speaker|the quoted speaker|the narrator|she|he|they|%s|%s" % (C.YOUTH, SOURCE),
                             sp, re.I)) or C.is_name(sp)


def speaker_name(sp):
    if sp == "I" or sp.lower() == "the narrator":
        return "narrator"
    if sp.lower() in ("the speaker", "the quoted speaker", "she", "he", "they"):
        return "the speaker"
    if re.fullmatch(C.YOUTH, sp):
        return C.youth(sp)
    if re.fullmatch(SOURCE, sp, re.I):
        return sp.lower()
    return C.person(sp)


def attribute(facts, sp):
    """Give every fact its speaker: 'I' becomes the speaker (when known), qualifier reported_by:<speaker>."""
    who = speaker_name(sp)
    out = []
    for f in facts:
        f = dict(f, qualifiers=list(f["qualifiers"]))
        if f["subject"] == "I":
            f["subject"] = who if who not in ("narrator", "the speaker") else "I (%s)" % who
        if not any(q.startswith("reported_by:") for q in f["qualifiers"]):
            f["qualifiers"].append("reported_by:" + who)
        out.append(f)
    return out


class Speech(Rule):
    name = "reported_speech"
    solves = ("quotations: '<speaker> said, \"...\"', '<speaker>: \"...\"', '\"...,\" the speaker said', '\"A,\" "
              "<speaker> noted, \"B\"', 'I contrasted this ..., noting, \"...\"', a bare '\"...\"' continuing a "
              "quote; the inside is parsed by the other rules, 'I/me' becomes the speaker and each fact gets "
              "reported_by:<speaker> (the speaker, the narrator, a youth id or a record when not a person)")
    added_by = "learning"
    is_speech = True
    FORMS = [
        # Ben said, "..."   /  For the record, Ben explained, "..."
        re.compile(r"(?:[A-Z][^\"“]*?, )?(?P<sp>%s)%s(?: (?:also|then|later|once|simply))? (?:%s)(?: that)?"
                   r"(?: to me)?[,:]? %s(?P<in>.*?)%s?(?P<post>[^\"“”]*)" % (SPEAKER, PAREN, SAY, OQ, CQ),
                   re.I | re.S),
        # Ben: "..."
        re.compile(r"(?P<sp>%s): %s(?P<in>.*?)%s?(?P<post>[^\"“”]*)" % (SPEAKER, OQ, CQ), re.I | re.S),
        # "A," Ben noted, "B."
        re.compile(r"%s(?P<in>[^\"“”]*?)%s,? (?P<sp>%s) (?:%s),? %s(?P<in2>[^\"“”]*?)%s?(?P<post>)"
                   % (OQ, CQ, SPEAKER, SAY, OQ, CQ), re.I | re.S),
        # "...," the speaker said.
        re.compile(r"%s(?P<in>.*?)%s,? (?P<sp>%s) (?:%s)(?P<post>[^\"“”]*)" % (OQ, CQ, SPEAKER, SAY),
                   re.I | re.S),
        # I contrasted this with the past, noting, "..."
        re.compile(r"(?P<sp>I) [^\"“]*?, (?:noting|adding|saying|explaining|writing),? %s(?P<in>.*?)%s?"
                   r"(?P<post>)" % (OQ, CQ), re.S),
        # "..."  (a quotation going on from the previous sentence)
        re.compile(r"%s(?P<in>.*?)%s?(?P<post>)" % (OQ, CQ), re.I | re.S),
    ]
    examples = [
        ('J. Jones said, "I helped with cleanup at the library, but C. Reed owns a garden tools."',
         [fact("J. Jones", "helped_with", "cleanup", ["at:library", "reported_by:J. Jones"]),
          fact("C. Reed", "owns", "garden tools", ["reported_by:J. Jones"])]),
        ('"Kofi Mensah recommended The Long Orchard," the speaker said.',
         [fact("Kofi Mensah", "recommended", "The Long Orchard", ["reported_by:the speaker"])]),
        ('F. Avery: "I helped with registration at the market."',
         [fact("F. Avery", "helped_with", "registration", ["at:market", "reported_by:F. Avery"])]),
        ('“L. Diaz owns a telescope.”', [fact("L. Diaz", "owns", "telescope", ["reported_by:the speaker"])]),
        ('"F. Patel attends the garden circle," F. Patel noted, "while I. Avery owns a garden tools."',
         [fact("F. Patel", "attends", "garden circle", ["reported_by:F. Patel"]),
          fact("I. Avery", "owns", "garden tools", ["reported_by:F. Patel"])]),
        ('Y023 said, "I currently attend evening_language during the evening."',
         [fact("Y023", "attends_course", "evening_language", ["time:current", "during:evening",
                                                               "reported_by:Y023"])]),
    ]

    def parse(self, clause):
        c = clause.strip()
        if not re.search(r"[\"“”]", c):
            return None
        for rx in self.FORMS:
            m = rx.fullmatch(c)
            if not m:
                continue
            sp = m.groupdict().get("sp") or "the speaker"
            if not ok_speaker(sp):
                continue
            post = m.group("post").strip(" .,")
            if post and not re.fullmatch(r"(?:%s) (?:%s)" % (SPEAKER, SAY), post, re.I):
                continue
            inner = m.group("in").strip().rstrip(",").strip()
            if m.groupdict().get("in2"):
                inner = inner + ", " + m.group("in2").strip()
            inner = re.sub(r"[\"“”]", "", inner).strip()
            facts = parse_inner(inner)
            if facts is None:
                continue
            return attribute(facts, sp)
        return None


C.register(Speech)


class IndirectSpeech(Rule):
    name = "indirect_speech"
    solves = ("indirect reported speech without quotation marks: '<speaker> said (that) he/she owns a camera' (the "
              "pronoun is the speaker), '<speaker> said that <person> ...', 'She also noted that <person> ...'; "
              "facts get reported_by:<speaker> ('the speaker' for a pronoun)")
    added_by = "learning"
    is_speech = True
    RX = re.compile(r"(?P<sp>(?:[Hh]e|[Ss]he|[Tt]hey)(?= )|%s)%s(?: (?:also|then|later|simply))? (?:%s)(?: that)?,? (?P<in>.+)"
                    % (C.NAME, PAREN, SAY), re.S)
    examples = [
        ("Ben Ito said she owns a camera.", [fact("Ben Ito", "owns", "camera", ["reported_by:Ben Ito"])]),
        ("Ben Ito said that Rosa Diaz routinely travels by bus",
         [fact("Rosa Diaz", "travels_by", "bus", ["freq:routinely", "reported_by:Ben Ito"])]),
        ("She also noted that T. Tran enjoys eating mango.",
         [fact("T. Tran", "enjoys_eating", "mango", ["reported_by:the speaker"])]),
        ("Priya Gupta, meanwhile, said she owns a telescope and often checks the night sky from the balcony.",
         [fact("Priya Gupta", "owns", "telescope", ["reported_by:Priya Gupta"])]),
    ]

    def parse(self, clause):
        c = clause.strip()
        if re.search(r"[\"“”]", c):
            return None
        m = self.RX.fullmatch(c)
        if not m:
            return None
        sp = m.group("sp")
        if sp.lower() not in ("he", "she", "they") and not C.is_name(sp):
            return None
        inner = m.group("in")
        pm = re.match(r"(?:he|she|they)\b(?! (?:said|says))", inner, re.I)
        if pm:
            inner = "I" + inner[pm.end():]
        elif not C.starts_clause(inner) and not re.match(r"I\b", inner):
            return None
        facts = parse_inner(inner)
        if facts is None:
            return None
        return attribute(facts, sp)


C.register(IndirectSpeech)
