# DB Topology

- Active authority: `trading.db` remains the current writable diagnostic DB.
- Future migration to `data/active/trading.db` is a separate dependency-aware task.
- Raw sources stay append-only under `data/raw/`.
- Task artifacts stay under `data/artifacts/<task_id>/`.
- Read-only MCP access must use `data/readonly_mcp/trading_readonly_latest.db`.
- Restore snapshots live under `data/snapshots/`.
- Unknown DBs are registered or quarantined; they are not blindly deleted.

Safety footer: Strategy `NOT_ACCEPTED`; Deployment `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`; Real Capital `FORBIDDEN`.
