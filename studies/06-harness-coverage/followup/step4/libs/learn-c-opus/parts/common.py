"""Shared grammar for community-record documents (not a part; imported by the parts in this folder).

The grammar, top down:

  line       := sentence+                       sentences end at . ! ? outside quotes (not after an initial or "St")
  sentence   := clause (CONNECTOR clause)*      a connector splits only where a new clause starts after it
  clause     := OPENER* core MOD* TAIL?         (one family rule per kind of core, see CORES)
              | speech frame around a quoted discourse          (reported_speech rule)
              | clauses joined by "who"/"which"/"and ... both"    (linked_clauses rule)
              | commentary without any fact                      (commentary ignore-rule)
  OPENER     := discourse marker ("In a separate update,", "During the meeting,", "At the market,")
              | reporting frame ("The observer noted that", "I observed", "It came up that")
              | narrator circumstance ("I was filing my notes when", "I filed the reimbursement after")
  core       := SUBJECT predicate               third person, or first person inside a quotation ("I own a camera")
  MOD        := time / frequency phrase         ("some time ago", "only in the past", "every morning")
  TAIL       := commentary after a comma or a linking word; scanned for words that make the fact a past one, and
                for "he/she also <predicate>", which adds a fact about the same subject

analyze(clause) returns Result(family, facts) or None; each family rule takes the clauses of its own family.
"""
import copy
import re
from functools import lru_cache

# ---------------------------------------------------------------- tokens

_STOP1 = (r"the|a|an|he|she|it|they|we|i|you|me|us|him|them|this|that|these|those|which|who|whom|where|when|while|so"
          r"|and|but|or|as|to|for|with|in|on|at|by|of|from|his|her|their|our|my|its|there|here|then|also|everyone"
          r"|someone|org|organization|youth|one|some|all|both|each|not|no|was|is|were|be|been|meanwhile|unrelatedly"
          r"|elsewhere|later|nearby|during|after|before|ensuring|making|adding|having|what|how|why|if|though|although"
          r"|whereas|unlike|like|just|only|even|still|now|today|yesterday|every|most|many|several|few|other|another"
          r"|whose|since|because|until|once|about|into|onto|over|under|up|down|out|off|again|too|very|really|recently"
          r"|everything|nothing|something|anyone|people|staff|members|volunteers|organizers|group|team|book|place"
          r"|meaning|noting|saying|explaining|which|contrast|instead|either|way|go")
_VERBS2 = (r"owns|own|recommended|attends|attend|attended|visited|visit|helped|discussed|is|was|said|says|works|work"
           r"|worked|currently|used|plans|routinely|likes|chose|genuinely|enjoys|dislikes|buys|serves|volunteered"
           r"|went|also|no|previously|formerly|suggested|talked|mentioned|simply|prefers|added|explained|keeps"
           r"|volunteer|has|had|assisted|explains|agreed|avoids|helps|buy|serve|enjoyed|disliked|noted"
           r"|continued|concluded|wrote|writes|told|remarked|states|stated|notes|adds|only|chooses")
_NOT_NAME = r"(?!(?:%s|%s|both|and)\b)" % (_STOP1, _VERBS2)
NAME = r"(?:%s[A-Za-z][a-z]+|[A-Za-z]\.)\s%s[A-Za-z][a-z]+(?:[-'][A-Za-z][a-z]+)?" % (_NOT_NAME, _NOT_NAME)
# a name as printed in running text (capitalised surname), used to spot other people inside commentary
NAME_CASED = re.compile(r"\b(?:[A-Z][a-z]+|[A-Za-z]\.)\s[A-Z][a-z]+\b")
YOUTH = r"(?:y\d+|youth\s\d+)"
ORG = r"(?:org|organization)\s\d+"
ID = r"p-\d+"
WORD = r"[\w'-]+"
WORDS = r"[\w'-]+(?:\s[\w'-]+){0,5}?"      # a lazy slot of 1-6 words, ended by what follows it

SUBJ = (r"(?:I,\s(?P<si>%s),|(?P<s>%s|I|he|she|they))(?:,\s(?:on the other hand|meanwhile|however|in turn|too|also|for (?:her|his|their) part),)?"
        % (NAME, NAME))

# ---------------------------------------------------------------- canonical forms


def cap_name(n):
    """'nadia reed' -> 'Nadia Reed', 'n. reed' -> 'N. Reed'."""
    return " ".join(p[:1].upper() + p[1:].lower() for p in n.split())


def canon_youth(y):
    return "Youth " + re.search(r"\d+", y).group(0)


def canon_org(o):
    return "Organization " + re.search(r"\d+", o).group(0)


def canon_id(i):
    return i.upper()


_SMALL = {"of", "the", "a", "an", "and", "in", "on", "at", "to", "for"}


def canon_title(t):
    ws = t.split()
    return " ".join(w.lower() if i and w.lower() in _SMALL else w[:1].upper() + w[1:].lower()
                    for i, w in enumerate(ws))


def canon_city(c):
    return " ".join(w[:1].upper() + w[1:] for w in c.split())


def canon_obj(o):
    o = re.sub(r"\s+", " ", o.strip().lower())
    o = re.sub(r"^(?:the|a|an|some) ", "", o)
    return re.sub(r"(?<=s) kit$| set$", "", o)


def canon_topic(o):
    """objects of recommended / discussed: lower case, no leading article ('The Long Orchard' -> 'long orchard')."""
    return re.sub(r"^(?:the|a|an) ", "", re.sub(r"\s+", " ", o.strip().lower()))


def canon_event(e):
    return re.sub(r"p-", "P-", e.lower())


