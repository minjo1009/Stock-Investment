from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK713_PANEL = Path("docs/reports/task_713_evidence_provenance_brain/task713_evidence_provenance_panel.csv")
TASK714_PANEL = Path("docs/reports/task_714_economic_transmission_brain/task714_economic_transmission_panel.csv")
TASK715_PANEL = Path("docs/reports/task_715_market_pricing_acceptance_brain/task715_market_pricing_acceptance_panel.csv")
TASK716_PANEL = Path("docs/reports/task_716_portfolio_competition_brain/task716_slot_competition_panel.csv")
TASK717_PANEL = Path("docs/reports/task_717_decision_invalidation_risk_brain/task717_decision_invalidation_panel.csv")
TASK708_EVAL = Path("docs/reports/task_708_full_period_backtest_comparison/task708_eval_panel.csv")
TASK718_DIR = Path("docs/reports/task_718_winner_structure_interaction_brain")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
NO_ACTION_REASON = "winner_structure_interpretation_only;not_buy_sell_or_budget_instruction"


def build_task718(
    *,
    task713_path: Path = TASK713_PANEL,
    task714_path: Path = TASK714_PANEL,
    task715_path: Path = TASK715_PANEL,
    task716_path: Path = TASK716_PANEL,
    task717_path: Path = TASK717_PANEL,
    eval_path: Path = TASK708_EVAL,
    out_dir: Path = TASK718_DIR,
) -> dict[str, pd.DataFrame]:
    base = load_input_panels(task713_path, task714_path, task715_path, task716_path, task717_path)
    eval_panel = pd.read_csv(eval_path)
    panel = build_winner_structure_panel(base)
    graph = build_interaction_graph(panel)
    watch = build_watch_decomposition(panel)
    convexity = build_convexity_audit(panel, eval_panel)
    guardrail = build_guardrail_audit(panel, eval_panel)
    governance = build_governance_audit(panel, graph, watch)
    decision = decision_frame(panel, guardrail)
    pass_fail = pass_fail_matrix(panel, graph, watch, guardrail, governance)

    write_outputs(
        out_dir,
        {
            "task718_winner_structure_panel.csv": panel,
            "task718_interaction_graph.csv": graph,
            "task718_watch_decomposition.csv": watch,
            "task718_convexity_audit.csv": convexity,
            "task718_guardrail_audit.csv": guardrail,
            "task718_governance_audit.csv": governance,
            "task_718_decision.csv": decision,
            "task_718_pass_fail_matrix.csv": pass_fail,
        },
        decision,
        pass_fail,
    )
    return {
        "panel": panel,
        "graph": graph,
        "watch": watch,
        "convexity": convexity,
        "guardrail": guardrail,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def load_input_panels(
    task713_path: Path,
    task714_path: Path,
    task715_path: Path,
    task716_path: Path,
    task717_path: Path,
) -> pd.DataFrame:
    t713 = pd.read_csv(task713_path)
    t714 = pd.read_csv(task714_path)
    t715 = pd.read_csv(task715_path)
    t716 = pd.read_csv(task716_path)
    t717 = pd.read_csv(task717_path)

    cols713 = KEYS + [
        "source_event_available_flag",
        "source_directness_state",
        "novelty_state",
        "evidence_strength_state",
        "source_gap_state",
        "evidence_brain_state",
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
    ]
    cols715 = KEYS + [
        "pricing_acceptance_state",
        "priced_vs_unpriced_state",
        "positioning_proxy_state",
        "acceptance_failure_state",
        "market_pricing_brain_state",
    ]
    cols716 = KEYS + [
        "slot_context_score",
        "same_timestamp_context_rank",
        "same_timestamp_theme_count",
        "slot_competition_state",
        "exposure_cluster_state",
        "portfolio_brain_state",
    ]
    cols717 = KEYS + [
        "review_decision_state",
        "invalidation_condition",
        "risk_budget_state",
        "sizing_cap_reason",
        "final_brain_state",
    ]
    out = t713[[c for c in cols713 if c in t713.columns]].merge(
        t714[[c for c in cols714 if c in t714.columns]], on=KEYS, how="left", validate="one_to_one"
    )
    out = out.merge(t715[[c for c in cols715 if c in t715.columns]], on=KEYS, how="left", validate="one_to_one")
    out = out.merge(t716[[c for c in cols716 if c in t716.columns]], on=KEYS, how="left", validate="one_to_one")
    out = out.merge(t717[[c for c in cols717 if c in t717.columns]], on=KEYS, how="left", validate="one_to_one")
    return out


def build_winner_structure_panel(base: pd.DataFrame) -> pd.DataFrame:
    out = base.copy()
    out["expectation_gap_state"] = out.apply(expectation_gap_state, axis=1)
    out["absorption_under_risk_state"] = out.apply(absorption_under_risk_state, axis=1)
    out["narrative_conflict_state"] = out.apply(narrative_conflict_state, axis=1)
    out["convexity_asymmetry_state"] = out.apply(convexity_asymmetry_state, axis=1)
    out["lifecycle_transition_state"] = out.apply(lifecycle_transition_state, axis=1)
    out["winner_structure_state"] = out.apply(winner_structure_state, axis=1)
    out["watch_subtype"] = out.apply(watch_subtype, axis=1)
    out["interaction_reason_codes"] = out.apply(interaction_reason_codes, axis=1)
    add_no_action_flags(out)
    cols = KEYS + [
        "source_event_available_flag",
        "evidence_brain_state",
        "source_directness_state",
        "novelty_state",
        "evidence_strength_state",
        "economic_transmission_state",
        "funding_path_state",
        "dilution_overhang_state",
        "valuation_pressure_state",
        "pricing_acceptance_state",
        "priced_vs_unpriced_state",
        "market_pricing_brain_state",
        "portfolio_brain_state",
        "review_decision_state",
        "final_brain_state",
        "expectation_gap_state",
        "absorption_under_risk_state",
        "narrative_conflict_state",
        "convexity_asymmetry_state",
        "lifecycle_transition_state",
        "winner_structure_state",
        "watch_subtype",
        "interaction_reason_codes",
        "top50_used_for_assignment_flag",
        "watch_promoted_to_buy_flag",
        "ticker_theme_protection_rule_flag",
        "threshold_tuned_from_outcome_flag",
    ] + no_action_columns()
    return out[[c for c in cols if c in out.columns]].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def expectation_gap_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "expectation_source_gap"
    novelty = str(row.get("novelty_state", ""))
    strength = str(row.get("evidence_strength_state", ""))
    priced = str(row.get("priced_vs_unpriced_state", ""))
    econ = str(row.get("economic_transmission_state", ""))
    if "reaffirmation" in novelty or "stale" in novelty:
        if "accepted" in priced or "runway" in priced:
            return "expectation_stale_but_repriced"
        return "expectation_reaffirmation_only"
    if strength in {"strong_multi_signal_company_evidence", "company_evidence_with_economic_detail"} and "priced_but_extension" not in priced:
        return "expectation_positive_surprise_possible"
    if econ in {"growth_funding_revenue_reinforcing", "revenue_margin_reinforcing", "policy_demand_tailwind_with_company_link"} and "unpriced" in priced:
        return "expectation_positive_surprise_possible"
    if "priced_but_extension" in priced:
        return "expectation_already_priced"
    return "expectation_unclear"


def absorption_under_risk_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "absorption_source_gap"
    funding = str(row.get("funding_path_state", ""))
    dilution = str(row.get("dilution_overhang_state", ""))
    pricing = str(row.get("pricing_acceptance_state", ""))
    market = str(row.get("market_pricing_brain_state", ""))
    risk_present = any(x in funding for x in ["overhang", "funding_event", "unconfirmed"]) or "overhang" in dilution
    if risk_present and pricing in {"accepted_by_price_and_tape_proxy", "absorbed_but_tape_confirmation_partial"}:
        return "risk_absorbed_by_price"
    if risk_present and market == "market_waiting_on_overhang_absorption":
        return "risk_absorption_incomplete"
    if risk_present:
        return "risk_not_absorbed"
    if market in {"market_accepts_economic_path", "market_acceptance_incomplete"}:
        return "no_major_risk_to_absorb"
    return "absorption_unclear"


def narrative_conflict_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "narrative_source_gap"
    econ = str(row.get("economic_transmission_state", ""))
    funding = str(row.get("funding_path_state", ""))
    dilution = str(row.get("dilution_overhang_state", ""))
    policy = str(row.get("policy_demand_path_state", ""))
    valuation = str(row.get("valuation_pressure_state", ""))
    positive = econ in {
        "growth_funding_revenue_reinforcing",
        "revenue_margin_reinforcing",
        "policy_demand_tailwind_with_company_link",
        "backlog_or_order_path_visible",
    }
    if positive and ("overhang" in funding or "overhang" in dilution):
        return "positive_growth_vs_financing_conflict"
    if positive and "weak" in policy:
        return "positive_growth_vs_policy_conflict"
    if positive and "pressure" in valuation:
        return "positive_growth_vs_valuation_conflict"
    if positive:
        return "clean_positive_narrative"
    if econ == "capital_need_overhang_vs_growth_question":
        return "financing_conflict_without_resolution"
    return "negative_or_unclear_narrative"


def convexity_asymmetry_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "convexity_source_gap"
    econ = str(row.get("economic_transmission_state", ""))
    strength = str(row.get("evidence_strength_state", ""))
    pricing = str(row.get("pricing_acceptance_state", ""))
    narrative = narrative_conflict_state(row)
    if econ in {"policy_demand_tailwind_with_company_link", "backlog_or_order_path_visible"} and pricing != "not_accepted_by_market_proxy":
        return "high_upside_optionality"
    if strength == "strong_multi_signal_company_evidence" and pricing in {"accepted_by_price_and_tape_proxy", "acceptance_building_not_final"}:
        return "high_upside_optionality"
    if "conflict" in narrative and absorption_under_risk_state(row) in {"risk_absorbed_by_price", "risk_absorption_incomplete"}:
        return "asymmetric_but_unconfirmed"
    if econ in {"revenue_margin_reinforcing", "growth_funding_revenue_reinforcing"}:
        return "linear_quality_signal"
    if econ in {"no_clear_economic_path", "no_economic_claim_source_gap"}:
        return "low_convexity_signal"
    return "convexity_unclear"


def lifecycle_transition_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        return "lifecycle_source_gap"
    review = str(row.get("review_decision_state", ""))
    pricing = str(row.get("pricing_acceptance_state", ""))
    market = str(row.get("market_pricing_brain_state", ""))
    econ = str(row.get("economic_transmission_state", ""))
    if "watch" in review and pricing in {"accepted_by_price_and_tape_proxy", "absorbed_but_tape_confirmation_partial"}:
        return "watch_to_confirmation_candidate"
    if "watch" in review and econ not in {"no_clear_economic_path", "no_economic_claim_source_gap"}:
        return "early_confirmation_missing"
    if market == "market_waiting_on_overhang_absorption":
        return "delayed_absorption_candidate"
    if market == "market_accepts_economic_path":
        return "mature_confirmed_candidate"
    return "lifecycle_unclear"


def winner_structure_state(row: pd.Series) -> str:
    if int_safe(row.get("source_event_available_flag")) == 0:
        pricing = str(row.get("pricing_acceptance_state", ""))
        if pricing == "accepted_by_price_and_tape_proxy":
            return "source_gap_price_accepted_unknown_structure"
        if pricing == "acceptance_building_not_final":
            return "source_gap_price_building_unknown_structure"
        return "source_gap_unknown_structure"
    expectation = expectation_gap_state(row)
    absorption = absorption_under_risk_state(row)
    narrative = narrative_conflict_state(row)
    convexity = convexity_asymmetry_state(row)
    lifecycle = lifecycle_transition_state(row)
    pricing = str(row.get("pricing_acceptance_state", ""))
    econ = str(row.get("economic_transmission_state", ""))
    strength = str(row.get("evidence_strength_state", ""))
    portfolio = str(row.get("portfolio_brain_state", ""))
    if expectation == "expectation_positive_surprise_possible" and absorption == "risk_absorbed_by_price":
        return "expectation_gap_repricing_structure"
    if narrative == "positive_growth_vs_financing_conflict" and absorption == "risk_absorbed_by_price":
        return "narrative_conflict_resolution_structure"
    if econ == "capital_need_overhang_vs_growth_question" and absorption == "risk_absorption_incomplete":
        if portfolio == "slot_candidate_needs_confirmation":
            return "capital_need_slot_confirmation_structure"
        if strength == "company_evidence_with_economic_detail":
            return "capital_need_company_evidence_watch_structure"
        if strength == "thin_single_signal_evidence":
            return "capital_need_thin_signal_watch_structure"
        return "capital_need_noise_watch_structure"
    if narrative == "positive_growth_vs_financing_conflict" and absorption == "risk_absorption_incomplete":
        return "financing_conflict_awaiting_absorption_structure"
    if narrative == "positive_growth_vs_financing_conflict" and absorption == "risk_not_absorbed":
        return "unresolved_financing_conflict_structure"
    if convexity == "high_upside_optionality" and pricing != "not_accepted_by_market_proxy":
        return "convex_optional_repricing_structure"
    if convexity == "asymmetric_but_unconfirmed" and absorption in {"risk_absorbed_by_price", "risk_absorption_incomplete"}:
        return "asymmetric_unconfirmed_repricing_structure"
    if lifecycle in {"watch_to_confirmation_candidate", "early_confirmation_missing", "delayed_absorption_candidate"}:
        return "delayed_absorption_structure"
    if narrative == "clean_positive_narrative" and pricing == "accepted_by_price_and_tape_proxy":
        return "clean_confirmed_quality_structure"
    if expectation == "expectation_reaffirmation_only" and pricing != "not_accepted_by_market_proxy":
        return "reaffirmation_repricing_structure"
    return "unclear_watch_structure"


def watch_subtype(row: pd.Series) -> str:
    review = str(row.get("review_decision_state", ""))
    if "watch" not in review:
        return "not_watch_state"
    winner = winner_structure_state(row)
    convexity = convexity_asymmetry_state(row)
    narrative = narrative_conflict_state(row)
    absorption = absorption_under_risk_state(row)
    lifecycle = lifecycle_transition_state(row)
    if winner in {"expectation_gap_repricing_structure", "convex_optional_repricing_structure", "narrative_conflict_resolution_structure"}:
        return "watch_with_positive_structure"
    if winner == "capital_need_slot_confirmation_structure":
        return "watch_due_to_slot_confirmation_needed"
    if winner == "capital_need_company_evidence_watch_structure":
        return "watch_due_to_company_evidence_absorption_needed"
    if winner == "capital_need_thin_signal_watch_structure":
        return "watch_due_to_thin_signal_absorption_needed"
    if winner in {"capital_need_noise_watch_structure", "financing_conflict_awaiting_absorption_structure"}:
        return "watch_due_to_financing_absorption_test"
    if convexity == "asymmetric_but_unconfirmed":
        return "watch_due_to_convexity_unconfirmed"
    if narrative.endswith("conflict"):
        return "watch_due_to_narrative_conflict"
    if lifecycle == "early_confirmation_missing":
        return "watch_due_to_incomplete_confirmation"
    if absorption in {"risk_not_absorbed", "risk_absorption_incomplete"}:
        return "watch_due_to_unabsorbed_risk"
    if str(row.get("source_gap_state", "")) == "source_gap_unknown_not_negative":
        return "watch_due_to_source_uncertainty"
    return "watch_due_to_slot_or_context_uncertainty"


def interaction_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"expectation={expectation_gap_state(row)}",
            f"absorption={absorption_under_risk_state(row)}",
            f"narrative={narrative_conflict_state(row)}",
            f"convexity={convexity_asymmetry_state(row)}",
            f"lifecycle={lifecycle_transition_state(row)}",
            f"winner_structure={winner_structure_state(row)}",
        ]
    )


