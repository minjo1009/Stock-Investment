from __future__ import annotations

import sys

from news_ops_to_backtest_common import (
    ARTIFACT_DIR,
    ROOT,
    DISCOVERY_NEWS_SOURCE_FAMILIES,
    connect_readonly,
    ensure_dirs,
    fail_if_errors,
    safety_payload,
    write_csv,
    write_json,
)

SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brain.contracts import (
    EconomicMeaning,
    MeaningDirection,
    MeaningRelationEdge,
    PolicyAction,
    PolicyActionType,
    RelationEdgeType,
    RuntimeDecision,
    RuntimeGate,
    SizingDirective,
    SourceGap,
    ThesisBundle,
    ThesisInvalidationState,
)


def _exercise_review_chain() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    meaning = EconomicMeaning(
        meaning_id="meaning:scope-d:discovery",
        asof_ts="2026-06-24T00:00:00Z",
        symbol="AAPL",
        direction=MeaningDirection.UNKNOWN,
        confidence=0.0,
        uncertainty_flags=("DISCOVERY_SOURCE_NOT_AUTHORITY",),
        source_packet_ids=("news_event_l1:gdelt:sample",),
        relation_readiness="BLOCKED_DISCOVERY_ONLY",
    )
    edge = MeaningRelationEdge(
        relation_edge_id="edge:scope-d:blocked",
        symbol=meaning.symbol,
        decision_asof_ts=meaning.asof_ts,
        meaning_ids=(meaning.meaning_id,),
        edge_type=RelationEdgeType.BLOCKED_NOT_READY,
        confidence_floor=0.0,
        source_packet_ids=meaning.source_packet_ids,
        blocker_flags=("DISCOVERY_SOURCE_NOT_AUTHORITY",),
        source_gaps=(SourceGap.MISSING_RAW_SOURCE,),
    )
    thesis = ThesisBundle(
        thesis_id="thesis:scope-d:blocked",
        trade_spec_id="trade-spec:scope-d:blocked",
        symbol=meaning.symbol,
        decision_asof_ts=meaning.asof_ts,
        meaning_ids=edge.meaning_ids,
        catalyst_summary="Discovery-only news requires authority confirmation.",
        invalidation_state=ThesisInvalidationState.UNKNOWN,
        blocker_flags=edge.blocker_flags,
        source_gaps=edge.source_gaps,
    )
    action = PolicyAction(
        action_id="action:scope-d:skip",
        policy_id="review-only-policy",
        thesis_id=thesis.thesis_id,
        action=PolicyActionType.SKIP,
        sizing_directive=SizingDirective.NONE,
        reason_codes=("DISCOVERY_SOURCE_NOT_AUTHORITY", "L5_REVIEW_ONLY"),
        evidence_paths=("data/artifacts/task_3883_news_ops_scope_a_g_implementation/scope_c_l0_l1_storage_matrix.csv",),
    )
    runtime = RuntimeDecision(
        runtime_decision_id="runtime:scope-d:blocked",
        policy_action_id=action.action_id,
        gate=RuntimeGate.BLOCKED,
        blocker_flags=("DISCOVERY_SOURCE_NOT_AUTHORITY", "L6_REVIEW_ONLY_NOT_PAPER_ELIGIBLE"),
        validation_refs=("python scripts/validate_l1_l6_consumption_contract.py",),
        paper_order_intent_allowed=False,
        live_order_allowed=False,
    )
    rows.append(
        {
            "meaning_id": meaning.meaning_id,
            "relation_edge_id": edge.relation_edge_id,
            "thesis_id": thesis.thesis_id,
            "action_id": action.action_id,
            "runtime_decision_id": runtime.runtime_decision_id,
            "runtime_gate": runtime.gate,
            "paper_order_intent_allowed": int(runtime.paper_order_intent_allowed),
            "live_order_allowed": int(runtime.live_order_allowed),
        }
    )
    return rows


def main() -> None:
    ensure_dirs()
    errors: list[str] = []
    contract_rows = _exercise_review_chain()
    con = connect_readonly()
    discovery_rows: list[dict[str, object]] = []
    try:
        for family in DISCOVERY_NEWS_SOURCE_FAMILIES:
            row = con.execute(
                """
                SELECT source_family,
                       COUNT(*) AS rows,
                       SUM(CASE WHEN promotion_status='BLOCKED' THEN 1 ELSE 0 END) AS blocked_rows,
                       SUM(CASE WHEN quality_flags_json LIKE '%non_authority_discovery_source%' THEN 1 ELSE 0 END) AS discovery_flags,
                       SUM(CASE WHEN promotion_status!='BLOCKED' THEN 1 ELSE 0 END) AS unblocked_rows
                FROM news_event_l1_evidence
                WHERE source_family=?
                GROUP BY source_family
                """,
                (family,),
            ).fetchone()
            if row is None:
                errors.append(f"missing_l1_discovery_rows:{family}")
                continue
            record = dict(row)
            discovery_rows.append(record)
            if int(record["rows"]) <= 0:
                errors.append(f"empty_l1_discovery_rows:{family}")
            if int(record["unblocked_rows"] or 0) != 0:
                errors.append(f"discovery_source_unblocked:{family}")
            if int(record["blocked_rows"] or 0) != int(record["rows"]):
                errors.append(f"discovery_source_not_all_blocked:{family}")
            if int(record["discovery_flags"] or 0) != int(record["rows"]):
                errors.append(f"discovery_source_missing_quality_flag:{family}")
    finally:
        con.close()

    write_csv(ARTIFACT_DIR / "scope_d_contract_chain.csv", contract_rows)
    write_csv(ARTIFACT_DIR / "scope_d_discovery_l1_blockers.csv", discovery_rows)
    write_json(
        ARTIFACT_DIR / "scope_d_l1_l6_consumption_validation.json",
        {"status": "PASS" if not errors else "FAIL", "errors": errors, **safety_payload()},
    )
    fail_if_errors(errors)
    print("[TASK3883_SCOPE_D_OK] l1_l6_contract=PASS discovery_sources_blocked=1 no_order_or_replay_eligibility=1")


if __name__ == "__main__":
    main()
