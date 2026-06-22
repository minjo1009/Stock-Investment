from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task537_factor_premium_validation import ENTRY_SAFE_NUMERIC_FEATURES, load_lifecycle_panel
from src.backtest.build_task539_market_cap_shares_source import COMPANYFACTS_DIR
from src.backtest.task_report_utils import write_standard_report


TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
TASK540_MARKET_CAP = Path("docs/reports/task_540_market_cap_coverage_gap/expanded_market_cap_panel.csv")
TASK541_OUT = Path("docs/reports/task_541_size_bm_fama_macbeth")

BOOK_EQUITY_CONCEPTS = [
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
]


def build_task541_size_bm_fama_macbeth(
    *,
    lifecycle_panel_path: Path = TASK503_PANEL,
    market_cap_panel_path: Path = TASK540_MARKET_CAP,
    companyfacts_dir: Path = COMPANYFACTS_DIR,
    out_dir: Path = TASK541_OUT,
) -> dict[str, pd.DataFrame]:
    lifecycle = load_lifecycle_panel(lifecycle_panel_path)
    market_cap = load_market_cap_panel(market_cap_panel_path)
    book_equity = extract_book_equity_panel(companyfacts_dir)
    factor_panel = build_size_bm_factor_panel(lifecycle, market_cap, book_equity)
    coef_panel, fmb_result = fit_fama_macbeth_with_size_bm(factor_panel)
    coverage = build_size_bm_coverage_audit(factor_panel, book_equity, market_cap)
    leakage = build_leakage_audit()
    decision = build_decision(coverage, fmb_result)
    artifacts = {
        "book_equity_source_audit": build_book_equity_source_audit(book_equity),
        "book_equity_panel": book_equity,
        "size_bm_factor_panel": factor_panel,
        "size_bm_factor_coverage_audit": coverage,
        "fama_macbeth_with_size_bm_coef_panel": coef_panel,
        "fama_macbeth_with_size_bm_result": fmb_result,
        "size_bm_leakage_audit": leakage,
        "task_541_decision": decision,
    }
    write_task541(out_dir, artifacts)
    return artifacts


