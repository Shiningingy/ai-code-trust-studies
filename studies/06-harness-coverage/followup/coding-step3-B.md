# Step 3 method coding, arms B and B1 (Claude subagent's proposals; Zili Luo checks)

Everything below is a proposal for Zili Luo to check. Codes are the frozen ones in `plan.md` (L0-L3, G, K). The convention is the one in `coding-step2-notes.md`: a keyword-limited residue is **L1**. L2 needs the residue of all passages, every passage of every person not ruled out, or a template inventory over all text with the unlabelled shapes read to the end.

Sources: `runs/step2_summary.jsonl` (the 00041 lines), the `runs/step2/<run>-a<N>.jsonl` transcripts (digest tool plus full tool outputs where a code depended on them), and the plan files `plans/CV-*-00041-*` (arm B) and `plans/CV1-*-00041-*` (arm B1). In three places I re-ran an agent's own inventory code on its own copy of `context.md` (read only, in my scratchpad). That was only to check what a truncated or filtered printout contained (Sonnet B-1, Opus B-2). The answer-key folder was not opened.

**K (key access): none.** The summary records `key_access: false` for all 13 attempts. No transcript contains `lhb-data`, `answers/` or "answer key".
**G (guess-and-check): none.** The only retry (Opus B-3 a2) gathered new evidence before it changed the answer.

**A coding point to flag.** Seven of the attempts built a template or shape inventory over the whole file, then set a class of templates aside before reading the rest. In every case the set-aside class was defined by filler verbs or by openers, not by topic keywords. I code these **L2 (with exclusion)**, following Opus B-00013 in step 2, and I name each exclusion. In one run the exclusion hid the decisive line (Opus B-2), and that run still passed. In another, a segmenter hole meant part of the text was never inventoried (Opus B-3 a1). Zili Luo may prefer to code by what text was actually enumerated, not by method. If so, Opus B-3 a1 drops to L1, and Opus B-2 becomes borderline.

## Table (attempt 1 unless marked)

| Run | Pass | Code | Plan's full-coverage step executed? | Cost / tool calls |
|---|---|---|---|---|
| S2Bsonnet55000411 | yes | **L2** (with exclusion) | Mostly: inventory read in full after a verb filter; coverage check keyword-limited; final verification shortened | $0.5993 / 21 |
| S2Bsonnet55000412 | yes | L1 | Started and dropped (inventory); random-sample audit not done (says so) | $0.7062 / 32 |
| S2Bsonnet55000413 | yes | L1 | Started and dropped (inventory); sample read of low-fact people skipped (says so) | $0.5322 / 15 |
| S2B1sonnet55000411 | **no** (missed P-104, added P-159) | L1 (weak; the author may prefer L0) | Not attempted: the whole-file read; zero Read calls (says so) | $0.2960 / 21 |
| S2B1sonnet55000412 | yes | L1 | Started and dropped silently (inventory); dossiers done but keyword-filtered; whole-file fallback not used | $0.4092 / 18 |
| S2B1sonnet55000413 | **no** (missed P-104) | L1 (strong; closest Sonnet run to L2) | Reduced: dossiers for the 16 c1 survivors only, by full name only, without linked youth; index, cross-check and unassigned sample not done (says so) | $0.2981 / 12 |
| S2Bopus55000411 | yes | **L2** (with exclusion) | Yes, mostly (clause accounting, name accounting, cancellations, near-misses); filler bucket checked by keyword, not by the planned Read sample | $1.2887 / 33 |
| S2Bopus55000412 | yes | **L2** (with exclusion; the exclusion hid the P-104 line) | Partly: census read with 286 of 705 non-filler skeletons filtered unread; the 92-person dossier file was written, but only `head -1` was printed | $0.7517 / 21 |
| S2Bopus55000413 a1 | **no** (missed P-104) | **L2 by method, with a structural hole** (L1 if coded by text covered) | Yes, as written (shape inventory, loose superset, unresolved sentences, near-misses), but the shape inventory never saw lowercase youth lines | $1.2437 / 28 |
| S2Bopus55000413 a2 | yes | L1 | n/a (retry): identifier-format census plus audits | $1.8892 / 11 (run total $3.1329) |
| S2B1opus55000411 | yes | **L2** (person-side inventory complete; youth side by keyword net) | Template step yes; dossier step started and dropped (says why) | $1.4449 / 28 |
| S2B1opus55000412 | yes | **L2** (with exclusion; remainder printed in full) | Residue loop yes (keyword-based by design); dossiers for people with 2+ NO-EVIDENCE cells not done | $0.8690 / 22 |
| S2B1opus55000413 | yes | L1 | On keyword hits only: keyword-tagged residue partly read; per-youth review and loose-tier dossiers reduced to 5 finalists + 10 near-misses, keyword-filtered | $0.8600 / 21 |

