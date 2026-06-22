from __future__ import annotations

import json
import os
import sqlite3
import sys
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PLOTLY_AVAILABLE = False
PLOTLY_IMPORT_ERROR: str | None = None
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except Exception:  # pragma: no cover - optional dependency fallback
    go = None
    make_subplots = None
    PLOTLY_IMPORT_ERROR = str(sys.exc_info()[1]) if sys.exc_info()[1] else "unknown import error"
else:
    PLOTLY_AVAILABLE = True

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from backtest.data_loader import load_daily_bars
from reporting.research_task_catalog import build_research_task_catalog, load_artifact_manifest
from strategy.conditions import condition_snapshot, find_last_index_before, is_exit_condition, prepare_condition_frame
from strategy.validator import validate_trade_alignment
from ui.trade_review_model import load_trade_reviews, to_dataframe


def _db_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.environ.get("TRADING_DB_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("trading.db"),
            Path("data") / "trading.db",
            Path("docs") / "logs" / "trading.db",
        ]
    )
    out: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def _db_path() -> str:
    env_path = os.environ.get("TRADING_DB_PATH")
    if env_path:
        return str(Path(env_path))
    existing = [p for p in _db_candidates() if p.exists()]
    if existing:
        latest = max(existing, key=lambda p: p.stat().st_mtime)
        return str(latest)
    return "trading.db"


def _backtest_trades_path() -> str:
    env_path = os.environ.get("BACKTEST_TRADES_PATH")
    if env_path:
        return str(Path(env_path))
    candidates = [
        Path("data") / "backtest" / "trades.json",
        Path("docs") / "reports" / "task_083" / "trades.json",
        Path("docs") / "reports" / "task_084" / "trades.json",
    ]
    existing = [p for p in candidates if p.exists()]
    if existing:
        latest = max(existing, key=lambda p: p.stat().st_mtime)
        return str(latest)
    return str(candidates[0])


