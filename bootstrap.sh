#!/usr/bin/env bash
# Auto-start on every codespace boot: daytona MCP bridge (port 10000) + guard REST (port 8000).
set +e
cd /workspaces/e2b-mcp-server || exit 0
pkill -f "python3 app.py" >/dev/null 2>&1
nohup bash -c 'while true; do PORT=10000 python3 /workspaces/e2b-mcp-server/app.py >> /tmp/ishak-mcp.log 2>&1; sleep 3; done' >/dev/null 2>&1 &
bash /workspaces/e2b-mcp-server/ops/guard/start.sh
date -u +"%Y-%m-%dT%H:%M:%SZ boot" >> /tmp/ishak-bootstrap.log
