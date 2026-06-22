from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


TERMINAL_REPLAY_STATES = {"EXITED"}
TERMINAL_REASONS = {"dislocation_exit", "size_to_zero", "no_live_position", "fragile_exit"}


@dataclass(frozen=True)
class ContinuationSetupIdentity:
    setup_id: str
    symbol: str
    session_date: str
    setup_timestamp: pd.Timestamp | None
    setup_type: str


@dataclass(frozen=True)
class ContinuationSetupIdentityConfig:
    gap_minutes: int = 20


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


def _pick_master_columns(master_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "trade_id",
        "symbol",
        "entry_date",
        "entry_ts",
        "exit_ts",
        "breakout_timestamp",
        "realized_R",
    ]
    available = [column for column in columns if column in master_df.columns]
    selected = master_df[available].copy()
    if "trade_id" in selected.columns:
        selected["trade_id"] = selected["trade_id"].astype(str)
    if "symbol" in selected.columns:
        selected["symbol"] = selected["symbol"].astype(str).str.upper()
    for column in ("entry_ts", "exit_ts", "breakout_timestamp"):
        if column in selected.columns:
            selected[column] = pd.to_datetime(selected[column], errors="coerce", utc=True)
    if "entry_date" in selected.columns:
        selected["entry_date"] = pd.to_datetime(selected["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    selected = selected.drop_duplicates(subset=["trade_id"], keep="first")
    return selected


def _merge_replay_sources(
    shadow_log_df: pd.DataFrame,
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame,
) -> pd.DataFrame:
    if shadow_log_df.empty:
        return pd.DataFrame()

    replay_columns = [
        "lifecycle_id",
        "trade_id",
        "replay_state",
        "previous_replay_state",
        "add_activated",
        "transition_reason",
        "add_path_open",
        "is_fragile",
        "is_dislocation",
        "is_live_position",
        "size_increased_vs_prev",
        "size_reduced_vs_prev",
    ]
    lifecycle_columns = [
        "lifecycle_id",
        "trade_id",
        "signal_id",
        "strategy_id",
        "session_date",
        "timestamp",
        "sequence_in_lifecycle",
        "participation_quality_label",
        "expansion_score",
        "fragility_score",
        "confidence",
        "state_label",
        "continuation_risk_score",
        "factor_budget_allowed",
        "exposure_allow_add",
        "staged_gate_stage",
        "staged_add_allowed",
        "quality_aware_policy_stage",
        "quality_aware_add_allowed",
        "healthy_policy_label",
        "final_add_allowed",
        "size_multiplier",
    ]

    replay_frame = replay_trace_df[[column for column in replay_columns if column in replay_trace_df.columns]].copy()
    lifecycle_frame = lifecycle_rows_df[[column for column in lifecycle_columns if column in lifecycle_rows_df.columns]].copy()
    frame = lifecycle_frame.merge(replay_frame, on=["lifecycle_id", "trade_id"], how="left")
    if "trade_id" in shadow_log_df.columns:
        shadow_frame = shadow_log_df.copy()
        shadow_frame["trade_id"] = shadow_frame["trade_id"].astype(str)
    else:
        shadow_frame = shadow_log_df.copy()
    if "trade_id" in frame.columns:
        frame["trade_id"] = frame["trade_id"].astype(str)

    shadow_columns = [
        "trade_id",
        "symbol",
        "day_key",
        "current_split",
        "sector_group",
        "baseline_realized_R",
    ]
    available_shadow = [column for column in shadow_columns if column in shadow_frame.columns]
    if available_shadow:
        frame = frame.merge(
            shadow_frame[available_shadow].drop_duplicates(subset=["trade_id"]),
            on="trade_id",
            how="left",
        )
    return frame


def build_setup_identity_frame(
    shadow_log_df: pd.DataFrame,
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame,
    corrected_master_df: pd.DataFrame,
    config: ContinuationSetupIdentityConfig = ContinuationSetupIdentityConfig(),
) -> pd.DataFrame:
    frame = _merge_replay_sources(shadow_log_df, replay_trace_df, lifecycle_rows_df)
    if frame.empty:
        return pd.DataFrame()

    master = _pick_master_columns(corrected_master_df)
    if not master.empty:
        frame["symbol"] = frame["symbol"].astype(str).str.upper()
        frame = frame.merge(master, on=["trade_id"], how="left", suffixes=("", "_master"))
        if "symbol_master" in frame.columns:
            symbol_match = frame["symbol_master"].astype(str).str.upper().eq(frame["symbol"].astype(str).str.upper())
            if "entry_date" in frame.columns:
                session_match = frame["entry_date"].fillna("").astype(str).eq(frame["session_date"].fillna("").astype(str))
                matched = symbol_match & session_match
            else:
                matched = symbol_match
        else:
            matched = pd.Series(False, index=frame.index)
    else:
        matched = pd.Series(False, index=frame.index)

    frame["entry_ts"] = pd.to_datetime(frame.get("entry_ts"), errors="coerce", utc=True)
    frame["exit_ts"] = pd.to_datetime(frame.get("exit_ts"), errors="coerce", utc=True)
    frame["breakout_timestamp"] = pd.to_datetime(frame.get("breakout_timestamp"), errors="coerce", utc=True)
    frame["timestamp"] = pd.to_datetime(frame.get("timestamp"), errors="coerce", utc=True)

    frame["master_match"] = matched.fillna(False)
    frame["setup_type"] = "unmatched_shadow_only"
    frame.loc[frame["master_match"] & frame["breakout_timestamp"].notna(), "setup_type"] = "breakout_timestamp"
    frame.loc[
        frame["master_match"] & frame["breakout_timestamp"].isna() & frame["entry_ts"].notna(),
        "setup_type",
    ] = "entry_timestamp_fallback"
    frame["setup_anchor_ts"] = frame["breakout_timestamp"].where(frame["breakout_timestamp"].notna(), frame["entry_ts"])
    frame["setup_anchor_ts"] = frame["setup_anchor_ts"].where(frame["setup_anchor_ts"].notna(), frame["timestamp"])
    frame["setup_session_date"] = frame["session_date"].fillna("").astype(str)
    anchor_session = frame["setup_anchor_ts"].dt.strftime("%Y-%m-%d")
    frame.loc[frame["setup_session_date"].eq(""), "setup_session_date"] = anchor_session.fillna("")
    frame["setup_session_date"] = frame["setup_session_date"].replace("", "unknown_date")
    frame["symbol"] = frame["symbol"].fillna("").astype(str).str.upper().replace("", "UNKNOWN")

    sort_anchor = frame["setup_anchor_ts"].fillna(frame["timestamp"])
    frame = frame.assign(_sort_anchor=sort_anchor).sort_values(
        ["symbol", "setup_session_date", "_sort_anchor", "trade_id"],
        kind="stable",
    ).reset_index(drop=True)

    setup_ids: list[str] = []
    setup_ordinals: list[int] = []
    setup_member_indices: list[int] = []
    setup_identities: list[ContinuationSetupIdentity] = []
    current_key: tuple[str, str] | None = None
    current_setup_ordinal = 0
    current_member_index = 0
    previous_row: pd.Series | None = None
    gap_delta = pd.Timedelta(minutes=config.gap_minutes)

    for _, row in frame.iterrows():
        key = (_safe_text(row.get("symbol"), "UNKNOWN"), _safe_text(row.get("setup_session_date"), "unknown_date"))
        anchor_ts = pd.Timestamp(row.get("setup_anchor_ts")) if pd.notna(row.get("setup_anchor_ts")) else pd.NaT
        start_new = previous_row is None or key != current_key
        if not start_new and previous_row is not None:
            prev_anchor = pd.Timestamp(previous_row.get("setup_anchor_ts")) if pd.notna(previous_row.get("setup_anchor_ts")) else pd.NaT
            prev_unmatched = _safe_text(previous_row.get("setup_type")) == "unmatched_shadow_only"
            curr_matched = _safe_text(row.get("setup_type")) != "unmatched_shadow_only"
            prev_terminal = (
                _safe_text(previous_row.get("replay_state")) in TERMINAL_REPLAY_STATES
                or _safe_text(previous_row.get("transition_reason")) in TERMINAL_REASONS
            )
            has_large_gap = pd.notna(anchor_ts) and pd.notna(prev_anchor) and (anchor_ts - prev_anchor) > gap_delta
            terminal_and_later = pd.notna(anchor_ts) and pd.notna(prev_anchor) and prev_terminal and anchor_ts > prev_anchor
            start_new = prev_unmatched and curr_matched or terminal_and_later or has_large_gap

        if start_new:
            current_setup_ordinal = current_setup_ordinal + 1 if key == current_key else 1
            current_member_index = 1
        else:
            current_member_index += 1

        setup_id = f"{key[0]}|{key[1]}|setup_{current_setup_ordinal:03d}"
        setup_ids.append(setup_id)
        setup_ordinals.append(current_setup_ordinal)
        setup_member_indices.append(current_member_index)
        setup_identities.append(
            ContinuationSetupIdentity(
                setup_id=setup_id,
                symbol=key[0],
                session_date=key[1],
                setup_timestamp=anchor_ts if pd.notna(anchor_ts) else pd.NaT,
                setup_type=_safe_text(row.get("setup_type"), "unmatched_shadow_only"),
            )
        )
        current_key = key
        previous_row = row

    frame["setup_id"] = setup_ids
    frame["setup_ordinal"] = setup_ordinals
    frame["setup_member_index"] = setup_member_indices
    frame["setup_timestamp"] = frame["setup_anchor_ts"]
    frame["intraday_match_status"] = "unmatched_shadow_only"
    frame.loc[frame["master_match"], "intraday_match_status"] = "matched_master_pending_bars"
    frame["raw_trade_id"] = frame["trade_id"].astype(str)
    frame["raw_signal_id"] = frame.get("signal_id")
    frame["setup_identity"] = [asdict(identity) for identity in setup_identities]
    return frame.drop(columns=["_sort_anchor"]).reset_index(drop=True)


def build_setup_identity_summary(setup_frame: pd.DataFrame) -> pd.DataFrame:
    if setup_frame.empty:
        return pd.DataFrame(
            columns=["setup_type", "intraday_match_status", "setup_count", "row_count", "symbol_count"]
        )
    summary = (
        setup_frame.groupby(["setup_type", "intraday_match_status"], dropna=False)
        .agg(
            setup_count=("setup_id", "nunique"),
            row_count=("trade_id", "size"),
            symbol_count=("symbol", "nunique"),
        )
        .reset_index()
    )
    return summary.sort_values(
        ["setup_count", "row_count", "setup_type"],
        ascending=[False, False, True],
        kind="stable",
    ).reset_index(drop=True)


@dataclass(frozen=True)
class ContinuationSetup:
    continuation_id: str
    setup_id: str
    setup_index: int
    symbol: str
    session_date: str
    setup_timestamp: pd.Timestamp | None
    anchor_trade_id: str
    anchor_signal_id: str | None
    anchor_sequence_in_lifecycle: int
    setup_status: str
    initial_replay_state: str
    initial_transition_reason: str
    initial_state_label: str
    initial_participation_quality_label: str
    initial_size_multiplier: float
    initial_add_activated: bool


def _ordered_columns(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in frame.columns]


def _normalize_minimal_replay_inputs(
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if replay_trace_df.empty:
        return pd.DataFrame()

    frame = replay_trace_df.copy()
    if lifecycle_rows_df is not None and not lifecycle_rows_df.empty:
        merge_columns = [
            "lifecycle_id",
            "trade_id",
            "signal_id",
            "timestamp",
            "symbol",
            "session_date",
            "sequence_in_lifecycle",
        ]
        available_merge = _ordered_columns(lifecycle_rows_df, merge_columns)
        extra_columns = [
            column
            for column in available_merge
            if column not in {"lifecycle_id", "trade_id"} and column not in frame.columns
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
    if "session_date" not in frame.columns:
        frame["session_date"] = frame["timestamp"].dt.strftime("%Y-%m-%d").fillna("unknown_date")
    frame["session_date"] = frame["session_date"].astype(str)
    if "signal_id" not in frame.columns:
        frame["signal_id"] = None
    if "lifecycle_id" not in frame.columns:
        frame["lifecycle_id"] = frame.apply(
            lambda row: f"{_safe_text(row.get('symbol'), 'unknown_symbol')}|{_safe_text(row.get('session_date'), 'unknown_date')}",
            axis=1,
        )
    sort_columns = _ordered_columns(frame, ["lifecycle_id", "sequence_in_lifecycle", "timestamp", "trade_id", "signal_id"])
    return frame.sort_values(sort_columns, kind="stable").reset_index(drop=True)


def _minimal_setup_status(row: pd.Series) -> str:
    replay_state = _safe_text(row.get("replay_state"), "UNKNOWN")
    transition_reason = _safe_text(row.get("transition_reason"))
    quality_label = _safe_text(row.get("participation_quality_label"), "UNKNOWN")

    if replay_state == "EXITED" and transition_reason in {"dislocation_exit", "size_to_zero", "no_live_position"}:
        return "INVALIDATED"
    if replay_state == "REDUCING" or quality_label == "FRAGILE_CROWDING":
        return "FRAGILE"
    return "ACTIVE"


def build_continuation_setups(
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame | None = None,
    config: ContinuationSetupIdentityConfig = ContinuationSetupIdentityConfig(),
) -> tuple[ContinuationSetup, ...]:
    _ = config
    frame = _normalize_minimal_replay_inputs(replay_trace_df, lifecycle_rows_df)
    if frame.empty:
        return ()

    setups: list[ContinuationSetup] = []
    for continuation_id, group in frame.groupby("lifecycle_id", dropna=False, sort=False):
        group = group.sort_values(
            _ordered_columns(group, ["sequence_in_lifecycle", "timestamp", "trade_id", "signal_id"]),
            kind="stable",
        ).reset_index(drop=True)
        anchor = group.iloc[0]
        setups.append(
            ContinuationSetup(
                continuation_id=_safe_text(continuation_id, "unknown_continuation"),
                setup_id=f"{_safe_text(continuation_id, 'unknown_continuation')}|setup|001",
                setup_index=1,
                symbol=_safe_text(anchor.get("symbol"), "unknown_symbol"),
                session_date=_safe_text(anchor.get("session_date"), "unknown_date"),
                setup_timestamp=anchor.get("timestamp"),
                anchor_trade_id=_safe_text(anchor.get("trade_id"), "unknown_trade"),
                anchor_signal_id=(_safe_text(anchor.get("signal_id")) or None),
                anchor_sequence_in_lifecycle=int(_safe_float(anchor.get("sequence_in_lifecycle"), 0.0)),
                setup_status=_minimal_setup_status(anchor),
                initial_replay_state=_safe_text(anchor.get("replay_state"), "UNKNOWN"),
                initial_transition_reason=_safe_text(anchor.get("transition_reason"), "unknown_transition"),
                initial_state_label=_safe_text(anchor.get("state_label"), "UNKNOWN"),
                initial_participation_quality_label=_safe_text(anchor.get("participation_quality_label"), "UNKNOWN"),
                initial_size_multiplier=_safe_float(anchor.get("size_multiplier"), 0.0),
                initial_add_activated=_safe_bool(anchor.get("add_activated")),
            )
        )
    return tuple(setups)


def normalize_continuation_setup_rows(
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    setups = build_continuation_setups(replay_trace_df, lifecycle_rows_df)
    if not setups:
        return pd.DataFrame(
            columns=[
                "continuation_id",
                "setup_id",
                "setup_index",
                "symbol",
                "session_date",
                "setup_timestamp",
                "anchor_trade_id",
                "anchor_signal_id",
                "anchor_sequence_in_lifecycle",
                "setup_status",
                "initial_replay_state",
                "initial_transition_reason",
                "initial_state_label",
                "initial_participation_quality_label",
                "initial_size_multiplier",
                "initial_add_activated",
            ]
        )
    return pd.DataFrame([asdict(setup) for setup in setups])


def build_continuation_setup_type_summary(setup_df: pd.DataFrame) -> pd.DataFrame:
    if setup_df.empty:
        return pd.DataFrame(columns=["setup_status", "setup_count", "live_setup_count", "avg_initial_size_multiplier"])
    summary = (
        setup_df.groupby("setup_status", dropna=False)
        .agg(
            setup_count=("setup_id", "size"),
            live_setup_count=("initial_size_multiplier", lambda values: int(pd.to_numeric(values, errors="coerce").fillna(0.0).gt(0.0).sum())),
            avg_initial_size_multiplier=("initial_size_multiplier", lambda values: round(float(pd.to_numeric(values, errors="coerce").fillna(0.0).mean()), 6)),
        )
        .reset_index()
    )
    summary["setup_count"] = pd.to_numeric(summary["setup_count"], errors="coerce").fillna(0).astype(int)
    summary["live_setup_count"] = pd.to_numeric(summary["live_setup_count"], errors="coerce").fillna(0).astype(int)
    return summary.sort_values(["setup_count", "setup_status"], ascending=[False, True], kind="stable").reset_index(drop=True)


def build_continuation_setup_identity(
    replay_trace_df: pd.DataFrame,
    lifecycle_rows_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    setup_df = normalize_continuation_setup_rows(replay_trace_df, lifecycle_rows_df)
    return setup_df, build_continuation_setup_type_summary(setup_df)