def _empty_df(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _connect_read_only(db_path: str) -> sqlite3.Connection:
    uri = f"file:{Path(db_path).resolve()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    return con


def _run_query(db_path: str, query: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    try:
        con = _connect_read_only(db_path)
    except Exception:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(query, con, params=params)
    except Exception:
        return pd.DataFrame()
    finally:
        con.close()


@st.cache_data(ttl=10)
def _table_exists(db_path: str, table_name: str) -> bool:
    query = "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ? LIMIT 1"
    df = _run_query(db_path, query, (table_name,))
    return not df.empty


@st.cache_data(ttl=10)
def _table_row_count(db_path: str, table_name: str) -> int:
    if not _table_exists(db_path, table_name):
        return 0
    df = _run_query(db_path, f"SELECT COUNT(*) AS cnt FROM {table_name}")
    if df.empty or "cnt" not in df.columns:
        return 0
    return int(df.iloc[0]["cnt"])


@st.cache_data(ttl=10)
def _table_columns(db_path: str, table_name: str) -> list[str]:
    if not _table_exists(db_path, table_name):
        return []
    df = _run_query(db_path, f"PRAGMA table_info({table_name})")
    if df.empty or "name" not in df.columns:
        return []
    return [str(col) for col in df["name"].tolist()]


def _render_table_state(db_path: str, table_name: str) -> tuple[bool, int]:
    exists = _table_exists(db_path, table_name)
    if not exists:
        st.warning(f"Table not found: {table_name}")
        return False, 0

    count = _table_row_count(db_path, table_name)
    if count == 0:
        st.info(f"No data in table: {table_name}")
    return True, count


@st.cache_data(ttl=15)
def load_trade_review_records(json_path: str) -> pd.DataFrame:
    records = load_trade_reviews(json_path)
    if not records:
        return pd.DataFrame()
    return to_dataframe(records)


@st.cache_data(ttl=15)
def load_backtest_trade_results(json_path: str) -> pd.DataFrame:
    path = Path(json_path)
    if not path.exists():
        return pd.DataFrame()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    if isinstance(payload, dict) and isinstance(payload.get("trades"), list):
        rows = payload["trades"]
    elif isinstance(payload, list):
        rows = payload

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    for col in ("entry_time", "exit_time"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    return df


@st.cache_data(ttl=15)
def load_symbol_price_series(symbol: str) -> pd.DataFrame:
    try:
        return load_daily_bars(symbol)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=15)
def load_trade_detail_fallback(db_path: str, limit: int = 50) -> pd.DataFrame:
    required_tables = ("trade_runs", "orders", "fills")
    if not all(_table_exists(db_path, t) for t in required_tables):
        return pd.DataFrame()

    query = """
        SELECT
            tr.run_id AS trade_id,
            'us_swing_breakout_v0' AS strategy_id,
            tr.symbol,
            tr.started_at AS entry_time,
            tr.finished_at AS exit_time,
            tr.result_status,
            o.order_id,
            o.status AS order_status,
            o.quantity,
            f.fill_price AS entry_fill_price,
            f.filled_quantity,
            f.filled_at,
            f.source AS fill_source
        FROM trade_runs tr
        LEFT JOIN orders o ON o.run_id = tr.run_id
        LEFT JOIN (
            SELECT f1.*
            FROM fills f1
            INNER JOIN (
                SELECT order_id, MAX(filled_at) AS max_filled_at
                FROM fills
                GROUP BY order_id
            ) latest
            ON latest.order_id = f1.order_id
            AND latest.max_filled_at = f1.filled_at
        ) f ON f.order_id = o.order_id
        ORDER BY tr.started_at DESC
        LIMIT ?
    """
    df = _run_query(db_path, query, (limit,))
    if df.empty:
        return df

    df["entry_time"] = pd.to_datetime(df.get("entry_time"), utc=True, errors="coerce")
    df["exit_time"] = pd.to_datetime(df.get("exit_time"), utc=True, errors="coerce")
    df["entry_price"] = df.get("entry_fill_price")
    df["exit_price"] = None
    df["exit_fill_price"] = None
    df["breakout_level"] = None
    df["stop_price"] = None
    df["reason"] = "fallback_from_run_order_fill"
    df["source"] = "fallback"
    df["strategy_id"] = "us_swing_breakout_v0"
    df["sector"] = "UNMAPPED"
    df["regime"] = "UNKNOWN"
    df["expected_pnl"] = None
    df["actual_pnl"] = None
    df["slippage"] = None
    df["holding_time"] = None
    return df


def _safe_parse_ts(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            return value.to_pydatetime().replace(tzinfo=UTC)
        return value.to_pydatetime().astimezone(UTC)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _build_trade_chart_points(trade_row: pd.Series) -> pd.DataFrame:
    points: list[dict[str, object]] = []
    entry_t = _safe_parse_ts(trade_row.get("entry_time"))
    exit_t = _safe_parse_ts(trade_row.get("exit_time"))

    if entry_t and pd.notna(trade_row.get("entry_price")):
        points.append({"time": entry_t, "price": float(trade_row.get("entry_price")), "label": "expected_entry"})
    if entry_t and pd.notna(trade_row.get("entry_fill_price")):
        points.append({"time": entry_t, "price": float(trade_row.get("entry_fill_price")), "label": "actual_entry"})
    if exit_t and pd.notna(trade_row.get("exit_price")):
        points.append({"time": exit_t, "price": float(trade_row.get("exit_price")), "label": "expected_exit"})
    if exit_t and pd.notna(trade_row.get("exit_fill_price")):
        points.append({"time": exit_t, "price": float(trade_row.get("exit_fill_price")), "label": "actual_exit"})

    if not points:
        return _empty_df(["time", "price", "label"])
    return pd.DataFrame(points).sort_values("time")


def _compute_indicator_frame(price_df: pd.DataFrame) -> pd.DataFrame:
    return prepare_condition_frame(price_df)


def _signal_index_for_trade(frame: pd.DataFrame, trade_row: pd.Series, *, field: str) -> int | None:
    signal_time = _safe_parse_ts(trade_row.get(field))
    if signal_time is None:
        return None
    return find_last_index_before(frame, signal_time)


def _render_trade_chart(trade_row: pd.Series) -> pd.DataFrame:
    symbol = str(trade_row.get("symbol") or "").upper()
    price_df = load_symbol_price_series(symbol) if symbol else pd.DataFrame()
    markers = _build_trade_chart_points(trade_row)

    entry_t = _safe_parse_ts(trade_row.get("entry_time"))
    exit_t = _safe_parse_ts(trade_row.get("exit_time"))
    breakout_level = trade_row.get("breakout_level")
    stop_price = trade_row.get("stop_price")

    window_df = pd.DataFrame()
    chart_mode = "candlestick"
    if not price_df.empty and "timestamp" in price_df.columns:
        if entry_t is not None:
            right_anchor = exit_t or entry_t
            left = pd.Timestamp(entry_t) - pd.Timedelta(days=20)
            right = pd.Timestamp(right_anchor) + pd.Timedelta(days=20)
            window_df = price_df[(price_df["timestamp"] >= left) & (price_df["timestamp"] <= right)].copy()
        if window_df.empty:
            window_df = price_df.tail(120).copy()

    if go is None or make_subplots is None:
        chart_mode = "fallback_line"
        if PLOTLY_IMPORT_ERROR:
            st.error(f"Plotly import failed: {PLOTLY_IMPORT_ERROR}")
            st.info("Install plotly to enable candlestick / overlay rendering.")
        if not window_df.empty:
            st.line_chart(window_df.set_index("timestamp")["close"])
        elif not markers.empty:
            st.line_chart(markers.set_index("time")["price"])
        else:
            st.info("No chartable data for this trade.")
            return pd.DataFrame(
                [
                    {"metric": "price_source_loaded", "value": "no"},
                    {"metric": "ohlcv_rows", "value": 0},
                    {"metric": "plotly_available", "value": "no"},
                    {"metric": "chart_mode", "value": chart_mode},
                ]
            )
        st.caption("Plotly not available. Showing simplified line chart.")
        indicator_df = _compute_indicator_frame(window_df)
        return pd.DataFrame(
            [
                {"metric": "price_source_loaded", "value": "yes" if not window_df.empty else "no"},
                {"metric": "ohlcv_rows", "value": int(len(window_df))},
                {"metric": "plotly_available", "value": "no"},
                {"metric": "chart_mode", "value": chart_mode},
                {"metric": "ema20_computed", "value": "yes" if "ema20" in indicator_df.columns and indicator_df["ema20"].notna().any() else "no"},
                {"metric": "ema50_computed", "value": "yes" if "ema50" in indicator_df.columns and indicator_df["ema50"].notna().any() else "no"},
                {"metric": "ema200_computed", "value": "yes" if "ema200" in indicator_df.columns and indicator_df["ema200"].notna().any() else "no"},
                {"metric": "macd_computed", "value": "yes" if "macd" in indicator_df.columns and indicator_df["macd"].notna().any() else "no"},
                {"metric": "rsi14_computed", "value": "yes" if "rsi14" in indicator_df.columns and indicator_df["rsi14"].notna().any() else "no"},
                {
                    "metric": "breakout_high_20_computed",
                    "value": "yes" if "breakout_high_20" in indicator_df.columns and indicator_df["breakout_high_20"].notna().any() else "no",
                },
            ]
        )

    required_ohlc = {"timestamp", "open", "high", "low", "close"}
    if window_df.empty or not required_ohlc.issubset(set(window_df.columns)):
        st.info("No OHLC data available for candlestick view.")
        chart_mode = "fallback_line"
        return pd.DataFrame(
            [
                {"metric": "price_source_loaded", "value": "yes" if not window_df.empty else "no"},
                {"metric": "ohlcv_rows", "value": int(len(window_df))},
                {"metric": "plotly_available", "value": "yes" if PLOTLY_AVAILABLE else "no"},
                {"metric": "chart_mode", "value": chart_mode},
            ]
        )

    # Indicator overlay inputs (Task 058-A2)
    window_df = _compute_indicator_frame(window_df)

    # Performance guard: keep one-trade focused rendering responsive.
    max_bars = 260
    if len(window_df) > max_bars:
        window_df = window_df.tail(max_bars).copy()

    entry_date = pd.Timestamp(entry_t).date() if entry_t is not None else None
    exit_date = pd.Timestamp(exit_t).date() if exit_t is not None else None
    if entry_t is not None and exit_t is not None:
        start_t = min(pd.Timestamp(entry_t), pd.Timestamp(exit_t))
        end_t = max(pd.Timestamp(entry_t), pd.Timestamp(exit_t))
        trade_window = (window_df["timestamp"] >= start_t) & (window_df["timestamp"] <= end_t)
    else:
        trade_window = pd.Series(False, index=window_df.index)
    entry_flag = window_df["timestamp"].dt.date == entry_date if entry_date is not None else pd.Series(False, index=window_df.index)
    exit_flag = window_df["timestamp"].dt.date == exit_date if exit_date is not None else pd.Series(False, index=window_df.index)

    customdata = pd.DataFrame(
        {
            "trade": trade_window.map(lambda x: "yes" if bool(x) else "no"),
            "entry": entry_flag.map(lambda x: "yes" if bool(x) else "no"),
            "exit": exit_flag.map(lambda x: "yes" if bool(x) else "no"),
            "ema20": window_df["ema20"],
            "ema50": window_df["ema50"],
            "ema200": window_df["ema200"],
            "breakout20": window_df["breakout_high_20"],
            "macd": window_df["macd"],
            "macd_signal": window_df["macd_signal"],
            "macd_hist": window_df["macd_hist"],
            "rsi14": window_df["rsi14"],
        }
    ).to_numpy()

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.56, 0.16, 0.16, 0.12],
        subplot_titles=(f"{symbol} Candlestick", "Volume", "MACD", "RSI14"),
    )
    fig.add_trace(
        go.Candlestick(
            x=window_df["timestamp"],
            open=window_df["open"],
            high=window_df["high"],
            low=window_df["low"],
            close=window_df["close"],
            name="OHLC",
            increasing_line_color="#2ca02c",
            decreasing_line_color="#d62728",
            customdata=customdata,
            hovertemplate=(
                "Date: %{x|%Y-%m-%d}<br>"
                "Open: %{open:.2f}<br>"
                "High: %{high:.2f}<br>"
                "Low: %{low:.2f}<br>"
                "Close: %{close:.2f}<br>"
                "EMA20: %{customdata[3]:.2f}<br>"
                "EMA50: %{customdata[4]:.2f}<br>"
                "EMA200: %{customdata[5]:.2f}<br>"
                "Breakout20: %{customdata[6]:.2f}<br>"
                "MACD: %{customdata[7]:.4f}<br>"
                "MACD Signal: %{customdata[8]:.4f}<br>"
                "MACD Hist: %{customdata[9]:.4f}<br>"
                "RSI14: %{customdata[10]:.2f}<br>"
                "trade: %{customdata[0]}<br>"
                "entry: %{customdata[1]}<br>"
                "exit: %{customdata[2]}<extra></extra>"
            ),
        ),
        row=1,
        col=1,
    )

    # Layer 2: EMA lines.
    fig.add_trace(
        go.Scatter(
            x=window_df["timestamp"],
            y=window_df["ema20"],
            mode="lines",
            name="EMA20",
            line={"color": "blue", "width": 1.1},
            hovertemplate="Date: %{x|%Y-%m-%d}<br>EMA20: %{y:.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=window_df["timestamp"],
            y=window_df["ema50"],
            mode="lines",
            name="EMA50",
            line={"color": "orange", "width": 1.1},
            hovertemplate="Date: %{x|%Y-%m-%d}<br>EMA50: %{y:.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=window_df["timestamp"],
            y=window_df["ema200"],
            mode="lines",
            name="EMA200",
            line={"color": "gray", "width": 1.1},
            hovertemplate="Date: %{x|%Y-%m-%d}<br>EMA200: %{y:.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=window_df["timestamp"],
            y=window_df["breakout_high_20"],
            mode="lines",
            name="Breakout20",
            line={"color": "blue", "width": 1.0, "dash": "dash"},
            hovertemplate="Date: %{x|%Y-%m-%d}<br>Breakout20: %{y:.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Layer 3: breakout/stop/target horizontal levels.
    if pd.notna(breakout_level):
        fig.add_hline(y=float(breakout_level), line_dash="dash", line_color="blue", annotation_text="breakout_level", row=1, col=1)
    if pd.notna(stop_price):
        fig.add_hline(y=float(stop_price), line_dash="dash", line_color="orange", annotation_text="stop_price", row=1, col=1)
    if pd.notna(trade_row.get("target_price")):
        fig.add_hline(
            y=float(trade_row.get("target_price")),
            line_dash="dash",
            line_color="purple",
            annotation_text="target_price",
            row=1,
            col=1,
        )

    # Layer 4: volume subplot.
    if "volume" in window_df.columns:
        vol_color = [
            "#2ca02c" if float(c) >= float(o) else "#d62728"
            for c, o in zip(window_df["close"], window_df["open"], strict=False)
        ]
        fig.add_trace(
            go.Bar(
                x=window_df["timestamp"],
                y=window_df["volume"],
                marker_color=vol_color,
                name="Volume",
                opacity=0.6,
                hovertemplate="Date: %{x|%Y-%m-%d}<br>Volume: %{y:,.0f}<extra></extra>",
            ),
            row=2,
            col=1,
        )

    # MACD subplot.
    if {"macd", "macd_signal", "macd_hist"}.issubset(set(window_df.columns)):
        hist_color = ["#2ca02c" if float(v) >= 0 else "#d62728" for v in window_df["macd_hist"]]
        fig.add_trace(
            go.Bar(
                x=window_df["timestamp"],
                y=window_df["macd_hist"],
                marker_color=hist_color,
                opacity=0.5,
                name="MACD Hist",
                hovertemplate="Date: %{x|%Y-%m-%d}<br>MACD Hist: %{y:.4f}<extra></extra>",
            ),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=window_df["timestamp"],
                y=window_df["macd"],
                mode="lines",
                name="MACD",
                line={"color": "#1f77b4", "width": 1.1},
                hovertemplate="Date: %{x|%Y-%m-%d}<br>MACD: %{y:.4f}<extra></extra>",
            ),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=window_df["timestamp"],
                y=window_df["macd_signal"],
                mode="lines",
                name="MACD Signal",
                line={"color": "#ff7f0e", "width": 1.1},
                hovertemplate="Date: %{x|%Y-%m-%d}<br>MACD Signal: %{y:.4f}<extra></extra>",
            ),
            row=3,
            col=1,
        )

    # RSI subplot.
    if "rsi14" in window_df.columns:
        fig.add_trace(
            go.Scatter(
                x=window_df["timestamp"],
                y=window_df["rsi14"],
                mode="lines",
                name="RSI14",
                line={"color": "#9467bd", "width": 1.2},
                hovertemplate="Date: %{x|%Y-%m-%d}<br>RSI14: %{y:.2f}<extra></extra>",
            ),
            row=4,
            col=1,
        )
        fig.add_hline(y=70, line_dash="dot", line_color="#999999", row=4, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#999999", row=4, col=1)

    # Trade window highlight.
    if entry_t is not None and exit_t is not None:
        x0 = min(pd.Timestamp(entry_t), pd.Timestamp(exit_t))
        x1 = max(pd.Timestamp(entry_t), pd.Timestamp(exit_t))
        fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(46, 160, 67, 0.14)", line_width=0, row=1, col=1)
        fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(46, 160, 67, 0.08)", line_width=0, row=2, col=1)
        fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(46, 160, 67, 0.06)", line_width=0, row=3, col=1)
        fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(46, 160, 67, 0.06)", line_width=0, row=4, col=1)

    # Layer 5: markers (force highest visibility).
    style_map = {
        "expected_entry": {"color": "green", "symbol": "circle-open", "name": "expected_entry", "size": 16},
        "actual_entry": {"color": "green", "symbol": "circle", "name": "actual_entry", "size": 18},
        "expected_exit": {"color": "red", "symbol": "circle-open", "name": "expected_exit", "size": 16},
        "actual_exit": {"color": "red", "symbol": "circle", "name": "actual_exit", "size": 18},
    }
    marker_points: dict[str, tuple[pd.Timestamp, float]] = {}
    for label, style in style_map.items():
        subset = markers[markers["label"] == label]
        if subset.empty:
            continue
        marker_points[label] = (pd.Timestamp(subset.iloc[-1]["time"]), float(subset.iloc[-1]["price"]))
        fig.add_trace(
            go.Scatter(
                x=subset["time"],
                y=subset["price"],
                mode="markers",
                marker={
                    "size": style["size"],
                    "color": style["color"],
                    "symbol": style["symbol"],
                    "opacity": 1.0,
                    "line": {"width": 2, "color": style["color"]},
                },
                opacity=1.0,
                name=style["name"],
                hovertemplate=f"Date: %{{x|%Y-%m-%d}}<br>Price: %{{y:.2f}}<br>{style['name']}<extra></extra>",
            )
        , row=1, col=1)

    # Layer 6: annotations.
    reason_raw = str(trade_row.get("reason") or "Unknown")
    reason_short = reason_raw.replace("ENTRY_", "").replace("_", " ").title()
    if "actual_entry" in marker_points:
        t, p = marker_points["actual_entry"]
        fig.add_annotation(
            x=t,
            y=p,
            text=f"BUY<br>${p:.2f}<br>{reason_short}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1.5,
            arrowcolor="green",
            ax=0,
            ay=-70,
            bgcolor="rgba(0,0,0,0)",
            font={"size": 10, "color": "green"},
            row=1,
            col=1,
        )
    if "expected_entry" in marker_points:
        t, p = marker_points["expected_entry"]
        fig.add_annotation(
            x=t,
            y=p,
            text=f"BUY (exp)<br>${p:.2f}",
            showarrow=True,
            arrowhead=1,
            arrowsize=1,
            arrowwidth=1.2,
            arrowcolor="green",
            ax=0,
            ay=-55,
            bgcolor="rgba(0,0,0,0)",
            font={"size": 9, "color": "green"},
            row=1,
            col=1,
        )

    entry_fill = trade_row.get("entry_fill_price")
    exit_fill = trade_row.get("exit_fill_price")
    pnl_pct_text = "N/A"
    if pd.notna(entry_fill) and pd.notna(exit_fill) and float(entry_fill) != 0.0:
        pnl_pct = ((float(exit_fill) - float(entry_fill)) / float(entry_fill)) * 100.0
        pnl_pct_text = f"{pnl_pct:+.2f}%"
    if "actual_exit" in marker_points:
        t, p = marker_points["actual_exit"]
        fig.add_annotation(
            x=t,
            y=p,
            text=f"SELL<br>${p:.2f}<br>{pnl_pct_text}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1.5,
            arrowcolor="red",
            ax=0,
            ay=70,
            bgcolor="rgba(0,0,0,0)",
            font={"size": 10, "color": "red"},
            row=1,
            col=1,
        )
    if "expected_exit" in marker_points:
        t, p = marker_points["expected_exit"]
        fig.add_annotation(
            x=t,
            y=p,
            text=f"SELL (exp)<br>${p:.2f}",
            showarrow=True,
            arrowhead=1,
            arrowsize=1,
            arrowwidth=1.2,
            arrowcolor="red",
            ax=0,
            ay=55,
            bgcolor="rgba(0,0,0,0)",
            font={"size": 9, "color": "red"},
            row=1,
            col=1,
        )

    regime = str(trade_row.get("regime", "")).strip().upper()
    if regime in {"BULL", "BEAR"}:
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.01,
            y=1.10,
            text=f"Regime: {regime}",
            showarrow=False,
            font={"size": 12, "color": "#444"},
        )

    fig.update_layout(
        height=860,
        margin={"l": 20, "r": 20, "t": 36, "b": 20},
        xaxis_rangeslider_visible=False,
        yaxis_title="price",
        yaxis2_title="volume",
        yaxis3_title="macd",
        yaxis4_title="rsi",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
    return pd.DataFrame(
        [
            {"metric": "price_source_loaded", "value": "yes"},
            {"metric": "ohlcv_rows", "value": int(len(window_df))},
            {"metric": "plotly_available", "value": "yes" if PLOTLY_AVAILABLE else "no"},
            {"metric": "chart_mode", "value": chart_mode},
            {"metric": "ema20_computed", "value": "yes" if "ema20" in window_df.columns and window_df["ema20"].notna().any() else "no"},
            {"metric": "ema50_computed", "value": "yes" if "ema50" in window_df.columns and window_df["ema50"].notna().any() else "no"},
            {"metric": "ema200_computed", "value": "yes" if "ema200" in window_df.columns and window_df["ema200"].notna().any() else "no"},
            {"metric": "macd_computed", "value": "yes" if "macd" in window_df.columns and window_df["macd"].notna().any() else "no"},
            {"metric": "rsi14_computed", "value": "yes" if "rsi14" in window_df.columns and window_df["rsi14"].notna().any() else "no"},
            {"metric": "breakout_high_20_computed", "value": "yes" if window_df["breakout_high_20"].notna().any() else "no"},
        ]
    )


def _derive_entry_conditions(trade_row: pd.Series, price_df: pd.DataFrame) -> list[tuple[str, bool | None, str]]:
    out: list[tuple[str, bool | None, str]] = []
    stored_breakout = trade_row.get("breakout_flag")
    stored_ma = trade_row.get("ma_trend_flag")
    if pd.notna(stored_breakout) or pd.notna(stored_ma):
        breakout_flag = None if pd.isna(stored_breakout) else bool(stored_breakout)
        ma_flag = None if pd.isna(stored_ma) else bool(stored_ma)
        out.append(("Close >= breakout_high_20", breakout_flag, "actual"))
        out.append(("Close > MA50 & MA20 > MA50", ma_flag, "actual"))
        return out

    frame = _compute_indicator_frame(price_df)
    entry_idx = _signal_index_for_trade(frame, trade_row, field="entry_time")
    if frame.empty or entry_idx is None:
        out.append(("Close >= breakout_high_20", None, "shared"))
        out.append(("Close > MA50", None, "shared"))
        out.append(("MA20 > MA50", None, "shared"))
        return out

    snapshot = condition_snapshot(frame, entry_idx)
    out.append(("Close >= breakout_high_20", snapshot["breakout_condition"], "shared"))
    out.append(("Close > MA50", snapshot["close_above_ma50"], "shared"))
    out.append(("MA20 > MA50", snapshot["ma20_above_ma50"], "shared"))
    return out


def _derive_exit_reason(trade_row: pd.Series, price_df: pd.DataFrame) -> tuple[str, str]:
    exit_rule = str(trade_row.get("exit_rule", "")).upper().strip()
    if exit_rule == "STOP":
        return "stop hit", "actual"
    if exit_rule == "TREND_BREAK_2BAR":
        return "SMA20 2-bar break", "actual"
    if exit_rule == "TIME_EXIT":
        return "max holding", "actual"

    reason = str(trade_row.get("reason", "")).upper()
    if "STOP" in reason:
        return "stop hit", "actual"
    if "TREND_BREAK" in reason or "MA" in reason or "EMA" in reason:
        return "MA/EMA break", "actual"
    if "TIME" in reason:
        return "max holding", "actual"

    exit_price = trade_row.get("exit_price")
    stop_price = trade_row.get("stop_price")
    holding_time = trade_row.get("holding_time")

    frame = _compute_indicator_frame(price_df)
    exit_idx = _signal_index_for_trade(frame, trade_row, field="exit_time")
    if (
        exit_idx is not None
        and pd.notna(stop_price)
        and "low" in frame.columns
        and pd.notna(frame.iloc[exit_idx]["low"])
        and float(frame.iloc[exit_idx]["low"]) <= float(stop_price)
    ):
        return "stop hit", "shared"
    if exit_idx is not None and is_exit_condition(frame, exit_idx) is True:
        return "SMA20 2-bar break", "shared"
    if pd.notna(holding_time) and float(holding_time) > (20 * 86400):
        return "max holding", "shared"

    if pd.notna(exit_price) and pd.notna(stop_price) and float(exit_price) <= float(stop_price):
        return "stop hit", "inferred"
    if pd.notna(holding_time) and float(holding_time) >= (20 * 86400):
        return "max holding", "inferred"
    return "other / unresolved", "inferred"


def _derive_alignment_status(trade_row: pd.Series, price_df: pd.DataFrame):
    signal_reason = str(trade_row.get("reason", "")).upper().strip() or "UNKNOWN"
    payload = trade_row.to_dict()
    # Canonical stored flags are truth source. Validator verifies shared-condition consistency.
    result = validate_trade_alignment(payload, price_df)
    return signal_reason, result


def _render_reason_panel(trade_row: pd.Series, price_df: pd.DataFrame) -> None:
    st.markdown("**Trade Reason Panel**")
    entry_conditions = _derive_entry_conditions(trade_row, price_df)
    exit_reason, exit_source = _derive_exit_reason(trade_row, price_df)

    st.markdown("[Entry Conditions]")
    for label, passed, source in entry_conditions:
        if passed is True:
            color = "#14833b"
            state = "True"
        elif passed is False:
            color = "#b42318"
            state = "False"
        else:
            color = "#6b7280"
            state = "Unknown"
        st.markdown(
            f"<span style='color:{color};font-weight:600'>{label}: {state}</span>"
            f" <span style='color:#6b7280'>({source})</span>",
            unsafe_allow_html=True,
        )

    st.markdown("[Exit Reason]")
    st.write(f"- {exit_reason} ({exit_source})")


def _missing_fields(trade_row: pd.Series) -> list[str]:
    required = [
        "trade_id",
        "entry_time",
        "entry_price",
        "entry_fill_price",
        "exit_time",
        "exit_price",
        "exit_fill_price",
        "breakout_level",
        "stop_price",
        "reason",
    ]
    missing: list[str] = []
    for field in required:
        value = trade_row.get(field)
        if value is None or (isinstance(value, float) and pd.isna(value)) or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return missing


def _render_db_status(db_path: str) -> None:
    resolved = Path(db_path).resolve()
    exists = resolved.exists()
    st.sidebar.markdown("### Data Source")
    st.sidebar.code(str(resolved))
    st.sidebar.write(f"DB exists: {exists}")
    if exists:
        st.sidebar.write(f"DB updated: {datetime.fromtimestamp(resolved.stat().st_mtime).isoformat(timespec='seconds')}")
    candidates = _db_candidates()
    existing = [p for p in candidates if p.exists()]
    if len(existing) > 1:
        latest = max(existing, key=lambda p: p.stat().st_mtime).resolve()
        if latest != resolved:
            st.sidebar.warning(f"Selected DB is not latest. latest={latest}")
        with st.sidebar.expander("DB candidates"):
            rows = []
            for p in existing:
                rows.append(
                    {
                        "path": str(p.resolve()),
                        "updated": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.sidebar.markdown("### Backtest Trades")
    trades_path = Path(_backtest_trades_path())
    st.sidebar.code(str(trades_path))
    st.sidebar.write(f"Trades exists: {trades_path.exists()}")


def _render_overview_page(db_path: str) -> None:
    st.subheader("Overview")
    run_ok, run_count = _render_table_state(db_path, "trade_runs")
    order_ok, order_count = _render_table_state(db_path, "orders")
    fill_ok, fill_count = _render_table_state(db_path, "fills")
    pos_ok, _ = _render_table_state(db_path, "positions")

    open_positions = 0
    if pos_ok:
        pos_df = _run_query(db_path, "SELECT COUNT(*) AS cnt FROM positions WHERE quantity <> 0")
        if not pos_df.empty:
            open_positions = int(pos_df.iloc[0]["cnt"])

    last_run_status = "N/A"
    if run_ok and run_count > 0:
        last_df = _run_query(db_path, "SELECT result_status FROM trade_runs ORDER BY started_at DESC LIMIT 1")
        if not last_df.empty and "result_status" in last_df.columns:
            last_run_status = str(last_df.iloc[0]["result_status"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("total runs", run_count if run_ok else 0)
    c2.metric("total orders", order_count if order_ok else 0)
    c3.metric("total fills", fill_count if fill_ok else 0)
    c4.metric("open positions count", open_positions)
    c5.metric("last run status", last_run_status)

    if run_ok and run_count > 0:
        limit = st.slider("Overview recent runs", min_value=5, max_value=100, value=20, step=5)
        runs = _run_query(
            db_path,
            """
            SELECT run_id, symbol, side, started_at, finished_at, result_status, environment
            FROM trade_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        if runs.empty:
            st.info("No data in table: trade_runs")
        else:
            st.dataframe(runs, use_container_width=True)


def _render_orders_fills_page(db_path: str) -> None:
    st.subheader("Orders / Fills")
    limit = st.slider("Orders/Fills recent rows", min_value=10, max_value=500, value=100, step=10)

    orders_ok, orders_count = _render_table_state(db_path, "orders")
    fills_ok, fills_count = _render_table_state(db_path, "fills")

    if not orders_ok or orders_count == 0:
        return

    order_cols = _table_columns(db_path, "orders")
    intent_col = "intent_key" if "intent_key" in order_cols else ("order_intent_key" if "order_intent_key" in order_cols else None)

    select_intent = f", o.{intent_col} AS intent_key" if intent_col else ", NULL AS intent_key"
    query = f"""
        SELECT
            o.order_id,
            o.symbol,
            o.status
            {select_intent},
            f.filled_quantity AS filled_qty,
            f.fill_price,
            f.source
        FROM orders o
        LEFT JOIN (
            SELECT f1.*
            FROM fills f1
            INNER JOIN (
                SELECT order_id, MAX(filled_at) AS max_filled_at
                FROM fills
                GROUP BY order_id
            ) latest
            ON latest.order_id = f1.order_id
            AND latest.max_filled_at = f1.filled_at
        ) f ON f.order_id = o.order_id
        ORDER BY o.submitted_at DESC
        LIMIT ?
    """
    if fills_ok and fills_count > 0:
        df = _run_query(db_path, query, (limit,))
    else:
        st.info("No data in table: fills")
        df = _run_query(
            db_path,
            f"""
            SELECT o.order_id, o.symbol, o.status {select_intent},
                   NULL AS filled_qty, NULL AS fill_price, NULL AS source
            FROM orders o
            ORDER BY o.submitted_at DESC
            LIMIT ?
            """,
            (limit,),
        )

    if df.empty:
        st.info("No data in table: orders")
        return
    st.dataframe(df[["order_id", "symbol", "status", "intent_key", "filled_qty", "fill_price", "source"]], use_container_width=True)


def _render_positions_page(db_path: str) -> None:
    st.subheader("Positions")
    ok, count = _render_table_state(db_path, "positions")
    if not ok or count == 0:
        return
    df = _run_query(
        db_path,
        """
        SELECT symbol, quantity, avg_price, updated_at
        FROM positions
        ORDER BY symbol ASC
        """,
    )
    if df.empty:
        st.info("No data in table: positions")
        return
    st.dataframe(df[["symbol", "quantity", "avg_price", "updated_at"]], use_container_width=True)


def _render_reconciliation_page(db_path: str) -> None:
    st.subheader("Reconciliation")
    limit = st.slider("Reconciliation recent rows", min_value=5, max_value=200, value=30, step=5)

    events_ok, events_count = _render_table_state(db_path, "reconciliation_events")
    runs_ok, _ = _render_table_state(db_path, "reconciliation_runs")

    if events_ok and events_count > 0:
        cols = _table_columns(db_path, "reconciliation_events")
        mismatch_col = "event_type" if "event_type" in cols else "details_json"
        query = f"""
            SELECT
                reconciliation_id AS run_id,
                severity AS status,
                {mismatch_col} AS mismatch_type,
                created_at
            FROM reconciliation_events
            ORDER BY created_at DESC
            LIMIT ?
        """
        df = _run_query(db_path, query, (limit,))
        if df.empty:
            st.info("No data in table: reconciliation_events")
            return
        st.dataframe(df[["run_id", "status", "mismatch_type", "created_at"]], use_container_width=True)
        return

    if runs_ok:
        df = _run_query(
            db_path,
            """
            SELECT
                run_id,
                status,
                summary_text AS mismatch_type,
                started_at AS created_at
            FROM reconciliation_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        if df.empty:
            st.info("No data in table: reconciliation_runs")
            return
        st.dataframe(df[["run_id", "status", "mismatch_type", "created_at"]], use_container_width=True)
        return

    # If both tables are missing, messages are already shown by _render_table_state.


def _load_portfolio_trades(db_path: str, limit: int = 1000) -> tuple[pd.DataFrame, str, str]:
    trades_path = _backtest_trades_path()
    review_trades = load_trade_review_records(trades_path)
    if not review_trades.empty:
        return review_trades.copy(), "json_trade_review", trades_path

    fallback = load_trade_detail_fallback(db_path, limit=limit)
    if not fallback.empty:
        return fallback.copy(), "fallback_db", db_path

    backtest_trades = load_backtest_trade_results(trades_path)
    if not backtest_trades.empty:
        return backtest_trades.copy(), "json_backtest", trades_path
    return pd.DataFrame(), "none", ""


def _render_portfolio_source_warning(source: str, source_path: str) -> None:
    st.markdown("### Portfolio Data Provenance")
    st.warning(
        "??Portfolio Overview??Research Task artifact ?붾㈃???꾨떃?덈떎. "
        "?꾩옱 ?깃낵 ?レ옄???꾨옒 legacy/backtest trade source?먯꽌 怨꾩궛?⑸땲?? "
        "Task489/505/521/547 媛숈? task 寃곌낵? 媛숈? ?곗씠?곕줈 蹂대㈃ ???⑸땲??"
    )
    rows = [
        {"field": "page", "value": "Portfolio Overview"},
        {"field": "source_type", "value": source},
        {"field": "source_path", "value": source_path},
        {"field": "task_id", "value": "NOT_TASK_ARTIFACT"},
        {"field": "strategy_version", "value": "legacy_trades_json_or_db_fallback"},
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if source_path:
        st.markdown("**Source File / Version Hash**")
        st.dataframe(pd.DataFrame([_file_metadata(source_path, "portfolio_source")]), use_container_width=True, hide_index=True)


def _render_portfolio_overview_page(db_path: str) -> None:
    st.subheader("Portfolio Overview")
    trades, source, source_path = _load_portfolio_trades(db_path)
    if trades.empty:
        st.info("No trade data available for portfolio timeline.")
        return
    _render_portfolio_source_warning(source, source_path)

    if "entry_time" not in trades.columns:
        st.info("entry_time missing in source data.")
        return

    trades = trades.copy()
    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True, errors="coerce")
    if "exit_time" in trades.columns:
        trades["exit_time"] = pd.to_datetime(trades["exit_time"], utc=True, errors="coerce")
    trades["actual_pnl"] = pd.to_numeric(trades.get("actual_pnl"), errors="coerce")
    trades["expected_pnl"] = pd.to_numeric(trades.get("expected_pnl"), errors="coerce")
    trades["slippage"] = pd.to_numeric(trades.get("slippage"), errors="coerce")
    trades["holding_time"] = pd.to_numeric(trades.get("holding_time"), errors="coerce")
    trades = trades.dropna(subset=["entry_time"]).sort_values("entry_time").reset_index(drop=True)

    if trades.empty:
        st.info("No valid trade timeline rows.")
        return

    min_date = trades["entry_time"].dt.date.min()
    max_date = trades["entry_time"].dt.date.max()
    date_range = st.slider("Date Range", min_value=min_date, max_value=max_date, value=(min_date, max_date))

    symbol_opts = sorted({str(sym) for sym in trades.get("symbol", pd.Series(dtype=str)).dropna().tolist()})
    symbol_filter = st.selectbox("Symbol Filter", options=["ALL"] + symbol_opts, index=0)

    filtered = trades[
        (trades["entry_time"].dt.date >= date_range[0]) & (trades["entry_time"].dt.date <= date_range[1])
    ].copy()
    if symbol_filter != "ALL":
        filtered = filtered[filtered["symbol"] == symbol_filter]

    if filtered.empty:
        st.warning("No trades in selected range/filter.")
        return

    _render_trading_report(filtered)

    pnl_series = pd.to_numeric(filtered["actual_pnl"], errors="coerce").fillna(0.0)
    filtered["pnl_for_curve"] = pnl_series
    filtered["cum_pnl"] = filtered["pnl_for_curve"].cumsum()
    filtered["equity_peak"] = filtered["cum_pnl"].cummax()
    filtered["drawdown"] = filtered["equity_peak"] - filtered["cum_pnl"]
    filtered["win"] = filtered["pnl_for_curve"] > 0

    st.caption(f"Source: {source} | {source_path}")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    trade_count = int(len(filtered))
    win_rate = float((filtered["win"].sum() / trade_count) * 100.0) if trade_count > 0 else 0.0
    total_pnl = float(filtered["pnl_for_curve"].sum())
    avg_pnl = float(filtered["pnl_for_curve"].mean()) if trade_count > 0 else 0.0
    max_dd = float(filtered["drawdown"].max()) if trade_count > 0 else 0.0
    ret = filtered["pnl_for_curve"]
    sharpe = 0.0
    std_value = pd.to_numeric(ret, errors="coerce").std(ddof=0)
    if len(ret) > 1 and pd.notna(std_value):
        std = float(std_value)
        if std > 0:
            sharpe = float((ret.mean() / std) * (len(ret) ** 0.5))
    c1.metric("Total Trades", trade_count)
    c2.metric("Win Rate", f"{win_rate:.2f}%")
    c3.metric("Total PnL", f"{total_pnl:.4f}")
    c4.metric("Avg PnL", f"{avg_pnl:.4f}")
    c5.metric("Max Drawdown", f"{max_dd:.4f}")
    c6.metric("Sharpe Proxy", f"{sharpe:.4f}")

    if go is None or make_subplots is None:
        st.error("Plotly import failed. Install plotly for Portfolio Overview charts.")
        st.dataframe(filtered[["entry_time", "symbol", "pnl_for_curve", "cum_pnl", "drawdown"]], use_container_width=True)
    else:
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.46, 0.28, 0.26],
            subplot_titles=("Equity Curve", "Drawdown", "Trade Timeline"),
        )
        fig.add_trace(
            go.Scatter(
                x=filtered["entry_time"],
                y=filtered["cum_pnl"],
                mode="lines",
                name="Cumulative PnL",
                line={"color": "#1f77b4", "width": 2},
                hovertemplate="Date: %{x|%Y-%m-%d}<br>Cumulative PnL: %{y:.4f}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=filtered["entry_time"],
                y=filtered["drawdown"],
                mode="lines",
                name="Drawdown",
                line={"color": "#d62728", "width": 1.8},
                hovertemplate="Date: %{x|%Y-%m-%d}<br>Drawdown: %{y:.4f}<extra></extra>",
            ),
            row=2,
            col=1,
        )

        entry_y = pd.to_numeric(filtered.get("entry_price"), errors="coerce")
        if entry_y.isna().all():
            entry_y = filtered["cum_pnl"]
        exit_y = pd.to_numeric(filtered.get("exit_price"), errors="coerce")
        if exit_y.isna().all():
            exit_y = filtered["cum_pnl"]

        fig.add_trace(
            go.Scatter(
                x=filtered["entry_time"],
                y=entry_y,
                mode="markers",
                name="Entry",
                marker={"color": "green", "size": 10, "symbol": "circle"},
                customdata=filtered[["symbol", "trade_id", "pnl_for_curve"]],
                hovertemplate=(
                    "Entry: %{x|%Y-%m-%d}<br>"
                    "Symbol: %{customdata[0]}<br>"
                    "Trade: %{customdata[1]}<br>"
                    "PnL: %{customdata[2]:.4f}<extra></extra>"
                ),
            ),
            row=3,
            col=1,
        )
        if "exit_time" in filtered.columns and filtered["exit_time"].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=filtered["exit_time"],
                    y=exit_y,
                    mode="markers",
                    name="Exit",
                    marker={"color": "red", "size": 10, "symbol": "circle"},
                    customdata=filtered[["symbol", "trade_id", "pnl_for_curve"]],
                    hovertemplate=(
                        "Exit: %{x|%Y-%m-%d}<br>"
                        "Symbol: %{customdata[0]}<br>"
                        "Trade: %{customdata[1]}<br>"
                        "PnL: %{customdata[2]:.4f}<extra></extra>"
                    ),
                ),
                row=3,
                col=1,
            )

        fig.update_layout(height=820, margin={"l": 20, "r": 20, "t": 30, "b": 20}, hovermode="x unified")
        fig.update_yaxes(title_text="cum_pnl", row=1, col=1)
        fig.update_yaxes(title_text="drawdown", row=2, col=1)
        fig.update_yaxes(title_text="timeline", row=3, col=1)
        st.plotly_chart(fig, use_container_width=True)

    table_df = filtered.copy()
    table_df["holding_days"] = pd.to_numeric(table_df.get("holding_time"), errors="coerce") / 86400.0
    cols = ["symbol", "entry_time", "exit_time", "holding_days", "pnl_for_curve"]
    for col in cols:
        if col not in table_df.columns:
            table_df[col] = None
    st.markdown("**Position Timeline**")
    st.dataframe(
        table_df[cols].rename(columns={"pnl_for_curve": "pnl"}),
        use_container_width=True,
    )


def _render_symbol_trade_timeline_chart(trades: pd.DataFrame, *, symbol: str) -> None:
    if not symbol:
        st.info("Select a symbol to render timeline chart.")
        return
    symbol_trades = trades[trades["symbol"] == symbol].copy()
    if symbol_trades.empty:
        st.info("No trade rows for selected symbol.")
        return

    price_df = load_symbol_price_series(symbol)
    if price_df.empty or go is None or make_subplots is None:
        st.info("No OHLCV/Plotly data for timeline chart.")
        return

    symbol_trades["entry_time"] = pd.to_datetime(symbol_trades.get("entry_time"), utc=True, errors="coerce")
    symbol_trades["exit_time"] = pd.to_datetime(symbol_trades.get("exit_time"), utc=True, errors="coerce")
    symbol_trades = symbol_trades.dropna(subset=["entry_time"]).sort_values("entry_time")
    if symbol_trades.empty:
        st.info("No valid entry_time rows.")
        return

    min_t = symbol_trades["entry_time"].min() - pd.Timedelta(days=15)
    max_ref = symbol_trades["exit_time"].dropna().max()
    if pd.isna(max_ref):
        max_ref = symbol_trades["entry_time"].max()
    max_t = max_ref + pd.Timedelta(days=15)
    window_df = price_df[(price_df["timestamp"] >= min_t) & (price_df["timestamp"] <= max_t)].copy()
    if window_df.empty:
        window_df = price_df.tail(320).copy()

    window_df = _compute_indicator_frame(window_df)
    if len(window_df) > 420:
        window_df = window_df.tail(420).copy()

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25],
        subplot_titles=(f"{symbol} Trade Timeline", "Volume"),
    )
    fig.add_trace(
        go.Candlestick(
            x=window_df["timestamp"],
            open=window_df["open"],
            high=window_df["high"],
            low=window_df["low"],
            close=window_df["close"],
            name="OHLC",
            increasing_line_color="#2ca02c",
            decreasing_line_color="#d62728",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=window_df["timestamp"],
            y=window_df["ema20"],
            mode="lines",
            name="EMA20",
            line={"color": "blue", "width": 1.0},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=window_df["timestamp"],
            y=window_df["ema50"],
            mode="lines",
            name="EMA50",
            line={"color": "orange", "width": 1.0},
        ),
        row=1,
        col=1,
    )

    vol_color = ["#2ca02c" if float(c) >= float(o) else "#d62728" for c, o in zip(window_df["close"], window_df["open"], strict=False)]
    fig.add_trace(
        go.Bar(
            x=window_df["timestamp"],
            y=window_df["volume"],
            marker_color=vol_color,
            name="Volume",
            opacity=0.55,
        ),
        row=2,
        col=1,
    )

    if "entry_fill_price" not in symbol_trades.columns and "entry_price" in symbol_trades.columns:
        symbol_trades["entry_fill_price"] = symbol_trades["entry_price"]
    if "exit_fill_price" not in symbol_trades.columns and "exit_price" in symbol_trades.columns:
        symbol_trades["exit_fill_price"] = symbol_trades["exit_price"]

    entry_df = symbol_trades.dropna(subset=["entry_fill_price"]).copy()
    exit_df = symbol_trades.dropna(subset=["exit_fill_price", "exit_time"]).copy()
    if not entry_df.empty:
        fig.add_trace(
            go.Scatter(
                x=entry_df["entry_time"],
                y=pd.to_numeric(entry_df["entry_fill_price"], errors="coerce"),
                mode="markers+text",
                text=["Buy"] * len(entry_df),
                textposition="top center",
                marker={"size": 12, "color": "green", "symbol": "triangle-up", "opacity": 1.0},
                name="Buy",
                hovertemplate="BUY %{x|%Y-%m-%d}<br>Price %{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )
    if not exit_df.empty:
        fig.add_trace(
            go.Scatter(
                x=exit_df["exit_time"],
                y=pd.to_numeric(exit_df["exit_fill_price"], errors="coerce"),
                mode="markers+text",
                text=["Sell"] * len(exit_df),
                textposition="bottom center",
                marker={"size": 12, "color": "red", "symbol": "triangle-down", "opacity": 1.0},
                name="Sell",
                hovertemplate="SELL %{x|%Y-%m-%d}<br>Price %{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    fig.update_layout(
        height=760,
        margin={"l": 18, "r": 18, "t": 30, "b": 20},
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def _report_view_subset(trades: pd.DataFrame, view: str, symbol: str | None = None) -> pd.DataFrame:
    base = trades.copy()
    base["actual_pnl"] = pd.to_numeric(base.get("actual_pnl"), errors="coerce").fillna(0.0)
    by_symbol = (
        base.groupby("symbol", as_index=False)["actual_pnl"]
        .sum()
        .sort_values("actual_pnl", ascending=False)
    )
    if view == "SYMBOL" and symbol:
        return base[base["symbol"] == symbol].copy()
    if view == "TOP5":
        top = set(by_symbol.head(5)["symbol"].tolist())
        return base[base["symbol"].isin(top)].copy()
    if view == "BOTTOM5":
        bottom = set(by_symbol.tail(5)["symbol"].tolist())
        return base[base["symbol"].isin(bottom)].copy()
    return base


def _compute_profit_factor(pnls: pd.Series) -> float:
    wins = float(pnls[pnls > 0].sum())
    losses = float(pnls[pnls < 0].sum())
    if losses == 0.0:
        return float("inf")
    return wins / abs(losses)


def _render_trading_report(trades: pd.DataFrame) -> None:
    if trades.empty:
        st.info("No trade rows for report.")
        return
    trades = trades.copy()
    trades["symbol"] = trades.get("symbol", pd.Series(dtype=str)).astype(str)
    trades["actual_pnl"] = pd.to_numeric(trades.get("actual_pnl"), errors="coerce").fillna(0.0)
    trades["entry_time"] = pd.to_datetime(trades.get("entry_time"), utc=True, errors="coerce")
    trades["exit_time"] = pd.to_datetime(trades.get("exit_time"), utc=True, errors="coerce")
    trades["holding_time"] = pd.to_numeric(trades.get("holding_time"), errors="coerce")
    if trades["holding_time"].isna().all():
        trades["holding_time"] = (trades["exit_time"] - trades["entry_time"]).dt.total_seconds()

    st.markdown("**Strategy Report**")
    left, right = st.columns([2, 1])
    with left:
        view = st.radio("Report View", options=["ALL", "SYMBOL", "TOP5", "BOTTOM5"], horizontal=True)
    with right:
        symbol_options = sorted(set(trades["symbol"].dropna().tolist()))
        symbol_pick = st.selectbox("Symbol", options=symbol_options, index=0) if symbol_options else ""

    report_df = _report_view_subset(trades, view=view, symbol=symbol_pick if view == "SYMBOL" else None)
    if report_df.empty:
        st.warning("No rows for selected report view.")
        return

    pnls = report_df["actual_pnl"]
    total_pnl = float(pnls.sum())
    trade_count = int(len(report_df))
    win_rate = float((pnls > 0).sum() / trade_count * 100.0) if trade_count > 0 else 0.0
    avg_pnl = float(pnls.mean()) if trade_count > 0 else 0.0
    pf = _compute_profit_factor(pnls)
    avg_hold_hr = float(report_df["holding_time"].dropna().mean() / 3600.0) if report_df["holding_time"].notna().any() else 0.0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("珥??먯씡 (USD)", f"{total_pnl:.2f}")
    c2.metric("嫄곕옒 ?잛닔", f"{trade_count}")
    c3.metric("?밸쪧", f"{win_rate:.2f}%")
    c4.metric("?됯퇏 PnL", f"{avg_pnl:.2f}")
    c5.metric("Profit Factor", "inf" if pf == float("inf") else f"{pf:.3f}")
    c6.metric("?됯퇏 蹂댁쑀?쒓컙(h)", f"{avg_hold_hr:.2f}")

    report_df = report_df.sort_values(["exit_time", "entry_time"], na_position="last").reset_index(drop=True)
    report_df["trade_no"] = range(1, len(report_df) + 1)
    report_df["cum_pnl"] = report_df["actual_pnl"].cumsum()
    report_df["win_flag"] = report_df["actual_pnl"] > 0
    report_df["loss_flag"] = report_df["actual_pnl"] < 0

    st.markdown("**嫄곕옒 援ш컙蹂?PnL ?꾩쟻怨≪꽑**")
    if go is None:
        st.line_chart(report_df.set_index("trade_no")["cum_pnl"])
    else:
        y_min = float(min(report_df["actual_pnl"].min(), report_df["cum_pnl"].min(), 0.0))
        y_max = float(max(report_df["actual_pnl"].max(), report_df["cum_pnl"].max(), 0.0))
        if y_min == y_max:
            y_max = y_min + 1.0

        chart = make_subplots(
            rows=1,
            cols=1,
            subplot_titles=("PnL Bars + Cumulative Curve",),
        )
        chart.add_hrect(y0=0, y1=y_max, fillcolor="rgba(33, 186, 69, 0.08)", line_width=0)
        chart.add_hrect(y0=y_min, y1=0, fillcolor="rgba(219, 40, 40, 0.08)", line_width=0)
        chart.add_hline(y=0, line_dash="solid", line_color="#888888", line_width=1)

        bar_colors = ["#1f9d55" if v > 0 else ("#d64545" if v < 0 else "#9ca3af") for v in report_df["actual_pnl"]]
        chart.add_trace(
            go.Bar(
                x=report_df["trade_no"],
                y=report_df["actual_pnl"],
                marker_color=bar_colors,
                opacity=0.55,
                name="Trade PnL",
                hovertemplate="Trade #%{x}<br>PnL: %{y:.2f}<extra></extra>",
            )
        )

        cum_pos = report_df["cum_pnl"].where(report_df["cum_pnl"] >= 0)
        cum_neg = report_df["cum_pnl"].where(report_df["cum_pnl"] < 0)
        chart.add_trace(
            go.Scatter(
                x=report_df["trade_no"],
                y=cum_pos,
                mode="lines+markers",
                name="Cumulative (>=0)",
                line={"color": "#12853a", "width": 2.2},
                marker={"size": 5, "color": "#12853a"},
                hovertemplate="Trade #%{x}<br>Cumulative: %{y:.2f}<extra></extra>",
            )
        )
        chart.add_trace(
            go.Scatter(
                x=report_df["trade_no"],
                y=cum_neg,
                mode="lines+markers",
                name="Cumulative (<0)",
                line={"color": "#c81e1e", "width": 2.2},
                marker={"size": 5, "color": "#c81e1e"},
                hovertemplate="Trade #%{x}<br>Cumulative: %{y:.2f}<extra></extra>",
            )
        )

        chart.update_layout(
            height=420,
            margin={"l": 16, "r": 16, "t": 30, "b": 10},
            barmode="overlay",
            hovermode="x unified",
            xaxis_title="Trade Sequence",
            yaxis_title="USD",
        )
        st.plotly_chart(chart, use_container_width=True)

    by_symbol = (
        report_df.groupby("symbol", as_index=False)
        .agg(
            total_pnl=("actual_pnl", "sum"),
            trades=("actual_pnl", "count"),
            win_rate=("actual_pnl", lambda s: float((s > 0).sum() / max(len(s), 1) * 100.0)),
            avg_pnl=("actual_pnl", "mean"),
            start=("entry_time", "min"),
            end=("exit_time", "max"),
        )
        .sort_values("total_pnl", ascending=False)
        .reset_index(drop=True)
    )
    st.dataframe(by_symbol, use_container_width=True)


def _render_trade_detail_page(db_path: str) -> None:
    st.subheader("Trade Detail")
    limit = st.slider("Trade detail recent trades", min_value=10, max_value=300, value=50, step=10)

    trades_path = _backtest_trades_path()
    review_trades = load_trade_review_records(trades_path)
    data_source = "json"
    if not review_trades.empty:
        trades = review_trades.copy()
    else:
        fallback_trades = load_trade_detail_fallback(db_path, limit=limit)
        if not fallback_trades.empty:
            trades = fallback_trades
            data_source = "fallback"
        else:
            backtest_trades = load_backtest_trade_results(trades_path)
            if backtest_trades.empty:
                st.info("No trades found. Backtest trade file and fallback source are both empty.")
                return
            trades = backtest_trades
            data_source = "json"

    symbols = sorted({str(sym) for sym in trades.get("symbol", pd.Series(dtype=str)).dropna().tolist()})
    selected_symbol = st.selectbox("Symbol Filter", options=["ALL"] + symbols, index=0)
    pnl_filter = st.selectbox("Winner / Loser", options=["ALL", "WINNER", "LOSER"], index=0)
    regimes = sorted({str(r) for r in trades.get("regime", pd.Series(dtype=str)).dropna().tolist() if str(r)})
    selected_regime = st.selectbox("Regime Filter", options=["ALL"] + regimes, index=0)

    filtered = trades.copy()
    if selected_symbol != "ALL":
        filtered = filtered[filtered["symbol"] == selected_symbol]
    if pnl_filter == "WINNER" and "actual_pnl" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["actual_pnl"], errors="coerce") > 0]
    if pnl_filter == "LOSER" and "actual_pnl" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["actual_pnl"], errors="coerce") < 0]
    if selected_regime != "ALL" and "regime" in filtered.columns:
        filtered = filtered[filtered["regime"] == selected_regime]

    if filtered.empty:
        st.warning("No trades match the current filters.")
        return

    timeline_symbol = selected_symbol if selected_symbol != "ALL" else str(filtered.iloc[0].get("symbol", ""))
    st.markdown("**Symbol Timeline Chart**")
    _render_symbol_trade_timeline_chart(filtered, symbol=timeline_symbol)

    view_mode = st.radio("Detail View", options=["Single Trade", "Report"], horizontal=True)
    if view_mode == "Report":
        _render_trading_report(filtered)
        return

    labels = filtered.apply(
        lambda row: f"{row.get('symbol', '-')} | {row.get('entry_time', '-')} | {row.get('trade_id', '-')}",
        axis=1,
    )
    selected_label = st.selectbox("Select trade", options=labels.tolist())
    selected = filtered.iloc[labels.tolist().index(selected_label)]

    st.markdown("**Debug Info**")
    missing = _missing_fields(selected)
    debug_df = pd.DataFrame(
        [
            {"key": "trade_id", "value": selected.get("trade_id")},
            {"key": "data source", "value": data_source},
            {"key": "missing fields", "value": ", ".join(missing) if missing else "(none)"},
        ]
    )
    st.dataframe(debug_df, use_container_width=True, hide_index=True)

    st.markdown("**Price Chart**")
    diag_df = _render_trade_chart(selected)

    # Build a compact indicator source for reasoning/alignment.
    symbol = str(selected.get("symbol") or "").upper()
    price_df = load_symbol_price_series(symbol) if symbol else pd.DataFrame()

    st.markdown("**PnL Panel**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expected PnL", "N/A" if pd.isna(selected.get("expected_pnl")) else f"{selected.get('expected_pnl'):.4f}")
    c2.metric("Actual PnL", "N/A" if pd.isna(selected.get("actual_pnl")) else f"{selected.get('actual_pnl'):.4f}")
    c3.metric("Slippage", "N/A" if pd.isna(selected.get("slippage")) else f"{selected.get('slippage'):.4f}")
    c4.metric("Holding Time (sec)", "N/A" if pd.isna(selected.get("holding_time")) else f"{selected.get('holding_time'):.0f}")

    _render_reason_panel(selected, price_df)

    st.markdown("**Alignment Panel**")
    signal_reason, alignment = _derive_alignment_status(selected, price_df)
    align_df = pd.DataFrame(
        [
            {"key": "signal_reason", "value": signal_reason or "UNKNOWN"},
            {
                "key": "breakout_condition",
                "value": "Unknown" if alignment.breakout_condition is None else str(bool(alignment.breakout_condition)),
            },
            {
                "key": "ma_condition",
                "value": "Unknown" if alignment.ma_condition is None else str(bool(alignment.ma_condition)),
            },
            {
                "key": "exit_condition",
                "value": "Unknown" if alignment.exit_condition is None else str(bool(alignment.exit_condition)),
            },
            {"key": "alignment_status", "value": alignment.alignment_result},
            {
                "key": "mismatch_reasons",
                "value": ", ".join(alignment.mismatch_reasons) if alignment.mismatch_reasons else "(none)",
            },
        ]
    )
    st.dataframe(align_df, use_container_width=True, hide_index=True)
    if alignment.alignment_result == "MISMATCH":
        st.warning("Review condition does not match recorded signal reason. Possible timing / calculation alignment issue.")

    st.markdown("**Data / Indicator Diagnostics**")
    diag_extra = pd.DataFrame(
        [
            {
                "metric": "breakout_condition",
                "value": "unknown" if alignment.breakout_condition is None else str(bool(alignment.breakout_condition)).lower(),
            },
            {
                "metric": "ma_condition",
                "value": "unknown" if alignment.ma_condition is None else str(bool(alignment.ma_condition)).lower(),
            },
            {
                "metric": "exit_condition",
                "value": "unknown" if alignment.exit_condition is None else str(bool(alignment.exit_condition)).lower(),
            },
            {"metric": "alignment_result", "value": alignment.alignment_result.lower()},
        ]
    )
    diag_df = pd.concat([diag_df, diag_extra], ignore_index=True) if not diag_df.empty else diag_extra
    if diag_df.empty:
        st.info("No chart diagnostics available.")
    else:
        st.dataframe(diag_df, use_container_width=True, hide_index=True)

    st.markdown("**Meta**")
    meta = {
        "strategy_id": selected.get("strategy_id"),
        "symbol": selected.get("symbol"),
        "sector": selected.get("sector"),
        "regime": selected.get("regime"),
        "signal_bar_index": selected.get("signal_bar_index"),
        "signal_bar_time": selected.get("signal_bar_time"),
        "entry_fill_bar_time": selected.get("entry_fill_bar_time"),
        "exit_signal_bar_time": selected.get("exit_signal_bar_time"),
        "exit_fill_bar_time": selected.get("exit_fill_bar_time"),
        "entry_rule": selected.get("entry_rule"),
        "exit_rule": selected.get("exit_rule"),
        "breakout_flag": selected.get("breakout_flag"),
        "ma_trend_flag": selected.get("ma_trend_flag"),
        "trend_break_2bar_flag": selected.get("trend_break_2bar_flag"),
        "stop_hit_flag": selected.get("stop_hit_flag"),
        "entry_order_status": selected.get("entry_order_status"),
        "exit_order_status": selected.get("exit_order_status"),
        "entry_wait_bars": selected.get("entry_wait_bars"),
        "exit_wait_bars": selected.get("exit_wait_bars"),
        "unfilled_flag": selected.get("unfilled_flag"),
        "expired_flag": selected.get("expired_flag"),
        "validation_error": selected.get("validation_error"),
        "reason": selected.get("reason"),
        "source": selected.get("source"),
        "entry_time": selected.get("entry_time"),
        "exit_time": selected.get("exit_time"),
        "entry_price": selected.get("entry_price"),
        "entry_fill_price": selected.get("entry_fill_price"),
        "exit_price": selected.get("exit_price"),
        "exit_fill_price": selected.get("exit_fill_price"),
        "breakout_level": selected.get("breakout_level"),
        "stop_price": selected.get("stop_price"),
    }
    safe_meta = {k: (None if pd.isna(v) else str(v) if isinstance(v, pd.Timestamp) else v) for k, v in meta.items()}
    st.json(safe_meta)


@st.cache_data(ttl=10)
def _load_json_file(path: str) -> dict[str, Any] | list[Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


@st.cache_data(ttl=10)
def _load_text_file(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return None


def _file_metadata(path_value: object, label: str) -> dict[str, object]:
    path = Path(str(path_value or ""))
    exists = path.exists()
    row: dict[str, object] = {
        "source": label,
        "path": str(path),
        "exists": int(exists),
        "modified_utc": "",
        "size_bytes": pd.NA,
        "sha256_12": "",
    }
    if not exists or path.is_dir():
        return row
    stat = path.stat()
    row["modified_utc"] = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()
    row["size_bytes"] = stat.st_size
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        digest = ""
    row["sha256_12"] = digest[:12]
    return row


def _result_fingerprint(selected: dict[str, object], decision_path: Path, manifest: pd.DataFrame) -> str:
    payload = {
        "task_id": selected.get("task_id"),
        "task_name": selected.get("task_name"),
        "upstream_task": selected.get("upstream_task"),
        "decision_path": str(decision_path),
        "decision_sha": _file_metadata(decision_path, "decision_csv").get("sha256_12", ""),
        "artifact_rows": manifest.to_dict(orient="records") if not manifest.empty else [],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _render_selected_task_provenance(
    selected: dict[str, object],
    decision_path: Path,
    report_path: Path,
    manifest: pd.DataFrame,
) -> None:
    st.markdown("### Selected Result Provenance")
    st.caption(
        "???붾㈃???レ옄???꾨옒 task registry row, decision CSV, report markdown, artifact manifest?먯꽌留??쎌뒿?덈떎. "
        "湲곗? task? artifact hash媛 ?ㅻⅤ硫?媛숈? 諛깊뀒?ㅽ듃 寃곌낵濡?痍④툒?섎㈃ ???⑸땲??"
    )

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Task / Backtest Version", str(selected.get("task_id", "-")))
    p2.metric("Upstream", str(selected.get("upstream_task", "-")))
    p3.metric("Owner", str(selected.get("owner_team", "-")))
    p4.metric("Result Fingerprint", _result_fingerprint(selected, decision_path, manifest))

    registry_rows = [
        {"field": "task_name", "value": selected.get("task_name", "")},
        {"field": "strategy_acceptance", "value": selected.get("strategy_acceptance", "")},
        {"field": "data_readiness", "value": selected.get("data_readiness", "")},
        {"field": "decision_badge", "value": selected.get("decision_badge", "")},
        {"field": "blocker_hint", "value": selected.get("blocker_hint", "")},
        {"field": "summary", "value": selected.get("summary", "")},
        {"field": "validation_command", "value": selected.get("validation_command", "")},
    ]
    with st.expander("Registry Basis", expanded=True):
        st.dataframe(pd.DataFrame(registry_rows), use_container_width=True, hide_index=True)

    artifact_dir = Path(str(selected.get("artifact_dir", "")))
    manifest_path = artifact_dir / "artifact_manifest.csv"
    source_rows = [
        _file_metadata("tasks/task_registry.csv", "task_registry"),
        _file_metadata(decision_path, "decision_csv"),
        _file_metadata(report_path, "report_markdown"),
        _file_metadata(manifest_path, "artifact_manifest"),
    ]
    st.markdown("**Source Files / Version Hashes**")
    st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)


def _safe_read_csv(path: Path, *, nrows: int | None = None) -> pd.DataFrame:
    if not path.exists() or path.is_dir():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, nrows=nrows)
    except Exception:
        return pd.DataFrame()


def _candidate_perf_artifacts(artifact_dir: object, manifest: pd.DataFrame) -> list[Path]:
    root = Path(str(artifact_dir or ""))
    paths: list[Path] = []
    if not manifest.empty and "relative_path" in manifest.columns:
        for value in manifest["relative_path"].dropna().tolist():
            rel = str(value)
            if rel.endswith(".csv") and any(token in rel.lower() for token in ("assignment", "trade", "portfolio", "quality")):
                paths.append(root / rel)
    if root.exists():
        for path in root.glob("*.csv"):
            if any(token in path.name.lower() for token in ("assignment", "trade", "portfolio", "quality")):
                paths.append(path)
    out: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def _find_performance_artifacts(artifact_dir: object, manifest: pd.DataFrame) -> list[Path]:
    result: list[Path] = []
    for path in _candidate_perf_artifacts(artifact_dir, manifest):
        frame = _safe_read_csv(path, nrows=5)
        cols = set(frame.columns)
        if cols.intersection({"net_return_from_entry", "net_return", "net_pnl", "avg_net_pct", "avg_net_return"}):
            result.append(path)
    return result


def _net_return_pct(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.dropna().empty:
        return values
    max_abs = float(values.abs().quantile(0.95))
    return values * 100.0 if max_abs <= 2.0 else values


def _performance_column(frame: pd.DataFrame) -> str | None:
    for col in ("net_return_from_entry", "net_return", "net_pnl", "avg_net_pct", "avg_net_return"):
        if col in frame.columns:
            return col
    return None


def _win_series(frame: pd.DataFrame, pnl_col: str) -> pd.Series:
    if "win_flag" in frame.columns:
        return pd.to_numeric(frame["win_flag"], errors="coerce").fillna(0).astype(int)
    return (_net_return_pct(frame[pnl_col]) > 0).astype(int)


def _drawdown_pct_from_net(net_pct: pd.Series) -> float:
    clean = pd.to_numeric(net_pct, errors="coerce").fillna(0.0)
    if clean.empty:
        return 0.0
    equity = clean.cumsum()
    peak = equity.cummax()
    drawdown = peak - equity
    return float(drawdown.max()) if not drawdown.empty else 0.0


def _format_pct_value(value: object) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):+.2f}%"
    except Exception:
        return "-"


def _format_rate_value(value: object) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):.1f}%"
    except Exception:
        return "-"


