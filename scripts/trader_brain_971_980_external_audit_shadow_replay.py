from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.trader_brain_941_950_slot_capped_selection_replay import (
    CALENDAR_PATH,
    DAILY_DIR,
    ENTRY_FEE_BPS,
    ENTRY_SLIPPAGE_BPS,
    EXIT_FEE_BPS,
    EXIT_SLIPPAGE_BPS,
    INITIAL_CAPITAL,
    PERIOD_END,
    PERIOD_START,
    annualized_return,
    date_part,
    load_prices,
    max_drawdown,
)


SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
REDESIGN_DIR = ROOT / "data/artifacts/task_961_970_external_audit_redesign"
BASELINE_DIR = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"
OUT_DIR = ROOT / "data/artifacts/task_971_980_external_audit_shadow_replay"

SPEC_PATH = SPEC_DIR / "task929_controlled_trade_specs.csv"
SHADOW_RANKING_PATH = REDESIGN_DIR / "task969_shadow_trader_ranking.csv"
BASELINE_TRADES_PATH = BASELINE_DIR / "task943_slot_capped_replay_trades.csv"
BASELINE_SUMMARY_PATH = BASELINE_DIR / "task946_slot_capped_summary.csv"

POLICY_ID = "slot10_external_audit_shadow_rank_v1"
SLOT_CAP = 10
AUTHORITY = "DIAGNOSTIC_EXTERNAL_AUDIT_SHADOW_REPLAY_ONLY"
ALLOWED_HARD_BLOCK_REASONS = "future_evidence;missing_required_lineage;source_backed_invalidation"
FORBIDDEN_OUTCOME_INPUTS = "future_return realized_return pnl post_entry_price_change outcome_rank"
ACTION_PRIORITY = {"enter": 0, "monitor": 1, "wait": 2}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def policy_sort_key(row: dict[str, str]) -> tuple[object, ...]:
    return (
        -int(row["shadow_rank_score"]),
        ACTION_PRIORITY.get(row["trader_action"], 99),
        row["theme"],
        row["symbol"],
        row["trade_spec_id"],
    )


def build_policy_selection(ranking_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], dict[str, list[dict[str, object]]]]:
    by_entry: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ranking_rows:
        by_entry[row["entry_date"]].append(row)

    ledger: list[dict[str, object]] = []
    selected_by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for entry_date, group in sorted(by_entry.items()):
        eligible = [row for row in group if row["trader_action"] != "hard_block"]
        blocked = [row for row in group if row["trader_action"] == "hard_block"]
        ranked = sorted(eligible, key=policy_sort_key)
        selected_ids = {row["trade_spec_id"] for row in ranked[:SLOT_CAP]}
        for rank, row in enumerate(ranked, start=1):
            state = "selected" if row["trade_spec_id"] in selected_ids else "rejected_by_slot_cap"
            out = {
                **row,
                "policy_id": POLICY_ID,
                "selection_rank": rank,
                "selection_state": state,
                "blocked_reason": "" if state == "selected" else "slot_cap_filled_by_higher_shadow_rank",
                "policy_sort_key": "|".join(str(item) for item in policy_sort_key(row)),
                "allowed_hard_block_reasons": ALLOWED_HARD_BLOCK_REASONS,
                "authority": AUTHORITY,
            }
            ledger.append(out)
            if state == "selected":
                selected_by_entry[entry_date].append(out)
        for row in blocked:
            ledger.append(
                {
                    **row,
                    "policy_id": POLICY_ID,
                    "selection_rank": "",
                    "selection_state": "hard_blocked",
                    "blocked_reason": "hard_block_from_pre_registered_shadow_input",
                    "policy_sort_key": "",
                    "allowed_hard_block_reasons": ALLOWED_HARD_BLOCK_REASONS,
                    "authority": AUTHORITY,
                }
            )
    return ledger, selected_by_entry


