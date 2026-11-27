#!/usr/bin/env bash
# Wait until the Sonnet batch log says it ended (done or STOP), then start the Opus batch unless Sonnet hit a hard error.
f="$(cd "$(dirname "$0")/.." && pwd)"; L="$f/runs/step2_batch_sonnet.log"
until grep -qE "batch done|STOP" "$L" 2>/dev/null; do sleep 60; done
if grep -q "STOP hard error" "$L"; then echo "$(date -Is) Opus not started: Sonnet stopped on a hard error" >> "$f/runs/step2_batch_opus.log"; exit 0; fi
bash "$(dirname "$0")/run_batch_opus.sh" > "$f/runs/step2_batch_opus.out" 2>&1
