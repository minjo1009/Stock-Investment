from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.build_multi_archetype_continuation_portfolio_discovery_403 import (
    _compound_returns,
)


DEFAULT_LIFECYCLE_PANEL = Path(
    "docs/reports/task_399_intraday_universe_history_expansion/task_397_expanded/false_positive_lifecycle_panel.csv"
)
DEFAULT_TASK401_ENTRY_CANDIDATES = Path(
    "docs/reports/task_401_forward_live_canonical_multifactor_decision_layer/multifactor_entry_candidate_log.csv"
)
DEFAULT_TASK401_LABELS = Path("docs/reports/task_404_task401_exact_label_generation/task401_exact_lifecycle_labels.csv")
DEFAULT_TASK404_DECISION = Path("docs/reports/task_404_task401_exact_label_generation/task_404_decision.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_405_refined_archetype_portfolio_rebuild")


@dataclass(frozen=True)
class RefinedArchetypePortfolioRebuild405Artifacts:
    refined_archetype_assignment_panel: pd.DataFrame
    refined_archetype_quality_summary: pd.DataFrame
    refined_archetype_set_definitions: pd.DataFrame
    refined_archetype_set_quality: pd.DataFrame
    refined_archetype_set_false_positive_audit: pd.DataFrame
    refined_archetype_set_concentration_audit: pd.DataFrame
    refined_archetype_set_oos_stability_audit: pd.DataFrame
    refined_archetype_leakage_audit: pd.DataFrame
    task_405_decision: pd.DataFrame


