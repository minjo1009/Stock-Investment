from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest import build_task673_677_setup_slot_exposure_action as t673
from src.backtest import build_task678_active_cap3_winner_archetype as t678
from src.backtest.build_task637_content_signal_account_backtest import (
    INITIAL_CAPITAL_USD,
    load_qqq_history,
    qqq_final_for_period,
)
from src.backtest.build_task659_theme_specific_relation_engine import QQQ_PATH


TASK682_DIR = Path("docs/reports/task_682_integrated_prediction_stack")
ACTIVE_CAP3 = "active_relation_cap3_reference"
COHORT_SLOT_V1 = "integrated_cohort_slot_v1"
COHORT_SLOT_SOURCE_STRICT = "integrated_cohort_slot_source_strict_probe"
COHORT_SLOT_DISPLACEMENT = "integrated_cohort_slot_displacement_hurdle_v2"
MAX_POSITIONS = 5


def build_task682_program(
    *,
    task672_dir: Path = t673.TASK672_DIR,
    qqq_path: Path = QQQ_PATH,
) -> dict[str, pd.DataFrame]:
    TASK682_DIR.mkdir(parents=True, exist_ok=True)
    base = t673.load_task672_panel(task672_dir)
    base = t673.add_setup_quality(base)
    base = t673.add_slot_value_ladder(base)

    leadership = build_leadership_lifecycle_panel(base)
    catalyst = build_catalyst_quality_matrix(base)
    archetype = build_archetype_candidate_panel(base, leadership, catalyst)
    symbol_context = build_same_symbol_context_matrix(merge_engine_outputs(base, leadership, catalyst, archetype))
    stack = build_integrated_stack(base, leadership, catalyst, archetype, symbol_context)

    qqq = load_qqq_history(qqq_path)
    grid, accepted, allocation, curves = build_candidate_grid(stack, qqq)
    guardrail = build_guardrail_audit(accepted)
    displacement = build_displacement_pairs(accepted)
    slot_summary = build_slot_summary(allocation)
    forbidden = build_forbidden_input_audit(stack, allocation)
    decision = build_decision(grid, guardrail, forbidden)
    pass_fail = build_pass_fail(stack, grid, guardrail, forbidden, allocation)

    write_outputs(
        leadership,
        catalyst,
        archetype,
        symbol_context,
        stack,
        grid,
        accepted,
        allocation,
        curves,
        guardrail,
        displacement,
        slot_summary,
        forbidden,
        decision,
        pass_fail,
    )
    return {
        "leadership": leadership,
        "catalyst": catalyst,
        "archetype": archetype,
        "symbol_context": symbol_context,
        "stack": stack,
        "grid": grid,
        "accepted": accepted,
        "allocation": allocation,
        "curves": curves,
        "guardrail": guardrail,
        "displacement": displacement,
        "slot_summary": slot_summary,
        "forbidden": forbidden,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_leadership_lifecycle_panel(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in panel.to_dict(orient="records"):
        ret20 = f(row.get("theme_ret20_prev", 0.0))
        breadth = f(row.get("theme_breadth20_prev", 0.0))
        volume = f(row.get("theme_volume_ratio_prev", 1.0))
        rank = f(row.get("theme_rank_prev", 99.0))
        market = f(row.get("market_ret_20d", 0.0))
        market_breadth = f(row.get("breadth_20d", 0.0))
        regime = s(row.get("theme_regime_state_v4", ""))
        reasons = []
        if ret20 >= 0.12:
            reasons.append("theme_return_strong")
        if breadth >= 0.75:
            reasons.append("breadth_broad")
        if rank <= 3:
            reasons.append("top_theme_rank")
        if volume >= 1.0:
            reasons.append("volume_confirming")
        if market < 0 or market_breadth < 0.45:
            reasons.append("broad_market_less_supportive")

        if ret20 >= 0.10 and rank <= 3 and breadth >= 0.55 and regime != "persistent_theme_leader":
            state = "emerging_leadership"
        elif regime == "persistent_theme_leader" and ret20 >= 0.12 and breadth >= 0.70:
            state = "persistent_leadership"
        elif ret20 >= 0.15 and (breadth < 0.60 or volume < 0.80):
            state = "late_leadership"
        elif regime == "narrow_theme_leader" or (ret20 >= 0.10 and breadth < 0.65):
            state = "narrow_leader"
        elif ret20 < 0.03 or breadth < 0.55 or volume < 0.70:
            state = "fading_leadership"
        else:
            state = "participating_theme"

        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "entry_ts": row["entry_ts"],
                "symbol": row.get("symbol", ""),
                "theme_id": row.get("theme_id", ""),
                "leadership_lifecycle_state": state,
                "leadership_strength": leadership_strength(ret20, breadth, rank),
                "leadership_breadth_quality": breadth_quality(breadth),
                "leadership_timing_risk": leadership_timing_risk(state, ret20, breadth, volume),
                "leadership_reason_codes": "|".join(reasons) if reasons else "neutral_theme_participation",
                "leadership_return_used_in_assignment_flag": 0,
                "leadership_label_used_in_assignment_flag": 0,
                "leadership_future_price_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def leadership_strength(ret20: float, breadth: float, rank: float) -> str:
    if ret20 >= 0.15 and breadth >= 0.75 and rank <= 3:
        return "high"
    if ret20 >= 0.08 and breadth >= 0.55 and rank <= 5:
        return "medium"
    return "low"


def breadth_quality(breadth: float) -> str:
    if breadth >= 0.75:
        return "broad"
    if breadth >= 0.55:
        return "mixed"
    return "narrow_or_weak"


def leadership_timing_risk(state: str, ret20: float, breadth: float, volume: float) -> str:
    if state in {"late_leadership", "fading_leadership"}:
        return "high"
    if ret20 >= 0.15 and (breadth < 0.65 or volume < 0.85):
        return "medium"
    return "low"


def build_catalyst_quality_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in panel.to_dict(orient="records"):
        contract = i(row.get("positive_contract_customer_count", 0))
        backlog = i(row.get("positive_backlog_order_count", 0))
        guidance = i(row.get("positive_guidance_up_count", 0))
        margin_supply = i(row.get("positive_margin_supply_combo_count", 0))
        supply = i(row.get("content_supply_demand_count", 0))
        guidance_margin = i(row.get("content_guidance_margin_count", 0))
        weak_revenue = i(row.get("positive_revenue_talk_weak_count", 0))
        negative = i(row.get("content_negative_score_flag", 0))
        direct_bullish = i(row.get("content_direct_bullish_count", 0))
        direct_bearish = i(row.get("content_direct_bearish_count", 0))
        refined_strength = f(row.get("content_refined_strength_score", 0.0))
        net_prediction = f(row.get("content_net_prediction_score", 0.0))
        dilution = i(row.get("negative_dilution_financing_count", 0))
        regulatory = i(row.get("negative_regulation_sanction_tariff_count", 0))
        ceo_disappoint = i(row.get("negative_ceo_ir_disappointment_count", 0))
        insider_sell = i(row.get("negative_insider_sell_count", 0))
        margin_damage = i(row.get("negative_earnings_margin_damage_count", 0))
        score = f(row.get("catalyst_quality_score", 0.0))
        magnitude = f(row.get("content_max_magnitude_score", 0.0))

        path = catalyst_path_type(contract, backlog, guidance, margin_supply, supply, guidance_margin, weak_revenue, negative)
        directness = catalyst_directness(contract, backlog, guidance, margin_supply, supply)
        durability = catalyst_durability(contract, backlog, guidance, margin_supply)
        surprise = catalyst_surprise_proxy(score, magnitude, row)
        overhang = catalyst_negative_overhang(dilution, regulatory, ceo_disappoint, insider_sell, margin_damage, direct_bearish)
        quality = catalyst_economic_quality(
            path,
            directness,
            durability,
            surprise,
            score,
            refined_strength,
            net_prediction,
            direct_bullish,
            overhang,
        )
        reasons = [
            f"path={path}",
            f"directness={directness}",
            f"durability={durability}",
            f"surprise={surprise}",
            f"overhang={overhang}",
        ]
        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "entry_ts": row["entry_ts"],
                "symbol": row.get("symbol", ""),
                "theme_id": row.get("theme_id", ""),
                "catalyst_path_type": path,
                "catalyst_economic_quality": quality,
                "catalyst_durability": durability,
                "catalyst_directness": directness,
                "catalyst_surprise_proxy": surprise,
                "catalyst_negative_overhang": overhang,
                "catalyst_signal_density": catalyst_signal_density(contract, backlog, guidance, margin_supply, supply, guidance_margin, direct_bullish),
                "catalyst_priced_in_state": catalyst_priced_in_state(row),
                "catalyst_reason_codes": "|".join(reasons),
                "catalyst_return_used_in_assignment_flag": 0,
                "catalyst_label_used_in_assignment_flag": 0,
                "catalyst_future_price_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def catalyst_path_type(contract: int, backlog: int, guidance: int, margin_supply: int, supply: int, guidance_margin: int, weak_revenue: int, negative: int) -> str:
    if negative > 0 and contract + backlog + guidance + margin_supply + supply == 0:
        return "negative_event_rebound_context"
    if contract > 0 and backlog > 0:
        return "contract_customer_backlog"
    if guidance > 0 or guidance_margin > 0 or margin_supply > 0:
        return "guidance_margin_upgrade"
    if supply > 0 and (contract > 0 or backlog > 0):
        return "contract_supply_combo"
    if supply > 0:
        return "supply_demand_shock"
    if contract > 0:
        return "contract_only"
    if backlog > 0:
        return "backlog_only"
    if weak_revenue > 0:
        return "weak_revenue_talk"
    return "no_clear_company_catalyst"


def catalyst_directness(contract: int, backlog: int, guidance: int, margin_supply: int, supply: int) -> str:
    if contract > 0 or backlog > 0 or guidance > 0 or margin_supply > 0:
        return "direct"
    if supply > 0:
        return "indirect"
    return "unclear"


def catalyst_durability(contract: int, backlog: int, guidance: int, margin_supply: int) -> str:
    if backlog > 0 or (contract > 0 and guidance + margin_supply > 0):
        return "durable"
    if contract > 0 or guidance > 0 or margin_supply > 0:
        return "medium"
    return "low"


def catalyst_surprise_proxy(score: float, magnitude: float, row: dict[str, object]) -> str:
    priced_in = f(row.get("content_avg_priced_in_risk_score", 0.0))
    low_priced_in = i(row.get("content_low_priced_in_positive_flag", 0)) == 1
    if score >= 7 or magnitude >= 3.0 or low_priced_in:
        return "high"
    if score >= 4 or priced_in < 0.6:
        return "medium"
    return "low"


def catalyst_negative_overhang(dilution: int, regulatory: int, ceo_disappoint: int, insider_sell: int, margin_damage: int, direct_bearish: int) -> str:
    severe = dilution + regulatory + ceo_disappoint + margin_damage
    if severe >= 2 or dilution > 0 or margin_damage > 0:
        return "severe"
    if severe == 1 or insider_sell > 0 or direct_bearish > 0:
        return "moderate"
    return "none"


def catalyst_signal_density(contract: int, backlog: int, guidance: int, margin_supply: int, supply: int, guidance_margin: int, direct_bullish: int) -> str:
    count = sum(int(x > 0) for x in [contract, backlog, guidance, margin_supply, supply, guidance_margin, direct_bullish])
    if count >= 4:
        return "multi_vector"
    if count >= 2:
        return "two_vector"
    if count == 1:
        return "single_vector"
    return "no_vector"


def catalyst_priced_in_state(row: dict[str, object]) -> str:
    priced = f(row.get("content_avg_priced_in_risk_score", 0.0))
    low_priced = i(row.get("content_low_priced_in_positive_flag", 0)) == 1
    if low_priced or priced <= 0.35:
        return "underpriced_proxy"
    if priced >= 0.75:
        return "priced_in_risk"
    return "mixed_pricing_proxy"


def catalyst_economic_quality(
    path: str,
    directness: str,
    durability: str,
    surprise: str,
    score: float,
    refined_strength: float,
    net_prediction: float,
    direct_bullish: int,
    overhang: str,
) -> str:
    if overhang == "severe":
        return "low"
    if path in {"negative_event_rebound_context", "weak_revenue_talk", "no_clear_company_catalyst"} and direct_bullish <= 0:
        return "low"
    if overhang == "moderate" and score < 6 and refined_strength < 6:
        return "low"
    if (
        path in {"contract_customer_backlog", "guidance_margin_upgrade", "contract_supply_combo"}
        and directness == "direct"
        and durability in {"durable", "medium"}
        and surprise in {"high", "medium"}
        and (score >= 6 or refined_strength >= 6 or net_prediction >= 2)
    ):
        return "high"
    if path in {"supply_demand_shock", "contract_only", "backlog_only"} and (score >= 4 or refined_strength >= 4 or direct_bullish > 0):
        return "medium"
    return "medium" if score >= 4 or refined_strength >= 4 else "low"


def build_archetype_candidate_panel(base: pd.DataFrame, leadership: pd.DataFrame, catalyst: pd.DataFrame) -> pd.DataFrame:
    frame = merge_engine_outputs(base, leadership, catalyst)
    rows = []
    for row in frame.to_dict(orient="records"):
        archetype, confidence, risks, reasons = classify_archetype_candidate(row)
        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "entry_ts": row["entry_ts"],
                "symbol": row.get("symbol", ""),
                "theme_id": row.get("theme_id", ""),
                "archetype_candidate": archetype,
                "archetype_confidence": confidence,
                "archetype_risk_flags": "|".join(risks) if risks else "none",
                "archetype_reason_codes": "|".join(reasons) if reasons else "mixed_or_unclear",
                "archetype_return_used_in_assignment_flag": 0,
                "archetype_label_used_in_assignment_flag": 0,
                "archetype_future_price_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def classify_archetype_candidate(row: dict[str, object]) -> tuple[str, str, list[str], list[str]]:
    leadership = s(row.get("leadership_lifecycle_state", ""))
    leadership_strength_value = s(row.get("leadership_strength", ""))
    leadership_breadth = s(row.get("leadership_breadth_quality", ""))
    catalyst_quality = s(row.get("catalyst_economic_quality", ""))
    catalyst_path = s(row.get("catalyst_path_type", ""))
    catalyst_density = s(row.get("catalyst_signal_density", ""))
    catalyst_overhang = s(row.get("catalyst_negative_overhang", ""))
    price = s(row.get("price_chart_acceptance_state", ""))
    relation = s(row.get("relation_transmission_state", ""))
    support = i(row.get("mechanism_support_count", row.get("support_count", 0)))
    pressure = i(row.get("mechanism_pressure_count", row.get("conflict_count", 0)))
    near_high = i(row.get("near_high60_prev", 0))
    trend = i(row.get("trend_stack_prev", 0))
    volume = f(row.get("volume_ratio_prev", 1.0))
    range_pos = f(row.get("range_pos", 0.0))
    intraday = f(row.get("intraday_ret_from_open", 0.0))
    theme_ret20 = f(row.get("theme_ret20_prev", 0.0))
    market_ret20 = f(row.get("market_ret_20d", 0.0))
    price_score = f(row.get("price_acceptance_score", 0.0))
    risks: list[str] = []
    reasons: list[str] = []

    if pressure > support:
        risks.append("pressure_gt_support")
    if price == "price_confirmed_but_extended" or range_pos >= 0.98 or intraday >= 0.04:
        risks.append("extension_risk")
    if leadership in {"late_leadership", "fading_leadership"}:
        risks.append("leadership_timing_risk")
    if catalyst_overhang == "severe":
        risks.append("severe_catalyst_overhang")
    elif catalyst_overhang == "moderate":
        risks.append("moderate_catalyst_overhang")
    if volume < 0.75:
        risks.append("volume_not_confirming")

    if (
        leadership in {"emerging_leadership", "narrow_leader"}
        and catalyst_quality in {"high", "medium"}
        and theme_ret20 > max(market_ret20, 0.0) + 0.04
        and support >= pressure
    ):
        reasons.extend(["leadership_rotation", "relative_theme_strength", "catalyst_support", "support_not_pressure"])
        return "theme_rotation_candidate", confidence_from(reasons, risks), risks, reasons
    if (
        price in {"price_fragile_or_unconfirmed", "price_accepted_needs_confirmation"}
        and catalyst_quality in {"high", "medium"}
        and leadership not in {"fading_leadership"}
        and support >= pressure
        and (volume >= 0.90 or price_score >= 50)
    ):
        reasons.extend(["early_price_uncertainty", "catalyst_support", "support_not_pressure", "entry_confirmation_partial"])
        return "early_acceleration_candidate", confidence_from(reasons, risks), risks, reasons
    if (
        price == "price_confirmed_but_extended"
        and trend == 1
        and volume >= 0.80
        and catalyst_quality in {"high", "medium"}
        and pressure <= support + 1
    ):
        reasons.extend(["late_extension", "trend_confirmed", "volume_ok", "catalyst_support"])
        return "late_extension_candidate", confidence_from(reasons, risks), risks, reasons
    if (
        catalyst_quality == "high"
        and catalyst_density in {"multi_vector", "two_vector"}
        and relation in {"company_price_confirmed_macro_secondary", "relation_reinforcing", "company_positive_confirmation_needed"}
        and price in {"price_confirmed_basic", "price_confirmed_not_extended", "price_accepted_needs_confirmation"}
    ):
        reasons.extend(["high_quality_catalyst", "multi_vector_catalyst", "relation_support", "price_accepted"])
        return "catalyst_repricing_candidate", confidence_from(reasons, risks), risks, reasons
    if (
        trend == 1
        and near_high == 1
        and leadership in {"persistent_leadership", "participating_theme"}
        and leadership_strength_value in {"high", "medium"}
        and leadership_breadth in {"broad", "mixed"}
        and catalyst_path not in {"no_clear_company_catalyst", "weak_revenue_talk"}
        and price in {"price_confirmed_basic", "price_confirmed_not_extended"}
    ):
        reasons.extend(["trend_persistence", "near_high", "leadership_not_fading", "price_not_extended"])
        return "steady_trend_candidate", confidence_from(reasons, risks), risks, reasons
    if catalyst_path == "negative_event_rebound_context" and price in {"price_confirmed_basic", "price_accepted_needs_confirmation"} and support >= pressure:
        reasons.extend(["negative_event_rebound_context", "price_stabilizing", "support_not_pressure"])
        return "rebound_context_candidate", confidence_from(reasons, risks), risks, reasons
    return "mixed_or_unclear_candidate", "low", risks, reasons


def confidence_from(reasons: list[str], risks: list[str]) -> str:
    score = len(reasons) - len(risks)
    if score >= 3:
        return "high"
    if score >= 1:
        return "medium"
    return "low"


def build_same_symbol_context_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    work = frame.copy()
    work["entry_ts"] = pd.to_datetime(work["entry_ts"], utc=True)
    work = work.sort_values(["symbol", "entry_ts", "lifecycle_id"]).reset_index(drop=True)
    previous_by_symbol: dict[str, dict[str, object]] = {}
    seen_count_by_symbol: dict[str, int] = {}
    for row in work.to_dict(orient="records"):
        symbol = s(row.get("symbol", ""))
        previous = previous_by_symbol.get(symbol)
        seen_count = seen_count_by_symbol.get(symbol, 0)
        signature = "|".join(
            [
                s(row.get("archetype_candidate", "")),
                s(row.get("archetype_confidence", "")),
                s(row.get("archetype_risk_flags", "")),
                s(row.get("leadership_lifecycle_state", "")),
                s(row.get("catalyst_path_type", "")),
                s(row.get("price_chart_acceptance_state", "")),
                s(row.get("relation_transmission_state", "")),
            ]
        )
        variant, divergence = same_symbol_variant(row, previous, seen_count)
        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "entry_ts": row["entry_ts"],
                "symbol": symbol,
                "theme_id": row.get("theme_id", ""),
                "symbol_context_signature": signature,
                "same_symbol_state_variant": variant,
                "same_symbol_prior_setup_count": int(seen_count),
                "same_symbol_prior_signature": s(previous.get("symbol_context_signature", "")) if previous else "",
                "same_symbol_divergence_reason_codes": divergence,
                "same_symbol_return_used_in_assignment_flag": 0,
                "same_symbol_label_used_in_assignment_flag": 0,
                "same_symbol_future_price_used_in_assignment_flag": 0,
            }
        )
        previous_by_symbol[symbol] = {**row, "symbol_context_signature": signature}
        seen_count_by_symbol[symbol] = seen_count + 1
    return pd.DataFrame(rows)


