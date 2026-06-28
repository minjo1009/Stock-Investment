from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.contracts import MeaningRelationEdgeType
from src.brain.meaning_adapter import adapt_task742_row_to_economic_meaning
from src.brain.relation_adapter import build_legacy_relation_edge


def validate() -> list[str]:
    errors: list[str] = []
    ready = adapt_task742_row_to_economic_meaning(
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
    not_ready = adapt_task742_row_to_economic_meaning(
        {
            "meaning_id": "m2",
            "asof_ts": "2026-06-01T10:00:00Z",
            "symbol": "AAPL",
            "lifecycle_id": "life-1",
            "economic_direction_hint": "neutral",
            "confidence_band": "low",
            "relation_readiness": "not_ready",
        }
    )
    edge = build_legacy_relation_edge((ready, not_ready))
    if edge.edge_type != MeaningRelationEdgeType.BLOCKED_NOT_READY:
        errors.append("legacy relation not_ready behavior changed")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_LEGACY_ERROR] {error}")
        sys.exit(1)
    print("[L3_LEGACY_OK]")


if __name__ == "__main__":
    main()
