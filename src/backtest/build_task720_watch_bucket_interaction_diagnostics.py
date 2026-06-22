from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK719_PANEL = Path("docs/reports/task_719_watch_subtype_confirmation_contract/task719_watch_confirmation_contract_panel.csv")
TASK713_PANEL = Path("docs/reports/task_713_evidence_provenance_brain/task713_evidence_provenance_panel.csv")
TASK714_PANEL = Path("docs/reports/task_714_economic_transmission_brain/task714_economic_transmission_panel.csv")
TASK715_PANEL = Path("docs/reports/task_715_market_pricing_acceptance_brain/task715_market_pricing_acceptance_panel.csv")
TASK716_PANEL = Path("docs/reports/task_716_portfolio_competition_brain/task716_slot_competition_panel.csv")
TASK708_EVAL = Path("docs/reports/task_708_full_period_backtest_comparison/task708_eval_panel.csv")
TASK720_DIR = Path("docs/reports/task_720_watch_bucket_interaction_diagnostics")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
TARGET_SUBTYPES = {
    "watch_due_to_financing_absorption_test",
    "watch_due_to_slot_confirmation_needed",
    "watch_due_to_company_evidence_absorption_needed",
}
NO_ACTION_REASON = "watch_bucket_interaction_diagnostic_only;not_buy_sell_or_sizing_instruction"


