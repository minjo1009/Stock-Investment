from __future__ import annotations

import inspect
import os
from pathlib import Path
from typing import Mapping

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report
from src.data.alpaca_stock_stream_archive import DEFAULT_CHANNELS, StreamArchiveConfig
from src.data.env_loader import load_repo_env
from src.data.paper_shadow_microstructure_capture import build_latest_microstructure_state, load_stream_archive_records


TASK571_REPORT = Path("docs/reports/task_571_alpaca_sip_microstructure_capture_activation")
STREAM_ARCHIVE_DIR = Path("data/raw/alpaca_stock_stream_archive")


def _decision(task_id: str, status: str, **extra: object) -> pd.DataFrame:
    return pd.DataFrame([{"task_id": task_id, "strategy_acceptance_status": status, "deployment_ready_flag": 0, **extra}])


def _credential_audit(env: Mapping[str, str] | None = None) -> pd.DataFrame:
    source = env if env is not None else os.environ
    key_present = bool(source.get("APCA_API_KEY_ID") or source.get("ALPACA_API_KEY"))
    secret_present = bool(source.get("APCA_API_SECRET_KEY") or source.get("ALPACA_SECRET_KEY"))
    return pd.DataFrame(
        [
            {
                "credential_name": "APCA_API_KEY_ID or ALPACA_API_KEY",
                "present_flag": int(key_present),
                "secret_value_logged_flag": 0,
            },
            {
                "credential_name": "APCA_API_SECRET_KEY or ALPACA_SECRET_KEY",
                "present_flag": int(secret_present),
                "secret_value_logged_flag": 0,
            },
        ]
    )


def _stream_client_audit() -> pd.DataFrame:
    try:
        import websockets

        connect_params = inspect.signature(websockets.connect).parameters
        header_argument = "additional_headers" if "additional_headers" in connect_params else "extra_headers"
        version = getattr(websockets, "__version__", "unknown")
        available = 1
        error = ""
    except Exception as exc:  # pragma: no cover - environment dependent
        header_argument = ""
        version = ""
        available = 0
        error = f"{type(exc).__name__}: {exc}"
    return pd.DataFrame(
        [
            {
                "client_component": "websockets",
                "available_flag": available,
                "version": version,
                "header_argument": header_argument,
                "compatibility_status": "PASS" if available and header_argument else "FAIL",
                "error": error,
            },
            {
                "client_component": "alpaca_stock_stream_archive",
                "available_flag": 1,
                "version": "repo_local",
                "header_argument": header_argument,
                "compatibility_status": "PASS" if available and header_argument else "FAIL",
                "error": "",
            },
        ]
    )


def _feed_scope_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "feed": "sip",
                "firm_grade_role": "required_for_full_nbbo_scope",
                "current_status": "requires_credentials_and_feed_entitlement_probe",
                "scope_limited_flag": 0,
                "deployment_grade_flag": 0,
            },
            {
                "feed": "iex",
                "firm_grade_role": "paper_shadow_diagnostic_only",
                "current_status": "scope_limited_possible_not_full_nbbo",
                "scope_limited_flag": 1,
                "deployment_grade_flag": 0,
            },
        ]
    )


def _command_contract(symbols: str = "AAPL,NVDA,AMD,MSFT,GOOGL,PLTR,AFRM") -> pd.DataFrame:
    base = "python -m src.data.alpaca_stock_stream_archive"
    return pd.DataFrame(
        [
            {
                "run_mode": "firm_grade_sip_market_hours",
                "command": f"{base} --symbols {symbols} --feed sip --channels quotes,bars,updatedBars,statuses,lulds --duration-seconds 1800",
                "required_env": "APCA_API_KEY_ID,APCA_API_SECRET_KEY",
                "expected_output": "data/raw/alpaca_stock_stream_archive/trade_date=*/channel=*/SYMBOL.jsonl",
                "secret_in_command_flag": 0,
            },
            {
                "run_mode": "scope_limited_iex_smoke",
                "command": f"{base} --symbols {symbols} --feed iex --channels quotes,bars,updatedBars,statuses,lulds --duration-seconds 300",
                "required_env": "APCA_API_KEY_ID,APCA_API_SECRET_KEY",
                "expected_output": "data/raw/alpaca_stock_stream_archive/trade_date=*/channel=*/SYMBOL.jsonl",
                "secret_in_command_flag": 0,
            },
            {
                "run_mode": "post_capture_snapshot_rebuild",
                "command": "python -m src.backtest.analysis_structural_breakout_task547_paper_shadow_microstructure_capture_run",
                "required_env": "none",
                "expected_output": "docs/reports/task_547_paper_shadow_microstructure_capture_run/decision_microstructure_snapshot_log.csv",
                "secret_in_command_flag": 0,
            },
        ]
    )


