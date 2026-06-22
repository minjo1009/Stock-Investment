from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from src.execution.broker_truth_exit_mapper import is_broker_truth_fill_source


TASK_ID = "T603-6"
MATCHING_POLICY = "EXACT_POSITION_ORDER_FILL_OR_BROKER_EVENT_ID_ONLY"
BROKER_TRADE_LINEAGE_COLUMNS = [
    "lineage_id",
    "position_id",
    "signal_id",
    "order_id",
    "broker_order_id",
    "fill_id",
    "broker_fill_id",
    "broker_status",
    "broker_fill_price",
    "broker_fill_timestamp",
    "created_at",
]


@dataclass(frozen=True)
class BrokerTradeLineageMetrics:
    task_id: str
    runtime_sell_trade_count: int
    broker_truth_sell_fills: int
    lineage_rows: int
    exact_local_lineage_rows: int
    broker_fill_linked_rows: int
    missing_broker_fill_count: int
    non_unique_exact_match_count: int
    lineage_coverage: float
    broker_fill_linkage: float
    current_status: str
    acceptance_status: str
    matching_policy: str
    inferred_matching_used_flag: int
    proximity_fallback_used_flag: int
    real_capital_status: str


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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


def _float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(parsed):
        return None
    return parsed


def _frame(value: pd.DataFrame | list[dict[str, Any]] | None) -> pd.DataFrame:
    if value is None:
        return pd.DataFrame()
    if isinstance(value, pd.DataFrame):
        return value.copy()
    return pd.DataFrame(value)


def _extract_first_fill_id(raw_json: object) -> str:
    raw_text = _text(raw_json)
    if not raw_text:
        return ""
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return ""

    def walk(value: object) -> str:
        if isinstance(value, dict):
            for key in ("fill_id", "execution_id", "exec_id", "trade_id", "ccld_no"):
                found = _text(value.get(key))
                if found:
                    return found
            for child in value.values():
                found = walk(child)
                if found:
                    return found
        if isinstance(value, list):
            for child in value:
                found = walk(child)
                if found:
                    return found
        return ""

    return walk(payload)


def _empty_broker_truth_sources() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "broker_fill_id",
            "broker_order_id",
            "broker_event_id",
            "broker_lifecycle_id",
            "broker_status",
            "broker_fill_price",
            "broker_fill_timestamp",
            "broker_truth_source",
            "broker_truth_source_table",
            "source_priority",
        ]
    )


