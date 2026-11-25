# Step 1 results: plan-only probe, Opus 5.5 in Claude Code (2026-11-25)

Scores below are **Claude's proposals** under the frozen rule in `plan.md`; Zili Luo scores. Plans: `runs/plans/PH-opus55-*.md` (raw `*.jsonl`).

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
