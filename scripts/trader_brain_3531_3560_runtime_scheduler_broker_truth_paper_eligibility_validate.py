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
        "configs/runtime_diagnostic_scheduler.json",
        (
            '"owner_id": "operator-runtime-diagnostic-scheduler"',
            '"kis_environment": "paper"',
            '"cadence": "5_min_safety"',
            '"cadence": "10_min_brain"',
            '"cadence": "30_min_heavy_source"',
            '"enabled": false',
        ),
    )
    _require(
        "scripts/run_runtime_diagnostic_scheduler.ps1",
        (
            "$env:KIS_ENVIRONMENT = \"paper\"",
            "src.app.runtime_scheduler_supervisor",
            "exit $LASTEXITCODE",
            "MaxRuns",
            "ForceDue",
        ),
    )
    _require(
        "scripts/install_runtime_diagnostic_scheduler_task.ps1",
        (
            "Register-ScheduledTask",
            "Install-StartupFallback",
            "StartupFolderFallback",
            "TraderBrainRuntimeDiagnosticScheduler",
            "MultipleInstances IgnoreNew",
            "Diagnostic-only; no broker submit",
        ),
    )
    _require(
        "src/app/runtime_scheduler_supervisor.py",
        (
            "RuntimeSchedulerConfig",
            "run_runtime_scheduler_supervisor_once",
            "utf-8-sig",
            "kis_environment != \"paper\"",
            "dry_run_only=True",
        ),
    )
    _require(
        "src/app/broker_truth_reconciliation.py",
        (
            "run_broker_truth_reconciliation",
            "build_broker_truth_ref",
            "KIS_PAPER_ORDER_STATUS",
            "resolve_paper_order_intent_after_reconciliation",
            "BROKER_TRUTH_RECONCILIATION_REQUIRES_PAPER_ENVIRONMENT",
        ),
    )
    _require(
        "src/execution/paper_eligibility_path.py",
        (
            "create_paper_intent_from_latest_authority",
            "LATEST_RUNTIME_DECISION_NOT_PAPER_ELIGIBLE",
            "record_runtime_authority_evidence",
            "create_authorized_paper_order_intent",
        ),
    )
    _require(
        "src/state/store.py",
        (
            "def list_paper_order_intents",
            "FROM paper_order_intents",
            "WHERE state IN",
        ),
    )
    _require(
        "tests/test_runtime_scheduler_supervisor.py",
        (
            "test_due_cadences_run_dry_run_only",
            "test_config_requires_paper_environment",
        ),
    )
    _require(
        "tests/test_broker_truth_reconciliation.py",
        (
            "test_clean_broker_truth_records_reconciliation_run",
            "test_missing_broker_truth_blocks_new_orders",
            "test_unknown_intent_resolves_from_broker_truth",
        ),
    )
    _require(
        "tests/test_paper_eligibility_path.py",
        (
            "test_full_evidence_paper_eligible_path_creates_local_intent_only",
            "test_incomplete_evidence_blocks_before_intent",
        ),
    )
    _require(
        "docs/reports/task_3531_3560_runtime_scheduler_broker_truth_paper_eligibility/task_3531_3560_runtime_scheduler_broker_truth_paper_eligibility.md",
        (
            "OPERATOR_DRY_RUN_SCHEDULER_BROKER_TRUTH_PAPER_ELIGIBILITY_PATH_IMPLEMENTED_NOT_PROMOTION",
            "StartupFolderFallback READY_AT_NEXT_LOGON",
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
        "data/artifacts/task_3531_3560_runtime_scheduler_broker_truth_paper_eligibility/operator_scheduler_install_result.txt",
        (
            "InstallMode: StartupFolderFallback",
            "State: READY_AT_NEXT_LOGON",
            "StartNow: false",
            "ScheduledTaskRegistration: ACCESS_DENIED",
        ),
    )
    _require(
        "tasks/task_registry.csv",
        (
            "Task3531,Runtime Scheduler Broker Truth Paper Eligibility Selection",
            "Task3560,Runtime Scheduler Broker Truth Paper Eligibility Closeout",
            "task_3531_3560_runtime_scheduler_broker_truth_paper_eligibility",
        ),
    )
    _require(
        "docs/operating_system/project_operating_state.md",
        (
            "Task3531-Task3560",
            "operator-owned dry-run recurring scheduler",
            "broker truth reconciliation source",
            "evidence-backed PAPER_ELIGIBLE",
        ),
    )
    _require(
        "docs/llm_wiki/realtime_trading_operations.md",
        (
            "Task3531-Task3560",
            "runtime_scheduler_supervisor",
            "broker_truth_reconciliation",
            "paper_eligibility_path",
        ),
    )
    _require(
        "docs/obsidian/Vault Home.md",
        (
            "Task3531-3560",
            "operator dry-run scheduler",
            "broker truth reconciliation",
            "PAPER_ELIGIBLE evidence path",
        ),
    )
    _require(
        "docs/architecture/test_validation_canonicalization_map.md",
        (
            "Task3531-Task3560 adds the runtime scheduler broker-truth paper-eligibility validation lane",
            "tests/test_runtime_scheduler_supervisor.py",
            "tests/test_paper_eligibility_path.py",
        ),
    )
    print("TASK3531_3560_OK")


if __name__ == "__main__":
    main()
