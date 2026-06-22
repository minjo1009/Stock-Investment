from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


ENGINEERING_HIGH_FAMILIES = {
    "activist_control_intent_enrichment",
    "activist_ownership_change_enrichment",
    "financial_results_expectation_enrichment",
    "financing_terms_enrichment",
    "form4_plan_pattern_enrichment",
    "form4_transaction_code_enrichment",
    "generic_8k_item_classifier_enrichment",
    "ownership_change_enrichment",
    "strategic_mna_enrichment",
}


CIRCUIT_TAXONOMY = {
    "form4_insider_behavior": {
        "allowed": [
            "form4_plan_pattern_resolved",
            "form4_open_market_buy_context",
            "form4_open_market_sale_context",
            "form4_award_or_option_context_only",
            "form4_automatic_plan_context_only",
            "form4_transaction_code_unknown",
            "insider_pattern_enrichment_needed",
        ],
        "forbidden": ["operating_catalyst_supported", "buy_signal", "sell_signal"],
    },
    "activist_control": {
        "allowed": [
            "active_control_intent_review",
            "passive_ownership_context",
            "activist_escalation_needed",
            "ownership_threshold_context",
            "purpose_language_unknown",
        ],
        "forbidden": ["operating_catalyst_supported", "actionability"],
    },
    "institutional_positioning": {
        "allowed": [
            "institutional_positioning_context_only",
            "sponsorship_context_resolved",
            "crowding_review_needed",
            "filing_lag_context",
        ],
        "forbidden": ["fresh_catalyst", "buy_signal"],
    },
    "ownership_float_structure": {
        "allowed": [
            "ownership_structure_resolved",
            "float_context_needed",
            "holder_concentration_review",
            "ownership_change_unknown",
        ],
        "forbidden": ["revenue_path_visible", "margin_path_visible"],
    },
    "generic_8k_classifier": {
        "allowed": [
            "generic_8k_classified",
            "generic_8k_route_needed",
            "compensation_context_only",
            "governance_context_only",
            "financing_route_required",
            "mna_route_required",
            "operating_transmission_needed",
        ],
        "forbidden": ["connection_supported_from_item_101_only"],
    },
    "credit_financing": {
        "allowed": [
            "financing_terms_complete",
            "financing_terms_incomplete",
            "growth_funding_review",
            "dilution_overhang_review",
            "liquidity_rescue_review",
            "debt_refinance_context",
        ],
        "forbidden": ["bullish_financing", "bearish_financing", "trade_ready"],
    },
    "strategic_mna_investment": {
        "allowed": [
            "strategic_mna_review",
            "strategic_fit_context",
            "integration_risk_review",
            "stock_consideration_dilution_review",
            "mna_operating_link_needed",
        ],
        "forbidden": ["operating_supported_without_transmission"],
    },
    "macro_policy_transmission": {
        "allowed": [
            "theme_context_only",
            "company_link_needed",
            "weak_company_link_review",
            "policy_transmission_review",
            "regulatory_risk_context",
        ],
        "forbidden": ["single_name_catalyst_without_company_link"],
    },
    "financial_results_guidance": {
        "allowed": [
            "financial_result_context_resolved",
            "results_denominator_needed",
            "guidance_revision_review",
            "expectation_comparator_needed",
            "margin_bridge_needed",
        ],
        "forbidden": ["earnings_trade_signal", "beat_miss_score"],
    },
    "governance_management": {
        "allowed": [
            "governance_context_only",
            "management_change_review",
            "governance_risk_review",
            "compensation_context_only",
            "severance_context_only",
        ],
        "forbidden": ["operating_catalyst_supported"],
    },
}


TARGET_EXTRACTORS = {
    "activist_control": "activist_control_ownership_extractor",
    "credit_financing": "financing_terms_extractor",
    "financial_results_guidance": "financial_results_guidance_extractor",
    "form4_insider_behavior": "form4_insider_pattern_extractor",
    "generic_8k_classifier": "generic_8k_router_extractor",
    "governance_management": "governance_management_context_extractor",
    "institutional_positioning": "institutional_positioning_extractor",
    "macro_policy_transmission": "macro_company_link_extractor",
    "ownership_float_structure": "ownership_float_structure_extractor",
    "strategic_mna_investment": "strategic_mna_extractor",
}


TARGET_RESOLVERS = {
    "activist_control": "activist_control_resolver",
    "credit_financing": "financing_terms_resolver",
    "financial_results_guidance": "financial_results_guidance_resolver",
    "form4_insider_behavior": "form4_insider_behavior_resolver",
    "generic_8k_classifier": "generic_8k_route_resolver",
    "governance_management": "governance_management_resolver",
    "institutional_positioning": "institutional_positioning_resolver",
    "macro_policy_transmission": "macro_company_link_resolver",
    "ownership_float_structure": "ownership_float_structure_resolver",
    "strategic_mna_investment": "strategic_mna_resolver",
}


