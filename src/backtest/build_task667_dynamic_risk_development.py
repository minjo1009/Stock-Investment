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
from src.backtest.build_task659_theme_specific_relation_engine import QQQ_PATH, task639_core
from src.backtest.build_task661_mechanism_relation_engine import (
    TASK659_PANEL,
    build_institutional_transmission_template,
    build_mechanism_state_panel,
    load_task659_panel,
)
from src.backtest.build_task664_relation_priority_backtest import COST_BPS, MAX_POSITIONS, add_priority


TASK_ID = "Task667"
REPORT_DIR = Path("docs/reports/task_667_dynamic_risk_development")
PRIORITY_RULE = "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse"
BASELINE_CANDIDATE = "baseline_task639"


def build_task667_dynamic_risk_development(
    *,
    task659_panel_path: Path = TASK659_PANEL,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = build_mechanism_state_panel(load_task659_panel(task659_panel_path), build_institutional_transmission_template())
    core = add_priority(task639_core(panel), PRIORITY_RULE)
    qqq = load_qqq_history(qqq_path)
    specs = build_candidate_specs()
    candidate_grid, accepted, allocation, equity_curve, sizing_audit = build_candidate_grid(core, specs, qqq)
    promotion = build_promotion_report(candidate_grid, specs)
    mdd_windows = build_mdd_windows(equity_curve)
    mdd_audit = build_mdd_interval_audit(accepted, mdd_windows)
    decision = build_decision(promotion)
    pass_fail = build_pass_fail(specs, promotion, allocation, sizing_audit, mdd_audit)

    specs.to_csv(out_dir / "task667_candidate_specs.csv", index=False, encoding="utf-8-sig")
    candidate_grid.to_csv(out_dir / "task667_candidate_grid.csv", index=False, encoding="utf-8-sig")
    accepted.to_csv(out_dir / "task667_accepted_trades.csv", index=False, encoding="utf-8-sig")
    allocation.to_csv(out_dir / "task667_allocation_panel.csv", index=False, encoding="utf-8-sig")
    equity_curve.to_csv(out_dir / "task667_equity_curve.csv", index=False, encoding="utf-8-sig")
    sizing_audit.to_csv(out_dir / "task667_sizing_audit.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(out_dir / "task667_promotion_report.csv", index=False, encoding="utf-8-sig")
    mdd_windows.to_csv(out_dir / "task667_mdd_windows.csv", index=False, encoding="utf-8-sig")
    mdd_audit.to_csv(out_dir / "task667_mdd_interval_audit.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_667_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_667_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, candidate_grid, promotion, mdd_windows, mdd_audit, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "specs": specs,
        "candidate_grid": candidate_grid,
        "accepted": accepted,
        "allocation": allocation,
        "equity_curve": equity_curve,
        "sizing_audit": sizing_audit,
        "promotion": promotion,
        "mdd_windows": mdd_windows,
        "mdd_audit": mdd_audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_candidate_specs() -> pd.DataFrame:
    rows = [
        {
            "candidate_name": BASELINE_CANDIDATE,
            "candidate_type": "baseline",
            "priority_enabled_flag": 0,
            "active_relation_cap_mode": "none",
            "slot_hurdle_mode": "none",
            "sizing_mode": "equal",
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Task639 chronological baseline with existing timing and exits.",
        },
        {
            "candidate_name": "task666_active_relation_cap3_reference",
            "candidate_type": "reference",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "static3",
            "slot_hurdle_mode": "none",
            "sizing_mode": "equal",
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Task666 promising reference: at most three open positions from the same relation state.",
        },
        {
            "candidate_name": "dynamic_relation_cap_market_only",
            "candidate_type": "predeclared_dynamic_cap",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "market_dynamic",
            "slot_hurdle_mode": "none",
            "sizing_mode": "equal",
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Relation cap is three in clean tape and two in weak or stressed tape using only entry-time market and macro fields.",
        },
        {
            "candidate_name": "slot_hurdle_quality_scarce_slot",
            "candidate_type": "predeclared_slot_hurdle",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "static3",
            "slot_hurdle_mode": "scarce_slot_quality",
            "sizing_mode": "equal",
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "A candidate may consume the last scarce slot only if its entry-time quality score clears a hurdle.",
        },
        {
            "candidate_name": "slot_hurdle_weak_only_scarce_slot",
            "candidate_type": "predeclared_slot_hurdle",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "static3",
            "slot_hurdle_mode": "weak_scarce_slot",
            "sizing_mode": "equal",
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Only weak entry-time quality candidates are blocked from consuming the last scarce slot.",
        },
        {
            "candidate_name": "relation_cap3_risk_proxy_sizing",
            "candidate_type": "predeclared_sizing",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "static3",
            "slot_hurdle_mode": "none",
            "sizing_mode": "risk_proxy_scaled",
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Same relation cap3, but extended or stressed entries use smaller slot capital.",
        },
        {
            "candidate_name": "relation_cap3_contextual_risk_sizing",
            "candidate_type": "predeclared_sizing",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "static3",
            "slot_hurdle_mode": "none",
            "sizing_mode": "contextual_risk_scaled",
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Reduce size only when extension or macro stress combines with weaker relation quality.",
        },
        {
            "candidate_name": "dynamic_cap_slot_hurdle_combo",
            "candidate_type": "predeclared_combo",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "market_dynamic",
            "slot_hurdle_mode": "weak_scarce_slot",
            "sizing_mode": "equal",
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Dynamic relation cap plus scarce-slot admission hurdle.",
        },
        {
            "candidate_name": "dynamic_cap_hurdle_risk_sizing_combo",
            "candidate_type": "predeclared_combo",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "market_dynamic",
            "slot_hurdle_mode": "weak_scarce_slot",
            "sizing_mode": "contextual_risk_scaled",
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Dynamic cap, slot hurdle, and risk proxy sizing together.",
        },
        {
            "candidate_name": "diagnostic_dynamic_relation_cap_market_account",
            "candidate_type": "diagnostic_path_control",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "market_account_dynamic",
            "slot_hurdle_mode": "none",
            "sizing_mode": "equal",
            "diagnostic_only_flag": 1,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Diagnostic only: market dynamic cap plus account drawdown cap tightening.",
        },
        {
            "candidate_name": "diagnostic_equity_drawdown_deleverage",
            "candidate_type": "diagnostic_path_control",
            "priority_enabled_flag": 1,
            "active_relation_cap_mode": "static3",
            "slot_hurdle_mode": "drawdown_hurdle",
            "sizing_mode": "drawdown_scaled",
            "diagnostic_only_flag": 1,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Diagnostic only: when the account is already in drawdown, require a higher quality score and reduce slot size.",
        },
    ]
    return pd.DataFrame(rows)


def build_candidate_grid(core: pd.DataFrame, specs: pd.DataFrame, qqq: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    accepted_rows: list[pd.DataFrame] = []
    allocation_rows: list[pd.DataFrame] = []
    curve_rows: list[pd.DataFrame] = []
    sizing_rows: list[pd.DataFrame] = []
    for _, spec in specs.iterrows():
        panel = core.copy()
        if int(spec["priority_enabled_flag"]) == 0:
            panel = panel.assign(priority_rank=50, priority_rule="entry_ts_then_lifecycle_id")
        for split_name in ["all", "validation", "recent_oos"]:
            scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)].copy()
            quality, accepted, allocation, curve, sizing = simulate_account(scoped, spec)
            qqq_final = qqq_final_for_period(qqq, scoped)
            final = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
            rows.append(
                {
                    "candidate_name": spec["candidate_name"],
                    "split_name": split_name,
                    "candidate_type": spec["candidate_type"],
                    "initial_capital_usd": INITIAL_CAPITAL_USD,
                    "source_trade_count": int(len(scoped)),
                    "accepted_trade_count": int(len(accepted)),
                    "avg_size_multiplier": float(accepted["size_multiplier"].mean()) if not accepted.empty else 0.0,
                    "final_capital_usd": float(final),
                    "capital_return_pct": float(quality["capital_pnl_pct"]),
                    "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                    "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                    "qqq_final_capital_usd": float(qqq_final),
                    "beats_qqq_flag": int(final > qqq_final),
                    "diagnostic_only_flag": int(spec["diagnostic_only_flag"]),
                    "return_tuned_flag": int(spec["return_tuned_flag"]),
                    "fixed_hold_or_timing_override_flag": int(spec["fixed_hold_or_timing_override_flag"]),
                    "label_used_in_assignment_flag": 0,
                    "return_used_in_assignment_flag": 0,
                }
            )
            for frame, bucket in [(accepted, accepted_rows), (allocation, allocation_rows), (curve, curve_rows), (sizing, sizing_rows)]:
                if not frame.empty:
                    enriched = frame.copy()
                    enriched["candidate_name"] = spec["candidate_name"]
                    enriched["split_scope"] = split_name
                    bucket.append(enriched)
    grid = pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)
    return (
        grid,
        pd.concat(accepted_rows, ignore_index=True) if accepted_rows else pd.DataFrame(),
        pd.concat(allocation_rows, ignore_index=True) if allocation_rows else pd.DataFrame(),
        pd.concat(curve_rows, ignore_index=True) if curve_rows else pd.DataFrame(),
        pd.concat(sizing_rows, ignore_index=True) if sizing_rows else pd.DataFrame(),
    )


def simulate_account(panel: pd.DataFrame, spec: pd.Series) -> tuple[dict[str, float], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if panel.empty:
        return empty_quality(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ordered = panel.sort_values(["entry_ts", "priority_rank", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    ordered["net_return_costed"] = pd.to_numeric(ordered["net_return_from_entry"], errors="coerce") - COST_BPS / 10000.0
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    allocation_rows: list[dict[str, object]] = []
    sizing_rows: list[dict[str, object]] = []
    curve_rows = [{"event_ts": ordered["entry_ts"].min(), "equity": equity, "drawdown_pct": 0.0, "event_type": "start"}]

    def close_positions_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still_open: list[dict[str, object]] = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= current_ts:
                equity += float(pos["capital"]) * float(pos["return"])
                peak = max(peak, equity)
                curve_rows.append(
                    {
                        "event_ts": pos["exit_ts"],
                        "equity": equity,
                        "drawdown_pct": (equity / max(peak, 1e-9) - 1.0) * 100.0,
                        "event_type": "close",
                    }
                )
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_positions_until(entry_ts)
        account_drawdown_pct = (equity / max(peak, 1e-9) - 1.0) * 100.0
        quality_score = entry_quality_score(row)
        dynamic_cap = relation_cap_for_row(row, spec, account_drawdown_pct)
        size_multiplier, sizing_reason = size_multiplier_for_row(row, spec, account_drawdown_pct, quality_score)
        if len(open_positions) >= MAX_POSITIONS:
            allocation_rows.append(allocation_record(row, 0, "max_positions_full", account_drawdown_pct, quality_score, dynamic_cap, size_multiplier))
            continue
        relation_count = sum(1 for pos in open_positions if str(pos.get("mechanism_relation_state", "")) == str(row.get("mechanism_relation_state", "")))
        if relation_count >= dynamic_cap:
            allocation_rows.append(allocation_record(row, 0, "active_relation_dynamic_cap", account_drawdown_pct, quality_score, dynamic_cap, size_multiplier))
            continue
        open_slots = MAX_POSITIONS - len(open_positions)
        ok, reason = passes_slot_hurdle(row, spec, open_slots, account_drawdown_pct, quality_score)
        if not ok:
            allocation_rows.append(allocation_record(row, 0, reason, account_drawdown_pct, quality_score, dynamic_cap, size_multiplier))
            continue
        capital = equity / float(MAX_POSITIONS) * size_multiplier
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_costed"],
                "theme_id": row.get("theme_id", ""),
                "mechanism_relation_state": row.get("mechanism_relation_state", ""),
            }
        )
        accepted = dict(row)
        accepted["entry_quality_score"] = quality_score
        accepted["active_relation_cap_at_entry"] = dynamic_cap
        accepted["account_drawdown_pct_at_entry"] = account_drawdown_pct
        accepted["size_multiplier"] = size_multiplier
        accepted["position_capital_fraction"] = capital
        accepted["sizing_reason"] = sizing_reason
        accepted_rows.append(accepted)
        allocation_rows.append(allocation_record(row, 1, "accepted", account_drawdown_pct, quality_score, dynamic_cap, size_multiplier))
        sizing_rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "symbol": row.get("symbol", ""),
                "entry_ts": row["entry_ts"],
                "theme_id": row.get("theme_id", ""),
                "mechanism_relation_state": row.get("mechanism_relation_state", ""),
                "entry_quality_score": quality_score,
                "account_drawdown_pct_at_entry": account_drawdown_pct,
                "size_multiplier": size_multiplier,
                "sizing_reason": sizing_reason,
            }
        )

    close_positions_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    allocation = pd.DataFrame(allocation_rows)
    curve = pd.DataFrame(curve_rows).sort_values("event_ts").reset_index(drop=True)
    sizing = pd.DataFrame(sizing_rows)
    if accepted.empty:
        return empty_quality(), accepted, allocation, curve, sizing
    returns = pd.to_numeric(accepted["net_return_costed"], errors="coerce")
    quality = {
        "capital_pnl_pct": float((equity - 1.0) * 100.0),
        "max_drawdown_pct": float(curve["drawdown_pct"].min() if not curve.empty else 0.0),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
    }
    return quality, accepted, allocation, curve, sizing


def relation_cap_for_row(row: dict[str, object], spec: pd.Series, account_drawdown_pct: float) -> int:
    mode = str(spec["active_relation_cap_mode"])
    if mode == "none":
        return 999
    if mode == "static3":
        return 3
    if mode in {"market_dynamic", "market_account_dynamic"}:
        cap = 3
        macro = str(row.get("macro_overall_state", ""))
        pressure = float_or_zero(row.get("macro_pressure_score", 0.0))
        market_score = float_or_zero(row.get("broad_market_score", 100.0))
        market_stress = float_or_zero(row.get("broad_market_stress", 0.0))
        if macro == "macro_hostile" or pressure >= 2.0 or market_score < 50.0 or market_stress >= 40.0:
            cap = 2
        if mode == "market_account_dynamic":
            if account_drawdown_pct <= -10.0:
                cap = min(cap, 2)
            if account_drawdown_pct <= -20.0:
                cap = min(cap, 1)
        return cap
    return 3


def passes_slot_hurdle(row: dict[str, object], spec: pd.Series, open_slots: int, account_drawdown_pct: float, quality_score: float) -> tuple[bool, str]:
    mode = str(spec["slot_hurdle_mode"])
    if mode == "none":
        return True, "accepted"
    hurdle = 5.0
    if mode == "scarce_slot_quality":
        if open_slots <= 1 and quality_score < hurdle:
            return False, "scarce_slot_quality_hurdle"
        return True, "accepted"
    if mode == "weak_scarce_slot":
        if open_slots <= 1 and quality_score < 3.5:
            return False, "weak_scarce_slot_hurdle"
        return True, "accepted"
    if mode == "drawdown_hurdle":
        if account_drawdown_pct <= -10.0 and quality_score < 5.5:
            return False, "drawdown_quality_hurdle"
        return True, "accepted"
    return True, "accepted"


def size_multiplier_for_row(row: dict[str, object], spec: pd.Series, account_drawdown_pct: float, quality_score: float) -> tuple[float, str]:
    mode = str(spec["sizing_mode"])
    if mode == "equal":
        return 1.0, "equal"
    multiplier = 1.0
    reasons: list[str] = []
    macro = str(row.get("macro_overall_state", ""))
    pressure = float_or_zero(row.get("macro_pressure_score", 0.0))
    market_score = float_or_zero(row.get("broad_market_score", 100.0))
    intraday_extension = float_or_zero(row.get("intraday_ret_from_open", 0.0))
    range_pos = float_or_zero(row.get("range_pos", 0.0))
    volume_ratio = float_or_zero(row.get("volume_ratio_prev", 1.0))
    if mode in {"risk_proxy_scaled", "drawdown_scaled"}:
        if macro == "macro_hostile" or pressure >= 2.0 or market_score < 50.0:
            multiplier *= 0.75
            reasons.append("macro_or_market_stress")
        if intraday_extension >= 0.06:
            multiplier *= 0.50
            reasons.append("extreme_intraday_extension")
        elif intraday_extension >= 0.03:
            multiplier *= 0.75
            reasons.append("high_intraday_extension")
        if range_pos >= 0.98:
            multiplier *= 0.85
            reasons.append("near_intraday_range_top")
        if volume_ratio < 0.70:
            multiplier *= 0.85
            reasons.append("thin_prior_volume")
    if mode == "contextual_risk_scaled":
        relation = str(row.get("mechanism_relation_state", ""))
        weaker_relation = relation in {"company_quality_price_confirmed", "sparse_mechanism_cell", "company_positive_needs_confirmation"}
        if weaker_relation and (macro == "macro_hostile" or pressure >= 2.0 or market_score < 50.0):
            multiplier *= 0.80
            reasons.append("weak_relation_with_macro_or_market_stress")
        if weaker_relation and intraday_extension >= 0.04:
            multiplier *= 0.80
            reasons.append("weak_relation_with_extension")
        if quality_score < 3.5:
            multiplier *= 0.80
            reasons.append("low_entry_quality")
        if relation == "mechanism_reinforcing_company_positive" and quality_score >= 6.0:
            reasons.append("full_size_reinforcing_quality")
    if mode == "drawdown_scaled":
        if account_drawdown_pct <= -20.0:
            multiplier *= 0.50
            reasons.append("deep_account_drawdown")
        elif account_drawdown_pct <= -10.0:
            multiplier *= 0.75
            reasons.append("account_drawdown")
    if quality_score >= 7.0 and not reasons:
        reasons.append("full_size_high_quality")
    multiplier = max(0.30, min(1.0, multiplier))
    return float(multiplier), "+".join(reasons) if reasons else "full_size"


def entry_quality_score(row: dict[str, object]) -> float:
    state = str(row.get("mechanism_relation_state", ""))
    catalyst = str(row.get("catalyst_quality_tier", ""))
    price = str(row.get("price_acceptance_state", ""))
    macro = str(row.get("macro_overall_state", ""))
    score = {
        "mechanism_reinforcing_company_positive": 4.0,
        "mechanism_offsetting_company_positive": 3.0,
        "company_positive_needs_confirmation": 2.0,
        "company_quality_price_confirmed": 1.0,
        "sparse_mechanism_cell": 0.0,
    }.get(state, 1.0)
    score += {
        "very_strong_catalyst": 2.0,
        "strong_catalyst": 1.5,
        "medium_catalyst": 0.75,
        "weak_catalyst": 0.0,
    }.get(catalyst, 0.0)
    score += {"price_acceptance_strong": 1.0, "price_acceptance_accepted": 0.5}.get(price, 0.0)
    score += float_or_zero(row.get("mechanism_support_count", 0.0)) * 0.5
    score -= float_or_zero(row.get("mechanism_pressure_count", 0.0)) * 0.75
    if macro == "macro_supportive":
        score += 0.5
    elif macro == "macro_hostile":
        score -= 1.0
    if float_or_zero(row.get("intraday_ret_from_open", 0.0)) >= 0.04:
        score -= 0.5
    if float_or_zero(row.get("volume_ratio_prev", 1.0)) < 0.70:
        score -= 0.5
    return float(score)


def allocation_record(row: dict[str, object], accepted_flag: int, reason: str, account_drawdown_pct: float, quality_score: float, relation_cap: int, size_multiplier: float) -> dict[str, object]:
    return {
        "lifecycle_id": row.get("lifecycle_id", ""),
        "symbol": row.get("symbol", ""),
        "entry_ts": row.get("entry_ts", ""),
        "simulated_exit_ts": row.get("simulated_exit_ts", ""),
        "split_name": row.get("split_name", ""),
        "theme_id": row.get("theme_id", ""),
        "mechanism_relation_state": row.get("mechanism_relation_state", ""),
        "macro_overall_state": row.get("macro_overall_state", ""),
        "priority_rank": row.get("priority_rank", ""),
        "accepted_flag": accepted_flag,
        "allocation_reason": reason,
        "account_drawdown_pct_at_entry": account_drawdown_pct,
        "entry_quality_score": quality_score,
        "active_relation_cap_at_entry": relation_cap,
        "size_multiplier": size_multiplier,
        "net_return_costed": row.get("net_return_costed", ""),
    }


def build_promotion_report(grid: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    baseline = pivot_candidate(grid, BASELINE_CANDIDATE)
    rows = []
    for candidate_name in specs["candidate_name"]:
        metrics = pivot_candidate(grid, candidate_name)
        spec = specs[specs["candidate_name"].eq(candidate_name)].iloc[0]
        beats_all = int(metrics["all_final_capital_usd"] > baseline["all_final_capital_usd"])
        dd_ok = int(metrics["all_max_drawdown_pct"] >= baseline["all_max_drawdown_pct"])
        validation_up = int(metrics["validation_final_capital_usd"] > baseline["validation_final_capital_usd"])
        recent_up = int(metrics["recent_oos_final_capital_usd"] > baseline["recent_oos_final_capital_usd"])
        validation_dd_ok = int(metrics["validation_max_drawdown_pct"] >= baseline["validation_max_drawdown_pct"])
        recent_dd_ok = int(metrics["recent_oos_max_drawdown_pct"] >= baseline["recent_oos_max_drawdown_pct"])
        allowed = int(int(spec["diagnostic_only_flag"]) == 0 and int(spec["return_tuned_flag"]) == 0 and int(spec["fixed_hold_or_timing_override_flag"]) == 0)
        promotion = int(candidate_name != BASELINE_CANDIDATE and beats_all and dd_ok and validation_up and recent_up and validation_dd_ok and recent_dd_ok and allowed)
        rows.append(
            {
                "candidate_name": candidate_name,
                **metrics,
                "beats_all_task639_flag": beats_all,
                "all_drawdown_not_worse_flag": dd_ok,
                "validation_improves_task639_flag": validation_up,
                "recent_oos_improves_task639_flag": recent_up,
                "validation_drawdown_not_worse_flag": validation_dd_ok,
                "recent_oos_drawdown_not_worse_flag": recent_dd_ok,
                "promotion_allowed_flag": allowed,
                "promotion_candidate_flag": promotion,
                "failure_reason": failure_reason(promotion, allowed, beats_all, dd_ok, validation_up, recent_up, validation_dd_ok, recent_dd_ok),
            }
        )
    return pd.DataFrame(rows).sort_values(["promotion_candidate_flag", "all_final_capital_usd"], ascending=[False, False]).reset_index(drop=True)


def pivot_candidate(grid: pd.DataFrame, candidate_name: str) -> dict[str, float]:
    rows = grid[grid["candidate_name"].eq(candidate_name)]
    out: dict[str, float] = {}
    for _, row in rows.iterrows():
        split = str(row["split_name"])
        for column in ["final_capital_usd", "max_drawdown_pct", "accepted_trade_count", "avg_size_multiplier", "entry_reduce_failure_rate", "beats_qqq_flag"]:
            out[f"{split}_{column}"] = float(row[column])
    return out


def failure_reason(promotion: int, allowed: int, beats_all: int, dd_ok: int, validation_up: int, recent_up: int, validation_dd_ok: int, recent_dd_ok: int) -> str:
    if promotion:
        return "passes_all_dynamic_risk_gates"
    if not allowed:
        return "diagnostic_or_return_tuned_not_promotion_eligible"
    if not beats_all:
        return "full_period_return_not_better"
    if not dd_ok:
        return "full_period_drawdown_worse"
    if not validation_up or not recent_up:
        return "validation_or_recent_oos_not_better"
    if not validation_dd_ok or not recent_dd_ok:
        return "validation_or_recent_oos_drawdown_worse"
    return "other_gate_failure"


def build_mdd_windows(equity_curve: pd.DataFrame) -> pd.DataFrame:
    if equity_curve.empty:
        return pd.DataFrame()
    rows = []
    for (candidate, split), group in equity_curve.groupby(["candidate_name", "split_scope"], dropna=False):
        g = group.sort_values("event_ts").copy()
        if g.empty:
            continue
        trough = g.loc[pd.to_numeric(g["drawdown_pct"], errors="coerce").idxmin()]
        before = g[g["event_ts"].le(trough["event_ts"])].copy()
        peak = before.loc[pd.to_numeric(before["equity"], errors="coerce").idxmax()]
        rows.append(
            {
                "candidate_name": candidate,
                "split_scope": split,
                "mdd_peak_ts": peak["event_ts"],
                "mdd_trough_ts": trough["event_ts"],
                "peak_equity": float(peak["equity"]),
                "trough_equity": float(trough["equity"]),
                "max_drawdown_pct": float(trough["drawdown_pct"]),
            }
        )
    return pd.DataFrame(rows).sort_values(["split_scope", "max_drawdown_pct"]).reset_index(drop=True)


def build_mdd_interval_audit(accepted: pd.DataFrame, mdd_windows: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty or mdd_windows.empty:
        return pd.DataFrame()
    rows = []
    all_accepted = accepted[accepted["split_scope"].astype(str).eq("all")].copy()
    all_windows = mdd_windows[mdd_windows["split_scope"].astype(str).eq("all")].copy()
    for _, window in all_windows.iterrows():
        candidate = str(window["candidate_name"])
        group = all_accepted[all_accepted["candidate_name"].astype(str).eq(candidate)].copy()
        peak = pd.Timestamp(window["mdd_peak_ts"])
        trough = pd.Timestamp(window["mdd_trough_ts"])
        group["entry_ts"] = pd.to_datetime(group["entry_ts"], utc=True)
        group["simulated_exit_ts"] = pd.to_datetime(group["simulated_exit_ts"], utc=True)
        active = group[(group["entry_ts"].le(trough)) & (group["simulated_exit_ts"].ge(peak))].copy()
        if active.empty:
            rows.append({"candidate_name": candidate, "audit_group": "none", "group_value": "no_active_trades", "active_trade_count": 0})
            continue
        for key in ["mechanism_relation_state", "theme_id", "symbol"]:
            for value, sub in active.groupby(key, dropna=False):
                rows.append(
                    {
                        "candidate_name": candidate,
                        "audit_group": key,
                        "group_value": value,
                        "active_trade_count": int(len(sub)),
                        "avg_return_costed_pct": float(pd.to_numeric(sub["net_return_costed"], errors="coerce").mean() * 100.0),
                        "sum_position_capital_fraction": float(pd.to_numeric(sub["position_capital_fraction"], errors="coerce").sum()),
                        "avg_size_multiplier": float(pd.to_numeric(sub["size_multiplier"], errors="coerce").mean()),
                    }
                )
    return pd.DataFrame(rows).sort_values(["candidate_name", "audit_group", "active_trade_count"], ascending=[True, True, False]).reset_index(drop=True)


def build_decision(promotion: pd.DataFrame) -> pd.DataFrame:
    baseline = promotion[promotion["candidate_name"].eq(BASELINE_CANDIDATE)].iloc[0]
    best = promotion.sort_values("all_final_capital_usd", ascending=False).iloc[0]
    best_promotable = promotion[promotion["promotion_allowed_flag"].eq(1)].sort_values("all_final_capital_usd", ascending=False).iloc[0]
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    decision = "DYNAMIC_RISK_TESTED_NO_PROMOTION_CANDIDATE"
    if promotion_count > 0:
        decision = "DYNAMIC_RISK_PROMOTION_CANDIDATE_FOUND_NOT_ACCEPTED"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "baseline_final_capital_usd": float(baseline["all_final_capital_usd"]),
                "baseline_max_drawdown_pct": float(baseline["all_max_drawdown_pct"]),
                "best_candidate_name": best["candidate_name"],
                "best_candidate_final_capital_usd": float(best["all_final_capital_usd"]),
                "best_candidate_max_drawdown_pct": float(best["all_max_drawdown_pct"]),
                "best_promotion_allowed_candidate_name": best_promotable["candidate_name"],
                "best_promotion_allowed_final_capital_usd": float(best_promotable["all_final_capital_usd"]),
                "best_promotion_allowed_max_drawdown_pct": float(best_promotable["all_max_drawdown_pct"]),
                "promotion_candidate_count": promotion_count,
                "trading_promotion_pass_flag": 0,
                "next_action": "If no candidate passes, audit active_relation_cap3 MDD exposures and design drawdown-aware sizing or exit-risk controls.",
            }
        ]
    )


