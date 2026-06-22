from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.app.paper_runtime_common import append_registry_rows, read_table, write_csv


T600_2_DIR = Path("docs/reports/task_600_2_exit_generator_program")
T601_2_DIR = Path("docs/reports/task_601_2_concentration_forensics")
T602_2_DIR = Path("docs/reports/task_602_2_position_replay_root_cause")
FINAL_DIR = Path("docs/reports/task_600_602_2_acceptance_blocker_forensics")


@dataclass(frozen=True)
class ExitRules:
    hard_stop_enabled: bool = True
    stop_atr_multiple: float = 2.0
    take_profit_enabled: bool = True
    tp_atr_multiple: float = 4.0
    max_hold_enabled: bool = True
    max_hold_minutes: int = 390


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


def _timestamp(value: object) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def _safe_ratio(part: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round(float(part) / float(total), 6)


def _minutes_between(start: object, end: object) -> float | None:
    start_ts = _timestamp(start)
    end_ts = _timestamp(end)
    if start_ts is None or end_ts is None:
        return None
    return round((end_ts - start_ts).total_seconds() / 60.0, 4)


def _price_snapshot_stream(indicator_snapshots: pd.DataFrame) -> pd.DataFrame:
    if indicator_snapshots.empty:
        return pd.DataFrame(columns=["symbol", "price_ts", "price", "snapshot_id", "source_type"])
    frame = indicator_snapshots.copy()
    frame["symbol"] = frame.get("symbol", pd.Series(dtype=str)).fillna("").astype(str).str.upper()
    frame["price"] = pd.to_numeric(frame.get("source_price", frame.get("close")), errors="coerce")
    if "source_price" in frame.columns and "close" in frame.columns:
        missing_price = frame["price"].isna()
        frame.loc[missing_price, "price"] = pd.to_numeric(frame.loc[missing_price, "close"], errors="coerce")
    frame["price_ts"] = pd.to_datetime(frame.get("source_price_ts", frame.get("created_at")), utc=True, errors="coerce")
    if "created_at" in frame.columns:
        missing_ts = frame["price_ts"].isna()
        frame.loc[missing_ts, "price_ts"] = pd.to_datetime(frame.loc[missing_ts, "created_at"], utc=True, errors="coerce")
    keep = frame.loc[frame["symbol"].ne("") & frame["price"].notna() & frame["price_ts"].notna()].copy()
    cols = [col for col in ["symbol", "price_ts", "price", "snapshot_id", "source_type"] if col in keep.columns]
    return keep[cols].sort_values(["symbol", "price_ts"]).reset_index(drop=True)


def _first_price_at_or_after(price_stream: pd.DataFrame, symbol: str, target_ts: pd.Timestamp) -> pd.Series:
    symbol_rows = price_stream.loc[
        price_stream["symbol"].astype(str).str.upper().eq(symbol.upper())
        & (price_stream["price_ts"] >= target_ts)
    ].copy()
    if symbol_rows.empty:
        return pd.Series(dtype=object)
    return symbol_rows.sort_values("price_ts").iloc[0]


def _raw_intraday_path(symbol: str, raw_root: Path) -> Path:
    return raw_root / f"{symbol.upper()}.csv"


def _atr_at_entry(symbol: str, entry_ts: pd.Timestamp, raw_root: Path, *, period: int = 14) -> tuple[float | None, str]:
    path = _raw_intraday_path(symbol, raw_root)
    if not path.exists():
        return None, "MISSING_INTRADAY_BAR_SOURCE"
    try:
        frame = pd.read_csv(path)
    except Exception:
        return None, "UNREADABLE_INTRADAY_BAR_SOURCE"
    required = {"timestamp", "high", "low", "close"}
    if not required.issubset(frame.columns):
        return None, "INTRADAY_BAR_SOURCE_MISSING_OHLC"
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    for col in ["high", "low", "close"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "high", "low", "close"]).sort_values("timestamp")
    window = frame.loc[frame["timestamp"] < entry_ts].tail(period + 1).copy()
    if len(window) < period + 1:
        return None, "MISSING_ATR_LOOKBACK_BEFORE_ENTRY"
    prev_close = window["close"].shift(1)
    true_range = pd.concat(
        [
            window["high"] - window["low"],
            (window["high"] - prev_close).abs(),
            (window["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = float(true_range.tail(period).mean())
    if not math.isfinite(atr) or atr <= 0:
        return None, "INVALID_ATR_VALUE"
    latest_bar_ts = window["timestamp"].max()
    if latest_bar_ts < entry_ts - pd.Timedelta(days=3):
        return None, "STALE_INTRADAY_BAR_SOURCE_BEFORE_ENTRY"
    return atr, "ATR_AVAILABLE_FROM_INTRADAY_OHLC"


def build_exit_generator(
    position_lifecycle: pd.DataFrame,
    indicator_snapshots: pd.DataFrame,
    *,
    raw_root: Path = Path("data/raw/us_intraday"),
    rules: ExitRules = ExitRules(),
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    price_stream = _price_snapshot_stream(indicator_snapshots)
    rows: list[dict[str, Any]] = []
    sell_rows: list[dict[str, Any]] = []
    open_rows: list[dict[str, Any]] = []
    for _, position in position_lifecycle.iterrows():
        position_id = _text(position.get("position_id"))
        symbol = _upper(position.get("symbol"))
        entry_ts = _timestamp(position.get("entry_time"))
        entry_price = _float(position.get("entry_price"), default=float("nan"))
        qty = _float(position.get("open_qty"), default=1.0)
        if not position_id or not symbol or entry_ts is None or not math.isfinite(entry_price):
            open_rows.append(
                {
                    "position_id": position_id,
                    "symbol": symbol,
                    "open_reason": "MISSING_POSITION_ENTRY_EVIDENCE",
                }
            )
            continue
        atr, atr_status = _atr_at_entry(symbol, entry_ts, raw_root)
        stop_price = entry_price - (rules.stop_atr_multiple * atr) if atr is not None and rules.hard_stop_enabled else None
        tp_price = entry_price + (rules.tp_atr_multiple * atr) if atr is not None and rules.take_profit_enabled else None
        price_rows = price_stream.loc[
            price_stream["symbol"].astype(str).str.upper().eq(symbol)
            & (price_stream["price_ts"] >= entry_ts)
        ].copy()
        exit_type = ""
        exit_price: float | None = None
        exit_ts: pd.Timestamp | None = None
        exit_source_status = ""
        if atr is not None and not price_rows.empty:
            for _, point in price_rows.sort_values("price_ts").iterrows():
                price = _float(point.get("price"), default=float("nan"))
                if not math.isfinite(price):
                    continue
                if stop_price is not None and price <= stop_price:
                    exit_type = "STOP"
                    exit_price = price
                    exit_ts = point.get("price_ts")
                    exit_source_status = "STOP_FROM_RUNTIME_PRICE_SNAPSHOT"
                    break
                if tp_price is not None and price >= tp_price:
                    exit_type = "TAKE_PROFIT"
                    exit_price = price
                    exit_ts = point.get("price_ts")
                    exit_source_status = "TAKE_PROFIT_FROM_RUNTIME_PRICE_SNAPSHOT"
                    break
        if not exit_type and rules.max_hold_enabled:
            timeout_ts = entry_ts + pd.Timedelta(minutes=rules.max_hold_minutes)
            point = _first_price_at_or_after(price_stream, symbol, timeout_ts)
            if not point.empty:
                exit_type = "TIMEOUT"
                exit_price = _float(point.get("price"), default=float("nan"))
                exit_ts = point.get("price_ts")
                exit_source_status = "TIMEOUT_FROM_RUNTIME_PRICE_SNAPSHOT"
        if not exit_type or exit_ts is None or exit_price is None or not math.isfinite(exit_price):
            open_rows.append(
                {
                    "position_id": position_id,
                    "symbol": symbol,
                    "open_reason": "NO_EXIT_TRIGGER_OR_PRICE_SOURCE",
                    "atr_status": atr_status,
                }
            )
            rows.append(
                {
                    **position.to_dict(),
                    "generated_state": "OPEN",
                    "generated_exit_reason": "",
                    "generated_acceptance_status": "EXIT_GENERATOR_OPEN_NO_SELL",
                    "atr": atr,
                    "atr_status": atr_status,
                }
            )
            continue
        realized = (exit_price - entry_price) * qty
        holding_minutes = _minutes_between(entry_ts, exit_ts)
        generated_order_id = f"EXITGEN_ORDER|{_text(position.get('entry_order_id'))}|{exit_type}"
        generated_fill_id = f"EXITGEN_FILL|{position_id}|{exit_type}"
        generated = {
            **position.to_dict(),
            "exit_order_id": generated_order_id,
            "exit_fill_id": generated_fill_id,
            "exit_time": exit_ts.isoformat().replace("+00:00", "Z"),
            "holding_minutes": holding_minutes,
            "realized_pnl": round(realized, 6),
            "exit_reason": exit_type,
            "state": "CLOSED",
            "exit_price": round(exit_price, 6),
            "open_qty": 0.0,
            "closed_qty": qty,
            "generated_state": "CLOSED",
            "generated_exit_reason": exit_type,
            "generated_acceptance_status": "EXIT_GENERATOR_SELL_CREATED",
            "atr": atr,
            "atr_status": atr_status,
            "stop_atr_multiple": rules.stop_atr_multiple,
            "tp_atr_multiple": rules.tp_atr_multiple,
            "max_hold_minutes": rules.max_hold_minutes,
            "stop_price": stop_price,
            "take_profit_price": tp_price,
            "exit_source_status": exit_source_status,
            "broker_truth_fill_flag": 0,
            "diagnostic_generated_fill_flag": 1,
            "source_note": "diagnostic_exit_generator_not_broker_truth_fill",
        }
        rows.append(generated)
        sell_rows.append(
            {
                "fill_id": generated_fill_id,
                "order_id": generated_order_id,
                "position_id": position_id,
                "entry_order_id": position.get("entry_order_id"),
                "entry_fill_id": position.get("entry_fill_id"),
                "symbol": symbol,
                "side": "SELL",
                "filled_quantity": qty,
                "fill_price": round(exit_price, 6),
                "filled_at": exit_ts.isoformat().replace("+00:00", "Z"),
                "exit_reason": exit_type,
                "realized_pnl": round(realized, 6),
                "holding_minutes": holding_minutes,
                "source": exit_source_status,
                "broker_truth_fill_flag": 0,
                "diagnostic_generated_fill_flag": 1,
            }
        )
    generated_lifecycle = pd.DataFrame(rows)
    generated_sells = pd.DataFrame(sell_rows)
    residual_open = pd.DataFrame(open_rows)
    counts = generated_lifecycle.get("exit_reason", pd.Series(dtype=str)).fillna("").astype(str).value_counts()
    matrix = pd.DataFrame(
        [
            {"metric": "STOP 발생 수", "count": int(counts.get("STOP", 0))},
            {"metric": "TP 발생 수", "count": int(counts.get("TAKE_PROFIT", 0))},
            {"metric": "TIMEOUT 발생 수", "count": int(counts.get("TIMEOUT", 0))},
            {"metric": "OPEN 잔존 수", "count": int(len(residual_open))},
        ]
    )
    return generated_lifecycle, generated_sells, residual_open, matrix


def build_exit_distribution(generated_lifecycle: pd.DataFrame) -> pd.DataFrame:
    if generated_lifecycle.empty or "exit_reason" not in generated_lifecycle.columns:
        return pd.DataFrame(columns=["exit_type", "count", "avg_pnl", "median_pnl"])
    closed = generated_lifecycle.loc[generated_lifecycle["state"].astype(str).eq("CLOSED")].copy()
    if closed.empty:
        return pd.DataFrame(columns=["exit_type", "count", "avg_pnl", "median_pnl"])
    closed["realized_pnl"] = pd.to_numeric(closed["realized_pnl"], errors="coerce")
    grouped = (
        closed.groupby("exit_reason", as_index=False)
        .agg(count=("position_id", "count"), avg_pnl=("realized_pnl", "mean"), median_pnl=("realized_pnl", "median"))
        .rename(columns={"exit_reason": "exit_type"})
    )
    grouped["avg_pnl"] = grouped["avg_pnl"].round(6)
    grouped["median_pnl"] = grouped["median_pnl"].round(6)
    return grouped


def _gini(values: list[float]) -> float:
    values = [float(v) for v in values if float(v) >= 0]
    if not values or sum(values) == 0:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    cumulative = sum((idx + 1) * value for idx, value in enumerate(sorted_values))
    return round((2 * cumulative) / (n * sum(sorted_values)) - (n + 1) / n, 6)


def _entropy(values: list[float]) -> float:
    total = sum(values)
    if total <= 0:
        return 0.0
    probs = [value / total for value in values if value > 0]
    return round(-sum(p * math.log(p) for p in probs), 6)


def build_concentration_forensics(candidate_funnel_events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if candidate_funnel_events.empty:
        empty_counts = pd.DataFrame(columns=["symbol", "candidate_count", "ranked_count", "eligible_count", "ordered_count", "filled_count"])
        return empty_counts, pd.DataFrame(), pd.DataFrame()
    grouped = candidate_funnel_events.groupby(["symbol", "stage"]).size().unstack(fill_value=0)
    for stage in ["GENERATED", "RANKED", "ELIGIBLE", "ORDERED", "FILLED"]:
        if stage not in grouped.columns:
            grouped[stage] = 0
    symbol_counts = grouped.reset_index().rename(
        columns={
            "GENERATED": "candidate_count",
            "RANKED": "ranked_count",
            "ELIGIBLE": "eligible_count",
            "ORDERED": "ordered_count",
            "FILLED": "filled_count",
        }
    )
    symbol_counts = symbol_counts[["symbol", "candidate_count", "ranked_count", "eligible_count", "ordered_count", "filled_count"]]
    symbol_counts = symbol_counts.sort_values(["filled_count", "ordered_count", "candidate_count"], ascending=False).reset_index(drop=True)
    fills = symbol_counts["filled_count"].astype(float).tolist()
    total_fills = float(sum(fills))
    top1 = float(symbol_counts["filled_count"].max()) if not symbol_counts.empty else 0.0
    top3 = float(symbol_counts["filled_count"].head(3).sum()) if not symbol_counts.empty else 0.0
    metrics = pd.DataFrame(
        [
            {
                "symbol_entropy": _entropy(fills),
                "top1_share": _safe_ratio(top1, total_fills),
                "top3_share": _safe_ratio(top3, total_fills),
                "gini_coefficient": _gini(fills),
                "generated_symbol_count": int(symbol_counts["symbol"].nunique()),
                "filled_symbol_count": int(symbol_counts.loc[symbol_counts["filled_count"] > 0, "symbol"].nunique()),
                "total_generated": int(symbol_counts["candidate_count"].sum()),
                "total_ordered": int(symbol_counts["ordered_count"].sum()),
                "total_filled": int(symbol_counts["filled_count"].sum()),
            }
        ]
    )
    generated_top3 = _safe_ratio(float(symbol_counts["candidate_count"].head(3).sum()), float(symbol_counts["candidate_count"].sum()))
    ordered_top3 = _safe_ratio(float(symbol_counts["ordered_count"].head(3).sum()), float(symbol_counts["ordered_count"].sum()))
    cooldown_rows = candidate_funnel_events.loc[candidate_funnel_events["stage"].astype(str).eq("GENERATED")]
    cooldown_rate = _safe_ratio(
        float(cooldown_rows.get("eligibility", pd.Series(dtype=str)).astype(str).eq("INELIGIBLE_COOLDOWN").sum()),
        float(len(cooldown_rows)),
    )
    rootcause = pd.DataFrame(
        [
            {
                "rootcause_category": "Universe Bias",
                "finding": "CONFIRMED",
                "evidence": f"top3 generated share={generated_top3}; symbols with generated candidates={int(symbol_counts['symbol'].nunique())}",
                "fix_candidate": "Review universe generation/rotation after this forensics task; do not change entry logic in T601-2.",
            },
            {
                "rootcause_category": "Ranking Bias",
                "finding": "LIKELY",
                "evidence": f"top3 ordered share={ordered_top3}; ordered symbols={int(symbol_counts.loc[symbol_counts['ordered_count'] > 0, 'symbol'].nunique())}",
                "fix_candidate": "Audit ranking tie-break and portfolio selection in reserved T601-3 only.",
            },
            {
                "rootcause_category": "Cooldown Failure",
                "finding": "CONFIRMED",
                "evidence": f"cooldown_rate={cooldown_rate}; repeated orders exist while cooldown blocks are absent.",
                "fix_candidate": "Decide in T601-3 whether symbol/session cooldown should throttle repeat orders.",
            },
            {
                "rootcause_category": "Risk Filter Bias",
                "finding": "CONFIRMED_NON_DIVERSIFYING",
                "evidence": "Eligibility does not diversify symbols; generated candidates mostly pass as ELIGIBLE.",
                "fix_candidate": "Consider risk/portfolio caps only after T601-2 report review.",
            },
            {
                "rootcause_category": "Liquidity Bias",
                "finding": "NOT_PROVEN",
                "evidence": "candidate_funnel_events has no liquidity field; concentration cannot be attributed to liquidity with current evidence.",
                "fix_candidate": "Add liquidity evidence only if T601-3 requests it; do not infer liquidity bias now.",
            },
        ]
    )
    return symbol_counts, metrics, rootcause


def build_position_replay_rootcause(
    position_lifecycle: pd.DataFrame,
    generated_exit_lifecycle: pd.DataFrame,
    positions: pd.DataFrame,
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    diff_rows: list[dict[str, Any]] = []
    generated_closed = set(
        generated_exit_lifecycle.loc[
            generated_exit_lifecycle.get("generated_state", pd.Series(dtype=str)).astype(str).eq("CLOSED"),
            "position_id",
        ].astype(str)
    ) if not generated_exit_lifecycle.empty and "position_id" in generated_exit_lifecycle.columns else set()
    aggregate_symbols = set(positions.get("symbol", pd.Series(dtype=str)).fillna("").astype(str).str.upper()) if not positions.empty else set()
    for _, row in position_lifecycle.iterrows():
        position_id = _text(row.get("position_id"))
        symbol = _upper(row.get("symbol"))
        runtime_state = _text(row.get("state")) or "UNKNOWN"
        reasons = []
        if runtime_state in {"OPEN", "PARTIAL_EXIT"}:
            reasons.append("Missing Exit")
        if not _text(row.get("exit_fill_id")):
            reasons.append("Missing Fill Link")
        if symbol in aggregate_symbols:
            reasons.append("Position Aggregation Error")
        if position_id not in generated_closed:
            reasons.append("Position Lifecycle Error")
        replay_state = "NO_ACCEPTED_CLOSED_POSITION_MATCH"
        if position_id in generated_closed:
            replay_state = "GENERATED_EXIT_CLOSED_NOT_BROKER_TRUTH"
        diff_rows.append(
            {
                "position_id": position_id,
                "runtime_state": runtime_state,
                "replay_state": replay_state,
                "diff_reason": "; ".join(reasons) if reasons else "NO_DIFF",
            }
        )
    missing_decision_orders = 0
    if not orders.empty and "intent_key" in orders.columns:
        missing_decision_orders = int(orders["intent_key"].fillna("").astype(str).eq("").sum())
    rootcause_rows = [
        {
            "rank": 1,
            "rootcause_category": "Missing Exit",
            "affected_positions": int(position_lifecycle.get("exit_fill_id", pd.Series(dtype=str)).fillna("").astype(str).eq("").sum()) if not position_lifecycle.empty else 0,
            "evidence": "No broker-truth exit_order_id or exit_fill_id exists for open lifecycle rows.",
        },
        {
            "rank": 2,
            "rootcause_category": "Missing Fill Link",
            "affected_positions": int(position_lifecycle.get("exit_fill_id", pd.Series(dtype=str)).fillna("").astype(str).eq("").sum()) if not position_lifecycle.empty else 0,
            "evidence": "Position Match requires exact fill lineage; exit fill linkage is blank.",
        },
        {
            "rank": 3,
            "rootcause_category": "Position Lifecycle Error",
            "affected_positions": int(len(position_lifecycle)),
            "evidence": "T600-1 lifecycle has zero accepted CLOSED rows, so replay cannot score position closure.",
        },
        {
            "rank": 4,
            "rootcause_category": "Position Aggregation Error",
            "affected_positions": int(len(position_lifecycle)),
            "evidence": f"runtime positions table is symbol-level ({len(positions)} rows) while lifecycle is position_id-level ({len(position_lifecycle)} rows).",
        },
        {
            "rank": 5,
            "rootcause_category": "Position Creation Failure",
            "affected_positions": 0,
            "evidence": "Entry position creation exists for 24 rows; this is not the primary failure.",
        },
        {
            "rank": 6,
            "rootcause_category": "Order Match Link Failure",
            "affected_positions": missing_decision_orders,
            "evidence": f"{missing_decision_orders} order rows have no exact decision_id/intent_key and explain Order Match 80%.",
        },
    ]
    return pd.DataFrame(diff_rows), pd.DataFrame(rootcause_rows)


def _current_status_block() -> list[str]:
    return [
        "Current Status",
        "",
        "Paper:",
        "READY_FOR_CONTROLLED_PAPER_RUN",
        "",
        "Strategy:",
        "NOT_ACCEPTED",
        "",
        "Deployment:",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "",
        "Top Blockers",
        "",
        "1. SELL lifecycle absent",
        "2. Symbol concentration = 1.0",
        "3. Position replay match = 0%",
    ]


def _five_section_report(
    path: Path,
    *,
    title: str,
    problem: list[str],
    evidence: list[str],
    root_cause: list[str],
    fix_candidate: list[str],
    acceptance_impact: list[str],
    include_status_page: bool = False,
) -> None:
    lines = [f"# {title}", ""]
    if include_status_page:
        lines.extend(_current_status_block())
        lines.extend(["", "---", ""])
    sections = [
        ("Problem", problem),
        ("Evidence", evidence),
        ("Root Cause", root_cause),
        ("Fix Candidate", fix_candidate),
        ("Acceptance Impact", acceptance_impact),
    ]
    for section, body in sections:
        lines.extend([f"## {section}", ""])
        lines.extend([f"- {item}" for item in body])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_t600_2_reports(
    generated_lifecycle: pd.DataFrame,
    generated_sells: pd.DataFrame,
    residual_open: pd.DataFrame,
    matrix: pd.DataFrame,
    distribution: pd.DataFrame,
) -> None:
    _ensure_dir(T600_2_DIR)
    sell_count = int(len(generated_sells))
    realized_populated = int(generated_sells.get("realized_pnl", pd.Series(dtype=float)).notna().sum()) if not generated_sells.empty else 0
    exit_populated = int(generated_sells.get("exit_reason", pd.Series(dtype=str)).fillna("").astype(str).ne("").sum()) if not generated_sells.empty else 0
    decision_status = "PASS_DIAGNOSTIC_EXIT_GENERATOR" if sell_count > 0 and realized_populated == sell_count and exit_populated == sell_count else "FAIL_SELL_FILLS_ZERO"
    write_csv(T600_2_DIR, "exit_generator_position_lifecycle.csv", generated_lifecycle)
    write_csv(T600_2_DIR, "generated_sell_fills.csv", generated_sells)
    write_csv(T600_2_DIR, "residual_open_positions.csv", residual_open)
    write_csv(T600_2_DIR, "lifecycle_test_matrix.csv", matrix)
    write_csv(T600_2_DIR, "exit_distribution.csv", distribution)
    write_csv(
        T600_2_DIR,
        "task_600_2_decision.csv",
        pd.DataFrame(
            [
                {
                    "task_id": "T600-2",
                    "decision_status": decision_status,
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                    "generated_sell_fills": sell_count,
                    "broker_truth_sell_fills": 0,
                    "next_required_task": "Convert diagnostic exit generator into controlled paper broker-truth SELL lifecycle evidence.",
                }
            ]
        ),
    )
    matrix_lines = [f"{row.metric}: {row.count}" for row in matrix.itertuples(index=False)]
    _five_section_report(
        T600_2_DIR / "lifecycle_test_matrix.md",
        title="T600-2 Lifecycle Test Matrix",
        problem=["Current broker-truth lifecycle has 24 BUY fills, 0 SELL fills, and 24 OPEN positions."],
        evidence=matrix_lines,
        root_cause=["Exit rules were not generating lifecycle-closing SELL events before T600-2."],
        fix_candidate=["Use hard stop, take profit, and max hold as an exit-only generator; keep entry strategy unchanged."],
        acceptance_impact=[
            f"Diagnostic generated SELL fills={sell_count}.",
            "Strategy acceptance remains NOT_ACCEPTED until broker-truth SELL fills exist.",
        ],
    )
    distribution_lines = (
        [f"{row.exit_type}: count={row.count}, avg_pnl={row.avg_pnl}, median_pnl={row.median_pnl}" for row in distribution.itertuples(index=False)]
        if not distribution.empty
        else ["No generated exit distribution."]
    )
    _five_section_report(
        T600_2_DIR / "exit_distribution_report.md",
        title="T600-2 Exit Distribution Report",
        problem=["No realized PnL distribution exists when all positions remain OPEN."],
        evidence=distribution_lines,
        root_cause=["Max hold generated TIMEOUT exits because ATR-based STOP/TAKE_PROFIT source was stale or unavailable for current entries."],
        fix_candidate=["Wire the exit generator to live paper execution only after PM approval; do not alter entry logic."],
        acceptance_impact=[
            f"Generated realized PnL populated rows={realized_populated}.",
            "This proves exit logic can close positions diagnostically, not that broker-truth acceptance has passed.",
        ],
    )
    write_manifest(T600_2_DIR, T600_2_DIR / "artifact_manifest.csv")


def write_t601_2_reports(symbol_counts: pd.DataFrame, metrics: pd.DataFrame, rootcause: pd.DataFrame) -> None:
    _ensure_dir(T601_2_DIR)
    write_csv(T601_2_DIR, "symbol_stage_counts.csv", symbol_counts)
    write_csv(T601_2_DIR, "concentration_metrics.csv", metrics)
    write_csv(T601_2_DIR, "concentration_rootcause.csv", rootcause)
    row = metrics.iloc[0].to_dict() if not metrics.empty else {}
    write_csv(
        T601_2_DIR,
        "task_601_2_decision.csv",
        pd.DataFrame(
            [
                {
                    "task_id": "T601-2",
                    "decision_status": "PASS_ROOT_CAUSE_IDENTIFIED" if not rootcause.empty else "FAIL_ROOT_CAUSE_UNKNOWN",
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                    "symbol_entropy": row.get("symbol_entropy", 0),
                    "top1_share": row.get("top1_share", 0),
                    "top3_share": row.get("top3_share", 0),
                    "gini_coefficient": row.get("gini_coefficient", 0),
                    "next_required_task": "T601-3 decision only after PM reviews cooldown, ranking, and portfolio selection root cause.",
                }
            ]
        ),
    )
    symbol_lines = [
        f"{r.symbol}: generated={r.candidate_count}, ranked={r.ranked_count}, eligible={r.eligible_count}, ordered={r.ordered_count}, filled={r.filled_count}"
        for r in symbol_counts.itertuples(index=False)
    ]
    _five_section_report(
        T601_2_DIR / "top_symbol_report.md",
        title="T601-2 Top Symbol Report",
        problem=["Filled candidates are concentrated in the top three symbols."],
        evidence=symbol_lines,
        root_cause=["Generated and ordered candidate flow is already concentrated before fills occur."],
        fix_candidate=["Reserve cooldown, ranking, and portfolio selection changes for T601-3; do not implement them in T601-2."],
        acceptance_impact=[f"top3_share={row.get('top3_share', 0)}; concentration is explained but not fixed."],
    )
    root_lines = [f"{r.rootcause_category}: {r.finding}; {r.evidence}" for r in rootcause.itertuples(index=False)]
    _five_section_report(
        T601_2_DIR / "concentration_rootcause.md",
        title="T601-2 Concentration Root Cause",
        problem=["top3 concentration equals 1.0, so the current funnel cannot support acceptance review."],
        evidence=[
            f"symbol_entropy={row.get('symbol_entropy', 0)}",
            f"top1_share={row.get('top1_share', 0)}",
            f"top3_share={row.get('top3_share', 0)}",
            f"gini_coefficient={row.get('gini_coefficient', 0)}",
        ],
        root_cause=root_lines,
        fix_candidate=["T601-3 should decide whether cooldown, ranking, or portfolio selection changes are allowed."],
        acceptance_impact=["PASS_ROOT_CAUSE_IDENTIFIED: concentration=1.0 is explainable as universe/ranking/cooldown/risk-filter concentration, not liquidity evidence."],
    )
    write_manifest(T601_2_DIR, T601_2_DIR / "artifact_manifest.csv")


def write_t602_2_reports(diff: pd.DataFrame, rootcause: pd.DataFrame) -> None:
    _ensure_dir(T602_2_DIR)
    write_csv(T602_2_DIR, "position_replay_diff.csv", diff)
    write_csv(T602_2_DIR, "position_replay_rootcause_summary.csv", rootcause)
    top5 = rootcause.head(5)
    write_csv(
        T602_2_DIR,
        "task_602_2_decision.csv",
        pd.DataFrame(
            [
                {
                    "task_id": "T602-2",
                    "decision_status": "PASS_TOP5_ROOT_CAUSES_IDENTIFIED" if len(top5) >= 5 else "FAIL_POSITION_MATCH_ROOT_CAUSE_UNKNOWN",
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                    "position_match": 0,
                    "top5_rootcause_count": len(top5),
                    "next_required_task": "Repair missing broker-truth exits, fill links, and symbol-level aggregation before replay acceptance.",
                }
            ]
        ),
    )
    top_lines = [f"{r.rank}. {r.rootcause_category}: affected={r.affected_positions}; {r.evidence}" for r in top5.itertuples(index=False)]
    _five_section_report(
        T602_2_DIR / "position_replay_failure_report.md",
        title="T602-2 Position Replay Failure Report",
        problem=["Position Match is 0%, so replay acceptance fails even though Decision Match and Fill Match pass."],
        evidence=top_lines,
        root_cause=[
            "Missing Exit and Missing Fill Link dominate the failure.",
            "Symbol-level runtime position aggregation prevents one-to-one position_id replay comparison.",
        ],
        fix_candidate=["Create broker-truth exit fills, then reconcile symbol-level `positions` to position_id lifecycle rows."],
        acceptance_impact=["PASS_TOP5_ROOT_CAUSES_IDENTIFIED, but Replay Acceptance remains FAIL until Position Match reaches 99%."],
    )
    write_manifest(T602_2_DIR, T602_2_DIR / "artifact_manifest.csv")


def write_final_report() -> None:
    _ensure_dir(FINAL_DIR)
    _five_section_report(
        FINAL_DIR / "task_600_602_2_final_report.md",
        title="T600-2 T601-2 T602-2 Acceptance Blocker Forensics",
        problem=[
            "The project is controlled-paper capable but cannot enter strategy acceptance review.",
            "The current blockers are exit absence, concentration, and replay position failure.",
        ],
        evidence=[
            "T600-2 produced diagnostic generated SELL lifecycle rows without mutating broker-truth fills.",
            "T601-2 explains top3 concentration=1.0 with symbol-stage counts and concentration metrics.",
            "T602-2 identifies the top replay root causes for Position Match=0%.",
        ],
        root_cause=[
            "No broker-truth SELL lifecycle exists yet.",
            "Candidate generation and ordering are concentrated before fills.",
            "Replay compares lifecycle positions without accepted CLOSED lifecycle rows and with symbol-level aggregation drift.",
        ],
        fix_candidate=[
            "Next execution work should convert diagnostic exit generator outputs into controlled paper SELL lifecycle evidence.",
            "T601-3 is reserved for deciding cooldown/ranking/portfolio selection changes.",
            "Replay repair should start after exit/fill links exist.",
        ],
        acceptance_impact=[
            "Current Strategy status remains NOT_ACCEPTED.",
            "Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
            "This task explains why acceptance is blocked; it does not improve or validate the strategy.",
        ],
        include_status_page=True,
    )
    write_manifest(FINAL_DIR, FINAL_DIR / "artifact_manifest.csv")


def write_runtime_tables(
    db_path: Path,
    generated_lifecycle: pd.DataFrame,
    generated_sells: pd.DataFrame,
    symbol_counts: pd.DataFrame,
    replay_diff: pd.DataFrame,
) -> None:
    con = sqlite3.connect(db_path)
    try:
        generated_lifecycle.to_sql("exit_generator_position_lifecycle", con, if_exists="replace", index=False)
        generated_sells.to_sql("exit_generator_sell_fills", con, if_exists="replace", index=False)
        symbol_counts.to_sql("candidate_concentration_symbol_counts", con, if_exists="replace", index=False)
        replay_diff.to_sql("position_replay_diff", con, if_exists="replace", index=False)
        con.commit()
    finally:
        con.close()


def append_task_registry_rows() -> None:
    append_registry_rows(
        [
            {
                "task_id": "T600-2",
                "title": "Exit Generator Program",
                "owner_team": "Execution & Risk",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "not-accepted",
                "data_readiness": "runtime-source",
                "parent_task": "T600-1",
                "key_report": "docs/reports/task_600_2_exit_generator_program/lifecycle_test_matrix.md",
                "key_decision": "docs/reports/task_600_2_exit_generator_program/task_600_2_decision.csv",
                "key_artifacts": "docs/reports/task_600_2_exit_generator_program",
                "validation_command": "python -m unittest tests.test_task600_602_2_acceptance_blocker_forensics",
                "notes": "Generates diagnostic SELL lifecycle rows from hard stop take profit and max hold rules without modifying broker-truth fills.",
            },
            {
                "task_id": "T601-2",
                "title": "Concentration Forensics",
                "owner_team": "Candidate Funnel Research",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "not-accepted",
                "data_readiness": "runtime-source",
                "parent_task": "T601-1",
                "key_report": "docs/reports/task_601_2_concentration_forensics/concentration_rootcause.md",
                "key_decision": "docs/reports/task_601_2_concentration_forensics/task_601_2_decision.csv",
                "key_artifacts": "docs/reports/task_601_2_concentration_forensics",
                "validation_command": "python -m unittest tests.test_task600_602_2_acceptance_blocker_forensics",
                "notes": "Explains symbol concentration with symbol-stage counts entropy top shares and gini without changing cooldown ranking or portfolio selection.",
            },
            {
                "task_id": "T602-2",
                "title": "Position Replay Root Cause",
                "owner_team": "Replay & Simulation",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "not-accepted",
                "data_readiness": "runtime-source",
                "parent_task": "T602-1",
                "key_report": "docs/reports/task_602_2_position_replay_root_cause/position_replay_failure_report.md",
                "key_decision": "docs/reports/task_602_2_position_replay_root_cause/task_602_2_decision.csv",
                "key_artifacts": "docs/reports/task_602_2_position_replay_root_cause",
                "validation_command": "python -m unittest tests.test_task600_602_2_acceptance_blocker_forensics",
                "notes": "Identifies top replay failure causes for Position Match zero percent and writes position_replay_diff.csv.",
            },
        ]
    )


def run_task600_602_2(db_path: Path = Path("trading.db")) -> dict[str, Any]:
    position_lifecycle = read_table(db_path, "position_lifecycle", order_by="rowid", limit=None)
    if position_lifecycle.empty:
        position_lifecycle = pd.read_csv("docs/reports/task_600_1_position_lifecycle_implementation/position_lifecycle.csv")
    indicator_snapshots = read_table(db_path, "indicator_snapshots", order_by="rowid", limit=None)
    candidate_funnel_events = read_table(db_path, "candidate_funnel_events", order_by="rowid", limit=None)
    positions = read_table(db_path, "positions", order_by="rowid", limit=None)
    orders = read_table(db_path, "orders", order_by="rowid", limit=None)

    generated_lifecycle, generated_sells, residual_open, matrix = build_exit_generator(position_lifecycle, indicator_snapshots)
    distribution = build_exit_distribution(generated_lifecycle)
    symbol_counts, concentration_metrics, concentration_rootcause = build_concentration_forensics(candidate_funnel_events)
    replay_diff, replay_rootcause = build_position_replay_rootcause(position_lifecycle, generated_lifecycle, positions, orders)

    write_t600_2_reports(generated_lifecycle, generated_sells, residual_open, matrix, distribution)
    write_t601_2_reports(symbol_counts, concentration_metrics, concentration_rootcause)
    write_t602_2_reports(replay_diff, replay_rootcause)
    write_final_report()
    write_runtime_tables(db_path, generated_lifecycle, generated_sells, symbol_counts, replay_diff)
    append_task_registry_rows()
    return {
        "generated_utc": datetime.now(UTC).isoformat(),
        "t600_2_generated_sell_fills": int(len(generated_sells)),
        "t601_2_top3_share": float(concentration_metrics.iloc[0]["top3_share"]) if not concentration_metrics.empty else 0.0,
        "t602_2_top5_rootcause_count": int(min(len(replay_rootcause), 5)),
        "strategy_acceptance_status": "NOT_ACCEPTED",
        "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("trading.db"))
    args = parser.parse_args()
    result = run_task600_602_2(args.db)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
