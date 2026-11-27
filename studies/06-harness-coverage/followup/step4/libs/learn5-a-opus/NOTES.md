# Grammar library for the community-records documents — notes for later sessions

## Running it

```
python -m gram test  --lib lib
python -m gram parse train/docN.md --lib lib --manual train/docN.manual.jsonl --out out
```
Then query `out/parsed.jsonl` with `lib/query.py` (it is outside `parts/`, so it is not a grammar part):
```python
import sys; sys.path.insert(0, "lib")
from query import Facts, FRUITS, DAIRY, PUBLIC_TRANSPORT, COASTAL
F = Facts("out/parsed.jsonl")
for p in F.ids():                       # every P-id named in a roster sentence
    F.of(p, "works_for")                # facts about p under all its written forms
    F.current(F.of(p, "works_shift"))   # drops time:past / time:future / neg / freq:once
F.subject_facts("Organization 010", "based_in"); F.subject_facts("Y118", "attends_course")
```
On the four training documents every clause is resolved (2 clauses via manual files, both pronoun or "there"
references to the previous sentence), and the four final queries are answered correctly with the recipes below.

## The language

A document is `### Passage D-xxxxx` headings, each followed by one line of 1–6 sentences, then `### Final Query`.
A sentence is one or more clauses joined by `, and` / `, but` / `, while` / `, whereas` / `; ` / list commas /
bare `and`. A clause is

```
[discourse opener]  [evidence opener]  [context,]  SUBJECT  [adverbs]  VERB-PHRASE  [tail]
```

* **Discourse openers** (dropped by the splitter, no meaning): `In a separate update,`, `Elsewhere in the note,`,
  `The same account also says that`, `Unrelatedly,`, `Also,`, `In contrast,`, `Later,`, `Then`, `During an
  ordinary team conversation,`, `In/On/During/At the|my <...> notes|recap|log|chat|meeting|handoff|...,` (list in
  `common.INTRO`).
* **Evidence openers** (kept as a qualifier): `it came up that` → `evidence:it came up`; `I noted/observed/recorded/
  stated/remember/watched/know (that)`, `I was <doing X> when (I remembered that)`, `I filed the reimbursement
  after`, `I handed off the notes:` → `evidence:narrator`; `The <source> notes/records/states/shows (that)` →
  `evidence:record`; `The (quoted) speaker explained that`, `According to the speaker,`, `In the quoted speaker's
  account,`, `I quoted the speaker:` → `reported_by:the speaker`; `it was noted that` → `evidence:it was noted`.
* **Context**: `During this-year,` → `time:this-year`; `At the <place>,` → the place of a helping clause.
* **Subject**: a person in any written form, `I`/`me` (inside quotes: the speaker), `I, Omar Foster,` (narrator
  names themself), a list `P. Khan and G. Ito both`, with a parenthetical `, meanwhile,` or a relative `, who`.
  Non-person subjects: `Organization 009` / `Org 009`, `Y118` / `Youth 118`.
* **Adverbs** before the verb map to qualifiers (`common.ADVERBS`): used to / previously / formerly / no longer →
  `time:past`; currently / now → `time:current`; routinely / usually / regularly → `freq:routinely`; temporarily →
  `temporarily`; genuinely → `genuinely`; plans to / will → `time:future`; never → `neg`; also/often/simply... → none.
* **Tail** (anything after the verb phrase, incl. `, which ...`, `, a task that ...`, `, and she ...`): phrases in
  `common.TAIL_QUALS` become qualifiers (`only in the past`, `in a former role`, `but no longer does`, `has since
  lapsed`, `having stopped`, `is not a member now` → `time:past`; `some time ago`; `in the future`; `once` →
  `freq:once`; `this year`; `every week` → `freq:regular`; `during the evening` → `during:evening` ...). Any other
  tail is elaboration and is ignored — UNLESS it contains a negation/hedge word (`common.RED_FLAG`) or a person/id
  (then the clause is left unparsed instead of misread). Text after `so` / `because` is a consequence, never a
  change of the fact.
* **Reported speech**: `X said, "..."`, `X: "..."`, `"...," the speaker said.`, `"A," X noted, "B"`, a bare
  `"..."` continuing a quote, `I ..., noting, "..."`, and indirect `X said (that) she owns ...`. The inside is
  parsed with all other rules; `I`/`me` becomes the speaker; every fact gets `reported_by:<speaker>`
  (`the speaker` if unnamed, `narrator` if the narrator speaks, `Y023` for a youth, `the administrative record`
  for a quoted record). If the speaker is not a person, an inner `I` becomes `I (the speaker)` / `I (narrator)`.
