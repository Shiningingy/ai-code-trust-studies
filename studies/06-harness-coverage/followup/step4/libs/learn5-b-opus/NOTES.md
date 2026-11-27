# Community-records grammar: notes for later sessions

Documents: `### Passage D-xxxxx` headings, each followed by one paragraph line of short template sentences, then a
`### Final Query`. One content line = one paragraph. ~8,000 clauses per document; on the four training documents
every clause resolves (≈96% parsed, ≈3% ignored filler, 7 clauses in `train/docN.manual.jsonl`).

## Running and querying

```
python -m gram test  --lib lib
python -m gram parse doc.md --lib lib --manual doc.manual.jsonl --out out     # out/parsed.jsonl, out/outliers.jsonl
```
```python
import sys; sys.path.insert(0, ".")
from lib.query import *                      # Facts, current, has, COASTAL_CITIES, PUBLIC_TRANSIT, FRUITS, predicates
fx = Facts.from_parsed("out/parsed.jsonl")   # or Facts.from_document("doc.md")
ans = sorted(p for p in fx.people()
             if works_for_coastal_org(fx, p) and ordinarily_public_transit(fx, p) and current_shift(fx, p, "night"))
```
`Facts` joins every name form to the person ID (roster facts + unique initial/surname match); `fx.of(pid, rel)` gives
that person's facts, `fx.of("Y055", "attends")` works for youths, `fx.org_city("Organization 031")` for orgs.
`lib/query.py` already has predicates for every condition of the four training queries (see the end of that file);
reuse or adapt them. Check `out/outliers.jsonl` first: an unparsed clause may hide a fact the query needs.

## Clause structure (lib/parts/common.py)

`[opener] [frame] CORE [remark]`
- **Splitter** (`splitter.py`, logic in `common.split_line`): sentences end at `. ! ?` except after a one-letter
  initial (`N. Reed`) or abbreviation (`St. John's`), and never inside a quotation. A sentence is cut at
  `, and / , but / , while / ; / and that ...` only where `<subject> <predicate verb>` starts (`CLAUSE_START`,
  verbs in `PRED_START`) and the text before it already holds a clause. So `, but no longer does` stays with its clause.
  A whole quotation (possibly several sentences) is ONE clause, handled by `quoted_speech`.
- **Openers** (`OPENER_RX`): "Elsewhere in the note,", "In a separate update,", "Unrelatedly,", "Meanwhile," ... dropped.
  "The same account also says that" dropped. Any other fronted phrase ("During this-year,", "At the riverside park,",
  "In the volunteer log,") -> qualifier `context=<text>` (+ time words, e.g. `time=this_year`).
- **Frames** -> qualifier `reported`, plus `reported_by=<Name>` for a named speaker or `reported_by=narrator` for the
  writer's "I": `A recent personal note mentioned that`, `it came up that`, `I noticed / I saw / I remember`,
  `The club newsletter states`, `I handed off the notes:`, `I was filing a reimbursement when ...`, `X said she ...`,
  `I, Ben Ito, helped ...`, `'X said, "I ..."'`, `'"...," the speaker said'`, `X: "..."`. Inside a frame,
  `I / me / he / she / they` = the named speaker; with no named speaker such a clause is not parsed.
- **Remark**: text after the core starting with `,` or a function word -> `remark=<text>` + canonical qualifiers for
  meaning words in it: `status=former` (no longer, in the past, has since ended, former ...), `freq=<...>`
  (every Tuesday, often, weekly ...), `time=<...>` (last week, recently ...), `remark_negated` (other negations).
  A remark that holds another clause is parsed too, not swallowed: `..., noting that A. Evans attends ...`,
  `..., which L. Evans recommended` (same object), `... and discussed radio society` (same subject),
  `..., while P. Khan and G. Ito both visited ...`, `..., who helped ...` -> extra facts with qualifier `embedded`.
- Between subject and verb: `also/simply/...` ignored; `previously` -> time=past, `recently` -> time=recent,
  `still/now` -> status=current, `formerly` -> status=former; `does not/never` -> `neg`; `no longer` -> status=former;
  `is not X` -> `neg`, `is no longer X` -> status=former; `had visited` = visited.
- **Normalizers**: `strip_garbage` (U+FFFD etc.), `verb_agreement` ("used to attends", "I attends" -> base form).

## Facts: subjects, relations, objects

Subjects are written name forms, title-cased: `Nadia Reed`, `N. Reed` (lower-case mentions are title-cased);
youths `Y055` (`Youth 55` joined); organizations `Organization 031` (`Org 31`, `org 031` joined). Always go
through `Facts.resolve` / `fx.of(pid)` to join forms. Objects are lower case without article.

