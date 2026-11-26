"""What people eat, avoid and buy."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import FamilyRule  # noqa: E402


class Diet(FamilyRule):
    name = "diet"
    family = "diet"
    solves = ("food statements, each its own relation because they mean different things: 'currently chooses to avoid "
              "dairy products' (avoids + 'currently'), 'is temporarily skipping cheese' (skips + 'temporarily'), "
              "'buys milk for other people' (buys_for_others), 'enjoys eating pear' / 'used to enjoy eating' "
              "(enjoys_eating, 'past'), 'dislikes eating yogurt', 'serves mango to other people but does not eat it' "
              "(serves_to_others + eats 'negated')")
    added_by = "learning"
    examples = [
        ("Nadia Ortiz currently chooses to avoid dairy products",
         [{"subject": "Nadia Ortiz", "relation": "avoids", "object": "dairy products", "qualifiers": ["currently"]}]),
        ("Amina Bennett is temporarily skipping cheese",
         [{"subject": "Amina Bennett", "relation": "skips", "object": "cheese", "qualifiers": ["temporarily"]}]),
        ("E. Laurent buys cheese for other people",
         [{"subject": "E. Laurent", "relation": "buys_for_others", "object": "cheese", "qualifiers": []}]),
        ("Omar Tran enjoys eating watermelon, and it is one of their favorite fruits",
         [{"subject": "Omar Tran", "relation": "enjoys_eating", "object": "watermelon", "qualifiers": []}]),
        ("S. Jones enjoyed eating peach in the past",
         [{"subject": "S. Jones", "relation": "enjoys_eating", "object": "peach", "qualifiers": ["past"]}]),
        ("B. Mensah serves plum to other people but does not eat it",
         [{"subject": "B. Mensah", "relation": "serves_to_others", "object": "plum", "qualifiers": []},
          {"subject": "B. Mensah", "relation": "eats", "object": "plum", "qualifiers": ["negated"]}]),
        ("Talia Novak dislikes eating yogurt, so he rarely buys it",
         [{"subject": "Talia Novak", "relation": "dislikes_eating", "object": "yogurt", "qualifiers": []}]),
    ]
