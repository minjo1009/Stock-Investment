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


TASK_ID = "Task666"
REPORT_DIR = Path("docs/reports/task_666_priority_risk_cap_backtest")
PRIORITY_RULE = "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse"


def build_task666_priority_risk_cap_backtest(
    *,
    task659_panel_path: Path = TASK659_PANEL,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = build_mechanism_state_panel(load_task659_panel(task659_panel_path), build_institutional_transmission_template())
    core = add_priority(task639_core(panel), PRIORITY_RULE)
    qqq = load_qqq_history(qqq_path)
    specs = build_risk_cap_specs()
    candidate_grid, accepted, allocation = build_candidate_grid(core, specs, qqq)
    promotion = build_promotion_report(candidate_grid, specs)
    cap_audit = build_cap_audit(accepted)
    theme_concentration = build_concentration_audit(allocation, ["entry_ts", "theme_id"], "theme")
    relation_concentration = build_concentration_audit(allocation, ["entry_ts", "mechanism_relation_state"], "relation_state")
    displacement_pairs = build_displacement_pairs(accepted)
    mdd_contribution = build_mdd_contribution_report(accepted, candidate_grid)
    decision = build_decision(promotion)
    pass_fail = build_pass_fail(specs, promotion, cap_audit, displacement_pairs)

    specs.to_csv(out_dir / "priority_risk_cap_specs.csv", index=False, encoding="utf-8-sig")
    candidate_grid.to_csv(out_dir / "priority_risk_cap_candidate_grid.csv", index=False, encoding="utf-8-sig")
    accepted.to_csv(out_dir / "priority_risk_cap_accepted_trades.csv", index=False, encoding="utf-8-sig")
    allocation.to_csv(out_dir / "task666_capacity_allocation_panel.csv", index=False, encoding="utf-8-sig")
    theme_concentration.to_csv(out_dir / "task666_theme_concentration_audit.csv", index=False, encoding="utf-8-sig")
    relation_concentration.to_csv(out_dir / "task666_relation_concentration_audit.csv", index=False, encoding="utf-8-sig")
    displacement_pairs.to_csv(out_dir / "task666_displacement_pairs.csv", index=False, encoding="utf-8-sig")
    mdd_contribution.to_csv(out_dir / "task666_mdd_contribution_report.csv", index=False, encoding="utf-8-sig")
    cap_audit.to_csv(out_dir / "priority_risk_cap_audit.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(out_dir / "priority_risk_cap_promotion_report.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_666_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_666_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, candidate_grid, promotion, cap_audit, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "specs": specs,
        "candidate_grid": candidate_grid,
        "accepted": accepted,
        "allocation": allocation,
        "theme_concentration": theme_concentration,
        "relation_concentration": relation_concentration,
        "displacement_pairs": displacement_pairs,
        "mdd_contribution": mdd_contribution,
        "cap_audit": cap_audit,
        "promotion": promotion,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_risk_cap_specs() -> pd.DataFrame:
    rows = [
        {
            "candidate_name": "baseline_task639",
            "candidate_type": "baseline",
            "priority_enabled_flag": 0,
            "theme_cap_per_timestamp": 999,
            "high_vol_theme_cap_per_timestamp": 999,
            "sparse_allowed_flag": 1,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Original Task639 ordering and capacity.",
        },
        {
            "candidate_name": "priority_no_cap",
            "candidate_type": "priority_reference",
            "priority_enabled_flag": 1,
            "theme_cap_per_timestamp": 999,
            "high_vol_theme_cap_per_timestamp": 999,
            "sparse_allowed_flag": 1,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Task664 relation priority reference.",
        },
        {
            "candidate_name": "priority_theme_cap2",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "theme_cap_per_timestamp": 2,
            "high_vol_theme_cap_per_timestamp": 999,
            "sparse_allowed_flag": 1,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "At most two accepted trades from the same theme at the same entry timestamp.",
        },
        {
            "candidate_name": "priority_theme_cap1",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "theme_cap_per_timestamp": 1,
            "high_vol_theme_cap_per_timestamp": 999,
            "sparse_allowed_flag": 1,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "At most one accepted trade from the same theme at the same entry timestamp.",
        },
        {
            "candidate_name": "priority_highvol_theme_cap1",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "theme_cap_per_timestamp": 999,
            "high_vol_theme_cap_per_timestamp": 1,
            "sparse_allowed_flag": 1,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "At most one high-volatility theme trade at the same entry timestamp.",
        },
        {
            "candidate_name": "priority_theme_cap2_no_sparse",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "theme_cap_per_timestamp": 2,
            "high_vol_theme_cap_per_timestamp": 999,
            "sparse_allowed_flag": 0,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Theme cap two plus sparse mechanism rows cannot consume slots.",
        },
        {
            "candidate_name": "priority_relation_cap2",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "timestamp_relation_cap": 2,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "At most two accepted trades from the same relation state at the same entry timestamp.",
        },
        {
            "candidate_name": "priority_theme_relation_cap1",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "timestamp_theme_relation_cap": 1,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "At most one accepted trade from the same theme and relation state at the same entry timestamp.",
        },
        {
            "candidate_name": "priority_active_theme_cap2",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "active_theme_cap": 2,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "At most two open positions from the same theme.",
        },
        {
            "candidate_name": "priority_active_relation_cap3",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "active_relation_cap": 3,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "At most three open positions from the same relation state.",
        },
        {
            "candidate_name": "priority_active_theme_relation_cap1",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "active_theme_relation_cap": 1,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "At most one open position from the same theme and relation state.",
        },
        {
            "candidate_name": "priority_active_theme2_relation3_combo",
            "candidate_type": "predeclared_risk_cap",
            "priority_enabled_flag": 1,
            "active_theme_cap": 2,
            "active_relation_cap": 3,
            "diagnostic_only_flag": 0,
            "return_tuned_flag": 0,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Open portfolio cap: same theme at most two and same relation state at most three.",
        },
        {
            "candidate_name": "diagnostic_block_mdd_bad_added_themes",
            "candidate_type": "diagnostic_risk_cap",
            "priority_enabled_flag": 1,
            "theme_cap_per_timestamp": 999,
            "high_vol_theme_cap_per_timestamp": 999,
            "sparse_allowed_flag": 1,
            "diagnostic_only_flag": 1,
            "return_tuned_flag": 1,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Diagnostic only: blocks themes observed in Task665 added-loss examples.",
        },
        {
            "candidate_name": "diagnostic_active_highvol_cap2",
            "candidate_type": "diagnostic_risk_cap",
            "priority_enabled_flag": 1,
            "active_high_vol_cap": 2,
            "diagnostic_only_flag": 1,
            "return_tuned_flag": 1,
            "fixed_hold_or_timing_override_flag": 0,
            "description": "Diagnostic only: at most two open positions from predefined high-volatility themes.",
        },
    ]
    specs = pd.DataFrame(rows)
    defaults = {
        "theme_cap_per_timestamp": 999,
        "high_vol_theme_cap_per_timestamp": 999,
        "timestamp_relation_cap": 999,
        "timestamp_theme_relation_cap": 999,
        "active_theme_cap": 999,
        "active_relation_cap": 999,
        "active_theme_relation_cap": 999,
        "active_high_vol_cap": 999,
        "sparse_allowed_flag": 1,
        "diagnostic_only_flag": 0,
        "return_tuned_flag": 0,
        "fixed_hold_or_timing_override_flag": 0,
    }
    for column, value in defaults.items():
        if column not in specs.columns:
            specs[column] = value
        specs[column] = specs[column].fillna(value)
    return specs


def build_candidate_grid(core: pd.DataFrame, specs: pd.DataFrame, qqq: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    accepted_rows = []
    allocation_rows = []
    for _, spec in specs.iterrows():
        panel = core.copy()
        if int(spec["priority_enabled_flag"]) == 0:
            panel = panel.assign(priority_rank=50, priority_rule="entry_ts_then_lifecycle_id")
        for split_name in ["all", "validation", "recent_oos"]:
            scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)].copy()
            quality, accepted, allocation = simulate_with_risk_caps(scoped, spec)
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
            if not accepted.empty:
                acc = accepted.copy()
                acc["candidate_name"] = spec["candidate_name"]
                acc["split_scope"] = split_name
                accepted_rows.append(acc)
            if not allocation.empty:
                alloc = allocation.copy()
                alloc["candidate_name"] = spec["candidate_name"]
                alloc["split_scope"] = split_name
                allocation_rows.append(alloc)
    grid = pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True)
    accepted_all = pd.concat(accepted_rows, ignore_index=True) if accepted_rows else pd.DataFrame()
    allocation_all = pd.concat(allocation_rows, ignore_index=True) if allocation_rows else pd.DataFrame()
    return grid, accepted_all, allocation_all


