from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK2151 = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
TASK1991 = ROOT / "data/artifacts/task_1991_2000_winner_acceleration_surgery"
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
OUT_DIR = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"
REPORT_DIR = ROOT / "docs/reports/task_2191_2200_api_drawdown_sizing_guard"
REPORT = REPORT_DIR / "task_2191_2200_api_drawdown_sizing_guard.md"
DECISION = REPORT_DIR / "task_2191_2200_decision.csv"

AUTHORITY = "DIAGNOSTIC_API_DRAWDOWN_SIZING_GUARD_ONLY"
SOURCE_POLICY = "winner_defense_budget_top5_v1"
BASELINE_POLICY = "api_loop3_guarded_risk_cap_top2_v1"
PREVIOUS_POLICY = "free_api_proxy_top5_to_top2_convex_v1"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265
POLICIES = [
    "api_dd_guard_soft_boost_cap_top2_v1",
    "api_dd_guard_stress_neutral_top2_v1",
    "api_dd_guard_winner_preserve_top2_v1",
]


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


def parse_date(value: object) -> date | None:
    dt = parse_dt(value)
    return dt.date() if dt else None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "l5": read_csv(TASK1991 / "task1996_l5_winner_acceleration_decisions.csv"),
        "cards": read_csv(TASK2151 / "task2171_l4_api_score_cards_hardened.csv"),
        "decisions": read_csv(TASK2151 / "task2172_l5_api_decisions_hardened.csv"),
        "source_trades": read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        "baseline_metrics": read_csv(TASK2151 / "task2175_api_three_loop_replay_metrics.csv"),
    }


def is_winner_preserve(source_trade: dict[str, str], l5: dict[str, str]) -> bool:
    quality = to_float(source_trade.get("winner_quality_beta"))
    bucket = source_trade.get("winner_defense_bucket", "")
    state = l5.get("winner_acceleration_state", "")
    sleeve = l5.get("strategy_sleeve", "")
    return (
        quality >= 88.0
        or (bucket == "strong_winner_defense" and quality >= 86.0)
        or (sleeve == "winner_compounder" and state == "convex_winner_acceleration" and quality >= 84.0)
    )


def stress_state(current_drawdown: float, previous_period_pnl: float) -> str:
    if current_drawdown <= -0.18:
        return "portfolio_hard_drawdown"
    if current_drawdown <= -0.10:
        return "portfolio_soft_drawdown"
    if previous_period_pnl < 0 and current_drawdown <= -0.005:
        return "early_stress_after_loss"
    return "normal"


def guard_multiplier(policy_id: str, base_api_mult: float, state: str, api_l2_state: str, winner_preserve: bool) -> tuple[float, str]:
    if state == "normal":
        return base_api_mult, "no_guard_normal_state"
    if winner_preserve and api_l2_state in {"api_event_context_supportive", "api_two_family_expectation_support"}:
        if policy_id == "api_dd_guard_winner_preserve_top2_v1":
            return base_api_mult, "winner_preserved_full_boost"
        return max(1.0, 1.0 + (base_api_mult - 1.0) * 0.65), "winner_preserved_partial_boost"
    if api_l2_state in {"api_financing_or_dilution_risk", "api_expectation_weakening_risk", "api_risk_context_cap_required"}:
        return min(base_api_mult, 0.68 if state == "portfolio_hard_drawdown" else 0.78), "risk_state_tighter_cap"
    if policy_id == "api_dd_guard_soft_boost_cap_top2_v1":
        return min(base_api_mult, 1.0 + max(base_api_mult - 1.0, 0.0) * 0.35), "soft_boost_cap"
    if policy_id == "api_dd_guard_stress_neutral_top2_v1":
        return min(base_api_mult, 1.0), "stress_neutralizes_api_boost"
    if policy_id == "api_dd_guard_winner_preserve_top2_v1":
        return min(base_api_mult, 0.78 if state == "portfolio_hard_drawdown" else 0.9), "nonwinner_stress_cap"
    return base_api_mult, "no_guard_fallback"


def final_budget_cap(policy_id: str, final_mult: float, state: str, winner_preserve: bool) -> tuple[float, str]:
    if state == "normal":
        return final_mult, "no_final_budget_cap"
    if winner_preserve:
        if state == "portfolio_hard_drawdown":
            return min(final_mult, 1.2), "winner_hard_drawdown_final_cap"
        return min(final_mult, 1.28), "winner_soft_drawdown_final_cap"
    if policy_id == "api_dd_guard_soft_boost_cap_top2_v1":
        cap = 0.95 if state != "portfolio_hard_drawdown" else 0.82
    elif policy_id == "api_dd_guard_stress_neutral_top2_v1":
        cap = 0.86 if state != "portfolio_hard_drawdown" else 0.68
    else:
        cap = 0.78 if state != "portfolio_hard_drawdown" else 0.55
    return min(final_mult, cap), "nonwinner_stress_final_budget_cap"


