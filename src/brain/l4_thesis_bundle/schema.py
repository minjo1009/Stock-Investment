from __future__ import annotations

TASK_ID = "TASK-4156"

SCHEMA_VERSION_BUNDLE = "l4_thesis_bundle.v0.1"
SCHEMA_VERSION_EVIDENCE = "l4_evidence_link.v0.1"
SCHEMA_VERSION_BLOCKER = "l4_blocker.v0.1"
SCHEMA_VERSION_MANIFEST = "l4_run_manifest.v0.1"

STRATEGY_STATUS = "NOT_ACCEPTED"
DEPLOYMENT_STATUS = "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"
REAL_CAPITAL = "FORBIDDEN"

ALLOWED_BUNDLE_STATUS = {"DRAFT_BLOCKED", "DRAFT_MIXED", "ASSEMBLED_FOR_REVIEW", "INVALID"}
ALLOWED_QUALITY_STATUS = {"BLOCKED", "MIXED", "REVIEW_ONLY_DIAGNOSTIC"}
ALLOWED_THESIS_TYPES = {"ENTITY_EVENT", "MACRO_CONTEXT", "SOURCE_EVENT_PROTO", "COVERAGE_GAP", "MIXED_CONTEXT"}
ALLOWED_BLOCKER_TYPES = {
    "L0_INCOMPLETE_COVERAGE",
    "L1_BLOCKED_UNKNOWN",
    "L2_FEATURE_MISSING",
    "L3_COVERAGE_GAP",
    "UNSUPPORTED_RELATION_FAMILY",
    "CONTRADICTION_NOT_SCANNED",
    "SOURCE_ACCESS_MISSING",
    "LINEAGE_MISSING",
    "MIXED_CONTEXT",
    "PROTO_EVENT_IDENTITY",
    "LOW_THESIS_SPECIFICITY",
    "LOW_EVIDENCE_LINKAGE",
    "SCHEMA_INVALID",
}

BUNDLE_REQUIRED_FIELDS = [
    "schema_version",
    "task_id",
    "bundle_id",
    "created_at_utc",
    "diagnostic_only",
    "strategy_status",
    "deployment_status",
    "real_capital",
    "no_broker_mutation",
    "no_live_order",
    "no_paper_promotion",
    "bundle_status",
    "institutional_quality_status",
    "thesis_type",
    "thesis_statement",
    "thesis_scope",
    "primary_symbols",
    "primary_entity_ids",
    "source_lanes",
    "time_window_start_utc",
    "time_window_end_utc",
    "l3_graph_ids",
    "l3_graph_families",
    "l3_event_cluster_ids",
    "event_identity_status",
    "same_event_assertion",
    "supporting_evidence_count",
    "context_evidence_count",
    "contradicting_evidence_count",
    "coverage_gap_count",
    "lineage_status",
    "source_access_status",
    "coverage_status",
    "contradiction_status",
    "relation_quality_status",
    "thesis_specificity_score",
    "evidence_linkage_score",
    "source_traceability_score",
    "contradiction_handling_score",
    "institutional_quality_score",
    "block_reasons",
    "warnings",
]

EVIDENCE_REQUIRED_FIELDS = [
    "schema_version",
    "bundle_id",
    "evidence_link_id",
    "evidence_role",
    "evidence_claim",
    "source_lane",
    "source_id",
    "source_url_or_path",
    "publisher_or_origin",
    "source_time_utc",
    "ingested_at_utc",
    "l1_packet_id",
    "l1_mapping_status",
    "l2_feature_id",
    "l2_feature_family",
    "l3_edge_id",
    "l3_graph_id",
    "l3_graph_family",
    "lineage_status",
    "source_access_status",
    "mapping_confidence",
    "evidence_quality_flag",
    "negative_evidence_allowed",
]

BLOCKER_REQUIRED_FIELDS = [
    "schema_version",
    "bundle_id",
    "blocker_id",
    "blocker_type",
    "severity",
    "source_layer",
    "related_artifact_id",
    "reason",
    "required_action",
    "is_hard_blocker",
    "negative_evidence_allowed",
]

FORBIDDEN_AUTHORITY_FIELDS = {
    "final_policy_action",
    "buy_sell_hold",
    "recommendation",
    "policy_action",
    "order_intent",
    "position_size",
    "target_weight",
    "quantity",
    "ranking",
    "rank",
    "final_score",
    "broker_order_id",
    "paper_eligible",
    "live_eligible",
    "broker_mutation",
    "strategy_accepted",
    "deployment_ready",
}
