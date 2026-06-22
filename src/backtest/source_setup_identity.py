from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


SETUP_CONFIDENCE = {
    "explicit_breakout_setup": 1.00,
    "explicit_entry_setup": 0.90,
    "trade_linked_setup": 0.80,
    "chronology_linked_setup": 0.60,
    "replay_linked_setup": 0.35,
    "unmatched_setup": 0.10,
}


@dataclass(frozen=True)
class SourceSetupIdentity:
    setup_id: str
    symbol: str
    session_date: str
    setup_timestamp: pd.Timestamp | None
    setup_origin_type: str
    setup_confidence: float


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
    return frame.drop_duplicates(subset=["trade_id"], keep="first").reset_index(drop=True)


def _has_session_bars(intraday_bars_df: pd.DataFrame, symbol: str, session_date: str) -> bool:
    if intraday_bars_df.empty or "symbol" not in intraday_bars_df.columns or "bar_date" not in intraday_bars_df.columns:
        return False
    mask = (
        intraday_bars_df["symbol"].astype(str).str.upper().eq(str(symbol).upper())
        & intraday_bars_df["bar_date"].astype(str).eq(str(session_date))
    )
    return bool(mask.any())


def _classify_setup_origin(row: pd.Series, session_bar_match: bool) -> str:
    setup_type = _safe_text(row.get("setup_type"))
    master_match = bool(row.get("master_match", False))
    if setup_type == "unmatched_shadow_only":
        return "unmatched_setup"
    if session_bar_match and setup_type == "breakout_timestamp":
        return "explicit_breakout_setup"
    if session_bar_match and setup_type == "entry_timestamp_fallback":
        return "explicit_entry_setup"
    if master_match:
        return "trade_linked_setup"
    if setup_type != "unmatched_shadow_only":
        return "chronology_linked_setup"
    if _safe_text(row.get("setup_id")):
        return "replay_linked_setup"
    return "unmatched_setup"


def build_source_setup_identity(
    setup_frame: pd.DataFrame,
    multi_event_dataset_df: pd.DataFrame,
    corrected_master_df: pd.DataFrame,
    intraday_bars_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if setup_frame.empty:
        empty = pd.DataFrame(
            columns=[
                "setup_id",
                "symbol",
                "session_date",
                "setup_timestamp",
                "setup_origin_type",
                "setup_confidence",
                "session_bar_match",
                "master_match",
            ]
        )
        summary = pd.DataFrame(columns=["setup_origin_type", "setup_count", "symbol_count", "avg_setup_confidence"])
        return empty, summary

    setup = setup_frame.copy()
    master = _normalize_master(corrected_master_df)
    events = multi_event_dataset_df.copy()
    intraday = intraday_bars_df.copy()

    if "symbol" in setup.columns:
        setup["symbol"] = setup["symbol"].astype(str).str.upper()
    if "setup_session_date" in setup.columns:
        setup["setup_session_date"] = setup["setup_session_date"].astype(str)
    if "session_date" in setup.columns:
        setup["session_date"] = setup["session_date"].astype(str)
    if "trade_id" in setup.columns:
        setup["trade_id"] = setup["trade_id"].astype(str)
    if "setup_timestamp" in setup.columns:
        setup["setup_timestamp"] = pd.to_datetime(setup["setup_timestamp"], errors="coerce", utc=True)

    if not master.empty and "trade_id" in setup.columns:
        setup = setup.merge(
            master.rename(columns={"symbol": "master_symbol", "entry_date": "master_entry_date"}),
            on="trade_id",
            how="left",
        )
        session_series = setup.get("setup_session_date", setup.get("session_date", pd.Series(["unknown_date"] * len(setup), index=setup.index)))
        setup["master_match"] = (
            setup.get("master_match", False).fillna(False).astype(bool)
            & setup["master_symbol"].fillna("").astype(str).str.upper().eq(setup["symbol"].fillna("").astype(str).str.upper())
            & setup.get("master_entry_date", pd.Series([""] * len(setup), index=setup.index)).fillna("").astype(str).eq(session_series.fillna("").astype(str))
        )
    else:
        setup["master_match"] = setup.get("master_match", False).fillna(False).astype(bool)

    session_series = setup.get("setup_session_date", setup.get("session_date", pd.Series(["unknown_date"] * len(setup), index=setup.index))).fillna("unknown_date").astype(str)
    setup["session_bar_match"] = [
        _has_session_bars(intraday, symbol, session_date)
        for symbol, session_date in zip(setup["symbol"].fillna("UNKNOWN"), session_series)
    ]
    setup["setup_origin_type"] = [
        _classify_setup_origin(row, bool(session_bar_match))
        for (_, row), session_bar_match in zip(setup.iterrows(), setup["session_bar_match"].tolist())
    ]
    setup["setup_confidence"] = setup["setup_origin_type"].map(SETUP_CONFIDENCE).fillna(0.10)

    if not events.empty and "setup_id" in events.columns:
        first_event_ts = (
            events.assign(timestamp=pd.to_datetime(events["timestamp"], errors="coerce", utc=True))
            .groupby("setup_id", dropna=False)["timestamp"]
            .min()
            .reset_index(name="first_event_timestamp")
        )
        setup = setup.merge(first_event_ts, on="setup_id", how="left")
        setup["setup_timestamp"] = setup["setup_timestamp"].where(setup["setup_timestamp"].notna(), setup["first_event_timestamp"])
    else:
        setup["first_event_timestamp"] = pd.NaT

    setup["resolved_session_date"] = session_series
    setup_identity_df = (
        setup.sort_values(["symbol", "resolved_session_date", "setup_timestamp", "setup_id"], kind="stable")
        .drop_duplicates(subset=["setup_id"], keep="first")
    )
    setup_identity_df = setup_identity_df[
        [
            "setup_id",
            "symbol",
            "resolved_session_date",
            "setup_timestamp",
            "setup_origin_type",
            "setup_confidence",
            "session_bar_match",
            "master_match",
        ]
    ].rename(columns={"resolved_session_date": "session_date"}).reset_index(drop=True)

    summary_df = (
        setup_identity_df.groupby("setup_origin_type", dropna=False)
        .agg(
            setup_count=("setup_id", "nunique"),
            symbol_count=("symbol", "nunique"),
            avg_setup_confidence=("setup_confidence", lambda values: round(float(pd.to_numeric(values, errors="coerce").fillna(0.0).mean()), 6)),
        )
        .reset_index()
        .sort_values(["setup_count", "setup_origin_type"], ascending=[False, True], kind="stable")
        .reset_index(drop=True)
    )
    return setup_identity_df, summary_df
