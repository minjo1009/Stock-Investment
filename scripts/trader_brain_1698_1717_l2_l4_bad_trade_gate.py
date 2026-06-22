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
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK1518 = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
TASK1618 = ROOT / "data/artifacts/task_1618_1647_expectation_payoff_rerisk_bridge"
TASK1668 = ROOT / "data/artifacts/task_1668_1687_l5_thesis_aware_action_engine"
TASK1688 = ROOT / "data/artifacts/task_1688_1697_l2_l4_gate_source_audit"
TASK1428 = ROOT / "data/artifacts/task_1428_1447_full_ruler_source_time_acquisition"

OUT_DIR = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
REPORT_DIR = ROOT / "docs/reports/task_1698_1717_l2_l4_bad_trade_gate"
REPORT = REPORT_DIR / "task_1698_1717_l2_l4_bad_trade_gate.md"
DECISION = REPORT_DIR / "task_1698_1717_decision.csv"

AUTHORITY = "DIAGNOSTIC_L2_L4_BAD_TRADE_GATE_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "bad_trade_gate_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3},
    "bad_trade_gate_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5},
}

BASELINE_REPLAY_POLICY = {
    "bad_trade_gate_top3_v1": "thesis_aware_no_rerisk_top3_v1",
    "bad_trade_gate_top5_v1": "thesis_aware_no_rerisk_top5_v1",
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


def net_return(start: float, end: float) -> float:
    return pct_return(start, end) - ROUND_TRIP_COST_BPS / 10000.0


def by_trade_spec(path: Path) -> dict[str, dict[str, str]]:
    return {row["trade_spec_id"]: row for row in read_csv(path)}


def expert_review_rows() -> list[dict[str, object]]:
    source_reviews = read_csv(TASK1688 / "task1688_expert_source_review.csv")
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(source_reviews, 1):
        rows.append(
            {
                "task_id": "Task1698",
                "expert_review_id": f"BADGATE1698-{idx:03d}",
                "expert_role": row["role"],
                "verdict": row["verdict"],
                "source_anchor": row["source_anchor"],
                "implementation_takeaway": row["next_requirement"],
                "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
                "authority": AUTHORITY,
            }
        )
    return rows


def price_snapshot(frame: pd.DataFrame | None, decision_date: date) -> dict[str, float | str]:
    if frame is None:
        return {
            "price_asof": "",
            "avg_dollar_volume_20d": "",
            "prior_return_63d": "",
            "prior_drawdown_126d": "",
            "realized_vol_63d": "",
            "price_history_state": "missing_price_history",
        }
    hist = frame[frame["Date"] <= decision_date].tail(126).copy()
    if hist.empty:
        return {
            "price_asof": "",
            "avg_dollar_volume_20d": "",
            "prior_return_63d": "",
            "prior_drawdown_126d": "",
            "realized_vol_63d": "",
            "price_history_state": "missing_price_history",
        }
    price = float(hist.iloc[-1]["Close"])
    avg20 = hist.tail(20).assign(dollar_volume=lambda x: x["Close"] * x["Volume"])["dollar_volume"].mean()
    if len(hist) >= 64:
        prior63 = pct_return(float(hist.iloc[-64]["Close"]), price)
    else:
        prior63 = 0.0
    high126 = float(hist["Close"].max())
    drawdown126 = price / high126 - 1.0 if high126 > 0 else 0.0
    returns = hist["Close"].pct_change().dropna().tail(63)
    vol63 = float(returns.std() * (252**0.5)) if not returns.empty else 0.0
    return {
        "price_asof": round(price, 6),
        "avg_dollar_volume_20d": round(float(avg20), 4) if pd.notna(avg20) else "",
        "prior_return_63d": round(prior63, 8),
        "prior_drawdown_126d": round(drawdown126, 8),
        "realized_vol_63d": round(vol63, 8),
        "price_history_state": "price_history_present",
    }


def build_collapse_risk_panel() -> list[dict[str, object]]:
    l2_rows = read_csv(TASK1488 / "task1491_l2_semantic_v6_panel.csv")
    l4_payoff = by_trade_spec(TASK1618 / "task1624_l4_payoff_thesis_cards.csv")
    cache: dict[str, pd.DataFrame | None] = {}
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(l2_rows, 1):
        decision_date = replay.parse_ts(row["decision_asof_ts"]).date()
        frame = replay.load_price(row["symbol"], cache)
        snap = price_snapshot(frame, decision_date)
        payoff = l4_payoff.get(row["trade_spec_id"], {})
        event_family = row.get("event_family", "unknown")
        payoff_mechanism = payoff.get("payoff_mechanism", "unknown")
        expectation = row.get("expectation_v6_state", "")
        absorption = row.get("absorption_v6_state", "")
        price = to_float(snap["price_asof"])
        dollar_vol = to_float(snap["avg_dollar_volume_20d"])
        prior_dd = to_float(snap["prior_drawdown_126d"])
        prior_ret = to_float(snap["prior_return_63d"])
        vol = to_float(snap["realized_vol_63d"])
        low_price = price > 0 and price < 5
        sub_dollar_liquidity = dollar_vol > 0 and dollar_vol < 5_000_000
        listing_risk = price > 0 and (price < 1.25 or (price < 2.0 and prior_dd <= -0.35))
        terminal_language = event_family == "survival" or "cash_runway" in payoff_mechanism
        dilution_language = event_family in {"dilution", "financing"} or "dilution" in payoff_mechanism
        market_rejected = absorption in {"market_rejection_or_reversal", "weak_absorption"} or payoff.get("absorption_persistence_state") == "reversed"
        positive_payoff = event_family == "positive" or payoff_mechanism == "revenue_or_customer_validation"
        theme_valid_vol = vol >= 0.70 and positive_payoff and not listing_risk and not terminal_language and price >= 3

        risk_points = 0.0
        if terminal_language:
            risk_points += 35
        if dilution_language:
            risk_points += 22
        if listing_risk:
            risk_points += 35
        elif low_price:
            risk_points += 12
        if sub_dollar_liquidity:
            risk_points += 10
        if prior_dd <= -0.45:
            risk_points += 16
        if vol >= 1.10:
            risk_points += 10
        if market_rejected:
            risk_points += 12
        if expectation == "negative_expectation_proxy":
            risk_points += 10
        if theme_valid_vol:
            risk_points -= 18
        risk_points = max(0.0, min(100.0, risk_points))

        if listing_risk and (terminal_language or market_rejected):
            bucket = "listing_compliance_risk"
        elif terminal_language and risk_points >= 45:
            bucket = "terminal_business_risk"
        elif dilution_language and risk_points >= 34:
            bucket = "dilution_pressure"
        elif event_family == "financing" or "financing" in payoff_mechanism:
            bucket = "financing_stress"
        elif theme_valid_vol:
            bucket = "theme_volatility"
        elif vol >= 0.70 or prior_dd <= -0.30:
            bucket = "ordinary_volatility"
        else:
            bucket = "ordinary_pass"

        if bucket in {"terminal_business_risk", "listing_compliance_risk"} and not positive_payoff:
            gate = "block"
        elif bucket in {"dilution_pressure", "financing_stress", "listing_compliance_risk"}:
            gate = "cap"
        elif bucket == "terminal_business_risk":
            gate = "cap"
        else:
            gate = "allow"

        rows.append(
            {
                "task_id": "Task1699",
                "collapse_risk_id": f"COLLAPSE1699-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "event_family": event_family,
                "payoff_mechanism": payoff_mechanism,
                "expectation_state": expectation,
                "absorption_state": absorption,
                "price_asof": snap["price_asof"],
                "avg_dollar_volume_20d": snap["avg_dollar_volume_20d"],
                "prior_return_63d": snap["prior_return_63d"],
                "prior_drawdown_126d": snap["prior_drawdown_126d"],
                "realized_vol_63d": snap["realized_vol_63d"],
                "collapse_risk_bucket": bucket,
                "collapse_risk_score": round(risk_points, 6),
                "pre_entry_gate": gate,
                "volatility_not_terminal_flag": "1" if bucket in {"theme_volatility", "ordinary_volatility"} else "0",
                "terminal_risk_flag": "1" if bucket in {"terminal_business_risk", "listing_compliance_risk"} else "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_payoff_quality_panel(collapse_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    l2 = by_trade_spec(TASK1488 / "task1491_l2_semantic_v6_panel.csv")
    l4_v6 = by_trade_spec(TASK1488 / "task1493_l4_thesis_cards_v6.csv")
    l4_payoff = by_trade_spec(TASK1618 / "task1624_l4_payoff_thesis_cards.csv")
    ruler_path = TASK1428 / "task1445_payoff_ranker_v4.csv"
    ruler = by_trade_spec(ruler_path if ruler_path.exists() else TASK1428 / "task1425_payoff_ranker_v3.csv")
    rows: list[dict[str, object]] = []
    for idx, risk in enumerate(collapse_rows, 1):
        spec_id = str(risk["trade_spec_id"])
        l2_row = l2.get(spec_id, {})
        l4_row = l4_v6.get(spec_id, {})
        payoff = l4_payoff.get(spec_id, {})
        ruler_row = ruler.get(spec_id, {})
        event_family = l2_row.get("event_family", "unknown")
        expectation = l2_row.get("expectation_v6_state", "")
        absorption = l2_row.get("absorption_v6_state", "")
        materiality = l2_row.get("materiality_v6_state", "")
        independence = l2_row.get("source_independence_v2_state", "")
        payoff_mechanism = payoff.get("payoff_mechanism", "")
        alpha_left = to_float(payoff.get("alpha_left_score"))
        semantic_score = to_float(l2_row.get("semantic_v6_score"))
        ruler_score = to_float(ruler_row.get("ruler_payoff_rank_score"), to_float(ruler_row.get("integrated_ruler_score")))
        risk_score = to_float(risk.get("collapse_risk_score"))

        score = 0.35 * semantic_score + 0.30 * ruler_score + 2.0 * alpha_left
        if event_family == "positive":
            score += 12
        if payoff_mechanism == "revenue_or_customer_validation":
            score += 10
        if expectation == "true_surprise_proxy":
            score += 16
        elif expectation == "guidance_change_proxy":
            score += 10
        elif expectation == "good_words_only":
            score += 2
        elif expectation == "negative_expectation_proxy":
            score -= 12
        if absorption == "sustained_market_acceptance" or payoff.get("absorption_persistence_state") == "persistent":
            score += 14
        elif absorption == "initial_reaction_only":
            score += 4
        elif absorption in {"market_rejection_or_reversal", "weak_absorption"}:
            score -= 12
        if "independent_non_issuer" in independence:
            score += 8
        if materiality == "conditional_positive_materiality":
            score += 5
        if risk.get("collapse_risk_bucket") in {"terminal_business_risk", "listing_compliance_risk"}:
            score -= min(28, risk_score * 0.35)
        elif risk.get("collapse_risk_bucket") in {"dilution_pressure", "financing_stress"}:
            score -= min(18, risk_score * 0.25)
        elif risk.get("collapse_risk_bucket") == "theme_volatility":
            score += 4

        if risk.get("pre_entry_gate") == "block":
            quality = "blocked_terminal_or_listing_risk"
        elif score >= 70:
            quality = "top3_payoff_candidate"
        elif score >= 52:
            quality = "eligible_payoff_candidate"
        elif score >= 38:
            quality = "watch_or_cap_candidate"
        else:
            quality = "low_payoff_candidate"

        rows.append(
            {
                "task_id": "Task1700",
                "payoff_quality_id": f"PAYQUAL1700-{idx:07d}",
                "candidate_source_id": risk["candidate_source_id"],
                "trade_spec_id": spec_id,
                "symbol": risk["symbol"],
                "decision_asof_ts": risk["decision_asof_ts"],
                "event_family": event_family,
                "payoff_mechanism": payoff_mechanism,
                "expectation_state": expectation,
                "absorption_state": absorption,
                "materiality_state": materiality,
                "source_independence_state": independence,
                "semantic_v6_score": round(semantic_score, 6),
                "ruler_payoff_score": round(ruler_score, 6),
                "alpha_left_score": round(alpha_left, 6),
                "collapse_risk_bucket": risk["collapse_risk_bucket"],
                "collapse_risk_score": round(risk_score, 6),
                "payoff_quality_score": round(score, 6),
                "payoff_quality_bucket": quality,
                "pre_entry_gate": risk["pre_entry_gate"],
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_l3_edges(payoff_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for row in payoff_rows:
        edge_specs = [
            ("event_to_payoff", "increases_payoff" if row["event_family"] == "positive" else "routes_to_review", row["event_family"]),
            ("expectation_to_payoff", "increases_payoff" if row["expectation_state"] in {"true_surprise_proxy", "guidance_change_proxy"} else "caps_payoff", row["expectation_state"]),
            ("absorption_to_confirmation", "increases_payoff" if row["absorption_state"] == "sustained_market_acceptance" else "caps_payoff", row["absorption_state"]),
            ("collapse_to_sizing", "routes_smaller_size" if row["pre_entry_gate"] == "cap" else ("invalidates_entry" if row["pre_entry_gate"] == "block" else "preserves_size"), row["collapse_risk_bucket"]),
            ("quality_to_l4", "promotes_candidate" if row["payoff_quality_bucket"] == "top3_payoff_candidate" else "ranks_candidate", row["payoff_quality_bucket"]),
        ]
        for edge_type, mechanism, evidence in edge_specs:
            rows.append(
                {
                    "task_id": "Task1701",
                    "mechanism_edge_id": f"RISKPAYEDGE1701-{idx:07d}",
                    "candidate_source_id": row["candidate_source_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "edge_type": edge_type,
                    "mechanism": mechanism,
                    "evidence_state": evidence,
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def baseline_policy_specs() -> list[dict[str, str]]:
    return read_csv(TASK1518 / "task1524_policy_specs_final.csv")


def build_candidate_compressor(payoff_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    by_spec = {str(row["trade_spec_id"]): row for row in payoff_rows}
    for row in payoff_rows:
        by_decision[str(row["decision_asof_ts"])].append(row)
    baseline = baseline_policy_specs()
    baseline_by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in baseline:
        if row["policy_variant_id"] in {"l5_operating_top3_v1", "l5_operating_top5_v1"}:
            baseline_by_key[(row["policy_variant_id"], row["decision_asof_ts"])].append(row)
    rows: list[dict[str, object]] = []
    idx = 1
    for policy_id, policy in POLICIES.items():
        source_policy = policy["source_policy"]
        slot_cap = int(policy["slot_cap"])
        for decision_ts in sorted(by_decision):
            candidates = sorted(
                [row for row in by_decision[decision_ts] if row["pre_entry_gate"] != "block"],
                key=lambda row: (-to_float(row["payoff_quality_score"]), to_float(by_spec[str(row["trade_spec_id"])].get("candidate_rank"), 999)),
            )
            baseline_items = baseline_by_key.get((source_policy, decision_ts), [])
            chosen: list[dict[str, object]] = []
            used: set[str] = set()
            for base in baseline_items:
                candidate = by_spec.get(base["trade_spec_id"])
                if not candidate:
                    continue
                if candidate["pre_entry_gate"] == "block":
                    replacement = next((cand for cand in candidates if str(cand["trade_spec_id"]) not in used), None)
                    if replacement:
                        chosen.append({**replacement, "selection_reason": "blocked_baseline_replaced"})
                        used.add(str(replacement["trade_spec_id"]))
                    continue
                chosen.append({**candidate, "selection_reason": "baseline_preserved"})
                used.add(str(candidate["trade_spec_id"]))
            while len(chosen) < slot_cap:
                replacement = next(
                    (
                        cand
                        for cand in candidates
                        if str(cand["trade_spec_id"]) not in used
                        and cand["payoff_quality_bucket"] == "top3_payoff_candidate"
                        and cand["collapse_risk_bucket"] in {"ordinary_pass", "theme_volatility"}
                        and to_float(cand["payoff_quality_score"]) >= 78
                    ),
                    None,
                )
                if not replacement:
                    break
                chosen.append({**replacement, "selection_reason": "high_confidence_open_slot_filled_by_payoff_rank"})
                used.add(str(replacement["trade_spec_id"]))
            if candidates and chosen:
                floor = min(to_float(row["payoff_quality_score"]) for row in chosen)
                upgrade = next(
                    (
                        cand
                        for cand in candidates
                        if str(cand["trade_spec_id"]) not in used
                        and to_float(cand["payoff_quality_score"]) >= floor + 10
                        and cand["payoff_quality_bucket"] in {"top3_payoff_candidate", "eligible_payoff_candidate"}
                    ),
                    None,
                )
                weakest_i = min(range(len(chosen)), key=lambda i: to_float(chosen[i]["payoff_quality_score"]))
                if upgrade and chosen[weakest_i]["selection_reason"] != "baseline_preserved":
                    used.discard(str(chosen[weakest_i]["trade_spec_id"]))
                    chosen[weakest_i] = {**upgrade, "selection_reason": "payoff_quality_upgrade"}
                    used.add(str(upgrade["trade_spec_id"]))
            chosen = sorted(chosen, key=lambda row: -to_float(row["payoff_quality_score"]))[:slot_cap]
            for rank, row in enumerate(chosen, 1):
                cap_multiplier = 1.0
                if row["pre_entry_gate"] == "cap":
                    cap_multiplier = 0.5
                elif row["collapse_risk_bucket"] in {"ordinary_volatility", "theme_volatility"} and row["payoff_quality_bucket"] == "low_payoff_candidate":
                    cap_multiplier = 0.5
                elif row["selection_reason"] == "high_confidence_open_slot_filled_by_payoff_rank":
                    cap_multiplier = 0.25
                rows.append(
                    {
                        "task_id": "Task1702",
                        "candidate_compressor_id": f"COMPRESS1702-{idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "slot_cap": slot_cap,
                        "candidate_source_id": row["candidate_source_id"],
                        "trade_spec_id": row["trade_spec_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "compressed_rank": rank,
                        "payoff_quality_score": row["payoff_quality_score"],
                        "payoff_quality_bucket": row["payoff_quality_bucket"],
                        "collapse_risk_bucket": row["collapse_risk_bucket"],
                        "pre_entry_gate": row["pre_entry_gate"],
                        "position_size_cap_multiplier": round(cap_multiplier, 4),
                        "selection_reason": row["selection_reason"],
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
                idx += 1
    return rows


def runtime_exit(
    frame: pd.DataFrame | None,
    qqq: pd.DataFrame | None,
    entry_date: date,
    planned_exit: date,
    entry_price: float,
    qqq_entry_price: float | None,
    risk_bucket: str,
    quality_bucket: str,
) -> tuple[str, str, date | None, float | None, float]:
    if frame is None:
        return "hold", "no_price_path_available", None, None, 0.0
    sub = frame[(frame["Date"] >= entry_date) & (frame["Date"] <= planned_exit)]
    if sub.empty:
        return "hold", "empty_price_path", None, None, 0.0
    for _, price_row in sub.iterrows():
        current_date = price_row["Date"]
        close = float(price_row["Close"])
        drawdown = close / entry_price - 1.0
        qqq_close = replay.close_on_or_before(qqq, current_date) if qqq is not None else None
        qqq_ret = pct_return(qqq_entry_price, qqq_close[1]) if qqq_entry_price and qqq_close else 0.0
        relative = drawdown - qqq_ret
        terminal = risk_bucket in {"terminal_business_risk", "listing_compliance_risk", "dilution_pressure", "financing_stress"}
        weak_quality = quality_bucket in {"low_payoff_candidate", "watch_or_cap_candidate", "blocked_terminal_or_listing_risk"}
        if terminal and weak_quality and drawdown <= -0.10 and relative <= -0.06:
            return "exit", "thesis_break_terminal_risk_plus_idiosyncratic_damage", current_date, close, 1.0
        if terminal and drawdown <= -0.14:
            return "reduce", "terminal_or_dilution_risk_runtime_damage_reduce", current_date, close, 0.5
        if weak_quality and drawdown <= -0.20 and relative <= -0.14:
            return "exit", "weak_payoff_deep_idiosyncratic_breakdown_exit", current_date, close, 1.0
        if weak_quality and drawdown <= -0.12 and relative <= -0.08:
            return "reduce", "weak_payoff_idiosyncratic_breakdown_reduce", current_date, close, 0.5
        if quality_bucket == "eligible_payoff_candidate" and drawdown <= -0.18 and relative <= -0.12:
            return "reduce", "eligible_payoff_relative_breakdown_reduce", current_date, close, 0.35
        if risk_bucket == "ordinary_volatility" and weak_quality and drawdown <= -0.18 and relative <= -0.12:
            return "reduce", "weak_payoff_idiosyncratic_breakdown_reduce", current_date, close, 0.35
    return "hold", "thesis_not_broken_hold_to_plan", None, None, 0.0


def replay_selected(compressor_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    specs = damage.trade_specs_by_id()
    baseline_trade = {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1668 / "task1673_thesis_aware_replay_trades.csv")
    }
    by_policy_decision: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in compressor_rows:
        by_policy_decision[(str(row["policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    cache: dict[str, pd.DataFrame | None] = {}
    qqq = replay.load_price("QQQ", cache)
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    actions: list[dict[str, object]] = []
    trade_idx = 1
    action_idx = 1
    for policy_id, policy in POLICIES.items():
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in by_policy_decision if key[0] == policy_id}):
            items = sorted(by_policy_decision[(policy_id, decision_ts)], key=lambda row: to_float(row["compressed_rank"]))
            base_alloc = capital / int(policy["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            for selected in items:
                spec = specs.get(str(selected["trade_spec_id"]), {})
                frame = replay.load_price(str(selected["symbol"]), cache)
                entry_after = parse_date(spec.get("entry_after_date")) or date(1970, 1, 1)
                scheduled_exit = parse_date(spec.get("exit_on_or_before_date")) or entry_after
                entry = replay.price_on_or_after(frame, entry_after)
                if not entry:
                    continue
                entry_date, entry_price = entry
                planned = replay.close_on_or_before(frame, scheduled_exit)
                if not planned:
                    continue
                planned_exit_date, planned_exit_price = planned[0], planned[1]
                qqq_entry = replay.price_on_or_after(qqq, entry_date)
                qqq_entry_price = qqq_entry[1] if qqq_entry else None
                base_replay = baseline_trade.get((BASELINE_REPLAY_POLICY[policy_id], str(selected["trade_spec_id"])))
                reuse_baseline_action = selected["selection_reason"] == "baseline_preserved" and base_replay is not None
                if reuse_baseline_action:
                    action = base_replay.get("thesis_aware_action", "hold")
                    reason = "task1668_thesis_aware_action_reused"
                    action_date = parse_date(base_replay.get("actual_exit_date")) if action in {"reduce", "exit"} else None
                    action_price = to_float(base_replay.get("actual_exit_price")) if action in {"reduce", "exit"} else None
                    reduce_fraction = 0.0
                else:
                    action, reason, action_date, action_price, reduce_fraction = runtime_exit(
                        frame,
                        qqq,
                        entry_date,
                        planned_exit_date,
                        entry_price,
                        qqq_entry_price,
                        str(selected["collapse_risk_bucket"]),
                        str(selected["payoff_quality_bucket"]),
                    )
                actions.append(
                    {
                        "task_id": "Task1703",
                        "runtime_action_id": f"THESISBREAK1703-{action_idx:07d}",
                        "policy_variant_id": policy_id,
                        "trade_spec_id": selected["trade_spec_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "runtime_action": action,
                        "runtime_action_reason": reason,
                        "runtime_action_date": action_date.isoformat() if action_date else "",
                        "collapse_risk_bucket": selected["collapse_risk_bucket"],
                        "payoff_quality_bucket": selected["payoff_quality_bucket"],
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
                action_idx += 1
                size_multiplier = to_float(selected["position_size_cap_multiplier"], 1.0)
                allocated = base_alloc * size_multiplier
                if reuse_baseline_action:
                    actual_exit_date = parse_date(base_replay.get("actual_exit_date")) or planned_exit_date
                    actual_exit_price = to_float(base_replay.get("actual_exit_price"), planned_exit_price)
                    net = to_float(base_replay.get("net_return"))
                    pnl = allocated * net
                    base_allocated = to_float(base_replay.get("capital_allocated"))
                    reduced_ratio = to_float(base_replay.get("reduced_capital")) / base_allocated if base_allocated > 0 else 0.0
                    reduced_capital = allocated * reduced_ratio
                    reduce_pnl = allocated * to_float(base_replay.get("reduce_pnl")) / base_allocated if base_allocated > 0 else 0.0
                    final_pnl = pnl - reduce_pnl
                elif action == "exit" and action_date and action_price:
                    actual_exit_date = action_date
                    actual_exit_price = action_price
                    pnl = allocated * net_return(entry_price, action_price)
                    reduced_capital = 0.0
                    reduce_pnl = 0.0
                    final_pnl = pnl
                elif action == "reduce" and action_date and action_price and reduce_fraction > 0:
                    actual_exit_date = planned_exit_date
                    actual_exit_price = planned_exit_price
                    reduced_capital = allocated * reduce_fraction
                    remaining_capital = allocated - reduced_capital
                    reduce_pnl = reduced_capital * net_return(entry_price, action_price)
                    final_pnl = remaining_capital * net_return(entry_price, planned_exit_price)
                    pnl = reduce_pnl + final_pnl
                else:
                    actual_exit_date = planned_exit_date
                    actual_exit_price = planned_exit_price
                    reduced_capital = 0.0
                    reduce_pnl = 0.0
                    final_pnl = allocated * net_return(entry_price, planned_exit_price)
                    pnl = final_pnl
                period_pnl += pnl
                capital += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task1704",
                        "trade_row_id": f"BADGATETRADE1704-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": selected["symbol"],
                        "decision_asof_ts": decision_ts,
                        "entry_date": entry_date.isoformat(),
                        "entry_price": round(entry_price, 6),
                        "planned_exit_date": planned_exit_date.isoformat(),
                        "actual_exit_date": actual_exit_date.isoformat(),
                        "actual_exit_price": round(actual_exit_price, 6),
                        "runtime_action": action,
                        "runtime_action_reason": reason,
                        "position_size_cap_multiplier": round(size_multiplier, 4),
                        "capital_allocated": round(allocated, 4),
                        "reduced_capital": round(reduced_capital, 4),
                        "reduce_pnl": round(reduce_pnl, 4),
                        "final_pnl": round(final_pnl, 4),
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
                    "task_id": "Task1704",
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


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    baseline = {row["policy_variant_id"]: row for row in read_csv(TASK1668 / "task1674_thesis_aware_replay_metrics.csv")}
    baseline_map = {
        "bad_trade_gate_top3_v1": "thesis_aware_no_rerisk_top3_v1",
        "bad_trade_gate_top5_v1": "thesis_aware_no_rerisk_top5_v1",
    }
    trade_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    eq_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trade_groups[str(row["policy_variant_id"])].append(row)
    for row in equity:
        eq_groups[str(row["policy_variant_id"])].append(row)
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(eq_groups.items()):
        tr_rows = trade_groups[policy_id]
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end = max(parse_date(row["actual_exit_date"]) or start for row in tr_rows)
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        base = baseline[baseline_map[policy_id]]
        rows.append(
            {
                "task_id": "Task1705",
                "policy_variant_id": policy_id,
                "baseline_policy_variant_id": baseline_map[policy_id],
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "hold_count": sum(1 for row in tr_rows if row["runtime_action"] == "hold"),
                "reduce_count": sum(1 for row in tr_rows if row["runtime_action"] == "reduce"),
                "exit_count": sum(1 for row in tr_rows if row["runtime_action"] == "exit"),
                "baseline_final_equity": base["final_equity"],
                "baseline_cagr": base["cagr"],
                "baseline_max_drawdown": base["max_drawdown"],
                "delta_final_equity": round(final - to_float(base["final_equity"]), 4),
                "delta_cagr": round(cagr - to_float(base["cagr"]), 6),
                "delta_mdd": round(mdd - to_float(base["max_drawdown"]), 6),
                "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
                "beats_task1668_baseline": "1" if final > to_float(base["final_equity"]) and mdd >= to_float(base["max_drawdown"]) else "0",
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
                "task_id": "Task1706",
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


def failure_rows(
    collapse: list[dict[str, object]],
    payoff: list[dict[str, object]],
    compressor: list[dict[str, object]],
    actions: list[dict[str, object]],
    metrics: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for label, counts in [
        ("collapse_risk_bucket", Counter(str(row["collapse_risk_bucket"]) for row in collapse)),
        ("pre_entry_gate", Counter(str(row["pre_entry_gate"]) for row in collapse)),
        ("payoff_quality_bucket", Counter(str(row["payoff_quality_bucket"]) for row in payoff)),
        ("selection_reason", Counter(str(row["selection_reason"]) for row in compressor)),
        ("runtime_action", Counter(str(row["runtime_action"]) for row in actions)),
    ]:
        for reason, count in counts.most_common():
            rows.append(
                {
                    "task_id": "Task1707",
                    "failure_id": f"BADGATEFAIL1707-{idx:05d}",
                    "failure_area": label,
                    "reason": reason,
                    "row_count": count,
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    for row in metrics:
        if row["target_cagr_30pct_met"] != "1" or row["target_mdd_minus30pct_met"] != "1" or row["beats_task1668_baseline"] != "1":
            rows.append(
                {
                    "task_id": "Task1707",
                    "failure_id": f"BADGATEFAIL1707-{idx:05d}",
                    "failure_area": "target_or_baseline_failure",
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


def gate_closeout(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gate = [
        {
            "task_id": "Task1716",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "beats_task1668_baseline_by_any": "1" if any(row["beats_task1668_baseline"] == "1" for row in metrics) else "0",
            "cagr_30pct_met_by_any": "1" if any(row["target_cagr_30pct_met"] == "1" for row in metrics) else "0",
            "mdd_minus30pct_met_by_any": "1" if any(row["target_mdd_minus30pct_met"] == "1" for row in metrics) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "l2_l4_bad_trade_gate_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1717",
            "verdict": "l2_l4_bad_trade_gate_implemented_diagnostic_only",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit selected replacements and blocked baseline rows before expanding candidate replacement aggressiveness",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(
    metrics: list[dict[str, object]],
    split: list[dict[str, object]],
    failures: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1698-1717 L2/L4 Bad-Trade Gate",
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
        "| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | Hold | Reduce | Exit | Beats Base | QQQ Beat | CAGR Target | MDD Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['baseline_final_equity']} | {row['baseline_max_drawdown']} | {row['delta_final_equity']} | {row['delta_mdd']} | {row['trade_count']} | {row['hold_count']} | {row['reduce_count']} | {row['exit_count']} | {row['beats_task1668_baseline']} | {row['beats_qqq']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |"
        )
    lines.extend(["", "Split/OOS diagnostics:", "", "| Policy | Window | Final | Return | MDD |", "| --- | --- | ---: | ---: | ---: |"])
    for row in split:
        lines.append(f"| `{row['policy_variant_id']}` | {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. The gate is implemented as one frozen policy family, not a broad parameter search.",
            "2. L2 now separates terminal/listing/dilution risk from ordinary or theme volatility.",
            "3. L4 now preserves baseline winners unless a severe pre-entry risk or much stronger payoff candidate appears.",
            "4. L5 now exits only on thesis-break evidence, not isolated price noise.",
            "5. This remains diagnostic and does not approve strategy.",
            "",
            "## Failure / Blocker Summary",
            "",
        ]
    )
    for row in failures[:24]:
        lines.append(
            f"- `{row['failure_area']}`: {row.get('reason', row.get('policy_variant_id', ''))} count={row.get('row_count','')} cagr={row.get('cagr','')} mdd={row.get('max_drawdown','')} delta_final={row.get('delta_final_equity','')}"
        )
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task1698_expert_review.csv`",
            "- `task1699_collapse_risk_v2_panel.csv`",
            "- `task1700_payoff_quality_v2_panel.csv`",
            "- `task1701_risk_payoff_mechanism_edges.csv`",
            "- `task1702_top3_top5_candidate_compressor.csv`",
            "- `task1703_thesis_break_action_panel.csv`",
            "- `task1704_bad_trade_gate_replay_trades.csv/equity`",
            "- `task1705_bad_trade_gate_replay_metrics.csv`",
            "- `task1706_split_oos_metrics.csv`",
            "- `task1707_failure_attribution.csv`",
            "- `task1716_acceptance_gate.csv`",
            "- `task1717_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1698_1717_l2_l4_bad_trade_gate_validate.py`",
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
    collapse = build_collapse_risk_panel()
    payoff = build_payoff_quality_panel(collapse)
    edges = build_l3_edges(payoff)
    compressor = build_candidate_compressor(payoff)
    actions, trades, equity = replay_selected(compressor)
    metrics = build_metrics(trades, equity)
    splits = split_rows(equity)
    failures = failure_rows(collapse, payoff, compressor, actions, metrics)
    gate, closeout = gate_closeout(metrics)
    outputs = [
        ("task1698_expert_review.csv", experts),
        ("task1699_collapse_risk_v2_panel.csv", collapse),
        ("task1700_payoff_quality_v2_panel.csv", payoff),
        ("task1701_risk_payoff_mechanism_edges.csv", edges),
        ("task1702_top3_top5_candidate_compressor.csv", compressor),
        ("task1703_thesis_break_action_panel.csv", actions),
        ("task1704_bad_trade_gate_replay_trades.csv", trades),
        ("task1704_bad_trade_gate_replay_equity.csv", equity),
        ("task1705_bad_trade_gate_replay_metrics.csv", metrics),
        ("task1706_split_oos_metrics.csv", splits),
        ("task1707_failure_attribution.csv", failures),
        ("task1716_acceptance_gate.csv", gate),
        ("task1717_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1717_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(metrics, splits, failures, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1698_1717] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