def metrics_for(policy_id: str, trades: list[dict[str, object]], equity: list[dict[str, object]], baseline_metrics: list[dict[str, str]]) -> dict[str, object]:
    values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in equity]
    final = values[-1] if values else INITIAL_CAPITAL
    start = replay.parse_ts(str(equity[0]["decision_asof_ts"])).date() if equity else date(2021, 1, 1)
    end_dates = [parse_date(row.get("actual_exit_date")) for row in trades]
    end = max([d for d in end_dates if d] or [start])
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = (final / INITIAL_CAPITAL) ** (1 / years) - 1.0
    mdd = replay.max_drawdown(values)
    baseline = next(row for row in baseline_metrics if row["policy_variant_id"] == BASELINE_POLICY)
    return {
        "task_id": "Task2196",
        "policy_variant_id": policy_id,
        "baseline_policy_variant_id": BASELINE_POLICY,
        "previous_policy_variant_id": PREVIOUS_POLICY,
        "initial_capital": INITIAL_CAPITAL,
        "final_equity": round(final, 4),
        "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
        "cagr": round(cagr, 6),
        "max_drawdown": round(mdd, 6),
        "trade_count": len(trades),
        "qqq_benchmark_final": QQQ_BENCHMARK_FINAL,
        "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
        "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
        "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
        "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 and final > QQQ_BENCHMARK_FINAL else "0",
        "baseline_final_equity": baseline["final_equity"],
        "baseline_cagr": baseline["cagr"],
        "baseline_max_drawdown": baseline["max_drawdown"],
        "delta_vs_baseline_final_equity": round(final - to_float(baseline["final_equity"]), 4),
        "delta_vs_baseline_cagr": round(cagr - to_float(baseline["cagr"]), 6),
        "delta_vs_baseline_mdd": round(mdd - to_float(baseline["max_drawdown"]), 6),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "outcome_used_for_audit_only": "1",
        "authority": AUTHORITY,
    }


