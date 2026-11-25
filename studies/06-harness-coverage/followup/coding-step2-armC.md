# Step 2, arm C (critic): method coding of the 12 runs

**Claude's proposed coding, for Zili Luo to check.** It was written 2026-11-25 from the transcripts (`runs/step2/<run>-a<N>.jsonl`), the critic logs (`<run>-critic.jsonl`) and `runs/step2_summary.jsonl`. The codes follow plan.md (L0-L3, G, K) and the convention in `coding-step2-notes.md`. A keyword-limited residue or a keyword-filtered per-person dossier is coded **L1**, and a phrasing census is pattern work (L0/L1). A check on unresolved or unrostered names is coded L1, as in A-00000-2/-3. Nothing was run or edited apart from writing this file.

**Critic challenge classes.** Each challenge is classed by the claim it rests on. Where a challenge mixes claims, the note says so.
- **(a) correct and useful:** a real bug in the proposed step, or a check the answer depends on (even when the check then confirmed the worker).
- **(b) wrong:** rests on a false claim about the file or the worker's state. This includes misreadings caused by what the critic is shown (see "Harness findings" below).
- **(c) process or cosmetic:** file paths, edit style, a "the file was never written" bookkeeping note, or phrasings the critic imagined with nothing in the file behind them.

## Table

| Run | Att. | Pass at | Code per attempt | Critic calls / challenges | a / b / c | Deciding quote |
|---|---|---|---|---|---|---|
| S2Csonnet55000001 | 4 | 4 | a1 L0, a2 L1, a3 L1, a4 L1 | 30 / 7 | 1 / 4 / 2 | a4: "My roster parse was case-sensitive and missed lowercase entries like "amina foster under identifier p-101"." |
| S2Csonnet55000002 | 1 | 1 | L0 | 15 / 5 | 0 / 4 / 1 | "I didn't read each of the 156 employer matches individually." |
| S2Csonnet55000003 | 1 | 1 | L1 | 15 / 3 | 0 / 2 / 1 | "Four names matched no roster entry, so I checked them by hand. None qualifies." |
| S2Csonnet55000011 | 1 | 1 | L1 | 18 / 3 | 2 / 1 / 0 | "I'm checking all 27 candidates for dairy, transit and organization together" (sentences filtered by `dairy\|Organization\|tram\|train\|bus\|subway\|metro\|travel\|transit`) |
| S2Csonnet55000012 | 1 | 1 | L1 | 13 / 1 | 0 / 1 / 0 | per-candidate dossier filtered by `kw=re.compile(r'work\|dairy\|travel\|tram\|bus\b\|train\|subway\|milk\|butter\|cheese\|Org',re.I)` |
| S2Csonnet55000013 | 1 | 1 | L1 | 10 / 0 | - | per-candidate sentences filtered by `kw=re.compile(r'works for\|dairy\|travel\|bus\b\|...')` |
| S2Copus55000001 | 1 | 1 | L1 | 10 / 0 | - | "Amina Foster's roster entry is written in lowercase, so my first pass missed it, and I found P-101 by searching for her directly." |
| S2Copus55000002 | 1 | 1 | L1 | 23 / 7 | 6 / 0 / 1 | "Who didn't, among the other current night-shift workers: Inland employer: P-041 and P-063 ..." |
| S2Copus55000003 | 2 | 2 | a1 L1, a2 L1 | 47 / 16 | 9 / 2 / 5 | a1: "Checking who has a current night shift, and what they're missing." a2: "Some roster entries are lowercase or use "lists" instead of "records", so five people ... were never loaded." |
| S2Copus55000011 | 2 | 2 | a1 L1, a2 L1 | 65 / 32 | 15 / 9 / 8 | a1: "Next I'll pull each candidate's passages that mention employment, dairy or travel." a2: "some passages are written entirely in lowercase, which my case-sensitive org→city grep would have skipped." |
| S2Copus55000012 | 1 | 1 | L1 | 19 / 7 | 2 / 3 / 2 | "Now pulling every candidate's passages (full name, alias, and quoted "I" from them as speaker) with the broadened keywords" |
| S2Copus55000013 | 1 | 1 | L1 | 28 / 10 | 4 / 3 / 3 | whole passages per candidate kept only `if pat.search(p) and kw.search(p)`; then "I'll pull out just the clauses about work, diet and travel for each candidate" |

No run reached L2 or L3. **G: none**: every changed answer followed new evidence-gathering in that attempt. **K: none**: no tool call touched `answers`, `lhb-data`, a parent folder or another run's folder (all 297 calls scanned), and `key_access` is false for every attempt.