| relation | object | qualifiers / notes | rule (file) |
|---|---|---|---|
| has_id | P-114 | `alias` for familiar names; from "the community roster records <name> under identifier P-114 and also uses the familiar names N. Reed" | roster (identity) |
| owns | camera, garden tools, guitar, telescope, sewing kit | `item_detail=set` | owns (activities) |
| recommended | atlas of clouds, long orchard, quiet machines, copper harbor | "suggested" too | recommended |
| discussed | a place/group/title; sometimes longer ("market trends") -> match with startswith | "talked about", "mentioned the" | discussed |
| visited | market, museum, library, sports hall, riverside park | `time=past` (some time ago / in the past / previously), `time=recent` | visited |
| helped | the place | `task=setup|cleanup|registration` | helped |
| attends | chess club, garden circle, history group, radio society, walking group | `status=former` for "only in the past", "used to attend", "previously attended", "used to be a member of"; no status = current | attends_group (groups_events) |
| attends (youth) | evening_language, evening_pottery, evening_carpentry, evening_accounting, daytime_first_aid | `status=current`, `when=evening|day` | youth_course (diet_family) |
| volunteered | event id (`event-P-114-0`, `old-event-P-030`) | `time=this_year` / `time=last_year` | volunteered |
| took_part_in | repair class, pottery class, language class | `role=teacher|student|observer|organizer`, `time=this_year`; "taught X class" -> role=teacher | took_part_class |
| works_for | Organization NNN | `status=current` ("currently"), `status=former` ("used to work", "worked") | works_for (work_travel) |
| based_in (subject = org) | city | Halifax, St. John's, Vancouver, Victoria, Lunenburg (coastal); Edmonton, Calgary, Ottawa, Regina, Winnipeg (inland) | based_in |
| works_shift | night, day | `status=former` ("in a former role", "used to work", "stopped working") | works_shift |
| travels_by | bus, tram, subway, train | `freq=routine` ("routinely travels by", "takes the X every day"); + `status=former` ("but no longer does", "used to"); `freq=once` ("used the X once"); `time=future` ("plans to use") | travels_by |
| prefers | train over plane | `genuine`, `when_both_available` | train_vs_plane |
| chose | train over plane | `reason=disruption`, `only_because` (a distractor, NOT a preference) | train_vs_plane |
| likes_equally | train and plane | (NOT a preference) | train_vs_plane |
| avoids | dairy products / cheese / milk / butter / yogurt | `status=current` ("currently chooses to avoid"); `temporary` ("is temporarily skipping cheese") | avoids_food (diet_family) |
| enjoys_eating / dislikes_eating | a food | `status=former` for "used to enjoy", "enjoyed ... in the past" | eating_taste |
| buys_for_others / serves_to_others | a food | "serves X to other people but does not eat it" also gives `eats X [neg]` | food_for_others |
| guardian_of | Y055 | `neg` from "emergency contact, but not a guardian" | guardian |
| emergency_contact_for | Y055 | | guardian |

Ignored clauses: `passage_intro` ("The appointment note recorded a few pieces of background.") and
`narrative_filler` (writer's glue naming nobody and using no fact words, e.g. "I recently traveled and had a few
expenses to account for."). Neither takes a clause any template rule can parse.

## Query conventions used (all four training answers were computed this way)

- "currently" = `current(f)`: no `status=former`, `neg`, `temporary`, `freq=once`, `time=future`.
- Reported facts (`reported`, `reported_by=...`) are accepted as true, including a person's own quoted "I ...".
- Employer in a coastal city: current `works_for` -> `based_in` city in `COASTAL_CITIES`.
- Ordinarily uses public transport: `travels_by` in `PUBLIC_TRANSIT` (bus, tram, subway, train, ...) with
  `freq=routine` and current. "used the tram once" and "plans to use the bus" do not count.
- Volunteered at N distinct events this year: distinct `volunteered` objects with `time=this_year`
  (`helped` facts are not events).
- Taught a class this year: `took_part_in` with `role=teacher` and `time=this_year` (organizer/observer/student no).
- Guardian of someone attending an evening course: current `guardian_of` Y (not `neg`) and Y `attends`
  `evening_*` currently. Emergency contacts are not guardians.
- Avoids dairy: `avoids` "dairy products" current (temporary skipping of cheese/milk does not count; neither does
  buying cheese for others or disliking milk).
- Fruit: `enjoys_eating` with object in `FRUITS` (lentils, bread, rice are not fruit), current.

## Manual entries and known limits

`train/docN.manual.jsonl` holds 7 clauses with cross-sentence anaphora ("He used to attend ..." after "I remembered
Samir Jones", "helped with setup there"), the narrator as subject ("I visited the museum with A. Foster"), and
"mentioned keeping a sewing kit". New documents will have a few such clauses; resolve them by hand the same way.
Not covered on purpose (they come out as `unparsed`, not as wrong facts): pronoun subjects with no speaker in the
same clause, frequency words the grammar does not know ("rarely takes the bus"), a remark holding a clause that no
rule parses. Remarks keep their full text, so unusual meaning can still be checked with `remark=` qualifiers.