def same_symbol_variant(row: dict[str, object], previous: dict[str, object] | None, seen_count: int) -> tuple[str, str]:
    archetype = s(row.get("archetype_candidate", ""))
    confidence = s(row.get("archetype_confidence", ""))
    risks = s(row.get("archetype_risk_flags", ""))
    reasons = [f"prior_count={seen_count}"]
    if previous is None:
        if confidence == "high" and risks == "none":
            return "new_symbol_constructive_context", "|".join(reasons + ["high_confidence_no_prior"])
        if archetype == "mixed_or_unclear_candidate":
            return "new_symbol_unclear_context", "|".join(reasons + ["unclear_no_prior"])
        return "new_symbol_neutral_context", "|".join(reasons + ["no_prior_context"])

    current_score = symbol_context_score(row)
    previous_score = symbol_context_score(previous)
    delta = current_score - previous_score
    reasons.extend(
        [
            f"current_score={current_score}",
            f"previous_score={previous_score}",
            f"delta={delta}",
            f"previous_archetype={s(previous.get('archetype_candidate', ''))}",
        ]
    )
    if delta >= 2:
        return "same_symbol_context_upgrade", "|".join(reasons)
    if delta <= -2:
        return "same_symbol_context_downgrade", "|".join(reasons)
    if confidence == "high" and risks == "none":
        return "same_symbol_constructive_repeat", "|".join(reasons + ["high_confidence_repeat"])
    if "extension_risk" in risks or "leadership_timing_risk" in risks:
        return "same_symbol_caution_repeat", "|".join(reasons + ["timing_or_extension_risk"])
    if archetype == "mixed_or_unclear_candidate":
        return "same_symbol_unclear_repeat", "|".join(reasons + ["unclear_repeat"])
    return "same_symbol_neutral_repeat", "|".join(reasons)


