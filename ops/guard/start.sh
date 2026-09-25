#!/usr/bin/env bash
set +e
REPO=${GUARD_REPO:-/workspaces/e2b-mcp-server}
cd "$REPO" 2>/dev/null || exit 0
mkdir -p ops/guard_data
{
  echo "host=$(hostname) date=$(date -u +%FT%TZ)"
  echo "user=$(id -un) home=$HOME"
  (ss -ltnp 2>/dev/null || netstat -ltnp 2>/dev/null) | head -25
  echo '--- procs ---'
  ps -eo pid,args 2>/dev/null | grep -E 'python|uvicorn|app.py' | grep -v grep | head -10
} > ops/guard_data/env.txt 2>&1
pgrep -f 'ops/guard/server.py' >/dev/null && exit 0
nohup bash "$REPO/ops/guard/run.sh" >> /tmp/guard.log 2>&1 &
echo "$(date -u +%FT%TZ) guard started" >> /tmp/guard.log
