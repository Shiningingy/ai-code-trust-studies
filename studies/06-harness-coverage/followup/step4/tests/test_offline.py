"""Offline checks of the step-4 harness (no model calls): hook learn/reconcile/test modes and the library diff.
Uses the toy library in tests/toylib (deliberately incomplete). Usage: python -I tests/test_offline.py <scratch dir>"""
import json
import os
import shutil
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
s4 = os.path.dirname(here)
sys.path.insert(0, s4)
from merge import diff_libraries  # noqa: E402
from hook import lib_hashes  # noqa: E402

scratch = sys.argv[1]
shutil.rmtree(scratch, ignore_errors=True)
ws, state = os.path.join(scratch, "ws"), os.path.join(scratch, "state")
os.makedirs(os.path.join(ws, "train"))
os.makedirs(state)
docs = {"doc1": "E:/lhb-data/contexts/sample-00000.md", "doc2": "E:/lhb-data/contexts/sample-00001.md"}
for d, p in docs.items():
    shutil.copy(p, os.path.join(ws, "train", d + ".md"))
shutil.copytree(os.path.join(here, "toylib"), os.path.join(ws, "lib"))
keys = {d: sorted(json.load(open(p.replace("contexts", "answers").replace(".md", ".json")))["matches"]) for d, p in docs.items()}
json.dump(keys, open(os.path.join(state, "keys.json"), "w"))
json.dump({"doc1": keys["doc1"], "doc2": ["P-001"]}, open(os.path.join(ws, "answers.json"), "w"))


def hook(mode):
    p = subprocess.run([sys.executable, "-I", os.path.join(s4, "hook.py"), state, mode],
                       input=json.dumps({"cwd": ws, "transcript_path": ""}), capture_output=True, text=True)
    return p.stdout.strip(), p.stderr.strip()


out, err = hook("learn")
print("LEARN:", out[:400], err[-300:])
json.dump(["G01", "G02"], open(os.path.join(state, "groups.json"), "w"))
open(os.path.join(ws, "lib", "RECONCILE.md"), "w").write("G01 kept lib_a\n")
out, err = hook("reconcile")
print("RECONCILE:", out[:500], err[-300:])

# test mode: context.md + v0 hashes; edit one v0 part, add one new part
shutil.copy(docs["doc1"], os.path.join(ws, "context.md"))
os.remove(os.path.join(state, "rounds.txt"))
json.dump(lib_hashes(os.path.join(ws, "lib")), open(os.path.join(state, "v0_hashes.json"), "w"))
with open(os.path.join(ws, "lib", "parts", "toy.py"), "a") as f:
    f.write("\n# edited\n")
open(os.path.join(ws, "lib", "parts", "new_part.py"), "w").write("")
out, err = hook("test")
print("TEST 1st stop:", out[:700].replace("\\n", "\n"), err[-300:])
out, err = hook("test")
print("TEST 2nd stop (must be empty = allowed):", repr(out))
log = [json.loads(l) for l in open(os.path.join(state, "hook_log.jsonl"))]
print("TEST record:", {k: log[-1].get(k) for k in ("edited_v0_parts", "new_parts", "unresolved", "tests_failing", "blocked")})

# diff: toylib against a copy with one rule changed
lb = os.path.join(scratch, "lib_b")
shutil.copytree(os.path.join(here, "toylib"), lb)
t = open(os.path.join(lb, "parts", "toy.py")).read().replace('"object": g["o"]', '"object": g["o"] + " extra"')
open(os.path.join(lb, "parts", "toy.py"), "w").write(t)
ids, md = diff_libraries({"a": os.path.join(here, "toylib"), "b": lb, "c": os.path.join(here, "toylib")},
                         {"doc1": docs["doc1"]})
print("DIFF:", len(ids), "groups")
print(md[:900])

# step 5: the hook takes the workspace as a third argument, so a session that stopped inside lib/ is still checked
os.remove(os.path.join(state, "rounds.txt"))
sub = os.path.join(ws, "lib")
p = subprocess.run([sys.executable, "-I", os.path.join(s4, "hook.py"), state, "test", ws],
                   input=json.dumps({"cwd": sub, "transcript_path": ""}), capture_output=True, text=True)
rec = [json.loads(l) for l in open(os.path.join(state, "hook_log.jsonl"))][-1]
assert "library_error" not in rec, rec.get("library_error")
print("WORKSPACE ARG (cwd = lib/): library loads, unresolved =", rec.get("unresolved"))
os.remove(os.path.join(state, "rounds.txt"))
p = subprocess.run([sys.executable, "-I", os.path.join(s4, "hook.py"), state, "test"],
                   input=json.dumps({"cwd": sub, "transcript_path": ""}), capture_output=True, text=True)
rec = [json.loads(l) for l in open(os.path.join(state, "hook_log.jsonl"))][-1]
print("NO WORKSPACE ARG (cwd = lib/, the step-4 bug): library_error =", rec.get("library_error"))

# step 5: prompts for four documents; for three they are the frozen step-4 texts
import prompts  # noqa: E402
assert prompts.learn_text(3) == prompts.LEARN and prompts.reconcile_text(3) == prompts.RECONCILE
assert "three" not in prompts.learn_text(4) and "doc4.md" in prompts.learn_text(4)
print("PROMPTS: n=3 identical to step 4; n=4 has doc4 and no 'three'")
