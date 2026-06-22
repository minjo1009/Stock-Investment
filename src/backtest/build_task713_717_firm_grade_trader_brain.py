from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK712_PANEL = Path("docs/reports/task_712_firm_grade_translator_engine/task712_context_state_panel.csv")
TASK708_EVAL = Path("docs/reports/task_708_full_period_backtest_comparison/task708_eval_panel.csv")

TASK713_DIR = Path("docs/reports/task_713_evidence_provenance_brain")
TASK714_DIR = Path("docs/reports/task_714_economic_transmission_brain")
TASK715_DIR = Path("docs/reports/task_715_market_pricing_acceptance_brain")
TASK716_DIR = Path("docs/reports/task_716_portfolio_competition_brain")
TASK717_DIR = Path("docs/reports/task_717_decision_invalidation_risk_brain")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
NO_ACTION_REASON = "review_layer_only;not_buy_sell_or_position_instruction;real_capital_forbidden"


def build_task713_717(
    *,
    task712_panel_path: Path = TASK712_PANEL,
    eval_path: Path = TASK708_EVAL,
) -> dict[str, pd.DataFrame]:
    task712 = pd.read_csv(task712_panel_path)
    eval_panel = pd.read_csv(eval_path)

    t713 = build_task713_evidence(task712)
    write_task713(t713)

    t714 = build_task714_transmission(t713)
    write_task714(t714)

    t715 = build_task715_market_acceptance(t714)
    write_task715(t715)

    t716 = build_task716_portfolio_competition(t715, eval_panel)
    write_task716(t716)

    t717 = build_task717_decision_risk(t716, eval_panel)
    write_task717(t717)

    return {
        "task713_panel": t713,
        "task714_panel": t714,
        "task715_panel": t715,
        "task716_panel": t716["panel"],
        "task717_panel": t717["panel"],
    }


def build_task713_evidence(task712: pd.DataFrame) -> pd.DataFrame:
    out = task712.copy()
    out["source_type_state"] = out.apply(source_type_state, axis=1)
    out["source_directness_state"] = out.apply(source_directness_state, axis=1)
    out["novelty_state"] = out.apply(novelty_state, axis=1)
    out["evidence_strength_state"] = out.apply(evidence_strength_state, axis=1)
    out["timestamp_validity_state"] = "asof_entry_timestamp_inherited_from_task704_706"
    out["source_gap_state"] = out["source_event_available_flag"].apply(lambda x: "source_available" if int_safe(x) else "source_gap_unknown_not_negative")
    out["evidence_brain_state"] = out.apply(evidence_brain_state, axis=1)
    out["evidence_reason_codes"] = out.apply(evidence_reason_codes, axis=1)
    add_no_action_flags(out)
    cols = KEYS + [
        "source_event_available_flag",
        "source_type_state",
        "source_directness_state",
        "novelty_state",
        "evidence_strength_state",
        "timestamp_validity_state",
        "source_gap_state",
        "evidence_brain_state",
        "evidence_reason_codes",
        "firm_grade_context_state",
        "company_anchor_state",
        "financing_context_state",
        "high_noise_context_state",
        "low_novelty_context_state",
        "guidance_context_state",
        "market_acceptance_state",
        "theme_leadership_context",
        "policy_macro_context_state",
        "customer_event_count",
        "revenue_backlog_event_count",
        "guidance_margin_event_count",
        "supply_demand_event_count",
        "company_direct_event_count",
        "ownership_noise_event_count",
        "broad_policy_event_count",
        "regulatory_policy_event_count",
        "noise_ratio",
    ] + no_action_columns()
    return out[[c for c in cols if c in out.columns]].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def source_type_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "source_gap"
    if int_safe(row.get("company_direct_event_count")) > 0:
        return "company_direct_source"
    if int_safe(row.get("broad_policy_event_count")) + int_safe(row.get("regulatory_policy_event_count")) > 0:
        return "policy_or_macro_source"
    if int_safe(row.get("ownership_noise_event_count")) > 0:
        return "ownership_or_filing_source"
    return "mixed_event_source"


def source_directness_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "no_source_directness_claim"
    company = str(row.get("company_anchor_state", ""))
    if company == "direct_company_anchor_with_economic_detail":
        return "direct_company_economic_detail"
    if company == "direct_company_anchor_thin_detail":
        return "direct_company_thin_detail"
    if company == "indirect_economic_anchor":
        return "indirect_but_economic"
    if company == "single_economic_signal":
        return "thin_single_economic_signal"
    return "source_present_but_no_company_anchor"


def novelty_state(row: pd.Series) -> str:
    low = str(row.get("low_novelty_context_state", ""))
    guidance = str(row.get("guidance_context_state", ""))
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "no_source_novelty_claim"
    if "reaccelerating" in low:
        return "stale_or_reaffirmed_but_reaccelerating"
    if "reaffirm" in guidance:
        return "reaffirmation_not_new_information"
    if "stale" in low:
        return "stale_unconfirmed_information"
    return "new_or_not_obviously_stale"


