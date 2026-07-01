# Restore Runbook

Current restore drill status: `PASS`.

Commands:

```powershell
python -m tools.db.export_readonly_snapshot --readonly --snapshot --manifest data/artifacts/task_3601_3640_db_management_program/readonly_snapshot_manifest.json
python -m tools.db.restore_drill --json data/artifacts/task_3601_3640_db_management_program/restore_drill_result.json
python -m tools.db.healthcheck --diagnostic-only --strict
```

Restore success never changes strategy acceptance, deployment readiness, paper eligibility, or real-capital status.