def _status_text(flag: object) -> str:
    try:
        return "PASS" if int(float(flag or 0)) == 1 else "FAIL"
    except Exception:
        return "UNKNOWN"


def _data_quality_summary(frame: pd.DataFrame) -> pd.DataFrame:
    checks = []
    for col, label, good_value in [
        ("inferred_lifecycle_matching_used_flag", "No inferred lifecycle matching", 0),
        ("label_used_in_assignment_flag", "No label used in assignment", 0),
        ("outcome_field_used_flag", "No outcome field in assignment", 0),
        ("symbol_date_price_time_fallback_used_flag", "No symbol/date/price/time fallback", 0),
        ("unlabeled_treated_as_negative_flag", "Unlabeled not treated as negative", 0),
        ("entry_safe_feature_available_flag", "Entry-safe feature available", 1),
    ]:
        if col not in frame.columns:
            checks.append({"check": label, "status": "NOT_REPORTED", "bad_rows": pd.NA, "total_rows": len(frame)})
            continue
        values = pd.to_numeric(frame[col], errors="coerce")
        bad_rows = int((values != good_value).fillna(True).sum())
        checks.append(
            {
                "check": label,
                "status": "PASS" if bad_rows == 0 else "FAIL",
                "bad_rows": bad_rows,
                "total_rows": len(frame),
            }
        )
    return pd.DataFrame(checks)


