# Community-records grammar library — notes for later sessions

Built from lib_c, reconciled with lib_a and lib_b; `RECONCILE.md` records each decision. State on the training set:
`python -m gram test --lib lib` passes, every clause of doc1-3 is resolved (parsed, ignored, or one of 4 manual rows),
and `answers.json` comes from `python lib/query_examples.py`. All three source libraries gave the same three answers.

## Running it

```
python -m gram test  --lib lib
python -m gram parse <doc.md> --lib lib --manual <doc.manual.jsonl> --out out/<doc>
```
Then query `out/<doc>/parsed.jsonl` with `lib/query.py`; `lib/query_examples.py` answers the three training queries and
writes `answers.json` (see "Querying" below). Parsing a 9k-line document takes
about 3 s. Start a new document by parsing it, then read `outliers.jsonl`: it should be empty or nearly so.

## Layout

| file | what it holds |
|---|---|
| `parts/common.py` | the whole grammar, shared by every part: name/ID tokens, core predicates (`CORES`), modifiers, openers, tails, the splitter logic, speech and linked-clause frames, `analyze()` |
| `parts/splitting.py` | splitter `sentence_clause`; normalizers `straight_quotes`, `squash_spaces`, `name_case` |
| `parts/people.py` | rules `roster`, `org_location`, `employment`, `shift` |
| `parts/travel.py` | rules `travel_mode`, `travel_preference` |
| `parts/food.py` | rule `diet` |
| `parts/community.py` | rules `volunteering`, `guardianship`, `youth_course` |
| `parts/activities.py` | rules `ownership`, `recommendation`, `discussion`, `attendance`, `visit`, `helping` |
| `parts/frames.py` | rules `reported_speech`, `linked_clauses`; ignore-rules `commentary`, `contrast_remark` |
| `query_examples.py` | the eight condition functions of the training queries; writes `answers.json` |
| `query.py` | loads parsed facts, joins name forms to person IDs, world-knowledge sets (coastal cities, fruits, public transport) |

Each rule is a `FamilyRule`: `common.analyze(clause)` decides the clause's family once (cached), and the rule of that
family returns the facts. So a clause can never be claimed by two rules. To add a construction, add a `@core(...)`
predicate (or an opener / frame) in `common.py`, then put an example in the matching part.

## Grammar (how the text is built)

- **Line** → sentences. Sentences end at `.`/`!`/`?` outside quotes; never after a one-letter initial (`N. Reed`) or
  `St.` (`St. John's`). A quotation is never cut: `P said, "I own a camera. Q visited the museum."` is one clause.
- **Sentence** → clauses at `, and` `, but` `, while` `, whereas` `;` `,` ` and `, but only where a new clause starts
  after the connector: a name + predicate verb, `the community roster`, `Org 012`, `Y034`/`Youth 034`, `I <verb>`,
  `that <name> <verb>`, `P and Q ...`. Otherwise the rest stays with the clause as its *tail*.
- **Clause** = `OPENER* SUBJECT predicate MOD* TAIL?`
  - OPENER: discourse markers (`In a separate update,`, `Elsewhere in the note,`, `Unrelatedly,`, `Meanwhile`,
    `During the shift handoff,`, `According to the speaker,`, `At the market,` — the last one supplies the place for
    `helped with registration`), reporting frames (`The observer noted that`, `A recent personal note mentioned that`,
    `The same account also says that`, `I observed`, `It came up that`, `My meeting notes record`), narrator
    circumstances (`I was filing the reimbursement when`, `I filed ... after`). Reporting frames add qualifier
    `reported` (for every family, roster and org location included); markers add nothing.
  - SUBJECT: `Nadia Reed`, `N. Reed`, any case (`nadia reed`, `elena Jones`, `c. Patel`), `I` inside a quotation
    (= the speaker), `he/she/they` in a tail (= the clause subject), `I, omar foster,`; `Youth 012`/`Y012` for youth
    courses (canonical `Y012`); `Org 012`/`Organization 012` for locations (canonical `Org 012`).
  - MOD: time / frequency phrases right after the predicate (table `MODS`).
  - TAIL: commentary after a comma or linking word (`, a task that took several hours`, `to the group`, `with the
    team`). Tails are scanned: past markers (`no longer`, `has since lapsed`, `that is in the past`, `a former role`,
    ... — `PAST_TAIL`) add `past`; `, and she also visited X` / ` and owns a guitar` add facts about the same subject.
    A tail that names another person or an identifier together with a fact word is rejected, so such facts are never
    swallowed (the clause becomes an outlier instead).
