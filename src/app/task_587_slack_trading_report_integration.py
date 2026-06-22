from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from .paper_runtime_common import (
    append_registry_rows,
    load_runtime_env,
    utc_now,
    write_csv,
    write_task_report,
)
try:
    from src.integration import slack_client
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from integration import slack_client


REPORT_DIR = Path("docs/reports/task_587_slack_trading_report_integration")


def _read_latest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    if frame.empty:
        return {}
    return frame.iloc[0].where(pd.notnull(frame.iloc[0]), None).to_dict()


def _is_filled_trade(task585: dict[str, object]) -> bool:
    status = str(task585.get("order_status") or "").upper()
    broker_truth = str(task585.get("broker_truth_fill_flag") or "0") in {"1", "1.0", "True", "true"}
    try:
        filled_qty = float(task585.get("filled_qty") or task585.get("quantity") or 0)
    except Exception:
        filled_qty = 0.0
    return status == "FILLED" and broker_truth and filled_qty > 0


def _build_message(task584: dict[str, object], task585: dict[str, object]) -> tuple[str, str]:
    status = str(task585.get("order_status") or "")
    decision_status = str(task584.get("decision_status") or "")
    symbol = str(task584.get("symbol") or task585.get("symbol") or "-")
    side = str(task584.get("side") or task585.get("side") or "-")
    qty = str(task584.get("quantity") or task585.get("quantity") or "0")
    price = str(task584.get("limit_price") or task585.get("limit_price") or "-")
    reason = str(task584.get("reason_code") or task585.get("reason_code") or "-")
    data_fresh = str(task584.get("data_fresh") or "0")
    lifecycle_id = str(task585.get("lifecycle_id") or "-")
    order_id = str(task585.get("order_id") or "-")
    if not _is_filled_trade(task585):
        message_type = "SKIPPED_NO_FILLED_TRADE"
        text = (
            f"[{message_type}]\n"
            "reason: Slack trade reports are sent only for broker-truth filled paper trades.\n"
            f"decision_status: {decision_status or 'NO_DECISION'}\n"
            f"order_status: {status or 'NO_ORDER'}\n"
            f"order_id: {order_id}"
        )
        return message_type, text
    message_type = "FILLED_TRADE_REPORT"
    text = (
        f"[{message_type}]\n"
        f"symbol: {symbol}\n"
        f"side: {side}\n"
        f"quantity: {qty}\n"
        f"price: {price}\n"
        f"decision_status: {decision_status}\n"
        f"decision_reason: {reason}\n"
        f"data_fresh: {data_fresh}\n"
        f"order_status: {status or 'NO_ORDER'}\n"
        f"order_id: {order_id}\n"
        f"lifecycle_id: {lifecycle_id}\n"
        "frontend: React Trader Terminal > 모의거래"
    )
    return message_type, text


def _secret_free(text: str) -> bool:
    needles = [
        os.environ.get("KIS_APP_KEY", ""),
        os.environ.get("KIS_APP_SECRET", ""),
        os.environ.get("KIS_ACCOUNT_NUMBER", ""),
        os.environ.get("SLACK_WEBHOOK_URL", ""),
    ]
    return not any(value and value in text for value in needles)


def run_task587(*, env_file: Path = Path("config/kis_paper.env")) -> dict[str, pd.DataFrame]:
    load_runtime_env(env_file)
    task584 = _read_latest(Path("docs/reports/task_584_runtime_strategy_decision_gate/runtime_strategy_decision_log.csv"))
    task585 = _read_latest(Path("docs/reports/task_585_kis_paper_order_execution/paper_order_execution_log.csv"))
    message_type, text = _build_message(task584, task585)
    webhook_present = bool(os.environ.get("SLACK_WEBHOOK_URL", "").strip())
    secret_free = int(_secret_free(text))
    if message_type == "SKIPPED_NO_FILLED_TRADE":
        status = "SKIPPED_NO_FILLED_TRADE"
        error = ""
    elif not webhook_present:
        status = "SLACK_BLOCKED_MISSING_WEBHOOK"
        error = ""
    elif not secret_free:
        status = "SLACK_BLOCKED_SECRET_IN_MESSAGE"
        error = ""
    else:
        try:
            slack_client.send_message(text)
            status = "SENT"
            error = ""
        except Exception as exc:  # pragma: no cover - external Slack availability.
            status = "FAILED"
            error = str(exc)
    audit = pd.DataFrame(
        [
            {
                "task_id": "Task587",
                "created_at_utc": utc_now(),
                "message_type": message_type,
                "slack_send_status": status,
                "webhook_present_flag": int(webhook_present),
                "secret_in_message_flag": int(not secret_free),
                "error": error,
            }
        ]
    )
    payload = pd.DataFrame(
        [
            {
                "message_type": message_type,
                "message_text": text,
                "secret_logged_flag": 0,
            }
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task587",
                "task_name": "Slack Trading Report Integration",
                "decision_status": status,
                "message_type": message_type,
                "deployment_ready_flag": 0,
                "diagnostic_only_flag": 1,
            }
        ]
    )
    artifacts = {
        "slack_trading_notification_audit.csv": audit,
        "slack_message_payload_sample.csv": payload,
        "task_587_decision.csv": decision,
    }
    for name, frame in artifacts.items():
        write_csv(REPORT_DIR, name, frame)
    write_task_report(
        REPORT_DIR,
        "task_587_slack_trading_report_integration.md",
        title="Task587 - Slack Trading Report Integration",
        decision_summary=[
            f"decision_status={status}",
            f"message_type={message_type}",
            "Secrets are never included in Slack payloads.",
        ],
        quant_lines=[
            "Slack messages are downstream reports of Task584/585 state and do not alter trading decisions.",
            "Trade Slack reports are sent only for broker-truth filled paper trades.",
            "No-trade, submitted, pending, rejected, cancelled, timeout, and failed states are audited but not sent as trade reports.",
            "Missing webhook is a blocker, not a successful send.",
        ],
        decision_maker_lines=[
            "이번 단계는 모의거래 판단과 주문 상태를 Slack으로 보내는 연결입니다.",
            "Webhook이 없으면 전송 성공처럼 표시하지 않고 blocked로 남깁니다.",
            "거래가 없어도 왜 거래하지 않았는지 Slack 보고용 메시지를 만들 수 있습니다.",
        ],
    )
    append_registry_rows(
        [
            {
                "task_id": "Task587",
                "title": "Slack Trading Report Integration",
                "owner_team": "Execution & Risk",
                "status": "Accepted",
                "canonical_state": "active",
                "strategy_acceptance": "diagnostic-only",
                "data_readiness": "runtime-source",
                "parent_task": "Task585",
                "key_report": str(REPORT_DIR / "task_587_slack_trading_report_integration.md"),
                "key_decision": str(REPORT_DIR / "task_587_decision.csv"),
                "key_artifacts": str(REPORT_DIR),
                "validation_command": "python -m unittest tests.test_task587_slack_trading_report_integration",
                "notes": "Sends Slack trade reports only for broker-truth filled paper trades; unfilled states are audited but not sent.",
            }
        ]
    )
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=Path("config/kis_paper.env"))
    args = parser.parse_args()
    artifacts = run_task587(env_file=args.env_file)
    print(artifacts["task_587_decision.csv"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