def simulate_with_risk_caps(panel: pd.DataFrame, spec: pd.Series) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    if panel.empty:
        return empty_quality(), panel.copy(), panel.copy()
    ordered = panel.sort_values(["entry_ts", "priority_rank", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    ordered["net_return_costed"] = pd.to_numeric(ordered["net_return_from_entry"], errors="coerce") - COST_BPS / 10000.0
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    drawdowns = [0.0]
    current_entry_ts: pd.Timestamp | None = None
    timestamp_theme_counts: dict[str, int] = {}
    timestamp_relation_counts: dict[str, int] = {}
    timestamp_theme_relation_counts: dict[tuple[str, str], int] = {}
    timestamp_highvol_count = 0
    allocation_rows: list[dict[str, object]] = []

    def close_positions_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= current_ts:
                equity += float(pos["capital"]) * float(pos["return"])
                peak = max(peak, equity)
                drawdowns.append((equity / max(peak, 1e-9) - 1.0) * 100.0)
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_positions_until(entry_ts)
        if current_entry_ts is None or entry_ts != current_entry_ts:
            current_entry_ts = entry_ts
            timestamp_theme_counts = {}
            timestamp_relation_counts = {}
            timestamp_theme_relation_counts = {}
            timestamp_highvol_count = 0
        if len(open_positions) >= MAX_POSITIONS:
            allocation_rows.append(allocation_record(row, 0, "max_positions_full", len(open_positions)))
            continue
        ok, reason = passes_risk_caps(row, spec, timestamp_theme_counts, timestamp_relation_counts, timestamp_theme_relation_counts, timestamp_highvol_count, open_positions)
        if not ok:
            allocation_rows.append(allocation_record(row, 0, reason, len(open_positions)))
            continue
        theme = str(row.get("theme_id", ""))
        relation = str(row.get("mechanism_relation_state", ""))
        highvol = is_high_vol_theme(theme)
        timestamp_theme_counts[theme] = timestamp_theme_counts.get(theme, 0) + 1
        timestamp_relation_counts[relation] = timestamp_relation_counts.get(relation, 0) + 1
        timestamp_theme_relation_counts[(theme, relation)] = timestamp_theme_relation_counts.get((theme, relation), 0) + 1
        if highvol:
            timestamp_highvol_count += 1
        capital = equity / float(MAX_POSITIONS)
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_costed"],
                "theme_id": theme,
                "mechanism_relation_state": relation,
            }
        )
        allocation_rows.append(allocation_record(row, 1, "accepted", len(open_positions)))
        accepted = dict(row)
        accepted["risk_cap_accepted_flag"] = 1
        accepted["net_return_costed"] = row["net_return_costed"]
        accepted_rows.append(accepted)
    close_positions_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    allocation = pd.DataFrame(allocation_rows)
    if accepted.empty:
        return empty_quality(), accepted, allocation
    returns = pd.to_numeric(accepted["net_return_costed"], errors="coerce")
    quality = {
        "capital_pnl_pct": float((equity - 1.0) * 100.0),
        "max_drawdown_pct": float(min(drawdowns) if drawdowns else 0.0),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
        "avg_return_pct": float(returns.mean() * 100.0),
        "win_rate": float(returns.gt(0).mean()),
    }
    return quality, accepted, allocation


