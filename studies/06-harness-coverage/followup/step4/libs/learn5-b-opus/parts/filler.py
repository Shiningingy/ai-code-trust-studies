"""Clauses that carry no facts."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ORG, PID, YOUTH, strip_end, template_rules  # noqa: E402

from gram import Rule  # noqa: E402

# a name: "Ben Ito", "B. Ito", or any youth / organization / person-id / event mention
_ENTITY = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b|\b[A-Za-z]\. [A-Za-z][a-z]+|\b(?:%s|%s)\b|\b%s\b|event-"
                     % (YOUTH, ORG, PID))
# words of the fact templates; a clause containing one of them is never filler
_FACT_WORDS = re.compile(
    r"\b(?:owns?|owned|camera|guitar|telescope|sewing kit|garden tools|attends?|attended|member of|visited|visits|"
    r"discussed|recommended|suggested|helped|helps|assisted|volunteered|works? for|worked for|(?:night|day) shift|"
    r"bus|tram|subway|train|plane|metro|eating|eats|dairy|cheese|milk|butter|yogurt|guardian|emergency contact|"
    r"roster|identifier|class|based in|avoids?|avoiding|skipping|serves|buys|talked about|spoke about|went to|"
    r"keeps?|mentioned the)\b", re.I)
# "<The|This week's|A> <document kind> <verb> ...": the opening sentence that says what kind of record follows.
_INTRO = re.compile(
    r"(?:the|this|a|an|our|today's|this week's|last week's|this month's)(?: [\w'-]+){0,8}? "
    r"(?:included|includes|recorded|records|covered|covers|moved|moves|touched|touches|collected|collects|"
    r"highlights|highlighted|shows|showed|contains|contained|captured|captures|listed|lists|mentioned|mentions|"
    r"noted|notes|gathered|gathers|summarized|summarizes|summarised|brought|brings|offered|offers|shared|shares|"
    r"described|describes|documented|documents|featured|features|compiled|compiles|spanned|spans|ranged|ranges|"
    r"mixed|mixes|reported|reports|went|goes|jumped|jumps|wandered|wanders|drifted|drifts|has|had|was|is)"
    r"(?: [\w'.,-]+)+", re.I)


def is_narrative_filler(clause):
    """True for a clause that names nobody and uses none of the fact templates' words."""
    s = strip_end(clause.strip())
    if not s or _ENTITY.search(s) or _FACT_WORDS.search(s):
        return False
    return all(r.parse_in(s) is None for r in template_rules())


class PassageIntro(Rule):
    name = "passage_intro"
    solves = ("ignores the opening sentence of a passage that only says what kind of record follows ('The appointment "
              "note recorded a few pieces of background.', 'This week's community bulletin collected several "
              "unrelated updates.'); it names no person, youth, organization or event, so it carries no facts")
    added_by = "learning"
    ignore = True
    examples = [
        ("The appointment note recorded a few pieces of background.", []),
        ("This week's community bulletin collected several unrelated updates.", []),
        ("The volunteer log from the administrative record shows a mix of activities.", []),
        ("The club newsletter included Ben Ito.", None),
    ]

    def parse(self, clause):
        s = strip_end(clause.strip())
        if _ENTITY.search(s) or _FACT_WORDS.search(s) or not _INTRO.fullmatch(s):
            return None
        return []


class NarrativeFiller(Rule):
    name = "narrative_filler"
    solves = ("ignores the writer's narrative glue that names nobody and contains no fact-template words ('I was "
              "sorting through my travel notes when I remembered the conversations from last week.', 'The contrast "
              "between the two entries is clear in the volunteer log.'); a clause with a pronoun subject AND fact "
              "words ('He used to attend the walking group') is NOT taken, it needs its antecedent")
    added_by = "learning"
    ignore = True
    examples = [
        ("I recently traveled and had a few expenses to account for.", []),
        ("It was a quiet afternoon, and the shelves seemed to stretch on forever.", []),
        ("He used to attend the walking group, but only in the past.", None),
        ("The meeting covered Ben Ito.", None),
    ]

    def parse(self, clause):
        return [] if is_narrative_filler(clause) else None
