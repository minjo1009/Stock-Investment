from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1228 = ROOT / "data/artifacts/task_1228_1237_volatility_terminal_discriminator"
TASK1238 = ROOT / "data/artifacts/task_1238_1247_raw_text_terminal_evidence"
PRICE_DIR = ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy/daily"
OUT_DIR = ROOT / "data/artifacts/task_1248_1257_raw_text_policy_replay"
REPORT_DIR = ROOT / "docs/reports/task_1248_1257_raw_text_policy_replay"

AUTHORITY = "DIAGNOSTIC_RAW_TEXT_POLICY_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0

POLICIES = {
    "raw_text_strict_exit_slot5_v1": {
        "terminal_distress": 0.0,
        "watch_distress": 0.50,
        "evidence_watch": 0.75,
        "high_vol_upside_raw_not_contradicted": 1.00,
        "ordinary_or_proxy_only": 1.00,
    },
    "raw_text_balanced_risk_slot5_v1": {
        "terminal_distress": 0.25,
        "watch_distress": 0.75,
        "evidence_watch": 1.00,
        "high_vol_upside_raw_not_contradicted": 1.00,
        "ordinary_or_proxy_only": 1.00,
    },
    "raw_text_watch_only_slot5_v1": {
        "terminal_distress": 0.50,
        "watch_distress": 1.00,
        "evidence_watch": 1.00,
        "high_vol_upside_raw_not_contradicted": 1.00,
        "ordinary_or_proxy_only": 1.00,
    },
    "raw_text_shadow_only_slot5_v1": {
        "terminal_distress": 1.00,
        "watch_distress": 1.00,
        "evidence_watch": 1.00,
        "high_vol_upside_raw_not_contradicted": 1.00,
        "ordinary_or_proxy_only": 1.00,
    },
}

SHADOW_ONLY_POLICY = "raw_text_shadow_only_slot5_v1"


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


def load_price(symbol: str) -> pd.DataFrame | None:
    path = PRICE_DIR / symbol / f"{symbol}_daily.csv"
    if not path.exists():
        return None
    frame = pd.read_csv(path)
    if "Date" not in frame.columns or "Close" not in frame.columns:
        return None
    frame["Date"] = pd.to_datetime(frame["Date"]).dt.date
    return frame.sort_values("Date")


def cagr(start_value: float, end_value: float, start: date, end: date) -> float:
    years = (end - start).days / 365.25
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1.0


def max_drawdown(values: list[float]) -> float:
    peak = -float("inf")
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def route_exit(symbol: str, entry_date: str, scheduled_exit_date: str, entry_price: float, route: str) -> tuple[str, float, str]:
    frame = load_price(symbol)
    if frame is None:
        return scheduled_exit_date, entry_price, "missing_price_hold_flat"
    start = datetime.fromisoformat(entry_date).date()
    end = datetime.fromisoformat(scheduled_exit_date).date()
    if route == "terminal_distress":
        end = min(end, start + timedelta(days=21))
    sub = frame[(frame["Date"] >= start) & (frame["Date"] <= end)]
    if sub.empty:
        return scheduled_exit_date, entry_price, "missing_window_hold_flat"
    if route in {"ordinary_or_proxy_only", "high_vol_upside_raw_not_contradicted", "evidence_watch"}:
        last = sub.iloc[-1]
        return last["Date"].isoformat(), float(last["Close"]), "scheduled_raw_evidence_route"
    entry_stop = {
        "watch_distress": 0.75,
        "terminal_distress": 0.88,
    }.get(route, 0.75)
    peak_stop = {
        "watch_distress": 0.65,
        "terminal_distress": 0.80,
    }.get(route, 0.65)
    peak = entry_price
    for price_row in sub.itertuples(index=False):
        close = float(price_row.Close)
        peak = max(peak, close)
        if close <= entry_price * entry_stop:
            return price_row.Date.isoformat(), close, "raw_text_entry_drawdown_stop"
        if close <= peak * peak_stop:
            return price_row.Date.isoformat(), close, "raw_text_peak_drawdown_stop"
    last = sub.iloc[-1]
    return last["Date"].isoformat(), float(last["Close"]), "scheduled_or_terminal_short_horizon"


