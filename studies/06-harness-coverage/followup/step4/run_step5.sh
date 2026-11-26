#!/usr/bin/env bash
# Study 06 follow-up, step 5 batch (see ../plan.md, Step 5): the whole Constraint task.
# Learning on 4 training documents (00000 00001 00041 00020): Sonnet 5.5 learners + reconcile -> libs/v5,
# Opus 5.5 learners + reconcile -> libs/v5-opus. Then the 46 other instances, one run each, arms N1 P1 G1 GO1
# (all Sonnet 5.5), order: untouched, scanned, earlier test instances; then the variant 90017, G1 and GO1 x 3.
# One session at a time. On a usage-limit error (exit 3) wait 30 minutes and retry the same session, up to 20 times.
set -u
cd "$(dirname "$0")"
S4="$(pwd -W)"
SCR="$S4/../scripts"
SONNET=claude-sonnet-5-5
OPUS=claude-opus-5-5
export LHB_WORK=E:/r LHB_DATA=E:/lhb-final LHB_STEP=5 LHB_RUN_PREFIX=S5 LHB_LIBSET=5
SUM2="$S4/../runs/step2_summary.jsonl"
SUM4="$S4/../runs/step4_summary.jsonl"
FRESH="00004 00006 00007 00009 00012 00013 00015 00016 00018 00022 00024 00025 00027 00030 00033 00034 00035 00036 00037 00040 00042 00044 00047 00048"
SCANNED="00005 00008 00010 00011 00019 00023 00026 00028 00031 00032 00038 00043 00046 00049"
OLD="00002 00014 00029 00003 00021 00039 00045 00017"

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
    if d['label'].startswith(('learn5-','v5')): last[d['label']]=d.get('cost') or 0
print(round(sum(last.values()),2))"; }

test_cost() { python -I -c "
import json
last={}
for l in open('$SUM2',encoding='utf-8'):
    d=json.loads(l)
    if d['run'].startswith('S5'): last[d['run']]=d.get('total_cost') or 0
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

has_parts() { [ -n "$(find "libs/$1/parts" -name '*.py' 2>/dev/null)" ]; }

learn_set() {  # $1 = model, $2 = label suffix ("" or "-opus"), $3 = library name
  for L in learn5-a$2 learn5-b$2 learn5-c$2; do
    has_parts "$L" && { echo "skip $L (exists)"; continue; }
    retry python -I run_learn.py learn "$L" "$1" || { echo "learning session $L failed"; exit 1; }
    has_parts "$L" || { echo "$L produced no parts; stopping for review"; exit 1; }
    c=$(learn_cost); echo "step 5 learning cost so far \$$c"
    python -I -c "import sys; sys.exit(0 if $c <= 100 else 1)" || { echo "learning passed \$100; stopping"; exit 1; }
  done
  if ! has_parts "$3"; then
    retry python -I run_learn.py reconcile "$3" "$1" libs/learn5-a$2 libs/learn5-b$2 libs/learn5-c$2 || { echo "reconcile $3 failed"; exit 1; }
  fi
  has_parts "$3" || { echo "$3 has no parts; stopping"; exit 1; }
}

run_one() {  # $1 = arm, $2 = sample, $3 = rep
  local run="S5${1}sonnet55${2}${3}"
  done_run "$run" && { echo "skip $run"; return; }
  retry python -I "$SCR/run_step2.py" "$1" "$SONNET" "$2" "$3"
  c=$(test_cost); echo "step 5 test cost so far \$$c ($run)"
  python -I -c "import sys; sys.exit(0 if $c <= 150 else 1)" || { echo "step 5 tests passed \$150; stopping"; exit 1; }
}

echo "$(date '+%F %T') step 5 start"
learn_set "$SONNET" "" v5
learn_set "$OPUS" "-opus" v5-opus
echo "$(date '+%F %T') step 5 learning done, cost \$$(learn_cost)"
for s in $FRESH $SCANNED $OLD; do
  for arm in N1 P1 G1 GO1; do run_one "$arm" "$s" 1; done
done
for rep in 1 2 3; do
  for arm in G1 GO1; do run_one "$arm" 90017 "$rep"; done
done
echo "$(date '+%F %T') step 5 done"
