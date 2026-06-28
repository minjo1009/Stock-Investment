from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from src.data.env_loader import load_repo_env
from tools.db.source_acquisition.secret_redaction import redact_text


DEFAULT_RAW_DIR = Path("data/raw/l0_reference")
DEFAULT_STATE_DIR = Path("data/artifacts/l0_reference_snapshot")
DEFAULT_PROGRESS_PATH = DEFAULT_STATE_DIR / "collector_progress.json"
DEFAULT_EVENT_PATH = DEFAULT_STATE_DIR / "collector_events.jsonl"
DEFAULT_PLAN_PATH = DEFAULT_STATE_DIR / "reference_snapshot_plan.json"
DEFAULT_CONTRACT_PATH = DEFAULT_STATE_DIR / "l0_reference_contract.json"
DEFAULT_START_DATE = "2016-01-01"
DEFAULT_TRADING_BASE_URL = "https://paper-api.alpaca.markets"


@dataclass(frozen=True)
class ReferenceSnapshotConfig:
    raw_dir: Path = DEFAULT_RAW_DIR
    progress_path: Path = DEFAULT_PROGRESS_PATH
    event_path: Path = DEFAULT_EVENT_PATH
    plan_path: Path = DEFAULT_PLAN_PATH
    contract_path: Path = DEFAULT_CONTRACT_PATH
    start_date: str = DEFAULT_START_DATE
    end_date: str = ""
    base_url: str = DEFAULT_TRADING_BASE_URL


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def resolved_end_date(config: ReferenceSnapshotConfig) -> str:
    return config.end_date or datetime.now(UTC).date().isoformat()


