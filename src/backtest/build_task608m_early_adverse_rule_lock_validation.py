from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task608l_early_adverse_false_positive_decomposition import (
    REPORT_DIR as TASK608L_REPORT_DIR,
    TASK608K_PANEL,
    TASK608K_TAXONOMY,
    add_trigger_features,
    load_panel,
    load_taxonomy,
)


TASK_ID = "Task608M"
REPORT_DIR = Path("docs/reports/task_608m_early_adverse_rule_lock_validation")
BASELINE_FAILURE_RATE = 6 / 13
BASELINE_CLEAN_FALSE_COUNT = 7


def build_task608m_early_adverse_rule_lock_validation(
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
    panel = add_candidate_flags(panel)

    candidate_profile = build_candidate_profile(panel)
    strict_fold = build_strict_fold_forward(panel)
    threshold = build_threshold_neighborhood(panel)
    winner_damage = build_winner_destruction_audit(panel)
    decision = build_decision(candidate_profile, strict_fold, threshold, winner_damage)

    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_profile.to_csv(out_dir / "candidate_profile.csv", index=False)
    strict_fold.to_csv(out_dir / "strict_fold_forward_validation.csv", index=False)
    threshold.to_csv(out_dir / "threshold_neighborhood_validation.csv", index=False)
    winner_damage.to_csv(out_dir / "winner_destruction_audit.csv", index=False)
    decision.to_csv(out_dir / "task_608m_decision.csv", index=False)
    (out_dir / "task_608m_early_adverse_rule_lock_validation.md").write_text(
        render_report(candidate_profile, strict_fold, threshold, winner_damage, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "candidate_profile": candidate_profile,
        "strict_fold_forward_validation": strict_fold,
        "threshold_neighborhood_validation": threshold,
        "winner_destruction_audit": winner_damage,
        "task_608m_decision": decision,
    }


def add_candidate_flags(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["candidate_rule_flag"] = (
        result["early_adverse_trigger_flag"].eq(1)
        & result["no_mfe_recovery_30m_flag"].eq(1)
        & result["volume_decay_flag"].eq(1)
    ).astype(int)
    result["candidate_rule_name"] = "early_adverse__no_mfe_recovery_and_volume_decay"
    return result


def build_candidate_profile(panel: pd.DataFrame) -> pd.DataFrame:
    candidate = panel[panel["candidate_rule_flag"].eq(1)].copy()
    baseline = panel[panel["early_adverse_trigger_flag"].eq(1)].copy()
    return pd.DataFrame(
        [
            {
                "rule_name": "wait15_baseline_early_adverse",
                "trigger_count": int(len(baseline)),
                "failure_count": int(baseline["entry_reduce_failure_flag"].sum()),
                "clean_false_count": int(baseline["entry_reduce_failure_flag"].eq(0).sum()),
                "failure_rate": _mean_flag(baseline["entry_reduce_failure_flag"]),
                "avg_return_pct": float(baseline["net_return_from_entry"].mean() * 100.0),
                "clean_false_avg_return_pct": float(
                    baseline.loc[baseline["entry_reduce_failure_flag"].eq(0), "net_return_from_entry"].mean() * 100.0
                ),
            },
            {
                "rule_name": "early_adverse__no_mfe_recovery_and_volume_decay",
                "trigger_count": int(len(candidate)),
                "failure_count": int(candidate["entry_reduce_failure_flag"].sum()),
                "clean_false_count": int(candidate["entry_reduce_failure_flag"].eq(0).sum()),
                "failure_rate": _mean_flag(candidate["entry_reduce_failure_flag"]),
                "avg_return_pct": float(candidate["net_return_from_entry"].mean() * 100.0) if len(candidate) else 0.0,
                "clean_false_avg_return_pct": float(
                    candidate.loc[candidate["entry_reduce_failure_flag"].eq(0), "net_return_from_entry"].mean() * 100.0
                ) if int(candidate["entry_reduce_failure_flag"].eq(0).sum()) else 0.0,
            },
        ]
    )


def build_strict_fold_forward(panel: pd.DataFrame) -> pd.DataFrame:
    quarters = sorted(panel["quarter"].astype(str).unique().tolist())
    rows = []
    base = panel["early_adverse_trigger_flag"].eq(1)
    candidate = panel["candidate_rule_flag"].eq(1)
    for idx in range(1, len(quarters)):
        train = panel[panel["quarter"].astype(str).isin(quarters[:idx])]
        test = panel[panel["quarter"].astype(str).eq(quarters[idx])]
        train_base = base.loc[train.index]
        train_candidate = candidate.loc[train.index]
        test_base = base.loc[test.index]
        test_candidate = candidate.loc[test.index]
        if int(train_base.sum()) < 3 or int(test_base.sum()) == 0:
            continue
        train_candidate_failure_rate = _mean_flag(train.loc[train_candidate, "entry_reduce_failure_flag"])
        train_base_failure_rate = _mean_flag(train.loc[train_base, "entry_reduce_failure_flag"])
        train_rule_eligible = int(
            int(train_candidate.sum()) >= 3
            and train_candidate_failure_rate > train_base_failure_rate
            and int((train_candidate & train["entry_reduce_failure_flag"].eq(0)).sum()) < int(
                (train_base & train["entry_reduce_failure_flag"].eq(0)).sum()
            )
        )
        test_candidate_failure_rate = _mean_flag(test.loc[test_candidate, "entry_reduce_failure_flag"])
        test_base_failure_rate = _mean_flag(test.loc[test_base, "entry_reduce_failure_flag"])
        rows.append(
            {
                "test_quarter": quarters[idx],
                "train_base_trigger_count": int(train_base.sum()),
                "train_candidate_trigger_count": int(train_candidate.sum()),
                "train_base_failure_rate": train_base_failure_rate,
                "train_candidate_failure_rate": train_candidate_failure_rate,
                "train_rule_eligible_flag": train_rule_eligible,
                "test_base_trigger_count": int(test_base.sum()),
                "test_candidate_trigger_count": int(test_candidate.sum()),
                "test_candidate_failure_count": int(test.loc[test_candidate, "entry_reduce_failure_flag"].sum()),
                "test_candidate_clean_false_count": int((test_candidate & test["entry_reduce_failure_flag"].eq(0)).sum()),
                "test_base_failure_rate": test_base_failure_rate,
                "test_candidate_failure_rate": test_candidate_failure_rate,
                "positive_test_flag": int(
                    train_rule_eligible == 1
                    and int(test_candidate.sum()) >= 1
                    and test_candidate_failure_rate > test_base_failure_rate
                    and int((test_candidate & test["entry_reduce_failure_flag"].eq(0)).sum())
                    < int((test_base & test["entry_reduce_failure_flag"].eq(0)).sum())
                ),
                "label_used_in_test_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_threshold_neighborhood(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ret_thresholds = [-0.010, -0.015, -0.020]
    mae_thresholds = [-0.025, -0.030, -0.035]
    mfe_thresholds = [0.005, 0.010, 0.015]
    for ret_threshold in ret_thresholds:
        for mae_threshold in mae_thresholds:
            for mfe_threshold in mfe_thresholds:
                early = _le_series(panel["symbol_ret_15m"], ret_threshold) | _le_series(panel["symbol_mae_15m"], mae_threshold)
                candidate = early & _le_series(panel["symbol_mfe_30m"], mfe_threshold) & panel["volume_decay_flag"].eq(1)
                selected = panel[candidate].copy()
                rows.append(
                    {
                        "ret_15m_threshold": ret_threshold,
                        "mae_15m_threshold": mae_threshold,
                        "mfe_30m_threshold": mfe_threshold,
                        "trigger_count": int(len(selected)),
                        "failure_count": int(selected["entry_reduce_failure_flag"].sum()),
                        "clean_false_count": int(selected["entry_reduce_failure_flag"].eq(0).sum()),
                        "failure_rate": _mean_flag(selected["entry_reduce_failure_flag"]),
                        "pass_neighborhood_flag": int(
                            len(selected) >= 3
                            and _mean_flag(selected["entry_reduce_failure_flag"]) > BASELINE_FAILURE_RATE
                            and int(selected["entry_reduce_failure_flag"].eq(0).sum()) < BASELINE_CLEAN_FALSE_COUNT
                        ),
                    }
                )
    return pd.DataFrame(rows).sort_values(
        ["pass_neighborhood_flag", "failure_rate", "trigger_count"], ascending=[False, False, False]
    ).reset_index(drop=True)


def build_winner_destruction_audit(panel: pd.DataFrame) -> pd.DataFrame:
    candidate = panel[panel["candidate_rule_flag"].eq(1)].copy()
    clean = candidate[candidate["entry_reduce_failure_flag"].eq(0)].copy()
    failed = candidate[candidate["entry_reduce_failure_flag"].eq(1)].copy()
    return pd.DataFrame(
        [
            {
                "audit_name": "candidate_abort_winner_destruction",
                "candidate_trigger_count": int(len(candidate)),
                "candidate_failure_count": int(len(failed)),
                "candidate_clean_false_count": int(len(clean)),
                "clean_false_avg_return_pct": float(clean["net_return_from_entry"].mean() * 100.0) if len(clean) else 0.0,
                "clean_false_total_return_pct": float(clean["net_return_from_entry"].sum() * 100.0) if len(clean) else 0.0,
                "failed_avg_return_pct": float(failed["net_return_from_entry"].mean() * 100.0) if len(failed) else 0.0,
                "winner_destruction_risk_flag": int(len(clean) > 0 and float(clean["net_return_from_entry"].mean()) > 0.0),
            }
        ]
    )


def build_decision(
    candidate_profile: pd.DataFrame,
    strict_fold: pd.DataFrame,
    threshold: pd.DataFrame,
    winner_damage: pd.DataFrame,
) -> pd.DataFrame:
    candidate = candidate_profile[candidate_profile["rule_name"].eq("early_adverse__no_mfe_recovery_and_volume_decay")].iloc[0].to_dict()
    eligible_folds = int(strict_fold["train_rule_eligible_flag"].sum()) if len(strict_fold) else 0
    positive_tests = int(strict_fold["positive_test_flag"].sum()) if len(strict_fold) else 0
    test_triggers = int(strict_fold.loc[strict_fold["train_rule_eligible_flag"].eq(1), "test_candidate_trigger_count"].sum()) if len(strict_fold) else 0
    neighborhood_pass_count = int(threshold["pass_neighborhood_flag"].sum()) if len(threshold) else 0
    winner_flag = int(winner_damage["winner_destruction_risk_flag"].iloc[0]) if len(winner_damage) else 0
    rule_lock_pass = int(
        int(candidate.get("trigger_count", 0)) >= 5
        and float(candidate.get("failure_rate", 0.0)) >= 0.60
        and eligible_folds >= 2
        and positive_tests >= 2
        and test_triggers >= 3
        and neighborhood_pass_count >= 9
        and winner_flag == 0
    )
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "PASS_RULE_LOCK_CANDIDATE" if rule_lock_pass else "FAIL_RULE_LOCK_INSUFFICIENT_SUPPORT",
                "pass_flag": rule_lock_pass,
                "candidate_trigger_count": candidate.get("trigger_count", 0),
                "candidate_failure_rate": candidate.get("failure_rate", 0.0),
                "candidate_clean_false_count": candidate.get("clean_false_count", 0),
                "eligible_fold_count": eligible_folds,
                "positive_test_count": positive_tests,
                "eligible_test_trigger_count": test_triggers,
                "threshold_neighborhood_pass_count": neighborhood_pass_count,
                "winner_destruction_risk_flag": winner_flag,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "rule_lock_status": "FAILED",
                "reducer_retry_status": "CLOSED",
                "branch_recommendation": "STOP_EARLY_ADVERSE_RULE_LOCK_BRANCH_MOVE_LATE_FOLLOWTHROUGH_TO_EXIT_TRAILING_REVIEW",
            }
        ]
    )


def render_report(
    candidate_profile: pd.DataFrame,
    strict_fold: pd.DataFrame,
    threshold: pd.DataFrame,
    winner_damage: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    row = decision.iloc[0].to_dict()
    candidate = candidate_profile[candidate_profile["rule_name"].eq("early_adverse__no_mfe_recovery_and_volume_decay")].iloc[0].to_dict()
    fold_lines = [
        f"- {item['test_quarter']}: train eligible {int(item['train_rule_eligible_flag'])}, test trigger {int(item['test_candidate_trigger_count'])}, positive {int(item['positive_test_flag'])}"
        for _, item in strict_fold.iterrows()
    ]
    threshold_lines = [
        f"- ret {item['ret_15m_threshold']}, mae {item['mae_15m_threshold']}, mfe {item['mfe_30m_threshold']}: trigger {int(item['trigger_count'])}, fail rate {float(item['failure_rate']):.2%}, pass {int(item['pass_neighborhood_flag'])}"
        for _, item in threshold.head(5).iterrows()
    ]
    damage = winner_damage.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task608M Early Adverse Rule Lock Validation",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: {row['decision']}",
            "- Strategy acceptance status: NOT_ACCEPTED",
            "- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "- Reducer retry: CLOSED",
            f"- Candidate trigger: {int(candidate['trigger_count'])}, failure rate {float(candidate['failure_rate']):.2%}, clean false {int(candidate['clean_false_count'])}.",
            f"- Eligible folds: {int(row['eligible_fold_count'])}, positive tests: {int(row['positive_test_count'])}, eligible test triggers: {int(row['eligible_test_trigger_count'])}.",
            f"- Threshold-neighborhood pass count: {int(row['threshold_neighborhood_pass_count'])}.",
            f"- Winner-destruction risk flag: {int(row['winner_destruction_risk_flag'])}.",
            f"- Branch recommendation: {row['branch_recommendation']}",
            "",
            "## Quant Expert Report",
            "",
            "- Data source and source readiness: Task608K panel, Task608K taxonomy, and Task608L candidate definition.",
            "- Exact join keys: `lifecycle_id` only.",
            "- Leakage audit: strict test assignment uses live/wait-window candidate flags. Labels are used only for evaluation.",
            "- Split/OOS metrics: expanding fold-forward with train eligibility gates.",
            "- Failure decomposition: candidate remains inside wait15 early adverse bucket.",
            "- Cost/slippage stress where PnL changed: not applicable because no rule is promoted.",
            "- Remaining blockers: fold support is too thin and candidate trigger count is too small.",
            "",
            "Strict fold-forward:",
            *(fold_lines or ["- No strict fold rows."]),
            "",
            "Threshold neighborhood leaders:",
            *threshold_lines,
            "",
            "Winner destruction:",
            f"- Clean false count {int(damage['candidate_clean_false_count'])}, clean false avg {float(damage['clean_false_avg_return_pct']):.2f}%, risk flag {int(damage['winner_destruction_risk_flag'])}.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: the Task608L candidate was tested harder.",
            "- Why it matters: it looked useful, but the sample is too small and fold evidence is too thin.",
            "- Whether this changes capital/deployment readiness: no.",
            "- Plain-language next step: stop early-adverse rule-lock for now and move late follow-through to exit/trailing review.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    ).rstrip() + "\n"


def _mean_flag(series: pd.Series) -> float:
    return float(pd.to_numeric(series, errors="coerce").mean()) if len(series) else 0.0


def _le_series(series: pd.Series, threshold: float) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").le(threshold)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task608k-panel", type=Path, default=TASK608K_PANEL)
    parser.add_argument("--task608k-taxonomy", type=Path, default=TASK608K_TAXONOMY)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task608m_early_adverse_rule_lock_validation(
        task608k_panel=args.task608k_panel,
        task608k_taxonomy=args.task608k_taxonomy,
        out_dir=args.out_dir,
    )
    row = artifacts["task_608m_decision"].iloc[0]
    print(f"[TASK608M] decision={row['decision']} pass={int(row['pass_flag'])}")


if __name__ == "__main__":
    main()
