from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4124"
STAGE5_SLUG = "task_4123_l0_stage_5_background_historical_backfill_from_2016"
SLUG = "task_4124_l0_stage_6_l1_quality_coverage_audit_l2_handoff"
DEFAULT_REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
STAGE5_REPORT_DIR = ROOT / f"docs/reports/{STAGE5_SLUG}"
STAGE5_RAW_DIR = ROOT / f"data/raw/{STAGE5_SLUG}"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    fields = list(fieldnames or [])
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def secret_like(path: Path) -> bool:
    if path.suffix.lower() not in {".json", ".jsonl", ".csv", ".txt", ".log"}:
        return False
    text = path.read_text(encoding="utf-8-sig", errors="ignore")[:200_000]
    patterns = [
        r"(?i)\bAuthorization\s*[:=]",
        r"(?i)\bBearer\s+[A-Za-z0-9._-]{10,}",
        r"(?i)\b(api[_-]?key|apikey|token|secret)\s*[:=]\s*[A-Za-z0-9._-]{12,}",
        r"\bsk-[A-Za-z0-9_-]{12,}",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def raw_payloads() -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for path in sorted(STAGE5_RAW_DIR.rglob("headlines.json")):
        payload = read_json(path)
        payloads.append({"path": path, "payload": payload})
    return payloads


def headline_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in raw_payloads():
        path = item["path"]
        payload = item["payload"]
        provider = ""
        for row in payload.get("headlines", []) if isinstance(payload.get("headlines"), list) else []:
            record = dict(row)
            provider = str(record.get("provider") or payload.get("provider") or "")
            record["_raw_path"] = rel(path)
            record["_raw_sha256"] = sha256_file(path)
            rows.append(record)
        if not payload.get("headlines"):
            provider = "public_market_macro_news_feeds" if "public_market_macro" in path.as_posix() else "unknown"
            rows.append(
                {
                    "_raw_path": rel(path),
                    "_raw_sha256": sha256_file(path),
                    "provider": provider,
                    "source_key": "",
                    "title": "",
                    "published_at": "",
                    "source_url": "",
                    "_empty_provider_response": 1,
                }
            )
    return rows


def raw_hash_audit() -> list[dict[str, Any]]:
    stage5_raw_ledger = read_csv(STAGE5_REPORT_DIR / "task_4123_raw_response_classification.csv")
    rows: list[dict[str, Any]] = []
    for row in stage5_raw_ledger:
        raw_path = row.get("raw_path", "")
        path = ROOT / raw_path
        exists = path.exists()
        actual_hash = sha256_file(path) if exists else ""
        rows.append(
            {
                "task_id": TASK_ID,
                "raw_path": raw_path,
                "expected_sha256": row.get("raw_sha256", ""),
                "actual_sha256": actual_hash,
                "hash_match": int(exists and actual_hash == row.get("raw_sha256", "")),
                "secret_scan_pass": int(exists and not secret_like(path)),
                "raw_exists": int(exists),
            }
        )
    return rows


def mapping_audit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        provider = str(row.get("provider", ""))
        ticker_required = int(row.get("ticker_mapping_required_flag", 1) or 0) if str(row.get("ticker_mapping_required_flag", "")) != "" else 1
        macro_context = int(row.get("macro_context_candidate_flag", 0) or 0)
        has_mapping = bool(row.get("symbols") or row.get("tickers") or row.get("entities") or row.get("entity_map"))
        empty = int(row.get("_empty_provider_response", 0) or 0)
        if empty:
            status = "NO_ROWS_TO_MAP"
        elif ticker_required == 0 or macro_context == 1:
            status = "PASS_MAPPING_NOT_REQUIRED_CONTEXT_ROW"
        elif has_mapping:
            status = "PASS_MAPPING_PRESENT"
        else:
            status = "BLOCKED_MAPPING_MISSING"
        out.append(
            {
                "task_id": TASK_ID,
                "row_id": f"stage5-row-{idx:04d}",
                "provider": provider,
                "source_key": row.get("source_key", ""),
                "title_present": int(bool(row.get("title") or row.get("headline"))),
                "source_url_present": int(bool(row.get("source_url") or row.get("url") or row.get("canonical_url"))),
                "ticker_mapping_required": ticker_required,
                "macro_context_candidate": macro_context,
                "mapping_status": status,
                "raw_path": row.get("_raw_path", ""),
            }
        )
    return out


def source_time_audit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        empty = int(row.get("_empty_provider_response", 0) or 0)
        published = str(row.get("published_at") or row.get("publication_time") or row.get("event_time") or "")
        certified = int(row.get("source_time_certified_flag", 0) or 0)
        status = "NO_ROWS_TO_CERTIFY" if empty else "PASS_SOURCE_TIME_CERTIFIED" if published and certified else "BLOCKED_SOURCE_TIME_UNCERTIFIED"
        out.append(
            {
                "task_id": TASK_ID,
                "row_id": f"stage5-row-{idx:04d}",
                "provider": row.get("provider", ""),
                "published_at": published,
                "source_time_certified_flag": certified,
                "available_to_brain_ts_basis": "capture_time_only_until_stage6_admission",
                "source_time_status": status,
                "raw_path": row.get("_raw_path", ""),
            }
        )
    return out


def coverage_audit(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stage5_summary = read_json(STAGE5_REPORT_DIR / "stage5_background_backfill_summary.json")
    providers = sorted({str(row.get("provider", "")) for row in rows if row.get("provider")})
    return [
        {
            "task_id": TASK_ID,
            "coverage_scope": "stage5_bounded_2016_baseline",
            "providers_observed": "|".join(providers),
            "headline_rows_observed": sum(1 for row in rows if not row.get("_empty_provider_response")),
            "empty_provider_response_rows": sum(1 for row in rows if row.get("_empty_provider_response")),
            "full_2016_to_present_run_completed": int(stage5_summary.get("full_2016_to_present_run_completed", 0) or 0),
            "coverage_status": "BLOCKED_FULL_2016_TO_PRESENT_NOT_COMPLETE",
        }
    ]


def handoff_decision(mapping_rows: list[dict[str, Any]], source_time_rows: list[dict[str, Any]], raw_rows: list[dict[str, Any]], coverage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = []
    if any(row.get("mapping_status", "").startswith("BLOCKED") for row in mapping_rows):
        blockers.append("mapping_blocker")
    if any(row.get("source_time_status", "").startswith("BLOCKED") for row in source_time_rows):
        blockers.append("source_time_blocker")
    if any(str(row.get("hash_match")) != "1" or str(row.get("secret_scan_pass")) != "1" for row in raw_rows):
        blockers.append("raw_integrity_or_secret_blocker")
    if any(row.get("coverage_status") != "PASS" for row in coverage_rows):
        blockers.append("coverage_blocker")
    return [
        {
            "task_id": TASK_ID,
            "l2_handoff_decision": "BLOCKED",
            "blockers": "|".join(blockers),
            "strict_gate_rows": 0,
            "proxy_feature_rows_allowed": 0,
            "missing_source_is_negative": 0,
            "assignment_uses_future_outcome": 0,
            "outcome_used_for_assignment": 0,
            "decision_note": "Stage 5 bounded proof has raw evidence, but full 2016-to-present coverage and L2 admission gates are not satisfied.",
        }
    ]


def run(report_dir: Path) -> dict[str, Any]:
    report_dir.mkdir(parents=True, exist_ok=True)
    rows = headline_rows()
    raw_rows = raw_hash_audit()
    mapping_rows = mapping_audit(rows)
    source_time_rows = source_time_audit(rows)
    coverage_rows = coverage_audit(rows)
    handoff_rows = handoff_decision(mapping_rows, source_time_rows, raw_rows, coverage_rows)
    write_csv(report_dir / "task_4124_raw_hash_audit.csv", raw_rows)
    write_csv(report_dir / "task_4124_mapping_audit.csv", mapping_rows)
    write_csv(report_dir / "task_4124_source_time_audit.csv", source_time_rows)
    write_csv(report_dir / "task_4124_coverage_audit.csv", coverage_rows)
    write_csv(report_dir / "task_4124_l2_handoff_decision.csv", handoff_rows)
    summary = {
        "task_id": TASK_ID,
        "stage6_status": "L1_QUALITY_COVERAGE_AUDIT_COMPLETE_L2_HANDOFF_BLOCKED",
        "headline_audit_rows": len(rows),
        "raw_hash_rows": len(raw_rows),
        "mapping_blocker_count": sum(1 for row in mapping_rows if row.get("mapping_status", "").startswith("BLOCKED")),
        "source_time_blocker_count": sum(1 for row in source_time_rows if row.get("source_time_status", "").startswith("BLOCKED")),
        "raw_integrity_failure_count": sum(1 for row in raw_rows if str(row.get("hash_match")) != "1" or str(row.get("secret_scan_pass")) != "1"),
        "l2_handoff_decision": handoff_rows[0]["l2_handoff_decision"],
        "strict_gate_rows": 0,
        "proxy_feature_rows_allowed": 0,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_json(report_dir / "stage6_l1_quality_coverage_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit L0 Stage 6 L1 quality/coverage and L2 handoff decision.")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()
    summary = run(args.report_dir)
    print(
        "[L0_STAGE6_L1_AUDIT] "
        f"status={summary['stage6_status']} l2_handoff={summary['l2_handoff_decision']} "
        f"mapping_blockers={summary['mapping_blocker_count']} source_time_blockers={summary['source_time_blocker_count']} "
        "strict_gate_rows=0 proxy_feature_rows_allowed=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