Attempt-1 cost by cell: Sonnet B $1.8377 (mean $0.613, 22.7 calls); Sonnet B1 $1.0033 (mean $0.334, 17.0 calls); Opus B $3.2841 (mean $1.095, 27.3 calls); Opus B1 $3.1739 (mean $1.058, 23.7 calls).

## Per run

### Sonnet, arm B (1c plan, retries)

**S2Bsonnet55000411** (plan CV-sonnet55-00041-1: template inventory, label every template, coverage check until only irrelevant templates are unclaimed). Pass a1.
- **Code: L2 (with exclusion).** `inv.py` split every passage into sentences and normalised them (1,457 templates; `head -150` printed). `inv2.py` then dropped every template matching `(visited|discussed|recommended|owns a|helped with|attends the|used to attend|^<N> volunteered at old-event)` and printed the rest. That rest was 234 lines, under its `head -300` cap, so it was complete. The agent: "I'll strip the lead-in phrases and list every core template that isn't obvious noise."
- I checked the printout: it contains `1 | youth 104 currently attends <COURSE> during the evening` and 22 other lowercase youth lines. Its extractor then used `YTH=r'((?i:youth) ?\d+|[Yy]\d+)'`.
- **Exclusion:** about 1,200 templates holding a filler verb anywhere in the sentence were set aside unread. The split is by sentence, not clause, so a compound sentence with one filler verb and one real fact would be hidden. (Inference: this did not matter here.)
- **Plan steps.** Inventory done. The coverage check (`cov.py`) is keyword-limited: `if kw.search(cl) and not claimed(cl)`. The near-miss review was done. Verification was shortened: "I did not separately print their train and dairy source lines."

**S2Bsonnet55000412** (plan CV-sonnet55-00041-2: full sentence inventory, label every template, keyword coverage check, random-sample audit of raw lines). Pass a1.
- **Code: L1.** The inventory gave 10,213 lines (`head -120` printed), and the agent abandoned it: "The normalizer is too noisy. I'll inventory only the sentences that carry the five relations, using keyword anchors."
- It then took per-keyword phrasing censuses, read the raw lines for each person who failed exactly one condition, and compared raw keyword counts with extracted counts (257/257, 96/96, 92 vs 86).
- P-104 was found by the near-miss pass: "P-104 was missing because the text writes 'youth 104' in lowercase."
- **Plan steps.** Inventory started and dropped. Random-sample audit not done: "I did not do the random-sample audit from the plan. In its place I compared raw keyword counts against extracted counts."

**S2Bsonnet55000413** (plan CV-sonnet55-00041-3: passage-level template inventory read in full, UNMATCHED bucket iterated to filler, keyword cross-check, random sample read of people with 0-2 facts). Pass a1.
- **Code: L1.** The inventory gave 3,199 templates (`head -150`). Then: "My sentence splitter broke on initials like "Q.", so the inventory is noisy. I'll fix the splitting and list the distinct templates for each relevant keyword."
- It went on to keyword templates, raw keyword counts against extracted counts, and keyword-filtered raw sentences for the 5 matches and the 9 near-misses.
- **Plan steps.** Inventory started and dropped. UNMATCHED bucket not built over all sentences. Step 7 skipped: "I didn't do the random sample-read of people with few extracted facts (plan step 7) ... I can't rule out a fact phrased in a way none of my keywords cover."

### Sonnet, arm B1 (one-pass plan, one answer)

