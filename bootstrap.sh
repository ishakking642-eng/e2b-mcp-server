#!/usr/bin/env bash
# Runs on every codespace boot: sync repo, then start daytona MCP bridge + guard REST.
set +e
REPO=/workspaces/e2b-mcp-server
cd "$REPO" || exit 0
git config --global --add safe.directory "$REPO" >/dev/null 2>&1
git pull --ff-only -q origin main >/dev/null 2>&1
date -u +"%Y-%m-%dT%H:%M:%SZ boot" >> /tmp/ishak-bootstrap.log
# 1) guard REST (port 8000)
bash "$REPO/ops/guard/start.sh"
# 2) daytona MCP SSE bridge (port 10000)
pkill -f "python3 .*app.py" >/dev/null 2>&1
nohup bash -c 'while true; do PORT=10000 python3 /workspaces/e2b-mcp-server/app.py >> /tmp/ishak-mcp.log 2>&1; sleep 3; done' >/dev/null 2>&1 &
echo "$(date -u +%FT%TZ) bootstrap done" >> /tmp/ishak-bootstrap.log
