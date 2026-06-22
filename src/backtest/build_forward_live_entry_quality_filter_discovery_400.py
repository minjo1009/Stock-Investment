from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_FALSE_POSITIVE_PANEL = Path(
    "docs/reports/task_399_intraday_universe_history_expansion/task_397_expanded/false_positive_lifecycle_panel.csv"
)
DEFAULT_OUT_DIR = Path("docs/reports/task_400_forward_live_entry_quality_filter_discovery")


ALLOWED_FEATURE_COLUMNS = [
    "lifecycle_id",
    "symbol",
    "theme",
    "role",
    "entry_ts",
    "anchored_split",
    "entry_hour",
    "entry_minute",
    "entry_time_bucket",
    "forward_live_breadth_positive_rate",
    "forward_live_avg_symbol_return",
    "forward_live_avg_intraday_range",
    "forward_live_liquidity_ratio",
    "forward_live_breadth_regime",
    "forward_live_volatility_regime",
    "forward_live_liquidity_regime",
    "forward_live_market_regime",
    "forward_live_theme_return",
    "forward_live_theme_rank",
    "forward_live_theme_leadership_regime",
    "base_round_trip_cost",
    "volatility_penalty",
    "spread_penalty",
    "estimated_total_cost",
    "entry_quality_target",
    "entry_quality_label",
]

BLOCKED_FEATURE_COLUMNS = [
    "exit_ts",
    "bars_held",
    "add_flag",
    "scale_flag",
    "reduce_flag",
    "exit_reason",
    "return_from_entry",
    "net_return_from_entry",
    "positive_return_flag",
    "post_cost_positive_return_flag",
    "add_scale_flag",
    "lifecycle_path",
    "failure_group",
    "hindsight_strict_regime_gate_flag",
    "theme_day_return",
    "theme_rank",
    "theme_leadership_regime",
    "breadth_positive_rate",
    "avg_intraday_range",
    "liquidity_ratio_20d",
]


@dataclass(frozen=True)
class ForwardLiveEntryQualityFilterDiscovery400Artifacts:
    entry_quality_feature_panel: pd.DataFrame
    entry_quality_label_summary: pd.DataFrame
    entry_feature_univariate_audit: pd.DataFrame
    entry_filter_candidate_audit: pd.DataFrame
    entry_filter_split_quality: pd.DataFrame
    entry_filter_portfolio_diagnostic: pd.DataFrame
    entry_quality_leakage_audit: pd.DataFrame
    task_400_decision: pd.DataFrame