# ---------------------------------------------------------------- modifiers and tails

# time / frequency phrases right after a predicate, mapped to qualifiers (None = adds nothing)
MODS = [
    (r"some time ago", "some time ago"), (r"only in the past", "past"), (r"in the past", "past"),
    (r"in a former role", "past"), (r"previously", "past"), (r"more recently", "recently"), (r"recently", "recently"),
    (r"now", "currently"), (r"currently", "currently"), (r"yesterday", "yesterday"), (r"last weekend", "last weekend"),
    (r"last week", "last week"), (r"last month", "last month"), (r"earlier this week", "earlier this week"),
    (r"this week", "this week"), (r"later that (?:afternoon|day|evening|morning)", "@"), (r"later", "later"),
    (r"earlier", "earlier"), (r"afterwards?", "afterward"), (r"this morning", "this morning"),
    (r"on (?:mon|tues|wednes|thurs|fri|satur|sun)days?", "@"), (r"on weekends", "on weekends"), (r"every \w+(?: morning| afternoon| evening| night)?", "@"),
    (r"regularly", "regularly"), (r"routinely", "routinely"), (r"once", "once"),
    (r"too", None), (r"as well", None), (r"also", None), (r"nearby", None), (r"again", None), (r"instead", None),
]
MOD_RX = "|".join(m for m, _ in MODS)
TAIL_START = (r"(?:\s*[,;:]|\s+(?:and|so|which|who|that|to|for|with|during|as|in|on|at|after|before|because|when|where"
              r"|while|though|but|from|since|outlining|highlighting|sharing|providing|bringing|ensuring|making|adding"
              r"|having|assisting|supporting|showing|whereas|until|by|via|about|alongside|near|over|under|into|around"
              r"|through|throughout|without|helping|offering|noting|despite|together|picked|meaning|used)\b)")
END = r"(?P<mods>(?:\s(?:%s))*)(?P<tail>%s.*)?" % (MOD_RX, TAIL_START)

PAST_TAIL = re.compile(r"\b(?:no longer|in the past|lapsed|has since ended|former|previously|past (?:event|visit|activity)"
                       r"|used to|does not (?:attend )?now|not now|is now in the past|was in the past|has ended|as (?:a )?past"
                       r"|has since (?:faded|concluded|stopped)|stepped back|having (?:left|stopped|quit)|formerly)\b", re.I)

# words showing that a text carries a fact; commentary containing them is never ignored
FACT_SIGNAL = re.compile(
    r"\b(?:owns?|own)\s(?:a|an)\b|\brecommended\b|\bsuggested\b|\battend(?:s|ed)?\s(?:the|evening|daytime)\b"
    r"|\bvisit(?:ed|s)?\sthe\b|\bwent\sto\b|\bhelped\swith\b|\bdiscussed\b|\btalked\sabout\b|\bvolunteer(?:ed|s)?\sat\b"
    r"|\bworks?\s(?:the|for)\b|\bworked\b|\btravel(?:s|ed)?\sby\b|\bused\sthe\b|\bplans\sto\suse\b|\bprefers?\b"
    r"|\bequally\b|\bchose\b|\bavoid\b|\bskipping\b|\benjoys?\seating\b|\bdislikes?\b|\bbuys?\b|\bserves?\b"
    r"|\bguardian\b|\bemergency contact\b|\broster\b|\bbased in\b|\bevent-|\bp-\d|\b(?:org|organization)\s\d"
    r"|\by\d|\byouth\s\d|\bidentifier\b", re.I)
# words that change meaning; a standalone sentence holding them may modify a neighbouring fact, so it is not ignored
MEANING = re.compile(r"\b(?:no longer|not|never|n't|in the past|used to|formerly|previously|future|plans? to use"
                     r"|temporarily|guardian)\b", re.I)


def mod_quals(mods):
    out = []
    for m in re.findall(MOD_RX, mods or "", re.I):
        for rx, q in MODS:
            if re.fullmatch(rx, m, re.I):
                q = m.lower() if q == "@" else q
                if q and q not in out:
                    out.append(q)
                break
    return out


# ---------------------------------------------------------------- core predicates

class Core:
    def __init__(self, family, pattern, build):
        self.family = family
        self.rx = re.compile(pattern + END, re.I)
        self.build = build


def _q(*qs):
    return [q for q in qs if q]


def _f(s, rel, obj, quals):
    return {"subject": s, "relation": rel, "object": obj, "qualifiers": list(quals)}


CORES = []


def core(family, pattern):
    def deco(fn):
        CORES.append(Core(family, pattern, fn))
        return fn
    return deco


# identity -------------------------------------------------------------
@core("identity", r"the community roster (?:records|lists) (?P<n>%s|me) under identifier (?P<id>%s)"
      r"(?: and also uses the familiar names? (?P<a>%s(?:(?:,\s|\sand\s|\sor\s)%s)*))?" % (NAME, ID, NAME, NAME))
def _roster(g, s):
    pid = canon_id(g["id"])
    n = s if g["n"].lower() == "me" else cap_name(g["n"])
    if not n:
        return None
    out = [_f(pid, "has_name", n, [])]
    for a in re.split(r",\s|\sand\s|\sor\s", g["a"]) if g["a"] else []:
        out.append(_f(pid, "has_alias", cap_name(a), []))
    return out


# organisations --------------------------------------------------------
@core("org_location", r"(?P<org>%s) is based in (?P<city>[A-Za-z][\w'.]*(?:\s[A-Za-z][\w'.]*){0,3}?)" % ORG)
def _based(g, s):
    return [_f(canon_org(g["org"]), "based_in", canon_city(g["city"]), [])]


