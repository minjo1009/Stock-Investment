from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.semantic_enrichment_requirements import build_enrichment_requirements


TASK_ID = "Task738"
TASK737_ATTACHMENT = Path("docs/reports/task_737_semantic_modifier_bundle_attachment/task737_bundle_semantic_modifier_attachment.csv")
TASK736_TRANSLATIONS = Path("docs/reports/task_736_context_semantic_translator/task736_semantic_translation.csv")
OUT_DIR = Path("docs/reports/task_738_semantic_enrichment_requirements")


def build_task738(
    *,
    attachment_path: Path = TASK737_ATTACHMENT,
    translations_path: Path = TASK736_TRANSLATIONS,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    attachments = pd.read_csv(attachment_path)
    translations = pd.read_csv(translations_path)
    requirements = build_enrichment_requirements(attachments, translations)
    family_distribution = build_family_distribution(requirements)
    resolver_targets = build_resolver_targets(requirements)
    review_lanes = build_review_lane_assignment(requirements)
    missing_matrix = build_pipe_matrix(requirements, "missing_primitive_fields", "primitive_field")
    denominator_matrix = build_pipe_matrix(requirements, "required_denominators", "denominator")
    interaction_edges = build_interaction_edges(requirements)
    coverage = build_coverage_report(attachments, translations, requirements)
    guardrail = build_guardrail(requirements, attachments)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(requirements, family_distribution, resolver_targets, coverage, guardrail)
    pass_fail = build_pass_fail(requirements, family_distribution, resolver_targets, interaction_edges, coverage, guardrail)
    outputs = {
        "task738_enrichment_requirements.csv": requirements,
        "task738_requirement_family_distribution.csv": family_distribution,
        "task738_resolver_targets.csv": resolver_targets,
        "task738_review_lane_assignment.csv": review_lanes,
        "task738_missing_primitive_matrix.csv": missing_matrix,
        "task738_denominator_requirement_matrix.csv": denominator_matrix,
        "task738_interaction_requirement_edges.csv": interaction_edges,
        "task738_coverage_report.csv": coverage,
        "task738_guardrail.csv": guardrail,
        "task738_gpt_review_summary.csv": gpt_review,
        "task_738_decision.csv": decision,
        "task_738_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, requirements, resolver_targets, interaction_edges, decision, pass_fail)
    return {
        "attachments": attachments,
        "translations": translations,
        "requirements": requirements,
        "family_distribution": family_distribution,
        "resolver_targets": resolver_targets,
        "review_lanes": review_lanes,
        "missing_matrix": missing_matrix,
        "denominator_matrix": denominator_matrix,
        "interaction_edges": interaction_edges,
        "coverage": coverage,
        "guardrail": guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_family_distribution(requirements: pd.DataFrame) -> pd.DataFrame:
    grouped = requirements.groupby(["circuit_type", "requirement_family", "review_lane"], dropna=False)
    rows = []
    for keys, group in grouped:
        circuit_type, family, lane = keys
        rows.append(
            {
                "circuit_type": circuit_type,
                "requirement_family": family,
                "review_lane": lane,
                "requirement_count": len(group),
                "bundle_count": group["lifecycle_id"].nunique(),
                "source_event_count": group["source_event_id"].nunique(),
                "can_affect_confidence_count": int(group["can_affect_confidence"].sum()),
                "can_affect_risk_count": int(group["can_affect_risk"].sum()),
                "can_affect_slot_count": int(group["can_affect_slot"].sum()),
                "operating_catalyst_created_count": int(group["can_create_operating_catalyst"].sum()),
                "backtest_eligible_count": int(group["backtest_eligible_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["requirement_count", "requirement_family"], ascending=[False, True]).reset_index(drop=True)


def build_resolver_targets(requirements: pd.DataFrame) -> pd.DataFrame:
    grouped = requirements.groupby(["resolver_target_state", "review_lane"], dropna=False)
    rows = []
    for keys, group in grouped:
        resolver, lane = keys
        rows.append(
            {
                "resolver_target_state": resolver,
                "review_lane": lane,
                "requirement_count": len(group),
                "bundle_count": group["lifecycle_id"].nunique(),
                "requirement_family_set": "|".join(sorted(set(group["requirement_family"].astype(str)))),
                "circuit_type_set": "|".join(sorted(set(group["circuit_type"].astype(str)))),
                "backtest_eligible_count": int(group["backtest_eligible_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["requirement_count", "resolver_target_state"], ascending=[False, True]).reset_index(drop=True)


def build_review_lane_assignment(requirements: pd.DataFrame) -> pd.DataFrame:
    grouped = requirements.groupby(["review_lane", "circuit_type"], dropna=False)
    rows = []
    for keys, group in grouped:
        lane, circuit = keys
        rows.append(
            {
                "review_lane": lane,
                "circuit_type": circuit,
                "requirement_count": len(group),
                "bundle_count": group["lifecycle_id"].nunique(),
                "review_lane_is_trading_priority_flag": 0,
                "backtest_eligible_count": int(group["backtest_eligible_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["review_lane", "requirement_count"], ascending=[True, False]).reset_index(drop=True)


def build_pipe_matrix(requirements: pd.DataFrame, column: str, output_name: str) -> pd.DataFrame:
    rows = []
    for _, row in requirements.iterrows():
        for value in split_pipe(row.get(column)):
            rows.append(
                {
                    output_name: value,
                    "requirement_family": row["requirement_family"],
                    "circuit_type": row["circuit_type"],
                    "review_lane": row["review_lane"],
                    "requirement_count": 1,
                    "backtest_eligible_count": int(row["backtest_eligible_flag"]),
                }
            )
    frame = pd.DataFrame(rows)
    grouped = frame.groupby([output_name, "requirement_family", "circuit_type", "review_lane"], dropna=False).agg(
        requirement_count=("requirement_count", "sum"),
        backtest_eligible_count=("backtest_eligible_count", "sum"),
    )
    return grouped.reset_index().sort_values(["requirement_count", output_name], ascending=[False, True]).reset_index(drop=True)


def build_interaction_edges(requirements: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in requirements.iterrows():
        for field in split_pipe(row.get("required_interaction_fields")):
            rows.append(
                {
                    "lifecycle_id": row["lifecycle_id"],
                    "bundle_id": row["bundle_id"],
                    "source_event_id": row["source_event_id"],
                    "symbol": row["symbol"],
                    "circuit_type": row["circuit_type"],
                    "requirement_family": row["requirement_family"],
                    "required_interaction_field": field,
                    "resolver_target_state": row["resolver_target_state"],
                    "review_lane": row["review_lane"],
                    "rule_id": "TASK738_REQUIREMENT_INTERACTION_EDGE_REVIEW_ONLY",
                    "used_for_trading_flag": 0,
                    "backtest_eligible_flag": 0,
                    "outcome_used_for_assignment_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_coverage_report(attachments: pd.DataFrame, translations: pd.DataFrame, requirements: pd.DataFrame) -> pd.DataFrame:
    enrichment = attachments[attachments["queue_transition_state"].astype(str).eq("semantic_enrichment_needed")]
    scoped_translations = translations[translations["lifecycle_id"].astype(str).isin(set(enrichment["lifecycle_id"].astype(str)))]
    return pd.DataFrame(
        [
            {
                "scope": "task737_semantic_enrichment_needed_bundles",
                "bundle_count": len(enrichment),
                "expected_source_modifier_count": int(enrichment["source_modifier_count"].sum()),
                "translation_row_count": len(scoped_translations),
                "requirement_row_count": len(requirements),
                "coverage_state": "all_enrichment_bundles_have_requirement_objects" if len(enrichment) == requirements["lifecycle_id"].nunique() else "coverage_gap",
                "used_for_trading_flag": 0,
            }
        ]
    )


def build_guardrail(requirements: pd.DataFrame, attachments: pd.DataFrame) -> pd.DataFrame:
    enrichment = attachments[attachments["queue_transition_state"].astype(str).eq("semantic_enrichment_needed")]
    expected_source_modifiers = int(enrichment["source_modifier_count"].sum())
    forbidden_cols = forbidden_columns_found(requirements)
    action = requirements[
        (requirements["actionability_created_flag"] != 0)
        | (requirements["used_for_trading_flag"] != 0)
        | (requirements["backtest_eligible_flag"] != 0)
        | (requirements["outcome_used_for_assignment_flag"] != 0)
    ]
    missing_required = requirements[
        requirements["missing_primitive_fields"].fillna("").astype(str).eq("")
        | requirements["required_denominators"].fillna("").astype(str).eq("")
        | requirements["required_comparators"].fillna("").astype(str).eq("")
        | requirements["required_timing_checks"].fillna("").astype(str).eq("")
        | requirements["required_interaction_fields"].fillna("").astype(str).eq("")
        | requirements["resolver_target_state"].fillna("").astype(str).eq("")
    ]
    invalid_lane = requirements[~requirements["review_lane"].isin(["high_review_lane", "normal_review_lane"])]
    operating_for_context = requirements[
        requirements["circuit_type"].isin(
            ["form4_insider_behavior", "institutional_positioning", "ownership_float_structure", "governance_management", "activist_control"]
        )
        & (requirements["can_create_operating_catalyst"] != 0)
    ]
    unknown_as_adverse = requirements[
        requirements["current_semantic_state"].astype(str).str.contains("unknown", na=False)
        & requirements["current_semantic_polarity"].astype(str).eq("adverse")
    ]
    return pd.DataFrame(
        [
            gate("all_enrichment_bundles_covered", requirements["lifecycle_id"].nunique() == len(enrichment), f"bundles={requirements['lifecycle_id'].nunique()}", str(len(enrichment))),
            gate("all_source_modifiers_have_requirements", len(requirements) == expected_source_modifiers, f"rows={len(requirements)}", str(expected_source_modifiers)),
            gate("required_fields_present", missing_required.empty, f"rows={len(missing_required)}", "0"),
            gate("review_lane_not_trading_priority", invalid_lane.empty, f"rows={len(invalid_lane)}", "0"),
            gate("no_forbidden_score_rank_trade_columns", not forbidden_cols, "checked", "no score/rank/buy/sell/PnL/return columns"),
            gate("no_actionability_or_backtest_flags", action.empty, f"rows={len(action)}", "0"),
            gate("unknown_not_adverse", unknown_as_adverse.empty, f"rows={len(unknown_as_adverse)}", "0"),
            gate("context_circuits_do_not_create_operating_catalyst", operating_for_context.empty, f"rows={len(operating_for_context)}", "0"),
            gate("resolver_targets_present", requirements["resolver_target_state"].nunique() >= 8, f"targets={requirements['resolver_target_state'].nunique()}", ">=8"),
        ]
    )


def forbidden_columns_found(frame: pd.DataFrame) -> bool:
    forbidden = [
        "future_return",
        "forward_return",
        "net_return",
        "realized_pnl",
        "pnl",
        "win_loss",
        "winner",
        "loser",
        "top50",
        "rank",
        "score",
        "alpha_score",
        "priority_score",
        "buy_signal",
        "sell_signal",
        "trade_label",
        "backtest_label",
    ]
    for column in frame.columns:
        lower = str(column).lower()
        if any(token in lower for token in forbidden):
            return True
    return False


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "overall_brain_strategy_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "Institutional GPT review passed Task738 direction as SemanticModifier to EnrichmentRequirement to ResolverTarget to ReviewLane. It explicitly rejected score, rank, buy, sell, and backtest conversion.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "circuit_detail_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "GPT specified circuit-specific primitive facts, denominators, comparators, timing checks, interaction fields, resolver targets, review lanes, and guardrails for Form4, 13D/13G, 13F, ownership, generic 8-K, financing, M&A, macro, financial results, and governance.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(
    requirements: pd.DataFrame,
    family_distribution: pd.DataFrame,
    resolver_targets: pd.DataFrame,
    coverage: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "SEMANTIC_ENRICHMENT_REQUIREMENTS_BUILT_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "requirement_count": len(requirements),
                "bundle_count": requirements["lifecycle_id"].nunique(),
                "requirement_family_count": requirements["requirement_family"].nunique(),
                "resolver_target_count": requirements["resolver_target_state"].nunique(),
                "high_review_lane_count": int((requirements["review_lane"] == "high_review_lane").sum()),
                "normal_review_lane_count": int((requirements["review_lane"] == "normal_review_lane").sum()),
                "coverage_state": coverage.iloc[0]["coverage_state"],
                "guardrail_pass": int(guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Use Task738 requirements to upgrade source extractors and resolvers by circuit before any allocation, scoring, or backtest experiment.",
            }
        ]
    )


def build_pass_fail(
    requirements: pd.DataFrame,
    family_distribution: pd.DataFrame,
    resolver_targets: pd.DataFrame,
    interaction_edges: pd.DataFrame,
    coverage: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("requirements_created", len(requirements) > 0, f"rows={len(requirements)}", ">0"),
            gate("family_distribution_created", len(family_distribution) > 0, f"rows={len(family_distribution)}", ">0"),
            gate("resolver_targets_created", len(resolver_targets) > 0, f"rows={len(resolver_targets)}", ">0"),
            gate("interaction_edges_created", len(interaction_edges) >= len(requirements), f"rows={len(interaction_edges)}", ">= requirements"),
            gate("coverage_report_created", coverage.iloc[0]["coverage_state"] == "all_enrichment_bundles_have_requirement_objects", str(coverage.iloc[0]["coverage_state"]), "all covered"),
            gate("guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "semantic enrichment requirements review only"),
        ]
    )


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    requirements: pd.DataFrame,
    resolver_targets: pd.DataFrame,
    interaction_edges: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task738_enrichment_requirements.jsonl", requirements)
    write_jsonl(out_dir / "task738_resolver_targets.jsonl", resolver_targets)
    write_jsonl(out_dir / "task738_interaction_requirement_edges.jsonl", interaction_edges)
    (out_dir / "task_738_semantic_enrichment_requirements.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task738 Semantic Enrichment Requirements",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        f"- Requirements: {int(d['requirement_count'])}",
        f"- Covered bundles: {int(d['bundle_count'])}",
        f"- Requirement families: {int(d['requirement_family_count'])}",
        f"- Resolver targets: {int(d['resolver_target_count'])}",
        f"- High review lane rows: {int(d['high_review_lane_count'])}",
        f"- Normal review lane rows: {int(d['normal_review_lane_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task738 converts Task737 `semantic_enrichment_needed` bundles into circuit-specific enrichment requirements. It does not create scores, ranks, buy/sell signals, actionability, allocation, or backtest eligibility. The output is a work contract for upstream extractors and semantic resolvers.",
        "",
        "### Requirement Family Distribution",
        "",
        frame_to_markdown(outputs["task738_requirement_family_distribution.csv"].head(20)),
        "",
        "### Resolver Targets",
        "",
        frame_to_markdown(outputs["task738_resolver_targets.csv"].head(20)),
        "",
        "### Review Lanes",
        "",
        frame_to_markdown(outputs["task738_review_lane_assignment.csv"]),
        "",
        "### Coverage",
        "",
        frame_to_markdown(outputs["task738_coverage_report.csv"]),
        "",
        "### Guardrail",
        "",
        frame_to_markdown(outputs["task738_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task738_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "Task737 showed that 235 candidate bundles had attached information but insufficient interpreted facts. Task738 turns those gaps into exact extractor requirements: what fact to read, what denominator to compare against, what timing check is needed, and which resolver should handle it. This is still research infrastructure, not a trading rule.",
        "",
        "## Artifact Manifest",
        "",
        "- `task738_enrichment_requirements.csv/jsonl`",
        "- `task738_requirement_family_distribution.csv`",
        "- `task738_resolver_targets.csv/jsonl`",
        "- `task738_review_lane_assignment.csv`",
        "- `task738_missing_primitive_matrix.csv`",
        "- `task738_denominator_requirement_matrix.csv`",
        "- `task738_interaction_requirement_edges.csv/jsonl`",
        "- `task738_coverage_report.csv`",
        "- `task738_guardrail.csv`",
        "- `task738_gpt_review_summary.csv`",
        "- `task_738_decision.csv`",
        "- `task_738_pass_fail_matrix.csv`",
        "",
        "## Pass Fail Matrix",
        "",
        frame_to_markdown(pass_fail),
    ]
    return "\n".join(lines) + "\n"


def frame_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    columns = [str(column) for column in frame.columns]
    rows = []
    rows.append("| " + " | ".join(columns) + " |")
    rows.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for _, row in frame.iterrows():
        values = [markdown_cell(row[column]) for column in frame.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def markdown_cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_stdout_summary(artifacts: dict[str, pd.DataFrame]) -> None:
    decision = artifacts["decision"].iloc[0].to_dict()
    print(json.dumps(decision, ensure_ascii=False, default=str, indent=2))


def split_pipe(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [part for part in str(value).split("|") if part]


def gate(name: str, passed: bool, observed: str, expected: str) -> dict[str, object]:
    return {
        "gate": name,
        "pass_flag": int(bool(passed)),
        "observed": observed,
        "expected": expected,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Task738 semantic enrichment requirements.")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_stdout_summary(build_task738(out_dir=args.out_dir))


if __name__ == "__main__":
    main()
