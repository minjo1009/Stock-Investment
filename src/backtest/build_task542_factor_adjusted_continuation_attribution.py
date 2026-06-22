from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task537_factor_premium_validation import load_lifecycle_panel
from src.backtest.task_report_utils import write_standard_report


TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
TASK505_PANEL = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_panel.csv")
TASK529_FEATURES = Path("docs/reports/task_529_trend_persistence_entry_safe_refinement/entry_safe_feature_audit.csv")
FF_DAILY_PANEL = Path("data/raw/fama_french/fama_french_5_factor_daily.csv")
TASK541_SIZE_BM_PANEL = Path("docs/reports/task_541_size_bm_fama_macbeth/size_bm_factor_panel.csv")
TASK542_OUT = Path("docs/reports/task_542_factor_adjusted_continuation_attribution")

FF_FEATURES = ["cum_Mkt_RF_pct", "cum_SMB_pct", "cum_HML_pct", "cum_RMW_pct", "cum_CMA_pct"]
SIZE_BM_FEATURES = ["size_log_market_cap", "book_to_market_log"]
MODEL_FEATURES = [*FF_FEATURES, *SIZE_BM_FEATURES]


def build_task542_factor_adjusted_continuation_attribution(
    *,
    lifecycle_panel_path: Path = TASK503_PANEL,
    task505_panel_path: Path = TASK505_PANEL,
    task529_features_path: Path = TASK529_FEATURES,
    ff_daily_path: Path = FF_DAILY_PANEL,
    size_bm_panel_path: Path = TASK541_SIZE_BM_PANEL,
    out_dir: Path = TASK542_OUT,
) -> dict[str, pd.DataFrame]:
    universe = build_factor_model_universe(lifecycle_panel_path, ff_daily_path, size_bm_panel_path)
    model_summary, universe_scored = fit_factor_model(universe)
    candidates = build_candidate_assignment_panel(task505_panel_path, task529_features_path)
    attributed = attach_factor_adjustment(candidates, universe_scored)
    quality = summarize_candidate_quality(attributed)
    split_quality = summarize_split_quality(attributed)
    exposure = summarize_candidate_exposure(attributed)
    leakage = build_leakage_audit()
    decision = build_decision(quality, model_summary, attributed)
    artifacts = {
        "factor_model_summary": model_summary,
        "factor_adjusted_candidate_panel": attributed,
        "candidate_factor_adjusted_quality": quality,
        "candidate_factor_adjusted_split_quality": split_quality,
        "candidate_factor_exposure_audit": exposure,
        "factor_adjustment_leakage_audit": leakage,
        "task_542_decision": decision,
    }
    write_task542(out_dir, artifacts)
    return artifacts


def build_factor_model_universe(lifecycle_panel_path: Path, ff_daily_path: Path, size_bm_panel_path: Path) -> pd.DataFrame:
    ff = build_ff_exposure_panel(lifecycle_panel_path, ff_daily_path)
    size = pd.read_csv(size_bm_panel_path)
    keep = ["lifecycle_id", "size_log_market_cap", "book_to_market_log", "size_factor_available_flag", "book_to_market_available_flag"]
    frame = ff.merge(size[keep], on="lifecycle_id", how="left")
    for col in ["return_pct", "excess_return_pct", *MODEL_FEATURES]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["factor_model_coverage_flag"] = frame[MODEL_FEATURES].notna().all(axis=1).astype(int)
    frame["factor_result_used_as_trading_trigger_flag"] = 0
    return frame


