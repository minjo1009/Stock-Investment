from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest import build_task678_active_cap3_winner_archetype as t678


TASK684_DIR = Path("docs/reports/task_684_interaction_context_prediction_stack")
TASK686_DIR = Path("docs/reports/task_686_source_certification_contract_repair")
TASK687_DIR = Path("docs/reports/task_687_information_ontology_logic_audit")


INFO_GROUPS: list[dict[str, object]] = [
    {
        "information_group": "chart_price_volume",
        "plain_name": "chart_price_volume",
        "columns": [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "vwap",
            "ret_5d_prev_x",
            "ret_20d_prev_x",
            "ma20_prev",
            "ma50_prev",
            "high20_prev",
            "high60_prev",
            "volume_ratio_prev",
            "near_high60_prev",
            "trend_stack_prev",
            "range_pos",
            "intraday_ret_from_open",
            "timing_state",
            "price_acceptance_score",
            "price_acceptance_state",
            "price_chart_acceptance_state",
        ],
        "assignment_status": "assignment_certified",
        "quality_grade": "A-",
        "main_gap": "Chart is quantified, but price acceptance is still rule-threshold based rather than microstructure-confirmed.",
    },
    {
        "information_group": "theme_market_leadership",
        "plain_name": "theme_market_leadership",
        "columns": [
            "theme_id",
            "theme_ret20_prev",
            "theme_breadth20_prev",
            "theme_volume_ratio_prev",
            "theme_rank_prev",
            "theme_regime_state_v4",
            "broad_market_score",
            "broad_market_stress",
            "breadth_20d",
            "market_ret_20d",
            "liquidity_ratio",
            "multi_day_market_state_v4",
            "leadership_lifecycle_state",
            "leadership_phase_strength",
            "leadership_market_alignment",
        ],
        "assignment_status": "assignment_certified",
        "quality_grade": "B+",
        "main_gap": "Leadership is mostly static state; rotation path and capital-flow transition are shallow.",
    },
    {
        "information_group": "company_source_event_presence",
        "plain_name": "company_news_event_presence",
        "columns": [
            "political_statement_pre7d_count",
            "geopolitical_event_pre7d_count",
            "institution_ownership_pre30d_count",
            "activist_13d_pre30d_flag",
            "passive_13g_pre30d_flag",
            "insider_form4_or_144_pre30d_flag",
            "ceo_ir_proxy_pre14d_count",
            "linked_event_count",
            "source_text_certified_event_count",
            "content_prediction_certified_event_count",
            "temporal_source_event_density",
            "temporal_source_time_gap_count",
        ],
        "assignment_status": "company_source_certified",
        "quality_grade": "B",
        "main_gap": "Presence and certification are good, but direct economic linkage quality still varies.",
    },
    {
        "information_group": "content_positive_negative_interpretation",
        "plain_name": "positive_negative_content_interpretation",
        "columns": [
            "content_direct_bullish_count",
            "content_direct_bearish_count",
            "content_contract_revenue_count",
            "content_guidance_margin_count",
            "content_supply_demand_count",
            "content_regulatory_policy_count",
            "content_insider_buy_count",
            "content_insider_sell_count",
            "negative_dilution_financing_count",
            "negative_regulation_sanction_tariff_count",
            "negative_ceo_ir_disappointment_count",
            "negative_insider_sell_count",
            "negative_earnings_margin_damage_count",
            "positive_contract_customer_count",
            "positive_backlog_order_count",
            "positive_guidance_up_count",
            "positive_margin_supply_combo_count",
            "positive_revenue_talk_weak_count",
            "content_refined_strength_score",
            "content_negative_score_flag",
            "positive_high_quality_flag",
            "negative_core_reversal_flag",
        ],
        "assignment_status": "content_prediction_certified",
        "quality_grade": "B-",
        "main_gap": "Interpretation is richer than presence, but still mostly keyword/count taxonomy, not full economic magnitude/counterparty/expectations analysis.",
    },
    {
        "information_group": "company_catalyst_quality",
        "plain_name": "company_catalyst_quality",
        "columns": [
            "catalyst_quality_score",
            "catalyst_quality_tier",
            "company_catalyst_state",
            "catalyst_path_type",
            "catalyst_economic_quality",
            "catalyst_durability",
            "catalyst_directness",
            "catalyst_surprise_proxy",
            "catalyst_negative_overhang",
            "catalyst_signal_density",
            "catalyst_priced_in_state",
            "catalyst_absorption_state",
            "catalyst_conflict_state",
            "catalyst_cross_context_state",
        ],
        "assignment_status": "derived_from_certified_content",
        "quality_grade": "B-",
        "main_gap": "Catalyst quality reuses content interpretation; it does not yet estimate dollar magnitude, margin bridge, backlog conversion, or expectation surprise robustly.",
    },
    {
        "information_group": "macro_context",
        "plain_name": "macro_context",
        "columns": [
            "macro_series_available_count",
            "macro_employment_state",
            "macro_inflation_state",
            "macro_rates_state",
            "macro_dollar_state",
            "macro_oil_state",
            "macro_credit_state",
            "macro_liquidity_state",
            "macro_overall_state",
            "macro_action_modifier",
            "macro_release_timestamp_repaired_flag",
            "macro_asof_provisional_for_diagnostic_flag",
            "macro_assignment_certified_flag",
            "macro_used_for_assignment_flag",
        ],
        "assignment_status": "diagnostic_only",
        "quality_grade": "C",
        "main_gap": "Macro is fetched and attached, but latest-vintage/repaired release timing blocks assignment use.",
    },
    {
        "information_group": "relation_engine",
        "plain_name": "relation_engine",
        "columns": [
            "rates_exposure",
            "oil_exposure",
            "dollar_exposure",
            "credit_exposure",
            "liquidity_exposure",
            "capital_intensity",
            "funding_sensitivity",
            "duration_sensitivity",
            "energy_sensitivity",
            "capex_demand_sensitivity",
            "policy_sensitivity",
            "liquidity_sensitivity",
            "mechanism_support_count",
            "mechanism_pressure_count",
            "mechanism_relation_state",
            "relation_transmission_state",
            "relation_assignment_certified_flag",
        ],
        "assignment_status": "partial_assignment_certified",
        "quality_grade": "C+",
        "main_gap": "This is still a handcrafted transmission template, not a full state graph across chart/theme/company/macro/news.",
    },
    {
        "information_group": "portfolio_slot_capacity",
        "plain_name": "portfolio_slot_capacity",
        "columns": [
            "same_entry_candidate_count",
            "same_entry_theme_count",
            "same_entry_relation_count",
            "portfolio_capacity_state",
            "active_theme_count",
            "active_relation_count",
            "active_driver_count",
            "active_fragile_count",
            "cohort_candidate_count",
            "cohort_slot_rank",
            "interaction_context_packet",
        ],
        "assignment_status": "assignment_certified",
        "quality_grade": "B-",
        "main_gap": "Capacity is cohort-aware, but replacement value and opportunity cost are not yet firm-grade.",
    },
    {
        "information_group": "microstructure",
        "plain_name": "microstructure",
        "columns": [
            "microstructure_state",
            "microstructure_state_v4",
            "microstructure_used_in_assignment",
        ],
        "assignment_status": "not_used_pending_raw_feature_builder",
        "quality_grade": "raw_pending",
        "main_gap": "Raw quote/trade folders exist, but current five-engine stack does not use them.",
    },
]


