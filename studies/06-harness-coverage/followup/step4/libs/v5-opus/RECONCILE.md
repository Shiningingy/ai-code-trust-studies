# Reconciliation of lib_a, lib_b, lib_c

Base: lib_a. It is the only library that keeps every fact in the Part 2 samples: lib_c loses the embedded facts in
R12/R15 and the place in R08, and lib_b adds `remark=` text and bare `reported` that carry no meaning. Changes made
to lib_a are named below. Naming differences (relation names, `time:` vs `status=` / `when:`, `Organization 001`
vs `Org 001`, book titles in title case vs lower case) are the same fact; lib_a's names are kept throughout.

## Part 1 groups

G01 lib_b: both written forms get `has_id P-114`, and the familiar name also gets `alias` (the text says "uses the familiar names"). lib_c's `P-114 has_name/has_alias` is the same fact named the other way round. lib_a lost the alias distinction, so the roster rule now adds `alias`.
G02 as G01 (lowercase roster sentence after a dropped connector). lib_b's clause text keeps "Unrelatedly," or "Elsewhere in the note,", which is only a boundary difference: the connector carries no fact.
G03 lib_a: keep `legal` on `guardian_of`. The text says "legal guardian", which is what separates it from the "emergency contact, but not a guardian" sentences. lib_b and lib_c drop it.
G04 lib_a: two facts, `likes_equally train [and:plane]` and `likes_equally plane [and:train]`. lib_b's fused object "train and plane" yields no fact about either mode, and lib_c drops the plane half.
G05 lib_b/lib_c keep the passage frame "A recent personal note mentioned that"; lib_a's splitter dropped it as a connector. Decision: keep it as `evidence:record`, the same qualifier lib_a already gives "The appointment note records that ..." (the same shape: a named source plus a reporting verb). It is now removed from `common.INTRO`, so the evidence reader handles it. Object case is lib_a's ("The Long Orchard").
G06 as G01 (roster sentence without a final period).
G07 as G05 (discussed a book, under the personal-note frame).
G08 as G05 (owns a sewing kit, under the personal-note frame).
G09 as G05 (recommended Atlas of Clouds, under the personal-note frame).
G10 as G01.
G11 as G05 (owns a camera).
G12 as G05 (owns a guitar).
G13 as G05 (attends the walking group).
G14 as G05 (owns garden tools).
G15 lib_a/lib_c: "owns a garden tools set" is `owns garden tools` with no qualifier. "set" is part of the item's name and does not change the fact, so lib_b's `item_detail=set` is dropped.
G16 lib_a/lib_b: "The same account also says that" carries no qualifier. In all 903 uses it is the third connector of a fixed rotation ("In a separate update, ... Elsewhere in the note, ... The same account also says that ... Unrelatedly, ..."). It refers to the same note as the sentences around it, so lib_c's `source:` would mark every third sentence of one note arbitrarily. It stays a dropped opener.
G17 as G16 (lowercase given name "farah", under the same-account connector).
G18 as G05 (attends the garden circle).
G19 as G04 (no final period).
G20 as G03 (no final period).
G21 lib_c: "discussed market trends" is `discussed market [aspect:trends]`. The topic stays the object, so it can be matched like every other group or place, and the aspect noun is kept. lib_a lost "trends", and lib_b's object "market trends" hides the topic. New: the discussed rule reads a noun after a group or place (`common.ASPECT`) as `aspect:<noun>`; this also covers matters, hours, plans, activities, events and similar nouns in the smaller groups.
G22 as G16 ("nadia", same-account connector).
G23 as G05 (attends the radio society).
G24 as G05 (discussed riverside park).
G25 as G16 ("l.", same-account connector).
G26 as G05 (visited the sports hall).
G27 as G16 ("ben", same-account connector).
G28 as G05 (discussed radio society).
G29 as G05 (discussed history group).
G30 as G16 ("dev", same-account connector).
G31 as G16 ("f.", same-account connector).
G32 as G16 ("leah" attends, same-account connector).
G33 as G16 ("h.", same-account connector).
G34 as G16 ("leah" discussed garden circle, same-account connector).
G35 as G16 ("d.", same-account connector).
G36 as G16 ("n.", same-account connector).
G37 as G05 (owns a telescope).
G38 lib_a/lib_c: "recommended X to the group" is `recommended X` with no qualifier. The addressee does not change the fact, so lib_b's `remark=to the group` is dropped.
G39 as G05 (discussed museum).
G40 as G05 (discussed market).

