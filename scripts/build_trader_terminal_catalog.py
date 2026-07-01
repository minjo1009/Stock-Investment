from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.reporting.research_task_catalog import build_research_task_catalog, load_artifact_manifest
from src.reporting.readiness_registry import build_readiness_registry_payload


PNL_COLUMNS = [
    "net_return_from_entry",
    "net_return_pct",
    "post_cost_return_pct",
    "net_pnl_pct",
    "return_from_entry",
]

STATUS_FIELDS = [
    "strategy_acceptance_status",
    "promotion_decision",
    "promotion_decision_v2",
    "edge_status",
    "task_547_status",
]

INTRADAY_RAW_ROOT = Path("data/raw/us_intraday")
_INTRADAY_CACHE: dict[str, pd.DataFrame] = {}
_RUNTIME_INTRADAY_CACHE: dict[str, pd.DataFrame] = {}


def _repo_rel(path: Path) -> str:
    try:
        return path.as_posix()
    except Exception:
        return str(path)


def _sha256_12(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def _file_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": _repo_rel(path),
            "exists": False,
            "modified_utc": None,
            "size_bytes": 0,
            "sha256_12": "",
        }
    stat = path.stat()
    return {
        "path": _repo_rel(path),
        "exists": True,
        "modified_utc": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
        "size_bytes": stat.st_size,
        "sha256_12": _sha256_12(path),
    }


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _read_decision(path: Path) -> dict[str, Any]:
    frame = _read_csv(path)
    return frame.iloc[0].to_dict() if not frame.empty else {}


def _pnl_column(frame: pd.DataFrame) -> str | None:
    for column in PNL_COLUMNS:
        if column in frame.columns:
            return column
    return None


