# Notes for later sessions

Run: `python -m gram parse docN.md --lib lib --manual docN.manual.jsonl --out out/docN` (then read `out/docN/parsed.jsonl`),
or in Python `sys.path.insert(0, "lib"); from tools import Facts; F = Facts.from_document(doc, manual)`.
`answer.py` (repo root) answers the four training queries with `lib/tools.py`; copy it as a template.
`python -m gram test --lib lib` must stay green. All four training documents parse with 0 unresolved clauses.

## The language

A document is a list of passages (`### Passage D-nnnnn`), each one line of 1-8 sentences, then `### Final Query`.
Sentences are `Subject verb-phrase.`; they are chained with `, and` / `, while` / `, but` / `, ` / `;`, may start with a
scene-setting opening ("In a separate update,", "Elsewhere in the note,", "Unrelatedly,", "A recent personal note mentioned that")
and may end with a flavour tail ("..., which he often brings to our events", "..., a task that took several hours").
Filler sentences ("The appointment note recorded a few pieces of background.") carry nothing (ignore-rules `filler`, `narration`,
`narration_fragments`).

Names are written as `Hana Ortiz`, `H. Ortiz`, `hana ortiz`, `h. ortiz`, sometimes bare surname. Facts always use the canonical
form `Hana Ortiz` / `H. Ortiz` (title case). `Youth 75` / `Y075` / `youth 075` all become `Youth 75`. `Org 030` / `Organization 030` /
`org 030` become `Org 030` (zero padding kept). Joining names to person IDs is NOT done by the parts: use `Facts.pid(subject)`
(roster `has_id` + `also_known_as`, and the id inside `event-P-nnn-k`). A few people are not in the roster (no ID) - they cannot
be answers.

## Facts (subject / relation / object / qualifiers)

| relation | object | qualifiers |
|---|---|---|
| owns | item (camera, garden tools, telescope, guitar, sewing kit) | - |
| recommended | book title, lower case (`the long orchard`, `atlas of clouds`...) | - |
| discussed | place / group / title (also `talked about`, `mentioned`) | `about <detail>` |
| attends | group (walking group, chess club, history group, radio society, garden circle) | `past` (only in the past, used to, no longer, previously, lapsed); frequency words |
| visited | place (market, library, museum, riverside park, sports hall) | `past` (some time ago, in the past, previously); `last week`... |
| helped_with_setup / _registration / _cleanup | place | - |
| volunteered_at | event id (`event-P-020-0`, `old-event-P-081`) | `this year` / `last year` |
| works_for | `Org nnn` | `current` (if "currently"), `past` (used to) |
| based_in | city (`Org nnn based_in Halifax`) | - |
| works_shift | day / night | `past` (in a former role, used to), `current` |
| avoids | `dairy products` | `current` |
| enjoys_eating | food | `past` |
| dislikes_eating / skips (`temporary`) / buys_for_others / serves_to_others (`does not eat`) | food | distractors: NOT dairy avoidance, NOT enjoying |
| travels_by | subway/bus/train/tram | `routinely` (ordinary habit), `past` (no longer), `once`, `future` |
| prefers | train (`over plane`) | `genuine` (when "genuinely prefers"; plain "prefers" lacks it) |
| likes_equally / chose | train | `and plane` / `over plane`, `because of a disruption` (NOT a real preference) |
| class_role_teacher / _student / _organizer / _observer | `<subject> class` | `this year` |
| guardian_of | `Youth n` | - |
| emergency_contact_of | `Youth n` | `not guardian` (when stated) |
| attends_course | course (`evening_pottery`, `daytime_first_aid`) | `current`, `during the evening` / `during the day` |
| has_id / also_known_as | `P-nnn` / written form | - |

Qualifiers that change meaning and must be respected when querying: `past`, `once`, `future`, `temporary`, `not guardian`,
`does not eat`, `genuine`, `this year`/`last year`, `routinely`, `current`.
Wrapper qualifiers: `said` (the person says it about themself: `X said, "I ..."`, `X said she ...`), `reported` (someone else reports
it: "The observer noted that X ...", `"...," the speaker noted`), `contrast` (second subject of a "which contrasts with Y, who ..." clause),
and an aside word (`meanwhile`, `on the other hand`). In the four training documents, counting `said`/`reported` facts as true gives
exactly 5 matches per query; dropping them gives fewer. Treat them as true statements (the wrapper is surface variation).

## Part families (lib/parts)

* `splitter.py` - `sentence_clause`: sentences (not split after initials / `St.`), strips scene-setting openings, splits at
  `, and / , while / , but / ; / , ` + new `subject verb`, also at "noting that", "unlike", "which contrasts with" (+ `who` clauses),
  keeps attribution openings ("According to the speaker,", "I noted that", "During this-year,") inside the clause.
* `activity.py` - owns, recommended, discussed, attends, visited, helped (closed vocabularies of items/places/groups; titles are open).
* `persona.py` - roster, volunteered, works_for, org_based, shift, avoid_dairy, food_attitude, transport, transport_preference,
  class_role, guardian, youth_course.
* `reported.py` - `reported` (quotes and attributions) and `aside`; `wrappers.py` - `embedded` (narration + claim),
  `shared_subject` (`X visited ... and owns ...`, `X and Y both ...`), `relative` (`X, who ...`).
  Wrappers delegate the inner claim to the plain rules through `common.delegate`, so each construction is defined once.
* `filler.py` - ignore-rules for sentences with no claim.
* `common.py` - vocabulary regexes (SUBJ, PLACES, GROUPS, ITEMS, MODES), TAIL/TAILX (flavour tails), ADV, canonical-name helpers.
  Helper modules are imported by plain name; each part file inserts its own folder in `sys.path`.

Rules that take free tails: `TAIL` (open-vocabulary objects: only recognised flavour openers may follow, so a title is not eaten)
and `TAILX` (closed objects: anything may follow unless it contains a second claim - then the splitter or a wrapper must split it).
A tail never silently swallows a claim: it is rejected if it contains a fact verb (`_NOFACT`) or ends with a speech verb.

## Things to know when querying

* Domain knowledge is NOT in the facts: coastal cities (Halifax, Vancouver, Victoria, St. John's, Lunenburg; inland: Calgary, Edmonton,
  Regina, Winnipeg, Ottawa), public transport (subway, bus, train, tram), fruits (apple, banana, pear, mango, plum, peach, orange,
  watermelon; not lentils/bread/rice), dairy (milk, cheese, butter, yogurt). Check the city list of each new document.
* "ordinarily travels by public transport" = `travels_by` with `routinely` and without `past`.
* "currently works a night shift" = `works_shift night` without `past`. "works for an organization in a coastal city" = `works_for`
  Org (no `past`) joined with `based_in`.
* "volunteered at >= 3 distinct events this year" = distinct `volunteered_at` objects with `this year` per person ID.
* "guardian of someone currently attending an evening course" = `guardian_of Youth n` joined with `attends_course` (`current`, course starting `evening`).
* Pronoun subjects ("He used to attend...") and multi-sentence quotes ("X said, "I ... . I work the day shift.") cannot be resolved
  inside one clause; training documents have ~35 such clauses in `train/docN.manual.jsonl` (manual rows give the speaker as subject).
  A new document may need the same treatment: `python -m gram parse` lists them in `outliers.jsonl`.
* Qualifiers on a fact come from the clause only; a dangling attribution clause (`The record shows`) is ignored.
