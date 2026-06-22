from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
L4_DIR = ROOT / "data/artifacts/task_917_920_multifamily_relation_adapter"
MARKET_DIR = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay"
OUT_DIR = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"

TRADE_SPEC_PATH = SPEC_DIR / "task929_controlled_trade_specs.csv"
CANDIDATE_PATH = L4_DIR / "task919_l4_candidate_bundles_contradiction.csv"
RELATION_PATH = L4_DIR / "task919_relation_edges_9primitive.csv"
DAILY_DIR = MARKET_DIR / "canonical_daily"
CALENDAR_PATH = MARKET_DIR / "calendar" / "data_derived_qqq_sessions_v1.csv"

INITIAL_CAPITAL = 1000.0
PERIOD_START = "2021-01-01"
PERIOD_END = "2026-03-31"
ENTRY_SLIPPAGE_BPS = 5.0
EXIT_SLIPPAGE_BPS = 5.0
ROUND_TRIP_COST_BPS = 10.0
ENTRY_FEE_BPS = ROUND_TRIP_COST_BPS / 2.0
EXIT_FEE_BPS = ROUND_TRIP_COST_BPS / 2.0
SLOT_CAPS = [3, 5, 10]
AUTHORITY = "DIAGNOSTIC_SLOT_CAPPED_SELECTION_REPLAY_ONLY"

THESIS_PRIORITY = {
    "source_backed_watch_packet": 3,
    "mixed_source_backed_watch_packet": 2,
    "thin_or_gap_context_packet": 1,
}
POSITIVE_PRIMITIVES = {"reinforces", "conditions", "explains"}
NEGATIVE_OR_NOISE_PRIMITIVES = {"weakens", "source_gap_for", "noise_for", "invalidates", "contradicts"}


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


def date_part(ts: str) -> str:
    return ts[:10]


