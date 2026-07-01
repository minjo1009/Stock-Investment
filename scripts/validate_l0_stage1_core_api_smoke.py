from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs/reports/task_4118_l0_stage_1_official_core_api_smoke_stabilization"
SUMMARY_PATH = REPORT_DIR / "stage1_smoke_summary.json"
REQUIRED_CSVS = [
    "task_4118_scope_freeze.csv",
    "task_4118_source_family_plan.csv",
    "task_4118_api_or_raw_call_ledger.csv",
    "task_4118_raw_response_classification.csv",
    "task_4118_normalized_source_packets.csv",
    "task_4118_decision_asof_coverage.csv",
    "task_4118_feature_admission_gate.csv",
    "task_4118_source_gap_ledger.csv",
    "task_4118_materialization_audit.csv",
]
REQUIRED_FAMILIES = {
    "official_public_releases",
    "gdelt_news_events",
    "marketaux_news_free",
    "microstructure_quotes_trades",
}
SECRET_PATTERN = re.compile(
    r"(api[_-]?key|apikey|token|authorization|secret)\s*[:=]\s*[A-Za-z0-9_\-]{12,}",
    flags=re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    if not SUMMARY_PATH.exists():
        return [f"missing summary: {SUMMARY_PATH.relative_to(ROOT)}"]
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8-sig"))
    if summary.get("stage1_status") != "PREFLIGHT_PASS_NETWORK_SMOKE_PENDING":
        errors.append(f"unexpected stage1 status: {summary.get('stage1_status')}")
    if int(summary.get("network_calls_made", -1)) != 0:
        errors.append("stage1 preflight must not make network calls")
    if int(summary.get("fail_count", -1)) != 0:
        errors.append("stage1 preflight fail_count must be 0")
    if summary.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy status changed")
    if summary.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment status changed")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital status changed")

    for name in REQUIRED_CSVS:
        path = REPORT_DIR / name
        if not path.exists():
            errors.append(f"missing required csv: {path.relative_to(ROOT)}")
        elif path.stat().st_size <= 0:
            errors.append(f"empty required csv: {path.relative_to(ROOT)}")

    ledger_path = REPORT_DIR / "task_4118_api_or_raw_call_ledger.csv"
    if ledger_path.exists():
        ledger = read_csv(ledger_path)
        families = {row.get("source_family", "") for row in ledger}
        missing = REQUIRED_FAMILIES - families
        if missing:
            errors.append(f"ledger missing families: {sorted(missing)}")
        for row in ledger:
            if row.get("network_call_made") not in {"0", 0}:
                errors.append(f"network call recorded in preflight ledger: {row}")
            if row.get("broker_mutation_permitted_flag") not in {"0", 0}:
                errors.append(f"broker mutation flag opened: {row}")
            if row.get("real_capital_permitted_flag") not in {"0", 0}:
                errors.append(f"real capital flag opened: {row}")

    packets_path = REPORT_DIR / "task_4118_normalized_source_packets.csv"
    if packets_path.exists():
        packets = read_csv(packets_path)
        for row in packets:
            if row.get("missing_source_is_negative") not in {"0", 0}:
                errors.append(f"missing source used as negative: {row.get('source_packet_id')}")
            if row.get("assignment_uses_future_outcome") not in {"0", 0}:
                errors.append(f"future outcome assignment opened: {row.get('source_packet_id')}")
            if row.get("outcome_used_for_assignment") not in {"0", 0}:
                errors.append(f"outcome assignment opened: {row.get('source_packet_id')}")
            if row.get("strict_gate_pass") not in {"0", 0}:
                errors.append(f"strict gate opened during preflight: {row.get('source_packet_id')}")

    for path in [SUMMARY_PATH, *[REPORT_DIR / name for name in REQUIRED_CSVS]]:
        if path.exists():
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
            if SECRET_PATTERN.search(text):
                errors.append(f"secret-like value detected in artifact: {path.relative_to(ROOT)}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_STAGE1_CORE_API_SMOKE_ERROR] {error}")
        return 1
    print("[L0_STAGE1_CORE_API_SMOKE_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
