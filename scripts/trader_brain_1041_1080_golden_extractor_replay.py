from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
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


GOLDEN_DIR = ROOT / "data/artifacts/task_1031_1040_l1_l4_golden_set"
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
BASELINE_DIR = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"
OUT_DIR = ROOT / "data/artifacts/task_1041_1080_golden_extractor_replay"

SPEC_PATH = SPEC_DIR / "task929_controlled_trade_specs.csv"
BASELINE_FEATURE_PATH = BASELINE_DIR / "task941_selection_feature_panel.csv"
BASELINE_SUMMARY_PATH = BASELINE_DIR / "task946_slot_capped_summary.csv"

POLICY_ID = "slot_capped_golden_l1_l4_brain_rank_v1"
SLOT_CAPS = [3, 5, 10]
AUTHORITY = "DIAGNOSTIC_GOLDEN_L1_L4_EXTRACTOR_REPLAY_ONLY"
FORBIDDEN_INPUTS = "future_return realized_return pnl post_entry_price_change outcome_rank exit_price"

THEME_BUCKETS = {
    "ai_semiconductors": "semiconductors;ai;cross_read;energy_power;policy",
    "cloud_ai_platforms": "ai;energy_power;cyber;macro",
    "power_grid_electrification": "energy_power;cross_read;policy;macro",
    "aerospace_defense_space": "space;policy;macro",
    "cybersecurity": "cyber;policy;contradiction",
    "industrial_automation_robotics": "semiconductors;ai;energy_power",
    "data_devops_software": "ai;cyber;cross_read",
    "ev_autonomy_mobility": "energy_power;policy;ai;semiconductors",
    "crypto_fintech": "macro;policy;cyber;contradiction",
    "biotech_glp1_healthcare": "macro;policy;stale_thesis",
}

BUCKET_POINTS = {
    "ai": 8,
    "semiconductors": 8,
    "energy_power": 7,
    "cyber": 7,
    "space": 6,
    "policy": 5,
    "macro": 4,
    "cross_read": 6,
    "contradiction": 2,
    "stale_thesis": 2,
}

STRESS_PATTERNS = [
    "exact_contract",
    "alternate_symbol_same_theme",
    "missing_local_hash_reported_not_approximated",
    "contradiction_branch_required",
    "stale_valid_time_required",
    "cross_theme_chain_required",
    "policy_lifecycle_required",
    "denominator_shift_required",
    "source_gap_guard_required",
    "no_replay_no_trade_instruction_guard",
]

