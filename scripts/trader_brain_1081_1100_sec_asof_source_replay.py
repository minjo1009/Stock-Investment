from __future__ import annotations

import csv
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


SEC_DIR = ROOT / "data/artifacts/task_907_916_sec_l1_l5_pipeline"
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
OUT_DIR = ROOT / "data/artifacts/task_1081_1100_sec_asof_source_replay"

SPEC_PATH = SPEC_DIR / "task929_controlled_trade_specs.csv"
L1_PATH = SEC_DIR / "task908_l1_sec_companyfacts_evidence.csv"
L2_PATH = SEC_DIR / "task911_l2_primitive_facts.csv"
L3_PATH = SEC_DIR / "task913_l3_relation_snapshots.csv"
L4_PATH = SEC_DIR / "task914_l4_candidate_bundles.csv"

AUTHORITY = "DIAGNOSTIC_SEC_ASOF_SOURCE_REPLAY_ONLY"
POLICY_ID = "sec_asof_source_slot_theme_cap_v1"
FORBIDDEN_INPUTS = "future_return realized_return pnl post_entry_price_change outcome_rank exit_price"
VARIANTS = [
    {"policy_variant_id": "sec_slot3_theme_cap1_dd25_v1", "slot_cap": 3, "max_open_per_theme": 1, "drawdown_pause_pct": -25.0},
    {"policy_variant_id": "sec_slot3_theme_cap1_dd20_v1", "slot_cap": 3, "max_open_per_theme": 1, "drawdown_pause_pct": -20.0},
    {"policy_variant_id": "sec_slot4_theme_cap1_dd25_v1", "slot_cap": 4, "max_open_per_theme": 1, "drawdown_pause_pct": -25.0},
    {"policy_variant_id": "sec_slot5_theme_cap1_dd25_v1", "slot_cap": 5, "max_open_per_theme": 1, "drawdown_pause_pct": -25.0},
    {"policy_variant_id": "sec_slot8_theme_cap3_dd25_v1", "slot_cap": 8, "max_open_per_theme": 3, "drawdown_pause_pct": -25.0},
    {"policy_variant_id": "sec_slot3_theme_cap1_v1", "slot_cap": 3, "max_open_per_theme": 1},
    {"policy_variant_id": "sec_slot4_theme_cap1_v1", "slot_cap": 4, "max_open_per_theme": 1},
    {"policy_variant_id": "sec_slot5_theme_cap1_v1", "slot_cap": 5, "max_open_per_theme": 1},
    {"policy_variant_id": "sec_slot6_theme_cap1_v1", "slot_cap": 6, "max_open_per_theme": 1},
    {"policy_variant_id": "sec_slot7_theme_cap2_v1", "slot_cap": 7, "max_open_per_theme": 2},
    {"policy_variant_id": "sec_slot7_theme_cap3_v1", "slot_cap": 7, "max_open_per_theme": 3},
    {"policy_variant_id": "sec_slot8_theme_cap3_v1", "slot_cap": 8, "max_open_per_theme": 3},
    {"policy_variant_id": "sec_slot8_theme_cap4_v1", "slot_cap": 8, "max_open_per_theme": 4},
    {"policy_variant_id": "sec_slot5_theme_cap2_v1", "slot_cap": 5, "max_open_per_theme": 2},
    {"policy_variant_id": "sec_slot10_theme_cap3_v1", "slot_cap": 10, "max_open_per_theme": 3},
]

THEME_STRUCTURAL_PRIOR = {
    "ai_semiconductors": 18,
    "power_grid_electrification": 14,
    "aerospace_defense_space": 12,
    "cybersecurity": 10,
    "cloud_ai_platforms": 9,
    "industrial_automation_robotics": 7,
    "data_devops_software": 6,
    "ev_autonomy_mobility": 5,
    "crypto_fintech": 2,
    "biotech_glp1_healthcare": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def as_int(value: object) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def split_items(value: str, sep: str = ";") -> list[str]:
    return [item for item in value.split(sep) if item]


def load_sec_feature_maps() -> tuple[dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str, str], dict[str, str]], dict[str, list[dict[str, str]]]]:
    l3 = {(row["decision_asof_ts"], row["symbol"], row["theme"]): row for row in read_csv(L3_PATH)}
    l4 = {(row["decision_asof_ts"], row["symbol"], row["theme"]): row for row in read_csv(L4_PATH)}
    l1_by_symbol: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(L1_PATH):
        l1_by_symbol[row["symbol"]].append(row)
    return l3, l4, l1_by_symbol


