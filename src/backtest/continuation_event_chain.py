from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from src.backtest.continuation_event_identity import ContinuationEvent, build_continuation_events, events_to_frame


@dataclass(frozen=True)
class ContinuationEventChain:
    continuation_id: str
    symbol: str
    events: tuple[ContinuationEvent, ...]


@dataclass(frozen=True)
class ContinuationEvolutionSnapshot:
    continuation_id: str
    event_index: int
    replay_state: str
    participation_quality_label: str
    expansion_score: float
    fragility_score: float
    size_multiplier: float
    allow_add: bool


@dataclass(frozen=True)
class ContinuationEventChainSummary:
    continuation_id: str
    symbol: str
    session_date: str
    first_setup_timestamp: pd.Timestamp | None
    probe_timestamp: pd.Timestamp | None
    first_add_timestamp: pd.Timestamp | None
    first_scale_timestamp: pd.Timestamp | None
    first_reduce_timestamp: pd.Timestamp | None
    exit_timestamp: pd.Timestamp | None
    persistence_duration_events: int
    event_count: int
    max_size_multiplier: float
    avg_size_multiplier: float
    healthy_event_count: int
    fragile_event_count: int
    invalidated: bool
    exit_reason: str


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


def _normalize_replay_inputs(replay_trace_df: pd.DataFrame, lifecycle_rows_df: pd.DataFrame) -> pd.DataFrame:
    if replay_trace_df.empty:
        return pd.DataFrame()

    frame = replay_trace_df.copy()
    merge_columns = [
        "lifecycle_id",
        "trade_id",
        "signal_id",
        "timestamp",
        "strategy_id",
        "expansion_score",
        "fragility_score",
        "confidence",
        "factor_budget_allowed",
        "exposure_allow_add",
        "staged_gate_stage",
        "staged_add_allowed",
        "final_add_allowed",
    ]
    extra_columns = [
        column
        for column in merge_columns
        if column in lifecycle_rows_df.columns and column not in {"lifecycle_id", "trade_id"} and column not in frame.columns
    ]
    if extra_columns:
        frame = frame.merge(
            lifecycle_rows_df[["lifecycle_id", "trade_id", *extra_columns]].drop_duplicates(
                subset=["lifecycle_id", "trade_id"]
            ),
            on=["lifecycle_id", "trade_id"],
            how="left",
        )

    frame["timestamp"] = pd.to_datetime(frame.get("timestamp"), errors="coerce", utc=True)
    sort_columns = [column for column in ["lifecycle_id", "sequence_in_lifecycle", "timestamp", "trade_id"] if column in frame.columns]
    return frame.sort_values(sort_columns, kind="stable").reset_index(drop=True)


def build_continuation_event_chains(
    events: tuple[ContinuationEvent, ...],
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame,
) -> tuple[ContinuationEventChain, ...]:
    _ = replay_trace_df
    _ = lifecycle_rows_df
    if not events:
        return ()

    frame = events_to_frame(events).sort_values(["continuation_id", "event_index", "trade_id"], kind="stable")
    chains: list[ContinuationEventChain] = []
    for continuation_id, group in frame.groupby("continuation_id", dropna=False, sort=False):
        ordered_events = tuple(ContinuationEvent(**record) for record in group.to_dict(orient="records"))
        chains.append(
            ContinuationEventChain(
                continuation_id=_safe_text(continuation_id, "unknown_continuation"),
                symbol=_safe_text(group["symbol"].iloc[0], "unknown_symbol"),
                events=ordered_events,
            )
        )
    return tuple(chains)


