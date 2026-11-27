"""Quoted speech: 'D. Haddad said, "I helped with setup at the museum. I work the day shift."'"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CONTEXT_RX, OPENER_RX, PERSON, REPORT_VERB, YOUTH, context_quals, name_form,  # noqa: E402
                    split_line, strip_end, template_rules)
from filler import is_narrative_filler  # noqa: E402

from gram import Rule  # noqa: E402

_SPEAKER = r"(?P<src>%s|%s|I|we|he|she|they|the speaker|(?:the|a|an|one|our) [a-z' -]{1,50}?)" % (PERSON, YOUTH)
# an interrupted quotation: '"F. Patel attends the garden circle," F. Patel noted, "while I. Avery owns a camera."'
_RESUME = re.compile(r"[\s,]*%s(?: also| then)? %s(?: [a-z' ]{0,40}?)?,\s*[\"“](?P<more>[^\"“”]*)[\"”]?[\s.]*"
                     % (_SPEAKER, REPORT_VERB), re.I)
_LEAD = re.compile(r"(?:and|but|while|whereas|so|also)\s+(?=\S)", re.I)
# text before the opening quote: 'Ben Ito said,' / 'Carla Tran:' / 'I contrasted this with the past, noting,'
_PRE = [re.compile(r"%s(?: also| then| later| simply)? %s(?: [a-z' ]{0,40}?)?\s*[,:]?" % (_SPEAKER, REPORT_VERB), re.I),
        re.compile(r"(?P<src>%s|%s)\s*:" % (PERSON, YOUTH)),
        re.compile(r"(?P<src>I|we)\b[^\"“”]{0,120}?,? (?:noting|saying|adding|explaining|writing|recalling|"
                   r"quoting)(?: that)?\s*[,:]?", re.I)]
# text after the closing quote: ', the speaker said' / ' Ben Ito explains'
_POST = re.compile(r"[\s,]*%s(?: also| then)? %s(?: [a-z' ]{0,40})?" % (_SPEAKER, REPORT_VERB), re.I)


def _speaker_of(src, quals):
    quals.append("reported")
    if re.fullmatch(PERSON, src) or re.fullmatch(YOUTH, src):
        quals.append("reported_by=" + name_form(src))
        return name_form(src)
    if src.lower() == "i":
        quals.append("reported_by=narrator")
    return None


class QuotedSpeech(Rule):
    name = "quoted_speech"
    solves = ("a quotation with its speaker ('Ben Ito said, \"I own a camera. Rosa Chen discussed library.\"', "
              "'Carla Tran: \"I ...', '\"...,\" the speaker said'): every sentence inside is parsed by the template "
              "rules with qualifiers reported and reported_by=<speaker>, and 'I'/'me' standing for the speaker; the "
              "whole quotation is one clause because the speaker carries across its sentences")
    added_by = "learning"
    examples = [
        ('D. Haddad said, "I helped with setup at the museum. I work the day shift."',
         [{"subject": "D. Haddad", "relation": "helped", "object": "museum",
           "qualifiers": ["task=setup", "reported", "reported_by=D. Haddad"]},
          {"subject": "D. Haddad", "relation": "works_shift", "object": "day",
           "qualifiers": ["reported", "reported_by=D. Haddad"]}]),
        ('Carla Tran: "I helped with setup at the riverside park.',
         [{"subject": "Carla Tran", "relation": "helped", "object": "riverside park",
           "qualifiers": ["task=setup", "reported", "reported_by=Carla Tran"]}]),
        ('"Priya Ito owns a camera," the speaker said.',
         [{"subject": "Priya Ito", "relation": "owns", "object": "camera", "qualifiers": ["reported"]}]),
        ('"F. Patel attends the garden circle," F. Patel noted, "while I. Avery owns a camera."',
         [{"subject": "F. Patel", "relation": "attends", "object": "garden circle",
           "qualifiers": ["reported", "reported_by=F. Patel"]},
          {"subject": "I. Avery", "relation": "owns", "object": "camera",
           "qualifiers": ["reported", "reported_by=F. Patel"]}]),
    ]

    def parse(self, clause):
        s = clause.strip()
        q1 = re.search(r"[\"“”]", s)
        if not q1:
            return None
        pre, rest = s[:q1.start()], s[q1.end():]
        q2 = re.search(r"[\"“”]", rest)
        inner, post = (rest[:q2.start()], rest[q2.end():]) if q2 else (rest, "")
        m = _RESUME.fullmatch(post)
        if m:
            more = _LEAD.sub("", m.group("more").strip(), count=1)
            inner, post = inner.rstrip(" ,") + ". " + more, ", %s said" % m.group("src")
        if re.search(r"[\"“”]", post):
            return None
        quals, speaker = [], None
        pre = pre.strip()
        for _ in range(4):  # openers before the speaker
            m = OPENER_RX.match(pre) or CONTEXT_RX.match(pre)
            if not m or m.end() >= len(pre):
                break
            if "ctx" in m.groupdict():
                quals += context_quals(m.group("ctx"))
            pre = pre[m.end():]
        if pre:
            for rx in _PRE:
                m = rx.fullmatch(pre)
                if m:
                    speaker = _speaker_of(m.group("src"), quals)
                    break
            else:
                return None
            if strip_end(post).strip(" ,"):
                return None
        else:
            p = strip_end(post).strip()
            if p:
                m = _POST.fullmatch(p)
                if not m:
                    return None
                speaker = _speaker_of(m.group("src"), quals)
            else:
                quals.append("reported")
        facts = []
        rules = template_rules()
        for piece in split_line(inner.strip()):
            piece = _LEAD.sub("", piece.strip(), count=1) if _LEAD.match(piece.strip()) else piece
            got = {}
            for r in rules:
                f = r.parse_in(piece, speaker, quals)
                if f is not None:
                    got[json.dumps(f, sort_keys=True)] = f
            if len(got) == 1:
                facts.extend(next(iter(got.values())))
            elif not got and is_narrative_filler(piece):
                continue
            else:
                return None
        return facts or None
