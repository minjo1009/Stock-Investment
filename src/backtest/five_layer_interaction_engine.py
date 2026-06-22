from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import pandas as pd


RELATION_PRIORITY = {
    "blocker": 100,
    "prerequisite": 90,
    "invalidation": 80,
    "confidence_cap": 70,
    "offsetting": 60,
    "sizing_modifier": 50,
    "escalation": 40,
    "reinforcing": 30,
}


@dataclass(frozen=True)
class InteractionEdge:
    lifecycle_id: str
    symbol: str
    theme_id: str
    entry_ts: str
    split_name: str
    edge_scope: str
    rule_family_id: str
    relation_type: str
    source_layer: str
    target_layer: str
    output_state: str
    reason: str
    priority: int
    assignment_allowed_flag: int = 0
    backtest_allowed_flag: int = 0


@dataclass(frozen=True)
class InteractionResolution:
    lifecycle_id: str
    symbol: str
    theme_id: str
    entry_ts: str
    split_name: str
    l1_l2_economic_permission_state: str
    l2_l3_thesis_confirmation_state: str
    l3_l4_slot_adjustment_state: str
    l4_l5_budget_state: str
    final_actionability_state: str
    dominant_relation_type: str
    dominant_rule_family_id: str
    edge_count: int
    blocker_edge_count: int
    confidence_cap_edge_count: int
    reinforcing_edge_count: int
    source_denominator_gate_pass_flag: int
    primitive_fact_gate_state: str
    primitive_fact_adapter_source_task: str
    primitive_fact_adapter_source_packet_id: str
    primitive_fact_gate_reason: str
    primitive_fact_gate_pass_flag: int
    interaction_engine_assignment_allowed_flag: int = 0
    backtest_eligible_flag: int = 0
    real_capital_status: str = "FORBIDDEN"


def evaluate_interaction_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    edge_rows: list[dict[str, object]] = []
    resolution_rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        edges = evaluate_candidate_edges(row)
        resolution = resolve_candidate(row, edges)
        edge_rows.extend(asdict(edge) for edge in edges)
        resolution_rows.append(asdict(resolution))
    return pd.DataFrame(edge_rows), pd.DataFrame(resolution_rows)


def evaluate_candidate_edges(row: pd.Series) -> list[InteractionEdge]:
    edges = [
        l1_l2_evidence_gate(row),
        l1_l2_source_economic_contradiction(row),
        l2_l3_thesis_confirmation(row),
        l2_l5_thesis_invalidation(row),
        l3_l4_slot_adjustment(row),
        l4_l5_budget_interaction(row),
        all_layer_final_gate(row),
    ]
    return [edge for edge in edges if edge is not None]


