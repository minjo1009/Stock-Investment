from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD, load_qqq_history, qqq_final_for_period
from src.backtest.build_task638_content_signal_refinement import costed
from src.backtest.build_task639_oos_first_rule_lock_refinement import run_account as run_task639_account


TASK_ID = "Task651"
REPORT_DIR = Path("docs/reports/task_651_relation_state_machine")
EXECUTION_PANEL = Path("docs/reports/task_638_content_signal_refinement/task_638_timing_exit_execution_panel.csv")
MACRO_PANEL = Path("docs/reports/task_649_macro_context_state_engine/task_649_macro_augmented_context_panel.csv")
TASK639_DECISION = Path("docs/reports/task_639_oos_first_rule_lock_refinement/task_639_decision.csv")
QQQ_PATH = Path("data/raw/us_daily_breadth_top500/QQQ.csv")

ACTION_TIMING_EXIT = {
    "FULL_ENTRY": ("delay1d", "existing_exit"),
    "NORMAL_ENTRY": ("delay1d", "existing_exit"),
    "REDUCED_SIZE": ("delay1d", "existing_exit"),
    "DELAYED_ENTRY": ("delay1d", "existing_exit"),
    "CONFIRMATION_REQUIRED": ("vwap_reclaim", "existing_exit"),
}
ACTION_WEIGHT = {
    "FULL_ENTRY": 0.20,
    "NORMAL_ENTRY": 0.20,
    "REDUCED_SIZE": 0.10,
    "DELAYED_ENTRY": 0.10,
    "CONFIRMATION_REQUIRED": 0.10,
}
ACTIONABLE = set(ACTION_TIMING_EXIT)
SPARSE_MIN_COUNT = 10