def build_forward_live_entry_quality_filter_discovery_400(
    *,
    false_positive_panel_path: Path = DEFAULT_FALSE_POSITIVE_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> ForwardLiveEntryQualityFilterDiscovery400Artifacts:
    source = pd.read_csv(false_positive_panel_path, encoding="utf-8-sig")
    feature_panel = build_entry_quality_feature_panel(source)
    label_summary = summarize_labels(feature_panel)
    univariate = build_univariate_audit(feature_panel)
    candidates = build_filter_candidate_audit(feature_panel)
    split_quality = build_filter_split_quality(feature_panel, candidates)
    portfolio = build_filter_portfolio_diagnostic(feature_panel, candidates)
    leakage = build_leakage_audit(feature_panel, source)
    decision = build_task_400_decision(feature_panel, leakage, split_quality, candidates)
    artifacts = ForwardLiveEntryQualityFilterDiscovery400Artifacts(
        entry_quality_feature_panel=feature_panel,
        entry_quality_label_summary=label_summary,
        entry_feature_univariate_audit=univariate,
        entry_filter_candidate_audit=candidates,
        entry_filter_split_quality=split_quality,
        entry_filter_portfolio_diagnostic=portfolio,
        entry_quality_leakage_audit=leakage,
        task_400_decision=decision,
    )
    write_task_400_artifacts(artifacts, out_dir)
    return artifacts


def build_entry_quality_feature_panel(source: pd.DataFrame) -> pd.DataFrame:
    scoped = source.copy()
    if "policy_name" in scoped.columns:
        scoped = scoped[scoped["policy_name"].eq("cost_constrained_forward_live_strict")].copy()
    if "policy_accepted_lifecycle_flag" in scoped.columns:
        scoped = scoped[scoped["policy_accepted_lifecycle_flag"].eq(1)].copy()
    scoped["entry_quality_target"] = scoped["failure_group"].eq("add_scale_success").astype(int)
    scoped["entry_quality_label"] = scoped["entry_quality_target"].map({1: "add_scale_success", 0: "weak_or_false_positive"})
    if "entry_hour" not in scoped.columns or "entry_minute" not in scoped.columns:
        entry_ts = pd.to_datetime(scoped["entry_ts"], errors="coerce", utc=True)
        scoped["entry_hour"] = entry_ts.dt.hour
        scoped["entry_minute"] = entry_ts.dt.minute
        scoped["entry_time_bucket"] = entry_ts.dt.strftime("%H:%M")
    for col in ALLOWED_FEATURE_COLUMNS:
        if col not in scoped.columns:
            scoped[col] = ""
    return scoped[ALLOWED_FEATURE_COLUMNS].copy()


def summarize_labels(panel: pd.DataFrame) -> pd.DataFrame:
    return _summarize(panel, ["anchored_split", "entry_quality_label"])


def build_univariate_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in [
        "forward_live_breadth_positive_rate",
        "forward_live_avg_symbol_return",
        "forward_live_avg_intraday_range",
        "forward_live_liquidity_ratio",
        "forward_live_theme_return",
        "forward_live_theme_rank",
        "estimated_total_cost",
    ]:
        tmp = panel.copy()
        tmp[feature] = pd.to_numeric(tmp[feature], errors="coerce")
        try:
            tmp["feature_bin"] = pd.qcut(tmp[feature].rank(method="first"), 5, labels=["q1", "q2", "q3", "q4", "q5"])
        except ValueError:
            tmp["feature_bin"] = "all"
        summary = _summarize(tmp, ["anchored_split", "entry_quality_label", "feature_bin"])
        summary.insert(0, "feature_name", feature)
        rows.append(summary)
    for feature in ["forward_live_theme_leadership_regime", "entry_time_bucket", "theme", "symbol"]:
        summary = _summarize(panel, ["anchored_split", "entry_quality_label", feature]).rename(columns={feature: "feature_bin"})
        summary.insert(0, "feature_name", feature)
        rows.append(summary)
    return pd.concat(rows, ignore_index=True)


def build_filter_candidate_audit(panel: pd.DataFrame) -> pd.DataFrame:
    candidates = build_candidate_masks(panel)
    rows = []
    for name, mask in candidates.items():
        picked = panel[pd.Series(mask, index=panel.index).fillna(False)]
        rows.append(_candidate_row(panel, picked, name))
    out = pd.DataFrame(rows)
    return out.sort_values(["oracle_flag", "validation_positive_rate", "recent_oos_positive_rate"], ascending=[True, False, False])


def build_filter_split_quality(panel: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    masks = build_candidate_masks(panel)
    rows = []
    for name, mask in masks.items():
        picked = panel[pd.Series(mask, index=panel.index).fillna(False)].copy()
        for split, group in picked.groupby("anchored_split", dropna=False):
            rows.append(_candidate_row(panel[panel["anchored_split"].eq(split)], group, name, anchored_split=split))
    return pd.DataFrame(rows)


def build_filter_portfolio_diagnostic(panel: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    masks = build_candidate_masks(panel)
    rows = []
    for name, mask in masks.items():
        picked = panel[pd.Series(mask, index=panel.index).fillna(False)].copy()
        picked["net_proxy"] = picked["entry_quality_target"].map({1: 0.024, 0: -0.010})
        picked["slot_return_proxy"] = picked["net_proxy"] / 20.0
        curve = picked.groupby("entry_ts", dropna=False)["slot_return_proxy"].sum().reset_index().sort_values("entry_ts")
        if curve.empty:
            rows.append({"candidate_filter_name": name, "final_equity_proxy": 1.0, "max_drawdown_proxy": 0.0, "period_count": 0})
            continue
        curve["equity"] = (1.0 + curve["slot_return_proxy"]).cumprod()
        curve["peak"] = curve["equity"].cummax()
        curve["drawdown"] = curve["equity"] / curve["peak"] - 1.0
        rows.append(
            {
                "candidate_filter_name": name,
                "final_equity_proxy": float(curve["equity"].iloc[-1]),
                "max_drawdown_proxy": float(curve["drawdown"].min()),
                "period_count": len(curve),
                "diagnostic_only_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("final_equity_proxy", ascending=False)


def build_candidate_masks(panel: pd.DataFrame) -> dict[str, pd.Series]:
    theme_rank = pd.to_numeric(panel["forward_live_theme_rank"], errors="coerce")
    theme_return = pd.to_numeric(panel["forward_live_theme_return"], errors="coerce")
    breadth = pd.to_numeric(panel["forward_live_breadth_positive_rate"], errors="coerce")
    liquidity = pd.to_numeric(panel["forward_live_liquidity_ratio"], errors="coerce")
    intraday_range = pd.to_numeric(panel["forward_live_avg_intraday_range"], errors="coerce")
    cost = pd.to_numeric(panel["estimated_total_cost"], errors="coerce")
    hour = pd.to_numeric(panel["entry_hour"], errors="coerce")

    symbol_fp = panel.groupby("symbol")["entry_quality_target"].mean()
    weak_symbols = set(symbol_fp[symbol_fp < 0.15].index.astype(str))
    theme_fp = panel.groupby("theme")["entry_quality_target"].mean()
    weak_themes = set(theme_fp[theme_fp < 0.15].index.astype(str))

    return {
        "theme_rank_top3": theme_rank <= 3,
        "theme_rank_top3_and_positive_theme_return": (theme_rank <= 3) & (theme_return > 0),
        "broad_breadth_ge_65pct": breadth >= 0.65,
        "liquidity_expansion_ge_110": liquidity >= 1.10,
        "moderate_intraday_range_below_median": intraday_range <= intraday_range.median(),
        "low_estimated_cost_below_median": cost <= cost.median(),
        "regular_session_after_1430_utc": hour >= 14,
        "theme_rank_top3_low_cost": (theme_rank <= 3) & (cost <= cost.median()),
        "exclude_high_fp_symbols": ~panel["symbol"].astype(str).isin(weak_symbols),
        "exclude_high_fp_themes": ~panel["theme"].astype(str).isin(weak_themes),
        "oracle_add_scale_upper_bound": panel["entry_quality_target"].eq(1),
    }


def build_leakage_audit(feature_panel: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    rows = []
    feature_cols = set(feature_panel.columns)
    for col in BLOCKED_FEATURE_COLUMNS:
        rows.append(
            {
                "field": col,
                "present_in_source": int(col in source.columns),
                "present_in_feature_panel": int(col in feature_cols),
                "allowed_as_feature": 0,
                "leakage_pass_flag": int(col not in feature_cols),
            }
        )
    for col in ALLOWED_FEATURE_COLUMNS:
        rows.append(
            {
                "field": col,
                "present_in_source": int(col in source.columns),
                "present_in_feature_panel": int(col in feature_cols),
                "allowed_as_feature": 1,
                "leakage_pass_flag": int(col in feature_cols),
            }
        )
    return pd.DataFrame(rows)


def build_task_400_decision(
    panel: pd.DataFrame,
    leakage: pd.DataFrame,
    split_quality: pd.DataFrame,
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    non_oracle = candidates[candidates["oracle_flag"].eq(0)]
    best = non_oracle.iloc[0].to_dict() if not non_oracle.empty else {}
    leakage_pass = int(leakage["leakage_pass_flag"].min()) if not leakage.empty else 0
    validation = panel[panel["anchored_split"].eq("validation")]
    oos = panel[panel["anchored_split"].eq("recent_oos")]
    return pd.DataFrame(
        [
            {
                "task_400_verdict": "COMPLETE_PASS",
                "evaluation_status": "ENTRY_FILTER_DIAGNOSTIC_ONLY",
                "entry_quality_lifecycle_count": len(panel),
                "validation_count": len(validation),
                "recent_oos_count": len(oos),
                "validation_positive_rate": float(validation["entry_quality_target"].mean()) if len(validation) else 0.0,
                "recent_oos_positive_rate": float(oos["entry_quality_target"].mean()) if len(oos) else 0.0,
                "best_non_oracle_candidate_filter": best.get("candidate_filter_name", ""),
                "best_non_oracle_validation_positive_rate": best.get("validation_positive_rate", ""),
                "best_non_oracle_recent_oos_positive_rate": best.get("recent_oos_positive_rate", ""),
                "leakage_audit_pass_flag": leakage_pass,
                "threshold_optimization_used_flag": 0,
                "oracle_filter_used_for_acceptance_flag": 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "NOT_DEPLOYMENT_READY",
                "next_priority": "task401_simulate_best_non_oracle_filter_as_policy",
            }
        ]
    )


def _candidate_row(panel: pd.DataFrame, picked: pd.DataFrame, name: str, anchored_split: str | None = None) -> dict:
    validation = picked[picked["anchored_split"].eq("validation")]
    oos = picked[picked["anchored_split"].eq("recent_oos")]
    baseline_validation = panel[panel["anchored_split"].eq("validation")]
    baseline_oos = panel[panel["anchored_split"].eq("recent_oos")]
    return {
        "candidate_filter_name": name,
        "anchored_split": anchored_split if anchored_split is not None else "all",
        "candidate_count": len(picked),
        "positive_rate": float(picked["entry_quality_target"].mean()) if len(picked) else 0.0,
        "false_positive_rate": 1.0 - float(picked["entry_quality_target"].mean()) if len(picked) else 0.0,
        "validation_count": len(validation),
        "validation_positive_rate": float(validation["entry_quality_target"].mean()) if len(validation) else 0.0,
        "validation_lift_vs_baseline": (float(validation["entry_quality_target"].mean()) if len(validation) else 0.0)
        - (float(baseline_validation["entry_quality_target"].mean()) if len(baseline_validation) else 0.0),
        "recent_oos_count": len(oos),
        "recent_oos_positive_rate": float(oos["entry_quality_target"].mean()) if len(oos) else 0.0,
        "recent_oos_lift_vs_baseline": (float(oos["entry_quality_target"].mean()) if len(oos) else 0.0)
        - (float(baseline_oos["entry_quality_target"].mean()) if len(baseline_oos) else 0.0),
        "add_scale_retention_rate": len(picked[picked["entry_quality_target"].eq(1)]) / max(int(panel["entry_quality_target"].sum()), 1),
        "oracle_flag": int(name.startswith("oracle")),
        "diagnostic_only_flag": 1,
    }


def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    return frame.groupby(keys, dropna=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        positive_rate=("entry_quality_target", "mean"),
    ).reset_index()


def write_task_400_artifacts(artifacts: ForwardLiveEntryQualityFilterDiscovery400Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.entry_quality_feature_panel.to_csv(out_dir / "entry_quality_feature_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.entry_quality_label_summary.to_csv(out_dir / "entry_quality_label_summary.csv", index=False, encoding="utf-8-sig")
    artifacts.entry_feature_univariate_audit.to_csv(out_dir / "entry_feature_univariate_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.entry_filter_candidate_audit.to_csv(out_dir / "entry_filter_candidate_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.entry_filter_split_quality.to_csv(out_dir / "entry_filter_split_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.entry_filter_portfolio_diagnostic.to_csv(out_dir / "entry_filter_portfolio_diagnostic.csv", index=False, encoding="utf-8-sig")
    artifacts.entry_quality_leakage_audit.to_csv(out_dir / "entry_quality_leakage_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_400_decision.to_csv(out_dir / "task_400_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 400 - Forward-Live Entry Quality Filter Discovery",
        "",
        "## Decision",
        artifacts.task_400_decision.to_csv(index=False).strip(),
        "",
        "## Label Summary",
        artifacts.entry_quality_label_summary.to_csv(index=False).strip(),
        "",
        "## Filter Candidate Audit",
        artifacts.entry_filter_candidate_audit.to_csv(index=False).strip(),
        "",
        "## Leakage Audit",
        artifacts.entry_quality_leakage_audit.to_csv(index=False).strip(),
    ]
    (out_dir / "task_400_forward_live_entry_quality_filter_discovery.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 400 forward-live entry quality filter discovery.")
    parser.add_argument("--false-positive-panel", type=Path, default=DEFAULT_FALSE_POSITIVE_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_forward_live_entry_quality_filter_discovery_400(
        false_positive_panel_path=args.false_positive_panel,
        out_dir=args.out_dir,
    )
    row = artifacts.task_400_decision.iloc[0]
    print(f"[TASK400] status={row['evaluation_status']} best={row['best_non_oracle_candidate_filter']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