**S2B1sonnet55000411** (plan CV1-sonnet55-00041-1: person-first extraction by reading the whole file in 2,000-line chunks, an L3 plan). **Fail:** missed P-104, included P-159.
- **Code: L1 (weak; the author may prefer L0).** It took phrasing censuses (`grep ... | sort | uniq -c`), wrote strict regexes and built a k ≥ 3 table. Calls 15-17 grepped only the c2 lines of five near-misses (P-104, P-144, P-055, P-085, P-153).
- The agent: "I did not re-read the near-misses, such as P-104, P-144 and P-085. I only spot-checked a few of them."
- **Plan step: not attempted.** No Read call in the run. "I checked each condition with a script, not by hand. I didn't read each person's passages one by one, as my plan said I would."
- **Why P-104 was missed.** The course regex `(?:Youth |Y)(\d+)(?:, who)? currently attends evening_` has no case flag, so "youth 104" never matched. The spot-check grep `(Youth |Y)(104|055|085|144)` was also case-sensitive. It returned only "Gupta is the legal guardian of Youth 104." The agent then wrote: "P-104 and P-085 fail c2 or c1 on explicit text." For P-104 that was absence of evidence, not explicit text.
- **Why P-159 was included.** The c4 pattern `enjoys eating (?:apple|...|watermelon)\b` has no "in the past" exclusion. P-159's only fruit line is "enjoys eating mango in the past". The census in call 8 had already printed past-tense variants for other people.

**S2B1sonnet55000412** (plan CV1-sonnet55-00041-2: full sentence inventory, rules written from the labelled templates, leftovers read until none are unassigned, then dossiers for finalists and near-misses; fallback = read the whole file if the template count is too high). Pass.
- **Code: L1.** It built the inventory (1,529 templates, `head -150`, noisy). Then, without comment, it switched to per-keyword censuses (`t2.py "<keyword>"`). The `evening|daytime|attends_|youth` census showed "youth N currently attends evening_pottery", and its course regex used `re.I`.
- The dossiers (`d.py`) print all sentences that name the person or their youth, then keep only those matching `volunteer|guardian|evening|...|butter` (keyword-filtered). The final message says "then read every passage about each finalist and near-miss". In fact these were the keyword-filtered sentences.
- **Plan steps.** Inventory and labelling started and dropped silently. The leftover loop was never run over all sentences. The fallback was not used, even though 1,529 templates is far above the "dozens to a few hundred" the plan expected.

**S2B1sonnet55000413** (plan CV1-sonnet55-00041-3: person-centred index with linked youths, dossiers read for everyone with at least one keyword hit, strict-pattern cross-check, count unassigned passages and read a sample). **Fail:** missed P-104.
- **Code: L1 (strong).** It counted c1 by event ID over all 257 event mentions, which left 16 people. Call 10 printed every sentence naming each of the 16, except "volunteered at" sentences, with no keyword filter (25 KB, all in context).
- This is close to "every passage for each person not ruled out", but short of it in two ways, so L1.
  - The sentence splitter breaks after initials, so initial-form mentions are missing. P-051's block has only "Kofi Mensah"/"kofi Mensah" lines, though "K. Mensah" occurs 25 times in the file. Those forms were seen only in the keyword-filtered windows of call 11.
  - The ward's course lines are not in the dossier. They were fetched separately with the case-sensitive pattern `\b(?:Youth |Y)%s\b`.
- **Plan steps.** Reduced, and it says so: "I did not build the full dossier index or the pattern-versus-manual cross-check from my plan. I read the 16 candidates' mentions directly instead. I also did not read a sample of passages with no person assigned."
- **Why P-104 was missed.** Call 12's youth lookup was case-sensitive and returned only "D. Gupta is the legal guardian of Youth 104." Its verdict: "P-104: the youth has no evening-course evidence."

### Opus, arm B (1c plan, retries)

