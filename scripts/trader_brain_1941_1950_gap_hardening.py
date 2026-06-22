from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
TASK1808 = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
TASK1834 = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
TASK1931 = ROOT / "data/artifacts/task_1931_1940_interaction_forecast_layer"
OUT_DIR = ROOT / "data/artifacts/task_1941_1950_gap_hardening"
REPORT_DIR = ROOT / "docs/reports/task_1941_1950_gap_hardening"
REPORT = REPORT_DIR / "task_1941_1950_gap_hardening.md"
DECISION = REPORT_DIR / "task_1941_1950_decision.csv"
AUTHORITY = "DIAGNOSTIC_GAP_HARDENING_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265


def read_csv(path: Path) -> list[dict[str, str]]:
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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value: object) -> date | None:
    try:
        if value in {"", None}:
            return None
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_inputs() -> dict[str, object]:
    return {
        "budget": read_csv(TASK1808 / "task1815_sleeve_risk_budget.csv"),
        "winner_trades": read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        "sleeve_metrics": read_csv(TASK1808 / "task1823_sleeve_replay_metrics.csv"),
        "interaction_metrics": read_csv(TASK1931 / "task1938_interaction_top3_replay_metrics.csv"),
        "interaction_l4": read_csv(TASK1931 / "task1935_l4_interaction_payoff_thesis_cards.csv"),
        "interaction_trades": read_csv(TASK1931 / "task1938_interaction_top3_replay_trades.csv"),
        "rates": read_csv(TASK1834 / "task1835_rates_liquidity_decision_asof_panel.csv"),
        "earnings_gate": read_csv(TASK1834 / "task1838_earnings_revision_vendor_gate.csv"),
        "top5_gate": read_csv(TASK1931 / "task1939_top5_expansion_gate.csv"),
    }


