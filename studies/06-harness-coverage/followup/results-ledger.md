# Read ledger and cost breakdown (2026-11-25, after the fact, no new model runs)

**Idea (Zili Luo).** Give every line of context.md a status, UNREAD at the start. Flip it to READ whenever its text is returned to the model. After the run, the UNREAD list shows exactly what the model never saw. This is different from the agents' own "coverage", which means that *their script* processed every line, and says nothing about what the model looked at.

**How it was computed** ([scripts/ledger.py](scripts/ledger.py), output [data/ledger.jsonl](data/ledger.jsonl)). Unit = sentence of context.md (9,079-9,300 per file), because agents often print fragments rather than whole lines. A sentence is SEEN if its exact text appears in any tool result of the run (Read output, Grep hits, printed script output). A masked form such as `<P> enjoys eating <FOOD>` does not count. Applied to all 86 transcripts: Study 06 H, HC, HV (14 runs) and follow-up steps 2-3 (72 runs). Costs come from Claude Code's per-model usage records; the list prices fit them exactly ($/M tokens: Sonnet 5.5 input 2, cache write 4, cache read 0.20, output 10; Opus 5.5 4, 8, 0.20, 20).

## 1. The model sees 6-20% of the file in every arm

| Arm | Exact (first answer) | Sentences seen | Mean cost | = writing new content to context | + re-reading the context each turn | + output (scripts, reasoning, text) | Turns | Context per turn |
|---|---|---|---|---|---|---|---|---|
| Study 06 H (Sonnet) | 3/6 | 13% | $0.14 | $0.06 | $0.03 | $0.04 | 12 | 13K tokens |
| Study 06 HV (Sonnet) | 6/6 | 16% | $0.48 | $0.16 | $0.15 | $0.17 | 26 | 28K tokens |
| Step 3 B (Sonnet) | 3/3 | 12% | $0.61 | $0.23 | $0.17 | $0.21 | 24 | 37K tokens |
| Step 3 B (Opus) | 2/3 | 15% | $1.31 | $0.56 | $0.28 | $0.47 | 32 | 40K tokens |

(All 21 arms: see the script output in data/ledger.jsonl; the pattern is the same. Arm C costs here are the worker's only.)

Even HV, which had to pass a check that "every statement" was accounted for, showed the model only 16% of the sentences, against 13% for H. Its coverage was done by its script, not by reading.

## 2. Every miss came from a line the model never saw

The decisive trap lines: P-101's lowercase roster line (sample 00000) and P-104's lowercase youth-course line (sample 00041). First attempts only.

| Trap line on attempt 1 | Person found | Person missed |
|---|---|---|
| Shown to the model | 22 | **0** |
| Never shown | 27 | 12 |

- **No run that saw the line missed the person.** All 12 misses are runs in which the line never came back to the model.
- **But an unseen line is usually not a miss** (27 of 39): a script can parse a line correctly without printing it. Seeing everything is sufficient here; it is not necessary.
- So a ledger used as a gate ("no answer while lines are unread") would have caught every one of these misses, but it would also flag lines the scripts handled correctly.

## 3. Where HV's 3.5× went

HV cost $0.48 against H's $0.14. The extra $0.34 splits roughly in thirds:
- **Re-reading the context** (+$0.12): twice as many turns (26 vs 12), each re-sending a context twice as large (28K vs 13K tokens).
- **Output** (+$0.13): reasoning (7.0K vs 1.5K thinking tokens) and scripts written (about 5K vs 1K tokens of tool input).
- **New content written to context** (+$0.10): tool results and the agent's own messages.

**The line-to-template conversion itself costs no tokens**: it runs in Python. What costs tokens is the loop around it: writing the scripts, reading their printouts, fixing a failed check, and each turn re-sending the conversation.

## 4. Would reading every line be cheaper? (Claude's estimate, not run)

The file is about 179K tokens by Sonnet 5.5's tokenizer (the Direct runs' recorded input; Haiku 4.5 counts the same text as 128K, which is where the earlier "~120K" came from). In Claude Code at Sonnet prices:
- Bringing it all into context once costs about 179K × $4/M ≈ **$0.72**.
- After that, every turn re-reads it: about 179K × $0.20/M ≈ **$0.036 per turn**, so 15-20 turns add about $0.55-0.72.
- Total about **$1.3-1.5 per run**, roughly 3 times HV and 10 times H.

Study 06's Direct arm put the whole file in the prompt: $0.87 per run ($0.74 Sonnet, matching the estimate above, plus $0.13 for a background Haiku call Claude Code made on the same first prompt), 100% of sentences seen, 0/2 exact (6 of 10 people). Seeing a line in a 179K-token prompt is not the same as using it. Whether a Claude Code run that reads in chunks and writes notes does better is untested: Sonnet B1-1 planned exactly that and made zero Read calls.

**So for a one-pass task, structuring the text with scripts is the cheaper route here, because the scripts run for free.** Its weakness is not cost but silence: a line the script's rules miss is dropped without any visible sign, and the agent's own check uses the same rules.

## 5. What this suggests (Claude's reading; Zili Luo decides)

- **A ledger is cheap to keep in the harness** and cannot be relabelled by the agent. A middle form between "see everything" ($1.3-1.5) and "trust the script" ($0.14-0.48): after the agent answers, the harness lists the unseen sentences that touch an answer candidate or a near-miss, and the agent must look at those before its answer counts.
- A second column is needed to separate "unseen but correctly parsed" from "unseen and dropped": the lines the agent's extraction actually placed. That needs the agent's extracted data in a known format, which the HV arm had (`check_coverage.py`'s placed/irrelevant output).

## Limits

- Exact-text matching: a sentence printed with changed spacing or cut in the middle counts as unseen. A 30-character middle chunk is recorded separately (`part`); it does not change the picture.
- Seeing a sentence is not reading it with attention (Direct arm).
- Two trap lines, two samples. The 0-of-22 result is strong for these traps, not a general law.

## 6. What Claude Code itself does, and a cue that needs no reading (added 2026-11-25)

**Claude Code makes no relevance judgment; it only caps sizes.** Across 104 attempt transcripts: 1,594 Bash calls and 26 Read calls. A Read of the whole file returns "File content (459.9KB) exceeds maximum allowed size (256KB). Use offset and limit parameters to read specific portions of the file, or search for specific content instead of reading the whole file." (22 times). A Bash output over the limit is saved to a file and the model sees a 2 KB preview (7 times). Both push the model towards search and scripts.

**Rarity of a sentence's shape** ([scripts/rarity_check.py](scripts/rarity_check.py); shape = capitalised words → C, digits → N, case kept, nothing task-specific). All four trap sentences behind the misses (P-101's roster line and its employer's city line in 00000, P-091's quote in 00001, P-104's youth line in 00041) have a shape that occurs **once** in their file. About 1,500-1,650 sentences per file (17-18%) are in such one-off shapes. The reason is the generator: traps are rare variants of common templates (lowercase name, quote, connector phrase). In natural text, rare does not mean relevant, so this cue is benchmark-dependent. Opus B-2 had these very shapes in its inventory and filtered count-1 lines unread.
