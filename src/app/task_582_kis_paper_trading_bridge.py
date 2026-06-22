from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report
from src.data.env_loader import load_repo_env
from src.integration import slack_client
from src.state.store import initialize_store


REPORT_DIR = Path("docs/reports/task_582_kis_paper_trading_bridge")
DEFAULT_DB_PATH = Path("trading.db")
DEFAULT_KIS_ENV_FILE = Path("config/kis_paper.env")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load_env_file(path: Path) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and not os.environ.get(key):
            os.environ[key] = value
        if key:
            loaded[key] = value
    return loaded


def _env_presence(keys: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "env_key": key,
                "present_flag": int(bool(os.environ.get(key, "").strip())),
                "value_logged_flag": 0,
            }
            for key in keys
        ]
    )


def _table_rows(db_path: Path, table: str, limit: int = 25) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table,),
        ).fetchone()
        if not exists:
            return []
        rows = con.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def _latest_runtime_snapshot(db_path: Path) -> tuple[bool, dict[str, Any] | None]:
    rows = _table_rows(db_path, "indicator_snapshots", limit=200)
    if not rows:
        return False, None
    latest_created = max(str(row.get("created_at") or "") for row in rows)
    candidates = [
        row
        for row in rows
        if str(row.get("created_at") or "") == latest_created
        and int(row.get("entry_allowed") or 0) == 1
        and int(row.get("data_fresh") or 0) == 1
        and int(row.get("selected_for_portfolio") or 0) == 1
    ]
    if not candidates:
        candidates = [
            row
            for row in rows
            if str(row.get("created_at") or "") == latest_created
            and int(row.get("entry_allowed") or 0) == 1
            and int(row.get("data_fresh") or 0) == 1
        ]
    candidates.sort(key=lambda row: (float(row.get("score") or 0.0), str(row.get("symbol") or "")), reverse=True)
    return True, candidates[0] if candidates else None


def _send_slack(text: str) -> tuple[str, str]:
    if not os.environ.get("SLACK_WEBHOOK_URL", "").strip():
        return "SKIPPED_MISSING_SLACK_WEBHOOK_URL", ""
    try:
        slack_client.send_message(text)
        return "SENT", ""
    except Exception as exc:  # pragma: no cover - depends on external Slack availability.
        return "FAILED", str(exc)