@core("employment", SUBJ + r"\s(?P<cur>currently\s)?(?:(?P<past>used to work|worked|formerly worked)|works?) for (?P<org>%s)"
      % ORG)
def _works_for(g, s):
    return [_f(s, "works_for", canon_org(g["org"]), _q(g["cur"] and "currently", g["past"] and "past"))]


@core("shift", SUBJ + r"\s(?P<cur>currently\s)?(?:(?P<past>used to work|worked|formerly worked)|works?) the (?P<o>\w+) shift")
def _shift(g, s):
    return [_f(s, "works_shift", g["o"].lower(), _q(g["cur"] and "currently", g["past"] and "past"))]


# travel ---------------------------------------------------------------
@core("travel", SUBJ + r"\s(?:(?P<used>used to )?routinely (?:travels?|traveled) by|(?P<used2>used to) travel by)"
      r" (?P<o>%s)(?P<rt> routinely)?(?P<nl>,? but (?:I |he |she |they )?no longer (?:does|do))?" % WORD)
def _routine(g, s):
    return [_f(s, "travels_by", g["o"].lower(), _q("routinely", (g["used"] or g["used2"] or g["nl"]) and "past"))]


@core("travel", SUBJ + r"\sused to take the (?P<o>%s) (?P<f>most weekdays|every day|daily)" % WORD)
def _used_take(g, s):
    return [_f(s, "travels_by", g["o"].lower(), ["routinely", "past"])]


@core("travel", SUBJ + r"\s(?:used|took) the (?P<o>%s) once" % WORD)
def _once(g, s):
    return [_f(s, "travels_by", g["o"].lower(), ["once"])]


@core("travel", SUBJ + r"\splans? to use the (?P<o>%s) in the future" % WORD)
def _future(g, s):
    return [_f(s, "travels_by", g["o"].lower(), ["future", "planned"])]


@core("travel_preference", SUBJ + r"\s(?P<g>genuinely )?prefers? (?:the )?(?P<a>%s) to (?:the )?(?P<b>%s) when both are available"
      % (WORD, WORD))
def _prefers(g, s):
    return [_f(s, "prefers", "%s over %s" % (g["a"].lower(), g["b"].lower()),
               _q(g["g"] and "genuinely", "when both are available"))]


@core("travel_preference", SUBJ + r"\slikes? (?:the )?(?P<a>%s) and (?:the )?(?P<b>%s) equally" % (WORD, WORD))
def _equal(g, s):
    return [_f(s, "likes_equally", "%s and %s" % (g["a"].lower(), g["b"].lower()), [])]


@core("travel_preference", SUBJ + r"\schose (?:the )?(?P<a>%s) over (?:the )?(?P<b>%s) (?P<only>only )?because of"
      r" (?:a |an )?(?P<why>\w+)" % (WORD, WORD))
def _chose(g, s):
    return [_f(s, "chose", "%s over %s" % (g["a"].lower(), g["b"].lower()),
               _q(("only " if g["only"] else "") + "because of " + g["why"].lower()))]


# food -----------------------------------------------------------------
@core("diet", SUBJ + r"\s(?P<cur>currently )?(?:chooses? to avoid|avoids?) (?P<o>%s)" % WORDS)
def _avoid(g, s):
    return [_f(s, "avoids", canon_obj(g["o"]), _q(g["cur"] and "currently"))]


@core("diet", SUBJ + r"\s(?:is|am) (?P<t>temporarily )?skipping (?P<o>%s)" % WORDS)
def _skip(g, s):
    return [_f(s, "skips", canon_obj(g["o"]), _q(g["t"] and "temporarily"))]


@core("diet", SUBJ + r"\sbuys? (?P<o>%s) for other people" % WORDS)
def _buys(g, s):
    return [_f(s, "buys_for_others", canon_obj(g["o"]), [])]


@core("diet", SUBJ + r"\s(?:simply )?(?:(?P<past>used to enjoy|enjoyed)|enjoys?) eating (?P<o>%s)" % WORDS)
def _enjoys(g, s):
    return [_f(s, "enjoys_eating", canon_obj(g["o"]), _q(g["past"] and "past"))]


@core("diet", SUBJ + r"\s(?:(?P<past>used to dislike|disliked)|dislikes?) eating (?P<o>%s)" % WORDS)
def _dislikes(g, s):
    return [_f(s, "dislikes_eating", canon_obj(g["o"]), _q(g["past"] and "past"))]


@core("diet", SUBJ + r"\sserves? (?P<o>%s) to other people but does not eat (?:it|them)" % WORDS)
def _serves(g, s):
    o = canon_obj(g["o"])
    return [_f(s, "serves_to_others", o, []), _f(s, "eats", o, ["negated"])]


# volunteering -----------------------------------------------------------
@core("volunteering", SUBJ + r"\s(?:also )?volunteer(?:ed|s)? at (?P<e>(?:old-)?event-[\w-]+?) during (?P<t>(?:this|last|next)[- ]year|[\w-]+)")
def _volunteer(g, s):
    return [_f(s, "volunteered_at", canon_event(g["e"]), [re.sub(r"\s", "-", g["t"].lower())])]


# guardianship -----------------------------------------------------------
@core("guardianship", SUBJ + r"\s(?:is|am) the (?P<l>legal )?guardian of (?P<y>%s)" % YOUTH)
def _guardian(g, s):
    return [_f(s, "guardian_of", canon_youth(g["y"]), _q(g["l"] and "legal"))]


