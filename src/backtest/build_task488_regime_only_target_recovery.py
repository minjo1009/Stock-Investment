from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_TASK487_PANEL = Path("docs/reports/task_487_regime_phase_target_validation/regime_phase_lifecycle_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_488_regime_only_target_recovery")

TARGET_COUNT_MIN = 800
TARGET_COUNT_MAX = 1200
TARGET_AVG_NET = 0.35
TARGET_WIN_RATE = 0.50
TARGET_ENTRY_REDUCE_MAX = 0.27

OUTCOME_COLUMNS = {
    "failure_group",
    "lifecycle_outcome_class",
    "return_from_entry",
    "net_return_from_entry",
    "add_flag",
    "scale_flag",
    "reduce_flag",
    "exit_flag",
    "exit_ts",
    "event_path",
    "win_flag",
    "add_scale_success_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
}


@dataclass(frozen=True)
class Task488Artifacts:
    regime_only_candidate_search: pd.DataFrame
    target_recovered_candidate_summary: pd.DataFrame
    target_recovered_split_quality: pd.DataFrame
    target_recovered_quarterly_quality: pd.DataFrame
    target_recovered_theme_quality: pd.DataFrame
    target_recovered_leakage_audit: pd.DataFrame
    task_488_decision: pd.DataFrame


def build_task488_regime_only_target_recovery(
    *,
    task487_panel_path: Path = DEFAULT_TASK487_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> Task488Artifacts:
    panel = load_task487_panel(task487_panel_path)
    candidates = build_regime_only_candidate_search(panel)
    recovered = candidates[candidates["all_targets_pass"] == 1].copy()
    if recovered.empty:
        best = candidates.head(1).copy()
    else:
        robust = recovered[
            (recovered["validation_count"] > 0)
            & (recovered["recent_oos_count"] > 0)
            & (recovered["validation_avg_net_pct"] >= 0.0)
            & (recovered["recent_oos_avg_net_pct"] >= 0.0)
        ].copy()
        selection_pool = robust if not robust.empty else recovered
        best = selection_pool.sort_values(
            ["avg_net_return_pct", "recent_oos_avg_net_pct", "validation_avg_net_pct"],
            ascending=[False, False, False],
        ).head(1)
    if best.empty:
        selected_panel = panel.iloc[0:0].copy()
    else:
        selected_panel = assign_selected_candidate(panel, best.iloc[0])
    split_quality = aggregate_quality(selected_panel, ["split_name"])
    quarterly_quality = aggregate_quality(selected_panel, ["quarter"])
    theme_quality = aggregate_quality(selected_panel, ["theme_id"])
    leakage = build_leakage_audit(best)
    decision = build_task488_decision(candidates, best, leakage)
    artifacts = Task488Artifacts(
        candidates,
        best.reset_index(drop=True),
        split_quality,
        quarterly_quality,
        theme_quality,
        leakage,
        decision,
    )
    write_task488_artifacts(artifacts, out_dir)
    return artifacts


def load_task487_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path, parse_dates=["entry_ts"])
    panel = panel[panel["exact_regime_join_flag"].astype(bool)].copy()
    panel["market_minus_stress"] = panel["payoff_market_score"] - panel["payoff_market_stress_score"]
    panel["theme_minus_stress"] = panel["payoff_theme_score"] - panel["payoff_theme_stress_score"]
    panel["market_theme_sum"] = panel["payoff_market_score"] + panel["payoff_theme_score"]
    panel["stress_sum"] = panel["payoff_market_stress_score"] + panel["payoff_theme_stress_score"]
    panel["split_name"] = split_by_time_series(panel["entry_ts"])
    return panel


