from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2281_2290_post_acquisition_parity"
REPORT = ROOT / "docs/reports/task_2281_2290_post_acquisition_parity/task_2281_2290_post_acquisition_parity.md"
DECISION = ROOT / "docs/reports/task_2281_2290_post_acquisition_parity/task_2281_2290_decision.csv"
AUTHORITY = "POST_ACQUISITION_PLUS8000_PARITY_GATE_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    panel = read_csv(OUT_DIR / "task2283_post_acquisition_parity_panel.csv")
    summary = read_csv(OUT_DIR / "task2284_post_acquisition_parity_summary.csv")
    closeout = read_csv(OUT_DIR / "task2290_closeout.csv")
    decision = read_csv(DECISION)
    manifest = read_csv(OUT_DIR / "artifact_manifest.csv")
    require(REPORT.exists(), "missing report")
    require(len(panel) == 3100, "panel not full candidate pool")
    require(len(summary) >= 12, "summary incomplete")
    require(len(closeout) == 1, "expected one closeout")
    require(closeout == decision, "decision differs from closeout")
    require(len(manifest) >= 4, "manifest incomplete")
    for rows, context in [(panel, "panel"), (summary, "summary"), (closeout, "closeout")]:
        for row in rows:
            require(row.get("authority", AUTHORITY) == AUTHORITY, f"{context} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                require(row["assignment_uses_future_outcome"] == "0", f"{context} future assignment")
            if "outcome_used_for_assignment" in row:
                require(row["outcome_used_for_assignment"] == "0", f"{context} outcome assignment")
            if "missing_source_is_negative" in row:
                require(row["missing_source_is_negative"] == "0", f"{context} missing source negative")
    gate = next(row for row in summary if row["coverage_metric"] == "replay_gate_candidate_pass")
    require(gate["covered_rows"] == closeout[0]["replay_gate_candidate_rows"], "gate row mismatch")
    require(closeout[0]["replay_allowed"] == "0", "post-acquisition parity must not auto-authorize replay")
    require(closeout[0]["replay_requires_user_confirmation"] == "1", "user confirmation gate missing")
    if closeout[0].get("parity_gate_pass") == "1":
        require(closeout[0]["verdict"] == "post_acquisition_parity_pass_replay_still_requires_user_confirmation", "bad parity pass verdict")
    else:
        require(closeout[0]["verdict"] == "post_acquisition_parity_insufficient_replay_blocked", "bad parity blocked verdict")
    require(closeout[0]["strategy_acceptance"] == "NOT_ACCEPTED", "strategy acceptance changed")
    require(closeout[0]["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
    require(closeout[0]["real_capital"] == "FORBIDDEN", "real capital changed")
    print("[TASK2281_2290_VALIDATE_OK] post_acquisition_parity=pass")
    print("Strategy: NOT_ACCEPTED")
    print("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    print("Real Capital: FORBIDDEN")


if __name__ == "__main__":
    main()