def replay(
    specs_by_id: dict[str, dict[str, str]],
    selected_by_entry: dict[str, list[dict[str, object]]],
    prices: dict[str, dict[str, float]],
    calendar: list[str],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    cash = INITIAL_CAPITAL
    open_positions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    skips: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []
    entry_decisions: list[dict[str, object]] = []

    for day in calendar:
        remaining: list[dict[str, object]] = []
        exits_closed = 0
        for position in open_positions:
            if position["planned_exit_date"] == day:
                symbol = str(position["symbol"])
                exit_ref = prices.get(symbol, {}).get(day)
                if exit_ref is None:
                    remaining.append(position)
                    continue
                exit_price = exit_ref * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0)
                gross_exit = float(position["shares"]) * exit_price
                exit_fee = gross_exit * (EXIT_FEE_BPS / 10000.0)
                net_exit = gross_exit - exit_fee
                cash += net_exit
                pnl = net_exit - float(position["entry_cash_spent"])
                trade = dict(position)
                trade.update(
                    {
                        "exit_date": day,
                        "exit_adj_close": f"{exit_ref:.6f}",
                        "exit_price_after_slippage": f"{exit_price:.6f}",
                        "exit_fee": f"{exit_fee:.6f}",
                        "net_exit_value": f"{net_exit:.6f}",
                        "pnl": f"{pnl:.6f}",
                        "return_pct": f"{((net_exit / float(position['entry_cash_spent'])) - 1.0) * 100.0:.6f}",
                        "fill_state": "closed",
                    }
                )
                trades.append(trade)
                exits_closed += 1
            else:
                remaining.append(position)
        open_positions = remaining

        available_slots = max(SLOT_CAP - len(open_positions), 0)
        policy_candidates = selected_by_entry.get(day, [])
        selected = policy_candidates[:available_slots]
        deferred = policy_candidates[available_slots:]
        for order, decision in enumerate(selected, start=1):
            entry_decisions.append(
                {
                    "policy_id": POLICY_ID,
                    "trade_spec_id": decision["trade_spec_id"],
                    "entry_date": day,
                    "symbol": decision["symbol"],
                    "theme": decision["theme"],
                    "shadow_rank_score": decision["shadow_rank_score"],
                    "trader_action": decision["trader_action"],
                    "entry_decision_state": "entered",
                    "entry_order": order,
                    "open_positions_before_entry": len(open_positions),
                    "available_slots": available_slots,
                    "blocked_reason": "",
                    "authority": AUTHORITY,
                }
            )
        for decision in deferred:
            entry_decisions.append(
                {
                    "policy_id": POLICY_ID,
                    "trade_spec_id": decision["trade_spec_id"],
                    "entry_date": day,
                    "symbol": decision["symbol"],
                    "theme": decision["theme"],
                    "shadow_rank_score": decision["shadow_rank_score"],
                    "trader_action": decision["trader_action"],
                    "entry_decision_state": "deferred_by_live_slot_cap",
                    "entry_order": "",
                    "open_positions_before_entry": len(open_positions),
                    "available_slots": available_slots,
                    "blocked_reason": "slot_cap_already_occupied_by_open_positions",
                    "authority": AUTHORITY,
                }
            )
        valid_orders: list[tuple[dict[str, str], dict[str, object], float, float]] = []
        for decision in selected:
            spec = specs_by_id[str(decision["trade_spec_id"])]
            symbol = spec["symbol"]
            entry_ref = prices.get(symbol, {}).get(day)
            exit_date = date_part(spec["planned_exit_not_after_ts"])
            exit_ref = prices.get(symbol, {}).get(exit_date)
            if entry_ref is None:
                skips.append({**spec, "policy_id": POLICY_ID, "skip_date": day, "skip_reason": "missing_exact_entry_price", "authority": AUTHORITY})
                continue
            if exit_ref is None:
                skips.append({**spec, "policy_id": POLICY_ID, "skip_date": day, "skip_reason": "missing_exact_planned_exit_price", "authority": AUTHORITY})
                continue
            entry_price = entry_ref * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0)
            valid_orders.append((spec, decision, entry_ref, entry_price))

        per_slot_cash = cash / len(valid_orders) if valid_orders else 0.0
        for spec, decision, entry_ref, entry_price in valid_orders:
            entry_fee = per_slot_cash * (ENTRY_FEE_BPS / 10000.0)
            entry_notional = max(per_slot_cash - entry_fee, 0.0)
            entry_cash_spent = entry_notional + entry_fee
            if entry_cash_spent <= 0.000001:
                skips.append({**spec, "policy_id": POLICY_ID, "skip_date": day, "skip_reason": "no_available_cash", "authority": AUTHORITY})
                continue
            shares = entry_notional / entry_price
            cash -= entry_cash_spent
            open_positions.append(
                {
                    "policy_id": POLICY_ID,
                    "trade_spec_id": spec["trade_spec_id"],
                    "adapter_input_id": spec["adapter_input_id"],
                    "candidate_bundle_id": spec["candidate_bundle_id"],
                    "trader_decision_id": spec["trader_decision_id"],
                    "source_graph_id": spec["source_graph_id"],
                    "decision_asof_ts": spec["decision_asof_ts"],
                    "split_id": spec["split_id"],
                    "theme": spec["theme"],
                    "symbol": spec["symbol"],
                    "side": spec["side"],
                    "shadow_rank_score": decision["shadow_rank_score"],
                    "trader_action": decision["trader_action"],
                    "entry_date": day,
                    "planned_exit_date": date_part(spec["planned_exit_not_after_ts"]),
                    "entry_adj_close": f"{entry_ref:.6f}",
                    "entry_price_after_slippage": f"{entry_price:.6f}",
                    "entry_notional": f"{entry_notional:.6f}",
                    "entry_fee": f"{entry_fee:.6f}",
                    "entry_cash_spent": f"{entry_cash_spent:.6f}",
                    "shares": f"{shares:.10f}",
                    "authority": AUTHORITY,
                }
            )

        market_value = 0.0
        for position in open_positions:
            px = prices.get(str(position["symbol"]), {}).get(day)
            if px is not None:
                market_value += float(position["shares"]) * px
        equity_rows.append(
            {
                "policy_id": POLICY_ID,
                "date": day,
                "cash": f"{cash:.6f}",
                "open_market_value": f"{market_value:.6f}",
                "equity": f"{cash + market_value:.6f}",
                "open_positions": len(open_positions),
                "entry_candidates": len(selected_by_entry.get(day, [])),
                "entries_selected": len(selected),
                "exits_closed": exits_closed,
                "authority": AUTHORITY,
            }
        )

    final_day = calendar[-1]
    forced_count = 0
    for position in list(open_positions):
        symbol = str(position["symbol"])
        exit_ref = prices.get(symbol, {}).get(final_day)
        if exit_ref is None:
            continue
        exit_price = exit_ref * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0)
        gross_exit = float(position["shares"]) * exit_price
        exit_fee = gross_exit * (EXIT_FEE_BPS / 10000.0)
        net_exit = gross_exit - exit_fee
        cash += net_exit
        pnl = net_exit - float(position["entry_cash_spent"])
        trade = dict(position)
        trade.update(
            {
                "exit_date": final_day,
                "exit_adj_close": f"{exit_ref:.6f}",
                "exit_price_after_slippage": f"{exit_price:.6f}",
                "exit_fee": f"{exit_fee:.6f}",
                "net_exit_value": f"{net_exit:.6f}",
                "pnl": f"{pnl:.6f}",
                "return_pct": f"{((net_exit / float(position['entry_cash_spent'])) - 1.0) * 100.0:.6f}",
                "fill_state": "forced_closed_period_end",
            }
        )
        trades.append(trade)
        forced_count += 1
    open_positions.clear()
    if forced_count:
        equity_rows.append(
            {
                "policy_id": POLICY_ID,
                "date": final_day,
                "cash": f"{cash:.6f}",
                "open_market_value": "0.000000",
                "equity": f"{cash:.6f}",
                "open_positions": 0,
                "entry_candidates": 0,
                "entries_selected": 0,
                "exits_closed": forced_count,
                "authority": AUTHORITY,
            }
        )

    equity_values = [float(row["equity"]) for row in equity_rows]
    final_equity = equity_values[-1]
    qqq = prices["QQQ"]
    qqq_start = next(day for day in calendar if day in qqq)
    qqq_end = max(day for day in calendar if day in qqq)
    qqq_final = INITIAL_CAPITAL * qqq[qqq_end] / qqq[qqq_start]
    strategy_cagr = annualized_return(INITIAL_CAPITAL, final_equity, str(equity_rows[0]["date"]), str(equity_rows[-1]["date"]))
    strategy_mdd = max_drawdown(equity_values)
    summary = {
        "policy_id": POLICY_ID,
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "initial_capital": round(INITIAL_CAPITAL, 2),
        "policy_preselected_entries": sum(len(rows) for rows in selected_by_entry.values()),
        "selected_entries": sum(1 for row in entry_decisions if row["entry_decision_state"] == "entered"),
        "deferred_by_live_slot_cap": sum(1 for row in entry_decisions if row["entry_decision_state"] == "deferred_by_live_slot_cap"),
        "closed_trades": len(trades),
        "skipped_orders": len(skips),
        "forced_closed_period_end": forced_count,
        "strategy_final_equity": round(final_equity, 2),
        "strategy_total_return_pct": round(((final_equity / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "strategy_cagr_pct": round(strategy_cagr, 6),
        "strategy_max_drawdown_pct": round(strategy_mdd, 6),
        "qqq_final_equity": round(qqq_final, 2),
        "qqq_total_return_pct": round(((qqq_final / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "qqq_cagr_pct": round(annualized_return(INITIAL_CAPITAL, qqq_final, qqq_start, qqq_end), 6),
        "meets_cagr_30": "1" if strategy_cagr >= 30.0 else "0",
        "meets_mdd_minus30": "1" if strategy_mdd >= -30.0 else "0",
        "beats_qqq": "1" if final_equity > qqq_final else "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    return entry_decisions, trades, skips, equity_rows, summary


def build() -> dict[str, object]:
    specs = [row for row in read_csv(SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    specs_by_id = {row["trade_spec_id"]: row for row in specs}
    ranking_rows = read_csv(SHADOW_RANKING_PATH)
    selection_ledger, selected_by_entry = build_policy_selection(ranking_rows)
    calendar = [row["session_date"] for row in read_csv(CALENDAR_PATH) if PERIOD_START <= row["session_date"] <= PERIOD_END]
    prices = load_prices({row["symbol"] for row in specs} | {"QQQ"})
    entry_decisions, trades, skips, equity, replay_summary = replay(specs_by_id, selected_by_entry, prices, calendar)
    baseline_summary = next(row for row in read_csv(BASELINE_SUMMARY_PATH) if row["slot_cap"] == "10")
    baseline_trades = [row for row in read_csv(BASELINE_TRADES_PATH) if row["slot_cap"] == "10"]
    baseline_ids = {row["trade_spec_id"] for row in baseline_trades}
    replay_ids = {row["trade_spec_id"] for row in trades}

    policy = {
        "policy_id": POLICY_ID,
        "source_ranking_path": SHADOW_RANKING_PATH.relative_to(ROOT).as_posix(),
        "source_ranking_sha256": sha256(SHADOW_RANKING_PATH),
        "slot_cap": SLOT_CAP,
        "rank_rule": "entry_date_cohort_top10_by_shadow_rank_score_desc_action_enter_monitor_wait_theme_symbol_trade_spec_id",
        "eligibility_rule": "exclude_only_trader_action_hard_block",
        "allowed_hard_block_reasons": ALLOWED_HARD_BLOCK_REASONS,
        "cost_slippage_rule": "Task941_same_5bps_entry_5bps_exit_10bps_round_trip",
        "forbidden_inputs": FORBIDDEN_OUTCOME_INPUTS,
        "pre_registered_before_replay": "1",
        "authority": AUTHORITY,
    }
    comparison = {
        "comparison_id": "task971_980_vs_task941_slot10",
        "baseline_final_equity": baseline_summary["strategy_final_equity"],
        "baseline_cagr_pct": baseline_summary["strategy_cagr_pct"],
        "baseline_mdd_pct": baseline_summary["strategy_max_drawdown_pct"],
        "baseline_beats_qqq": baseline_summary["beats_qqq"],
        "replay_final_equity": replay_summary["strategy_final_equity"],
        "replay_cagr_pct": replay_summary["strategy_cagr_pct"],
        "replay_mdd_pct": replay_summary["strategy_max_drawdown_pct"],
        "replay_beats_qqq": replay_summary["beats_qqq"],
        "beats_baseline_final_equity": "1" if float(replay_summary["strategy_final_equity"]) > float(baseline_summary["strategy_final_equity"]) else "0",
        "baseline_trade_count": len(baseline_ids),
        "replay_trade_count": len(replay_ids),
        "overlap_count": len(baseline_ids & replay_ids),
        "replay_only_count": len(replay_ids - baseline_ids),
        "baseline_only_count": len(baseline_ids - replay_ids),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    by_split_rows: list[dict[str, object]] = []
    for split in sorted({str(row["split_id"]) for row in trades}):
        split_rows = [row for row in trades if row["split_id"] == split]
        spent = sum(float(row["entry_cash_spent"]) for row in split_rows)
        pnl = sum(float(row["pnl"]) for row in split_rows)
        by_split_rows.append(
            {
                "policy_id": POLICY_ID,
                "split_id": split,
                "closed_trades": len(split_rows),
                "entry_cash_spent": f"{spent:.6f}",
                "pnl": f"{pnl:.6f}",
                "return_on_spent_pct": f"{((pnl / spent) * 100.0) if spent else 0.0:.6f}",
                "authority": AUTHORITY,
            }
        )
    source_manifest = [
        {"source_name": "task969_shadow_trader_ranking", "path": SHADOW_RANKING_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(SHADOW_RANKING_PATH), "authority": AUTHORITY},
        {"source_name": "task929_controlled_trade_specs", "path": SPEC_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(SPEC_PATH), "authority": AUTHORITY},
        {"source_name": "task941_baseline_summary", "path": BASELINE_SUMMARY_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(BASELINE_SUMMARY_PATH), "authority": AUTHORITY},
        {"source_name": "task941_baseline_trades", "path": BASELINE_TRADES_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(BASELINE_TRADES_PATH), "authority": AUTHORITY},
        {"source_name": "calendar", "path": CALENDAR_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(CALENDAR_PATH), "authority": AUTHORITY},
    ]
    closeout = {
        "gate_id": "Task980",
        "policy_id": POLICY_ID,
        "verdict": "controlled_replay_executed_diagnostic_only",
        "beats_task941_slot10": comparison["beats_baseline_final_equity"],
        "beats_qqq": replay_summary["beats_qqq"],
        "meets_cagr_30": replay_summary["meets_cagr_30"],
        "meets_mdd_minus30": replay_summary["meets_mdd_minus30"],
        "next_action": "failure_or_success_decomposition_before_any_policy_change",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }

    write_csv(OUT_DIR / "task971_expert_review_and_policy_freeze.csv", [policy], list(policy.keys()))
    write_csv(OUT_DIR / "task972_pre_registered_policy.csv", [policy], list(policy.keys()))
    selection_fields = [
        "policy_id", "trade_spec_id", "decision_asof_ts", "entry_date", "split_id", "symbol", "theme",
        "thesis_cluster_key", "shadow_rank_score", "shadow_rank_within_entry_date", "shadow_slot10_selected",
        "trader_action", "action_reason", "duplicate_meaning", "thesis_duration_class", "source_gap_materiality",
        "selection_rank", "selection_state", "blocked_reason",
        "policy_sort_key", "allowed_hard_block_reasons", "does_not_use", "authority",
        "changes_executed_trade",
    ]
    write_csv(OUT_DIR / "task973_policy_selection_ledger.csv", selection_ledger, selection_fields)
    trade_fields = [
        "policy_id", "trade_spec_id", "adapter_input_id", "candidate_bundle_id", "trader_decision_id",
        "source_graph_id", "decision_asof_ts", "split_id", "theme", "symbol", "side", "shadow_rank_score",
        "trader_action", "entry_date", "planned_exit_date", "entry_adj_close", "entry_price_after_slippage",
        "entry_notional", "entry_fee", "entry_cash_spent", "shares", "exit_date", "exit_adj_close",
        "exit_price_after_slippage", "exit_fee", "net_exit_value", "pnl", "return_pct", "fill_state",
        "authority",
    ]
    write_csv(OUT_DIR / "task974_replay_entry_decision_ledger.csv", entry_decisions, [
        "policy_id", "trade_spec_id", "entry_date", "symbol", "theme", "shadow_rank_score", "trader_action",
        "entry_decision_state", "entry_order", "open_positions_before_entry", "available_slots",
        "blocked_reason", "authority",
    ])
    write_csv(OUT_DIR / "task975_replay_trades.csv", trades, trade_fields)
    write_csv(OUT_DIR / "task976_replay_equity.csv", equity, ["policy_id", "date", "cash", "open_market_value", "equity", "open_positions", "entry_candidates", "entries_selected", "exits_closed", "authority"])
    skip_fields = list(skips[0].keys()) if skips else ["policy_id", "trade_spec_id", "skip_date", "skip_reason", "authority"]
    write_csv(OUT_DIR / "task977_skipped_orders.csv", skips, skip_fields)
    write_csv(OUT_DIR / "task978_replay_summary.csv", [replay_summary], list(replay_summary.keys()))
    (OUT_DIR / "task978_replay_summary.json").write_text(json.dumps(replay_summary, indent=2), encoding="utf-8")
    write_csv(OUT_DIR / "task979_by_split.csv", by_split_rows, ["policy_id", "split_id", "closed_trades", "entry_cash_spent", "pnl", "return_on_spent_pct", "authority"])
    write_csv(OUT_DIR / "task979_baseline_shadow_attribution.csv", [comparison], list(comparison.keys()))
    write_csv(OUT_DIR / "task980_source_manifest.csv", source_manifest, ["source_name", "path", "sha256", "authority"])
    write_csv(OUT_DIR / "task980_governance_closeout.csv", [closeout], list(closeout.keys()))

    summary = {
        "task_id": "Task971-980",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_id": POLICY_ID,
        "authority": AUTHORITY,
        "input_ranking_rows": len(ranking_rows),
        "policy_selection_rows": len(selection_ledger),
        "selected_entries": replay_summary["selected_entries"],
        "closed_trades": replay_summary["closed_trades"],
        "strategy_final_equity": replay_summary["strategy_final_equity"],
        "strategy_cagr_pct": replay_summary["strategy_cagr_pct"],
        "strategy_max_drawdown_pct": replay_summary["strategy_max_drawdown_pct"],
        "beats_task941_slot10": comparison["beats_baseline_final_equity"],
        "beats_qqq": replay_summary["beats_qqq"],
        "meets_cagr_30": replay_summary["meets_cagr_30"],
        "meets_mdd_minus30": replay_summary["meets_mdd_minus30"],
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_csv(OUT_DIR / "task971_980_summary.csv", [summary], list(summary.keys()))
    (OUT_DIR / "task971_980_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_971_980_EXTERNAL_AUDIT_SHADOW_REPLAY_OK] "
        f"equity={summary['strategy_final_equity']} cagr={summary['strategy_cagr_pct']} "
        f"mdd={summary['strategy_max_drawdown_pct']} beats_baseline={summary['beats_task941_slot10']}"
    )


if __name__ == "__main__":
    main()