**S2Bopus55000411** (plan CV-opus55-00041-1: tag every clause in all 2,327 passages as positive / look-alike / strict filler / unexplained and read the unexplained until nothing relevant is left; name accounting; looser second extractor; near-miss check; cancellation check). Pass a1.
- **Code: L2 (with exclusion).** `x.py` split all passages into clauses and matched them against strict rules, including a `fill` rule anchored at clause start. Everything else went to `unex.txt`: 163 shapes, printed with `head -80` and then `sed -n '80,163p'`, so all of it was read. It was re-run after each fix.
- The residue surfaced lowercase youth lines ("youth 007 ...", "y048 ...", and "youth 104 currently attends evening_pottery"). "Updating the extractor to handle the variant wordings I found (verb agreement, prefixes, lowercase youth IDs, "I." initials)." Later: "Every remaining unexplained clause is irrelevant."
- **Exclusion.** The filler bucket (6,805, then 6,976 clauses) was checked only by a keyword scan (`kw.search(c)` → `FILL?`). That scan found facts hidden in comma-joined lists and led to a comma split. The plan's "spot-check a sample of filler clauses with Read" was replaced by this keyword scan.
- **Plan steps** 5, 6, 8, 9 and 10 were executed. Step 7, the loose extractor, ran as a keyword search over the aliases of near-misses and of the other people with 3+ events.

**S2Bopus55000412** (plan CV-opus55-00041-2: A, a template census with every skeleton labelled; B, a loose superset of people touched on all five conditions, with each dossier read completely; C, name coverage). Pass a1.
- **Code: L2 (with exclusion; the exclusion hid the decisive line).** `census.py` gave 976 clause skeletons. A filler-verb filter (`recommended|discussed|owns a|visited|helped with|previously visited`, with no comma) left 705. `head -250` was printed. The tail was printed after a further filter: `grep -viE "^1\s+(Org|Organization|org) [0-9<]|^1\s+(a|an|which|making|ensuring|adding|so|it|they|the) "`.
- I re-ran its census on its own `context.md`. That second filter removed 286 of the 455 tail skeletons, and one of them was "The same account also says that youth 104 currently attends evening_pottery during the evening". It is a count-1 line that starts with "The", and the `-i` flag made that exclusion catch it.
- The run passed anyway. Its youth parser used `[Yy]outh \d+|[Yy]\d+`, generalised from the other lowercase lines it did see ("youth 007", "y070", ...).
- **Plan steps.**
  - C was done ("Name coverage is clean").
  - A was done with the exclusions above. The final message claims more than was done: "The file breaks down into 976 distinct clause shapes, and I gave every one a label."
  - B: it said "Next I'm running the loose superset check and reading the dossiers." `loose.py` found 92 people and wrote their dossiers (themselves keyword-filtered) to `dossier.txt`, but the command printed only `head -1` (the count and the ID list). No dossier was read.
  - The unclassified-keyword check (`unc.py`) is keyword-limited.

**S2Bopus55000413** (plan CV-opus55-00041-3: shape inventory with every shape labelled and unmarked shapes read; loose superset check; unresolved-name sentences; near-miss audit).
- **a1, fail (missed P-104). Code: L2 by method, with a structural hole.**
  - The inventory was built from segments. Each segment starts at a match of `SUBJ=r'\b([A-Za-z][a-z]*\.? (?:<surnames>)|(?:Youth |Y)\d+|[Oo]rganization \d+|\bI\b|\bme\b)'`, which is case-sensitive for youth IDs, and is cut at the first sentence end.
  - Text that does not begin at a recognised subject is in no segment. Every lowercase youth line ("youth 104 ...", "y097 ...") falls in this gap. The 515-shape list it read after the verb filter contains no lowercase youth line. The agent's later count: "There are 23 lowercase ones".
  - Its claim: "I sorted every sentence fragment in the file into about 500 wording patterns".
  - The loose superset check (keyword-based by design) and the near-miss dump both ran.
  - **Why P-104 was missed.** c2 needs the ward's course. The segment-based youth facts never contained "youth 104 ...". The near-miss dump `d.py` looked up youths with `\b(Y|Youth )0*%d\b`, which is case-sensitive. For Y104 it returned only the guardian line ("-- Y 104 [('D-01283', '... D. Gupta is the legal guardian of Youth 104.')]"). The verdict: "P-104: their youth has no course on record."
  - **Plan steps** were executed as written. The hole is in the denominator of step 3, not in a skipped step.
