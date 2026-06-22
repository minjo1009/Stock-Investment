from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK2151 = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
TASK2121 = ROOT / "data/artifacts/task_2121_2150_free_api_full_capture_proxy_replay"
OUT_DIR = ROOT / "data/artifacts/task_2181_2190_api_overlay_decomposition"
REPORT_DIR = ROOT / "docs/reports/task_2181_2190_api_overlay_decomposition"
REPORT = REPORT_DIR / "task_2181_2190_api_overlay_decomposition.md"
DECISION = REPORT_DIR / "task_2181_2190_decision.csv"

AUTHORITY = "DIAGNOSTIC_API_OVERLAY_DECOMPOSITION_ONLY"
NEW_POLICY = "api_loop3_guarded_risk_cap_top2_v1"
PREV_POLICY = "free_api_proxy_top5_to_top2_convex_v1"
INITIAL_CAPITAL = 1000.0


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


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "None", "nan"}:
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def parse_dt(value: object) -> datetime | None:
    if value in {"", None}:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def filter_policy(rows: list[dict[str, str]], policy_id: str) -> list[dict[str, str]]:
    return [row for row in rows if row["policy_variant_id"] == policy_id]


def equity_map(rows: list[dict[str, str]], policy_id: str) -> dict[str, dict[str, str]]:
    return {row["decision_asof_ts"]: row for row in rows if row["policy_variant_id"] == policy_id}


def find_drawdown_window(equity_rows: list[dict[str, str]]) -> dict[str, object]:
    ordered = sorted(equity_rows, key=lambda row: row["decision_asof_ts"])
    values = [(None, INITIAL_CAPITAL)]
    values.extend((row["decision_asof_ts"], to_float(row["equity"])) for row in ordered)
    peak_value = values[0][1]
    peak_ts = values[0][0]
    worst = 0.0
    worst_peak_ts = peak_ts
    worst_peak_value = peak_value
    trough_ts = peak_ts
    trough_value = peak_value
    for ts, value in values:
        if value > peak_value:
            peak_value = value
            peak_ts = ts
        drawdown = value / peak_value - 1.0 if peak_value else 0.0
        if drawdown < worst:
            worst = drawdown
            worst_peak_ts = peak_ts
            worst_peak_value = peak_value
            trough_ts = ts
            trough_value = value
    return {
        "peak_decision_asof_ts": worst_peak_ts or "",
        "trough_decision_asof_ts": trough_ts or "",
        "peak_equity": round(worst_peak_value, 4),
        "trough_equity": round(trough_value, 4),
        "max_drawdown": round(worst, 6),
    }


def in_window(ts: str, start: str, end: str) -> bool:
    if not start or not end:
        return False
    dt = parse_dt(ts)
    s = parse_dt(start)
    e = parse_dt(end)
    return bool(dt and s and e and s <= dt <= e)