def build_task687_program(task684_dir: Path = TASK684_DIR, task686_dir: Path = TASK686_DIR) -> dict[str, pd.DataFrame]:
    TASK687_DIR.mkdir(parents=True, exist_ok=True)
    stack = pd.read_csv(task684_dir / "task684_interaction_stack_panel.csv")
    source_summary = pd.read_csv(task686_dir / "task686_source_certification_summary.csv")

    inventory = build_information_inventory(stack)
    overlap = build_overlap_audit()
    logic = build_logic_gap_audit(stack, source_summary)
    relation = build_relation_engine_scope_audit(stack)
    ontology = build_firm_grade_target_ontology()
    decision = build_decision(inventory, logic, relation)
    pass_fail = build_pass_fail(inventory, logic, relation)

    write_outputs(inventory, overlap, logic, relation, ontology, decision, pass_fail)
    return {
        "inventory": inventory,
        "overlap": overlap,
        "logic": logic,
        "relation": relation,
        "ontology": ontology,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_information_inventory(stack: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for group in INFO_GROUPS:
        cols = [col for col in group["columns"] if col in stack.columns]
        non_null = int(stack[cols].notna().all(axis=1).sum()) if cols else 0
        any_non_null = int(stack[cols].notna().any(axis=1).sum()) if cols else 0
        rows.append(
            {
                "information_group": group["information_group"],
                "plain_name": group["plain_name"],
                "assignment_status": group["assignment_status"],
                "quality_grade": group["quality_grade"],
                "configured_column_count": len(group["columns"]),
                "present_column_count": len(cols),
                "row_count": int(len(stack)),
                "all_required_present_row_count": non_null,
                "any_present_row_count": any_non_null,
                "coverage_rate_pct": rate(any_non_null, len(stack)),
                "main_gap": group["main_gap"],
                "example_columns": "|".join(cols[:12]),
            }
        )
    return pd.DataFrame(rows)


def build_overlap_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "overlap_id": "content_to_catalyst",
                "overlapping_groups": "content_positive_negative_interpretation -> company_catalyst_quality",
                "what_overlaps": "Contract, backlog, guidance, margin, supply-demand counts are reused as catalyst score/path/quality.",
                "risk": "Same evidence can be double-counted as both news quality and catalyst quality.",
                "needed_fix": "Separate raw evidence, interpreted economic content, and derived catalyst state with explicit dependency lineage.",
            },
            {
                "overlap_id": "catalyst_to_relation",
                "overlapping_groups": "company_catalyst_quality -> relation_engine",
                "what_overlaps": "Catalyst quality and price acceptance feed mechanism_relation_state.",
                "risk": "Relation engine can appear multi-dimensional while mostly repackaging catalyst/price states.",
                "needed_fix": "Relation state must expose which edges are company-only, macro-dependent, or price-confirmed.",
            },
            {
                "overlap_id": "theme_to_leadership_to_slot",
                "overlapping_groups": "theme_market_leadership -> portfolio_slot_capacity",
                "what_overlaps": "Theme rank/breadth and same-entry theme counts both affect selection pressure.",
                "risk": "A strong theme can be rewarded by leadership and penalized by concentration without a capital-flow explanation.",
                "needed_fix": "Add flow-regime interpretation: leadership expansion, crowding, rotation-out, defensive rotation.",
            },
            {
                "overlap_id": "macro_to_market_to_relation",
                "overlapping_groups": "macro_context -> theme_market_leadership -> relation_engine",
                "what_overlaps": "Macro states, broad market score, liquidity ratio, and relation pressure/support all describe regime.",
                "risk": "Macro is diagnostic-only but still appears semantically inside relation labels.",
                "needed_fix": "Keep macro-derived relation edges blocked unless macro certification or macro-excluded relation path is explicit.",
            },
            {
                "overlap_id": "price_to_catalyst_absorption",
                "overlapping_groups": "chart_price_volume -> company_catalyst_quality",
                "what_overlaps": "Price acceptance is used to infer catalyst absorption.",
                "risk": "Good price action can be mistaken for good fundamental interpretation.",
                "needed_fix": "Separate 'market accepted the story' from 'story has high economic value'.",
            },
        ]
    )


