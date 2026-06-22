from __future__ import annotations

import argparse
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from .paper_runtime_common import (
    append_registry_rows,
    latest_indicator_snapshot,
    load_runtime_env,
    utc_now,
    write_csv,
    write_task_report,
)


REPORT_DIR = Path("docs/reports/task_584_runtime_strategy_decision_gate")
RUNTIME_STATE_PANEL = Path("data/artifacts/task_567_capital_flow_regime_v6/capital_flow_regime_v6_panel.csv")


def _ensure_table(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_strategy_decisions (
                decision_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                decision_status TEXT NOT NULL,
                symbol TEXT,
                side TEXT,
                quantity INTEGER NOT NULL,
                limit_price REAL,
                reason_code TEXT NOT NULL,
                reason_detail TEXT,
                entry_allowed INTEGER NOT NULL,
                data_fresh INTEGER NOT NULL,
                selected_for_portfolio INTEGER NOT NULL,
                score REAL,
                source_snapshot_id TEXT,
                source_price_ts TEXT,
                source_type TEXT,
                regime_state TEXT,
                intraday_state TEXT,
                runtime_state_capture_status TEXT,
                state_source_snapshot_id TEXT,
                used_label_flag INTEGER NOT NULL DEFAULT 0,
                dummy_fallback_used_flag INTEGER NOT NULL DEFAULT 0,
                kis_paper_env_flag INTEGER NOT NULL DEFAULT 0,
                kill_switch_off_flag INTEGER NOT NULL DEFAULT 0,
                created_by_task TEXT NOT NULL
            )
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_runtime_decisions_created ON runtime_strategy_decisions(created_at)")
        cols = {
            str(r[1]).lower()
            for r in con.execute("PRAGMA table_info(runtime_strategy_decisions)").fetchall()
        }
        optional_cols = {
            "regime_state": "TEXT",
            "intraday_state": "TEXT",
            "runtime_state_capture_status": "TEXT",
            "state_source_snapshot_id": "TEXT",
        }
        for col, col_type in optional_cols.items():
            if col not in cols:
                con.execute(f"ALTER TABLE runtime_strategy_decisions ADD COLUMN {col} {col_type}")
        con.commit()
    finally:
        con.close()


def _kill_switch_off(db_path: Path) -> bool:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='control_state' LIMIT 1"
        ).fetchone()
        if not exists:
            return True
        row = con.execute("SELECT * FROM control_state ORDER BY rowid DESC LIMIT 1").fetchone()
        if row is None:
            return True
        text = " ".join(str(v).upper() for v in dict(row).values())
        return "KILL" not in text and "HALT" not in text and "STOP" not in text
    finally:
        con.close()


