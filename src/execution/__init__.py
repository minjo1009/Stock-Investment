"""Execution layer package."""

try:
    from src.execution.broker_submit_state import (
        PaperOrderIntentSpec,
        create_authorized_paper_order_intent,
        get_submit_state,
        mark_paper_order_intent_local_recorded,
        mark_paper_order_intent_submitting,
        mark_paper_order_intent_unknown_after_submit,
        reconcile_paper_order_intent,
    )
    from src.execution.paper_eligibility_path import (
        PaperEligibilityIntentResult,
        create_paper_intent_from_latest_authority,
    )
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from execution.broker_submit_state import (
        PaperOrderIntentSpec,
        create_authorized_paper_order_intent,
        get_submit_state,
        mark_paper_order_intent_local_recorded,
        mark_paper_order_intent_submitting,
        mark_paper_order_intent_unknown_after_submit,
        reconcile_paper_order_intent,
    )
    from execution.paper_eligibility_path import (
        PaperEligibilityIntentResult,
        create_paper_intent_from_latest_authority,
    )

__all__ = [
    "PaperOrderIntentSpec",
    "PaperEligibilityIntentResult",
    "create_authorized_paper_order_intent",
    "create_paper_intent_from_latest_authority",
    "get_submit_state",
    "mark_paper_order_intent_local_recorded",
    "mark_paper_order_intent_submitting",
    "mark_paper_order_intent_unknown_after_submit",
    "reconcile_paper_order_intent",
]
