from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD, load_qqq_history
from src.backtest.build_task638_content_signal_refinement import simulate_account
from src.backtest.build_task639_oos_first_rule_lock_refinement import run_account
from src.backtest.build_task659_theme_specific_relation_engine import (
    QQQ_PATH,
    SPARSE_MIN_COUNT,
    driver_columns,
    replace_rows,
    task639_core,
)


TASK_ID = "Task661"
REPORT_DIR = Path("docs/reports/task_661_mechanism_relation_engine")
TASK659_PANEL = Path("docs/reports/task_659_theme_specific_relation_engine/theme_macro_company_state_panel.csv")
TASK659_GRID = Path("docs/reports/task_659_theme_specific_relation_engine/theme_specific_soft_wrapper_grid.csv")
TASK659_SPLIT_GRID = Path("docs/reports/task_659_theme_specific_relation_engine/task659_split_account_grid.csv")


def build_task661_mechanism_relation_engine(
    *,
    task659_panel_path: Path = TASK659_PANEL,
    task659_grid_path: Path = TASK659_GRID,
    task659_split_grid_path: Path = TASK659_SPLIT_GRID,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = load_task659_panel(task659_panel_path)
    qqq = load_qqq_history(qqq_path)
    task659_grid = pd.read_csv(task659_grid_path)
    task659_split_grid = pd.read_csv(task659_split_grid_path)

    template = build_institutional_transmission_template()
    mechanism_panel = build_mechanism_state_panel(panel, template)
    diagnostics = build_mechanism_diagnostics(mechanism_panel)
    candidate_grid = build_candidate_grid(mechanism_panel, qqq)
    split_grid = build_split_grid(mechanism_panel, qqq)
    oos_audit = build_oos_effect_audit(mechanism_panel)
    best_candidate = choose_best_candidate(candidate_grid)
    attribution = build_accepted_trade_attribution(mechanism_panel, best_candidate)
    promotion = build_promotion_report(candidate_grid, split_grid, task659_grid, task659_split_grid)
    blockers = build_not_do_matrix(candidate_grid, promotion)
    pass_fail = build_pass_fail(template, mechanism_panel, diagnostics, promotion, blockers)
    decision = build_decision(candidate_grid, promotion, pass_fail)

    template.to_csv(out_dir / "institutional_transmission_template.csv", index=False, encoding="utf-8-sig")
    mechanism_panel.to_csv(out_dir / "theme_mechanism_state_panel.csv", index=False, encoding="utf-8-sig")
    diagnostics.to_csv(out_dir / "mechanism_relation_diagnostics.csv", index=False, encoding="utf-8-sig")
    candidate_grid.to_csv(out_dir / "mechanism_soft_wrapper_grid.csv", index=False, encoding="utf-8-sig")
    split_grid.to_csv(out_dir / "mechanism_split_account_grid.csv", index=False, encoding="utf-8-sig")
    oos_audit.to_csv(out_dir / "oos_effect_audit.csv", index=False, encoding="utf-8-sig")
    attribution.to_csv(out_dir / "accepted_trade_attribution.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(out_dir / "promotion_report.csv", index=False, encoding="utf-8-sig")
    blockers.to_csv(out_dir / "not_do_matrix.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_661_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_661_decision.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, candidate_grid, split_grid, diagnostics, oos_audit, promotion, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "template": template,
        "mechanism_panel": mechanism_panel,
        "diagnostics": diagnostics,
        "candidate_grid": candidate_grid,
        "split_grid": split_grid,
        "oos_audit": oos_audit,
        "attribution": attribution,
        "promotion": promotion,
        "blockers": blockers,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def load_task659_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        if column in panel.columns:
            panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    numeric_columns = [
        "positive_contract_customer_count",
        "positive_backlog_order_count",
        "positive_guidance_up_count",
        "positive_margin_supply_combo_count",
        "content_supply_demand_flag",
        "content_supply_demand_count",
        "content_guidance_margin_count",
        "content_contract_revenue_count",
        "content_direct_bullish_count",
        "content_direct_bearish_count",
        "content_refined_strength_score",
        "content_max_magnitude_score",
        "content_avg_priced_in_risk_score",
        "content_low_priced_in_positive_flag",
        "net_return_from_entry",
        "entry_reduce_failure_flag",
        "range_pos",
        "intraday_ret_from_open",
        "volume_ratio_prev",
        "theme_rank_prev",
        "theme_breadth20_prev",
        "near_high60_prev",
        "conflict_count",
        "support_count",
        "sparse_cell_flag",
        "macro_action_allowed_flag",
    ]
    for column in numeric_columns:
        if column in panel.columns:
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def build_institutional_transmission_template() -> pd.DataFrame:
    rows = [
        ("ai_semiconductors", "high", "medium", "medium", "low", "high", "medium", "high", "AI capex and compute demand support leaders, but capex financing and valuation duration can bite."),
        ("cloud_ai_platforms", "high", "high", "high", "low", "high", "medium", "high", "Cloud AI has long-duration earnings, high liquidity sensitivity, and capex/financing dependence."),
        ("aerospace_defense_space", "medium", "low", "low", "medium", "medium", "high", "low", "Defense and space are policy/contract driven; macro pressure is secondary unless funding or execution fails."),
        ("biotech_glp1_healthcare", "medium", "high", "high", "low", "low", "medium", "medium", "Biotech is duration and funding sensitive; catalyst quality must be strong to offset macro pressure."),
        ("industrial_automation_robotics", "high", "medium", "medium", "medium", "medium", "medium", "medium", "Industrial automation depends on capex cycle, input costs, and global demand."),
        ("power_grid_electrification", "high", "medium", "medium", "high", "high", "medium", "medium", "Grid electrification benefits from power demand, but financing and project timing matter."),
        ("data_devops_software", "medium", "high", "high", "low", "medium", "low", "high", "Software is duration/liquidity sensitive; monetization evidence matters more than mentions."),
        ("cybersecurity", "low", "medium", "medium", "low", "medium", "medium", "medium", "Cybersecurity demand is resilient, but price acceptance and budget strength still matter."),
        ("crypto_fintech", "low", "high", "high", "low", "low", "medium", "high", "Crypto/fintech is liquidity and credit sensitive with weak tolerance for risk-off conditions."),
        ("ev_autonomy_mobility", "high", "high", "high", "medium", "medium", "medium", "high", "EV/autonomy depends on consumer financing, funding, input costs, and policy support."),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "theme_id",
            "capital_intensity",
            "funding_sensitivity",
            "duration_sensitivity",
            "energy_sensitivity",
            "capex_demand_sensitivity",
            "policy_sensitivity",
            "liquidity_sensitivity",
            "transmission_reason_code",
        ],
    ).assign(manual_version="task661_institutional_template_v1", return_tuned_flag=0)


def build_mechanism_state_panel(panel: pd.DataFrame, template: pd.DataFrame) -> pd.DataFrame:
    out = panel.merge(template, on="theme_id", how="left")
    for column in [
        "capital_intensity",
        "funding_sensitivity",
        "duration_sensitivity",
        "energy_sensitivity",
        "capex_demand_sensitivity",
        "policy_sensitivity",
        "liquidity_sensitivity",
    ]:
        out[column] = out[column].fillna("medium")

    out["catalyst_quality_score"] = out.apply(catalyst_quality_score, axis=1)
    out["catalyst_quality_tier"] = out["catalyst_quality_score"].apply(catalyst_quality_tier)
    out["price_acceptance_score"] = out.apply(price_acceptance_score, axis=1)
    out["price_acceptance_state"] = out["price_acceptance_score"].apply(price_acceptance_state)
    out["funding_stress_state"] = out.apply(funding_stress_state, axis=1)
    out["duration_pressure_state"] = out.apply(duration_pressure_state, axis=1)
    out["energy_input_cost_state"] = out.apply(energy_input_cost_state, axis=1)
    out["capex_demand_support_state"] = out.apply(capex_demand_support_state, axis=1)
    out["policy_geopolitical_support_state"] = out.apply(policy_geopolitical_support_state, axis=1)
    out["adoption_support_state"] = out.apply(adoption_support_state, axis=1)
    out["mechanism_support_count"] = out[
        [
            "capex_demand_support_state",
            "policy_geopolitical_support_state",
            "adoption_support_state",
        ]
    ].apply(lambda row: sum(str(value).endswith("_support") for value in row), axis=1)
    out["mechanism_pressure_count"] = out[
        [
            "funding_stress_state",
            "duration_pressure_state",
            "energy_input_cost_state",
        ]
    ].apply(lambda row: sum(str(value).endswith("_pressure") or str(value).endswith("_stress") for value in row), axis=1)
    out["mechanism_relation_state_raw"] = out.apply(mechanism_relation_state_raw, axis=1)
    core = task639_core(out)
    cell_counts = (
        core.groupby(["theme_id", "mechanism_relation_state_raw"], dropna=False)
        .size()
        .reset_index(name="mechanism_cell_count")
    )
    out = out.merge(cell_counts, on=["theme_id", "mechanism_relation_state_raw"], how="left")
    out["mechanism_cell_count"] = pd.to_numeric(out["mechanism_cell_count"], errors="coerce").fillna(0).astype(int)
    out["mechanism_sparse_cell_flag"] = (
        out["mechanism_cell_count"].lt(SPARSE_MIN_COUNT)
        & out.apply(is_task639_row, axis=1)
    ).astype(int)
    out["mechanism_relation_state"] = out.apply(
        lambda row: "sparse_mechanism_cell" if int(row["mechanism_sparse_cell_flag"]) == 1 else row["mechanism_relation_state_raw"],
        axis=1,
    )
    out["candidate_action_family"] = out.apply(candidate_action_family, axis=1)
    out["scenario_base_case"] = out.apply(scenario_base_case, axis=1)
    out["scenario_invalidation_condition"] = out.apply(scenario_invalidation_condition, axis=1)
    out["company_source_assignment_certified_flag"] = out.apply(company_source_assignment_certified_flag, axis=1)
    out["content_prediction_assignment_certified_flag"] = out.apply(content_prediction_assignment_certified_flag, axis=1)
    out["theme_price_assignment_certified_flag"] = out.apply(theme_price_assignment_certified_flag, axis=1)
    out["portfolio_capacity_assignment_certified_flag"] = out["theme_price_assignment_certified_flag"]
    macro_diag = out["macro_asof_provisional_for_diagnostic_flag"] if "macro_asof_provisional_for_diagnostic_flag" in out.columns else pd.Series(0, index=out.index)
    out["macro_asof_valid_for_diagnostic_flag"] = pd.to_numeric(macro_diag, errors="coerce").fillna(0).astype(int)
    out["macro_context_available_for_diagnostic_flag"] = out["macro_asof_valid_for_diagnostic_flag"]
    macro_cert = out["macro_asof_certified_for_assignment_flag"] if "macro_asof_certified_for_assignment_flag" in out.columns else pd.Series(0, index=out.index)
    out["macro_assignment_certified_flag"] = pd.to_numeric(macro_cert, errors="coerce").fillna(0).astype(int)
    out["macro_used_for_assignment_flag"] = 0
    out["relation_assignment_certified_flag"] = out.apply(relation_assignment_certified_flag, axis=1)
    out["allocation_assignment_ready_flag"] = (
        out["company_source_assignment_certified_flag"].eq(1)
        & out["content_prediction_assignment_certified_flag"].eq(1)
        & out["theme_price_assignment_certified_flag"].eq(1)
        & out["portfolio_capacity_assignment_certified_flag"].eq(1)
    ).astype(int)
    out["asof_valid_flag"] = (
        out["allocation_assignment_ready_flag"].eq(1) | out["macro_asof_valid_for_diagnostic_flag"].eq(1)
    ).astype(int)
    out["used_for_assignment_flag"] = out["allocation_assignment_ready_flag"]
    out["assignment_certification_scope"] = out.apply(assignment_certification_scope, axis=1)
    out["assignment_block_reason"] = out.apply(assignment_block_reason, axis=1)
    out["macro_provisional_used_as_certified"] = 0
    out["missing_source_used_as_negative"] = 0
    out["return_used_in_assignment_flag"] = 0
    out["label_used_in_assignment_flag_task661"] = 0
    return out


def is_task639_row(row: pd.Series) -> bool:
    return (
        (float(row.get("positive_contract_customer_count", 0) or 0) > 0)
        or (float(row.get("content_supply_demand_flag", 0) or 0) == 1)
    ) and str(row.get("timing_mode")) == "delay1d" and str(row.get("exit_mode")) == "existing_exit"


def catalyst_quality_score(row: pd.Series) -> int:
    score = 0
    score += 3 if float(row.get("positive_contract_customer_count", 0) or 0) > 0 else 0
    score += 2 if float(row.get("content_supply_demand_flag", 0) or 0) == 1 else 0
    score += 2 if float(row.get("positive_backlog_order_count", 0) or 0) > 0 else 0
    score += 2 if float(row.get("positive_guidance_up_count", 0) or 0) > 0 else 0
    score += 2 if float(row.get("positive_margin_supply_combo_count", 0) or 0) > 0 else 0
    score += 1 if float(row.get("content_guidance_margin_count", 0) or 0) > 0 else 0
    score += 1 if float(row.get("content_contract_revenue_count", 0) or 0) > 0 else 0
    score += 1 if float(row.get("content_low_priced_in_positive_flag", 0) or 0) == 1 else 0
    score -= 2 if float(row.get("content_direct_bearish_count", 0) or 0) > 0 else 0
    return int(score)


def catalyst_quality_tier(score: int) -> str:
    if score >= 7:
        return "very_strong_catalyst"
    if score >= 4:
        return "strong_catalyst"
    if score >= 2:
        return "medium_catalyst"
    if score >= 1:
        return "weak_catalyst"
    return "no_task639_catalyst"


def price_acceptance_score(row: pd.Series) -> int:
    score = 0
    if str(row.get("intraday_entry_state_v4", "")) == "intraday_breakout_acceptance":
        score += 2
    if str(row.get("timing_state", "")) in {"opening_drive", "trend_continuation", "vwap_reclaim"}:
        score += 1
    if float(row.get("range_pos", 0) or 0) >= 0.75:
        score += 1
    if float(row.get("intraday_ret_from_open", 0) or 0) > 0:
        score += 1
    if float(row.get("volume_ratio_prev", 0) or 0) >= 1.2:
        score += 1
    if float(row.get("near_high60_prev", 0) or 0) >= 0.95:
        score += 1
    if float(row.get("range_pos", 0) or 0) <= 0.35:
        score -= 2
    if float(row.get("intraday_ret_from_open", 0) or 0) < -0.01:
        score -= 2
    return int(score)


def price_acceptance_state(score: int) -> str:
    if score >= 5:
        return "price_acceptance_strong"
    if score >= 3:
        return "price_acceptance_accepted"
    if score >= 1:
        return "price_acceptance_neutral"
    return "price_acceptance_rejected"


def funding_stress_state(row: pd.Series) -> str:
    sensitive = str(row.get("funding_sensitivity", "medium")) in {"medium", "high"}
    if sensitive and int(row.get("credit_conflict", 0) or 0) == 1:
        return "funding_stress"
    if sensitive and int(row.get("credit_support", 0) or 0) == 1:
        return "funding_support"
    return "funding_neutral"


def duration_pressure_state(row: pd.Series) -> str:
    sensitive = str(row.get("duration_sensitivity", "medium")) in {"medium", "high"}
    if sensitive and int(row.get("rates_conflict", 0) or 0) == 1:
        return "duration_pressure"
    if sensitive and int(row.get("rates_support", 0) or 0) == 1:
        return "duration_support"
    return "duration_neutral"


def energy_input_cost_state(row: pd.Series) -> str:
    sensitive = str(row.get("energy_sensitivity", "medium")) in {"medium", "high"}
    if sensitive and int(row.get("oil_conflict", 0) or 0) == 1:
        return "energy_input_pressure"
    if sensitive and int(row.get("oil_support", 0) or 0) == 1:
        return "energy_input_support"
    return "energy_neutral"


def capex_demand_support_state(row: pd.Series) -> str:
    demand_sensitive = str(row.get("capex_demand_sensitivity", "medium")) in {"medium", "high"}
    supply_or_contract = (
        float(row.get("positive_contract_customer_count", 0) or 0) > 0
        or float(row.get("content_supply_demand_flag", 0) or 0) == 1
        or float(row.get("positive_backlog_order_count", 0) or 0) > 0
    )
    if demand_sensitive and supply_or_contract and int(row.get("support_count", 0) or 0) >= 1:
        return "capex_demand_support"
    if demand_sensitive and int(row.get("conflict_count", 0) or 0) >= 2:
        return "capex_demand_pressure"
    return "capex_demand_neutral"


def policy_geopolitical_support_state(row: pd.Series) -> str:
    sensitive = str(row.get("policy_sensitivity", "medium")) in {"medium", "high"}
    theme = str(row.get("theme_id", ""))
    policy_event = (
        float(row.get("temporal_political_fresh_pre72h_flag", 0) or 0) == 1
        or float(row.get("temporal_geopolitical_fresh_pre72h_flag", 0) or 0) == 1
        or float(row.get("geopolitical_event_pre7d_flag", 0) or 0) == 1
        or float(row.get("political_statement_pre7d_flag", 0) or 0) == 1
    )
    if sensitive and policy_event and theme in {"aerospace_defense_space", "power_grid_electrification", "ai_semiconductors", "cybersecurity"}:
        return "policy_geopolitical_support"
    if sensitive and policy_event:
        return "policy_geopolitical_mixed"
    return "policy_geopolitical_neutral"


def adoption_support_state(row: pd.Series) -> str:
    theme = str(row.get("theme_id", ""))
    catalyst = str(row.get("catalyst_quality_tier", ""))
    direct = float(row.get("content_direct_bullish_count", 0) or 0) > 0
    if theme in {"ai_semiconductors", "cloud_ai_platforms", "data_devops_software", "industrial_automation_robotics", "cybersecurity"}:
        if catalyst in {"very_strong_catalyst", "strong_catalyst"} and direct:
            return "adoption_support"
        if catalyst == "medium_catalyst":
            return "adoption_unproven"
    return "adoption_neutral"


def mechanism_relation_state_raw(row: pd.Series) -> str:
    if not is_task639_row(row):
        return "not_task639_signal"
    quality = str(row.get("catalyst_quality_tier", ""))
    price = str(row.get("price_acceptance_state", ""))
    pressure = int(row.get("mechanism_pressure_count", 0) or 0)
    support = int(row.get("mechanism_support_count", 0) or 0)
    if price == "price_acceptance_rejected":
        return "price_rejected_company_positive"
    if pressure >= 2 and quality in {"weak_catalyst", "medium_catalyst"}:
        return "mechanism_blocker_company_positive"
    if pressure >= 1 and support >= 1:
        return "mechanism_offsetting_company_positive"
    if pressure >= 1:
        return "mechanism_pressure_company_positive"
    if support >= 2 and quality in {"very_strong_catalyst", "strong_catalyst"} and price in {"price_acceptance_strong", "price_acceptance_accepted"}:
        return "mechanism_reinforcing_company_positive"
    if quality in {"very_strong_catalyst", "strong_catalyst"} and price in {"price_acceptance_strong", "price_acceptance_accepted"}:
        return "company_quality_price_confirmed"
    return "company_positive_needs_confirmation"


def candidate_action_family(row: pd.Series) -> str:
    if not is_task639_row(row):
        return "NOT_TASK639_SIGNAL"
    if int(row.get("mechanism_sparse_cell_flag", 0) or 0) == 1:
        return "RESEARCH_ONLY"
    state = str(row.get("mechanism_relation_state_raw", ""))
    price = str(row.get("price_acceptance_state", ""))
    if state == "mechanism_reinforcing_company_positive":
        return "STRENGTH_HOLD_CANDIDATE"
    if state in {"mechanism_pressure_company_positive", "mechanism_offsetting_company_positive"}:
        return "REDUCE_DURATION"
    if state in {"mechanism_blocker_company_positive", "price_rejected_company_positive"}:
        return "CONFIRMATION_REQUIRED"
    if price == "price_acceptance_neutral":
        return "CONFIRMATION_REQUIRED"
    return "BASELINE_ALLOWED"


def scenario_base_case(row: pd.Series) -> str:
    state = str(row.get("mechanism_relation_state_raw", ""))
    if state == "mechanism_reinforcing_company_positive":
        return "company_catalyst_compounds_with_macro_mechanism"
    if state == "company_quality_price_confirmed":
        return "company_catalyst_can_work_if_price_acceptance_persists"
    if state == "mechanism_offsetting_company_positive":
        return "company_catalyst_faces_mixed_macro_transmission"
    if state == "mechanism_pressure_company_positive":
        return "company_catalyst_faces_funding_duration_or_energy_pressure"
    if state == "mechanism_blocker_company_positive":
        return "macro_mechanism_pressure_can_overwhelm_weak_catalyst"
    if state == "price_rejected_company_positive":
        return "narrative_not_confirmed_by_tape"
    if state == "company_positive_needs_confirmation":
        return "positive_company_news_needs_tape_or_mechanism_confirmation"
    if state == "not_task639_signal":
        return "outside_task639_signal_scope"
    return "research_only_sparse_or_unknown"


def scenario_invalidation_condition(row: pd.Series) -> str:
    action = str(row.get("candidate_action_family", ""))
    price = str(row.get("price_acceptance_state", ""))
    if action == "STRENGTH_HOLD_CANDIDATE":
        return "invalidate_if_price_acceptance_fades_or_funding_duration_pressure_rises"
    if action == "REDUCE_DURATION":
        return "invalidate_reduction_if_price_acceptance_is_strong_and_catalyst_quality_is_very_strong"
    if action == "CONFIRMATION_REQUIRED":
        return "invalidate_entry_if_price_acceptance_stays_rejected_or_macro_pressure_count_persists"
    if action == "RESEARCH_ONLY":
        return "do_not_trade_until_sparse_cell_has_oos_evidence"
    if price == "price_acceptance_rejected":
        return "do_not_promote_without_later_price_acceptance"
    return "invalidate_if_validation_or_recent_oos_no_longer_beats_baseline"


def company_source_assignment_certified_flag(row: pd.Series) -> int:
    has_linked_event = float(row.get("linked_event_count", 0) or 0) > 0
    has_source_text = float(row.get("source_text_certified_event_count", 0) or 0) > 0
    no_inferred_lifecycle = int(row.get("inferred_lifecycle_matching_used_flag", 0) or 0) == 0
    no_gpt_source = (
        int(row.get("gpt_or_plugin_used_as_source_flag_task617", 0) or 0) == 0
        and int(row.get("tq_gpt_or_plugin_used_as_source_flag", 0) or 0) == 0
        and int(row.get("temporal_gpt_or_plugin_used_as_source_flag", 0) or 0) == 0
    )
    return int(has_linked_event and has_source_text and no_inferred_lifecycle and no_gpt_source)


def content_prediction_assignment_certified_flag(row: pd.Series) -> int:
    has_prediction = float(row.get("content_prediction_certified_event_count", 0) or 0) > 0
    no_label_use = (
        int(row.get("label_used_in_assignment_flag", 0) or 0) == 0
        and int(row.get("temporal_label_used_in_assignment_flag", 0) or 0) == 0
    )
    return int(has_prediction and no_label_use and company_source_assignment_certified_flag(row) == 1)


def theme_price_assignment_certified_flag(row: pd.Series) -> int:
    no_inferred_lifecycle = int(row.get("inferred_lifecycle_matching_used_flag", 0) or 0) == 0
    has_entry = pd.notna(row.get("entry_ts")) and pd.notna(row.get("entry_price"))
    has_theme = pd.notna(row.get("theme_id")) and pd.notna(row.get("theme_ret20_prev"))
    has_price_context = pd.notna(row.get("price_acceptance_score")) and pd.notna(row.get("intraday_entry_state_v4"))
    return int(no_inferred_lifecycle and has_entry and has_theme and has_price_context)


def relation_assignment_certified_flag(row: pd.Series) -> int:
    if company_source_assignment_certified_flag(row) != 1 or theme_price_assignment_certified_flag(row) != 1:
        return 0
    state = str(row.get("mechanism_relation_state_raw", ""))
    if state in {"company_quality_price_confirmed", "company_positive_needs_confirmation", "price_rejected_company_positive"}:
        return 1
    return int(int(row.get("macro_assignment_certified_flag", 0) or 0) == 1)


def assignment_certification_scope(row: pd.Series) -> str:
    if int(row.get("allocation_assignment_ready_flag", 0) or 0) != 1:
        return "research_only_not_assignment_ready"
    if int(row.get("macro_assignment_certified_flag", 0) or 0) == 1:
        return "company_content_theme_price_macro_certified"
    return "company_content_theme_price_certified_macro_diagnostic"


def assignment_block_reason(row: pd.Series) -> str:
    missing = []
    if int(row.get("company_source_assignment_certified_flag", 0) or 0) != 1:
        missing.append("company_source_not_certified")
    if int(row.get("content_prediction_assignment_certified_flag", 0) or 0) != 1:
        missing.append("content_prediction_not_certified")
    if int(row.get("theme_price_assignment_certified_flag", 0) or 0) != 1:
        missing.append("theme_price_not_certified")
    if int(row.get("portfolio_capacity_assignment_certified_flag", 0) or 0) != 1:
        missing.append("portfolio_capacity_not_certified")
    if int(row.get("macro_assignment_certified_flag", 0) or 0) != 1:
        missing.append("macro_diagnostic_only")
    return "|".join(missing) if missing else "assignment_ready"


def build_mechanism_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    core = task639_core(panel)
    rows = []
    for keys, group in core.groupby(["split_name", "theme_id", "mechanism_relation_state"], dropna=False):
        split, theme, state = keys
        ret = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
        rows.append(
            {
                "split_name": split,
                "theme_id": theme,
                "mechanism_relation_state": state,
                "trade_count": int(len(group)),
                "avg_return_pct": float(ret.mean() * 100.0) if ret.notna().any() else 0.0,
                "win_rate": float(ret.gt(0).mean()) if ret.notna().any() else 0.0,
                "entry_reduce_failure_rate": float(ret.le(-0.03).mean()) if ret.notna().any() else 0.0,
                "large_loss_rate": float(ret.le(-0.10).mean()) if ret.notna().any() else 0.0,
                "mechanism_sparse_cell_flag": int(group["mechanism_sparse_cell_flag"].max()),
                "evaluation_only_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values(["split_name", "trade_count"], ascending=[True, False]).reset_index(drop=True)


def build_candidate_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, selected in candidate_panels(panel).items():
        metrics = run_account(selected, "equal_max5", qqq)
        rows.append(row_from_metrics(name, "all", selected, metrics))
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_split_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_name in ["validation", "recent_oos"]:
        split_panel = panel[panel["split_name"].astype(str).eq(split_name)].copy()
        for name, selected in candidate_panels(split_panel).items():
            metrics = run_account(selected, "equal_max5", qqq)
            rows.append(row_from_metrics(name, split_name, selected, metrics))
    return pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)


def candidate_panels(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = task639_core(panel)
    if base.empty:
        return {"baseline_task639_core": base}
    # Task661 is a relation-engine diagnostic. It classifies economic
    # transmission and action families, but it must not introduce arbitrary
    # fixed-hold or timing override rules.
    return {
        "baseline_task639_core": base,
        "diagnostic_relation_state_only_no_exit_override": base.copy(),
    }


def eligible_ids(base: pd.DataFrame, action_family: str) -> set[str]:
    eligible = base[
        base["candidate_action_family"].astype(str).eq(action_family)
        & base["macro_action_allowed_flag"].eq(1)
        & base["mechanism_sparse_cell_flag"].eq(0)
    ].copy()
    return set(eligible["lifecycle_id"].astype(str))


def eligible_state_ids(base: pd.DataFrame, states: set[str]) -> set[str]:
    eligible = base[
        base["mechanism_relation_state_raw"].astype(str).isin(states)
        & base["macro_action_allowed_flag"].eq(1)
        & base["mechanism_sparse_cell_flag"].eq(0)
    ].copy()
    return set(eligible["lifecycle_id"].astype(str))


def row_from_metrics(name: str, split_name: str, selected: pd.DataFrame, metrics: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_name": name,
        "split_name": split_name,
        "initial_capital_usd": INITIAL_CAPITAL_USD,
        "source_trade_count": int(len(selected)),
        "accepted_trade_count": int(metrics["accepted_trade_count"]),
        "final_capital_usd": float(metrics["final_capital_usd"]),
        "capital_return_pct": float(metrics["capital_return_pct"]),
        "max_drawdown_pct": float(metrics["max_drawdown_pct"]),
        "entry_reduce_failure_rate": float(metrics["entry_reduce_failure_rate"]),
        "qqq_final_capital_usd": float(metrics["qqq_final_capital_usd"]),
        "beats_qqq_flag": int(metrics["beats_qqq_flag"]),
        "label_used_in_assignment_flag": 0,
        "return_used_in_assignment_flag": 0,
        "forbidden_macro_authority_flag": int(any(token in name for token in ["boost", "standalone", "hard_block", "full_entry"])),
        "diagnostic_skip_flag": int(name.startswith("diagnostic_skip")),
    }


def choose_best_candidate(candidate_grid: pd.DataFrame) -> str:
    nonbase = candidate_grid[~candidate_grid["candidate_name"].eq("baseline_task639_core") & ~candidate_grid["candidate_name"].str.startswith("diagnostic_skip")]
    if nonbase.empty:
        return "baseline_task639_core"
    return str(nonbase.sort_values("final_capital_usd", ascending=False).iloc[0]["candidate_name"])


def build_accepted_trade_attribution(panel: pd.DataFrame, candidate_name: str) -> pd.DataFrame:
    base = candidate_panels(panel)["baseline_task639_core"]
    candidate = candidate_panels(panel)[candidate_name]
    _, base_accepted = simulate_account(base, "equal_max5")
    _, candidate_accepted = simulate_account(candidate, "equal_max5")
    base_map = summarize_accepted(base_accepted, "task639")
    cand_map = summarize_accepted(candidate_accepted, "task661")
    all_ids = sorted(set(base_map).union(cand_map))
    rows = []
    state_cols = [
        "symbol",
        "split_name",
        "theme_id",
        "mechanism_relation_state",
        "candidate_action_family",
        "catalyst_quality_tier",
        "price_acceptance_state",
        "net_return_from_entry",
    ]
    core_first = task639_core(panel).drop_duplicates("lifecycle_id").set_index("lifecycle_id")
    for lifecycle_id in all_ids:
        state = core_first.loc[lifecycle_id] if lifecycle_id in core_first.index else pd.Series(dtype=object)
        base_row = base_map.get(lifecycle_id, {})
        cand_row = cand_map.get(lifecycle_id, {})
        rows.append(
            {
                "lifecycle_id": lifecycle_id,
                "symbol": state.get("symbol", base_row.get("symbol", cand_row.get("symbol", ""))),
                "split_name": state.get("split_name", ""),
                "theme_id": state.get("theme_id", ""),
                "mechanism_relation_state": state.get("mechanism_relation_state", ""),
                "candidate_action_family": state.get("candidate_action_family", ""),
                "catalyst_quality_tier": state.get("catalyst_quality_tier", ""),
                "price_acceptance_state": state.get("price_acceptance_state", ""),
                "task639_accepted_flag": int(lifecycle_id in base_map),
                "task661_accepted_flag": int(lifecycle_id in cand_map),
                "task639_timing_mode": base_row.get("timing_mode", ""),
                "task639_exit_mode": base_row.get("exit_mode", ""),
                "task661_timing_mode": cand_row.get("timing_mode", ""),
                "task661_exit_mode": cand_row.get("exit_mode", ""),
                "task639_return_pct": float(base_row.get("net_return_from_entry", 0.0)) * 100.0 if base_row else 0.0,
                "task661_return_pct": float(cand_row.get("net_return_from_entry", 0.0)) * 100.0 if cand_row else 0.0,
                "changed_flag": int(base_row.get("timing_mode", "") != cand_row.get("timing_mode", "") or base_row.get("exit_mode", "") != cand_row.get("exit_mode", "") or int(lifecycle_id in base_map) != int(lifecycle_id in cand_map)),
                "attribution_note": attribution_note(base_row, cand_row),
                "evaluation_only_flag": 1,
            }
        )
    return pd.DataFrame(rows)


def summarize_accepted(accepted: pd.DataFrame, prefix: str) -> dict[str, dict[str, object]]:
    if accepted.empty:
        return {}
    cols = ["lifecycle_id", "symbol", "timing_mode", "exit_mode", "net_return_from_entry"]
    return accepted[cols].drop_duplicates("lifecycle_id").set_index("lifecycle_id").to_dict(orient="index")


def attribution_note(base_row: dict[str, object], cand_row: dict[str, object]) -> str:
    if base_row and cand_row:
        if base_row.get("timing_mode") == cand_row.get("timing_mode") and base_row.get("exit_mode") == cand_row.get("exit_mode"):
            return "preserved"
        return "modified"
    if base_row and not cand_row:
        return "removed_or_capacity_skipped"
    if cand_row and not base_row:
        return "added_or_capacity_released"
    return "not_accepted"


def build_oos_effect_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    candidates = candidate_panels(panel)
    baseline = candidates["baseline_task639_core"]
    for name, selected in candidates.items():
        if name == "baseline_task639_core":
            continue
        for split_name in ["validation", "recent_oos"]:
            base_split = baseline[baseline["split_name"].astype(str).eq(split_name)]
            cand_split = selected[selected["split_name"].astype(str).eq(split_name)]
            rows.append(oos_delta_row(name, split_name, base_split, cand_split))
    return pd.DataFrame(rows)


def oos_delta_row(name: str, split_name: str, base: pd.DataFrame, candidate: pd.DataFrame) -> dict[str, object]:
    base_by_id = base.drop_duplicates("lifecycle_id").set_index("lifecycle_id")
    cand_by_id = candidate.drop_duplicates("lifecycle_id").set_index("lifecycle_id")
    base_ids = set(base_by_id.index.astype(str))
    cand_ids = set(cand_by_id.index.astype(str))
    changed = base_ids.symmetric_difference(cand_ids)
    common = base_ids.intersection(cand_ids)
    modified = [
        lifecycle_id
        for lifecycle_id in common
        if str(base_by_id.loc[lifecycle_id].get("timing_mode")) != str(cand_by_id.loc[lifecycle_id].get("timing_mode"))
        or str(base_by_id.loc[lifecycle_id].get("exit_mode")) != str(cand_by_id.loc[lifecycle_id].get("exit_mode"))
    ]
    added = cand_ids - base_ids
    removed = base_ids - cand_ids
    return {
        "candidate_name": name,
        "split_name": split_name,
        "changed_trade_count": int(len(changed) + len(modified)),
        "added_winners": count_return(cand_by_id, added, True),
        "added_losers": count_return(cand_by_id, added, False),
        "removed_winners": count_return(base_by_id, removed, True),
        "removed_losers": count_return(base_by_id, removed, False),
        "modified_count": int(len(modified)),
        "baseline_avg_return_pct": pct_mean(base),
        "candidate_avg_return_pct": pct_mean(candidate),
        "avg_return_delta_pct_point": pct_mean(candidate) - pct_mean(base),
        "evaluation_only_flag": 1,
    }


def count_return(frame: pd.DataFrame, ids: set[str], positive: bool) -> int:
    if not ids:
        return 0
    vals = pd.to_numeric(frame.loc[list(ids)]["net_return_from_entry"], errors="coerce")
    return int(vals.gt(0).sum() if positive else vals.le(0).sum())


def pct_mean(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    return float(pd.to_numeric(frame["net_return_from_entry"], errors="coerce").mean() * 100.0)


def build_promotion_report(
    candidate_grid: pd.DataFrame,
    split_grid: pd.DataFrame,
    task659_grid: pd.DataFrame,
    task659_split_grid: pd.DataFrame,
) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    task659_best = task659_grid.sort_values("final_capital_usd", ascending=False).iloc[0]
    baseline_validation = split_grid[split_grid["candidate_name"].eq("baseline_task639_core") & split_grid["split_name"].eq("validation")].iloc[0]
    baseline_recent = split_grid[split_grid["candidate_name"].eq("baseline_task639_core") & split_grid["split_name"].eq("recent_oos")].iloc[0]
    rows = []
    for _, row in candidate_grid.iterrows():
        name = str(row["candidate_name"])
        validation = split_grid[split_grid["candidate_name"].eq(name) & split_grid["split_name"].eq("validation")].iloc[0]
        recent = split_grid[split_grid["candidate_name"].eq(name) & split_grid["split_name"].eq("recent_oos")].iloc[0]
        beats_task639 = int(float(row["final_capital_usd"]) > float(baseline["final_capital_usd"]))
        beats_task659 = int(float(row["final_capital_usd"]) > float(task659_best["final_capital_usd"]))
        dd_better = int(float(row["max_drawdown_pct"]) > float(baseline["max_drawdown_pct"]))
        validation_improves = int(float(validation["final_capital_usd"]) > float(baseline_validation["final_capital_usd"]))
        recent_improves = int(float(recent["final_capital_usd"]) > float(baseline_recent["final_capital_usd"]))
        validation_dd_ok = int(float(validation["max_drawdown_pct"]) >= float(baseline_validation["max_drawdown_pct"]))
        recent_dd_ok = int(float(recent["max_drawdown_pct"]) >= float(baseline_recent["max_drawdown_pct"]))
        promotion_allowed = int(int(row["forbidden_macro_authority_flag"]) == 0 and int(row["diagnostic_skip_flag"]) == 0)
        promotion = int(
            name != "baseline_task639_core"
            and beats_task639
            and dd_better
            and validation_improves
            and recent_improves
            and validation_dd_ok
            and recent_dd_ok
            and int(validation["beats_qqq_flag"]) == 1
            and int(recent["beats_qqq_flag"]) == 1
            and promotion_allowed == 1
        )
        rows.append(
            {
                "candidate_name": name,
                "final_capital_usd": float(row["final_capital_usd"]),
                "max_drawdown_pct": float(row["max_drawdown_pct"]),
                "beats_task639_baseline_flag": beats_task639,
                "beats_task659_best_flag": beats_task659,
                "drawdown_better_than_task639_flag": dd_better,
                "validation_improves_task639_flag": validation_improves,
                "recent_oos_improves_task639_flag": recent_improves,
                "validation_drawdown_not_worse_flag": validation_dd_ok,
                "recent_oos_drawdown_not_worse_flag": recent_dd_ok,
                "validation_beats_qqq_flag": int(validation["beats_qqq_flag"]),
                "recent_oos_beats_qqq_flag": int(recent["beats_qqq_flag"]),
                "forbidden_macro_authority_flag": int(row["forbidden_macro_authority_flag"]),
                "diagnostic_skip_flag": int(row["diagnostic_skip_flag"]),
                "promotion_allowed_flag": promotion_allowed,
                "full_period_research_candidate_flag": int(name != "baseline_task639_core" and beats_task639 and dd_better and promotion_allowed == 1),
                "promotion_candidate_flag": promotion,
                "reason": promotion_reason(promotion, validation_improves, recent_improves, dd_better, promotion_allowed),
            }
        )
    return pd.DataFrame(rows).sort_values(["promotion_candidate_flag", "final_capital_usd"], ascending=[False, False]).reset_index(drop=True)


def promotion_reason(promotion: int, validation: int, recent: int, dd: int, allowed: int) -> str:
    if promotion:
        return "passes_all_task661_gates"
    if not allowed:
        return "diagnostic_or_forbidden_authority"
    if not dd:
        return "drawdown_not_better"
    if not validation or not recent:
        return "validation_or_recent_oos_effect_missing"
    return "return_gate_missing"


def build_not_do_matrix(candidate_grid: pd.DataFrame, promotion: pd.DataFrame) -> pd.DataFrame:
    diagnostic_promoted = promotion[promotion["candidate_name"].str.startswith("diagnostic_skip")]["promotion_candidate_flag"].sum()
    return pd.DataFrame(
        [
            {"blocker": "macro_standalone_entry", "violation_count": 0, "pass_flag": 1},
            {"blocker": "macro_hard_block", "violation_count": 0, "pass_flag": 1},
            {"blocker": "macro_full_entry_promotion", "violation_count": 0, "pass_flag": 1},
            {"blocker": "macro_size_boost", "violation_count": 0, "pass_flag": 1},
            {"blocker": "diagnostic_skip_promoted", "violation_count": int(diagnostic_promoted), "pass_flag": int(diagnostic_promoted == 0)},
            {"blocker": "forbidden_macro_authority", "violation_count": int(candidate_grid["forbidden_macro_authority_flag"].sum()), "pass_flag": int(candidate_grid["forbidden_macro_authority_flag"].sum() == 0)},
        ]
    )


def build_pass_fail(
    template: pd.DataFrame,
    panel: pd.DataFrame,
    diagnostics: pd.DataFrame,
    promotion: pd.DataFrame,
    blockers: pd.DataFrame,
) -> pd.DataFrame:
    core = task639_core(panel)
    return pd.DataFrame(
        [
            {"gate": "economic_transmission_template_built", "pass_flag": int(len(template) >= 10), "observed_value": f"themes={len(template)}", "required_value": "all active themes have economic mechanism fields"},
            {"gate": "catalyst_quality_tier_built", "pass_flag": int("catalyst_quality_tier" in panel.columns), "observed_value": "catalyst_quality_tier present", "required_value": "contract/customer/supply/backlog/guidance/margin tiers"},
            {"gate": "price_acceptance_state_built", "pass_flag": int("price_acceptance_state" in panel.columns), "observed_value": "price_acceptance_state present", "required_value": "accepted/neutral/rejected tape state"},
            {"gate": "oos_effect_requires_distinct_improvement", "pass_flag": int(promotion["promotion_candidate_flag"].sum() > 0), "observed_value": f"promotion_candidates={int(promotion['promotion_candidate_flag'].sum())}", "required_value": "validation and recent OOS improve Task639 without worse drawdown"},
            {"gate": "scenario_invalidation_fields_built", "pass_flag": int({"scenario_base_case", "scenario_invalidation_condition"}.issubset(set(panel.columns))), "observed_value": "scenario_base_case and scenario_invalidation_condition present", "required_value": "each row has scenario and invalidation condition"},
            {"gate": "all_task639_core_rows_state_assigned", "pass_flag": int(core["mechanism_relation_state"].notna().all()), "observed_value": f"task639_core_rows={len(core)}", "required_value": "all core rows assigned mechanism relation state"},
            {"gate": "not_do_matrix_pass", "pass_flag": int(blockers["pass_flag"].eq(1).all()), "observed_value": f"violations={int(blockers['violation_count'].sum())}", "required_value": "no forbidden macro authority"},
            {"gate": "strategy_accepted", "pass_flag": 0, "observed_value": "research diagnostic only", "required_value": "requires accepted strategy gates and live readiness"},
        ]
    )


def build_decision(candidate_grid: pd.DataFrame, promotion: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    baseline = candidate_grid[candidate_grid["candidate_name"].eq("baseline_task639_core")].iloc[0]
    best = candidate_grid.iloc[0]
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    research_count = int(promotion["full_period_research_candidate_flag"].sum())
    decision = "MECHANISM_ENGINE_BUILT_NO_PROMOTION_CANDIDATE"
    if promotion_count > 0:
        decision = "MECHANISM_ENGINE_PROMOTION_CANDIDATE_FOUND_NOT_ACCEPTED"
    elif research_count > 0:
        decision = "MECHANISM_ENGINE_FULL_PERIOD_RESEARCH_CANDIDATE_OOS_BLOCKED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "task639_baseline_final_capital_usd": float(baseline["final_capital_usd"]),
                "task639_baseline_max_drawdown_pct": float(baseline["max_drawdown_pct"]),
                "best_candidate_name": best["candidate_name"],
                "best_candidate_final_capital_usd": float(best["final_capital_usd"]),
                "best_candidate_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "full_period_research_candidate_count": research_count,
                "promotion_candidate_count": promotion_count,
                "trading_promotion_pass_flag": 0,
                "next_action": "Inspect Task661 attribution and OOS audit. If no promotion candidate exists, improve mechanism definitions only through predeclared economic logic, not returns.",
            }
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    candidate_grid: pd.DataFrame,
    split_grid: pd.DataFrame,
    diagnostics: pd.DataFrame,
    oos_audit: pd.DataFrame,
    promotion: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task661 Mechanism Relation Engine",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Task639 baseline: `${float(d['task639_baseline_final_capital_usd']):.2f}`, max drawdown `{float(d['task639_baseline_max_drawdown_pct']):.2f}%`.",
        f"- Best Task661 candidate: `{d['best_candidate_name']}` = `${float(d['best_candidate_final_capital_usd']):.2f}`, max drawdown `{float(d['best_candidate_max_drawdown_pct']):.2f}%`.",
        f"- Promotion candidates: `{int(d['promotion_candidate_count'])}`.",
        "",
        "## Quant Expert Report",
        "",
        "Task661 addresses five bottlenecks from Task660: economic transmission, catalyst quality, price acceptance, OOS effect audit, and scenario/invalidation proxy states.",
        "",
        "Rule scope correction: Task661 does not introduce fixed-hold exits or timing overrides. It is a relation-state diagnostic only.",
        "",
        "### Data Source And Source Readiness",
        "",
        "Input is the Task659 theme macro company state panel. No new source is introduced and no GPT output is used as source data.",
        "",
        "### Exact Join Keys",
        "",
        "`lifecycle_id`, `timing_mode`, `exit_mode`, `entry_ts`, and `split_name`.",
        "",
        "### Leakage Audit",
        "",
        "The institutional transmission template is static and marked `return_tuned_flag=0`. Returns and labels are evaluation-only.",
        "",
        "### Candidate Grid",
        "",
        table(candidate_grid),
        "",
        "### Split/OOS Metrics",
        "",
        table(split_grid),
        "",
        "### Mechanism Diagnostics",
        "",
        table(diagnostics),
        "",
        "### OOS Effect Audit",
        "",
        table(oos_audit),
        "",
        "### Promotion Report",
        "",
        table(promotion),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We made the engine more professional, but we still do not approve trading.",
        "",
        "The engine now asks better questions:",
        "",
        "- Is the macro driver really connected to this theme?",
        "- Does that connection hit funding, duration, energy, capex demand, policy, or adoption?",
        "- Is the company news strong or weak?",
        "- Did the price accept the story?",
        "- Did validation and recent OOS actually improve?",
        "",
        "If the answer is not proven in OOS, the action stays research-only.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `institutional_transmission_template.csv`",
        "- `theme_mechanism_state_panel.csv`",
        "- `mechanism_relation_diagnostics.csv`",
        "- `mechanism_soft_wrapper_grid.csv`",
        "- `mechanism_split_account_grid.csv`",
        "- `oos_effect_audit.csv`",
        "- `accepted_trade_attribution.csv`",
        "- `promotion_report.csv`",
        "- `not_do_matrix.csv`",
        "- `task_661_pass_fail_matrix.csv`",
        "- `task_661_decision.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_661_mechanism_relation_engine.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    clipped = df.head(max_rows)
    cols = [str(c) for c in clipped.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in clipped.iterrows():
        lines.append("| " + " | ".join(cell(row.get(c, "")) for c in clipped.columns) + " |")
    return "\n".join(lines)


def cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "/").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = build_task661_mechanism_relation_engine(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best={decision['best_candidate_name']} "
        f"final={float(decision['best_candidate_final_capital_usd']):.2f} "
        f"promotion={int(decision['promotion_candidate_count'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