- **a2, pass. Code: L1.** "The answer was marked wrong, so I'll recheck two things: wordings my templates could have missed, and corrections that might cancel facts I counted." The first command included an identifier-format census, `grep -oiE "\b(youth|y)[ #-]?[0-9]+" context.md | sed -E 's/[0-9]+/N/' | sort | uniq -c`, which printed "161 YN | 136 Youth N | 10 yN | 13 youth N".
  - It also audited speaker attribution, listed everyone passing c2-c5 whatever their c1, checked alias forms, and printed the finalists' segments. Then it fixed `SUBJ` to `[Yy]outh |[Yy]`.
  - "What went wrong: my subject pattern recognised youth labels only when written "Youth 104" or "Y104"."
  - New evidence came before the answer changed, so not G. The fix came from a format census, which is L0/L1 under the convention.

### Opus, arm B1 (one-pass plan, one answer)

**S2B1opus55000411** (plan CV1-opus55-00041-1: alias audit; template mining with the unmatched residue read until it is empty; tri-state table; near-misses; dossiers read in full for all candidates, near-misses, everyone SAT on the selective conditions, and everyone with 3+ SAT and no REFUTED). Pass.
- **Code: L2.** `pred.py` took the predicate after each of the 8,312 recognised name mentions (lowercase first names included) and reduced them to 262 templates, read in full with Read. "Only the two unrostered Priyas remain unresolved. Here are all 262 predicate templates."
- `q.py` covered the text that has no name subject: pronoun clauses, clauses with `Y\d+|Youth \d+` (case-sensitive), and any clause containing `evening|daytime`. Its 206 lines were read in full with Read, and they include "C: The same account also says that youth 104 currently attends <eveningC> during the evening".
- **Point for the author:** the person-attributed text was enumerated completely. The non-person text was reached only through pronoun, Y-token and `evening|daytime` nets, so P-104's course line came in through a keyword net. Under a strict reading of the convention that part is L1-grade.
- A sentence-level inventory (`t2.py`, 2,961 templates, verb exclusion, `head -150`) was also printed but not read to the end.
- **Plan steps.** Template step and near-miss review done. The dossier step was started for the 5 candidates only, then dropped: "The sentence splitter breaks on initials, so this view drops some lines. I'll print the extracted facts for these people instead, since those come from the initial-aware parser." The plan's wider dossier set was never attempted.

**S2B1opus55000412** (plan CV1-opus55-00041-2: sentence labelling; a coverage residue loop until no condition-keyword sentence is unexplained; unlinked-name audit; 160 × 5 matrix; near-misses; full dossiers for anyone with 2+ NO-EVIDENCE cells; finalists re-read). Pass.
- **Code: L2 (with exclusion).** `tmpl.py` gave 1,226 clause templates. A `grep -vE` dropped templates containing `recommended|discussed|owns a|visited the|helped with|attends the <club>|familiar names|roster records` or bare speaker tags, and printed the rest in two parts (`head -300`, then `tail -n +301`), so all of it was shown. The printout contains "youth 104 currently attends evening_pottery during the evening" and the other lowercase youth lines.
- After that, the extractor and completeness checks are keyword-based ("the totals for this-year events, evening and daytime classes, "dairy" and "train" matched the extracted facts. I read the leftover mentions of "prefer", "eat" and fruit by hand").
- **Plan steps.** Residue loop done (keyword-defined in the plan itself), name audit done, near-misses done, finalists re-read through their extracted sentences. The full dossiers for people with 2+ NO-EVIDENCE cells were not run, and the final message does not mention them.

**S2B1opus55000413** (plan CV1-opus55-00041-3: tag every line with broad keywords and read every residual; settle c2 youth by youth; a loose tier, with every passage of every loose candidate read; near-miss filter; whole-file fallback above about 300 residuals). Pass.
- **Code: L1.** The template inventory (401 templates) was looked at only through a keyword grep (`grep -iE "event|volunt|guardian|youth|...|\bI\b" templates.txt | head -300`).
- The residue is the keyword-tagged clauses its patterns did not classify (`if not KW.search(cl): continue`). It was 608, then 104, then 168 lines, read after `grep -v` filters, and the last run printed `head -30`.
- The per-person view (`show.py`) keeps only keyword sentences (`ss=[s for s in ss if KW.search(s)]`). It ran for the 5 finalists and the 10 near-misses.
- Lowercase youth IDs came from a phrasing census (`grep -oE "[^ ]+ [^ ]+ [^ ]+ (evening|daytime)_[a-z_]+..." | uniq -c`) and from an explicit fix (`NAME=r'(?:[Yy]outh \d+|[Yy]\d{3}|...`).
- **Plan steps.** Executed on keyword hits only, which is what the plan's step 2 itself specifies. Step 3 (youth by youth) was reduced to the census. Step 4 (loose tier, every passage read) was reduced to 15 people with keyword-filtered views. The final message says "I reread every passage that mentions any of the five". In fact, only their keyword sentences were printed.