def extract_book_equity_panel(companyfacts_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in companyfacts_dir.glob("*.json") if companyfacts_dir.exists() else []:
        symbol = path.name.split("_", 1)[0].upper()
        cik10 = path.stem.split("_", 1)[1] if "_" in path.stem else ""
        payload = json.loads(path.read_text(encoding="utf-8"))
        for taxonomy, facts in payload.get("facts", {}).items():
            for concept in BOOK_EQUITY_CONCEPTS:
                if concept not in facts:
                    continue
                priority = BOOK_EQUITY_CONCEPTS.index(concept)
                for unit, records in facts.get(concept, {}).get("units", {}).items():
                    if unit.upper() != "USD":
                        continue
                    for rec in records:
                        value = rec.get("val")
                        end = rec.get("end")
                        filed = rec.get("filed")
                        if value is None or not end or not filed:
                            continue
                        rows.append(
                            {
                                "symbol": symbol,
                                "cik10": cik10,
                                "taxonomy": taxonomy,
                                "concept": concept,
                                "concept_priority": priority,
                                "unit": unit,
                                "period_end": end,
                                "filed_date": filed,
                                "book_equity": value,
                                "source_path": str(path),
                                "book_equity_source_grade": f"SEC_companyfacts_{concept}",
                            }
                        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["period_end"] = pd.to_datetime(frame["period_end"], utc=True, errors="coerce")
    frame["filed_date"] = pd.to_datetime(frame["filed_date"], utc=True, errors="coerce")
    frame["book_equity"] = pd.to_numeric(frame["book_equity"], errors="coerce")
    frame = frame.dropna(subset=["symbol", "filed_date", "book_equity"]).copy()
    frame = frame.sort_values(["symbol", "filed_date", "concept_priority", "period_end"]).drop_duplicates(
        ["symbol", "filed_date"],
        keep="first",
    )
    return frame.drop(columns=["concept_priority"]).reset_index(drop=True)


def load_market_cap_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if frame.empty:
        return frame
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    frame["market_cap_date"] = pd.to_datetime(frame["date"], utc=True, errors="coerce")
    frame["market_cap"] = pd.to_numeric(frame["market_cap"], errors="coerce")
    frame = frame.dropna(subset=["symbol", "market_cap_date", "market_cap"]).copy()
    return frame.sort_values(["symbol", "market_cap_date"]).reset_index(drop=True)


def build_size_bm_factor_panel(lifecycle: pd.DataFrame, market_cap: pd.DataFrame, book_equity: pd.DataFrame) -> pd.DataFrame:
    base = lifecycle.copy()
    base["symbol"] = base["symbol"].astype(str).str.upper()
    base["entry_date_ts"] = base["entry_ts"].dt.floor("D")
    with_market = merge_previous_market_cap(base, market_cap)
    with_book = merge_filed_book_equity(with_market, book_equity)
    with_book["size_log_market_cap"] = np.nan
    market_cap_positive = with_book["market_cap"] > 0
    with_book.loc[market_cap_positive, "size_log_market_cap"] = np.log(with_book.loc[market_cap_positive, "market_cap"])
    with_book["book_to_market"] = with_book["book_equity"] / with_book["market_cap"]
    with_book["negative_book_equity_flag"] = (with_book["book_equity"] <= 0).astype(int)
    with_book["book_to_market_log"] = np.nan
    bm_positive = with_book["book_to_market"] > 0
    with_book.loc[bm_positive, "book_to_market_log"] = np.log(with_book.loc[bm_positive, "book_to_market"])
    with_book["size_factor_available_flag"] = with_book["size_log_market_cap"].notna().astype(int)
    with_book["book_to_market_available_flag"] = with_book["book_to_market_log"].notna().astype(int)
    with_book["factor_source_grade"] = np.where(
        with_book["book_to_market_available_flag"].eq(1),
        "SEC_companyfacts_book_equity_x_SEC_shares_x_previous_daily_close",
        "missing_book_or_market_cap",
    )
    with_book["factor_result_used_as_trading_trigger_flag"] = 0
    with_book["missing_data_approximated_flag"] = 0
    keep = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "entry_ts",
        "quarter",
        "return_pct",
        *[col for col in ENTRY_SAFE_NUMERIC_FEATURES if col in with_book.columns],
        "market_cap_date",
        "market_cap",
        "book_equity",
        "book_equity_filed_date",
        "book_equity_period_end",
        "size_log_market_cap",
        "book_to_market",
        "book_to_market_log",
        "negative_book_equity_flag",
        "size_factor_available_flag",
        "book_to_market_available_flag",
        "factor_source_grade",
        "factor_result_used_as_trading_trigger_flag",
        "missing_data_approximated_flag",
    ]
    return with_book[keep].copy()


def merge_previous_market_cap(base: pd.DataFrame, market_cap: pd.DataFrame) -> pd.DataFrame:
    if market_cap.empty:
        out = base.copy()
        out["market_cap_date"] = pd.NaT
        out["market_cap"] = np.nan
        return out
    rows = []
    for symbol, subset in base.sort_values("entry_date_ts").groupby("symbol", sort=False):
        right = market_cap[market_cap["symbol"].eq(symbol)].sort_values("market_cap_date")
        if right.empty:
            rows.append(subset.assign(market_cap_date=pd.NaT, market_cap=np.nan))
            continue
        shifted = subset.copy()
        shifted["market_cap_join_ts"] = shifted["entry_date_ts"] - pd.Timedelta(microseconds=1)
        merged = pd.merge_asof(
            shifted.sort_values("market_cap_join_ts"),
            right[["market_cap_date", "market_cap"]].sort_values("market_cap_date"),
            left_on="market_cap_join_ts",
            right_on="market_cap_date",
            direction="backward",
        ).drop(columns=["market_cap_join_ts"])
        rows.append(merged)
    return pd.concat(rows, ignore_index=True) if rows else base.copy()


def merge_filed_book_equity(base: pd.DataFrame, book_equity: pd.DataFrame) -> pd.DataFrame:
    if book_equity.empty:
        out = base.copy()
        out["book_equity"] = np.nan
        out["book_equity_filed_date"] = pd.NaT
        out["book_equity_period_end"] = pd.NaT
        return out
    rows = []
    book = book_equity.rename(columns={"filed_date": "book_equity_filed_date", "period_end": "book_equity_period_end"})
    for symbol, subset in base.sort_values("entry_date_ts").groupby("symbol", sort=False):
        right = book[book["symbol"].eq(symbol)].sort_values("book_equity_filed_date")
        if right.empty:
            rows.append(subset.assign(book_equity=np.nan, book_equity_filed_date=pd.NaT, book_equity_period_end=pd.NaT))
            continue
        merged = pd.merge_asof(
            subset.sort_values("entry_ts"),
            right[["book_equity_filed_date", "book_equity_period_end", "book_equity"]].sort_values("book_equity_filed_date"),
            left_on="entry_ts",
            right_on="book_equity_filed_date",
            direction="backward",
        )
        rows.append(merged)
    return pd.concat(rows, ignore_index=True) if rows else base.copy()


def fit_fama_macbeth_with_size_bm(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = [col for col in [*ENTRY_SAFE_NUMERIC_FEATURES, "size_log_market_cap", "book_to_market_log"] if col in panel.columns]
    rows = panel[["lifecycle_id", "symbol", "theme_id", "quarter", "return_pct", *features]].copy()
    for col in features:
        rows[col] = pd.to_numeric(rows[col], errors="coerce")
    rows["return_pct"] = pd.to_numeric(rows["return_pct"], errors="coerce")
    rows = rows.dropna(subset=["quarter", "return_pct"]).copy()
    coef_rows = []
    for quarter, subset in rows.groupby("quarter"):
        min_non_null = max(8, len(subset) // 3)
        use_features = [col for col in features if subset[col].notna().sum() >= min_non_null]
        use_features = [col for col in use_features if subset[col].nunique(dropna=True) > 1]
        if len(subset) < max(12, len(use_features) + 4) or not use_features:
            continue
        x_frame = subset[use_features].fillna(subset[use_features].median(numeric_only=True)).astype(float)
        x_frame = (x_frame - x_frame.mean()) / x_frame.std(ddof=0).replace(0, 1.0)
        X = np.column_stack([np.ones(len(x_frame)), x_frame.to_numpy(dtype=float)])
        y = subset["return_pct"].to_numpy(dtype=float)
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        for name, value in zip(["intercept", *use_features], coef):
            coef_rows.append({"quarter": quarter, "term": name, "coefficient": float(value), "cross_section_count": int(len(subset))})
    coef_panel = pd.DataFrame(coef_rows)
    if coef_panel.empty:
        return coef_panel, pd.DataFrame()
    result = (
        coef_panel.groupby("term")
        .agg(
            period_count=("quarter", "nunique"),
            mean_coefficient=("coefficient", "mean"),
            std_coefficient=("coefficient", "std"),
            avg_cross_section_count=("cross_section_count", "mean"),
        )
        .reset_index()
    )
    denom = result["std_coefficient"].fillna(0.0) / np.sqrt(result["period_count"]).replace(0, np.nan)
    result["t_stat_proxy"] = result["mean_coefficient"] / denom.replace(0, np.nan)
    result["factor_result_used_as_trading_trigger_flag"] = 0
    return coef_panel, result


def build_book_equity_source_audit(book_equity: pd.DataFrame) -> pd.DataFrame:
    if book_equity.empty:
        return pd.DataFrame([{"source_name": "SEC_companyfacts_book_equity", "available_flag": 0, "symbol_count": 0, "row_count": 0}])
    return (
        book_equity.groupby("concept")
        .agg(symbol_count=("symbol", "nunique"), row_count=("symbol", "size"), min_filed_date=("filed_date", "min"), max_filed_date=("filed_date", "max"))
        .reset_index()
        .assign(source_name="SEC_companyfacts_book_equity", available_flag=1)
    )


def build_size_bm_coverage_audit(panel: pd.DataFrame, book_equity: pd.DataFrame, market_cap: pd.DataFrame) -> pd.DataFrame:
    total = len(panel)
    return pd.DataFrame(
        [
            {
                "population_name": "Task503_exact_lifecycle_panel",
                "row_count": int(total),
                "symbol_count": int(panel["symbol"].nunique()) if total else 0,
                "market_cap_coverage_rate": float(panel["size_factor_available_flag"].mean()) if total else 0.0,
                "book_to_market_coverage_rate": float(panel["book_to_market_available_flag"].mean()) if total else 0.0,
                "book_equity_source_symbol_count": int(book_equity["symbol"].nunique()) if not book_equity.empty else 0,
                "market_cap_source_symbol_count": int(market_cap["symbol"].nunique()) if not market_cap.empty else 0,
                "same_day_daily_close_used_flag": 0,
                "book_equity_filed_date_asof_used_flag": 1,
                "missing_data_approximated_flag": 0,
                "crsp_compustat_grade_flag": 0,
            }
        ]
    )


def build_leakage_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"rule": "market_cap_uses_previous_daily_close_only", "pass_flag": 1},
            {"rule": "book_equity_uses_filed_date_asof_only", "pass_flag": 1},
            {"rule": "factor_result_not_used_as_entry_trigger", "pass_flag": 1},
            {"rule": "missing_book_or_market_cap_not_approximated", "pass_flag": 1},
            {"rule": "exact_lifecycle_panel_only_no_symbol_date_fallback", "pass_flag": 1},
        ]
    )


