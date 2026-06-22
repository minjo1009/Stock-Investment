from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import (
    _load_frozen_behavior_state,
    _markdown_table,
)
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import (
    DB_PATH,
    ENTRY_ONLY,
    IMMEDIATE_POST_BREAK,
    WINDOW_MODES,
    _add_train_only_bands,
    _available_features,
    _build_intraday_subset,
    _derive_target,
    _feature_set_features,
    _fit_logistic_local,
    _holdout_results as _holdout_results_336,
    _load_intraday_bars,
    _majority_predictor,
    _metric_row,
    _predict_band_probability,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_338_intraday_evaluation_fix")
MIN_TRADES_PER_SPLIT = 20

FEATURE_SETS = [
    "core_only",
    "intraday_only_entry_only",
    "intraday_only_immediate_post_break",
    "core_plus_intraday_entry_only",
    "core_plus_intraday_immediate_post_break",
    "intraday_plus_volume",
    "intraday_plus_vwap",
    "all_combined_entry_only",
    "all_combined_immediate_post_break",
]
TARGETS = ["bad_state", "clean_state", "continuation_quality_rank"]
MODELS = ["majority", "band_probability", "logistic"]
SPLITS = ["train", "anchored_oos", "full_period"]


def _missing_reason(status: str) -> str:
    if status == "covered":
        return ""
    if status == "insufficient_window":
        return "incomplete_intraday_window"
    return str(status)


def _build_split_frames(intraday_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    frozen_train, frozen_oos, frozen_full = _load_frozen_behavior_state()
    split_inputs = {
        "train": frozen_train,
        "anchored_oos": frozen_oos,
        "full_period": frozen_full,
    }
    coverage_parts: list[pd.DataFrame] = []
    feature_parts: dict[str, pd.DataFrame] = {}
    for split_name, split_df in split_inputs.items():
        coverage_df, feature_df = _build_intraday_subset(split_df, intraday_df)
        if coverage_df.empty:
            coverage_df = split_df.copy()
            coverage_df["coverage_status"] = "missing_date"
            coverage_df["entry_only_status"] = "missing_date"
            coverage_df["immediate_post_break_status"] = "missing_date"
            coverage_df["session_bar_count"] = 0
            coverage_df["breakout_bar_index"] = math.nan
            coverage_df["breakout_timestamp"] = ""
        coverage_df = coverage_df.copy()
        coverage_df["split"] = split_name
        coverage_df["date"] = pd.to_datetime(coverage_df["entry_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        coverage_df["is_covered"] = coverage_df["coverage_status"].astype(str) == "covered"
        coverage_df["missing_reason"] = coverage_df["coverage_status"].astype(str).map(_missing_reason)
        coverage_parts.append(coverage_df)
        feature_parts[split_name] = feature_df.copy()
    coverage_all = pd.concat(coverage_parts, ignore_index=True) if coverage_parts else pd.DataFrame()
    return coverage_all, feature_parts


def _split_coverage_summary(coverage_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_name in SPLITS:
        scoped = coverage_df[coverage_df["split"] == split_name].copy()
        total = int(len(scoped))
        covered = int(scoped["is_covered"].sum()) if not scoped.empty else 0
        rows.append(
            {
                "split": split_name,
                "total_trades": total,
                "covered_trades": covered,
                "coverage_ratio": round(float(covered / max(total, 1)), 6),
            }
        )
    return pd.DataFrame(rows)


def _empty_metric_row(
    split_name: str,
    window_mode: str,
    feature_set: str,
    target_name: str,
    model_name: str,
    covered_trade_count: int,
    total_split_trades: int,
    status: str,
) -> dict[str, Any]:
    return {
        "split": split_name,
        "window_mode": window_mode,
        "feature_set": feature_set,
        "target": target_name,
        "model": model_name,
        "accuracy": math.nan,
        "majority_baseline_accuracy": math.nan,
        "lift_vs_baseline": math.nan,
        "bad_state_recall": math.nan,
        "clean_state_precision": math.nan,
        "ranking_correlation": math.nan,
        "coverage_trade_count": int(covered_trade_count),
        "total_split_trades": int(total_split_trades),
        "coverage_ratio": round(float(covered_trade_count / max(total_split_trades, 1)), 6),
        "status": status,
    }


def _evaluate_subset_corrected(
    train_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    split_name: str,
    target_name: str,
    feature_set: str,
    window_mode: str,
    model_name: str,
    total_split_trades: int,
    min_trades_per_split: int,
) -> dict[str, Any]:
    features = _available_features(train_df, _feature_set_features(window_mode, feature_set))
    if len(train_df) < min_trades_per_split or len(eval_df) < min_trades_per_split:
        return _empty_metric_row(
            split_name,
            window_mode,
            feature_set,
            target_name,
            model_name,
            len(eval_df),
            total_split_trades,
            "insufficient_sample",
        )
    if not features:
        return _empty_metric_row(
            split_name,
            window_mode,
            feature_set,
            target_name,
            model_name,
            len(eval_df),
            total_split_trades,
            "insufficient_intraday_coverage",
        )
    y_train = _derive_target(train_df, target_name)
    y_eval = _derive_target(eval_df, target_name)
    train_banded, eval_banded = _add_train_only_bands(train_df, eval_df, features)
    if model_name == "majority":
        preds = _majority_predictor(y_train, len(eval_df))
    elif model_name == "band_probability":
        preds = _predict_band_probability(train_banded, eval_banded, target_name, features)
    elif model_name == "logistic":
        model = _fit_logistic_local(train_df, y_train, features)
        preds = model.predict(eval_df[features])
    else:
        raise ValueError(model_name)
    row = _metric_row(y_eval, preds, target_name)
    row.update(
        {
            "split": split_name,
            "window_mode": window_mode,
            "feature_set": feature_set,
            "target": target_name,
            "model": model_name,
            "coverage_trade_count": int(len(eval_df)),
            "total_split_trades": int(total_split_trades),
            "coverage_ratio": round(float(len(eval_df) / max(total_split_trades, 1)), 6),
            "status": "ok",
        }
    )
    return row


def _diagnostic_overlay_rows_corrected(
    train_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    split_name: str,
    feature_set: str,
    window_mode: str,
    total_split_trades: int,
    min_trades_per_split: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    features = _available_features(train_df, _feature_set_features(window_mode, feature_set))
    if len(train_df) < min_trades_per_split or len(eval_df) < min_trades_per_split or not features:
        return (
            {
                "split": split_name,
                "window_mode": window_mode,
                "feature_set": feature_set,
                "policy_name": "bad_skip_clean_fullsize",
                "baseline_expectancy": math.nan,
                "diagnostic_expectancy": math.nan,
                "baseline_return_proxy": math.nan,
                "diagnostic_return_proxy": math.nan,
                "saved_loss": math.nan,
                "missed_gain": math.nan,
                "trade_count": int(len(eval_df)),
                "total_split_trades": int(total_split_trades),
                "diagnostic_trade_count": 0,
                "coverage_trade_count": int(len(eval_df)),
                "status": "insufficient_sample" if len(eval_df) < min_trades_per_split else "insufficient_intraday_coverage",
            },
            pd.DataFrame(),
        )
    bad_model = _fit_logistic_local(train_df, _derive_target(train_df, "bad_state"), features)
    clean_model = _fit_logistic_local(train_df, _derive_target(train_df, "clean_state"), features)
    bad_proba_train = bad_model.predict_proba(train_df[features])
    clean_proba_train = clean_model.predict_proba(train_df[features])
    bad_idx = list(bad_model.classes_).index(1) if 1 in set(bad_model.classes_) else list(bad_model.classes_).index("1")
    clean_idx = list(clean_model.classes_).index(1) if 1 in set(clean_model.classes_) else list(clean_model.classes_).index("1")
    bad_cut = float(np.quantile(bad_proba_train[:, bad_idx], 2 / 3))
    clean_cut = float(np.quantile(clean_proba_train[:, clean_idx], 2 / 3))
    bad_scores = bad_model.predict_proba(eval_df[features])[:, bad_idx]
    clean_scores = clean_model.predict_proba(eval_df[features])[:, clean_idx]
    pred_bad = bad_scores >= bad_cut
    pred_clean = clean_scores >= clean_cut

    out = eval_df.copy()
    out["pred_bad_state"] = pred_bad.astype(int)
    out["pred_clean_state"] = pred_clean.astype(int)
    out["diagnostic_multiplier"] = np.where(pred_bad, 0.0, np.where(pred_clean, 1.25, 1.0))
    out["diagnostic_adjusted_R"] = pd.to_numeric(out["realized_R"], errors="coerce") * pd.to_numeric(out["diagnostic_multiplier"], errors="coerce")
    baseline_return = float(pd.to_numeric(out["realized_R"], errors="coerce").sum())
    adjusted_return = float(pd.to_numeric(out["diagnostic_adjusted_R"], errors="coerce").sum())
    baseline_expectancy = float(pd.to_numeric(out["realized_R"], errors="coerce").mean()) if not out.empty else math.nan
    adjusted_expectancy = float(pd.to_numeric(out.loc[out["diagnostic_multiplier"] > 0, "diagnostic_adjusted_R"], errors="coerce").mean()) if (out["diagnostic_multiplier"] > 0).any() else math.nan
    saved_loss = float((-pd.to_numeric(out.loc[(out["diagnostic_multiplier"] == 0.0) & (pd.to_numeric(out["realized_R"], errors="coerce") < 0), "realized_R"], errors="coerce")).sum())
    missed_gain = float(pd.to_numeric(out.loc[(out["diagnostic_multiplier"] == 0.0) & (pd.to_numeric(out["realized_R"], errors="coerce") > 0), "realized_R"], errors="coerce").sum())
    metrics = {
        "split": split_name,
        "window_mode": window_mode,
        "feature_set": feature_set,
        "policy_name": "bad_skip_clean_fullsize",
        "baseline_expectancy": round(baseline_expectancy, 6),
        "diagnostic_expectancy": round(adjusted_expectancy, 6) if not pd.isna(adjusted_expectancy) else math.nan,
        "baseline_return_proxy": round(baseline_return, 6),
        "diagnostic_return_proxy": round(adjusted_return, 6),
        "saved_loss": round(saved_loss, 6),
        "missed_gain": round(missed_gain, 6),
        "trade_count": int(len(out)),
        "total_split_trades": int(total_split_trades),
        "diagnostic_trade_count": int((out["diagnostic_multiplier"] > 0).sum()),
        "coverage_trade_count": int(len(out)),
        "status": "ok",
    }
    delta = out[
        [
            "trade_id",
            "symbol",
            "scenario",
            "cluster_label",
            "cluster_label_base",
            "realized_R",
            "pred_bad_state",
            "pred_clean_state",
            "diagnostic_multiplier",
            "diagnostic_adjusted_R",
        ]
    ].copy()
    delta["split"] = split_name
    delta["window_mode"] = window_mode
    delta["feature_set"] = feature_set
    return metrics, delta


def _holdout_results_corrected(
    train_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    window_mode: str,
    feature_set: str,
    target_name: str,
    model_name: str,
    min_trades_per_split: int,
) -> pd.DataFrame:
    base = _holdout_results_336(train_df, oos_df, window_mode, feature_set, target_name, model_name).copy()
    if base.empty:
        return base
    if "scope" in base.columns:
        base = base.drop(columns=["scope"])
    base["split"] = np.where(base["holdout_type"].astype(str) == "time_split_oos", "anchored_oos", "train_holdout")
    base["status"] = np.where(
        pd.to_numeric(base["coverage_trade_count"], errors="coerce").fillna(0).astype(int) < min_trades_per_split,
        "insufficient_sample",
        base["status"],
    )
    return base


def _final_decision_corrected(
    prediction_df: pd.DataFrame,
    holdout_df: pd.DataFrame,
    economic_df: pd.DataFrame,
    split_summary_df: pd.DataFrame,
    min_trades_per_split: int,
) -> pd.DataFrame:
    oos_summary = split_summary_df[split_summary_df["split"] == "anchored_oos"]
    covered_oos = int(oos_summary["covered_trades"].iloc[0]) if not oos_summary.empty else 0
    if covered_oos < min_trades_per_split:
        return pd.DataFrame(
            [
                {
                    "decision": "INSUFFICIENT_SAMPLE",
                    "decision_reason": "anchored_oos covered subset is below minimum sample threshold",
                    "covered_trade_count": covered_oos,
                    "positive_oos_lift_exists": False,
                    "best_bad_state_recall": math.nan,
                    "best_clean_state_precision": math.nan,
                    "holdout_mean_lift": math.nan,
                }
            ]
        )
    oos_rows = prediction_df[(prediction_df["split"] == "anchored_oos") & (prediction_df["status"] == "ok")].copy()
    positive_oos_lift = bool((pd.to_numeric(oos_rows["lift_vs_baseline"], errors="coerce") > 0).any()) if not oos_rows.empty else False
    best_bad_recall = float(pd.to_numeric(oos_rows["bad_state_recall"], errors="coerce").max()) if not oos_rows.empty else math.nan
    best_clean_precision = float(pd.to_numeric(oos_rows["clean_state_precision"], errors="coerce").max()) if not oos_rows.empty else math.nan
    ok_holdouts = holdout_df[holdout_df.get("status", "ok") == "ok"].copy()
    holdout_mean_lift = float(pd.to_numeric(ok_holdouts["lift_vs_baseline"], errors="coerce").mean()) if not ok_holdouts.empty else math.nan
    econ_ok = economic_df[economic_df.get("status", "ok") == "ok"].copy()
    saved_gt_missed = bool((pd.to_numeric(econ_ok["saved_loss"], errors="coerce") > pd.to_numeric(econ_ok["missed_gain"], errors="coerce")).any()) if not econ_ok.empty else False
    expectancy_improved = bool((pd.to_numeric(econ_ok["diagnostic_expectancy"], errors="coerce") > pd.to_numeric(econ_ok["baseline_expectancy"], errors="coerce")).any()) if not econ_ok.empty else False
    decision = "NO_INTRADAY_EDGE"
    reason = "covered subset did not show stable OOS intraday signal"
    if positive_oos_lift and expectancy_improved and saved_gt_missed:
        decision = "PARTIAL_INTRADAY_EDGE"
        reason = "covered subset shows some OOS intraday signal but holdout support remains limited"
        if not math.isnan(holdout_mean_lift) and holdout_mean_lift > 0:
            decision = "STRONG_INTRADAY_EDGE"
            reason = "covered subset shows stable OOS intraday signal across holdouts"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "covered_trade_count": covered_oos,
                "positive_oos_lift_exists": positive_oos_lift,
                "best_bad_state_recall": round(best_bad_recall, 6) if not math.isnan(best_bad_recall) else math.nan,
                "best_clean_state_precision": round(best_clean_precision, 6) if not math.isnan(best_clean_precision) else math.nan,
                "holdout_mean_lift": round(holdout_mean_lift, 6) if not math.isnan(holdout_mean_lift) else math.nan,
            }
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 338: fix intraday evaluation on covered subset.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--min-trades-per-split", type=int, default=MIN_TRADES_PER_SPLIT)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    intraday_df = _load_intraday_bars(Path(args.db_path))
    coverage_df, feature_parts = _build_split_frames(intraday_df)
    split_summary_df = _split_coverage_summary(coverage_df)
    total_by_split = split_summary_df.set_index("split")["total_trades"].to_dict()

    prediction_rows: list[dict[str, Any]] = []
    economic_rows: list[dict[str, Any]] = []
    trade_delta_rows: list[pd.DataFrame] = []
    holdout_parts: list[pd.DataFrame] = []

    for window_mode in WINDOW_MODES:
        train_df = feature_parts["train"][feature_parts["train"]["window_mode"] == window_mode].copy()
        oos_df = feature_parts["anchored_oos"][feature_parts["anchored_oos"]["window_mode"] == window_mode].copy()
        full_df = feature_parts["full_period"][feature_parts["full_period"]["window_mode"] == window_mode].copy()
        split_eval_frames = {
            "train": train_df,
            "anchored_oos": oos_df,
            "full_period": full_df,
        }
        for feature_set in FEATURE_SETS:
            for split_name, eval_df in split_eval_frames.items():
                for target_name in TARGETS:
                    for model_name in MODELS:
                        prediction_rows.append(
                            _evaluate_subset_corrected(
                                train_df,
                                eval_df,
                                split_name,
                                target_name,
                                feature_set,
                                window_mode,
                                model_name,
                                int(total_by_split.get(split_name, 0)),
                                args.min_trades_per_split,
                            )
                        )
            metrics, delta = _diagnostic_overlay_rows_corrected(
                train_df,
                oos_df,
                "anchored_oos",
                feature_set,
                window_mode,
                int(total_by_split.get("anchored_oos", 0)),
                args.min_trades_per_split,
            )
            economic_rows.append(metrics)
            if not delta.empty:
                trade_delta_rows.append(delta)
            holdout_parts.append(
                _holdout_results_corrected(
                    train_df,
                    oos_df,
                    window_mode,
                    feature_set,
                    "bad_state",
                    "band_probability",
                    args.min_trades_per_split,
                )
            )
            holdout_parts.append(
                _holdout_results_corrected(
                    train_df,
                    oos_df,
                    window_mode,
                    feature_set,
                    "clean_state",
                    "band_probability",
                    args.min_trades_per_split,
                )
            )

    prediction_df = pd.DataFrame(prediction_rows)
    economic_df = pd.DataFrame(economic_rows)
    trade_delta_df = pd.concat(trade_delta_rows, ignore_index=True) if trade_delta_rows else pd.DataFrame()
    holdout_df = pd.concat(holdout_parts, ignore_index=True) if holdout_parts else pd.DataFrame()
    final_decision_df = _final_decision_corrected(
        prediction_df,
        holdout_df,
        economic_df,
        split_summary_df,
        args.min_trades_per_split,
    )

    coverage_flags_df = coverage_df[
        [
            "trade_id",
            "symbol",
            "date",
            "split",
            "is_covered",
            "missing_reason",
        ]
    ].copy()

    md_lines = [
        "# Task 338: Intraday Evaluation Fix",
        "",
        f"- Final decision: `{final_decision_df.iloc[0]['decision']}`.",
        f"- Anchored OOS covered trades: `{int(split_summary_df.loc[split_summary_df['split'] == 'anchored_oos', 'covered_trades'].iloc[0]) if not split_summary_df.empty else 0}`.",
        "",
        "## Split Coverage Summary",
        "",
    ]
    md_lines.extend(_markdown_table(split_summary_df))
    md_lines.extend(["", "## Prediction Metrics (Corrected)", ""])
    md_lines.extend(_markdown_table(prediction_df.head(24)))
    md_lines.extend(["", "## Holdout Results (Corrected)", ""])
    md_lines.extend(_markdown_table(holdout_df.head(24)))
    md_lines.extend(["", "## Economic Action Test (Corrected)", ""])
    md_lines.extend(_markdown_table(economic_df.head(24)))
    md_lines.extend(
        [
            "",
            "## Final Answer",
            "",
            "- Covered-subset evaluation now uses only trades with valid intraday windows.",
            "- Splits with partial coverage are evaluated on the covered subset instead of being dropped wholesale.",
            "- Splits below the minimum covered-sample threshold are marked `insufficient_sample` rather than `insufficient_intraday_coverage`.",
        ]
    )

    coverage_flags_df.to_csv(out_dir / "task_338_trade_coverage_flags.csv", index=False)
    split_summary_df.to_csv(out_dir / "task_338_split_coverage_summary.csv", index=False)
    prediction_df.to_csv(out_dir / "task_338_prediction_metrics_corrected.csv", index=False)
    economic_df.to_csv(out_dir / "task_338_economic_action_test_corrected.csv", index=False)
    trade_delta_df.to_csv(out_dir / "task_338_trade_level_delta_corrected.csv", index=False)
    holdout_df.to_csv(out_dir / "task_338_holdout_results_corrected.csv", index=False)
    final_decision_df.to_csv(out_dir / "task_338_final_decision_corrected.csv", index=False)
    (out_dir / "task_338_intraday_evaluation_fix.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
