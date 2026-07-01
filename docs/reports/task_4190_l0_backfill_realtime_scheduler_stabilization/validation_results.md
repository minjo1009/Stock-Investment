# TASK-4190 Validation Results

## Command

```powershell
python -m py_compile scripts/build_l0_operating_status_4190.py scripts/validate_l0_operating_contract_4190.py
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text

```

## Command

```powershell
python scripts/build_l0_operating_status_4190.py --contract ops/l0_operating_contract.yaml
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
{
  "status_path": "data/artifacts/l0_operating_status/current_l0_status.json",
  "context_path": "data/artifacts/l0_operating_status/current_l0_context.md",
  "overall_verdict": "BLOCKED",
  "blockers": [
    "L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD",
    "L0_PUBLIC_NEWSWIRE_INCOMPLETE",
    "L0_REALTIME_SCHEDULER_LAST_RESULT_FAILED"
  ],
  "warnings": [
    "L0_BACKGROUND_PID_DEAD:daily_bars_backfill",
    "L0_BACKGROUND_PID_DEAD:five_min_bars_backfill",
    "L0_LEGACY_PATH_PRESENT:configs/db_source_acquisition_scheduler.json",
    "L0_LEGACY_PATH_PRESENT:data/artifacts/l0_public_newswire_backfill/background_process.json",
    "L0_LEGACY_PATH_PRESENT:scripts/start_l0_prioritized_backfills.ps1",
    "L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_backfill.ps1",
    "L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_collector.ps1",
    "L0_STALE_WORKERS_PRESENT"
  ]
}
```

## Command

```powershell
python scripts/validate_l0_operating_contract_4190.py --mode harness --expect-blocked
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
L0 OPERATING CONTRACT HARNESS VALIDATION
PASS contract exists
PASS data/artifacts/l0_operating_status/current_l0_status.json exists
PASS data/artifacts/l0_operating_status/current_l0_context.md exists
PASS data/artifacts/l0_operating_status/l0_operating_manifest.json exists
PASS current L0 context is fresh
PASS dead RUNNING public newswire launcher is detected
PASS public newswire incomplete blocker is explicit
PASS realtime scheduler failure is explicit
PASS realtime config scheduler aligns with contract
PASS expected L0 blockers detected
WARN L0_BACKGROUND_PID_DEAD:daily_bars_backfill
WARN L0_BACKGROUND_PID_DEAD:five_min_bars_backfill
WARN L0_LEGACY_PATH_PRESENT:configs/db_source_acquisition_scheduler.json
WARN L0_LEGACY_PATH_PRESENT:data/artifacts/l0_public_newswire_backfill/background_process.json
WARN L0_LEGACY_PATH_PRESENT:scripts/start_l0_prioritized_backfills.ps1
WARN L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_backfill.ps1
WARN L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_collector.ps1
WARN L0_STALE_WORKERS_PRESENT
RESULT: PASS_WITH_WARNINGS
```

## Command

```powershell
python scripts/validate_l0_operating_contract_4190.py --mode health
```

Expected exit: 1
Actual exit: 1
Result: PASS

```text
L0 OPERATING CONTRACT HEALTH VALIDATION
PASS contract exists
PASS data/artifacts/l0_operating_status/current_l0_status.json exists
PASS data/artifacts/l0_operating_status/current_l0_context.md exists
PASS data/artifacts/l0_operating_status/l0_operating_manifest.json exists
PASS current L0 context is fresh
PASS dead RUNNING public newswire launcher is detected
PASS public newswire incomplete blocker is explicit
PASS realtime scheduler failure is explicit
PASS realtime config scheduler aligns with contract
WARN L0_BACKGROUND_PID_DEAD:daily_bars_backfill
WARN L0_BACKGROUND_PID_DEAD:five_min_bars_backfill
WARN L0_LEGACY_PATH_PRESENT:configs/db_source_acquisition_scheduler.json
WARN L0_LEGACY_PATH_PRESENT:data/artifacts/l0_public_newswire_backfill/background_process.json
WARN L0_LEGACY_PATH_PRESENT:scripts/start_l0_prioritized_backfills.ps1
WARN L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_backfill.ps1
WARN L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_collector.ps1
WARN L0_STALE_WORKERS_PRESENT
FAIL L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD
FAIL L0_PUBLIC_NEWSWIRE_INCOMPLETE
FAIL L0_REALTIME_SCHEDULER_LAST_RESULT_FAILED
RESULT: FAIL
```

## Command

```powershell
python scripts/ops/build_context_bundle.py --task TASK-4190
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
PASS bundle: TASK_4190
PASS context: docs/generated_context/TASK-4190_context.md
PASS manifest: docs/generated_context/TASK-4190_manifest.csv
PASS token_count: 15494 (approximate)
RESULT: PASS
```

