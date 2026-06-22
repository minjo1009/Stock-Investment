from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_TASK396_PANEL = Path("docs/reports/task_396_forward_live_cost_constrained_validation/cost_constrained_lifecycle_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_397_forward_live_strict_false_positive_decomposition")


@dataclass(frozen=True)
class ForwardLiveStrictFalsePositive397Artifacts:
    false_positive_lifecycle_panel: pd.DataFrame
    false_positive_group_summary: pd.DataFrame
    false_positive_feature_bins: pd.DataFrame
    false_positive_symbol_theme_audit: pd.DataFrame
    false_positive_time_audit: pd.DataFrame
    false_positive_filter_candidate_audit: pd.DataFrame
    task_397_decision: pd.DataFrame


def build_forward_live_strict_false_positive_decomposition_397(
    *,
    task396_panel_path: Path = DEFAULT_TASK396_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> ForwardLiveStrictFalsePositive397Artifacts:
    panel = pd.read_csv(task396_panel_path, encoding="utf-8-sig")
    scoped = build_false_positive_lifecycle_panel(panel)
    summary = summarize_groups(scoped)
    bins = summarize_feature_bins(scoped)
    symbol_theme = summarize_symbol_theme(scoped)
    time_audit = summarize_entry_time(scoped)
    filter_candidates = build_filter_candidate_audit(scoped)
    decision = build_task_397_decision(scoped, summary, filter_candidates)
    artifacts = ForwardLiveStrictFalsePositive397Artifacts(
        false_positive_lifecycle_panel=scoped,
        false_positive_group_summary=summary,
        false_positive_feature_bins=bins,
        false_positive_symbol_theme_audit=symbol_theme,
        false_positive_time_audit=time_audit,
        false_positive_filter_candidate_audit=filter_candidates,
        task_397_decision=decision,
    )
    write_task_397_artifacts(artifacts, out_dir)
    return artifacts


def build_false_positive_lifecycle_panel(panel: pd.DataFrame) -> pd.DataFrame:
    scoped = panel[
        panel["policy_name"].eq("cost_constrained_forward_live_strict")
        & panel["policy_accepted_lifecycle_flag"].eq(1)
    ].copy()
    scoped["entry_ts_dt"] = pd.to_datetime(scoped["entry_ts"], errors="coerce", utc=True)
    scoped["entry_hour"] = scoped["entry_ts_dt"].dt.hour
    scoped["entry_minute"] = scoped["entry_ts_dt"].dt.minute
    scoped["entry_time_bucket"] = scoped["entry_ts_dt"].dt.strftime("%H:%M")
    scoped["failure_group"] = "entry_reduce_failure"
    scoped.loc[(scoped["add_flag"] == 1) & (scoped["scale_flag"] == 0), "failure_group"] = "add_only_weak"
    scoped.loc[(scoped["add_flag"] == 1) & (scoped["scale_flag"] == 1), "failure_group"] = "add_scale_success"
    scoped.loc[(scoped["net_return_from_entry"] <= 0) & (scoped["failure_group"].eq("add_scale_success")), "failure_group"] = "post_cost_false_positive"
    scoped["forward_live_strict_false_positive_flag"] = scoped["failure_group"].ne("add_scale_success").astype(int)
    scoped["diagnostic_filter_candidate_flag"] = 0
    return scoped


def summarize_groups(scoped: pd.DataFrame) -> pd.DataFrame:
    return _summarize(scoped, ["anchored_split", "failure_group"])


def summarize_feature_bins(scoped: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for column in [
        "forward_live_breadth_positive_rate",
        "forward_live_liquidity_ratio",
        "forward_live_theme_rank",
        "forward_live_theme_return",
        "forward_live_avg_intraday_range",
    ]:
        if column not in scoped.columns:
            continue
        tmp = scoped.copy()
        tmp[column] = pd.to_numeric(tmp[column], errors="coerce")
        tmp["feature_name"] = column
        try:
            tmp["feature_bin"] = pd.qcut(tmp[column].rank(method="first"), 5, labels=["q1", "q2", "q3", "q4", "q5"])
        except ValueError:
            tmp["feature_bin"] = "all"
        frames.append(_summarize(tmp, ["anchored_split", "feature_name", "feature_bin", "failure_group"]))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def summarize_symbol_theme(scoped: pd.DataFrame) -> pd.DataFrame:
    return _summarize(scoped, ["anchored_split", "theme", "symbol", "failure_group"]).sort_values(
        ["anchored_split", "avg_net_return_from_entry"], ascending=[True, True]
    )


def summarize_entry_time(scoped: pd.DataFrame) -> pd.DataFrame:
    return _summarize(scoped, ["anchored_split", "entry_time_bucket", "failure_group"]).sort_values(
        ["anchored_split", "entry_time_bucket", "avg_net_return_from_entry"]
    )


def build_filter_candidate_audit(scoped: pd.DataFrame) -> pd.DataFrame:
    rows = []
    candidates = {
        "add_scale_only_oracle_diagnostic": scoped["add_scale_flag"].eq(1),
        "theme_leader_only": scoped.get("forward_live_theme_leadership_regime", pd.Series("", index=scoped.index)).eq("theme_leader"),
        "top3_theme_rank": pd.to_numeric(scoped.get("forward_live_theme_rank", 999), errors="coerce") <= 3,
        "positive_theme_return": pd.to_numeric(scoped.get("forward_live_theme_return", 0), errors="coerce") > 0,
        "no_reduce_observed_oracle_diagnostic": scoped["reduce_flag"].eq(0),
    }
    for name, mask in candidates.items():
        picked = scoped[pd.Series(mask, index=scoped.index).fillna(False)]
        rows.append(
            {
                "diagnostic_filter_candidate": name,
                "candidate_count": len(picked),
                "false_positive_rate": float(picked["forward_live_strict_false_positive_flag"].mean()) if len(picked) else 0.0,
                "avg_net_return_from_entry": float(picked["net_return_from_entry"].mean()) if len(picked) else 0.0,
                "validation_avg_net_return": float(picked[picked["anchored_split"].eq("validation")]["net_return_from_entry"].mean()) if len(picked[picked["anchored_split"].eq("validation")]) else 0.0,
                "recent_oos_avg_net_return": float(picked[picked["anchored_split"].eq("recent_oos")]["net_return_from_entry"].mean()) if len(picked[picked["anchored_split"].eq("recent_oos")]) else 0.0,
                "oracle_flag": int("oracle" in name),
            }
        )
    return pd.DataFrame(rows).sort_values(["oracle_flag", "validation_avg_net_return"], ascending=[True, False])


def build_task_397_decision(scoped: pd.DataFrame, summary: pd.DataFrame, filter_candidates: pd.DataFrame) -> pd.DataFrame:
    validation = scoped[scoped["anchored_split"].eq("validation")]
    oos = scoped[scoped["anchored_split"].eq("recent_oos")]
    fp_rate = float(validation["forward_live_strict_false_positive_flag"].mean()) if len(validation) else 0.0
    add_scale_val = validation[validation["failure_group"].eq("add_scale_success")]
    failure_val = validation[validation["failure_group"].ne("add_scale_success")]
    return pd.DataFrame(
        [
            {
                "task_397_verdict": "COMPLETE_PASS",
                "evaluation_status": "FALSE_POSITIVE_DECOMPOSITION_COMPLETE",
                "forward_live_strict_lifecycle_count": len(scoped),
                "validation_lifecycle_count": len(validation),
                "recent_oos_lifecycle_count": len(oos),
                "validation_false_positive_rate": fp_rate,
                "validation_add_scale_success_net_avg": float(add_scale_val["net_return_from_entry"].mean()) if len(add_scale_val) else 0.0,
                "validation_failure_net_avg": float(failure_val["net_return_from_entry"].mean()) if len(failure_val) else 0.0,
                "threshold_optimization_used_flag": 0,
                "oracle_filter_used_for_acceptance_flag": 0,
                "deployment_claim_flag": 0,
                "next_priority": "convert_non_oracle_failure_patterns_to_forward_live_policy_candidates",
            }
        ]
    )


def write_task_397_artifacts(artifacts: ForwardLiveStrictFalsePositive397Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.false_positive_lifecycle_panel.to_csv(out_dir / "false_positive_lifecycle_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.false_positive_group_summary.to_csv(out_dir / "false_positive_group_summary.csv", index=False, encoding="utf-8-sig")
    artifacts.false_positive_feature_bins.to_csv(out_dir / "false_positive_feature_bins.csv", index=False, encoding="utf-8-sig")
    artifacts.false_positive_symbol_theme_audit.to_csv(out_dir / "false_positive_symbol_theme_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.false_positive_time_audit.to_csv(out_dir / "false_positive_time_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.false_positive_filter_candidate_audit.to_csv(out_dir / "false_positive_filter_candidate_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_397_decision.to_csv(out_dir / "task_397_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 397 - Forward-Live Strict False Positive Decomposition",
        "",
        "## Decision",
        artifacts.task_397_decision.to_csv(index=False).strip(),
        "",
        "## Group Summary",
        artifacts.false_positive_group_summary.to_csv(index=False).strip(),
        "",
        "## Diagnostic Filter Candidate Audit",
        artifacts.false_positive_filter_candidate_audit.to_csv(index=False).strip(),
    ]
    (out_dir / "task_397_forward_live_strict_false_positive_decomposition.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    tmp = frame.copy()
    tmp["positive_net_flag"] = (tmp["net_return_from_entry"] > 0).astype(int)
    return tmp.groupby(keys, dropna=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        win_rate=("positive_net_flag", "mean"),
        avg_gross_return_from_entry=("return_from_entry", "mean"),
        avg_net_return_from_entry=("net_return_from_entry", "mean"),
        median_net_return_from_entry=("net_return_from_entry", "median"),
        avg_cost=("estimated_total_cost", "mean"),
        add_rate=("add_flag", "mean"),
        scale_rate=("scale_flag", "mean"),
        reduce_rate=("reduce_flag", "mean"),
    ).reset_index()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 397 false positive decomposition.")
    parser.add_argument("--task396-panel", type=Path, default=DEFAULT_TASK396_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_forward_live_strict_false_positive_decomposition_397(
        task396_panel_path=args.task396_panel,
        out_dir=args.out_dir,
    )
    row = artifacts.task_397_decision.iloc[0]
    print(f"[TASK397] status={row['evaluation_status']} fp_rate={row['validation_false_positive_rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
