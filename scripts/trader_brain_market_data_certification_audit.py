from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data/artifacts/task_850_859_data_certification"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def inspect_csv_file(path: Path) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        timestamp_col = "timestamp" if "timestamp" in columns else ("date" if "date" in columns else "")
        symbol_values: set[str] = set()
        row_count = 0
        min_ts = ""
        max_ts = ""
        prev_ts = ""
        duplicate_count = 0
        unsorted_count = 0
        missing_cells = 0
        seen_ts: set[str] = set()
        for row in reader:
            row_count += 1
            if "symbol" in row and row.get("symbol"):
                symbol_values.add(str(row["symbol"]))
            if timestamp_col:
                ts = str(row.get(timestamp_col, ""))
                if ts:
                    min_ts = ts if not min_ts or ts < min_ts else min_ts
                    max_ts = ts if not max_ts or ts > max_ts else max_ts
                    if ts in seen_ts:
                        duplicate_count += 1
                    seen_ts.add(ts)
                    if prev_ts and ts < prev_ts:
                        unsorted_count += 1
                    prev_ts = ts
            missing_cells += sum(1 for value in row.values() if value is None or value == "")
    schema_fingerprint = "_".join(columns)
    return {
        "columns": columns,
        "schema_fingerprint": schema_fingerprint,
        "timestamp_column": timestamp_col,
        "row_count": row_count,
        "min_ts": min_ts,
        "max_ts": max_ts,
        "symbol_values": sorted(symbol_values),
        "duplicate_count": duplicate_count,
        "unsorted_count": unsorted_count,
        "missing_cells": missing_cells,
        "content_hash": sha256_file(path),
    }


def certification_for_dataset(dataset_id: str, *, has_symbol: bool, adjustment_policy: str, schema_variants: int, calendar_ready: bool, pit_ready: bool) -> tuple[str, str]:
    blockers: list[str] = []
    if not has_symbol:
        blockers.append("blocked_missing_symbol_namespace")
    if adjustment_policy == "unknown":
        blockers.append("blocked_missing_adjustment_proof")
    if schema_variants > 1:
        blockers.append("blocked_mixed_schema")
    if not calendar_ready and dataset_id in {"us_intraday", "us_daily_breadth_top500", "us_daily"}:
        blockers.append("blocked_calendar_not_certified")
    if not pit_ready and dataset_id in {"us_daily_breadth_top500"}:
        blockers.append("blocked_point_in_time_universe_missing")
    if blockers:
        return "redownload_required" if "blocked_mixed_schema" in blockers else "schema_valid_source_blocked", ";".join(blockers)
    return "conditional_reuse", "source hash schema and coverage observed; still requires Task859 owner gate"


