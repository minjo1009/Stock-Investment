from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1318 = ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors"
OUT_DIR = ROOT / "data/artifacts/task_1338_1357_full_candidate_replacement_replay"
REPORT_DIR = ROOT / "docs/reports/task_1338_1357_full_candidate_replacement_replay"

AUTHORITY = "DIAGNOSTIC_FULL_CANDIDATE_REPLACEMENT_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
SLOT_CAPS = [3, 5, 10]

COMPOSITE_BASE = {
    "validated_growth_multisource_confirmed": 100.0,
    "revenue_validation_market_confirmed": 72.0,
    "management_narrative_market_confirmed": 55.0,
    "multisource_incomplete_or_watch": 22.0,
    "hard_survival_review_required": -55.0,
}

MANAGEMENT_SCORE = {
    "specific_management_narrative": 18.0,
    "limited_management_narrative": 7.0,
    "generic_management_narrative": 1.0,
    "promotional_low_specificity": -8.0,
    "missing_or_no_ir_exhibit_signal": 0.0,
}

CONTRACT_SCORE = {
    "validated_contract_or_order": 22.0,
    "contract_watch_needs_materiality": 8.0,
    "generic_contract_keyword": 1.0,
    "weak_nonbinding_or_pilot": -16.0,
    "missing_or_no_contract_signal": 0.0,
}

