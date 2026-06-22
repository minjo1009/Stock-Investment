from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task634"
REPORT_DIR = Path("docs/reports/task_634_information_predictive_value_audit")
TASK633_DIR = Path("docs/reports/task_633_qqq_benchmark_full_period_refresh")
SCORED = TASK633_DIR / "task632_temporal_strict_refresh" / "task_632_temporal_strict_scored_entry_panel.csv"
ORIGINAL_PANEL = TASK633_DIR / "task617_refreshed_inputs" / "fresh_turboquant_strategy_backtest_panel.csv"
STRICT_PANEL = TASK633_DIR / "task632_temporal_strict_refresh" / "task_632_temporal_strict_strategy_backtest_panel.csv"

FEATURES = [
    "temporal_political_fresh_pre72h_flag",
    "temporal_geopolitical_fresh_pre72h_flag",
    "temporal_institution_pre30d_flag",
    "temporal_passive_13g_pre30d_flag",
    "temporal_insider_form4_or_144_pre30d_flag",
    "temporal_ceo_ir_proxy_pre14d_flag",
    "p0_source_event_density_ge2_flag",
]


def build_task634_information_predictive_value_audit(
    *,
    scored_path: Path = SCORED,
    original_panel_path: Path = ORIGINAL_PANEL,
    strict_panel_path: Path = STRICT_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    scored = pd.read_csv(scored_path)
    original = normalize_panel(pd.read_csv(original_panel_path))
    strict = normalize_panel(pd.read_csv(strict_panel_path))
    analysis = build_analysis_frame(scored, original, strict)
    feature_audit = build_feature_predictive_audit(analysis)
    strict_damage = build_strict_filter_damage(analysis)
    missed_winners = build_extreme_table(analysis, keep_strict=False, ascending=False)
    retained_losers = build_extreme_table(analysis, keep_strict=True, ascending=True)
    pass_fail = build_pass_fail(feature_audit, strict_damage)
    decision = build_decision(feature_audit, strict_damage, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    feature_audit.to_csv(out_dir / "task_634_feature_predictive_value_audit.csv", index=False)
    strict_damage.to_csv(out_dir / "task_634_strict_filter_damage_audit.csv", index=False)
    missed_winners.to_csv(out_dir / "task_634_missed_winners.csv", index=False)
    retained_losers.to_csv(out_dir / "task_634_retained_losers.csv", index=False)
    pass_fail.to_csv(out_dir / "task_634_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_634_decision.csv", index=False)
    (out_dir / "task_634_information_predictive_value_audit.md").write_text(
        render_report(feature_audit, strict_damage, missed_winners, retained_losers, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_634_feature_predictive_value_audit": feature_audit,
        "task_634_strict_filter_damage_audit": strict_damage,
        "task_634_missed_winners": missed_winners,
        "task_634_retained_losers": retained_losers,
        "task_634_pass_fail_matrix": pass_fail,
        "task_634_decision": decision,
    }


def normalize_panel(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["lifecycle_id"] = out["lifecycle_id"].astype(str)
    out["net_return_pct"] = pd.to_numeric(out["net_return_from_entry"], errors="coerce") * 100.0
    out["win_eval_flag"] = out["net_return_pct"].gt(0).astype(int)
    out["entry_reduce_eval_flag"] = out["net_return_pct"].le(-3.0).astype(int)
    return out


def build_analysis_frame(scored: pd.DataFrame, original: pd.DataFrame, strict: pd.DataFrame) -> pd.DataFrame:
    strict_ids = set(strict["lifecycle_id"].astype(str))
    keep_cols = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "entry_ts",
        "split_name",
        "net_return_pct",
        "win_eval_flag",
        "entry_reduce_eval_flag",
    ]
    returns = original[keep_cols].copy()
    out = scored.merge(returns, on="lifecycle_id", how="inner", suffixes=("", "_ret"))
    out["strict_kept_flag"] = out["lifecycle_id"].astype(str).isin(strict_ids).astype(int)
    for feature in FEATURES:
        if feature not in out.columns:
            out[feature] = 0
        out[feature] = pd.to_numeric(out[feature], errors="coerce").fillna(0).astype(int)
    out["temporal_source_event_density"] = pd.to_numeric(out["temporal_source_event_density"], errors="coerce").fillna(0)
    out["temporal_source_time_gap_count"] = pd.to_numeric(out["temporal_source_time_gap_count"], errors="coerce").fillna(0)
    out["source_density_high_flag"] = out["temporal_source_event_density"].ge(out["temporal_source_event_density"].median()).astype(int)
    out["source_time_gap_high_flag"] = out["temporal_source_time_gap_count"].ge(out["temporal_source_time_gap_count"].median()).astype(int)
    return out


def metrics(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {
            "count": 0,
            "avg_return_pct": float("nan"),
            "sum_return_pct": 0.0,
            "win_rate": float("nan"),
            "entry_reduce_rate": float("nan"),
        }
    return {
        "count": int(len(frame)),
        "avg_return_pct": float(frame["net_return_pct"].mean()),
        "sum_return_pct": float(frame["net_return_pct"].sum()),
        "win_rate": float(frame["win_eval_flag"].mean()),
        "entry_reduce_rate": float(frame["entry_reduce_eval_flag"].mean()),
    }


def build_feature_predictive_audit(analysis: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    candidate_features = FEATURES + ["source_density_high_flag", "source_time_gap_high_flag"]
    for feature in candidate_features:
        for split_name in ["all", "train_design", "validation", "recent_oos"]:
            subset = analysis if split_name == "all" else analysis[analysis["split_name"].astype(str).eq(split_name)]
            yes = subset[subset[feature].astype(int).eq(1)]
            no = subset[subset[feature].astype(int).eq(0)]
            yes_m = metrics(yes)
            no_m = metrics(no)
            rows.append(
                {
                    "feature": feature,
                    "split_name": split_name,
                    "feature_1_count": yes_m["count"],
                    "feature_0_count": no_m["count"],
                    "feature_1_avg_return_pct": yes_m["avg_return_pct"],
                    "feature_0_avg_return_pct": no_m["avg_return_pct"],
                    "avg_return_lift_pct_point": yes_m["avg_return_pct"] - no_m["avg_return_pct"],
                    "feature_1_win_rate": yes_m["win_rate"],
                    "feature_0_win_rate": no_m["win_rate"],
                    "feature_1_entry_reduce_rate": yes_m["entry_reduce_rate"],
                    "feature_0_entry_reduce_rate": no_m["entry_reduce_rate"],
                    "entry_reduce_delta_pct_point": (yes_m["entry_reduce_rate"] - no_m["entry_reduce_rate"]) * 100.0,
                    "feature_1_sum_return_pct": yes_m["sum_return_pct"],
                    "feature_0_sum_return_pct": no_m["sum_return_pct"],
                }
            )
    out = pd.DataFrame(rows)
    return add_feature_stability(out)


def add_feature_stability(audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature, group in audit.groupby("feature", dropna=False):
        train = group[group["split_name"].eq("train_design")].iloc[0]
        validation = group[group["split_name"].eq("validation")].iloc[0]
        recent = group[group["split_name"].eq("recent_oos")].iloc[0]
        stable = (
            int(train["feature_1_count"]) >= 30
            and int(validation["feature_1_count"]) >= 20
            and int(recent["feature_1_count"]) >= 10
            and float(validation["avg_return_lift_pct_point"]) > 0
            and float(recent["avg_return_lift_pct_point"]) > 0
            and float(validation["entry_reduce_delta_pct_point"]) <= 0
            and float(recent["entry_reduce_delta_pct_point"]) <= 0
        )
        rows.append(
            {
                "feature": feature,
                "predictive_stability_pass_flag": int(stable),
                "reason": "passes validation and recent return lift with no worse entry-reduce"
                if stable
                else "does not prove stable predictive value across validation and recent OOS",
            }
        )
    stability = pd.DataFrame(rows)
    return audit.merge(stability, on="feature", how="left")


def build_strict_filter_damage(analysis: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, frame in [
        ("task617_original_all", analysis),
        ("task632_strict_kept", analysis[analysis["strict_kept_flag"].eq(1)]),
        ("task617_missed_by_strict", analysis[analysis["strict_kept_flag"].eq(0)]),
    ]:
        row = {"bucket": name, **metrics(frame)}
        row["top10_winner_sum_pct"] = float(frame.sort_values("net_return_pct", ascending=False).head(10)["net_return_pct"].sum()) if not frame.empty else 0.0
        row["bottom10_loser_sum_pct"] = float(frame.sort_values("net_return_pct", ascending=True).head(10)["net_return_pct"].sum()) if not frame.empty else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def build_extreme_table(analysis: pd.DataFrame, *, keep_strict: bool, ascending: bool) -> pd.DataFrame:
    subset = analysis[analysis["strict_kept_flag"].eq(1 if keep_strict else 0)].copy()
    columns = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name", "net_return_pct"] + FEATURES
    return subset.sort_values("net_return_pct", ascending=ascending)[columns].head(25).reset_index(drop=True)


def build_pass_fail(feature_audit: pd.DataFrame, strict_damage: pd.DataFrame) -> pd.DataFrame:
    stable_feature_count = int(feature_audit[["feature", "predictive_stability_pass_flag"]].drop_duplicates()["predictive_stability_pass_flag"].sum())
    kept_avg = float(strict_damage[strict_damage["bucket"].eq("task632_strict_kept")].iloc[0]["avg_return_pct"])
    missed_avg = float(strict_damage[strict_damage["bucket"].eq("task617_missed_by_strict")].iloc[0]["avg_return_pct"])
    kept_er = float(strict_damage[strict_damage["bucket"].eq("task632_strict_kept")].iloc[0]["entry_reduce_rate"])
    missed_er = float(strict_damage[strict_damage["bucket"].eq("task617_missed_by_strict")].iloc[0]["entry_reduce_rate"])
    return pd.DataFrame(
        [
            {
                "gate": "information_features_have_predictive_value",
                "pass_flag": int(stable_feature_count > 0),
                "observed_value": f"stable_predictive_features={stable_feature_count}",
                "required_value": "at least one information feature must improve validation and recent OOS return without worse entry-reduce",
            },
            {
                "gate": "strict_filter_does_not_discard_better_trades",
                "pass_flag": int(kept_avg >= missed_avg),
                "observed_value": f"kept_avg={kept_avg:.2f}%; missed_avg={missed_avg:.2f}%",
                "required_value": "strict information filter should not discard a higher-return bucket",
            },
            {
                "gate": "strict_filter_reduces_entry_reduce",
                "pass_flag": int(kept_er <= missed_er),
                "observed_value": f"kept_entry_reduce={kept_er:.2%}; missed_entry_reduce={missed_er:.2%}",
                "required_value": "strict information filter should lower entry-reduce failure",
            },
            {
                "gate": "presence_based_information_scoring",
                "pass_flag": 0,
                "observed_value": "current strict score still rewards source/event presence",
                "required_value": "replace presence scoring with relevance and predictive validation gates",
            },
        ]
    )


def build_decision(feature_audit: pd.DataFrame, strict_damage: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    kept = strict_damage[strict_damage["bucket"].eq("task632_strict_kept")].iloc[0]
    missed = strict_damage[strict_damage["bucket"].eq("task617_missed_by_strict")].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "FAIL_INFORMATION_PRESENCE_NOT_PREDICTIVE_NOT_ACCEPTED",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "stable_predictive_feature_count": int(feature_audit[["feature", "predictive_stability_pass_flag"]].drop_duplicates()["predictive_stability_pass_flag"].sum()),
                "strict_kept_count": int(kept["count"]),
                "strict_kept_avg_return_pct": float(kept["avg_return_pct"]),
                "missed_by_strict_count": int(missed["count"]),
                "missed_by_strict_avg_return_pct": float(missed["avg_return_pct"]),
                "trading_promotion_pass_flag": 0,
                "next_action": "Replace event presence scoring with event-to-symbol relevance and validation/recent-OOS predictive gates before using information in assignment.",
            }
        ]
    )


def render_report(
    feature_audit: pd.DataFrame,
    strict_damage: pd.DataFrame,
    missed_winners: pd.DataFrame,
    retained_losers: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task634 Information Predictive Value Audit",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Stable predictive information features: {int(d['stable_predictive_feature_count'])}",
        f"- Strict kept: {int(d['strict_kept_count'])} trades at {float(d['strict_kept_avg_return_pct']):.2f}% average",
        f"- Strict missed: {int(d['missed_by_strict_count'])} trades at {float(d['missed_by_strict_avg_return_pct']):.2f}% average",
        "",
        "## Quant Expert Report",
        "",
        "This audit tests whether the information columns predict price outcomes. The current strict strategy is not accepted because it uses presence-like information fields that do not prove stable predictive value across validation and recent OOS.",
        "",
        "### Strict Filter Damage",
        "",
        "| Bucket | Count | Avg Return | Sum Return | Win Rate | Entry-Reduce | Top10 Winners | Bottom10 Losers |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in strict_damage.iterrows():
        lines.append(
            f"| `{row['bucket']}` | {int(row['count'])} | {float(row['avg_return_pct']):.2f}% | "
            f"{float(row['sum_return_pct']):.2f}% | {float(row['win_rate']):.2%} | "
            f"{float(row['entry_reduce_rate']):.2%} | {float(row['top10_winner_sum_pct']):.2f}% | "
            f"{float(row['bottom10_loser_sum_pct']):.2f}% |"
        )
    lines.extend(
        [
            "",
            "### Stable Predictive Feature Test",
            "",
            "| Feature | Stable Pass | Validation Lift | Recent Lift | Validation Entry-Reduce Delta | Recent Entry-Reduce Delta |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for feature, group in feature_audit.groupby("feature", dropna=False):
        validation = group[group["split_name"].eq("validation")].iloc[0]
        recent = group[group["split_name"].eq("recent_oos")].iloc[0]
        lines.append(
            f"| `{feature}` | {int(validation['predictive_stability_pass_flag'])} | "
            f"{float(validation['avg_return_lift_pct_point']):.2f} | {float(recent['avg_return_lift_pct_point']):.2f} | "
            f"{float(validation['entry_reduce_delta_pct_point']):.2f} | {float(recent['entry_reduce_delta_pct_point']):.2f} |"
        )
    lines.extend(
        [
            "",
            "### Missed Winners",
            "",
            "| Symbol | Split | Return | Lifecycle |",
            "|---|---|---:|---|",
        ]
    )
    for _, row in missed_winners.head(10).iterrows():
        lines.append(f"| `{row['symbol']}` | `{row['split_name']}` | {float(row['net_return_pct']):.2f}% | `{row['lifecycle_id']}` |")
    lines.extend(
        [
            "",
            "### Retained Losers",
            "",
            "| Symbol | Split | Return | Lifecycle |",
            "|---|---|---:|---|",
        ]
    )
    for _, row in retained_losers.head(10).iterrows():
        lines.append(f"| `{row['symbol']}` | `{row['split_name']}` | {float(row['net_return_pct']):.2f}% | `{row['lifecycle_id']}` |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- More information did not mean better prediction.",
            "- The strict filter threw away a better bucket and kept enough losers to underperform Task617.",
            "- Information must be connected to a stock-specific expected price move before it can affect entries.",
            "",
            "## Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task_634_feature_predictive_value_audit.csv`",
            "- `task_634_strict_filter_damage_audit.csv`",
            "- `task_634_missed_winners.csv`",
            "- `task_634_retained_losers.csv`",
            "- `task_634_pass_fail_matrix.csv`",
            "- `task_634_decision.csv`",
            "- `artifact_manifest.csv`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task634_information_predictive_value_audit(out_dir=args.out_dir)
    decision = artifacts["task_634_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"stable_features={int(decision['stable_predictive_feature_count'])} "
        f"kept_avg={float(decision['strict_kept_avg_return_pct']):.2f}% "
        f"missed_avg={float(decision['missed_by_strict_avg_return_pct']):.2f}%"
    )


if __name__ == "__main__":
    main()
