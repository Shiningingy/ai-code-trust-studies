"""Primary language for each repo in repos.txt via the GitHub GraphQL API (gh CLI). Writes langs.csv.
Usage: python -I langs.py <out_dir>
"""
import sys, os, json, subprocess

out = sys.argv[1]
repos = open(os.path.join(out, "repos.txt")).read().split()
rows = []
for i in range(0, len(repos), 40):
    chunk = repos[i:i + 40]
    parts = []
    for j, r in enumerate(chunk):
        o, n = r.split("/", 1)
        parts.append(f'r{j}: repository(owner: {json.dumps(o)}, name: {json.dumps(n)}) {{ nameWithOwner primaryLanguage {{ name }} }}')
    q = "query {" + " ".join(parts) + "}"
    res = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}"], capture_output=True, text=True, encoding="utf-8")
    data = json.loads(res.stdout or "{}").get("data") or {}
    for j, r in enumerate(chunk):
        node = data.get(f"r{j}")
        lang = ((node or {}).get("primaryLanguage") or {}).get("name") if node else "MISSING"
        rows.append((r, lang))
with open(os.path.join(out, "langs.csv"), "w", encoding="utf-8") as f:
    f.write("repo,language\n" + "\n".join(f"{r},{l}" for r, l in rows))
print("done", len(rows))
