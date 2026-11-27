# Grammar library notes

Documents are "passages" of short sentences generated from fixed templates, plus noisy paraphrases (commentary, quotes,
lower-case names, reported speech). One content line = one passage body. The final query asks for person IDs (`P-NNN`).

Run:

    python -m gram test  --lib lib
    python -m gram parse train/docN.md --lib lib --manual train/docN.manual.jsonl --out outN
    python solve.py                      # example: answers the three training queries from outN/parsed.jsonl

Query helpers are in `lib/tools/factdb.py` (`DB.from_parsed(...)`, joins names to person IDs, has the condition
predicates used by the training queries; adapt/extend for new queries). Delete `lib/parts/__pycache__` if edits seem ignored.

## Parts (lib/parts)

* `a_split.py` - `clause_splitter`: sentence split (not after initials like `N.` or `St.`), then clause split at
  `, and / , while / , whereas / , but / ; / ,` when what follows starts a new `SUBJECT PREDICATE`. Drops lead-ins
  (`In a separate update,` `Elsewhere in the note,` `The same account also says that`, `The club newsletter records that`, `I noted that`...).
  Trailing commentary (`, which ...`, `, a task that ...`, `, ensuring ...`) becomes its own clause (ignored) UNLESS it
  contains a meaning word (no longer / in the past / lapsed / ended / formerly ...): then it stays attached and the rule adds `past`.
  Normalizers: `straight_quotes`, `used_to_verb` (typo `used to attends`), `name_case` (lower-case leading name `c. bennett`).
* `gcommon.py` - helpers + `Pred` base class used by all fact rules: optional speaker frame
  (`X said, "I ..."`, `X said he ...`, `X: "I ..."`, `I, X, ...`, trailing `, the speaker noted`), optional adjunct, optional
  meaning-changing tail. Not a part itself.
* `b_rules.py` - fact rules (below). `c_misc.py` - roster rule, ignore rules (`background_sentence`, `commentary_tail`).

## Facts: subject / relation / object / qualifiers

Subjects: person as written but case-fixed (`N. Reed` or `Nadia Reed`), youth `Y077` (`Youth 077` and `Y077` are one entity),
organisation `Org 027` (`organization 027` / `Org 027` unify). Objects are lower-case without article (`atlas of clouds`).

| relation | clause | notes |
|---|---|---|
| has_id / familiar_name | roster sentence | `Nadia Reed has_id P-114`; `familiar_name N. Reed`. THE way to join `N. Reed` to a person ID. Event ids `event-P-008-2` also embed the volunteer's ID. |
| visited, discussed, recommended, owns, attends | basic sentences | `discussed` also covers `mentioned`/`talked about`; `recommended` covers `suggested`; `owns` covers `has`. |
| helped_with_setup / _cleanup / _registration | `helped with setup at the market` | object = place |
| attends | `attends the G` | qualifier `past` for: only in the past, used to attend, previously/formerly attended, no longer attends (+`no_longer`), but no longer does. NO `past` = current. |
| volunteered_at | `volunteered at event-P-008-2 during this-year` | object = event id; qualifier `this-year` or `last-year` (old-event-... ids are last-year). Count DISTINCT objects. |
| works_for | `(currently) works for Org 027` | qualifier `current` if "currently" was written. |
| based_in | `Org 027 is based in Halifax` | subject Org, object city lower-case (`st. john's`). Whether a city is coastal is world knowledge (see factdb). |
| works_shift | `works the day/night shift` | `past` for "in a former role", "used to work", "worked". |
| travels_by | `routinely travels by bus` | quals `routinely`; `past`,`no_longer` for "but no longer does"/"used to". Public transport = bus/train/tram/subway. |
| used_transport | `used the tram once` | quals `once`,`past` - NOT a routine. |
| plans_to_use | `plans to use the bus in the future` | qual `future` - NOT current travel. |
| likes_equally / prefers / chose | train vs plane | `prefers` train (qual `genuinely` if written, `over plane`); `chose` train "only because of a disruption" is NOT a preference; `likes_equally` is no preference. |
| avoids | `currently chooses to avoid dairy products` | qual `current`. |
| skips | `is temporarily skipping cheese` | qual `temporary` - not a lasting avoidance. |
| buys_for_others, serves_to_others (+ eats with qual `not`), dislikes_eating, enjoys_eating | food sentences | `enjoys_eating` has `past` for "in the past"/"used to enjoy"; fruit is world knowledge (factdb.FRUITS). |
| legal_guardian_of, emergency_contact_of | `is the legal guardian of Youth 075` | object `Y075`. emergency contact "but not a guardian" has qual `not guardian` and is NOT a guardian. |
| attends_course | `Youth 077 currently attends evening_carpentry during the evening` | quals `current`, `evening` or `day`. Subject is a youth id, not a person. |
| keeps, takes_photos, helped_with_logistics, mentioned, checks_night_sky, plans_to_read | rare, from manual rows only | |

Qualifiers worth knowing:
* `past`, `no_longer`, `future`, `once`, `temporary`, `current`, `this-year`, `last-year`, `routinely`, `genuinely`, `not`.
* `said`: the fact was given in reported speech / quote (`X said, "I own a camera"`, `"..." she said`). Treat as a normal fact unless a query cares.
* `detail: <text>`: free adjunct kept verbatim (`detail: to the group`, `detail: on Thursdays`, `detail: every morning`). Frequency/time
  words such as `every Tuesday` live here - check them if a query asks about frequency. If the adjunct contains a meaning word it also gets `past`.

## Things to know when querying
* Every person ID in a query is `P-NNN` from the roster. `DB.resolve(name)` joins full name, initial form (`N. Reed`, via familiar_name or
  matching initial+surname) and event ids. In the training docs all 160 people resolve.
* A clause is attached to its person by name only, so pronoun clauses are in manual.jsonl with hand-resolved subjects.
* Distractors seen: past forms (`only in the past`, `used to`, `no longer`), `once`, `plans to`, `temporarily`, `emergency contact but not a guardian`,
  `chose ... only because of a disruption`, `likes equally`, `serves but does not eat`, `buys for other people`, `last-year` volunteering.
* Ignore rules: `background_sentence` (scene-setting sentences) and `commentary_tail` (lower-case trailing commentary). They refuse any
  clause with a NAME+PREDICATE shape, a meaning word, or a first-person statement, so real facts are never silently ignored.
* manual.jsonl rows (train/docN.manual.jsonl) are only for free-text clauses: conjoined predicates with one subject, pronoun subjects,
  relative clauses, first-person quote continuations, odd verbs (`keeps`). If new documents show a repeated one, write a rule instead.
