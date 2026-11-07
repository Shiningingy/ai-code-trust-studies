#!/usr/bin/env bash
# Overnight run of the planned follow-ups (report Section 8), cheapest first.
# Usage guards from llm.py apply to every model call (pause at 80% of the five-hour window, stop at 75% of the week).
# At the end Docker Desktop and WSL are shut down to free memory.
# Usage (Git Bash):  bash followups_overnight.sh   -> log in runs/followups_overnight.log
cd "$(dirname "$0")"
PY=/g/PhD-Prototype/.venv/Scripts/python
LOG=../runs/followups_overnight.log
{
  echo "== start $(date)"
  echo "== 8.3 summary coverage";      $PY followup_coverage.py;            $PY followup_coverage.py --report
  echo "== 8.1 pre-review tagging";     $PY followup_prereview.py;           $PY followup_prereview.py --early-cut
  $PY followup_prereview.py --report
  echo "== 8.2 oracle arm";             $PY followup_oracle.py;              $PY followup_oracle.py --report
  echo "== done $(date)"
} >> "$LOG" 2>&1
powershell -NoProfile -Command "Get-Process 'Docker Desktop','com.docker.backend','com.docker.build' -ErrorAction SilentlyContinue | Stop-Process -Force; wsl --shutdown" >> "$LOG" 2>&1
echo "== docker and wsl stopped $(date)" >> "$LOG"
