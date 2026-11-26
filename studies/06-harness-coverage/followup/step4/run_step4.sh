#!/usr/bin/env bash
# Study 06 follow-up, step 4 batch (see ../plan.md, Step 4). One session at a time.
# On a usage-limit error (exit 3) wait 30 minutes and retry the same session, up to 20 times.
set -u
cd "$(dirname "$0")"
S4="$(pwd)"
SCR="$S4/../scripts"
MODEL=claude-sonnet-5-5
export LHB_WORK=E:/r LHB_DATA=E:/lhb-data-hard
SUM2="$S4/../runs/step2_summary.jsonl"
SUM4="$S4/../runs/step4_summary.jsonl"
TESTS="00002 00014 00029 00003 00021 00039 00045"

retry() {  # run "$@" until it does not exit 3
  local n=0 rc
  while :; do
    "$@"; rc=$?
    [ $rc -ne 3 ] && return $rc
    n=$((n + 1)); [ $n -gt 20 ] && { echo "usage limit persists; stopping"; exit 1; }
    echo "$(date '+%F %T') usage limit; waiting 30 min (retry $n)"; sleep 1800
  done
}

cost4() { python -I -c "
import json,sys
last={}
for f,key in ((sys.argv[1],'label'),(sys.argv[2],'run')):
    try:
        for l in open(f,encoding='utf-8'):
            d=json.loads(l); k=d.get(key,'')
            if f==sys.argv[1] or any(('sonnet55'+x) in k for x in ('00002','00014','00029','00003','00021','00039','00045','90017')) and k[2:4] in ('N1','P1','G1'):
                last[k]=d.get('cost') or d.get('total_cost') or 0
    except OSError: pass
print(round(sum(last.values()),2))" "$SUM4" "$SUM2"; }

done_run() { python -I -c "
import json,sys
ok=False
try:
    for l in open(sys.argv[1],encoding='utf-8'):
        d=json.loads(l)
        if d.get('run')==sys.argv[2]: ok=not d.get('stopped_on_error')
except OSError: pass
sys.exit(0 if ok else 1)" "$SUM2" "$1"; }

learn_cost() { python -I -c "
import json
last={}
for l in open('$SUM4',encoding='utf-8'):
    d=json.loads(l); last[d['label']]=d.get('cost') or 0
print(round(sum(last.values()),2))"; }

echo "$(date '+%F %T') step 4 start"
for L in learn-a learn-b learn-c; do
  if [ -d "libs/$L/parts" ] && [ -n "$(ls libs/$L/parts 2>/dev/null)" ]; then echo "skip $L (exists)"; continue; fi
  retry python -I run_learn.py learn "$L" "$MODEL" || { echo "learning session $L failed"; exit 1; }
  [ -n "$(find "libs/$L/parts" -name '*.py' 2>/dev/null)" ] || { echo "$L produced no parts; stopping for review"; exit 1; }
  c=$(learn_cost); echo "learning cost so far \$$c"
  python -I -c "import sys; sys.exit(0 if $c <= 15 else 1)" || { echo "learning passed \$15; stopping"; exit 1; }
done
if [ ! -d libs/v0/parts ] || [ -z "$(ls libs/v0/parts 2>/dev/null)" ]; then
  retry python -I run_learn.py reconcile v0 "$MODEL" libs/learn-a libs/learn-b libs/learn-c || { echo "reconcile failed"; exit 1; }
fi
[ -n "$(find libs/v0/parts -name '*.py' 2>/dev/null)" ] || { echo "v0 has no parts; stopping"; exit 1; }

for rep in 1 2 3; do
  for s in $TESTS; do
    for arm in N1 P1 G1; do
      run="S2${arm}sonnet55${s}${rep}"
      done_run "$run" && { echo "skip $run"; continue; }
      retry python -I "$SCR/run_step2.py" "$arm" "$MODEL" "$s" "$rep"
      c=$(cost4); echo "step 4 cost so far \$$c"
      python -I -c "import sys; sys.exit(0 if $c <= 60 else 1)" || { echo "step 4 passed \$60; stopping"; exit 1; }
    done
  done
done
for rep in 1 2 3; do
  for arm in G1 N1; do
    run="S2${arm}sonnet5590017${rep}"
    done_run "$run" && { echo "skip $run"; continue; }
    retry python -I "$SCR/run_step2.py" "$arm" "$MODEL" 90017 "$rep"
    c=$(cost4); echo "step 4 cost so far \$$c"
  done
done
echo "$(date '+%F %T') step 4 done"