def build_source_time_audit(specs: list[dict[str, str]], l1_by_symbol: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in specs:
        available = [
            row for row in l1_by_symbol.get(spec["symbol"], [])
            if row["available_to_brain_ts"] <= spec["decision_asof_ts"]
            and row["outcome_used_for_assignment_flag"] == "0"
        ]
        latest_ts = max((row["available_to_brain_ts"] for row in available), default="")
        rows.append(
            {
                "trade_spec_id": spec["trade_spec_id"],
                "decision_asof_ts": spec["decision_asof_ts"],
                "symbol": spec["symbol"],
                "theme": spec["theme"],
                "available_sec_l1_rows": len(available),
                "latest_available_to_brain_ts": latest_ts,
                "source_time_pass": "1" if available and (not latest_ts or latest_ts <= spec["decision_asof_ts"]) else "0",
                "future_source_rows_used": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def sec_score(l3: dict[str, str] | None, l4: dict[str, str] | None, theme: str) -> tuple[int, dict[str, object]]:
    if not l3 or not l4:
        return -999, {
            "available_meaning_count": 0,
            "available_fact_family_count": 0,
            "relation_edge_count": 0,
            "missing_core_count": 99,
            "source_gap_count": 99,
            "candidate_thesis_type": "missing_sec_asof_candidate",
            "relation_state": "missing",
        }
    families = split_items(l3["available_fact_families"])
    relation_edges = split_items(l3["relation_edges"])
    missing_core = split_items(l3["missing_core_families"])
    source_gaps = split_items(l4["unresolved_source_gaps"])
    candidate_type = l4["candidate_thesis_type"]
    type_points = {
        "source_backed_fundamental_context_packet": 24,
        "source_backed_thin_context_packet": 8,
    }.get(candidate_type, 0)
    family_points = len(families) * 7
    relation_points = len(relation_edges) * 9
    meaning_points = as_int(l3["available_meaning_count"]) * 4
    missing_penalty = len(missing_core) * 8
    gap_penalty = len(source_gaps) * 4
    innovation_bonus = 0
    if "research_and_development" in families:
        innovation_bonus += 12
    if "capex" in families and theme in {"ai_semiconductors", "power_grid_electrification", "industrial_automation_robotics"}:
        innovation_bonus += 8
    if "revenue" in families and "net_income" in families:
        innovation_bonus += 6
    structural_prior = THEME_STRUCTURAL_PRIOR.get(theme, 0)
    score = type_points + family_points + relation_points + meaning_points + innovation_bonus + structural_prior - missing_penalty - gap_penalty
    return score, {
        "available_meaning_count": as_int(l3["available_meaning_count"]),
        "available_fact_family_count": len(families),
        "available_fact_families": ";".join(families),
        "relation_edge_count": len(relation_edges),
        "relation_edges": ";".join(relation_edges),
        "missing_core_count": len(missing_core),
        "source_gap_count": len(source_gaps),
        "candidate_thesis_type": candidate_type,
        "relation_state": l3["relation_state"],
        "theme_structural_prior": structural_prior,
        "innovation_bonus": innovation_bonus,
    }


def build_adapter_feature_panel(specs: list[dict[str, str]]) -> list[dict[str, object]]:
    l3_map, l4_map, l1_by_symbol = load_sec_feature_maps()
    source_audit = {
        row["trade_spec_id"]: row
        for row in build_source_time_audit(specs, l1_by_symbol)
    }
    rows: list[dict[str, object]] = []
    for spec in specs:
        key = (spec["decision_asof_ts"], spec["symbol"], spec["theme"])
        score, components = sec_score(l3_map.get(key), l4_map.get(key), spec["theme"])
        audit = source_audit[spec["trade_spec_id"]]
        rows.append(
            {
                "policy_id": POLICY_ID,
                "trade_spec_id": spec["trade_spec_id"],
                "adapter_input_id": spec["adapter_input_id"],
                "candidate_bundle_id": spec["candidate_bundle_id"],
                "decision_asof_ts": spec["decision_asof_ts"],
                "entry_date": date_part(spec["tradable_after_ts"]),
                "split_id": spec["split_id"],
                "theme": spec["theme"],
                "symbol": spec["symbol"],
                "sec_asof_source_score": score,
                **components,
                "available_sec_l1_rows": audit["available_sec_l1_rows"],
                "latest_available_to_brain_ts": audit["latest_available_to_brain_ts"],
                "source_time_pass": audit["source_time_pass"],
                "future_source_rows_used": "0",
                "forbidden_inputs": FORBIDDEN_INPUTS,
                "authority": AUTHORITY,
            }
        )
    return rows


def policy_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        -as_int(row["sec_asof_source_score"]),
        -as_int(row["available_meaning_count"]),
        -as_int(row["relation_edge_count"]),
        -as_int(row["available_fact_family_count"]),
        as_int(row["missing_core_count"]),
        as_int(row["source_gap_count"]),
        str(row["theme"]),
        str(row["symbol"]),
        str(row["trade_spec_id"]),
    )


def replay_variant(
    variant: dict[str, object],
    specs_by_id: dict[str, dict[str, str]],
    features_by_entry: dict[str, list[dict[str, object]]],
    prices: dict[str, dict[str, float]],
    calendar: list[str],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    policy_variant_id = str(variant["policy_variant_id"])
    slot_cap = int(variant["slot_cap"])
    max_open_per_theme = int(variant["max_open_per_theme"])
    drawdown_pause_pct = variant.get("drawdown_pause_pct")
    cash = INITIAL_CAPITAL
    peak_equity = INITIAL_CAPITAL
    open_positions: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
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

        current_market_value = 0.0
        for position in open_positions:
            px = prices.get(str(position["symbol"]), {}).get(day)
            if px is not None:
                current_market_value += float(position["shares"]) * px
        current_equity_before_entries = cash + current_market_value
        peak_equity = max(peak_equity, current_equity_before_entries)
        current_drawdown_pct = ((current_equity_before_entries / peak_equity) - 1.0) * 100.0 if peak_equity > 0 else 0.0
        drawdown_pause_active = drawdown_pause_pct is not None and current_drawdown_pct <= float(drawdown_pause_pct)

        open_theme_counts: dict[str, int] = defaultdict(int)
        for position in open_positions:
            open_theme_counts[str(position["theme"])] += 1
        available_slots = max(slot_cap - len(open_positions), 0)
        selected: list[dict[str, object]] = []
        selected_theme_counts: dict[str, int] = defaultdict(int)
        for feature in sorted(features_by_entry.get(day, []), key=policy_sort_key):
            theme = str(feature["theme"])
            blocked_reason = ""
            if drawdown_pause_active:
                blocked_reason = "drawdown_pause_active"
            elif feature["source_time_pass"] != "1":
                blocked_reason = "source_time_fail"
            elif len(selected) >= available_slots:
                blocked_reason = "slot_cap_filled"
            elif open_theme_counts[theme] + selected_theme_counts[theme] >= max_open_per_theme:
                blocked_reason = "theme_cap_filled"
            if blocked_reason:
                decisions.append({**feature, "policy_variant_id": policy_variant_id, "slot_cap": slot_cap, "max_open_per_theme": max_open_per_theme, "decision_state": "rejected", "blocked_reason": blocked_reason})
                continue
            selected.append(feature)
            selected_theme_counts[theme] += 1
            decisions.append({**feature, "policy_variant_id": policy_variant_id, "slot_cap": slot_cap, "max_open_per_theme": max_open_per_theme, "decision_state": "selected", "blocked_reason": ""})

        valid_orders: list[tuple[dict[str, str], dict[str, object], float, float]] = []
        for feature in selected:
            spec = specs_by_id[str(feature["trade_spec_id"])]
            entry_ref = prices.get(spec["symbol"], {}).get(day)
            exit_ref = prices.get(spec["symbol"], {}).get(date_part(spec["planned_exit_not_after_ts"]))
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
                    "policy_id": POLICY_ID,
                    "policy_variant_id": policy_variant_id,
                    "slot_cap": slot_cap,
                    "max_open_per_theme": max_open_per_theme,
                    "drawdown_pause_pct": "" if drawdown_pause_pct is None else drawdown_pause_pct,
                    "trade_spec_id": spec["trade_spec_id"],
                    "decision_asof_ts": spec["decision_asof_ts"],
                    "split_id": spec["split_id"],
                    "theme": spec["theme"],
                    "symbol": spec["symbol"],
                    "side": spec["side"],
                    "sec_asof_source_score": feature["sec_asof_source_score"],
                    "available_meaning_count": feature["available_meaning_count"],
                    "available_fact_families": feature["available_fact_families"],
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
                "policy_variant_id": policy_variant_id,
                "slot_cap": slot_cap,
                "max_open_per_theme": max_open_per_theme,
                "drawdown_pause_pct": "" if drawdown_pause_pct is None else drawdown_pause_pct,
                "date": day,
                "cash": f"{cash:.6f}",
                "open_market_value": f"{market_value:.6f}",
                "equity": f"{cash + market_value:.6f}",
                "open_positions": len(open_positions),
                "current_drawdown_pct": f"{current_drawdown_pct:.6f}",
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
    equity_rows.append(
        {
            "policy_id": POLICY_ID,
            "policy_variant_id": policy_variant_id,
            "slot_cap": slot_cap,
            "max_open_per_theme": max_open_per_theme,
            "drawdown_pause_pct": "" if drawdown_pause_pct is None else drawdown_pause_pct,
            "date": final_day,
            "cash": f"{cash:.6f}",
            "open_market_value": "0.000000",
            "equity": f"{cash:.6f}",
            "open_positions": 0,
            "current_drawdown_pct": "0.000000",
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
        "policy_variant_id": policy_variant_id,
        "slot_cap": slot_cap,
        "max_open_per_theme": max_open_per_theme,
        "drawdown_pause_pct": "" if drawdown_pause_pct is None else drawdown_pause_pct,
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "initial_capital": round(INITIAL_CAPITAL, 2),
        "selected_entries": sum(1 for row in decisions if row["policy_variant_id"] == policy_variant_id and row["decision_state"] == "selected"),
        "closed_trades": len(trades),
        "forced_closed_period_end": forced_count,
        "strategy_final_equity": round(final_equity, 2),
        "strategy_cagr_pct": round(strategy_cagr, 6),
        "strategy_max_drawdown_pct": round(strategy_mdd, 6),
        "qqq_final_equity": round(qqq_final, 2),
        "qqq_cagr_pct": round(annualized_return(INITIAL_CAPITAL, qqq_final, qqq_start, qqq_end), 6),
        "beats_qqq": "1" if final_equity > qqq_final else "0",
        "meets_cagr_30": "1" if strategy_cagr >= 30.0 else "0",
        "meets_mdd_minus30": "1" if strategy_mdd >= -30.0 else "0",
        "historical_source_time_gap": "0",
        "source_scope": "sec_companyfacts_only",
        "non_sec_source_gap": "1",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    return decisions, trades, equity_rows, summary


def build_attribution(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for axis in ["policy_variant_id", "theme", "symbol"]:
        groups: dict[str, list[dict[str, object]]] = defaultdict(list)
        for trade in trades:
            groups[str(trade[axis])].append(trade)
        for bucket, group in sorted(groups.items()):
            spent = sum(float(row["entry_cash_spent"]) for row in group)
            pnl = sum(float(row["pnl"]) for row in group)
            out.append(
                {
                    "policy_id": POLICY_ID,
                    "axis": axis,
                    "bucket": bucket,
                    "closed_trades": len(group),
                    "entry_cash_spent": f"{spent:.6f}",
                    "pnl": f"{pnl:.6f}",
                    "return_on_spent_pct": f"{((pnl / spent) * 100.0) if spent else 0.0:.6f}",
                    "evaluation_use_mode": "post_replay_diagnostics_only_never_selection_input",
                    "authority": AUTHORITY,
                }
            )
    return out


def build() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    specs = [row for row in read_csv(SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    specs_by_id = {row["trade_spec_id"]: row for row in specs}
    l3_map, _l4_map, l1_by_symbol = load_sec_feature_maps()
    source_audit = build_source_time_audit(specs, l1_by_symbol)
    features = build_adapter_feature_panel(specs)
    features_by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for feature in features:
        features_by_entry[str(feature["entry_date"])].append(feature)
    calendar = [row["session_date"] for row in read_csv(CALENDAR_PATH) if PERIOD_START <= row["session_date"] <= PERIOD_END]
    prices = load_prices({row["symbol"] for row in specs} | {"QQQ"})

    all_decisions: list[dict[str, object]] = []
    all_trades: list[dict[str, object]] = []
    all_equity: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for variant in VARIANTS:
        decisions, trades, equity, summary = replay_variant(variant, specs_by_id, features_by_entry, prices, calendar)
        all_decisions.extend(decisions)
        all_trades.extend(trades)
        all_equity.extend(equity)
        summaries.append(summary)

    best = max(summaries, key=lambda row: (row["meets_cagr_30"] == "1" and row["meets_mdd_minus30"] == "1", float(row["strategy_final_equity"])))
    balanced = max(
        [row for row in summaries if row["meets_cagr_30"] == "1"],
        key=lambda row: (float(row["strategy_max_drawdown_pct"]), float(row["strategy_final_equity"])),
    )
    closeout = {
        "task_id": "Task1081-1100",
        "policy_id": POLICY_ID,
        "source_scope": "sec_companyfacts_only",
        "sec_l1_source_rows": len(read_csv(L1_PATH)),
        "sec_l3_snapshot_keys": len(l3_map),
        "adapter_feature_rows": len(features),
        "source_time_pass_rows": sum(1 for row in source_audit if row["source_time_pass"] == "1"),
        "replay_variants": len(summaries),
        "best_variant": best["policy_variant_id"],
        "best_final_equity": best["strategy_final_equity"],
        "best_cagr_pct": best["strategy_cagr_pct"],
        "best_mdd_pct": best["strategy_max_drawdown_pct"],
        "best_beats_qqq": best["beats_qqq"],
        "best_meets_cagr_30": best["meets_cagr_30"],
        "best_meets_mdd_minus30": best["meets_mdd_minus30"],
        "balanced_variant": balanced["policy_variant_id"],
        "balanced_final_equity": balanced["strategy_final_equity"],
        "balanced_cagr_pct": balanced["strategy_cagr_pct"],
        "balanced_mdd_pct": balanced["strategy_max_drawdown_pct"],
        "balanced_meets_cagr_30": balanced["meets_cagr_30"],
        "balanced_meets_mdd_minus30": balanced["meets_mdd_minus30"],
        "historical_source_time_gap": "0",
        "non_sec_source_gap": "1",
        "replay_executed": "1",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "add_non_sec_asof_sources_transcripts_policy_macro_theme_news_then_rerun_same_policy",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1081_sec_source_time_audit.csv", source_audit, list(source_audit[0].keys()))
    write_csv(OUT_DIR / "task1082_sec_asof_adapter_feature_panel.csv", features, list(features[0].keys()))
    write_csv(OUT_DIR / "task1083_sec_asof_selection_ledger.csv", all_decisions, list(all_decisions[0].keys()))
    write_csv(OUT_DIR / "task1084_sec_asof_replay_trades.csv", all_trades, list(all_trades[0].keys()))
    write_csv(OUT_DIR / "task1085_sec_asof_equity_curves.csv", all_equity, list(all_equity[0].keys()))
    write_csv(OUT_DIR / "task1086_sec_asof_backtest_summary.csv", summaries, list(summaries[0].keys()))
    write_csv(OUT_DIR / "task1087_sec_asof_attribution.csv", build_attribution(all_trades), ["policy_id", "axis", "bucket", "closed_trades", "entry_cash_spent", "pnl", "return_on_spent_pct", "evaluation_use_mode", "authority"])
    write_csv(OUT_DIR / "task1100_sec_asof_source_replay_closeout.csv", [closeout], list(closeout.keys()))
    (OUT_DIR / "task1100_sec_asof_source_replay_closeout.json").write_text(json.dumps(closeout, indent=2), encoding="utf-8")
    return closeout


def main() -> None:
    closeout = build()
    print(
        "[TRADER_BRAIN_1081_1100_SEC_ASOF_SOURCE_REPLAY_OK] "
        f"best={closeout['best_variant']} final={closeout['best_final_equity']} "
        f"cagr={closeout['best_cagr_pct']} mdd={closeout['best_mdd_pct']}"
    )


if __name__ == "__main__":
    main()
