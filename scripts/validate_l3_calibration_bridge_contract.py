from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod, L3OutcomeBridgeRow


def validate() -> list[str]:
    errors: list[str] = []
    row = L3OutcomeBridgeRow(
        bridge_id="bridge-1",
        meaning_id="l3v2:l2-1",
        l2_primitive_id="l2-1",
        source_receipt_id="receipt-1",
        outcome_source_table="docs/reports/task_391_intraday_canonical_oos_validation/split_lifecycle_panel.csv",
        outcome_bridge_key="life-1",
        lifecycle_id="life-1",
        continuation_id="",
        bridge_method=L3OutcomeBridgeMethod.MANIFEST_BACKED_EXACT_KEY,
        bridge_source_artifact="docs/reports/task_l3_calibration_rule_migration/l3_calibration_bridge_gap_audit.csv",
        inferred_matching_used_flag=0,
    )
    if row.trade_output_flag or row.score_output_flag or row.order_intent_flag:
        errors.append("bridge row created a trade output flag")
    try:
        L3OutcomeBridgeRow(
            bridge_id="bridge-unsafe",
            meaning_id="l3v2:l2-1",
            l2_primitive_id="",
            source_receipt_id="",
            outcome_source_table="unsafe.proximity",
            outcome_bridge_key="AAPL:2026-06-01",
            lifecycle_id="",
            continuation_id="",
            bridge_method=L3OutcomeBridgeMethod.MANIFEST_BACKED_EXACT_KEY,
            bridge_source_artifact="unsafe",
            inferred_matching_used_flag=1,
        )
    except ValueError:
        pass
    else:
        errors.append("bridge contract allowed inferred matching")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_BRIDGE_ERROR] {error}")
        sys.exit(1)
    print("[L3_BRIDGE_OK]")


if __name__ == "__main__":
    main()