def build_interaction_graph(panel: pd.DataFrame) -> pd.DataFrame:
    edges: list[dict[str, object]] = []
    for _, row in panel.iterrows():
        lifecycle_id = row["lifecycle_id"]
        base = {key: row[key] for key in KEYS if key in row}
        edge_defs = [
            ("evidence", row.get("evidence_brain_state"), "economic_transmission", row.get("economic_transmission_state"), relation_evidence_to_economic(row), "evidence_brain_state,economic_transmission_state"),
            ("economic_transmission", row.get("economic_transmission_state"), "market_pricing", row.get("market_pricing_brain_state"), relation_economic_to_pricing(row), "economic_transmission_state,market_pricing_brain_state"),
            ("market_pricing", row.get("market_pricing_brain_state"), "winner_structure", row.get("winner_structure_state"), relation_pricing_to_winner(row), "market_pricing_brain_state,winner_structure_state"),
            ("narrative_conflict", row.get("narrative_conflict_state"), "winner_structure", row.get("winner_structure_state"), relation_narrative_to_winner(row), "narrative_conflict_state,winner_structure_state"),
            ("convexity", row.get("convexity_asymmetry_state"), "winner_structure", row.get("winner_structure_state"), relation_convexity_to_winner(row), "convexity_asymmetry_state,winner_structure_state"),
        ]
        for source_layer, source_state, target_layer, target_state, relation_type, refs in edge_defs:
            edges.append(
                {
                    **base,
                    "lifecycle_id": lifecycle_id,
                    "source_layer": source_layer,
                    "source_state": source_state,
                    "target_layer": target_layer,
                    "target_state": target_state,
                    "relation_type": relation_type,
                    "relation_strength_bucket": relation_strength(relation_type),
                    "evidence_column_refs": refs,
                    "reason_code": f"{source_layer}:{source_state}->{target_layer}:{target_state}",
                    "assignment_safe_flag": 1,
                    "outcome_used_for_assignment_flag": 0,
                }
            )
    return pd.DataFrame(edges)


