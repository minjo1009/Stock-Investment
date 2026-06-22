from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1558_1577_l5_damage_control_engine as damage
import trader_brain_1668_1687_l5_thesis_aware_action_engine as thesis_l5
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK1698 = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
OUT_DIR = ROOT / "data/artifacts/task_1748_1767_preentry_risk_budget"
REPORT_DIR = ROOT / "docs/reports/task_1748_1767_preentry_risk_budget"
REPORT = REPORT_DIR / "task_1748_1767_preentry_risk_budget.md"
DECISION = REPORT_DIR / "task_1748_1767_decision.csv"

AUTHORITY = "DIAGNOSTIC_PREENTRY_RISK_BUDGET_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "preentry_risk_budget_top3_v1": {"source_policy": "bad_trade_gate_top3_v1", "slot_cap": 3},
    "preentry_risk_budget_top5_v1": {"source_policy": "bad_trade_gate_top5_v1", "slot_cap": 5},
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
    return thesis_l5.parse_date(value)


def pct_return(start: float, end: float) -> float:
    if start <= 0:
        return 0.0
    return end / start - 1.0


def expert_review_rows() -> list[dict[str, object]]:
    rows = [
        ("firm_trader", "SEC/FINRA market access", "pre-trade controls must exist before exposure enters the book", "adopt"),
        ("risk_pm", "CFA risk budgeting", "position size should follow risk contribution not conviction alone", "adopt"),
        ("execution_trader", "CME position sizing", "maximum loss and stop distance must be known before entry", "adopt"),
        ("factor_pm", "AQR portfolio construction", "risk clusters can dominate security-level signal", "adopt"),
        ("risk_layer_specialist", "BlackRock risk layers", "decompose positions into risk drivers before sizing", "adopt"),
        ("event_trader", "MacKinlay event-study framing", "post-event drift must be sized by event-window risk", "adopt"),
        ("distress_researcher", "distress risk literature", "terminal and liquidity risk should cap entry size", "adopt"),
        ("backend_engineer", "project harness discipline", "risk budget assignment must be source-time safe", "adopt"),
        ("governance_reviewer", "Task747 validation map", "diagnostic replay cannot approve strategy", "adopt"),
        ("portfolio_manager", "cluster exposure audit", "avoid holding multiple names with the same shock exposure at full size", "adopt"),
    ]
    return [
        {
            "task_id": "Task1748",
            "expert_review_id": f"PREBUDGET1748-{idx:03d}",
            "expert_role": role,
            "source_anchor": source,
            "critique": critique,
            "implementation_decision": decision,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, source, critique, decision) in enumerate(rows, 1)
    ]


def trade_specs_by_id() -> dict[str, dict[str, str]]:
    return {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}


def l2_by_spec() -> dict[str, dict[str, str]]:
    return {row["trade_spec_id"]: row for row in read_csv(TASK1488 / "task1491_l2_semantic_v6_panel.csv")}


def snapshot(frame: pd.DataFrame | None, qqq: pd.DataFrame | None, symbol: str, decision_date: date) -> dict[str, object]:
    if frame is None:
        return {
            "price_history_state": "missing_price_history",
            "prior_return_63d": "",
            "qqq_prior_return_63d": "",
            "relative_return_63d": "",
            "prior_drawdown_126d": "",
            "realized_vol_63d": "",
            "avg_dollar_volume_20d": "",
        }
    hist = frame[frame["Date"] <= decision_date].tail(126).copy()
    if hist.empty:
        return {
            "price_history_state": "empty_price_history",
            "prior_return_63d": "",
            "qqq_prior_return_63d": "",
            "relative_return_63d": "",
            "prior_drawdown_126d": "",
            "realized_vol_63d": "",
            "avg_dollar_volume_20d": "",
        }
    price = float(hist.iloc[-1]["Close"])
    prior63 = pct_return(float(hist.iloc[-64]["Close"]), price) if len(hist) >= 64 else 0.0
    qqq_prior = 0.0
    if qqq is not None:
        qhist = qqq[qqq["Date"] <= decision_date].tail(64)
        if len(qhist) >= 2:
            qqq_prior = pct_return(float(qhist.iloc[0]["Close"]), float(qhist.iloc[-1]["Close"]))
    high126 = float(hist["Close"].max())
    drawdown126 = price / high126 - 1.0 if high126 > 0 else 0.0
    returns = hist["Close"].pct_change().dropna().tail(63)
    vol63 = float(returns.std() * (252**0.5)) if not returns.empty else 0.0
    avg20 = hist.tail(20).assign(dollar_volume=lambda x: x["Close"] * x["Volume"])["dollar_volume"].mean()
    return {
        "price_history_state": "present",
        "prior_return_63d": round(prior63, 8),
        "qqq_prior_return_63d": round(qqq_prior, 8),
        "relative_return_63d": round(prior63 - qqq_prior, 8),
        "prior_drawdown_126d": round(drawdown126, 8),
        "realized_vol_63d": round(vol63, 8),
        "avg_dollar_volume_20d": round(float(avg20), 4) if pd.notna(avg20) else "",
    }