def build_logic_gap_audit(stack: pd.DataFrame, source_summary: pd.DataFrame) -> pd.DataFrame:
    core = source_summary[source_summary["scope"].eq("task672_core_panel")].iloc[0]
    rows = [
        {
            "logic_layer": "raw_source_layer",
            "current_state": f"company/content/theme-price certified rows={int(core['allocation_assignment_ready_count'])}/{int(core['row_count'])}; macro certified=0",
            "firm_grade_gap": "Raw source certification is improved, but original text evidence and economic extraction are not fully lineage-separated in the final stack.",
            "severity": "medium",
            "result_leakage_risk": "low",
        },
        {
            "logic_layer": "content_interpretation_layer",
            "current_state": summarize_counts(stack, ["positive_contract_customer_count", "positive_guidance_up_count", "negative_dilution_financing_count", "negative_earnings_margin_damage_count"]),
            "firm_grade_gap": "Interpretation buckets lack contract size, customer quality, recurring revenue, margin bridge, expectation delta, and priced-in analysis.",
            "severity": "high",
            "result_leakage_risk": "low",
        },
        {
            "logic_layer": "catalyst_quality_layer",
            "current_state": value_counts_text(stack, "catalyst_economic_quality"),
            "firm_grade_gap": "Catalyst quality is a derivative of content counts; it is not a full economic materiality model.",
            "severity": "high",
            "result_leakage_risk": "low",
        },
        {
            "logic_layer": "relation_engine_layer",
            "current_state": value_counts_text(stack, "relation_transmission_state"),
            "firm_grade_gap": "Relation engine is not yet a graph of conditional edges across macro, theme, company, price, and portfolio; it is mostly rule labels.",
            "severity": "high",
            "result_leakage_risk": "low",
        },
        {
            "logic_layer": "interaction_layer",
            "current_state": value_counts_text(stack, "archetype_interaction_context"),
            "firm_grade_gap": "Interaction exists, but still ranks predefined labels rather than resolving causal conflicts and prerequisites.",
            "severity": "high",
            "result_leakage_risk": "medium_if_retuned_by_outcome",
        },
        {
            "logic_layer": "slot_allocation_layer",
            "current_state": "guarded challenger accepted count remains 0 after source repair",
            "firm_grade_gap": "Slot logic lacks ex-ante replacement value, opportunity cost, and incumbent vulnerability model.",
            "severity": "high",
            "result_leakage_risk": "medium_if_tuned_on_winners",
        },
    ]
    return pd.DataFrame(rows)


