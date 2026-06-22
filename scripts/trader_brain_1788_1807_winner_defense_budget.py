from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1768_1787_preentry_risk_budget_v2 as v2
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1698 = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
TASK1768 = ROOT / "data/artifacts/task_1768_1787_preentry_risk_budget_v2"
OUT_DIR = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
REPORT_DIR = ROOT / "docs/reports/task_1788_1807_winner_defense_budget"
REPORT = REPORT_DIR / "task_1788_1807_winner_defense_budget.md"
DECISION = REPORT_DIR / "task_1788_1807_decision.csv"

AUTHORITY = "DIAGNOSTIC_WINNER_DEFENSE_BUDGET_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "winner_defense_budget_top3_v1": {
        "source_policy": "bad_trade_gate_top3_v1",
        "slot_cap": 3,
        "defense_credit_cap": 0.10,
        "max_multiplier": 1.14,
    },
    "winner_defense_budget_top5_v1": {
        "source_policy": "bad_trade_gate_top5_v1",
        "slot_cap": 5,
        "defense_credit_cap": 0.12,
        "max_multiplier": 1.15,
    },
}


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
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value: object) -> date | None:
    return v2.parse_date(value)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def expert_rows() -> list[dict[str, object]]:
    rows = [
        (
            "portfolio_trader",
            "AQR quality and momentum context",
            "Do not punish volatility before checking quality, surprise, and absorption.",
            "winner_defense_before_risk_budget",
        ),
        (
            "factor_quant",
            "Fama-French profitability, investment, and momentum factor framing",
            "Separate normal high-beta winner volatility from terminal business risk.",
            "add_winner_quality_beta",
        ),
        (
            "event_study_quant",
            "MacKinlay event-study abnormal-return framing",
            "Classify market/sector selloff separately from issuer-specific thesis break.",
            "add_volatility_cause",
        ),
        (
            "semiconductor_specialist",
            "AI and semiconductor cycle playbook",
            "High volatility is expected when relative strength and payoff quality persist.",
            "allow_quality_size_release",
        ),
        (
            "risk_officer",
            "pre-trade risk-budget discipline",
            "Winner defense must not override survival, dilution, financing, or terminal risk.",
            "hard_override_terminal_risk",
        ),
        (
            "backend_validator",
            "project no-leakage and harness discipline",
            "Use only pre-entry candidate and prior-price fields; outcomes remain audit-only.",
            "preserve_diagnostic_authority",
        ),
    ]
    return [
        {
            "task_id": "Task1788",
            "expert_review_id": f"WINDEF-1788-{idx:03d}",
            "expert_role": role,
            "source_anchor": source,
            "critique": critique,
            "implementation_decision": decision,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, source, critique, decision) in enumerate(rows, 1)
    ]


def keyed(path: Path) -> dict[str, dict[str, str]]:
    return {row["trade_spec_id"]: row for row in read_csv(path)}


def volatility_cause(row: dict[str, object], payoff: dict[str, str], collapse: dict[str, str]) -> str:
    event_family = str(payoff.get("event_family", row.get("event_family", "")))
    payoff_mechanism = str(payoff.get("payoff_mechanism", ""))
    prior_return = to_float(row.get("prior_return_63d"))
    relative_return = to_float(row.get("relative_return_63d"))
    drawdown = to_float(row.get("prior_drawdown_126d"))
    vol = to_float(row.get("realized_vol_63d"))
    terminal = str(collapse.get("terminal_risk_flag", "0")) == "1"

    if terminal or event_family in {"survival", "dilution", "financing"} or "terminal" in payoff_mechanism:
        return "terminal_or_financing_thesis_risk"
    if relative_return <= -0.16 and prior_return <= -0.12:
        return "issuer_specific_expectation_break"
    if prior_return <= -0.10 and relative_return >= -0.04:
        return "market_beta_selloff"
    if drawdown <= -0.18 and relative_return <= -0.08:
        return "company_specific_drawdown"
    if vol >= 0.45 and prior_return >= 0.12 and relative_return >= 0.08:
        return "normal_winner_volatility"
    if prior_return >= 0.20 and relative_return >= 0.12:
        return "leader_momentum_volatility"
    return "ordinary_noise"