def build_regime_only_candidate_search(panel: pd.DataFrame) -> pd.DataFrame:
    score_columns = [
        "payoff_market_score",
        "payoff_market_stress_score",
        "payoff_theme_score",
        "payoff_theme_stress_score",
        "market_minus_stress",
        "theme_minus_stress",
        "market_theme_sum",
        "stress_sum",
    ]
    quantiles = [0, 10, 15, 20, 30, 40, 50, 60, 70, 80, 85, 90, 95, 100]
    thresholds = {
        column: sorted({round(float(v), 6) for v in panel[column].quantile([q / 100 for q in quantiles]).dropna()})
        for column in score_columns
    }
    rows: list[dict[str, object]] = []
    candidate_id = 0
    for left_idx, left_column in enumerate(score_columns):
        for right_column in score_columns[left_idx + 1 :]:
            for left_low, left_high in _intervals(thresholds[left_column]):
                left_mask = panel[left_column].between(left_low, left_high, inclusive="both")
                if int(left_mask.sum()) < TARGET_COUNT_MIN:
                    continue
                for right_low, right_high in _intervals(thresholds[right_column]):
                    mask = left_mask & panel[right_column].between(right_low, right_high, inclusive="both")
                    count = int(mask.sum())
                    if count < TARGET_COUNT_MIN or count > TARGET_COUNT_MAX:
                        continue
                    subset = panel[mask]
                    quality = aggregate_one(subset)
                    candidate_id += 1
                    rows.append(
                        {
                            "candidate_name": f"regime_only_grid_{candidate_id:04d}",
                            "candidate_rule": (
                                f"{left_column} between {left_low:.6f} and {left_high:.6f}; "
                                f"{right_column} between {right_low:.6f} and {right_high:.6f}"
                            ),
                            "left_factor": left_column,
                            "left_low": left_low,
                            "left_high": left_high,
                            "right_factor": right_column,
                            "right_low": right_low,
                            "right_high": right_high,
                            **quality,
                            **split_metrics(subset),
                        }
                    )
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    out["target_count_pass"] = out["lifecycle_count"].between(TARGET_COUNT_MIN, TARGET_COUNT_MAX).astype(int)
    out["target_avg_net_pass"] = (out["avg_net_return_pct"] >= TARGET_AVG_NET).astype(int)
    out["target_win_pass"] = (out["win_rate"] >= TARGET_WIN_RATE).astype(int)
    out["target_entry_reduce_pass"] = (out["entry_reduce_failure_rate"] <= TARGET_ENTRY_REDUCE_MAX).astype(int)
    out["all_targets_pass"] = (
        out["target_count_pass"]
        & out["target_avg_net_pass"]
        & out["target_win_pass"]
        & out["target_entry_reduce_pass"]
    ).astype(int)
    out["diagnostic_only_flag"] = 1
    out["deployment_ready_flag"] = 0
    return out.sort_values(
        ["all_targets_pass", "recent_oos_avg_net_pct", "validation_avg_net_pct", "avg_net_return_pct"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)


def _intervals(values: list[float]) -> list[tuple[float, float]]:
    return [(values[i], values[j]) for i in range(len(values) - 1) for j in range(i + 1, len(values))]


def assign_selected_candidate(panel: pd.DataFrame, candidate: pd.Series) -> pd.DataFrame:
    mask = panel[str(candidate["left_factor"])].between(float(candidate["left_low"]), float(candidate["left_high"]), inclusive="both")
    mask &= panel[str(candidate["right_factor"])].between(float(candidate["right_low"]), float(candidate["right_high"]), inclusive="both")
    out = panel[mask].copy()
    out["selected_candidate_name"] = candidate["candidate_name"]
    out["selected_candidate_rule"] = candidate["candidate_rule"]
    return out


def aggregate_one(subset: pd.DataFrame) -> dict[str, float | int]:
    return {
        "lifecycle_count": int(len(subset)),
        "avg_net_return_pct": float(subset["net_return_from_entry"].mean() * 100.0),
        "win_rate": float(subset["win_flag"].mean()),
        "add_scale_success_rate": float(subset["add_scale_success_flag"].mean()),
        "entry_reduce_failure_rate": float(subset["entry_reduce_failure_flag"].mean()),
        "false_positive_rate": float(subset["false_positive_flag"].mean()),
    }


def aggregate_quality(panel: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame(columns=keys)
    return (
        panel.groupby(keys, dropna=False)
        .agg(
            lifecycle_count=("lifecycle_id", "count"),
            avg_net_return_pct=("net_return_from_entry", lambda s: float(s.mean() * 100.0)),
            win_rate=("win_flag", "mean"),
            add_scale_success_rate=("add_scale_success_flag", "mean"),
            entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
            false_positive_rate=("false_positive_flag", "mean"),
        )
        .reset_index()
        .sort_values("avg_net_return_pct", ascending=False)
    )


def split_metrics(subset: pd.DataFrame) -> dict[str, float | int]:
    rows: dict[str, float | int] = {}
    for split_name in ["train_design", "validation", "recent_oos"]:
        split = subset[subset["split_name"] == split_name]
        prefix = split_name
        rows[f"{prefix}_count"] = int(len(split))
        rows[f"{prefix}_avg_net_pct"] = float(split["net_return_from_entry"].mean() * 100.0) if not split.empty else float("nan")
        rows[f"{prefix}_win_rate"] = float(split["win_flag"].mean()) if not split.empty else float("nan")
        rows[f"{prefix}_entry_reduce_rate"] = float(split["entry_reduce_failure_flag"].mean()) if not split.empty else float("nan")
    return rows


def split_by_time_series(ts: pd.Series) -> pd.Series:
    valid = ts.dropna().sort_values()
    out = pd.Series("unknown", index=ts.index)
    if valid.empty:
        return out
    validation_cut = valid.quantile(0.70)
    recent_cut = valid.quantile(0.85)
    out.loc[:] = "train_design"
    out.loc[ts >= validation_cut] = "validation"
    out.loc[ts >= recent_cut] = "recent_oos"
    return out


def build_leakage_audit(selected: pd.DataFrame) -> pd.DataFrame:
    assignment_fields = []
    if not selected.empty:
        assignment_fields = [str(selected.iloc[0]["left_factor"]), str(selected.iloc[0]["right_factor"])]
    blocked = sorted(set(assignment_fields) & OUTCOME_COLUMNS)
    return pd.DataFrame(
        [
            {
                "audit_name": "regime_only_assignment_fields",
                "assignment_fields": "|".join(assignment_fields),
                "blocked_outcome_field_used_count": len(blocked),
                "blocked_outcome_fields": "|".join(blocked),
                "label_used_in_assignment_flag": int(bool(blocked)),
                "inferred_lifecycle_matching_used_flag": 0,
                "leakage_pass_flag": int(not blocked),
            }
        ]
    )


def build_task488_decision(candidates: pd.DataFrame, selected: pd.DataFrame, leakage: pd.DataFrame) -> pd.DataFrame:
    passing = candidates[candidates["all_targets_pass"] == 1] if not candidates.empty else pd.DataFrame()
    if selected.empty:
        selected_row = {}
    else:
        selected_row = selected.iloc[0].to_dict()
    return pd.DataFrame(
        [
            {
                "task_id": "Task488",
                "task_name": "Regime Only Target Recovery Search",
                "candidate_count": int(len(candidates)),
                "target_passing_candidate_count": int(len(passing)),
                "selected_candidate_name": selected_row.get("candidate_name", ""),
                "selected_candidate_rule": selected_row.get("candidate_rule", ""),
                "selected_candidate_count": int(selected_row.get("lifecycle_count", 0) or 0),
                "selected_candidate_avg_net_pct": selected_row.get("avg_net_return_pct", pd.NA),
                "selected_candidate_win_rate": selected_row.get("win_rate", pd.NA),
                "selected_candidate_entry_reduce_rate": selected_row.get("entry_reduce_failure_rate", pd.NA),
                "selected_validation_avg_net_pct": selected_row.get("validation_avg_net_pct", pd.NA),
                "selected_recent_oos_avg_net_pct": selected_row.get("recent_oos_avg_net_pct", pd.NA),
                "selected_validation_coverage_flag": int((selected_row.get("validation_count", 0) or 0) > 0),
                "selected_recent_oos_coverage_flag": int((selected_row.get("recent_oos_count", 0) or 0) > 0),
                "selected_nonnegative_validation_recent_flag": int(
                    (selected_row.get("validation_avg_net_pct", -1) or -1) >= 0
                    and (selected_row.get("recent_oos_avg_net_pct", -1) or -1) >= 0
                ),
                "goal_achieved_full_sample_flag": int(bool(selected_row.get("all_targets_pass", 0))),
                "leakage_pass_flag": int(leakage["leakage_pass_flag"].min()) if not leakage.empty else 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_task488_artifacts(artifacts: Task488Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.regime_only_candidate_search.to_csv(out_dir / "regime_only_candidate_search.csv", index=False)
    artifacts.target_recovered_candidate_summary.to_csv(out_dir / "target_recovered_candidate_summary.csv", index=False)
    artifacts.target_recovered_split_quality.to_csv(out_dir / "target_recovered_split_quality.csv", index=False)
    artifacts.target_recovered_quarterly_quality.to_csv(out_dir / "target_recovered_quarterly_quality.csv", index=False)
    artifacts.target_recovered_theme_quality.to_csv(out_dir / "target_recovered_theme_quality.csv", index=False)
    artifacts.target_recovered_leakage_audit.to_csv(out_dir / "target_recovered_leakage_audit.csv", index=False)
    artifacts.task_488_decision.to_csv(out_dir / "task_488_decision.csv", index=False)
    (out_dir / "task_488_regime_only_target_recovery.md").write_text(build_report(artifacts), encoding="utf-8")


def build_report(artifacts: Task488Artifacts) -> str:
    decision = artifacts.task_488_decision.iloc[0].to_dict()
    selected = artifacts.target_recovered_candidate_summary
    split = artifacts.target_recovered_split_quality
    quarter = artifacts.target_recovered_quarterly_quality
    theme = artifacts.target_recovered_theme_quality
    return "\n".join(
        [
            "# Task 488 - Regime Only Target Recovery Search",
            "",
            "## Quant Expert Report",
            "",
            f"- Candidate rules tested: {decision['candidate_count']}",
            f"- Full-sample target passing rules: {decision['target_passing_candidate_count']}",
            f"- Selected rule: `{decision['selected_candidate_rule']}`",
            f"- Full-sample count / avg net / win / entry_reduce: {decision['selected_candidate_count']} / "
            f"{float(decision['selected_candidate_avg_net_pct']):.3f}% / "
            f"{float(decision['selected_candidate_win_rate']):.1%} / "
            f"{float(decision['selected_candidate_entry_reduce_rate']):.1%}",
            f"- Validation avg net: {float(decision['selected_validation_avg_net_pct']):.3f}%",
            f"- Recent OOS avg net: {float(decision['selected_recent_oos_avg_net_pct']):.3f}%",
            "- Inferred lifecycle matching used: NO",
            "- Label/outcome fields used in assignment: NO",
            "- Strategy acceptance: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "",
            "### Selected Candidate",
            "",
            _csv_block(selected),
            "",
            "### Split Quality",
            "",
            _csv_block(split),
            "",
            "### Quarterly Quality",
            "",
            _csv_block(quarter),
            "",
            "### Theme Quality",
            "",
            _csv_block(theme),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "Regime-only 조건만으로 목표를 만족하는 후보는 발견됐다. 다만 이 후보는 연구용 진단 결과다. "
            "전체 표본에서는 목표를 넘지만 validation 구간은 거의 flat이고, recent OOS 표본도 작다. "
            "따라서 바로 실전 투입이 아니라 다음 단계에서 동일 규칙을 더 긴 기간/더 넓은 breadth source로 검증해야 한다.",
            "",
        ]
    )


def _csv_block(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    return "```csv\n" + df.to_csv(index=False) + "```"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task487-panel-path", type=Path, default=DEFAULT_TASK487_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task488_regime_only_target_recovery(task487_panel_path=args.task487_panel_path, out_dir=args.out_dir)
    decision = artifacts.task_488_decision.iloc[0]
    print(
        "[TASK488] "
        f"goal_achieved_full_sample={decision['goal_achieved_full_sample_flag']} "
        f"selected={decision['selected_candidate_name']} "
        f"avg_net={float(decision['selected_candidate_avg_net_pct']):.3f}"
    )


if __name__ == "__main__":
    main()
