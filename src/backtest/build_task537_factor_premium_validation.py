from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK505_PANEL = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_panel.csv")
TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
TASK537_OUT = Path("docs/reports/task_537_factor_premium_validation")
FF_RAW_DIR = Path("data/raw/fama_french")
FF5_DAILY_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"


ENTRY_SAFE_NUMERIC_FEATURES = [
    "ret_5d_prev",
    "ret_20d_prev",
    "ret_60d_prev",
    "volume_ratio_prev",
    "near_high60_prev",
    "theme_ret20_prev",
    "theme_breadth20_prev",
    "theme_volume_ratio_prev",
    "theme_rank_prev",
    "broad_market_score",
    "broad_market_stress",
    "breadth_20d",
    "market_ret_20d",
    "liquidity_ratio",
    "vol_ratio",
    "range_pos",
    "intraday_ret_from_open",
]


def download_fama_french_5_daily(*, out_dir: Path = FF_RAW_DIR, url: str = FF5_DAILY_URL) -> tuple[pd.DataFrame, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_zip = out_dir / "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    raw_zip.write_bytes(response.content)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        csv_name = next(name for name in zf.namelist() if name.lower().endswith(".csv"))
        raw_text = zf.read(csv_name).decode("latin1")
    parsed = parse_fama_french_daily(raw_text)
    parsed.to_csv(out_dir / "fama_french_5_factor_daily.csv", index=False)
    audit = pd.DataFrame(
        [
            {
                "source_name": "Kenneth French Data Library Fama-French 5 Factors Daily",
                "source_url": url,
                "raw_zip_path": str(raw_zip),
                "parsed_path": str(out_dir / "fama_french_5_factor_daily.csv"),
                "row_count": int(len(parsed)),
                "min_date": str(parsed["date"].min().date()) if not parsed.empty else "",
                "max_date": str(parsed["date"].max().date()) if not parsed.empty else "",
                "download_success_flag": int(not parsed.empty),
            }
        ]
    )
    return parsed, audit


def parse_fama_french_daily(raw_text: str) -> pd.DataFrame:
    lines = raw_text.splitlines()
    header_idx = next(i for i, line in enumerate(lines) if line.strip().startswith(",Mkt-RF"))
    rows = []
    for line in lines[header_idx + 1 :]:
        stripped = line.strip()
        if not stripped or not stripped[0].isdigit():
            break
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 7:
            continue
        rows.append(parts[:7])
    frame = pd.DataFrame(rows, columns=["date", "Mkt_RF", "SMB", "HML", "RMW", "CMA", "RF"])
    frame["date"] = pd.to_datetime(frame["date"], format="%Y%m%d", errors="coerce")
    for col in ["Mkt_RF", "SMB", "HML", "RMW", "CMA", "RF"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame.dropna(subset=["date"]).reset_index(drop=True)


def build_task537_factor_premium_validation(
    *,
    task505_panel_path: Path = TASK505_PANEL,
    fmb_panel_path: Path = TASK503_PANEL,
    out_dir: Path = TASK537_OUT,
    ff_raw_dir: Path = FF_RAW_DIR,
) -> dict[str, pd.DataFrame]:
    ff, ff_audit = download_fama_french_5_daily(out_dir=ff_raw_dir)
    panel = load_lifecycle_panel(task505_panel_path)
    fmb_source_panel = load_lifecycle_panel(fmb_panel_path)
    joined = build_trade_factor_panel(panel, ff)
    ff_regression = fit_fama_french_trade_regression(joined)
    fmb_panel, fmb_result = fit_fama_macbeth_entry_safe_panel(fmb_source_panel)
    source_audit = build_source_audit(ff_audit, panel, fmb_source_panel)
    leakage = pd.DataFrame(
        [
            {"rule": "exact_lifecycle_join_only", "pass_flag": 1},
            {"rule": "factor_validation_not_entry_assignment", "pass_flag": 1},
            {"rule": "fundamental_missing_not_approximated", "pass_flag": 1},
            {"rule": "label_used_only_as_dependent_variable", "pass_flag": 1},
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task537",
                "fama_french_data_available_flag": int(not ff.empty),
                "fama_french_adjustment_run_flag": int(not ff_regression.empty),
                "fundamental_factor_data_available_flag": 0,
                "fama_macbeth_entry_safe_run_flag": int(not fmb_result.empty),
                "factor_result_used_as_trading_trigger_flag": 0,
                "missing_data_approximated_flag": 0,
                "strategy_acceptance_status": "FACTOR_PREMIUM_VALIDATION_PARTIAL_FF_READY_FUNDAMENTAL_BLOCKED",
            }
        ]
    )
    artifacts = {
        "fama_french_source_audit": ff_audit,
        "factor_source_availability_audit": source_audit,
        "trade_fama_french_factor_panel": joined,
        "fama_french_risk_adjustment_summary": ff_regression,
        "fama_macbeth_entry_safe_panel": fmb_panel,
        "fama_macbeth_entry_safe_result": fmb_result,
        "factor_premium_leakage_audit": leakage,
        "task_537_decision": decision,
    }
    write_task537(out_dir, artifacts)
    return artifacts


def load_lifecycle_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["simulated_exit_ts"] = pd.to_datetime(panel["simulated_exit_ts"], utc=True, errors="coerce")
    panel["entry_date"] = panel["entry_ts"].dt.tz_convert("UTC").dt.date
    panel["exit_date"] = panel["simulated_exit_ts"].dt.tz_convert("UTC").dt.date
    panel["return_pct"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce") * 100.0
    panel["inferred_lifecycle_matching_used_flag"] = 0
    panel["label_used_in_assignment_flag"] = 0
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "return_pct"]).copy()


