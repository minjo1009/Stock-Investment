from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1961_1970_free_source_acquisition"
RAW_DIR = ROOT / "data/raw/task_1961_1970_free_source_acquisition"
REPORT = ROOT / "docs/reports/task_1961_1970_free_source_acquisition/task_1961_1970_free_source_acquisition.md"
DECISION = ROOT / "docs/reports/task_1961_1970_free_source_acquisition/task_1961_1970_decision.csv"
AUTHORITY = "DIAGNOSTIC_FREE_SOURCE_ACQUISITION_ONLY"

REQUIRED_COUNTS = {
    "task1961_free_source_scope_manifest.csv": 73,
    "task1962_alfred_fred_acquisition_ledger.csv": 8,
    "task1963_price_free_source_download_manifest.csv": 146,
    "task1964_price_free_source_coverage.csv": 73,
    "task1965_sec_guidance_expanded_receipt_ledger.csv": 8105,
    "task1966_analyst_free_source_gate.csv": 1,
    "task1967_free_source_readiness_summary.csv": 5,
    "task1970_acceptance_gate.csv": 1,
    "task1970_closeout.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name in REQUIRED_COUNTS:
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not (RAW_DIR / "artifact_manifest.csv").exists(), "missing raw artifact manifest")
    fail_if(not (RAW_DIR / "yahoo_chart_daily_normalized.csv").exists(), "missing normalized Yahoo file")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")
    fail_if(not (OUT_DIR / "task1970_closeout.json").exists(), "missing closeout json")


def validate_counts_and_authority() -> None:
    for name, expected in REQUIRED_COUNTS.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} got {len(rows)}")
    for path in OUT_DIR.glob("*.csv"):
        if path.name == "artifact_manifest.csv":
            continue
        for idx, row in enumerate(read_csv(path), start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{path.name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{path.name}:{idx} future outcome assignment")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{path.name}:{idx} outcome assignment")


def validate_price_sources() -> None:
    coverage = read_csv(OUT_DIR / "task1964_price_free_source_coverage.csv")
    fail_if(any(row["download_state"] != "downloaded_json_normalized" for row in coverage), "not all scoped Yahoo price files downloaded")
    fail_if(any(row["acceptance_ready"] != "0" for row in coverage), "free price cross-check cannot be acceptance-ready")
    for idx, row in enumerate(coverage, start=2):
        fail_if(not row["raw_path"] or not row["raw_sha256"], f"missing raw path/hash at price row {idx}")
        fail_if(not (ROOT / row["raw_path"]).exists(), f"missing raw price file at row {idx}")
    manifest = read_csv(OUT_DIR / "task1963_price_free_source_download_manifest.csv")
    stooq = [row for row in manifest if row["source"] == "stooq_daily_csv"]
    yahoo = [row for row in manifest if row["source"] == "yahoo_chart_daily_public"]
    fail_if(len(stooq) != 73 or len(yahoo) != 73, "price source split mismatch")
    fail_if(any(row["source_grade"] != "free_public_attempt_not_acceptance_receipt" for row in stooq), "Stooq source grade overclaim")
    fail_if(any(row["source_grade"] != "free_public_crosscheck_not_original_asof_receipt" for row in yahoo), "Yahoo source grade overclaim")


def validate_sec_alfred_analyst_gates() -> None:
    sec = read_csv(OUT_DIR / "task1965_sec_guidance_expanded_receipt_ledger.csv")
    fail_if(not any(row["guidance_receipt_state"] == "issuer_public_guidance_hit_asof" for row in sec), "SEC guidance hit missing")
    fail_if(any(row["inferred_matching_used"] != "0" for row in sec), "SEC inferred matching used")
    for idx, row in enumerate(sec, start=2):
        fail_if(row["join_key_rule"] != "exact_existing_trade_spec_id_cik_accession_only", f"bad SEC join rule at row {idx}")
        fail_if(row["asof_guard_pass"] != "1", f"SEC asof guard failed at row {idx}")
        fail_if(not row["cik"] or not row["accession"] or not row["sha256"], f"missing SEC identity/hash at row {idx}")
    alfred = read_csv(OUT_DIR / "task1962_alfred_fred_acquisition_ledger.csv")
    if not any(row["download_status"] == "downloaded" for row in alfred):
        fail_if(any(row["alfred_vintage_certified"] != "0" for row in alfred), "ALFRED certified without downloaded vintage")
        fail_if(any("FRED_API_KEY" not in row["download_status"] for row in alfred), "ALFRED block reason not explicit")
    analyst = read_csv(OUT_DIR / "task1966_analyst_free_source_gate.csv")
    fail_if(any(row["pit_consensus_revision_certified"] != "0" for row in analyst), "analyst PIT consensus incorrectly certified")


def validate_closeout_and_report() -> None:
    closeout = read_csv(OUT_DIR / "task1970_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "strategy acceptance changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital changed")
    payload = json.loads((OUT_DIR / "task1970_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["verdict"] != "free_source_acquisition_complete_diagnostic_only", "json verdict mismatch")
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Free Source Acquisition",
        "Yahoo daily chart",
        "Stooq",
        "ALFRED",
        "Analyst revision",
        "real-capital",
    ]:
        fail_if(phrase not in text, f"report missing phrase {phrase}")


def main() -> None:
    try:
        validate_files()
        validate_counts_and_authority()
        validate_price_sources()
        validate_sec_alfred_analyst_gates()
        validate_closeout_and_report()
    except AssertionError as exc:
        print(f"[TASK1961_1970_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1961_1970_VALIDATE_OK] free source acquisition artifacts are valid")


if __name__ == "__main__":
    main()
