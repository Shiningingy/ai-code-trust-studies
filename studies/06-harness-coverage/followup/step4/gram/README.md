# gram: grammar libraries for templated text

`gram` turns text that follows a grammar into facts, and reports every piece it could not handle. You write the
grammar as a library of small parts; `gram` runs them and checks them.

## A library

```
lib/
  config.json        which parts are used
  parts/             Python files; each defines one or more parts
```

`config.json`:
```json
{"splitter": "comma_and", "normalizers": ["straight_quotes"], "rules": "all"}
```
`"rules": "all"` uses every rule in `parts/`; a list of names selects some. Normalizers run in the listed order.

## Parts

Each part is a class with `name`, `solves` (one sentence: what it handles and why it exists), `added_by` (who wrote
it) and `examples` (these run as tests). Import them with `from gram import Splitter, Normalizer, Rule, PatternRule`.

- **Splitter**: cuts a line into clauses. Clauses must be pieces of the line, unchanged. Connector text between
  clauses may be dropped only if it matches one of the splitter's `droppable` regexes; any other lost word is an error.
- **Normalizer**: repairs the FORM of a clause (case, punctuation, spacing, small typos) before rules see it. It must
  keep every word: same number of words, each the same up to case or a small typo fix. `gram` checks this on every
  use. If the change is bigger than that, it is not a repair; write a Rule for the construction instead.
- **Rule**: parses one kind of clause into facts, or returns None if the clause is not its kind. It must account for
  the whole clause. `PatternRule` does this with one regex that must match the whole clause (`re.fullmatch`).
  A fact is a dict: `{"subject": str, "relation": str, "object": str, "qualifiers": [str, ...]}`; use qualifiers
  for words that change the meaning (a time, a negation, a frequency). A rule for clauses that carry no facts sets
  `ignore = True`, says why in `solves`, and returns `[]`.

Example, for a made-up log format:

```python
from gram import PatternRule

class DiskFull(PatternRule):
    name = "disk_full"
    solves = "lines reporting that a disk is full, with an optional time"
    added_by = "example"
    pattern = r"[Dd]isk (?P<disk>\w+) (?:is|was) full(?: at (?P<time>\d\d:\d\d))?\.?"
    examples = [("Disk sda1 is full at 10:42.",
                 [{"subject": "sda1", "relation": "is_full", "object": "", "qualifiers": ["at 10:42"]}])]

    def build(self, g):
        return [{"subject": g["disk"], "relation": "is_full", "object": "",
                 "qualifiers": ["at " + g["time"]] if g["time"] else []}]
```

## Resolving every clause

A clause is resolved when exactly one rule parses it (several rules giving identical facts also count), when an
ignore-rule takes it, or when `manual.jsonl` covers it. Two rules giving different facts is an `ambiguous` outlier:
fix the rules, do not pick one at random.

`manual.jsonl` is for text that no grammar should cover, one row per clause (or `"clause": null` for a whole line):
```json
{"line": 812, "clause": "<exact clause text>", "facts": [{"subject": "...", "relation": "...", "object": "", "qualifiers": []}], "reason": "free text, no template"}
{"line": 905, "clause": "<exact clause text>", "ignore": true, "reason": "garbled, carries no recoverable fact"}
```

## Commands

```
python -m gram test  --lib lib
python -m gram parse <document> --lib lib --manual manual.jsonl --out out
```
`parse` writes `out/parsed.jsonl` (one row per content line: its status and facts; each fact records which clause it
came from) and `out/outliers.jsonl` (every unresolved clause with its status: `unparsed`, `ambiguous`,
`normalizer_changed_words`, `split_error`, `bad_facts` or `error`), and prints a summary. A content line is any
non-empty line not starting with `#`, before the final query.
