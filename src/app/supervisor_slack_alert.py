from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from .paper_runtime_common import load_runtime_env, utc_now, write_csv
try:
    from src.integration import slack_client
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from integration import slack_client


REPORT_DIR = Path("docs/reports/task_589_nasdaq_paper_ops_hardening")


def _secret_free(text: str) -> bool:
    needles = [
        os.environ.get("KIS_APP_KEY", ""),
        os.environ.get("KIS_APP_SECRET", ""),
        os.environ.get("KIS_ACCOUNT_NUMBER", ""),
        os.environ.get("SLACK_WEBHOOK_URL", ""),
    ]
    return not any(value and value in text for value in needles)


def send_supervisor_alert(
    *,
    component: str,
    status: str,
    detail: str,
    env_file: Path,
    message_type: str = "SUPERVISOR_FAILURE",
) -> pd.DataFrame:
    load_runtime_env(env_file)
    text = f"[{message_type}]\ncomponent: {component}\nstatus: {status}\ndetail: {detail}"
    webhook_present = bool(os.environ.get("SLACK_WEBHOOK_URL", "").strip())
    secret_free = _secret_free(text)
    error = ""
    if not webhook_present:
        send_status = "SLACK_BLOCKED_MISSING_WEBHOOK"
    elif not secret_free:
        send_status = "SLACK_BLOCKED_SECRET_IN_MESSAGE"
    else:
        try:
            slack_client.send_message(text)
            send_status = "SENT"
        except Exception as exc:  # pragma: no cover - external Slack availability.
            send_status = "FAILED"
            error = str(exc)
    audit = pd.DataFrame(
        [
            {
                "created_at_utc": utc_now(),
                "component": component,
                "message_type": message_type,
                "status": status,
                "detail": detail,
                "slack_send_status": send_status,
                "webhook_present_flag": int(webhook_present),
                "secret_in_message_flag": int(not secret_free),
                "error": error,
            }
        ]
    )
    write_csv(REPORT_DIR, "supervisor_failure_alert_audit.csv", audit)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--detail", required=True)
    parser.add_argument("--env-file", type=Path, default=Path("config/kis_paper.env"))
    parser.add_argument("--message-type", default="SUPERVISOR_FAILURE")
    args = parser.parse_args()
    audit = send_supervisor_alert(
        component=args.component,
        status=args.status,
        detail=args.detail,
        env_file=args.env_file,
        message_type=args.message_type,
    )
    print(audit.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
