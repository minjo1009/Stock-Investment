from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd


MATCHING_POLICY = "EXACT_EXIT_ORDER_FILL_OR_EVENT_ID_ONLY"
BROKER_TRUTH_FILL_SOURCES = {
    "ORDER_STATUS",
    "BROKER_ORDER_STATUS",
    "BROKER_ORDER_STATUS_REFRESH",
    "BROKER_EXECUTION_REPORT",
    "EXECUTION_REPORT",
    "BROKER_FILL",
    "BROKER_TRADE_CONFIRM",
    "KIS_ORDER_STATUS",
}
FORBIDDEN_BROKER_TRUTH_SOURCES = {
    "PAPER_RUNTIME_SYNTHETIC_EXIT",
    "POSITION_DELTA_FALLBACK",
    "SHADOW",
    "SYNTHETIC",
    "SIMULATED",
    "BACKTEST",
}


@dataclass(frozen=True)
class ExitMappingMetrics:
    broker_truth_sell_fills: int
    mapped_broker_truth_exits: int
    runtime_exit_count: int
    closed_position_count: int
    exit_fill_linkage_coverage: float
    closed_positions_with_fill: float
    missing_broker_exit_count: int
    acceptance_status: str


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


def is_broker_truth_fill_source(source: object) -> bool:
    source_text = _upper(source)
    if not source_text:
        return False
    if source_text in FORBIDDEN_BROKER_TRUTH_SOURCES:
        return False
    if any(token in source_text for token in FORBIDDEN_BROKER_TRUTH_SOURCES):
        return False
    if source_text in BROKER_TRUTH_FILL_SOURCES:
        return True
    return "BROKER" in source_text or "ORDER_STATUS" in source_text or "EXECUTION_REPORT" in source_text


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


