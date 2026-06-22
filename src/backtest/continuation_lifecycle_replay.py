from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

import pandas as pd


ReplayState = Literal["IDLE", "PROBE", "BUILDING", "PERSISTING", "REDUCING", "EXITED"]
_EPSILON = 1e-12


@dataclass(frozen=True)
class LifecycleRow:
    lifecycle_id: str
    trade_id: str
    signal_id: str | None
    symbol: str
    strategy_id: str | None
    session_date: str
    timestamp: pd.Timestamp | None
    sequence_in_lifecycle: int
    participation_quality_label: str
    expansion_score: float
    fragility_score: float
    confidence: float
    state_label: str
    continuation_risk_score: float
    factor_budget_allowed: bool
    exposure_allow_add: bool
    staged_gate_stage: str
    staged_add_allowed: bool
    quality_aware_policy_stage: str
    quality_aware_add_allowed: bool
    healthy_policy_label: str
    final_add_allowed: bool
    size_multiplier: float
    baseline_realized_r: float
    old_shadow_realized_r_proxy: float
    quality_aware_realized_r_proxy: float
    healthy_aggressive_realized_r_proxy: float


@dataclass(frozen=True)
class ContinuationLifecycle:
    lifecycle_id: str
    symbol: str
    session_date: str
    rows: tuple[LifecycleRow, ...]


@dataclass(frozen=True)
class ReplayTransition:
    lifecycle_id: str
    trade_id: str
    from_state: str
    to_state: str
    transition_reason: str


@dataclass(frozen=True)
class ReplayStateRow:
    lifecycle_id: str
    trade_id: str
    replay_state: str
    add_activated: bool
    size_multiplier: float
    concentration_step: float
    transition_reason: str


@dataclass(frozen=True)
class ReplayDiagnostics:
    lifecycle_rows_df: pd.DataFrame
    replay_trace_df: pd.DataFrame
    transition_matrix_df: pd.DataFrame
    lifecycle_summary_df: pd.DataFrame
    replay_state_distribution_df: pd.DataFrame
    add_activation_df: pd.DataFrame
    compounding_diagnostics_df: pd.DataFrame
    fragility_transition_df: pd.DataFrame


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if pd.isna(numeric):
        return float(default)
    return numeric


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _normalize_shadow_frame(shadow_log_df: pd.DataFrame) -> pd.DataFrame:
    if shadow_log_df.empty:
        return shadow_log_df.copy()
    frame = shadow_log_df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame["session_date"] = frame["timestamp"].dt.strftime("%Y-%m-%d")
    frame["session_date"] = frame["session_date"].fillna(frame.get("day_key", pd.Series("", index=frame.index)).astype(str))
    frame = frame.sort_values(["symbol", "session_date", "timestamp", "trade_id"], kind="stable").reset_index(drop=True)
    return frame