def resolve_candidate(row: pd.Series, edges: list[InteractionEdge]) -> InteractionResolution:
    sorted_edges = sorted(edges, key=lambda edge: edge.priority, reverse=True)
    dominant = sorted_edges[0] if sorted_edges else make_edge(row, "ALL", "ALL_000", "prerequisite", "ALL", "ALL", "no_interaction_edges", "no interaction edge generated")
    edge_types = [edge.relation_type for edge in edges]
    rule_ids = [edge.rule_family_id for edge in edges]

    blocker_count = edge_types.count("blocker")
    cap_count = edge_types.count("confidence_cap")
    reinforcing_count = edge_types.count("reinforcing")
    source_gate_pass = int(not any(edge.rule_family_id in {"L1_L2_GATE_001", "L1_L2_GATE_002", "L1_L2_GATE_003", "L1_L2_CONTRA_005", "ALL_026"} for edge in edges))
    primitive_gate_state = primitive_fact_gate_state(row)
    primitive_fact_gate_pass = int(primitive_gate_state == "pass")

    return InteractionResolution(
        lifecycle_id=str(row.get("lifecycle_id", "")),
        symbol=str(row.get("symbol", "")),
        theme_id=str(row.get("theme_id", "")),
        entry_ts=str(row.get("entry_ts", "")),
        split_name=str(row.get("split_name", "")),
        l1_l2_economic_permission_state=resolution_for_scope(edges, "L1->L2", default="economic_permission_unknown"),
        l2_l3_thesis_confirmation_state=resolution_for_scope(edges, "L2xL3", default="thesis_confirmation_unknown"),
        l3_l4_slot_adjustment_state=resolution_for_scope(edges, "L3xL4", default="slot_adjustment_unknown"),
        l4_l5_budget_state=resolution_for_scope(edges, "L4xL5", default="budget_interaction_unknown"),
        final_actionability_state=final_actionability(edge_types, rule_ids, source_gate_pass, primitive_gate_state),
        dominant_relation_type=dominant.relation_type,
        dominant_rule_family_id=dominant.rule_family_id,
        edge_count=len(edges),
        blocker_edge_count=blocker_count,
        confidence_cap_edge_count=cap_count,
        reinforcing_edge_count=reinforcing_count,
        source_denominator_gate_pass_flag=source_gate_pass,
        primitive_fact_gate_state=primitive_gate_state,
        primitive_fact_adapter_source_task=adapter_provenance(row, "adapter_source_task"),
        primitive_fact_adapter_source_packet_id=adapter_provenance(row, "adapter_source_packet_id"),
        primitive_fact_gate_reason=adapter_provenance(row, "adapter_gate_reason"),
        primitive_fact_gate_pass_flag=primitive_fact_gate_pass,
    )


def l1_l2_evidence_gate(row: pd.Series) -> InteractionEdge:
    evidence = state(row, "evidence_brain_state")
    source_type = state(row, "source_type_state")
    strength = state(row, "evidence_strength_state")
    directness = state(row, "source_directness_state")
    if "source_gap" in evidence or "no_source" in strength:
        return make_edge(row, "L1->L2", "L1_L2_GATE_001", "prerequisite", "L1_Evidence", "L2_Economic", "economic_claim_source_blocked", "source gap or no source evidence blocks positive economic transmission")
    if source_type in {"ownership_or_filing_source"}:
        return make_edge(row, "L1->L2", "L1_L2_GATE_003", "blocker", "L1_Evidence", "L2_Economic", "source_family_blocks_economic_claim", "ownership or filing-only source cannot support economic claim")
    if "weak" in strength or "noise" in evidence or "thin" in directness:
        return make_edge(row, "L1->L2", "L1_L2_GATE_002", "confidence_cap", "L1_Evidence", "L2_Economic", "economic_claim_capped_by_evidence", "weak or thin evidence caps L2 economic interpretation")
    return make_edge(row, "L1->L2", "L1_L2_ALLOW_001", "prerequisite", "L1_Evidence", "L2_Economic", "economic_claim_review_allowed", "L1 does not block L2, but no standalone trade signal is allowed")


def l1_l2_source_economic_contradiction(row: pd.Series) -> InteractionEdge:
    novelty = state(row, "novelty_state")
    directness = state(row, "source_directness_state")
    economic = state(row, "economic_transmission_state")
    funding = state(row, "funding_path_state")
    dilution = state(row, "dilution_overhang_state")
    if "funding_need" in funding or "dilution_overhang_unabsorbed" in dilution:
        return make_edge(row, "L1xL2", "L1_L2_FIN_007", "blocker", "L1_Evidence", "L2_Economic", "dilution_offsets_growth_claim", "unabsorbed dilution or funding need offsets growth claim")
    if is_stale_or_reaffirmed(novelty) and positive_economic(economic):
        return make_edge(row, "L1xL2", "L1_L2_CONTRA_004", "offsetting", "L1_Evidence", "L2_Economic", "stale_or_reaffirmed_economic_claim", "stale or reaffirmed source offsets strong L2 economic claim")
    if "indirect" in directness and positive_economic(economic):
        return make_edge(row, "L1xL2", "L1_L2_CONTRA_005", "confidence_cap", "L1_Evidence", "L2_Economic", "indirect_strong_economic_review", "indirect evidence cannot fully support strong economic state")
    if "financing" in state(row, "financing_context_state") and positive_economic(economic):
        return make_edge(row, "L1xL2", "L1_L2_FIN_006", "escalation", "L1_Evidence", "L2_Economic", "financing_growth_bridge_needed", "financing plus growth path requires use-of-proceeds and dilution bridge")
    return make_edge(row, "L1xL2", "L1_L2_NEUTRAL_001", "prerequisite", "L1_Evidence", "L2_Economic", "no_source_economic_contradiction_detected", "no L1/L2 contradiction detected")


