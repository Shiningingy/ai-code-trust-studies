# Model-Built References and Graphs for Car Manuals: Where People Still Matter

Zili Luo · Independent study, November 2026 · Proposal from reading; no experiment run · Not peer reviewed

## Abstract
Two EMNLP 2025 Industry papers build car-assistant knowledge from owner's manuals with LLMs. GEAR [1] grades an assistant's
answers against reference answers that GPT generates from the manual. The spatial knowledge graph (SKG) paper [2] has a
vision-language model build a graph of dashboard components, then answers "Where is X?" with landmarks picked from it. Neither
paper can be fully reproduced from what is released, so this study does not try. It records what can and cannot be rebuilt,
and proposes two questions. First, would a glossary of the manual's terms, built before anything else, help GEAR's reference,
assistant and judge agree on what counts as the same fact, and do GEAR's measures notice facts the reference does not contain?
That one comes with a setup whose labels are known by construction. Second, would landmarks chosen from what drivers already
know, and given one at a time, serve drivers better than three at once? No result is claimed here.

## 1. Why a proposal, not a replication
**GEAR.** All prompts are printed (Figs. 3-15), the assistant's retrieval settings are given (Table 2), and the source is a
public manual (Tesla Model 3, 2024). No code or data link appears in the paper, and none was found on 3 November 2026. The
generated question-answer set and the human annotations are not released, and the Gemini and DeepSeek versions, temperatures
and seeds are not stated. The human checks also need people: three annotators for the references (Table 3), one automotive
expert for the fact tags (Table 4) and six annotators for the judge (Table 5). So the pipeline can be rebuilt; the tables
cannot be checked.

**SKG.** All prompts are printed (Prompts 1-11), and the expert's annotations and ground-truth landmarks are public [3],
with references to the source manuals instead of the images. Code is not mentioned, the curated QA questions are not stated
as released, and the LLM judge's prompt is not printed. So the landmark agreement (Table 2) could be rebuilt against real
human labels; the QA comparison (Fig. 5) could not.

Both papers are industry work with a company partner, so withheld data is expected. The questions below are chosen so that
they need no large new annotation.

## 2. GEAR: what it settles and what it leaves open
GEAR splits the reference and the assistant's answer into atomic key facts, tags reference facts as essential, optional or
safety-critical, and asks an LLM judge, one prompt per metric, which facts are covered, correct and relevant. On 75 of the
754 questions, the references agreed with three annotators at 80.2 to 91.2 percent (Table 3), and the judge's completeness
scores correlated with six annotators at 0.86 to 0.91 (Table 5). The authors note that generated references "may not always
match human-authored references" (Limitations).

Two points stay open:
- **Facts outside the reference.** By the correctness prompt, an assistant fact the reference does not mention is set aside
  (Fig. 12), and the relevance prompt does not check truth (Fig. 13). What the measures can see therefore depends on how much
  the reference covers.
- **What counts as the same fact.** "Covered" means semantically equivalent, decided by the judge on each call (Fig. 11). The
  annotators agreed least on relevance (ICC 0.553, Table 8).

## 3. Idea 1: a domain vocabulary first
**Where it comes from.** I build software by directing Claude Code. Keeping a shared glossary of domain terms, a "ubiquitous
language" in domain-driven design [4], has made its output more stable and of better quality. That is my experience, not a
measured result. Car manuals have the same need: Giebisch et al. [5] report a car-manual assistant treating "standby" and
"idle" as interchangeable.

**Question.** Does a glossary built from the manual first (its terms, their definitions, and which words name the same thing)
help the reference, the assistant and the judge agree on what counts as the same fact?

**Setup.** One public manual, GEAR's printed prompts, about 100 questions. Four kinds of change are inserted into assistant
answers:

| Insert | How it is made | Correct label, known in advance |
|---|---|---|
| True, outside the reference | A fact from another part of the manual, on the same topic | correct |
| Altered | A manual fact with one detail changed (a number, a step order, a warning) | wrong |
| Term swap | Two manual terms that mean different things, swapped | wrong |
| Control | No change | baseline |

Three configurations: GEAR's judge as printed; the judge given the glossary; the assistant also using the glossary to rewrite
queries. The measure is how often each of GEAR's metrics changes for each kind of insert. A person checks a sample of the
inserts (do they read naturally?) and the glossary entries against the manual. No car expertise is needed, because the manual
is the authority, as it is in GEAR. That check also gives a number for a question GEAR leaves open: how much a short human
review of the glossary changes the results.

**Cautions.** If the reference, the assistant and the judge share one glossary, a wrong entry passes on every side, so the
judge-side and assistant-side uses must be tested apart. Copying true facts from neighbouring sections mirrors how GEAR's own
generator adds two similar sections, which the write-up must say. And the study would test GEAR's prompts on another model,
not GEAR as published.

