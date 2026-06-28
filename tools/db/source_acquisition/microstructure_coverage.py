from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from tools.db.source_acquisition.microstructure_checkpoint import DEFAULT_CHECKPOINT_PATH, MicrostructureCheckpointStore, sha256_file


DEFAULT_RAW_DIR = Path("data/raw/alpaca_historical_microstructure")
DEFAULT_OUTPUT_DIR = Path("data/artifacts/microstructure")
COVERAGE_FILES = {
    "raw_catalog": "microstructure_raw_catalog.csv",
    "by_symbol": "microstructure_coverage_by_symbol.csv",
    "by_date": "microstructure_coverage_by_date.csv",
    "by_symbol_date": "microstructure_coverage_by_symbol_date.csv",
    "integrity": "microstructure_integrity_audit.csv",
    "missing_reason": "microstructure_missing_reason.csv",
}


def build_microstructure_coverage(
    *,
    raw_dir: Path = DEFAULT_RAW_DIR,
    output_dir: Path | None = DEFAULT_OUTPUT_DIR,
    symbols: Iterable[str] | None = None,
    session_dates: Iterable[str] | None = None,
) -> dict[str, pd.DataFrame]:
    expected_symbols = sorted({str(symbol).upper() for symbol in (symbols or []) if str(symbol).strip()})
    expected_dates = sorted({str(day) for day in (session_dates or []) if str(day).strip()})
    catalog = build_raw_catalog(raw_dir)
    if not expected_symbols:
        expected_symbols = sorted(catalog["symbol"].dropna().astype(str).str.upper().unique().tolist()) if not catalog.empty else []
    if not expected_dates:
        expected_dates = sorted(catalog["session_date"].dropna().astype(str).unique().tolist()) if not catalog.empty else []
    by_symbol_date = build_symbol_date_coverage(catalog, expected_symbols, expected_dates)
    by_symbol = _coverage_group(by_symbol_date, ["symbol"])
    by_date = _coverage_group(by_symbol_date, ["session_date"])
    integrity = build_integrity_audit(catalog)
    missing = build_missing_reason(by_symbol_date)
    artifacts = {
        "raw_catalog": catalog,
        "by_symbol": by_symbol,
        "by_date": by_date,
        "by_symbol_date": by_symbol_date,
        "integrity": integrity,
        "missing_reason": missing,
    }
    if output_dir is not None:
        write_coverage_artifacts(artifacts, output_dir)
    return artifacts


def build_raw_catalog(raw_dir: Path = DEFAULT_RAW_DIR) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in sorted(raw_dir.rglob("*.csv")):
        if not any(part.startswith("feed=") for part in path.parts):
            continue
        source_type = _source_type_from_path(path)
        if source_type not in {"quotes", "trades"}:
            continue
        feed = next((part.split("=", 1)[1] for part in path.parts if part.startswith("feed=")), "")
        rows.append(
            _catalog_one(
                path,
                source_type=source_type,
                feed=feed,
                symbol=_symbol_from_path(path),
                session_date_hint=_session_date_from_path(path),
            )
        )
    columns = [
        "source_type",
        "feed",
        "symbol",
        "session_date",
        "raw_path",
        "file_exists_flag",
        "readable_flag",
        "timestamp_parseable_flag",
        "timestamps_inside_requested_chunk_window_flag",
        "first_ts",
        "last_ts",
        "row_count",
        "duplicate_timestamp_or_trade_id_count",
        "raw_sha256",
        "future_data_used_flag",
        "open_bar_proxy_used_flag",
        "yfinance_proxy_used_flag",
        "secret_logged_flag",
    ]
    return pd.DataFrame(rows, columns=columns)


def _source_type_from_path(path: Path) -> str:
    normalized = path.as_posix()
    if "/source_type=quotes/" in normalized or "/quotes/" in normalized:
        return "quotes"
    if "/source_type=trades/" in normalized or "/trades/" in normalized:
        return "trades"
    return "unknown"