def build_continuation_evolution_snapshots(
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame,
) -> pd.DataFrame:
    frame = _normalize_replay_inputs(replay_trace_df, lifecycle_rows_df)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "continuation_id",
                "event_index",
                "event_type",
                "replay_state",
                "participation_quality_label",
                "expansion_score",
                "fragility_score",
                "size_multiplier",
                "allow_add",
                "expansion_score_delta",
                "fragility_score_delta",
                "size_multiplier_delta",
                "participation_quality_transition",
                "replay_state_transition",
                "add_path_transition",
                "transition_reason",
            ]
        )

    events = build_continuation_events(replay_trace_df, lifecycle_rows_df)
    event_df = events_to_frame(events)
    if event_df.empty:
        return pd.DataFrame()

    event_df = event_df[["continuation_id", "event_index", "trade_id", "event_type"]]
    merged = frame.merge(
        event_df,
        left_on=["lifecycle_id", "trade_id"],
        right_on=["continuation_id", "trade_id"],
        how="left",
    )
    merged = merged.sort_values(["lifecycle_id", "sequence_in_lifecycle", "trade_id"], kind="stable").reset_index(drop=True)

    snapshots: list[dict[str, Any]] = []
    for continuation_id, group in merged.groupby("lifecycle_id", dropna=False, sort=False):
        group = group.sort_values(["sequence_in_lifecycle", "trade_id"], kind="stable").reset_index(drop=True)
        previous_row: pd.Series | None = None
        for _, row in group.iterrows():
            previous_quality = _safe_text(previous_row.get("participation_quality_label"), "NONE") if previous_row is not None else "NONE"
            previous_state = _safe_text(previous_row.get("replay_state"), "NONE") if previous_row is not None else "NONE"
            previous_add_path = _safe_bool(previous_row.get("add_path_open")) if previous_row is not None else False
            current_add_path = _safe_bool(row.get("add_path_open"))
            if previous_add_path and current_add_path:
                add_path_transition = "open_to_open"
            elif previous_add_path and not current_add_path:
                add_path_transition = "open_to_closed"
            elif not previous_add_path and current_add_path:
                add_path_transition = "closed_to_open"
            else:
                add_path_transition = "closed_to_closed"

            snapshots.append(
                {
                    "continuation_id": _safe_text(continuation_id, "unknown_continuation"),
                    "symbol": _safe_text(row.get("symbol"), "unknown_symbol"),
                    "session_date": _safe_text(row.get("session_date"), "unknown_date"),
                    "event_index": int(_safe_float(row.get("event_index"), 0.0)),
                    "trade_id": _safe_text(row.get("trade_id"), "unknown_trade"),
                    "event_type": _safe_text(row.get("event_type"), "SETUP"),
                    "timestamp": row.get("timestamp"),
                    "replay_state": _safe_text(row.get("replay_state"), "UNKNOWN"),
                    "participation_quality_label": _safe_text(row.get("participation_quality_label"), "UNKNOWN"),
                    "expansion_score": _safe_float(row.get("expansion_score"), 0.0),
                    "fragility_score": _safe_float(row.get("fragility_score"), 0.0),
                    "size_multiplier": _safe_float(row.get("size_multiplier"), 0.0),
                    "allow_add": current_add_path,
                    "expansion_score_delta": _safe_float(row.get("expansion_score"), 0.0)
                    - (_safe_float(previous_row.get("expansion_score"), 0.0) if previous_row is not None else 0.0),
                    "fragility_score_delta": _safe_float(row.get("fragility_score"), 0.0)
                    - (_safe_float(previous_row.get("fragility_score"), 0.0) if previous_row is not None else 0.0),
                    "size_multiplier_delta": _safe_float(row.get("size_multiplier"), 0.0)
                    - (_safe_float(previous_row.get("size_multiplier"), 0.0) if previous_row is not None else 0.0),
                    "participation_quality_transition": (
                        f"{previous_quality}->{_safe_text(row.get('participation_quality_label'), 'UNKNOWN')}"
                    ),
                    "replay_state_transition": f"{previous_state}->{_safe_text(row.get('replay_state'), 'UNKNOWN')}",
                    "add_path_transition": add_path_transition,
                    "transition_reason": _safe_text(row.get("transition_reason")),
                }
            )
            previous_row = row

    return pd.DataFrame(snapshots)


