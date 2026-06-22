from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1558_1577_l5_damage_control_engine as damage
import trader_brain_1698_1717_l2_l4_bad_trade_gate as badgate
import trader_brain_2191_2200_api_drawdown_sizing_guard as guard
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2361_2380_full_exit_quality_parity_backtest"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2361_2380_full_exit_quality_parity_backtest.md"
DECISION = REPORT_DIR / "task_2361_2380_decision.csv"

TASK2151 = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
TASK2191 = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"
TASK2321 = ROOT / "data/artifacts/task_2321_2340_plus8000_brain_newdata_backtest"
TASK2341 = ROOT / "data/artifacts/task_2341_2360_plus8000_brain_full_universe_backtest"

AUTHORITY = "DIAGNOSTIC_FULL_EXIT_QUALITY_PARITY_BACKTEST_ONLY"
SOURCE_POLICY = "winner_defense_budget_top5_v1"
QQQ_BENCHMARK_FINAL = 1847.0265
QQQ_BENCHMARK_CAGR = 0.126318
POLICY_MAP = {
    "api_dd_guard_soft_boost_cap_top2_v1": "full_exit_quality_soft_boost_cap_top2_v1",
    "api_dd_guard_stress_neutral_top2_v1": "full_exit_quality_stress_neutral_top2_v1",
    "api_dd_guard_winner_preserve_top2_v1": "full_exit_quality_winner_preserve_top2_v1",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def f(value: object, default: float = 0.0) -> float:
    return guard.to_float(value, default)


def sha256_or_empty(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def price_path(symbol: str) -> Path:
    return replay.PRICE_DIR / symbol / f"{symbol}_daily.csv"


def scope_freeze_rows(l5: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2361",
            "scope_id": "FULLEXIT2361-0001",
            "universe_scope": "full_3100_candidate_pool",
            "candidate_rows": len(l5),
            "l5_source": "data/artifacts/task_2341_2360_plus8000_brain_full_universe_backtest/task2349_full_l5_decisions.csv",
            "selector_brain": "plus8000_brain_structure_preserved_from_task2341",
            "exit_quality_target": "task1704_compatible_price_path_runtime_exit_for_all_candidates",
            "same_selected_trades_only": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def source_family_plan_rows() -> list[dict[str, object]]:
    families = [
        ("market_price_path", "yfinance_cached_daily_ohlcv", "required_for_entry_planned_exit_runtime_exit", "replay_outcome_only"),
        ("trade_spec_schedule", "task1203_l5_trade_specs", "required_for_entry_after_and_exit_on_or_before", "frozen_input"),
        ("l2_l4_risk_quality", "task2343_full_winner_defense_panel", "required_for_task1704_runtime_exit_thresholds", "assignment_input_preexisting"),
        ("api_overlay", "task2350_task2351", "required_for_guard_rank_and_budget", "assignment_input_preexisting"),
    ]
    return [
        {
            "task_id": "Task2362",
            "source_family_plan_id": f"FULLEXITPLAN2362-{idx:04d}",
            "source_family": family,
            "provider_or_artifact": provider,
            "purpose": purpose,
            "admission_class": klass,
            "strict_gate_pass": "0" if klass == "replay_outcome_only" else "1",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (family, provider, purpose, klass) in enumerate(families, start=1)
    ]


def build_exit_quality_packets(l5: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    specs = damage.trade_specs_by_id()
    winner_by_spec = {row["trade_spec_id"]: row for row in read_csv(TASK2341 / "task2343_full_winner_defense_panel.csv")}
    cache = {}
    qqq = replay.load_price("QQQ", cache)
    packets: list[dict[str, object]] = []
    returns: list[dict[str, object]] = []
    ledger: list[dict[str, object]] = []
    gaps: list[dict[str, object]] = []
    seen_symbols: set[str] = set()

    for idx, row in enumerate(l5, start=1):
        symbol = row["symbol"]
        spec_id = row["trade_spec_id"]
        spec = specs.get(spec_id, {})
        win = winner_by_spec.get(spec_id, {})
        raw_path = price_path(symbol)
        if symbol not in seen_symbols:
            seen_symbols.add(symbol)
            ledger.append(
                {
                    "task_id": "Task2363",
                    "call_ledger_id": f"FULLEXITLEDGER2363-{len(ledger)+1:05d}",
                    "provider": "local_yfinance_cache",
                    "endpoint_or_source_family": "daily_ohlcv_csv",
                    "symbol": symbol,
                    "raw_path": str(raw_path.relative_to(ROOT)) if raw_path.exists() else "",
                    "raw_sha256": sha256_or_empty(raw_path),
                    "request_status": "cache_hit" if raw_path.exists() else "cache_missing",
                    "secret_persisted": "0",
                    "authority": AUTHORITY,
                }
            )
        frame = replay.load_price(symbol, cache)
        entry_after = replay.parse_date(spec.get("entry_after_date", "")) or replay.parse_ts(row["decision_asof_ts"]).date()
        scheduled_exit = replay.parse_date(spec.get("exit_on_or_before_date", "")) or entry_after
        entry = replay.price_on_or_after(frame, entry_after)
        planned = replay.close_on_or_before(frame, scheduled_exit)
        qqq_entry = replay.price_on_or_after(qqq, entry_after)
        gap_reason = ""
        if frame is None:
            gap_reason = "missing_symbol_price_history"
        elif not entry:
            gap_reason = "missing_entry_price"
        elif not planned:
            gap_reason = "missing_planned_exit_price"
        if gap_reason:
            gaps.append(
                {
                    "task_id": "Task2364",
                    "source_gap_id": f"FULLEXITGAP2364-{len(gaps)+1:05d}",
                    "trade_spec_id": spec_id,
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": symbol,
                    "decision_asof_ts": row["decision_asof_ts"],
                    "gap_reason": gap_reason,
                    "missing_source_is_negative": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            continue
        entry_date, entry_price = entry
        planned_exit_date, planned_exit_price, _planned_vol = planned
        qqq_entry_price = qqq_entry[1] if qqq_entry else None
        action, reason, action_date, action_price, reduce_fraction = badgate.runtime_exit(
            frame,
            qqq,
            entry_date,
            planned_exit_date,
            entry_price,
            qqq_entry_price,
            str(win.get("collapse_risk_bucket", "")),
            str(win.get("payoff_quality_bucket", "")),
        )
        if action == "exit" and action_date and action_price:
            actual_exit_date = action_date
            actual_exit_price = action_price
            reduced_capital_ratio = 0.0
            reduce_return_component = 0.0
            final_return_component = badgate.net_return(entry_price, action_price)
            net = final_return_component
        elif action == "reduce" and action_date and action_price and reduce_fraction > 0:
            actual_exit_date = planned_exit_date
            actual_exit_price = planned_exit_price
            reduced_capital_ratio = reduce_fraction
            reduce_return_component = reduce_fraction * badgate.net_return(entry_price, action_price)
            final_return_component = (1.0 - reduce_fraction) * badgate.net_return(entry_price, planned_exit_price)
            net = reduce_return_component + final_return_component
        else:
            actual_exit_date = planned_exit_date
            actual_exit_price = planned_exit_price
            reduced_capital_ratio = 0.0
            reduce_return_component = 0.0
            final_return_component = badgate.net_return(entry_price, planned_exit_price)
            net = final_return_component
        source_ts = actual_exit_date.isoformat()
        packet = {
            "task_id": "Task2364",
            "source_packet_id": f"FULLEXITPACKET2364-{idx:07d}",
            "candidate_id": row["candidate_source_id"],
            "candidate_source_id": row["candidate_source_id"],
            "trade_spec_id": spec_id,
            "symbol": symbol,
            "decision_asof_ts": row["decision_asof_ts"],
            "provider": "local_yfinance_cache",
            "endpoint_or_source_family": "daily_ohlcv_price_path_runtime_exit",
            "source_ts": source_ts,
            "available_to_brain_ts": source_ts,
            "source_time_basis": "post_decision_replay_price_path_outcome_only",
            "source_time_certified": "1",
            "raw_path": str(raw_path.relative_to(ROOT)) if raw_path.exists() else "",
            "raw_sha256": sha256_or_empty(raw_path),
            "strict_gate_pass": "0",
            "proxy_feature_allowed": "0",
            "replay_outcome_allowed": "1",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
        packets.append(packet)
        returns.append(
            {
                "task_id": "Task2365",
                "source_trade_id": f"FULLEXITSOURCE2365-{idx:07d}",
                "return_source_policy": "full_exit_quality_task1704_compatible",
                "policy_variant_id": SOURCE_POLICY,
                "trade_spec_id": spec_id,
                "candidate_source_id": row["candidate_source_id"],
                "symbol": symbol,
                "decision_asof_ts": row["decision_asof_ts"],
                "entry_date": entry_date.isoformat(),
                "entry_price": round(entry_price, 6),
                "planned_exit_date": planned_exit_date.isoformat(),
                "actual_exit_date": actual_exit_date.isoformat(),
                "actual_exit_price": round(actual_exit_price, 6),
                "runtime_action": action,
                "runtime_action_reason": reason,
                "reduced_capital_ratio": round(reduced_capital_ratio, 6),
                "reduce_return_component": round(reduce_return_component, 8),
                "final_return_component": round(final_return_component, 8),
                "net_return": round(net, 8),
                "winner_quality_beta": win.get("winner_quality_beta", ""),
                "winner_defense_bucket": win.get("winner_defense_bucket", ""),
                "volatility_cause": win.get("volatility_cause", ""),
                "collapse_risk_bucket": win.get("collapse_risk_bucket", ""),
                "payoff_quality_bucket": win.get("payoff_quality_bucket", ""),
                "source_packet_id": packet["source_packet_id"],
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return packets, returns, ledger, gaps


def replay_with_full_exit_quality(l5: list[dict[str, str]], cards: list[dict[str, str]], decisions: list[dict[str, str]], source_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    inputs = {
        "l5": l5,
        "cards": cards,
        "decisions": decisions,
        "source_trades": [{str(k): str(v) for k, v in row.items()} for row in source_rows],
        "baseline_metrics": read_csv(TASK2151 / "task2175_api_three_loop_replay_metrics.csv"),
    }
    old_auth = guard.AUTHORITY
    try:
        guard.AUTHORITY = AUTHORITY
        guard_rows, trades, equity, metrics = guard.replay_guard(inputs)
    finally:
        guard.AUTHORITY = old_auth
    for rows, task in [(guard_rows, "Task2367"), (trades, "Task2368"), (equity, "Task2369"), (metrics, "Task2370")]:
        for row in rows:
            old_policy = str(row["policy_variant_id"])
            row["task_id"] = task
            row["return_source_policy"] = "full_exit_quality_task1704_compatible"
            row["policy_variant_id"] = POLICY_MAP.get(old_policy, old_policy)
            row["authority"] = AUTHORITY
    return guard_rows, trades, equity, metrics


def coverage_rows(l5: list[dict[str, str]], packets: list[dict[str, object]], returns: list[dict[str, object]], gaps: list[dict[str, object]]) -> list[dict[str, object]]:
    actions = Counter(str(row["runtime_action"]) for row in returns)
    metrics = [
        ("l5_candidate_rows", len(l5), len(l5)),
        ("exit_quality_packet_rows", len(packets), len(l5)),
        ("return_source_rows", len(returns), len(l5)),
        ("price_gap_rows", len(gaps), len(l5)),
    ]
    for action, count in sorted(actions.items()):
        metrics.append((f"runtime_action_{action}", count, len(returns)))
    return [
        {
            "task_id": "Task2366",
            "coverage_id": f"FULLEXITCOVER2366-{idx:04d}",
            "metric": metric,
            "rows": count,
            "total_rows": total,
            "ratio": round(count / total, 6) if total else 0.0,
            "authority": AUTHORITY,
        }
        for idx, (metric, count, total) in enumerate(metrics, start=1)
    ]


def comparison_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "task_id": "Task2371",
            "comparison_id": "FULLEXITCOMP2371-0001",
            "scope": "benchmark",
            "variant": "qqq_buy_hold_benchmark",
            "final_equity": QQQ_BENCHMARK_FINAL,
            "cagr": QQQ_BENCHMARK_CAGR,
            "max_drawdown": "",
            "trade_count": "",
            "authority": AUTHORITY,
        }
    ]
    idx = 2
    refs = [
        (TASK2191 / "task2196_guard_replay_metrics.csv", "original_plus8000_selected_trade"),
        (TASK2321 / "task2328_replay_metrics.csv", "plus8000_brain_existing_universe_newdata"),
        (TASK2341 / "task2357_full_replay_metrics.csv", "prior_full_universe_scheduled_or_partial_actual"),
    ]
    for path, scope in refs:
        for row in read_csv(path):
            rows.append(
                {
                    "task_id": "Task2371",
                    "comparison_id": f"FULLEXITCOMP2371-{idx:04d}",
                    "scope": scope,
                    "variant": row.get("policy_variant_id", ""),
                    "final_equity": row.get("final_equity", ""),
                    "cagr": row.get("cagr", ""),
                    "max_drawdown": row.get("max_drawdown", ""),
                    "trade_count": row.get("trade_count", ""),
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    for row in metrics:
        rows.append(
            {
                "task_id": "Task2371",
                "comparison_id": f"FULLEXITCOMP2371-{idx:04d}",
                "scope": "full_exit_quality_parity_full_universe",
                "variant": row.get("policy_variant_id", ""),
                "final_equity": row.get("final_equity", ""),
                "cagr": row.get("cagr", ""),
                "max_drawdown": row.get("max_drawdown", ""),
                "trade_count": row.get("trade_count", ""),
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def overlap_rows(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    old_rows = [row for row in read_csv(TASK2191 / "task2194_guard_replay_trades.csv") if row["policy_variant_id"] == "api_dd_guard_winner_preserve_top2_v1"]
    new_rows = [row for row in trades if row["policy_variant_id"] == "full_exit_quality_winner_preserve_top2_v1"]
    old_specs = {row["trade_spec_id"] for row in old_rows}
    new_specs = {row["trade_spec_id"] for row in new_rows}
    common = old_specs & new_specs
    added = new_specs - old_specs
    removed = old_specs - new_specs
    return [
        {
            "task_id": "Task2372",
            "overlap_id": "FULLEXITOVERLAP2372-0001",
            "old_policy_variant_id": "api_dd_guard_winner_preserve_top2_v1",
            "new_policy_variant_id": "full_exit_quality_winner_preserve_top2_v1",
            "old_trade_count": len(old_specs),
            "new_trade_count": len(new_specs),
            "common_trade_count": len(common),
            "added_trade_count": len(added),
            "removed_trade_count": len(removed),
            "common_ratio_vs_old": round(len(common) / len(old_specs), 6) if old_specs else 0.0,
            "top_added_symbols": ";".join(f"{s}:{c}" for s, c in Counter(row["symbol"] for row in new_rows if row["trade_spec_id"] in added).most_common(10)),
            "top_removed_symbols": ";".join(f"{s}:{c}" for s, c in Counter(row["symbol"] for row in old_rows if row["trade_spec_id"] in removed).most_common(10)),
            "authority": AUTHORITY,
        }
    ]


def attribution_rows(source_rows: list[dict[str, object]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    source_by_spec = {str(row["trade_spec_id"]): row for row in source_rows}
    selected = [row for row in trades if row["policy_variant_id"] == "full_exit_quality_soft_boost_cap_top2_v1"]
    rows: list[dict[str, object]] = []
    idx = 1

    def add_group(area: str, grouped: dict[str, list[dict[str, object]]]) -> None:
        nonlocal idx
        for reason, items in sorted(grouped.items(), key=lambda item: sum(f(row.get("pnl")) for row in item[1])):
            net_returns = [f(row.get("net_return")) for row in items]
            rows.append(
                {
                    "task_id": "Task2373",
                    "attribution_id": f"FULLEXITATTR2373-{idx:05d}",
                    "failure_area": area,
                    "reason": reason,
                    "row_count": len(items),
                    "pnl_sum": round(sum(f(row.get("pnl")) for row in items), 4),
                    "avg_net_return": round(sum(net_returns) / len(net_returns), 6) if net_returns else 0.0,
                    "min_net_return": round(min(net_returns), 6) if net_returns else 0.0,
                    "max_net_return": round(max(net_returns), 6) if net_returns else 0.0,
                    "authority": AUTHORITY,
                }
            )
            idx += 1

    by_symbol: dict[str, list[dict[str, object]]] = {}
    by_action: dict[str, list[dict[str, object]]] = {}
    by_guard: dict[str, list[dict[str, object]]] = {}
    by_winner: dict[str, list[dict[str, object]]] = {}
    by_source_action: dict[str, list[dict[str, object]]] = {}
    for row in selected:
        spec = str(row["trade_spec_id"])
        source = source_by_spec.get(spec, {})
        by_symbol.setdefault(str(row["symbol"]), []).append(row)
        by_guard.setdefault(str(row.get("guard_action", "")), []).append(row)
        by_winner.setdefault(f"winner_preserve_{row.get('winner_preserve_flag', '0')}", []).append(row)
        by_source_action.setdefault(str(source.get("runtime_action", "")), []).append(row)
        by_action.setdefault(f"{row.get('guard_action','')}|{row.get('api_l2_state','')}|winner={row.get('winner_preserve_flag','0')}", []).append(row)

    add_group("selected_symbol_pnl", by_symbol)
    add_group("guard_action_pnl", by_guard)
    add_group("winner_preserve_pnl", by_winner)
    add_group("exit_runtime_action_pnl", by_source_action)
    add_group("guard_api_winner_pnl", by_action)

    for pnl, row in sorted([(f(row.get("pnl")), row) for row in selected])[:25]:
        source = source_by_spec.get(str(row["trade_spec_id"]), {})
        rows.append(
            {
                "task_id": "Task2373",
                "attribution_id": f"FULLEXITATTR2373-{idx:05d}",
                "failure_area": "worst_selected_trade",
                "reason": str(row["symbol"]),
                "trade_spec_id": row["trade_spec_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "pnl_sum": round(pnl, 4),
                "net_return": row.get("net_return", ""),
                "guard_action": row.get("guard_action", ""),
                "winner_preserve_flag": row.get("winner_preserve_flag", ""),
                "runtime_action": source.get("runtime_action", ""),
                "runtime_action_reason": source.get("runtime_action_reason", ""),
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def closeout_rows(metrics: list[dict[str, object]], coverage: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: (row.get("joint_target_met") == "1", f(row.get("final_equity"))))
    cov = {row["metric"]: row for row in coverage}
    return [
        {
            "task_id": "Task2380",
            "verdict": "full_exit_quality_parity_backtest_complete_diagnostic_only",
            "full_universe_candidate_rows": cov["l5_candidate_rows"]["rows"],
            "exit_quality_rows": cov["return_source_rows"]["rows"],
            "price_gap_rows": cov["price_gap_rows"]["rows"],
            "scheduled_fallback_rows": "0",
            "same_selected_trades_only": "0",
            "selector_brain_preserved": "1",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "joint_target_met": best["joint_target_met"],
            "strict_raw_asof_complete": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], coverage: list[dict[str, object]], comparison: list[dict[str, object]], overlap: list[dict[str, object]], attribution: list[dict[str, object]]) -> None:
    metric_lines = "\n".join(
        f"- `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in metrics
    )
    coverage_lines = "\n".join(f"- `{row['metric']}`: {row['rows']}/{row['total_rows']} ({row['ratio']})." for row in coverage)
    comparison_lines = "\n".join(
        f"- `{row['variant']}` ({row['scope']}): final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in comparison
    )
    overlap_lines = "\n".join(
        f"- `{row['new_policy_variant_id']}`: common {row['common_trade_count']}/{row['old_trade_count']}, added {row['added_trade_count']}, removed {row['removed_trade_count']}."
        for row in overlap
    )
    attribution_lines = "\n".join(
        f"- `{row['failure_area']}` / {row['reason']}: rows {row.get('row_count','')}, pnl {row.get('pnl_sum','')}, avg_return {row.get('avg_net_return', row.get('net_return', ''))}."
        for row in attribution[:40]
    )
    REPORT.write_text(
        f"""# Task2361-2380 Full Exit Quality Parity Backtest

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Full universe candidate rows: {closeout['full_universe_candidate_rows']}.
- Exit quality rows: {closeout['exit_quality_rows']}.
- Price gap rows: {closeout['price_gap_rows']}.
- Scheduled fallback rows: `{closeout['scheduled_fallback_rows']}`.
- Same selected trades only: `{closeout['same_selected_trades_only']}`.
- Selector brain preserved: `{closeout['selector_brain_preserved']}`.
- Best policy: `{closeout['best_policy_variant_id']}`.
- Best final equity: {closeout['best_final_equity']}.
- Best CAGR: {closeout['best_cagr']}.
- Best MDD: {closeout['best_max_drawdown']}.
- Joint target met: `{closeout['joint_target_met']}`.
- Strict raw/as-of complete: `{closeout['strict_raw_asof_complete']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task removes the scheduled-return fallback from Task2341 for the full 3,100-candidate L5 universe. It generates Task1704-compatible entry/planned-exit/runtime-exit/reduce/hold return rows from cached daily price paths for every candidate with price coverage. The return rows are replay outcome only and are not used for assignment or ranking.

Replay results:

{metric_lines}

Coverage:

{coverage_lines}

Comparison:

{comparison_lines}

Selection overlap:

{overlap_lines}

Failure attribution:

{attribution_lines}

## No-Background Decision-Maker Report

Conclusion first: full exit-quality parity is now attached to the 3,100-candidate pool. This removes scheduled fallback rows from the replay source. The result is still diagnostic because the exit path uses post-decision market prices for replay outcome only, not strict live-source readiness.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2361_2380_full_exit_quality_parity_backtest/`.
- Validator: `python scripts/trader_brain_2361_2380_full_exit_quality_parity_backtest_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
""",
        encoding="utf-8",
    )


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    existing = {row["task_id"] for row in rows}
    fieldnames = list(rows[0].keys())
    for task_no in range(2361, 2381):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Full Exit Quality Parity Backtest Step {task_no}",
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "full-exit-quality-replay-outcome-ready-strict-live-source-incomplete",
                "parent_task": f"Task{task_no - 1}" if task_no > 2361 else "Task2360",
                "key_report": "docs/reports/task_2361_2380_full_exit_quality_parity_backtest/task_2361_2380_full_exit_quality_parity_backtest.md",
                "key_decision": "docs/reports/task_2361_2380_full_exit_quality_parity_backtest/task_2361_2380_decision.csv",
                "key_artifacts": "data/artifacts/task_2361_2380_full_exit_quality_parity_backtest",
                "validation_command": "python scripts/trader_brain_2361_2380_full_exit_quality_parity_backtest_validate.py",
                "notes": "Extends Task1704-compatible exit quality return source to full 3100 candidate pool and reruns +8000 brain full-universe replay.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "117. Task2361-Task2380"
    if marker in text:
        return
    line = (
        f"117. Task2361-Task2380 attached Task1704-compatible full exit-quality return sources to the 3,100-candidate pool "
        f"and reran the +8000 brain full-universe replay with scheduled fallback rows 0. Best `{closeout['best_policy_variant_id']}` "
        f"final {closeout['best_final_equity']} CAGR {closeout['best_cagr']} MDD {closeout['best_max_drawdown']}; strict raw/as-of "
        f"complete remains 0. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    l5 = read_csv(TASK2341 / "task2349_full_l5_decisions.csv")
    cards = read_csv(TASK2341 / "task2350_full_api_l4_cards.csv")
    decisions = read_csv(TASK2341 / "task2351_full_api_l5_decisions.csv")
    packets, source_rows, ledger, gaps = build_exit_quality_packets(l5)
    guard_rows, trades, equity, metrics = replay_with_full_exit_quality(l5, cards, decisions, source_rows)
    coverage = coverage_rows(l5, packets, source_rows, gaps)
    comparison = comparison_rows(metrics)
    overlap = overlap_rows(trades)
    attribution = attribution_rows(source_rows, trades)
    closeout = closeout_rows(metrics, coverage)

    write_csv(OUT_DIR / "task2361_scope_freeze.csv", scope_freeze_rows(l5))
    write_csv(OUT_DIR / "task2362_source_family_plan.csv", source_family_plan_rows())
    write_csv(OUT_DIR / "task2363_api_or_raw_call_ledger.csv", ledger)
    write_csv(OUT_DIR / "task2364_normalized_exit_quality_packets.csv", packets)
    write_csv(OUT_DIR / "task2364_source_gap_ledger.csv", gaps)
    write_csv(OUT_DIR / "task2365_full_exit_quality_return_source_rows.csv", source_rows)
    write_csv(OUT_DIR / "task2366_exit_quality_coverage.csv", coverage)
    write_csv(OUT_DIR / "task2367_guard_rows.csv", guard_rows)
    write_csv(OUT_DIR / "task2368_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task2369_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task2370_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task2371_comparison_matrix.csv", comparison)
    write_csv(OUT_DIR / "task2372_selection_overlap_audit.csv", overlap)
    write_csv(OUT_DIR / "task2373_failure_attribution.csv", attribution)
    write_csv(OUT_DIR / "task2380_closeout.csv", closeout)
    write_json(OUT_DIR / "task2380_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], metrics, coverage, comparison, overlap, attribution)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2361_2380_FULL_EXIT_QUALITY_PARITY_BACKTEST_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
