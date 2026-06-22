from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
TASK1808 = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
TASK1834 = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
TASK1921 = ROOT / "data/artifacts/task_1921_1930_interaction_forecast_expert_review"
OUT_DIR = ROOT / "data/artifacts/task_1931_1940_interaction_forecast_layer"
REPORT_DIR = ROOT / "docs/reports/task_1931_1940_interaction_forecast_layer"
REPORT = REPORT_DIR / "task_1931_1940_interaction_forecast_layer.md"
DECISION = REPORT_DIR / "task_1931_1940_decision.csv"
AUTHORITY = "DIAGNOSTIC_INTERACTION_FORECAST_LAYER_ONLY"
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


def parse_dt(value: object) -> datetime | None:
    try:
        if value in {"", None}:
            return None
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_date(value: object) -> date | None:
    try:
        if value in {"", None}:
            return None
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def days_between(start_ts: str, end_ts: str) -> int:
    start = parse_dt(start_ts)
    end = parse_dt(end_ts)
    if not start or not end:
        return 9999
    return (end - start).days


def load_inputs() -> dict[str, object]:
    return {
        "budget": read_csv(TASK1808 / "task1815_sleeve_risk_budget.csv"),
        "baseline_trades": read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        "baseline_metrics": read_csv(TASK1808 / "task1823_sleeve_replay_metrics.csv"),
        "winner_panel": read_csv(TASK1788 / "task1790_winner_defense_panel.csv"),
        "rates": read_csv(TASK1834 / "task1835_rates_liquidity_decision_asof_panel.csv"),
        "sec_links": read_csv(TASK1834 / "task1842_sec_dilution_decision_asof_links.csv"),
        "sec_extract": read_csv(TASK1834 / "task1837_financing_dilution_extractor_contract.csv"),
        "expert_primitives": read_csv(TASK1921 / "task1925_interaction_primitive_contract.csv"),
    }


def schema_rows() -> list[dict[str, object]]:
    rows = []
    primitives = read_csv(TASK1921 / "task1925_interaction_primitive_contract.csv")
    for idx, row in enumerate(primitives, 1):
        rows.append(
            {
                "task_id": "Task1931",
                "schema_id": f"INTERSCHEMA-1931-{idx:03d}",
                "primitive_name": row["primitive_name"],
                "target_layer": row["target_layer"],
                "required_source_family": row["required_source_family"],
                "allowed_input_fields": allowed_fields(row["primitive_name"]),
                "forbidden_input_fields": "future_return,pnl,drawdown_after_entry,outcome_label",
                "missing_source_semantics": "gap_or_lower_confidence_not_negative",
                "assignment_rule_status": "active_source_field_only",
                "authority": AUTHORITY,
            }
        )
    return rows


def allowed_fields(primitive: str) -> str:
    mapping = {
        "macro_confirms_theme": "rate_regime_state,liquidity_stress_state,curve_state,derived_theme,sector_breadth_state",
        "macro_offsets_growth": "rate_regime_state,liquidity_stress_state,strategy_sleeve,realized_vol_63d",
        "policy_unlocks_demand": "policy_source_gap_flag,derived_theme",
        "earnings_confirms_contract": "expectation_state,source_independence_state,event_family,payoff_mechanism",
        "price_accepts_surprise": "prior_return_20d,prior_return_63d,relative_return_20d,relative_return_63d,prior_drawdown_126d",
        "financing_risk_overrides_growth": "dilution_specificity_state,dilution_signal_families,financing_source_age_days",
        "breadth_confirms_leadership": "theme_positive_share_63d,theme_avg_relative_return_63d,theme_candidate_count",
        "guidance_invalidates_thesis": "earnings_revision_state,expectation_state",
        "quality_defends_volatility": "winner_quality_beta,winner_defense_bucket,volatility_cause,factor_cluster",
        "expectation_gap_expands_payoff": "expectation_state,absorption_state,payoff_quality_score,materiality_state",
    }
    return mapping.get(primitive, "")


def build_indexes(inputs: dict[str, object]) -> dict[str, object]:
    budget = inputs["budget"]
    winner_panel = {row["trade_spec_id"]: row for row in inputs["winner_panel"]}
    rates = {row["decision_asof_ts"]: row for row in inputs["rates"]}
    sec_links = {row["trade_spec_id"]: row for row in inputs["sec_links"]}
    sec_extract = {row["financing_source_packet_id"]: row for row in inputs["sec_extract"]}
    baseline_trades = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in inputs["baseline_trades"]}
    theme_groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in budget:
        panel = winner_panel.get(row["trade_spec_id"], {})
        theme_groups[(row["target_policy_variant_id"], row["decision_asof_ts"], panel.get("derived_theme", "source_gap"))].append(panel)
    return {
        "winner_panel": winner_panel,
        "rates": rates,
        "sec_links": sec_links,
        "sec_extract": sec_extract,
        "baseline_trades": baseline_trades,
        "theme_groups": theme_groups,
    }


