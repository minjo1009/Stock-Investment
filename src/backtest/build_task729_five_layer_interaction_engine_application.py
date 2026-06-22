from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task728_five_layer_interaction_logic_contract import (
    LAYER_STATE_COLUMNS,
    TASK713_PANEL,
    TASK714_PANEL,
    TASK715_PANEL,
    TASK716_PANEL,
    TASK717_PANEL,
    merge_layers,
)
from src.backtest.five_layer_interaction_engine import RELATION_PRIORITY, evaluate_interaction_frame


TASK_ID = "Task729"
OUT_DIR = Path("docs/reports/task_729_five_layer_interaction_engine_application")
KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]


def build_task729(
    *,
    task713_path: Path = TASK713_PANEL,
    task714_path: Path = TASK714_PANEL,
    task715_path: Path = TASK715_PANEL,
    task716_path: Path = TASK716_PANEL,
    task717_path: Path = TASK717_PANEL,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    frames = {
        "L1_Evidence": pd.read_csv(task713_path),
        "L2_Economic": pd.read_csv(task714_path),
        "L3_Price": pd.read_csv(task715_path),
        "L4_Portfolio": pd.read_csv(task716_path),
        "L5_Risk": pd.read_csv(task717_path),
    }
    merged = merge_layers(frames)
    edge_panel, resolution_panel = evaluate_interaction_frame(merged)

    edge_summary = build_edge_summary(edge_panel)
    resolution_summary = build_resolution_summary(resolution_panel)
    dependency_audit = build_dependency_audit(edge_panel, resolution_panel, merged)
    code_review_audit = build_code_review_audit(edge_panel, resolution_panel, dependency_audit)
    gpt_review = build_gpt_review_summary()
    leakage = build_leakage_guardrail([edge_panel, resolution_panel, edge_summary, resolution_summary, dependency_audit, code_review_audit, gpt_review])
    governance = build_governance_audit(merged, edge_panel, resolution_panel, dependency_audit, code_review_audit, leakage)
    decision = build_decision(merged, edge_panel, resolution_panel, code_review_audit)
    pass_fail = build_pass_fail(merged, edge_panel, resolution_panel, dependency_audit, code_review_audit, leakage, governance)

    outputs = {
        "task729_interaction_edge_panel.csv": edge_panel,
        "task729_interaction_resolution_panel.csv": resolution_panel,
        "task729_edge_summary.csv": edge_summary,
        "task729_resolution_summary.csv": resolution_summary,
        "task729_layer_dependency_audit.csv": dependency_audit,
        "task729_code_review_audit.csv": code_review_audit,
        "task729_gpt_institutional_review_summary.csv": gpt_review,
        "task729_leakage_guardrail.csv": leakage,
        "task729_governance_audit.csv": governance,
        "task_729_decision.csv": decision,
        "task_729_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "merged": merged,
        "edge_panel": edge_panel,
        "resolution_panel": resolution_panel,
        "edge_summary": edge_summary,
        "resolution_summary": resolution_summary,
        "dependency_audit": dependency_audit,
        "code_review_audit": code_review_audit,
        "gpt_review": gpt_review,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_edge_summary(edge_panel: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["edge_scope", "rule_family_id", "relation_type", "output_state"]
    return (
        edge_panel.groupby(group_cols, dropna=False)
        .size()
        .reset_index(name="edge_count")
        .sort_values(["edge_count", "edge_scope", "rule_family_id"], ascending=[False, True, True])
        .reset_index(drop=True)
    )


def build_resolution_summary(resolution_panel: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "l1_l2_economic_permission_state",
        "l2_l3_thesis_confirmation_state",
        "l3_l4_slot_adjustment_state",
        "l4_l5_budget_state",
        "final_actionability_state",
    ]
    return (
        resolution_panel.groupby(group_cols, dropna=False)
        .size()
        .reset_index(name="candidate_count")
        .sort_values(["candidate_count"] + group_cols, ascending=[False] + [True] * len(group_cols))
        .reset_index(drop=True)
    )


def build_dependency_audit(edge_panel: pd.DataFrame, resolution_panel: pd.DataFrame, merged: pd.DataFrame) -> pd.DataFrame:
    expected_scopes = {
        "L1->L2",
        "L1xL2",
        "L2xL3",
        "L2xL5",
        "L3xL4",
        "L4xL5",
        "L1xL2xL3xL4xL5",
    }
    candidate_count = len(merged)
    rows = [
        gate("row_coverage", len(resolution_panel) == candidate_count, f"resolution_rows={len(resolution_panel)};input_rows={candidate_count}", "one resolution per input row"),
        gate("edge_coverage", len(edge_panel) == candidate_count * len(expected_scopes), f"edge_rows={len(edge_panel)};expected={candidate_count * len(expected_scopes)}", "seven edges per input row"),
        gate("required_scopes_present", expected_scopes.issubset(set(edge_panel["edge_scope"])), f"scopes={sorted(set(edge_panel['edge_scope']))}", "all interaction scopes"),
        gate("all_candidates_have_l1_l2", (edge_panel["edge_scope"] == "L1->L2").sum() == candidate_count, str(int((edge_panel["edge_scope"] == "L1->L2").sum())), str(candidate_count)),
        gate("all_candidates_have_l2_l3", (edge_panel["edge_scope"] == "L2xL3").sum() == candidate_count, str(int((edge_panel["edge_scope"] == "L2xL3").sum())), str(candidate_count)),
        gate("all_candidates_have_l3_l4", (edge_panel["edge_scope"] == "L3xL4").sum() == candidate_count, str(int((edge_panel["edge_scope"] == "L3xL4").sum())), str(candidate_count)),
        gate("all_candidates_have_l4_l5", (edge_panel["edge_scope"] == "L4xL5").sum() == candidate_count, str(int((edge_panel["edge_scope"] == "L4xL5").sum())), str(candidate_count)),
        gate("priority_order_declared", min(RELATION_PRIORITY.values()) > 0 and RELATION_PRIORITY["blocker"] > RELATION_PRIORITY["reinforcing"], str(RELATION_PRIORITY), "blocker must dominate reinforcing"),
        gate("no_backtest_eligible", int(resolution_panel["backtest_eligible_flag"].sum()) == 0, str(int(resolution_panel["backtest_eligible_flag"].sum())), "0 until primitive fact and denominator gates"),
    ]
    return pd.DataFrame(rows)


def build_code_review_audit(edge_panel: pd.DataFrame, resolution_panel: pd.DataFrame, dependency_audit: pd.DataFrame) -> pd.DataFrame:
    rows = [
        gate("coderabbit_plugin_available", False, "not_available_in_current_plugin_list", "available plugin or explicit fallback"),
        gate("coderabbit_fallback_local_review_performed", True, "local_review_audit_created", "local code review audit when CodeRabbit unavailable"),
        gate("weak_source_not_rescued_by_price", weak_source_not_rescued_by_price(edge_panel, resolution_panel), "checked edge/resolution panel", "weak/noise/source gap must not become backtest eligible"),
        gate("l5_cannot_override_source_gap", l5_cannot_override_source_gap(edge_panel, resolution_panel), "checked source blocker rows", "L5 cannot rescue L1 source gap"),
        gate("interaction_outputs_review_only", int(edge_panel["assignment_allowed_flag"].sum()) == 0 and int(resolution_panel["interaction_engine_assignment_allowed_flag"].sum()) == 0, "assignment sums are zero", "no assignment output"),
        gate("backtest_outputs_forbidden", int(edge_panel["backtest_allowed_flag"].sum()) == 0 and int(resolution_panel["backtest_eligible_flag"].sum()) == 0, "backtest sums are zero", "no backtest promotion"),
        gate("dependency_audit_pass_except_coderabbit", int(dependency_audit["pass_flag"].min()) == 1, f"min={int(dependency_audit['pass_flag'].min())}", "all dependency gates pass"),
    ]
    return pd.DataFrame(rows)


def weak_source_not_rescued_by_price(edge_panel: pd.DataFrame, resolution_panel: pd.DataFrame) -> bool:
    weak_keys = row_key_set(
        edge_panel.loc[
            edge_panel["rule_family_id"].isin(["L1_L2_GATE_001", "L1_L2_GATE_002", "L1_L2_GATE_003", "L1_L2_CONTRA_005", "ALL_026"]),
        ]
    )
    promoted = resolution_panel[resolution_panel.apply(row_key, axis=1).isin(weak_keys) & (resolution_panel["backtest_eligible_flag"] != 0)]
    return promoted.empty


def l5_cannot_override_source_gap(edge_panel: pd.DataFrame, resolution_panel: pd.DataFrame) -> bool:
    source_gap_keys = row_key_set(edge_panel.loc[edge_panel["rule_family_id"] == "L1_L2_GATE_001"])
    rescued = resolution_panel[
        resolution_panel.apply(row_key, axis=1).isin(source_gap_keys)
        & ~resolution_panel["final_actionability_state"].str.contains("RESEARCH_ONLY", na=False)
    ]
    return rescued.empty


def row_key_set(frame: pd.DataFrame) -> set[tuple[str, str, str, str, str]]:
    return set(frame.apply(row_key, axis=1))


def row_key(row: pd.Series) -> tuple[str, str, str, str, str]:
    return tuple(str(row.get(col, "")) for col in KEYS)


def build_gpt_review_summary() -> pd.DataFrame:
    rows = [
        ("overall", "CONDITIONAL_PASS", "engine structure creates a row-level Layer Interaction Network rather than another stacked label table"),
        ("priority", "blocker > prerequisite > invalidation > confidence_cap > offsetting > sizing_modifier > escalation > reinforcing", "implemented as RELATION_PRIORITY and dominant edge resolution"),
        ("state_system", "final_actionability must be a state machine, not score summation", "implemented as research/watch-only states with no approval/trade-ready states"),
        ("source_risk", "price acceptance cannot rescue source gap or weak evidence", "tested in local CodeRabbit fallback audit"),
        ("risk_layer", "L5 cannot upgrade failed L1/L2 permission; it can only cap/block/invalidate", "tested in local dependency and code review audit"),
        ("permission", "backtest permission remains FAIL", "Task729 applies interaction diagnosis only because raw source objects, denominators, and primitive economic facts remain missing"),
    ]
    return pd.DataFrame(
        [
            {
                "review_topic": topic,
                "captured_gpt_point": point,
                "implementation_response": response,
                "gpt_is_source_of_truth_flag": 0,
            }
            for topic, point, response in rows
        ]
    )


def build_leakage_guardrail(frames: list[pd.DataFrame]) -> pd.DataFrame:
    forbidden = ["future_return", "realized_outcome", "top50", "winner", "loser", "costed_return", "net_return"]
    rows = []
    for i, frame in enumerate(frames):
        cols = [str(c).lower() for c in frame.columns]
        found = sorted({token for token in forbidden for col in cols if token in col})
        rows.append(
            {
                "artifact_index": i,
                "forbidden_columns_found": "|".join(found),
                "pass_flag": int(not found),
                "outcome_used_for_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_governance_audit(
    merged: pd.DataFrame,
    edge_panel: pd.DataFrame,
    resolution_panel: pd.DataFrame,
    dependency_audit: pd.DataFrame,
    code_review_audit: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    candidate_count = len(merged)
    rows = [
        gate("input_layer_rows_present", candidate_count > 0, str(candidate_count), ">0"),
        gate("edge_panel_present", len(edge_panel) >= candidate_count * 7, f"rows={len(edge_panel)}", ">=7 edges per candidate"),
        gate("resolution_panel_present", len(resolution_panel) == candidate_count, f"rows={len(resolution_panel)}", "one per candidate"),
        gate("dominant_priority_valid", set(resolution_panel["dominant_relation_type"]).issubset(set(RELATION_PRIORITY)), str(sorted(set(resolution_panel["dominant_relation_type"]))), "declared relation priorities"),
        gate("dependency_audit_pass", int(dependency_audit["pass_flag"].min()) == 1, f"min={int(dependency_audit['pass_flag'].min())}", "1"),
        gate("code_review_audit_has_expected_coderabbit_unavailable", "coderabbit_plugin_available" in set(code_review_audit["gate_name"]), "present", "present"),
        gate("local_code_review_pass_except_unavailable_plugin", int(code_review_audit.loc[code_review_audit["gate_name"] != "coderabbit_plugin_available", "pass_flag"].min()) == 1, "fallback gates pass", "1"),
        gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
    ]
    return pd.DataFrame(rows)


def build_decision(
    merged: pd.DataFrame,
    edge_panel: pd.DataFrame,
    resolution_panel: pd.DataFrame,
    code_review_audit: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "FIVE_LAYER_INTERACTION_ENGINE_APPLIED_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "candidate_count": len(merged),
                "edge_count": len(edge_panel),
                "resolution_count": len(resolution_panel),
                "final_actionability_states": resolution_panel["final_actionability_state"].nunique(),
                "coderabbit_plugin_status": "NOT_AVAILABLE_LOCAL_REVIEW_USED",
                "code_review_pass_except_coderabbit_unavailable": int(code_review_audit.loc[code_review_audit["gate_name"] != "coderabbit_plugin_available", "pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Implement source-certified primitive facts and denominator gates, then reconnect this engine before any backtest candidate promotion.",
            }
        ]
    )


def build_pass_fail(
    merged: pd.DataFrame,
    edge_panel: pd.DataFrame,
    resolution_panel: pd.DataFrame,
    dependency_audit: pd.DataFrame,
    code_review_audit: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        gate("interaction_engine_applied_to_all_candidates", len(resolution_panel) == len(merged), f"resolution={len(resolution_panel)};input={len(merged)}", "one resolution per candidate"),
        gate("seven_edges_per_candidate", len(edge_panel) == len(merged) * 7, f"edges={len(edge_panel)}", f"{len(merged) * 7}"),
        gate("all_relation_priorities_declared", set(edge_panel["relation_type"]).issubset(set(RELATION_PRIORITY)), str(sorted(set(edge_panel["relation_type"]))), "declared relation types"),
        gate("final_actionability_generated", resolution_panel["final_actionability_state"].nunique() >= 3, f"unique={resolution_panel['final_actionability_state'].nunique()}", ">=3"),
        gate("dependency_audit_pass", int(dependency_audit["pass_flag"].min()) == 1, f"min={int(dependency_audit['pass_flag'].min())}", "1"),
        gate("coderabbit_plugin_available", False, "not_available", "available"),
        gate("coderabbit_fallback_review_pass", int(code_review_audit.loc[code_review_audit["gate_name"] != "coderabbit_plugin_available", "pass_flag"].min()) == 1, "local fallback pass", "1"),
        gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
        gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
        gate("backtest_permission", False, "FAIL", "PASS only after primitive fact and denominator gates"),
    ]
    return pd.DataFrame(rows)


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    (out_dir / "task_729_five_layer_interaction_engine_application.md").write_text(
        render_report(outputs, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task729 Five Layer Interaction Engine Application",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        f"- Candidates: {int(d['candidate_count'])}",
        f"- Edges: {int(d['edge_count'])}",
        f"- Resolutions: {int(d['resolution_count'])}",
        "- CodeRabbit: `NOT_AVAILABLE_LOCAL_REVIEW_USED`",
        "",
        "## Quant Expert Report",
        "",
        "Task729 applies the Task728 contract as a row-level interaction engine. It generates seven typed edges per candidate, resolves edge priority into layer interaction states, blocks assignment/backtest promotion, and audits that source gaps, weak evidence, and L5 risk labels cannot be rescued by price or slot states.",
        "",
        "### Edge Summary",
        "",
        frame_to_markdown(outputs["task729_edge_summary.csv"].head(40)),
        "",
        "### Resolution Summary",
        "",
        frame_to_markdown(outputs["task729_resolution_summary.csv"].head(40)),
        "",
        "### Code Review Audit",
        "",
        frame_to_markdown(outputs["task729_code_review_audit.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- 결론: 5개 Layer를 실제 엔진으로 연결했습니다.",
        "- 후보마다 L1->L2, L2->L3, L3->L4, L4->L5, 전체 gate edge를 생성합니다.",
        "- Price가 약한 source를 구제하지 못하게 막았습니다.",
        "- L5가 L1 source gap을 덮지 못하게 막았습니다.",
        "- CodeRabbit은 현재 사용 불가라 로컬 코드리뷰 감사로 대체했습니다.",
        "- 그래도 백테스트는 아직 금지입니다. 원문 primitive fact와 denominator가 없기 때문입니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        frame_to_markdown(pass_fail),
        "",
        "## Artifact Manifest",
        "",
    ]
    for filename in outputs:
        lines.append(f"- `{filename}`")
    lines.append("- `artifact_manifest.csv`")
    return "\n".join(lines)


def frame_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    cols = [str(c) for c in frame.columns]
    rows = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in frame.iterrows():
        rows.append("| " + " | ".join([markdown_cell(row.get(col, "")) for col in frame.columns]) + " |")
    return "\n".join(rows)


def markdown_cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task729(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} "
        f"candidates={decision['candidate_count']} edges={decision['edge_count']} "
        f"backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