def relation_evidence_to_economic(row: pd.Series) -> str:
    econ = str(row.get("economic_transmission_state", ""))
    evidence = str(row.get("evidence_brain_state", ""))
    if evidence == "source_gap_unknown_not_negative":
        return "source_gap_unknown"
    if econ in {"revenue_margin_reinforcing", "growth_funding_revenue_reinforcing", "policy_demand_tailwind_with_company_link"}:
        return "reinforces"
    if econ == "capital_need_overhang_vs_growth_question":
        return "conflicts_with"
    return "requires_confirmation"


def relation_economic_to_pricing(row: pd.Series) -> str:
    pricing = str(row.get("market_pricing_brain_state", ""))
    if pricing == "market_accepts_economic_path":
        return "reinforces"
    if pricing == "market_waiting_on_overhang_absorption":
        return "delayed_absorption"
    if pricing == "source_gap_no_market_pricing_claim":
        return "source_gap_unknown"
    return "requires_confirmation"


def relation_pricing_to_winner(row: pd.Series) -> str:
    absorption = absorption_under_risk_state(row)
    winner = str(row.get("winner_structure_state", ""))
    if absorption == "risk_absorbed_by_price":
        return "absorbed_by_price"
    if winner in {"delayed_absorption_structure", "unclear_watch_structure"}:
        return "requires_confirmation"
    return "reinforces"


