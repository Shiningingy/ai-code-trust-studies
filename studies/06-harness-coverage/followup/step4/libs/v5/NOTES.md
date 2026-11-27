# Notes for later sessions (library `lib/`, reconciled from lib_a, lib_b, lib_c)

Base is lib_a (fewest unresolved clauses, fewest manual rows); decisions per diff group are in `RECONCILE.md`.

Run: `python -m gram test --lib lib`; `python -m gram parse train/docN.md --lib lib --manual train/docN.manual.jsonl --out out/N`.
Answers: `python lib/tools/query.py .` (set env TMP to an output folder) parses the four training documents and writes
`answers.json`; `answer()` in `lib/tools/query.py` holds the four queries (copy it for a new one). All four documents have
0 unresolved clauses; each query gives exactly 5 people (same with or without plain `avoids`)..

## Shape of the text
One line = a passage: a scene-setting sentence (ignored) + sentences `NAME verb-phrase [tail]`, chained with ", and" / ", but" /
";" / lists, wrapped by neutral openers ("In a separate update,", "The same account also says that", "A recent personal
note mentioned that"), reporting frames ("I noted that", "The speaker said that") or quotations (`X said, "I ..."`,
`X: "I ..."`, `X wrote in the volunteer log, "I ..."`). Noise: case ("elena jones", "p-066"), "I attends", free tails
("..., which he uses to ...").

## Parts (lib/parts)
- `splitter.py` sentence_clause; `normalizers.py` (quotes, name case, id case, sentence-initial case).
- `core.py` (helper, not a part): `ClauseRule` = [opener] SUBJECT PREDICATE [tail]. Initials expand to the roster first name
  ("N. Reed" -> "Nadia Reed"). `I` = the speaker named by `X said, "I`, `X: "I`, `X wrote in the log, "I`, `I, X, can confirm`;
  with no speaker the subject is `narrator`. Tail: `TAIL_Q` words become qualifiers; a second claim in the tail about the
  same subject (", and she also visited X", " and discussed Y afterward") is read through all rules (`_coordinated`); other
  tail text is commentary. `finish` adds the single qualifier `past` to any fact whose wording says it no longer holds
  (some time ago, in the past, only in the past, previously, used to, no longer, in a former role, last week ...); the original
  words stay too. Neutral openers add no qualifier; reporting frames add `reported`, quotes `quoted` / `said`.
- `facts_basic.py`: recommended, discussed (also `A and B` topics, ", which N recommended"), owns, visited, helped_with,
  volunteered (year from `during X`, else the opener, else the id: `old-event-` = last-year).
- `facts_attend.py`, `facts_profile.py` (roster, works_for, based_in, works_shift), `facts_life.py` (travel, diet, classes,
  guardian / emergency contact, youth courses), `facts_wrap.py` (did_when, different_from, helped_when: one-off constructions
  that delegate to the plain rules), `ignore.py` (scene-setting, narrator remarks, bare attributions).
- Manual rows (`train/docN.manual.jsonl`, 7 clauses in doc1, doc2, doc4): first-person sentences of a quotation whose speaker
  was named in an EARLIER sentence with other sentences between, and "He ..." after "I remembered Samir Jones.". A clause
  cannot see the previous clause, so this is not grammar.

## Facts (subject, relation, object, qualifiers)
Subjects: full name ("Nadia Reed"), "Organization 030", "Youth 114", or `narrator` (unnamed speaker, 2 clauses). Names join to
ids through `has_id` (roster); `also_known_as` lists the short names. `works_for` -> Organization; `based_in` -> city;
`works_shift` day|night (`past` = former); `travels_by` (`routinely`; `past` = former habit); `used_transport` (`once`) and
`plans_to_use` are NOT habits; `prefers` (`genuinely`), `likes_equally`, `chose` (`only because of a disruption`): only a
`prefers` with `genuinely` is a real preference; `avoids` `dairy products` (`currently` or plain), `skips` (`temporarily`),
`buys_for_others`, `dislikes_eating`, `serves_to_others` (`does not eat it`), `enjoys_eating` (`past` = former);
`volunteered_at` event id with `this-year` / `last-year`; `took_part_in` "<kind> class" with `as the teacher|student|observer|organizer`
+ `this year`; `guardian_of` (`legal`) vs `emergency_contact_of` (never a guardian); `attends_course` (Youth) with `currently`
+ `during the evening|day`; `attends`, `visited`, `owns`, `recommended`, `discussed` (`about <word>`), `helped_with_<activity>`.

## Querying
Domain knowledge lives in `lib/tools/query.py`: COASTAL cities (Halifax, Vancouver, Victoria, Lunenburg, St. John's), PUBLIC
transport, FRUIT (lentils, bread, rice are not fruit), PAST qualifiers. For "current / ordinary" conditions exclude facts that
carry `past`, `temporarily`, `once`, `in the future`. Quoted / reported facts are true statements of the same world.