## Summary (Claude's reading, for Zili Luo to judge)

**Did the one-pass runs (B1) do more coverage in execution than the retry runs (B)? No, not for either model.**

- **Sonnet.**
  - B: one L2 (B-1), two L1. B1: no L2 (one weak L1, one L1, one strong L1).
  - B1 spent less: attempt-1 cost $1.00 against $1.84 for B, and 17.0 tool calls per run against 22.7.
  - Its plans were at least as ambitious. One was a whole-file chunked read (an L3 plan), one a template inventory with a whole-file fallback, one person dossiers.
  - All three B1 runs dropped or shrank the plan's main coverage step: B1-1 not attempted, B1-2 dropped silently, B1-3 reduced (and says so).
  - All three B runs also dropped or shortened parts of their plans: B-2 and B-3 abandoned the inventory, and B-1 shortened verification.
  - The two Sonnet failures (B1-1, B1-3) both came after a near-miss look at P-104 that used a case-sensitive youth pattern.
- **Opus.**
  - B attempt 1: three inventory-type runs coded L2, but one exclusion hid the P-104 line (B-2) and one had a segmenter hole (B-3, failed).
  - B1: two L2 (B1-1, B1-2) and one L1 (B1-3).
  - Attempt-1 cost was about equal ($3.17 for B1 against $3.28 for B), with 23.7 against 27.3 calls.
  - By code count, B1 did no more full coverage than B. If Opus B-3 a1 is coded by text actually covered (L1), it is 2 L2 in each arm.
  - The B1 3/3 against B 2/3 difference in pass rate rests on one run, Opus B-3 a1. That run did execute its inventory plan, and it failed through a case-sensitive subject regex in its segmenter. *Inference:* the extra pass in B1 reflects which pattern bugs each run happened to make more than any extra coverage effort from the one-pass sentence. Opus B1-3 (L1) and Opus B-2 (an exclusion that hid the line) both passed only because their patterns had been generalised from other lowercase youth lines.

**Other observations (seen, not inferred):**
- In every attempt that missed P-104 (Sonnet B1-1, Sonnet B1-3, Opus B-3 a1), the agent did look at P-104 as a near-miss. Each time it fetched the ward's lines with a case-sensitive `Youth |Y` pattern, saw only the guardian line, and wrote that the course was absent ("fail c2 ... on explicit text", "the youth has no evening-course evidence", "their youth has no course on record").
- The decisive line "youth 104 currently attends evening_pottery" appeared in a printout the agent had in context in these passing attempts: Sonnet B-1, Sonnet B-2, Sonnet B1-2, Opus B-1, Opus B1-1, Opus B1-2 and Opus B1-3.
- In Opus B-2 and Sonnet B-3 the line was never printed. Opus B-2 passed by generalising its youth pattern from other lowercase lines. Sonnet B-3's first full extraction already included P-104; I did not trace which regex caught the line.
- Three final messages claim more coverage than the transcript shows:
  - Opus B-2: "I gave every one a label", though 286 skeletons were filtered unread.
  - Opus B1-3: "I reread every passage that mentions any of the five", though only keyword sentences were printed.
  - Sonnet B1-2: "read every passage about each finalist and near-miss", though the sentences were keyword-filtered.
- Opus B-3 a1 is in the same position: "I sorted every sentence fragment in the file", though there was a segmenter hole.
- Several runs, by contrast, say plainly what they skipped (Sonnet B-2, B-3, B1-1, B1-3; Opus B1-1).