Borderline cases to check: Opus 00012 and 00013 printed *whole passages* for each of the 27-28 candidates and read all of them (00013 in four `Read` pages). They kept only passages that contain a keyword, though, and the keyword sets are broad (`work|org|dairy|travel|...`). By the convention this is L1, but it is the closest any arm-C run came to L2's "reads every passage for each person not ruled out".

## Per run

**S2Csonnet55000001 (pass at a4, $2.65, 382 s).**
- a1 (L0) used strict patterns, then "Five names ... have no roster ID ... I didn't check whether any of them would otherwise qualify." It missed P-018 and P-101.
- a2 (L1) ran a phrasing census plus a keyword residue: "works for org N" hits not preceded by a known name. It found employer sentences without "currently" and first-person quotes, which added P-018. It also grepped the unresolved names.
- a3 (L1) built a dossier of every night-shift person. The answer did not change. The worker refused to infer Amina Foster's ID from the roster order ("I won't guess").
- a4 (L1) ran a case-insensitive census of "identifier" forms and found the lowercase roster entry, which added P-101.
- Critic, 7 challenges:
  - #2 (a): the `re.sub` replacement contained `\d`, which would have crashed with a bad-escape error.
  - #1 and #3 (c): blind stacked `sed` edits.
  - #4-#7 (b): P-006/046/066/101/141 "never appear anywhere in context.md". P-101 is in the file as "records amina foster under identifier p-101". The critic was echoing the worker's own case-sensitive grep, and it reinforced the worker's a2/a3 belief that "one qualifying person has no ID anywhere in the file".
- Worker response: it complied with #1-#3. With #4-#7 it neither complied nor argued: it resubmitted variants of the roster listing until the 3-challenge auto-approve. The blocked listings were case-sensitive and would not have found P-101.
- Coverage: the critic's repeated "resolve the ambiguous aliases (amina foster ...)" is roughly what a4 then did, but its false premise pointed away from the roster.
- 4 of this run's 34 calls have no critic entry (see Harness findings).

**S2Csonnet55000002 (pass a1).**
- L0: a phrasing census of "travels by" and "night shift", the city list, then the script.
- Critic, 5 challenges:
  - #1 (b): "before the agent has listed the full set of org cities ... city-list output was truncated". The worker had listed them with `uniq -c`; the critic saw that output cut at 500 characters.
  - #2 (c): the copy is pointless because the blocked heredoc never wrote `a.py`, which is true. It also called the worker's scratchpad path "invented".
  - #3-#5 (b): the scratchpad "uses session ID 7bd3d6fa…, not this session's". 7bd3d6fa is the worker's real session. The critic named a different UUID each time, its own. #3-#4 also claim "32 org cities"; there are 10 cities across 32 organizations.
- Worker response: it complied with #1 ("The enumeration confirms the ten cities and the coastal set I used"). It resubmitted the same script against #3-#4, then sidestepped by piping the script to Python on stdin and writing no file.

**S2Csonnet55000003 (pass a1).**
- L1: a script, then a hand check of the four unrostered names.
- Critic, 3 challenges:
  - #1 (c): move `a_tmp.py` out of the project folder.
  - #2-#3 (b): the critic again substituted its own session's scratchpad UUID.
- Worker argued: "The hook has given a different "real" scratchpad ID on every attempt, so I can't act on it. I'll avoid the question and write no files."

**S2Csonnet55000011 (pass a1).**
- L1: candidates came from event IDs (3+ this-year events). For each of the 27 candidates, the worker read the sentences that mention the person and contain a keyword.
- Critic, 3 challenges:
  - #1 (b): "nothing the agent has seen shows that format; the visible passages use ... "Leah Chen helped with cleanup at the museum"". The file has 277 "volunteered at event-P-NNN-N during this-year" mentions; "helped with" lines are distractors.
  - #2 (a, check): confirm that the event-ID P-number is the volunteer.
  - #3 (a, bug): initial-only matching without the initial-ambiguity guard could credit "G. Jones" to the wrong Jones.
- Worker complied with all three ("That's a fair point").

**S2Csonnet55000012 (pass a1).**
- L1: a census of employment sentences, then keyword-filtered dossiers for the 27 candidates.
- Critic, 1 challenge (b): the pattern "I currently chooses to avoid dairy" "will likely match nothing" because the text reads "choose".
- Worker argued and widened the pattern: "N. Tran's quote literally says "chooses", so I'll match both spellings."

