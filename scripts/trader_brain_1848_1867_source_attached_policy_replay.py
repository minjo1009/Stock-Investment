from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1808 = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
TASK1834 = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
OUT_DIR = ROOT / "data/artifacts/task_1848_1867_source_attached_policy_replay"
REPORT_DIR = ROOT / "docs/reports/task_1848_1867_source_attached_policy_replay"
REPORT = REPORT_DIR / "task_1848_1867_source_attached_policy_replay.md"
DECISION = REPORT_DIR / "task_1848_1867_decision.csv"

AUTHORITY = "DIAGNOSTIC_SOURCE_ATTACHED_POLICY_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "source_attached_top3_v1": {"source_policy": "winner_defense_budget_top3_v1", "slot_cap": 3},
    "source_attached_top5_v1": {"source_policy": "winner_defense_budget_top5_v1", "slot_cap": 5},
}


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


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def parse_date(value: object) -> date | None:
    try:
        if value in {"", None}:
            return None
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def expert_review_rows() -> list[dict[str, object]]:
    rows = [
        (
            "portfolio_pm",
            "Integrate targeted source state as coarse sleeve action, not micro sizing.",
            "adopt",
        ),
        (
            "macro_rates_trader",
            "Rates/liquidity should change sleeve permission and budget state when liquidity stress or rate pressure is known as-of.",
            "adopt",
        ),
        (
            "capital_markets_trader",
            "SEC financing/dilution should be a hard cap/no-entry for speculative_event and a trim warning for other sleeves.",
            "adopt",
        ),
        (
            "earnings_analyst",
            "Earnings revision must remain blocked because no PIT vendor feed exists locally.",
            "adopt_block",
        ),
        (
            "backend_validator",
            "Use only source packet timestamps and exact ids; PnL remains audit-only.",
            "adopt",
        ),
    ]
    return [
        {
            "task_id": "Task1848",
            "expert_review_id": f"SRCREPLAYEXPERT-1848-{idx:03d}",
            "expert_role": role,
            "critique": critique,
            "decision": decision,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, critique, decision) in enumerate(rows, 1)
    ]


def source_trade_map() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv")
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in rows}


def load_inputs() -> tuple[list[dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, str]]:
    budgets = read_csv(TASK1808 / "task1815_sleeve_risk_budget.csv")
    rates = {row["decision_asof_ts"]: row for row in read_csv(TASK1834 / "task1835_rates_liquidity_decision_asof_panel.csv")}
    sec_links = {row["trade_spec_id"]: row for row in read_csv(TASK1834 / "task1842_sec_dilution_decision_asof_links.csv")}
    sec_extract = {
        row["financing_source_packet_id"]: row
        for row in read_csv(TASK1834 / "task1837_financing_dilution_extractor_contract.csv")
    }
    earnings_gate = read_csv(TASK1834 / "task1838_earnings_revision_vendor_gate.csv")[0]
    return budgets, rates, sec_links, sec_extract, earnings_gate