def build_relation_engine_scope_audit(stack: pd.DataFrame) -> pd.DataFrame:
    relation_cert = int(pd.to_numeric(stack.get("relation_assignment_certified_flag"), errors="coerce").fillna(0).sum())
    macro_cert = int(pd.to_numeric(stack.get("macro_assignment_certified_flag"), errors="coerce").fillna(0).sum())
    macro_used = int(pd.to_numeric(stack.get("macro_used_for_assignment_flag"), errors="coerce").fillna(0).sum())
    return pd.DataFrame(
        [
            {
                "relation_component": "industry_exposure_template",
                "current_inputs": "capital_intensity|funding_sensitivity|duration_sensitivity|energy_sensitivity|capex_demand_sensitivity|policy_sensitivity|liquidity_sensitivity",
                "current_method": "manual template by theme_id",
                "coverage": f"rows={len(stack)}",
                "firm_grade_gap": "Static template; not updated by company business mix, balance sheet, or changing macro regime.",
            },
            {
                "relation_component": "macro_driver_pressure_support",
                "current_inputs": "rates|oil|dollar|credit|liquidity states and exposures",
                "current_method": "support_count vs pressure_count",
                "coverage": f"macro_certified={macro_cert}; macro_used={macro_used}",
                "firm_grade_gap": "Macro is diagnostic-only, so macro-driven relation authority is correctly blocked but economically incomplete.",
            },
            {
                "relation_component": "company_price_confirmed_path",
                "current_inputs": "catalyst_quality_tier|price_acceptance_state|mechanism_support_count",
                "current_method": "rule-based mechanism_relation_state",
                "coverage": f"relation_certified={relation_cert}/{len(stack)}",
                "firm_grade_gap": "This path is usable, but it blends price confirmation with economic causality.",
            },
            {
                "relation_component": "full_context_graph",
                "current_inputs": "chart|theme|market|company|event|macro|portfolio",
                "current_method": "not implemented as graph; partially represented by interaction_context_packet",
                "coverage": "not_available",
                "firm_grade_gap": "Missing prerequisite/blocker/offsetting/reinforcing edge graph with confidence and authority scope.",
            },
        ]
    )