@core("guardianship", SUBJ + r"\s(?:is|am) (?:listed as )?an emergency contact(?P<ng>,? (?:but )?not a (?:legal )?guardian,?)?"
      r" for (?P<y>%s)(?P<ng2>,? but not (?:a |the |their )?(?:legal )?guardian)?" % YOUTH)
def _emergency(g, s):
    y = canon_youth(g["y"])
    out = [_f(s, "emergency_contact_for", y, [])]
    if g["ng"] or g["ng2"]:
        out.append(_f(s, "guardian_of", y, ["negated"]))
    return out


@core("youth_course", r"(?P<y>%s|I) (?P<cur>currently )?(?:(?P<past>used to attend|attended)|attends?) (?P<o>[a-z]+_[\w]+)"
      r" during the (?P<p>\w+)" % YOUTH)
def _course(g, s):
    subj = canon_youth(g["y"]) if g["y"].lower() != "i" else s
    if not subj:
        return None
    return [_f(subj, "attends_course", g["o"].lower(),
               _q(g["cur"] and "currently", g["past"] and "past", "during the " + g["p"].lower()))]


# everyday activities ------------------------------------------------------
@core("ownership", SUBJ + r"\s(?:also )?owns? (?:a |an )?(?P<o>%s)" % WORDS)
def _owns(g, s):
    return [_f(s, "owns", canon_obj(g["o"]), [])]


@core("ownership", SUBJ + r"\s(?:has|have) (?:a |an |some )?(?!since\b|been\b|already\b|just\b|never\b|not\b|to\b)(?P<o>%s)"
      % WORDS)
def _has(g, s):
    return [_f(s, "owns", canon_obj(g["o"]), [])]


@core("ownership", SUBJ + r"\smentioned keeping (?:a |an |my |his |her )(?P<o>%s)" % WORDS)
def _keeping(g, s):
    return [_f(s, "owns", canon_obj(g["o"]), [])]


@core("ownership", SUBJ + r"\skeeps? (?:my|his|her|their|a|an) (?:set of )?(?P<o>%s)(?=\s(?:in|at|by|on|under)\b)" % WORDS)
def _keeps(g, s):
    return [_f(s, "owns", canon_obj(g["o"]), [])]


@core("recommendation", SUBJ + r"\s(?:also )?(?:recommended|suggested|recommends|recommend|suggest) (?P<o>%s)" % WORDS)
def _recommended(g, s):
    return [_f(s, "recommended", canon_topic(g["o"]), [])]


ASPECTS = (r"plans|activities|trends|events|matters|hours|visits|conditions|access|schedules?|availability"
           r"|renovations|needs|membership|updates|news|programs?|programming|changes|history|layout|options|issues"
           r"|improvements|routes|exhibits|strategies|experience|prices|logistics|operations|initiatives|maintenance"
           r"|attendance|expenses|rules|resources|arrangements|work|meetings?|sessions|projects|budget|safety|services")


@core("discussion", SUBJ + r"\s(?:also )?(?:discussed|discuss(?:es)?|talked about|talk about|mentioned(?! that\b| keeping\b)) (?P<o>%s)"
      r"(?: (?P<asp>%s))*" % (WORDS, ASPECTS))
def _discussed(g, s):
    return [_f(s, "discussed", canon_topic(g["o"]), [])]


@core("attendance", SUBJ + r"\s(?:(?P<past>used to attends?|previously attended|formerly attended|attended|no longer attends?)"
      r"|(?:also )?attends?) the (?P<o>%s)(?: (?:meetings?|sessions?|gatherings?))?" % WORDS)
def _attends(g, s):
    return [_f(s, "attends", canon_obj(g["o"]), _q(g["past"] and "past"))]


@core("attendance", SUBJ + r"\s(?:(?P<past>used to be|was|had been)|is) (?:a )?member of the (?P<o>%s)" % WORDS)
def _member(g, s):
    return [_f(s, "attends", canon_obj(g["o"]), _q(g["past"] and "past"))]


@core("visit", SUBJ + r"\s(?:(?P<prev>previously visited|previously went to)|(?:also )?(?:had )?(?:visited|visits?|went to))"
      r" the (?P<o>%s)" % WORDS)
def _visited(g, s):
    return [_f(s, "visited", canon_obj(g["o"]), _q(g["prev"] and "past"))]


@core("helping", SUBJ + r"\s(?:also )?(?:help(?:ed|s)?|assisted|assists) with (?P<t>\w+) at the (?P<o>%s)" % WORDS)
def _helped(g, s):
    return [_f(s, "helped_with_" + g["t"].lower(), canon_obj(g["o"]), [])]


@core("helping", SUBJ + r"\s(?:also )?(?:help(?:ed|s)?|assisted|assists) with (?P<t>setup|registration|cleanup)")
def _helped_here(g, s):
    # the place comes from an opener ("At the market, ...") or a frame ("I was at the market when ...")
    return [_f(s, "helped_with_" + g["t"].lower(), None, [])]


# ---------------------------------------------------------------- openers

MARKER = re.compile(
    r"(?:(?P<at>at the (?P<pl>[\w' -]{1,40}?))|in a separate update|elsewhere in the note|unrelatedly|meanwhile|in contrast"
    r"|also|later|nearby|then|similarly|separately|additionally|by contrast|on the other hand|finally|first|next|however"
    r"|according to [^,]{1,60}?|(?:during|in|on|as|after|before|for|from|within|throughout|while|when|at) [^,\"]{1,80}?)"
    r"\s*(?:,\s*|(?<=then)\s+|(?<=meanwhile)\s+|(?<=also)\s+)", re.I)
