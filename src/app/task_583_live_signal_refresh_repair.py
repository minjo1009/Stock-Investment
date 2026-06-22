from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from .task_089_market_data_signal_refresh import THEME_UNIVERSE_SCOPE, load_theme_universe_symbols
from .paper_runtime_common import (
    append_registry_rows,
    latest_indicator_snapshot,
    load_runtime_env,
    read_table,
    utc_now,
    write_csv,
    write_task_report,
)


REPORT_DIR = Path("docs/reports/task_583_live_signal_refresh_repair")
RAW_INTRADAY_ROOT = Path("data/raw/us_intraday")
RAW_DAILY_ROOT = Path("data/raw/us_daily")


def _resolve_universe(symbols: str) -> tuple[list[str], str, str]:
    if symbols.strip():
        resolved = sorted({s.strip().upper() for s in symbols.split(",") if s.strip()})
        return resolved, "explicit_symbols", ",".join(resolved)
    resolved = load_theme_universe_symbols()
    return resolved, THEME_UNIVERSE_SCOPE, ",".join(resolved)


def _run_task089(db_path: Path, env_file: Path, symbols: str = "") -> tuple[str, str, int]:
    env = {**os.environ}
    src_path = str(Path("src").resolve())
    env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cmd = [
        sys.executable,
        "-m",
        "app.task_089_market_data_signal_refresh",
        "--db-path",
        str(db_path),
        "--env-file",
        str(env_file),
        "--json-out",
        str(REPORT_DIR / "task_089_runtime_refresh.json"),
        "--md-out",
        str(REPORT_DIR / "task_089_runtime_refresh.md"),
    ]
    if symbols:
        cmd.extend(["--symbols", symbols])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=180, env=env)
    return proc.stdout[-4000:], proc.stderr[-4000:], int(proc.returncode)


def _latest_indicator_snapshot_per_symbol(db_path: Path, expected_symbols: list[str]) -> pd.DataFrame:
    limit = max(len(expected_symbols) * 200, 1000)
    frame = read_table(db_path, "indicator_snapshots", order_by="created_at", limit=limit)
    if frame.empty or "symbol" not in frame.columns:
        return latest_indicator_snapshot(db_path)
    work = frame.copy()
    work["symbol"] = work["symbol"].astype(str).str.upper()
    expected = {symbol.upper() for symbol in expected_symbols}
    if expected:
        work = work.loc[work["symbol"].isin(expected)].copy()
    if work.empty:
        return latest_indicator_snapshot(db_path)
    work = work.sort_values("created_at")
    return work.groupby("symbol", as_index=False).tail(1).reset_index(drop=True)


def _coverage_status(*, expected_count: int, evaluated_count: int, fresh_count: int) -> str:
    if expected_count <= 0:
        return "UNIVERSE_SCOPE_EMPTY"
    if evaluated_count < expected_count:
        return "UNIVERSE_COVERAGE_GAP"
    if fresh_count < expected_count:
        return "FULL_UNIVERSE_EVALUATED_WITH_SOURCE_GAPS"
    return "FULL_UNIVERSE_EVALUATED"


