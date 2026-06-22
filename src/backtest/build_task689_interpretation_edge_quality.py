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
TASK688_DIR = Path("docs/reports/task_688_context_object_contracts")
TASK689_DIR = Path("docs/reports/task_689_interpretation_edge_quality")

FORBIDDEN_OBJECT_COLUMNS = {
    "net_return_from_entry",
    "net_return_pct",
    "return_pct",
    "win_flag",
    "win_eval_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "simulated_exit_price",
    "simulated_exit_ts",
}

IDENTITY = ["lifecycle_id", "symbol", "entry_ts", "entry_ts_utc", "theme_id", "split_name"]


def build_task689_program(task684_dir: Path = TASK684_DIR, task688_dir: Path = TASK688_DIR) -> dict[str, pd.DataFrame]:
    TASK689_DIR.mkdir(parents=True, exist_ok=True)
    stack = pd.read_csv(task684_dir / "task684_interaction_stack_panel.csv")
    interpretations = pd.read_csv(task688_dir / "task688_economic_interpretation_objects.csv")
    edges = pd.read_csv(task688_dir / "task688_state_graph_edges.csv")
    bundles = pd.read_csv(task688_dir / "task688_candidate_context_bundles.csv")
    slot = pd.read_csv(task688_dir / "task688_slot_decision_explanations.csv")

    stack = add_sector_family(stack)
    rulebook = build_sector_edge_rulebook()
    interpretation_quality = build_interpretation_quality_panel(interpretations, stack)
    edge_quality = build_edge_quality_panel(edges, stack, rulebook)
    weak_layer = build_candidate_weak_layer_audit(stack, bundles, slot, interpretation_quality, edge_quality)
    audit = build_integrity_audit(interpretation_quality, edge_quality, weak_layer)
    decision = build_decision(stack, interpretation_quality, edge_quality, weak_layer, audit)
    pass_fail = audit.copy()

    write_outputs(rulebook, interpretation_quality, edge_quality, weak_layer, audit, decision, pass_fail)
    return {
        "rulebook": rulebook,
        "interpretation_quality": interpretation_quality,
        "edge_quality": edge_quality,
        "weak_layer": weak_layer,
        "audit": audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def add_sector_family(stack: pd.DataFrame) -> pd.DataFrame:
    stack = stack.copy()
    stack["sector_family"] = stack["theme_id"].map(classify_sector_family)
    return stack


def build_sector_edge_rulebook() -> pd.DataFrame:
    rows = [
        {
            "sector_family": "semis_ai_infrastructure",
            "economic_transmission_priority": "demand_cycle|capex_cycle|supply_chain|duration_liquidity",
            "positive_edge_requirements": "contract_or_supply_demand plus price_acceptance plus theme_leadership",
            "blocker_edge_conditions": "demand_fade|duration_pressure|liquidity_pressure|late_extension_without_absorption",
            "sizing_modifier_conditions": "high_volatility_or_late_extension requires reduced slot claim",
            "current_gap": "No order-size, backlog-conversion, hyperscaler capex revision, or inventory-cycle bridge.",
        },
        {
            "sector_family": "defense_space_policy",
            "economic_transmission_priority": "policy_budget|contract_visibility|funding_risk|duration_risk",
            "positive_edge_requirements": "named_customer_or_budget visibility plus price_acceptance",
            "blocker_edge_conditions": "funding_stress|policy_headline_fade|contract_size_unknown|space_financing_risk",
            "sizing_modifier_conditions": "binary_contract_or_funding_dependent names require smaller initial claim",
            "current_gap": "Contract value, funded backlog, award protest risk, and dilution runway are mostly proxy-only.",
        },
        {
            "sector_family": "biotech_healthcare",
            "economic_transmission_priority": "clinical_regulatory|reimbursement|cash_runway|event_binary_risk",
            "positive_edge_requirements": "regulatory/clinical catalyst must be direct and price accepted",
            "blocker_edge_conditions": "binary_event|cash_runway_pressure|regulatory_uncertainty|no_follow_through",
            "sizing_modifier_conditions": "event-binary and funding-sensitive candidates need cap-limited role",
            "current_gap": "Trial phase, endpoint quality, FDA calendar, and cash runway are not fully modeled.",
        },
        {
            "sector_family": "financials_credit",
            "economic_transmission_priority": "rates_path|credit_cycle|curve|deposit_beta|capital_return",
            "positive_edge_requirements": "credit_support or rate_margin_support plus price_acceptance",
            "blocker_edge_conditions": "credit_pressure|yield_curve_conflict|liquidity_stress|regulatory_capital_risk",
            "sizing_modifier_conditions": "credit stress and rate conflict reduce slot claim",
            "current_gap": "Curve, spread, deposit, and credit-quality details are still coarse.",
        },
        {
            "sector_family": "energy_commodities",
            "economic_transmission_priority": "oil_price|supply_demand|inventory|geopolitics|capex_discipline",
            "positive_edge_requirements": "oil_support or supply_demand plus price_acceptance",
            "blocker_edge_conditions": "oil_pressure|demand_fade|cost_inflation|geopolitical_fade",
            "sizing_modifier_conditions": "commodity reversal risk requires confirmation or reduced size",
            "current_gap": "Commodity curve, inventory surprise, and realized spread bridge are missing.",
        },
        {
            "sector_family": "industrials_capex",
            "economic_transmission_priority": "capex_cycle|backlog|margin|policy|global_demand",
            "positive_edge_requirements": "backlog/order or capex demand support plus price_acceptance",
            "blocker_edge_conditions": "capex_demand_pressure|energy_input_cost|dollar_pressure|late_cycle_order_fade",
            "sizing_modifier_conditions": "extended price with unclear backlog conversion needs confirmation",
            "current_gap": "Backlog conversion, margin bridge, and customer capex budget quality are mostly proxy-only.",
        },
        {
            "sector_family": "consumer_platform",
            "economic_transmission_priority": "demand_elasticity|margin|ad_spend|subscription_retention|rates",
            "positive_edge_requirements": "guidance/margin or demand signal plus price_acceptance",
            "blocker_edge_conditions": "demand_slowdown|margin_pressure|consumer_credit_pressure|competition",
            "sizing_modifier_conditions": "weak demand or margin uncertainty limits slot priority",
            "current_gap": "Unit economics, cohort retention, and spend revisions are not deeply modeled.",
        },
        {
            "sector_family": "general_growth",
            "economic_transmission_priority": "revenue_growth|margin|duration|liquidity|theme_flow",
            "positive_edge_requirements": "durable catalyst plus price_acceptance plus non-hostile market context",
            "blocker_edge_conditions": "duration_pressure|liquidity_pressure|no_price_acceptance|single_weak_source",
            "sizing_modifier_conditions": "uncertain catalyst or crowded relation lowers replacement claim",
            "current_gap": "Sector-specific economics are under-specified; this row is fallback only.",
        },
    ]
    return pd.DataFrame(rows)


def build_interpretation_quality_panel(interpretations: pd.DataFrame, stack: pd.DataFrame) -> pd.DataFrame:
    joined = interpretations.merge(
        select_columns_with_defaults(stack, identity_plus_stack_columns()), on="lifecycle_id", how="left", suffixes=("", "_stack")
    )
    rows = []
    for _, row in joined.iterrows():
        quality = score_interpretation_quality(row)
        rows.append(
            {
                "interpretation_quality_id": f"{row['interpretation_object_id']}|quality",
                **identity_from_row(row),
                "primary_driver": row["primary_driver"],
                "sector_family": row["sector_family"],
                "direction": row["direction"],
                "economic_channel": row["economic_channel"],
                "economic_specificity_score": quality["economic_specificity_score"],
                "magnitude_quality_state": quality["magnitude_quality_state"],
                "counterparty_quality_state": quality["counterparty_quality_state"],
                "cash_flow_bridge_state": quality["cash_flow_bridge_state"],
                "expectation_surprise_state": quality["expectation_surprise_state"],
                "priced_in_quality_state": quality["priced_in_quality_state"],
                "duration_quality_state": quality["duration_quality_state"],
                "directness_quality_state": quality["directness_quality_state"],
                "firm_grade_gap_count": quality["firm_grade_gap_count"],
                "interpretation_quality_tier": quality["interpretation_quality_tier"],
                "upgrade_priority": quality["upgrade_priority"],
                "quality_reason_codes": quality["quality_reason_codes"],
                "assignment_authority_scope": row["authority_scope"],
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_edge_quality_panel(edges: pd.DataFrame, stack: pd.DataFrame, rulebook: pd.DataFrame) -> pd.DataFrame:
    joined = edges.merge(
        select_columns_with_defaults(stack, edge_stack_columns()), on="lifecycle_id", how="left", suffixes=("", "_stack")
    )
    rule = rulebook.set_index("sector_family")
    rows = []
    for _, row in joined.iterrows():
        edge = score_edge_quality(row, rule)
        rows.append(
            {
                "edge_quality_id": f"{row['state_graph_edge_id']}|quality",
                **identity_from_row(row),
                "sector_family": row["sector_family"],
                "from_node": row["from_node"],
                "to_node": row["to_node"],
                "original_edge_type": row["edge_type"],
                "refined_edge_type": edge["refined_edge_type"],
                "sector_transmission_role": edge["sector_transmission_role"],
                "sector_specific_blocker_flag": edge["sector_specific_blocker_flag"],
                "sector_specific_confirmation_required_flag": edge["sector_specific_confirmation_required_flag"],
                "sizing_modifier_flag": edge["sizing_modifier_flag"],
                "edge_quality_score": edge["edge_quality_score"],
                "edge_quality_tier": edge["edge_quality_tier"],
                "edge_weakness_reason_codes": edge["edge_weakness_reason_codes"],
                "authority_scope": row["authority_scope"],
                "eligible_for_slot_assignment_flag": int(row["eligible_for_slot_assignment_flag"]),
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_candidate_weak_layer_audit(
    stack: pd.DataFrame,
    bundles: pd.DataFrame,
    slot: pd.DataFrame,
    interpretation_quality: pd.DataFrame,
    edge_quality: pd.DataFrame,
) -> pd.DataFrame:
    interp_summary = interpretation_quality.groupby("lifecycle_id").agg(
        interpretation_weak_count=("interpretation_quality_tier", lambda values: int(values.isin(["weak", "proxy_only"]).sum())),
        interpretation_strong_count=("interpretation_quality_tier", lambda values: int(values.eq("strong").sum())),
        firm_grade_gap_count=("firm_grade_gap_count", "sum"),
        dominant_interpretation_gap=("quality_reason_codes", dominant_gap_reason),
    )
    edge_summary = edge_quality.groupby("lifecycle_id").agg(
        edge_weak_count=("edge_quality_tier", lambda values: int(values.isin(["weak", "proxy_only"]).sum())),
        edge_strong_count=("edge_quality_tier", lambda values: int(values.eq("strong").sum())),
        blocker_edge_count=("sector_specific_blocker_flag", "sum"),
        confirmation_edge_count=("sector_specific_confirmation_required_flag", "sum"),
        sizing_modifier_count=("sizing_modifier_flag", "sum"),
    )
    bundle_map = bundles.set_index("lifecycle_id")
    slot_map = slot.set_index("lifecycle_id")
    rows = []
    for _, row in stack.iterrows():
        lifecycle_id = str(row["lifecycle_id"])
        interp = interp_summary.loc[lifecycle_id]
        edge = edge_summary.loc[lifecycle_id]
        bundle = bundle_map.loc[lifecycle_id]
        slot_row = slot_map.loc[lifecycle_id]
        weak_layer = choose_weakest_layer(bundle, interp, edge, slot_row)
        rows.append(
            {
                "candidate_weak_layer_audit_id": f"{lifecycle_id}|weak_layer_audit",
                **identity_from_row(row),
                "sector_family": row["sector_family"],
                "weakest_layer": weak_layer,
                "evidence_gap_flag": int(str(bundle["missing_evidence_flags"]) != "no_material_missing_flags"),
                "interpretation_weak_count": int(interp["interpretation_weak_count"]),
                "interpretation_strong_count": int(interp["interpretation_strong_count"]),
                "firm_grade_gap_count": int(interp["firm_grade_gap_count"]),
                "dominant_interpretation_gap": interp["dominant_interpretation_gap"],
                "edge_weak_count": int(edge["edge_weak_count"]),
                "edge_strong_count": int(edge["edge_strong_count"]),
                "blocker_edge_count": int(edge["blocker_edge_count"]),
                "confirmation_edge_count": int(edge["confirmation_edge_count"]),
                "sizing_modifier_count": int(edge["sizing_modifier_count"]),
                "slot_replacement_hurdle_required_flag": int(slot_row["replacement_hurdle_required_flag"]),
                "slot_candidate_role": slot_row["candidate_role"],
                "next_research_action": next_action_for_weakest_layer(weak_layer),
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def score_interpretation_quality(row: pd.Series) -> dict[str, object]:
    driver = str(row["primary_driver"])
    gaps: list[str] = []
    score = 0

    magnitude_quality = "proxy_only"
    if driver == "company_catalyst":
        score += count_positive_company_vectors(row)
        if int(value(row, "positive_contract_customer_count", 0)) > 0:
            score += 2
            counterparty = "customer_proxy_present"
        else:
            counterparty = "customer_quality_missing"
            gaps.append("customer_quality_missing")
        if int(value(row, "positive_margin_supply_combo_count", 0)) > 0 or int(value(row, "content_guidance_margin_count", 0)) > 0:
            score += 2
            cash_flow = "margin_or_guidance_bridge_present"
        elif int(value(row, "positive_backlog_order_count", 0)) > 0 or int(value(row, "content_contract_revenue_count", 0)) > 0:
            score += 1
            cash_flow = "revenue_or_backlog_bridge_proxy"
        else:
            cash_flow = "cash_flow_bridge_missing"
            gaps.append("cash_flow_bridge_missing")
        if int(value(row, "content_max_magnitude_score", 0)) >= 3:
            score += 1
            magnitude_quality = "magnitude_proxy_present"
        else:
            gaps.append("contract_value_actual_missing")
        surprise = surprise_state(value(row, "catalyst_surprise_proxy", "unknown"))
        priced = priced_in_state(value(row, "catalyst_priced_in_state", "proxy_only"))
        duration = duration_state(value(row, "catalyst_durability", "unknown"))
        directness = directness_state(value(row, "catalyst_directness", "unknown"))
        score += bonus_for_state(surprise, "strong") + bonus_for_state(priced, "clean") + bonus_for_state(duration, "durable") + bonus_for_state(directness, "direct")
    elif driver == "price_acceptance":
        counterparty = "not_applicable"
        cash_flow = "not_applicable"
        surprise = "not_measured"
        priced = priced_in_state(value(row, "priced_in_risk", "proxy_only"))
        duration = "entry_window_proxy"
        directness = "direct_price"
        if str(value(row, "direction", "")) == "positive":
            score += 3
        if "extended" in str(value(row, "economic_channel", "")):
            gaps.append("extension_absorption_unproven")
            score -= 1
        magnitude_quality = "price_acceptance_proxy"
    elif driver == "theme_leadership":
        counterparty = "not_applicable"
        cash_flow = "theme_flow_proxy"
        surprise = "not_measured"
        priced = "not_measured"
        duration = str(value(row, "duration", "unknown"))
        directness = "theme_flow"
        if str(value(row, "direction", "")) == "positive":
            score += 2
        if str(value(row, "leadership_breadth_quality", "")) == "broad":
            score += 2
        else:
            gaps.append("theme_breadth_not_broad")
        magnitude_quality = "theme_proxy"
    elif driver == "market_context":
        counterparty = "not_applicable"
        cash_flow = "market_beta_proxy"
        surprise = "not_measured"
        priced = "not_measured"
        duration = "multi_day_proxy"
        directness = "market_context"
        score += 2 if str(value(row, "direction", "")) in {"positive", "mixed"} else 0
        magnitude_quality = "market_proxy"
    elif driver == "macro_context":
        counterparty = "not_applicable"
        cash_flow = "macro_transmission_proxy"
        surprise = "not_latest_vintage_certified"
        priced = "diagnostic_only"
        duration = "asof_provisional"
        directness = "macro_transmission"
        gaps.append("macro_assignment_certification_missing")
        magnitude_quality = "diagnostic_only"
    else:
        counterparty = "not_applicable"
        cash_flow = "portfolio_constraint"
        surprise = "not_applicable"
        priced = "not_applicable"
        duration = "slot_window"
        directness = "portfolio_constraint"
        score += 2 if str(value(row, "direction", "")) != "negative" else 0
        magnitude_quality = "capacity_proxy"

    if surprise in {"unknown", "not_measured", "not_latest_vintage_certified"} and driver == "company_catalyst":
        gaps.append("expectation_surprise_weak")
    if priced in {"proxy_only", "mixed_proxy"} and driver == "company_catalyst":
        gaps.append("priced_in_analysis_proxy_only")

    tier = quality_tier(score, len(gaps), driver)
    return {
        "economic_specificity_score": int(max(score, 0)),
        "magnitude_quality_state": magnitude_quality,
        "counterparty_quality_state": counterparty,
        "cash_flow_bridge_state": cash_flow,
        "expectation_surprise_state": surprise,
        "priced_in_quality_state": priced,
        "duration_quality_state": duration,
        "directness_quality_state": directness,
        "firm_grade_gap_count": len(set(gaps)),
        "interpretation_quality_tier": tier,
        "upgrade_priority": upgrade_priority_for_tier(tier, driver),
        "quality_reason_codes": "|".join(sorted(set(gaps))) if gaps else "no_major_quality_gap_detected",
    }


def score_edge_quality(row: pd.Series, rulebook: pd.DataFrame) -> dict[str, object]:
    sector = str(row["sector_family"])
    original = str(row["edge_type"])
    from_node = str(row["from_node"])
    to_node = str(row["to_node"])
    score = 0
    reasons: list[str] = []

    role = classify_edge_role(from_node, to_node, sector)
    blocker = sector_blocker(row, sector)
    confirm = int(original in {"confirmation_required", "prerequisite_unproven"} or blocker)
    sizing = int(
        blocker
        or "extended" in str(value(row, "price_chart_acceptance_state", ""))
        or int(value(row, "active_relation_count", 0)) >= 3
    )

    if original in {"reinforcing", "sizing_modifier"}:
        score += 2
    if int(value(row, "eligible_for_slot_assignment_flag", 0)) == 1:
        score += 2
    if int(value(row, "mechanism_sparse_cell_flag", 0)) == 0:
        score += 1
    if sector != "general_growth":
        score += 1
    if blocker:
        score -= 2
        reasons.append("sector_blocker_present")
    if confirm:
        reasons.append("confirmation_required_by_sector_or_edge")
    if from_node == "macro_context":
        score = 1
        reasons.append("macro_diagnostic_only_no_slot_authority")

    refined = refine_edge_type(original, blocker, confirm, from_node)
    tier = edge_tier(score, from_node)
    if sector in rulebook.index:
        current_gap = str(rulebook.loc[sector, "current_gap"])
    else:
        current_gap = "fallback_sector_rule_used"
    if current_gap:
        reasons.append(f"sector_gap={current_gap}")
    return {
        "refined_edge_type": refined,
        "sector_transmission_role": role,
        "sector_specific_blocker_flag": int(blocker),
        "sector_specific_confirmation_required_flag": int(confirm),
        "sizing_modifier_flag": int(sizing),
        "edge_quality_score": int(max(score, 0)),
        "edge_quality_tier": tier,
        "edge_weakness_reason_codes": "|".join(reasons) if reasons else "no_major_edge_gap_detected",
    }


def build_integrity_audit(
    interpretation_quality: pd.DataFrame,
    edge_quality: pd.DataFrame,
    weak_layer: pd.DataFrame,
) -> pd.DataFrame:
    outputs = {
        "interpretation_quality": interpretation_quality,
        "edge_quality": edge_quality,
        "weak_layer": weak_layer,
    }
    forbidden = sorted(
        f"{name}:{col}" for name, frame in outputs.items() for col in frame.columns if col in FORBIDDEN_OBJECT_COLUMNS
    )
    rows = [
        gate(
            "quality_panels_present",
            all(len(frame) > 0 for frame in outputs.values()),
            "; ".join(f"{name}={len(frame)}" for name, frame in outputs.items()),
            "interpretation, edge, and weak-layer panels must have rows",
        ),
        gate(
            "weak_layer_one_row_per_candidate",
            weak_layer["lifecycle_id"].is_unique,
            f"rows={len(weak_layer)}; unique_lifecycle={weak_layer['lifecycle_id'].nunique()}",
            "one weak-layer audit row per lifecycle",
        ),
        gate(
            "sector_specific_edge_rules_present",
            edge_quality["sector_family"].nunique() >= 5,
            f"sector_families={edge_quality['sector_family'].nunique()}",
            "multiple sector families must be handled",
        ),
        gate(
            "weak_layers_are_not_all_same",
            weak_layer["weakest_layer"].nunique() >= 3,
            f"weakest_layer_count={weak_layer['weakest_layer'].nunique()}",
            "weakest layer should decompose candidates into multiple failure modes",
        ),
        gate(
            "no_outcome_columns_in_quality_outputs",
            len(forbidden) == 0,
            "|".join(forbidden) if forbidden else "none",
            "PnL/outcome columns excluded",
        ),
        gate(
            "macro_still_not_promoted",
            int(edge_quality.loc[edge_quality["from_node"].eq("macro_context"), "eligible_for_slot_assignment_flag"].sum()) == 0,
            "macro eligible edge sum="
            f"{int(edge_quality.loc[edge_quality['from_node'].eq('macro_context'), 'eligible_for_slot_assignment_flag'].sum())}",
            "macro diagnostic-only edge cannot become slot authority",
        ),
    ]
    return pd.DataFrame(rows)


def build_decision(
    stack: pd.DataFrame,
    interpretation_quality: pd.DataFrame,
    edge_quality: pd.DataFrame,
    weak_layer: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task689",
                "verdict": "INTERPRETATION_EDGE_QUALITY_PANELS_BUILT_NO_TRADING_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "candidate_count": int(len(stack)),
                "interpretation_quality_rows": int(len(interpretation_quality)),
                "edge_quality_rows": int(len(edge_quality)),
                "weak_layer_rows": int(len(weak_layer)),
                "sector_family_count": int(edge_quality["sector_family"].nunique()),
                "weakest_layer_count": int(weak_layer["weakest_layer"].nunique()),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Economic interpretation and sector-specific edge quality are now audited before any return tuning.",
                "next_action": "Upgrade weakest interpretation and edge layers, then review candidate examples before allocation backtest.",
            }
        ]
    )


def write_outputs(
    rulebook: pd.DataFrame,
    interpretation_quality: pd.DataFrame,
    edge_quality: pd.DataFrame,
    weak_layer: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task689_sector_edge_rulebook.csv": rulebook,
        "task689_interpretation_quality_panel.csv": interpretation_quality,
        "task689_edge_quality_panel.csv": edge_quality,
        "task689_candidate_weak_layer_audit.csv": weak_layer,
        "task689_integrity_audit.csv": audit,
        "task_689_decision.csv": decision,
        "task_689_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK689_DIR / name, index=False)
    (TASK689_DIR / "task_689_interpretation_edge_quality.md").write_text(
        render_report(rulebook, interpretation_quality, edge_quality, weak_layer, audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK689_DIR, TASK689_DIR / "artifact_manifest.csv")


def render_report(
    rulebook: pd.DataFrame,
    interpretation_quality: pd.DataFrame,
    edge_quality: pd.DataFrame,
    weak_layer: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    interpretation_summary = (
        interpretation_quality.groupby(["primary_driver", "interpretation_quality_tier"], dropna=False)
        .size()
        .reset_index(name="row_count")
    )
    edge_summary = (
        edge_quality.groupby(["sector_family", "refined_edge_type", "edge_quality_tier"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .head(60)
    )
    weak_summary = weak_layer.groupby(["weakest_layer"], dropna=False).size().reset_index(name="candidate_count")
    return f"""# Task689 Interpretation and Edge Quality

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: candidates {int(d["candidate_count"])}, interpretation quality rows {int(d["interpretation_quality_rows"])}, edge quality rows {int(d["edge_quality_rows"])}, sector families {int(d["sector_family_count"])}, weakest-layer states {int(d["weakest_layer_count"])}.
- What changed: economic interpretation quality and sector-specific edge quality are now explicit panels.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Inputs are Task684 interaction stack and Task688 five-layer object contracts. This task does not add raw sources and does not infer lifecycle matches.

### Exact join keys

- `lifecycle_id` joins Task688 interpretation, edge, bundle, and slot objects to Task684 candidate context.
- `theme_id` maps candidates into sector families for sector-specific edge rules.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included in the quality outputs.
- All quality outputs set outcome/future/label flags to zero.
- This task runs no return test and promotes no trading rule.

### Economic interpretation quality

{t678.markdown_table(interpretation_summary)}

### Sector edge rulebook

{t678.markdown_table(rulebook)}

### Edge quality sample summary

{t678.markdown_table(edge_summary)}

### Candidate weakest-layer decomposition

{t678.markdown_table(weak_summary)}

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Company catalyst interpretation is still often proxy-only where contract value, named customer quality, margin bridge, and expectation surprise are absent.
- Sector edges are now explicit, but they still depend on existing proxy fields.
- Macro remains diagnostic-only; it is not promoted into slot authority.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Add source-text extraction for contract value, customer quality, repeatability, margin impact, and expectation surprise.
- Upgrade sector-specific edge thresholds from template logic to validated candidate-review logic.
- Only after quality panels are reviewed should allocation/backtest change.

## No-Background Decision-Maker Report

- What happened: candidates are now split by where the reasoning is weak.
- Why it matters: we can fix the weak layer first instead of tuning after seeing returns.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: inspect examples from each weak layer and improve the source interpretation or edge rule.

## Artifact Manifest

- Inputs: Task684 interaction stack, Task688 interpretation/edge/bundle/slot objects.
- Outputs: sector edge rulebook, interpretation quality panel, edge quality panel, weak-layer audit, integrity audit, decision, pass/fail, manifest.
- Row counts: rulebook {len(rulebook)}, interpretation quality {len(interpretation_quality)}, edge quality {len(edge_quality)}, weak layer {len(weak_layer)}.
- Validation commands: `python src/backtest/build_task689_interpretation_edge_quality.py`; `python -m unittest tests.test_task689_interpretation_edge_quality`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def classify_sector_family(theme_id: object) -> str:
    text = str(theme_id).lower()
    if any(token in text for token in ["semi", "ai", "cloud", "data_center", "chip"]):
        return "semis_ai_infrastructure"
    if any(token in text for token in ["space", "defense", "aerospace", "drone", "satellite"]):
        return "defense_space_policy"
    if any(token in text for token in ["bio", "health", "pharma", "medical", "genomics"]):
        return "biotech_healthcare"
    if any(token in text for token in ["bank", "financial", "insurance", "fintech", "broker"]):
        return "financials_credit"
    if any(token in text for token in ["oil", "gas", "energy", "uranium", "solar", "battery", "commodity"]):
        return "energy_commodities"
    if any(token in text for token in ["industrial", "robot", "automation", "machinery", "infrastructure"]):
        return "industrials_capex"
    if any(token in text for token in ["consumer", "retail", "media", "platform", "gaming", "ecommerce"]):
        return "consumer_platform"
    return "general_growth"


def identity_plus_stack_columns() -> list[str]:
    return unique(
        [
            "lifecycle_id",
            *IDENTITY,
            "sector_family",
            "positive_contract_customer_count",
            "positive_backlog_order_count",
            "positive_guidance_up_count",
            "positive_margin_supply_combo_count",
            "content_contract_revenue_count",
            "content_guidance_margin_count",
            "content_supply_demand_count",
            "content_max_magnitude_score",
            "content_avg_priced_in_risk_score",
            "leadership_breadth_quality",
            "catalyst_surprise_proxy",
            "catalyst_priced_in_state",
            "catalyst_durability",
            "catalyst_directness",
        ]
    )


def edge_stack_columns() -> list[str]:
    return unique(
        [
            "lifecycle_id",
            *IDENTITY,
            "sector_family",
            "price_chart_acceptance_state",
            "mechanism_sparse_cell_flag",
            "active_relation_count",
            "funding_stress_state",
            "duration_pressure_state",
            "energy_input_cost_state",
            "capex_demand_support_state",
            "policy_geopolitical_support_state",
            "adoption_support_state",
            "rates_exposure",
            "oil_exposure",
            "dollar_exposure",
            "credit_exposure",
            "liquidity_exposure",
            "mechanism_support_count",
            "mechanism_pressure_count",
            "relation_assignment_certified_flag",
        ]
    )


def identity_from_row(row: pd.Series) -> dict[str, object]:
    return {col: value(row, col, "") for col in IDENTITY}


def count_positive_company_vectors(row: pd.Series) -> int:
    cols = [
        "positive_contract_customer_count",
        "positive_backlog_order_count",
        "positive_guidance_up_count",
        "positive_margin_supply_combo_count",
        "content_contract_revenue_count",
        "content_guidance_margin_count",
        "content_supply_demand_count",
    ]
    return int(sum(1 for col in cols if int(value(row, col, 0)) > 0))


def surprise_state(raw: object) -> str:
    text = str(raw)
    if text in {"high", "medium", "low"}:
        return text
    if text in {"not_applicable", "not_measured"}:
        return text
    return "unknown"


def priced_in_state(raw: object) -> str:
    text = str(raw)
    if "clean" in text or "low_priced" in text:
        return "clean"
    if "mixed" in text:
        return "mixed_proxy"
    if text in {"not_applicable", "not_measured", "diagnostic_only"}:
        return text
    return "proxy_only"


def duration_state(raw: object) -> str:
    text = str(raw)
    if "durable" in text:
        return "durable"
    if "transient" in text:
        return "transient"
    return text or "unknown"


def directness_state(raw: object) -> str:
    text = str(raw)
    if "direct" in text:
        return "direct"
    if "indirect" in text:
        return "indirect"
    return text or "unknown"


def bonus_for_state(state: str, target: str) -> int:
    return 1 if state == target else 0


def quality_tier(score: int, gap_count: int, driver: str) -> str:
    if driver == "macro_context":
        return "proxy_only"
    if gap_count >= 3:
        return "weak"
    if score >= 7 and gap_count <= 1:
        return "strong"
    if score >= 4:
        return "medium"
    return "proxy_only"


def upgrade_priority_for_tier(tier: str, driver: str) -> str:
    if driver == "macro_context":
        return "keep_diagnostic_until_asof_certified"
    if tier in {"weak", "proxy_only"}:
        return "source_text_and_interpretation_upgrade"
    if tier == "medium":
        return "edge_context_review"
    return "candidate_example_review"


def classify_edge_role(from_node: str, to_node: str, sector: str) -> str:
    if from_node == "company_catalyst" and to_node == "price_acceptance":
        return f"{sector}_catalyst_absorption_prerequisite"
    if from_node == "theme_leadership" and to_node == "price_acceptance":
        return f"{sector}_leadership_to_price_confirmation"
    if from_node == "market_context" and to_node == "theme_leadership":
        return f"{sector}_market_theme_amplifier"
    if from_node == "macro_context":
        return f"{sector}_macro_diagnostic_context"
    if to_node == "relation_transmission":
        return f"{sector}_economic_transmission_core"
    if to_node == "slot_decision":
        return f"{sector}_portfolio_capacity_modifier"
    return f"{sector}_generic_edge"


def sector_blocker(row: pd.Series, sector: str) -> bool:
    funding_pressure = "pressure" in str(value(row, "funding_stress_state", ""))
    duration_pressure = "pressure" in str(value(row, "duration_pressure_state", ""))
    energy_pressure = "pressure" in str(value(row, "energy_input_cost_state", ""))
    capex_pressure = "pressure" in str(value(row, "capex_demand_support_state", ""))
    policy_pressure = "pressure" in str(value(row, "policy_geopolitical_support_state", ""))
    liquidity_high = str(value(row, "liquidity_exposure", "")) == "high" and duration_pressure
    if sector == "semis_ai_infrastructure":
        return bool(duration_pressure or liquidity_high or capex_pressure)
    if sector == "defense_space_policy":
        return bool(funding_pressure or policy_pressure or duration_pressure)
    if sector == "biotech_healthcare":
        return bool(funding_pressure or policy_pressure)
    if sector == "financials_credit":
        return bool("pressure" in str(value(row, "credit_exposure", "")) or liquidity_high)
    if sector == "energy_commodities":
        return bool(energy_pressure or "pressure" in str(value(row, "oil_exposure", "")))
    if sector == "industrials_capex":
        return bool(capex_pressure or energy_pressure or "pressure" in str(value(row, "dollar_exposure", "")))
    if sector == "consumer_platform":
        return bool(duration_pressure or "pressure" in str(value(row, "credit_exposure", "")))
    return bool(duration_pressure or funding_pressure or liquidity_high)


def refine_edge_type(original: str, blocker: bool, confirm: int, from_node: str) -> str:
    if from_node == "macro_context":
        return "diagnostic_context"
    if blocker:
        return "blocker"
    if confirm:
        return "confirmation_required"
    return original


def edge_tier(score: int, from_node: str) -> str:
    if from_node == "macro_context":
        return "proxy_only"
    if score >= 5:
        return "strong"
    if score >= 3:
        return "medium"
    return "weak"


def choose_weakest_layer(bundle: pd.Series, interp: pd.Series, edge: pd.Series, slot_row: pd.Series) -> str:
    if int(edge["blocker_edge_count"]) > 0:
        return "sector_edge_blocker"
    if int(edge["edge_weak_count"]) >= 2:
        return "relation_edge_weak"
    if int(slot_row["replacement_hurdle_required_flag"]) == 1:
        return "slot_replacement_hurdle"
    if int(interp["firm_grade_gap_count"]) >= 8 or int(interp["interpretation_weak_count"]) >= 3:
        return economic_weak_layer_from_gap(str(interp["dominant_interpretation_gap"]))
    if int(bundle["microstructure_pending_flag"]) == 1 and str(bundle["missing_evidence_flags"]) != "microstructure_feature_missing":
        return "evidence_quality_gap"
    return "context_bundle_review"


def next_action_for_weakest_layer(layer: str) -> str:
    mapping = {
        "evidence_microstructure_pending": "wait_for_microstructure_or_keep_diagnostic",
        "economic_customer_quality_gap": "extract_named_customer_and_counterparty_quality_from_source_text",
        "economic_cash_flow_bridge_gap": "extract_revenue_margin_backlog_conversion_bridge",
        "economic_priced_in_gap": "review_price_acceptance_and_what_is_already_priced",
        "economic_macro_certification_gap": "keep_macro_diagnostic_until_release_asof_certified",
        "economic_interpretation_weak": "extract_contract_customer_margin_surprise_from_source_text",
        "sector_edge_blocker": "review_sector_specific_blocker_and_invalidation",
        "relation_edge_weak": "upgrade_edge_transmission_logic_before_allocation",
        "slot_replacement_hurdle": "compare_same_timestamp_candidates_only",
        "context_bundle_review": "manual_candidate_packet_review",
    }
    return mapping.get(layer, "manual_review")


def dominant_gap_reason(values: pd.Series) -> str:
    counts: dict[str, int] = {}
    for raw in values:
        text = str(raw)
        if text == "no_major_quality_gap_detected":
            continue
        for token in text.split("|"):
            if token:
                counts[token] = counts.get(token, 0) + 1
    if not counts:
        return "no_major_quality_gap_detected"
    return max(counts.items(), key=lambda item: (item[1], item[0]))[0]


def economic_weak_layer_from_gap(gap: str) -> str:
    if "customer_quality" in gap:
        return "economic_customer_quality_gap"
    if "cash_flow_bridge" in gap or "contract_value" in gap:
        return "economic_cash_flow_bridge_gap"
    if "priced_in" in gap:
        return "economic_priced_in_gap"
    if "macro_assignment" in gap:
        return "economic_macro_certification_gap"
    return "economic_interpretation_weak"


def value(row: pd.Series, column: str, default: object = "") -> object:
    if column not in row.index:
        return default
    raw = row[column]
    if pd.isna(raw):
        return default
    return raw


def unique(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in values:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def select_columns_with_defaults(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    selected = frame.copy()
    for col in columns:
        if col not in selected.columns:
            selected[col] = 0
    return selected[columns]


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
    parser.add_argument("--task688-dir", type=Path, default=TASK688_DIR)
    args = parser.parse_args()
    build_task689_program(task684_dir=args.task684_dir, task688_dir=args.task688_dir)
    print(f"[Task689] wrote {TASK689_DIR}")


if __name__ == "__main__":
    main()