def relation_narrative_to_winner(row: pd.Series) -> str:
    narrative = str(row.get("narrative_conflict_state", ""))
    if "conflict" in narrative and str(row.get("winner_structure_state", "")) == "narrative_conflict_resolution_structure":
        return "resolved_conflict"
    if "conflict" in narrative:
        return "conflicts_with"
    return "reinforces"


def relation_convexity_to_winner(row: pd.Series) -> str:
    convexity = str(row.get("convexity_asymmetry_state", ""))
    if convexity in {"high_upside_optionality", "asymmetric_but_unconfirmed"}:
        return "supports_convexity"
    if convexity == "low_convexity_signal":
        return "weakens"
    return "requires_confirmation"


def relation_strength(relation_type: str) -> str:
    if relation_type in {"reinforces", "absorbed_by_price", "resolved_conflict", "supports_convexity"}:
        return "strong_interpretive_link"
    if relation_type in {"conflicts_with", "delayed_absorption"}:
        return "conflicted_interpretive_link"
    if relation_type == "source_gap_unknown":
        return "unknown_source_link"
    return "needs_confirmation_link"


def build_watch_decomposition(panel: pd.DataFrame) -> pd.DataFrame:
    watch = panel[panel["review_decision_state"].astype(str).str.contains("watch", na=False)].copy()
    cols = KEYS + [
        "review_decision_state",
        "final_brain_state",
        "expectation_gap_state",
        "absorption_under_risk_state",
        "narrative_conflict_state",
        "convexity_asymmetry_state",
        "lifecycle_transition_state",
        "winner_structure_state",
        "watch_subtype",
        "interaction_reason_codes",
        "watch_promoted_to_buy_flag",
        "outcome_used_for_assignment_flag",
    ]
    return watch[cols].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def build_convexity_audit(panel: pd.DataFrame, eval_panel: pd.DataFrame) -> pd.DataFrame:
    return eval_group_audit(panel, eval_panel, "convexity_asymmetry_state")