REPVERB = re.compile(
    r"\b(?:noted|notes|note|said|says|explained|explains|mentioned|mentions|reports|reported|recorded|records|record"
    r"|shows|show|showed|stated|states|state|observed|observe|confirmed|confirms|confirm|remember|remembered|saw|see"
    r"|know|knew|wrote|writes|added|quoted the speaker|came up|recalled|heard|learned|indicated|indicates|lists"
    r"|listed|highlighted|highlights|documented|documents|captured|captures|clarified|clarifies|noticed|recalls"
    r"|told me|told us|reads|contains|includes|included|contrasted|watched|spotted)\b", re.I)
NARRATOR = re.compile(r"I [^\",]{1,80}?\s(?:when|after|while|before|as)(?: noting that| hearing that)?\s+", re.I)


def _openers(t):
    """Yield (rest, qualifiers, place) for every way of reading a prefix of t as openers; the bare text first."""
    yield t, [], None
    if re.match(r"that\s", t, re.I):
        for rest, q, pl in _openers(t[5:].lstrip()):
            yield rest, ["reported"] + q, pl
    m = MARKER.match(t)
    if m and m.end() < len(t) and not FACT_SIGNAL.search(m.group(0)) and not _other_person(m.group(0)):
        for rest, q, pl in _openers(t[m.end():]):
            yield rest, q, pl or (m.group("pl") if m.group("at") else None)
    m = NARRATOR.match(t)
    if m and m.end() < len(t):
        for rest, q, pl in _openers(t[m.end():]):
            yield rest, q, pl
    for v in REPVERB.finditer(t):
        pre = t[:v.start()]
        if '"' in pre or re.search(r"\d", pre) or len(pre.split()) > 16:
            break
        starts = []
        m = re.compile(r"(?: that)?\s*:?\s+").match(t, v.end())
        if m:
            starts.append(m.end())
        for m2 in re.finditer(r"\sthat\s+", t[v.end():v.end() + 70]):
            starts.append(v.end() + m2.end())
        for st in starts:
            if st < len(t):
                for r2, q, pl in _openers(t[st:]):
                    yield r2, ["reported"] + q, pl


# ---------------------------------------------------------------- analysis

class Result:
    def __init__(self, family, facts):
        self.family, self.facts = family, facts


def clean(t):
    t = t.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'").replace("\u2018", "'")
    t = re.sub(r"\s+", " ", t).strip()
    return re.sub(r"^[\s,;:]+|[\s.,;:!?]+$", "", t)


_PERSON_IN_TEXT = re.compile(r"\b(?:%s[A-Z][a-z]+\s[A-Z][a-z]+|[A-Za-z]\.\s[A-Za-z][a-z]+)(?:\s(?i:%s)\b|,\s(?:who|meanwhile)\b)"
                             r"|\b(?i:%s)\b" % (_NOT_NAME, _VERBS2, YOUTH))


# any-case name followed by a predicate ('and that isaac usman used to attend ...')
_PERSON_DOING = re.compile(r"\b(?:%s)\s(?:owns?\s(?:a|an)\b|used to\b|attends?\sthe\b|visited\sthe\b|recommended\b|helped\swith\b"
                           r"|discussed\b|volunteered\b|works\s(?:for|the)\b|routinely\b|currently\b|is\s(?:the|an)\b"
                           r"|enjoys\b|dislikes\b|buys\b|serves\b|plans\sto\b|likes\b|genuinely\b|chose\b)" % NAME, re.I)
# a capitalised name that is not the object of a verb (titles such as 'Quiet Machines' follow 'recommended' etc.)
_CASED_PERSON = re.compile(r"(?<!recommended )(?<!discussed )(?<!suggested )(?<!mentioned )(?<!about )(?<!of )"
                           r"(?<!the )(?<!The )\b%s[A-Z][a-z]+\s[A-Z][a-z]+\b(?!\s(?:of|and|in|on|at)\b)"
                           % _NOT_NAME)


def _other_person(t):
    """True if t names somebody or something with an identifier ('... while Q. Reed owns a camera', 'Org 027 is ...')."""
    if re.search(r"\b(?:%s|%s)\b|\bevent-|\bp-\d" % (ORG, ID), t, re.I):
        return True
    if _PERSON_DOING.search(t) or _CASED_PERSON.search(t):
        return True
    return any(not re.fullmatch(_STOP1, m.group(0).split()[0], re.I) for m in _PERSON_IN_TEXT.finditer(t))


def _tail_ok(tail):
    """A tail is commentary; it must not hide a fact about another person."""
    if not tail:
        return True
    if FACT_SIGNAL.search(tail) and _other_person(tail):
        return False
    if re.search(r"\bwho\b", tail) and FACT_SIGNAL.search(tail):
        return False
    return True


def _tail_facts(tail, subj, speaker):
    """Facts in a tail about the same subject: ', and she also visited the library', ' and owns a guitar'."""
    if not subj:
        return []
    m = re.match(r"\s*[,;]?\s*(?:and|but)\s+(?:also\s+|later\s+)?(?P<vp>(?!he\b|she\b|they\b|I\b|it\b|we\b)\w.*)$",
                 tail or "", re.I)
    if m and re.fullmatch(NAME, subj):
        r = parse_core(subj + " " + m.group("vp"), speaker=speaker, pron=subj)
        if r:
            return [f for f in r[1] if f["object"] not in ("it", "them", "this", "that")]
    m = re.match(r"\s*[,;]?\s*(?:and|but|so)?\s*(?P<c>(?:he|she|they)\s.*)$", tail or "", re.I)
    if not m:
        return []
    r = parse_core(m.group("c"), speaker=speaker, pron=subj)
    # "he mentioned it": an object that only points back carries nothing new
    return [f for f in r[1] if f["object"] not in ("it", "them", "this", "that")] if r else []