def summarize_event_chains(
    chains: tuple[ContinuationEventChain, ...],
    evolution_df: pd.DataFrame,
) -> pd.DataFrame:
    if not chains:
        return pd.DataFrame(
            columns=[
                "continuation_id",
                "symbol",
                "session_date",
                "first_setup_timestamp",
                "probe_timestamp",
                "first_add_timestamp",
                "first_scale_timestamp",
                "first_reduce_timestamp",
                "exit_timestamp",
                "persistence_duration_events",
                "event_count",
                "max_size_multiplier",
                "avg_size_multiplier",
                "healthy_event_count",
                "fragile_event_count",
                "invalidated",
                "exit_reason",
            ]
        )

    summaries: list[dict[str, Any]] = []
    for chain in chains:
        chain_df = evolution_df[evolution_df["continuation_id"].astype(str) == chain.continuation_id].copy()
        events_df = events_to_frame(chain.events).sort_values("event_index", kind="stable")

        def _first_timestamp(event_type: str) -> pd.Timestamp | None:
            scoped = events_df[events_df["event_type"].astype(str) == event_type]
            if scoped.empty:
                return pd.NaT
            return scoped["timestamp"].iloc[0]

        exit_rows = chain_df[chain_df["event_type"].astype(str).isin({"EXIT", "INVALIDATE"})]
        exit_reason = _safe_text(exit_rows["transition_reason"].iloc[-1], "") if not exit_rows.empty else ""
        summaries.append(
            asdict(
                ContinuationEventChainSummary(
                    continuation_id=chain.continuation_id,
                    symbol=chain.symbol,
                    session_date=_safe_text(events_df["session_date"].iloc[0], "unknown_date"),
                    first_setup_timestamp=_first_timestamp("SETUP"),
                    probe_timestamp=_first_timestamp("PROBE_ENTRY"),
                    first_add_timestamp=_first_timestamp("ADD"),
                    first_scale_timestamp=_first_timestamp("SCALE_UP"),
                    first_reduce_timestamp=_first_timestamp("REDUCE"),
                    exit_timestamp=_first_timestamp("EXIT") if pd.notna(_first_timestamp("EXIT")) else _first_timestamp("INVALIDATE"),
                    persistence_duration_events=int(events_df["event_type"].astype(str).eq("PERSIST").sum()),
                    event_count=int(len(events_df)),
                    max_size_multiplier=round(float(pd.to_numeric(chain_df["size_multiplier"], errors="coerce").fillna(0.0).max()), 6)
                    if not chain_df.empty
                    else 0.0,
                    avg_size_multiplier=round(float(pd.to_numeric(chain_df["size_multiplier"], errors="coerce").fillna(0.0).mean()), 6)
                    if not chain_df.empty
                    else 0.0,
                    healthy_event_count=int(events_df["participation_quality_label"].astype(str).eq("HEALTHY_EXPANSION").sum()),
                    fragile_event_count=int(events_df["participation_quality_label"].astype(str).eq("FRAGILE_CROWDING").sum()),
                    invalidated=bool(events_df["event_type"].astype(str).eq("INVALIDATE").any()),
                    exit_reason=exit_reason,
                )
            )
        )
    return pd.DataFrame(summaries).sort_values(["symbol", "session_date", "continuation_id"], kind="stable").reset_index(drop=True)


def build_event_transition_summary(evolution_df: pd.DataFrame) -> pd.DataFrame:
    if evolution_df.empty:
        return pd.DataFrame(columns=["continuation_id", "event_index", "event_type", "replay_state_transition", "transition_reason"])
    return evolution_df[
        ["continuation_id", "event_index", "event_type", "replay_state_transition", "transition_reason"]
    ].copy()


def build_quality_evolution_summary(evolution_df: pd.DataFrame) -> pd.DataFrame:
    if evolution_df.empty:
        return pd.DataFrame(columns=["continuation_id", "event_index", "participation_quality_label", "expansion_score", "fragility_score", "participation_quality_transition"])
    return evolution_df[
        [
            "continuation_id",
            "event_index",
            "participation_quality_label",
            "expansion_score",
            "fragility_score",
            "participation_quality_transition",
        ]
    ].copy()


