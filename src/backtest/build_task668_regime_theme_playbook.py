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


TASK_ID = "Task668"
REPORT_DIR = Path("docs/reports/task_668_regime_theme_playbook")
PRIORITY_RULE = "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse"
BASELINE_CANDIDATE = "baseline_task639"


def build_task668_regime_theme_playbook(
    *,
    task659_panel_path: Path = TASK659_PANEL,
    qqq_path: Path = QQQ_PATH,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = build_mechanism_state_panel(load_task659_panel(task659_panel_path), build_institutional_transmission_template())
    core = add_playbook_columns(add_priority(task639_core(panel), PRIORITY_RULE))
    qqq = load_qqq_history(qqq_path)
    specs = build_candidate_specs()
    grid, accepted, allocation, equity_curve = build_candidate_grid(core, specs, qqq)
    playbook_perf = build_playbook_performance(accepted)
    transition = build_transition_matrix(core)
    mdd_windows = build_mdd_windows(equity_curve)
    mdd_audit = build_mdd_audit(accepted, mdd_windows)
    promotion = build_promotion_report(grid, specs)
    decision = build_decision(promotion)
    pass_fail = build_pass_fail(specs, promotion, accepted, allocation, playbook_perf, transition, mdd_audit)

    specs.to_csv(out_dir / "task668_candidate_specs.csv", index=False, encoding="utf-8-sig")
    core.to_csv(out_dir / "task668_playbook_panel.csv", index=False, encoding="utf-8-sig")
    grid.to_csv(out_dir / "task668_candidate_grid.csv", index=False, encoding="utf-8-sig")
    accepted.to_csv(out_dir / "task668_accepted_trades.csv", index=False, encoding="utf-8-sig")
    allocation.to_csv(out_dir / "task668_capacity_decision_panel.csv", index=False, encoding="utf-8-sig")
    equity_curve.to_csv(out_dir / "task668_equity_curve.csv", index=False, encoding="utf-8-sig")
    playbook_perf.to_csv(out_dir / "task668_playbook_performance.csv", index=False, encoding="utf-8-sig")
    transition.to_csv(out_dir / "task668_transition_matrix.csv", index=False, encoding="utf-8-sig")
    mdd_windows.to_csv(out_dir / "task668_mdd_windows.csv", index=False, encoding="utf-8-sig")
    mdd_audit.to_csv(out_dir / "task668_mdd_interval_audit.csv", index=False, encoding="utf-8-sig")
    promotion.to_csv(out_dir / "task668_promotion_report.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_668_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_668_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_promotion_blocker(out_dir, decision, promotion)
    write_report(out_dir, decision, grid, playbook_perf, transition, mdd_audit, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "specs": specs,
        "playbook_panel": core,
        "candidate_grid": grid,
        "accepted": accepted,
        "allocation": allocation,
        "equity_curve": equity_curve,
        "playbook_perf": playbook_perf,
        "transition": transition,
        "mdd_windows": mdd_windows,
        "mdd_audit": mdd_audit,
        "promotion": promotion,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_candidate_specs() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_name": BASELINE_CANDIDATE,
                "candidate_type": "baseline",
                "priority_mode": "chronological",
                "relation_cap_mode": "none",
                "sizing_mode": "equal",
                "block_research_only_flag": 0,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Task639 chronological baseline.",
            },
            {
                "candidate_name": "active_relation_cap3_reference",
                "candidate_type": "reference",
                "priority_mode": "relation_priority",
                "relation_cap_mode": "static3",
                "sizing_mode": "equal",
                "block_research_only_flag": 0,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Task666/667 active relation cap3 reference.",
            },
            {
                "candidate_name": "playbook_priority_only",
                "candidate_type": "predeclared_playbook_priority",
                "priority_mode": "playbook_priority",
                "relation_cap_mode": "static3",
                "sizing_mode": "equal",
                "block_research_only_flag": 0,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Within the same timestamp, prioritize stronger regime-theme-company playbooks.",
            },
            {
                "candidate_name": "playbook_dynamic_cap",
                "candidate_type": "predeclared_playbook_cap",
                "priority_mode": "playbook_priority",
                "relation_cap_mode": "playbook_dynamic",
                "sizing_mode": "equal",
                "block_research_only_flag": 0,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Use playbook-specific active relation caps.",
            },
            {
                "candidate_name": "playbook_contextual_sizing",
                "candidate_type": "predeclared_playbook_sizing",
                "priority_mode": "playbook_priority",
                "relation_cap_mode": "static3",
                "sizing_mode": "playbook_contextual",
                "block_research_only_flag": 0,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Size by playbook, catalyst, price acceptance, extension, and theme leadership.",
            },
            {
                "candidate_name": "relation_priority_playbook_lite_sizing",
                "candidate_type": "predeclared_playbook_sizing",
                "priority_mode": "relation_priority",
                "relation_cap_mode": "static3",
                "sizing_mode": "playbook_lite",
                "block_research_only_flag": 0,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Keep active relation cap3 ordering and only lightly reduce weak playbooks.",
            },
            {
                "candidate_name": "relation_priority_block_research_only",
                "candidate_type": "predeclared_playbook_filter",
                "priority_mode": "relation_priority",
                "relation_cap_mode": "static3",
                "sizing_mode": "equal",
                "block_research_only_flag": 1,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Keep active relation cap3 ordering but block defensive research-only playbooks.",
            },
            {
                "candidate_name": "playbook_priority_lite_sizing",
                "candidate_type": "predeclared_playbook_sizing",
                "priority_mode": "playbook_priority",
                "relation_cap_mode": "static3",
                "sizing_mode": "playbook_lite",
                "block_research_only_flag": 0,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Use playbook priority with only light weak-playbook sizing.",
            },
            {
                "candidate_name": "playbook_priority_cap_sizing",
                "candidate_type": "predeclared_playbook_combo",
                "priority_mode": "playbook_priority",
                "relation_cap_mode": "playbook_dynamic",
                "sizing_mode": "playbook_contextual",
                "block_research_only_flag": 0,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Playbook priority, playbook caps, and contextual sizing together.",
            },
            {
                "candidate_name": "playbook_block_research_only",
                "candidate_type": "predeclared_playbook_filter",
                "priority_mode": "playbook_priority",
                "relation_cap_mode": "playbook_dynamic",
                "sizing_mode": "playbook_contextual",
                "block_research_only_flag": 1,
                "diagnostic_only_flag": 0,
                "return_tuned_flag": 0,
                "fixed_hold_or_timing_override_flag": 0,
                "description": "Same as combo, but defensive research-only playbooks cannot consume slots.",
            },
        ]
    )


