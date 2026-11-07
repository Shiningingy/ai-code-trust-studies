"""Print the pip requirements of the Home Assistant integrations whose tests the PR changes
(from $PR_TESTS), following each manifest's dependencies and after_dependencies. One per line.
Runs inside the setup container; reads /work only."""
import json
import os
import re

root = "/work/homeassistant/components"
todo, seen, reqs = [], set(), []
for p in os.environ.get("PR_TESTS", "").split():
    m = re.match(r"tests/components/([^/]+)/", p)
    if m:
        todo.append(m.group(1))
while todo:
    d = todo.pop()
    if d in seen:
        continue
    seen.add(d)
    f = os.path.join(root, d, "manifest.json")
    if not os.path.exists(f):
        continue
    m = json.load(open(f, encoding="utf-8"))
    for r in m.get("requirements", []):
        if r not in reqs:
            reqs.append(r)
    todo += m.get("dependencies", []) + m.get("after_dependencies", [])
print("\n".join(reqs))