* **Compound clauses** (`compound.py`): `<clause> in contrast to / which contrasts with / with <person>, who <vp>`;
  `<person>, who <vp>, noted that A and that B` (A, B get `reported_by:<person>`); `<clause>, noting/explaining
  that <clause>` (second gets `reported_by:<subject>`); `<clause>, which is different from how / the fact that
  <clause>`; `<clause about book X>, which <person> recommended`; `I visited the museum with A. Foster` →
  A. Foster visited (`with:narrator`); `..., but that is different from what <person> did when she <vp>`.

## Families of parts

| file | parts | covers |
|---|---|---|
| `splitter.py` + `common.py` | `note_splitter` | sentences, quotes as one unit, connector splitting only before a clause with its own subject, dropped discourse openers |
| `activities.py` | `owns`, `recommended`, `discussed`, `attends`, `visited`, `helped_with`, `helped_when_there`, `volunteered`, `took_part_in_class` | everyday activities |
| `work_travel.py` | `works_for`, `works_shift`, `based_in`, `travels_by`, `travel_preference` | employer, shift, org city, travel habit, train-vs-plane |
| `diet_family.py` | `avoids_food`, `eating_habits`, `guardian`, `youth_course`, `roster` | food, guardianship, youth courses, identities |
| `speech.py` | `reported_speech`, `indirect_speech` | quotations / said-that |
| `compound.py` | `relative_who`, `aside_that`, `object_relative`, `with_narrator`, `different_from_what`, `narration` (ignore), `bare_mention` (ignore) | clauses containing clauses; narrator remarks |
| `framing.py` | `passage_frame` (ignore) | "The travel note included context beyond the submitted expense." etc. |

Rules built on `common.FactRule` only define the verb phrase; subject, adverbs, evidence, context and tail are
shared. All rules are listed in `common.REGISTRY`, which `common.parse_clause()` uses to parse inner clauses.

## Facts: subjects, relations, objects

Subjects are written forms, canonically capitalised (`"k. laurent"` → `K. Laurent`). Join them to ids with the
roster facts: every written form `X` with `X has_id P-114` is that person (`query.Facts` does this). In the
training documents no written form maps to two ids, and some people have no roster sentence (no id).

| relation | subject | object | notable qualifiers |
|---|---|---|---|
| `has_id` | written name | `P-114` | (from "The community roster records <full> under identifier P-114 and also uses the familiar names <short>") |
| `owns` | person | `camera`, `garden tools`, `sewing kit`, `telescope`, `guitar` | `neg` ("..., but I do not"), `time:past` (owned) |
| `recommended` | person | book title (`The Long Orchard`, `Quiet Machines`, `Atlas of Clouds`, `Copper Harbor`) | |
| `discussed` | person | book title, group or place (lowercase) | |
| `attends` | person | `walking group`, `history group`, `chess club`, `garden circle`, `radio society` | `time:past` (only in the past / used to / previously / no longer), `freq:regular` |
| `visited` | person | `museum`, `market`, `sports hall`, `library`, `riverside park` | `time:some time ago`, `time:past`, `time:recently`, `time:last week(end)` |
| `helped_with` | person | `setup` / `cleanup` / `registration` | `at:<place>` |
| `volunteered_at` | person | `event-P-139-0` (this year) / `old-event-P-075` (last year) | `time:this-year` / `time:last-year` |
| `took_part_in_class` | person | `language` / `pottery` / `repair` | `role:teacher|student|observer|organizer`, `time:this-year` |
| `works_for` | person | `Organization 010` (Org 010 = Organization 010) | `time:current` (currently), `time:past` |
| `based_in` | `Organization 010` | city (`Halifax`, `St. John's`, ...) | |
| `works_shift` | person | `night` / `day` | `time:past` ("in a former role", "used to") |
| `travels_by` | person | `bus`, `tram`, `train`, `subway` | `freq:routinely` (habit), `freq:once` (used the tram once), `time:future` (plans to use), `time:past` (but no longer does) |
| `prefers_over` | person | mode | `over:plane`, `genuinely`, `when both are available` |
| `chose_over` | person | mode | `over:plane`, `reason:disruption`, `only because` (NOT a preference) |
| `likes_equally` | person | each of the two modes | `and:<other>` |
| `avoids` | person | `dairy products` | `time:current`, `choice` ("currently chooses to avoid dairy products") |
| `skips` | person | food | `temporarily` ("is temporarily skipping milk" — not a lasting choice) |
| `enjoys_eating` | person | food | `time:past` (used to enjoy / enjoyed ... in the past) |
| `dislikes_eating`, `buys_for_others`, `serves_to_others` | person | food | `serves_to_others` comes with `eats <food> [neg]` ("but does not eat it") |
| `eats` | person | food | `neg` |
| `guardian_of` | person | `Y118` (Youth 118 = Y118) | `legal`; `neg` when "an emergency contact, but not a guardian" |
| `emergency_contact_for` | person | youth | |
| `attends_course` | `Y118` | `evening_pottery`, `evening_language`, `evening_accounting`, `evening_carpentry`, `daytime_first_aid` | `time:current`, `during:evening` / `during:day` |