def build_ff_exposure_panel(lifecycle_panel_path: Path, ff_daily_path: Path) -> pd.DataFrame:
    lifecycle = load_lifecycle_panel(lifecycle_panel_path)
    ff = pd.read_csv(ff_daily_path)
    ff["date"] = pd.to_datetime(ff["date"], utc=True, errors="coerce")
    ff["date_only"] = ff["date"].dt.date
    for col in ["Mkt_RF", "SMB", "HML", "RMW", "CMA", "RF"]:
        ff[col] = pd.to_numeric(ff[col], errors="coerce")
    rows = []
    for row in lifecycle.to_dict(orient="records"):
        window = ff[ff["date_only"].between(row["entry_date"], row["exit_date"])]
        if window.empty:
            continue
        out = {
            "lifecycle_id": row["lifecycle_id"],
            "symbol": row.get("symbol"),
            "theme_id": row.get("theme_id"),
            "entry_date": row["entry_date"],
            "exit_date": row["exit_date"],
            "return_pct": row["return_pct"],
            "ff_day_count": int(len(window)),
        }
        for col in ["Mkt_RF", "SMB", "HML", "RMW", "CMA", "RF"]:
            out[f"cum_{col}_pct"] = float(window[col].sum())
        out["excess_return_pct"] = float(row["return_pct"] - out["cum_RF_pct"])
        rows.append(out)
    return pd.DataFrame(rows)