def build_continuation_lifecycles(shadow_log_df: pd.DataFrame) -> tuple[ContinuationLifecycle, ...]:
    frame = _normalize_shadow_frame(shadow_log_df)
    if frame.empty:
        return ()

    lifecycles: list[ContinuationLifecycle] = []
    for (symbol, session_date), group in frame.groupby(["symbol", "session_date"], dropna=False, sort=False):
        group = group.sort_values(["timestamp", "trade_id"], kind="stable").reset_index(drop=True)
        lifecycle_id = f"{symbol}|{session_date}"
        rows: list[LifecycleRow] = []
        for sequence_in_lifecycle, (_, row) in enumerate(group.iterrows(), start=1):
            rows.append(
                LifecycleRow(
                    lifecycle_id=lifecycle_id,
                    trade_id=_safe_text(row.get("trade_id"), "unknown_trade"),
                    signal_id=(_safe_text(row.get("signal_id")) or None),
                    symbol=_safe_text(row.get("symbol"), "unknown_symbol"),
                    strategy_id=(_safe_text(row.get("strategy_id")) or None),
                    session_date=_safe_text(session_date, "unknown_date"),
                    timestamp=row.get("timestamp"),
                    sequence_in_lifecycle=sequence_in_lifecycle,
                    participation_quality_label=_safe_text(row.get("participation_quality_label"), "UNKNOWN"),
                    expansion_score=_safe_float(row.get("participation_expansion_score"), 0.0),
                    fragility_score=_safe_float(row.get("participation_fragility_score"), 0.0),
                    confidence=_safe_float(row.get("participation_confidence"), 0.0),
                    state_label=_safe_text(row.get("state_label"), "UNKNOWN"),
                    continuation_risk_score=_safe_float(row.get("continuation_risk_score"), 0.0),
                    factor_budget_allowed=not _safe_bool(row.get("factor_exposure_violated")),
                    exposure_allow_add=_safe_bool(row.get("allow_add")),
                    staged_gate_stage=_safe_text(row.get("staged_gate_stage"), "UNKNOWN"),
                    staged_add_allowed=_safe_bool(row.get("staged_add_allowed")),
                    quality_aware_policy_stage=_safe_text(row.get("quality_aware_policy_stage"), "UNKNOWN"),
                    quality_aware_add_allowed=_safe_bool(row.get("quality_aware_add_allowed")),
                    healthy_policy_label=_safe_text(row.get("healthy_aggressive_policy_label"), "UNKNOWN"),
                    final_add_allowed=_safe_bool(row.get("healthy_aggressive_final_add_allowed")),
                    size_multiplier=_safe_float(row.get("healthy_aggressive_final_size_multiplier"), 0.0),
                    baseline_realized_r=_safe_float(row.get("baseline_realized_R"), 0.0),
                    old_shadow_realized_r_proxy=_safe_float(row.get("shadow_realized_R_proxy"), 0.0),
                    quality_aware_realized_r_proxy=_safe_float(row.get("quality_aware_realized_R_proxy"), 0.0),
                    healthy_aggressive_realized_r_proxy=_safe_float(row.get("healthy_aggressive_realized_R_proxy"), 0.0),
                )
            )
        lifecycles.append(
            ContinuationLifecycle(
                lifecycle_id=lifecycle_id,
                symbol=_safe_text(symbol, "unknown_symbol"),
                session_date=_safe_text(session_date, "unknown_date"),
                rows=tuple(rows),
            )
        )
    return tuple(lifecycles)


def _add_path_open(row: LifecycleRow) -> bool:
    return (
        row.factor_budget_allowed
        and row.exposure_allow_add
        and row.staged_gate_stage == "stage_2_add"
        and row.staged_add_allowed
        and row.final_add_allowed
    )


def _next_state(
    current_state: ReplayState,
    row: LifecycleRow,
    previous_size: float,
) -> tuple[ReplayState, str]:
    is_fragile = row.participation_quality_label == "FRAGILE_CROWDING"
    is_dislocation = row.state_label == "DISLOCATION"
    is_live_position = row.size_multiplier > _EPSILON
    size_increased_vs_prev = row.size_multiplier > previous_size + _EPSILON
    size_reduced_vs_prev = row.size_multiplier < previous_size - _EPSILON
    add_path_open = _add_path_open(row)

    if row.size_multiplier <= _EPSILON:
        return "EXITED", "size_to_zero"
    if is_dislocation:
        return "EXITED", "dislocation_exit"

    if current_state in {"IDLE", "EXITED"}:
        if is_live_position and not is_fragile:
            return "PROBE", "initial_live_probe"
        if is_live_position and is_fragile:
            return "REDUCING", "fragile_start_reducing"
        return "EXITED", "no_live_position"

    if is_fragile:
        if is_live_position:
            return "REDUCING", "fragility_increase"
        return "EXITED", "fragile_exit"

    if add_path_open:
        if current_state == "PROBE":
            return "BUILDING", "probe_to_build"
        if current_state in {"PERSISTING", "REDUCING"} and size_increased_vs_prev:
            return "BUILDING", "add_path_reopened"
        if current_state == "BUILDING" and not size_reduced_vs_prev:
            return "BUILDING", "building_continues"

    if size_reduced_vs_prev and is_live_position:
        return "REDUCING", "size_step_down"

    if current_state == "PROBE":
        return "PERSISTING", "probe_without_add"
    if current_state == "BUILDING":
        return "PERSISTING", "build_to_persist"
    if current_state == "PERSISTING":
        return "PERSISTING", "persisting_stable"
    if current_state == "REDUCING":
        if size_increased_vs_prev and add_path_open:
            return "BUILDING", "reducing_to_build"
        return "PERSISTING", "reduction_stabilized"
    return "EXITED", "terminal"


