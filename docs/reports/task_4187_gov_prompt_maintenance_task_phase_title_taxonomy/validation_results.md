# TASK-4187 Validation Results

## Command

```powershell
python scripts/ops/validate_prime_task_contracts.py --task TASK-4187
```

## Output

```text
PRIME TASK CONTRACT VALIDATION
PASS TASK-4187 prime contract valid: docs/reports/task_4187_gov_prompt_maintenance_task_phase_title_taxonomy/task_result_contract.yaml
PASS enforced_tasks_checked: 1
RESULT: PASS
exit_code=0
```

## Command

```powershell
python scripts/ops/validate_task_registry.py
```

## Output

```text
TASK REGISTRY VALIDATION
PASS tasks: 87
PASS TASK-4100 exists
PASS profiles_resolved: 87
PASS required_fields
RESULT: PASS
exit_code=0
```

## Command

```powershell
python scripts/ops/validate_doc_registry.py --soft
```

## Output

```text
DOC REGISTRY VALIDATION
PASS documents: 832
PASS required_fields
PASS no_duplicate_paths
RESULT: PASS
exit_code=0
```

## Command

```powershell
python scripts/ops/validate_required_artifacts.py --task TASK-4187
```

## Output

```text
REQUIRED ARTIFACTS VALIDATION
PASS required_artifacts_exist: 8
PASS manifest_rows: 8
RESULT: PASS
exit_code=0
```

## Command

```powershell
python scripts/ops/validate_task_scope.py --task TASK-4187
```

## Output

```text
TASK SCOPE VALIDATION
PASS git_changed_files_seen: 782
PASS scoped_files_checked: 8
PASS forbidden_paths_clean
WARN dirty files outside task manifest ignored for scope gate: 780
RESULT: PASS_WITH_WARNINGS
exit_code=0
```

## Command

```powershell
python scripts/ops/validate_codex_closeout.py --task TASK-4187
```

## Output

```text
CODEX CLOSEOUT VALIDATION
PASS python scripts/ops/validate_task_registry.py: PASS
PASS python scripts/ops/validate_doc_registry.py --soft: PASS
PASS python scripts/ops/validate_prime_task_contracts.py --task TASK-4187: PASS
PASS python scripts/ops/validate_required_artifacts.py --task TASK-4187: PASS
PASS closeout.registry_updated: true
PASS closeout.doc_registry_updated: true
PASS closeout.validators_passed: true
PASS closeout.artifact_manifest_exists: true
PASS closeout.forbidden_paths_clean: true
WARN python scripts/ops/validate_task_scope.py --task TASK-4187: PASS_WITH_WARNINGS
RESULT: PASS_WITH_WARNINGS
exit_code=0
```

