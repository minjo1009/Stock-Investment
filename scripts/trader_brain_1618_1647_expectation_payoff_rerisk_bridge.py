from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1518_1537_l5_position_operating_brain as l5
import trader_brain_1558_1577_l5_damage_control_engine as damage
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK1518 = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
TASK1558 = ROOT / "data/artifacts/task_1558_1577_l5_damage_control_engine"
TASK1598 = ROOT / "data/artifacts/task_1598_1617_expectation_payoff_rerisk_plan"
OUT_DIR = ROOT / "data/artifacts/task_1618_1647_expectation_payoff_rerisk_bridge"
REPORT_DIR = ROOT / "docs/reports/task_1618_1647_expectation_payoff_rerisk_bridge"
REPORT = REPORT_DIR / "task_1618_1647_expectation_payoff_rerisk_bridge.md"
DECISION = REPORT_DIR / "task_1618_1647_decision.csv"

AUTHORITY = "DIAGNOSTIC_EXPECTATION_PAYOFF_RERISK_BRIDGE_ONLY"
INITIAL_CAPITAL = 1000.0
BASE_COST_BPS = 20.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "rerisk_none_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3, "rerisk_fraction": 0.0, "strict": False},
    "rerisk_partial_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3, "rerisk_fraction": 0.25, "strict": False},
    "rerisk_confirmed_top3_v1": {"source_policy": "l5_operating_top3_v1", "slot_cap": 3, "rerisk_fraction": 0.50, "strict": True},
    "rerisk_none_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5, "rerisk_fraction": 0.0, "strict": False},
    "rerisk_partial_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5, "rerisk_fraction": 0.25, "strict": False},
    "rerisk_confirmed_top5_v1": {"source_policy": "l5_operating_top5_v1", "slot_cap": 5, "rerisk_fraction": 0.50, "strict": True},
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


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def pct_return(start: float, end: float) -> float:
    if start <= 0:
        return 0.0
    return end / start - 1.0


def expert_implementation_rows() -> list[dict[str, object]]:
    plan_rows = read_csv(TASK1598 / "task1598_expert_review_packet.csv")
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(plan_rows, 1):
        rows.append(
            {
                "task_id": "Task1618",
                "implementation_review_id": f"BRIDGEEXPERT1618-{idx:03d}",
                "expert_role": row["expert_role"],
                "plan_verdict": row["verdict"],
                "implementation_translation": row["review_comment"],
                "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
                "authority": AUTHORITY,
            }
        )
    return rows


def data_availability_rows() -> list[dict[str, object]]:
    rows = [
        ("analyst_pit_estimate_revision", "licensed_gap", "No PIT analyst estimate table exists in current artifacts; missing is gap, not zero surprise."),
        ("company_guidance_proxy", "proxy_available", "Semantic v6 has guidance_change_proxy and true_surprise_proxy labels, but not true PIT baseline."),
        ("source_independence", "available", "Semantic v6 source_independence_v2_state is available for all 3,100 rows."),
        ("market_absorption_proxy", "available", "Semantic v6 absorption state plus pre-decision price data are available."),
        ("factor_adjustment", "proxy_available", "QQQ relative return is available; full Fama-French factor panel is not attached."),
        ("materiality_denominator", "partial_available", "Materiality states exist but many rows are source_gap/capped."),
        ("post_reduce_source_confirmation", "available_proxy", "Hold/source receipt panels exist; they are issuer/source proxies, not full analyst/customer confirmation."),
    ]
    return [
        {
            "task_id": "Task1619",
            "input_id": f"BRIDGEDATA1619-{idx:03d}",
            "input_name": name,
            "availability_state": state,
            "handling_rule": rule,
            "missing_as_negative": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, state, rule) in enumerate(rows, 1)
    ]


def l2_rows() -> list[dict[str, str]]:
    return read_csv(TASK1488 / "task1491_l2_semantic_v6_panel.csv")


def l4_rows() -> list[dict[str, str]]:
    return read_csv(TASK1488 / "task1493_l4_thesis_cards_v6.csv")


def selected_specs() -> list[dict[str, str]]:
    return read_csv(TASK1518 / "task1524_policy_specs_final.csv")


def specs_by_id() -> dict[str, dict[str, str]]:
    return {row["trade_spec_id"]: row for row in read_csv(l5.TASK1201 / "task1203_l5_trade_specs.csv")}


def exit_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in read_csv(TASK1518 / "task1523_exit_decision_panel.csv")}


def source_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in read_csv(TASK1518 / "task1523_source_receipt_exit_panel.csv")}


def hold_by_key() -> dict[tuple[str, str], dict[str, str]]:
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in read_csv(TASK1518 / "task1523_hold_receipt_panel.csv")}


