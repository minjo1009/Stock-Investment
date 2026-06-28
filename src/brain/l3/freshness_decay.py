from __future__ import annotations

from pathlib import Path

from src.brain.l3.config_loader import load_simple_yaml


DEFAULT_FRESHNESS_DECAY_CONFIG = Path("configs/brain/l3_freshness_decay.yaml")


def freshness_decay(age_minutes: float, half_life_minutes: float) -> float:
    if half_life_minutes <= 0:
        raise ValueError("half_life_minutes must be positive")
    age = max(0.0, float(age_minutes))
    return max(0.0, min(1.0, 0.5 ** (age / float(half_life_minutes))))


def load_freshness_half_life_config(path: str | Path = DEFAULT_FRESHNESS_DECAY_CONFIG) -> dict[str, float]:
    raw = load_simple_yaml(path)
    config: dict[str, float] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            config[str(key)] = float(value.get("half_life_minutes", 1440))
        else:
            config[str(key)] = float(value)
    return config
