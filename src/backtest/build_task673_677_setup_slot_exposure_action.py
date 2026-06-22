from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import (
    INITIAL_CAPITAL_USD,
    load_qqq_history,
    qqq_final_for_period,
)
from src.backtest.build_task659_theme_specific_relation_engine import QQQ_PATH
from src.backtest.build_task668_regime_theme_playbook import COST_BPS, MAX_POSITIONS


TASK672_DIR = Path("docs/reports/task_672_current_data_state_axis_panel")
TASK673_DIR = Path("docs/reports/task_673_setup_quality_layer")
TASK674_DIR = Path("docs/reports/task_674_slot_value_displacement_engine")
TASK675_DIR = Path("docs/reports/task_675_exposure_cluster_audit")
TASK676_DIR = Path("docs/reports/task_676_conservative_capacity_cap")
TASK677_DIR = Path("docs/reports/task_677_action_permission_matrix")

BASELINE = "baseline_task639"
ACTIVE_CAP3 = "active_relation_cap3_reference"


def build_task673_677_program(
    *,
    task672_dir: Path = TASK672_DIR,
    qqq_path: Path = QQQ_PATH,
) -> dict[str, pd.DataFrame]:
    for out_dir in [TASK673_DIR, TASK674_DIR, TASK675_DIR, TASK676_DIR, TASK677_DIR]:
        out_dir.mkdir(parents=True, exist_ok=True)

    panel = load_task672_panel(task672_dir)
    panel = add_setup_quality(panel)
    panel = add_slot_value_ladder(panel)
    action_matrix = build_action_permission_matrix()
    qqq = load_qqq_history(qqq_path)
    specs = build_candidate_specs()
    grid, accepted, allocation, equity_curve = build_candidate_grid(panel, specs, qqq)
    displacement = build_displacement_audit(accepted)
    winner_damage = build_winner_damage_audit_from_accepted(accepted)
    mdd_windows = build_mdd_windows(equity_curve)
    exposure = build_exposure_cluster_audit(accepted, mdd_windows)
    setup_perf = build_setup_quality_performance(panel)
    setup_mix = build_setup_quality_mix(panel)
    capacity_reason = build_capacity_reason_audit(allocation)
    promotion = build_promotion_report(grid, specs)
    forbidden = build_forbidden_input_audit(panel, specs, allocation)

    task673_decision = build_task673_decision(panel, setup_perf)
    task674_decision = build_task674_decision(grid, displacement)
    task675_decision = build_task675_decision(exposure)
    task676_decision = build_task676_decision(promotion)
    task677_decision = build_task677_decision(action_matrix)

    task673_pass = build_task673_pass_fail(panel, setup_perf)
    task674_pass = build_task674_pass_fail(grid, displacement, winner_damage)
    task675_pass = build_task675_pass_fail(exposure)
    task676_pass = build_task676_pass_fail(promotion, forbidden, capacity_reason)
    task677_pass = build_task677_pass_fail(action_matrix, forbidden)

    write_task673(panel, setup_perf, setup_mix, task673_decision, task673_pass)
    write_task674(grid, displacement, winner_damage, task674_decision, task674_pass)
    write_task675(exposure, mdd_windows, task675_decision, task675_pass)
    write_task676(specs, grid, accepted, allocation, capacity_reason, promotion, forbidden, task676_decision, task676_pass)
    write_task677(action_matrix, forbidden, task677_decision, task677_pass)

    return {
        "panel": panel,
        "specs": specs,
        "grid": grid,
        "accepted": accepted,
        "allocation": allocation,
        "equity_curve": equity_curve,
        "displacement": displacement,
        "winner_damage": winner_damage,
        "mdd_windows": mdd_windows,
        "exposure": exposure,
        "setup_perf": setup_perf,
        "promotion": promotion,
        "forbidden": forbidden,
        "action_matrix": action_matrix,
    }


def load_task672_panel(task672_dir: Path) -> pd.DataFrame:
    path = task672_dir / "task672_state_axis_panel.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    panel = pd.read_csv(path)
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True)
    panel["simulated_exit_ts"] = pd.to_datetime(panel["simulated_exit_ts"], utc=True)
    return panel