def passes_risk_caps(
    row: dict[str, object],
    spec: pd.Series,
    theme_counts: dict[str, int],
    relation_counts: dict[str, int],
    theme_relation_counts: dict[tuple[str, str], int],
    highvol_count: int,
    open_positions: list[dict[str, object]],
) -> tuple[bool, str]:
    theme = str(row.get("theme_id", ""))
    relation = str(row.get("mechanism_relation_state", ""))
    if int(spec["sparse_allowed_flag"]) == 0 and str(row.get("mechanism_relation_state", "")) == "sparse_mechanism_cell":
        return False, "sparse_not_allowed"
    if theme_counts.get(theme, 0) >= int(spec["theme_cap_per_timestamp"]):
        return False, "timestamp_theme_cap"
    if relation_counts.get(relation, 0) >= int(spec["timestamp_relation_cap"]):
        return False, "timestamp_relation_cap"
    if theme_relation_counts.get((theme, relation), 0) >= int(spec["timestamp_theme_relation_cap"]):
        return False, "timestamp_theme_relation_cap"
    if is_high_vol_theme(theme) and highvol_count >= int(spec["high_vol_theme_cap_per_timestamp"]):
        return False, "timestamp_high_vol_theme_cap"
    active_theme_count = sum(1 for pos in open_positions if str(pos.get("theme_id", "")) == theme)
    if active_theme_count >= int(spec["active_theme_cap"]):
        return False, "active_theme_cap"
    active_relation_count = sum(1 for pos in open_positions if str(pos.get("mechanism_relation_state", "")) == relation)
    if active_relation_count >= int(spec["active_relation_cap"]):
        return False, "active_relation_cap"
    active_theme_relation_count = sum(
        1
        for pos in open_positions
        if str(pos.get("theme_id", "")) == theme and str(pos.get("mechanism_relation_state", "")) == relation
    )
    if active_theme_relation_count >= int(spec["active_theme_relation_cap"]):
        return False, "active_theme_relation_cap"
    active_high_vol_count = sum(1 for pos in open_positions if is_high_vol_theme(str(pos.get("theme_id", ""))))
    if is_high_vol_theme(theme) and active_high_vol_count >= int(spec["active_high_vol_cap"]):
        return False, "active_high_vol_cap"
    if str(spec["candidate_name"]) == "diagnostic_block_mdd_bad_added_themes" and theme in {
        "data_devops_software",
        "cybersecurity",
        "biotech_glp1_healthcare",
    }:
        return False, "diagnostic_mdd_bad_theme_block"
    return True, "accepted"


