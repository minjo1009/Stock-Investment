from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.l3.source_gaps import L3SourceGap, classify_source_gaps
from src.l2.runtime_context import HISTORICAL_RESEARCH


def validate() -> list[str]:
    errors: list[str] = []
    critical, noncritical = classify_source_gaps(
        ("missing_raw_source", "missing_confirmation", "missing_denominator"),
        runtime_context=HISTORICAL_RESEARCH,
        source_time_certified=True,
        freshness_status="FRESH",
        authority_class="official_primary",
    )
    if L3SourceGap.MISSING_RAW_SOURCE not in critical:
        errors.append("MISSING_RAW_SOURCE must be critical")
    if L3SourceGap.MISSING_CONFIRMATION not in noncritical:
        errors.append("MISSING_CONFIRMATION must be noncritical")
    if L3SourceGap.MISSING_DENOMINATOR not in noncritical:
        errors.append("MISSING_DENOMINATOR must be noncritical")
    if len({gap.value for gap in critical + noncritical}) < 3:
        errors.append("source gap taxonomy collapsed distinct gaps")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_SOURCE_GAP_ERROR] {error}")
        sys.exit(1)
    print("[L3_SOURCE_GAP_OK]")


if __name__ == "__main__":
    main()