def build_pass_fail(specs: pd.DataFrame, promotion: pd.DataFrame, allocation: pd.DataFrame, sizing_audit: pd.DataFrame, mdd_audit: pd.DataFrame) -> pd.DataFrame:
    fixed = int(pd.to_numeric(specs["fixed_hold_or_timing_override_flag"], errors="coerce").sum())
    return_tuned_promoted = int(
        promotion[promotion["promotion_candidate_flag"].eq(1)]["candidate_name"]
        .isin(specs[specs["return_tuned_flag"].eq(1)]["candidate_name"])
        .sum()
    )
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    return pd.DataFrame(
        [
            {"gate": "no_fixed_hold_or_timing_override", "pass_flag": int(fixed == 0), "observed_value": f"violations={fixed}", "required_value": "preserve Task639 entry timing and exits"},
            {"gate": "dynamic_cap_tested", "pass_flag": int(specs["active_relation_cap_mode"].astype(str).str.contains("dynamic").any()), "observed_value": ",".join(sorted(set(specs["active_relation_cap_mode"].astype(str)))), "required_value": "dynamic relation cap candidates exist"},
            {"gate": "slot_hurdle_tested", "pass_flag": int(specs["slot_hurdle_mode"].astype(str).ne("none").any()), "observed_value": ",".join(sorted(set(specs["slot_hurdle_mode"].astype(str)))), "required_value": "slot hurdle candidates exist"},
            {"gate": "sizing_tested", "pass_flag": int(specs["sizing_mode"].astype(str).ne("equal").any()), "observed_value": ",".join(sorted(set(specs["sizing_mode"].astype(str)))), "required_value": "risk proxy sizing candidates exist"},
            {"gate": "allocation_audit_built", "pass_flag": int(not allocation.empty), "observed_value": f"rows={len(allocation)}", "required_value": "allocation panel exists"},
            {"gate": "sizing_audit_built", "pass_flag": int(not sizing_audit.empty), "observed_value": f"rows={len(sizing_audit)}", "required_value": "sizing audit exists"},
            {"gate": "mdd_audit_built", "pass_flag": int(not mdd_audit.empty), "observed_value": f"rows={len(mdd_audit)}", "required_value": "MDD interval audit exists"},
            {"gate": "no_return_tuned_promotion", "pass_flag": int(return_tuned_promoted == 0), "observed_value": f"return_tuned_promoted={return_tuned_promoted}", "required_value": "return-tuned candidate cannot promote"},
            {"gate": "promotion_candidate_found", "pass_flag": int(promotion_count > 0), "observed_value": f"promotion_candidates={promotion_count}", "required_value": "candidate improves return drawdown validation and recent OOS"},
            {"gate": "strategy_accepted", "pass_flag": 0, "observed_value": "research diagnostic only", "required_value": "requires accepted strategy gates and live readiness"},
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    grid: pd.DataFrame,
    promotion: pd.DataFrame,
    mdd_windows: pd.DataFrame,
    mdd_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task667 Dynamic Risk Development",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Baseline: `${float(d['baseline_final_capital_usd']):.2f}`, MDD `{float(d['baseline_max_drawdown_pct']):.2f}%`.",
        f"- Best candidate: `{d['best_candidate_name']}` = `${float(d['best_candidate_final_capital_usd']):.2f}`, MDD `{float(d['best_candidate_max_drawdown_pct']):.2f}%`.",
        f"- Best promotion-allowed candidate: `{d['best_promotion_allowed_candidate_name']}` = `${float(d['best_promotion_allowed_final_capital_usd']):.2f}`, MDD `{float(d['best_promotion_allowed_max_drawdown_pct']):.2f}%`.",
        f"- Promotion candidates: `{int(d['promotion_candidate_count'])}`.",
        "",
        "## Quant Expert Report",
        "",
        "Task667 tests dynamic relation caps, scarce-slot admission hurdles, and risk-proxy sizing while preserving Task639 entry timing and exits.",
        "",
        "### Candidate Grid",
        "",
        table(grid),
        "",
        "### Promotion Report",
        "",
        table(promotion),
        "",
        "### MDD Windows",
        "",
        table(mdd_windows),
        "",
        "### MDD Interval Audit",
        "",
        table(mdd_audit),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "이번 작업은 active relation cap3를 더 똑똑하게 만들 수 있는지 본 테스트입니다.",
        "",
        "시장 상태가 안 좋거나 계좌가 이미 맞고 있을 때 더 작게 들어가고, 마지막 slot은 더 까다롭게 쓰게 했습니다.",
        "",
        "수익과 낙폭이 동시에 좋아져야 승격입니다. 하나만 좋아지면 연구용입니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `task667_candidate_specs.csv`",
        "- `task667_candidate_grid.csv`",
        "- `task667_accepted_trades.csv`",
        "- `task667_allocation_panel.csv`",
        "- `task667_equity_curve.csv`",
        "- `task667_sizing_audit.csv`",
        "- `task667_promotion_report.csv`",
        "- `task667_mdd_windows.csv`",
        "- `task667_mdd_interval_audit.csv`",
        "- `task667_promotion_blocker_report.md`",
        "- `task_667_gpt_review_packet.md`",
        "- `task_667_gpt_review_response.md`",
        "- `task_667_decision.csv`",
        "- `task_667_pass_fail_matrix.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_667_dynamic_risk_development.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def empty_quality() -> dict[str, float]:
    return {"capital_pnl_pct": 0.0, "max_drawdown_pct": 0.0, "entry_reduce_failure_rate": 0.0}


def float_or_zero(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    clipped = df.head(max_rows)
    lines = ["| " + " | ".join(map(str, clipped.columns)) + " |", "| " + " | ".join(["---"] * len(clipped.columns)) + " |"]
    for _, row in clipped.iterrows():
        lines.append("| " + " | ".join(cell(row.get(c, "")) for c in clipped.columns) + " |")
    return "\n".join(lines)


def cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "/").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    result = build_task667_dynamic_risk_development(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best={decision['best_candidate_name']} "
        f"best_allowed={decision['best_promotion_allowed_candidate_name']} "
        f"promotion={int(decision['promotion_candidate_count'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
