from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report
from src.backtest.build_task538_fundamental_factor_source_audit import download_companyfacts


TASK539_OUT = Path("docs/reports/task_539_market_cap_shares_source")
COMPANYFACTS_DIR = Path("data/raw/fundamental/sec_companyfacts/companyfacts")
DAILY_DIR = Path("data/raw/us_daily_breadth_top500")
TASK538_CIK = Path("docs/reports/task_538_fundamental_factor_source_audit/fundamental_cik_coverage_audit.csv")
TASK505_PANEL = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_panel.csv")

SHARES_CONCEPTS = [
    "CommonStockSharesOutstanding",
    "EntityCommonStockSharesOutstanding",
    "CommonStockSharesIssued",
]


def build_task539_market_cap_shares_source(
    *,
    companyfacts_dir: Path = COMPANYFACTS_DIR,
    daily_dir: Path = DAILY_DIR,
    cik_coverage_path: Path = TASK538_CIK,
    task505_panel_path: Path = TASK505_PANEL,
    out_dir: Path = TASK539_OUT,
) -> dict[str, pd.DataFrame]:
    cik_coverage = pd.read_csv(cik_coverage_path) if cik_coverage_path.exists() else pd.DataFrame()
    ensure_task505_companyfacts(task505_panel_path, cik_coverage, companyfacts_dir)
    shares = extract_shares_outstanding_panel(companyfacts_dir)
    price = load_daily_prices_for_symbols(daily_dir, sorted(shares["symbol"].dropna().unique().tolist()))
    market_cap = build_market_cap_panel(shares, price)
    task505_join = join_market_cap_to_task505(task505_panel_path, market_cap)
    source_audit = build_source_audit(cik_coverage, shares, price, market_cap)
    factor_readiness = build_market_cap_factor_readiness(market_cap, task505_join)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task539",
                "shares_source_available_flag": int(not shares.empty),
                "daily_price_source_available_flag": int(not price.empty),
                "market_cap_panel_available_flag": int(not market_cap.empty),
                "task505_market_cap_coverage_rate": float(task505_join["market_cap_available_flag"].mean()) if not task505_join.empty else 0.0,
                "market_cap_approximated_flag": 0,
                "crsp_compustat_grade_flag": 0,
                "strategy_acceptance_status": "MARKET_CAP_SOURCE_PARTIAL_READY_SEC_FACT_BASED",
            }
        ]
    )
    artifacts = {
        "shares_outstanding_source_audit": source_audit,
        "shares_outstanding_panel": shares,
        "daily_price_source_panel": price,
        "market_cap_panel": market_cap,
        "task505_market_cap_join_audit": task505_join,
        "market_cap_factor_readiness_audit": factor_readiness,
        "task_539_decision": decision,
    }
    write_task539(out_dir, artifacts)
    return artifacts


def ensure_task505_companyfacts(task505_panel_path: Path, cik_coverage: pd.DataFrame, companyfacts_dir: Path) -> None:
    if not task505_panel_path.exists() or cik_coverage.empty:
        return
    panel_symbols = pd.read_csv(task505_panel_path, usecols=lambda col: col == "symbol")
    symbols = sorted(panel_symbols["symbol"].dropna().astype(str).str.upper().unique().tolist())
    symbol_to_cik = dict(zip(cik_coverage["symbol"].astype(str).str.upper(), cik_coverage["cik10"].astype(str).str.zfill(10)))
    for symbol in symbols:
        cik10 = symbol_to_cik.get(symbol)
        if not cik10:
            continue
        path = companyfacts_dir / f"{symbol}_{cik10}.json"
        if path.exists():
            continue
        download_companyfacts(symbol, cik10, companyfacts_dir.parent)


def extract_shares_outstanding_panel(companyfacts_dir: Path) -> pd.DataFrame:
    rows = []
    for path in companyfacts_dir.glob("*.json") if companyfacts_dir.exists() else []:
        symbol = path.name.split("_", 1)[0].upper()
        cik10 = path.stem.split("_", 1)[1] if "_" in path.stem else ""
        payload = json.loads(path.read_text(encoding="utf-8"))
        facts = payload.get("facts", {}).get("us-gaap", {})
        for concept in SHARES_CONCEPTS:
            if concept not in facts:
                continue
            for unit, records in facts.get(concept, {}).get("units", {}).items():
                if "shares" not in unit.lower():
                    continue
                for rec in records:
                    val = rec.get("val")
                    end = rec.get("end")
                    filed = rec.get("filed")
                    if val is None or not end:
                        continue
                    rows.append(
                        {
                            "symbol": symbol,
                            "cik10": cik10,
                            "concept": concept,
                            "unit": unit,
                            "period_end": end,
                            "filed_date": filed,
                            "shares_outstanding": val,
                            "source_path": str(path),
                            "source_type": "SEC_companyfacts_us_gaap",
                        }
                    )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["period_end"] = pd.to_datetime(frame["period_end"], errors="coerce")
    frame["filed_date"] = pd.to_datetime(frame["filed_date"], errors="coerce")
    frame["shares_outstanding"] = pd.to_numeric(frame["shares_outstanding"], errors="coerce")
    frame = frame.dropna(subset=["symbol", "period_end", "shares_outstanding"]).copy()
    frame = frame.sort_values(["symbol", "period_end", "filed_date", "concept"]).drop_duplicates(["symbol", "period_end"], keep="last")
    return frame.reset_index(drop=True)


