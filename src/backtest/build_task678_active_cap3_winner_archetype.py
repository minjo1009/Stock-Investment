from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest import build_task673_677_setup_slot_exposure_action as t673
from src.backtest.build_task637_content_signal_account_backtest import (
    INITIAL_CAPITAL_USD,
    load_qqq_history,
    qqq_final_for_period,
)
from src.backtest.build_task659_theme_specific_relation_engine import QQQ_PATH


TASK678_DIR = Path("docs/reports/task_678_active_cap3_winner_archetype")
ACTIVE_CAP3 = "active_relation_cap3_reference"
TASK639 = "baseline_task639"
ACTIVE_CAP3_MAX10 = "active_relation_cap3_max10"
TASK639_MAX10 = "baseline_task639_max10"


def build_task678_program(
    *,
    task672_dir: Path = t673.TASK672_DIR,
    task676_dir: Path = t673.TASK676_DIR,
    qqq_path: Path = QQQ_PATH,
) -> dict[str, pd.DataFrame]:
    TASK678_DIR.mkdir(parents=True, exist_ok=True)

    panel = t673.load_task672_panel(task672_dir)
    panel = t673.add_setup_quality(panel)
    panel = t673.add_slot_value_ladder(panel)
    qqq = load_qqq_history(qqq_path)

    performance, accepted, allocation, curves = build_max_position_comparison(panel, qqq)
    active5 = accepted[(accepted["candidate_name"].eq(ACTIVE_CAP3)) & (accepted["split_scope"].eq("all"))].copy()
    active10 = accepted[(accepted["candidate_name"].eq(ACTIVE_CAP3_MAX10)) & (accepted["split_scope"].eq("all"))].copy()

    archetypes = build_winner_archetype_study(active5)
    same_symbol = build_same_symbol_divergence(active5)
    catalyst_path = build_catalyst_path_study(active5)
    preservation = build_winner_preservation_audit(task676_dir, active5)
    slot_competition = build_slot_competition_study(allocation, panel)
    max10_delta = build_max10_delta(active5, active10)
    decision = build_decision(performance, archetypes, preservation)
    pass_fail = build_pass_fail(performance, archetypes, same_symbol, catalyst_path, preservation, slot_competition)

    write_outputs(
        performance,
        accepted,
        allocation,
        archetypes,
        same_symbol,
        catalyst_path,
        preservation,
        slot_competition,
        max10_delta,
        decision,
        pass_fail,
    )

    return {
        "performance": performance,
        "accepted": accepted,
        "allocation": allocation,
        "curves": curves,
        "archetypes": archetypes,
        "same_symbol": same_symbol,
        "catalyst_path": catalyst_path,
        "preservation": preservation,
        "slot_competition": slot_competition,
        "max10_delta": max10_delta,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_max_position_comparison(panel: pd.DataFrame, qqq: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    specs = [
        (TASK639, t673.candidate(TASK639, "reference", "chronological", "none", 0, 0, 0, 0, "Task639 max5 reference."), 5),
        (ACTIVE_CAP3, t673.candidate(ACTIVE_CAP3, "reference", "relation_priority", "relation3", 0, 0, 0, 0, "Active relation cap3 max5 reference."), 5),
        (TASK639_MAX10, t673.candidate(TASK639_MAX10, "capacity_probe", "chronological", "none", 0, 1, 0, 0, "Task639 with max10 positions."), 10),
        (ACTIVE_CAP3_MAX10, t673.candidate(ACTIVE_CAP3_MAX10, "capacity_probe", "relation_priority", "relation3", 0, 1, 0, 0, "Active relation cap3 with max10 positions."), 10),
    ]
    original_max_positions = t673.MAX_POSITIONS
    rows: list[dict[str, object]] = []
    accepted_frames: list[pd.DataFrame] = []
    allocation_frames: list[pd.DataFrame] = []
    curve_frames: list[pd.DataFrame] = []
    try:
        for candidate_name, spec_dict, max_positions in specs:
            t673.MAX_POSITIONS = max_positions
            spec = pd.Series(spec_dict)
            for split_name in ["all", "validation", "recent_oos"]:
                scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)].copy()
                quality, accepted, allocation, curve = t673.simulate_candidate(scoped, spec)
                qqq_final = qqq_final_for_period(qqq, scoped)
                final = INITIAL_CAPITAL_USD * (1.0 + quality["capital_pnl_pct"] / 100.0)
                rows.append(
                    {
                        "candidate_name": candidate_name,
                        "split_name": split_name,
                        "max_positions": max_positions,
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
                        "return_used_in_assignment_flag": 0,
                        "label_used_in_assignment_flag": 0,
                        "future_price_used_in_assignment_flag": 0,
                    }
                )
                for frame, bucket in [(accepted, accepted_frames), (allocation, allocation_frames), (curve, curve_frames)]:
                    if not frame.empty:
                        tmp = frame.copy()
                        tmp["candidate_name"] = candidate_name
                        tmp["split_scope"] = split_name
                        tmp["max_positions"] = max_positions
                        bucket.append(tmp)
    finally:
        t673.MAX_POSITIONS = original_max_positions

    return (
        pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True),
        pd.concat(accepted_frames, ignore_index=True) if accepted_frames else pd.DataFrame(),
        pd.concat(allocation_frames, ignore_index=True) if allocation_frames else pd.DataFrame(),
        pd.concat(curve_frames, ignore_index=True) if curve_frames else pd.DataFrame(),
    )


