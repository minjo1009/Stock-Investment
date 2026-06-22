# Retention And Archive Policy

- No blind deletion of DBs, raw sources, reports, snapshots, logs, or broker evidence.
- Generated cache DBs may be cleaned only after scan classification and when no report depends on them.
- Root host DB copies remain `NOT_AUTHORITATIVE` until operator-approved archive.
- Snapshot/backup existence is required before destructive migration.
- Retention enforcement starts as dry-run reporting.
