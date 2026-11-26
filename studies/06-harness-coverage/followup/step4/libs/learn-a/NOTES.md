# Notes for later sessions

Library for the "Community Records" documents: many short passages (lines) of templated sentences, then a final query.
Run: `python -m gram parse docN.md --lib lib --manual docN.manual.jsonl --out out`, then read `out/parsed.jsonl`
(`facts` per line; every fact is `{subject, relation, object, qualifiers, clause, line}`).
`lib/tools/facts_io.py` (loader + name/ID resolver) and `lib/tools/example_queries.py` (the three training queries
answered from the facts) are working examples; they read `work/outN/parsed.jsonl`, adjust the path as needed.
Set `PYTHONUTF8=1` on Windows (the documents contain U+FFFD characters).

## Layout of a line
A line = optional frame sentence + clauses. Clauses are joined by ". ", ", and ", ", while ", ", whereas ", ", but ", ";",
comma lists, or bare " and " before a new subject. Wrappers with no content are dropped by the splitter ("In a separate
update,", "Elsewhere in the note,", "The same account also says that", "I noted/observed/remember that", "A recent
personal note mentioned that", "it came up that", "Then", "The log notes", "Unrelatedly,", ...). Quote introductions are
kept inside the clause (`T. Tran said, "I visited the library`) so that "I" can be resolved to the speaker.
Trailing narrative ("a task that was completed efficiently", "which he uses for stargazing") is emitted as its own clause
and ignored (rules `no_fact_clause`, `narrative_tail`, `speech_tag`). Frame sentences ("The appointment note recorded ...")
are ignored the same way. Tails that change meaning stay attached to their clause ("..., but only in the past",
"..., but no longer does", "..., so the note marks it as past").

## Entities and names
* People: "First Last", "F. Last" (initial form), any case ("elena Jones", "k. reed"): canonical form is Title Case
  ("Elena Jones", "K. Reed"). Subjects are NOT replaced by P-ids: join them yourself.
* `The community roster records NAME under identifier P-NNN and also uses the familiar names ALIAS` gives facts
  `NAME has_id P-NNN`, `P-NNN has_name NAME`, `NAME also_called ALIAS` (the alias is the initial form). The "also uses" part
  is sometimes missing (then the roster NAME may itself be an initial form, e.g. `P. Mensah` -> P-156) and ~5% of persons
  have no roster line at all.
* `volunteered_at` clauses also emit `NAME id_hint P-NNN` ("from event id"): the P-id inside `event-P-118-0` is the
  volunteer's id. Use it to give ids to people without a roster line.
* Join recipe (see `facts_io.resolver2`): union all names that share an id (has_id, id_hint, also_called); then link
  "G. Foster" with "Gabriel Foster" when exactly one full name has that (initial, surname).
* Orgs: `Org NNN` (written Org / Organization / org, any case) -> canonical `Org NNN`. Youths: `Youth 077`, `Y077`, `youth 7`
  -> `Y077`. "I"/"he"/"she" are resolved to the speaker named in the quote introduction ("X said/added/explained, "I ...");
  otherwise the clause goes to manual (subject `narrator` when the narrator is the actor and unnamed).
* Objects are lower-case without article: `museum`, `sports hall`, `garden tools`, `atlas of clouds`, `long orchard`
  ("The Long Orchard" loses "The"). Known entities absorb trailing noun suffixes ("museum exhibits" -> `museum`);
  extend `KNOWN_ENTITIES` in `parts/common.py` when documents bring new places/groups/books/items.

## Relations (subject relation object; qualifiers)
* visited (place; `some time ago`, `in the past`, `previously`, `recently`, `last week`...), discussed (place/group/book;
  also "talked about", "mentioned"), recommended (book/destination), owns (item).
* attends (group; `only in the past`, `used to`, `no longer`, `previously`, `formerly`, `in the past`, `regularly`,
  `every week`, `on weekends`...).
* helped_with_setup / helped_with_cleanup / helped_with_registration (place).
* volunteered_at (event id; qualifier `this-year` or `last-year`; `old-event-...` ids go with `last-year`).
* works_for (`Org NNN`; qualifier `currently` when written), based_in (`Org NNN` -> city),
  works_shift (`day`/`night`; `in a former role`, `used to`, `formerly`).
* travels_by (mode; `routinely`; plus `no longer` / `used to` when it stopped), plans_to_use (mode; `in the future`),
  used (mode; `once`), likes_equally (`train and plane`), prefers_over (`train over plane`; `genuinely`, `when both are
  available`), chose_over (`train over plane`; `only because of a disruption`: a forced one-off, NOT a preference).
* avoids (`dairy products`; `currently`; the bare "avoids dairy products" variant has no qualifier but means the same),
  skips (`temporarily` skipping one dairy item), buys_for_others / serves_to_others (a food bought/served for others only;
  the latter has `does not eat it`), enjoys_eating / dislikes_eating (food; `in the past`, `used to`, `formerly` = no longer).
* attends_course (youth -> course; `currently`, plus `evening` or `day`), legal_guardian_of (person -> youth),
  emergency_contact_of (person -> youth; `not a guardian` when stated).
* has_id / has_name / also_called / id_hint (identity, see above).

## Querying: things that bite
* Always check qualifiers. "Current" means none of `no longer`, `used to`, `formerly`, `in a former role`, `only in the
  past`, `in the past`, `previously`. "Ordinarily travels by public transport" = travels_by (bus/train/tram/subway) with
  `routinely` and without `no longer`/`used to` (plans_to_use and used-once are distractors).
* "Coastal city" is outside knowledge: in these documents Halifax, Vancouver, Victoria, St. John's, Lunenburg are coastal;
  Calgary, Edmonton, Regina, Winnipeg, Ottawa are not. A person's org city = based_in of their works_for org.
* "n or more distinct events this year": count distinct volunteered_at objects with `this-year`.
* Fruit: apple banana pear mango peach orange plum watermelon (bread, rice, lentils are not). `serves_to_others` and
  `dislikes_eating` do not count as enjoying.
* Guardian of someone currently attending an evening course: legal_guardian_of -> Y, and Y attends_course with `evening`
  (courses named `evening_*`; `daytime_*` use `day`). `emergency_contact_of` with `not a guardian` is a distractor.
* Every person had exactly one fact of each profile kind (employer, shift, travel, diet, ...) in the training documents.
* Unrecognised tail words after a clause ("... for the walk", "... with the team") are dropped as details; only time,
  frequency and negation words are kept as qualifiers (`parts/common.py` `TIME_Q`). Extend it if new words appear.

## Manual rows (train/docN.manual.jsonl)
Only ~50 clauses in total: pronoun / relative-clause facts whose subject is in another clause ("she also visited the museum"),
first-person clauses after a split quote ("I helped with cleanup at the museum"), two facts in one clause, and free
narrative asides (ignored). Built by hand; subjects were taken from the neighbouring clause.

## Parts
* `parts/splitter.py` `clause_cutter` - sentence/clause cutting, wrapper stripping, tails.
* `parts/normalizers.py` `straight_quotes`.
* `parts/rules_activity.py` visited, discussed, recommended, owns, attends, helped, volunteered.
* `parts/rules_profile.py` works_for, based_in, shift, travel (routine, plans, used once, used to take), preferences,
  diet (avoids dairy, skipping, buys/serves for others, eating), roster, youth course, guardian, emergency contact.
* `parts/rules_ignore.py` no_fact_clause, narrative_tail, speech_tag (ignore-rules; they refuse clauses with fact words,
  so an unknown construction shows up as `unparsed` instead of being swallowed).
* `parts/common.py` shared regexes, canonical forms, qualifier extraction (`tail_quals`), `TAIL` (free tail after a core
  pattern).
