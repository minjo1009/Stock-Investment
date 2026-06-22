from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2231_2250_plus8000_data_parity"
REPORT = ROOT / "docs/reports/task_2231_2250_plus8000_data_parity/task_2231_2250_plus8000_data_parity.md"
DECISION = ROOT / "docs/reports/task_2231_2250_plus8000_data_parity/task_2231_2250_decision.csv"
AUTHORITY = "DATA_PARITY_PLUS8000_SELECTED_TRADE_FEATURE_EXPANSION_ONLY"


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
        if "assignment_uses_future_outcome" in row:
            require(row["assignment_uses_future_outcome"] == "0", f"{context} future assignment")
        if "outcome_used_for_assignment" in row:
            require(row["outcome_used_for_assignment"] == "0", f"{context} outcome assignment")
        if "missing_source_is_negative" in row:
            require(row["missing_source_is_negative"] == "0", f"{context} missing source negative")


def main() -> None:
    contract = read_csv(OUT_DIR / "task2231_plus8000_feature_contract.csv")
    universe = read_csv(OUT_DIR / "task2232_full_candidate_target_universe.csv")
    panel = read_csv(OUT_DIR / "task2233_full_candidate_plus8000_parity_panel.csv")
    queue = read_csv(OUT_DIR / "task2234_missing_source_acquisition_queue.csv")
    summary = read_csv(OUT_DIR / "task2235_parity_coverage_summary.csv")
    recomputed = read_csv(OUT_DIR / "task2236_recomputed_plus8000_feature_panel.csv")
    feature_summary = read_csv(OUT_DIR / "task2237_recomputed_feature_summary.csv")
    closeout = read_csv(OUT_DIR / "task2250_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    require(REPORT.exists(), "missing report")
    require(len(contract) == 5, "expected five +8000 contract artifacts")
    require(len(universe) == 1, "expected one universe row")
    require(universe[0]["candidate_rows"] == "3100", "target universe not 3100")
    require(len(panel) == 3100, "parity panel not full candidate pool")
    require(len(summary) >= 17, "coverage summary incomplete")
    require(len(recomputed) == 3100, "recomputed feature panel not full candidate pool")
    require(len(feature_summary) >= 2, "feature schema summary missing")
    require(len(closeout) == 1, "expected one closeout")
    require(closeout == decision, "decision differs from closeout")
    require(len(manifest) >= 6, "manifest incomplete")

    validate_authority(contract, "contract")
    validate_authority(panel, "panel")
    validate_authority(queue, "queue")
    validate_authority(summary, "summary")
    validate_authority(recomputed, "recomputed")
    validate_authority(feature_summary, "feature_summary")
    validate_authority(closeout, "closeout")

    full = next(row for row in summary if row["coverage_metric"] == "plus8000_data_parity_pass")
    require(full["covered_rows"] == closeout[0]["plus8000_parity_rows"], "closeout parity row mismatch")
    require(full["coverage_ratio"] == closeout[0]["plus8000_parity_ratio"], "closeout parity ratio mismatch")
    require(closeout[0]["replay_allowed"] == "0", "parity task must not auto-authorize replay")
    if closeout[0].get("parity_gate_pass") == "1":
        require(closeout[0]["verdict"] == "plus8000_data_parity_pass_replay_still_requires_user_confirmation", "bad pass verdict")
        require(closeout[0].get("replay_requires_user_confirmation") == "1", "pass verdict still needs user confirmation")
    else:
        require(closeout[0]["verdict"] == "plus8000_data_parity_failed_replay_blocked", "bad blocked verdict")
        require(closeout[0]["replay_block_reason"] != "", "blocked replay needs reason")
    require(all(row["replay_allowed"] == "0" for row in panel), "panel should not authorize replay rows")
    require(all(row["replay_block_reason"] == "plus8000_data_parity_not_complete" for row in panel), "panel missing replay block reason")
    schema = next(row for row in feature_summary if row["coverage_metric"] == "feature_schema_parity_pass")
    require(schema["covered_rows"] == "3100", "feature schema parity was not generated for all candidates")
    require(all(row["feature_schema_parity_pass"] == "1" for row in recomputed), "recomputed feature schema rows missing")
    require(all(row["strict_transcript_gate_pass"] == "0" for row in recomputed), "strict transcript gate incorrectly opened")
    require(all(row["strict_analyst_revision_gate_pass"] == "0" for row in recomputed), "strict analyst gate incorrectly opened")
    require(closeout[0]["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
    require(closeout[0]["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
    require(closeout[0]["real_capital"] == "FORBIDDEN", "real capital changed")

    print("[TASK2231_2250_VALIDATE_OK] plus8000_data_parity_gate=pass replay_block_rule=pass")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