def build_trade_change_ledger(new_trades: list[dict[str, str]], prev_trades: list[dict[str, str]]) -> list[dict[str, object]]:
    new_by_key = {(row["decision_asof_ts"], row["trade_spec_id"]): row for row in new_trades}
    prev_by_key = {(row["decision_asof_ts"], row["trade_spec_id"]): row for row in prev_trades}
    rows: list[dict[str, object]] = []
    for idx, key in enumerate(sorted(set(new_by_key) | set(prev_by_key)), start=1):
        new = new_by_key.get(key)
        prev = prev_by_key.get(key)
        if new and prev:
            status = "same_trade_resized_or_retagged"
            symbol = new["symbol"]
            api_state = new.get("api_l2_state", "")
            api_action = new.get("api_l5_action", "")
            new_pnl = to_float(new["pnl"])
            prev_pnl = to_float(prev["pnl"])
            new_alloc = to_float(new["capital_allocated"])
            prev_alloc = to_float(prev["capital_allocated"])
            new_mult = to_float(new["final_budget_multiplier"])
            prev_mult = to_float(prev["final_budget_multiplier"])
        elif new:
            status = "new_overlay_added_trade"
            symbol = new["symbol"]
            api_state = new.get("api_l2_state", "")
            api_action = new.get("api_l5_action", "")
            new_pnl = to_float(new["pnl"])
            prev_pnl = 0.0
            new_alloc = to_float(new["capital_allocated"])
            prev_alloc = 0.0
            new_mult = to_float(new["final_budget_multiplier"])
            prev_mult = 0.0
        else:
            status = "previous_trade_dropped_by_overlay"
            symbol = prev["symbol"]
            api_state = ""
            api_action = "dropped_by_new_overlay_rank"
            new_pnl = 0.0
            prev_pnl = to_float(prev["pnl"])
            new_alloc = 0.0
            prev_alloc = to_float(prev["capital_allocated"])
            new_mult = 0.0
            prev_mult = to_float(prev["final_budget_multiplier"])
        rows.append(
            {
                "task_id": "Task2181",
                "change_row_id": f"APIOVLCHG-2181-{idx:06d}",
                "decision_asof_ts": key[0],
                "trade_spec_id": key[1],
                "symbol": symbol,
                "change_status": status,
                "new_policy_variant_id": NEW_POLICY,
                "previous_policy_variant_id": PREV_POLICY,
                "api_l2_state": api_state,
                "api_l5_action": api_action,
                "new_capital_allocated": round(new_alloc, 4),
                "previous_capital_allocated": round(prev_alloc, 4),
                "capital_delta": round(new_alloc - prev_alloc, 4),
                "new_final_budget_multiplier": round(new_mult, 6),
                "previous_final_budget_multiplier": round(prev_mult, 6),
                "multiplier_delta": round(new_mult - prev_mult, 6),
                "new_pnl": round(new_pnl, 4),
                "previous_pnl": round(prev_pnl, 4),
                "row_level_pnl_delta": round(new_pnl - prev_pnl, 4),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_monthly_delta(new_equity: dict[str, dict[str, str]], prev_equity: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    prev_cumulative_delta = 0.0
    for idx, decision_ts in enumerate(sorted(set(new_equity) | set(prev_equity)), start=1):
        new = new_equity.get(decision_ts, {})
        old = prev_equity.get(decision_ts, {})
        new_eq = to_float(new.get("equity"))
        old_eq = to_float(old.get("equity"))
        cumulative_delta = new_eq - old_eq
        rows.append(
            {
                "task_id": "Task2182",
                "month_delta_id": f"APIOVLMONTH-2182-{idx:05d}",
                "decision_asof_ts": decision_ts,
                "new_equity": round(new_eq, 4),
                "previous_equity": round(old_eq, 4),
                "equity_delta": round(cumulative_delta, 4),
                "incremental_equity_delta": round(cumulative_delta - prev_cumulative_delta, 4),
                "new_period_pnl": round(to_float(new.get("period_pnl")), 4),
                "previous_period_pnl": round(to_float(old.get("period_pnl")), 4),
                "period_pnl_delta": round(to_float(new.get("period_pnl")) - to_float(old.get("period_pnl")), 4),
                "authority": AUTHORITY,
            }
        )
        prev_cumulative_delta = cumulative_delta
    return rows


def aggregate(rows: list[dict[str, object]], key_field: str, value_field: str) -> list[dict[str, object]]:
    acc: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0.0, "sum": 0.0})
    for row in rows:
        key = str(row.get(key_field, ""))
        acc[key]["count"] += 1
        acc[key]["sum"] += to_float(row.get(value_field))
    out = []
    for idx, (key, value) in enumerate(sorted(acc.items(), key=lambda item: item[1]["sum"], reverse=True), start=1):
        out.append(
            {
                "rank": idx,
                key_field: key,
                "row_count": int(value["count"]),
                value_field + "_sum": round(value["sum"], 4),
                "authority": AUTHORITY,
            }
        )
    return out


def build_drawdown_ledger(
    new_trades: list[dict[str, str]],
    prev_trades: list[dict[str, str]],
    new_equity_rows: list[dict[str, str]],
    prev_equity_rows: list[dict[str, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object], dict[str, object]]:
    new_dd = find_drawdown_window(new_equity_rows)
    prev_dd = find_drawdown_window(prev_equity_rows)
    new_window_trades = [row for row in new_trades if in_window(row["decision_asof_ts"], str(new_dd["peak_decision_asof_ts"]), str(new_dd["trough_decision_asof_ts"]))]
    prev_window_trades = [row for row in prev_trades if in_window(row["decision_asof_ts"], str(prev_dd["peak_decision_asof_ts"]), str(prev_dd["trough_decision_asof_ts"]))]
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(new_window_trades, start=1):
        rows.append(
            {
                "task_id": "Task2183",
                "drawdown_trade_id": f"APIOVLDD-2183-{idx:05d}",
                "policy_variant_id": NEW_POLICY,
                "drawdown_peak_decision_asof_ts": new_dd["peak_decision_asof_ts"],
                "drawdown_trough_decision_asof_ts": new_dd["trough_decision_asof_ts"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "api_l2_state": row.get("api_l2_state", ""),
                "api_l5_action": row.get("api_l5_action", ""),
                "capital_allocated": row["capital_allocated"],
                "pnl": row["pnl"],
                "net_return": row["net_return"],
                "authority": AUTHORITY,
            }
        )
    summary_rows = [
        {
            "task_id": "Task2184",
            "drawdown_summary_id": "APIOVLDD-SUMMARY-NEW",
            "policy_variant_id": NEW_POLICY,
            **new_dd,
            "window_trade_count": len(new_window_trades),
            "window_pnl_sum": round(sum(to_float(row["pnl"]) for row in new_window_trades), 4),
            "worst_symbols": ";".join([symbol for symbol, _ in Counter(row["symbol"] for row in new_window_trades).most_common(8)]),
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2184",
            "drawdown_summary_id": "APIOVLDD-SUMMARY-PREV",
            "policy_variant_id": PREV_POLICY,
            **prev_dd,
            "window_trade_count": len(prev_window_trades),
            "window_pnl_sum": round(sum(to_float(row["pnl"]) for row in prev_window_trades), 4),
            "worst_symbols": ";".join([symbol for symbol, _ in Counter(row["symbol"] for row in prev_window_trades).most_common(8)]),
            "authority": AUTHORITY,
        },
    ]
    return rows, summary_rows, new_dd, prev_dd


def build_closeout(
    changes: list[dict[str, object]],
    monthly: list[dict[str, object]],
    dd_summary: list[dict[str, object]],
) -> list[dict[str, object]]:
    status_count = Counter(row["change_status"] for row in changes)
    added = [row for row in changes if row["change_status"] == "new_overlay_added_trade"]
    dropped = [row for row in changes if row["change_status"] == "previous_trade_dropped_by_overlay"]
    resized = [row for row in changes if row["change_status"] == "same_trade_resized_or_retagged"]
    positive_months = sorted(monthly, key=lambda row: to_float(row["incremental_equity_delta"]), reverse=True)[:5]
    negative_months = sorted(monthly, key=lambda row: to_float(row["incremental_equity_delta"]))[:5]
    new_dd = next(row for row in dd_summary if row["policy_variant_id"] == NEW_POLICY)
    prev_dd = next(row for row in dd_summary if row["policy_variant_id"] == PREV_POLICY)
    final_delta = monthly[-1]["equity_delta"] if monthly else 0.0
    return [
        {
            "task_id": "Task2190",
            "verdict": "api_overlay_decomposition_complete_diagnostic_only",
            "new_policy_variant_id": NEW_POLICY,
            "previous_policy_variant_id": PREV_POLICY,
            "same_trade_count": status_count.get("same_trade_resized_or_retagged", 0),
            "added_trade_count": status_count.get("new_overlay_added_trade", 0),
            "dropped_trade_count": status_count.get("previous_trade_dropped_by_overlay", 0),
            "same_trade_pnl_delta_sum": round(sum(to_float(row["row_level_pnl_delta"]) for row in resized), 4),
            "added_trade_pnl_sum": round(sum(to_float(row["row_level_pnl_delta"]) for row in added), 4),
            "dropped_trade_pnl_saved_or_lost": round(sum(to_float(row["row_level_pnl_delta"]) for row in dropped), 4),
            "final_equity_delta": final_delta,
            "top_positive_delta_months": ";".join(str(row["decision_asof_ts"]) for row in positive_months),
            "top_negative_delta_months": ";".join(str(row["decision_asof_ts"]) for row in negative_months),
            "new_mdd": new_dd["max_drawdown"],
            "previous_mdd": prev_dd["max_drawdown"],
            "mdd_delta": round(to_float(new_dd["max_drawdown"]) - to_float(prev_dd["max_drawdown"]), 6),
            "new_mdd_peak_ts": new_dd["peak_decision_asof_ts"],
            "new_mdd_trough_ts": new_dd["trough_decision_asof_ts"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], state_agg: list[dict[str, object]], symbol_agg: list[dict[str, object]], monthly: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    top_states = "\n".join(f"- {row['api_l2_state']}: {row['row_level_pnl_delta_sum']}" for row in state_agg[:8])
    top_symbols = "\n".join(f"- {row['symbol']}: {row['row_level_pnl_delta_sum']}" for row in symbol_agg[:10])
    neg_months = sorted(monthly, key=lambda row: to_float(row["incremental_equity_delta"]))[:5]
    neg_lines = "\n".join(
        f"- {row['decision_asof_ts']}: incremental delta {row['incremental_equity_delta']}, period pnl delta {row['period_pnl_delta']}"
        for row in neg_months
    )
    text = f"""# Task2181-2190 API Overlay Decomposition

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- New policy: `{closeout['new_policy_variant_id']}`.
- Previous policy: `{closeout['previous_policy_variant_id']}`.
- Final equity delta: {closeout['final_equity_delta']}.
- Same trades: {closeout['same_trade_count']}.
- Added trades: {closeout['added_trade_count']}.
- Dropped trades: {closeout['dropped_trade_count']}.
- New MDD: {closeout['new_mdd']}.
- Previous MDD: {closeout['previous_mdd']}.
- MDD delta: {closeout['mdd_delta']}.
- New MDD window: {closeout['new_mdd_peak_ts']} to {closeout['new_mdd_trough_ts']}.

## Quant Expert Report

API overlay improved final equity by changing both selection and sizing. The key audit result is not just that return improved, but that MDD worsened slightly. Therefore the next rule should not add more generic boost. It should protect the MDD window without deleting the positive overlay months.

PnL delta by API state:

{top_states}

PnL delta by symbol:

{top_symbols}

Worst incremental delta months:

{neg_lines}

## No-Background Decision-Maker Report

Conclusion first: API overlay made money, but it also made the worst drawdown a little worse. The next fix should target the drawdown-window trades, not the whole strategy.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2181_2190_api_overlay_decomposition/`.
- Validator: `python scripts/trader_brain_2181_2190_api_overlay_decomposition_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    existing = {row["task_id"] for row in rows}
    fieldnames = list(rows[0].keys())
    for task_no in range(2181, 2191):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "task_name": f"API Overlay Decomposition Step {task_no}",
                "workstream": "Research Governance / Backtest & Simulation Infra",
                "status": "active",
                "validation_tier": "diagnostic-only",
                "acceptance_state": "NOT_ACCEPTED",
                "current_decision": "api-overlay-decomposed-mdd-bottleneck-identified",
                "upstream_task": f"Task{task_no - 1}" if task_no > 2181 else "Task2180",
                "report_path": "docs/reports/task_2181_2190_api_overlay_decomposition/task_2181_2190_api_overlay_decomposition.md",
                "decision_path": "docs/reports/task_2181_2190_api_overlay_decomposition/task_2181_2190_decision.csv",
                "artifact_path": "data/artifacts/task_2181_2190_api_overlay_decomposition",
                "validation_command": "python scripts/trader_brain_2181_2190_api_overlay_decomposition_validate.py",
                "notes": "Decomposes API overlay trade changes, final equity delta, and MDD window versus Task2121 proxy replay.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "108. Task2181-Task2190"
    if marker in text:
        return
    line = (
        f"108. Task2181-Task2190 decomposed the Task2151 API overlay versus Task2121: "
        f"same trades {closeout['same_trade_count']}, added trades {closeout['added_trade_count']}, "
        f"dropped trades {closeout['dropped_trade_count']}, final equity delta {closeout['final_equity_delta']}, "
        f"new MDD {closeout['new_mdd']} versus previous MDD {closeout['previous_mdd']}; next work should target "
        f"drawdown-window API states rather than add broad overlay boosts, while status remains NOT_ACCEPTED / "
        f"DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert_at = text.find("\n\n\nTask851-859 data certification status:")
    if insert_at == -1:
        text = text.rstrip() + "\n" + line
    else:
        text = text[:insert_at] + "\n" + line + text[insert_at:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    new_trades = filter_policy(read_csv(TASK2151 / "task2173_api_three_loop_replay_trades.csv"), NEW_POLICY)
    prev_trades = filter_policy(read_csv(TASK2121 / "task2128_api_proxy_replay_trades.csv"), PREV_POLICY)
    new_equity_rows = filter_policy(read_csv(TASK2151 / "task2174_api_three_loop_replay_equity.csv"), NEW_POLICY)
    prev_equity_rows = filter_policy(read_csv(TASK2121 / "task2129_api_proxy_replay_equity.csv"), PREV_POLICY)

    changes = build_trade_change_ledger(new_trades, prev_trades)
    monthly = build_monthly_delta(equity_map(new_equity_rows, NEW_POLICY), equity_map(prev_equity_rows, PREV_POLICY))
    dd_trades, dd_summary, _, _ = build_drawdown_ledger(new_trades, prev_trades, new_equity_rows, prev_equity_rows)
    state_agg = aggregate(changes, "api_l2_state", "row_level_pnl_delta")
    symbol_agg = aggregate(changes, "symbol", "row_level_pnl_delta")
    status_agg = aggregate(changes, "change_status", "row_level_pnl_delta")
    closeout = build_closeout(changes, monthly, dd_summary)

    write_csv(OUT_DIR / "task2181_api_overlay_trade_change_ledger.csv", changes)
    write_csv(OUT_DIR / "task2182_monthly_equity_delta.csv", monthly)
    write_csv(OUT_DIR / "task2183_mdd_window_trade_ledger.csv", dd_trades)
    write_csv(OUT_DIR / "task2184_mdd_window_summary.csv", dd_summary)
    write_csv(OUT_DIR / "task2185_pnl_delta_by_api_state.csv", state_agg)
    write_csv(OUT_DIR / "task2186_pnl_delta_by_symbol.csv", symbol_agg)
    write_csv(OUT_DIR / "task2187_pnl_delta_by_change_status.csv", status_agg)
    write_csv(OUT_DIR / "task2190_closeout.csv", closeout)
    write_json(OUT_DIR / "task2190_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], state_agg, symbol_agg, monthly)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2181_2190_API_OVERLAY_DECOMPOSITION_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