def winner_quality_beta(row: dict[str, object], payoff: dict[str, str], collapse: dict[str, str], cause: str) -> float:
    score = 0.0
    payoff_score = to_float(row.get("payoff_quality_score"))
    score += clamp((payoff_score - 60.0) / 45.0, 0.0, 1.0) * 24.0

    bucket = str(row.get("payoff_quality_bucket", payoff.get("payoff_quality_bucket", "")))
    if bucket == "top3_payoff_candidate":
        score += 17.0
    elif bucket == "eligible_payoff_candidate":
        score += 10.0
    elif bucket == "watch_or_cap_candidate":
        score += 4.0
    elif bucket == "blocked_terminal_or_listing_risk":
        score -= 22.0

    event_family = str(payoff.get("event_family", ""))
    payoff_mechanism = str(payoff.get("payoff_mechanism", ""))
    if event_family == "positive" or payoff_mechanism == "revenue_or_customer_validation":
        score += 15.0
    elif event_family == "mixed":
        score += 4.0
    elif event_family in {"survival", "dilution", "financing"}:
        score -= 25.0

    expectation = str(payoff.get("expectation_state", ""))
    if expectation == "true_surprise_proxy":
        score += 18.0
    elif expectation == "guidance_change_proxy":
        score += 12.0
    elif expectation == "good_words_only":
        score += 4.0
    elif expectation == "negative_expectation_proxy":
        score -= 12.0

    absorption = str(payoff.get("absorption_state", ""))
    if absorption == "sustained_market_acceptance":
        score += 18.0
    elif absorption == "initial_reaction_only":
        score += 7.0
    elif absorption == "neutral_absorption":
        score += 2.0
    elif absorption in {"market_rejection_or_reversal", "weak_absorption"}:
        score -= 12.0

    independence = str(payoff.get("source_independence_state", ""))
    if independence == "independent_non_issuer_confirmation_present":
        score += 9.0
    elif independence == "confirmation_source_gap":
        score -= 4.0

    relative_return = to_float(row.get("relative_return_63d"))
    prior_return = to_float(row.get("prior_return_63d"))
    if relative_return >= 0.20:
        score += 11.0
    elif relative_return >= 0.08:
        score += 6.0
    elif relative_return <= -0.16:
        score -= 10.0
    if prior_return >= 0.30:
        score += 5.0

    if cause in {"normal_winner_volatility", "leader_momentum_volatility"}:
        score += 10.0
    elif cause == "market_beta_selloff":
        score += 5.0
    elif cause in {"issuer_specific_expectation_break", "company_specific_drawdown"}:
        score -= 10.0
    elif cause == "terminal_or_financing_thesis_risk":
        score -= 30.0

    if str(collapse.get("terminal_risk_flag", "0")) == "1":
        score = min(score, 20.0)
    return round(clamp(score, 0.0, 100.0), 4)


def defense_bucket(score: float) -> str:
    if score >= 82:
        return "strong_winner_defense"
    if score >= 68:
        return "qualified_winner_defense"
    if score >= 48:
        return "ordinary_defense"
    return "weak_or_no_defense"


def defense_credit(score: float, cause: str, event_family: str, cap: float) -> float:
    if event_family in {"survival", "dilution", "financing"} or cause == "terminal_or_financing_thesis_risk":
        return 0.0
    if score < 62:
        return 0.0
    raw = (score - 62.0) / 100.0
    if cause in {"normal_winner_volatility", "leader_momentum_volatility"}:
        raw += 0.04
    elif cause == "market_beta_selloff":
        raw += 0.025
    elif cause in {"issuer_specific_expectation_break", "company_specific_drawdown"}:
        raw -= 0.05
    return round(clamp(raw, 0.0, cap), 6)


