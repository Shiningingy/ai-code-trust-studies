#!/usr/bin/env bash
# Study 06 follow-up, step 2, Sonnet batch: Sonnet step-1 and 1c plans, then arms A, B, C (2 examples x 3 runs).
# Stops at the first hard error (exit 3) or when the step-2 notional cost of this batch passes $25 (plan: budget guard).
set -u
export LHB_DATA=${LHB_DATA:-/e/lhb-data} LHB_WORK=${LHB_WORK:-/e/r}
here="$(cd "$(dirname "$0")" && pwd)"; f="$(dirname "$here")"
M=claude-sonnet-5-5; T=sonnet55; CAP=25
log="$f/runs/step2_batch_sonnet.log"; mkdir -p "$f/runs"; : >> "$log"
extract() {  # stream-json -> plan text
  python -I -c "
import json,sys,io
r=''
for l in open(sys.argv[1],encoding='utf-8'):
  d=json.loads(l)
  if d.get('type')=='result': r=d.get('result','')
io.open(sys.argv[2],'w',encoding='utf-8').write(r)" "$1" "$2"
}
for s in 00000 00001; do for r in 1 2 3; do
  [ -s "$f/plans/PH-$T-$s-$r.md" ] || { bash "$here/plan_models.sh" $M $s $r; extract "$f/runs/plans/PH-$T-$s-$r.jsonl" "$f/plans/PH-$T-$s-$r.md"; }
  [ -s "$f/plans/CV-$T-$s-$r.md" ] || { bash "$here/plan_revise_1c.sh" $s $r $M; extract "$f/runs/plans/CV-$T-$s-$r.jsonl" "$f/plans/CV-$T-$s-$r.md"; }
done; done
echo "$(date -Is) plans done" >> "$log"
spent() { python -I -c "
import json,sys
t=0
try:
  for l in open(sys.argv[1],encoding='utf-8'):
    d=json.loads(l)
    if d['model']==sys.argv[2]: t+=d['total_cost']
except OSError: pass
print(round(t,2))" "$f/runs/step2_summary.jsonl" $M; }
for arm in A B C; do for s in 00000 00001; do for r in 1 2 3; do
  if grep -q "\"run\": \"S2$arm$T$s$r\"" "$f/runs/step2_summary.jsonl" 2>/dev/null; then continue; fi
  c=$(spent); if python -I -c "import sys; sys.exit(0 if float('$c')>$CAP else 1)"; then echo "$(date -Is) STOP budget cap: spent \$$c" >> "$log"; exit 0; fi
  out=$(python -I "$here/run_step2.py" $arm $M $s $r); rc=$?
  echo "$(date -Is) $out rc=$rc" >> "$log"
  [ $rc -eq 3 ] && { echo "$(date -Is) STOP hard error" >> "$log"; exit 3; }
done; done; done
echo "$(date -Is) batch done, spent \$$(spent)" >> "$log"