def replay_guard(inputs: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    cards_by_spec = {row["trade_spec_id"]: row for row in inputs["cards"]}
    decisions_by_spec = {row["trade_spec_id"]: row for row in inputs["decisions"]}
    l5_by_spec = {row["trade_spec_id"]: row for row in inputs["l5"]}
    source_trades = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in inputs["source_trades"]}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["l5"]:
        if row["target_policy_variant_id"] == SOURCE_POLICY:
            grouped[row["decision_asof_ts"]].append(row)

    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    guard_rows: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    trade_idx = 1
    guard_idx = 1
    for policy_id in POLICIES:
        capital = INITIAL_CAPITAL
        peak_capital = INITIAL_CAPITAL
        prev_period_pnl = 0.0
        for decision_ts in sorted(grouped):
            current_drawdown = capital / peak_capital - 1.0 if peak_capital else 0.0
            state = stress_state(current_drawdown, prev_period_pnl)
            candidates = sorted(
                grouped[decision_ts],
                key=lambda row: (
                    to_float(cards_by_spec.get(row["trade_spec_id"], {}).get("api_adjusted_rank_score")),
                    to_float(cards_by_spec.get(row["trade_spec_id"], {}).get("base_winner_acceleration_rank_score")),
                ),
                reverse=True,
            )[:2]
            base_alloc = capital / 2.0
            period_pnl = 0.0
            allocated = 0
            for row in candidates:
                spec_id = row["trade_spec_id"]
                card = cards_by_spec.get(spec_id)
                decision = decisions_by_spec.get(spec_id)
                l5 = l5_by_spec.get(spec_id)
                src = source_trades.get((SOURCE_POLICY, spec_id))
                if not card or not decision or not l5 or not src:
                    continue
                winner = is_winner_preserve(src, l5)
                api_mult_base = to_float(decision["api_l5_budget_multiplier"], 1.0)
                api_mult, guard_action = guard_multiplier(policy_id, api_mult_base, state, card["api_l2_state"], winner)
                raw_mult = to_float(l5["raw_combined_multiplier"])
                pre_final_mult = clamp(raw_mult * api_mult, 0.0, 1.42)
                mult, final_cap_action = final_budget_cap(policy_id, pre_final_mult, state, winner)
                cap_alloc = base_alloc * mult
                pnl = cap_alloc * to_float(src["net_return"])
                capital += pnl
                period_pnl += pnl
                allocated += 1
                guard_rows.append(
                    {
                        "task_id": "Task2192",
                        "guard_row_id": f"APIDDGUARD-2192-{guard_idx:07d}",
                        "policy_variant_id": policy_id,
                        "trade_spec_id": spec_id,
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "portfolio_drawdown_before_trade": round(current_drawdown, 6),
                        "previous_period_pnl": round(prev_period_pnl, 4),
                        "drawdown_guard_state": state,
                        "api_l2_state": card["api_l2_state"],
                        "winner_preserve_flag": "1" if winner else "0",
                        "api_multiplier_before_guard": round(api_mult_base, 6),
                        "api_multiplier_after_guard": round(api_mult, 6),
                        "guard_action": guard_action,
                        "final_budget_multiplier_before_cap": round(pre_final_mult, 6),
                        "final_budget_multiplier_after_cap": round(mult, 6),
                        "final_budget_cap_action": final_cap_action,
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "authority": AUTHORITY,
                    }
                )
                guard_idx += 1
                trades.append(
                    {
                        "task_id": "Task2194",
                        "trade_row_id": f"APIDDTRADE-2194-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": SOURCE_POLICY,
                        "baseline_policy_variant_id": BASELINE_POLICY,
                        "trade_spec_id": spec_id,
                        "candidate_source_id": row["candidate_source_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "drawdown_guard_state": state,
                        "guard_action": guard_action,
                        "final_budget_cap_action": final_cap_action,
                        "api_l2_state": card["api_l2_state"],
                        "winner_preserve_flag": "1" if winner else "0",
                        "final_budget_multiplier": round(mult, 6),
                        "source_net_return": src.get("net_return", ""),
                        "capital_allocated": round(cap_alloc, 4),
                        "pnl": round(pnl, 4),
                        "net_return": src.get("net_return", ""),
                        "entry_date": src.get("entry_date", ""),
                        "actual_exit_date": src.get("actual_exit_date", ""),
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            equity.append(
                {
                    "task_id": "Task2195",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "portfolio_drawdown_before_period": round(current_drawdown, 6),
                    "drawdown_guard_state": state,
                    "candidate_pool_count": len(grouped[decision_ts]),
                    "allocated_count": allocated,
                    "authority": AUTHORITY,
                }
            )
            prev_period_pnl = period_pnl
            peak_capital = max(peak_capital, capital)
        policy_trades = [row for row in trades if row["policy_variant_id"] == policy_id]
        policy_equity = [row for row in equity if row["policy_variant_id"] == policy_id]
        metrics.append(metrics_for(policy_id, policy_trades, policy_equity, inputs["baseline_metrics"]))
    return guard_rows, trades, equity, metrics


def aggregate_guard(guard_rows: list[dict[str, object]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    pnl_by_key = {(row["policy_variant_id"], row["trade_spec_id"], row["decision_asof_ts"]): to_float(row["pnl"]) for row in trades}
    acc: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"rows": 0.0, "delta_mult": 0.0, "pnl": 0.0})
    for row in guard_rows:
        key = (str(row["policy_variant_id"]), str(row["guard_action"]))
        acc[key]["rows"] += 1
        acc[key]["delta_mult"] += to_float(row["api_multiplier_after_guard"]) - to_float(row["api_multiplier_before_guard"])
        acc[key]["pnl"] += pnl_by_key.get((row["policy_variant_id"], row["trade_spec_id"], row["decision_asof_ts"]), 0.0)
    out = []
    for idx, ((policy_id, action), vals) in enumerate(sorted(acc.items()), start=1):
        out.append(
            {
                "task_id": "Task2193",
                "guard_summary_id": f"APIDDGUARDSUM-2193-{idx:04d}",
                "policy_variant_id": policy_id,
                "guard_action": action,
                "row_count": int(vals["rows"]),
                "api_multiplier_delta_sum": round(vals["delta_mult"], 6),
                "guarded_trade_pnl_sum": round(vals["pnl"], 4),
                "authority": AUTHORITY,
            }
        )
    return out


def closeout_rows(metrics: list[dict[str, object]], guard_summary: list[dict[str, object]]) -> list[dict[str, object]]:
    best_joint = [row for row in metrics if row["joint_target_met"] == "1"]
    if best_joint:
        best = max(best_joint, key=lambda row: to_float(row["final_equity"]))
    else:
        best = max(metrics, key=lambda row: to_float(row["final_equity"]) + max(to_float(row["max_drawdown"]), -1.0) * 1000.0)
    guarded_rows = sum(int(row["row_count"]) for row in guard_summary if row["guard_action"] != "no_guard_normal_state")
    return [
        {
            "task_id": "Task2200",
            "verdict": "api_drawdown_sizing_guard_complete_diagnostic_only",
            "policy_variant_count": len(metrics),
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "best_delta_vs_api_baseline_final": best["delta_vs_baseline_final_equity"],
            "best_delta_vs_api_baseline_mdd": best["delta_vs_baseline_mdd"],
            "joint_target_met": best["joint_target_met"],
            "guarded_trade_rows": guarded_rows,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], guard_summary: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metric_lines = "\n".join(
        f"- `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, delta final {row['delta_vs_baseline_final_equity']}, delta MDD {row['delta_vs_baseline_mdd']}."
        for row in metrics
    )
    guard_lines = "\n".join(
        f"- `{row['policy_variant_id']}` / {row['guard_action']}: rows {row['row_count']}, multiplier delta {row['api_multiplier_delta_sum']}, pnl {row['guarded_trade_pnl_sum']}."
        for row in guard_summary[:20]
    )
    text = f"""# Task2191-2200 API Drawdown Sizing Guard

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Best policy: `{closeout['best_policy_variant_id']}`.
- Final equity: {closeout['best_final_equity']}.
- CAGR: {closeout['best_cagr']}.
- MDD: {closeout['best_max_drawdown']}.
- Delta vs API baseline final: {closeout['best_delta_vs_api_baseline_final']}.
- Delta vs API baseline MDD: {closeout['best_delta_vs_api_baseline_mdd']}.
- Joint target met: {closeout['joint_target_met']}.
- Guarded trade rows: {closeout['guarded_trade_rows']}.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

The guard uses only prior portfolio drawdown and previous-period PnL state at each decision. It caps API boost during stress and preserves high winner-defense trades. The intent is to reduce drawdown without killing CIEN/AVGO/AEIS-style winner sizing.

Replay results:

{metric_lines}

Guard action summary:

{guard_lines}

## No-Background Decision-Maker Report

Conclusion first: this is a drawdown-state sizing guard, not a new selector. It tries to stop API boost from making bad market windows worse while leaving strong winner trades alone.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2191_2200_api_drawdown_sizing_guard/`.
- Validator: `python scripts/trader_brain_2191_2200_api_drawdown_sizing_guard_validate.py`.

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
    for task_no in range(2191, 2201):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "task_name": f"API Drawdown Sizing Guard Step {task_no}",
                "workstream": "Research Governance / Backtest & Simulation Infra",
                "status": "active",
                "validation_tier": "diagnostic-only",
                "acceptance_state": "NOT_ACCEPTED",
                "current_decision": "api-drawdown-sizing-guard-diagnostic-only",
                "upstream_task": f"Task{task_no - 1}" if task_no > 2191 else "Task2190",
                "report_path": "docs/reports/task_2191_2200_api_drawdown_sizing_guard/task_2191_2200_api_drawdown_sizing_guard.md",
                "decision_path": "docs/reports/task_2191_2200_api_drawdown_sizing_guard/task_2191_2200_decision.csv",
                "artifact_path": "data/artifacts/task_2191_2200_api_drawdown_sizing_guard",
                "validation_command": "python scripts/trader_brain_2191_2200_api_drawdown_sizing_guard_validate.py",
                "notes": "Adds prior-state drawdown sizing guard to API overlay while preserving strong winner-defense trades.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "109. Task2191-Task2200"
    if marker in text:
        return
    line = (
        f"109. Task2191-Task2200 implemented a prior-state API drawdown sizing guard: best "
        f"`{closeout['best_policy_variant_id']}` ended final {closeout['best_final_equity']} with CAGR "
        f"{closeout['best_cagr']} and MDD {closeout['best_max_drawdown']}, guarded rows "
        f"{closeout['guarded_trade_rows']}, while status remains NOT_ACCEPTED / "
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
    inputs = load_inputs()
    guard_rows, trades, equity, metrics = replay_guard(inputs)
    guard_summary = aggregate_guard(guard_rows, trades)
    closeout = closeout_rows(metrics, guard_summary)
    write_csv(OUT_DIR / "task2191_guard_contract.csv", [
        {
            "task_id": "Task2191",
            "guard_contract_id": "APIDDGUARD-CONTRACT-2191",
            "input_state_allowed": "prior_portfolio_drawdown;previous_period_pnl;winner_defense_bucket;winner_quality_beta;api_l2_state",
            "forbidden_inputs": "future_return;future_drawdown_window;outcome_label;post_trade_price_path",
            "goal": "cap API boost during stress while preserving strong winner-defense trades",
            "authority": AUTHORITY,
        }
    ])
    write_csv(OUT_DIR / "task2192_guard_decision_ledger.csv", guard_rows)
    write_csv(OUT_DIR / "task2193_guard_action_summary.csv", guard_summary)
    write_csv(OUT_DIR / "task2194_guard_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task2195_guard_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task2196_guard_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task2200_closeout.csv", closeout)
    write_json(OUT_DIR / "task2200_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], metrics, guard_summary)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2191_2200_API_DRAWDOWN_SIZING_GUARD_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
