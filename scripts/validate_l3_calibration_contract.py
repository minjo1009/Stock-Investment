from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.contracts import MeaningDirection
from src.brain.l3.adapters.task742_rule_adapter import adapt_task742_rule_inputs_to_l3_meaning
from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod, L3OutcomeBridgeRow
from src.brain.l3.calibration_builder import build_calibration_outcome_row, build_calibration_outcome_row_from_bridge
from src.brain.l3.calibration_contracts import L3OutcomeLabel


def validate() -> list[str]:
    errors: list[str] = []
    meaning = adapt_task742_rule_inputs_to_l3_meaning(
        {
            "source_circuit": "financial_results_guidance",
            "source_event_id": "event-1",
            "symbol": "AAPL",
            "tradable_after_dt": "2026-06-01T10:00:00Z",
        },
        primitive={"guidance_raise_flag": 1, "margin_language_flag": 1},
    )
    if meaning.direction != MeaningDirection.SUPPORTIVE:
        errors.append("Task742 migrated rule did not produce supportive guidance meaning")
    bridge = L3OutcomeBridgeRow(
        bridge_id="bridge-1",
        meaning_id=meaning.meaning_id,
        l2_primitive_id="",
        source_receipt_id="",
        outcome_source_table="unit.lifecycle_outcomes",
        outcome_bridge_key="life-1",
        lifecycle_id="life-1",
        continuation_id="",
        bridge_method=L3OutcomeBridgeMethod.MANIFEST_BACKED_EXACT_KEY,
        bridge_source_artifact="unit_manifest.csv",
        inferred_matching_used_flag=0,
    )
    bridged_row = build_calibration_outcome_row_from_bridge(
        meaning,
        bridge,
        {
            "lifecycle_id": "life-1",
            "entry_ts": "2026-06-01T10:00:00Z",
            "exit_ts": "2026-06-06T10:00:00Z",
            "return_from_entry": "0.04",
            "positive_return_flag": "1",
            "canonical_split": "OOS",
        },
    )
    if bridged_row.outcome_bridge_key != "life-1" or bridged_row.outcome_label != L3OutcomeLabel.POSITIVE:
        errors.append("manifest-backed bridge did not produce explicit lifecycle calibration row")
    try:
        build_calibration_outcome_row_from_bridge(
            meaning,
            bridge,
            {
                "lifecycle_id": "life-2",
                "return_from_entry": "0.04",
                "positive_return_flag": "1",
                "canonical_split": "OOS",
            },
        )
    except ValueError:
        pass
    else:
        errors.append("calibration builder allowed mismatched lifecycle bridge key")
    try:
        build_calibration_outcome_row(
            meaning,
            {
                "outcome_bridge_key": "AAPL:2026-06-01",
                "split_name": "OOS_2026Q2",
                "outcome_source_table": "unsafe.proximity_join",
                "outcome_metric": "FORWARD_RETURN_PCT",
                "outcome_label": "POSITIVE",
                "label_source": "unsafe",
                "inferred_matching_used_flag": 1,
            },
        )
    except ValueError:
        pass
    else:
        errors.append("calibration builder allowed inferred matching")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_CALIBRATION_ERROR] {error}")
        sys.exit(1)
    print("[L3_CALIBRATION_OK]")


if __name__ == "__main__":
    main()
