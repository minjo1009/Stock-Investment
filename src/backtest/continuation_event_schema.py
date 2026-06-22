from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


CANONICAL_EVENT_TYPES = (
    "SETUP_DETECTED",
    "PROBE_ENTRY",
    "ADD_ATTEMPT",
    "ADD_CONFIRMED",
    "SIZE_INCREASE",
    "PERSISTENCE_CONFIRMED",
    "FRAGILITY_WARNING",
    "REDUCTION_TRIGGER",
    "EXIT_TRIGGER",
    "INVALIDATION",
)

EVENT_SOURCE_TYPES = (
    "SOURCE_CAPTURED",
    "SESSION_DERIVED",
    "REPLAY_DERIVED",
)


@dataclass(frozen=True)
class ContinuationLifecycleEvent:
    event_id: str
    setup_id: str
    lifecycle_id: str
    parent_lifecycle_id: str | None
    symbol: str
    session_date: str
    timestamp: pd.Timestamp | None
    event_type: str
    event_source: str
    state_label: str
    participation_quality_label: str
    expansion_score: float
    fragility_score: float
    continuation_risk_score: float
    size_multiplier: float
    add_depth: int
    scale_depth: int


@dataclass(frozen=True)
class ContinuationLifecycleStateSnapshot:
    lifecycle_id: str
    timestamp: pd.Timestamp | None
    replay_state: str
    size_multiplier: float
    add_depth: int
    scale_depth: int
    persistence_depth: int
    weakening_flag: bool
    invalidated_flag: bool
