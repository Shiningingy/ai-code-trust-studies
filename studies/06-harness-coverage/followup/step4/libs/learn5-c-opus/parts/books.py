"""Recommendations: 'NAME recommended Atlas of Clouds [to the group | as a good read | too]', 'suggested ...'."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang  # noqa: E402
from gram import Rule  # noqa: E402

lang.register("recommendation",
              r"(?:also |later |then )?(?:recommended|recommends|recommend|suggested|suggests) {O}{M}",
              lambda g, q: [("recommended", lang.canon_obj(g["obj"]), q)])


class Recommendation(Rule):
    name = "recommendation"
    solves = ("recommendation clauses ('recommended Quiet Machines to the group', 'suggested The Long Orchard') -> "
              "recommended; the object is the title in lower case without a leading article")
    added_by = "learning"
    examples = [
        ("Hana Ortiz recommended Quiet Machines.", [lang.fact("Hana Ortiz", "recommended", "quiet machines")]),
        ("Rosa Foster recommended Atlas of Clouds to the group",
         [lang.fact("Rosa Foster", "recommended", "atlas of clouds")]),
        ("K. Silva recommended the long orchard.", [lang.fact("K. Silva", "recommended", "long orchard")]),
        ("Farah Patel also recommended Copper Harbor, adding another option to the list.",
         [lang.fact("Farah Patel", "recommended", "copper harbor")]),
        ("Leah Usman recommended Copper Harbor, and she also visited the museum.",
         [lang.fact("Leah Usman", "recommended", "copper harbor"), lang.fact("Leah Usman", "visited", "museum")]),
        ("F. Reed recommended Atlas of Clouds, in contrast to Farah Patel, who visited the sports hall previously",
         [lang.fact("F. Reed", "recommended", "atlas of clouds"),
          lang.fact("Farah Patel", "visited", "sports hall", ["when:previously"])]),
        ("A recent personal note mentioned that N. Ortiz recommended Atlas of Clouds.",
         [lang.fact("N. Ortiz", "recommended", "atlas of clouds", ["source:a recent personal note mentioned"])]),
        ("Kofi Silva noted that Q. Reed recommended Quiet Machines.",
         [lang.fact("Q. Reed", "recommended", "quiet machines", ["reported_by:Kofi Silva"])]),
    ]

    def parse(self, clause):
        return lang.family_parse(clause, {"recommendation"})
