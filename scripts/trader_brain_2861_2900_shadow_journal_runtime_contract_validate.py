from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2861_2900_shadow_journal_runtime_contract"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
CATALOG_DIR = OUT_DIR / "runtime_catalog_snapshot"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> object:
    if not path.exists():
        raise AssertionError(f"missing json: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report = REPORT_DIR / "task_2861_2900_shadow_journal_runtime_contract.md"
    decision = REPORT_DIR / "task_2900_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    schema = read_csv(OUT_DIR / "task2861_shadow_decision_journal_schema.csv")
    journal = read_csv(OUT_DIR / "task2862_shadow_decision_journal_rows.csv")
    schema_gate = read_csv(OUT_DIR / "task2881_runtime_schema_gate.csv")
    quality = read_csv(OUT_DIR / "task2882_runtime_data_quality_summary.csv")
    publish_manifest = read_csv(OUT_DIR / "task2883_runtime_catalog_publish_manifest.csv")
    asof = read_csv(OUT_DIR / "task2891_strict_asof_ledger_summary.csv")
    closeout = read_csv(OUT_DIR / "task2900_closeout.csv")
    artifact_manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    runtime_catalog = read_json(CATALOG_DIR / "paper_ops_runtime_catalog.json")
    trade_detail = read_json(CATALOG_DIR / "paper_trade_detail_view.json")
    data_quality = read_json(CATALOG_DIR / "paper_runtime_data_quality.json")
    shadow_json = read_json(CATALOG_DIR / "shadow_decision_journal.json")

    required_fields = {
        "journal_id",
        "run_id",
        "decision_timestamp",
        "policy_id",
        "decision_id",
        "symbol",
        "source_ids",
        "thesis_id",
        "risk_state",
        "source_time_status",
        "decision_state",
        "journal_action",
        "paper_fill_status",
        "outcome_used_for_assignment",
        "assignment_uses_future_outcome",
        "real_capital",
    }
    schema_fields = {row["field_name"] for row in schema}
    require(required_fields.issubset(schema_fields), "journal schema missing required fields")
    require(journal, "shadow journal rows empty")
    for idx, row in enumerate(journal, start=1):
        require(row.get("outcome_used_for_assignment") == "0", f"journal row {idx} uses outcome for assignment")
        require(row.get("assignment_uses_future_outcome") == "0", f"journal row {idx} uses future outcome")
        require(row.get("real_capital") == "FORBIDDEN", f"journal row {idx} permits real capital")

    require(all(row.get("pass") == "1" for row in schema_gate), "schema gate failed")
    manifest_files = {row.get("file_name") for row in publish_manifest}
    for file_name in [
        "paper_ops_runtime_catalog.json",
        "paper_trade_detail_view.json",
        "paper_runtime_data_quality.json",
        "paper_runtime_data_quality.csv",
        "shadow_decision_journal.json",
        "shadow_decision_journal.csv",
        "paper_runtime_catalog_manifest.json",
    ]:
        require((CATALOG_DIR / file_name).exists(), f"missing catalog file {file_name}")
    for file_name in [
        "paper_ops_runtime_catalog.json",
        "paper_trade_detail_view.json",
        "paper_runtime_data_quality.json",
        "shadow_decision_journal.csv",
    ]:
        require(file_name in manifest_files, f"manifest missing {file_name}")

    require(isinstance(runtime_catalog, dict) and runtime_catalog.get("contract_version") == "paper-ops-runtime-v1", "bad runtime contract")
    require(runtime_catalog.get("rules", {}).get("deployment_claim_allowed") is False, "runtime catalog permits deployment claim")
    require(runtime_catalog.get("rules", {}).get("missing_source_approximation_allowed") is False, "runtime catalog permits source approximation")
    require(isinstance(trade_detail, dict) and trade_detail.get("contract_version") == "paper_trade_detail_view_v1", "bad trade detail contract")
    require(isinstance(data_quality, dict) and data_quality.get("schema_version") == "paper_runtime_quality_v1", "bad quality contract")
    require(isinstance(shadow_json, dict) and shadow_json.get("contract_version") == "shadow_decision_journal_v1", "bad shadow journal contract")

    require(len(quality) >= 4, "quality summary incomplete")
    require(len(asof) == 1, "strict as-of summary should be one row")
    require(asof[0].get("missing_source_is_negative") == "0", "as-of ledger treats missing source as negative")
    require(closeout and closeout[0].get("acceptance_conclusion") == "NO_GO", "closeout must remain NO_GO")
    require(closeout[0].get("live_orders_created") == "0", "live order created")
    require(closeout[0].get("paper_order_intents_created") == "0", "paper order intent created")
    require(closeout[0].get("strategy_acceptance") == "NOT_ACCEPTED", "strategy status changed")
    require(closeout[0].get("deployment_readiness") == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    require(closeout[0].get("real_capital") == "FORBIDDEN", "real capital status changed")
    require(len(artifact_manifest) >= 8, "artifact manifest too small")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2861, 2901)), "registry missing Task2861-2900 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("142. Task2861-Task2900" in op_state, "operating state missing Task2861-2900 line")

    print("[TASK2861_2900_SHADOW_JOURNAL_RUNTIME_CONTRACT_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