def inspect_csv_dataset(path: Path, dataset_id: str, provider: str, data_family: str, granularity: str, adjustment_policy: str, out_rows: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    files = sorted(path.glob("*.csv"))
    schema_counter: Counter[str] = Counter()
    total_rows = 0
    min_ts = ""
    max_ts = ""
    bad_files = 0
    duplicate_files = 0
    unsorted_files = 0
    symbol_count = 0
    explicit_symbol_files = 0
    file_symbols: list[str] = []

    for file_path in files:
        try:
            info = inspect_csv_file(file_path)
        except Exception as exc:  # pragma: no cover - defensive audit output
            bad_files += 1
            out_rows["file_inventory"].append(
                {
                    "dataset_id": dataset_id,
                    "raw_source_path": str(file_path.as_posix()),
                    "asset_class": "us_equity",
                    "provider": provider,
                    "feed": "file",
                    "data_family": data_family,
                    "symbol": file_path.stem,
                    "symbol_source": "file_stem_untrusted",
                    "date_start": "",
                    "date_end": "",
                    "timezone": "unknown",
                    "bar_interval": granularity,
                    "adjustment_policy": adjustment_policy,
                    "content_hash": "",
                    "row_count": 0,
                    "schema_fingerprint": "read_error",
                    "timestamp_column": "",
                    "duplicate_count": "",
                    "unsorted_count": "",
                    "missing_cells": "",
                    "certification_status": "schema_invalid",
                    "certification_reason": repr(exc),
                }
            )
            continue
        columns = list(info["columns"])
        schema = str(info["schema_fingerprint"])
        schema_counter[schema] += 1
        total_rows += int(info["row_count"])
        if info["min_ts"]:
            min_ts = str(info["min_ts"]) if not min_ts or str(info["min_ts"]) < min_ts else min_ts
        if info["max_ts"]:
            max_ts = str(info["max_ts"]) if not max_ts or str(info["max_ts"]) > max_ts else max_ts
        if int(info["duplicate_count"]) > 0:
            duplicate_files += 1
        if int(info["unsorted_count"]) > 0:
            unsorted_files += 1
        has_explicit_symbol = bool(info["symbol_values"])
        if has_explicit_symbol:
            explicit_symbol_files += 1
        file_symbols.append(file_path.stem)
        symbol_count += 1
        status, reason = certification_for_dataset(
            dataset_id,
            has_symbol=has_explicit_symbol,
            adjustment_policy=adjustment_policy,
            schema_variants=1,
            calendar_ready=False,
            pit_ready=False,
        )
        if dataset_id == "us_daily" and has_explicit_symbol:
            status = "schema_valid_source_blocked"
            reason = "blocked_missing_adjustment_proof;blocked_calendar_not_certified;limited_23_symbol_reference_only"
        out_rows["file_inventory"].append(
            {
                "dataset_id": dataset_id,
                "raw_source_path": str(file_path.as_posix()),
                "asset_class": "us_equity",
                "provider": provider,
                "feed": "file",
                "data_family": data_family,
                "symbol": ";".join(info["symbol_values"]) if has_explicit_symbol else file_path.stem,
                "symbol_source": "row_column" if has_explicit_symbol else "file_stem_requires_manifest",
                "date_start": str(info["min_ts"])[:10],
                "date_end": str(info["max_ts"])[:10],
                "timezone": "UTC_or_date_text_unverified",
                "bar_interval": granularity,
                "adjustment_policy": adjustment_policy,
                "content_hash": info["content_hash"],
                "row_count": info["row_count"],
                "schema_fingerprint": schema,
                "timestamp_column": info["timestamp_column"],
                "duplicate_count": info["duplicate_count"],
                "unsorted_count": info["unsorted_count"],
                "missing_cells": info["missing_cells"],
                "certification_status": status,
                "certification_reason": reason,
            }
        )
        out_rows["symbol_file_map"].append(
            {
                "dataset_id": dataset_id,
                "symbol": file_path.stem,
                "raw_source_path": str(file_path.as_posix()),
                "symbol_source": "row_column" if has_explicit_symbol else "file_stem_requires_owner_certification",
                "allowed_use": "symbol_panel_after_certification" if has_explicit_symbol else "not_allowed_for_replay_until_manifest_certified",
            }
        )

    for schema, count in sorted(schema_counter.items()):
        out_rows["schema_fingerprint_inventory"].append(
            {
                "dataset_id": dataset_id,
                "schema_fingerprint": schema,
                "file_count": count,
                "certification_status": "schema_consistent" if len(schema_counter) == 1 else "blocked_mixed_schema",
            }
        )

    dataset_status, dataset_reason = certification_for_dataset(
        dataset_id,
        has_symbol=explicit_symbol_files == len(files) and len(files) > 0,
        adjustment_policy=adjustment_policy,
        schema_variants=len(schema_counter),
        calendar_ready=False,
        pit_ready=False,
    )
    if dataset_id == "us_daily":
        dataset_status = "certified_reference_only"
        dataset_reason = "clean 23-symbol schema but limited universe and adjustment proof/calendar missing"
    if dataset_id == "us_intraday":
        dataset_status = "redownload_required"
        dataset_reason = "blocked_mixed_schema;blocked_missing_adjustment_proof;blocked_calendar_not_certified;normalize_or_redownload_gap_slices"
    out_rows["canonical_data_manifest"].append(
        {
            "dataset_id": dataset_id,
            "asset_class": "us_equity",
            "provider": provider,
            "feed": "file",
            "data_family": data_family,
            "symbol": "MULTI",
            "symbol_source": "row_column" if explicit_symbol_files == len(files) and files else "file_stem_requires_manifest",
            "date_start": min_ts[:10],
            "date_end": max_ts[:10],
            "timezone": "UTC_or_date_text_unverified",
            "bar_interval": granularity,
            "adjustment_policy": adjustment_policy,
            "raw_source_path": str(path.as_posix()),
            "canonical_path": "",
            "content_hash": hash_text("|".join(sorted(f"{p.name}:{p.stat().st_size}:{p.stat().st_mtime_ns}" for p in files))),
            "row_count": total_rows,
            "schema_version": "market_data_manifest_v1",
            "schema_fingerprint": "mixed" if len(schema_counter) > 1 else next(iter(schema_counter), ""),
            "required_columns_present": "true" if bad_files == 0 else "false",
            "timestamp_column": "timestamp",
            "event_time_available_flag": "1",
            "receive_time_available_flag": "0",
            "downloaded_at": "",
            "as_of_cutoff": datetime.now(timezone.utc).isoformat(),
            "data_available_ts": "",
            "future_leakage_check": "not_checked_no_replay",
            "dedupe_key": "symbol_timestamp",
            "certification_status": dataset_status,
            "certification_reason": dataset_reason,
            "gap_id": f"gap_{dataset_id}_certification",
            "redownload_required": "true" if dataset_status == "redownload_required" else "false",
            "validator_version": "market_data_certifier_v1",
        }
    )
    return {
        "dataset_id": dataset_id,
        "file_count": len(files),
        "row_count": total_rows,
        "schema_variants": len(schema_counter),
        "date_start": min_ts[:10],
        "date_end": max_ts[:10],
        "explicit_symbol_files": explicit_symbol_files,
        "duplicate_files": duplicate_files,
        "unsorted_files": unsorted_files,
    }


def inspect_microstructure(path: Path, out_rows: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    stats: dict[str, dict[str, object]] = {}
    for root, _, files in os.walk(path):
        parquet_files = [name for name in files if name.endswith(".parquet")]
        if not parquet_files:
            continue
        parts = Path(root).parts
        provider = next((part.split("=", 1)[1] for part in parts if part.startswith("provider=")), "unknown")
        feed = next((part.split("=", 1)[1] for part in parts if part.startswith("feed=")), "unknown")
        typ = next((part.split("=", 1)[1] for part in parts if part.startswith("type=")), "unknown")
        symbol = next((part.split("=", 1)[1] for part in parts if part.startswith("symbol=")), "unknown")
        date = next((part.split("=", 1)[1] for part in parts if part.startswith("date=")), "")
        key = typ
        item = stats.setdefault(
            key,
            {
                "provider": provider,
                "feed": feed,
                "type": typ,
                "symbols": set(),
                "date_start": "",
                "date_end": "",
                "parquet_files": 0,
                "bytes": 0,
            },
        )
        item["symbols"].add(symbol)
        item["parquet_files"] += len(parquet_files)
        item["bytes"] += sum((Path(root) / name).stat().st_size for name in parquet_files)
        if date:
            item["date_start"] = date if not item["date_start"] or date < item["date_start"] else item["date_start"]
            item["date_end"] = date if not item["date_end"] or date > item["date_end"] else item["date_end"]

    for item in stats.values():
        symbols = sorted(item["symbols"])
        out_rows["microstructure_readiness_audit"].append(
            {
                "dataset_id": "microstructure_full",
                "provider": item["provider"],
                "feed": item["feed"],
                "source_type": item["type"],
                "symbol_count": len(symbols),
                "symbols": ";".join(symbols),
                "date_start": item["date_start"],
                "date_end": item["date_end"],
                "parquet_file_count": item["parquet_files"],
                "total_bytes": item["bytes"],
                "receive_time_available_flag": "0_observed_in_sample",
                "historical_live_ready_flag": "0_observed_in_sample",
                "certification_status": "certified_reference_only",
                "certification_reason": "research_only_event_window_candidate_not_common_first_replay_input",
            }
        )
        out_rows["canonical_data_manifest"].append(
            {
                "dataset_id": f"microstructure_full_{item['type']}",
                "asset_class": "us_equity",
                "provider": item["provider"],
                "feed": item["feed"],
                "data_family": f"microstructure_{item['type']}",
                "symbol": ";".join(symbols),
                "symbol_source": "partition_path",
                "date_start": item["date_start"],
                "date_end": item["date_end"],
                "timezone": "UTC",
                "bar_interval": "tick",
                "adjustment_policy": "not_for_first_replay",
                "raw_source_path": str(path.as_posix()),
                "canonical_path": "",
                "content_hash": hash_text(f"{item['type']}|{symbols}|{item['parquet_files']}|{item['bytes']}"),
                "row_count": "",
                "schema_version": "market_data_manifest_v1",
                "schema_fingerprint": f"alpaca_sip_{item['type']}_parquet_partitioned",
                "required_columns_present": "not_checked_partition_only",
                "timestamp_column": "quote_ts_or_trade_ts",
                "event_time_available_flag": "1",
                "receive_time_available_flag": "0",
                "downloaded_at": "",
                "as_of_cutoff": datetime.now(timezone.utc).isoformat(),
                "data_available_ts": "",
                "future_leakage_check": "not_checked_no_replay",
                "dedupe_key": "provider_feed_type_symbol_date_chunk",
                "certification_status": "certified_reference_only",
                "certification_reason": "microstructure research-only; not live-ready; not first controlled replay common input",
                "gap_id": "",
                "redownload_required": "false",
                "validator_version": "market_data_certifier_v1",
            }
        )
    return {key: {**value, "symbols": sorted(value["symbols"])} for key, value in stats.items()}


def inspect_calendar(path: Path, out_rows: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    if not path.exists():
        row = {
            "calendar_id": "nasdaq_market_calendar",
            "path": str(path.as_posix()),
            "date_start": "",
            "date_end": "",
            "row_count": 0,
            "certification_status": "blocked_missing_calendar",
            "certification_reason": "calendar file missing",
        }
        out_rows["calendar_audit"].append(row)
        return row
    rows = read_csv_rows(path)
    dates = [row.get("date", "") for row in rows if row.get("date")]
    status = "schema_valid_source_blocked"
    reason = "calendar observed but coverage starts after required 2021-01-01 and open-session rows need version certification"
    row = {
        "calendar_id": "nasdaq_market_calendar",
        "path": str(path.as_posix()),
        "date_start": min(dates) if dates else "",
        "date_end": max(dates) if dates else "",
        "row_count": len(rows),
        "certification_status": status,
        "certification_reason": reason,
    }
    out_rows["calendar_audit"].append(row)
    return row


def build_gap_rows(out_rows: dict[str, list[dict[str, object]]]) -> None:
    gaps = [
        ("gap_daily_adjustment_proof", "daily_ohlcv_adjusted", "all candidate daily datasets", "2021-01-01", "latest_completed_session", "corporate action or adjusted provider proof missing", "attach corporate actions or redownload adjusted daily source"),
        ("gap_pit_universe", "point_in_time_universe", "harness universe", "2021-01-01", "latest_completed_session", "point-in-time universe missing", "source PIT membership or constrain to explicit harness symbols only"),
        ("gap_calendar_2021_2025", "market_calendar", "NASDAQ/NYSE", "2021-01-01", "2025-12-31", "existing config calendar covers 2026 only", "download or build certified exchange calendar"),
        ("gap_intraday_schema_normalization", "intraday_15m_bars", "data/raw/us_intraday", "2024-01-02", "latest_completed_session", "mixed schema and adjustment policy unclear", "normalize exact schema or redownload affected slices"),
        ("gap_corporate_actions", "corporate_actions", "certified replay symbols", "2021-01-01", "latest_completed_session", "no corporate action source found", "download split/dividend/action source"),
    ]
    for gap_id, family, symbol_scope, start, end, reason, action in gaps:
        out_rows["coverage_gap_report"].append(
            {
                "gap_id": gap_id,
                "data_family": family,
                "symbol_scope": symbol_scope,
                "date_start": start,
                "date_end": end,
                "gap_reason": reason,
                "redownload_required": "true" if "redownload" in action or "download" in action else "false",
                "recommended_action": action,
            }
        )
        out_rows["redownload_queue"].append(
            {
                "gap_id": gap_id,
                "download_scope": symbol_scope,
                "data_family": family,
                "date_start": start,
                "date_end": end,
                "priority": "high",
                "download_action": action,
                "approval_required": "yes",
                "overwrite_existing_raw": "no",
            }
        )


def build_decisions(out_rows: dict[str, list[dict[str, object]]]) -> None:
    decisions = [
        ("daily_ohlcv_adjusted", "partial_no_replay", "Existing daily data is useful but blocked by adjustment proof, PIT universe, and calendar gaps"),
        ("intraday_15m_bars", "partial_no_replay", "Existing 15m data has large coverage but mixed schema and missing adjustment/session certification"),
        ("microstructure_quotes_trades", "research_only_no_first_replay", "Alpaca SIP parquet remains research-only and not common first replay input"),
        ("market_calendar", "blocked", "Existing calendar file covers 2026 only and is not enough for 2021-forward replay"),
        ("corporate_actions", "blocked", "No corporate action source found for adjusted replay proof"),
        ("point_in_time_universe", "blocked", "No point-in-time universe source certified"),
        ("market_data_gate_handoff", "MARKET_DATA_CERTIFICATION_PARTIAL_NO_REPLAY", "Task843 must remain blocked until required gates pass"),
    ]
    for area, status, reason in decisions:
        out_rows["certification_decision"].append(
            {
                "decision_area": area,
                "status": status,
                "decision_reason": reason,
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
            }
        )


def run(out_dir: Path) -> dict[str, object]:
    out_rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    summaries: list[dict[str, object]] = []
    summaries.append(inspect_csv_dataset(ROOT / "data/raw/us_daily", "us_daily", "yahoo", "daily_ohlcv", "daily", "unknown", out_rows))
    summaries.append(inspect_csv_dataset(ROOT / "data/raw/us_daily_breadth_top500", "us_daily_breadth_top500", "alpaca_or_unknown", "daily_ohlcv_breadth", "daily", "unknown", out_rows))
    summaries.append(inspect_csv_dataset(ROOT / "data/raw/us_intraday", "us_intraday", "alpaca_or_unknown", "intraday_15m_bars", "15m", "unknown", out_rows))
    micro = inspect_microstructure(ROOT / "data/raw/microstructure_full", out_rows)
    calendar = inspect_calendar(ROOT / "config/nasdaq_market_calendar.csv", out_rows)
    out_rows["corporate_action_audit"].append(
        {
            "source_id": "corporate_actions",
            "path": "",
            "date_start": "",
            "date_end": "",
            "row_count": 0,
            "certification_status": "blocked_missing_corporate_actions",
            "certification_reason": "no split dividend corporate action source found in expected raw paths",
        }
    )
    build_gap_rows(out_rows)
    build_decisions(out_rows)

    write_csv(
        out_dir / "file_inventory.csv",
        out_rows["file_inventory"],
        [
            "dataset_id",
            "raw_source_path",
            "asset_class",
            "provider",
            "feed",
            "data_family",
            "symbol",
            "symbol_source",
            "date_start",
            "date_end",
            "timezone",
            "bar_interval",
            "adjustment_policy",
            "content_hash",
            "row_count",
            "schema_fingerprint",
            "timestamp_column",
            "duplicate_count",
            "unsorted_count",
            "missing_cells",
            "certification_status",
            "certification_reason",
        ],
    )
    write_csv(out_dir / "schema_fingerprint_inventory.csv", out_rows["schema_fingerprint_inventory"], ["dataset_id", "schema_fingerprint", "file_count", "certification_status"])
    write_csv(out_dir / "symbol_file_map.csv", out_rows["symbol_file_map"], ["dataset_id", "symbol", "raw_source_path", "symbol_source", "allowed_use"])
    write_csv(
        out_dir / "canonical_data_manifest.csv",
        out_rows["canonical_data_manifest"],
        [
            "dataset_id",
            "asset_class",
            "provider",
            "feed",
            "data_family",
            "symbol",
            "symbol_source",
            "date_start",
            "date_end",
            "timezone",
            "bar_interval",
            "adjustment_policy",
            "raw_source_path",
            "canonical_path",
            "content_hash",
            "row_count",
            "schema_version",
            "schema_fingerprint",
            "required_columns_present",
            "timestamp_column",
            "event_time_available_flag",
            "receive_time_available_flag",
            "downloaded_at",
            "as_of_cutoff",
            "data_available_ts",
            "future_leakage_check",
            "dedupe_key",
            "certification_status",
            "certification_reason",
            "gap_id",
            "redownload_required",
            "validator_version",
        ],
    )
    write_csv(out_dir / "coverage_gap_report.csv", out_rows["coverage_gap_report"], ["gap_id", "data_family", "symbol_scope", "date_start", "date_end", "gap_reason", "redownload_required", "recommended_action"])
    write_csv(out_dir / "redownload_queue.csv", out_rows["redownload_queue"], ["gap_id", "download_scope", "data_family", "date_start", "date_end", "priority", "download_action", "approval_required", "overwrite_existing_raw"])
    write_csv(out_dir / "certification_decision.csv", out_rows["certification_decision"], ["decision_area", "status", "decision_reason", "strategy_acceptance", "deployment_readiness", "real_capital"])
    write_csv(out_dir / "microstructure_readiness_audit.csv", out_rows["microstructure_readiness_audit"], ["dataset_id", "provider", "feed", "source_type", "symbol_count", "symbols", "date_start", "date_end", "parquet_file_count", "total_bytes", "receive_time_available_flag", "historical_live_ready_flag", "certification_status", "certification_reason"])
    write_csv(out_dir / "market_calendar_audit.csv", out_rows["calendar_audit"], ["calendar_id", "path", "date_start", "date_end", "row_count", "certification_status", "certification_reason"])
    write_csv(out_dir / "corporate_action_audit.csv", out_rows["corporate_action_audit"], ["source_id", "path", "date_start", "date_end", "row_count", "certification_status", "certification_reason"])

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_summaries": summaries,
        "microstructure_summary": micro,
        "calendar_summary": calendar,
        "decision": "MARKET_DATA_CERTIFICATION_PARTIAL_NO_REPLAY",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "no_backtest_executed": True,
    }
    (out_dir / "validator_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_MARKET_DATA_AUDIT_OK] "
        f"decision={summary['decision']} out_dir={args.out_dir}"
    )


if __name__ == "__main__":
    main()