def broker_truth_sell_fill_sources(
    fills: pd.DataFrame | list[dict[str, Any]] | None,
    execution_events: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> pd.DataFrame:
    fill_frame = _frame(fills)
    event_frame = _frame(execution_events)
    rows: list[dict[str, Any]] = []
    order_ids_with_fill_rows: set[str] = set()

    if not fill_frame.empty:
        for _, row in fill_frame.iterrows():
            if _upper(row.get("side")) != "SELL":
                continue
            source = _text(row.get("source"))
            if not is_broker_truth_fill_source(source):
                continue
            fill_id = _text(row.get("fill_id"))
            order_id = _text(row.get("order_id"))
            if not fill_id or not order_id:
                continue
            qty = _float(row.get("filled_quantity"))
            if qty is not None and qty <= 0:
                continue
            order_ids_with_fill_rows.add(order_id)
            rows.append(
                {
                    "broker_fill_id": fill_id,
                    "broker_order_id": order_id,
                    "broker_event_id": "",
                    "broker_lifecycle_id": "",
                    "broker_status": "FILLED",
                    "broker_fill_price": _float(row.get("fill_price")),
                    "broker_fill_timestamp": _text(row.get("filled_at")),
                    "broker_truth_source": source,
                    "broker_truth_source_table": "fills",
                    "source_priority": 1,
                }
            )

    if not event_frame.empty:
        for _, row in event_frame.iterrows():
            if _upper(row.get("side")) != "SELL":
                continue
            if int(_float(row.get("broker_truth_fill_flag")) or 0) != 1:
                continue
            source = _text(row.get("fill_confirmation_source")) or "BROKER_ORDER_STATUS_EVENT"
            if not is_broker_truth_fill_source(source):
                continue
            order_id = _text(row.get("order_id"))
            event_id = _text(row.get("event_id"))
            if not order_id or not event_id or order_id in order_ids_with_fill_rows:
                continue
            qty = _float(row.get("filled_qty"))
            if qty is not None and qty <= 0:
                continue
            rows.append(
                {
                    "broker_fill_id": _extract_first_fill_id(row.get("raw_response_json")) or event_id,
                    "broker_order_id": order_id,
                    "broker_event_id": event_id,
                    "broker_lifecycle_id": _text(row.get("lifecycle_id")),
                    "broker_status": _text(row.get("order_status")) or "FILLED",
                    "broker_fill_price": _float(row.get("filled_avg_price")),
                    "broker_fill_timestamp": _text(row.get("created_at")),
                    "broker_truth_source": source,
                    "broker_truth_source_table": "paper_order_execution_events",
                    "source_priority": 2,
                }
            )

    if not rows:
        return _empty_broker_truth_sources()
    frame = pd.DataFrame(rows)
    return frame.sort_values(["source_priority", "broker_fill_timestamp", "broker_fill_id"]).reset_index(drop=True)


def runtime_sell_trade_candidates(
    position_lifecycle: pd.DataFrame | list[dict[str, Any]] | None,
) -> pd.DataFrame:
    lifecycle = _frame(position_lifecycle)
    rows: list[dict[str, Any]] = []
    if lifecycle.empty:
        return pd.DataFrame(columns=["position_id", "symbol", "state", "order_id", "fill_id"])

    for _, row in lifecycle.iterrows():
        state = _upper(row.get("state"))
        order_id = _text(row.get("exit_order_id"))
        fill_id = _text(row.get("exit_fill_id"))
        if not (order_id or fill_id or state in {"CLOSED", "PARTIAL_EXIT"}):
            continue
        rows.append(
            {
                "position_id": _text(row.get("position_id")),
                "symbol": _upper(row.get("symbol")),
                "state": state,
                "order_id": order_id,
                "fill_id": fill_id,
            }
        )
    return pd.DataFrame(rows, columns=["position_id", "symbol", "state", "order_id", "fill_id"])


def build_broker_trade_lineage(
    position_lifecycle: pd.DataFrame | list[dict[str, Any]] | None,
    fills: pd.DataFrame | list[dict[str, Any]] | None,
    orders: pd.DataFrame | list[dict[str, Any]] | None = None,
    execution_events: pd.DataFrame | list[dict[str, Any]] | None = None,
    *,
    created_at: str | None = None,
) -> dict[str, pd.DataFrame]:
    created_at = created_at or utc_now_iso()
    candidates = runtime_sell_trade_candidates(position_lifecycle)
    sources = broker_truth_sell_fill_sources(fills, execution_events)
    order_frame = _frame(orders)
    event_frame = _frame(execution_events)
    lineage_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []

    for candidate in candidates.to_dict(orient="records"):
        position_id = _text(candidate.get("position_id"))
        order_id = _text(candidate.get("order_id"))
        fill_id = _text(candidate.get("fill_id"))
        exact_matches = _exact_broker_matches(position_id, order_id, fill_id, sources)
        match_count = int(len(exact_matches))
        if match_count == 1:
            match = exact_matches.iloc[0].to_dict()
            mapping_status = "MAPPED_EXACT_BROKER_TRUTH_SELL_FILL"
            matching_key_type = _text(match.get("matching_key_type"))
        elif match_count > 1:
            match = {}
            mapping_status = "NON_UNIQUE_EXACT_BROKER_TRUTH_SELL_FILL"
            matching_key_type = ""
        else:
            match = {}
            mapping_status = "MISSING_EXACT_BROKER_TRUTH_SELL_FILL"
            matching_key_type = ""

        signal_id = _resolve_signal_id(position_id, order_id, order_frame, event_frame)
        lineage_row = {
            "lineage_id": _lineage_id(position_id, order_id, fill_id, match),
            "position_id": position_id,
            "signal_id": signal_id,
            "order_id": order_id,
            "broker_order_id": _text(match.get("broker_order_id")),
            "fill_id": fill_id,
            "broker_fill_id": _text(match.get("broker_fill_id")),
            "broker_status": _text(match.get("broker_status")),
            "broker_fill_price": match.get("broker_fill_price"),
            "broker_fill_timestamp": _text(match.get("broker_fill_timestamp")),
            "created_at": created_at,
        }
        lineage_rows.append(lineage_row)
        diagnostic_rows.append(
            {
                **lineage_row,
                "symbol": _text(candidate.get("symbol")),
                "state": _text(candidate.get("state")),
                "mapping_status": mapping_status,
                "matching_key_type": matching_key_type,
                "exact_match_count": match_count,
                "matching_policy": MATCHING_POLICY,
                "inferred_matching_used_flag": 0,
                "proximity_fallback_used_flag": 0,
                "broker_truth_source": _text(match.get("broker_truth_source")),
                "broker_truth_source_table": _text(match.get("broker_truth_source_table")),
            }
        )

    lineage = pd.DataFrame(lineage_rows, columns=BROKER_TRADE_LINEAGE_COLUMNS)
    diagnostics = pd.DataFrame(diagnostic_rows)
    summary = summarize_broker_trade_lineage(candidates, sources, lineage, diagnostics)
    return {
        "broker_trade_lineage": lineage,
        "broker_truth_sell_sources": sources,
        "broker_trade_lineage_diagnostics": diagnostics,
        "broker_trade_lineage_summary": summary,
    }


def _exact_broker_matches(
    position_id: str,
    order_id: str,
    fill_id: str,
    sources: pd.DataFrame,
) -> pd.DataFrame:
    if sources.empty:
        return pd.DataFrame()
    parts: list[pd.DataFrame] = []
    if fill_id:
        by_fill = sources.loc[sources["broker_fill_id"].fillna("").astype(str).eq(fill_id)]
        if not by_fill.empty:
            by_fill = by_fill.copy()
            by_fill["matching_key_type"] = "EXACT_FILL_ID"
            parts.append(by_fill)
    if order_id:
        by_order = sources.loc[sources["broker_order_id"].fillna("").astype(str).eq(order_id)]
        if not by_order.empty:
            by_order = by_order.copy()
            by_order["matching_key_type"] = "EXACT_ORDER_ID"
            parts.append(by_order)
    if position_id and "broker_lifecycle_id" in sources.columns:
        by_lifecycle = sources.loc[
            sources["broker_truth_source_table"].fillna("").astype(str).eq("paper_order_execution_events")
            & sources["broker_lifecycle_id"].fillna("").astype(str).eq(position_id)
        ]
        if not by_lifecycle.empty:
            by_lifecycle = by_lifecycle.copy()
            by_lifecycle["matching_key_type"] = "EXACT_BROKER_EVENT_LIFECYCLE_ID"
            parts.append(by_lifecycle)
    if not parts:
        return pd.DataFrame()
    exact = pd.concat(parts, ignore_index=True)
    return exact.drop_duplicates(
        subset=["broker_fill_id", "broker_order_id", "broker_event_id", "broker_truth_source_table"]
    )


def _resolve_signal_id(
    position_id: str,
    order_id: str,
    orders: pd.DataFrame,
    execution_events: pd.DataFrame,
) -> str:
    values: list[str] = []
    if order_id and not execution_events.empty and "order_id" in execution_events.columns:
        matched = execution_events.loc[execution_events["order_id"].fillna("").astype(str).eq(order_id)]
        if "side" in matched.columns:
            matched = matched.loc[matched["side"].fillna("").astype(str).str.upper().eq("SELL")]
        if "decision_id" in matched.columns:
            values.extend(_text(value) for value in matched["decision_id"].tolist())
    if position_id and not execution_events.empty and "lifecycle_id" in execution_events.columns:
        matched = execution_events.loc[execution_events["lifecycle_id"].fillna("").astype(str).eq(position_id)]
        if "side" in matched.columns:
            matched = matched.loc[matched["side"].fillna("").astype(str).str.upper().eq("SELL")]
        if "decision_id" in matched.columns:
            values.extend(_text(value) for value in matched["decision_id"].tolist())
    if order_id and not orders.empty and "order_id" in orders.columns and "intent_key" in orders.columns:
        matched = orders.loc[orders["order_id"].fillna("").astype(str).eq(order_id)]
        values.extend(_text(value) for value in matched["intent_key"].tolist())

    unique: list[str] = []
    for value in values:
        if value and value not in unique:
            unique.append(value)
    if len(unique) == 1:
        return unique[0]
    return ""


def _lineage_id(position_id: str, order_id: str, fill_id: str, match: dict[str, Any]) -> str:
    payload = {
        "position_id": position_id,
        "order_id": order_id,
        "fill_id": fill_id,
        "broker_order_id": _text(match.get("broker_order_id")),
        "broker_fill_id": _text(match.get("broker_fill_id")),
    }
    raw = json.dumps(payload, sort_keys=True)
    return "broker_trade_lineage_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def summarize_broker_trade_lineage(
    candidates: pd.DataFrame | list[dict[str, Any]] | None,
    broker_truth_sources: pd.DataFrame | list[dict[str, Any]] | None,
    lineage: pd.DataFrame | list[dict[str, Any]] | None,
    diagnostics: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> pd.DataFrame:
    candidate_frame = _frame(candidates)
    source_frame = _frame(broker_truth_sources)
    lineage_frame = _frame(lineage)
    diagnostic_frame = _frame(diagnostics)
    runtime_count = int(len(candidate_frame))
    broker_truth_sell_fills = int(len(source_frame))
    lineage_rows = int(len(lineage_frame))
    exact_local_rows = _complete_local_lineage_rows(lineage_frame)
    accepted_broker_fill_ids = {
        _text(value)
        for value in source_frame.get("broker_fill_id", pd.Series(dtype=str)).tolist()
        if _text(value)
    }
    linked_rows = 0
    if not lineage_frame.empty and "broker_fill_id" in lineage_frame.columns and accepted_broker_fill_ids:
        linked_rows = int(
            lineage_frame["broker_fill_id"].fillna("").astype(str).isin(accepted_broker_fill_ids).sum()
        )
    non_unique = 0
    if not diagnostic_frame.empty and "mapping_status" in diagnostic_frame.columns:
        non_unique = int(
            diagnostic_frame["mapping_status"].astype(str).eq("NON_UNIQUE_EXACT_BROKER_TRUTH_SELL_FILL").sum()
        )
    lineage_coverage = _pct(exact_local_rows, runtime_count)
    broker_fill_linkage = _pct(linked_rows, runtime_count)
    missing_broker_fill_count = max(runtime_count - linked_rows, 0)
    acceptance_status = (
        "PASS"
        if broker_truth_sell_fills > 0 and lineage_coverage > 95.0 and broker_fill_linkage > 95.0
        else "FAIL"
    )
    current_status = _current_status(
        broker_truth_sell_fills=broker_truth_sell_fills,
        lineage_coverage=lineage_coverage,
        broker_fill_linkage=broker_fill_linkage,
        acceptance_status=acceptance_status,
    )
    metrics = BrokerTradeLineageMetrics(
        task_id=TASK_ID,
        runtime_sell_trade_count=runtime_count,
        broker_truth_sell_fills=broker_truth_sell_fills,
        lineage_rows=lineage_rows,
        exact_local_lineage_rows=exact_local_rows,
        broker_fill_linked_rows=linked_rows,
        missing_broker_fill_count=missing_broker_fill_count,
        non_unique_exact_match_count=non_unique,
        lineage_coverage=lineage_coverage,
        broker_fill_linkage=broker_fill_linkage,
        current_status=current_status,
        acceptance_status=acceptance_status,
        matching_policy=MATCHING_POLICY,
        inferred_matching_used_flag=0,
        proximity_fallback_used_flag=0,
        real_capital_status="FORBIDDEN",
    )
    return pd.DataFrame([metrics.__dict__])


def _complete_local_lineage_rows(lineage: pd.DataFrame) -> int:
    if lineage.empty:
        return 0
    required = ["position_id", "order_id", "fill_id"]
    if any(column not in lineage.columns for column in required):
        return 0
    mask = pd.Series([True] * len(lineage), index=lineage.index)
    for column in required:
        mask &= lineage[column].fillna("").astype(str).ne("")
    return int(mask.sum())


def _pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 6)


def _current_status(
    *,
    broker_truth_sell_fills: int,
    lineage_coverage: float,
    broker_fill_linkage: float,
    acceptance_status: str,
) -> str:
    if broker_truth_sell_fills == 0:
        return "FAIL_BROKER_TRUTH_SELL_FILLS_ZERO"
    if lineage_coverage <= 95.0:
        return "FAIL_LINEAGE_COVERAGE_BELOW_THRESHOLD"
    if broker_fill_linkage <= 95.0:
        return "FAIL_BROKER_FILL_LINKAGE_BELOW_THRESHOLD"
    if acceptance_status == "PASS":
        return "PASS_BROKER_TRADE_LINEAGE_LINKED"
    return "FAIL_BROKER_TRADE_LINEAGE_NOT_ACCEPTED"