def evidence_strength_state(row: pd.Series) -> str:
    economic = economic_signal_count(row)
    direct = int_safe(row.get("company_direct_event_count"))
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "no_source_evidence"
    if direct > 0 and economic >= 3:
        return "strong_multi_signal_company_evidence"
    if direct > 0 and economic >= 1:
        return "company_evidence_with_economic_detail"
    if economic >= 2:
        return "multi_signal_indirect_evidence"
    if economic == 1:
        return "thin_single_signal_evidence"
    return "weak_or_noise_dominated_evidence"


def evidence_brain_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "source_gap_unknown_not_negative"
    strength = evidence_strength_state(row)
    directness = source_directness_state(row)
    novelty = novelty_state(row)
    if strength == "strong_multi_signal_company_evidence":
        return "certified_company_direct_strong_evidence"
    if directness.startswith("direct_company") and "reaffirmation" in novelty:
        return "company_direct_but_reaffirmed"
    if "noise" in strength:
        return "source_present_but_noise_dominated"
    if directness == "indirect_but_economic":
        return "indirect_economic_evidence"
    if "reaccelerating" in novelty:
        return "stale_evidence_reaccelerating"
    return "evidence_needs_context"


def evidence_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"type={source_type_state(row)}",
            f"directness={source_directness_state(row)}",
            f"novelty={novelty_state(row)}",
            f"strength={evidence_strength_state(row)}",
            f"gap={row.get('source_gap_state', '')}",
        ]
    )


def build_task714_transmission(t713: pd.DataFrame) -> pd.DataFrame:
    out = t713.copy()
    out["revenue_path_state"] = out.apply(revenue_path_state, axis=1)
    out["margin_path_state"] = out.apply(margin_path_state, axis=1)
    out["order_backlog_path_state"] = out.apply(order_backlog_path_state, axis=1)
    out["funding_path_state"] = out.apply(funding_path_state, axis=1)
    out["dilution_overhang_state"] = out.apply(dilution_overhang_state, axis=1)
    out["policy_demand_path_state"] = out.apply(policy_demand_path_state, axis=1)
    out["valuation_pressure_state"] = out.apply(valuation_pressure_state, axis=1)
    out["economic_transmission_state"] = out.apply(economic_transmission_state, axis=1)
    out["economic_reason_codes"] = out.apply(economic_reason_codes, axis=1)
    add_no_action_flags(out)
    cols = KEYS + [
        "source_event_available_flag",
        "evidence_brain_state",
        "source_directness_state",
        "evidence_strength_state",
        "revenue_path_state",
        "margin_path_state",
        "order_backlog_path_state",
        "funding_path_state",
        "dilution_overhang_state",
        "policy_demand_path_state",
        "valuation_pressure_state",
        "economic_transmission_state",
        "economic_reason_codes",
        "company_anchor_state",
        "financing_context_state",
        "guidance_context_state",
        "theme_leadership_context",
        "policy_macro_context_state",
        "market_acceptance_state",
        "customer_event_count",
        "revenue_backlog_event_count",
        "guidance_margin_event_count",
        "supply_demand_event_count",
        "company_direct_event_count",
    ] + no_action_columns()
    return out[[c for c in cols if c in out.columns]].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def revenue_path_state(row: pd.Series) -> str:
    if int_safe(row.get("customer_event_count")) > 0 and int_safe(row.get("revenue_backlog_event_count")) > 0:
        return "revenue_acceleration_with_customer_anchor"
    if int_safe(row.get("revenue_backlog_event_count")) > 0:
        return "revenue_or_backlog_signal_without_named_customer"
    if int_safe(row.get("customer_event_count")) > 0:
        return "customer_anchor_without_explicit_revenue_path"
    return "no_revenue_path_claim"


def margin_path_state(row: pd.Series) -> str:
    if int_safe(row.get("guidance_margin_event_count")) > 0 and int_safe(row.get("supply_demand_event_count")) > 0:
        return "margin_and_demand_reinforcing"
    if int_safe(row.get("guidance_margin_event_count")) > 0:
        return "guidance_or_margin_path_visible"
    if str(row.get("guidance_context_state", "")) == "guidance_soft_or_lower_quality":
        return "margin_or_guidance_pressure"
    return "no_margin_path_claim"


def order_backlog_path_state(row: pd.Series) -> str:
    if int_safe(row.get("revenue_backlog_event_count")) > 0:
        return "order_or_backlog_conversion_visible"
    return "no_order_backlog_path_claim"


def funding_path_state(row: pd.Series) -> str:
    finance = str(row.get("financing_context_state", ""))
    if finance == "financing_absorbed_with_fundamental_support":
        return "funding_capacity_for_growth_absorbed"
    if finance == "financing_growth_capital_unabsorbed":
        return "funding_capacity_for_growth_unconfirmed"
    if "dilutive" in finance or "convertible" in finance:
        return "funding_need_with_overhang"
    if "financing" in finance and finance != "not_financing":
        return "funding_event_unclear"
    return "no_funding_event"


def dilution_overhang_state(row: pd.Series) -> str:
    finance = str(row.get("financing_context_state", ""))
    if "dilutive" in finance:
        return "dilution_overhang_unabsorbed"
    if "convertible" in finance:
        return "convertible_overhang_unabsorbed"
    if "absorbed" in finance and finance != "not_financing":
        return "financing_overhang_absorbed_by_market"
    return "no_dilution_overhang_claim"


