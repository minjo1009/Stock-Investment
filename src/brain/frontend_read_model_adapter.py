"""Adapters from L6 runtime decisions into L7 read-only frontend models.

This adapter only formats runtime review state for cockpit display. It does not
write catalogs, run replay, submit orders, or claim acceptance/deployment
readiness.
"""

from __future__ import annotations

from brain.contracts import FrontendReadModel, RuntimeDecision, RuntimeGate


def _display_status_for_runtime(runtime: RuntimeDecision) -> str:
    if runtime.gate == RuntimeGate.SHADOW_ONLY:
        return "review_shadow_only"
    if runtime.gate == RuntimeGate.BLOCKED:
        return "review_blocked"
    if runtime.gate == RuntimeGate.BROKER_REVIEW_REQUIRED:
        return "review_broker_required"
    raise ValueError("frontend review adapter cannot display PAPER_ELIGIBLE")


def build_frontend_read_model_from_runtime_decision_review(
    runtime: RuntimeDecision,
    *,
    read_model_id: str | None = None,
    provenance_paths: tuple[str, ...],
    source_tier: str = "brain_runtime_review",
) -> FrontendReadModel:
    """Build one read-only L7 model from an L6 review runtime decision."""

    if not provenance_paths:
        raise ValueError("provenance_paths is required")
    if runtime.gate == RuntimeGate.PAPER_ELIGIBLE:
        raise ValueError("review frontend adapter cannot display PAPER_ELIGIBLE as review state")
    if runtime.paper_order_intent_allowed:
        raise ValueError("frontend review model cannot expose paper order intent")
    if runtime.live_order_allowed:
        raise ValueError("frontend review model cannot expose live order permission")

    read_model = FrontendReadModel(
        read_model_id=read_model_id or f"read-model:{runtime.runtime_decision_id}",
        runtime_decision_id=runtime.runtime_decision_id,
        source_tier=source_tier,
        display_status=_display_status_for_runtime(runtime),
        provenance_paths=provenance_paths,
        blocker_flags=runtime.blocker_flags,
        read_only=True,
    )
    assert_runtime_frontend_read_model_review_chain(runtime, read_model)
    return read_model


def assert_runtime_frontend_read_model_review_chain(runtime: RuntimeDecision, read_model: FrontendReadModel) -> None:
    """Validate L6 runtime decision to L7 read model invariants."""

    if read_model.runtime_decision_id != runtime.runtime_decision_id:
        raise ValueError("frontend read model must reference the supplied runtime decision")
    if not read_model.read_only:
        raise ValueError("frontend read model must be read-only")
    if runtime.gate == RuntimeGate.PAPER_ELIGIBLE:
        raise ValueError("review frontend adapter cannot display PAPER_ELIGIBLE")
    if runtime.paper_order_intent_allowed:
        raise ValueError("frontend review model cannot expose paper order intent")
    if runtime.live_order_allowed:
        raise ValueError("frontend review model cannot expose live order permission")
