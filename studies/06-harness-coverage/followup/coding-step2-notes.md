# Step 2 method coding: working notes (Claude's proposals; Zili Luo checks)

Codes are the frozen ones in plan.md (L0-L3, G, K). Digest tool: `scripts/trace_digest.py <run_id>`.

**Coding convention used (flag for Zili Luo).** A "keyword-limited residue" means listing sentences that contain the agent's own topic keywords but match none of its extraction patterns. Sentences without the keywords are never looked at. That is the Study 06 HV blind spot, so it is coded **L1**, not L2 (L2 needs the residue of *all* passages, or every passage of every person not ruled out). A "phrasing census" (grep a keyword, normalise names, `uniq -c`) is pattern work, coded L0/L1.

## Sonnet plans (scored under the frozen step-1 / 1c rules)
- PH (step 1), 6/6 PARTIAL: each plans a near-miss look. 00000-1 "spot-check near misses, meaning people who meet two conditions"; 00000-2 "spot-check a few near-misses"; 00000-3 near-misses that fail one condition plus "a random sample of passages"; 00001-1 "look at near-misses, people who satisfy three conditions"; 00001-2 "people with two events, or people who match three conditions"; 00001-3 "spot-check near-misses, meaning people who satisfy three conditions". Several say "spot-check", weaker than Opus's "every near-miss".
- CV (1c), 6/6 FULL: 00000-1 a dossier of every kept passage per person, read in full (filler templates dropped, a sample of them checked); 00000-2 "list every sentence template in the file ... read all of the templates"; 00000-3 "go person by person and read everything about each one", plus an "unattributed" file; 00001-1 template every passage, "any passage left unlabeled counts as a failure ... until zero"; 00001-2 classify every passage, "read all the 'other' passages, or a large sample"; 00001-3 passages that mention a known person but match no template, "repeat until the unmatched residue is only distractors".
- Sonnet near-miss definitions vary more than Opus's: exactly two of three with the third missing/unresolved (00000-2); 3 Pass + 1 non-Pass, *or* 2 Pass + 2 Unknown (00001-1); exactly 3 of 4 (00001-3).

## Arm A, Sonnet (PH plan + pass/fail)
- A-00000-1: pass a1. L1: the final reply lists the night-shift people who fail one condition and catches P-155 there ("P-155 should have been included. I'm correcting that now").
- A-00000-2: pass a1. L1 (checks "ambiguous aliases, the two unresolved names").
- A-00000-3: pass a1. L1 (checks first-person "I work..." quotes and the A. Haddad / F. Silva unresolved roster entries).
- A-00001-1: a1 fail (missed P-091), a2 pass. a2 = L1: reads the passages of 8 near-miss people, then a first-person phrasing census (`grep -ohE "\bI [a-z]+ [a-z]+ [a-z]+" | uniq -c`) finds "I currently works for", which its regex missed. Quote: "P-091's employer is only given in a quote: K. Ortiz said, \"I currently works for Org 005\". My regex missed that phrasing".
- A-00001-2: a1 fail (2 of 5), a2 pass. a2 = L0 (pattern widening): "I'll look for phrasings my patterns missed ... Public transport also covers tram, train and subway, so my bus-only pattern was too narrow". Also fixed a "St. John's" → "St" city parse bug.
- A-00001-3: pass a1. L1: keyword-limited residue (dairy / travel sentences minus its standard templates, `grep -v "currently chooses to avoid dairy products\.$"`), then greps of 7 near-miss IDs. Began the plan's template step, then "Let me grep the relevant keywords directly."

## Arm B, Sonnet (1c plan, which describes full coverage, + pass/fail)
All 6 passed on attempt 1, so RQ2's "attempt at which L2/L3 first appears" is: never needed, and in most runs never executed.
- B-00000-1: L1. Near-miss check: "Five more have two conditions and one unknown ... I'm checking those for phrasing my patterns missed." Template look at the start.
- B-00000-2: L1 (keyword-limited residue, `resid.txt`: sentences with shift/work/travel/... words left after removing its patterns). Tried the full template census first and abandoned it: "Too many templates, because the name normalisation is loose. I'll look at the sentences that touch the three conditions instead." Then accounted for all 16 night-shift mentions: "All 16 current night-shift people are accounted for."
- B-00000-3: L1 ("checking the leftovers"; per-name greps of unresolved people).
- B-00001-1: L1 (keyword-limited residue, `resid.py`, filtered by dairy/volunteer/work/travel/... words) after a template census that "is too many" (5,072) and was refined; then near-miss dossiers.
- B-00001-2: L1. Says so itself: "I did not run the full template profiling and 'other' passage review from the plan. Instead I listed every phrasing of the facts that matter".
- B-00001-3: L1 (keyword-limited residue: "RES" lines for dairy / volunteered / works for / travel after masking matched spans): "the parser's residue contains only distractors". Also: "I did not do its separate organization and city tables or the final per-candidate re-read".

## Arm C
(pending)

## Framing decided with Zili Luo (2026-11-25, during the night run)
- One-pass vs retries matters little once the focus is cost: retries show whether the agent can solve it at all, and the main number is cost to the first correct answer. The attempt-1 result is still reported as the view comparable to one-pass benchmark scoring.
- Open question he raised: is full coverage an exploit of this benchmark? Claude's reading, for him to judge: it is not reward hacking (it answers by doing the task), but it is only cheap because the generator uses a small fixed set of sentence templates. Report template-inventory methods as generator-dependent. The real exploit risks in step 2 are the pass/fail oracle (G, guess-and-check) and key access (K). The query does not state how many people qualify, so the count does not leak (checked both contexts).

## Zili Luo's instruction for the rest of the night (2026-11-25, ~01:50)
If the full suite is the same task (Constraint Solving Search, more instances), extend the current arms (A, B, C; same harness, prompts and limits) to the hardest instances once the Sonnet and Opus batches end, within the budget guard and session limit. If it is not the same task, do not run anything new: describe the hard tasks in the report for discussion.

## Full-suite check (subagent report, 2026-11-25 ~01:55): not run tonight, per Zili Luo's rule
- Report: a local note outside this repo, `full-suite-hardest-tasks.md` (sources: arXiv 2609.38137v1 incl. TeX, repo 6e3da81, HF StringNLP/longharness @ d6339b6).
- The suite is 4 different tasks × 50 instances, not all the same task, so no new arms were run. Hardest by the paper's Table 2 (mean over 25 configurations): Equivalent Program Pair Search 6.9%, Outlier Memo Detection 20.9%, Constraint Solving Search 21.8%, Program Execution Tracing 39.2%. The paper's protocol is one pass ("We report task-specific exact accuracy", §4.1; 3M-token budget per instance; no retries or verifier).
- Staged for discussion only: Constraint instances 2, 14, 29, 41 (5 conditions each, combining guardian-of, train-over-flying and fruit; none of these conditions occur in instances 0-1), at `E:\lhb-data-hard\{contexts,answers}`, SHA-256 checked against the HF DATA_CHECKSUMS. Same layout as `E:\lhb-data`, so `LHB_DATA=/e/lhb-data-hard` would run the arms on them (A and B need their plans generated first).