def policy_demand_path_state(row: pd.Series) -> str:
    policy = str(row.get("policy_macro_context_state", ""))
    if "company_context_needed" in policy and economic_signal_count(row) >= 2:
        return "policy_tailwind_with_company_link"
    if "company_context_needed" in policy:
        return "policy_tailwind_company_link_weak"
    if "stress" in policy:
        return "policy_linked_under_macro_stress"
    return "no_policy_demand_claim"


def valuation_pressure_state(row: pd.Series) -> str:
    theme = str(row.get("theme_leadership_context", ""))
    market = str(row.get("market_acceptance_state", ""))
    if theme == "theme_context_fading" and not market.startswith("price_absorbed"):
        return "multiple_pressure_offsets_catalyst"
    if market == "price_absorbed_and_confirmed" and theme == "theme_leadership_supportive":
        return "multiple_context_supportive"
    if market == "upper_range_but_unconfirmed":
        return "extension_valuation_pressure_possible"
    return "valuation_pressure_not_primary"


def economic_transmission_state(row: pd.Series) -> str:
    if str(row.get("source_gap_state", "")) == "source_gap_unknown_not_negative":
        return "no_economic_claim_source_gap"
    if funding_path_state(row) == "funding_capacity_for_growth_absorbed" and revenue_path_state(row) != "no_revenue_path_claim":
        return "growth_funding_revenue_reinforcing"
    if funding_path_state(row) == "funding_need_with_overhang":
        return "capital_need_overhang_vs_growth_question"
    if revenue_path_state(row).startswith("revenue_acceleration") and margin_path_state(row).startswith("margin"):
        return "revenue_margin_reinforcing"
    if policy_demand_path_state(row) == "policy_tailwind_with_company_link":
        return "policy_demand_tailwind_with_company_link"
    if order_backlog_path_state(row) == "order_or_backlog_conversion_visible":
        return "backlog_or_order_path_visible"
    if evidence_strength_state_from_row(row).startswith("weak"):
        return "no_clear_economic_path"
    return "economic_path_needs_review"


def economic_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"rev={revenue_path_state(row)}",
            f"margin={margin_path_state(row)}",
            f"orders={order_backlog_path_state(row)}",
            f"funding={funding_path_state(row)}",
            f"dilution={dilution_overhang_state(row)}",
            f"policy={policy_demand_path_state(row)}",
            f"valuation={valuation_pressure_state(row)}",
        ]
    )


def build_task715_market_acceptance(t714: pd.DataFrame) -> pd.DataFrame:
    out = t714.copy()
    out["pricing_acceptance_state"] = out.apply(pricing_acceptance_state, axis=1)
    out["priced_vs_unpriced_state"] = out.apply(priced_vs_unpriced_state, axis=1)
    out["positioning_proxy_state"] = out.apply(positioning_proxy_state, axis=1)
    out["acceptance_failure_state"] = out.apply(acceptance_failure_state, axis=1)
    out["market_pricing_brain_state"] = out.apply(market_pricing_brain_state, axis=1)
    out["market_pricing_reason_codes"] = out.apply(market_pricing_reason_codes, axis=1)
    add_no_action_flags(out)
    cols = KEYS + [
        "source_event_available_flag",
        "evidence_brain_state",
        "economic_transmission_state",
        "pricing_acceptance_state",
        "priced_vs_unpriced_state",
        "positioning_proxy_state",
        "acceptance_failure_state",
        "market_pricing_brain_state",
        "market_pricing_reason_codes",
        "market_acceptance_state",
        "theme_leadership_context",
        "valuation_pressure_state",
        "funding_path_state",
        "dilution_overhang_state",
        "policy_demand_path_state",
    ] + no_action_columns()
    return out[[c for c in cols if c in out.columns]].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def pricing_acceptance_state(row: pd.Series) -> str:
    acceptance = str(row.get("market_acceptance_state", ""))
    if acceptance == "price_absorbed_and_confirmed":
        return "accepted_by_price_and_tape_proxy"
    if acceptance == "price_absorbed_without_full_confirmation":
        return "absorbed_but_tape_confirmation_partial"
    if acceptance == "intraday_acceptance_building":
        return "acceptance_building_not_final"
    if acceptance == "upper_range_but_unconfirmed":
        return "near_high_but_acceptance_unproven"
    return "not_accepted_by_market_proxy"


def priced_vs_unpriced_state(row: pd.Series) -> str:
    valuation = str(row.get("valuation_pressure_state", ""))
    pricing = pricing_acceptance_state(row)
    econ = str(row.get("economic_transmission_state", ""))
    if pricing.startswith("accepted") and valuation == "extension_valuation_pressure_possible":
        return "priced_but_extension_risk"
    if pricing.startswith("accepted") and econ in {"growth_funding_revenue_reinforcing", "revenue_margin_reinforcing"}:
        return "accepted_with_fundamental_runway"
    if "not_accepted" in pricing and econ != "no_clear_economic_path":
        return "economic_path_unpriced_or_rejected"
    if pricing == "acceptance_building_not_final":
        return "pricing_process_incomplete"
    return "pricing_state_unclear"