def load_prices(symbols: set[str]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for symbol in sorted(symbols):
        path = DAILY_DIR / f"{symbol}.csv"
        prices: dict[str, float] = {}
        if path.exists():
            for row in read_csv(path):
                day = row["timestamp"]
                if PERIOD_START <= day <= PERIOD_END:
                    prices[day] = float(row["adj_close"])
        out[symbol] = prices
    return out


def max_drawdown(equity_values: list[float]) -> float:
    peak = -math.inf
    max_dd = 0.0
    for value in equity_values:
        peak = max(peak, value)
        if peak > 0:
            max_dd = min(max_dd, (value / peak) - 1.0)
    return max_dd * 100.0


def annualized_return(start_value: float, end_value: float, start_date: str, end_date: str) -> float:
    d0 = datetime.fromisoformat(start_date)
    d1 = datetime.fromisoformat(end_date)
    years = max((d1 - d0).days, 1) / 365.25
    return ((end_value / start_value) ** (1.0 / years) - 1.0) * 100.0


def source_families(evidence_ids: str) -> set[str]:
    families = set()
    for item in evidence_ids.split(";"):
        parts = item.split("|")
        if len(parts) >= 3:
            families.add(parts[1])
        elif parts:
            families.add(parts[0])
    return families


def relation_features(candidate: dict[str, str], relations: dict[str, dict[str, str]]) -> dict[str, int]:
    support_ids = [item for item in candidate["supporting_relation_ids"].split(";") if item]
    gap_ids = [item for item in candidate["source_gap_relation_ids"].split(";") if item]
    primitives = [relations[item]["relation_primitive"] for item in support_ids + gap_ids if item in relations]
    return {
        "support_relation_count": len(support_ids),
        "source_gap_relation_count": len(gap_ids),
        "positive_relation_count": sum(1 for primitive in primitives if primitive in POSITIVE_PRIMITIVES),
        "negative_or_noise_relation_count": sum(1 for primitive in primitives if primitive in NEGATIVE_OR_NOISE_PRIMITIVES),
    }


def build_selection_features(specs: list[dict[str, str]], candidates: dict[str, dict[str, str]], relations: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in specs:
        candidate = candidates[spec["candidate_bundle_id"]]
        rel = relation_features(candidate, relations)
        families = source_families(candidate["supporting_evidence_ids"])
        unresolved_gap_count = len([item for item in candidate["unresolved_source_gaps"].split(";") if item])
        thesis_priority = THESIS_PRIORITY.get(candidate["candidate_thesis_type"], 0)
        selection_key = (
            thesis_priority,
            len(families),
            rel["support_relation_count"],
            rel["positive_relation_count"],
            -unresolved_gap_count,
            -rel["source_gap_relation_count"],
            -rel["negative_or_noise_relation_count"],
            spec["theme"],
            spec["symbol"],
            spec["trade_spec_id"],
        )
        rows.append(
            {
                "trade_spec_id": spec["trade_spec_id"],
                "adapter_input_id": spec["adapter_input_id"],
                "candidate_bundle_id": spec["candidate_bundle_id"],
                "decision_asof_ts": spec["decision_asof_ts"],
                "entry_date": date_part(spec["tradable_after_ts"]),
                "split_id": spec["split_id"],
                "theme": spec["theme"],
                "symbol": spec["symbol"],
                "candidate_thesis_type": candidate["candidate_thesis_type"],
                "thesis_priority": thesis_priority,
                "source_family_count": len(families),
                "support_relation_count": rel["support_relation_count"],
                "positive_relation_count": rel["positive_relation_count"],
                "source_gap_relation_count": rel["source_gap_relation_count"],
                "negative_or_noise_relation_count": rel["negative_or_noise_relation_count"],
                "unresolved_source_gap_count": unresolved_gap_count,
                "contradiction_state": candidate["contradiction_state"],
                "selection_key": "|".join(str(item) for item in selection_key),
                "does_not_use": "future_return realized_return pnl price_change rank_score_from_outcome",
                "authority": AUTHORITY,
            }
        )
    return rows


def selection_sort_key(feature: dict[str, object]) -> tuple[object, ...]:
    return (
        -int(feature["thesis_priority"]),
        -int(feature["source_family_count"]),
        -int(feature["support_relation_count"]),
        -int(feature["positive_relation_count"]),
        int(feature["unresolved_source_gap_count"]),
        int(feature["source_gap_relation_count"]),
        int(feature["negative_or_noise_relation_count"]),
        str(feature["theme"]),
        str(feature["symbol"]),
        str(feature["trade_spec_id"]),
    )


def replay_variant(slot_cap: int, specs_by_id: dict[str, dict[str, str]], features_by_entry: dict[str, list[dict[str, object]]], prices: dict[str, dict[str, float]], calendar: list[str]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    cash = INITIAL_CAPITAL
    open_positions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    skips: list[dict[str, object]] = []
    selections: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []

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
        candidates = sorted(features_by_entry.get(day, []), key=selection_sort_key)
        selected = candidates[:available_slots]
        rejected = candidates[available_slots:]
        for order, feature in enumerate(selected, start=1):
            selections.append(
                {
                    **feature,
                    "slot_cap": slot_cap,
                    "selection_state": "selected",
                    "selection_order": order,
                    "open_positions_before_entry": len(open_positions),
                    "available_slots": available_slots,
                    "blocked_reason": "",
                }
            )
        for feature in rejected:
            selections.append(
                {
                    **feature,
                    "slot_cap": slot_cap,
                    "selection_state": "rejected_by_slot_cap",
                    "selection_order": "",
                    "open_positions_before_entry": len(open_positions),
                    "available_slots": available_slots,
                    "blocked_reason": "slot_cap_filled_by_higher_priority_candidates",
                }
            )

        valid_orders: list[tuple[dict[str, str], float, float]] = []
        for feature in selected:
            spec = specs_by_id[str(feature["trade_spec_id"])]
            symbol = spec["symbol"]
            entry_ref = prices.get(symbol, {}).get(day)
            exit_date = date_part(spec["planned_exit_not_after_ts"])
            exit_ref = prices.get(symbol, {}).get(exit_date)
            if entry_ref is None:
                skips.append({**spec, "slot_cap": slot_cap, "skip_date": day, "skip_reason": "missing_exact_entry_price", "authority": AUTHORITY})
                continue
            if exit_ref is None:
                skips.append({**spec, "slot_cap": slot_cap, "skip_date": day, "skip_reason": "missing_exact_planned_exit_price", "authority": AUTHORITY})
                continue
            entry_price = entry_ref * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0)
            valid_orders.append((spec, entry_ref, entry_price))

        per_slot_cash = cash / len(valid_orders) if valid_orders else 0.0
        for spec, entry_ref, entry_price in valid_orders:
            entry_fee = per_slot_cash * (ENTRY_FEE_BPS / 10000.0)
            entry_notional = max(per_slot_cash - entry_fee, 0.0)
            entry_cash_spent = entry_notional + entry_fee
            if entry_cash_spent <= 0.000001:
                skips.append({**spec, "slot_cap": slot_cap, "skip_date": day, "skip_reason": "no_available_cash", "authority": AUTHORITY})
                continue
            shares = entry_notional / entry_price
            cash -= entry_cash_spent
            open_positions.append(
                {
                    "slot_cap": slot_cap,
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
                "slot_cap": slot_cap,
                "date": day,
                "cash": f"{cash:.6f}",
                "open_market_value": f"{market_value:.6f}",
                "equity": f"{cash + market_value:.6f}",
                "open_positions": len(open_positions),
                "entry_candidates": len(candidates),
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
                "slot_cap": slot_cap,
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
    summary = {
        "slot_cap": slot_cap,
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "initial_capital": round(INITIAL_CAPITAL, 2),
        "selected_entries": sum(1 for row in selections if row["selection_state"] == "selected"),
        "rejected_by_slot_cap": sum(1 for row in selections if row["selection_state"] == "rejected_by_slot_cap"),
        "closed_trades": len(trades),
        "skipped_orders": len(skips),
        "forced_closed_period_end": forced_count,
        "strategy_final_equity": round(final_equity, 2),
        "strategy_total_return_pct": round(((final_equity / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "strategy_cagr_pct": round(annualized_return(INITIAL_CAPITAL, final_equity, str(equity_rows[0]["date"]), str(equity_rows[-1]["date"])), 6),
        "strategy_max_drawdown_pct": round(max_drawdown(equity_values), 6),
        "qqq_final_equity": round(qqq_final, 2),
        "qqq_total_return_pct": round(((qqq_final / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "qqq_cagr_pct": round(annualized_return(INITIAL_CAPITAL, qqq_final, qqq_start, qqq_end), 6),
        "meets_cagr_30": "1" if annualized_return(INITIAL_CAPITAL, final_equity, str(equity_rows[0]["date"]), str(equity_rows[-1]["date"])) >= 30.0 else "0",
        "meets_mdd_minus30": "1" if max_drawdown(equity_values) >= -30.0 else "0",
        "beats_qqq": "1" if final_equity > qqq_final else "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    return selections, trades, skips, equity_rows, summary


def build() -> dict[str, object]:
    specs = [row for row in read_csv(TRADE_SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    candidates = {row["candidate_bundle_id"]: row for row in read_csv(CANDIDATE_PATH)}
    relations = {row["relation_edge_id"]: row for row in read_csv(RELATION_PATH)}
    features = build_selection_features(specs, candidates, relations)
    specs_by_id = {row["trade_spec_id"]: row for row in specs}
    features_by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for feature in features:
        features_by_entry[str(feature["entry_date"])].append(feature)

    calendar = [row["session_date"] for row in read_csv(CALENDAR_PATH) if PERIOD_START <= row["session_date"] <= PERIOD_END]
    prices = load_prices({row["symbol"] for row in specs} | {"QQQ"})

    all_selections: list[dict[str, object]] = []
    all_trades: list[dict[str, object]] = []
    all_skips: list[dict[str, object]] = []
    all_equity: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []

    for slot_cap in SLOT_CAPS:
        selections, trades, skips, equity, summary = replay_variant(slot_cap, specs_by_id, features_by_entry, prices, calendar)
        all_selections.extend(selections)
        all_trades.extend(trades)
        all_skips.extend(skips)
        all_equity.extend(equity)
        summaries.append(summary)

    best_by_final = max(summaries, key=lambda row: float(row["strategy_final_equity"]))
    best_by_drawdown = max(summaries, key=lambda row: float(row["strategy_max_drawdown_pct"]))
    closeout = [
        {
            "gate_id": "Task950",
            "tested_slot_caps": ";".join(str(cap) for cap in SLOT_CAPS),
            "best_final_equity_slot_cap": best_by_final["slot_cap"],
            "best_final_equity": best_by_final["strategy_final_equity"],
            "best_mdd_slot_cap": best_by_drawdown["slot_cap"],
            "best_mdd_pct": best_by_drawdown["strategy_max_drawdown_pct"],
            "any_meets_cagr_30": "1" if any(row["meets_cagr_30"] == "1" for row in summaries) else "0",
            "any_meets_mdd_minus30": "1" if any(row["meets_mdd_minus30"] == "1" for row in summaries) else "0",
            "any_beats_qqq": "1" if any(row["beats_qqq"] == "1" for row in summaries) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_action": "review whether ex-ante selection features are too weak before adding new filters",
            "authority": AUTHORITY,
        }
    ]

    write_csv(
        OUT_DIR / "task941_selection_feature_panel.csv",
        features,
        [
            "trade_spec_id",
            "adapter_input_id",
            "candidate_bundle_id",
            "decision_asof_ts",
            "entry_date",
            "split_id",
            "theme",
            "symbol",
            "candidate_thesis_type",
            "thesis_priority",
            "source_family_count",
            "support_relation_count",
            "positive_relation_count",
            "source_gap_relation_count",
            "negative_or_noise_relation_count",
            "unresolved_source_gap_count",
            "contradiction_state",
            "selection_key",
            "does_not_use",
            "authority",
        ],
    )
    write_csv(
        OUT_DIR / "task942_slot_capped_selection_ledger.csv",
        all_selections,
        [
            "trade_spec_id",
            "adapter_input_id",
            "candidate_bundle_id",
            "decision_asof_ts",
            "entry_date",
            "split_id",
            "theme",
            "symbol",
            "candidate_thesis_type",
            "thesis_priority",
            "source_family_count",
            "support_relation_count",
            "positive_relation_count",
            "source_gap_relation_count",
            "negative_or_noise_relation_count",
            "unresolved_source_gap_count",
            "contradiction_state",
            "selection_key",
            "does_not_use",
            "authority",
            "slot_cap",
            "selection_state",
            "selection_order",
            "open_positions_before_entry",
            "available_slots",
            "blocked_reason",
        ],
    )
    trade_fields = [
        "slot_cap",
        "trade_spec_id",
        "adapter_input_id",
        "candidate_bundle_id",
        "trader_decision_id",
        "source_graph_id",
        "decision_asof_ts",
        "split_id",
        "theme",
        "symbol",
        "side",
        "entry_date",
        "planned_exit_date",
        "entry_adj_close",
        "entry_price_after_slippage",
        "entry_notional",
        "entry_fee",
        "entry_cash_spent",
        "shares",
        "exit_date",
        "exit_adj_close",
        "exit_price_after_slippage",
        "exit_fee",
        "net_exit_value",
        "pnl",
        "return_pct",
        "fill_state",
        "authority",
    ]
    write_csv(OUT_DIR / "task943_slot_capped_replay_trades.csv", all_trades, trade_fields)
    write_csv(
        OUT_DIR / "task944_slot_capped_equity_curves.csv",
        all_equity,
        ["slot_cap", "date", "cash", "open_market_value", "equity", "open_positions", "entry_candidates", "entries_selected", "exits_closed", "authority"],
    )
    skip_fields = list(all_skips[0].keys()) if all_skips else ["slot_cap", "trade_spec_id", "skip_date", "skip_reason", "authority"]
    write_csv(OUT_DIR / "task945_slot_capped_skipped_orders.csv", all_skips, skip_fields)
    write_csv(
        OUT_DIR / "task946_slot_capped_summary.csv",
        summaries,
        [
            "slot_cap",
            "period_start",
            "period_end",
            "initial_capital",
            "selected_entries",
            "rejected_by_slot_cap",
            "closed_trades",
            "skipped_orders",
            "forced_closed_period_end",
            "strategy_final_equity",
            "strategy_total_return_pct",
            "strategy_cagr_pct",
            "strategy_max_drawdown_pct",
            "qqq_final_equity",
            "qqq_total_return_pct",
            "qqq_cagr_pct",
            "meets_cagr_30",
            "meets_mdd_minus30",
            "beats_qqq",
            "strategy_acceptance",
            "deployment_readiness",
            "real_capital",
            "authority",
        ],
    )
    (OUT_DIR / "task946_slot_capped_summary.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")

    by_split_rows: list[dict[str, object]] = []
    for slot_cap in SLOT_CAPS:
        cap_trades = [row for row in all_trades if int(row["slot_cap"]) == slot_cap]
        for split in sorted({str(row["split_id"]) for row in cap_trades}):
            split_rows = [row for row in cap_trades if row["split_id"] == split]
            spent = sum(float(row["entry_cash_spent"]) for row in split_rows)
            pnl = sum(float(row["pnl"]) for row in split_rows)
            by_split_rows.append(
                {
                    "slot_cap": slot_cap,
                    "split_id": split,
                    "closed_trades": len(split_rows),
                    "entry_cash_spent": f"{spent:.6f}",
                    "pnl": f"{pnl:.6f}",
                    "return_on_spent_pct": f"{((pnl / spent) * 100.0) if spent else 0.0:.6f}",
                    "authority": AUTHORITY,
                }
            )
    write_csv(OUT_DIR / "task947_slot_capped_by_split.csv", by_split_rows, ["slot_cap", "split_id", "closed_trades", "entry_cash_spent", "pnl", "return_on_spent_pct", "authority"])

    source_manifest = [
        {"source_name": "task929_controlled_trade_specs", "path": str(TRADE_SPEC_PATH.as_posix()), "sha256": sha256(TRADE_SPEC_PATH), "authority": AUTHORITY},
        {"source_name": "task919_l4_candidates", "path": str(CANDIDATE_PATH.as_posix()), "sha256": sha256(CANDIDATE_PATH), "authority": AUTHORITY},
        {"source_name": "task919_l3_relations", "path": str(RELATION_PATH.as_posix()), "sha256": sha256(RELATION_PATH), "authority": AUTHORITY},
        {"source_name": "calendar", "path": str(CALENDAR_PATH.as_posix()), "sha256": sha256(CALENDAR_PATH), "authority": AUTHORITY},
    ]
    write_csv(OUT_DIR / "task948_slot_capped_source_manifest.csv", source_manifest, ["source_name", "path", "sha256", "authority"])
    write_csv(
        OUT_DIR / "task950_slot_capped_governance_closeout.csv",
        closeout,
        [
            "gate_id",
            "tested_slot_caps",
            "best_final_equity_slot_cap",
            "best_final_equity",
            "best_mdd_slot_cap",
            "best_mdd_pct",
            "any_meets_cagr_30",
            "any_meets_mdd_minus30",
            "any_beats_qqq",
            "strategy_acceptance",
            "deployment_readiness",
            "real_capital",
            "next_action",
            "authority",
        ],
    )
    summary = {
        "task_id": "Task941-950",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": AUTHORITY,
        "slot_caps": SLOT_CAPS,
        "input_trade_specs": len(specs),
        "selection_feature_rows": len(features),
        "selection_ledger_rows": len(all_selections),
        "trade_rows": len(all_trades),
        "summary_rows": len(summaries),
        "best_final_equity_slot_cap": best_by_final["slot_cap"],
        "best_final_equity": best_by_final["strategy_final_equity"],
        "best_mdd_slot_cap": best_by_drawdown["slot_cap"],
        "best_mdd_pct": best_by_drawdown["strategy_max_drawdown_pct"],
        "any_meets_cagr_30": closeout[0]["any_meets_cagr_30"],
        "any_meets_mdd_minus30": closeout[0]["any_meets_mdd_minus30"],
        "any_beats_qqq": closeout[0]["any_beats_qqq"],
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (OUT_DIR / "task941_950_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_csv(OUT_DIR / "task941_950_summary.csv", [summary], list(summary.keys()))
    return summary


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_941_950_SLOT_REPLAY_OK] "
        f"best_slot={summary['best_final_equity_slot_cap']} "
        f"best_equity={summary['best_final_equity']} "
        f"mdd_slot={summary['best_mdd_slot_cap']} "
        f"mdd={summary['best_mdd_pct']}"
    )


if __name__ == "__main__":
    main()