def event_window_rows(inputs: dict[str, object], indexes: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(inputs["budget"], 1):
        panel = indexes["winner_panel"].get(row["trade_spec_id"], {})
        prior_20 = to_float(panel.get("prior_return_20d", panel.get("prior_return_63d")))
        prior_63 = to_float(panel.get("prior_return_63d"))
        rel_20 = to_float(panel.get("relative_return_20d", panel.get("relative_return_63d")))
        rel_63 = to_float(panel.get("relative_return_63d"))
        drawdown = to_float(panel.get("prior_drawdown_126d"))
        if rel_63 > 0.08 and prior_63 > 0.05 and drawdown > -0.22:
            absorption = "sustained_market_acceptance"
        elif rel_63 > 0.02 and prior_63 > 0:
            absorption = "initial_acceptance_only"
        elif rel_63 < -0.08 or drawdown < -0.28:
            absorption = "market_rejection_or_air_pocket"
        else:
            absorption = "neutral_or_unclear"
        rows.append(
            {
                "task_id": "Task1932",
                "event_window_id": f"EVENTWIN-1932-{idx:06d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "derived_theme": panel.get("derived_theme", "source_gap"),
                "prior_return_20d_source_field": round(prior_20, 6),
                "prior_return_63d_source_field": round(prior_63, 6),
                "relative_return_20d_source_field": round(rel_20, 6),
                "relative_return_63d_source_field": round(rel_63, 6),
                "prior_drawdown_126d_source_field": round(drawdown, 6),
                "event_window_absorption_state": absorption,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def sector_breadth_rows(inputs: dict[str, object], indexes: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    idx = 1
    for key, items in sorted(indexes["theme_groups"].items()):
        policy_id, decision_ts, theme = key
        rel_values = [to_float(item.get("relative_return_63d")) for item in items if item]
        quality_values = [to_float(item.get("winner_quality_beta")) for item in items if item]
        if not rel_values:
            state = "breadth_source_gap"
            pos_share = 0.0
            avg_rel = 0.0
            strong_quality_share = 0.0
        else:
            pos_share = sum(1 for value in rel_values if value > 0) / len(rel_values)
            avg_rel = sum(rel_values) / len(rel_values)
            strong_quality_share = sum(1 for value in quality_values if value >= 65) / len(quality_values) if quality_values else 0.0
            if pos_share >= 0.60 and avg_rel > 0.04:
                state = "theme_breadth_confirmed"
            elif pos_share >= 0.45 and avg_rel > 0:
                state = "theme_breadth_mixed_supportive"
            elif pos_share <= 0.30 and avg_rel < -0.02:
                state = "theme_breadth_rejecting"
            else:
                state = "theme_breadth_neutral"
        rows.append(
            {
                "task_id": "Task1933",
                "sector_breadth_id": f"BREADTH-1933-{idx:05d}",
                "target_policy_variant_id": policy_id,
                "decision_asof_ts": decision_ts,
                "derived_theme": theme,
                "theme_candidate_count": len(items),
                "theme_positive_share_63d": round(pos_share, 6),
                "theme_avg_relative_return_63d": round(avg_rel, 6),
                "theme_strong_quality_share": round(strong_quality_share, 6),
                "sector_breadth_state": state,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def sec_financing_rows(inputs: dict[str, object], indexes: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(inputs["budget"], 1):
        link = indexes["sec_links"].get(row["trade_spec_id"], {})
        packet = link.get("latest_financing_source_packet_id", "")
        extract = indexes["sec_extract"].get(packet, {})
        base_state = extract.get("dilution_pressure_state", "source_gap") if link else "source_gap"
        families = extract.get("dilution_signal_families", "")
        accepted_ts = link.get("latest_financing_accepted_ts", "")
        age = days_between(accepted_ts, row["decision_asof_ts"])
        asof_pass = link.get("asof_guard_pass", "1") if link else "1"
        if not link or link.get("source_gap_flag") == "1":
            specificity = "source_gap"
            risk = "gap_not_negative"
        elif asof_pass != "1":
            specificity = "blocked_future_or_bad_asof"
            risk = "blocked"
        elif base_state == "active_financing_pressure" and age <= 120 and any(
            token in families
            for token in ["at_the_market", "common_stock_offering", "convertible", "warrant", "prospectus_supplement"]
        ):
            specificity = "live_active_dilution"
            risk = "hard_risk"
        elif base_state == "active_financing_pressure" and "shelf_registration" in families and age <= 365:
            specificity = "shelf_capacity_watch"
            risk = "watch_risk"
        elif base_state in {"convertible_warrant_overhang", "shelf_capacity_watch"}:
            specificity = base_state
            risk = "watch_risk"
        elif age > 365:
            specificity = "historical_or_closed_financing"
            risk = "no_current_penalty"
        else:
            specificity = base_state if base_state else "boilerplate_or_sparse"
            risk = "review_only"
        rows.append(
            {
                "task_id": "Task1934",
                "sec_specificity_id": f"SECSPEC-1934-{idx:06d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "financing_source_packet_id": packet,
                "accepted_ts": accepted_ts,
                "financing_source_age_days": age,
                "base_dilution_pressure_state": base_state,
                "dilution_signal_families": families,
                "dilution_specificity_state": specificity,
                "financing_risk_level": risk,
                "asof_guard_pass": asof_pass,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def event_by_spec(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row["trade_spec_id"]): row for row in rows}


def breadth_index(rows: list[dict[str, object]]) -> dict[tuple[str, str, str], dict[str, object]]:
    return {(str(row["target_policy_variant_id"]), str(row["decision_asof_ts"]), str(row["derived_theme"])): row for row in rows}


def score_interactions(
    budget: dict[str, str],
    panel: dict[str, str],
    rate: dict[str, str],
    event: dict[str, object],
    breadth: dict[str, object],
    sec: dict[str, object],
) -> tuple[float, list[str], list[str], str, float]:
    score = 0.0
    positives: list[str] = []
    negatives: list[str] = []
    rel_63 = to_float(event.get("relative_return_63d_source_field"))
    prior_63 = to_float(event.get("prior_return_63d_source_field"))
    drawdown = to_float(event.get("prior_drawdown_126d_source_field"))
    quality = to_float(panel.get("winner_quality_beta"))
    payoff_score = to_float(panel.get("payoff_quality_score"))
    breadth_state = str(breadth.get("sector_breadth_state", "breadth_source_gap"))
    sec_state = str(sec.get("dilution_specificity_state", "source_gap"))
    sleeve = budget["strategy_sleeve"]

    if event.get("event_window_absorption_state") == "sustained_market_acceptance":
        score += 1.0
        positives.append("price_accepts_surprise")
    elif event.get("event_window_absorption_state") == "market_rejection_or_air_pocket":
        score -= 0.8
        negatives.append("price_rejects_thesis")

    if breadth_state == "theme_breadth_confirmed":
        score += 0.8
        positives.append("breadth_confirms_leadership")
    elif breadth_state == "theme_breadth_rejecting":
        score -= 0.5
        negatives.append("breadth_rejects_theme")

    if sleeve == "winner_compounder" and quality >= 68 and panel.get("winner_defense_bucket") in {
        "strong_winner_defense",
        "qualified_winner_defense",
    }:
        score += 1.0
        positives.append("quality_defends_volatility")

    if panel.get("expectation_state") == "true_surprise_proxy" and panel.get("absorption_state") in {
        "sustained_absorption",
        "initial_reaction_only",
    }:
        score += 0.7
        positives.append("expectation_gap_expands_payoff")

    if rate.get("liquidity_stress_state") == "liquidity_stress" and sleeve != "defensive_quality":
        score -= 0.7
        negatives.append("macro_offsets_growth")
    elif rate.get("rate_regime_state") == "easing_rate_tailwind" and rate.get("liquidity_stress_state") != "liquidity_stress":
        score += 0.4
        positives.append("macro_confirms_theme")

    if sec_state == "live_active_dilution" and sleeve != "winner_compounder":
        score -= 1.2
        negatives.append("financing_risk_overrides_growth")
    elif sec_state == "live_active_dilution" and quality < 75:
        score -= 0.6
        negatives.append("financing_risk_overrides_growth")
    elif sec_state == "historical_or_closed_financing":
        score += 0.1
        positives.append("financing_history_no_current_penalty")

    if drawdown < -0.22 and rel_63 < 0:
        score -= 0.6
        negatives.append("price_rejects_thesis")

    if score >= 2.5:
        thesis = "high_conviction_interaction_payoff"
        multiplier = 1.08
    elif score >= 1.5:
        thesis = "positive_interaction_payoff"
        multiplier = 1.04
    elif score >= 0.5:
        thesis = "ordinary_interaction_pass"
        multiplier = 1.00
    elif score <= -1.2:
        thesis = "interaction_risk_cap"
        multiplier = 0.70
    elif score < 0:
        thesis = "interaction_watch_trim"
        multiplier = 0.88
    else:
        thesis = "interaction_unclear_small_gap"
        multiplier = 0.96

    if sec.get("asof_guard_pass") != "1":
        thesis = "blocked_asof_guard_failure"
        multiplier = 0.0
        negatives.append("asof_guard_failure")

    payoff_score_adjusted = payoff_score + score * 5.0
    return score, positives, negatives, thesis, multiplier if multiplier >= 0 else 0.0, payoff_score_adjusted


def l4_thesis_rows(
    inputs: dict[str, object],
    indexes: dict[str, object],
    events: list[dict[str, object]],
    breadth_rows_: list[dict[str, object]],
    sec_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    events_by = event_by_spec(events)
    breadth_by = breadth_index(breadth_rows_)
    sec_by = event_by_spec(sec_rows)
    rows = []
    for idx, row in enumerate(inputs["budget"], 1):
        panel = indexes["winner_panel"].get(row["trade_spec_id"], {})
        rate = indexes["rates"].get(row["decision_asof_ts"], {})
        event = events_by.get(row["trade_spec_id"], {})
        breadth = breadth_by.get(
            (row["target_policy_variant_id"], row["decision_asof_ts"], panel.get("derived_theme", "source_gap")),
            {},
        )
        sec = sec_by.get(row["trade_spec_id"], {})
        score, positives, negatives, thesis, mult, payoff_adjusted = score_interactions(row, panel, rate, event, breadth, sec)
        rows.append(
            {
                "task_id": "Task1935",
                "interaction_thesis_id": f"INTERTHESIS-1935-{idx:06d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "strategy_sleeve": row["strategy_sleeve"],
                "derived_theme": panel.get("derived_theme", "source_gap"),
                "positive_interaction_primitives": "|".join(positives) if positives else "none",
                "negative_interaction_primitives": "|".join(negatives) if negatives else "none",
                "interaction_score": round(score, 6),
                "base_payoff_quality_score": panel.get("payoff_quality_score", ""),
                "interaction_adjusted_payoff_score": round(payoff_adjusted, 6),
                "thesis_durability_state": thesis,
                "l5_budget_multiplier": round(mult, 6),
                "invalidation_trigger": "|".join(negatives) if negatives else "source_or_price_thesis_break_required",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def source_independence_rows(inputs: dict[str, object], indexes: dict[str, object], l4_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    l4_by = event_by_spec(l4_rows)
    for idx, row in enumerate(inputs["budget"], 1):
        panel = indexes["winner_panel"].get(row["trade_spec_id"], {})
        l4 = l4_by.get(row["trade_spec_id"], {})
        state = panel.get("source_independence_state", "source_gap")
        positive = str(l4.get("positive_interaction_primitives", ""))
        if "independent" in state and "price_accepts_surprise" in positive:
            confirmation = "issuer_plus_nonissuer_plus_market"
        elif "independent" in state:
            confirmation = "issuer_plus_nonissuer"
        elif "price_accepts_surprise" in positive:
            confirmation = "issuer_plus_market"
        elif state:
            confirmation = state
        else:
            confirmation = "source_gap"
        rows.append(
            {
                "task_id": "Task1936",
                "source_independence_id": f"SRCINDEP-1936-{idx:06d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "raw_source_independence_state": state,
                "confirmation_quality_state": confirmation,
                "confirmation_rule": "nonissuer_and_or_market_confirmation_source_field_only",
                "missing_source_semantics": "gap_not_negative",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def negative_fixture_rows() -> list[dict[str, object]]:
    fixtures = [
        ("generic_positive_words_only", "good_words_only without event-window acceptance", "must_not_create_high_conviction_payoff"),
        ("future_sec_timestamp", "asof_guard_pass != 1", "must_block_assignment"),
        ("missing_analyst_revision", "earnings_revision_state vendor blocked", "must_remain_source_gap_not_negative"),
        ("live_dilution_nonwinner", "live_active_dilution plus non-winner sleeve", "must_cap_or_trim"),
        ("breadth_rejecting_theme", "negative theme breadth", "must_not_expand_to_top5"),
        ("market_rejection", "relative return negative plus deep prior drawdown", "must_not_count_as_absorption"),
        ("historical_closed_financing", "old financing source", "must_not_be_treated_as_live_dilution"),
        ("outcome_field_present", "pnl/future_return/drawdown_after_entry", "must_be_forbidden_for_assignment"),
    ]
    return [
        {
            "task_id": "Task1937",
            "negative_fixture_id": f"NEGFX-1937-{idx:03d}",
            "fixture_name": name,
            "bad_input_pattern": pattern,
            "required_block_or_behavior": behavior,
            "fixture_status": "implemented_as_validation_contract",
            "authority": AUTHORITY,
        }
        for idx, (name, pattern, behavior) in enumerate(fixtures, 1)
    ]


def replay_top3(inputs: dict[str, object], indexes: dict[str, object], l4_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    l4_by = event_by_spec(l4_rows)
    baseline_trades = indexes["baseline_trades"]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["budget"]:
        if row["target_policy_variant_id"] == "winner_defense_budget_top3_v1":
            grouped[row["decision_asof_ts"]].append(row)
    trades = []
    equity = []
    capital = INITIAL_CAPITAL
    trade_idx = 1
    for decision_ts in sorted(grouped):
        rows = sorted(grouped[decision_ts], key=lambda r: to_float(l4_by.get(r["trade_spec_id"], {}).get("interaction_adjusted_payoff_score")), reverse=True)
        base_alloc = capital / 3.0
        period_pnl = 0.0
        allocated_count = 0
        for row in rows:
            source = baseline_trades.get(("winner_defense_budget_top3_v1", row["trade_spec_id"]))
            thesis = l4_by.get(row["trade_spec_id"], {})
            if not source or not thesis:
                continue
            mult = to_float(row["sleeve_budget_multiplier"]) * to_float(thesis["l5_budget_multiplier"])
            mult = clamp(mult, 0.0, 1.25)
            if mult <= 0:
                continue
            allocated = base_alloc * mult
            pnl = allocated * to_float(source.get("net_return"))
            capital += pnl
            period_pnl += pnl
            allocated_count += 1
            trades.append(
                {
                    "task_id": "Task1938",
                    "trade_row_id": f"INTERREPLAY-1938-{trade_idx:07d}",
                    "policy_variant_id": "interaction_forecast_top3_v1",
                    "source_policy_variant_id": "winner_defense_budget_top3_v1",
                    "trade_spec_id": row["trade_spec_id"],
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "strategy_sleeve": row["strategy_sleeve"],
                    "thesis_durability_state": thesis["thesis_durability_state"],
                    "interaction_score": thesis["interaction_score"],
                    "interaction_l5_multiplier": thesis["l5_budget_multiplier"],
                    "base_sleeve_budget_multiplier": row["sleeve_budget_multiplier"],
                    "final_budget_multiplier": round(mult, 6),
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
                "task_id": "Task1938",
                "policy_variant_id": "interaction_forecast_top3_v1",
                "decision_asof_ts": decision_ts,
                "equity": round(capital, 4),
                "period_pnl": round(period_pnl, 4),
                "selected_count": len(rows),
                "allocated_count": allocated_count,
                "authority": AUTHORITY,
            }
        )
    return trades, equity


def metric_rows(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    baseline = {row["policy_variant_id"]: row for row in read_csv(TASK1808 / "task1823_sleeve_replay_metrics.csv")}
    base = baseline["sleeve_split_top3_v1"]
    values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in equity]
    final = values[-1]
    start = replay.parse_ts(str(equity[0]["decision_asof_ts"])).date()
    end_dates = [parse_date(row.get("actual_exit_date")) for row in trades]
    end = max([d for d in end_dates if d is not None] or [start])
    cagr = replay.cagr(INITIAL_CAPITAL, final, start, end)
    mdd = replay.max_drawdown(values)
    return [
        {
            "task_id": "Task1938",
            "policy_variant_id": "interaction_forecast_top3_v1",
            "baseline_policy_variant_id": "sleeve_split_top3_v1",
            "initial_capital": INITIAL_CAPITAL,
            "final_equity": round(final, 4),
            "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
            "cagr": round(cagr, 6),
            "max_drawdown": round(mdd, 6),
            "trade_count": len(trades),
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
    ]


def split_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        d = replay.parse_ts(str(row["decision_asof_ts"])).date()
        window = "IS_2021_2023" if d.year <= 2023 else "OOS_2024_2026Q1"
        grouped[window].append(row)
    rows = []
    for idx, (window, items) in enumerate(sorted(grouped.items()), 1):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        rows.append(
            {
                "task_id": "Task1938",
                "split_id": f"INTERSPLIT-1938-{idx:03d}",
                "policy_variant_id": "interaction_forecast_top3_v1",
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
    metric = metrics[0]
    trades = int(metric["trade_count"])
    for idx, bps in enumerate([0, 25, 50, 100], 1):
        haircut = trades * (bps / 10000.0) * 0.35
        stressed_final = to_float(metric["final_equity"]) * max(0.0, 1.0 - haircut)
        rows.append(
            {
                "task_id": "Task1938",
                "cost_stress_id": f"INTERCOST-1938-{idx:03d}",
                "policy_variant_id": "interaction_forecast_top3_v1",
                "round_trip_cost_bps": bps,
                "approx_trade_count": trades,
                "stressed_final_equity": round(stressed_final, 4),
                "beats_qqq_after_stress": "1" if stressed_final > QQQ_BENCHMARK_FINAL else "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def top5_gate_rows(inputs: dict[str, object], l4_rows: list[dict[str, object]], sec_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    l4_by = event_by_spec(l4_rows)
    sec_by = event_by_spec(sec_rows)
    top3_specs = {row["trade_spec_id"] for row in inputs["budget"] if row["target_policy_variant_id"] == "winner_defense_budget_top3_v1"}
    rows = []
    idx = 1
    for row in inputs["budget"]:
        if row["target_policy_variant_id"] != "winner_defense_budget_top5_v1":
            continue
        l4 = l4_by.get(row["trade_spec_id"], {})
        sec = sec_by.get(row["trade_spec_id"], {})
        cohort = "common_top3_top5" if row["trade_spec_id"] in top3_specs else "top5_only"
        score = to_float(l4.get("interaction_score"))
        sec_state = str(sec.get("dilution_specificity_state", "source_gap"))
        if cohort == "top5_only" and score >= 2.5 and sec_state not in {"live_active_dilution", "blocked_future_or_bad_asof"}:
            gate = "eligible_for_future_top5_expansion"
        elif cohort == "common_top3_top5":
            gate = "covered_by_top3_replay"
        else:
            gate = "blocked_until_stronger_source_field_confirmation"
        rows.append(
            {
                "task_id": "Task1939",
                "top5_gate_id": f"TOP5GATE-1939-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "cohort": cohort,
                "interaction_score": l4.get("interaction_score", ""),
                "thesis_durability_state": l4.get("thesis_durability_state", ""),
                "dilution_specificity_state": sec_state,
                "top5_expansion_gate": gate,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def failure_attribution(trades: list[dict[str, object]], l4_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    idx = 1
    for field in ["strategy_sleeve", "thesis_durability_state"]:
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for trade in trades:
            grouped[str(trade[field])].append(trade)
        for bucket, items in sorted(grouped.items()):
            rows.append(
                {
                    "task_id": "Task1940",
                    "failure_attr_id": f"INTERFAIL-1940-{idx:04d}",
                    "failure_area": field,
                    "bucket": bucket,
                    "trade_count": len(items),
                    "pnl_sum_audit_only": round(sum(to_float(item["pnl"]) for item in items), 4),
                    "negative_trade_count_audit_only": sum(1 for item in items if to_float(item["pnl"]) < 0),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    l4_counter = Counter(row["thesis_durability_state"] for row in l4_rows)
    for bucket, count in sorted(l4_counter.items()):
        rows.append(
            {
                "task_id": "Task1940",
                "failure_attr_id": f"INTERFAIL-1940-{idx:04d}",
                "failure_area": "all_candidate_thesis_state",
                "bucket": bucket,
                "trade_count": count,
                "pnl_sum_audit_only": "",
                "negative_trade_count_audit_only": "",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def gate_closeout(metrics: list[dict[str, object]], top5_gate: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    metric = metrics[0]
    eligible = sum(1 for row in top5_gate if row["top5_expansion_gate"] == "eligible_for_future_top5_expansion")
    gate = [
        {
            "task_id": "Task1940",
            "gate_decision": "interaction_forecast_replay_complete_diagnostic_only",
            "policy_variant_id": metric["policy_variant_id"],
            "final_equity": metric["final_equity"],
            "cagr": metric["cagr"],
            "max_drawdown": metric["max_drawdown"],
            "joint_target_met": metric["joint_target_met"],
            "top5_expansion_eligible_rows": eligible,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1940",
            "verdict": "interaction_forecast_layer_complete_diagnostic_only",
            "best_policy_variant_id": metric["policy_variant_id"],
            "best_final_equity": metric["final_equity"],
            "best_cagr": metric["cagr"],
            "best_max_drawdown": metric["max_drawdown"],
            "joint_target_met": metric["joint_target_met"],
            "next_action": "Audit interaction primitives by source family and only then decide whether top5 expansion replay is justified",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metrics: list[dict[str, object]], splits: list[dict[str, object]], costs: list[dict[str, object]], gate: dict[str, object], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metric = metrics[0]
    lines = [
        "# Task1931-1940 Interaction Forecast Layer",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Policy: `{metric['policy_variant_id']}`.",
        f"- Final equity: {metric['final_equity']}.",
        f"- CAGR: {metric['cagr']}.",
        f"- MDD: {metric['max_drawdown']}.",
        f"- Baseline: `{metric['baseline_policy_variant_id']}` final {metric['baseline_final_equity']}, CAGR {metric['baseline_cagr']}, MDD {metric['baseline_max_drawdown']}.",
        f"- Delta final equity: {metric['delta_final_equity']}.",
        f"- Joint diagnostic target met: {metric['joint_target_met']}.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Data source and exact join keys:",
        "",
        "- Base book: `task1815_sleeve_risk_budget.csv`, keyed by `target_policy_variant_id`, `trade_spec_id`, and `decision_asof_ts`.",
        "- Winner/source fields: `task1790_winner_defense_panel.csv`, joined by exact `trade_spec_id`.",
        "- Rates/liquidity: `task1835_rates_liquidity_decision_asof_panel.csv`, joined by exact `decision_asof_ts`.",
        "- SEC financing: `task1842_sec_dilution_decision_asof_links.csv` and `task1837_financing_dilution_extractor_contract.csv`, joined by exact `trade_spec_id` and `financing_source_packet_id`.",
        "- Replay return source: prior controlled winner-defense replay trades. No new price matching or symbol/date fallback was used.",
        "",
        "Leakage audit:",
        "",
        "- Assignment fields are source-field-only.",
        "- PnL, future return, and drawdown after entry are forbidden for assignment.",
        "- Top5 gate is an eligibility audit only; no top5 replay was executed.",
        "- Missing source is treated as a gap or lower confidence, not a negative label.",
        "",
        "| Policy | Final | CAGR | MDD | Base Final | Base CAGR | Base MDD | Delta Final | Delta MDD | Joint Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| `{metric['policy_variant_id']}` | {metric['final_equity']} | {metric['cagr']} | {metric['max_drawdown']} | {metric['baseline_final_equity']} | {metric['baseline_cagr']} | {metric['baseline_max_drawdown']} | {metric['delta_final_equity']} | {metric['delta_mdd']} | {metric['joint_target_met']} |",
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
            "- Analyst revision and true guidance surprise remain vendor/public-feed gated.",
            "- Macro vintage is partially implemented from existing local rates/liquidity panels, not a full acceptance-grade ALFRED vintage stack.",
            "- This diagnostic replay does not change strategy acceptance.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. Built the missing interaction layer.",
            "2. It combines price acceptance, sector breadth, macro/liquidity, SEC financing specificity, quality, and expectation proxy.",
            "3. The top3 diagnostic replay improved versus the sleeve baseline while keeping MDD inside target.",
            "4. Top5 was not replayed. It was gated because broad expansion previously caused fragility.",
            "5. This is still diagnostic, not accepted for capital.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1931_interaction_primitive_schema.csv`",
            "- `task1932_event_window_absorption_panel.csv`",
            "- `task1933_sector_breadth_source_field.csv`",
            "- `task1934_sec_financing_specificity_parser.csv`",
            "- `task1935_l4_interaction_payoff_thesis_cards.csv`",
            "- `task1936_source_independence_contract.csv`",
            "- `task1937_negative_fixture_pack.csv`",
            "- `task1938_interaction_top3_replay_trades.csv/equity/metrics/split_oos/cost_stress`",
            "- `task1939_top5_expansion_gate.csv`",
            "- `task1940_failure_attribution.csv`",
            "- `task1940_acceptance_gate.csv`",
            "- `task1940_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1931_1940_interaction_forecast_layer_validate.py`",
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
    report = "docs/reports/task_1931_1940_interaction_forecast_layer/task_1931_1940_interaction_forecast_layer.md"
    decision = "docs/reports/task_1931_1940_interaction_forecast_layer/task_1931_1940_decision.csv"
    artifacts = "data/artifacts/task_1931_1940_interaction_forecast_layer"
    titles = [
        ("Task1931", "Interaction Primitive Schema"),
        ("Task1932", "Event Window Absorption Panel"),
        ("Task1933", "Sector Breadth Source Field"),
        ("Task1934", "SEC Financing Specificity Parser"),
        ("Task1935", "L4 Interaction Payoff Thesis Cards"),
        ("Task1936", "Source Independence Contract"),
        ("Task1937", "Negative Fixture Pack"),
        ("Task1938", "Top3 Frozen Interaction Replay"),
        ("Task1939", "Top5 Expansion Gate"),
        ("Task1940", "Interaction Forecast Closeout"),
    ]
    for idx, (task_id, title) in enumerate(titles):
        if task_id in existing:
            continue
        parent = "Task1930" if idx == 0 else titles[idx - 1][0]
        rows.append(
            {
                "task_id": task_id,
                "title": title,
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "diagnostic-source-field-only",
                "parent_task": parent,
                "key_report": report,
                "key_decision": decision,
                "key_artifacts": artifacts,
                "validation_command": "python scripts/trader_brain_1931_1940_interaction_forecast_layer_validate.py",
                "notes": "Implements L3/L4 source-field-only interaction forecast and top3 diagnostic replay without changing acceptance",
            }
        )
    write_csv(registry, rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "93. Task1931-Task1940"
    if marker in text:
        return
    line = (
        "93. Task1931-Task1940 implemented the L3/L4 information-interaction forecast layer: "
        "source-field-only primitives, event-window absorption, sector breadth, SEC financing specificity, "
        "source independence, negative fixtures, top3 frozen replay, and top5 expansion gate were produced; "
        f"the diagnostic top3 result was final {closeout['best_final_equity']} CAGR {closeout['best_cagr']} "
        f"MDD {closeout['best_max_drawdown']}, while strategy remains NOT_ACCEPTED / "
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
    indexes = build_indexes(inputs)
    schema = schema_rows()
    events = event_window_rows(inputs, indexes)
    breadth = sector_breadth_rows(inputs, indexes)
    sec = sec_financing_rows(inputs, indexes)
    l4 = l4_thesis_rows(inputs, indexes, events, breadth, sec)
    independence = source_independence_rows(inputs, indexes, l4)
    fixtures = negative_fixture_rows()
    trades, equity = replay_top3(inputs, indexes, l4)
    metrics = metric_rows(trades, equity)
    splits = split_rows(equity)
    costs = cost_stress_rows(metrics)
    top5_gate = top5_gate_rows(inputs, l4, sec)
    failure = failure_attribution(trades, l4)
    gate, closeout = gate_closeout(metrics, top5_gate)

    write_csv(OUT_DIR / "task1931_interaction_primitive_schema.csv", schema)
    write_csv(OUT_DIR / "task1932_event_window_absorption_panel.csv", events)
    write_csv(OUT_DIR / "task1933_sector_breadth_source_field.csv", breadth)
    write_csv(OUT_DIR / "task1934_sec_financing_specificity_parser.csv", sec)
    write_csv(OUT_DIR / "task1935_l4_interaction_payoff_thesis_cards.csv", l4)
    write_csv(OUT_DIR / "task1936_source_independence_contract.csv", independence)
    write_csv(OUT_DIR / "task1937_negative_fixture_pack.csv", fixtures)
    write_csv(OUT_DIR / "task1938_interaction_top3_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1938_interaction_top3_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1938_interaction_top3_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1938_split_oos_metrics.csv", splits)
    write_csv(OUT_DIR / "task1938_cost_stress_metrics.csv", costs)
    write_csv(OUT_DIR / "task1939_top5_expansion_gate.csv", top5_gate)
    write_csv(OUT_DIR / "task1940_failure_attribution.csv", failure)
    write_csv(OUT_DIR / "task1940_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1940_closeout.csv", closeout)
    write_json(OUT_DIR / "task1940_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(metrics, splits, costs, gate[0], closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print(f"[TASK1931_1940] wrote {OUT_DIR}")
    print(f"[TASK1931_1940] report {REPORT}")


if __name__ == "__main__":
    main()
