import json, sys
import stmts

text = open('context.md', encoding='utf8').read()
statements = stmts.split_statements(text)
records = json.load(open('extracted_statements.json', encoding='utf8'))

placed = irrelevant = unaccounted = 0
if len(records) != len(statements):
    print('record count mismatch', len(records), len(statements))
for i, s in enumerate(statements):
    r = records[i] if i < len(records) else None
    if r is None or r['text'] != s:
        unaccounted += 1
    elif r['status'] == 'placed' and r['detail']:
        placed += 1
    elif r['status'] == 'irrelevant' and r['detail']:
        irrelevant += 1
    else:
        unaccounted += 1
unaccounted += max(0, len(records) - len(statements))
print('total statements:', len(statements))
print('placed:', placed)
print('irrelevant:', irrelevant)
print('unaccounted:', unaccounted)
sys.exit(1 if unaccounted else 0)