def _split_performance(frame: pd.DataFrame, split_col: str, pnl_col: str) -> pd.DataFrame:
    if split_col not in frame.columns:
        return pd.DataFrame()
    grouped = _group_performance(frame, split_col, pnl_col)
    if grouped.empty:
        return grouped
    return grouped.rename(columns={split_col: "bucket"})


def _equity_curve_frame(frame: pd.DataFrame, pnl_col: str) -> pd.DataFrame:
    date_col = None
    for candidate in ("entry_ts", "decision_ts_utc", "timestamp", "trade_date"):
        if candidate in frame.columns:
            date_col = candidate
            break
    working = pd.DataFrame({"net_pct": _net_return_pct(frame[pnl_col])})
    if date_col:
        working["event_time"] = pd.to_datetime(frame[date_col], utc=True, errors="coerce")
        working = working.sort_values("event_time")
    else:
        working["event_time"] = range(len(working))
    working["cumulative_net_pct"] = working["net_pct"].fillna(0.0).cumsum()
    working["equity_peak_pct"] = working["cumulative_net_pct"].cummax()
    working["drawdown_pp"] = working["equity_peak_pct"] - working["cumulative_net_pct"]
    return working


def _group_performance(frame: pd.DataFrame, group_col: str, pnl_col: str) -> pd.DataFrame:
    if group_col not in frame.columns:
        return pd.DataFrame()
    working = frame[[group_col, pnl_col] + (["win_flag"] if "win_flag" in frame.columns else [])].copy()
    working["_net_pct"] = _net_return_pct(working[pnl_col])
    working["_win"] = _win_series(working, pnl_col)
    grouped = (
        working.dropna(subset=[group_col])
        .groupby(group_col, as_index=False)
        .agg(
            trades=("_net_pct", "count"),
            avg_net_pct=("_net_pct", "mean"),
            total_net_pct=("_net_pct", "sum"),
            win_rate=("_win", "mean"),
        )
    )
    if grouped.empty:
        return grouped
    grouped["win_rate"] = grouped["win_rate"] * 100.0
    return grouped.sort_values(["total_net_pct", "trades"], ascending=[False, False])