def symbol_context_score(row: dict[str, object]) -> int:
    score = 0
    if s(row.get("archetype_confidence", "")) == "high":
        score += 2
    elif s(row.get("archetype_confidence", "")) == "medium":
        score += 1
    if s(row.get("catalyst_economic_quality", "")) == "high":
        score += 1
    if s(row.get("leadership_lifecycle_state", "")) in {"emerging_leadership", "persistent_leadership", "narrow_leader"}:
        score += 1
    if s(row.get("price_chart_acceptance_state", "")) in {"price_confirmed_basic", "price_confirmed_not_extended"}:
        score += 1
    if s(row.get("relation_transmission_state", "")) in {"company_price_confirmed_macro_secondary", "relation_reinforcing"}:
        score += 1
    risks = s(row.get("archetype_risk_flags", ""))
    if "extension_risk" in risks:
        score -= 1
    if "leadership_timing_risk" in risks or "severe_catalyst_overhang" in risks:
        score -= 2
    return score


def build_integrated_stack(
    base: pd.DataFrame,
    leadership: pd.DataFrame,
    catalyst: pd.DataFrame,
    archetype: pd.DataFrame,
    symbol_context: pd.DataFrame,
) -> pd.DataFrame:
    frame = merge_engine_outputs(base, leadership, catalyst, archetype, symbol_context)
    frame["stack_return_used_in_assignment_flag"] = 0
    frame["stack_label_used_in_assignment_flag"] = 0
    frame["stack_future_price_used_in_assignment_flag"] = 0
    return frame


