"""Print the Home Assistant integrations whose tests the PR changes (from $PR_TESTS), one per line.
Runs inside the setup container; reads paths only."""
import os
import re

seen = []
for p in os.environ.get("PR_TESTS", "").split():
    m = re.match(r"tests/components/([^/]+)/", p)
    if m and m.group(1) not in seen:
        seen.append(m.group(1))
print("\n".join(seen))
