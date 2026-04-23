from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover - optional dependency fallback
    go = None

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from backtest.data_loader import load_daily_bars


def _db_path() -> str:
    return os.environ.get("TRADING_DB_PATH", "trading.db")


def _backtest_trades_path() -> str:
    return os.environ.get("BACKTEST_TRADES_PATH", "data/backtest/trades.json")


def _connect_read_only(db_path: str) -> sqlite3.Connection:
    uri = f"file:{Path(db_path).resolve()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    return con


def _empty_df(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _run_query(db_path: str, query: str, params: tuple = ()) -> pd.DataFrame:
    try:
        con = _connect_read_only(db_path)
    except sqlite3.OperationalError:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(query, con, params=params)
    except Exception:
        return pd.DataFrame()
    finally:
        con.close()


@st.cache_data(ttl=15)
def load_recent_runs(db_path: str, limit: int = 20) -> pd.DataFrame:
    query = """
        SELECT run_id, symbol, side, requested_quantity, started_at, finished_at, result_status, environment
        FROM trade_runs
        ORDER BY started_at DESC
        LIMIT ?
    """
    return _run_query(db_path, query, (limit,))


@st.cache_data(ttl=15)
def load_orders(db_path: str, limit: int = 100, symbol: str | None = None) -> pd.DataFrame:
    if symbol:
        query = """
            SELECT order_id, run_id, symbol, side, quantity, status, raw_status, submitted_at, environment
            FROM orders
            WHERE symbol = ?
            ORDER BY submitted_at DESC
            LIMIT ?
        """
        return _run_query(db_path, query, (symbol, limit))
    query = """
        SELECT order_id, run_id, symbol, side, quantity, status, raw_status, submitted_at, environment
        FROM orders
        ORDER BY submitted_at DESC
        LIMIT ?
    """
    return _run_query(db_path, query, (limit,))


@st.cache_data(ttl=15)
def load_fills(db_path: str, limit: int = 200, symbol: str | None = None) -> pd.DataFrame:
    if symbol:
        query = """
            SELECT fill_id, order_id, run_id, symbol, side, filled_quantity, fill_price, filled_at, source
            FROM fills
            WHERE symbol = ?
            ORDER BY filled_at DESC
            LIMIT ?
        """
        return _run_query(db_path, query, (symbol, limit))
    query = """
        SELECT fill_id, order_id, run_id, symbol, side, filled_quantity, fill_price, filled_at, source
        FROM fills
        ORDER BY filled_at DESC
        LIMIT ?
    """
    return _run_query(db_path, query, (limit,))


@st.cache_data(ttl=15)
def load_positions(db_path: str) -> pd.DataFrame:
    query = """
        SELECT symbol, side, quantity, avg_price, updated_at
        FROM positions
        ORDER BY symbol ASC
    """
    return _run_query(db_path, query)


@st.cache_data(ttl=15)
def load_reconciliation(db_path: str, limit: int = 30) -> pd.DataFrame:
    query = """
        SELECT
            rr.reconciliation_id,
            rr.run_id,
            rr.started_at,
            rr.finished_at,
            rr.status,
            rr.max_severity,
            rr.block_new_orders,
            rr.summary_text,
            (
                SELECT COUNT(*)
                FROM reconciliation_events re
                WHERE re.reconciliation_id = rr.reconciliation_id
            ) AS event_count
        FROM reconciliation_runs rr
        ORDER BY rr.started_at DESC
        LIMIT ?
    """
    return _run_query(db_path, query, (limit,))


@st.cache_data(ttl=15)
def load_reconciliation_events(db_path: str, reconciliation_id: str) -> pd.DataFrame:
    query = """
        SELECT event_id, reconciliation_id, symbol, local_order_id, broker_order_id,
               event_type, severity, local_status, broker_status, details_json, created_at
        FROM reconciliation_events
        WHERE reconciliation_id = ?
        ORDER BY created_at ASC
    """
    return _run_query(db_path, query, (reconciliation_id,))


@st.cache_data(ttl=15)
def load_backtest_trade_results(json_path: str) -> pd.DataFrame:
    path = Path(json_path)
    if not path.exists():
        return pd.DataFrame()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return pd.DataFrame()

    rows: list[dict] = []
    if isinstance(payload, dict):
        if isinstance(payload.get("trades"), list):
            rows = payload["trades"]
    elif isinstance(payload, list):
        rows = payload

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    for col in ("entry_time", "exit_time"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    if "result_status" not in df.columns:
        df["result_status"] = "BACKTEST"
    return df


@st.cache_data(ttl=15)
def load_symbol_price_series(symbol: str) -> pd.DataFrame:
    try:
        return load_daily_bars(symbol)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=15)
def load_trade_detail_fallback(db_path: str, limit: int = 50) -> pd.DataFrame:
    query = """
        SELECT
            tr.run_id AS trade_id,
            'us_swing_breakout_v0' AS strategy_id,
            tr.symbol,
            tr.side,
            tr.started_at AS entry_time,
            tr.finished_at AS exit_time,
            tr.result_status,
            o.order_id,
            o.status AS order_status,
            o.submitted_at,
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

    df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
    df["exit_time"] = pd.to_datetime(df["exit_time"], utc=True, errors="coerce")
    df["entry_price"] = df["entry_fill_price"]
    df["exit_price"] = None
    df["exit_fill_price"] = None
    df["breakout_level"] = None
    df["stop_price"] = None
    df["reason"] = "fallback_from_run_order_fill"
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
    points: list[dict] = []
    entry_t = _safe_parse_ts(trade_row.get("entry_time"))
    exit_t = _safe_parse_ts(trade_row.get("exit_time"))

    if entry_t and pd.notna(trade_row.get("entry_price")):
        points.append({"time": entry_t, "price": float(trade_row.get("entry_price")), "label": "entry_price"})
    if entry_t and pd.notna(trade_row.get("entry_fill_price")):
        points.append({"time": entry_t, "price": float(trade_row.get("entry_fill_price")), "label": "entry_fill_price"})
    if exit_t and pd.notna(trade_row.get("exit_price")):
        points.append({"time": exit_t, "price": float(trade_row.get("exit_price")), "label": "exit_price"})
    if exit_t and pd.notna(trade_row.get("exit_fill_price")):
        points.append({"time": exit_t, "price": float(trade_row.get("exit_fill_price")), "label": "exit_fill_price"})

    if not points:
        return _empty_df(["time", "price", "label"])
    return pd.DataFrame(points).sort_values("time")


def _render_trade_chart(trade_row: pd.Series) -> None:
    symbol = str(trade_row.get("symbol") or "").upper()
    price_df = load_symbol_price_series(symbol) if symbol else pd.DataFrame()
    markers = _build_trade_chart_points(trade_row)

    entry_t = _safe_parse_ts(trade_row.get("entry_time"))
    exit_t = _safe_parse_ts(trade_row.get("exit_time"))
    breakout_level = trade_row.get("breakout_level")
    stop_price = trade_row.get("stop_price")

    window_df = pd.DataFrame()
    if not price_df.empty and "timestamp" in price_df.columns:
        if entry_t is not None:
            right_anchor = exit_t or entry_t
            left = pd.Timestamp(entry_t) - pd.Timedelta(days=20)
            right = pd.Timestamp(right_anchor) + pd.Timedelta(days=20)
            window_df = price_df[(price_df["timestamp"] >= left) & (price_df["timestamp"] <= right)].copy()
        if window_df.empty:
            window_df = price_df.tail(120).copy()

    if go is None:
        if not window_df.empty:
            st.line_chart(window_df.set_index("timestamp")["close"])
        elif not markers.empty:
            st.line_chart(markers.set_index("time")["price"])
        else:
            st.info("No chartable data for this trade.")
            return
        st.caption("Plotly not available. Showing simplified line chart.")
        return

    fig = go.Figure()
    if not window_df.empty:
        fig.add_trace(
            go.Scatter(
                x=window_df["timestamp"],
                y=window_df["close"],
                mode="lines",
                name=f"{symbol}_close",
            )
        )

    if not markers.empty:
        label_style = {
            "entry_price": ("blue", "circle"),
            "entry_fill_price": ("green", "diamond"),
            "exit_price": ("orange", "square"),
            "exit_fill_price": ("red", "x"),
        }
        for label, (color, shape) in label_style.items():
            subset = markers[markers["label"] == label]
            if not subset.empty:
                fig.add_trace(
                    go.Scatter(
                        x=subset["time"],
                        y=subset["price"],
                        mode="markers",
                        marker={"size": 11, "color": color, "symbol": shape},
                        name=label,
                    )
                )

    if pd.notna(breakout_level):
        fig.add_hline(y=float(breakout_level), line_dash="dash", line_color="purple", annotation_text="breakout_level")
    if pd.notna(stop_price):
        fig.add_hline(y=float(stop_price), line_dash="dot", line_color="brown", annotation_text="stop_price")

    fig.update_layout(height=420, margin={"l": 20, "r": 20, "t": 20, "b": 20}, xaxis_title="time", yaxis_title="price")
    st.plotly_chart(fig, use_container_width=True)


def _render_overview_page(db_path: str) -> None:
    st.subheader("Overview")
    limit = st.sidebar.slider("Overview recent runs", min_value=5, max_value=100, value=20, step=5)
    runs = load_recent_runs(db_path, limit=limit)

    if runs.empty:
        st.info("No run data found. Check TRADING_DB_PATH or run the engine first.")
        return

    total = len(runs)
    failed = int((runs["result_status"] == "FAILED").sum())
    recon_block = int((runs["result_status"] == "SKIPPED_RECON_BLOCK").sum())
    idem_block = int((runs["result_status"] == "SKIPPED_DUPLICATE").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recent Runs", total)
    c2.metric("Failed", failed)
    c3.metric("RECON Block", recon_block)
    c4.metric("Idempotent Block", idem_block)

    st.dataframe(runs[["run_id", "symbol", "side", "started_at", "finished_at", "result_status", "environment"]], use_container_width=True)


def _render_orders_fills_page(db_path: str) -> None:
    st.subheader("Orders / Fills")
    limit = st.sidebar.slider("Orders/Fills recent rows", min_value=10, max_value=500, value=100, step=10)

    orders_all = load_orders(db_path, limit=500)
    if orders_all.empty:
        st.info("No order data found.")
        return

    symbols = sorted({str(s) for s in orders_all["symbol"].dropna().tolist()})
    selected_symbol = st.sidebar.selectbox("Orders symbol filter", options=["ALL"] + symbols, index=0)

    symbol_filter = None if selected_symbol == "ALL" else selected_symbol
    orders = load_orders(db_path, limit=limit, symbol=symbol_filter)
    fills = load_fills(db_path, limit=limit * 2, symbol=symbol_filter)

    latest_fill_by_order = (
        fills.sort_values("filled_at", ascending=False).drop_duplicates(subset=["order_id"], keep="first")
        if not fills.empty
        else _empty_df(["order_id", "fill_price", "filled_quantity", "filled_at"])
    )

    merged = orders.merge(
        latest_fill_by_order[[c for c in ["order_id", "fill_price", "filled_quantity", "filled_at"] if c in latest_fill_by_order.columns]],
        how="left",
        on="order_id",
    )

    merged["order_price"] = merged.get("fill_price")
    merged["created_at"] = merged.get("submitted_at")
    cols = ["order_id", "symbol", "side", "status", "order_price", "fill_price", "filled_quantity", "created_at"]
    for col in cols:
        if col not in merged.columns:
            merged[col] = None
    st.dataframe(merged[cols], use_container_width=True)


def _render_positions_page(db_path: str) -> None:
    st.subheader("Positions")
    positions = load_positions(db_path)
    if positions.empty:
        st.info("No positions found.")
        return
    st.dataframe(positions[["symbol", "quantity", "avg_price", "updated_at"]], use_container_width=True)


def _render_reconciliation_page(db_path: str) -> None:
    st.subheader("Reconciliation")
    limit = st.sidebar.slider("Reconciliation recent runs", min_value=5, max_value=200, value=30, step=5)
    recon = load_reconciliation(db_path, limit=limit)

    if recon.empty:
        st.info("No reconciliation records found.")
        return

    top_cols = ["run_id", "status", "max_severity", "event_count", "block_new_orders", "started_at"]
    for col in top_cols:
        if col not in recon.columns:
            recon[col] = None
    st.dataframe(recon[top_cols], use_container_width=True)

    options = recon["reconciliation_id"].dropna().tolist()
    selected = st.selectbox("Reconciliation run", options=options)
    events = load_reconciliation_events(db_path, selected)
    if events.empty:
        st.info("No reconciliation events for selected run.")
    else:
        cols = ["event_id", "symbol", "event_type", "severity", "local_order_id", "broker_order_id", "local_status", "broker_status", "created_at"]
        for col in cols:
            if col not in events.columns:
                events[col] = None
        st.dataframe(events[cols], use_container_width=True)


def _render_trade_detail_page(db_path: str) -> None:
    st.subheader("Trade Detail")
    limit = st.sidebar.slider("Trade detail recent trades", min_value=10, max_value=300, value=50, step=10)

    trades_path = _backtest_trades_path()
    backtest_trades = load_backtest_trade_results(trades_path)
    use_backtest = not backtest_trades.empty
    trades = backtest_trades if use_backtest else load_trade_detail_fallback(db_path, limit=limit)

    if trades.empty:
        st.info("No trades found. Backtest trade file and fallback source are both empty.")
        return

    st.caption(f"Source: {'TradeResult JSON' if use_backtest else 'fallback(run/order/fill)'}")

    labels = trades.apply(
        lambda row: f"{row.get('trade_id', '-')} | {row.get('symbol', '-')} | {row.get('entry_time', '-')}",
        axis=1,
    )
    selected_label = st.selectbox("Select trade", options=labels.tolist())
    selected = trades.iloc[labels.tolist().index(selected_label)]

    st.markdown("**Price Chart**")
    _render_trade_chart(selected)

    st.markdown("**PnL Comparison**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expected PnL", "N/A" if pd.isna(selected.get("expected_pnl")) else f"{selected.get('expected_pnl'):.4f}")
    c2.metric("Actual PnL", "N/A" if pd.isna(selected.get("actual_pnl")) else f"{selected.get('actual_pnl'):.4f}")
    c3.metric("Slippage", "N/A" if pd.isna(selected.get("slippage")) else f"{selected.get('slippage'):.4f}")
    c4.metric("Holding Time (sec)", "N/A" if pd.isna(selected.get("holding_time")) else f"{selected.get('holding_time'):.0f}")

    st.markdown("**Meta**")
    meta = {
        "strategy_id": selected.get("strategy_id"),
        "symbol": selected.get("symbol"),
        "reason": selected.get("reason"),
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


def main() -> None:
    st.set_page_config(page_title="Trading Ops UI", layout="wide")
    st.title("Trading Operations / Debug UI")

    db_path = _db_path()
    st.sidebar.markdown("### Data Source")
    st.sidebar.code(db_path)
    st.sidebar.markdown("### Backtest Trades")
    st.sidebar.code(_backtest_trades_path())

    page = st.sidebar.radio(
        "Page",
        options=["Overview", "Orders / Fills", "Positions", "Reconciliation", "Trade Detail"],
    )

    if not Path(db_path).exists():
        st.warning("DB file not found. UI will stay read-only and show empty fallback views.")

    if page == "Overview":
        _render_overview_page(db_path)
    elif page == "Orders / Fills":
        _render_orders_fills_page(db_path)
    elif page == "Positions":
        _render_positions_page(db_path)
    elif page == "Reconciliation":
        _render_reconciliation_page(db_path)
    else:
        _render_trade_detail_page(db_path)


if __name__ == "__main__":
    main()