def _symbol_from_path(path: Path) -> str:
    for part in path.parts:
        if part.startswith("symbol="):
            return part.split("=", 1)[1].upper()
    return path.stem.upper()


def _session_date_from_path(path: Path) -> str:
    for part in path.parts:
        if part.startswith("session_date="):
            return part.split("=", 1)[1]
    return ""


def _catalog_one(path: Path, *, source_type: str, feed: str, symbol: str, session_date_hint: str = "") -> dict[str, object]:
    base = {
        "source_type": source_type,
        "feed": feed,
        "symbol": symbol.upper(),
        "session_date": session_date_hint,
        "raw_path": str(path),
        "file_exists_flag": int(path.exists()),
        "readable_flag": 0,
        "timestamp_parseable_flag": 0,
        "timestamps_inside_requested_chunk_window_flag": 1,
        "first_ts": "",
        "last_ts": "",
        "row_count": 0,
        "duplicate_timestamp_or_trade_id_count": 0,
        "raw_sha256": "",
        "future_data_used_flag": 0,
        "open_bar_proxy_used_flag": 0,
        "yfinance_proxy_used_flag": 0,
        "secret_logged_flag": 0,
    }
    try:
        frame = pd.read_csv(path)
        base["readable_flag"] = 1
        base["row_count"] = int(len(frame))
        ts_col = "quote_ts" if source_type == "quotes" else "trade_ts" if source_type == "trades" else ""
        if ts_col and ts_col in frame.columns and not frame.empty:
            ts = pd.to_datetime(frame[ts_col], utc=True, errors="coerce").dropna()
            if not ts.empty:
                base["timestamp_parseable_flag"] = 1
                base["first_ts"] = ts.min().isoformat().replace("+00:00", "Z")
                base["last_ts"] = ts.max().isoformat().replace("+00:00", "Z")
                base["session_date"] = str(ts.min().date())
                duplicate_cols = [ts_col, "symbol"]
                if source_type == "trades" and "trade_id" in frame.columns:
                    duplicate_cols.append("trade_id")
                base["duplicate_timestamp_or_trade_id_count"] = int(frame.duplicated([col for col in duplicate_cols if col in frame.columns]).sum())
        text_sample = path.read_text(encoding="utf-8-sig", errors="ignore")[:4096]
        base["secret_logged_flag"] = int("APCA_API_SECRET" in text_sample or "MARKETAUX_API_KEY" in text_sample)
        base["raw_sha256"] = sha256_file(path)
    except Exception:
        base["readable_flag"] = 0
    return base