def replay_lifecycle(lifecycle: ContinuationLifecycle) -> tuple[pd.DataFrame, pd.DataFrame]:
    replay_rows: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    current_state: ReplayState = "IDLE"
    previous_size = 0.0

    for row in lifecycle.rows:
        add_path_open = _add_path_open(row)
        is_fragile = row.participation_quality_label == "FRAGILE_CROWDING"
        is_dislocation = row.state_label == "DISLOCATION"
        is_live_position = row.size_multiplier > _EPSILON
        size_increased_vs_prev = row.size_multiplier > previous_size + _EPSILON
        size_reduced_vs_prev = row.size_multiplier < previous_size - _EPSILON
        next_state, transition_reason = _next_state(current_state, row, previous_size)
        add_activated = next_state == "BUILDING" or add_path_open
        concentration_step = row.size_multiplier - previous_size

        replay_rows.append(
            {
                "lifecycle_id": row.lifecycle_id,
                "trade_id": row.trade_id,
                "symbol": row.symbol,
                "session_date": row.session_date,
                "sequence_in_lifecycle": row.sequence_in_lifecycle,
                "participation_quality_label": row.participation_quality_label,
                "state_label": row.state_label,
                "continuation_risk_score": row.continuation_risk_score,
                "replay_state": next_state,
                "previous_replay_state": current_state,
                "add_activated": add_activated,
                "size_multiplier": row.size_multiplier,
                "concentration_step": concentration_step,
                "transition_reason": transition_reason,
                "add_path_open": add_path_open,
                "is_fragile": is_fragile,
                "is_dislocation": is_dislocation,
                "is_live_position": is_live_position,
                "size_increased_vs_prev": size_increased_vs_prev,
                "size_reduced_vs_prev": size_reduced_vs_prev,
                "baseline_realized_r": row.baseline_realized_r,
                "old_shadow_realized_r_proxy": row.old_shadow_realized_r_proxy,
                "quality_aware_realized_r_proxy": row.quality_aware_realized_r_proxy,
                "healthy_aggressive_realized_r_proxy": row.healthy_aggressive_realized_r_proxy,
            }
        )
        transitions.append(
            {
                "lifecycle_id": row.lifecycle_id,
                "trade_id": row.trade_id,
                "sequence_in_lifecycle": row.sequence_in_lifecycle,
                "from_state": current_state,
                "to_state": next_state,
                "transition_reason": transition_reason,
                "participation_quality_label": row.participation_quality_label,
                "state_label": row.state_label,
                "size_multiplier": row.size_multiplier,
                "concentration_step": concentration_step,
                "add_activated": add_activated,
            }
        )
        current_state = next_state
        previous_size = row.size_multiplier

    return pd.DataFrame(replay_rows), pd.DataFrame(transitions)


def _lifecycle_rows_dataframe(lifecycles: tuple[ContinuationLifecycle, ...]) -> pd.DataFrame:
    rows = [asdict(row) for lifecycle in lifecycles for row in lifecycle.rows]
    return pd.DataFrame(rows)


def build_transition_matrix(transition_df: pd.DataFrame) -> pd.DataFrame:
    if transition_df.empty:
        return pd.DataFrame(columns=["from_state", "to_state", "transition_count"])
    return (
        transition_df.groupby(["from_state", "to_state"], dropna=False)
        .size()
        .reset_index(name="transition_count")
        .sort_values(["from_state", "to_state"], kind="stable")
        .reset_index(drop=True)
    )


def build_replay_state_distribution(replay_trace_df: pd.DataFrame) -> pd.DataFrame:
    if replay_trace_df.empty:
        return pd.DataFrame(columns=["replay_state", "row_count", "row_share"])
    counts = replay_trace_df["replay_state"].value_counts(dropna=False).sort_index()
    total = max(int(counts.sum()), 1)
    return pd.DataFrame(
        {
            "replay_state": counts.index.astype(str),
            "row_count": counts.values,
            "row_share": [round(float(value / total), 6) for value in counts.values],
        }
    )


def build_add_activation_summary(replay_trace_df: pd.DataFrame) -> pd.DataFrame:
    if replay_trace_df.empty:
        return pd.DataFrame(columns=["bucket_type", "bucket_value", "row_count", "add_activation_count", "add_activation_rate", "avg_size_multiplier"])
    rows: list[dict[str, Any]] = []
    for bucket_type, column in (
        ("participation_quality_label", "participation_quality_label"),
        ("state_label", "state_label"),
    ):
        for bucket_value, group in replay_trace_df.groupby(column, dropna=False):
            row_count = int(len(group))
            add_count = int(group["add_activated"].fillna(False).astype(bool).sum())
            rows.append(
                {
                    "bucket_type": bucket_type,
                    "bucket_value": str(bucket_value),
                    "row_count": row_count,
                    "add_activation_count": add_count,
                    "add_activation_rate": round(float(add_count / row_count), 6) if row_count else 0.0,
                    "avg_size_multiplier": round(float(pd.to_numeric(group["size_multiplier"], errors="coerce").fillna(0.0).mean()), 6),
                }
            )
    return pd.DataFrame(rows).sort_values(["bucket_type", "bucket_value"], kind="stable").reset_index(drop=True)


