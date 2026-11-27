import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram import Rule

from common import PAST_TAIL, Pred, analyze, clean, slot, v


class Diet(Rule):
    name = "diet"
    solves = ("what a person eats or avoids: 'currently chooses to avoid dairy products' / 'avoids dairy products' "
              "(avoids), 'is temporarily skipping cheese' (temporarily_skipping), 'enjoys eating peach' (enjoys_eating; "
              "'in the past' / 'used to enjoy' / 'enjoyed' give qualifier past), 'dislikes eating milk' "
              "(dislikes_eating), 'buys cheese for other people' (buys_for_others), 'serves mango to other people "
              "but does not eat it' (serves_to_others plus eats with qualifier negated)")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+)?(?:currently\s+|still\s+|now\s+)?(?:%s\s+to\s+avoid|%s)\s+%s" % (v("choose"), v("avoid"),
                                                                                     slot("obj")),
             lambda m: ("avoids", clean(m["obj"]), []), 0),
        Pred(r"(?:is|am|are)\s+(?:currently\s+)?temporarily\s+(?:skipping|avoiding)\s+%s" % slot("obj"),
             lambda m: ("temporarily_skipping", clean(m["obj"]), []), 0),
        Pred(r"(?:also\s+)?(?:simply\s+|really\s+|still\s+)?%s\s+eating\s+%s(?P<past>\s+in the past)?" % (v("enjoy"),
                                                                                              slot("obj")),
             lambda m: ("enjoys_eating", clean(m["obj"]), ["past"] if m["past"] else []), 0),
        Pred(r"(?:used to enjoy|enjoyed|previously enjoyed)\s+eating\s+%s(?:\s+in the past)?%s" % (slot("obj"),
                                                                                                    PAST_TAIL),
             lambda m: ("enjoys_eating", clean(m["obj"]), ["past"]), 0),
        Pred(r"(?:also\s+)?%s\s+eating\s+%s" % (v("dislike"), slot("obj")),
             lambda m: ("dislikes_eating", clean(m["obj"]), []), 0),
        Pred(r"(?:also\s+)?%s\s+%s\s+for\s+other\s+people" % (v("buy"), slot("obj")),
             lambda m: ("buys_for_others", clean(m["obj"]), []), 0),
        Pred(r"(?:also\s+)?%s\s+%s\s+to\s+other\s+people\s+but\s+(?:does|do)\s+not\s+eat\s+it" % (v("serve"),
                                                                                                slot("obj")),
             lambda m: [("serves_to_others", clean(m["obj"]), []), ("eats", clean(m["obj"]), ["negated"])], 0),
    ]
    examples = [
        ("Rosa Chen currently chooses to avoid dairy products, so I made sure not to order anything with milk",
         [{"subject": "Rosa Chen", "relation": "avoids", "object": "dairy products", "qualifiers": []}]),
        ("Q. Mensah is temporarily skipping milk, a small change noted in passing",
         [{"subject": "Q. Mensah", "relation": "temporarily_skipping", "object": "milk", "qualifiers": []}]),
        ("T. Usman used to enjoy eating mango",
         [{"subject": "T. Usman", "relation": "enjoys_eating", "object": "mango", "qualifiers": ["past"]}]),
        ("Omar Chen serves mango to other people but does not eat it",
         [{"subject": "Omar Chen", "relation": "serves_to_others", "object": "mango", "qualifiers": []},
          {"subject": "Omar Chen", "relation": "eats", "object": "mango", "qualifiers": ["negated"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)
