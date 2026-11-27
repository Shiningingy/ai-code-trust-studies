#!/usr/bin/env bash
# Study 06 follow-up, step 4b batch (see ../plan.md, Step 4b): the step-4 learning pipeline run by Opus 5.5
# (3 learners + reconcile, same prompts, framework and hook), then arm GO1 (Sonnet 5.5 test sessions on the
# Opus-learned library v0-opus) on the same 7 test instances x 3 and the variant 90017 x 3. One session at a time.
# On a usage-limit error (exit 3) wait 30 minutes and retry the same session, up to 20 times.
set -u
cd "$(dirname "$0")"
S4="$(pwd -W)"
SCR="$S4/../scripts"
LEARN_MODEL=claude-opus-5-5
TEST_MODEL=claude-sonnet-5-5
export LHB_WORK=E:/r LHB_DATA=E:/lhb-data-hard
SUM2="$S4/../runs/step2_summary.jsonl"
SUM4="$S4/../runs/step4_summary.jsonl"
TESTS="00002 00014 00029 00003 00021 00039 00045"

retry() {
  local n=0 rc
  while :; do
    "$@"; rc=$?
    [ $rc -ne 3 ] && return $rc
    n=$((n + 1)); [ $n -gt 20 ] && { echo "usage limit persists; stopping"; exit 1; }
    echo "$(date '+%F %T') usage limit; waiting 30 min (retry $n)"; sleep 1800
  done
}

learn_cost() { python -I -c "
import json
last={}
for l in open('$SUM4',encoding='utf-8'):
    d=json.loads(l)
    if d['label'].endswith('-opus'): last[d['label']]=d.get('cost') or 0
print(round(sum(last.values()),2))"; }

test_cost() { python -I -c "
import json
last={}
for l in open('$SUM2',encoding='utf-8'):
    d=json.loads(l)
    if d['run'].startswith('S2GO1'): last[d['run']]=d.get('total_cost') or 0
print(round(sum(last.values()),2))"; }

done_run() { python -I -c "
import json,sys
ok=False
try:
    for l in open(sys.argv[1],encoding='utf-8'):
        d=json.loads(l)
        if d.get('run')==sys.argv[2]: ok=not d.get('stopped_on_error')
except OSError: pass
sys.exit(0 if ok else 1)" "$SUM2" "$1"; }

echo "$(date '+%F %T') step 4b start"
for L in learn-a-opus learn-b-opus learn-c-opus; do
  if [ -n "$(find "libs/$L/parts" -name '*.py' 2>/dev/null)" ]; then echo "skip $L (exists)"; continue; fi
  retry python -I run_learn.py learn "$L" "$LEARN_MODEL" || { echo "learning session $L failed"; exit 1; }
  [ -n "$(find "libs/$L/parts" -name '*.py' 2>/dev/null)" ] || { echo "$L produced no parts; stopping for review"; exit 1; }
  c=$(learn_cost); echo "opus learning cost so far \$$c"
  python -I -c "import sys; sys.exit(0 if $c <= 80 else 1)" || { echo "learning passed \$80; stopping"; exit 1; }
done
if [ -z "$(find libs/v0-opus/parts -name '*.py' 2>/dev/null)" ]; then
  retry python -I run_learn.py reconcile v0-opus "$LEARN_MODEL" libs/learn-a-opus libs/learn-b-opus libs/learn-c-opus || { echo "reconcile failed"; exit 1; }
fi
[ -n "$(find libs/v0-opus/parts -name '*.py' 2>/dev/null)" ] || { echo "v0-opus has no parts; stopping"; exit 1; }

for rep in 1 2 3; do
  for s in $TESTS 90017; do
    run="S2GO1sonnet55${s}${rep}"
    done_run "$run" && { echo "skip $run"; continue; }
    retry python -I "$SCR/run_step2.py" GO1 "$TEST_MODEL" "$s" "$rep"
    c=$(test_cost); echo "step 4b test cost so far \$$c"
    python -I -c "import sys; sys.exit(0 if $c <= 40 else 1)" || { echo "step 4b tests passed \$40; stopping"; exit 1; }
  done
done
echo "$(date '+%F %T') step 4b done"
