"""Ignore-rules: clauses that carry no fact (scene-setting openers, trailing commentary)."""
import re

from gram import Rule

FACT_WORDS = (r"(?<![A-Za-z])(?:owns|recommended|suggested|discussed|visited|attends|attended|helped|"
              r"volunteered|works|worked|travels|traveled|enjoys|enjoyed|dislikes|prefers|chose|chooses|buys|serves|"
              r"skipping|avoids|took part|take part|based in|identifier|roster|guardian|emergency|used to|plans? to use|"
              r"participates|eating|eats|use the|used the)(?![A-Za-z])")
NAME_LIKE = r"[A-Za-z]\. [A-Za-z]{2,}|[A-Z][a-z]+ [A-Z][a-z]+|(?:Org|Organization|Youth) \d|Y\d{3}|P-\d"


FIRST_PERSON_FACT = re.compile(r"I (?:currently |also |genuinely |routinely )?(?:work|own|attend|travel|choose|volunteer|am|enjoy|dislike|buy|"
                               r"serve|prefer|like|plan|took|helped|visited|discussed|recommended|used|use|currently)(?![A-Za-z])")


class Opener(Rule):
    name = "ignore_opener"
    ignore = True
    solves = ("scene-setting sentence that opens a passage ('The appointment note recorded a few pieces of background.', "
              "'This week's community bulletin collected several unrelated updates.'); it names nobody and states nothing")
    added_by = "learning"
    rx = re.compile(r"(?:The|A|This week's|An) [A-Za-z' -]+? (?:recorded|included|covered|moved|touched on|collected|highlights|"
                    r"contained|reviewed|listed|summarized|mentioned|captured|noted) [A-Za-z' ,-]+")
    examples = [("The appointment note recorded a few pieces of background", []),
                ("This week's community bulletin collected several unrelated updates", [])]

    def parse(self, clause):
        c = clause.strip()
        if self.rx.fullmatch(c) and not re.search(NAME_LIKE, c):
            return []
        return None


class Commentary(Rule):
    name = "ignore_commentary"
    ignore = True
    solves = ("trailing commentary after a fact ('which was a key task', 'a book that has been generating interest', "
              "'she is no longer a member'); it repeats or decorates the fact and names no new subject")
    added_by = "learning"
    START = (r"which|a|an|the|so|as|it|its|she|he|they|his|her|their|ensuring|making|adding|bringing|highlighting|showing|"
             r"sharing|guiding|that|only in the past|unlike|noting|and|but|while|whereas|also|though|this|those|these|"
             r"[a-z]+ing|both of which|where|who|when|because|since|during|after|before|with|for|to|in|on|at|by|i|we|my|our")
    rx = re.compile(r"(?:%s)(?![A-Za-z])[^\"]*" % START, re.I)
    examples = [("which was a key task", []), ("a book that has been generating a lot of interest", [])]

    def parse(self, clause):
        c = clause.strip()
        if FIRST_PERSON_FACT.match(c) or c.startswith("I, "):
            return None
        if self.rx.fullmatch(c) and not re.search(FACT_WORDS, c, re.I) and not re.search(r"(?:Org|Organization|Youth) \d|Y\d{3}", c):
            if re.search(r"[A-Za-z]\. [A-Za-z]{2,}|[A-Z][a-z]+ [A-Z][a-z]+", c):
                return None
            return []
        return None


class SpeechTag(Rule):
    name = "ignore_speech_tag"
    ignore = True
    solves = ("bare attribution left over after a quotation ('Talia Novak concluded', 'P. Ito agreed', 'J. Ito said'); the "
              "quoted facts are parsed from their own clauses")
    added_by = "learning"
    rx = re.compile(r"(?:[A-Za-z]\.|[A-Za-z]{2,}) [A-Za-z]{2,} (?:concluded|explained|agreed|said|says|noted|added|continued|"
                    r"replied|answered|finished|stated|remarked)")
    examples = [("Talia Novak concluded", []), ("J. Ito said", [])]

    def parse(self, clause):
        return [] if self.rx.fullmatch(clause.strip()) else None


class LowerFragment(Rule):
    name = "ignore_lowercase_fragment"
    ignore = True
    solves = ("short lower-case leftover fragments of commentary after a fact ('suggestion', 'both are marked as former "
              "participants', 'item as well', 'kept neatly in a drawer'); no name, no fact verb")
    added_by = "learning"
    rx = re.compile(r"[a-z][a-z' ,-]{0,100}")
    examples = [("suggestion", []), ("both are marked as former participants", [])]

    def parse(self, clause):
        c = clause.strip()
        if self.rx.fullmatch(c) and not re.search(FACT_WORDS, c, re.I) and not FIRST_PERSON_FACT.match(c):
            return []
        return None
