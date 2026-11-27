"""Normalizers: form repairs applied to a clause before the rules see it."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gram import Normalizer  # noqa: E402

GARBLED = "“”‘’�"


class StraightQuotes(Normalizer):
    name = "straight_quotes"
    solves = ("curly quotes and the replacement character U+FFFD (how the source garbles curly quotes) become a plain \" "
              "so quote introductions like 'N. Tran said, \"I ...' look the same in every line; no word changes")
    added_by = "learning"
    examples = [
        ("B. Laurent said, “I discussed Atlas of Clouds", "B. Laurent said, \"I discussed Atlas of Clouds"),
        ("N. Tran said, �I helped with setup at the market", "N. Tran said, \"I helped with setup at the market"),
    ]

    def apply(self, clause):
        return "".join('"' if ch in GARBLED and ch not in "‘’" else ch for ch in clause)
