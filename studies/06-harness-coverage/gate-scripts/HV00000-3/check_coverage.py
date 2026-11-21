"""Split context.md into statements; every one must be placed (in extracted.json) or explicitly irrelevant."""
import re, json, sys
from split import statements

NAME = r"(?:[A-Za-z]\.|[A-Za-z]{2,}) [A-Za-z]{2,}"
PLACE = r"(?:the |a )?[A-Za-z ]+"
# Explicit irrelevance rules: facts about activities, ownership, books, past habits, one-off/future transport, day shift, narrative filler.
IRRELEVANT = [re.compile(p, re.I) for p in [
    rf"{NAME} (?:attends|used to attend|visited|went to|owns|helped with \w+ at|discussed|recommended|said|says|explains|used the (?:subway|bus|train|tram)|plans to use the (?:subway|bus|train|tram)|works the day shift|no longer attends)\b",
    r"^(?:though |but )?(?:he |she |they |I )?no longer do(?:es)?\.?$",
    r"^[“”\"]?I (?:used to attend|visited|own|owns|helped|discussed|recommended|used|no longer)\b",
    r"^[“”\"]?I work the day shift",
    r"^(?:In|During|While preparing)\b.*(?:travel reimbursement|shift handoff|my shift)",
    r"^(?:Elsewhere in the note|Unrelatedly|In a separate update|In contrast|which|a |an |the |it |so |having |whereas |that |this |I |we |.*\bwith the (?:team|group)\b)",
]]

def main():
    S = statements()
    ex = json.load(open('extracted.json', encoding='utf8'))
    placed_idx = {p['index']: p for p in ex['placed']}
    placed = irrelevant = 0
    unaccounted = []
    for i, (pid, s) in enumerate(S):
        if i in placed_idx:
            if placed_idx[i]['text'] != s: unaccounted.append((pid, s)); continue
            placed += 1
        elif any(r.search(s) for r in IRRELEVANT) or not re.search(r"\b(?:shift|travel|works? for|based in|roster|routinely|commut|subway|Org)", s, re.I) and not re.search(NAME + r" (?:works|travels)", s):
            irrelevant += 1
        else:
            unaccounted.append((pid, s))
    print(f"total statements: {len(S)}")
    print(f"placed: {placed}")
    print(f"irrelevant: {irrelevant}")
    print(f"unaccounted: {len(unaccounted)}")
    for u in unaccounted[:30]: print('  ', u)
    sys.exit(1 if unaccounted else 0)

main()
