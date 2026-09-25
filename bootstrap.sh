#!/usr/bin/env bash
# Auto-start the MCP SSE bridge whenever the codespace boots (wake-on-demand).
set +e
cd /workspaces/e2b-mcp-server || exit 0
pkill -f "python3 app.py" >/dev/null 2>&1
nohup bash -c 'while true; do python3 /workspaces/e2b-mcp-server/app.py >> /tmp/ishak-mcp.log 2>&1; sleep 3; done' >/dev/null 2>&1 &
date -u +"%Y-%m-%dT%H:%M:%SZ boot" >> /tmp/ishak-bootstrap.log
