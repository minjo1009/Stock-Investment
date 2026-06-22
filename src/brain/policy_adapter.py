"""Adapters from L4 thesis bundles into L5 review-only policy actions.

This adapter intentionally emits only review actions. It does not rank
candidates, size positions, create order intent, run replay, or mutate runtime
state.
"""

from __future__ import annotations

from brain.contracts import (
    PolicyAction,
    PolicyActionType,
    SizingDirective,
    SourceGap,
    ThesisBundle,
    ThesisInvalidationState,
)


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return tuple(seen)


def _source_gap_reason_codes(thesis: ThesisBundle) -> tuple[str, ...]:
    return tuple(f"SOURCE_GAP_{gap.value}" for gap in thesis.source_gaps if gap != SourceGap.NONE)


def _review_action_type(thesis: ThesisBundle) -> PolicyActionType:
    if thesis.outcome_used_for_assignment:
        raise ValueError("outcome fields are forbidden in L5 review action assignment")
    if SourceGap.NONE not in thesis.source_gaps:
        return PolicyActionType.SKIP
    if thesis.invalidation_state in (ThesisInvalidationState.HARD_INVALIDATED, ThesisInvalidationState.UNKNOWN):
        return PolicyActionType.SKIP
    if "RELATION_NOT_READY" in thesis.blocker_flags:
        return PolicyActionType.SKIP
    return PolicyActionType.WATCH


def build_policy_action_review_from_thesis(
    thesis: ThesisBundle,
    policy_id: str,
    evidence_paths: tuple[str, ...],
    action_id: str | None = None,
) -> PolicyAction:
    """Build one L5 review-only policy action from an L4 thesis bundle."""

    if not policy_id:
        raise ValueError("policy_id is required")
    if not evidence_paths:
        raise ValueError("evidence_paths is required")

    action_type = _review_action_type(thesis)
    reason_codes = _dedupe(
        (
            "L5_REVIEW_ONLY",
            f"THESIS_INVALIDATION_{thesis.invalidation_state.value}",
            *thesis.blocker_flags,
            *_source_gap_reason_codes(thesis),
        )
    )
    action = PolicyAction(
        action_id=action_id or f"review-action:{thesis.thesis_id}",
        policy_id=policy_id,
        thesis_id=thesis.thesis_id,
        action=action_type,
        sizing_directive=SizingDirective.NONE,
        reason_codes=reason_codes,
        evidence_paths=evidence_paths,
        creates_order_intent=False,
    )
    assert_thesis_policy_action_review_chain(thesis, action)
    return action


def assert_thesis_policy_action_review_chain(thesis: ThesisBundle, action: PolicyAction) -> None:
    """Validate L4 thesis to L5 review-action invariants."""

    if action.thesis_id != thesis.thesis_id:
        raise ValueError("policy action must reference the supplied thesis")
    if action.action not in (PolicyActionType.WATCH, PolicyActionType.SKIP):
        raise ValueError("review adapter may only emit WATCH or SKIP")
    if action.sizing_directive != SizingDirective.NONE:
        raise ValueError("review adapter cannot carry sizing directives")
    if action.creates_order_intent:
        raise ValueError("review adapter cannot create order intent")
    if thesis.outcome_used_for_assignment:
        raise ValueError("outcome fields are forbidden in thesis assignment")