def l2_l3_thesis_confirmation(row: pd.Series) -> InteractionEdge:
    economic = state(row, "economic_transmission_state")
    price = state(row, "market_pricing_brain_state")
    acceptance = state(row, "pricing_acceptance_state")
    acceptance_failure = state(row, "acceptance_failure_state")
    if positive_economic(economic) and "market_accepts" in price:
        return make_edge(row, "L2xL3", "L2_L3_PRICE_008", "reinforcing", "L2_Economic", "L3_Price", "economic_price_reinforcing", "economic path and market acceptance align")
    if positive_economic(economic) and ("incomplete" in price or "building" in acceptance):
        return make_edge(row, "L2xL3", "L2_L3_PRICE_009", "prerequisite", "L2_Economic", "L3_Price", "positive_thesis_needs_price_acceptance", "positive economic thesis requires market acceptance confirmation")
    if not positive_economic(economic) and "market_accepts" in price:
        return make_edge(row, "L2xL3", "L2_L3_PRICE_010", "offsetting", "L2_Economic", "L3_Price", "price_without_economic_thesis", "price acceptance exists without clear source-backed economic thesis")
    if "extension" in acceptance_failure or "near_high" in acceptance:
        return make_edge(row, "L2xL3", "L2_L3_PRICE_011", "confidence_cap", "L2_Economic", "L3_Price", "extension_caps_thesis", "extension risk caps thesis despite price strength")
    return make_edge(row, "L2xL3", "L2_L3_NEUTRAL_001", "prerequisite", "L2_Economic", "L3_Price", "market_confirmation_needed", "L2/L3 interaction remains unconfirmed")


def l2_l5_thesis_invalidation(row: pd.Series) -> InteractionEdge:
    economic = state(row, "economic_transmission_state")
    funding = state(row, "funding_path_state")
    invalidation = state(row, "invalidation_condition")
    if "overhang" in funding or "overhang" in invalidation:
        return make_edge(row, "L2xL5", "L2_L5_INV_013", "invalidation", "L2_Economic", "L5_Risk", "overhang_absorption_required", "overhang thesis is invalid if follow-up price/action does not absorb financing")
    if positive_economic(economic) and "invalid_if" in invalidation:
        return make_edge(row, "L2xL5", "L2_L5_INV_012", "invalidation", "L2_Economic", "L5_Risk", "thesis_specific_invalidation_required", "economic claim must trace to thesis-specific invalidation")
    return make_edge(row, "L2xL5", "L2_L5_NEUTRAL_001", "prerequisite", "L2_Economic", "L5_Risk", "invalidation_trace_required", "L5 must cite which L2 thesis would fail")


