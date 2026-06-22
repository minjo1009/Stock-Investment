from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREV_DIR = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"
SPEC_DIR = ROOT / "data/artifacts/task_921_930_controlled_adapter_gate"
LAYER_DIR = ROOT / "data/artifacts/task_917_920_multifamily_relation_adapter"
MARKET_DIR = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay"
OUT_DIR = ROOT / "data/artifacts/task_961_970_trading_judgment_upgrade"

SPEC_PATH = SPEC_DIR / "task929_controlled_trade_specs.csv"
FEATURE_PATH = PREV_DIR / "task941_selection_feature_panel.csv"
BASELINE_SELECTION_PATH = PREV_DIR / "task942_slot_capped_selection_ledger.csv"
BASELINE_SUMMARY_PATH = PREV_DIR / "task946_slot_capped_summary.csv"
L1_PATH = LAYER_DIR / "task917_multifamily_l1_evidence.csv"
CANDIDATE_PATH = LAYER_DIR / "task919_l4_candidate_bundles_contradiction.csv"
RELATION_PATH = LAYER_DIR / "task919_relation_edges_9primitive.csv"
CALENDAR_PATH = MARKET_DIR / "calendar" / "data_derived_qqq_sessions_v1.csv"
DAILY_DIR = MARKET_DIR / "canonical_daily"

INITIAL_CAPITAL = 1000.0
PERIOD_START = "2021-01-01"
PERIOD_END = "2026-03-31"
SLOT_CAP = 10
ENTRY_SLIPPAGE_BPS = 5.0
EXIT_SLIPPAGE_BPS = 5.0
ROUND_TRIP_COST_BPS = 10.0
ENTRY_FEE_BPS = ROUND_TRIP_COST_BPS / 2.0
EXIT_FEE_BPS = ROUND_TRIP_COST_BPS / 2.0
AUTHORITY = "DIAGNOSTIC_TRADING_JUDGMENT_UPGRADE_ONLY"


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


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def date_part(ts: str) -> str:
    return ts[:10]


def days_between(start_ts: str, end_ts: str) -> int:
    return max((parse_ts(end_ts) - parse_ts(start_ts)).days, 0)


def load_prices(symbols: set[str]) -> dict[str, dict[str, float]]:
    prices: dict[str, dict[str, float]] = {}
    for symbol in sorted(symbols):
        path = DAILY_DIR / f"{symbol}.csv"
        rows = {}
        if path.exists():
            for row in read_csv(path):
                day = row["timestamp"]
                if PERIOD_START <= day <= PERIOD_END:
                    rows[day] = float(row["adj_close"])
        prices[symbol] = rows
    return prices


def max_drawdown(values: list[float]) -> float:
    peak = -math.inf
    dd = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            dd = min(dd, value / peak - 1.0)
    return dd * 100.0


