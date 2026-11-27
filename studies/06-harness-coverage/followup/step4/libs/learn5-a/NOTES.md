# Grammar notes (library `lib/`)

Run: `python -m gram parse docN.md --lib lib --manual docN.manual.jsonl --out out` (needs `PYTHONPATH` = repo root so
helper modules can import `gram`; the `gram` command already does this). `python -m gram test --lib lib` must pass.
`python lib/tools/query.py <repo root>` parses train/doc1..4 and writes answers.json using `lib/tools/query.py:answer`
(copy that function and change the conditions for a new query).

## Shape of the text
A document is many one-paragraph "passages" (lines). A paragraph = optional scene-setting sentence ("The appointment
note recorded a few pieces of background.") + sentences about people. Sentences join clauses with ", and", ", but", ";",
" and", lists with commas, or via linking phrases ("in contrast to X, who ...", "noting that X ..."). Clauses can be
wrapped by neutral openers ("In a separate update,", "Elsewhere in the note,", "Unrelatedly,", "The same account also
says that", "A recent personal note mentioned that", ...), by reporting frames ("I observed that", "The speaker said
that"), or by quotations (`X said, "I own a guitar. Y visited the market."`, curly quotes U+201C/D or plain). Inside a
quotation `I` is the speaker. Noise: wrong case ("elena Jones", "j. foster", whole lowercase lines, "p-066", "youth 007"),
"I attends" agreement slips, free elaboration after a fact (", which he uses to ...", ", a task that ...").

## Parts (all `added_by = "learning"`)
- `splitter.py` `sentence_clause`: sentences, then clauses. Does not cut `, and I ...` inside a quotation (speaker kept);
  cuts before a person introduced by a linking phrase (the phrase stays at the end of the previous clause).
- `normalizers.py`: `straight_quotes`, `name_case` (lower-case names), `id_case` (p-/y/youth/org ids), `sentence_initial_case`.
- `core.py` (helper, not a part): `ClauseRule` base = [opener] SUBJECT PREDICATE [tail]. Subject `NAME` is canonicalised:
  initials expand ("N. Reed" -> "Nadia Reed"; each initial is one first name in the roster). `I` takes the speaker of
  `X said, "I ..."`; with no speaker the subject is `narrator` (qualifier `speaker not named`). Opener -> qualifiers
  (`quoted`, `reported`, `said`, `hedged: <word>`). Tail (free text after the fact) is scanned by `TAIL_Q` for time /
  frequency / negation words which become qualifiers; the rest of the tail is ignored elaboration.
  `NAME and NAME both ...` gives one fact per person. `, and I ...` in a quote is re-parsed with all rules.
- `facts_basic.py`: recommended, discussed, owns, visited, helped_with, volunteered.
- `facts_attend.py`: attends (current/lapsed), used_to_attend (also "no longer attends").
- `facts_profile.py`: roster (id + aliases), works_for, org_based_in, works_shift.
- `facts_life.py`: travels_by, used_once, plans_to_use, travel_preference, diet, serves_not_eats, class_role, guardian, youth_course.
- `ignore.py`: ignore-rules for scene-setting sentences, narrator remarks, bare speech attributions.
- Manual: `train/docN.manual.jsonl` only for one-off free text (4 clauses in doc3/doc4).

## Fact vocabulary (subject, relation, object, qualifiers)
Subjects are canonical full names ("Nadia Reed"), "Organization 030", "Youth 114" (also written Y114), or `narrator`.
- `has_id` (name -> "P-114") and `also_known_as` come from the roster sentence: THIS IS THE JOIN TO PERSON IDS.
  Event ids contain the volunteer's id (`event-P-085-0`) but the roster is the authority.
- `works_for` -> "Organization NNN" (qual `currently`); `based_in` (Organization -> city). Coastal cities in the data:
  Halifax, Vancouver, Lunenburg, Victoria, St. John's (inland: Edmonton, Regina, Ottawa, Calgary, Winnipeg).
- `works_shift` -> day|night; qualifiers `in a former role` / `used to` mean NOT current.
- `travels_by` -> subway|bus|train|tram; qual `routinely`; `no longer` / `used to` => not ordinary any more.
  `used_transport` (qual `once`) and `plans_to_use` (qual `in the future`) are NOT habits.
  `prefers` ("train over plane", quals `genuinely`, `when both are available`), `likes_equally`, `chose`
  (qual `only because of a disruption`; not a real preference).
- `volunteered_at` -> event id, qual `this-year` or `last-year` (old-event-... ids). "N distinct events this year" =
  count distinct objects with `this-year` per person.
- `took_part_in` -> "<kind> class", quals `as the teacher|student|observer|organizer`, `this year`.
- `guardian_of` -> Youth NNN (qual `legal`); `emergency_contact_of` (qual `not a guardian`) is NOT a guardian.
  `attends_course` (subject Youth) -> evening_x / daytime_x, quals `currently`, `during the evening|day`.
- diet: `avoids` "dairy products" (qual `currently`), `skips` (qual `temporarily`), `buys_for_others`, `dislikes_eating`,
  `serves_to_others` (qual `does not eat it`), `enjoys_eating` (qual `used to` when past). "Is a fruit" needs a fruit list
  (see FRUIT in lib/tools/query.py; lentils, bread, rice are not fruit).
- `attends` (group): quals `only in the past`, `in the past`, `used to`, `no longer`, `previously` mean lapsed.
  `visited` quals `some time ago`, `in the past`, `previously`, `last week`...; `owns` item (garden tools, camera, ...);
  `recommended` book title; `discussed` topic (place/group/title; extra word such as "market trends" -> qual `about trends`);
  `helped_with_setup|registration|cleanup` -> place.

## Querying tips
- Quoted/reported facts (quals `quoted`, `reported`, `said`) are statements of the same world: including them gave
  exactly 5 answers per training document, excluding them gave 1-3; they are treated as true.
- Always exclude facts whose qualifiers say past/former/negated (see PAST in lib/tools/query.py) when a question says
  "currently"/"ordinarily".
- Check `has_id` exists for every answer (query.py prints people without one).
- Run the audit idea: parsed clauses whose text still contains a second person name may hide a fact in an ignored tail.