def source_manifest_rows(budgets: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(budgets, 1):
        rows.append(
            {
                "task_id": "Task1849",
                "source_attach_input_id": f"SRCATTACHINPUT-1849-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "source_budget_row_authority": row["authority"],
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def sleeve_rate_multiplier(sleeve: str, rate_row: dict[str, str]) -> float:
    key = {
        "winner_compounder": "winner_compounder_multiplier",
        "cyclical_beta": "cyclical_beta_multiplier",
        "speculative_event": "speculative_event_multiplier",
        "defensive_quality": "defensive_quality_multiplier",
    }.get(sleeve, "winner_compounder_multiplier")
    return to_float(rate_row.get(key), 1.0)


def sec_state_for(row: dict[str, str], sec_links: dict[str, dict[str, str]], sec_extract: dict[str, dict[str, str]]) -> dict[str, str]:
    link = sec_links.get(row["trade_spec_id"], {})
    packet_id = link.get("latest_financing_source_packet_id", "")
    extraction = sec_extract.get(packet_id, {})
    if not link or link.get("source_gap_flag") == "1":
        return {
            "packet_id": "",
            "accepted_ts": "",
            "dilution_pressure_state": "source_gap",
            "dilution_signal_families": "",
            "asof_guard_pass": link.get("asof_guard_pass", "1") if link else "1",
        }
    return {
        "packet_id": packet_id,
        "accepted_ts": link.get("latest_financing_accepted_ts", ""),
        "dilution_pressure_state": extraction.get("dilution_pressure_state", "source_gap"),
        "dilution_signal_families": extraction.get("dilution_signal_families", ""),
        "asof_guard_pass": link.get("asof_guard_pass", "0"),
    }


def sec_action_modifier(sleeve: str, dilution_state: str) -> tuple[str, float, str]:
    if dilution_state == "source_gap":
        return "sec_source_gap_neutral", 1.0, "missing_source_not_negative"
    if dilution_state in {"active_financing_pressure", "convertible_warrant_overhang"}:
        if sleeve == "speculative_event":
            return "no_entry", 0.0, "speculative_financing_or_dilution_hard_block"
        return "trim", 0.85, "financing_or_dilution_trim_warning"
    if dilution_state == "shelf_capacity_watch":
        if sleeve == "speculative_event":
            return "cap", 0.35, "speculative_shelf_capacity_cap"
        return "trim", 0.9, "shelf_capacity_watch_trim"
    if dilution_state == "historical_or_closed_financing":
        return "hold", 1.0, "historical_financing_no_current_penalty"
    return "hold", 1.0, "boilerplate_or_sparse_financing_no_current_penalty"


def rate_action_modifier(sleeve: str, rate_row: dict[str, str]) -> tuple[str, float, str]:
    rate_state = rate_row.get("rate_regime_state", "rate_source_gap")
    liquidity = rate_row.get("liquidity_stress_state", "liquidity_source_gap")
    multiplier = sleeve_rate_multiplier(sleeve, rate_row)
    if liquidity == "liquidity_stress":
        return "macro_trim", multiplier, "liquidity_stress_known_asof"
    if rate_state == "rising_rate_pressure" and sleeve in {"winner_compounder", "cyclical_beta", "speculative_event"}:
        return "macro_trim", multiplier, "rising_rate_pressure_known_asof"
    if rate_state == "easing_rate_tailwind" and liquidity != "liquidity_stress":
        return "macro_support", multiplier, "easing_rate_tailwind_known_asof"
    return "macro_hold", multiplier, "rates_liquidity_neutral"


def build_source_attached_layers() -> dict[str, list[dict[str, object]]]:
    budgets, rates, sec_links, sec_extract, earnings_gate = load_inputs()
    l2_rates: list[dict[str, object]] = []
    l2_sec: list[dict[str, object]] = []
    l2_earnings: list[dict[str, object]] = []
    l3_edges: list[dict[str, object]] = []
    l4_cards: list[dict[str, object]] = []
    l5_budget: list[dict[str, object]] = []

    for idx, row in enumerate(budgets, 1):
        rate_row = rates.get(row["decision_asof_ts"], {})
        sec_state = sec_state_for(row, sec_links, sec_extract)
        sleeve = row["strategy_sleeve"]
        rate_action, rate_mult, rate_reason = rate_action_modifier(sleeve, rate_row)
        sec_action, sec_mult, sec_reason = sec_action_modifier(sleeve, sec_state["dilution_pressure_state"])
        earnings_state = "vendor_blocked_schema_only"
        base_mult = to_float(row["sleeve_budget_multiplier"])

        source_action = "hold"
        source_reason = "source_neutral"
        if sec_action == "no_entry":
            source_action, source_reason = "no_entry", sec_reason
        elif sec_action == "cap":
            source_action, source_reason = "cap", sec_reason
        elif sec_action == "trim" or rate_action == "macro_trim":
            source_action, source_reason = "trim", f"{rate_reason}|{sec_reason}"
        elif rate_action == "macro_support" and sec_action in {"hold", "sec_source_gap_neutral"}:
            source_action, source_reason = "hold", rate_reason

        final_mult = 0.0 if source_action == "no_entry" else clamp(base_mult * rate_mult * sec_mult, 0.0, 1.18)
        if source_action == "cap":
            final_mult = min(final_mult, 0.35)

        l2_rates.append(
            {
                "task_id": "Task1850",
                "rates_l2_id": f"RATESL2-1850-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": sleeve,
                "rate_regime_state": rate_row.get("rate_regime_state", "source_gap"),
                "liquidity_stress_state": rate_row.get("liquidity_stress_state", "source_gap"),
                "curve_state": rate_row.get("curve_state", "source_gap"),
                "source_available_to_brain_ts": rate_row.get("source_available_to_brain_ts", ""),
                "rate_action": rate_action,
                "rate_action_multiplier": rate_mult,
                "asof_guard_pass": "1" if not rate_row or rate_row.get("source_available_to_brain_ts", "") <= row["decision_asof_ts"] else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l2_sec.append(
            {
                "task_id": "Task1851",
                "sec_l2_id": f"SECL2-1851-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": sleeve,
                "latest_financing_source_packet_id": sec_state["packet_id"],
                "latest_financing_accepted_ts": sec_state["accepted_ts"],
                "dilution_pressure_state": sec_state["dilution_pressure_state"],
                "dilution_signal_families": sec_state["dilution_signal_families"],
                "sec_action": sec_action,
                "sec_action_multiplier": sec_mult,
                "asof_guard_pass": sec_state["asof_guard_pass"],
                "source_gap_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l2_earnings.append(
            {
                "task_id": "Task1852",
                "earnings_l2_id": f"EARNL2-1852-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "earnings_revision_state": earnings_state,
                "gate_verdict": earnings_gate.get("gate_verdict", ""),
                "assignment_effect": "blocked_no_score_change",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l3_edges.append(
            {
                "task_id": "Task1853",
                "targeted_source_edge_id": f"SRCEDGE-1853-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": sleeve,
                "rates_edge": f"{rate_action}:{rate_reason}",
                "sec_edge": f"{sec_action}:{sec_reason}",
                "earnings_edge": "blocked_vendor_gate_no_assignment_effect",
                "edge_state": source_action,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l4_cards.append(
            {
                "task_id": "Task1854",
                "source_attached_thesis_card_id": f"SRCTHESIS-1854-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": sleeve,
                "base_sleeve_action": row["sleeve_action"],
                "source_attached_action": source_action,
                "source_attached_reason": source_reason,
                "rate_regime_state": rate_row.get("rate_regime_state", "source_gap"),
                "liquidity_stress_state": rate_row.get("liquidity_stress_state", "source_gap"),
                "dilution_pressure_state": sec_state["dilution_pressure_state"],
                "earnings_revision_state": earnings_state,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l5_budget.append(
            {
                "task_id": "Task1855",
                "source_attached_budget_id": f"SRCBUDGET-1855-{idx:06d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": sleeve,
                "base_sleeve_budget_multiplier": base_mult,
                "rate_action_multiplier": rate_mult,
                "sec_action_multiplier": sec_mult,
                "source_attached_budget_multiplier": round(final_mult, 6),
                "source_attached_action": source_action,
                "source_attached_reason": source_reason,
                "rate_regime_state": rate_row.get("rate_regime_state", "source_gap"),
                "liquidity_stress_state": rate_row.get("liquidity_stress_state", "source_gap"),
                "dilution_pressure_state": sec_state["dilution_pressure_state"],
                "earnings_revision_state": earnings_state,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return {
        "task1849_source_attach_input_manifest.csv": source_manifest_rows(budgets),
        "task1850_rates_l2_meaning_panel.csv": l2_rates,
        "task1851_sec_financing_l2_meaning_panel.csv": l2_sec,
        "task1852_earnings_vendor_block_panel.csv": l2_earnings,
        "task1853_l3_targeted_source_edges.csv": l3_edges,
        "task1854_l4_source_attached_thesis_cards.csv": l4_cards,
        "task1855_l5_source_attached_budget.csv": l5_budget,
    }


def replay_budget(budget_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    source_trades = source_trade_map()
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in budget_rows:
        grouped[(str(row["target_policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    trade_idx = 1
    for policy_id, config in POLICIES.items():
        source_policy = config["source_policy"]
        capital = INITIAL_CAPITAL
        decisions = sorted({key[1] for key in grouped if key[0] == source_policy})
        for decision_ts in decisions:
            rows = sorted(
                grouped[(source_policy, decision_ts)],
                key=lambda r: to_float(r["source_attached_budget_multiplier"]),
                reverse=True,
            )
            base_alloc = capital / int(config["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            sleeve_counts: Counter[str] = Counter()
            for row in rows:
                source = source_trades.get((source_policy, str(row["trade_spec_id"])))
                if not source:
                    continue
                mult = to_float(row["source_attached_budget_multiplier"])
                if mult <= 0:
                    continue
                allocated = base_alloc * mult
                pnl = allocated * to_float(source.get("net_return"))
                capital += pnl
                period_pnl += pnl
                allocated_count += 1
                sleeve_counts[str(row["strategy_sleeve"])] += 1
                trades.append(
                    {
                        "task_id": "Task1857",
                        "trade_row_id": f"SRCREPLAYTRADE-1857-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": row["trade_spec_id"],
                        "candidate_source_id": row["candidate_source_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "strategy_sleeve": row["strategy_sleeve"],
                        "source_attached_action": row["source_attached_action"],
                        "source_attached_reason": row["source_attached_reason"],
                        "source_attached_budget_multiplier": mult,
                        "rate_regime_state": row["rate_regime_state"],
                        "liquidity_stress_state": row["liquidity_stress_state"],
                        "dilution_pressure_state": row["dilution_pressure_state"],
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
                    "task_id": "Task1857",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(rows),
                    "allocated_count": allocated_count,
                    "winner_compounder_count": sleeve_counts["winner_compounder"],
                    "cyclical_beta_count": sleeve_counts["cyclical_beta"],
                    "speculative_event_count": sleeve_counts["speculative_event"],
                    "defensive_quality_count": sleeve_counts["defensive_quality"],
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    baseline = {row["policy_variant_id"]: row for row in read_csv(TASK1808 / "task1823_sleeve_replay_metrics.csv")}
    base_map = {
        "source_attached_top3_v1": "sleeve_split_top3_v1",
        "source_attached_top5_v1": "sleeve_split_top5_v1",
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
        base = baseline[base_map[policy_id]]
        out.append(
            {
                "task_id": "Task1858",
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
                "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 else "0",
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
                "task_id": "Task1858",
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


def cost_stress_rows(metric_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for metric in metric_rows:
        trades = int(metric["trade_count"])
        for bps in [0, 25, 50, 100]:
            haircut = trades * (bps / 10000.0) * 0.35
            stressed_final = to_float(metric["final_equity"]) * max(0.0, 1.0 - haircut)
            rows.append(
                {
                    "task_id": "Task1858",
                    "cost_stress_id": f"SRCCOST-1858-{idx:04d}",
                    "policy_variant_id": metric["policy_variant_id"],
                    "round_trip_cost_bps": bps,
                    "approx_trade_count": trades,
                    "stressed_final_equity": round(stressed_final, 4),
                    "beats_qqq_after_stress": "1" if stressed_final > QQQ_BENCHMARK_FINAL else "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def failure_attribution(trades: list[dict[str, object]], metric_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for label in ["strategy_sleeve", "source_attached_action", "rate_regime_state", "liquidity_stress_state", "dilution_pressure_state"]:
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for trade in trades:
            grouped[str(trade[label])].append(trade)
        for key, items in sorted(grouped.items()):
            rows.append(
                {
                    "task_id": "Task1859",
                    "failure_attr_id": f"SRCFAIL-1859-{idx:04d}",
                    "failure_area": label,
                    "bucket": key,
                    "trade_count": len(items),
                    "pnl_sum_audit_only": round(sum(to_float(item["pnl"]) for item in items), 4),
                    "negative_trade_count_audit_only": sum(1 for item in items if to_float(item["pnl"]) < 0),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    for metric in metric_rows:
        rows.append(
            {
                "task_id": "Task1859",
                "failure_attr_id": f"SRCFAIL-1859-{idx:04d}",
                "failure_area": "policy_metric",
                "bucket": metric["policy_variant_id"],
                "trade_count": metric["trade_count"],
                "pnl_sum_audit_only": round(to_float(metric["final_equity"]) - INITIAL_CAPITAL, 4),
                "negative_trade_count_audit_only": "",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def config_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1856",
            "policy_config_id": "SRCPOLICY-1856-001",
            "policy_variant_id": "source_attached_top3_v1",
            "source_policy_variant_id": "winner_defense_budget_top3_v1",
            "slot_cap": 3,
            "policy_freeze_state": "frozen_before_replay",
            "source_fields_used": "rates_regime/liquidity_stress/sec_dilution_pressure/earnings_vendor_gate",
            "forbidden_fields": "future_price/future_return/pnl/drawdown/outcome_label",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1856",
            "policy_config_id": "SRCPOLICY-1856-002",
            "policy_variant_id": "source_attached_top5_v1",
            "source_policy_variant_id": "winner_defense_budget_top5_v1",
            "slot_cap": 5,
            "policy_freeze_state": "frozen_before_replay",
            "source_fields_used": "rates_regime/liquidity_stress/sec_dilution_pressure/earnings_vendor_gate",
            "forbidden_fields": "future_price/future_return/pnl/drawdown/outcome_label",
            "authority": AUTHORITY,
        },
    ]


def gate_closeout(metric_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best = max(metric_rows, key=lambda row: to_float(row["final_equity"]))
    gate = [
        {
            "task_id": "Task1860",
            "gate_decision": "diagnostic_replay_complete_not_accepted",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "joint_target_met": best["joint_target_met"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1867",
            "verdict": "source_attached_policy_replay_complete_diagnostic_only",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit whether source-attached policy improved true sleeve behavior before promoting any rule",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metric_rows: list[dict[str, object]], split: list[dict[str, object]], cost: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1848-1867 Source-Attached Policy Replay",
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
        "Data source and exact join keys:",
        "",
        "- Base sleeve budget: `task1815_sleeve_risk_budget.csv`, joined by `trade_spec_id` and `decision_asof_ts`.",
        "- Rates/liquidity: `task1835_rates_liquidity_decision_asof_panel.csv`, joined by exact `decision_asof_ts` with source time <= decision time.",
        "- SEC financing/dilution: `task1842_sec_dilution_decision_asof_links.csv` and `task1837_financing_dilution_extractor_contract.csv`, joined by exact `trade_spec_id` and source packet id.",
        "- Earnings revision: blocked by `task1838_earnings_revision_vendor_gate.csv`; no assignment effect.",
        "- Replay return source: prior controlled winner-defense replay trades; no new price matching.",
        "",
        "Leakage audit:",
        "",
        "- Assignment uses only source states known as-of.",
        "- PnL, drawdown, and future returns remain audit-only.",
        "- Missing SEC or earnings source is source gap, not bearish evidence.",
        "",
        "| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | Joint Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metric_rows:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['baseline_final_equity']} | {row['baseline_max_drawdown']} | {row['delta_final_equity']} | {row['delta_mdd']} | {row['trade_count']} | {row['joint_target_met']} |"
        )
    lines.extend(["", "Split/OOS metrics:", "", "| Policy | Window | Final | Return | MDD |", "| --- | --- | ---: | ---: | ---: |"])
    for row in split:
        lines.append(f"| `{row['policy_variant_id']}` | {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(["", "Cost/slippage stress:", "", "| Policy | Cost bps | Stressed Final | Beats QQQ |", "| --- | ---: | ---: | ---: |"])
    for row in cost:
        lines.append(f"| `{row['policy_variant_id']}` | {row['round_trip_cost_bps']} | {row['stressed_final_equity']} | {row['beats_qqq_after_stress']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Rates/liquidity와 SEC dilution source를 실제 판단에 붙였습니다.",
            "2. Earnings revision은 vendor data가 없어서 판단에 안 넣었습니다.",
            "3. 새 매칭이나 micro sizing은 만들지 않았습니다.",
            "4. 결과가 좋아도 아직 승인 상태는 아닙니다.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1848_expert_review.csv`",
            "- `task1849_source_attach_input_manifest.csv`",
            "- `task1850_rates_l2_meaning_panel.csv`",
            "- `task1851_sec_financing_l2_meaning_panel.csv`",
            "- `task1852_earnings_vendor_block_panel.csv`",
            "- `task1853_l3_targeted_source_edges.csv`",
            "- `task1854_l4_source_attached_thesis_cards.csv`",
            "- `task1855_l5_source_attached_budget.csv`",
            "- `task1856_frozen_policy_config.csv`",
            "- `task1857_controlled_source_attached_replay_trades.csv/equity`",
            "- `task1858_source_attached_replay_metrics.csv/split_oos/cost_stress`",
            "- `task1859_failure_attribution.csv`",
            "- `task1860_acceptance_gate.csv`",
            "- `task1867_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1848_1867_source_attached_policy_replay_validate.py`",
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

    layers = build_source_attached_layers()
    budgets = layers["task1855_l5_source_attached_budget.csv"]
    trades, equity = replay_budget(budgets)
    metric_rows = metrics(trades, equity)
    split = split_rows(equity)
    cost = cost_stress_rows(metric_rows)
    fail_attr = failure_attribution(trades, metric_rows)
    gate, closeout = gate_closeout(metric_rows)

    outputs = [
        ("task1848_expert_review.csv", expert_review_rows()),
        *list(layers.items()),
        ("task1856_frozen_policy_config.csv", config_rows()),
        ("task1857_controlled_source_attached_replay_trades.csv", trades),
        ("task1857_controlled_source_attached_replay_equity.csv", equity),
        ("task1858_source_attached_replay_metrics.csv", metric_rows),
        ("task1858_split_oos_metrics.csv", split),
        ("task1858_cost_stress_metrics.csv", cost),
        ("task1859_failure_attribution.csv", fail_attr),
        ("task1860_acceptance_gate.csv", gate),
        ("task1867_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task1867_closeout.json", closeout[0])
    write_report(metric_rows, split, cost, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1848_1867] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