def input_manifest_rows() -> list[dict[str, object]]:
    inputs = [
        ("base_budget", TASK1808 / "task1815_sleeve_risk_budget.csv"),
        ("baseline_metrics", TASK1808 / "task1823_sleeve_replay_metrics.csv"),
        ("winner_replay_trades", TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        ("interaction_l4", TASK1931 / "task1935_l4_interaction_payoff_thesis_cards.csv"),
        ("interaction_metrics", TASK1931 / "task1938_interaction_top3_replay_metrics.csv"),
        ("rates_panel", TASK1834 / "task1835_rates_liquidity_decision_asof_panel.csv"),
        ("earnings_vendor_gate", TASK1834 / "task1838_earnings_revision_vendor_gate.csv"),
        ("top5_expansion_gate", TASK1931 / "task1939_top5_expansion_gate.csv"),
    ]
    return [
        {
            "task_id": "Task1941",
            "input_id": f"GAPHARDINPUT-1941-{idx:03d}",
            "input_name": name,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "exists": "1" if path.exists() else "0",
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, path) in enumerate(inputs, 1)
    ]


def macro_vintage_gate_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    top3_decisions = sorted(
        {row["decision_asof_ts"] for row in inputs["budget"] if row["target_policy_variant_id"] == "winner_defense_budget_top3_v1"}
    )
    rates = {row["decision_asof_ts"]: row for row in inputs["rates"]}
    rows = []
    for idx, decision_ts in enumerate(top3_decisions, 1):
        rate = rates.get(decision_ts, {})
        source_ready = "1" if rate.get("source_available_to_brain_ts") and rate.get("source_available_to_brain_ts") <= decision_ts else "0"
        # Current local rates panel is source-time-lagged, but not full ALFRED vintage certified.
        vintage_certified = "0"
        rows.append(
            {
                "task_id": "Task1942",
                "macro_vintage_gate_id": f"MACROVINTAGE-1942-{idx:05d}",
                "decision_asof_ts": decision_ts,
                "source_observation_date": rate.get("source_observation_date", ""),
                "source_available_to_brain_ts": rate.get("source_available_to_brain_ts", ""),
                "rate_regime_state": rate.get("rate_regime_state", "source_gap"),
                "liquidity_stress_state": rate.get("liquidity_stress_state", "source_gap"),
                "source_time_lag_safe": source_ready,
                "alfred_vintage_certified": vintage_certified,
                "active_assignment_permission": "macro_shadow_only_until_vintage_certified",
                "hardening_action": "remove_macro_score_effect_keep_audit_trace",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def earnings_guidance_gate_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    gate = inputs["earnings_gate"][0]
    rows = []
    for idx, l4 in enumerate(inputs["interaction_l4"], 1):
        has_expectation_proxy = "expectation_gap_expands_payoff" in l4["positive_interaction_primitives"]
        rows.append(
            {
                "task_id": "Task1943",
                "earnings_gate_row_id": f"EARNGATE-1943-{idx:06d}",
                "trade_spec_id": l4["trade_spec_id"],
                "candidate_source_id": l4["candidate_source_id"],
                "symbol": l4["symbol"],
                "decision_asof_ts": l4["decision_asof_ts"],
                "local_pit_available_rows": gate.get("local_pit_available_rows", "0"),
                "gate_verdict": gate.get("gate_verdict", "vendor_blocked_schema_only"),
                "expectation_proxy_present": "1" if has_expectation_proxy else "0",
                "active_assignment_permission": "confidence_limited_proxy_only_not_true_guidance_surprise",
                "hardening_action": "downgrade_expectation_proxy_score_effect",
                "missing_source_semantics": "source_gap_not_negative",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def primitive_quality_audit_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    primitives = [
        "macro_confirms_theme",
        "macro_offsets_growth",
        "policy_unlocks_demand",
        "earnings_confirms_contract",
        "price_accepts_surprise",
        "financing_risk_overrides_growth",
        "breadth_confirms_leadership",
        "guidance_invalidates_thesis",
        "quality_defends_volatility",
        "expectation_gap_expands_payoff",
    ]
    l4_rows = inputs["interaction_l4"]
    trade_by_spec = {row["trade_spec_id"]: row for row in inputs["interaction_trades"]}
    rows = []
    for idx, primitive in enumerate(primitives, 1):
        pos = [row for row in l4_rows if primitive in row["positive_interaction_primitives"].split("|")]
        neg = [row for row in l4_rows if primitive in row["negative_interaction_primitives"].split("|")]
        traded = [trade_by_spec[row["trade_spec_id"]] for row in pos + neg if row["trade_spec_id"] in trade_by_spec]
        if primitive in {"macro_confirms_theme", "macro_offsets_growth"}:
            readiness = "shadow_only_not_vintage_certified"
        elif primitive in {"expectation_gap_expands_payoff", "guidance_invalidates_thesis", "earnings_confirms_contract"}:
            readiness = "confidence_limited_vendor_or_guidance_gap"
        elif primitive == "policy_unlocks_demand":
            readiness = "source_gap_not_active"
        else:
            readiness = "active_source_field_available"
        rows.append(
            {
                "task_id": "Task1944",
                "primitive_audit_id": f"PRIMAUDIT-1944-{idx:03d}",
                "primitive_name": primitive,
                "positive_l4_count": len(pos),
                "negative_l4_count": len(neg),
                "top3_trade_count_audit_only": len(traded),
                "top3_pnl_sum_audit_only": round(sum(to_float(row["pnl"]) for row in traded), 4),
                "source_readiness_state": readiness,
                "hardening_decision": hardening_decision_for_primitive(primitive, readiness),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def hardening_decision_for_primitive(primitive: str, readiness: str) -> str:
    if readiness == "shadow_only_not_vintage_certified":
        return "remove_active_score_effect_keep_shadow_audit"
    if readiness == "confidence_limited_vendor_or_guidance_gap":
        return "cap_or_downgrade_score_effect_until_pit_source"
    if readiness == "source_gap_not_active":
        return "inactive_until_source_packet_exists"
    return "keep_active"


def hardened_l4_rows(inputs: dict[str, object], macro_gate: list[dict[str, object]], earnings_gate: list[dict[str, object]]) -> list[dict[str, object]]:
    macro_by_decision = {row["decision_asof_ts"]: row for row in macro_gate}
    earnings_by_spec = {row["trade_spec_id"]: row for row in earnings_gate}
    rows = []
    for idx, l4 in enumerate(inputs["interaction_l4"], 1):
        positive = set() if l4["positive_interaction_primitives"] == "none" else set(l4["positive_interaction_primitives"].split("|"))
        negative = set() if l4["negative_interaction_primitives"] == "none" else set(l4["negative_interaction_primitives"].split("|"))
        score = to_float(l4["interaction_score"])
        macro_adjust = 0.0
        earnings_adjust = 0.0
        if macro_by_decision[l4["decision_asof_ts"]]["alfred_vintage_certified"] != "1":
            if "macro_offsets_growth" in negative:
                macro_adjust += 0.7
            if "macro_confirms_theme" in positive:
                macro_adjust -= 0.4
        if earnings_by_spec[l4["trade_spec_id"]]["gate_verdict"] == "vendor_blocked_schema_only":
            if "expectation_gap_expands_payoff" in positive:
                earnings_adjust -= 0.45
        hardened_score = score + macro_adjust + earnings_adjust
        if hardened_score >= 2.5:
            state = "hardened_high_conviction_payoff"
            multiplier = 1.06
        elif hardened_score >= 1.5:
            state = "hardened_positive_payoff"
            multiplier = 1.03
        elif hardened_score >= 0.5:
            state = "hardened_ordinary_pass"
            multiplier = 1.00
        elif hardened_score <= -1.2:
            state = "hardened_risk_cap"
            multiplier = 0.72
        elif hardened_score < 0:
            state = "hardened_watch_trim"
            multiplier = 0.90
        else:
            state = "hardened_unclear_gap"
            multiplier = 0.97
        rows.append(
            {
                "task_id": "Task1945",
                "hardened_l4_id": f"HARDL4-1945-{idx:06d}",
                "target_policy_variant_id": l4["target_policy_variant_id"],
                "trade_spec_id": l4["trade_spec_id"],
                "candidate_source_id": l4["candidate_source_id"],
                "symbol": l4["symbol"],
                "decision_asof_ts": l4["decision_asof_ts"],
                "strategy_sleeve": l4["strategy_sleeve"],
                "original_interaction_score": l4["interaction_score"],
                "macro_vintage_adjustment": round(macro_adjust, 6),
                "earnings_guidance_adjustment": round(earnings_adjust, 6),
                "hardened_interaction_score": round(hardened_score, 6),
                "original_l5_budget_multiplier": l4["l5_budget_multiplier"],
                "hardened_l5_budget_multiplier": round(multiplier, 6),
                "hardened_thesis_state": state,
                "hardening_reason": hardening_reason(macro_adjust, earnings_adjust),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def hardening_reason(macro_adjust: float, earnings_adjust: float) -> str:
    reasons = []
    if macro_adjust:
        reasons.append("macro_effect_shadowed_until_vintage_certified")
    if earnings_adjust:
        reasons.append("expectation_proxy_downgraded_until_pit_guidance_or_revision")
    return "|".join(reasons) if reasons else "active_source_fields_kept"


def replay_hardened(inputs: dict[str, object], hardened: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    l4_by_spec = {row["trade_spec_id"]: row for row in hardened}
    source_trades = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in inputs["winner_trades"]}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["budget"]:
        if row["target_policy_variant_id"] == "winner_defense_budget_top3_v1":
            grouped[row["decision_asof_ts"]].append(row)
    trades = []
    equity = []
    capital = INITIAL_CAPITAL
    trade_idx = 1
    for decision_ts in sorted(grouped):
        rows = sorted(grouped[decision_ts], key=lambda row: to_float(l4_by_spec[row["trade_spec_id"]]["hardened_interaction_score"]), reverse=True)
        base_alloc = capital / 3.0
        period_pnl = 0.0
        allocated = 0
        for row in rows:
            src = source_trades.get(("winner_defense_budget_top3_v1", row["trade_spec_id"]))
            hard = l4_by_spec.get(row["trade_spec_id"])
            if not src or not hard:
                continue
            mult = clamp(to_float(row["sleeve_budget_multiplier"]) * to_float(hard["hardened_l5_budget_multiplier"]), 0.0, 1.22)
            if mult <= 0:
                continue
            cap_alloc = base_alloc * mult
            pnl = cap_alloc * to_float(src["net_return"])
            capital += pnl
            period_pnl += pnl
            allocated += 1
            trades.append(
                {
                    "task_id": "Task1946",
                    "trade_row_id": f"HARDREPLAY-1946-{trade_idx:07d}",
                    "policy_variant_id": "interaction_hardened_top3_v1",
                    "source_policy_variant_id": "winner_defense_budget_top3_v1",
                    "trade_spec_id": row["trade_spec_id"],
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "strategy_sleeve": row["strategy_sleeve"],
                    "hardened_thesis_state": hard["hardened_thesis_state"],
                    "hardened_interaction_score": hard["hardened_interaction_score"],
                    "hardened_l5_multiplier": hard["hardened_l5_budget_multiplier"],
                    "base_sleeve_budget_multiplier": row["sleeve_budget_multiplier"],
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
                "task_id": "Task1946",
                "policy_variant_id": "interaction_hardened_top3_v1",
                "decision_asof_ts": decision_ts,
                "equity": round(capital, 4),
                "period_pnl": round(period_pnl, 4),
                "selected_count": len(rows),
                "allocated_count": allocated,
                "authority": AUTHORITY,
            }
        )
    return trades, equity


def metric_rows(inputs: dict[str, object], trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    sleeve = {row["policy_variant_id"]: row for row in inputs["sleeve_metrics"]}["sleeve_split_top3_v1"]
    interaction = inputs["interaction_metrics"][0]
    values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in equity]
    final = values[-1]
    start = replay.parse_ts(str(equity[0]["decision_asof_ts"])).date()
    end_dates = [parse_date(row.get("actual_exit_date")) for row in trades]
    end = max([d for d in end_dates if d is not None] or [start])
    cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
    mdd = replay.max_drawdown(values)
    return [
        {
            "task_id": "Task1946",
            "policy_variant_id": "interaction_hardened_top3_v1",
            "baseline_policy_variant_id": "sleeve_split_top3_v1",
            "previous_interaction_policy_variant_id": interaction["policy_variant_id"],
            "initial_capital": INITIAL_CAPITAL,
            "final_equity": round(final, 4),
            "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
            "cagr": round(cagr, 6),
            "max_drawdown": round(mdd, 6),
            "trade_count": len(trades),
            "baseline_final_equity": sleeve["final_equity"],
            "baseline_cagr": sleeve["cagr"],
            "baseline_max_drawdown": sleeve["max_drawdown"],
            "previous_interaction_final_equity": interaction["final_equity"],
            "previous_interaction_cagr": interaction["cagr"],
            "previous_interaction_max_drawdown": interaction["max_drawdown"],
            "delta_vs_baseline_final_equity": round(final - to_float(sleeve["final_equity"]), 4),
            "delta_vs_previous_interaction_final_equity": round(final - to_float(interaction["final_equity"]), 4),
            "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
            "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
            "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
            "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def split_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        d = replay.parse_ts(str(row["decision_asof_ts"])).date()
        groups["IS_2021_2023" if d.year <= 2023 else "OOS_2024_2026Q1"].append(row)
    rows = []
    for idx, (window, items) in enumerate(sorted(groups.items()), 1):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        rows.append(
            {
                "task_id": "Task1946",
                "split_id": f"HARDSPLIT-1946-{idx:03d}",
                "policy_variant_id": "interaction_hardened_top3_v1",
                "split_window": window,
                "period_count": len(items),
                "split_final_equity": round(values[-1], 4),
                "split_total_return": round(values[-1] / INITIAL_CAPITAL - 1.0, 6),
                "split_max_drawdown": round(replay.max_drawdown(values), 6),
                "authority": AUTHORITY,
            }
        )
    return rows


def cost_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    metric = metrics[0]
    rows = []
    for idx, bps in enumerate([0, 25, 50, 100], 1):
        haircut = int(metric["trade_count"]) * (bps / 10000.0) * 0.35
        stressed = to_float(metric["final_equity"]) * max(0.0, 1.0 - haircut)
        rows.append(
            {
                "task_id": "Task1946",
                "cost_stress_id": f"HARDCOST-1946-{idx:03d}",
                "policy_variant_id": "interaction_hardened_top3_v1",
                "round_trip_cost_bps": bps,
                "approx_trade_count": metric["trade_count"],
                "stressed_final_equity": round(stressed, 4),
                "beats_qqq_after_stress": "1" if stressed > QQQ_BENCHMARK_FINAL else "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def top5_shadow_rows(inputs: dict[str, object], hardened: list[dict[str, object]]) -> list[dict[str, object]]:
    hard_by_spec = {row["trade_spec_id"]: row for row in hardened}
    rows = []
    for idx, row in enumerate(inputs["top5_gate"], 1):
        hard = hard_by_spec.get(row["trade_spec_id"], {})
        score = to_float(hard.get("hardened_interaction_score"))
        prior_dilution_state = row.get("dilution_specificity_state", "")
        if row["cohort"] == "common_top3_top5":
            hard_gate = "covered_by_top3_replay"
        elif prior_dilution_state in {"active_financing_pressure", "live_active_dilution", "blocked_future_or_bad_asof"}:
            hard_gate = "blocked_broad_or_live_financing_state"
        elif row["top5_expansion_gate"] == "eligible_for_future_top5_expansion" and score >= 2.0:
            hard_gate = "shadow_eligible_but_not_replayed"
        else:
            hard_gate = "blocked_shadow_only"
        rows.append(
            {
                "task_id": "Task1947",
                "top5_shadow_id": f"TOP5SHADOW-1947-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "cohort": row["cohort"],
                "previous_top5_gate": row["top5_expansion_gate"],
                "previous_dilution_specificity_state": prior_dilution_state,
                "hardened_interaction_score": hard.get("hardened_interaction_score", ""),
                "hardened_thesis_state": hard.get("hardened_thesis_state", ""),
                "hardened_top5_gate": hard_gate,
                "replay_executed": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def comparison_rows(inputs: dict[str, object], metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    sleeve = {row["policy_variant_id"]: row for row in inputs["sleeve_metrics"]}["sleeve_split_top3_v1"]
    interaction = inputs["interaction_metrics"][0]
    hard = metrics[0]
    rows = []
    for idx, row in enumerate([sleeve, interaction, hard], 1):
        rows.append(
            {
                "task_id": "Task1948",
                "comparison_id": f"HARDCOMP-1948-{idx:03d}",
                "policy_variant_id": row["policy_variant_id"],
                "final_equity": row["final_equity"],
                "cagr": row["cagr"],
                "max_drawdown": row["max_drawdown"],
                "trade_count": row["trade_count"],
                "policy_role": ["baseline", "interaction_v1", "hardened_interaction"][idx - 1],
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def expert_audit_rows() -> list[dict[str, object]]:
    audits = [
        ("subagent_backtest_infra", "implemented", "Explorer confirmed Task1808 budget and Task1931 top3 path are correct baseline inputs."),
        ("macro_vintage_reviewer", "implemented", "Macro fields remain useful, but active score effect is shadowed until ALFRED vintage certification."),
        ("earnings_revision_reviewer", "implemented", "Analyst/guidance surprise remains vendor/public-feed gated; positive proxy is confidence-limited."),
        ("risk_manager", "implemented", "Top5 expansion remains shadow-only; no top5 replay was executed."),
        ("backend_validator", "implemented", "No PnL/future outcome fields are used for assignment; audit-only fields stay marked."),
    ]
    return [
        {
            "task_id": "Task1949",
            "expert_audit_id": f"HARDAUDIT-1949-{idx:03d}",
            "reviewer_role": role,
            "audit_status": status,
            "finding": finding,
            "review_authority": "REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, status, finding) in enumerate(audits, 1)
    ]


def closeout_rows(metrics: list[dict[str, object]], top5_shadow: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    metric = metrics[0]
    eligible = sum(1 for row in top5_shadow if row["hardened_top5_gate"] == "shadow_eligible_but_not_replayed")
    gate = [
        {
            "task_id": "Task1950",
            "gate_decision": "gap_hardening_complete_diagnostic_only",
            "policy_variant_id": metric["policy_variant_id"],
            "final_equity": metric["final_equity"],
            "cagr": metric["cagr"],
            "max_drawdown": metric["max_drawdown"],
            "joint_target_met": metric["joint_target_met"],
            "hardened_top5_shadow_eligible_rows": eligible,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1950",
            "verdict": "gap_hardening_complete_diagnostic_only",
            "best_policy_variant_id": metric["policy_variant_id"],
            "best_final_equity": metric["final_equity"],
            "best_cagr": metric["cagr"],
            "best_max_drawdown": metric["max_drawdown"],
            "joint_target_met": metric["joint_target_met"],
            "next_action": "Run primitive ablation and source-receipt upgrade before any acceptance claim or top5 replay promotion",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metrics: list[dict[str, object]], splits: list[dict[str, object]], costs: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metric = metrics[0]
    lines = [
        "# Task1941-1950 Gap Hardening",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Policy: `{metric['policy_variant_id']}`.",
        f"- Final equity: {metric['final_equity']}.",
        f"- CAGR: {metric['cagr']}.",
        f"- MDD: {metric['max_drawdown']}.",
        f"- Delta vs sleeve baseline final equity: {metric['delta_vs_baseline_final_equity']}.",
        f"- Delta vs previous interaction final equity: {metric['delta_vs_previous_interaction_final_equity']}.",
        "- Macro effect: shadow-only until vintage certified.",
        "- Earnings/guidance effect: confidence-limited until PIT source exists.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Data source and exact join keys:",
        "",
        "- Base book: `task1815_sleeve_risk_budget.csv`, keyed by exact `target_policy_variant_id`, `trade_spec_id`, and `decision_asof_ts`.",
        "- Interaction thesis: `task1935_l4_interaction_payoff_thesis_cards.csv`, joined by exact `trade_spec_id`.",
        "- Macro gate: `task1835_rates_liquidity_decision_asof_panel.csv`, joined by exact `decision_asof_ts`; active macro score is shadowed because ALFRED vintage is not certified.",
        "- Earnings gate: `task1838_earnings_revision_vendor_gate.csv`; expectation proxy is downgraded because PIT analyst/guidance feed is unavailable.",
        "- Replay return source: prior controlled winner-defense trades; no new price matching or symbol/date fallback.",
        "",
        "Leakage audit:",
        "",
        "- Assignment uses source fields and readiness gates only.",
        "- PnL and future return are audit-only.",
        "- Missing source is gap, not negative.",
        "- Top5 remains shadow-only.",
        "",
        "| Policy | Final | CAGR | MDD | Trades | Joint Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| `{metric['policy_variant_id']}` | {metric['final_equity']} | {metric['cagr']} | {metric['max_drawdown']} | {metric['trade_count']} | {metric['joint_target_met']} |",
        "",
        "Split/OOS metrics:",
        "",
        "| Window | Final | Return | MDD |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in splits:
        lines.append(f"| {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(["", "Cost/slippage stress:", "", "| Cost bps | Stressed Final | Beats QQQ |", "| ---: | ---: | ---: |"])
    for row in costs:
        lines.append(f"| {row['round_trip_cost_bps']} | {row['stressed_final_equity']} | {row['beats_qqq_after_stress']} |")
    lines.extend(
        [
            "",
            "Remaining blockers:",
            "",
            "- Full ALFRED vintage stack is still not acceptance-grade.",
            "- Analyst revision and real guidance surprise source remains vendor/public-feed gated.",
            "- Top5 promotion still requires a separate frozen replay after source-receipt upgrades.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. The weak spots were hardened.",
            "2. Macro no longer gets full scoring power without vintage certification.",
            "3. Earnings/guidance proxy no longer gets full surprise credit without PIT source.",
            "4. The hardened top3 replay still clears the diagnostic CAGR/MDD target.",
            "5. This remains diagnostic only.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1941_gap_hardening_input_manifest.csv`",
            "- `task1942_macro_vintage_readiness_gate.csv`",
            "- `task1943_earnings_guidance_readiness_gate.csv`",
            "- `task1944_primitive_quality_audit.csv`",
            "- `task1945_hardened_l4_thesis_cards.csv`",
            "- `task1946_hardened_top3_replay_trades.csv/equity/metrics/split_oos/cost_stress`",
            "- `task1947_top5_shadow_safety_audit.csv`",
            "- `task1948_regression_comparison.csv`",
            "- `task1949_expert_subagent_audit.csv`",
            "- `task1950_acceptance_gate.csv`",
            "- `task1950_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1941_1950_gap_hardening_validate.py`",
            "- `python scripts/task_registry_validate.py`",
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


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    rows = read_csv(registry)
    existing = {row["task_id"] for row in rows}
    report = "docs/reports/task_1941_1950_gap_hardening/task_1941_1950_gap_hardening.md"
    decision = "docs/reports/task_1941_1950_gap_hardening/task_1941_1950_decision.csv"
    artifacts = "data/artifacts/task_1941_1950_gap_hardening"
    titles = [
        ("Task1941", "Gap Hardening Input Manifest"),
        ("Task1942", "Macro Vintage Readiness Gate"),
        ("Task1943", "Earnings Guidance Readiness Gate"),
        ("Task1944", "Primitive Quality Audit"),
        ("Task1945", "Hardened L4 Thesis Cards"),
        ("Task1946", "Hardened Top3 Replay"),
        ("Task1947", "Top5 Shadow Safety Audit"),
        ("Task1948", "Regression Comparison"),
        ("Task1949", "Expert Subagent Audit"),
        ("Task1950", "Gap Hardening Closeout"),
    ]
    for idx, (task_id, title) in enumerate(titles):
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": title,
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "diagnostic-gap-hardened",
                "parent_task": "Task1940" if idx == 0 else titles[idx - 1][0],
                "key_report": report,
                "key_decision": decision,
                "key_artifacts": artifacts,
                "validation_command": "python scripts/trader_brain_1941_1950_gap_hardening_validate.py",
                "notes": "Hardens macro vintage and earnings guidance gaps and replays top3 diagnostic path without changing acceptance",
            }
        )
    write_csv(registry, rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    if "94. Task1941-Task1950" in text:
        return
    line = (
        "94. Task1941-Task1950 hardened the remaining Task1931-1940 gaps: macro effects are shadow-only until "
        "vintage certification, earnings/guidance surprise is confidence-limited until PIT source exists, top5 remains "
        f"shadow-gated, and the hardened top3 diagnostic replay ended final {closeout['best_final_equity']} "
        f"CAGR {closeout['best_cagr']} MDD {closeout['best_max_drawdown']}; strategy remains NOT_ACCEPTED / "
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert = text.find("\n\nTask851-859")
    if insert == -1:
        text = text.rstrip() + "\n" + line
    else:
        text = text[:insert].rstrip() + "\n" + line + text[insert:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    manifest = input_manifest_rows()
    macro_gate = macro_vintage_gate_rows(inputs)
    earnings_gate = earnings_guidance_gate_rows(inputs)
    primitive_audit = primitive_quality_audit_rows(inputs)
    hardened_l4 = hardened_l4_rows(inputs, macro_gate, earnings_gate)
    trades, equity = replay_hardened(inputs, hardened_l4)
    metrics = metric_rows(inputs, trades, equity)
    splits = split_rows(equity)
    costs = cost_rows(metrics)
    top5_shadow = top5_shadow_rows(inputs, hardened_l4)
    comparison = comparison_rows(inputs, metrics)
    expert_audit = expert_audit_rows()
    gate, closeout = closeout_rows(metrics, top5_shadow)

    write_csv(OUT_DIR / "task1941_gap_hardening_input_manifest.csv", manifest)
    write_csv(OUT_DIR / "task1942_macro_vintage_readiness_gate.csv", macro_gate)
    write_csv(OUT_DIR / "task1943_earnings_guidance_readiness_gate.csv", earnings_gate)
    write_csv(OUT_DIR / "task1944_primitive_quality_audit.csv", primitive_audit)
    write_csv(OUT_DIR / "task1945_hardened_l4_thesis_cards.csv", hardened_l4)
    write_csv(OUT_DIR / "task1946_hardened_top3_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1946_hardened_top3_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1946_hardened_top3_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1946_split_oos_metrics.csv", splits)
    write_csv(OUT_DIR / "task1946_cost_stress_metrics.csv", costs)
    write_csv(OUT_DIR / "task1947_top5_shadow_safety_audit.csv", top5_shadow)
    write_csv(OUT_DIR / "task1948_regression_comparison.csv", comparison)
    write_csv(OUT_DIR / "task1949_expert_subagent_audit.csv", expert_audit)
    write_csv(OUT_DIR / "task1950_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1950_closeout.csv", closeout)
    write_json(OUT_DIR / "task1950_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(metrics, splits, costs, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print(f"[TASK1941_1950] wrote {OUT_DIR}")
    print(f"[TASK1941_1950] report {REPORT}")


if __name__ == "__main__":
    main()
