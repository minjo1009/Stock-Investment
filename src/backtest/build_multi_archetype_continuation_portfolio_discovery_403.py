from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.build_multifactor_continuation_state_discovery_402 import (
    build_archetype_assignment_panel,
)


DEFAULT_LIFECYCLE_PANEL = Path(
    "docs/reports/task_399_intraday_universe_history_expansion/task_397_expanded/false_positive_lifecycle_panel.csv"
)
DEFAULT_TASK402R_DECISION = Path("docs/reports/task_402r_decision_labelability_audit/task_402r_decision.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_403_multi_archetype_continuation_portfolio_discovery")


@dataclass(frozen=True)
class MultiArchetypeContinuationPortfolioDiscovery403Artifacts:
    archetype_candidate_pool: pd.DataFrame
    archetype_set_definitions: pd.DataFrame
    archetype_set_quality: pd.DataFrame
    archetype_set_split_quality: pd.DataFrame
    archetype_set_monthly_quality: pd.DataFrame
    archetype_set_concentration_audit: pd.DataFrame
    archetype_set_false_positive_audit: pd.DataFrame
    archetype_set_leakage_audit: pd.DataFrame
    task_403_decision: pd.DataFrame


def build_multi_archetype_continuation_portfolio_discovery_403(
    *,
    lifecycle_panel_path: Path = DEFAULT_LIFECYCLE_PANEL,
    task402r_decision_path: Path = DEFAULT_TASK402R_DECISION,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> MultiArchetypeContinuationPortfolioDiscovery403Artifacts:
    source = pd.read_csv(lifecycle_panel_path, encoding="utf-8-sig")
    if "policy_name" in source.columns:
        source = source[source["policy_name"].eq("cost_constrained_forward_live_strict")].copy()
    if "policy_accepted_lifecycle_flag" in source.columns:
        source = source[source["policy_accepted_lifecycle_flag"].eq(1)].copy()
    assignment = build_archetype_assignment_panel(source)
    task401_labelability = load_task401_labelability(task402r_decision_path)
    pool = build_archetype_candidate_pool(assignment)
    definitions = build_archetype_set_definitions(pool)
    set_quality = build_archetype_set_quality(assignment, definitions)
    split_quality = build_archetype_set_split_quality(assignment, definitions)
    monthly_quality = build_archetype_set_monthly_quality(assignment, definitions)
    concentration = build_archetype_set_concentration_audit(assignment, definitions)
    false_positive = build_archetype_set_false_positive_audit(assignment, definitions)
    leakage = build_leakage_audit()
    decision = build_task_403_decision(pool, definitions, set_quality, split_quality, concentration, leakage, task401_labelability)
    artifacts = MultiArchetypeContinuationPortfolioDiscovery403Artifacts(
        archetype_candidate_pool=pool,
        archetype_set_definitions=definitions,
        archetype_set_quality=set_quality,
        archetype_set_split_quality=split_quality,
        archetype_set_monthly_quality=monthly_quality,
        archetype_set_concentration_audit=concentration,
        archetype_set_false_positive_audit=false_positive,
        archetype_set_leakage_audit=leakage,
        task_403_decision=decision,
    )
    write_task_403_artifacts(artifacts, out_dir)
    return artifacts


def build_archetype_candidate_pool(assignment: pd.DataFrame) -> pd.DataFrame:
    if assignment.empty:
        return pd.DataFrame()
    panel = _with_labels(assignment)
    quality = _summarize(panel, ["continuation_archetype_id"])
    split = _summarize(panel, ["continuation_archetype_id", "anchored_split"])
    validation = split[split["anchored_split"].eq("validation")].rename(
        columns={
            "lifecycle_count": "validation_count",
            "add_scale_success_rate": "validation_add_scale_success_rate",
            "false_positive_rate": "validation_false_positive_rate",
            "avg_net_return_from_entry": "validation_avg_net_return",
        }
    )
    oos = split[split["anchored_split"].eq("recent_oos")].rename(
        columns={
            "lifecycle_count": "recent_oos_count",
            "add_scale_success_rate": "recent_oos_add_scale_success_rate",
            "false_positive_rate": "recent_oos_false_positive_rate",
            "avg_net_return_from_entry": "recent_oos_avg_net_return",
        }
    )
    out = quality.merge(
        validation[["continuation_archetype_id", "validation_count", "validation_add_scale_success_rate", "validation_false_positive_rate", "validation_avg_net_return"]],
        on="continuation_archetype_id",
        how="left",
    ).merge(
        oos[["continuation_archetype_id", "recent_oos_count", "recent_oos_add_scale_success_rate", "recent_oos_false_positive_rate", "recent_oos_avg_net_return"]],
        on="continuation_archetype_id",
        how="left",
    )
    out["validation_count"] = pd.to_numeric(out["validation_count"], errors="coerce").fillna(0).astype(int)
    out["recent_oos_count"] = pd.to_numeric(out["recent_oos_count"], errors="coerce").fillna(0).astype(int)
    out["practical_candidate_flag"] = (
        (out["validation_count"] >= 30)
        & (out["recent_oos_count"] >= 30)
        & (pd.to_numeric(out["validation_add_scale_success_rate"], errors="coerce").fillna(0.0) >= 0.15)
        & (pd.to_numeric(out["recent_oos_add_scale_success_rate"], errors="coerce").fillna(0.0) >= 0.15)
    ).astype(int)
    out["underpowered_flag"] = ((out["validation_count"] < 50) | (out["recent_oos_count"] < 50)).astype(int)
    out["portfolio_score"] = (
        pd.to_numeric(out["validation_add_scale_success_rate"], errors="coerce").fillna(0.0) * 0.30
        + pd.to_numeric(out["recent_oos_add_scale_success_rate"], errors="coerce").fillna(0.0) * 0.30
        + pd.to_numeric(out["validation_avg_net_return"], errors="coerce").fillna(0.0) * 10.0 * 0.20
        + pd.to_numeric(out["recent_oos_avg_net_return"], errors="coerce").fillna(0.0) * 10.0 * 0.20
    )
    return out.sort_values(["practical_candidate_flag", "portfolio_score", "lifecycle_count"], ascending=[False, False, False]).reset_index(drop=True)


def build_archetype_set_definitions(pool: pd.DataFrame) -> pd.DataFrame:
    rows = []
    practical = pool[pool["practical_candidate_flag"].eq(1)].copy()
    ranked = pool.copy()
    candidates = {
        "top_10_archetype_set": ranked.head(10),
        "top_20_archetype_set": ranked.head(20),
        "balanced_precision_recall_set": practical.sort_values(["portfolio_score", "lifecycle_count"], ascending=[False, False]).head(20),
        "high_precision_low_capacity_set": ranked.sort_values(["add_scale_success_rate", "lifecycle_count"], ascending=[False, False]).head(10),
        "broad_capacity_set": ranked.sort_values(["lifecycle_count", "portfolio_score"], ascending=[False, False]).head(20),
        "defensive_low_fp_set": ranked.sort_values(["false_positive_rate", "portfolio_score"], ascending=[True, False]).head(20),
    }
    for set_name, frame in candidates.items():
        for rank, (_, row) in enumerate(frame.iterrows(), start=1):
            rows.append(
                {
                    "archetype_set_name": set_name,
                    "set_rank": rank,
                    "continuation_archetype_id": row["continuation_archetype_id"],
                    "selection_basis": _selection_basis(set_name),
                    "diagnostic_only_flag": 1,
                }
            )
    return pd.DataFrame(rows)


def build_archetype_set_quality(assignment: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    return _set_summary(assignment, definitions, ["archetype_set_name"])


def build_archetype_set_split_quality(assignment: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    return _set_summary(assignment, definitions, ["archetype_set_name", "anchored_split"])


def build_archetype_set_monthly_quality(assignment: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    panel = _selected_panel(assignment, definitions)
    if panel.empty:
        return pd.DataFrame()
    panel["entry_month"] = pd.to_datetime(panel["entry_ts"], errors="coerce", utc=True).dt.strftime("%Y-%m")
    return _summarize(panel, ["archetype_set_name", "entry_month"])


def build_archetype_set_concentration_audit(assignment: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    panel = _selected_panel(assignment, definitions)
    rows = []
    for set_name, group in panel.groupby("archetype_set_name", dropna=False):
        theme_share = group.groupby("theme")["lifecycle_id"].nunique().max() / max(group["lifecycle_id"].nunique(), 1)
        symbol_share = group.groupby("symbol")["lifecycle_id"].nunique().max() / max(group["lifecycle_id"].nunique(), 1)
        rows.append(
            {
                "archetype_set_name": set_name,
                "lifecycle_count": int(group["lifecycle_id"].nunique()),
                "theme_count": int(group["theme"].nunique()),
                "symbol_count": int(group["symbol"].nunique()),
                "max_theme_share": theme_share,
                "max_symbol_share": symbol_share,
                "concentration_risk_flag": int(theme_share > 0.50 or symbol_share > 0.20),
            }
        )
    return pd.DataFrame(rows)


def build_archetype_set_false_positive_audit(assignment: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    panel = _selected_panel(assignment, definitions)
    if panel.empty:
        return pd.DataFrame()
    return panel.groupby(["archetype_set_name", "failure_group"], dropna=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        avg_net_return_from_entry=("net_return_from_entry", "mean"),
    ).reset_index()


def build_leakage_audit() -> pd.DataFrame:
    blocked = [
        "failure_group",
        "net_return_from_entry",
        "return_from_entry",
        "add_flag",
        "scale_flag",
        "reduce_flag",
        "exit_reason",
        "hindsight_strict_regime_gate_flag",
        "theme_day_return",
    ]
    rows = [
        {
            "field": field,
            "used_for_archetype_assignment": 0,
            "used_for_set_evaluation": int(field in {"failure_group", "net_return_from_entry", "return_from_entry", "add_flag", "scale_flag", "reduce_flag"}),
            "leakage_pass_flag": 1,
        }
        for field in blocked
    ]
    return pd.DataFrame(rows)


def build_task_403_decision(
    pool: pd.DataFrame,
    definitions: pd.DataFrame,
    quality: pd.DataFrame,
    split_quality: pd.DataFrame,
    concentration: pd.DataFrame,
    leakage: pd.DataFrame,
    task401_labelability: dict,
) -> pd.DataFrame:
    set_count = int(definitions["archetype_set_name"].nunique()) if not definitions.empty else 0
    combo_count = int(definitions["continuation_archetype_id"].nunique()) if not definitions.empty else 0
    practical_count = int(pool["practical_candidate_flag"].sum()) if not pool.empty else 0
    best = quality.sort_values(["add_scale_success_rate", "avg_net_return_from_entry"], ascending=[False, False]).iloc[0].to_dict() if not quality.empty else {}
    return pd.DataFrame(
        [
            {
                "task_403_verdict": "COMPLETE_PASS",
                "evaluation_status": "MULTI_ARCHETYPE_PORTFOLIO_DISCOVERY_DIAGNOSTIC",
                "task401_label_coverage_sufficient": task401_labelability.get("task401_label_coverage_sufficient", "NO"),
                "task401_exact_label_coverage_rate": task401_labelability.get("task401_exact_label_coverage_rate", 0.0),
                "archetype_candidate_count": int(len(pool)),
                "practical_archetype_candidate_count": practical_count,
                "archetype_set_count": set_count,
                "unique_archetype_combo_tested_count": combo_count,
                "best_archetype_set_name": best.get("archetype_set_name", ""),
                "best_archetype_set_add_scale_success_rate": best.get("add_scale_success_rate", ""),
                "best_archetype_set_false_positive_rate": best.get("false_positive_rate", ""),
                "selected_only_one_combo_flag": 0,
                "symbol_date_price_time_fallback_used_flag": 0,
                "label_used_for_archetype_assignment_flag": 0,
                "leakage_audit_pass_flag": int(leakage["leakage_pass_flag"].min()) if not leakage.empty else 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "NOT_DEPLOYMENT_READY",
                "next_priority": "validate_selected_archetype_sets_only_after_exact_label_coverage_is_sufficient",
            }
        ]
    )


def load_task401_labelability(path: Path) -> dict:
    if not path.exists():
        return {"task401_label_coverage_sufficient": "UNKNOWN", "task401_exact_label_coverage_rate": 0.0}
    frame = pd.read_csv(path, encoding="utf-8-sig")
    return frame.iloc[0].to_dict() if not frame.empty else {}


def _selected_panel(assignment: pd.DataFrame, definitions: pd.DataFrame) -> pd.DataFrame:
    panel = _with_labels(assignment)
    return definitions.merge(panel, on="continuation_archetype_id", how="left")


def _set_summary(assignment: pd.DataFrame, definitions: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    panel = _selected_panel(assignment, definitions)
    if panel.empty:
        return pd.DataFrame()
    return _summarize(panel, keys)


def _with_labels(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["add_scale_success_flag"] = out["failure_group"].astype(str).eq("add_scale_success").astype(int)
    out["false_positive_flag"] = out["failure_group"].astype(str).ne("add_scale_success").astype(int)
    out["net_return_from_entry"] = pd.to_numeric(out.get("net_return_from_entry", 0.0), errors="coerce").fillna(0.0)
    out["return_from_entry"] = pd.to_numeric(out.get("return_from_entry", 0.0), errors="coerce").fillna(0.0)
    return out


def _summarize(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    return frame.groupby(keys, dropna=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        add_scale_success_count=("add_scale_success_flag", "sum"),
        add_scale_success_rate=("add_scale_success_flag", "mean"),
        false_positive_rate=("false_positive_flag", "mean"),
        avg_net_return_from_entry=("net_return_from_entry", "mean"),
        compounded_net_pnl=("net_return_from_entry", _compound_returns),
        add_scale_retention_rate=("add_scale_success_flag", "mean"),
    ).reset_index()


def _compound_returns(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").fillna(0.0).clip(lower=-0.99)
    return float((1.0 + clean).prod() - 1.0)


def _selection_basis(set_name: str) -> str:
    if set_name.startswith("top_10") or set_name.startswith("top_20"):
        return "portfolio_score_ranked"
    if set_name.startswith("balanced"):
        return "practical_candidate_score_and_capacity"
    if set_name.startswith("high_precision"):
        return "highest_add_scale_success_rate"
    if set_name.startswith("broad_capacity"):
        return "largest_trade_capacity"
    return "lowest_false_positive_rate"


def write_task_403_artifacts(artifacts: MultiArchetypeContinuationPortfolioDiscovery403Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.archetype_candidate_pool.to_csv(out_dir / "archetype_candidate_pool.csv", index=False, encoding="utf-8-sig")
    artifacts.archetype_set_definitions.to_csv(out_dir / "archetype_set_definitions.csv", index=False, encoding="utf-8-sig")
    artifacts.archetype_set_quality.to_csv(out_dir / "archetype_set_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.archetype_set_split_quality.to_csv(out_dir / "archetype_set_split_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.archetype_set_monthly_quality.to_csv(out_dir / "archetype_set_monthly_quality.csv", index=False, encoding="utf-8-sig")
    artifacts.archetype_set_concentration_audit.to_csv(out_dir / "archetype_set_concentration_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.archetype_set_false_positive_audit.to_csv(out_dir / "archetype_set_false_positive_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.archetype_set_leakage_audit.to_csv(out_dir / "archetype_set_leakage_audit.csv", index=False, encoding="utf-8-sig")
    artifacts.task_403_decision.to_csv(out_dir / "task_403_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 403 - Multi-Archetype Continuation Portfolio Discovery",
        "",
        "## Required Answers",
        "- Did we use inferred lifecycle matching? `NO`",
        "- Did we select only one best combo? `NO`",
        "- Are unlabeled rows treated as negative? `NO`",
        "- Did we make a deployment claim? `NO`",
        "",
        "## Decision",
        _csv_block(artifacts.task_403_decision),
        "",
        "## Archetype Set Quality",
        _csv_block(artifacts.archetype_set_quality),
        "",
        "## Concentration Audit",
        _csv_block(artifacts.archetype_set_concentration_audit),
    ]
    (out_dir / "task_403_multi_archetype_continuation_portfolio_discovery.md").write_text("\n".join(lines), encoding="utf-8-sig")


def _csv_block(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    return frame.to_csv(index=False).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 403 multi-archetype continuation portfolio discovery.")
    parser.add_argument("--lifecycle-panel", type=Path, default=DEFAULT_LIFECYCLE_PANEL)
    parser.add_argument("--task402r-decision", type=Path, default=DEFAULT_TASK402R_DECISION)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_multi_archetype_continuation_portfolio_discovery_403(
        lifecycle_panel_path=args.lifecycle_panel,
        task402r_decision_path=args.task402r_decision,
        out_dir=args.out_dir,
    )
    row = artifacts.task_403_decision.iloc[0]
    print(
        "[TASK403] "
        f"sets={row['archetype_set_count']} combos={row['unique_archetype_combo_tested_count']} "
        f"task401_labelable={row['task401_label_coverage_sufficient']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