def build_fragility_transition_summary(transition_df: pd.DataFrame) -> pd.DataFrame:
    if transition_df.empty:
        return pd.DataFrame(columns=["from_state", "to_state", "transition_count", "avg_size_multiplier", "avg_concentration_step"])
    fragile = transition_df[
        transition_df["participation_quality_label"].astype(str).eq("FRAGILE_CROWDING")
        & transition_df["to_state"].astype(str).isin({"REDUCING", "EXITED"})
    ].copy()
    if fragile.empty:
        return pd.DataFrame(columns=["from_state", "to_state", "transition_count", "avg_size_multiplier", "avg_concentration_step"])
    return (
        fragile.groupby(["from_state", "to_state"], dropna=False)
        .agg(
            transition_count=("trade_id", "size"),
            avg_size_multiplier=("size_multiplier", lambda values: round(float(pd.to_numeric(values, errors="coerce").fillna(0.0).mean()), 6)),
            avg_concentration_step=("concentration_step", lambda values: round(float(pd.to_numeric(values, errors="coerce").fillna(0.0).mean()), 6)),
        )
        .reset_index()
        .sort_values(["from_state", "to_state"], kind="stable")
        .reset_index(drop=True)
    )


def _lifecycle_summary(replay_trace_df: pd.DataFrame) -> pd.DataFrame:
    if replay_trace_df.empty:
        return pd.DataFrame(
            columns=[
                "lifecycle_id",
                "symbol",
                "session_date",
                "row_count",
                "start_state",
                "end_state",
                "has_probe",
                "has_building",
                "has_persisting",
                "has_reducing",
                "has_exited",
                "healthy_start",
                "fragile_start",
                "max_size_multiplier",
                "avg_size_multiplier",
                "baseline_pnl_r_sum",
                "old_shadow_pnl_proxy_sum",
                "quality_aware_pnl_proxy_sum",
                "healthy_aggressive_pnl_proxy_sum",
            ]
        )
    rows: list[dict[str, Any]] = []
    for lifecycle_id, group in replay_trace_df.groupby("lifecycle_id", dropna=False, sort=False):
        group = group.sort_values("sequence_in_lifecycle", kind="stable").reset_index(drop=True)
        rows.append(
            {
                "lifecycle_id": str(lifecycle_id),
                "symbol": str(group["symbol"].iloc[0]),
                "session_date": str(group["session_date"].iloc[0]),
                "row_count": int(len(group)),
                "start_state": str(group["replay_state"].iloc[0]),
                "end_state": str(group["replay_state"].iloc[-1]),
                "has_probe": bool(group["replay_state"].astype(str).eq("PROBE").any()),
                "has_building": bool(group["replay_state"].astype(str).eq("BUILDING").any()),
                "has_persisting": bool(group["replay_state"].astype(str).eq("PERSISTING").any()),
                "has_reducing": bool(group["replay_state"].astype(str).eq("REDUCING").any()),
                "has_exited": bool(group["replay_state"].astype(str).eq("EXITED").any()),
                "healthy_start": bool(group["participation_quality_label"].astype(str).iloc[0] == "HEALTHY_EXPANSION"),
                "fragile_start": bool(group["participation_quality_label"].astype(str).iloc[0] == "FRAGILE_CROWDING"),
                "max_size_multiplier": round(float(pd.to_numeric(group["size_multiplier"], errors="coerce").fillna(0.0).max()), 6),
                "avg_size_multiplier": round(float(pd.to_numeric(group["size_multiplier"], errors="coerce").fillna(0.0).mean()), 6),
                "baseline_pnl_r_sum": round(float(pd.to_numeric(group["baseline_realized_r"], errors="coerce").fillna(0.0).sum()), 6),
                "old_shadow_pnl_proxy_sum": round(float(pd.to_numeric(group["old_shadow_realized_r_proxy"], errors="coerce").fillna(0.0).sum()), 6),
                "quality_aware_pnl_proxy_sum": round(float(pd.to_numeric(group["quality_aware_realized_r_proxy"], errors="coerce").fillna(0.0).sum()), 6),
                "healthy_aggressive_pnl_proxy_sum": round(float(pd.to_numeric(group["healthy_aggressive_realized_r_proxy"], errors="coerce").fillna(0.0).sum()), 6),
            }
        )
    return pd.DataFrame(rows)