def _freshness_audit(snapshot: pd.DataFrame, *, expected_symbols: list[str] | None = None, universe_scope: str = "explicit_symbols") -> pd.DataFrame:
    if expected_symbols is None:
        expected_symbols = (
            sorted(snapshot["symbol"].dropna().astype(str).str.upper().unique().tolist())
            if not snapshot.empty and "symbol" in snapshot.columns
            else []
        )
    expected_count = len(expected_symbols)
    if snapshot.empty:
        return pd.DataFrame(
            [
                {
                    "audit_ts_utc": utc_now(),
                    "universe_scope": universe_scope,
                    "expected_universe_count": expected_count,
                    "evaluated_symbol_count": 0,
                    "fresh_symbol_count": 0,
                    "selected_symbol_count": 0,
                    "missing_or_stale_symbol_count": expected_count,
                    "coverage_status": _coverage_status(expected_count=expected_count, evaluated_count=0, fresh_count=0),
                    "latest_snapshot_created_at": "",
                    "rows": 0,
                    "fresh_rows": 0,
                    "entry_allowed_rows": 0,
                    "selected_fresh_rows": 0,
                    "latest_source_price_ts": "",
                    "max_freshness_age_sec": None,
                    "top_stale_reason": "NO_INDICATOR_SNAPSHOT",
                }
            ]
        )
    fresh = snapshot["data_fresh"].fillna(0).astype(int) if "data_fresh" in snapshot.columns else pd.Series([], dtype=int)
    selected = snapshot["selected_for_portfolio"].fillna(0).astype(int) if "selected_for_portfolio" in snapshot.columns else pd.Series(0, index=snapshot.index)
    entry = snapshot["entry_allowed"].fillna(0).astype(int) if "entry_allowed" in snapshot.columns else pd.Series(0, index=snapshot.index)
    evaluated_symbols = set(snapshot.get("symbol", pd.Series(dtype=str)).dropna().astype(str).str.upper())
    fresh_symbols = set(snapshot.loc[fresh.eq(1), "symbol"].dropna().astype(str).str.upper()) if "symbol" in snapshot.columns and len(fresh) else set()
    selected_symbols = set(snapshot.loc[selected.eq(1), "symbol"].dropna().astype(str).str.upper()) if "symbol" in snapshot.columns and len(selected) else set()
    expected_set = set(expected_symbols)
    missing_or_stale = len((expected_set - fresh_symbols) | (expected_set - evaluated_symbols))
    stale_reason = ""
    if "stale_reason" in snapshot.columns and not snapshot["stale_reason"].dropna().empty:
        stale_reason = str(snapshot["stale_reason"].dropna().astype(str).replace("", pd.NA).dropna().head(1).iloc[0]) if not snapshot["stale_reason"].dropna().replace("", pd.NA).dropna().empty else ""
    return pd.DataFrame(
        [
                {
                    "audit_ts_utc": utc_now(),
                    "universe_scope": universe_scope,
                    "expected_universe_count": expected_count,
                    "evaluated_symbol_count": len(evaluated_symbols),
                    "fresh_symbol_count": len(fresh_symbols),
                    "selected_symbol_count": len(selected_symbols),
                    "missing_or_stale_symbol_count": int(missing_or_stale),
                    "coverage_status": _coverage_status(
                        expected_count=expected_count,
                        evaluated_count=len(evaluated_symbols),
                        fresh_count=len(fresh_symbols),
                    ),
                    "latest_snapshot_created_at": str(snapshot["created_at"].astype(str).max()) if "created_at" in snapshot.columns else "",
                "rows": len(snapshot),
                "fresh_rows": int(fresh.sum()) if len(fresh) else 0,
                "entry_allowed_rows": int(entry.sum()) if len(entry) else 0,
                "selected_fresh_rows": int(((fresh == 1) & (selected == 1)).sum()) if len(fresh) else 0,
                "latest_source_price_ts": str(snapshot.get("source_price_ts", pd.Series([""])).astype(str).max()),
                "max_freshness_age_sec": float(pd.to_numeric(snapshot.get("freshness_age_sec", pd.Series([0])), errors="coerce").max()),
                "top_stale_reason": stale_reason,
            }
        ]
    )


