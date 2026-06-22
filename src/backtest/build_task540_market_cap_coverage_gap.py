from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task539_market_cap_shares_source import (
    COMPANYFACTS_DIR,
    DAILY_DIR,
    TASK505_PANEL,
    build_market_cap_factor_readiness,
    build_market_cap_panel,
    join_market_cap_to_task505,
    load_daily_prices_for_symbols,
)
from src.backtest.task_report_utils import write_standard_report


TASK540_OUT = Path("docs/reports/task_540_market_cap_coverage_gap")

PRIMARY_SHARES = ["CommonStockSharesOutstanding", "EntityCommonStockSharesOutstanding", "CommonStockSharesIssued"]
FALLBACK_SHARES = [
    "WeightedAverageNumberOfSharesOutstandingBasic",
    "WeightedAverageNumberOfDilutedSharesOutstanding",
    "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
]


def build_task540_market_cap_coverage_gap(
    *,
    companyfacts_dir: Path = COMPANYFACTS_DIR,
    daily_dir: Path = DAILY_DIR,
    task505_panel_path: Path = TASK505_PANEL,
    out_dir: Path = TASK540_OUT,
) -> dict[str, pd.DataFrame]:
    gap_before = load_gap_before()
    shares = extract_expanded_shares_panel(companyfacts_dir)
    price = load_daily_prices_for_symbols(daily_dir, sorted(shares["symbol"].dropna().unique().tolist()))
    market_cap = build_market_cap_panel(shares, price)
    joined = join_market_cap_to_task505(task505_panel_path, market_cap)
    gap_after = build_gap_decomposition(joined, shares, price)
    readiness = build_market_cap_factor_readiness(market_cap, joined)
    coverage = float(joined["market_cap_available_flag"].mean()) if not joined.empty else 0.0
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task540",
                "pre_task539_coverage_rate": float(gap_before["market_cap_available_flag"].mean()) if not gap_before.empty else pd.NA,
                "post_expanded_coverage_rate": coverage,
                "coverage_90pct_pass_flag": int(coverage >= 0.90),
                "fallback_weighted_average_shares_used_flag": int((shares["share_source_grade"] == "fallback_weighted_average_shares").any()) if not shares.empty else 0,
                "missing_data_approximated_flag": 0,
                "crsp_compustat_grade_flag": 0,
                "strategy_acceptance_status": "MARKET_CAP_COVERAGE_90_PASS_DIAGNOSTIC_SOURCE_GRADE_LIMITED"
                if coverage >= 0.90
                else "MARKET_CAP_COVERAGE_GAP_EXPLAINED_BELOW_90",
            }
        ]
    )
    artifacts = {
        "expanded_shares_outstanding_panel": shares,
        "expanded_market_cap_panel": market_cap,
        "market_cap_coverage_gap_before": gap_before,
        "market_cap_coverage_gap_after": gap_after,
        "task505_market_cap_expanded_join_audit": joined,
        "market_cap_factor_readiness_after_expansion": readiness,
        "task_540_decision": decision,
    }
    write_task540(out_dir, artifacts)
    return artifacts


def load_gap_before() -> pd.DataFrame:
    path = Path("docs/reports/task_539_market_cap_shares_source/task505_market_cap_join_audit.csv")
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def extract_expanded_shares_panel(companyfacts_dir: Path) -> pd.DataFrame:
    rows = []
    for path in companyfacts_dir.glob("*.json") if companyfacts_dir.exists() else []:
        symbol = path.name.split("_", 1)[0].upper()
        cik10 = path.stem.split("_", 1)[1] if "_" in path.stem else ""
        payload = json.loads(path.read_text(encoding="utf-8"))
        for taxonomy, facts in payload.get("facts", {}).items():
            for concept in [*PRIMARY_SHARES, *FALLBACK_SHARES]:
                if concept not in facts:
                    continue
                grade = "primary_shares_outstanding" if concept in PRIMARY_SHARES else "fallback_weighted_average_shares"
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
                                "taxonomy": taxonomy,
                                "concept": concept,
                                "unit": unit,
                                "period_end": end,
                                "filed_date": filed,
                                "shares_outstanding": val,
                                "source_path": str(path),
                                "source_type": f"SEC_companyfacts_{taxonomy}",
                                "share_source_grade": grade,
                            }
                        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["period_end"] = pd.to_datetime(frame["period_end"], errors="coerce")
    frame["filed_date"] = pd.to_datetime(frame["filed_date"], errors="coerce")
    frame["shares_outstanding"] = pd.to_numeric(frame["shares_outstanding"], errors="coerce")
    frame["source_priority"] = frame["share_source_grade"].map({"primary_shares_outstanding": 0, "fallback_weighted_average_shares": 1}).fillna(9)
    frame = frame.dropna(subset=["symbol", "period_end", "shares_outstanding"]).copy()
    frame = frame.sort_values(["symbol", "period_end", "source_priority", "filed_date"]).drop_duplicates(["symbol", "period_end"], keep="first")
    return frame.drop(columns=["source_priority"]).reset_index(drop=True)


def build_gap_decomposition(joined: pd.DataFrame, shares: pd.DataFrame, price: pd.DataFrame) -> pd.DataFrame:
    if joined.empty:
        return pd.DataFrame()
    rows = []
    share_symbols = set(shares["symbol"].astype(str)) if not shares.empty else set()
    price_symbols = set(price["symbol"].astype(str)) if not price.empty else set()
    for symbol, subset in joined.groupby("symbol"):
        missing = subset[subset["market_cap_available_flag"].eq(0)]
        if missing.empty:
            reason = "covered"
        elif symbol not in share_symbols:
            reason = "shares_source_missing"
        elif symbol not in price_symbols:
            reason = "daily_price_source_missing"
        else:
            reason = "asof_date_before_first_share_fact_or_join_gap"
        rows.append(
            {
                "symbol": symbol,
                "lifecycle_count": int(len(subset)),
                "missing_market_cap_count": int(len(missing)),
                "coverage_rate": float(subset["market_cap_available_flag"].mean()),
                "gap_reason": reason,
            }
        )
    return pd.DataFrame(rows)


def write_task540(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_540_decision"].iloc[0].to_dict()
    write_standard_report(
        out_dir / "task_540_market_cap_coverage_gap.md",
        title="Task 540 Market Cap Coverage Gap",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Pre coverage: {decision['pre_task539_coverage_rate']:.2%}",
            f"Post coverage: {decision['post_expanded_coverage_rate']:.2%}",
            f"90pct pass: {decision['coverage_90pct_pass_flag']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task540 expands SEC shares extraction to include DEI EntityCommonStockSharesOutstanding and clearly graded weighted-average share fallbacks.",
            "Fallback weighted-average shares are not fabricated, but they are lower-grade than true shares outstanding. CRSP/Compustat-grade remains false.",
            "The purpose is coverage diagnosis and size/book-to-market diagnostic readiness, not institutional factor-model finalization.",
        ],
        decision_maker_lines=[
            "We explained the market-cap coverage gap and improved coverage without inventing missing values.",
            "If coverage passes, it is still a diagnostic source because some rows use lower-grade reported share concepts.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_task540_market_cap_coverage_gap()


if __name__ == "__main__":
    main()
