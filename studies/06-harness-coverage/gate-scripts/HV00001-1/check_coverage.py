"""Split context.md into statements and verify each is placed in extracted.json
or classified irrelevant. Exit 1 if any statement is unaccounted."""
import re, json, sys

SPEECH = r"(?:said|explained|added|continued|concluded|noted|mentioned)"

def split_statements(text):
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            out.append(line)
            continue
        # sentence split: after . ! ? followed by space, not after an initial / St.
        parts, start = [], 0
        for m in re.finditer(r'[.!?]["”]?\s+', line):
            before = line[start:m.start() + 1]
            last = before.split()[-1] if before.split() else ""
            if re.fullmatch(r"[\"“(]?(?:[A-Za-z]\.|St\.)", last) and m.group(0)[0] == ".":
                continue
            parts.append(line[start:m.end()].strip())
            start = m.end()
        if line[start:].strip():
            parts.append(line[start:].strip())
        for s in parts:
            s = re.sub(r"(\b" + SPEECH + r"),\s", r"\1§ ", s)
            for c in re.split(r",\s+|;\s+", s):
                c = c.replace("§", ",").strip()
                if c:
                    out.append(c)
    return out

IRRELEVANT_RULES = [
    ("heading", r"^#"),
    ("former commute", r"used to take the"),
    ("travel reimbursement narration", r"reimbursement|travel note|travel to the venue"),
    ("last-year event", r"old-event-p-\d+ during last-year"),
    ("former/past commute", r"no longer does|used to routinely travel|routinely travels? by \w+ but no longer"),
    ("one-off / future travel", r"\bused the (?:bus|train|subway|tram) once|plans? to use the"),
    ("temporary / non-dairy-avoidance diet", r"temporarily skipping|buys \w+ for other people|dislikes eating"),
]
TRIGGER = re.compile(r"works? for|based in|volunteered at|dairy|travel|\bbus\b|train|subway|tram|roster|identifier|familiar names", re.I)

def classify_irrelevant(stmt):
    low = stmt.lower()
    for name, pat in IRRELEVANT_RULES:
        if re.search(pat, low, re.I):
            return name
    if not TRIGGER.search(stmt):
        return "no work/org/event/diet/transport/identity content"
    return None

def main():
    text = open("context.md", encoding="utf8").read()
    stmts = split_statements(text)
    data = json.load(open("extracted.json", encoding="utf8"))
    placed_set = {f["statement"] for f in data["facts"]}
    placed = irrelevant = unacc = 0
    bad = []
    in_query = False
    for s in stmts:
        if s.startswith("#") and "Final Query" in s:
            in_query = True
        if in_query:
            irrelevant += 1  # the query itself, not evidence
            continue
        if s in placed_set:
            placed += 1
        elif classify_irrelevant(s):
            irrelevant += 1
        else:
            unacc += 1
            bad.append(s)
    print("total statements:", len(stmts))
    print("placed:", placed)
    print("irrelevant:", irrelevant)
    print("unaccounted:", unacc)
    for b in bad[:40]:
        print("  UNACCOUNTED:", b)
    sys.exit(1 if unacc else 0)

if __name__ == "__main__":
    main()
