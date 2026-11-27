# Step 1 results: plan-only probe, Opus 5.5 in Claude Code (2026-11-25)

Scores below are **Claude's proposals** under the frozen rule in `plan.md`; Zili Luo scores. Plans: [plans/](plans/) (`PH-opus55-*.md`; raw stream-json kept locally under `runs/plans/`, not committed).

| Plan | Cost | Turns | Proposed score | Deciding sentence |
|---|---|---|---|---|
| 00000-1 | $0.196 | 6 | UNCLEAR (near-miss only) | "Also scan near-misses, meaning people who meet two conditions, for a third fact my patterns missed because of unusual wording" |
| 00000-2 | $0.171 | 6 | UNCLEAR (near-miss only) | "I'll also check the near-misses, people who meet two of the three, to make sure I didn't drop a third fact through a phrasing variant." |
| 00000-3 | $0.133 | 5 | NO | Near-misses are re-read only "to confirm the subject is right"; the other recall-like step is a search for unseen wording ("commutes", "employed by"), which the rule does not count |
| 00001-1 | $0.122 | 5 | UNCLEAR (near-miss only) | "every near-miss that fails only one condition, I'd grep their name and aliases again and read the source sentences by hand. That confirms nothing was missed" |
| 00001-2 | $0.111 | 4 | UNCLEAR (near-miss only) | "every near-miss that passes three, I'd Grep the person's names and re-read the source sentences" (also a phrasing census with `uniq -c`, which the rule does not count) |
| 00001-3 | $0.138 | 5 | UNCLEAR (near-miss only) | "for anyone who meets three of the four conditions, I'd Grep their full name and short forms and read the actual passages" |

Total $0.87 for 6 plans. All exit 0.

**Reading (Claude's, not Zili Luo's).**
- No Opus plan has the full recall step: none examines the passages its extraction did not place, or fails if any passage is unaccounted for.
- 5 of 6 plan a partial one: re-read every near-miss (a person who fails exactly one condition) to look for a missed fact. Sonnet 5.5's Study 06 plan had a weaker version ("print the evidence sentences ... for a sample of near-misses").
- A near-miss check catches a person whose patterns missed one fact. It does not catch a person who fails two or more conditions only because of extraction misses, which is the Study 06 HC miss (one person whose facts used all three traps).
- The scoring rule did not anticipate the near-miss step; whether it counts is Zili Luo's call. The rule is unchanged.

**Fable 5.2: not run.** Claude Code 2.1.289 rejects `claude-fable-5-2` (`unrecognized_model`); the alias `fable` resolves to Fable 5.1. A one-line connectivity test to Fable 5.1 returned "safeguards flagged this message"; the full error text and category were not kept (output was filtered). Per the stop rule, no further Fable calls were made.

## Scores decided by Zili Luo (2026-11-25)
Near-miss step = PARTIAL recall. Step 1: 5 PARTIAL, 1 NO (00000-3), 0 FULL.

# Steps 1b and 1c (2026-11-25): own plan back, plus a hint
Plans: [plans/](plans/) (`RV-*` = 1b, `CV-*` = 1c). Proposed scores are Claude's; Zili Luo scores.

| Example-rep | 1b (we define near-miss and name the gap) | 1c (model defines near-miss, then: what if it is not enough) |
|---|---|---|
| 00000-1 | FULL: label every sentence consumed / known distractor / unclassified, read the unclassified ($0.065) | FULL: "confirm that every sentence that could carry one of these facts was either used or deliberately set aside" ($0.082) |
| 00000-2 | FULL: tag every passage; sweep leftovers; full file of passages for every person not ruled out ($0.071) | FULL: per-person and topic residual audits, "subtract the sentences my extractors already used ... read all of it" ($0.077) |
| 00000-3 | FULL: residue file of clauses no pattern explains, read until empty; 40-passage spot check ($0.071) | FULL: leftover-text audit plus per-person passages for everyone without a disqualifier ($0.086) |
| 00001-1 | FULL: residual sentences + "unaccounted-sentence audit" ($0.074) | FULL: read every broad-net sentence the strict tier missed, "not a sample" ($0.088) |
| 00001-2 | FULL: dossier of every sentence for each person with no explicit fail ($0.078) | FULL: label every sentence template; "anything unlabeled is residue", read until none ($0.088) |
| 00001-3 | FULL: account for every clause; unexplained clauses to a residual file, read until resolved ($0.070) | FULL: template inventory + keyword nets, rerun "until nothing is unexplained" ($0.092) |

- **Model's near-miss definitions (1c):** all six define a near-miss as a person who passes all conditions but one, where the remaining one is unknown or weakly supported, not explicitly disqualified. Several add that an explicit disqualifier (e.g. a current inland employer) removes the person.
- **Model's own cost estimates for the revision:** about 1.5x to 4x the original checking effort (roughly 10k to 60k extra tokens), against about 120k tokens to read the whole file. None ran the revision, so these are estimates.
- **Cost of the probes:** step 1 $0.87 (6), step 1b $0.43 (6, one turn each, no tool calls), step 1c $0.51 (6, one turn each). Total $1.81, plus the failed Fable test ($0.14).

**Reading (Claude's, not Zili Luo's).**
- Unprompted, Opus plans a near-miss re-check at best (PARTIAL). Once the gap is named, 12 of 12 revisions plan the full recall step: an accounting of every sentence or clause, with the unexplained residue read until it is empty. That is the coverage check Zili Luo imposed in Study 06, invented by the model.
- 1c is not a much weaker hint than 1b: its prompt still says the patterns "miss facts for several of that person's conditions", which names the failure. A truly weaker hint (e.g. only "could your plan still miss someone?") is untested.
- These are plans, not runs. Study 06 showed that an agent given a coverage check passed failed checks by relabelling statements irrelevant; whether these self-designed checks behave better when executed, and at what real cost, needs full runs.