def _all_performance_sources(catalog: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for row in catalog.to_dict(orient="records"):
        manifest = load_artifact_manifest(str(row.get("artifact_dir", "")))
        for path in _find_performance_artifacts(row.get("artifact_dir", ""), manifest):
            rows.append(
                {
                    "task_id": row.get("task_id"),
                    "task_name": row.get("task_name"),
                    "strategy_acceptance": row.get("strategy_acceptance"),
                    "data_readiness": row.get("data_readiness"),
                    "artifact_path": str(path),
                    "artifact_name": path.name,
                }
            )
    return pd.DataFrame(rows)


def _render_investor_performance_dashboard(selected: dict[str, object], manifest: pd.DataFrame, catalog: pd.DataFrame) -> None:
    st.markdown("### Investor / Trader Dashboard")
    st.caption(
        "?깃낵 ?レ옄???좏깮??task artifact ?덉쓽 trade/lifecycle-level PnL 而щ읆?먯꽌留?怨꾩궛?⑸땲?? "
        "PnL 而щ읆???놁쑝硫??깃낵 ??쒕낫?쒕줈 ?꾩옣?섏? ?딄퀬 source blocker濡??쒖떆?⑸땲??"
    )

    selected_perf_paths = _find_performance_artifacts(selected.get("artifact_dir", ""), manifest)
    all_perf = _all_performance_sources(catalog)
    if not selected_perf_paths and all_perf.empty:
        st.warning(
            "??task?먮뒗 嫄곕옒蹂?PnL??怨꾩궛?????덈뒗 performance artifact媛 ?놁뒿?덈떎. "
            "?꾩옱 ?좏깮 寃곌낵???깃낵 諛깊뀒?ㅽ듃媛 ?꾨땲??source/capture/infrastructure ?깃꺽?닿퀬, ?ㅻⅨ ?깃낵 artifact??李얠? 紐삵뻽?듬땲??"
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {"required": "trade/lifecycle-level net return", "status": "missing_for_selected_task"},
                    {"required": "symbol/theme fields", "status": "unknown_until_performance_artifact_selected"},
                    {"required": "trade rationale fields", "status": "unknown_until_performance_artifact_selected"},
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        return

    if selected_perf_paths:
        source_rows = pd.DataFrame(
            [
                {
                    "task_id": selected.get("task_id"),
                    "task_name": selected.get("task_name"),
                    "strategy_acceptance": selected.get("strategy_acceptance"),
                    "data_readiness": selected.get("data_readiness"),
                    "artifact_path": str(path),
                    "artifact_name": path.name,
                }
                for path in selected_perf_paths
            ]
        )
    else:
        st.warning(
            "?꾩옱 ?좏깮 Task?먮뒗 PnL artifact媛 ?놁뒿?덈떎. ?꾨옒 ?깃낵 ?쒕뒗 ?ㅻⅨ task??performance artifact瑜?紐낆떆?곸쑝濡??좏깮?댁꽌 蹂대뒗 寃껋엯?덈떎."
        )
        source_rows = all_perf

    source_rows = source_rows.reset_index(drop=True)
    labels = (
        source_rows["task_id"].astype(str)
        + " | "
        + source_rows["artifact_name"].astype(str)
        + " | "
        + source_rows["strategy_acceptance"].astype(str)
    ).tolist()
    selected_perf_label = st.selectbox("Performance source task/artifact", options=labels, index=len(labels) - 1)
    selected_source = source_rows.iloc[labels.index(selected_perf_label)].to_dict()
    selected_perf = str(selected_source["artifact_path"])
    if str(selected_source.get("task_id")) != str(selected.get("task_id")):
        st.info(
            f"?꾩옱 ?붾㈃??selected task??{selected.get('task_id')}?닿퀬, ?깃낵 ?곗씠?곕뒗 {selected_source.get('task_id')} artifact?낅땲?? "
            "??湲곗????쇰룞?섏? 留덉떗?쒖삤."
        )
    perf_path = Path(selected_perf)
    frame = _safe_read_csv(perf_path)
    pnl_col = _performance_column(frame)
    if frame.empty or pnl_col is None:
        st.warning("Selected artifact is unreadable or has no supported PnL column.")
        return

    net_pct = _net_return_pct(frame[pnl_col])
    wins = _win_series(frame, pnl_col)
    trade_count = int(net_pct.count())
    avg_net = float(net_pct.mean()) if trade_count else 0.0
    total_net = float(net_pct.sum()) if trade_count else 0.0
    win_rate = float(wins.mean() * 100.0) if trade_count else 0.0
    max_dd = _drawdown_pct_from_net(net_pct)
    date_values = pd.Series(dtype="datetime64[ns, UTC]")
    for candidate in ("entry_ts", "decision_ts_utc", "timestamp", "trade_date"):
        if candidate in frame.columns:
            date_values = pd.to_datetime(frame[candidate], utc=True, errors="coerce").dropna()
            break
    date_range = "-"
    if not date_values.empty:
        date_range = f"{date_values.min().date()} ??{date_values.max().date()}"

    cost_basis = "not_reported"
    if "estimated_total_cost" in frame.columns:
        avg_cost = pd.to_numeric(frame["estimated_total_cost"], errors="coerce").mean()
        cost_basis = f"estimated_total_cost avg {avg_cost:.4f}" if pd.notna(avg_cost) else "estimated_total_cost reported"

    st.markdown("**Strategy / Backtest Context**")
    context_rows = [
        {"field": "performance_task", "value": selected_source.get("task_id")},
        {"field": "artifact", "value": perf_path.name},
        {"field": "strategy_acceptance", "value": selected_source.get("strategy_acceptance")},
        {"field": "data_readiness", "value": selected_source.get("data_readiness")},
        {"field": "date_range", "value": date_range},
        {"field": "cost_basis", "value": cost_basis},
    ]
    st.dataframe(pd.DataFrame(context_rows), use_container_width=True, hide_index=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Trades", f"{trade_count:,}")
    m2.metric("Avg Net / Trade", _format_pct_value(avg_net))
    m3.metric("Win Rate", _format_rate_value(win_rate))
    m4.metric("Max DD Proxy", f"{max_dd:.2f} pp")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Net Proxy", _format_pct_value(total_net))
    c2.metric("ADD/SCALE Success", _format_rate_value(pd.to_numeric(frame.get("add_scale_success_flag", pd.Series(dtype=float)), errors="coerce").mean() * 100.0))
    c3.metric("Entry Reduce", _format_rate_value(pd.to_numeric(frame.get("entry_reduce_failure_flag", pd.Series(dtype=float)), errors="coerce").mean() * 100.0))
    c4.metric("False Positive", _format_rate_value(pd.to_numeric(frame.get("false_positive_flag", pd.Series(dtype=float)), errors="coerce").mean() * 100.0))

    source_meta = pd.DataFrame(
        [
            _file_metadata(perf_path, "selected_performance_artifact"),
            {"source": "pnl_column", "path": pnl_col, "exists": 1, "modified_utc": "", "size_bytes": pd.NA, "sha256_12": ""},
        ]
    )
    st.markdown("**Performance Source / PnL Basis**")
    st.dataframe(source_meta, use_container_width=True, hide_index=True)

    quality = _data_quality_summary(frame)
    failed_quality = quality[quality["status"].eq("FAIL")]
    if failed_quality.empty:
        st.success("Data quality gate: no reported leakage/fallback failures in selected artifact.")
    else:
        st.error("Data quality gate failed. Do not treat this as clean strategy evidence.")
    st.dataframe(quality, use_container_width=True, hide_index=True)

    curve = _equity_curve_frame(frame, pnl_col)
    if not curve.empty:
        st.markdown("**Equity / Drawdown Proxy**")
        chart_frame = curve[["event_time", "cumulative_net_pct", "drawdown_pp"]].set_index("event_time")
        st.line_chart(chart_frame)

    t1, t2, t3, t4, t5 = st.tabs(["Trades", "By Symbol", "By Theme", "Splits / Quarters", "Trade Rationale"])
    with t1:
        display_cols = [
            col
            for col in [
                "lifecycle_id",
                "decision_id",
                "entry_ts",
                "simulated_exit_ts",
                "exit_ts",
                "symbol",
                "theme_id",
                pnl_col,
                "win_flag",
                "holding_days",
                "lifecycle_outcome_class",
                "exit_reason",
                "split_name",
                "quarter",
            ]
            if col in frame.columns
        ]
        view = frame[display_cols].copy()
        if pnl_col in view.columns:
            view[pnl_col] = _net_return_pct(view[pnl_col])
        st.dataframe(view.head(500), use_container_width=True, hide_index=True)
    with t2:
        symbol_perf = _group_performance(frame, "symbol", pnl_col)
        st.dataframe(symbol_perf.head(50), use_container_width=True, hide_index=True)
        if not symbol_perf.empty:
            st.bar_chart(symbol_perf.set_index("symbol")["total_net_pct"].head(25))
    with t3:
        theme_col = "theme_id" if "theme_id" in frame.columns else ("theme_regime_state_v4" if "theme_regime_state_v4" in frame.columns else "")
        theme_perf = _group_performance(frame, theme_col, pnl_col) if theme_col else pd.DataFrame()
        if theme_perf.empty:
            st.info("No theme column found in selected performance artifact.")
        else:
            st.dataframe(theme_perf.head(50), use_container_width=True, hide_index=True)
            st.bar_chart(theme_perf.set_index(theme_col)["total_net_pct"].head(25))
    with t4:
        split_rows = []
        for col in ("split_name", "quarter"):
            split_perf = _split_performance(frame, col, pnl_col)
            if not split_perf.empty:
                split_perf.insert(0, "dimension", col)
                split_rows.append(split_perf)
        if split_rows:
            st.dataframe(pd.concat(split_rows, ignore_index=True), use_container_width=True, hide_index=True)
        else:
            st.info("No split or quarter columns found in selected performance artifact.")
    with t5:
        rationale_cols = [
            col
            for col in [
                "symbol",
                "theme_id",
                "multi_day_market_state_v4",
                "theme_regime_state_v4",
                "symbol_multiday_setup_state",
                "intraday_entry_state_v4",
                "microstructure_state_v4",
                "continuation_state_v4",
                "timing_state",
                "bucket",
                "reason_codes",
                "selected_family",
                "selected_goal_portfolio_name",
                "candidate_strategy_name",
                "policy_name",
                "source_hash",
                "inferred_lifecycle_matching_used_flag",
                "label_used_in_assignment_flag",
            ]
            if col in frame.columns
        ]
        if rationale_cols:
            st.dataframe(frame[rationale_cols].head(500), use_container_width=True, hide_index=True)
        else:
            st.info("No explicit rationale columns found in selected performance artifact.")


def _render_research_reports_page() -> None:
    st.subheader("Backtest / Experiment Results")
    catalog = build_research_task_catalog()
    if catalog.empty:
        st.warning("No task registry rows found.")
        return
    latest = catalog.tail(1).iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tasks", str(len(catalog)))
    c2.metric("Latest", str(latest.get("task_id", "-")))
    c3.metric("Decision", str(latest.get("decision_badge", "-")))
    c4.metric("Deployment Ready", "YES" if int(latest.get("deployment_ready_flag", 0) or 0) else "NO")

    st.markdown("**Task Catalog**")
    display_cols = [
        "task_id",
        "task_name",
        "owner_team",
        "strategy_acceptance",
        "data_readiness",
        "decision_badge",
        "blocker_hint",
        "report_exists_flag",
        "decision_exists_flag",
        "artifact_manifest_exists_flag",
    ]
    st.dataframe(catalog[display_cols], use_container_width=True, hide_index=True)

    blocker_rows = catalog[catalog["blocker_hint"].astype(str).ne("none")][["task_id", "task_name", "blocker_hint", "data_readiness", "decision_badge"]].tail(20)
    st.markdown("**Blocker Board**")
    st.dataframe(blocker_rows, use_container_width=True, hide_index=True)

    selected_label = st.selectbox("Select task", options=(catalog["task_id"] + " | " + catalog["task_name"]).tolist(), index=len(catalog) - 1)
    selected_task_id = selected_label.split(" | ", 1)[0]
    selected = catalog[catalog["task_id"].eq(selected_task_id)].iloc[0].to_dict()
    selected_json = selected.get("decision_path")
    selected_md = selected.get("report_path")
    manifest = load_artifact_manifest(str(selected.get("artifact_dir", "")))

    data = None
    decision_path = Path(str(selected_json))
    report_path = Path(str(selected_md))
    _render_selected_task_provenance(selected, decision_path, report_path, manifest)

    if decision_path.exists():
        try:
            data = {"decision": pd.read_csv(decision_path).to_dict(orient="records")}
        except Exception:
            data = None
    md_text = _load_text_file(str(selected_md)) if selected_md else None

    _render_investor_performance_dashboard(selected, manifest, catalog)

    if isinstance(data, dict) and "decision" in data:
        st.markdown("**Decision CSV**")
        st.dataframe(pd.DataFrame(data["decision"]), use_container_width=True, hide_index=True)
    elif isinstance(data, dict):
        if "kpi_gate_result" in data:
            gate = data.get("kpi_gate_result", {})
            if isinstance(gate, dict):
                status = gate.get("status", gate.get("task_066", {}).get("status", "UNKNOWN"))
                st.metric("KPI Gate Status", str(status))
        if "revalidation_results" in data and isinstance(data["revalidation_results"], dict):
            rows: list[dict[str, Any]] = []
            for scenario_name, row in data["revalidation_results"].items():
                if isinstance(row, dict):
                    rows.append(
                        {
                            "scenario": scenario_name,
                            "trades": row.get("trades"),
                            "win_rate": row.get("win_rate"),
                            "pf": row.get("profit_factor"),
                            "net_pnl": row.get("net_pnl"),
                            "mdd": row.get("max_drawdown"),
                            "sharpe": row.get("sharpe"),
                            "fill_rate": row.get("fill_rate"),
                            "stop": row.get("stop_count"),
                            "good_then_stop": row.get("good_then_stop_count"),
                            "big_miss": row.get("big_miss_count"),
                        }
                    )
            if rows:
                st.markdown("**Scenario Comparison (S1~S6)**")
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if "s4_comparison" in data and isinstance(data["s4_comparison"], dict):
            rows = []
            for candidate, delta in data["s4_comparison"].items():
                if isinstance(delta, dict):
                    rows.append(
                        {
                            "candidate": candidate,
                            "pf_delta": delta.get("profit_factor_delta"),
                            "net_pnl_delta": delta.get("net_pnl_delta"),
                            "mdd_delta": delta.get("max_drawdown_delta"),
                            "sharpe_delta": delta.get("sharpe_delta"),
                            "trades_delta": delta.get("trades_delta"),
                        }
                    )
            if rows:
                st.markdown("**S4 Delta Comparison**")
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if "gate_attribution" in data and isinstance(data["gate_attribution"], dict):
            rows = []
            for candidate, detail in data["gate_attribution"].items():
                if isinstance(detail, dict):
                    rows.append(
                        {
                            "candidate": candidate,
                            "skipped": detail.get("skipped_by_gate"),
                            "avg_blocked_pnl": detail.get("blocked_trade_avg_estimated_pnl"),
                            "median_blocked_pnl": detail.get("blocked_trade_median_estimated_pnl"),
                            "blocked_winner_ratio": detail.get("blocked_trade_winner_ratio"),
                            "reason_breakdown": json.dumps(detail.get("skipped_by_gate_reason_breakdown", {}), ensure_ascii=False),
                        }
                    )
            if rows:
                st.markdown("**Gate Attribution**")
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if "top5" in data and isinstance(data["top5"], list):
            top_rows: list[dict[str, Any]] = []
            for idx, item in enumerate(data["top5"], start=1):
                s4 = (item.get("scenarios") or {}).get("s4_kis_realistic", {})
                top_rows.append(
                    {
                        "rank": idx,
                        "policy_group": item.get("policy_group"),
                        "time_stop_days": item.get("time_stop_days"),
                        "mfe_trigger": item.get("mfe_trigger"),
                        "giveback_ratio": item.get("giveback_ratio"),
                        "min_profit_buffer": item.get("min_profit_buffer"),
                        "pf_s4": s4.get("pf"),
                        "net_pnl_s4": s4.get("net_pnl"),
                        "mdd_s4": s4.get("mdd"),
                        "sharpe_s4": s4.get("sharpe"),
                    }
                )
            if top_rows:
                st.markdown("**Top Candidates (S4)**")
                st.dataframe(pd.DataFrame(top_rows), use_container_width=True, hide_index=True)
        if "s4_detailed_comparison" in data and isinstance(data["s4_detailed_comparison"], dict):
            s4 = data["s4_detailed_comparison"]
            delta = s4.get("delta", {})
            st.markdown("**S4 Detailed Comparison**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PF delta", f"{float(delta.get('profit_factor_delta', 0.0)):.4f}")
            c2.metric("Net PnL delta", f"{float(delta.get('net_pnl_delta', 0.0)):.2f}")
            c3.metric("MDD delta", f"{float(delta.get('max_drawdown_delta', 0.0)):.2f}")
            c4.metric("Sharpe delta", f"{float(delta.get('sharpe_delta', 0.0)):.4f}")
    elif data is None and selected_json:
        st.info(f"Decision CSV not found or unreadable: {selected_json}")

    st.markdown("**Artifact Manifest**")
    if manifest.empty:
        st.info("Artifact manifest not found.")
    else:
        st.dataframe(manifest, use_container_width=True, hide_index=True)

    st.markdown("**Report Markdown**")
    if md_text:
        st.markdown(md_text)
    else:
        st.info(f"Markdown not found or unreadable: {selected_md}")

    if data is not None:
        with st.expander("Raw JSON"):
            st.json(data)


def _render_paper_ops_monitor_page(db_path: str) -> None:
    st.subheader("Paper Ops Monitor")
    st.caption("5m data freshness + runtime signal snapshot + execution/block status")

    bars_exists = _table_exists(db_path, "market_bars_5m")
    snap_exists = _table_exists(db_path, "indicator_snapshots")

    if not bars_exists:
        st.warning("Table not found: market_bars_5m")
    if not snap_exists:
        st.warning("Table not found: indicator_snapshots")

    latest_bar_age_min = None
    latest_bar_df = _run_query(db_path, "SELECT MAX(bar_end_ts) AS latest_bar_end FROM market_bars_5m")
    if not latest_bar_df.empty and latest_bar_df.iloc[0].get("latest_bar_end"):
        latest_ts = _safe_parse_ts(latest_bar_df.iloc[0]["latest_bar_end"])
        if latest_ts:
            latest_bar_age_min = max(0.0, (datetime.now(UTC) - latest_ts).total_seconds() / 60.0)

    latest_created_df = _run_query(db_path, "SELECT MAX(created_at) AS latest_created FROM indicator_snapshots")
    latest_created = None
    if not latest_created_df.empty:
        latest_created = latest_created_df.iloc[0].get("latest_created")

    fresh_ratio = 0.0
    missing_ratio = 1.0
    entry_candidates = 0
    total_symbols = 0
    if latest_created:
        stat_df = _run_query(
            db_path,
            """
            SELECT
                COUNT(*) AS n,
                SUM(CASE WHEN data_fresh = 1 THEN 1 ELSE 0 END) AS n_fresh,
                SUM(CASE WHEN insufficient_history = 1 THEN 1 ELSE 0 END) AS n_missing,
                SUM(CASE WHEN entry_allowed = 1 THEN 1 ELSE 0 END) AS n_entry
            FROM indicator_snapshots
            WHERE created_at = ?
            """,
            (latest_created,),
        )
        if not stat_df.empty:
            total_symbols = int(stat_df.iloc[0].get("n") or 0)
            n_fresh = int(stat_df.iloc[0].get("n_fresh") or 0)
            n_missing = int(stat_df.iloc[0].get("n_missing") or 0)
            entry_candidates = int(stat_df.iloc[0].get("n_entry") or 0)
            fresh_ratio = (n_fresh / total_symbols) if total_symbols else 0.0
            missing_ratio = (n_missing / total_symbols) if total_symbols else 1.0

    unknown_df = _run_query(db_path, "SELECT COUNT(*) AS cnt FROM orders WHERE UPPER(status)='UNKNOWN'")
    unknown_cnt = int(unknown_df.iloc[0]["cnt"]) if (not unknown_df.empty and "cnt" in unknown_df.columns) else 0
    recon_df = _run_query(db_path, "SELECT COUNT(*) AS cnt FROM reconciliation_runs WHERE UPPER(max_severity)='CRITICAL'")
    recon_critical_cnt = int(recon_df.iloc[0]["cnt"]) if (not recon_df.empty and "cnt" in recon_df.columns) else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest 5m Bar Age (min)", f"{latest_bar_age_min:.1f}" if latest_bar_age_min is not None else "-")
    c2.metric("Data Fresh Ratio", f"{fresh_ratio:.2%}")
    c3.metric("Missing Bar Ratio", f"{missing_ratio:.2%}")
    c4.metric("Entry Candidates", f"{entry_candidates}/{total_symbols}")

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("UNKNOWN Orders", unknown_cnt)
    b2.metric("Recon Critical", recon_critical_cnt)
    b3.metric("Market Stale Block", "YES" if (latest_bar_age_min is not None and latest_bar_age_min > 15.0) else "NO")
    b4.metric("Latest Snapshot", str(latest_created or "-"))

    st.markdown("**Latest Runtime Signal Snapshot**")
    if latest_created:
        latest_snap_df = _run_query(
            db_path,
            """
            SELECT symbol, action, side, reason, score, data_fresh, insufficient_history, entry_allowed, candidate_rank, bar_end_ts
            FROM indicator_snapshots
            WHERE created_at = ?
            ORDER BY candidate_rank ASC
            LIMIT 30
            """,
            (latest_created,),
        )
        if latest_snap_df.empty:
            st.info("No rows in latest indicator snapshot.")
        else:
            st.dataframe(latest_snap_df, use_container_width=True)
    else:
        st.info("No indicator snapshots found.")

    st.markdown("**Recent Orders / Fills**")
    orders_df = _run_query(
        db_path,
        """
        SELECT o.order_id, o.symbol, o.status, o.submitted_at, f.filled_quantity, f.fill_price, f.filled_at
        FROM orders o
        LEFT JOIN fills f ON f.order_id = o.order_id
        ORDER BY o.submitted_at DESC
        LIMIT 30
        """,
    )
    if orders_df.empty:
        st.info("No recent orders/fills.")
    else:
        st.dataframe(orders_df, use_container_width=True)

    st.markdown("**Blocking Reasons (Derived)**")
    block_reasons: list[str] = []
    if unknown_cnt > 0:
        block_reasons.append("UNKNOWN order exists")
    if recon_critical_cnt > 0:
        block_reasons.append("reconciliation critical mismatch exists")
    if latest_bar_age_min is not None and latest_bar_age_min > 15.0:
        block_reasons.append("stale market bars (>15m)")
    if not block_reasons:
        st.success("No blocking reason detected from DB snapshot.")
    else:
        for reason in block_reasons:
            st.warning(reason)


def _inject_terminal_style() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 18% 0%, rgba(14, 165, 233, 0.08), transparent 28%),
                linear-gradient(180deg, #0a0f18 0%, #0d111a 54%, #0a0d14 100%);
        }
        .block-container {
            padding-top: 1.45rem;
            padding-bottom: 1.25rem;
            max-width: 1580px;
        }
        [data-testid="stSidebar"] {
            background: #161b26;
            border-right: 1px solid rgba(148, 163, 184, 0.16);
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        h1 {
            margin-bottom: .15rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.62);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 8px;
            padding: 10px 12px;
        }
        div[data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
        }
        .stSelectbox label, .stRadio label {
            color: #cbd5e1 !important;
            font-weight: 650;
        }
        .evidence-card {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 8px;
            padding: 12px 14px;
            background: rgba(15, 23, 42, 0.58);
            min-height: 104px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
        }
        .evidence-label {
            color: #94a3b8;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        }
        .evidence-value {
            font-size: 1.05rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 8px;
        }
        .evidence-detail {
            color: #cbd5e1;
            font-size: 0.86rem;
            line-height: 1.35;
        }
        .source-warning {
            border-left: 4px solid #f59e0b;
            padding: 10px 14px;
            background: rgba(245, 158, 11, 0.10);
            margin: 8px 0 14px 0;
        }
        .insight-strip {
            border: 1px solid rgba(45, 212, 191, 0.26);
            border-left: 4px solid #2dd4bf;
            border-radius: 8px;
            padding: 11px 14px;
            background: rgba(20, 184, 166, 0.09);
            margin: 6px 0 14px 0;
            color: #d9fbf5;
            font-size: 0.95rem;
            line-height: 1.45;
        }
        .kpi-card {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 8px;
            padding: 12px 14px;
            background: linear-gradient(180deg, rgba(20,28,42,.92), rgba(13,19,30,.72));
            min-height: 86px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.035);
        }
        .kpi-label {
            color: #9ca3af;
            font-size: .78rem;
            margin-bottom: 4px;
        }
        .kpi-value {
            color: #f8fafc;
            font-size: 1.55rem;
            font-weight: 780;
            line-height: 1.1;
        }
        .kpi-note {
            color: #94a3b8;
            font-size: .75rem;
            margin-top: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _load_selected_performance_frame(label: str, sources: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object], Path, str | None]:
    if sources.empty:
        return pd.DataFrame(), {}, Path(""), None
    labels = (
        sources["task_id"].astype(str)
        + " | "
        + sources["artifact_name"].astype(str)
        + " | "
        + sources["strategy_acceptance"].astype(str)
    ).tolist()
    index = labels.index(label) if label in labels else max(0, len(labels) - 1)
    selected_source = sources.iloc[index].to_dict()
    perf_path = Path(str(selected_source.get("artifact_path", "")))
    frame = _safe_read_csv(perf_path)
    pnl_col = _performance_column(frame)
    return frame, selected_source, perf_path, pnl_col


def _performance_source_selector(catalog: pd.DataFrame, *, key: str) -> tuple[pd.DataFrame, dict[str, object], Path, str | None]:
    sources = _all_performance_sources(catalog)
    if sources.empty:
        st.warning("No task performance artifacts found.")
        return pd.DataFrame(), {}, Path(""), None
    labels = (
        sources["task_id"].astype(str)
        + " | "
        + sources["artifact_name"].astype(str)
        + " | "
        + sources["strategy_acceptance"].astype(str)
    ).tolist()
    default_idx = len(labels) - 1
    label = st.selectbox("성과 데이터 기준", labels, index=default_idx, key=key)
    frame, selected_source, perf_path, pnl_col = _load_selected_performance_frame(label, sources)
    if pnl_col is None or frame.empty:
        st.warning("Selected performance artifact is unreadable or has no supported PnL column.")
    return frame, selected_source, perf_path, pnl_col


def _source_context_table(selected_source: dict[str, object], perf_path: Path, pnl_col: str | None) -> None:
    st.caption("성과 데이터는 선택한 task/artifact 기준입니다. 두 기준을 혼동하지 마십시오.")
    rows = [
        {"field": "task_id", "value": selected_source.get("task_id", "-")},
        {"field": "task_name", "value": selected_source.get("task_name", "-")},
        {"field": "artifact", "value": perf_path.name},
        {"field": "pnl_column", "value": pnl_col or "-"},
        {"field": "strategy_acceptance", "value": selected_source.get("strategy_acceptance", "-")},
        {"field": "data_readiness", "value": selected_source.get("data_readiness", "-")},
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.dataframe(pd.DataFrame([_file_metadata(perf_path, "selected_performance_artifact")]), use_container_width=True, hide_index=True)



def _render_source_context_expander(selected_source: dict[str, object], perf_path: Path, pnl_col: str | None) -> None:
    with st.expander("기준 데이터 / 버전 / 해시 보기", expanded=False):
        _source_context_table(selected_source, perf_path, pnl_col)


def _korean_quality_table(quality: pd.DataFrame) -> pd.DataFrame:
    name_map = {
        "No inferred lifecycle matching": "추론 기반 lifecycle 연결 없음",
        "No label used in assignment": "라벨/결과를 진입판단에 사용 안 함",
        "No outcome field in assignment": "미래 outcome 필드 사용 안 함",
        "No symbol/date/price/time fallback": "symbol/date/price/time fallback 없음",
        "Unlabeled not treated as negative": "미라벨을 손실로 처리 안 함",
        "Entry-safe feature available": "entry-safe feature 보고됨",
    }
    status_map = {"PASS": "통과", "FAIL": "실패", "NOT_REPORTED": "미보고"}
    out = quality.copy()
    if "check" in out.columns:
        out["항목"] = out["check"].map(name_map).fillna(out["check"])
    if "status" in out.columns:
        out["상태"] = out["status"].map(status_map).fillna(out["status"])
    if "bad_rows" in out.columns:
        out["문제 행"] = out["bad_rows"]
    if "total_rows" in out.columns:
        out["전체 행"] = out["total_rows"]
    cols = [col for col in ["항목", "상태", "문제 행", "전체 행"] if col in out.columns]
    return out[cols] if cols else out


def _account_insight(metrics: dict[str, float], quality: pd.DataFrame) -> str:
    quality_fail = not quality[quality["status"].eq("FAIL")].empty if "status" in quality.columns else False
    warnings: list[str] = []
    if metrics["entry_reduce"] >= 30:
        warnings.append(f"entry-reduce가 {metrics['entry_reduce']:.1f}%로 높아 실패 continuation 제거가 핵심입니다")
    if metrics["false_positive"] >= 30:
        warnings.append(f"false positive가 {metrics['false_positive']:.1f}%라 근거 신호 추가 검증이 필요합니다")
    if quality_fail:
        warnings.append("데이터 품질 gate 실패가 있어 성과 해석을 보류해야 합니다")
    if not warnings:
        warnings.append("선택 artifact 기준으로 품질 gate는 통과했고 성과 요약은 해석 가능합니다")
    return " / ".join(warnings)


def _render_evidence_card(label: str, value: object, detail: object = "") -> None:
    st.markdown(
        f"""
        <div class="evidence-card">
          <div class="evidence-label">{label}</div>
          <div class="evidence-value">{value}</div>
          <div class="evidence-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_kpi_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _friendly_strategy_label(value: object) -> str:
    text = str(value or "-")
    if text in {"", "nan", "None"}:
        return "-"
    replacements = {
        "task505": "Task505",
        "task489": "Task489",
        "theme": "테마",
        "id": "",
        "timing": "진입시간",
        "state": "",
        "regime": "레짐",
        "participation": "참여",
        "theme_participation": "테마참여",
        "trend": "추세",
        "closepos": "종가위치",
        "only": "단독",
        "strict": "엄격",
        "volume": "거래량",
        "confirmed": "확인",
        "reclaim": "회복",
        "opening": "장초반",
        "drive": "드라이브",
        "hold": "보유",
        "stop": "손절",
        "upper": "상단",
        "range": "범위",
        "midday": "장중",
        "continuation": "컨티뉴에이션",
        "accepted": "수용",
        "overextension": "과열확장",
        "leader": "리더",
        "risk": "리스크",
        "on": "ON",
        "off": "OFF",
        "broad": "광범위",
        "narrow": "협소",
        "mixed": "혼합",
        "weak": "약함",
        "strong": "강함",
    }
    parts = [part for part in text.split("_") if part]
    readable: list[str] = []
    idx = 0
    while idx < len(parts):
        part = parts[idx]
        lower = part.lower()
        next_lower = parts[idx + 1].lower() if idx + 1 < len(parts) else ""
        if lower == "theme" and next_lower == "id":
            readable.append("테마")
            idx += 2
            continue
        if lower == "timing" and next_lower == "state":
            readable.append("진입시간")
            idx += 2
            continue
        if lower == "theme" and next_lower == "participation":
            readable.append("테마참여")
            idx += 2
            continue
        if lower == "risk" and next_lower in {"on", "off"}:
            readable.append(f"리스크-{next_lower.upper()}")
            idx += 2
            continue
        if lower.startswith("avg") and lower[3:].isdigit():
            readable.append(f"평균수익≥{lower[3:]}%")
        elif lower.startswith("win") and lower[3:].isdigit():
            readable.append(f"승률≥{lower[3:]}%")
        elif lower.startswith("er") and lower[2:].isdigit():
            readable.append(f"entry-reduce≤{lower[2:]}%")
        elif lower.startswith("pos") and lower[3:].isdigit():
            readable.append(f"양수표본≥{lower[3:]}")
        elif lower.startswith("hold") and lower[4:].isdigit():
            readable.append(f"최대보유 {lower[4:]}일")
        elif lower.startswith("stop") and lower[4:].isdigit():
            readable.append(f"추적손절 {lower[4:]}%")
        elif lower.isdigit():
            readable.append(lower)
        else:
            label = replacements.get(lower, part)
            if label:
                readable.append(label)
        idx += 1
    return " · ".join(readable)


def _display_group_performance(grouped: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if grouped.empty:
        return grouped
    out = grouped.copy()
    out.insert(0, "상태/조합", out[group_col].map(_friendly_strategy_label))
    rename = {
        "trades": "거래수",
        "avg_net_pct": "평균순수익(%)",
        "total_net_pct": "누적순수익(%)",
        "win_rate": "승률(%)",
    }
    out = out.rename(columns=rename)
    keep = ["상태/조합", "거래수", "평균순수익(%)", "누적순수익(%)", "승률(%)", group_col]
    return out[[col for col in keep if col in out.columns]]


def _account_summary_metrics(frame: pd.DataFrame, pnl_col: str) -> dict[str, float]:
    net_pct = _net_return_pct(frame[pnl_col])
    wins = _win_series(frame, pnl_col)
    return {
        "trades": float(net_pct.count()),
        "avg_net": float(net_pct.mean()) if net_pct.count() else 0.0,
        "total_net": float(net_pct.sum()) if net_pct.count() else 0.0,
        "win_rate": float(wins.mean() * 100.0) if net_pct.count() else 0.0,
        "max_dd": _drawdown_pct_from_net(net_pct),
        "entry_reduce": float(pd.to_numeric(frame.get("entry_reduce_failure_flag", pd.Series(dtype=float)), errors="coerce").mean() * 100.0),
        "add_scale": float(pd.to_numeric(frame.get("add_scale_success_flag", pd.Series(dtype=float)), errors="coerce").mean() * 100.0),
        "false_positive": float(pd.to_numeric(frame.get("false_positive_flag", pd.Series(dtype=float)), errors="coerce").mean() * 100.0),
    }


def _render_account_summary_page() -> None:
    st.subheader("전체 계좌 요약")
    catalog = build_research_task_catalog()
    frame, source, perf_path, pnl_col = _performance_source_selector(catalog, key="account_source")
    if frame.empty or pnl_col is None:
        return

    metrics = _account_summary_metrics(frame, pnl_col)
    quality = _data_quality_summary(frame)
    st.markdown(
        f"<div class='insight-strip'><b>핵심 시사점</b><br>{_account_insight(metrics, quality)}</div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _render_kpi_card("거래수", f"{int(metrics['trades']):,}", "선택 artifact 기준")
    with c2:
        _render_kpi_card("평균 순수익", _format_pct_value(metrics["avg_net"]), "trade당 net")
    with c3:
        _render_kpi_card("승률", _format_rate_value(metrics["win_rate"]), "net > 0")
    with c4:
        _render_kpi_card("최대 낙폭", f"{metrics['max_dd']:.2f} pp", "proxy")
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        _render_kpi_card("누적 순수익", _format_pct_value(metrics["total_net"]), "capital path 아님")
    with c6:
        _render_kpi_card("ADD/SCALE 성공", _format_rate_value(metrics["add_scale"]), "continuation 강화")
    with c7:
        _render_kpi_card("진입 후 축소 실패", _format_rate_value(metrics["entry_reduce"]), "낮을수록 좋음")
    with c8:
        _render_kpi_card("가짜 continuation", _format_rate_value(metrics["false_positive"]), "낮을수록 좋음")

    if quality[quality["status"].eq("FAIL")].empty:
        st.success("데이터 품질: 보고된 leakage/fallback 실패 없음")
    else:
        st.error("데이터 품질 실패 존재: 성과 해석 보류")

    _render_source_context_expander(source, perf_path, pnl_col)
    with st.expander("데이터 품질 상세 보기", expanded=False):
        st.dataframe(_korean_quality_table(quality), use_container_width=True, hide_index=True)

    st.markdown("**계좌 곡선 / 낙폭 요약**")
    curve = _equity_curve_frame(frame, pnl_col)
    if not curve.empty:
        compact_curve = curve[["event_time", "cumulative_net_pct", "drawdown_pp"]].set_index("event_time")
        st.line_chart(compact_curve, height=240)

    symbol_perf = _group_performance(frame, "symbol", pnl_col)
    with st.expander("종목별 Top/Bottom 상세 보기", expanded=False):
        left, right = st.columns(2)
        with left:
            st.markdown("**상위 종목**")
            st.dataframe(symbol_perf.head(15), use_container_width=True, hide_index=True)
        with right:
            st.markdown("**하위 종목**")
            st.dataframe(symbol_perf.tail(15).sort_values("total_net_pct"), use_container_width=True, hide_index=True)


def _render_strategy_summary_page() -> None:
    st.subheader("전략 구분 요약")
    st.caption("레짐 / 테마 / 인트라데이 / 컨티뉴에이션 조합별로 어떤 상태가 수익과 실패를 만드는지 본다.")
    catalog = build_research_task_catalog()
    frame, source, perf_path, pnl_col = _performance_source_selector(catalog, key="strategy_source")
    if frame.empty or pnl_col is None:
        return
    _render_source_context_expander(source, perf_path, pnl_col)

    grouping_options = [
        col
        for col in [
            "candidate_strategy_name",
            "selected_goal_portfolio_name",
            "selected_family",
            "policy_name",
            "multi_day_market_state_v4",
            "theme_regime_state_v4",
            "symbol_multiday_setup_state",
            "intraday_entry_state_v4",
            "continuation_state_v4",
            "microstructure_state_v4",
            "timing_state",
            "quarter",
            "split_name",
        ]
        if col in frame.columns
    ]
    if not grouping_options:
        st.warning("전략/레짐 grouping 컬럼이 없습니다.")
        return
    label_map = {
        "candidate_strategy_name": "전략 후보",
        "selected_goal_portfolio_name": "포트폴리오 후보",
        "selected_family": "선택군",
        "policy_name": "정책",
        "multi_day_market_state_v4": "멀티데이 시장 레짐",
        "theme_regime_state_v4": "테마 레짐",
        "symbol_multiday_setup_state": "종목 멀티데이 구조",
        "intraday_entry_state_v4": "인트라데이 진입 구조",
        "continuation_state_v4": "컨티뉴에이션 구조",
        "microstructure_state_v4": "미시구조 상태",
        "timing_state": "진입 시간대",
        "quarter": "분기",
        "split_name": "검증 구간",
    }
    display_options = [label_map.get(col, col) for col in grouping_options]
    selected_display = st.selectbox("분석 축", display_options, index=0)
    group_col = grouping_options[display_options.index(selected_display)]
    grouped = _group_performance(frame, group_col, pnl_col)
    if not grouped.empty:
        best = grouped.iloc[0]
        worst = grouped.sort_values("total_net_pct").iloc[0]
        st.markdown(
            f"<div class='insight-strip'><b>핵심 시사점</b><br>"
            f"가장 큰 기여 상태는 {_friendly_strategy_label(best[group_col])} / 총 {best['total_net_pct']:+.2f}pp, "
            f"가장 약한 상태는 {_friendly_strategy_label(worst[group_col])} / 총 {worst['total_net_pct']:+.2f}pp 입니다.</div>",
            unsafe_allow_html=True,
        )
    display_grouped = _display_group_performance(grouped, group_col)
    st.dataframe(display_grouped, use_container_width=True, hide_index=True)
    if not grouped.empty:
        chart_df = grouped.copy()
        chart_df["표시명"] = chart_df[group_col].map(_friendly_strategy_label)
        st.bar_chart(chart_df.set_index("표시명")["total_net_pct"].head(20), height=240)

    st.markdown("**Regime × Intraday × Continuation Matrix**")
    matrix_cols = [col for col in ["multi_day_market_state_v4", "theme_regime_state_v4", "intraday_entry_state_v4", "continuation_state_v4"] if col in frame.columns]
    if len(matrix_cols) >= 2:
        matrix = frame.copy()
        matrix["_net_pct"] = _net_return_pct(matrix[pnl_col])
        matrix["_cell"] = matrix[matrix_cols].astype(str).agg(" × ".join, axis=1)
        cell_perf = (
            matrix.groupby("_cell", as_index=False)
            .agg(trades=("_net_pct", "count"), avg_net_pct=("_net_pct", "mean"), total_net_pct=("_net_pct", "sum"))
            .sort_values("total_net_pct", ascending=False)
        )
        cell_perf.insert(0, "조합", cell_perf["_cell"].map(_friendly_strategy_label))
        cell_perf = cell_perf.rename(columns={"trades": "거래수", "avg_net_pct": "평균순수익(%)", "total_net_pct": "누적순수익(%)", "_cell": "원본키"})
        with st.expander("상태 조합 상세 보기", expanded=False):
            st.dataframe(cell_perf.head(50), use_container_width=True, hide_index=True)



def _parse_json_cell(value: object) -> dict[str, object]:
    if value is None or pd.isna(value):
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _render_trade_evidence_page() -> None:
    st.subheader("트레이드별 근거")
    st.caption("개별 trade가 어떤 레짐, 진입 구조, 컨티뉴에이션 근거로 선택됐는지 한 줄 근거로 확인한다.")
    catalog = build_research_task_catalog()
    frame, source, perf_path, pnl_col = _performance_source_selector(catalog, key="trade_evidence_source")
    if frame.empty or pnl_col is None:
        return
    _render_source_context_expander(source, perf_path, pnl_col)

    symbols = sorted(frame["symbol"].dropna().astype(str).unique().tolist()) if "symbol" in frame.columns else []
    if symbols:
        symbol = st.selectbox("종목", ["ALL"] + symbols, index=0)
        if symbol != "ALL":
            frame = frame[frame["symbol"].astype(str).eq(symbol)].copy()
    if frame.empty:
        st.warning("필터 이후 표시할 trade가 없습니다.")
        return

    net_pct = _net_return_pct(frame[pnl_col])
    frame = frame.copy()
    frame["_net_pct"] = net_pct
    id_col = "lifecycle_id" if "lifecycle_id" in frame.columns else ("decision_id" if "decision_id" in frame.columns else "")
    labels = []
    for idx, row in frame.head(1000).iterrows():
        symbol_text = row.get("symbol", "-")
        ts = row.get("entry_ts", row.get("decision_ts_utc", row.get("timestamp", "")))
        labels.append(f"{idx} | {symbol_text} | {ts} | {row.get('_net_pct', 0):+.2f}%")
    selected_label = st.selectbox("트레이드", labels, index=0)
    selected_idx = int(selected_label.split(" | ", 1)[0])
    row = frame.loc[selected_idx]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("순수익", _format_pct_value(row.get("_net_pct")))
    k2.metric("승리 여부", _status_text(row.get("win_flag")))
    k3.metric("ADD/SCALE", _status_text(row.get("add_scale_success_flag")))
    k4.metric("진입 후 축소 실패", _status_text(row.get("entry_reduce_failure_flag")))

    e1, e2, e3, e4 = st.columns(4)
    with e1:
        _render_evidence_card(
            "멀티데이 레짐",
            _friendly_strategy_label(row.get("multi_day_market_state_v4", row.get("refined_market_phase", "-"))),
            f"테마={_friendly_strategy_label(row.get('theme_regime_state_v4', row.get('refined_theme_phase', '-')))}",
        )
    with e2:
        _render_evidence_card(
            "인트라데이 구조",
            _friendly_strategy_label(row.get("intraday_entry_state_v4", row.get("entry_bar_quality_state", "-"))),
            f"시간대={_friendly_strategy_label(row.get('timing_state', '-'))}",
        )
    with e3:
        _render_evidence_card(
            "컨티뉴에이션",
            _friendly_strategy_label(row.get("continuation_state_v4", row.get("symbol_multiday_setup_state", "-"))),
            f"path={row.get('event_path', row.get('lifecycle_outcome_class', '-'))}",
        )
    with e4:
        _render_evidence_card(
            "미시구조",
            _friendly_strategy_label(row.get("microstructure_state_v4", row.get("microstructure_tradability_state", "-"))),
            f"spread={row.get('spread_state', '-')} quote={row.get('quote_freshness_state', '-')}",
        )

    factors = _parse_json_cell(row.get("raw_factors_json"))
    scores = _parse_json_cell(row.get("component_scores_json"))
    with st.expander("결정 시점 raw factor / component score 보기", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Raw Factors**")
            if factors:
                st.dataframe(pd.DataFrame([{"factor": k, "value": v} for k, v in factors.items()]), use_container_width=True, hide_index=True)
            else:
                st.info("이 trade에는 raw_factors_json이 없습니다.")
        with c2:
            st.markdown("**Component Scores**")
            if scores:
                st.dataframe(pd.DataFrame([{"component": k, "score": v} for k, v in scores.items()]), use_container_width=True, hide_index=True)
            else:
                st.info("이 trade에는 component_scores_json이 없습니다.")

    rationale_cols = [
        col
        for col in [
            id_col,
            "decision_id",
            "candidate_strategy_name",
            "policy_name",
            "bucket",
            "reason_codes",
            "source_hash",
            "inferred_lifecycle_matching_used_flag",
            "label_used_in_assignment_flag",
            "label_source",
            "join_key_used",
        ]
        if col and col in frame.columns
    ]
    with st.expander("lineage / audit field 보기", expanded=False):
        st.dataframe(pd.DataFrame([row[rationale_cols].to_dict()]), use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Trading Ops UI", layout="wide")
    _inject_terminal_style()
    st.title("Continuation Trading Research Terminal")

    db_path = _db_path()
    _render_db_status(db_path)

    page = st.sidebar.radio(
        "Page",
        options=[
            "Account Summary",
            "Strategy Summary",
            "Trade Evidence",
            "Research Reports",
        ],
    )
    if not Path(db_path).exists():
        st.warning("DB file not found. UI will show table diagnostics and fallback views when possible.")

    if page == "Account Summary":
        _render_account_summary_page()
    elif page == "Strategy Summary":
        _render_strategy_summary_page()
    elif page == "Trade Evidence":
        _render_trade_evidence_page()
    elif page == "Overview":
        _render_overview_page(db_path)
    elif page == "Orders / Fills":
        _render_orders_fills_page(db_path)
    elif page == "Positions":
        _render_positions_page(db_path)
    elif page == "Reconciliation":
        _render_reconciliation_page(db_path)
    elif page == "Trade Detail":
        _render_trade_detail_page(db_path)
    elif page == "Paper Ops Monitor":
        _render_paper_ops_monitor_page(db_path)
    elif page == "Research Reports":
        _render_research_reports_page()
    else:
        _render_portfolio_overview_page(db_path)


if __name__ == "__main__":
    main()
