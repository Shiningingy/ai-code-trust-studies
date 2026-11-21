import json, re, sys

def split_statements(path="context.md"):
    """Split context.md into statements: headings, sentences, and comma/semicolon clauses."""
    out = []
    text = open(path, encoding="utf8").read()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            out.append(line)
            continue
        for s in re.split(r"(?<=[\w'][\w'])(?<!\bSt)\.[\"\u201d]?\s+|(?<=[\w'][\w'])(?<!\bSt)\.[\"\u201d]?$", line):
            for f in re.split(r",\s+|;\s+", s):
                f = f.strip().rstrip(".").strip()
                if f:
                    out.append(f)
    return out

def main():
    stmts = split_statements()
    data = json.load(open("extracted.json", encoding="utf8"))
    recs = data["statements"]
    placed = irrelevant = unaccounted = 0
    bad = []
    if len(recs) != len(stmts):
        print(f"record count {len(recs)} != statement count {len(stmts)}")
    for i, s in enumerate(stmts):
        r = recs[i] if i < len(recs) else None
        if r and r["text"] == s and r["class"] == "placed" and r.get("fact"):
            placed += 1
        elif r and r["text"] == s and r["class"] == "irrelevant" and r.get("reason"):
            irrelevant += 1
        else:
            unaccounted += 1
            bad.append(s)
    print("total statements:", len(stmts))
    print("placed:", placed)
    print("irrelevant:", irrelevant)
    print("unaccounted:", unaccounted)
    for b in bad[:30]:
        print("  UNACCOUNTED:", b)
    sys.exit(1 if unaccounted or len(recs) != len(stmts) else 0)

if __name__ == "__main__":
    main()