def _load_runtime_state_from_panel(symbol: str, asof_ts: object = None) -> dict[str, str]:
    symbol = str(symbol or "").upper()
    if not symbol or not RUNTIME_STATE_PANEL.exists():
        return {}
    usecols = [
        "timestamp",
        "trade_date",
        "symbol",
        "multi_day_market_state_v4",
        "theme_regime_state_v4",
        "intraday_entry_state_v4",
        "continuation_structure_v2",
        "capital_flow_regime_v6",
    ]
    try:
        panel = pd.read_csv(RUNTIME_STATE_PANEL, usecols=lambda col: col in usecols)
    except Exception:
        return {}
    if panel.empty or "symbol" not in panel.columns:
        return {}
    frame = panel.loc[panel["symbol"].astype(str).str.upper().eq(symbol)].copy()
    if frame.empty:
        return {}
    if "timestamp" in frame.columns:
        frame["_ts"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        asof = pd.to_datetime(asof_ts, utc=True, errors="coerce")
        if pd.notna(asof):
            eligible = frame.loc[frame["_ts"].le(asof)].copy()
            if not eligible.empty:
                frame = eligible
        frame = frame.sort_values("_ts")
    row = frame.iloc[-1].to_dict()
    market = str(row.get("multi_day_market_state_v4") or "")
    theme = str(row.get("theme_regime_state_v4") or "")
    regime_parts = [part for part in [market, theme] if part and part.lower() != "nan"]
    intraday = str(row.get("intraday_entry_state_v4") or row.get("continuation_structure_v2") or "")
    capital_flow = str(row.get("capital_flow_regime_v6") or "")
    state_ts = str(row.get("timestamp") or row.get("trade_date") or "")
    return {
        "regime_state": "|".join(regime_parts) if regime_parts else "",
        "intraday_state": intraday if intraday and intraday.lower() != "nan" else "",
        "capital_flow_state": capital_flow if capital_flow and capital_flow.lower() != "nan" else "",
        "state_source_snapshot_id": f"Task567:{symbol}:{state_ts}",
    }


def _runtime_state_fields(row: dict[str, Any] | None) -> dict[str, str]:
    row = row or {}
    panel_state = _load_runtime_state_from_panel(str(row.get("symbol") or ""), row.get("source_price_ts") or row.get("created_at"))
    regime = str(
        row.get("regime_state")
        or row.get("theme_regime_state_v4")
        or row.get("multi_day_market_state_v4")
        or panel_state.get("regime_state")
        or "NOT_CAPTURED_IN_RUNTIME_DB"
    )
    intraday = str(
        row.get("intraday_state")
        or row.get("intraday_entry_state_v4")
        or row.get("continuation_state_v4")
        or panel_state.get("intraday_state")
        or "NOT_CAPTURED_IN_RUNTIME_DB"
    )
    captured = regime != "NOT_CAPTURED_IN_RUNTIME_DB" and intraday != "NOT_CAPTURED_IN_RUNTIME_DB"
    return {
        "regime_state": regime,
        "intraday_state": intraday,
        "runtime_state_capture_status": "CAPTURED" if captured else "NOT_CAPTURED_IN_RUNTIME_DB",
        "state_source_snapshot_id": str(row.get("state_source_snapshot_id") or panel_state.get("state_source_snapshot_id") or row.get("snapshot_id") or ""),
    }


def _select_candidate(snapshot: pd.DataFrame, *, db_path: Path) -> dict[str, Any]:
    now = utc_now()
    if snapshot.empty:
        return {
            "decision_id": f"decision-{uuid.uuid4().hex[:16]}",
            "created_at": now,
            "decision_status": "DATA_BLOCKED",
            "symbol": "",
            "side": "NONE",
            "quantity": 0,
            "limit_price": 0.0,
            "reason_code": "NO_INDICATOR_SNAPSHOT",
            "reason_detail": "No runtime indicator snapshot exists.",
            "entry_allowed": 0,
            "data_fresh": 0,
            "selected_for_portfolio": 0,
            "score": 0.0,
            "source_snapshot_id": "",
            "source_price_ts": "",
            "source_type": "",
            **_runtime_state_fields({}),
            "used_label_flag": 0,
            "dummy_fallback_used_flag": 0,
            "kis_paper_env_flag": 0,
            "kill_switch_off_flag": int(_kill_switch_off(db_path)),
            "created_by_task": "Task584",
        }
    frame = snapshot.copy()
    for col in ("data_fresh", "entry_allowed", "selected_for_portfolio"):
        if col not in frame.columns:
            frame[col] = 0
        frame[col] = frame[col].fillna(0).astype(int)
    frame["score"] = pd.to_numeric(frame.get("score", 0.0), errors="coerce").fillna(0.0)
    paper_env = 1
    kill_off = int(_kill_switch_off(db_path))
    viable = frame.loc[
        frame["data_fresh"].eq(1)
        & frame["entry_allowed"].eq(1)
        & frame["selected_for_portfolio"].eq(1)
        & frame.get("side", pd.Series("", index=frame.index)).astype(str).str.upper().isin(["BUY", "SELL"])
    ].sort_values("score", ascending=False)
    if not viable.empty and kill_off:
        row = viable.iloc[0].to_dict()
        status = "PAPER_ORDER_CANDIDATE"
        reason = "RUNTIME_SIGNAL_SELECTED"
        qty = 1
    else:
        row = frame.sort_values(["data_fresh", "selected_for_portfolio", "score"], ascending=False).iloc[0].to_dict()
        status = "NO_TRADE" if int(row.get("data_fresh") or 0) == 1 else "DATA_BLOCKED"
        if int(row.get("data_fresh") or 0) == 0:
            reason = "STALE_DATA"
        elif not kill_off:
            reason = "KILL_SWITCH_ON"
        elif int(row.get("selected_for_portfolio") or 0) == 0:
            reason = "NOT_SELECTED_FOR_PORTFOLIO"
        elif int(row.get("entry_allowed") or 0) == 0:
            reason = "STRATEGY_FILTER_NOT_MET"
        else:
            reason = "NO_VALID_SIDE_OR_QUANTITY"
        qty = 0
    state_fields = _runtime_state_fields(row)
    return {
        "decision_id": f"decision-{uuid.uuid4().hex[:16]}",
        "created_at": now,
        "decision_status": status,
        "symbol": str(row.get("symbol") or ""),
        "side": str(row.get("side") or "NONE").upper(),
        "quantity": int(qty),
        "limit_price": float(row.get("close") or row.get("source_price") or 0.0),
        "reason_code": reason,
        "reason_detail": str(row.get("reason") or ""),
        "entry_allowed": int(row.get("entry_allowed") or 0),
        "data_fresh": int(row.get("data_fresh") or 0),
        "selected_for_portfolio": int(row.get("selected_for_portfolio") or 0),
        "score": float(row.get("score") or 0.0),
        "source_snapshot_id": str(row.get("snapshot_id") or ""),
        "source_price_ts": str(row.get("source_price_ts") or ""),
        "source_type": str(row.get("source_type") or ""),
        **state_fields,
        "used_label_flag": 0,
        "dummy_fallback_used_flag": 0,
        "kis_paper_env_flag": paper_env,
        "kill_switch_off_flag": kill_off,
        "created_by_task": "Task584",
    }


def _no_trade_decomposition(snapshot: pd.DataFrame) -> pd.DataFrame:
    if snapshot.empty:
        return pd.DataFrame(
            [
                {
                    "symbol": "",
                    "blocker_category": "DATA_BLOCKED_NO_SNAPSHOT",
                    "owner": "윤헌",
                    "decision_implication": "NO_PAPER_ORDER_CANDIDATE",
                    "unblock_condition": "Create provider-backed indicator snapshot before runtime decision.",
                    "data_fresh": 0,
                    "selected_for_portfolio": 0,
                    "entry_allowed": 0,
                    "side": "NONE",
                    "score": 0.0,
                    "source_snapshot_id": "",
                    "source_price_ts": "",
                    "source_type": "",
                    "regime_state": "NOT_CAPTURED_IN_RUNTIME_DB",
                    "intraday_state": "NOT_CAPTURED_IN_RUNTIME_DB",
                    "runtime_state_capture_status": "NOT_CAPTURED_IN_RUNTIME_DB",
                }
            ]
        )
    frame = snapshot.copy()
    for col in ("data_fresh", "entry_allowed", "selected_for_portfolio"):
        if col not in frame.columns:
            frame[col] = 0
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0).astype(int)
    if "side" not in frame.columns:
        frame["side"] = "NONE"
    frame["score"] = pd.to_numeric(frame.get("score", 0.0), errors="coerce").fillna(0.0)
    rows: list[dict[str, Any]] = []
    for _, raw in frame.iterrows():
        row = raw.to_dict()
        side = str(row.get("side") or "NONE").upper()
        if int(row.get("data_fresh") or 0) == 0:
            category = "DATA_BLOCKED_STALE_SOURCE"
            owner = "윤헌"
            unblock = "Refresh live/runtime source and rerun Task583; stale source is blocker, not negative signal."
        elif int(row.get("selected_for_portfolio") or 0) == 0:
            category = "PORTFOLIO_FILTER_BLOCKED"
            owner = "필수"
            unblock = "Review portfolio selection/ranking policy for this symbol without using future labels."
        elif int(row.get("entry_allowed") or 0) == 0:
            category = "STRATEGY_FILTER_BLOCKED"
            owner = "필수+성원"
            unblock = "Decompose regime/intraday condition failure and decide whether rule change is justified by OOS evidence."
        elif side not in {"BUY", "SELL"}:
            category = "SIDE_CONTRACT_BLOCKED"
            owner = "Execution & Risk"
            unblock = "Emit explicit BUY/SELL side before order handoff."
        else:
            category = "READY_PAPER_ORDER_CANDIDATE"
            owner = "Execution & Risk"
            unblock = "Candidate can proceed to order handoff if risk and kill switch allow."
        state_fields = _runtime_state_fields(row)
        rows.append(
            {
                "symbol": str(row.get("symbol") or "").upper(),
                "blocker_category": category,
                "owner": owner,
                "decision_implication": "PAPER_ORDER_CANDIDATE" if category == "READY_PAPER_ORDER_CANDIDATE" else "NO_PAPER_ORDER_CANDIDATE",
                "unblock_condition": unblock,
                "data_fresh": int(row.get("data_fresh") or 0),
                "selected_for_portfolio": int(row.get("selected_for_portfolio") or 0),
                "entry_allowed": int(row.get("entry_allowed") or 0),
                "side": side,
                "score": float(row.get("score") or 0.0),
                "source_snapshot_id": str(row.get("snapshot_id") or ""),
                "source_price_ts": str(row.get("source_price_ts") or ""),
                "source_type": str(row.get("source_type") or ""),
                **state_fields,
            }
        )
    order = {
        "READY_PAPER_ORDER_CANDIDATE": 0,
        "STRATEGY_FILTER_BLOCKED": 1,
        "PORTFOLIO_FILTER_BLOCKED": 2,
        "SIDE_CONTRACT_BLOCKED": 3,
        "DATA_BLOCKED_STALE_SOURCE": 4,
    }
    out = pd.DataFrame(rows)
    out["_order"] = out["blocker_category"].map(order).fillna(9)
    return out.sort_values(["_order", "score", "symbol"], ascending=[True, False, True]).drop(columns=["_order"]).reset_index(drop=True)