def load_daily_prices_for_symbols(daily_dir: Path, symbols: list[str]) -> pd.DataFrame:
    rows = []
    for symbol in symbols:
        path = daily_dir / f"{symbol}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        if "timestamp" not in frame.columns or "close" not in frame.columns:
            continue
        frame = frame[["timestamp", "close"]].copy()
        frame["symbol"] = symbol
        frame["date"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").dt.tz_convert(None)
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame["price_source_path"] = str(path)
        rows.append(frame.dropna(subset=["date", "close"]))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_market_cap_panel(shares: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    if shares.empty or prices.empty:
        return pd.DataFrame()
    rows = []
    for symbol, price_subset in prices.groupby("symbol"):
        share_subset = shares[shares["symbol"].eq(symbol)].sort_values("period_end").copy()
        if share_subset.empty:
            continue
        merged = pd.merge_asof(
            price_subset.sort_values("date"),
            share_subset.sort_values("period_end"),
            left_on="date",
            right_on="period_end",
            by="symbol",
            direction="backward",
        )
        merged["market_cap"] = merged["close"] * merged["shares_outstanding"]
        merged["shares_asof_lag_days"] = (merged["date"] - merged["period_end"]).dt.days
        rows.append(merged)
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if out.empty:
        return out
    out["market_cap_available_flag"] = out["market_cap"].notna().astype(int)
    out["market_cap_source_grade"] = "SEC_companyfacts_shares_x_daily_close"
    return out


def join_market_cap_to_task505(task505_panel_path: Path, market_cap: pd.DataFrame) -> pd.DataFrame:
    if not task505_panel_path.exists() or market_cap.empty:
        return pd.DataFrame()
    panel = pd.read_csv(task505_panel_path, usecols=lambda col: col in {"lifecycle_id", "symbol", "entry_ts"})
    panel["entry_date"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce").dt.tz_convert(None)
    rows = []
    for symbol, subset in panel.groupby("symbol"):
        cap_subset = market_cap[market_cap["symbol"].eq(symbol)].sort_values("date")
        if cap_subset.empty:
            subset = subset.copy()
            subset["market_cap_available_flag"] = 0
            rows.append(subset)
            continue
        joined = pd.merge_asof(
            subset.sort_values("entry_date"),
            cap_subset[["symbol", "date", "market_cap", "shares_outstanding", "period_end", "shares_asof_lag_days", "market_cap_source_grade"]].sort_values("date"),
            left_on="entry_date",
            right_on="date",
            by="symbol",
            direction="backward",
        )
        joined["market_cap_available_flag"] = joined["market_cap"].notna().astype(int)
        rows.append(joined)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_source_audit(cik_coverage: pd.DataFrame, shares: pd.DataFrame, price: pd.DataFrame, market_cap: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"source_name": "SEC Company Facts shares concepts", "available_flag": int(not shares.empty), "row_count": int(len(shares)), "limitation": "reported SEC fact dates, not CRSP daily share history"},
            {"source_name": "daily close prices", "available_flag": int(not price.empty), "row_count": int(len(price)), "limitation": "daily close market cap proxy, not intraday market cap"},
            {"source_name": "market cap panel", "available_flag": int(not market_cap.empty), "row_count": int(len(market_cap)), "limitation": "shares carried forward from latest reported period"},
            {"source_name": "CIK coverage", "available_flag": int(not cik_coverage.empty), "row_count": int(len(cik_coverage)), "limitation": "SEC filers only"},
        ]
    )


def build_market_cap_factor_readiness(market_cap: pd.DataFrame, task505_join: pd.DataFrame) -> pd.DataFrame:
    coverage = float(task505_join["market_cap_available_flag"].mean()) if not task505_join.empty else 0.0
    return pd.DataFrame(
        [
            {"factor_name": "size_market_cap", "current_available_flag": int(coverage > 0), "coverage_rate": coverage, "ready_for_diagnostic_flag": int(coverage > 0.8), "ready_for_crsp_compustat_grade_flag": 0},
            {"factor_name": "book_to_market", "current_available_flag": int(coverage > 0), "coverage_rate": coverage, "ready_for_diagnostic_flag": int(coverage > 0.8), "ready_for_crsp_compustat_grade_flag": 0},
            {"factor_name": "full_factor_premium", "current_available_flag": 0, "coverage_rate": coverage, "ready_for_diagnostic_flag": 0, "ready_for_crsp_compustat_grade_flag": 0},
        ]
    )


def write_task539(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_539_decision"].iloc[0].to_dict()
    write_standard_report(
        out_dir / "task_539_market_cap_shares_source.md",
        title="Task 539 Market Cap Shares Source",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Shares source available: {decision['shares_source_available_flag']}",
            f"Market cap panel available: {decision['market_cap_panel_available_flag']}",
            f"Task505 market cap coverage: {decision['task505_market_cap_coverage_rate']:.2%}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task539 extracts shares outstanding from SEC Company Facts and combines them with existing daily close prices to create a diagnostic market-cap panel.",
            "This is not CRSP/Compustat-grade daily shares. Shares are carried forward from reported SEC fact periods, so it is acceptable for diagnostic size/book-to-market work but not for final institutional factor claims.",
            "No shares or market-cap values are fabricated. Missing source grade remains explicit.",
        ],
        decision_maker_lines=[
            "We can now calculate a practical market-cap proxy for covered symbols.",
            "This helps start size and book-to-market diagnostics, but it is not yet the gold-standard professional dataset.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_task539_market_cap_shares_source()


if __name__ == "__main__":
    main()
