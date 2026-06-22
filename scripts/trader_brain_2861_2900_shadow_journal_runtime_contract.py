from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_trader_terminal_catalog import build_paper_ops_runtime_catalog, write_paper_ops_runtime_catalog


TASK_ID = "task_2861_2900_shadow_journal_runtime_contract"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2861_2900_shadow_journal_runtime_contract.md"
DECISION = REPORT_DIR / "task_2900_decision.csv"
CATALOG_SNAPSHOT_DIR = OUT_DIR / "runtime_catalog_snapshot"
AUTHORITY = "DIAGNOSTIC_SHADOW_JOURNAL_RUNTIME_CONTRACT_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def now_utc() -> str:
    return datetime.now(tz=UTC).isoformat()


def required_journal_schema() -> list[dict[str, object]]:
    fields = [
        ("journal_id", "1", "Stable append-only journal row id."),
        ("run_id", "1", "Daily/shadow run id."),
        ("decision_timestamp", "1", "Decision timestamp, not outcome timestamp."),
        ("policy_id", "1", "Frozen or runtime policy identity."),
        ("decision_id", "1", "Source runtime decision id."),
        ("symbol", "1", "Ticker symbol."),
        ("side", "1", "BUY/SELL/empty for no-trade."),
        ("order_intent_id", "0", "Paper-only intent id if present."),
        ("source_ids", "1", "Source snapshot ids used by the decision."),
        ("thesis_id", "1", "Thesis or reason code."),
        ("risk_state", "1", "Runtime regime/risk state."),
        ("source_time_status", "1", "Captured/missing/stale source-time state."),
        ("decision_state", "1", "Candidate/no-trade/block state."),
        ("journal_action", "1", "PAPER_CANDIDATE, NO_TRADE, OBSERVE_OR_BLOCK."),
        ("no_trade_reason", "0", "Block/reject reason."),
        ("paper_fill_status", "1", "NOT_SENT unless paper execution evidence exists."),
        ("reduce_exit_reason", "0", "Reduce/exit note when present."),
        ("outcome_used_for_assignment", "1", "Must be 0."),
        ("assignment_uses_future_outcome", "1", "Must be 0."),
        ("real_capital", "1", "Must be FORBIDDEN."),
    ]
    return [
        {
            "task_id": "Task2861",
            "schema_id": f"SHADOWSCHEMA2861-{idx:04d}",
            "field_name": name,
            "required": required,
            "description": desc,
            "outcome_allowed_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, required, desc) in enumerate(fields, start=1)
    ]


def schema_gate_rows(payload: dict[str, Any], manifest_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    paper_ops = payload.get("paper_ops", {})
    data_quality = payload.get("data_quality", {})
    journal = payload.get("shadow_decision_journal", [])
    manifest_files = {row.get("file_name", ""): row for row in manifest_rows}
    checks = [
        ("runtime_catalog_has_paper_ops", bool(paper_ops), "paper_ops object must exist."),
        ("runtime_catalog_has_v2", bool(isinstance(paper_ops, dict) and paper_ops.get("v2")), "paper_ops.v2 must exist."),
        ("runtime_catalog_has_data_quality", bool(data_quality), "data_quality object must exist."),
        ("runtime_catalog_has_shadow_journal", isinstance(journal, list), "shadow_decision_journal must be a list."),
        ("manifest_has_runtime_catalog", "paper_ops_runtime_catalog.json" in manifest_files, "Runtime catalog manifest row required."),
        ("manifest_has_trade_detail_view", "paper_trade_detail_view.json" in manifest_files, "Trade detail manifest row required."),
        ("manifest_has_quality_json", "paper_runtime_data_quality.json" in manifest_files, "Data quality manifest row required."),
        ("manifest_has_shadow_journal", "shadow_decision_journal.csv" in manifest_files, "Shadow journal manifest row required."),
        ("deployment_claim_blocked", payload.get("rules", {}).get("deployment_claim_allowed") is False, "Deployment claim must remain false."),
        ("missing_source_approximation_blocked", payload.get("rules", {}).get("missing_source_approximation_allowed") is False, "Missing sources cannot be approximated."),
    ]
    return [
        {
            "task_id": "Task2881",
            "schema_gate_id": f"RUNTIMESCHEMA2881-{idx:04d}",
            "check_name": name,
            "pass": "1" if passed else "0",
            "detail": detail,
            "required_for_paper": "1",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def quality_summary_rows(payload: dict[str, Any]) -> list[dict[str, object]]:
    quality = payload.get("data_quality", {})
    flags = quality.get("data_quality_flags") or []
    rows = [
        {
            "task_id": "Task2882",
            "quality_id": "RUNTIMEQUALITY2882-0001",
            "metric": "trade_detail_row_count",
            "value": quality.get("trade_detail_row_count", 0),
            "status": quality.get("trade_detail_status", ""),
            "flags": "|".join(flags),
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2882",
            "quality_id": "RUNTIMEQUALITY2882-0002",
            "metric": "missing_chart_count",
            "value": quality.get("missing_chart_count", 0),
            "status": quality.get("data_quality_status", ""),
            "flags": "|".join(flags),
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2882",
            "quality_id": "RUNTIMEQUALITY2882-0003",
            "metric": "missing_marker_count",
            "value": quality.get("missing_marker_count", 0),
            "status": quality.get("data_quality_status", ""),
            "flags": "|".join(flags),
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2882",
            "quality_id": "RUNTIMEQUALITY2882-0004",
            "metric": "missing_vwap_count",
            "value": quality.get("missing_vwap_count", 0),
            "status": quality.get("data_quality_status", ""),
            "flags": "|".join(flags),
            "authority": AUTHORITY,
        },
    ]
    return rows


def strict_asof_ledger_summary() -> list[dict[str, object]]:
    source_gate = read_csv(ROOT / "data/artifacts/task_2401_2500_research_to_paper_readiness/task2421_source_time_gate_ledger.csv")
    strict_count = sum(1 for row in source_gate if row.get("strict_raw_asof_complete") == "1")
    return [
        {
            "task_id": "Task2891",
            "asof_audit_id": "STRICTASOF2891-0001",
            "scope": "Task2401 source gate ledger",
            "row_count": len(source_gate),
            "strict_raw_asof_complete_rows": strict_count,
            "strict_raw_asof_incomplete_rows": len(source_gate) - strict_count,
            "deployment_blocker": "STRICT_RAW_ASOF_INCOMPLETE" if strict_count < len(source_gate) else "",
            "missing_source_is_negative": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def closeout_row(
    payload: dict[str, Any],
    schema_rows: list[dict[str, object]],
    quality_rows: list[dict[str, object]],
    asof_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    journal = payload.get("shadow_decision_journal", [])
    schema_pass = all(row.get("pass") == "1" for row in schema_rows)
    quality = payload.get("data_quality", {})
    strict_complete = asof_rows[0].get("strict_raw_asof_incomplete_rows") == 0
    return [
        {
            "task_id": "Task2900",
            "verdict": "shadow_journal_runtime_contract_implemented_diagnostic_only",
            "shadow_journal_rows": len(journal),
            "schema_gate_pass": "1" if schema_pass else "0",
            "runtime_data_quality_status": quality.get("data_quality_status", ""),
            "runtime_data_quality_flags": "|".join(quality.get("data_quality_flags") or []),
            "trade_detail_rows": quality.get("trade_detail_row_count", 0),
            "missing_chart_count": quality.get("missing_chart_count", 0),
            "missing_marker_count": quality.get("missing_marker_count", 0),
            "missing_vwap_count": quality.get("missing_vwap_count", 0),
            "strict_raw_asof_complete_rows": asof_rows[0].get("strict_raw_asof_complete_rows", 0),
            "strict_raw_asof_incomplete_rows": asof_rows[0].get("strict_raw_asof_incomplete_rows", 0),
            "paper_order_intents_created": 0,
            "live_orders_created": 0,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "acceptance_conclusion": "NO_GO",
            "next_action": "Task2901-2920 should use this journal/contract to build 2022 MDD L2-L3 attribution without replay tuning.",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], schema_rows: list[dict[str, object]], quality_rows: list[dict[str, object]]) -> None:
    failed_schema = [row for row in schema_rows if row.get("pass") != "1"]
    quality_lines = "\n".join(
        f"- `{row['metric']}`: {row['value']} ({row['status']})"
        for row in quality_rows
    )
    failed_lines = "\n".join(f"- `{row['check_name']}`: {row['detail']}" for row in failed_schema) or "- None."
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# Task2861-2900 Shadow Journal Runtime Contract

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Shadow journal rows: {closeout['shadow_journal_rows']}.
- Schema gate pass: `{closeout['schema_gate_pass']}`.
- Runtime data quality: `{closeout['runtime_data_quality_status']}`.
- Runtime data quality flags: `{closeout['runtime_data_quality_flags']}`.
- Trade detail rows: {closeout['trade_detail_rows']}.
- Missing chart count: {closeout['missing_chart_count']}.
- Missing marker count: {closeout['missing_marker_count']}.
- Missing VWAP count: {closeout['missing_vwap_count']}.
- Strict raw/as-of complete rows: {closeout['strict_raw_asof_complete_rows']}.
- Paper order intents created: `0`.
- Live orders created: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task implements the governed paper/shadow operating contract rather than tuning a strategy. It adds a shadow decision journal, runtime schema gates, runtime data-quality flags, and atomic catalog publication artifacts.

Runtime quality summary:

{quality_lines}

Failed schema gates:

{failed_lines}

No selector, sizing, exit, replay, paper order, or live order logic was changed.

## No-Background Decision-Maker Report

완료: 매일 판단을 남길 shadow journal 구조를 만들었습니다.

완료: 앱이 읽는 runtime JSON에 schema gate, data quality flag, manifest를 붙였습니다.

중요: 데이터가 빠졌을 때 정상처럼 보이지 않도록 `CHART_BARS_MISSING`, `MARKERS_MISSING`, `VWAP_MISSING` 같은 플래그를 남깁니다.

아직 실전/모의 주문 승격은 아닙니다. strict raw/as-of가 아직 막혀 있습니다.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2861_2900_shadow_journal_runtime_contract/`.
- Validator: `python scripts/trader_brain_2861_2900_shadow_journal_runtime_contract_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
""",
        encoding="utf-8",
    )


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    existing = {row["task_id"] for row in rows}
    title_by_task: dict[int, str] = {}
    for task_no in range(2861, 2881):
        title_by_task[task_no] = "Shadow Decision Journal"
    for task_no in range(2881, 2901):
        title_by_task[task_no] = "Runtime Catalog Schema Gate And Atomic Publish"
    for task_no in range(2861, 2901):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"{title_by_task[task_no]} Step {task_no}",
                "owner_team": "Research Governance / Paper Ops / Backend Runtime / Frontend Reporting",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "shadow-journal-runtime-contract-diagnostic-only",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2861_2900_shadow_journal_runtime_contract/task_2861_2900_shadow_journal_runtime_contract.md",
                "key_decision": "docs/reports/task_2861_2900_shadow_journal_runtime_contract/task_2900_decision.csv",
                "key_artifacts": "data/artifacts/task_2861_2900_shadow_journal_runtime_contract",
                "validation_command": "python scripts/trader_brain_2861_2900_shadow_journal_runtime_contract_validate.py",
                "notes": "Implements shadow decision journal runtime schema/data-quality gates and atomic catalog publication; no replay/order/live-capital change.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "142. Task2861-Task2900"
    if marker in text:
        return
    line = (
        "142. Task2861-Task2900 implemented the shadow journal/runtime contract: "
        f"shadow journal rows {closeout['shadow_journal_rows']}, schema gate pass {closeout['schema_gate_pass']}, "
        f"runtime quality `{closeout['runtime_data_quality_status']}`, flags `{closeout['runtime_data_quality_flags']}`, "
        f"strict raw/as-of complete rows {closeout['strict_raw_asof_complete_rows']}, paper order intents 0, live orders 0. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_paper_ops_runtime_catalog(ROOT)
    write_paper_ops_runtime_catalog(payload, [CATALOG_SNAPSHOT_DIR])

    manifest_rows = read_csv(CATALOG_SNAPSHOT_DIR / "paper_runtime_catalog_manifest.csv")
    schema = required_journal_schema()
    schema_gate = schema_gate_rows(payload, manifest_rows)
    quality_summary = quality_summary_rows(payload)
    asof_summary = strict_asof_ledger_summary()
    closeout = closeout_row(payload, schema_gate, quality_summary, asof_summary)

    write_csv(OUT_DIR / "task2861_shadow_decision_journal_schema.csv", schema)
    write_csv(OUT_DIR / "task2862_shadow_decision_journal_rows.csv", payload.get("shadow_decision_journal", []))
    write_csv(OUT_DIR / "task2881_runtime_schema_gate.csv", schema_gate)
    write_csv(OUT_DIR / "task2882_runtime_data_quality_summary.csv", quality_summary)
    write_csv(OUT_DIR / "task2883_runtime_catalog_publish_manifest.csv", manifest_rows)
    write_csv(OUT_DIR / "task2891_strict_asof_ledger_summary.csv", asof_summary)
    write_csv(OUT_DIR / "task2900_closeout.csv", closeout)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2900_closeout.json", closeout[0])

    write_report(closeout[0], schema_gate, quality_summary)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2861_2900_SHADOW_JOURNAL_RUNTIME_CONTRACT_COMPLETE]")
    print(json.dumps(closeout[0], ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
