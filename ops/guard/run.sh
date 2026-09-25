#!/usr/bin/env bash
# Long-lived cycle: pull -> run server -> self-restart (keeps public port alive).
export OCT=${OCT:-1}
REPO=${GUARD_REPO:-/workspaces/e2b-mcp-server}
cd "$REPO" || exit 1
MAX_LIFE=${MAX_LIFE:-1200}
while true; do
  git pull --ff-only -q origin main >/dev/null 2>&1 || true
  python3 ops/guard/server.py >> /tmp/guard.log 2>&1 &
  SPID=$!
  sleep "$MAX_LIFE"
  kill "$SPID" 2>/dev/null
  sleep 2
done