def policy_catalog() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for policy_id, route_map in POLICIES.items():
        for route, multiplier in route_map.items():
            rows.append(
                {
                    "task_id": "Task1248",
                    "policy_variant_id": policy_id,
                    "terminal_interpretation_route": route,
                    "position_multiplier": multiplier,
                    "rule": "block" if multiplier == 0 else "size_and_route",
                    "selection_promoted": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_specs() -> list[dict[str, object]]:
    base_specs = read_csv(TASK1228 / "task1233_policy_specs.csv")
    l2_by_selection = {row["selection_id"]: row for row in read_csv(TASK1238 / "task1242_l2_survival_primitives.csv")}
    specs: list[dict[str, object]] = []
    for policy_id, route_map in POLICIES.items():
        cooldown_until: dict[str, date] = {}
        for row in sorted(base_specs, key=lambda item: (item["decision_asof_ts"], int(item["candidate_rank"]))):
            l2 = l2_by_selection[row["selection_id"]]
            raw_route = l2["terminal_interpretation_route"]
            symbol = row["symbol"]
            decision_date = datetime.fromisoformat(row["decision_asof_ts"].replace("Z", "+00:00")).date()
            blocked_by_cooldown = symbol in cooldown_until and decision_date < cooldown_until[symbol]
            base_multiplier = to_float(row["position_multiplier"])
            raw_multiplier = route_map.get(raw_route, 1.0)
            entry_price = to_float(row["entry_price"])
            if policy_id == SHADOW_ONLY_POLICY:
                adjusted_exit_date = row["adjusted_exit_date"]
                adjusted_exit_price = to_float(row["adjusted_exit_price"])
                exit_reason = f"raw_text_shadow_only_no_trade_action:{row['exit_reason']}"
            else:
                adjusted_exit_date, adjusted_exit_price, exit_reason = route_exit(
                    symbol,
                    row["entry_date"],
                    row["scheduled_exit_date"],
                    entry_price,
                    raw_route,
                )
            position_multiplier = base_multiplier * raw_multiplier
            if raw_route == "terminal_distress" and raw_multiplier == 0:
                adjusted_exit_date = row["entry_date"]
                adjusted_exit_price = entry_price
                exit_reason = "raw_text_terminal_block"
                position_multiplier = 0.0
            elif blocked_by_cooldown:
                adjusted_exit_date = row["entry_date"]
                adjusted_exit_price = entry_price
                exit_reason = "raw_text_reentry_cooling_block"
                position_multiplier = 0.0
            if exit_reason in {"raw_text_entry_drawdown_stop", "raw_text_peak_drawdown_stop"} and raw_route in {"terminal_distress", "watch_distress"}:
                cooldown_until[symbol] = datetime.fromisoformat(adjusted_exit_date).date() + timedelta(days=62)
            specs.append(
                {
                    "task_id": "Task1249",
                    "policy_spec_id": f"RTPLY1249-{len(specs)+1:07d}",
                    "policy_variant_id": policy_id,
                    "selection_id": row["selection_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "symbol": symbol,
                    "candidate_rank": row["candidate_rank"],
                    "derived_theme": row["derived_theme"],
                    "previous_volatility_route": row["volatility_terminal_route"],
                    "terminal_interpretation_route": raw_route,
                    "survival_state": l2["survival_state"],
                    "evidence_families": l2["evidence_families"],
                    "terminal_evidence_families": l2["terminal_evidence_families"],
                    "independent_source_family_count": l2["independent_source_family_count"],
                    "entry_date": row["entry_date"],
                    "entry_price": entry_price,
                    "scheduled_exit_date": row["scheduled_exit_date"],
                    "scheduled_exit_price": row["scheduled_exit_price"],
                    "adjusted_exit_date": adjusted_exit_date,
                    "adjusted_exit_price": round(adjusted_exit_price, 6),
                    "exit_reason": exit_reason,
                    "base_position_multiplier": base_multiplier,
                    "raw_text_position_multiplier": raw_multiplier,
                    "position_multiplier": round(position_multiplier, 6),
                    "selection_promoted": "0",
                    "assignment_uses_future_outcome": "0",
                    "exit_uses_post_entry_price_path": "1",
                    "authority": AUTHORITY,
                }
            )
    return specs


def run_replay(specs: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    specs_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for spec in specs:
        specs_by_policy[str(spec["policy_variant_id"])].append(spec)
    for policy_id, policy_specs in sorted(specs_by_policy.items()):
        by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
        for spec in policy_specs:
            by_decision[str(spec["decision_asof_ts"])].append(spec)
        capital = INITIAL_CAPITAL
        for decision_ts, items in sorted(by_decision.items()):
            base_slot = capital / 5.0
            invested = 0.0
            period_pnl = 0.0
            new_capital = capital
            for item in sorted(items, key=lambda row: int(str(row["candidate_rank"]))):
                allocation = base_slot * to_float(item["position_multiplier"])
                invested += allocation
                entry = to_float(item["entry_price"])
                exit_ = to_float(item["adjusted_exit_price"])
                net_return = exit_ / entry - 1.0 - ROUND_TRIP_COST_BPS / 10000.0 if allocation > 0 and entry > 0 else 0.0
                pnl = allocation * net_return
                period_pnl += pnl
                new_capital += pnl
                trades.append(
                    {
                        "task_id": "Task1250",
                        "trade_id": f"TRADE1250-{len(trades)+1:07d}",
                        **item,
                        "capital_allocated": round(allocation, 4),
                        "net_return": round(net_return, 8),
                        "pnl": round(pnl, 4),
                        "authority": AUTHORITY,
                    }
                )
            cash_weight = max(0.0, 1.0 - invested / capital) if capital > 0 else 0.0
            period_return = new_capital / capital - 1.0 if capital > 0 else 0.0
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1251",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_return": round(period_return, 8),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "cash_weight_after_routing": round(cash_weight, 6),
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base_metrics = read_csv(TASK1201 / "task1207_replay_metrics.csv")
    base_slot5 = next(row for row in base_metrics if row["policy_variant_id"] == "l0_l3_slot5_v1")
    task1228_metric = read_csv(TASK1228 / "task1234_replay_metrics.csv")[0]
    metrics_rows: list[dict[str, object]] = []
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = datetime.fromisoformat(str(eq_rows[0]["decision_asof_ts"]).replace("Z", "+00:00")).date()
        executed = [row for row in tr_rows if to_float(row["capital_allocated"]) > 0]
        end = max(datetime.fromisoformat(str(row["adjusted_exit_date"])).date() for row in tr_rows)
        wins = sum(1 for row in executed if to_float(row["net_return"]) > 0)
        metrics_rows.append(
            {
                "task_id": "Task1252",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr(INITIAL_CAPITAL, final, start, end), 6),
                "max_drawdown": round(max_drawdown(values), 6),
                "trade_count": len(executed),
                "blocked_or_zero_size_count": len(tr_rows) - len(executed),
                "win_rate": round(wins / len(executed), 6) if executed else 0,
                "base_slot5_final_equity": base_slot5["final_equity"],
                "base_slot5_cagr": base_slot5["cagr"],
                "base_slot5_max_drawdown": base_slot5["max_drawdown"],
                "beats_base_slot5": "1" if final > float(base_slot5["final_equity"]) else "0",
                "task1228_final_equity": task1228_metric["final_equity"],
                "task1228_delta": round(final - float(task1228_metric["final_equity"]), 4),
                "beats_task1228": "1" if final > float(task1228_metric["final_equity"]) else "0",
                "benchmark_symbol": base_slot5["benchmark_symbol"],
                "benchmark_final_equity": base_slot5["benchmark_final_equity"],
                "benchmark_cagr": base_slot5["benchmark_cagr"],
                "beats_benchmark": "1" if final > float(base_slot5["benchmark_final_equity"]) else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return metrics_rows


def route_attribution(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        grouped[(str(row["policy_variant_id"]), str(row["terminal_interpretation_route"]))].append(row)
    rows: list[dict[str, object]] = []
    for (policy_id, route), items in sorted(grouped.items()):
        executed = [row for row in items if to_float(row["capital_allocated"]) > 0]
        rows.append(
            {
                "task_id": "Task1253",
                "policy_variant_id": policy_id,
                "terminal_interpretation_route": route,
                "row_count": len(items),
                "executed_count": len(executed),
                "pnl": round(sum(to_float(row["pnl"]) for row in items), 4),
                "avg_net_return_executed": round(sum(to_float(row["net_return"]) for row in executed) / len(executed), 6) if executed else 0,
                "selection_promoted": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def acceptance_gate(metric_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in metric_rows:
        rows.append(
            {
                "task_id": "Task1254",
                "policy_variant_id": row["policy_variant_id"],
                "final_equity": row["final_equity"],
                "cagr": row["cagr"],
                "max_drawdown": row["max_drawdown"],
                "beats_base_slot5": row["beats_base_slot5"],
                "beats_task1228": row["beats_task1228"],
                "beats_benchmark": row["beats_benchmark"],
                "target_cagr_30pct_pass": "1" if to_float(row["cagr"]) >= 0.30 else "0",
                "target_mdd_minus30pct_pass": "1" if to_float(row["max_drawdown"]) >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def expert_closeout(metric_rows: list[dict[str, object]], attribution_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metric_rows, key=lambda row: to_float(row["final_equity"]))
    return [
        {
            "task_id": "Task1255",
            "expert_role": "distressed_listing_trader",
            "review_verdict": "replay_diagnostic_only",
            "finding": "Raw terminal evidence can reduce exposure but should not become a broad veto without route attribution review.",
            "best_policy": best["policy_variant_id"],
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1255",
            "expert_role": "quant_risk_reviewer",
            "review_verdict": "compare_return_drawdown_before_promotion",
            "finding": "Policy promotion requires beating Task1228 or materially reducing drawdown without losing QQQ/base context.",
            "best_policy": best["policy_variant_id"],
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1255",
            "expert_role": "post_replay_quant_trader_audit",
            "review_verdict": "raw_text_should_be_shadow_or_quality_modifier_first",
            "finding": "Raw text risk evidence degraded L5 replacement policies; evidence_watch and terminal_distress rows were profitable, while watch_distress needs entry hurdles rather than broad exit/size cuts.",
            "best_policy": best["policy_variant_id"],
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1255",
            "expert_role": "backend_source_engineer",
            "review_verdict": "source_lineage_preserved",
            "finding": "Replay specs carry selection id, SEC raw interpretation route, family counts, and no outcome assignment flags.",
            "best_policy": best["policy_variant_id"],
            "authority": AUTHORITY,
        },
    ]


def write_report(closeout: dict[str, object], metric_rows: list[dict[str, object]], attribution_rows: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metric_lines = ["| Policy | Final | CAGR | MDD | Beats QQQ | Beats Task1228 |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in metric_rows:
        metric_lines.append(f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['beats_benchmark']} | {row['beats_task1228']} |")
    report = [
        "# Task1248-1257 Raw Text Policy Replay",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Best policy: `{closeout['best_policy_variant_id']}`.",
        f"- Best final equity: {closeout['best_final_equity']}.",
        f"- Best CAGR: {closeout['best_cagr']}.",
        f"- Best MDD: {closeout['best_max_drawdown']}.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "This task preregistered four raw-text route policies and replayed them over the Task1201 slot5 path.",
        "",
        *metric_lines,
        "",
        "Leakage audit:",
        "",
        "- L1/L2 raw terminal routes came from Task1238-1247 as-of evidence.",
        "- Future return, PnL, and realized outcome columns are not used for assignment.",
        "- Post-entry prices are used only inside L5 exit simulation.",
        "",
        "Remaining blockers:",
        "",
        "- Results are diagnostic only.",
        "- Source extractor is SEC-only and still lacks official exchange deficiency event feeds and non-SEC dynamic sources.",
        "- Policy promotion requires route-level manual review before any broader replay.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We let the brain trade with the new raw filing-text risk layer.",
        "",
        "The result shows whether this evidence helps or hurts compared with the prior volatility-terminal replay.",
        "",
        "This does not make the strategy accepted.",
        "",
        "## Artifact Manifest",
        "",
        "- `task1248_policy_catalog.csv`",
        "- `task1249_policy_specs.csv`",
        "- `task1250_replay_trades.csv`",
        "- `task1251_replay_equity.csv`",
        "- `task1252_replay_metrics.csv`",
        "- `task1253_route_attribution.csv`",
        "- `task1254_acceptance_gate.csv`",
        "- `task1255_expert_closeout.csv`",
        "- `task1257_closeout.csv/json`",
        "",
        "Validation commands:",
        "",
        "- `python scripts/trader_brain_1248_1257_raw_text_policy_replay_validate.py`",
        "- `python -m unittest tests.test_trader_brain_1248_1257_raw_text_policy_replay`",
        "",
        "```text",
        "Test results do not modify strategy acceptance status.",
        "Strategy: NOT_ACCEPTED",
        "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "Real Capital: FORBIDDEN",
        "```",
    ]
    (REPORT_DIR / "task_1248_1257_raw_text_policy_replay.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    policy_rows = policy_catalog()
    specs = build_specs()
    trades, equity = run_replay(specs)
    metric_rows = metrics(trades, equity)
    attribution_rows = route_attribution(trades)
    gate_rows = acceptance_gate(metric_rows)
    expert_rows = expert_closeout(metric_rows, attribution_rows)
    best = max(metric_rows, key=lambda row: to_float(row["final_equity"]))
    closeout = {
        "task_id": "Task1257",
        "verdict": "raw_text_policy_replay_executed_not_accepted",
        "policy_variants": len(POLICIES),
        "policy_spec_rows": len(specs),
        "trade_rows": len(trades),
        "equity_rows": len(equity),
        "best_policy_variant_id": best["policy_variant_id"],
        "best_final_equity": best["final_equity"],
        "best_cagr": best["cagr"],
        "best_max_drawdown": best["max_drawdown"],
        "best_beats_task1228": best["beats_task1228"],
        "best_task1228_delta": best["task1228_delta"],
        "best_beats_benchmark": best["beats_benchmark"],
        "replay_executed": "1",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "Review route attribution and decide whether raw evidence should become a replacement policy or a shadow risk overlay.",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1248_policy_catalog.csv", policy_rows)
    write_csv(OUT_DIR / "task1249_policy_specs.csv", specs)
    write_csv(OUT_DIR / "task1250_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1251_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1252_replay_metrics.csv", metric_rows)
    write_csv(OUT_DIR / "task1253_route_attribution.csv", attribution_rows)
    write_csv(OUT_DIR / "task1254_acceptance_gate.csv", gate_rows)
    write_csv(OUT_DIR / "task1255_expert_closeout.csv", expert_rows)
    write_csv(OUT_DIR / "task1257_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1257_closeout.json", closeout)
    write_csv(REPORT_DIR / "task_1248_1257_decision.csv", [closeout])
    write_report(closeout, metric_rows, attribution_rows)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
