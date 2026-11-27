import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DROPPABLE, split_line  # noqa: E402

from gram import Splitter  # noqa: E402


class CommunitySplitter(Splitter):
    name = "community_splitter"
    solves = ("cuts a passage line into sentences (not at initials like 'N. Reed' or 'St. John's', not inside a "
              "quotation), then cuts each sentence at commas/semicolons/'and'/'but'/'while'/'whereas' only where a new "
              "'<person> <verb>' clause starts, so trailing remarks such as ', but no longer does' stay with their "
              "clause and a quotation stays whole for the quoted_speech rule")
    added_by = "learning"
    droppable = DROPPABLE
    examples = [
        ("Leah Avery attends the chess club. In a separate update, elena Jones discussed Atlas of Clouds.",
         ["Leah Avery attends the chess club.", "In a separate update, elena Jones discussed Atlas of Clouds."]),
        ("Kofi Laurent recommended Atlas of Clouds, but Farah Reed used the subway once. B. Khan owns a sewing kit.",
         ["Kofi Laurent recommended Atlas of Clouds", "Farah Reed used the subway once.", "B. Khan owns a sewing kit."]),
        ("J. Haddad used to attend the walking group, but no longer does.",
         ["J. Haddad used to attend the walking group, but no longer does."]),
        ('Ben Ito said, "I discussed market. I own a camera." N. Reed owns a camera, and it was new.',
         ['Ben Ito said, "I discussed market. I own a camera."', "N. Reed owns a camera, and it was new."]),
        ("Org 023 is based in St. John's. Nadia Patel helped with setup at the market, ensuring everything was ready.",
         ["Org 023 is based in St. John's.",
          "Nadia Patel helped with setup at the market, ensuring everything was ready."]),
    ]

    def split(self, line):
        return split_line(line)
