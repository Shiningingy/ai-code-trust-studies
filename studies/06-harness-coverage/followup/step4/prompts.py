"""Every model-facing text of step 4, in one place (DRAFT: Zili Luo approves before any run).
The hook messages are in hook.py (LEARN_MSG, RECON_EXTRA, TEST_MSG); review_drafts.py prints all of them."""

LEARN = """The folder train/ holds three documents, doc1.md, doc2.md and doc3.md. Each is a long collection of short passages, generated from a fixed set of sentence templates, followed by a final query. The three documents share their grammar but not their content.

Your job is to write a grammar library that parses documents of this kind completely. Later sessions will get new documents of the same kind, with different queries, and will answer them by running your library and querying the facts it produces; they will not have time to relearn the grammar.

Use the framework in gram/ (read gram/README.md first) and write the library in lib/.

Treat the text as a small language and work out its grammar from the text itself, starting from the data, not from the queries:
- Find how lines are built from clauses: the connectors and the opening phrases that join or introduce them.
- For each kind of clause, separate the fixed wording from the slots (names, identifiers, objects), and collect every variant of the fixed wording that occurs.
- Find the words that change what a clause means, such as a time, a negation, a frequency, a hedge or reported speech. Keep them as qualifiers; never drop them.
- Find the forms in which the same entity is written, so that facts about one entity can be joined.

Then:
- Write rules for every construction you find, not only the ones the three queries ask about, because later queries ask about other things.
- Every clause of every content line of the three documents must be resolved: parsed by a rule, taken by an ignore-rule, or, only for text that no grammar should cover, entered in train/docN.manual.jsonl for that document.
- When a clause fails, decide which case it is. If its form is broken (case, punctuation, spacing, a small typo), write a Normalizer. If it is a construction the grammar lacks, write a Rule. Keep every part general: never write a part for one specific line or person.
- Give every part a clear `solves` line, `added_by = "learning"` and examples. `python -m gram test --lib lib` must pass.
- Keep notes for later sessions in lib/NOTES.md: what each family of parts covers, how facts are named (subjects, relations, objects, qualifiers), and anything a later session should know to query the facts correctly.

To check the library, answer the three final queries from the parsed facts and write the answers to answers.json as {"doc1": [...], "doc2": [...], "doc3": [...]}, each a sorted list of person IDs. When you stop, you will be told which answers are correct, whether the tests pass and how many clauses are still unresolved. Keep improving the library until all three answers are correct and nothing is unresolved."""

RECONCILE = """The folder train/ holds three documents, doc1.md, doc2.md and doc3.md, generated from a fixed set of sentence templates. Three grammar libraries were written for them independently, in lib_a/, lib_b/ and lib_c/, using the framework in gram/ (see gram/README.md). Each library's notes are in its NOTES.md.

diff.md lists the clauses on which the three libraries disagree, grouped by clause shape (group IDs G01, G02, ...), with what each library produced. A disagreement may mean one library is wrong, or that they name the same fact differently.

Build one library in lib/ that is right on all of them. Start from whichever library you judge best. For each group in diff.md, read the clauses, decide which output is right or write a better rule, and record the decision in lib/RECONCILE.md: one line per group, starting with its ID, saying what you decided and why. Write lib/NOTES.md for later sessions, as in the libraries you started from.

The library must meet the same requirements as the three originals: `python -m gram test --lib lib` passes, every clause of the three documents is resolved (train/docN.manual.jsonl only for text no grammar should cover), parts stay general, and answers.json holds correct answers to the three final queries, as {"doc1": [...], "doc2": [...], "doc3": [...]}. When you stop, you will be told which answers are correct, whether the tests pass, how many clauses are unresolved and which groups RECONCILE.md does not yet mention."""

TEST = """A grammar library for documents of this kind is in lib/ (read lib/NOTES.md), built with the framework in gram/ (read gram/README.md). Run it on context.md: python -m gram parse context.md --lib lib --manual manual.jsonl --out out

If clauses are unresolved, handle each one. Read it as the library's grammar does: its fixed wording, its slots, and the words that change its meaning, which become qualifiers and are never dropped.
- If its form is broken (case, punctuation, spacing, a small typo), add a Normalizer.
- If it is a construction the library lacks, add a Rule.
- Only for text that no grammar should cover, enter it in manual.jsonl, with the facts it states or "ignore": true, and a reason.
Add new parts as new files in lib/parts/, each with `solves`, `added_by = "test session"` and examples, and add their names to lib/config.json if it lists parts by name. Do not edit the existing parts. `python -m gram test --lib lib` must still pass.

When every clause is resolved, answer the final query from the parsed facts."""
