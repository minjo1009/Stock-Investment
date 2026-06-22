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

IDENTITY_COLUMNS = ["lifecycle_id", "symbol", "entry_ts", "entry_ts_utc", "theme_id", "split_name"]

EVIDENCE_CONTRACTS: list[dict[str, object]] = [
    {
        "evidence_type": "company_source_event_presence",
        "authority_scope": "assignment_certified",
        "quality_flag": "company_source_assignment_certified_flag",
        "columns": [
            "linked_event_count",
            "source_text_certified_event_count",
            "content_prediction_certified_event_count",
            "political_statement_pre7d_count",
            "geopolitical_event_pre7d_count",
            "institution_ownership_pre30d_count",
            "activist_13d_pre30d_flag",
            "passive_13g_pre30d_flag",
            "insider_form4_or_144_pre30d_flag",
            "ceo_ir_proxy_pre14d_count",
        ],
    },
    {
        "evidence_type": "content_interpretation_signals",
        "authority_scope": "assignment_certified",
        "quality_flag": "content_prediction_assignment_certified_flag",
        "columns": [
            "content_direct_bullish_count",
            "content_direct_bearish_count",
            "content_contract_revenue_count",
            "content_guidance_margin_count",
            "content_supply_demand_count",
            "content_regulatory_policy_count",
            "content_insider_buy_count",
            "content_insider_sell_count",
            "negative_dilution_financing_count",
            "negative_regulation_sanction_tariff_count",
            "negative_ceo_ir_disappointment_count",
            "negative_insider_sell_count",
            "negative_earnings_margin_damage_count",
            "positive_contract_customer_count",
            "positive_backlog_order_count",
            "positive_guidance_up_count",
            "positive_margin_supply_combo_count",
        ],
    },
    {
        "evidence_type": "chart_price_volume",
        "authority_scope": "assignment_certified",
        "quality_flag": "theme_price_assignment_certified_flag",
        "columns": [
            "close_prev",
            "volume_ratio_prev",
            "near_high60_prev",
            "trend_stack_prev",
            "range_pos",
            "intraday_ret_from_open",
            "timing_state",
            "price_acceptance_score",
            "price_acceptance_state",
            "price_chart_acceptance_state",
        ],
    },
    {
        "evidence_type": "theme_market_leadership",
        "authority_scope": "assignment_certified",
        "quality_flag": "theme_price_assignment_certified_flag",
        "columns": [
            "theme_ret20_prev",
            "theme_breadth20_prev",
            "theme_volume_ratio_prev",
            "theme_rank_prev",
            "theme_regime_state_v4",
            "leadership_lifecycle_state",
            "leadership_phase_strength",
            "leadership_market_alignment",
            "theme_leadership_state",
        ],
    },
    {
        "evidence_type": "market_context",
        "authority_scope": "assignment_certified",
        "quality_flag": "theme_price_assignment_certified_flag",
        "columns": [
            "broad_market_score",
            "broad_market_stress",
            "breadth_20d",
            "market_ret_20d",
            "liquidity_ratio",
            "multi_day_market_state_v4",
            "market_state",
            "macro_market_state",
        ],
    },
    {
        "evidence_type": "macro_context_diagnostic",
        "authority_scope": "diagnostic_only",
        "quality_flag": "macro_context_available_for_diagnostic_flag",
        "columns": [
            "macro_series_available_count",
            "macro_employment_state",
            "macro_inflation_state",
            "macro_rates_state",
            "macro_dollar_state",
            "macro_oil_state",
            "macro_credit_state",
            "macro_liquidity_state",
            "macro_overall_state",
            "macro_action_modifier",
            "macro_release_timestamp_repaired_flag",
            "macro_asof_provisional_for_diagnostic_flag",
        ],
    },
    {
        "evidence_type": "portfolio_slot_capacity",
        "authority_scope": "assignment_certified",
        "quality_flag": "portfolio_capacity_assignment_certified_flag",
        "columns": [
            "same_entry_candidate_count",
            "same_entry_theme_count",
            "same_entry_relation_count",
            "portfolio_capacity_state",
            "active_theme_count",
            "active_relation_count",
            "active_driver_count",
            "active_fragile_count",
            "cohort_candidate_count",
            "cohort_slot_rank",
        ],
    },
    {
        "evidence_type": "microstructure_pending",
        "authority_scope": "raw_pending_not_assignment",
        "quality_flag": None,
        "columns": [
            "microstructure_state",
            "microstructure_state_v4",
            "microstructure_used_in_assignment",
        ],
    },
]

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