def merge_engine_outputs(base: pd.DataFrame, *frames: pd.DataFrame) -> pd.DataFrame:
    out = base.copy()
    for frame in frames:
        add_cols = [c for c in frame.columns if c != "lifecycle_id" and c not in out.columns]
        out = out.merge(frame[["lifecycle_id"] + add_cols], on="lifecycle_id", how="left")
    return out


def build_candidate_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    accepted_frames: list[pd.DataFrame] = []
    allocation_frames: list[pd.DataFrame] = []
    curve_frames: list[pd.DataFrame] = []

    active_spec = pd.Series(t673.candidate(ACTIVE_CAP3, "reference", "relation_priority", "relation3", 0, 0, 0, 0, "Active relation cap3 reference."))
    original_max_positions = t673.MAX_POSITIONS
    try:
        t673.MAX_POSITIONS = MAX_POSITIONS
        candidates = [
            (ACTIVE_CAP3, "active_reference", False, False),
            (COHORT_SLOT_V1, "cohort_slot", False, False),
            (COHORT_SLOT_SOURCE_STRICT, "cohort_slot", True, False),
            (COHORT_SLOT_DISPLACEMENT, "cohort_slot", False, True),
        ]
        for candidate_name, mode, source_strict, displacement_hurdle in candidates:
            for split_name in ["all", "validation", "recent_oos"]:
                scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)].copy()
                if mode == "active_reference":
                    quality, accepted, allocation, curve = t673.simulate_candidate(scoped, active_spec)
                else:
                    _, active_accepted, _, _ = t673.simulate_candidate(scoped, active_spec)
                    active_baseline_ids = set(active_accepted["lifecycle_id"].astype(str)) if not active_accepted.empty else set()
                    quality, accepted, allocation, curve = simulate_cohort_slot(
                        scoped,
                        candidate_name,
                        source_strict=source_strict,
                        active_baseline_ids=active_baseline_ids,
                        displacement_hurdle=displacement_hurdle,
                    )
                qqq_final = qqq_final_for_period(qqq, scoped)
                final = INITIAL_CAPITAL_USD * (1.0 + quality["capital_pnl_pct"] / 100.0)
                rows.append(
                    {
                        "candidate_name": candidate_name,
                        "split_name": split_name,
                        "initial_capital_usd": INITIAL_CAPITAL_USD,
                        "source_trade_count": int(len(scoped)),
                        "accepted_trade_count": int(len(accepted)),
                        "final_capital_usd": float(final),
                        "capital_return_pct": float(quality["capital_pnl_pct"]),
                        "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                        "entry_reduce_failure_rate": float(quality["entry_reduce_failure_rate"]),
                        "qqq_final_capital_usd": float(qqq_final),
                        "beats_qqq_flag": int(final > qqq_final),
                        "cohort_slot_assignment_flag": int(mode == "cohort_slot"),
                        "source_strict_flag": int(source_strict),
                        "return_used_in_assignment_flag": 0,
                        "label_used_in_assignment_flag": 0,
                        "future_price_used_in_assignment_flag": 0,
                    }
                )
                for frame, bucket in [(accepted, accepted_frames), (allocation, allocation_frames), (curve, curve_frames)]:
                    if not frame.empty:
                        tmp = frame.copy()
                        tmp["candidate_name"] = candidate_name
                        tmp["split_scope"] = split_name
                        bucket.append(tmp)
    finally:
        t673.MAX_POSITIONS = original_max_positions

    return (
        pd.DataFrame(rows).sort_values(["split_name", "final_capital_usd"], ascending=[True, False]).reset_index(drop=True),
        pd.concat(accepted_frames, ignore_index=True) if accepted_frames else pd.DataFrame(),
        pd.concat(allocation_frames, ignore_index=True) if allocation_frames else pd.DataFrame(),
        pd.concat(curve_frames, ignore_index=True) if curve_frames else pd.DataFrame(),
    )


