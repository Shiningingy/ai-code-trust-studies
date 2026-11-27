# Community-records grammar: notes for later sessions

## Quick start

```
python -m gram test --lib lib
python -m gram parse train/doc1.md --lib lib --manual train/doc1.manual.jsonl --out out/doc1
```
Then query with `lib/facts.py` (run from the project root, or put `lib` on `sys.path`):
```python
from facts import Facts
F = Facts("out/doc1/parsed.jsonl")
F.persons()                     # every person ID (P-###) known from the roster
F.of("P-114", "works_for")      # facts about a person, any written form of the name joined in
F.about("Org 013", "based_in")  # facts about an organization or a youth (Y###)
F.current(f)                    # False if neg / status:former / status:planned / status:temporary / freq:once
F.has(f, "role:teacher", "when:this year")
```
`lib/answer_train.py` answers the four training queries this way and is the template to copy. For a new
document with no manual file, pass any non-existent path to `--manual` (or omit it).

## How a line is built

A document is `### Passage` headings and one content line per passage. The splitter (`sentence_clauses`,
`parts/framing.py`, logic in `lang.split_clauses`) cuts a line:
1. into sentences at `.`/`!`/`?` (also after a closing quote), but not after an initial (`N.`) or `St.`/`Dr.`,
   and never inside quotation marks (an unclosed quote runs to the end of the line);
2. inside a sentence, outside quotes, at `, and` / `, but` / `, while` / `, whereas` / `;` / `,` / ` and ` /
   ` while ` when what follows starts a new clause: a name followed by a predicate verb (`VSTART` in lang.py),
   `NAME and NAME both`, `the community roster`, `Org NNN`, `Youth NNN`; after `, and|but` also `I`/`we`/`it`.
   `he/she/they` are NOT split off: "X recommended Y, and she also visited Z" stays one clause and the pronoun
   clause is attributed to X.

Each clause is read as `[opener]* SUBJECT VP (and VP)* [modifiers] [tail]` (engine: `parts/lang.py`):
- **discourse openers** carry no meaning and are dropped: "In a separate update,", "Elsewhere in the note,",
  "Unrelatedly,", "Meanwhile,", "Then", any "In/During/At/As/For ... ," phrase, "I was ... when", "I filed ... after".
- **evidential openers** are kept as qualifiers: `source:<frame>` ("source:the same account also says",
  "source:a recent personal note mentioned", "source:the record shows") or `reported_by:<Name>` when a person
  reports ("Kofi Silva noted that ...", "I noted that ..." -> reported_by:narrator). "NAME said he/she VP" makes
  NAME the subject (reported_by:NAME).
- **subjects**: person name (full "Nadia Reed" or initial "N. Reed", any case — canonicalised to "Nadia Reed",
  "N. Reed"), "I" (= the speaker inside quotes, else `narrator`), "I, omar foster, ..." (= Omar Foster),
  "NAME and NAME both", he/she/they (unresolved -> subject "he"/"she" + `coref:pronoun`), `Org NNN`
  (canonical `Org 013`), `Youth 43`/`Y043` (canonical `Y043`), "the community roster records NAME|me".
- **modifiers** after the object: time phrases -> `when:<phrase>` (some time ago, in the past, previously,
  recently, last weekend, on saturday, this year...), frequency -> `freq:<phrase>` (routinely, every morning,
  on weekends, once), plain prepositional phrases ("to the group", "with the team") are dropped.
- **tail**: commentary after a comma / which / that / so / while / having / ... is dropped, except: past
  markers in it ("though only in the past", "but she no longer does", "a membership that has since lapsed")
  add `status:former` to stative facts; a pronoun clause ("..., and she also visited the museum") is parsed for
  the clause's subject; an embedded clause about another capitalised name ("in contrast to Farah Patel, who
  visited the sports hall", "unlike Quinn Ortiz, who owns a camera") gives extra facts.