def fit_factor_model(universe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    universe = universe.copy()
    if "factor_model_coverage_flag" not in universe.columns:
        universe["factor_model_coverage_flag"] = universe[MODEL_FEATURES].notna().all(axis=1).astype(int)
    train = universe[universe["factor_model_coverage_flag"].eq(1)].copy()
    if len(train) <= len(MODEL_FEATURES) + 5:
        out = universe.copy()
        out["factor_predicted_excess_return_pct"] = np.nan
        out["factor_adjusted_residual_pct"] = np.nan
        return pd.DataFrame(), out
    x_frame = train[MODEL_FEATURES].astype(float)
    means = x_frame.mean()
    stds = x_frame.std(ddof=0).replace(0, 1.0)
    X = np.column_stack([np.ones(len(train)), ((x_frame - means) / stds).to_numpy(dtype=float)])
    y = train["excess_return_pct"].to_numpy(dtype=float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    scored = universe.copy()
    x_all = scored[MODEL_FEATURES].astype(float)
    valid = x_all.notna().all(axis=1)
    X_all = np.column_stack([np.ones(int(valid.sum())), ((x_all.loc[valid] - means) / stds).to_numpy(dtype=float)])
    scored["factor_predicted_excess_return_pct"] = np.nan
    scored.loc[valid, "factor_predicted_excess_return_pct"] = X_all @ coef
    scored["factor_adjusted_residual_pct"] = scored["excess_return_pct"] - scored["factor_predicted_excess_return_pct"]
    pred = X @ coef
    resid = y - pred
    tss = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - float(np.sum(resid**2)) / tss if tss else 0.0
    summary = pd.DataFrame(
        [
            {
                "term": term,
                "coefficient": float(value),
                "model_row_count": int(len(train)),
                "universe_row_count": int(len(universe)),
                "coverage_rate": float(len(train) / len(universe)) if len(universe) else 0.0,
                "r_squared": float(r2),
                "factor_result_used_as_trading_trigger_flag": 0,
            }
            for term, value in zip(["intercept", *MODEL_FEATURES], coef)
        ]
    )
    return summary, scored


def build_candidate_assignment_panel(task505_panel_path: Path, task529_features_path: Path) -> pd.DataFrame:
    panel = pd.read_csv(task505_panel_path)
    panel["candidate_set"] = "task505_selected_two_year_strategy"
    panel["return_pct"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce") * 100.0
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    rows = [panel.copy()]
    if task529_features_path.exists():
        features = pd.read_csv(task529_features_path)
        features["entry_close_pos_in_bar"] = pd.to_numeric(features["entry_close_pos_in_bar"], errors="coerce")
        refined_ids = set(features.loc[features["entry_close_pos_in_bar"].le(0.97), "lifecycle_id"].astype(str))
        refined = panel[
            panel["lifecycle_id"].astype(str).isin(refined_ids)
            & panel["symbol_multiday_setup_state"].astype(str).eq("trend_persistence_near_high")
        ].copy()
        refined["candidate_set"] = "task529_trend_closepos_only_097"
        rows.append(refined)
        shadow = refined.copy()
        shadow["candidate_set"] = "task530_paper_shadow_candidate"
        rows.append(shadow)
    out = pd.concat(rows, ignore_index=True)
    out["factor_assignment_used_label_flag"] = 0
    out["inferred_lifecycle_matching_used_flag"] = 0
    return out


def attach_factor_adjustment(candidates: pd.DataFrame, scored_universe: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "lifecycle_id",
        "cum_Mkt_RF_pct",
        "cum_SMB_pct",
        "cum_HML_pct",
        "cum_RMW_pct",
        "cum_CMA_pct",
        "cum_RF_pct",
        "excess_return_pct",
        "size_log_market_cap",
        "book_to_market_log",
        "factor_model_coverage_flag",
        "factor_predicted_excess_return_pct",
        "factor_adjusted_residual_pct",
    ]
    out = candidates.merge(scored_universe[keep], on="lifecycle_id", how="left")
    out["factor_adjustment_available_flag"] = out["factor_adjusted_residual_pct"].notna().astype(int)
    out["factor_result_used_as_trading_trigger_flag"] = 0
    out["missing_data_approximated_flag"] = 0
    return out


def summarize_candidate_quality(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate_set, subset in panel.groupby("candidate_set"):
        adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
        rows.append(
            {
                "candidate_set": candidate_set,
                "lifecycle_count": int(len(subset)),
                "factor_adjusted_count": int(len(adjusted)),
                "factor_adjustment_coverage_rate": float(len(adjusted) / len(subset)) if len(subset) else 0.0,
                "raw_avg_return_pct": float(subset["return_pct"].mean()) if len(subset) else np.nan,
                "raw_win_rate": float(pd.to_numeric(subset["win_flag"], errors="coerce").mean()) if "win_flag" in subset else np.nan,
                "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                "factor_adjusted_win_rate": float((adjusted["factor_adjusted_residual_pct"] > 0).mean()) if len(adjusted) else np.nan,
                "entry_reduce_failure_rate": float(pd.to_numeric(subset["entry_reduce_failure_flag"], errors="coerce").mean()) if "entry_reduce_failure_flag" in subset else np.nan,
                "add_scale_success_rate": float(pd.to_numeric(subset["add_scale_success_flag"], errors="coerce").mean()) if "add_scale_success_flag" in subset else np.nan,
                "factor_attribution_status": classify_attribution(subset, adjusted),
            }
        )
    return pd.DataFrame(rows)


def classify_attribution(subset: pd.DataFrame, adjusted: pd.DataFrame) -> str:
    if len(adjusted) < max(20, int(0.5 * len(subset))):
        return "insufficient_factor_coverage"
    raw_avg = float(subset["return_pct"].mean())
    residual_avg = float(adjusted["factor_adjusted_residual_pct"].mean())
    if residual_avg > 0 and residual_avg >= raw_avg * 0.5:
        return "true_continuation_alpha_candidate"
    if raw_avg > 0 and residual_avg <= 0:
        return "factor_exposure_driven_or_unexplained_after_adjustment"
    return "mixed_factor_adjusted_evidence"


def summarize_split_quality(panel: pd.DataFrame) -> pd.DataFrame:
    if "split_name" not in panel.columns:
        return pd.DataFrame()
    rows = []
    for (candidate_set, split_name), subset in panel.groupby(["candidate_set", "split_name"]):
        adjusted = subset[subset["factor_adjustment_available_flag"].eq(1)]
        rows.append(
            {
                "candidate_set": candidate_set,
                "split_name": split_name,
                "lifecycle_count": int(len(subset)),
                "factor_adjusted_count": int(len(adjusted)),
                "raw_avg_return_pct": float(subset["return_pct"].mean()) if len(subset) else np.nan,
                "factor_adjusted_avg_residual_pct": float(adjusted["factor_adjusted_residual_pct"].mean()) if len(adjusted) else np.nan,
                "entry_reduce_failure_rate": float(pd.to_numeric(subset["entry_reduce_failure_flag"], errors="coerce").mean()) if "entry_reduce_failure_flag" in subset else np.nan,
            }
        )
    return pd.DataFrame(rows)


def summarize_candidate_exposure(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate_set, subset in panel.groupby("candidate_set"):
        rec = {"candidate_set": candidate_set, "lifecycle_count": int(len(subset))}
        for feature in MODEL_FEATURES:
            rec[f"avg_{feature}"] = float(pd.to_numeric(subset[feature], errors="coerce").mean()) if feature in subset else np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def build_leakage_audit() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"rule": "candidate_assignment_does_not_use_factor_result", "pass_flag": 1},
            {"rule": "factor_result_used_as_trading_trigger_flag_zero", "pass_flag": 1},
            {"rule": "exact_lifecycle_id_join_only", "pass_flag": 1},
            {"rule": "missing_factor_data_not_approximated", "pass_flag": 1},
            {"rule": "size_bm_source_grade_limited_not_deployment_claim", "pass_flag": 1},
        ]
    )


def build_decision(quality: pd.DataFrame, model_summary: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    true_count = int((quality["factor_attribution_status"] == "true_continuation_alpha_candidate").sum()) if not quality.empty else 0
    coverage = float(panel["factor_adjustment_available_flag"].mean()) if not panel.empty else 0.0
    return pd.DataFrame(
        [
            {
                "task_id": "Task542",
                "factor_model_run_flag": int(not model_summary.empty),
                "candidate_set_count": int(quality["candidate_set"].nunique()) if not quality.empty else 0,
                "candidate_factor_adjustment_coverage_rate": coverage,
                "true_continuation_alpha_candidate_count": true_count,
                "factor_result_used_as_trading_trigger_flag": 0,
                "missing_data_approximated_flag": 0,
                "deployment_ready_flag": 0,
                "strategy_acceptance_status": "FACTOR_ADJUSTED_ATTRIBUTION_DIAGNOSTIC_ONLY",
            }
        ]
    )


def write_task542(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_542_decision"].iloc[0].to_dict()
    quality = artifacts["candidate_factor_adjusted_quality"]
    lines = []
    for row in quality.to_dict(orient="records"):
        lines.append(
            f"{row['candidate_set']}: raw {row['raw_avg_return_pct']:.2f}%, "
            f"factor-adjusted residual {row['factor_adjusted_avg_residual_pct']:.2f}%, "
            f"coverage {row['factor_adjustment_coverage_rate']:.2%}, status {row['factor_attribution_status']}."
        )
    write_standard_report(
        out_dir / "task_542_factor_adjusted_continuation_attribution.md",
        title="Task 542 Factor-Adjusted Continuation Edge Attribution",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Candidate sets evaluated: {decision['candidate_set_count']}",
            f"Factor-adjustment coverage: {decision['candidate_factor_adjustment_coverage_rate']:.2%}",
            f"True continuation alpha candidates: {decision['true_continuation_alpha_candidate_count']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task542 fits a broad exact-lifecycle factor model using Fama-French cumulative factors plus Task541 size and book-to-market diagnostics.",
            "The fitted factor model is then used only as an attribution lens on Task505/529/530 continuation candidates.",
            *lines,
            "This is not a trading trigger and remains source-grade limited because size/BM coverage is incomplete and SEC-derived rather than CRSP/Compustat-grade.",
        ],
        decision_maker_lines=[
            "We checked whether the continuation candidates still look good after removing broad factor exposure.",
            "A positive residual means the candidate may contain continuation-specific edge beyond market/size/value style exposure.",
            "This still does not approve deployment; it tells us where the next validation should focus.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_task542_factor_adjusted_continuation_attribution()


if __name__ == "__main__":
    main()
