#!/usr/bin/env bash
# Study 06 follow-up, step 3 (../plan.md): instance 00041, plans PH/CV/PH1/CV1, then arms B B1 A A1 N N1 x 3 runs.
# Usage: run_step3.sh <model> <cap_usd>. Stops at the first hard error (exit 3) or when step-3 spend (sample 00041) passes the cap.
set -u
export LHB_DATA=/e/lhb-data-hard LHB_WORK=${LHB_WORK:-/e/r}
here="$(cd "$(dirname "$0")" && pwd)"; f="$(dirname "$here")"
M=$1; CAP=$2; T=$(echo "$M" | sed 's/claude-//; s/-//g'); S=00041
log="$f/runs/step3_batch_$T.log"; mkdir -p "$f/runs"; : >> "$log"
extract() {  # stream-json -> plan text
  python -I -c "
import json,sys,io
r=''
for l in open(sys.argv[1],encoding='utf-8'):
  d=json.loads(l)
  if d.get('type')=='result': r=d.get('result','')
io.open(sys.argv[2],'w',encoding='utf-8').write(r)" "$1" "$2"
}
for r in 1 2 3; do
  [ -s "$f/plans/PH-$T-$S-$r.md" ]  || { bash "$here/plan_models.sh" $M $S $r; extract "$f/runs/plans/PH-$T-$S-$r.jsonl" "$f/plans/PH-$T-$S-$r.md"; }
  [ -s "$f/plans/CV-$T-$S-$r.md" ]  || { bash "$here/plan_revise_1c.sh" $S $r $M; extract "$f/runs/plans/CV-$T-$S-$r.jsonl" "$f/plans/CV-$T-$S-$r.md"; }
  [ -s "$f/plans/PH1-$T-$S-$r.md" ] || { ONEPASS=1 bash "$here/plan_models.sh" $M $S $r; extract "$f/runs/plans/PH1-$T-$S-$r.jsonl" "$f/plans/PH1-$T-$S-$r.md"; }
  [ -s "$f/plans/CV1-$T-$S-$r.md" ] || { ONEPASS=1 bash "$here/plan_revise_1c.sh" $S $r $M; extract "$f/runs/plans/CV1-$T-$S-$r.jsonl" "$f/plans/CV1-$T-$S-$r.md"; }
done
for p in PH CV PH1 CV1; do for r in 1 2 3; do
  [ -s "$f/plans/$p-$T-$S-$r.md" ] || { echo "$(date -Is) Halted: plan $p-$T-$S-$r is empty" >> "$log"; exit 3; }
done; done
echo "$(date -Is) plans done" >> "$log"
spent() { python -I -c "
import json,sys
t=0
try:
  for l in open(sys.argv[1],encoding='utf-8'):
    d=json.loads(l)
    if d['model']==sys.argv[2] and d['sample']==sys.argv[3]: t+=d['total_cost']
except OSError: pass
print(round(t,2))" "$f/runs/step2_summary.jsonl" $M $S; }
for arm in B B1 A A1 N N1; do for r in 1 2 3; do
  if grep -q "\"run\": \"S2$arm$T$S$r\"" "$f/runs/step2_summary.jsonl" 2>/dev/null; then continue; fi
  c=$(spent); if python -I -c "import sys; sys.exit(0 if float('$c')>$CAP else 1)"; then echo "$(date -Is) Halted at budget cap: spent \$$c" >> "$log"; exit 0; fi
  out=$(python -I "$here/run_step2.py" $arm $M $S $r); rc=$?
  echo "$(date -Is) $out rc=$rc" >> "$log"
  [ $rc -eq 3 ] && { echo "$(date -Is) Halted on hard error" >> "$log"; exit 3; }
done; done
echo "$(date -Is) batch done, spent \$$(spent)" >> "$log"
