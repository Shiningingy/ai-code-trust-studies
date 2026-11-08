# Study 04 follow-up H.4: another agent model (report Section 7.5), fixed before running

Written 2026-11-08 ~02:00 (commit a34b0a0), before any run of this follow-up. Exploratory; results go in the follow-up report next to H.1-H.3 and cannot change the main verdicts.

**Question.** Do the main results carry to a stronger agent? Section 7.5 lists "other agents and models" as future work. This follow-up reruns the three main arms with Claude Opus 5.5 as the agent instead of Sonnet 5.5, on the same 56 PRs.

**What stays the same.** Prompts (Appendix D), summaries, harness, tools, container, time limit, effort (medium), stage 1, the two inspectors (Opus main, Sonnet agreement), rubric, and the Holm-corrected tests of H1 (+HumanReview vs Baseline) and H2 (+HumanReview vs +AgentReview). Only the agent model changes. The harness already supports this (`agent.py --model opus`, used for the pilot's ceiling check); runs go to `runs/prs/<id>/arms/{A,B,C}-opus/`.

**Order, so a partial run is still a fair sample.** The quota and time run out at the weekly reset (Sun 2026-11-08 14:00), so the run may not finish. PRs are taken in a fixed random order (seed 4), split across three work streams by repository. Pass 1 runs Baseline and +HumanReview for each PR (enough for H1), pass 2 adds +AgentReview. The oracle arm (H.2) runs first in each stream, since it was planned earlier.

**Analysis.**
1. H1 and H2 on the PRs with the needed Opus arms complete, same tests, labelled exploratory; the number of PRs is reported, and no verdict is claimed below the main plan's 30 PRs.
2. Sonnet vs Opus on the same PRs and arms: mean rubric per arm and model, and whether the +HumanReview gain is larger, smaller or similar (descriptive only).
3. Cost per arm (median tokens, seconds), as in Section 4.6.
4. Stage 1 resolved counts per arm.

**Known threat.** The main inspector is Opus, now the same model as the agent; self-preference could raise Opus agents' scores. All Opus arms share this, so H1/H2 within Opus are less affected than the Sonnet-vs-Opus comparison, which is reported with that caveat. The Sonnet inspector's scores are reported alongside.