def allocation_record(row: dict[str, object], accepted_flag: int, reason: str, open_position_count: int) -> dict[str, object]:
    return {
        "lifecycle_id": row.get("lifecycle_id", ""),
        "symbol": row.get("symbol", ""),
        "entry_ts": row.get("entry_ts", ""),
        "simulated_exit_ts": row.get("simulated_exit_ts", ""),
        "split_name": row.get("split_name", ""),
        "theme_id": row.get("theme_id", ""),
        "mechanism_relation_state": row.get("mechanism_relation_state", ""),
        "priority_rank": row.get("priority_rank", ""),
        "accepted_flag": accepted_flag,
        "allocation_reason": reason,
        "open_position_count_after_decision": open_position_count,
        "net_return_from_entry": row.get("net_return_from_entry", ""),
        "net_return_costed": row.get("net_return_costed", ""),
    }


def is_high_vol_theme(theme: str) -> bool:
    return theme in {"crypto_fintech", "ev_autonomy_mobility", "biotech_glp1_healthcare", "data_devops_software", "cybersecurity"}


def empty_quality() -> dict[str, object]:
    return {
        "capital_pnl_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "avg_return_pct": 0.0,
        "win_rate": 0.0,
    }


def build_promotion_report(grid: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    baseline = pivot_candidate(grid, "baseline_task639")
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
        promotion = int(
            candidate_name != "baseline_task639"
            and beats_all
            and dd_ok
            and validation_up
            and recent_up
            and validation_dd_ok
            and recent_dd_ok
            and allowed
        )
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
        for column in ["final_capital_usd", "max_drawdown_pct", "accepted_trade_count", "entry_reduce_failure_rate", "beats_qqq_flag"]:
            out[f"{split}_{column}"] = float(row[column])
    return out


def failure_reason(
    promotion: int,
    allowed: int,
    beats_all: int,
    dd_ok: int,
    validation_up: int,
    recent_up: int,
    validation_dd_ok: int,
    recent_dd_ok: int,
) -> str:
    if promotion:
        return "passes_all_risk_cap_gates"
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


def build_cap_audit(accepted: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in accepted.groupby(["candidate_name", "split_scope"], dropna=False):
        candidate, split = keys
        theme_counts = group.groupby("theme_id").size().sort_values(ascending=False)
        rows.append(
            {
                "candidate_name": candidate,
                "split_scope": split,
                "accepted_count": int(len(group)),
                "unique_theme_count": int(group["theme_id"].nunique()),
                "top_theme": str(theme_counts.index[0]) if len(theme_counts) else "",
                "top_theme_count": int(theme_counts.iloc[0]) if len(theme_counts) else 0,
                "high_vol_theme_count": int(group["theme_id"].astype(str).apply(is_high_vol_theme).sum()),
                "entry_reduce_failure_rate": float(pd.to_numeric(group["net_return_costed"], errors="coerce").le(-0.03).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["split_scope", "candidate_name"]).reset_index(drop=True)


def build_concentration_audit(allocation: pd.DataFrame, keys: list[str], concentration_type: str) -> pd.DataFrame:
    if allocation.empty:
        return pd.DataFrame()
    group_cols = ["candidate_name", "split_scope", *keys]
    rows = (
        allocation.groupby(group_cols, dropna=False)
        .agg(
            source_count=("lifecycle_id", "count"),
            accepted_count=("accepted_flag", "sum"),
        )
        .reset_index()
    )
    rows["concentration_type"] = concentration_type
    return rows.sort_values(["split_scope", "candidate_name", "accepted_count"], ascending=[True, True, False]).reset_index(drop=True)


def build_displacement_pairs(accepted: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty:
        return pd.DataFrame()
    all_split = accepted[accepted["split_scope"].astype(str).eq("all")].copy()
    baseline = all_split[all_split["candidate_name"].eq("baseline_task639")].copy()
    rows = []
    baseline_ids = set(baseline["lifecycle_id"].astype(str))
    for candidate_name, candidate in all_split.groupby("candidate_name", dropna=False):
        if candidate_name == "baseline_task639":
            continue
        candidate_ids = set(candidate["lifecycle_id"].astype(str))
        added = candidate[~candidate["lifecycle_id"].astype(str).isin(baseline_ids)].sort_values(["entry_ts", "priority_rank", "lifecycle_id"]).reset_index(drop=True)
        removed = baseline[~baseline["lifecycle_id"].astype(str).isin(candidate_ids)].sort_values(["entry_ts", "lifecycle_id"]).reset_index(drop=True)
        pair_count = max(len(added), len(removed))
        for idx in range(pair_count):
            add = added.iloc[idx] if idx < len(added) else None
            rem = removed.iloc[idx] if idx < len(removed) else None
            rows.append(
                {
                    "candidate_name": candidate_name,
                    "pair_index": idx + 1,
                    "added_lifecycle_id": "" if add is None else add["lifecycle_id"],
                    "added_symbol": "" if add is None else add.get("symbol", ""),
                    "added_entry_ts": "" if add is None else add["entry_ts"],
                    "added_theme_id": "" if add is None else add.get("theme_id", ""),
                    "added_relation_state": "" if add is None else add.get("mechanism_relation_state", ""),
                    "added_return_costed_pct": "" if add is None else float(add.get("net_return_costed", 0.0)) * 100.0,
                    "removed_lifecycle_id": "" if rem is None else rem["lifecycle_id"],
                    "removed_symbol": "" if rem is None else rem.get("symbol", ""),
                    "removed_entry_ts": "" if rem is None else rem["entry_ts"],
                    "removed_theme_id": "" if rem is None else rem.get("theme_id", ""),
                    "removed_relation_state": "" if rem is None else rem.get("mechanism_relation_state", ""),
                    "removed_return_costed_pct": "" if rem is None else float(rem.get("net_return_costed", 0.0)) * 100.0,
                    "pair_return_delta_pct": (
                        ""
                        if add is None or rem is None
                        else (float(add.get("net_return_costed", 0.0)) - float(rem.get("net_return_costed", 0.0))) * 100.0
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_mdd_contribution_report(accepted: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty:
        return pd.DataFrame()
    rows = []
    all_split = accepted[accepted["split_scope"].astype(str).eq("all")].copy()
    for candidate_name, group in all_split.groupby("candidate_name", dropna=False):
        values = pd.to_numeric(group["net_return_costed"], errors="coerce")
        grid_row = grid[(grid["candidate_name"].eq(candidate_name)) & (grid["split_name"].eq("all"))]
        rows.append(
            {
                "candidate_name": candidate_name,
                "accepted_trade_count": int(len(group)),
                "losing_trade_count": int(values.lt(0).sum()),
                "large_loss_trade_count": int(values.le(-0.10).sum()),
                "entry_reduce_failure_count": int(values.le(-0.03).sum()),
                "sum_negative_return_pct": float(values[values.lt(0)].sum() * 100.0),
                "avg_return_pct": float(values.mean() * 100.0),
                "final_capital_usd": float(grid_row.iloc[0]["final_capital_usd"]) if not grid_row.empty else 0.0,
                "max_drawdown_pct": float(grid_row.iloc[0]["max_drawdown_pct"]) if not grid_row.empty else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values("final_capital_usd", ascending=False).reset_index(drop=True)


def build_decision(promotion: pd.DataFrame) -> pd.DataFrame:
    baseline = promotion[promotion["candidate_name"].eq("baseline_task639")].iloc[0]
    best = promotion.sort_values("all_final_capital_usd", ascending=False).iloc[0]
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    decision = "PRIORITY_RISK_CAP_TESTED_NO_PROMOTION_CANDIDATE"
    if promotion_count > 0:
        decision = "PRIORITY_RISK_CAP_PROMOTION_CANDIDATE_FOUND_NOT_ACCEPTED"
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
                "promotion_candidate_count": promotion_count,
                "trading_promotion_pass_flag": 0,
                "next_action": "If no risk cap passes, move to accepted-trade risk scoring rather than broad theme caps.",
            }
        ]
    )


def build_pass_fail(specs: pd.DataFrame, promotion: pd.DataFrame, cap_audit: pd.DataFrame, displacement_pairs: pd.DataFrame) -> pd.DataFrame:
    fixed = int(specs["fixed_hold_or_timing_override_flag"].sum())
    return_tuned_promoted = int(
        promotion[promotion["promotion_candidate_flag"].eq(1)]["candidate_name"]
        .isin(specs[specs["return_tuned_flag"].eq(1)]["candidate_name"])
        .sum()
    )
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    return pd.DataFrame(
        [
            {"gate": "no_fixed_hold_or_timing_override", "pass_flag": int(fixed == 0), "observed_value": f"violations={fixed}", "required_value": "risk caps preserve timing and exit"},
            {"gate": "risk_cap_candidates_tested", "pass_flag": int(len(specs) >= 4), "observed_value": f"candidates={len(specs)}", "required_value": "multiple cap candidates"},
            {"gate": "displacement_audit_built", "pass_flag": int(not displacement_pairs.empty), "observed_value": f"rows={len(displacement_pairs)}", "required_value": "added/removed trade audit exists"},
            {"gate": "no_return_tuned_promotion", "pass_flag": int(return_tuned_promoted == 0), "observed_value": f"return_tuned_promoted={return_tuned_promoted}", "required_value": "diagnostic return-tuned candidates cannot promote"},
            {"gate": "promotion_candidate_found", "pass_flag": int(promotion_count > 0), "observed_value": f"promotion_candidates={promotion_count}", "required_value": "candidate improves return drawdown validation and recent OOS"},
            {"gate": "strategy_accepted", "pass_flag": 0, "observed_value": "research diagnostic only", "required_value": "requires accepted strategy gates and live readiness"},
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    grid: pd.DataFrame,
    promotion: pd.DataFrame,
    cap_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task666 Priority Risk Cap Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Baseline: `${float(d['baseline_final_capital_usd']):.2f}`, MDD `{float(d['baseline_max_drawdown_pct']):.2f}%`.",
        f"- Best candidate: `{d['best_candidate_name']}` = `${float(d['best_candidate_final_capital_usd']):.2f}`, MDD `{float(d['best_candidate_max_drawdown_pct']):.2f}%`.",
        f"- Promotion candidates: `{int(d['promotion_candidate_count'])}`.",
        "",
        "## Quant Expert Report",
        "",
        "Task666 tests non-return-tuned risk caps on top of relation priority. It does not change entry timing, exits, fixed holds, or sizing.",
        "",
        "### Data Source And Source Readiness",
        "",
        "Input is the Task661 mechanism state panel rebuilt from Task659. No new source is introduced.",
        "",
        "### Exact Join Keys",
        "",
        "`lifecycle_id`, `entry_ts`, `simulated_exit_ts`, and theme/relation state fields.",
        "",
        "### Leakage Audit",
        "",
        "Promotion-eligible caps are predeclared structural caps. The MDD-bad-theme block is marked diagnostic and return-tuned.",
        "",
        "### Candidate Grid",
        "",
        table(grid),
        "",
        "### Promotion Report",
        "",
        table(promotion),
        "",
        "### Cap Audit",
        "",
        table(cap_audit),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "나쁜 slot 교체를 막는 risk cap을 테스트했습니다.",
        "",
        "좋은 후보를 너무 많이 죽이면 수익도 같이 죽습니다.",
        "",
        "그래서 승격은 return, MDD, validation, recent OOS가 모두 좋아질 때만 허용했습니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `priority_risk_cap_specs.csv`",
        "- `priority_risk_cap_candidate_grid.csv`",
        "- `priority_risk_cap_accepted_trades.csv`",
        "- `task666_capacity_allocation_panel.csv`",
        "- `task666_theme_concentration_audit.csv`",
        "- `task666_relation_concentration_audit.csv`",
        "- `task666_displacement_pairs.csv`",
        "- `task666_mdd_contribution_report.csv`",
        "- `task666_promotion_blockers.md`",
        "- `task_666_gpt_review_packet.md`",
        "- `task_666_gpt_review_response.md`",
        "- `priority_risk_cap_audit.csv`",
        "- `priority_risk_cap_promotion_report.csv`",
        "- `task_666_decision.csv`",
        "- `task_666_pass_fail_matrix.csv`",
        "- `artifact_manifest.csv`",
    ]
    lines = clean_no_background_section(lines)
    (out_dir / "task_666_priority_risk_cap_backtest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def clean_no_background_section(lines: list[str]) -> list[str]:
    out: list[str] = []
    skipping = False
    inserted = False
    for line in lines:
        if line == "## No-Background Decision-Maker Report":
            out.append(line)
            out.extend(
                [
                    "",
                    "좋은 우선순위는 살리고, 나쁜 slot 교체만 막는 risk cap을 테스트했습니다.",
                    "",
                    "좋은 후보까지 너무 많이 막으면 수익도 같이 죽습니다.",
                    "",
                    "그래서 수익, MDD, validation, recent OOS가 모두 좋아질 때만 승격합니다.",
                    "",
                ]
            )
            skipping = True
            inserted = True
            continue
        if skipping and line == "## Pass/Fail Matrix":
            skipping = False
            out.append(line)
            continue
        if skipping:
            continue
        out.append(line)
    return out if inserted else lines


def table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_No rows._"
    clipped = df.head(max_rows)
    cols = [str(c) for c in clipped.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
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
    result = build_task666_priority_risk_cap_backtest(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best={decision['best_candidate_name']} "
        f"promotion={int(decision['promotion_candidate_count'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
