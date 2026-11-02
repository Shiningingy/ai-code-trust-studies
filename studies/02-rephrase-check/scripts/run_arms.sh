#!/bin/bash
# Scores the arms named on the command line, one at a time, each with the plan's one retry.
# A second pass re-runs only bugs with no report, so it does nothing if the first had no errors.
cd "$(dirname "$0")"
for arm in "$@"; do
  for pass in first retry; do
    workers=8; [ "$pass" = retry ] && workers=4
    bash harness.sh --predictions_path "/preds/$arm.jsonl" --max_workers "$workers" --run_id "study02-$arm" \
      > "E:/swt-scoring/$arm-$pass.log" 2>&1
    echo "$arm $pass exit $? $(date +%H:%M)"
  done
done
echo "all arms finished"