def credentials() -> tuple[str, str]:
    load_repo_env()
    api_key = os.environ.get("APCA_API_KEY_ID") or os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("APCA_API_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("Alpaca credentials are missing. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")
    return api_key, secret_key


def request_json(base_url: str, path: str, params: dict[str, str] | None = None) -> Any:
    api_key, secret_key = credentials()
    query = "" if not params else f"?{urlencode(params)}"
    request = Request(
        f"{base_url.rstrip('/')}{path}{query}",
        headers={
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=60) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_event(path: Path, event: dict[str, Any]) -> None:
    payload = dict(event)
    payload["updated_at"] = now_z()
    payload["diagnostic_only_flag"] = 1
    payload["trade_authority_flag"] = 0
    payload["broker_mutation_permitted_flag"] = 0
    payload["real_capital_permitted_flag"] = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def source_event(
    *,
    source: str,
    status: str,
    row_count: int,
    raw_path: Path | None = None,
    error_category: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    return {
        "provider": "alpaca_trading_api",
        "source": source,
        "status": status,
        "row_count": int(row_count),
        "raw_path": "" if raw_path is None else str(raw_path),
        "error_category": error_category,
        "error_message": redact_text(error_message),
    }


def write_assets_csv(path: Path, rows: list[dict[str, Any]]) -> int:
    fieldnames = [
        "id",
        "class",
        "exchange",
        "symbol",
        "name",
        "status",
        "tradable",
        "marginable",
        "shortable",
        "easy_to_borrow",
        "fractionable",
        "maintenance_margin_requirement",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in sorted(rows, key=lambda item: str(item.get("symbol", ""))):
            writer.writerow(row)
    return len(rows)


def write_calendar_csv(path: Path, rows: list[dict[str, Any]]) -> int:
    frame = pd.DataFrame(rows)
    columns = ["date", "open", "close", "session_open", "session_close"]
    for col in columns:
        if col not in frame.columns:
            frame[col] = ""
    frame = frame.loc[:, columns].sort_values("date").drop_duplicates("date", keep="last")
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return int(len(frame))


def build_plan(config: ReferenceSnapshotConfig) -> dict[str, Any]:
    end_date = resolved_end_date(config)
    plan = {
        "created_at": now_z(),
        "objective": "Capture L0 reference sources for universe/assets, trading calendar, and current market status.",
        "sources": {
            "alpaca_assets_active": "/v2/assets?status=active&asset_class=us_equity",
            "alpaca_assets_inactive": "/v2/assets?status=inactive&asset_class=us_equity",
            "alpaca_calendar": f"/v2/calendar?start={config.start_date}&end={end_date}",
            "alpaca_clock": "/v2/clock",
        },
        "outputs": {
            "raw_dir": str(config.raw_dir),
            "assets_csv": str(config.raw_dir / "alpaca_assets_us_equity_snapshot.csv"),
            "calendar_csv": str(config.raw_dir / f"alpaca_calendar_{config.start_date}_{end_date}.csv"),
            "clock_json": str(config.raw_dir / "alpaca_clock_snapshot.json"),
        },
        "permissions": {
            "diagnostic_only": True,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
        },
    }
    write_json(config.plan_path, plan)
    write_json(
        config.contract_path,
        {
            "created_at": now_z(),
            "status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
            "assets": {
                "consumer_role": "L0 universe/status reference",
                "key": "symbol",
                "historical_lifecycle_status": "CURRENT_AND_INACTIVE_SNAPSHOT_ONLY_NOT_FULL_HISTORICAL_LIFECYCLE",
            },
            "calendar": {
                "consumer_role": "session-date reference for L1/L2 coverage audit",
                "key": "date",
                "range": {"start": config.start_date, "end": end_date},
            },
            "clock": {
                "consumer_role": "current market status evidence",
                "historical_status": "CURRENT_STATUS_SNAPSHOT_ONLY",
            },
            "non_negotiables": {
                "missing_raw_sources_are_not_approximated": True,
                "no_trading_or_broker_mutation": True,
            },
        },
    )
    return plan


def run_reference_snapshot(config: ReferenceSnapshotConfig) -> dict[str, Any]:
    build_plan(config)
    events: list[dict[str, Any]] = []
    active_assets: list[dict[str, Any]] = []
    inactive_assets: list[dict[str, Any]] = []
    end_date = resolved_end_date(config)

    for status in ("active", "inactive"):
        source = f"alpaca_assets_{status}"
        raw_path = config.raw_dir / f"{source}.json"
        try:
            payload = request_json(config.base_url, "/v2/assets", {"status": status, "asset_class": "us_equity"})
            rows = payload if isinstance(payload, list) else []
            write_json(raw_path, rows)
            if status == "active":
                active_assets = rows
            else:
                inactive_assets = rows
            events.append(source_event(source=source, status="EXPORTED", row_count=len(rows), raw_path=raw_path))
        except Exception as exc:  # noqa: BLE001
            events.append(source_event(source=source, status="FAILED_RETRYABLE", row_count=0, raw_path=raw_path, error_category=type(exc).__name__, error_message=str(exc)))

    assets_csv = config.raw_dir / "alpaca_assets_us_equity_snapshot.csv"
    asset_rows = active_assets + inactive_assets
    if asset_rows:
        row_count = write_assets_csv(assets_csv, asset_rows)
        events.append(source_event(source="alpaca_assets_us_equity_snapshot_csv", status="EXPORTED", row_count=row_count, raw_path=assets_csv))

    calendar_raw = config.raw_dir / f"alpaca_calendar_{config.start_date}_{end_date}.json"
    calendar_csv = config.raw_dir / f"alpaca_calendar_{config.start_date}_{end_date}.csv"
    try:
        payload = request_json(config.base_url, "/v2/calendar", {"start": config.start_date, "end": end_date})
        rows = payload if isinstance(payload, list) else []
        write_json(calendar_raw, rows)
        row_count = write_calendar_csv(calendar_csv, rows)
        events.append(source_event(source="alpaca_calendar", status="EXPORTED", row_count=row_count, raw_path=calendar_csv))
    except Exception as exc:  # noqa: BLE001
        events.append(source_event(source="alpaca_calendar", status="FAILED_RETRYABLE", row_count=0, raw_path=calendar_raw, error_category=type(exc).__name__, error_message=str(exc)))

    clock_raw = config.raw_dir / "alpaca_clock_snapshot.json"
    try:
        payload = request_json(config.base_url, "/v2/clock")
        write_json(clock_raw, payload)
        events.append(source_event(source="alpaca_clock", status="EXPORTED", row_count=1, raw_path=clock_raw))
    except Exception as exc:  # noqa: BLE001
        events.append(source_event(source="alpaca_clock", status="FAILED_RETRYABLE", row_count=0, raw_path=clock_raw, error_category=type(exc).__name__, error_message=str(exc)))

    for event in events:
        append_event(config.event_path, event)

    progress = {
        "updated_at": now_z(),
        "status": "PRIMARY_PASS" if all(event["status"] == "EXPORTED" for event in events) else "PARTIAL_SOURCE",
        "processed_events": len(events),
        "exported_events": sum(1 for event in events if event["status"] == "EXPORTED"),
        "failed_events": sum(1 for event in events if event["status"] != "EXPORTED"),
        "raw_dir": str(config.raw_dir),
        "plan_path": str(config.plan_path),
        "contract_path": str(config.contract_path),
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
        "events": events,
    }
    write_json(config.progress_path, progress)
    return progress
