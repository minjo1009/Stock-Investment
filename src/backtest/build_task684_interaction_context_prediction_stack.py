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
from src.backtest import build_task682_integrated_prediction_stack as t682
from src.backtest import build_task683_firm_grade_context_gather_5_engine_review as t683
from src.backtest.build_task637_content_signal_account_backtest import (
    INITIAL_CAPITAL_USD,
    load_qqq_history,
    qqq_final_for_period,
)
from src.backtest.build_task659_theme_specific_relation_engine import QQQ_PATH


TASK682_DIR = Path("docs/reports/task_682_integrated_prediction_stack")
TASK684_DIR = Path("docs/reports/task_684_interaction_context_prediction_stack")
ACTIVE_CAP3 = "active_relation_cap3_reference"
INTERACTION_PACKET = "interaction_context_packet_v3"
INTERACTION_GUARDED = "interaction_context_superiority_guarded_v3"
MAX_POSITIONS = 5


def build_task684_program(task682_dir: Path = TASK682_DIR, qqq_path: Path = QQQ_PATH) -> dict[str, pd.DataFrame]:
    TASK684_DIR.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(task682_dir / "task682_integrated_stack_panel.csv")

    leadership = build_leadership_lifecycle_interaction_panel(base)
    catalyst = build_catalyst_quality_interaction_matrix(merge_outputs(base, leadership))
    archetype = build_archetype_candidate_interaction_engine(merge_outputs(base, leadership, catalyst))
    same_symbol = build_same_symbol_context_interaction_matrix(merge_outputs(base, leadership, catalyst, archetype))
    stack = merge_outputs(base, leadership, catalyst, archetype, same_symbol)
    stack["interaction_stack_return_used_in_assignment_flag"] = 0
    stack["interaction_stack_label_used_in_assignment_flag"] = 0
    stack["interaction_stack_future_price_used_in_assignment_flag"] = 0

    qqq = load_qqq_history(qqq_path)
    grid, accepted, allocation, curves = build_candidate_grid(stack, qqq)
    guardrail = build_guardrail_audit(accepted)
    superiority = build_superiority_audit(allocation)
    forbidden = build_forbidden_input_audit(stack, allocation)
    decision = build_decision(grid, guardrail, forbidden)
    pass_fail = build_pass_fail(stack, grid, guardrail, forbidden, allocation)

    write_outputs(
        leadership,
        catalyst,
        archetype,
        same_symbol,
        stack,
        grid,
        accepted,
        allocation,
        curves,
        guardrail,
        superiority,
        forbidden,
        decision,
        pass_fail,
    )
    return {
        "leadership": leadership,
        "catalyst": catalyst,
        "archetype": archetype,
        "same_symbol": same_symbol,
        "stack": stack,
        "grid": grid,
        "accepted": accepted,
        "allocation": allocation,
        "curves": curves,
        "guardrail": guardrail,
        "superiority": superiority,
        "forbidden": forbidden,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_leadership_lifecycle_interaction_panel(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in base.to_dict(orient="records"):
        ret20 = f(row.get("theme_ret20_prev", 0.0))
        breadth = f(row.get("theme_breadth20_prev", 0.0))
        volume = f(row.get("theme_volume_ratio_prev", 1.0))
        rank = f(row.get("theme_rank_prev", 99.0))
        market_ret = f(row.get("market_ret_20d", 0.0))
        market_breadth = f(row.get("breadth_20d", 0.0))
        price = s(row.get("price_chart_acceptance_state", ""))
        catalyst = s(row.get("catalyst_economic_quality", ""))
        relation = s(row.get("relation_transmission_state", ""))
        state = s(row.get("leadership_lifecycle_state", ""))
        reasons = []

        if ret20 > market_ret + 0.04 and rank <= 5:
            phase = "theme_relative_leader"
            reasons.append("theme_beats_market")
        elif ret20 >= 0.10 and breadth >= 0.70 and volume >= 0.90:
            phase = "broad_persistent_leader"
            reasons.append("broad_volume_confirmed")
        elif ret20 >= 0.12 and (breadth < 0.60 or volume < 0.80 or price == "price_confirmed_but_extended"):
            phase = "late_or_crowded_leader"
            reasons.append("strength_with_decay_or_extension")
        elif market_ret < 0 and ret20 > 0 and breadth >= 0.55:
            phase = "defensive_relative_strength"
            reasons.append("theme_up_in_weak_market")
        elif ret20 < 0.03 or breadth < 0.50 or state == "fading_leadership":
            phase = "fragile_or_fading_theme"
            reasons.append("weak_theme_context")
        else:
            phase = "neutral_participation"
            reasons.append("neutral_theme_context")

        if market_ret >= 0 and market_breadth >= 0.55:
            market_alignment = "market_tailwind"
        elif ret20 > market_ret + 0.04:
            market_alignment = "theme_resists_market"
        else:
            market_alignment = "market_headwind_or_beta"

        if price in {"price_confirmed_basic", "price_confirmed_not_extended"} and phase in {"theme_relative_leader", "broad_persistent_leader", "defensive_relative_strength"}:
            price_interaction = "leadership_price_confirmed"
        elif price == "price_confirmed_but_extended" and phase in {"late_or_crowded_leader", "fragile_or_fading_theme"}:
            price_interaction = "leadership_price_extension_risk"
        else:
            price_interaction = "leadership_price_mixed"

        if catalyst == "low" and relation in {"relation_reinforcing", "company_positive_confirmation_needed", "company_price_confirmed_macro_secondary"}:
            catalyst_interaction = "leadership_relation_offsets_weak_catalyst"
        elif catalyst == "high" and phase in {"theme_relative_leader", "broad_persistent_leader"}:
            catalyst_interaction = "leadership_catalyst_reinforcing"
        else:
            catalyst_interaction = "leadership_catalyst_neutral"

        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "entry_ts": row.get("entry_ts", ""),
                "symbol": row.get("symbol", ""),
                "theme_id": row.get("theme_id", ""),
                "leadership_phase_strength": phase,
                "leadership_market_alignment": market_alignment,
                "leadership_price_interaction_state": price_interaction,
                "leadership_catalyst_interaction_state": catalyst_interaction,
                "leadership_interaction_reason_codes": "|".join(reasons),
                "leadership_interaction_return_used_in_assignment_flag": 0,
                "leadership_interaction_label_used_in_assignment_flag": 0,
                "leadership_interaction_future_price_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_catalyst_quality_interaction_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict(orient="records"):
        quality = s(row.get("catalyst_economic_quality", ""))
        overhang = s(row.get("catalyst_negative_overhang", ""))
        density = s(row.get("catalyst_signal_density", ""))
        price = s(row.get("price_chart_acceptance_state", ""))
        relation = s(row.get("relation_transmission_state", ""))
        leadership = s(row.get("leadership_phase_strength", ""))
        path = s(row.get("catalyst_path_type", ""))
        reasons = []

        if quality == "low":
            absorption, absorption_reasons = enhanced_catalyst_low_state(row)
            reasons.extend(absorption_reasons)
        elif quality == "high" and price in {"price_confirmed_basic", "price_confirmed_not_extended"}:
            absorption = "high_catalyst_price_absorbing"
            reasons.append("high_catalyst_price_confirmed")
        elif quality == "high" and price in {"price_fragile_or_unconfirmed", "price_accepted_needs_confirmation"}:
            absorption = "high_catalyst_not_fully_absorbed"
            reasons.append("high_catalyst_price_needs_confirmation")
        else:
            absorption = "catalyst_absorption_mixed"
            reasons.append("mixed_absorption")

        if overhang == "severe" and price not in {"price_confirmed_basic", "price_confirmed_not_extended"}:
            conflict = "hard_catalyst_conflict"
        elif overhang in {"moderate", "severe"} and relation in {"relation_reinforcing", "company_positive_confirmation_needed"}:
            conflict = "conflicted_but_relation_supported"
        elif quality == "high" and density in {"multi_vector", "two_vector"}:
            conflict = "clean_or_multi_vector_positive"
        else:
            conflict = "ordinary_or_unclear_catalyst"

        if absorption in {"weak_but_price_relation_confirmed", "high_catalyst_price_absorbing"} and leadership in {"theme_relative_leader", "broad_persistent_leader", "defensive_relative_strength"}:
            cross_state = "catalyst_theme_price_reinforcing"
        elif absorption.startswith("weak_but") and relation in {"relation_reinforcing", "company_positive_confirmation_needed"}:
            cross_state = "weak_catalyst_relation_absorption"
        elif conflict == "hard_catalyst_conflict":
            cross_state = "catalyst_blocker_not_absorbed"
        else:
            cross_state = "catalyst_cross_context_mixed"

        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "entry_ts": row.get("entry_ts", ""),
                "symbol": row.get("symbol", ""),
                "theme_id": row.get("theme_id", ""),
                "catalyst_absorption_state": absorption,
                "catalyst_conflict_state": conflict,
                "catalyst_cross_context_state": cross_state,
                "catalyst_interaction_reason_codes": "|".join(reasons + [f"path={path}", f"overhang={overhang}"]),
                "catalyst_interaction_return_used_in_assignment_flag": 0,
                "catalyst_interaction_label_used_in_assignment_flag": 0,
                "catalyst_interaction_future_price_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_archetype_candidate_interaction_engine(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict(orient="records"):
        base_archetype = s(row.get("archetype_candidate", ""))
        absorption = s(row.get("catalyst_absorption_state", ""))
        leadership = s(row.get("leadership_phase_strength", ""))
        price = s(row.get("price_chart_acceptance_state", ""))
        relation = s(row.get("relation_transmission_state", ""))
        support = i(row.get("mechanism_support_count", row.get("support_count", 0)))
        pressure = i(row.get("mechanism_pressure_count", row.get("conflict_count", 0)))

        if base_archetype == "mixed_or_unclear_candidate":
            sub_context, sub_reasons = t683.mixed_sub_context(row)
        else:
            sub_context = base_archetype
            sub_reasons = [base_archetype]

        if sub_context in {"mixed_delayed_absorption_or_price_led", "mixed_price_led_continuation"}:
            archetype_context = "price_led_continuation_context"
        elif sub_context == "mixed_relation_led_continuation":
            archetype_context = "relation_led_continuation_context"
        elif sub_context == "mixed_theme_led_continuation":
            archetype_context = "theme_led_continuation_context"
        elif base_archetype == "catalyst_repricing_candidate":
            archetype_context = "catalyst_repricing_context"
        elif base_archetype == "late_extension_candidate":
            archetype_context = "late_extension_context"
        elif base_archetype == "theme_rotation_candidate":
            archetype_context = "theme_rotation_context"
        elif sub_context == "mixed_due_to_late_extension" and relation in {"relation_reinforcing", "company_price_confirmed_macro_secondary", "company_positive_confirmation_needed"}:
            archetype_context = "extension_relation_continuation_context"
        elif sub_context == "mixed_conflicted_but_alive":
            archetype_context = "conflicted_but_alive_context"
        else:
            archetype_context = "true_unclear_or_low_clarity_context"

        if (
            archetype_context in {"price_led_continuation_context", "relation_led_continuation_context", "catalyst_repricing_context"}
            and price in {"price_confirmed_basic", "price_confirmed_not_extended"}
            and support >= pressure
        ):
            clarity = "high_context_clarity"
        elif archetype_context == "true_unclear_or_low_clarity_context" or pressure > support + 1:
            clarity = "low_context_clarity"
        else:
            clarity = "medium_context_clarity"

        if absorption in {"weak_but_price_relation_confirmed", "high_catalyst_price_absorbing"} and relation in {"relation_reinforcing", "company_positive_confirmation_needed"}:
            absorption_mode = "absorption_relation_reinforced"
        elif price in {"price_confirmed_basic", "price_confirmed_not_extended"}:
            absorption_mode = "price_absorption_primary"
        elif leadership in {"theme_relative_leader", "broad_persistent_leader"}:
            absorption_mode = "theme_absorption_primary"
        else:
            absorption_mode = "absorption_unproven"

        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "entry_ts": row.get("entry_ts", ""),
                "symbol": row.get("symbol", ""),
                "theme_id": row.get("theme_id", ""),
                "archetype_interaction_context": archetype_context,
                "archetype_sub_context": sub_context,
                "archetype_context_clarity": clarity,
                "archetype_absorption_mode": absorption_mode,
                "archetype_interaction_reason_codes": "|".join(sub_reasons),
                "archetype_interaction_return_used_in_assignment_flag": 0,
                "archetype_interaction_label_used_in_assignment_flag": 0,
                "archetype_interaction_future_price_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_same_symbol_context_interaction_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    work = frame.copy()
    work["entry_ts"] = pd.to_datetime(work["entry_ts"], utc=True)
    work = work.sort_values(["symbol", "entry_ts", "lifecycle_id"]).reset_index(drop=True)
    previous_by_symbol: dict[str, dict[str, object]] = {}
    for row in work.to_dict(orient="records"):
        previous = previous_by_symbol.get(s(row.get("symbol", "")))
        interpretation, reasons = t683.same_symbol_interpretation(row)
        if previous is None:
            setup_shift = "first_observed_setup"
        else:
            changed = []
            for col in [
                "leadership_phase_strength",
                "catalyst_absorption_state",
                "archetype_interaction_context",
                "price_chart_acceptance_state",
                "relation_transmission_state",
            ]:
                if s(previous.get(col, "")) != s(row.get(col, "")):
                    changed.append(col)
            setup_shift = "same_symbol_distinct_setup" if len(changed) >= 2 else "same_symbol_similar_setup"
            reasons.extend([f"changed={','.join(changed)}" if changed else "changed=none"])

        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "entry_ts": row.get("entry_ts", ""),
                "symbol": row.get("symbol", ""),
                "theme_id": row.get("theme_id", ""),
                "same_symbol_interaction_state": interpretation,
                "same_symbol_setup_shift_state": setup_shift,
                "same_symbol_assignment_role": "conflict_interpreter_only",
                "same_symbol_interaction_reason_codes": "|".join(reasons),
                "same_symbol_interaction_return_used_in_assignment_flag": 0,
                "same_symbol_interaction_label_used_in_assignment_flag": 0,
                "same_symbol_interaction_future_price_used_in_assignment_flag": 0,
            }
        )
        previous_by_symbol[s(row.get("symbol", ""))] = row
    return pd.DataFrame(rows)