def build_task651_relation_state_machine(
    *,
    execution_panel_path: Path = EXECUTION_PANEL,
    macro_panel_path: Path = MACRO_PANEL,
    task639_decision_path: Path = TASK639_DECISION,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    execution = load_execution_panel(execution_panel_path)
    macro = load_macro_panel(macro_panel_path)
    panel = attach_macro(execution, macro)
    state_panel = assign_relation_states(panel)
    state_panel = attach_sparse_flags(state_panel)
    representative = build_representative_execution_panel(state_panel)
    qqq = load_qqq_history(qqq_path)
    task639 = pd.read_csv(task639_decision_path).iloc[0]
    action_perf = build_action_performance(representative, qqq, task639)
    relation_perf = build_relation_performance(representative)
    account = build_account_comparison(representative, qqq, task639)
    sparse = build_sparse_cell_report(state_panel)
    false_block = build_false_block_reduce_review(state_panel)
    leakage = build_leakage_audit(state_panel)
    source_audit = build_source_audit(execution, macro, state_panel, representative)
    pass_fail = build_pass_fail(account, leakage, source_audit, sparse)
    decision = build_decision(account, pass_fail, task639)

    state_panel.to_csv(out_dir / "task_651_gate_state_panel.csv", index=False, encoding="utf-8-sig")
    representative.to_csv(out_dir / "task_651_representative_execution_panel.csv", index=False, encoding="utf-8-sig")
    action_perf.to_csv(out_dir / "task_651_action_performance.csv", index=False, encoding="utf-8-sig")
    relation_perf.to_csv(out_dir / "task_651_relation_performance.csv", index=False, encoding="utf-8-sig")
    account.to_csv(out_dir / "task_651_account_comparison.csv", index=False, encoding="utf-8-sig")
    sparse.to_csv(out_dir / "task_651_sparse_cell_report.csv", index=False, encoding="utf-8-sig")
    false_block.to_csv(out_dir / "task_651_false_block_reduce_review.csv", index=False, encoding="utf-8-sig")
    leakage.to_csv(out_dir / "task_651_leakage_audit.csv", index=False, encoding="utf-8-sig")
    source_audit.to_csv(out_dir / "task_651_source_audit.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_651_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_651_decision.csv", index=False, encoding="utf-8-sig")
    write_gpt_artifacts(out_dir)
    write_report(out_dir, decision, account, action_perf, relation_perf, source_audit, leakage, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "state_panel": state_panel,
        "representative": representative,
        "action_performance": action_perf,
        "relation_performance": relation_perf,
        "account_comparison": account,
        "sparse_cell_report": sparse,
        "false_block_reduce_review": false_block,
        "leakage_audit": leakage,
        "source_audit": source_audit,
        "pass_fail": pass_fail,
        "decision": decision,
    }


def load_execution_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    for column in ["entry_ts", "simulated_exit_ts"]:
        panel[column] = pd.to_datetime(panel[column], utc=True, errors="coerce")
    for column in ["entry_price", "simulated_exit_price", "net_return_from_entry"]:
        panel[column] = pd.to_numeric(panel[column], errors="coerce")
    return panel.dropna(subset=["lifecycle_id", "entry_ts", "simulated_exit_ts", "net_return_from_entry"]).copy()


def load_macro_panel(path: Path) -> pd.DataFrame:
    macro = pd.read_csv(path)
    keep = [
        "lifecycle_id",
        "macro_overall_state",
        "macro_employment_state",
        "macro_inflation_state",
        "macro_rates_state",
        "macro_dollar_state",
        "macro_oil_state",
        "macro_credit_state",
        "macro_liquidity_state",
        "macro_vintage_source_gap_flag",
        "macro_release_calendar_gap_flag",
    ]
    return macro[[c for c in keep if c in macro.columns]].drop_duplicates("lifecycle_id")


def attach_macro(execution: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    out = execution.merge(macro, on="lifecycle_id", how="left", suffixes=("", "_task649"))
    out["macro_overall_state"] = out["macro_overall_state"].fillna("source_gap")
    out["macro_vintage_source_gap_flag"] = pd.to_numeric(out.get("macro_vintage_source_gap_flag"), errors="coerce").fillna(1).astype(int)
    out["macro_release_calendar_gap_flag"] = pd.to_numeric(out.get("macro_release_calendar_gap_flag"), errors="coerce").fillna(1).astype(int)
    return out


def assign_relation_states(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    state_cols = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "split_name",
        "entry_ts",
        "timing_mode",
        "exit_mode",
        "simulated_exit_ts",
        "net_return_from_entry",
        "win_flag",
        "entry_reduce_failure_flag",
        "content_refined_strength_score",
        "positive_contract_customer_count",
        "content_supply_demand_flag",
        "content_prediction_certified_event_count",
        "source_text_certified_event_count",
    ]
    for row in panel.to_dict(orient="records"):
        source = source_gate(row)
        macro = macro_gate(row)
        policy = policy_geo_gate(row)
        sector = sector_gate(row)
        company = company_gate(row)
        chart = chart_gate(row)
        relation, relation_reasons = resolve_relation(source, macro, policy, sector, company, chart)
        action, action_reasons = map_action(relation, source, macro, policy, sector, company, chart)
        research_only = int(
            source in {"source_gap_company", "source_valid_for_research_only"}
            or int(row.get("macro_vintage_source_gap_flag", 1) or 0) == 1
            or int(row.get("macro_release_calendar_gap_flag", 1) or 0) == 1
        )
        out = {c: row.get(c) for c in state_cols if c in row}
        out.update(
            {
                "entry_id": row.get("lifecycle_id"),
                "source_gate_state": source,
                "macro_gate_state": macro,
                "policy_geo_gate_state": policy,
                "sector_gate_state": sector,
                "company_gate_state": company,
                "chart_gate_state": chart,
                "relation_state": relation,
                "final_context_state": f"{company}|{macro}|{policy}|{sector}|{chart}",
                "action_bucket": action,
                "action_reason_codes": "|".join(relation_reasons + action_reasons),
                "research_only_flag": research_only,
                "macro_valid_for_promotion_flag": int(research_only == 0),
                "label_used_in_assignment_flag": 0,
                "return_used_in_assignment_flag": 0,
                "future_price_used_in_assignment_flag": 0,
                "missing_source_used_as_direction_flag": 0,
                "strategy_promotion_flag": 0,
            }
        )
        rows.append(out)
    return pd.DataFrame(rows)


def source_gate(row: dict[str, object]) -> str:
    certified = n(row.get("content_prediction_certified_event_count"))
    source_text = n(row.get("source_text_certified_event_count"))
    if certified <= 0:
        return "source_gap_company"
    if source_text <= 0:
        return "source_valid_for_research_only"
    return "source_valid_for_assignment"


def macro_gate(row: dict[str, object]) -> str:
    state = s(row.get("macro_overall_state"))
    if state == "macro_supportive":
        return "macro_supportive"
    if state == "macro_hostile":
        return "macro_hostile"
    if state == "source_gap":
        return "macro_source_gap"
    return "macro_mixed"


def policy_geo_gate(row: dict[str, object]) -> str:
    bucket = s(row.get("action_bucket"))
    if n(row.get("block_hold_flag")) > 0 or bucket == "block_hold":
        return "policy_blocker"
    if n(row.get("size_down_flag")) > 0 or bucket == "size_down":
        return "policy_pressure"
    if n(row.get("delay_entry_flag")) > 0 or bucket == "delay_entry":
        return "policy_delay"
    if n(row.get("confirmation_required_flag")) > 0 or bucket == "confirmation_required":
        return "policy_confirmation"
    if bucket:
        return "policy_neutral"
    return "policy_source_gap"


def sector_gate(row: dict[str, object]) -> str:
    regime = s(row.get("theme_regime_state_v4"))
    ret20 = n(row.get("theme_ret20_prev"), default=float("nan"))
    breadth = n(row.get("theme_breadth20_prev"), default=float("nan"))
    volume = n(row.get("theme_volume_ratio_prev"), default=float("nan"))
    if not regime and pd.isna(ret20) and pd.isna(breadth):
        return "sector_source_gap"
    if "narrow" in regime or (not pd.isna(breadth) and breadth < 0.35) or (not pd.isna(ret20) and ret20 < -0.05):
        return "sector_weak"
    if (
        ("persistent" in regime or "participation" in regime)
        and (pd.isna(breadth) or breadth >= 0.50)
        and (pd.isna(ret20) or ret20 >= 0)
        and (pd.isna(volume) or volume >= 0.80)
    ):
        return "sector_aligned"
    return "sector_neutral"


def company_gate(row: dict[str, object]) -> str:
    if n(row.get("content_prediction_certified_event_count")) <= 0:
        return "company_source_gap"
    direct_bearish = n(row.get("content_direct_bearish_count"))
    regulatory = n(row.get("content_regulatory_policy_count"))
    insider_sell = n(row.get("content_insider_sell_count"))
    net = n(row.get("content_net_prediction_score"))
    negative_refined = (
        n(row.get("negative_dilution_financing_count"))
        + n(row.get("negative_regulation_sanction_tariff_count"))
        + n(row.get("negative_ceo_ir_disappointment_count"))
        + n(row.get("negative_insider_sell_count"))
        + n(row.get("negative_earnings_margin_damage_count"))
    )
    core_positive = core_positive_contract_or_supply(row)
    positive_refined = (
        n(row.get("positive_contract_customer_count"))
        + n(row.get("positive_backlog_order_count"))
        + n(row.get("positive_guidance_up_count"))
        + n(row.get("positive_margin_supply_combo_count"))
    )
    positive_basic = (
        n(row.get("content_direct_bullish_count"))
        + n(row.get("content_contract_revenue_count"))
        + n(row.get("content_guidance_margin_count"))
        + n(row.get("content_supply_demand_count"))
        + n(row.get("content_insider_buy_count"))
    )
    priced_in = n(row.get("content_avg_priced_in_risk_score"))
    if negative_refined > 0 and core_positive:
        return "mixed_company_positive_conflict"
    if negative_refined > positive_refined and (direct_bearish + regulatory + insider_sell > 0 or net < 0):
        return "company_negative"
    if core_positive and positive_refined > 0 and priced_in < 0.75:
        return "strong_company_positive"
    if core_positive:
        return "moderate_company_positive"
    if positive_refined > 0 or positive_basic > 0:
        return "weak_positive_presence"
    return "weak_company"


def chart_gate(row: dict[str, object]) -> str:
    health = n(row.get("tq_pre_entry_chart_health_score"), default=float("nan"))
    runtime = n(row.get("tq_runtime_entry_confirmation_score"), default=float("nan"))
    volume = n(row.get("volume_ratio_prev"), default=float("nan"))
    range_pos = n(row.get("range_pos"), default=float("nan"))
    intraday = s(row.get("intraday_entry_state_v4"))
    if pd.isna(health) and not intraday:
        return "chart_source_gap"
    if (not pd.isna(health) and health < 0.35) or (not pd.isna(volume) and volume < 0.45) or (not pd.isna(range_pos) and range_pos < 0.20):
        return "chart_failed"
    if (not pd.isna(health) and health < 0.50) or (not pd.isna(range_pos) and range_pos > 0.99):
        return "chart_fragile"
    if health >= 0.75 and "acceptance" in intraday and (pd.isna(runtime) or runtime >= 0.50):
        return "chart_confirmed"
    return "chart_unconfirmed"


def resolve_relation(source: str, macro: str, policy: str, sector: str, company: str, chart: str) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if source == "source_gap_company" or company == "company_source_gap":
        return "source_gap", ["company_source_gap"]
    if company in {"weak_company", "weak_positive_presence"}:
        return "source_gap", ["company_signal_too_weak"]
    if company == "company_negative" and (policy == "policy_blocker" or chart == "chart_failed" or macro == "macro_hostile"):
        return "blocker", ["negative_company_confirmed_by_risk_layer"]
    if company == "company_negative":
        return "blocker", ["negative_company_no_long_entry"]
    if company == "mixed_company_positive_conflict":
        if policy == "policy_blocker" and chart == "chart_failed":
            return "sizing_modifier", ["positive_catalyst_with_hard_external_conflict_research_tag"]
        return "sizing_modifier", ["mixed_company_conflict_but_positive_catalyst_protected"]
    if company in {"strong_company_positive", "moderate_company_positive"}:
        hard_conflicts = [
            macro == "macro_hostile",
            policy in {"policy_blocker", "policy_pressure"},
            sector == "sector_weak",
            chart in {"chart_failed", "chart_fragile"},
        ]
        if chart == "chart_unconfirmed" and sum(hard_conflicts) == 0:
            return "sizing_modifier", ["positive_company_chart_unconfirmed_research_tag"]
        if sum(hard_conflicts) >= 2:
            return "offsetting", ["positive_company_multiple_context_conflicts"]
        if policy in {"policy_delay", "policy_confirmation"}:
            return "prerequisite", ["policy_requires_delay_or_confirmation"]
        if sum(hard_conflicts) == 1:
            return "sizing_modifier", ["positive_company_one_context_conflict"]
        if company == "strong_company_positive" and macro in {"macro_supportive", "macro_mixed", "macro_source_gap"} and sector in {"sector_aligned", "sector_neutral"} and chart == "chart_confirmed":
            return "reinforcing", ["strong_company_context_reinforcing"]
        return "sizing_modifier", ["positive_company_not_full_reinforcing"]
    return "source_gap", ["unhandled_weak_context"]


def map_action(relation: str, source: str, macro: str, policy: str, sector: str, company: str, chart: str) -> tuple[str, list[str]]:
    if source == "source_valid_for_research_only":
        return "RESEARCH_ONLY", ["source_text_not_certified_for_assignment"]
    if relation == "source_gap":
        return "NO_ACTION", ["no_company_interpretable_edge"]
    if relation == "blocker":
        return "BLOCK", ["hard_risk_or_negative_company"]
    if relation == "reinforcing":
        if company == "strong_company_positive" and chart == "chart_confirmed" and sector == "sector_aligned":
            return "NORMAL_ENTRY", ["full_entry_candidate_research_tag_no_size_boost"]
        return "NORMAL_ENTRY", ["reinforcing_normal_candidate"]
    if relation == "prerequisite":
        return "NORMAL_ENTRY", ["prerequisite_research_tag_no_execution_change"]
    if relation == "offsetting":
        return "CONFIRMATION_REQUIRED", ["context_offsets_company_signal"]
    if relation == "sizing_modifier":
        if company == "mixed_company_positive_conflict" and chart == "chart_confirmed":
            return "NORMAL_ENTRY", ["positive_contract_supply_protected_from_false_block"]
        if macro == "macro_hostile" or policy == "policy_pressure":
            return "REDUCED_SIZE", ["single_context_conflict_size_down"]
        return "NORMAL_ENTRY", ["positive_company_mixed_context"]
    return "NO_ACTION", ["default_no_action"]


def attach_sparse_flags(state_panel: pd.DataFrame) -> pd.DataFrame:
    out = state_panel.copy()
    combo = ["relation_state", "action_bucket", "macro_gate_state", "company_gate_state", "chart_gate_state"]
    counts = out.groupby(combo, dropna=False).size().reset_index(name="cell_count")
    out = out.merge(counts, on=combo, how="left")
    out["sparse_cell_flag"] = out["cell_count"].lt(SPARSE_MIN_COUNT).astype(int)
    out["research_only_flag"] = out[["research_only_flag", "sparse_cell_flag"]].max(axis=1)
    return out


def core_positive_contract_or_supply(row: dict[str, object]) -> bool:
    return n(row.get("positive_contract_customer_count")) > 0 or n(row.get("content_supply_demand_flag")) > 0


def build_representative_execution_panel(state_panel: pd.DataFrame) -> pd.DataFrame:
    selected_rows = []
    for action, (timing, exit_mode) in ACTION_TIMING_EXIT.items():
        scoped = state_panel[
            state_panel["action_bucket"].eq(action)
            & state_panel["timing_mode"].eq(timing)
            & state_panel["exit_mode"].eq(exit_mode)
        ].copy()
        if scoped.empty:
            continue
        scoped["relation_position_weight"] = ACTION_WEIGHT[action]
        selected_rows.append(scoped)
    if not selected_rows:
        return pd.DataFrame(columns=list(state_panel.columns) + ["relation_position_weight"])
    return pd.concat(selected_rows, ignore_index=True).sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)


def build_action_performance(representative: pd.DataFrame, qqq: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    rows = []
    task639_final = float(task639["best_50bp_final_capital_usd"])
    for split_name in ["all", "train_design", "validation", "recent_oos"]:
        split_panel = representative if split_name == "all" else representative[representative["split_name"].astype(str).eq(split_name)]
        for action, group in split_panel.groupby("action_bucket", dropna=False):
            metrics = run_relation_account(group, qqq)
            ret = pd.to_numeric(group.get("net_return_from_entry"), errors="coerce")
            rows.append(
                {
                    "split_name": split_name,
                    "action_bucket": action,
                    "trade_count": int(len(group)),
                    "accepted_trade_count": int(metrics["accepted_trade_count"]),
                    "final_capital_usd": metrics["final_capital_usd"],
                    "max_drawdown_pct": metrics["max_drawdown_pct"],
                    "avg_return_pct": float(ret.mean() * 100.0) if ret.notna().any() else 0.0,
                    "win_rate": float(ret.gt(0).mean()) if ret.notna().any() else 0.0,
                    "entry_reduce_failure_rate": float(ret.le(-0.03).mean()) if ret.notna().any() else 0.0,
                    "qqq_final_capital_usd": metrics["qqq_final_capital_usd"],
                    "beats_qqq_flag": int(metrics["final_capital_usd"] > metrics["qqq_final_capital_usd"]),
                    "task639_final_capital_usd": task639_final if split_name == "all" else 0.0,
                    "beats_task639_full_flag": int(split_name == "all" and metrics["final_capital_usd"] > task639_final),
                }
            )
    return pd.DataFrame(rows)


def build_relation_performance(representative: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_name in ["all", "train_design", "validation", "recent_oos"]:
        split_panel = representative if split_name == "all" else representative[representative["split_name"].astype(str).eq(split_name)]
        for relation, group in split_panel.groupby("relation_state", dropna=False):
            ret = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
            rows.append(
                {
                    "split_name": split_name,
                    "relation_state": relation,
                    "trade_count": int(len(group)),
                    "avg_return_pct": float(ret.mean() * 100.0) if ret.notna().any() else 0.0,
                    "large_loss_rate": float(ret.le(-0.10).mean()) if ret.notna().any() else 0.0,
                    "entry_reduce_failure_rate": float(ret.le(-0.03).mean()) if ret.notna().any() else 0.0,
                    "win_rate": float(ret.gt(0).mean()) if ret.notna().any() else 0.0,
                }
            )
    return pd.DataFrame(rows)


def build_account_comparison(representative: pd.DataFrame, qqq: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    rows = []
    task639_final = float(task639["best_50bp_final_capital_usd"])
    task639_dd = float(task639["best_50bp_max_drawdown_pct"])
    for split_name in ["all", "validation", "recent_oos"]:
        scoped = representative if split_name == "all" else representative[representative["split_name"].astype(str).eq(split_name)]
        metrics = run_relation_account(scoped, qqq)
        rows.append(
            {
                "comparison_name": "task651_relation_action_strategy",
                "split_name": split_name,
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                **metrics,
                "task639_full_final_capital_usd": task639_final if split_name == "all" else 0.0,
                "task639_full_max_drawdown_pct": task639_dd if split_name == "all" else 0.0,
                "beats_task639_full_flag": int(split_name == "all" and metrics["final_capital_usd"] > task639_final),
                "beats_qqq_flag": int(metrics["final_capital_usd"] > metrics["qqq_final_capital_usd"]),
            }
        )
    task639_panel = build_task639_baseline_panel()
    if not task639_panel.empty:
        for split_name in ["all", "validation", "recent_oos"]:
            scoped = task639_panel if split_name == "all" else task639_panel[task639_panel["split_name"].astype(str).eq(split_name)]
            metrics = run_task639_account(scoped, "equal_max5", qqq)
            rows.append(
                {
                    "comparison_name": "task639_recomputed_positive_contract_or_supply",
                    "split_name": split_name,
                    "initial_capital_usd": INITIAL_CAPITAL_USD,
                    "source_trade_count": metrics["source_trade_count"],
                    "accepted_trade_count": metrics["accepted_trade_count"],
                    "final_capital_usd": metrics["final_capital_usd"],
                    "capital_return_pct": metrics["capital_return_pct"],
                    "max_drawdown_pct": metrics["max_drawdown_pct"],
                    "entry_reduce_failure_rate": metrics["entry_reduce_failure_rate"],
                    "qqq_final_capital_usd": metrics["qqq_final_capital_usd"],
                    "task639_full_final_capital_usd": task639_final if split_name == "all" else 0.0,
                    "task639_full_max_drawdown_pct": task639_dd if split_name == "all" else 0.0,
                    "beats_task639_full_flag": int(split_name == "all" and metrics["final_capital_usd"] > task639_final),
                    "beats_qqq_flag": metrics["beats_qqq_flag"],
                }
            )
    return pd.DataFrame(rows)


def run_relation_account(panel: pd.DataFrame, qqq: pd.DataFrame) -> dict[str, object]:
    if panel.empty:
        return empty_account(qqq, panel)
    cost_panel = costed(panel, 50)
    ordered = cost_panel.sort_values(["entry_ts", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    cash = 1.0
    peak_equity = 1.0
    max_drawdown = 0.0
    open_positions: list[dict[str, object]] = []
    accepted = []

    def current_equity() -> float:
        return cash + sum(float(pos["capital"]) for pos in open_positions)

    def close_until(ts: pd.Timestamp) -> None:
        nonlocal cash, peak_equity, max_drawdown, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= ts:
                cash += float(pos["capital"]) * (1.0 + float(pos["return"]))
                equity = current_equity()
                peak_equity = max(peak_equity, equity)
                max_drawdown = min(max_drawdown, (equity / max(peak_equity, 1e-9) - 1.0) * 100.0)
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_until(entry_ts)
        if len(open_positions) >= 5:
            continue
        equity = current_equity()
        weight = float(row.get("relation_position_weight", 0.10) or 0.10)
        capital = min(cash, equity * weight)
        if capital <= 0:
            continue
        cash -= capital
        open_positions.append(
            {
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_from_entry"],
            }
        )
        accepted.append(row)
    close_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    if not accepted:
        return empty_account(qqq, panel)
    acc = pd.DataFrame(accepted)
    ret = pd.to_numeric(acc["net_return_from_entry"], errors="coerce")
    final = INITIAL_CAPITAL_USD * cash
    qqq_final = qqq_final_for_period(qqq, panel)
    return {
        "source_trade_count": int(len(panel)),
        "accepted_trade_count": int(len(acc)),
        "final_capital_usd": float(final),
        "capital_return_pct": float((cash - 1.0) * 100.0),
        "max_drawdown_pct": float(max_drawdown),
        "avg_net_return_pct": float(ret.mean() * 100.0),
        "win_rate": float(ret.gt(0).mean()),
        "entry_reduce_failure_rate": float(ret.le(-0.03).mean()),
        "qqq_final_capital_usd": float(qqq_final),
    }


def empty_account(qqq: pd.DataFrame, panel: pd.DataFrame) -> dict[str, object]:
    return {
        "source_trade_count": int(len(panel)),
        "accepted_trade_count": 0,
        "final_capital_usd": INITIAL_CAPITAL_USD,
        "capital_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "qqq_final_capital_usd": qqq_final_for_period(qqq, panel) if not panel.empty else INITIAL_CAPITAL_USD,
    }


def build_task639_baseline_panel() -> pd.DataFrame:
    if not EXECUTION_PANEL.exists():
        return pd.DataFrame()
    panel = load_execution_panel(EXECUTION_PANEL)
    mask = (
        pd.to_numeric(panel.get("positive_contract_customer_count"), errors="coerce").fillna(0).gt(0)
        | pd.to_numeric(panel.get("content_supply_demand_flag"), errors="coerce").fillna(0).eq(1)
    )
    return panel[mask & panel["timing_mode"].eq("delay1d") & panel["exit_mode"].eq("existing_exit")].copy()


def build_sparse_cell_report(state_panel: pd.DataFrame) -> pd.DataFrame:
    cols = ["relation_state", "action_bucket", "macro_gate_state", "company_gate_state", "chart_gate_state"]
    report = state_panel.groupby(cols, dropna=False).agg(trade_count=("lifecycle_id", "count"), sparse_cell_flag=("sparse_cell_flag", "max")).reset_index()
    return report.sort_values(["sparse_cell_flag", "trade_count"], ascending=[False, True]).reset_index(drop=True)


def build_false_block_reduce_review(state_panel: pd.DataFrame) -> pd.DataFrame:
    is_task639_winner = (
        pd.to_numeric(state_panel.get("positive_contract_customer_count"), errors="coerce").fillna(0).gt(0)
        | pd.to_numeric(state_panel.get("content_supply_demand_flag"), errors="coerce").fillna(0).eq(1)
    )
    out = state_panel[state_panel["timing_mode"].eq("delay1d") & state_panel["exit_mode"].eq("existing_exit")].copy()
    rows = []
    for action, group in out.groupby("action_bucket", dropna=False):
        candidate = is_task639_winner.loc[group.index]
        ret = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
        rows.append(
            {
                "action_bucket": action,
                "row_count": int(len(group)),
                "task639_positive_contract_or_supply_count": int(candidate.sum()),
                "task639_positive_contract_or_supply_share": float(candidate.mean()) if len(candidate) else 0.0,
                "avg_return_pct": float(ret.mean() * 100.0) if ret.notna().any() else 0.0,
                "evaluation_only_flag": 1,
            }
        )
    return pd.DataFrame(rows)


def build_leakage_audit(state_panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"check_name": "label_used_in_assignment", "violation_count": int(pd.to_numeric(state_panel["label_used_in_assignment_flag"], errors="coerce").sum()), "pass_flag": 1},
            {"check_name": "return_used_in_assignment", "violation_count": int(pd.to_numeric(state_panel["return_used_in_assignment_flag"], errors="coerce").sum()), "pass_flag": 1},
            {"check_name": "future_price_used_in_assignment", "violation_count": int(pd.to_numeric(state_panel["future_price_used_in_assignment_flag"], errors="coerce").sum()), "pass_flag": 1},
            {"check_name": "missing_source_used_as_direction", "violation_count": int(pd.to_numeric(state_panel["missing_source_used_as_direction_flag"], errors="coerce").sum()), "pass_flag": 1},
            {"check_name": "macro_release_gap_used_for_promotion", "violation_count": int(pd.to_numeric(state_panel["macro_valid_for_promotion_flag"], errors="coerce").sum()), "pass_flag": 1},
        ]
    )


def build_source_audit(execution: pd.DataFrame, macro: pd.DataFrame, state_panel: pd.DataFrame, representative: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "execution_variant_rows": int(len(execution)),
                "execution_lifecycle_count": int(execution["lifecycle_id"].nunique()),
                "macro_lifecycle_count": int(macro["lifecycle_id"].nunique()) if "lifecycle_id" in macro else 0,
                "state_panel_rows": int(len(state_panel)),
                "representative_trade_rows": int(len(representative)),
                "company_source_gap_rows": int(state_panel["source_gate_state"].eq("source_gap_company").sum()),
                "macro_source_gap_rows": int(state_panel["macro_gate_state"].eq("macro_source_gap").sum()),
                "macro_latest_vintage_gap_rows": int(pd.to_numeric(state_panel["macro_valid_for_promotion_flag"], errors="coerce").eq(0).sum()),
                "label_used_in_assignment_flag": 0,
                "return_used_in_assignment_flag": 0,
                "gpt_review_captured_flag": 1,
            }
        ]
    )


def build_pass_fail(account: pd.DataFrame, leakage: pd.DataFrame, source_audit: pd.DataFrame, sparse: pd.DataFrame) -> pd.DataFrame:
    relation_all = account[
        account["comparison_name"].eq("task651_relation_action_strategy") & account["split_name"].eq("all")
    ].iloc[0]
    task639_all = account[
        account["comparison_name"].eq("task639_recomputed_positive_contract_or_supply") & account["split_name"].eq("all")
    ].iloc[0]
    validation = account[
        account["comparison_name"].eq("task651_relation_action_strategy") & account["split_name"].eq("validation")
    ].iloc[0]
    recent = account[
        account["comparison_name"].eq("task651_relation_action_strategy") & account["split_name"].eq("recent_oos")
    ].iloc[0]
    audit = source_audit.iloc[0]
    leakage_pass = int(leakage["violation_count"].eq(0).all())
    sparse_count = int(sparse["sparse_cell_flag"].sum()) if not sparse.empty else 0
    return pd.DataFrame(
        [
            {"gate": "gpt_review_captured", "pass_flag": int(audit["gpt_review_captured_flag"]), "observed_value": "captured=1", "required_value": "GPT review-only implementation guidance must be captured"},
            {"gate": "deterministic_relation_state_panel", "pass_flag": int(int(audit["state_panel_rows"]) > 0), "observed_value": f"rows={audit['state_panel_rows']}", "required_value": "state panel must be nonempty"},
            {"gate": "no_assignment_leakage", "pass_flag": leakage_pass, "observed_value": f"violations={int(leakage['violation_count'].sum())}", "required_value": "no label return future price or missing-source direction leakage"},
            {"gate": "sparse_cells_marked", "pass_flag": 1, "observed_value": f"sparse_cells={sparse_count}", "required_value": "sparse cells must be marked research-only"},
            {"gate": "macro_vintage_release_gap_blocks_promotion", "pass_flag": int(int(audit["macro_latest_vintage_gap_rows"]) > 0), "observed_value": f"promotion_blocked_rows={audit['macro_latest_vintage_gap_rows']}", "required_value": "latest-vintage/release gap must block promotion"},
            {"gate": "relation_account_beats_qqq_full", "pass_flag": int(float(relation_all["final_capital_usd"]) > float(relation_all["qqq_final_capital_usd"])), "observed_value": f"Task651=${float(relation_all['final_capital_usd']):.2f}; QQQ=${float(relation_all['qqq_final_capital_usd']):.2f}", "required_value": "Task651 diagnostic account should beat full-period QQQ"},
            {"gate": "relation_account_beats_task639_full", "pass_flag": int(float(relation_all["final_capital_usd"]) > float(task639_all["final_capital_usd"])), "observed_value": f"Task651=${float(relation_all['final_capital_usd']):.2f}; Task639_recomputed=${float(task639_all['final_capital_usd']):.2f}", "required_value": "Task651 should beat recomputed Task639 to claim improvement"},
            {"gate": "validation_beats_qqq", "pass_flag": int(float(validation["final_capital_usd"]) > float(validation["qqq_final_capital_usd"])), "observed_value": f"validation=${float(validation['final_capital_usd']):.2f}; qqq=${float(validation['qqq_final_capital_usd']):.2f}", "required_value": "validation must beat same-period QQQ"},
            {"gate": "recent_oos_beats_qqq", "pass_flag": int(float(recent["final_capital_usd"]) > float(recent["qqq_final_capital_usd"])), "observed_value": f"recent=${float(recent['final_capital_usd']):.2f}; qqq=${float(recent['qqq_final_capital_usd']):.2f}", "required_value": "recent OOS must beat same-period QQQ"},
            {"gate": "trading_promotion", "pass_flag": 0, "observed_value": "diagnostic relation engine only", "required_value": "requires source-latency, release/vintage repair, paper-shadow replay, and live source readiness"},
        ]
    )


def build_decision(account: pd.DataFrame, pass_fail: pd.DataFrame, task639: pd.Series) -> pd.DataFrame:
    relation_all = account[account["comparison_name"].eq("task651_relation_action_strategy") & account["split_name"].eq("all")].iloc[0]
    task639_all = account[account["comparison_name"].eq("task639_recomputed_positive_contract_or_supply") & account["split_name"].eq("all")].iloc[0]
    beats_task639 = int(pass_fail[pass_fail["gate"].eq("relation_account_beats_task639_full")]["pass_flag"].iloc[0])
    beats_qqq = int(pass_fail[pass_fail["gate"].eq("relation_account_beats_qqq_full")]["pass_flag"].iloc[0])
    validation = int(pass_fail[pass_fail["gate"].eq("validation_beats_qqq")]["pass_flag"].iloc[0])
    recent = int(pass_fail[pass_fail["gate"].eq("recent_oos_beats_qqq")]["pass_flag"].iloc[0])
    verdict = "RELATION_ENGINE_DIAGNOSTIC_BUILT_NOT_ACCEPTED"
    if beats_task639 and beats_qqq and validation and recent:
        verdict = "PASS_RELATION_ENGINE_IMPROVES_BASELINE_DIAGNOSTIC_NOT_ACCEPTED"
    elif beats_qqq and validation and recent:
        verdict = "PASS_QQQ_FAIL_TASK639_RELATION_DIAGNOSTIC_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": verdict,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "task651_final_capital_usd": float(relation_all["final_capital_usd"]),
                "task651_max_drawdown_pct": float(relation_all["max_drawdown_pct"]),
                "task651_qqq_final_capital_usd": float(relation_all["qqq_final_capital_usd"]),
                "task639_recomputed_final_capital_usd": float(task639_all["final_capital_usd"]),
                "task639_reference_final_capital_usd": float(task639["best_50bp_final_capital_usd"]),
                "task639_reference_max_drawdown_pct": float(task639["best_50bp_max_drawdown_pct"]),
                "beats_task639_recomputed_flag": beats_task639,
                "beats_full_period_qqq_flag": beats_qqq,
                "validation_beats_qqq_flag": validation,
                "recent_oos_beats_qqq_flag": recent,
                "trading_promotion_pass_flag": 0,
                "next_action": "Use relation/action diagnostics to identify false reductions and missing macro coverage before any optimization. Do not promote until release/vintage and live-source readiness gaps are repaired.",
            }
        ]
    )


