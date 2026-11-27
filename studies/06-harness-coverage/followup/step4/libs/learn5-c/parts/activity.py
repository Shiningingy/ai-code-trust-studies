"""Rules for the activity sentences: owns, recommended, discussed, attends, visited, helped."""
import re
from gram import PatternRule
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

class Owns(PatternRule):
    name = "owns"
    solves = "'X owns/has/keeps a camera' (items: camera, garden tools, telescope, guitar, sewing kit [set]), with flavour tails"
    added_by = "learning"
    flags = re.I
    pattern = r"(?P<s>%s) (?:also |simply |just |still |even |only )?(?:(?:owns|own) |(?:has|keeps|keep) (?=(?:an? |the |my )?(?:set of )?(?:%s)\b))(?:an? |the |my )?(?:set of )?(?P<o>(?:%s)|[a-z ]+?)(?: set| kit| collection)?(?: in the shed| in my craft room| near the shed| in her bag| in his bag)?%s%s" % (SUBJ, ITEMS, ITEMS, EXTRA, TAIL)
    examples = [("B. Ito owns a garden tools", [fact("B. Ito", "owns", "garden tools")]),
                ("Mateo Foster owns a telescope, which he often brings to our outdoor events",
                 [fact("Mateo Foster", "owns", "telescope")])]

    def build(self, g):
        return [fact(subj(g["s"]), "owns", g["o"].lower().strip(), advq(g["tail"]))]


class Recommended(PatternRule):
    name = "recommended"
    solves = "'X recommended <book>' (optionally 'to a friend', 'for the reading list'), object is the lower-cased title"
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:also |simply |just |still |even |only )?(?:recommended|recommend|recommends|suggested) (?P<o>[a-z' ]+?)"
               r"%s%s" % (SUBJ, EXTRA, TAIL))
    examples = [("Hana Ortiz recommended Quiet Machines", [fact("Hana Ortiz", "recommended", "quiet machines")])]

    def build(self, g):
        return [fact(subj(g["s"]), "recommended", g["o"].lower().strip(), advq(g["tail"]))]


class Discussed(PatternRule):
    name = "discussed"
    solves = ("'X discussed/talked about/mentioned <topic>' where the topic is a place, a group or a book title "
              "('library hours' -> topic library, qualifier 'about hours'; a title keeps a leading 'the')")
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:also |simply |just |still |even |only )?(?:discussed|discuss|talked about|mentioned) (?P<det>the )?"
               r"(?!(?:that|he|she|they|it|keeping)\b)(?P<o>[a-z' ]+?)"
               r"(?: (?:activities|trends|events|conditions|plans|schedule|updates|changes|matters))?"
               r"(?: in the meeting| with (?:a|the) [a-z ]+)?%s%s" % (SUBJ, EXTRA, TAIL))
    examples = [("T. Avery discussed the market, highlighting its recent changes",
                 [fact("T. Avery", "discussed", "market")]),
                ("T. Avery discussed The Long Orchard with us", [fact("T. Avery", "discussed", "the long orchard")]),
                ("T. Avery discussed library hours", [fact("T. Avery", "discussed", "library", ["about hours"])])]

    def build(self, g):
        o = g["o"].lower().strip()
        m = re.match(r"(%s|%s)\b(?: (.+))?" % (PLACES, GROUPS), o)
        q = advq(g["tail"])
        if m and m.group(2):
            o, q = m.group(1), ["about " + m.group(2)] + q
        elif not m and g["det"]:
            o = "the " + o
        return [fact(subj(g["s"]), "discussed", o, q)]


class Attends(PatternRule):
    name = "attends"
    solves = ("'X attends the <group>' with past markers (only in the past, used to, previously, no longer, lapsed, "
              "'used to be a member of'); frequency words after it become qualifiers")
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:also |simply |just |still |even |only )?(?P<v>attends?|attended|had attended|used to attends?|used to be a member of|"
               r"previously attended|formerly attended|no longer attends?|is no longer a member of|was a member of) the (?P<o>%s)"
               r"(?P<q>(?:,? but (?:only )?(?:in the past|that (?:is|was) in the past|no longer does)|"
               r" only in the past| in the past| no longer| but no longer does)*)%s" % (SUBJ, GROUPS, TAILX))
    examples = [("T. Patel attends the walking group only in the past",
                 [fact("T. Patel", "attends", "walking group", ["past"])]),
                ("G. Evans attends the chess club", [fact("G. Evans", "attends", "chess club")]),
                ("G. Evans attends the chess club every Tuesday", [fact("G. Evans", "attends", "chess club", ["every tuesday"])]),
                ("g. gupta used to be a member of the history group", [fact("G. Gupta", "attends", "history group", ["past"])])]

    def build(self, g):
        past = bool(re.search(r"attended|used|previously|formerly|no longer|was a", g["v"], re.I)) or bool(g["q"]) or "past" in tailq(g["tail"])
        q = ["past"] if past else []
        return [fact(subj(g["s"]), "attends", g["o"].lower(), q + [x for x in tailq(g["tail"]) if x != "past"])]


class Visited(PatternRule):
    name = "visited"
    solves = "'X visited/went to the <place>' with past markers (some time ago, in the past, previously) and time adverbs (last week, recently)"
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:also |simply |just |still |even |only )?(?P<pre>previously |formerly )?(?:visited|visit|visits|had visited|went to) the (?P<o>%s)"
               r"(?P<q>(?: some time ago| in the past| previously| for the walk)*)%s" % (SUBJ, PLACES, TAILX))
    examples = [("Ben Jones visited the sports hall some time ago",
                 [fact("Ben Jones", "visited", "sports hall", ["past"])]),
                ("Ben Jones visited the sports hall last week", [fact("Ben Jones", "visited", "sports hall", ["last week"])])]

    def build(self, g):
        past = bool(g["pre"]) or bool(re.search("ago|past|previous", g["q"])) or "past" in tailq(g["tail"])
        return [fact(subj(g["s"]), "visited", g["o"].lower(), (["past"] if past else []) + [x for x in tailq(g["tail"]) if x != "past"])]


class Helped(PatternRule):
    name = "helped"
    solves = "'X helped with registration/setup/cleanup at the <place>'; relation is helped_with_<task>"
    added_by = "learning"
    flags = re.I
    pattern = (r"(?P<s>%s) (?:also |simply |just |still |even |only )?(?:helped|help|helping|helps|assisted) with (?P<t>registration|setup|cleanup)(?: at the (?P<o>%s)| there)?%s" % (SUBJ, PLACES, TAILX))
    examples = [("K. Khan helped with setup at the library", [fact("K. Khan", "helped_with_setup", "library")])]

    def build(self, g):
        return [fact(subj(g["s"]), "helped_with_" + g["t"].lower(), g["o"].lower(), advq(g["tail"]))]