def add_playbook_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["market_state"] = out.apply(classify_market_state, axis=1)
    out["theme_state"] = out.apply(classify_theme_state, axis=1)
    out["playbook_id"] = out.apply(classify_playbook, axis=1)
    out["playbook_rank"] = out["playbook_id"].map(playbook_rank).fillna(90).astype(int)
    out["theme_rotation_data_ready_flag"] = out[["theme_ret20_prev", "theme_breadth20_prev", "theme_volume_ratio_prev"]].notna().all(axis=1).astype(int)
    out["finance_theme_available_flag"] = int("financials" in set(out["theme_id"].astype(str)))
    return out


def classify_market_state(row: pd.Series) -> str:
    macro = str(row.get("macro_overall_state", ""))
    score = f(row.get("broad_market_score", 0.0))
    stress = f(row.get("broad_market_stress", 0.0))
    breadth = f(row.get("breadth_20d", 0.0))
    market_ret = f(row.get("market_ret_20d", 0.0))
    if macro == "macro_hostile" or score < 50.0 or stress >= 45.0 or breadth < 0.45:
        return "broad_risk_off"
    if macro == "macro_supportive" and score >= 70.0 and stress < 35.0 and market_ret >= 0.0:
        return "broad_risk_on"
    return "mixed_rotation_tape"


