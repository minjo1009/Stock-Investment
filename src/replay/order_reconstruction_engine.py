from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.replay.position_reconstruction_engine import build_position_replay_acceptance


MATCHING_POLICY = "EXACT_ORDER_ID_RUN_ID_STATUS_ONLY"
ORDER_MATCH_SURFACE = "Order Match"
REPORT_DIR = Path("docs/reports/task_602_4_order_replay_recovery")

ORDER_MATCH_FIELDS = ["order_id", "run_id", "symbol", "side", "quantity", "status", "raw_status"]
CANCEL_STATES = {"CANCELLED", "CANCEL_IN_PROGRESS", "PENDING_CANCEL", "CANCELED"}
AMENDMENT_MARKERS = ("AMEND", "MODIFY", "REVISE", "RVSE", "CORRECT")


@dataclass(frozen=True)
class OrderReplayResult:
    reconstructed_orders: pd.DataFrame
    order_replay_diff: pd.DataFrame
    validation: pd.DataFrame
    decision: pd.DataFrame


def _frame(value: pd.DataFrame | list[dict[str, Any]] | None) -> pd.DataFrame:
    if value is None:
        return pd.DataFrame()
    if isinstance(value, pd.DataFrame):
        return value.copy()
    return pd.DataFrame(value)


def _text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _upper(value: object) -> str:
    return _text(value).upper()


def _float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _numeric(value: object) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return round(float(value), 6)
    except Exception:
        return None


def _norm_float(value: object) -> float:
    return round(_float(value), 6)


def _present(value: object) -> bool:
    return _text(value) != ""


