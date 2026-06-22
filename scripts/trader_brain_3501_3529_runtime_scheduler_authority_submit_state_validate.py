from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    full = ROOT / path
    if not full.exists():
        raise AssertionError(f"missing required file: {path}")
    return full.read_text(encoding="utf-8")


def _require(path: str, needles: tuple[str, ...]) -> None:
    text = _read(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path} missing: {missing}")


def main() -> None:
    _require(
        "src/app/diagnostic_scheduler.py",
        (
            "run_diagnostic_scheduler_once",
            "BLOCKED_NON_PAPER_ENV",
            "LEASE_HELD_SKIPPED",
            "validate_scheduler_lease_token",
            "record_diagnostic_runtime_heartbeat",
            "market_data_asof_ts=market_data_asof_ts or heartbeat_bucket_ts",
        ),
    )
    _require(
        "src/brain/runtime_authority.py",
        (
            "RuntimeAuthorityCandidate",
            "LatestRuntimeAuthorityDecision",
            "authorize_latest_runtime_decision",
            "SINGLE_LATEST_L6_AUTHORITY",
            "single runtime authority requires one latest RuntimeDecision",
        ),
    )
    _require(
        "src/execution/broker_submit_state.py",
        (
            "PaperOrderIntentSpec",
            "create_authorized_paper_order_intent",
            "mark_paper_order_intent_unknown_after_submit",
            "reconcile_paper_order_intent",
        ),
    )
    _require(
        "tests/test_diagnostic_scheduler.py",
        (
            "test_safety_tick_acquires_records_and_releases_lease",
            "test_duplicate_state_skips_without_new_lease",
            "test_non_paper_environment_blocks_dry_run_tick",
            "test_active_lease_held_by_other_owner_skips_tick",
        ),
    )
    _require(
        "tests/test_runtime_authority_contract.py",
        (
            "test_single_latest_authority_selects_latest_runtime_decision",
            "test_single_latest_authority_rejects_tied_latest_decisions",
        ),
    )
    _require(
        "tests/test_broker_submit_state.py",
        (
            "test_authorized_intent_lifecycle_reconciles",
            "test_unknown_after_submit_blocks_until_reconciliation",
            "test_blocked_authority_cannot_create_intent_spec",
        ),
    )
    _require(
        "docs/reports/task_3501_3529_runtime_scheduler_authority_submit_state/task_3501_3529_runtime_scheduler_authority_submit_state.md",
        (
            "DRY_RUN_SCHEDULER_AUTHORITY_SUBMIT_STATE_IMPLEMENTED_NOT_PROMOTION",
            "Decision Summary",
            "Quant Expert Report",
            "No-Background Decision-Maker Report",
            "Artifact Manifest",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ),
    )
    _require(
        "docs/reports/task_3501_3529_runtime_scheduler_authority_submit_state/task_3529_decision.csv",
        (
            "Task3529",
            "DRY_RUN_SCHEDULER_AUTHORITY_SUBMIT_STATE_IMPLEMENTED_NOT_PROMOTION",
            "NOT_ACCEPTED",
            "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "FORBIDDEN",
        ),
    )
    _require(
        "data/artifacts/task_3501_3529_runtime_scheduler_authority_submit_state/artifact_manifest.md",
        (
            "Task3501-3529 Runtime Scheduler Authority Submit State",
            "src/app/diagnostic_scheduler.py",
            "src/execution/broker_submit_state.py",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ),
    )
    _require(
        "tasks/task_registry.csv",
        (
            "Task3501,Runtime Scheduler Authority Submit State Selection",
            "Task3529,Runtime Scheduler Authority Submit State Closeout",
            "task_3501_3529_runtime_scheduler_authority_submit_state",
        ),
    )
    _require(
        "docs/operating_system/project_operating_state.md",
        (
            "Task3501-Task3529",
            "dry-run diagnostic scheduler",
            "single latest-L6 authority",
            "local broker submit/reconciliation state machine",
        ),
    )
    _require(
        "docs/llm_wiki/realtime_trading_operations.md",
        (
            "Task3501-Task3529",
            "run_diagnostic_scheduler_once",
            "authorize_latest_runtime_decision",
            "broker_submit_state.py",
        ),
    )
    _require(
        "docs/obsidian/Vault Home.md",
        (
            "Task3501-3529",
            "dry-run scheduler",
            "single latest-L6 authority",
            "broker submit/reconciliation state machine",
        ),
    )
    _require(
        "docs/architecture/test_validation_canonicalization_map.md",
        (
            "Task3501-Task3529 adds the runtime scheduler authority submit-state validation lane",
            "tests/test_diagnostic_scheduler.py",
            "tests/test_broker_submit_state.py",
        ),
    )
    print("TASK3501_3529_OK")


if __name__ == "__main__":
    main()