def l3_l4_slot_adjustment(row: pd.Series) -> InteractionEdge:
    price = state(row, "market_pricing_brain_state")
    acceptance = state(row, "pricing_acceptance_state")
    slot = state(row, "slot_competition_state")
    cluster = state(row, "exposure_cluster_state")
    portfolio = state(row, "portfolio_brain_state")
    if "market_accepts" in price and "slot_leader" in slot and cluster == "theme_cluster_low":
        return make_edge(row, "L3xL4", "L3_L4_SLOT_014", "reinforcing", "L3_Price", "L4_Portfolio", "accepted_slot_leader", "price accepted and same-timestamp slot leader reinforce review priority")
    if ("incomplete" in price or "building" in acceptance) and "contender" in slot:
        return make_edge(row, "L3xL4", "L3_L4_SLOT_015", "confidence_cap", "L3_Price", "L4_Portfolio", "contender_needs_absorption_and_superiority", "contender needs both price absorption and cohort superiority proof")
    if "market_accepts" in price and ("cluster_high" in cluster or "clustered" in portfolio):
        return make_edge(row, "L3xL4", "L3_L4_SLOT_016", "offsetting", "L3_Price", "L4_Portfolio", "accepted_but_cluster_or_extension_capped", "accepted price is capped by cluster or exposure concentration")
    return make_edge(row, "L3xL4", "L3_L4_NEUTRAL_001", "prerequisite", "L3_Price", "L4_Portfolio", "slot_claim_needs_cohort_context", "slot adjustment needs same-timestamp cohort context")


def l4_l5_budget_interaction(row: pd.Series) -> InteractionEdge:
    slot = state(row, "slot_competition_state")
    cluster = state(row, "exposure_cluster_state")
    portfolio = state(row, "portfolio_brain_state")
    risk_budget = state(row, "risk_budget_state")
    if cluster in {"theme_cluster_medium", "theme_cluster_high"} or "cluster" in risk_budget:
        return make_edge(row, "L4xL5", "L4_L5_RISK_017", "sizing_modifier", "L4_Portfolio", "L5_Risk", "cluster_capped_budget", "theme cluster exposure caps risk budget")
    if "no_slot" in slot or "no_slot" in portfolio:
        return make_edge(row, "L4xL5", "L4_L5_RISK_018", "blocker", "L4_Portfolio", "L5_Risk", "no_slot_no_budget", "no slot claim or no competition proof keeps candidate research-only")
    if "small_review" in risk_budget:
        return make_edge(row, "L4xL5", "L4_L5_RISK_019", "sizing_modifier", "L4_Portfolio", "L5_Risk", "small_review_budget_cap", "risk layer caps review budget")
    return make_edge(row, "L4xL5", "L4_L5_RISK_020", "sizing_modifier", "L4_Portfolio", "L5_Risk", "budget_not_approved", "budget remains review-only and not approved")


def all_layer_final_gate(row: pd.Series) -> InteractionEdge:
    evidence = state(row, "evidence_brain_state")
    review = state(row, "review_decision_state")
    final = state(row, "final_brain_state")
    if "source_gap" in evidence or "source_gap" in review:
        return make_edge(row, "L1xL2xL3xL4xL5", "ALL_026", "blocker", "ALL", "L5_Risk", "full_stack_source_or_risk_block", "source gap or research-only risk blocks actionability")
    if "research_only" in review or "research_only" in final:
        return make_edge(row, "L1xL2xL3xL4xL5", "ALL_026", "blocker", "ALL", "L5_Risk", "full_stack_source_or_risk_block", "research-only state blocks actionability")
    return make_edge(row, "L1xL2xL3xL4xL5", "ALL_025", "prerequisite", "ALL", "L5_Risk", "full_stack_gate_required", "full stack still requires source-certified primitive facts and denominators")


def resolution_for_scope(edges: Iterable[InteractionEdge], scope: str, *, default: str) -> str:
    scoped = [edge for edge in edges if edge.edge_scope == scope]
    if not scoped:
        return default
    return max(scoped, key=lambda edge: edge.priority).output_state