def build_firm_grade_target_ontology() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "target_layer": "evidence_object",
                "purpose": "Store raw event/source facts without trading interpretation.",
                "must_contain": "source_id|event_ts|available_at_ts|symbol_link|theme_link|text_span|source_quality",
                "current_status": "partial",
            },
            {
                "target_layer": "economic_interpretation_object",
                "purpose": "Translate event into revenue/margin/cash-flow/backlog/regulatory/funding impact.",
                "must_contain": "direction|magnitude_proxy|duration|directness|surprise|priced_in_risk|confidence",
                "current_status": "shallow",
            },
            {
                "target_layer": "state_graph_edge",
                "purpose": "Represent how chart/theme/market/company/macro/portfolio affect each other.",
                "must_contain": "edge_type reinforcing|offsetting|prerequisite|blocker|sizing_modifier; authority_scope; confidence",
                "current_status": "not_firm_grade",
            },
            {
                "target_layer": "candidate_context_bundle",
                "purpose": "Bundle ex-ante facts for each lifecycle before allocation.",
                "must_contain": "evidence_objects|interpretation_objects|state_edges|missing_evidence|forbidden_flags",
                "current_status": "partial",
            },
            {
                "target_layer": "slot_decision_explanation",
                "purpose": "Explain why one candidate deserves a finite portfolio slot versus peers.",
                "must_contain": "incumbent_comparison|opportunity_cost|replacement_hurdle|do_not_trade_reason",
                "current_status": "weak",
            },
        ]
    )


def build_decision(inventory: pd.DataFrame, logic: pd.DataFrame, relation: pd.DataFrame) -> pd.DataFrame:
    high_gaps = int(logic["severity"].eq("high").sum())
    return pd.DataFrame(
        [
            {
                "task_id": "Task687",
                "verdict": "INFORMATION_ONTOLOGY_LOGIC_AUDIT_COMPLETE_NOT_FIRM_GRADE_YET",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "information_group_count": int(len(inventory)),
                "high_severity_logic_gap_count": high_gaps,
                "macro_assignment_status": "diagnostic_only",
                "relation_engine_status": "partial_not_full_context_graph",
                "primary_result": "Information exists, but firm-grade relational usage is not implemented yet.",
                "next_action": "Build explicit evidence-object -> economic-interpretation -> state-graph-edge contracts before another allocation rule.",
            }
        ]
    )


def build_pass_fail(inventory: pd.DataFrame, logic: pd.DataFrame, relation: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("information_groups_listed", len(inventory) >= 8, f"groups={len(inventory)}", ">=8 groups"),
            gate("overlap_risk_identified", True, "content/catalyst/relation/theme overlaps documented", "overlaps documented"),
            gate("logic_gaps_identified", int(logic["severity"].eq("high").sum()) >= 3, f"high={int(logic['severity'].eq('high').sum())}", ">=3 high gaps"),
            gate("relation_not_overclaimed", relation["firm_grade_gap"].astype(str).str.contains("graph|Static|incomplete", case=False).any(), "relation partial", "do not claim firm-grade"),
            gate("no_strategy_promotion", True, "audit only", "NOT_ACCEPTED/FORBIDDEN"),
        ]
    )


