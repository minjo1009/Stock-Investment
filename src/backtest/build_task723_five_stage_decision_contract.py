from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK722_PANEL = Path("docs/reports/task_722_source_attached_review_packets/task722_source_attached_packet_panel.csv")
TASK723_DIR = Path("docs/reports/task_723_five_stage_decision_contract")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
NO_ACTION_REASON = "five_stage_decision_contract_only;not_buy_sell_or_sizing_instruction"
FORBIDDEN_TOKENS = [
    "future_return",
    "net_return",
    "realized_outcome",
    "top50",
    "winner",
    "loser",
    "future_price",
    "post_event",
    "backtest_target",
    "selection_result",
    "costed_return",
]


def build_task723(
    *,
    task722_path: Path = TASK722_PANEL,
    out_dir: Path = TASK723_DIR,
) -> dict[str, pd.DataFrame]:
    source = pd.read_csv(task722_path)
    evidence = build_evidence_objects(source)
    interpretations = build_economic_interpretation_objects(source, evidence)
    edges = build_relation_edge_objects(source, evidence, interpretations)
    bundles = build_candidate_context_bundles(source, evidence, interpretations, edges)
    slots = build_slot_judgment_objects(source, bundles)
    queue = build_manual_review_queue(source, evidence, interpretations, bundles, slots)
    stage_contract = build_stage_contract()
    leakage = build_leakage_guardrail([evidence, interpretations, edges, bundles, slots, queue])
    governance = build_governance_audit(evidence, interpretations, edges, bundles, slots, queue, leakage)
    decision = build_decision_frame(source, queue)
    pass_fail = build_pass_fail_matrix(evidence, interpretations, edges, bundles, slots, queue, leakage, governance)
    outputs = {
        "task723_stage_contract.csv": stage_contract,
        "task723_evidence_objects.csv": evidence,
        "task723_economic_interpretation_objects.csv": interpretations,
        "task723_relation_edge_objects.csv": edges,
        "task723_candidate_context_bundles.csv": bundles,
        "task723_slot_judgment_objects.csv": slots,
        "task723_manual_review_queue.csv": queue,
        "task723_leakage_guardrail.csv": leakage,
        "task723_governance_audit.csv": governance,
        "task_723_decision.csv": decision,
        "task_723_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "stage_contract": stage_contract,
        "evidence": evidence,
        "interpretations": interpretations,
        "edges": edges,
        "bundles": bundles,
        "slots": slots,
        "queue": queue,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_evidence_objects(source: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in source.iterrows():
        evidence_id = f"evidence::{row['lifecycle_id']}"
        rows.append(
            {
                **key_values(row),
                "evidence_id": evidence_id,
                "event_id": row.get("best_event_id_for_review", ""),
                "event_title": row.get("best_event_title_for_review", ""),
                "source_lane": row.get("best_source_lane_for_review", ""),
                "source_url": row.get("best_source_url_for_review", ""),
                "source_text_certified_flag": int(row.get("best_event_certified_flag", 0)),
                "raw_text_path": row.get("best_raw_text_path_for_review", ""),
                "evidence_span": row.get("best_evidence_span_for_review", ""),
                "authority_state": evidence_authority_state(row),
                "source_noise_type": row.get("source_noise_type", ""),
                "source_strength_state": row.get("source_strength_state", ""),
                "evidence_timestamp": row.get("best_event_timestamp_for_review", ""),
                "event_priority_reason": row.get("event_priority_reason", ""),
                "aggregate_event_count": int(row.get("aggregate_event_count", row.get("source_linked_event_count", 0))),
                "object_layer": "evidence_object",
                "assignment_used_flag": 0,
                "outcome_used_for_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_economic_interpretation_objects(source: pd.DataFrame, evidence: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in source.iterrows():
        lifecycle_id = row["lifecycle_id"]
        rows.append(
            {
                **key_values(row),
                "interpretation_id": f"interpretation::{lifecycle_id}",
                "evidence_id": f"evidence::{lifecycle_id}",
                "cashflow_state": cashflow_state(row),
                "customer_state": customer_state(row),
                "backlog_state": backlog_state(row),
                "guidance_state": guidance_state(row),
                "margin_state": margin_state(row),
                "financing_state": financing_state(row),
                "novelty_state": novelty_state(row),
                "priced_in_state": priced_in_state(row),
                "economic_path_state": row.get("economic_path_state", ""),
                "company_specificity_state": row.get("company_specificity_state", ""),
                "missing_interpretation_reason": missing_interpretation_reason(row),
                "interpretation_review_state": interpretation_review_state(row),
                "object_layer": "economic_interpretation_object",
                "assignment_used_flag": 0,
                "outcome_used_for_assignment_flag": 0,
            }
        )
    out = pd.DataFrame(rows)
    assert set(out["evidence_id"]).issubset(set(evidence["evidence_id"]))
    return out


def build_relation_edge_objects(source: pd.DataFrame, evidence: pd.DataFrame, interpretations: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in source.iterrows():
        lifecycle_id = row["lifecycle_id"]
        evidence_id = f"evidence::{lifecycle_id}"
        interpretation_id = f"interpretation::{lifecycle_id}"
        bundle_id = f"bundle::{lifecycle_id}"
        slot_id = f"slot::{lifecycle_id}"
        rows.extend(
            [
                edge_row(row, "evidence_to_interpretation", evidence_id, interpretation_id, evidence_to_interpretation_edge(row)),
                edge_row(row, "interpretation_to_price_absorption", interpretation_id, bundle_id, interpretation_to_price_edge(row)),
                edge_row(row, "interpretation_to_slot_prerequisite", interpretation_id, slot_id, interpretation_to_slot_edge(row)),
                edge_row(row, "source_noise_to_review_queue", evidence_id, bundle_id, noise_to_queue_edge(row)),
            ]
        )
    out = pd.DataFrame(rows)
    valid_from = set(evidence["evidence_id"]) | set(interpretations["interpretation_id"])
    assert set(out["from_object_id"]).issubset(valid_from)
    return out


def build_candidate_context_bundles(
    source: pd.DataFrame,
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    edges: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    edge_groups = edges.groupby("lifecycle_id")["edge_id"].apply(lambda values: "|".join(values.astype(str))).to_dict()
    for _, row in source.iterrows():
        lifecycle_id = row["lifecycle_id"]
        weakest = weakest_layer(row)
        rows.append(
            {
                **key_values(row),
                "bundle_id": f"bundle::{lifecycle_id}",
                "evidence_object_ids": f"evidence::{lifecycle_id}",
                "interpretation_object_ids": f"interpretation::{lifecycle_id}",
                "relation_edge_ids": edge_groups.get(lifecycle_id, ""),
                "weakest_layer": weakest,
                "missing_evidence": row.get("missing_source_reason", row.get("source_missing_evidence", "")),
                "review_queue": review_queue(row),
                "bundle_state": bundle_state(row, weakest),
                "manual_review_required_flag": 1,
                "object_layer": "candidate_context_bundle",
                "assignment_used_flag": 0,
                "outcome_used_for_assignment_flag": 0,
            }
        )
    out = pd.DataFrame(rows)
    assert set(out["evidence_object_ids"]).issubset(set(evidence["evidence_id"]))
    assert set(out["interpretation_object_ids"]).issubset(set(interpretations["interpretation_id"]))
    return out


def build_slot_judgment_objects(source: pd.DataFrame, bundles: pd.DataFrame) -> pd.DataFrame:
    work = source.copy()
    work["cohort_id"] = work["split_name"].astype(str) + "::" + work["entry_ts"].astype(str)
    work["same_timestamp_rank"] = work.groupby("cohort_id")["review_priority_rank"].rank(method="first").astype(int)
    rows = []
    for _, row in work.iterrows():
        lifecycle_id = row["lifecycle_id"]
        claim_state = slot_claim_state(row)
        hurdle_state = slot_hurdle_state(row)
        rows.append(
            {
                **key_values(row),
                "slot_id": f"slot::{lifecycle_id}",
                "bundle_id": f"bundle::{lifecycle_id}",
                "cohort_id": row["cohort_id"],
                "same_timestamp_rank": int(row["same_timestamp_rank"]),
                "slot_claim_state": claim_state,
                "slot_hurdle_state": hurdle_state,
                "slot_review_state": slot_review_state(row, claim_state, hurdle_state),
                "slot_explanation": slot_explanation(row, claim_state, hurdle_state),
                "slot_missing_reason": slot_missing_reason(row),
                "cohort_only_flag": 1,
                "object_layer": "slot_judgment_object",
                "assignment_used_flag": 0,
                "outcome_used_for_assignment_flag": 0,
            }
        )
    out = pd.DataFrame(rows)
    assert set(out["bundle_id"]).issubset(set(bundles["bundle_id"]))
    return out


def build_manual_review_queue(
    source: pd.DataFrame,
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    bundles: pd.DataFrame,
    slots: pd.DataFrame,
) -> pd.DataFrame:
    merged = source[KEYS + ["review_priority_rank", "source_review_readiness_state"]].merge(
        evidence[KEYS + ["evidence_id", "event_title", "source_lane", "authority_state", "source_noise_type", "evidence_span"]],
        on=KEYS,
        how="left",
        validate="one_to_one",
    )
    merged = merged.merge(
        interpretations[KEYS + ["interpretation_id", "cashflow_state", "financing_state", "economic_path_state", "interpretation_review_state"]],
        on=KEYS,
        how="left",
        validate="one_to_one",
    )
    merged = merged.merge(
        bundles[KEYS + ["bundle_id", "weakest_layer", "missing_evidence", "review_queue", "bundle_state"]],
        on=KEYS,
        how="left",
        validate="one_to_one",
    )
    merged = merged.merge(
        slots[KEYS + ["slot_id", "cohort_id", "same_timestamp_rank", "slot_claim_state", "slot_hurdle_state", "slot_review_state", "slot_explanation"]],
        on=KEYS,
        how="left",
        validate="one_to_one",
    )
    merged["queue_priority"] = merged["review_queue"].map(
        {
            "queue_1_cashflow_packet_review": 1,
            "queue_2_semantic_enrichment_review": 2,
            "queue_3_noise_taxonomy_qa": 3,
        }
    )
    merged["manual_review_question"] = merged.apply(manual_review_question, axis=1)
    merged["reviewer_decision"] = "manual_review_pending"
    merged["strategy_acceptance_status"] = "NOT_ACCEPTED"
    merged["real_capital_status"] = "FORBIDDEN"
    return merged.sort_values(["queue_priority", "review_priority_rank", "entry_ts", "symbol"]).reset_index(drop=True)


def build_stage_contract() -> pd.DataFrame:
    rows = [
        ("evidence_object", "source facts and provenance", "source/raw/evidence/certification/noise authority", "future outcomes; returns; winner labels", "source attached"),
        ("economic_interpretation_object", "economic meaning of evidence", "cashflow/customer/backlog/guidance/margin/financing/novelty/priced-in states", "PnL-derived strength", "interpretation attached"),
        ("relation_edge_object", "relationships between objects", "reinforcing/offsetting/prerequisite/blocker/diagnostic", "edge to future outcome", "edge graph attached"),
        ("candidate_context_bundle", "candidate-level context packet", "object ids/weakest layer/missing evidence/review queue", "global ranking from future performance", "bundle attached"),
        ("slot_judgment_object", "same timestamp slot explanation", "cohort id/same timestamp rank/slot claim/hurdle/explanation", "top winner or realized loser labels", "cohort-only slot attached"),
    ]
    return pd.DataFrame(
        [
            {
                "stage_name": stage,
                "purpose": purpose,
                "required_contract": required,
                "forbidden_contract": forbidden,
                "task723_acceptance_gate": gate,
            }
            for stage, purpose, required, forbidden, gate in rows
        ]
    )


def evidence_authority_state(row: pd.Series) -> str:
    if int(row.get("best_event_certified_flag", 0)) <= 0:
        return "evidence_authority_blocked_uncertified"
    if row.get("source_review_readiness_state") == "source_review_ready_cashflow_packet":
        return "evidence_authority_manual_review_ready"
    if row.get("source_review_readiness_state") == "source_review_noise_triage_required":
        return "evidence_authority_noise_qa_only"
    return "evidence_authority_semantic_review_required"


def cashflow_state(row: pd.Series) -> str:
    count = int(row.get("cashflow_signal_count", 0))
    if count <= 0:
        return "cashflow_not_established"
    if int(row.get("stock_specific_causal_link_count", 0)) > 0:
        return "cashflow_company_specific_signal"
    return "cashflow_signal_without_company_specificity"


def customer_state(row: pd.Series) -> str:
    if int(row.get("named_customer_or_counterparty_count", 0)) > 0:
        return "customer_or_counterparty_named"
    return "customer_or_counterparty_not_named"


def backlog_state(row: pd.Series) -> str:
    if int(row.get("revenue_or_backlog_signal_count", 0)) > 0:
        return "revenue_or_backlog_signal_present"
    return "revenue_or_backlog_not_established"


def guidance_state(row: pd.Series) -> str:
    if int(row.get("guidance_or_margin_signal_count", 0)) > 0:
        return "guidance_or_margin_signal_present"
    return "guidance_or_margin_not_established"


def margin_state(row: pd.Series) -> str:
    if int(row.get("guidance_or_margin_signal_count", 0)) > 0:
        return "margin_bridge_possible_from_source"
    return "margin_bridge_not_established"


def financing_state(row: pd.Series) -> str:
    noise = str(row.get("source_noise_type", ""))
    if "form4" in noise or "ownership" in noise or "insider" in noise:
        return "financing_or_ownership_noise_present"
    if "financing" in str(row.get("financing_pressure_state", "")).lower():
        return "financing_pressure_context_present"
    return "financing_pressure_not_established"


def novelty_state(row: pd.Series) -> str:
    reason = str(row.get("event_priority_reason", ""))
    if "certified_source_text" in reason and "cashflow" in reason:
        return "novelty_review_required_source_supported"
    return "novelty_not_proven"


def priced_in_state(row: pd.Series) -> str:
    state = str(row.get("price_absorption_state", ""))
    if not state or state == "nan":
        return "priced_in_state_missing"
    if "pending" in state or "unabsorbed" in state:
        return "priced_in_absorption_pending"
    if "confirmed" in state or "accept" in state:
        return "priced_in_absorption_confirmed"
    return "priced_in_state_review_required"


def missing_interpretation_reason(row: pd.Series) -> str:
    missing = []
    if cashflow_state(row) == "cashflow_not_established":
        missing.append("cashflow_path")
    if customer_state(row) == "customer_or_counterparty_not_named":
        missing.append("named_customer")
    if int(row.get("stock_specific_causal_link_count", 0)) <= 0:
        missing.append("company_specific_causality")
    if novelty_state(row) == "novelty_not_proven":
        missing.append("novelty")
    return ";".join(missing) if missing else "none_for_interpretation_review"


def interpretation_review_state(row: pd.Series) -> str:
    readiness = row.get("source_review_readiness_state")
    if readiness == "source_review_ready_cashflow_packet":
        return "interpretation_review_cashflow_first"
    if readiness == "source_review_semantic_enrichment_required":
        return "interpretation_review_parser_gap"
    return "interpretation_review_noise_qa_only"


def edge_row(row: pd.Series, relation_name: str, from_id: str, to_id: str, edge_type: str) -> dict[str, object]:
    lifecycle_id = row["lifecycle_id"]
    return {
        **key_values(row),
        "edge_id": f"edge::{relation_name}::{lifecycle_id}",
        "relation_name": relation_name,
        "from_object_id": from_id,
        "to_object_id": to_id,
        "edge_type": edge_type,
        "support_strength": edge_support_strength(row, edge_type),
        "confidence_state": edge_confidence_state(row, edge_type),
        "review_required_flag": 1,
        "object_layer": "relation_edge_object",
        "assignment_used_flag": 0,
        "outcome_used_for_assignment_flag": 0,
    }


def evidence_to_interpretation_edge(row: pd.Series) -> str:
    if row.get("source_review_readiness_state") == "source_review_ready_cashflow_packet":
        return "prerequisite"
    if row.get("source_review_readiness_state") == "source_review_noise_triage_required":
        return "diagnostic"
    return "prerequisite"


def interpretation_to_price_edge(row: pd.Series) -> str:
    if "absorption_pending" in priced_in_state(row):
        return "prerequisite"
    if row.get("source_review_readiness_state") == "source_review_noise_triage_required":
        return "diagnostic"
    return "reinforcing" if cashflow_state(row) != "cashflow_not_established" else "prerequisite"


def interpretation_to_slot_edge(row: pd.Series) -> str:
    if row.get("source_review_readiness_state") == "source_review_noise_triage_required":
        return "blocker"
    if missing_interpretation_reason(row) == "none_for_interpretation_review":
        return "reinforcing"
    return "prerequisite"


def noise_to_queue_edge(row: pd.Series) -> str:
    if row.get("source_review_readiness_state") == "source_review_noise_triage_required":
        return "diagnostic"
    return "offsetting" if "noise" in str(row.get("source_noise_type", "")) else "reinforcing"


def edge_support_strength(row: pd.Series, edge_type: str) -> str:
    if edge_type == "reinforcing" and int(row.get("cashflow_signal_count", 0)) > 0:
        return "support_strength_medium_source_supported"
    if edge_type in {"blocker", "diagnostic"}:
        return "support_strength_noise_or_review_limited"
    return "support_strength_pending_manual_review"


def edge_confidence_state(row: pd.Series, edge_type: str) -> str:
    if int(row.get("best_event_certified_flag", 0)) <= 0:
        return "confidence_blocked_uncertified"
    if edge_type == "reinforcing" and int(row.get("stock_specific_causal_link_count", 0)) > 0:
        return "confidence_medium_company_specific"
    return "confidence_low_until_manual_review"


def weakest_layer(row: pd.Series) -> str:
    readiness = row.get("source_review_readiness_state")
    if readiness == "source_review_noise_triage_required":
        return "evidence_object_noise_dominant"
    if readiness == "source_review_semantic_enrichment_required":
        return "economic_interpretation_semantic_gap"
    if "pending" in priced_in_state(row):
        return "relation_edge_price_absorption_pending"
    if missing_interpretation_reason(row) != "none_for_interpretation_review":
        return "economic_interpretation_missing_fields"
    return "slot_judgment_manual_review_needed"


def review_queue(row: pd.Series) -> str:
    readiness = row.get("source_review_readiness_state")
    if readiness == "source_review_ready_cashflow_packet":
        return "queue_1_cashflow_packet_review"
    if readiness == "source_review_semantic_enrichment_required":
        return "queue_2_semantic_enrichment_review"
    return "queue_3_noise_taxonomy_qa"


def bundle_state(row: pd.Series, weakest: str) -> str:
    if weakest == "evidence_object_noise_dominant":
        return "bundle_noise_qa_only"
    if weakest == "economic_interpretation_semantic_gap":
        return "bundle_semantic_enrichment_required"
    if weakest == "relation_edge_price_absorption_pending":
        return "bundle_price_absorption_review_required"
    return "bundle_manual_review_ready"


def slot_claim_state(row: pd.Series) -> str:
    if row.get("source_review_readiness_state") == "source_review_ready_cashflow_packet":
        return "slot_claim_reviewable_not_actionable"
    if row.get("source_review_readiness_state") == "source_review_semantic_enrichment_required":
        return "slot_claim_blocked_by_semantic_gap"
    return "slot_claim_noise_qa_only"


def slot_hurdle_state(row: pd.Series) -> str:
    if row.get("source_review_readiness_state") == "source_review_ready_cashflow_packet":
        return "slot_hurdle_requires_manual_cashflow_validation"
    if row.get("source_review_readiness_state") == "source_review_semantic_enrichment_required":
        return "slot_hurdle_requires_parser_or_manual_semantic_repair"
    return "slot_hurdle_requires_noise_taxonomy_confirmation"


def slot_review_state(row: pd.Series, claim_state: str, hurdle_state: str) -> str:
    if claim_state == "slot_claim_reviewable_not_actionable":
        return "slot_review_queue_1_pending"
    if "semantic" in hurdle_state:
        return "slot_review_queue_2_pending"
    return "slot_review_queue_3_qa_pending"


def slot_explanation(row: pd.Series, claim_state: str, hurdle_state: str) -> str:
    return f"{claim_state};{hurdle_state};cohort_only_same_timestamp_no_outcome_rank"


def slot_missing_reason(row: pd.Series) -> str:
    if row.get("source_review_readiness_state") == "source_review_ready_cashflow_packet":
        return "manual_confirmation_not_completed"
    if row.get("source_review_readiness_state") == "source_review_semantic_enrichment_required":
        return "semantic_enrichment_not_completed"
    return "economic_source_not_established_noise_qa_only"


def manual_review_question(row: pd.Series) -> str:
    queue = row["review_queue"]
    if queue == "queue_1_cashflow_packet_review":
        return "does_raw_source_support_real_cashflow_customer_backlog_guidance_or_margin_path_without_overhang_conflict"
    if queue == "queue_2_semantic_enrichment_review":
        return "did_parser_miss_an_economic_path_or_is_source_economically_empty"
    return "is_this_only_form4_ownership_or_insider_noise_and_should_remain_qa_only"


def key_values(row: pd.Series) -> dict[str, object]:
    return {key: row[key] for key in KEYS}


def build_leakage_guardrail(frames: list[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for index, frame in enumerate(frames):
        columns = [str(col) for col in frame.columns]
        forbidden_hits = sorted({col for col in columns for token in FORBIDDEN_TOKENS if token in col.lower()})
        assignment_sum = int(frame["assignment_used_flag"].sum()) if "assignment_used_flag" in frame.columns else 0
        outcome_sum = int(frame["outcome_used_for_assignment_flag"].sum()) if "outcome_used_for_assignment_flag" in frame.columns else 0
        rows.append(
            gate(
                f"frame_{index}_no_forbidden_or_assignment_leakage",
                not forbidden_hits and assignment_sum == 0 and outcome_sum == 0,
                f"forbidden={','.join(forbidden_hits) if forbidden_hits else 'none'}; assignment={assignment_sum}; outcome={outcome_sum}",
                "no forbidden fields; assignment=0; outcome=0",
            )
        )
    return pd.DataFrame(rows)


def build_governance_audit(
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    edges: pd.DataFrame,
    bundles: pd.DataFrame,
    slots: pd.DataFrame,
    queue: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    n = len(evidence)
    return pd.DataFrame(
        [
            gate("evidence_objects_present", n == 345, f"rows={n}", "345"),
            gate("interpretation_objects_present", len(interpretations) == n, f"rows={len(interpretations)}", "match evidence"),
            gate("relation_edges_present", len(edges) == n * 4, f"rows={len(edges)}", "4 per evidence object"),
            gate("candidate_bundles_present", len(bundles) == n, f"rows={len(bundles)}", "match evidence"),
            gate("slot_judgments_present", len(slots) == n, f"rows={len(slots)}", "match evidence"),
            gate("manual_queue_present", len(queue) == n, f"rows={len(queue)}", "match evidence"),
            gate("all_object_ids_linked", linked_ids_pass(evidence, interpretations, edges, bundles, slots), "linked", "linked"),
            gate(
                "queue_priority_order_present",
                set(queue["queue_priority"]).issubset({1, 2, 3}) and set(queue["queue_priority"]).issuperset({2, 3}),
                f"priorities={sorted(queue['queue_priority'].unique())}",
                "subset of 1,2,3; 2 and 3 present; queue1 may be zero after parser repair",
            ),
            gate("slot_cohort_only", int(slots["cohort_only_flag"].min()) == 1, "cohort_only=1", "cohort_only=1"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
        ]
    )


def linked_ids_pass(
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    edges: pd.DataFrame,
    bundles: pd.DataFrame,
    slots: pd.DataFrame,
) -> bool:
    return (
        set(interpretations["evidence_id"]).issubset(set(evidence["evidence_id"]))
        and set(bundles["evidence_object_ids"]).issubset(set(evidence["evidence_id"]))
        and set(bundles["interpretation_object_ids"]).issubset(set(interpretations["interpretation_id"]))
        and set(slots["bundle_id"]).issubset(set(bundles["bundle_id"]))
        and set(edges["from_object_id"]).issubset(set(evidence["evidence_id"]) | set(interpretations["interpretation_id"]))
    )


def build_decision_frame(source: pd.DataFrame, queue: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task723",
                "verdict": "FIVE_STAGE_DECISION_CONTRACT_BUILT_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "candidate_count": len(source),
                "queue_1_cashflow_count": int((queue["queue_priority"] == 1).sum()),
                "queue_2_semantic_count": int((queue["queue_priority"] == 2).sum()),
                "queue_3_noise_count": int((queue["queue_priority"] == 3).sum()),
                "trading_promotion_pass_flag": 0,
                "next_action": "Queue1 is empty after source parser repair; repair queue2 semantic gaps and queue3 ownership/noise taxonomy before any eligibility rule or backtest.",
            }
        ]
    )


def build_pass_fail_matrix(
    evidence: pd.DataFrame,
    interpretations: pd.DataFrame,
    edges: pd.DataFrame,
    bundles: pd.DataFrame,
    slots: pd.DataFrame,
    queue: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("five_stage_artifacts_present", all(len(frame) > 0 for frame in [evidence, interpretations, edges, bundles, slots]), "all present", "all present"),
            gate("one_object_per_candidate_except_edges", len(evidence) == len(interpretations) == len(bundles) == len(slots) == len(queue), "matched", "matched"),
            gate("relation_edges_four_per_candidate", len(edges) == len(evidence) * 4, f"edges={len(edges)}", "4 per candidate"),
            gate("weakest_layer_populated", bundles["weakest_layer"].astype(str).str.len().gt(0).all(), "complete", "complete"),
            gate("manual_review_queue_populated", queue["review_queue"].astype(str).str.len().gt(0).all(), "complete", "complete"),
            gate("slot_judgment_cohort_only", int(slots["cohort_only_flag"].min()) == 1, "cohort_only=1", "cohort_only=1"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
            gate("strategy_not_accepted", True, "NOT_ACCEPTED", "NOT_ACCEPTED"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


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
    report = f"""# Task723 Five Stage Decision Contract

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: candidates {decision.iloc[0]['candidate_count']}, queue1 {decision.iloc[0]['queue_1_cashflow_count']}, queue2 {decision.iloc[0]['queue_2_semantic_count']}, queue3 {decision.iloc[0]['queue_3_noise_count']}.
- What changed: Task722 source-attached packets are converted into five linked object layers: evidence, interpretation, relation, bundle, and slot judgment.
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

### Data source and source readiness

Input is Task722 source-attached review packet panel. Task723 does not add a data source, infer lifecycle matches, or use missing evidence as a negative signal.

### Exact join keys

All objects retain `lifecycle_id`, `symbol`, `theme_id`, `entry_ts`, and `split_name`. Slot judgment uses same `split_name` plus same `entry_ts` cohort only.

### Leakage audit

Forbidden future outcome, return, winner, loser, top50, future price, post-event, backtest target, and selection result fields are blocked from all Task723 objects. No action output is produced.

### Five-stage contract

1. Evidence object: source facts, raw text path, evidence span, certification, source noise, and authority.
2. Economic interpretation object: cashflow, customer, backlog, guidance, margin, financing, novelty, priced-in, and economic path states.
3. Relation edge object: evidence-to-interpretation, interpretation-to-price, interpretation-to-slot, and source-noise-to-queue edges.
4. Candidate context bundle: object ids, weakest layer, missing evidence, bundle state, and manual review queue.
5. Slot judgment object: same-timestamp cohort, slot claim, hurdle, review state, and explanation.

### Split/OOS metrics

Not applicable. This task is not a backtest.

### Failure decomposition

Queue 1 is the first review target because it has source-supported cashflow evidence. Queue 2 checks parser or semantic gaps. Queue 3 is noise taxonomy QA only.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Queue 1 manual packet review is not complete.
- Queue 2 semantic enrichment is not complete.
- Slot judgment remains explanatory only, not allocation authority.

## No-Background Decision-Maker Report

- What happened: the five-step structure is now fixed in code and artifacts.
- Why it matters: each candidate can be inspected by weak layer before any trading rule is changed.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: if queue1 is empty after parser repair, fix remaining semantic/noise parser gaps before any backtest.

## Artifact Manifest

- Inputs: `{TASK722_PANEL}`.
- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation command: `python -m unittest tests.test_task723_five_stage_decision_contract`.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / "task_723_five_stage_decision_contract.md").write_text(report, encoding="utf-8")
    manifest = out_dir / "artifact_manifest.csv"
    if manifest.exists():
        manifest.unlink()
    write_manifest(out_dir, manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task723 five-stage decision contract.")
    parser.add_argument("--task722", type=Path, default=TASK722_PANEL)
    parser.add_argument("--out-dir", type=Path, default=TASK723_DIR)
    args = parser.parse_args()
    build_task723(task722_path=args.task722, out_dir=args.out_dir)
    print("[Task723] wrote five-stage decision contract")


if __name__ == "__main__":
    main()
