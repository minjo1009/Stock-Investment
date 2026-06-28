from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.brain.l3.config_loader import load_simple_yaml
from src.brain.l3.contracts import L3CalibrationStatus


DEFAULT_EVENT_PRIORS_CONFIG = Path("configs/brain/l3_event_type_priors.yaml")


@dataclass(frozen=True)
class L3EventPrior:
    event_type: str
    base_prior_score: float
    calibration_status: L3CalibrationStatus
    min_sample_size: int


def load_event_type_priors_config(path: str | Path = DEFAULT_EVENT_PRIORS_CONFIG) -> dict[str, L3EventPrior]:
    raw = load_simple_yaml(path)
    priors: dict[str, L3EventPrior] = {}
    for event_type, values in raw.items():
        if not isinstance(values, dict):
            continue
        priors[str(event_type)] = L3EventPrior(
            event_type=str(event_type),
            base_prior_score=max(0.0, min(1.0, float(values.get("base_prior_score", 0.0)))),
            calibration_status=L3CalibrationStatus(str(values.get("calibration_status", "NOT_CALIBRATED"))),
            min_sample_size=int(values.get("min_sample_size", 0)),
        )
    return priors


def event_prior_score(
    event_type: str,
    *,
    config: dict[str, L3EventPrior] | None = None,
    default: float = 0.50,
) -> float:
    priors = config if config is not None else load_event_type_priors_config()
    prior = priors.get(str(event_type or "").strip())
    if prior is None:
        return max(0.0, min(1.0, float(default)))
    return prior.base_prior_score
