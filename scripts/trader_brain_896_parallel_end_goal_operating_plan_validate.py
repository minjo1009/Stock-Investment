from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_896_parallel_end_goal_operating_plan"

REQUIRED_FILES = [
    "end_goal_progress_scorecard.csv",
    "parallel_execution_plan_task897_906.csv",
    "expert_panel_review_synthesis.csv",
    "external_gpt_review_synthesis.csv",
    "stop_doing_rules.csv",
    "parallel_lane_symbol_scope.csv",
    "task_896_parallel_end_goal_operating_plan_summary.json",
    "artifact_manifest.csv",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors

    scorecard = rows(ART / "end_goal_progress_scorecard.csv")
    plan = rows(ART / "parallel_execution_plan_task897_906.csv")
    experts = rows(ART / "expert_panel_review_synthesis.csv")
    external_review = rows(ART / "external_gpt_review_synthesis.csv")
    stop_rules = rows(ART / "stop_doing_rules.csv")
    scope = rows(ART / "parallel_lane_symbol_scope.csv")
    summary = json.loads((ART / "task_896_parallel_end_goal_operating_plan_summary.json").read_text(encoding="utf-8"))

    expected_stages = {
        "0_universe_market_data",
        "1_l1_source_evidence",
        "2_l2_primitive_fact",
        "3_l3_relationship_graph",
        "4_l4_candidate_thesis",
        "5_l5_trader_decision",
        "6_backtest_paper_live_gate",
    }
    if {row["stage"] for row in scorecard} != expected_stages:
        errors.append("scorecard must cover the full end-goal chain")
    if len(plan) != 10:
        errors.append("parallel execution plan must define Task897 through Task906")
    if [row["task_id"] for row in plan] != [f"Task{task_id}" for task_id in range(897, 907)]:
        errors.append("parallel execution plan must be ordered Task897 through Task906")
    lane_counts: dict[str, int] = {}
    for row in plan:
        lane_counts[row["lane"]] = lane_counts.get(row["lane"], 0) + 1
    if lane_counts.get("vertical_slice") != 5:
        errors.append("vertical_slice lane must have 5 tasks")
    if lane_counts.get("data_corpus") != 4:
        errors.append("data_corpus lane must have 4 tasks")
    if lane_counts.get("integration") != 1:
        errors.append("integration lane must have 1 task")
    if len(experts) < 15:
        errors.append("expert panel must include 10 institutions plus domain experts")
    if len(external_review) < 8:
        errors.append("external GPT review synthesis must capture actionable findings")
    task898 = next((row for row in plan if row["task_id"] == "Task898"), {})
    if task898.get("blocked_by") != "Task897;Task903":
        errors.append("Task898 must be blocked by Task897 and Task903 after external GPT review")
    task897 = next((row for row in plan if row["task_id"] == "Task897"), {})
    for required in ["source span", "as_of", "uncertainty", "deterministic"]:
        if required not in task897.get("success_criteria", ""):
            errors.append(f"Task897 success criteria missing {required}")
            break
    if len(stop_rules) < 9:
        errors.append("stop-doing rules must prevent project drift")
    stop_rule_text = " ".join(row["rule"] for row in stop_rules)
    for required in ["80 percent", "95 percent", "uncertainty", "freeze architecture"]:
        if required not in stop_rule_text:
            errors.append(f"stop rules missing {required}")
            break
    scope_by_lane = {row["lane"]: row for row in scope}
    if scope_by_lane.get("vertical_slice", {}).get("symbol_count") != "8":
        errors.append("vertical slice must be fixed to 8 seed symbols")
    if scope_by_lane.get("data_corpus", {}).get("symbol_count") != "62":
        errors.append("data corpus lane must track 62 missing-seed symbols")
    if summary.get("operating_mode") != "parallel_vertical_slice_plus_data_corpus":
        errors.append("operating mode mismatch")
    if summary.get("external_gpt_review_captured") is not True:
        errors.append("external GPT review capture must be recorded")
    if summary.get("first_next_task") != "Task897":
        errors.append("first next task must be Task897")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment readiness must remain diagnostic-only")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital must remain FORBIDDEN")

    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_896_PARALLEL_END_GOAL_PLAN_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_896_PARALLEL_END_GOAL_PLAN_OK] parallel end-goal operating plan artifacts validated")


if __name__ == "__main__":
    main()
