#!/usr/bin/env bash
# Study 06 follow-up, step 1: plan-only probe (PH condition of ../../scripts/plan.sh), any model, either example.
# Usage: plan_models.sh <model> <sample 00000|00001> <rep>   Env: LHB_DATA, LHB_WORK
set -u
model=$1; s=$2; rep=$3
data=${LHB_DATA:-/e/lhb-data}; work=${LHB_WORK:-/e/r}
ctx=$data/contexts/sample-$s.md
tag=$(echo "$model" | sed 's/claude-//; s/-//g')
out_dir="$(cd "$(dirname "$0")/.." && pwd)/runs/plans"
mkdir -p "$out_dir"
w=$work/P$tag$s$rep; rm -rf "$w"; mkdir -p "$w"; cd "$w" || exit 1
ask="Do not answer the query yet. First describe, step by step, the plan you would follow to answer it reliably, including what could make you miss a qualifying person or include a wrong one."
cp "$ctx" context.md
claude -p "The file context.md in the current directory contains a collection of documents followed by a final query at the end. You may look at the file to understand its structure. $ask Describe the plan in terms of the tools you have." \
  --model "$model" --safe-mode --no-session-persistence --tools "Read,Grep,Glob,Bash" --allowedTools "Read,Grep,Glob,Bash" \
  --output-format stream-json --verbose > "$out_dir/PH-$tag-$s-$rep.jsonl" 2> "$out_dir/PH-$tag-$s-$rep.err"
echo "PH-$tag-$s-$rep exit=$?" >> "$out_dir/plans.log"
