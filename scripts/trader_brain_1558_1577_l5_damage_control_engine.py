from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

import trader_brain_1518_1537_l5_position_operating_brain as l5
import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1518 = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
TASK1538 = ROOT / "data/artifacts/task_1538_1557_l5_hold_sizing_audit"
OUT_DIR = ROOT / "data/artifacts/task_1558_1577_l5_damage_control_engine"
REPORT_DIR = ROOT / "docs/reports/task_1558_1577_l5_damage_control_engine"
REPORT = REPORT_DIR / "task_1558_1577_l5_damage_control_engine.md"
DECISION = REPORT_DIR / "task_1558_1577_decision.csv"

AUTHORITY = "DIAGNOSTIC_L5_DAMAGE_CONTROL_ENGINE_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
COOLDOWN_DAYS = 63

DAMAGE_THRESHOLDS = {
    "confirmation_wait": {"reduce": -0.08, "exit": -0.99},
    "active_thesis": {"reduce": -0.12, "exit": -0.99},
    "confirmed_thesis": {"reduce": -0.16, "exit": -0.99},
    "source_gap_watch": {"reduce": -0.07, "exit": -0.99},
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def expert_goal_rows() -> list[dict[str, object]]:
    rows = [
        ("quant_pm", "MDD is the target, but return destruction is a failure."),
        ("event_driven_trader", "Source invalidation must override lazy hold extension unless confirmation is strong."),
        ("risk_manager", "Damage control must have reduce before exit so it does not become a blunt liquidation rule."),
        ("portfolio_construction", "No-reentry must be symbol and time bounded; never permanent blacklist."),
        ("backend_engineer", "Damage actions must be row-level auditable and separated from assignment outcomes."),
        ("governance", "Even a better MDD replay stays diagnostic-only until split/OOS/source audit gates pass."),
    ]
    return [
        {
            "task_id": "Task1558",
            "goal_id": f"DAMAGEGOAL1558-{idx:03d}",
            "expert_role": role,
            "perfect_goal_definition": definition,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, definition) in enumerate(rows, 1)
    ]


def rulebook_rows() -> list[dict[str, object]]:
    rows = [
        ("reuse_existing_signals", "Use Task1518 thesis_state, source exits, hold receipts, price path risk, and cap multipliers. Do not invent new L0-L4 inputs."),
        ("source_damage_priority", "Post-entry source invalidation overrides hold extension: confirmation_wait exits; active/confirmed reduce unless price confirms deeper damage."),
        ("price_damage_reduce_first", "Price damage reduces exposure by thesis-state threshold; price-only full exit is disabled because the audit showed it destroys return."),
        ("no_reentry_cooling", "After damage exit, same symbol is blocked for 63 calendar days for the same policy."),
        ("return_preservation_gate", "A policy that improves MDD but falls below QQQ or destroys more than 35 pct of actual-L5 final equity is not promoted."),
        ("audit_only", "All PnL and damage outcomes are audit-only and do not feed assignment logic."),
    ]
    return [
        {
            "task_id": "Task1559",
            "rule_id": f"DAMAGERULE1559-{idx:03d}",
            "rule_name": name,
            "pre_registered_rule": rule,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, rule) in enumerate(rows, 1)
    ]


def selected_specs() -> list[dict[str, object]]:
    return [dict(row) for row in read_csv(TASK1518 / "task1524_policy_specs_final.csv")]


def trade_specs_by_id() -> dict[str, dict[str, str]]:
    return {row["trade_spec_id"]: row for row in read_csv(l5.TASK1201 / "task1203_l5_trade_specs.csv")}


def exit_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1518 / "task1523_exit_decision_panel.csv")
    }


def source_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1518 / "task1523_source_receipt_exit_panel.csv")
    }


def hold_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1518 / "task1523_hold_receipt_panel.csv")
    }