- **Frames**: quotations (`P said/explains/added, "..."`, `P: "..."`, `"...," the speaker noted`, `"...," P said`,
  `I ..., noting, "..."`, `P said he/she ...`): every quoted sentence is parsed, `I` = speaker, all facts get
  `reported`. Linked clauses: `X, in contrast to P, who ...`, `X, which P recommended`, `X, which is different from
  how P ...`, `P and Q both ...`, `I visited the museum with P`, `I was at the market when P helped with registration`.
- **Ignored**: passage headers and narrator remarks (`The appointment note recorded a few pieces of background`,
  `it was a notable visit`) — only if they contain no predicate word, no name, no number and no meaning-changing word;
  `The contrast between the A and the B was noted` remarks.

## Facts

Every fact: `{"subject", "relation", "object", "qualifiers"}`. Person subjects are name forms exactly as written but
capitalised (`Nadia Reed`, `N. Reed`) — join them to IDs with `query.py`.

| relation | subject | object | qualifiers / notes |
|---|---|---|---|
| `has_name` | `P-114` | `Nadia Reed` (sometimes only `F. Silva`) | from the roster |
| `has_alias` | `P-114` | `N. Reed` | |
| `based_in` | `Org 012` | city, title case (`St. John's`) | |
| `works_for` | person | `Org 012` (`Organization 12` → `Org 012`, padded to 3 digits) | `currently`; `past` for used to work / worked |
| `works_shift` | person | `night` / `day` | `past` = "in a former role", "used to work" |
| `travels_by` | person | `bus` `train` `tram` `subway` | `routinely` (habit); `routinely`+`past` = "but no longer does"/"used to"; `once`; `future`+`planned` |
| `prefers` | person | `train over plane` | `genuinely`, `when both are available` — the real preference |
| `likes_equally` | person | `train and plane` | no preference |
| `chose` | person | `train over plane` | `only because of disruption` — not a preference |
| `avoids` | person | `dairy products` | `currently` |
| `skips` | person | `cheese` / `milk` / ... | `temporarily` — not the same as avoiding dairy |
| `buys_for_others` | person | food | not eating it |
| `enjoys_eating` | person | food (`banana`, `rice`, ...) | `past` = used to enjoy / "in the past" |
| `dislikes_eating` | person | food | |
| `serves_to_others` + `eats` | person | food | `eats` carries `negated` |
| `volunteered_at` | person | `event-P-122-1` / `old-event-P-075` | `this-year` / `last-year` ("this year" normalised) |
| `guardian_of` | person | `Y012` | `legal`; `negated` for "emergency contact, but not a guardian" |
| `emergency_contact_for` | person | `Y012` | |
| `attends_course` | `Y012` | `evening_pottery`, `daytime_first_aid`, ... | `currently`, `during the evening` / `during the day` |
| `owns` | person | `camera`, `garden tools`, `sewing kit`, ... | |
| `recommended` | person | title, lower case, no article: `long orchard`, `atlas of clouds` | |
| `discussed` | person | topic, lower case, no article: `market`, `chess club`, `long orchard` | `aspect:trends` for "market trends", `aspect:plans` for "garden circle plans" |
| `attends` | person | group: `chess club`, `walking group`, ... | `past` (only in the past, used to, no longer, formerly, lapsed); frequencies (`every morning`, `on weekends`, `regularly`) |
| `visited` | person | place: `market`, `library`, `museum`, `sports hall`, `riverside park` | `some time ago`, `past` (in the past/previously), `recently`, `last week`, ... |
| `helped_with_setup` / `_registration` / `_cleanup` | person | place | |

Qualifier vocabulary: `past`, `currently`, `once`, `future`, `planned`, `routinely`, `temporarily`, `negated`,
`legal`, `genuinely`, `when both are available`, `only because of disruption`, `this-year`, `last-year`,
`some time ago`, `recently`, `during the evening`/`during the day`, `with narrator`, literal time/frequency phrases,
and `reported` (the fact was reported or quoted; it still counts as a fact — the training answers include them).

## Querying

```python
import sys; sys.path.insert(0, "lib")
from query import Facts, current, PUBLIC_TRANSPORT, COASTAL_CITIES, FRUITS
fx = Facts("out/doc1/parsed.jsonl")
for p in fx.people():                     # roster IDs
    jobs = [f for f in fx.of(p, "works_for") if current(f)]
    cities = [b["object"] for j in jobs for b in fx.about(j["object"], "based_in")]
```
- `fx.of(pid, relation)` gathers facts written under any name form of that person. `fx.about(subject, relation)`
  is the same for organisations and youths.