def parse_core(t, speaker=None, pron=None, place=None, quals=()):
    """Match t as SUBJECT predicate MOD* TAIL?; return (family, facts) or None."""
    for c in CORES:
        m = c.rx.fullmatch(t)
        if not m:
            continue
        g = {k: (v or "") for k, v in m.groupdict().items()}
        subj = None
        if "s" in g or "si" in g:
            raw = g.get("si") or g.get("s")
            if raw.lower() == "i":
                subj = speaker
            elif raw.lower() in ("he", "she", "they"):
                subj = pron
            else:
                subj = cap_name(raw)
            if not subj:
                continue
        elif g.get("n", "").lower() == "me":
            subj = speaker
        elif g.get("y", "").lower() == "i":
            subj = speaker
            if not subj:
                continue
        tail = g.get("tail", "")
        if not _tail_ok(tail):
            continue
        facts = c.build(g, subj)
        if not facts:
            continue
        extra = mod_quals(g.get("mods"))
        if tail and PAST_TAIL.search(tail):
            extra.append("past")
        if any(f["object"] is None for f in facts):
            if not place:
                continue
            for f in facts:
                f["object"] = canon_obj(place)
        if c.family not in ("identity", "org_location"):
            for f in facts:
                for q in list(quals) + extra:
                    if q not in f["qualifiers"]:
                        f["qualifiers"].append(q)
        return c.family, facts + _tail_facts(tail, subj, speaker)
    return None


def parse_simple(t, speaker=None, pron=None):
    """OPENER* core: a clause without quotes."""
    for rest, quals, place in _openers(t):
        r = parse_core(rest, speaker=speaker, pron=pron, place=place, quals=quals)
        if r:
            return r
    return None


def openers_only(pre):
    """True if pre is empty or only openers (markers, reporting frames)."""
    pre = pre.strip()
    if not pre:
        return True
    return any(rest == "X" for rest, _, _ in _openers(pre + " X"))


def is_commentary(t):
    """Text that carries no fact: no predicate words, no names, no identifiers, no meaning-changing words."""
    t = clean(t).replace('"', "")
    if not t:
        return True
    if FACT_SIGNAL.search(t) or MEANING.search(t) or re.search(r"\d", t):
        return False
    if re.search(r"\b[A-Za-z]\.\s[A-Za-z]+", t):
        return False
    return True


# ---------------------------------------------------------------- splitting

_ABBR = re.compile(r"(?:^|[\s\"(\u201c])(?:[A-Za-z]|St|Mr|Mrs|Ms|Dr)$")
CLAUSE_START = re.compile(
    r"\s*(?:(?:%s)(?:\s(?:%s)\b|:|,\s(?:meanwhile|also|on the other hand),|\sand\s(?:%s))|the community roster\b|%s\s|%s\s"
    r"|I\s(?:own|attend|visited|helped|discussed|recommended|volunteered|work|used|routinely|genuinely|like|currently"
    r"|keep|remember|noted|observed|saw|also|went|plan|prefer|enjoy|dislike|buy|serve|am|chose|know|knew|heard|learned"
    r"|recorded|stated|explained|confirmed|noticed|watched|think|believe)\b|that\s(?:%s)\s(?:%s)\b)"
    % (NAME, _VERBS2, NAME, ORG, YOUTH, NAME, _VERBS2), re.I)
CONNECTOR = re.compile(r",\s(?:and|but|while|whereas)\s|;\s|\s(?:and|but|while|whereas)\s|,\s", re.I)
DROPPABLE = [r"[,;]?\s*(?:and|but|while|whereas)?"]

_OPEN_Q, _CLOSE_Q = "\u201c", "\u201d"


def _in_quote(s):
    """flags[i] = True if character i is a quotation mark or lies inside a quotation."""
    inside, out = False, []
    for ch in s:
        if ch == _OPEN_Q:
            inside = True
            out.append(True)
        elif ch == _CLOSE_Q:
            inside = False
            out.append(True)
        elif ch == '"':
            inside = not inside
            out.append(True)
        else:
            out.append(inside)
    return out


def sentences(line):
    """Cut a line into sentence spans (start, end), never inside a quotation, never after an initial or 'St'."""
    q = _in_quote(line)
    spans, start, i, n = [], 0, 0, len(line)
    while i < n:
        ch = line[i]
        if ch in ".!?":
            j = i + 1
            if q[i]:
                # only a quotation that closes right here can end the sentence: '... library." Next'
                if not (j < n and line[j] in "\"\u201d"):
                    i += 1
                    continue
                j += 1
            while j < n and line[j] in "'":
                j += 1
            if (j >= n or line[j] == " ") and not (ch == "." and _ABBR.search(line[start:i])):
                spans.append((start, j))
                start = j
                i = j
                continue
        i += 1
    if line[start:].strip():
        spans.append((start, n))
    return spans


def _trim(line, a, b):
    while a < b and line[a] in " \t":
        a += 1
    while b > a and line[b - 1] in " \t.,;:!?":
        b -= 1
    return a, b


def clause_spans(line):
    out = []
    q = _in_quote(line)
    for s, e in sentences(line):
        bounds, a = [], s
        for m in CONNECTOR.finditer(line, s, e):
            if q[m.start()] or m.start() < a:
                continue
            left = line[a:m.start()]
            if left.strip() and CLAUSE_START.match(line, m.end()) and not openers_only(clean(left) + ","):
                bounds.append((a, m.start()))
                a = m.end()
        bounds.append((a, e))
        for a, b in bounds:
            a, b = _trim(line, a, b)
            if b > a:
                out.append((a, b))
    return out