- **negation** "does not / never / is not" + VP -> same facts with qualifier `neg`.
- **quotes** (`reported_speech`): `NAME said|says|explained|added|concluded|...|: "..."`, `"...," the speaker
  said [in ...]`, `"...," NAME noted, "..."`, bare quotations. The quotation is split and parsed with the whole
  grammar; "I" is the speaker; every fact gets `reported_by:<speaker>` (`narrator` for I, `unknown` for a bare
  quote, `the speaker` etc. otherwise).

## Families of parts

| part (file) | covers | relation(s) |
|---|---|---|
| possession (possession.py) | owns a X / owns X / owns a X set / has X / I keep my X / mentioned keeping a X | `owns` |
| recommendation (books.py) | recommended / suggested TITLE | `recommended` |
| discussion (discussion.py) | discussed / talked about / mentioned X; "market trends" -> object market + `aspect:trends` | `discussed` |
| attendance (attendance.py) | attends the GROUP [only in the past]; used to attend; previously/formerly attended; no longer attends | `attends` |
| visit (visits.py) | visited / went to PLACE [time] | `visited` |
| helping (helping.py) | helped / assisted with TASK at PLACE | `helped_with` TASK, `at:<place>` |
| volunteering (volunteering.py) | volunteered at event-P-051-0 during this-year / old-event-P-145 during last-year | `volunteered_at` EVENT, `when:this year`/`when:last year` |
| employment (work.py) | [currently] works for Org/Organization NNN; works the night/day shift [in a former role]; used to work ... | `works_for` "Org NNN", `works_shift` night/day |
| org_location (work.py) | Org NNN is based in CITY | `based_in` (subject "Org NNN") |
| transport (transport.py) | routinely travels by X [but no longer does]; used to (routinely) travel by / take the X; used the X once; plans to use the X in the future | `travels_by` |
| travel_preference (transport.py) | genuinely prefers A to B; likes A and B equally; chose A over B (only) because of a disruption | `prefers`, `likes_equally`, `chose_over` |
| diet (diet.py) | currently chooses to avoid X; avoids X; is temporarily skipping X; buys X for other people; dislikes eating X; enjoys eating X [in the past]; used to enjoy / enjoyed eating X; serves X to other people but does not eat it | `avoids`, `buys_for_others`, `dislikes_eating`, `enjoys_eating`, `serves_to_others` |
| classes (people.py) | took part in X class as the ROLE this year; taught X class | `took_part_in` "repair class", `role:<teacher/student/observer/organizer>` |
| guardianship (people.py) | is the legal guardian of Y###; is (listed as) an emergency contact, (but) not a guardian, for Y### | `guardian_of`, `emergency_contact_for` + `neg:guardian` |
| youth_course (people.py) | Youth NNN currently attends evening_language during the evening | `attends_course` (subject Y###), `during:evening/day` |
| roster (people.py) | The community roster records/lists NAME under identifier P-### [and also uses the familiar names N. X] | `has_name`, `has_alias` (subject P-###) |
| mixed_coordination (framing.py) | one subject, predicates of different families joined by "and" | any |
| relative_clause (framing.py) | "NAME, who VP, ..." and "That is different from NAME, who VP." | any |
| reported_speech (framing.py) | quotations, see above | any |
| filler (framing.py, ignore) | sentences with no name / ID / org / youth / event and no predicate | — |
| straight_quotes, verb_agreement (framing.py, normalizers) | curly quotes; "I attends", "used to attends", "NAME volunteer at event" | — |

## Facts: naming conventions

- `subject`: canonical person name as written ("Nadia Reed" or "N. Reed"), `narrator`, a pronoun (see coref),
  `Org 013`, `Y043`, or `P-114` (roster facts).
- `object`: lower case, leading article and "set of" removed: "garden tools", "chess club", "long orchard"
  (book titles too: "The Long Orchard" -> "long orchard"), "dairy products", "night", "subway",
  "event-P-051-0", "Org 018", "St. John's" (cities keep their case), "evening_language".
- qualifiers (a list of strings):
  - `status:current` (explicit "currently"/"still"/"now"), `status:former` (only in the past, used to, no longer,
    in a former role, previously/in the past on states), `status:planned` (plans to ... in the future),
    `status:temporary` (temporarily skipping)
  - `when:<phrase>`, `freq:<phrase>` (`freq:routinely`, `freq:once`)
  - `neg` (negated), `neg:guardian` (emergency contact but not guardian), `neg:eats` (serves but does not eat)
  - `role:<x>`, `at:<place>`, `during:<evening|day>`, `aspect:<noun>`, `over:<b>`, `and:<b>`, `genuine`,
    `reason:<x>`, `only_because`
  - `reported_by:<Name|narrator|unknown|the speaker|Y###>`, `source:<evidential frame>`, `coref:pronoun`

## Joining an entity's forms

- Every written form is canonicalised (case of names fixed: "elena Jones", "omar foster" -> "Elena Jones",
  "Omar Foster"; "c. Patel" -> "C. Patel"; "Organization 7" -> "Org 007"; "Youth 43" -> "Y043").
- The roster gives `P-### has_name <full>` and `has_alias <familiar>` -> `Facts.pid(name)`.
- Sometimes the roster records only the initial form ("F. Silva") while the text says "Farah Silva", or only
  the full name while the text says "A. Haddad". `Facts.pid` falls back to "same first initial + surname" when
  exactly one person ID has a roster name of that shape (two different full first names never merge).
- Pronoun subjects (`coref:pronoun`, a handful per document, e.g. "He used to attend ...") are resolved by
  `Facts` to the last capitalised full name earlier in the same line.

## Query semantics that the training queries confirmed (all 4 traps per condition exist in the data)

- "works for an organization based in a coastal city": `works_for` (current) -> `based_in` of that Org.
  Coastal in these docs: Halifax, St. John's, Vancouver, Victoria, Lunenburg; inland: Regina, Edmonton, Ottawa,
  Calgary, Winnipeg.
- "ordinarily travels using public transportation": `travels_by` bus/tram/subway/train with `freq:routinely`
  and not `status:former`. Not: `freq:once` ("used the bus once"), `status:planned`, "but no longer does".
- "currently works a night shift": `works_shift night` without `status:former` ("in a former role", "used to").
- "volunteered at three or more distinct events this year": distinct `volunteered_at` objects with
  `when:this year` (old-event-... during last-year does not count).
- "currently chooses to avoid dairy products": `avoids dairy products` not `status:temporary`
  ("temporarily skipping cheese" is a trap, so are `buys_for_others` and `dislikes_eating`).
- "guardian of someone currently attending an evening course": `guardian_of Y###` (not
  `emergency_contact_for`) and that youth's `attends_course` with `during:evening` / `evening_*`.
- "genuinely prefers train travel to flying": `prefers train` with `genuine`; not `likes_equally`, not
  `chose_over` (disruption).
- "enjoys eating something that is a fruit": `enjoys_eating <fruit>` current (not "in the past", not
  `serves_to_others`, not `dislikes_eating`); bread / rice / lentils are not fruit.
- "has personally taught a class this year": `took_part_in` with `role:teacher` and `when:this year`
  (student / observer / organizer do not count).
- Facts from quotes and evidential frames (`reported_by`, `source`) were counted as true; that gave the
  expected answers.

## Known limits

- Names are two tokens ("First Last" or "F. Last"); a three-token name would not be recognised.
- `VSTART` (lang.py) lists the verbs that may start a clause after a name; a new predicate verb should be added
  there as well as registered in a family file, or "A VP1, B VP2" lists will only be caught through the tail.
- Truly free narrative ("I was at the library for a cleanup when Kofi Mensah helped.") goes to
  `train/docN.manual.jsonl`; there are 2 such rows in the training docs.
- To add a predicate: `lang.register(family, regex, build, subj=("person",), stative=...)` in a family file,
  using `{O}` (object), `{M}` (modifiers), `{ORG}`, `{YOUTH}`, `{NAME}`; give the Rule an example.