def broker_truth_exit_sources(
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
                    "symbol": _upper(row.get("symbol")),
                    "side": "SELL",
                    "filled_quantity": qty,
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
            extracted_fill_id = _extract_first_fill_id(row.get("raw_response_json"))
            rows.append(
                {
                    "broker_fill_id": extracted_fill_id or event_id,
                    "broker_order_id": order_id,
                    "broker_event_id": event_id,
                    "broker_lifecycle_id": _text(row.get("lifecycle_id")),
                    "symbol": _upper(row.get("symbol")),
                    "side": "SELL",
                    "filled_quantity": qty,
                    "broker_fill_price": _float(row.get("filled_avg_price")),
                    "broker_fill_timestamp": _text(row.get("created_at")),
                    "broker_truth_source": source,
                    "broker_truth_source_table": "paper_order_execution_events",
                    "source_priority": 2,
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "broker_fill_id",
                "broker_order_id",
                "broker_event_id",
                "broker_lifecycle_id",
                "symbol",
                "side",
                "filled_quantity",
                "broker_fill_price",
                "broker_fill_timestamp",
                "broker_truth_source",
                "broker_truth_source_table",
                "source_priority",
            ]
        )
    frame = pd.DataFrame(rows)
    return frame.sort_values(["source_priority", "broker_fill_timestamp", "broker_fill_id"]).reset_index(drop=True)


def map_broker_truth_exits_to_lifecycle(
    position_lifecycle: pd.DataFrame | list[dict[str, Any]] | None,
    broker_truth_exits: pd.DataFrame | list[dict[str, Any]] | None,
) -> pd.DataFrame:
    lifecycle = _frame(position_lifecycle)
    sources = _frame(broker_truth_exits)
    rows: list[dict[str, Any]] = []

    if lifecycle.empty:
        return pd.DataFrame(columns=_mapping_columns())

    if "lifecycle_rowid" not in lifecycle.columns:
        lifecycle = lifecycle.reset_index(drop=False).rename(columns={"index": "lifecycle_rowid"})

    for _, row in lifecycle.iterrows():
        position_id = _text(row.get("position_id"))
        exit_order_id = _text(row.get("exit_order_id"))
        exit_fill_id = _text(row.get("exit_fill_id"))
        state = _upper(row.get("state"))
        has_runtime_exit = bool(exit_order_id or exit_fill_id or state in {"CLOSED", "PARTIAL_EXIT"})
        if not has_runtime_exit:
            continue

        exact_matches = pd.DataFrame()
        match_key_type = ""
        if not sources.empty:
            parts: list[pd.DataFrame] = []
            if exit_fill_id:
                by_fill = sources.loc[sources["broker_fill_id"].astype(str).eq(exit_fill_id)]
                if not by_fill.empty:
                    by_fill = by_fill.copy()
                    by_fill["matching_key_type"] = "EXACT_EXIT_FILL_ID"
                    parts.append(by_fill)
            if exit_order_id:
                by_order = sources.loc[sources["broker_order_id"].astype(str).eq(exit_order_id)]
                if not by_order.empty:
                    by_order = by_order.copy()
                    by_order["matching_key_type"] = "EXACT_EXIT_ORDER_ID"
                    parts.append(by_order)
            if position_id and "broker_lifecycle_id" in sources.columns:
                by_event = sources.loc[
                    sources["broker_truth_source_table"].astype(str).eq("paper_order_execution_events")
                    & sources["broker_lifecycle_id"].astype(str).eq(position_id)
                ]
                if not by_event.empty:
                    by_event = by_event.copy()
                    by_event["matching_key_type"] = "EXACT_BROKER_EVENT_LIFECYCLE_ID"
                    parts.append(by_event)
            if parts:
                exact_matches = pd.concat(parts, ignore_index=True)
                exact_matches = exact_matches.drop_duplicates(
                    subset=["broker_fill_id", "broker_order_id", "broker_event_id", "broker_truth_source_table"]
                )

        match_count = int(len(exact_matches))
        if match_count == 1:
            match = exact_matches.iloc[0].to_dict()
            match_key_type = _text(match.get("matching_key_type"))
            status = "MAPPED_EXACT_BROKER_TRUTH_EXIT"
        elif match_count > 1:
            match = {}
            status = "NON_UNIQUE_EXACT_BROKER_TRUTH_EXIT_MATCH"
        else:
            match = {}
            status = "MISSING_EXACT_BROKER_TRUTH_EXIT"

        rows.append(
            {
                "lifecycle_rowid": row.get("lifecycle_rowid"),
                "position_id": position_id,
                "symbol": _upper(row.get("symbol")),
                "state": state,
                "exit_order_id": exit_order_id,
                "exit_fill_id": exit_fill_id,
                "broker_order_id": _text(match.get("broker_order_id")),
                "broker_fill_id": _text(match.get("broker_fill_id")),
                "broker_event_id": _text(match.get("broker_event_id")),
                "broker_fill_timestamp": _text(match.get("broker_fill_timestamp")),
                "broker_fill_price": match.get("broker_fill_price"),
                "broker_truth_source": _text(match.get("broker_truth_source")),
                "broker_truth_source_table": _text(match.get("broker_truth_source_table")),
                "mapping_status": status,
                "matching_key_type": match_key_type,
                "exact_match_count": match_count,
                "matching_policy": MATCHING_POLICY,
                "proximity_fallback_used_flag": 0,
            }
        )

    return pd.DataFrame(rows, columns=_mapping_columns())


def summarize_exit_mapping(
    position_lifecycle: pd.DataFrame | list[dict[str, Any]] | None,
    broker_truth_exits: pd.DataFrame | list[dict[str, Any]] | None,
    mapping: pd.DataFrame | list[dict[str, Any]] | None,
    *,
    runtime_exit_count: int | None = None,
) -> ExitMappingMetrics:
    lifecycle = _frame(position_lifecycle)
    sources = _frame(broker_truth_exits)
    mapped = _frame(mapping)
    broker_truth_sell_fills = int(len(sources))
    mapped_count = (
        int(mapped["mapping_status"].astype(str).eq("MAPPED_EXACT_BROKER_TRUTH_EXIT").sum())
        if not mapped.empty and "mapping_status" in mapped.columns
        else 0
    )
    if runtime_exit_count is None:
        runtime_exit_count = _runtime_exit_count_from_lifecycle(lifecycle)
    closed_count = _closed_position_count(lifecycle)
    closed_with_fill = _closed_positions_with_broker_fill(lifecycle, mapped)
    linkage = _pct(mapped_count, int(runtime_exit_count))
    closed_with_fill_pct = _pct(closed_with_fill, closed_count)
    missing = max(int(runtime_exit_count) - mapped_count, 0)
    acceptance = (
        "PASS"
        if broker_truth_sell_fills > 0 and linkage > 95.0 and closed_with_fill_pct > 95.0
        else "FAIL"
    )
    return ExitMappingMetrics(
        broker_truth_sell_fills=broker_truth_sell_fills,
        mapped_broker_truth_exits=mapped_count,
        runtime_exit_count=int(runtime_exit_count),
        closed_position_count=closed_count,
        exit_fill_linkage_coverage=linkage,
        closed_positions_with_fill=closed_with_fill_pct,
        missing_broker_exit_count=missing,
        acceptance_status=acceptance,
    )


def _runtime_exit_count_from_lifecycle(lifecycle: pd.DataFrame) -> int:
    if lifecycle.empty:
        return 0
    exit_fill = lifecycle.get("exit_fill_id", pd.Series([""] * len(lifecycle), index=lifecycle.index)).fillna("").astype(str)
    state = lifecycle.get("state", pd.Series([""] * len(lifecycle), index=lifecycle.index)).fillna("").astype(str).str.upper()
    return int((exit_fill.ne("") | state.isin({"CLOSED", "PARTIAL_EXIT"})).sum())


def _closed_position_count(lifecycle: pd.DataFrame) -> int:
    if lifecycle.empty or "state" not in lifecycle.columns:
        return 0
    return int(lifecycle["state"].fillna("").astype(str).str.upper().eq("CLOSED").sum())


def _closed_positions_with_broker_fill(lifecycle: pd.DataFrame, mapping: pd.DataFrame) -> int:
    if lifecycle.empty:
        return 0
    existing = 0
    if "broker_fill_id" in lifecycle.columns and "state" in lifecycle.columns:
        state = lifecycle["state"].fillna("").astype(str).str.upper()
        fill = lifecycle["broker_fill_id"].fillna("").astype(str)
        existing = int((state.eq("CLOSED") & fill.ne("")).sum())
    if mapping.empty or "mapping_status" not in mapping.columns:
        return existing
    mapped_positions = mapping.loc[
        mapping["state"].fillna("").astype(str).str.upper().eq("CLOSED")
        & mapping["mapping_status"].astype(str).eq("MAPPED_EXACT_BROKER_TRUTH_EXIT"),
        "position_id",
    ]
    return max(existing, int(mapped_positions.nunique()))


def _pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 6)


def _mapping_columns() -> list[str]:
    return [
        "lifecycle_rowid",
        "position_id",
        "symbol",
        "state",
        "exit_order_id",
        "exit_fill_id",
        "broker_order_id",
        "broker_fill_id",
        "broker_event_id",
        "broker_fill_timestamp",
        "broker_fill_price",
        "broker_truth_source",
        "broker_truth_source_table",
        "mapping_status",
        "matching_key_type",
        "exact_match_count",
        "matching_policy",
        "proximity_fallback_used_flag",
    ]
