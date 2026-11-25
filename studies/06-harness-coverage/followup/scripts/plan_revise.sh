#!/usr/bin/env bash
# Study 06 follow-up, step 1b: give Opus its own step-1 plan back plus the near-miss failure mode (not the fix).
# Usage: plan_revise.sh <sample 00000|00001> <rep>   Env: LHB_DATA, LHB_WORK
set -u
s=$1; rep=$2; model=claude-opus-5-5; tag=opus55
data=${LHB_DATA:-/e/lhb-data}; work=${LHB_WORK:-/e/r}
here="$(cd "$(dirname "$0")/.." && pwd)"
prev="$here/plans/PH-$tag-$s-$rep.md"; out_dir="$here/runs/plans"; mkdir -p "$out_dir"
w=$work/R$tag$s$rep; rm -rf "$w"; mkdir -p "$w"; cd "$w" || exit 1
cp "$data/contexts/sample-$s.md" context.md
ask="The file context.md in the current directory contains a collection of documents followed by a final query at the end. Earlier you looked at it and wrote this plan:

----- your earlier plan -----
$(cat "$prev")
----- end of plan -----

Suppose a qualifying person's facts are worded so that your patterns miss two or more of that person's conditions. A check that re-reads only near-misses (people who fail exactly one condition) would not catch them. Do not answer the query yet. Revise your plan so that it would still find such a person, and say roughly what the revision adds in cost. Describe the plan in terms of the tools you have."
claude -p "$ask" --model "$model" --safe-mode --no-session-persistence --tools "Read,Grep,Glob,Bash" --allowedTools "Read,Grep,Glob,Bash" \
  --output-format stream-json --verbose > "$out_dir/RV-$tag-$s-$rep.jsonl" 2> "$out_dir/RV-$tag-$s-$rep.err"
echo "RV-$tag-$s-$rep exit=$?" >> "$out_dir/plans.log"