## 4. SKG: what it settles and what it leaves open
The goal is to answer "Where is X?" with landmarks a driver can already find, not with another unknown button. A
vision-language model labels every dashboard component's size and estimated use frequency, and every pair's proximity and
relative position. A fixed formula, an equal-weight average of the mapped labels, ranks each component's partners, and the top
three become its landmarks. The best setup matched one expert's landmark choices 71.3% of the time, after the frequency term
was dropped (Table 2). Answers built from the graph scored higher than image-only answers on an LLM judge (0.397 vs 0.225,
Fig. 5).

Two points stay open:
- **What drivers already recognise.** Landmarks are ranked from what the model sees in the diagram and its estimate of use
  frequency, not from what drivers actually know.
- **All at once.** The answer gives all three landmarks in one turn, the same for every driver.

## 5. Idea 2: landmarks drivers already know
**Familiarity from real questions.** The paper set aside a fixed landmark list because such landmarks are not labelled in every
diagram, and its stand-in for familiarity, the model's estimate of use frequency, lowered agreement. What drivers already know
could instead be read from what they ask. A component used often but never asked about (where the diagram labels it) is likely
a safe anchor. One rarely used and never asked about is merely obscure, so the two signals need combining.

**Progressive disclosure.** If a driver recognises one landmark but not the other two, three at once does not help. The graph
already stores each landmark's own neighbours, so an answer could start from the most familiar landmark and add more only when
asked. This is the setting of referring-expression generation [6] and of reference as a collaborative process [7].

**Setup sketch.** Real query logs are not public, so the familiarity half needs a partner with an assistant in use. The
disclosure half can start with simulated drivers: for each target, sample which components a driver knows, and count the turns
until the target is placed, for three-at-once versus familiar-first answers, using the public annotations [3]. A study with
real drivers would have to follow.

## 6. Related work found
A short search on 3 November 2026, not a systematic review. Errors inserted into judged answers: FBI [8] found evaluator LLMs
missed them in over half of cases on average. Small or domain-adapted judges: ARES [9], which grades against retrieved
passages rather than a reference. Glossaries in RAG: used for retrieval [10]. Car-manual QA: Giebisch et al. [5] and the
DelucionQA hallucination dataset [11]. Not found: a test of facts outside a generated reference, or a judge given a domain
glossary.

## 7. Limits
No experiment has been run, so nothing here is a finding. Statements about both papers come from reading them in full; the
GEAR prompt behaviour in Section 2 is read from the printed prompts, not observed. The glossary benefit is my experience. I am
not a car expert, so every check proposed here is against the manual, not the real vehicle. Several related-work items were
read as abstracts only.

## 8. How this was written
I read both papers in full with Claude Code's help (structured summaries, then my own reading). The ideas in Sections 3 and 5,
the glossary, familiarity from real questions and progressive disclosure, are mine. The literature search and the drafting of
this text were done with Claude Code under my direction.

## References
1. N. Beyranvand, H. Dastmalchi, A. An, H. Davoudi, W. Chan, R. DiCarlantonio. GEAR: A Scalable and Interpretable Evaluation Framework for RAG-Based Car Assistant Systems. EMNLP 2025 Industry Track, 2792-2810. https://aclanthology.org/2025.emnlp-industry.187/
2. S. Bakos, C. Xing, H. Davoudi, A. An, R. DiCarlantonio. Generating Spatial Knowledge Graphs from Automotive Diagrams for Question Answering. EMNLP 2025 Industry Track, 2270-2286. https://aclanthology.org/2025.emnlp-industry.157/
3. Vehicle components dataset. https://github.com/steve-bakos/vehicle-components-dataset
4. E. Evans. Domain-Driven Design: Tackling Complexity in the Heart of Software. Addison-Wesley, 2003.
5. R. Giebisch et al. Automated Factual Benchmarking for In-Car Conversational Systems using Large Language Models. IEEE IV 2025. arXiv:2504.01248
6. R. Dale, E. Reiter. Computational Interpretations of the Gricean Maxims in the Generation of Referring Expressions. Cognitive Science 19(2), 1995.
7. H. H. Clark, D. Wilkes-Gibbs. Referring as a Collaborative Process. Cognition 22(1), 1986.
8. S. Doddapaneni et al. Finding Blind Spots in Evaluator LLMs with Interpretable Checklists. EMNLP 2024. https://aclanthology.org/2024.emnlp-main.911
9. J. Saad-Falcon et al. ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems. arXiv:2311.09476
10. Terminology Enhanced Retrieval Augmented Generation for Spanish Legal Corpora. LDK 2025. https://aclanthology.org/2025.ldk-1.16
11. M. Sadat et al. DelucionQA: Detecting Hallucinations in Domain-specific Question Answering. Findings of EMNLP 2023. https://github.com/boschresearch/DelucionQA