def annualized_return(start_value: float, end_value: float, start_date: str, end_date: str) -> float:
    days = max((datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days, 1)
    years = days / 365.25
    return ((end_value / start_value) ** (1.0 / years) - 1.0) * 100.0


def ids(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def feature_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        -int(row["fresh_conviction_points"]),
        int(row["duplicate_cluster_prior_selected_count"]),
        int(row["stale_flag"]),
        int(row["unresolved_source_gap_count"]),
        -int(row["independent_evidence_family_count"]),
        str(row["theme"]),
        str(row["symbol"]),
        str(row["trade_spec_id"]),
    )


def build_panels() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    features = read_csv(FEATURE_PATH)
    baseline_selections = [
        row for row in read_csv(BASELINE_SELECTION_PATH)
        if row["slot_cap"] == "10" and row["selection_state"] == "selected"
    ]
    selected_ids = {row["trade_spec_id"] for row in baseline_selections}
    candidates = {row["candidate_bundle_id"]: row for row in read_csv(CANDIDATE_PATH)}
    l1 = {row["evidence_id"]: row for row in read_csv(L1_PATH)}
    relations = {row["relation_edge_id"]: row for row in read_csv(RELATION_PATH)}

    weakness_rows = []
    freshness_rows = []
    duplicate_rows = []
    evidence_rows = []
    catalyst_rows = []
    contradiction_rows = []

    cluster_seen: dict[str, int] = defaultdict(int)
    for feature in features:
        candidate = candidates[feature["candidate_bundle_id"]]
        evidence_ids = ids(candidate["supporting_evidence_ids"])
        evidences = [l1[eid] for eid in evidence_ids if eid in l1]
        evidence_families = sorted({row["source_family"] for row in evidences})
        evidence_hashes = sorted({row["raw_source_hash"] for row in evidences})
        evidence_names = sorted({row["source_name"] for row in evidences})
        available_dates = [row["available_to_brain_ts"] for row in evidences]
        newest_available = max(available_dates) if available_dates else ""
        oldest_available = min(available_dates) if available_dates else ""
        newest_age = days_between(newest_available, feature["decision_asof_ts"]) if newest_available else 99999
        oldest_age = days_between(oldest_available, feature["decision_asof_ts"]) if oldest_available else 99999
        leakage_state = "pass" if not newest_available or parse_ts(newest_available) <= parse_ts(feature["decision_asof_ts"]) else "blocked_future_evidence"
        stale_flag = "1" if newest_age > 540 else "0"
        catalyst_like = "1" if any(fam in {"earnings_guidance", "macro_policy_official", "sector_specialist_official_docs"} for fam in evidence_families) else "0"
        catalyst_valid = "1" if catalyst_like == "1" and newest_age <= 270 else "0"
        evergreen_quality = "1" if catalyst_like == "0" and newest_age <= 900 else "0"
        relation_ids = ids(candidate["supporting_relation_ids"]) + ids(candidate["contradicting_relation_ids"]) + ids(candidate["source_gap_relation_ids"])
        relation_primitives = [relations[rid]["relation_primitive"] for rid in relation_ids if rid in relations]
        contradiction_severity = "none"
        if candidate["contradiction_state"] == "contradiction_present":
            contradiction_severity = "medium"
        if candidate["invalidation_relation_ids"]:
            contradiction_severity = "high"
        source_gap_count = len(ids(candidate["source_gap_relation_ids"]))
        thesis_cluster_key = "|".join(
            [
                feature["theme"],
                feature["symbol"],
                candidate["candidate_thesis_type"],
                "+".join(evidence_families),
                "+".join(sorted(set(relation_primitives))),
            ]
        )
        prior_selected_count = cluster_seen[thesis_cluster_key]
        if feature["trade_spec_id"] in selected_ids:
            cluster_seen[thesis_cluster_key] += 1
        independent_family_count = len(evidence_families)
        fresh_conviction_points = int(feature["thesis_priority"]) + int(feature["positive_relation_count"]) + independent_family_count
        if catalyst_valid == "1" or evergreen_quality == "1":
            fresh_conviction_points += 1
        if stale_flag == "1":
            fresh_conviction_points -= 1
        fresh_conviction_points -= max(int(feature["unresolved_source_gap_count"]) - 1, 0)
        if prior_selected_count:
            fresh_conviction_points -= 1

        base = {
            **feature,
            "baseline_slot10_selected": "1" if feature["trade_spec_id"] in selected_ids else "0",
            "supporting_evidence_count": len(evidences),
            "independent_evidence_family_count": independent_family_count,
            "independent_raw_hash_count": len(evidence_hashes),
            "independent_source_name_count": len(evidence_names),
            "newest_available_to_brain_ts": newest_available,
            "oldest_available_to_brain_ts": oldest_available,
            "newest_source_age_days": newest_age,
            "oldest_source_age_days": oldest_age,
            "stale_flag": stale_flag,
            "catalyst_like": catalyst_like,
            "catalyst_valid": catalyst_valid,
            "evergreen_quality": evergreen_quality,
            "leakage_state": leakage_state,
            "thesis_cluster_key": thesis_cluster_key,
            "duplicate_cluster_prior_selected_count": prior_selected_count,
            "contradiction_severity": contradiction_severity,
            "source_gap_relation_count_l4": source_gap_count,
            "fresh_conviction_points": fresh_conviction_points,
            "does_not_use": "future_return realized_return pnl post_entry_price_change outcome_rank",
            "authority": AUTHORITY,
        }
        weakness_rows.append(
            {
                "trade_spec_id": feature["trade_spec_id"],
                "baseline_slot10_selected": base["baseline_slot10_selected"],
                "symbol": feature["symbol"],
                "theme": feature["theme"],
                "candidate_thesis_type": candidate["candidate_thesis_type"],
                "weakness_flags": ";".join(
                    flag
                    for flag, cond in [
                        ("thin_packet", candidate["candidate_thesis_type"] == "thin_or_gap_context_packet"),
                        ("stale_source", stale_flag == "1"),
                        ("duplicate_thesis", prior_selected_count > 0),
                        ("low_independent_evidence", independent_family_count < 2),
                        ("source_gap_heavy", int(feature["unresolved_source_gap_count"]) >= 2),
                    ]
                    if cond
                ),
                "authority": AUTHORITY,
            }
        )
        freshness_rows.append({k: base[k] for k in [
            "trade_spec_id", "candidate_bundle_id", "decision_asof_ts", "symbol", "theme",
            "newest_available_to_brain_ts", "oldest_available_to_brain_ts", "newest_source_age_days",
            "oldest_source_age_days", "stale_flag", "leakage_state", "fresh_conviction_points",
            "does_not_use", "authority"
        ]})
        duplicate_rows.append({k: base[k] for k in [
            "trade_spec_id", "decision_asof_ts", "symbol", "theme", "thesis_cluster_key",
            "duplicate_cluster_prior_selected_count", "baseline_slot10_selected", "authority"
        ]})
        evidence_rows.append({k: base[k] for k in [
            "trade_spec_id", "symbol", "theme", "supporting_evidence_count",
            "independent_evidence_family_count", "independent_raw_hash_count",
            "independent_source_name_count", "authority"
        ]})
        catalyst_rows.append({k: base[k] for k in [
            "trade_spec_id", "symbol", "theme", "catalyst_like", "catalyst_valid",
            "evergreen_quality", "newest_source_age_days", "authority"
        ]})
        contradiction_rows.append({k: base[k] for k in [
            "trade_spec_id", "symbol", "theme", "contradiction_state", "contradiction_severity",
            "source_gap_relation_count_l4", "unresolved_source_gap_count", "authority"
        ]})
        feature.update({k: str(v) for k, v in base.items() if k not in feature})

    return weakness_rows, freshness_rows, duplicate_rows, evidence_rows, catalyst_rows, contradiction_rows


def replay_upgraded(features: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    specs = {row["trade_spec_id"]: row for row in read_csv(SPEC_PATH) if row["trade_spec_state"] == "ready_for_controlled_replay_plan"}
    sessions = [row["session_date"] for row in read_csv(CALENDAR_PATH) if PERIOD_START <= row["session_date"] <= PERIOD_END]
    prices = load_prices({row["symbol"] for row in specs.values()} | {"QQQ"})
    by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in features:
        by_entry[row["entry_date"]].append(row)  # type: ignore[arg-type]

    cash = INITIAL_CAPITAL
    open_positions: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    live_clusters: set[str] = set()

    for day in sessions:
        remaining = []
        exits_closed = 0
        for pos in open_positions:
            if pos["planned_exit_date"] == day:
                px = prices[str(pos["symbol"])].get(day)
                if px is None:
                    remaining.append(pos)
                    continue
                exit_price = px * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0)
                gross = float(pos["shares"]) * exit_price
                fee = gross * (EXIT_FEE_BPS / 10000.0)
                net = gross - fee
                cash += net
                pnl = net - float(pos["entry_cash_spent"])
                trade = dict(pos)
                trade.update(
                    {
                        "exit_date": day,
                        "exit_adj_close": f"{px:.6f}",
                        "exit_price_after_slippage": f"{exit_price:.6f}",
                        "exit_fee": f"{fee:.6f}",
                        "net_exit_value": f"{net:.6f}",
                        "pnl": f"{pnl:.6f}",
                        "return_pct": f"{((net / float(pos['entry_cash_spent'])) - 1.0) * 100.0:.6f}",
                        "fill_state": "closed",
                    }
                )
                trades.append(trade)
                live_clusters.discard(str(pos["thesis_cluster_key"]))
                exits_closed += 1
            else:
                remaining.append(pos)
        open_positions = remaining

        candidates = sorted(by_entry.get(day, []), key=feature_sort_key)
        selected = []
        for row in candidates:
            reasons = []
            if row["leakage_state"] != "pass":
                reasons.append("future_evidence_blocked")
            if int(row["fresh_conviction_points"]) < 1:
                reasons.append("fresh_conviction_below_1")
            if int(row["duplicate_cluster_prior_selected_count"]) > 0:
                reasons.append("historical_duplicate_thesis")
            if str(row["thesis_cluster_key"]) in live_clusters:
                reasons.append("live_duplicate_thesis")
            if row["contradiction_severity"] == "high":
                reasons.append("high_contradiction_severity")
            if row["stale_flag"] == "1" and row["catalyst_valid"] != "1":
                reasons.append("stale_without_valid_catalyst")
            if len(selected) >= max(SLOT_CAP - len(open_positions), 0):
                reasons.append("slot_cap_filled")
            state = "selected" if not reasons else "rejected"
            if state == "selected":
                selected.append(row)
                live_clusters.add(str(row["thesis_cluster_key"]))
            decisions.append(
                {
                    "trade_spec_id": row["trade_spec_id"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "entry_date": day,
                    "symbol": row["symbol"],
                    "theme": row["theme"],
                    "thesis_cluster_key": row["thesis_cluster_key"],
                    "fresh_conviction_points": row["fresh_conviction_points"],
                    "selection_state": state,
                    "blocked_reason": ";".join(reasons),
                    "authority": AUTHORITY,
                }
            )

        valid_orders = []
        for row in selected:
            spec = specs[str(row["trade_spec_id"])]
            entry_px = prices[spec["symbol"]].get(day)
            exit_date = date_part(spec["planned_exit_not_after_ts"])
            exit_px = prices[spec["symbol"]].get(exit_date)
            if entry_px is None or exit_px is None:
                skipped.append({**spec, "skip_date": day, "skip_reason": "missing_exact_entry_or_exit_price", "authority": AUTHORITY})
                continue
            valid_orders.append((row, spec, entry_px, entry_px * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0)))

        per_order_cash = cash / len(valid_orders) if valid_orders else 0.0
        for row, spec, entry_ref, entry_price in valid_orders:
            fee = per_order_cash * (ENTRY_FEE_BPS / 10000.0)
            notional = max(per_order_cash - fee, 0.0)
            spent = notional + fee
            if spent <= 0.000001:
                skipped.append({**spec, "skip_date": day, "skip_reason": "no_available_cash", "authority": AUTHORITY})
                continue
            shares = notional / entry_price
            cash -= spent
            open_positions.append(
                {
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
                    "thesis_cluster_key": row["thesis_cluster_key"],
                    "entry_date": day,
                    "planned_exit_date": date_part(spec["planned_exit_not_after_ts"]),
                    "entry_adj_close": f"{entry_ref:.6f}",
                    "entry_price_after_slippage": f"{entry_price:.6f}",
                    "entry_notional": f"{notional:.6f}",
                    "entry_fee": f"{fee:.6f}",
                    "entry_cash_spent": f"{spent:.6f}",
                    "shares": f"{shares:.10f}",
                    "authority": AUTHORITY,
                }
            )

        mv = 0.0
        for pos in open_positions:
            px = prices[str(pos["symbol"])].get(day)
            if px is not None:
                mv += float(pos["shares"]) * px
        equity_rows.append(
            {
                "date": day,
                "cash": f"{cash:.6f}",
                "open_market_value": f"{mv:.6f}",
                "equity": f"{cash + mv:.6f}",
                "open_positions": len(open_positions),
                "entry_candidates": len(candidates),
                "entries_selected": len(selected),
                "exits_closed": exits_closed,
                "authority": AUTHORITY,
            }
        )

    final_day = sessions[-1]
    for pos in list(open_positions):
        px = prices[str(pos["symbol"])].get(final_day)
        if px is None:
            continue
        exit_price = px * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0)
        gross = float(pos["shares"]) * exit_price
        fee = gross * (EXIT_FEE_BPS / 10000.0)
        net = gross - fee
        cash += net
        pnl = net - float(pos["entry_cash_spent"])
        trade = dict(pos)
        trade.update(
            {
                "exit_date": final_day,
                "exit_adj_close": f"{px:.6f}",
                "exit_price_after_slippage": f"{exit_price:.6f}",
                "exit_fee": f"{fee:.6f}",
                "net_exit_value": f"{net:.6f}",
                "pnl": f"{pnl:.6f}",
                "return_pct": f"{((net / float(pos['entry_cash_spent'])) - 1.0) * 100.0:.6f}",
                "fill_state": "forced_closed_period_end",
            }
        )
        trades.append(trade)
    if open_positions:
        open_positions.clear()
        equity_rows.append(
            {
                "date": final_day,
                "cash": f"{cash:.6f}",
                "open_market_value": "0.000000",
                "equity": f"{cash:.6f}",
                "open_positions": 0,
                "entry_candidates": 0,
                "entries_selected": 0,
                "exits_closed": 0,
                "authority": AUTHORITY,
            }
        )

    equity_values = [float(row["equity"]) for row in equity_rows]
    final_equity = equity_values[-1]
    qqq = prices["QQQ"]
    qqq_start = next(day for day in sessions if day in qqq)
    qqq_end = max(day for day in sessions if day in qqq)
    qqq_final = INITIAL_CAPITAL * qqq[qqq_end] / qqq[qqq_start]
    summary = {
        "policy_id": "fresh_duplicate_suppression_slot10_v1",
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
        "initial_capital": INITIAL_CAPITAL,
        "selected_entries": sum(1 for row in decisions if row["selection_state"] == "selected"),
        "rejected_entries": sum(1 for row in decisions if row["selection_state"] == "rejected"),
        "closed_trades": len(trades),
        "skipped_orders": len(skipped),
        "strategy_final_equity": round(final_equity, 2),
        "strategy_total_return_pct": round(((final_equity / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "strategy_cagr_pct": round(annualized_return(INITIAL_CAPITAL, final_equity, str(equity_rows[0]["date"]), str(equity_rows[-1]["date"])), 6),
        "strategy_max_drawdown_pct": round(max_drawdown(equity_values), 6),
        "qqq_final_equity": round(qqq_final, 2),
        "qqq_total_return_pct": round(((qqq_final / INITIAL_CAPITAL) - 1.0) * 100.0, 6),
        "beats_qqq": "1" if final_equity > qqq_final else "0",
        "meets_cagr_30": "1" if annualized_return(INITIAL_CAPITAL, final_equity, str(equity_rows[0]["date"]), str(equity_rows[-1]["date"])) >= 30 else "0",
        "meets_mdd_minus30": "1" if max_drawdown(equity_values) >= -30 else "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    return decisions, trades, skipped, equity_rows, summary


def build() -> dict[str, object]:
    weakness, freshness, duplicate, evidence_quality, catalyst, contradiction = build_panels()
    features = read_csv(FEATURE_PATH)
    by_id = {row["trade_spec_id"]: row for row in features}
    for panel in [freshness, duplicate, evidence_quality, catalyst, contradiction]:
        for row in panel:
            by_id[row["trade_spec_id"]].update({k: str(v) for k, v in row.items() if k not in {"authority"}})
    decisions, trades, skipped, equity, replay_summary = replay_upgraded(list(by_id.values()))
    baseline = next(row for row in read_csv(BASELINE_SUMMARY_PATH) if row["slot_cap"] == "10")
    closeout = [
        {
            "gate_id": "Task970",
            "baseline_slot10_final_equity": baseline["strategy_final_equity"],
            "baseline_slot10_cagr_pct": baseline["strategy_cagr_pct"],
            "baseline_slot10_mdd_pct": baseline["strategy_max_drawdown_pct"],
            "upgraded_final_equity": replay_summary["strategy_final_equity"],
            "upgraded_cagr_pct": replay_summary["strategy_cagr_pct"],
            "upgraded_mdd_pct": replay_summary["strategy_max_drawdown_pct"],
            "beats_baseline_slot10": "1" if float(replay_summary["strategy_final_equity"]) > float(baseline["strategy_final_equity"]) else "0",
            "beats_qqq": replay_summary["beats_qqq"],
            "meets_cagr_30": replay_summary["meets_cagr_30"],
            "meets_mdd_minus30": replay_summary["meets_mdd_minus30"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_action": "review whether freshness duplicate suppression should be refined or rejected",
            "authority": AUTHORITY,
        }
    ]

    write_csv(OUT_DIR / "task961_baseline_weakness_decomposition.csv", weakness, ["trade_spec_id", "baseline_slot10_selected", "symbol", "theme", "candidate_thesis_type", "weakness_flags", "authority"])
    write_csv(OUT_DIR / "task962_thesis_freshness_panel.csv", freshness, ["trade_spec_id", "candidate_bundle_id", "decision_asof_ts", "symbol", "theme", "newest_available_to_brain_ts", "oldest_available_to_brain_ts", "newest_source_age_days", "oldest_source_age_days", "stale_flag", "leakage_state", "fresh_conviction_points", "does_not_use", "authority"])
    write_csv(OUT_DIR / "task963_duplicate_thesis_clusters.csv", duplicate, ["trade_spec_id", "decision_asof_ts", "symbol", "theme", "thesis_cluster_key", "duplicate_cluster_prior_selected_count", "baseline_slot10_selected", "authority"])
    write_csv(OUT_DIR / "task964_independent_evidence_quality.csv", evidence_quality, ["trade_spec_id", "symbol", "theme", "supporting_evidence_count", "independent_evidence_family_count", "independent_raw_hash_count", "independent_source_name_count", "authority"])
    write_csv(OUT_DIR / "task965_catalyst_validity_expiry.csv", catalyst, ["trade_spec_id", "symbol", "theme", "catalyst_like", "catalyst_valid", "evergreen_quality", "newest_source_age_days", "authority"])
    write_csv(OUT_DIR / "task966_contradiction_severity_panel.csv", contradiction, ["trade_spec_id", "symbol", "theme", "contradiction_state", "contradiction_severity", "source_gap_relation_count_l4", "unresolved_source_gap_count", "authority"])
    exposure = []
    selected_decisions = [row for row in decisions if row["selection_state"] == "selected"]
    for key, group in sorted(defaultdict(list, {k: [r for r in selected_decisions if r["theme"] == k] for k in {r["theme"] for r in selected_decisions}}).items()):
        exposure.append({"exposure_type": "theme", "exposure_key": key, "selected_count": len(group), "authority": AUTHORITY})
    write_csv(OUT_DIR / "task967_thesis_exposure_map.csv", exposure, ["exposure_type", "exposure_key", "selected_count", "authority"])
    stability = []
    by_date: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in decisions:
        by_date[str(row["entry_date"])].append(row)
    for day, group in sorted(by_date.items()):
        selected = [row for row in group if row["selection_state"] == "selected"]
        rejected = [row for row in group if row["selection_state"] == "rejected"]
        stability.append({"entry_date": day, "selected_count": len(selected), "rejected_count": len(rejected), "cohort_stability_state": "review" if rejected else "no_rejection", "authority": AUTHORITY})
    write_csv(OUT_DIR / "task968_entry_cohort_stability_audit.csv", stability, ["entry_date", "selected_count", "rejected_count", "cohort_stability_state", "authority"])
    write_csv(OUT_DIR / "task969_fresh_duplicate_replay_decisions.csv", decisions, ["trade_spec_id", "decision_asof_ts", "entry_date", "symbol", "theme", "thesis_cluster_key", "fresh_conviction_points", "selection_state", "blocked_reason", "authority"])
    trade_fields = ["trade_spec_id", "adapter_input_id", "candidate_bundle_id", "trader_decision_id", "source_graph_id", "decision_asof_ts", "split_id", "theme", "symbol", "side", "thesis_cluster_key", "entry_date", "planned_exit_date", "entry_adj_close", "entry_price_after_slippage", "entry_notional", "entry_fee", "entry_cash_spent", "shares", "exit_date", "exit_adj_close", "exit_price_after_slippage", "exit_fee", "net_exit_value", "pnl", "return_pct", "fill_state", "authority"]
    write_csv(OUT_DIR / "task969_fresh_duplicate_replay_trades.csv", trades, trade_fields)
    write_csv(OUT_DIR / "task969_fresh_duplicate_replay_equity.csv", equity, ["date", "cash", "open_market_value", "equity", "open_positions", "entry_candidates", "entries_selected", "exits_closed", "authority"])
    write_csv(OUT_DIR / "task969_fresh_duplicate_replay_summary.csv", [replay_summary], list(replay_summary.keys()))
    (OUT_DIR / "task969_fresh_duplicate_replay_summary.json").write_text(json.dumps(replay_summary, indent=2), encoding="utf-8")
    source_manifest = [
        {"source_name": "task941_features", "path": str(FEATURE_PATH.as_posix()), "sha256": sha256(FEATURE_PATH), "authority": AUTHORITY},
        {"source_name": "task929_trade_specs", "path": str(SPEC_PATH.as_posix()), "sha256": sha256(SPEC_PATH), "authority": AUTHORITY},
        {"source_name": "task917_l1_evidence", "path": str(L1_PATH.as_posix()), "sha256": sha256(L1_PATH), "authority": AUTHORITY},
        {"source_name": "task919_candidates", "path": str(CANDIDATE_PATH.as_posix()), "sha256": sha256(CANDIDATE_PATH), "authority": AUTHORITY},
    ]
    write_csv(OUT_DIR / "task970_source_manifest.csv", source_manifest, ["source_name", "path", "sha256", "authority"])
    write_csv(OUT_DIR / "task970_governance_closeout.csv", closeout, list(closeout[0].keys()))
    summary = {
        "task_id": "Task961-970",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": AUTHORITY,
        "input_trade_specs": len(features),
        "selected_entries": replay_summary["selected_entries"],
        "baseline_slot10_final_equity": baseline["strategy_final_equity"],
        "upgraded_final_equity": replay_summary["strategy_final_equity"],
        "beats_baseline_slot10": closeout[0]["beats_baseline_slot10"],
        "beats_qqq": replay_summary["beats_qqq"],
        "meets_cagr_30": replay_summary["meets_cagr_30"],
        "meets_mdd_minus30": replay_summary["meets_mdd_minus30"],
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (OUT_DIR / "task961_970_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_csv(OUT_DIR / "task961_970_summary.csv", [summary], list(summary.keys()))
    return summary


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_961_970_TRADING_JUDGMENT_OK] "
        f"selected={summary['selected_entries']} upgraded={summary['upgraded_final_equity']} "
        f"baseline={summary['baseline_slot10_final_equity']} beats_baseline={summary['beats_baseline_slot10']}"
    )


if __name__ == "__main__":
    main()
