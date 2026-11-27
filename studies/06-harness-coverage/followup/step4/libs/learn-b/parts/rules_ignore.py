import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common_stmt import IgnoreBase as _Ignore  # noqa: E402



class SceneSetter(_Ignore):
    name = "ignore_scene_setter"
    solves = ("opening sentences such as 'The appointment note recorded a few pieces of background.': they describe the "
              "document, not a person, and carry no fact")
    added_by = "learning"
    rx = re.compile(r"(?:the|this|a|an|my|our)\s+[a-z' ]+?\s+(?:recorded|included|collected|touched on|moved (?:across|between)|"
                    r"covered|highlights|captured|shows?|contained|offered|stood|mixed|gathered|summarized|"
                    r"listed|reviewed)\b.*?[.]?", re.I)
    examples = [("The appointment note recorded a few pieces of background.", []),
                ("This week's community bulletin collected several unrelated updates.", [])]


class FillerTail(_Ignore):
    name = "ignore_filler_tail"
    solves = ("free commentary after a fact (', which was a key task', ', a task that took several hours', 'she told me', "
              "', ensuring everything was ready', ', noting its changes'): a clause with no person, id or organization "
              "that starts with a lower-case word (relative word, pronoun, article, participle) other than a bare verb "
              "phrase that would hide a fact")
    added_by = "learning"
    rx = re.compile(r"(?-i:(?!(?:helped|assisted|suggested|attended|went|recommended|owns|visited|attends|discussed|volunteered|works|used|who|and|said|previously|later|had|has|have)\b))"
                    r"(?-i:[a-z]).*|(?:the|a|an|my|our|i|it|we)\b.*", re.I | re.S)
    examples = [("which was a key task.", []), ("a task that took several hours.", []),
                ("ensuring everything was ready for the opening.", []), ("noting its recent renovations.", [])]


class Attribution(_Ignore):
    name = "ignore_attribution"
    solves = "speaker tags after a quotation ('the speaker said.', 'the report noted.', 'she told me.')"
    added_by = "learning"
    rx = re.compile(r"(?:the [a-z ]+?|she|he|they|i)\s+(?:said|says|noted|told me|explained|added|wrote|remarked|stated)"
                    r"(?:\s+[a-z ]+)?[.]?", re.I)
    examples = [("the speaker noted.", [])]
