from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task608k_failure_taxonomy_v2_conditional_treatment import (
    REPORT_DIR as TASK608K_REPORT_DIR,
    build_task608k_failure_taxonomy_v2_conditional_treatment,
)


TASK_ID = "Task608L"
REPORT_DIR = Path("docs/reports/task_608l_early_adverse_false_positive_decomposition")
TASK608K_PANEL = TASK608K_REPORT_DIR / "entry_upgrade_feature_panel_v2.csv"
TASK608K_TAXONOMY = TASK608K_REPORT_DIR / "failure_taxonomy_v2_panel.csv"
BASELINE_FAILURE_RATE = 6 / 13
BASELINE_CLEAN_FALSE_COUNT = 7


def build_task608l_early_adverse_false_positive_decomposition(
    *,
    task608k_panel: Path = TASK608K_PANEL,
    task608k_taxonomy: Path = TASK608K_TAXONOMY,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task608k_panel)
    taxonomy = load_taxonomy(task608k_taxonomy)
    panel = panel.merge(
        taxonomy[["lifecycle_id", "failure_type_v2", "detection_horizon"]],
        on="lifecycle_id",
        how="left",
    )
    panel["failure_type_v2"] = panel["failure_type_v2"].fillna("clean_or_non_failure")
    panel["detection_horizon"] = panel["detection_horizon"].fillna("not_failure")
    panel = add_trigger_features(panel)
    trigger_panel = build_trigger_profile(panel)
    group_comparison = build_true_vs_clean_comparison(trigger_panel)
    interaction_matrix = build_interaction_matrix(panel)
    fold_forward = build_fold_forward_validation(panel, interaction_matrix)
    decision = build_decision(trigger_panel, interaction_matrix, fold_forward)

    out_dir.mkdir(parents=True, exist_ok=True)
    trigger_panel.to_csv(out_dir / "early_adverse_trigger_profile.csv", index=False)
    group_comparison.to_csv(out_dir / "true_failure_vs_clean_false_comparison.csv", index=False)
    interaction_matrix.to_csv(out_dir / "early_adverse_interaction_matrix.csv", index=False)
    fold_forward.to_csv(out_dir / "early_adverse_fold_forward_validation.csv", index=False)
    decision.to_csv(out_dir / "task_608l_decision.csv", index=False)
    (out_dir / "task_608l_early_adverse_false_positive_decomposition.md").write_text(
        render_report(trigger_panel, group_comparison, interaction_matrix, fold_forward, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "early_adverse_trigger_profile": trigger_panel,
        "true_failure_vs_clean_false_comparison": group_comparison,
        "early_adverse_interaction_matrix": interaction_matrix,
        "early_adverse_fold_forward_validation": fold_forward,
        "task_608l_decision": decision,
    }


def load_panel(path: Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        build_task608k_failure_taxonomy_v2_conditional_treatment()
    frame = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")
    numeric_columns = [
        "entry_price",
        "simulated_exit_price",
        "net_return_from_entry",
        "symbol_ret_15m",
        "symbol_ret_30m",
        "symbol_ret_60m",
        "symbol_ret_120m",
        "symbol_mae_15m",
        "symbol_mfe_15m",
        "symbol_mae_30m",
        "symbol_mfe_30m",
        "symbol_mfe_60m",
        "relative_ret_vs_qqq_15m",
        "relative_ret_vs_qqq_30m",
        "relative_ret_vs_qqq_120m",
        "symbol_volume_decay_120m",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["entry_reduce_failure_flag"] = pd.to_numeric(
        frame["entry_reduce_failure_flag"], errors="coerce"
    ).fillna(0).astype(int)
    return frame


def load_taxonomy(path: Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        build_task608k_failure_taxonomy_v2_conditional_treatment()
    return pd.read_csv(path)


def add_trigger_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["early_adverse_trigger_flag"] = (
        _le_series(result["symbol_ret_15m"], -0.015) | _le_series(result["symbol_mae_15m"], -0.03)
    ).astype(int)
    result["no_mfe_recovery_30m_flag"] = _le_series(result["symbol_mfe_30m"], 0.01).astype(int)
    result["no_mfe_recovery_60m_flag"] = _le_series(result["symbol_mfe_60m"], 0.01).astype(int)
    result["persistent_vwap_fail_30_60m_flag"] = (
        result["symbol_vwap_fail_30m_flag"].fillna(0).astype(int).eq(1)
        & result["symbol_vwap_fail_60m_flag"].fillna(0).astype(int).eq(1)
    ).astype(int)
    result["opening_range_rejection_flag"] = result["opening_rejection_120m_flag"].fillna(0).astype(int)
    result["opening_range_reclaim_fail_flag"] = (
        result["symbol_opening_range_high_reclaim_120m_flag"].fillna(0).astype(int).eq(0)
    ).astype(int)
    result["qqq_rs_decay_30m_flag"] = _le_series(result["relative_ret_vs_qqq_30m"], -0.015).astype(int)
    result["qqq_rs_decay_120m_flag"] = _le_series(result["relative_ret_vs_qqq_120m"], -0.02).astype(int)
    result["volume_decay_flag"] = result["volume_decay_120m_flag"].fillna(0).astype(int)
    result["theme_drag_flag"] = result["theme_confirmation_fail_pre_entry_flag"].fillna(0).astype(int)
    result["true_failure_flag"] = result["entry_reduce_failure_flag"].astype(int)
    result["clean_false_flag"] = (
        result["early_adverse_trigger_flag"].eq(1) & result["entry_reduce_failure_flag"].eq(0)
    ).astype(int)
    result["recovery_cluster"] = result.apply(classify_recovery_cluster, axis=1)
    return result


def classify_recovery_cluster(row: pd.Series) -> str:
    if int(row.get("early_adverse_trigger_flag", 0)) != 1:
        return "not_early_adverse_trigger"
    if int(row.get("entry_reduce_failure_flag", 0)) == 1:
        if int(row.get("volume_decay_flag", 0)) == 1 and int(row.get("qqq_rs_decay_120m_flag", 0)) == 1:
            return "true_failure_rs_decay_volume_decay"
        if int(row.get("opening_range_rejection_flag", 0)) == 1:
            return "true_failure_opening_rejection"
        return "true_failure_other"
    if not _le(row.get("symbol_mfe_30m"), 0.01):
        return "clean_false_mfe_recovered"
    if int(row.get("opening_range_reclaim_fail_flag", 0)) == 0:
        return "clean_false_opening_reclaimed"
    return "clean_false_survived_adverse"


def build_trigger_profile(panel: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "lifecycle_id",
        "symbol",
        "quarter",
        "timing_state",
        "entry_ts",
        "entry_reduce_failure_flag",
        "net_return_from_entry",
        "failure_type_v2",
        "detection_horizon",
        "recovery_cluster",
        "symbol_ret_15m",
        "symbol_mae_15m",
        "symbol_mfe_15m",
        "symbol_ret_30m",
        "symbol_mae_30m",
        "symbol_mfe_30m",
        "symbol_ret_60m",
        "symbol_ret_120m",
        "symbol_mfe_60m",
        "symbol_vwap_fail_15m_flag",
        "symbol_vwap_fail_30m_flag",
        "symbol_vwap_fail_60m_flag",
        "persistent_vwap_fail_30_60m_flag",
        "opening_range_rejection_flag",
        "opening_range_reclaim_fail_flag",
        "relative_ret_vs_qqq_15m",
        "relative_ret_vs_qqq_30m",
        "relative_ret_vs_qqq_120m",
        "qqq_rs_decay_30m_flag",
        "qqq_rs_decay_120m_flag",
        "volume_decay_flag",
        "theme_drag_flag",
        "clean_false_flag",
    ]
    return panel.loc[panel["early_adverse_trigger_flag"].eq(1), columns].sort_values("entry_ts").reset_index(drop=True)


def build_true_vs_clean_comparison(trigger_panel: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "symbol_ret_15m",
        "symbol_mae_15m",
        "symbol_mfe_15m",
        "symbol_ret_30m",
        "symbol_mae_30m",
        "symbol_mfe_30m",
        "symbol_mfe_60m",
        "relative_ret_vs_qqq_15m",
        "relative_ret_vs_qqq_30m",
        "relative_ret_vs_qqq_120m",
        "persistent_vwap_fail_30_60m_flag",
        "opening_range_rejection_flag",
        "opening_range_reclaim_fail_flag",
        "qqq_rs_decay_30m_flag",
        "qqq_rs_decay_120m_flag",
        "volume_decay_flag",
        "theme_drag_flag",
    ]
    rows = []
    true_failure = trigger_panel[trigger_panel["entry_reduce_failure_flag"].eq(1)]
    clean_false = trigger_panel[trigger_panel["entry_reduce_failure_flag"].eq(0)]
    for column in metric_columns:
        rows.append(
            {
                "feature": column,
                "true_failure_mean": float(pd.to_numeric(true_failure[column], errors="coerce").mean()),
                "clean_false_mean": float(pd.to_numeric(clean_false[column], errors="coerce").mean()),
                "difference_true_minus_clean": float(
                    pd.to_numeric(true_failure[column], errors="coerce").mean()
                    - pd.to_numeric(clean_false[column], errors="coerce").mean()
                ),
                "true_failure_nonnull": int(pd.to_numeric(true_failure[column], errors="coerce").notna().sum()),
                "clean_false_nonnull": int(pd.to_numeric(clean_false[column], errors="coerce").notna().sum()),
            }
        )
    return pd.DataFrame(rows)


def build_interaction_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    candidates = interaction_candidates()
    base = panel["early_adverse_trigger_flag"].eq(1)
    baseline = panel[base]
    rows = []
    for name, horizon, predicate in candidates:
        flags = base & panel.apply(predicate, axis=1)
        triggered = panel[flags].copy()
        rows.append(
            {
                "interaction_name": name,
                "detection_horizon": horizon,
                "trigger_count": int(len(triggered)),
                "failure_count": int(triggered["entry_reduce_failure_flag"].sum()),
                "clean_false_count": int((triggered["entry_reduce_failure_flag"].eq(0)).sum()),
                "failure_rate": _mean_flag(triggered["entry_reduce_failure_flag"]),
                "clean_false_ratio": _safe_div(int(triggered["entry_reduce_failure_flag"].eq(0).sum()), len(triggered)),
                "baseline_trigger_count": int(len(baseline)),
                "baseline_failure_count": int(baseline["entry_reduce_failure_flag"].sum()),
                "baseline_clean_false_count": int(baseline["entry_reduce_failure_flag"].eq(0).sum()),
                "baseline_failure_rate": _mean_flag(baseline["entry_reduce_failure_flag"]),
                "failure_rate_lift": _mean_flag(triggered["entry_reduce_failure_flag"]) - _mean_flag(baseline["entry_reduce_failure_flag"]),
                "clean_false_reduction_count": int(baseline["entry_reduce_failure_flag"].eq(0).sum())
                - int(triggered["entry_reduce_failure_flag"].eq(0).sum()),
                "triggered_avg_return_pct": float(triggered["net_return_from_entry"].mean() * 100.0) if len(triggered) else 0.0,
                "label_used_in_assignment_flag": 0,
                "deployment_claim_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["failure_rate", "failure_count", "clean_false_count"], ascending=[False, False, True]
    ).reset_index(drop=True)


def interaction_candidates() -> list[tuple[str, str, Callable[[pd.Series], bool]]]:
    return [
        ("early_adverse__no_mfe_recovery_30m", "30m_wait", lambda r: _le(r.get("symbol_mfe_30m"), 0.01)),
        ("early_adverse__persistent_vwap_fail_30_60m", "60m_wait", lambda r: int(r.get("persistent_vwap_fail_30_60m_flag", 0)) == 1),
        ("early_adverse__opening_range_rejection", "120m_wait", lambda r: int(r.get("opening_range_rejection_flag", 0)) == 1),
        ("early_adverse__qqq_rs_decay_30m", "30m_wait", lambda r: int(r.get("qqq_rs_decay_30m_flag", 0)) == 1),
        ("early_adverse__volume_decay", "120m_wait", lambda r: int(r.get("volume_decay_flag", 0)) == 1),
        ("early_adverse__theme_drag", "pre_entry", lambda r: int(r.get("theme_drag_flag", 0)) == 1),
        (
            "early_adverse__vwap_fail_and_no_mfe_recovery",
            "60m_wait",
            lambda r: int(r.get("persistent_vwap_fail_30_60m_flag", 0)) == 1 and int(r.get("no_mfe_recovery_30m_flag", 0)) == 1,
        ),
        (
            "early_adverse__rs_decay_120m_and_volume_decay",
            "120m_wait",
            lambda r: int(r.get("qqq_rs_decay_120m_flag", 0)) == 1 and int(r.get("volume_decay_flag", 0)) == 1,
        ),
        (
            "early_adverse__no_mfe_recovery_and_volume_decay",
            "120m_wait",
            lambda r: int(r.get("no_mfe_recovery_30m_flag", 0)) == 1 and int(r.get("volume_decay_flag", 0)) == 1,
        ),
        (
            "early_adverse__persistent_vwap_fail_and_reclaim_fail",
            "120m_wait",
            lambda r: int(r.get("persistent_vwap_fail_30_60m_flag", 0)) == 1 and int(r.get("opening_range_reclaim_fail_flag", 0)) == 1,
        ),
    ]


def build_fold_forward_validation(panel: pd.DataFrame, interaction_matrix: pd.DataFrame) -> pd.DataFrame:
    candidates_by_name = {name: predicate for name, _, predicate in interaction_candidates()}
    quarters = sorted(panel["quarter"].astype(str).unique().tolist())
    rows = []
    base = panel["early_adverse_trigger_flag"].eq(1)
    for interaction_name in interaction_matrix["interaction_name"].tolist():
        predicate = candidates_by_name[interaction_name]
        flags = base & panel.apply(predicate, axis=1)
        for idx in range(1, len(quarters)):
            train = panel[panel["quarter"].astype(str).isin(quarters[:idx])]
            test = panel[panel["quarter"].astype(str).eq(quarters[idx])]
            train_base = base.loc[train.index]
            train_flags = flags.loc[train.index]
            test_base = base.loc[test.index]
            test_flags = flags.loc[test.index]
            if int(train_base.sum()) < 3 or int(train_flags.sum()) < 2 or int(test_base.sum()) == 0:
                continue
            train_failure_rate = _mean_flag(train.loc[train_flags, "entry_reduce_failure_flag"])
            train_base_failure_rate = _mean_flag(train.loc[train_base, "entry_reduce_failure_flag"])
            test_failure_rate = _mean_flag(test.loc[test_flags, "entry_reduce_failure_flag"])
            test_base_failure_rate = _mean_flag(test.loc[test_base, "entry_reduce_failure_flag"])
            test_clean_false = int((test_flags & test["entry_reduce_failure_flag"].eq(0)).sum())
            test_base_clean_false = int((test_base & test["entry_reduce_failure_flag"].eq(0)).sum())
            rows.append(
                {
                    "interaction_name": interaction_name,
                    "test_quarter": quarters[idx],
                    "train_trigger_count": int(train_flags.sum()),
                    "train_failure_rate": train_failure_rate,
                    "train_base_failure_rate": train_base_failure_rate,
                    "test_base_trigger_count": int(test_base.sum()),
                    "test_trigger_count": int(test_flags.sum()),
                    "test_failure_count": int(test.loc[test_flags, "entry_reduce_failure_flag"].sum()),
                    "test_clean_false_count": test_clean_false,
                    "test_failure_rate": test_failure_rate,
                    "test_base_failure_rate": test_base_failure_rate,
                    "test_base_clean_false_count": test_base_clean_false,
                    "positive_fold_flag": int(
                        int(test_flags.sum()) > 0
                        and test_failure_rate > test_base_failure_rate
                        and test_clean_false < test_base_clean_false
                    ),
                    "label_used_in_test_assignment_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_decision(trigger_panel: pd.DataFrame, interaction_matrix: pd.DataFrame, fold_forward: pd.DataFrame) -> pd.DataFrame:
    fold_summary = summarize_fold_forward(fold_forward)
    scored = interaction_matrix.merge(fold_summary, on="interaction_name", how="left")
    scored["positive_fold_count"] = scored["positive_fold_count"].fillna(0).astype(int)
    scored["test_trigger_total"] = scored["test_trigger_total"].fillna(0).astype(int)
    scored["same_candidate_pass_flag"] = (
        (scored["trigger_count"].astype(int) >= 3)
        & (scored["failure_rate"].astype(float) > BASELINE_FAILURE_RATE)
        & (scored["clean_false_count"].astype(int) < BASELINE_CLEAN_FALSE_COUNT)
        & (scored["positive_fold_count"].astype(int) >= 1)
    ).astype(int)
    if int(scored["same_candidate_pass_flag"].sum()) > 0:
        best = scored[scored["same_candidate_pass_flag"].eq(1)].sort_values(
            ["positive_fold_count", "failure_rate", "failure_count", "clean_false_count"],
            ascending=[False, False, False, True],
        ).iloc[0].to_dict()
    else:
        best = scored.sort_values(
            ["failure_rate", "failure_count", "clean_false_count"],
            ascending=[False, False, True],
        ).iloc[0].to_dict() if len(scored) else {}
    classifier_pass = int(
        int(best.get("trigger_count", 0)) >= 3
        and float(best.get("failure_rate", 0.0)) > BASELINE_FAILURE_RATE
        and int(best.get("clean_false_count", BASELINE_CLEAN_FALSE_COUNT)) < BASELINE_CLEAN_FALSE_COUNT
        and int(best.get("positive_fold_count", 0)) >= 1
    )
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": (
                    "PASS_EARLY_ADVERSE_CLASSIFIER_CANDIDATE_NEEDS_RULE_LOCK"
                    if classifier_pass
                    else "FAIL_EARLY_ADVERSE_RULE_LOCK_NOT_READY"
                ),
                "pass_flag": classifier_pass,
                "baseline_trigger_count": int(len(trigger_panel)),
                "baseline_failure_count": int(trigger_panel["entry_reduce_failure_flag"].sum()),
                "baseline_clean_false_count": int(trigger_panel["entry_reduce_failure_flag"].eq(0).sum()),
                "baseline_failure_rate": BASELINE_FAILURE_RATE,
                "best_interaction": best.get("interaction_name", ""),
                "best_interaction_trigger_count": best.get("trigger_count", 0),
                "best_interaction_failure_rate": best.get("failure_rate", 0.0),
                "best_interaction_clean_false_count": best.get("clean_false_count", 0),
                "best_interaction_positive_fold_count": best.get("positive_fold_count", 0),
                "best_interaction_test_trigger_total": best.get("test_trigger_total", 0),
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "rule_lock_status": "NOT_READY",
                "reducer_retry_status": "CLOSED",
                "next_action": "If early-adverse interactions do not hold under stricter fold-forward, stop this branch and move late follow-through to exit/trailing review.",
            }
        ]
    )


def summarize_fold_forward(fold_forward: pd.DataFrame) -> pd.DataFrame:
    if fold_forward.empty:
        return pd.DataFrame()
    rows = []
    for name, group in fold_forward.groupby("interaction_name", sort=True):
        rows.append(
            {
                "interaction_name": name,
                "fold_count": int(len(group)),
                "test_trigger_total": int(group["test_trigger_count"].sum()),
                "test_failure_total": int(group["test_failure_count"].sum()),
                "test_clean_false_total": int(group["test_clean_false_count"].sum()),
                "positive_fold_count": int(group["positive_fold_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["positive_fold_count", "test_failure_total", "test_clean_false_total"], ascending=[False, False, True]
    ).reset_index(drop=True)


def render_report(
    trigger_panel: pd.DataFrame,
    group_comparison: pd.DataFrame,
    interaction_matrix: pd.DataFrame,
    fold_forward: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    row = decision.iloc[0].to_dict()
    top_interactions = [
        f"- {item['interaction_name']}: trigger {int(item['trigger_count'])}, fail {int(item['failure_count'])}, clean {int(item['clean_false_count'])}, fail rate {float(item['failure_rate']):.2%}"
        for _, item in interaction_matrix.head(5).iterrows()
    ]
    top_diff = [
        f"- {item['feature']}: true-clean diff {float(item['difference_true_minus_clean']):.4f}"
        for _, item in group_comparison.reindex(group_comparison["difference_true_minus_clean"].abs().sort_values(ascending=False).index).head(5).iterrows()
    ]
    fold_summary = summarize_fold_forward(fold_forward)
    fold_lines = [
        f"- {item['interaction_name']}: folds {int(item['fold_count'])}, test trigger {int(item['test_trigger_total'])}, fail {int(item['test_failure_total'])}, clean {int(item['test_clean_false_total'])}, positive {int(item['positive_fold_count'])}"
        for _, item in fold_summary.head(5).iterrows()
    ]
    return "\n".join(
        [
            "# Task608L Early Adverse False Positive Decomposition",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: {row['decision']}",
            "- Strategy acceptance status: NOT_ACCEPTED",
            "- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "- Rule-lock status: NOT_READY",
            "- Reducer retry: CLOSED",
            f"- Baseline wait15 trigger: {int(row['baseline_trigger_count'])}, failure {int(row['baseline_failure_count'])}, clean false {int(row['baseline_clean_false_count'])}, failure rate {float(row['baseline_failure_rate']):.2%}.",
            f"- Best interaction: {row['best_interaction']}, trigger {int(row['best_interaction_trigger_count'])}, failure rate {float(row['best_interaction_failure_rate']):.2%}, clean false {int(row['best_interaction_clean_false_count'])}.",
            f"- Best interaction fold evidence: positive folds {int(row['best_interaction_positive_fold_count'])}, test triggers {int(row['best_interaction_test_trigger_total'])}.",
            f"- Next action: {row['next_action']}",
            "",
            "## Quant Expert Report",
            "",
            "- Data source and source readiness: Task608K feature panel and taxonomy v2.",
            "- Exact join keys: `lifecycle_id` only.",
            "- Leakage audit: labels are used to evaluate true failure versus clean false, not to assign candidate flags.",
            "- Split/OOS metrics: fold-forward interaction validation is included, but sample is small and not deployable.",
            "- Failure decomposition: wait15 early adverse has 6 failures and 7 clean false rows.",
            "- Cost/slippage stress where PnL changed: not applicable; no treatment is promoted.",
            "- Remaining blockers: fold-forward stability and winner-destruction control.",
            "",
            "True-vs-clean strongest differences:",
            *top_diff,
            "",
            "Interaction candidates:",
            *top_interactions,
            "",
            "Fold-forward summary:",
            *(fold_lines or ["- No fold-forward rows met minimum train/test coverage."]),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: the early adverse bucket was split into true failures and clean false rows.",
            "- Why it matters: the best interaction looks better in-sample, but fold-forward evidence is still too thin.",
            "- Whether this changes capital/deployment readiness: no.",
            "- Plain-language next step: do not lock the rule yet; either tighten and retest or stop this branch.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    ).rstrip() + "\n"


def _mean_flag(series: pd.Series) -> float:
    return float(pd.to_numeric(series, errors="coerce").mean()) if len(series) else 0.0


def _safe_div(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _le_series(series: pd.Series, threshold: float) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").le(threshold)


def _le(value: object, threshold: float) -> bool:
    try:
        return pd.notna(value) and float(value) <= threshold
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task608k-panel", type=Path, default=TASK608K_PANEL)
    parser.add_argument("--task608k-taxonomy", type=Path, default=TASK608K_TAXONOMY)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task608l_early_adverse_false_positive_decomposition(
        task608k_panel=args.task608k_panel,
        task608k_taxonomy=args.task608k_taxonomy,
        out_dir=args.out_dir,
    )
    row = artifacts["task_608l_decision"].iloc[0]
    print(f"[TASK608L] decision={row['decision']} pass={int(row['pass_flag'])}")


if __name__ == "__main__":
    main()