**S2Csonnet55000013 (pass a1).** L1: keyword-filtered sentences for the 27 candidates, plus keyword-filtered whole passages for 4 people. The critic made 10 approvals and no challenges.

**S2Copus55000001 (pass a1).** L1: phrasing census, a parser, then a direct search for the one unresolved name. That search found P-101. The critic made 10 approvals and no challenges.

**S2Copus55000002 (pass a1).**
- L1: every name mention in every passage was segmented and attributed, with unknown names tagged "?". Only keyword segments were kept. The worker then checked every night-shift worker for the conditions they fail.
- Critic, 7 challenges:
  - #1 (a, bug): the alias regex stopped at the first initial's period. Its diagnosis was off: Amina Foster was unresolved because of the lowercase roster entry, not the alias regex.
  - #2 (a, bug): the worker invented the first names "Farah Patel" and "Fiona Silva"; the roster has only "f. patel" and "f. silva".
  - #3 (a, bug): full names were keyed by initial and surname.
  - #4 (a, bug): unlisted names such as "Rosa Foster" were not treated as segment boundaries.
  - #5 (c): the file was never written.
  - #6 (a, check): look up every organization's city, including relocations.
  - #7 (a, bug): a `.{0,40}` cut would have dropped the city names.
- Worker complied with every challenge ("The reviewer is right", "Fair point", "Good catch").
- This is the clearest case of a critic improving attribution before the first answer. It pushed toward accounting for names, not passages.

**S2Copus55000003 (pass a2; 918 s, $4.91).**
- a1 (L1): parser, near-miss look at all night-shift people, a corpus-wide predicate census that was started and abandoned, and a keyword sweep. Its answer of 4 people missed P-101.
- a2 (L1): a census of first name plus roster surname across the file turned up unrostered full names. The worker then fixed the roster regex for lowercase entries, "lists" and initial-only entries, and checked all 160 IDs ("158 of the 160 entries. Finding the last two"). That added P-101.
- Critic, 16 challenges: 9 (a), 2 (b), 5 (c).
  - The (a) challenges are real code bugs or checks:
    - #1-#2: first-person quotes use curly quotes.
    - #3: the org→city map had 14 of 32 organizations.
    - #6: clauses are packed into one sentence.
    - #9: `head -150` truncated the census.
    - #12: merged sentences.
    - #13: lowercase surname slot.
    - #15: positional awk fields.
    - #16, which was decisive: "five full names (Amina Foster, ...) ... are not on your roster ... map them to IDs before chasing day-shift quotes". The worker had produced that evidence itself and was moving on; the challenge sent it back, and the fix followed.
  - (b) #4: St. John's "probably has a curly apostrophe". It is a straight apostrophe.
  - (b) #8: the split regex "never closes its `[`" and contains mojibake. The worker's regex was `[.;"“”]`; the critic saw it garbled (see Harness findings).
  - (c) #7, #10, #11 and #14 imagined phrasings such as "commutes by bus" and "moved to the night roster", which are not in the file; #5 was about edit style.
- Worker complied almost always ("Fair points", "Agreed").
- Coverage: #7, #9 and #10 pushed toward coverage (print every line about the candidates, then make the corpus-wide census complete). After three blocked census calls the worker retreated: "The survey is noisy, so I'll use a targeted keyword sweep ... instead". So the critic asked for coverage, and the friction it caused coincided with the worker dropping it.

**S2Copus55000011 (pass a2; 1,139 s, $5.74).**
- a1 (L1): keyword-filtered passages for the 27 event-ID candidates. It treated orgs 003/011/016/022 as cityless and missed P-024 and P-082.
- a2 (L1): re-checked aliases and event attribution, then ran a keyword-limited city residue: city and coast words in lines without "is based in". That surfaced the lowercase passages: "some passages are written entirely in lowercase, which my case-sensitive org→city grep would have skipped". A case-insensitive rebuild added P-024 and P-082.
- Critic, 32 challenges:
  - a1: 4 (a), 9 (b), 5 (c).
    - (b) #1-#2: "Nothing seen so far uses an `event-P-<n>-<n>` pattern; volunteering appears as prose like "helped with cleanup"". False.
    - (b) #3-#5: the roster and "Organization N" phrasings are "guessed and have not appeared in any output". They had appeared; the critic saw them cut off.
    - (b) #6, #8, #9, #11: "the previous output was cut off at "Organization 00"" and "cut off at "Org 029=Vancouver Or"". The results were 1,102 and 626 characters long; the worker saw them whole, and the critic sees 500. #6's suggestion of a full org→city table was still adopted: "The hook's suggestion is better than my hand-picked list".
    - (a) #7: GNU grep's `\t` is not a tab. #12: `[^\n]` in ERE. #15: the sentence splitter breaks at initials. #10: combined clauses.
  - a2: 11 (a), 0 (b), 3 (c).
    - (a) #20: a variable-width lookbehind would crash. #21-#22: leftmost-match capture. #23: `not` matches "note". #27: `port` matches "transport". #31: a broken diff.
    - (a) #28: rebuild the org→city map case-insensitively. This seconded the lead the worker had just found itself.