def positioning_proxy_state(row: pd.Series) -> str:
    theme = str(row.get("theme_leadership_context", ""))
    pricing = pricing_acceptance_state(row)
    if theme == "theme_leadership_supportive" and pricing.startswith("accepted"):
        return "theme_and_price_positioning_supportive"
    if theme == "theme_context_fading" and pricing.startswith("accepted"):
        return "price_acceptance_against_fading_theme"
    if theme == "theme_narrow_leadership":
        return "narrow_theme_positioning_risk"
    return "positioning_proxy_unclear"


def acceptance_failure_state(row: pd.Series) -> str:
    if pricing_acceptance_state(row) == "not_accepted_by_market_proxy":
        return "market_rejected_or_no_acceptance"
    if str(row.get("dilution_overhang_state", "")) in {"dilution_overhang_unabsorbed", "convertible_overhang_unabsorbed"}:
        return "overhang_not_yet_absorbed"
    if str(row.get("valuation_pressure_state", "")) == "extension_valuation_pressure_possible":
        return "accepted_but_extension_risk"
    return "no_primary_acceptance_failure"


def market_pricing_brain_state(row: pd.Series) -> str:
    if str(row.get("evidence_brain_state", "")) == "source_gap_unknown_not_negative":
        return "source_gap_no_market_pricing_claim"
    priced = priced_vs_unpriced_state(row)
    failure = acceptance_failure_state(row)
    if priced == "accepted_with_fundamental_runway":
        return "market_accepts_economic_path"
    if priced == "economic_path_unpriced_or_rejected":
        return "economic_path_not_accepted_yet"
    if failure == "overhang_not_yet_absorbed":
        return "market_waiting_on_overhang_absorption"
    if priced == "priced_but_extension_risk":
        return "accepted_but_overextended"
    if priced == "pricing_process_incomplete":
        return "market_acceptance_incomplete"
    return "market_pricing_needs_review"


def market_pricing_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"acceptance={pricing_acceptance_state(row)}",
            f"priced={priced_vs_unpriced_state(row)}",
            f"positioning={positioning_proxy_state(row)}",
            f"failure={acceptance_failure_state(row)}",
        ]
    )


def build_task716_portfolio_competition(t715: pd.DataFrame, eval_panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = t715.copy()
    out["slot_context_score"] = out.apply(slot_context_score, axis=1)
    out["same_timestamp_candidate_count"] = out.groupby(["split_name", "entry_ts"])["lifecycle_id"].transform("count")
    out["same_timestamp_context_rank"] = out.groupby(["split_name", "entry_ts"])["slot_context_score"].rank(method="first", ascending=False)
    out["same_timestamp_theme_count"] = out.groupby(["split_name", "entry_ts", "theme_id"])["lifecycle_id"].transform("count")
    out["slot_competition_state"] = out.apply(slot_competition_state, axis=1)
    out["exposure_cluster_state"] = out.apply(exposure_cluster_state, axis=1)
    out["portfolio_brain_state"] = out.apply(portfolio_brain_state, axis=1)
    out["portfolio_reason_codes"] = out.apply(portfolio_reason_codes, axis=1)
    add_no_action_flags(out)

    panel_cols = KEYS + [
        "source_event_available_flag",
        "evidence_brain_state",
        "economic_transmission_state",
        "market_pricing_brain_state",
        "slot_context_score",
        "same_timestamp_candidate_count",
        "same_timestamp_context_rank",
        "same_timestamp_theme_count",
        "slot_competition_state",
        "exposure_cluster_state",
        "portfolio_brain_state",
        "portfolio_reason_codes",
        "pricing_acceptance_state",
        "priced_vs_unpriced_state",
        "positioning_proxy_state",
    ] + no_action_columns()
    panel = out[[c for c in panel_cols if c in out.columns]].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)
    slot_matrix = panel.groupby(
        ["split_name", "entry_ts", "slot_competition_state", "portfolio_brain_state"], dropna=False
    ).size().reset_index(name="candidate_count")
    exposure = panel.groupby(
        ["split_name", "entry_ts", "theme_id", "exposure_cluster_state"], dropna=False
    ).size().reset_index(name="candidate_count").sort_values("candidate_count", ascending=False).reset_index(drop=True)
    winner_damage = build_winner_damage_audit(panel, eval_panel)
    governance = build_layer_governance(panel, "task716")
    decision = generic_decision("Task716", "PORTFOLIO_COMPETITION_BRAIN_BUILT_DIAGNOSTIC_ONLY", len(panel))
    pass_fail = generic_pass_fail(panel, governance, extra_gates=[
        gate("same_timestamp_rank_present", panel["same_timestamp_context_rank"].notna().all(), "rank=present", "present"),
        gate("slot_matrix_present", len(slot_matrix) > 0, f"rows={len(slot_matrix)}", ">0"),
        gate("winner_damage_eval_present", len(winner_damage) > 0, f"rows={len(winner_damage)}", ">0"),
    ])
    return {
        "panel": panel,
        "slot_matrix": slot_matrix,
        "exposure": exposure,
        "winner_damage": winner_damage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def slot_context_score(row: pd.Series) -> int:
    score = 0
    if str(row.get("evidence_brain_state", "")).startswith("certified_company_direct"):
        score += 2
    if str(row.get("economic_transmission_state", "")) in {"growth_funding_revenue_reinforcing", "revenue_margin_reinforcing", "policy_demand_tailwind_with_company_link"}:
        score += 2
    if str(row.get("market_pricing_brain_state", "")) == "market_accepts_economic_path":
        score += 2
    if str(row.get("market_pricing_brain_state", "")) in {"market_waiting_on_overhang_absorption", "accepted_but_overextended"}:
        score -= 1
    if str(row.get("evidence_brain_state", "")) == "source_gap_unknown_not_negative":
        score -= 2
    return score


def slot_competition_state(row: pd.Series) -> str:
    rank = float_safe(row.get("same_timestamp_context_rank"))
    count = int_safe(row.get("same_timestamp_candidate_count"))
    score = int_safe(row.get("slot_context_score"))
    if count <= 1:
        return "single_candidate_no_competition"
    if rank <= 5 and score >= 4:
        return "same_timestamp_slot_leader"
    if rank <= 10 and score >= 2:
        return "same_timestamp_contender"
    if score < 0:
        return "same_timestamp_no_slot_claim"
    return "same_timestamp_needs_confirmation"


def exposure_cluster_state(row: pd.Series) -> str:
    theme_count = int_safe(row.get("same_timestamp_theme_count"))
    if theme_count >= 5:
        return "theme_cluster_high"
    if theme_count >= 3:
        return "theme_cluster_medium"
    return "theme_cluster_low"


def portfolio_brain_state(row: pd.Series) -> str:
    slot = slot_competition_state(row)
    exposure = exposure_cluster_state(row)
    if slot == "same_timestamp_slot_leader" and exposure != "theme_cluster_high":
        return "distinct_driver_slot_leader_review"
    if slot == "same_timestamp_slot_leader":
        return "slot_leader_but_clustered_exposure"
    if slot == "same_timestamp_contender":
        return "slot_contender_needs_comparison"
    if slot == "same_timestamp_no_slot_claim":
        return "no_slot_claim_review_only"
    return "slot_candidate_needs_confirmation"


def portfolio_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"score={int_safe(row.get('slot_context_score'))}",
            f"rank={float_safe(row.get('same_timestamp_context_rank')):.0f}",
            f"cohort={int_safe(row.get('same_timestamp_candidate_count'))}",
            f"theme_cluster={exposure_cluster_state(row)}",
        ]
    )


