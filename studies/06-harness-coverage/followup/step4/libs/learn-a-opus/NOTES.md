# Community-records grammar: notes for later sessions

## Run it

```
python -m gram test --lib lib
python -m gram parse <doc.md> --lib lib --manual <doc.manual.jsonl> --out out/<doc>
python lib/query_examples.py        # worked example: the 3 training queries -> answers.json
```

`lib/kb.py` (not a part) loads `parsed.jsonl` and joins every name form to a person id:
`k = kb.KB("out/doc1/parsed.jsonl")`; `k.people()` (all ids), `k.of(pid, relation)`, `k.entity("Org 027", "based_in")`,
`kb.KB.current(f)`, `kb.KB.has(f, "routinely")`, `kb.KB.qual(f, "period")`. Copy a condition function from
`lib/query_examples.py` and adapt it; that is usually all a new query needs.

State on the training set: every clause of doc1-3 is resolved (parsed, ignored, or one of 7 manual rows); the three
answers in answers.json come from the facts.

## Document shape

`### Passage D-xxxxx` headings, then one content line per passage: 1-6 sentences, each sentence 1-5 clauses. The
query follows `### Final Query`. Facts about one person are scattered over many passages; the person's id appears only
in a roster sentence.

## Parts, by family

| file | parts | covers |
|---|---|---|
| `common.py` | (no parts) | entity patterns, canonical names, the splitter logic, object slots, the tail parser, base class `Core` |
| `splitter.py` | `record_splitter` | sentences (initials `N.`, `St.` are not ends); a quoted span plus its speaker frame = one clause; a leading opener = its own clause; connectors `, and` `, while` `, but` `, whereas` `;` `,` `and` `, and that` split only when SUBJECT + predicate word follows (so `, and it was a busy day` stays as a remark); `A and B both ...` is not split |
| `normalizers.py` | `straight_quotes`, `spacing_repair` | curly quotes -> `"`; doubled spaces / space before punctuation |
| `activities.py` | `recommended`, `discussed`, `owns`, `helped_with`, `visited`, `attends_group`, `volunteered` | community activities |
| `work.py` | `works_for`, `works_shift`, `org_based_in` | employer, shift, org city |
| `travel.py` | `routinely_travels`, `used_transport_once`, `used_to_take_transport`, `plans_to_use_transport`, `prefers_mode`, `likes_modes_equally`, `chose_mode_over` | transport habits and train/plane preference |
| `food.py` | `avoids_food`, `temporarily_skipping`, `enjoys_eating`, `dislikes_eating`, `serves_food_to_others`, `buys_food_for_others` | diet and food |
| `family.py` | `legal_guardian`, `emergency_contact`, `youth_attends_course` | youths (Y###) |
| `roster.py` | `roster_record` | person ids and aliases |
| `openers.py` | `discourse_opener`, `framing_sentence` (ignore-rules) | "In a separate update,", "Elsewhere in the note,", "The same account also says that", "I observed that", "During the meeting,", "As a direct observer, I noted that"; entity-free framing sentences ("The appointment note recorded a few pieces of background."). Both REFUSE text containing a time/negation/hedge word (past, previously, ago, last, not, never, maybe, ...) so such text surfaces as unparsed instead of being dropped |
| `speech.py` | `quoted_speech`, `said_pronoun_clause`, `self_introduction` | `X said, "..."`, `X: "..."`, `"...," the speaker explains.`; `X said he ...`; `I, omar foster, helped ...` |
| `composite.py` | `compound_subject`, `embedded_who_clause`, `which_other_did`, `witnessed_doing`, `scene_when`, `pre_verb_modifier` | `A and B both ...`; `..., in contrast to X, who ...`; `..., which X recommended`; `I saw X help ...`; `I was at the <place> when ...`; `X does not / no longer / will / usually / reportedly <verb> ...`, `X stopped <verb>ing ...` |

Every clause rule is `SUBJECT + fixed wording with slots + TAIL`. The TAIL (common.tail) turns known modifiers into
qualifiers and keeps anything else that starts like a remark (`,`, a preposition, an -ing/-ly word) as `note:<text>`.
A remark that contains another clause (a person/org/youth followed by a predicate word, or `X, who`) is refused, so a
hidden fact is never swallowed. The composite rules (speech/composite) re-split their text and call the clause rules
through `speech.parse_inner`.

## How facts are named

`{"subject", "relation", "object", "qualifiers"}`. Subjects/objects are canonical:

* person: `Nadia Reed` or `N. Reed` (each token capitalised; the rules never expand an initial). `I` = the
  first-person speaker; inside quotes it is replaced by the speaker, so `I` survives only for an unnamed narrator.
* org: `Org 027` (from `Org 027`, `Organization 027`, `org 027`); youth: `Y045` (from `Youth 045`, `Y045`, `youth 045`);
  person id: `P-114`; events: `event-P-027-1`, `old-event-P-061`.
* other objects: lowercase, leading article/possessive dropped: `sports hall`, `chess club`, `long orchard`
  (= "The Long Orchard"), `atlas of clouds`, `garden tools` (also from "garden tools set/kit", "set of garden tools").

| relation | object | qualifiers it may carry |
|---|---|---|
| `has_id` | `P-114` | (roster) |
| `also_known_as` | alias, e.g. `N. Reed` | (roster) |
| `recommended` | title | |
| `discussed` | topic (title, place or group) | `aspect:trends` (from "market trends", "radio society membership updates") |
| `owns` | item | |
| `helped_with` | task: `registration` / `setup` / `cleanup` | `at:<place>` |
| `visited` | place | `past` for "some time ago", "in the past", "previously" |
| `attends` | group | `past` for "only in the past", "used to attend", "previously attended", "no longer attends", ", but no longer does"; `current` if "currently" written |
| `volunteered_at` | event id | `period:this-year` / `period:last-year` |
| `works_for` | `Org 027` | `current` ("currently"), `past` |
| `works_shift` | `night` / `day` | `past` ("in a former role", "used to work") |
| `based_in` (subject org) | city, title case, `St. John's` | |
| `travels_by` | `bus` / `subway` / `tram` / `train` | `routinely` (habit), `once` (single trip), `future` ("plans to use"), `past` ("but no longer does", "used to") |
| `prefers` | `train` | `over:plane`, `genuinely`, `when both are available` |
| `likes_equally` | `train and plane` | |
| `chose` | `train` | `over:plane`, `reason:only because of a disruption` |
| `avoids` | `dairy products` | `current` |
| `skipping` | food | `temporarily` |
| `enjoys_eating` | food | `past` |
| `dislikes_eating` | food | |
| `serves_to_others` | food | `does not eat it` |
| `buys_for_others` | food | |
| `guardian_of` | `Y045` | `legal` |
| `emergency_contact_for` | `Y045` | `not guardian` |
| `attends_course` (subject youth) | e.g. `evening_pottery`, `daytime_first_aid` | `current`, `during:evening` / `during:day` |

Other qualifiers: `time:<phrase>` (yesterday, last week, on saturday, ...), `frequency:<phrase>` (every morning,
on weekends, usually, ...), `negated`, `future`, `hedge:<word>` (reportedly, apparently, ...),
`said_by:<speaker>` (the fact was stated in reported speech; `said_by:unknown` if the speaker is not named),
`observed_by:I`, `note:<free remark>`.

## Querying correctly

* Join through the roster: `kb.KB` maps full names, roster aliases and (when unambiguous) the derived initial form to
  the id. A few names in each document have no roster entry; they cannot be in an answer.
* "Currently / ordinarily / now" = `kb.KB.current(f)`: no `past`, `future`, `once`, `negated`. Decide `hedge:` per query.
* `said_by:` facts are ordinary facts (people report their own and others' facts in quotes); treat them as true.
  `note:` qualifiers are free remarks; they never change the meaning (past-signalling remarks such as "a membership
  that has since lapsed" already add `past`).
* The documents plant near-miss distractors for every condition; the qualifiers separate them:
  past vs current (`works the night shift in a former role`, `routinely travels by bus but no longer does`,
  `enjoys eating mango in the past`), `once` / `future` travel, `temporarily skipping cheese` and `dislikes eating milk`
  (not "avoids dairy products"), `emergency_contact_for ... not guardian` (not a guardian), `likes_equally` and
  `chose ... because of a disruption` (not a genuine preference), `serves ... but does not eat it`, `old-event-...
  period:last-year` (not this year), youth courses `daytime_*` / `during:day` (not evening).
* World knowledge is not in the documents and lives in the query code: coastal cities (Halifax, Vancouver, Victoria,
  St. John's, Lunenburg; inland: Calgary, Edmonton, Winnipeg, Regina, Ottawa), fruits (watermelon, banana, pear, peach,
  mango, apple, orange, plum; not lentils, bread, rice, dairy), public transport (bus, subway, tram, train).
* Count distinct objects where a query says "distinct" (the same event can be mentioned twice).

## Extending

* New object values usually still parse: each slot (common.slot) tries the known values, then a short generic phrase.
  Add frequent new values to the lists in common.py (PLACES, GROUPS, TITLES, ITEMS, FOODS, MODES) so they are not cut
  short. Names: capitalised names need no list; ALL-lowercase names are only recognised when the first or last word is
  in FIRST_NAMES / SURNAMES (common.py) - add new name words there.
* New modifier words: MODIFIERS in common.py (tail) or _PREMODS in composite.py (before the verb).
* A new clause kind: a `C.Core` subclass with `pattern = SUBJ + " <fixed words> " + slot(...) + r"(?P<tail>.*)"` and
  `make()`; add its first verb word to PRED_HEADS (common.py) so the splitter cuts before it after a connector. Rules
  in the other files are picked up by the composite rules automatically only if their module is in speech.py's import
  list.
* Clause rules refuse any clause with a quote mark; quotes always go through `quoted_speech`.
* Use manual.jsonl only for free text: pronoun subjects across sentences ("I remembered Samir Jones. He used to ..."),
  free-form quotes ("unlike X, who owns a camera, I don't take photos of them").
* Pitfall seen while building: writing regexes through shell heredocs turned `\b` into a backspace character; edit
  part files with a file editor, and grep for control characters if a pattern mysteriously fails.