## Command

```powershell
python scripts/ops/validate_context_bundle.py --task TASK-4190
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
CONTEXT BUNDLE VALIDATION
PASS token_count_present: 15494
PASS token_budget: 15494/24000
PASS included_files: 10
RESULT: PASS
```

## Command

```powershell
python scripts/ops/validate_prime_task_contracts.py --task TASK-4190
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
PRIME TASK CONTRACT VALIDATION
PASS TASK-4190 prime contract valid: docs/reports/task_4190_l0_backfill_realtime_scheduler_stabilization/task_result_contract.yaml
PASS enforced_tasks_checked: 1
RESULT: PASS
```

## Command

```powershell
python scripts/ops/validate_task_registry.py
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
TASK REGISTRY VALIDATION
PASS tasks: 91
PASS TASK-4100 exists
PASS profiles_resolved: 91
PASS required_fields
RESULT: PASS
```

## Command

```powershell
python scripts/ops/validate_doc_registry.py --soft
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
DOC REGISTRY VALIDATION
PASS documents: 879
PASS required_fields
PASS no_duplicate_paths
RESULT: PASS
```

## Command

```powershell
python scripts/ops/validate_project_hygiene.py
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
PROJECT HYGIENE VALIDATION
PASS optional root entry absent: .pytest_cache
PASS optional root entry absent: config
PASS closeout_gate_includes_project_hygiene
PASS root_entries_seen: 27
PASS root_entries_classified: 27
PASS no_unclassified_root_entries
WARN known_debt root entries: trading-DESKTOP-2R00TB4.db, trading.db
WARN sensitive local root entries classified do-not-read: .env, .kis_token_cache.json, kis_paper.env
RESULT: PASS_WITH_WARNINGS
```

## Command

```powershell
python scripts/ops/validate_project_structure_policy.py
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
PROJECT STRUCTURE POLICY VALIDATION
PASS all root entries covered by structure policy
PASS duplicate axes declared: 4
PASS all docs surfaces classified
PASS closeout validator declared: python scripts/ops/validate_project_hygiene.py
PASS closeout validator declared: python scripts/ops/validate_project_structure_policy.py
PASS codex closeout runs structure policy validator
RESULT: PASS
```

## Command

```powershell
python scripts/ops/validate_required_artifacts.py --task TASK-4190
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
REQUIRED ARTIFACTS VALIDATION
PASS required_artifacts_exist: 20
PASS manifest_rows: 20
RESULT: PASS
```

## Command

```powershell
python scripts/ops/validate_task_scope.py --task TASK-4190
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
TASK SCOPE VALIDATION
PASS git_changed_files_seen: 791
PASS scoped_files_checked: 20
PASS forbidden_paths_clean
WARN dirty files outside task manifest ignored for scope gate: 789
RESULT: PASS_WITH_WARNINGS
```

## Command

```powershell
python scripts/ops/validate_codex_closeout.py --task TASK-4190
```

Expected exit: 0
Actual exit: 0
Result: PASS

```text
CODEX CLOSEOUT VALIDATION
PASS python scripts/ops/validate_task_registry.py: PASS
PASS python scripts/ops/validate_doc_registry.py --soft: PASS
PASS python scripts/ops/validate_context_bundle.py --task TASK-4190: PASS
PASS python scripts/ops/validate_project_structure_policy.py: PASS
PASS python scripts/ops/validate_prime_task_contracts.py --task TASK-4190: PASS
PASS python scripts/ops/validate_required_artifacts.py --task TASK-4190: PASS
PASS python -m py_compile scripts/build_l0_operating_status_4190.py scripts/validate_l0_operating_contract_4190.py: PASS
PASS python scripts/build_l0_operating_status_4190.py --contract ops/l0_operating_contract.yaml: PASS
PASS python scripts/ops/build_context_bundle.py --task TASK-4190: PASS
PASS closeout.registry_updated: true
PASS closeout.doc_registry_updated: true
PASS closeout.validators_passed: true
PASS closeout.artifact_manifest_exists: true
PASS closeout.forbidden_paths_clean: true
WARN python scripts/ops/validate_project_hygiene.py: PASS_WITH_WARNINGS
WARN python scripts/ops/validate_task_scope.py --task TASK-4190: PASS_WITH_WARNINGS
WARN python scripts/validate_l0_operating_contract_4190.py --mode harness --expect-blocked: PASS_WITH_WARNINGS
RESULT: PASS_WITH_WARNINGS
```

## Overall

PASS_WITH_EXPECTED_HEALTH_BLOCKER
