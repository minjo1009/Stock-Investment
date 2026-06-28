from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.l3.confidence import build_static_l3_confidence
from src.brain.l3.contracts import L3CalibrationStatus


def validate() -> list[str]:
    errors: list[str] = []
    confidence = build_static_l3_confidence("medium")
    if confidence.static_weight != 0.60:
        errors.append("medium confidence must map to static_weight 0.60")
    if confidence.calibration_status != L3CalibrationStatus.NOT_CALIBRATED:
        errors.append("static confidence must remain NOT_CALIBRATED")
    if confidence.calibrated_probability is not None:
        errors.append("static confidence must not set calibrated_probability")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_CONFIDENCE_ERROR] {error}")
        sys.exit(1)
    print("[L3_CONFIDENCE_OK]")


if __name__ == "__main__":
    main()