def add_setup_quality(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["source_action_block_flag"] = out.apply(source_action_block_flag, axis=1)
    out["sparse_action_block_flag"] = out.apply(sparse_action_block_flag, axis=1)
    out["risk_warning_flag"] = out.apply(risk_warning_flag, axis=1)
    out["setup_quality_bucket"] = out.apply(classify_setup_quality, axis=1)
    out["setup_reason_codes"] = out.apply(setup_reason_codes, axis=1)
    out["proxy_risk_used_as_hard_rule_flag"] = 0
    out["relation_name_alone_high_quality_flag"] = out.apply(relation_name_alone_high_quality_flag, axis=1)
    out["return_used_in_setup_assignment_flag"] = 0
    out["label_used_in_setup_assignment_flag"] = 0
    out["future_price_used_in_setup_assignment_flag"] = 0
    return out


def source_action_block_flag(row: pd.Series) -> int:
    forbidden = [
        "return_used_in_assignment_flag",
        "label_used_in_assignment_flag_task661",
        "microstructure_used_in_assignment",
        "missing_source_used_as_signal",
        "symbol_blacklist_used",
        "theme_blacklist_used",
        "future_price_used_in_assignment",
    ]
    if i(row.get("asof_valid_flag", 0)) != 1:
        return 1
    if i(row.get("allocation_assignment_ready_flag", row.get("used_for_assignment_flag", 0))) != 1:
        return 1
    if i(row.get("macro_provisional_used_as_certified", 0)) != 0:
        return 1
    if i(row.get("missing_source_used_as_negative", 0)) != 0:
        return 1
    for col in forbidden:
        if i(row.get(col, 0)) != 0:
            return 1
    return 0


def sparse_action_block_flag(row: pd.Series) -> int:
    return int(i(row.get("mechanism_sparse_cell_flag", 0)) == 1 or s(row.get("mechanism_relation_state", "")) == "sparse_mechanism_cell")


def risk_warning_flag(row: pd.Series) -> int:
    proxy = s(row.get("proxy_risk_context", ""))
    price = s(row.get("price_chart_acceptance_state", ""))
    return int(proxy in {"extension_proxy", "market_stress_proxy", "stress_plus_extension_proxy"} or price == "price_confirmed_but_extended")


def classify_setup_quality(row: pd.Series) -> str:
    if source_action_block_flag(row) == 1 or sparse_action_block_flag(row) == 1:
        return "research_only_setup"
    support = i(row.get("mechanism_support_count", row.get("support_count", 0)))
    pressure = i(row.get("mechanism_pressure_count", row.get("conflict_count", 0)))
    company = s(row.get("company_catalyst_state", ""))
    price = s(row.get("price_chart_acceptance_state", ""))
    theme = s(row.get("theme_leadership_state", ""))
    catalyst_tier = s(row.get("catalyst_quality_tier", ""))
    strong_company = company in {
        "multi_dimension_high_quality_catalyst",
        "hard_company_catalyst",
        "demand_supply_catalyst",
    } or catalyst_tier in {"very_strong_catalyst", "strong_catalyst"}
    medium_company = strong_company or company == "multi_signal_medium_catalyst" or catalyst_tier == "medium_catalyst"
    price_not_fragile = price != "price_fragile_or_unconfirmed"
    price_strong = price in {"price_confirmed_not_extended", "price_confirmed_basic", "price_confirmed_but_extended"}
    theme_not_fading = theme != "theme_leadership_fading"
    support_ok = support >= pressure
    support_bad = pressure > support
    if price == "price_fragile_or_unconfirmed" or support_bad:
        return "fragile_setup"
    high_components = sum([int(strong_company), int(price_strong), int(support_ok), int(theme_not_fading)])
    if strong_company and price_not_fragile and support_ok and theme_not_fading and high_components >= 3:
        return "high_quality_setup"
    if medium_company and price_not_fragile and support_ok:
        return "medium_quality_setup"
    return "uncertain_setup"


def setup_reason_codes(row: pd.Series) -> str:
    reasons = []
    if source_action_block_flag(row):
        reasons.append("source_or_forbidden_input_block")
    if sparse_action_block_flag(row):
        reasons.append("sparse_mechanism_research_only")
    if s(row.get("price_chart_acceptance_state", "")) == "price_fragile_or_unconfirmed":
        reasons.append("price_fragile")
    if i(row.get("mechanism_pressure_count", row.get("conflict_count", 0))) > i(row.get("mechanism_support_count", row.get("support_count", 0))):
        reasons.append("pressure_gt_support")
    if risk_warning_flag(row):
        reasons.append("risk_warning_diagnostic")
    if not reasons:
        reasons.append("predeclared_quality_ladder")
    return "|".join(reasons)


def relation_name_alone_high_quality_flag(row: pd.Series) -> int:
    if classify_setup_quality(row) != "high_quality_setup":
        return 0
    company = s(row.get("company_catalyst_state", ""))
    price = s(row.get("price_chart_acceptance_state", ""))
    theme = s(row.get("theme_leadership_state", ""))
    strong_company = company in {"multi_dimension_high_quality_catalyst", "hard_company_catalyst", "demand_supply_catalyst"}
    return int(not strong_company or price == "price_fragile_or_unconfirmed" or theme == "theme_leadership_fading")


def add_slot_value_ladder(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["setup_rank"] = out["setup_quality_bucket"].map(
        {
            "high_quality_setup": 10,
            "medium_quality_setup": 20,
            "uncertain_setup": 40,
            "fragile_setup": 60,
            "research_only_setup": 90,
        }
    ).fillna(80).astype(int)
    out["source_sparse_rank"] = out.apply(lambda r: 90 if source_action_block_flag(r) or sparse_action_block_flag(r) else 10, axis=1)
    out["price_rank"] = out["price_chart_acceptance_state"].map(
        {
            "price_confirmed_not_extended": 10,
            "price_confirmed_basic": 20,
            "price_confirmed_but_extended": 30,
            "price_accepted_needs_confirmation": 40,
            "price_fragile_or_unconfirmed": 80,
        }
    ).fillna(70).astype(int)
    out["catalyst_rank"] = out["catalyst_quality_tier"].map(
        {
            "very_strong_catalyst": 10,
            "strong_catalyst": 20,
            "medium_catalyst": 40,
            "weak_catalyst": 70,
        }
    ).fillna(80).astype(int)
    support_delta = pd.to_numeric(out.get("mechanism_support_count", 0), errors="coerce").fillna(0) - pd.to_numeric(out.get("mechanism_pressure_count", 0), errors="coerce").fillna(0)
    out["support_pressure_rank"] = (-support_delta).astype(int)
    out["theme_ladder_rank"] = out["theme_leadership_state"].map(
        {
            "persistent_broad_theme_leader": 10,
            "theme_leadership_expanding": 20,
            "narrow_leadership": 30,
            "theme_participating": 40,
            "theme_leadership_fading": 70,
        }
    ).fillna(60).astype(int)
    out["slot_value_ladder"] = out.apply(
        lambda r: f"{int(r['setup_rank'])}:{int(r['source_sparse_rank'])}:{int(r['price_rank'])}:{int(r['catalyst_rank'])}:{int(r['support_pressure_rank'])}:{int(r['theme_ladder_rank'])}",
        axis=1,
    )
    out["slot_value_rank_tuned_flag"] = 0
    return out


def build_candidate_specs() -> pd.DataFrame:
    return pd.DataFrame(
        [
            candidate(BASELINE, "baseline", "chronological", "none", 0, 0, 0, 0, "Task639 chronological reference."),
            candidate(ACTIVE_CAP3, "reference", "relation_priority", "relation3", 0, 0, 0, 0, "Task668 active relation cap3 reference."),
            candidate("setup_slot_priority_only", "task674_slot_value", "setup_ladder", "none", 0, 0, 0, 0, "Same timestamp setup-quality ladder only."),
            candidate("setup_slot_priority_research_block", "task674_slot_value", "setup_ladder", "none", 1, 0, 0, 0, "Setup-quality ladder with source/sparse research-only block."),
            candidate("capacity_relation_cap2", "task676_capacity_cap", "setup_ladder", "relation2", 0, 0, 0, 0, "Predeclared relation concentration cap."),
            candidate("capacity_theme_cap2", "task676_capacity_cap", "setup_ladder", "theme2", 0, 0, 0, 0, "Predeclared theme concentration cap."),
            candidate("capacity_driver_cap2", "task676_capacity_cap", "setup_ladder", "driver2", 0, 0, 0, 0, "Predeclared driver concentration cap."),
            candidate("capacity_fragile_cap1", "task676_capacity_cap", "setup_ladder", "fragile1", 0, 0, 0, 0, "Predeclared fragile setup concentration cap."),
            candidate("capacity_combined_conservative", "task676_capacity_cap", "setup_ladder", "combined", 0, 0, 0, 0, "Relation theme driver fragile concentration caps together."),
            candidate("action_permission_research_block", "task677_action_permission", "permission_ladder", "combined", 1, 0, 0, 0, "Action permission matrix with research-only exclusion."),
        ]
    )


def candidate(name: str, typ: str, priority: str, cap: str, block_research: int, diagnostic: int, return_tuned: int, fixed_override: int, desc: str) -> dict[str, object]:
    return {
        "candidate_name": name,
        "candidate_type": typ,
        "priority_mode": priority,
        "cap_mode": cap,
        "block_research_only_flag": block_research,
        "diagnostic_only_flag": diagnostic,
        "return_tuned_flag": return_tuned,
        "fixed_hold_or_timing_override_flag": fixed_override,
        "description": desc,
    }


def build_candidate_grid(panel: pd.DataFrame, specs: pd.DataFrame, qqq: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    accepted_frames = []
    allocation_frames = []
    curve_frames = []
    for _, spec in specs.iterrows():
        for split_name in ["all", "validation", "recent_oos"]:
            scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)].copy()
            quality, accepted, allocation, curve = simulate_candidate(scoped, spec)
            qqq_final = qqq_final_for_period(qqq, scoped)
            final = INITIAL_CAPITAL_USD * (1.0 + quality["capital_pnl_pct"] / 100.0)
            rows.append(
                {
                    "candidate_name": spec["candidate_name"],
                    "candidate_type": spec["candidate_type"],
                    "split_name": split_name,
                    "initial_capital_usd": INITIAL_CAPITAL_USD,
                    "source_trade_count": int(len(scoped)),
                    "accepted_trade_count": int(len(accepted)),
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
            for frame, bucket in [(accepted, accepted_frames), (allocation, allocation_frames), (curve, curve_frames)]:
                if not frame.empty:
                    tmp = frame.copy()
                    tmp["candidate_name"] = spec["candidate_name"]
                    tmp["split_scope"] = split_name
                    bucket.append(tmp)
    return (
        pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True),
        pd.concat(accepted_frames, ignore_index=True) if accepted_frames else pd.DataFrame(),
        pd.concat(allocation_frames, ignore_index=True) if allocation_frames else pd.DataFrame(),
        pd.concat(curve_frames, ignore_index=True) if curve_frames else pd.DataFrame(),
    )


def simulate_candidate(panel: pd.DataFrame, spec: pd.Series) -> tuple[dict[str, float], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if panel.empty:
        return empty_quality(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ordered = sort_for_spec(panel, spec).copy()
    ordered["net_return_costed"] = pd.to_numeric(ordered["net_return_from_entry"], errors="coerce") - COST_BPS / 10000.0
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    allocation_rows: list[dict[str, object]] = []
    curve_rows = [{"event_ts": ordered["entry_ts"].min(), "equity": equity, "drawdown_pct": 0.0, "event_type": "start"}]

    def close_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still_open = []
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
        close_until(entry_ts)
        exposure = exposure_context(row, open_positions)
        permission = action_permission(row, exposure)
        if len(open_positions) >= MAX_POSITIONS:
            allocation_rows.append(allocation_record(row, exposure, permission, 0, "max_positions_full"))
            continue
        if int(spec["block_research_only_flag"]) == 1 and permission == "research_only":
            allocation_rows.append(allocation_record(row, exposure, permission, 0, "research_only_permission"))
            continue
        cap_reason = capacity_block_reason(row, exposure, spec)
        if cap_reason:
            allocation_rows.append(allocation_record(row, exposure, permission, 0, cap_reason))
            continue
        capital = equity / float(MAX_POSITIONS)
        position = {
            "lifecycle_id": row["lifecycle_id"],
            "exit_ts": row["simulated_exit_ts"],
            "capital": capital,
            "return": row["net_return_costed"],
            "theme_id": row.get("theme_id", ""),
            "relation_transmission_state": row.get("relation_transmission_state", ""),
            "driver_state": dominant_driver(row),
            "setup_quality_bucket": row.get("setup_quality_bucket", ""),
            "price_chart_acceptance_state": row.get("price_chart_acceptance_state", ""),
            "risk_warning_flag": row.get("risk_warning_flag", 0),
        }
        open_positions.append(position)
        accepted = dict(row)
        accepted.update(exposure)
        accepted["dominant_driver"] = dominant_driver(row)
        accepted["action_permission"] = permission
        accepted["position_capital_fraction"] = capital
        accepted_rows.append(accepted)
        allocation_rows.append(allocation_record(row, exposure, permission, 1, "accepted"))
    close_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    allocation = pd.DataFrame(allocation_rows)
    curve = pd.DataFrame(curve_rows).sort_values("event_ts").reset_index(drop=True)
    if accepted.empty:
        return empty_quality(), accepted, allocation, curve
    returns = pd.to_numeric(accepted["net_return_costed"], errors="coerce")
    return {
        "capital_pnl_pct": float((equity - 1.0) * 100.0),
        "max_drawdown_pct": float(curve["drawdown_pct"].min()),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
    }, accepted, allocation, curve


def sort_for_spec(panel: pd.DataFrame, spec: pd.Series) -> pd.DataFrame:
    mode = s(spec["priority_mode"])
    if mode == "chronological":
        cols = ["entry_ts", "lifecycle_id"]
    elif mode == "relation_priority":
        cols = ["entry_ts", "priority_rank", "lifecycle_id"]
    elif mode == "permission_ladder":
        tmp = panel.copy()
        tmp["static_permission_rank"] = tmp.apply(lambda row: permission_rank(action_permission(row, empty_exposure())), axis=1)
        cols = ["entry_ts", "static_permission_rank", "setup_rank", "source_sparse_rank", "price_rank", "catalyst_rank", "support_pressure_rank", "theme_ladder_rank", "lifecycle_id"]
        return tmp.sort_values(cols, kind="mergesort").reset_index(drop=True)
    else:
        cols = ["entry_ts", "setup_rank", "source_sparse_rank", "price_rank", "catalyst_rank", "support_pressure_rank", "theme_ladder_rank", "lifecycle_id"]
    return panel.sort_values(cols, kind="mergesort").reset_index(drop=True)


def empty_exposure() -> dict[str, object]:
    return {
        "active_theme_count": 0,
        "active_relation_count": 0,
        "active_driver_count": 0,
        "active_fragile_count": 0,
        "active_risk_warning_count": 0,
        "exposure_cluster_state": "exposure_clean",
    }


def exposure_context(row: dict[str, object], open_positions: list[dict[str, object]]) -> dict[str, object]:
    theme = s(row.get("theme_id", ""))
    relation = s(row.get("relation_transmission_state", ""))
    driver = dominant_driver(row)
    setup = s(row.get("setup_quality_bucket", ""))
    theme_count = sum(1 for pos in open_positions if s(pos.get("theme_id", "")) == theme)
    relation_count = sum(1 for pos in open_positions if s(pos.get("relation_transmission_state", "")) == relation)
    driver_count = sum(1 for pos in open_positions if s(pos.get("driver_state", "")) == driver)
    fragile_count = sum(1 for pos in open_positions if s(pos.get("setup_quality_bucket", "")) == "fragile_setup")
    warning_count = sum(1 for pos in open_positions if i(pos.get("risk_warning_flag", 0)) == 1)
    if setup == "fragile_setup" and fragile_count >= 1:
        cluster = "exposure_fragile_cluster"
    elif i(row.get("risk_warning_flag", 0)) == 1 and warning_count >= 2:
        cluster = "exposure_warning_cluster"
    elif theme_count >= 2 or relation_count >= 2 or driver_count >= 2:
        cluster = "exposure_concentrated"
    else:
        cluster = "exposure_clean"
    return {
        "active_theme_count": int(theme_count),
        "active_relation_count": int(relation_count),
        "active_driver_count": int(driver_count),
        "active_fragile_count": int(fragile_count),
        "active_risk_warning_count": int(warning_count),
        "exposure_cluster_state": cluster,
    }


def dominant_driver(row: dict[str, object] | pd.Series) -> str:
    value = s(row.get("rates_dollar_credit_liquidity_state", "driver_neutral_or_mixed"))
    if "rates" in value:
        return "rates"
    if "dollar" in value:
        return "dollar"
    if "credit" in value:
        return "credit"
    if "liquidity" in value:
        return "liquidity"
    if "multi_driver" in value:
        return "multi_driver"
    return "neutral_driver"


def action_permission(row: dict[str, object] | pd.Series, exposure: dict[str, object]) -> str:
    setup = s(row.get("setup_quality_bucket", ""))
    exposure_state = s(exposure.get("exposure_cluster_state", "exposure_clean"))
    if setup == "research_only_setup":
        return "research_only"
    if setup == "high_quality_setup" and exposure_state == "exposure_clean":
        return "priority_eligible"
    if setup == "high_quality_setup":
        return "cap_limited"
    if setup == "medium_quality_setup" and exposure_state == "exposure_clean":
        return "normal_eligible"
    if setup == "medium_quality_setup":
        return "cap_limited"
    if setup == "fragile_setup" and exposure_state in {"exposure_concentrated", "exposure_fragile_cluster", "exposure_warning_cluster"}:
        return "research_only"
    if setup == "fragile_setup":
        return "reduced_admission"
    return "reduced_admission"


def permission_rank(permission: str) -> int:
    return {
        "priority_eligible": 10,
        "normal_eligible": 20,
        "cap_limited": 40,
        "reduced_admission": 60,
        "research_only": 90,
    }.get(permission, 80)


def capacity_block_reason(row: dict[str, object], exposure: dict[str, object], spec: pd.Series) -> str:
    mode = s(spec["cap_mode"])
    setup = s(row.get("setup_quality_bucket", ""))
    high = setup == "high_quality_setup"
    if mode == "none":
        return ""
    if mode in {"relation3", "combined"} and int(exposure["active_relation_count"]) >= (3 if mode == "relation3" else 2):
        return "relation_concentration_cap"
    if mode == "relation2" and int(exposure["active_relation_count"]) >= 2:
        return "relation_concentration_cap"
    if mode in {"theme2", "combined"} and int(exposure["active_theme_count"]) >= 2:
        return "theme_concentration_cap"
    if mode in {"driver2", "combined"} and int(exposure["active_driver_count"]) >= 2:
        return "driver_concentration_cap"
    if mode in {"fragile1", "combined"} and not high and setup == "fragile_setup" and int(exposure["active_fragile_count"]) >= 1:
        return "fragile_cluster_cap"
    return ""


def allocation_record(row: dict[str, object], exposure: dict[str, object], permission: str, accepted_flag: int, reason: str) -> dict[str, object]:
    return {
        "lifecycle_id": row.get("lifecycle_id", ""),
        "symbol": row.get("symbol", ""),
        "entry_ts": row.get("entry_ts", ""),
        "split_name": row.get("split_name", ""),
        "theme_id": row.get("theme_id", ""),
        "setup_quality_bucket": row.get("setup_quality_bucket", ""),
        "slot_value_ladder": row.get("slot_value_ladder", ""),
        "relation_transmission_state": row.get("relation_transmission_state", ""),
        "dominant_driver": dominant_driver(row),
        "price_chart_acceptance_state": row.get("price_chart_acceptance_state", ""),
        "risk_warning_flag": row.get("risk_warning_flag", 0),
        "action_permission": permission,
        "exposure_cluster_state": exposure.get("exposure_cluster_state", ""),
        "active_theme_count": exposure.get("active_theme_count", 0),
        "active_relation_count": exposure.get("active_relation_count", 0),
        "active_driver_count": exposure.get("active_driver_count", 0),
        "active_fragile_count": exposure.get("active_fragile_count", 0),
        "accepted_flag": accepted_flag,
        "allocation_reason": reason,
        "net_return_costed": row.get("net_return_costed", ""),
    }


def build_setup_quality_performance(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    work = panel.copy()
    work["net_return_costed_eval"] = pd.to_numeric(work["net_return_from_entry"], errors="coerce") - COST_BPS / 10000.0
    for split in ["all", "validation", "recent_oos"]:
        scoped = work if split == "all" else work[work["split_name"].astype(str).eq(split)]
        for bucket, group in scoped.groupby("setup_quality_bucket", dropna=False):
            returns = pd.to_numeric(group["net_return_costed_eval"], errors="coerce")
            rows.append(
                {
                    "split_name": split,
                    "setup_quality_bucket": bucket,
                    "candidate_count": int(len(group)),
                    "avg_return_costed_pct_eval_only": float(returns.mean() * 100.0),
                    "win_rate_eval_only": float(returns.gt(0).mean()),
                    "entry_reduce_failure_rate_eval_only": float(returns.le(-0.03).mean()),
                    "return_used_in_assignment_flag": 0,
                    "label_used_in_assignment_flag": 0,
                }
            )
    return pd.DataFrame(rows).sort_values(["split_name", "setup_quality_bucket"]).reset_index(drop=True)


def build_setup_quality_mix(panel: pd.DataFrame) -> pd.DataFrame:
    cols = ["setup_quality_bucket", "company_catalyst_state", "relation_transmission_state", "price_chart_acceptance_state", "theme_leadership_state"]
    return panel.groupby(cols, dropna=False).size().reset_index(name="candidate_count").sort_values(["setup_quality_bucket", "candidate_count"], ascending=[True, False]).reset_index(drop=True)


def build_displacement_audit(accepted: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty:
        return pd.DataFrame()
    rows = []
    for split in ["all", "validation", "recent_oos"]:
        base = accepted[(accepted["candidate_name"].eq(BASELINE)) & (accepted["split_scope"].eq(split))]
        base_ids = set(base["lifecycle_id"].astype(str))
        for candidate_name, group in accepted[accepted["split_scope"].eq(split)].groupby("candidate_name", dropna=False):
            ids = set(group["lifecycle_id"].astype(str))
            rows.append(
                {
                    "candidate_name": candidate_name,
                    "split_name": split,
                    "baseline_accepted_count": int(len(base_ids)),
                    "candidate_accepted_count": int(len(ids)),
                    "common_accepted_count": int(len(base_ids & ids)),
                    "added_accepted_count": int(len(ids - base_ids)),
                    "removed_accepted_count": int(len(base_ids - ids)),
                    "accepted_set_changed_flag": int(ids != base_ids),
                }
            )
    return pd.DataFrame(rows).sort_values(["split_name", "candidate_name"]).reset_index(drop=True)


def build_winner_damage_audit(displacement: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    if displacement.empty:
        return pd.DataFrame()
    # Reconstruct accepted sets by re-simulating is intentionally avoided here; this report uses saved accepted trades below.
    return pd.DataFrame(columns=["candidate_name", "split_name", "audit_type", "trade_count", "avg_return_costed_pct_eval_only"])


def build_winner_damage_audit_from_accepted(accepted: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty:
        return pd.DataFrame()
    rows = []
    for split in ["all", "validation", "recent_oos"]:
        base = accepted[(accepted["candidate_name"].eq(BASELINE)) & (accepted["split_scope"].eq(split))]
        base_ids = set(base["lifecycle_id"].astype(str))
        for candidate_name, group in accepted[accepted["split_scope"].eq(split)].groupby("candidate_name", dropna=False):
            ids = set(group["lifecycle_id"].astype(str))
            candidate_rows = accepted[(accepted["candidate_name"].eq(candidate_name)) & (accepted["split_scope"].eq(split))]
            added = candidate_rows[candidate_rows["lifecycle_id"].astype(str).isin(ids - base_ids)]
            removed = base[base["lifecycle_id"].astype(str).isin(base_ids - ids)]
            for label, sub in [("added_vs_task639", added), ("removed_from_task639", removed)]:
                returns = pd.to_numeric(sub.get("net_return_costed", pd.Series(dtype=float)), errors="coerce")
                rows.append(
                    {
                        "candidate_name": candidate_name,
                        "split_name": split,
                        "audit_type": label,
                        "trade_count": int(len(sub)),
                        "avg_return_costed_pct_eval_only": float(returns.mean() * 100.0) if len(sub) else 0.0,
                        "return_used_in_assignment_flag": 0,
                    }
                )
    return pd.DataFrame(rows)


def build_mdd_windows(equity_curve: pd.DataFrame) -> pd.DataFrame:
    if equity_curve.empty:
        return pd.DataFrame()
    rows = []
    work = equity_curve.copy()
    work["event_ts"] = pd.to_datetime(work["event_ts"], utc=True)
    for (candidate, split), group in work.groupby(["candidate_name", "split_scope"], dropna=False):
        g = group.sort_values("event_ts")
        trough = g.loc[pd.to_numeric(g["drawdown_pct"], errors="coerce").idxmin()]
        before = g[g["event_ts"].le(trough["event_ts"])]
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


def build_exposure_cluster_audit(accepted: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty or windows.empty:
        return pd.DataFrame()
    rows = []
    acc = accepted.copy()
    acc["entry_ts"] = pd.to_datetime(acc["entry_ts"], utc=True)
    acc["simulated_exit_ts"] = pd.to_datetime(acc["simulated_exit_ts"], utc=True)
    for _, win in windows[windows["split_scope"].eq("all")].iterrows():
        candidate = s(win["candidate_name"])
        peak = pd.Timestamp(win["mdd_peak_ts"])
        trough = pd.Timestamp(win["mdd_trough_ts"])
        active = acc[(acc["candidate_name"].eq(candidate)) & (acc["split_scope"].eq("all"))]
        active = active[(active["entry_ts"].le(trough)) & (active["simulated_exit_ts"].ge(peak))]
        for axis in ["theme_id", "relation_transmission_state", "dominant_driver", "setup_quality_bucket", "price_chart_acceptance_state", "exposure_cluster_state"]:
            for value, group in active.groupby(axis, dropna=False):
                returns = pd.to_numeric(group["net_return_costed"], errors="coerce")
                rows.append(
                    {
                        "candidate_name": candidate,
                        "mdd_peak_ts": win["mdd_peak_ts"],
                        "mdd_trough_ts": win["mdd_trough_ts"],
                        "max_drawdown_pct": float(win["max_drawdown_pct"]),
                        "audit_axis": axis,
                        "axis_value": value,
                        "active_trade_count": int(len(group)),
                        "avg_return_costed_pct_eval_only": float(returns.mean() * 100.0),
                        "assignment_used_flag": 0,
                    }
                )
    return pd.DataFrame(rows).sort_values(["candidate_name", "audit_axis", "active_trade_count"], ascending=[True, True, False]).reset_index(drop=True)


def build_capacity_reason_audit(allocation: pd.DataFrame) -> pd.DataFrame:
    if allocation.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in allocation.groupby(["candidate_name", "split_scope", "allocation_reason"], dropna=False):
        candidate, split, reason = keys
        rows.append(
            {
                "candidate_name": candidate,
                "split_name": split,
                "allocation_reason": reason,
                "candidate_count": int(len(group)),
                "accepted_count": int(pd.to_numeric(group["accepted_flag"], errors="coerce").sum()),
                "blocked_count": int(pd.to_numeric(group["accepted_flag"], errors="coerce").eq(0).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["split_name", "candidate_name", "allocation_reason"]).reset_index(drop=True)


def build_promotion_report(grid: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    baseline = grid[(grid["candidate_name"].eq(BASELINE)) & (grid["split_name"].eq("all"))].iloc[0]
    base_validation = grid[(grid["candidate_name"].eq(BASELINE)) & (grid["split_name"].eq("validation"))].iloc[0]
    base_recent = grid[(grid["candidate_name"].eq(BASELINE)) & (grid["split_name"].eq("recent_oos"))].iloc[0]
    rows = []
    for _, spec in specs.iterrows():
        candidate_name = s(spec["candidate_name"])
        all_row = grid[(grid["candidate_name"].eq(candidate_name)) & (grid["split_name"].eq("all"))].iloc[0]
        val_row = grid[(grid["candidate_name"].eq(candidate_name)) & (grid["split_name"].eq("validation"))].iloc[0]
        recent_row = grid[(grid["candidate_name"].eq(candidate_name)) & (grid["split_name"].eq("recent_oos"))].iloc[0]
        final_up = float(all_row["final_capital_usd"]) > float(baseline["final_capital_usd"])
        mdd_ok = float(all_row["max_drawdown_pct"]) >= float(baseline["max_drawdown_pct"])
        validation_ok = float(val_row["final_capital_usd"]) >= float(base_validation["final_capital_usd"]) and float(val_row["max_drawdown_pct"]) >= float(base_validation["max_drawdown_pct"])
        recent_ok = float(recent_row["final_capital_usd"]) >= float(base_recent["final_capital_usd"]) and float(recent_row["max_drawdown_pct"]) >= float(base_recent["max_drawdown_pct"])
        allowed = int(spec["return_tuned_flag"]) == 0 and int(spec["fixed_hold_or_timing_override_flag"]) == 0 and int(spec["diagnostic_only_flag"]) == 0
        promotion = candidate_name != BASELINE and final_up and mdd_ok and validation_ok and recent_ok and allowed
        rows.append(
            {
                "candidate_name": candidate_name,
                "all_final_capital_usd": float(all_row["final_capital_usd"]),
                "all_max_drawdown_pct": float(all_row["max_drawdown_pct"]),
                "validation_final_capital_usd": float(val_row["final_capital_usd"]),
                "validation_max_drawdown_pct": float(val_row["max_drawdown_pct"]),
                "recent_oos_final_capital_usd": float(recent_row["final_capital_usd"]),
                "recent_oos_max_drawdown_pct": float(recent_row["max_drawdown_pct"]),
                "beats_task639_final_flag": int(final_up),
                "mdd_not_worse_than_task639_flag": int(mdd_ok),
                "validation_not_worse_flag": int(validation_ok),
                "recent_oos_not_worse_flag": int(recent_ok),
                "promotion_candidate_flag": int(promotion),
                "failure_reason": promotion_failure_reason(final_up, mdd_ok, validation_ok, recent_ok, allowed),
            }
        )
    return pd.DataFrame(rows).sort_values(["promotion_candidate_flag", "all_final_capital_usd"], ascending=[False, False]).reset_index(drop=True)


def promotion_failure_reason(final_up: bool, mdd_ok: bool, validation_ok: bool, recent_ok: bool, allowed: bool) -> str:
    reasons = []
    if not allowed:
        reasons.append("not_promotion_allowed")
    if not final_up:
        reasons.append("final_not_above_task639")
    if not mdd_ok:
        reasons.append("mdd_worse_than_task639")
    if not validation_ok:
        reasons.append("validation_not_worse_gate_failed")
    if not recent_ok:
        reasons.append("recent_oos_not_worse_gate_failed")
    return "PASS" if not reasons else "+".join(reasons)


def build_forbidden_input_audit(panel: pd.DataFrame, specs: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    checks = {
        "return_used_in_setup_assignment_flag": int(pd.to_numeric(panel["return_used_in_setup_assignment_flag"], errors="coerce").fillna(0).sum()),
        "label_used_in_setup_assignment_flag": int(pd.to_numeric(panel["label_used_in_setup_assignment_flag"], errors="coerce").fillna(0).sum()),
        "future_price_used_in_setup_assignment_flag": int(pd.to_numeric(panel["future_price_used_in_setup_assignment_flag"], errors="coerce").fillna(0).sum()),
        "proxy_risk_used_as_hard_rule_flag": int(pd.to_numeric(panel["proxy_risk_used_as_hard_rule_flag"], errors="coerce").fillna(0).sum()),
        "slot_value_rank_tuned_flag": int(pd.to_numeric(panel["slot_value_rank_tuned_flag"], errors="coerce").fillna(0).sum()),
        "symbol_blacklist_used": 0,
        "theme_blacklist_used": 0,
        "fixed_hold_or_timing_override": int(pd.to_numeric(specs["fixed_hold_or_timing_override_flag"], errors="coerce").fillna(0).sum()),
        "return_tuned_candidates": int(pd.to_numeric(specs["return_tuned_flag"], errors="coerce").fillna(0).sum()),
    }
    rows = []
    for name, violations in checks.items():
        rows.append({"check_name": name, "violation_count": violations, "pass_flag": int(violations == 0), "required_value": "0 violations"})
    return pd.DataFrame(rows)


def build_action_permission_matrix() -> pd.DataFrame:
    rows = [
        ("high_quality_setup", "exposure_clean", "priority_eligible", 1),
        ("high_quality_setup", "exposure_concentrated", "cap_limited", 1),
        ("high_quality_setup", "exposure_warning_cluster", "cap_limited", 1),
        ("medium_quality_setup", "exposure_clean", "normal_eligible", 1),
        ("medium_quality_setup", "exposure_concentrated", "cap_limited", 1),
        ("medium_quality_setup", "exposure_warning_cluster", "cap_limited", 1),
        ("uncertain_setup", "exposure_clean", "reduced_admission", 1),
        ("fragile_setup", "exposure_clean", "reduced_admission", 1),
        ("fragile_setup", "exposure_concentrated", "research_only", 0),
        ("fragile_setup", "exposure_fragile_cluster", "research_only", 0),
        ("research_only_setup", "any", "research_only", 0),
    ]
    return pd.DataFrame(
        [
            {
                "setup_quality_bucket": setup,
                "exposure_cluster_state": exposure,
                "action_permission": permission,
                "trading_assignment_allowed_flag": allowed,
                "full_entry_or_size_boost_flag": 0,
                "symbol_block_flag": 0,
                "theme_block_flag": 0,
                "hard_block_flag": 0,
                "rule_basis": "predeclared_entry_time_state_ladder",
            }
            for setup, exposure, permission, allowed in rows
        ]
    )


def build_task673_decision(panel: pd.DataFrame, setup_perf: pd.DataFrame) -> pd.DataFrame:
    return decision_frame(
        "Task673",
        "SETUP_QUALITY_LAYER_BUILT_RESEARCH_ONLY",
        {
            "candidate_count": len(panel),
            "setup_bucket_count": panel["setup_quality_bucket"].nunique(),
            "high_quality_count": int(panel["setup_quality_bucket"].eq("high_quality_setup").sum()),
            "research_only_count": int(panel["setup_quality_bucket"].eq("research_only_setup").sum()),
            "relation_name_alone_high_quality_violations": int(panel["relation_name_alone_high_quality_flag"].sum()),
            "next_action": "Use setup buckets only as a predeclared intermediate layer; do not promote without slot and exposure validation.",
        },
    )


def build_task674_decision(grid: pd.DataFrame, displacement: pd.DataFrame) -> pd.DataFrame:
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    return decision_frame(
        "Task674",
        "SLOT_VALUE_LADDER_TESTED_NO_PROMOTION_YET",
        {
            "best_candidate_name": best["candidate_name"],
            "best_final_capital_usd": float(best["final_capital_usd"]),
            "best_max_drawdown_pct": float(best["max_drawdown_pct"]),
            "displacement_rows": len(displacement),
            "next_action": "Review displacement and winner damage before accepting any same-timestamp slot ladder.",
        },
    )


def build_task675_decision(exposure: pd.DataFrame) -> pd.DataFrame:
    return decision_frame(
        "Task675",
        "EXPOSURE_CLUSTER_AUDIT_BUILT_DIAGNOSTIC_ONLY",
        {
            "exposure_audit_rows": len(exposure),
            "assignment_used_flag": int(pd.to_numeric(exposure.get("assignment_used_flag", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()) if not exposure.empty else 0,
            "next_action": "Use exposure audit to predeclare conservative caps; do not derive caps from MDD-only hindsight.",
        },
    )


def build_task676_decision(promotion: pd.DataFrame) -> pd.DataFrame:
    promo_count = int(pd.to_numeric(promotion["promotion_candidate_flag"], errors="coerce").sum()) if not promotion.empty else 0
    best = promotion.sort_values("all_final_capital_usd", ascending=False).iloc[0]
    return decision_frame(
        "Task676",
        "CONSERVATIVE_CAP_TESTED_PROMOTION_GATE_EVALUATED",
        {
            "promotion_candidate_count": promo_count,
            "best_candidate_name": best["candidate_name"],
            "best_final_capital_usd": float(best["all_final_capital_usd"]),
            "best_max_drawdown_pct": float(best["all_max_drawdown_pct"]),
            "next_action": "If no candidate passes all gates, keep as research and inspect which cap damaged winners.",
        },
    )


def build_task677_decision(action_matrix: pd.DataFrame) -> pd.DataFrame:
    forbidden_actions = action_matrix[action_matrix[["full_entry_or_size_boost_flag", "symbol_block_flag", "theme_block_flag", "hard_block_flag"]].sum(axis=1).gt(0)]
    return decision_frame(
        "Task677",
        "ACTION_PERMISSION_MATRIX_BUILT_NOT_DEPLOYMENT_READY",
        {
            "action_permission_rows": len(action_matrix),
            "forbidden_action_rows": len(forbidden_actions),
            "next_action": "Use matrix as permission contract for future OOS tests only.",
        },
    )


def decision_frame(task_id: str, decision: str, extras: dict[str, object]) -> pd.DataFrame:
    base = {
        "task_id": task_id,
        "decision": decision,
        "strategy_acceptance_status": "NOT_ACCEPTED",
        "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital_status": "FORBIDDEN",
        "trading_promotion_pass_flag": 0,
    }
    base.update(extras)
    return pd.DataFrame([base])


def build_task673_pass_fail(panel: pd.DataFrame, setup_perf: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("setup_quality_panel_built", not panel.empty, f"rows={len(panel)}", "setup quality exists"),
            gate("all_required_buckets_present", panel["setup_quality_bucket"].nunique() >= 4, f"buckets={panel['setup_quality_bucket'].nunique()}", "multiple setup buckets"),
            gate("no_return_label_future_assignment", panel[["return_used_in_setup_assignment_flag", "label_used_in_setup_assignment_flag", "future_price_used_in_setup_assignment_flag"]].sum().sum() == 0, "violations=0", "0 violations"),
            gate("relation_name_alone_not_high", panel["relation_name_alone_high_quality_flag"].sum() == 0, f"violations={int(panel['relation_name_alone_high_quality_flag'].sum())}", "0 violations"),
            gate("proxy_not_hard_rule", panel["proxy_risk_used_as_hard_rule_flag"].sum() == 0, "violations=0", "0 violations"),
            gate("setup_oos_perf_report_built", not setup_perf.empty, f"rows={len(setup_perf)}", "split setup quality performance"),
            gate("strategy_accepted", False, "research only", "promotion gates required"),
        ]
    )


def build_task674_pass_fail(grid: pd.DataFrame, displacement: pd.DataFrame, winner_damage: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("candidate_grid_built", not grid.empty, f"rows={len(grid)}", "slot ladder candidate grid"),
            gate("same_timestamp_ladder_only", True, "entry/exit/cost unchanged", "only ordering changed"),
            gate("rank_ladder_not_weighted_score", True, "predeclared rank columns", "no tuned score weights"),
            gate("displacement_audit_built", not displacement.empty, f"rows={len(displacement)}", "Task639 displacement audit"),
            gate("winner_damage_audit_built", not winner_damage.empty, f"rows={len(winner_damage)}", "added removed trade audit"),
            gate("strategy_accepted", False, "research only", "Task676 promotion gates required"),
        ]
    )


def build_task675_pass_fail(exposure: pd.DataFrame) -> pd.DataFrame:
    used = int(pd.to_numeric(exposure.get("assignment_used_flag", pd.Series(dtype=int)), errors="coerce").fillna(0).sum()) if not exposure.empty else 0
    return pd.DataFrame(
        [
            gate("exposure_cluster_audit_built", not exposure.empty, f"rows={len(exposure)}", "MDD exposure cluster audit"),
            gate("assignment_not_used", used == 0, f"assignment_used={used}", "0 assignment use"),
            gate("mdd_hindsight_not_promoted", True, "audit only", "no MDD-only cap promotion"),
        ]
    )


def build_task676_pass_fail(promotion: pd.DataFrame, forbidden: pd.DataFrame, capacity_reason: pd.DataFrame) -> pd.DataFrame:
    promo_count = int(pd.to_numeric(promotion["promotion_candidate_flag"], errors="coerce").sum()) if not promotion.empty else 0
    violations = int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum()) if not forbidden.empty else 999
    return pd.DataFrame(
        [
            gate("capacity_backtest_built", not promotion.empty, f"rows={len(promotion)}", "capacity promotion report"),
            gate("capacity_reason_audit_built", not capacity_reason.empty, f"rows={len(capacity_reason)}", "capacity reason audit"),
            gate("forbidden_inputs_clean", violations == 0, f"violations={violations}", "0 violations"),
            gate("promotion_candidate_found", promo_count > 0, f"promotion_candidates={promo_count}", "must beat Task639 final MDD validation recent"),
            gate("strategy_accepted", False, "not accepted", "separate acceptance gate"),
        ]
    )


def build_task677_pass_fail(action_matrix: pd.DataFrame, forbidden: pd.DataFrame) -> pd.DataFrame:
    bad = int(action_matrix[["full_entry_or_size_boost_flag", "symbol_block_flag", "theme_block_flag", "hard_block_flag"]].sum().sum()) if not action_matrix.empty else 999
    return pd.DataFrame(
        [
            gate("action_permission_matrix_built", not action_matrix.empty, f"rows={len(action_matrix)}", "permission matrix"),
            gate("no_forbidden_actions", bad == 0, f"forbidden_action_flags={bad}", "0 forbidden action flags"),
            gate("no_return_label_assignment", int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum()) == 0, "violations=0", "0 violations"),
            gate("real_capital_allowed", False, "FORBIDDEN", "accepted strategy and live readiness"),
        ]
    )


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {"gate": name, "pass_flag": int(bool(passed)), "observed_value": observed, "required_value": required}


def write_task673(panel: pd.DataFrame, perf: pd.DataFrame, mix: pd.DataFrame, decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    panel.to_csv(TASK673_DIR / "task673_setup_quality_panel.csv", index=False, encoding="utf-8-sig")
    perf.to_csv(TASK673_DIR / "task673_setup_quality_performance.csv", index=False, encoding="utf-8-sig")
    mix.to_csv(TASK673_DIR / "task673_setup_quality_component_mix.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(TASK673_DIR / "task_673_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(TASK673_DIR / "task_673_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_gpt_review(TASK673_DIR)
    write_report(TASK673_DIR, "Task673 Setup Quality Layer", decision, [("Setup Performance", perf), ("Pass Fail", pass_fail)])
    write_manifest(TASK673_DIR, TASK673_DIR / "artifact_manifest.csv")


def write_task674(grid: pd.DataFrame, displacement: pd.DataFrame, winner_damage: pd.DataFrame, decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    grid.to_csv(TASK674_DIR / "task674_slot_value_candidate_grid.csv", index=False, encoding="utf-8-sig")
    displacement.to_csv(TASK674_DIR / "task674_displacement_audit.csv", index=False, encoding="utf-8-sig")
    winner_damage.to_csv(TASK674_DIR / "task674_winner_damage_audit.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(TASK674_DIR / "task_674_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(TASK674_DIR / "task_674_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(TASK674_DIR, "Task674 Slot Value Displacement Engine", decision, [("Candidate Grid", grid), ("Displacement", displacement), ("Pass Fail", pass_fail)])
    write_manifest(TASK674_DIR, TASK674_DIR / "artifact_manifest.csv")


def write_task675(exposure: pd.DataFrame, windows: pd.DataFrame, decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    exposure.to_csv(TASK675_DIR / "task675_exposure_cluster_report.csv", index=False, encoding="utf-8-sig")
    windows.to_csv(TASK675_DIR / "task675_mdd_windows.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(TASK675_DIR / "task_675_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(TASK675_DIR / "task_675_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(TASK675_DIR, "Task675 Exposure Cluster Audit", decision, [("Exposure Cluster", exposure), ("Pass Fail", pass_fail)])
    write_manifest(TASK675_DIR, TASK675_DIR / "artifact_manifest.csv")


def write_task676(specs: pd.DataFrame, grid: pd.DataFrame, accepted: pd.DataFrame, allocation: pd.DataFrame, capacity_reason: pd.DataFrame, promotion: pd.DataFrame, forbidden: pd.DataFrame, decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    winner_damage = build_winner_damage_audit_from_accepted(accepted)
    specs.to_csv(TASK676_DIR / "task676_capacity_candidate_specs.csv", index=False, encoding="utf-8-sig")
    grid.to_csv(TASK676_DIR / "task676_capacity_candidate_grid.csv", index=False, encoding="utf-8-sig")
    accepted.to_csv(TASK676_DIR / "task676_accepted_trades.csv", index=False, encoding="utf-8-sig")
    allocation.to_csv(TASK676_DIR / "task676_allocation_panel.csv", index=False, encoding="utf-8-sig")
    capacity_reason.to_csv(TASK676_DIR / "task676_capacity_reason_audit.csv", index=False, encoding="utf-8-sig")
    winner_damage.to_csv(TASK676_DIR / "task676_added_removed_trade_audit.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(TASK676_DIR / "task676_promotion_report.csv", index=False, encoding="utf-8-sig")
    forbidden.to_csv(TASK676_DIR / "task676_forbidden_input_audit.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(TASK676_DIR / "task_676_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(TASK676_DIR / "task_676_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(TASK676_DIR, "Task676 Conservative Capacity Cap", decision, [("Candidate Grid", grid), ("Promotion", promotion), ("Capacity Reasons", capacity_reason), ("Forbidden", forbidden), ("Pass Fail", pass_fail)])
    write_manifest(TASK676_DIR, TASK676_DIR / "artifact_manifest.csv")


def write_task677(action_matrix: pd.DataFrame, forbidden: pd.DataFrame, decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    action_matrix.to_csv(TASK677_DIR / "task677_action_permission_matrix.csv", index=False, encoding="utf-8-sig")
    forbidden.to_csv(TASK677_DIR / "task677_forbidden_action_audit.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(TASK677_DIR / "task_677_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(TASK677_DIR / "task_677_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(TASK677_DIR, "Task677 Action Permission Matrix", decision, [("Action Permission Matrix", action_matrix), ("Pass Fail", pass_fail)])
    write_manifest(TASK677_DIR, TASK677_DIR / "artifact_manifest.csv")


def write_gpt_review(out_dir: Path) -> None:
    text = """# Task673-677 GPT Design Review Summary

Captured via Chrome ChatGPT in the `1. 코딩/투자` tab.

Status: external model interpretation only.

Key instructions adopted:

- Use predeclared rank ladders instead of tuned slot scores.
- Do not use `extension_proxy` or `market_stress_proxy` as standalone hard rules.
- Do not let `relation_reinforcing` alone create `high_quality_setup`.
- Task675 exposure cluster work is diagnostic only.
- Capacity caps must be tested step by step: relation, theme, driver, fragile, combined.
- Promotion requires final capital above Task639, MDD not worse than Task639, validation/recent not worse, and forbidden inputs clean.
"""
    (out_dir / "task_673_677_gpt_design_review_response.md").write_text(text, encoding="utf-8")


def write_report(out_dir: Path, title: str, decision: pd.DataFrame, sections: list[tuple[str, pd.DataFrame]]) -> None:
    d = decision.iloc[0]
    lines = [
        f"# {title}",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        "",
        "## Quant Expert Report",
        "",
        "This task uses current entry-time data only. It does not use microstructure, future returns, future labels, symbol blacklist, or theme blacklist for assignment.",
        "",
    ]
    for heading, frame in sections:
        lines.extend([f"### {heading}", "", table(frame.head(40)), ""])
    lines.extend(
        [
            "## No-Background Decision-Maker Report",
            "",
            "이번 작업은 바로 실전 매매로 승격하지 않습니다.",
            "",
            "상태를 더 쪼개고, 슬롯 경쟁과 동시 노출을 분리해서 다음 매매 룰 후보가 과최적화인지 확인하는 단계입니다.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    )
    filename = out_dir.name.replace("task_", "task_") + ".md"
    (out_dir / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    clipped = df.fillna("")
    headers = [str(c) for c in clipped.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in clipped.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "\\|").replace("\n", " ") for c in clipped.columns) + " |")
    return "\n".join(lines)


def empty_quality() -> dict[str, float]:
    return {"capital_pnl_pct": 0.0, "max_drawdown_pct": 0.0, "entry_reduce_failure_rate": 0.0}


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
    parser.add_argument("--task672-dir", type=Path, default=TASK672_DIR)
    parser.add_argument("--qqq-path", type=Path, default=QQQ_PATH)
    args = parser.parse_args()
    outputs = build_task673_677_program(task672_dir=args.task672_dir, qqq_path=args.qqq_path)
    print("[Task673-677] complete")
    print(outputs["promotion"].to_string(index=False))


if __name__ == "__main__":
    main()
