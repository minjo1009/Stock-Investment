from __future__ import annotations

from src.brain.l3.contracts import L3CalibrationStatus, L3Confidence


_STATIC_CONFIDENCE_WEIGHTS = {
    "high": 0.85,
    "medium": 0.60,
    "low": 0.35,
    "insufficient": 0.0,
    "unknown": 0.0,
    "": 0.0,
}


def normalize_confidence_band(band: str) -> str:
    return str(band or "").strip().lower()


def map_confidence_band_to_static_weight(band: str) -> float:
    """Return a static diagnostic weight, not an empirical probability."""

    return _STATIC_CONFIDENCE_WEIGHTS.get(normalize_confidence_band(band), 0.0)


def build_static_l3_confidence(
    band: str,
    *,
    calibration_version: str = "UNAVAILABLE",
) -> L3Confidence:
    return L3Confidence(
        raw_band=normalize_confidence_band(band) or "unknown",
        static_weight=map_confidence_band_to_static_weight(band),
        calibrated_probability=None,
        calibration_status=L3CalibrationStatus.NOT_CALIBRATED,
        calibration_version=calibration_version,
        sample_size=None,
        brier_score=None,
        calibration_error=None,
    )
