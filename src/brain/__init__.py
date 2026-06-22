"""Trader Brain runtime contract package."""

from brain.contracts import (
    BrainLayer,
    EconomicMeaning,
    FrontendReadModel,
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
    assert_no_assignment_leakage,
)
from brain.meaning_adapter import task742_row_to_economic_meaning, task742_rows_to_economic_meanings
from brain.relation_adapter import (
    assert_relation_edge_thesis_chain,
    build_meaning_relation_edge,
    build_thesis_bundle_from_relation_edge,
)
from brain.policy_adapter import assert_thesis_policy_action_review_chain, build_policy_action_review_from_thesis
from brain.runtime_decision_adapter import (
    assert_policy_action_runtime_review_chain,
    build_runtime_decision_from_policy_action_review,
)
from brain.frontend_read_model_adapter import (
    assert_runtime_frontend_read_model_review_chain,
    build_frontend_read_model_from_runtime_decision_review,
)
from brain.runtime_catalog import build_frontend_read_model_from_paper_ops_catalog
from brain.runtime_catalog import PAPER_OPS_RUNTIME_CONTRACT_VERSION
from brain.runtime_authority import (
    BrokerSubmitIdempotencyPlan,
    LatestRuntimeAuthorityDecision,
    REQUIRED_KILL_SWITCH_LEVELS,
    REQUIRED_PAPER_ELIGIBILITY_EVIDENCE,
    RuntimeAuthorityCandidate,
    RuntimeAuthorityEvidence,
    RuntimeAuthorityGate,
    RuntimeAuthorityResult,
    RuntimeLineageHashes,
    RuntimeSnapshotRefs,
    authorize_latest_runtime_decision,
    validate_runtime_authority,
)
from brain.diagnostic_orchestration import (
    DiagnosticHeartbeatCadence,
    DiagnosticOrchestrationDecision,
    DiagnosticOrchestrationStatus,
    L0L6DiagnosticRuntimeState,
    build_diagnostic_orchestration_decision,
    build_idempotency_key,
)

__all__ = [
    "BrainLayer",
    "EconomicMeaning",
    "FrontendReadModel",
    "MeaningDirection",
    "MeaningRelationEdge",
    "PolicyAction",
    "PolicyActionType",
    "RelationEdgeType",
    "RuntimeDecision",
    "RuntimeGate",
    "SizingDirective",
    "SourceGap",
    "ThesisBundle",
    "ThesisInvalidationState",
    "assert_no_assignment_leakage",
    "assert_relation_edge_thesis_chain",
    "assert_thesis_policy_action_review_chain",
    "assert_policy_action_runtime_review_chain",
    "assert_runtime_frontend_read_model_review_chain",
    "build_meaning_relation_edge",
    "build_policy_action_review_from_thesis",
    "build_frontend_read_model_from_runtime_decision_review",
    "build_runtime_decision_from_policy_action_review",
    "build_thesis_bundle_from_relation_edge",
    "task742_row_to_economic_meaning",
    "task742_rows_to_economic_meanings",
    "build_frontend_read_model_from_paper_ops_catalog",
    "PAPER_OPS_RUNTIME_CONTRACT_VERSION",
    "BrokerSubmitIdempotencyPlan",
    "LatestRuntimeAuthorityDecision",
    "REQUIRED_KILL_SWITCH_LEVELS",
    "REQUIRED_PAPER_ELIGIBILITY_EVIDENCE",
    "RuntimeAuthorityCandidate",
    "RuntimeAuthorityEvidence",
    "RuntimeAuthorityGate",
    "RuntimeAuthorityResult",
    "RuntimeLineageHashes",
    "RuntimeSnapshotRefs",
    "authorize_latest_runtime_decision",
    "validate_runtime_authority",
    "DiagnosticHeartbeatCadence",
    "DiagnosticOrchestrationDecision",
    "DiagnosticOrchestrationStatus",
    "L0L6DiagnosticRuntimeState",
    "build_diagnostic_orchestration_decision",
    "build_idempotency_key",
]
