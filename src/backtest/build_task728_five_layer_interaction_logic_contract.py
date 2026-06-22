from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task728"
KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
TASK713_PANEL = Path("docs/reports/task_713_evidence_provenance_brain/task713_evidence_provenance_panel.csv")
TASK714_PANEL = Path("docs/reports/task_714_economic_transmission_brain/task714_economic_transmission_panel.csv")
TASK715_PANEL = Path("docs/reports/task_715_market_pricing_acceptance_brain/task715_market_pricing_acceptance_panel.csv")
TASK716_PANEL = Path("docs/reports/task_716_portfolio_competition_brain/task716_slot_competition_panel.csv")
TASK717_PANEL = Path("docs/reports/task_717_decision_invalidation_risk_brain/task717_decision_invalidation_panel.csv")
OUT_DIR = Path("docs/reports/task_728_five_layer_interaction_logic_contract")

LAYER_STATE_COLUMNS = {
    "L1_Evidence": [
        "source_type_state",
        "source_directness_state",
        "novelty_state",
        "evidence_strength_state",
        "source_gap_state",
        "evidence_brain_state",
        "company_anchor_state",
        "financing_context_state",
        "high_noise_context_state",
        "low_novelty_context_state",
        "guidance_context_state",
        "market_acceptance_state",
        "theme_leadership_context",
        "policy_macro_context_state",
    ],
    "L2_Economic": [
        "revenue_path_state",
        "margin_path_state",
        "order_backlog_path_state",
        "funding_path_state",
        "dilution_overhang_state",
        "policy_demand_path_state",
        "valuation_pressure_state",
        "economic_transmission_state",
    ],
    "L3_Price": [
        "pricing_acceptance_state",
        "priced_vs_unpriced_state",
        "positioning_proxy_state",
        "acceptance_failure_state",
        "market_pricing_brain_state",
    ],
    "L4_Portfolio": [
        "slot_competition_state",
        "exposure_cluster_state",
        "portfolio_brain_state",
    ],
    "L5_Risk": [
        "review_decision_state",
        "invalidation_condition",
        "risk_budget_state",
        "sizing_cap_reason",
        "final_brain_state",
    ],
}

CORE_INTERACTION_COLUMNS = [
    "evidence_brain_state",
    "source_directness_state",
    "novelty_state",
    "evidence_strength_state",
    "economic_transmission_state",
    "funding_path_state",
    "dilution_overhang_state",
    "pricing_acceptance_state",
    "market_pricing_brain_state",
    "slot_competition_state",
    "exposure_cluster_state",
    "portfolio_brain_state",
    "review_decision_state",
    "invalidation_condition",
    "risk_budget_state",
]


