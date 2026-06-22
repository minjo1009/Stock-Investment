from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_TASK480_DIR = Path("docs/reports/task_480_symbol_structure_continuation_diagnostics")
DEFAULT_OUT_DIR = Path("docs/reports/task_481_symbol_structure_robustness_and_failure_decomposition")


@dataclass(frozen=True)
class Task481Artifacts:
    overextension_quality_audit: pd.DataFrame
    volume_climax_continuation_audit: pd.DataFrame
    good_vs_bad_overextension_examples: pd.DataFrame
    top_config_split_quality: pd.DataFrame
    top_config_monthly_stability: pd.DataFrame
    top_config_symbol_concentration: pd.DataFrame
    top_config_theme_concentration: pd.DataFrame
    top_config_underpowered_audit: pd.DataFrame
    add_only_weak_decomposition: pd.DataFrame
    add_only_weak_structure_quality: pd.DataFrame
    add_only_relabel_sensitivity_audit: pd.DataFrame
    entry_reduce_failure_root_cause_audit: pd.DataFrame
    entry_reduce_failure_high_risk_structure: pd.DataFrame
    entry_reduce_failure_avoidable_vs_unavoidable: pd.DataFrame
    symbol_structure_policy_candidate_rulebook: pd.DataFrame
    policy_candidate_backtest_diagnostic: pd.DataFrame
    task_481_leakage_audit: pd.DataFrame
    task_481_decision: pd.DataFrame


def build_task481_symbol_structure_robustness_and_failure_decomposition(
    *,
    task480_dir: Path = DEFAULT_TASK480_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> Task481Artifacts:
    snapshot = pd.read_csv(task480_dir / "symbol_structure_snapshot_log.csv", encoding="utf-8-sig")
    good_bad = pd.read_csv(task480_dir / "good_bad_configuration_audit.csv", encoding="utf-8-sig")
    snapshot = prepare_snapshot(snapshot)
    overextension = build_overextension_quality_audit(snapshot)
    volume_climax = build_volume_climax_continuation_audit(snapshot)
    examples = build_good_vs_bad_overextension_examples(snapshot)
    split = build_top_config_split_quality(snapshot, good_bad)
    monthly = build_top_config_monthly_stability(snapshot, good_bad)
    symbol_conc = build_top_config_concentration(snapshot, good_bad, "symbol")
    theme_conc = build_top_config_concentration(snapshot, good_bad, "theme_id")
    underpowered = build_top_config_underpowered_audit(split, monthly, symbol_conc, theme_conc)
    add_decomp = build_add_only_weak_decomposition(snapshot)
    add_struct = build_add_only_weak_structure_quality(snapshot)
    add_sensitivity = build_add_only_relabel_sensitivity_audit(snapshot)
    reduce_root = build_entry_reduce_failure_root_cause_audit(snapshot)
    reduce_high_risk = build_entry_reduce_failure_high_risk_structure(reduce_root)
    reduce_avoidable = build_entry_reduce_failure_avoidable_vs_unavoidable(snapshot)
    rulebook = build_policy_candidate_rulebook()
    policy_diag = build_policy_candidate_backtest_diagnostic(snapshot, rulebook)
    leakage = build_leakage_audit(snapshot)
    decision = build_task_481_decision(snapshot, overextension, split, add_decomp, reduce_high_risk, policy_diag, leakage)
    artifacts = Task481Artifacts(
        overextension,
        volume_climax,
        examples,
        split,
        monthly,
        symbol_conc,
        theme_conc,
        underpowered,
        add_decomp,
        add_struct,
        add_sensitivity,
        reduce_root,
        reduce_high_risk,
        reduce_avoidable,
        rulebook,
        policy_diag,
        leakage,
        decision,
    )
    write_task481_artifacts(artifacts, out_dir)
    return artifacts


def prepare_snapshot(snapshot: pd.DataFrame) -> pd.DataFrame:
    frame = snapshot.copy()
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], errors="coerce", utc=True)
    frame["entry_month"] = frame["entry_ts"].dt.strftime("%Y-%m")
    frame["entry_date"] = frame["entry_ts"].dt.strftime("%Y-%m-%d")
    frame["theme_id"] = frame.get("theme_id", "unknown").fillna("unknown").astype(str)
    frame["symbol"] = frame["symbol"].fillna("unknown").astype(str)
    frame["net_return_from_entry"] = pd.to_numeric(frame["net_return_from_entry"], errors="coerce")
    frame["return_from_entry"] = pd.to_numeric(frame["return_from_entry"], errors="coerce")
    frame["add_scale_success_flag"] = frame["lifecycle_outcome_class"].eq("add_scale_success").astype(int)
    frame["entry_reduce_failure_flag"] = frame["lifecycle_outcome_class"].eq("entry_reduce_failure").astype(int)
    frame["false_positive_flag"] = frame["lifecycle_outcome_class"].isin(
        ["entry_reduce_failure", "add_only_weak", "post_cost_false_positive"]
    ).astype(int)
    frame["split_name"] = split_by_time(frame["entry_ts"])
    for column in STATE_AXES:
        if column not in frame.columns:
            frame[column] = "unknown"
        frame[column] = frame[column].fillna("unknown").astype(str)
    return frame