def build_panel() -> list[dict[str, object]]:
    base = read_csv(TASK1768 / "task1770_preentry_risk_budget_v2_panel.csv")
    payoff = keyed(TASK1698 / "task1700_payoff_quality_v2_panel.csv")
    collapse = keyed(TASK1698 / "task1699_collapse_risk_v2_panel.csv")
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(base, 1):
        spec_id = str(row["trade_spec_id"])
        pay = payoff.get(spec_id, {})
        col = collapse.get(spec_id, {})
        source_policy = str(row["policy_variant_id"])
        target_policy = "winner_defense_budget_top3_v1" if source_policy == "bad_trade_gate_top3_v1" else "winner_defense_budget_top5_v1"
        policy = POLICIES[target_policy]
        cause = volatility_cause(row, pay, col)
        quality = winner_quality_beta(row, pay, col, cause)
        credit = defense_credit(quality, cause, str(pay.get("event_family", "")), float(policy["defense_credit_cap"]))
        risk_pressure = to_float(row.get("risk_pressure"))
        cluster_pressure = to_float(row.get("cluster_pressure"))
        fragility_pressure = to_float(row.get("fragility_pressure"))
        air_pressure = to_float(row.get("air_pocket_pressure"))
        liquidity_pressure = to_float(row.get("liquidity_pressure"))
        payoff_credit = to_float(row.get("payoff_credit"))

        adjusted_risk_pressure = risk_pressure
        adjusted_cluster_pressure = cluster_pressure
        if quality >= 82 and cause in {"normal_winner_volatility", "leader_momentum_volatility", "market_beta_selloff"}:
            adjusted_risk_pressure = max(0.0, risk_pressure - 0.08)
        elif quality >= 68 and cause in {"normal_winner_volatility", "leader_momentum_volatility"}:
            adjusted_risk_pressure = max(0.0, risk_pressure - 0.04)

        if cause in {"issuer_specific_expectation_break", "company_specific_drawdown"} and quality < 70:
            adjusted_risk_pressure += 0.04
        if cause == "terminal_or_financing_thesis_risk":
            adjusted_risk_pressure += 0.10

        multiplier = (
            1.0
            + payoff_credit
            + credit
            - adjusted_risk_pressure
            - adjusted_cluster_pressure
            - fragility_pressure
            - air_pressure
            - liquidity_pressure
        )
        if row["selection_reason"] != "baseline_preserved":
            multiplier = min(multiplier, 0.45 if quality >= 70 else 0.35)
        if cause == "terminal_or_financing_thesis_risk":
            multiplier = min(multiplier, 0.40)
        no_entry = cause == "terminal_or_financing_thesis_risk" and quality < 35
        if no_entry:
            multiplier = 0.0
        elif multiplier < 0.20:
            multiplier = 0.20
        multiplier = round(clamp(multiplier, 0.0, float(policy["max_multiplier"])), 4)

        out = dict(row)
        out.update(
            {
                "task_id": "Task1790",
                "winner_defense_id": f"WINDEF-1790-{idx:07d}",
                "target_policy_variant_id": target_policy,
                "event_family": pay.get("event_family", ""),
                "payoff_mechanism": pay.get("payoff_mechanism", ""),
                "expectation_state": pay.get("expectation_state", ""),
                "absorption_state": pay.get("absorption_state", ""),
                "materiality_state": pay.get("materiality_state", ""),
                "source_independence_state": pay.get("source_independence_state", ""),
                "volatility_cause": cause,
                "winner_quality_beta": quality,
                "winner_defense_bucket": defense_bucket(quality),
                "winner_defense_credit": credit,
                "adjusted_risk_pressure": round(adjusted_risk_pressure, 6),
                "adjusted_cluster_pressure": round(adjusted_cluster_pressure, 6),
                "winner_defense_multiplier_v3": multiplier,
                "winner_defense_action": "no_entry" if no_entry else "enter_with_winner_defense_budget",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        rows.append(out)
    return rows


def baseline_trade_returns() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1698 / "task1704_bad_trade_gate_replay_trades.csv")
    }


