from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2941_2960_l4_thesis_invalidation"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID

FORBIDDEN_ASSIGNMENT_RE = re.compile(
    r"pnl|return|loss|negative|mdd|drawdown|exit|runtime_action|rank_by_kis_pnl|survival_read|avoidability|bad_trade",
    re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_assignment_leak(rows: list[dict[str, str]], name: str) -> None:
    require(rows, f"{name} empty")
    for idx, row in enumerate(rows, start=1):
        require(row.get("assignment_uses_future_outcome", "0") == "0", f"{name} row {idx} uses future outcome")
        require(row.get("outcome_used_for_assignment", "0") == "0", f"{name} row {idx} uses outcome for assignment")
        require(row.get("missing_source_is_negative", "0") == "0", f"{name} row {idx} treats missing source as negative")


def assert_status(rows: list[dict[str, str]], name: str) -> None:
    for idx, row in enumerate(rows, start=1):
        if "strategy_acceptance" in row:
            require(row["strategy_acceptance"] == "NOT_ACCEPTED", f"{name} row {idx} changed strategy status")
        if "deployment_readiness" in row:
            require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", f"{name} row {idx} changed deployment status")
        if "real_capital" in row:
            require(row["real_capital"] == "FORBIDDEN", f"{name} row {idx} permits real capital")


def main() -> None:
    report = REPORT_DIR / "task_2941_2960_l4_thesis_invalidation.md"
    decision = REPORT_DIR / "task_2960_decision.csv"
    require(report.exists(), "missing report")
    require(decision.exists(), "missing decision")

    scope = read_csv(OUT_DIR / "task2941_scope_freeze.csv")
    manifest = read_csv(OUT_DIR / "task2942_l4_input_manifest.csv")
    evidence = read_csv(OUT_DIR / "task2943_l4_thesis_evidence_snapshot.csv")
    rulebook = read_csv(OUT_DIR / "task2944_l4_invalidation_rulebook.csv")
    full_map = read_csv(OUT_DIR / "task2944_full_candidate_invalidation_map.csv")
    assignment = read_csv(OUT_DIR / "task2945_l4_assignment.csv")
    gaps = read_csv(OUT_DIR / "task2946_source_gap_boundary.csv")
    outcome = read_csv(OUT_DIR / "task2947_outcome_audit_attachment.csv")
    false_guard = read_csv(OUT_DIR / "task2946_clean_state_false_positive_guard.csv")
    bridge = read_csv(OUT_DIR / "task2947_l3_to_l4_bridge.csv")
    packets = read_csv(OUT_DIR / "task2948_gpt_expert_review_packets.csv")
    checks = read_csv(OUT_DIR / "task2949_acceptance_checks.csv")
    closeout = read_csv(OUT_DIR / "task2960_closeout.csv")
    artifact_manifest = read_csv(OUT_DIR / "artifact_manifest.csv")

    for name, rows in [
        ("scope", scope),
        ("manifest", manifest),
        ("evidence", evidence),
        ("rulebook", rulebook),
        ("full_map", full_map),
        ("assignment", assignment),
        ("gaps", gaps),
        ("outcome", outcome),
        ("false_guard", false_guard),
        ("bridge", bridge),
        ("packets", packets),
        ("checks", checks),
        ("closeout", closeout),
    ]:
        assert_no_assignment_leak(rows, name)

    assert_status(scope, "scope")
    assert_status(closeout, "closeout")

    require(len(scope) == 1, "scope row count mismatch")
    s = scope[0]
    require(s["l4_assignment_outcome_blind"] == "1", "scope must declare outcome-blind assignment")
    require(s["replay_performed"] == "0", "scope should not replay")
    require(s["selector_tuning_performed"] == "0", "scope should not tune selector")
    require(s["policy_changed"] == "0", "scope should not change policy")

    require(len(manifest) == 3100, f"input manifest should cover 3100 rows, got {len(manifest)}")
    require(len(evidence) == 3100, f"evidence snapshot should cover 3100 rows, got {len(evidence)}")
    require(len(full_map) == 3100, f"full map should cover 3100 rows, got {len(full_map)}")
    require(len(assignment) == 3100, f"assignment should cover 3100 rows, got {len(assignment)}")
    require(len(outcome) == 14, f"outcome audit should cover 14 MDD rows, got {len(outcome)}")

    allowed_governance_columns = {"missing_source_is_negative"}
    forbidden_cols = [col for col in assignment[0].keys() if col not in allowed_governance_columns and FORBIDDEN_ASSIGNMENT_RE.search(col)]
    require(not forbidden_cols, f"assignment has forbidden outcome-like columns: {forbidden_cols}")
    require(all(row["assignment_outcome_blind"] == "1" for row in assignment), "assignment rows must be outcome blind")
    require(all(row["allowed_use"] == "diagnostic_thesis_invalidation_only_not_policy" for row in assignment), "assignment allowed_use mismatch")
    require(all(row["outcome_used_for_audit_only"] == "0" for row in assignment), "assignment must not use outcomes")

    outcome_cols = set(outcome[0].keys())
    require({"kis_pnl", "kis_net_return", "mdd_window_flag"}.issubset(outcome_cols), "outcome audit missing outcome columns")
    require(all(row["post_assignment_join"] == "1" for row in outcome), "outcome audit must be post-assignment join")
    require(all(row["outcome_used_for_audit_only"] == "1" for row in outcome), "outcome audit rows must be audit-only")

    require(any(row["sec_state_condition"] == "hard_survival_or_listing_risk" and row["l4_action"] == "HARD_INVALIDATE" for row in rulebook), "hard survival/listing rule missing")
    require(any(row["sec_state_condition"] == "debt_survival_financing_cluster" and row["l4_action"] == "CAP_TO_WATCH" for row in rulebook), "debt survival should be cap/watch")
    require(any(row["sec_state_condition"] == "clean_or_low_financing_pressure" and row["l4_action"] == "PASS_CLEAN_SEC" for row in rulebook), "clean SEC pass rule missing")
    require(all(row["outcome_calibrated"] == "0" for row in rulebook), "rulebook must not be outcome calibrated")

    clean_invalidated = [
        row for row in full_map
        if row["sec_state"] == "clean_or_low_financing_pressure"
        and row["l4_action"] in {"HARD_INVALIDATE", "CAP_TO_WATCH", "WATCH_REQUIRE_CONFIRMATION"}
    ]
    require(not clean_invalidated, "clean SEC rows should not be invalidated")
    require(false_guard[0]["pass"] == "1", "clean false-positive guard failed")
    require(any(row["l4_action"] in {"CAP_TO_WATCH", "WATCH_REQUIRE_CONFIRMATION"} for row in full_map), "cap/watch candidates missing")
    require(any(row["gap_action"] == "report_gap_not_negative" for row in gaps), "source gap boundary should report gaps as non-negative")
    require(len(bridge) >= 1, "L3/L4 bridge missing")
    require(len(packets) >= 3, "expert review packets missing")
    require(all(row["pass"] == "1" for row in checks), "acceptance checks failed")

    require(len(closeout) == 1, "closeout row count mismatch")
    co = closeout[0]
    require(co["verdict"] == "l4_thesis_invalidation_completed_diagnostic_only", "bad closeout verdict")
    require(co["assignment_row_count"] == "3100", "closeout assignment count mismatch")
    require(co["outcome_audit_row_count"] == "14", "closeout outcome audit count mismatch")
    require(co["replay_performed"] == "0", "closeout should not replay")
    require(co["selector_tuning_performed"] == "0", "closeout should not tune selector")
    require(co["sizing_tuning_performed"] == "0", "closeout should not tune sizing")
    require(co["exit_tuning_performed"] == "0", "closeout should not tune exit")
    require(co["policy_changed"] == "0", "closeout should not change policy")
    require(co["all_acceptance_checks_pass"] == "1", "closeout acceptance checks not pass")

    manifest_paths = {row["relative_path"] for row in artifact_manifest}
    require("task2945_l4_assignment.csv" in manifest_paths, "artifact manifest missing assignment")
    require("task2947_outcome_audit_attachment.csv" in manifest_paths, "artifact manifest missing outcome audit")

    registry = read_csv(ROOT / "tasks/task_registry.csv")
    task_ids = {row["task_id"] for row in registry}
    require(all(f"Task{i}" in task_ids for i in range(2941, 2961)), "registry missing Task2941-2960 rows")
    op_state = (ROOT / "docs/operating_system/project_operating_state.md").read_text(encoding="utf-8")
    require("144. Task2941-Task2960" in op_state, "operating state missing Task2941-2960 line")
    print("[TASK2941_2960_L4_THESIS_INVALIDATION_VALIDATE_PASS]")


if __name__ == "__main__":
    main()