def build_compounding_diagnostics(
    replay_trace_df: pd.DataFrame,
    lifecycle_summary_df: pd.DataFrame,
    transition_df: pd.DataFrame,
) -> pd.DataFrame:
    if replay_trace_df.empty or lifecycle_summary_df.empty:
        return pd.DataFrame(columns=["metric_name", "metric_value"])

    lifecycle_count = int(lifecycle_summary_df["lifecycle_id"].nunique())
    avg_lifecycle_length = float(pd.to_numeric(lifecycle_summary_df["row_count"], errors="coerce").fillna(0.0).mean())

    probe_lifecycles = set(lifecycle_summary_df.loc[lifecycle_summary_df["has_probe"], "lifecycle_id"].astype(str))
    building_lifecycles = set(lifecycle_summary_df.loc[lifecycle_summary_df["has_building"], "lifecycle_id"].astype(str))
    persisting_lifecycles = set(lifecycle_summary_df.loc[lifecycle_summary_df["has_persisting"], "lifecycle_id"].astype(str))
    healthy_start_lifecycles = set(lifecycle_summary_df.loc[lifecycle_summary_df["healthy_start"], "lifecycle_id"].astype(str))
    fragile_start_lifecycles = set(lifecycle_summary_df.loc[lifecycle_summary_df["fragile_start"], "lifecycle_id"].astype(str))

    probe_to_build_rate = float(len(probe_lifecycles & building_lifecycles) / max(len(probe_lifecycles), 1))
    build_to_persist_rate = float(len(building_lifecycles & persisting_lifecycles) / max(len(building_lifecycles), 1))
    add_activation_rate = float(replay_trace_df["add_activated"].fillna(False).astype(bool).mean())
    healthy_persist_rate = float(len(healthy_start_lifecycles & persisting_lifecycles) / max(len(healthy_start_lifecycles), 1))
    fragile_collapse_candidates = lifecycle_summary_df[lifecycle_summary_df["fragile_start"]].copy()
    fragile_collapse_rate = float(
        (
            fragile_collapse_candidates["has_exited"].fillna(False).astype(bool)
            & ~fragile_collapse_candidates["has_persisting"].fillna(False).astype(bool)
        ).mean()
    ) if not fragile_collapse_candidates.empty else 0.0

    reduction_transitions = transition_df[transition_df["to_state"].astype(str) == "REDUCING"].copy()
    avg_reduction_speed = float(
        pd.to_numeric(reduction_transitions["concentration_step"], errors="coerce").fillna(0.0).abs().mean()
    ) if not reduction_transitions.empty else 0.0

    metrics: list[tuple[str, float]] = [
        ("lifecycle_count", float(lifecycle_count)),
        ("avg_lifecycle_length", avg_lifecycle_length),
        ("probe_to_build_rate", probe_to_build_rate),
        ("build_to_persist_rate", build_to_persist_rate),
        ("add_activation_rate", add_activation_rate),
        ("healthy_persist_rate", healthy_persist_rate),
        ("fragile_collapse_rate", fragile_collapse_rate),
        ("avg_reduction_speed", avg_reduction_speed),
    ]
    for replay_state, group in replay_trace_df.groupby("replay_state", dropna=False):
        metrics.append(
            (
                f"avg_size_multiplier_{str(replay_state).lower()}",
                float(pd.to_numeric(group["size_multiplier"], errors="coerce").fillna(0.0).mean()),
            )
        )
    return pd.DataFrame(
        [{"metric_name": name, "metric_value": round(value, 6)} for name, value in metrics]
    )


def run_lifecycle_replay(shadow_log_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    lifecycles = build_continuation_lifecycles(shadow_log_df)
    lifecycle_rows_df = _lifecycle_rows_dataframe(lifecycles)
    replay_frames: list[pd.DataFrame] = []
    transition_frames: list[pd.DataFrame] = []
    for lifecycle in lifecycles:
        replay_df, transition_df = replay_lifecycle(lifecycle)
        replay_frames.append(replay_df)
        transition_frames.append(transition_df)
    replay_trace_df = pd.concat(replay_frames, ignore_index=True) if replay_frames else pd.DataFrame()
    transition_df = pd.concat(transition_frames, ignore_index=True) if transition_frames else pd.DataFrame()
    transition_matrix_df = build_transition_matrix(transition_df)
    lifecycle_summary_df = _lifecycle_summary(replay_trace_df)
    return lifecycle_rows_df, replay_trace_df, transition_matrix_df, lifecycle_summary_df