def _net_pct(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.dropna().abs().max() <= 5:
        return values * 100.0
    return values


def _drawdown_pp(net_pct: pd.Series) -> float:
    curve = net_pct.fillna(0.0).cumsum()
    if curve.empty:
        return 0.0
    return float((curve.cummax() - curve).max())


def _bool_rate(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns:
        return None
    values = pd.to_numeric(frame[column], errors="coerce")
    if values.notna().sum() == 0:
        return None
    return float(values.mean() * 100.0)


def _group_quality(frame: pd.DataFrame, group_col: str, pnl_col: str, *, limit: int = 20) -> list[dict[str, Any]]:
    if group_col not in frame.columns:
        return []
    net = _net_pct(frame[pnl_col])
    temp = frame[[group_col]].copy()
    temp["_net_pct"] = net
    temp["_win"] = net > 0
    grouped = (
        temp.dropna(subset=[group_col])
        .groupby(group_col, as_index=False)
        .agg(
            count=("_net_pct", "count"),
            avg_net_pct=("_net_pct", "mean"),
            total_net_pct=("_net_pct", "sum"),
            win_rate=("_win", "mean"),
        )
        .sort_values("total_net_pct", ascending=False)
        .head(limit)
    )
    grouped["win_rate"] = grouped["win_rate"] * 100.0
    grouped = grouped.rename(columns={group_col: "key"})
    return grouped.to_dict(orient="records")


def _composite_group_quality(frame: pd.DataFrame, group_cols: list[str], pnl_col: str, *, limit: int = 40) -> list[dict[str, Any]]:
    available_cols = [col for col in group_cols if col in frame.columns]
    if len(available_cols) != len(group_cols):
        return []
    temp = frame[available_cols].copy()
    temp["_net_pct"] = _net_pct(frame[pnl_col])
    temp["_win"] = temp["_net_pct"] > 0
    temp["_entry_reduce"] = pd.to_numeric(frame.get("entry_reduce_failure_flag", pd.Series(dtype=float)), errors="coerce")
    temp["_add_scale"] = pd.to_numeric(frame.get("add_scale_success_flag", pd.Series(dtype=float)), errors="coerce")
    temp["_key"] = temp[available_cols].astype(str).agg(" × ".join, axis=1)
    grouped = (
        temp.groupby("_key", as_index=False)
        .agg(
            count=("_net_pct", "count"),
            avg_net_pct=("_net_pct", "mean"),
            total_net_pct=("_net_pct", "sum"),
            win_rate=("_win", "mean"),
            entry_reduce_rate=("_entry_reduce", "mean"),
            add_scale_rate=("_add_scale", "mean"),
        )
        .sort_values(["total_net_pct", "count"], ascending=[False, False])
        .head(limit)
    )
    for column in ["win_rate", "entry_reduce_rate", "add_scale_rate"]:
        grouped[column] = grouped[column] * 100.0
    grouped = grouped.rename(columns={"_key": "key"})
    grouped["group_columns"] = " × ".join(available_cols)
    return grouped.to_dict(orient="records")


def _matrix_quality(frame: pd.DataFrame, pnl_col: str) -> list[dict[str, Any]]:
    matrix_cols = [
        col
        for col in ["multi_day_market_state_v4", "theme_regime_state_v4", "intraday_entry_state_v4", "continuation_state_v4"]
        if col in frame.columns
    ]
    if len(matrix_cols) < 2:
        return []
    temp = frame[matrix_cols].copy()
    temp["_net_pct"] = _net_pct(frame[pnl_col])
    temp["_win"] = temp["_net_pct"] > 0
    temp["_entry_reduce"] = pd.to_numeric(frame.get("entry_reduce_failure_flag", pd.Series(dtype=float)), errors="coerce")
    temp["_add_scale"] = pd.to_numeric(frame.get("add_scale_success_flag", pd.Series(dtype=float)), errors="coerce")
    temp["_cell"] = temp[matrix_cols].astype(str).agg(" × ".join, axis=1)
    grouped = (
        temp.groupby("_cell", as_index=False)
        .agg(
            count=("_net_pct", "count"),
            avg_net_pct=("_net_pct", "mean"),
            total_net_pct=("_net_pct", "sum"),
            win_rate=("_win", "mean"),
            entry_reduce_rate=("_entry_reduce", "mean"),
            add_scale_rate=("_add_scale", "mean"),
        )
        .sort_values("total_net_pct", ascending=False)
        .head(80)
    )
    for column in ["win_rate", "entry_reduce_rate", "add_scale_rate"]:
        grouped[column] = grouped[column] * 100.0
    grouped = grouped.rename(columns={"_cell": "key"})
    return grouped.to_dict(orient="records")


COMPOSITE_GROUPS = {
    "market_theme_intraday": [
        "multi_day_market_state_v4",
        "theme_regime_state_v4",
        "intraday_entry_state_v4",
    ],
    "market_theme_intraday_quarter": [
        "multi_day_market_state_v4",
        "theme_regime_state_v4",
        "intraday_entry_state_v4",
        "quarter",
    ],
    "market_theme_intraday_quarter_split": [
        "multi_day_market_state_v4",
        "theme_regime_state_v4",
        "intraday_entry_state_v4",
        "quarter",
        "split_name",
    ],
}


def _load_intraday_symbol(symbol: object) -> pd.DataFrame:
    symbol_text = str(symbol or "").upper()
    if not symbol_text:
        return pd.DataFrame()
    if symbol_text in _INTRADAY_CACHE:
        return _INTRADAY_CACHE[symbol_text]
    path = INTRADAY_RAW_ROOT / f"{symbol_text}.csv"
    frame = _read_csv(path)
    if frame.empty or "timestamp" not in frame.columns:
        _INTRADAY_CACHE[symbol_text] = pd.DataFrame()
        return _INTRADAY_CACHE[symbol_text]
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    for column in ["open", "high", "low", "close", "volume", "vwap"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    if "vwap" not in frame.columns or frame["vwap"].isna().all():
        typical = frame[["high", "low", "close"]].mean(axis=1)
        session_key = frame["timestamp"].dt.date
        pv = typical * frame.get("volume", pd.Series(1.0, index=frame.index)).fillna(0.0)
        cum_pv = pv.groupby(session_key).cumsum()
        cum_vol = frame.get("volume", pd.Series(1.0, index=frame.index)).fillna(0.0).groupby(session_key).cumsum()
        frame["vwap"] = cum_pv / cum_vol.replace(0, pd.NA)
    _INTRADAY_CACHE[symbol_text] = frame
    return frame


def _load_runtime_intraday_symbol(symbol: object, *, db_path: Path = Path("trading.db")) -> pd.DataFrame:
    symbol_text = str(symbol or "").upper()
    if not symbol_text:
        return pd.DataFrame()
    cache_key = f"{db_path}:{symbol_text}"
    if cache_key in _RUNTIME_INTRADAY_CACHE:
        return _RUNTIME_INTRADAY_CACHE[cache_key]
    if not db_path.exists():
        _RUNTIME_INTRADAY_CACHE[cache_key] = pd.DataFrame()
        return _RUNTIME_INTRADAY_CACHE[cache_key]
    con = sqlite3.connect(db_path)
    try:
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='market_bars_5m' LIMIT 1"
        ).fetchone()
        if exists is None:
            _RUNTIME_INTRADAY_CACHE[cache_key] = pd.DataFrame()
            return _RUNTIME_INTRADAY_CACHE[cache_key]
        frame = pd.read_sql_query(
            """
            SELECT
                bar_start_ts AS timestamp,
                open,
                high,
                low,
                close,
                volume,
                tick_count,
                source,
                last_updated_at
            FROM market_bars_5m
            WHERE symbol = ?
            ORDER BY bar_start_ts
            """,
            con,
            params=(symbol_text,),
        )
    finally:
        con.close()
    if frame.empty or "timestamp" not in frame.columns:
        _RUNTIME_INTRADAY_CACHE[cache_key] = pd.DataFrame()
        return _RUNTIME_INTRADAY_CACHE[cache_key]
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp").reset_index(drop=True)
    frame["vwap"] = frame["close"]
    _RUNTIME_INTRADAY_CACHE[cache_key] = frame
    return frame


def _bars_payload(window: pd.DataFrame) -> list[dict[str, Any]]:
    columns = [col for col in ["timestamp", "open", "high", "low", "close", "volume", "vwap"] if col in window.columns]
    bars = window[columns].copy()
    bars["timestamp"] = bars["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return bars.where(pd.notnull(bars), None).to_dict(orient="records")


def _window_around(frame: pd.DataFrame, center_ts: pd.Timestamp, *, before_hours: float, after_hours: float, max_bars: int) -> pd.DataFrame:
    start = center_ts - pd.Timedelta(hours=before_hours)
    end = center_ts + pd.Timedelta(hours=after_hours)
    window = frame[(frame["timestamp"] >= start) & (frame["timestamp"] <= end)].copy()
    if len(window) > max_bars:
        pre = window[window["timestamp"] <= center_ts].tail(max_bars // 2)
        post = window[window["timestamp"] > center_ts].head(max_bars - len(pre))
        window = pd.concat([pre, post], ignore_index=True)
    return window


def _window_from_entry_to_latest(
    frame: pd.DataFrame,
    entry_ts: pd.Timestamp,
    *,
    before_hours: float,
    max_bars: int,
) -> tuple[pd.DataFrame, bool]:
    start = entry_ts - pd.Timedelta(hours=before_hours)
    window = frame[frame["timestamp"] >= start].copy()
    if window.empty:
        return window, False
    lifecycle_window, downsampled = _downsample_lifecycle_window(
        window,
        [entry_ts, window["timestamp"].iloc[-1]],
        max_bars=max_bars,
    )
    return lifecycle_window, downsampled


def _downsample_lifecycle_window(window: pd.DataFrame, required_ts: list[pd.Timestamp], *, max_bars: int) -> tuple[pd.DataFrame, bool]:
    if len(window) <= max_bars:
        return window.copy(), False
    required_indices: set[int] = set()
    for ts in required_ts:
        if pd.isna(ts):
            continue
        distances = (window["timestamp"] - ts).abs()
        if not distances.empty:
            required_indices.add(int(distances.idxmin()))
    stride = max(1, math.ceil(len(window) / max_bars))
    sampled_indices = set(window.iloc[::stride].index.tolist())
    sampled_indices.update(required_indices)
    sampled_indices.add(int(window.index[0]))
    sampled_indices.add(int(window.index[-1]))
    sampled = window.loc[sorted(sampled_indices)].copy()
    if len(sampled) > max_bars + len(required_indices) + 2:
        keep = sorted(required_indices | {int(window.index[0]), int(window.index[-1])})
        filler = [idx for idx in sampled.index.tolist() if idx not in keep]
        allowed_filler = max_bars - len(keep)
        sampled = window.loc[sorted(keep + filler[: max(0, allowed_filler)])].copy()
    return sampled.reset_index(drop=True), True


def _trade_chart_window(row: pd.Series, *, max_bars: int = 180) -> dict[str, Any]:
    symbol = row.get("symbol")
    entry_ts = pd.to_datetime(row.get("entry_ts", row.get("decision_ts_utc")), utc=True, errors="coerce")
    exit_ts = pd.to_datetime(row.get("simulated_exit_ts"), utc=True, errors="coerce")
    source_path = INTRADAY_RAW_ROOT / f"{str(symbol or '').upper()}.csv"
    if pd.isna(entry_ts):
        return {"status": "missing_entry_ts", "source_path": _repo_rel(source_path), "bars": []}
    frame = _load_intraday_symbol(symbol)
    if frame.empty:
        return {"status": "missing_intraday_source", "source_path": _repo_rel(source_path), "bars": []}
    entry_window = _window_around(frame, entry_ts, before_hours=4, after_hours=10, max_bars=max_bars)
    exit_window = pd.DataFrame()
    lifecycle_window = entry_window.copy()
    if pd.notna(exit_ts):
        exit_window = _window_around(frame, exit_ts, before_hours=10, after_hours=4, max_bars=max_bars)
        lifecycle_raw = frame[
            (frame["timestamp"] >= entry_ts - pd.Timedelta(hours=1))
            & (frame["timestamp"] <= exit_ts + pd.Timedelta(hours=1))
        ].copy()
        if not lifecycle_raw.empty:
            lifecycle_window, lifecycle_downsampled = _downsample_lifecycle_window(
                lifecycle_raw,
                [entry_ts, exit_ts],
                max_bars=max_bars,
            )
        else:
            lifecycle_downsampled = False
    else:
        lifecycle_downsampled = False
    if entry_window.empty:
        return {"status": "no_bars_in_entry_window", "source_path": _repo_rel(source_path), "bars": []}
    holding_days = (exit_ts - entry_ts) / pd.Timedelta(days=1) if pd.notna(exit_ts) else None
    long_hold = bool(holding_days is not None and holding_days > 5)
    return {
        "status": "raw_intraday_entry_exit_windows" if long_hold else "raw_intraday_window",
        "source_path": _repo_rel(source_path),
        "source_hash": _sha256_12(source_path),
        "entry_ts": entry_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "exit_ts": None if pd.isna(exit_ts) else exit_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "holding_days": None if holding_days is None else float(holding_days),
        "long_hold_split_flag": long_hold,
        "lifecycle_downsampled_flag": lifecycle_downsampled,
        "lifecycle_bars": _bars_payload(lifecycle_window),
        "entry_bars": _bars_payload(entry_window),
        "exit_bars": [] if exit_window.empty else _bars_payload(exit_window),
        "bars": _bars_payload(lifecycle_window),
    }


def _numeric_flag(value: object) -> int:
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def _indicator_context(snapshot: dict[str, Any] | None, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    decision = decision or {}
    if not snapshot:
        return {
            "indicator_status": "SNAPSHOT_NOT_CAPTURED",
            "regime_status": decision.get("regime_state") or "NOT_CAPTURED_IN_RUNTIME_DB",
            "intraday_status": decision.get("intraday_state") or "NOT_CAPTURED_IN_RUNTIME_DB",
            "runtime_state_capture_status": decision.get("runtime_state_capture_status") or "NOT_CAPTURED_IN_RUNTIME_DB",
            "state_source_snapshot_id": decision.get("state_source_snapshot_id") or "",
        }
    breakout = _numeric_flag(snapshot.get("breakout_condition"))
    ma = _numeric_flag(snapshot.get("ma_condition"))
    entry_allowed = _numeric_flag(snapshot.get("entry_allowed"))
    return {
        "indicator_status": "PRIMARY_RUNTIME_SNAPSHOT",
        "regime_status": decision.get("regime_state") or snapshot.get("regime_state") or "NOT_CAPTURED_IN_RUNTIME_DB",
        "intraday_status": decision.get("intraday_state") or snapshot.get("intraday_state") or "NOT_CAPTURED_IN_RUNTIME_DB",
        "runtime_state_capture_status": decision.get("runtime_state_capture_status") or "NOT_CAPTURED_IN_RUNTIME_DB",
        "state_source_snapshot_id": decision.get("state_source_snapshot_id") or snapshot.get("snapshot_id") or "",
        "entry_signal_state": "ENTRY_ALLOWED" if entry_allowed else "ENTRY_BLOCKED",
        "breakout_state": "BREAKOUT_CONFIRMED" if breakout else "NO_BREAKOUT",
        "ma_trend_state": "MA_TREND_CONFIRMED" if ma else "MA_TREND_BLOCKED",
        "close": snapshot.get("close"),
        "source_price": snapshot.get("source_price"),
        "ma20": snapshot.get("ma20"),
        "ma50": snapshot.get("ma50"),
        "ma200": snapshot.get("ma200"),
        "breakout_high_20": snapshot.get("breakout_high_20"),
        "score": snapshot.get("score"),
        "candidate_rank": snapshot.get("candidate_rank"),
        "freshness_age_sec": snapshot.get("freshness_age_sec"),
        "stale_reason": snapshot.get("stale_reason"),
        "source_type": snapshot.get("source_type"),
        "source_price_ts": snapshot.get("source_price_ts"),
    }


def _paper_entry_context(trades: pd.DataFrame, decisions: pd.DataFrame, snapshots: pd.DataFrame) -> list[dict[str, Any]]:
    if trades.empty:
        return []
    decisions_by_id = (
        {
            str(row.get("decision_id") or ""): row.where(pd.notnull(row), None).to_dict()
            for _, row in decisions.iterrows()
        }
        if not decisions.empty
        else {}
    )
    snapshots_by_id = (
        {
            str(row.get("snapshot_id") or ""): row.where(pd.notnull(row), None).to_dict()
            for _, row in snapshots.iterrows()
        }
        if not snapshots.empty
        else {}
    )
    contexts: list[dict[str, Any]] = []
    for idx, raw in trades.tail(60).iterrows():
        row = raw.where(pd.notnull(raw), None).to_dict()
        decision = decisions_by_id.get(str(row.get("decision_id") or ""), {})
        snapshot = snapshots_by_id.get(str(decision.get("source_snapshot_id") or ""), {})
        symbol = str(row.get("symbol") or decision.get("symbol") or "").upper()
        center_raw = decision.get("source_price_ts") or snapshot.get("source_price_ts") or row.get("created_at")
        center = pd.to_datetime(center_raw, utc=True, errors="coerce")
        raw_source_path = INTRADAY_RAW_ROOT / f"{symbol}.csv"
        runtime_frame = _load_runtime_intraday_symbol(symbol)
        raw_frame = pd.DataFrame() if not runtime_frame.empty else _load_intraday_symbol(symbol)
        frame = runtime_frame if not runtime_frame.empty else raw_frame
        source_kind = "trading_db_market_bars_5m" if not runtime_frame.empty else "raw_us_intraday_csv"
        source_path = Path("trading.db::market_bars_5m") if not runtime_frame.empty else raw_source_path
        if symbol and not frame.empty and pd.notna(center):
            lifecycle_window, lifecycle_downsampled = _window_from_entry_to_latest(
                frame,
                center,
                before_hours=1.5,
                max_bars=180,
            )
            entry_window = _window_around(frame, center, before_hours=1.5, after_hours=1.5, max_bars=80)
            latest_bar = lifecycle_window.iloc[-1].to_dict() if not lifecycle_window.empty else {}
            chart_window = {
                "status": "ENTRY_TO_LATEST_HOLDING_WINDOW" if not lifecycle_window.empty else "OHLC_WINDOW_EMPTY_FOR_DECISION_TIME",
                "symbol": symbol,
                "entry_ts": center.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "decision_ts": row.get("created_at"),
                "current_ts": latest_bar.get("timestamp").strftime("%Y-%m-%dT%H:%M:%SZ") if latest_bar and pd.notna(latest_bar.get("timestamp")) else "",
                "current_price": latest_bar.get("close"),
                "holding_days_to_current": float((latest_bar.get("timestamp") - center) / pd.Timedelta(days=1)) if latest_bar and pd.notna(latest_bar.get("timestamp")) else None,
                "lifecycle_downsampled_flag": lifecycle_downsampled,
                "long_hold_split_flag": True,
                "lifecycle_bars": _bars_payload(lifecycle_window),
                "entry_bars": _bars_payload(entry_window),
                "exit_bars": [],
                "bars": _bars_payload(lifecycle_window),
                "source_type": source_kind,
                "source_path": _repo_rel(source_path),
                "source_hash": _sha256_12(raw_source_path) if source_kind == "raw_us_intraday_csv" else _sha256_12(Path("trading.db")),
            }
        else:
            chart_window = {
                "status": "OHLC_WINDOW_MISSING",
                "symbol": symbol,
                "entry_ts": str(center_raw or ""),
                "bars": [],
                "source_type": source_kind if symbol else "",
                "source_path": _repo_rel(source_path) if symbol else "",
                "source_hash": "",
            }
        contexts.append(
            {
                "key": row.get("order_id") or row.get("decision_id") or f"paper-entry-{idx}",
                "trade": row,
                "decision": decision,
                "indicator_context": _indicator_context(snapshot, decision),
                "chart_window": chart_window,
            }
        )
    return contexts


def _safe_float_or_none(value: object) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    except Exception:
        return None


def _safe_int(value: object) -> int:
    try:
        if value in (None, "") or pd.isna(value):
            return 0
        return int(float(value))
    except Exception:
        return 0


def _latest_row_by_time(frame: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    if frame.empty:
        return {}
    for column in columns:
        if column not in frame.columns:
            continue
        sortable = frame.copy()
        sortable["_sort_ts"] = pd.to_datetime(sortable[column], utc=True, errors="coerce")
        sortable = sortable.loc[sortable["_sort_ts"].notna()].sort_values("_sort_ts")
        if not sortable.empty:
            return sortable.iloc[-1].drop(labels=["_sort_ts"]).to_dict()
    return frame.iloc[-1].to_dict()


def _timestamp_after(left: object, right: object) -> bool:
    left_ts = pd.to_datetime(left, utc=True, errors="coerce")
    right_ts = pd.to_datetime(right, utc=True, errors="coerce")
    if pd.isna(left_ts) or pd.isna(right_ts):
        return False
    return bool(left_ts > right_ts)


def _trade_key(row: dict[str, Any], idx: int = 0) -> str:
    return str(row.get("order_id") or row.get("decision_id") or row.get("lifecycle_id") or f"paper-trade-{idx}")


def _paper_reason_ko(value: object) -> str:
    text = str(value or "").upper().replace("_", " ").strip()
    known = {
        "BREAKOUT + MA TREND": "돌파 + 이동평균 추세",
        "BREAKOUT + MA_TREND": "돌파 + 이동평균 추세",
        "ORDER FILLED": "체결 완료",
        "ORDER SUBMITTED": "주문 제출",
        "RUNTIME SIGNAL SELECTED": "런타임 신호 선택",
        "PAPER ORDER CANDIDATE": "모의주문 후보",
    }
    return known.get(text, str(value or "체결 조건"))


def _paper_trade_detail_view(
    trades: pd.DataFrame,
    entry_context: list[dict[str, Any]],
    open_positions: pd.DataFrame,
) -> list[dict[str, Any]]:
    if trades.empty:
        return []
    context_by_key: dict[str, dict[str, Any]] = {}
    context_by_decision: dict[str, dict[str, Any]] = {}
    for idx, context in enumerate(entry_context):
        trade = context.get("trade") or {}
        key = _trade_key(trade, idx)
        context_by_key[key] = context
        decision_id = str(trade.get("decision_id") or context.get("decision", {}).get("decision_id") or "")
        if decision_id:
            context_by_decision[decision_id] = context

    position_pool = []
    if not open_positions.empty:
        for _, raw in open_positions.iterrows():
            position_pool.append(raw.where(pd.notnull(raw), None).to_dict())
    used_positions: set[int] = set()

    views: list[dict[str, Any]] = []
    sorted_trades = trades.sort_values("filled_at" if "filled_at" in trades.columns else "created_at", ascending=False)
    for idx, raw in enumerate(sorted_trades.to_dict(orient="records")):
        row = {key: (None if pd.isna(value) else value) for key, value in raw.items()}
        context = context_by_key.get(_trade_key(row, idx)) or context_by_decision.get(str(row.get("decision_id") or "")) or {}
        chart_window = context.get("chart_window") or {}
        indicator = context.get("indicator_context") or {}
        symbol = str(row.get("symbol") or chart_window.get("symbol") or "").upper()
        qty = _safe_float_or_none(row.get("filled_qty") or row.get("quantity")) or 0.0
        entry_price = _safe_float_or_none(row.get("filled_avg_price") or row.get("limit_price"))
        current_price = _safe_float_or_none(chart_window.get("current_price"))
        if current_price is None:
            current_price = _safe_float_or_none(row.get("mark_price"))

        matched_position: dict[str, Any] = {}
        best_idx: int | None = None
        trade_order_id = str(row.get("order_id") or "")
        trade_fill_id = str(row.get("fill_id") or row.get("entry_fill_id") or "")
        for pos_idx, position in enumerate(position_pool):
            if pos_idx in used_positions:
                continue
            pos_order_id = str(position.get("entry_order_id") or "")
            pos_fill_id = str(position.get("entry_fill_id") or "")
            exact_fill_match = bool(trade_fill_id and pos_fill_id and trade_fill_id == pos_fill_id)
            exact_order_match = bool(trade_order_id and pos_order_id and trade_order_id == pos_order_id)
            if not exact_fill_match and not exact_order_match:
                continue
            matched_position = position
            best_idx = pos_idx
            break
        if best_idx is not None:
            used_positions.add(best_idx)

        position_qty = _safe_float_or_none(matched_position.get("open_qty")) or qty
        if current_price is None:
            current_price = _safe_float_or_none(matched_position.get("mark_price"))
        entry_amount = position_qty * entry_price if entry_price is not None else None
        market_value = position_qty * current_price if current_price is not None else None
        pnl = _safe_float_or_none(matched_position.get("mtm_proxy_pnl_usd"))
        if pnl is None and entry_amount is not None and market_value is not None:
            pnl = market_value - entry_amount
        pnl_pct = (pnl / entry_amount * 100.0) if pnl is not None and entry_amount else None
        reason = str(row.get("reason_detail") or row.get("reason_code") or "ORDER_FILLED")
        reason_ko = _paper_reason_ko(reason)
        missing_evidence = []
        if indicator.get("indicator_status") == "SNAPSHOT_NOT_CAPTURED":
            missing_evidence.append("indicator_snapshot")
        if indicator.get("runtime_state_capture_status") == "NOT_CAPTURED_IN_RUNTIME_DB":
            missing_evidence.append("runtime_state")
        if not matched_position:
            missing_evidence.append("exact_position_link")
        view = {
            "view_contract": "paper_trade_detail_view_v1",
            "trade_id": _trade_key(row, idx),
            "position_id": str(matched_position.get("entry_order_id") or row.get("order_id") or row.get("decision_id") or ""),
            "symbol": symbol,
            "side": row.get("side") or "BUY",
            "status": row.get("order_status") or "FILLED",
            "entry_at": row.get("filled_at") or row.get("created_at") or chart_window.get("entry_ts"),
            "entry_price": entry_price,
            "entry_amount": entry_amount,
            "quantity": position_qty,
            "current_at": chart_window.get("current_ts"),
            "current_price": current_price,
            "market_value": market_value,
            "unrealized_pnl_usd": pnl,
            "unrealized_pnl_pct": pnl_pct,
            "holding_days": chart_window.get("holding_days_to_current"),
            "decision_reason_ko": f"{symbol}는 {reason_ko} 조건으로 모의주문 후보가 됐고 실제 체결 내역으로 확인됐다.",
            "post_entry_summary_ko": (
                f"체결가 {entry_price:.2f}에서 현재가 {current_price:.2f}까지 보유 경로를 추적한다."
                if entry_price is not None and current_price is not None
                else "체결 후 현재까지 가격 경로를 추적한다."
            ),
            "risk_note_ko": "현재 손익은 보유 중인 포지션의 평가손익이며 실현손익과 분리한다.",
            "chart": {
                "bars": chart_window.get("lifecycle_bars") or chart_window.get("bars") or [],
                "entry_bars": chart_window.get("entry_bars") or [],
                "overlays": {
                    "entry": {"at": chart_window.get("entry_ts"), "price": entry_price},
                    "fill": {"at": row.get("filled_at") or row.get("created_at"), "price": entry_price},
                    "current": {"at": chart_window.get("current_ts"), "price": current_price},
                    "limit": {"at": row.get("created_at"), "price": _safe_float_or_none(row.get("limit_price"))},
                },
                "status": chart_window.get("status") or "OHLC_WINDOW_MISSING",
                "source_type": chart_window.get("source_type"),
                "source_path": chart_window.get("source_path"),
                "source_hash": chart_window.get("source_hash"),
            },
            "evidence": {
                "decision_id": row.get("decision_id"),
                "order_id": row.get("order_id"),
                "fill_id": row.get("fill_id"),
                "lifecycle_id": row.get("lifecycle_id"),
                "reason_code": row.get("reason_code"),
                "indicator": indicator,
                "raw_trade": row,
                "position_matching_policy": "EXACT_ORDER_OR_FILL_ID_ONLY",
                "position_link_status": "EXACT_MATCHED" if matched_position else "UNMATCHED_EXACT_ID_ONLY",
                "proximity_fallback_used_flag": 0,
                "source_disclosure_default_visible": False,
            },
            "evidence_quality": "PARTIAL_RUNTIME_EVIDENCE" if missing_evidence else "COMPLETE_RUNTIME_EVIDENCE",
            "missing_evidence": missing_evidence,
        }
        views.append(view)
    return views


def _performance_sources(catalog: pd.DataFrame) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for task in catalog.to_dict(orient="records"):
        artifact_dir = Path(str(task.get("artifact_dir", "")))
        manifest = load_artifact_manifest(artifact_dir)
        if manifest.empty:
            continue
        for item in manifest.to_dict(orient="records"):
            rel = item.get("relative_path") or item.get("path")
            if not rel or not str(rel).endswith(".csv"):
                continue
            rel_name = str(rel).lower()
            if rel_name.endswith("_sample.csv") or "_audit" in rel_name or "decision" in rel_name:
                continue
            path = artifact_dir / str(rel)
            frame = _read_csv(path)
            pnl_col = _pnl_column(frame)
            if frame.empty or pnl_col is None:
                continue
            net = _net_pct(frame[pnl_col])
            wins = net > 0
            symbol_count = int(frame["symbol"].nunique()) if "symbol" in frame.columns else 0
            sources.append(
                {
                    "task_id": task.get("task_id"),
                    "task_name": task.get("task_name"),
                    "owner_team": task.get("owner_team"),
                    "artifact": str(rel),
                    "artifact_path": _repo_rel(path),
                    "pnl_column": pnl_col,
                    "strategy_acceptance": task.get("strategy_acceptance"),
                    "data_readiness": task.get("data_readiness"),
                    "source_hash": _sha256_12(path),
                    "modified_utc": _file_meta(path)["modified_utc"],
                    "count": int(net.count()),
                    "symbol_count": symbol_count,
                    "avg_net_pct": float(net.mean()) if net.count() else 0.0,
                    "total_net_pct": float(net.sum()) if net.count() else 0.0,
                    "win_rate": float(wins.mean() * 100.0) if net.count() else 0.0,
                    "max_dd_pp": _drawdown_pp(net),
                    "entry_reduce_rate": _bool_rate(frame, "entry_reduce_failure_flag"),
                    "add_scale_rate": _bool_rate(frame, "add_scale_success_flag"),
                    "false_positive_rate": _bool_rate(frame, "false_positive_flag"),
                    "group_columns": [
                        col
                        for col in [
                            "candidate_strategy_name",
                            "selected_goal_portfolio_name",
                            "policy_name",
                            "multi_day_market_state_v4",
                            "theme_regime_state_v4",
                            "symbol_multiday_setup_state",
                            "intraday_entry_state_v4",
                            "continuation_state_v4",
                            "microstructure_state_v4",
                            "quarter",
                            "split_name",
                            "symbol",
                            "theme_id",
                        ]
                        if col in frame.columns
                    ],
                }
            )
    sources.sort(key=lambda row: (str(row.get("modified_utc") or ""), int(row.get("count") or 0)))
    return sources


def _sample_trade_frame(frame: pd.DataFrame, *, max_rows: int = 1200) -> tuple[pd.DataFrame, dict[str, Any]]:
    if frame.empty or len(frame) <= max_rows or "symbol" not in frame.columns:
        return frame.copy(), {
            "sample_policy": "full" if len(frame) <= max_rows else "unbalanced_no_symbol",
            "full_trade_count": int(len(frame)),
            "sample_trade_count": int(len(frame)),
            "full_symbol_count": int(frame["symbol"].nunique()) if "symbol" in frame.columns else 0,
            "sample_symbol_count": int(frame["symbol"].nunique()) if "symbol" in frame.columns else 0,
        }
    sort_cols = [col for col in ["symbol", "entry_ts", "decision_ts_utc", "lifecycle_id"] if col in frame.columns]
    sorted_frame = frame.sort_values(sort_cols).copy() if sort_cols else frame.copy()
    symbols = sorted_frame["symbol"].dropna().astype(str).unique().tolist()
    per_symbol_cap = max(1, max_rows // max(len(symbols), 1))
    sampled_parts: list[pd.DataFrame] = []
    for _, group in sorted_frame.groupby("symbol", sort=False):
        if len(group) <= per_symbol_cap:
            sampled_parts.append(group)
            continue
        positions = sorted(set(round(i) for i in pd.Series(range(per_symbol_cap)) * ((len(group) - 1) / max(per_symbol_cap - 1, 1))))
        sampled_parts.append(group.iloc[positions])
    sampled = pd.concat(sampled_parts).drop_duplicates().head(max_rows).copy()
    return sampled, {
        "sample_policy": "symbol_balanced_even_time",
        "full_trade_count": int(len(frame)),
        "sample_trade_count": int(len(sampled)),
        "full_symbol_count": int(frame["symbol"].nunique()),
        "sample_symbol_count": int(sampled["symbol"].nunique()),
        "per_symbol_cap": int(per_symbol_cap),
    }


def _task_cards(catalog: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in catalog.to_dict(orient="records"):
        decision_path = Path(str(task.get("decision_path", "")))
        report_path = Path(str(task.get("report_path", "")))
        decision = _read_decision(decision_path)
        status = next((str(decision[key]) for key in STATUS_FIELDS if key in decision and pd.notna(decision[key])), "")
        rows.append(
            {
                "task_id": task.get("task_id"),
                "task_name": task.get("task_name"),
                "owner_team": task.get("owner_team"),
                "strategy_acceptance": task.get("strategy_acceptance"),
                "data_readiness": task.get("data_readiness"),
                "review_status": task.get("review_status"),
                "upstream_task": task.get("upstream_task"),
                "decision_status": status or task.get("strategy_acceptance"),
                "report": _file_meta(report_path),
                "decision": _file_meta(decision_path),
                "artifact_dir": str(task.get("artifact_dir", "")),
                "blocker_hint": task.get("blocker_hint"),
            }
        )
    return rows


def _paper_ops_payload() -> dict[str, Any]:
    report_dir = Path("docs/reports/task_582_kis_paper_trading_bridge")
    report_583 = Path("docs/reports/task_583_live_signal_refresh_repair")
    report_584 = Path("docs/reports/task_584_runtime_strategy_decision_gate")
    report_585 = Path("docs/reports/task_585_kis_paper_order_execution")
    report_587 = Path("docs/reports/task_587_slack_trading_report_integration")
    report_588 = Path("docs/reports/task_588_kis_paper_market_hours_runtime_loop")
    report_589 = Path("docs/reports/task_589_nasdaq_paper_ops_hardening")
    report_597 = Path("docs/reports/task_597_frontend_backend_paper_ops_triage")
    readiness_registry = build_readiness_registry_payload()
    files = {
        "decision": report_dir / "task_582_decision.csv",
        "run_log": report_dir / "paper_trading_run_log.csv",
        "connection": report_dir / "kis_paper_connection_audit.csv",
        "orders": report_dir / "paper_order_lineage_recent.csv",
        "fills": report_dir / "paper_fill_lineage_recent.csv",
        "continuation": report_dir / "paper_continuation_event_recent.csv",
        "slack": report_dir / "paper_slack_notification_audit.csv",
    }
    task583_freshness = _read_csv(report_583 / "indicator_snapshot_freshness_audit.csv")
    task583_candidates = _read_csv(report_583 / "runtime_candidate_audit.csv")
    task583_stale_scoreboard = _read_csv(report_583 / "runtime_stale_source_closure_scoreboard.csv")
    task584_runtime = _read_csv(report_584 / "runtime_strategy_decision_log.csv")
    task584_no_trade = _read_csv(report_584 / "runtime_no_trade_reason_audit.csv")
    task584_no_trade_decomposition = _read_csv(report_584 / "runtime_no_trade_decomposition_audit.csv")
    task589_summary = _read_csv(report_589 / "paper_eod_summary.csv")
    task589_trade_detail = _read_csv(report_589 / "paper_eod_trade_detail.csv")
    task589_filled_trade_history = _read_csv(report_589 / "paper_eod_filled_trade_history.csv")
    task589_filled_decision_evidence = _read_csv(report_589 / "paper_eod_filled_decision_evidence.csv")
    task589_decision_evidence = _read_csv(report_589 / "paper_eod_decision_evidence.csv")
    task589_indicator_snapshot = _read_csv(report_589 / "paper_eod_indicator_snapshot_evidence.csv")
    task589_open_positions = _read_csv(report_589 / "paper_eod_open_position_proxy.csv")
    task589_realized_pnl = _read_csv(report_589 / "paper_eod_realized_pnl.csv")
    task589_slack_audit = _read_csv(report_589 / "paper_eod_slack_audit.csv")
    task589_fill_price_repair = _read_csv(report_589 / "paper_eod_fill_price_repair_audit.csv")
    task597_promotion_scorecard = _read_csv(report_597 / "promotion_scorecard_refresh.csv")
    task589_entry_context = _paper_entry_context(
        task589_filled_trade_history if not task589_filled_trade_history.empty else task589_trade_detail,
        task589_filled_decision_evidence if not task589_filled_decision_evidence.empty else task589_decision_evidence,
        task589_indicator_snapshot,
    )
    task589_trade_detail_view = _paper_trade_detail_view(
        task589_filled_trade_history if not task589_filled_trade_history.empty else task589_trade_detail,
        task589_entry_context,
        task589_open_positions,
    )
    latest_freshness = _latest_row_by_time(task583_freshness, ["audit_ts_utc", "latest_snapshot_created_at"])
    latest_runtime = _latest_row_by_time(task584_runtime, ["created_at"])
    latest_eod = _latest_row_by_time(task589_summary, ["generated_utc", "session_date_et"])
    latest_eod_slack = _latest_row_by_time(task589_slack_audit, ["created_at_utc"])

    def safe_float(value: object) -> float:
        try:
            if value is None or pd.isna(value):
                return 0.0
            return float(value)
        except Exception:
            return 0.0

    canonical_source = "Task589 EOD summary" if latest_eod else "Task583 freshness fallback"
    expected = _safe_int(latest_eod.get("expected_universe_count") or latest_freshness.get("expected_universe_count") or 0)
    evaluated = _safe_int(latest_eod.get("evaluated_symbol_count") or latest_freshness.get("evaluated_symbol_count") or 0)
    fresh = _safe_int(latest_eod.get("fresh_symbol_count") or latest_freshness.get("fresh_symbol_count") or 0)
    selected = _safe_int(latest_eod.get("selected_symbol_count") or latest_freshness.get("selected_symbol_count") or 0)
    missing_or_stale = _safe_int(latest_eod.get("missing_or_stale_symbol_count") or latest_freshness.get("missing_or_stale_symbol_count") or 0)
    coverage_status = str(latest_eod.get("universe_coverage_status") or latest_freshness.get("coverage_status") or "UNKNOWN_BLOCKER")
    eod_generated_utc = latest_eod.get("generated_utc") or latest_eod_slack.get("created_at_utc") or ""
    freshness_audit_utc = latest_freshness.get("audit_ts_utc") or ""
    eod_stale_against_refresh = bool(latest_eod and _timestamp_after(freshness_audit_utc, eod_generated_utc))
    fill_price_unrepairable_rows = _safe_int(latest_eod.get("fill_price_unrepairable_rows") or 0)
    fill_price_active_blocker_value = latest_eod.get("fill_price_active_blocker_rows")
    fill_price_active_blocker_rows = (
        _safe_int(fill_price_active_blocker_value)
        if fill_price_active_blocker_value not in (None, "")
        else fill_price_unrepairable_rows
    )
    fill_price_quarantined_rows = _safe_int(latest_eod.get("fill_price_quarantined_rows") or 0)
    scorecard_statuses = (
        task597_promotion_scorecard.get("status", pd.Series(dtype=str)).fillna("").astype(str).str.upper().tolist()
        if not task597_promotion_scorecard.empty
        else []
    )
    scorecard_blocked = any("BLOCKED" in status or "NOT_ACCEPTED" in status for status in scorecard_statuses)
    slack_send_status = str(latest_eod.get("slack_send_status") or latest_eod_slack.get("send_status") or "")
    slack_dry_run_only = slack_send_status == "DRY_RUN_NOT_SENT"
    freshness_mismatch = bool(
        latest_eod
        and latest_freshness
        and (
            _safe_int(latest_freshness.get("expected_universe_count")) != expected
            or _safe_int(latest_freshness.get("evaluated_symbol_count")) != evaluated
            or _safe_int(latest_freshness.get("fresh_symbol_count")) != fresh
            or _safe_int(latest_freshness.get("missing_or_stale_symbol_count")) != missing_or_stale
        )
    )
    warning_priority = [
        "PAPER_READY_BLOCKED",
        "SOURCE_STALE_BLOCKER",
        "UNPRICED_FILL_BLOCKER",
        "FIRM_GRADE_REPLAY_BLOCKER",
        "SLACK_DRY_RUN_ONLY",
        "EOD_STALE_AGAINST_REFRESH",
        "CANONICAL_MISMATCH",
        "UNIVERSE_COVERAGE_GAP",
        "STALE_EOD_CLOSEOUT",
        "DIAGNOSTIC_ONLY",
        "MISSING_RUNTIME_CAPTURE",
        "PROXY_PNL",
    ]
    warning_codes: list[str] = []
    readiness_blockers: list[dict[str, str]] = []
    deployment_blockers: list[dict[str, str]] = []
    if missing_or_stale > 0:
        warning_codes.append("SOURCE_STALE_BLOCKER")
        readiness_blockers.append(
            {
                "priority": "P0",
                "owner_team": "Data & Market Microstructure",
                "owner_name": "윤헌",
                "blocker_code": "SOURCE_STALE_BLOCKER",
                "evidence": f"{missing_or_stale} symbols missing or stale in canonical EOD coverage",
                "required_fix": "Close Task583 stale source scoreboard with live/raw source evidence for every expected symbol.",
            }
        )
    if fill_price_active_blocker_rows > 0:
        warning_codes.append("UNPRICED_FILL_BLOCKER")
        readiness_blockers.append(
            {
                "priority": "P0",
                "owner_team": "Execution & Risk",
                "owner_name": "주은",
                "blocker_code": "UNPRICED_FILL_BLOCKER",
                "evidence": f"{fill_price_active_blocker_rows} current-session fill rows have no exact broker fill price repair path",
                "required_fix": "Recover exact broker execution price by order_id/fill_id or mark the account run non-promotable.",
            }
        )
    if scorecard_blocked:
        warning_codes.append("FIRM_GRADE_REPLAY_BLOCKER")
        deployment_blockers.append(
            {
                "priority": "P0",
                "owner_team": "Backtest & Simulation Infra",
                "owner_name": "동승",
                "blocker_code": "FIRM_GRADE_REPLAY_BLOCKER",
                "evidence": "promotion scorecard still contains BLOCKED or NOT_ACCEPTED status",
                "required_fix": "Complete deterministic replay / OOS / artifact audit acceptance before any deployment or strategy-acceptance claim.",
            }
        )
    if slack_dry_run_only:
        warning_codes.append("SLACK_DRY_RUN_ONLY")
        readiness_blockers.append(
            {
                "priority": "P1",
                "owner_team": "Research Governance",
                "owner_name": "서연",
                "blocker_code": "SLACK_DRY_RUN_ONLY",
                "evidence": "latest EOD Slack audit is DRY_RUN_NOT_SENT",
                "required_fix": "Run a real Slack delivery audit or keep communication readiness blocked.",
            }
        )
    if eod_stale_against_refresh:
        warning_codes.append("EOD_STALE_AGAINST_REFRESH")
    if freshness_mismatch:
        warning_codes.append("CANONICAL_MISMATCH")
    if coverage_status == "UNIVERSE_COVERAGE_GAP" or (expected and evaluated < expected):
        warning_codes.append("UNIVERSE_COVERAGE_GAP")
    if str(latest_eod.get("freshness_gap_status") or "") == "STALE_EOD_CLOSEOUT":
        warning_codes.append("STALE_EOD_CLOSEOUT")
    if str(latest_eod.get("diagnostic_only_flag") or latest_runtime.get("diagnostic_only_flag") or "1") in {"1", "1.0", "True", "true"}:
        warning_codes.append("DIAGNOSTIC_ONLY")
    if str(latest_runtime.get("runtime_state_capture_status") or "") != "CAPTURED":
        warning_codes.append("MISSING_RUNTIME_CAPTURE")
    if safe_float(latest_eod.get("mtm_proxy_pnl_usd") or 0.0) != 0.0 or _safe_int(latest_eod.get("open_position_rows") or 0) > 0:
        warning_codes.append("PROXY_PNL")
    if readiness_blockers:
        warning_codes.append("PAPER_READY_BLOCKED")
    warning_codes = [code for code in warning_priority if code in set(warning_codes)]
    paper_readiness_gate = {
        "paper_ready_flag": 0 if readiness_blockers else 1,
        "paper_readiness_status": "BLOCKED" if readiness_blockers else "READY_FOR_CONTROLLED_PAPER_RUN",
        "blocker_count": len(readiness_blockers),
        "blockers": readiness_blockers,
        "deployment_blocker_count": len(deployment_blockers),
        "deployment_blockers": deployment_blockers,
        "reviewer_name": "필수",
        "review_rule": "Paper-ready requires source coverage, active-session exact fill pricing, and delivery audit. Deployment remains blocked until firm-grade replay governance passes.",
    }
    source_diagnostics = {
        "warning_priority": warning_priority,
        "warning_codes": warning_codes,
        "paper_ready_flag": paper_readiness_gate["paper_ready_flag"],
        "paper_readiness_status": paper_readiness_gate["paper_readiness_status"],
        "paper_readiness_blocker_count": paper_readiness_gate["blocker_count"],
        "fill_price_unrepairable_rows": fill_price_unrepairable_rows,
        "fill_price_active_blocker_rows": fill_price_active_blocker_rows,
        "fill_price_quarantined_rows": fill_price_quarantined_rows,
        "fill_price_integrity_status": latest_eod.get("fill_price_integrity_status") or "",
        "scorecard_blocked_flag": int(scorecard_blocked),
        "slack_dry_run_only_flag": int(slack_dry_run_only),
        "latest_catalog_generated_time": datetime.now(UTC).isoformat(),
        "task583_freshness_audit_utc": freshness_audit_utc,
        "task589_eod_generated_utc": eod_generated_utc,
        "eod_stale_against_refresh_flag": int(eod_stale_against_refresh),
        "latest_runtime_decision": latest_runtime.get("created_at") or latest_runtime.get("decision_id") or "",
        "latest_eod_session": latest_eod.get("session_date_et") or "",
        "trade_rows_count": int(len(task589_trade_detail)),
        "filled_trade_history_rows_count": int(len(task589_filled_trade_history)),
        "trade_detail_view_rows_count": int(len(task589_trade_detail_view)),
        "canonical_universe_source": canonical_source,
        "canonical_freshness_mismatch_flag": int(freshness_mismatch),
        "session_trade_scope": latest_eod.get("session_trade_scope") or "CURRENT_SESSION_ONLY",
        "cumulative_account_scope": latest_eod.get("cumulative_account_scope") or "CUMULATIVE_BROKER_TRUTH_FILLS",
        "account_truth_source": latest_eod.get("account_truth_source") or "",
        "position_sync_status": latest_eod.get("position_sync_status") or "",
        "current_session_trade_status": latest_eod.get("current_session_trade_status") or "",
        "empty_sources": [
            key
            for key, frame in {
            "Task583 freshness": task583_freshness,
            "Task583 runtime candidates": task583_candidates,
            "Task583 stale source scoreboard": task583_stale_scoreboard,
            "Task584 runtime decision": task584_runtime,
            "Task584 no-trade decomposition": task584_no_trade_decomposition,
            "Task589 EOD summary": task589_summary,
            "Task589 trade detail": task589_trade_detail,
            "Task589 filled trade history": task589_filled_trade_history,
            "Task589 filled decision evidence": task589_filled_decision_evidence,
            "Task589 fill price repair audit": task589_fill_price_repair,
            "Task589 trade detail view": pd.DataFrame(task589_trade_detail_view),
            "Task597 promotion scorecard": task597_promotion_scorecard,
            }.items()
            if frame.empty
        ],
    }
    universe_coverage = {
        "universe_scope": latest_eod.get("universe_scope") or latest_freshness.get("universe_scope") or "theme_10x7",
        "expected_universe_count": expected,
        "evaluated_symbol_count": evaluated,
        "fresh_symbol_count": fresh,
        "selected_symbol_count": selected,
        "missing_or_stale_symbol_count": missing_or_stale,
        "coverage_status": coverage_status,
        "canonical_source": canonical_source,
        "symbol_status_counts": task583_candidates.get("symbol_status", pd.Series(dtype=str)).astype(str).value_counts().to_dict()
        if not task583_candidates.empty
        else {},
    }
    payload: dict[str, Any] = {
        "source_task": "Task582",
        "source_dir": str(report_dir),
        "files": {name: _file_meta(path) for name, path in files.items()},
        "decision": _read_decision(files["decision"]),
        "v2": {
            "source_tasks": ["Task583", "Task584", "Task585", "Task587", "Task588", "Task589"],
            "readiness_registry": readiness_registry,
            "universe_coverage": universe_coverage,
            "source_diagnostics": source_diagnostics,
            "paper_readiness_gate": paper_readiness_gate,
            "files": {
                "task583_decision": _file_meta(report_583 / "task_583_decision.csv"),
                "task583_freshness": _file_meta(report_583 / "indicator_snapshot_freshness_audit.csv"),
                "task583_candidates": _file_meta(report_583 / "runtime_candidate_audit.csv"),
                "task583_stale_scoreboard": _file_meta(report_583 / "runtime_stale_source_closure_scoreboard.csv"),
                "task584_decision": _file_meta(report_584 / "task_584_decision.csv"),
                "task584_runtime_decision": _file_meta(report_584 / "runtime_strategy_decision_log.csv"),
                "task584_no_trade": _file_meta(report_584 / "runtime_no_trade_reason_audit.csv"),
                "task584_no_trade_decomposition": _file_meta(report_584 / "runtime_no_trade_decomposition_audit.csv"),
                "task585_decision": _file_meta(report_585 / "task_585_decision.csv"),
                "task585_execution": _file_meta(report_585 / "paper_order_execution_log.csv"),
                "task585_active_refresh": _file_meta(report_585 / "paper_active_order_status_refresh.csv"),
                "task585_lineage": _file_meta(report_585 / "paper_order_fill_lineage.csv"),
                "task585_lifecycle": _file_meta(report_585 / "paper_lifecycle_event_log.csv"),
                "task587_decision": _file_meta(report_587 / "task_587_decision.csv"),
                "task587_slack": _file_meta(report_587 / "slack_trading_notification_audit.csv"),
                "task588_decision": _file_meta(report_588 / "task_588_decision.csv"),
                "task588_loop_log": _file_meta(report_588 / "paper_runtime_loop_log.csv"),
                "task588_latest_status": _file_meta(report_588 / "paper_runtime_loop_latest_status.csv"),
                "task588_supervisor": _file_meta(report_588 / "nasdaq_paper_supervisor_status.csv"),
                "task589_eod_summary": _file_meta(report_589 / "paper_eod_summary.csv"),
                "task589_filled_trade_history": _file_meta(report_589 / "paper_eod_filled_trade_history.csv"),
                "task589_filled_decision_evidence": _file_meta(report_589 / "paper_eod_filled_decision_evidence.csv"),
                "task589_indicator_snapshot": _file_meta(report_589 / "paper_eod_indicator_snapshot_evidence.csv"),
                "task589_realized_pnl": _file_meta(report_589 / "paper_eod_realized_pnl.csv"),
                "task589_fill_price_repair": _file_meta(report_589 / "paper_eod_fill_price_repair_audit.csv"),
                "task589_eod_slack": _file_meta(report_589 / "paper_eod_slack_audit.csv"),
                "task589_supervisor_alert": _file_meta(report_589 / "supervisor_failure_alert_audit.csv"),
                "task597_promotion_scorecard": _file_meta(report_597 / "promotion_scorecard_refresh.csv"),
            },
            "signal_refresh": {
                "decision": _read_decision(report_583 / "task_583_decision.csv"),
                "freshness": task583_freshness.where(pd.notnull(task583_freshness), None).to_dict(orient="records"),
                "candidates": task583_candidates.head(70).where(pd.notnull(task583_candidates.head(70)), None).to_dict(orient="records"),
                "stale_source_scoreboard": task583_stale_scoreboard.where(
                    pd.notnull(task583_stale_scoreboard), None
                ).to_dict(orient="records"),
            },
            "runtime_decision": {
                "decision": _read_decision(report_584 / "task_584_decision.csv"),
                "log": task584_runtime.where(pd.notnull(task584_runtime), None).to_dict(orient="records"),
                "no_trade": task584_no_trade.where(pd.notnull(task584_no_trade), None).to_dict(orient="records"),
                "no_trade_decomposition": task584_no_trade_decomposition.where(
                    pd.notnull(task584_no_trade_decomposition), None
                ).to_dict(orient="records"),
            },
            "order_execution": {
                "decision": _read_decision(report_585 / "task_585_decision.csv"),
                "log": _read_csv(report_585 / "paper_order_execution_log.csv").where(
                    pd.notnull(_read_csv(report_585 / "paper_order_execution_log.csv")), None
                ).to_dict(orient="records"),
                "active_refresh": _read_csv(report_585 / "paper_active_order_status_refresh.csv").where(
                    pd.notnull(_read_csv(report_585 / "paper_active_order_status_refresh.csv")), None
                ).to_dict(orient="records"),
                "lineage": _read_csv(report_585 / "paper_order_fill_lineage.csv").head(30).where(
                    pd.notnull(_read_csv(report_585 / "paper_order_fill_lineage.csv").head(30)), None
                ).to_dict(orient="records"),
                "lifecycle": _read_csv(report_585 / "paper_lifecycle_event_log.csv").head(30).where(
                    pd.notnull(_read_csv(report_585 / "paper_lifecycle_event_log.csv").head(30)), None
                ).to_dict(orient="records"),
            },
            "slack_report": {
                "decision": _read_decision(report_587 / "task_587_decision.csv"),
                "audit": _read_csv(report_587 / "slack_trading_notification_audit.csv").where(
                    pd.notnull(_read_csv(report_587 / "slack_trading_notification_audit.csv")), None
                ).to_dict(orient="records"),
            },
            "runtime_loop": {
                "decision": _read_decision(report_588 / "task_588_decision.csv"),
                "latest_status": _read_csv(report_588 / "paper_runtime_loop_latest_status.csv").where(
                    pd.notnull(_read_csv(report_588 / "paper_runtime_loop_latest_status.csv")), None
                ).to_dict(orient="records"),
                "log": _read_csv(report_588 / "paper_runtime_loop_log.csv").tail(20).where(
                    pd.notnull(_read_csv(report_588 / "paper_runtime_loop_log.csv").tail(20)), None
                ).to_dict(orient="records"),
                "supervisor": _read_csv(report_588 / "nasdaq_paper_supervisor_status.csv").tail(20).where(
                    pd.notnull(_read_csv(report_588 / "nasdaq_paper_supervisor_status.csv").tail(20)), None
                ).to_dict(orient="records"),
            },
            "eod_report": {
                "summary": task589_summary.where(pd.notnull(task589_summary), None).to_dict(orient="records"),
                "trade_detail": task589_trade_detail.where(pd.notnull(task589_trade_detail), None).to_dict(orient="records"),
                "filled_trade_history": task589_filled_trade_history.where(pd.notnull(task589_filled_trade_history), None).to_dict(orient="records"),
                "trade_detail_view": task589_trade_detail_view,
                "decision_evidence": task589_decision_evidence.head(20).where(
                    pd.notnull(task589_decision_evidence.head(20)), None
                ).to_dict(orient="records"),
                "filled_decision_evidence": task589_filled_decision_evidence.where(pd.notnull(task589_filled_decision_evidence), None).to_dict(orient="records"),
                "indicator_snapshot_evidence": task589_indicator_snapshot.head(20).where(
                    pd.notnull(task589_indicator_snapshot.head(20)), None
                ).to_dict(orient="records"),
                "open_position_proxy": task589_open_positions.where(
                    pd.notnull(task589_open_positions), None
                ).to_dict(orient="records"),
                "realized_pnl": task589_realized_pnl.where(
                    pd.notnull(task589_realized_pnl), None
                ).to_dict(orient="records"),
                "fill_price_repair_audit": task589_fill_price_repair.where(
                    pd.notnull(task589_fill_price_repair), None
                ).to_dict(orient="records"),
                "slack_audit": _read_csv(report_589 / "paper_eod_slack_audit.csv").where(
                    pd.notnull(_read_csv(report_589 / "paper_eod_slack_audit.csv")), None
                ).to_dict(orient="records"),
                "supervisor_alert_audit": _read_csv(report_589 / "supervisor_failure_alert_audit.csv").tail(10).where(
                    pd.notnull(_read_csv(report_589 / "supervisor_failure_alert_audit.csv").tail(10)), None
                ).to_dict(orient="records"),
                "entry_context": task589_entry_context,
            },
        },
    }
    for name, path in files.items():
        if name == "decision":
            continue
        frame = _read_csv(path)
        payload[name] = frame.where(pd.notnull(frame), None).to_dict(orient="records")
    return payload


def _selected_performance_payload(
    source: dict[str, Any] | None,
    *,
    include_chart_windows: bool = True,
    chart_window_limit: int = 120,
) -> dict[str, Any]:
    if not source:
        return {"source": None, "groups": {}, "trades": []}
    path = Path(str(source["artifact_path"]))
    frame = _read_csv(path)
    pnl_col = str(source["pnl_column"])
    groups = {
        col: _group_quality(frame, col, pnl_col)
        for col in source.get("group_columns", [])
        if col in frame.columns
    }
    composite_groups = {
        name: _composite_group_quality(frame, cols, pnl_col)
        for name, cols in COMPOSITE_GROUPS.items()
    }
    composite_groups = {name: rows for name, rows in composite_groups.items() if rows}
    trade_cols = [
        col
        for col in [
            "lifecycle_id",
            "decision_id",
            "symbol",
            "theme_id",
            "role",
            "entry_ts",
            "entry_price",
            "decision_ts_utc",
            "simulated_exit_ts",
            "simulated_exit_price",
            "exit_reason",
            "holding_days",
            "same_day_exit_flag",
            "multi_day_market_state_v4",
            "theme_regime_state_v4",
            "symbol_multiday_setup_state",
            "intraday_entry_state_v4",
            "continuation_state_v4",
            "microstructure_state_v4",
            "timing_state",
            "candidate_strategy_name",
            "policy_name",
            "candidate_set",
            "suppression_rule_name",
            "range_pos",
            "intraday_ret_from_open",
            "entry_close_pos_in_bar",
            "entry_close_vs_vwap",
            "ret_5d_prev",
            "ret_20d_prev",
            "ret_60d_prev",
            "volume_ratio_prev",
            "near_high60_prev",
            "theme_ret20_prev",
            "theme_breadth20_prev",
            "theme_rank_prev",
            "broad_market_score",
            "breadth_20d",
            "market_ret_20d",
            "liquidity_ratio",
            "vol_ratio",
            "factor_adjusted_residual_pct",
            "factor_model_coverage_flag",
            "label_source",
            "entry_reduce_failure_flag",
            "add_scale_success_flag",
            "false_positive_flag",
            pnl_col,
        ]
        if col in frame.columns
    ]
    trades = frame[trade_cols].copy() if trade_cols else pd.DataFrame()
    trades, trade_sample = _sample_trade_frame(trades, max_rows=1200)
    if pnl_col in trades.columns:
        trades["net_pct_display"] = _net_pct(trades[pnl_col])
    if include_chart_windows and not trades.empty:
        chart_windows: list[dict[str, Any]] = []
        for _, row in trades.head(chart_window_limit).iterrows():
            chart_windows.append(_trade_chart_window(row))
        trades = trades.copy()
        trades.loc[trades.head(chart_window_limit).index, "chart_window"] = chart_windows
    return {
        "source": source,
        "groups": groups,
        "composite_groups": composite_groups,
        "matrix": _matrix_quality(frame, pnl_col),
        "trade_sample": trade_sample,
        "trades": trades.where(pd.notnull(trades), None).to_dict(orient="records"),
    }


def build_catalog(root: Path) -> dict[str, Any]:
    catalog = build_research_task_catalog()
    sources = _performance_sources(catalog)
    selected = sources[-1] if sources else None
    payloads = {
        str(source.get("artifact_path")): _selected_performance_payload(
            source,
            include_chart_windows=True,
            chart_window_limit=35,
        )
        for source in sources
    }
    if selected:
        payloads[str(selected.get("artifact_path"))] = _selected_performance_payload(
            selected,
            include_chart_windows=True,
            chart_window_limit=180,
        )
    return {
        "generated_utc": datetime.now(tz=UTC).isoformat(),
        "contract_version": "trader-terminal-v1",
        "rules": {
            "ui_reads_catalog_only": True,
            "legacy_backtest_not_task_artifact": True,
            "deployment_claim_allowed": False,
            "missing_source_approximation_allowed": False,
        },
        "tasks": _task_cards(catalog),
        "paper_ops": _paper_ops_payload(),
        "performance_sources": sources,
        "selected_performance": payloads.get(str(selected.get("artifact_path"))) if selected else _selected_performance_payload(None),
        "performance_payloads": payloads,
    }


def write_catalog(payload: dict[str, Any], outputs: list[Path]) -> None:
    text = json.dumps(_json_clean(payload), ensure_ascii=False, indent=2, default=str, allow_nan=False)
    readiness_registry = payload.get("paper_ops", {}).get("v2", {}).get("readiness_registry")
    readiness_text = json.dumps(_json_clean(readiness_registry), ensure_ascii=False, indent=2, default=str, allow_nan=False)
    for output in outputs:
        output.mkdir(parents=True, exist_ok=True)
        (output / "trader_terminal_catalog.json").write_text(text, encoding="utf-8")
        if readiness_registry:
            (output / "readiness_registry.json").write_text(readiness_text, encoding="utf-8")


def build_paper_ops_runtime_catalog(root: Path) -> dict[str, Any]:
    return {
        "generated_utc": datetime.now(tz=UTC).isoformat(),
        "contract_version": "paper-ops-runtime-v1",
        "rules": {
            "ui_reads_catalog_only": True,
            "deployment_claim_allowed": False,
            "missing_source_approximation_allowed": False,
        },
        "paper_ops": _paper_ops_payload(),
    }


def write_paper_ops_runtime_catalog(payload: dict[str, Any], outputs: list[Path]) -> None:
    text = json.dumps(_json_clean(payload), ensure_ascii=False, indent=2, default=str, allow_nan=False)
    trade_detail_view = payload.get("paper_ops", {}).get("v2", {}).get("eod_report", {}).get("trade_detail_view", [])
    readiness_registry = payload.get("paper_ops", {}).get("v2", {}).get("readiness_registry")
    readiness_text = json.dumps(_json_clean(readiness_registry), ensure_ascii=False, indent=2, default=str, allow_nan=False)
    view_text = json.dumps(
        _json_clean(
            {
                "generated_utc": payload.get("generated_utc"),
                "contract_version": "paper_trade_detail_view_v1",
                "trade_detail_view": trade_detail_view,
            }
        ),
        ensure_ascii=False,
        indent=2,
        default=str,
        allow_nan=False,
    )
    for output in outputs:
        output.mkdir(parents=True, exist_ok=True)
        (output / "paper_ops_runtime_catalog.json").write_text(text, encoding="utf-8")
        (output / "paper_trade_detail_view.json").write_text(view_text, encoding="utf-8")
        if readiness_registry:
            (output / "readiness_registry.json").write_text(readiness_text, encoding="utf-8")


def _json_clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_clean(item) for item in value]
    if isinstance(value, tuple):
        return [_json_clean(item) for item in value]
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if pd.isna(value) if not isinstance(value, (str, bytes, list, dict, tuple)) else False:
        return None
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("frontend_data/catalog"))
    parser.add_argument("--app-public", type=Path, default=Path("frontend/trader-terminal/public/catalog"))
    parser.add_argument("--paper-ops-only", action="store_true")
    args = parser.parse_args()
    if args.paper_ops_only:
        payload = build_paper_ops_runtime_catalog(args.root)
        write_paper_ops_runtime_catalog(payload, [args.out, args.app_public])
        print("[PAPER_OPS_RUNTIME_CATALOG_OK]")
        return
    payload = build_catalog(args.root)
    write_catalog(payload, [args.out, args.app_public])
    print(f"[TRADER_TERMINAL_CATALOG_OK] tasks={len(payload['tasks'])} performance_sources={len(payload['performance_sources'])}")


if __name__ == "__main__":
    main()
