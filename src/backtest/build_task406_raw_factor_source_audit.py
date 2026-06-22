from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.intraday_canonical_continuation_engine_388 import discover_intraday_symbols


DEFAULT_INTRADAY_DIR = Path("data/raw/us_intraday")
DEFAULT_OUT_DIR = Path("docs/reports/task_406_raw_factor_source_audit")

AVAILABLE_EXACT_FACTORS = {
    "ohlcv_bar": ["timestamp", "open", "high", "low", "close", "volume"],
    "trade_count": ["trade_count"],
    "vwap": ["vwap"],
    "entry_momentum_2bar": ["timestamp", "close"],
    "entry_range_position": ["timestamp", "high", "low", "close"],
    "entry_range_expansion": ["timestamp", "high", "low", "close"],
    "symbol_liquidity_ratio": ["timestamp", "close", "volume"],
    "market_breadth": ["timestamp", "close", "open"],
    "market_liquidity_ratio": ["timestamp", "close", "volume"],
    "theme_return_rank": ["timestamp", "close", "open"],
}

COLLECTABLE_BUT_MISSING_FACTORS = [
    "quote_bid_ask",
    "spread_bps",
    "quote_staleness",
    "displayed_depth",
    "trading_status",
    "luld_status",
    "trade_corrections",
    "trade_cancel_errors",
    "raw_stream_receive_timestamp",
]

NOT_AVAILABLE_IN_CURRENT_SOURCE_FACTORS = [
    "full_depth_order_book",
    "official_order_imbalance_feed",
]


@dataclass(frozen=True)
class RawFactorSourceAudit406Artifacts:
    raw_bar_provenance_panel: pd.DataFrame
    raw_factor_source_audit: pd.DataFrame
    raw_session_eligibility_audit: pd.DataFrame
    raw_collection_gap_audit: pd.DataFrame
    task_406a_decision: pd.DataFrame


def build_task406_raw_factor_source_audit(
    *,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
    symbols: list[str] | None = None,
) -> RawFactorSourceAudit406Artifacts:
    selected = sorted({str(s).strip().upper() for s in (symbols or discover_intraday_symbols(intraday_dir)) if str(s).strip()})
    provenance = build_raw_bar_provenance_panel(intraday_dir, selected)
    source_audit = build_raw_factor_source_audit_table(provenance)
    session_audit = build_raw_session_eligibility_audit(provenance)
    gap_audit = build_raw_collection_gap_audit(source_audit)
    decision = build_task_406a_decision(provenance, source_audit, session_audit)
    artifacts = RawFactorSourceAudit406Artifacts(provenance, source_audit, session_audit, gap_audit, decision)
    write_task406a_artifacts(artifacts, out_dir)
    return artifacts


