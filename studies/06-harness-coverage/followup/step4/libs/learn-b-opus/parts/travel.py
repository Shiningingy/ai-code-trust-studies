import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gram import Rule

from common import Pred, analyze, v

MODE = r"(?:the\s+|a\s+)?(?P<mode>bus|tram|subway|train|metro|ferry|car|bike|bicycle|plane|taxi|streetcar|light rail)"
NO_LONGER = r"(?P<nl>,?\s*but\s+(?:I\s+|he\s+|she\s+|they\s+)?no longer (?:does|do)(?: so)?)"


def _mode(m):
    return m["mode"].lower()


class Commute(Rule):
    name = "commute"
    solves = ("how a person travels: 'routinely travels by bus' (qualifier routinely), '... but no longer does' / "
              "'used to routinely travel by' / 'used to take the tram most weekdays, but I no longer do' "
              "(routinely + past), 'used the train once' (once), 'plans to use the subway in the future' (future); "
              "relation travels_by, object the mode")
    added_by = "learning"
    preds = [
        Pred(r"(?:also\s+)?(?:still\s+)?routinely\s+%s\s+by\s+%s(?:\s+to\s+work)?%s?" % (v("travel"), MODE, NO_LONGER),
             lambda m: ("travels_by", _mode(m), ["routinely"] + (["past"] if m["nl"] else [])), 0),
        Pred(r"routinely\s+traveled\s+by\s+%s%s?" % (MODE, NO_LONGER),
             lambda m: ("travels_by", _mode(m), ["routinely", "past"]), 0),
        Pred(r"used to\s+(?:routinely\s+)?travel\s+by\s+%s(?:\s+routinely)?%s?" % (MODE, NO_LONGER),
             lambda m: ("travels_by", _mode(m), ["routinely", "past"]), 0),
        Pred(r"used to\s+(?:routinely\s+)?take\s+%s(?:\s+(?:most|every)\s+(?:weekdays|days|day|morning|mornings))?%s?"
             % (MODE, NO_LONGER),
             lambda m: ("travels_by", _mode(m), ["routinely", "past"]), 0),
        Pred(r"(?:has\s+)?(?:used|took|rode)\s+%s\s+once" % MODE,
             lambda m: ("travels_by", _mode(m), ["once"]), 0),
        Pred(r"%s\s+to\s+(?:use|take)\s+%s\s+in the future" % (v("plan"), MODE),
             lambda m: ("travels_by", _mode(m), ["future"]), 0),
    ]
    examples = [
        ("Dev Chen routinely travels by train",
         [{"subject": "Dev Chen", "relation": "travels_by", "object": "train", "qualifiers": ["routinely"]}]),
        ("Samir Haddad routinely travels by train but no longer does",
         [{"subject": "Samir Haddad", "relation": "travels_by", "object": "train", "qualifiers": ["routinely", "past"]}]),
        ("Farah Usman used the train once",
         [{"subject": "Farah Usman", "relation": "travels_by", "object": "train", "qualifiers": ["once"]}]),
        ("Rosa Diaz plans to use the train in the future",
         [{"subject": "Rosa Diaz", "relation": "travels_by", "object": "train", "qualifiers": ["future"]}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)


class TrainPlane(Rule):
    name = "train_plane"
    solves = ("a person's train-versus-plane preference, three different statements: 'genuinely prefers train to "
              "plane when both are available' (prefers_train_to_plane), 'chose train over plane only because of a "
              "disruption' (chose_train_over_plane, qualifier 'only because of a disruption'), 'likes train and "
              "plane equally' (likes_train_and_plane_equally)")
    added_by = "learning"
    preds = [
        Pred(r"(?:genuinely\s+|really\s+|truly\s+)?%s\s+(?:the\s+)?train\s+(?:travel\s+)?(?:to|over)\s+(?:the\s+)?"
             r"(?:plane|flying)(?:\s+when\s+both\s+are\s+available)?" % v("prefer"),
             lambda m: ("prefers_train_to_plane", "", []), 0),
        Pred(r"(?:chose|chooses|choose)\s+(?:the\s+)?train\s+over\s+(?:the\s+)?plane\s+(?P<only>only\s+)?because of a "
             r"disruption",
             lambda m: ("chose_train_over_plane", "", ["only because of a disruption"]), 0),
        Pred(r"%s\s+(?:the\s+)?train\s+and\s+(?:the\s+)?plane\s+equally" % v("like"),
             lambda m: ("likes_train_and_plane_equally", "", []), 0),
    ]
    examples = [
        ("P. Foster prefers train to plane when both are available",
         [{"subject": "P. Foster", "relation": "prefers_train_to_plane", "object": "", "qualifiers": []}]),
        ("Leah Silva chose the train over the plane only because of a disruption",
         [{"subject": "Leah Silva", "relation": "chose_train_over_plane", "object": "",
           "qualifiers": ["only because of a disruption"]}]),
        ("Mateo Foster likes train and plane equally for travel",
         [{"subject": "Mateo Foster", "relation": "likes_train_and_plane_equally", "object": "", "qualifiers": []}]),
    ]

    def parse(self, clause):
        return analyze(clause, "person", self.preds)