def base_planned_close(
    frame: pd.DataFrame | None,
    entry_date: date,
    scheduled_exit: date,
    exit_row: dict[str, str],
) -> tuple[date, float] | None:
    if frame is None:
        return None
    action = str(exit_row.get("exit_action", "scheduled_exit"))
    override = str(exit_row.get("exit_date_override", ""))
    close = l5.close_for_exit(frame, entry_date, scheduled_exit, action, override)
    if close:
        return close[0], close[1]
    return None


def price_at_or_after(frame: pd.DataFrame | None, d: date) -> tuple[date, float] | None:
    return replay.price_on_or_after(frame, d)


def find_price_damage(
    frame: pd.DataFrame | None,
    entry_date: date,
    planned_exit: date,
    entry_price: float,
    thesis_state: str,
) -> tuple[date | None, float | None, date | None, float | None]:
    if frame is None:
        return None, None, None, None
    thresholds = DAMAGE_THRESHOLDS.get(thesis_state, DAMAGE_THRESHOLDS["confirmation_wait"])
    sub = frame[(frame["Date"] >= entry_date) & (frame["Date"] <= planned_exit)]
    reduce_event: tuple[date, float] | None = None
    exit_event: tuple[date, float] | None = None
    for _, row in sub.iterrows():
        current_date = row["Date"]
        close = float(row["Close"])
        drawdown = close / entry_price - 1.0
        if reduce_event is None and drawdown <= thresholds["reduce"]:
            reduce_event = (current_date, close)
        if drawdown <= thresholds["exit"]:
            exit_event = (current_date, close)
            break
    return (
        reduce_event[0] if reduce_event else None,
        reduce_event[1] if reduce_event else None,
        exit_event[0] if exit_event else None,
        exit_event[1] if exit_event else None,
    )


def source_damage_event(
    source_row: dict[str, str],
    entry_date: date,
    planned_exit: date,
) -> tuple[date | None, str]:
    if str(source_row.get("source_receipt_exit_ready", "")) != "1":
        return None, ""
    ts = replay.parse_ts(str(source_row.get("source_receipt_ts", "")))
    if not ts:
        return None, ""
    event_date = ts.date()
    if entry_date <= event_date <= planned_exit:
        return event_date, str(source_row.get("source_receipt_exit_type", "source_damage"))
    return None, ""


def decide_damage_action(
    selected: dict[str, object],
    source_event_date: date | None,
    source_event_type: str,
    price_reduce_date: date | None,
    price_exit_date: date | None,
    original_exit_action: str,
) -> dict[str, object]:
    thesis_state = str(selected.get("thesis_state", ""))
    action = "hold"
    reason = "damage_control_hold"
    reduce_fraction = 0.0
    exit_date: date | None = None
    reduce_date: date | None = None
    no_reentry = "0"

    if source_event_date:
        if thesis_state in {"confirmation_wait", "source_gap_watch"}:
            action = "exit"
            reason = source_event_type or "source_damage_exit"
            exit_date = source_event_date
            no_reentry = "1"
        else:
            action = "reduce"
            reason = source_event_type or "source_damage_reduce"
            reduce_date = source_event_date
            reduce_fraction = 0.5

    if price_exit_date and (exit_date is None or price_exit_date < exit_date):
        action = "exit"
        reason = "price_damage_exit"
        exit_date = price_exit_date
        no_reentry = "1"
    elif price_reduce_date and action == "hold":
        action = "reduce"
        reason = "price_damage_reduce"
        reduce_date = price_reduce_date
        reduce_fraction = 0.5

    if original_exit_action == "hold_extend" and action == "hold":
        action = "hold"
        reason = "qualified_hold_extension_preserved"
    return {
        "damage_action": action,
        "damage_reason": reason,
        "damage_reduce_fraction": reduce_fraction,
        "damage_reduce_date": reduce_date.isoformat() if reduce_date else "",
        "damage_exit_date": exit_date.isoformat() if exit_date else "",
        "no_reentry_triggered": no_reentry,
    }


