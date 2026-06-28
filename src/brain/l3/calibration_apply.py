from __future__ import annotations

from src.brain.l3.calibration_contracts import L3CalibrationAuditBucket
from src.brain.l3.contracts import L3CalibrationStatus, L3Confidence


def confidence_from_calibration_bucket(
    *,
    raw_band: str,
    static_weight: float,
    bucket: L3CalibrationAuditBucket | None,
    calibration_version: str,
) -> L3Confidence:
    if bucket is None or bucket.calibration_status != L3CalibrationStatus.CALIBRATED:
        return L3Confidence(
            raw_band=raw_band,
            static_weight=static_weight,
            calibrated_probability=None,
            calibration_status=L3CalibrationStatus.INSUFFICIENT_SAMPLE,
            calibration_version=calibration_version,
            sample_size=0 if bucket is None else bucket.sample_size,
            brier_score=None,
            calibration_error=None,
        )
    return L3Confidence(
        raw_band=raw_band,
        static_weight=static_weight,
        calibrated_probability=bucket.calibrated_probability,
        calibration_status=L3CalibrationStatus.CALIBRATED,
        calibration_version=calibration_version,
        sample_size=bucket.sample_size,
        brier_score=bucket.brier_score,
        calibration_error=bucket.calibration_error,
    )