def split_clauses(line):
    return [line[a:b] for a, b in clause_spans(line)]


# ---------------------------------------------------------------- reported speech

SPEECH_V = (r"said|says|added|adds|explained|explains|mentioned|mentions|continued|continues|concluded|concludes|noted"
            r"|notes|stated|states|remarked|replied|recalled|shared|insisted|admitted|agreed|agrees|reported|reports"
            r"|told (?:me|us)|wrote(?: in [^,\"]{1,60})?|writes(?: in [^,\"]{1,60})?")
SPEAKER = r"(?P<sp>%s|%s|I)" % (NAME, YOUTH)
REPORTER = r"(?:the [\w ]{1,30}?|she|he|they|I|we|%s)" % NAME
SPEECH = [
    # P said, "I own a camera. ..."      Y012 said, "I currently attend ..."      I added, "P attends ..."
    re.compile(r"(?P<pre>[^\"]*?)%s(?:,\s(?:meanwhile|also|then|later),)?\s(?:also\s)?(?:%s)(?:,\snoting)?\s*[,:]?\s*"
               r"\"(?P<inner>[^\"]*)\"?(?P<after>[^\"]*)" % (SPEAKER, SPEECH_V), re.I),
    # P: "I recommended ..."
    re.compile(r"(?P<pre>[^\"]*?)%s:\s*\"(?P<inner>[^\"]*)\"?(?P<after>[^\"]*)" % SPEAKER, re.I),
    # "P visited the museum," the speaker noted      "P owns a camera," P said, "while Q owns a guitar."
    re.compile(r"(?P<pre>)\"(?P<inner>[^\"]*)\"(?P<after>,?\s*%s\s(?:%s)\b.*)" % (REPORTER, SPEECH_V), re.I),
    # I contrasted this with the past, noting, "P attends ..."
    re.compile(r"(?P<pre>[^\"]*?),?\s(?:noting|adding|saying|explaining|stating)(?: that)?,?\s*\"(?P<inner>[^\"]*)\"?"
               r"(?P<after>[^\"]*)", re.I),
    # a bare quotation
    re.compile(r"(?P<pre>)\"(?P<inner>[^\"]*?)\"?(?P<after>)", re.I),
]
AFTER_OK = re.compile(r",?\s*%s\s(?:%s)\b(?P<more>.*)" % (REPORTER, SPEECH_V), re.I)
SAID_PRON = re.compile(r"(?P<pre>.*?)(?P<sp>%s)(?:,\s(?:meanwhile|also),)?\s(?:said|says|mentioned|explained|added|noted|stated)"
                       r"(?: that)?\s(?P<c>(?:he|she|they)\s.*)" % NAME, re.I)


def _discourse(inner, speaker):
    """Facts of a quoted discourse; every piece must parse or be commentary."""
    facts = []
    for piece in split_clauses(inner):
        p = clean(piece)
        if not p:
            continue
        r = parse_simple(p, speaker=speaker) or parse_linked(p, speaker=speaker)
        if r:
            facts.extend(r[1])
        elif is_commentary(p):
            continue
        else:
            return None
    return facts


def _after_facts(after, speaker):
    """What follows a closing quotation: nothing, commentary, '...,' the speaker said, or a further quoted part."""
    after = after.strip()
    if not after or is_commentary(after):
        return []
    m = AFTER_OK.fullmatch(after)
    if m:
        more = clean(m.group("more"))
        if not more or is_commentary(more):
            return []
        more = re.sub(r"^(?:while|and|but|whereas|adding that|that)\s+", "", more.strip('"').strip(), flags=re.I)
        return _discourse(more, speaker)
    return None


def parse_speech(t):
    t = t.replace("\u201c", '"').replace("\u201d", '"').strip()
    t = re.sub(r"[\s.,;:!?]+$", "", t)
    if '"' in t:
        for rx in SPEECH:
            m = rx.fullmatch(t)
            if not m or not (openers_only(m.group("pre")) or is_commentary(m.group("pre"))):
                continue
            sp = m.groupdict().get("sp")
            speaker = None
            if sp and sp.lower() != "i":
                speaker = canon_youth(sp) if re.fullmatch(YOUTH, sp, re.I) else cap_name(sp)
            # a speaker named only after the quotation: "P owns a camera," P said
            if speaker is None:
                am = re.match(r",?\s*(?P<n>%s)\s(?:%s)\b" % (NAME, SPEECH_V), m.group("after") or "", re.I)
                if am:
                    speaker = cap_name(am.group("n"))
            facts = _discourse(m.group("inner"), speaker)
            more = _after_facts(m.group("after") or "", speaker)
            if facts is None or more is None or not (facts or more):
                continue
            facts = facts + more
            for f in facts:
                if "reported" not in f["qualifiers"]:
                    f["qualifiers"].append("reported")
            return "speech", facts
        return None
    m = SAID_PRON.fullmatch(t)
    if m and openers_only(m.group("pre")):
        r = parse_core(clean(m.group("c")), pron=cap_name(m.group("sp")), quals=["reported"])
        if r:
            return "speech", r[1]
    return None


# ---------------------------------------------------------------- linked clauses

LINK = (r"in contrast to|unlike|like|along with|together with|with|alongside|which is (?:a contrast|different|in contrast)"
        r" (?:to|from)|in addition to")
