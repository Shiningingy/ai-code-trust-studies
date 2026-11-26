import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

from gram import Splitter  # noqa: E402


class RecordSplitter(Splitter):
    name = "record_splitter"
    solves = ("cuts a passage line into clauses: sentences (initials like 'N.' and 'St.' are not sentence ends), "
              "a quoted span together with its speaker frame as one unit, a leading discourse opener ('In a separate "
              "update,', 'I observed that') as its own clause, and connectors (', and', ', while', ', but', ';', "
              "list commas) only where a new subject + predicate follows, so trailing remarks stay with their clause")
    added_by = "learning"
    droppable = [r"[,;]?\s*(?:and then|and that|and|while|but|whereas)", r"[,;:]"]
    examples = [
        ("Kofi Laurent recommended Atlas of Clouds, but Farah Reed used the subway once. B. Khan owns a sewing kit.",
         ["Kofi Laurent recommended Atlas of Clouds", "Farah Reed used the subway once.",
          "B. Khan owns a sewing kit."]),
        ("Leah Avery attends the chess club. In a separate update, elena Jones discussed Atlas of Clouds.",
         ["Leah Avery attends the chess club.", "In a separate update,", "elena Jones discussed Atlas of Clouds."]),
        ("J. Haddad helped with setup at the sports hall, a task that took several hours.",
         ["J. Haddad helped with setup at the sports hall, a task that took several hours."]),
        ('Hana Ortiz said, "I visited the sports hall, and Samir Mensah owns a sewing kit." Q. Novak owns a guitar.',
         ['Hana Ortiz said, "I visited the sports hall, and Samir Mensah owns a sewing kit."',
          "Q. Novak owns a guitar."]),
        ("Ben Mensah recommended The Long Orchard, M. Ito discussed Quiet Machines, and I. Chen visited the museum.",
         ["Ben Mensah recommended The Long Orchard", "M. Ito discussed Quiet Machines", "I. Chen visited the museum."]),
        ("Org 013 is based in St. John's, and E. Usman owns a telescope.",
         ["Org 013 is based in St. John's", "E. Usman owns a telescope."]),
    ]

    def split(self, line):
        return C.split_line(line)
