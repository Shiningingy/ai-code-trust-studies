# Step 2 method coding, Opus 5.5, arms A and B (Claude's proposed coding, for Zili Luo to check)

**Cost correction (2026-11-25).** Costs below come from the uncorrected summary, which added up cumulative session totals for runs with retries. Only B-00002 changes: its total is $0.98 (not $1.53), so arm B is $4.62 for 6 runs, about $0.77 a run (1.7x Opus arm A). See results-step2.md.

Everything below is Claude's proposal. Codes are the frozen ones in `plan.md` (L0-L3, G, K). The convention is the one in `coding-step2-notes.md`: a keyword-limited residue (sentences that contain the agent's own topic keywords but match none of its patterns) is **L1**. L2 needs the residue of all passages, every passage of every person not ruled out, or a template inventory over all passages with the unlabelled shapes read until none are left. Sources: `runs/step2_summary.jsonl`, the `runs/step2/<run>-a<N>.jsonl` transcripts, read through `scripts/trace_digest.py`, plus the tool results where a code depended on them (B-00013 shape file, B-00002 roster check). The answer-key folder was not opened.

**K (key access): none.** The summary records `key_access: false` for all 13 attempts, and no transcript mentions `lhb-data` or `answers`.
**G (guess-and-check): none.** The only retry (B-00002 a2) gathered new evidence before it changed the answer.

## Table

