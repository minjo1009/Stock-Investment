from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.contracts import MeaningDirection
from src.brain.l3.adapters.task742_rule_adapter import adapt_task742_rule_inputs_to_l3_meaning
from src.brain.l3.task742_rules import interpret_task742_economic_context


def validate() -> list[str]:
    errors: list[str] = []
    guidance = interpret_task742_economic_context(
        {"source_circuit": "financial_results_guidance"},
        primitive={"guidance_raise_flag": 1, "margin_language_flag": 1},
    )
    if guidance.interpretation_state != "guidance_raise_with_margin_language":
        errors.append("guidance raise rule did not map to recovered interpretation state")
    if guidance.economic_direction_hint != "positive":
        errors.append("guidance raise rule did not remain positive")
    blocked = interpret_task742_economic_context(
        {"source_circuit": "form4_insider_behavior"},
        availability={"has_task740_primitive": False, "has_raw_text_path": False},
    )
    if blocked.relation_ready_tier != "not_ready":
        errors.append("hard blocker did not remain not_ready")
    meaning = adapt_task742_rule_inputs_to_l3_meaning(
        {
            "source_circuit": "credit_financing",
            "source_event_id": "event-1",
            "symbol": "AAPL",
            "tradable_after_dt": "2026-06-01T10:00:00Z",
        },
        primitive={"principal_amount": 10000000, "instrument_warrant_flag": 1},
        comparators={"principal_pct_of_market_cap": 0.05},
    )
    if meaning.direction != MeaningDirection.RISK:
        errors.append("financing dilution rule did not map to L3 RISK")
    if not meaning.diagnostic_only or meaning.trade_output_flag or meaning.score_output_flag or meaning.order_intent_flag:
        errors.append("Task742 migrated L3 meaning violated no-trade flags")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_TASK742_RULE_ERROR] {error}")
        sys.exit(1)
    print("[L3_TASK742_RULE_OK]")


if __name__ == "__main__":
    main()
