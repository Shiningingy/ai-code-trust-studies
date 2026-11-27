# Community-records grammar: notes for later sessions

## How to use

```
python -m gram test  --lib lib
python -m gram parse doc.md --lib lib --manual doc.manual.jsonl --out out
python lib/facts.py out/parsed.jsonl           # summary; also lists subjects that do not resolve to a person ID
python lib/query_examples.py out/parsed.jsonl  # sizes of the usual condition sets
```

In Python: `from facts import Facts` (add `lib` to `sys.path`). `F = Facts("out/parsed.jsonl")`; every fact gets
`f["pid"]` (person ID, or None for orgs and youths); `F.find(relation, obj, has=(...), lacks=(...))` filters by
qualifiers; `F.orgs_in()` maps `Org NNN` to its city; `F.youth_courses()` maps `YNNN` to its course facts.
`query_examples.py` has worked condition functions (coastal employer, public transport, night shift, N events this
year, dairy, guardian of an evening-course youth, train preference, fruit) and the world-knowledge sets they need
(which cities are coastal, which foods are fruit, which modes are public transport). Answers on the training docs:
doc1 coastal + transit + night shift, doc2 coastal + 3 events + dairy + transit, doc3 3 events + evening guardian +
prefers train + fruit + dairy; all three were checked against near misses by hand.

## The grammar

A line is a sequence of sentences; a sentence is one or more clauses:

    clause := [opener ","] [report frame] SUBJECT PREDICATE [tail]

- **Splitter** (`splitter.py`, `sentence_clause`): sentence ends at `. ! ?` (+ closing quote), but not after an
  initial (`N. Reed`, `"A. Gupta`) or `St` (`St. John's`). Inside a sentence it cuts at `, and` `, while` `, but`
  `, whereas` `;` `,` `, "while` `, and that` or a bare `and` ONLY where a new clause starts (`CLAUSE_START` in
  `common.py`: a name + predicate verb, `NAME and NAME both ...`, `Org NNN is based`, `Youth NNN attends`, `the
  community roster`, `she explained that NAME ...`). A bare comma/`and` never cuts off an opener or a first name
  of a pair. So `..., but no longer does` stays in its clause.
