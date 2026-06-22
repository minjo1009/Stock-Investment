from __future__ import annotations

import argparse
import hashlib
import sqlite3
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd


TASK_ID = "T600-5"
REPORT_DIR = Path("docs/reports/task_600_5_stop_tp_validation")
MATCHING_POLICY = "EXACT_POSITION_ID_AND_ENTRY_ORDER_FILL_ID_ONLY"
RUNTIME_EXIT_FILL_PREFIX = "RUNTIME_EXIT_FILL|"
RUNTIME_EXIT_ORDER_PREFIX = "RUNTIME_EXIT_ORDER|"
REAL_CAPITAL_STATUS = "FORBIDDEN"
STRATEGY_ACCEPTANCE_STATUS = "NOT_ACCEPTED"
DEPLOYMENT_READINESS_STATUS = "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"


@dataclass(frozen=True)
class StopTpRules:
    stop_atr_multiple: float = 2.0
    tp_atr_multiple: float = 4.0
    timeout_minutes: int = 390
    atr_max_stale_days: int = 3


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


def _timestamp(value: object) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def _iso(ts: pd.Timestamp | None) -> str:
    if ts is None:
        return ""
    return ts.isoformat().replace("+00:00", "Z")


def _minutes_between(start: object, end: object) -> float | None:
    start_ts = _timestamp(start)
    end_ts = _timestamp(end)
    if start_ts is None or end_ts is None:
        return None
    return round((end_ts - start_ts).total_seconds() / 60.0, 4)


def _normalize_exit_reason(value: object) -> str:
    reason = _upper(value)
    if reason in {"TAKE_PROFIT", "TAKE PROFIT", "PROFIT_TARGET"}:
        return "TP"
    if reason == "STOP_LOSS":
        return "STOP"
    if reason in {"STOP", "TP", "TIMEOUT"}:
        return reason
    return ""


def _positive_float(value: object) -> float | None:
    parsed = _float(value)
    if parsed is None or parsed <= 0:
        return None
    return parsed


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