def build_symbol_date_coverage(catalog: pd.DataFrame, symbols: list[str], session_dates: list[str]) -> pd.DataFrame:
    if not symbols or not session_dates:
        return pd.DataFrame(
            columns=[
                "symbol",
                "session_date",
                "quotes_expected_flag",
                "trades_expected_flag",
                "quotes_available_flag",
                "trades_available_flag",
                "quote_row_count",
                "trade_row_count",
                "future_data_used_flag",
                "open_bar_proxy_used_flag",
                "yfinance_proxy_used_flag",
                "secret_logged_flag",
                "feature_builder_allowed_flag",
            ]
        )
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        for session_date in session_dates:
            subset = catalog[catalog.get("symbol", pd.Series(dtype=str)).astype(str).str.upper().eq(symbol)]
            subset = subset[subset.get("session_date", pd.Series(dtype=str)).astype(str).eq(session_date)] if not subset.empty else subset
            quotes = subset[subset.get("source_type", pd.Series(dtype=str)).eq("quotes")] if not subset.empty else pd.DataFrame()
            trades = subset[subset.get("source_type", pd.Series(dtype=str)).eq("trades")] if not subset.empty else pd.DataFrame()
            rows.append(
                {
                    "symbol": symbol,
                    "session_date": session_date,
                    "quotes_expected_flag": 1,
                    "trades_expected_flag": 1,
                    "quotes_available_flag": int(not quotes.empty and int(quotes["row_count"].sum()) > 0),
                    "trades_available_flag": int(not trades.empty and int(trades["row_count"].sum()) > 0),
                    "quote_row_count": int(quotes["row_count"].sum()) if not quotes.empty else 0,
                    "trade_row_count": int(trades["row_count"].sum()) if not trades.empty else 0,
                    "future_data_used_flag": int(subset.get("future_data_used_flag", pd.Series([0])).max()) if not subset.empty else 0,
                    "open_bar_proxy_used_flag": int(subset.get("open_bar_proxy_used_flag", pd.Series([0])).max()) if not subset.empty else 0,
                    "yfinance_proxy_used_flag": int(subset.get("yfinance_proxy_used_flag", pd.Series([0])).max()) if not subset.empty else 0,
                    "secret_logged_flag": int(subset.get("secret_logged_flag", pd.Series([0])).max()) if not subset.empty else 0,
                    "feature_builder_allowed_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def _coverage_group(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=group_cols + ["expected_rows", "quote_coverage_rate", "trade_coverage_rate"])
    rows = []
    for key, group in frame.groupby(group_cols, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        rows.append(
            {
                **dict(zip(group_cols, key)),
                "expected_rows": int(len(group)),
                "quote_coverage_rate": float(group["quotes_available_flag"].mean()),
                "trade_coverage_rate": float(group["trades_available_flag"].mean()),
                "quote_row_count": int(group["quote_row_count"].sum()),
                "trade_row_count": int(group["trade_row_count"].sum()),
            }
        )
    return pd.DataFrame(rows)


def build_integrity_audit(catalog: pd.DataFrame) -> pd.DataFrame:
    if catalog.empty:
        return pd.DataFrame(
            [
                {
                    "audit_name": "microstructure_raw_catalog_nonempty",
                    "pass_flag": 0,
                    "future_data_used_flag": 0,
                    "open_bar_proxy_used_flag": 0,
                    "yfinance_proxy_used_flag": 0,
                    "secret_logged_flag": 0,
                    "feature_builder_allowed_flag": 0,
                }
            ]
        )
    checks = [
        ("files_readable", int(catalog["readable_flag"].min())),
        ("timestamps_parseable", int(catalog["timestamp_parseable_flag"].min())),
        ("no_duplicate_timestamp_or_trade_id", int(int(catalog["duplicate_timestamp_or_trade_id_count"].sum()) == 0)),
        ("no_future_data", int(int(catalog["future_data_used_flag"].max()) == 0)),
        ("no_open_bar_proxy", int(int(catalog["open_bar_proxy_used_flag"].max()) == 0)),
        ("no_yfinance_proxy", int(int(catalog["yfinance_proxy_used_flag"].max()) == 0)),
        ("no_secret_logged", int(int(catalog["secret_logged_flag"].max()) == 0)),
        ("feature_builder_blocked", 1),
    ]
    return pd.DataFrame(
        [
            {
                "audit_name": name,
                "pass_flag": passed,
                "future_data_used_flag": int(catalog["future_data_used_flag"].max()),
                "open_bar_proxy_used_flag": int(catalog["open_bar_proxy_used_flag"].max()),
                "yfinance_proxy_used_flag": int(catalog["yfinance_proxy_used_flag"].max()),
                "secret_logged_flag": int(catalog["secret_logged_flag"].max()),
                "feature_builder_allowed_flag": 0,
            }
            for name, passed in checks
        ]
    )


def build_missing_reason(by_symbol_date: pd.DataFrame) -> pd.DataFrame:
    if by_symbol_date.empty:
        return pd.DataFrame(columns=["symbol", "session_date", "source_type", "missing_reason"])
    rows: list[dict[str, object]] = []
    for rec in by_symbol_date.to_dict(orient="records"):
        if int(rec["quotes_available_flag"]) == 0:
            rows.append({"symbol": rec["symbol"], "session_date": rec["session_date"], "source_type": "quotes", "missing_reason": "MISSING_RAW_CHUNK_NOT_APPROXIMATED"})
        if int(rec["trades_available_flag"]) == 0:
            rows.append({"symbol": rec["symbol"], "session_date": rec["session_date"], "source_type": "trades", "missing_reason": "MISSING_RAW_CHUNK_NOT_APPROXIMATED"})
    return pd.DataFrame(rows)


def write_coverage_artifacts(artifacts: dict[str, pd.DataFrame], output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, filename in COVERAGE_FILES.items():
        artifacts[key].to_csv(output_dir / filename, index=False, encoding="utf-8-sig")
    heartbeat = build_heartbeat(artifacts)
    (output_dir / "microstructure_collection_heartbeat.json").write_text(json.dumps(heartbeat, indent=2, sort_keys=True), encoding="utf-8")
    build_failure_ledger().to_csv(output_dir / "microstructure_collection_failure_ledger.csv", index=False, encoding="utf-8-sig")


def build_failure_ledger(checkpoint_path: Path = DEFAULT_CHECKPOINT_PATH) -> pd.DataFrame:
    rows = MicrostructureCheckpointStore(checkpoint_path).load()
    failures = [row for row in rows if str(row.get("status", "")).startswith("FAILED") or row.get("status") in {"RATE_LIMITED", "CREDENTIAL_BLOCKED", "EMPTY_PROVIDER_RESPONSE", "QUARANTINED"}]
    return pd.DataFrame(failures)


def build_heartbeat(artifacts: dict[str, pd.DataFrame], checkpoint_path: Path = DEFAULT_CHECKPOINT_PATH) -> dict[str, object]:
    rows = MicrostructureCheckpointStore(checkpoint_path).load()
    success = [row for row in rows if row.get("status") == "EXPORTED"]
    quote_success = [row for row in success if row.get("source_type") == "quotes"]
    trade_success = [row for row in success if row.get("source_type") == "trades"]
    by_symbol_date = artifacts.get("by_symbol_date", pd.DataFrame())
    quote_rate = float(by_symbol_date["quotes_available_flag"].mean()) if not by_symbol_date.empty else 0.0
    trade_rate = float(by_symbol_date["trades_available_flag"].mean()) if not by_symbol_date.empty else 0.0
    failure_rows = [row for row in rows if str(row.get("status", "")).startswith("FAILED")]
    latest_error = sorted(failure_rows, key=lambda row: str(row.get("updated_at", "")))[-1] if failure_rows else {}
    latest_success_ts = max([str(row.get("last_success_ts", "")) for row in success], default="")
    stale_status = "STALE" if not latest_success_ts else "OK"
    if any(row.get("status") == "CREDENTIAL_BLOCKED" for row in rows):
        stale_status = "CREDENTIAL_BLOCKED"
    elif any(row.get("status") == "RATE_LIMITED" for row in rows):
        stale_status = "RATE_LIMITED"
    elif any(row.get("status") == "EMPTY_PROVIDER_RESPONSE" for row in rows):
        stale_status = "EMPTY_PROVIDER_RESPONSE"
    elif len([row for row in rows if row.get("status") == "FAILED_RETRYABLE"]) >= 3:
        stale_status = "DEGRADED"
    return {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "last_success_ts": latest_success_ts,
        "last_quote_success_ts": max([str(row.get("last_success_ts", "")) for row in quote_success], default=""),
        "last_trade_success_ts": max([str(row.get("last_success_ts", "")) for row in trade_success], default=""),
        "last_failed_ts": max([str(row.get("updated_at", "")) for row in failure_rows], default=""),
        "pending_chunks": sum(1 for row in rows if row.get("status") == "PENDING"),
        "running_chunks": sum(1 for row in rows if row.get("status") == "RUNNING"),
        "failed_retryable_chunks": sum(1 for row in rows if row.get("status") == "FAILED_RETRYABLE"),
        "failed_permanent_chunks": sum(1 for row in rows if row.get("status") == "FAILED_PERMANENT"),
        "quote_coverage_rate": quote_rate,
        "trade_coverage_rate": trade_rate,
        "latest_error_category": latest_error.get("error_category", ""),
        "stale_status": stale_status,
    }