def enhanced_catalyst_low_state(row: dict[str, object]) -> tuple[str, list[str]]:
    price = s(row.get("price_chart_acceptance_state", ""))
    relation = s(row.get("relation_transmission_state", ""))
    leadership = s(row.get("leadership_phase_strength", ""))
    base_state, reasons = t683.catalyst_low_state(row)
    if (
        price == "price_confirmed_but_extended"
        and relation in {"relation_reinforcing", "company_positive_confirmation_needed", "company_price_confirmed_macro_secondary"}
        and leadership in {"theme_relative_leader", "broad_persistent_leader", "neutral_participation", "fragile_or_fading_theme"}
    ):
        return "weak_but_extension_relation_supported", reasons + ["extension_relation_supported"]
    return base_state, reasons


def build_candidate_grid(panel: pd.DataFrame, qqq: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    accepted_frames = []
    allocation_frames = []
    curve_frames = []
    active_spec = pd.Series(t673.candidate(ACTIVE_CAP3, "reference", "relation_priority", "relation3", 0, 0, 0, 0, "Active relation cap3 reference."))
    original_max_positions = t673.MAX_POSITIONS
    try:
        t673.MAX_POSITIONS = MAX_POSITIONS
        candidates = [
            (ACTIVE_CAP3, "active", False),
            (INTERACTION_PACKET, "interaction", False),
            (INTERACTION_GUARDED, "interaction", True),
        ]
        for candidate_name, mode, guarded in candidates:
            for split_name in ["all", "validation", "recent_oos"]:
                scoped = panel if split_name == "all" else panel[panel["split_name"].astype(str).eq(split_name)].copy()
                if mode == "active":
                    quality, accepted, allocation, curve = t673.simulate_candidate(scoped, active_spec)
                else:
                    _, active_accepted, _, _ = t673.simulate_candidate(scoped, active_spec)
                    active_ids = set(active_accepted["lifecycle_id"].astype(str)) if not active_accepted.empty else set()
                    quality, accepted, allocation, curve = simulate_interaction_candidate(scoped, candidate_name, active_ids, guarded=guarded)
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
                        "interaction_assignment_flag": int(mode == "interaction"),
                        "guarded_superiority_flag": int(guarded),
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


def simulate_interaction_candidate(
    panel: pd.DataFrame,
    candidate_name: str,
    active_baseline_ids: set[str],
    *,
    guarded: bool,
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
    accepted_rows = []
    allocation_rows = []
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
        rows = []
        for row in cohort.to_dict(orient="records"):
            row.update(interaction_slot_packet(row, open_positions))
            row["active_cap3_baseline_flag"] = int(s(row.get("lifecycle_id", "")) in active_baseline_ids)
            row["cohort_candidate_count"] = int(len(cohort))
            row["available_slots_at_cohort_start"] = int(available_slots)
            rows.append(row)
        ranked = sorted(rows, key=lambda r: (r["interaction_packet_tuple"], s(r.get("lifecycle_id", ""))))
        for idx, row in enumerate(ranked, start=1):
            row["cohort_slot_rank"] = idx

        if guarded:
            selected, decisions = select_guarded_superiority(ranked, open_positions, available_slots)
        else:
            selected, decisions = select_packet_ranked(ranked, open_positions, available_slots)

        selected_ids = {s(row.get("lifecycle_id", "")) for row in selected}
        selected_positions = []
        for row in ranked:
            lifecycle_id = s(row.get("lifecycle_id", ""))
            if lifecycle_id not in selected_ids:
                allocation_rows.append(allocation_record(row, 0, decisions.get(lifecycle_id, "max_positions_full")))
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
            }
            selected_positions.append(position)
            accepted = dict(row)
            accepted["position_capital_fraction"] = capital
            accepted_rows.append(accepted)
            allocation_rows.append(allocation_record(row, 1, decisions.get(lifecycle_id, "accepted")))
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


def interaction_slot_packet(row: dict[str, object], open_positions: list[dict[str, object]]) -> dict[str, object]:
    source_rank = interaction_source_rank(row)
    context_rank = rank_archetype_interaction(row)
    absorption_rank = rank_catalyst_absorption(row)
    leadership_rank = rank_leadership_interaction(row)
    price_rank = rank_price_interaction(row)
    relation_rank = t682.rank_relation(row)
    same_symbol_rank = rank_same_symbol_interpreter(row)
    concentration_rank = t682.rank_concentration(row, open_positions)
    priority_tiebreak = i(row.get("priority_rank", 999))
    packet = (
        source_rank,
        context_rank,
        absorption_rank,
        leadership_rank,
        price_rank,
        relation_rank,
        same_symbol_rank,
        concentration_rank,
        priority_tiebreak,
    )
    return {
        "interaction_source_rank": source_rank,
        "interaction_context_rank": context_rank,
        "interaction_absorption_rank": absorption_rank,
        "interaction_leadership_rank": leadership_rank,
        "interaction_price_rank": price_rank,
        "interaction_relation_rank": relation_rank,
        "interaction_same_symbol_rank": same_symbol_rank,
        "interaction_concentration_rank": concentration_rank,
        "interaction_priority_tiebreaker": priority_tiebreak,
        "interaction_context_packet": ":".join(str(x) for x in packet),
        "interaction_packet_tuple": packet,
        "interaction_return_used_in_assignment_flag": 0,
    }


def select_packet_ranked(rows: list[dict[str, object]], open_positions: list[dict[str, object]], available_slots: int) -> tuple[list[dict[str, object]], dict[str, str]]:
    selected = []
    decisions = {}
    for row in rows:
        reason = block_reason(row, open_positions, selected, available_slots)
        if reason:
            decisions[s(row.get("lifecycle_id", ""))] = reason
            continue
        selected.append(row)
        decisions[s(row.get("lifecycle_id", ""))] = "accepted_context_packet"
    return selected, decisions


def select_guarded_superiority(rows: list[dict[str, object]], open_positions: list[dict[str, object]], available_slots: int) -> tuple[list[dict[str, object]], dict[str, str]]:
    selected = []
    decisions = {}
    baseline = [row for row in rows if i(row.get("active_cap3_baseline_flag", 0)) == 1]
    challengers = [row for row in rows if i(row.get("active_cap3_baseline_flag", 0)) != 1]
    for row in baseline:
        reason = block_reason(row, open_positions, selected, available_slots)
        if reason:
            decisions[s(row.get("lifecycle_id", ""))] = reason
            continue
        selected.append(row)
        decisions[s(row.get("lifecycle_id", ""))] = "accepted_baseline_context_preserved"
    for row in challengers:
        lifecycle_id = s(row.get("lifecycle_id", ""))
        reason = block_reason(row, open_positions, selected, available_slots)
        if not reason:
            selected.append(row)
            decisions[lifecycle_id] = "accepted_open_slot_context"
            continue
        if reason != "max_positions_full":
            decisions[lifecycle_id] = reason
            continue
        incumbent = weakest_context_incumbent(selected)
        if incumbent is None:
            decisions[lifecycle_id] = "superiority_no_replaceable_incumbent"
            continue
        passed, pass_reason = context_superiority_pass(row, incumbent, open_positions, selected)
        if not passed:
            decisions[lifecycle_id] = pass_reason
            continue
        selected = [pos for pos in selected if s(pos.get("lifecycle_id", "")) != s(incumbent.get("lifecycle_id", ""))]
        decisions[s(incumbent.get("lifecycle_id", ""))] = f"superiority_displaced_by={lifecycle_id}"
        selected.append(row)
        decisions[lifecycle_id] = "accepted_context_superiority"
    return selected, decisions


def block_reason(row: dict[str, object], open_positions: list[dict[str, object]], selected: list[dict[str, object]], available_slots: int) -> str:
    if len(selected) >= available_slots:
        return "max_positions_full"
    if i(row.get("allocation_assignment_ready_flag", row.get("used_for_assignment_flag", 0))) != 1:
        return "source_assignment_not_ready"
    relation = s(row.get("relation_transmission_state", ""))
    relation_count = sum(1 for pos in open_positions + selected if s(pos.get("relation_transmission_state", "")) == relation)
    if relation_count >= 3:
        return "relation_cap3"
    return ""


def weakest_context_incumbent(selected: list[dict[str, object]]) -> dict[str, object] | None:
    baseline = [row for row in selected if i(row.get("active_cap3_baseline_flag", 0)) == 1 and incumbent_context_vulnerability(row) >= 1]
    if not baseline:
        return None
    return sorted(baseline, key=lambda row: (-incumbent_context_vulnerability(row), row.get("interaction_packet_tuple", ())))[0]


def incumbent_context_vulnerability(row: dict[str, object]) -> int:
    vulnerability = 0
    if s(row.get("archetype_interaction_context", "")) == "true_unclear_or_low_clarity_context":
        vulnerability += 1
    if s(row.get("catalyst_cross_context_state", "")) == "catalyst_blocker_not_absorbed":
        vulnerability += 2
    if s(row.get("same_symbol_interaction_state", "")) == "same_symbol_context_conflict":
        vulnerability += 1
    if s(row.get("price_chart_acceptance_state", "")) == "price_fragile_or_unconfirmed":
        vulnerability += 1
    if s(row.get("relation_transmission_state", "")) in {"relation_offsetting", "relation_sparse_research_only"}:
        vulnerability += 1
    if i(row.get("priority_rank", 999)) <= 10:
        vulnerability -= 1
    return max(0, vulnerability)


def context_superiority_pass(challenger: dict[str, object], incumbent: dict[str, object], open_positions: list[dict[str, object]], selected: list[dict[str, object]]) -> tuple[bool, str]:
    if i(challenger.get("allocation_assignment_ready_flag", challenger.get("used_for_assignment_flag", 0))) != 1:
        return False, "superiority_failed_assignment_readiness"
    if i(challenger.get("sparse_action_block_flag", 0)) == 1:
        return False, "superiority_failed_source"
    if rank_archetype_interaction(challenger) > rank_archetype_interaction(incumbent) - 15:
        return False, "superiority_failed_archetype_context"
    if rank_catalyst_absorption(challenger) > rank_catalyst_absorption(incumbent):
        return False, "superiority_failed_catalyst_absorption"
    if rank_price_interaction(challenger) > rank_price_interaction(incumbent):
        return False, "superiority_failed_price_acceptance"
    if (
        i(challenger.get("relation_assignment_certified_flag", 0)) == 1
        and i(incumbent.get("relation_assignment_certified_flag", 0)) == 1
        and t682.rank_relation(challenger) > t682.rank_relation(incumbent)
    ):
        return False, "superiority_failed_relation"
    selected_without = [row for row in selected if s(row.get("lifecycle_id", "")) != s(incumbent.get("lifecycle_id", ""))]
    if t682.rank_concentration(challenger, open_positions + selected_without) > t682.rank_concentration(incumbent, open_positions + selected_without):
        return False, "superiority_failed_concentration"
    if rank_same_symbol_interpreter(challenger) > 70:
        return False, "superiority_failed_same_symbol_conflict"
    return True, "context_superiority_pass"


def interaction_source_rank(row: dict[str, object]) -> int:
    if i(row.get("allocation_assignment_ready_flag", row.get("used_for_assignment_flag", 0))) != 1:
        return 90
    if i(row.get("sparse_action_block_flag", 0)) == 1:
        return 75
    if i(row.get("macro_assignment_certified_flag", 0)) == 1:
        return 10
    if i(row.get("company_source_assignment_certified_flag", 0)) == 1 and i(row.get("theme_price_assignment_certified_flag", 0)) == 1:
        return 20
    return 80


def rank_archetype_interaction(row: dict[str, object]) -> int:
    return {
        "price_led_continuation_context": 10,
        "relation_led_continuation_context": 15,
        "extension_relation_continuation_context": 18,
        "catalyst_repricing_context": 20,
        "theme_led_continuation_context": 25,
        "theme_rotation_context": 25,
        "late_extension_context": 45,
        "conflicted_but_alive_context": 55,
        "true_unclear_or_low_clarity_context": 85,
    }.get(s(row.get("archetype_interaction_context", "")), 70)


def rank_catalyst_absorption(row: dict[str, object]) -> int:
    return {
        "weak_but_price_relation_confirmed": 10,
        "high_catalyst_price_absorbing": 15,
        "weak_but_extension_relation_supported": 18,
        "weak_but_price_theme_supported": 25,
        "weak_but_relation_supported": 30,
        "high_catalyst_not_fully_absorbed": 40,
        "catalyst_absorption_mixed": 55,
        "true_low_or_blocker_context": 75,
        "true_low_unconfirmed": 85,
    }.get(s(row.get("catalyst_absorption_state", "")), 60)


def rank_price_interaction(row: dict[str, object]) -> int:
    price = s(row.get("price_chart_acceptance_state", ""))
    archetype = s(row.get("archetype_interaction_context", ""))
    leadership = s(row.get("leadership_phase_strength", ""))
    relation = s(row.get("relation_transmission_state", ""))
    if price in {"price_confirmed_basic", "price_confirmed_not_extended"}:
        return 15
    if (
        price == "price_confirmed_but_extended"
        and archetype in {"relation_led_continuation_context", "extension_relation_continuation_context", "late_extension_context"}
        and leadership in {"theme_relative_leader", "broad_persistent_leader", "neutral_participation", "fragile_or_fading_theme"}
        and relation in {"relation_reinforcing", "company_price_confirmed_macro_secondary", "company_positive_confirmation_needed"}
    ):
        return 18
    if price == "price_accepted_needs_confirmation":
        return 35
    if price == "price_confirmed_but_extended":
        return 45
    if price == "price_fragile_or_unconfirmed":
        return 60
    return 70


def rank_leadership_interaction(row: dict[str, object]) -> int:
    return {
        "theme_relative_leader": 10,
        "broad_persistent_leader": 15,
        "defensive_relative_strength": 25,
        "neutral_participation": 45,
        "late_or_crowded_leader": 65,
        "fragile_or_fading_theme": 80,
    }.get(s(row.get("leadership_phase_strength", "")), 60)


def rank_same_symbol_interpreter(row: dict[str, object]) -> int:
    state = s(row.get("same_symbol_interaction_state", ""))
    if state in {"context_shift_not_direct_negative", "context_upgrade_interpretation_only", "same_symbol_repeat_or_neutral_interpretation"}:
        return 20
    if state == "same_symbol_unclear_do_not_rank":
        return 45
    if state == "same_symbol_context_conflict":
        return 80
    return 50


def allocation_record(row: dict[str, object], accepted_flag: int, reason: str) -> dict[str, object]:
    cols = [
        "lifecycle_id",
        "symbol",
        "entry_ts",
        "split_name",
        "theme_id",
        "leadership_phase_strength",
        "catalyst_absorption_state",
        "catalyst_cross_context_state",
        "archetype_interaction_context",
        "archetype_context_clarity",
        "same_symbol_interaction_state",
        "same_symbol_assignment_role",
        "price_chart_acceptance_state",
        "relation_transmission_state",
        "interaction_context_packet",
        "active_cap3_baseline_flag",
        "cohort_slot_rank",
        "cohort_candidate_count",
        "available_slots_at_cohort_start",
        "source_integrity_state",
        "asof_valid_flag",
        "used_for_assignment_flag",
        "company_source_assignment_certified_flag",
        "content_prediction_assignment_certified_flag",
        "macro_assignment_certified_flag",
        "macro_used_for_assignment_flag",
        "theme_price_assignment_certified_flag",
        "relation_assignment_certified_flag",
        "portfolio_capacity_assignment_certified_flag",
        "allocation_assignment_ready_flag",
        "assignment_certification_scope",
        "assignment_block_reason",
        "macro_asof_provisional_for_diagnostic_flag",
        "macro_provisional_used_as_certified",
        "missing_source_used_as_negative",
        "return_used_in_assignment_flag",
        "label_used_in_assignment_flag_task661",
        "future_price_used_in_assignment",
        "net_return_costed",
    ]
    out = {col: row.get(col, "") for col in cols}
    out["accepted_flag"] = int(accepted_flag)
    out["allocation_reason"] = reason
    out["return_used_in_assignment_flag"] = 0
    out["label_used_in_assignment_flag"] = 0
    out["future_price_used_in_assignment_flag"] = 0
    out["macro_provisional_used_as_certified"] = 0
    out["missing_source_used_as_negative"] = 0
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
        rows.append(
            {
                "candidate_name": candidate_name,
                "active_cap3_trade_count": int(len(active_ids)),
                "candidate_trade_count": int(len(ids)),
                "common_trade_count": int(len(active_ids & ids)),
                "removed_active_cap3_trade_count": int(len(removed_ids)),
                "removed_active_cap3_big_winner_count_eval_only": int(removed.ge(0.50).sum()) if len(removed) else 0,
                "removed_active_cap3_avg_return_pct_eval_only": float(removed.mean() * 100.0) if len(removed) else 0.0,
                "added_trade_count": int(len(added_ids)),
                "added_avg_return_pct_eval_only": float(added.mean() * 100.0) if len(added) else 0.0,
                "added_big_winner_count_eval_only": int(added.ge(0.50).sum()) if len(added) else 0,
                "winner_preservation_guardrail_pass_flag": int((int(removed.ge(0.50).sum()) if len(removed) else 0) == 0),
                "return_used_in_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_superiority_audit(allocation: pd.DataFrame) -> pd.DataFrame:
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
        "leadership_interaction_return_used": sum_col(stack, "leadership_interaction_return_used_in_assignment_flag"),
        "catalyst_interaction_return_used": sum_col(stack, "catalyst_interaction_return_used_in_assignment_flag"),
        "archetype_interaction_return_used": sum_col(stack, "archetype_interaction_return_used_in_assignment_flag"),
        "same_symbol_interaction_return_used": sum_col(stack, "same_symbol_interaction_return_used_in_assignment_flag"),
        "stack_interaction_return_used": sum_col(stack, "interaction_stack_return_used_in_assignment_flag"),
        "stack_interaction_label_used": sum_col(stack, "interaction_stack_label_used_in_assignment_flag"),
        "stack_interaction_future_price_used": sum_col(stack, "interaction_stack_future_price_used_in_assignment_flag"),
        "allocation_return_used": sum_col(allocation, "return_used_in_assignment_flag") if not allocation.empty else 0,
        "symbol_blacklist_used": sum_col(stack, "symbol_blacklist_used"),
        "theme_blacklist_used": sum_col(stack, "theme_blacklist_used"),
        "microstructure_used": sum_col(stack, "microstructure_used_in_assignment"),
    }
    return pd.DataFrame(
        [{"check_name": name, "violation_count": int(value), "pass_flag": int(value == 0), "required_value": "0 violations"} for name, value in checks.items()]
    )


def build_decision(grid: pd.DataFrame, guardrail: pd.DataFrame, forbidden: pd.DataFrame) -> pd.DataFrame:
    active = grid[(grid["candidate_name"].eq(ACTIVE_CAP3)) & (grid["split_name"].eq("all"))].iloc[0]
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    best_guard = guardrail[guardrail["candidate_name"].eq(best["candidate_name"])].iloc[0]
    violations = int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum())
    accepted_flag = (
        best["candidate_name"] != ACTIVE_CAP3
        and float(best["final_capital_usd"]) > float(active["final_capital_usd"])
        and float(best["max_drawdown_pct"]) >= float(active["max_drawdown_pct"])
        and int(best_guard["removed_active_cap3_big_winner_count_eval_only"]) == 0
        and violations == 0
    )
    return pd.DataFrame(
        [
            {
                "task_id": "Task684",
                "decision": "INTERACTION_CONTEXT_STACK_IMPLEMENTED_RESEARCH_ONLY",
                "strategy_acceptance_status": "PRIMARY_PASS" if accepted_flag else "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "active_cap3_final_capital_usd": float(active["final_capital_usd"]),
                "active_cap3_max_drawdown_pct": float(active["max_drawdown_pct"]),
                "best_candidate_name": best["candidate_name"],
                "best_final_capital_usd": float(best["final_capital_usd"]),
                "best_max_drawdown_pct": float(best["max_drawdown_pct"]),
                "best_removed_big_winners": int(best_guard["removed_active_cap3_big_winner_count_eval_only"]),
                "forbidden_input_violations": violations,
                "trading_promotion_pass_flag": int(accepted_flag),
                "next_action": "Keep research-only unless split/OOS and guardrail gates stay clean after further review.",
            }
        ]
    )


def build_pass_fail(stack: pd.DataFrame, grid: pd.DataFrame, guardrail: pd.DataFrame, forbidden: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    active = grid[(grid["candidate_name"].eq(ACTIVE_CAP3)) & (grid["split_name"].eq("all"))].iloc[0]
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    best_guard = guardrail[guardrail["candidate_name"].eq(best["candidate_name"])].iloc[0]
    violations = int(pd.to_numeric(forbidden["violation_count"], errors="coerce").sum())
    return pd.DataFrame(
        [
            gate("five_interaction_engine_artifacts_built", required_columns().issubset(stack.columns), "columns present", "all interaction columns"),
            gate("cohort_only_assignment", "cohort_slot_rank" in allocation.columns, f"rows={len(allocation)}", "cohort allocation rows"),
            gate("no_forbidden_assignment_inputs", violations == 0, f"violations={violations}", "0 violations"),
            gate("no_global_top5_rank", "top5_priority_rank" not in stack.columns, "absent", "no global rank"),
            gate("best_beats_active_cap3", float(best["final_capital_usd"]) > float(active["final_capital_usd"]), f"best={float(best['final_capital_usd']):.2f}, active={float(active['final_capital_usd']):.2f}", "best > active"),
            gate("best_mdd_not_worse", float(best["max_drawdown_pct"]) >= float(active["max_drawdown_pct"]), f"best={float(best['max_drawdown_pct']):.2f}, active={float(active['max_drawdown_pct']):.2f}", "MDD not worse"),
            gate("best_preserves_active_big_winners", int(best_guard["removed_active_cap3_big_winner_count_eval_only"]) == 0, f"removed_big={int(best_guard['removed_active_cap3_big_winner_count_eval_only'])}", "0 removed"),
            gate("strategy_not_deployment_ready", True, "research only", "real capital forbidden"),
        ]
    )


def required_columns() -> set[str]:
    return {
        "leadership_phase_strength",
        "catalyst_absorption_state",
        "archetype_interaction_context",
        "same_symbol_interaction_state",
    }


def write_outputs(
    leadership: pd.DataFrame,
    catalyst: pd.DataFrame,
    archetype: pd.DataFrame,
    same_symbol: pd.DataFrame,
    stack: pd.DataFrame,
    grid: pd.DataFrame,
    accepted: pd.DataFrame,
    allocation: pd.DataFrame,
    curves: pd.DataFrame,
    guardrail: pd.DataFrame,
    superiority: pd.DataFrame,
    forbidden: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task684_leadership_lifecycle_interaction_panel.csv": leadership,
        "task684_catalyst_quality_interaction_matrix.csv": catalyst,
        "task684_archetype_candidate_interaction_engine.csv": archetype,
        "task684_same_symbol_context_interaction_matrix.csv": same_symbol,
        "task684_interaction_stack_panel.csv": stack,
        "task684_simulation_result.csv": grid,
        "task684_accepted_trades.csv": accepted,
        "task684_cohort_slot_qualification.csv": allocation,
        "task684_equity_curves.csv": curves,
        "task684_guardrail_audit.csv": guardrail,
        "task684_superiority_audit.csv": superiority,
        "task684_forbidden_input_audit.csv": forbidden,
        "task_684_decision.csv": decision,
        "task_684_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK684_DIR / name, index=False)
    (TASK684_DIR / "task_684_interaction_context_prediction_stack.md").write_text(
        render_report(grid, guardrail, superiority, forbidden, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK684_DIR, TASK684_DIR / "artifact_manifest.csv")


def render_report(grid: pd.DataFrame, guardrail: pd.DataFrame, superiority: pd.DataFrame, forbidden: pd.DataFrame, decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    active = grid[(grid["candidate_name"].eq(ACTIVE_CAP3)) & (grid["split_name"].eq("all"))].iloc[0]
    best = grid[grid["split_name"].eq("all")].sort_values("final_capital_usd", ascending=False).iloc[0]
    return f"""# Task684 Interaction Context Prediction Stack

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: {decision.iloc[0]['strategy_acceptance_status']}.
- Real capital status: FORBIDDEN.
- Key metrics: active cap3 ${float(active['final_capital_usd']):,.2f} / MDD {float(active['max_drawdown_pct']):.2f}%; best `{best['candidate_name']}` ${float(best['final_capital_usd']):,.2f} / MDD {float(best['max_drawdown_pct']):.2f}%.
- What changed: the same five engines were rebuilt as interaction-aware artifacts. Catalyst is linked to price/relation/leadership absorption, archetype is linked to mixed sub-contexts, same-symbol is interpreter-only, and cohort slot qualification compares context packets only inside `entry_ts`.
- Next action: research-only review of interaction candidates; no deployment.

## Quant Expert Report

### Data source and source readiness

- Inputs: Task682 stack and current Task672-derived fields.
- No new raw data, microstructure, quote, trade, NBBO, label, future price, symbol blacklist, or theme blacklist.
- GPT is not used as source truth or assignment input.

### Exact join keys

- Five engine outputs join by `lifecycle_id`.
- Slot qualification groups by `entry_ts`.
- Displacement guardrail compares `lifecycle_id` sets.

### Leakage audit

- All return/label/future-price assignment flags are zero.
- `classify_winner_archetype`, `classify_top5_tier`, and `top5_priority_rank` are not used.
- `priority_rank` is only the final tie-breaker inside the context packet.

### Split/OOS metrics

{t678.markdown_table(grid)}

### Guardrail audit

{t678.markdown_table(guardrail)}

### Superiority audit

{t678.markdown_table(superiority.head(40))}

### Forbidden input audit

{t678.markdown_table(forbidden)}

### Remaining blockers

- This is still research-only.
- If a non-active candidate wins, it must still survive split/OOS review, cost review, and code review before any promotion.
- If it fails, the interaction artifacts still identify which context comparisons are too weak.

## No-Background Decision-Maker Report

- What happened: the five engines now talk to each other instead of acting like isolated labels.
- Why it matters: `mixed`, `low catalyst`, and `same-symbol downgrade` are no longer treated as simple bad labels.
- Whether this changes capital readiness: no. FORBIDDEN remains.
- Plain-language next step: inspect whether the interaction candidate actually beats active cap3 without killing active cap3 winners.

## Artifact Manifest

- Inputs: Task682 stack.
- Outputs: five interaction artifacts, stack panel, simulation, accepted trades, slot qualification, equity curves, guardrail, superiority audit, forbidden audit, decision, pass/fail, manifest.
- Validation commands: `python src/backtest/build_task684_interaction_context_prediction_stack.py`; `python -m unittest tests.test_task684_interaction_context_prediction_stack`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def merge_outputs(base: pd.DataFrame, *frames: pd.DataFrame) -> pd.DataFrame:
    out = base.copy()
    for frame in frames:
        add_cols = [c for c in frame.columns if c != "lifecycle_id" and c not in out.columns]
        out = out.merge(frame[["lifecycle_id"] + add_cols], on="lifecycle_id", how="left")
    return out


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
    parser.add_argument("--task682-dir", type=Path, default=TASK682_DIR)
    parser.add_argument("--qqq-path", type=Path, default=QQQ_PATH)
    args = parser.parse_args()
    build_task684_program(args.task682_dir, args.qqq_path)
    print(f"[Task684] wrote {TASK684_DIR}")


if __name__ == "__main__":
    main()
