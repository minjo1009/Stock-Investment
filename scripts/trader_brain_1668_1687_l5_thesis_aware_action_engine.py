from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1558_1577_l5_damage_control_engine as damage
import trader_brain_1648_1667_l5_action_quality_audit as aq
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK1518 = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
TASK1558 = ROOT / "data/artifacts/task_1558_1577_l5_damage_control_engine"
TASK1618 = ROOT / "data/artifacts/task_1618_1647_expectation_payoff_rerisk_bridge"
OUT_DIR = ROOT / "data/artifacts/task_1668_1687_l5_thesis_aware_action_engine"
REPORT_DIR = ROOT / "docs/reports/task_1668_1687_l5_thesis_aware_action_engine"
REPORT = REPORT_DIR / "task_1668_1687_l5_thesis_aware_action_engine.md"
DECISION = REPORT_DIR / "task_1668_1687_decision.csv"

AUTHORITY = "DIAGNOSTIC_L5_THESIS_AWARE_ACTION_ENGINE_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "thesis_aware_no_rerisk_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3, "rerisk_fraction": 0.0},
    "thesis_aware_rerisk_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3, "rerisk_fraction": 0.25},
    "thesis_aware_no_rerisk_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5, "rerisk_fraction": 0.0},
    "thesis_aware_rerisk_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5, "rerisk_fraction": 0.25},
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
    return aq.to_float(value, default)


def parse_date(value: object) -> date | None:
    return aq.parse_date(value)


def pct_return(start: float, end: float) -> float:
    if start <= 0:
        return 0.0
    return end / start - 1.0


def net_return(start: float, end: float) -> float:
    return pct_return(start, end) - ROUND_TRIP_COST_BPS / 10000.0


def expert_review_rows() -> list[dict[str, object]]:
    rows = [
        ("risk_pm", "Reduce only after separating market-linked selloff from idiosyncratic thesis damage.", "adopt"),
        ("event_driven_trader", "Exit needs evidence quorum; source text alone is not enough unless thesis is weak.", "adopt"),
        ("execution_trader", "Re-risk must buy thesis recovery, not a small bounce.", "adopt"),
        ("portfolio_manager", "Preserve hold extension because it is the only passing L5 action.", "adopt"),
        ("validation_engineer", "Keep all counterfactual and PnL labels audit-only.", "adopt"),
        ("governance_reviewer", "No replay output changes strategy acceptance or real-capital permission.", "adopt"),
    ]
    return [
        {
            "task_id": "Task1668",
            "expert_review_id": f"THESISACT1668-{idx:03d}",
            "expert_role": role,
            "critique": critique,
            "implementation_decision": decision,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, critique, decision) in enumerate(rows, 1)
    ]


def keyed(rows: list[dict[str, str]], key: str = "trade_spec_id") -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def selected_specs() -> list[dict[str, str]]:
    return read_csv(TASK1518 / "task1524_policy_specs_final.csv")


def actions_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in read_csv(TASK1558 / "task1561_damage_action_panel.csv")}


def l2_by_spec() -> dict[str, dict[str, str]]:
    return keyed(read_csv(TASK1488 / "task1491_l2_semantic_v6_panel.csv"))


def l4_by_spec() -> dict[str, dict[str, str]]:
    return keyed(read_csv(TASK1618 / "task1624_l4_payoff_thesis_cards.csv"))


def rerisk_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in read_csv(TASK1618 / "task1625_l5_rerisk_state_panel.csv")}


def price_return(frame: pd.DataFrame | None, start: date, end: date) -> float | None:
    if frame is None:
        return None
    start_close = replay.close_on_or_before(frame, start)
    end_close = replay.close_on_or_before(frame, end)
    if not start_close or not end_close:
        return None
    return pct_return(start_close[1], end_close[1])


def classify_drawdown(stock_ret: float | None, qqq_ret: float | None) -> tuple[str, float]:
    if stock_ret is None:
        return "no_price_damage", 0.0
    if qqq_ret is None:
        rel = stock_ret
    else:
        rel = stock_ret - qqq_ret
    if stock_ret > -0.04:
        return "minor_noise", rel
    if qqq_ret is not None and qqq_ret <= -0.04 and rel >= -0.08:
        return "market_or_sector_linked_selloff", rel
    if rel <= -0.10:
        return "idiosyncratic_breakdown", rel
    return "stock_drawdown_unconfirmed", rel