def build_winner_archetype_study(active: pd.DataFrame) -> pd.DataFrame:
    work = active.copy()
    work["winner_archetype"] = work.apply(classify_winner_archetype, axis=1)
    work["net_return_costed_pct"] = pd.to_numeric(work["net_return_costed"], errors="coerce") * 100.0
    rows = []
    for archetype, group in work.groupby("winner_archetype", dropna=False):
        returns = pd.to_numeric(group["net_return_costed_pct"], errors="coerce")
        rows.append(
            {
                "winner_archetype": archetype,
                "trade_count": int(len(group)),
                "avg_return_costed_pct_eval_only": float(returns.mean()),
                "median_return_costed_pct_eval_only": float(returns.median()),
                "total_return_costed_pct_eval_only": float(returns.sum()),
                "win_rate_eval_only": float(returns.gt(0).mean()),
                "big_winner_count_eval_only": int(returns.ge(50.0).sum()),
                "failure_count_eval_only": int(returns.le(-10.0).sum()),
                "return_used_in_assignment_flag": 0,
                "label_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("total_return_costed_pct_eval_only", ascending=False).reset_index(drop=True)


def classify_winner_archetype(row: pd.Series) -> str:
    price = s(row.get("price_chart_acceptance_state", ""))
    setup = s(row.get("setup_quality_bucket", ""))
    theme = s(row.get("theme_leadership_state", ""))
    catalyst = s(row.get("company_catalyst_state", ""))
    multiday = s(row.get("symbol_multiday_setup_state", ""))
    relation = s(row.get("relation_transmission_state", ""))
    if price == "price_fragile_or_unconfirmed" or setup == "fragile_setup":
        return "explosive_fragile_continuation"
    if theme in {"narrow_leadership", "theme_leadership_expanding"}:
        return "theme_rotation_or_narrow_leader"
    if "extended" in price:
        return "late_extended_breakout"
    if catalyst in {"hard_company_catalyst", "multi_dimension_high_quality_catalyst"} and "company_price_confirmed" in relation:
        return "catalyst_repricing_confirmed"
    if multiday == "trend_persistence_near_high":
        return "steady_trend_persistence"
    if catalyst == "multi_signal_medium_catalyst":
        return "medium_signal_continuation"
    return "mixed_continuation"


def build_same_symbol_divergence(active: pd.DataFrame) -> pd.DataFrame:
    work = active.copy()
    work["net_return_costed_pct"] = pd.to_numeric(work["net_return_costed"], errors="coerce") * 100.0
    rows = []
    for symbol, group in work.groupby("symbol", dropna=False):
        returns = pd.to_numeric(group["net_return_costed_pct"], errors="coerce")
        if len(group) < 2:
            continue
        best = group.loc[returns.idxmax()]
        worst = group.loc[returns.idxmin()]
        rows.append(
            {
                "symbol": symbol,
                "trade_count": int(len(group)),
                "best_return_costed_pct_eval_only": float(best["net_return_costed_pct"]),
                "best_entry_ts": best["entry_ts"],
                "best_archetype": classify_winner_archetype(best),
                "best_setup": best.get("setup_quality_bucket", ""),
                "best_relation": best.get("relation_transmission_state", ""),
                "worst_return_costed_pct_eval_only": float(worst["net_return_costed_pct"]),
                "worst_entry_ts": worst["entry_ts"],
                "worst_archetype": classify_winner_archetype(worst),
                "worst_setup": worst.get("setup_quality_bucket", ""),
                "worst_relation": worst.get("relation_transmission_state", ""),
                "spread_pct_points_eval_only": float(best["net_return_costed_pct"] - worst["net_return_costed_pct"]),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("spread_pct_points_eval_only", ascending=False).reset_index(drop=True)


def build_catalyst_path_study(active: pd.DataFrame) -> pd.DataFrame:
    work = active.copy()
    work["catalyst_path"] = work.apply(classify_catalyst_path, axis=1)
    work["net_return_costed_pct"] = pd.to_numeric(work["net_return_costed"], errors="coerce") * 100.0
    group_cols = ["catalyst_path", "company_catalyst_state", "relation_transmission_state"]
    rows = []
    for keys, group in work.groupby(group_cols, dropna=False):
        returns = pd.to_numeric(group["net_return_costed_pct"], errors="coerce")
        rows.append(
            {
                "catalyst_path": keys[0],
                "company_catalyst_state": keys[1],
                "relation_transmission_state": keys[2],
                "trade_count": int(len(group)),
                "avg_return_costed_pct_eval_only": float(returns.mean()),
                "win_rate_eval_only": float(returns.gt(0).mean()),
                "big_winner_count_eval_only": int(returns.ge(50.0).sum()),
                "failure_count_eval_only": int(returns.le(-10.0).sum()),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["big_winner_count_eval_only", "avg_return_costed_pct_eval_only"], ascending=[False, False]).reset_index(drop=True)


def classify_catalyst_path(row: pd.Series) -> str:
    contract = num(row.get("positive_contract_customer_count", 0))
    backlog = num(row.get("positive_backlog_order_count", 0))
    guidance = num(row.get("positive_guidance_up_count", 0))
    margin_supply = num(row.get("positive_margin_supply_combo_count", 0))
    supply = num(row.get("content_supply_demand_count", 0))
    weak_revenue = num(row.get("positive_revenue_talk_weak_count", 0))
    negative = num(row.get("content_negative_score_flag", 0))
    if contract > 0 and (supply > 0 or margin_supply > 0 or backlog > 0):
        return "contract_plus_supply_or_backlog"
    if guidance > 0 or margin_supply > 0:
        return "guidance_margin_upgrade"
    if contract > 0:
        return "contract_customer_only"
    if supply > 0 or backlog > 0:
        return "supply_demand_or_backlog"
    if negative > 0:
        return "negative_event_rebound"
    if weak_revenue > 0:
        return "weak_revenue_talk"
    return "unclear_or_multi_signal"


def build_winner_preservation_audit(task676_dir: Path, active5: pd.DataFrame) -> pd.DataFrame:
    path = task676_dir / "task676_accepted_trades.csv"
    historical = pd.read_csv(path) if path.exists() else pd.DataFrame()
    if historical.empty:
        return pd.DataFrame()
    active_ids = set(active5["lifecycle_id"].astype(str))
    active_returns = active5.set_index(active5["lifecycle_id"].astype(str))["net_return_costed"]
    rows = []
    for candidate_name, group in historical[historical["split_scope"].astype(str).eq("all")].groupby("candidate_name", dropna=False):
        ids = set(group["lifecycle_id"].astype(str))
        removed_ids = active_ids - ids
        removed_returns = pd.to_numeric(active_returns.loc[list(removed_ids)] if removed_ids else pd.Series(dtype=float), errors="coerce")
        rows.append(
            {
                "candidate_name": candidate_name,
                "active_cap3_trade_count": int(len(active_ids)),
                "candidate_trade_count": int(len(ids)),
                "removed_active_cap3_trade_count": int(len(removed_ids)),
                "removed_active_cap3_avg_return_pct_eval_only": float(removed_returns.mean() * 100.0) if len(removed_returns) else 0.0,
                "removed_active_cap3_big_winner_count_eval_only": int(removed_returns.ge(0.50).sum()) if len(removed_returns) else 0,
                "removed_active_cap3_failure_count_eval_only": int(removed_returns.le(-0.10).sum()) if len(removed_returns) else 0,
                "winner_preservation_pass_flag": int((len(removed_returns) == 0) or int(removed_returns.ge(0.50).sum()) == 0),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["removed_active_cap3_big_winner_count_eval_only", "removed_active_cap3_avg_return_pct_eval_only"], ascending=[False, False]).reset_index(drop=True)


def build_slot_competition_study(allocation: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    if allocation.empty:
        return pd.DataFrame()
    panel_returns = panel[["lifecycle_id", "net_return_from_entry"]].copy()
    panel_returns["lifecycle_id"] = panel_returns["lifecycle_id"].astype(str)
    work = allocation.copy()
    work["lifecycle_id"] = work["lifecycle_id"].astype(str)
    work = work.merge(panel_returns, on="lifecycle_id", how="left", suffixes=("", "_panel"))
    work["net_return_costed_eval"] = pd.to_numeric(work["net_return_from_entry"], errors="coerce") - t673.COST_BPS / 10000.0
    rows = []
    for keys, group in work[work["split_scope"].eq("all")].groupby(["candidate_name", "max_positions", "entry_ts"], dropna=False):
        candidate_name, max_positions, entry_ts = keys
        blocked = group[pd.to_numeric(group["accepted_flag"], errors="coerce").eq(0)]
        accepted = group[pd.to_numeric(group["accepted_flag"], errors="coerce").eq(1)]
        blocked_returns = pd.to_numeric(blocked["net_return_costed_eval"], errors="coerce")
        accepted_returns = pd.to_numeric(accepted["net_return_costed_eval"], errors="coerce")
        rows.append(
            {
                "candidate_name": candidate_name,
                "max_positions": int(max_positions),
                "entry_ts": entry_ts,
                "candidate_count_at_ts": int(len(group)),
                "accepted_count_at_ts": int(len(accepted)),
                "blocked_count_at_ts": int(len(blocked)),
                "accepted_avg_return_pct_eval_only": float(accepted_returns.mean() * 100.0) if len(accepted_returns) else 0.0,
                "blocked_avg_return_pct_eval_only": float(blocked_returns.mean() * 100.0) if len(blocked_returns) else 0.0,
                "blocked_big_winner_count_eval_only": int(blocked_returns.ge(0.50).sum()) if len(blocked_returns) else 0,
                "blocked_failure_count_eval_only": int(blocked_returns.le(-0.10).sum()) if len(blocked_returns) else 0,
                "max_positions_full_blocks": int(blocked["allocation_reason"].astype(str).eq("max_positions_full").sum()),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["blocked_big_winner_count_eval_only", "candidate_count_at_ts"], ascending=[False, False]).reset_index(drop=True)


def build_max10_delta(active5: pd.DataFrame, active10: pd.DataFrame) -> pd.DataFrame:
    ids5 = set(active5["lifecycle_id"].astype(str))
    ids10 = set(active10["lifecycle_id"].astype(str))
    rows = []
    for label, sub in [
        ("common", active10[active10["lifecycle_id"].astype(str).isin(ids5 & ids10)]),
        ("added_by_max10", active10[active10["lifecycle_id"].astype(str).isin(ids10 - ids5)]),
        ("removed_by_max10", active5[active5["lifecycle_id"].astype(str).isin(ids5 - ids10)]),
    ]:
        returns = pd.to_numeric(sub.get("net_return_costed", pd.Series(dtype=float)), errors="coerce")
        rows.append(
            {
                "bucket": label,
                "trade_count": int(len(sub)),
                "avg_return_costed_pct_eval_only": float(returns.mean() * 100.0) if len(returns) else 0.0,
                "win_rate_eval_only": float(returns.gt(0).mean()) if len(returns) else 0.0,
                "big_winner_count_eval_only": int(returns.ge(0.50).sum()) if len(returns) else 0,
                "failure_count_eval_only": int(returns.le(-0.10).sum()) if len(returns) else 0,
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_decision(performance: pd.DataFrame, archetypes: pd.DataFrame, preservation: pd.DataFrame) -> pd.DataFrame:
    active5 = performance[(performance["candidate_name"].eq(ACTIVE_CAP3)) & (performance["split_name"].eq("all"))].iloc[0]
    active10 = performance[(performance["candidate_name"].eq(ACTIVE_CAP3_MAX10)) & (performance["split_name"].eq("all"))].iloc[0]
    best_arch = archetypes.iloc[0] if not archetypes.empty else pd.Series(dtype=object)
    removed_big_winners = int(pd.to_numeric(preservation.get("removed_active_cap3_big_winner_count_eval_only", pd.Series(dtype=int)), errors="coerce").max()) if not preservation.empty else 0
    return pd.DataFrame(
        [
            {
                "task_id": "Task678",
                "decision": "ACTIVE_CAP3_WINNER_ARCHETYPE_STUDY_COMPLETE_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "active_cap3_max5_final_capital_usd": float(active5["final_capital_usd"]),
                "active_cap3_max5_mdd_pct": float(active5["max_drawdown_pct"]),
                "active_cap3_max10_final_capital_usd": float(active10["final_capital_usd"]),
                "active_cap3_max10_mdd_pct": float(active10["max_drawdown_pct"]),
                "top_winner_archetype": best_arch.get("winner_archetype", ""),
                "top_winner_archetype_total_return_pct_eval_only": float(best_arch.get("total_return_costed_pct_eval_only", 0.0)),
                "max_removed_big_winners_by_prior_wrappers": removed_big_winners,
                "next_action": "Build rules around winner-archetype preservation and slot competition before adding any new cap or permission layer.",
            }
        ]
    )


def build_pass_fail(
    performance: pd.DataFrame,
    archetypes: pd.DataFrame,
    same_symbol: pd.DataFrame,
    catalyst_path: pd.DataFrame,
    preservation: pd.DataFrame,
    slot_competition: pd.DataFrame,
) -> pd.DataFrame:
    active10 = performance[(performance["candidate_name"].eq(ACTIVE_CAP3_MAX10)) & (performance["split_name"].eq("all"))].iloc[0]
    active5 = performance[(performance["candidate_name"].eq(ACTIVE_CAP3)) & (performance["split_name"].eq("all"))].iloc[0]
    return pd.DataFrame(
        [
            gate("winner_archetype_study_built", not archetypes.empty, f"rows={len(archetypes)}", "winner archetype rows"),
            gate("same_symbol_divergence_built", not same_symbol.empty, f"rows={len(same_symbol)}", "same symbol divergence rows"),
            gate("catalyst_path_study_built", not catalyst_path.empty, f"rows={len(catalyst_path)}", "catalyst path rows"),
            gate("winner_preservation_audit_built", not preservation.empty, f"rows={len(preservation)}", "preservation rows"),
            gate("slot_competition_study_built", not slot_competition.empty, f"rows={len(slot_competition)}", "slot competition rows"),
            gate("max10_comparison_built", not performance.empty and ACTIVE_CAP3_MAX10 in set(performance["candidate_name"]), "max10 present", "active cap3 max10"),
            gate("max10_beats_active_cap3_max5_return", float(active10["final_capital_usd"]) > float(active5["final_capital_usd"]), f"max10={float(active10['final_capital_usd']):.2f}, max5={float(active5['final_capital_usd']):.2f}", "max10 final greater than max5"),
            gate("max10_mdd_not_worse_than_active_cap3_max5", float(active10["max_drawdown_pct"]) >= float(active5["max_drawdown_pct"]), f"max10={float(active10['max_drawdown_pct']):.2f}, max5={float(active5['max_drawdown_pct']):.2f}", "max10 MDD not worse"),
            gate("strategy_accepted", False, "research only", "promotion gates require new predeclared rules and OOS validation"),
        ]
    )


def write_outputs(
    performance: pd.DataFrame,
    accepted: pd.DataFrame,
    allocation: pd.DataFrame,
    archetypes: pd.DataFrame,
    same_symbol: pd.DataFrame,
    catalyst_path: pd.DataFrame,
    preservation: pd.DataFrame,
    slot_competition: pd.DataFrame,
    max10_delta: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task678_max_position_comparison.csv": performance,
        "task678_accepted_trades.csv": accepted,
        "task678_allocation_panel.csv": allocation,
        "task678_winner_archetype_study.csv": archetypes,
        "task678_same_symbol_divergence.csv": same_symbol,
        "task678_catalyst_path_study.csv": catalyst_path,
        "task678_winner_preservation_audit.csv": preservation,
        "task678_slot_competition_study.csv": slot_competition,
        "task678_max10_delta.csv": max10_delta,
        "task_678_decision.csv": decision,
        "task_678_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK678_DIR / name, index=False)
    (TASK678_DIR / "task_678_active_cap3_winner_archetype.md").write_text(
        render_report(performance, archetypes, same_symbol, catalyst_path, preservation, slot_competition, max10_delta, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK678_DIR, TASK678_DIR / "artifact_manifest.csv")


def render_report(
    performance: pd.DataFrame,
    archetypes: pd.DataFrame,
    same_symbol: pd.DataFrame,
    catalyst_path: pd.DataFrame,
    preservation: pd.DataFrame,
    slot_competition: pd.DataFrame,
    max10_delta: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    active5 = performance[(performance["candidate_name"].eq(ACTIVE_CAP3)) & (performance["split_name"].eq("all"))].iloc[0]
    active10 = performance[(performance["candidate_name"].eq(ACTIVE_CAP3_MAX10)) & (performance["split_name"].eq("all"))].iloc[0]
    task639 = performance[(performance["candidate_name"].eq(TASK639)) & (performance["split_name"].eq("all"))].iloc[0]
    task63910 = performance[(performance["candidate_name"].eq(TASK639_MAX10)) & (performance["split_name"].eq("all"))].iloc[0]
    top_arch = markdown_table(archetypes.head(5))
    top_symbols = markdown_table(same_symbol.head(8))
    top_catalyst = markdown_table(catalyst_path.head(8))
    top_preservation = markdown_table(preservation.head(8))
    top_slot = markdown_table(slot_competition.head(8))
    max10 = markdown_table(max10_delta)
    perf = markdown_table(performance)
    gates = markdown_table(pass_fail)
    return f"""# Task678 Active Cap3 Winner Archetype

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: active relation cap3 was decomposed into winner archetypes, same-symbol divergence, catalyst paths, winner preservation, slot competition, and max5 versus max10 capacity.
- Key metrics: Task639 max5 ${float(task639['final_capital_usd']):,.2f} / MDD {float(task639['max_drawdown_pct']):.2f}%; active cap3 max5 ${float(active5['final_capital_usd']):,.2f} / MDD {float(active5['max_drawdown_pct']):.2f}%; Task639 max10 ${float(task63910['final_capital_usd']):,.2f} / MDD {float(task63910['max_drawdown_pct']):.2f}%; active cap3 max10 ${float(active10['final_capital_usd']):,.2f} / MDD {float(active10['max_drawdown_pct']):.2f}%.
- Next action: do not add another cap until winner archetype preservation and slot competition rules are predeclared and OOS-tested.

## Quant Expert Report

### Data source and source readiness

- Inputs: Task672 current-data state axis panel, Task676 accepted trades, QQQ daily benchmark.
- Quote, trade, NBBO, and microstructure are not used.
- GPT is not used as a source of truth or an assignment input.

### Exact join keys

- Portfolio replay uses `lifecycle_id`, `entry_ts`, and existing `simulated_exit_ts`.
- Winner preservation compares accepted-trade sets by `lifecycle_id`.
- Slot competition merges allocation rows back to the candidate panel by `lifecycle_id` only.

### Leakage audit

- Archetype, catalyst path, capacity, and slot logic use entry-time/current panel columns only.
- Return fields are evaluation-only and marked with `return_used_in_assignment_flag=0`.
- Labels, future price, symbol blacklist, and theme blacklist are not used.

### Split/OOS metrics

{perf}

### Winner archetype study

{top_arch}

### Same-symbol divergence

{top_symbols}

### Catalyst path study

{top_catalyst}

### Winner preservation audit

{top_preservation}

### Slot competition study

{top_slot}

### Max10 delta

{max10}

### Cost/slippage stress

- The replay preserves the existing 50 bps cost treatment from Task673-677.
- No new exit, hold period, timing, or slippage override is introduced.

### Remaining blockers

- The winner archetype taxonomy is diagnostic and not yet a trading rule.
- Max10 is a capacity probe, not a deployment recommendation.
- Promotion requires predeclared rules, split/OOS validation, leakage audit, and cost stress.

## No-Background Decision-Maker Report

- What happened: active cap3 was returned to the center and decomposed by how winners are made, not by how losses can be capped.
- Why it matters: prior conservative layers likely damaged the few trades that created most of the profit.
- Whether this changes capital readiness: no. It remains NOT_ACCEPTED and FORBIDDEN for real capital.
- Plain-language next step: preserve the big-winner patterns first, then design risk control around not killing those winners.

## Artifact Manifest

- Inputs: Task672 panel, Task676 accepted trades, QQQ benchmark.
- Outputs: all CSVs in this directory plus `artifact_manifest.csv`.
- Validation commands: `python -m unittest tests.test_task678_active_cap3_winner_archetype`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{gates}
"""


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "pass_flag": int(bool(passed)),
        "observed": observed,
        "required": required,
    }


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    limited = frame.copy()
    cols = list(limited.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in limited.iterrows():
        values = [format_markdown_cell(row[col]) for col in cols]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def format_markdown_cell(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return text


def s(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def num(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task672-dir", type=Path, default=t673.TASK672_DIR)
    parser.add_argument("--task676-dir", type=Path, default=t673.TASK676_DIR)
    parser.add_argument("--qqq-path", type=Path, default=QQQ_PATH)
    args = parser.parse_args()
    build_task678_program(task672_dir=args.task672_dir, task676_dir=args.task676_dir, qqq_path=args.qqq_path)
    print(f"[Task678] wrote {TASK678_DIR}")


if __name__ == "__main__":
    main()
