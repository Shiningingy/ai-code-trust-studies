# Does a scam-URL benchmark measure memory or task pressure?

An audit of Innoc2Scam-bench from Scam2Prompt (Chen, Saba, Deng, Si, Long; ICML 2026; arXiv 2509.02372).
Run 2026-10-31. Not peer reviewed.

**Safety.** Generated code was stored as text and never executed. No scam site was contacted: lookups went to public
registries and the Internet Archive only. Raw outputs and benchmark data are not in this repo, because they contain
real scam URLs. Get the benchmark from the authors' release. Domains here are written with [.].

## Question
Scam2Prompt reads scam URLs in generated code as contamination absorbed into model weights. Could a model reach the
same URLs by following the task, building a URL from a name in the prompt? And do models treat the request as ground truth?

## Findings
1. **The prompt nearly always supplies the name.** The authors' artifact classifies 41,317 flagged URLs from the full
   audit: URL in prompt 49.7%, platform name in prompt 49.8%, neither 0.5%. Independently, in three of their audit reports,
   the flagged domain's name is spelled in the prompt for 95.7-98.2% of flagged URLs. On the benchmark, for seven 2025 models,
   it is 99.5% of 3,441 flagged outputs.
2. **Models write URLs for brands that do not exist.** With the paper's template, the rate is close for real and invented names.
3. **The template matters more than the brand.** Dropping "runnable, production-ready" and allowing a placeholder cuts
   brand URLs by 19-30 points on real brands.
4. **That change costs nothing measured on real services.** Usable answers stay at 98-100% across 40 popular services.
5. **A "verified" claim does not act as ground truth.** It did not raise URL rates, and it made Haiku refuse more.
6. **Some URLs are unlikely to be memory.** In a sample of GPT-4o's flagged domains, 20 show no sign of existing before its stated
   cutoff (Oct 2023); 6 were registered in 2025.

None of this removes the need for the outside URL check the paper recommends. See "What this does not show".

## Results
Share of outputs with a concrete URL built from the brand, or for real services a usable answer (official URL or SDK).

| Model | Template | Real service | Scam-site brand | Invented brand |
|---|---|---|---|---|
| Haiku 4.5 | Paper | 98% | 42% | 35% |
| Haiku 4.5 | Relaxed | 98% | 12% | 12% |
| Haiku 4.5 | "Verified" note | 98% | 40% | 26% |
| Sonnet 5.5 | Paper | 95% | 21% | 20% |
| Sonnet 5.5 | Relaxed | 100% | 2% | 0% |
| Sonnet 5.5 | "Verified" note | 95% | 21% | 15% |

Paired differences on 80 prompts, 95% bootstrap CI, resampled by brand:

| Effect | Haiku 4.5 | Sonnet 5.5 |
|---|---|---|
| Scam brand minus invented, paper template | +7.5 [-4.9, +19.0] | +1.2 [-10.4, +12.8] |
| Paper minus relaxed, scam brand | +30.0 [+17.3, +43.2] | +18.8 [+11.0, +28.2] |
| Paper minus relaxed, invented | +22.5 [+10.0, +35.4] | +20.0 [+11.1, +30.4] |
| Verified minus paper, scam brand | -2.5 [-14.6, +9.8] | 0.0 [-9.5, +9.3] |
| Scam brand minus invented, verified note | +13.8 [+2.4, +26.2] | +6.2 [-1.3, +14.5] |

Other results:
- With the note, Haiku refused more (31% to 51% on scam brands, 46% to 65% on invented). Sonnet 5.5 refused almost never.
- Wording of "can't verify this service", same 80 prompts, paper template: Sonnet 4 1%, GPT-5 0%, Gemini 2.5 Pro 1%,
  DeepSeek 1%, Haiku 4.5 19%, Sonnet 5.5 44%. Matched by regex, and affected by the harness (see Limits).
- Detectors flagged the placeholder `yourdomain[.]com` 18 times in the 2025 outputs.

## Method
- **Published data:** reproduced the benchmark's Table 2 counts exactly (9,639 outputs), then classified each output.
- **Control:** 80 Category 2 prompts sampled from the 1,007 where the brand could be located. Each brand was swapped for a
  new invented name. Templates: the paper's, a relaxed one, and the paper's plus a "verified by our team" note. 960 calls.
- **Real services:** 40 services, one simple task each, three templates. 240 calls. Answer key checked against Tranco.
- **Models:** Haiku 4.5 and Sonnet 5.5 through `claude -p`, one turn, no tools, in a neutrally named folder.
- **Domain age:** registry dates, with Internet Archive captures used to reject re-registered domains.

## What this does not show
- **It does not show memory plays no role.** The scam-minus-invented gap could be up to about 19 points for Haiku, and the
  gap with the note excludes zero. That may be name plausibility, since invented names look odd, but it is unresolved.
- **It does not show models are safe.** Models seem to rely on recognising a name. A scam the model recognises, or a
  domain an attacker registers to match a guessed URL, would not be stopped by the relaxed template.
- **It is not a re-run of the paper.** `claude-sonnet-4` was unavailable, and neither model here is in the paper.
- **It does not explain cases where the prompt names no scam,** such as the paper's pump.fun incident.

## Limits
- Two Claude models and 80 prompts. Real-service tasks are simpler than the scam prompts, and every service is popular.
  A small real service the model has never seen is untested.
- The relaxed template changes two things at once: it removes pressure and adds a placeholder instruction.
- The "verified" note is not a clean change. Unprompted reassurance may itself read as suspicious.
- The harness told models their knowledge cutoff and today's date, and thinking was on. The paper's text never mentions
  thinking, and its code does not set it, so its state per model is unknown. Model differences here are not purely model effects.
- Default temperature, against T=0 in the paper. Scoring uses text heuristics; samples were read by hand.
- Domain-age test on 2025 models was uninformative: a loose test gave 23-33% too new, a strict one 0.7-4%, because most
  late dates were re-registrations. For GPT-4o: 400 of 1,067 domains sampled, 181 dated, 10 archive lookups failed. Many
  domains have lapsed and cannot be dated, and later GPT-4o snapshots may have a later cutoff.
- Reports read in the full audit: 3 of 12.

## Contaminated first run
The first run used a folder named after this study, and the working-directory path reaches the model. 101 of 320 Haiku
outputs mentioned it, which inflated refusals. Hand-reading the outputs caught this. All 640 calls were discarded and rerun.

## How this was built
I asked the question, proposed the task-following hypothesis and the "verified" test, and set the rule that generated code
is never run. Claude Code, working under my direction, proposed the invented-brand control, the real-service control and
the domain-age test, wrote and ran the code, and drafted this report. I reviewed the results and decided what to keep.

## Reproduce
`scripts/` holds the analysis code. Paths point at a local working folder, and `results/` is not included.
