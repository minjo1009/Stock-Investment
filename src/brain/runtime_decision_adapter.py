"""Adapters from L5 review policy actions into L6 runtime decisions.

This adapter preserves the current repository boundary: review actions can
become shadow-only or blocked runtime decisions, but never paper-eligible or
live-order decisions.
"""

from __future__ import annotations

from brain.contracts import PolicyAction, PolicyActionType, RuntimeDecision, RuntimeGate


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return tuple(seen)


def _blockers_for_review_action(action: PolicyAction) -> tuple[str, ...]:
    blockers = list(action.reason_codes)
    blockers.append("L6_REVIEW_ONLY_NOT_PAPER_ELIGIBLE")
    if action.action == PolicyActionType.SKIP:
        blockers.append("L5_SKIP_ACTION_BLOCKED")
    return _dedupe(tuple(blockers))


def build_runtime_decision_from_policy_action_review(
    action: PolicyAction,
    validation_refs: tuple[str, ...],
    runtime_decision_id: str | None = None,
) -> RuntimeDecision:
    """Build one L6 runtime decision from an L5 review-only policy action."""

    if not validation_refs:
        raise ValueError("validation_refs is required")
    if action.creates_order_intent:
        raise ValueError("review policy action cannot create runtime order intent")
    if action.action not in (PolicyActionType.WATCH, PolicyActionType.SKIP):
        raise ValueError("review runtime adapter may only accept WATCH or SKIP")

    gate = RuntimeGate.SHADOW_ONLY if action.action == PolicyActionType.WATCH else RuntimeGate.BLOCKED
    runtime = RuntimeDecision(
        runtime_decision_id=runtime_decision_id or f"runtime-review:{action.action_id}",
        policy_action_id=action.action_id,
        gate=gate,
        blocker_flags=_blockers_for_review_action(action),
        validation_refs=validation_refs,
        paper_order_intent_allowed=False,
        live_order_allowed=False,
    )
    assert_policy_action_runtime_review_chain(action, runtime)
    return runtime


def assert_policy_action_runtime_review_chain(action: PolicyAction, runtime: RuntimeDecision) -> None:
    """Validate L5 review action to L6 runtime decision invariants."""

    if runtime.policy_action_id != action.action_id:
        raise ValueError("runtime decision must reference the supplied policy action")
    if runtime.gate == RuntimeGate.PAPER_ELIGIBLE:
        raise ValueError("review runtime adapter cannot emit PAPER_ELIGIBLE")
    if runtime.paper_order_intent_allowed:
        raise ValueError("review runtime adapter cannot allow paper order intent")
    if runtime.live_order_allowed:
        raise ValueError("review runtime adapter cannot allow live orders")
    if action.action == PolicyActionType.SKIP and runtime.gate != RuntimeGate.BLOCKED:
        raise ValueError("SKIP review actions must become BLOCKED runtime decisions")
    if action.action == PolicyActionType.WATCH and runtime.gate != RuntimeGate.SHADOW_ONLY:
        raise ValueError("WATCH review actions must become SHADOW_ONLY runtime decisions")
    if action.action not in (PolicyActionType.WATCH, PolicyActionType.SKIP):
        raise ValueError("review runtime adapter may only accept WATCH or SKIP")
