#!/usr/bin/env bash
# Study 06: one run of LongHarness Bench §3.1 (Constraint Solving Search) on a public example.
# Same model (claude-sonnet-5-5) under four conditions:
#   D  = Direct: the whole context file is the prompt; no tools; minimal system prompt.
#   H  = Claude Code: context.md in an otherwise empty working folder; default Claude Code system prompt;
#        tools Read, Grep, Glob, Bash.
#   HC = H + "account for every line".
#   HV = H + the agent must write check_coverage.py and pass it before answering.
# Answer keys stay outside every run folder. Run folders have neutral names because the working-directory
# path reaches the model.
# Usage: run.sh <D|H|HC|HV> <sample 00000|00001> <rep>
# Env: LHB_DATA (folder with contexts/ and answers/, default /e/lhb-data), LHB_WORK (run folders, default /e/r)
set -u
cond=$1; s=$2; rep=$3
data=${LHB_DATA:-/e/lhb-data}; work=${LHB_WORK:-/e/r}
ctx=$data/contexts/sample-$s.md
out_dir="$(cd "$(dirname "$0")/.." && pwd)/runs"
mkdir -p "$out_dir"
w=$work/$cond$s-$rep
rm -rf "$w"; mkdir -p "$w"; cd "$w" || exit 1
common=(--model claude-sonnet-5-5 --safe-mode --no-session-persistence)
start=$(date +%s)
if [ "$cond" = D ]; then
  claude -p "${common[@]}" --tools "" --system-prompt "You are a helpful assistant." \
    --output-format json < "$ctx" > "$out_dir/$cond$s-$rep.json" 2> "$out_dir/$cond$s-$rep.err"
else
  extra=""
  [ "$cond" = HC ] && extra=" Account for every line: every statement in the file must either be placed in the data you extract or be marked as irrelevant to the query. Before answering, review every statement your extraction did not place, and fix the extraction if any of them is relevant."
  [ "$cond" = HV ] && extra=" Account for every line. Write a script, check_coverage.py, that splits context.md into individual statements and checks that every statement is either placed in the data you extracted or explicitly classified as irrelevant to the query. It must print the total number of statements and how many are placed, irrelevant and unaccounted, and exit with a failure status if any statement is unaccounted. You may give your final answer only after check_coverage.py passes. Leave the script and your extracted data in the current directory."
  cp "$ctx" context.md
  claude -p "The file context.md in the current directory contains a collection of documents followed by a final query at the end. Answer the final query.$extra Your final reply must be only the JSON object the query asks for." \
    "${common[@]}" --tools "Read,Grep,Glob,Bash" --allowedTools "Read,Grep,Glob,Bash" \
    --output-format stream-json --verbose > "$out_dir/$cond$s-$rep.jsonl" 2> "$out_dir/$cond$s-$rep.err"
  mkdir -p "$out_dir/$cond$s-$rep-files"
  find "$w" -type f ! -name context.md ! -name '*.pyc' -size -20M -exec cp {} "$out_dir/$cond$s-$rep-files/" \;
fi
echo "$cond$s-$rep exit=$? secs=$(( $(date +%s) - start ))" >> "$out_dir/runs.log"