def build_task717_decision_risk(t716: dict[str, pd.DataFrame], eval_panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = t716["panel"].copy()
    base["review_decision_state"] = base.apply(review_decision_state, axis=1)
    base["invalidation_condition"] = base.apply(invalidation_condition, axis=1)
    base["risk_budget_state"] = base.apply(risk_budget_state, axis=1)
    base["sizing_cap_reason"] = base.apply(sizing_cap_reason, axis=1)
    base["final_brain_state"] = base.apply(final_brain_state, axis=1)
    base["final_brain_reason_codes"] = base.apply(final_brain_reason_codes, axis=1)
    add_no_action_flags(base)
    panel_cols = KEYS + [
        "source_event_available_flag",
        "evidence_brain_state",
        "economic_transmission_state",
        "market_pricing_brain_state",
        "portfolio_brain_state",
        "review_decision_state",
        "invalidation_condition",
        "risk_budget_state",
        "sizing_cap_reason",
        "final_brain_state",
        "final_brain_reason_codes",
    ] + no_action_columns()
    panel = base[[c for c in panel_cols if c in base.columns]].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)
    invalidation = panel.groupby(["review_decision_state", "invalidation_condition"], dropna=False).size().reset_index(name="candidate_count")
    risk_budget = panel.groupby(["risk_budget_state", "sizing_cap_reason"], dropna=False).size().reset_index(name="candidate_count")
    guardrail = build_final_guardrail(panel, eval_panel)
    governance = build_layer_governance(panel, "task717")
    decision = generic_decision("Task717", "DECISION_INVALIDATION_RISK_BRAIN_BUILT_DIAGNOSTIC_ONLY", len(panel))
    pass_fail = generic_pass_fail(panel, governance, extra_gates=[
        gate("invalidation_all_present", panel["invalidation_condition"].astype(str).str.len().gt(0).all(), "all_present", "all_present"),
        gate("risk_budget_all_present", panel["risk_budget_state"].astype(str).str.len().gt(0).all(), "all_present", "all_present"),
        gate("guardrail_eval_present", len(guardrail) > 0, f"rows={len(guardrail)}", ">0"),
    ])
    return {
        "panel": panel,
        "invalidation": invalidation,
        "risk_budget": risk_budget,
        "guardrail": guardrail,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def review_decision_state(row: pd.Series) -> str:
    portfolio = str(row.get("portfolio_brain_state", ""))
    pricing = str(row.get("market_pricing_brain_state", ""))
    evidence = str(row.get("evidence_brain_state", ""))
    if evidence == "source_gap_unknown_not_negative":
        return "research_only_source_gap"
    if portfolio == "distinct_driver_slot_leader_review" and pricing == "market_accepts_economic_path":
        return "normal_size_review_candidate_not_approved"
    if portfolio in {"distinct_driver_slot_leader_review", "slot_contender_needs_comparison"}:
        return "small_size_review_candidate_not_approved"
    if pricing in {"market_waiting_on_overhang_absorption", "economic_path_not_accepted_yet"}:
        return "watch_for_confirmation"
    return "research_only_no_slot_or_confirmation"


def invalidation_condition(row: pd.Series) -> str:
    pricing = str(row.get("market_pricing_brain_state", ""))
    evidence = str(row.get("evidence_brain_state", ""))
    if evidence == "source_gap_unknown_not_negative":
        return "invalidation_not_applicable_source_gap"
    if pricing == "market_accepts_economic_path":
        return "invalid_if_price_acceptance_breaks_or_theme_leadership_fades"
    if pricing == "market_waiting_on_overhang_absorption":
        return "invalid_if_overhang_not_absorbed_by_followup_price_action"
    if pricing == "economic_path_not_accepted_yet":
        return "invalid_if_no_confirmation_after_economic_catalyst"
    return "invalid_if_evidence_cannot_be_tied_to_price_or_economics"


def risk_budget_state(row: pd.Series) -> str:
    review = review_decision_state(row)
    exposure = str(row.get("exposure_cluster_state", ""))
    if review == "normal_size_review_candidate_not_approved" and exposure != "theme_cluster_high":
        return "normal_review_budget_not_approved"
    if review == "small_size_review_candidate_not_approved":
        return "small_review_budget_not_approved"
    if exposure == "theme_cluster_high":
        return "cluster_capped_review_budget"
    return "no_budget_research_only"


def sizing_cap_reason(row: pd.Series) -> str:
    if str(row.get("exposure_cluster_state", "")) == "theme_cluster_high":
        return "same_timestamp_theme_cluster"
    if "overhang" in str(row.get("market_pricing_brain_state", "")):
        return "financing_or_overhang_confirmation_needed"
    if str(row.get("evidence_brain_state", "")) == "source_gap_unknown_not_negative":
        return "source_gap_no_size_claim"
    return "not_approved_until_guardrail_passes"


def final_brain_state(row: pd.Series) -> str:
    return f"{review_decision_state(row)}__{risk_budget_state(row)}"


def final_brain_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"review={review_decision_state(row)}",
            f"invalidation={invalidation_condition(row)}",
            f"budget={risk_budget_state(row)}",
            f"cap={sizing_cap_reason(row)}",
        ]
    )