def write_outputs(
    inventory: pd.DataFrame,
    overlap: pd.DataFrame,
    logic: pd.DataFrame,
    relation: pd.DataFrame,
    ontology: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task687_information_inventory.csv": inventory,
        "task687_overlap_audit.csv": overlap,
        "task687_logic_gap_audit.csv": logic,
        "task687_relation_engine_scope_audit.csv": relation,
        "task687_firm_grade_target_ontology.csv": ontology,
        "task_687_decision.csv": decision,
        "task_687_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK687_DIR / name, index=False)
    (TASK687_DIR / "task_687_information_ontology_logic_audit.md").write_text(
        render_report(inventory, overlap, logic, relation, ontology, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK687_DIR, TASK687_DIR / "artifact_manifest.csv")


def render_report(
    inventory: pd.DataFrame,
    overlap: pd.DataFrame,
    logic: pd.DataFrame,
    relation: pd.DataFrame,
    ontology: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    return f"""# Task687 Information Ontology Logic Audit

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: information groups {int(d["information_group_count"])}, high-severity logic gaps {int(d["high_severity_logic_gap_count"])}, macro status `{d["macro_assignment_status"]}`, relation status `{d["relation_engine_status"]}`.
- What changed: no trading rule changed; this task audits what information exists, where it overlaps, and why current usage is not firm-grade relational logic yet.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

The project has usable chart, theme, market, company-source, content-interpretation, catalyst, relation, and portfolio-slot fields. Macro is available but diagnostic-only. Microstructure raw data exists separately but is not used in this stack.

{t678.markdown_table(inventory)}

### Exact join keys

- Current candidate-level surfaces are keyed by `lifecycle_id`, `symbol`, `entry_ts`, `theme_id`, and `split_name`.
- This audit creates no new inferred lifecycle match.

### Leakage audit

- No return, label, or future price is used to define the audit categories.
- The audit is diagnostic only.

### Overlap audit

{t678.markdown_table(overlap)}

### Logic gap audit

{t678.markdown_table(logic)}

### Relation engine scope audit

{t678.markdown_table(relation)}

### Firm-grade target ontology

{t678.markdown_table(ontology)}

### Split/OOS metrics

Not applicable. This task does not test a new trading rule.

### Failure decomposition

- The information layer is broad, but not cleanly separated into evidence, interpretation, relation edge, and slot decision objects.
- Several downstream labels repackage the same content evidence.
- The relation engine is not yet a full graph of interactions and authority scopes.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Economic interpretation quality needs contract size, customer quality, recurrence, margin bridge, expectation surprise, and priced-in analysis.
- Relation logic needs explicit edge types: reinforcing, offsetting, prerequisite, blocker, and sizing modifier.
- Allocation needs context bundles and replacement-hurdle explanations before another backtest.

## No-Background Decision-Maker Report

- What happened: we listed the information and found the weak point.
- Why it matters: the project has many data fields, but it does not yet reason like a firm-grade relational engine.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: separate raw evidence, event meaning, relationship logic, and slot decision before tuning returns.

## Artifact Manifest

- Inputs: Task684 interaction stack, Task686 source certification summary.
- Outputs: information inventory, overlap audit, logic gap audit, relation scope audit, target ontology, decision, pass/fail, manifest.
- Row counts: inventory {len(inventory)}, overlap {len(overlap)}, logic {len(logic)}, relation {len(relation)}, ontology {len(ontology)}.
- Validation commands: `python src/backtest/build_task687_information_ontology_logic_audit.py`; `python -m unittest tests.test_task687_information_ontology_logic_audit`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def value_counts_text(frame: pd.DataFrame, column: str, limit: int = 8) -> str:
    if column not in frame.columns:
        return "missing_column"
    counts = frame[column].fillna("__NA__").value_counts().head(limit)
    return "; ".join(f"{idx}={int(val)}" for idx, val in counts.items())


def summarize_counts(frame: pd.DataFrame, columns: list[str]) -> str:
    parts = []
    for col in columns:
        if col in frame.columns:
            parts.append(f"{col}_nonzero={int(pd.to_numeric(frame[col], errors='coerce').fillna(0).gt(0).sum())}")
    return "; ".join(parts)


def rate(num: int, den: int) -> float:
    return float(num / den * 100.0) if den else 0.0


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
    parser.add_argument("--task684-dir", type=Path, default=TASK684_DIR)
    parser.add_argument("--task686-dir", type=Path, default=TASK686_DIR)
    args = parser.parse_args()
    build_task687_program(task684_dir=args.task684_dir, task686_dir=args.task686_dir)
    print(f"[Task687] wrote {TASK687_DIR}")


if __name__ == "__main__":
    main()