def build_market_context_panel() -> list[dict[str, object]]:
    specs = damage.trade_specs_by_id()
    actions = actions_by_key()
    price_cache: dict[str, pd.DataFrame | None] = {}
    qqq = replay.load_price("QQQ", price_cache)
    rows: list[dict[str, object]] = []
    for idx, selected in enumerate(selected_specs(), 1):
        spec = specs[selected["trade_spec_id"]]
        entry_after = parse_date(spec.get("entry_after_date")) or date(1970, 1, 1)
        action = actions.get((selected["policy_variant_id"], selected["trade_spec_id"]), {})
        event_date = parse_date(action.get("damage_reduce_date")) or parse_date(action.get("damage_exit_date"))
        frame = replay.load_price(selected["symbol"], price_cache)
        stock_ret = price_return(frame, entry_after, event_date) if event_date else None
        qqq_ret = price_return(qqq, entry_after, event_date) if event_date else None
        classification, relative = classify_drawdown(stock_ret, qqq_ret)
        rows.append(
            {
                "task_id": "Task1669",
                "market_context_id": f"THESISMKT1669-{idx:06d}",
                "policy_variant_id": selected["policy_variant_id"],
                "trade_spec_id": selected["trade_spec_id"],
                "candidate_source_id": selected["candidate_source_id"],
                "symbol": selected["symbol"],
                "decision_asof_ts": selected["decision_asof_ts"],
                "event_date": event_date.isoformat() if event_date else "",
                "stock_return_to_event": round(stock_ret, 8) if stock_ret is not None else "",
                "qqq_return_to_event": round(qqq_ret, 8) if qqq_ret is not None else "",
                "relative_return_to_event": round(relative, 8),
                "drawdown_cause": classification,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_thesis_integrity_panel(market_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    l2 = l2_by_spec()
    l4 = l4_by_spec()
    rerisk = rerisk_by_key()
    rows: list[dict[str, object]] = []
    for idx, selected in enumerate(selected_specs(), 1):
        spec_id = selected["trade_spec_id"]
        l2_row = l2.get(spec_id, {})
        l4_row = l4.get(spec_id, {})
        rr = rerisk.get((selected["policy_variant_id"], spec_id), {})
        alpha = to_float(l4_row.get("alpha_left_score"))
        event_family = l2_row.get("event_family", "unknown")
        payoff_mechanism = l4_row.get("payoff_mechanism", "unknown")
        source_damage = str(rr.get("source_damage_present", "0")) == "1"
        payoff_open = str(rr.get("payoff_still_open", "0")) == "1" or l4_row.get("thesis_expiry_state") == "open_or_unknown"
        source_confirmed = str(rr.get("source_confirmed", "0")) == "1"
        absorption = l4_row.get("absorption_persistence_state", "")
        weak_thesis = selected["thesis_state"] in {"confirmation_wait", "source_gap_watch"} or alpha < 0
        terminal_family = event_family in {"survival", "dilution"} or "dilution" in payoff_mechanism or "cash_runway" in payoff_mechanism
        thesis_survives = (
            not source_damage
            and payoff_open
            and source_confirmed
            and selected["thesis_state"] in {"active_thesis", "confirmed_thesis"}
            and alpha >= 6
            and not terminal_family
        )
        rows.append(
            {
                "task_id": "Task1670",
                "thesis_integrity_id": f"THESISINT1670-{idx:06d}",
                "policy_variant_id": selected["policy_variant_id"],
                "trade_spec_id": spec_id,
                "candidate_source_id": selected["candidate_source_id"],
                "symbol": selected["symbol"],
                "decision_asof_ts": selected["decision_asof_ts"],
                "thesis_state": selected["thesis_state"],
                "event_family": event_family,
                "payoff_mechanism": payoff_mechanism,
                "surprise_quality": l4_row.get("surprise_quality", ""),
                "absorption_persistence_state": absorption,
                "alpha_left_score": round(alpha, 6),
                "source_confirmed": "1" if source_confirmed else "0",
                "source_damage_present": "1" if source_damage else "0",
                "payoff_still_open": "1" if payoff_open else "0",
                "weak_thesis_flag": "1" if weak_thesis else "0",
                "terminal_family_flag": "1" if terminal_family else "0",
                "thesis_survives_damage": "1" if thesis_survives else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_exit_quorum_panel(market_rows: list[dict[str, object]], thesis_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    market = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in market_rows}
    thesis = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in thesis_rows}
    actions = actions_by_key()
    rows: list[dict[str, object]] = []
    for idx, selected in enumerate(selected_specs(), 1):
        key = (selected["policy_variant_id"], selected["trade_spec_id"])
        action = actions.get(key, {})
        m = market.get(key, {})
        t = thesis.get(key, {})
        source_evidence = str(t.get("source_damage_present", "0")) == "1"
        price_breakdown = action.get("price_exit_date", "") not in {"", "nan"} or (
            m.get("drawdown_cause") == "idiosyncratic_breakdown" and to_float(m.get("relative_return_to_event")) <= -0.12
        )
        thesis_weak = str(t.get("weak_thesis_flag", "0")) == "1"
        terminal = str(t.get("terminal_family_flag", "0")) == "1"
        absorption_fail = t.get("absorption_persistence_state") == "reversed" and to_float(t.get("alpha_left_score")) < 5
        evidence_count = sum([source_evidence, price_breakdown, thesis_weak, terminal, absorption_fail])
        exit_allowed = evidence_count >= 2
        rows.append(
            {
                "task_id": "Task1671",
                "exit_quorum_id": f"THESISEXIT1671-{idx:06d}",
                "policy_variant_id": selected["policy_variant_id"],
                "trade_spec_id": selected["trade_spec_id"],
                "candidate_source_id": selected["candidate_source_id"],
                "symbol": selected["symbol"],
                "decision_asof_ts": selected["decision_asof_ts"],
                "source_evidence": "1" if source_evidence else "0",
                "price_breakdown_evidence": "1" if price_breakdown else "0",
                "thesis_weak_evidence": "1" if thesis_weak else "0",
                "terminal_family_evidence": "1" if terminal else "0",
                "absorption_failure_evidence": "1" if absorption_fail else "0",
                "exit_evidence_count": evidence_count,
                "exit_allowed": "1" if exit_allowed else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def recovery_after_reduce(frame: pd.DataFrame | None, reduce_date: date, planned_exit: date, reduce_price: float) -> tuple[date | None, float | None, float]:
    if frame is None:
        return None, None, 0.0
    candidate = replay.close_n_sessions_after(frame, reduce_date, 7, planned_exit)
    if not candidate:
        return None, None, 0.0
    return candidate[0], candidate[1], pct_return(reduce_price, candidate[1])


def decide_action(
    selected: dict[str, str],
    base_action: dict[str, str],
    market: dict[str, object],
    thesis: dict[str, object],
    quorum: dict[str, object],
) -> dict[str, object]:
    base = base_action.get("damage_action", "hold")
    reason = base_action.get("damage_reason", "hold")
    source_damage = str(thesis.get("source_damage_present", "0")) == "1"
    thesis_survives = str(thesis.get("thesis_survives_damage", "0")) == "1"
    exit_allowed = str(quorum.get("exit_allowed", "0")) == "1"
    cause = str(market.get("drawdown_cause", "no_price_damage"))
    action = "hold"
    reduce_fraction = 0.0
    reduce_date = ""
    exit_date = ""

    if base == "no_reentry":
        return {
            "action": "no_reentry",
            "reason": "prior_no_reentry_cooldown_preserved",
            "reduce_fraction": 0.0,
            "reduce_date": "",
            "exit_date": "",
        }
    if exit_allowed:
        action = "exit"
        reason = "exit_quorum_met"
        exit_date = base_action.get("damage_exit_date") or base_action.get("source_damage_date") or base_action.get("price_exit_date") or ""
    elif source_damage:
        action = "reduce"
        reason = "source_damage_without_exit_quorum_reduce"
        reduce_fraction = 0.5
        reduce_date = base_action.get("source_damage_date", "")
    elif base == "reduce":
        if cause == "market_or_sector_linked_selloff" and thesis_survives:
            action = "hold"
            reason = "market_linked_selloff_thesis_survives_hold"
        elif cause == "idiosyncratic_breakdown" and not thesis_survives:
            action = "reduce"
            reason = "idiosyncratic_breakdown_thesis_not_confirmed_reduce"
            reduce_fraction = 0.5
            reduce_date = base_action.get("damage_reduce_date", "")
        elif thesis_survives:
            action = "reduce"
            reason = "thesis_survives_uncertain_drawdown_soft_reduce"
            reduce_fraction = 0.25
            reduce_date = base_action.get("damage_reduce_date", "")
        else:
            action = "reduce"
            reason = "unconfirmed_drawdown_reduce"
            reduce_fraction = 0.25
            reduce_date = base_action.get("damage_reduce_date", "")
    elif base == "exit":
        action = "reduce"
        reason = "exit_without_quorum_demoted_to_reduce"
        reduce_fraction = 0.5
        reduce_date = base_action.get("source_damage_date") or base_action.get("damage_exit_date", "")
    else:
        action = "hold"
        reason = "hold_preserved"

    return {
        "action": action,
        "reason": reason,
        "reduce_fraction": reduce_fraction,
        "reduce_date": reduce_date,
        "exit_date": exit_date,
    }


def run_replay(
    market_rows: list[dict[str, object]],
    thesis_rows: list[dict[str, object]],
    quorum_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    specs = damage.trade_specs_by_id()
    actions = actions_by_key()
    exits = damage.exit_by_key()
    market = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in market_rows}
    thesis = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in thesis_rows}
    quorum = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in quorum_rows}
    by_policy_decision: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in selected_specs():
        by_policy_decision[(row["policy_variant_id"], row["decision_asof_ts"])].append(row)
    cache: dict[str, pd.DataFrame | None] = {}
    revisions: list[dict[str, object]] = []
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    revision_idx = 1
    trade_idx = 1
    event_idx = 1
    for policy_id, policy in POLICIES.items():
        source_policy = policy["source_policy"]
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in by_policy_decision if key[0] == source_policy}):
            items = by_policy_decision[(source_policy, decision_ts)]
            base_alloc = capital / int(policy["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            for selected in items:
                key = (source_policy, selected["trade_spec_id"])
                base_action = actions.get(key, {})
                decision = decide_action(selected, base_action, market.get(key, {}), thesis.get(key, {}), quorum.get(key, {}))
                revisions.append(
                    {
                        "task_id": "Task1672",
                        "revision_id": f"THESISREV1672-{revision_idx:06d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "base_action": base_action.get("damage_action", ""),
                        "thesis_aware_action": decision["action"],
                        "thesis_aware_reason": decision["reason"],
                        "drawdown_cause": market.get(key, {}).get("drawdown_cause", ""),
                        "exit_evidence_count": quorum.get(key, {}).get("exit_evidence_count", ""),
                        "thesis_survives_damage": thesis.get(key, {}).get("thesis_survives_damage", ""),
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
                revision_idx += 1
                if decision["action"] == "no_reentry":
                    continue
                spec = specs[selected["trade_spec_id"]]
                frame = replay.load_price(selected["symbol"], cache)
                entry_after = parse_date(spec.get("entry_after_date")) or date(1970, 1, 1)
                scheduled_exit = parse_date(spec.get("exit_on_or_before_date")) or entry_after
                entry = replay.price_on_or_after(frame, entry_after)
                if not entry:
                    continue
                entry_date, entry_price = entry
                planned_close = damage.base_planned_close(frame, entry_date, scheduled_exit, exits.get(key, {}))
                if not planned_close:
                    continue
                planned_exit_date, planned_exit_price = planned_close
                size_multiplier = to_float(selected.get("position_size_cap_multiplier"), 1.0)
                allocated = base_alloc * size_multiplier
                reduced_capital = 0.0
                final_capital = allocated
                reduce_pnl = 0.0
                final_pnl = 0.0
                rerisk_pnl = 0.0
                rerisk_fraction = 0.0
                rerisk_date = ""
                actual_exit_date = planned_exit_date
                actual_exit_price = planned_exit_price
                if decision["action"] == "exit":
                    exit_date = parse_date(decision["exit_date"]) or planned_exit_date
                    close = replay.close_on_or_before(frame, exit_date)
                    actual_exit_date = close[0] if close else planned_exit_date
                    actual_exit_price = close[1] if close else planned_exit_price
                    final_pnl = allocated * net_return(entry_price, actual_exit_price)
                elif decision["action"] == "reduce" and to_float(decision["reduce_fraction"]) > 0:
                    reduce_fraction = to_float(decision["reduce_fraction"])
                    reduce_date = parse_date(decision["reduce_date"]) or planned_exit_date
                    reduce_close = replay.close_on_or_before(frame, reduce_date)
                    reduce_exit_date = reduce_close[0] if reduce_close else planned_exit_date
                    reduce_exit_price = reduce_close[1] if reduce_close else planned_exit_price
                    reduced_capital = allocated * reduce_fraction
                    final_capital = allocated - reduced_capital
                    reduce_pnl = reduced_capital * net_return(entry_price, reduce_exit_price)
                    remain_fraction = 1.0 - reduce_fraction
                    rr_allowed = policy["rerisk_fraction"] > 0 and thesis.get(key, {}).get("thesis_survives_damage") == "1"
                    rec_date, rec_price, recovery_return = recovery_after_reduce(frame, reduce_exit_date, planned_exit_date, reduce_exit_price)
                    if rr_allowed and rec_date and rec_price and recovery_return >= 0.03:
                        rerisk_fraction = min(float(policy["rerisk_fraction"]), reduce_fraction)
                        remain_fraction += rerisk_fraction
                        rerisk_date = rec_date.isoformat()
                        rerisk_pnl = allocated * rerisk_fraction * net_return(rec_price, planned_exit_price)
                        events.append(
                            {
                                "task_id": "Task1673",
                                "rerisk_event_id": f"THESISRERISK1673-{event_idx:06d}",
                                "policy_variant_id": policy_id,
                                "source_policy_variant_id": source_policy,
                                "trade_spec_id": selected["trade_spec_id"],
                                "symbol": selected["symbol"],
                                "decision_asof_ts": decision_ts,
                                "reduce_date": reduce_exit_date.isoformat(),
                                "rerisk_date": rerisk_date,
                                "rerisk_fraction": rerisk_fraction,
                                "recovery_return_at_rerisk": round(recovery_return, 8),
                                "thesis_survives_damage": "1",
                                "outcome_used_for_assignment": "0",
                                "outcome_used_for_audit_only": "1",
                                "authority": AUTHORITY,
                            }
                        )
                        event_idx += 1
                    final_pnl = allocated * remain_fraction * net_return(entry_price, planned_exit_price)
                else:
                    final_pnl = allocated * net_return(entry_price, planned_exit_price)
                pnl = reduce_pnl + final_pnl + rerisk_pnl
                period_pnl += pnl
                capital += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task1673",
                        "trade_row_id": f"THESISTRADE1673-{trade_idx:06d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "entry_date": entry_date.isoformat(),
                        "entry_price": round(entry_price, 6),
                        "planned_exit_date": planned_exit_date.isoformat(),
                        "actual_exit_date": actual_exit_date.isoformat(),
                        "actual_exit_price": round(actual_exit_price, 6),
                        "thesis_aware_action": decision["action"],
                        "thesis_aware_reason": decision["reason"],
                        "position_size_cap_multiplier": round(size_multiplier, 4),
                        "capital_allocated": round(allocated, 4),
                        "reduced_capital": round(reduced_capital, 4),
                        "final_capital": round(final_capital, 4),
                        "reduce_pnl": round(reduce_pnl, 4),
                        "final_pnl": round(final_pnl, 4),
                        "rerisk_fraction": round(rerisk_fraction, 4),
                        "rerisk_date": rerisk_date,
                        "rerisk_pnl": round(rerisk_pnl, 4),
                        "pnl": round(pnl, 4),
                        "net_return": round(pnl / allocated, 8) if allocated else 0.0,
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            equity.append(
                {
                    "task_id": "Task1673",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "allocated_count": allocated_count,
                    "authority": AUTHORITY,
                }
            )
    return revisions, trades, equity, events


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    eq_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        groups[str(row["policy_variant_id"])].append(row)
    for row in equity:
        eq_groups[str(row["policy_variant_id"])].append(row)
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(eq_groups.items()):
        tr_rows = groups[policy_id]
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end = max(parse_date(row["actual_exit_date"]) or start for row in tr_rows)
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        rows.append(
            {
                "task_id": "Task1674",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "hold_count": sum(1 for row in tr_rows if row["thesis_aware_action"] == "hold"),
                "reduce_count": sum(1 for row in tr_rows if row["thesis_aware_action"] == "reduce"),
                "exit_count": sum(1 for row in tr_rows if row["thesis_aware_action"] == "exit"),
                "rerisk_trade_count": sum(1 for row in tr_rows if to_float(row["rerisk_fraction"]) > 0),
                "rerisk_total_pnl": round(sum(to_float(row["rerisk_pnl"]) for row in tr_rows), 4),
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
                "task_id": "Task1675",
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


def failure_rows(market_rows: list[dict[str, object]], quorum_rows: list[dict[str, object]], metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for label, counts in [
        ("drawdown_cause", Counter(str(row["drawdown_cause"]) for row in market_rows)),
        ("exit_evidence_count", Counter(str(row["exit_evidence_count"]) for row in quorum_rows)),
    ]:
        for reason, count in counts.most_common():
            rows.append({"task_id": "Task1676", "failure_id": f"THESISFAIL1676-{idx:04d}", "failure_area": label, "reason": reason, "row_count": count, "authority": AUTHORITY})
            idx += 1
    for row in metrics:
        if row["target_cagr_30pct_met"] != "1" or row["target_mdd_minus30pct_met"] != "1":
            rows.append(
                {
                    "task_id": "Task1676",
                    "failure_id": f"THESISFAIL1676-{idx:04d}",
                    "failure_area": "target_failure",
                    "policy_variant_id": row["policy_variant_id"],
                    "cagr": row["cagr"],
                    "max_drawdown": row["max_drawdown"],
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def gate_closeout(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gate = [
        {
            "task_id": "Task1686",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "cagr_30pct_met_by_any": "1" if any(row["target_cagr_30pct_met"] == "1" for row in metrics) else "0",
            "mdd_minus30pct_met_by_any": "1" if any(row["target_mdd_minus30pct_met"] == "1" for row in metrics) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "l5_thesis_aware_action_engine_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1687",
            "verdict": "l5_thesis_aware_action_engine_implemented_not_accepted",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit whether market-linked holds and exit quorum reduce return too much before adding stronger source-confirmed alpha entry",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metrics: list[dict[str, object]], split: list[dict[str, object]], failures: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1668-1687 L5 Thesis-Aware Action Engine",
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
        "| Policy | Final | CAGR | MDD | Trades | Hold | Reduce | Exit | Rerisk | Rerisk PnL | QQQ Beat | CAGR Target | MDD Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['trade_count']} | {row['hold_count']} | {row['reduce_count']} | {row['exit_count']} | {row['rerisk_trade_count']} | {row['rerisk_total_pnl']} | {row['beats_qqq']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |"
        )
    lines.extend(["", "Split/OOS diagnostics:", "", "| Policy | Window | Final | Return | MDD |", "| --- | --- | ---: | ---: | ---: |"])
    for row in split:
        lines.append(f"| `{row['policy_variant_id']}` | {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Reduce now checks drawdown cause before cutting.",
            "2. Exit now requires a two-evidence quorum.",
            "3. Re-risk now requires thesis survival plus runtime recovery.",
            "4. Hold is preserved when drawdown is market-linked and thesis survives.",
            "5. The replay is still diagnostic and does not approve strategy.",
            "",
            "## Failure / Blocker Summary",
            "",
        ]
    )
    for row in failures[:20]:
        lines.append(f"- `{row['failure_area']}`: {row.get('reason', row.get('policy_variant_id', ''))} count={row.get('row_count','')} cagr={row.get('cagr','')} mdd={row.get('max_drawdown','')}")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task1668_expert_review.csv`",
            "- `task1669_drawdown_cause_panel.csv`",
            "- `task1670_thesis_integrity_panel.csv`",
            "- `task1671_exit_quorum_panel.csv`",
            "- `task1672_action_revision_panel.csv`",
            "- `task1673_thesis_aware_replay_trades.csv/equity/events`",
            "- `task1674_thesis_aware_replay_metrics.csv`",
            "- `task1675_split_oos_metrics.csv`",
            "- `task1676_failure_attribution.csv`",
            "- `task1686_acceptance_gate.csv`",
            "- `task1687_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1668_1687_l5_thesis_aware_action_engine_validate.py`",
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
    market = build_market_context_panel()
    thesis = build_thesis_integrity_panel(market)
    quorum = build_exit_quorum_panel(market, thesis)
    revisions, trades, equity, events = run_replay(market, thesis, quorum)
    metrics = build_metrics(trades, equity)
    splits = split_rows(equity)
    failures = failure_rows(market, quorum, metrics)
    gate, closeout = gate_closeout(metrics)
    outputs = [
        ("task1668_expert_review.csv", experts),
        ("task1669_drawdown_cause_panel.csv", market),
        ("task1670_thesis_integrity_panel.csv", thesis),
        ("task1671_exit_quorum_panel.csv", quorum),
        ("task1672_action_revision_panel.csv", revisions),
        ("task1673_thesis_aware_replay_trades.csv", trades),
        ("task1673_thesis_aware_replay_equity.csv", equity),
        ("task1673_thesis_aware_rerisk_events.csv", events),
        ("task1674_thesis_aware_replay_metrics.csv", metrics),
        ("task1675_split_oos_metrics.csv", splits),
        ("task1676_failure_attribution.csv", failures),
        ("task1686_acceptance_gate.csv", gate),
        ("task1687_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1687_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(metrics, splits, failures, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1668_1687] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