def build_task688_program(task684_dir: Path = TASK684_DIR) -> dict[str, pd.DataFrame]:
    TASK688_DIR.mkdir(parents=True, exist_ok=True)
    stack = pd.read_csv(task684_dir / "task684_interaction_stack_panel.csv")
    stack = stack.reset_index(drop=True).copy()
    stack["candidate_row_id"] = stack.index.map(lambda idx: f"row_{idx:06d}")

    evidence = build_evidence_objects(stack)
    interpretations = build_economic_interpretation_objects(stack)
    edges = build_state_graph_edges(stack)
    bundles = build_candidate_context_bundles(stack, evidence, interpretations, edges)
    slot = build_slot_decision_explanations(stack, bundles)
    audit = build_contract_integrity_audit(stack, evidence, interpretations, edges, bundles, slot)
    decision = build_decision(stack, evidence, interpretations, edges, bundles, slot, audit)
    pass_fail = build_pass_fail(audit)

    write_outputs(evidence, interpretations, edges, bundles, slot, audit, decision, pass_fail)
    return {
        "evidence": evidence,
        "interpretations": interpretations,
        "edges": edges,
        "bundles": bundles,
        "slot": slot,
        "audit": audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_evidence_objects(stack: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in stack.iterrows():
        for contract in EVIDENCE_CONTRACTS:
            evidence_type = str(contract["evidence_type"])
            configured = list(contract["columns"])
            present = [col for col in configured if col in stack.columns]
            quality_flag = contract["quality_flag"]
            certified = int(row_value(row, quality_flag, 0)) if quality_flag else 0
            if contract["authority_scope"] == "raw_pending_not_assignment":
                source_quality = "raw_pending"
            elif contract["authority_scope"] == "diagnostic_only":
                source_quality = "diagnostic_available" if certified else "diagnostic_gap"
            else:
                source_quality = "certified" if certified else "certification_gap"

            rows.append(
                {
                    "evidence_object_id": object_id(row, evidence_type),
                    **identity(row),
                    "evidence_type": evidence_type,
                    "authority_scope": contract["authority_scope"],
                    "source_quality": source_quality,
                    "available_at_ts": first_nonempty(row, ["entry_ts_utc", "entry_ts"]),
                    "configured_column_count": len(configured),
                    "present_column_count": len(present),
                    "non_null_present_column_count": int(sum(pd.notna(row.get(col)) for col in present)),
                    "raw_columns_used": "|".join(present),
                    "source_certified_flag": certified,
                    "eligible_for_slot_assignment_flag": int(
                        contract["authority_scope"] == "assignment_certified" and certified == 1
                    ),
                    "outcome_used_flag": 0,
                    "future_price_used_flag": 0,
                    "missing_source_used_as_negative_flag": int(row_value(row, "missing_source_used_as_negative", 0)),
                    "macro_provisional_used_as_certified_flag": int(
                        row_value(row, "macro_provisional_used_as_certified", 0)
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_economic_interpretation_objects(stack: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in stack.iterrows():
        contexts = [
            interpret_company_catalyst(row),
            interpret_price_acceptance(row),
            interpret_theme_leadership(row),
            interpret_market_context(row),
            interpret_macro_context(row),
            interpret_portfolio_capacity(row),
        ]
        for context in contexts:
            driver = context["primary_driver"]
            rows.append(
                {
                    "interpretation_object_id": object_id(row, f"interpretation_{driver}"),
                    **identity(row),
                    **context,
                    "outcome_used_flag": 0,
                    "future_price_used_flag": 0,
                    "label_used_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_state_graph_edges(stack: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in stack.iterrows():
        company = interpret_company_catalyst(row)
        price = interpret_price_acceptance(row)
        theme = interpret_theme_leadership(row)
        market = interpret_market_context(row)
        macro = interpret_macro_context(row)
        portfolio = interpret_portfolio_capacity(row)
        edge_specs = [
            {
                "from_node": "company_catalyst",
                "to_node": "price_acceptance",
                "edge_type": relation_between(company["direction"], price["direction"]),
                "authority_scope": "assignment_certified",
                "confidence": min(float(company["confidence"]), float(price["confidence"])),
                "reason_codes": f"company={company['economic_channel']}|price={price['economic_channel']}",
            },
            {
                "from_node": "theme_leadership",
                "to_node": "price_acceptance",
                "edge_type": relation_between(theme["direction"], price["direction"]),
                "authority_scope": "assignment_certified",
                "confidence": min(float(theme["confidence"]), float(price["confidence"])),
                "reason_codes": f"theme={theme['direction']}|price={price['direction']}",
            },
            {
                "from_node": "market_context",
                "to_node": "theme_leadership",
                "edge_type": relation_between(market["direction"], theme["direction"]),
                "authority_scope": "assignment_certified",
                "confidence": min(float(market["confidence"]), float(theme["confidence"])),
                "reason_codes": f"market={market['economic_channel']}|theme={theme['economic_channel']}",
            },
            {
                "from_node": "macro_context",
                "to_node": "market_context",
                "edge_type": "diagnostic_context",
                "authority_scope": "diagnostic_only",
                "confidence": float(macro["confidence"]),
                "reason_codes": f"macro={macro['economic_channel']}|not_slot_assignment_certified",
            },
            {
                "from_node": "company_catalyst",
                "to_node": "relation_transmission",
                "edge_type": relation_from_state(row_value(row, "mechanism_relation_state", "")),
                "authority_scope": "assignment_certified"
                if int(row_value(row, "relation_assignment_certified_flag", 0)) == 1
                else "research_only",
                "confidence": 0.7 if int(row_value(row, "relation_assignment_certified_flag", 0)) == 1 else 0.3,
                "reason_codes": str(row_value(row, "mechanism_relation_state", "missing_relation_state")),
            },
            {
                "from_node": "portfolio_capacity",
                "to_node": "slot_decision",
                "edge_type": "sizing_modifier" if portfolio["direction"] in {"negative", "mixed"} else "reinforcing",
                "authority_scope": "assignment_certified",
                "confidence": float(portfolio["confidence"]),
                "reason_codes": f"capacity={portfolio['economic_channel']}",
            },
        ]
        for spec in edge_specs:
            authority = str(spec["authority_scope"])
            rows.append(
                {
                    "state_graph_edge_id": object_id(row, f"edge_{spec['from_node']}_{spec['to_node']}"),
                    **identity(row),
                    **spec,
                    "eligible_for_slot_assignment_flag": int(authority == "assignment_certified"),
                    "outcome_used_flag": 0,
                    "future_price_used_flag": 0,
                    "label_used_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_candidate_context_bundles(
    stack: pd.DataFrame,
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    edges: pd.DataFrame,
) -> pd.DataFrame:
    evidence_counts = evidence.groupby("lifecycle_id").agg(
        evidence_object_count=("evidence_object_id", "count"),
        slot_eligible_evidence_count=("eligible_for_slot_assignment_flag", "sum"),
    )
    interpretation_counts = interpretations.groupby("lifecycle_id").agg(
        interpretation_object_count=("interpretation_object_id", "count"),
    )
    edge_counts = edges.groupby("lifecycle_id").agg(
        state_graph_edge_count=("state_graph_edge_id", "count"),
        assignment_eligible_edge_count=("eligible_for_slot_assignment_flag", "sum"),
        diagnostic_only_edge_count=("authority_scope", lambda values: int((values == "diagnostic_only").sum())),
    )

    rows = []
    for _, row in stack.iterrows():
        lifecycle_id = str(row["lifecycle_id"])
        evidence_count = int(evidence_counts.loc[lifecycle_id, "evidence_object_count"])
        eligible_evidence = int(evidence_counts.loc[lifecycle_id, "slot_eligible_evidence_count"])
        interpretation_count = int(interpretation_counts.loc[lifecycle_id, "interpretation_object_count"])
        edge_count = int(edge_counts.loc[lifecycle_id, "state_graph_edge_count"])
        eligible_edges = int(edge_counts.loc[lifecycle_id, "assignment_eligible_edge_count"])
        diagnostic_edges = int(edge_counts.loc[lifecycle_id, "diagnostic_only_edge_count"])
        forbidden_sum = int(row_value(row, "missing_source_used_as_negative", 0)) + int(
            row_value(row, "macro_provisional_used_as_certified", 0)
        )
        missing_flags = build_missing_evidence_flags(row)
        rows.append(
            {
                "candidate_context_bundle_id": object_id(row, "candidate_context_bundle"),
                **identity(row),
                "evidence_object_count": evidence_count,
                "slot_eligible_evidence_count": eligible_evidence,
                "interpretation_object_count": interpretation_count,
                "state_graph_edge_count": edge_count,
                "assignment_eligible_edge_count": eligible_edges,
                "diagnostic_only_edge_count": diagnostic_edges,
                "primary_context_summary": build_primary_context_summary(row),
                "missing_evidence_flags": missing_flags,
                "forbidden_flags_sum": forbidden_sum,
                "bundle_assignment_ready_flag": int(
                    int(row_value(row, "allocation_assignment_ready_flag", 0)) == 1
                    and eligible_evidence >= 5
                    and eligible_edges >= 4
                    and forbidden_sum == 0
                ),
                "macro_diagnostic_only_flag": int(row_value(row, "macro_used_for_assignment_flag", 0) == 0),
                "microstructure_pending_flag": int(
                    str(row_value(row, "microstructure_state", "")).upper() == "SOURCE_PENDING_NOT_USED"
                    or str(row_value(row, "microstructure_state_v4", "")).lower() == "microstructure_not_available"
                ),
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_slot_decision_explanations(stack: pd.DataFrame, bundles: pd.DataFrame) -> pd.DataFrame:
    bundle_map = bundles.set_index("lifecycle_id")
    rows = []
    for _, row in stack.iterrows():
        lifecycle_id = str(row["lifecycle_id"])
        bundle = bundle_map.loc[lifecycle_id]
        ready = int(bundle["bundle_assignment_ready_flag"]) == 1
        capacity_state = str(row_value(row, "portfolio_capacity_state", "unknown_capacity"))
        setup = str(row_value(row, "setup_quality_bucket", "unknown_setup"))
        role = classify_candidate_role(row, ready)
        replacement_hurdle = int(
            capacity_state not in {"slot_competition_low", "low_competition"}
            or int(row_value(row, "same_entry_candidate_count", 0)) >= 5
            or int(row_value(row, "active_relation_count", 0)) >= 3
        )
        rows.append(
            {
                "slot_decision_explanation_id": object_id(row, "slot_decision_explanation"),
                **identity(row),
                "candidate_role": role,
                "slot_claim_basis": build_slot_claim_basis(row),
                "slot_risk_basis": build_slot_risk_basis(row),
                "replacement_hurdle_required_flag": replacement_hurdle,
                "same_entry_candidate_count": int(row_value(row, "same_entry_candidate_count", 0)),
                "same_entry_theme_count": int(row_value(row, "same_entry_theme_count", 0)),
                "same_entry_relation_count": int(row_value(row, "same_entry_relation_count", 0)),
                "active_theme_count": int(row_value(row, "active_theme_count", 0)),
                "active_relation_count": int(row_value(row, "active_relation_count", 0)),
                "bundle_assignment_ready_flag": int(ready),
                "do_not_trade_reason": "" if ready else build_do_not_trade_reason(row, bundle),
                "setup_quality_bucket": setup,
                "action_family": str(row_value(row, "candidate_action_family", "no_action_family")),
                "allowed_inputs_only_flag": 1,
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def interpret_company_catalyst(row: pd.Series) -> dict[str, object]:
    positive = sum_int_values(
        row,
        [
            "positive_contract_customer_count",
            "positive_backlog_order_count",
            "positive_guidance_up_count",
            "positive_margin_supply_combo_count",
            "content_contract_revenue_count",
            "content_guidance_margin_count",
            "content_supply_demand_count",
        ],
    )
    negative = sum_int_values(
        row,
        [
            "negative_dilution_financing_count",
            "negative_regulation_sanction_tariff_count",
            "negative_ceo_ir_disappointment_count",
            "negative_insider_sell_count",
            "negative_earnings_margin_damage_count",
            "content_direct_bearish_count",
        ],
    )
    if positive > 0 and negative > 0:
        direction = "mixed"
    elif positive > 0:
        direction = "positive"
    elif negative > 0:
        direction = "negative"
    else:
        direction = "neutral"

    channel = str(row_value(row, "catalyst_path_type", "no_explicit_catalyst"))
    if channel in {"", "nan", "None"}:
        channel = strongest_company_channel(row)
    return {
        "primary_driver": "company_catalyst",
        "direction": direction,
        "economic_channel": channel,
        "magnitude_proxy": safe_float(row_value(row, "catalyst_quality_score", positive - negative)),
        "duration": str(row_value(row, "catalyst_durability", "unknown_duration")),
        "directness": str(row_value(row, "catalyst_directness", "unknown_directness")),
        "surprise_proxy": str(row_value(row, "catalyst_surprise_proxy", "unknown_surprise")),
        "priced_in_risk": str(row_value(row, "catalyst_priced_in_state", "proxy_only")),
        "confidence": 0.8 if int(row_value(row, "content_prediction_assignment_certified_flag", 0)) == 1 else 0.3,
        "authority_scope": "assignment_certified",
    }


def interpret_price_acceptance(row: pd.Series) -> dict[str, object]:
    state = str(row_value(row, "price_acceptance_state", row_value(row, "price_chart_acceptance_state", "")))
    if "strong" in state or "confirmed" in state:
        direction = "positive"
    elif "fragile" in state or "fades" in state or "weak" in state:
        direction = "negative"
    elif "extended" in state or "mixed" in state:
        direction = "mixed"
    else:
        direction = "neutral"
    return {
        "primary_driver": "price_acceptance",
        "direction": direction,
        "economic_channel": state or "price_acceptance_unknown",
        "magnitude_proxy": safe_float(row_value(row, "price_acceptance_score", 0.0)),
        "duration": "entry_window_proxy",
        "directness": "direct_price",
        "surprise_proxy": "not_measured",
        "priced_in_risk": str(row_value(row, "catalyst_absorption_state", "absorption_unproven")),
        "confidence": 0.75 if int(row_value(row, "theme_price_assignment_certified_flag", 0)) == 1 else 0.25,
        "authority_scope": "assignment_certified",
    }


def interpret_theme_leadership(row: pd.Series) -> dict[str, object]:
    state = str(row_value(row, "leadership_lifecycle_state", row_value(row, "theme_leadership_state", "")))
    if any(token in state for token in ["persistent", "emerging", "strong", "participating"]):
        direction = "positive"
    elif any(token in state for token in ["fading", "late", "weak"]):
        direction = "negative"
    elif "neutral" in state or "mixed" in state:
        direction = "mixed"
    else:
        direction = "neutral"
    return {
        "primary_driver": "theme_leadership",
        "direction": direction,
        "economic_channel": state or "theme_leadership_unknown",
        "magnitude_proxy": safe_float(
            row_value(row, "leadership_strength", row_value(row, "theme_breadth20_prev", 0.0))
        ),
        "duration": str(row_value(row, "leadership_phase_strength", "unknown_phase_strength")),
        "directness": "theme_flow",
        "surprise_proxy": "not_measured",
        "priced_in_risk": str(row_value(row, "leadership_timing_risk", "unknown_timing_risk")),
        "confidence": 0.75 if int(row_value(row, "theme_price_assignment_certified_flag", 0)) == 1 else 0.25,
        "authority_scope": "assignment_certified",
    }


def interpret_market_context(row: pd.Series) -> dict[str, object]:
    state = str(row_value(row, "market_state", row_value(row, "multi_day_market_state_v4", "")))
    if "risk_on" in state or "constructive" in state:
        direction = "positive"
    elif "risk_off" in state or "stress" in state:
        direction = "negative"
    elif "mixed" in state or "rotation" in state:
        direction = "mixed"
    else:
        direction = "neutral"
    return {
        "primary_driver": "market_context",
        "direction": direction,
        "economic_channel": state or "market_context_unknown",
        "magnitude_proxy": safe_float(row_value(row, "broad_market_score", 0.0)),
        "duration": "multi_day",
        "directness": "market_beta",
        "surprise_proxy": "not_measured",
        "priced_in_risk": "not_measured",
        "confidence": 0.7 if int(row_value(row, "theme_price_assignment_certified_flag", 0)) == 1 else 0.25,
        "authority_scope": "assignment_certified",
    }


def interpret_macro_context(row: pd.Series) -> dict[str, object]:
    return {
        "primary_driver": "macro_context",
        "direction": "diagnostic_only",
        "economic_channel": str(row_value(row, "macro_overall_state", "macro_not_assignment_certified")),
        "magnitude_proxy": safe_float(row_value(row, "macro_series_available_count", 0.0)),
        "duration": "asof_provisional",
        "directness": "macro_transmission",
        "surprise_proxy": "not_latest_vintage_certified",
        "priced_in_risk": "diagnostic_only",
        "confidence": 0.35 if int(row_value(row, "macro_context_available_for_diagnostic_flag", 0)) == 1 else 0.1,
        "authority_scope": "diagnostic_only",
    }


def interpret_portfolio_capacity(row: pd.Series) -> dict[str, object]:
    same_entry = int(row_value(row, "same_entry_candidate_count", 0))
    active_relation = int(row_value(row, "active_relation_count", 0))
    if same_entry >= 8 or active_relation >= 3:
        direction = "negative"
    elif same_entry >= 5 or active_relation >= 2:
        direction = "mixed"
    else:
        direction = "positive"
    return {
        "primary_driver": "portfolio_capacity",
        "direction": direction,
        "economic_channel": str(row_value(row, "portfolio_capacity_state", "capacity_unknown")),
        "magnitude_proxy": float(same_entry + active_relation),
        "duration": "current_slot_window",
        "directness": "portfolio_constraint",
        "surprise_proxy": "not_applicable",
        "priced_in_risk": "not_applicable",
        "confidence": 0.8 if int(row_value(row, "portfolio_capacity_assignment_certified_flag", 0)) == 1 else 0.25,
        "authority_scope": "assignment_certified",
    }


def build_contract_integrity_audit(
    stack: pd.DataFrame,
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    edges: pd.DataFrame,
    bundles: pd.DataFrame,
    slot: pd.DataFrame,
) -> pd.DataFrame:
    outputs = {
        "evidence_objects": evidence,
        "economic_interpretation_objects": interpretations,
        "state_graph_edges": edges,
        "candidate_context_bundles": bundles,
        "slot_decision_explanations": slot,
    }
    forbidden_columns = sorted(
        {
            f"{name}:{col}"
            for name, frame in outputs.items()
            for col in frame.columns
            if col in FORBIDDEN_OBJECT_COLUMNS
        }
    )
    rows = [
        gate(
            "five_layer_artifacts_present",
            all(len(frame) > 0 for frame in outputs.values()),
            "; ".join(f"{name}={len(frame)}" for name, frame in outputs.items()),
            "all five object layers must have rows",
        ),
        gate(
            "bundle_row_count_matches_candidates",
            len(bundles) == len(stack),
            f"bundles={len(bundles)}; candidates={len(stack)}",
            "one bundle per candidate lifecycle",
        ),
        gate(
            "slot_explanation_row_count_matches_candidates",
            len(slot) == len(stack),
            f"slot_explanations={len(slot)}; candidates={len(stack)}",
            "one slot explanation per candidate lifecycle",
        ),
        gate(
            "object_ids_unique",
            evidence["evidence_object_id"].is_unique
            and interpretations["interpretation_object_id"].is_unique
            and edges["state_graph_edge_id"].is_unique
            and bundles["candidate_context_bundle_id"].is_unique
            and slot["slot_decision_explanation_id"].is_unique,
            "object ids checked across five layers",
            "all object ids unique inside each layer",
        ),
        gate(
            "no_outcome_columns_in_object_contracts",
            len(forbidden_columns) == 0,
            "|".join(forbidden_columns) if forbidden_columns else "none",
            "PnL/outcome columns excluded from object contracts",
        ),
        gate(
            "macro_edges_are_diagnostic_only",
            edges.loc[edges["from_node"].eq("macro_context"), "eligible_for_slot_assignment_flag"].sum() == 0
            and edges.loc[edges["from_node"].eq("macro_context"), "authority_scope"].eq("diagnostic_only").all(),
            "macro edges assignment eligible count="
            f"{int(edges.loc[edges['from_node'].eq('macro_context'), 'eligible_for_slot_assignment_flag'].sum())}",
            "macro context cannot grant slot authority until certified",
        ),
        gate(
            "missing_sources_not_used_as_negative",
            int(evidence["missing_source_used_as_negative_flag"].sum()) == 0
            and int(bundles["forbidden_flags_sum"].sum()) == 0,
            f"evidence_missing_negative_sum={int(evidence['missing_source_used_as_negative_flag'].sum())}; "
            f"bundle_forbidden_sum={int(bundles['forbidden_flags_sum'].sum())}",
            "missing source cannot become a negative signal",
        ),
        gate(
            "no_strategy_promotion",
            True,
            "no PnL simulation or allocation rule promotion was run",
            "context contracts only",
        ),
    ]
    return pd.DataFrame(rows)


def build_decision(
    stack: pd.DataFrame,
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    edges: pd.DataFrame,
    bundles: pd.DataFrame,
    slot: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task688",
                "verdict": "CONTEXT_OBJECT_CONTRACTS_BUILT_NO_TRADING_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "candidate_count": int(len(stack)),
                "evidence_object_count": int(len(evidence)),
                "economic_interpretation_object_count": int(len(interpretations)),
                "state_graph_edge_count": int(len(edges)),
                "candidate_context_bundle_count": int(len(bundles)),
                "slot_decision_explanation_count": int(len(slot)),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Five-layer context object contract created before any new return test.",
                "next_action": "Review object quality by layer, then improve economic interpretation and edges before another allocation backtest.",
            }
        ]
    )


def build_pass_fail(audit: pd.DataFrame) -> pd.DataFrame:
    return audit.copy()


def write_outputs(
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    edges: pd.DataFrame,
    bundles: pd.DataFrame,
    slot: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task688_evidence_objects.csv": evidence,
        "task688_economic_interpretation_objects.csv": interpretations,
        "task688_state_graph_edges.csv": edges,
        "task688_candidate_context_bundles.csv": bundles,
        "task688_slot_decision_explanations.csv": slot,
        "task688_contract_integrity_audit.csv": audit,
        "task_688_decision.csv": decision,
        "task_688_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK688_DIR / name, index=False)
    (TASK688_DIR / "task_688_context_object_contracts.md").write_text(
        render_report(evidence, interpretations, edges, bundles, slot, audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK688_DIR, TASK688_DIR / "artifact_manifest.csv")


def render_report(
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    edges: pd.DataFrame,
    bundles: pd.DataFrame,
    slot: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    evidence_summary = evidence.groupby(["evidence_type", "authority_scope", "source_quality"], dropna=False).size()
    edge_summary = edges.groupby(["from_node", "to_node", "edge_type", "authority_scope"], dropna=False).size()
    role_summary = slot.groupby(["candidate_role"], dropna=False).size()
    return f"""# Task688 Context Object Contracts

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: candidates {int(d["candidate_count"])}, evidence objects {int(d["evidence_object_count"])}, interpretation objects {int(d["economic_interpretation_object_count"])}, state edges {int(d["state_graph_edge_count"])}, bundles {int(d["candidate_context_bundle_count"])}, slot explanations {int(d["slot_decision_explanation_count"])}.
- What changed: created the five-layer context contract before any new return test.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Input is Task684 interaction stack keyed by `lifecycle_id`, `symbol`, `entry_ts`, `theme_id`, and `split_name`. This task creates no inferred lifecycle match and no new source fallback.

### Exact join keys

- Evidence, interpretation, edge, bundle, and slot explanation objects all retain `lifecycle_id`.
- Candidate-level bundle and slot explanation are one row per `lifecycle_id`.
- Macro remains diagnostic-only and cannot grant slot authority.

### Leakage audit

- Object contracts exclude PnL/outcome columns.
- All object layers set outcome/future/label usage flags to zero.
- This task does not run a backtest, compare returns, or promote a strategy.

### Five-layer contract

1. Evidence object: stores source facts and assignment authority.
2. Economic interpretation object: translates evidence into direction, magnitude proxy, duration, directness, surprise proxy, priced-in risk, and confidence.
3. State graph edge: records reinforcing, offsetting, prerequisite, diagnostic, or sizing-modifier relationships.
4. Candidate context bundle: combines ex-ante objects per lifecycle and marks missing/diagnostic/pending evidence.
5. Slot decision explanation: explains candidate role, slot claim, risk basis, and replacement hurdle without using outcomes.

### Evidence summary

{t678.markdown_table(evidence_summary.reset_index(name="row_count"))}

### Edge summary

{t678.markdown_table(edge_summary.reset_index(name="row_count"))}

### Slot role summary

{t678.markdown_table(role_summary.reset_index(name="row_count"))}

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- The object contract now makes weak layers visible instead of hiding them inside one ranking score.
- Economic interpretation still uses existing proxy fields; contract size, customer quality, backlog conversion, expectation surprise, and true priced-in analysis remain improvement targets.
- Microstructure is present only as pending evidence and is not eligible for slot assignment.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Upgrade economic interpretation content quality.
- Upgrade state graph edge logic by sector and driver.
- Add certified microstructure when raw feature builder is ready.
- Only after those changes, rerun allocation/backtest.

## No-Background Decision-Maker Report

- What happened: we stopped tuning returns and built the missing reasoning structure.
- Why it matters: now each candidate has a paper trail: evidence, meaning, relationship, bundle, and slot explanation.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: inspect which layer is weak before changing any trading rule.

## Artifact Manifest

- Inputs: `docs/reports/task_684_interaction_context_prediction_stack/task684_interaction_stack_panel.csv`.
- Outputs: evidence objects, economic interpretation objects, state graph edges, candidate bundles, slot explanations, integrity audit, decision, pass/fail, manifest.
- Row counts: evidence {len(evidence)}, interpretations {len(interpretations)}, edges {len(edges)}, bundles {len(bundles)}, slot explanations {len(slot)}.
- Validation commands: `python src/backtest/build_task688_context_object_contracts.py`; `python -m unittest tests.test_task688_context_object_contracts`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def identity(row: pd.Series) -> dict[str, object]:
    return {col: row_value(row, col, "") for col in IDENTITY_COLUMNS}


def object_id(row: pd.Series, suffix: str) -> str:
    lifecycle_id = str(row_value(row, "lifecycle_id", row_value(row, "candidate_row_id", "unknown_lifecycle")))
    clean_suffix = suffix.replace(" ", "_").replace("|", "_")
    return f"{lifecycle_id}|{clean_suffix}"


def row_value(row: pd.Series, column: object, default: object = "") -> object:
    if not column or column not in row.index:
        return default
    value = row[column]
    if pd.isna(value):
        return default
    return value


def first_nonempty(row: pd.Series, columns: list[str]) -> object:
    for col in columns:
        value = row_value(row, col, "")
        if str(value):
            return value
    return ""


def sum_int_values(row: pd.Series, columns: list[str]) -> int:
    total = 0
    for col in columns:
        total += int(float(row_value(row, col, 0) or 0))
    return total


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def strongest_company_channel(row: pd.Series) -> str:
    channels = [
        ("contract_customer", "positive_contract_customer_count"),
        ("backlog_order", "positive_backlog_order_count"),
        ("guidance_up", "positive_guidance_up_count"),
        ("margin_supply_combo", "positive_margin_supply_combo_count"),
        ("dilution_financing", "negative_dilution_financing_count"),
        ("regulation_sanction_tariff", "negative_regulation_sanction_tariff_count"),
        ("ceo_ir_disappointment", "negative_ceo_ir_disappointment_count"),
        ("insider_sell", "negative_insider_sell_count"),
        ("earnings_margin_damage", "negative_earnings_margin_damage_count"),
    ]
    scored = [(name, int(row_value(row, col, 0) or 0)) for name, col in channels]
    best = max(scored, key=lambda item: item[1])
    return best[0] if best[1] > 0 else "no_explicit_catalyst"


def relation_between(left_direction: object, right_direction: object) -> str:
    left = str(left_direction)
    right = str(right_direction)
    if left == "positive" and right == "positive":
        return "reinforcing"
    if left == "negative" and right == "negative":
        return "reinforcing_negative"
    if {left, right} == {"positive", "negative"}:
        return "offsetting"
    if "mixed" in {left, right}:
        return "confirmation_required"
    return "prerequisite_unproven"


def relation_from_state(state: object) -> str:
    text = str(state)
    if "reinforcing" in text:
        return "reinforcing"
    if "pressure" in text or "conflict" in text:
        return "offsetting"
    if "mixed" in text or "needs_confirmation" in text:
        return "confirmation_required"
    return "prerequisite_unproven"


def build_missing_evidence_flags(row: pd.Series) -> str:
    flags = []
    if int(row_value(row, "macro_assignment_certified_flag", 0)) == 0:
        flags.append("macro_assignment_certification_missing")
    if str(row_value(row, "microstructure_state_v4", "")).lower() == "microstructure_not_available":
        flags.append("microstructure_feature_missing")
    if str(row_value(row, "catalyst_surprise_proxy", "not_measured")) in {"not_measured", "unknown_surprise"}:
        flags.append("expectation_surprise_proxy_weak")
    if str(row_value(row, "catalyst_priced_in_state", "proxy_only")) in {"proxy_only", "mixed_pricing_proxy"}:
        flags.append("priced_in_analysis_proxy_only")
    return "|".join(flags) if flags else "no_material_missing_flags"


def build_primary_context_summary(row: pd.Series) -> str:
    parts = [
        f"company={row_value(row, 'company_catalyst_state', 'unknown_company')}",
        f"price={row_value(row, 'price_chart_acceptance_state', 'unknown_price')}",
        f"theme={row_value(row, 'leadership_lifecycle_state', 'unknown_theme')}",
        f"relation={row_value(row, 'relation_transmission_state', row_value(row, 'mechanism_relation_state', 'unknown_relation'))}",
        f"capacity={row_value(row, 'portfolio_capacity_state', 'unknown_capacity')}",
    ]
    return "|".join(str(part) for part in parts)


def classify_candidate_role(row: pd.Series, ready: bool) -> str:
    if not ready:
        return "research_only"
    action = str(row_value(row, "candidate_action_family", ""))
    setup = str(row_value(row, "setup_quality_bucket", ""))
    if "STRENGTH_HOLD" in action or setup == "high_quality_setup":
        return "priority_candidate"
    if "CONFIRMATION" in action or setup in {"medium_quality_setup", "uncertain_setup"}:
        return "confirmation_required_candidate"
    if "BLOCK" in action or setup == "fragile_setup":
        return "research_only"
    return "normal_candidate"


def build_slot_claim_basis(row: pd.Series) -> str:
    return "|".join(
        [
            f"setup={row_value(row, 'setup_quality_bucket', 'unknown_setup')}",
            f"catalyst={row_value(row, 'catalyst_path_type', 'unknown_catalyst')}",
            f"price={row_value(row, 'price_chart_acceptance_state', 'unknown_price')}",
            f"theme={row_value(row, 'leadership_lifecycle_state', 'unknown_theme')}",
            f"relation={row_value(row, 'relation_transmission_state', row_value(row, 'mechanism_relation_state', 'unknown_relation'))}",
        ]
    )


def build_slot_risk_basis(row: pd.Series) -> str:
    return "|".join(
        [
            f"capacity={row_value(row, 'portfolio_capacity_state', 'unknown_capacity')}",
            f"same_entry_candidates={int(row_value(row, 'same_entry_candidate_count', 0))}",
            f"active_relations={int(row_value(row, 'active_relation_count', 0))}",
            f"risk={row_value(row, 'proxy_risk_context', 'unknown_risk')}",
            f"microstructure={row_value(row, 'microstructure_state', row_value(row, 'microstructure_state_v4', 'unknown_microstructure'))}",
        ]
    )


def build_do_not_trade_reason(row: pd.Series, bundle: pd.Series) -> str:
    reasons = []
    if int(row_value(row, "allocation_assignment_ready_flag", 0)) == 0:
        reasons.append("allocation_not_assignment_ready")
    if int(bundle["slot_eligible_evidence_count"]) < 5:
        reasons.append("insufficient_slot_eligible_evidence")
    if int(bundle["assignment_eligible_edge_count"]) < 4:
        reasons.append("insufficient_assignment_eligible_edges")
    if int(bundle["forbidden_flags_sum"]) > 0:
        reasons.append("forbidden_source_flag_present")
    if not reasons:
        reasons.append("research_only_by_context_role")
    return "|".join(reasons)


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
    args = parser.parse_args()
    build_task688_program(task684_dir=args.task684_dir)
    print(f"[Task688] wrote {TASK688_DIR}")


if __name__ == "__main__":
    main()