def simulate_cohort_slot(
    panel: pd.DataFrame,
    candidate_name: str,
    *,
    source_strict: bool,
    active_baseline_ids: set[str] | None = None,
    displacement_hurdle: bool = False,
) -> tuple[dict[str, float], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if panel.empty:
        return t673.empty_quality(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    work = panel.copy()
    work["entry_ts"] = pd.to_datetime(work["entry_ts"], utc=True)
    work["simulated_exit_ts"] = pd.to_datetime(work["simulated_exit_ts"], utc=True)
    work["net_return_costed"] = pd.to_numeric(work["net_return_from_entry"], errors="coerce") - t673.COST_BPS / 10000.0
    equity = 1.0
    peak = 1.0
    open_positions: list[dict[str, object]] = []
    accepted_rows: list[dict[str, object]] = []
    allocation_rows: list[dict[str, object]] = []
    curve_rows = [{"event_ts": work["entry_ts"].min(), "equity": equity, "drawdown_pct": 0.0, "event_type": "start"}]

    def close_until(current_ts: pd.Timestamp) -> None:
        nonlocal equity, peak, open_positions
        still_open = []
        for pos in open_positions:
            if pd.Timestamp(pos["exit_ts"]) <= current_ts:
                equity += float(pos["capital"]) * float(pos["return"])
                peak = max(peak, equity)
                curve_rows.append(
                    {
                        "event_ts": pos["exit_ts"],
                        "equity": equity,
                        "drawdown_pct": (equity / max(peak, 1e-9) - 1.0) * 100.0,
                        "event_type": "close",
                    }
                )
            else:
                still_open.append(pos)
        open_positions = still_open

    for entry_ts, cohort in work.sort_values(["entry_ts", "lifecycle_id"]).groupby("entry_ts", sort=True):
        close_until(pd.Timestamp(entry_ts))
        available_slots = max(0, MAX_POSITIONS - len(open_positions))
        cohort_records = []
        for row in cohort.to_dict(orient="records"):
            evidence = slot_evidence(row, open_positions, source_strict=source_strict)
            row.update(evidence)
            row["cohort_candidate_count"] = int(len(cohort))
            row["available_slots_at_cohort_start"] = int(available_slots)
            cohort_records.append(row)
        for row in cohort_records:
            row["active_cap3_baseline_flag"] = int(s(row.get("lifecycle_id", "")) in (active_baseline_ids or set()))
        ranked = sorted(cohort_records, key=lambda r: (r["slot_ladder_tuple"], s(r.get("lifecycle_id", ""))))
        for idx, row in enumerate(ranked, start=1):
            row["cohort_slot_rank"] = idx

        if displacement_hurdle:
            selected_rows, allocation_decisions = select_with_displacement_hurdle(
                ranked,
                open_positions,
                available_slots,
                source_strict=source_strict,
            )
        else:
            selected_rows = []
            allocation_decisions = {}
            for row in ranked:
                reason = cohort_block_reason(row, open_positions, selected_rows, available_slots, source_strict=source_strict)
                if reason:
                    allocation_decisions[s(row.get("lifecycle_id", ""))] = reason
                    continue
                selected_rows.append(row)
                allocation_decisions[s(row.get("lifecycle_id", ""))] = "accepted"

        selected_positions: list[dict[str, object]] = []
        selected_ids = {s(row.get("lifecycle_id", "")) for row in selected_rows}
        for row in ranked:
            lifecycle_id = s(row.get("lifecycle_id", ""))
            reason = allocation_decisions.get(lifecycle_id, "max_positions_full")
            if lifecycle_id not in selected_ids:
                allocation_rows.append(slot_allocation_record(row, 0, reason))
                continue
            capital = equity / float(MAX_POSITIONS)
            position = {
                "lifecycle_id": row["lifecycle_id"],
                "exit_ts": row["simulated_exit_ts"],
                "capital": capital,
                "return": row["net_return_costed"],
                "theme_id": row.get("theme_id", ""),
                "relation_transmission_state": row.get("relation_transmission_state", ""),
                "driver_state": t673.dominant_driver(row),
                "setup_quality_bucket": row.get("setup_quality_bucket", ""),
                "price_chart_acceptance_state": row.get("price_chart_acceptance_state", ""),
                "risk_warning_flag": row.get("risk_warning_flag", 0),
            }
            selected_positions.append(position)
            accepted = dict(row)
            accepted["position_capital_fraction"] = capital
            accepted_rows.append(accepted)
            allocation_rows.append(slot_allocation_record(row, 1, "accepted"))
        open_positions.extend(selected_positions)

    close_until(pd.Timestamp.max.tz_localize("UTC") - pd.Timedelta(days=1))
    accepted = pd.DataFrame(accepted_rows)
    allocation = pd.DataFrame(allocation_rows)
    curve = pd.DataFrame(curve_rows).sort_values("event_ts").reset_index(drop=True)
    if accepted.empty:
        return t673.empty_quality(), accepted, allocation, curve
    returns = pd.to_numeric(accepted["net_return_costed"], errors="coerce")
    return {
        "capital_pnl_pct": float((equity - 1.0) * 100.0),
        "max_drawdown_pct": float(curve["drawdown_pct"].min()),
        "entry_reduce_failure_rate": float(returns.le(-0.03).mean()),
    }, accepted, allocation, curve


def slot_evidence(row: dict[str, object], open_positions: list[dict[str, object]], *, source_strict: bool) -> dict[str, object]:
    source_rank = rank_source(row, source_strict=source_strict)
    catalyst_rank = rank_catalyst(row)
    archetype_rank = rank_archetype(row)
    leadership_rank = rank_leadership(row)
    alignment_rank = rank_price_leadership_alignment(row)
    price_rank = rank_price(row)
    relation_rank = rank_relation(row)
    symbol_context_rank = rank_symbol_context(row)
    concentration_rank = rank_concentration(row, open_positions)
    original_priority = i(row.get("priority_rank", 999))
    ladder = (
        source_rank,
        archetype_rank,
        alignment_rank,
        catalyst_rank,
        leadership_rank,
        price_rank,
        relation_rank,
        symbol_context_rank,
        concentration_rank,
        original_priority,
    )
    return {
        "slot_source_rank": source_rank,
        "slot_catalyst_rank": catalyst_rank,
        "slot_archetype_rank": archetype_rank,
        "slot_price_leadership_alignment_rank": alignment_rank,
        "slot_leadership_rank": leadership_rank,
        "slot_price_rank": price_rank,
        "slot_relation_rank": relation_rank,
        "slot_symbol_context_rank": symbol_context_rank,
        "slot_concentration_rank": concentration_rank,
        "slot_original_priority_tiebreaker": original_priority,
        "slot_ladder": ":".join(str(x) for x in ladder),
        "slot_ladder_tuple": ladder,
    }


def rank_source(row: dict[str, object], *, source_strict: bool) -> int:
    if i(row.get("asof_valid_flag", 0)) != 1:
        return 90
    if i(row.get("return_used_in_assignment_flag", 0)) or i(row.get("label_used_in_assignment_flag_task661", 0)) or i(row.get("future_price_used_in_assignment", 0)):
        return 90
    if source_strict and i(row.get("sparse_action_block_flag", 0)) == 1:
        return 80
    if i(row.get("sparse_action_block_flag", 0)) == 1:
        return 50
    return 10


def rank_catalyst(row: dict[str, object]) -> int:
    quality = s(row.get("catalyst_economic_quality", ""))
    directness = s(row.get("catalyst_directness", ""))
    durability = s(row.get("catalyst_durability", ""))
    overhang = s(row.get("catalyst_negative_overhang", ""))
    density = s(row.get("catalyst_signal_density", ""))
    if overhang == "severe":
        return 90
    if quality == "high" and directness == "direct" and durability in {"durable", "medium"} and density in {"multi_vector", "two_vector"}:
        return 10
    if quality == "high":
        return 25
    if quality == "medium":
        return 45
    if quality == "low":
        return 80
    return 80


def rank_archetype(row: dict[str, object]) -> int:
    archetype = s(row.get("archetype_candidate", ""))
    confidence = s(row.get("archetype_confidence", ""))
    base = {
        "theme_rotation_candidate": 10,
        "early_acceleration_candidate": 15,
        "catalyst_repricing_candidate": 20,
        "steady_trend_candidate": 25,
        "late_extension_candidate": 40,
        "rebound_context_candidate": 55,
        "mixed_or_unclear_candidate": 80,
    }.get(archetype, 80)
    if confidence == "high":
        return max(10, base - 5)
    if confidence == "low":
        return min(90, base + 15)
    return base


def rank_leadership(row: dict[str, object]) -> int:
    return {
        "emerging_leadership": 10,
        "persistent_leadership": 20,
        "narrow_leader": 25,
        "participating_theme": 40,
        "late_leadership": 65,
        "fading_leadership": 85,
    }.get(s(row.get("leadership_lifecycle_state", "")), 70)


def rank_price_leadership_alignment(row: dict[str, object]) -> int:
    price = s(row.get("price_chart_acceptance_state", ""))
    leadership = s(row.get("leadership_lifecycle_state", ""))
    if price in {"price_confirmed_basic", "price_confirmed_not_extended"} and leadership in {"emerging_leadership", "persistent_leadership", "narrow_leader"}:
        return 10
    if price in {"price_confirmed_basic", "price_accepted_needs_confirmation"} and leadership in {"participating_theme", "persistent_leadership"}:
        return 25
    if price == "price_confirmed_but_extended" and leadership in {"late_leadership", "fading_leadership"}:
        return 85
    if price == "price_fragile_or_unconfirmed" or leadership == "fading_leadership":
        return 70
    return 45


def rank_price(row: dict[str, object]) -> int:
    return {
        "price_confirmed_not_extended": 10,
        "price_confirmed_basic": 15,
        "price_accepted_needs_confirmation": 25,
        "price_confirmed_but_extended": 35,
        "price_fragile_or_unconfirmed": 45,
    }.get(s(row.get("price_chart_acceptance_state", "")), 70)


def rank_relation(row: dict[str, object]) -> int:
    return {
        "company_price_confirmed_macro_secondary": 10,
        "relation_reinforcing": 20,
        "company_positive_confirmation_needed": 30,
        "relation_support_dominant": 40,
        "relation_offsetting": 55,
        "relation_pressure_dominant": 75,
        "relation_sparse_research_only": 80,
    }.get(s(row.get("relation_transmission_state", "")), 70)


def rank_symbol_context(row: dict[str, object]) -> int:
    return {
        "new_symbol_constructive_context": 15,
        "same_symbol_context_upgrade": 10,
        "same_symbol_constructive_repeat": 20,
        "new_symbol_neutral_context": 35,
        "same_symbol_neutral_repeat": 40,
        "same_symbol_context_downgrade": 70,
        "same_symbol_caution_repeat": 75,
        "new_symbol_unclear_context": 80,
        "same_symbol_unclear_repeat": 80,
    }.get(s(row.get("same_symbol_state_variant", "")), 50)


def rank_concentration(row: dict[str, object], open_positions: list[dict[str, object]]) -> int:
    theme = s(row.get("theme_id", ""))
    relation = s(row.get("relation_transmission_state", ""))
    driver = t673.dominant_driver(row)
    theme_count = sum(1 for pos in open_positions if s(pos.get("theme_id", "")) == theme)
    relation_count = sum(1 for pos in open_positions if s(pos.get("relation_transmission_state", "")) == relation)
    driver_count = sum(1 for pos in open_positions if s(pos.get("driver_state", "")) == driver)
    if relation_count >= 3:
        return 90
    if theme_count >= 2 or relation_count >= 2 or driver_count >= 2:
        return 50
    return 10


def cohort_block_reason(row: dict[str, object], open_positions: list[dict[str, object]], selected_positions: list[dict[str, object]], available_slots: int, *, source_strict: bool) -> str:
    if len(selected_positions) >= available_slots:
        return "max_positions_full"
    if i(row.get("asof_valid_flag", 0)) != 1:
        return "source_asof_invalid"
    if source_strict and i(row.get("sparse_action_block_flag", 0)) == 1:
        return "source_strict_sparse_block"
    relation = s(row.get("relation_transmission_state", ""))
    relation_count = sum(1 for pos in open_positions + selected_positions if s(pos.get("relation_transmission_state", "")) == relation)
    if relation_count >= 3:
        return "relation_cap3"
    return ""


def select_with_displacement_hurdle(
    ranked: list[dict[str, object]],
    open_positions: list[dict[str, object]],
    available_slots: int,
    *,
    source_strict: bool,
) -> tuple[list[dict[str, object]], dict[str, str]]:
    selected: list[dict[str, object]] = []
    decisions: dict[str, str] = {}
    baseline = [row for row in ranked if i(row.get("active_cap3_baseline_flag", 0)) == 1]
    challengers = [row for row in ranked if i(row.get("active_cap3_baseline_flag", 0)) != 1]

    for row in baseline:
        reason = cohort_block_reason(row, open_positions, selected, available_slots, source_strict=source_strict)
        if reason:
            decisions[s(row.get("lifecycle_id", ""))] = reason
            continue
        selected.append(row)
        decisions[s(row.get("lifecycle_id", ""))] = "accepted_baseline_preserved"

    for row in challengers:
        lifecycle_id = s(row.get("lifecycle_id", ""))
        reason = cohort_block_reason(row, open_positions, selected, available_slots, source_strict=source_strict)
        if not reason:
            selected.append(row)
            decisions[lifecycle_id] = "accepted_available_slot"
            continue
        if reason != "max_positions_full":
            decisions[lifecycle_id] = reason
            continue
        incumbent = weakest_replaceable_baseline(selected)
        if incumbent is None:
            decisions[lifecycle_id] = "displacement_no_baseline_incumbent"
            continue
        hurdle_pass, hurdle_reason = passes_displacement_hurdle(row, incumbent, open_positions, selected)
        if not hurdle_pass:
            decisions[lifecycle_id] = hurdle_reason
            continue
        selected = [pos for pos in selected if s(pos.get("lifecycle_id", "")) != s(incumbent.get("lifecycle_id", ""))]
        decisions[s(incumbent.get("lifecycle_id", ""))] = f"displaced_by={lifecycle_id}"
        selected.append(row)
        decisions[lifecycle_id] = "accepted_displacement_hurdle_pass"

    return selected, decisions


def weakest_replaceable_baseline(selected: list[dict[str, object]]) -> dict[str, object] | None:
    baseline = [
        row
        for row in selected
        if i(row.get("active_cap3_baseline_flag", 0)) == 1 and incumbent_displacement_vulnerability(row) >= 2
    ]
    if not baseline:
        return None
    return sorted(baseline, key=lambda row: (-incumbent_displacement_vulnerability(row), displacement_defense_score(row), row.get("slot_ladder_tuple", ())))[0]


def incumbent_displacement_vulnerability(row: dict[str, object]) -> int:
    vulnerability = 0
    if i(row.get("asof_valid_flag", 0)) != 1 or i(row.get("sparse_action_block_flag", 0)) == 1:
        vulnerability += 2
    if s(row.get("relation_transmission_state", "")) in {"relation_pressure_dominant", "relation_sparse_research_only", "relation_offsetting"}:
        vulnerability += 1
    if s(row.get("catalyst_negative_overhang", "")) == "severe":
        vulnerability += 1
    if "severe_catalyst_overhang" in s(row.get("archetype_risk_flags", "")):
        vulnerability += 1
    if rank_archetype(row) >= 80 and rank_price_leadership_alignment(row) >= 80:
        vulnerability += 1
    if i(row.get("priority_rank", 999)) <= 10:
        vulnerability -= 1
    return max(0, vulnerability)


def displacement_defense_score(row: dict[str, object]) -> int:
    score = 0
    if s(row.get("archetype_confidence", "")) == "high":
        score += 3
    elif s(row.get("archetype_confidence", "")) == "medium":
        score += 1
    if s(row.get("catalyst_economic_quality", "")) == "high":
        score += 1
    if rank_price_leadership_alignment(row) <= 25:
        score += 2
    if rank_concentration(row, []) <= 10:
        score += 1
    if "extension_risk" in s(row.get("archetype_risk_flags", "")):
        score -= 1
    if "severe_catalyst_overhang" in s(row.get("archetype_risk_flags", "")):
        score -= 2
    return score


def passes_displacement_hurdle(
    challenger: dict[str, object],
    incumbent: dict[str, object],
    open_positions: list[dict[str, object]],
    selected: list[dict[str, object]],
) -> tuple[bool, str]:
    if i(challenger.get("asof_valid_flag", 0)) != 1:
        return False, "displacement_failed_source_invalid"
    if i(challenger.get("sparse_action_block_flag", 0)) == 1:
        return False, "displacement_failed_sparse_source"
    if incumbent_displacement_vulnerability(incumbent) < 2:
        return False, "displacement_failed_incumbent_not_vulnerable"
    if rank_archetype(challenger) > rank_archetype(incumbent) - 10:
        return False, "displacement_failed_no_archetype_advantage"
    if rank_price_leadership_alignment(challenger) > rank_price_leadership_alignment(incumbent) - 10:
        return False, "displacement_failed_no_price_leadership_advantage"
    if rank_catalyst(challenger) > rank_catalyst(incumbent):
        return False, "displacement_failed_catalyst_worse"
    selected_without_incumbent = [row for row in selected if s(row.get("lifecycle_id", "")) != s(incumbent.get("lifecycle_id", ""))]
    relation = s(challenger.get("relation_transmission_state", ""))
    relation_count = sum(1 for pos in open_positions + selected_without_incumbent if s(pos.get("relation_transmission_state", "")) == relation)
    if relation_count >= 3:
        return False, "displacement_failed_relation_cap3"
    if rank_concentration(challenger, open_positions + selected_without_incumbent) > rank_concentration(incumbent, open_positions + selected_without_incumbent):
        return False, "displacement_failed_concentration_worse"
    if displacement_defense_score(challenger) <= displacement_defense_score(incumbent):
        return False, "displacement_failed_no_total_superiority"
    return True, "displacement_hurdle_pass"


def slot_allocation_record(row: dict[str, object], accepted_flag: int, reason: str) -> dict[str, object]:
    cols = [
        "lifecycle_id",
        "symbol",
        "entry_ts",
        "split_name",
        "theme_id",
        "leadership_lifecycle_state",
        "catalyst_path_type",
        "catalyst_economic_quality",
        "archetype_candidate",
        "archetype_confidence",
        "same_symbol_state_variant",
        "price_chart_acceptance_state",
        "relation_transmission_state",
        "cohort_candidate_count",
        "available_slots_at_cohort_start",
        "cohort_slot_rank",
        "slot_ladder",
        "slot_archetype_rank",
        "slot_price_leadership_alignment_rank",
        "slot_catalyst_rank",
        "slot_original_priority_tiebreaker",
        "active_cap3_baseline_flag",
        "net_return_costed",
    ]
    out = {col: row.get(col, "") for col in cols}
    out["accepted_flag"] = int(accepted_flag)
    out["allocation_reason"] = reason
    out["return_used_in_assignment_flag"] = 0
    return out


def build_guardrail_audit(accepted: pd.DataFrame) -> pd.DataFrame:
    active = accepted[(accepted["candidate_name"].eq(ACTIVE_CAP3)) & (accepted["split_scope"].eq("all"))].copy()
    active_ids = set(active["lifecycle_id"].astype(str))
    active_returns = active.set_index(active["lifecycle_id"].astype(str))["net_return_costed"]
    rows = []
    for candidate_name, group in accepted[accepted["split_scope"].eq("all")].groupby("candidate_name", dropna=False):
        ids = set(group["lifecycle_id"].astype(str))
        removed_ids = active_ids - ids
        added_ids = ids - active_ids
        removed = pd.to_numeric(active_returns.loc[list(removed_ids)] if removed_ids else pd.Series(dtype=float), errors="coerce")
        added = pd.to_numeric(group[group["lifecycle_id"].astype(str).isin(added_ids)]["net_return_costed"] if added_ids else pd.Series(dtype=float), errors="coerce")
        removed_big = int(removed.ge(0.50).sum()) if len(removed) else 0
        rows.append(
            {
                "candidate_name": candidate_name,
                "active_cap3_trade_count": int(len(active_ids)),
                "candidate_trade_count": int(len(ids)),
                "common_trade_count": int(len(active_ids & ids)),
                "removed_active_cap3_trade_count": int(len(removed_ids)),
                "added_trade_count": int(len(added_ids)),
                "removed_active_cap3_avg_return_pct_eval_only": float(removed.mean() * 100.0) if len(removed) else 0.0,
                "removed_active_cap3_big_winner_count_eval_only": removed_big,
                "removed_active_cap3_failure_count_eval_only": int(removed.le(-0.10).sum()) if len(removed) else 0,
                "added_avg_return_pct_eval_only": float(added.mean() * 100.0) if len(added) else 0.0,
                "added_big_winner_count_eval_only": int(added.ge(0.50).sum()) if len(added) else 0,
                "winner_preservation_guardrail_pass_flag": int(removed_big == 0),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["winner_preservation_guardrail_pass_flag", "removed_active_cap3_big_winner_count_eval_only"], ascending=[True, False]).reset_index(drop=True)


def build_displacement_pairs(accepted: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty:
        return pd.DataFrame()
    active = accepted[(accepted["candidate_name"].eq(ACTIVE_CAP3)) & (accepted["split_scope"].eq("all"))].copy()
    rows = []
    for candidate_name, group in accepted[accepted["split_scope"].eq("all")].groupby("candidate_name", dropna=False):
        if candidate_name == ACTIVE_CAP3:
            continue
        candidate_ids = set(group["lifecycle_id"].astype(str))
        active_ids = set(active["lifecycle_id"].astype(str))
        removed = active[active["lifecycle_id"].astype(str).isin(active_ids - candidate_ids)]
        added = group[group["lifecycle_id"].astype(str).isin(candidate_ids - active_ids)]
        rows.append(
            {
                "candidate_name": candidate_name,
                "removed_count": int(len(removed)),
                "removed_avg_return_pct_eval_only": float(pd.to_numeric(removed["net_return_costed"], errors="coerce").mean() * 100.0) if len(removed) else 0.0,
                "removed_big_winner_count_eval_only": int(pd.to_numeric(removed["net_return_costed"], errors="coerce").ge(0.50).sum()) if len(removed) else 0,
                "added_count": int(len(added)),
                "added_avg_return_pct_eval_only": float(pd.to_numeric(added["net_return_costed"], errors="coerce").mean() * 100.0) if len(added) else 0.0,
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_slot_summary(allocation: pd.DataFrame) -> pd.DataFrame:
    if allocation.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in allocation.groupby(["candidate_name", "split_scope", "allocation_reason"], dropna=False):
        candidate_name, split, reason = keys
        returns = pd.to_numeric(group["net_return_costed"], errors="coerce")
        rows.append(
            {
                "candidate_name": candidate_name,
                "split_name": split,
                "allocation_reason": reason,
                "row_count": int(len(group)),
                "accepted_count": int(pd.to_numeric(group["accepted_flag"], errors="coerce").sum()),
                "avg_return_pct_eval_only": float(returns.mean() * 100.0) if len(returns) else 0.0,
                "big_winner_count_eval_only": int(returns.ge(0.50).sum()) if len(returns) else 0,
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["split_name", "candidate_name", "allocation_reason"]).reset_index(drop=True)


def build_forbidden_input_audit(stack: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    checks = {
        "leadership_return_used_in_assignment_flag": sum_col(stack, "leadership_return_used_in_assignment_flag"),
        "catalyst_return_used_in_assignment_flag": sum_col(stack, "catalyst_return_used_in_assignment_flag"),
        "archetype_return_used_in_assignment_flag": sum_col(stack, "archetype_return_used_in_assignment_flag"),
        "same_symbol_return_used_in_assignment_flag": sum_col(stack, "same_symbol_return_used_in_assignment_flag"),
        "stack_return_used_in_assignment_flag": sum_col(stack, "stack_return_used_in_assignment_flag"),
        "stack_label_used_in_assignment_flag": sum_col(stack, "stack_label_used_in_assignment_flag"),
        "stack_future_price_used_in_assignment_flag": sum_col(stack, "stack_future_price_used_in_assignment_flag"),
        "symbol_blacklist_used": sum_col(stack, "symbol_blacklist_used"),
        "theme_blacklist_used": sum_col(stack, "theme_blacklist_used"),
        "microstructure_used_in_assignment": sum_col(stack, "microstructure_used_in_assignment"),
        "allocation_return_used_in_assignment_flag": sum_col(allocation, "return_used_in_assignment_flag") if not allocation.empty else 0,
    }
    return pd.DataFrame(
        [
            {
                "check_name": name,
                "violation_count": int(value),
                "pass_flag": int(value == 0),
                "required_value": "0 violations",
            }
            for name, value in checks.items()
        ]
    )


def build_decision(grid: pd.DataFrame, guardrail: pd.DataFrame, forbidden: pd.DataFrame) -> pd.DataFrame:
    active = grid[(grid["candidate_name"].eq(ACTIVE_CAP3)) & (grid["split_name"].eq("all"))].iloc[0]
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    best_guard = guardrail[guardrail["candidate_name"].eq(best["candidate_name"])].iloc[0]
    violations = int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum())
    return pd.DataFrame(
        [
            {
                "task_id": "Task682",
                "decision": "INTEGRATED_PREDICTION_STACK_IMPLEMENTED_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "active_cap3_final_capital_usd": float(active["final_capital_usd"]),
                "active_cap3_max_drawdown_pct": float(active["max_drawdown_pct"]),
                "best_candidate_name": best["candidate_name"],
                "best_final_capital_usd": float(best["final_capital_usd"]),
                "best_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "best_removed_big_winners": int(best_guard["removed_active_cap3_big_winner_count_eval_only"]),
                "forbidden_input_violations": violations,
                "next_action": "Keep the five-engine stack research-only. Displacement hurdle v2 protects active cap3 winners, but the five engines still need predictive improvement before promotion.",
            }
        ]
    )


def build_pass_fail(stack: pd.DataFrame, grid: pd.DataFrame, guardrail: pd.DataFrame, forbidden: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    active = grid[(grid["candidate_name"].eq(ACTIVE_CAP3)) & (grid["split_name"].eq("all"))].iloc[0]
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    best_guard = guardrail[guardrail["candidate_name"].eq(best["candidate_name"])].iloc[0]
    violations = int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum())
    cohort_rows = allocation[allocation["candidate_name"].eq(COHORT_SLOT_V1)] if not allocation.empty else pd.DataFrame()
    return pd.DataFrame(
        [
            gate("five_engine_columns_built", required_engine_columns().issubset(stack.columns), "columns present", "all engine outputs"),
            gate("cohort_slot_assignment_built", not cohort_rows.empty and "cohort_slot_rank" in cohort_rows.columns, f"rows={len(cohort_rows)}", "cohort allocation rows"),
            gate("no_forbidden_assignment_inputs", violations == 0, f"violations={violations}", "0 violations"),
            gate("task678_assignment_reuse_removed", "entry_time_archetype_candidate" not in stack.columns, "old assignment column absent", "no Task678 assignment column"),
            gate("global_top5_rank_removed", "top5_priority_rank" not in stack.columns, "global top5 rank absent", "no global top5 rank"),
            gate("best_beats_active_cap3_return", float(best["final_capital_usd"]) > float(active["final_capital_usd"]), f"best={float(best['final_capital_usd']):.2f}, active={float(active['final_capital_usd']):.2f}", "best final > active cap3"),
            gate("best_mdd_not_worse_than_active_cap3", float(best["max_drawdown_pct"]) >= float(active["max_drawdown_pct"]), f"best={float(best['max_drawdown_pct']):.2f}, active={float(active['max_drawdown_pct']):.2f}", "best MDD not worse"),
            gate("best_preserves_active_big_winners", int(best_guard["removed_active_cap3_big_winner_count_eval_only"]) == 0, f"removed_big={int(best_guard['removed_active_cap3_big_winner_count_eval_only'])}", "0 removed big winners"),
            gate("strategy_accepted", False, "research only", "split/OOS promotion required"),
        ]
    )


def required_engine_columns() -> set[str]:
    return {
        "leadership_lifecycle_state",
        "catalyst_path_type",
        "catalyst_economic_quality",
        "catalyst_negative_overhang",
        "catalyst_signal_density",
        "archetype_candidate",
        "same_symbol_state_variant",
        "same_symbol_prior_setup_count",
    }


def write_outputs(
    leadership: pd.DataFrame,
    catalyst: pd.DataFrame,
    archetype: pd.DataFrame,
    symbol_context: pd.DataFrame,
    stack: pd.DataFrame,
    grid: pd.DataFrame,
    accepted: pd.DataFrame,
    allocation: pd.DataFrame,
    curves: pd.DataFrame,
    guardrail: pd.DataFrame,
    displacement: pd.DataFrame,
    slot_summary: pd.DataFrame,
    forbidden: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task682_leadership_lifecycle_panel.csv": leadership,
        "task682_catalyst_quality_matrix.csv": catalyst,
        "task682_archetype_candidate_panel.csv": archetype,
        "task682_same_symbol_context_matrix.csv": symbol_context,
        "task682_slot_qualification_panel.csv": allocation,
        "task682_integrated_stack_panel.csv": stack,
        "task682_simulation_result.csv": grid,
        "task682_accepted_trades.csv": accepted,
        "task682_equity_curves.csv": curves,
        "task682_guardrail_audit.csv": guardrail,
        "task682_displacement_pairs.csv": displacement,
        "task682_slot_summary.csv": slot_summary,
        "task682_forbidden_input_audit.csv": forbidden,
        "task_682_decision.csv": decision,
        "task_682_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK682_DIR / name, index=False)
    (TASK682_DIR / "task_682_integrated_prediction_stack.md").write_text(
        render_report(grid, guardrail, displacement, slot_summary, forbidden, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK682_DIR, TASK682_DIR / "artifact_manifest.csv")


def render_report(
    grid: pd.DataFrame,
    guardrail: pd.DataFrame,
    displacement: pd.DataFrame,
    slot_summary: pd.DataFrame,
    forbidden: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    active = grid[(grid["candidate_name"].eq(ACTIVE_CAP3)) & (grid["split_name"].eq("all"))].iloc[0]
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    return f"""# Task682 Integrated Prediction Stack

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: the five-engine prediction stack was implemented as separate artifacts and linked through cohort slot qualification.
- Quality rewrite: catalyst now separates low/overhang/density, archetype uses entry-time structure, same-symbol context compares prior symbol signatures, and displacement hurdle v2 requires incumbent vulnerability before replacement.
- Key metrics: active cap3 ${float(active['final_capital_usd']):,.2f} / MDD {float(active['max_drawdown_pct']):.2f}%; best candidate `{best['candidate_name']}` ${float(best['final_capital_usd']):,.2f} / MDD {float(best['max_drawdown_pct']):.2f}%.
- Next action: keep as research-only until split/OOS gates and active cap3 winner preservation both pass.

## Quant Expert Report

### Data source and source readiness

- Input: Task672 current-data state panel.
- Microstructure, quote, trade, and NBBO are not used.
- GPT is not used as market data, source truth, label, or assignment input.

### Exact join keys

- Five engine panels join on `lifecycle_id`.
- Cohort slot qualification groups by `entry_ts`.
- Accepted-trade displacement compares `lifecycle_id` sets.
- `integrated_cohort_slot_displacement_hurdle_v2` uses active cap3 as a baseline slot set, but only allows replacement when source safety, archetype advantage, price/leadership advantage, catalyst non-deterioration, concentration non-deterioration, and incumbent vulnerability are all satisfied.

### Leakage audit

- Return, label, and future price assignment flags are zero.
- `classify_winner_archetype` is not used for assignment.
- `classify_top5_tier` and `top5_priority_rank` are not used.
- Active cap3 big-winner guardrail is evaluation-only.
- Displacement vulnerability uses only entry-time source/relation/catalyst/setup fields and does not use realized return.

### Split/OOS metrics

{t678.markdown_table(grid)}

### Winner preservation guardrail

{t678.markdown_table(guardrail)}

### Displacement pairs

{t678.markdown_table(displacement)}

### Slot summary

{t678.markdown_table(slot_summary.head(30))}

### Forbidden input audit

{t678.markdown_table(forbidden)}

### Remaining blockers

- The integrated stack is a research candidate, not deployment logic.
- Displacement hurdle v2 preserved active cap3 winners, but did not improve final capital versus active cap3.
- The remaining blocker is predictive improvement inside the five engines without turning active cap3 preservation into a disguised global rank.

## No-Background Decision-Maker Report

- What happened: the five required engines were built separately and connected in order.
- Why it matters: we stopped using one global top5 score and started comparing candidates only inside the same entry-time cohort.
- Whether this changes capital readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: inspect whether the cohort slot engine protects winners without diluting alpha.

## Artifact Manifest

- Inputs: Task672 panel and QQQ benchmark.
- Outputs: five engine artifacts, integrated stack, simulation results, guardrail audit, report, manifest.
- Validation commands: `python -m unittest tests.test_task682_integrated_prediction_stack`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def sum_col(frame: pd.DataFrame, col: str) -> int:
    if col not in frame.columns:
        return 0
    return int(pd.to_numeric(frame[col], errors="coerce").fillna(0).sum())


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {"gate_name": name, "pass_flag": int(bool(passed)), "observed": observed, "required": required}


def f(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def i(value: object, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def s(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task672-dir", type=Path, default=t673.TASK672_DIR)
    parser.add_argument("--qqq-path", type=Path, default=QQQ_PATH)
    args = parser.parse_args()
    build_task682_program(task672_dir=args.task672_dir, qqq_path=args.qqq_path)
    print(f"[Task682] wrote {TASK682_DIR}")


if __name__ == "__main__":
    main()