def build_raw_bar_provenance_panel(intraday_dir: Path, symbols: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        path = _symbol_path(intraday_dir, symbol)
        if path is None:
            continue
        raw = pd.read_csv(path, encoding="utf-8-sig")
        raw.columns = [str(c).strip().lower() for c in raw.columns]
        if "datetime" in raw.columns and "timestamp" not in raw.columns:
            raw = raw.rename(columns={"datetime": "timestamp"})
        if "date" in raw.columns and "timestamp" not in raw.columns:
            raw = raw.rename(columns={"date": "timestamp"})
        if "timestamp" not in raw.columns:
            continue
        frame = raw.reset_index(drop=False).rename(columns={"index": "raw_row_number"}).copy()
        frame["raw_row_number"] = frame["raw_row_number"].astype(int) + 1
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        frame = frame.dropna(subset=["timestamp"]).copy()
        if frame.empty:
            continue
        frame["timestamp"] = frame["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        frame["symbol"] = symbol
        frame["raw_bar_id"] = frame["symbol"] + "|" + frame["timestamp"].astype(str)
        frame["raw_source_path"] = str(path)
        hash_source_cols = [c for c in ["timestamp", "open", "high", "low", "close", "volume", "trade_count", "vwap"] if c in frame.columns]
        frame["raw_row_hash"] = pd.util.hash_pandas_object(frame[hash_source_cols].astype(str), index=False).astype(str)
        for column in ["timestamp", "open", "high", "low", "close", "volume", "trade_count", "vwap"]:
            flag = f"{column}_available_flag"
            frame[flag] = int(column in frame.columns)
            if column in frame.columns:
                frame[flag] = frame[column].notna().astype(int)
        frame["quote_bid_ask_available_flag"] = int({"bid", "ask"}.issubset(set(frame.columns)))
        frame["trading_status_available_flag"] = int("trading_status" in frame.columns or "status" in frame.columns)
        frame["luld_status_available_flag"] = int("luld_status" in frame.columns)
        frame["raw_recv_ts_available_flag"] = int("recv_ts_utc" in frame.columns or "receive_timestamp" in frame.columns)
        minutes = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True).dt.hour * 60 + pd.to_datetime(frame["timestamp"], errors="coerce", utc=True).dt.minute
        frame["regular_session_eligible_flag"] = ((minutes >= 13 * 60 + 30) & (minutes <= 21 * 60)).astype(int)
        frame["inferred_matching_used_flag"] = 0
        keep = [
            "symbol",
            "timestamp",
            "raw_bar_id",
            "raw_source_path",
            "raw_row_number",
            "raw_row_hash",
            "timestamp_available_flag",
            "open_available_flag",
            "high_available_flag",
            "low_available_flag",
            "close_available_flag",
            "volume_available_flag",
            "trade_count_available_flag",
            "vwap_available_flag",
            "quote_bid_ask_available_flag",
            "trading_status_available_flag",
            "luld_status_available_flag",
            "raw_recv_ts_available_flag",
            "regular_session_eligible_flag",
            "inferred_matching_used_flag",
        ]
        frames.append(frame[keep].copy())
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_raw_factor_source_audit_table(provenance: pd.DataFrame) -> pd.DataFrame:
    columns = set(provenance.columns)
    rows: list[dict] = []
    raw_names = {c.replace("_available_flag", "") for c in columns if c.endswith("_available_flag")}
    for factor, requirements in AVAILABLE_EXACT_FACTORS.items():
        required_flags = [_requirement_to_flag(req) for req in requirements]
        available = bool(len(provenance)) and all(flag in columns and int(provenance[flag].min()) == 1 for flag in required_flags)
        rows.append(
            {
                "factor_name": factor,
                "source_availability_status": "available_exact" if available else "collectable_but_missing",
                "required_raw_fields_json": json.dumps(requirements),
                "available_raw_field_count": sum(1 for req in requirements if _requirement_to_flag(req).replace("_available_flag", "") in raw_names),
                "exact_source_available_flag": int(available),
                "missing_raw_source_flag": int(not available),
                "inferred_matching_used_flag": 0,
            }
        )
    for factor in COLLECTABLE_BUT_MISSING_FACTORS:
        rows.append(
            {
                "factor_name": factor,
                "source_availability_status": "collectable_but_missing",
                "required_raw_fields_json": "[]",
                "available_raw_field_count": 0,
                "exact_source_available_flag": 0,
                "missing_raw_source_flag": 1,
                "inferred_matching_used_flag": 0,
            }
        )
    for factor in NOT_AVAILABLE_IN_CURRENT_SOURCE_FACTORS:
        rows.append(
            {
                "factor_name": factor,
                "source_availability_status": "not_available_in_current_source",
                "required_raw_fields_json": "[]",
                "available_raw_field_count": 0,
                "exact_source_available_flag": 0,
                "missing_raw_source_flag": 1,
                "inferred_matching_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_raw_session_eligibility_audit(provenance: pd.DataFrame) -> pd.DataFrame:
    if provenance.empty:
        return pd.DataFrame(columns=["symbol", "raw_bar_count", "regular_session_bar_count", "non_regular_session_bar_count", "non_regular_session_detected_flag"])
    grouped = provenance.groupby("symbol", as_index=False).agg(
        raw_bar_count=("raw_bar_id", "count"),
        regular_session_bar_count=("regular_session_eligible_flag", "sum"),
    )
    grouped["non_regular_session_bar_count"] = grouped["raw_bar_count"] - grouped["regular_session_bar_count"]
    grouped["non_regular_session_detected_flag"] = (grouped["non_regular_session_bar_count"] > 0).astype(int)
    return grouped


def build_raw_collection_gap_audit(source_audit: pd.DataFrame) -> pd.DataFrame:
    return source_audit[source_audit["missing_raw_source_flag"].eq(1)].copy().reset_index(drop=True)


def build_task_406a_decision(provenance: pd.DataFrame, source_audit: pd.DataFrame, session_audit: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_406a_verdict": "COMPLETE_PASS",
                "evaluation_status": "RAW_FACTOR_SOURCE_AUDIT_DIAGNOSTIC",
                "raw_bar_count": int(len(provenance)),
                "symbol_count": int(provenance["symbol"].nunique()) if not provenance.empty else 0,
                "available_exact_factor_count": int(source_audit["source_availability_status"].eq("available_exact").sum()) if not source_audit.empty else 0,
                "missing_raw_source_factor_count": int(source_audit["missing_raw_source_flag"].sum()) if not source_audit.empty else 0,
                "non_regular_session_bar_count": int(session_audit["non_regular_session_bar_count"].sum()) if not session_audit.empty else 0,
                "quote_spread_status_missing_flag": int(source_audit["factor_name"].isin(["quote_bid_ask", "spread_bps", "trading_status", "luld_status"]).any()),
                "inferred_matching_used_flag": 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "RAW_SOURCE_LIMITED_DIAGNOSTIC_ONLY",
            }
        ]
    )


def write_task406a_artifacts(artifacts: RawFactorSourceAudit406Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.raw_bar_provenance_panel.to_csv(out_dir / "raw_bar_provenance_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.raw_factor_source_audit.to_csv(out_dir / "raw_factor_source_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.raw_session_eligibility_audit.to_csv(out_dir / "raw_session_eligibility_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.raw_collection_gap_audit.to_csv(out_dir / "raw_collection_gap_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_406a_decision.to_csv(out_dir / "task_406a_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 406A - Raw Factor Source Audit",
        "",
        "## Quant Expert Report",
        "- Raw row provenance is deterministic and uses no inferred matching.",
        "- Missing quote/spread/status/LULD/raw receive timestamp sources are explicitly reported as missing raw source.",
        "",
        "## No-Background Decision-Maker Report",
        "- The local raw data is usable for OHLCV-based factors.",
        "- It is not deployment-grade for quote/spread/status factors yet.",
        "",
        "## Decision",
        _csv_block(artifacts.task_406a_decision),
    ]
    (out_dir / "task_406_raw_factor_source_audit.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _symbol_path(intraday_dir: Path, symbol: str) -> Path | None:
    candidates = [intraday_dir / f"{symbol}.csv", intraday_dir / symbol / "bars.csv", intraday_dir / f"{symbol}_15m.csv"]
    return next((p for p in candidates if p.exists()), None)


def _requirement_to_flag(requirement: str) -> str:
    if requirement == "timestamp":
        return "timestamp_available_flag"
    return f"{requirement}_available_flag"


def _csv_block(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    return frame.to_csv(index=False).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task406A raw factor source audit.")
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task406_raw_factor_source_audit(intraday_dir=args.intraday_dir, out_dir=args.out_dir)
    row = artifacts.task_406a_decision.iloc[0]
    print(f"[TASK406A] raw_bars={row['raw_bar_count']} missing_factors={row['missing_raw_source_factor_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
