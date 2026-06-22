from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK538_OUT = Path("docs/reports/task_538_fundamental_factor_source_audit")
FUND_RAW_DIR = Path("data/raw/fundamental/sec_companyfacts")
THEME_UNIVERSE = Path("data/raw/theme_universe_10x7.csv")
TASK505_PANEL = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_panel.csv")
SEC_TICKER_CIK_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"
USER_AGENT = "foreign-stock-quant-research contact@example.com"


US_GAAP_CONCEPTS = {
    "assets": ["Assets"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "revenue": ["Revenues", "SalesRevenueNet"],
    "net_income": ["NetIncomeLoss"],
    "operating_income": ["OperatingIncomeLoss"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
}


def build_task538_fundamental_factor_source_audit(
    *,
    theme_universe_path: Path = THEME_UNIVERSE,
    task505_panel_path: Path = TASK505_PANEL,
    out_dir: Path = TASK538_OUT,
    raw_dir: Path = FUND_RAW_DIR,
    max_download_symbols: int = 25,
) -> dict[str, pd.DataFrame]:
    symbols = load_target_symbols(theme_universe_path, task505_panel_path)
    cik_map, cik_audit = download_ticker_cik_map(raw_dir)
    coverage = build_cik_coverage(symbols, cik_map)
    selected = coverage[coverage["cik_available_flag"].eq(1)].head(max_download_symbols).copy()
    raw_audit_rows = []
    concept_rows = []
    for row in selected.to_dict(orient="records"):
        raw_json, raw_audit = download_companyfacts(str(row["symbol"]), str(row["cik10"]), raw_dir)
        raw_audit_rows.append(raw_audit)
        concept_rows.append(extract_concept_availability(str(row["symbol"]), str(row["cik10"]), raw_json))
    raw_audit_df = pd.DataFrame(raw_audit_rows)
    concept_df = pd.DataFrame(concept_rows)
    source_matrix = build_source_matrix(coverage, raw_audit_df, concept_df)
    factor_readiness = build_factor_readiness(concept_df)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task538",
                "target_symbol_count": int(len(symbols)),
                "cik_coverage_count": int(coverage["cik_available_flag"].sum()),
                "companyfacts_downloaded_count": int(raw_audit_df["download_success_flag"].sum()) if not raw_audit_df.empty else 0,
                "fundamental_raw_source_available_flag": int(not concept_df.empty and int(raw_audit_df["download_success_flag"].sum()) > 0),
                "full_factor_premium_ready_flag": int(factor_readiness["ready_for_full_factor_premium_flag"].min()) if not factor_readiness.empty else 0,
                "missing_data_approximated_flag": 0,
                "strategy_acceptance_status": "FUNDAMENTAL_SOURCE_PARTIAL_READY_FULL_FACTOR_PREMIUM_NOT_READY",
            }
        ]
    )
    artifacts = {
        "fundamental_target_symbol_universe": pd.DataFrame({"symbol": symbols}),
        "sec_ticker_cik_source_audit": cik_audit,
        "fundamental_cik_coverage_audit": coverage,
        "sec_companyfacts_download_audit": raw_audit_df,
        "fundamental_concept_availability_audit": concept_df,
        "fundamental_factor_readiness_audit": factor_readiness,
        "fundamental_source_matrix": source_matrix,
        "task_538_decision": decision,
    }
    write_task538(out_dir, artifacts)
    return artifacts


def load_target_symbols(theme_universe_path: Path, task505_panel_path: Path) -> list[str]:
    symbols: set[str] = set()
    if theme_universe_path.exists():
        theme = pd.read_csv(theme_universe_path)
        if "symbol" in theme.columns:
            symbols.update(theme["symbol"].dropna().astype(str).str.upper().tolist())
    if task505_panel_path.exists():
        panel = pd.read_csv(task505_panel_path, usecols=lambda c: c in {"symbol"})
        if "symbol" in panel.columns:
            symbols.update(panel["symbol"].dropna().astype(str).str.upper().tolist())
    return sorted(symbols)


def sec_headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate", "Host": "www.sec.gov"}