SURVIVAL_SCORE = {
    "no_terminal_distress_evidence_found": 5.0,
    "watch_distress": -8.0,
    "terminal_distress": -70.0,
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
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


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


def policy_catalog() -> list[dict[str, object]]:
    rows = []
    for slot_cap in SLOT_CAPS:
        rows.append(
            {
                "task_id": "Task1338",
                "policy_variant_id": f"full_candidate_l2l3_replace_top{slot_cap}_v1",
                "slot_cap": slot_cap,
                "selection_scope": "same_decision_month_top50_candidate_cohort",
                "rank_inputs": "full_candidate_L2_composite;L1_states;L3_evidence_counts;original_candidate_rank",
                "forbidden_inputs": "future_return;realized_return;pnl;exit_price;post_entry_price_path;outcome_label",
                "position_sizing_rule": "equal_weight_within_selected_slots",
                "selection_promoted": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def score_candidate(l2: dict[str, str], l1: dict[str, str], l3_edges: list[dict[str, str]], readiness: dict[str, str]) -> dict[str, object]:
    composite = l2["full_candidate_composite_interpretation"]
    base = COMPOSITE_BASE.get(composite, 0.0)
    management = MANAGEMENT_SCORE.get(l2["management_narrative_state"], 0.0)
    contract = CONTRACT_SCORE.get(l2["contract_revenue_state"], 0.0)
    survival = SURVIVAL_SCORE.get(l2["sec_survival_state"], 0.0)
    evidence_edge_count = sum(1 for edge in l3_edges if edge.get("evidence_id"))
    reinforce_count = sum(1 for edge in l3_edges if edge.get("relation_primitive") in {"reinforces", "confirms"})
    condition_count = sum(1 for edge in l3_edges if edge.get("relation_primitive") == "conditions")
    invalidation_count = sum(1 for edge in l3_edges if edge.get("relation_primitive") == "invalidates")
    rank_bonus = max(0.0, 51.0 - to_float(l2["candidate_rank"])) * 0.35
    readiness_bonus = 5.0 if readiness["backtest_readiness_state"] == "full_candidate_shadow_ready_no_analyst" else 0.0
    market_bonus = 4.0 if l2["market_acceptance_state"] == "price_gate_attached" else 0.0
    evidence_bonus = min(12.0, evidence_edge_count * 1.5 + reinforce_count * 2.0 + condition_count * 0.5)
    score = base + management + contract + survival + rank_bonus + readiness_bonus + market_bonus + evidence_bonus - invalidation_count * 25.0
    route = "eligible"
    if composite == "hard_survival_review_required" or invalidation_count:
        route = "survival_capped_low_priority"
    elif composite == "multisource_incomplete_or_watch" and evidence_edge_count == 0:
        route = "incomplete_low_priority"
    elif composite == "validated_growth_multisource_confirmed":
        route = "validated_growth_priority"
    elif composite == "revenue_validation_market_confirmed":
        route = "revenue_validation_priority"
    return {
        "replacement_score": round(score, 6),
        "replacement_route": route,
        "evidence_edge_count": evidence_edge_count,
        "reinforce_count": reinforce_count,
        "condition_count": condition_count,
        "invalidation_count": invalidation_count,
        "rank_bonus": round(rank_bonus, 6),
    }


def build_rank_panel() -> list[dict[str, object]]:
    l1 = {row["candidate_source_id"]: row for row in read_csv(TASK1318 / "task1324_candidate_l1_source_bindings.csv")}
    l2_rows = read_csv(TASK1318 / "task1325_candidate_l2_interpretation.csv")
    readiness = {row["candidate_source_id"]: row for row in read_csv(TASK1318 / "task1327_full_candidate_readiness_panel.csv")}
    l3_by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(TASK1318 / "task1326_candidate_l3_evidence_edges.csv"):
        l3_by_candidate[row["candidate_source_id"]].append(row)

    rows = []
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in l2_rows:
        cid = row["candidate_source_id"]
        score = score_candidate(row, l1[cid], l3_by_candidate[cid], readiness[cid])
        out = {
            "task_id": "Task1339",
            "candidate_source_id": cid,
            "trade_spec_id": row["trade_spec_id"],
            "symbol": row["symbol"],
            "decision_asof_ts": row["decision_asof_ts"],
            "candidate_rank": row["candidate_rank"],
            "derived_theme": row["derived_theme"],
            "full_candidate_composite_interpretation": row["full_candidate_composite_interpretation"],
            "sec_survival_state": row["sec_survival_state"],
            "management_narrative_state": row["management_narrative_state"],
            "contract_revenue_state": row["contract_revenue_state"],
            "market_acceptance_state": row["market_acceptance_state"],
            **score,
            "assignment_uses_future_outcome": "0",
            "selection_promoted": "0",
            "authority": AUTHORITY,
        }
        by_decision[row["decision_asof_ts"]].append(out)
    for decision_ts, items in sorted(by_decision.items()):
        ranked = sorted(
            items,
            key=lambda item: (
                -to_float(item["replacement_score"]),
                int(str(item["candidate_rank"])),
                str(item["symbol"]),
                str(item["trade_spec_id"]),
            ),
        )
        for rank, item in enumerate(ranked, 1):
            rows.append({**item, "replacement_rank_within_decision": rank})
    return rows


def build_policy_specs(rank_panel: list[dict[str, object]]) -> list[dict[str, object]]:
    trade_specs = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}
    prices = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1204_price_gate.csv")}
    specs = []
    for slot_cap in SLOT_CAPS:
        variant = f"full_candidate_l2l3_replace_top{slot_cap}_v1"
        for row in rank_panel:
            selected = int(row["replacement_rank_within_decision"]) <= slot_cap
            spec = trade_specs[str(row["trade_spec_id"])]
            price = prices[str(row["trade_spec_id"])]
            specs.append(
                {
                    "task_id": "Task1340",
                    "policy_spec_id": f"FCRSPEC1340-{len(specs)+1:07d}",
                    "policy_variant_id": variant,
                    "slot_cap": slot_cap,
                    "candidate_source_id": row["candidate_source_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "symbol": row["symbol"],
                    "candidate_rank": row["candidate_rank"],
                    "replacement_rank_within_decision": row["replacement_rank_within_decision"],
                    "derived_theme": row["derived_theme"],
                    "full_candidate_composite_interpretation": row["full_candidate_composite_interpretation"],
                    "replacement_score": row["replacement_score"],
                    "replacement_route": row["replacement_route"],
                    "selected_for_replay": "1" if selected else "0",
                    "entry_date": price["entry_date"],
                    "entry_price": price["entry_price"],
                    "exit_date": price["exit_date"],
                    "exit_price": price["exit_price"],
                    "price_gate_pass": price["price_gate_pass"],
                    "side": spec["side"],
                    "position_sizing_rule": "equal_weight_within_selected_slots",
                    "assignment_uses_future_outcome": "0",
                    "selection_promoted": "0",
                    "authority": AUTHORITY,
                }
            )
    return specs


def run_replay(policy_specs: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    specs_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for spec in policy_specs:
        if spec["selected_for_replay"] == "1" and spec["price_gate_pass"] == "1":
            specs_by_policy[str(spec["policy_variant_id"])].append(spec)
    trades = []
    equity = []
    for policy_id, specs in sorted(specs_by_policy.items()):
        by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
        for spec in specs:
            by_decision[str(spec["decision_asof_ts"])].append(spec)
        capital = INITIAL_CAPITAL
        for decision_ts, items in sorted(by_decision.items()):
            selected = sorted(items, key=lambda row: int(str(row["replacement_rank_within_decision"])))
            per_position = capital / len(selected) if selected else 0.0
            period_pnl = 0.0
            new_capital = 0.0
            for item in selected:
                entry = to_float(item["entry_price"])
                exit_ = to_float(item["exit_price"])
                gross_return = exit_ / entry - 1.0 if entry > 0 else 0.0
                net_return = gross_return - ROUND_TRIP_COST_BPS / 10000.0
                pnl = per_position * net_return
                period_pnl += pnl
                new_capital += per_position + pnl
                trades.append(
                    {
                        "task_id": "Task1341",
                        "trade_id": f"FCRTRADE1341-{len(trades)+1:07d}",
                        **item,
                        "capital_allocated": round(per_position, 4),
                        "gross_return": round(gross_return, 8),
                        "net_return": round(net_return, 8),
                        "pnl": round(pnl, 4),
                        "exit_uses_post_entry_price_path": "1",
                        "authority": AUTHORITY,
                    }
                )
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1342",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_return": round(capital / (capital - period_pnl) - 1.0, 8) if capital - period_pnl > 0 else 0.0,
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(selected),
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base_metrics = read_csv(TASK1201 / "task1207_replay_metrics.csv")
    base_by_variant = {row["policy_variant_id"]: row for row in base_metrics}
    base_slot5 = base_by_variant["l0_l3_slot5_v1"]
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    rows = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        slot_cap = policy_id.split("top")[-1].split("_")[0]
        baseline = base_by_variant.get(f"l0_l3_slot{slot_cap}_v1", base_slot5)
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = datetime.fromisoformat(str(eq_rows[0]["decision_asof_ts"]).replace("Z", "+00:00")).date()
        end = max(datetime.fromisoformat(str(row["exit_date"])).date() for row in tr_rows)
        cagr_value = cagr(INITIAL_CAPITAL, final, start, end)
        mdd_value = max_drawdown(values)
        rows.append(
            {
                "task_id": "Task1343",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr_value, 6),
                "max_drawdown": round(mdd_value, 6),
                "trade_count": len(tr_rows),
                "baseline_slot_variant": baseline["policy_variant_id"],
                "baseline_final_equity": baseline["final_equity"],
                "baseline_delta": round(final - to_float(baseline["final_equity"]), 4),
                "beats_baseline_slot": "1" if final > to_float(baseline["final_equity"]) else "0",
                "benchmark_symbol": base_slot5["benchmark_symbol"],
                "benchmark_final_equity": base_slot5["benchmark_final_equity"],
                "benchmark_cagr": base_slot5["benchmark_cagr"],
                "beats_benchmark": "1" if final > to_float(base_slot5["benchmark_final_equity"]) else "0",
                "target_cagr_30pct_met": "1" if cagr_value >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd_value >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_attribution(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        groups[(str(row["policy_variant_id"]), str(row["full_candidate_composite_interpretation"]))].append(row)
    rows = []
    for (policy, interpretation), items in sorted(groups.items()):
        pnl = sum(to_float(row["pnl"]) for row in items)
        avg_return = sum(to_float(row["net_return"]) for row in items) / len(items)
        rows.append(
            {
                "task_id": "Task1344",
                "policy_variant_id": policy,
                "full_candidate_composite_interpretation": interpretation,
                "trade_count": len(items),
                "pnl": round(pnl, 4),
                "avg_net_return": round(avg_return, 8),
                "authority": AUTHORITY,
            }
        )
    return rows


def build_replacement_audit(policy_specs: list[dict[str, object]]) -> list[dict[str, object]]:
    old_slot5 = {row["decision_asof_ts"]: [] for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}
    old_selected = [row for row in read_csv(TASK1201 / "task1205_slot_selections.csv") if row["policy_variant_id"] == "l0_l3_slot5_v1"]
    for row in old_selected:
        old_slot5[row["decision_asof_ts"]].append(row["trade_spec_id"])
    rows = []
    for slot_cap in SLOT_CAPS:
        variant = f"full_candidate_l2l3_replace_top{slot_cap}_v1"
        selected = [row for row in policy_specs if row["policy_variant_id"] == variant and row["selected_for_replay"] == "1"]
        by_decision: dict[str, list[str]] = defaultdict(list)
        for row in selected:
            by_decision[str(row["decision_asof_ts"])].append(str(row["trade_spec_id"]))
        for decision_ts, new_ids in sorted(by_decision.items()):
            old_ids = set(old_slot5.get(decision_ts, [])[:slot_cap])
            new_set = set(new_ids)
            rows.append(
                {
                    "task_id": "Task1345",
                    "policy_variant_id": variant,
                    "decision_asof_ts": decision_ts,
                    "slot_cap": slot_cap,
                    "old_selected_count": len(old_ids),
                    "new_selected_count": len(new_set),
                    "overlap_count": len(old_ids & new_set),
                    "replaced_count": len(new_set - old_ids),
                    "dropped_count": len(old_ids - new_set),
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def write_report(metrics: list[dict[str, object]], gate: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    report = f"""# Task1338-1357 Full Candidate Replacement Replay

## Decision Summary

- Verdict: `full_candidate_replacement_replay_executed_not_accepted`.
- Best policy: `{best['policy_variant_id']}`.
- Best final equity: {best['final_equity']}.
- Best CAGR: {best['cagr']}.
- Best MDD: {best['max_drawdown']}.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: full-candidate L2/L3 source judgment now selects top 3/5/10 replacement portfolios inside each monthly cohort.
- Next action: diagnose replacement winners/losers before changing thresholds or adding dynamic exits.

## Quant Expert Report

Data source and readiness:

- Inputs are Task1318-1337 full-candidate source extractor outputs and Task1201 trade specs/price gates.
- Selection uses only same-month candidate cohort rows.
- No future PnL, realized return, exit price, or outcome labels are used for assignment.

Exact join keys:

- `candidate_source_id`
- `trade_spec_id`
- `decision_asof_ts`
- `symbol`

Policy metrics:

| Policy | Final | CAGR | MDD | Beats Slot Baseline | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in sorted(metrics, key=lambda item: str(item["policy_variant_id"])):
        report += (
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | "
            f"{row['max_drawdown']} | {row['beats_baseline_slot']} | {row['beats_benchmark']} | "
            f"{row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |\n"
        )
    report += f"""
Leakage audit:

- L4 replacement scores use L2 composite interpretation, L1 source states, L3 evidence-edge counts, readiness state, and original candidate rank.
- L5 replay uses entry and exit prices only after selection.
- `assignment_uses_future_outcome` remains 0 in ranking and policy specs.

Remaining blockers:

- Analyst PIT source remains absent.
- Policy/news affected-entity extraction remains incomplete for all candidates.
- Dynamic exit and post-entry source receipt are not implemented in this replay.

## No-Background Decision-Maker Report

This is the first replay where the brain can actually replace weak candidates with stronger candidates from the same month.

It is still diagnostic.

The target was CAGR 30%+ and MDD around -30%.

## Artifact Manifest

- `task1338_policy_catalog.csv`
- `task1339_l4_replacement_rank_panel.csv`
- `task1340_l5_replacement_policy_specs.csv`
- `task1341_replay_trades.csv`
- `task1342_replay_equity.csv`
- `task1343_replay_metrics.csv`
- `task1344_interpretation_attribution.csv`
- `task1345_replacement_audit.csv`
- `task1346_acceptance_gate.csv`
- `task1357_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1338_1357_full_candidate_replacement_replay_validate.py`
- `python -m unittest tests.test_trader_brain_1338_1357_full_candidate_replacement_replay`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1338_1357_full_candidate_replacement_replay.md").write_text(report, encoding="utf-8")
    write_csv(REPORT_DIR / "task_1338_1357_decision.csv", [gate])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    policy = policy_catalog()
    rank_panel = build_rank_panel()
    policy_specs = build_policy_specs(rank_panel)
    trades, equity = run_replay(policy_specs)
    metrics = build_metrics(trades, equity)
    attribution = build_attribution(trades)
    replacement_audit = build_replacement_audit(policy_specs)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gate = {
        "task_id": "Task1346",
        "best_policy_variant_id": best["policy_variant_id"],
        "best_final_equity": best["final_equity"],
        "best_cagr": best["cagr"],
        "best_max_drawdown": best["max_drawdown"],
        "target_cagr_30pct_met": best["target_cagr_30pct_met"],
        "target_mdd_minus30pct_met": best["target_mdd_minus30pct_met"],
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "decision": "diagnostic_replay_not_accepted",
        "authority": AUTHORITY,
    }
    closeout = {
        "task_id": "Task1357",
        "verdict": "full_candidate_replacement_replay_executed_not_accepted",
        **gate,
        "trade_rows": len(trades),
        "equity_rows": len(equity),
        "next_action": "diagnose_replacement_winners_losers_and_add_dynamic_exit_sources",
    }
    write_csv(OUT_DIR / "task1338_policy_catalog.csv", policy)
    write_csv(OUT_DIR / "task1339_l4_replacement_rank_panel.csv", rank_panel)
    write_csv(OUT_DIR / "task1340_l5_replacement_policy_specs.csv", policy_specs)
    write_csv(OUT_DIR / "task1341_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1342_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1343_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1344_interpretation_attribution.csv", attribution)
    write_csv(OUT_DIR / "task1345_replacement_audit.csv", replacement_audit)
    write_csv(OUT_DIR / "task1346_acceptance_gate.csv", [gate])
    write_csv(OUT_DIR / "task1357_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1357_closeout.json", closeout)
    write_report(metrics, gate)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(gate, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
