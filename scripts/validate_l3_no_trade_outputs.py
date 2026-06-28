from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.contracts import MeaningDirection
from src.brain.l3.adapters.task742_legacy_adapter import adapt_task742_row_to_l3_v2


def validate() -> list[str]:
    errors: list[str] = []
    meaning = adapt_task742_row_to_l3_v2(
        {
            "meaning_id": "m1",
            "asof_ts": "2026-06-01T10:00:00Z",
            "symbol": "AAPL",
            "lifecycle_id": "life-1",
            "economic_direction_hint": "positive",
            "confidence_band": "medium",
            "relation_readiness": "directional",
        }
    )
    if meaning.direction != MeaningDirection.SUPPORTIVE:
        errors.append("meaning direction mapping failed")
    if not meaning.diagnostic_only:
        errors.append("L3 v2 meaning must remain diagnostic_only")
    for flag_name in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
        if int(getattr(meaning, flag_name)) != 0:
            errors.append(f"{flag_name} must remain 0")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_NO_TRADE_OUTPUT_ERROR] {error}")
        sys.exit(1)
    print("[L3_NO_TRADE_OUTPUTS_OK]")


if __name__ == "__main__":
    main()
