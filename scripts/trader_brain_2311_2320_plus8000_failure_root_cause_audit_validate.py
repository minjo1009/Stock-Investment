from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2311_2320_plus8000_failure_root_cause_audit"
REPORT = ROOT / "docs/reports/task_2311_2320_plus8000_failure_root_cause_audit/task_2311_2320_plus8000_failure_root_cause_audit.md"
DECISION = ROOT / "docs/reports/task_2311_2320_plus8000_failure_root_cause_audit/task_2311_2320_decision.csv"
AUTHORITY = "DIAGNOSTIC_PLUS8000_FAILURE_ROOT_CAUSE_AUDIT_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_authority(rows: list[dict[str, str]], context: str) -> None:
    for row in rows:
        if "authority" in row:
            require(row["authority"] == AUTHORITY, f"{context} authority mismatch")


def main() -> None:
    lineage = read_csv(OUT_DIR / "task2311_experiment_metric_lineage.csv")
    overlap = read_csv(OUT_DIR / "task2312_trade_overlap_matrix.csv")
    bridge = read_csv(OUT_DIR / "task2313_common_trade_pnl_bridge.csv")
    failures = read_csv(OUT_DIR / "task2314_selection_failure_snapshot.csv")
    coverage = read_csv(OUT_DIR / "task2315_data_coverage_signal_quality.csv")
    causes = read_csv(OUT_DIR / "task2316_root_cause_ranking.csv")
    closeout = read_csv(OUT_DIR / "task2320_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(len(lineage) >= 10, "lineage incomplete")
    require(len(overlap) >= 10, "overlap matrix incomplete")
    require(len(bridge) >= 150, "common bridge should include Task2151 and Task2191 references")
    require(len(failures) >= 20, "failure snapshot too small")
    require(len(coverage) >= 6, "coverage rows incomplete")
    require(len(causes) >= 5, "cause ranking incomplete")
    require(len(closeout) == 1, "expected one closeout")
    require(closeout == decision, "decision differs from closeout")
    require(len(manifest) >= 7, "manifest incomplete")

    for context, rows in [
        ("lineage", lineage),
        ("overlap", overlap),
        ("bridge", bridge),
        ("failures", failures),
        ("coverage", coverage),
        ("causes", causes),
        ("closeout", closeout),
    ]:
        validate_authority(rows, context)

    require(closeout[0]["verdict"] == "root_cause_not_same_experiment_plus_selector_and_sizing_path_break", "bad verdict")
    require(closeout[0]["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
    require(closeout[0]["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
    require(closeout[0]["real_capital"] == "FORBIDDEN", "real capital changed")
    require(closeout[0]["assignment_uses_future_outcome"] == "0", "future assignment")
    require(closeout[0]["outcome_used_for_assignment"] == "0", "outcome assignment")
    require(closeout[0]["outcome_used_for_audit_only"] == "1", "audit flag missing")

    primary = causes[0]
    require(primary["cause"] == "not_same_experiment", "primary cause should be experiment mismatch")
    require(any(row["cause"] == "exact_sizing_engine_not_reused" for row in causes), "missing sizing path cause")
    require(any(row["cause"] == "bad_trades_ranked_good_before_sizing" for row in causes), "missing selector weakness cause")
    require(any(row["reference_experiment"] == "Task2191_api_dd_winner_preserve" for row in bridge), "missing Task2191 bridge")
    require(any(row["interpretation"] == "selection_power_sparse" for row in coverage), "selection-power sparse coverage not identified")

    print("[TASK2311_2320_VALIDATE_OK] root_cause_audit=pass diagnostic_only=pass")
    print("Test results do not modify strategy acceptance status.")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