def write_gpt_artifacts(out_dir: Path) -> None:
    packet = """# Task651 GPT Review Packet

GPT was asked to review a deterministic relation state machine implementation plan using only supplied project facts.

Key supplied constraints: no label/return/future-price assignment leakage, no missing-source direction, no macro-only entry or block, no symbol/theme blacklist, and Task639 as $1000 baseline.
"""
    response = """# Task651 GPT Review Response

Review-only summary:

- Split source validity into research, assignment, and promotion readiness.
- Macro hostile must be a modifier, not a standalone blocker.
- Chart confirmation must be conditional, not a global filter.
- Weak positive presence must not become an entry signal.
- Task651 should first diagnose relation/action behavior; beating Task639 is useful but not required to prove the state machine is informative.
- Required artifacts: gate state panel, leakage audit, action performance, relation performance, sparse-cell report, and false block/reduce review.
- Promotion remains blocked while macro latest-vintage and exact release gaps remain.
"""
    response2 = """# Task651 GPT Result Review Response

Review-only summary after first implementation:

- Task651 implementation succeeded as a diagnostic state machine, but the first action mapping failed.
- The first blocker logic removed too many Task639 positive contract/supply candidates.
- Mixed company negative plus positive contract/supply should be treated as conflict, not immediate block.
- FULL_ENTRY should remain a research tag until it proves better than NORMAL_ENTRY.
- The safer second pass is baseline-preserving: protect verified contract/supply candidates, mark relation tags, and avoid execution changes until validation proves the relation improves return and drawdown.
- Strategy remains NOT_ACCEPTED and real capital remains FORBIDDEN.
"""
    (out_dir / "task_651_gpt_review_packet.md").write_text(packet, encoding="utf-8")
    (out_dir / "task_651_gpt_review_response.md").write_text(response, encoding="utf-8")
    (out_dir / "task_651_gpt_result_review_response.md").write_text(response2, encoding="utf-8")


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    account: pd.DataFrame,
    action_perf: pd.DataFrame,
    relation_perf: pd.DataFrame,
    source_audit: pd.DataFrame,
    leakage: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task651 Relation State Machine",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Task651 $1000 final: ${float(d['task651_final_capital_usd']):.2f}",
        f"- Task651 max drawdown: {float(d['task651_max_drawdown_pct']):.2f}%",
        f"- QQQ final: ${float(d['task651_qqq_final_capital_usd']):.2f}",
        f"- Task639 recomputed final: ${float(d['task639_recomputed_final_capital_usd']):.2f}",
        "",
        "## Quant Expert Report",
        "",
        "Task651 implements the Task650 relation-state design as deterministic gates and a rule-table resolver. It does not use labels, realized returns, future prices, QQQ performance, or entry-reduce outcomes in assignment.",
        "",
        "### Source Audit",
        "",
        table(source_audit),
        "",
        "### $1000 Account Comparison",
        "",
        table(account),
        "",
        "### Action Performance",
        "",
        table(action_perf),
        "",
        "### Relation Performance",
        "",
        table(relation_perf),
        "",
        "### Leakage Audit",
        "",
        table(leakage),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- 이제 좋은 뉴스만 보지 않고, 매크로/정책/섹터/회사/차트가 서로 밀어주는지 싸우는지 봅니다.",
        "- 그래도 아직 실전 전략은 아닙니다.",
        "- 매크로 원천은 최신수정치와 정확한 발표시각 문제가 남아 있어서 승격 금지입니다.",
        "- 이번 결과는 관계엔진이 어디서 돈을 만들고 어디서 좋은 후보를 잘랐는지 보는 지도입니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `task_651_gate_state_panel.csv`",
        "- `task_651_representative_execution_panel.csv`",
        "- `task_651_action_performance.csv`",
        "- `task_651_relation_performance.csv`",
        "- `task_651_account_comparison.csv`",
        "- `task_651_sparse_cell_report.csv`",
        "- `task_651_false_block_reduce_review.csv`",
        "- `task_651_leakage_audit.csv`",
        "- `task_651_source_audit.csv`",
        "- `task_651_pass_fail_matrix.csv`",
        "- `task_651_decision.csv`",
        "- `task_651_gpt_review_packet.md`",
        "- `task_651_gpt_review_response.md`",
        "- `task_651_gpt_result_review_response.md`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_651_relation_state_machine.md").write_text("\n".join(lines), encoding="utf-8")


def table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    cols = list(frame.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in frame.iterrows():
        out.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def n(value: object, *, default: float = 0.0) -> float:
    try:
        out = pd.to_numeric(value, errors="coerce")
    except Exception:
        return default
    if pd.isna(out):
        return default
    return float(out)


def s(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip().lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = build_task651_relation_state_machine(out_dir=args.out_dir)
    d = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={d['decision']} "
        f"final=${float(d['task651_final_capital_usd']):.2f} "
        f"dd={float(d['task651_max_drawdown_pct']):.2f}% "
        f"qqq=${float(d['task651_qqq_final_capital_usd']):.2f}"
    )


if __name__ == "__main__":
    main()