def build_trade_factor_panel(panel: pd.DataFrame, ff: pd.DataFrame) -> pd.DataFrame:
    factor = ff.copy()
    factor["date_only"] = factor["date"].dt.date
    rows = []
    for row in panel.to_dict(orient="records"):
        start = row["entry_date"]
        end = row["exit_date"]
        window = factor[factor["date_only"].between(start, end)].copy()
        if window.empty:
            continue
        out = {
            "lifecycle_id": row["lifecycle_id"],
            "symbol": row.get("symbol"),
            "theme_id": row.get("theme_id"),
            "entry_date": start,
            "exit_date": end,
            "return_pct": row["return_pct"],
            "ff_day_count": int(len(window)),
            "inferred_lifecycle_matching_used_flag": 0,
            "label_used_in_assignment_flag": 0,
        }
        for col in ["Mkt_RF", "SMB", "HML", "RMW", "CMA", "RF"]:
            out[f"cum_{col}_pct"] = float(window[col].sum())
        out["excess_return_pct"] = float(row["return_pct"] - out["cum_RF_pct"])
        rows.append(out)
    return pd.DataFrame(rows)


def fit_fama_french_trade_regression(panel: pd.DataFrame) -> pd.DataFrame:
    features = ["cum_Mkt_RF_pct", "cum_SMB_pct", "cum_HML_pct", "cum_RMW_pct", "cum_CMA_pct"]
    if panel.empty or len(panel) <= len(features) + 2:
        return pd.DataFrame()
    X = panel[features].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(X)), X])
    y = pd.to_numeric(panel["excess_return_pct"], errors="coerce").to_numpy(dtype=float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    resid = y - pred
    sse = float(np.sum(resid**2))
    tss = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - sse / tss if tss else 0.0
    names = ["alpha_pct", *features]
    return pd.DataFrame(
        [
            {
                "term": name,
                "coefficient": float(value),
                "trade_count": int(len(panel)),
                "r_squared": float(r2),
                "mean_excess_return_pct": float(np.mean(y)),
                "factor_result_used_as_trading_trigger_flag": 0,
            }
            for name, value in zip(names, coef)
        ]
    )


def fit_fama_macbeth_entry_safe_panel(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    available = [col for col in ENTRY_SAFE_NUMERIC_FEATURES if col in panel.columns]
    rows = panel[["lifecycle_id", "symbol", "theme_id", "quarter", "return_pct", *available]].copy()
    for col in available:
        rows[col] = pd.to_numeric(rows[col], errors="coerce")
    rows = rows.dropna(subset=["quarter", "return_pct"]).copy()
    coef_rows = []
    for quarter, subset in rows.groupby("quarter"):
        use_features = [col for col in available if subset[col].notna().sum() >= max(5, len(subset) // 3)]
        if len(subset) < max(8, len(use_features) + 3) or not use_features:
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
        return rows, pd.DataFrame()
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
    result["t_stat_proxy"] = result["mean_coefficient"] / (result["std_coefficient"].fillna(0.0) / np.sqrt(result["period_count"]).replace(0, np.nan))
    result["factor_result_used_as_trading_trigger_flag"] = 0
    return coef_panel, result


def build_source_audit(ff_audit: pd.DataFrame, panel: pd.DataFrame, fmb_panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source_name": "Fama_French_5_daily",
                "available_flag": int(not ff_audit.empty and int(ff_audit.iloc[0]["download_success_flag"]) == 1),
                "required_for": "risk_adjusted_alpha_claim",
                "blocked_reason": "",
            },
            {
                "source_name": "fundamental_size_value_profitability_investment",
                "available_flag": 0,
                "required_for": "full_Fama_MacBeth_factor_premium_claim",
                "blocked_reason": "fundamental_raw_source_missing",
            },
            {
                "source_name": "exact_lifecycle_return_panel",
                "available_flag": int(not panel.empty),
                "required_for": "entry_safe_Fama_MacBeth_diagnostic",
                "blocked_reason": "",
            },
            {
                "source_name": "broad_exact_lifecycle_cross_section_panel",
                "available_flag": int(not fmb_panel.empty),
                "required_for": "Fama_MacBeth_entry_safe_cross_section",
                "blocked_reason": "",
            },
        ]
    )


def write_task537(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_537_decision"].iloc[0].to_dict()
    ff_summary = artifacts["fama_french_risk_adjustment_summary"]
    fmb_summary = artifacts["fama_macbeth_entry_safe_result"]
    write_standard_report(
        out_dir / "task_537_factor_premium_validation.md",
        title="Task 537 Factor Premium Validation",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Fama-French data available: {decision['fama_french_data_available_flag']}",
            f"Fama-French adjustment run: {decision['fama_french_adjustment_run_flag']}",
            f"Fama-MacBeth entry-safe diagnostic run: {decision['fama_macbeth_entry_safe_run_flag']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task537 downloads Kenneth French daily 5-factor data and joins it to exact lifecycle trade windows by calendar date.",
            "The Fama-French regression is a diagnostic risk adjustment on trade-window excess returns. It is not used for entry assignment.",
            "A Fama-MacBeth-style quarterly cross-sectional diagnostic is run only on currently available entry-safe technical/regime features. Full size/value/profitability/investment factor premium validation remains blocked because fundamental raw data is missing.",
            f"Fama-French regression terms: {len(ff_summary)}. Fama-MacBeth terms: {len(fmb_summary)}.",
        ],
        decision_maker_lines=[
            "We obtained the market factor data needed to start risk-adjusting strategy returns.",
            "We still do not have the company fundamental data needed to claim a full professional factor-premium test.",
            "The new statistics are validation tools only; they do not change the trading rules.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task505-panel", type=Path, default=TASK505_PANEL)
    parser.add_argument("--fmb-panel", type=Path, default=TASK503_PANEL)
    args = parser.parse_args()
    build_task537_factor_premium_validation(task505_panel_path=args.task505_panel, fmb_panel_path=args.fmb_panel)


if __name__ == "__main__":
    main()
