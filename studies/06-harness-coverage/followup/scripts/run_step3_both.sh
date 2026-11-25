#!/usr/bin/env bash
# Study 06 follow-up, step 3: Sonnet batch, then Opus only if Sonnet did not halt on a hard error.
here="$(cd "$(dirname "$0")" && pwd)"
bash "$here/run_step3.sh" claude-sonnet-5-5 20 || exit $?
bash "$here/run_step3.sh" claude-opus-5-5 35