def download_ticker_cik_map(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / "company_tickers.json"
    response = requests.get(SEC_TICKER_CIK_URL, headers=sec_headers(), timeout=60)
    response.raise_for_status()
    path.write_bytes(response.content)
    payload = response.json()
    rows = []
    for item in payload.values():
        cik = str(item.get("cik_str", "")).zfill(10)
        rows.append({"symbol": str(item.get("ticker", "")).upper(), "title": item.get("title", ""), "cik10": cik})
    frame = pd.DataFrame(rows)
    audit = pd.DataFrame(
        [
            {
                "source_name": "SEC company_tickers.json",
                "source_url": SEC_TICKER_CIK_URL,
                "raw_path": str(path),
                "row_count": int(len(frame)),
                "download_success_flag": int(not frame.empty),
            }
        ]
    )
    return frame, audit


def build_cik_coverage(symbols: list[str], cik_map: pd.DataFrame) -> pd.DataFrame:
    target = pd.DataFrame({"symbol": symbols})
    merged = target.merge(cik_map, on="symbol", how="left")
    merged["cik_available_flag"] = merged["cik10"].notna().astype(int)
    return merged


def download_companyfacts(symbol: str, cik10: str, raw_dir: Path) -> tuple[dict[str, Any], dict[str, object]]:
    symbol_dir = raw_dir / "companyfacts"
    symbol_dir.mkdir(parents=True, exist_ok=True)
    path = symbol_dir / f"{symbol}_{cik10}.json"
    url = SEC_COMPANY_FACTS_URL.format(cik10=cik10)
    headers = sec_headers()
    headers["Host"] = "data.sec.gov"
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        path.write_bytes(response.content)
        payload = response.json()
        return payload, {"symbol": symbol, "cik10": cik10, "source_url": url, "raw_path": str(path), "download_success_flag": 1, "error": ""}
    except Exception as exc:
        return {}, {"symbol": symbol, "cik10": cik10, "source_url": url, "raw_path": str(path), "download_success_flag": 0, "error": str(exc)}


def extract_concept_availability(symbol: str, cik10: str, payload: dict[str, Any]) -> dict[str, object]:
    facts = payload.get("facts", {}).get("us-gaap", {}) if payload else {}
    out: dict[str, object] = {"symbol": symbol, "cik10": cik10, "companyfacts_available_flag": int(bool(facts))}
    for factor_name, concepts in US_GAAP_CONCEPTS.items():
        matched = [concept for concept in concepts if concept in facts]
        out[f"{factor_name}_available_flag"] = int(bool(matched))
        out[f"{factor_name}_concept"] = "|".join(matched)
        out[f"{factor_name}_fact_count"] = int(sum(len(facts.get(concept, {}).get("units", {}).get(unit, [])) for concept in matched for unit in facts.get(concept, {}).get("units", {})))
    return out


def build_factor_readiness(concept_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    factor_requirements = {
        "size_market_cap": {"raw_required": "shares_outstanding_or_market_cap", "current_available_flag": 0, "reason": "market_cap_raw_source_missing"},
        "book_to_market": {"raw_required": "equity + market_cap", "current_available_flag": int(not concept_df.empty and concept_df["equity_available_flag"].mean() > 0), "reason": "market_cap_missing_even_if_equity_exists"},
        "profitability": {"raw_required": "net_income or operating_income + equity/assets", "current_available_flag": int(not concept_df.empty and concept_df[["net_income_available_flag", "operating_income_available_flag"]].max(axis=1).mean() > 0), "reason": ""},
        "investment_asset_growth": {"raw_required": "assets time series", "current_available_flag": int(not concept_df.empty and concept_df["assets_available_flag"].mean() > 0), "reason": ""},
        "earnings_revision": {"raw_required": "analyst estimates/revisions", "current_available_flag": 0, "reason": "estimate_revision_source_missing"},
    }
    for factor, meta in factor_requirements.items():
        rows.append(
            {
                "factor_name": factor,
                "raw_required": meta["raw_required"],
                "current_available_flag": int(meta["current_available_flag"]),
                "blocked_reason": meta["reason"],
                "ready_for_full_factor_premium_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_source_matrix(coverage: pd.DataFrame, raw_audit: pd.DataFrame, concept_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"source": "SEC ticker CIK map", "available_flag": int(not coverage.empty), "role": "symbol_to_cik", "limitation": "US listed SEC filers only"},
            {"source": "SEC companyfacts", "available_flag": int(not raw_audit.empty and raw_audit["download_success_flag"].sum() > 0), "role": "financial_statement_facts", "limitation": "taxonomy normalization required"},
            {"source": "market_cap/shares_outstanding", "available_flag": 0, "role": "size and book-to-market denominator", "limitation": "not collected in this task"},
            {"source": "analyst estimates", "available_flag": 0, "role": "earnings revision factor", "limitation": "requires separate vendor/source"},
            {"source": "concept availability panel", "available_flag": int(not concept_df.empty), "role": "fundamental coverage audit", "limitation": "coverage sample limited by max_download_symbols"},
        ]
    )


def write_task538(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_538_decision"].iloc[0].to_dict()
    write_standard_report(
        out_dir / "task_538_fundamental_factor_source_audit.md",
        title="Task 538 Fundamental Factor Source Audit",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Target symbols: {decision['target_symbol_count']}",
            f"CIK coverage: {decision['cik_coverage_count']}",
            f"Companyfacts downloaded: {decision['companyfacts_downloaded_count']}",
            f"Full factor premium ready: {decision['full_factor_premium_ready_flag']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task538 uses SEC company_tickers and Company Facts APIs as a first raw fundamental source for the theme and Task505 universe.",
            "SEC XBRL facts provide financial statement concepts such as assets, equity, revenue, income, and cash flow, but they do not by themselves complete market-cap, book-to-market, or earnings-revision factors.",
            "Missing market cap/shares and analyst estimate revisions are not approximated. Full Fama-MacBeth factor premium validation remains blocked until those sources are collected.",
        ],
        decision_maker_lines=[
            "We started collecting real fundamental data instead of pretending it exists.",
            "SEC data gives us company financial statement facts, but not every factor needed for a full professional factor-premium test.",
            "The next data gap is market cap/shares and estimate revision data.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-download-symbols", type=int, default=25)
    args = parser.parse_args()
    build_task538_fundamental_factor_source_audit(max_download_symbols=args.max_download_symbols)


if __name__ == "__main__":
    main()