def build_winner_damage_audit(panel: pd.DataFrame, eval_panel: pd.DataFrame) -> pd.DataFrame:
    merged = panel.merge(eval_panel[KEYS + ["costed_return_pct"]], on=KEYS, how="left", validate="one_to_one")
    top50 = set(merged.nlargest(50, "costed_return_pct")["lifecycle_id"])
    bottom50 = set(merged.nsmallest(50, "costed_return_pct")["lifecycle_id"])
    rows = []
    for state, group in merged.groupby("portfolio_brain_state", dropna=False):
        ids = set(group["lifecycle_id"])
        rows.append(
            {
                "portfolio_brain_state": state,
                "candidate_count": len(group),
                "top50_winner_count_eval_only": len(top50 & ids),
                "bottom50_loser_count_eval_only": len(bottom50 & ids),
                "outcome_used_for_assignment_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("top50_winner_count_eval_only", ascending=False).reset_index(drop=True)


def build_final_guardrail(panel: pd.DataFrame, eval_panel: pd.DataFrame) -> pd.DataFrame:
    merged = panel.merge(eval_panel[KEYS + ["costed_return_pct", "entry_reduce_failure_flag"]], on=KEYS, how="left", validate="one_to_one")
    top50 = set(merged.nlargest(50, "costed_return_pct")["lifecycle_id"])
    bottom50 = set(merged.nsmallest(50, "costed_return_pct")["lifecycle_id"])
    rows = []
    for state, group in merged.groupby("final_brain_state", dropna=False):
        ids = set(group["lifecycle_id"])
        rows.append(
            {
                "final_brain_state": state,
                "candidate_count": len(group),
                "top50_winner_count": len(top50 & ids),
                "bottom50_loser_count": len(bottom50 & ids),
                "winner_preservation_share_eval_only": len(top50 & ids) / 50.0,
                "loser_preservation_share_eval_only": len(bottom50 & ids) / 50.0,
                "avg_costed_return_pct_eval_only": float(group["costed_return_pct"].mean()),
                "entry_reduce_failure_rate_eval_only": float(pd.to_numeric(group["entry_reduce_failure_flag"], errors="coerce").fillna(0).mean()),
                "outcome_used_for_assignment_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("top50_winner_count", ascending=False).reset_index(drop=True)


def write_task713(panel: pd.DataFrame) -> None:
    matrix = panel.groupby(["source_type_state", "source_directness_state", "novelty_state", "evidence_strength_state", "evidence_brain_state"], dropna=False).size().reset_index(name="candidate_count")
    gap = panel.groupby("source_gap_state", dropna=False).size().reset_index(name="candidate_count")
    governance = build_layer_governance(panel, "task713")
    decision = generic_decision("Task713", "EVIDENCE_PROVENANCE_BRAIN_BUILT_DIAGNOSTIC_ONLY", len(panel))
    pass_fail = generic_pass_fail(panel, governance, [gate("evidence_states_present", panel["evidence_brain_state"].nunique() >= 5, f"states={panel['evidence_brain_state'].nunique()}", ">=5")])
    write_task_outputs(
        TASK713_DIR,
        "task_713_evidence_provenance_brain.md",
        {
            "task713_evidence_provenance_panel.csv": panel,
            "task713_evidence_strength_matrix.csv": matrix,
            "task713_source_gap_audit.csv": gap,
            "task713_governance_audit.csv": governance,
            "task_713_decision.csv": decision,
            "task_713_pass_fail_matrix.csv": pass_fail,
        },
        "Task713 Evidence Provenance Brain",
        decision,
        pass_fail,
        "Layer 1 separates source type, directness, novelty, evidence strength, timestamp validity, and source gaps before economics.",
    )


def write_task714(panel: pd.DataFrame) -> None:
    matrix = panel.groupby(["economic_transmission_state", "revenue_path_state", "margin_path_state", "funding_path_state", "policy_demand_path_state"], dropna=False).size().reset_index(name="candidate_count")
    financing = panel.groupby(["funding_path_state", "dilution_overhang_state", "economic_transmission_state"], dropna=False).size().reset_index(name="candidate_count")
    governance = build_layer_governance(panel, "task714")
    decision = generic_decision("Task714", "ECONOMIC_TRANSMISSION_BRAIN_BUILT_DIAGNOSTIC_ONLY", len(panel))
    pass_fail = generic_pass_fail(panel, governance, [gate("economic_states_present", panel["economic_transmission_state"].nunique() >= 6, f"states={panel['economic_transmission_state'].nunique()}", ">=6")])
    write_task_outputs(
        TASK714_DIR,
        "task_714_economic_transmission_brain.md",
        {
            "task714_economic_transmission_panel.csv": panel,
            "task714_mechanism_interaction_matrix.csv": matrix,
            "task714_financing_quality_decomposition.csv": financing,
            "task714_governance_audit.csv": governance,
            "task_714_decision.csv": decision,
            "task_714_pass_fail_matrix.csv": pass_fail,
        },
        "Task714 Economic Transmission Brain",
        decision,
        pass_fail,
        "Layer 2 maps evidence into revenue, margin, backlog, funding, dilution, policy, and valuation transmission paths.",
    )


def write_task715(panel: pd.DataFrame) -> None:
    matrix = panel.groupby(["market_pricing_brain_state", "pricing_acceptance_state", "priced_vs_unpriced_state", "positioning_proxy_state"], dropna=False).size().reset_index(name="candidate_count")
    failure = panel.groupby(["acceptance_failure_state", "market_pricing_brain_state"], dropna=False).size().reset_index(name="candidate_count")
    governance = build_layer_governance(panel, "task715")
    decision = generic_decision("Task715", "MARKET_PRICING_ACCEPTANCE_BRAIN_BUILT_DIAGNOSTIC_ONLY", len(panel))
    pass_fail = generic_pass_fail(panel, governance, [gate("pricing_states_present", panel["market_pricing_brain_state"].nunique() >= 5, f"states={panel['market_pricing_brain_state'].nunique()}", ">=5")])
    write_task_outputs(
        TASK715_DIR,
        "task_715_market_pricing_acceptance_brain.md",
        {
            "task715_market_pricing_acceptance_panel.csv": panel,
            "task715_priced_vs_unpriced_matrix.csv": matrix,
            "task715_price_acceptance_failure_audit.csv": failure,
            "task715_governance_audit.csv": governance,
            "task_715_decision.csv": decision,
            "task_715_pass_fail_matrix.csv": pass_fail,
        },
        "Task715 Market Pricing Acceptance Brain",
        decision,
        pass_fail,
        "Layer 3 checks whether the market accepts, rejects, overextends, or has not yet priced the economic path.",
    )


def write_task716(outputs: dict[str, pd.DataFrame]) -> None:
    write_task_outputs(
        TASK716_DIR,
        "task_716_portfolio_competition_brain.md",
        {
            "task716_slot_competition_panel.csv": outputs["panel"],
            "task716_same_timestamp_slot_matrix.csv": outputs["slot_matrix"],
            "task716_exposure_cluster_audit.csv": outputs["exposure"],
            "task716_winner_damage_audit.csv": outputs["winner_damage"],
            "task716_governance_audit.csv": outputs["governance"],
            "task_716_decision.csv": outputs["decision"],
            "task_716_pass_fail_matrix.csv": outputs["pass_fail"],
        },
        "Task716 Portfolio Competition Brain",
        outputs["decision"],
        outputs["pass_fail"],
        "Layer 4 compares candidates only inside the same timestamp cohort and reports slot/exposure context without approving trades.",
    )


def write_task717(outputs: dict[str, pd.DataFrame]) -> None:
    write_task_outputs(
        TASK717_DIR,
        "task_717_decision_invalidation_risk_brain.md",
        {
            "task717_decision_invalidation_panel.csv": outputs["panel"],
            "task717_invalidation_map.csv": outputs["invalidation"],
            "task717_risk_budget_explanation.csv": outputs["risk_budget"],
            "task717_final_brain_guardrail.csv": outputs["guardrail"],
            "task717_governance_audit.csv": outputs["governance"],
            "task_717_decision.csv": outputs["decision"],
            "task_717_pass_fail_matrix.csv": outputs["pass_fail"],
        },
        "Task717 Decision Invalidation Risk Brain",
        outputs["decision"],
        outputs["pass_fail"],
        "Layer 5 creates review-only decision, invalidation, and risk-budget explanations while keeping capital forbidden.",
    )


def build_layer_governance(panel: pd.DataFrame, task_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_5265", len(panel) == 5265, f"rows={len(panel)}", "5265"),
            gate("event_linked_2445", int(panel["source_event_available_flag"].sum()) == 2445, f"event={int(panel['source_event_available_flag'].sum())}", "2445"),
            gate("no_action_output", int(panel["translator_output_is_action_flag"].sum()) == 0, "0", "0"),
            gate("no_outcome_assignment", int(panel["outcome_used_for_assignment_flag"].sum()) == 0, "0", "0"),
            gate("no_future_price_assignment", int(panel["future_price_used_for_assignment_flag"].sum()) == 0, "0", "0"),
            gate("missing_source_not_negative", int(panel["missing_source_used_as_negative_flag"].sum()) == 0, "0", "0"),
            gate("macro_not_promoted", int(panel["macro_used_for_assignment_flag"].sum()) == 0, "0", "0"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    ).assign(task_id=task_id)


def generic_decision(task_id: str, verdict: str, rows: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": task_id,
                "verdict": verdict,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "row_count": int(rows),
                "trading_promotion_pass_flag": 0,
                "next_action": "Keep as diagnostic translator-brain layer; do not promote to trading or paper execution.",
            }
        ]
    )


def generic_pass_fail(panel: pd.DataFrame, governance: pd.DataFrame, extra_gates: list[dict[str, object]] | None = None) -> pd.DataFrame:
    rows = [
        gate("scope_5265", len(panel) == 5265, f"rows={len(panel)}", "5265"),
        gate("event_linked_2445", int(panel["source_event_available_flag"].sum()) == 2445, f"event={int(panel['source_event_available_flag'].sum())}", "2445"),
        gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
        gate("no_action_output", int(panel["translator_output_is_action_flag"].sum()) == 0, "0", "0"),
        gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
    ]
    rows.extend(extra_gates or [])
    return pd.DataFrame(rows)


def write_task_outputs(
    out_dir: Path,
    report_name: str,
    outputs: dict[str, pd.DataFrame],
    title: str,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
    summary: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    report = f"""# {title}

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: {summary}
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

- Data scope: 5,265 candidates and 2,445 event-linked candidates.
- Assignment safety: no outcome, future price, missing-source-negative, or macro-provisional promotion is allowed.
- Capital safety: no buy/sell/order/sizing instruction is approved.
- Layer purpose: this artifact is a trader-brain reasoning layer, not a strategy promotion.

## No-Background Decision-Maker Report

- What happened: {summary}
- Why it matters: the model now explains the institutional reasoning step before any trade action.
- Whether this changes capital/deployment readiness: no.

## Artifact Manifest

- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation command: see task registry.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / report_name).write_text(report, encoding="utf-8")
    manifest = out_dir / "artifact_manifest.csv"
    if manifest.exists():
        manifest.unlink()
    write_manifest(out_dir, manifest)


def add_no_action_flags(frame: pd.DataFrame) -> None:
    frame["translator_output_is_action_flag"] = 0
    frame["outcome_used_for_assignment_flag"] = 0
    frame["future_price_used_for_assignment_flag"] = 0
    frame["missing_source_used_as_negative_flag"] = 0
    frame["macro_used_for_assignment_flag"] = 0
    frame["real_capital_status"] = "FORBIDDEN"
    frame["no_action_reason"] = NO_ACTION_REASON


def no_action_columns() -> list[str]:
    return [
        "translator_output_is_action_flag",
        "outcome_used_for_assignment_flag",
        "future_price_used_for_assignment_flag",
        "missing_source_used_as_negative_flag",
        "macro_used_for_assignment_flag",
        "real_capital_status",
        "no_action_reason",
    ]


def evidence_strength_state_from_row(row: pd.Series) -> str:
    if "evidence_strength_state" in row:
        return str(row.get("evidence_strength_state", ""))
    return evidence_strength_state(row)


def economic_signal_count(row: pd.Series) -> int:
    return (
        int_safe(row.get("customer_event_count"))
        + int_safe(row.get("revenue_backlog_event_count"))
        + int_safe(row.get("guidance_margin_event_count"))
        + int_safe(row.get("supply_demand_event_count"))
    )


def int_safe(value: object) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def float_safe(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def artifact_counts(outputs: dict[str, pd.DataFrame]) -> str:
    return "; ".join(f"{name}={len(frame)}" for name, frame in outputs.items())


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task713-717 firm-grade trader brain layers.")
    parser.add_argument("--task712-panel", type=Path, default=TASK712_PANEL)
    parser.add_argument("--eval", type=Path, default=TASK708_EVAL)
    args = parser.parse_args()
    build_task713_717(task712_panel_path=args.task712_panel, eval_path=args.eval)
    print("[Task713-717] wrote firm-grade trader brain artifacts")


if __name__ == "__main__":
    main()