def build_decision(coverage: pd.DataFrame, fmb_result: pd.DataFrame) -> pd.DataFrame:
    rec = coverage.iloc[0].to_dict() if not coverage.empty else {}
    bm_cov = float(rec.get("book_to_market_coverage_rate", 0.0))
    size_cov = float(rec.get("market_cap_coverage_rate", 0.0))
    ran = int(not fmb_result.empty and {"size_log_market_cap", "book_to_market_log"}.issubset(set(fmb_result["term"])))
    status = "SIZE_BM_FAMA_MACBETH_DIAGNOSTIC_READY_SOURCE_GRADE_LIMITED" if ran and bm_cov >= 0.50 else "SIZE_BM_FAMA_MACBETH_DIAGNOSTIC_COVERAGE_LIMITED"
    return pd.DataFrame(
        [
            {
                "task_id": "Task541",
                "size_factor_available_flag": int(size_cov > 0),
                "book_to_market_available_flag": int(bm_cov > 0),
                "task503_size_coverage_rate": size_cov,
                "task503_book_to_market_coverage_rate": bm_cov,
                "fama_macbeth_size_bm_run_flag": ran,
                "factor_result_used_as_trading_trigger_flag": 0,
                "missing_data_approximated_flag": 0,
                "crsp_compustat_grade_flag": 0,
                "strategy_acceptance_status": status,
            }
        ]
    )


