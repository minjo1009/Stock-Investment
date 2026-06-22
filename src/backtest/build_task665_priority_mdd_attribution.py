from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task637_content_signal_account_backtest import INITIAL_CAPITAL_USD
from src.backtest.build_task659_theme_specific_relation_engine import task639_core
from src.backtest.build_task661_mechanism_relation_engine import (
    TASK659_PANEL,
    build_institutional_transmission_template,
    build_mechanism_state_panel,
    load_task659_panel,
)
from src.backtest.build_task664_relation_priority_backtest import (
    COST_BPS,
    MAX_POSITIONS,
    add_priority,
)


TASK_ID = "Task665"
REPORT_DIR = Path("docs/reports/task_665_priority_mdd_attribution")
BASELINE_RULE = "entry_ts_then_lifecycle_id"
PRIORITY_RULE = "reinforcing_offsetting_needs_confirmation_quality_confirmed_sparse"


def build_task665_priority_mdd_attribution(
    *,
    task659_panel_path: Path = TASK659_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = build_mechanism_state_panel(load_task659_panel(task659_panel_path), build_institutional_transmission_template())
    core = task639_core(panel)

    baseline_panel = add_priority(core, BASELINE_RULE)
    priority_panel = add_priority(core, PRIORITY_RULE)
    baseline_quality, baseline_accepted, baseline_curve = simulate_with_curve(baseline_panel, "baseline_chronological")
    priority_quality, priority_accepted, priority_curve = simulate_with_curve(priority_panel, "predeclared_relation_ladder")

    mdd_summary = build_mdd_summary(baseline_quality, baseline_curve, priority_quality, priority_curve)
    accepted_delta = build_accepted_trade_delta(baseline_accepted, priority_accepted, mdd_summary)
    active_inventory = build_active_trade_inventory(accepted_delta, mdd_summary)
    displacement = build_slot_displacement_pairs(baseline_accepted, priority_accepted, mdd_summary)
    mdd_attribution = build_mdd_interval_trade_attribution(accepted_delta, displacement, mdd_summary)
    risk_findings = build_risk_findings(accepted_delta, displacement, mdd_attribution)
    decision = build_decision(mdd_summary, accepted_delta, displacement, risk_findings)
    pass_fail = build_pass_fail(mdd_summary, accepted_delta, displacement)

    pd.concat([baseline_curve, priority_curve], ignore_index=True).to_csv(out_dir / "priority_equity_curve_comparison.csv", index=False, encoding="utf-8-sig")
    mdd_summary.to_csv(out_dir / "priority_mdd_interval_summary.csv", index=False, encoding="utf-8-sig")
    accepted_delta.to_csv(out_dir / "accepted_trade_delta.csv", index=False, encoding="utf-8-sig")
    active_inventory.to_csv(out_dir / "priority_mdd_active_trade_inventory.csv", index=False, encoding="utf-8-sig")
    displacement.to_csv(out_dir / "slot_displacement_pairs.csv", index=False, encoding="utf-8-sig")
    mdd_attribution.to_csv(out_dir / "mdd_interval_trade_attribution.csv", index=False, encoding="utf-8-sig")
    risk_findings.to_csv(out_dir / "risk_cap_research_findings.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(out_dir / "task_665_decision.csv", index=False, encoding="utf-8-sig")
    pass_fail.to_csv(out_dir / "task_665_pass_fail_matrix.csv", index=False, encoding="utf-8-sig")
    write_report(out_dir, decision, mdd_summary, accepted_delta, displacement, mdd_attribution, risk_findings, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "mdd_summary": mdd_summary,
        "accepted_delta": accepted_delta,
        "active_inventory": active_inventory,
        "displacement": displacement,
        "mdd_attribution": mdd_attribution,
        "risk_findings": risk_findings,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def simulate_with_curve(panel: pd.DataFrame, candidate_name: str) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    if panel.empty:
        return empty_quality(), panel.copy(), pd.DataFrame()
    ordered = panel.sort_values(["entry_ts", "priority_rank", "lifecycle_id"], kind="mergesort").reset_index(drop=True)
    ordered["net_return_costed"] = pd.to_numeric(ordered["net_return_from_entry"], errors="coerce") - COST_BPS / 10000.0
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    curve_rows: list[dict[str, object]] = [
        {
            "candidate_name": candidate_name,
            "event_ts": pd.Timestamp.min.tz_localize("UTC") + pd.Timedelta(days=1),
            "event_type": "START",
            "lifecycle_id": "",
            "equity": equity,
            "equity_usd": equity * INITIAL_CAPITAL_USD,
            "drawdown_pct": 0.0,
            "realized_pnl_fraction": 0.0,
        }
    ]

    def append_event(event_ts: pd.Timestamp, event_type: str, lifecycle_id: str, realized_pnl: float = 0.0) -> None:
        curve_rows.append(
            {
                "candidate_name": candidate_name,
                "event_ts": event_ts,
                "event_type": event_type,
                "lifecycle_id": lifecycle_id,
                "equity": equity,
                "equity_usd": equity * INITIAL_CAPITAL_USD,
                "drawdown_pct": (equity / max(peak, 1e-9) - 1.0) * 100.0,
                "realized_pnl_fraction": realized_pnl,
            }
        )

    def close_positions_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= current_ts:
                pnl = float(pos["capital"]) * float(pos["return"])
                equity += pnl
                peak = max(peak, equity)
                append_event(pd.Timestamp(pos["exit_ts"]), "EXIT", str(pos["lifecycle_id"]), pnl)
            else:
                still_open.append(pos)
        open_positions = still_open

    for row in ordered.to_dict(orient="records"):
        entry_ts = pd.Timestamp(row["entry_ts"])
        close_positions_until(entry_ts)
        if len(open_positions) >= MAX_POSITIONS:
            continue
        capital = equity / float(MAX_POSITIONS)
        open_positions.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_costed"],
            }
        )
        accepted = dict(row)
        accepted["candidate_name"] = candidate_name
        accepted["accepted_capital_fraction"] = capital
        accepted["accepted_return_costed"] = row["net_return_costed"]
        accepted_rows.append(accepted)
        append_event(entry_ts, "ENTRY", str(row["lifecycle_id"]), 0.0)
    close_positions_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))

    accepted = pd.DataFrame(accepted_rows)
    curve = (
        pd.DataFrame(curve_rows)
        .sort_values(["event_ts", "event_type", "lifecycle_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    if accepted.empty:
        return empty_quality(), accepted, curve
    returns = pd.to_numeric(accepted["accepted_return_costed"], errors="coerce")
    quality = {
        "final_capital_usd": float(equity * INITIAL_CAPITAL_USD),
        "capital_return_pct": float((equity - 1.0) * 100.0),
        "max_drawdown_pct": float(curve["drawdown_pct"].min()),
        "accepted_trade_count": int(len(accepted)),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
        "avg_return_pct": float(returns.mean() * 100.0),
        "win_rate": float(returns.gt(0).mean()),
    }
    return quality, accepted, curve


def empty_quality() -> dict[str, object]:
    return {
        "final_capital_usd": INITIAL_CAPITAL_USD,
        "capital_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "accepted_trade_count": 0,
        "entry_reduce_failure_rate": 0.0,
        "avg_return_pct": 0.0,
        "win_rate": 0.0,
    }


def build_mdd_summary(
    baseline_quality: dict[str, object],
    baseline_curve: pd.DataFrame,
    priority_quality: dict[str, object],
    priority_curve: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for candidate_name, quality, curve in [
        ("baseline_chronological", baseline_quality, baseline_curve),
        ("predeclared_relation_ladder", priority_quality, priority_curve),
    ]:
        trough = curve.sort_values("drawdown_pct").iloc[0]
        peak_before = curve[curve["event_ts"].le(trough["event_ts"])].sort_values("equity", ascending=False).iloc[0]
        rows.append(
            {
                "candidate_name": candidate_name,
                "final_capital_usd": float(quality["final_capital_usd"]),
                "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                "accepted_trade_count": int(quality["accepted_trade_count"]),
                "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                "mdd_peak_ts": peak_before["event_ts"],
                "mdd_peak_equity_usd": float(peak_before["equity_usd"]),
                "mdd_trough_ts": trough["event_ts"],
                "mdd_trough_equity_usd": float(trough["equity_usd"]),
                "mdd_interval_days": float((pd.Timestamp(trough["event_ts"]) - pd.Timestamp(peak_before["event_ts"])).total_seconds() / 86400.0),
            }
        )
    out = pd.DataFrame(rows)
    base = out[out["candidate_name"].eq("baseline_chronological")].iloc[0]
    priority = out[out["candidate_name"].eq("predeclared_relation_ladder")].iloc[0]
    out["mdd_worse_than_baseline_pct_point"] = out["max_drawdown_pct"] - float(base["max_drawdown_pct"])
    out["final_capital_delta_vs_baseline_usd"] = out["final_capital_usd"] - float(base["final_capital_usd"])
    out.loc[out["candidate_name"].eq("predeclared_relation_ladder"), "priority_mdd_penalty_pct_point"] = float(priority["max_drawdown_pct"]) - float(base["max_drawdown_pct"])
    return out


def build_accepted_trade_delta(
    baseline_accepted: pd.DataFrame,
    priority_accepted: pd.DataFrame,
    mdd_summary: pd.DataFrame,
) -> pd.DataFrame:
    base = accepted_map(baseline_accepted)
    priority = accepted_map(priority_accepted)
    priority_mdd = mdd_summary[mdd_summary["candidate_name"].eq("predeclared_relation_ladder")].iloc[0]
    start = pd.Timestamp(priority_mdd["mdd_peak_ts"])
    end = pd.Timestamp(priority_mdd["mdd_trough_ts"])
    rows = []
    for lifecycle_id in sorted(set(base).union(priority)):
        base_row = base.get(lifecycle_id)
        priority_row = priority.get(lifecycle_id)
        row = priority_row or base_row or {}
        base_return = float(base_row.get("accepted_return_costed", 0.0)) if base_row else 0.0
        priority_return = float(priority_row.get("accepted_return_costed", 0.0)) if priority_row else 0.0
        entry_ts = pd.Timestamp(row.get("entry_ts"))
        exit_ts = pd.Timestamp(row.get("simulated_exit_ts"))
        rows.append(
            {
                "lifecycle_id": lifecycle_id,
                "symbol": row.get("symbol", ""),
                "theme_id": row.get("theme_id", ""),
                "entry_ts": entry_ts,
                "simulated_exit_ts": exit_ts,
                "mechanism_relation_state": row.get("mechanism_relation_state", ""),
                "catalyst_quality_tier": row.get("catalyst_quality_tier", ""),
                "price_acceptance_state": row.get("price_acceptance_state", ""),
                "baseline_accepted_flag": int(base_row is not None),
                "priority_accepted_flag": int(priority_row is not None),
                "delta_class": delta_class(base_row is not None, priority_row is not None),
                "baseline_return_pct": base_return * 100.0,
                "priority_return_pct": priority_return * 100.0,
                "return_delta_pct_point": (priority_return - base_return) * 100.0,
                "entry_in_priority_mdd_interval_flag": int(start <= entry_ts <= end),
                "exit_in_priority_mdd_interval_flag": int(start <= exit_ts <= end),
                "open_during_priority_mdd_trough_flag": int(entry_ts <= end <= exit_ts),
                "evaluation_only_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values(["delta_class", "return_delta_pct_point"], ascending=[True, True]).reset_index(drop=True)


def accepted_map(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    if frame.empty:
        return {}
    return frame.drop_duplicates("lifecycle_id").set_index("lifecycle_id").to_dict(orient="index")


def delta_class(base: bool, priority: bool) -> str:
    if base and priority:
        return "preserved"
    if priority and not base:
        return "added_by_priority"
    if base and not priority:
        return "removed_by_priority"
    return "not_accepted"


def build_slot_displacement_pairs(
    baseline_accepted: pd.DataFrame,
    priority_accepted: pd.DataFrame,
    mdd_summary: pd.DataFrame,
) -> pd.DataFrame:
    priority_mdd = mdd_summary[mdd_summary["candidate_name"].eq("predeclared_relation_ladder")].iloc[0]
    start = pd.Timestamp(priority_mdd["mdd_peak_ts"])
    end = pd.Timestamp(priority_mdd["mdd_trough_ts"])
    base = baseline_accepted.copy()
    priority = priority_accepted.copy()
    base["entry_ts_key"] = pd.to_datetime(base["entry_ts"], utc=True, errors="coerce").astype(str)
    priority["entry_ts_key"] = pd.to_datetime(priority["entry_ts"], utc=True, errors="coerce").astype(str)
    rows = []
    for entry_ts_key in sorted(set(base["entry_ts_key"]).union(priority["entry_ts_key"])):
        base_group = base[base["entry_ts_key"].eq(entry_ts_key)].copy()
        priority_group = priority[priority["entry_ts_key"].eq(entry_ts_key)].copy()
        base_ids = set(base_group["lifecycle_id"].astype(str))
        priority_ids = set(priority_group["lifecycle_id"].astype(str))
        added = priority_group[priority_group["lifecycle_id"].astype(str).isin(priority_ids - base_ids)].sort_values(["priority_rank", "lifecycle_id"])
        removed = base_group[base_group["lifecycle_id"].astype(str).isin(base_ids - priority_ids)].sort_values(["priority_rank", "lifecycle_id"])
        max_len = max(len(added), len(removed))
        for idx in range(max_len):
            added_row = added.iloc[idx] if idx < len(added) else pd.Series(dtype=object)
            removed_row = removed.iloc[idx] if idx < len(removed) else pd.Series(dtype=object)
            pair_entry_ts = pd.Timestamp(added_row.get("entry_ts", removed_row.get("entry_ts")))
            pair_exit_ts = pd.Timestamp(added_row.get("simulated_exit_ts", removed_row.get("simulated_exit_ts")))
            added_return = float(added_row.get("accepted_return_costed", 0.0)) if not added_row.empty else 0.0
            removed_return = float(removed_row.get("accepted_return_costed", 0.0)) if not removed_row.empty else 0.0
            rows.append(
                {
                    "entry_ts": pair_entry_ts,
                    "pair_type": "same_timestamp_displacement" if not added_row.empty and not removed_row.empty else "unpaired_capacity_path_effect",
                    "added_lifecycle_id": added_row.get("lifecycle_id", ""),
                    "added_symbol": added_row.get("symbol", ""),
                    "added_theme_id": added_row.get("theme_id", ""),
                    "added_relation_state": added_row.get("mechanism_relation_state", ""),
                    "added_priority_rank": added_row.get("priority_rank", ""),
                    "added_return_pct": added_return * 100.0,
                    "removed_lifecycle_id": removed_row.get("lifecycle_id", ""),
                    "removed_symbol": removed_row.get("symbol", ""),
                    "removed_theme_id": removed_row.get("theme_id", ""),
                    "removed_relation_state": removed_row.get("mechanism_relation_state", ""),
                    "removed_priority_rank": removed_row.get("priority_rank", ""),
                    "removed_return_pct": removed_return * 100.0,
                    "pair_return_delta_pct_point": (added_return - removed_return) * 100.0,
                    "entry_in_priority_mdd_interval_flag": int(start <= pair_entry_ts <= end),
                    "exit_in_priority_mdd_interval_flag": int(start <= pair_exit_ts <= end),
                    "open_during_priority_mdd_trough_flag": int(pair_entry_ts <= end <= pair_exit_ts),
                    "evaluation_only_flag": 1,
                }
            )
    return pd.DataFrame(rows).sort_values("pair_return_delta_pct_point").reset_index(drop=True) if rows else pd.DataFrame()


def build_active_trade_inventory(accepted_delta: pd.DataFrame, mdd_summary: pd.DataFrame) -> pd.DataFrame:
    priority_mdd = mdd_summary[mdd_summary["candidate_name"].eq("predeclared_relation_ladder")].iloc[0]
    start = pd.Timestamp(priority_mdd["mdd_peak_ts"])
    end = pd.Timestamp(priority_mdd["mdd_trough_ts"])
    active = accepted_delta[
        pd.to_datetime(accepted_delta["entry_ts"], utc=True, errors="coerce").le(end)
        & pd.to_datetime(accepted_delta["simulated_exit_ts"], utc=True, errors="coerce").ge(start)
    ].copy()
    active["priority_mdd_peak_ts"] = start
    active["priority_mdd_trough_ts"] = end
    active["active_during_priority_mdd_interval_flag"] = 1
    return active.sort_values(["delta_class", "entry_ts", "symbol"], kind="mergesort").reset_index(drop=True)


def build_mdd_interval_trade_attribution(
    accepted_delta: pd.DataFrame,
    displacement: pd.DataFrame,
    mdd_summary: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for delta_class_name, group in accepted_delta.groupby("delta_class"):
        rows.append(
            {
                "bucket": delta_class_name,
                "row_count": int(len(group)),
                "avg_return_delta_pct_point": float(group["return_delta_pct_point"].mean()),
                "sum_return_delta_pct_point": float(group["return_delta_pct_point"].sum()),
                "open_during_priority_mdd_trough_count": int(group["open_during_priority_mdd_trough_flag"].sum()),
                "entry_in_priority_mdd_interval_count": int(group["entry_in_priority_mdd_interval_flag"].sum()),
                "exit_in_priority_mdd_interval_count": int(group["exit_in_priority_mdd_interval_flag"].sum()),
            }
        )
    if not displacement.empty:
        worse_pairs = displacement[displacement["pair_return_delta_pct_point"].lt(0)]
        rows.append(
            {
                "bucket": "negative_displacement_pairs",
                "row_count": int(len(worse_pairs)),
                "avg_return_delta_pct_point": float(worse_pairs["pair_return_delta_pct_point"].mean()) if not worse_pairs.empty else 0.0,
                "sum_return_delta_pct_point": float(worse_pairs["pair_return_delta_pct_point"].sum()) if not worse_pairs.empty else 0.0,
                "open_during_priority_mdd_trough_count": int(worse_pairs["open_during_priority_mdd_trough_flag"].sum()) if not worse_pairs.empty else 0,
                "entry_in_priority_mdd_interval_count": int(worse_pairs["entry_in_priority_mdd_interval_flag"].sum()) if not worse_pairs.empty else 0,
                "exit_in_priority_mdd_interval_count": int(worse_pairs["exit_in_priority_mdd_interval_flag"].sum()) if not worse_pairs.empty else 0,
            }
        )
    return pd.DataFrame(rows)


def build_risk_findings(
    accepted_delta: pd.DataFrame,
    displacement: pd.DataFrame,
    mdd_attribution: pd.DataFrame,
) -> pd.DataFrame:
    added = accepted_delta[accepted_delta["delta_class"].eq("added_by_priority")]
    removed = accepted_delta[accepted_delta["delta_class"].eq("removed_by_priority")]
    negative_pairs = displacement[displacement["pair_return_delta_pct_point"].lt(0)] if not displacement.empty else pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "finding_id": "F1",
                "finding": "priority_changes_capacity_path",
                "evidence": f"added={len(added)} removed={len(removed)}",
                "research_implication": "Priority affects actual accepted trades, so the relation engine is connected to capital allocation.",
                "promotion_status": "research_useful",
            },
            {
                "finding_id": "F2",
                "finding": "drawdown_penalty_blocks_promotion",
                "evidence": "priority final capital improves but MDD worsens versus baseline",
                "research_implication": "Need risk caps before promotion; return improvement alone is insufficient.",
                "promotion_status": "promotion_blocker",
            },
            {
                "finding_id": "F3",
                "finding": "negative_displacement_pairs_exist",
                "evidence": f"negative_pairs={len(negative_pairs)}",
                "research_implication": "Next risk cap should target bad displacement conditions, not broad relation-state filtering.",
                "promotion_status": "research_useful",
            },
        ]
    )


def build_decision(
    mdd_summary: pd.DataFrame,
    accepted_delta: pd.DataFrame,
    displacement: pd.DataFrame,
    risk_findings: pd.DataFrame,
) -> pd.DataFrame:
    base = mdd_summary[mdd_summary["candidate_name"].eq("baseline_chronological")].iloc[0]
    priority = mdd_summary[mdd_summary["candidate_name"].eq("predeclared_relation_ladder")].iloc[0]
    added = int(accepted_delta["delta_class"].eq("added_by_priority").sum())
    removed = int(accepted_delta["delta_class"].eq("removed_by_priority").sum())
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "PRIORITY_MDD_ATTRIBUTION_COMPLETE_RISK_CAP_REQUIRED",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "baseline_final_capital_usd": float(base["final_capital_usd"]),
                "baseline_max_drawdown_pct": float(base["max_drawdown_pct"]),
                "priority_final_capital_usd": float(priority["final_capital_usd"]),
                "priority_max_drawdown_pct": float(priority["max_drawdown_pct"]),
                "priority_final_capital_delta_usd": float(priority["final_capital_delta_vs_baseline_usd"]),
                "priority_mdd_penalty_pct_point": float(priority["priority_mdd_penalty_pct_point"]),
                "added_by_priority_count": added,
                "removed_by_priority_count": removed,
                "negative_displacement_pair_count": int(displacement["pair_return_delta_pct_point"].lt(0).sum()) if not displacement.empty else 0,
                "promotion_candidate_count": 0,
                "trading_promotion_pass_flag": 0,
                "next_action": "Design Task666 risk caps from displacement conditions only: cap harmful theme concentration or weak displacement pairs without changing entry or exit.",
            }
        ]
    )


def build_pass_fail(
    mdd_summary: pd.DataFrame,
    accepted_delta: pd.DataFrame,
    displacement: pd.DataFrame,
) -> pd.DataFrame:
    priority = mdd_summary[mdd_summary["candidate_name"].eq("predeclared_relation_ladder")].iloc[0]
    return pd.DataFrame(
        [
            {
                "gate": "mdd_interval_identified",
                "pass_flag": int(pd.notna(priority["mdd_peak_ts"]) and pd.notna(priority["mdd_trough_ts"])),
                "observed_value": f"{priority['mdd_peak_ts']} to {priority['mdd_trough_ts']}",
                "required_value": "priority peak and trough timestamps",
            },
            {
                "gate": "accepted_delta_built",
                "pass_flag": int(len(accepted_delta) > 0),
                "observed_value": f"rows={len(accepted_delta)}",
                "required_value": "accepted trade delta rows",
            },
            {
                "gate": "displacement_pairs_built",
                "pass_flag": int(len(displacement) > 0),
                "observed_value": f"rows={len(displacement)}",
                "required_value": "slot displacement pair rows",
            },
            {
                "gate": "drawdown_not_worse",
                "pass_flag": int(float(priority["priority_mdd_penalty_pct_point"]) >= 0),
                "observed_value": f"mdd_penalty={float(priority['priority_mdd_penalty_pct_point']):.2f}",
                "required_value": "priority must not worsen MDD before promotion",
            },
            {
                "gate": "strategy_accepted",
                "pass_flag": 0,
                "observed_value": "diagnostic attribution only",
                "required_value": "requires accepted strategy gates and live readiness",
            },
        ]
    )


def write_report(
    out_dir: Path,
    decision: pd.DataFrame,
    mdd_summary: pd.DataFrame,
    accepted_delta: pd.DataFrame,
    displacement: pd.DataFrame,
    mdd_attribution: pd.DataFrame,
    risk_findings: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    d = decision.iloc[0]
    lines = [
        "# Task665 Priority MDD Attribution",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        f"- Baseline: `${float(d['baseline_final_capital_usd']):.2f}`, MDD `{float(d['baseline_max_drawdown_pct']):.2f}%`.",
        f"- Priority: `${float(d['priority_final_capital_usd']):.2f}`, MDD `{float(d['priority_max_drawdown_pct']):.2f}%`.",
        f"- Added/removed accepted trades: `{int(d['added_by_priority_count'])}` / `{int(d['removed_by_priority_count'])}`.",
        f"- Negative displacement pairs: `{int(d['negative_displacement_pair_count'])}`.",
        "",
        "## Quant Expert Report",
        "",
        "Task665 attributes Task664's higher return but worse drawdown. It does not change entry, exit, timing, sizing, or priority rules.",
        "",
        "### Data Source And Source Readiness",
        "",
        "Input is the Task661 mechanism state panel rebuilt from Task659. No new source is introduced.",
        "",
        "### Exact Join Keys",
        "",
        "`lifecycle_id`, `entry_ts`, `simulated_exit_ts`, and accepted-trade membership.",
        "",
        "### Leakage Audit",
        "",
        "Returns are used only for post-trade attribution. No assignment rule is changed in this task.",
        "",
        "### MDD Interval Summary",
        "",
        table(mdd_summary),
        "",
        "### Accepted Trade Delta",
        "",
        table(accepted_delta),
        "",
        "### Active Trade Inventory",
        "",
        table(accepted_delta[accepted_delta["entry_in_priority_mdd_interval_flag"].eq(1) | accepted_delta["exit_in_priority_mdd_interval_flag"].eq(1) | accepted_delta["open_during_priority_mdd_trough_flag"].eq(1)]),
        "",
        "### Slot Displacement Pairs",
        "",
        table(displacement),
        "",
        "### MDD Attribution",
        "",
        table(mdd_attribution),
        "",
        "### Risk Findings",
        "",
        table(risk_findings),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "수익은 늘었는데 낙폭도 커진 이유를 뜯었습니다.",
        "",
        "핵심은 relation priority가 실제 accepted trade를 바꿨다는 점입니다.",
        "",
        "그런데 일부 slot 교체가 낙폭 구간에서 위험을 키웠습니다.",
        "",
        "그래서 다음은 새 매수/청산이 아니라, 나쁜 slot 교체를 막는 risk cap입니다.",
        "",
        "## Pass/Fail Matrix",
        "",
        table(pass_fail),
        "",
        "## Artifact Manifest",
        "",
        "- `priority_equity_curve_comparison.csv`",
        "- `priority_mdd_interval_summary.csv`",
        "- `accepted_trade_delta.csv`",
        "- `priority_mdd_active_trade_inventory.csv`",
        "- `slot_displacement_pairs.csv`",
        "- `mdd_interval_trade_attribution.csv`",
        "- `risk_cap_research_findings.csv`",
        "- `task_665_decision.csv`",
        "- `task_665_pass_fail_matrix.csv`",
        "- `artifact_manifest.csv`",
    ]
    (out_dir / "task_665_priority_mdd_attribution.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    result = build_task665_priority_mdd_attribution(out_dir=args.out_dir)
    decision = result["decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"mdd_penalty={float(decision['priority_mdd_penalty_pct_point']):.2f} "
        f"negative_pairs={int(decision['negative_displacement_pair_count'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
