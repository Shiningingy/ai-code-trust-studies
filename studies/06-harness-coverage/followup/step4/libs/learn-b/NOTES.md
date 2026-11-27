# Notes for later sessions

Documents are lists of short passages ("### Passage D-xxxxx"), each a paragraph of sentences about people, then a
"Final Query" of conditions c1..cn. Run `python -m gram parse docN.md --lib lib --out out` and query `out/parsed.jsonl`
(one row per line, `facts` = list of facts, each with `subject, relation, object, qualifiers, clause`).
`lib/example_queries.py` shows how the three training queries were answered from the facts.

## Layout of lib/parts
- `splitter.py`: `clause_splitter` (sentences, then `,` `;` ` and <Name>`; drops connectors and/while/but/whereas/so and
  scene-setting intros "In contrast," "During the meeting,"; keeps lead-ins and meaning-bearing tails such as
  "but no longer does", "only in the past", "but not a guardian", "for Y123" inside their clause) and the normalizer
  `straight_quotes` (curly quotes -> straight).
- `common.py`, `common_stmt.py`: helpers (not parts). `Stmt` = base of "SUBJECT predicate" rules; clause shape is
  `[quote][lead-in] [I,] SUBJECT [said/says/explained... + I/he/she/they] [also] [no longer] PREDICATE [adjunct]`.
- `rules_basic.py`: owns, recommended, discussed, attends, visited, helped_with_*, volunteered_at, works_for,
  org_based_in. `rules_more.py`: works_shift, travels_by, used (once), plans_to_use, likes_equally, prefers, chose,
  avoids/skips/dislikes_eating/enjoys_eating/buys_for_others, went_to, talked_about, roster, conjoined predicates.
  `rules_youth.py`: guardian_of, emergency_contact, attends_course (youth ids), serves_not_eats, named attribution.
  `rules_ignore.py`: ignore rules (scene-setter sentences, filler commentary clauses, speaker tags). They only
  fire on clauses that contain no person, id or organization.
- Rules are case-insensitive (names appear as `elena Jones`, `d. bennett`, `p-066`).

## How facts are named
- Subject = person, written `First Last` (Title case). Initial forms `M. Laurent` are EXPANDED to the first name
  (the 20 first names have distinct initials), so one person has one subject string. Roster facts:
  `(Mateo Laurent, has_id, P-153)` and `(Mateo Laurent, also_known_as, M. Laurent)`. Person ID answers = `has_id` object.
  Orgs: `Org 004` (from "Organization 004"/"org 004"). Youths: `Y075` (from "Youth 075"/"y075").
- Objects are lower case with a leading "the/a/an" removed: `owns` camera|telescope|guitar|garden tools|sewing kit;
  `recommended`/`discussed` book|group|place (`long orchard`, `chess club`, `library`); `attends` group;
  `visited` place; `helped_with_registration|setup|cleanup` place (object `""` if no place given).
- Relations: owns, recommended, discussed, attends, visited, helped_with_<task>, volunteered_at (object = event id,
  qualifier `this-year` or `last-year`; "old-event-..." ids are last-year), works_for (Org N), based_in (Org N -> city, e.g.
  `St. John's`), works_shift (day|night), travels_by (bus|train|tram|subway|plane), used (vehicle, qualifier `once`),
  plans_to_use (qualifier `future`), likes_equally (two facts, one per vehicle), prefers (object = preferred vehicle,
  qualifiers `genuinely`, `over <other>`, `when both are available`), chose (qualifier `only because of a disruption`),
  avoids (object `dairy products`, qualifier `currently`), skips (qualifier `temporarily`), dislikes_eating,
  buys_for_others, enjoys_eating, serves_to_others (qualifier `does not eat it`), guardian_of / emergency_contact_of
  (object = youth id; "not a guardian" gives `guardian_of` with qualifier `not`), attends_course (subject youth, object
  `evening_pottery` ..., qualifiers `currently`, `during the evening|day`), has_id, also_known_as.

## Qualifiers (never drop them when querying)
- `past`: former/ended: "only in the past", "used to", "previously", "formerly", "no longer", "but no longer does",
  "some time ago" (visited), "worked ... in a former role" ("former role" is also added), "enjoyed".
  A fact WITHOUT `past` is present/unspecified. For "currently/ordinarily X" exclude `past`, `no longer`, `future`,
  `once`, `former role`.
- `reported`: the clause was quoted or introduced by a speaker/observer ("X said, \"I own...\"", "I noted that ...",
  "According to ..."). The content is still the speaker's claim about the subject; the training queries counted it.
- `currently`, `routinely`, `genuinely`, `temporarily`, `this-year`, `last-year`, `once`, `future`, `legal`, `not`.
- Any other adjunct ("to the group", "every morning", "on saturday", "as well", "with the team") is kept lower-cased as
  its own qualifier text; frequency words (regularly, every week) live there.

## Querying tips (how the training queries map)
- "works for an organization in a coastal city": works_for -> Org -> based_in city. Cities seen: Halifax, Victoria,
  Vancouver, Lunenburg, St. John's (coastal); Calgary, Edmonton, Regina, Winnipeg, Ottawa (inland).
- "ordinarily travels by public transport": travels_by in bus/train/tram/subway without `past` (the clause
  "routinely travels by X but no longer does" has `past`). "used the X once" / "plans to use" are NOT habits.
- "currently works a night shift": works_shift night without `past`/`former role`.
- "volunteered at >= 3 distinct events this year": distinct volunteered_at objects with qualifier `this-year`.
- "currently chooses to avoid dairy": `avoids` + `currently`; `skips`(temporary), `dislikes_eating`,
  `buys_for_others` are look-alikes that do not count.
- "guardian of someone currently attending an evening course": guardian_of (no `not`) -> youth -> attends_course with
  `currently` and an `evening_*` course. Emergency contacts are not guardians.
- "genuinely prefers train to flying": prefers object train with `genuinely`; likes_equally/chose do not count.
- "enjoys eating a fruit": enjoys_eating with a fruit object (banana, peach, apple, plum, mango, pear, watermelon,
  orange seen; lentils/bread/rice are not fruit), not `past`.

## Known gaps / manual
Each doc has `train/docN.manual.jsonl` for ~12-30 clauses of free text (relative clauses, "X and Y both ...",
first-person narrator sentences). Unseen free-text may need new manual rows. Filler commentary after a fact
(", which was a key task") is ignored by `ignore_filler_tail`; it is redundant with the fact clause.