def _write_csv(name: str, frame: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(REPORT_DIR / name, index=False, encoding="utf-8-sig")


def run_task582(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    env_file: Path = DEFAULT_KIS_ENV_FILE,
    test_symbol: str = "AAPL",
    run_paper_order: bool = False,
    send_slack: bool = True,
) -> dict[str, pd.DataFrame]:
    load_repo_env()
    loaded_repo_env = int(Path(".env").exists())
    loaded_kis_env = _load_env_file(env_file)
    os.environ["TRADING_DB_PATH"] = str(db_path)
    os.environ["TRADING_REQUIRE_RUNTIME_SIGNAL"] = "1"
    initialize_store(str(db_path))

    env_keys = [
        "KIS_ENVIRONMENT",
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "KIS_ACCOUNT_NUMBER",
        "KIS_PRODUCT_CODE",
        "SLACK_WEBHOOK_URL",
    ]
    env_audit = _env_presence(env_keys)
    env_name = os.environ.get("KIS_ENVIRONMENT", "paper").strip().lower() or "paper"
    paper_env_flag = int(env_name == "paper")

    connection_rows: list[dict[str, Any]] = []
    quote_price: float | None = None
    kis_status = "NOT_RUN"
    kis_error = ""
    if paper_env_flag and env_audit.loc[env_audit["env_key"].str.startswith("KIS_"), "present_flag"].all():
        try:
            from integration.kis_client import KISClient

            kis = KISClient.from_env()
            auth_state = kis.describe_auth_state()
            quote_price = kis.get_current_price(test_symbol)
            kis_status = "CONNECTED_PRICE_OK"
            connection_rows.append(
                {
                    "check": "kis_paper_auth_and_quote",
                    "status": kis_status,
                    "symbol": test_symbol,
                    "price": quote_price,
                    "token_present": auth_state.get("token_present"),
                    "token_expired": auth_state.get("expired"),
                    "secret_logged_flag": 0,
                }
            )
        except Exception as exc:
            kis_status = "FAILED"
            kis_error = str(exc)
            connection_rows.append(
                {
                    "check": "kis_paper_auth_and_quote",
                    "status": kis_status,
                    "symbol": test_symbol,
                    "price": None,
                    "token_present": None,
                    "token_expired": None,
                    "secret_logged_flag": 0,
                    "error": kis_error,
                }
            )
    else:
        missing = ",".join(env_audit.loc[env_audit["present_flag"].eq(0), "env_key"].tolist())
        kis_status = "SKIPPED_ENV_NOT_READY"
        kis_error = missing
        connection_rows.append(
            {
                "check": "kis_paper_auth_and_quote",
                "status": kis_status,
                "symbol": test_symbol,
                "price": None,
                "secret_logged_flag": 0,
                "error": missing,
            }
        )

    runtime_active, runtime_candidate = _latest_runtime_snapshot(db_path)
    order_run_status = "SKIPPED_BY_DEFAULT"
    order_stdout = ""
    order_stderr = ""
    if run_paper_order:
        if not runtime_active or runtime_candidate is None:
            order_run_status = "SKIPPED_NO_RUNTIME_SIGNAL"
        elif not paper_env_flag:
            order_run_status = "SKIPPED_NOT_PAPER_ENV"
        elif kis_status != "CONNECTED_PRICE_OK":
            order_run_status = "SKIPPED_KIS_NOT_CONNECTED"
        else:
            child_env = {**os.environ, "TRADING_REQUIRE_RUNTIME_SIGNAL": "1"}
            src_path = str(Path("src").resolve())
            child_env["PYTHONPATH"] = src_path + (os.pathsep + child_env["PYTHONPATH"] if child_env.get("PYTHONPATH") else "")
            completed = subprocess.run(
                [sys.executable, "-m", "app.paper_one_shot_080", "--db-path", str(db_path)],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
                env=child_env,
            )
            order_run_status = "PAPER_ORDER_RUN_OK" if completed.returncode == 0 else "PAPER_ORDER_RUN_FAILED"
            order_stdout = completed.stdout[-2000:]
            order_stderr = completed.stderr[-2000:]

    run_rows = _table_rows(db_path, "trade_runs", limit=30)
    order_rows = _table_rows(db_path, "orders", limit=30)
    fill_rows = _table_rows(db_path, "fills", limit=30)
    continuation_rows = _table_rows(db_path, "continuation_events", limit=30)

    run_log = pd.DataFrame(
        [
            {
                "created_at_utc": _utc_now(),
                "db_path": str(db_path),
                "repo_env_file_present_flag": loaded_repo_env,
                "kis_env_file": str(env_file),
                "kis_env_file_loaded_key_count": len(loaded_kis_env),
                "kis_environment": env_name,
                "paper_env_flag": paper_env_flag,
                "kis_connection_status": kis_status,
                "kis_connection_error": kis_error,
                "runtime_indicator_snapshot_active_flag": int(runtime_active),
                "runtime_candidate_available_flag": int(runtime_candidate is not None),
                "runtime_candidate_symbol": "" if runtime_candidate is None else str(runtime_candidate.get("symbol") or ""),
                "paper_order_requested_flag": int(run_paper_order),
                "paper_order_run_status": order_run_status,
                "dummy_fallback_blocked_flag": 1,
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
            }
        ]
    )
    db_counts = pd.DataFrame(
        [
            {"table": "trade_runs", "recent_rows_exported": len(run_rows)},
            {"table": "orders", "recent_rows_exported": len(order_rows)},
            {"table": "fills", "recent_rows_exported": len(fill_rows)},
            {"table": "continuation_events", "recent_rows_exported": len(continuation_rows)},
        ]
    )
    order_lineage = pd.DataFrame(order_rows)
    fill_lineage = pd.DataFrame(fill_rows)
    continuation_log = pd.DataFrame(continuation_rows)
    if order_lineage.empty:
        order_lineage = pd.DataFrame(columns=["order_id", "run_id", "symbol", "side", "status", "created_at"])
    if fill_lineage.empty:
        fill_lineage = pd.DataFrame(columns=["fill_id", "order_id", "run_id", "symbol", "side", "filled_quantity", "fill_price"])
    if continuation_log.empty:
        continuation_log = pd.DataFrame(columns=["event_id", "run_id", "lifecycle_id", "event_type", "symbol", "created_at"])

    slack_text = (
        "[Task582 KIS Paper Bridge]\n"
        f"status: {kis_status}\n"
        f"paper_order: {order_run_status}\n"
        f"runtime_candidate: {run_log.iloc[0]['runtime_candidate_symbol'] or 'NONE'}\n"
        f"dummy_fallback_blocked: YES\n"
        f"frontend: catalog will expose task_582 paper logs"
    )
    slack_status, slack_error = _send_slack(slack_text) if send_slack else ("SKIPPED_BY_ARG", "")
    slack_audit = pd.DataFrame(
        [
            {
                "created_at_utc": _utc_now(),
                "slack_webhook_present_flag": int(bool(os.environ.get("SLACK_WEBHOOK_URL", "").strip())),
                "slack_send_status": slack_status,
                "slack_error": slack_error,
                "message_contains_secret_flag": 0,
            }
        ]
    )

    decision_status = "PAPER_BRIDGE_READY_NO_ORDER" if kis_status == "CONNECTED_PRICE_OK" else "DATA_BLOCKED_KIS_CONNECTION"
    if order_run_status == "PAPER_ORDER_RUN_OK":
        decision_status = "PAPER_ORDER_SUBMITTED_OR_RECORDED"
    elif run_paper_order and order_run_status.startswith("SKIPPED"):
        decision_status = order_run_status
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task582",
                "strategy_acceptance_status": decision_status,
                "kis_connection_status": kis_status,
                "paper_order_run_status": order_run_status,
                "slack_send_status": slack_status,
                "frontend_catalog_ready_flag": 1,
                "dummy_fallback_blocked_flag": 1,
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
            }
        ]
    )

    artifacts = {
        "kis_paper_environment_audit.csv": env_audit,
        "kis_paper_connection_audit.csv": pd.DataFrame(connection_rows),
        "paper_trading_run_log.csv": run_log,
        "paper_trading_db_recent_counts.csv": db_counts,
        "paper_order_lineage_recent.csv": order_lineage,
        "paper_fill_lineage_recent.csv": fill_lineage,
        "paper_continuation_event_recent.csv": continuation_log,
        "paper_slack_notification_audit.csv": slack_audit,
        "task_582_decision.csv": decision,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        _write_csv(name, frame)
    write_standard_report(
        REPORT_DIR / "task_582_kis_paper_trading_bridge.md",
        title="Task 582 - KIS Paper Trading Bridge",
        decision_summary=[f"{k}: {v}" for k, v in decision.iloc[0].to_dict().items()],
        quant_expert_lines=[
            "KIS paper connectivity is audited separately from order submission.",
            "TRADING_REQUIRE_RUNTIME_SIGNAL=1 blocks the legacy dummy AAPL fallback path.",
            "Decision/order/fill/lifecycle lineage is exported from the trading DB for frontend catalog ingestion.",
        ],
        decision_maker_lines=[
            "한국투자 모의계좌 연결 상태와 주문 로그를 프론트엔드에 표시할 수 있게 만들었다.",
            "실제 신호가 없으면 더미 주문을 내지 않도록 막았다.",
            "Slack에는 연결/주문 상태와 다음 확인 포인트만 전송한다.",
        ],
    )
    if order_stdout or order_stderr:
        (REPORT_DIR / "paper_order_run_stdout.txt").write_text(order_stdout, encoding="utf-8")
        (REPORT_DIR / "paper_order_run_stderr.txt").write_text(order_stderr, encoding="utf-8")
    write_manifest(REPORT_DIR, REPORT_DIR / "artifact_manifest.csv")
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Task582 KIS paper trading bridge")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_KIS_ENV_FILE)
    parser.add_argument("--test-symbol", type=str, default=os.environ.get("PAPER_TEST_SYMBOL", "AAPL"))
    parser.add_argument("--run-paper-order", action="store_true")
    parser.add_argument("--no-slack", action="store_true")
    args = parser.parse_args()
    run_task582(
        db_path=args.db_path,
        env_file=args.env_file,
        test_symbol=args.test_symbol.upper(),
        run_paper_order=args.run_paper_order,
        send_slack=not args.no_slack,
    )


if __name__ == "__main__":
    main()
