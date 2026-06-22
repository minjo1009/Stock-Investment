from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2541_2560_sec_financing_dilution_acquisition"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def as_float(value: object) -> float:
    try:
        if value in {"", None, "nan"}:
            return 0.0
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return 0.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def assert_no_leak(rows: list[dict[str, str]], name: str) -> None:
    require(rows, f"{name} empty")
    forbidden_names = ["apikey", "api_key", "token", "authorization", "bearer"]
    forbidden_values = ["d826f6", "d8oktf", "UPwwRz", "7RU6"]
    for idx, row in enumerate(rows, start=1):
        blob = " ".join(str(value) for value in row.values())
        lower_blob = blob.lower()
        require(row.get("missing_source_is_negative", "0") == "0", f"{name} row {idx} treats missing source as negative")
        require(row.get("assignment_uses_future_outcome", "0") == "0", f"{name} row {idx} uses future outcome")
        require(row.get("outcome_used_for_assignment", "0") == "0", f"{name} row {idx} uses outcome for assignment")
        for forbidden in forbidden_names:
            require(forbidden not in lower_blob, f"{name} row {idx} leaks request credential field")
        for token in forbidden_values:
            require(token not in blob, f"{name} row {idx} leaks secret-like token")


def assert_status(rows: list[dict[str, str]], name: str) -> None:
    for idx, row in enumerate(rows, start=1):
        if "strategy_acceptance" in row:
            require(row["strategy_acceptance"] == "NOT_ACCEPTED", f"{name} row {idx} changed strategy status")
        if "deployment_readiness" in row:
            require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", f"{name} row {idx} changed deployment status")
        if "real_capital" in row:
            require(row["real_capital"] == "FORBIDDEN", f"{name} row {idx} permits real capital")