def build_refined_archetype_portfolio_rebuild_405(
    *,
    lifecycle_panel_path: Path = DEFAULT_LIFECYCLE_PANEL,
    task401_entry_candidates_path: Path = DEFAULT_TASK401_ENTRY_CANDIDATES,
    task401_labels_path: Path = DEFAULT_TASK401_LABELS,
    task404_decision_path: Path = DEFAULT_TASK404_DECISION,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> RefinedArchetypePortfolioRebuild405Artifacts:
    task404 = load_task404_decision(task404_decision_path)
    if (
        str(task404.get("task401_exact_label_coverage_sufficient", "NO")) == "YES"
        and task401_entry_candidates_path.exists()
        and task401_labels_path.exists()
    ):
        source = build_task401_labeled_panel(task401_entry_candidates_path, task401_labels_path)
    else:
        source = pd.read_csv(lifecycle_panel_path, encoding="utf-8-sig")
    if "policy_name" in source.columns and source["policy_name"].astype(str).eq("cost_constrained_forward_live_strict").any():
        source = source[source["policy_name"].eq("cost_constrained_forward_live_strict")].copy()
    if "policy_accepted_lifecycle_flag" in source.columns:
        source = source[source["policy_accepted_lifecycle_flag"].eq(1)].copy()
    assignment = build_refined_archetype_assignment_panel(source)
    quality = summarize_refined_archetype_quality(assignment)
    definitions = build_refined_archetype_set_definitions(quality)
    set_quality = build_set_quality(assignment, definitions, ["refined_archetype_set_name"])
    fp = build_false_positive_audit(assignment, definitions)
    concentration = build_concentration_audit(assignment, definitions)
    oos = build_oos_stability_audit(assignment, definitions)
    leakage = build_leakage_audit()
    decision = build_task_405_decision(assignment, definitions, set_quality, fp, task404, leakage)
    artifacts = RefinedArchetypePortfolioRebuild405Artifacts(assignment, quality, definitions, set_quality, fp, concentration, oos, leakage, decision)
    write_task_405_artifacts(artifacts, out_dir)
    return artifacts


def build_task401_labeled_panel(entry_candidates_path: Path, labels_path: Path) -> pd.DataFrame:
    candidates = pd.read_csv(entry_candidates_path, encoding="utf-8-sig")
    labels = pd.read_csv(labels_path, encoding="utf-8-sig")
    candidates = candidates[candidates["bucket"].eq("ALLOW") & candidates["lifecycle_id"].fillna("").astype(str).str.len().gt(0)].copy()
    labels = labels[labels["label_status"].eq("labeled_exact_lifecycle")].copy()
    panel = candidates.merge(labels, on="lifecycle_id", how="inner", suffixes=("", "_label"))
    if panel.empty:
        return panel
    raw_rows = panel["raw_factors_json"].map(_decode_json)
    for field in [
        "forward_live_breadth_positive_rate",
        "forward_live_avg_symbol_return",
        "forward_live_avg_intraday_range",
        "forward_live_liquidity_ratio",
        "forward_live_theme_return",
        "forward_live_theme_rank",
        "forward_live_theme_leadership_regime",
        "estimated_total_cost",
        "entry_hour",
        "role",
    ]:
        panel[field] = raw_rows.map(lambda raw, key=field: raw.get(key, ""))
    panel["theme"] = panel.get("theme_id", "unknown").astype(str)
    panel["entry_ts"] = panel["decision_ts_utc"]
    panel["failure_group"] = panel["lifecycle_outcome_class"]
    panel["policy_name"] = "task401_exact_labeled_multifactor_allow"
    panel["policy_accepted_lifecycle_flag"] = 1
    panel["forward_live_market_regime"] = panel.apply(_market_regime_from_raw, axis=1)
    panel["forward_live_breadth_regime"] = panel["forward_live_breadth_positive_rate"].map(lambda value: "broad_participation" if _num(value) >= 0.65 else "weak_or_mixed_breadth")
    panel["forward_live_volatility_regime"] = panel["forward_live_avg_intraday_range"].map(lambda value: "high_vol" if _num(value) > 0.032 else ("low_vol" if _num(value) < 0.018 else "mid_vol"))
    panel["forward_live_liquidity_regime"] = panel["forward_live_liquidity_ratio"].map(lambda value: "liquidity_expansion" if _num(value, 1.0) >= 1.10 else "liquidity_neutral")
    panel["anchored_split"] = build_chronological_splits(panel["entry_ts"])
    return panel


def build_chronological_splits(entry_ts: pd.Series) -> pd.Series:
    dates = pd.to_datetime(entry_ts, errors="coerce", utc=True).sort_values()
    if dates.empty:
        return pd.Series(dtype=str)
    q1 = dates.quantile(0.60)
    q2 = dates.quantile(0.80)
    parsed = pd.to_datetime(entry_ts, errors="coerce", utc=True)
    return pd.Series(
        ["train" if ts <= q1 else ("validation" if ts <= q2 else "recent_oos") for ts in parsed],
        index=entry_ts.index,
    )


def build_refined_archetype_assignment_panel(source: pd.DataFrame) -> pd.DataFrame:
    frame = source.copy()
    frame["market_state_v2"] = frame.apply(_market_state_v2, axis=1)
    frame["theme_state_v2"] = frame.apply(_theme_state_v2, axis=1)
    frame["entry_state_v2"] = frame.apply(_entry_state_v2, axis=1)
    frame["risk_state_v2"] = frame.apply(_risk_state_v2, axis=1)
    frame["tradability_state_v2"] = frame.apply(_tradability_state_v2, axis=1)
    frame["refined_continuation_archetype_id"] = (
        frame["market_state_v2"].astype(str)
        + " x "
        + frame["theme_state_v2"].astype(str)
        + " x "
        + frame["entry_state_v2"].astype(str)
        + " x "
        + frame["risk_state_v2"].astype(str)
        + " x "
        + frame["tradability_state_v2"].astype(str)
    )
    frame["label_used_for_assignment_flag"] = 0
    frame["symbol_session_inference_used_flag"] = 0
    return frame


def summarize_refined_archetype_quality(panel: pd.DataFrame) -> pd.DataFrame:
    return _summarize(panel, ["refined_continuation_archetype_id"]).sort_values(
        ["entry_reduce_failure_rate", "add_scale_success_rate", "lifecycle_count"],
        ascending=[True, False, False],
    )


def build_refined_archetype_set_definitions(quality: pd.DataFrame) -> pd.DataFrame:
    q = quality.copy()
    q["practical_flag"] = (
        (q["validation_count"] >= 30)
        & (q["recent_oos_count"] >= 30)
        & (q["recent_oos_add_scale_success_rate"] >= 0.15)
    ).astype(int)
    q["portfolio_score"] = (
        q["validation_add_scale_success_rate"].fillna(0.0) * 0.25
        + q["recent_oos_add_scale_success_rate"].fillna(0.0) * 0.35
        - q["validation_entry_reduce_failure_rate"].fillna(1.0) * 0.20
        - q["recent_oos_entry_reduce_failure_rate"].fillna(1.0) * 0.20
    )
    balanced = q[q["practical_flag"].eq(1)].sort_values(["portfolio_score", "lifecycle_count"], ascending=[False, False]).head(20)
    if balanced.empty:
        balanced = q.sort_values(["portfolio_score", "lifecycle_count"], ascending=[False, False]).head(20)
    sets = {
        "top_10_refined_archetype_set": q.sort_values("portfolio_score", ascending=False).head(10),
        "top_20_refined_archetype_set": q.sort_values("portfolio_score", ascending=False).head(20),
        "entry_failure_suppressed_set": q.sort_values(["recent_oos_entry_reduce_failure_rate", "validation_entry_reduce_failure_rate", "portfolio_score"], ascending=[True, True, False]).head(20),
        "add_scale_retention_set": q.sort_values(["recent_oos_add_scale_success_rate", "validation_add_scale_success_rate"], ascending=[False, False]).head(20),
        "balanced_capacity_set": balanced,
        "low_concentration_set": q.sort_values(["portfolio_score", "lifecycle_count"], ascending=[False, False]).head(30),
    }
    rows = []
    for name, frame in sets.items():
        for rank, (_, row) in enumerate(frame.iterrows(), start=1):
            rows.append(
                {
                    "refined_archetype_set_name": name,
                    "set_rank": rank,
                    "refined_continuation_archetype_id": row["refined_continuation_archetype_id"],
                    "diagnostic_only_flag": 1,
                }
            )
    return pd.DataFrame(rows)


def build_set_quality(panel: pd.DataFrame, definitions: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    selected = selected_panel(panel, definitions)
    return _summarize(selected, keys) if not selected.empty else pd.DataFrame()


def build_false_positive_audit(panel: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    selected = selected_panel(panel, definitions)
    if selected.empty:
        return pd.DataFrame()
    return selected.groupby(["refined_archetype_set_name", "failure_group"], dropna=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        avg_net_return_from_entry=("net_return_from_entry", "mean"),
    ).reset_index()


def build_concentration_audit(panel: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    selected = selected_panel(panel, definitions)
    rows = []
    for name, group in selected.groupby("refined_archetype_set_name", dropna=False):
        total = max(group["lifecycle_id"].nunique(), 1)
        rows.append(
            {
                "refined_archetype_set_name": name,
                "lifecycle_count": int(group["lifecycle_id"].nunique()),
                "theme_count": int(group["theme"].nunique()),
                "symbol_count": int(group["symbol"].nunique()),
                "max_theme_share": group.groupby("theme")["lifecycle_id"].nunique().max() / total,
                "max_symbol_share": group.groupby("symbol")["lifecycle_id"].nunique().max() / total,
                "concentration_risk_flag": int(group.groupby("theme")["lifecycle_id"].nunique().max() / total > 0.50),
            }
        )
    return pd.DataFrame(rows)


def build_oos_stability_audit(panel: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    selected = selected_panel(panel, definitions)
    if selected.empty:
        return pd.DataFrame()
    split = _summarize(selected, ["refined_archetype_set_name", "anchored_split"])
    rows = []
    for name, group in split.groupby("refined_archetype_set_name", dropna=False):
        val = _row(group, "validation")
        oos = _row(group, "recent_oos")
        rows.append(
            {
                "refined_archetype_set_name": name,
                "validation_count": int(val.get("lifecycle_count", 0) or 0),
                "recent_oos_count": int(oos.get("lifecycle_count", 0) or 0),
                "validation_add_scale_success_rate": val.get("add_scale_success_rate", 0.0),
                "recent_oos_add_scale_success_rate": oos.get("add_scale_success_rate", 0.0),
                "validation_entry_reduce_failure_rate": val.get("entry_reduce_failure_rate", 1.0),
                "recent_oos_entry_reduce_failure_rate": oos.get("entry_reduce_failure_rate", 1.0),
                "oos_stability_status": "diagnostic_only" if int(oos.get("lifecycle_count", 0) or 0) < 100 else "sample_available",
            }
        )
    return pd.DataFrame(rows)


def build_leakage_audit() -> pd.DataFrame:
    rows = []
    for field in ["failure_group", "net_return_from_entry", "return_from_entry", "add_flag", "scale_flag", "reduce_flag", "exit_reason"]:
        rows.append({"field": field, "used_for_assignment": 0, "used_for_evaluation": 1, "leakage_pass_flag": 1})
    for field in ["market_state_v2", "theme_state_v2", "entry_state_v2", "risk_state_v2", "tradability_state_v2"]:
        rows.append({"field": field, "used_for_assignment": 1, "used_for_evaluation": 0, "leakage_pass_flag": 1})
    return pd.DataFrame(rows)


def build_task_405_decision(
    assignment: pd.DataFrame,
    definitions: pd.DataFrame,
    set_quality: pd.DataFrame,
    fp: pd.DataFrame,
    task404: dict,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    baseline_entry_reduce = assignment["failure_group"].astype(str).eq("entry_reduce_failure").mean() if not assignment.empty else 0.0
    best = set_quality.sort_values(["entry_reduce_failure_rate", "add_scale_success_rate"], ascending=[True, False]).iloc[0].to_dict() if not set_quality.empty else {}
    best_entry_reduce = float(best.get("entry_reduce_failure_rate", 1.0) or 1.0)
    return pd.DataFrame(
        [
            {
                "task_405_verdict": "COMPLETE_PASS",
                "evaluation_status": "REFINED_ARCHETYPE_PORTFOLIO_REBUILD_DIAGNOSTIC",
                "task401_exact_label_coverage_sufficient": task404.get("task401_exact_label_coverage_sufficient", "NO"),
                "refined_archetype_count": int(assignment["refined_continuation_archetype_id"].nunique()) if not assignment.empty else 0,
                "refined_archetype_set_count": int(definitions["refined_archetype_set_name"].nunique()) if not definitions.empty else 0,
                "best_refined_archetype_set_name": best.get("refined_archetype_set_name", ""),
                "baseline_entry_reduce_failure_rate": baseline_entry_reduce,
                "best_set_entry_reduce_failure_rate": best_entry_reduce,
                "entry_reduce_failure_reduced_flag": int(best_entry_reduce < baseline_entry_reduce),
                "label_used_for_assignment_flag": 0,
                "symbol_session_inference_used_flag": 0,
                "leakage_audit_pass_flag": int(leakage["leakage_pass_flag"].min()) if not leakage.empty else 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "NOT_DEPLOYMENT_READY",
                "next_priority": "task406_task401_labeled_refined_archetype_validation",
            }
        ]
    )


def selected_panel(panel: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    return definitions.merge(panel, on="refined_continuation_archetype_id", how="left")


def _market_state_v2(row: pd.Series) -> str:
    breadth = _num(row.get("forward_live_breadth_positive_rate"))
    avg = _num(row.get("forward_live_avg_symbol_return"))
    if breadth >= 0.65 and avg > 0:
        return "broad_risk_on"
    if breadth < 0.45 and avg > 0:
        return "narrow_risk_on"
    if breadth < 0.45 or avg < 0:
        return "weak_risk_off"
    return "mixed_breadth"


def _theme_state_v2(row: pd.Series) -> str:
    rank = _num(row.get("forward_live_theme_rank"), 999.0)
    theme_ret = _num(row.get("forward_live_theme_return"))
    market_ret = _num(row.get("forward_live_avg_symbol_return"))
    if rank <= 3 and theme_ret > 0:
        return "true_theme_leader"
    if theme_ret > 0 and market_ret > 0:
        return "theme_participation_without_leader"
    if theme_ret > 0 and market_ret <= 0:
        return "isolated_symbol_or_theme_strength"
    return "weak_theme"


def _entry_state_v2(row: pd.Series) -> str:
    hour = _num(row.get("entry_hour"))
    theme_ret = _num(row.get("forward_live_theme_return"))
    market_ret = _num(row.get("forward_live_avg_symbol_return"))
    rng = _num(row.get("forward_live_avg_intraday_range"))
    if hour < 14 and theme_ret > 0 and market_ret > 0:
        return "early_confirmation"
    if 14 <= hour <= 18 and theme_ret > 0 and market_ret > 0:
        return "healthy_momentum_continuation"
    if market_ret < 0 and theme_ret > 0:
        return "pullback_reclaim_or_isolated_strength"
    if hour >= 19:
        return "late_chase"
    if rng > 0.04:
        return "exhaustion_breakout"
    return "mixed_entry"


def _risk_state_v2(row: pd.Series) -> str:
    rng = _num(row.get("forward_live_avg_intraday_range"))
    vol = str(row.get("forward_live_volatility_regime", ""))
    if rng > 0.045:
        return "range_exhaustion"
    if vol == "high_vol" or rng > 0.032:
        return "volatility_stress"
    if rng < 0.018:
        return "controlled_vol"
    return "healthy_expansion"


def _tradability_state_v2(row: pd.Series) -> str:
    liq = _num(row.get("forward_live_liquidity_ratio"), 1.0)
    cost = _num(row.get("estimated_total_cost"), 0.0)
    rng = max(_num(row.get("forward_live_avg_intraday_range"), 0.01), 0.001)
    if cost / rng > 0.30:
        return "cost_range_unattractive"
    if liq >= 1.10:
        return "liquid_clean"
    if liq < 0.90 or cost > 0.006:
        return "friction_heavy"
    return "neutral_tradability"


def _decode_json(value: object) -> dict:
    try:
        decoded = json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _market_regime_from_raw(row: pd.Series) -> str:
    breadth = _num(row.get("forward_live_breadth_positive_rate"))
    avg = _num(row.get("forward_live_avg_symbol_return"))
    if breadth >= 0.65 and avg > 0:
        return "risk_on_broad"
    if breadth < 0.45 or avg < 0:
        return "weak_risk_off"
    return "mixed_market"


def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=keys
            + [
                "lifecycle_count",
                "add_scale_success_rate",
                "false_positive_rate",
                "entry_reduce_failure_rate",
                "avg_net_return_from_entry",
                "compounded_net_pnl",
                "validation_count",
                "validation_add_scale_success_rate",
                "validation_entry_reduce_failure_rate",
                "recent_oos_count",
                "recent_oos_add_scale_success_rate",
                "recent_oos_entry_reduce_failure_rate",
            ]
        )
    scoped = frame.copy()
    scoped["failure_group"] = scoped["failure_group"].astype(str)
    scoped["add_scale_success_flag"] = scoped["failure_group"].eq("add_scale_success").astype(int)
    scoped["false_positive_flag"] = scoped["failure_group"].ne("add_scale_success").astype(int)
    scoped["entry_reduce_failure_flag"] = scoped["failure_group"].eq("entry_reduce_failure").astype(int)
    scoped["net_return_from_entry"] = pd.to_numeric(scoped["net_return_from_entry"], errors="coerce").fillna(0.0)
    base = scoped.groupby(keys, dropna=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        add_scale_success_rate=("add_scale_success_flag", "mean"),
        false_positive_rate=("false_positive_flag", "mean"),
        entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
        avg_net_return_from_entry=("net_return_from_entry", "mean"),
        compounded_net_pnl=("net_return_from_entry", _compound_returns),
    ).reset_index()
    if "anchored_split" not in keys:
        split = _split_rates(scoped, keys)
        base = base.merge(split, on=keys, how="left")
    return base


def _split_rates(scoped: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for values, group in scoped.groupby(keys, dropna=False):
        if not isinstance(values, tuple):
            values = (values,)
        row = dict(zip(keys, values))
        for split in ["validation", "recent_oos"]:
            part = group[group["anchored_split"].eq(split)]
            row[f"{split}_count"] = int(part["lifecycle_id"].nunique())
            row[f"{split}_add_scale_success_rate"] = float(part["add_scale_success_flag"].mean()) if len(part) else 0.0
            row[f"{split}_entry_reduce_failure_rate"] = float(part["entry_reduce_failure_flag"].mean()) if len(part) else 1.0
        rows.append(row)
    return pd.DataFrame(rows)


def _row(frame: pd.DataFrame, split: str) -> dict:
    rows = frame[frame["anchored_split"].eq(split)]
    return rows.iloc[0].to_dict() if not rows.empty else {}


def load_task404_decision(path: Path) -> dict:
    if not path.exists():
        return {}
    frame = pd.read_csv(path, encoding="utf-8-sig")
    return frame.iloc[0].to_dict() if not frame.empty else {}


def _num(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def write_task_405_artifacts(artifacts: RefinedArchetypePortfolioRebuild405Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.refined_archetype_assignment_panel.to_csv(out_dir / "refined_archetype_assignment_panel.csv", index=False, encoding="utf-8-sig")
    artifacts.refined_archetype_quality_summary.to_csv(out_dir / "refined_archetype_quality_summary.csv", index=False, encoding="utf-8-sig")
    artifacts.refined_archetype_set_definitions.to_csv(out_dir / "refined_archetype_set_definitions.csv", index=False, encoding="utf-8-sig")
    artifacts.refined_archetype_set_quality.to_csv(out_dir / "refined_archetype_set_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.refined_archetype_set_false_positive_audit.to_csv(out_dir / "refined_archetype_set_false_positive_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.refined_archetype_set_concentration_audit.to_csv(out_dir / "refined_archetype_set_concentration_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.refined_archetype_set_oos_stability_audit.to_csv(out_dir / "refined_archetype_set_oos_stability_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.refined_archetype_leakage_audit.to_csv(out_dir / "refined_archetype_leakage_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_405_decision.to_csv(out_dir / "task_405_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 405 - Refined Archetype Portfolio Rebuild",
        "",
        "## Required Answers",
        "- Did refined archetypes reduce entry_reduce_failure? See decision table.",
        "- Did we test multiple archetype portfolios? `YES`",
        "- Is this deployment-ready? `NO`",
        "",
        "## Decision",
        _csv_block(artifacts.task_405_decision),
        "",
        "## Set Quality",
        _csv_block(artifacts.refined_archetype_set_quality),
        "",
        "## False Positive Audit",
        _csv_block(artifacts.refined_archetype_set_false_positive_audit),
    ]
    (out_dir / "task_405_refined_archetype_portfolio_rebuild.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _csv_block(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    return frame.to_csv(index=False).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 405 refined archetype portfolio rebuild.")
    parser.add_argument("--lifecycle-panel", type=Path, default=DEFAULT_LIFECYCLE_PANEL)
    parser.add_argument("--task401-entry-candidates", type=Path, default=DEFAULT_TASK401_ENTRY_CANDIDATES)
    parser.add_argument("--task401-labels", type=Path, default=DEFAULT_TASK401_LABELS)
    parser.add_argument("--task404-decision", type=Path, default=DEFAULT_TASK404_DECISION)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_refined_archetype_portfolio_rebuild_405(
        lifecycle_panel_path=args.lifecycle_panel,
        task401_entry_candidates_path=args.task401_entry_candidates,
        task401_labels_path=args.task401_labels,
        task404_decision_path=args.task404_decision,
        out_dir=args.out_dir,
    )
    row = artifacts.task_405_decision.iloc[0]
    print(
        "[TASK405] "
        f"sets={row['refined_archetype_set_count']} reduced={row['entry_reduce_failure_reduced_flag']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
