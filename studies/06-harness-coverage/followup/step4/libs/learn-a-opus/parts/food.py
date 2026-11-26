"""Food: diets, likes and dislikes, food bought or served for others."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from common import F, SUBJ, lead, slot  # noqa: E402

Q = ""
T = r"(?P<tail>.*)"
FOOD = slot("food", C.FOODS + ["dairy products", "dairy", "meat", "gluten", "sugar"])


class AvoidsFood(C.Core):
    name = "avoids_food"
    solves = ("'X currently chooses to avoid dairy products' (also 'avoids') -> avoids 'dairy products', with "
              "qualifier current when 'currently' is written")
    added_by = "learning"
    pattern = (Q + SUBJ + r" (?:(?P<cur>currently) )?(?:(?:chooses|choose) to avoid|avoids|avoid)"
               r"(?: eating)? " + FOOD + T)
    examples = [("Priya Mensah currently chooses to avoid dairy products.",
                 [F("Priya Mensah", "avoids", "dairy products", "current")]),
                ("Kofi Mensah avoids dairy products for health reasons.",
                 [F("Kofi Mensah", "avoids", "dairy products", "note:for health reasons")])]

    def make(self, s, g, q):
        return [F(s, "avoids", C.obj(g["food"]), lead(g, "cur", "current"), q)]


class TemporarilySkipping(C.Core):
    name = "temporarily_skipping"
    solves = ("'X is temporarily skipping <food>' -> skipping <food> with qualifier temporarily (a short break, "
              "different from choosing to avoid a food group)")
    added_by = "learning"
    pattern = Q + SUBJ + r" (?:is|am) (?P<tmp>temporarily )?(?:skipping|avoiding) " + FOOD + T
    examples = [("Samir Mensah is temporarily skipping cheese.",
                 [F("Samir Mensah", "skipping", "cheese", "temporarily")])]

    def make(self, s, g, q):
        return [F(s, "skipping", C.obj(g["food"]), lead(g, "tmp", "temporarily"), q)]


class EnjoysEating(C.Core):
    name = "enjoys_eating"
    solves = ("'X enjoys eating <food>' -> enjoys_eating; past forms ('in the past', 'used to enjoy eating', "
              "'enjoyed eating') add past")
    added_by = "learning"
    pattern = (Q + SUBJ + r" (?:(?P<past>used to enjoy|enjoyed)|enjoys|enjoy|likes|like|loves|love) eating "
               + FOOD + T)
    examples = [("Jia Haddad enjoys eating orange, and it is one of their favorite fruits.",
                 [F("Jia Haddad", "enjoys_eating", "orange", "note:and it is one of their favorite fruits")]),
                ("Dev Bennett used to enjoy eating peach.", [F("Dev Bennett", "enjoys_eating", "peach", "past")]),
                ("T. Ito enjoys eating pear in the past.", [F("T. Ito", "enjoys_eating", "pear", "past")])]

    def make(self, s, g, q):
        return [F(s, "enjoys_eating", C.obj(g["food"]), lead(g, "past", "past"), q)]


class DislikesEating(C.Core):
    name = "dislikes_eating"
    solves = "'X dislikes eating <food>' -> dislikes_eating (a taste, not a diet)"
    added_by = "learning"
    pattern = Q + SUBJ + r" (?:dislikes|dislike|hates|hate) eating " + FOOD + T
    examples = [("Talia Novak dislikes eating yogurt.", [F("Talia Novak", "dislikes_eating", "yogurt")])]

    def make(self, s, g, q):
        return [F(s, "dislikes_eating", C.obj(g["food"]), q)]


class ServesNotEats(C.Core):
    name = "serves_food_to_others"
    solves = ("'X serves <food> to other people but does not eat it' -> serves_to_others with qualifier "
              "'does not eat it' (X does NOT eat the food)")
    added_by = "learning"
    pattern = (Q + SUBJ + r" (?:serves|serve) " + FOOD + r" to other people(?P<neg>,? but (?:does|do) not eat it)?"
               + T)
    examples = [("Kofi Ito serves mango to other people but does not eat it.",
                 [F("Kofi Ito", "serves_to_others", "mango", "does not eat it")])]

    def make(self, s, g, q):
        return [F(s, "serves_to_others", C.obj(g["food"]), lead(g, "neg", "does not eat it"), q)]


class BuysForOthers(C.Core):
    name = "buys_food_for_others"
    solves = "'X buys <food> for other people' -> buys_for_others (says nothing about what X eats)"
    added_by = "learning"
    pattern = Q + SUBJ + r" (?:buys|buy|bought) " + FOOD + r" for other people" + T
    examples = [("Rosa Diaz buys cheese for other people.", [F("Rosa Diaz", "buys_for_others", "cheese")])]

    def make(self, s, g, q):
        return [F(s, "buys_for_others", C.obj(g["food"]), q)]