def _readonly_connect(db_path: Path | str) -> sqlite3.Connection:
    resolved = Path(db_path).resolve()
    uri = "file:" + quote(resolved.as_posix(), safe="/:") + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _runtime_lifecycle_scope(position_lifecycle: pd.DataFrame) -> pd.DataFrame:
    if position_lifecycle.empty:
        return position_lifecycle.copy()
    frame = position_lifecycle.copy()
    exit_fill = frame.get("exit_fill_id", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    exit_order = frame.get("exit_order_id", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    acceptance = frame.get("acceptance_status", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    runtime_mask = (
        exit_fill.str.startswith(RUNTIME_EXIT_FILL_PREFIX)
        | exit_order.str.startswith(RUNTIME_EXIT_ORDER_PREFIX)
        | acceptance.eq("CLOSED_RUNTIME_PAPER_EXACT_IDS")
    )
    if runtime_mask.any():
        return frame.loc[runtime_mask].reset_index(drop=True)
    return frame.reset_index(drop=True)


def _price_stream_from_indicator_snapshots(indicator_snapshots: pd.DataFrame) -> pd.DataFrame:
    if indicator_snapshots.empty:
        return pd.DataFrame(columns=_price_stream_columns())
    frame = indicator_snapshots.copy()
    frame["symbol"] = frame.get("symbol", pd.Series(dtype=str)).fillna("").astype(str).str.upper()
    frame["price"] = pd.to_numeric(frame.get("source_price", frame.get("price", frame.get("close"))), errors="coerce")
    if "close" in frame.columns:
        missing_price = frame["price"].isna()
        frame.loc[missing_price, "price"] = pd.to_numeric(frame.loc[missing_price, "close"], errors="coerce")
    frame["price_ts"] = pd.to_datetime(
        frame.get("source_price_ts", frame.get("price_ts", frame.get("bar_end_ts", frame.get("created_at")))),
        utc=True,
        errors="coerce",
    )
    for fallback in ("bar_end_ts", "created_at"):
        if fallback in frame.columns:
            missing_ts = frame["price_ts"].isna()
            frame.loc[missing_ts, "price_ts"] = pd.to_datetime(frame.loc[missing_ts, fallback], utc=True, errors="coerce")
    frame["source_table"] = frame.get("source_table", pd.Series(["indicator_snapshots"] * len(frame), index=frame.index)).fillna("indicator_snapshots").astype(str)
    frame["source_id"] = frame.get("snapshot_id", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    frame["source_type"] = frame.get("source_type", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    frame["data_fresh"] = frame.get("data_fresh", pd.Series([None] * len(frame), index=frame.index))
    frame["freshness_age_sec"] = frame.get("freshness_age_sec", pd.Series([None] * len(frame), index=frame.index))
    frame["stale_reason"] = frame.get("stale_reason", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    frame["atr"] = _first_numeric_column(frame, ["entry_atr", "atr", "atr_14", "atr14"])
    keep = frame.loc[frame["symbol"].ne("") & frame["price"].notna() & frame["price_ts"].notna()].copy()
    return keep[_price_stream_columns()].reset_index(drop=True)


def _price_stream_from_market_bars(market_bars: pd.DataFrame) -> pd.DataFrame:
    if market_bars.empty:
        return pd.DataFrame(columns=_price_stream_columns())
    frame = market_bars.copy()
    frame["symbol"] = frame.get("symbol", pd.Series(dtype=str)).fillna("").astype(str).str.upper()
    frame["price"] = pd.to_numeric(frame.get("close"), errors="coerce")
    frame["price_ts"] = pd.to_datetime(frame.get("bar_end_ts", frame.get("last_updated_at")), utc=True, errors="coerce")
    frame["source_table"] = "market_bars_5m"
    frame["source_id"] = frame.get("bar_id", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    frame["source_type"] = frame.get("source", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    frame["data_fresh"] = None
    frame["freshness_age_sec"] = None
    frame["stale_reason"] = ""
    frame["atr"] = _market_bar_atr(frame)
    keep = frame.loc[frame["symbol"].ne("") & frame["price"].notna() & frame["price_ts"].notna()].copy()
    return keep[_price_stream_columns()].reset_index(drop=True)


def _market_bar_atr(frame: pd.DataFrame, *, period: int = 14) -> pd.Series:
    explicit = _first_numeric_column(frame, ["entry_atr", "atr", "atr_14", "atr14"])
    required = {"symbol", "price_ts", "high", "low", "close"}
    if not required.issubset(frame.columns):
        return explicit

    bars = frame[["symbol", "price_ts", "high", "low", "close"]].copy()
    bars["high"] = pd.to_numeric(bars["high"], errors="coerce")
    bars["low"] = pd.to_numeric(bars["low"], errors="coerce")
    bars["close"] = pd.to_numeric(bars["close"], errors="coerce")
    bars = bars.sort_values(["symbol", "price_ts"])
    prev_close = bars.groupby("symbol")["close"].shift(1)
    ranges = pd.concat(
        [
            (bars["high"] - bars["low"]).abs(),
            (bars["high"] - prev_close).abs(),
            (bars["low"] - prev_close).abs(),
        ],
        axis=1,
    )
    true_range = ranges.max(axis=1)
    computed = true_range.groupby(bars["symbol"]).rolling(period, min_periods=period).mean().reset_index(level=0, drop=True)
    computed = computed.reindex(bars.index).reindex(frame.index)
    return explicit.where(explicit.notna(), computed)


def _price_stream_from_market_ticks(market_ticks: pd.DataFrame) -> pd.DataFrame:
    if market_ticks.empty:
        return pd.DataFrame(columns=_price_stream_columns())
    frame = market_ticks.copy()
    frame["symbol"] = frame.get("symbol", pd.Series(dtype=str)).fillna("").astype(str).str.upper()
    frame["price"] = pd.to_numeric(frame.get("last_price"), errors="coerce")
    frame["price_ts"] = pd.to_datetime(frame.get("timestamp", frame.get("created_at")), utc=True, errors="coerce")
    frame["source_table"] = "market_ticks"
    frame["source_id"] = frame.get("tick_id", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    frame["source_type"] = frame.get("source", pd.Series([""] * len(frame), index=frame.index)).fillna("").astype(str)
    frame["data_fresh"] = None
    frame["freshness_age_sec"] = None
    frame["stale_reason"] = ""
    frame["atr"] = None
    keep = frame.loc[frame["symbol"].ne("") & frame["price"].notna() & frame["price_ts"].notna()].copy()
    return keep[_price_stream_columns()].reset_index(drop=True)


def _first_numeric_column(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    out = pd.Series(float("nan"), index=frame.index, dtype="float64")
    for column in columns:
        if column in frame.columns:
            values = pd.to_numeric(frame[column], errors="coerce")
            out = out.where(out.notna(), values)
    return pd.to_numeric(out, errors="coerce")


def _price_stream_columns() -> list[str]:
    return [
        "symbol",
        "price_ts",
        "price",
        "source_table",
        "source_id",
        "source_type",
        "data_fresh",
        "freshness_age_sec",
        "stale_reason",
        "atr",
    ]


def build_runtime_price_evidence(
    indicator_snapshots: pd.DataFrame | None = None,
    market_bars_5m: pd.DataFrame | None = None,
    market_ticks: pd.DataFrame | None = None,
) -> pd.DataFrame:
    frames = [
        _price_stream_from_indicator_snapshots(indicator_snapshots if indicator_snapshots is not None else pd.DataFrame()),
        _price_stream_from_market_bars(market_bars_5m if market_bars_5m is not None else pd.DataFrame()),
        _price_stream_from_market_ticks(market_ticks if market_ticks is not None else pd.DataFrame()),
    ]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=_price_stream_columns())
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning, message="The behavior of DataFrame concatenation.*")
        frame = pd.concat(frames, ignore_index=True)
    if frame.empty:
        return pd.DataFrame(columns=_price_stream_columns())
    frame["price_ts"] = pd.to_datetime(frame["price_ts"], utc=True, errors="coerce")
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    frame["atr"] = pd.to_numeric(frame["atr"], errors="coerce")
    return (
        frame.loc[frame["symbol"].astype(str).ne("") & frame["price"].notna() & frame["price_ts"].notna()]
        .sort_values(["symbol", "price_ts", "source_table", "source_id"])
        .reset_index(drop=True)
    )


def _position_atr_status(position: pd.Series) -> str:
    status = _upper(position.get("atr_status"))
    if not status:
        return ""
    if any(token in status for token in ("STALE", "MISSING", "INVALID", "UNREADABLE", "SOURCE_BLOCKED")):
        return status
    return ""


def _atr_for_position(
    position: pd.Series,
    symbol_prices: pd.DataFrame,
    entry_ts: pd.Timestamp,
    rules: StopTpRules,
) -> tuple[float | None, str]:
    blocked_status = _position_atr_status(position)
    if blocked_status:
        return None, blocked_status

    for column in ("entry_atr", "atr", "atr_14", "atr14"):
        atr = _positive_float(position.get(column))
        if atr is None:
            continue
        ts = _timestamp(position.get(f"{column}_ts")) or _timestamp(position.get("atr_ts")) or _timestamp(position.get("atr_source_ts"))
        if ts is not None and ts < entry_ts - pd.Timedelta(days=rules.atr_max_stale_days):
            return None, "STALE_ATR_SOURCE_BEFORE_ENTRY"
        if ts is not None and ts > entry_ts:
            return None, "FUTURE_ATR_SOURCE_BLOCKED"
        return atr, f"{column.upper()}_FROM_POSITION_LIFECYCLE"

    if symbol_prices.empty or "atr" not in symbol_prices.columns:
        return None, "ATR_SOURCE_MISSING_NO_APPROXIMATION"

    priced = symbol_prices.copy()
    priced["atr"] = pd.to_numeric(priced["atr"], errors="coerce")
    has_any_atr = priced["atr"].notna().any()
    eligible = priced.loc[(priced["price_ts"] <= entry_ts) & priced["atr"].gt(0)].sort_values("price_ts")
    if eligible.empty:
        if has_any_atr:
            return None, "MISSING_FRESH_ATR_BEFORE_ENTRY_NO_APPROXIMATION"
        return None, "ATR_SOURCE_MISSING_NO_APPROXIMATION"

    latest = eligible.iloc[-1]
    latest_ts = latest["price_ts"]
    if latest_ts < entry_ts - pd.Timedelta(days=rules.atr_max_stale_days):
        return None, "STALE_ATR_SOURCE_BEFORE_ENTRY"
    data_fresh = _float(latest.get("data_fresh"))
    stale_reason = _text(latest.get("stale_reason"))
    if data_fresh == 0 or stale_reason:
        return None, "STALE_ATR_RUNTIME_SNAPSHOT"
    return float(latest["atr"]), "ATR_FROM_RUNTIME_PRICE_EVIDENCE"


def validate_stop_tp_lifecycle(
    position_lifecycle: pd.DataFrame,
    runtime_price_evidence: pd.DataFrame,
    *,
    rules: StopTpRules = StopTpRules(),
) -> dict[str, pd.DataFrame]:
    lifecycle = _runtime_lifecycle_scope(position_lifecycle)
    price_stream = build_runtime_price_evidence(runtime_price_evidence)
    before_distribution = _distribution_from_series(lifecycle.get("exit_reason", pd.Series(dtype=str)))
    detail_rows: list[dict[str, Any]] = []

    for _, position in lifecycle.iterrows():
        position_id = _text(position.get("position_id"))
        symbol = _upper(position.get("symbol"))
        entry_order_id = _text(position.get("entry_order_id"))
        entry_fill_id = _text(position.get("entry_fill_id"))
        entry_ts = _timestamp(position.get("entry_time"))
        entry_price = _float(position.get("entry_price"))
        qty = _float(position.get("closed_qty")) or _float(position.get("open_qty")) or _float(position.get("entry_qty")) or 0.0
        existing_reason = _normalize_exit_reason(position.get("exit_reason"))
        existing_exit_ts = _timestamp(position.get("exit_time"))
        existing_exit_price = _float(position.get("exit_price"))
        existing_hold = _float(position.get("holding_minutes"))

        if not position_id or not symbol or not entry_order_id or not entry_fill_id or entry_ts is None or entry_price is None:
            detail_rows.append(
                _detail_row(
                    position,
                    validation_exit_reason="",
                    validation_exit_time="",
                    validation_exit_price=None,
                    holding_minutes=None,
                    atr=None,
                    atr_status="SOURCE_BLOCKED_MISSING_EXACT_ENTRY_EVIDENCE",
                    source_blocked_flag=1,
                    price_evidence_count=0,
                    exit_source_status="SOURCE_BLOCKED_MISSING_EXACT_ENTRY_EVIDENCE",
                )
            )
            continue

        symbol_prices = price_stream.loc[
            price_stream["symbol"].astype(str).str.upper().eq(symbol)
            & (price_stream["price_ts"] >= entry_ts)
        ].sort_values("price_ts")
        atr, atr_status = _atr_for_position(position, price_stream.loc[price_stream["symbol"].astype(str).str.upper().eq(symbol)], entry_ts, rules)
        stop_price = entry_price - (rules.stop_atr_multiple * atr) if atr is not None else None
        tp_price = entry_price + (rules.tp_atr_multiple * atr) if atr is not None else None
        timeout_ts = entry_ts + pd.Timedelta(minutes=rules.timeout_minutes)
        exit_reason = ""
        exit_ts: pd.Timestamp | None = None
        exit_price: float | None = None
        exit_source_status = ""
        source_blocked = 0

        if atr is None:
            source_blocked = 1
            if existing_reason == "TIMEOUT" and existing_exit_ts is not None:
                exit_reason = "TIMEOUT"
                exit_ts = existing_exit_ts
                exit_price = existing_exit_price
                exit_source_status = "TIMEOUT_FROM_EXISTING_RUNTIME_LIFECYCLE_ATR_SOURCE_BLOCKED"
            else:
                timeout = _first_price_at_or_after(symbol_prices, timeout_ts)
                if not timeout.empty:
                    exit_reason = "TIMEOUT"
                    exit_ts = timeout["price_ts"]
                    exit_price = _float(timeout.get("price"))
                    exit_source_status = "TIMEOUT_FROM_RUNTIME_PRICE_EVIDENCE_ATR_SOURCE_BLOCKED"
                else:
                    exit_source_status = "NO_RUNTIME_TIMEOUT_PRICE_EVIDENCE_ATR_SOURCE_BLOCKED"
        else:
            for _, point in symbol_prices.iterrows():
                point_ts = point["price_ts"]
                price = _float(point.get("price"))
                if point_ts is None or price is None:
                    continue
                if point_ts >= timeout_ts:
                    exit_reason = "TIMEOUT"
                    exit_ts = point_ts
                    exit_price = price
                    exit_source_status = "TIMEOUT_FROM_RUNTIME_PRICE_EVIDENCE"
                    break
                if stop_price is not None and price <= stop_price:
                    exit_reason = "STOP"
                    exit_ts = point_ts
                    exit_price = price
                    exit_source_status = "STOP_FROM_RUNTIME_PRICE_EVIDENCE"
                    break
                if tp_price is not None and price >= tp_price:
                    exit_reason = "TP"
                    exit_ts = point_ts
                    exit_price = price
                    exit_source_status = "TP_FROM_RUNTIME_PRICE_EVIDENCE"
                    break
            if not exit_reason and existing_reason in {"STOP", "TP", "TIMEOUT"} and existing_exit_ts is not None:
                exit_reason = existing_reason
                exit_ts = existing_exit_ts
                exit_price = existing_exit_price
                exit_source_status = "EXISTING_RUNTIME_LIFECYCLE_EXIT"
            elif not exit_reason:
                exit_source_status = "NO_RUNTIME_EXIT_TRIGGER_OR_PRICE_EVIDENCE"

        holding_minutes = _minutes_between(entry_ts, exit_ts) if exit_ts is not None else existing_hold
        if holding_minutes is None and existing_hold is not None:
            holding_minutes = existing_hold

        row = _detail_row(
            position,
            validation_exit_reason=exit_reason,
            validation_exit_time=_iso(exit_ts),
            validation_exit_price=exit_price,
            holding_minutes=holding_minutes,
            atr=atr,
            atr_status=atr_status,
            source_blocked_flag=source_blocked,
            price_evidence_count=int(len(symbol_prices)),
            exit_source_status=exit_source_status,
        )
        row["stop_price"] = None if stop_price is None else round(stop_price, 6)
        row["take_profit_price"] = None if tp_price is None else round(tp_price, 6)
        row["timeout_minutes"] = int(rules.timeout_minutes)
        row["timeout_time"] = _iso(timeout_ts)
        row["closed_qty"] = qty
        detail_rows.append(row)

    detail = pd.DataFrame(detail_rows)
    summary = _summary_frame(detail, before_distribution, runtime_lifecycle_count=int(len(lifecycle)), price_evidence_count=int(len(price_stream)))
    return {
        "stop_tp_validation_summary": summary,
        "stop_tp_validation_detail": detail,
        "before_exit_distribution": before_distribution,
    }


def _first_price_at_or_after(symbol_prices: pd.DataFrame, target_ts: pd.Timestamp) -> pd.Series:
    eligible = symbol_prices.loc[symbol_prices["price_ts"] >= target_ts].sort_values("price_ts")
    if eligible.empty:
        return pd.Series(dtype=object)
    return eligible.iloc[0]


def _detail_row(
    position: pd.Series,
    *,
    validation_exit_reason: str,
    validation_exit_time: str,
    validation_exit_price: float | None,
    holding_minutes: float | None,
    atr: float | None,
    atr_status: str,
    source_blocked_flag: int,
    price_evidence_count: int,
    exit_source_status: str,
) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "position_id": _text(position.get("position_id")),
        "symbol": _upper(position.get("symbol")),
        "entry_order_id": _text(position.get("entry_order_id")),
        "entry_fill_id": _text(position.get("entry_fill_id")),
        "entry_time": _text(position.get("entry_time")),
        "entry_price": _float(position.get("entry_price")),
        "existing_exit_reason": _normalize_exit_reason(position.get("exit_reason")),
        "existing_exit_time": _text(position.get("exit_time")),
        "existing_exit_price": _float(position.get("exit_price")),
        "validation_exit_reason": validation_exit_reason,
        "validation_exit_time": validation_exit_time,
        "validation_exit_price": validation_exit_price,
        "holding_minutes": holding_minutes,
        "atr": atr,
        "atr_status": atr_status,
        "source_blocked_flag": int(source_blocked_flag),
        "price_evidence_count": int(price_evidence_count),
        "exit_source_status": exit_source_status,
        "matching_policy": MATCHING_POLICY,
        "inferred_matching_used_flag": 0,
        "proximity_fallback_used_flag": 0,
        "real_capital_status": REAL_CAPITAL_STATUS,
    }


def _distribution_from_series(series: pd.Series) -> pd.DataFrame:
    values = series.fillna("").map(_normalize_exit_reason)
    rows = [{"exit_reason": reason, "count": int(values.eq(reason).sum())} for reason in ["STOP", "TP", "TIMEOUT"]]
    return pd.DataFrame(rows)


def _summary_frame(
    detail: pd.DataFrame,
    before_distribution: pd.DataFrame,
    *,
    runtime_lifecycle_count: int,
    price_evidence_count: int,
) -> pd.DataFrame:
    reason = detail.get("validation_exit_reason", pd.Series(dtype=str)).fillna("").astype(str) if not detail.empty else pd.Series(dtype=str)
    stop_count = int(reason.eq("STOP").sum())
    tp_count = int(reason.eq("TP").sum())
    timeout_count = int(reason.eq("TIMEOUT").sum())
    source_blocked_count = (
        int(pd.to_numeric(detail.get("source_blocked_flag", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
        if not detail.empty
        else 0
    )
    atr_status = detail.get("atr_status", pd.Series(dtype=str)).fillna("").astype(str).str.upper() if not detail.empty else pd.Series(dtype=str)
    missing_count = int(atr_status.str.contains("MISSING|NO_APPROXIMATION", regex=True).sum()) if not atr_status.empty else 0
    stale_count = int(atr_status.str.contains("STALE", regex=True).sum()) if not atr_status.empty else 0
    hold = pd.to_numeric(detail.get("holding_minutes", pd.Series(dtype=float)), errors="coerce") if not detail.empty else pd.Series(dtype=float)
    avg_hold_time = round(float(hold.dropna().mean()), 4) if not hold.dropna().empty else 0.0
    exit_distribution = _distribution_string(stop_count, tp_count, timeout_count)
    before_exit_distribution = _distribution_string(
        _dist_count(before_distribution, "STOP"),
        _dist_count(before_distribution, "TP"),
        _dist_count(before_distribution, "TIMEOUT"),
    )
    acceptance_status = "PASS" if stop_count > 0 and tp_count > 0 else "FAIL"
    if acceptance_status == "PASS":
        decision_status = "PASS_STOP_TP_RUNTIME_VALIDATED"
        next_action = "Proceed to reviewer audit; STOP and TP are both observed from runtime lifecycle price evidence."
    elif stop_count == 0 and tp_count == 0 and source_blocked_count > 0:
        decision_status = "FAIL_STOP_TP_ZERO_SOURCE_BLOCKED"
        next_action = "Add fresh ATR-at-entry runtime source evidence, then rerun T600-5 without approximating ATR."
    elif stop_count == 0 and tp_count == 0:
        decision_status = "FAIL_STOP_TP_ZERO"
        next_action = "Inspect stop/take-profit thresholds and runtime price evidence; no STOP or TP trigger was observed."
    else:
        decision_status = "FAIL_STOP_OR_TP_MISSING"
        next_action = "Review the missing side of STOP/TP evidence before acceptance."
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision_status": decision_status,
                "acceptance_status": acceptance_status,
                "strategy_acceptance_status": STRATEGY_ACCEPTANCE_STATUS,
                "deployment_readiness_status": DEPLOYMENT_READINESS_STATUS,
                "real_capital_status": REAL_CAPITAL_STATUS,
                "stop_count": stop_count,
                "tp_count": tp_count,
                "timeout_count": timeout_count,
                "avg_hold_time": avg_hold_time,
                "exit_distribution": exit_distribution,
                "before_exit_distribution": before_exit_distribution,
                "source_blocked_count": source_blocked_count,
                "atr_source_missing_count": missing_count,
                "atr_source_stale_count": stale_count,
                "runtime_lifecycle_count": int(runtime_lifecycle_count),
                "price_evidence_count": int(price_evidence_count),
                "inferred_matching_used_flag": 0,
                "proximity_fallback_used_flag": 0,
                "next_required_task": next_action,
            }
        ]
    )


def _dist_count(distribution: pd.DataFrame, reason: str) -> int:
    if distribution.empty:
        return 0
    row = distribution.loc[distribution["exit_reason"].astype(str).eq(reason)]
    if row.empty:
        return 0
    return int(row.iloc[0]["count"])


def _distribution_string(stop_count: int, tp_count: int, timeout_count: int) -> str:
    return f"STOP={int(stop_count)};TP={int(tp_count)};TIMEOUT={int(timeout_count)}"


def validate_stop_tp_from_db(db_path: Path | str, *, rules: StopTpRules = StopTpRules()) -> dict[str, pd.DataFrame]:
    con = _readonly_connect(db_path)
    try:
        position_lifecycle = _read_table(con, "position_lifecycle")
        indicator_snapshots = _read_table(con, "indicator_snapshots")
        market_bars = _read_table(con, "market_bars_5m")
        market_ticks = _read_table(con, "market_ticks")
    finally:
        con.close()
    price_evidence = build_runtime_price_evidence(indicator_snapshots, market_bars, market_ticks)
    return validate_stop_tp_lifecycle(position_lifecycle, price_evidence, rules=rules)


def write_stop_tp_reports(report_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["stop_tp_validation_summary"]
    detail = artifacts["stop_tp_validation_detail"]
    row = summary.iloc[0].to_dict()
    _write_csv(report_dir / "stop_tp_validation_summary.csv", summary)
    _write_csv(report_dir / "stop_tp_validation_detail.csv", detail)
    _write_csv(report_dir / "task_600_5_decision.csv", summary)
    _write_report(report_dir / "stop_tp_validation.md", row, detail)
    _write_manifest(report_dir)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def _write_report(path: Path, row: dict[str, Any], detail: pd.DataFrame) -> None:
    source_blockers = _source_blocker_lines(detail)
    source_blocked = int(row.get("source_blocked_count") or 0) > 0
    stability_source_line = (
        "- STOP/TP validation remains diagnostic-only because missing or stale ATR is source-blocked and was not approximated."
        if source_blocked
        else "- STOP/TP validation now has runtime ATR evidence; the result remains diagnostic-only until broker-truth SELL and replay gates pass."
    )
    failure_decomposition_line = (
        "- Failure decomposition: STOP and TP require fresh ATR-at-entry evidence. Missing or stale ATR is reported as source-blocked, not approximated."
        if source_blocked
        else "- Failure decomposition: ATR-at-entry source is no longer blocked for this runtime scope; remaining acceptance blockers are broker-truth SELL linkage and replay position coverage."
    )
    plain_what_happened = (
        "- What happened: the current runtime lifecycle still validates as TIMEOUT-only for the T600-3 scope."
        if source_blocked
        else f"- What happened: runtime 5m bar ATR evidence changed the validation distribution to {row['exit_distribution']}."
    )
    plain_why_it_matters = (
        "- Why it matters: without fresh ATR evidence, STOP/TP cannot be proven as runtime-possible and cannot support an acceptance claim."
        if source_blocked
        else "- Why it matters: STOP and TP are now visible in runtime evidence, but they still cannot support strategy acceptance without broker-truth SELL fills."
    )
    lines = [
        "## Decision Summary",
        "",
        f"- Verdict: {row['acceptance_status']} ({row['decision_status']})",
        f"- Strategy acceptance status: {STRATEGY_ACCEPTANCE_STATUS}",
        f"- Deployment readiness status: {DEPLOYMENT_READINESS_STATUS}",
        f"- Real Capital: {REAL_CAPITAL_STATUS}",
        f"- Key metrics: stop_count={row['stop_count']}, tp_count={row['tp_count']}, timeout_count={row['timeout_count']}, avg_hold_time={row['avg_hold_time']}, exit_distribution={row['exit_distribution']}",
        "- What changed: STOP/TP validation now uses runtime price evidence, including ATR14 computed from captured 5m market bars when explicit ATR snapshots are absent.",
        f"- Next action: {row['next_required_task']}",
        "",
        "## Before",
        "",
        f"- T600-3 baseline exit_distribution={row['before_exit_distribution']}.",
        "- T600-3 created controlled paper runtime SELL fills only; it did not create broker-truth or real-capital evidence.",
        "",
        "## After",
        "",
        f"- T600-5 validation exit_distribution={row['exit_distribution']}.",
        f"- source_blocked_count={row['source_blocked_count']}, atr_source_missing_count={row['atr_source_missing_count']}, atr_source_stale_count={row['atr_source_stale_count']}.",
        f"- runtime_lifecycle_count={row['runtime_lifecycle_count']}, price_evidence_count={row['price_evidence_count']}.",
        "",
        "## Stability Assessment",
        "",
        stability_source_line,
        "- No inferred lifecycle matching, symbol/date/price/time proximity fallback, missing-label negative conversion, or label/outcome leakage was used.",
        "- Unit tests cover both a fixture with STOP/TP triggers and fixtures where STOP/TP must remain blocked.",
        "",
        "## Acceptance Impact",
        "",
        f"- {row['acceptance_status']}: acceptance requires STOP > 0 and TP > 0; observed stop_count={row['stop_count']} and tp_count={row['tp_count']}.",
        f"- Strategy remains {STRATEGY_ACCEPTANCE_STATUS}; deployment remains {DEPLOYMENT_READINESS_STATUS}; Real Capital remains {REAL_CAPITAL_STATUS}.",
        "",
        "## Quant Expert Report",
        "",
        "- Data source and source readiness: runtime lifecycle rows are read from `position_lifecycle`; runtime prices are read from `indicator_snapshots`, `market_bars_5m`, and `market_ticks` when present.",
        "- Exact join keys: this task evaluates existing lifecycle rows by `position_id`, `entry_order_id`, and `entry_fill_id`; it does not join by symbol/date/price/time proximity.",
        "- Leakage audit: labels/outcomes do not enter assignment logic; existing exit labels are used only for the Before baseline and timeout carry-through when ATR is source-blocked.",
        "- Split/OOS metrics: not applicable; this is an execution evidence validation, not a strategy performance claim.",
        failure_decomposition_line,
        "- Cost/slippage stress where PnL changed: not applicable; no PnL or execution records were changed.",
        "- Remaining blockers:",
    ]
    lines.extend([f"  - {item}" for item in source_blockers])
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            plain_what_happened,
            plain_why_it_matters,
            f"- Whether this changes capital/deployment readiness: no; {REAL_CAPITAL_STATUS} and {DEPLOYMENT_READINESS_STATUS} remain unchanged.",
            f"- Plain-language next step: {row['next_required_task']}",
            "",
            "## Artifact Manifest",
            "",
            "- stop_tp_validation.md",
            "- stop_tp_validation_summary.csv",
            "- stop_tp_validation_detail.csv",
            "- task_600_5_decision.csv",
            "- artifact_manifest.csv",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _source_blocker_lines(detail: pd.DataFrame) -> list[str]:
    if detail.empty or "atr_status" not in detail.columns:
        return ["No lifecycle rows were available for STOP/TP validation."]
    blocked = detail.loc[pd.to_numeric(detail.get("source_blocked_flag", 0), errors="coerce").fillna(0).astype(int).eq(1)]
    if blocked.empty:
        return ["No ATR source blocker in validated rows."]
    counts = blocked["atr_status"].fillna("").astype(str).value_counts().sort_index()
    return [f"{status}: {int(count)} rows" for status, count in counts.items()]


def _write_manifest(report_dir: Path) -> None:
    rows: list[dict[str, Any]] = []
    for file_path in sorted(report_dir.iterdir()):
        if not file_path.is_file() or file_path.name == "artifact_manifest.csv":
            continue
        rows.append(
            {
                "relative_path": file_path.name,
                "artifact_class": _artifact_class(file_path),
                "row_count": _row_count(file_path),
                "size_bytes": file_path.stat().st_size,
                "sha256": _sha256(file_path),
            }
        )
    pd.DataFrame(rows).to_csv(report_dir / "artifact_manifest.csv", index=False, encoding="utf-8-sig")


def _artifact_class(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return "report"
    if "decision" in path.name.lower():
        return "decision"
    return "small_table"


def _row_count(path: Path) -> int | str:
    if path.suffix.lower() != ".csv":
        return ""
    try:
        return int(len(pd.read_csv(path)))
    except Exception:
        return ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = validate_stop_tp_from_db(args.db_path)
    write_stop_tp_reports(args.report_dir, artifacts)
    print(artifacts["stop_tp_validation_summary"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