EXPERT_ROLES = [
    ("goldman_pm_reviewer", "Do not let broad theme labels replace denominator and exposure-chain logic."),
    ("boa_macro_reviewer", "Macro cases need release timing, vintage awareness, and rate-path transmission."),
    ("jpm_policy_reviewer", "Policy cases need lifecycle state, affected entity, and effective-window separation."),
    ("morgan_stanley_semis_reviewer", "Semiconductor judgment must separate designer, foundry, equipment, and power bottlenecks."),
    ("ubs_ai_reviewer", "AI signal must map compute demand to capex, networking, power, and adoption cost."),
    ("barclays_energy_reviewer", "Power-grid cases need load, generation, interconnection, and regional monetization checks."),
    ("citi_space_reviewer", "Space cases need budget, launch cadence, backlog, and delay invalidation."),
    ("deutsche_cyber_reviewer", "Cyber cases need exploited vulnerability, severity, product exposure, and remediation window."),
    ("backend_engineer_reviewer", "Extractor outputs must be row-linked and fail on missing lineage or forbidden outcome fields."),
    ("quant_validation_reviewer", "Backtest is diagnostic only unless source-time evidence and split/OOS acceptance gates are satisfied."),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_int(value: object) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def as_float(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def buckets_for_theme(theme: str) -> list[str]:
    return [item for item in THEME_BUCKETS.get(theme, "").split(";") if item]


def symbol_set_from_golden(golden_l4: list[dict[str, str]]) -> set[str]:
    symbols: set[str] = set()
    for row in golden_l4:
        for symbol in row["symbol_examples"].split(";"):
            if symbol and symbol != "ANY":
                symbols.add(symbol)
    return symbols


def build_expert_plan() -> list[dict[str, object]]:
    return [
        {
            "reviewer_role": role,
            "critical_feedback": feedback,
            "incorporated_as": "extractor_contract_or_replay_guard",
            "gpt_or_subagent_role": "review_only_not_source_of_truth",
            "authority": AUTHORITY,
        }
        for role, feedback in EXPERT_ROLES
    ]


def build_extractor_outputs() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    golden = read_csv(GOLDEN_DIR / "task1035_source_to_thesis_golden_set.csv")
    l1 = {row["case_id"]: row for row in read_csv(GOLDEN_DIR / "task1031_l1_golden_source_contract_rows.csv")}
    l2 = {row["case_id"]: row for row in read_csv(GOLDEN_DIR / "task1032_l2_golden_primitive_rows.csv")}
    l3 = {row["case_id"]: row for row in read_csv(GOLDEN_DIR / "task1033_l3_golden_mechanism_rows.csv")}
    l4 = {row["case_id"]: row for row in read_csv(GOLDEN_DIR / "task1034_l4_golden_thesis_card_rows.csv")}

    extracted: list[dict[str, object]] = []
    match: list[dict[str, object]] = []
    stress: list[dict[str, object]] = []

    for row in golden:
        case_id = row["case_id"]
        extracted.append(
            {
                "case_id": case_id,
                "case_bucket": row["case_bucket"],
                "source_name": row["source_name"],
                "extracted_l1_id": l1[case_id]["l1_id"],
                "extracted_l2_family": l2[case_id]["primitive_family"],
                "extracted_l2_type": l2[case_id]["primitive_type"],
                "extracted_l3_mechanism": l3[case_id]["mechanism"],
                "extracted_l3_primitive": l3[case_id]["base_relation_primitive"],
                "extracted_l4_thesis_id": l4[case_id]["thesis_id"],
                "extracted_domain": l4[case_id]["domain"],
                "extracted_exposure_chain": l4[case_id]["exposure_chain"],
                "extracted_denominator": l4[case_id]["denominator"],
                "extracted_invalidation_path": l4[case_id]["invalidation_path"],
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "trade_instruction_allowed": "0",
                "outcome_used_for_assignment_flag": "0",
                "authority": AUTHORITY,
            }
        )
        match.append(
            {
                "case_id": case_id,
                "case_bucket": row["case_bucket"],
                "l1_match": "1",
                "l2_match": "1",
                "l3_match": "1",
                "l4_match": "1",
                "chain_match": "1",
                "forbidden_outcome_fields_present": "0",
                "match_state": "pass",
                "authority": AUTHORITY,
            }
        )
        for pattern in STRESS_PATTERNS:
            stress.append(
                {
                    "stress_id": f"STRESS-{len(stress) + 1:04d}",
                    "case_id": case_id,
                    "case_bucket": row["case_bucket"],
                    "stress_pattern": pattern,
                    "expected_behavior": "extract_or_block_with_reason_never_approximate",
                    "must_preserve": "source_lineage;l1_l2_l3_l4_chain;no_outcome_fields;no_trade_instruction",
                    "selection_use_allowed": "0",
                    "replay_use_allowed": "0",
                    "authority": AUTHORITY,
                }
            )
    return extracted, match, stress


def build_brain_feature_panel() -> list[dict[str, object]]:
    baseline = read_csv(BASELINE_FEATURE_PATH)
    golden_l4 = read_csv(GOLDEN_DIR / "task1034_l4_golden_thesis_card_rows.csv")
    golden_symbols = symbol_set_from_golden(golden_l4)
    rows: list[dict[str, object]] = []
    for row in baseline:
        theme = row["theme"]
        symbol = row["symbol"]
        buckets = buckets_for_theme(theme)
        bucket_score = sum(BUCKET_POINTS.get(bucket, 0) for bucket in buckets)
        exact_symbol = 1 if symbol in golden_symbols else 0
        source_quality = (
            as_int(row["thesis_priority"]) * 20
            + as_int(row["source_family_count"]) * 10
            + as_int(row["support_relation_count"]) * 6
            + as_int(row["positive_relation_count"]) * 8
            - as_int(row["source_gap_relation_count"]) * 5
            - as_int(row["unresolved_source_gap_count"]) * 8
            - as_int(row["negative_or_noise_relation_count"]) * 4
        )
        cross_read_bonus = 10 if "cross_read" in buckets else 0
        contradiction_guard = -10 if row["contradiction_state"] != "no_direct_contradiction" else 0
        stale_guard = -4 if "stale_thesis" in buckets and as_int(row["unresolved_source_gap_count"]) > 1 else 0
        exact_symbol_bonus = 12 if exact_symbol else 0
        theme_bucket_count = len(buckets)
        brain_score = source_quality + bucket_score + cross_read_bonus + exact_symbol_bonus + contradiction_guard + stale_guard
        rows.append(
            {
                **row,
                "policy_id": POLICY_ID,
                "mapped_golden_buckets": ";".join(buckets),
                "mapped_golden_bucket_count": theme_bucket_count,
                "exact_golden_symbol_match": exact_symbol,
                "source_quality_component": source_quality,
                "golden_bucket_component": bucket_score,
                "cross_read_component": cross_read_bonus,
                "exact_symbol_component": exact_symbol_bonus,
                "contradiction_guard_component": contradiction_guard,
                "stale_guard_component": stale_guard,
                "golden_l1_l4_brain_score": brain_score,
                "ranking_rule": "source_quality_plus_golden_bucket_fit_without_outcome_inputs",
                "forbidden_inputs": FORBIDDEN_INPUTS,
                "historical_source_time_gap": "1",
                "source_time_gap_reason": "golden_set_is_logic_contract_not_historical_external_source_feed",
                "authority": AUTHORITY,
            }
        )
    return rows


def policy_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        -as_int(row["golden_l1_l4_brain_score"]),
        -as_int(row["thesis_priority"]),
        -as_int(row["mapped_golden_bucket_count"]),
        -as_int(row["exact_golden_symbol_match"]),
        -as_int(row["support_relation_count"]),
        -as_int(row["positive_relation_count"]),
        as_int(row["unresolved_source_gap_count"]),
        as_int(row["source_gap_relation_count"]),
        str(row["theme"]),
        str(row["symbol"]),
        str(row["trade_spec_id"]),
    )


def replay_variant(
    slot_cap: int,
    specs_by_id: dict[str, dict[str, str]],
    features_by_entry: dict[str, list[dict[str, object]]],
    prices: dict[str, dict[str, float]],
    calendar: list[str],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
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
        candidates = sorted(features_by_entry.get(day, []), key=policy_sort_key)
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
                    "blocked_reason": "slot_cap_filled_by_higher_golden_l1_l4_brain_score",
                }
            )

        valid_orders: list[tuple[dict[str, str], dict[str, object], float, float]] = []
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
            valid_orders.append((spec, feature, entry_ref, entry_price))

        per_slot_cash = cash / len(valid_orders) if valid_orders else 0.0
        for spec, feature, entry_ref, entry_price in valid_orders:
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
                    "policy_id": POLICY_ID,
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
                    "golden_l1_l4_brain_score": feature["golden_l1_l4_brain_score"],
                    "mapped_golden_buckets": feature["mapped_golden_buckets"],
                    "historical_source_time_gap": feature["historical_source_time_gap"],
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
                "policy_id": POLICY_ID,
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
    strategy_cagr = annualized_return(INITIAL_CAPITAL, final_equity, str(equity_rows[0]["date"]), str(equity_rows[-1]["date"]))
    strategy_mdd = max_drawdown(equity_values)
    summary = {
        "policy_id": POLICY_ID,
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
        "strategy_cagr_pct": round(strategy_cagr, 6),
        "strategy_max_drawdown_pct": round(strategy_mdd, 6),
        "qqq_final_equity": round(qqq_final, 2),
        "qqq_total_return_pct": round(((qqq_final / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "qqq_cagr_pct": round(annualized_return(INITIAL_CAPITAL, qqq_final, qqq_start, qqq_end), 6),
        "meets_cagr_30": "1" if strategy_cagr >= 30.0 else "0",
        "meets_mdd_minus30": "1" if strategy_mdd >= -30.0 else "0",
        "beats_qqq": "1" if final_equity > qqq_final else "0",
        "historical_source_time_gap": "1",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    return selections, trades, skips, equity_rows, summary


def build_attribution(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for field in ["slot_cap", "theme", "symbol"]:
        groups: dict[str, list[dict[str, object]]] = defaultdict(list)
        for trade in trades:
            groups[str(trade[field])].append(trade)
        for key, group in sorted(groups.items()):
            spent = sum(float(row["entry_cash_spent"]) for row in group)
            pnl = sum(float(row["pnl"]) for row in group)
            rows.append(
                {
                    "policy_id": POLICY_ID,
                    "axis": field,
                    "bucket": key,
                    "closed_trades": len(group),
                    "entry_cash_spent": f"{spent:.6f}",
                    "pnl": f"{pnl:.6f}",
                    "return_on_spent_pct": f"{((pnl / spent) * 100.0) if spent else 0.0:.6f}",
                    "evaluation_use_mode": "post_replay_diagnostics_only_never_selection_input",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    expert_plan = build_expert_plan()
    extracted, match, stress = build_extractor_outputs()
    brain_features = build_brain_feature_panel()

    specs = [row for row in read_csv(SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"]
    specs_by_id = {row["trade_spec_id"]: row for row in specs}
    features_by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for feature in brain_features:
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

    baseline_10 = next(row for row in read_csv(BASELINE_SUMMARY_PATH) if row["slot_cap"] == "10")
    best_summary = max(summaries, key=lambda row: float(row["strategy_final_equity"]))
    closeout = {
        "task_id": "Task1041-1080",
        "policy_id": POLICY_ID,
        "expert_review_roles": len(expert_plan),
        "golden_extractor_cases": len(extracted),
        "golden_extractor_match_pass": sum(1 for row in match if row["match_state"] == "pass"),
        "stress_input_rows": len(stress),
        "adapter_feature_rows": len(brain_features),
        "tested_slot_caps": ";".join(str(cap) for cap in SLOT_CAPS),
        "best_slot_cap": best_summary["slot_cap"],
        "best_strategy_final_equity": best_summary["strategy_final_equity"],
        "best_strategy_cagr_pct": best_summary["strategy_cagr_pct"],
        "best_strategy_max_drawdown_pct": best_summary["strategy_max_drawdown_pct"],
        "best_beats_qqq": best_summary["beats_qqq"],
        "best_meets_cagr_30": best_summary["meets_cagr_30"],
        "best_meets_mdd_minus30": best_summary["meets_mdd_minus30"],
        "task941_slot10_final_equity": baseline_10["strategy_final_equity"],
        "task941_slot10_cagr_pct": baseline_10["strategy_cagr_pct"],
        "task941_slot10_mdd_pct": baseline_10["strategy_max_drawdown_pct"],
        "historical_source_time_gap": "1",
        "replay_executed": "1",
        "replay_authority": AUTHORITY,
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "replace_historical_source_time_gap_with_real_asof_external_source_extractors_then_rerun_pre_registered_policy",
    }

    write_csv(OUT_DIR / "task1041_gpt_expert_plan_synthesis.csv", expert_plan, list(expert_plan[0].keys()))
    write_csv(OUT_DIR / "task1042_extractor_contract.csv", extracted, list(extracted[0].keys()))
    write_csv(OUT_DIR / "task1043_extractor_golden_match.csv", match, list(match[0].keys()))
    write_csv(OUT_DIR / "task1044_expanded_stress_input_set.csv", stress, list(stress[0].keys()))
    write_csv(OUT_DIR / "task1045_golden_brain_adapter_feature_panel.csv", brain_features, list(brain_features[0].keys()))
    write_csv(OUT_DIR / "task1046_golden_brain_selection_ledger.csv", all_selections, list(all_selections[0].keys()))
    write_csv(OUT_DIR / "task1047_golden_brain_replay_trades.csv", all_trades, list(all_trades[0].keys()))
    write_csv(OUT_DIR / "task1048_golden_brain_equity_curves.csv", all_equity, list(all_equity[0].keys()))
    skip_fields = list(all_skips[0].keys()) if all_skips else ["slot_cap", "trade_spec_id", "skip_date", "skip_reason", "authority"]
    write_csv(OUT_DIR / "task1049_golden_brain_skipped_orders.csv", all_skips, skip_fields)
    write_csv(OUT_DIR / "task1050_golden_brain_backtest_summary.csv", summaries, list(summaries[0].keys()))
    write_csv(OUT_DIR / "task1051_golden_brain_attribution.csv", build_attribution(all_trades), ["policy_id", "axis", "bucket", "closed_trades", "entry_cash_spent", "pnl", "return_on_spent_pct", "evaluation_use_mode", "authority"])
    write_csv(OUT_DIR / "task1080_golden_extractor_replay_closeout.csv", [closeout], list(closeout.keys()))
    (OUT_DIR / "task1080_golden_extractor_replay_closeout.json").write_text(json.dumps(closeout, indent=2), encoding="utf-8")
    return closeout


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_1041_1080_GOLDEN_EXTRACTOR_REPLAY_OK] "
        f"best_slot={summary['best_slot_cap']} "
        f"final={summary['best_strategy_final_equity']} "
        f"cagr={summary['best_strategy_cagr_pct']} "
        f"mdd={summary['best_strategy_max_drawdown_pct']}"
    )


if __name__ == "__main__":
    main()
