#!/usr/bin/env bash
# Study 06 follow-up, step 1c: own plan back; the model defines near-miss, then says what to do if it is not enough.
# Usage: plan_revise_1c.sh <sample 00000|00001> <rep> [model, default claude-opus-5-5]   Env: LHB_DATA, LHB_WORK; ONEPASS=1: from PH1, adds the one-pass sentence (CV1)
set -u
s=$1; rep=$2; model=${3:-claude-opus-5-5}; tag=$(echo "$model" | sed 's/claude-//; s/-//g')
data=${LHB_DATA:-/e/lhb-data}; work=${LHB_WORK:-/e/r}
here="$(cd "$(dirname "$0")/.." && pwd)"
P=PH; C=CV; one=""; [ "${ONEPASS:-0}" = 1 ] && { P=PH1; C=CV1; one=" You will give one final answer. It is scored once, by exact match, with no feedback and no second try."; }
prev="$here/plans/$P-$tag-$s-$rep.md"; out_dir="$here/runs/plans"; mkdir -p "$out_dir"
w=$work/C${C#CV}$tag$s$rep; rm -rf "$w"; mkdir -p "$w"; cd "$w" || exit 1
cp "$data/contexts/sample-$s.md" context.md
ask="The file context.md in the current directory contains a collection of documents followed by a final query at the end. Earlier you looked at it and wrote this plan:

----- your earlier plan -----
$(cat "$prev")
----- end of plan -----

First, explain what a near-miss would mean for this query and how you would define it precisely (for example, how many conditions a person may fail and still count, and how you would find such people). Then suppose a qualifying person would still not be caught by a near-miss check, because your patterns miss facts for several of that person's conditions. What would you do instead? Do not answer the query yet. Revise your plan accordingly, and say roughly what the revision adds in cost.$one Describe the plan in terms of the tools you have."
claude -p "$ask" --model "$model" --safe-mode --no-session-persistence --tools "Read,Grep,Glob,Bash" --allowedTools "Read,Grep,Glob,Bash" \
  --output-format stream-json --verbose > "$out_dir/$C-$tag-$s-$rep.jsonl" 2> "$out_dir/$C-$tag-$s-$rep.err"
echo "$C-$tag-$s-$rep exit=$?" >> "$out_dir/plans.log"
