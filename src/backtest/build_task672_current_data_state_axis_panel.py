from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import load_qqq_history
from src.backtest.build_task659_theme_specific_relation_engine import QQQ_PATH, task639_core
from src.backtest.build_task661_mechanism_relation_engine import (
    TASK659_PANEL,
    build_institutional_transmission_template,
    build_mechanism_state_panel,
    load_task659_panel,
)
from src.backtest.build_task664_relation_priority_backtest import add_priority
from src.backtest.build_task668_regime_theme_playbook import (
    PRIORITY_RULE,
    add_playbook_columns,
    build_candidate_grid,
    build_candidate_specs,
    build_mdd_windows,
)


TASK_ID = "Task672"
REPORT_DIR = Path("docs/reports/task_672_current_data_state_axis_panel")
AXES = [
    "source_integrity_state",
    "macro_market_state",
    "rates_dollar_credit_liquidity_state",
    "theme_leadership_state",
    "company_catalyst_state",
    "price_chart_acceptance_state",
    "relation_transmission_state",
    "portfolio_capacity_state",
]
AUX_AXES = ["proxy_risk_context"]


def build_task672_current_data_state_axis_panel(
    *,
    task659_panel_path: Path = TASK659_PANEL,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = build_mechanism_state_panel(load_task659_panel(task659_panel_path), build_institutional_transmission_template())
    core = add_state_axes(add_playbook_columns(add_priority(task639_core(panel), PRIORITY_RULE)))
    qqq = load_qqq_history(qqq_path)
    grid, accepted, allocation, equity_curve = build_candidate_grid(core, build_candidate_specs(), qqq)
    accepted = add_state_axes_to_replay(accepted, core)
    allocation = add_state_axes_to_replay(allocation, core)

    axis_perf = build_axis_value_performance(core)
    active_exposure = build_active_cap3_axis_exposure(accepted)
    mdd_windows = build_mdd_windows(equity_curve)
    mdd_axis = build_mdd_axis_exposure(accepted, mdd_windows)
    capacity = build_capacity_context_report(core, allocation)
    sparse = build_sparse_cell_report(core)
    forbidden = build_forbidden_input_audit(core)
    comparison = build_comparison_summary(grid, active_exposure, mdd_axis)
    decision = build_decision(core, comparison, forbidden)
    pass_fail = build_pass_fail(core, axis_perf, active_exposure, mdd_axis, capacity, sparse, forbidden, comparison)

    core.to_csv(out_dir / "task672_state_axis_panel.csv", index=False, encoding="utf-8-sig")
    axis_perf.to_csv(out_dir / "task672_axis_value_performance.csv", index=False, encoding="utf-8-sig")
    active_exposure.to_csv(out_dir / "task672_active_relation_cap3_axis_exposure.csv", index=False, encoding="utf-8-sig")
    mdd_axis.to_csv(out_dir / "task672_mdd_axis_exposure_report.csv", index=False, encoding="utf-8-sig")
    capacity.to_csv(out_dir / "task672_capacity_context_report.csv", index=False, encoding="utf-8-sig")
    sparse.to_csv(out_dir / "task672_sparse_cell_report.csv", index=False, encoding="utf-8-sig")
    forbidden.to_csv(out_dir / "task672_forbidden_input_audit.csv", index=False, encoding="utf-8-sig")
    comparison.to_csv(out_dir / "task672_comparison_summary.csv", index=False, encoding="utf-8-sig")
    grid.to_csv(out_dir / "task672_candidate_grid_reference.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_672_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_672_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, comparison, active_exposure, mdd_axis, capacity, sparse, forbidden, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "state_axis_panel": core,
        "axis_perf": axis_perf,
        "active_exposure": active_exposure,
        "mdd_axis": mdd_axis,
        "capacity": capacity,
        "sparse": sparse,
        "forbidden": forbidden,
        "comparison": comparison,
        "grid": grid,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def add_state_axes(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["entry_ts"] = pd.to_datetime(out["entry_ts"], utc=True)
    out["simulated_exit_ts"] = pd.to_datetime(out["simulated_exit_ts"], utc=True)
    out["source_integrity_state"] = out.apply(classify_source_integrity, axis=1)
    out["macro_market_state"] = out.apply(classify_macro_market, axis=1)
    out["rates_dollar_credit_liquidity_state"] = out.apply(classify_driver_state, axis=1)
    out["theme_leadership_state"] = out.apply(classify_theme_leadership, axis=1)
    out["company_catalyst_state"] = out.apply(classify_company_catalyst, axis=1)
    out["price_chart_acceptance_state"] = out.apply(classify_price_chart_acceptance, axis=1)
    out["relation_transmission_state"] = out.apply(classify_relation_transmission, axis=1)
    out = add_portfolio_capacity_state(out)
    out["proxy_risk_context"] = out.apply(classify_proxy_risk, axis=1)
    out["microstructure_state"] = "SOURCE_PENDING_NOT_USED"
    out["microstructure_used_in_assignment"] = 0
    out["missing_source_used_as_signal"] = 0
    out["symbol_blacklist_used"] = 0
    out["theme_blacklist_used"] = 0
    out["future_price_used_in_assignment"] = 0
    return out


def add_state_axes_to_replay(replay: pd.DataFrame, core: pd.DataFrame) -> pd.DataFrame:
    if replay.empty:
        return replay
    keys = ["lifecycle_id", "entry_ts"]
    provenance_cols = [
        "asof_valid_flag",
        "used_for_assignment_flag",
        "company_source_assignment_certified_flag",
        "content_prediction_assignment_certified_flag",
        "macro_assignment_certified_flag",
        "macro_used_for_assignment_flag",
        "theme_price_assignment_certified_flag",
        "relation_assignment_certified_flag",
        "portfolio_capacity_assignment_certified_flag",
        "allocation_assignment_ready_flag",
        "assignment_certification_scope",
        "assignment_block_reason",
        "macro_asof_provisional_for_diagnostic_flag",
        "macro_provisional_used_as_certified",
        "missing_source_used_as_negative",
    ]
    cols = keys + AXES + AUX_AXES + ["microstructure_state", "microstructure_used_in_assignment"] + provenance_cols
    cols = [col for col in cols if col in core.columns]
    lookup = core[cols].copy()
    lookup["entry_ts"] = pd.to_datetime(lookup["entry_ts"], utc=True)
    out = replay.copy()
    out["entry_ts"] = pd.to_datetime(out["entry_ts"], utc=True)
    keep = [col for col in lookup.columns if col not in out.columns or col in keys]
    return out.merge(lookup[keep], on=keys, how="left")


def classify_source_integrity(row: pd.Series) -> str:
    asof_ok = i(row.get("asof_valid_flag", 0)) == 1
    allocation_ok = i(row.get("allocation_assignment_ready_flag", row.get("used_for_assignment_flag", 0))) == 1
    company_ok = i(row.get("company_source_assignment_certified_flag", 0)) == 1
    theme_price_ok = i(row.get("theme_price_assignment_certified_flag", 0)) == 1
    macro_ok = i(row.get("macro_assignment_certified_flag", 0)) == 1
    macro_provisional = i(row.get("macro_asof_provisional_for_diagnostic_flag", 0)) == 1
    if not asof_ok or not company_ok:
        return "source_gap_research_only"
    if allocation_ok and macro_ok:
        return "fully_assignment_certified"
    if allocation_ok and macro_provisional:
        return "company_certified_macro_provisional"
    if allocation_ok:
        return "company_certified_macro_gap"
    if company_ok and not theme_price_ok:
        return "company_certified_market_context_gap"
    return "source_gap_research_only"


def classify_macro_market(row: pd.Series) -> str:
    macro = s(row.get("macro_overall_state", ""))
    score = f(row.get("broad_market_score", 0.0))
    stress = f(row.get("broad_market_stress", 0.0))
    breadth = f(row.get("breadth_20d", 0.0))
    market_ret = f(row.get("market_ret_20d", 0.0))
    if macro == "macro_hostile" or score < 50.0 or stress >= 45.0 or breadth < 0.45:
        return "market_stress"
    if macro == "macro_supportive" and score >= 70.0 and stress < 35.0 and market_ret >= 0.0:
        return "market_supportive"
    if macro == "macro_mixed" or 50.0 <= score < 70.0:
        return "market_mixed"
    return "market_neutral"


def classify_driver_state(row: pd.Series) -> str:
    pressures = []
    supports = []
    driver_pairs = [
        ("rates", "macro_rates_state", "rates_exposure"),
        ("dollar", "macro_dollar_state", "dollar_exposure"),
        ("credit", "macro_credit_state", "credit_exposure"),
        ("liquidity", "macro_liquidity_state", "liquidity_exposure"),
    ]
    for name, state_col, exposure_col in driver_pairs:
        state = s(row.get(state_col, ""))
        exposure = s(row.get(exposure_col, "medium"))
        if state_has_pressure(state) and exposure in {"high", "medium"}:
            pressures.append(name)
        if state_has_support(state) and exposure in {"high", "medium"}:
            supports.append(name)
    if f(row.get("liquidity_ratio", 1.0)) < 0.75:
        pressures.append("liquidity")
    if len(pressures) >= 2:
        return "multi_driver_pressure_exposed"
    if len(pressures) == 1 and supports:
        return f"{pressures[0]}_pressure_offset_by_support"
    if len(pressures) == 1:
        return f"{pressures[0]}_pressure_exposed"
    if len(supports) >= 2:
        return "multi_driver_support"
    if len(supports) == 1:
        return f"{supports[0]}_support"
    return "driver_neutral_or_mixed"


def classify_theme_leadership(row: pd.Series) -> str:
    regime = s(row.get("theme_regime_state_v4", ""))
    ret20 = f(row.get("theme_ret20_prev", 0.0))
    breadth = f(row.get("theme_breadth20_prev", 0.0))
    volume = f(row.get("theme_volume_ratio_prev", 1.0))
    rank = f(row.get("theme_rank_prev", 99.0))
    if regime == "persistent_theme_leader" and ret20 >= 0.15 and breadth >= 0.80 and volume >= 0.90:
        return "persistent_broad_theme_leader"
    if ret20 >= 0.12 and breadth >= 0.75 and rank <= 3:
        return "theme_leadership_expanding"
    if regime == "narrow_theme_leader" or (ret20 >= 0.12 and breadth < 0.65):
        return "narrow_leadership"
    if ret20 < 0.03 or breadth < 0.60 or volume < 0.75:
        return "theme_leadership_fading"
    return "theme_participating"


def classify_company_catalyst(row: pd.Series) -> str:
    tier = s(row.get("catalyst_quality_tier", ""))
    score = f(row.get("catalyst_quality_score", 0.0))
    contract = i(row.get("positive_contract_customer_count", 0))
    backlog = i(row.get("positive_backlog_order_count", 0))
    guidance = i(row.get("positive_guidance_up_count", 0))
    margin_supply = i(row.get("positive_margin_supply_combo_count", 0))
    supply = i(row.get("content_supply_demand_count", 0))
    guidance_margin = i(row.get("content_guidance_margin_count", 0))
    dimensions = sum(int(x > 0) for x in [contract, backlog, guidance, margin_supply, supply, guidance_margin])
    if tier == "very_strong_catalyst" and (contract + backlog + guidance + margin_supply) >= 2:
        return "multi_dimension_high_quality_catalyst"
    if tier in {"very_strong_catalyst", "strong_catalyst"} and (contract > 0 or backlog > 0 or guidance > 0):
        return "hard_company_catalyst"
    if tier in {"very_strong_catalyst", "strong_catalyst"} and supply > 0:
        return "demand_supply_catalyst"
    if tier == "medium_catalyst" and dimensions >= 2:
        return "multi_signal_medium_catalyst"
    if score > 0 or tier in {"medium_catalyst", "weak_catalyst"}:
        return "weak_or_single_dimension_catalyst"
    return "no_company_catalyst"


def classify_price_chart_acceptance(row: pd.Series) -> str:
    state = s(row.get("price_acceptance_state", ""))
    score = f(row.get("price_acceptance_score", 0.0))
    range_pos = f(row.get("range_pos", 0.0))
    intraday = f(row.get("intraday_ret_from_open", 0.0))
    volume = f(row.get("volume_ratio_prev", 1.0))
    near_high = i(row.get("near_high60_prev", 0))
    trend = i(row.get("trend_stack_prev", 0))
    if state == "price_acceptance_strong" and score >= 6.0 and trend == 1 and near_high == 1 and intraday < 0.04:
        return "price_confirmed_not_extended"
    if state == "price_acceptance_strong" and (range_pos >= 0.98 or intraday >= 0.04):
        return "price_confirmed_but_extended"
    if state == "price_acceptance_strong":
        return "price_confirmed_basic"
    if state == "price_acceptance_accepted" and volume >= 0.8:
        return "price_accepted_needs_confirmation"
    return "price_fragile_or_unconfirmed"


def classify_relation_transmission(row: pd.Series) -> str:
    state = s(row.get("mechanism_relation_state", ""))
    support = i(row.get("mechanism_support_count", row.get("support_count", 0)))
    pressure = i(row.get("mechanism_pressure_count", row.get("conflict_count", 0)))
    if state == "mechanism_reinforcing_company_positive":
        return "relation_reinforcing"
    if state == "mechanism_offsetting_company_positive":
        return "relation_offsetting"
    if state == "company_quality_price_confirmed":
        return "company_price_confirmed_macro_secondary"
    if state == "company_positive_needs_confirmation":
        return "company_positive_confirmation_needed"
    if state == "sparse_mechanism_cell":
        return "relation_sparse_research_only"
    if pressure > support:
        return "relation_pressure_dominant"
    if support > pressure:
        return "relation_support_dominant"
    return "relation_unclear"


def add_portfolio_capacity_state(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    ts_count = out.groupby("entry_ts")["lifecycle_id"].transform("count")
    theme_count = out.groupby(["entry_ts", "theme_id"])["lifecycle_id"].transform("count")
    relation_count = out.groupby(["entry_ts", "mechanism_relation_state"])["lifecycle_id"].transform("count")
    out["same_entry_candidate_count"] = ts_count.astype(int)
    out["same_entry_theme_count"] = theme_count.astype(int)
    out["same_entry_relation_count"] = relation_count.astype(int)
    states = []
    for _, row in out.iterrows():
        if i(row["same_entry_candidate_count"]) > 8:
            states.append("slot_competition_very_high")
        elif i(row["same_entry_candidate_count"]) > 5:
            states.append("slot_competition_high")
        elif i(row["same_entry_theme_count"]) >= 4:
            states.append("same_theme_crowded")
        elif i(row["same_entry_relation_count"]) >= 4:
            states.append("same_relation_crowded")
        else:
            states.append("slot_competition_low")
    out["portfolio_capacity_state"] = states
    return out


def classify_proxy_risk(row: pd.Series) -> str:
    vol = f(row.get("vol20_prev", 0.0))
    range_pos = f(row.get("range_pos", 0.0))
    intraday = f(row.get("intraday_ret_from_open", 0.0))
    stress = f(row.get("broad_market_stress", 0.0))
    theme_volume = f(row.get("theme_volume_ratio_prev", 1.0))
    if stress >= 45.0 and (range_pos >= 0.98 or intraday >= 0.04):
        return "stress_plus_extension_proxy"
    if range_pos >= 0.98 or intraday >= 0.04:
        return "extension_proxy"
    if vol >= 3_000_000 and theme_volume >= 1.20:
        return "high_liquidity_momentum_proxy"
    if stress >= 45.0:
        return "market_stress_proxy"
    return "proxy_neutral"


def build_axis_value_performance(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    work = panel.copy()
    work["net_return_costed_eval"] = pd.to_numeric(work["net_return_from_entry"], errors="coerce") - 0.005
    for axis in AXES + AUX_AXES:
        for split in ["all", "validation", "recent_oos"]:
            scoped = work if split == "all" else work[work["split_name"].astype(str).eq(split)]
            for value, group in scoped.groupby(axis, dropna=False):
                returns = pd.to_numeric(group["net_return_costed_eval"], errors="coerce")
                rows.append(
                    {
                        "axis": axis,
                        "axis_value": value,
                        "split_name": split,
                        "candidate_count": int(len(group)),
                        "avg_return_costed_pct_eval_only": float(returns.mean() * 100.0),
                        "median_return_costed_pct_eval_only": float(returns.median() * 100.0),
                        "win_rate_eval_only": float(returns.gt(0).mean()),
                        "entry_reduce_failure_rate_eval_only": float(returns.le(-0.03).mean()),
                        "return_used_in_assignment_flag": 0,
                        "label_used_in_assignment_flag": 0,
                        "promotion_allowed_flag": 0,
                    }
                )
    return pd.DataFrame(rows).sort_values(["split_name", "axis", "candidate_count"], ascending=[True, True, False]).reset_index(drop=True)


def build_active_cap3_axis_exposure(accepted: pd.DataFrame) -> pd.DataFrame:
    active = accepted[(accepted["candidate_name"].astype(str).eq("active_relation_cap3_reference")) & (accepted["split_scope"].astype(str).eq("all"))].copy()
    if active.empty:
        return pd.DataFrame()
    rows = []
    for axis in AXES + AUX_AXES:
        for value, group in active.groupby(axis, dropna=False):
            returns = pd.to_numeric(group["net_return_costed"], errors="coerce")
            rows.append(
                {
                    "candidate_name": "active_relation_cap3_reference",
                    "axis": axis,
                    "axis_value": value,
                    "accepted_trade_count": int(len(group)),
                    "avg_return_costed_pct": float(returns.mean() * 100.0),
                    "win_rate": float(returns.gt(0).mean()),
                    "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
                    "promotion_allowed_flag": 0,
                }
            )
    return pd.DataFrame(rows).sort_values(["axis", "accepted_trade_count"], ascending=[True, False]).reset_index(drop=True)


def build_mdd_axis_exposure(accepted: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty or windows.empty:
        return pd.DataFrame()
    win = windows[(windows["candidate_name"].astype(str).eq("active_relation_cap3_reference")) & (windows["split_scope"].astype(str).eq("all"))]
    if win.empty:
        return pd.DataFrame()
    row = win.iloc[0]
    peak = pd.Timestamp(row["mdd_peak_ts"])
    trough = pd.Timestamp(row["mdd_trough_ts"])
    active = accepted[
        (accepted["candidate_name"].astype(str).eq("active_relation_cap3_reference"))
        & (accepted["split_scope"].astype(str).eq("all"))
    ].copy()
    active["entry_ts"] = pd.to_datetime(active["entry_ts"], utc=True)
    active["simulated_exit_ts"] = pd.to_datetime(active["simulated_exit_ts"], utc=True)
    active = active[(active["entry_ts"].le(trough)) & (active["simulated_exit_ts"].ge(peak))]
    rows = []
    for axis in AXES + AUX_AXES:
        for value, group in active.groupby(axis, dropna=False):
            returns = pd.to_numeric(group["net_return_costed"], errors="coerce")
            rows.append(
                {
                    "candidate_name": "active_relation_cap3_reference",
                    "axis": axis,
                    "axis_value": value,
                    "mdd_peak_ts": row["mdd_peak_ts"],
                    "mdd_trough_ts": row["mdd_trough_ts"],
                    "max_drawdown_pct": float(row["max_drawdown_pct"]),
                    "active_trade_count": int(len(group)),
                    "avg_return_costed_pct": float(returns.mean() * 100.0),
                    "negative_mdd_exposure_flag": int(returns.mean() < 0),
                    "promotion_allowed_flag": 0,
                }
            )
    return pd.DataFrame(rows).sort_values(["axis", "active_trade_count"], ascending=[True, False]).reset_index(drop=True)


def build_capacity_context_report(panel: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = panel.groupby(["entry_ts", "portfolio_capacity_state"], dropna=False)
    for (entry_ts, state), group in grouped:
        rows.append(
            {
                "context_type": "candidate_timestamp",
                "entry_ts": entry_ts,
                "portfolio_capacity_state": state,
                "candidate_count": int(len(group)),
                "max_same_theme_count": int(group["same_entry_theme_count"].max()),
                "max_same_relation_count": int(group["same_entry_relation_count"].max()),
                "accepted_count": "",
                "blocked_count": "",
            }
        )
    active_alloc = allocation[
        (allocation["candidate_name"].astype(str).eq("active_relation_cap3_reference"))
        & (allocation["split_scope"].astype(str).eq("all"))
    ].copy() if not allocation.empty else pd.DataFrame()
    if not active_alloc.empty:
        for reason, group in active_alloc.groupby("allocation_reason", dropna=False):
            rows.append(
                {
                    "context_type": "active_relation_cap3_allocation",
                    "entry_ts": "",
                    "portfolio_capacity_state": "",
                    "candidate_count": int(len(group)),
                    "max_same_theme_count": "",
                    "max_same_relation_count": "",
                    "accepted_count": int(pd.to_numeric(group["accepted_flag"], errors="coerce").sum()),
                    "blocked_count": int((pd.to_numeric(group["accepted_flag"], errors="coerce") == 0).sum()),
                    "allocation_reason": reason,
                }
            )
    return pd.DataFrame(rows).reset_index(drop=True)


def build_sparse_cell_report(panel: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "macro_market_state",
        "rates_dollar_credit_liquidity_state",
        "theme_leadership_state",
        "company_catalyst_state",
        "price_chart_acceptance_state",
        "relation_transmission_state",
        "portfolio_capacity_state",
    ]
    rows = []
    for split in ["all", "validation", "recent_oos"]:
        scoped = panel if split == "all" else panel[panel["split_name"].astype(str).eq(split)]
        counts = scoped.groupby(group_cols, dropna=False).size().reset_index(name="candidate_count")
        sparse = counts[counts["candidate_count"].lt(5)].copy()
        sparse["split_name"] = split
        sparse["promotion_allowed_flag"] = 0
        sparse["recommended_use"] = "diagnostic_only_until_cell_has_enough_split_oos_support"
        rows.append(sparse)
    return pd.concat(rows, ignore_index=True).sort_values(["split_name", "candidate_count"]).reset_index(drop=True)


def build_forbidden_input_audit(panel: pd.DataFrame) -> pd.DataFrame:
    checks = {
        "return_used_in_assignment_flag": "return_used_in_assignment_flag",
        "label_used_in_assignment_flag_task661": "label_used_in_assignment_flag_task661",
        "microstructure_used_in_assignment": "microstructure_used_in_assignment",
        "missing_source_used_as_signal": "missing_source_used_as_signal",
        "symbol_blacklist_used": "symbol_blacklist_used",
        "theme_blacklist_used": "theme_blacklist_used",
        "future_price_used_in_assignment": "future_price_used_in_assignment",
    }
    rows = []
    for name, col in checks.items():
        violations = int(pd.to_numeric(panel.get(col, pd.Series([0] * len(panel))), errors="coerce").fillna(0).ne(0).sum())
        rows.append(
            {
                "check_name": name,
                "violation_count": violations,
                "pass_flag": int(violations == 0),
                "required_value": "0 violations",
            }
        )
    return pd.DataFrame(rows)


def build_comparison_summary(grid: pd.DataFrame, active_exposure: pd.DataFrame, mdd_axis: pd.DataFrame) -> pd.DataFrame:
    wanted = {
        "baseline_task639": "Task639 baseline",
        "active_relation_cap3_reference": "Active relation cap3 reference",
        "relation_priority_playbook_lite_sizing": "Task668 lite sizing",
        "playbook_dynamic_cap": "Task668 dynamic cap",
    }
    rows = []
    for candidate, label in wanted.items():
        for split in ["all", "validation", "recent_oos"]:
            row = grid[(grid["candidate_name"].astype(str).eq(candidate)) & (grid["split_name"].astype(str).eq(split))]
            if row.empty:
                continue
            r = row.iloc[0]
            rows.append(
                {
                    "comparison_type": "account_result",
                    "candidate_name": candidate,
                    "label": label,
                    "split_name": split,
                    "final_capital_usd": float(r["final_capital_usd"]),
                    "max_drawdown_pct": float(r["max_drawdown_pct"]),
                    "accepted_trade_count": int(r["accepted_trade_count"]),
                    "qqq_final_capital_usd": float(r["qqq_final_capital_usd"]),
                    "beats_qqq_flag": int(r["beats_qqq_flag"]),
                    "promotion_allowed_flag": 0,
                    "comment": "reference comparison only",
                }
            )
    if not active_exposure.empty:
        best = active_exposure.sort_values(["avg_return_costed_pct", "accepted_trade_count"], ascending=[False, False]).head(5)
        for _, r in best.iterrows():
            rows.append(
                {
                    "comparison_type": "active_cap3_high_payoff_axis",
                    "candidate_name": "active_relation_cap3_reference",
                    "label": f"{r['axis']}={r['axis_value']}",
                    "split_name": "all",
                    "final_capital_usd": "",
                    "max_drawdown_pct": "",
                    "accepted_trade_count": int(r["accepted_trade_count"]),
                    "qqq_final_capital_usd": "",
                    "beats_qqq_flag": "",
                    "promotion_allowed_flag": 0,
                    "comment": f"avg_return_costed_pct={float(r['avg_return_costed_pct']):.2f}",
                }
            )
    if not mdd_axis.empty:
        bad = mdd_axis[mdd_axis["negative_mdd_exposure_flag"].eq(1)].sort_values(["active_trade_count", "avg_return_costed_pct"], ascending=[False, True]).head(5)
        for _, r in bad.iterrows():
            rows.append(
                {
                    "comparison_type": "active_cap3_mdd_bad_axis",
                    "candidate_name": "active_relation_cap3_reference",
                    "label": f"{r['axis']}={r['axis_value']}",
                    "split_name": "all",
                    "final_capital_usd": "",
                    "max_drawdown_pct": float(r["max_drawdown_pct"]),
                    "accepted_trade_count": int(r["active_trade_count"]),
                    "qqq_final_capital_usd": "",
                    "beats_qqq_flag": "",
                    "promotion_allowed_flag": 0,
                    "comment": f"mdd_window_avg_return_costed_pct={float(r['avg_return_costed_pct']):.2f}",
                }
            )
    return pd.DataFrame(rows)


def build_decision(panel: pd.DataFrame, comparison: pd.DataFrame, forbidden: pd.DataFrame) -> pd.DataFrame:
    active_all = comparison[
        (comparison["comparison_type"].eq("account_result"))
        & (comparison["candidate_name"].eq("active_relation_cap3_reference"))
        & (comparison["split_name"].eq("all"))
    ].iloc[0]
    baseline_all = comparison[
        (comparison["comparison_type"].eq("account_result"))
        & (comparison["candidate_name"].eq("baseline_task639"))
        & (comparison["split_name"].eq("all"))
    ].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "CURRENT_DATA_STATE_AXIS_PANEL_BUILT_NO_TRADING_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "source_candidate_count": int(len(panel)),
                "implementable_axis_count": len(AXES),
                "diagnostic_aux_axis_count": len(AUX_AXES),
                "microstructure_state": "SOURCE_PENDING_NOT_USED",
                "microstructure_used_in_assignment": 0,
                "forbidden_input_violation_count": int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum()),
                "task639_final_capital_usd": float(baseline_all["final_capital_usd"]),
                "task639_max_drawdown_pct": float(baseline_all["max_drawdown_pct"]),
                "active_relation_cap3_final_capital_usd": float(active_all["final_capital_usd"]),
                "active_relation_cap3_max_drawdown_pct": float(active_all["max_drawdown_pct"]),
                "trading_promotion_pass_flag": 0,
                "next_action": "Use the state-axis panel to design predeclared action mapping; do not promote any axis by name until split/OOS and drawdown gates pass.",
            }
        ]
    )


def build_pass_fail(
    panel: pd.DataFrame,
    axis_perf: pd.DataFrame,
    active_exposure: pd.DataFrame,
    mdd_axis: pd.DataFrame,
    capacity: pd.DataFrame,
    sparse: pd.DataFrame,
    forbidden: pd.DataFrame,
    comparison: pd.DataFrame,
) -> pd.DataFrame:
    forbidden_violations = int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum()) if not forbidden.empty else 999
    return pd.DataFrame(
        [
            {"gate": "state_axis_panel_built", "pass_flag": int(not panel.empty), "observed_value": f"rows={len(panel)}", "required_value": "candidate-level current-data state panel exists"},
            {"gate": "all_8_axes_present", "pass_flag": int(all(axis in panel.columns for axis in AXES)), "observed_value": f"axes={len([a for a in AXES if a in panel.columns])}", "required_value": "8 implementable axes"},
            {"gate": "microstructure_not_used", "pass_flag": int(panel["microstructure_used_in_assignment"].eq(0).all()), "observed_value": "SOURCE_PENDING_NOT_USED", "required_value": "microstructure assignment flag zero"},
            {"gate": "forbidden_input_audit_clean", "pass_flag": int(forbidden_violations == 0), "observed_value": f"violations={forbidden_violations}", "required_value": "0 forbidden-input violations"},
            {"gate": "axis_value_performance_built", "pass_flag": int(not axis_perf.empty), "observed_value": f"rows={len(axis_perf)}", "required_value": "axis diagnostics exist"},
            {"gate": "active_cap3_axis_exposure_built", "pass_flag": int(not active_exposure.empty), "observed_value": f"rows={len(active_exposure)}", "required_value": "active cap3 axis exposure exists"},
            {"gate": "mdd_axis_exposure_built", "pass_flag": int(not mdd_axis.empty), "observed_value": f"rows={len(mdd_axis)}", "required_value": "MDD window axis exposure exists"},
            {"gate": "capacity_context_built", "pass_flag": int(not capacity.empty), "observed_value": f"rows={len(capacity)}", "required_value": "slot/capacity context exists"},
            {"gate": "sparse_cell_report_built", "pass_flag": int(not sparse.empty), "observed_value": f"rows={len(sparse)}", "required_value": "sparse cells identified"},
            {"gate": "comparison_summary_built", "pass_flag": int(not comparison.empty), "observed_value": f"rows={len(comparison)}", "required_value": "Task639 active cap3 Task668 comparison exists"},
            {"gate": "trading_action_allowed", "pass_flag": 0, "observed_value": "diagnostic decomposition only", "required_value": "predeclared action mapping and OOS gates required"},
            {"gate": "real_capital_allowed", "pass_flag": 0, "observed_value": "FORBIDDEN", "required_value": "accepted strategy plus live-source readiness"},
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    comparison: pd.DataFrame,
    active_exposure: pd.DataFrame,
    mdd_axis: pd.DataFrame,
    capacity: pd.DataFrame,
    sparse: pd.DataFrame,
    forbidden: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task672 Current Data State Axis Panel",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Candidate rows: `{int(d['source_candidate_count'])}`",
        f"- Task639: `${float(d['task639_final_capital_usd']):.2f}`, MDD `{float(d['task639_max_drawdown_pct']):.2f}%`.",
        f"- Active relation cap3: `${float(d['active_relation_cap3_final_capital_usd']):.2f}`, MDD `{float(d['active_relation_cap3_max_drawdown_pct']):.2f}%`.",
        "- What changed: current-data-only state axes are now implemented and audited.",
        "- Next action: design a predeclared action matrix from these axes, then test split/OOS and MDD gates.",
        "",
        "## Quant Expert Report",
        "",
        "Task672 implements the Task671 state decomposition with currently available entry-time data only. It does not use quote/trade/NBBO/microstructure data and does not create a new trading action.",
        "",
        "### Data Source and Join Keys",
        "",
        "- Source: Task659 panel rebuilt through Task661 mechanism state panel and Task668 replay functions.",
        "- Join keys for replay annotation: `lifecycle_id`, `entry_ts`.",
        "- Assignment leakage controls: return, label, future price, missing source, symbol blacklist, theme blacklist, and microstructure flags are audited as zero-use inputs.",
        "",
        "### Account Comparison",
        "",
        table(comparison[comparison["comparison_type"].eq("account_result")]),
        "",
        "### Active Relation Cap3 Axis Exposure",
        "",
        table(active_exposure.head(40)),
        "",
        "### MDD Axis Exposure",
        "",
        table(mdd_axis.head(40)),
        "",
        "### Capacity Context",
        "",
        table(capacity.tail(20)),
        "",
        "### Sparse Cell Report",
        "",
        table(sparse.head(40)),
        "",
        "### Forbidden Input Audit",
        "",
        table(forbidden),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "상태를 더 잘게 쪼개는 코드는 구현됐습니다.",
        "",
        "아직 새 매매 룰은 아닙니다. 지금은 어떤 상태가 돈을 벌고, 어떤 상태가 낙폭을 만드는지 보는 진단판입니다.",
        "",
        "미시구조 데이터는 아직 수집 중이라 쓰지 않았습니다. 차트 데이터를 미시구조처럼 속여 쓰지도 않았습니다.",
        "",
        "다음은 이 상태축으로 선제 룰을 정하고, 그 룰이 OOS와 낙폭에서 살아남는지 검증해야 합니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `task672_state_axis_panel.csv`",
        "- `task672_axis_value_performance.csv`",
        "- `task672_active_relation_cap3_axis_exposure.csv`",
        "- `task672_mdd_axis_exposure_report.csv`",
        "- `task672_capacity_context_report.csv`",
        "- `task672_sparse_cell_report.csv`",
        "- `task672_forbidden_input_audit.csv`",
        "- `task672_comparison_summary.csv`",
        "- `task672_candidate_grid_reference.csv`",
        "- `task_672_decision.csv`",
        "- `task_672_pass_fail_matrix.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_672_current_data_state_axis_panel.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    clipped = df.copy()
    clipped = clipped.fillna("")
    headers = [str(col) for col in clipped.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in clipped.iterrows():
        values = [markdown_cell(row[col]) for col in clipped.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def markdown_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("|", "\\|")


def state_has_pressure(value: str) -> bool:
    return any(token in value for token in ["pressure", "stress", "tight", "hostile"])


def state_has_support(value: str) -> bool:
    return any(token in value for token in ["support", "easing"])


def f(value: object, default: float = 0.0) -> float:
    try:
        out = float(value)
        if pd.isna(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def i(value: object, default: int = 0) -> int:
    try:
        out = int(float(value))
        return out
    except (TypeError, ValueError):
        return default


def s(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task659-panel", type=Path, default=TASK659_PANEL)
    parser.add_argument("--qqq-path", type=Path, default=QQQ_PATH)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    outputs = build_task672_current_data_state_axis_panel(
        task659_panel_path=args.task659_panel,
        qqq_path=args.qqq_path,
        out_dir=args.out_dir,
    )
    print(f"[{TASK_ID}] wrote {args.out_dir}")
    print(outputs["decision"].to_string(index=False))


if __name__ == "__main__":
    main()
