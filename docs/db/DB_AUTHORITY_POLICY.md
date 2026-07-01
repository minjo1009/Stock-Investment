# DB Authority Policy

1. Exactly one DB may be `ACTIVE`: current path `trading.db`.
2. Non-authoritative DBs are audit evidence until retention policy permits archive/removal.
3. Every DB-like file must be hash-scanned and classified.
4. Duplicate hashes are reference duplicates, not deletion permission.
5. Read-only MCP and DuckDB analysis must use copied DBs or artifacts, never the active DB.
6. Stale source is a blocker/unknown, never negative evidence.
