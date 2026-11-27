# Reconciliation of diff.md (base: lib_a; one decision per group)

G01 guardian_of keeps the qualifier `legal` (lib_a): the text says "legal guardian", b dropped it; youth ids stay zero-padded as written ("Youth 075"), c's "Youth 75" is the same entity under a different string, so one form is used everywhere.
G02 likes_equally object is `train and plane` (a, b); c cut it to `train` + qualifier `and plane`, which loses the second mode.
G03 a closing quote left on a quoted statement keeps the qualifier `quoted` (a): true of the text and harmless for queries; b/c drop it. Titles keep one canonical title case ("Copper Harbor") on every line.
G04 "A recent personal note mentioned that ..." is a neutral opener: no qualifier. a had marked it `reported`, which wrongly suggests someone else's claim; b/c agree with the new form; the fact is stated as true.
G05 same neutral opener, `owns sewing kit`: no qualifier.
G06 same neutral opener, `discussed`: no qualifier.
G07 same neutral opener, `recommended Atlas of Clouds`: no qualifier; title case kept.
G08 closing-quote residue on `recommended ... of ...`: `quoted` kept, title case kept (see G03).
G09 closing-quote residue on `owns a sewing kit`: `quoted` kept; object `sewing kit`.
G10 neutral opener, `owns camera`: no qualifier.
G11 closing-quote residue on `owns a garden tools`: `quoted` kept; article dropped, object `garden tools`.
G12 neutral opener, `owns guitar`: no qualifier.
G13 `visited ... some time ago`: a kept only the words; b/c mark it past. The fact now carries `some time ago` plus the common `past`. c's "ambiguous" was two of its own rules overlapping.
G14 neutral opener, `attends walking group`: no qualifier.
G15 closing-quote residue on `discussed`: `quoted` kept (see G03).
G16 closing-quote residue on `owns a telescope`: `quoted` kept.
G17 neutral opener, `owns garden tools`: no qualifier.
G18 closing-quote residue on `helped_with_cleanup`: `quoted` kept.
G19 `X said, "I visited the museum some time ago.`: the subject is the speaker X (a, b); qualifiers `quoted`, `said`, `some time ago`, `past`. c left it unparsed.
G20 same as G19 for the library.
G21 `attends the radio society only in the past`: lapsed, so qualifiers `only in the past` + `past` (a had no `past`); c had two rules matching (ambiguous) but only one reading exists.
G22 roster sentence with a closing quote: has_id / also_known_as keep `quoted`; relation name `also_known_as` (a, c), not b's `alias`.
G23 closing-quote residue on `owns a guitar`: `quoted` kept.
G24 `attends the walking group only in the past`: as G21.
G25 closing-quote residue on `owns a camera`: `quoted` kept.
G26 closing-quote residue on `visited the library`: `quoted` kept.
G27 closing-quote residue on `attends the radio society`: `quoted` kept.
G28 `currently works for Org 019`: object `Organization 019` ("Org" and "Organization" are one entity, and it must equal the subject of based_in), qualifier `currently` as written (c's `current` is the same). b's split_error came from its splitter on that line, not from the clause.
G29 "The same account also says that r. Avery attends ...": neutral opener, no qualifier; the lower-case initial is repaired by a normalizer and expanded to the roster first name.
G30 closing-quote residue on `helped_with_setup`: `quoted` kept.
G31 roster sentence behind the neutral opener: no qualifier, relation `also_known_as`.
G32 neutral opener with a lower-case name ("farah Chen attends"): no qualifier, name repaired.
G33 neutral opener, `attends garden circle`: no qualifier.
G34 `visited the library some time ago`: as G13.
G35 neutral opener, `helped_with_setup museum`: no qualifier.
G36 `likes train and plane equally` without a final stop: as G02, object `train and plane`.
G37 `is the legal guardian of <Y>` without a final stop: as G01, `legal` kept.
G38 "I explained that " is only a dangling narrator fragment and is ignored; the claim after it is a clause of its own and is parsed with the same facts as c gets (a loses only the wrapper word `reported`, which changes no meaning).
G39 closing-quote residue on `helped_with_setup` at the market: `quoted` kept.
G40 neutral opener, `helped_with_setup market`: no qualifier.
R01 attends: all libraries agree on `attends` / `history group`.
R02 class roles: one relation `took_part_in` with `as the student` + `this year` (a, b); c's relation per role (`class_role_student`) splits one fact over four relations; the query only needs `as the teacher`.
R03 diet: `avoids dairy products` with the written word `currently`; c's `current` is a rename only; a plain "avoids" with no "currently" is the same present-tense fact and counts as current in the query.
R04 discussed + participle ("highlighting its recent changes"): the tail is commentary, not a second claim; the fact is `discussed market` (b split the tail into an ignored clause, same facts).
R05 guardian: see G01.
R06 helped_with + commentary tail ("ensuring everything was ready"): same fact `helped_with_setup market`; the tail is ignored (b split it off, same facts).
R07 intro_frame: scene-setting sentence, ignored by all three.
R08 narrator_comment ("I explained that "): see G38.
R09 org_based_in: subject `Organization 031` (b/c write `Org 031`): one canonical form, equal to the works_for object so the two join.
R10 owns "a garden tools": object `garden tools`, article removed; all libraries agree.
R11 plans_to_use: relation `plans_to_use` with `in the future` (a, b); c's travels_by with `future` would make a plan look like a habit.
R12 recommended: agree; canonical title case.
R13 roster: has_id + `also_known_as` (b's `alias` is the same relation); the join from names to person ids goes through it.
R14 serves_not_eats: one fact `serves_to_others` with `does not eat it`; b's extra `eats`/`negated` fact only repeats it.
R15 speech_attribution ("X wrote in the volunteer log"): a bare attribution; the splitter now keeps `wrote in the volunteer log, "I ...` together so the quoted `I` gets the speaker (a produced `narrator` there).
R16 travel_preference: `prefers` object `train over plane`, qualifiers `genuinely` + `when both are available`; c cut the object to `train` and moved the rest into qualifiers.
R17 travels_by with "but no longer does": qualifiers `routinely`, `no longer`, `past`: a former habit, not ordinary travel.
R18 used_once: relation `used_transport` with `once` (a, b); c's travels_by + `once` would read as a habit.
R19 used_to_attend: `attends` with `used to` (+ `no longer`, `past`) is a former membership; a commentary tail ("which was a notable change") is ignored.
Smaller groups (no id): same decisions by shape: neutral opener = no qualifier; closing-quote residue = `quoted`; discussed + extra word ("market trends") = object `market` with qualifier `about trends` (b/c drop the word, a keeps it); `works the night shift in a former role` = `in a former role` + `past`; initials expand to the roster first name.
Beyond diff.md (found by comparing the three on every line): an emergency contact without "not a guardian" was parsed as guardian_of by a (b, c were right): now `emergency_contact_of`; "During this-year, X volunteered at event-..." had no year (now `this-year`) and a trailing "this year's list" added a second year (now ignored); second claims in a tail ("and she also visited X", "and discussed Y afterward", "discussed A and B", "discussed A, which N recommended") were dropped (now read); speaker forms `Name: "I ...` and `Name wrote in the log, "I ...` now give the speaker; `used to document` (an instrument) and `was not present` (commentary) no longer produce `past` / `not`.
R20 visited "some time ago": qualifiers `some time ago` + `past` (b's form); a had only the words, c only `past`; both are kept so the wording and the common marker are present.
R21 volunteered: qualifier `this-year` as written in the text (b/c's `this year` is the same period with a space); the year is always present, also when only the opener or the event id (`old-event-` = last-year) gives it.
R22 works_for: object `Organization 001` (b/c `Org 001` is the same entity; one form joins with based_in), qualifier `currently` as written (c's `current` is a rename).
R23 works_shift "in a former role": qualifiers `in a former role` + `past` (a had no common marker; b's `former` and c's `past` say the same): the shift is NOT current.
R24 youth_course: subject `Youth 077` (zero padding as written; c's `Youth 77` is one entity under another string), qualifiers `currently` + `during the evening` as written (b's `evening` is shorter, c's `current` a rename).
