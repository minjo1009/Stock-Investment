from __future__ import annotations

from pathlib import Path

from src.brain.l3.config_loader import load_simple_yaml


DEFAULT_RELATION_GRAPH_THRESHOLDS_CONFIG = Path("configs/brain/l3_relation_graph_thresholds.yaml")


def load_relation_graph_thresholds(path: str | Path = DEFAULT_RELATION_GRAPH_THRESHOLDS_CONFIG) -> dict[str, float]:
    raw = load_simple_yaml(path)
    return {
        "coverage_threshold": float(raw.get("coverage_threshold", 0.50)),
        "dominance_ratio": float(raw.get("dominance_ratio", 1.25)),
    }
