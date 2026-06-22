from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.trader_brain_941_950_slot_capped_selection_replay import (
    CALENDAR_PATH,
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
from scripts.trader_brain_1041_1080_golden_extractor_replay import (
    AUTHORITY,
    OUT_DIR,
    SPEC_PATH,
    build_brain_feature_panel,
    policy_sort_key,
    read_csv,
    write_csv,
)

POLICY_FAMILY = "golden_l1_l4_theme_risk_overlay"
VARIANTS = [
    {"policy_variant_id": "golden_slot8_theme_cap4_v1", "slot_cap": 8, "max_open_per_theme": 4},
    {"policy_variant_id": "golden_slot8_theme_cap3_v1", "slot_cap": 8, "max_open_per_theme": 3},
    {"policy_variant_id": "golden_slot7_theme_cap3_v1", "slot_cap": 7, "max_open_per_theme": 3},
    {"policy_variant_id": "golden_slot6_theme_cap2_v1", "slot_cap": 6, "max_open_per_theme": 2},
    {"policy_variant_id": "golden_slot10_theme_cap4_v1", "slot_cap": 10, "max_open_per_theme": 4},
    {"policy_variant_id": "golden_slot10_theme_cap3_v1", "slot_cap": 10, "max_open_per_theme": 3},
    {"policy_variant_id": "golden_slot10_theme_cap2_v1", "slot_cap": 10, "max_open_per_theme": 2},
    {"policy_variant_id": "golden_slot5_theme_cap2_v1", "slot_cap": 5, "max_open_per_theme": 2},
]


def replay_theme_cap(
    policy_variant_id: str,
    slot_cap: int,
    max_open_per_theme: int,
    specs_by_id: dict[str, dict[str, str]],
    features_by_entry: dict[str, list[dict[str, object]]],
    prices: dict[str, dict[str, float]],
    calendar: list[str],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    cash = INITIAL_CAPITAL
    open_positions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []

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

        available_slots = max(slot_cap - len(open_positions), 0)
        open_theme_counts: dict[str, int] = defaultdict(int)
        for position in open_positions:
            open_theme_counts[str(position["theme"])] += 1

        selected: list[dict[str, object]] = []
        rejected: list[dict[str, object]] = []
        selected_theme_counts: dict[str, int] = defaultdict(int)
        for feature in sorted(features_by_entry.get(day, []), key=policy_sort_key):
            theme = str(feature["theme"])
            if len(selected) >= available_slots:
                rejected.append({**feature, "blocked_reason": "slot_cap_filled"})
                continue
            if open_theme_counts[theme] + selected_theme_counts[theme] >= max_open_per_theme:
                rejected.append({**feature, "blocked_reason": "theme_cap_filled"})
                continue
            selected.append(feature)
            selected_theme_counts[theme] += 1

        for order, feature in enumerate(selected, start=1):
            decisions.append(
                {
                    **feature,
                    "policy_variant_id": policy_variant_id,
                    "slot_cap": slot_cap,
                    "max_open_per_theme": max_open_per_theme,
                    "decision_state": "selected",
                    "selection_order": order,
                    "blocked_reason": "",
                    "authority": AUTHORITY,
                }
            )
        for feature in rejected:
            decisions.append(
                {
                    **feature,
                    "policy_variant_id": policy_variant_id,
                    "slot_cap": slot_cap,
                    "max_open_per_theme": max_open_per_theme,
                    "decision_state": "rejected",
                    "selection_order": "",
                    "authority": AUTHORITY,
                }
            )

        valid_orders: list[tuple[dict[str, str], dict[str, object], float, float]] = []
        for feature in selected:
            spec = specs_by_id[str(feature["trade_spec_id"])]
            symbol = spec["symbol"]
            entry_ref = prices.get(symbol, {}).get(day)
            exit_ref = prices.get(symbol, {}).get(date_part(spec["planned_exit_not_after_ts"]))
            if entry_ref is None or exit_ref is None:
                continue
            valid_orders.append((spec, feature, entry_ref, entry_ref * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0)))

        per_slot_cash = cash / len(valid_orders) if valid_orders else 0.0
        for spec, feature, entry_ref, entry_price in valid_orders:
            entry_fee = per_slot_cash * (ENTRY_FEE_BPS / 10000.0)
            entry_notional = max(per_slot_cash - entry_fee, 0.0)
            entry_cash_spent = entry_notional + entry_fee
            if entry_cash_spent <= 0:
                continue
            shares = entry_notional / entry_price
            cash -= entry_cash_spent
            open_positions.append(
                {
                    "policy_family": POLICY_FAMILY,
                    "policy_variant_id": policy_variant_id,
                    "slot_cap": slot_cap,
                    "max_open_per_theme": max_open_per_theme,
                    "trade_spec_id": spec["trade_spec_id"],
                    "symbol": spec["symbol"],
                    "theme": spec["theme"],
                    "side": spec["side"],
                    "decision_asof_ts": spec["decision_asof_ts"],
                    "entry_date": day,
                    "planned_exit_date": date_part(spec["planned_exit_not_after_ts"]),
                    "golden_l1_l4_brain_score": feature["golden_l1_l4_brain_score"],
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
                "policy_variant_id": policy_variant_id,
                "slot_cap": slot_cap,
                "max_open_per_theme": max_open_per_theme,
                "date": day,
                "cash": f"{cash:.6f}",
                "open_market_value": f"{market_value:.6f}",
                "equity": f"{cash + market_value:.6f}",
                "open_positions": len(open_positions),
                "entries_selected": len(selected),
                "exits_closed": exits_closed,
                "authority": AUTHORITY,
            }
        )

    final_day = calendar[-1]
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
    open_positions.clear()
    equity_rows.append(
        {
            "policy_variant_id": policy_variant_id,
            "slot_cap": slot_cap,
            "max_open_per_theme": max_open_per_theme,
            "date": final_day,
            "cash": f"{cash:.6f}",
            "open_market_value": "0.000000",
            "equity": f"{cash:.6f}",
            "open_positions": 0,
            "entries_selected": 0,
            "exits_closed": 0,
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
        "policy_variant_id": policy_variant_id,
        "slot_cap": slot_cap,
        "max_open_per_theme": max_open_per_theme,
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "initial_capital": round(INITIAL_CAPITAL, 2),
        "selected_entries": sum(1 for row in decisions if row["decision_state"] == "selected"),
        "closed_trades": len(trades),
        "strategy_final_equity": round(final_equity, 2),
        "strategy_cagr_pct": round(strategy_cagr, 6),
        "strategy_max_drawdown_pct": round(strategy_mdd, 6),
        "qqq_final_equity": round(qqq_final, 2),
        "qqq_cagr_pct": round(annualized_return(INITIAL_CAPITAL, qqq_final, qqq_start, qqq_end), 6),
        "beats_qqq": "1" if final_equity > qqq_final else "0",
        "meets_cagr_30": "1" if strategy_cagr >= 30.0 else "0",
        "meets_mdd_minus30": "1" if strategy_mdd >= -30.0 else "0",
        "historical_source_time_gap": "1",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    return decisions, trades, equity_rows, summary


def build() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    specs = [row for row in read_csv(SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    specs_by_id = {row["trade_spec_id"]: row for row in specs}
    features_by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for feature in build_brain_feature_panel():
        features_by_entry[str(feature["entry_date"])].append(feature)
    calendar = [row["session_date"] for row in read_csv(CALENDAR_PATH) if PERIOD_START <= row["session_date"] <= PERIOD_END]
    prices = load_prices({row["symbol"] for row in specs} | {"QQQ"})

    all_decisions: list[dict[str, object]] = []
    all_trades: list[dict[str, object]] = []
    all_equity: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for variant in VARIANTS:
        decisions, trades, equity, summary = replay_theme_cap(
            str(variant["policy_variant_id"]),
            int(variant["slot_cap"]),
            int(variant["max_open_per_theme"]),
            specs_by_id,
            features_by_entry,
            prices,
            calendar,
        )
        all_decisions.extend(decisions)
        all_trades.extend(trades)
        all_equity.extend(equity)
        summaries.append(summary)

    best_by_goal = sorted(
        summaries,
        key=lambda row: (
            row["meets_cagr_30"] == "1" and row["meets_mdd_minus30"] == "1",
            float(row["strategy_final_equity"]),
            float(row["strategy_max_drawdown_pct"]),
        ),
        reverse=True,
    )[0]

    write_csv(OUT_DIR / "task1052_golden_risk_overlay_selection_ledger.csv", all_decisions, list(all_decisions[0].keys()))
    write_csv(OUT_DIR / "task1053_golden_risk_overlay_replay_trades.csv", all_trades, list(all_trades[0].keys()))
    write_csv(OUT_DIR / "task1054_golden_risk_overlay_equity_curves.csv", all_equity, list(all_equity[0].keys()))
    write_csv(OUT_DIR / "task1055_golden_risk_overlay_summary.csv", summaries, list(summaries[0].keys()))

    closeout_path = OUT_DIR / "task1080_golden_extractor_replay_closeout.json"
    closeout = json.loads(closeout_path.read_text(encoding="utf-8"))
    closeout.update(
        {
            "risk_overlay_variants": len(summaries),
            "risk_overlay_best_variant": best_by_goal["policy_variant_id"],
            "risk_overlay_best_final_equity": best_by_goal["strategy_final_equity"],
            "risk_overlay_best_cagr_pct": best_by_goal["strategy_cagr_pct"],
            "risk_overlay_best_mdd_pct": best_by_goal["strategy_max_drawdown_pct"],
            "risk_overlay_best_meets_cagr_30": best_by_goal["meets_cagr_30"],
            "risk_overlay_best_meets_mdd_minus30": best_by_goal["meets_mdd_minus30"],
        }
    )
    (OUT_DIR / "task1080_golden_extractor_replay_closeout.json").write_text(json.dumps(closeout, indent=2), encoding="utf-8")
    write_csv(OUT_DIR / "task1080_golden_extractor_replay_closeout.csv", [closeout], list(closeout.keys()))
    return closeout


def main() -> None:
    closeout = build()
    print(
        "[TRADER_BRAIN_1041_1080_GOLDEN_RISK_OVERLAY_OK] "
        f"best={closeout['risk_overlay_best_variant']} "
        f"final={closeout['risk_overlay_best_final_equity']} "
        f"cagr={closeout['risk_overlay_best_cagr_pct']} "
        f"mdd={closeout['risk_overlay_best_mdd_pct']}"
    )


if __name__ == "__main__":
    main()