@dataclass(frozen=True)
class ExtractorUpgradeWorkOrder:
    work_order_id: str
    requirement_family: str
    source_circuit: str
    target_extractor: str
    input_artifacts: str
    required_primitive_fields: str
    forbidden_primitive_fields: str
    required_denominator_joins: str
    required_comparator_joins: str
    required_timing_checks: str
    output_contract: str
    allowed_downstream_layers: str
    guardrail_ids: str
    engineering_lane: str
    engineering_reason: str
    research_only_flag: int
    rule_id: str


@dataclass(frozen=True)
class ResolverUpgradeWorkOrder:
    work_order_id: str
    requirement_family: str
    resolver_target_state: str
    source_circuit: str
    target_resolver: str
    input_primitives: str
    input_denominators: str
    input_comparators: str
    input_timing_fields: str
    allowed_output_states: str
    forbidden_output_states: str
    layer_interactions_allowed: str
    layer_interactions_forbidden: str
    must_emit_trace: int
    research_only_flag: int
    rule_id: str


def build_workbench(requirements: pd.DataFrame) -> dict[str, pd.DataFrame]:
    extractor_orders = build_extractor_work_orders(requirements)
    resolver_orders = build_resolver_work_orders(requirements)
    trace = build_requirement_trace(requirements, extractor_orders, resolver_orders)
    taxonomy = build_allowed_resolver_state_taxonomy()
    lane_summary = build_engineering_lane_summary(extractor_orders, resolver_orders, requirements)
    return {
        "extractor_orders": extractor_orders,
        "resolver_orders": resolver_orders,
        "trace": trace,
        "taxonomy": taxonomy,
        "lane_summary": lane_summary,
    }


def build_extractor_work_orders(requirements: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in requirements.groupby(["requirement_family", "circuit_type"], dropna=False):
        family, circuit = keys
        primitives = sorted(set_from_pipe(group["missing_primitive_fields"]))
        denominators = sorted(set_from_pipe(group["required_denominators"]))
        comparators = sorted(set_from_pipe(group["required_comparators"]))
        timing = sorted(set_from_pipe(group["required_timing_checks"]))
        lane, reason = engineering_lane(family, circuit, len(group), group["lifecycle_id"].nunique())
        rows.append(
            asdict(
                ExtractorUpgradeWorkOrder(
                    work_order_id=f"TASK739_EXTRACTOR__{family}",
                    requirement_family=str(family),
                    source_circuit=str(circuit),
                    target_extractor=TARGET_EXTRACTORS.get(str(circuit), "generic_semantic_extractor"),
                    input_artifacts="task738_enrichment_requirements|task736_semantic_translation|source_attached_event_detail",
                    required_primitive_fields=pipe(primitives),
                    forbidden_primitive_fields=pipe(forbidden_primitives_for_circuit(str(circuit))),
                    required_denominator_joins=pipe(denominators),
                    required_comparator_joins=pipe(comparators),
                    required_timing_checks=pipe(timing),
                    output_contract=f"{family}_primitive_packet",
                    allowed_downstream_layers=pipe(allowed_layers_for_group(group)),
                    guardrail_ids=pipe(common_guardrails(str(circuit))),
                    engineering_lane=lane,
                    engineering_reason=reason,
                    research_only_flag=1,
                    rule_id="TASK739_EXTRACTOR_WORK_ORDER_REVIEW_ONLY",
                )
            )
        )
    return pd.DataFrame(rows).sort_values(["engineering_lane", "requirement_family"]).reset_index(drop=True)


def build_resolver_work_orders(requirements: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in requirements.groupby(["requirement_family", "resolver_target_state", "circuit_type"], dropna=False):
        family, resolver_target, circuit = keys
        taxonomy = CIRCUIT_TAXONOMY.get(str(circuit), {"allowed": ["semantic_context_needed"], "forbidden": ["trade_ready"]})
        rows.append(
            asdict(
                ResolverUpgradeWorkOrder(
                    work_order_id=f"TASK739_RESOLVER__{family}",
                    requirement_family=str(family),
                    resolver_target_state=str(resolver_target),
                    source_circuit=str(circuit),
                    target_resolver=TARGET_RESOLVERS.get(str(circuit), "generic_semantic_resolver"),
                    input_primitives=pipe(sorted(set_from_pipe(group["missing_primitive_fields"]))),
                    input_denominators=pipe(sorted(set_from_pipe(group["required_denominators"]))),
                    input_comparators=pipe(sorted(set_from_pipe(group["required_comparators"]))),
                    input_timing_fields=pipe(sorted(set_from_pipe(group["required_timing_checks"]))),
                    allowed_output_states=pipe(taxonomy["allowed"]),
                    forbidden_output_states=pipe(taxonomy["forbidden"]),
                    layer_interactions_allowed=pipe(sorted(set_from_pipe(group["required_interaction_fields"]))),
                    layer_interactions_forbidden=pipe(["score_creation", "ranking_creation", "trade_signal_creation", "outcome_label_use"]),
                    must_emit_trace=1,
                    research_only_flag=1,
                    rule_id="TASK739_RESOLVER_WORK_ORDER_REVIEW_ONLY",
                )
            )
        )
    return pd.DataFrame(rows).sort_values(["source_circuit", "requirement_family"]).reset_index(drop=True)


def build_requirement_trace(requirements: pd.DataFrame, extractor_orders: pd.DataFrame, resolver_orders: pd.DataFrame) -> pd.DataFrame:
    extractor_map = dict(zip(extractor_orders["requirement_family"], extractor_orders["work_order_id"]))
    resolver_map = dict(zip(resolver_orders["requirement_family"], resolver_orders["work_order_id"]))
    rows = []
    for _, row in requirements.iterrows():
        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "bundle_id": row["bundle_id"],
                "source_event_id": row["source_event_id"],
                "symbol": row["symbol"],
                "theme_id": row["theme_id"],
                "entry_ts": row["entry_ts"],
                "requirement_family": row["requirement_family"],
                "resolver_target_state": row["resolver_target_state"],
                "extractor_work_order_id": extractor_map[row["requirement_family"]],
                "resolver_work_order_id": resolver_map[row["requirement_family"]],
                "source_circuit": row["circuit_type"],
                "engineering_lane": engineering_lane(row["requirement_family"], row["circuit_type"], 1, 1)[0],
                "research_only_flag": 1,
                "rule_id": "TASK739_REQUIREMENT_TO_WORK_ORDER_TRACE",
            }
        )
    return pd.DataFrame(rows)


