#!/usr/bin/env bash
# Study 06, step 1: ask the model for its plan on sample-00000 without answering.
#   PD = Direct: the whole context file in the prompt + the plan request; no tools.
#   PH = Claude Code: context.md in an empty folder; it may look at the file; tools Read, Grep, Glob, Bash.
# Usage: plan.sh <PD|PH>    Env: LHB_DATA, LHB_WORK as in run.sh
set -u
cond=$1; s=00000
data=${LHB_DATA:-/e/lhb-data}; work=${LHB_WORK:-/e/r}
ctx=$data/contexts/sample-$s.md
out_dir="$(cd "$(dirname "$0")/.." && pwd)/runs/plans"
mkdir -p "$out_dir"
w=$work/$cond$s; rm -rf "$w"; mkdir -p "$w"; cd "$w" || exit 1
common=(--model claude-sonnet-5-5 --safe-mode --no-session-persistence)
ask="Do not answer the query yet. First describe, step by step, the plan you would follow to answer it reliably, including what could make you miss a qualifying person or include a wrong one."
if [ "$cond" = PD ]; then
  { cat "$ctx"; printf '\n\n---\n%s\n' "$ask"; } | claude -p "${common[@]}" --tools "" \
    --system-prompt "You are a helpful assistant." --output-format json > "$out_dir/$cond.json" 2> "$out_dir/$cond.err"
else
  cp "$ctx" context.md
  claude -p "The file context.md in the current directory contains a collection of documents followed by a final query at the end. You may look at the file to understand its structure. $ask Describe the plan in terms of the tools you have." \
    "${common[@]}" --tools "Read,Grep,Glob,Bash" --allowedTools "Read,Grep,Glob,Bash" \
    --output-format stream-json --verbose > "$out_dir/$cond.jsonl" 2> "$out_dir/$cond.err"
fi
echo "$cond exit=$?" >> "$out_dir/plans.log"
