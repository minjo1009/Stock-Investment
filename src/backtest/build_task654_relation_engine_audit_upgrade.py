from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD, load_qqq_history
from src.backtest.build_task639_oos_first_rule_lock_refinement import run_account


TASK_ID = "Task654"
REPORT_DIR = Path("docs/reports/task_654_relation_engine_audit_upgrade")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")
MACRO_PANEL = Path("docs/reports/task_649_macro_context_state_engine/task_649_macro_augmented_context_panel.csv")
STATE_PANEL = Path("docs/reports/task_651_relation_state_machine/task_651_gate_state_panel.csv")
TASK651_ACCOUNT = Path("docs/reports/task_651_relation_state_machine/task_651_account_comparison.csv")
TASK652_CANDIDATE_GRID = Path("docs/reports/task_652_relation_overlay_stability/task_652_candidate_account_grid.csv")
TASK652_SPLIT_GRID = Path("docs/reports/task_652_relation_overlay_stability/task_652_split_account_grid.csv")
TASK652_TAG_DIAGNOSTICS = Path("docs/reports/task_652_relation_overlay_stability/task_652_tag_diagnostics.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
QQQ_PATH = Path("data/raw/us_daily_breadth_top500/QQQ.csv")


def build_task654_relation_engine_audit_upgrade(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    macro_panel_path: Path = MACRO_PANEL,
    state_panel_path: Path = STATE_PANEL,
    task651_account_path: Path = TASK651_ACCOUNT,
    task652_candidate_grid_path: Path = TASK652_CANDIDATE_GRID,
    task652_split_grid_path: Path = TASK652_SPLIT_GRID,
    task652_tag_diagnostics_path: Path = TASK652_TAG_DIAGNOSTICS,
    task639_decision_path: Path = TASK639_DECISION,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    execution = load_execution_panel(execution_panel_path)
    macro = load_macro_panel(macro_panel_path)
    state = load_state_panel(state_panel_path)
    qqq = load_qqq_history(qqq_path)
    task639 = pd.read_csv(task639_decision_path).iloc[0]
    task651_account = pd.read_csv(task651_account_path)
    task652_candidates = pd.read_csv(task652_candidate_grid_path)
    task652_splits = pd.read_csv(task652_split_grid_path)
    tag_diagnostics = pd.read_csv(task652_tag_diagnostics_path)

    join_audit = build_join_contract_audit(state, macro)
    coverage = build_coverage_scope_report(execution, state, macro)
    baseline = build_baseline_preservation_audit(state, join_audit, qqq)
    taxonomy = build_taxonomy_definition_vs_performance(tag_diagnostics)
    transition = build_action_transition_matrix(state, join_audit)
    simulator = build_single_simulator_comparison(task651_account, task652_candidates, task639)
    promotion = build_promotion_eligibility_report(task652_candidates, task652_splits, task651_account, coverage, task639)
    pass_fail = build_pass_fail(coverage, join_audit, baseline, taxonomy, transition, promotion)
    decision = build_decision(pass_fail, coverage, baseline, promotion, task639)

    coverage.to_csv(out_dir / "coverage_scope_report.csv", index=False, encoding="utf-8-sig")
    join_audit.to_csv(out_dir / "join_contract_audit.csv", index=False, encoding="utf-8-sig")
    baseline.to_csv(out_dir / "baseline_preservation_audit.csv", index=False, encoding="utf-8-sig")
    taxonomy.to_csv(out_dir / "taxonomy_definition_vs_performance.csv", index=False, encoding="utf-8-sig")
    transition.to_csv(out_dir / "action_transition_matrix.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(out_dir / "promotion_eligibility_report.csv", index=False, encoding="utf-8-sig")
    simulator.to_csv(out_dir / "single_simulator_comparison.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_654_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_654_decision.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, coverage, baseline, promotion, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "coverage_scope_report": coverage,
        "join_contract_audit": join_audit,
        "baseline_preservation_audit": baseline,
        "taxonomy_definition_vs_performance": taxonomy,
        "action_transition_matrix": transition,
        "promotion_eligibility_report": promotion,
        "single_simulator_comparison": simulator,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        if column in panel.columns:
            panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    for column in ["net_return_from_entry", "positive_contract_customer_count", "content_supply_demand_flag"]:
        if column in panel.columns:
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id"]).copy()


def load_macro_panel(path: Path) -> pd.DataFrame:
    macro = pd.read_csv(path)
    keep = [
        "lifecycle_id",
        "entry_ts",
        "macro_overall_state",
        "macro_raw_source_gap_flag",
        "macro_vintage_source_gap_flag",
        "macro_release_calendar_gap_flag",
        "macro_latest_vintage_gap_flag",
    ]
    out = macro[[c for c in keep if c in macro.columns]].drop_duplicates("lifecycle_id").copy()
    for column in ["macro_raw_source_gap_flag", "macro_vintage_source_gap_flag", "macro_release_calendar_gap_flag", "macro_latest_vintage_gap_flag"]:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce").fillna(1).astype(int)
    return out


def load_state_panel(path: Path) -> pd.DataFrame:
    state = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        if column in state.columns:
            state[column] = pd.to_datetime(state[column], utc=True, errors="coerce")
    for column in [
        "net_return_from_entry",
        "positive_contract_customer_count",
        "content_supply_demand_flag",
        "content_prediction_certified_event_count",
        "source_text_certified_event_count",
        "research_only_flag",
        "macro_valid_for_promotion_flag",
    ]:
        if column in state.columns:
            state[column] = pd.to_numeric(state[column], errors="coerce")
    return state.dropna(subset=["lifecycle_id"]).copy()


def build_join_contract_audit(state: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    macro_keep = macro.rename(columns={"entry_ts": "macro_context_entry_ts"})
    out = state.merge(macro_keep, on="lifecycle_id", how="left", indicator="macro_join_indicator")
    out["macro_join_key"] = out["lifecycle_id"].astype(str)
    out["company_join_key"] = out["lifecycle_id"].astype(str)
    out["macro_join_status"] = out["macro_join_indicator"].map({"both": "exact_lifecycle_match", "left_only": "missing_macro_context"}).fillna("missing_macro_context")
    out["company_join_status"] = out.apply(company_join_status, axis=1)
    out["macro_source_gap_flag"] = out["macro_gate_state"].astype(str).eq("macro_source_gap").astype(int)
    out["company_source_gap_flag"] = out["company_gate_state"].astype(str).eq("company_source_gap").astype(int)
    out["macro_release_calendar_gap_flag"] = numeric_series(out, "macro_release_calendar_gap_flag", 1).astype(int)
    vintage = numeric_series(out, "macro_vintage_source_gap_flag", 1).astype(int)
    latest = numeric_series(out, "macro_latest_vintage_gap_flag", 1).fillna(vintage).astype(int)
    out["latest_vintage_gap_flag"] = latest
    out["asof_valid_flag"] = (
        out["macro_join_status"].eq("exact_lifecycle_match")
        & out["macro_source_gap_flag"].eq(0)
        & out["macro_release_calendar_gap_flag"].eq(0)
    ).astype(int)
    out["used_for_assignment_flag"] = (
        out["asof_valid_flag"].eq(1)
        & out["latest_vintage_gap_flag"].eq(0)
        & out["company_join_status"].eq("company_assignment_valid")
    ).astype(int)
    out["used_for_diagnostic_only_flag"] = (1 - out["used_for_assignment_flag"]).astype(int)
    keep = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "split_name",
        "entry_ts",
        "timing_mode",
        "exit_mode",
        "macro_join_key",
        "company_join_key",
        "macro_join_status",
        "company_join_status",
        "asof_valid_flag",
        "latest_vintage_gap_flag",
        "macro_source_gap_flag",
        "company_source_gap_flag",
        "used_for_assignment_flag",
        "used_for_diagnostic_only_flag",
        "source_gate_state",
        "macro_gate_state",
        "company_gate_state",
        "chart_gate_state",
        "relation_state",
        "action_bucket",
        "research_only_flag",
    ]
    return out[[c for c in keep if c in out.columns]].copy()


def company_join_status(row: pd.Series) -> str:
    source = str(row.get("source_gate_state", ""))
    company = str(row.get("company_gate_state", ""))
    if source == "source_valid_for_assignment" and company != "company_source_gap":
        return "company_assignment_valid"
    if source == "source_valid_for_research_only":
        return "company_research_only"
    return "missing_company_context"


def numeric_series(frame: pd.DataFrame, column: str, default: float) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce").fillna(default)


def build_coverage_scope_report(execution: pd.DataFrame, state: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    scopes = {
        "execution_all_variants": execution,
        "execution_delay1d_existing": execution[execution["timing_mode"].eq("delay1d") & execution["exit_mode"].eq("existing_exit")].copy(),
        "task639_core_delay1d_existing": task639_core(execution),
        "task651_state_panel": state,
    }
    rows = []
    macro_keys = set(macro["lifecycle_id"].astype(str))
    macro_flags = macro.set_index(macro["lifecycle_id"].astype(str))
    for scope_name, panel in scopes.items():
        ids = panel["lifecycle_id"].astype(str)
        macro_match = ids.isin(macro_keys)
        company_valid = company_valid_mask(panel)
        latest_gap = ids.map(lambda x: latest_gap_for_key(x, macro_flags))
        release_gap = ids.map(lambda x: release_gap_for_key(x, macro_flags))
        assignment_eligible = macro_match & company_valid & latest_gap.eq(0) & release_gap.eq(0)
        rows.append(
            {
                "scope": scope_name,
                "row_count": int(len(panel)),
                "lifecycle_count": int(panel["lifecycle_id"].nunique()),
                "macro_exact_match_rows": int(macro_match.sum()),
                "macro_missing_rows": int((~macro_match).sum()),
                "macro_missing_rate": rate((~macro_match).sum(), len(panel)),
                "company_assignment_valid_rows": int(company_valid.sum()),
                "company_source_gap_rows": int((~company_valid).sum()),
                "company_source_gap_rate": rate((~company_valid).sum(), len(panel)),
                "latest_vintage_gap_rows": int(latest_gap.sum()),
                "latest_vintage_gap_rate": rate(latest_gap.sum(), len(panel)),
                "release_calendar_gap_rows": int(release_gap.sum()),
                "release_calendar_gap_rate": rate(release_gap.sum(), len(panel)),
                "assignment_eligible_rows": int(assignment_eligible.sum()),
                "assignment_eligible_rate": rate(assignment_eligible.sum(), len(panel)),
            }
        )
    return pd.DataFrame(rows)


def task639_core(panel: pd.DataFrame) -> pd.DataFrame:
    mask = (
        pd.to_numeric(panel.get("positive_contract_customer_count"), errors="coerce").fillna(0).gt(0)
        | pd.to_numeric(panel.get("content_supply_demand_flag"), errors="coerce").fillna(0).eq(1)
    )
    return panel[mask & panel["timing_mode"].eq("delay1d") & panel["exit_mode"].eq("existing_exit")].copy()


def company_valid_mask(panel: pd.DataFrame) -> pd.Series:
    if "source_gate_state" in panel.columns:
        return panel["source_gate_state"].astype(str).eq("source_valid_for_assignment")
    return pd.to_numeric(panel.get("content_prediction_certified_event_count"), errors="coerce").fillna(0).gt(0)


def latest_gap_for_key(key: str, macro_flags: pd.DataFrame) -> int:
    if key not in macro_flags.index:
        return 1
    row = macro_flags.loc[key]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]
    if "macro_latest_vintage_gap_flag" in row:
        return int(row["macro_latest_vintage_gap_flag"])
    return int(row.get("macro_vintage_source_gap_flag", 1))


def release_gap_for_key(key: str, macro_flags: pd.DataFrame) -> int:
    if key not in macro_flags.index:
        return 1
    row = macro_flags.loc[key]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]
    return int(row.get("macro_release_calendar_gap_flag", 1))


def build_baseline_preservation_audit(state: pd.DataFrame, join_audit: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    core = task639_core(state)
    join_keep = join_audit[
        [
            "lifecycle_id",
            "timing_mode",
            "exit_mode",
            "used_for_assignment_flag",
            "used_for_diagnostic_only_flag",
            "macro_join_status",
            "company_join_status",
            "latest_vintage_gap_flag",
        ]
    ].drop_duplicates(["lifecycle_id", "timing_mode", "exit_mode"])
    core = core.merge(join_keep, on=["lifecycle_id", "timing_mode", "exit_mode"], how="left")
    if "holding_days" not in core.columns and {"entry_ts", "simulated_exit_ts"}.issubset(core.columns):
        core["holding_days"] = (pd.to_datetime(core["simulated_exit_ts"], utc=True) - pd.to_datetime(core["entry_ts"], utc=True)).dt.total_seconds() / 86400.0
    if "same_day_exit_flag" not in core.columns and "holding_days" in core.columns:
        core["same_day_exit_flag"] = pd.to_numeric(core["holding_days"], errors="coerce").fillna(0).lt(1.0).astype(int)
    core["baseline_transition"] = core.apply(baseline_transition, axis=1)
    rows = []
    for transition, group in core.groupby("baseline_transition", dropna=False):
        metrics = run_account(group, "equal_max5", qqq)
        ret = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
        rows.append(
            {
                "baseline_transition": transition,
                "row_count": int(len(group)),
                "accepted_trade_count": int(metrics["accepted_trade_count"]),
                "final_capital_usd": float(metrics["final_capital_usd"]),
                "max_drawdown_pct": float(metrics["max_drawdown_pct"]),
                "avg_return_pct": float(ret.mean() * 100.0) if ret.notna().any() else 0.0,
                "entry_reduce_failure_rate": float(ret.le(-0.03).mean()) if ret.notna().any() else 0.0,
                "macro_missing_or_latest_gap_rows": int(
                    group["macro_join_status"].astype(str).ne("exact_lifecycle_match").sum()
                    + pd.to_numeric(group["latest_vintage_gap_flag"], errors="coerce").fillna(1).eq(1).sum()
                ),
                "relation_can_change_execution_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("row_count", ascending=False).reset_index(drop=True)


def baseline_transition(row: pd.Series) -> str:
    action = str(row.get("action_bucket", ""))
    diagnostic_only = int(row.get("used_for_diagnostic_only_flag", 1) or 0) == 1
    if diagnostic_only:
        return "kept_task639_but_relation_diagnostic_only"
    if action in {"NORMAL_ENTRY", "FULL_ENTRY"}:
        return "kept_task639_action"
    if action == "REDUCED_SIZE":
        return "reduced_by_relation"
    if action == "DELAYED_ENTRY":
        return "delayed_by_relation"
    if action == "CONFIRMATION_REQUIRED":
        return "confirmation_required_by_relation"
    if action == "BLOCK":
        return "blocked_by_relation"
    if action == "RESEARCH_ONLY":
        return "research_only_by_relation"
    return "no_action_by_relation"


def build_taxonomy_definition_vs_performance(tag_diagnostics: pd.DataFrame) -> pd.DataFrame:
    definitions = taxonomy_definitions()
    rows = []
    for _, row in tag_diagnostics.iterrows():
        key = (str(row["tag_column"]), str(row["tag_value"]))
        definition = definitions.get(key, {})
        rows.append(
            {
                "taxonomy_column": row["tag_column"],
                "original_state_name": row["tag_value"],
                "neutral_state_name": definition.get("neutral_name", row["tag_value"]),
                "logical_definition": definition.get("logical_definition", "Observed diagnostic state from Task651."),
                "coverage_count": int(row["row_count"]),
                "assignment_permission": definition.get("assignment_permission", "diagnostic_only"),
                "promotion_permission": 0,
                "avg_return_pct": float(row["avg_return_pct"]),
                "win_rate": float(row["win_rate"]),
                "entry_reduce_failure_rate": float(row["entry_reduce_failure_rate"]),
                "evaluation_only_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values(["taxonomy_column", "coverage_count"], ascending=[True, False]).reset_index(drop=True)


def taxonomy_definitions() -> dict[tuple[str, str], dict[str, str]]:
    return {
        ("relation_state", "reinforcing"): {
            "neutral_name": "all_conditions_aligned",
            "logical_definition": "Company, chart, sector, and context appeared aligned under Task651 rules.",
            "assignment_permission": "no_size_boost_without_split_pass",
        },
        ("relation_state", "sizing_modifier"): {
            "neutral_name": "partial_alignment_or_conflict",
            "logical_definition": "Positive company signal had at least one conflict or incomplete confirmation.",
            "assignment_permission": "baseline_preservation_only",
        },
        ("relation_state", "offsetting"): {
            "neutral_name": "positive_with_conflict",
            "logical_definition": "Positive company signal had offsetting context conflict.",
            "assignment_permission": "confirmation_only_if_valid_coverage",
        },
        ("company_gate_state", "strong_company_positive"): {
            "neutral_name": "multi_evidence_company_positive",
            "logical_definition": "Contract or supply signal plus refined positive evidence and not heavily priced in.",
            "assignment_permission": "diagnostic_until_empirical_pass",
        },
        ("company_gate_state", "moderate_company_positive"): {
            "neutral_name": "single_or_moderate_company_positive",
            "logical_definition": "Contract or supply signal exists without enough extra evidence for multi-evidence status.",
            "assignment_permission": "baseline_preservation_only",
        },
        ("company_gate_state", "mixed_company_positive_conflict"): {
            "neutral_name": "positive_with_company_conflict",
            "logical_definition": "Positive catalyst exists together with negative subtype evidence.",
            "assignment_permission": "baseline_preservation_only",
        },
        ("macro_gate_state", "macro_source_gap"): {
            "neutral_name": "macro_not_available",
            "logical_definition": "Macro context was not validly attached for this row.",
            "assignment_permission": "no_assignment",
        },
    }


def build_action_transition_matrix(state: pd.DataFrame, join_audit: pd.DataFrame) -> pd.DataFrame:
    join_keep = join_audit[
        [
            "lifecycle_id",
            "timing_mode",
            "exit_mode",
            "used_for_assignment_flag",
            "used_for_diagnostic_only_flag",
            "macro_source_gap_flag",
            "company_source_gap_flag",
            "latest_vintage_gap_flag",
        ]
    ].drop_duplicates(["lifecycle_id", "timing_mode", "exit_mode"])
    panel = state.merge(join_keep, on=["lifecycle_id", "timing_mode", "exit_mode"], how="left")
    panel["task639_core_flag"] = (
        pd.to_numeric(panel.get("positive_contract_customer_count"), errors="coerce").fillna(0).gt(0)
        | pd.to_numeric(panel.get("content_supply_demand_flag"), errors="coerce").fillna(0).eq(1)
    ).astype(int)
    panel["action_authority_bucket"] = panel.apply(action_authority_bucket, axis=1)
    cols = [
        "source_gate_state",
        "macro_gate_state",
        "company_gate_state",
        "chart_gate_state",
        "relation_state",
        "action_bucket",
        "action_authority_bucket",
    ]
    grouped = panel.groupby(cols, dropna=False).agg(
        row_count=("lifecycle_id", "count"),
        task639_core_rows=("task639_core_flag", "sum"),
        assignment_valid_rows=("used_for_assignment_flag", "sum"),
        diagnostic_only_rows=("used_for_diagnostic_only_flag", "sum"),
        macro_source_gap_rows=("macro_source_gap_flag", "sum"),
        company_source_gap_rows=("company_source_gap_flag", "sum"),
        latest_vintage_gap_rows=("latest_vintage_gap_flag", "sum"),
    )
    return grouped.reset_index().sort_values("row_count", ascending=False).reset_index(drop=True)


def action_authority_bucket(row: pd.Series) -> str:
    if int(row.get("used_for_assignment_flag", 0) or 0) == 1:
        return "relation_assignment_allowed"
    if int(row.get("task639_core_flag", 0) or 0) == 1:
        return "task639_baseline_preservation_only"
    return "diagnostic_only_no_action_authority"


def build_single_simulator_comparison(task651_account: pd.DataFrame, task652_candidates: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    rows = []
    task639_all = task651_account[
        task651_account["comparison_name"].eq("task639_recomputed_positive_contract_or_supply")
        & task651_account["split_name"].eq("all")
    ].iloc[0]
    task651_all = task651_account[
        task651_account["comparison_name"].eq("task651_relation_action_strategy")
        & task651_account["split_name"].eq("all")
    ].iloc[0]
    baseline652 = task652_candidates[task652_candidates["candidate_name"].eq("baseline_task639_core")].iloc[0]
    for name, row in [
        ("task639_reference_decision", task639),
        ("task639_recomputed_task651_account", task639_all),
        ("task651_relation_action_strategy", task651_all),
        ("task652_baseline_task639_core", baseline652),
    ]:
        rows.append(
            {
                "comparison_name": name,
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "final_capital_usd": float(row.get("best_50bp_final_capital_usd", row.get("final_capital_usd", 0.0))),
                "max_drawdown_pct": float(row.get("best_50bp_max_drawdown_pct", row.get("max_drawdown_pct", 0.0))),
                "source": "existing_single_simulator_output",
            }
        )
    return pd.DataFrame(rows)


def build_promotion_eligibility_report(
    task652_candidates: pd.DataFrame,
    task652_splits: pd.DataFrame,
    task651_account: pd.DataFrame,
    coverage: pd.DataFrame,
    task639: pd.Series,
) -> pd.DataFrame:
    task639_final = float(task639["best_50bp_final_capital_usd"])
    task639_dd = float(task639["best_50bp_max_drawdown_pct"])
    assignment_rate = float(coverage[coverage["scope"].eq("task639_core_delay1d_existing")]["assignment_eligible_rate"].iloc[0])
    rows = []
    relation_all = task651_account[
        task651_account["comparison_name"].eq("task651_relation_action_strategy")
        & task651_account["split_name"].eq("all")
    ].iloc[0]
    rows.append(promotion_row("task651_relation_action_strategy", relation_all, task639_final, task639_dd, assignment_rate, 0, 0))
    for _, row in task652_candidates.iterrows():
        name = str(row["candidate_name"])
        validation = task652_splits[task652_splits["candidate_name"].eq(name) & task652_splits["split_name"].eq("validation")].iloc[0]
        recent = task652_splits[task652_splits["candidate_name"].eq(name) & task652_splits["split_name"].eq("recent_oos")].iloc[0]
        rows.append(
            promotion_row(
                name,
                row,
                task639_final,
                task639_dd,
                assignment_rate,
                int(validation["beats_qqq_flag"]),
                int(recent["beats_qqq_flag"]),
            )
        )
    return pd.DataFrame(rows).sort_values(["promotion_pass_flag", "final_capital_usd"], ascending=[False, False]).reset_index(drop=True)


def promotion_row(
    candidate_name: str,
    row: pd.Series,
    task639_final: float,
    task639_dd: float,
    assignment_rate: float,
    validation_beats_qqq: int,
    recent_beats_qqq: int,
) -> dict[str, object]:
    final = float(row["final_capital_usd"])
    dd = float(row["max_drawdown_pct"])
    beats_task639_return = int(final > task639_final)
    drawdown_better = int(dd > task639_dd)
    source_coverage_pass = int(assignment_rate >= 0.80)
    latest_vintage_pass = 0
    pass_flag = int(beats_task639_return and drawdown_better and validation_beats_qqq and recent_beats_qqq and source_coverage_pass and latest_vintage_pass)
    return {
        "candidate_name": candidate_name,
        "initial_capital_usd": INITIAL_CAPITAL_USD,
        "final_capital_usd": final,
        "max_drawdown_pct": dd,
        "beats_task639_return_flag": beats_task639_return,
        "drawdown_better_than_task639_flag": drawdown_better,
        "validation_beats_qqq_flag": validation_beats_qqq,
        "recent_oos_beats_qqq_flag": recent_beats_qqq,
        "source_coverage_pass_flag": source_coverage_pass,
        "latest_vintage_pass_flag": latest_vintage_pass,
        "promotion_pass_flag": pass_flag,
        "reason": "blocked_by_coverage_latest_vintage_or_task639_baseline",
    }


def build_pass_fail(
    coverage: pd.DataFrame,
    join_audit: pd.DataFrame,
    baseline: pd.DataFrame,
    taxonomy: pd.DataFrame,
    transition: pd.DataFrame,
    promotion: pd.DataFrame,
) -> pd.DataFrame:
    required_join_cols = {
        "macro_join_key",
        "company_join_key",
        "macro_join_status",
        "company_join_status",
        "asof_valid_flag",
        "latest_vintage_gap_flag",
        "used_for_assignment_flag",
        "used_for_diagnostic_only_flag",
    }
    task639_scope = coverage[coverage["scope"].eq("task639_core_delay1d_existing")].iloc[0]
    assignment_rate = float(task639_scope["assignment_eligible_rate"])
    relation_assignment_rows = int(join_audit["used_for_assignment_flag"].sum())
    promotion_count = int(promotion["promotion_pass_flag"].sum())
    taxonomy_bad = taxonomy[taxonomy["promotion_permission"].ne(0)]
    return pd.DataFrame(
        [
            {"gate": "coverage_scope_report_built", "pass_flag": int(len(coverage) >= 4), "observed_value": f"scopes={len(coverage)}", "required_value": "all required scopes present"},
            {"gate": "join_contract_required_columns", "pass_flag": int(required_join_cols.issubset(set(join_audit.columns))), "observed_value": f"columns={len(join_audit.columns)}", "required_value": "join audit must contain required row-level authority fields"},
            {"gate": "task639_core_assignment_coverage", "pass_flag": int(assignment_rate >= 0.80), "observed_value": f"assignment_eligible_rate={assignment_rate:.4f}", "required_value": ">=0.80 before relation can affect Task639 execution"},
            {"gate": "baseline_preservation_audit_built", "pass_flag": int(int(baseline["row_count"].sum()) > 0), "observed_value": f"rows={int(baseline['row_count'].sum())}", "required_value": "Task639 candidate treatment must be auditable"},
            {"gate": "taxonomy_permissions_split", "pass_flag": int(taxonomy_bad.empty), "observed_value": f"promotion_permission_nonzero={len(taxonomy_bad)}", "required_value": "taxonomy names cannot grant promotion"},
            {"gate": "action_transition_matrix_built", "pass_flag": int(len(transition) > 0), "observed_value": f"rows={len(transition)}", "required_value": "state-to-action transitions must be visible"},
            {"gate": "relation_assignment_rows_available", "pass_flag": int(relation_assignment_rows > 0), "observed_value": f"assignment_rows={relation_assignment_rows}", "required_value": ">0 rows with valid source coverage before relation assignment"},
            {"gate": "promotion_eligibility_report_built", "pass_flag": int(len(promotion) > 0), "observed_value": f"candidates={len(promotion)}", "required_value": "all relation candidates must be checked"},
            {"gate": "relation_promotion_candidate_found", "pass_flag": int(promotion_count > 0), "observed_value": f"promotion_candidates={promotion_count}", "required_value": "candidate must beat Task639 return and drawdown plus OOS and source gates"},
            {"gate": "trading_promotion", "pass_flag": 0, "observed_value": "relation remains diagnostic only", "required_value": "all gates above plus live source readiness"},
        ]
    )


def build_decision(
    pass_fail: pd.DataFrame,
    coverage: pd.DataFrame,
    baseline: pd.DataFrame,
    promotion: pd.DataFrame,
    task639: pd.Series,
) -> pd.DataFrame:
    gates = {str(row["gate"]): int(row["pass_flag"]) for _, row in pass_fail.iterrows()}
    task639_scope = coverage[coverage["scope"].eq("task639_core_delay1d_existing")].iloc[0]
    verdict = "AUDIT_BUILT_RELATION_ENGINE_STILL_DIAGNOSTIC_ONLY"
    if gates.get("task639_core_assignment_coverage", 0) == 0:
        verdict = "COVERAGE_JOIN_GAPS_BLOCK_RELATION_ENGINE_AUTHORITY"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": verdict,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "task639_reference_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_reference_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
                "task639_core_rows": int(task639_scope["row_count"]),
                "task639_core_assignment_eligible_rate": float(task639_scope["assignment_eligible_rate"]),
                "baseline_audited_rows": int(baseline["row_count"].sum()),
                "promotion_candidate_count": int(promotion["promotion_pass_flag"].sum()),
                "trading_promotion_pass_flag": 0,
                "next_action": "Repair macro join/vintage coverage and keep relation states diagnostic. Do not let source gaps or strong-sounding taxonomy names change Task639 execution.",
            }
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    coverage: pd.DataFrame,
    baseline: pd.DataFrame,
    promotion: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task654 Relation Engine Audit Upgrade",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Task639 reference: $1000 to ${float(d['task639_reference_final_capital_usd']):.2f}, max drawdown {float(d['task639_reference_max_drawdown_pct']):.2f} percent.",
        f"- Task639 core assignment eligible rate: {float(d['task639_core_assignment_eligible_rate']):.4f}.",
        f"- Relation promotion candidates: {int(d['promotion_candidate_count'])}.",
        "- What changed: audit infrastructure was added; no trading rule was promoted.",
        "- Next action: repair macro join/vintage coverage before relation states can change execution.",
        "",
        "## Quant Expert Report",
        "",
        "Task654 implements the Task653 firm-grade checklist as auditable artifacts. The task does not add new source categories and does not change Task639 execution.",
        "",
        "### Data Source And Source Readiness",
        "",
        table(coverage),
        "",
        "### Exact Join Keys",
        "",
        "`join_contract_audit.csv` contains row-level `macro_join_key`, `company_join_key`, `macro_join_status`, `company_join_status`, `asof_valid_flag`, `latest_vintage_gap_flag`, `used_for_assignment_flag`, and `used_for_diagnostic_only_flag`.",
        "",
        "### Leakage Audit",
        "",
        "Labels, future returns, and realized outcomes are not used in the audit assignment logic. Missing macro or latest-vintage gaps are not treated as bullish or bearish.",
        "",
        "### Split/OOS Metrics",
        "",
        "No new strategy PnL was promoted. Promotion eligibility checks continue to compare against Task639, validation QQQ, and recent OOS QQQ.",
        "",
        "### Failure Decomposition",
        "",
        table(baseline),
        "",
        "### Promotion Eligibility",
        "",
        table(promotion),
        "",
        "### Remaining Blockers",
        "",
        table(pass_fail),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "The relation engine still cannot trade by itself. It does not have enough clean row-by-row evidence yet.",
        "",
        "Plain version:",
        "",
        "- We checked whether the data is really attached.",
        "- We checked whether Task639 trades were preserved or damaged.",
        "- We checked whether strong-sounding names actually deserve trading power.",
        "- Result: not yet.",
        "",
        "Task639 stays the baseline. Relation states stay research-only until coverage and join quality are repaired.",
        "",
        "## Artifact Manifest",
        "",
        "- `coverage_scope_report.csv`",
        "- `join_contract_audit.csv`",
        "- `baseline_preservation_audit.csv`",
        "- `taxonomy_definition_vs_performance.csv`",
        "- `action_transition_matrix.csv`",
        "- `promotion_eligibility_report.csv`",
        "- `single_simulator_comparison.csv`",
        "- `task_654_pass_fail_matrix.csv`",
        "- `task_654_decision.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_654_relation_engine_audit_upgrade.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    clipped = df.head(max_rows)
    columns = [str(c) for c in clipped.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in clipped.iterrows():
        values = [markdown_cell(row.get(column, "")) for column in clipped.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def markdown_cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "/").replace("\n", " ")


def rate(count: int | float, total: int | float) -> float:
    if not total:
        return 0.0
    return float(count) / float(total)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    build_task654_relation_engine_audit_upgrade(out_dir=args.out_dir)
    print(f"[{TASK_ID}] wrote={args.out_dir}")


if __name__ == "__main__":
    main()