def _runtime_candidates(snapshot: pd.DataFrame, *, expected_symbols: list[str] | None = None, universe_scope: str = "explicit_symbols") -> pd.DataFrame:
    if expected_symbols is None:
        expected_symbols = (
            sorted(snapshot["symbol"].dropna().astype(str).str.upper().unique().tolist())
            if not snapshot.empty and "symbol" in snapshot.columns
            else []
        )
    expected_count = len(expected_symbols)
    if snapshot.empty:
        rows = expected_symbols or [""]
        return pd.DataFrame(
            [
                {
                    "candidate_status": "DATA_BLOCKED_NO_SNAPSHOT" if not symbol else "DATA_BLOCKED_MISSING_SOURCE",
                    "symbol_status": "MISSING_SOURCE",
                    "universe_scope": universe_scope,
                    "expected_universe_count": expected_count,
                    "evaluated_symbol_count": 0,
                    "fresh_symbol_count": 0,
                    "selected_symbol_count": 0,
                    "missing_or_stale_symbol_count": expected_count,
                    "coverage_status": _coverage_status(expected_count=expected_count, evaluated_count=0, fresh_count=0),
                    "symbol": symbol,
                    "data_fresh": 0,
                    "entry_allowed": 0,
                    "selected_for_portfolio": 0,
                    "reason": "NO_INDICATOR_SNAPSHOT" if not symbol else "MISSING_SOURCE",
                    "source_type": "",
                    "freshness_age_sec": None,
                }
                for symbol in rows
            ]
        )
    frame = snapshot.copy()
    for col in ("data_fresh", "entry_allowed", "selected_for_portfolio"):
        if col not in frame.columns:
            frame[col] = 0
        frame[col] = frame[col].fillna(0).astype(int)
    frame["candidate_status"] = "NO_TRADE"
    frame.loc[frame["data_fresh"].eq(0), "candidate_status"] = "NO_TRADE_STALE_DATA"
    frame.loc[
        frame["data_fresh"].eq(1) & frame["entry_allowed"].eq(1) & frame["selected_for_portfolio"].eq(1),
        "candidate_status",
    ] = "PAPER_ORDER_CANDIDATE"
    frame["symbol"] = frame["symbol"].astype(str).str.upper() if "symbol" in frame.columns else ""
    frame["symbol_status"] = "FRESH_EVALUATED"
    frame.loc[frame["data_fresh"].eq(0), "symbol_status"] = "STALE_SOURCE"
    frame.loc[frame["data_fresh"].eq(1) & frame["selected_for_portfolio"].eq(0), "symbol_status"] = "NOT_SELECTED_BY_PORTFOLIO"
    frame.loc[frame["data_fresh"].eq(1) & frame["entry_allowed"].eq(1), "symbol_status"] = "ENTRY_ALLOWED"
    expected_set = set(expected_symbols)
    evaluated_symbols = set(frame.get("symbol", pd.Series(dtype=str)).dropna().astype(str).str.upper())
    fresh_symbols = set(frame.loc[frame["data_fresh"].eq(1), "symbol"].dropna().astype(str).str.upper()) if "symbol" in frame.columns else set()
    selected_symbols = set(frame.loc[frame["selected_for_portfolio"].eq(1), "symbol"].dropna().astype(str).str.upper()) if "symbol" in frame.columns else set()
    missing_symbols = sorted(expected_set - evaluated_symbols)
    if missing_symbols:
        missing = pd.DataFrame(
            [
                {
                    "candidate_status": "DATA_BLOCKED_MISSING_SOURCE",
                    "symbol_status": "MISSING_SOURCE",
                    "symbol": symbol,
                    "data_fresh": 0,
                    "entry_allowed": 0,
                    "selected_for_portfolio": 0,
                    "reason": "MISSING_SOURCE",
                    "source_type": "",
                    "freshness_age_sec": None,
                    "score": -999.0,
                }
                for symbol in missing_symbols
            ]
        )
        frame = pd.concat([frame, missing], ignore_index=True, sort=False)
    evaluated_count = len(evaluated_symbols)
    fresh_count = len(fresh_symbols)
    selected_count = len(selected_symbols)
    missing_or_stale = len((expected_set - fresh_symbols) | (expected_set - evaluated_symbols))
    coverage = _coverage_status(expected_count=expected_count, evaluated_count=evaluated_count, fresh_count=fresh_count)
    frame["universe_scope"] = universe_scope
    frame["expected_universe_count"] = expected_count
    frame["evaluated_symbol_count"] = evaluated_count
    frame["fresh_symbol_count"] = fresh_count
    frame["selected_symbol_count"] = selected_count
    frame["missing_or_stale_symbol_count"] = int(missing_or_stale)
    frame["coverage_status"] = coverage
    cols = [
        col
        for col in [
            "candidate_status",
            "symbol_status",
            "universe_scope",
            "expected_universe_count",
            "evaluated_symbol_count",
            "fresh_symbol_count",
            "selected_symbol_count",
            "missing_or_stale_symbol_count",
            "coverage_status",
            "snapshot_id",
            "created_at",
            "symbol",
            "bar_end_ts",
            "close",
            "data_fresh",
            "entry_allowed",
            "selected_for_portfolio",
            "side",
            "reason",
            "score",
            "source_price_ts",
            "source_price",
            "source_type",
            "freshness_age_sec",
            "stale_reason",
        ]
        if col in frame.columns
    ]
    status_order = {
        "PAPER_ORDER_CANDIDATE": 0,
        "NO_TRADE": 1,
        "NO_TRADE_STALE_DATA": 2,
        "DATA_BLOCKED_MISSING_SOURCE": 3,
        "DATA_BLOCKED_NO_SNAPSHOT": 4,
    }
    frame["_candidate_status_order"] = frame["candidate_status"].map(status_order).fillna(9)
    cols_with_sort = ["_candidate_status_order"] + cols
    return (
        frame[cols_with_sort]
        .sort_values(["_candidate_status_order", "score"], ascending=[True, False])
        .drop(columns=["_candidate_status_order"])
        .head(200)
    )