- Worker response: it argued once, against #13 ("c2 is already settled from the event IDs, so I won't add volunteer keywords"). It resubmitted the same employment command four times while #23-#26 kept re-opening the settled c2 condition, and it ignored #29 once.
- Coverage: in a2 the worker first wrote a per-candidate residue: every clause naming the candidate, minus known distractor templates, with no keyword filter. That is nearly L2, but challenge #19 blocked it ("keep the first-name allowances, and print the skipped clauses"). The critic asked for *more* coverage, but the rewrite put a keyword filter back. So the challenge moved the worker away from the residue, though that was not what it asked for.

**S2Copus55000012 (pass a1).**
- L1: whole passages per candidate, filtered by broadened keywords, all read via `Read`.
- Critic, 7 challenges:
  - #1-#2 (b): `grep -o "event-P-[0-9]*-[0-9]"` "also matches inside `old-event-P-...`". False: old events are written "old-event-P-NNN during last-year", with no "-N" suffix, so the pattern cannot match them.
  - #3 (a, bug): the awk step dropped the event suffix before `uniq`, so it counted names, not events.
  - #4 (a, check): the negation check and the org-city facts.
  - #5 (c): imagined synonyms.
  - #6 (b): "never pulls passages where the candidate speaks as "I"" and the script "crashes ... for a. evans (P-081)". The worker rebutted both: "The passage search already catches "I" quotes ... and P-081 isn't a candidate".
  - #7 (c): the file was never written.

**S2Copus55000013 (pass a1).**
- L1: keyword-filtered whole passages for the 28 candidates, read in full, then clause extraction. It also listed every `event-p` mention its volunteer pattern did not capture, a residue for c2 only (`UNCAP`).
- Critic, 10 challenges:
  - #1 (b): the same false `old-event` claim as in 00012.
  - #2 (a): the passage truncation `[:700]` was real. The nickname half was speculative, and the worker rebutted it ("The roster aliases are all "F. Last" initial forms").
  - #3 (b): the entry "I. Silva, M. …" is "a multi-alias entry whose second alias likely uses a different initial". In fact the comma starts a new clause.
  - #4 (a, check): the alias check could not see second aliases.
  - #5 (a, bug): the "a. evans" roster entry breaks `[a-z]+ [a-z]+`.
  - #6 (a): the uncaptured-mention residue, which the worker adopted.
  - #7 and #10 (c): files never written.
  - #8 (b): the `Read` at offset 130 "skips the first 129 lines ... the agent hasn't read yet". The offset-1 `Read` was issued in the same turn, in parallel, and the critic was not shown it (see Harness findings).
  - #9 (c): imagined "relies on public transport" and pronoun follow-ups; neither exists in the file.

## Where the time and money went in the two longest runs

Times are measured from transcript timestamps and critic log times. Critic wait is the time from the tool call to the critic's decision; it includes starting the hook process.

| Run | Wall (transcript) | Critic wait | Tool execution | Worker turns | Worker $ | Critic $ | Calls blocked |
|---|---|---|---|---|---|---|---|
| S2Copus55000003 | 899 s | 468 s (52%), 47 calls, about 10 s each | 27 s | ~404 s | 2.67 (a1 1.16 / 38 calls; a2 1.51 / 9 calls) | 2.24 (46%) | 16 of 47 (34%); 205 s of critic wait on blocked calls |
| S2Copus55000011 | 1,124 s | 600 s (53%), 65 calls, about 9 s each | 29 s | ~495 s | 2.76 (a1 0.87; a2 1.89) | 2.98 (52%) | 32 of 65 (49%); 344 s of critic wait on blocked calls |

The time split roughly in half:
- About half went to waiting for the critic. The critic runs synchronously before every tool call, at 8-10 s per Opus call. Tool execution is negligible.
- The other half went to worker turns, and the challenges inflate this too: every blocked call costs a worker turn to rewrite it, plus another critic call on the rewrite.
- In 00011, 9 of the 32 challenges rest on the critic's 500-character view. Four in a row (#23-#26) re-opened a condition the worker had already settled.