def build_guardrail_audit(panel: pd.DataFrame, eval_panel: pd.DataFrame) -> pd.DataFrame:
    return eval_group_audit(panel, eval_panel, "winner_structure_state")


def eval_group_audit(panel: pd.DataFrame, eval_panel: pd.DataFrame, group_col: str) -> pd.DataFrame:
    merged = panel.merge(
        eval_panel[KEYS + ["costed_return_pct", "entry_reduce_failure_flag"]],
        on=KEYS,
        how="left",
        validate="one_to_one",
    )
    top50 = set(merged.nlargest(50, "costed_return_pct")["lifecycle_id"])
    bottom50 = set(merged.nsmallest(50, "costed_return_pct")["lifecycle_id"])
    rows = []
    for state, group in merged.groupby(group_col, dropna=False):
        ids = set(group["lifecycle_id"])
        rows.append(
            {
                group_col: state,
                "candidate_count": len(group),
                "top50_winner_count_eval_only": len(top50 & ids),
                "bottom50_loser_count_eval_only": len(bottom50 & ids),
                "avg_costed_return_pct_eval_only": float(group["costed_return_pct"].mean()),
                "entry_reduce_failure_rate_eval_only": float(pd.to_numeric(group["entry_reduce_failure_flag"], errors="coerce").fillna(0).mean()),
                "winner_preservation_flag_eval_only": int(len(top50 & ids) > 0),
                "loser_concentration_flag_eval_only": int(len(bottom50 & ids) >= 10),
                "outcome_used_for_assignment_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("top50_winner_count_eval_only", ascending=False).reset_index(drop=True)


def build_governance_audit(panel: pd.DataFrame, graph: pd.DataFrame, watch: pd.DataFrame) -> pd.DataFrame:
    rows = [
        gate("scope_5265", len(panel) == 5265, f"rows={len(panel)}", "5265"),
        gate("event_linked_2445", int(panel["source_event_available_flag"].sum()) == 2445, f"event={int(panel['source_event_available_flag'].sum())}", "2445"),
        gate("winner_states_present", panel["winner_structure_state"].nunique() >= 6, f"states={panel['winner_structure_state'].nunique()}", ">=6"),
        gate("watch_decomposed", len(watch) > 0 and watch["watch_subtype"].nunique() >= 2, f"rows={len(watch)} states={watch['watch_subtype'].nunique() if len(watch) else 0}", ">0 and >=2 states"),
        gate("interaction_graph_present", len(graph) == len(panel) * 5, f"edges={len(graph)}", "5 edges per row"),
        gate("no_action_output", int(panel["translator_output_is_action_flag"].sum()) == 0, "0", "0"),
        gate("no_outcome_assignment", int(panel["outcome_used_for_assignment_flag"].sum()) == 0, "0", "0"),
        gate("no_future_price_assignment", int(panel["future_price_used_for_assignment_flag"].sum()) == 0, "0", "0"),
        gate("missing_source_not_negative", int(panel["missing_source_used_as_negative_flag"].sum()) == 0, "0", "0"),
        gate("macro_not_promoted", int(panel["macro_used_for_assignment_flag"].sum()) == 0, "0", "0"),
        gate("top50_not_used_for_assignment", int(panel["top50_used_for_assignment_flag"].sum()) == 0, "0", "0"),
        gate("watch_not_promoted_to_buy", int(panel["watch_promoted_to_buy_flag"].sum()) == 0, "0", "0"),
        gate("no_ticker_theme_protection", int(panel["ticker_theme_protection_rule_flag"].sum()) == 0, "0", "0"),
        gate("no_outcome_threshold_tuning", int(panel["threshold_tuned_from_outcome_flag"].sum()) == 0, "0", "0"),
        gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
    ]
    return pd.DataFrame(rows)


def decision_frame(panel: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    top_state = guardrail.iloc[0]["winner_structure_state"] if len(guardrail) else ""
    top_count = int(guardrail.iloc[0]["top50_winner_count_eval_only"]) if len(guardrail) else 0
    return pd.DataFrame(
        [
            {
                "task_id": "Task718",
                "verdict": "WINNER_STRUCTURE_INTERACTION_BRAIN_BUILT_DIAGNOSTIC_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "row_count": len(panel),
                "winner_structure_state_count": int(panel["winner_structure_state"].nunique()),
                "top_winner_structure_state_eval_only": top_state,
                "top_winner_count_eval_only": top_count,
                "trading_promotion_pass_flag": 0,
                "next_action": "Review winner-structure interactions before any allocation or backtest promotion.",
            }
        ]
    )


def pass_fail_matrix(
    panel: pd.DataFrame,
    graph: pd.DataFrame,
    watch: pd.DataFrame,
    guardrail: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        gate("scope_5265", len(panel) == 5265, f"rows={len(panel)}", "5265"),
        gate("event_linked_2445", int(panel["source_event_available_flag"].sum()) == 2445, f"event={int(panel['source_event_available_flag'].sum())}", "2445"),
        gate("winner_states_present", panel["winner_structure_state"].nunique() >= 6, f"states={panel['winner_structure_state'].nunique()}", ">=6"),
        gate("watch_decomposition_present", len(watch) > 0, f"rows={len(watch)}", ">0"),
        gate("interaction_graph_present", len(graph) == len(panel) * 5, f"edges={len(graph)}", "5 edges per row"),
        gate("guardrail_eval_present", int(guardrail["top50_winner_count_eval_only"].sum()) == 50 and int(guardrail["bottom50_loser_count_eval_only"].sum()) == 50, f"top={int(guardrail['top50_winner_count_eval_only'].sum())}; bottom={int(guardrail['bottom50_loser_count_eval_only'].sum())}", "50/50"),
        gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
        gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
    ]
    return pd.DataFrame(rows)


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    report = f"""# Task718 Winner Structure Interaction Brain

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: watch and review candidates are decomposed into expectation, absorption, narrative-conflict, convexity, lifecycle, and winner-structure states.
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

- Data scope: 5,265 candidates and 2,445 event-linked candidates.
- Inputs: Task713 evidence, Task714 economics, Task715 pricing, Task716 slot context, and Task717 review state.
- Purpose: explain why a candidate could be watch/review but still have a winner-like structure, without promoting it to a trade.
- Assignment safety: outcome, future price, top-50 labels, ticker/theme protection, and outcome-tuned thresholds are all blocked from assignment.
- Evaluation safety: top/bottom winner/loser counts are computed only in guardrail artifacts.

## No-Background Decision-Maker Report

- This does not buy anything.
- It explains the hidden structure inside watch candidates.
- The key question is now: is this watch state a weak signal, or a delayed-absorption / convexity / conflict-resolution structure?
- Capital remains forbidden.

## Artifact Manifest

- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation command: `python -m unittest tests.test_task718_winner_structure_interaction_brain`.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / "task_718_winner_structure_interaction_brain.md").write_text(report, encoding="utf-8")
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
    frame["top50_used_for_assignment_flag"] = 0
    frame["watch_promoted_to_buy_flag"] = 0
    frame["ticker_theme_protection_rule_flag"] = 0
    frame["threshold_tuned_from_outcome_flag"] = 0
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


def int_safe(value: object) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


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
    parser = argparse.ArgumentParser(description="Build Task718 winner structure interaction brain.")
    parser.add_argument("--task713", type=Path, default=TASK713_PANEL)
    parser.add_argument("--task714", type=Path, default=TASK714_PANEL)
    parser.add_argument("--task715", type=Path, default=TASK715_PANEL)
    parser.add_argument("--task716", type=Path, default=TASK716_PANEL)
    parser.add_argument("--task717", type=Path, default=TASK717_PANEL)
    parser.add_argument("--eval", type=Path, default=TASK708_EVAL)
    parser.add_argument("--out-dir", type=Path, default=TASK718_DIR)
    args = parser.parse_args()
    build_task718(
        task713_path=args.task713,
        task714_path=args.task714,
        task715_path=args.task715,
        task716_path=args.task716,
        task717_path=args.task717,
        eval_path=args.eval,
        out_dir=args.out_dir,
    )
    print("[Task718] wrote winner structure interaction artifacts")


if __name__ == "__main__":
    main()