def main() -> None:
    report = REPORT_DIR / "task_2541_2560_sec_financing_dilution_acquisition.md"
    decision = REPORT_DIR / "task_2560_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    scope = read_csv(OUT_DIR / "task2541_scope_freeze.csv")
    families = read_csv(OUT_DIR / "task2542_source_family_plan.csv")
    cik_map = read_csv(OUT_DIR / "task2542_cik_map.csv")
    calls = read_csv(OUT_DIR / "task2543_api_or_raw_call_ledger.csv")
    raw = read_csv(OUT_DIR / "task2544_raw_response_classification.csv")
    packets = read_csv(OUT_DIR / "task2545_normalized_sec_financing_dilution_packets.csv")
    coverage = read_csv(OUT_DIR / "task2546_decision_asof_coverage.csv")
    gates = read_csv(OUT_DIR / "task2547_feature_admission_gate.csv")
    gaps = read_csv(OUT_DIR / "task2548_source_gap_ledger.csv")
    summary = read_csv(OUT_DIR / "task2549_event_summary.csv")
    subagents = read_csv(OUT_DIR / "task2550_subagent_packets.csv")
    closeout = read_csv(OUT_DIR / "task2560_closeout.csv")
    decision_rows = read_csv(decision)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("scope", scope),
        ("families", families),
        ("cik_map", cik_map),
        ("calls", calls),
        ("raw", raw),
        ("packets", packets),
        ("coverage", coverage),
        ("gates", gates),
        ("gaps", gaps),
        ("summary", summary),
        ("subagents", subagents),
        ("closeout", closeout),
    ]:
        assert_no_leak(rows, name)
    for name, rows in [("scope", scope), ("closeout", closeout)]:
        assert_status(rows, name)

    require(len(scope) == 1, "scope row mismatch")
    s = scope[0]
    require(int(s["universe_rows"]) == 3100, "universe rows mismatch")
    require(int(s["unique_symbols"]) == 283, "unique symbol count mismatch")
    require(s["download_or_api_call_run"] == "1", "download flag should be 1")
    require(s["backtest_run"] == "0", "backtest should not run")
    require(s["selector_changed"] == "0", "selector should not change")

    require(len(families) == 1, "source family row mismatch")
    require(families[0]["source_family"] == "sec_financing_dilution", "bad source family")
    require(len(cik_map) == 283, "CIK map should cover unique symbols")
    mapped = [row for row in cik_map if row["cik"]]
    missing = [row for row in cik_map if not row["cik"]]
    require(len(mapped) == 282, f"expected 282 mapped symbols, got {len(mapped)}")
    require(len(missing) == 1 and missing[0]["symbol"] == "ACLX", "expected only ACLX CIK mapping gap")

    require(len(calls) >= 6000, "raw call ledger too small")
    require(len(raw) == len(calls), "raw classification/call count mismatch")
    require(all(row["api_secret_written"] == "0" for row in calls), "API secret flag found")
    require(all(row["classification"] == "usable" for row in raw), "all completed raw rows should be usable")

    # Hash check every unique raw file referenced by raw classification.
    checked: set[str] = set()
    for row in raw:
        rel = row["raw_path"]
        if not rel or rel in checked:
            continue
        path = ROOT / rel
        require(path.exists(), f"missing raw path {rel}")
        require(sha256_file(path) == row["raw_sha256"], f"raw hash mismatch {rel}")
        checked.add(rel)

    require(len(packets) > 100000, "SEC financing/dilution packet count too small")
    packet_ids = {row["source_packet_id"] for row in packets}
    require(len(packet_ids) == len(packets), "duplicate source packet ids")
    require(any(row["event_family"] == "unregistered_equity_issuance" for row in packets), "missing 8-K 3.02 event family")
    require(any(row["event_family"] == "listing_survival_risk" for row in packets), "missing 8-K 3.01 event family")
    require(any(row["event_family"] == "private_financing_form_d" for row in packets), "missing Form D event family")
    require(any(row["event_family"] == "registered_capacity_or_status" for row in packets), "missing registered capacity event family")
    require(any(row["event_family"] == "prospectus_supplement" for row in packets), "missing prospectus supplement event family")
    for idx, row in enumerate(packets[:1000], start=1):
        source_ts = parse_ts(row["source_ts"])
        available = parse_ts(row["available_to_brain_ts"])
        require(source_ts is not None, f"packet row {idx} missing source_ts")
        require(available is not None, f"packet row {idx} missing available_to_brain_ts")
        require(row["source_time_certified"] == "1", f"packet row {idx} source time not certified")
        if row["primary_document_download_target"] == "1":
            require(row["primary_document_raw_path"], f"packet row {idx} primary doc target missing raw path")
            require(row["primary_document_raw_sha256"], f"packet row {idx} primary doc target missing hash")
            require((ROOT / row["primary_document_raw_path"]).exists(), f"packet row {idx} primary doc missing")
            require(row["strict_gate_pass"] == "1", f"packet row {idx} primary doc target not strict")

    require(len(coverage) == 62, "decision asof coverage row mismatch")
    require(all(as_float(row["cik_mapping_coverage_ratio"]) >= 0.98 for row in coverage), "bad CIK mapping coverage")
    require(
        sum(int(row["candidate_rows"]) - int(row["mapped_cik_rows"]) for row in coverage) == 6,
        "coverage gap should equal six ACLX candidate rows",
    )
    require(len(gates) == 3100, "feature gate row mismatch")
    require(sum(1 for row in gates if row["strict_gate_pass"] == "1") == 3094, "strict feature row count mismatch")
    require(sum(1 for row in gates if row["admission_state"] == "blocked") == 6, "blocked feature row count mismatch")
    require(all(row["can_score_assignment"] == row["strict_gate_pass"] for row in gates), "strict scoring mismatch")
    require(len(gaps) == 1, "source gap count mismatch")
    require(gaps[0]["symbol"] == "ACLX" and gaps[0]["gap_reason"] == "missing_exact_sec_cik_mapping", "unexpected source gap")
    require(any(row["summary_type"] == "event_severity" and row["bucket"] == "high" for row in summary), "missing high severity summary")
    require(len(subagents) == 3, "subagent row count mismatch")
    require(all(row["write_scope"] == "read-only" for row in subagents), "subagents should be read-only")

    require(closeout == decision_rows, "decision and closeout mismatch")
    co = closeout[0]
    require(co["verdict"] == "sec_financing_dilution_full_universe_acquisition_complete", "bad closeout verdict")
    require(int(co["financing_dilution_event_rows"]) == len(packets), "closeout packet count mismatch")
    require(int(co["downloaded_primary_document_rows"]) >= 5000, "primary doc download count too small")
    require(co["backtest_run"] == "0", "closeout should not run backtest")
    require(co["selector_changed"] == "0", "closeout should not change selector")
    require(len(manifest) >= 12, "manifest too small")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2541, 2561)), "registry missing Task2541-2560 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("124. Task2541-Task2560" in op_state, "operating state missing Task2541-2560 line")

    print("[TASK2541_2560_SEC_FINANCING_DILUTION_ACQUISITION_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
