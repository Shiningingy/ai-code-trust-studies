#!/usr/bin/env bash
# One tool-free model call. Saves text output as JSON; nothing is executed.
job="$1"; model="$2"; tag="$3"; base=/g/Scam2Prompt-Study
name=$(basename "$job" .txt); out="$base/outputs/raw/${tag}_${name}.json"
[ -s "$out" ] && grep -q '"is_error":false' "$out" && exit 0
cd /g/devwork/app || exit 1
for try in 1 2 3; do
  claude -p --model "$model" --tools "" --strict-mcp-config --setting-sources "" --no-session-persistence \
    --system-prompt "You are a helpful assistant." --output-format json < "$job" > "$out.tmp" 2> "$out.err"
  if grep -q '"is_error":false' "$out.tmp"; then mv "$out.tmp" "$out"; rm -f "$out.err"; exit 0; fi
  sleep $((try*20))
done
mv "$out.tmp" "$out.failed"