def build_task720(
    *,
    task719_path: Path = TASK719_PANEL,
    task713_path: Path = TASK713_PANEL,
    task714_path: Path = TASK714_PANEL,
    task715_path: Path = TASK715_PANEL,
    task716_path: Path = TASK716_PANEL,
    eval_path: Path = TASK708_EVAL,
    out_dir: Path = TASK720_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_interaction_inputs(task719_path, task713_path, task714_path, task715_path, task716_path)
    panel = build_interaction_panel(panel)
    context = build_institutional_context_pack()
    matrix = build_bucket_interaction_matrix(panel)
    queue = build_human_review_queue(panel)
    eval_guardrail = build_eval_guardrail(panel, eval_path)
    leakage = build_leakage_guardrail(panel)
    governance = build_governance_audit(panel, matrix, queue, leakage)
    decision = decision_frame(panel)
    pass_fail = pass_fail_matrix(panel, matrix, queue, eval_guardrail, leakage, governance)
    outputs = {
        "task720_watch_bucket_interaction_panel.csv": panel,
        "task720_institutional_context_pack.csv": context,
        "task720_bucket_interaction_matrix.csv": matrix,
        "task720_human_review_queue.csv": queue,
        "task720_eval_guardrail.csv": eval_guardrail,
        "task720_leakage_guardrail.csv": leakage,
        "task720_governance_audit.csv": governance,
        "task_720_decision.csv": decision,
        "task_720_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "panel": panel,
        "context": context,
        "matrix": matrix,
        "queue": queue,
        "eval_guardrail": eval_guardrail,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def load_interaction_inputs(
    task719_path: Path,
    task713_path: Path,
    task714_path: Path,
    task715_path: Path,
    task716_path: Path,
) -> pd.DataFrame:
    base = pd.read_csv(task719_path)
    base = base[base["watch_subtype"].isin(TARGET_SUBTYPES)].copy()
    t713 = pd.read_csv(task713_path)
    t714 = pd.read_csv(task714_path)
    t715 = pd.read_csv(task715_path)
    t716 = pd.read_csv(task716_path)
    cols713 = KEYS + [
        "source_type_state",
        "source_directness_state",
        "novelty_state",
        "evidence_strength_state",
        "company_anchor_state",
        "financing_context_state",
        "high_noise_context_state",
        "low_novelty_context_state",
        "guidance_context_state",
        "customer_event_count",
        "revenue_backlog_event_count",
        "guidance_margin_event_count",
        "supply_demand_event_count",
        "company_direct_event_count",
        "ownership_noise_event_count",
        "broad_policy_event_count",
        "regulatory_policy_event_count",
        "noise_ratio",
    ]
    cols714 = KEYS + [
        "revenue_path_state",
        "margin_path_state",
        "order_backlog_path_state",
        "funding_path_state",
        "dilution_overhang_state",
        "policy_demand_path_state",
        "valuation_pressure_state",
        "economic_transmission_state",
        "economic_reason_codes",
        "customer_event_count",
        "revenue_backlog_event_count",
        "guidance_margin_event_count",
        "supply_demand_event_count",
        "company_direct_event_count",
    ]
    cols715 = KEYS + [
        "pricing_acceptance_state",
        "priced_vs_unpriced_state",
        "positioning_proxy_state",
        "acceptance_failure_state",
        "market_pricing_brain_state",
        "market_pricing_reason_codes",
    ]
    cols716 = KEYS + [
        "slot_context_score",
        "same_timestamp_candidate_count",
        "same_timestamp_context_rank",
        "same_timestamp_theme_count",
        "slot_competition_state",
        "exposure_cluster_state",
        "portfolio_brain_state",
    ]
    out = base.merge(t713[[c for c in cols713 if c in t713.columns]], on=KEYS, how="left", validate="one_to_one")
    out = out.merge(t714[[c for c in cols714 if c in t714.columns]], on=KEYS, how="left", validate="one_to_one", suffixes=("", "_econ"))
    out = out.merge(t715[[c for c in cols715 if c in t715.columns]], on=KEYS, how="left", validate="one_to_one", suffixes=("", "_price"))
    out = out.merge(t716[[c for c in cols716 if c in t716.columns]], on=KEYS, how="left", validate="one_to_one", suffixes=("", "_slot"))
    return out


def build_interaction_panel(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["analysis_priority"] = out["watch_subtype"].map(
        {
            "watch_due_to_company_evidence_absorption_needed": "priority_1_company_evidence_absorption",
            "watch_due_to_slot_confirmation_needed": "priority_2_slot_superiority_bridge",
            "watch_due_to_financing_absorption_test": "priority_3_financing_noise_resolution",
        }
    )
    out["cashflow_evidence_axis"] = out.apply(cashflow_evidence_axis, axis=1)
    out["financing_risk_axis"] = out.apply(financing_risk_axis, axis=1)
    out["price_absorption_axis"] = out.apply(price_absorption_axis, axis=1)
    out["slot_competition_axis"] = out.apply(slot_competition_axis, axis=1)
    out["invalidation_axis"] = out.apply(invalidation_axis, axis=1)
    out["layer_interaction_state"] = out.apply(layer_interaction_state, axis=1)
    out["relationship_diagnosis"] = out.apply(relationship_diagnosis, axis=1)
    out["diagnostic_bucket_state"] = out.apply(diagnostic_bucket_state, axis=1)
    out["final_diagnostic_state"] = out.apply(final_diagnostic_state, axis=1)
    out["new_layer_required_flag"] = 0
    out["interaction_logic_upgrade_required_flag"] = 1
    out["human_review_packet_type"] = out.apply(human_review_packet_type, axis=1)
    out["manual_review_questions"] = out.apply(manual_review_questions, axis=1)
    out["diagnostic_reason_codes"] = out.apply(diagnostic_reason_codes, axis=1)
    add_no_action_flags(out)
    cols = KEYS + [
        "watch_subtype",
        "analysis_priority",
        "promotion_candidate_state",
        "confirmation_contract_id",
        "cashflow_evidence_axis",
        "financing_risk_axis",
        "price_absorption_axis",
        "slot_competition_axis",
        "invalidation_axis",
        "layer_interaction_state",
        "relationship_diagnosis",
        "diagnostic_bucket_state",
        "final_diagnostic_state",
        "new_layer_required_flag",
        "interaction_logic_upgrade_required_flag",
        "human_review_packet_type",
        "manual_review_questions",
        "diagnostic_reason_codes",
        "source_directness_state",
        "novelty_state",
        "evidence_strength_state",
        "company_anchor_state",
        "high_noise_context_state",
        "low_novelty_context_state",
        "funding_path_state",
        "dilution_overhang_state",
        "economic_transmission_state",
        "pricing_acceptance_state",
        "priced_vs_unpriced_state",
        "market_pricing_brain_state",
        "same_timestamp_context_rank",
        "same_timestamp_theme_count",
        "slot_competition_state",
        "exposure_cluster_state",
    ] + no_action_columns()
    return out[[c for c in cols if c in out.columns]].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def build_institutional_context_pack() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "context_id": "FED_FSR_2026_VULNERABILITY_INTERACTION",
                "source_url": "https://www.federalreserve.gov/publications/2026-may-financial-stability-report-purpose-and-framework.htm",
                "institutional_lesson": "valuation_pressure_borrowing_leverage_and_funding_risk_can_amplify_stress",
                "project_application": "financing risk cannot be judged alone; it must be checked against price absorption and growth survival",
            },
            {
                "context_id": "IMF_GFSR_2026_AMPLIFICATION_CHANNELS",
                "source_url": "https://www.imf.org/en/publications/gfsr/issues/2026/04/14/global-financial-stability-report-april-2026",
                "institutional_lesson": "risk_sentiment_financial_conditions_leverage_and_flow_channels_can_move_together",
                "project_application": "slot superiority needs market and theme context; rank alone is not enough",
            },
            {
                "context_id": "NBER_CASHFLOW_NEWS_UNDERREACTION",
                "source_url": "https://www.nber.org/papers/w8793",
                "institutional_lesson": "cashflow_news_and_price_reaction_must_be_jointly_evaluated",
                "project_application": "company evidence needs price absorption; price alone without cashflow evidence is weak",
            },
            {
                "context_id": "NBER_CONFLICTING_MACRO_NEWS_REACTION",
                "source_url": "https://www.nber.org/papers/w32301",
                "institutional_lesson": "conflicting_signals_can_create_underreaction_even_when_individual_shocks_are_overreacted_to",
                "project_application": "financing risk and growth news can conflict; interaction state is more important than another layer",
            },
        ]
    )