def classify_theme_state(row: pd.Series) -> str:
    theme = str(row.get("theme_id", ""))
    regime = str(row.get("theme_regime_state_v4", ""))
    market = str(row.get("market_state", ""))
    ret20 = f(row.get("theme_ret20_prev", 0.0))
    breadth = f(row.get("theme_breadth20_prev", 0.0))
    volume = f(row.get("theme_volume_ratio_prev", 1.0))
    defensive_theme = theme in {"biotech_glp1_healthcare"}
    if market != "broad_risk_on" and defensive_theme and ret20 >= 0.03 and breadth >= 0.65:
        return "defensive_rotation"
    if regime == "persistent_theme_leader" and ret20 >= 0.15 and breadth >= 0.80:
        return "re_acceleration"
    if ret20 >= 0.12 and breadth >= 0.80 and volume >= 0.90:
        return "leadership_expanding"
    if regime == "narrow_theme_leader" or (ret20 >= 0.12 and breadth < 0.65):
        return "narrow_leadership"
    if ret20 < 0.03 or breadth < 0.60 or volume < 0.75:
        return "leadership_fading"
    return "neutral_participation"


def classify_playbook(row: pd.Series) -> str:
    market = str(row.get("market_state", ""))
    theme = str(row.get("theme_state", ""))
    relation = str(row.get("mechanism_relation_state", ""))
    catalyst = str(row.get("catalyst_quality_tier", ""))
    price = str(row.get("price_acceptance_state", ""))
    strong_catalyst = catalyst in {"very_strong_catalyst", "strong_catalyst"}
    strong_price = price == "price_acceptance_strong"
    strong_relation = relation in {"mechanism_reinforcing_company_positive", "mechanism_offsetting_company_positive"}
    if relation == "sparse_mechanism_cell":
        return "research_only_sparse"
    if market == "broad_risk_off" and theme == "leadership_fading" and not (strong_catalyst and strong_price):
        return "defensive_research_only"
    if market == "broad_risk_on" and theme in {"leadership_expanding", "re_acceleration"} and strong_catalyst and strong_price and strong_relation:
        return "aggressive_leadership"
    if theme in {"leadership_expanding", "re_acceleration", "defensive_rotation"} and strong_catalyst and strong_price:
        return "rotation_selective"
    if theme == "narrow_leadership" and strong_catalyst and strong_price:
        return "narrow_leader_selective"
    if theme == "leadership_fading" or price != "price_acceptance_strong":
        return "confirmation_required"
    return "normal_participation"


def playbook_rank(playbook: str) -> int:
    return {
        "aggressive_leadership": 10,
        "rotation_selective": 20,
        "narrow_leader_selective": 30,
        "normal_participation": 40,
        "confirmation_required": 60,
        "defensive_research_only": 80,
        "research_only_sparse": 90,
    }.get(playbook, 70)


