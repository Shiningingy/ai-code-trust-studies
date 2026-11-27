# Reconciling lib_a, lib_b and lib_c into lib/

Base: lib_c. It keeps an opener on its clause, so a reporting frame can qualify the fact. It tells discourse markers
(add nothing) apart from reporting frames (add `reported`). Its one-analysis-per-clause design rules out `ambiguous`
outliers, and it had the fewest unresolved clauses. All three libraries gave the same answers on the training queries,
so the groups below are about naming and qualifiers, not about which people qualify. Changes made to lib_c are marked
"changed".

G01 CARRY "In a separate update," + clause: lib_b/lib_c are right. The opener belongs to the clause it introduces. It is a discourse marker, so it adds no qualifier. lib_a's separate ignored clause is a split artefact: no fact is lost, but the opener is not a clause.
G02 CARRY "Elsewhere in the note," + clause: lib_c is right. A discourse marker with no qualifier. lib_b adds `reported`, but the marker only moves to another part of the same note and reports nothing; lib_a's split is the same artefact as in G01.
G03 CARRY "The same account also says that" + clause: lib_b/lib_c are right. The frame stays on the clause and adds `reported`. lib_a drops the frame as an ignored clause and loses the attribution.
G04 QUAL "helped with registration at the market": lib_b/lib_c naming, `helped_with_registration` with the place as object. Same fact as lib_a's `helped_with registration` + `at:market`, but it keeps the place where a query can join on it, and openers like "At the riverside park," fill the same slot.
G05 CARRY "A recent personal note mentioned that" + clause: lib_b/lib_c are right. A reporting frame on its clause, adding `reported`; lib_a loses it.
G06 QUAL "helped with setup at the museum": `helped_with_setup` / object `museum`, the same decision as G04.
G07 QUAL "currently works for Org 001": object `Org 001`, as in lib_a/lib_b (changed: lib_c's `Organization 001` is now canonicalised to `Org NNN`, 3 digits). Qualifier `currently` is kept, as in lib_c (lib_b drops it, and a time word should survive). lib_a's `current` means the same; lib_c's spelling is used everywhere.
G08 CARRY "Unrelatedly," / "In contrast," + clause: lib_b/lib_c are right. A discourse marker stays on its clause with no qualifier.
G09 QUAL "helped with setup at the library": `helped_with_setup` / object `library`, the same decision as G04.
G10 QUAL "helped with cleanup at the museum": `helped_with_cleanup` / object `museum`, the same decision as G04.
G11 QUAL "helped with setup at the riverside park": `helped_with_setup` / object `riverside park`, the same decision as G04.
G12 QUAL "helped with setup at the sports hall": `helped_with_setup` / object `sports hall`, the same decision as G04.
G13 QUAL "helped with cleanup at the sports hall": `helped_with_cleanup` / object `sports hall`, the same decision as G04.
G14 QUAL "helped with cleanup at the riverside park": `helped_with_cleanup` / object `riverside park`, the same decision as G04.
G15 QUAL "helped with cleanup at the library": `helped_with_cleanup` / object `library`, the same decision as G04.
G16 QUAL "helped with registration at the sports hall": `helped_with_registration` / object `sports hall`, the same decision as G04.
G17 QUAL "helped with cleanup at the market": `helped_with_cleanup` / object `market`, the same decision as G04.
G18 QUAL "helped with registration at the riverside park": `helped_with_registration` / object `riverside park`, the same decision as G04.
G19 QUAL "helped with registration at the library": `helped_with_registration` / object `library`, the same decision as G04.
G20 QUAL "helped with registration at the museum": `helped_with_registration` / object `museum`, the same decision as G04.
G21 QUAL "helped with setup at the market": `helped_with_setup` / object `market`, the same decision as G04.
G22 QUAL "currently chooses to avoid dairy products": lib_c's `avoids` `dairy products` with `currently`. The time word is kept (lib_b drops it); lib_a's `current` is the same meaning in another spelling.
G23 QUAL "is the legal guardian of Youth 075 / Y028": object `Y075` as in lib_a/lib_b (changed: lib_c's `Youth 075` is now canonicalised to `YNNN`, so `Youth 075` and `Y075` join). Qualifier `legal` is kept, as in lib_a/lib_c (lib_b drops it).
G24 QUAL "recommended The Long Orchard" after "A recent personal note mentioned that": lib_b/lib_c are right, `recommended` `long orchard` with `reported` from the frame (see G05). lib_a's facts are the same but lose the frame.
G25 QUAL "genuinely prefers train to plane when both are available": lib_c's `prefers` `train over plane` with `genuinely` and `when both are available`. lib_a holds the same information in another shape. lib_b's `prefers_train_to_plane` drops both qualifiers. The query uses relation `prefers` (not `chose`, not `likes_equally`), because "prefers train to plane" without "genuinely" (doc3 line 8193) is still a preference.
G26 QUAL "helped with cleanup at the riverside park" (clause after a connector): `helped_with_cleanup` / object `riverside park`, the same decision as G04.
G27 QUAL "currently works for Organization 014" (clause after a connector): `works_for` `Org 014` with `currently`, the same decision as G07.
G28 CARRY "I observed that" + clause: lib_b/lib_c are right. A reporting frame on its clause, adding `reported`; lib_a's split loses it.
G29 CARRY "I noted that" + clause: lib_b/lib_c are right. A reporting frame, adding `reported`.
G30 QUAL "helped with registration at the market" (after a connector): `helped_with_registration` / object `market`, the same decision as G04.
G31 QUAL "helped with registration at the museum" (after a connector): `helped_with_registration` / object `museum`, the same decision as G04.
G32 QUAL "helped with setup at the museum" (after a connector): `helped_with_setup` / object `museum`, the same decision as G04.
G33 QUAL "helped with registration at the library" (after a connector): `helped_with_registration` / object `library`, the same decision as G04.
G34 QUAL "helped with registration at the riverside park" (after a connector): `helped_with_registration` / object `riverside park`, the same decision as G04.
G35 QUAL "helped with registration at the sports hall" (after a connector): `helped_with_registration` / object `sports hall`, the same decision as G04.
G36 CARRY "During an ordinary team conversation, it came up that" + clause: lib_b/lib_c are right. The frame ("it came up that") stays on its clause and adds `reported`.
G37 QUAL "the community roster records NAME under identifier P-131 ..." after an opener: lib_c's `has_name` / `has_alias` with the ID as subject. Changed: a reporting frame ("The same account also says that") now adds `reported` to roster and org-location facts too, as it does for every other fact, so the rule is uniform. A plain marker ("Elsewhere in the note,") adds nothing, unlike lib_b. lib_a's `has_id` / `also_known_as` is the same fact with name and ID swapped.
G38 QUAL "discussed Copper Harbor" after "A recent personal note mentioned that": `discussed` `copper harbor` with `reported`, the same decision as G24. Changed: an aspect word after a topic ("market trends", "garden circle plans") is no longer dropped; it is kept as qualifier `aspect:trends` (lib_a's choice; lib_b put it in the object), so the topic still joins and the detail survives.
G39 QUAL "recommended Atlas of Clouds" after a reporting frame: `recommended` `atlas of clouds` with `reported`, the same decision as G24.
G40 QUAL "is temporarily skipping cheese": lib_c's `skips` `cheese` with `temporarily`. Same meaning as lib_a's `skipping` and lib_b's `temporarily_skipping`; it stays a separate relation from `avoids`, so it can never pass for "avoids dairy products".

Smaller groups (no ID): the `<name> recommended/owns/attends/helped ...` shapes with lowercase or initial names follow an opener. They are decided as G01/G02/G08 (no `reported` after a discourse marker, `reported` after a reporting frame), with the naming of G04/G07/G23/G40. "In contrast," / "I explained that" / "I recorded that" / "The observer noted that" / "The record shows that" are G08 (marker) and G28 (frame) respectively.

Fixes to lib_c found by comparing all three libraries' facts line by line (not in diff.md):
- ", which he used to show us the stars" / ", which was used to document the event" no longer marks an `owns` fact `past`. Here "used to" says what the object is for (doc1 5869, 8845; doc2 1593, 1993; doc3 5249).
- ", and (she) mentioned the new equipment / how the path had changed" is a remark, not a `discussed` fact (doc1 5733; doc2 2077, 3941, 4901).
- "P owns a telescope, and she explained that Q helped ..." was read as a reporting frame, which dropped P's fact. A frame may no longer contain a fact word. The construction is now a linked clause giving both facts, with `reported` on the explained one (doc3 2269).

## Part 2: one sample per lib_a rule (R01-R34)

R01 attends_group "Samir Ito attends the history group": all three agree (`attends` `history group`); kept.
R02 avoids_food "currently chooses to avoid dairy products": `avoids` `dairy products` with `currently`, as in G22 (lib_b drops the time word; lib_a's `current` is the same meaning).
R03 buys_food_for_others "E. Laurent buys cheese for other people" after "A recent personal note mentioned that": `buys_for_others` `cheese` with `reported` from the frame (lib_b/lib_c), as in G05. It never counts as eating or avoiding.
R04 chose_mode_over "chose train over plane only because of a disruption": lib_c's `chose` `train over plane` with `only because of disruption` (+ `reported` from the frame). This is the same information as lib_a's `chose train` + `over:plane` and lib_b's `chose_train_over_plane`. It is a separate relation from `prefers`, so it is never a genuine preference.
R05 compound_subject "P. Khan and G. Ito both visited the market previously": all three agree (one `visited` fact per person, `past`); kept as lib_c's linked clause.
R06 discourse_opener "In a separate update,": the opener stays on its clause and adds nothing, as in G01. lib_a's ignored opener clause is a split artefact.
R07 discussed "discussed the market, highlighting its recent changes": `discussed` `market`. The participle tail is commentary and adds no qualifier (lib_b/lib_c). lib_a's `note:` qualifier carries no meaning, and no query reads it.
R08 dislikes_eating "dislikes eating yogurt": all three agree; kept.
R09 embedded_who_clause "discussed library matters with R. Bennett, who recommended The Long Orchard": lib_c's two facts are right. lib_b loses R. Bennett's `recommended` fact. Now `discussed` `library` also carries `aspect:matters` (see G38), as lib_a has it.
R10 emergency_contact "is an emergency contact, but not a guardian, for Youth 058": lib_c's `emergency_contact_for` `Y058` plus `guardian_of` `Y058` `negated`. The negation is a fact that a guardian query must exclude, so it is not left as a free-text qualifier (lib_a's `not guardian`, lib_b's `not a guardian`). The object is in `YNNN` form, as in G23. lib_b's `reported` after the marker "Elsewhere in the note," is rejected, as in G02.
R11 enjoys_eating "enjoys eating banana": all three agree; kept.
R12 framing_sentence "The travel note included context beyond the submitted expense": all three ignore it; kept as lib_c's `commentary` ignore-rule, which refuses fact words, names, digits and meaning-changing words.
R13 helped_with "helped with setup at the market, ensuring everything was ready...": `helped_with_setup` `market`, as in G04; the participle tail is commentary (see R07).
R14 legal_guardian "is the legal guardian of Youth 075": `guardian_of` `Y075` `legal`, as in G23.
R15 likes_modes_equally "likes train and plane equally": `likes_equally` `train and plane` (lib_a/lib_c agree; lib_b's `likes_train_and_plane_equally` is the same fact). It is not a preference.
R16 org_based_in "Organization 031 is based in Halifax": subject `Org 031` (lib_a/lib_b; changed in lib_c's canon_org), city `Halifax`.
R17 owns "owns a garden tools": all three agree (`garden tools`); kept.
R18 plans_to_use_transport "plans to use the tram in the future": `travels_by` `tram` `future` (all agree). lib_c's extra `planned` repeats the same meaning; it is kept, and `current()` excludes both.
R19 prefers_mode "genuinely prefers train to plane when both are available": `prefers` `train over plane` with `genuinely`, `when both are available`, as in G25.
R20 quoted_speech '"O. Foster owns a camera, but Talia Ortiz visited the library some time ago," the speaker noted': lib_c is right, with one clause and both facts `reported`. lib_b cuts inside the quotation and loses the attribution of the first fact. lib_a's `said_by:unknown` is the same information.
R21 recommended "recommended Quiet Machines": all three agree (`quiet machines`); kept.
R22 roster_record "The community roster records Nadia Reed under identifier P-114 ...": `has_name` / `has_alias` with the ID as subject (lib_b/lib_c); lib_a's `has_id` / `also_known_as` is the same fact reversed.
R23 routinely_travels "routinely travels by subway but no longer does": all three agree (`routinely` + `past`); kept. It is not ordinary travel now.
R24 said_pronoun_clause "H. Khan said he helped with cleanup at the market": `helped_with_cleanup` `market` with `reported` (lib_c). lib_a's `said_by:H. Khan` and lib_b's `self_reported` are the same information; the fact still counts.
R25 self_introduction "I, omar foster, helped with registration at the library": `helped_with_registration` `library`, subject `Omar Foster`, no qualifier (lib_c). The narrator states the fact directly rather than through a frame or quotation, so `reported` does not apply. lib_a's `said_by` and lib_b's `self_reported` don't change its truth.
R26 serves_food_to_others "serves plum to other people but does not eat it": `serves_to_others` `plum` plus `eats` `plum` `negated` (lib_b/lib_c). The negation is a fact a "enjoys eating" query must not miss, not a free-text qualifier.
R27 temporarily_skipping "is temporarily skipping butter": `skips` `butter` `temporarily`, as in G40.
R28 used_transport_once "used the subway once": all three agree (`travels_by` `once`); kept. It is not ordinary travel.
R29 visited "visited the market some time ago": `visited` with `some time ago` as written (lib_b/lib_c). lib_a turns it into `past`, which hides the difference between "some time ago" and "in the past / previously". Both are kept apart, and `past` stays for the explicit forms.
R30 volunteered "volunteered at event-P-020-0 during this-year": `volunteered_at` `event-P-020-0` with `this-year` (lib_c). lib_a's `period:this-year` and lib_b's `during this-year` are the same; the query counts distinct objects with `this-year`.
R31 witnessed_doing "I watched Talia Reed recommend Quiet Machines to a new volunteer": `recommended` `quiet machines` with `reported` (lib_b/lib_c). lib_a's `observed_by:I` is the same; "to a new volunteer" is commentary.
R32 works_for "currently works for Org 001": `works_for` `Org 001` `currently`, as in G07.
R33 works_shift "works the night shift in a former role": all three agree (`night`, `past`); kept. It is not a current night shift.
R34 youth_attends_course "Youth 077 currently attends evening_carpentry during the evening": `attends_course` subject `Y077` (changed from lib_c's `Youth 077`), with `currently` and `during the evening`. lib_b drops `currently`; lib_a has the same meaning in other spellings.