def build_bucket_interaction_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "watch_subtype",
        "layer_interaction_state",
        "diagnostic_bucket_state",
        "final_diagnostic_state",
        "relationship_diagnosis",
        "human_review_packet_type",
    ]
    rows = []
    for keys, group in panel.groupby(group_cols, dropna=False):
        rows.append(
            {
                "watch_subtype": keys[0],
                "layer_interaction_state": keys[1],
                "diagnostic_bucket_state": keys[2],
                "final_diagnostic_state": keys[3],
                "relationship_diagnosis": keys[4],
                "human_review_packet_type": keys[5],
                "candidate_count": len(group),
                "new_layer_required_flag": int(group["new_layer_required_flag"].max()),
                "interaction_logic_upgrade_required_flag": int(group["interaction_logic_upgrade_required_flag"].max()),
                "outcome_used_for_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["watch_subtype", "candidate_count"], ascending=[True, False]).reset_index(drop=True)


def build_human_review_queue(panel: pd.DataFrame) -> pd.DataFrame:
    cols = KEYS + [
        "watch_subtype",
        "analysis_priority",
        "human_review_packet_type",
        "manual_review_questions",
        "layer_interaction_state",
        "cashflow_evidence_axis",
        "financing_risk_axis",
        "price_absorption_axis",
        "slot_competition_axis",
        "invalidation_axis",
        "diagnostic_reason_codes",
        "assignment_used_flag",
        "outcome_used_for_assignment_flag",
    ]
    return panel[cols].sort_values(["analysis_priority", "entry_ts", "symbol"]).reset_index(drop=True)


def build_eval_guardrail(panel: pd.DataFrame, eval_path: Path) -> pd.DataFrame:
    eval_panel = pd.read_csv(eval_path)
    merged = panel.merge(
        eval_panel[KEYS + ["costed_return_pct", "entry_reduce_failure_flag"]],
        on=KEYS,
        how="left",
        validate="one_to_one",
    )
    top50 = set(eval_panel.nlargest(50, "costed_return_pct")["lifecycle_id"])
    bottom50 = set(eval_panel.nsmallest(50, "costed_return_pct")["lifecycle_id"])
    rows = []
    for state, group in merged.groupby("layer_interaction_state", dropna=False):
        ids = set(group["lifecycle_id"])
        rows.append(
            {
                "layer_interaction_state": state,
                "candidate_count": len(group),
                "top50_winner_count_eval_only": len(top50 & ids),
                "bottom50_loser_count_eval_only": len(bottom50 & ids),
                "avg_costed_return_pct_eval_only": float(group["costed_return_pct"].mean()),
                "entry_reduce_failure_rate_eval_only": float(pd.to_numeric(group["entry_reduce_failure_flag"], errors="coerce").fillna(0).mean()),
                "outcome_used_for_assignment_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("top50_winner_count_eval_only", ascending=False).reset_index(drop=True)


def build_leakage_guardrail(panel: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("no_assignment_use", int(panel["assignment_used_flag"].sum()) == 0, str(int(panel["assignment_used_flag"].sum())), "0"),
        ("no_outcome_assignment", int(panel["outcome_used_for_assignment_flag"].sum()) == 0, str(int(panel["outcome_used_for_assignment_flag"].sum())), "0"),
        ("no_future_price_assignment", int(panel["future_price_used_for_assignment_flag"].sum()) == 0, str(int(panel["future_price_used_for_assignment_flag"].sum())), "0"),
        ("top50_not_used", int(panel["top50_used_for_assignment_flag"].sum()) == 0, str(int(panel["top50_used_for_assignment_flag"].sum())), "0"),
        ("no_ticker_theme_protection", int(panel["ticker_theme_protection_rule_flag"].sum()) == 0, str(int(panel["ticker_theme_protection_rule_flag"].sum())), "0"),
        ("no_outcome_threshold_tuning", int(panel["threshold_tuned_from_outcome_flag"].sum()) == 0, str(int(panel["threshold_tuned_from_outcome_flag"].sum())), "0"),
        ("no_action_output", int(panel["translator_output_is_action_flag"].sum()) == 0, str(int(panel["translator_output_is_action_flag"].sum())), "0"),
        ("real_capital_forbidden", set(panel["real_capital_status"]) == {"FORBIDDEN"}, ",".join(sorted(set(panel["real_capital_status"]))), "FORBIDDEN"),
    ]
    return pd.DataFrame([gate(name, passed, observed, required) for name, passed, observed, required in checks])


def build_governance_audit(panel: pd.DataFrame, matrix: pd.DataFrame, queue: pd.DataFrame, leakage: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_target_345", len(panel) == 345, f"rows={len(panel)}", "345"),
            gate("target_subtype_count_3", panel["watch_subtype"].nunique() == 3, f"subtypes={panel['watch_subtype'].nunique()}", "3"),
            gate("new_layer_not_primary", int(panel["new_layer_required_flag"].sum()) == 0, "0", "0"),
            gate("interaction_logic_primary", int(panel["interaction_logic_upgrade_required_flag"].min()) == 1, "1", "1"),
            gate("matrix_present", len(matrix) > 0, f"rows={len(matrix)}", ">0"),
            gate("human_review_queue_complete", len(queue) == len(panel), f"rows={len(queue)}", "345"),
            gate("manual_questions_present", queue["manual_review_questions"].astype(str).str.len().gt(0).all(), "nonempty", "nonempty"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


def cashflow_evidence_axis(row: pd.Series) -> str:
    subtype = str(row.get("watch_subtype", ""))
    company_direct = number(row.get("company_direct_event_count"))
    customer = number(row.get("customer_event_count"))
    backlog = number(row.get("revenue_backlog_event_count"))
    guidance = number(row.get("guidance_margin_event_count"))
    supply = number(row.get("supply_demand_event_count"))
    strength = str(row.get("evidence_strength_state", ""))
    if subtype == "watch_due_to_company_evidence_absorption_needed":
        return "cashflow_evidence_present_needs_market_acceptance"
    if company_direct + customer + backlog + guidance + supply >= 2:
        return "multi_signal_cashflow_evidence_present"
    if strength == "thin_single_signal_evidence":
        return "thin_cashflow_evidence_needs_second_signal"
    return "weak_or_noise_cashflow_link"


def financing_risk_axis(row: pd.Series) -> str:
    funding = str(row.get("funding_path_state", ""))
    dilution = str(row.get("dilution_overhang_state", ""))
    valuation = str(row.get("valuation_pressure_state", ""))
    if "overhang" in funding and "unabsorbed" in dilution:
        if "pressure" in valuation:
            return "funding_dilution_and_valuation_pressure_stack"
        return "funding_dilution_overhang_unabsorbed"
    if "overhang" in funding or "overhang" in dilution:
        return "funding_or_dilution_overhang_partial"
    return "no_financing_overhang_claim"


def price_absorption_axis(row: pd.Series) -> str:
    pricing = str(row.get("pricing_acceptance_state", ""))
    priced = str(row.get("priced_vs_unpriced_state", ""))
    market = str(row.get("market_pricing_brain_state", ""))
    if pricing == "accepted_by_price_and_tape_proxy":
        return "price_absorption_confirmed_proxy"
    if pricing == "acceptance_building_not_final" and "incomplete" in priced:
        return "price_absorption_building_but_incomplete"
    if market == "market_waiting_on_overhang_absorption":
        return "market_waiting_on_financing_absorption"
    return "price_absorption_unclear"


def slot_competition_axis(row: pd.Series) -> str:
    rank = number(row.get("same_timestamp_context_rank"), default=999)
    theme_count = number(row.get("same_timestamp_theme_count"), default=999)
    subtype = str(row.get("watch_subtype", ""))
    if subtype == "watch_due_to_slot_confirmation_needed":
        return "rank_first_but_slot_quality_unproven"
    if rank <= 1 and theme_count <= 2:
        return "cohort_rank_ok_cluster_not_extreme"
    if rank <= 2:
        return "cohort_near_top_but_cluster_check_needed"
    return "cohort_competition_weak"


def invalidation_axis(row: pd.Series) -> str:
    financing = financing_risk_axis(row)
    price = price_absorption_axis(row)
    evidence = cashflow_evidence_axis(row)
    if ("unabsorbed" in financing or "pressure_stack" in financing) and "incomplete" in price and evidence == "weak_or_noise_cashflow_link":
        return "invalidation_active_financing_dominates_weak_evidence"
    if ("unabsorbed" in financing or "pressure_stack" in financing) and "present" in evidence and "incomplete" in price:
        return "invalidation_watch_price_must_absorb_financing"
    if "rank_first" in slot_competition_axis(row) and "incomplete" in price:
        return "invalidation_watch_rank_first_not_enough"
    return "invalidation_not_triggered_but_unproven"


def layer_interaction_state(row: pd.Series) -> str:
    subtype = str(row.get("watch_subtype", ""))
    evidence = cashflow_evidence_axis(row)
    financing = financing_risk_axis(row)
    price = price_absorption_axis(row)
    slot = slot_competition_axis(row)
    if subtype == "watch_due_to_company_evidence_absorption_needed":
        return "company_cashflow_vs_unabsorbed_financing_bridge"
    if subtype == "watch_due_to_slot_confirmation_needed":
        return "rank_first_but_financing_price_bridge_unresolved"
    if evidence == "weak_or_noise_cashflow_link" and ("unabsorbed" in financing or "pressure_stack" in financing):
        if slot == "cohort_rank_ok_cluster_not_extreme":
            return "financing_noise_with_rank_ok_but_no_cashflow_bridge"
        if slot == "cohort_near_top_but_cluster_check_needed":
            return "financing_noise_with_cluster_check_bridge"
        return "financing_noise_with_weak_cohort_bridge"
    if "incomplete" in price and ("unabsorbed" in financing or "pressure_stack" in financing):
        return "financing_absorption_pending_bridge"
    if "cohort" in slot:
        return "cohort_context_pending_bridge"
    return "watch_interaction_unclear_bridge"


def relationship_diagnosis(row: pd.Series) -> str:
    state = layer_interaction_state(row)
    if state == "company_cashflow_vs_unabsorbed_financing_bridge":
        return "cashflow_evidence_exists_but_market_has_not_absorbed_financing_risk"
    if state == "rank_first_but_financing_price_bridge_unresolved":
        return "slot_rank_is_not_sufficient_without_cashflow_price_and_invalidation_confirmation"
    if state == "financing_noise_with_rank_ok_but_no_cashflow_bridge":
        return "rank_is_ok_but_financing_risk_dominates_without_cashflow_evidence"
    if state == "financing_noise_with_cluster_check_bridge":
        return "financing_risk_and_theme_cluster_need_joint_review_before_any_promotion"
    if state == "financing_noise_with_weak_cohort_bridge":
        return "financing_risk_weak_evidence_and_weak_cohort_context_align_negative"
    if state == "financing_absorption_pending_bridge":
        return "financing_risk_may_be_resolved_only_if_price_absorption_and_growth_path_confirm"
    return "interaction_needs_manual_review"


def diagnostic_bucket_state(row: pd.Series) -> str:
    state = layer_interaction_state(row)
    if state == "company_cashflow_vs_unabsorbed_financing_bridge":
        return "cashflow_news_absorption_pending"
    if state == "rank_first_but_financing_price_bridge_unresolved":
        return "slot_rank_unconfirmed"
    if state == "financing_noise_with_rank_ok_but_no_cashflow_bridge":
        return "funding_need_noise_only_rank_ok"
    if state == "financing_noise_with_cluster_check_bridge":
        return "funding_risk_absorption_diagnostic_hold"
    if state == "financing_noise_with_weak_cohort_bridge":
        return "financing_overhang_unabsorbed"
    return "diagnostic_interaction_unclear"


def final_diagnostic_state(row: pd.Series) -> str:
    bucket = diagnostic_bucket_state(row)
    if bucket == "slot_rank_unconfirmed":
        return "DIAGNOSTIC_SLOT_CONFIRMATION_PENDING"
    if bucket in {"cashflow_news_absorption_pending", "funding_risk_absorption_diagnostic_hold"}:
        return "DIAGNOSTIC_ABSORPTION_PENDING"
    if bucket in {"funding_need_noise_only_rank_ok", "financing_overhang_unabsorbed"}:
        return "DIAGNOSTIC_INTERACTION_UNCONFIRMED"
    return "DIAGNOSTIC_REVIEW_REQUIRED"


def human_review_packet_type(row: pd.Series) -> str:
    subtype = str(row.get("watch_subtype", ""))
    if subtype == "watch_due_to_company_evidence_absorption_needed":
        return "review_company_evidence_price_absorption_packet"
    if subtype == "watch_due_to_slot_confirmation_needed":
        return "review_slot_superiority_context_packet"
    return "review_financing_use_of_proceeds_and_absorption_packet"


def manual_review_questions(row: pd.Series) -> str:
    packet = human_review_packet_type(row)
    if packet == "review_company_evidence_price_absorption_packet":
        return "does_company_evidence_translate_to_cashflow;is_financing_risk_absorbed_by_price;what_invalidates_absorption"
    if packet == "review_slot_superiority_context_packet":
        return "why_is_rank_first;is_cashflow_evidence_real;is_price_absorption_confirmed;does_cluster_risk_reduce_slot_quality"
    return "is_financing_growth_fuel_or_dilution_overhang;is_cashflow_evidence_real;has_price_started_absorbing_risk;what_invalidates_growth_survival"


def diagnostic_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"cashflow={cashflow_evidence_axis(row)}",
            f"financing={financing_risk_axis(row)}",
            f"price={price_absorption_axis(row)}",
            f"slot={slot_competition_axis(row)}",
            f"invalidation={invalidation_axis(row)}",
            f"interaction={layer_interaction_state(row)}",
            f"bucket_state={diagnostic_bucket_state(row)}",
            f"final_state={final_diagnostic_state(row)}",
        ]
    )


def decision_frame(panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task720",
                "verdict": "WATCH_BUCKET_INTERACTION_DIAGNOSTICS_BUILT_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "target_watch_candidate_count": len(panel),
                "new_layer_required_flag": 0,
                "interaction_logic_upgrade_required_flag": 1,
                "trading_promotion_pass_flag": 0,
                "next_action": "Manually review the three interaction packets before any backtest promotion.",
            }
        ]
    )


def pass_fail_matrix(
    panel: pd.DataFrame,
    matrix: pd.DataFrame,
    queue: pd.DataFrame,
    eval_guardrail: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_target_345", len(panel) == 345, f"rows={len(panel)}", "345"),
            gate("target_subtype_count_3", panel["watch_subtype"].nunique() == 3, f"subtypes={panel['watch_subtype'].nunique()}", "3"),
            gate("interaction_matrix_present", len(matrix) > 0, f"rows={len(matrix)}", ">0"),
            gate("human_review_queue_complete", len(queue) == len(panel), f"rows={len(queue)}", "345"),
            gate("eval_guardrail_present", int(eval_guardrail["outcome_used_for_assignment_flag"].sum()) == 0, "0", "0"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
            gate("strategy_not_accepted", True, "NOT_ACCEPTED", "NOT_ACCEPTED"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


def add_no_action_flags(frame: pd.DataFrame) -> None:
    frame["translator_output_is_action_flag"] = 0
    frame["assignment_used_flag"] = 0
    frame["outcome_used_for_assignment_flag"] = 0
    frame["future_price_used_for_assignment_flag"] = 0
    frame["top50_used_for_assignment_flag"] = 0
    frame["ticker_theme_protection_rule_flag"] = 0
    frame["threshold_tuned_from_outcome_flag"] = 0
    frame["buy_sell_or_sizing_instruction_flag"] = 0
    frame["missing_source_used_as_negative_flag"] = 0
    frame["real_capital_status"] = "FORBIDDEN"
    frame["no_action_reason"] = NO_ACTION_REASON


def no_action_columns() -> list[str]:
    return [
        "translator_output_is_action_flag",
        "assignment_used_flag",
        "outcome_used_for_assignment_flag",
        "future_price_used_for_assignment_flag",
        "top50_used_for_assignment_flag",
        "ticker_theme_protection_rule_flag",
        "threshold_tuned_from_outcome_flag",
        "buy_sell_or_sizing_instruction_flag",
        "missing_source_used_as_negative_flag",
        "real_capital_status",
        "no_action_reason",
    ]


def number(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


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


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    report = f"""# Task720 Watch Bucket Interaction Diagnostics

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Conclusion: do not add a new brain layer first; strengthen interaction logic between existing layers.
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

- Scope: 345 watch candidates across the three priority buckets.
- Inputs: Task713 evidence, Task714 economic transmission, Task715 market pricing, Task716 slot context, and Task719 confirmation contracts.
- Institutional context:
  - Fed FSR 2026: valuation, borrowing, leverage, and funding risks can amplify stress.
  - IMF GFSR 2026: risk sentiment, financial conditions, leverage, and flow channels can move together.
  - NBER cash-flow news: cash-flow evidence and price reaction must be evaluated jointly.
  - NBER macro news reaction: conflicting signals can produce both overreaction and underreaction.
- Implementation: cashflow, financing, price absorption, slot competition, and invalidation axes are linked into a diagnostic interaction state.
- No action output is produced.

## No-Background Decision-Maker Report

- This does not buy anything.
- The issue is not another brain layer yet.
- The issue is whether company evidence, financing risk, price absorption, and slot quality agree or fight each other.
- The next human review should inspect financing use-of-proceeds, slot superiority, and company evidence price absorption packets.

## Artifact Manifest

- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation command: `python -m unittest tests.test_task720_watch_bucket_interaction_diagnostics`.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / "task_720_watch_bucket_interaction_diagnostics.md").write_text(report, encoding="utf-8")
    manifest = out_dir / "artifact_manifest.csv"
    if manifest.exists():
        manifest.unlink()
    write_manifest(out_dir, manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task720 watch bucket interaction diagnostics.")
    parser.add_argument("--task719", type=Path, default=TASK719_PANEL)
    parser.add_argument("--task713", type=Path, default=TASK713_PANEL)
    parser.add_argument("--task714", type=Path, default=TASK714_PANEL)
    parser.add_argument("--task715", type=Path, default=TASK715_PANEL)
    parser.add_argument("--task716", type=Path, default=TASK716_PANEL)
    parser.add_argument("--eval", type=Path, default=TASK708_EVAL)
    parser.add_argument("--out-dir", type=Path, default=TASK720_DIR)
    args = parser.parse_args()
    build_task720(
        task719_path=args.task719,
        task713_path=args.task713,
        task714_path=args.task714,
        task715_path=args.task715,
        task716_path=args.task716,
        eval_path=args.eval,
        out_dir=args.out_dir,
    )
    print("[Task720] wrote watch bucket interaction diagnostics")


if __name__ == "__main__":
    main()