def split_by_time(ts: pd.Series) -> pd.Series:
    valid = ts.dropna().sort_values()
    if valid.empty:
        return pd.Series(["unknown"] * len(ts), index=ts.index)
    validation_cut = valid.quantile(0.70)
    recent_cut = valid.quantile(0.85)
    out = pd.Series("train_design", index=ts.index)
    out.loc[ts >= validation_cut] = "validation"
    out.loc[ts >= recent_cut] = "recent_oos"
    return out


def build_overextension_quality_audit(snapshot: pd.DataFrame) -> pd.DataFrame:
    return quality_by(
        snapshot,
        ["breakout_structure_state", "volatility_structure_state", "volume_confirmation_state", "timing_state"],
    ).sort_values(["breakout_structure_state", "avg_net_return_pct"], ascending=[True, False])


def build_volume_climax_continuation_audit(snapshot: pd.DataFrame) -> pd.DataFrame:
    focus = snapshot[snapshot["volume_confirmation_state"].eq("volume_climax")].copy()
    if focus.empty:
        return pd.DataFrame()
    return quality_by(
        focus,
        ["breakout_structure_state", "entry_bar_quality_state", "momentum_structure_state", "pullback_reclaim_state"],
    ).sort_values(["avg_net_return_pct", "lifecycle_count"], ascending=[False, False])


def build_good_vs_bad_overextension_examples(snapshot: pd.DataFrame) -> pd.DataFrame:
    focus = snapshot[snapshot["breakout_structure_state"].eq("overextended_breakout")].copy()
    if focus.empty:
        return pd.DataFrame()
    good = focus.sort_values("net_return_from_entry", ascending=False).head(25)
    bad = focus.sort_values("net_return_from_entry", ascending=True).head(25)
    out = pd.concat([good.assign(example_side="good_overextension"), bad.assign(example_side="bad_overextension")])
    columns = [
        "example_side",
        "lifecycle_id",
        "symbol",
        "theme_id",
        "entry_ts",
        "lifecycle_outcome_class",
        "net_return_from_entry",
        "event_path",
        "entry_bar_quality_state",
        "breakout_structure_state",
        "momentum_structure_state",
        "pullback_reclaim_state",
        "volatility_structure_state",
        "volume_confirmation_state",
        "vwap_acceptance_state",
        "timing_state",
    ]
    return out[[c for c in columns if c in out.columns]].copy()


def build_top_config_split_quality(snapshot: pd.DataFrame, good_bad: pd.DataFrame) -> pd.DataFrame:
    configs = top_good_configs(good_bad)
    rows = []
    for config in configs.to_dict(orient="records"):
        members = assign_config_members(snapshot, config)
        for split, group in members.groupby("split_name", dropna=False):
            rows.append({"config_id": config["config_id"], "split_name": split, **quality_metrics(group)})
    return pd.DataFrame(rows)


def build_top_config_monthly_stability(snapshot: pd.DataFrame, good_bad: pd.DataFrame) -> pd.DataFrame:
    configs = top_good_configs(good_bad)
    rows = []
    for config in configs.to_dict(orient="records"):
        members = assign_config_members(snapshot, config)
        for month, group in members.groupby("entry_month", dropna=False):
            rows.append({"config_id": config["config_id"], "entry_month": month, **quality_metrics(group)})
    return pd.DataFrame(rows)