def _insert_decision(db_path: Path, row: dict[str, Any]) -> None:
    _ensure_table(db_path)
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT OR REPLACE INTO runtime_strategy_decisions(
                decision_id, created_at, decision_status, symbol, side, quantity, limit_price,
                reason_code, reason_detail, entry_allowed, data_fresh, selected_for_portfolio,
                score, source_snapshot_id, source_price_ts, source_type, regime_state, intraday_state,
                runtime_state_capture_status, state_source_snapshot_id, used_label_flag,
                dummy_fallback_used_flag, kis_paper_env_flag, kill_switch_off_flag, created_by_task
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                row["decision_id"],
                row["created_at"],
                row["decision_status"],
                row["symbol"],
                row["side"],
                row["quantity"],
                row["limit_price"],
                row["reason_code"],
                row["reason_detail"],
                row["entry_allowed"],
                row["data_fresh"],
                row["selected_for_portfolio"],
                row["score"],
                row["source_snapshot_id"],
                row["source_price_ts"],
                row["source_type"],
                row["regime_state"],
                row["intraday_state"],
                row["runtime_state_capture_status"],
                row["state_source_snapshot_id"],
                row["used_label_flag"],
                row["dummy_fallback_used_flag"],
                row["kis_paper_env_flag"],
                row["kill_switch_off_flag"],
                row["created_by_task"],
            ),
        )
        con.commit()
    finally:
        con.close()


