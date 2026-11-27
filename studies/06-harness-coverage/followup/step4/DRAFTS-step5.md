# Step 5 model-facing texts that differ from step 4 (generated from prompts.py)

Only the document count changes; the hook messages, the test prompt and everything else are as in [DRAFTS.md](DRAFTS.md).

## Learning (learn_text(4))

The folder train/ holds four documents, doc1.md, doc2.md, doc3.md and doc4.md. Each is a long collection of short passages, generated from a fixed set of sentence templates, followed by a final query. The four documents share their grammar but not their content.

Your job is to write a grammar library that parses documents of this kind completely. Later sessions will get new documents of the same kind, with different queries, and will answer them by running your library and querying the facts it produces; they will not have time to relearn the grammar.

Use the framework in gram/ (read gram/README.md first) and write the library in lib/.

Treat the text as a small language and work out its grammar from the text itself, starting from the data, not from the queries:
- Find how lines are built from clauses: the connectors and the opening phrases that join or introduce them.
- For each kind of clause, separate the fixed wording from the slots (names, identifiers, objects), and collect every variant of the fixed wording that occurs.
- Find the words that change what a clause means, such as a time, a negation, a frequency, a hedge or reported speech. Keep them as qualifiers; never drop them.
- Find the forms in which the same entity is written, so that facts about one entity can be joined.

Then:
- Write rules for every construction you find, not only the ones the four queries ask about, because later queries ask about other things.
- Every clause of every content line of the four documents must be resolved: parsed by a rule, taken by an ignore-rule, or, only for text that no grammar should cover, entered in train/docN.manual.jsonl for that document.
- When a clause fails, decide which case it is. If its form is broken (case, punctuation, spacing, a small typo), write a Normalizer. If it is a construction the grammar lacks, write a Rule. Keep every part general: never write a part for one specific line or person.
- Give every part a clear `solves` line, `added_by = "learning"` and examples. `python -m gram test --lib lib` must pass.
- Keep notes for later sessions in lib/NOTES.md: what each family of parts covers, how facts are named (subjects, relations, objects, qualifiers), and anything a later session should know to query the facts correctly.

To check the library, answer the four final queries from the parsed facts and write the answers to answers.json as {"doc1": [...], "doc2": [...], "doc3": [...], "doc4": [...]}, each a sorted list of person IDs. When you stop, you will be told which answers are correct, whether the tests pass and how many clauses are still unresolved. Keep improving the library until all four answers are correct and nothing is unresolved.

## Reconcile (reconcile_text(4))

The folder train/ holds four documents, doc1.md, doc2.md, doc3.md and doc4.md, generated from a fixed set of sentence templates. Three grammar libraries were written for them independently, in lib_a/, lib_b/ and lib_c/, using the framework in gram/ (see gram/README.md). Each library's notes are in its NOTES.md.

diff.md lists the clauses on which the three libraries disagree, grouped by clause shape (group IDs G01, G02, ...), with what each library produced. A disagreement may mean one library is wrong, or that they name the same fact differently.

Build one library in lib/ that is right on all of them. Start from whichever library you judge best. For each group in diff.md, read the clauses, decide which output is right or write a better rule, and record the decision in lib/RECONCILE.md: one line per group, starting with its ID, saying what you decided and why. Write lib/NOTES.md for later sessions, as in the libraries you started from.

The library must meet the same requirements as the three originals: `python -m gram test --lib lib` passes, every clause of the four documents is resolved (train/docN.manual.jsonl only for text no grammar should cover), parts stay general, and answers.json holds correct answers to the four final queries, as {"doc1": [...], "doc2": [...], "doc3": [...], "doc4": [...]}. When you stop, you will be told which answers are correct, whether the tests pass, how many clauses are unresolved and which groups RECONCILE.md does not yet mention.