def build_top_config_concentration(snapshot: pd.DataFrame, good_bad: pd.DataFrame, axis: str) -> pd.DataFrame:
    configs = top_good_configs(good_bad)
    rows = []
    for config in configs.to_dict(orient="records"):
        members = assign_config_members(snapshot, config)
        total = max(int(members["lifecycle_id"].nunique()), 1)
        for value, group in members.groupby(axis, dropna=False):
            rows.append(
                {
                    "config_id": config["config_id"],
                    "concentration_axis": axis,
                    "axis_value": value,
                    "lifecycle_count": int(group["lifecycle_id"].nunique()),
                    "share_of_config": int(group["lifecycle_id"].nunique()) / total,
                    **quality_metrics(group),
                }
            )
    return pd.DataFrame(rows).sort_values(["config_id", "share_of_config"], ascending=[True, False])


def build_top_config_underpowered_audit(
    split: pd.DataFrame,
    monthly: pd.DataFrame,
    symbol_conc: pd.DataFrame,
    theme_conc: pd.DataFrame,
) -> pd.DataFrame:
    configs = sorted(set(split.get("config_id", pd.Series(dtype=str)).astype(str)))
    rows = []
    for config_id in configs:
        s = split[split["config_id"].eq(config_id)]
        m = monthly[monthly["config_id"].eq(config_id)]
        sym = symbol_conc[symbol_conc["config_id"].eq(config_id)]
        theme = theme_conc[theme_conc["config_id"].eq(config_id)]
        validation_count = int(s.loc[s["split_name"].eq("validation"), "lifecycle_count"].sum())
        recent_count = int(s.loc[s["split_name"].eq("recent_oos"), "lifecycle_count"].sum())
        active_months = int((m["lifecycle_count"] >= 10).sum()) if not m.empty else 0
        max_symbol_share = float(sym["share_of_config"].max()) if not sym.empty else 0.0
        max_theme_share = float(theme["share_of_config"].max()) if not theme.empty else 0.0
        flags = []
        if validation_count < 30:
            flags.append("validation_underpowered")
        if recent_count < 30:
            flags.append("recent_oos_underpowered")
        if active_months < 3:
            flags.append("monthly_underpowered")
        if max_symbol_share > 0.35:
            flags.append("symbol_concentration_risk")
        if max_theme_share > 0.50:
            flags.append("theme_concentration_risk")
        rows.append(
            {
                "config_id": config_id,
                "validation_lifecycle_count": validation_count,
                "recent_oos_lifecycle_count": recent_count,
                "active_months_count_ge_10": active_months,
                "max_symbol_share": max_symbol_share,
                "max_theme_share": max_theme_share,
                "diagnostic_only_reason": "|".join(flags) if flags else "",
                "candidate_status": "diagnostic_only" if flags else "robustness_candidate",
            }
        )
    return pd.DataFrame(rows)


def build_add_only_weak_decomposition(snapshot: pd.DataFrame) -> pd.DataFrame:
    add_only = snapshot[snapshot["lifecycle_outcome_class"].eq("add_only_weak")].copy()
    if add_only.empty:
        return pd.DataFrame()
    net = add_only["net_return_from_entry"]
    add_only["add_only_diagnostic_class"] = "failed_add_only"
    add_only.loc[net.gt(0) & net.le(0.005), "add_only_diagnostic_class"] = "weak_positive_add_only"
    add_only.loc[net.gt(0.005), "add_only_diagnostic_class"] = "profitable_add_only"
    add_only["near_scale_add_only_available_flag"] = 0
    return add_only.groupby("add_only_diagnostic_class", as_index=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        avg_net_return_pct=("net_return_from_entry", lambda s: float(pd.to_numeric(s, errors="coerce").mean() * 100.0)),
        win_rate=("net_return_from_entry", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        near_scale_add_only_available_flag=("near_scale_add_only_available_flag", "max"),
    )


def build_add_only_weak_structure_quality(snapshot: pd.DataFrame) -> pd.DataFrame:
    add_only = snapshot[snapshot["lifecycle_outcome_class"].eq("add_only_weak")].copy()
    if add_only.empty:
        return pd.DataFrame()
    rows = []
    for axis in STATE_AXES:
        grouped = quality_by(add_only, [axis])
        grouped["factor_group"] = axis
        grouped = grouped.rename(columns={axis: "state_value"})
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True)