def run_task584(*, db_path: Path) -> dict[str, pd.DataFrame]:
    load_runtime_env()
    snapshot = latest_indicator_snapshot(db_path)
    row = _select_candidate(snapshot, db_path=db_path)
    _insert_decision(db_path, row)
    decision_log = pd.DataFrame([row])
    candidate_audit = decision_log.copy()
    no_trade_decomposition = _no_trade_decomposition(snapshot)
    decomposition_counts = no_trade_decomposition["blocker_category"].astype(str).value_counts().to_dict() if not no_trade_decomposition.empty else {}
    no_trade = decision_log.loc[decision_log["decision_status"].ne("PAPER_ORDER_CANDIDATE")].copy()
    no_trade["human_reason_ko"] = no_trade["reason_code"].map(
        {
            "NO_INDICATOR_SNAPSHOT": "런타임 신호 스냅샷이 없습니다.",
            "STALE_DATA": "가격/신호 데이터가 오래되어 거래하지 않았습니다.",
            "STRATEGY_FILTER_NOT_MET": "신호는 최신이지만 전략 조건을 통과하지 못했습니다.",
            "NOT_SELECTED_FOR_PORTFOLIO": "포트폴리오 후보로 선택되지 않았습니다.",
            "KILL_SWITCH_ON": "킬스위치가 켜져 있어 거래하지 않았습니다.",
        }
    ).fillna("주문 후보 조건을 충족하지 못했습니다.")
    status = str(row["decision_status"])
    task_decision = pd.DataFrame(
        [
            {
                "task_id": "Task584",
                "task_name": "Runtime Strategy Decision Gate",
                "decision_status": status,
                "runtime_decision_id": row["decision_id"],
                "symbol": row["symbol"],
                "reason_code": row["reason_code"],
                "regime_state": row["regime_state"],
                "intraday_state": row["intraday_state"],
                "runtime_state_capture_status": row["runtime_state_capture_status"],
                "state_source_snapshot_id": row["state_source_snapshot_id"],
                "paper_order_candidate_flag": int(status == "PAPER_ORDER_CANDIDATE"),
                "decomposition_rows": int(len(no_trade_decomposition)),
                "data_blocked_rows": int(decomposition_counts.get("DATA_BLOCKED_STALE_SOURCE", 0) + decomposition_counts.get("DATA_BLOCKED_NO_SNAPSHOT", 0)),
                "portfolio_filter_blocked_rows": int(decomposition_counts.get("PORTFOLIO_FILTER_BLOCKED", 0)),
                "strategy_filter_blocked_rows": int(decomposition_counts.get("STRATEGY_FILTER_BLOCKED", 0)),
                "side_contract_blocked_rows": int(decomposition_counts.get("SIDE_CONTRACT_BLOCKED", 0)),
                "ready_candidate_rows": int(decomposition_counts.get("READY_PAPER_ORDER_CANDIDATE", 0)),
                "dummy_fallback_used_flag": 0,
                "used_label_flag": 0,
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
            }
        ]
    )
    artifacts = {
        "runtime_strategy_decision_log.csv": decision_log,
        "runtime_candidate_selection_audit.csv": candidate_audit,
        "runtime_no_trade_reason_audit.csv": no_trade,
        "runtime_no_trade_decomposition_audit.csv": no_trade_decomposition,
        "task_584_decision.csv": task_decision,
    }
    for name, frame in artifacts.items():
        write_csv(REPORT_DIR, name, frame)
    write_task_report(
        REPORT_DIR,
        "task_584_runtime_strategy_decision_gate.md",
        title="Task584 - Runtime Strategy Decision Gate",
        decision_summary=[
            f"decision_status={status}",
            f"decision_id={row['decision_id']}",
            f"reason_code={row['reason_code']}",
            f"runtime_state_capture_status={row['runtime_state_capture_status']}",
            "dummy fallback is forbidden and was not used.",
        ],
        quant_lines=[
            "Runtime assignment uses only the latest indicator snapshot fields generated before order action.",
            "Backtest labels, outcomes, and historical PnL are not used in the runtime decision gate.",
            "The gate emits DATA_BLOCKED, NO_TRADE, or PAPER_ORDER_CANDIDATE with reason codes.",
            "The no-trade decomposition audit separates stale data, portfolio filter, strategy filter, side contract, and ready-candidate rows for owner-specific remediation.",
        ],
        decision_maker_lines=[
            "이번 단계는 주문 전 최종 판단 기록입니다.",
            "거래가 안 되면 왜 안 됐는지 reason_code로 남기고, 거래 가능하면 decision_id가 생성됩니다.",
            "이 decision_id가 다음 주문 단계의 client_order_id 역할을 합니다.",
        ],
    )
    append_registry_rows(
        [
            {
                "task_id": "Task584",
                "title": "Runtime Strategy Decision Gate",
                "owner_team": "Intraday Continuation Research",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "diagnostic-only",
                "data_readiness": "runtime-source",
                "parent_task": "Task583",
                "key_report": str(REPORT_DIR / "task_584_runtime_strategy_decision_gate.md"),
                "key_decision": str(REPORT_DIR / "task_584_decision.csv"),
                "key_artifacts": str(REPORT_DIR),
                "validation_command": "python -m unittest tests.test_task584_runtime_strategy_decision_gate",
                "notes": "Creates pre-order runtime decision snapshots with reason codes.",
            }
        ]
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    args = parser.parse_args()
    artifacts = run_task584(db_path=args.db_path)
    print(artifacts["task_584_decision.csv"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
