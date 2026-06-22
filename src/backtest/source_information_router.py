from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


OPERATING_FACT_FAMILIES = ["revenue", "order", "backlog", "guidance", "margin"]


@dataclass(frozen=True)
class SourceRoute:
    source_form_family: str
    route_circuit: str
    source_route_state: str
    allowed_fact_families: tuple[str, ...]
    forbidden_fact_families: tuple[str, ...]
    can_create_operating_catalyst: int
    can_modify_operating_catalyst: int
    required_interaction_edge: int
    operating_extractor_permission_state: str


SOURCE_ROUTE_MAP: dict[str, SourceRoute] = {
    "form4_insider": SourceRoute(
        source_form_family="form4_insider",
        route_circuit="insider_behavior_circuit",
        source_route_state="insider_behavior_route",
        allowed_fact_families=("insider_transaction", "executive_behavior", "ownership_change"),
        forbidden_fact_families=tuple(OPERATING_FACT_FAMILIES),
        can_create_operating_catalyst=0,
        can_modify_operating_catalyst=1,
        required_interaction_edge=1,
        operating_extractor_permission_state="denied_non_operating_source",
    ),
    "schedule_13d_13g": SourceRoute(
        source_form_family="schedule_13d_13g",
        route_circuit="activist_or_control_circuit",
        source_route_state="activist_or_control_route",
        allowed_fact_families=("ownership_intent", "control_intent", "activist_pressure", "holder_concentration"),
        forbidden_fact_families=tuple(OPERATING_FACT_FAMILIES),
        can_create_operating_catalyst=0,
        can_modify_operating_catalyst=1,
        required_interaction_edge=1,
        operating_extractor_permission_state="denied_non_operating_source",
    ),
    "form_13f": SourceRoute(
        source_form_family="form_13f",
        route_circuit="institutional_positioning_circuit",
        source_route_state="institutional_positioning_route",
        allowed_fact_families=("institutional_sponsorship", "crowding", "positioning_change"),
        forbidden_fact_families=tuple(OPERATING_FACT_FAMILIES),
        can_create_operating_catalyst=0,
        can_modify_operating_catalyst=1,
        required_interaction_edge=1,
        operating_extractor_permission_state="denied_non_operating_source",
    ),
    "ownership_or_institutional_filing": SourceRoute(
        source_form_family="ownership_or_institutional_filing",
        route_circuit="ownership_structure_circuit",
        source_route_state="ownership_structure_route",
        allowed_fact_families=("float_structure", "holder_concentration", "ownership_change"),
        forbidden_fact_families=tuple(OPERATING_FACT_FAMILIES),
        can_create_operating_catalyst=0,
        can_modify_operating_catalyst=1,
        required_interaction_edge=1,
        operating_extractor_permission_state="denied_non_operating_source",
    ),
    "generic_8k": SourceRoute(
        source_form_family="generic_8k",
        route_circuit="event_classifier_circuit",
        source_route_state="generic_event_classification_route",
        allowed_fact_families=("event_item_type", "material_agreement", "governance_event", "operations_if_classified"),
        forbidden_fact_families=("unclassified_operating_catalyst",),
        can_create_operating_catalyst=0,
        can_modify_operating_catalyst=1,
        required_interaction_edge=1,
        operating_extractor_permission_state="denied_generic_unclassified",
    ),
    "financing_8k": SourceRoute(
        source_form_family="financing_8k",
        route_circuit="credit_financing_circuit",
        source_route_state="financing_credit_route",
        allowed_fact_families=("liquidity", "dilution", "credit_terms", "runway", "use_of_proceeds"),
        forbidden_fact_families=("standalone_operating_catalyst",),
        can_create_operating_catalyst=0,
        can_modify_operating_catalyst=1,
        required_interaction_edge=1,
        operating_extractor_permission_state="denied_financing_needs_interaction",
    ),
    "macro_policy_or_geopolitical_source": SourceRoute(
        source_form_family="macro_policy_or_geopolitical_source",
        route_circuit="macro_policy_transmission_circuit",
        source_route_state="macro_policy_route",
        allowed_fact_families=("policy_tailwind", "regulatory_risk", "budget_impulse", "supply_chain_context"),
        forbidden_fact_families=("single_name_operating_catalyst_without_company_link",),
        can_create_operating_catalyst=0,
        can_modify_operating_catalyst=1,
        required_interaction_edge=1,
        operating_extractor_permission_state="denied_without_company_link",
    ),
}


