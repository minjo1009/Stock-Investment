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
TASK1848 = ROOT / "data/artifacts/task_1848_1867_source_attached_policy_replay"
TASK1868 = ROOT / "data/artifacts/task_1868_1877_desk_trader_logic_expert_review"
OUT_DIR = ROOT / "data/artifacts/task_1878_1885_desk_specific_policy_replay"
REPORT_DIR = ROOT / "docs/reports/task_1878_1885_desk_specific_policy_replay"
REPORT = REPORT_DIR / "task_1878_1885_desk_specific_policy_replay.md"
DECISION = REPORT_DIR / "task_1878_1885_decision.csv"

AUTHORITY = "DIAGNOSTIC_DESK_SPECIFIC_POLICY_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265

POLICIES = {
    "desk_specific_top3_v1": {
        "source_policy": "winner_defense_budget_top3_v1",
        "baseline_policy": "sleeve_split_top3_v1",
        "source_attached_policy": "source_attached_top3_v1",
        "slot_cap": 3,
    },
    "desk_specific_top5_v1": {
        "source_policy": "winner_defense_budget_top5_v1",
        "baseline_policy": "sleeve_split_top5_v1",
        "source_attached_policy": "source_attached_top5_v1",
        "slot_cap": 5,
    },
}

LIVE_DILUTION_FAMILIES = {
    "at_the_market",
    "common_stock_offering",
    "convertible_debt",
    "warrants_units",
    "dilution_language",
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
    if value in {"", None}:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def days_between(start_ts: str, end_ts: str) -> int | None:
    start = replay.parse_ts(start_ts)
    end = replay.parse_ts(end_ts)
    if start is None or end is None:
        return None
    return (end.date() - start.date()).days


def source_trade_map() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv")
    return {(row["policy_variant_id"], row["trade_spec_id"]): row for row in rows}


def load_inputs() -> tuple[
    list[dict[str, str]],
    dict[tuple[str, str], dict[str, str]],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
    dict[str, str],
]:
    budgets = read_csv(TASK1808 / "task1815_sleeve_risk_budget.csv")
    meaning = {
        (row["target_policy_variant_id"], row["trade_spec_id"]): row
        for row in read_csv(TASK1808 / "task1812_l2_sleeve_meaning_panel.csv")
    }
    rates = {row["decision_asof_ts"]: row for row in read_csv(TASK1834 / "task1835_rates_liquidity_decision_asof_panel.csv")}
    sec_links = {row["trade_spec_id"]: row for row in read_csv(TASK1834 / "task1842_sec_dilution_decision_asof_links.csv")}
    sec_extract = {
        row["financing_source_packet_id"]: row
        for row in read_csv(TASK1834 / "task1837_financing_dilution_extractor_contract.csv")
    }
    earnings_gate = read_csv(TASK1834 / "task1838_earnings_revision_vendor_gate.csv")[0]
    return budgets, meaning, rates, sec_links, sec_extract, earnings_gate


def source_manifest_rows(budgets: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(budgets, 1):
        rows.append(
            {
                "task_id": "Task1878",
                "input_manifest_id": f"DESKINPUT-1878-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "source_policy_variant_id": row["target_policy_variant_id"],
                "source_budget_authority": row["authority"],
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def sec_specificity(row: dict[str, str], sec_links: dict[str, dict[str, str]], sec_extract: dict[str, dict[str, str]]) -> dict[str, object]:
    link = sec_links.get(row["trade_spec_id"], {})
    packet_id = link.get("latest_financing_source_packet_id", "")
    extraction = sec_extract.get(packet_id, {})
    if not link or link.get("source_gap_flag") == "1":
        return {
            "packet_id": "",
            "accepted_ts": "",
            "raw_dilution_pressure_state": "source_gap",
            "dilution_signal_families": "",
            "financing_specificity_state": "source_gap_neutral",
            "financing_event_status": "source_gap",
            "financing_current_flag": "0",
            "financing_closed_flag": "0",
            "live_terms_detected_flag": "0",
            "offering_type": "source_gap",
            "remaining_capacity_state": "unknown",
            "financing_age_days": "",
            "asof_guard_pass": link.get("asof_guard_pass", "1") if link else "1",
        }
    families = set(filter(None, extraction.get("dilution_signal_families", "").split("|")))
    raw_state = extraction.get("dilution_pressure_state", "source_gap")
    age = days_between(link.get("latest_financing_accepted_ts", ""), row["decision_asof_ts"])
    has_shelf = "shelf_registration" in families
    if "at_the_market" in families:
        offering_type = "at_the_market"
    elif "common_stock_offering" in families:
        offering_type = "common_stock_offering"
    elif "convertible_debt" in families:
        offering_type = "convertible_debt"
    elif "warrants_units" in families:
        offering_type = "warrants_units"
    elif has_shelf:
        offering_type = "shelf_registration"
    else:
        offering_type = "boilerplate_or_other"
    current_common_no_shelf = "common_stock_offering" in families and not has_shelf and age is not None and 0 <= age <= 7
    current_hard_live_terms = bool(families & {"at_the_market", "convertible_debt", "warrants_units"}) and age is not None and 0 <= age <= 45
    live_terms_detected = current_hard_live_terms or current_common_no_shelf
    if raw_state == "active_financing_pressure" and live_terms_detected:
        specificity = "live_active_dilution"
        event_status = "live_or_current"
        current_flag = "1"
        closed_flag = "0"
        remaining_capacity = "current_use_detected"
    elif raw_state == "active_financing_pressure" and has_shelf and age is not None and 0 <= age <= 365:
        specificity = "shelf_capacity_watch"
        event_status = "shelf_capacity_watch"
        current_flag = "0"
        closed_flag = "0"
        remaining_capacity = "capacity_watch_no_live_terms"
    elif raw_state in {"active_financing_pressure", "convertible_warrant_overhang"} and age is not None and age > 120:
        specificity = "historical_or_closed_financing"
        event_status = "historical_or_closed"
        current_flag = "0"
        closed_flag = "1"
        remaining_capacity = "not_current_penalty"
    elif raw_state == "source_gap":
        specificity = "source_gap_neutral"
        event_status = "source_gap"
        current_flag = "0"
        closed_flag = "0"
        remaining_capacity = "unknown"
    else:
        specificity = "boilerplate_or_sparse"
        event_status = "boilerplate_or_sparse"
        current_flag = "0"
        closed_flag = "0"
        remaining_capacity = "not_current_penalty"
    return {
        "packet_id": packet_id,
        "accepted_ts": link.get("latest_financing_accepted_ts", ""),
        "raw_dilution_pressure_state": raw_state,
        "dilution_signal_families": extraction.get("dilution_signal_families", ""),
        "financing_specificity_state": specificity,
        "financing_event_status": event_status,
        "financing_current_flag": current_flag,
        "financing_closed_flag": closed_flag,
        "live_terms_detected_flag": "1" if live_terms_detected else "0",
        "offering_type": offering_type,
        "remaining_capacity_state": remaining_capacity,
        "financing_age_days": "" if age is None else age,
        "asof_guard_pass": link.get("asof_guard_pass", "0"),
    }


def build_theme_breadth(meaning_rows: dict[tuple[str, str], dict[str, str]]) -> dict[tuple[str, str], dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in meaning_rows.values():
        grouped[(row.get("decision_asof_ts", ""), row.get("derived_theme", "unknown"))].append(row)
    out: dict[tuple[str, str], dict[str, object]] = {}
    for key, items in grouped.items():
        rel = sorted(to_float(row.get("relative_return_63d")) for row in items)
        positive = sum(1 for value in rel if value > 0.0)
        median = rel[len(rel) // 2] if rel else 0.0
        participation = positive / len(rel) if rel else 0.0
        if len(rel) < 3:
            state = "theme_breadth_sparse_neutral"
        elif participation >= 0.55 and median >= 0.0:
            state = "theme_breadth_supportive"
        elif participation <= 0.35 and median < 0.0:
            state = "theme_breadth_weak"
        else:
            state = "theme_breadth_neutral"
        out[key] = {
            "theme_breadth_state": state,
            "theme_peer_count": len(rel),
            "theme_positive_participation": round(participation, 6),
            "theme_median_relative_return_63d": round(median, 6),
        }
    return out


def winner_thesis_state(meaning: dict[str, str], sec_state: str, rate_row: dict[str, str], breadth: dict[str, object]) -> tuple[str, float, str]:
    quality = to_float(meaning.get("winner_quality_beta"))
    sleeve_quality = to_float(meaning.get("sleeve_quality_score"))
    payoff_score = to_float(meaning.get("payoff_quality_score"))
    winner_bucket = meaning.get("winner_defense_bucket", "")
    volatility = meaning.get("volatility_cause", "")
    expectation = meaning.get("expectation_state", "")
    absorption = meaning.get("absorption_state", "")
    breadth_state = str(breadth.get("theme_breadth_state", "theme_breadth_neutral"))
    liquidity = rate_row.get("liquidity_stress_state", "source_gap")

    thesis_intact = (
        quality >= 68.0
        and sleeve_quality >= 50.0
        and payoff_score >= 68.0
        and winner_bucket in {"strong_winner_defense", "qualified_winner_defense"}
        and volatility in {"leader_momentum_volatility", "normal_winner_volatility", "ordinary_noise"}
        and sec_state != "live_active_dilution"
        and expectation in {"true_surprise_proxy", "good_words_only", "guidance_change_proxy"}
        and absorption in {"accepted_underreaction_or_followthrough", "initial_reaction_only"}
    )
    if thesis_intact and breadth_state != "theme_breadth_weak":
        return "winner_thesis_intact", 1.12, "quality_momentum_thesis_intact_override"
    if thesis_intact and liquidity != "liquidity_stress":
        return "winner_thesis_intact_macro_volatile", 1.0, "quality_intact_but_breadth_weak"
    if sec_state == "live_active_dilution":
        return "winner_thesis_damaged", 0.65, "live_dilution_overrides_winner_defense"
    if quality >= 60.0 and payoff_score >= 65.0:
        return "winner_thesis_watch", 0.88, "partial_winner_quality_watch"
    return "winner_thesis_not_confirmed", 0.7, "winner_quality_not_enough"


def winner_flags(winner_state: str, sec_state: str) -> tuple[str, str]:
    intact = "1" if winner_state.startswith("winner_thesis_intact") else "0"
    thesis_break = "1" if sec_state == "live_active_dilution" or winner_state == "winner_thesis_damaged" else "0"
    return intact, thesis_break


def desk_policy(
    base_row: dict[str, str],
    meaning: dict[str, str],
    rate_row: dict[str, str],
    sec: dict[str, object],
    breadth: dict[str, object],
) -> tuple[str, float, str, str]:
    sleeve = base_row["strategy_sleeve"]
    base_mult = to_float(base_row["sleeve_budget_multiplier"])
    sec_state = str(sec["financing_specificity_state"])
    rate_state = rate_row.get("rate_regime_state", "source_gap")
    liquidity = rate_row.get("liquidity_stress_state", "source_gap")
    breadth_state = str(breadth.get("theme_breadth_state", "theme_breadth_neutral"))
    relative_return = to_float(meaning.get("relative_return_63d"))
    prior_drawdown = to_float(meaning.get("prior_drawdown_126d"))
    high_vol = to_float(meaning.get("realized_vol_63d"))

    if sleeve == "winner_compounder":
        thesis_state, thesis_mult, thesis_reason = winner_thesis_state(meaning, sec_state, rate_row, breadth)
        if thesis_state.startswith("winner_thesis_intact"):
            return "hold", clamp(max(base_mult, 1.0) * thesis_mult, 0.0, 1.18), thesis_reason, thesis_state
        if liquidity == "liquidity_stress" and breadth_state == "theme_breadth_weak":
            return "trim", clamp(base_mult * thesis_mult * 0.82, 0.0, 0.85), "macro_and_breadth_weak_without_full_winner_override", thesis_state
        return "watch", clamp(base_mult * thesis_mult, 0.0, 1.0), thesis_reason, thesis_state

    if sleeve == "speculative_event":
        if sec_state == "live_active_dilution":
            return "no_entry", 0.0, "speculative_live_dilution_block", "speculative_thesis_blocked"
        if sec_state == "shelf_capacity_watch":
            return "cap", min(base_mult, 0.35), "speculative_shelf_capacity_cap", "speculative_thesis_capped"
        if liquidity == "liquidity_stress" and breadth_state == "theme_breadth_weak":
            return "trim", clamp(base_mult * 0.55, 0.0, 0.75), "speculative_macro_breadth_weak_trim", "speculative_thesis_watch"
        return "hold", clamp(base_mult, 0.0, 1.0), "no_live_financing_block", "speculative_thesis_allowed"

    if sleeve == "cyclical_beta":
        if rate_state == "rising_rate_pressure" and breadth_state == "theme_breadth_weak":
            return "trim", clamp(base_mult * 0.7, 0.0, 0.85), "cyclical_rate_pressure_and_breadth_weak", "cyclical_permission_weak"
        if liquidity == "liquidity_stress" and relative_return < 0.0:
            return "reduce", clamp(base_mult * 0.75, 0.0, 0.9), "cyclical_liquidity_stress_without_relative_strength", "cyclical_permission_watch"
        if breadth_state == "theme_breadth_supportive":
            return "hold", clamp(base_mult * 1.05, 0.0, 1.05), "cyclical_breadth_supportive", "cyclical_permission_allowed"
        return "hold", clamp(base_mult, 0.0, 1.0), "cyclical_neutral_permission", "cyclical_permission_neutral"

    if sleeve == "defensive_quality":
        if relative_return < -0.08 and prior_drawdown < -0.20 and high_vol > 0.45:
            return "reduce", clamp(base_mult * 0.7, 0.0, 0.85), "defensive_buffer_failed_price_quality", "defensive_buffer_failed"
        if liquidity == "liquidity_stress":
            return "hold", clamp(max(base_mult, 0.85), 0.0, 1.05), "defensive_buffer_kept_during_liquidity_stress", "defensive_buffer_validated"
        return "hold", clamp(base_mult, 0.0, 1.0), "defensive_neutral_hold", "defensive_buffer_neutral"

    return "hold", clamp(base_mult, 0.0, 1.0), "unknown_sleeve_neutral_hold", "unknown_sleeve"


def build_layers() -> dict[str, list[dict[str, object]]]:
    budgets, meaning_rows, rates, sec_links, sec_extract, earnings_gate = load_inputs()
    breadth_map = build_theme_breadth(meaning_rows)
    l2_sec: list[dict[str, object]] = []
    l2_winner: list[dict[str, object]] = []
    l2_breadth: list[dict[str, object]] = []
    l3_edges: list[dict[str, object]] = []
    l4_cards: list[dict[str, object]] = []
    l5_budget: list[dict[str, object]] = []
    action_counts: Counter[tuple[str, str]] = Counter()
    all_breadth_keys: set[tuple[str, str]] = set()

    for idx, row in enumerate(budgets, 1):
        meaning = meaning_rows.get((row["target_policy_variant_id"], row["trade_spec_id"]), {})
        rate_row = rates.get(row["decision_asof_ts"], {})
        sec = sec_specificity(row, sec_links, sec_extract)
        theme = meaning.get("derived_theme", "unknown")
        breadth = breadth_map.get((row["decision_asof_ts"], theme), {})
        all_breadth_keys.add((row["decision_asof_ts"], theme))
        winner_state, winner_mult, winner_reason = winner_thesis_state(meaning, str(sec["financing_specificity_state"]), rate_row, breadth)
        winner_intact_flag, thesis_break_flag = winner_flags(winner_state, str(sec["financing_specificity_state"]))
        action, multiplier, reason, thesis_state = desk_policy(row, meaning, rate_row, sec, breadth)
        desk_rule_id = f"{row['strategy_sleeve']}::{thesis_state}::{action}"
        action_counts[(row["strategy_sleeve"], action)] += 1

        l2_sec.append(
            {
                "task_id": "Task1878",
                "sec_specificity_id": f"SECSPEC-1878-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "latest_financing_source_packet_id": sec["packet_id"],
                "latest_financing_accepted_ts": sec["accepted_ts"],
                "raw_dilution_pressure_state": sec["raw_dilution_pressure_state"],
                "dilution_signal_families": sec["dilution_signal_families"],
                "financing_specificity_state": sec["financing_specificity_state"],
                "financing_event_status": sec["financing_event_status"],
                "financing_current_flag": sec["financing_current_flag"],
                "financing_closed_flag": sec["financing_closed_flag"],
                "live_terms_detected_flag": sec["live_terms_detected_flag"],
                "offering_type": sec["offering_type"],
                "remaining_capacity_state": sec["remaining_capacity_state"],
                "effective_ts": sec["accepted_ts"],
                "closed_ts": sec["accepted_ts"] if sec["financing_closed_flag"] == "1" else "",
                "cash_runway_state": "not_available_in_local_source",
                "financing_age_days": sec["financing_age_days"],
                "asof_guard_pass": sec["asof_guard_pass"],
                "source_gap_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l2_winner.append(
            {
                "task_id": "Task1879",
                "winner_override_id": f"WINOVERRIDE-1879-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "winner_quality_beta": meaning.get("winner_quality_beta", ""),
                "sleeve_quality_score": meaning.get("sleeve_quality_score", ""),
                "payoff_quality_score": meaning.get("payoff_quality_score", ""),
                "winner_defense_bucket": meaning.get("winner_defense_bucket", ""),
                "volatility_cause": meaning.get("volatility_cause", ""),
                "winner_thesis_state": winner_state,
                "winner_thesis_intact_flag": winner_intact_flag,
                "thesis_break_confirmed_flag": thesis_break_flag,
                "winner_override_multiplier": round(winner_mult, 6),
                "winner_override_reason": winner_reason,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l3_edges.append(
            {
                "task_id": "Task1881",
                "desk_edge_id": f"DESKEDGE-1881-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "rate_regime_state": rate_row.get("rate_regime_state", "source_gap"),
                "liquidity_stress_state": rate_row.get("liquidity_stress_state", "source_gap"),
                "financing_specificity_state": sec["financing_specificity_state"],
                "theme_breadth_state": breadth.get("theme_breadth_state", "theme_breadth_neutral"),
                "winner_thesis_state": winner_state,
                "winner_thesis_intact_flag": winner_intact_flag,
                "thesis_break_confirmed_flag": thesis_break_flag,
                "desk_rule_id": desk_rule_id,
                "desk_relation_primitive": desk_rule_id,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l4_cards.append(
            {
                "task_id": "Task1884",
                "desk_thesis_card_id": f"DESKTHESIS-1884-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "desk_thesis_state": thesis_state,
                "desk_action": action,
                "desk_action_reason": reason,
                "desk_rule_id": desk_rule_id,
                "rate_regime_state": rate_row.get("rate_regime_state", "source_gap"),
                "liquidity_stress_state": rate_row.get("liquidity_stress_state", "source_gap"),
                "financing_specificity_state": sec["financing_specificity_state"],
                "theme_breadth_state": breadth.get("theme_breadth_state", "theme_breadth_neutral"),
                "earnings_revision_state": "vendor_blocked_schema_only",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        l5_budget.append(
            {
                "task_id": "Task1884",
                "desk_budget_id": f"DESKBUDGET-1884-{idx:06d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "base_sleeve_budget_multiplier": row["sleeve_budget_multiplier"],
                "desk_budget_multiplier": round(multiplier, 6),
                "desk_action": action,
                "desk_action_reason": reason,
                "desk_rule_id": desk_rule_id,
                "desk_thesis_state": thesis_state,
                "winner_thesis_intact_flag": winner_intact_flag,
                "thesis_break_confirmed_flag": thesis_break_flag,
                "rate_regime_state": rate_row.get("rate_regime_state", "source_gap"),
                "liquidity_stress_state": rate_row.get("liquidity_stress_state", "source_gap"),
                "financing_specificity_state": sec["financing_specificity_state"],
                "theme_breadth_state": breadth.get("theme_breadth_state", "theme_breadth_neutral"),
                "earnings_revision_state": "vendor_blocked_schema_only",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )

    for idx, key in enumerate(sorted(all_breadth_keys), 1):
        item = breadth_map.get(key, {})
        l2_breadth.append(
            {
                "task_id": "Task1880",
                "theme_breadth_id": f"BREADTH-1880-{idx:05d}",
                "decision_asof_ts": key[0],
                "derived_theme": key[1],
                "theme_breadth_state": item.get("theme_breadth_state", "theme_breadth_neutral"),
                "theme_peer_count": item.get("theme_peer_count", 0),
                "theme_positive_participation": item.get("theme_positive_participation", 0),
                "theme_median_relative_return_63d": item.get("theme_median_relative_return_63d", 0),
                "source": "existing_preentry_relative_return_panel_only",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )

    task_plan = [
        ("Task1878", "SEC Financing Specificity Repair", "completed", "live_active_dilution separated from shelf/historical/boilerplate"),
        ("Task1879", "Winner Thesis Intact Override", "completed", "winner thesis state can override broad macro trim"),
        ("Task1880", "Sector Breadth Local Attachment", "completed", "theme breadth built from existing pre-entry relative return panel"),
        ("Task1881", "Cyclical Regime Permission", "completed", "cyclical action requires rate/liquidity and breadth state"),
        ("Task1882", "Speculative Live Financing Block", "completed", "no-entry applies only to source-specific live dilution"),
        ("Task1883", "Defensive Buffer Validation", "completed", "defensive desk checks buffer behavior under liquidity stress"),
        ("Task1884", "Desk-Specific Frozen Policy", "completed", "one rule set frozen before replay"),
        ("Task1885", "Controlled Desk Replay", "completed", "controlled replay reuses prior controlled trade returns only"),
    ]
    plan_rows = [
        {
            "task_id": task_id,
            "title": title,
            "status": status,
            "implementation_result": result,
            "authority": AUTHORITY,
        }
        for task_id, title, status, result in task_plan
    ]
    action_rows = [
        {
            "task_id": "Task1884",
            "action_audit_id": f"DESKACTION-1884-{idx:04d}",
            "strategy_sleeve": sleeve,
            "desk_action": action,
            "row_count": count,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        for idx, ((sleeve, action), count) in enumerate(sorted(action_counts.items()), 1)
    ]
    earnings_rows = [
        {
            "task_id": "Task1884",
            "earnings_gate_id": "EARNGATE-1884-001",
            "gate_verdict": earnings_gate.get("gate_verdict", "vendor_blocked_schema_only"),
            "earnings_revision_state": "vendor_blocked_schema_only",
            "assignment_effect": "blocked_no_score_change",
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
    ]
    return {
        "task1878_input_manifest.csv": source_manifest_rows(budgets),
        "task1878_sec_financing_specificity_panel.csv": l2_sec,
        "task1879_winner_thesis_override_panel.csv": l2_winner,
        "task1880_theme_breadth_panel.csv": l2_breadth,
        "task1881_l3_desk_relation_edges.csv": l3_edges,
        "task1882_speculative_live_financing_block.csv": [row for row in l5_budget if row["strategy_sleeve"] == "speculative_event"],
        "task1883_defensive_buffer_validation_panel.csv": [row for row in l5_budget if row["strategy_sleeve"] == "defensive_quality"],
        "task1884_l4_desk_thesis_cards.csv": l4_cards,
        "task1884_l5_desk_specific_budget.csv": l5_budget,
        "task1884_desk_action_audit.csv": action_rows,
        "task1884_earnings_vendor_block_panel.csv": earnings_rows,
        "task1878_1885_task_plan_status.csv": plan_rows,
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
                key=lambda item: to_float(item["desk_budget_multiplier"]),
                reverse=True,
            )
            base_alloc = capital / int(config["slot_cap"])
            period_pnl = 0.0
            allocated_count = 0
            sleeve_counts: Counter[str] = Counter()
            action_counts: Counter[str] = Counter()
            for row in rows:
                source = source_trades.get((source_policy, str(row["trade_spec_id"])))
                if not source:
                    continue
                mult = to_float(row["desk_budget_multiplier"])
                if mult <= 0.0:
                    continue
                allocated = base_alloc * mult
                pnl = allocated * to_float(source.get("net_return"))
                capital += pnl
                period_pnl += pnl
                allocated_count += 1
                sleeve_counts[str(row["strategy_sleeve"])] += 1
                action_counts[str(row["desk_action"])] += 1
                trades.append(
                    {
                        "task_id": "Task1885",
                        "trade_row_id": f"DESKREPLAYTRADE-1885-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "source_policy_variant_id": source_policy,
                        "trade_spec_id": row["trade_spec_id"],
                        "candidate_source_id": row["candidate_source_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "strategy_sleeve": row["strategy_sleeve"],
                        "desk_action": row["desk_action"],
                        "desk_action_reason": row["desk_action_reason"],
                        "desk_thesis_state": row["desk_thesis_state"],
                        "desk_budget_multiplier": mult,
                        "financing_specificity_state": row["financing_specificity_state"],
                        "theme_breadth_state": row["theme_breadth_state"],
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
                    "task_id": "Task1885",
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
                    "hold_count": action_counts["hold"],
                    "watch_count": action_counts["watch"],
                    "reduce_count": action_counts["reduce"],
                    "trim_count": action_counts["trim"],
                    "cap_count": action_counts["cap"],
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def metric_rows(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    baseline = {row["policy_variant_id"]: row for row in read_csv(TASK1808 / "task1823_sleeve_replay_metrics.csv")}
    source_attached = {row["policy_variant_id"]: row for row in read_csv(TASK1848 / "task1858_source_attached_replay_metrics.csv")}
    trade_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trade_groups[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_groups[str(row["policy_variant_id"])].append(row)
    out = []
    for policy_id, eq_rows in sorted(equity_groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        tr_rows = trade_groups[policy_id]
        start = replay.parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end_dates = [parse_date(row.get("actual_exit_date")) for row in tr_rows]
        end = max([item for item in end_dates if item is not None] or [start])
        cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
        mdd = replay.max_drawdown(values)
        base_id = str(POLICIES[policy_id]["baseline_policy"])
        source_attached_id = str(POLICIES[policy_id]["source_attached_policy"])
        base = baseline[base_id]
        prev = source_attached[source_attached_id]
        out.append(
            {
                "task_id": "Task1885",
                "policy_variant_id": policy_id,
                "baseline_policy_variant_id": base_id,
                "source_attached_policy_variant_id": source_attached_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr, 6),
                "max_drawdown": round(mdd, 6),
                "trade_count": len(tr_rows),
                "baseline_final_equity": base["final_equity"],
                "baseline_cagr": base["cagr"],
                "baseline_max_drawdown": base["max_drawdown"],
                "source_attached_final_equity": prev["final_equity"],
                "source_attached_cagr": prev["cagr"],
                "source_attached_max_drawdown": prev["max_drawdown"],
                "delta_vs_baseline_final": round(final - to_float(base["final_equity"]), 4),
                "delta_vs_baseline_cagr": round(cagr - to_float(base["cagr"]), 6),
                "delta_vs_baseline_mdd": round(mdd - to_float(base["max_drawdown"]), 6),
                "delta_vs_source_attached_final": round(final - to_float(prev["final_equity"]), 4),
                "delta_vs_source_attached_cagr": round(cagr - to_float(prev["cagr"]), 6),
                "delta_vs_source_attached_mdd": round(mdd - to_float(prev["max_drawdown"]), 6),
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
        parsed = replay.parse_ts(str(row["decision_asof_ts"]))
        window = "IS_2021_2023" if parsed and parsed.year <= 2023 else "OOS_2024_2026Q1"
        groups[(str(row["policy_variant_id"]), window)].append(row)
    rows = []
    for (policy_id, window), items in sorted(groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        rows.append(
            {
                "task_id": "Task1885",
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


def cost_stress_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    idx = 1
    for metric in metrics:
        trades = int(metric["trade_count"])
        for bps in [0, 25, 50, 100]:
            haircut = trades * (bps / 10000.0) * 0.35
            stressed_final = to_float(metric["final_equity"]) * max(0.0, 1.0 - haircut)
            rows.append(
                {
                    "task_id": "Task1885",
                    "cost_stress_id": f"DESKCOST-1885-{idx:04d}",
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


def failure_attribution(trades: list[dict[str, object]], metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    idx = 1
    for label in ["strategy_sleeve", "desk_action", "desk_thesis_state", "financing_specificity_state", "theme_breadth_state"]:
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for trade in trades:
            grouped[str(trade[label])].append(trade)
        for key, items in sorted(grouped.items()):
            rows.append(
                {
                    "task_id": "Task1885",
                    "failure_attr_id": f"DESKFAIL-1885-{idx:04d}",
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
    for metric in metrics:
        rows.append(
            {
                "task_id": "Task1885",
                "failure_attr_id": f"DESKFAIL-1885-{idx:04d}",
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


def expert_review_rows() -> list[dict[str, object]]:
    rows = [
        ("winner_trader", "Hold intact quality/momentum winners through macro volatility unless live dilution or thesis damage is source-specific.", "implemented"),
        ("capital_markets_trader", "Do not treat all SEC active_financing_pressure rows as active dilution; split live, shelf, historical, and boilerplate states.", "implemented"),
        ("rates_trader", "Use rates/liquidity as desk permission context, not global trim.", "implemented"),
        ("sector_specialist", "Use breadth to separate theme drawdown from issuer break.", "implemented"),
        ("risk_engineer", "Validation must prove winner broad trim fell and no outcome field entered assignment.", "implemented"),
    ]
    return [
        {
            "task_id": "Task1878",
            "expert_review_id": f"DESKIMPLREVIEW-1878-{idx:03d}",
            "expert_role": role,
            "critique": critique,
            "implementation_status": status,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, critique, status) in enumerate(rows, 1)
    ]


def config_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1884",
            "policy_config_id": f"DESKPOLICY-1884-{idx:03d}",
            "policy_variant_id": policy_id,
            "source_policy_variant_id": config["source_policy"],
            "slot_cap": config["slot_cap"],
            "policy_freeze_state": "frozen_before_replay",
            "allowed_source_fields": "sec_specificity/winner_thesis/rates_liquidity/theme_breadth/earnings_vendor_gate",
            "forbidden_fields": "future_price/future_return/pnl/drawdown/outcome_label",
            "authority": AUTHORITY,
        }
        for idx, (policy_id, config) in enumerate(POLICIES.items(), 1)
    ]


def gate_closeout(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    verdict = "desk_specific_policy_replay_complete_diagnostic_only"
    if best["joint_target_met"] != "1":
        verdict = "desk_specific_policy_replay_complete_target_not_met"
    gate = [
        {
            "task_id": "Task1885",
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
            "task_id": "Task1885",
            "verdict": verdict,
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "next_action": "audit sleeve attribution after desk-specific replay before adding more micro sizing",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metrics: list[dict[str, object]], split: list[dict[str, object]], cost: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1878-1885 Desk-Specific Policy Replay",
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
        "Implementation summary:",
        "",
        "- SEC financing was repaired from broad `active_financing_pressure` into `live_active_dilution`, `shelf_capacity_watch`, `historical_or_closed_financing`, `boilerplate_or_sparse`, and `source_gap_neutral`.",
        "- Winner desk gained a thesis-intact override using quality beta, sleeve quality, payoff score, volatility cause, expectation, absorption, SEC specificity, and theme breadth.",
        "- Theme breadth was attached from existing pre-entry relative-return fields only.",
        "- Speculative no-entry now requires source-specific `live_active_dilution`.",
        "- Earnings revision remains vendor-blocked and has no assignment effect.",
        "- Replay return source is the prior controlled winner-defense trade set; no new price matching was introduced.",
        "",
        "Leakage audit:",
        "",
        "- Assignment uses only source states known as-of.",
        "- PnL, drawdown, net return, and future outcomes are audit-only.",
        "- Missing raw source remains source gap, not negative evidence.",
        "",
        "| Policy | Final | CAGR | MDD | Source-Attached Final | Delta vs Source | Base Final | Delta vs Base | Trades | Joint Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['source_attached_final_equity']} | {row['delta_vs_source_attached_final']} | {row['baseline_final_equity']} | {row['delta_vs_baseline_final']} | {row['trade_count']} | {row['joint_target_met']} |"
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
            "1. The previous brain cut winners too broadly.",
            "2. This task made the action desk-specific.",
            "3. SEC danger now means live/current dilution, not any financing mention.",
            "4. Strong winners can now hold through macro volatility if the thesis is intact.",
            "5. The replay is still diagnostic only, not accepted for live capital.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1878_input_manifest.csv`",
            "- `task1878_sec_financing_specificity_panel.csv`",
            "- `task1879_winner_thesis_override_panel.csv`",
            "- `task1880_theme_breadth_panel.csv`",
            "- `task1881_l3_desk_relation_edges.csv`",
            "- `task1882_speculative_live_financing_block.csv`",
            "- `task1883_defensive_buffer_validation_panel.csv`",
            "- `task1884_l4_desk_thesis_cards.csv`",
            "- `task1884_l5_desk_specific_budget.csv`",
            "- `task1884_frozen_policy_config.csv`",
            "- `task1885_controlled_desk_replay_trades.csv/equity`",
            "- `task1885_desk_replay_metrics.csv/split_oos/cost_stress`",
            "- `task1885_failure_attribution.csv`",
            "- `task1885_acceptance_gate.csv`",
            "- `task1885_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1878_1885_desk_specific_policy_replay_validate.py`",
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    layers = build_layers()
    budget = layers["task1884_l5_desk_specific_budget.csv"]
    trades, equity = replay_budget(budget)
    metrics = metric_rows(trades, equity)
    split = split_rows(equity)
    cost = cost_stress_rows(metrics)
    fail_attr = failure_attribution(trades, metrics)
    gate, closeout = gate_closeout(metrics)
    outputs = [
        ("task1878_expert_implementation_review.csv", expert_review_rows()),
        *list(layers.items()),
        ("task1884_frozen_policy_config.csv", config_rows()),
        ("task1885_controlled_desk_replay_trades.csv", trades),
        ("task1885_controlled_desk_replay_equity.csv", equity),
        ("task1885_desk_replay_metrics.csv", metrics),
        ("task1885_split_oos_metrics.csv", split),
        ("task1885_cost_stress_metrics.csv", cost),
        ("task1885_failure_attribution.csv", fail_attr),
        ("task1885_acceptance_gate.csv", gate),
        ("task1885_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task1885_closeout.json", closeout[0])
    write_report(metrics, split, cost, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1878_1885] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