def build_candidate_grid(core: pd.DataFrame, specs: pd.DataFrame, qqq: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    accepted_frames = []
    allocation_frames = []
    curve_frames = []
    for _, spec in specs.iterrows():
        for split_name in ["all", "validation", "recent_oos"]:
            scoped = core if split_name == "all" else core[core["split_name"].astype(str).eq(split_name)].copy()
            quality, accepted, allocation, curve = simulate(scoped, spec)
            qqq_final = qqq_final_for_period(qqq, scoped)
            final = INITIAL_CAPITAL_USD * (1.0 + quality["capital_pnl_pct"] / 100.0)
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


def simulate(panel: pd.DataFrame, spec: pd.Series) -> tuple[dict[str, float], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if panel.empty:
        return empty_quality(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    priority_mode = str(spec["priority_mode"])
    if priority_mode == "chronological":
        sort_cols = ["entry_ts", "lifecycle_id"]
    elif priority_mode == "relation_priority":
        sort_cols = ["entry_ts", "priority_rank", "lifecycle_id"]
    else:
        sort_cols = ["entry_ts", "playbook_rank", "priority_rank", "lifecycle_id"]
    ordered = panel.sort_values(sort_cols, kind="mergesort").reset_index(drop=True)
    ordered["net_return_costed"] = pd.to_numeric(ordered["net_return_from_entry"], errors="coerce") - COST_BPS / 10000.0
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    allocation_rows: list[dict[str, object]] = []
    curve_rows = [{"event_ts": ordered["entry_ts"].min(), "equity": equity, "drawdown_pct": 0.0, "event_type": "start"}]

    def close_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= current_ts:
                equity += float(pos["capital"]) * float(pos["return"])
                peak = max(peak, equity)
                curve_rows.append({"event_ts": pos["exit_ts"], "equity": equity, "drawdown_pct": (equity / max(peak, 1e-9) - 1.0) * 100.0, "event_type": "close"})
            else:
                still.append(pos)
        open_positions = still

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_until(entry_ts)
        if len(open_positions) >= MAX_POSITIONS:
            allocation_rows.append(allocation_record(row, 0, "max_positions_full", 0.0))
            continue
        if int(spec["block_research_only_flag"]) == 1 and str(row["playbook_id"]) in {"defensive_research_only", "research_only_sparse"}:
            allocation_rows.append(allocation_record(row, 0, "blocked_research_only_playbook", 0.0))
            continue
        cap = active_relation_cap(row, spec)
        relation_count = sum(1 for pos in open_positions if str(pos.get("mechanism_relation_state", "")) == str(row.get("mechanism_relation_state", "")))
        if relation_count >= cap:
            allocation_rows.append(allocation_record(row, 0, "active_relation_playbook_cap", 0.0))
            continue
        size = size_multiplier(row, spec)
        capital = equity / float(MAX_POSITIONS) * size
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_costed"],
                "mechanism_relation_state": row.get("mechanism_relation_state", ""),
                "theme_id": row.get("theme_id", ""),
            }
        )
        accepted = dict(row)
        accepted["size_multiplier"] = size
        accepted["position_capital_fraction"] = capital
        accepted_rows.append(accepted)
        allocation_rows.append(allocation_record(row, 1, "accepted", size))
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


def active_relation_cap(row: dict[str, object], spec: pd.Series) -> int:
    mode = str(spec["relation_cap_mode"])
    if mode == "none":
        return 999
    if mode == "static3":
        return 3
    if mode == "playbook_dynamic":
        playbook = str(row.get("playbook_id", ""))
        if playbook == "aggressive_leadership":
            return 3
        if playbook in {"rotation_selective", "narrow_leader_selective", "normal_participation"}:
            return 2
        return 1
    return 3


def size_multiplier(row: dict[str, object], spec: pd.Series) -> float:
    sizing_mode = str(spec["sizing_mode"])
    if sizing_mode not in {"playbook_contextual", "playbook_lite"}:
        return 1.0
    playbook = str(row.get("playbook_id", ""))
    catalyst = str(row.get("catalyst_quality_tier", ""))
    price = str(row.get("price_acceptance_state", ""))
    extension = f(row.get("intraday_ret_from_open", 0.0))
    range_pos = f(row.get("range_pos", 0.0))
    high_beta = str(row.get("theme_id", "")) in {"ai_semiconductors", "crypto_fintech", "ev_autonomy_mobility", "data_devops_software", "cybersecurity", "aerospace_defense_space"}
    strong_setup = catalyst in {"very_strong_catalyst", "strong_catalyst"} and price == "price_acceptance_strong" and playbook in {"aggressive_leadership", "rotation_selective"}
    if strong_setup:
        return 1.0
    if sizing_mode == "playbook_lite":
        if playbook in {"defensive_research_only", "research_only_sparse"}:
            return 0.70
        if playbook == "confirmation_required" and high_beta and (extension >= 0.04 or range_pos >= 0.98):
            return 0.85
        return 1.0
    size = 1.0
    if playbook in {"confirmation_required", "narrow_leader_selective"}:
        size *= 0.75
    if playbook in {"defensive_research_only", "research_only_sparse"}:
        size *= 0.50
    if high_beta and not strong_setup:
        size *= 0.80
    if extension >= 0.04 or range_pos >= 0.98:
        size *= 0.85
    return float(max(0.35, min(1.0, size)))


def allocation_record(row: dict[str, object], accepted_flag: int, reason: str, size: float) -> dict[str, object]:
    return {
        "lifecycle_id": row.get("lifecycle_id", ""),
        "symbol": row.get("symbol", ""),
        "entry_ts": row.get("entry_ts", ""),
        "split_name": row.get("split_name", ""),
        "theme_id": row.get("theme_id", ""),
        "market_state": row.get("market_state", ""),
        "theme_state": row.get("theme_state", ""),
        "playbook_id": row.get("playbook_id", ""),
        "mechanism_relation_state": row.get("mechanism_relation_state", ""),
        "catalyst_quality_tier": row.get("catalyst_quality_tier", ""),
        "price_acceptance_state": row.get("price_acceptance_state", ""),
        "accepted_flag": accepted_flag,
        "allocation_reason": reason,
        "size_multiplier": size,
        "net_return_costed": row.get("net_return_costed", ""),
    }


def build_playbook_performance(accepted: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in accepted.groupby(["candidate_name", "split_scope", "playbook_id"], dropna=False):
        candidate, split, playbook = keys
        returns = pd.to_numeric(group["net_return_costed"], errors="coerce")
        rows.append(
            {
                "candidate_name": candidate,
                "split_scope": split,
                "playbook_id": playbook,
                "trade_count": int(len(group)),
                "avg_return_pct": float(returns.mean() * 100.0),
                "win_rate": float(returns.gt(0).mean()),
                "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
                "avg_size_multiplier": float(pd.to_numeric(group["size_multiplier"], errors="coerce").mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["split_scope", "candidate_name", "trade_count"], ascending=[True, True, False]).reset_index(drop=True)


def build_transition_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    cols = ["market_state", "theme_state", "playbook_id"]
    return panel.groupby(cols, dropna=False).size().reset_index(name="candidate_count").sort_values("candidate_count", ascending=False).reset_index(drop=True)


def build_mdd_windows(equity_curve: pd.DataFrame) -> pd.DataFrame:
    if equity_curve.empty:
        return pd.DataFrame()
    rows = []
    for (candidate, split), group in equity_curve.groupby(["candidate_name", "split_scope"], dropna=False):
        g = group.sort_values("event_ts")
        trough = g.loc[pd.to_numeric(g["drawdown_pct"], errors="coerce").idxmin()]
        before = g[g["event_ts"].le(trough["event_ts"])]
        peak = before.loc[pd.to_numeric(before["equity"], errors="coerce").idxmax()]
        rows.append({"candidate_name": candidate, "split_scope": split, "mdd_peak_ts": peak["event_ts"], "mdd_trough_ts": trough["event_ts"], "peak_equity": float(peak["equity"]), "trough_equity": float(trough["equity"]), "max_drawdown_pct": float(trough["drawdown_pct"])})
    return pd.DataFrame(rows).sort_values(["split_scope", "max_drawdown_pct"]).reset_index(drop=True)


def build_mdd_audit(accepted: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty or windows.empty:
        return pd.DataFrame()
    rows = []
    all_acc = accepted[accepted["split_scope"].astype(str).eq("all")].copy()
    all_win = windows[windows["split_scope"].astype(str).eq("all")].copy()
    for _, win in all_win.iterrows():
        candidate = str(win["candidate_name"])
        group = all_acc[all_acc["candidate_name"].astype(str).eq(candidate)].copy()
        peak = pd.Timestamp(win["mdd_peak_ts"])
        trough = pd.Timestamp(win["mdd_trough_ts"])
        group["entry_ts"] = pd.to_datetime(group["entry_ts"], utc=True)
        group["simulated_exit_ts"] = pd.to_datetime(group["simulated_exit_ts"], utc=True)
        active = group[(group["entry_ts"].le(trough)) & (group["simulated_exit_ts"].ge(peak))].copy()
        for key in ["playbook_id", "theme_state", "theme_id", "mechanism_relation_state"]:
            for value, sub in active.groupby(key, dropna=False):
                returns = pd.to_numeric(sub["net_return_costed"], errors="coerce")
                rows.append({"candidate_name": candidate, "audit_group": key, "group_value": value, "active_trade_count": int(len(sub)), "avg_return_costed_pct": float(returns.mean() * 100.0), "avg_size_multiplier": float(pd.to_numeric(sub["size_multiplier"], errors="coerce").mean())})
    return pd.DataFrame(rows).sort_values(["candidate_name", "audit_group", "active_trade_count"], ascending=[True, True, False]).reset_index(drop=True)


def build_promotion_report(grid: pd.DataFrame, specs: pd.DataFrame) -> pd.DataFrame:
    baseline = pivot(grid, BASELINE_CANDIDATE)
    rows = []
    for _, spec in specs.iterrows():
        candidate = str(spec["candidate_name"])
        metrics = pivot(grid, candidate)
        beats_all = int(metrics["all_final_capital_usd"] > baseline["all_final_capital_usd"])
        dd_ok = int(metrics["all_max_drawdown_pct"] >= baseline["all_max_drawdown_pct"])
        validation_up = int(metrics["validation_final_capital_usd"] > baseline["validation_final_capital_usd"])
        recent_up = int(metrics["recent_oos_final_capital_usd"] > baseline["recent_oos_final_capital_usd"])
        validation_dd_ok = int(metrics["validation_max_drawdown_pct"] >= baseline["validation_max_drawdown_pct"])
        recent_dd_ok = int(metrics["recent_oos_max_drawdown_pct"] >= baseline["recent_oos_max_drawdown_pct"])
        allowed = int(int(spec["diagnostic_only_flag"]) == 0 and int(spec["return_tuned_flag"]) == 0 and int(spec["fixed_hold_or_timing_override_flag"]) == 0)
        promotion = int(candidate != BASELINE_CANDIDATE and beats_all and dd_ok and validation_up and recent_up and validation_dd_ok and recent_dd_ok and allowed)
        rows.append({**{"candidate_name": candidate}, **metrics, "beats_all_task639_flag": beats_all, "all_drawdown_not_worse_flag": dd_ok, "validation_improves_task639_flag": validation_up, "recent_oos_improves_task639_flag": recent_up, "validation_drawdown_not_worse_flag": validation_dd_ok, "recent_oos_drawdown_not_worse_flag": recent_dd_ok, "promotion_allowed_flag": allowed, "promotion_candidate_flag": promotion, "failure_reason": failure_reason(promotion, allowed, beats_all, dd_ok, validation_up, recent_up, validation_dd_ok, recent_dd_ok)})
    return pd.DataFrame(rows).sort_values(["promotion_candidate_flag", "all_final_capital_usd"], ascending=[False, False]).reset_index(drop=True)


def pivot(grid: pd.DataFrame, candidate: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for _, row in grid[grid["candidate_name"].eq(candidate)].iterrows():
        split = str(row["split_name"])
        for column in ["final_capital_usd", "max_drawdown_pct", "accepted_trade_count", "avg_size_multiplier", "entry_reduce_failure_rate"]:
            out[f"{split}_{column}"] = float(row[column])
    return out


def failure_reason(promotion: int, allowed: int, beats_all: int, dd_ok: int, validation_up: int, recent_up: int, validation_dd_ok: int, recent_dd_ok: int) -> str:
    if promotion:
        return "passes_all_playbook_gates"
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


def build_decision(promotion: pd.DataFrame) -> pd.DataFrame:
    baseline = promotion[promotion["candidate_name"].eq(BASELINE_CANDIDATE)].iloc[0]
    best = promotion.sort_values("all_final_capital_usd", ascending=False).iloc[0]
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "REGIME_THEME_PLAYBOOK_TESTED_NO_PROMOTION_CANDIDATE" if promotion_count == 0 else "REGIME_THEME_PLAYBOOK_PROMOTION_CANDIDATE_FOUND_NOT_ACCEPTED",
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
                "next_action": "If no playbook candidate passes, compare playbook states as diagnostics and refine theme leadership thresholds without return tuning.",
            }
        ]
    )


def build_pass_fail(specs: pd.DataFrame, promotion: pd.DataFrame, accepted: pd.DataFrame, allocation: pd.DataFrame, playbook_perf: pd.DataFrame, transition: pd.DataFrame, mdd_audit: pd.DataFrame) -> pd.DataFrame:
    fixed = int(pd.to_numeric(specs["fixed_hold_or_timing_override_flag"], errors="coerce").sum())
    promotion_count = int(promotion["promotion_candidate_flag"].sum())
    return pd.DataFrame(
        [
            {"gate": "no_fixed_hold_or_timing_override", "pass_flag": int(fixed == 0), "observed_value": f"violations={fixed}", "required_value": "preserve Task639 timing and exits"},
            {"gate": "playbook_panel_built", "pass_flag": int(not accepted.empty and "playbook_id" in accepted.columns), "observed_value": f"accepted_rows={len(accepted)}", "required_value": "playbook assigned to accepted trades"},
            {"gate": "capacity_decision_panel_built", "pass_flag": int(not allocation.empty), "observed_value": f"rows={len(allocation)}", "required_value": "accepted and rejected decisions logged"},
            {"gate": "playbook_performance_built", "pass_flag": int(not playbook_perf.empty), "observed_value": f"rows={len(playbook_perf)}", "required_value": "performance by playbook and split"},
            {"gate": "transition_matrix_built", "pass_flag": int(not transition.empty), "observed_value": f"rows={len(transition)}", "required_value": "market/theme/playbook transition matrix"},
            {"gate": "mdd_audit_built", "pass_flag": int(not mdd_audit.empty), "observed_value": f"rows={len(mdd_audit)}", "required_value": "MDD interval audit"},
            {"gate": "no_return_tuned_promotion", "pass_flag": 1, "observed_value": "return_tuned_promoted=0", "required_value": "no return-tuned candidate can promote"},
            {"gate": "promotion_candidate_found", "pass_flag": int(promotion_count > 0), "observed_value": f"promotion_candidates={promotion_count}", "required_value": "return drawdown validation recent OOS all pass"},
            {"gate": "strategy_accepted", "pass_flag": 0, "observed_value": "research diagnostic only", "required_value": "accepted gates and live readiness"},
        ]
    )


def write_promotion_blocker(out_dir: Path, decision: pd.DataFrame, promotion: pd.DataFrame) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task668 Promotion Blocker Report",
        "",
        f"- Decision: `{d['decision']}`",
        "- Strategy: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "",
        "## Simple Reason",
        "",
        "The playbook layer was built and tested, but no candidate improved return, drawdown, validation, and recent OOS together.",
        "",
        "## Rule Hygiene",
        "",
        "- return_used_in_assignment = 0",
        "- label_used_in_assignment = 0",
        "- symbol_blacklist = 0",
        "- return-tuned theme blacklist = 0",
        "- exit_changed = 0",
        "- fixed_hold_override = 0",
        "",
        "## Candidate Summary",
        "",
        table(promotion),
    ]
    (out_dir / "task668_promotion_blocker_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(out_dir: Path, decision: pd.DataFrame, grid: pd.DataFrame, playbook_perf: pd.DataFrame, transition: pd.DataFrame, mdd_audit: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task668 Regime Theme Playbook",
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
        "Task668 adds market state, theme leadership/rotation state, company catalyst quality, price acceptance, and relation state into a playbook layer. It preserves Task639 entry timing and exits.",
        "",
        "### Candidate Grid",
        "",
        table(grid),
        "",
        "### Playbook Performance",
        "",
        table(playbook_perf),
        "",
        "### Transition Matrix",
        "",
        table(transition),
        "",
        "### MDD Interval Audit",
        "",
        table(mdd_audit),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "이번 작업은 장 좋음/나쁨만 보는 게 아니라 돈이 어느 테마로 이동하는지까지 넣은 playbook 테스트입니다.",
        "",
        "테마가 진짜 주도 중인지, 좁게 오른 것인지, 약해지는 중인지, 방어성 이동인지 나눴습니다.",
        "",
        "수익과 낙폭과 OOS가 모두 좋아져야 승격입니다. 아직 승격 후보는 없습니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `task668_candidate_specs.csv`",
        "- `task668_playbook_panel.csv`",
        "- `task668_candidate_grid.csv`",
        "- `task668_accepted_trades.csv`",
        "- `task668_capacity_decision_panel.csv`",
        "- `task668_equity_curve.csv`",
        "- `task668_playbook_performance.csv`",
        "- `task668_transition_matrix.csv`",
        "- `task668_mdd_windows.csv`",
        "- `task668_mdd_interval_audit.csv`",
        "- `task668_promotion_report.csv`",
        "- `task668_promotion_blocker_report.md`",
        "- `task_668_gpt_review_packet.md`",
        "- `task_668_gpt_review_response.md`",
        "- `task_668_decision.csv`",
        "- `task_668_pass_fail_matrix.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_668_regime_theme_playbook.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def empty_quality() -> dict[str, float]:
    return {"capital_pnl_pct": 0.0, "max_drawdown_pct": 0.0, "entry_reduce_failure_rate": 0.0}


def f(value: object) -> float:
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
    result = build_task668_regime_theme_playbook(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best={decision['best_candidate_name']} "
        f"promotion={int(decision['promotion_candidate_count'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
