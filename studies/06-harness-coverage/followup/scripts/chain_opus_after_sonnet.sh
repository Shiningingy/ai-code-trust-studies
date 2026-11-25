#!/usr/bin/env bash
# Wait for the Sonnet batch to finish, then start the Opus batch only if Sonnet did not stop on a hard error.
f="$(cd "$(dirname "$0")/.." && pwd)"
while ps -W 2>/dev/null | grep -q run_batch_sonnet || pgrep -f run_batch_sonnet >/dev/null 2>&1; do sleep 60; done
if grep -q "STOP hard error" "$f/runs/step2_batch_sonnet.log" 2>/dev/null; then echo "$(date -Is) Opus not started: Sonnet stopped on a hard error" >> "$f/runs/step2_batch_opus.log"; exit 0; fi
bash "$(dirname "$0")/run_batch_opus.sh" > "$f/runs/step2_batch_opus.out" 2>&1
