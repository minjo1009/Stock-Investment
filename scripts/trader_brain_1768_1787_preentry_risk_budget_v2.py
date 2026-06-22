from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1668_1687_l5_thesis_aware_action_engine as thesis_l5
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1698 = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
TASK1748 = ROOT / "data/artifacts/task_1748_1767_preentry_risk_budget"
OUT_DIR = ROOT / "data/artifacts/task_1768_1787_preentry_risk_budget_v2"
REPORT_DIR = ROOT / "docs/reports/task_1768_1787_preentry_risk_budget_v2"
REPORT = REPORT_DIR / "task_1768_1787_preentry_risk_budget_v2.md"
DECISION = REPORT_DIR / "task_1768_1787_decision.csv"

AUTHORITY = "DIAGNOSTIC_PREENTRY_RISK_BUDGET_V2_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "preentry_risk_budget_v2_top3_v1": {"source_policy": "bad_trade_gate_top3_v1", "slot_cap": 3},
    "preentry_risk_budget_v2_top5_v1": {"source_policy": "bad_trade_gate_top5_v1", "slot_cap": 5},
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


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def expert_review_rows() -> list[dict[str, object]]:
    rows = [
        ("firm_pm", "CFA risk budgeting", "move from bucket caps to risk contribution sizing", "adopt"),
        ("risk_trader", "CME pre-trade risk", "keep no-entry only for truly fragile cases; otherwise size smoothly", "adopt"),
        ("factor_quant", "AQR portfolio construction", "cluster exposure should be correlation-aware not only label-aware", "adopt"),
        ("risk_layer_pm", "BlackRock risk layers", "separate risk drivers and size by combined risk pressure", "adopt"),
        ("execution_engineer", "project harness discipline", "reuse existing trade outcomes and change only pre-entry sizing", "adopt"),
        ("governance_reviewer", "Task747 validation map", "diagnostic pass cannot approve strategy", "adopt"),
    ]
    return [
        {
            "task_id": "Task1768",
            "expert_review_id": f"PREBUDGETV2-1768-{idx:03d}",
            "expert_role": role,
            "source_anchor": source,
            "critique": critique,
            "implementation_decision": decision,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, source, critique, decision) in enumerate(rows, 1)
    ]


def prior_returns(frame: pd.DataFrame | None, decision_date: date, sessions: int = 63) -> pd.Series:
    if frame is None:
        return pd.Series(dtype=float)
    hist = frame[frame["Date"] <= decision_date].tail(sessions + 1).copy()
    if len(hist) < 10:
        return pd.Series(dtype=float)
    return hist.set_index("Date")["Close"].pct_change().dropna()


def cluster_corr_map(rows: list[dict[str, str]]) -> dict[tuple[str, str], float]:
    cache: dict[str, pd.DataFrame | None] = {}
    result: dict[tuple[str, str], float] = {}
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["policy_variant_id"], row["decision_asof_ts"], row["factor_cluster"])].append(row)
    for (_policy, _decision, _cluster), items in groups.items():
        if len(items) < 2:
            for item in items:
                result[(item["policy_variant_id"], item["trade_spec_id"])] = 0.0
            continue
        decision_date = replay.parse_ts(items[0]["decision_asof_ts"]).date()
        series_by_symbol: dict[str, pd.Series] = {}
        for item in items:
            frame = replay.load_price(item["symbol"], cache)
            series = prior_returns(frame, decision_date)
            if not series.empty:
                series_by_symbol[item["trade_spec_id"]] = series
        for item in items:
            spec_id = item["trade_spec_id"]
            corrs: list[float] = []
            base = series_by_symbol.get(spec_id)
            if base is not None:
                for other_id, other in series_by_symbol.items():
                    if other_id == spec_id:
                        continue
                    joined = pd.concat([base, other], axis=1, join="inner").dropna()
                    if len(joined) >= 10:
                        corr = float(joined.iloc[:, 0].corr(joined.iloc[:, 1]))
                        if pd.notna(corr):
                            corrs.append(corr)
            result[(item["policy_variant_id"], spec_id)] = round(max(corrs) if corrs else 0.0, 6)
    return result


def risk_budget_state(multiplier: float, no_entry: bool) -> str:
    if no_entry:
        return "no_entry"
    if multiplier >= 0.9:
        return "full_size_continuous"
    if multiplier >= 0.7:
        return "soft_cap_continuous"
    if multiplier >= 0.45:
        return "half_size_continuous"
    return "quarter_size_continuous"


