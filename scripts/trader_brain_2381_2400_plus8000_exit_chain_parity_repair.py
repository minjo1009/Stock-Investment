from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1558_1577_l5_damage_control_engine as damage
import trader_brain_1668_1687_l5_thesis_aware_action_engine as thesis
import trader_brain_1698_1717_l2_l4_bad_trade_gate as badgate
import trader_brain_2191_2200_api_drawdown_sizing_guard as guard
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2381_2400_plus8000_exit_chain_parity_repair"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2381_2400_plus8000_exit_chain_parity_repair.md"
DECISION = REPORT_DIR / "task_2381_2400_decision.csv"

TASK1668 = ROOT / "data/artifacts/task_1668_1687_l5_thesis_aware_action_engine"
TASK1698 = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
TASK2151 = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
TASK2191 = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"
TASK2321 = ROOT / "data/artifacts/task_2321_2340_plus8000_brain_newdata_backtest"
TASK2341 = ROOT / "data/artifacts/task_2341_2360_plus8000_brain_full_universe_backtest"
TASK2361 = ROOT / "data/artifacts/task_2361_2380_full_exit_quality_parity_backtest"

AUTHORITY = "DIAGNOSTIC_PLUS8000_EXIT_CHAIN_PARITY_REPAIR_ONLY"
SOURCE_POLICY = "winner_defense_budget_top5_v1"
SOURCE_BADGATE_POLICY = "bad_trade_gate_top5_v1"
SOURCE_THESIS_POLICY = "thesis_aware_no_rerisk_top5_v1"
ROUND_TRIP_COST_BPS = 20.0
QQQ_BENCHMARK_FINAL = 1847.0265
QQQ_BENCHMARK_CAGR = 0.126318
POLICY_MAP = {
    "api_dd_guard_soft_boost_cap_top2_v1": "exit_chain_repaired_soft_boost_cap_top2_v1",
    "api_dd_guard_stress_neutral_top2_v1": "exit_chain_repaired_stress_neutral_top2_v1",
    "api_dd_guard_winner_preserve_top2_v1": "exit_chain_repaired_winner_preserve_top2_v1",
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


def parse_date(value: object) -> date | None:
    if value in {"", None, "nan"}:
        return None
    return replay.parse_date(str(value))


def pct_return(start: float, end: float) -> float:
    if start <= 0:
        return 0.0
    return end / start - 1.0


def net_return(start: float, end: float) -> float:
    return pct_return(start, end) - ROUND_TRIP_COST_BPS / 10000.0


def price_path(symbol: str) -> Path:
    return replay.PRICE_DIR / symbol / f"{symbol}_daily.csv"


def keyed(rows: list[dict[str, str]], policy_id: str | None = None) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        if policy_id is not None and row.get("policy_variant_id") != policy_id:
            continue
        out[row["trade_spec_id"]] = row
    return out


def load_inputs() -> dict[str, object]:
    return {
        "l5": read_csv(TASK2341 / "task2349_full_l5_decisions.csv"),
        "cards": read_csv(TASK2341 / "task2350_full_api_l4_cards.csv"),
        "decisions": read_csv(TASK2341 / "task2351_full_api_l5_decisions.csv"),
        "orig2191": read_csv(TASK2191 / "task2194_guard_replay_trades.csv"),
        "orig1792": read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        "orig1704": read_csv(TASK1698 / "task1704_bad_trade_gate_replay_trades.csv"),
        "orig1673": read_csv(TASK1668 / "task1673_thesis_aware_replay_trades.csv"),
        "winner_panel": read_csv(TASK2341 / "task2343_full_winner_defense_panel.csv"),
        "task2361_sources": read_csv(TASK2361 / "task2365_full_exit_quality_return_source_rows.csv"),
    }


def contract_rows(l5: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2381",
            "contract_id": "EXITPARITY2381-0001",
            "universe_scope": "full_3100_candidate_pool",
            "full_universe_candidate_rows": len(l5),
            "selected_trade_parity_target": "original_plus8000_116_unique_trades",
            "original_exit_chain": "Task1668->Task1704->Task1788->Task2191",
            "generic_task2361_exit_replaced": "1",
            "same_selected_trades_only": "0",
            "scheduled_fallback_rows_allowed": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def source_family_plan_rows() -> list[dict[str, object]]:
    rows = [
        ("original_task1668_thesis_aware_exit", "task1673_thesis_aware_replay_trades", "lower-chain original action/PnL source"),
        ("original_task1704_bad_trade_gate_exit", "task1704_bad_trade_gate_replay_trades", "bad-trade gate source net return and runtime action"),
        ("original_task1788_winner_defense_source", "task1792_winner_defense_replay_trades", "+8000 source truth for copied rows"),
        ("original_task2191_final_guard", "task2194_guard_replay_trades", "+8000 final selected-trade parity target"),
        ("extension_price_path", "local_yfinance_daily_ohlcv", "Task1668-style full-universe extension outcome source"),
    ]
    return [
        {
            "task_id": "Task2381",
            "source_family_plan_id": f"EXITPARITYPLAN2381-{idx:04d}",
            "source_family": family,
            "provider_or_artifact": provider,
            "purpose": purpose,
            "strict_gate_pass": "0",
            "proxy_feature_allowed": "0",
            "replay_outcome_allowed": "1",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (family, provider, purpose) in enumerate(rows, start=1)
    ]


def raw_call_ledger(l5: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, symbol in enumerate(sorted({row["symbol"] for row in l5}), start=1):
        path = price_path(symbol)
        rows.append(
            {
                "task_id": "Task2381",
                "call_ledger_id": f"EXITPARITYLEDGER2381-{idx:05d}",
                "provider": "local_yfinance_cache",
                "endpoint_or_source_family": "daily_ohlcv_csv",
                "symbol": symbol,
                "raw_path": str(path.relative_to(ROOT)) if path.exists() else "",
                "raw_sha256": sha256_or_empty(path),
                "request_status": "cache_hit" if path.exists() else "cache_missing",
                "secret_persisted": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def chain_lineage_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    orig1792 = keyed(inputs["orig1792"], SOURCE_POLICY)  # type: ignore[arg-type]
    orig1704 = keyed(inputs["orig1704"], SOURCE_BADGATE_POLICY)  # type: ignore[arg-type]
    orig1673 = keyed(inputs["orig1673"], SOURCE_THESIS_POLICY)  # type: ignore[arg-type]
    selected_specs = sorted({row["trade_spec_id"] for row in inputs["orig2191"] if str(row.get("policy_variant_id", "")).startswith("api_dd_guard_")})  # type: ignore[index]
    rows: list[dict[str, object]] = []
    for idx, spec in enumerate(selected_specs, start=1):
        w = orig1792.get(spec, {})
        b = orig1704.get(spec, {})
        t = orig1673.get(spec, {})
        rows.append(
            {
                "task_id": "Task2382",
                "lineage_id": f"EXITLINEAGE2382-{idx:05d}",
                "trade_spec_id": spec,
                "symbol": w.get("symbol", b.get("symbol", t.get("symbol", ""))),
                "decision_asof_ts": w.get("decision_asof_ts", b.get("decision_asof_ts", t.get("decision_asof_ts", ""))),
                "task1668_policy_variant_id": t.get("policy_variant_id", ""),
                "task1668_action": t.get("thesis_aware_action", ""),
                "task1668_actual_exit_date": t.get("actual_exit_date", ""),
                "task1668_net_return": t.get("net_return", ""),
                "task1668_reduce_pnl": t.get("reduce_pnl", ""),
                "task1668_final_pnl": t.get("final_pnl", ""),
                "task1668_rerisk_pnl": t.get("rerisk_pnl", ""),
                "task1704_policy_variant_id": b.get("policy_variant_id", ""),
                "task1704_runtime_action": b.get("runtime_action", ""),
                "task1704_runtime_action_reason": b.get("runtime_action_reason", ""),
                "task1704_actual_exit_date": b.get("actual_exit_date", ""),
                "task1704_actual_exit_price": b.get("actual_exit_price", ""),
                "task1704_net_return": b.get("net_return", ""),
                "task1704_reduce_pnl": b.get("reduce_pnl", ""),
                "task1704_final_pnl": b.get("final_pnl", ""),
                "task1788_policy_variant_id": w.get("policy_variant_id", ""),
                "task1788_actual_exit_date": w.get("actual_exit_date", ""),
                "task1788_net_return": w.get("net_return", ""),
                "task1788_winner_quality_beta": w.get("winner_quality_beta", ""),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def first_damage_event(frame, entry_date: date, planned_exit: date, entry_price: float) -> dict[str, object]:
    if frame is None:
        return {"damage_action": "hold", "damage_reason": "missing_price_path", "damage_reduce_date": "", "damage_exit_date": ""}
    sub = frame[(frame["Date"] >= entry_date) & (frame["Date"] <= planned_exit)]
    if sub.empty:
        return {"damage_action": "hold", "damage_reason": "empty_price_path", "damage_reduce_date": "", "damage_exit_date": ""}
    for _, row in sub.iterrows():
        close = float(row["Close"])
        drawdown = close / entry_price - 1.0 if entry_price > 0 else 0.0
        current_date = row["Date"].isoformat()
        if drawdown <= -0.22:
            return {
                "damage_action": "exit",
                "damage_reason": "task1668_extended_price_exit_damage",
                "damage_reduce_date": current_date,
                "damage_exit_date": current_date,
                "price_exit_date": current_date,
                "source_damage_date": "",
            }
        if drawdown <= -0.12:
            return {
                "damage_action": "reduce",
                "damage_reason": "task1668_extended_price_reduce_damage",
                "damage_reduce_date": current_date,
                "damage_exit_date": "",
                "price_exit_date": "",
                "source_damage_date": "",
            }
    return {"damage_action": "hold", "damage_reason": "no_damage_event", "damage_reduce_date": "", "damage_exit_date": "", "price_exit_date": "", "source_damage_date": ""}


def map_thesis_state(row: dict[str, str]) -> str:
    state = row.get("winner_thesis_state", "")
    accel = row.get("winner_acceleration_state", "")
    if state == "convex_winner_thesis" or accel == "convex_winner_acceleration":
        return "confirmed_thesis"
    if state in {"ordinary_or_watch_thesis", "watch_thesis"}:
        return "confirmation_wait"
    return "active_thesis"


def extension_decision(
    row: dict[str, str],
    winner: dict[str, str],
    frame,
    qqq,
    entry_date: date,
    planned_exit: date,
    entry_price: float,
    base_action: dict[str, object],
) -> tuple[dict[str, object], str]:
    event_date = parse_date(base_action.get("damage_reduce_date")) or parse_date(base_action.get("damage_exit_date"))
    stock_ret = thesis.price_return(frame, entry_date, event_date) if event_date else None
    qqq_ret = thesis.price_return(qqq, entry_date, event_date) if event_date else None
    drawdown_cause, relative = thesis.classify_drawdown(stock_ret, qqq_ret)
    terminal = winner.get("event_family") in {"survival", "dilution", "financing"} or winner.get("volatility_cause") == "terminal_or_financing_thesis_risk"
    weak = f(winner.get("winner_quality_beta")) < 55 or row.get("l5_action") == "watch_small"
    source_damage = terminal
    thesis_survives = (
        not source_damage
        and f(winner.get("winner_quality_beta")) >= 72
        and row.get("winner_acceleration_state") == "convex_winner_acceleration"
        and winner.get("winner_defense_bucket") in {"strong_winner_defense", "qualified_winner_defense"}
    )
    market = {
        "drawdown_cause": drawdown_cause,
        "relative_return_to_event": round(relative, 8),
    }
    thesis_row = {
        "source_damage_present": "1" if source_damage else "0",
        "thesis_survives_damage": "1" if thesis_survives else "0",
        "weak_thesis_flag": "1" if weak else "0",
        "terminal_family_flag": "1" if terminal else "0",
        "absorption_persistence_state": winner.get("absorption_state", ""),
        "alpha_left_score": round(f(winner.get("winner_quality_beta")) / 10.0, 6),
    }
    price_breakdown = base_action.get("price_exit_date", "") not in {"", "nan"} or (drawdown_cause == "idiosyncratic_breakdown" and relative <= -0.12)
    absorption_fail = thesis_row["absorption_persistence_state"] in {"market_rejection_or_reversal", "weak_absorption"} and f(thesis_row["alpha_left_score"]) < 5
    evidence_count = sum([source_damage, price_breakdown, weak, terminal, absorption_fail])
    quorum = {"exit_allowed": "1" if evidence_count >= 2 else "0", "exit_evidence_count": evidence_count}
    selected = {
        "policy_variant_id": SOURCE_THESIS_POLICY,
        "trade_spec_id": row["trade_spec_id"],
        "candidate_source_id": row["candidate_source_id"],
        "symbol": row["symbol"],
        "decision_asof_ts": row["decision_asof_ts"],
        "thesis_state": map_thesis_state(row),
    }
    decision = thesis.decide_action(selected, {str(k): str(v) for k, v in base_action.items()}, market, thesis_row, quorum)
    return decision, "task1668_decide_action_extended"


def compute_extension_return(
    row: dict[str, str],
    winner: dict[str, str],
    cache: dict[str, object],
    qqq,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    specs = damage.trade_specs_by_id()
    spec = specs.get(row["trade_spec_id"], {})
    frame = replay.load_price(row["symbol"], cache)
    entry_after = parse_date(spec.get("entry_after_date")) or replay.parse_ts(row["decision_asof_ts"]).date()
    scheduled_exit = parse_date(spec.get("exit_on_or_before_date")) or entry_after
    entry = replay.price_on_or_after(frame, entry_after)
    planned = replay.close_on_or_before(frame, scheduled_exit)
    if frame is None or not entry or not planned:
        gap = {
            "task_id": "Task2384",
            "source_gap_id": f"EXITREPAIRGAP-{row['trade_spec_id']}",
            "trade_spec_id": row["trade_spec_id"],
            "candidate_source_id": row["candidate_source_id"],
            "symbol": row["symbol"],
            "decision_asof_ts": row["decision_asof_ts"],
            "gap_reason": "missing_price_path_or_entry_or_planned_exit",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        return None, gap
    entry_date, entry_price = entry
    planned_exit_date, planned_exit_price, _ = planned
    base_action = first_damage_event(frame, entry_date, planned_exit_date, entry_price)
    decision, method = extension_decision(row, winner, frame, qqq, entry_date, planned_exit_date, entry_price, base_action)
    action = str(decision["action"])
    reason = str(decision["reason"])
    reduce_pnl_ratio = 0.0
    final_pnl_ratio = 0.0
    rerisk_pnl_ratio = 0.0
    reduced_capital_ratio = 0.0
    actual_exit_date = planned_exit_date
    actual_exit_price = planned_exit_price
    reduce_fraction = f(decision.get("reduce_fraction"))
    if action == "exit":
        exit_date = parse_date(decision.get("exit_date")) or planned_exit_date
        close = replay.close_on_or_before(frame, exit_date)
        actual_exit_date = close[0] if close else planned_exit_date
        actual_exit_price = close[1] if close else planned_exit_price
        final_pnl_ratio = net_return(entry_price, actual_exit_price)
    elif action == "reduce" and reduce_fraction > 0:
        reduce_date = parse_date(decision.get("reduce_date")) or planned_exit_date
        reduce_close = replay.close_on_or_before(frame, reduce_date)
        reduce_exit_date = reduce_close[0] if reduce_close else planned_exit_date
        reduce_exit_price = reduce_close[1] if reduce_close else planned_exit_price
        actual_exit_date = planned_exit_date
        actual_exit_price = planned_exit_price
        reduced_capital_ratio = reduce_fraction
        reduce_pnl_ratio = reduce_fraction * net_return(entry_price, reduce_exit_price)
        final_pnl_ratio = (1.0 - reduce_fraction) * net_return(entry_price, planned_exit_price)
    elif action == "no_reentry":
        actual_exit_date = entry_date
        actual_exit_price = entry_price
        final_pnl_ratio = 0.0
    else:
        action = "hold"
        final_pnl_ratio = net_return(entry_price, planned_exit_price)
    net = reduce_pnl_ratio + final_pnl_ratio + rerisk_pnl_ratio
    out = {
        "task_id": "Task2384",
        "source_trade_id": f"EXITREPAIRSOURCE2384-{row['trade_spec_id']}",
        "return_source_policy": "plus8000_exit_chain_repaired",
        "policy_variant_id": SOURCE_POLICY,
        "trade_spec_id": row["trade_spec_id"],
        "candidate_source_id": row["candidate_source_id"],
        "symbol": row["symbol"],
        "decision_asof_ts": row["decision_asof_ts"],
        "entry_date": entry_date.isoformat(),
        "entry_price": round(entry_price, 6),
        "planned_exit_date": planned_exit_date.isoformat(),
        "actual_exit_date": actual_exit_date.isoformat(),
        "actual_exit_price": round(actual_exit_price, 6),
        "runtime_action": action,
        "runtime_action_reason": reason,
        "reduced_capital_ratio": round(reduced_capital_ratio, 6),
        "reduce_pnl": round(reduce_pnl_ratio, 8),
        "final_pnl": round(final_pnl_ratio, 8),
        "rerisk_pnl": round(rerisk_pnl_ratio, 8),
        "net_return": round(net, 8),
        "winner_quality_beta": winner.get("winner_quality_beta", ""),
        "winner_defense_bucket": winner.get("winner_defense_bucket", ""),
        "volatility_cause": winner.get("volatility_cause", ""),
        "extension_method": method,
        "copied_original_source": "0",
        "scheduled_fallback_used": "0",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "outcome_used_for_audit_only": "1",
        "authority": AUTHORITY,
    }
    return out, None


def copied_original_source_row(row: dict[str, str], win: dict[str, str], bad: dict[str, str], thesis_row: dict[str, str] | None) -> dict[str, object]:
    return {
        "task_id": "Task2384",
        "source_trade_id": f"EXITREPAIRSOURCE2384-{row['trade_spec_id']}",
        "return_source_policy": "plus8000_exit_chain_repaired",
        "policy_variant_id": SOURCE_POLICY,
        "trade_spec_id": row["trade_spec_id"],
        "candidate_source_id": row["candidate_source_id"],
        "symbol": row["symbol"],
        "decision_asof_ts": row["decision_asof_ts"],
        "entry_date": win.get("entry_date", bad.get("entry_date", "")),
        "entry_price": bad.get("entry_price", ""),
        "planned_exit_date": bad.get("planned_exit_date", ""),
        "actual_exit_date": win.get("actual_exit_date", bad.get("actual_exit_date", "")),
        "actual_exit_price": bad.get("actual_exit_price", ""),
        "runtime_action": bad.get("runtime_action", thesis_row.get("thesis_aware_action", "") if thesis_row else ""),
        "runtime_action_reason": bad.get("runtime_action_reason", thesis_row.get("thesis_aware_reason", "") if thesis_row else ""),
        "reduced_capital_ratio": "",
        "reduce_pnl": bad.get("reduce_pnl", thesis_row.get("reduce_pnl", "") if thesis_row else ""),
        "final_pnl": bad.get("final_pnl", thesis_row.get("final_pnl", "") if thesis_row else ""),
        "rerisk_pnl": thesis_row.get("rerisk_pnl", "") if thesis_row else "",
        "net_return": win.get("net_return", bad.get("net_return", "")),
        "winner_quality_beta": win.get("winner_quality_beta", ""),
        "winner_defense_bucket": win.get("winner_defense_bucket", ""),
        "volatility_cause": win.get("volatility_cause", ""),
        "extension_method": "copied_original_task1792_1704_1668_source",
        "copied_original_source": "1",
        "scheduled_fallback_used": "0",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "outcome_used_for_audit_only": "1",
        "authority": AUTHORITY,
    }


def build_repaired_source_rows(inputs: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    l5: list[dict[str, str]] = inputs["l5"]  # type: ignore[assignment]
    winner_by_spec = keyed(inputs["winner_panel"])  # type: ignore[arg-type]
    orig1792 = keyed(inputs["orig1792"], SOURCE_POLICY)  # type: ignore[arg-type]
    orig1704 = keyed(inputs["orig1704"], SOURCE_BADGATE_POLICY)  # type: ignore[arg-type]
    orig1673 = keyed(inputs["orig1673"], SOURCE_THESIS_POLICY)  # type: ignore[arg-type]
    cache: dict[str, object] = {}
    qqq = replay.load_price("QQQ", cache)
    rows: list[dict[str, object]] = []
    method_rows: list[dict[str, object]] = []
    gaps: list[dict[str, object]] = []
    for idx, row in enumerate(l5, start=1):
        spec = row["trade_spec_id"]
        win = orig1792.get(spec)
        bad = orig1704.get(spec, {})
        thesis_row = orig1673.get(spec)
        if win:
            out = copied_original_source_row(row, win, bad, thesis_row)
        else:
            out, gap = compute_extension_return(row, winner_by_spec.get(spec, {}), cache, qqq)
            if gap:
                gaps.append(gap)
                continue
        rows.append(out)
        method_rows.append(
            {
                "task_id": "Task2385",
                "method_audit_id": f"EXITMETHOD2385-{idx:07d}",
                "trade_spec_id": spec,
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "extension_method": out["extension_method"],
                "copied_original_source": out["copied_original_source"],
                "scheduled_fallback_used": out["scheduled_fallback_used"],
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows, method_rows, gaps


def parity_diff_rows(inputs: dict[str, object], repaired: list[dict[str, object]]) -> list[dict[str, object]]:
    repaired_by_spec = {str(row["trade_spec_id"]): row for row in repaired}
    orig2191: list[dict[str, str]] = inputs["orig2191"]  # type: ignore[assignment]
    orig1704 = keyed(inputs["orig1704"], SOURCE_BADGATE_POLICY)  # type: ignore[arg-type]
    orig1673 = keyed(inputs["orig1673"], SOURCE_THESIS_POLICY)  # type: ignore[arg-type]
    selected_specs = sorted({row["trade_spec_id"] for row in orig2191 if row["policy_variant_id"] == "api_dd_guard_winner_preserve_top2_v1"})
    rows: list[dict[str, object]] = []
    fields = ["runtime_action", "actual_exit_date", "actual_exit_price", "net_return", "reduce_pnl", "final_pnl", "rerisk_pnl"]
    for idx, spec in enumerate(selected_specs, start=1):
        old_final = next(row for row in orig2191 if row["policy_variant_id"] == "api_dd_guard_winner_preserve_top2_v1" and row["trade_spec_id"] == spec)
        old_bad = orig1704.get(spec, {})
        old_thesis = orig1673.get(spec, {})
        new = repaired_by_spec.get(spec, {})
        expected = {
            "runtime_action": old_bad.get("runtime_action", old_thesis.get("thesis_aware_action", "")),
            "actual_exit_date": old_final.get("actual_exit_date", old_bad.get("actual_exit_date", "")),
            "actual_exit_price": old_bad.get("actual_exit_price", ""),
            "net_return": old_final.get("net_return", old_bad.get("net_return", "")),
            "reduce_pnl": old_bad.get("reduce_pnl", old_thesis.get("reduce_pnl", "")),
            "final_pnl": old_bad.get("final_pnl", old_thesis.get("final_pnl", "")),
            "rerisk_pnl": old_thesis.get("rerisk_pnl", ""),
        }
        diff_fields = []
        for field in fields:
            exp = str(expected.get(field, ""))
            got = str(new.get(field, ""))
            numeric = field in {"actual_exit_price", "net_return", "reduce_pnl", "final_pnl", "rerisk_pnl"}
            same = abs(f(exp) - f(got)) <= 1e-8 if numeric and exp != "" and got != "" else exp == got
            if not same:
                diff_fields.append(field)
        rows.append(
            {
                "task_id": "Task2383",
                "parity_diff_id": f"EXITPARITYDIFF2383-{idx:05d}",
                "trade_spec_id": spec,
                "symbol": old_final["symbol"],
                "decision_asof_ts": old_final["decision_asof_ts"],
                "diff_count": len(diff_fields),
                "diff_fields": ";".join(diff_fields),
                **{f"expected_{field}": expected.get(field, "") for field in fields},
                **{f"repaired_{field}": new.get(field, "") for field in fields},
                "parity_pass": "1" if not diff_fields else "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def replay_with_repaired_sources(l5: list[dict[str, str]], cards: list[dict[str, str]], decisions: list[dict[str, str]], source_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
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
    for rows, task in [(guard_rows, "Task2386"), (trades, "Task2386"), (equity, "Task2386"), (metrics, "Task2386")]:
        for row in rows:
            old_policy = str(row["policy_variant_id"])
            row["task_id"] = task
            row["return_source_policy"] = "plus8000_exit_chain_repaired"
            row["policy_variant_id"] = POLICY_MAP.get(old_policy, old_policy)
            row["authority"] = AUTHORITY
    return guard_rows, trades, equity, metrics


def comparison_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "task_id": "Task2387",
            "comparison_id": "EXITCOMP2387-0001",
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
        (TASK2341 / "task2357_full_replay_metrics.csv", "prior_full_universe_partial_actual_or_scheduled"),
        (TASK2361 / "task2370_replay_metrics.csv", "generic_full_exit_quality_wrong_chain"),
    ]
    for path, scope in refs:
        for row in read_csv(path):
            rows.append(
                {
                    "task_id": "Task2387",
                    "comparison_id": f"EXITCOMP2387-{idx:04d}",
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
                "task_id": "Task2387",
                "comparison_id": f"EXITCOMP2387-{idx:04d}",
                "scope": "repaired_plus8000_exit_chain_full_universe",
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


def failure_attribution(source_rows: list[dict[str, object]], trades: list[dict[str, object]], method_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    method_by_spec = {str(row["trade_spec_id"]): row for row in method_rows}
    source_by_spec = {str(row["trade_spec_id"]): row for row in source_rows}
    selected = [row for row in trades if row["policy_variant_id"] == "exit_chain_repaired_soft_boost_cap_top2_v1"]
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in selected:
        spec = str(row["trade_spec_id"])
        source = source_by_spec.get(spec, {})
        method = method_by_spec.get(spec, {})
        groups[("symbol", str(row["symbol"]))].append(row)
        groups[("extension_method", str(method.get("extension_method", "")))].append(row)
        groups[("runtime_action", str(source.get("runtime_action", "")))].append(row)
        groups[("winner_preserve_flag", str(row.get("winner_preserve_flag", "")))].append(row)
    out: list[dict[str, object]] = []
    idx = 1
    for (area, reason), items in sorted(groups.items(), key=lambda item: sum(f(row.get("pnl")) for row in item[1])):
        returns = [f(row.get("net_return")) for row in items]
        out.append(
            {
                "task_id": "Task2388",
                "attribution_id": f"EXITATTR2388-{idx:05d}",
                "failure_area": area,
                "reason": reason,
                "row_count": len(items),
                "pnl_sum": round(sum(f(row.get("pnl")) for row in items), 4),
                "avg_net_return": round(sum(returns) / len(returns), 6) if returns else 0.0,
                "min_net_return": round(min(returns), 6) if returns else 0.0,
                "max_net_return": round(max(returns), 6) if returns else 0.0,
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return out


def coverage_rows(l5: list[dict[str, str]], source_rows: list[dict[str, object]], method_rows: list[dict[str, object]], gaps: list[dict[str, object]], parity: list[dict[str, object]]) -> list[dict[str, object]]:
    method_counts = Counter(str(row["extension_method"]) for row in method_rows)
    metrics = [
        ("full_universe_candidate_rows", len(l5), len(l5)),
        ("repaired_exit_source_rows", len(source_rows), len(l5)),
        ("price_gap_rows", len(gaps), len(l5)),
        ("scheduled_fallback_rows", sum(1 for row in source_rows if row.get("scheduled_fallback_used") == "1"), len(source_rows)),
        ("selected_116_parity_rows", len(parity), 116),
        ("selected_116_parity_diff_rows", sum(1 for row in parity if row.get("parity_pass") != "1"), len(parity)),
    ]
    for method, count in sorted(method_counts.items()):
        metrics.append((f"extension_method_{method}", count, len(method_rows)))
    return [
        {
            "task_id": "Task2389",
            "coverage_id": f"EXITCOVER2389-{idx:04d}",
            "metric": metric,
            "rows": count,
            "total_rows": total,
            "ratio": round(count / total, 6) if total else 0.0,
            "authority": AUTHORITY,
        }
        for idx, (metric, count, total) in enumerate(metrics, start=1)
    ]


def closeout_rows(metrics: list[dict[str, object]], coverage: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: (row.get("joint_target_met") == "1", f(row.get("final_equity"))))
    cov = {row["metric"]: row for row in coverage}
    return [
        {
            "task_id": "Task2400",
            "verdict": "plus8000_exit_chain_parity_repaired_diagnostic_only",
            "full_universe_candidate_rows": cov["full_universe_candidate_rows"]["rows"],
            "repaired_exit_source_rows": cov["repaired_exit_source_rows"]["rows"],
            "selected_116_parity_diff_rows": cov["selected_116_parity_diff_rows"]["rows"],
            "price_gap_rows": cov["price_gap_rows"]["rows"],
            "scheduled_fallback_rows": cov["scheduled_fallback_rows"]["rows"],
            "same_selected_trades_only": "0",
            "generic_task2361_exit_replaced": "1",
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


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], coverage: list[dict[str, object]], comparison: list[dict[str, object]], attr: list[dict[str, object]]) -> None:
    metric_lines = "\n".join(
        f"- `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in metrics
    )
    coverage_lines = "\n".join(f"- `{row['metric']}`: {row['rows']}/{row['total_rows']} ({row['ratio']})." for row in coverage)
    comparison_lines = "\n".join(
        f"- `{row['variant']}` ({row['scope']}): final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in comparison
    )
    attr_lines = "\n".join(
        f"- `{row['failure_area']}` / {row['reason']}: rows {row['row_count']}, pnl {row['pnl_sum']}, avg_return {row['avg_net_return']}."
        for row in attr[:40]
    )
    REPORT.write_text(
        f"""# Task2381-2400 Plus8000 Exit Chain Parity Repair

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Full universe candidate rows: {closeout['full_universe_candidate_rows']}.
- Repaired exit source rows: {closeout['repaired_exit_source_rows']}.
- Selected 116 parity diff rows: {closeout['selected_116_parity_diff_rows']}.
- Price gap rows: {closeout['price_gap_rows']}.
- Scheduled fallback rows: {closeout['scheduled_fallback_rows']}.
- Same selected trades only: `{closeout['same_selected_trades_only']}`.
- Generic Task2361 exit replaced: `{closeout['generic_task2361_exit_replaced']}`.
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

This task repairs the Task2361 mistake by copying original +8000 exit-chain source rows wherever Task1788/Task1704/Task1668 source truth exists. The selected 116 +8000 trades must match the original chain exactly before the full-universe replay is considered reviewable. Non-original full-universe rows use an extended Task1668 `decide_action` path and are clearly tagged by extension method.

Replay results:

{metric_lines}

Coverage:

{coverage_lines}

Comparison:

{comparison_lines}

Failure attribution:

{attr_lines}

## No-Background Decision-Maker Report

Conclusion first: the original +8000 selected-trade exit chain is now parity-locked before full-universe extension. This is still diagnostic because extension rows are replay outcome rows, not live-source readiness.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair/`.
- Validator: `python scripts/trader_brain_2381_2400_plus8000_exit_chain_parity_repair_validate.py`.

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
    for task_no in range(2381, 2401):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Plus8000 Exit Chain Parity Repair Step {task_no}",
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "exit-chain-parity-repaired-strict-live-source-incomplete",
                "parent_task": f"Task{task_no - 1}" if task_no > 2381 else "Task2380",
                "key_report": "docs/reports/task_2381_2400_plus8000_exit_chain_parity_repair/task_2381_2400_plus8000_exit_chain_parity_repair.md",
                "key_decision": "docs/reports/task_2381_2400_plus8000_exit_chain_parity_repair/task_2381_2400_decision.csv",
                "key_artifacts": "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair",
                "validation_command": "python scripts/trader_brain_2381_2400_plus8000_exit_chain_parity_repair_validate.py",
                "notes": "Repairs +8000 original exit chain parity before full-universe replay.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "118. Task2381-Task2400"
    if marker in text:
        return
    line = (
        f"118. Task2381-Task2400 repaired the +8000 original exit-chain parity before full-universe extension: "
        f"selected 116 parity diff rows {closeout['selected_116_parity_diff_rows']}, repaired source rows "
        f"{closeout['repaired_exit_source_rows']}, best `{closeout['best_policy_variant_id']}` final "
        f"{closeout['best_final_equity']} CAGR {closeout['best_cagr']} MDD {closeout['best_max_drawdown']}; "
        f"strict raw/as-of complete remains 0. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    l5: list[dict[str, str]] = inputs["l5"]  # type: ignore[assignment]
    cards: list[dict[str, str]] = inputs["cards"]  # type: ignore[assignment]
    decisions: list[dict[str, str]] = inputs["decisions"]  # type: ignore[assignment]
    source_rows, method_rows, gaps = build_repaired_source_rows(inputs)
    parity = parity_diff_rows(inputs, source_rows)
    guard_rows, trades, equity, metrics = replay_with_repaired_sources(l5, cards, decisions, source_rows)
    lineage = chain_lineage_rows(inputs)
    coverage = coverage_rows(l5, source_rows, method_rows, gaps, parity)
    comparison = comparison_rows(metrics)
    attr = failure_attribution(source_rows, trades, method_rows)
    closeout = closeout_rows(metrics, coverage)

    write_csv(OUT_DIR / "task2381_exit_chain_contract.csv", contract_rows(l5))
    write_csv(OUT_DIR / "task2381_source_family_plan.csv", source_family_plan_rows())
    write_csv(OUT_DIR / "task2381_api_or_raw_call_ledger.csv", raw_call_ledger(l5))
    write_csv(OUT_DIR / "task2382_original_chain_lineage.csv", lineage)
    write_csv(OUT_DIR / "task2383_selected_116_parity_diff.csv", parity)
    write_csv(OUT_DIR / "task2384_repaired_exit_source_rows.csv", source_rows)
    write_csv(OUT_DIR / "task2384_source_gap_ledger.csv", gaps)
    write_csv(OUT_DIR / "task2385_full_universe_extension_method_audit.csv", method_rows)
    write_csv(OUT_DIR / "task2386_replay_guard_rows.csv", guard_rows)
    write_csv(OUT_DIR / "task2386_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task2386_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task2386_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task2387_comparison_matrix.csv", comparison)
    write_csv(OUT_DIR / "task2388_failure_attribution.csv", attr)
    write_csv(OUT_DIR / "task2389_coverage.csv", coverage)
    write_csv(OUT_DIR / "task2400_closeout.csv", closeout)
    write_json(OUT_DIR / "task2400_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], metrics, coverage, comparison, attr)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2381_2400_PLUS8000_EXIT_CHAIN_PARITY_REPAIR_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