Attempt-2 worker turns are expensive because the resumed session carries the whole first attempt: 00003 paid $1.51 for 9 calls. The cost is driven by worker turns and critic calls together. Neither alone explains it.

## Harness findings (for review; nothing was changed)

1. **The critic sees results cut to 500 characters and calls cut to 600** (`critic_hook.py` `transcript_tail`). This is the source of every "output was cut off", "has not appeared in any output" and "script isn't visible" challenge (Sonnet 00001 #1, Sonnet 00002 #1, Opus 00011 #1-#6, #8, #9, #11). The worker had the full output each time.
2. **The critic projects its own environment onto the worker.** Each critic call is a fresh `claude -p` session whose system prompt names its own scratchpad. In Sonnet 00002 and 00003 it "corrected" the worker's real scratchpad path to a new UUID on every call (5 challenges).
3. **Encoding.** The hook runs as `python -I` (which ignores `PYTHONIOENCODING`) and reads stdin with the Windows code page (GBK), so curly quotes in the worker's commands reach the critic as mojibake ("鈥", Opus 00003 #8 and the "garbled curly-quote" parts of #1-#2). In Sonnet 00001, four calls containing `“`/`”` have no critic log entry and finished within 1-4 s including execution. Reviewed calls took 2-17 s for the critic alone. The hook probably exited with an error before calling the critic, which Claude Code treats as non-blocking, so those calls ran unreviewed. One of them was the a4 script that found P-101. Opus calls with curly quotes were reviewed, so the cause is likely but not proven.
4. **Implementation fix 1 also hides parallel sibling calls.** Dropping every trailing call without a result removes the other calls of the same turn too. That is why Opus 00013 #8 claimed the first 129 lines were unread: they had been read in the same turn.

## Summary

- **Did the critic ever lead to L2 or L3?** No. All 16 attempts are L0 or L1.
  - Four challenges did ask for more coverage: Opus 00003 #7, #9 and #10 (drop the keyword filter, make the corpus-wide census complete) and Opus 00011 #19 (print the skipped clauses). In both runs the worker ended at a keyword filter: 00003 abandoned the census after three blocks in a row, and in 00011 the rewrite after #19 replaced a near-L2 residue with a keyword filter.
  - The coverage-like steps the critic did produce were name- and anchor-level accounting: Opus 00003 #16 (unrostered names, decisive), Opus 00002 (tag unknown names), and Opus 00013 #6 (uncaptured event mentions).
- **Did it help?** Of 91 challenges, 39 were (a). They caught real bugs before they ran:
  - a `re.sub` bad escape, GNU grep `\t` and `[^\n]`, a variable-width lookbehind, positional awk fields, and leftmost-match captures;
  - attribution errors in Opus 00002.
  - Twice the critic pointed at the fix for a failed attempt: Opus 00003 #16 led directly to P-101, and Opus 00011 #28 seconded the worker's own lead.
- **Did it hurt?** 29 challenges were (b): the critic made false claims about the file or the state.
  - Sonnet 00001: P-101 "never appears", 4 times.
  - Sonnet 00011 and Opus 00011: volunteering is not recorded as `event-P`.
  - Opus 00012-13: the pattern matches `old-event`.
  - Opus 00003: a curly apostrophe in St. John's; an unclosed bracket that was really mojibake.
  - Wrong scratchpad paths (5) and "cut off" views (several).
  - None of these caused a wrong final answer: the workers rebutted or routed around them. Sonnet 00001's false claim reinforced the worker's wrong belief across a2 and a3.
- **Results compared with arms A and B.** First-attempt passes: arm C 9 of 12, A 10 of 12, B 11 of 12. Arm C also has no plan, so this mixes the effect of the critic with the effect of having no plan.
- **Cost share of the critic** (critic_cost / total_cost, from `step2_summary.jsonl`):
  - Sonnet: $2.04 of $5.29 (39%). Opus: $8.27 of $16.39 (50%). All 12 runs: $10.31 of $21.68 (48%).
  - Per run: Sonnet 25 / 55 / 51 / 59 / 46 / 44%; Opus 48 / 57 / 46 / 52 / 51 / 53%.
  - The critic also inflates the worker's own cost through rewrite turns and longer sessions. Opus arm C's worker cost alone ($8.11) is three times arm A's whole cost ($2.67).
  - Wall time per run roughly doubles: about half of every run is spent waiting for the critic (Sonnet 49%, Opus 52% of transcript time).