def build_size_evolution_summary(evolution_df: pd.DataFrame) -> pd.DataFrame:
    if evolution_df.empty:
        return pd.DataFrame(columns=["continuation_id", "event_index", "event_type", "size_multiplier", "size_multiplier_delta", "add_path_transition"])
    return evolution_df[
        [
            "continuation_id",
            "event_index",
            "event_type",
            "size_multiplier",
            "size_multiplier_delta",
            "add_path_transition",
        ]
    ].copy()


def build_exit_reason_summary(chain_summary_df: pd.DataFrame) -> pd.DataFrame:
    if chain_summary_df.empty:
        return pd.DataFrame(columns=["exit_reason", "chain_count"])
    return (
        chain_summary_df.groupby("exit_reason", dropna=False)
        .size()
        .reset_index(name="chain_count")
        .sort_values(["chain_count", "exit_reason"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )


def build_chain_summary_metrics(chain_summary_df: pd.DataFrame, evolution_df: pd.DataFrame) -> pd.DataFrame:
    if chain_summary_df.empty:
        return pd.DataFrame(columns=["metric_name", "metric_value"])

    if evolution_df.empty:
        evolution_df = pd.DataFrame(columns=["continuation_id", "event_type", "participation_quality_transition", "size_multiplier_delta"])

    continuation_ids = chain_summary_df["continuation_id"].astype(str)
    add_ids = set(evolution_df[evolution_df["event_type"].astype(str).eq("ADD")]["continuation_id"].astype(str))
    scale_ids = set(evolution_df[evolution_df["event_type"].astype(str).eq("SCALE_UP")]["continuation_id"].astype(str))
    probe_ids = set(evolution_df[evolution_df["event_type"].astype(str).eq("PROBE_ENTRY")]["continuation_id"].astype(str))
    persist_ids = set(evolution_df[evolution_df["event_type"].astype(str).eq("PERSIST")]["continuation_id"].astype(str))

    probe_to_add_rate = float(sum(1 for continuation_id in set(continuation_ids) if continuation_id in probe_ids and continuation_id in add_ids) / max(len(set(continuation_ids)), 1))
    add_to_scale_rate = float(sum(1 for continuation_id in add_ids if continuation_id in scale_ids) / max(len(add_ids), 1))
    avg_adds_per_chain = float(
        evolution_df["event_type"].astype(str).eq("ADD").groupby(evolution_df["continuation_id"]).sum().mean()
    ) if not evolution_df.empty else 0.0
    healthy_to_fragile_transition_rate = float(
        evolution_df["participation_quality_transition"].astype(str).eq("HEALTHY_EXPANSION->FRAGILE_CROWDING").groupby(evolution_df["continuation_id"]).any().mean()
    ) if not evolution_df.empty else 0.0
    avg_size_growth = float(
        pd.to_numeric(
            evolution_df.loc[pd.to_numeric(evolution_df["size_multiplier_delta"], errors="coerce").fillna(0.0) > 0, "size_multiplier_delta"],
            errors="coerce",
        ).fillna(0.0).mean()
    ) if not evolution_df.empty else 0.0

    metrics = [
        ("avg_event_chain_length", float(pd.to_numeric(chain_summary_df["event_count"], errors="coerce").fillna(0.0).mean())),
        ("avg_adds_per_chain", avg_adds_per_chain),
        ("probe_to_add_rate", probe_to_add_rate),
        ("add_to_scale_rate", add_to_scale_rate),
        ("persist_duration", float(pd.to_numeric(chain_summary_df["persistence_duration_events"], errors="coerce").fillna(0.0).mean())),
        ("healthy_to_fragile_transition_rate", healthy_to_fragile_transition_rate),
        ("avg_size_growth", avg_size_growth),
        ("invalidation_rate", float(chain_summary_df["invalidated"].fillna(False).astype(bool).mean())),
        ("chains_with_persist", float(sum(1 for continuation_id in set(continuation_ids) if continuation_id in persist_ids))),
    ]
    return pd.DataFrame([{"metric_name": name, "metric_value": round(value, 6)} for name, value in metrics])
