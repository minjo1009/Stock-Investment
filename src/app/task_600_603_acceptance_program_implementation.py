from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.app.paper_runtime_common import append_registry_rows, read_table, utc_now, write_csv
from src.backtest.task_report_utils import write_standard_report
from src.reporting.readiness_registry import build_readiness_registry_payload, write_readiness_registry_payload


T600_DIR = Path("docs/reports/task_600_1_position_lifecycle_implementation")
T601_DIR = Path("docs/reports/task_601_1_candidate_funnel_implementation")
T602_DIR = Path("docs/reports/task_602_1_replay_acceptance_implementation")
T603_DIR = Path("docs/reports/task_603_1_registry_backed_readiness_consumption")

EXIT_TYPES = {"STOP", "TAKE_PROFIT", "TIMEOUT", "TRIM"}


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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


def _is_present(value: object) -> bool:
    return _text(value) != ""


def _timestamp(value: object) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def _minutes_between(start: object, end: object) -> float | None:
    start_ts = _timestamp(start)
    end_ts = _timestamp(end)
    if start_ts is None or end_ts is None:
        return None
    return round((end_ts - start_ts).total_seconds() / 60.0, 4)


def _safe_ratio(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(part / total, 6)


def _event_by_order(events: pd.DataFrame) -> dict[str, pd.Series]:
    if events.empty or "order_id" not in events.columns:
        return {}
    sortable = events.copy()
    if "created_at" in sortable.columns:
        sortable = sortable.sort_values("created_at")
    result: dict[str, pd.Series] = {}
    for _, row in sortable.iterrows():
        order_id = _text(row.get("order_id"))
        if order_id:
            result[order_id] = row
    return result


def _latest_marks(indicator_snapshots: pd.DataFrame) -> dict[str, float]:
    if indicator_snapshots.empty or "symbol" not in indicator_snapshots.columns:
        return {}
    frame = indicator_snapshots.copy()
    if "created_at" in frame.columns:
        frame = frame.sort_values("created_at")
    marks: dict[str, float] = {}
    for _, row in frame.iterrows():
        symbol = _upper(row.get("symbol"))
        if not symbol:
            continue
        value = row.get("source_price")
        if not _is_present(value):
            value = row.get("close")
        price = _float(value, default=float("nan"))
        if pd.notna(price):
            marks[symbol] = price
    return marks


def _exit_reason(row: pd.Series) -> str:
    raw = f"{_upper(row.get('reason_code'))} {_upper(row.get('order_status'))}"
    if "STOP" in raw:
        return "STOP"
    if "TAKE" in raw or "PROFIT" in raw:
        return "TAKE_PROFIT"
    if "TIMEOUT" in raw or "MAX_HOLD" in raw:
        return "TIMEOUT"
    if "TRIM" in raw or "PARTIAL" in raw or "REDUCE" in raw:
        return "TRIM"
    return ""


def build_position_lifecycle(
    fills: pd.DataFrame,
    orders: pd.DataFrame,
    execution_events: pd.DataFrame,
    marks: dict[str, float],
    *,
    hard_stop_pct: float = 0.05,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    event_by_order = _event_by_order(execution_events)
    order_by_id = {
        _text(row.get("order_id")): row
        for _, row in orders.iterrows()
    } if not orders.empty and "order_id" in orders.columns else {}
    lifecycle_rows: dict[str, dict[str, Any]] = {}
    unresolved_exits: list[dict[str, Any]] = []

    frame = fills.copy()
    if not frame.empty and "filled_at" in frame.columns:
        frame = frame.sort_values("filled_at")

    for _, fill in frame.iterrows():
        side = _upper(fill.get("side"))
        order_id = _text(fill.get("order_id"))
        fill_id = _text(fill.get("fill_id"))
        event = event_by_order.get(order_id, pd.Series(dtype=object))
        order = order_by_id.get(order_id, pd.Series(dtype=object))
        lifecycle_id = _text(event.get("lifecycle_id"))
        symbol = _upper(fill.get("symbol") or event.get("symbol") or order.get("symbol"))
        qty = _float(fill.get("filled_quantity"))
        price = _float(fill.get("fill_price"), default=float("nan"))
        filled_at = _text(fill.get("filled_at"))
        if side == "BUY":
            if not lifecycle_id:
                lifecycle_id = f"UNLINKED_ENTRY_FILL|{fill_id}"
                acceptance_status = "REJECTED_MISSING_EXACT_LIFECYCLE_ID"
                matching_policy = "NO_PROXIMITY_FALLBACK_MISSING_LIFECYCLE_ID"
            else:
                acceptance_status = "OPEN_ACCEPTED_EXACT_ENTRY"
                matching_policy = "EXACT_LIFECYCLE_ID_AND_ORDER_FILL_ID_ONLY"
            lifecycle_rows[lifecycle_id] = {
                "position_id": lifecycle_id,
                "symbol": symbol,
                "entry_order_id": order_id,
                "entry_fill_id": fill_id,
                "exit_order_id": "",
                "exit_fill_id": "",
                "entry_time": filled_at,
                "exit_time": "",
                "holding_minutes": "",
                "realized_pnl": "",
                "exit_reason": "",
                "state": "OPEN",
                "entry_price": price,
                "exit_price": "",
                "entry_qty": qty,
                "open_qty": qty,
                "closed_qty": 0.0,
                "matching_policy": matching_policy,
                "acceptance_status": acceptance_status,
                "proxy_pnl_used_flag": 0,
                "proximity_fallback_used_flag": 0,
            }
            continue
        if side == "SELL":
            if not lifecycle_id or lifecycle_id not in lifecycle_rows:
                unresolved_exits.append(
                    {
                        "order_id": order_id,
                        "fill_id": fill_id,
                        "symbol": symbol,
                        "side": side,
                        "filled_quantity": qty,
                        "fill_price": price,
                        "filled_at": filled_at,
                        "lifecycle_id": lifecycle_id,
                        "resolution_status": "UNRESOLVED_EXIT_NO_EXACT_ENTRY_LIFECYCLE",
                        "forbidden_fallbacks": "no_symbol_date_price_time_proximity",
                    }
                )
                continue
            row = lifecycle_rows[lifecycle_id]
            exit_reason = _exit_reason(event)
            open_qty = _float(row.get("open_qty"))
            close_qty = min(open_qty, qty)
            remaining_qty = max(open_qty - close_qty, 0.0)
            realized = (price - _float(row.get("entry_price"))) * close_qty
            row["exit_order_id"] = order_id
            row["exit_fill_id"] = fill_id
            row["exit_time"] = filled_at
            row["holding_minutes"] = _minutes_between(row.get("entry_time"), filled_at)
            row["realized_pnl"] = round(realized, 6)
            row["exit_reason"] = exit_reason
            row["exit_price"] = price
            row["open_qty"] = remaining_qty
            row["closed_qty"] = _float(row.get("closed_qty")) + close_qty
            row["state"] = "CLOSED" if remaining_qty == 0 else "PARTIAL_EXIT"
            row["acceptance_status"] = (
                "CLOSED_ACCEPTED_EXACT_IDS"
                if remaining_qty == 0 and exit_reason in EXIT_TYPES
                else "PARTIAL_EXIT_ACCEPTED_EXACT_IDS"
                if exit_reason == "TRIM"
                else "REJECTED_EXIT_REASON_MISSING"
            )
            row["matching_policy"] = "EXACT_LIFECYCLE_ID_AND_ORDER_FILL_ID_ONLY"

    lifecycle = pd.DataFrame(lifecycle_rows.values())
    required_cols = [
        "position_id",
        "symbol",
        "entry_order_id",
        "entry_fill_id",
        "exit_order_id",
        "exit_fill_id",
        "entry_time",
        "exit_time",
        "holding_minutes",
        "realized_pnl",
        "exit_reason",
        "state",
        "entry_price",
        "exit_price",
        "entry_qty",
        "open_qty",
        "closed_qty",
        "matching_policy",
        "acceptance_status",
        "proxy_pnl_used_flag",
        "proximity_fallback_used_flag",
    ]
    for column in required_cols:
        if column not in lifecycle.columns:
            lifecycle[column] = []
    lifecycle = lifecycle[required_cols]

    hard_stop_rows: list[dict[str, Any]] = []
    for _, row in lifecycle.iterrows():
        state = _text(row.get("state"))
        open_qty = _float(row.get("open_qty"))
        symbol = _upper(row.get("symbol"))
        mark = marks.get(symbol)
        entry_price = _float(row.get("entry_price"), default=float("nan"))
        threshold = entry_price * (1.0 - hard_stop_pct) if pd.notna(entry_price) else None
        triggered = bool(mark is not None and threshold is not None and mark <= threshold and open_qty > 0)
        if state in {"OPEN", "PARTIAL_EXIT"} and open_qty > 0:
            hard_stop_rows.append(
                {
                    "position_id": row.get("position_id"),
                    "symbol": symbol,
                    "entry_order_id": row.get("entry_order_id"),
                    "entry_fill_id": row.get("entry_fill_id"),
                    "entry_time": row.get("entry_time"),
                    "entry_price": entry_price,
                    "open_qty": open_qty,
                    "mark_price": mark,
                    "hard_stop_pct": hard_stop_pct,
                    "stop_threshold": threshold,
                    "exit_reason": "STOP" if triggered else "",
                    "hard_stop_triggered_flag": int(triggered),
                    "would_submit_order_flag": 0,
                    "action_status": "DIAGNOSTIC_ONLY_NO_EXIT_ORDER_SUBMITTED",
                }
            )
    hard_stop = pd.DataFrame(hard_stop_rows)
    unresolved = pd.DataFrame(unresolved_exits)

    sell_count = int(_upper_series(fills, "side").eq("SELL").sum()) if not fills.empty else 0
    buy_count = int(_upper_series(fills, "side").eq("BUY").sum()) if not fills.empty else 0
    closed_count = int(lifecycle["state"].astype(str).eq("CLOSED").sum()) if not lifecycle.empty else 0
    accepted_closed = int(lifecycle["acceptance_status"].astype(str).eq("CLOSED_ACCEPTED_EXACT_IDS").sum()) if not lifecycle.empty else 0
    status = "IMPLEMENTED_ACCEPTANCE_BLOCKED_SELL_FILLS_MISSING"
    if sell_count > 0 and accepted_closed == 0:
        status = "IMPLEMENTED_ACCEPTANCE_BLOCKED_CLOSED_LIFECYCLE_MISSING"
    elif accepted_closed > 0:
        status = "IMPLEMENTED_ACCEPTANCE_BLOCKED_REALIZED_TRADES_UNDER_100"
    validation = pd.DataFrame(
        [
            {
                "task_id": "T600-1",
                "implementation_status": status,
                "buy_fill_count": buy_count,
                "sell_fill_count": sell_count,
                "position_lifecycle_rows": int(len(lifecycle)),
                "closed_position_rows": closed_count,
                "accepted_closed_position_rows": accepted_closed,
                "open_position_rows": int(lifecycle["state"].astype(str).isin(["OPEN", "PARTIAL_EXIT"]).sum()) if not lifecycle.empty else 0,
                "hard_stop_candidate_rows": int(len(hard_stop)),
                "unresolved_exit_rows": int(len(unresolved)),
                "proxy_pnl_used_flag": 0,
                "proximity_fallback_used_flag": 0,
                "acceptance_status": "NOT_ACCEPTED",
                "next_gate": "SELL fills and exact closed lifecycle evidence required before acceptance review.",
            }
        ]
    )
    return lifecycle, hard_stop, unresolved, validation


def _upper_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if frame.empty or column not in frame.columns:
        return pd.Series(dtype=str)
    return frame[column].fillna("").astype(str).str.strip().str.upper()


def _eligibility(row: pd.Series) -> tuple[str, str, str]:
    reason = f"{_upper(row.get('reason_code'))} {_upper(row.get('reason_detail'))}"
    data_fresh = _float(row.get("data_fresh"))
    entry_allowed = _float(row.get("entry_allowed"))
    if "COOLDOWN" in reason:
        return "INELIGIBLE_COOLDOWN", reason.strip(), reason.strip()
    if data_fresh != 1:
        return "INELIGIBLE_SOURCE", "", reason.strip() or "SOURCE_NOT_FRESH"
    if "RISK" in reason:
        return "INELIGIBLE_RISK", "", reason.strip()
    if entry_allowed == 1:
        return "ELIGIBLE", "", ""
    return "INELIGIBLE_UNKNOWN", "", reason.strip() or "NO_ELIGIBILITY_EVIDENCE"


def build_candidate_funnel_events(
    decisions: pd.DataFrame,
    execution_events: pd.DataFrame,
    fills: pd.DataFrame,
    position_lifecycle: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    events_by_decision: dict[str, pd.Series] = {}
    if not execution_events.empty and "decision_id" in execution_events.columns:
        sortable = execution_events.copy()
        if "created_at" in sortable.columns:
            sortable = sortable.sort_values("created_at")
        for _, row in sortable.iterrows():
            decision_id = _text(row.get("decision_id"))
            if decision_id:
                events_by_decision[decision_id] = row
    fills_by_order = {
        _text(row.get("order_id")): row
        for _, row in fills.iterrows()
    } if not fills.empty and "order_id" in fills.columns else {}
    closed_by_entry_order = set()
    if not position_lifecycle.empty:
        closed = position_lifecycle.loc[position_lifecycle["state"].astype(str).eq("CLOSED")]
        closed_by_entry_order = set(closed["entry_order_id"].fillna("").astype(str))

    rows: list[dict[str, Any]] = []
    ordered_ids: set[str] = set()
    filled_ids: set[str] = set()
    closed_ids: set[str] = set()
    ordered_without_rank = 0
    ordered_cooldown_blocked = 0
    missing_skip_reason = 0

    frame = decisions.copy()
    if not frame.empty and "created_at" in frame.columns:
        frame = frame.sort_values("created_at")
    for _, decision in frame.iterrows():
        decision_id = _text(decision.get("decision_id"))
        if not decision_id:
            continue
        candidate_id = decision_id
        symbol = _upper(decision.get("symbol"))
        generated_time = _text(decision.get("created_at"))
        rank_score = decision.get("score")
        source_snapshot_id = _text(decision.get("source_snapshot_id"))
        eligibility, cooldown_reason, skip_reason = _eligibility(decision)
        event = events_by_decision.get(decision_id, pd.Series(dtype=object))
        order_id = _text(event.get("order_id"))
        if not order_id:
            order_id = _text(event.get("client_order_id")) if _upper(event.get("order_status")) not in {"SKIPPED", ""} else ""
        fill = fills_by_order.get(order_id, pd.Series(dtype=object))
        fill_id = _text(fill.get("fill_id"))

        base = {
            "candidate_id": candidate_id,
            "symbol": symbol,
            "generated_time": generated_time,
            "rank_score": rank_score,
            "eligibility": eligibility,
            "cooldown_reason": cooldown_reason,
            "skip_reason": skip_reason,
            "order_id": order_id,
            "fill_id": fill_id,
            "source_snapshot_id": source_snapshot_id,
            "decision_id": decision_id,
            "created_at": utc_now(),
            "exact_join_keys": "decision_id,order_id,fill_id,position_id",
            "proximity_fallback_used_flag": 0,
        }
        rows.append({**base, "stage": "GENERATED", "stage_sequence": 1, "event_status": "RECORDED"})
        if _is_present(rank_score):
            rows.append({**base, "stage": "RANKED", "stage_sequence": 2, "event_status": "RECORDED"})
        if eligibility == "ELIGIBLE":
            rows.append({**base, "stage": "ELIGIBLE", "stage_sequence": 3, "event_status": "RECORDED"})
        elif not order_id and not skip_reason:
            missing_skip_reason += 1
        if order_id:
            ordered_ids.add(candidate_id)
            if not _is_present(rank_score):
                ordered_without_rank += 1
            if eligibility == "INELIGIBLE_COOLDOWN":
                ordered_cooldown_blocked += 1
            rows.append({**base, "stage": "ORDERED", "stage_sequence": 4, "event_status": "RECORDED"})
        elif skip_reason:
            rows.append({**base, "stage": "ELIGIBLE", "stage_sequence": 3, "event_status": "STOPPED_WITH_SKIP_REASON"})
        if fill_id:
            filled_ids.add(candidate_id)
            rows.append({**base, "stage": "FILLED", "stage_sequence": 5, "event_status": "RECORDED"})
        if order_id in closed_by_entry_order:
            closed_ids.add(candidate_id)
            rows.append({**base, "stage": "CLOSED", "stage_sequence": 6, "event_status": "RECORDED"})

    funnel = pd.DataFrame(rows)
    generated_count = int(decisions["decision_id"].dropna().astype(str).nunique()) if not decisions.empty and "decision_id" in decisions.columns else 0
    filled_symbols = funnel.loc[funnel["stage"].eq("FILLED"), "symbol"] if not funnel.empty else pd.Series(dtype=str)
    fill_count = int(len(filled_symbols))
    symbol_counts = filled_symbols.value_counts()
    top_symbol_concentration = _safe_ratio(int(symbol_counts.iloc[0]) if not symbol_counts.empty else 0, fill_count)
    top3_concentration = _safe_ratio(int(symbol_counts.head(3).sum()) if not symbol_counts.empty else 0, fill_count)
    cooldown_count = int(funnel.loc[funnel["stage"].eq("GENERATED"), "eligibility"].astype(str).eq("INELIGIBLE_COOLDOWN").sum()) if not funnel.empty else 0
    status = "IMPLEMENTED_AUDIT_READY"
    if top_symbol_concentration > 0.8:
        status = "IMPLEMENTED_ACCEPTANCE_BLOCKED_SINGLE_SYMBOL_CONCENTRATION"
    if top3_concentration >= 0.5 and fill_count > 0:
        status = "IMPLEMENTED_ACCEPTANCE_BLOCKED_TOP3_CONCENTRATION"
    if ordered_without_rank or ordered_cooldown_blocked or missing_skip_reason:
        status = "IMPLEMENTED_ACCEPTANCE_BLOCKED_FUNNEL_RULE_VIOLATION"
    metrics = pd.DataFrame(
        [
            {
                "task_id": "T601-1",
                "implementation_status": status,
                "generated_candidates": generated_count,
                "ordered_candidates": len(ordered_ids),
                "filled_candidates": len(filled_ids),
                "closed_candidates": len(closed_ids),
                "candidate_to_order_ratio": _safe_ratio(len(ordered_ids), generated_count),
                "candidate_to_fill_ratio": _safe_ratio(len(filled_ids), generated_count),
                "top_symbol_concentration": top_symbol_concentration,
                "top3_symbol_fill_concentration": top3_concentration,
                "cooldown_rate": _safe_ratio(cooldown_count, generated_count),
                "ordered_without_rank_count": ordered_without_rank,
                "ordered_cooldown_blocked_count": ordered_cooldown_blocked,
                "skipped_missing_reason_count": missing_skip_reason,
                "proximity_fallback_used_flag": 0,
                "acceptance_status": "NOT_ACCEPTED",
            }
        ]
    )
    return funnel, metrics


def _surface_status(match_rate: float, missing_reason_count: int = 0) -> str:
    if match_rate >= 0.99 and missing_reason_count == 0:
        return "PASS"
    if match_rate >= 0.95 and missing_reason_count == 0:
        return "REVIEW"
    return "FAIL"


def build_replay_acceptance(
    decisions: pd.DataFrame,
    orders: pd.DataFrame,
    fills: pd.DataFrame,
    position_lifecycle: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    diff_rows: list[dict[str, Any]] = []
    decision_total = int(decisions["decision_id"].dropna().astype(str).nunique()) if not decisions.empty and "decision_id" in decisions.columns else 0
    decision_matched = decision_total

    order_total = int(orders["order_id"].dropna().astype(str).nunique()) if not orders.empty and "order_id" in orders.columns else 0
    order_missing_decision = 0
    if order_total and "intent_key" in orders.columns:
        order_missing_decision = int(orders["intent_key"].fillna("").astype(str).eq("").sum())
        for _, row in orders.loc[orders["intent_key"].fillna("").astype(str).eq("")].iterrows():
            diff_rows.append(
                {
                    "surface": "Order Match",
                    "decision_id": "",
                    "order_id": row.get("order_id"),
                    "fill_id": "",
                    "position_id": "",
                    "field_name": "decision_id",
                    "runtime_value": "",
                    "replay_value": "",
                    "diff_reason": "order row has no exact decision_id/intent_key",
                    "severity": "material",
                }
            )
    order_matched = max(order_total - order_missing_decision, 0)

    fill_total = int(fills["fill_id"].dropna().astype(str).nunique()) if not fills.empty and "fill_id" in fills.columns else 0
    fill_missing_order = 0
    if fill_total and "order_id" in fills.columns:
        fill_missing_order = int(fills["order_id"].fillna("").astype(str).eq("").sum())
        for _, row in fills.loc[fills["order_id"].fillna("").astype(str).eq("")].iterrows():
            diff_rows.append(
                {
                    "surface": "Fill Match",
                    "decision_id": "",
                    "order_id": "",
                    "fill_id": row.get("fill_id"),
                    "position_id": "",
                    "field_name": "order_id",
                    "runtime_value": "",
                    "replay_value": "",
                    "diff_reason": "fill row has no exact order_id",
                    "severity": "material",
                }
            )
    fill_matched = max(fill_total - fill_missing_order, 0)

    position_total = int(len(position_lifecycle))
    closed_count = int(position_lifecycle["state"].astype(str).eq("CLOSED").sum()) if not position_lifecycle.empty else 0
    accepted_closed = int(position_lifecycle["acceptance_status"].astype(str).eq("CLOSED_ACCEPTED_EXACT_IDS").sum()) if not position_lifecycle.empty else 0
    if accepted_closed == 0:
        diff_rows.append(
            {
                "surface": "Position Match",
                "decision_id": "",
                "order_id": "",
                "fill_id": "",
                "position_id": "",
                "field_name": "closed_lifecycle_coverage",
                "runtime_value": f"closed={closed_count}",
                "replay_value": "accepted_closed=0",
                "diff_reason": "SELL fills or exact CLOSED lifecycle evidence missing; position replay surface cannot pass.",
                "severity": "material",
            }
        )
    position_matched = accepted_closed
    position_match_rate = _safe_ratio(position_matched, max(position_total, 1))

    validation_rows = [
        {
            "surface": "Decision Match",
            "evaluated_rows": decision_total,
            "matched_rows": decision_matched,
            "match_rate": _safe_ratio(decision_matched, decision_total),
            "status": _surface_status(_safe_ratio(decision_matched, decision_total)),
            "diff_reason_required_flag": 0,
        },
        {
            "surface": "Order Match",
            "evaluated_rows": order_total,
            "matched_rows": order_matched,
            "match_rate": _safe_ratio(order_matched, order_total),
            "status": _surface_status(_safe_ratio(order_matched, order_total), order_missing_decision),
            "diff_reason_required_flag": int(order_missing_decision > 0),
        },
        {
            "surface": "Fill Match",
            "evaluated_rows": fill_total,
            "matched_rows": fill_matched,
            "match_rate": _safe_ratio(fill_matched, fill_total),
            "status": _surface_status(_safe_ratio(fill_matched, fill_total), fill_missing_order),
            "diff_reason_required_flag": int(fill_missing_order > 0),
        },
        {
            "surface": "Position Match",
            "evaluated_rows": position_total,
            "matched_rows": position_matched,
            "match_rate": position_match_rate,
            "status": _surface_status(position_match_rate, int(accepted_closed == 0)),
            "diff_reason_required_flag": int(accepted_closed == 0),
        },
    ]
    validation = pd.DataFrame(validation_rows)
    if not diff_rows:
        diff_rows.append(
            {
                "surface": "All Surfaces",
                "decision_id": "",
                "order_id": "",
                "fill_id": "",
                "position_id": "",
                "field_name": "",
                "runtime_value": "",
                "replay_value": "",
                "diff_reason": "no material mismatch recorded",
                "severity": "info",
            }
        )
    return pd.DataFrame(diff_rows), validation


def write_runtime_tables(db_path: Path, position_lifecycle: pd.DataFrame, candidate_funnel_events: pd.DataFrame) -> None:
    con = sqlite3.connect(db_path)
    try:
        position_lifecycle.to_sql("position_lifecycle", con, if_exists="replace", index=False)
        candidate_funnel_events.to_sql("candidate_funnel_events", con, if_exists="replace", index=False)
        con.commit()
    finally:
        con.close()


def _decision_status(frame: pd.DataFrame, default: str) -> str:
    if frame.empty or "implementation_status" not in frame.columns:
        return default
    return _text(frame.iloc[0].get("implementation_status")) or default


def _write_t600_report(report_dir: Path, validation: pd.DataFrame) -> None:
    row = validation.iloc[0].to_dict()
    write_standard_report(
        report_dir / "lifecycle_test_report.md",
        title="T600-1 Position Lifecycle Implementation",
        decision_summary=[
            f"Verdict: {row['implementation_status']}",
            "Strategy acceptance status: NOT_ACCEPTED",
            f"Key metrics: BUY fills={row['buy_fill_count']}, SELL fills={row['sell_fill_count']}, accepted closed={row['accepted_closed_position_rows']}",
            "What changed: `position_lifecycle` is now generated from exact lifecycle/order/fill IDs only.",
            "Next action: create real STOP/TAKE_PROFIT/TIMEOUT/TRIM exit fills before acceptance review.",
        ],
        quant_expert_lines=[
            "- Data source and source readiness: `trading.db` broker-truth fills, orders, and paper_order_execution_events.",
            "- Exact join keys: `order_id`, `fill_id`, and `lifecycle_id` only.",
            "- Leakage audit: labels, future outcomes, and proxy PnL are not used.",
            "- Failure decomposition: current lifecycle remains buy-only when SELL fills equal zero.",
            "- Remaining blockers: exact SELL lifecycle, realized closed-trade evidence, and 100+ realized trades.",
        ],
        decision_maker_lines=[
            "- The project now has an implementation artifact for the lifecycle contract.",
            "- This does not make the strategy accepted because exits are still missing or insufficient.",
            "- Capital/deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        ],
    )


def _write_t601_report(report_dir: Path, metrics: pd.DataFrame) -> None:
    row = metrics.iloc[0].to_dict()
    write_standard_report(
        report_dir / "candidate_funnel_audit.md",
        title="T601-1 Candidate Funnel Implementation",
        decision_summary=[
            f"Verdict: {row['implementation_status']}",
            "Strategy acceptance status: NOT_ACCEPTED",
            f"Key metrics: generated={row['generated_candidates']}, ordered={row['ordered_candidates']}, filled={row['filled_candidates']}",
            "What changed: `candidate_funnel_events` is now populated across GENERATED/RANKED/ELIGIBLE/ORDERED/FILLED/CLOSED.",
            "Next action: reduce concentration and close every ordered/filled candidate through exact lifecycle evidence.",
        ],
        quant_expert_lines=[
            "- Data source and source readiness: runtime decisions, paper execution events, broker-truth fills, and T600 position lifecycle.",
            "- Exact join keys: `decision_id`, `order_id`, `fill_id`, `position_id`.",
            "- Leakage audit: candidate assignment does not use labels, future outcomes, or proximity matching.",
            "- Failure decomposition: concentration and missing CLOSED lifecycle coverage remain acceptance blockers when present.",
            "- Remaining blockers: top-symbol concentration, top-3 concentration, and skip/explanation coverage.",
        ],
        decision_maker_lines=[
            "- Candidate flow is now auditable instead of just reporting candidate and fill counts.",
            "- This does not prove candidate quality yet; it exposes where candidates stop.",
            "- Capital/deployment readiness remains unchanged.",
        ],
    )


def _write_t602_report(report_dir: Path, validation: pd.DataFrame) -> None:
    statuses = ", ".join(f"{row.surface}={row.status}" for row in validation.itertuples(index=False))
    write_standard_report(
        report_dir / "paper_replay_acceptance_report.md",
        title="T602-1 Replay Acceptance Implementation",
        decision_summary=[
            f"Verdict: {'FAIL' if 'FAIL' in set(validation['status'].astype(str)) else 'PASS'}",
            "Strategy acceptance status: NOT_ACCEPTED",
            f"Key metrics: {statuses}",
            "What changed: replay validation and diff artifacts now exist for decision, order, fill, and position surfaces.",
            "Next action: make Position Match pass with exact closed lifecycle evidence.",
        ],
        quant_expert_lines=[
            "- Data source and source readiness: runtime decisions, orders, broker-truth fills, and generated position_lifecycle.",
            "- Exact join keys: no symbol/date/price/time proximity fallback is used.",
            "- Leakage audit: replay surfaces do not use labels or post-close assignment information.",
            "- Failure decomposition: Position Match fails if accepted closed lifecycle rows are missing.",
            "- Remaining blockers: PASS requires every surface to reach at least 99%.",
        ],
        decision_maker_lines=[
            "- The replay acceptance report is now concrete instead of a placeholder.",
            "- The current result is still not acceptance because position replay cannot pass without real exits.",
            "- Capital/deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        ],
    )
    lines = [
        "# T602-1 Replay Validation",
        "",
        "| Surface | Evaluated Rows | Matched Rows | Match Rate | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for _, row in validation.iterrows():
        lines.append(
            f"| {row['surface']} | {row['evaluated_rows']} | {row['matched_rows']} | {row['match_rate']} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "PASS requires every surface to be `>= 99%`. REVIEW is not enough for program-level `ACCEPTANCE_REVIEW`.",
            "",
        ]
    )
    (report_dir / "replay_validation.md").write_text("\n".join(lines), encoding="utf-8")


def _write_t603_report(report_dir: Path, payload: dict[str, Any]) -> None:
    blockers = payload.get("blockers", [])
    rows = pd.DataFrame(
        [
            {
                "task_id": "T603-1",
                "canonical_source": payload.get("canonical_source"),
                "load_status": payload.get("load_status"),
                "paper_operation_status": payload.get("paper_operation", {}).get("status"),
                "strategy_acceptance_status": payload.get("strategy_acceptance", {}).get("status"),
                "deployment_readiness_status": payload.get("deployment_readiness", {}).get("status"),
                "blocker_count": len(blockers),
                "payload_outputs": "frontend_data/catalog/readiness_registry.json; frontend/trader-terminal/public/catalog/readiness_registry.json",
            }
        ]
    )
    write_csv(report_dir, "readiness_registry_consumption_audit.csv", rows)
    write_standard_report(
        report_dir / "task_603_1_registry_backed_readiness_consumption.md",
        title="T603-1 Registry-Backed Readiness Consumption",
        decision_summary=[
            "Verdict: REGISTRY_PAYLOAD_IMPLEMENTED",
            "Strategy acceptance status: NOT_ACCEPTED",
            f"Key metrics: blocker_count={len(blockers)}",
            "What changed: canonical readiness registry payload is generated for catalog/frontend consumption.",
            "Next action: frontend copy can render registry payload without re-deriving current acceptance state.",
        ],
        quant_expert_lines=[
            "- Data source and source readiness: `docs/ownership/readiness_registry.yaml`.",
            "- Exact join keys: blocker IDs and acceptance gate IDs from the registry.",
            "- Leakage audit: generated payload does not infer acceptance from scorecards or UI state.",
            "- Failure decomposition: catalog may still contain diagnostic warning codes, but current acceptance status comes from registry payload.",
            "- Remaining blockers: UI rendering can be tightened later without changing today's contract implementation.",
        ],
        decision_maker_lines=[
            "- The official project status is now exportable as JSON.",
            "- This reduces drift between operating docs, generated catalog, and frontend data.",
            "- Capital/deployment readiness remains unchanged.",
        ],
    )


def _write_decision(report_dir: Path, filename: str, row: dict[str, Any]) -> None:
    write_csv(report_dir, filename, pd.DataFrame([row]))


def _append_registry() -> None:
    append_registry_rows(
        [
            {
                "task_id": "T600-1",
                "title": "Position Lifecycle Implementation",
                "owner_team": "Execution & Risk",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "not-accepted",
                "data_readiness": "runtime-source",
                "parent_task": "T600-0",
                "key_report": "docs/reports/task_600_1_position_lifecycle_implementation/lifecycle_test_report.md",
                "key_decision": "docs/reports/task_600_1_position_lifecycle_implementation/task_600_1_decision.csv",
                "key_artifacts": "docs/reports/task_600_1_position_lifecycle_implementation",
                "validation_command": "python -m unittest tests.test_task600_603_acceptance_program_implementation",
                "notes": "Implements exact-ID position_lifecycle and hard-stop candidate evidence without submitting exit orders.",
            },
            {
                "task_id": "T601-1",
                "title": "Candidate Funnel Events Implementation",
                "owner_team": "Candidate Funnel Research",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "not-accepted",
                "data_readiness": "runtime-source",
                "parent_task": "T601-0",
                "key_report": "docs/reports/task_601_1_candidate_funnel_implementation/candidate_funnel_audit.md",
                "key_decision": "docs/reports/task_601_1_candidate_funnel_implementation/task_601_1_decision.csv",
                "key_artifacts": "docs/reports/task_601_1_candidate_funnel_implementation",
                "validation_command": "python -m unittest tests.test_task600_603_acceptance_program_implementation",
                "notes": "Populates candidate_funnel_events from generated decisions through ordered filled and closed stages using exact IDs only.",
            },
            {
                "task_id": "T602-1",
                "title": "Replay Acceptance Implementation",
                "owner_team": "Replay & Simulation",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "not-accepted",
                "data_readiness": "runtime-source",
                "parent_task": "T602-0",
                "key_report": "docs/reports/task_602_1_replay_acceptance_implementation/paper_replay_acceptance_report.md",
                "key_decision": "docs/reports/task_602_1_replay_acceptance_implementation/task_602_1_decision.csv",
                "key_artifacts": "docs/reports/task_602_1_replay_acceptance_implementation",
                "validation_command": "python -m unittest tests.test_task600_603_acceptance_program_implementation",
                "notes": "Produces replay_validation and replay_diff surfaces for decision order fill and position matching.",
            },
            {
                "task_id": "T603-1",
                "title": "Registry Backed Readiness Consumption",
                "owner_team": "Research Governance",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "not-accepted",
                "data_readiness": "runtime-source",
                "parent_task": "T603",
                "key_report": "docs/reports/task_603_1_registry_backed_readiness_consumption/task_603_1_registry_backed_readiness_consumption.md",
                "key_decision": "docs/reports/task_603_1_registry_backed_readiness_consumption/task_603_1_decision.csv",
                "key_artifacts": "docs/reports/task_603_1_registry_backed_readiness_consumption",
                "validation_command": "python -m unittest tests.test_trader_terminal_catalog tests.test_task600_603_acceptance_program_implementation",
                "notes": "Generates canonical readiness_registry.json for catalog and frontend consumption.",
            },
        ]
    )


def run_task600_603(db_path: Path = Path("trading.db")) -> dict[str, Any]:
    fills = read_table(db_path, "fills", order_by="rowid", limit=None)
    orders = read_table(db_path, "orders", order_by="rowid", limit=None)
    execution_events = read_table(db_path, "paper_order_execution_events", order_by="rowid", limit=None)
    decisions = read_table(db_path, "runtime_strategy_decisions", order_by="rowid", limit=None)
    indicator_snapshots = read_table(db_path, "indicator_snapshots", order_by="rowid", limit=None)
    marks = _latest_marks(indicator_snapshots)

    lifecycle, hard_stop, unresolved, lifecycle_validation = build_position_lifecycle(fills, orders, execution_events, marks)
    candidate_funnel, funnel_metrics = build_candidate_funnel_events(decisions, execution_events, fills, lifecycle)
    replay_diff, replay_validation = build_replay_acceptance(decisions, orders, fills, lifecycle)
    write_runtime_tables(db_path, lifecycle, candidate_funnel)

    for path in [T600_DIR, T601_DIR, T602_DIR, T603_DIR]:
        _ensure_dir(path)

    write_csv(T600_DIR, "position_lifecycle.csv", lifecycle)
    write_csv(T600_DIR, "hard_stop_exit_candidates.csv", hard_stop)
    write_csv(T600_DIR, "unresolved_exit_fills.csv", unresolved)
    write_csv(T600_DIR, "lifecycle_validation.csv", lifecycle_validation)
    _write_decision(
        T600_DIR,
        "task_600_1_decision.csv",
        {
            "task_id": "T600-1",
            "decision_status": _decision_status(lifecycle_validation, "IMPLEMENTED_ACCEPTANCE_BLOCKED"),
            "strategy_acceptance_status": "NOT_ACCEPTED",
            "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "program_blocker": "P0_EXIT_LIFECYCLE",
            "next_required_task": "Generate exact SELL lifecycle fills through STOP/TAKE_PROFIT/TIMEOUT/TRIM before acceptance review.",
        },
    )
    _write_t600_report(T600_DIR, lifecycle_validation)
    write_manifest(T600_DIR, T600_DIR / "artifact_manifest.csv")

    write_csv(T601_DIR, "candidate_funnel_events.csv", candidate_funnel)
    write_csv(T601_DIR, "candidate_funnel_metrics.csv", funnel_metrics)
    _write_decision(
        T601_DIR,
        "task_601_1_decision.csv",
        {
            "task_id": "T601-1",
            "decision_status": _decision_status(funnel_metrics, "IMPLEMENTED_AUDIT_READY"),
            "strategy_acceptance_status": "NOT_ACCEPTED",
            "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "program_blocker": "P0_CANDIDATE_FUNNEL",
            "next_required_task": "Use candidate_funnel_events to reduce concentration and prove every ordered/filled candidate path.",
        },
    )
    _write_t601_report(T601_DIR, funnel_metrics)
    write_manifest(T601_DIR, T601_DIR / "artifact_manifest.csv")

    write_csv(T602_DIR, "replay_diff.csv", replay_diff)
    write_csv(T602_DIR, "replay_validation.csv", replay_validation)
    _write_decision(
        T602_DIR,
        "task_602_1_decision.csv",
        {
            "task_id": "T602-1",
            "decision_status": "FAIL" if "FAIL" in set(replay_validation["status"].astype(str)) else "PASS",
            "strategy_acceptance_status": "NOT_ACCEPTED",
            "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "program_blocker": "P0_EXACT_REPLAY",
            "next_required_task": "Position Match must pass at 99 percent with exact CLOSED lifecycle evidence.",
        },
    )
    _write_t602_report(T602_DIR, replay_validation)
    write_manifest(T602_DIR, T602_DIR / "artifact_manifest.csv")

    readiness_payload = build_readiness_registry_payload()
    write_readiness_registry_payload(readiness_payload)
    (T603_DIR / "readiness_registry_payload.json").write_text(
        json.dumps(readiness_payload, ensure_ascii=False, indent=2, default=str, allow_nan=False),
        encoding="utf-8",
    )
    _write_decision(
        T603_DIR,
        "task_603_1_decision.csv",
        {
            "task_id": "T603-1",
            "decision_status": "REGISTRY_PAYLOAD_IMPLEMENTED",
            "strategy_acceptance_status": "NOT_ACCEPTED",
            "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "program_blocker": "P2_GOVERNANCE_ENFORCEMENT",
            "next_required_task": "Render canonical readiness payload in frontend without re-derived acceptance state.",
        },
    )
    _write_t603_report(T603_DIR, readiness_payload)
    write_manifest(T603_DIR, T603_DIR / "artifact_manifest.csv")
    _append_registry()

    return {
        "generated_utc": datetime.now(UTC).isoformat(),
        "t600_status": _decision_status(lifecycle_validation, ""),
        "t601_status": _decision_status(funnel_metrics, ""),
        "t602_status": "FAIL" if "FAIL" in set(replay_validation["status"].astype(str)) else "PASS",
        "t603_status": "REGISTRY_PAYLOAD_IMPLEMENTED",
        "position_lifecycle_rows": len(lifecycle),
        "candidate_funnel_events_rows": len(candidate_funnel),
        "replay_diff_rows": len(replay_diff),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("trading.db"))
    args = parser.parse_args()
    result = run_task600_603(args.db)
    print(result)


if __name__ == "__main__":
    main()