def final_actionability(edge_types: list[str], rule_ids: list[str], source_gate_pass: int, primitive_fact_gate_state_value: str) -> str:
    primitive_fact_gate_pass = primitive_fact_gate_state_value == "pass"
    if "L1_L2_GATE_001" in rule_ids:
        return "RESEARCH_ONLY_SOURCE_GAP_BLOCKED"
    if "L1_L2_GATE_003" in rule_ids:
        return "RESEARCH_ONLY_SOURCE_FAMILY_BLOCKED"
    if "L1_L2_GATE_002" in rule_ids or "L1_L2_CONTRA_005" in rule_ids:
        return "WATCH_CONFIRMATION_SOURCE_QUALITY_CAPPED"
    if "L1_L2_FIN_007" in rule_ids:
        return "RESEARCH_ONLY_DILUTION_OR_FUNDING_BLOCKER"
    if "L4_L5_RISK_018" in rule_ids:
        return "RESEARCH_ONLY_NO_SLOT_OR_BUDGET"
    if "ALL_026" in rule_ids or "blocker" in edge_types:
        return "RESEARCH_ONLY_BLOCKED_BY_INTERACTION"
    if not source_gate_pass:
        return "RESEARCH_ONLY_SOURCE_GATE_FAILED"
    if "invalidation" in edge_types:
        return "WATCH_CONFIRMATION_WITH_INVALIDATION_TRACE"
    if "confidence_cap" in edge_types:
        return "WATCH_CONFIRMATION_CONFIDENCE_CAPPED"
    if not primitive_fact_gate_pass:
        if primitive_fact_gate_state_value == "source_gap":
            return "RESEARCH_ONLY_PRIMITIVE_SOURCE_GAP"
        if primitive_fact_gate_state_value == "context_only":
            return "RESEARCH_ONLY_CONTEXT_ONLY_PRIMITIVE_FACTS"
        if "reinforcing" in edge_types and not {"confidence_cap", "offsetting", "invalidation"}.intersection(edge_types):
            return "REVIEW_ONLY_FULL_STACK_PROMISING_NEEDS_PRIMITIVE_FACTS"
        return "RESEARCH_ONLY_NEEDS_PRIMITIVE_FACTS"
    return "REVIEW_ONLY_PRIMITIVE_FACTS_READY"


def positive_economic(state_value: str) -> bool:
    positive_tokens = ["reinforcing", "tailwind", "growth_funding", "backlog_or_order_path_visible"]
    negative_tokens = ["source_gap", "no_clear", "needs_review"]
    return any(token in state_value for token in positive_tokens) and not any(token in state_value for token in negative_tokens)


def is_stale_or_reaffirmed(novelty_state: str) -> bool:
    return novelty_state in {
        "stale_unconfirmed_information",
        "stale_or_reaffirmed_but_reaccelerating",
        "reaffirmation_not_new_information",
    }


def state(row: pd.Series, column: str) -> str:
    value = row.get(column, "")
    if pd.isna(value):
        return ""
    return str(value)


def primitive_fact_gate_state(row: pd.Series) -> str:
    value = state(row, "primitive_fact_adapter_gate_state").strip().lower()
    if value in {"pass", "cap", "context_only", "not_ready", "source_gap"}:
        return value
    return "not_ready"


def adapter_provenance(row: pd.Series, column: str) -> str:
    value = state(row, column).strip()
    return value if value else "not_supplied"


def make_edge(
    row: pd.Series,
    scope: str,
    rule_family_id: str,
    relation_type: str,
    source_layer: str,
    target_layer: str,
    output_state: str,
    reason: str,
) -> InteractionEdge:
    return InteractionEdge(
        lifecycle_id=str(row.get("lifecycle_id", "")),
        symbol=str(row.get("symbol", "")),
        theme_id=str(row.get("theme_id", "")),
        entry_ts=str(row.get("entry_ts", "")),
        split_name=str(row.get("split_name", "")),
        edge_scope=scope,
        rule_family_id=rule_family_id,
        relation_type=relation_type,
        source_layer=source_layer,
        target_layer=target_layer,
        output_state=output_state,
        reason=reason,
        priority=RELATION_PRIORITY[relation_type],
    )
