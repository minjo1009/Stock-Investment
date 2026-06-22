from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2251_2280_plus8000_full_source_acquisition"
RAW_DIR = ROOT / "data/raw/task_2251_2280_plus8000_full_source_acquisition"
REPORT = ROOT / "docs/reports/task_2251_2280_plus8000_full_source_acquisition/task_2251_2280_plus8000_full_source_acquisition.md"
DECISION = ROOT / "docs/reports/task_2251_2280_plus8000_full_source_acquisition/task_2251_2280_decision.csv"
AUTHORITY = "PLUS8000_FULL_SOURCE_ACQUISITION_RAW_AND_FEATURE_PARITY_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def iter_csv(path: Path):
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_rows(rows: list[dict[str, str]], context: str) -> None:
    for row in rows:
        if "authority" in row:
            require(row["authority"] == AUTHORITY, f"{context} authority mismatch")
        if "assignment_uses_future_outcome" in row:
            require(row["assignment_uses_future_outcome"] == "0", f"{context} future assignment")
        if "outcome_used_for_assignment" in row:
            require(row["outcome_used_for_assignment"] == "0", f"{context} outcome assignment")
        if "missing_source_is_negative" in row:
            require(row["missing_source_is_negative"] == "0", f"{context} missing source negative")


def validate_stream_rows(path: Path, context: str) -> tuple[int, int]:
    count = 0
    parsed_checked = 0
    for row in iter_csv(path):
        count += 1
        validate_rows([row], context)
        if "record_json" in row and (count <= 1000 or count % 50000 == 0):
            try:
                json.loads(row.get("record_json", "") or "{}")
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{context} record_json parse failed at row {count}: {exc}") from exc
            parsed_checked += 1
    return count, parsed_checked


def secret_values() -> list[str]:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return []
    values: list[str] = []
    for line in env_path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        if key.strip() in {"FINNHUB_API_KEY", "FMP_API_KEY", "ALPHA_VANTAGE_API_KEY", "FRED_API_KEY"}:
            value = value.strip().strip('"').strip("'")
            if value:
                values.append(value)
    return values


def secret_scan(paths: list[Path]) -> None:
    secrets = [value.encode("utf-8") for value in secret_values()]
    if not secrets:
        return
    for root in paths:
        if not root.exists():
            continue
        files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
        for path in files:
            with path.open("rb") as handle:
                tail = b""
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    block = tail + chunk
                    for secret in secrets:
                        require(secret not in block, f"secret leaked in {path}")
                    tail = block[-128:]


def main() -> None:
    plan = read_csv(OUT_DIR / "task2251_acquisition_plan.csv")
    ledger = read_csv(OUT_DIR / "task2252_api_call_ledger.csv")
    normalized_path = OUT_DIR / "task2253_normalized_sources.csv"
    normalized_count, parsed_checked = validate_stream_rows(normalized_path, "normalized")
    index_summary = read_csv(OUT_DIR / "task2254_combined_source_index_summary.csv")
    coverage = read_csv(OUT_DIR / "task2255_post_acquisition_coverage_summary.csv")
    features = read_csv(OUT_DIR / "task2256_recomputed_plus8000_feature_panel.csv")
    retry = read_csv(OUT_DIR / "task2257_retry_or_blocked_queue.csv")
    closeout = read_csv(OUT_DIR / "task2280_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(RAW_DIR.exists(), "missing raw source directory")
    require(len(plan) > 0, "empty acquisition plan")
    require(len(ledger) >= len(plan), "ledger shorter than plan")
    require(normalized_count > 0, "no normalized sources")
    require(parsed_checked > 0, "normalized parseability was not checked")
    require(len(index_summary) == 1, "missing index summary")
    require(len(coverage) > 0, "missing coverage summary")
    require(len(features) == 3100, "feature panel not full candidate pool")
    require(len(closeout) == 1, "expected one closeout")
    require(closeout == decision, "decision differs from closeout")
    require(len(manifest) >= 8, "manifest incomplete")

    validate_rows(plan, "plan")
    validate_rows(ledger, "ledger")
    validate_rows(coverage, "coverage")
    validate_rows(features, "features")
    validate_rows(retry, "retry")
    validate_rows(closeout, "closeout")

    require(all(row["request_url_contains_secret"] == "0" for row in ledger), "secret URL flag violated")
    require(any(row["provider"] == "sec" and row["endpoint_name"] == "companyfacts" for row in ledger), "SEC fallback was not attempted")
    require(int(index_summary[0]["new_normalized_rows"]) == normalized_count, "normalized count mismatch")
    require(int(closeout[0]["feature_rows"]) == 3100, "closeout feature count mismatch")
    require(closeout[0]["replay_allowed"] == "0", "acquisition task should not authorize replay")
    require(closeout[0]["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
    require(closeout[0]["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
    require(closeout[0]["real_capital"] == "FORBIDDEN", "real capital changed")
    secret_scan([OUT_DIR, REPORT, RAW_DIR])

    print("[TASK2251_2280_VALIDATE_OK] acquisition=pass feature_panel=pass secret_scan=pass")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