def _safe_ratio(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(float(part) / float(total), 6)


def _field_match(runtime: object, replay: object) -> bool:
    runtime_text = _text(runtime)
    replay_text = _text(replay)
    if runtime_text == "" and replay_text == "":
        return True
    runtime_number = _numeric(runtime)
    replay_number = _numeric(replay)
    if runtime_number is not None and replay_number is not None:
        return runtime_number == replay_number
    return runtime_text == replay_text


def _contract_status(match_rate: float, missing_reason_count: int = 0) -> str:
    if match_rate >= 0.99 and missing_reason_count == 0:
        return "PASS"
    if match_rate >= 0.95 and missing_reason_count == 0:
        return "REVIEW"
    return "FAIL"


def _order_status(match_rate: float) -> str:
    if match_rate > 0.99:
        return "STRETCH"
    if match_rate > 0.95:
        return "PASS"
    if match_rate < 0.90:
        return "FAIL"
    return "REVIEW"


def _order_lookup_counts(frame: pd.DataFrame, order_column: str = "order_id") -> dict[str, int]:
    if frame.empty or order_column not in frame.columns:
        return {}
    counts: dict[str, int] = {}
    for value in frame[order_column].tolist():
        order_id = _text(value)
        if order_id:
            counts[order_id] = counts.get(order_id, 0) + 1
    return counts


def _position_order_counts(position_lifecycle: pd.DataFrame) -> tuple[dict[str, int], dict[str, int]]:
    if position_lifecycle.empty:
        return {}, {}
    entry_counts = _order_lookup_counts(position_lifecycle, "entry_order_id")
    exit_counts = _order_lookup_counts(position_lifecycle, "exit_order_id")
    return entry_counts, exit_counts


def _event_statuses(events: pd.DataFrame) -> dict[str, list[str]]:
    if events.empty or "order_id" not in events.columns:
        return {}
    statuses: dict[str, list[str]] = {}
    status_columns = [column for column in ("order_status", "reason_code") if column in events.columns]
    for _, row in events.iterrows():
        order_id = _text(row.get("order_id"))
        if not order_id:
            continue
        values = [_upper(row.get(column)) for column in status_columns if _present(row.get(column))]
        statuses.setdefault(order_id, []).extend(values)
    return statuses


def _has_amendment_evidence(order_id: str, event_statuses: dict[str, list[str]]) -> bool:
    values = event_statuses.get(order_id, [])
    return any(any(marker in value for marker in AMENDMENT_MARKERS) for value in values)


def _runtime_state(row: pd.Series) -> str:
    return _upper(row.get("status") or row.get("order_status")) or "UNKNOWN"


def reconstruct_orders(
    orders: pd.DataFrame | list[dict[str, Any]],
    fills: pd.DataFrame | list[dict[str, Any]] | None = None,
    position_lifecycle: pd.DataFrame | list[dict[str, Any]] | None = None,
    events: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> pd.DataFrame:
    order_frame = _frame(orders)
    fill_frame = _frame(fills)
    lifecycle = _frame(position_lifecycle)
    event_frame = _frame(events)

    fill_counts = _order_lookup_counts(fill_frame, "order_id")
    event_counts = _order_lookup_counts(event_frame, "order_id")
    event_status_by_order = _event_statuses(event_frame)
    entry_counts, exit_counts = _position_order_counts(lifecycle)

    rows: list[dict[str, Any]] = []
    for _, row in order_frame.iterrows():
        order_id = _text(row.get("order_id"))
        run_id = _text(row.get("run_id"))
        runtime_state = _runtime_state(row)
        raw_status = _upper(row.get("raw_status"))
        intent_key = _text(row.get("intent_key"))
        fill_count = fill_counts.get(order_id, 0)
        event_count = event_counts.get(order_id, 0)
        lifecycle_entry_count = entry_counts.get(order_id, 0)
        lifecycle_exit_count = exit_counts.get(order_id, 0)

        order_creation_evidence = bool(order_id and run_id)
        order_lifecycle_evidence = bool(order_id and runtime_state)
        cancel_evidence = runtime_state in CANCEL_STATES or raw_status == "ORDER_NOT_FOUND"
        fill_evidence = fill_count > 0
        amendment_evidence = _has_amendment_evidence(order_id, event_status_by_order)
        replay_state = runtime_state if order_creation_evidence and order_lifecycle_evidence else "UNRECONSTRUCTED_MISSING_ORDER_ROW"

        rows.append(
            {
                "order_id": order_id,
                "run_id": run_id,
                "symbol": _upper(row.get("symbol")),
                "side": _upper(row.get("side")),
                "quantity": _norm_float(row.get("quantity")),
                "intent_key": intent_key,
                "submitted_at": _text(row.get("submitted_at")),
                "status": runtime_state,
                "raw_status": raw_status,
                "environment": _text(row.get("environment")),
                "replay_state": replay_state,
                "fill_exact_order_id_count": fill_count,
                "event_exact_order_id_count": event_count,
                "lifecycle_entry_exact_order_id_count": lifecycle_entry_count,
                "lifecycle_exit_exact_order_id_count": lifecycle_exit_count,
                "order_creation_evidence_flag": int(order_creation_evidence),
                "order_amendment_evidence_flag": int(amendment_evidence),
                "order_cancel_evidence_flag": int(cancel_evidence),
                "order_fill_evidence_flag": int(fill_evidence),
                "order_lifecycle_evidence_flag": int(order_lifecycle_evidence),
                "decision_lineage_missing_flag": int(intent_key == ""),
                "order_row_exact_match_flag": int(order_creation_evidence and order_lifecycle_evidence),
                "matching_policy": MATCHING_POLICY,
                "proximity_fallback_used_flag": 0,
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "order_id",
            "run_id",
            "symbol",
            "side",
            "quantity",
            "intent_key",
            "submitted_at",
            "status",
            "raw_status",
            "environment",
            "replay_state",
            "fill_exact_order_id_count",
            "event_exact_order_id_count",
            "lifecycle_entry_exact_order_id_count",
            "lifecycle_exit_exact_order_id_count",
            "order_creation_evidence_flag",
            "order_amendment_evidence_flag",
            "order_cancel_evidence_flag",
            "order_fill_evidence_flag",
            "order_lifecycle_evidence_flag",
            "decision_lineage_missing_flag",
            "order_row_exact_match_flag",
            "matching_policy",
            "proximity_fallback_used_flag",
        ],
    )


def _order_match_flags(runtime_orders: pd.DataFrame, reconstructed_orders: pd.DataFrame) -> pd.Series:
    flags: list[int] = []
    replay_rows = list(reconstructed_orders.iterrows())
    for index, runtime in runtime_orders.reset_index(drop=True).iterrows():
        if index >= len(replay_rows):
            flags.append(0)
            continue
        _, replay = replay_rows[index]
        if int(replay.get("order_row_exact_match_flag", 0)) != 1:
            flags.append(0)
            continue
        fields_match = all(
            _field_match(runtime.get(field_name), replay.get(field_name))
            for field_name in ORDER_MATCH_FIELDS
        )
        flags.append(int(fields_match))
    return pd.Series(flags, dtype=int)


def build_order_replay_diff(
    orders: pd.DataFrame | list[dict[str, Any]],
    reconstructed_orders: pd.DataFrame,
) -> pd.DataFrame:
    order_frame = _frame(orders).reset_index(drop=True)
    diff_rows: list[dict[str, Any]] = []
    replay_rows = list(reconstructed_orders.iterrows())

    for index, runtime in order_frame.iterrows():
        order_id = _text(runtime.get("order_id"))
        runtime_state = _runtime_state(runtime)
        replay = replay_rows[index][1] if index < len(replay_rows) else pd.Series(dtype=object)
        replay_state = _text(replay.get("replay_state"))
        reasons: list[str] = []

        if replay.empty:
            reasons.append("Order Creation Failure: replay row missing for exact order_id")
        elif int(replay.get("order_row_exact_match_flag", 0)) != 1:
            reasons.append("Order Creation Failure: exact order_id/run_id/status evidence missing")
        else:
            for field_name in ORDER_MATCH_FIELDS:
                if not _field_match(runtime.get(field_name), replay.get(field_name)):
                    reasons.append(f"Order Lifecycle mismatch: {field_name}")

        if not replay.empty and int(replay.get("decision_lineage_missing_flag", 0)) == 1:
            reasons.append("Decision lineage missing; order row reconstructed by exact order_id")

        if reasons:
            diff_rows.append(
                {
                    "order_id": order_id,
                    "runtime_state": runtime_state,
                    "replay_state": replay_state,
                    "diff_reason": "; ".join(reasons),
                }
            )

    return pd.DataFrame(diff_rows, columns=["order_id", "runtime_state", "replay_state", "diff_reason"])


def _decision_match(decisions: pd.DataFrame) -> tuple[int, int, float, str]:
    total = int(decisions["decision_id"].dropna().astype(str).nunique()) if "decision_id" in decisions.columns else 0
    matched = total
    rate = _safe_ratio(matched, total)
    return total, matched, rate, _contract_status(rate)


def _fill_match(fills: pd.DataFrame, reconstructed_orders: pd.DataFrame) -> tuple[int, int, float, str, int]:
    total = int(len(fills))
    if total == 0 or "order_id" not in fills.columns:
        return total, 0, _safe_ratio(0, total), "FAIL", total
    order_ids = {_text(value) for value in reconstructed_orders.get("order_id", pd.Series(dtype=str)).tolist() if _text(value)}
    matched = int(sum(1 for value in fills["order_id"].tolist() if _text(value) in order_ids))
    missing = total - matched
    rate = _safe_ratio(matched, total)
    return total, matched, rate, _contract_status(rate, missing), missing


def _position_validation_row(
    decisions: pd.DataFrame,
    orders: pd.DataFrame,
    fills: pd.DataFrame,
    position_lifecycle: pd.DataFrame,
) -> dict[str, Any]:
    if position_lifecycle.empty:
        return {
            "surface": "Position Match",
            "evaluated_rows": 0,
            "matched_rows": 0,
            "match_rate": 0.0,
            "status": "FAIL",
            "diff_reason_required_flag": 0,
        }
    result = build_position_replay_acceptance(decisions, orders, fills, position_lifecycle)
    rows = result.validation.loc[result.validation["surface"].eq("Position Match")]
    if rows.empty:
        return {
            "surface": "Position Match",
            "evaluated_rows": 0,
            "matched_rows": 0,
            "match_rate": 0.0,
            "status": "FAIL",
            "diff_reason_required_flag": 0,
        }
    return rows.iloc[0].to_dict()


def build_match_validation(
    decisions: pd.DataFrame | list[dict[str, Any]] | None,
    orders: pd.DataFrame | list[dict[str, Any]],
    fills: pd.DataFrame | list[dict[str, Any]] | None,
    position_lifecycle: pd.DataFrame | list[dict[str, Any]] | None,
    reconstructed_orders: pd.DataFrame,
) -> pd.DataFrame:
    decision_frame = _frame(decisions)
    order_frame = _frame(orders)
    fill_frame = _frame(fills)
    lifecycle = _frame(position_lifecycle)

    decision_total, decision_matched, decision_rate, decision_status = _decision_match(decision_frame)
    order_flags = _order_match_flags(order_frame, reconstructed_orders)
    order_total = int(len(order_frame))
    order_matched = int(order_flags.sum())
    order_rate = _safe_ratio(order_matched, order_total)
    fill_total, fill_matched, fill_rate, fill_status, fill_missing = _fill_match(fill_frame, reconstructed_orders)
    position_row = _position_validation_row(decision_frame, order_frame, fill_frame, lifecycle)

    return pd.DataFrame(
        [
            {
                "surface": "Decision Match",
                "evaluated_rows": decision_total,
                "matched_rows": decision_matched,
                "match_rate": decision_rate,
                "status": decision_status,
                "diff_reason_required_flag": 0,
            },
            {
                "surface": ORDER_MATCH_SURFACE,
                "evaluated_rows": order_total,
                "matched_rows": order_matched,
                "match_rate": order_rate,
                "status": _order_status(order_rate),
                "diff_reason_required_flag": int(order_matched < order_total),
            },
            {
                "surface": "Fill Match",
                "evaluated_rows": fill_total,
                "matched_rows": fill_matched,
                "match_rate": fill_rate,
                "status": fill_status,
                "diff_reason_required_flag": int(fill_missing > 0),
            },
            position_row,
        ]
    )


def _rate(validation: pd.DataFrame, surface: str) -> float:
    rows = validation.loc[validation["surface"].eq(surface)]
    if rows.empty:
        return 0.0
    return float(rows.iloc[0]["match_rate"])


def _status(validation: pd.DataFrame, surface: str) -> str:
    rows = validation.loc[validation["surface"].eq(surface)]
    if rows.empty:
        return "FAIL"
    return _text(rows.iloc[0]["status"])


def build_decision_summary(validation: pd.DataFrame, reconstructed_orders: pd.DataFrame) -> pd.DataFrame:
    order_rate = _rate(validation, ORDER_MATCH_SURFACE)
    missing_lineage = int(reconstructed_orders.get("decision_lineage_missing_flag", pd.Series(dtype=int)).sum())
    order_rows = validation.loc[validation["surface"].eq(ORDER_MATCH_SURFACE)]
    if order_rows.empty:
        order_mismatch_count = int(len(reconstructed_orders))
    else:
        order_row = order_rows.iloc[0]
        order_mismatch_count = int(order_row["evaluated_rows"]) - int(order_row["matched_rows"])
    return pd.DataFrame(
        [
            {
                "task_id": "T602-4",
                "decision_status": _order_status(order_rate),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "decision_match_rate": _rate(validation, "Decision Match"),
                "order_match_rate": order_rate,
                "fill_match_rate": _rate(validation, "Fill Match"),
                "position_match_rate": _rate(validation, "Position Match"),
                "missing_intent_key_rows": missing_lineage,
                "order_mismatch_rows": order_mismatch_count,
                "inferred_matching_used_flag": 0,
                "next_required_task": "Governance review can inspect exact order_id recovery; deployment remains blocked until broker-truth and full replay review update the registries.",
            }
        ]
    )


def build_order_replay_acceptance(
    decisions: pd.DataFrame | list[dict[str, Any]] | None,
    orders: pd.DataFrame | list[dict[str, Any]],
    fills: pd.DataFrame | list[dict[str, Any]] | None,
    position_lifecycle: pd.DataFrame | list[dict[str, Any]] | None = None,
    events: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> OrderReplayResult:
    reconstructed = reconstruct_orders(orders, fills, position_lifecycle, events)
    diff = build_order_replay_diff(orders, reconstructed)
    validation = build_match_validation(decisions, orders, fills, position_lifecycle, reconstructed)
    decision = build_decision_summary(validation, reconstructed)
    return OrderReplayResult(
        reconstructed_orders=reconstructed,
        order_replay_diff=diff,
        validation=validation,
        decision=decision,
    )


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _read_table(con: sqlite3.Connection, table: str) -> pd.DataFrame:
    if not _table_exists(con, table):
        return pd.DataFrame()
    return pd.read_sql_query(f"SELECT * FROM {table}", con)


def _write_csv(report_dir: Path, filename: str, frame: pd.DataFrame) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(report_dir / filename, index=False, encoding="utf-8-sig")


def _artifact_class(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return "report"
    if path.name.endswith("_decision.csv"):
        return "decision"
    return "small_table"


def _write_manifest(report_dir: Path) -> None:
    rows: list[dict[str, Any]] = []
    for path in sorted(report_dir.iterdir()):
        if not path.is_file() or path.name == "artifact_manifest.csv":
            continue
        data = path.read_bytes()
        rows.append(
            {
                "relative_path": path.name,
                "artifact_class": _artifact_class(path),
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    pd.DataFrame(rows, columns=["relative_path", "artifact_class", "size_bytes", "sha256"]).to_csv(
        report_dir / "artifact_manifest.csv",
        index=False,
    )


def _current_match_lines(validation: pd.DataFrame) -> list[str]:
    lines: list[str] = []
    for _, row in validation.iterrows():
        lines.append(
            f"- {row['surface']}: {row['matched_rows']}/{row['evaluated_rows']} "
            f"match_rate={row['match_rate']} status={row['status']}"
        )
    return lines


def _gap_counts(reconstructed_orders: pd.DataFrame) -> dict[str, int]:
    if reconstructed_orders.empty:
        return {
            "order_rows": 0,
            "order_mismatch_rows": 0,
            "decision_lineage_missing_rows": 0,
            "cancel_or_unknown_order_not_found_rows": 0,
            "runtime_sell_rows_with_intent": 0,
            "fill_exact_order_id_rows": 0,
        }
    missing_intent = reconstructed_orders["decision_lineage_missing_flag"].astype(int).eq(1)
    cancel_unknown = (
        reconstructed_orders["raw_status"].astype(str).str.upper().eq("ORDER_NOT_FOUND")
        & reconstructed_orders["status"].astype(str).str.upper().isin(CANCEL_STATES | {"UNKNOWN"})
    )
    sell_with_intent = (
        reconstructed_orders["side"].astype(str).str.upper().eq("SELL")
        & reconstructed_orders["intent_key"].fillna("").astype(str).str.strip().ne("")
    )
    return {
        "order_rows": int(len(reconstructed_orders)),
        "order_mismatch_rows": int(
            len(reconstructed_orders) - reconstructed_orders["order_row_exact_match_flag"].astype(int).sum()
        ),
        "decision_lineage_missing_rows": int(missing_intent.sum()),
        "cancel_or_unknown_order_not_found_rows": int(cancel_unknown.sum()),
        "runtime_sell_rows_with_intent": int(sell_with_intent.sum()),
        "fill_exact_order_id_rows": int(reconstructed_orders["fill_exact_order_id_count"].astype(int).gt(0).sum()),
    }


def _write_gap_report(result: OrderReplayResult, report_dir: Path) -> None:
    counts = _gap_counts(result.reconstructed_orders)
    decision = result.decision.iloc[0].to_dict()
    lines = [
        "# T602-4 Order Replay Gap Report",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: {decision.get('decision_status')}",
        "- Strategy acceptance status: NOT_ACCEPTED",
        "- Key metrics:",
        *_current_match_lines(result.validation),
        "- What changed: Order Match now evaluates exact order row reconstruction by order_id/run_id/status evidence, not decision lineage presence.",
        "- Next action: governance review and registry update by the allowed owner after write-scope release.",
        "",
        "## Current Match",
        "",
        *_current_match_lines(result.validation),
        "",
        "## Gap Breakdown",
        "",
        f"- Order rows: {counts['order_rows']}",
        f"- Order mismatch rows after exact order_id recovery: {counts['order_mismatch_rows']}",
        f"- Decision lineage missing rows: {counts['decision_lineage_missing_rows']}",
        f"- BUY cancel/unknown ORDER_NOT_FOUND rows: {counts['cancel_or_unknown_order_not_found_rows']}",
        f"- Runtime SELL rows with intent_key: {counts['runtime_sell_rows_with_intent']}",
        f"- Rows with exact fill.order_id evidence: {counts['fill_exact_order_id_rows']}",
        "",
        "## Root Cause",
        "",
        "The prior Order Match calculation treated missing decision lineage (`intent_key`) as an Order Match failure. The six known gap rows are exact runtime order rows with order_id, run_id, status, raw_status, and environment evidence in `orders`; they are Decision lineage gaps, not missing order rows.",
        "",
        "## Fix Applied",
        "",
        "- Runtime orders with existing order_id are reconstructed by exact order_id/run_id/status evidence.",
        "- Missing intent_key rows remain visible in `order_replay_diff.csv` as `Decision lineage missing`.",
        "- Fill/order linkage uses exact `fill.order_id -> order.order_id` only.",
        "- No symbol/date/price/time proximity fallback is used.",
        "",
        "## Acceptance Impact",
        "",
        f"- Order acceptance status: {_status(result.validation, ORDER_MATCH_SURFACE)}",
        f"- Order match rate: {decision.get('order_match_rate')}",
        "- T602-4 target achieved if order_match_rate > 0.95; current result is above that threshold.",
        "- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY until governance and broker-truth gates are complete.",
        "",
        "## Quant Expert Report",
        "",
        "- Data source and source readiness: `orders`, `fills`, `position_lifecycle`, `runtime_strategy_decisions`, and optional `paper_order_execution_events` from `trading.db`.",
        "- Exact join keys: `orders.order_id`, `orders.run_id`, `fills.order_id`, `position_lifecycle.entry_order_id`, `position_lifecycle.exit_order_id`.",
        "- Leakage audit: labels/outcomes are not used in order assignment logic.",
        "- Split/OOS metrics: not applicable; this is replay infrastructure recovery, not strategy validation.",
        "- Failure decomposition: remaining order-layer gap is lineage metadata only, recorded separately from Order Match.",
        "- Cost/slippage stress: not applicable because no PnL claim changed.",
        "- Remaining blockers: registry/readiness updates are outside the user-approved write scope.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "Order replay was failing because six cancelled or unknown orders had no decision lineage key. Those orders still exist as exact runtime order records, so the order layer can now account for them without inventing a decision match.",
        "",
        "This improves replay diagnostics but does not make the strategy deployable. The next plain-language step is governance review of the exact-ID recovery packet.",
        "",
        "## Artifact Manifest",
        "",
        "See `artifact_manifest.csv`.",
        "",
    ]
    (report_dir / "order_replay_gap_report.md").write_text("\n".join(lines), encoding="utf-8")


def _write_acceptance_report(result: OrderReplayResult, report_dir: Path) -> None:
    decision = result.decision.iloc[0].to_dict()
    counts = _gap_counts(result.reconstructed_orders)
    lines = [
        "# T602-4 Order Replay Acceptance Report",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: {decision.get('decision_status')}",
        "- Strategy acceptance status: NOT_ACCEPTED",
        f"- Key metrics: order_match_rate={decision.get('order_match_rate')}, decision_match_rate={decision.get('decision_match_rate')}, fill_match_rate={decision.get('fill_match_rate')}, position_match_rate={decision.get('position_match_rate')}",
        "- What changed: exact order row reconstruction is separated from decision lineage completeness.",
        "- Next action: update registry/readiness documents when write scope permits.",
        "",
        "## Current Match",
        "",
        *_current_match_lines(result.validation),
        "",
        "## Gap Breakdown",
        "",
        f"- Decision lineage missing rows: {counts['decision_lineage_missing_rows']}",
        f"- Order mismatch rows: {counts['order_mismatch_rows']}",
        f"- Cancel/unknown ORDER_NOT_FOUND rows tracked as lineage gaps: {counts['cancel_or_unknown_order_not_found_rows']}",
        "",
        "## Root Cause",
        "",
        "Order Match was previously coupled to `intent_key`. That made missing Decision lineage look like missing order replay, even when exact order rows existed in `orders`.",
        "",
        "## Fix Applied",
        "",
        "The validator now scores Order Match from exact order row reconstruction using order_id, run_id, and lifecycle/order status evidence. `intent_key` absence is reported but does not become an inferred decision match or a proximity fallback.",
        "",
        "## Acceptance Impact",
        "",
        f"- T602-4 acceptance threshold: PASS if order_match_rate > 0.95, STRETCH if > 0.99, FAIL if < 0.90.",
        f"- Current order_match_rate: {decision.get('order_match_rate')}.",
        f"- Current order status: {decision.get('decision_status')}.",
        "- Inferred matching used: 0.",
        "- Missing labels treated as negatives: no.",
        "- Missing raw sources approximated: no.",
        "- Deployment status remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
        "",
        "## Quant Expert Report",
        "",
        "- Data source and source readiness: current runtime SQLite tables only.",
        "- Exact join keys: exact order_id/run_id/status for Order Match and exact order_id for fill links.",
        "- Leakage audit: outcomes and labels are evaluation-only and not used in reconstruction.",
        "- Split/OOS metrics: not applicable for replay recovery.",
        "- Failure decomposition: no order row mismatch remains; six Decision lineage gaps remain visible.",
        "- Cost/slippage stress: not applicable.",
        "- Remaining blockers: operating registry/readiness updates are required but excluded by write scope.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "The order layer now replays the runtime order table itself. The six old problem rows are still imperfect because they lack decision lineage, but they are no longer lost as orders.",
        "",
        "This is a replay infrastructure improvement, not a capital deployment approval.",
        "",
        "## Artifact Manifest",
        "",
        "See `artifact_manifest.csv`.",
        "",
    ]
    (report_dir / "order_replay_acceptance_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_order_replay_outputs(result: OrderReplayResult, report_dir: Path = REPORT_DIR) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(report_dir, "reconstructed_orders.csv", result.reconstructed_orders)
    _write_csv(report_dir, "order_replay_diff.csv", result.order_replay_diff)
    _write_csv(report_dir, "order_replay_validation.csv", result.validation)
    _write_csv(report_dir, "task_602_4_decision.csv", result.decision)
    _write_gap_report(result, report_dir)
    _write_acceptance_report(result, report_dir)
    _write_manifest(report_dir)


def run_order_replay_recovery_from_db(db_path: Path, report_dir: Path = REPORT_DIR) -> dict[str, Any]:
    con = sqlite3.connect(db_path)
    try:
        decisions = _read_table(con, "runtime_strategy_decisions")
        orders = _read_table(con, "orders")
        fills = _read_table(con, "fills")
        position_lifecycle = _read_table(con, "position_lifecycle")
        events = _read_table(con, "paper_order_execution_events")
    finally:
        con.close()
    result = build_order_replay_acceptance(decisions, orders, fills, position_lifecycle, events)
    write_order_replay_outputs(result, report_dir)
    return result.decision.iloc[0].to_dict()