| Run | Attempts | Pass attempt | Code per attempt | Executed the plan's coverage step? | Deciding quote |
|---|---|---|---|---|---|
| S2Aopus55000001 | 1 | 1 | a1 L1 | n/a (PH plan: near-miss only) | "I started from the 16 current night-shift mentions and checked each one's travel and employer statements" (plus a `grep "night shift" \| grep -v` residue on its own keywords) |
| S2Aopus55000002 | 1 | 1 | a1 L1 (weak) | n/a | "Near-misses that fail on the city: P-041, P-104, P-121 and P-142 take public transport and work nights" (near-miss rows printed from its own table; it re-read the source only for the 5 matches and P-133) |
| S2Aopus55000003 | 1 | 1 | a1 L1 | n/a | "People who pass c2 and c3 but work for an inland organization: Dev Gupta (P-104) ..." (re-greps those names' employer sentences) |
| S2Aopus55000011 | 1 | 1 | a1 L1 | n/a | Masks every matched fact, then sweeps 23 topic keywords over what is left: "I also caught a few sentences with unusual wording, such as 'P. Gupta volunteer at…'" |
| S2Aopus55000012 | 1 | 1 | a1 L1 | n/a | "I also checked the eight people who meet three of the four, and each one fails for a stated reason." |
| S2Aopus55000013 | 1 | 1 | a1 L1 | n/a | "my first run found only three matches ... It missed two quotes because they used 'continued,' instead of 'said,' and ungrammatical verbs" (found by its near-miss check) |
| S2Bopus55000001 | 1 | 1 | a1 L1 | Partly: steps 1-4 (keyword sweep, read all 112 leftovers, phrase census, pronouns); step 5 (per-person review of everyone with no negative) not done | "I read all 112 keyword sentences that my patterns hadn't already handled." |
| S2Bopus55000002 | 2 | 2 | a1 L1, a2 L1 | Partly: topic audit (B) done on keyword hits; person-centric audit (A) not done as written; final re-read shortened | a1: "Only 13 hits were left, and all were filler"; "For the other three, the table shows the sentences the parser matched; I didn't reopen those passages." |
| S2Bopus55000003 | 1 | 1 | a1 L1 | Partly: leftover-text audit (A) done on keyword hits; per-person check (B) and the review of everyone with no disqualifier reduced to matches + 14 near-misses | "I searched broadly for transport, shift and employment words. The only extra wordings were ..." |
| S2Bopus55000011 | 1 | 1 | a1 L1 | Partly: broad-tier residual (3″) and attribution list (4′) done; dossiers for everyone with at least one "yes" (5′) not done | "I listed every sentence in the file touching work, volunteering, dairy or transport that my main patterns hadn't already handled. There were only 29" |
| S2Bopus55000012 | 1 | 1 | a1 L1 | No (template labelling started, then dropped) | "I didn't label all ~1,200 sentence templates one by one. Instead I listed every phrasing in the file that mentions work, dairy foods, travel or volunteering" |
| S2Bopus55000013 | 1 | 1 | a1 **L2** | Yes, mostly (template inventory A, keyword nets B, attribution audit C) | "Now the template inventory (step A)"; "I grouped all 2,370 passages by sentence pattern and wrote the matching rules from that list ... A loose keyword search then left only five unclassified sentences" |

Cost per run (summary file): A 0.33 / 0.39 / 0.34 / 0.54 / 0.50 / 0.58 = **$2.66** for 6 runs. B 0.47 / 1.53 (0.55 + 0.98) / 0.67 / 0.83 / 0.93 / 0.75 = **$5.17**.

## Per run

**A-00001** (sample 0, pass a1, $0.33, 9 calls). It took a census of the night-shift phrasings, then ran a residue over its own "night/overnight/graveyard" keywords and over its transport keywords. It anchored on the 16 current night-shift people and read each one's travel and employer statements. It grepped the employer sentences of the inland near-misses (Dev Gupta, Amina Gupta, Ben Ortiz, Amina Chen). It noticed the lowercase roster entries (P-101, P-141). L1.

**A-00002** (pass a1, $0.39, 16 calls). It ran a predicate-phrasing census after every name (keyword-limited) and a grep of first-person quotes. Its script printed every person with at least two conditions, with the facts it had extracted. It re-read the source only for the 5 matches and for P-133's shift. This is near-miss work, but mostly read from its own table, so the code is a weak L1 (the author may prefer L0).

**A-00003** (pass a1, $0.34, 9 calls). It split all passages into sentences. It then printed every sentence with a night or transport keyword, minus the "former role" and "no longer/once/future" forms, and re-grepped the near-miss names for employer facts. L1.

**A-00011** (sample 1, pass a1, $0.54, 17 calls). It masked every matched fact and swept 23 keywords (dairy, milk, ..., work, org, volunteer) over what was left. That found two irregular sentences ("P. Gupta volunteer at", "I currently work for Org 031"). It then read the near-misses' transport and dairy sentences. The residue is keyword-limited, so L1. It is a broad keyword list, though, and close to the L1/L2 line.

**A-00012** (pass a1, $0.50, 14 calls). It took phrasing censuses per condition, then built per-person evidence for the 5 matches and the 8 people who met three of the four conditions, filtered by topic keywords. L1.

**A-00013** (pass a1, $0.58, 15 calls). Its first extraction gave 3 people (P-024, P-082, P-131). The near-miss check ("Next I'll check the near-misses for their missing condition") grepped 14 people and then counted every first-person "I ..." statement. That found "I currently works" and "N. Tran continued", which add P-091 and P-154. This is the clearest case of the PH plan's near-miss step catching a miss inside attempt 1. L1.

**B-00001** (sample 0, plan CV-00000-1, pass a1, $0.47, 12 calls). It ran plan steps 1-4 as written: a broad keyword sweep, a leftover file with matched spans removed (`left.txt`, 112 items, read in full), a 3-word phrase-frequency count after names, and a pronoun grep. Step 5, a review by hand of everyone with no negative and at least one unknown, was not run. It only checked one near-miss (P-133) and the 5 matches. It never said it had skipped step 5. The plan's own leftover step is keyword-limited, so even the executed part is L1 under the convention.

**B-00002** (plan CV-00000-2, fail a1, pass a2, $1.53 total).
- **a1 (L1, $0.55).** It split every passage into per-name-mention segments and classified them. Its leftover check was the keyword-filtered unused segments (13 hits, "all were filler"), plus the text before the first name in each passage. The plan's person-centric audit A (all unexplained mentions per person, with no keyword filter) was not run. It also shortened the final re-read: "For the other three, the table shows the sentences the parser matched; I didn't reopen those passages."
- **What was missed in a1.** P-101 (Amina Foster). This was an identity miss, not a fact-wording miss. Her roster line is lowercase ("records amina foster under identifier p-101"), and its roster regex required capitals. Its coverage step did surface her, and it wrote: "Amina Foster also meets all three conditions ... But the roster gives them no ID, so they can't go in the answer." The roster check behind that conclusion was a case-sensitive grep cut off by `head`, and it never showed the lowercase line.
- **a2 (L1, $0.98, 9 calls).** It audited its own pipeline step by step: compound clauses inside the used segments, every predicate occurrence with no resolvable name before it, alias collisions, then the roster format ("grep -c identifier", lines with non-standard identifier wording). That found "Some roster records are lowercase, e.g. 'amina foster under identifier p-101', and my case-sensitive parser missed them." It re-parsed the roster case-insensitively (160 IDs, not 155), reran the pipeline and added P-101. New evidence came before the changed answer, so not G. None of the a2 checks covers all passages, so L1, not L2.

**B-00003** (plan CV-00000-3, pass a1, $0.67, 20 calls). It ran the leftover-text audit as a `grep -v` of its known templates over keyword sentences, then `uniq -c`. It did an "identifier" accounting ("I'll print every identifier mention my strict pattern missed"), which caught the lowercase P-101 roster entry, and it compared extracted fact counts against raw keyword counts (160/160/160). The plan's per-person check of all 153 IDs, and the review of everyone with no disqualifier, shrank to the 5 matches plus 14 near-miss passages. L1.

**B-00011** (sample 1, plan CV-00001-1, pass a1, $0.83, 20 calls). It ran a template survey over all sentences but printed only the shapes that hit its keywords (L1-grade). Its first table gave 3 people. Then it ran the plan's broad-tier residual (29 sentences, "none changed anyone's status") and the attribution list of unresolved "I" subjects. A fix to the speaker lookup there added P-091 and P-154. The plan's dossiers for everyone with at least one "yes" (5′) were limited to the matches and 7 near-misses. L1.

**B-00012** (plan CV-00001-2, pass a1, $0.93, 21 calls). It built the sentence and clause template inventory, but it had about 1,200 shapes, so it dropped the plan's step of labelling every template until none is left: "I didn't label all ~1,200 sentence templates one by one. Instead I listed every phrasing in the file that mentions work, dairy foods, travel or volunteering". It then built keyword-filtered dossiers for 12 people (matches and near-misses). L1. This is the same retreat as Sonnet B-00000-2 and B-00001-1 ("Too many templates").

**B-00013** (plan CV-00001-3, pass a1, $0.75, 14 calls). It built a template inventory over all 2,370 passages (1,612 clause shapes). It dropped the shapes whose verb is on its own list of irrelevant predicates (recommended / owns / discussed / visited / attends / helped with) and three fixed filler openers, then read the remaining 606-line shape file in full with one Read. It wrote its rules from that list. A keyword net then left 5 unclassified sentences, all irrelevant. It also ran an attribution audit: every this-year event assigned, and each event ID matching its volunteer. Proposed **L2**: a full-file inventory with the residue read to the end. Two points for the author:
- The 1,612 → 606 cut used an exclusion list of verbs, not a keyword inclusion list.
- It did not save the shape labels as a rule table, as the plan said.

## Summary (Claude's reading, for Zili Luo to judge)

**RQ1 (arm A: PH plan, near-miss at best, plus pass/fail).**
- All 6 Opus runs passed on attempt 1, all at L1. No run reached L2, and the feedback never fired, so arm A shows nothing about whether pass/fail alone drives Opus to full coverage.
- Total cost $2.66, about $0.44 a run.
- The near-miss step did real work inside attempt 1. In A-00013 it found the 2 quote-worded people its first extraction missed.
- Sonnet in arm A: 4 of 6 passed on attempt 1, and the 2 retries were fixed at L1 or L0. Opus was cheaper to the first pass per run on sample 1 only because it needed no retries.

**RQ2 (arm B: CV plan with full coverage described).**
- L2 first appears at **attempt 1, in 1 of 6 runs** (B-00013, $0.75 to that point).
- In the other 5 runs it never appears. That includes the one retry: B-00002's a2 is a targeted L1 audit. That retry was not a coverage failure: the a1 audit had found the missed person, and the roster parse lost her ID.
- Arm B cost $5.17, about $0.86 a run: about 1.9x Opus arm A, and 2.4x Sonnet arm B ($2.15).

**Opus vs Sonnet on running the coverage step.**
- Opus ran more of it, but not by much. Sonnet's arm B: 6 of 6 L1, with explicit skips ("I did not run the full template profiling").
- Opus's arm B: 5 of 6 L1 and 1 of 6 L2.
- Opus read its whole keyword residue every time (112, 13, 29 and 5 items), where Sonnet mostly looked at its residue.
- Where both met an inventory of more than 1,000 templates, Opus dropped it once (B-00012) and pushed through once (B-00013).
- In 5 of 6 Opus B runs, the step that would have made the run L2 is the one that was skipped or shrunk: the per-person review of everyone not ruled out, or labelling every template.

**A scoring point to flag.** Several Opus 1c plans scored FULL in step 1c because their main coverage step is a broad keyword sweep minus matched text (CV-00000-1 steps 1-2, CV-00000-3 audit A, CV-00001-1 tier 3″). Under the step-2 convention that same step, run faithfully, is L1. So "executed the plan's coverage step" and "L2" are not the same thing here. Each of those plans also has an L2-grade step (per-person review of everyone not ruled out, or a template inventory), and that is the part the runs dropped. The author may want to say which step of each plan counts as "the" coverage step.
