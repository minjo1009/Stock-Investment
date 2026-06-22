from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


QUOTE_FIELDS = {"bid": "bp", "ask": "ap", "bid_size": "bs", "ask_size": "as"}
BAR_FIELDS = {"bar_open": "o", "bar_high": "h", "bar_low": "l", "bar_close": "c", "bar_volume": "v", "bar_vwap": "vw", "bar_trade_count": "n"}


def load_stream_archive_records(root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in root.rglob("*.jsonl") if root.exists() else []:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            rec = json.loads(line)
            rec["source_path"] = str(path)
            rec["source_line_number"] = line_no
            rows.append(rec)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["recv_ts_utc"] = pd.to_datetime(frame["recv_ts_utc"], utc=True, errors="coerce")
    frame["event_ts_utc"] = pd.to_datetime(frame["event_ts_utc"], utc=True, errors="coerce")
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    return frame.sort_values(["recv_ts_utc", "message_index"]).reset_index(drop=True)


def build_latest_microstructure_state(records: pd.DataFrame) -> pd.DataFrame:
    if records.empty:
        return pd.DataFrame()
    rows = []
    for symbol, subset in records.groupby("symbol"):
        latest_quote = latest_channel(subset, "quotes")
        latest_bar = latest_channel(subset, "bars")
        if latest_bar.empty:
            latest_bar = latest_channel(subset, "updatedBars")
        latest_status = latest_channel(subset, "statuses")
        latest_luld = latest_channel(subset, "lulds")
        row: dict[str, object] = {"symbol": symbol}
        row.update(extract_quote_state(latest_quote))
        row.update(extract_bar_state(latest_bar))
        row.update(extract_status_state(latest_status, latest_luld))
        rows.append(row)
    return pd.DataFrame(rows)


def latest_channel(frame: pd.DataFrame, channel: str) -> pd.Series:
    subset = frame[frame["channel"].astype(str).eq(channel)]
    return subset.iloc[-1] if not subset.empty else pd.Series(dtype=object)


def parse_raw_message(record: pd.Series) -> dict[str, object]:
    if record.empty:
        return {}
    raw = record.get("raw_message_json", "{}")
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return {}


def extract_quote_state(record: pd.Series) -> dict[str, object]:
    raw = parse_raw_message(record)
    out = {
        "last_quote_recv_ts_utc": pd.NaT,
        "last_quote_event_ts_utc": pd.NaT,
        "bid": pd.NA,
        "ask": pd.NA,
        "bid_size": pd.NA,
        "ask_size": pd.NA,
        "quote_raw_message_hash": pd.NA,
    }
    if record.empty:
        return out
    out["last_quote_recv_ts_utc"] = record.get("recv_ts_utc")
    out["last_quote_event_ts_utc"] = record.get("event_ts_utc")
    out["quote_raw_message_hash"] = record.get("raw_message_hash")
    for target, source in QUOTE_FIELDS.items():
        out[target] = raw.get(source, pd.NA)
    return out


def extract_bar_state(record: pd.Series) -> dict[str, object]:
    raw = parse_raw_message(record)
    out = {"last_bar_recv_ts_utc": pd.NaT, "last_bar_event_ts_utc": pd.NaT, "bar_raw_message_hash": pd.NA}
    for target in BAR_FIELDS:
        out[target] = pd.NA
    if record.empty:
        return out
    out["last_bar_recv_ts_utc"] = record.get("recv_ts_utc")
    out["last_bar_event_ts_utc"] = record.get("event_ts_utc")
    out["bar_raw_message_hash"] = record.get("raw_message_hash")
    for target, source in BAR_FIELDS.items():
        out[target] = raw.get(source, pd.NA)
    return out


def extract_status_state(status_record: pd.Series, luld_record: pd.Series) -> dict[str, object]:
    status_raw = parse_raw_message(status_record)
    luld_raw = parse_raw_message(luld_record)
    status_code = status_raw.get("sc", status_raw.get("status", pd.NA))
    luld_state = luld_raw.get("luld", luld_raw.get("indicator", pd.NA))
    return {
        "last_status_recv_ts_utc": status_record.get("recv_ts_utc") if not status_record.empty else pd.NaT,
        "last_luld_recv_ts_utc": luld_record.get("recv_ts_utc") if not luld_record.empty else pd.NaT,
        "status_code": status_code,
        "luld_state": luld_state,
        "status_clean_flag": int(pd.isna(status_code) or str(status_code).lower() in {"t", "active", "normal", "trading"}),
        "luld_active_flag": int(not pd.isna(luld_state) and str(luld_state).lower() not in {"", "none", "normal"}),
        "status_raw_message_hash": status_record.get("raw_message_hash") if not status_record.empty else pd.NA,
        "luld_raw_message_hash": luld_record.get("raw_message_hash") if not luld_record.empty else pd.NA,
    }


def build_decision_microstructure_snapshots(
    decisions: pd.DataFrame,
    state: pd.DataFrame,
    *,
    snapshot_ts_utc: str | None = None,
) -> pd.DataFrame:
    snapshot_ts = pd.Timestamp(snapshot_ts_utc or datetime.now(UTC).isoformat()).tz_convert("UTC")
    rows = []
    state_by_symbol = {row["symbol"]: row for row in state.to_dict(orient="records")} if not state.empty else {}
    for rec in decisions.to_dict(orient="records"):
        symbol = str(rec.get("symbol", "")).upper()
        source = state_by_symbol.get(symbol, {})
        quote_recv = pd.to_datetime(source.get("last_quote_recv_ts_utc"), utc=True, errors="coerce")
        bid = to_float(source.get("bid"))
        ask = to_float(source.get("ask"))
        bid_size = to_float(source.get("bid_size"))
        ask_size = to_float(source.get("ask_size"))
        mid = (bid + ask) / 2 if bid is not None and ask is not None else None
        spread_bps = ((ask - bid) / mid * 10000.0) if mid and mid > 0 else pd.NA
        nbbo_size_dollar = (mid * (bid_size + ask_size) * 100.0) if mid and bid_size is not None and ask_size is not None else pd.NA
        staleness = (snapshot_ts - quote_recv).total_seconds() * 1000 if pd.notna(quote_recv) else pd.NA
        missing = []
        if bid is None or ask is None:
            missing.append("nbbo_quote")
        if pd.isna(source.get("last_bar_recv_ts_utc", pd.NaT)):
            missing.append("bar_or_updated_bar")
        if pd.isna(source.get("last_status_recv_ts_utc", pd.NaT)):
            missing.append("status")
        if pd.isna(source.get("last_luld_recv_ts_utc", pd.NaT)):
            missing.append("luld")
        rows.append(
            {
                "microstructure_snapshot_id": stable_id("micro", str(rec.get("decision_id")), snapshot_ts.isoformat()),
                "decision_id": rec.get("decision_id"),
                "lifecycle_id": rec.get("lifecycle_id"),
                "symbol": symbol,
                "decision_ts_utc": rec.get("decision_recorded_ts_utc", snapshot_ts.isoformat()),
                "feature_cutoff_recv_ts_utc": snapshot_ts.isoformat(),
                "last_quote_recv_ts_utc": quote_recv.isoformat() if pd.notna(quote_recv) else pd.NA,
                "bid": bid if bid is not None else pd.NA,
                "ask": ask if ask is not None else pd.NA,
                "bid_size": bid_size if bid_size is not None else pd.NA,
                "ask_size": ask_size if ask_size is not None else pd.NA,
                "spread_bps": spread_bps,
                "nbbo_size_dollar": nbbo_size_dollar,
                "quote_staleness_ms": staleness,
                "status_clean_flag": source.get("status_clean_flag", pd.NA),
                "luld_active_flag": source.get("luld_active_flag", pd.NA),
                "microstructure_source_ready_flag": int(not missing),
                "missing_source_codes": ",".join(missing),
                "pre_action_snapshot_flag": 1,
                "order_submission_enabled_flag": rec.get("order_submission_enabled_flag", 0),
            }
        )
    return pd.DataFrame(rows)


def build_microstructure_feature_lineage(snapshots: pd.DataFrame, state: pd.DataFrame) -> pd.DataFrame:
    state_by_symbol = {row["symbol"]: row for row in state.to_dict(orient="records")} if not state.empty else {}
    rows = []
    feature_sources = {
        "spread_bps": ("nbbo_quote_stream", ["quote_raw_message_hash"]),
        "nbbo_size_dollar": ("nbbo_quote_stream", ["quote_raw_message_hash"]),
        "quote_staleness_ms": ("nbbo_quote_stream", ["quote_raw_message_hash"]),
        "status_clean_flag": ("status_luld_stream", ["status_raw_message_hash"]),
        "luld_active_flag": ("status_luld_stream", ["luld_raw_message_hash"]),
    }
    for rec in snapshots.to_dict(orient="records"):
        source = state_by_symbol.get(str(rec.get("symbol", "")).upper(), {})
        for feature, (required_source, hash_fields) in feature_sources.items():
            hashes = [str(source.get(field)) for field in hash_fields if not pd.isna(source.get(field, pd.NA))]
            rows.append(
                {
                    "decision_id": rec.get("decision_id"),
                    "microstructure_snapshot_id": rec.get("microstructure_snapshot_id"),
                    "feature_name": feature,
                    "required_source_name": required_source,
                    "source_hashes_json": json.dumps(hashes, ensure_ascii=False),
                    "source_available_flag": int(bool(hashes)),
                }
            )
    return pd.DataFrame(rows)


def to_float(value: object) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def stable_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