Qualifier prefixes: `time:`, `freq:`, `during:`, `at:`, `role:`, `over:`, `and:`, `reason:`, `evidence:`,
`reported_by:`, `hedge:`, `with:`; bare: `neg`, `temporarily`, `genuinely`, `choice`, `legal`, `only because`,
`when both are available`.

## Query recipes (verified on the four training queries)

* Reported speech and evidence openers are ordinary facts: COUNT facts with `reported_by:` / `evidence:` (dropping
  them loses correct answers).
* "currently X": use `Facts.current()` (drops `time:past`, `time:future`, `neg`, `freq:once`).
* works for an organization based in a coastal city: current `works_for` → org → `based_in` city in
  `query.COASTAL` (Halifax, Lunenburg, St. John's, Vancouver, Victoria are coastal; Calgary, Edmonton, Ottawa,
  Regina, Winnipeg are not).
* ordinarily travels using public transportation: current `travels_by` with `freq:routinely`, mode in
  `PUBLIC_TRANSPORT` (excludes once / plans to / but no longer does).
* currently works a night shift: current `works_shift` = `night` (excludes "in a former role").
* volunteered at ≥3 distinct events this year: distinct `volunteered_at` objects with `time:this-year`.
* currently chooses to avoid dairy: current `avoids` `dairy products` (NOT `skips`, `dislikes_eating`,
  `buys_for_others`).
* guardian of someone currently attending an evening course: `guardian_of` without `neg` → youth →
  `attends_course` `evening_*` with `time:current` (emergency contacts do not count).
* genuinely prefers train to flying when both available: `prefers_over` `train` with `over:plane` (NOT
  `chose_over` because of a disruption, NOT `likes_equally`).
* enjoys eating a fruit: current `enjoys_eating` with object in `FRUITS` (bread, rice, lentils are not fruit;
  `time:past` excluded).
* personally taught a class this year: `took_part_in_class` with `role:teacher` and `time:this-year` (organizer,
  observer, student do not count).

The documents are built so that one condition holds for ~100 people and distractor variants (past, once,
temporary, disruption, organizer, emergency contact, avoid-vs-skip) catch near misses: always check the
qualifiers.

## Extending

* A new clause kind: add a `FactRule` subclass with `phrases` (verb phrase regexes with named groups) and
  `facts(subject, groups, quals)`; it automatically gets subjects, adverbs, evidence, tails, and works inside
  quotes. Non-FactRule rules must call `C.register(cls)` to be usable inside quotes / compound clauses.
* A new meaningful tail phrase: add it to `common.TAIL_QUALS`; a harmless one containing a negation word: add it to
  `common.HARMLESS`. A new discourse opener: `common.INTRO`; a new evidence opener: `common.EVIDENCE_QUALS`.
* Object vocabularies (`PLACES`, `GROUPS`, `BOOKS`, `ITEMS`, `MODES`, `FOODS`) are in `common.py`; places, groups,
  items, books have a generic fallback, travel modes and foods after "likes" do not (to avoid misreadings).
* Lowercased names are recognised only with a known given name (`common.KNOWN_FIRST`) or an initial; capitalised
  names need no list.
* Check `out/outliers.jsonl`; use the manual file only for cross-sentence references ("He ...", "... there").
* When writing patch scripts, beware that shell heredocs may eat one level of backslashes (`\b` became a
  backspace once); write files with an editor tool instead.