def _source_inventory(candidates: pd.DataFrame, *, expected_symbols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    candidate_by_symbol = (
        {
            str(row.get("symbol") or "").upper(): row
            for _, row in candidates.iterrows()
            if str(row.get("symbol") or "").strip()
        }
        if not candidates.empty
        else {}
    )
    for symbol in expected_symbols:
        row = candidate_by_symbol.get(symbol, {})
        source_type = str(row.get("source_type") or "")
        symbol_status = str(row.get("symbol_status") or "MISSING_SOURCE")
        stale_reason = str(row.get("stale_reason") or "")
        raw_intraday_path = RAW_INTRADAY_ROOT / f"{symbol}.csv"
        raw_daily_path = RAW_DAILY_ROOT / f"{symbol}.csv"
        if source_type == "KIS_CURRENT_PRICE_APPENDED":
            provider_reason = "LIVE_QUOTE_ATTACHED"
        elif source_type == "RAW_INTRADAY_HISTORY":
            provider_reason = "RAW_INTRADAY_HISTORY_ATTACHED_STALE_FOR_LIVE"
        elif raw_intraday_path.exists():
            provider_reason = "RAW_INTRADAY_AVAILABLE"
        elif raw_daily_path.exists():
            provider_reason = "RAW_DAILY_AVAILABLE"
        else:
            provider_reason = "NO_LOCAL_SOURCE_FILE"
        rows.append(
            {
                "symbol": symbol,
                "symbol_status": symbol_status,
                "source_type": source_type or "MISSING_SOURCE",
                "data_fresh": row.get("data_fresh", 0),
                "entry_allowed": row.get("entry_allowed", 0),
                "selected_for_portfolio": row.get("selected_for_portfolio", 0),
                "source_price_ts": row.get("source_price_ts", ""),
                "freshness_age_sec": row.get("freshness_age_sec", ""),
                "stale_reason": stale_reason,
                "raw_intraday_exists_flag": int(raw_intraday_path.exists()),
                "raw_daily_exists_flag": int(raw_daily_path.exists()),
                "provider_reason": provider_reason,
            }
        )
    return pd.DataFrame(rows)


def _stale_source_closure_scoreboard(source_inventory: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "priority",
        "owner",
        "symbol",
        "symbol_status",
        "data_fresh",
        "source_type",
        "stale_reason",
        "provider_reason",
        "raw_intraday_exists_flag",
        "raw_daily_exists_flag",
        "unblock_condition",
        "next_action",
        "status",
    ]
    if source_inventory.empty:
        return pd.DataFrame(columns=columns)
    frame = source_inventory.copy()
    frame["data_fresh"] = pd.to_numeric(frame.get("data_fresh", 0), errors="coerce").fillna(0).astype(int)
    blocked = frame.loc[
        frame["data_fresh"].eq(0)
        | frame.get("symbol_status", pd.Series("", index=frame.index)).astype(str).isin(["STALE_SOURCE", "MISSING_SOURCE"])
    ].copy()
    if blocked.empty:
        return pd.DataFrame(columns=columns)
    blocked["priority"] = blocked["symbol_status"].astype(str).map({"MISSING_SOURCE": "P0", "STALE_SOURCE": "P1"}).fillna("P1")
    blocked["owner"] = "윤헌"
    blocked["unblock_condition"] = blocked.apply(
        lambda row: (
            "Attach live/runtime source row with current source_price_ts; do not infer from daily or stale intraday history."
            if str(row.get("symbol_status") or "") == "STALE_SOURCE"
            else "Add provider-backed raw/live source proof before candidate evaluation; missing source is blocker, not negative label."
        ),
        axis=1,
    )
    blocked["next_action"] = blocked.apply(
        lambda row: (
            "Refresh Task089 runtime source for symbol and rerun Task583 before Task589 EOD."
            if str(row.get("provider_reason") or "") != "NO_LOCAL_SOURCE_FILE"
            else "Create explicit source acquisition ticket with provider/path and rerun freshness audit after capture."
        ),
        axis=1,
    )
    blocked["status"] = "OPEN_SOURCE_BLOCKER"
    order = {"P0": 0, "P1": 1}
    blocked["_priority_order"] = blocked["priority"].map(order).fillna(9)
    return (
        blocked[[col for col in columns if col in blocked.columns] + ["_priority_order"]]
        .sort_values(["_priority_order", "symbol"])
        .drop(columns=["_priority_order"])
        .reset_index(drop=True)
    )


def run_task583(*, db_path: Path, env_file: Path, symbols: str = "") -> dict[str, pd.DataFrame]:
    load_runtime_env(env_file)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    expected_symbols, universe_scope, symbols_csv = _resolve_universe(symbols)
    stdout, stderr, returncode = _run_task089(db_path, env_file, symbols=symbols_csv)
    snapshot = _latest_indicator_snapshot_per_symbol(db_path, expected_symbols)
    freshness = _freshness_audit(snapshot, expected_symbols=expected_symbols, universe_scope=universe_scope)
    candidates = _runtime_candidates(snapshot, expected_symbols=expected_symbols, universe_scope=universe_scope)
    source_inventory = _source_inventory(candidates, expected_symbols=expected_symbols)
    stale_source_scoreboard = _stale_source_closure_scoreboard(source_inventory)
    fresh_rows = int(freshness.iloc[0]["fresh_rows"]) if not freshness.empty else 0
    candidate_rows = int(candidates["candidate_status"].eq("PAPER_ORDER_CANDIDATE").sum()) if not candidates.empty else 0
    coverage_status = str(freshness.iloc[0].get("coverage_status", "")) if not freshness.empty else "UNIVERSE_COVERAGE_GAP"
    if returncode != 0:
        status = "DATA_BLOCKED_REFRESH_FAILED"
    elif snapshot.empty:
        status = "DATA_BLOCKED_NO_INDICATOR_SNAPSHOT"
    elif fresh_rows <= 0:
        status = "DATA_BLOCKED_STALE_SIGNAL"
    else:
        status = "LIVE_SIGNAL_REFRESH_REPAIRED"
    live_audit = pd.DataFrame(
        [
            {
                "task_id": "Task583",
                "audit_ts_utc": utc_now(),
                "db_path": str(db_path),
                "env_file": str(env_file),
                "task089_returncode": returncode,
                "task089_stdout_tail": stdout,
                "task089_stderr_tail": stderr,
                "universe_scope": universe_scope,
                "expected_universe_count": int(freshness.iloc[0].get("expected_universe_count", len(expected_symbols))),
                "evaluated_symbol_count": int(freshness.iloc[0].get("evaluated_symbol_count", 0)),
                "fresh_symbol_count": int(freshness.iloc[0].get("fresh_symbol_count", 0)),
                "selected_symbol_count": int(freshness.iloc[0].get("selected_symbol_count", 0)),
                "missing_or_stale_symbol_count": int(freshness.iloc[0].get("missing_or_stale_symbol_count", len(expected_symbols))),
                "coverage_status": coverage_status,
                "fresh_rows": fresh_rows,
                "paper_order_candidate_rows": candidate_rows,
                "dummy_fallback_used_flag": 0,
                "data_fresh_manual_override_flag": 0,
            }
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task583",
                "task_name": "Live Signal Refresh Repair",
                "decision_status": status,
                "universe_scope": universe_scope,
                "expected_universe_count": int(freshness.iloc[0].get("expected_universe_count", len(expected_symbols))),
                "evaluated_symbol_count": int(freshness.iloc[0].get("evaluated_symbol_count", 0)),
                "fresh_symbol_count": int(freshness.iloc[0].get("fresh_symbol_count", 0)),
                "selected_symbol_count": int(freshness.iloc[0].get("selected_symbol_count", 0)),
                "missing_or_stale_symbol_count": int(freshness.iloc[0].get("missing_or_stale_symbol_count", len(expected_symbols))),
                "coverage_status": coverage_status,
                "fresh_rows": fresh_rows,
                "paper_order_candidate_rows": candidate_rows,
                "stale_rows": int(len(snapshot) - fresh_rows) if not snapshot.empty else 0,
                "strategy_acceptance_status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "diagnostic_only_flag": 1,
                "deployment_ready_flag": 0,
            }
        ]
    )
    artifacts = {
        "task_583_decision.csv": decision,
        "live_signal_refresh_audit.csv": live_audit,
        "indicator_snapshot_freshness_audit.csv": freshness,
        "runtime_candidate_audit.csv": candidates,
        "runtime_source_inventory_audit.csv": source_inventory,
        "runtime_stale_source_closure_scoreboard.csv": stale_source_scoreboard,
    }
    for name, frame in artifacts.items():
        write_csv(REPORT_DIR, name, frame)
    write_task_report(
        REPORT_DIR,
        "task_583_live_signal_refresh_repair.md",
        title="Task583 - Live Signal Refresh Repair",
        decision_summary=[
            f"decision_status={status}",
            f"universe_scope={universe_scope}",
            f"universe_coverage={coverage_status}",
            f"evaluated_symbol_count={freshness.iloc[0].get('evaluated_symbol_count', 0)}/{freshness.iloc[0].get('expected_universe_count', len(expected_symbols))}",
            f"fresh_rows={fresh_rows}",
            f"paper_order_candidate_rows={candidate_rows}",
            "stale data cannot produce paper order candidates.",
        ],
        quant_lines=[
            "Task089 now feeds KIS runtime price/tick data into the decision snapshot path instead of relying only on stale daily bars.",
            "The audit separates fresh runtime rows from stale rows and records source timestamp, source price, source type, freshness age, and stale reason.",
            "The source inventory identifies KIS current quote, raw intraday history, daily history, and missing local source status per expected theme_10x7 symbol.",
            "The stale source closure scoreboard names blocked symbols, owner, unblock condition, and next action without approximating missing sources.",
            "No data_fresh manual override or dummy fallback was used.",
        ],
        decision_maker_lines=[
            "이번 단계는 주문 전 신호가 최신인지 확인하는 단계입니다.",
            "데이터가 오래되면 주문 후보가 만들어지지 않으며, 그 이유가 artifact와 프론트엔드에 남습니다.",
            "fresh 신호가 생겨야 다음 Task584/585에서 주문 판단과 모의 주문이 가능합니다.",
        ],
    )
    append_registry_rows(
        [
            {
                "task_id": "Task583",
                "title": "Live Signal Refresh Repair",
                "owner_team": "Data & Market Microstructure",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "not-applicable",
                "data_readiness": "runtime-source",
                "parent_task": "Task582",
                "key_report": str(REPORT_DIR / "task_583_live_signal_refresh_repair.md"),
                "key_decision": str(REPORT_DIR / "task_583_decision.csv"),
                "key_artifacts": str(REPORT_DIR),
                "validation_command": "python -m unittest tests.test_task583_live_signal_refresh_repair",
                "notes": "Refreshes indicator snapshots from runtime KIS quote/bar source without stale override.",
            }
        ]
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--env-file", type=Path, default=Path("config/kis_paper.env"))
    parser.add_argument("--symbols", type=str, default="")
    args = parser.parse_args()
    artifacts = run_task583(db_path=args.db_path, env_file=args.env_file, symbols=args.symbols)
    print(artifacts["task_583_decision.csv"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