def build_allowed_resolver_state_taxonomy() -> pd.DataFrame:
    rows = []
    for circuit, taxonomy in CIRCUIT_TAXONOMY.items():
        for state in taxonomy["allowed"]:
            rows.append({"source_circuit": circuit, "state_type": "allowed", "resolver_state": state})
        for state in taxonomy["forbidden"]:
            rows.append({"source_circuit": circuit, "state_type": "forbidden", "resolver_state": state})
    return pd.DataFrame(rows)


def build_engineering_lane_summary(extractor_orders: pd.DataFrame, resolver_orders: pd.DataFrame, requirements: pd.DataFrame) -> pd.DataFrame:
    grouped = extractor_orders.groupby(["engineering_lane"], dropna=False)
    rows = []
    requirement_counts = requirements.groupby("requirement_family").size().to_dict()
    for lane, group in grouped:
        lane_value = lane[0] if isinstance(lane, tuple) else lane
        families = list(group["requirement_family"].astype(str))
        lane_requirements = requirements[requirements["requirement_family"].isin(families)]
        rows.append(
            {
                "engineering_lane": lane_value,
                "work_order_family_count": len(families),
                "extractor_work_order_count": len(group),
                "resolver_work_order_count": int(resolver_orders["requirement_family"].isin(families).sum()),
                "requirement_count": int(sum(requirement_counts.get(family, 0) for family in families)),
                "bundle_count": int(lane_requirements["lifecycle_id"].nunique()),
                "engineering_lane_is_trading_priority_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("engineering_lane").reset_index(drop=True)


def engineering_lane(family: str, circuit: str, requirement_count: int, bundle_count: int) -> tuple[str, str]:
    if family in ENGINEERING_HIGH_FAMILIES:
        return "engineering_high", "large unknown coverage or high contamination risk before later interpretation"
    if circuit in {"credit_financing", "financial_results_guidance", "generic_8k_classifier", "strategic_mna_investment"}:
        return "engineering_high", "small count but high false-positive operating risk"
    return "engineering_normal", "context or modifier circuit; preserve trace and avoid trade conversion"


def allowed_layers_for_group(group: pd.DataFrame) -> list[str]:
    layers = []
    if int(group["can_affect_confidence"].sum()) > 0:
        layers.append("L2_economic_interpretation")
    if int(group["can_affect_risk"].sum()) > 0:
        layers.append("L5_invalidation_risk")
    if int(group["can_affect_slot"].sum()) > 0:
        layers.append("L4_candidate_bundle_slot_context")
    if not layers:
        layers.append("L1_source_context_trace")
    return layers


def forbidden_primitives_for_circuit(circuit: str) -> list[str]:
    base = ["future_return", "pnl", "winner_label", "trade_signal", "global_rank", "alpha_score"]
    if circuit in {"form4_insider_behavior", "institutional_positioning", "ownership_float_structure", "governance_management", "activist_control"}:
        base.append("operating_catalyst_supported")
    return base


def common_guardrails(circuit: str) -> list[str]:
    guards = [
        "NO_OUTCOME_COLUMNS",
        "NO_SCORE_OR_RANK",
        "NO_BUY_SELL_ACTIONABILITY",
        "UNKNOWN_NOT_BEARISH",
        "TRACE_REQUIRED",
    ]
    if circuit in {"form4_insider_behavior", "institutional_positioning", "ownership_float_structure", "governance_management", "activist_control"}:
        guards.append("NON_OPERATING_CIRCUIT_NO_OPERATING_CATALYST")
    return guards


def set_from_pipe(series: pd.Series) -> set[str]:
    values: set[str] = set()
    for value in series.dropna().astype(str):
        values.update(part for part in value.split("|") if part)
    return values


def pipe(values: list[str]) -> str:
    return "|".join(values)
