import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import NAME, SPEECH, NoFactRule  # noqa: E402

# nameless narrator verbs: remarks about the writing or the reimbursement story, never a profile fact
NARR = (r"(?:noted|remembered|made sure|am submitting|recently|had|handed|noticed|also noted|was|kept|wrote|took|mentioned|"
        r"explained|no longer|confirmed|learned|read|thought|said|stated|filed|found|focus|know|asked|contrasted|plan to read|"
        r"can see|keep it|don't|do not|watched|do)")


class IntroFrame(NoFactRule):
    name = "intro_frame"
    solves = ("ignore: the scene-setting first sentence of a passage ('The appointment note recorded a few pieces of "
              "background.', 'This week's community bulletin collected several unrelated updates.'); it names no one")
    added_by = "learning"
    frames = [r"(?:This week's |The |A |An |Our )[\w' ]{3,70}? (?:collected|recorded|included|moved|touched|covered|captured|"
              r"highlights?|shows?|showed|include|contains?|were|was|offered|gathered|listed|noted|reviewed|required|explained)"
              r"\b[\w' ,-]*\.?"]
    examples = [("The appointment note recorded a few pieces of background.", []),
                ("This week's community bulletin collected several unrelated updates.", [])]

    def describe(self):
        return self.solves


class NarratorComment(NoFactRule):
    name = "narrator_comment"
    solves = ("ignore: nameless narrator remarks about the writing itself ('I noted a few key points.', 'The contrast "
              "between the two was evident in the notes.', 'I no longer go there.') that state no fact")
    added_by = "learning"
    frames = [r"(?:The (?:contrast|two entries|entries|local profile|team chat|volunteer log|quoted speaker)|Both topics|It was|"
              r"Our administrative)\b[\w' ,.-]*",
              r"I %s\b[\w' ,.-]*" % NARR,
              r"(?:During|In|At|On|While) [\w' ]+, I %s\b[\w' ,.-]*" % NARR]
    examples = [("I noted a few key points.", []), ("I no longer do.", [])]

    def describe(self):
        return self.solves


class SpeechAttribution(NoFactRule):
    name = "speech_attribution"
    solves = ("ignore: a bare attribution left over from a quotation ('Talia Avery explained.', 'I said.', 'the speaker "
              "said.'): it names the speaker but states no fact")
    added_by = "learning"
    examples = [("Talia Avery explained.", []), ("I said.", []), ("the speaker said.", [])]

    def describe(self):
        return self.solves

    def parse(self, clause):
        t = clause.strip().strip("\"“”").strip()
        if re.fullmatch(r"(?:%s|I|[Tt]he [\w ]{3,40}?|[Ss]he|[Hh]e) (?:also )?%s(?: in the [\w ]+?)?[.,]?" % (NAME, SPEECH), t):
            return []
        return None


class NarratorStatement(NoFactRule):
    name = "narrator_statement"
    solves = ("ignore: narrator sentences that mention a person only as the thing remembered ('I remembered Samir Jones.') "
              "and state no profile fact")
    added_by = "learning"
    examples = [("I remembered Samir Jones.", [])]

    def describe(self):
        return self.solves

    def parse(self, clause):
        t = clause.strip().strip("\"“”").strip()
        if re.fullmatch(r"(?:I was [\w' ]+ when )?I (?:remembered|watched|asked about|noticed) %s\.?" % NAME, t):
            return []
        return None
