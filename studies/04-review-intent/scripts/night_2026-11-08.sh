#!/usr/bin/env bash
# Night of 2026-11-08: all planned follow-ups (H.1-H.3) + Opus-agent replication (H.4), until the weekly reset.
# Owner's rule for tonight: use the rest of the week; only the five-hour window is guarded (pause at 80%).
# Streams: tags (coverage + pre-review, no Docker) and 3 Docker streams split by repository (followup_night.py).
# Logs: runs/night2_*.log.  At the end: reports, then Docker Desktop and WSL are stopped.
cd "$(dirname "$0")"
PY=/g/PhD-Prototype/.venv/Scripts/python
R=../runs
export STUDY_WEEK_STOP=0.99 STUDY_PAUSE_AT=0.80
export STUDY_STOP_AT=1794164100   # Sun 2026-11-08 13:55 Toronto, 5 min before the weekly reset
M=$R/night2_main.log
echo "== start $(date)" >> $M
for i in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 10; done
docker info >/dev/null 2>&1 && echo "== docker ready $(date)" >> $M || echo "== docker NOT ready $(date)" >> $M

( $PY followup_coverage.py; $PY followup_coverage.py --report
  $PY followup_prereview.py; $PY followup_prereview.py --early-cut; $PY followup_prereview.py --report
  echo "== tags done $(date)" ) >> $R/night2_tags.log 2>&1 &
for k in 0 1 2; do
  $PY followup_night.py --stream $k --of 3 >> $R/night2_s$k.log 2>&1 &
  sleep 20
done
wait
echo "== all streams ended $(date)" >> $M
$PY followup_oracle.py --report >> $M 2>&1
powershell -NoProfile -Command "Get-Process 'Docker Desktop','com.docker.backend','com.docker.build' -ErrorAction SilentlyContinue | Stop-Process -Force; wsl --shutdown" >> $M 2>&1
echo "== docker and wsl stopped $(date)" >> $M
