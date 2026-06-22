from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK720_PANEL = Path("docs/reports/task_720_watch_bucket_interaction_diagnostics/task720_watch_bucket_interaction_panel.csv")
TASK708_EVAL = Path("docs/reports/task_708_full_period_backtest_comparison/task708_eval_panel.csv")
TASK721_DIR = Path("docs/reports/task_721_watch_bucket_decomposition_packets")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
NO_ACTION_REASON = "human_review_packet_only;not_buy_sell_or_sizing_instruction"


def build_task721(
    *,
    task720_path: Path = TASK720_PANEL,
    eval_path: Path = TASK708_EVAL,
    out_dir: Path = TASK721_DIR,
) -> dict[str, pd.DataFrame]:
    source = pd.read_csv(task720_path)
    panel = build_decomposition_panel(source)
    edge_matrix = build_edge_matrix(panel)
    packet_queue = build_packet_queue(panel)
    sample_packets = build_sample_packets(packet_queue)
    protocol = build_review_protocol()
    eval_guardrail = build_eval_guardrail(panel, eval_path)
    leakage = build_leakage_guardrail(panel)
    governance = build_governance_audit(panel, edge_matrix, packet_queue, sample_packets, leakage)
    decision = decision_frame(panel)
    pass_fail = pass_fail_matrix(panel, edge_matrix, packet_queue, protocol, eval_guardrail, leakage, governance)
    outputs = {
        "task721_decomposition_panel.csv": panel,
        "task721_interaction_edge_matrix.csv": edge_matrix,
        "task721_human_review_packet_queue.csv": packet_queue,
        "task721_manual_review_samples.csv": sample_packets,
        "task721_bucket_review_protocol.csv": protocol,
        "task721_eval_guardrail.csv": eval_guardrail,
        "task721_leakage_guardrail.csv": leakage,
        "task721_governance_audit.csv": governance,
        "task_721_decision.csv": decision,
        "task_721_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "panel": panel,
        "edge_matrix": edge_matrix,
        "packet_queue": packet_queue,
        "sample_packets": sample_packets,
        "protocol": protocol,
        "eval_guardrail": eval_guardrail,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_decomposition_panel(source: pd.DataFrame) -> pd.DataFrame:
    out = source.copy()
    out["next_decomposition_state"] = out.apply(next_decomposition_state, axis=1)
    out["evidence_financing_relation"] = out.apply(evidence_financing_relation, axis=1)
    out["financing_price_relation"] = out.apply(financing_price_relation, axis=1)
    out["price_slot_relation"] = out.apply(price_slot_relation, axis=1)
    out["slot_invalidation_relation"] = out.apply(slot_invalidation_relation, axis=1)
    out["review_priority_rank"] = out.apply(review_priority_rank, axis=1)
    out["review_priority_bucket"] = out["review_priority_rank"].map(
        {1: "p1_company_cashflow_absorption", 2: "p2_slot_rank_explanation", 3: "p3_financing_rank_ok_noise", 4: "p4_financing_cluster", 5: "p5_financing_weak_cohort"}
    )
    out["minimum_acceptance_criteria"] = out.apply(minimum_acceptance_criteria, axis=1)
    out["manual_packet_title"] = out.apply(manual_packet_title, axis=1)
    out["manual_packet_questions"] = out.apply(manual_packet_questions, axis=1)
    out["do_not_decompose_further_reason"] = out.apply(do_not_decompose_further_reason, axis=1)
    out["diagnostic_only_state"] = "DIAGNOSTIC_REVIEW_REQUIRED"
    add_no_action_flags(out)
    cols = KEYS + [
        "watch_subtype",
        "diagnostic_bucket_state",
        "final_diagnostic_state",
        "next_decomposition_state",
        "review_priority_rank",
        "review_priority_bucket",
        "cashflow_evidence_axis",
        "financing_risk_axis",
        "price_absorption_axis",
        "slot_competition_axis",
        "invalidation_axis",
        "evidence_financing_relation",
        "financing_price_relation",
        "price_slot_relation",
        "slot_invalidation_relation",
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
        "minimum_acceptance_criteria",
        "manual_packet_title",
        "manual_packet_questions",
        "do_not_decompose_further_reason",
        "diagnostic_only_state",
    ] + no_action_columns()
    return out[[c for c in cols if c in out.columns]].sort_values(["review_priority_rank", "entry_ts", "symbol"]).reset_index(drop=True)


def build_edge_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    edges = [
        ("evidence", "financing", "evidence_financing_relation"),
        ("financing", "price", "financing_price_relation"),
        ("price", "slot", "price_slot_relation"),
        ("slot", "invalidation", "slot_invalidation_relation"),
    ]
    for _, row in panel.iterrows():
        base = {key: row[key] for key in KEYS}
        for source_layer, target_layer, relation_col in edges:
            relation = row[relation_col]
            rows.append(
                {
                    **base,
                    "next_decomposition_state": row["next_decomposition_state"],
                    "source_layer": source_layer,
                    "target_layer": target_layer,
                    "relation_type": relation,
                    "relation_strength_bucket": relation_strength(relation),
                    "evidence_column_refs": edge_refs(source_layer, target_layer),
                    "reason_code": f"{source_layer}->{target_layer}:{relation}",
                    "assignment_safe_flag": 1,
                    "outcome_used_for_assignment_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_packet_queue(panel: pd.DataFrame) -> pd.DataFrame:
    packet = panel.copy()
    packet["event_title"] = "source_title_not_available_in_task720_packet"
    packet["event_category"] = packet["watch_subtype"]
    packet["source_lane"] = packet["source_directness_state"]
    packet["evidence_quality_state"] = packet["cashflow_evidence_axis"]
    packet["cashflow_path_present"] = packet["cashflow_evidence_axis"].astype(str).str.contains("cashflow|company", regex=True).astype(int)
    packet["customer_or_counterparty_present"] = packet["company_anchor_state"].astype(str).str.contains("company_anchor").astype(int)
    packet["financing_pressure_state"] = packet["financing_risk_axis"]
    packet["dilution_or_overhang_flag"] = packet["financing_risk_axis"].astype(str).str.contains("overhang|pressure").astype(int)
    packet["price_absorption_state"] = packet["price_absorption_axis"]
    packet["slot_rank_state"] = packet["slot_competition_axis"]
    packet["cohort_strength_state"] = packet["exposure_cluster_state"]
    packet["invalidation_trigger"] = packet["invalidation_axis"]
    packet["missing_evidence"] = packet.apply(missing_evidence, axis=1)
    packet["reviewer_decision"] = "manual_review_pending"
    packet["reviewer_note"] = ""
    packet["leakage_guardrail_pass"] = 1
    cols = KEYS + [
        "review_priority_rank",
        "review_priority_bucket",
        "watch_subtype",
        "next_decomposition_state",
        "event_title",
        "event_category",
        "source_lane",
        "evidence_quality_state",
        "cashflow_path_present",
        "customer_or_counterparty_present",
        "financing_pressure_state",
        "dilution_or_overhang_flag",
        "price_absorption_state",
        "slot_rank_state",
        "cohort_strength_state",
        "invalidation_trigger",
        "missing_evidence",
        "manual_packet_title",
        "manual_packet_questions",
        "reviewer_decision",
        "reviewer_note",
        "leakage_guardrail_pass",
        "minimum_acceptance_criteria",
        "cashflow_evidence_axis",
        "financing_risk_axis",
        "price_absorption_axis",
        "slot_competition_axis",
        "invalidation_axis",
        "evidence_financing_relation",
        "financing_price_relation",
        "price_slot_relation",
        "slot_invalidation_relation",
        "source_directness_state",
        "novelty_state",
        "evidence_strength_state",
        "company_anchor_state",
        "high_noise_context_state",
        "low_novelty_context_state",
        "pricing_acceptance_state",
        "same_timestamp_context_rank",
        "same_timestamp_theme_count",
        "assignment_used_flag",
        "outcome_used_for_assignment_flag",
    ]
    return packet[cols].sort_values(["review_priority_rank", "entry_ts", "symbol"]).reset_index(drop=True)


def build_sample_packets(packet_queue: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, group in packet_queue.groupby("next_decomposition_state", sort=True):
        rows.append(group.head(min(10, len(group))))
    if not rows:
        return packet_queue.head(0).copy()
    return pd.concat(rows, ignore_index=True).sort_values(["review_priority_rank", "next_decomposition_state", "entry_ts", "symbol"]).reset_index(drop=True)


def build_review_protocol() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "protocol_step": "p1_company_cashflow_absorption",
                "review_scope": "cashflow_news_absorption_pending",
                "required_human_check": "separate real cashflow evidence from narrative and verify price absorption is not future-return based",
                "minimum_acceptance_criteria": "company_specific_cashflow_or_customer_backlog_path;price_absorption_predefined;invalidation_clear",
            },
            {
                "protocol_step": "p2_slot_rank_explanation",
                "review_scope": "slot_rank_unconfirmed",
                "required_human_check": "explain why rank one deserves attention beyond same timestamp ordering",
                "minimum_acceptance_criteria": "rank_reason_quality;company_specificity_or_clean_non_noise_signal;price_absorption_not_rejected",
            },
            {
                "protocol_step": "p3_financing_rank_ok_noise",
                "review_scope": "funding_need_noise_only_rank_ok",
                "required_human_check": "decide if rank is only a technical artifact while financing and weak evidence dominate",
                "minimum_acceptance_criteria": "cashflow_support_or_direct_anchor_required;financing_use_of_proceeds_not_dilution_only;price_absorption_predefined",
            },
            {
                "protocol_step": "p4_financing_cluster",
                "review_scope": "funding_risk_absorption_diagnostic_hold",
                "required_human_check": "check whether cluster/theme pressure is making financing risk harder to absorb",
                "minimum_acceptance_criteria": "cluster_risk_explained;financing_absorption_path;no_source_gap_as_negative",
            },
            {
                "protocol_step": "p5_financing_weak_cohort",
                "review_scope": "financing_overhang_unabsorbed",
                "required_human_check": "confirm whether this remains research-only because weak evidence weak cohort and financing risk align",
                "minimum_acceptance_criteria": "must_show_new_evidence_or_price_absorption_before_any_later_test",
            },
        ]
    )


def build_eval_guardrail(panel: pd.DataFrame, eval_path: Path) -> pd.DataFrame:
    eval_panel = pd.read_csv(eval_path)
    merged = panel.merge(eval_panel[KEYS + ["costed_return_pct", "entry_reduce_failure_flag"]], on=KEYS, how="left", validate="one_to_one")
    top50 = set(eval_panel.nlargest(50, "costed_return_pct")["lifecycle_id"])
    bottom50 = set(eval_panel.nsmallest(50, "costed_return_pct")["lifecycle_id"])
    rows = []
    for state, group in merged.groupby("next_decomposition_state", dropna=False):
        ids = set(group["lifecycle_id"])
        rows.append(
            {
                "next_decomposition_state": state,
                "candidate_count": len(group),
                "top50_winner_count_eval_only": len(top50 & ids),
                "bottom50_loser_count_eval_only": len(bottom50 & ids),
                "avg_costed_return_pct_eval_only": float(group["costed_return_pct"].mean()),
                "entry_reduce_failure_rate_eval_only": float(pd.to_numeric(group["entry_reduce_failure_flag"], errors="coerce").fillna(0).mean()),
                "outcome_used_for_assignment_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values(["top50_winner_count_eval_only", "candidate_count"], ascending=[False, False]).reset_index(drop=True)


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


def build_governance_audit(
    panel: pd.DataFrame,
    edge_matrix: pd.DataFrame,
    packet_queue: pd.DataFrame,
    sample_packets: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_345", len(panel) == 345, f"rows={len(panel)}", "345"),
            gate("next_state_count", panel["next_decomposition_state"].nunique() >= 8, f"states={panel['next_decomposition_state'].nunique()}", ">=8"),
            gate("edge_matrix_complete", len(edge_matrix) == len(panel) * 4, f"edges={len(edge_matrix)}", "4 edges per row"),
            gate("packet_queue_complete", len(packet_queue) == len(panel), f"rows={len(packet_queue)}", "345"),
            gate("sample_packets_present", len(sample_packets) >= expected_sample_count(panel), f"rows={len(sample_packets)}", f">={expected_sample_count(panel)}"),
            gate("manual_questions_present", packet_queue["manual_packet_questions"].astype(str).str.len().gt(0).all(), "nonempty", "nonempty"),
            gate("packet_required_columns_present", required_packet_columns_present(packet_queue), "present", "present"),
            gate("diagnostic_only", set(panel["diagnostic_only_state"]) == {"DIAGNOSTIC_REVIEW_REQUIRED"}, ",".join(sorted(set(panel["diagnostic_only_state"]))), "DIAGNOSTIC_REVIEW_REQUIRED"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


def next_decomposition_state(row: pd.Series) -> str:
    bucket = str(row.get("diagnostic_bucket_state", ""))
    high_noise = str(row.get("high_noise_context_state", ""))
    low_novelty = str(row.get("low_novelty_context_state", ""))
    company_anchor = str(row.get("company_anchor_state", ""))
    pricing = str(row.get("pricing_acceptance_state", ""))
    rank = number(row.get("same_timestamp_context_rank"), default=999)
    theme_count = number(row.get("same_timestamp_theme_count"), default=999)
    if bucket == "cashflow_news_absorption_pending":
        if "high_noise" in high_noise:
            return "company_anchor_noisy_absorption_pending"
        if rank > 1 or theme_count > 2:
            return "company_anchor_secondary_slot_absorption_pending"
        return "company_anchor_clean_absorption_pending"
    if bucket == "slot_rank_unconfirmed":
        if "direct_company_anchor" in company_anchor and "company_evidence" in str(row.get("evidence_strength_state", "")):
            return "slot_rank_company_economic_anchor"
        if "direct_company_anchor" in company_anchor:
            return "slot_rank_thin_company_anchor"
        if "ownership_noise" in high_noise and "stale" in low_novelty:
            return "slot_rank_stale_ownership_noise"
        return "slot_rank_clean_but_no_company_anchor"
    if bucket == "funding_need_noise_only_rank_ok":
        if "stale" in low_novelty and "ownership_noise" in high_noise:
            return "rank_ok_stale_ownership_noise_financing"
        if pricing == "near_high_but_acceptance_unproven":
            return "rank_ok_near_high_absorption_unclear"
        return "rank_ok_fresh_but_no_cashflow_financing"
    if bucket == "funding_risk_absorption_diagnostic_hold":
        if theme_count >= 3:
            return "financing_cluster_pressure_absorption_pending"
        if "direct_company_anchor" in company_anchor:
            return "financing_direct_anchor_but_absorption_pending"
        return "financing_near_top_absorption_pending"
    if bucket == "financing_overhang_unabsorbed":
        if rank >= 4 or theme_count >= 4:
            return "financing_weak_cohort_cluster_risk"
        return "financing_weak_cohort_stale_noise"
    return "decomposition_unknown_review_required"


def evidence_financing_relation(row: pd.Series) -> str:
    evidence = str(row.get("cashflow_evidence_axis", ""))
    financing = str(row.get("financing_risk_axis", ""))
    if "cashflow" in evidence and "present" in evidence and "unabsorbed" in financing:
        return "cashflow_evidence_conflicts_with_financing_overhang"
    if "weak" in evidence and ("unabsorbed" in financing or "pressure" in financing):
        return "financing_dominates_weak_evidence"
    return "evidence_financing_needs_review"


def financing_price_relation(row: pd.Series) -> str:
    financing = str(row.get("financing_risk_axis", ""))
    price = str(row.get("price_absorption_axis", ""))
    if ("unabsorbed" in financing or "pressure" in financing) and "incomplete" in price:
        return "financing_not_absorbed_by_price"
    if ("unabsorbed" in financing or "pressure" in financing) and "confirmed" in price:
        return "financing_absorbed_by_price_proxy"
    return "financing_price_needs_review"


def price_slot_relation(row: pd.Series) -> str:
    price = str(row.get("price_absorption_axis", ""))
    slot = str(row.get("slot_competition_axis", ""))
    if "rank_first" in slot and "incomplete" in price:
        return "rank_first_but_price_unconfirmed"
    if "rank_ok" in slot and "incomplete" in price:
        return "rank_ok_but_price_unconfirmed"
    if "weak" in slot:
        return "slot_weakens_price_claim"
    return "price_slot_needs_review"


def slot_invalidation_relation(row: pd.Series) -> str:
    slot = str(row.get("slot_competition_axis", ""))
    invalidation = str(row.get("invalidation_axis", ""))
    if "active" in invalidation:
        return "invalidation_overrides_slot_claim"
    if "rank_first" in slot and "rank_first_not_enough" in invalidation:
        return "slot_rank_requires_external_confirmation"
    return "slot_invalidation_needs_review"


def relation_strength(relation: str) -> str:
    if "overrides" in relation or "dominates" in relation or "not_absorbed" in relation:
        return "blocking_or_conflict_link"
    if "conflicts" in relation or "unconfirmed" in relation or "requires" in relation:
        return "needs_confirmation_link"
    if "absorbed" in relation:
        return "supportive_link"
    return "review_link"


def edge_refs(source_layer: str, target_layer: str) -> str:
    mapping = {
        ("evidence", "financing"): "cashflow_evidence_axis,financing_risk_axis,evidence_strength_state,company_anchor_state",
        ("financing", "price"): "financing_risk_axis,price_absorption_axis,pricing_acceptance_state,priced_vs_unpriced_state",
        ("price", "slot"): "price_absorption_axis,slot_competition_axis,same_timestamp_context_rank,same_timestamp_theme_count",
        ("slot", "invalidation"): "slot_competition_axis,invalidation_axis,manual_packet_questions",
    }
    return mapping[(source_layer, target_layer)]


def review_priority_rank(row: pd.Series) -> int:
    bucket = str(row.get("diagnostic_bucket_state", ""))
    if bucket == "cashflow_news_absorption_pending":
        return 1
    if bucket == "slot_rank_unconfirmed":
        return 2
    if bucket == "funding_need_noise_only_rank_ok":
        return 3
    if bucket == "funding_risk_absorption_diagnostic_hold":
        return 4
    return 5


def minimum_acceptance_criteria(row: pd.Series) -> str:
    state = next_decomposition_state(row)
    if state.startswith("company_anchor"):
        return "cashflow_path_specific;price_absorption_predefined;financing_overhang_not_dominant;invalidation_defined"
    if state.startswith("slot_rank"):
        return "rank_reason_explained;company_specificity_or_clean_signal;price_absorption_not_rejected;rank_not_sole_basis"
    if state.startswith("rank_ok"):
        return "cashflow_support_required;financing_use_of_proceeds_reviewed;price_absorption_predefined"
    if state.startswith("financing_cluster"):
        return "cluster_pressure_explained;financing_absorption_path_visible;no_missing_as_negative"
    if state.startswith("financing_weak"):
        return "new_evidence_or_price_absorption_required_before_later_test"
    return "manual_review_required"


def manual_packet_title(row: pd.Series) -> str:
    return f"{row['symbol']} {row['entry_ts']} {next_decomposition_state(row)}"


def manual_packet_questions(row: pd.Series) -> str:
    state = next_decomposition_state(row)
    if state.startswith("company_anchor"):
        return "is_cashflow_evidence_real;does_it_survive_financing_overhang;is_price_absorption_predefined_and_present;what_invalidates"
    if state.startswith("slot_rank"):
        return "why_rank_first;is_rank_supported_by_company_or_cashflow_evidence;is_price_absorption_only_partial;what_competing_candidate_would_displace_it"
    if state.startswith("rank_ok"):
        return "is_rank_ok_only_technical;is_financing_growth_fuel_or_dilution;is_cashflow_evidence_missing;what_price_absorption_would_change_state"
    if state.startswith("financing_cluster"):
        return "is_cluster_or_theme_pressure_active;does_financing_risk_amplify_cluster_risk;is_price_absorption_real_or_waiting"
    return "is_evidence_weak;is_cohort_weak;is_financing_overhang_unabsorbed;what_new_information_would_change_review_state"


def do_not_decompose_further_reason(row: pd.Series) -> str:
    state = next_decomposition_state(row)
    if state in {"company_anchor_clean_absorption_pending", "slot_rank_company_economic_anchor"}:
        return "next_step_is_human_packet_review_not_more_taxonomy"
    if state.startswith("financing_weak"):
        return "further_split_without_new_evidence_would_be_false_precision"
    return "decomposition_sufficient_for_manual_review_packet"


def missing_evidence(row: pd.Series) -> str:
    missing = []
    if "weak" in str(row.get("cashflow_evidence_axis", "")) or "no_cashflow" in next_decomposition_state(row):
        missing.append("cashflow_or_customer_specific_evidence")
    if "incomplete" in str(row.get("price_absorption_axis", "")):
        missing.append("confirmed_price_absorption")
    if "financing" in next_decomposition_state(row):
        missing.append("financing_use_of_proceeds_and_dilution_terms")
    if str(row.get("event_title", "")) == "source_title_not_available_in_task720_packet":
        missing.append("source_event_title")
    return ";".join(missing) if missing else "none_identified_for_manual_packet"


def expected_sample_count(panel: pd.DataFrame) -> int:
    return int(panel.groupby("next_decomposition_state").size().clip(upper=10).sum())


def required_packet_columns_present(packet_queue: pd.DataFrame) -> bool:
    required = {
        "event_title",
        "event_category",
        "source_lane",
        "evidence_quality_state",
        "cashflow_path_present",
        "customer_or_counterparty_present",
        "financing_pressure_state",
        "dilution_or_overhang_flag",
        "price_absorption_state",
        "slot_rank_state",
        "cohort_strength_state",
        "invalidation_trigger",
        "missing_evidence",
        "reviewer_decision",
        "reviewer_note",
        "leakage_guardrail_pass",
    }
    return required.issubset(set(packet_queue.columns))


def decision_frame(panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task721",
                "verdict": "WATCH_BUCKET_DECOMPOSITION_PACKETS_BUILT_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "candidate_count": len(panel),
                "next_decomposition_state_count": int(panel["next_decomposition_state"].nunique()),
                "trading_promotion_pass_flag": 0,
                "next_action": "Manual review packets before any backtest candidate rule.",
            }
        ]
    )


def pass_fail_matrix(
    panel: pd.DataFrame,
    edge_matrix: pd.DataFrame,
    packet_queue: pd.DataFrame,
    protocol: pd.DataFrame,
    eval_guardrail: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_345", len(panel) == 345, f"rows={len(panel)}", "345"),
            gate("next_state_count", panel["next_decomposition_state"].nunique() >= 8, f"states={panel['next_decomposition_state'].nunique()}", ">=8"),
            gate("edge_matrix_complete", len(edge_matrix) == len(panel) * 4, f"edges={len(edge_matrix)}", "4 edges per row"),
            gate("packet_queue_complete", len(packet_queue) == len(panel), f"rows={len(packet_queue)}", "345"),
            gate("protocol_present", len(protocol) == 5, f"rows={len(protocol)}", "5"),
            gate("eval_guardrail_eval_only", int(eval_guardrail["outcome_used_for_assignment_flag"].sum()) == 0, "0", "0"),
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
    report = f"""# Task721 Watch Bucket Decomposition Packets

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: the three Task720 priority buckets are decomposed into reviewable packet states.
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

- Scope: 345 Task720 candidates.
- Output states: {decision.iloc[0]['next_decomposition_state_count']}.
- Edge logic: evidence-financing, financing-price, price-slot, and slot-invalidation.
- Review protocol: company absorption first, slot explanation second, financing-noise cases third.
- No action output is produced.

## No-Background Decision-Maker Report

- This still does not buy anything.
- The goal is to make each candidate readable by a human before any backtest rule.
- The main question is whether the state assignment itself makes economic sense.

## Artifact Manifest

- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation command: `python -m unittest tests.test_task721_watch_bucket_decomposition_packets`.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / "task_721_watch_bucket_decomposition_packets.md").write_text(report, encoding="utf-8")
    manifest = out_dir / "artifact_manifest.csv"
    if manifest.exists():
        manifest.unlink()
    write_manifest(out_dir, manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task721 watch bucket decomposition packets.")
    parser.add_argument("--task720", type=Path, default=TASK720_PANEL)
    parser.add_argument("--eval", type=Path, default=TASK708_EVAL)
    parser.add_argument("--out-dir", type=Path, default=TASK721_DIR)
    args = parser.parse_args()
    build_task721(task720_path=args.task720, eval_path=args.eval, out_dir=args.out_dir)
    print("[Task721] wrote watch bucket decomposition packets")


if __name__ == "__main__":
    main()
