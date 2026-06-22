from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_893_source_time_recovery"
TASK372_EVENTS = ROOT / "docs/reports/task_372_historical_source_backfill/task_372_historical_source_event_dataset.csv"
TASK371_EVENTS = ROOT / "docs/reports/task_371_source_time_capture/task_371_source_event_dataset.csv"
UNIVERSE_PATH = ROOT / "data/raw/theme_universe_10x7.csv"

PERIOD_START = "2021-01-01T00:00:00+00:00"
PERIOD_END = "2026-03-31T23:59:59+00:00"

RECOVERED_FIELDS = [
    "evidence_id",
    "source_family",
    "symbol",
    "theme",
    "published_ts",
    "received_ts",
    "available_to_brain_ts",
    "source_url_or_file",
    "source_hash",
    "source_gap_flag",
    "bridge_authority",
    "source_event_id",
    "event_type",
    "state_label",
    "capture_mode",
    "source_dataset_version",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, data: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def parse_ts(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    if " " in normalized and "T" not in normalized:
        normalized = normalized.replace(" ", "T")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_ts(value: str) -> str:
    return parse_ts(value).isoformat()


def max_iso_ts(*values: str) -> str:
    parsed = [parse_ts(value) for value in values if value]
    return max(parsed).isoformat()


def row_hash(source_file: str, row: dict[str, str]) -> str:
    payload = json.dumps({"source_file": source_file, "row": row}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_theme_by_symbol() -> dict[str, str]:
    theme_by_symbol: dict[str, str] = {}
    for row in rows(UNIVERSE_PATH):
        theme_by_symbol[row["symbol"]] = row["theme"]
    return theme_by_symbol


def period_ok(ts: str) -> bool:
    event_ts = parse_ts(ts)
    return parse_ts(PERIOD_START) <= event_ts <= parse_ts(PERIOD_END)


def source_truth_like(row: dict[str, str]) -> bool:
    details = row.get("details_json", "")
    return row.get("event_source") == "SOURCE_CAPTURED" and "synthetic_only" not in details


def recover_row(source_file: str, row: dict[str, str], theme_by_symbol: dict[str, str]) -> dict[str, object]:
    published_ts = iso_ts(row["event_timestamp"])
    received_ts = iso_ts(row.get("created_at") or row["event_timestamp"])
    available_ts = max_iso_ts(published_ts, received_ts)
    evidence_id = f"Task893|{row['source_event_id']}"
    symbol = row["symbol"]
    return {
        "evidence_id": evidence_id,
        "source_family": "internal_source_event_capture",
        "symbol": symbol,
        "theme": theme_by_symbol.get(symbol, ""),
        "published_ts": published_ts,
        "received_ts": received_ts,
        "available_to_brain_ts": available_ts,
        "source_url_or_file": source_file,
        "source_hash": row_hash(source_file, row),
        "source_gap_flag": "raw_external_document_missing",
        "bridge_authority": "diagnostic_recovered_internal_event_only",
        "source_event_id": row["source_event_id"],
        "event_type": row.get("event_type", ""),
        "state_label": row.get("state_label", ""),
        "capture_mode": row.get("capture_mode", ""),
        "source_dataset_version": row.get("source_dataset_version", ""),
    }


def rejection_reason(source_file: str, row: dict[str, str]) -> str:
    if source_file.endswith("task_371_source_event_dataset.csv"):
        return "harness_fixture_not_historical_backtest_evidence"
    if not period_ok(row.get("event_timestamp", "")):
        return "outside_2021_2026q1_period"
    if row.get("event_source") != "SOURCE_CAPTURED":
        return "derived_or_session_event_not_source_capture"
    if "synthetic_only" in row.get("details_json", ""):
        return "synthetic_lineage_not_source_truth"
    return "not_recovered"


def run(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    theme_by_symbol = load_theme_by_symbol()
    recovered: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []

    input_files = [TASK372_EVENTS, TASK371_EVENTS]
    for input_path in input_files:
        source_file = input_path.relative_to(ROOT).as_posix()
        for row in rows(input_path):
            if source_file.endswith("task_372_historical_source_event_dataset.csv") and period_ok(row["event_timestamp"]) and source_truth_like(row):
                recovered.append(recover_row(source_file, row, theme_by_symbol))
            else:
                rejected.append(
                    {
                        "source_url_or_file": source_file,
                        "source_event_id": row.get("source_event_id", ""),
                        "symbol": row.get("symbol", ""),
                        "event_source": row.get("event_source", ""),
                        "event_timestamp": row.get("event_timestamp", ""),
                        "rejection_reason": rejection_reason(source_file, row),
                        "does_not_mean": "negative evidence or failed thesis",
                    }
                )

    recovered = sorted(recovered, key=lambda r: (str(r["available_to_brain_ts"]), str(r["symbol"]), str(r["evidence_id"])))
    rejected = sorted(rejected, key=lambda r: (str(r["source_url_or_file"]), str(r["event_timestamp"]), str(r["source_event_id"])))

    symbols = sorted({str(row["symbol"]) for row in recovered})
    themed_symbols = sorted({str(row["symbol"]) for row in recovered if row["theme"]})
    summary_rows = [
        {"metric": "input_event_rows", "value": len(rows(TASK372_EVENTS)) + len(rows(TASK371_EVENTS))},
        {"metric": "recovered_source_time_rows", "value": len(recovered)},
        {"metric": "rejected_event_rows", "value": len(rejected)},
        {"metric": "covered_symbols", "value": len(symbols)},
        {"metric": "covered_symbols_in_10x7_universe", "value": len(themed_symbols)},
        {"metric": "source_gap_flag", "value": "raw_external_document_missing"},
        {"metric": "bridge_authority", "value": "diagnostic_recovered_internal_event_only"},
        {"metric": "first_real_historical_brain_replay", "value": "no_go_until_external_source_or_owner_approved_internal_event_scope"},
    ]
    backlog_rows = [
        {
            "priority": 1,
            "gap": "raw external documents are still missing for recovered internal events",
            "implementation_step": "attach raw filing/news/transcript/macro source files or URLs with hashes to each recovered evidence row",
        },
        {
            "priority": 2,
            "gap": "coverage is partial across the 10x7 universe",
            "implementation_step": "build per-symbol coverage matrix and acquire missing evidence only for uncovered themes/symbols",
        },
        {
            "priority": 3,
            "gap": "replay-derived and session-derived rows are isolated",
            "implementation_step": "keep them out of source evidence; use only for lineage audit after explicit approval",
        },
        {
            "priority": 4,
            "gap": "L1/L2/L3 builders do not yet consume the recovered panel",
            "implementation_step": "add a brain-state builder that only reads recovered rows with available_to_brain_ts <= decision_asof_ts",
        },
    ]

    write_csv(out_dir / "recovered_source_time_panel.csv", recovered, RECOVERED_FIELDS)
    write_csv(
        out_dir / "rejected_event_source_rows.csv",
        rejected,
        ["source_url_or_file", "source_event_id", "symbol", "event_source", "event_timestamp", "rejection_reason", "does_not_mean"],
    )
    write_csv(out_dir / "source_time_recovery_summary.csv", summary_rows, ["metric", "value"])
    write_csv(out_dir / "source_time_recovery_backlog.csv", backlog_rows, ["priority", "gap", "implementation_step"])
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "Task893",
        "input_event_rows": len(rows(TASK372_EVENTS)) + len(rows(TASK371_EVENTS)),
        "recovered_source_time_rows": len(recovered),
        "rejected_event_rows": len(rejected),
        "covered_symbols": len(symbols),
        "covered_symbols_in_10x7_universe": len(themed_symbols),
        "source_gap_flag": "raw_external_document_missing",
        "bridge_authority": "diagnostic_recovered_internal_event_only",
        "first_real_historical_brain_replay": "no_go_until_external_source_or_owner_approved_internal_event_scope",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "task_893_source_time_recovery_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_893_SOURCE_TIME_RECOVERY_OK] "
        f"recovered={summary['recovered_source_time_rows']} rejected={summary['rejected_event_rows']} "
        f"covered_symbols={summary['covered_symbols']} replay={summary['first_real_historical_brain_replay']}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"[TRADER_BRAIN_893_SOURCE_TIME_RECOVERY_ERROR] {type(exc).__name__}: {exc}")
        sys.exit(1)