RELATIVE = re.compile(r"(?P<head>.*?)(?:,?\s(?:%s))?\s?(?P<n>%s|%s),\swho\s(?P<pred>.+?)(?P<more>,\sand\s(?P<n2>%s),\swho\s"
                      r"(?P<pred2>.+))?" % (LINK, NAME, YOUTH, NAME), re.I)
WHICH_NAME = re.compile(r"(?P<head>.+?),\swhich\s(?P<n>%s)\s(?P<v>recommended|discussed|mentioned|suggested)" % NAME, re.I)
HOW_LINK = re.compile(r"(?P<head>.+?),\s(?:which is (?:different from|similar to|in contrast to|unlike) (?:how|what|when)"
                      r"|unlike how|in contrast to how|just as|much like how)\s(?P<c>.+)", re.I)
BOTH = re.compile(r"(?P<pre>.*?)(?P<a>%s)\sand\s(?P<b>%s)\s(?:both\s)?(?P<pred>.+)" % (NAME, NAME), re.I)
NARRATOR_WITH = re.compile(r"(?P<pre>.*?)I (?P<v>visited|went to|discussed) (?:the )?(?P<o>%s) with (?P<n>%s)(?P<tail>%s.*)?"
                           % (WORDS, NAME, TAIL_START), re.I)
NARRATOR_WHEN = re.compile(r"(?P<pre>.*?)I was (?:at|in) the (?P<o>%s) when (?P<c>.+)" % WORDS, re.I)


def parse_linked(t, speaker=None):
    """Clauses joined into one: relative 'who'/'which' clauses, 'P and Q both ...', narrator frames."""
    m = RELATIVE.fullmatch(t)
    if m:
        facts = []
        head = m.group("head").strip(" ,")
        if head:
            r = parse_simple(head, speaker=speaker)
            if not r:
                return None
            facts.extend(r[1])
        n = m.group("n")
        for nm, pred in ((n, m.group("pred")), (m.group("n2"), m.group("pred2"))):
            if not nm:
                continue
            r = parse_core(nm + " " + pred, speaker=speaker)
            if not r:
                return None
            facts.extend(r[1])
        return "linked", facts
    m = WHICH_NAME.fullmatch(t)
    if m:
        r = parse_simple(m.group("head"), speaker=speaker)
        if r and r[1] and r[1][0]["object"]:
            rel = "recommended" if m.group("v").lower() in ("recommended", "suggested") else "discussed"
            return "linked", r[1] + [_f(cap_name(m.group("n")), rel, r[1][0]["object"], list(r[1][0]["qualifiers"]))]
    m = HOW_LINK.fullmatch(t)
    if m:
        r1 = parse_simple(m.group("head"), speaker=speaker)
        r2 = parse_core(m.group("c"), speaker=speaker)
        if r1 and r2:
            return "linked", r1[1] + r2[1]
    m = BOTH.fullmatch(t)
    if m and openers_only(m.group("pre")):
        ra = parse_core(m.group("a") + " " + m.group("pred"), speaker=speaker)
        rb = parse_core(m.group("b") + " " + m.group("pred"), speaker=speaker)
        if ra and rb:
            q = mod_quals("")
            pre_q = ["reported"] if m.group("pre").strip() and not MARKER.fullmatch(m.group("pre")) else q
            facts = ra[1] + rb[1]
            for f in facts:
                for x in pre_q:
                    if x not in f["qualifiers"]:
                        f["qualifiers"].append(x)
            return "linked", facts
    m = NARRATOR_WITH.fullmatch(t)
    if m and openers_only(m.group("pre")) and _tail_ok(m.group("tail")):
        rel = "discussed" if m.group("v").lower() == "discussed" else "visited"
        o = canon_topic(m.group("o")) if rel == "discussed" else canon_obj(m.group("o"))
        return "linked", [_f(cap_name(m.group("n")), rel, o, ["with narrator"])]
    m = NARRATOR_WHEN.fullmatch(t)
    if m and openers_only(m.group("pre")):
        r = parse_core(m.group("c"), speaker=speaker, place=m.group("o"))
        if r:
            return "linked", r[1]
    return None


# ---------------------------------------------------------------- entry point

CONTRAST_REMARK = re.compile(r"(?:the|this) contrast between the [\w -]+ and the [\w -]+ (?:was|is|seemed|stood)\b.*", re.I)


@lru_cache(maxsize=None)
def _analyze(t):
    if not t:
        return None
    if '"' in t or "\u201c" in t or "\u201d" in t:
        r = parse_speech(t)
        return Result(*r) if r else None
    c = clean(t)
    r = parse_simple(c) or parse_speech(t) or parse_linked(c)
    if r:
        return Result(*r)
    if CONTRAST_REMARK.fullmatch(c) and not FACT_SIGNAL.search(c) and not _other_person(c[1:]):
        return Result("remark", [])
    if is_commentary(t):
        return Result("commentary", [])
    return None


def analyze(clause):
    return _analyze(clause.strip())


def facts_of(clause, family):
    """The facts of clause if it belongs to family, else None (what each family rule returns)."""
    r = analyze(clause)
    if r is None or r.family != family:
        return None
    return copy.deepcopy(r.facts)


# ---------------------------------------------------------------- base class for the rules in this folder

from gram import Rule  # noqa: E402


class FamilyRule(Rule):
    """A rule that takes the clauses whose core predicate belongs to `family` (see CORES and analyze())."""
    family = ""

    def parse(self, clause):
        return facts_of(clause, self.family)


# FamilyRule is only a base: the library loader skips abstract classes, and subclasses become concrete by setting
# `family` to a string
FamilyRule.__abstractmethods__ = frozenset({"family"})