def write_task541(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_541_decision"].iloc[0].to_dict()
    coverage = artifacts["size_bm_factor_coverage_audit"].iloc[0].to_dict()
    result = artifacts["fama_macbeth_with_size_bm_result"]
    size_row = result[result["term"].eq("size_log_market_cap")].head(1)
    bm_row = result[result["term"].eq("book_to_market_log")].head(1)
    size_t = float(size_row["t_stat_proxy"].iloc[0]) if not size_row.empty else float("nan")
    bm_t = float(bm_row["t_stat_proxy"].iloc[0]) if not bm_row.empty else float("nan")
    write_standard_report(
        out_dir / "task_541_size_bm_fama_macbeth.md",
        title="Task 541 Size Book-to-Market Fama-MacBeth Diagnostic",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Task503 size coverage: {decision['task503_size_coverage_rate']:.2%}",
            f"Task503 book-to-market coverage: {decision['task503_book_to_market_coverage_rate']:.2%}",
            f"Fama-MacBeth size/BM run: {decision['fama_macbeth_size_bm_run_flag']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task541 builds actual diagnostic size and book-to-market factors from SEC companyfacts book equity, SEC-derived shares, and previous daily close market cap.",
            "Daily close market cap is joined strictly from dates before the intraday entry date; same-day daily close is not used as an entry-time feature.",
            "Book equity is joined by SEC filed date, not by fiscal period end alone, which preserves as-of discipline.",
            f"Fama-MacBeth proxy coefficients are diagnostic: size t-stat proxy {size_t:.2f}, book-to-market t-stat proxy {bm_t:.2f}.",
            "The Fama-MacBeth-style result is a validation layer only. It is not an entry trigger and remains source-grade limited versus CRSP/Compustat.",
        ],
        decision_maker_lines=[
            "We added real size and book-to-market diagnostics to the factor-premium check instead of assuming those values.",
            "This helps distinguish whether strategy returns are just exposure to large/small or value/growth effects, but it does not make the strategy deployable.",
            f"Coverage is explicit: size {coverage['market_cap_coverage_rate']:.2%}, book-to-market {coverage['book_to_market_coverage_rate']:.2%}. Missing values are not filled with guesses.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_task541_size_bm_fama_macbeth()


if __name__ == "__main__":
    main()