## Part 2 samples (one per lib_a rule)

R01 lib_a/lib_c: both facts, with no qualifiers. lib_b's `remark=which is different from how` and `embedded` are bookkeeping, not meaning.
R02 all agree.
R03 lib_a: `avoids dairy products [time:current, choice]`. "chooses to avoid" is the lasting choice the query asks about, as opposed to "is temporarily skipping". lib_b and lib_c say the same thing in other names.
R04 all agree (organization naming only).
R05 lib_a/lib_c: the participle elaboration ("highlighting its recent changes") carries no qualifier, so lib_b's `remark=` is dropped.
R06 as G05: lib_a now gives `evidence:record` for the personal-note frame.
R07 as G03.
R08 lib_a: `helped_with registration [at:riverside park, evidence:narrator]`. lib_c loses the place; lib_b is the same content with the place as the object.
R09 lib_a/lib_c: `helped_with setup [at:market]`. lib_b uses the place as the object (naming) and adds a remark (dropped).
R10 all agree up to naming (`reported_by:H. Khan`).
R11 all agree (ignored narration).
R12 lib_a/lib_b: keep the embedded `L. Evans recommended Atlas of Clouds`. lib_c loses that fact.
R13 all agree.
R14 all agree (title case vs lower case only).
R15 lib_a, plus the G21 aspect rule: `Talia Patel discussed library [aspect:matters]` and `R. Bennett recommended The Long Orchard`. lib_c loses R. Bennett's fact.
R16 lib_a/lib_c: `reported_by:the speaker` and the literal `time:some time ago`. lib_b's bare `reported` loses who reported.
R17 as G01.
R18 all agree up to naming (`took_part_in_class language [role:student, time:this-year]`).
R19 lib_a: `prefers_over train [over:plane, genuinely, when both are available]`. lib_c drops "when both are available"; lib_b is the same in other names.
R20 all agree (`freq:once`).
R21 lib_a/lib_c keep the literal "some time ago"; lib_b's `time=past` is the same meaning, less precise.
R22 all agree up to naming.
R23 all agree up to naming.
R24 all agree (former role = past).
R25 all agree up to naming.

## Smaller groups (no ID) and further changes

Smaller groups: these are the same shapes as above, so they get the same decisions. Personal-note frames become `evidence:record` (G05), same-account connectors stay dropped (G16), "a ... set" and addressees take no qualifier (G15, G38), and "discussed X <noun>" becomes `aspect:` (G21).

Tails (found while checking the smaller groups; lib_c gets most of these right by dropping commentary). lib_a gave the main fact qualifiers taken from an elaboration about something else:
- `owns guitar [freq:regular]` from "and plays it on weekends"
- `owns telescope [time:past]` from "which he used to show us the stars"
- `recommended [time:future]` from "and we plan to check it out soon"
- `discussed museum [time:last week]` from "a place that was visited last week"
- `attends [freq:regular]` from "a group that meets weekly"

`common.tail_quals` now reads every phrase in the head of the tail. After an elaboration boundary (a comma, `and`, `which`, `that`, `who`, `so`, `as a`, `for`) it reads only a past status of the fact itself ("but he no longer does", "a membership that has since lapsed"), without "used to". The exception is an appositive that names the fact ("a trip that ...", "a current fact ..."), which is read in full. `time:current` is dropped when `time:past` is also present ("but that is in the past now"). None of this changed whether a clause resolves, and the four answers stayed the same.
