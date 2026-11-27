import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from gram import Splitter  # noqa: E402


class NoteSplitter(Splitter):
    name = "note_splitter"
    solves = ("cuts a passage line into clauses: sentences (a quotation with its speaker stays one clause), then "
              "connectors (', and', ', but', ', while', ', whereas', '; ', list commas, bare 'and') wherever a new "
              "clause with its own subject follows; drops pure discourse openers ('In a separate update,', "
              "'Elsewhere in the note,', 'The same account also says that' ...) that carry no fact")
    added_by = "learning"
    droppable = common.DROPPABLE
    examples = [
        ("F. Avery discussed history group, and K. Patel owns a camera.",
         ["F. Avery discussed history group", "K. Patel owns a camera."]),
        ("Leah Avery attends the chess club. In a separate update, elena Jones discussed Atlas of Clouds.",
         ["Leah Avery attends the chess club.", "elena Jones discussed Atlas of Clouds."]),
        ("S. Khan attends the garden circle, though only in the past. G. Gupta used to attend the walking group, "
         "though he no longer does.",
         ["S. Khan attends the garden circle, though only in the past.",
          "G. Gupta used to attend the walking group, though he no longer does."]),
        ('J. Foster said, "I recommended Quiet Machines." Quinn Ortiz said, "I discussed radio society, and '
         'T. Reed owns a camera."',
         ['J. Foster said, "I recommended Quiet Machines."',
          'Quinn Ortiz said, "I discussed radio society, and T. Reed owns a camera."']),
        ("K. Silva visited the riverside park, J. Haddad helped with setup at the museum, and D. Gupta attends the "
         "chess club only in the past.",
         ["K. Silva visited the riverside park", "J. Haddad helped with setup at the museum",
          "D. Gupta attends the chess club only in the past."]),
        ("Org 023 is based in St. John's. Nadia Laurent owns a camera.",
         ["Org 023 is based in St. John's.", "Nadia Laurent owns a camera."]),
        ("Rosa Evans is an emergency contact, but not a guardian, for Y118.",
         ["Rosa Evans is an emergency contact, but not a guardian, for Y118."]),
    ]

    def split(self, line):
        return common.split_text(line)