def factor_cluster(symbol: str, theme: str) -> str:
    cyclical_materials = {"AA", "CC", "CE", "CF", "ALB", "X", "FCX", "NUE", "CLF", "CAT", "DE", "AGCO", "ADM", "CBT"}
    semis_growth = {"AMD", "AMAT", "AMBA", "AVGO", "ADI", "ASML", "ACLS", "AEIS", "ARM", "NVDA", "MRVL"}
    speculative_growth = {"ASTS", "ALHC", "CDNA", "AVPT", "ANET", "AXON", "BMRN", "CALX", "AZTA"}
    financial_beta = {"AIG", "AMP", "CB", "AFG", "AFL", "C", "BAC", "GS", "MS"}
    defensive = {"AEP", "BDX", "ABBV", "CI", "CASY"}
    if symbol in cyclical_materials or "industrial" in theme or "power_grid" in theme:
        return "cyclical_beta"
    if symbol in semis_growth or "semiconductor" in theme or "cloud_ai" in theme:
        return "semis_growth_beta"
    if symbol in speculative_growth or "biotech" in theme or "space" in theme:
        return "speculative_growth"
    if symbol in financial_beta:
        return "financial_beta"
    if symbol in defensive:
        return "defensive_quality"
    return "mixed_other"


def build_preentry_panel() -> list[dict[str, object]]:
    selected = read_csv(TASK1698 / "task1702_top3_top5_candidate_compressor.csv")
    specs = trade_specs_by_id()
    l2 = l2_by_spec()
    cache: dict[str, pd.DataFrame | None] = {}
    qqq = replay.load_price("QQQ", cache)
    base_rows: list[dict[str, object]] = []
    for idx, row in enumerate(selected, 1):
        spec = specs.get(row["trade_spec_id"], {})
        l2_row = l2.get(row["trade_spec_id"], {})
        decision_date = replay.parse_ts(row["decision_asof_ts"]).date()
        frame = replay.load_price(row["symbol"], cache)
        snap = snapshot(frame, qqq, row["symbol"], decision_date)
        theme = spec.get("derived_theme") or l2_row.get("derived_theme", "")
        cluster = factor_cluster(row["symbol"], theme)
        prior_ret = to_float(snap["prior_return_63d"])
        rel_ret = to_float(snap["relative_return_63d"])
        dd126 = to_float(snap["prior_drawdown_126d"])
        vol = to_float(snap["realized_vol_63d"])
        dollar_vol = to_float(snap["avg_dollar_volume_20d"])
        payoff = to_float(row["payoff_quality_score"])
        air_pocket = prior_ret >= 0.30 and vol >= 0.45
        fragility = rel_ret <= -0.08 or dd126 <= -0.18
        liquidity = dollar_vol > 0 and dollar_vol < 5_000_000
        high_vol = vol >= 0.70
        quality_weak = row["payoff_quality_bucket"] in {"watch_or_cap_candidate", "low_payoff_candidate"}
        base_rows.append(
            {
                "task_id": "Task1750",
                "preentry_risk_id": f"PREBUDGET1750-{idx:07d}",
                "policy_variant_id": row["policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "derived_theme": theme,
                "factor_cluster": cluster,
                "selection_reason": row["selection_reason"],
                "collapse_risk_bucket": row["collapse_risk_bucket"],
                "payoff_quality_bucket": row["payoff_quality_bucket"],
                "payoff_quality_score": payoff,
                "prior_return_63d": snap["prior_return_63d"],
                "relative_return_63d": snap["relative_return_63d"],
                "prior_drawdown_126d": snap["prior_drawdown_126d"],
                "realized_vol_63d": snap["realized_vol_63d"],
                "avg_dollar_volume_20d": snap["avg_dollar_volume_20d"],
                "air_pocket_risk": "1" if air_pocket else "0",
                "fragility_risk": "1" if fragility else "0",
                "liquidity_risk": "1" if liquidity else "0",
                "high_vol_risk": "1" if high_vol else "0",
                "quality_weak_risk": "1" if quality_weak else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    cluster_counts: Counter[tuple[str, str, str]] = Counter((str(r["policy_variant_id"]), str(r["decision_asof_ts"]), str(r["factor_cluster"])) for r in base_rows)
    rows: list[dict[str, object]] = []
    for row in base_rows:
        cluster_count = cluster_counts[(str(row["policy_variant_id"]), str(row["decision_asof_ts"]), str(row["factor_cluster"]))]
        risk_points = 0
        risk_points += 2 if row["air_pocket_risk"] == "1" else 0
        risk_points += 2 if row["fragility_risk"] == "1" else 0
        risk_points += 1 if row["liquidity_risk"] == "1" else 0
        risk_points += 1 if row["high_vol_risk"] == "1" else 0
        risk_points += 1 if row["quality_weak_risk"] == "1" else 0
        risk_points += 2 if cluster_count >= 2 and row["factor_cluster"] not in {"defensive_quality", "mixed_other"} else 0
        risk_points += 1 if row["collapse_risk_bucket"] in {"dilution_pressure", "terminal_business_risk", "listing_compliance_risk"} else 0
        payoff = to_float(row["payoff_quality_score"])
        if risk_points >= 5 and payoff < 85:
            state = "no_entry"
            cap = 0.0
        elif risk_points >= 4:
            state = "quarter_size_preplanned_reduce"
            cap = 0.25
        elif risk_points >= 3:
            state = "half_size_risk_budget"
            cap = 0.5
        elif risk_points >= 2 and cluster_count >= 2:
            state = "cluster_soft_cap"
            cap = 0.75
        else:
            state = "full_size"
            cap = 1.0
        if row["selection_reason"] != "baseline_preserved":
            cap = min(cap, 0.25)
            if state == "full_size":
                state = "new_candidate_quarter_size"
        row.update(
            {
                "cluster_count_same_decision": cluster_count,
                "preentry_risk_points": risk_points,
                "risk_budget_state": state,
                "risk_budget_multiplier": cap,
            }
        )
        rows.append(row)
    return rows


def baseline_trade_returns() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1698 / "task1704_bad_trade_gate_replay_trades.csv")
    }


def replay_budget(preentry_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    baseline = baseline_trade_returns()
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in preentry_rows:
        groups[(str(row["policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    action_rows: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    action_idx = 1
    trade_idx = 1
    for policy_id, policy in POLICIES.items():
        source_policy = policy["source_policy"]
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in groups if key[0] == source_policy}):
            items = sorted(groups[(source_policy, decision_ts)], key=lambda r: to_float(r["preentry_risk_points"], 0))
            base_alloc = capital / int(policy["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            for selected in items:
                base = baseline.get((source_policy, str(selected["trade_spec_id"])))
                if not base:
                    continue
                cap = to_float(selected["risk_budget_multiplier"])
                action = "no_entry" if cap <= 0 else "enter_with_preentry_budget"
                action_rows.append(
                    {
                        "task_id": "Task1751",
                        "budget_action_id": f"PREACTION1751-{action_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "risk_budget_state": selected["risk_budget_state"],
                        "risk_budget_multiplier": cap,
                        "budget_action": action,
                        "preplanned_reduce_trigger": "relative_break_or_cluster_shock" if 0 < cap < 1 else "",
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
                action_idx += 1
                if cap <= 0:
                    continue
                allocated = base_alloc * cap
                pnl = allocated * to_float(base.get("net_return"))
                period_pnl += pnl
                capital += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task1752",
                        "trade_row_id": f"PREBUDGETTRADE1752-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "entry_date": base.get("entry_date", ""),
                        "planned_exit_date": base.get("planned_exit_date", ""),
                        "actual_exit_date": base.get("actual_exit_date", ""),
                        "risk_budget_state": selected["risk_budget_state"],
                        "risk_budget_multiplier": cap,
                        "source_net_return": base.get("net_return", ""),
                        "capital_allocated": round(allocated, 4),
                        "pnl": round(pnl, 4),
                        "net_return": base.get("net_return", ""),
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            equity.append(
                {
                    "task_id": "Task1752",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "allocated_count": allocated_count,
                    "authority": AUTHORITY,
                }
            )
    return action_rows, trades, equity


def metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base_metrics = {row["policy_variant_id"]: row for row in read_csv(TASK1698 / "task1705_bad_trade_gate_replay_metrics.csv")}
    base_map = {
        "preentry_risk_budget_top3_v1": "bad_trade_gate_top3_v1",
        "preentry_risk_budget_top5_v1": "bad_trade_gate_top5_v1",
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
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        tr_rows = tr_groups[policy_id]
        end_dates = [parse_date(row.get("actual_exit_date")) for row in tr_rows]
        end = max([d for d in end_dates if d is not None] or [start])
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        base = base_metrics[base_map[policy_id]]
        rows.append(
            {
                "task_id": "Task1753",
                "policy_variant_id": policy_id,
                "baseline_policy_variant_id": base_map[policy_id],
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "baseline_final_equity": base["final_equity"],
                "baseline_cagr": base["cagr"],
                "baseline_max_drawdown": base["max_drawdown"],
                "delta_final_equity": round(final - to_float(base["final_equity"]), 4),
                "delta_cagr": round(cagr - to_float(base["cagr"]), 6),
                "delta_mdd": round(mdd - to_float(base["max_drawdown"]), 6),
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
                "task_id": "Task1754",
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


def attribution(preentry: list[dict[str, object]], trades: list[dict[str, object]], mrows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for label, counts in [
        ("risk_budget_state", Counter(str(row["risk_budget_state"]) for row in preentry)),
        ("factor_cluster", Counter(str(row["factor_cluster"]) for row in preentry)),
    ]:
        for reason, count in counts.most_common():
            rows.append({"task_id": "Task1755", "attribution_id": f"PREATTR1755-{idx:05d}", "failure_area": label, "reason": reason, "row_count": count, "authority": AUTHORITY})
            idx += 1
    by_state: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        by_state[str(row["risk_budget_state"])].append(row)
    for state, group in sorted(by_state.items()):
        rows.append(
            {
                "task_id": "Task1755",
                "attribution_id": f"PREATTR1755-{idx:05d}",
                "failure_area": "state_pnl",
                "reason": state,
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
                    "task_id": "Task1755",
                    "attribution_id": f"PREATTR1755-{idx:05d}",
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
            "task_id": "Task1766",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "cagr_30pct_met_by_any": "1" if any(row["target_cagr_30pct_met"] == "1" for row in mrows) else "0",
            "mdd_minus30pct_met_by_any": "1" if any(row["target_mdd_minus30pct_met"] == "1" for row in mrows) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "preentry_risk_budget_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1767",
            "verdict": "preentry_risk_budget_implemented_diagnostic_only",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit whether pre-entry caps are too broad and add true factor exposure estimates before further capital promotion",
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
        "# Task1748-1767 Pre-Entry Risk Budget",
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
    for row in attr[:30]:
        lines.append(f"- `{row['failure_area']}`: {row.get('reason', row.get('policy_variant_id', ''))} count={row.get('row_count','')} pnl={row.get('pnl_sum','')} cagr={row.get('cagr','')} mdd={row.get('max_drawdown','')}")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Risk budget is assigned before entry.",
            "2. The replay keeps Task1698 trade outcomes but changes initial sizing/no-entry only.",
            "3. This tests whether firm-style pre-trade risk planning is better than late reduce.",
            "4. The result remains diagnostic and does not approve strategy.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1748_expert_review.csv`",
            "- `task1750_preentry_risk_budget_panel.csv`",
            "- `task1751_budget_action_panel.csv`",
            "- `task1752_preentry_budget_replay_trades.csv/equity`",
            "- `task1753_preentry_budget_replay_metrics.csv`",
            "- `task1754_split_oos_metrics.csv`",
            "- `task1755_failure_attribution.csv`",
            "- `task1766_acceptance_gate.csv`",
            "- `task1767_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1748_1767_preentry_risk_budget_validate.py`",
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
    experts = expert_review_rows()
    preentry = build_preentry_panel()
    actions, trades, equity = replay_budget(preentry)
    mrows = metrics(trades, equity)
    splits = split_rows(equity)
    attr = attribution(preentry, trades, mrows)
    gate, closeout = gate_closeout(mrows)
    outputs = [
        ("task1748_expert_review.csv", experts),
        ("task1750_preentry_risk_budget_panel.csv", preentry),
        ("task1751_budget_action_panel.csv", actions),
        ("task1752_preentry_budget_replay_trades.csv", trades),
        ("task1752_preentry_budget_replay_equity.csv", equity),
        ("task1753_preentry_budget_replay_metrics.csv", mrows),
        ("task1754_split_oos_metrics.csv", splits),
        ("task1755_failure_attribution.csv", attr),
        ("task1766_acceptance_gate.csv", gate),
        ("task1767_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1767_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(mrows, splits, attr, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1748_1767] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
