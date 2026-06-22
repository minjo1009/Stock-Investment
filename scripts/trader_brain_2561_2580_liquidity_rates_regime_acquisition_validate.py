from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2561_2580_liquidity_rates_regime_acquisition"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    require(path.exists(), f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def iter_csv(path: Path):
    require(path.exists(), f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


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


def assert_no_secret_blob(blob: str, context: str) -> None:
    lower = blob.lower()
    for token in ["d826f6", "d8oktf", "UPwwRz", "7RU6", "bearer ", "authorization:"]:
        require(token.lower() not in lower, f"{context} leaks secret-like token")
    if "api_key=" in lower or "apikey=" in lower:
        require("%3credacted%3e" in lower or "<redacted>" in lower, f"{context} has unredacted api key param")


def assert_invariant_flags(row: dict[str, str], context: str) -> None:
    require(row.get("missing_source_is_negative", "0") == "0", f"{context} treats missing source as negative")
    require(row.get("assignment_uses_future_outcome", "0") == "0", f"{context} uses future outcome")
    require(row.get("outcome_used_for_assignment", "0") == "0", f"{context} uses outcome for assignment")


def assert_status(rows: list[dict[str, str]], name: str) -> None:
    for idx, row in enumerate(rows, start=1):
        if "strategy_acceptance" in row:
            require(row["strategy_acceptance"] == "NOT_ACCEPTED", f"{name} row {idx} changed strategy status")
        if "deployment_readiness" in row:
            require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", f"{name} row {idx} changed deployment status")
        if "real_capital" in row:
            require(row["real_capital"] == "FORBIDDEN", f"{name} row {idx} permits real capital")


def main() -> None:
    report = REPORT_DIR / "task_2561_2580_liquidity_rates_regime_acquisition.md"
    decision = REPORT_DIR / "task_2580_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    scope = read_csv(OUT_DIR / "task2561_scope_freeze.csv")
    families = read_csv(OUT_DIR / "task2562_source_family_plan.csv")
    calls = read_csv(OUT_DIR / "task2563_api_or_raw_call_ledger.csv")
    raw = read_csv(OUT_DIR / "task2564_raw_response_classification.csv")
    coverage = read_csv(OUT_DIR / "task2566_decision_asof_coverage.csv")
    gates = read_csv(OUT_DIR / "task2567_feature_admission_gate.csv")
    gaps = read_csv(OUT_DIR / "task2568_source_gap_ledger.csv")
    summary = read_csv(OUT_DIR / "task2569_packet_summary.csv")
    subagents = read_csv(OUT_DIR / "task2570_subagent_packets.csv")
    closeout = read_csv(OUT_DIR / "task2580_closeout.csv")
    decision_rows = read_csv(decision)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("scope", scope),
        ("families", families),
        ("calls", calls),
        ("raw", raw),
        ("coverage", coverage),
        ("gates", gates),
        ("gaps", gaps),
        ("summary", summary),
        ("subagents", subagents),
        ("closeout", closeout),
    ]:
        require(rows or name == "gaps", f"{name} unexpectedly empty")
        for idx, row in enumerate(rows, start=1):
            assert_invariant_flags(row, f"{name} row {idx}")
            assert_no_secret_blob(" ".join(str(value) for value in row.values()), f"{name} row {idx}")

    assert_no_secret_blob(report.read_text(encoding="utf-8"), "report")
    assert_status(scope, "scope")
    assert_status(closeout, "closeout")

    require(len(scope) == 1, "scope row mismatch")
    s = scope[0]
    require(int(s["universe_rows"]) == 3100, "universe rows mismatch")
    require(int(s["unique_decision_dates"]) == 62, "decision date count mismatch")
    require(s["date_window_start"] == "2021-01-01", "bad date window start")
    require(s["date_window_end"] == "2026-03-31", "bad date window end")
    require(s["fred_key_present"] == "1", "FRED key should be present")
    require(s["download_or_api_call_run"] == "1", "download flag should be 1")
    require(s["backtest_run"] == "0", "backtest should not run")
    require(s["selector_changed"] == "0", "selector should not change")

    require({row["provider"] for row in families} == {"NYFED", "TREASURY", "FRED_ALFRED"}, "source family provider mismatch")
    require(len(calls) == 49, "raw call count mismatch")
    require(len(raw) == 49, "raw classification count mismatch")
    require(all(row["api_secret_written"] == "0" for row in calls), "api secret flag found")
    for row in calls:
        url = row["request_url_no_secret"]
        if row["provider"] == "FRED_ALFRED":
            require("%3CREDACTED%3E" in url or "<REDACTED>" in url, "FRED URL not redacted")

    require(all(row["classification"] in {"usable", "empty"} for row in raw), "raw classifications should have no blocked rows")
    require(sum(1 for row in raw if row["classification"] == "usable") == 47, "usable raw count mismatch")
    require(sum(1 for row in raw if row["classification"] == "empty") == 2, "empty raw count mismatch")
    require(sum(1 for row in raw if row["provider"] == "NYFED") == 5, "NY Fed endpoint count mismatch")
    require(sum(1 for row in raw if row["provider"] == "TREASURY") == 4, "Treasury endpoint count mismatch")
    require(sum(1 for row in raw if row["provider"] == "FRED_ALFRED") == 40, "FRED endpoint count mismatch")

    checked: set[str] = set()
    for row in raw:
        rel = row["raw_path"]
        path = ROOT / rel
        require(path.exists(), f"missing raw path {rel}")
        require(sha256_file(path) == row["raw_sha256"], f"raw hash mismatch {rel}")
        checked.add(rel)
        if row["provider"] == "TREASURY":
            payload = json.loads(path.read_text(encoding="utf-8"))
            require(payload.get("compiled_full_pagination") == 1, f"Treasury raw is not paginated full compile: {rel}")

    treasury = {row["endpoint"]: int(row["row_count"]) for row in raw if row["provider"] == "TREASURY"}
    require(treasury["treasury_operating_cash_balance"] == 4931, "Treasury operating cash row count mismatch")
    require(treasury["treasury_deposits_withdrawals_operating_cash"] == 226824, "Treasury deposits/withdrawals row count mismatch")
    require(treasury["treasury_debt_to_penny"] == 1314, "Treasury debt row count mismatch")
    require(treasury["treasury_avg_interest_rates"] == 1071, "Treasury avg interest row count mismatch")

    packet_path = OUT_DIR / "task2565_normalized_liquidity_rates_packets.csv"
    packet_rows = 0
    strict_rows = 0
    proxy_rows = 0
    providers: set[str] = set()
    endpoint_counts: dict[str, int] = {}
    for idx, row in enumerate(iter_csv(packet_path), start=1):
        packet_rows += 1
        assert_invariant_flags(row, f"packet row {idx}")
        if idx <= 5000:
            assert_no_secret_blob(" ".join(str(value) for value in row.values()), f"packet row {idx}")
        providers.add(row["provider"])
        endpoint_counts[row["endpoint_or_source_family"]] = endpoint_counts.get(row["endpoint_or_source_family"], 0) + 1
        source_ts = parse_ts(row["source_ts"])
        available_ts = parse_ts(row["available_to_brain_ts"])
        require(source_ts is not None, f"packet row {idx} missing source_ts")
        require(available_ts is not None, f"packet row {idx} missing available_to_brain_ts")
        if row["strict_gate_pass"] == "1":
            strict_rows += 1
            require(row["source_time_certified"] == "1", f"packet row {idx} strict without certified time")
            require(row["proxy_feature_allowed"] == "0", f"packet row {idx} strict also proxy")
        else:
            proxy_rows += 1
            require(row["proxy_feature_allowed"] == "1", f"packet row {idx} non-strict not marked proxy")
        if row["endpoint_or_source_family"] == "treasury_avg_interest_rates":
            require(row["strict_gate_pass"] == "0", "Treasury avg interest rates should be proxy-only")

    require(packet_rows == 768841, f"packet count mismatch: {packet_rows}")
    require(strict_rows == 767770, f"strict packet count mismatch: {strict_rows}")
    require(proxy_rows == 1071, f"proxy packet count mismatch: {proxy_rows}")
    require(providers == {"NYFED", "TREASURY", "FRED_ALFRED"}, "packet provider mismatch")
    require(endpoint_counts.get("nyfed_repo_operations", 0) == 2844, "NY Fed repo packet count mismatch")
    require(endpoint_counts.get("treasury_deposits_withdrawals_operating_cash", 0) == 680472, "Treasury deposits packet count mismatch")

    require(len(coverage) == 62, "coverage row count mismatch")
    require(all(int(row["strict_available_packet_rows"]) > 0 for row in coverage), "all decisions should have strict packet coverage")
    require(all(row["strict_coverage_available"] == "1" for row in coverage), "all decisions should have strict coverage")
    require(len(gates) == 3100, "feature gate row count mismatch")
    require(sum(1 for row in gates if row["strict_gate_pass"] == "1") == 3100, "strict feature gate count mismatch")
    require(all(row["can_score_assignment"] == "1" for row in gates), "feature gate assignment flag mismatch")
    require(len(gaps) == 0, "source gaps should be zero")

    summary_by_provider = {row["bucket"]: int(row["row_count"]) for row in summary if row["summary_type"] == "provider"}
    require(summary_by_provider == {"FRED_ALFRED": 45068, "NYFED": 18564, "TREASURY": 705209}, "provider packet summary mismatch")
    require(len(subagents) == 3, "subagent packet row count mismatch")
    require(all(row["write_scope"] == "read-only" for row in subagents), "subagents should be read-only")
    require(closeout == decision_rows, "decision and closeout mismatch")
    co = closeout[0]
    require(co["verdict"] == "liquidity_rates_regime_acquisition_complete", "bad closeout verdict")
    require(int(co["raw_response_rows"]) == 49, "closeout raw count mismatch")
    require(int(co["normalized_packet_rows"]) == packet_rows, "closeout packet count mismatch")
    require(int(co["strict_packet_rows"]) == strict_rows, "closeout strict packet count mismatch")
    require(co["source_gap_rows"] == "0", "closeout source gap mismatch")
    require(co["backtest_run"] == "0", "closeout should not run backtest")
    require(co["selector_changed"] == "0", "closeout should not change selector")
    require(len(manifest) >= 10, "manifest too small")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2561, 2581)), "registry missing Task2561-2580 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("125. Task2561-Task2580" in op_state, "operating state missing Task2561-2580 line")

    print("[TASK2561_2580_LIQUIDITY_RATES_REGIME_ACQUISITION_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
