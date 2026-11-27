# Notes for later sessions

Library for the "community records" documents: passages of short, templated statements about people, organizations and
youths, followed by a final query ("Identify every person who ..."). Run it, then query the facts.

    python -m gram test --lib lib
    python -m gram parse train/doc1.md --lib lib --manual train/doc1.manual.jsonl --out out
    python answer.py                      # parses the four train docs, answers the queries, writes answers.json

From Python: `from lib.queries import Db; db = Db("doc.md", "doc.manual.jsonl")` gives `db.facts` (flat list, each fact has
its source `line`), `db.R.pid(name)` (name -> P-id) and the predicates used by the queries (`coastal_employee`,
`public_transit`, `night_shift`, `events_this_year`, `avoids_dairy`, `taught`, `guardian_of_evening`, `prefers_train`,
`enjoys_fruit`). `lib/resolve.py` has the loader and the name resolver, `lib/queries.py` the predicates. Edit
`answer.py` (the `Q` dict) for new conditions.

## How a line is built (grammar)

* A passage line = several sentences. Some are scene-setting openers ("The appointment note recorded a few pieces of
  background.") -> `ignore_opener`.
* Sentences hold one or more clauses joined by `, and` / `, but` / `, while` / `, whereas` / `, so` / `;` or new sentences.
  `comma_and` (splitter.py) cuts there. It does NOT cut before "but no longer does", "only in the past", "but not a guardian",
  "for Y110", inside a quotation after "X said,", after "I, Name," and before `she/he/they` + fact verb (those stay in one clause
  and are handled by `pronoun_coordination`).
* Opening phrases are dropped as droppable text (they never change the fact): "In a separate update,", "Elsewhere in the note,",
  "Unrelatedly,", "The same account also says that", "A recent personal note mentioned that", "I noted/observed that",
  "The meeting notes record that", "I was filling out ... when", "it came up that", ...
* Quotations: `X said, "I own a camera."` is ONE clause, subject = X, qualifier `quoted`. `X added that Y recommended Z` ->
  subject Y, qualifier `reported`. Several `I ...` sentences inside one quote only carry the speaker in the first clause; later
  ones are in the manual file. Trailing attributions (`," the speaker said`, `Omar concluded`) are ignored.
* Commentary clauses after a fact ("which was a key task", "a book that has been generating interest", "she is no longer a member")
  restate or decorate it -> `ignore_commentary` / `ignore_lowercase_fragment` / `ignore_speech_tag`. They are only ignored when they
  contain no fact verb and no name.
* Normalizers repair case: lower-case names at clause start ("talia usman visited"), "org 025", "p-101", bare verbs ("discuss").
* Text that no grammar should cover is in `train/docN.manual.jsonl` (pronoun/appositive/first-person fragments, ~25-40 per doc).
  `tools/mk_manual.py` shows how the rows were produced (one row per clause: facts, or ignore).

## Entities and names

* Person: written "Hana Ortiz", "H. Ortiz", or lower case. Roster facts link them: `has_id` (subject = full name as listed,
  object `P-nnn`) and `alias` (subject = full name, object = the short name). A person may be listed under an abbreviated name
  ("F. Silva", object P-046) while the text writes "Farah Silva": `Resolver.pid` resolves by initial+surname (first names have
  distinct initials) - always resolve through it, never by string equality.
* Organization: subject `Org 007` (both "Org 007" and "Organization 007" are normalised to `Org 007`). City via `based_in`.
* Youth (doc3): `Youth 037` (written "Youth 037" or "Y037"). Not a person id.
* Events: `event-P-151-0` (this year), `old-event-P-141` (last year), kept as written.
* Objects are lower-case ("quiet machines", "garden tools", "riverside park"); org city keeps its case ("St. John's").

## Facts (subject, relation, object, qualifiers)

| relation | object | qualifiers / notes |
|---|---|---|
| has_id, alias | P-nnn / short name | roster |
| owns | item | `quoted`; `detail:...` |
| recommended | book | ("suggested" is the same relation) |
| discussed | place / club / book | ("talked about", "mentioned") |
| visited | place | `past` + the wording (`some time ago`, `in the past`, `previously`), or `recently`, `last week`, ... ; none = undated |
| helped_with_registration / _setup / _cleanup | place | time words as for visited |
| attends | club | `past` (+ `only in the past`, `used to`, `no longer`, `previously`, `attended`) = former; `every Tuesday`, `now`... frequency |
| volunteered_at | event id | `this year` / `last year` |
| works_for | Org nnn | `currently` when written (plain "works for" is the same, present) |
| works_shift | `day` / `night` | `former` (+`in a former role`/`used to`) = no longer; none = present |
| travels_by | bus/train/tram/subway | `routinely`; `past`+`no longer`(+`used to`) = former habit |
| used_transit | mode | `once` (one-off, NOT a habit) |
| plans_to_use | mode | `future` (NOT a habit) |
| avoids | `dairy products` or a dairy item | `currently` (explicit) is the real avoidance; `temporarily` = skipping a single item |
| buys_for_others, dislikes_eating | dairy item / food | not avoidance |
| enjoys_eating | food | `past`/`used to`/`in the past` = former taste |
| serves_to_others + eats(`negated`) | food | serves it but does not eat it |
| prefers | `train over plane` | `genuinely`, `when both are available` |
| likes_equally | `train and plane` | no preference |
| chose | `train over plane` | `only because of a disruption` (not a preference) |
| took_part_in | `language class` etc. | `as student/teacher/observer/organizer`, `this year` |
| guardian_of | Youth nnn | legal guardian |
| emergency_contact_of | Youth nnn | `not a guardian` |
| attends_course | `evening_language`, `daytime_first_aid`.. | subject is a Youth; `currently`, `evening`/`day` |
| based_in | city | subject `Org nnn` |

Every qualifier word in the text is kept. `quoted` / `reported` facts state the same fact as the plain form (quotation and
reported speech are just a different rendering) - the final-query predicates treat them as true; filter on the qualifier if a
query needs first-hand statements only. `detail:` qualifiers carry harmless descriptive wording ("detail:to pick up supplies").

## Querying tips

* "Current / ordinarily / currently" conditions: exclude facts whose qualifiers contain `past`, `former`, `no longer`, `used to`,
  `once`, `future`, `negated`, `temporarily` (see `PAST_Q` in lib/queries.py).
* "Coastal city": Halifax, Vancouver, Victoria, St. John's, Lunenburg (world knowledge, `COASTAL`); Calgary, Edmonton, Regina,
  Winnipeg, Ottawa are inland. Extend the set if a new document uses other cities.
* "Public transportation": bus, train, tram, subway.
* "Three or more distinct events this year": count distinct `volunteered_at` objects with qualifier `this year`.
* "Taught a class this year": `took_part_in` with `as teacher` and `this year`.
* "Guardian of someone currently attending an evening course": `guardian_of` Youth + that Youth's `attends_course` with
  `currently` and `evening`.
* Lexicons that rules rely on (extend in lib/parts/common.py if a new document introduces new words): PLACES, CLUBS, THINGS,
  BOOKS, TRANSIT, DAIRY, VERBS (name anchors). Unknown objects show up as `unparsed` clauses in `parse` output.