def run_damage_replay() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    specs = trade_specs_by_id()
    policies = selected_specs()
    exits = exit_by_key()
    sources = source_by_key()
    price_cache: dict[str, pd.DataFrame | None] = {}
    by_policy_decision: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in policies:
        by_policy_decision[(str(row["policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)

    action_rows: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    cooldown_until: dict[tuple[str, str], date] = {}
    action_idx = 1
    trade_idx = 1

    for policy_id, slot_cap in l5.POLICIES.items():
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in by_policy_decision if key[0] == policy_id}):
            decision_date = (replay.parse_ts(decision_ts) or replay.parse_ts(decision_ts[:10])).date()
            items = by_policy_decision[(policy_id, decision_ts)]
            base_alloc = capital / slot_cap
            period_pnl = 0.0
            new_capital = capital
            allocated_count = 0
            for selected in items:
                symbol = str(selected["symbol"])
                cooldown_key = (policy_id, symbol)
                if cooldown_key in cooldown_until and decision_date <= cooldown_until[cooldown_key]:
                    action_rows.append(
                        {
                            "task_id": "Task1561",
                            "damage_action_id": f"DAMAGEACT1561-{action_idx:06d}",
                            "policy_variant_id": policy_id,
                            "trade_spec_id": selected["trade_spec_id"],
                            "candidate_source_id": selected["candidate_source_id"],
                            "symbol": symbol,
                            "decision_asof_ts": decision_ts,
                            "thesis_state": selected["thesis_state"],
                            "damage_action": "no_reentry",
                            "damage_reason": "cooldown_after_prior_damage_exit",
                            "damage_reduce_fraction": 0.0,
                            "damage_reduce_date": "",
                            "damage_exit_date": "",
                            "no_reentry_triggered": "1",
                            "assignment_uses_future_outcome": "0",
                            "authority": AUTHORITY,
                        }
                    )
                    action_idx += 1
                    continue
                spec = specs[str(selected["trade_spec_id"])]
                frame = replay.load_price(symbol, price_cache)
                entry_after = replay.parse_date(spec["entry_after_date"]) or date(1970, 1, 1)
                scheduled_exit = replay.parse_date(spec["exit_on_or_before_date"]) or entry_after
                entry = price_at_or_after(frame, entry_after)
                if not entry:
                    continue
                entry_date, entry_price = entry
                key = (policy_id, str(selected["trade_spec_id"]))
                exit_row = exits.get(key, {})
                original_close = base_planned_close(frame, entry_date, scheduled_exit, exit_row)
                if not original_close:
                    continue
                planned_exit_date, planned_exit_price = original_close
                src_date, src_type = source_damage_event(sources.get(key, {}), entry_date, planned_exit_date)
                price_reduce_date, price_reduce_price, price_exit_date, price_exit_price = find_price_damage(
                    frame,
                    entry_date,
                    planned_exit_date,
                    entry_price,
                    str(selected["thesis_state"]),
                )
                action = decide_damage_action(
                    selected,
                    src_date,
                    src_type,
                    price_reduce_date,
                    price_exit_date,
                    str(exit_row.get("exit_action", "scheduled_exit")),
                )
                action_rows.append(
                    {
                        "task_id": "Task1561",
                        "damage_action_id": f"DAMAGEACT1561-{action_idx:06d}",
                        "policy_variant_id": policy_id,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": symbol,
                        "decision_asof_ts": decision_ts,
                        "thesis_state": selected["thesis_state"],
                        "original_exit_action": exit_row.get("exit_action", "scheduled_exit"),
                        "source_damage_date": src_date.isoformat() if src_date else "",
                        "price_reduce_date": price_reduce_date.isoformat() if price_reduce_date else "",
                        "price_exit_date": price_exit_date.isoformat() if price_exit_date else "",
                        **action,
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
                action_idx += 1

                size_multiplier = to_float(selected.get("position_size_cap_multiplier"), 1.0)
                capital_allocated = base_alloc * size_multiplier
                cash_unallocated = base_alloc * (1.0 - size_multiplier)
                reduce_fraction = to_float(action["damage_reduce_fraction"])
                if action["damage_action"] == "exit":
                    exit_date = replay.parse_date(str(action["damage_exit_date"])) or planned_exit_date
                    close = replay.close_on_or_before(frame, exit_date)
                    actual_exit_date = close[0] if close else planned_exit_date
                    actual_exit_price = close[1] if close else planned_exit_price
                    gross_return = replay.pct_return(entry_price, actual_exit_price)
                    net_return = gross_return - ROUND_TRIP_COST_BPS / 10000.0
                    pnl = capital_allocated * net_return
                    reduce_pnl = 0.0
                    final_pnl = pnl
                    reduced_capital = 0.0
                    final_capital = capital_allocated
                    if action["no_reentry_triggered"] == "1":
                        cooldown_until[cooldown_key] = actual_exit_date + timedelta(days=COOLDOWN_DAYS)
                elif action["damage_action"] == "reduce" and reduce_fraction > 0:
                    reduce_date = replay.parse_date(str(action["damage_reduce_date"])) or planned_exit_date
                    reduce_close = replay.close_on_or_before(frame, reduce_date)
                    reduce_exit_date = reduce_close[0] if reduce_close else planned_exit_date
                    reduce_exit_price = reduce_close[1] if reduce_close else planned_exit_price
                    reduced_capital = capital_allocated * reduce_fraction
                    final_capital = capital_allocated - reduced_capital
                    reduce_return = replay.pct_return(entry_price, reduce_exit_price) - ROUND_TRIP_COST_BPS / 10000.0
                    final_return = replay.pct_return(entry_price, planned_exit_price) - ROUND_TRIP_COST_BPS / 10000.0
                    reduce_pnl = reduced_capital * reduce_return
                    final_pnl = final_capital * final_return
                    pnl = reduce_pnl + final_pnl
                    actual_exit_date = planned_exit_date
                    actual_exit_price = planned_exit_price
                    net_return = pnl / capital_allocated if capital_allocated else 0.0
                else:
                    reduced_capital = 0.0
                    final_capital = capital_allocated
                    reduce_pnl = 0.0
                    final_return = replay.pct_return(entry_price, planned_exit_price) - ROUND_TRIP_COST_BPS / 10000.0
                    final_pnl = capital_allocated * final_return
                    pnl = final_pnl
                    actual_exit_date = planned_exit_date
                    actual_exit_price = planned_exit_price
                    net_return = final_return
                new_capital += pnl
                period_pnl += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task1562",
                        "trade_row_id": f"DAMAGETRADE1562-{trade_idx:06d}",
                        "policy_variant_id": policy_id,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": symbol,
                        "decision_asof_ts": decision_ts,
                        "entry_date": entry_date.isoformat(),
                        "entry_price": round(entry_price, 6),
                        "scheduled_exit_date": scheduled_exit.isoformat(),
                        "planned_exit_date": planned_exit_date.isoformat(),
                        "actual_exit_date": actual_exit_date.isoformat(),
                        "actual_exit_price": round(actual_exit_price, 6),
                        "thesis_state": selected["thesis_state"],
                        "damage_action": action["damage_action"],
                        "damage_reason": action["damage_reason"],
                        "position_size_cap_multiplier": round(size_multiplier, 4),
                        "capital_allocated": round(capital_allocated, 4),
                        "cash_unallocated_from_cap": round(cash_unallocated, 4),
                        "reduced_capital": round(reduced_capital, 4),
                        "final_capital": round(final_capital, 4),
                        "reduce_pnl": round(reduce_pnl, 4),
                        "final_pnl": round(final_pnl, 4),
                        "net_return": round(net_return, 8),
                        "pnl": round(pnl, 4),
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1562",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "allocated_count": allocated_count,
                    "authority": AUTHORITY,
                }
            )
    return action_rows, trades, equity, build_metrics(trades, equity)


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    actual_metrics = {
        row["policy_variant_id"]: row
        for row in read_csv(TASK1518 / "task1525_replay_metrics.csv")
    }
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        actual = actual_metrics[policy_id]
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end = max(replay.parse_date(str(row["actual_exit_date"])) or start for row in tr_rows)
        cagr_value = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd_value = replay.max_drawdown(values)
        actual_final = to_float(actual["final_equity"])
        actual_mdd = to_float(actual["max_drawdown"])
        rows.append(
            {
                "task_id": "Task1563",
                "policy_variant_id": policy_id.replace("l5_operating", "l5_damage_reduce_first"),
                "source_policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr_value, 6),
                "max_drawdown": round(mdd_value, 6),
                "trade_count": len(tr_rows),
                "hold_count": sum(1 for row in tr_rows if row["damage_action"] == "hold"),
                "reduce_count": sum(1 for row in tr_rows if row["damage_action"] == "reduce"),
                "exit_count": sum(1 for row in tr_rows if row["damage_action"] == "exit"),
                "actual_l5_final_equity": actual["final_equity"],
                "actual_l5_final_delta": round(final - actual_final, 4),
                "actual_l5_max_drawdown": actual["max_drawdown"],
                "mdd_delta_positive_is_better": round(mdd_value - actual_mdd, 6),
                "mdd_improved_vs_actual_l5": "1" if mdd_value > actual_mdd else "0",
                "return_preservation_ratio": round(final / actual_final, 6) if actual_final else 0.0,
                "beats_qqq": "1" if final > to_float(actual["benchmark_final_equity"]) else "0",
                "target_cagr_30pct_met": "1" if cagr_value >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd_value >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_action_summary(actions: list[dict[str, object]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    action_counts = Counter((row["policy_variant_id"], row["damage_action"]) for row in actions)
    trade_groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trade_groups[(str(row["policy_variant_id"]), str(row["damage_action"]))].append(row)
    rows: list[dict[str, object]] = []
    idx = 1
    for key in sorted(set(action_counts) | set(trade_groups)):
        policy_id, action = key
        group = trade_groups.get(key, [])
        rows.append(
            {
                "task_id": "Task1564",
                "summary_id": f"DAMAGESUM1564-{idx:04d}",
                "policy_variant_id": policy_id,
                "damage_action": action,
                "action_count": action_counts.get(key, 0),
                "trade_count": len(group),
                "avg_net_return": round(mean([to_float(row["net_return"]) for row in group]), 8),
                "total_pnl": round(sum(to_float(row["pnl"]) for row in group), 4),
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def build_gate_and_closeout(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best_mdd = max(metrics, key=lambda row: to_float(row["max_drawdown"]))
    best_final = max(metrics, key=lambda row: to_float(row["final_equity"]))
    viable = [
        row for row in metrics
        if row["mdd_improved_vs_actual_l5"] == "1"
        and to_float(row["return_preservation_ratio"]) >= 0.65
        and row["beats_qqq"] == "1"
    ]
    gate = [
        {
            "task_id": "Task1576",
            "best_mdd_policy_variant_id": best_mdd["policy_variant_id"],
            "best_mdd_final_equity": best_mdd["final_equity"],
            "best_mdd_cagr": best_mdd["cagr"],
            "best_mdd_max_drawdown": best_mdd["max_drawdown"],
            "best_final_policy_variant_id": best_final["policy_variant_id"],
            "best_final_equity": best_final["final_equity"],
            "best_final_cagr": best_final["cagr"],
            "best_final_max_drawdown": best_final["max_drawdown"],
            "viable_damage_policy_count": len(viable),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "damage_control_engine_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1577",
            "verdict": "damage_control_engine_implemented_not_accepted",
            "mdd_target_met_by_any_policy": "1" if any(row["target_mdd_minus30pct_met"] == "1" for row in metrics) else "0",
            "cagr_target_met_by_any_policy": "1" if any(row["target_cagr_30pct_met"] == "1" for row in metrics) else "0",
            "viable_damage_policy_count": len(viable),
            "next_action": "audit damage actions by symbol and then test source-confirmed re-risking without disabling reduce-first guard",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(
    metrics: list[dict[str, object]],
    summary: list[dict[str, object]],
    gate: dict[str, object],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1558-1577 L5 Damage Control Engine",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        "- Goal: convert existing L0-L4/L5 risk signals into hold/reduce/exit/no-reentry actions.",
        "- Success condition: improve MDD versus Task1518 actual L5 without destroying QQQ-beating return.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "| Policy | Final | CAGR | MDD | Actual L5 Final Delta | MDD Delta | Return Preservation | Beats QQQ |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['actual_l5_final_delta']} | {row['mdd_delta_positive_is_better']} | {row['return_preservation_ratio']} | {row['beats_qqq']} |"
        )
    lines.extend(
        [
            "",
            "Damage action summary:",
            "",
            "| Source Policy | Action | Action Count | Trade Count | Avg Net Return | Total PnL |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary:
        lines.append(
            f"| `{row['policy_variant_id']}` | `{row['damage_action']}` | {row['action_count']} | {row['trade_count']} | {row['avg_net_return']} | {row['total_pnl']} |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. 기존 위험 신호를 새로 만들지 않고 L5 행동으로 연결했습니다.",
            "2. 각 포지션은 hold / reduce / exit / no_reentry 중 하나로 기록됩니다.",
            "3. reduce는 전량 매도가 아니라 절반 감속입니다.",
            "4. damage exit 뒤 같은 종목은 63일 재진입을 막습니다.",
            "5. 결과가 좋아도 전략 승인은 아닙니다.",
            "",
            "## Acceptance Gate",
            "",
            f"- Best MDD policy: `{gate['best_mdd_policy_variant_id']}` final {gate['best_mdd_final_equity']} CAGR {gate['best_mdd_cagr']} MDD {gate['best_mdd_max_drawdown']}.",
            f"- Best final policy: `{gate['best_final_policy_variant_id']}` final {gate['best_final_equity']} CAGR {gate['best_final_cagr']} MDD {gate['best_final_max_drawdown']}.",
            f"- Viable damage policy count: {gate['viable_damage_policy_count']}.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1558_perfect_goal.csv`",
            "- `task1559_damage_control_rulebook.csv`",
            "- `task1561_damage_action_panel.csv`",
            "- `task1562_damage_replay_trades.csv`",
            "- `task1562_damage_replay_equity.csv`",
            "- `task1563_damage_replay_metrics.csv`",
            "- `task1564_damage_action_summary.csv`",
            "- `task1576_acceptance_gate.csv`",
            "- `task1577_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1558_1577_l5_damage_control_engine_validate.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    goals = expert_goal_rows()
    rules = rulebook_rows()
    actions, trades, equity, metrics = run_damage_replay()
    summary = build_action_summary(actions, trades)
    gate, closeout = build_gate_and_closeout(metrics)
    write_csv(OUT_DIR / "task1558_perfect_goal.csv", goals)
    write_csv(OUT_DIR / "task1559_damage_control_rulebook.csv", rules)
    write_csv(OUT_DIR / "task1561_damage_action_panel.csv", actions)
    write_csv(OUT_DIR / "task1562_damage_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1562_damage_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1563_damage_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1564_damage_action_summary.csv", summary)
    write_csv(OUT_DIR / "task1576_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1577_closeout.csv", closeout)
    write_json(OUT_DIR / "task1577_closeout.json", closeout[0])
    write_csv(DECISION, gate)
    write_report(metrics, summary, gate[0], closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1558_1577] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