def route_source_event(row: pd.Series) -> dict[str, object]:
    source_family = clean_text(row.get("source_form_family"))
    route = SOURCE_ROUTE_MAP.get(
        source_family,
        SourceRoute(
            source_form_family=source_family or "unknown",
            route_circuit="source_gap_circuit",
            source_route_state="source_gap_route",
            allowed_fact_families=(),
            forbidden_fact_families=tuple(OPERATING_FACT_FAMILIES),
            can_create_operating_catalyst=0,
            can_modify_operating_catalyst=0,
            required_interaction_edge=0,
            operating_extractor_permission_state="denied_source_gap",
        ),
    )
    output = asdict(route)
    output["allowed_fact_families"] = "|".join(route.allowed_fact_families)
    output["forbidden_fact_families"] = "|".join(route.forbidden_fact_families)
    output["source_is_discarded_flag"] = 0
    output["operating_fact_creation_allowed_flag"] = int(route.can_create_operating_catalyst)
    output["backtest_eligible_flag"] = 0
    output["outcome_used_for_assignment_flag"] = 0
    return output


def build_cross_circuit_edges(routed_events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in routed_events.iterrows():
        circuit = row["route_circuit"]
        if circuit == "insider_behavior_circuit":
            rows.append(edge(row, "FORM4_CONTEXT_MODIFIES_NOT_CREATES_OPERATING_CATALYST", "confidence_cap_or_reinforcing", "operating_catalyst_circuit"))
        elif circuit == "activist_or_control_circuit":
            rows.append(edge(row, "ACTIVE_OR_PASSIVE_OWNERSHIP_ROUTES_SPECIAL_SITUATION", "escalation", "portfolio_slot_circuit"))
        elif circuit == "institutional_positioning_circuit":
            rows.append(edge(row, "INSTITUTIONAL_POSITIONING_MODIFIES_CROWDING_RISK", "sizing_modifier", "risk_budget_circuit"))
        elif circuit == "ownership_structure_circuit":
            rows.append(edge(row, "OWNERSHIP_STRUCTURE_MODIFIES_FLOAT_AND_LIQUIDITY", "sizing_modifier", "risk_budget_circuit"))
        elif circuit == "event_classifier_circuit":
            rows.append(edge(row, "GENERIC_8K_REQUIRES_ITEM_CLASSIFICATION", "prerequisite", "operating_catalyst_circuit"))
        elif circuit == "credit_financing_circuit":
            rows.append(edge(row, "FINANCING_INTERACTS_WITH_GROWTH_DILUTION_LIQUIDITY", "offsetting_or_reinforcing", "economic_transmission_circuit"))
        elif circuit == "macro_policy_transmission_circuit":
            rows.append(edge(row, "MACRO_POLICY_REQUIRES_COMPANY_LINK_FOR_SINGLE_NAME", "prerequisite", "operating_catalyst_circuit"))
    return pd.DataFrame(rows)


def edge(row: pd.Series, rule_id: str, relation_type: str, target_circuit: str) -> dict[str, object]:
    return {
        "lifecycle_id": row.get("lifecycle_id", ""),
        "symbol": row.get("symbol", ""),
        "theme_id": row.get("theme_id", ""),
        "entry_ts": row.get("entry_ts", ""),
        "split_name": row.get("split_name", ""),
        "source_form_family": row.get("source_form_family", ""),
        "source_route_state": row.get("source_route_state", ""),
        "source_circuit": row.get("route_circuit", ""),
        "target_circuit": target_circuit,
        "rule_id": rule_id,
        "relation_type": relation_type,
        "backtest_eligible_flag": 0,
        "outcome_used_for_assignment_flag": 0,
    }


def clean_text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "nat"} else text