def replay_budget(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    baseline = baseline_trade_returns()
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["target_policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    actions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    action_idx = 1
    trade_idx = 1
    for policy_id, policy in POLICIES.items():
        source_policy = str(policy["source_policy"])
        capital = INITIAL_CAPITAL
        decisions = sorted({key[1] for key in grouped if key[0] == policy_id})
        for decision_ts in decisions:
            items = sorted(
                grouped[(policy_id, decision_ts)],
                key=lambda row: (to_float(row["winner_defense_multiplier_v3"]), to_float(row["winner_quality_beta"])),
                reverse=True,
            )
            base_alloc = capital / int(policy["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            for selected in items:
                source = baseline.get((source_policy, str(selected["trade_spec_id"])))
                if not source:
                    continue
                cap = to_float(selected["winner_defense_multiplier_v3"])
                action = "no_entry" if cap <= 0 else "enter_with_winner_defense_budget"
                actions.append(
                    {
                        "task_id": "Task1791",
                        "winner_defense_action_id": f"WINDEFACTION-1791-{action_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "volatility_cause": selected["volatility_cause"],
                        "winner_defense_bucket": selected["winner_defense_bucket"],
                        "winner_quality_beta": selected["winner_quality_beta"],
                        "winner_defense_multiplier_v3": cap,
                        "budget_action": action,
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
                action_idx += 1
                if cap <= 0:
                    continue
                allocated = base_alloc * cap
                pnl = allocated * to_float(source.get("net_return"))
                period_pnl += pnl
                capital += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task1792",
                        "trade_row_id": f"WINDEFTRADE-1792-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "volatility_cause": selected["volatility_cause"],
                        "winner_defense_bucket": selected["winner_defense_bucket"],
                        "winner_quality_beta": selected["winner_quality_beta"],
                        "winner_defense_multiplier_v3": cap,
                        "source_net_return": source.get("net_return", ""),
                        "capital_allocated": round(allocated, 4),
                        "pnl": round(pnl, 4),
                        "net_return": source.get("net_return", ""),
                        "entry_date": source.get("entry_date", ""),
                        "actual_exit_date": source.get("actual_exit_date", ""),
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            equity.append(
                {
                    "task_id": "Task1792",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "allocated_count": allocated_count,
                    "authority": AUTHORITY,
                }
            )
    return actions, trades, equity


def metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base = {row["policy_variant_id"]: row for row in read_csv(TASK1768 / "task1773_preentry_budget_v2_replay_metrics.csv")}
    base_map = {
        "winner_defense_budget_top3_v1": "preentry_risk_budget_v2_top3_v1",
        "winner_defense_budget_top5_v1": "preentry_risk_budget_v2_top5_v1",
    }
    tr_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    eq_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        tr_groups[str(row["policy_variant_id"])].append(row)
    for row in equity:
        eq_groups[str(row["policy_variant_id"])].append(row)
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(eq_groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        tr_rows = tr_groups[policy_id]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end_dates = [parse_date(row.get("actual_exit_date")) for row in tr_rows]
        end = max([d for d in end_dates if d is not None] or [start])
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        baseline = base[base_map[policy_id]]
        rows.append(
            {
                "task_id": "Task1793",
                "policy_variant_id": policy_id,
                "baseline_policy_variant_id": base_map[policy_id],
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "baseline_final_equity": baseline["final_equity"],
                "baseline_cagr": baseline["cagr"],
                "baseline_max_drawdown": baseline["max_drawdown"],
                "delta_final_equity": round(final - to_float(baseline["final_equity"]), 4),
                "delta_cagr": round(cagr - to_float(baseline["cagr"]), 6),
                "delta_mdd": round(mdd - to_float(baseline["max_drawdown"]), 6),
                "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
                "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def split_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        d = replay.parse_ts(str(row["decision_asof_ts"])).date()
        window = "IS_2021_2023" if d.year <= 2023 else "OOS_2024_2026Q1"
        groups[(str(row["policy_variant_id"]), window)].append(row)
    rows: list[dict[str, object]] = []
    for (policy_id, window), items in sorted(groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        rows.append(
            {
                "task_id": "Task1794",
                "policy_variant_id": policy_id,
                "split_window": window,
                "period_count": len(items),
                "split_final_equity": round(values[-1], 4),
                "split_total_return": round(values[-1] / INITIAL_CAPITAL - 1.0, 6),
                "split_max_drawdown": round(replay.max_drawdown(values), 6),
                "authority": AUTHORITY,
            }
        )
    return rows


def attribution(panel: list[dict[str, object]], trades: list[dict[str, object]], mrows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for label in ["volatility_cause", "winner_defense_bucket", "factor_cluster"]:
        counts = Counter(str(row[label]) for row in panel)
        for reason, count in counts.most_common():
            rows.append({"task_id": "Task1795", "attribution_id": f"WINDEFATTR-1795-{idx:05d}", "failure_area": label, "reason": reason, "row_count": count, "authority": AUTHORITY})
            idx += 1
    by_bucket: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        by_bucket[str(row["winner_defense_bucket"])].append(row)
    for bucket, group in sorted(by_bucket.items()):
        rows.append(
            {
                "task_id": "Task1795",
                "attribution_id": f"WINDEFATTR-1795-{idx:05d}",
                "failure_area": "bucket_pnl",
                "reason": bucket,
                "row_count": len(group),
                "pnl_sum": round(sum(to_float(row["pnl"]) for row in group), 4),
                "avg_net_return": round(sum(to_float(row["net_return"]) for row in group) / len(group), 6) if group else 0.0,
                "authority": AUTHORITY,
            }
        )
        idx += 1
    for row in mrows:
        if row["target_cagr_30pct_met"] != "1" or row["target_mdd_minus30pct_met"] != "1":
            rows.append(
                {
                    "task_id": "Task1795",
                    "attribution_id": f"WINDEFATTR-1795-{idx:05d}",
                    "failure_area": "target_failure",
                    "policy_variant_id": row["policy_variant_id"],
                    "cagr": row["cagr"],
                    "max_drawdown": row["max_drawdown"],
                    "delta_final_equity": row["delta_final_equity"],
                    "delta_mdd": row["delta_mdd"],
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def gate_closeout(mrows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best = max(mrows, key=lambda row: to_float(row["final_equity"]))
    gate = [
        {
            "task_id": "Task1806",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "cagr_30pct_met_by_any": "1" if any(row["target_cagr_30pct_met"] == "1" for row in mrows) else "0",
            "mdd_minus30pct_met_by_any": "1" if any(row["target_mdd_minus30pct_met"] == "1" for row in mrows) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "winner_defense_budget_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1807",
            "verdict": "winner_defense_budget_implemented_diagnostic_only",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit winner defense misses and add true sector-relative quality beta before any acceptance claim",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(mrows: list[dict[str, object]], splits: list[dict[str, object]], attr: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1788-1807 Winner Defense Budget",
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
        "| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | CAGR Target | MDD Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in mrows:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['baseline_final_equity']} | {row['baseline_max_drawdown']} | {row['delta_final_equity']} | {row['delta_mdd']} | {row['trade_count']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |"
        )
    lines.extend(["", "Split/OOS diagnostics:", "", "| Policy | Window | Final | Return | MDD |", "| --- | --- | ---: | ---: | ---: |"])
    for row in splits:
        lines.append(f"| `{row['policy_variant_id']}` | {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(["", "Attribution:", ""])
    for row in attr[:32]:
        lines.append(f"- `{row['failure_area']}`: {row.get('reason', row.get('policy_variant_id', ''))} count={row.get('row_count','')} pnl={row.get('pnl_sum','')} cagr={row.get('cagr','')} mdd={row.get('max_drawdown','')}")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. V3 adds winner defense before risk-budget sizing.",
            "2. It separates normal winner volatility from terminal or issuer-specific damage.",
            "3. It lets high-quality winners regain size only when payoff, expectation, absorption, and relative strength support it.",
            "4. Survival, financing, dilution, and terminal risk cannot be overridden by winner defense.",
            "5. The result remains diagnostic and does not approve strategy.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1788_expert_review.csv`",
            "- `task1790_winner_defense_panel.csv`",
            "- `task1791_winner_defense_action_panel.csv`",
            "- `task1792_winner_defense_replay_trades.csv/equity`",
            "- `task1793_winner_defense_replay_metrics.csv`",
            "- `task1794_split_oos_metrics.csv`",
            "- `task1795_failure_attribution.csv`",
            "- `task1806_acceptance_gate.csv`",
            "- `task1807_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1788_1807_winner_defense_budget_validate.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    experts = expert_rows()
    panel = build_panel()
    actions, trades, equity = replay_budget(panel)
    mrows = metrics(trades, equity)
    splits = split_rows(equity)
    attr = attribution(panel, trades, mrows)
    gate, closeout = gate_closeout(mrows)
    outputs = [
        ("task1788_expert_review.csv", experts),
        ("task1790_winner_defense_panel.csv", panel),
        ("task1791_winner_defense_action_panel.csv", actions),
        ("task1792_winner_defense_replay_trades.csv", trades),
        ("task1792_winner_defense_replay_equity.csv", equity),
        ("task1793_winner_defense_replay_metrics.csv", mrows),
        ("task1794_split_oos_metrics.csv", splits),
        ("task1795_failure_attribution.csv", attr),
        ("task1806_acceptance_gate.csv", gate),
        ("task1807_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1807_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(mrows, splits, attr, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1788_1807] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