- **Openers** (`decompositions()` in `common.py`): any short phrase before a comma ("In a separate update",
  "Elsewhere in the note", "Unrelatedly", "In contrast", "During the shift handoff") is dropped; time openers ("In
  the past," -> past, "In the future," -> future) become qualifiers; an unknown opener with a time/negation word is
  refused (shows up as unparsed). `Then/Also/Later/Meanwhile N ...` without comma too.
- **Report frames**: `<source> <report verb> [in the X] [that]` ("The record shows that", "I observed that", "The
  speaker mentioned that", "I noted in the community bulletin that", "I was at the riverside park when", "I filed the
  reimbursement after noting that", `I contrasted this with ..., noting, "`) -> qualifier `reported`. A trailing
  `," the speaker noted` also gives `reported`.
- **Subjects**: a person name in any case (`Nadia Reed`, `N. Reed`, `nadia reed`, `c. Patel`), canonicalised to
  title case (`C. Patel`); `N and M both ...` gives one fact per person; `N, meanwhile, ...` asides; self-quotes
  `N said, "I ...` / `N: "I ...` / `N concluded, "I ...` / `N said he ...` / `N mentioned that she ...` /
  `I, omar foster, ...` -> qualifier `self_reported`. Orgs: `Org 014` / `Organization 14` / `org 014` -> `Org 014`.
  Youths: `Youth 045` / `Y045` / `youth 45` / `y045` -> `Y045`.
- **Predicates**: one Rule per family (below); each accepts 3rd and 1st person forms (`owns`/`I own`, `is`/`I am`,
  including slips like `I attends`).
- **Tails** (`tail_ok()`): elaborations after the predicate (", which he often brings to our outdoor events", " to
  the group", " every morning") carry no fact and are accepted, EXCEPT: a tail containing a new clause with a
  capitalised name (`, which L. Evans recommended`) is refused; a tail with a time/negation word (no longer, used to,
  not, in the past, plans to ...) is refused unless the predicate already says past, or the tail is clearly a remark
  about something else (", so I made sure not to order...", ", and the album has since been popular"). Visits are
  past by nature, so past words in their tails are accepted.
- **Normalizers**: `straight_quotes` (curly quote marks; NOT apostrophes inside words: the word check would split
  `John’s`), `collapse_spaces`, `base_verb_after_to` (`used to attends` -> `used to attend`).
- **Ignore rule** `fact_free_remark`: framing sentences without any predicate word, id or capitalised name pair
  ("This week's community bulletin collected several unrelated updates").

## Facts (subject, relation, object, qualifiers)

Objects are lower case, leading article removed (`The Long Orchard` -> `long orchard`, `the market` -> `market`).

| relation | subject | object | qualifiers / notes |
|---|---|---|---|
| `has_name` / `has_alias` | `P-114` | `Nadia Reed` / `N. Reed` | from the community roster line; also `N says, "The community roster records me under identifier P-076 ...` (self_reported). Some roster lines give only the short form (`f. silva` under P-046); facts.py then links the full name `Farah Silva` through its initial. |
| `owns` | person | item (`camera`, `garden tools`, `sewing kit`...) | `has X`, `keeps a set of X`, `X set` -> X; `past` for used to own |
| `recommended` | person | book/album (`atlas of clouds`, `long orchard`, `quiet machines`, `copper harbor`) | |
| `discussed` | person | topic as written (`market`, `chess club`, `market trends`, `garden circle plans`) | includes `mentioned X`, `talked about X`; compare with `startswith` |
| `attends` | person | group (`chess club`, `walking group`, `garden circle`, `history group`, `radio society`) | `past` = only in the past / used to attend / no longer / was a member of / `, but does not attend now` |
| `visited` | person | place (`market`, `library`, `museum`, `sports hall`, `riverside park`) | `some time ago`; `past` = in the past / previously |
| `helped_with_setup` / `_registration` / `_cleanup` | person | place (`''` if none) | also `assisted with` |
| `volunteered_at` | person | event id (`event-P-139-0`, `old-event-P-075`) | `during this-year` / `during last-year`; count DISTINCT objects |
| `works_for` | person | `Org NNN` | `currently works for` and `works for` are the same (no qualifier); `past` for used to / no longer |
| `based_in` | `Org NNN` | city as written (`Halifax`, `St. John's`) | |
| `works_shift` | person | `night` / `day` | `past` = in a former role / used to / worked |
| `travels_by` | person | `bus` `tram` `subway` `train` ... | `routinely` (ordinary travel); `routinely`+`past` = routinely ... but no longer does / used to take; `once` = used X once; `future` = plans to use |
| `prefers_train_to_plane` | person | `''` | "(genuinely) prefers train to plane when both are available" |
| `chose_train_over_plane` | person | `''` | `only because of a disruption` - NOT a genuine preference |
| `likes_train_and_plane_equally` | person | `''` | |
| `avoids` | person | `dairy products` | "currently chooses to avoid dairy products" |
| `temporarily_skipping` | person | `cheese` `milk` `butter` `yogurt` | a different, temporary thing; not `avoids` |
| `enjoys_eating` / `dislikes_eating` | person | food | `past` = enjoyed / used to enjoy / in the past |
| `buys_for_others` | person | food | does not say the person eats it |
| `serves_to_others` + `eats` (`negated`) | person | food | "serves mango to other people but does not eat it" |
| `guardian_of` | person | `YNNN` | legal guardian |
| `emergency_contact_for` | person | `YNNN` | `not a guardian` when stated; never guardianship |
| `attends_course` | `YNNN` | course id (`evening_pottery`, `daytime_first_aid`) | `during the evening` / `during the day`; `past` if used to |

General qualifiers: `past`, `future`, `once`, `routinely`, `some time ago`, `negated`, `reported` (someone else
reports it), `self_reported` (the subject's own words), `with the narrator` (manual rows only). `reported` and
`self_reported` do NOT weaken a fact: in the training queries such facts count like plain ones. Filter on `past`
(and `future`/`once` for travel) for "currently"/"ordinarily" conditions.

## Things to know

- Every person appears in the roster (160 per training doc); unresolved subjects are listed by `facts.py`.
- Initials were unique per document (one first name per initial), so `N. Reed` is safe to join with `Nadia Reed`.
- Distractors are built in for each query condition: past forms, one-off travel, future plans, `temporarily
  skipping`, `chose ... only because of a disruption`, `emergency contact, but not a guardian`, daytime courses,
  last-year events, non-coastal cities, non-fruit foods. The relations above keep them apart.
- Manual rows (train/docN.manual.jsonl) were needed only for cross-sentence reference (`He used to ...` after "I
  remembered Samir Jones"; `I also discussed ...` continuing someone's quotation from an earlier sentence) and for
  facts about a second person inside a relative clause (`, which L. Evans recommended`, `in contrast to N, who ...`).
  New documents will have a few such clauses; they show up as `unparsed`.
- To audit a library change: set `common.TAIL_LOG = []` (through a rule's `parse.__globals__`) to collect every tail
  `analyze()` accepted, and check none carries a fact.