def build_v2_panel() -> list[dict[str, object]]:
    base = read_csv(TASK1748 / "task1750_preentry_risk_budget_panel.csv")
    corr = cluster_corr_map(base)
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(base, 1):
        risk_points = to_float(row["preentry_risk_points"])
        payoff = to_float(row["payoff_quality_score"])
        cluster_count = to_float(row["cluster_count_same_decision"])
        cluster_corr = corr.get((row["policy_variant_id"], row["trade_spec_id"]), 0.0)
        payoff_credit = clamp((payoff - 75.0) / 100.0, -0.10, 0.28)
        risk_pressure = 0.075 * risk_points
        cluster_pressure = 0.0
        if cluster_count >= 2 and row["factor_cluster"] not in {"defensive_quality", "mixed_other"}:
            cluster_pressure += 0.07
        if cluster_corr >= 0.55:
            cluster_pressure += 0.08
        elif cluster_corr >= 0.35:
            cluster_pressure += 0.04
        fragility_pressure = 0.07 if row["fragility_risk"] == "1" else 0.0
        air_pocket_pressure = 0.06 if row["air_pocket_risk"] == "1" else 0.0
        liquidity_pressure = 0.05 if row["liquidity_risk"] == "1" else 0.0
        multiplier = 1.0 + payoff_credit - risk_pressure - cluster_pressure - fragility_pressure - air_pocket_pressure - liquidity_pressure
        if row["selection_reason"] != "baseline_preserved":
            multiplier = min(multiplier, 0.40)
        no_entry = risk_points >= 6 and payoff < 82 and row["selection_reason"] == "baseline_preserved"
        if no_entry:
            multiplier = 0.0
        elif multiplier < 0.20:
            multiplier = 0.20
        multiplier = round(clamp(multiplier, 0.0, 1.05), 4)
        out = dict(row)
        out.update(
            {
                "task_id": "Task1770",
                "preentry_v2_id": f"PREBUDGETV2-1770-{idx:07d}",
                "cluster_corr_63d": cluster_corr,
                "payoff_credit": round(payoff_credit, 6),
                "risk_pressure": round(risk_pressure, 6),
                "cluster_pressure": round(cluster_pressure, 6),
                "fragility_pressure": round(fragility_pressure, 6),
                "air_pocket_pressure": round(air_pocket_pressure, 6),
                "liquidity_pressure": round(liquidity_pressure, 6),
                "risk_budget_state_v2": risk_budget_state(multiplier, no_entry),
                "risk_budget_multiplier_v2": multiplier,
                "assignment_uses_future_outcome": "0",
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
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    actions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    action_idx = 1
    trade_idx = 1
    for policy_id, policy in POLICIES.items():
        source_policy = policy["source_policy"]
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in groups if key[0] == source_policy}):
            items = sorted(groups[(source_policy, decision_ts)], key=lambda row: to_float(row["risk_budget_multiplier_v2"]), reverse=True)
            base_alloc = capital / int(policy["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            for selected in items:
                source = baseline.get((source_policy, str(selected["trade_spec_id"])))
                if not source:
                    continue
                cap = to_float(selected["risk_budget_multiplier_v2"])
                action = "no_entry" if cap <= 0 else "enter_with_continuous_preentry_budget"
                actions.append(
                    {
                        "task_id": "Task1771",
                        "budget_action_id": f"PREBUDGETV2ACTION-1771-{action_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "risk_budget_state_v2": selected["risk_budget_state_v2"],
                        "risk_budget_multiplier_v2": cap,
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
                        "task_id": "Task1772",
                        "trade_row_id": f"PREBUDGETV2TRADE-1772-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "risk_budget_state_v2": selected["risk_budget_state_v2"],
                        "risk_budget_multiplier_v2": cap,
                        "cluster_corr_63d": selected["cluster_corr_63d"],
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
                    "task_id": "Task1772",
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
    base = {row["policy_variant_id"]: row for row in read_csv(TASK1748 / "task1753_preentry_budget_replay_metrics.csv")}
    base_map = {
        "preentry_risk_budget_v2_top3_v1": "preentry_risk_budget_top3_v1",
        "preentry_risk_budget_v2_top5_v1": "preentry_risk_budget_top5_v1",
    }
    tr_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    eq_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        tr_groups[str(row["policy_variant_id"])].append(row)
    for row in equity:
        eq_groups[str(row["policy_variant_id"])].append(row)
    out: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(eq_groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        tr_rows = tr_groups[policy_id]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end_dates = [parse_date(row.get("actual_exit_date")) for row in tr_rows]
        end = max([d for d in end_dates if d is not None] or [start])
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        b = base[base_map[policy_id]]
        out.append(
            {
                "task_id": "Task1773",
                "policy_variant_id": policy_id,
                "baseline_policy_variant_id": base_map[policy_id],
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "baseline_final_equity": b["final_equity"],
                "baseline_cagr": b["cagr"],
                "baseline_max_drawdown": b["max_drawdown"],
                "delta_final_equity": round(final - to_float(b["final_equity"]), 4),
                "delta_cagr": round(cagr - to_float(b["cagr"]), 6),
                "delta_mdd": round(mdd - to_float(b["max_drawdown"]), 6),
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
    return out


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
                "task_id": "Task1774",
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
    for label, counts in [
        ("risk_budget_state_v2", Counter(str(row["risk_budget_state_v2"]) for row in panel)),
        ("factor_cluster", Counter(str(row["factor_cluster"]) for row in panel)),
    ]:
        for reason, count in counts.most_common():
            rows.append({"task_id": "Task1775", "attribution_id": f"PREBUDGETV2ATTR-1775-{idx:05d}", "failure_area": label, "reason": reason, "row_count": count, "authority": AUTHORITY})
            idx += 1
    by_state: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        by_state[str(row["risk_budget_state_v2"])].append(row)
    for state, group in sorted(by_state.items()):
        rows.append(
            {
                "task_id": "Task1775",
                "attribution_id": f"PREBUDGETV2ATTR-1775-{idx:05d}",
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
                    "task_id": "Task1775",
                    "attribution_id": f"PREBUDGETV2ATTR-1775-{idx:05d}",
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
            "task_id": "Task1786",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "cagr_30pct_met_by_any": "1" if any(row["target_cagr_30pct_met"] == "1" for row in mrows) else "0",
            "mdd_minus30pct_met_by_any": "1" if any(row["target_mdd_minus30pct_met"] == "1" for row in mrows) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "preentry_risk_budget_v2_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1787",
            "verdict": "preentry_risk_budget_v2_implemented_diagnostic_only",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit v2 multiplier distribution and add true factor beta estimates before any acceptance claim",
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
        "# Task1768-1787 Pre-Entry Risk Budget V2",
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
    for row in attr[:28]:
        lines.append(f"- `{row['failure_area']}`: {row.get('reason', row.get('policy_variant_id', ''))} count={row.get('row_count','')} pnl={row.get('pnl_sum','')} cagr={row.get('cagr','')} mdd={row.get('max_drawdown','')}")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. V2 moves from coarse buckets to continuous pre-entry sizing.",
            "2. It adds 63-day same-cluster correlation pressure.",
            "3. It tries to restore return while keeping the MDD gain from Task1748.",
            "4. The result remains diagnostic and does not approve strategy.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1768_expert_review.csv`",
            "- `task1770_preentry_risk_budget_v2_panel.csv`",
            "- `task1771_budget_action_panel.csv`",
            "- `task1772_preentry_budget_v2_replay_trades.csv/equity`",
            "- `task1773_preentry_budget_v2_replay_metrics.csv`",
            "- `task1774_split_oos_metrics.csv`",
            "- `task1775_failure_attribution.csv`",
            "- `task1786_acceptance_gate.csv`",
            "- `task1787_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1768_1787_preentry_risk_budget_v2_validate.py`",
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
    panel = build_v2_panel()
    actions, trades, equity = replay_budget(panel)
    mrows = metrics(trades, equity)
    splits = split_rows(equity)
    attr = attribution(panel, trades, mrows)
    gate, closeout = gate_closeout(mrows)
    outputs = [
        ("task1768_expert_review.csv", experts),
        ("task1770_preentry_risk_budget_v2_panel.csv", panel),
        ("task1771_budget_action_panel.csv", actions),
        ("task1772_preentry_budget_v2_replay_trades.csv", trades),
        ("task1772_preentry_budget_v2_replay_equity.csv", equity),
        ("task1773_preentry_budget_v2_replay_metrics.csv", mrows),
        ("task1774_split_oos_metrics.csv", splits),
        ("task1775_failure_attribution.csv", attr),
        ("task1786_acceptance_gate.csv", gate),
        ("task1787_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1787_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(mrows, splits, attr, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1768_1787] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