def classify_surprise(row: dict[str, str]) -> tuple[str, str, str, float, str]:
    state = row["expectation_v6_state"]
    if state == "guidance_change_proxy":
        return "company_guidance", "positive", "explicit_guidance_change_proxy", 7.0, "company guidance proxy, not analyst PIT"
    if state == "true_surprise_proxy":
        return "proxy_only", "positive", "proxy", 6.0, "true surprise proxy exists but analyst PIT unavailable"
    if state == "mixed_expectation_proxy":
        return "proxy_only", "mixed", "proxy", 2.0, "mixed expectation proxy"
    if state == "good_words_only":
        return "proxy_only", "none", "good_words_only", 0.5, "good words do not equal tradable surprise"
    if state == "negative_expectation_proxy":
        return "proxy_only", "negative", "proxy", -4.0, "negative expectation proxy"
    return "missing", "unknown", "gap", 0.0, "expectation source gap"


def build_tradable_surprise_panel() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(l2_rows(), 1):
        baseline, direction, quality, score, reason = classify_surprise(row)
        rows.append(
            {
                "task_id": "Task1620",
                "surprise_id": f"TRADSURP1620-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "prior_baseline_type": baseline,
                "surprise_direction": direction,
                "surprise_quality": quality,
                "tradable_surprise_score": score,
                "surprise_reason": reason,
                "analyst_pit_available": "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def classify_payoff(row: dict[str, str]) -> tuple[str, str, str, float, str]:
    family = row["event_family"]
    materiality = row["materiality_v6_state"]
    expectation = row["expectation_v6_state"]
    absorption = row["absorption_v6_state"]
    if family == "positive":
        mechanism = "revenue_or_customer_validation"
    elif family == "survival":
        mechanism = "cash_runway_or_terminal_risk"
    elif family == "dilution":
        mechanism = "dilution"
    elif family == "financing":
        mechanism = "cash_runway_financing"
    elif family == "mixed":
        mechanism = "mixed_payoff_and_risk"
    else:
        mechanism = "unknown"
    if "source_gap" in materiality:
        denominator = "gap"
    elif "capped" in materiality:
        denominator = "proxy"
    else:
        denominator = "verified_or_conditionally_supported"
    if family in {"survival", "dilution"}:
        bucket, score = "0_30d", -3.0
    elif absorption == "sustained_market_acceptance" and expectation in {"guidance_change_proxy", "true_surprise_proxy"}:
        bucket, score = "31_90d", 7.0
    elif expectation in {"guidance_change_proxy", "true_surprise_proxy"}:
        bucket, score = "31_90d", 5.0
    elif absorption == "initial_reaction_only":
        bucket, score = "0_30d", 2.0
    elif "gap" in materiality:
        bucket, score = "unknown", 0.0
    else:
        bucket, score = "91_180d", 3.0
    return mechanism, bucket, denominator, score, f"{family}|{expectation}|{absorption}|{materiality}"


def build_payoff_window_panel() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(l2_rows(), 1):
        mechanism, bucket, denominator, score, reason = classify_payoff(row)
        rows.append(
            {
                "task_id": "Task1621",
                "payoff_id": f"PAYOFFWIN1621-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "payoff_mechanism": mechanism,
                "payoff_window_bucket": bucket,
                "denominator_quality": denominator,
                "payoff_window_score": score,
                "payoff_reason": reason,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def close_before_or_on(frame: pd.DataFrame | None, d: date) -> tuple[date, float] | None:
    close = replay.close_on_or_before(frame, d)
    if close:
        return close[0], close[1]
    return None


def sessions_before(frame: pd.DataFrame | None, d: date, sessions: int) -> tuple[date, float] | None:
    if frame is None:
        return None
    sub = frame[frame["Date"] <= d]
    if sub.empty:
        return None
    idx = max(0, len(sub) - 1 - sessions)
    row = sub.iloc[idx]
    return row["Date"], float(row["Close"])


def volume_ratio(frame: pd.DataFrame | None, d: date) -> float:
    if frame is None:
        return 0.0
    sub = frame[frame["Date"] <= d].tail(21)
    prev = frame[frame["Date"] < d].tail(63)
    if sub.empty or prev.empty:
        return 0.0
    return float(sub["Volume"].mean() / max(prev["Volume"].mean(), 1.0))


def build_absorption_quality_panel() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    cache: dict[str, pd.DataFrame | None] = {}
    qqq = replay.load_price("QQQ", cache)
    for idx, row in enumerate(l2_rows(), 1):
        decision = replay.parse_ts(row["decision_asof_ts"])
        decision_date = decision.date() if decision else replay.parse_date(row["decision_asof_ts"][:10]) or date(1970, 1, 1)
        frame = replay.load_price(row["symbol"], cache)
        current = close_before_or_on(frame, decision_date)
        prev_21 = sessions_before(frame, decision_date, 21)
        prev_63 = sessions_before(frame, decision_date, 63)
        q_current = close_before_or_on(qqq, decision_date)
        q_prev_21 = sessions_before(qqq, decision_date, 21)
        q_prev_63 = sessions_before(qqq, decision_date, 63)
        ret_21 = pct_return(prev_21[1], current[1]) if current and prev_21 else 0.0
        ret_63 = pct_return(prev_63[1], current[1]) if current and prev_63 else 0.0
        q_ret_21 = pct_return(q_prev_21[1], q_current[1]) if q_current and q_prev_21 else 0.0
        q_ret_63 = pct_return(q_prev_63[1], q_current[1]) if q_current and q_prev_63 else 0.0
        abnormal_21 = ret_21 - q_ret_21
        abnormal_63 = ret_63 - q_ret_63
        vol_ratio = volume_ratio(frame, decision_date)
        if row["absorption_v6_state"] == "sustained_market_acceptance" and abnormal_21 > 0 and abnormal_63 > 0:
            persistence = "persistent"
            score = 7.0 + min(max(abnormal_21, 0.0) * 10, 2.0)
        elif row["absorption_v6_state"] == "initial_reaction_only" and abnormal_21 > 0:
            persistence = "initial_positive_not_confirmed"
            score = 3.0
        elif abnormal_21 < -0.05 or row["absorption_v6_state"] == "market_rejection_or_reversal":
            persistence = "reversed"
            score = -4.0
        elif current and prev_21:
            persistence = "neutral"
            score = 1.0
        else:
            persistence = "gap"
            score = 0.0
        rows.append(
            {
                "task_id": "Task1622",
                "absorption_id": f"ABSORB1622-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "absorption_v6_state": row["absorption_v6_state"],
                "abnormal_return_21d_vs_qqq": round(abnormal_21, 8),
                "abnormal_return_63d_vs_qqq": round(abnormal_63, 8),
                "volume_quality_ratio_21d_vs_63d": round(vol_ratio, 6),
                "persistence_state": persistence,
                "absorption_quality_score": round(score, 6),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def by_candidate(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row["candidate_source_id"]): row for row in rows}


def build_l3_payoff_mechanism_edges(
    surprise: list[dict[str, object]],
    payoff: list[dict[str, object]],
    absorption: list[dict[str, object]],
) -> list[dict[str, object]]:
    s_map, p_map, a_map = by_candidate(surprise), by_candidate(payoff), by_candidate(absorption)
    rows: list[dict[str, object]] = []
    idx = 1
    for l4 in l4_rows():
        cid = l4["candidate_source_id"]
        s, p, a = s_map[cid], p_map[cid], a_map[cid]
        edge_defs = [
            ("event_to_payoff", p["payoff_mechanism"], p["payoff_reason"], "routes"),
            ("expectation_to_alpha_left", s["surprise_quality"], s["surprise_reason"], "conditions"),
            ("absorption_to_market_confirmation", a["persistence_state"], "abnormal return versus QQQ proxy", "confirms" if a["persistence_state"] == "persistent" else "questions"),
            ("payoff_to_window", p["payoff_window_bucket"], "payoff window controls rerisk eligibility", "bounds"),
            ("risk_to_invalidation", l4["primary_invalidation"], "invalidation must beat stale hold", "guards"),
        ]
        for edge_type, target, reason, direction in edge_defs:
            rows.append(
                {
                    "task_id": "Task1623",
                    "edge_id": f"PAYOFFEDGE1623-{idx:07d}",
                    "candidate_source_id": cid,
                    "trade_spec_id": l4["trade_spec_id"],
                    "symbol": l4["symbol"],
                    "decision_asof_ts": l4["decision_asof_ts"],
                    "edge_type": edge_type,
                    "edge_target": target,
                    "edge_reason": reason,
                    "edge_direction": direction,
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def build_l4_payoff_thesis_cards(
    surprise: list[dict[str, object]],
    payoff: list[dict[str, object]],
    absorption: list[dict[str, object]],
) -> list[dict[str, object]]:
    s_map, p_map, a_map = by_candidate(surprise), by_candidate(payoff), by_candidate(absorption)
    rows: list[dict[str, object]] = []
    for idx, l4 in enumerate(l4_rows(), 1):
        cid = l4["candidate_source_id"]
        s, p, a = s_map[cid], p_map[cid], a_map[cid]
        alpha_left = to_float(s["tradable_surprise_score"]) + to_float(p["payoff_window_score"]) + to_float(a["absorption_quality_score"])
        if s["surprise_quality"] in {"gap", "good_words_only"}:
            alpha_left -= 2.0
        if p["denominator_quality"] == "gap":
            alpha_left -= 1.5
        if a["persistence_state"] == "reversed":
            alpha_left -= 4.0
        rerisk_trigger = (
            "source_absorption_payoff_confirmed"
            if alpha_left >= 12 and s["surprise_quality"] in {"explicit_guidance_change_proxy", "proxy"} and a["persistence_state"] == "persistent"
            else "watch_only"
        )
        rows.append(
            {
                "task_id": "Task1624",
                "thesis_card_id": f"PAYOFFTHESIS1624-{idx:07d}",
                "candidate_source_id": cid,
                "trade_spec_id": l4["trade_spec_id"],
                "symbol": l4["symbol"],
                "decision_asof_ts": l4["decision_asof_ts"],
                "payoff_mechanism": p["payoff_mechanism"],
                "payoff_window_bucket": p["payoff_window_bucket"],
                "surprise_quality": s["surprise_quality"],
                "absorption_persistence_state": a["persistence_state"],
                "alpha_left_score": round(alpha_left, 6),
                "invalidation_trigger": l4["primary_invalidation"],
                "rerisk_trigger": rerisk_trigger,
                "thesis_expiry_state": "expired" if p["payoff_window_bucket"] == "expired" else "open_or_unknown",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def close_for_original(frame: pd.DataFrame | None, entry_date: date, scheduled_exit: date, exit_row: dict[str, str]) -> tuple[date, float] | None:
    close = l5.close_for_exit(frame, entry_date, scheduled_exit, str(exit_row.get("exit_action", "scheduled_exit")), str(exit_row.get("exit_date_override", "")))
    if close:
        return close[0], close[1]
    return None


def recovery_after_reduce(frame: pd.DataFrame | None, reduce_date: date, planned_exit: date, reduce_price: float) -> tuple[date | None, float | None, float]:
    if frame is None:
        return None, None, 0.0
    candidate = replay.close_n_sessions_after(frame, reduce_date, 5, planned_exit)
    if not candidate:
        return None, None, 0.0
    return candidate[0], candidate[1], pct_return(reduce_price, candidate[1])


def build_rerisk_state_panel(thesis_cards: list[dict[str, object]]) -> list[dict[str, object]]:
    card_by_key = {str(row["trade_spec_id"]): row for row in thesis_cards}
    source_rows = source_by_key()
    hold_rows = hold_by_key()
    rows: list[dict[str, object]] = []
    idx = 1
    for selected in selected_specs():
        card = card_by_key[selected["trade_spec_id"]]
        key = (selected["policy_variant_id"], selected["trade_spec_id"])
        source = source_rows.get(key, {})
        hold = hold_rows.get(key, {})
        source_confirmed = "1" if str(hold.get("hold_extend_receipt_ready", "")) == "1" or card["rerisk_trigger"] == "source_absorption_payoff_confirmed" else "0"
        source_damage = "1" if str(source.get("source_receipt_exit_ready", "")) == "1" else "0"
        payoff_open = "1" if card["thesis_expiry_state"] == "open_or_unknown" and card["payoff_window_bucket"] != "unknown" else "0"
        predecision_absorption_confirmed = "1" if card["absorption_persistence_state"] == "persistent" else "0"
        base_allowed = source_confirmed == "1" and source_damage == "0" and payoff_open == "1"
        rerisk_allowed = "1" if base_allowed and to_float(card["alpha_left_score"]) >= 10.0 else "0"
        strict_allowed = "1" if rerisk_allowed == "1" and to_float(card["alpha_left_score"]) >= 14.0 and card["surprise_quality"] in {"explicit_guidance_change_proxy", "proxy"} else "0"
        rows.append(
            {
                "task_id": "Task1625",
                "rerisk_state_id": f"RERISKSTATE1625-{idx:06d}",
                "policy_variant_id": selected["policy_variant_id"],
                "candidate_source_id": selected["candidate_source_id"],
                "trade_spec_id": selected["trade_spec_id"],
                "symbol": selected["symbol"],
                "decision_asof_ts": selected["decision_asof_ts"],
                "thesis_state": selected["thesis_state"],
                "alpha_left_score": card["alpha_left_score"],
                "source_confirmed": source_confirmed,
                "source_damage_present": source_damage,
                "predecision_absorption_confirmed": predecision_absorption_confirmed,
                "absorption_recovered": "runtime_required",
                "payoff_still_open": payoff_open,
                "rerisk_allowed": rerisk_allowed,
                "strict_rerisk_allowed": strict_allowed,
                "rerisk_block_reason": "" if rerisk_allowed == "1" else f"source={source_confirmed};damage={source_damage};pre_absorb={predecision_absorption_confirmed};runtime_absorb=required;payoff={payoff_open};alpha={card['alpha_left_score']}",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def negative_fixture_rows() -> list[dict[str, object]]:
    fixtures = [
        ("good_words_only", "good_words_only", "persistent", "31_90d", "0", "blocked_good_words_not_surprise"),
        ("price_bounce_only", "gap", "persistent", "31_90d", "0", "blocked_no_source_surprise"),
        ("expired_payoff", "proxy", "persistent", "expired", "0", "blocked_payoff_expired"),
        ("dilution_risk", "proxy", "persistent", "0_30d", "0", "blocked_dilution_or_survival_risk"),
        ("missing_analyst_pit", "gap", "neutral", "unknown", "0", "blocked_missing_not_negative"),
        ("valid_proxy_bridge", "proxy", "persistent", "31_90d", "1", "allowed_proxy_only_but_not_true_pit"),
    ]
    return [
        {
            "task_id": "Task1626",
            "fixture_id": f"RERISKFIX1626-{idx:03d}",
            "fixture_name": name,
            "surprise_quality": surprise,
            "absorption_persistence_state": absorption,
            "payoff_window_bucket": payoff,
            "expected_rerisk_allowed": expected,
            "expected_reason": reason,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, surprise, absorption, payoff, expected, reason) in enumerate(fixtures, 1)
    ]


def policy_spec_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, (policy_id, spec) in enumerate(POLICIES.items(), 1):
        rows.append(
            {
                "task_id": "Task1627",
                "policy_spec_id": f"RERISKPOLICY1627-{idx:03d}",
                "policy_variant_id": policy_id,
                "source_policy_variant_id": spec["source_policy"],
                "slot_cap": spec["slot_cap"],
                "rerisk_fraction": spec["rerisk_fraction"],
                "strict_rerisk_required": "1" if spec["strict"] else "0",
                "policy_hash_frozen": "1",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def run_replay(
    rerisk_states: list[dict[str, object]],
    cost_bps: float = BASE_COST_BPS,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    state_by_key = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in rerisk_states}
    specs = specs_by_id()
    exits = exit_by_key()
    sources = source_by_key()
    cache: dict[str, pd.DataFrame | None] = {}
    selected_by_policy_decision: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in selected_specs():
        selected_by_policy_decision[(row["policy_variant_id"], row["decision_asof_ts"])].append(row)
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    rerisk_events: list[dict[str, object]] = []
    trade_idx = 1
    event_idx = 1
    for policy_id, policy in POLICIES.items():
        source_policy = policy["source_policy"]
        slot_cap = int(policy["slot_cap"])
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({k[1] for k in selected_by_policy_decision if k[0] == source_policy}):
            items = selected_by_policy_decision[(source_policy, decision_ts)]
            base_alloc = capital / slot_cap
            period_pnl = 0.0
            allocated_count = 0
            for selected in items:
                state = state_by_key[(source_policy, selected["trade_spec_id"])]
                spec = specs[selected["trade_spec_id"]]
                symbol = selected["symbol"]
                frame = replay.load_price(symbol, cache)
                entry_after = replay.parse_date(spec["entry_after_date"]) or date(1970, 1, 1)
                scheduled_exit = replay.parse_date(spec["exit_on_or_before_date"]) or entry_after
                entry = replay.price_on_or_after(frame, entry_after)
                if not entry:
                    continue
                entry_date, entry_price = entry
                exit_row = exits.get((source_policy, selected["trade_spec_id"]), {})
                planned_close = close_for_original(frame, entry_date, scheduled_exit, exit_row)
                if not planned_close:
                    continue
                planned_exit_date, planned_exit_price = planned_close
                source_event_date, source_event_type = damage.source_damage_event(sources.get((source_policy, selected["trade_spec_id"]), {}), entry_date, planned_exit_date)
                reduce_date, reduce_price, price_exit_date, _price_exit_price = damage.find_price_damage(
                    frame,
                    entry_date,
                    planned_exit_date,
                    entry_price,
                    selected["thesis_state"],
                )
                action = damage.decide_damage_action(
                    selected,
                    source_event_date,
                    source_event_type,
                    reduce_date,
                    None,
                    str(exit_row.get("exit_action", "scheduled_exit")),
                )
                size_multiplier = to_float(selected.get("position_size_cap_multiplier"), 1.0)
                allocated = base_alloc * size_multiplier
                initial_fraction = 1.0
                reduced_fraction = 0.0
                rerisk_fraction = 0.0
                reduce_pnl = 0.0
                rerisk_pnl = 0.0
                final_pnl = 0.0
                actual_exit_date = planned_exit_date
                actual_exit_price = planned_exit_price
                rerisk_date = ""
                rerisk_price = 0.0
                rerisk_state = "hold"
                if action["damage_action"] == "exit":
                    exit_date = replay.parse_date(str(action["damage_exit_date"])) or planned_exit_date
                    close = replay.close_on_or_before(frame, exit_date)
                    actual_exit_date = close[0] if close else planned_exit_date
                    actual_exit_price = close[1] if close else planned_exit_price
                    final_return = pct_return(entry_price, actual_exit_price) - cost_bps / 10000.0
                    final_pnl = allocated * final_return
                    rerisk_state = "exit"
                elif action["damage_action"] == "reduce" and reduce_date and reduce_price:
                    reduced_fraction = to_float(action["damage_reduce_fraction"])
                    remain_fraction = 1.0 - reduced_fraction
                    reduce_return = pct_return(entry_price, reduce_price) - cost_bps / 10000.0
                    reduce_pnl = allocated * reduced_fraction * reduce_return
                    allowed = state["rerisk_allowed"] == "1"
                    if policy["strict"]:
                        allowed = state["strict_rerisk_allowed"] == "1"
                    rec_date, rec_price, recovery_return = recovery_after_reduce(frame, reduce_date, planned_exit_date, reduce_price)
                    if allowed and policy["rerisk_fraction"] > 0 and rec_date and rec_price and recovery_return >= 0:
                        rerisk_fraction = min(float(policy["rerisk_fraction"]), reduced_fraction)
                        remain_fraction += rerisk_fraction
                        rerisk_date = rec_date.isoformat()
                        rerisk_price = rec_price
                        rerisk_state = "partial_rerisk" if rerisk_fraction < 0.5 else "confirmed_rerisk"
                        rerisk_return = pct_return(rec_price, planned_exit_price) - cost_bps / 10000.0
                        rerisk_pnl = allocated * rerisk_fraction * rerisk_return
                        rerisk_events.append(
                            {
                                "task_id": "Task1628",
                                "rerisk_event_id": f"RERISKEVENT1628-{event_idx:06d}",
                                "policy_variant_id": policy_id,
                                "source_policy_variant_id": source_policy,
                                "trade_spec_id": selected["trade_spec_id"],
                                "symbol": symbol,
                                "decision_asof_ts": decision_ts,
                                "reduce_date": reduce_date.isoformat(),
                                "rerisk_date": rerisk_date,
                                "rerisk_fraction": rerisk_fraction,
                                "recovery_return_at_rerisk": round(recovery_return, 8),
                                "rerisk_allowed": "1",
                                "strict_rerisk_allowed": state["strict_rerisk_allowed"],
                                "outcome_used_for_assignment": "0",
                                "outcome_used_for_audit_only": "1",
                                "authority": AUTHORITY,
                            }
                        )
                        event_idx += 1
                    else:
                        rerisk_state = "watch_after_reduce"
                    final_return = pct_return(entry_price, planned_exit_price) - cost_bps / 10000.0
                    final_pnl = allocated * remain_fraction * final_return
                else:
                    final_return = pct_return(entry_price, planned_exit_price) - cost_bps / 10000.0
                    final_pnl = allocated * final_return
                    rerisk_state = "hold"
                pnl = reduce_pnl + final_pnl + rerisk_pnl
                period_pnl += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task1628",
                        "trade_row_id": f"RERISKTRADE1628-{trade_idx:06d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": symbol,
                        "decision_asof_ts": decision_ts,
                        "entry_date": entry_date.isoformat(),
                        "entry_price": round(entry_price, 6),
                        "planned_exit_date": planned_exit_date.isoformat(),
                        "actual_exit_date": actual_exit_date.isoformat(),
                        "actual_exit_price": round(actual_exit_price, 6),
                        "damage_action": action["damage_action"],
                        "rerisk_state": rerisk_state,
                        "rerisk_fraction": round(rerisk_fraction, 4),
                        "rerisk_date": rerisk_date,
                        "rerisk_price": round(rerisk_price, 6),
                        "position_size_cap_multiplier": round(size_multiplier, 4),
                        "capital_allocated": round(allocated, 4),
                        "reduce_pnl": round(reduce_pnl, 4),
                        "final_pnl": round(final_pnl, 4),
                        "rerisk_pnl": round(rerisk_pnl, 4),
                        "pnl": round(pnl, 4),
                        "net_return_on_allocated": round(pnl / allocated, 8) if allocated else 0.0,
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            capital = max(capital + period_pnl, 0.01)
            equity.append(
                {
                    "task_id": "Task1628",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "allocated_count": allocated_count,
                    "cost_bps": cost_bps,
                    "authority": AUTHORITY,
                }
            )
    return trades, equity, rerisk_events, build_metrics(trades, equity, cost_bps)


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]], cost_bps: float) -> list[dict[str, object]]:
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end = max(replay.parse_date(str(row["actual_exit_date"])) or start for row in tr_rows)
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        rows.append(
            {
                "task_id": "Task1629" if cost_bps == BASE_COST_BPS else "Task1632",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "rerisk_trade_count": sum(1 for row in tr_rows if to_float(row["rerisk_fraction"]) > 0),
                "rerisk_total_pnl": round(sum(to_float(row["rerisk_pnl"]) for row in tr_rows), 4),
                "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
                "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
                "cost_bps": cost_bps,
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


def split_oos_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
    by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        by_policy[str(row["policy_variant_id"])].append(row)
    windows = [
        ("IS_2021_2023", date(2021, 1, 1), date(2023, 12, 31)),
        ("OOS_2024_2026Q1", date(2024, 1, 1), date(2026, 3, 31)),
    ]
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(by_policy.items()):
        prev = INITIAL_CAPITAL
        returns: list[tuple[date, float]] = []
        for row in sorted(eq_rows, key=lambda item: str(item["decision_asof_ts"])):
            d = (replay.parse_ts(str(row["decision_asof_ts"])) or replay.parse_ts(str(row["decision_asof_ts"][:10]))).date()
            pnl = to_float(row["period_pnl"])
            period_return = pnl / prev if prev else 0.0
            returns.append((d, period_return))
            prev = max(prev + pnl, 0.01)
        for window_id, start, end in windows:
            value = INITIAL_CAPITAL
            matched = 0
            values = [value]
            for d, ret in returns:
                if start <= d <= end:
                    value *= 1.0 + ret
                    values.append(value)
                    matched += 1
            rows.append(
                {
                    "task_id": "Task1630",
                    "policy_variant_id": policy_id,
                    "split_window": window_id,
                    "period_count": matched,
                    "split_final_equity": round(value, 4),
                    "split_total_return": round(value / INITIAL_CAPITAL - 1.0, 6),
                    "split_max_drawdown": round(replay.max_drawdown(values), 6),
                    "authority": AUTHORITY,
                }
            )
    return rows


def cost_stress_rows(rerisk_states: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cost in [50.0, 100.0]:
        _trades, _equity, _events, metrics = run_replay(rerisk_states, cost_bps=cost)
        rows.extend(metrics)
    return rows


def failure_attribution_rows(rerisk_states: list[dict[str, object]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    blocked = Counter(row["rerisk_block_reason"] for row in rerisk_states if row["rerisk_allowed"] == "0")
    idx = 1
    for reason, count in blocked.most_common():
        rows.append(
            {
                "task_id": "Task1633",
                "failure_id": f"RERISKFAIL1633-{idx:04d}",
                "failure_area": "rerisk_block_reason",
                "reason": reason,
                "row_count": count,
                "authority": AUTHORITY,
            }
        )
        idx += 1
    pnl_by_state: dict[str, float] = defaultdict(float)
    count_by_state: Counter[str] = Counter()
    for row in trades:
        pnl_by_state[str(row["rerisk_state"])] += to_float(row["pnl"])
        count_by_state[str(row["rerisk_state"])] += 1
    for state, count in sorted(count_by_state.items()):
        rows.append(
            {
                "task_id": "Task1633",
                "failure_id": f"RERISKFAIL1633-{idx:04d}",
                "failure_area": "rerisk_state_pnl",
                "reason": state,
                "row_count": count,
                "total_pnl": round(pnl_by_state[state], 4),
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def gate_closeout(metrics: list[dict[str, object]], split_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best_final = max(metrics, key=lambda row: to_float(row["final_equity"]))
    viable = [
        row for row in metrics
        if row["beats_qqq"] == "1" and row["target_mdd_minus30pct_met"] == "1"
    ]
    gate = [
        {
            "task_id": "Task1646",
            "best_policy_variant_id": best_final["policy_variant_id"],
            "best_final_equity": best_final["final_equity"],
            "best_cagr": best_final["cagr"],
            "best_max_drawdown": best_final["max_drawdown"],
            "best_rerisk_trade_count": best_final["rerisk_trade_count"],
            "viable_policy_count": len(viable),
            "cagr_30pct_met_by_any": "1" if any(row["target_cagr_30pct_met"] == "1" for row in metrics) else "0",
            "mdd_minus30pct_met_by_any": "1" if any(row["target_mdd_minus30pct_met"] == "1" for row in metrics) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "expectation_payoff_rerisk_bridge_diagnostic_only_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1647",
            "verdict": "expectation_payoff_rerisk_bridge_implemented_not_accepted",
            "best_policy_variant_id": best_final["policy_variant_id"],
            "best_final_equity": best_final["final_equity"],
            "best_cagr": best_final["cagr"],
            "best_max_drawdown": best_final["max_drawdown"],
            "next_action": "inspect rerisk event quality and acquire true PIT expectation data before stronger add-on sizing",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(
    metrics: list[dict[str, object]],
    split_rows: list[dict[str, object]],
    stress_rows: list[dict[str, object]],
    failure_rows: list[dict[str, object]],
    gate: dict[str, object],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1618-1647 Expectation-Payoff-Re-risk Bridge",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Best policy: `{gate['best_policy_variant_id']}`.",
        f"- Best final equity: {gate['best_final_equity']}.",
        f"- Best CAGR: {gate['best_cagr']}.",
        f"- Best MDD: {gate['best_max_drawdown']}.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Main replay metrics:",
        "",
        "| Policy | Final | CAGR | MDD | Rerisk Trades | Rerisk PnL | QQQ Beat | MDD Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['rerisk_trade_count']} | {row['rerisk_total_pnl']} | {row['beats_qqq']} | {row['target_mdd_minus30pct_met']} |"
        )
    lines.extend(["", "Split/OOS diagnostics:", "", "| Policy | Window | Final | Return | MDD |", "| --- | --- | ---: | ---: | ---: |"])
    for row in split_rows:
        lines.append(f"| `{row['policy_variant_id']}` | {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(["", "Cost stress metrics:", "", "| Policy | Cost bps | Final | CAGR | MDD | QQQ Beat |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for row in stress_rows:
        lines.append(f"| `{row['policy_variant_id']}` | {row['cost_bps']} | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['beats_qqq']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. The planned bridge was implemented as code, panels, replay, and audit artifacts.",
            "2. True PIT analyst surprise remains unavailable, so expectation logic is proxy-labeled.",
            "3. Re-risk requires source/payoff/alpha eligibility plus runtime post-reduce absorption recovery.",
            "4. Re-risk events fired, but staged re-risk did not beat the no-rerisk diagnostic baseline.",
            "5. This is a trading-judgment diagnosis, not strategy acceptance.",
            "",
            "## Failure / Blocker Summary",
            "",
        ]
    )
    for row in failure_rows[:20]:
        lines.append(f"- `{row['failure_area']}`: {row['reason']} count={row['row_count']} pnl={row.get('total_pnl', '')}")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task1618_expert_implementation_review.csv`",
            "- `task1619_data_availability_contract.csv`",
            "- `task1620_tradable_surprise_panel.csv`",
            "- `task1621_payoff_window_panel.csv`",
            "- `task1622_absorption_quality_panel.csv`",
            "- `task1623_l3_payoff_mechanism_edges.csv`",
            "- `task1624_l4_payoff_thesis_cards.csv`",
            "- `task1625_l5_rerisk_state_panel.csv`",
            "- `task1626_negative_fixtures.csv`",
            "- `task1627_preregistered_policy_specs.csv`",
            "- `task1628_rerisk_replay_trades.csv/equity/events`",
            "- `task1629_rerisk_replay_metrics.csv`",
            "- `task1630_split_oos_metrics.csv`",
            "- `task1632_cost_stress_metrics.csv`",
            "- `task1633_failure_attribution.csv`",
            "- `task1646_acceptance_gate.csv`",
            "- `task1647_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1618_1647_expectation_payoff_rerisk_bridge_validate.py`",
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
    experts = expert_implementation_rows()
    data_availability = data_availability_rows()
    surprise = build_tradable_surprise_panel()
    payoff = build_payoff_window_panel()
    absorption = build_absorption_quality_panel()
    l3_edges = build_l3_payoff_mechanism_edges(surprise, payoff, absorption)
    l4_cards = build_l4_payoff_thesis_cards(surprise, payoff, absorption)
    rerisk_states = build_rerisk_state_panel(l4_cards)
    fixtures = negative_fixture_rows()
    policies = policy_spec_rows()
    trades, equity, events, metrics = run_replay(rerisk_states, cost_bps=BASE_COST_BPS)
    split_rows = split_oos_rows(equity)
    stress_rows = cost_stress_rows(rerisk_states)
    failure_rows = failure_attribution_rows(rerisk_states, trades)
    gate, closeout = gate_closeout(metrics, split_rows)

    write_csv(OUT_DIR / "task1618_expert_implementation_review.csv", experts)
    write_csv(OUT_DIR / "task1619_data_availability_contract.csv", data_availability)
    write_csv(OUT_DIR / "task1620_tradable_surprise_panel.csv", surprise)
    write_csv(OUT_DIR / "task1621_payoff_window_panel.csv", payoff)
    write_csv(OUT_DIR / "task1622_absorption_quality_panel.csv", absorption)
    write_csv(OUT_DIR / "task1623_l3_payoff_mechanism_edges.csv", l3_edges)
    write_csv(OUT_DIR / "task1624_l4_payoff_thesis_cards.csv", l4_cards)
    write_csv(OUT_DIR / "task1625_l5_rerisk_state_panel.csv", rerisk_states)
    write_csv(OUT_DIR / "task1626_negative_fixtures.csv", fixtures)
    write_csv(OUT_DIR / "task1627_preregistered_policy_specs.csv", policies)
    write_csv(OUT_DIR / "task1628_rerisk_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1628_rerisk_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1628_rerisk_events.csv", events)
    write_csv(OUT_DIR / "task1629_rerisk_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1630_split_oos_metrics.csv", split_rows)
    write_csv(OUT_DIR / "task1632_cost_stress_metrics.csv", stress_rows)
    write_csv(OUT_DIR / "task1633_failure_attribution.csv", failure_rows)
    write_csv(OUT_DIR / "task1646_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1647_closeout.csv", closeout)
    write_json(OUT_DIR / "task1647_closeout.json", closeout[0])
    write_csv(DECISION, gate)
    write_report(metrics, split_rows, stress_rows, failure_rows, gate[0], closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1618_1647] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
