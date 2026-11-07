"""Print the pip requirements for the sentry-python integrations whose tests the PR changes.

For each tests/integrations/<name>/ in $PR_TESTS, reads /work/tox.ini deps and keeps lines whose
env key is <name>, <name>-<variant>, or their "-latest" forms (the newest pinned versions). Falls
back to the highest "-v<version>" lines when there is no "-latest". One requirement per line.
"""
import os
import re

names = []
for p in os.environ.get("PR_TESTS", "").split():
    m = re.match(r"tests/integrations/([^/]+)/", p)
    if m and m.group(1) not in names:
        names.append(m.group(1))

lines = open("/work/tox.ini", encoding="utf-8").read().splitlines() if os.path.exists("/work/tox.ini") else []
entries = []
for l in lines:
    m = re.match(r"^\s+([{}\w.,\-]+):\s*(\S.*)$", l)
    if m:
        key = re.sub(r"^(\{[^}]*\}-|py3\.\d+-)+", "", m.group(1))
        entries.append((key, m.group(2).strip()))


def version_key(v):
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.]", v))


out = []
for n in names:
    keys = {k for k, _ in entries if k == n or k.startswith(n + "-")}
    latest = {k for k in keys if k.endswith("-latest")}
    plain = {k for k in keys if not re.search(r"-v[\d.]+$", k) and not k.endswith("-latest")}
    chosen = set(plain) | latest
    if not latest:
        vers = [(version_key(re.search(r"-v([\d.]+)$", k).group(1)), k) for k in keys if re.search(r"-v[\d.]+$", k)]
        if vers:
            chosen.add(max(vers)[1])
    for k, req in entries:
        if k in chosen and req not in out:
            out.append(req)
    if not chosen:
        out.append(n.replace("_", "-"))
print("\n".join(out))
