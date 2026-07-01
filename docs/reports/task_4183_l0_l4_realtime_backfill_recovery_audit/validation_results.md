# TASK-4183 Validation Results

Generated at: 2026-07-01T14:14:46Z

```powershell
python -m py_compile scripts/run_task4183_l0_l4_realtime_backfill_recovery_audit.py scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py
```
```text
EXIT_CODE=0
```

```powershell
python scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py
```
```text
TASK-4183 L0-L4 RECOVERY AUDIT VALIDATION
PASS exists: scripts\run_task4183_l0_l4_realtime_backfill_recovery_audit.py
PASS exists: scripts\validate_task4183_l0_l4_realtime_backfill_recovery_audit.py
PASS exists: data\artifacts\task_4183_l0_l4_realtime_backfill_recovery_audit\task_4183_recovery_audit_summary.json
PASS exists: data\artifacts\task_4183_l0_l4_realtime_backfill_recovery_audit\task_4183_level_verdicts.csv
PASS exists: data\artifacts\task_4183_l0_l4_realtime_backfill_recovery_audit\task_4183_scheduled_tasks.json
PASS exists: data\artifacts\task_4183_l0_l4_realtime_backfill_recovery_audit\task_4183_process_snapshot.json
PASS exists: data\artifacts\task_4183_l0_l4_realtime_backfill_recovery_audit\task_4183_db_latest_rows.json
PASS exists: data\artifacts\task_4183_l0_l4_realtime_backfill_recovery_audit\task_4183_artifact_snapshot.json
PASS exists: docs\reports\task_4183_l0_l4_realtime_backfill_recovery_audit\task_result_contract.yaml
PASS exists: docs\reports\task_4183_l0_l4_realtime_backfill_recovery_audit\report.md
PASS exists: docs\reports\task_4183_l0_l4_realtime_backfill_recovery_audit\artifact_manifest.csv
PASS overall_verdict: BLOCKED_NOT_ALL_RUNNING
PASS safety flags closed
RESULT: PASS
EXIT_CODE=0
```

```powershell
python scripts/ops/validate_prime_task_contracts.py --task TASK-4183
```
```text
PRIME TASK CONTRACT VALIDATION
PASS TASK-4183 prime contract valid: docs/reports/task_4183_l0_l4_realtime_backfill_recovery_audit/task_result_contract.yaml
PASS enforced_tasks_checked: 1
RESULT: PASS
EXIT_CODE=0
```

```powershell
python scripts/ops/validate_task_registry.py
```
```text
TASK REGISTRY VALIDATION
PASS tasks: 83
PASS TASK-4100 exists
PASS profiles_resolved: 83
PASS required_fields
RESULT: PASS
EXIT_CODE=0
```

```powershell
python scripts/ops/validate_doc_registry.py --soft
```
```text
DOC REGISTRY VALIDATION
PASS documents: 810
PASS required_fields
PASS no_duplicate_paths
RESULT: PASS
EXIT_CODE=0
```

```powershell
python scripts/ops/validate_required_artifacts.py --task TASK-4183
```
```text
REQUIRED ARTIFACTS VALIDATION
PASS required_artifacts_exist: 14
PASS manifest_rows: 14
RESULT: PASS
EXIT_CODE=0
```

```powershell
python scripts/ops/validate_task_scope.py --task TASK-4183
```
```text
TASK SCOPE VALIDATION
PASS git_changed_files_seen: 755
PASS scoped_files_checked: 14
PASS forbidden_paths_clean
WARN dirty files outside task manifest ignored for scope gate: 753
RESULT: PASS_WITH_WARNINGS
EXIT_CODE=0
```

```powershell
python scripts/ops/validate_codex_closeout.py --task TASK-4183
```
```text
CODEX CLOSEOUT VALIDATION
PASS python scripts/ops/validate_task_registry.py: PASS
PASS python scripts/ops/validate_doc_registry.py --soft: PASS
PASS python scripts/ops/validate_prime_task_contracts.py --task TASK-4183: PASS
PASS python scripts/ops/validate_required_artifacts.py --task TASK-4183: PASS
PASS python -m py_compile scripts/run_task4183_l0_l4_realtime_backfill_recovery_audit.py scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py: PASS
PASS python scripts/validate_task4183_l0_l4_realtime_backfill_recovery_audit.py: PASS
PASS closeout.registry_updated: true
PASS closeout.doc_registry_updated: true
PASS closeout.validators_passed: true
PASS closeout.artifact_manifest_exists: true
PASS closeout.forbidden_paths_clean: true
WARN python scripts/ops/validate_task_scope.py --task TASK-4183: PASS_WITH_WARNINGS
RESULT: PASS_WITH_WARNINGS
EXIT_CODE=0
```

Overall exit code: 0