def _archive_audit(stream_archive_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = load_stream_archive_records(stream_archive_dir)
    state = build_latest_microstructure_state(records)
    channels = records["channel"].value_counts().to_dict() if not records.empty else {}
    errors = _stream_error_summary(records)
    audit = pd.DataFrame(
        [
            {
                "archive_path": str(stream_archive_dir),
                "raw_stream_record_count": int(len(records)),
                "success_record_count": int(channels.get("success", 0)),
                "subscription_record_count": int(channels.get("subscription", 0)),
                "error_record_count": int(channels.get("error", 0)),
                "connection_limit_error_count": int(errors.get("connection limit exceeded", 0)),
                "not_authenticated_error_count": int(errors.get("not authenticated", 0)),
                "insufficient_subscription_error_count": int(errors.get("insufficient subscription", 0)),
                "quote_record_count": int(channels.get("quotes", 0)),
                "bar_record_count": int(channels.get("bars", 0) + channels.get("updatedBars", 0)),
                "status_record_count": int(channels.get("statuses", 0)),
                "luld_record_count": int(channels.get("lulds", 0)),
                "state_symbol_count": int(state["symbol"].nunique()) if not state.empty else 0,
                "historical_ohlcv_used_as_microstructure_flag": 0,
                "missing_source_approximated_flag": 0,
            }
        ]
    )
    return audit, state


def _stream_error_summary(records: pd.DataFrame) -> dict[str, int]:
    if records.empty or "raw_message_json" not in records.columns:
        return {}
    out: dict[str, int] = {}
    error_rows = records[records.get("channel", pd.Series(dtype=str)).astype(str).eq("error")]
    for raw in error_rows["raw_message_json"].astype(str):
        for key in ["connection limit exceeded", "not authenticated", "insufficient subscription"]:
            if key in raw:
                out[key] = out.get(key, 0) + 1
    return out


def build_task571(
    *,
    stream_archive_dir: Path = STREAM_ARCHIVE_DIR,
    env: Mapping[str, str] | None = None,
) -> dict[str, pd.DataFrame]:
    if env is None:
        load_repo_env()
    credentials = _credential_audit(env)
    client = _stream_client_audit()
    feed = _feed_scope_audit()
    commands = _command_contract()
    archive, state = _archive_audit(stream_archive_dir)
    credential_ready = int(credentials["present_flag"].min()) if not credentials.empty else 0
    client_ready = int(client["compatibility_status"].eq("PASS").all())
    raw_records = int(archive.iloc[0]["raw_stream_record_count"]) if not archive.empty else 0
    quote_records = int(archive.iloc[0]["quote_record_count"]) if not archive.empty else 0
    status_records = int(archive.iloc[0]["status_record_count"]) if not archive.empty else 0
    luld_records = int(archive.iloc[0]["luld_record_count"]) if not archive.empty else 0
    success_records = int(archive.iloc[0]["success_record_count"]) if not archive.empty else 0
    connection_limit_errors = int(archive.iloc[0]["connection_limit_error_count"]) if not archive.empty else 0
    insufficient_subscription_errors = int(archive.iloc[0]["insufficient_subscription_error_count"]) if not archive.empty else 0
    if not credential_ready:
        status = "DATA_BLOCKED_CREDENTIAL_ENV_MISSING"
    elif not client_ready:
        status = "DATA_BLOCKED_STREAM_CLIENT_INCOMPATIBLE"
    elif connection_limit_errors > 0:
        status = "DATA_BLOCKED_ALPACA_CONNECTION_LIMIT"
    elif insufficient_subscription_errors > 0:
        status = "DATA_BLOCKED_FEED_OR_CHANNEL_ENTITLEMENT"
    elif raw_records == 0:
        status = "READY_FOR_MARKET_HOURS_CAPTURE_NO_ROWS_YET"
    elif quote_records > 0 and status_records > 0 and luld_records > 0:
        status = "PAPER_SHADOW_CAPTURE_ROWS_AVAILABLE_REBUILD_TASK547"
    else:
        status = "PARTIAL_CAPTURE_ROWS_MISSING_STATUS_OR_LULD"
    readiness = pd.DataFrame(
        [
            {
                "readiness_check": "credentials_present",
                "pass_flag": credential_ready,
                "blocking_status": "PASS" if credential_ready else "DATA_BLOCKED",
            },
            {
                "readiness_check": "stream_client_compatible",
                "pass_flag": client_ready,
                "blocking_status": "PASS" if client_ready else "DATA_BLOCKED",
            },
            {
                "readiness_check": "stream_archive_has_records",
                "pass_flag": int(raw_records > 0),
                "blocking_status": "PASS" if raw_records > 0 else "PENDING_MARKET_HOURS_RUN",
            },
            {
                "readiness_check": "auth_success_observed",
                "pass_flag": int(success_records > 0),
                "blocking_status": "PASS" if success_records > 0 else "DATA_BLOCKED_AUTH_NOT_OBSERVED",
            },
            {
                "readiness_check": "no_connection_limit_error",
                "pass_flag": int(connection_limit_errors == 0),
                "blocking_status": "PASS" if connection_limit_errors == 0 else "DATA_BLOCKED_CONNECTION_LIMIT",
            },
            {
                "readiness_check": "no_feed_entitlement_error",
                "pass_flag": int(insufficient_subscription_errors == 0),
                "blocking_status": "PASS" if insufficient_subscription_errors == 0 else "DATA_BLOCKED_FEED_OR_CHANNEL_ENTITLEMENT",
            },
            {
                "readiness_check": "quote_status_luld_complete",
                "pass_flag": int(quote_records > 0 and status_records > 0 and luld_records > 0),
                "blocking_status": "PASS" if quote_records > 0 and status_records > 0 and luld_records > 0 else "PENDING_CAPTURE_COMPLETION",
            },
        ]
    )
    decision = _decision(
        "Task571",
        status,
        credential_ready_flag=credential_ready,
        stream_client_ready_flag=client_ready,
        raw_stream_record_count=raw_records,
        success_record_count=success_records,
        connection_limit_error_count=connection_limit_errors,
        insufficient_subscription_error_count=insufficient_subscription_errors,
        quote_record_count=quote_records,
        status_record_count=status_records,
        luld_record_count=luld_records,
        missing_source_approximated_flag=0,
    )
    return {
        "alpaca_credential_env_audit": credentials,
        "alpaca_stream_client_audit": client,
        "alpaca_feed_scope_audit": feed,
        "alpaca_capture_command_contract": commands,
        "alpaca_stream_archive_audit": archive,
        "latest_microstructure_state_preview": state.head(100) if not state.empty else state,
        "alpaca_capture_readiness_gate": readiness,
        "task_571_decision": decision,
    }


def _write_frames(out_dir: Path, frames: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    artifacts = build_task571()
    _write_frames(TASK571_REPORT, artifacts)
    decision = artifacts["task_571_decision"].iloc[0].to_dict()
    write_standard_report(
        TASK571_REPORT / "task_571_alpaca_sip_microstructure_capture_activation.md",
        title="Task571 — Alpaca SIP Microstructure Capture Activation",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Credential ready: {decision['credential_ready_flag']}",
            f"Stream client ready: {decision['stream_client_ready_flag']}",
            f"Raw stream records: {decision['raw_stream_record_count']}",
            "Deployment-ready claim: NO",
        ],
        quant_expert_lines=[
            "- The Alpaca stream archiver is the live/paper source for NBBO quote, bar/updatedBar, status, and LULD records with local receive timestamps.",
            "- SIP is the firm-grade target feed; IEX can only be used for scope-limited paper/shadow diagnostics.",
            "- Secrets are not written to artifacts. Credentials must be supplied through environment variables.",
            "- Historical OHLCV is not used as microstructure and missing sources are not approximated.",
        ],
        decision_maker_lines=[
            "- 실시간 호가/상태 데이터를 받는 수집기는 준비됐지만, 현재 환경변수/시장시간/권한 조건이 충족돼야 실제 row가 쌓입니다.",
            "- SIP feed가 막히면 IEX는 제한적 진단용일 뿐 firm-grade NBBO 검증은 아닙니다.",
            "- 장중 수집 후 Task547을 다시 돌리면 microstructure-ready 여부가 판정됩니다.",
        ],
    )
    write_manifest(TASK571_REPORT, TASK571_REPORT / "artifact_manifest.csv")
    print(f"[TASK571_OK] report={TASK571_REPORT}")


if __name__ == "__main__":
    main()
