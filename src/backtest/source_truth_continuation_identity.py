from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


LINKAGE_CONFIDENCE = {
    "trade_id_master_match": 1.00,
    "breakout_bar_match": 0.90,
    "entry_bar_match": 0.80,
    "session_bar_continuity": 0.65,
    "replay_continuity_fallback": 0.35,
    "unmatched_synthetic": 0.10,
}


@dataclass(frozen=True)
class SourceTruthContinuationIdentity:
    continuation_id: str
    setup_id: str
    symbol: str
    continuation_start_ts: pd.Timestamp | None
    continuation_end_ts: pd.Timestamp | None
    lineage_confidence: float
    linkage_source: str


@dataclass(frozen=True)
class SourceTruthContinuationIdentityConfig:
    source_linked_confidence_floor: float = 0.80


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


def _normalize_master(corrected_master_df: pd.DataFrame) -> pd.DataFrame:
    if corrected_master_df.empty:
        return pd.DataFrame(columns=["trade_id", "symbol", "entry_date"])

    frame = corrected_master_df.copy()
    if "trade_id" in frame.columns:
        frame["trade_id"] = frame["trade_id"].astype(str)
    if "symbol" in frame.columns:
        frame["symbol"] = frame["symbol"].astype(str).str.upper()
    if "entry_date" in frame.columns:
        frame["entry_date"] = pd.to_datetime(frame["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for column in ("entry_ts", "exit_ts", "breakout_timestamp"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)
    return frame.drop_duplicates(subset=["trade_id"], keep="first").reset_index(drop=True)


def _has_session_bars(intraday_bars_df: pd.DataFrame, symbol: str, session_date: str) -> bool:
    if intraday_bars_df.empty:
        return False
    frame = intraday_bars_df.copy()
    if "symbol" not in frame.columns or "bar_date" not in frame.columns:
        return False
    mask = (
        frame["symbol"].astype(str).str.upper().eq(str(symbol).upper())
        & frame["bar_date"].astype(str).eq(str(session_date))
    )
    return bool(mask.any())


def _classify_linkage_source(row: pd.Series, master_match: bool, session_bar_match: bool) -> str:
    setup_type = _safe_text(row.get("setup_type"))
    intraday_match_status = _safe_text(row.get("intraday_match_status"))

    if master_match and session_bar_match:
        return "trade_id_master_match"
    if session_bar_match and setup_type == "breakout_timestamp":
        return "breakout_bar_match"
    if session_bar_match and setup_type == "entry_timestamp_fallback":
        return "entry_bar_match"
    if intraday_match_status == "matched_session_bars":
        return "session_bar_continuity"
    if setup_type != "unmatched_shadow_only":
        return "replay_continuity_fallback"
    return "unmatched_synthetic"


def build_source_truth_continuation_identity(
    multi_event_dataset_df: pd.DataFrame,
    setup_frame: pd.DataFrame,
    corrected_master_df: pd.DataFrame,
    intraday_bars_df: pd.DataFrame,
    config: SourceTruthContinuationIdentityConfig = SourceTruthContinuationIdentityConfig(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if multi_event_dataset_df.empty:
        row_columns = [
            "continuation_id",
            "setup_id",
            "event_id",
            "event_type",
            "timestamp",
            "linkage_source",
            "lineage_confidence",
            "source_linked_flag",
            "intraday_match_status",
            "setup_type",
            "raw_trade_id",
            "raw_signal_id",
            "symbol",
            "session_date",
        ]
        continuation_columns = [
            "continuation_id",
            "setup_id",
            "symbol",
            "continuation_start_ts",
            "continuation_end_ts",
            "lineage_confidence",
            "linkage_source",
            "source_linked_flag",
        ]
        return pd.DataFrame(columns=row_columns), pd.DataFrame(columns=continuation_columns)

    events = multi_event_dataset_df.copy()
    setup = setup_frame.copy()
    master = _normalize_master(corrected_master_df)
    intraday = intraday_bars_df.copy()

    for frame in (events, setup):
        if "symbol" in frame.columns:
            frame["symbol"] = frame["symbol"].astype(str).str.upper()
        if "session_date" in frame.columns:
            frame["session_date"] = frame["session_date"].astype(str)
    if "setup_session_date" in setup.columns:
        setup["setup_session_date"] = setup["setup_session_date"].astype(str)

    setup_columns = [
        "setup_id",
        "symbol",
        "session_date",
        "setup_session_date",
        "setup_type",
        "intraday_match_status",
        "master_match",
        "breakout_timestamp",
        "entry_ts",
        "raw_trade_id",
        "raw_signal_id",
        "trade_id",
        "signal_id",
    ]
    events = events.merge(
        setup[[column for column in setup_columns if column in setup.columns]].drop_duplicates(
            subset=["setup_id", "raw_trade_id"],
            keep="first",
        ),
        on=["setup_id", "raw_trade_id"],
        how="left",
        suffixes=("", "_setup"),
    )
    if "trade_id_setup" in events.columns and "trade_id" not in events.columns:
        events["trade_id"] = events["trade_id_setup"]
    if "signal_id_setup" in events.columns and "signal_id" not in events.columns:
        events["signal_id"] = events["signal_id_setup"]

    if not master.empty and "trade_id" in events.columns:
        events["trade_id"] = events["trade_id"].astype(str)
        events = events.merge(
            master[[column for column in ("trade_id", "symbol", "entry_date") if column in master.columns]].rename(
                columns={"symbol": "master_symbol"}
            ),
            on="trade_id",
            how="left",
        )
    else:
        events["master_symbol"] = None
        events["entry_date"] = None

    session_date_series = events.get("session_date")
    if session_date_series is None:
        session_date_series = pd.Series(["unknown_date"] * len(events), index=events.index)
    else:
        session_date_series = session_date_series.fillna("unknown_date").astype(str)

    setup_session_series = events.get("setup_session_date")
    if setup_session_series is None:
        setup_session_series = session_date_series
    else:
        setup_session_series = setup_session_series.fillna("").astype(str)
        setup_session_series = setup_session_series.where(setup_session_series.ne(""), session_date_series)

    events["master_match"] = (
        events.get("master_match", False).fillna(False).astype(bool)
        & events["master_symbol"].fillna("").astype(str).str.upper().eq(events["symbol"].fillna("").astype(str).str.upper())
        & events["entry_date"].fillna("").astype(str).eq(setup_session_series)
    )
    events["session_bar_match"] = [
        _has_session_bars(intraday, symbol, session_date)
        for symbol, session_date in zip(events["symbol"].fillna("UNKNOWN"), setup_session_series)
    ]
    events["linkage_source"] = [
        _classify_linkage_source(row, bool(master_match), bool(session_bar_match))
        for (_, row), master_match, session_bar_match in zip(
            events.iterrows(),
            events["master_match"].tolist(),
            events["session_bar_match"].tolist(),
        )
    ]
    events["lineage_confidence"] = events["linkage_source"].map(LINKAGE_CONFIDENCE).fillna(0.10)
    events["source_linked_flag"] = (
        pd.to_numeric(events["lineage_confidence"], errors="coerce").fillna(0.0).ge(config.source_linked_confidence_floor)
        & ~events["linkage_source"].astype(str).isin({"replay_continuity_fallback", "unmatched_synthetic"})
    )

    row_identity_df = events[
        [
            "continuation_id",
            "setup_id",
            "event_id",
            "event_type",
            "timestamp",
            "linkage_source",
            "lineage_confidence",
            "source_linked_flag",
            "intraday_match_status",
            "setup_type",
            "raw_trade_id",
            "raw_signal_id",
            "symbol",
            "session_date",
        ]
    ].copy()
    row_identity_df["timestamp"] = pd.to_datetime(row_identity_df["timestamp"], errors="coerce", utc=True)
    row_identity_df = row_identity_df.sort_values(
        ["continuation_id", "timestamp", "event_id"],
        kind="stable",
    ).reset_index(drop=True)

    continuation_rows: list[dict[str, Any]] = []
    for continuation_id, group in row_identity_df.groupby("continuation_id", dropna=False, sort=False):
        group = group.sort_values(["timestamp", "event_id"], kind="stable").reset_index(drop=True)
        best_row = group.sort_values(["lineage_confidence", "timestamp"], ascending=[False, True], kind="stable").iloc[0]
        continuation_rows.append(
            {
                "continuation_id": continuation_id,
                "setup_id": _safe_text(group.iloc[0].get("setup_id"), "unknown_setup"),
                "symbol": _safe_text(group.iloc[0].get("symbol"), "UNKNOWN"),
                "continuation_start_ts": group["timestamp"].min(),
                "continuation_end_ts": group["timestamp"].max(),
                "lineage_confidence": round(_safe_float(best_row.get("lineage_confidence"), 0.10), 6),
                "linkage_source": _safe_text(best_row.get("linkage_source"), "unmatched_synthetic"),
                "source_linked_flag": bool(group["source_linked_flag"].any()),
            }
        )
    continuation_identity_df = pd.DataFrame(continuation_rows)
    if not continuation_identity_df.empty:
        continuation_identity_df = continuation_identity_df.sort_values(
            ["continuation_start_ts", "continuation_id"],
            kind="stable",
        ).reset_index(drop=True)
    return row_identity_df, continuation_identity_df