def build_task728(
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

    layer_inventory = build_layer_state_inventory(frames)
    layer_contract = build_corrected_layer_contract()
    rule_families = build_rule_family_catalog()
    observed_cells = build_observed_interaction_cells(merged)
    rule_candidates = build_rule_candidates(observed_cells)
    coverage = build_rule_coverage_audit(rule_candidates, rule_families)
    dangerous_surfaces = build_dangerous_surface_audit()
    gpt_packet = build_gpt_review_packet(rule_families, observed_cells, rule_candidates)
    leakage = build_leakage_guardrail([layer_inventory, layer_contract, rule_families, observed_cells, rule_candidates, coverage, gpt_packet])
    governance = build_governance_audit(layer_inventory, layer_contract, rule_families, observed_cells, rule_candidates, coverage, leakage)
    decision = build_decision(rule_candidates, coverage)
    pass_fail = build_pass_fail(layer_inventory, layer_contract, rule_families, observed_cells, rule_candidates, coverage, leakage, governance)

    outputs = {
        "task728_layer_state_inventory.csv": layer_inventory,
        "task728_corrected_five_layer_contract.csv": layer_contract,
        "task728_interaction_rule_family_catalog.csv": rule_families,
        "task728_observed_five_layer_interaction_cells.csv": observed_cells,
        "task728_rule_candidate_assignments.csv": rule_candidates,
        "task728_rule_coverage_audit.csv": coverage,
        "task728_dangerous_surface_audit.csv": dangerous_surfaces,
        "task728_gpt_institutional_review_packet.csv": gpt_packet,
        "task728_leakage_guardrail.csv": leakage,
        "task728_governance_audit.csv": governance,
        "task_728_decision.csv": decision,
        "task_728_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "merged": merged,
        "layer_inventory": layer_inventory,
        "layer_contract": layer_contract,
        "rule_families": rule_families,
        "observed_cells": observed_cells,
        "rule_candidates": rule_candidates,
        "coverage": coverage,
        "dangerous_surfaces": dangerous_surfaces,
        "gpt_packet": gpt_packet,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def merge_layers(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    base_cols = KEYS + [c for c in LAYER_STATE_COLUMNS["L1_Evidence"] if c in frames["L1_Evidence"].columns]
    out = frames["L1_Evidence"][base_cols].copy()
    for layer in ["L2_Economic", "L3_Price", "L4_Portfolio", "L5_Risk"]:
        cols = KEYS + [c for c in LAYER_STATE_COLUMNS[layer] if c in frames[layer].columns and c not in out.columns]
        out = out.merge(frames[layer][cols], on=KEYS, how="left", validate="one_to_one")
    return out


def build_layer_state_inventory(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for layer, frame in frames.items():
        for column in LAYER_STATE_COLUMNS[layer]:
            if column not in frame.columns:
                continue
            counts = frame[column].fillna("missing").astype(str).value_counts()
            rows.append(
                {
                    "layer": layer,
                    "state_axis": column,
                    "unique_state_count": int(counts.size),
                    "top_states": "; ".join([f"{idx}={int(value)}" for idx, value in counts.head(10).items()]),
                    "provides_to_next_layer": layer_output_contract(layer, column),
                    "standalone_trade_signal_allowed_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_corrected_layer_contract() -> pd.DataFrame:
    rows = [
        (
            "L1_Evidence",
            "source credibility and novelty filter",
            "source credibility, directness, novelty, contamination, timestamp validity, source gap",
            "must not claim economics; only permits or caps L2 interpretation",
            "L2_Economic",
        ),
        (
            "L2_Economic",
            "business transmission thesis",
            "revenue path, margin path, backlog conversion, funding, dilution, policy demand, valuation pressure",
            "must be capped by L1 and must declare missing denominator or contradiction",
            "L3_Price and L5_Risk",
        ),
        (
            "L3_Price",
            "market processing and acceptance",
            "acceptance, incomplete pricing, already extended, overhang absorption, positioning support",
            "confirms or challenges L2 thesis; never replaces L2 evidence",
            "L4_Portfolio and L5_Risk",
        ),
        (
            "L4_Portfolio",
            "same timestamp capital competition",
            "slot leader/contender, cohort rank, theme cluster, exposure pressure",
            "compares only candidates in the same timestamp cohort; no global rank",
            "L5_Risk",
        ),
        (
            "L5_Risk",
            "invalidation and budget gate",
            "review state, invalidation condition, risk budget, sizing cap reason",
            "final actionability is review-only until raw evidence and interaction gates pass",
            "downstream backtest gate",
        ),
    ]
    return pd.DataFrame(
        [
            {
                "layer": layer,
                "role": role,
                "must_output": output,
                "hard_constraint": constraint,
                "consumer_layer": consumer,
                "standalone_trade_signal_allowed_flag": 0,
            }
            for layer, role, output, constraint, consumer in rows
        ]
    )


def build_rule_family_catalog() -> pd.DataFrame:
    rows = [
        ("L1_L2_GATE_001", "L1->L2", "prerequisite", "source_gap or no_source_evidence blocks all positive economic transmission claims", "economic_claim_source_blocked"),
        ("L1_L2_GATE_002", "L1->L2", "confidence_cap", "thin or weak evidence caps revenue/margin/backlog states even when L2 has a positive path", "economic_claim_capped_by_evidence"),
        ("L1_L2_GATE_003", "L1->L2", "blocker", "ownership/Form4/13D/13G/13F or governance noise cannot support L2 economic claim", "source_family_blocks_economic_claim"),
        ("L1_L2_CONTRA_004", "L1xL2", "offsetting", "reaffirmation or stale evidence conflicts with revenue acceleration language", "stale_or_reaffirmed_economic_claim"),
        ("L1_L2_CONTRA_005", "L1xL2", "confidence_cap", "indirect evidence plus strong economic state requires source packet review", "indirect_strong_economic_review"),
        ("L1_L2_FIN_006", "L1xL2", "escalation", "financing context plus growth path requires use-of-proceeds and dilution interpretation", "financing_growth_bridge_needed"),
        ("L1_L2_FIN_007", "L1xL2", "blocker", "funding need with unabsorbed dilution offsets revenue or backlog path", "dilution_offsets_growth_claim"),
        ("L2_L3_PRICE_008", "L2xL3", "reinforcing", "economic path plus accepted price/tape proxy forms coherent thesis candidate", "economic_price_reinforcing"),
        ("L2_L3_PRICE_009", "L2xL3", "prerequisite", "positive economic path with incomplete acceptance requires confirmation", "positive_thesis_needs_price_acceptance"),
        ("L2_L3_PRICE_010", "L2xL3", "offsetting", "accepted price without clear economic path is momentum without thesis", "price_without_economic_thesis"),
        ("L2_L3_PRICE_011", "L2xL3", "confidence_cap", "near-high unconfirmed or extension pressure caps otherwise positive thesis", "extension_caps_thesis"),
        ("L2_L5_INV_012", "L2xL5", "invalidation", "economic claim must map to thesis-specific invalidation, not generic review text", "thesis_specific_invalidation_required"),
        ("L2_L5_INV_013", "L2xL5", "blocker", "overhang thesis invalid if follow-up price does not absorb financing", "overhang_absorption_required"),
        ("L3_L4_SLOT_014", "L3xL4", "reinforcing", "price accepted plus same-timestamp slot leader supports review priority", "accepted_slot_leader"),
        ("L3_L4_SLOT_015", "L3xL4", "confidence_cap", "price incomplete plus contender status requires cohort superiority proof", "contender_needs_absorption_and_superiority"),
        ("L3_L4_SLOT_016", "L3xL4", "offsetting", "accepted but clustered or extension risk limits slot claim", "accepted_but_cluster_or_extension_capped"),
        ("L4_L5_RISK_017", "L4xL5", "sizing_modifier", "theme cluster medium/high caps risk budget even for slot leaders", "cluster_capped_budget"),
        ("L4_L5_RISK_018", "L4xL5", "blocker", "no slot claim or no competition proof stays research-only", "no_slot_no_budget"),
        ("L1_L2_L3_019", "L1xL2xL3", "escalation", "direct company evidence + positive economics + incomplete price means watch for confirmation", "direct_positive_wait_for_price"),
        ("L1_L2_L3_020", "L1xL2xL3", "reinforcing", "direct strong evidence + positive economics + accepted price forms high-quality review candidate", "evidence_economic_price_stack"),
        ("L1_L2_L3_021", "L1xL2xL3", "blocker", "weak/noise evidence + positive economics + accepted price cannot be promoted without source repair", "price_cannot_rescue_weak_source"),
        ("L2_L3_L4_022", "L2xL3xL4", "reinforcing", "positive economics + accepted price + slot leader supports cohort leader review", "cohort_leader_thesis_stack"),
        ("L2_L3_L4_023", "L2xL3xL4", "confidence_cap", "positive economics + incomplete price + contender needs delayed confirmation", "cohort_contender_delayed_confirmation"),
        ("L2_L3_L4_024", "L2xL3xL4", "sizing_modifier", "positive economics + accepted price + cluster high limits size", "accepted_cluster_size_cap"),
        ("ALL_025", "L1xL2xL3xL4xL5", "prerequisite", "all positive layers still require raw source, denominator, and leakage gates", "full_stack_gate_required"),
        ("ALL_026", "L1xL2xL3xL4xL5", "blocker", "any source gap or generic research-only risk state blocks backtest eligibility", "full_stack_source_or_risk_block"),
        ("ALL_027", "L1xL2xL3xL4xL5", "invalidation", "final brain must cite which earlier layer would falsify the thesis", "full_stack_invalidation_trace"),
        ("ALL_028", "L1xL2xL3xL4xL5", "sizing_modifier", "cluster, overhang, extension, and low evidence strength jointly cap risk budget", "full_stack_size_cap_trace"),
    ]
    return pd.DataFrame(
        [
            {
                "rule_family_id": rule_id,
                "layer_scope": scope,
                "relation_type": relation,
                "precondition_template": precondition,
                "output_state_template": output,
                "implementation_mode": "typed_state_axes_not_one_off_if_chain",
                "assignment_allowed_flag": 0,
                "backtest_allowed_flag": 0,
            }
            for rule_id, scope, relation, precondition, output in rows
        ]
    )


def build_observed_interaction_cells(merged: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in CORE_INTERACTION_COLUMNS if c in merged.columns]
    cells = merged.groupby(cols, dropna=False).size().reset_index(name="candidate_count")
    return cells.sort_values(["candidate_count"] + cols, ascending=[False] + [True] * len(cols)).reset_index(drop=True)


def build_rule_candidates(observed_cells: pd.DataFrame) -> pd.DataFrame:
    out = observed_cells.copy()
    classified = out.apply(classify_interaction_cell, axis=1, result_type="expand")
    for col in classified.columns:
        out[col] = classified[col]
    out["assignment_allowed_flag"] = 0
    out["backtest_allowed_flag"] = 0
    return out.sort_values(["candidate_count", "rule_family_id"], ascending=[False, True]).reset_index(drop=True)


def classify_interaction_cell(row: pd.Series) -> dict[str, str]:
    evidence = str(row.get("evidence_brain_state", ""))
    directness = str(row.get("source_directness_state", ""))
    novelty = str(row.get("novelty_state", ""))
    strength = str(row.get("evidence_strength_state", ""))
    economic = str(row.get("economic_transmission_state", ""))
    funding = str(row.get("funding_path_state", ""))
    dilution = str(row.get("dilution_overhang_state", ""))
    price = str(row.get("market_pricing_brain_state", ""))
    pricing_acceptance = str(row.get("pricing_acceptance_state", ""))
    slot = str(row.get("slot_competition_state", ""))
    cluster = str(row.get("exposure_cluster_state", ""))
    portfolio = str(row.get("portfolio_brain_state", ""))
    review = str(row.get("review_decision_state", ""))
    invalidation = str(row.get("invalidation_condition", ""))
    risk_budget = str(row.get("risk_budget_state", ""))

    if "source_gap" in evidence or "no_source" in strength or "source_gap" in review:
        return rule("ALL_026", "blocker", "full_stack_source_or_risk_block", "source gap blocks economic/price/slot promotion")
    if "noise" in evidence or "weak" in strength:
        return rule("L1_L2_GATE_002", "confidence_cap", "economic_claim_capped_by_evidence", "weak/noise source caps downstream interpretation")
    if "reaffirm" in novelty and positive_economic(economic):
        return rule("L1_L2_CONTRA_004", "offsetting", "stale_or_reaffirmed_economic_claim", "reaffirmation/stale evidence offsets positive economic label")
    if "funding_need" in funding or "dilution_overhang_unabsorbed" in dilution:
        if "waiting_on_overhang" in price or "watch_for_confirmation" in review:
            return rule("L2_L5_INV_013", "invalidation", "overhang_absorption_required", "financing overhang needs follow-up absorption")
        return rule("L1_L2_FIN_007", "blocker", "dilution_offsets_growth_claim", "unabsorbed dilution offsets growth claim")
    if "indirect" in directness and positive_economic(economic):
        return rule("L1_L2_CONTRA_005", "confidence_cap", "indirect_strong_economic_review", "indirect evidence cannot fully support strong economic state")
    if positive_economic(economic) and "market_accepts" in price:
        if "slot_leader" in slot and cluster == "theme_cluster_low":
            return rule("L2_L3_L4_022", "reinforcing", "cohort_leader_thesis_stack", "economic, price, and slot layers reinforce")
        if "cluster_high" in cluster or "clustered" in portfolio or "cluster" in risk_budget:
            return rule("L2_L3_L4_024", "sizing_modifier", "accepted_cluster_size_cap", "accepted thesis is capped by cluster exposure")
        return rule("L2_L3_PRICE_008", "reinforcing", "economic_price_reinforcing", "economic path and price acceptance align")
    if positive_economic(economic) and ("incomplete" in price or "building" in pricing_acceptance):
        if "contender" in slot:
            return rule("L2_L3_L4_023", "confidence_cap", "cohort_contender_delayed_confirmation", "contender needs price absorption and superiority proof")
        return rule("L2_L3_PRICE_009", "prerequisite", "positive_thesis_needs_price_acceptance", "positive economic thesis awaits price acceptance")
    if not positive_economic(economic) and "market_accepts" in price:
        return rule("L2_L3_PRICE_010", "offsetting", "price_without_economic_thesis", "price acceptance lacks economic thesis support")
    if "cluster_high" in cluster or "cluster_capped" in risk_budget:
        return rule("L4_L5_RISK_017", "sizing_modifier", "cluster_capped_budget", "cluster exposure caps budget")
    if "no_slot" in slot or "no_slot" in portfolio:
        return rule("L4_L5_RISK_018", "blocker", "no_slot_no_budget", "no slot claim keeps candidate research-only")
    if "invalid_if" in invalidation:
        return rule("L2_L5_INV_012", "invalidation", "thesis_specific_invalidation_required", "risk layer requires earlier layer invalidation trace")
    return rule("ALL_025", "prerequisite", "full_stack_gate_required", "unclassified combination requires full stack source/denominator/leakage gate")


def positive_economic(state: str) -> bool:
    positive_tokens = ["reinforcing", "tailwind", "growth_funding", "backlog_or_order_path_visible"]
    negative_tokens = ["source_gap", "no_clear", "needs_review"]
    return any(token in state for token in positive_tokens) and not any(token in state for token in negative_tokens)


def rule(rule_family_id: str, relation_type: str, output_state: str, reason: str) -> dict[str, str]:
    return {
        "rule_family_id": rule_family_id,
        "relation_type": relation_type,
        "interaction_output_state": output_state,
        "interaction_reason": reason,
    }


def build_rule_coverage_audit(rule_candidates: pd.DataFrame, rule_families: pd.DataFrame) -> pd.DataFrame:
    candidate_counts = rule_candidates["rule_family_id"].value_counts()
    rows = []
    for _, family in rule_families.iterrows():
        rule_id = family["rule_family_id"]
        rows.append(
            {
                "rule_family_id": rule_id,
                "layer_scope": family["layer_scope"],
                "relation_type": family["relation_type"],
                "observed_cell_count": int(candidate_counts.get(rule_id, 0)),
                "candidate_count": int(rule_candidates.loc[rule_candidates["rule_family_id"] == rule_id, "candidate_count"].sum()),
                "coverage_status": "OBSERVED_IN_CURRENT_PANEL" if int(candidate_counts.get(rule_id, 0)) else "DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS",
            }
        )
    return pd.DataFrame(rows)


def build_dangerous_surface_audit() -> pd.DataFrame:
    rows = [
        ("Task713 evidence_strength_state", "can sound certified even when source parser later rejects evidence", "keep as diagnostic only; require EvidenceObject certification"),
        ("Task714 revenue_margin_reinforcing", "strong label from count co-occurrence", "downgrade to candidate economic state until L1 and denominator gates pass"),
        ("Task714 policy_demand_tailwind_with_company_link", "policy/company link may be broad narrative not company economics", "require policy-to-company edge and sector/theme confirmation"),
        ("Task714 capital_need_overhang_vs_growth_question", "good label but no use-of-proceeds/dilution/cost bridge", "replace with financing interaction edge"),
        ("Task715 market_accepts_economic_path", "price can confirm crowding or momentum without source-backed thesis", "must reference L2 thesis id"),
        ("Task716 same_timestamp_slot_leader", "slot leadership can become global rank if misused", "same timestamp cohort only"),
        ("Task717 final_brain_state", "final-looking name may be mistaken for action approval", "rename/guard as review_state only until hard gates pass"),
    ]
    return pd.DataFrame(
        [
            {
                "surface": surface,
                "risk": risk,
                "required_fix": fix,
                "assignment_allowed_flag": 0,
            }
            for surface, risk, fix in rows
        ]
    )


def build_gpt_review_packet(
    rule_families: pd.DataFrame,
    observed_cells: pd.DataFrame,
    rule_candidates: pd.DataFrame,
) -> pd.DataFrame:
    roles = [
        (
            "Goldman Sachs event-driven trader",
            "L1 evidence must gate L2 catalyst materiality before price/slot logic.",
            "Evidence and Economic states currently exist separately; L2 must not create a strong economic claim unless L1 permits it.",
        ),
        (
            "Morgan Stanley expectations strategist",
            "L2 economics must include expectation and novelty contradiction before L3 acceptance.",
            "The missing middle is expectations: fact minus prior expectation, reaffirmation versus raise, and novelty must alter L2-to-L3 interpretation.",
        ),
        (
            "JPMorgan credit/financing trader",
            "financing must be relation edges, not risk flag only.",
            "Funding can be positive for capacity-backed growth or negative for survival/dilution; it must interact with revenue/backlog thesis.",
        ),
        (
            "Citadel equity L/S pod PM",
            "L2-L3-L4 stack should decide thesis quality versus cohort opportunity cost.",
            "Even high-quality economics can lose the slot if price has already fully absorbed it or another same-timestamp candidate has a cleaner stack.",
        ),
        (
            "Millennium portfolio risk trader",
            "L4-L5 should turn cluster, overhang, extension, and invalidation into budget caps.",
            "Risk is not just blocking bad names; it converts uncertainty from all prior layers into confidence caps, escalation, and sizing modifiers.",
        ),
    ]
    return pd.DataFrame(
        [
            {
                "reviewer_role": role,
                "review_focus": focus,
                "captured_gpt_critique": critique,
                "supplied_context": f"5 layers, {len(rule_families)} rule families, {len(observed_cells)} observed interaction cells, {len(rule_candidates)} candidate rule assignments",
                "gpt_response_status": "CAPTURED_IN_CHROME",
                "gpt_overall_verdict": "FAIL_LAYER_STACK_NOT_LAYER_INTERACTION_NETWORK",
                "gpt_is_source_of_truth_flag": 0,
                "assignment_allowed_flag": 0,
            }
            for role, focus, critique in roles
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
    layer_inventory: pd.DataFrame,
    layer_contract: pd.DataFrame,
    rule_families: pd.DataFrame,
    observed_cells: pd.DataFrame,
    rule_candidates: pd.DataFrame,
    coverage: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    checks = [
        ("layer_inventory_present", len(layer_inventory) >= 25, f"rows={len(layer_inventory)}", ">=25"),
        ("five_layer_contract_present", len(layer_contract) == 5, f"rows={len(layer_contract)}", "5"),
        ("rule_families_present", len(rule_families) >= 25, f"rows={len(rule_families)}", ">=25"),
        ("observed_cells_present", len(observed_cells) >= 100, f"rows={len(observed_cells)}", ">=100"),
        ("rule_candidates_present", len(rule_candidates) == len(observed_cells), f"rows={len(rule_candidates)}", "same as observed cells"),
        ("relation_types_multiple", rule_candidates["relation_type"].nunique() >= 5, f"unique={rule_candidates['relation_type'].nunique()}", ">=5"),
        ("coverage_multiple_families_observed", int((coverage["observed_cell_count"] > 0).sum()) >= 10, f"observed_families={int((coverage['observed_cell_count'] > 0).sum())}", ">=10"),
        ("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
    ]
    return pd.DataFrame([gate(name, passed, observed, required) for name, passed, observed, required in checks])


def build_decision(rule_candidates: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "FIVE_LAYER_INTERACTION_LOGIC_CONTRACT_DEFINED_NOT_BACKTEST_READY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "observed_interaction_cell_count": len(rule_candidates),
                "observed_rule_family_count": int((coverage["observed_cell_count"] > 0).sum()),
                "backtest_permission": "FAIL",
                "next_action": "Capture GPT review and implement source-certified primitive facts before promoting any five-layer interaction rule to backtest candidate selection.",
            }
        ]
    )


def build_pass_fail(
    layer_inventory: pd.DataFrame,
    layer_contract: pd.DataFrame,
    rule_families: pd.DataFrame,
    observed_cells: pd.DataFrame,
    rule_candidates: pd.DataFrame,
    coverage: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("layer_inventory_completed", len(layer_inventory) >= 25, f"rows={len(layer_inventory)}", ">=25"),
            gate("corrected_five_layer_contract_completed", len(layer_contract) == 5, f"rows={len(layer_contract)}", "5"),
            gate("interaction_rule_family_catalog_completed", len(rule_families) >= 25, f"rows={len(rule_families)}", ">=25"),
            gate("observed_interaction_cells_generated", len(observed_cells) >= 100, f"rows={len(observed_cells)}", ">=100"),
            gate("rule_candidate_assignments_generated", len(rule_candidates) == len(observed_cells), f"rows={len(rule_candidates)}", "same as observed cells"),
            gate("relation_type_diversity", rule_candidates["relation_type"].nunique() >= 5, f"unique={rule_candidates['relation_type'].nunique()}", ">=5"),
            gate("coverage_multiple_families_observed", int((coverage["observed_cell_count"] > 0).sum()) >= 10, f"observed={int((coverage['observed_cell_count'] > 0).sum())}", ">=10"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "PASS only after source-certified primitive fact and denominator gates"),
        ]
    )


def layer_output_contract(layer: str, column: str) -> str:
    if layer == "L1_Evidence":
        return "credibility_or_confidence_cap_for_L2"
    if layer == "L2_Economic":
        return "thesis_mechanism_or_contradiction_for_L3_L5"
    if layer == "L3_Price":
        return "market_acceptance_or_price_rejection_for_L4_L5"
    if layer == "L4_Portfolio":
        return "cohort_slot_and_cluster_pressure_for_L5"
    return "invalidation_and_budget_gate_for_downstream"


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    (out_dir / "task_728_five_layer_interaction_logic_contract.md").write_text(
        render_report(outputs, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task728 Five Layer Interaction Logic Contract",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        f"- Observed interaction cells: {int(d['observed_interaction_cell_count'])}",
        f"- Observed rule families: {int(d['observed_rule_family_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task728 corrects the Task727 weakness: it does not reduce the brain to a few keyword fields. It inventories the actual Task713-717 five-layer state axes, defines each layer's contract, creates typed interaction rule families, and assigns every observed five-layer state cell to an interaction rule candidate without using outcomes.",
        "",
        "### Corrected Five Layer Contract",
        "",
        frame_to_markdown(outputs["task728_corrected_five_layer_contract.csv"]),
        "",
        "### Rule Family Catalog",
        "",
        frame_to_markdown(outputs["task728_interaction_rule_family_catalog.csv"].head(40)),
        "",
        "### Rule Coverage Audit",
        "",
        frame_to_markdown(outputs["task728_rule_coverage_audit.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- 결론: 이번엔 키워드 몇 개가 아니라 5개 Layer 전체 상호작용으로 다시 잡았습니다.",
        "- Evidence가 Economic을 허용/차단하고, Economic이 Price에서 확인되고, Price와 Slot이 경쟁하며, Risk가 최종 예산과 무효화를 겁니다.",
        "- 관측된 5-Layer 조합마다 rule family를 붙였습니다.",
        "- 그래도 아직 백테스트는 금지입니다. 앞단 source-certified primitive fact와 denominator가 아직 없기 때문입니다.",
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
    artifacts = build_task728(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} "
        f"observed_cells={decision['observed_interaction_cell_count']} "
        f"backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