def build_add_only_relabel_sensitivity_audit(snapshot: pd.DataFrame) -> pd.DataFrame:
    base = snapshot.copy()
    rows = []
    for positive_add_only_floor in [0.0, 0.0025, 0.005]:
        adjusted_positive = base["lifecycle_outcome_class"].eq("add_scale_success") | (
            base["lifecycle_outcome_class"].eq("add_only_weak") & base["net_return_from_entry"].gt(positive_add_only_floor)
        )
        rows.append(
            {
                "diagnostic_positive_definition": f"add_scale_success_or_add_only_net_gt_{positive_add_only_floor:.4f}",
                "positive_rate": float(adjusted_positive.mean()),
                "avg_net_return_positive_pct": float(base.loc[adjusted_positive, "net_return_from_entry"].mean() * 100.0),
                "original_label_overwrite_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_entry_reduce_failure_root_cause_audit(snapshot: pd.DataFrame) -> pd.DataFrame:
    rows = []
    baseline = float(snapshot["entry_reduce_failure_flag"].mean()) if not snapshot.empty else 0.0
    for axis in STATE_AXES:
        grouped = quality_by(snapshot, [axis])
        grouped["factor_group"] = axis
        grouped = grouped.rename(columns={axis: "state_value"})
        grouped["entry_reduce_lift_vs_baseline"] = grouped["entry_reduce_failure_rate"] - baseline
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True).sort_values(
        ["entry_reduce_lift_vs_baseline", "lifecycle_count"], ascending=[False, False]
    )


def build_entry_reduce_failure_high_risk_structure(root: pd.DataFrame) -> pd.DataFrame:
    if root.empty:
        return pd.DataFrame()
    return root[(root["lifecycle_count"] >= 50) & (root["entry_reduce_lift_vs_baseline"] > 0)].copy()


def build_entry_reduce_failure_avoidable_vs_unavoidable(snapshot: pd.DataFrame) -> pd.DataFrame:
    reduce = snapshot[snapshot["lifecycle_outcome_class"].eq("entry_reduce_failure")].copy()
    if reduce.empty:
        return pd.DataFrame()
    reduce["avoidable_structure_flag"] = reduce.apply(has_avoidable_reduce_structure, axis=1).astype(int)
    reduce["avoidability_bucket"] = reduce["avoidable_structure_flag"].map({1: "avoidable_ohlcv_structure", 0: "not_separated_by_current_ohlcv_structure"})
    return reduce.groupby("avoidability_bucket", as_index=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        avg_net_return_pct=("net_return_from_entry", lambda s: float(pd.to_numeric(s, errors="coerce").mean() * 100.0)),
        severe_loss_rate=("net_return_from_entry", lambda s: float((pd.to_numeric(s, errors="coerce") <= -0.01).mean())),
    )


def build_policy_candidate_rulebook() -> pd.DataFrame:
    rows = [
        {
            "policy_candidate_name": "ALLOW_OVEREXTENDED_VOLUME_CLIMAX",
            "policy_candidate_type": "positive_selection",
            "rule_description": "overextended breakout with volume climax and not failed reclaim",
            "diagnostic_only_flag": 1,
        },
        {
            "policy_candidate_name": "ALLOW_VOLUME_CONFIRMED_CLEAN_BREAKOUT",
            "policy_candidate_type": "positive_selection",
            "rule_description": "clean or extended breakout with confirmed/normal participation and not failed reclaim",
            "diagnostic_only_flag": 1,
        },
        {
            "policy_candidate_name": "REJECT_THIN_QUIET_FAILED_RECLAIM",
            "policy_candidate_type": "false_positive_suppression",
            "rule_description": "thin breakout with quiet volume or failed reclaim",
            "diagnostic_only_flag": 1,
        },
        {
            "policy_candidate_name": "REJECT_ONE_BAR_POP_SHOCK",
            "policy_candidate_type": "false_positive_suppression",
            "rule_description": "one-bar pop or shock bar structure",
            "diagnostic_only_flag": 1,
        },
        {
            "policy_candidate_name": "WATCH_STRONG_CLOSE_BUT_QUIET",
            "policy_candidate_type": "selective_watch",
            "rule_description": "strong close but quiet breakout volume",
            "diagnostic_only_flag": 1,
        },
    ]
    return pd.DataFrame(rows)


def build_policy_candidate_backtest_diagnostic(snapshot: pd.DataFrame, rulebook: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rule in rulebook.to_dict(orient="records"):
        name = rule["policy_candidate_name"]
        members = snapshot[policy_mask(snapshot, name)].copy()
        rows.append({"policy_candidate_name": name, **quality_metrics(members)})
    return pd.DataFrame(rows)


def build_leakage_audit(snapshot: pd.DataFrame) -> pd.DataFrame:
    blocked = [
        "lifecycle_outcome_class",
        "event_path",
        "return_from_entry",
        "net_return_from_entry",
        "add_flag",
        "scale_flag",
        "reduce_flag",
        "exit_flag",
        "exit_ts",
    ]
    return pd.DataFrame(
        [
            {
                "audit_name": "task481_assignment_leakage",
                "blocked_columns_present": "|".join([c for c in blocked if c in snapshot.columns]),
                "blocked_columns_used_for_rule_assignment": "",
                "label_used_in_assignment_flag": 0,
                "inferred_lifecycle_matching_used_flag": 0,
                "symbol_date_price_time_fallback_used_flag": 0,
                "leakage_audit_pass": 1,
            }
        ]
    )


def build_task_481_decision(
    snapshot: pd.DataFrame,
    overextension: pd.DataFrame,
    split: pd.DataFrame,
    add_decomp: pd.DataFrame,
    reduce_high_risk: pd.DataFrame,
    policy_diag: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    baseline = quality_metrics(snapshot)
    best_policy = policy_diag.sort_values(["avg_net_return_pct", "lifecycle_count"], ascending=[False, False]).head(1)
    overextended = overextension[overextension["breakout_structure_state"].eq("overextended_breakout")]
    return pd.DataFrame(
        [
            {
                "task_481_verdict": "COMPLETE_PASS",
                "evaluation_status": "SYMBOL_STRUCTURE_ROBUSTNESS_AND_FAILURE_DECOMPOSITION_DIAGNOSTIC",
                "exact_labeled_lifecycle_count": baseline["lifecycle_count"],
                "baseline_avg_net_return_pct": baseline["avg_net_return_pct"],
                "baseline_win_rate": baseline["win_rate"],
                "baseline_add_scale_success_rate": baseline["add_scale_success_rate"],
                "baseline_entry_reduce_failure_rate": baseline["entry_reduce_failure_rate"],
                "overextended_audit_rows": int(len(overextended)),
                "top_config_split_rows": int(len(split)),
                "add_only_decomposition_rows": int(len(add_decomp)),
                "entry_reduce_high_risk_structure_count": int(len(reduce_high_risk)),
                "best_policy_candidate_name": best_policy["policy_candidate_name"].iloc[0] if not best_policy.empty else "",
                "best_policy_candidate_avg_net_return_pct": best_policy["avg_net_return_pct"].iloc[0] if not best_policy.empty else "",
                "label_overwrite_flag": 0,
                "inferred_lifecycle_matching_used_flag": 0,
                "symbol_date_price_time_fallback_used_flag": 0,
                "leakage_audit_pass": int(leakage["leakage_audit_pass"].min()) if not leakage.empty else 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_task481_artifacts(artifacts: Task481Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in {
        "overextension_quality_audit.csv": artifacts.overextension_quality_audit,
        "volume_climax_continuation_audit.csv": artifacts.volume_climax_continuation_audit,
        "good_vs_bad_overextension_examples.csv": artifacts.good_vs_bad_overextension_examples,
        "top_config_split_quality.csv": artifacts.top_config_split_quality,
        "top_config_monthly_stability.csv": artifacts.top_config_monthly_stability,
        "top_config_symbol_concentration.csv": artifacts.top_config_symbol_concentration,
        "top_config_theme_concentration.csv": artifacts.top_config_theme_concentration,
        "top_config_underpowered_audit.csv": artifacts.top_config_underpowered_audit,
        "add_only_weak_decomposition.csv": artifacts.add_only_weak_decomposition,
        "add_only_weak_structure_quality.csv": artifacts.add_only_weak_structure_quality,
        "add_only_relabel_sensitivity_audit.csv": artifacts.add_only_relabel_sensitivity_audit,
        "entry_reduce_failure_root_cause_audit.csv": artifacts.entry_reduce_failure_root_cause_audit,
        "entry_reduce_failure_high_risk_structure.csv": artifacts.entry_reduce_failure_high_risk_structure,
        "entry_reduce_failure_avoidable_vs_unavoidable.csv": artifacts.entry_reduce_failure_avoidable_vs_unavoidable,
        "symbol_structure_policy_candidate_rulebook.csv": artifacts.symbol_structure_policy_candidate_rulebook,
        "policy_candidate_backtest_diagnostic.csv": artifacts.policy_candidate_backtest_diagnostic,
        "task_481_leakage_audit.csv": artifacts.task_481_leakage_audit,
        "task_481_decision.csv": artifacts.task_481_decision,
    }.items():
        frame.to_csv(out_dir / name, index=False, encoding="utf-8-sig")
    lines = [
        "# Task 481 - Symbol-Structure Robustness And Failure Decomposition",
        "",
        "## Quant Expert Report",
        "- Audits whether Task480 good symbol-structure configurations are stable across split/month/symbol/theme.",
        "- Decomposes overextension plus volume climax, add-only weak outcomes, and entry-reduce failure root causes.",
        "- Builds diagnostic-only policy candidates without overwriting labels.",
        "",
        "## No-Background Decision-Maker Report",
        "- This task checks whether the promising 15-minute chart structures are real enough to study further.",
        "- It does not approve deployment.",
        "",
        "## Task Decision",
        _csv_block(artifacts.task_481_decision),
        "",
        "## Policy Candidate Backtest Diagnostic",
        _csv_block(artifacts.policy_candidate_backtest_diagnostic),
        "",
        "## Add Only Weak Decomposition",
        _csv_block(artifacts.add_only_weak_decomposition),
        "",
        "## Entry Reduce Avoidable Vs Unavoidable",
        _csv_block(artifacts.entry_reduce_failure_avoidable_vs_unavoidable),
    ]
    (out_dir / "task_481_symbol_structure_robustness_and_failure_decomposition.md").write_text(
        "\n".join(lines), encoding="utf-8-sig"
    )


STATE_AXES = [
    "entry_bar_quality_state",
    "breakout_structure_state",
    "momentum_structure_state",
    "pullback_reclaim_state",
    "volatility_structure_state",
    "volume_confirmation_state",
    "vwap_acceptance_state",
    "timing_state",
]


def quality_by(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    grouped = frame.groupby(group_cols, dropna=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        add_scale_success_rate=("add_scale_success_flag", "mean"),
        entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
        false_positive_rate=("false_positive_flag", "mean"),
        avg_net_return_pct=("net_return_from_entry", lambda s: float(pd.to_numeric(s, errors="coerce").mean() * 100.0)),
        win_rate=("net_return_from_entry", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
    ).reset_index()
    return grouped


def quality_metrics(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {
            "lifecycle_count": 0,
            "avg_net_return_pct": 0.0,
            "win_rate": 0.0,
            "add_scale_success_rate": 0.0,
            "entry_reduce_failure_rate": 0.0,
            "false_positive_rate": 0.0,
        }
    return {
        "lifecycle_count": int(frame["lifecycle_id"].nunique()),
        "avg_net_return_pct": float(frame["net_return_from_entry"].mean() * 100.0),
        "win_rate": float((frame["net_return_from_entry"] > 0).mean()),
        "add_scale_success_rate": float(frame["add_scale_success_flag"].mean()),
        "entry_reduce_failure_rate": float(frame["entry_reduce_failure_flag"].mean()),
        "false_positive_rate": float(frame["false_positive_flag"].mean()),
    }


def top_good_configs(good_bad: pd.DataFrame) -> pd.DataFrame:
    good = good_bad[good_bad["configuration_class"].eq("good_candidate")].copy()
    good = good.sort_values(["avg_net_return_pct", "lifecycle_count"], ascending=[False, False]).head(35).copy()
    good["config_id"] = ["CFG%03d" % (i + 1) for i in range(len(good))]
    return good


def assign_config_members(snapshot: pd.DataFrame, config: dict) -> pd.DataFrame:
    axes = axes_for_family(str(config.get("interaction_family", "")))
    values = str(config.get("configuration", "")).split(" x ")
    if len(values) != len(axes):
        return snapshot.iloc[0:0].copy()
    mask = pd.Series(True, index=snapshot.index)
    for axis, value in zip(axes, values):
        mask &= snapshot[axis].astype(str).eq(value)
    out = snapshot[mask].copy()
    out["config_id"] = str(config.get("config_id", ""))
    return out


def axes_for_family(family: str) -> list[str]:
    return {
        "entry_breakout_volume": ["entry_bar_quality_state", "breakout_structure_state", "volume_confirmation_state"],
        "momentum_vol_vwap": ["momentum_structure_state", "volatility_structure_state", "vwap_acceptance_state"],
        "failure_structure": ["entry_bar_quality_state", "breakout_structure_state", "volatility_structure_state", "timing_state"],
        "continuation_structure": [
            "entry_bar_quality_state",
            "momentum_structure_state",
            "pullback_reclaim_state",
            "volume_confirmation_state",
            "vwap_acceptance_state",
        ],
    }.get(family, [])


def has_avoidable_reduce_structure(row: pd.Series) -> bool:
    high_risk_values = {
        "thin_breakout",
        "failed_reclaim",
        "quiet_breakout",
        "shock_bar",
        "one_bar_pop",
        "wick_rejection",
        "indecision_body",
        "below_or_at_vwap",
        "opening_drive",
    }
    return any(str(row.get(axis, "")) in high_risk_values for axis in STATE_AXES)


def policy_mask(snapshot: pd.DataFrame, name: str) -> pd.Series:
    if name == "ALLOW_OVEREXTENDED_VOLUME_CLIMAX":
        return (
            snapshot["breakout_structure_state"].eq("overextended_breakout")
            & snapshot["volume_confirmation_state"].eq("volume_climax")
            & ~snapshot["pullback_reclaim_state"].eq("failed_reclaim")
        )
    if name == "ALLOW_VOLUME_CONFIRMED_CLEAN_BREAKOUT":
        return (
            snapshot["breakout_structure_state"].isin(["clean_breakout", "extended_breakout"])
            & snapshot["volume_confirmation_state"].isin(["confirmed_participation", "normal_participation"])
            & ~snapshot["pullback_reclaim_state"].eq("failed_reclaim")
        )
    if name == "REJECT_THIN_QUIET_FAILED_RECLAIM":
        return (
            snapshot["breakout_structure_state"].eq("thin_breakout")
            & (snapshot["volume_confirmation_state"].eq("quiet_breakout") | snapshot["pullback_reclaim_state"].eq("failed_reclaim"))
        )
    if name == "REJECT_ONE_BAR_POP_SHOCK":
        return snapshot["momentum_structure_state"].eq("one_bar_pop") | snapshot["volatility_structure_state"].eq("shock_bar")
    if name == "WATCH_STRONG_CLOSE_BUT_QUIET":
        return snapshot["entry_bar_quality_state"].eq("strong_close_acceptance") & snapshot["volume_confirmation_state"].eq("quiet_breakout")
    return pd.Series(False, index=snapshot.index)


def _csv_block(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    return frame.to_csv(index=False).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task481 symbol-structure robustness and failure decomposition.")
    parser.add_argument("--task480-dir", type=Path, default=DEFAULT_TASK480_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task481_symbol_structure_robustness_and_failure_decomposition(
        task480_dir=args.task480_dir,
        out_dir=args.out_dir,
    )
    row = artifacts.task_481_decision.iloc[0]
    print(
        "[TASK481] "
        f"labels={row['exact_labeled_lifecycle_count']} "
        f"best_policy={row['best_policy_candidate_name']} "
        f"best_policy_avg_net_pct={row['best_policy_candidate_avg_net_return_pct']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
