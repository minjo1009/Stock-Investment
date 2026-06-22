from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPORT_DIR = Path("docs/reports/task_600_3_runtime_exit_engine")
RUNTIME_EXIT_SOURCE = "PAPER_RUNTIME_SYNTHETIC_EXIT"
MATCHING_POLICY = "EXACT_POSITION_ID_AND_ENTRY_ORDER_FILL_ID_ONLY"
EXIT_REASONS = {"STOP", "TAKE_PROFIT", "TIMEOUT"}


@dataclass(frozen=True)
class ExitRules:
    stop_atr_multiple: float = 2.0
    take_profit_atr_multiple: float = 4.0
    timeout_minutes: int = 390


def utc_now() -> str:
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


def _timestamp(value: object) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def _iso(ts: pd.Timestamp) -> str:
    return ts.isoformat().replace("+00:00", "Z")


def _minutes_between(start: object, end: object) -> float | None:
    start_ts = _timestamp(start)
    end_ts = _timestamp(end)
    if start_ts is None or end_ts is None:
        return None
    return round((end_ts - start_ts).total_seconds() / 60.0, 4)


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


def _ensure_columns(con: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, type_name in columns.items():
        if name not in existing:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {type_name}")


def ensure_runtime_exit_tables(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS position_lifecycle (
                position_id TEXT,
                symbol TEXT,
                entry_order_id TEXT,
                entry_fill_id TEXT,
                exit_order_id TEXT,
                exit_fill_id TEXT,
                entry_time TEXT,
                exit_time TEXT,
                holding_minutes REAL,
                realized_pnl REAL,
                exit_reason TEXT,
                state TEXT,
                entry_price REAL,
                exit_price REAL,
                entry_qty REAL,
                open_qty REAL,
                closed_qty REAL,
                matching_policy TEXT,
                acceptance_status TEXT,
                proxy_pnl_used_flag INTEGER,
                proximity_fallback_used_flag INTEGER
            )
            """
        )
        _ensure_columns(
            con,
            "position_lifecycle",
            {
                "exit_order_id": "TEXT",
                "exit_fill_id": "TEXT",
                "exit_time": "TEXT",
                "holding_minutes": "REAL",
                "realized_pnl": "REAL",
                "exit_reason": "TEXT",
                "state": "TEXT",
                "exit_price": "REAL",
                "open_qty": "REAL",
                "closed_qty": "REAL",
                "matching_policy": "TEXT",
                "acceptance_status": "TEXT",
                "proxy_pnl_used_flag": "INTEGER",
                "proximity_fallback_used_flag": "INTEGER",
            },
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                intent_key TEXT,
                submitted_at TEXT NOT NULL,
                status TEXT NOT NULL,
                raw_status TEXT,
                environment TEXT NOT NULL
            )
            """
        )
        _ensure_columns(
            con,
            "orders",
            {
                "run_id": "TEXT",
                "symbol": "TEXT",
                "side": "TEXT",
                "quantity": "REAL",
                "intent_key": "TEXT",
                "submitted_at": "TEXT",
                "status": "TEXT",
                "raw_status": "TEXT",
                "environment": "TEXT",
            },
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS fills (
                fill_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                filled_quantity REAL NOT NULL,
                fill_price REAL,
                filled_at TEXT NOT NULL,
                source TEXT NOT NULL,
                dedupe_key TEXT
            )
            """
        )
        _ensure_columns(
            con,
            "fills",
            {
                "order_id": "TEXT",
                "run_id": "TEXT",
                "symbol": "TEXT",
                "side": "TEXT",
                "filled_quantity": "REAL",
                "fill_price": "REAL",
                "filled_at": "TEXT",
                "source": "TEXT",
                "dedupe_key": "TEXT",
            },
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS paper_order_execution_events (
                event_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                decision_id TEXT,
                client_order_id TEXT,
                order_id TEXT,
                lifecycle_id TEXT,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                limit_price REAL,
                order_status TEXT NOT NULL,
                reason_code TEXT,
                raw_response_json TEXT,
                broker_truth_fill_flag INTEGER NOT NULL DEFAULT 0,
                filled_qty REAL,
                filled_avg_price REAL,
                status_refresh_json TEXT,
                pre_order_position_qty REAL,
                post_order_position_qty REAL,
                position_delta_qty REAL,
                fill_confirmation_source TEXT
            )
            """
        )
        _ensure_columns(
            con,
            "paper_order_execution_events",
            {
                "broker_truth_fill_flag": "INTEGER NOT NULL DEFAULT 0",
                "filled_qty": "REAL",
                "filled_avg_price": "REAL",
                "status_refresh_json": "TEXT",
                "pre_order_position_qty": "REAL",
                "post_order_position_qty": "REAL",
                "position_delta_qty": "REAL",
                "fill_confirmation_source": "TEXT",
            },
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_t6003_lifecycle_position ON position_lifecycle(position_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_t6003_fills_order ON fills(order_id)")
        con.commit()
    finally:
        con.close()


def _price_snapshot_stream(indicator_snapshots: pd.DataFrame) -> pd.DataFrame:
    if indicator_snapshots.empty:
        return pd.DataFrame(columns=["symbol", "price_ts", "price", "snapshot_id", "source_type", "atr"])
    frame = indicator_snapshots.copy()
    frame["symbol"] = frame.get("symbol", pd.Series(dtype=str)).fillna("").astype(str).str.upper()
    frame["price"] = pd.to_numeric(frame.get("source_price", frame.get("close")), errors="coerce")
    if "close" in frame.columns:
        missing_price = frame["price"].isna()
        frame.loc[missing_price, "price"] = pd.to_numeric(frame.loc[missing_price, "close"], errors="coerce")
    frame["price_ts"] = pd.to_datetime(frame.get("source_price_ts", frame.get("bar_end_ts", frame.get("created_at"))), utc=True, errors="coerce")
    for fallback_col in ("bar_end_ts", "created_at"):
        if fallback_col in frame.columns:
            missing_ts = frame["price_ts"].isna()
            frame.loc[missing_ts, "price_ts"] = pd.to_datetime(frame.loc[missing_ts, fallback_col], utc=True, errors="coerce")
    atr = pd.Series([None] * len(frame), index=frame.index, dtype=object)
    for col in ("entry_atr", "atr", "atr_14", "atr14"):
        if col in frame.columns:
            atr = atr.fillna(pd.to_numeric(frame[col], errors="coerce"))
    frame["atr"] = pd.to_numeric(atr, errors="coerce")
    keep = frame.loc[frame["symbol"].ne("") & frame["price"].notna() & frame["price_ts"].notna()].copy()
    cols = [col for col in ["symbol", "price_ts", "price", "snapshot_id", "source_type", "atr"] if col in keep.columns]
    return keep[cols].sort_values(["symbol", "price_ts"]).reset_index(drop=True)


def _atr_for_position(position: pd.Series, symbol_prices: pd.DataFrame, entry_ts: pd.Timestamp) -> tuple[float | None, str]:
    for col in ("entry_atr", "atr", "atr_14", "atr14"):
        value = _float(position.get(col))
        if value is not None:
            return value, f"{col.upper()}_FROM_POSITION_LIFECYCLE"
    if not symbol_prices.empty and "atr" in symbol_prices.columns:
        eligible = symbol_prices.loc[(symbol_prices["price_ts"] >= entry_ts) & symbol_prices["atr"].notna()].copy()
        if not eligible.empty:
            return float(eligible.sort_values("price_ts").iloc[0]["atr"]), "ATR_FROM_RUNTIME_PRICE_SNAPSHOT"
    return None, "ATR_SOURCE_MISSING_NO_APPROXIMATION"


def _open_position_mask(position_lifecycle: pd.DataFrame) -> pd.Series:
    if position_lifecycle.empty:
        return pd.Series(dtype=bool)
    state = position_lifecycle.get("state", pd.Series(["OPEN"] * len(position_lifecycle), index=position_lifecycle.index)).fillna("").astype(str).str.upper()
    exit_fill = position_lifecycle.get("exit_fill_id", pd.Series([""] * len(position_lifecycle), index=position_lifecycle.index)).fillna("").astype(str)
    open_qty = pd.to_numeric(position_lifecycle.get("open_qty", pd.Series([1.0] * len(position_lifecycle), index=position_lifecycle.index)), errors="coerce").fillna(0.0)
    return state.isin({"OPEN", "PARTIAL_EXIT"}) & exit_fill.eq("") & (open_qty > 0)


def build_runtime_exit_candidates(
    position_lifecycle: pd.DataFrame,
    indicator_snapshots: pd.DataFrame,
    *,
    rules: ExitRules = ExitRules(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    price_stream = _price_snapshot_stream(indicator_snapshots)
    candidates: list[dict[str, Any]] = []
    residuals: list[dict[str, Any]] = []
    if position_lifecycle.empty:
        return pd.DataFrame(), pd.DataFrame()

    for _, position in position_lifecycle.loc[_open_position_mask(position_lifecycle)].iterrows():
        position_id = _text(position.get("position_id"))
        entry_order_id = _text(position.get("entry_order_id"))
        entry_fill_id = _text(position.get("entry_fill_id"))
        symbol = _upper(position.get("symbol"))
        entry_ts = _timestamp(position.get("entry_time"))
        entry_price = _float(position.get("entry_price"))
        qty = _float(position.get("open_qty")) or _float(position.get("entry_qty")) or 0.0
        if not position_id or not entry_order_id or not entry_fill_id or not symbol or entry_ts is None or entry_price is None or qty <= 0:
            residuals.append(
                {
                    "position_id": position_id,
                    "symbol": symbol,
                    "residual_status": "MISSING_EXACT_ENTRY_LIFECYCLE_FIELDS",
                    "matching_policy": MATCHING_POLICY,
                    "proximity_fallback_used_flag": 0,
                }
            )
            continue

        symbol_prices = price_stream.loc[price_stream["symbol"].astype(str).str.upper().eq(symbol)].copy()
        symbol_prices = symbol_prices.loc[symbol_prices["price_ts"] >= entry_ts].sort_values("price_ts")
        atr, atr_status = _atr_for_position(position, symbol_prices, entry_ts)
        stop_price = entry_price - (rules.stop_atr_multiple * atr) if atr is not None else None
        take_profit_price = entry_price + (rules.take_profit_atr_multiple * atr) if atr is not None else None
        timeout_ts = entry_ts + pd.Timedelta(minutes=rules.timeout_minutes)
        exit_reason = ""
        exit_price: float | None = None
        exit_ts: pd.Timestamp | None = None
        exit_source_status = ""

        for _, point in symbol_prices.iterrows():
            point_ts = point.get("price_ts")
            price = _float(point.get("price"))
            if point_ts is None or price is None:
                continue
            if point_ts >= timeout_ts:
                exit_reason = "TIMEOUT"
                exit_price = price
                exit_ts = point_ts
                exit_source_status = "TIMEOUT_FROM_RUNTIME_PRICE_SNAPSHOT"
                break
            if stop_price is not None and price <= stop_price:
                exit_reason = "STOP"
                exit_price = price
                exit_ts = point_ts
                exit_source_status = "STOP_FROM_RUNTIME_PRICE_SNAPSHOT"
                break
            if take_profit_price is not None and price >= take_profit_price:
                exit_reason = "TAKE_PROFIT"
                exit_price = price
                exit_ts = point_ts
                exit_source_status = "TAKE_PROFIT_FROM_RUNTIME_PRICE_SNAPSHOT"
                break

        if not exit_reason or exit_ts is None or exit_price is None:
            residuals.append(
                {
                    "position_id": position_id,
                    "symbol": symbol,
                    "residual_status": "NO_RUNTIME_EXIT_TRIGGER_OR_PRICE_SOURCE",
                    "atr_status": atr_status,
                    "matching_policy": MATCHING_POLICY,
                    "proximity_fallback_used_flag": 0,
                }
            )
            continue

        holding_minutes = _minutes_between(entry_ts, exit_ts)
        realized_pnl = round((exit_price - entry_price) * qty, 6)
        exit_order_id = f"RUNTIME_EXIT_ORDER|{position_id}|{exit_reason}"
        exit_fill_id = f"RUNTIME_EXIT_FILL|{position_id}|{exit_reason}"
        candidates.append(
            {
                "position_id": position_id,
                "symbol": symbol,
                "entry_order_id": entry_order_id,
                "entry_fill_id": entry_fill_id,
                "exit_order_id": exit_order_id,
                "exit_fill_id": exit_fill_id,
                "entry_time": _iso(entry_ts),
                "exit_time": _iso(exit_ts),
                "holding_minutes": holding_minutes,
                "entry_price": round(entry_price, 6),
                "exit_price": round(exit_price, 6),
                "entry_qty": _float(position.get("entry_qty")) or qty,
                "closed_qty": qty,
                "realized_pnl": realized_pnl,
                "exit_reason": exit_reason,
                "stop_price": None if stop_price is None else round(stop_price, 6),
                "take_profit_price": None if take_profit_price is None else round(take_profit_price, 6),
                "timeout_minutes": rules.timeout_minutes,
                "atr": atr,
                "atr_status": atr_status,
                "exit_source_status": exit_source_status,
                "source": RUNTIME_EXIT_SOURCE,
                "broker_truth_fill_flag": 0,
                "real_capital_flag": 0,
                "matching_policy": MATCHING_POLICY,
                "proximity_fallback_used_flag": 0,
                "proxy_pnl_used_flag": 0,
            }
        )
    return pd.DataFrame(candidates), pd.DataFrame(residuals)


def _exact_lifecycle_rowids(con: sqlite3.Connection, candidate: dict[str, Any]) -> list[int]:
    rows = con.execute(
        """
        SELECT rowid
        FROM position_lifecycle
        WHERE position_id = ?
          AND entry_order_id = ?
          AND entry_fill_id = ?
          AND COALESCE(exit_fill_id, '') = ''
        """,
        (
            candidate["position_id"],
            candidate["entry_order_id"],
            candidate["entry_fill_id"],
        ),
    ).fetchall()
    return [int(row[0]) for row in rows]


def _insert_runtime_exit_records(con: sqlite3.Connection, candidate: dict[str, Any]) -> None:
    run_id = f"runtime-exit-run|{candidate['position_id']}"
    order_id = candidate["exit_order_id"]
    fill_id = candidate["exit_fill_id"]
    con.execute(
        """
        INSERT OR IGNORE INTO orders(
            order_id, run_id, symbol, side, quantity, intent_key, submitted_at, status, raw_status, environment
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            order_id,
            run_id,
            candidate["symbol"],
            "SELL",
            candidate["closed_qty"],
            candidate["position_id"],
            candidate["exit_time"],
            "FILLED",
            RUNTIME_EXIT_SOURCE,
            "paper",
        ),
    )
    con.execute(
        """
        INSERT OR IGNORE INTO fills(
            fill_id, order_id, run_id, symbol, side, filled_quantity, fill_price, filled_at, source, dedupe_key
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            fill_id,
            order_id,
            run_id,
            candidate["symbol"],
            "SELL",
            candidate["closed_qty"],
            candidate["exit_price"],
            candidate["exit_time"],
            RUNTIME_EXIT_SOURCE,
            f"{candidate['position_id']}|{candidate['entry_fill_id']}|{candidate['exit_reason']}",
        ),
    )
    raw_response = {
        "runtime_execution_source": RUNTIME_EXIT_SOURCE,
        "broker_api_called": False,
        "real_capital_flag": 0,
        "matching_policy": MATCHING_POLICY,
        "entry_order_id": candidate["entry_order_id"],
        "entry_fill_id": candidate["entry_fill_id"],
    }
    con.execute(
        """
        INSERT OR REPLACE INTO paper_order_execution_events(
            event_id, created_at, decision_id, client_order_id, order_id, lifecycle_id,
            symbol, side, quantity, limit_price, order_status, reason_code, raw_response_json,
            broker_truth_fill_flag, filled_qty, filled_avg_price, fill_confirmation_source
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            f"runtime-exit-event|{fill_id}",
            candidate["exit_time"],
            candidate["position_id"],
            candidate["position_id"],
            order_id,
            candidate["position_id"],
            candidate["symbol"],
            "SELL",
            candidate["closed_qty"],
            candidate["exit_price"],
            "FILLED",
            candidate["exit_reason"],
            json.dumps(raw_response, ensure_ascii=True, sort_keys=True),
            0,
            candidate["closed_qty"],
            candidate["exit_price"],
            RUNTIME_EXIT_SOURCE,
        ),
    )


def _close_lifecycle_row(con: sqlite3.Connection, rowid: int, candidate: dict[str, Any]) -> None:
    con.execute(
        """
        UPDATE position_lifecycle
        SET exit_order_id = ?,
            exit_fill_id = ?,
            exit_time = ?,
            holding_minutes = ?,
            realized_pnl = ?,
            exit_reason = ?,
            state = 'CLOSED',
            exit_price = ?,
            open_qty = 0.0,
            closed_qty = ?,
            matching_policy = ?,
            acceptance_status = 'CLOSED_RUNTIME_PAPER_EXACT_IDS',
            proxy_pnl_used_flag = 0,
            proximity_fallback_used_flag = 0
        WHERE rowid = ?
        """,
        (
            candidate["exit_order_id"],
            candidate["exit_fill_id"],
            candidate["exit_time"],
            candidate["holding_minutes"],
            candidate["realized_pnl"],
            candidate["exit_reason"],
            candidate["exit_price"],
            candidate["closed_qty"],
            MATCHING_POLICY,
            rowid,
        ),
    )


def _distribution(closed: pd.DataFrame) -> pd.DataFrame:
    if closed.empty:
        return pd.DataFrame(columns=["exit_reason", "count", "avg_realized_pnl", "total_realized_pnl"])
    frame = closed.copy()
    frame["realized_pnl"] = pd.to_numeric(frame["realized_pnl"], errors="coerce")
    grouped = (
        frame.groupby("exit_reason", as_index=False)
        .agg(count=("position_id", "count"), avg_realized_pnl=("realized_pnl", "mean"), total_realized_pnl=("realized_pnl", "sum"))
        .sort_values("exit_reason")
        .reset_index(drop=True)
    )
    grouped["avg_realized_pnl"] = grouped["avg_realized_pnl"].round(6)
    grouped["total_realized_pnl"] = grouped["total_realized_pnl"].round(6)
    return grouped


def _runtime_closed_lifecycle(con: sqlite3.Connection) -> pd.DataFrame:
    if not _table_exists(con, "position_lifecycle"):
        return pd.DataFrame()
    return pd.read_sql_query(
        """
        SELECT *
        FROM position_lifecycle
        WHERE UPPER(COALESCE(state, '')) = 'CLOSED'
          AND COALESCE(exit_fill_id, '') LIKE 'RUNTIME_EXIT_FILL|%'
        ORDER BY exit_time, position_id
        """,
        con,
    )


def _broker_truth_runtime_sell_fills(con: sqlite3.Connection) -> int:
    if not _table_exists(con, "paper_order_execution_events"):
        return 0
    row = con.execute(
        """
        SELECT COUNT(*)
        FROM paper_order_execution_events
        WHERE UPPER(COALESCE(side, '')) = 'SELL'
          AND COALESCE(broker_truth_fill_flag, 0) = 1
        """
    ).fetchone()
    return int(row[0]) if row else 0


def apply_runtime_exit_engine(
    db_path: Path,
    *,
    rules: ExitRules = ExitRules(),
    environment: str = "paper",
) -> dict[str, pd.DataFrame]:
    if environment.strip().lower() != "paper":
        raise RuntimeError("T600-3 runtime exit engine is paper-only; real-capital execution is forbidden.")
    ensure_runtime_exit_tables(db_path)
    con = sqlite3.connect(db_path)
    try:
        position_lifecycle = _read_table(con, "position_lifecycle")
        indicator_snapshots = _read_table(con, "indicator_snapshots")
        candidates, residuals = build_runtime_exit_candidates(position_lifecycle, indicator_snapshots, rules=rules)
        applied_rows: list[dict[str, Any]] = []
        skipped_rows: list[dict[str, Any]] = []
        for candidate in candidates.to_dict(orient="records"):
            rowids = _exact_lifecycle_rowids(con, candidate)
            if len(rowids) != 1:
                skipped = dict(candidate)
                skipped["runtime_exit_status"] = "SKIPPED_NON_UNIQUE_EXACT_LIFECYCLE_LINK"
                skipped["exact_lifecycle_match_count"] = len(rowids)
                skipped_rows.append(skipped)
                continue
            _insert_runtime_exit_records(con, candidate)
            _close_lifecycle_row(con, rowids[0], candidate)
            applied = dict(candidate)
            applied["runtime_exit_status"] = "RUNTIME_PAPER_SELL_CREATED"
            applied["exact_lifecycle_match_count"] = 1
            applied_rows.append(applied)
        con.commit()
        closed = _runtime_closed_lifecycle(con)
        skipped = pd.DataFrame(skipped_rows)
        distribution = _distribution(closed)
        broker_truth_sell_fills = _broker_truth_runtime_sell_fills(con)
        summary = pd.DataFrame(
            [
                {
                    "task_id": "T600-3",
                    "runtime_exit_status": "PASS_RUNTIME_PAPER_EXIT_ENGINE" if len(closed) > 0 else "NO_RUNTIME_EXIT_CREATED",
                    "sell_fill_count": int(len(closed)),
                    "closed_positions": int(len(closed)),
                    "realized_pnl_populated": int(closed.get("realized_pnl", pd.Series(dtype=float)).notna().sum()) if not closed.empty else 0,
                    "exit_reason_populated": int(closed.get("exit_reason", pd.Series(dtype=str)).fillna("").astype(str).ne("").sum()) if not closed.empty else 0,
                    "new_runtime_paper_sell_fills": int(len(applied_rows)),
                    "broker_truth_sell_fills": broker_truth_sell_fills,
                    "real_capital_orders": 0,
                    "inferred_matching_used_flag": 0,
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                    "real_capital_status": "FORBIDDEN",
                }
            ]
        )
        return {
            "runtime_exit_summary": summary,
            "runtime_sell_fills": closed,
            "runtime_exit_distribution": distribution,
            "runtime_exit_residuals": residuals,
            "runtime_exit_skipped": skipped,
        }
    finally:
        con.close()


def _write_csv(report_dir: Path, name: str, frame: pd.DataFrame) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(report_dir / name, index=False, encoding="utf-8-sig")


def _write_five_section_report(
    path: Path,
    *,
    problem: list[str],
    evidence: list[str],
    root_cause: list[str],
    fix_candidate: list[str],
    acceptance_impact: list[str],
) -> None:
    sections = [
        ("Problem", problem),
        ("Evidence", evidence),
        ("Root Cause", root_cause),
        ("Fix Candidate", fix_candidate),
        ("Acceptance Impact", acceptance_impact),
    ]
    lines: list[str] = []
    for section, items in sections:
        lines.extend([f"## {section}", ""])
        lines.extend([f"- {item}" for item in items])
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_runtime_exit_reports(report_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = artifacts["runtime_exit_summary"].iloc[0].to_dict()
    distribution = artifacts["runtime_exit_distribution"]
    closed = artifacts["runtime_sell_fills"]
    residuals = artifacts["runtime_exit_residuals"]
    skipped = artifacts["runtime_exit_skipped"]
    _write_csv(report_dir, "runtime_sell_fills.csv", closed)
    _write_csv(report_dir, "exit_distribution.csv", distribution)
    _write_csv(report_dir, "runtime_exit_residuals.csv", residuals)
    _write_csv(report_dir, "runtime_exit_skipped.csv", skipped)
    _write_csv(
        report_dir,
        "task_600_3_decision.csv",
        pd.DataFrame(
            [
                {
                    "task_id": "T600-3",
                    "decision_status": summary["runtime_exit_status"],
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                    "real_capital_status": "FORBIDDEN",
                    "runtime_paper_sell_fills": summary["sell_fill_count"],
                    "broker_truth_sell_fills": 0,
                    "closed_positions": summary["closed_positions"],
                    "inferred_matching_used_flag": 0,
                    "next_required_task": "Controlled paper review of runtime exit evidence; strategy acceptance remains blocked.",
                }
            ]
        ),
    )
    dist_lines = (
        [
            f"{row.exit_reason}: count={row.count}, avg_realized_pnl={row.avg_realized_pnl}, total_realized_pnl={row.total_realized_pnl}"
            for row in distribution.itertuples(index=False)
        ]
        if not distribution.empty
        else ["No runtime paper exit distribution was produced."]
    )
    realized_lines = (
        [
            f"{row.position_id}: {row.symbol} {row.exit_reason} realized_pnl={row.realized_pnl} holding_minutes={row.holding_minutes}"
            for row in closed.itertuples(index=False)
        ]
        if not closed.empty
        else ["No closed runtime paper trades were produced."]
    )
    _write_five_section_report(
        report_dir / "runtime_exit_report.md",
        problem=["Runtime paper positions need exit fills and CLOSED lifecycle fields before acceptance review can inspect realized trades."],
        evidence=[
            f"runtime_paper_sell_fills={summary['sell_fill_count']}",
            f"closed_positions={summary['closed_positions']}",
            "broker_api_called=False; real_capital_orders=0",
            "matching_policy=EXACT_POSITION_ID_AND_ENTRY_ORDER_FILL_ID_ONLY",
        ],
        root_cause=["T600-1 had BUY-only lifecycle rows, and T600-2 generated diagnostic exits without writing runtime paper SELL records."],
        fix_candidate=["Use STOP, TAKE_PROFIT, and TIMEOUT triggers to create paper/runtime SELL order, fill, and execution-event rows linked by exact lifecycle IDs."],
        acceptance_impact=[
            "This creates controlled paper runtime evidence only.",
            "Strategy remains NOT_ACCEPTED and deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
        ],
    )
    _write_five_section_report(
        report_dir / "exit_distribution_report.md",
        problem=["Exit acceptance cannot inspect distribution until runtime paper exits have explicit exit_reason values."],
        evidence=dist_lines,
        root_cause=["Prior closed-trade distribution was diagnostic-only and not written as runtime paper SELL fills."],
        fix_candidate=["Summarize runtime paper closed rows by exact exit_reason without symbol/date/price/time lifecycle fallback matching."],
        acceptance_impact=[
            f"exit_reason_populated={summary['exit_reason_populated']}",
            "Distribution evidence is paper/runtime scoped and does not claim broker-truth or real-capital readiness.",
        ],
    )
    _write_five_section_report(
        report_dir / "realized_trade_report.md",
        problem=["Closed runtime rows must populate realized_pnl and holding_minutes from exact entry and exit lifecycle timestamps."],
        evidence=realized_lines,
        root_cause=["OPEN-only lifecycle state prevented realized trade reporting before T600-3."],
        fix_candidate=["Update only exact-linked lifecycle rows with exit_order_id, exit_fill_id, exit_reason, realized_pnl, and holding_minutes."],
        acceptance_impact=[
            f"realized_pnl_populated={summary['realized_pnl_populated']}",
            "Inferred lifecycle matching used flag remains 0.",
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = apply_runtime_exit_engine(args.db_path)
    write_runtime_exit_reports(args.report_dir, artifacts)
    print(artifacts["runtime_exit_summary"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
