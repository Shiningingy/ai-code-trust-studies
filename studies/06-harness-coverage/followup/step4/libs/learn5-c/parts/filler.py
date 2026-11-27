import re
from gram import Rule


class Filler(Rule):
    name = "filler"
    solves = "scene-setting sentences that carry no fact about a person ('The appointment note recorded a few pieces of background.')"
    added_by = "learning"
    ignore = True
    rx = re.compile(r"(?:This week's community bulletin|The appointment note|The interview|A local profile|The club newsletter|"
                    r"The handoff|The volunteer log|The travel note|The meeting|The event recap|I recently|I handed)\b.*"
                    r"(?:updates|background|topics|life|details|information|expense|personal updates|participants|"
                    r"activities|shift with a few notes|account for)", re.I)
    examples = [("The appointment note recorded a few pieces of background", [])]

    def parse(self, clause):
        return [] if self.rx.fullmatch(clause.strip()) else None


class Narration(Rule):
    name = "narration"
    solves = ("narration with no claim about anyone: a clause that contains none of the grammar's verbs or nouns "
              "('The team chat was lively with various updates', 'I was filling out a form', 'The contrast was noted in the entry')")
    added_by = "learning"
    ignore = True
    cue = re.compile(r"\b(?:used|talked|mentioned|bus|once|enjoy\w*|take|took|plans?|tak\w+ part|own\w*|attend\w*|visit\w*|help\w*|"
                     r"volunteer\w*|discuss\w*|recommend\w*|prefer\w*|like\w*|dislike\w*|avoid\w*|skip\w*|buy\w*|serv\w+|work\w*|travel\w* by|"
                     r"owns?|has|keeps?|attends?|attended|visited|visits?|recommended|suggested|discussed|helped|helping|volunteered|"
                     r"works|worked|travels|travelled|traveled|enjoys|avoids?|guardian|contact|skipping|dislikes|buys|serves|prefers|likes|"
                     r"chose|plans to|took part|roster|based in|member|subway|tram|train|shift|currently|used to|no longer|org|organization|"
                     r"event-p|P-\d+|garden|camera|guitar|telescope|sewing|[a-z]\. [a-z]+ (?:said|noted))\b", re.I)
    examples = [("The team chat was lively with various updates", []),
                ("I was filling out a travel reimbursement form", [])]

    def parse(self, clause):
        c = clause.strip()
        if not c or self.cue.search(c) or re.search(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b|\b[A-Z]\. [A-Z][a-z]+", c):
            return None
        return []


class Fragments(Rule):
    name = "narration_fragments"
    solves = ("claim-free meta sentences: a dangling attribution ('The volunteer log recorded'), a comparison note "
              "('The contrast between the discussions and the visit was noted'), and narrator-only sentences "
              "('I noticed a few interesting details during the volunteer shift')")
    added_by = "learning"
    ignore = True
    rxs = [re.compile(r"(?:The|This|Our|My) [a-z ]+? (?:recorded|noted|shows?|showed|states?|stated|mentioned|reported)(?:,? it was noted)?", re.I),
           re.compile(r"(?:The|This) (?:contrast|difference|comparison|two entries|entries|two)\b.*", re.I),
           re.compile(r"(?:(?:During|While|For|In|At|After)\b[^,]*, )?I\b.*")]
    claim = re.compile(r"\b(?:own\w*|has|keeps?|attend\w*|visit\w*|recommend\w*|discuss\w*|help\w*|volunteered|volunteers|work\w*|enjoy\w*|"
                       r"travel\w*|avoid\w*|skipping|dislike\w*|buy\w*|serve\w*|prefer\w*|like\w*|chose|plans to|took part|"
                       r"guardian|contact|used to|no longer|currently|org|event-|P-\d|Youth|Y\d)\b|[A-Za-z]\. [A-Za-z]|"
                       r"(?-i:\b[A-Z][a-z]+ [A-Z][a-z]+\b)", re.I)
    examples = [("The volunteer log recorded", []), ("The contrast between the two was evident in the notes", []),
                ("I noticed a few interesting details during the volunteer shift", [])]

    def parse(self, clause):
        c = clause.strip()
        if not any(r.fullmatch(c) for r in self.rxs):
            return None
        if self.rxs[2].fullmatch(c) and self.claim.search(c):
            return None
        return []
