# TASK-4172 Validation Results

## Commands

| Command | Result |
|---|---|
| `python -m py_compile src/validation/prime_outcome_contract_validator.py` | PASS |
| `python -m pytest tests/test_prime_outcome_contract_validator.py -q` | PASS, 10 passed |
| `python -m src.validation.prime_outcome_contract_validator docs/reports/task_4172_prime_outcome_harness_bootstrap/task_result_contract.yaml` | PASS |
| `python scripts/ops/validate_task_registry.py` | PASS |
| `python scripts/ops/validate_doc_registry.py --soft` | PASS |
| `python scripts/ops/validate_required_artifacts.py --task TASK-4172` | PASS |
| `python scripts/ops/validate_task_scope.py --task TASK-4172` | PASS_WITH_WARNINGS |
| `python scripts/ops/validate_codex_closeout.py --task TASK-4172` | PASS_WITH_WARNINGS |

## Notes

`validate_task_scope.py` warned that 1112 dirty files outside the TASK-4172 artifact manifest were ignored by the scope gate. The 20 scoped TASK-4172 artifacts passed forbidden-path checks.