- `current(f)` is False for `past`, `future`, `planned`, `once`, `negated`. It does not drop `reported`.
- Name resolution: roster name/alias; otherwise initial + surname when exactly one roster person fits
  (`n. reed` → P-114, and `Farah Silva` → the roster person listed only as `f. silva`). In the training documents
  every first name had a distinct initial and every mention resolved; if a new document has two roster people with the
  same initial + surname, `pid()` returns None for the ambiguous short form.
- World knowledge the text does not give lives in `query.py`: `COASTAL_CITIES` (Halifax, Vancouver, Victoria,
  St. John's, Lunenburg; inland: Edmonton, Calgary, Ottawa, Regina, Winnipeg), `FRUITS`, `PUBLIC_TRANSPORT`, `DAIRY`.

Recipes that were checked against the training queries:
- "works for an organization based in a coastal city": current `works_for` → org → `based_in` ∈ COASTAL_CITIES.
  An organisation's city may be given only inside a quotation (`I know Org 027 is based in Lunenburg`).
- "ordinarily travels using public transportation": `travels_by` with `routinely` and not `past`
  (`once`, `planned`, "but no longer does" are distractors).
- "currently works a night shift": `works_shift` `night` without `past` ("in a former role" is the distractor).
- "volunteered at three or more distinct events this year": distinct `volunteered_at` objects with `this-year`
  (old-event ... last-year are distractors).
- "currently chooses to avoid dairy products": `avoids` `dairy products` (not `skips` / `buys_for_others`).
- "is guardian of someone currently attending an evening course": `guardian_of` without `negated` → youth →
  `attends_course` with `currently` and `during the evening` (emergency contacts are distractors).
- "genuinely prefers train travel to flying": relation `prefers`, object `train over plane` (not `likes_equally`, not
  `chose`). Do not require the `genuinely` qualifier: "P. Foster prefers train to plane when both are available" (doc3
  line 8193) is a real preference without the word.
- "enjoys eating something that is a fruit": `enjoys_eating` without `past`, object ∈ FRUITS (lentils, rice, bread
  are not fruits).

## Manual rows (train/docN.manual.jsonl)

Only text no grammar should cover: a sentence whose subject is a pronoun naming someone from the previous sentence
(`He used to attend ...`, `Dev Ito helped with setup there`), and two free-running quoted monologues with
comparisons (`unlike Quinn Ortiz, who ...`, `what Elena Patel did when she visited ...`). Four rows in total: doc1 5081,
doc2 5753, doc3 501 and 1645. Their facts use the same naming as the rules.

## Things to know

- `Y012` and `Org 012` are the canonical forms (lib_a/lib_b's); `Youth 12`, `y012`, `Organization 12`, `org 012` all map
  to them.
- Book titles are stored lower case (`long orchard`), the same in `recommended` and `discussed`; compare topics
  lower case.
- The roster sometimes registers a person only by initials (`the community roster records f. patel under identifier
  p-006`); `has_name` is then `F. Patel`.
- The `commentary` ignore-rule refuses anything with a fact word, a name with an initial, a digit, or a word such as
  `not`, `no longer`, `used to`; such text shows up as an outlier instead of disappearing. If a new document
  produces outliers, first check whether a new verb form or opener is missing from `common.py` (`CORES`, `MARKER`,
  `REPVERB`, `SPEECH_V`, `MODS`, `ASPECTS`).
- Tails that look like facts but are not (fixed while reconciling; each has an example in the parts):
  `, which he used to show us the stars` / `, which was used to document the event` say what the object is for, so they
  do not make `owns` past (`past_tail()` removes `which/that (X) used to` before checking `PAST_TAIL`);
  `, and (she) mentioned the new equipment` is a remark, not `discussed`.
- A reporting frame may not contain a fact word (`FACT_SIGNAL`). `P owns a telescope, and she explained that Q ...`
  is the linked form `PRON_REPORT` (P's fact, plus Q's fact with `reported`), not a frame that drops P's fact.
- To check a change, diff the facts of `out/docN/parsed.jsonl` against the previous run line by line, with the
  `clause` index ignored. That comparison against lib_a/lib_b is how the fixes above were found.
