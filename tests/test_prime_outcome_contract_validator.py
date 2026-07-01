from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ops.create_task import starter_contract
from src.validation.prime_outcome_contract_validator import load_contract, validate_contract


FIXTURES = Path(__file__).parent / "fixtures" / "prime_contracts"


def validation_for(name: str) -> dict:
    return validate_contract(load_contract(FIXTURES / name))


def assert_passes(name: str) -> None:
    validation = validation_for(name)
    assert validation["status"] == "PASS", validation


def assert_fails(name: str, expected_fragment: str) -> None:
    validation = validation_for(name)
    assert validation["status"] == "FAIL", validation
    failures = "\n".join(validation["failures"])
    assert expected_fragment in failures, validation


def test_valid_outcome_change_passes() -> None:
    assert_passes("valid_outcome_change.yaml")


def test_valid_diagnostic_only_passes() -> None:
    assert_passes("valid_diagnostic_only.yaml")


def test_valid_harness_bootstrap_passes() -> None:
    assert_passes("valid_harness_bootstrap.yaml")


def test_invalid_report_only_closeout_fails() -> None:
    assert_fails("invalid_report_only_closeout.yaml", "baseline.value is required")


def test_invalid_missing_baseline_outcome_change_fails() -> None:
    assert_fails("invalid_missing_baseline_outcome_change.yaml", "baseline.value is required")


def test_invalid_diagnostic_claims_progress_fails() -> None:
    assert_fails("invalid_diagnostic_claims_progress.yaml", "DIAGNOSTIC_ONLY cannot set actual_underlying_progress true")


def test_invalid_harness_claims_l0_l4_progress_fails() -> None:
    assert_fails("invalid_harness_claims_l0_l4_progress.yaml", "HARNESS_BOOTSTRAP report appears to claim")


def test_invalid_safety_authority_claim_fails() -> None:
    assert_fails("invalid_safety_authority_claim.yaml", "hard_state.deployment must be")


def test_invalid_scope_violation_fails() -> None:
    assert_fails("invalid_scope_violation.yaml", "changed path violates forbidden scope")


def test_invalid_missing_data_as_negative_evidence_fails() -> None:
    assert_fails(
        "invalid_missing_data_as_negative_evidence.yaml",
        "missing/stale/incomplete data used as negative evidence",
    )


def test_valid_l0_layer_outcome_passes() -> None:
    assert_passes("valid_l0_layer_outcome.yaml")


def test_invalid_l3_layer_outcome_fails() -> None:
    assert_fails("invalid_l3_layer_outcome.yaml", "L3 outcome_unit.name is not allowed")


def test_create_task_starter_contract_passes() -> None:
    contract = yaml.safe_load(starter_contract("TASK-9999", "Starter Contract", "docs/reports/task_9999_starter"))
    validation = validate_contract(contract)
    assert validation["status"] == "PASS", validation
