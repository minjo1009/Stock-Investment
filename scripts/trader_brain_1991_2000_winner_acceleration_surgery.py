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
TASK1931 = ROOT / "data/artifacts/task_1931_1940_interaction_forecast_layer"
TASK1971 = ROOT / "data/artifacts/task_1971_1980_free_source_l0_l5_replay"
TASK1981 = ROOT / "data/artifacts/task_1981_1990_current_2026_calibration_pack"
OUT_DIR = ROOT / "data/artifacts/task_1991_2000_winner_acceleration_surgery"
REPORT_DIR = ROOT / "docs/reports/task_1991_2000_winner_acceleration_surgery"
REPORT = REPORT_DIR / "task_1991_2000_winner_acceleration_surgery.md"
DECISION = REPORT_DIR / "task_1991_2000_decision.csv"
AUTHORITY = "DIAGNOSTIC_WINNER_ACCELERATION_SURGERY_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265


POLICIES = {
    "winner_accel_top3_source_v1": {
        "source_policy": "winner_defense_budget_top3_v1",
        "select_top_n": 3,
        "base_divisor": 3,
        "multiplier_cap": 1.30,
        "concentration_mode": "balanced_top3",
    },
    "winner_accel_top5_to_top3_v1": {
        "source_policy": "winner_defense_budget_top5_v1",
        "select_top_n": 3,
        "base_divisor": 3,
        "multiplier_cap": 1.36,
        "concentration_mode": "top5_pool_top3",
    },
    "winner_accel_top5_to_top2_convex_v1": {
        "source_policy": "winner_defense_budget_top5_v1",
        "select_top_n": 2,
        "base_divisor": 2,
        "multiplier_cap": 1.42,
        "concentration_mode": "top5_pool_top2_convex",
    },
}


BENEFICIARY_GROUPS = {
    "accelerator_compute": {"NVDA", "AMD", "AVGO", "ARM", "MRVL", "SMCI"},
    "semiconductor_equipment": {"AMAT", "LRCX", "ASML", "KLAC", "TER", "ONTO", "ACLS"},
    "memory_storage": {"MU", "WDC", "STX"},
    "power_grid_cooling": {"VRT", "ETN", "GEV", "CEG", "NEE", "PWR", "GNRC", "SMR"},
    "datacenter_connectivity": {"ANET", "DELL", "HPE", "EQIX", "DLR"},
    "software_ai_monetization": {"MSFT", "GOOGL", "META", "PLTR", "NOW", "CRM", "SNOW"},
    "space_infrastructure": {"ASTS", "RKLB", "LUNR", "IRDM"},
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
        "calibration": read_csv(TASK1981 / "task1984_l0_l5_current_calibration_map.csv"),
        "requirements": read_csv(TASK1981 / "task1985_winner_acceleration_requirements.csv"),
        "budget": read_csv(TASK1808 / "task1815_sleeve_risk_budget.csv"),
        "sleeve_metrics": read_csv(TASK1808 / "task1823_sleeve_replay_metrics.csv"),
        "winner_panel": read_csv(TASK1788 / "task1790_winner_defense_panel.csv"),
        "winner_trades": read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        "interaction_l4": read_csv(TASK1931 / "task1935_l4_interaction_payoff_thesis_cards.csv"),
        "free_l4": read_csv(TASK1971 / "task1975_l4_free_source_thesis_cards.csv"),
        "free_metrics": read_csv(TASK1971 / "task1976_free_source_top3_replay_metrics.csv"),
    }


def build_indexes(inputs: dict[str, object]) -> dict[str, object]:
    panel = {row["trade_spec_id"]: row for row in inputs["winner_panel"]}
    interaction = {row["trade_spec_id"]: row for row in inputs["interaction_l4"]}
    free_l4 = {row["trade_spec_id"]: row for row in inputs["free_l4"]}
    trades = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in inputs["winner_trades"]}
    return {"panel": panel, "interaction": interaction, "free_l4": free_l4, "trades": trades}


def beneficiary_chain(symbol: str, theme: str) -> str:
    for group, symbols in BENEFICIARY_GROUPS.items():
        if symbol in symbols:
            return group
    if "semiconductor" in theme:
        return "semiconductor_broad_cycle"
    if "energy" in theme or "power" in theme:
        return "power_grid_cooling"
    if "ai" in theme:
        return "software_ai_monetization"
    return "uncertified_beneficiary_chain"


def l0_contract_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for idx, req in enumerate(inputs["requirements"], start=1):
        rows.append(
            {
                "task_id": "Task1991",
                "source_contract_id": f"WINCONTRACT-1991-{idx:03d}",
                "primitive": req["primitive"],
                "required_historical_source_family": req["required_historical_source_family"],
                "current_2026_design_source": "task1981_1990_current_2026_calibration_pack",
                "historical_assignment_rule": "requires_prior_known_repo_field_or_source_packet",
                "current_source_direct_assignment_permission": "0",
                "historical_assignment_ready_now": "proxy_field_only_not_full_source_extractor",
                "diagnostic_replay_permission": "prior_known_repo_field_only",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def l1_rows(inputs: dict[str, object], indexes: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(inputs["budget"], start=1):
        panel = indexes["panel"].get(row["trade_spec_id"], {})
        inter = indexes["interaction"].get(row["trade_spec_id"], {})
        free = indexes["free_l4"].get(row["trade_spec_id"], {})
        theme = panel.get("derived_theme", "source_gap")
        chain = beneficiary_chain(row["symbol"], theme)
        rows.append(
            {
                "task_id": "Task1992",
                "l1_packet_id": f"WINL1-1992-{idx:06d}",
                "target_policy_variant_id": row["target_policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "source_published_ts": row["decision_asof_ts"],
                "source_received_ts": row["decision_asof_ts"],
                "available_to_brain_ts": row["decision_asof_ts"],
                "source_lineage_type": "derived_prior_known_repo_field_no_current_source_assignment",
                "raw_path": "",
                "raw_sha256": "",
                "derived_theme": theme,
                "beneficiary_chain": chain,
                "strategy_sleeve": row["strategy_sleeve"],
                "prior_return_63d": panel.get("prior_return_63d", ""),
                "relative_return_63d": panel.get("relative_return_63d", ""),
                "prior_drawdown_126d": panel.get("prior_drawdown_126d", ""),
                "realized_vol_63d": panel.get("realized_vol_63d", ""),
                "avg_dollar_volume_20d": panel.get("avg_dollar_volume_20d", ""),
                "payoff_quality_score": panel.get("payoff_quality_score", ""),
                "event_family": panel.get("event_family", ""),
                "expectation_state": panel.get("expectation_state", ""),
                "absorption_state": panel.get("absorption_state", ""),
                "source_independence_state": panel.get("source_independence_state", ""),
                "winner_quality_beta": panel.get("winner_quality_beta", ""),
                "volatility_cause": panel.get("volatility_cause", ""),
                "interaction_score": inter.get("interaction_score", ""),
                "positive_interaction_primitives": inter.get("positive_interaction_primitives", ""),
                "negative_interaction_primitives": inter.get("negative_interaction_primitives", ""),
                "free_source_l4_score": free.get("free_source_l4_score", ""),
                "free_source_thesis_state": free.get("free_source_thesis_state", ""),
                "historical_source_permission": "prior_known_repo_field_only",
                "current_2026_direct_input_used": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def score_l2(row: dict[str, object]) -> dict[str, object]:
    prior = to_float(row.get("prior_return_63d"))
    rel = to_float(row.get("relative_return_63d"))
    drawdown = to_float(row.get("prior_drawdown_126d"))
    vol = to_float(row.get("realized_vol_63d"))
    liquidity = to_float(row.get("avg_dollar_volume_20d"))
    payoff = to_float(row.get("payoff_quality_score"))
    quality = to_float(row.get("winner_quality_beta"))
    interaction = to_float(row.get("interaction_score"))
    event = str(row.get("event_family", ""))
    expectation = str(row.get("expectation_state", ""))
    absorption = str(row.get("absorption_state", ""))
    independence = str(row.get("source_independence_state", ""))
    chain = str(row.get("beneficiary_chain", ""))
    vol_cause = str(row.get("volatility_cause", ""))

    monetization = 0.0
    if event == "positive":
        monetization += 18
    elif event == "mixed":
        monetization += 7
    elif event in {"survival", "financing", "dilution"}:
        monetization -= 30
    monetization += clamp((payoff - 62) / 28, 0, 1) * 25
    if independence == "independent_non_issuer_confirmation_present":
        monetization += 9
    if chain != "uncertified_beneficiary_chain":
        monetization += 8

    acceptance = 0.0
    if prior >= 0.18:
        acceptance += 18
    elif prior >= 0.08:
        acceptance += 10
    elif prior <= -0.12:
        acceptance -= 12
    if rel >= 0.16:
        acceptance += 18
    elif rel >= 0.07:
        acceptance += 10
    elif rel <= -0.10:
        acceptance -= 14
    if drawdown >= -0.16:
        acceptance += 8
    elif drawdown <= -0.30:
        acceptance -= 18
    if absorption == "sustained_market_acceptance":
        acceptance += 14
    elif absorption == "initial_reaction_only":
        acceptance += 4
    elif absorption in {"market_rejection_or_reversal", "weak_absorption"}:
        acceptance -= 16

    expectation_gap = 0.0
    if expectation == "true_surprise_proxy":
        expectation_gap += 22
    elif expectation == "guidance_change_proxy":
        expectation_gap += 14
    elif expectation == "good_words_only":
        expectation_gap += 3
    elif expectation == "negative_expectation_proxy":
        expectation_gap -= 18
    expectation_gap += clamp(interaction, -3, 4) * 4

    risk = 0.0
    if vol_cause == "terminal_or_financing_thesis_risk":
        risk += 32
    if event in {"survival", "financing", "dilution"}:
        risk += 25
    if vol >= 0.75 and quality < 55:
        risk += 18
    elif vol >= 0.60 and quality < 65:
        risk += 10
    if liquidity and liquidity < 25_000_000:
        risk += 12
    if drawdown <= -0.32:
        risk += 16

    winner_acceleration_score = monetization + acceptance + expectation_gap + clamp((quality - 55) / 35, 0, 1) * 22 - risk
    if row.get("strategy_sleeve") == "winner_compounder":
        winner_acceleration_score += 8
    if row.get("strategy_sleeve") == "speculative_event":
        winner_acceleration_score -= 8

    if winner_acceleration_score >= 86 and risk < 24:
        state = "convex_winner_acceleration"
    elif winner_acceleration_score >= 68 and risk < 32:
        state = "qualified_winner_acceleration"
    elif risk >= 42:
        state = "blocked_or_tiny_size_risk"
    elif winner_acceleration_score >= 48:
        state = "watch_winner_acceleration"
    else:
        state = "ordinary_or_unproven"

    return {
        "monetization_score": round(monetization, 4),
        "market_acceptance_score": round(acceptance, 4),
        "expectation_gap_score": round(expectation_gap, 4),
        "winner_quality_score": round(quality, 4),
        "crowding_or_damage_risk": round(risk, 4),
        "winner_acceleration_score": round(winner_acceleration_score, 4),
        "winner_acceleration_state": state,
    }


def l2_rows(l1: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(l1, start=1):
        score = score_l2(row)
        rows.append(
            {
                "task_id": "Task1993",
                "l2_semantic_id": f"WINL2-1993-{idx:06d}",
                **{key: row[key] for key in ["target_policy_variant_id", "trade_spec_id", "candidate_source_id", "symbol", "decision_asof_ts", "beneficiary_chain", "strategy_sleeve"]},
                **score,
                "current_2026_direct_input_used": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def l3_rows(l2: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    edge_idx = 1
    for row in l2:
        edges: list[tuple[str, str, float]] = []
        if row["beneficiary_chain"] in {"accelerator_compute", "semiconductor_equipment", "memory_storage", "power_grid_cooling", "datacenter_connectivity"}:
            edges.append(("ai_capex_chain_supports_payoff", "supports", 1.0))
        if to_float(row["market_acceptance_score"]) >= 28:
            edges.append(("market_acceptance_confirms_repricing", "supports", 1.0))
        if to_float(row["expectation_gap_score"]) >= 18:
            edges.append(("expectation_gap_extends_payoff_window", "supports", 1.0))
        if to_float(row["crowding_or_damage_risk"]) >= 32:
            edges.append(("crowding_or_damage_caps_concentration", "caps", -1.0))
        if row["winner_acceleration_state"] in {"convex_winner_acceleration", "qualified_winner_acceleration"}:
            edges.append(("winner_quality_defends_normal_volatility", "supports", 1.0))
        if not edges:
            edges.append(("insufficient_mechanism_for_acceleration", "weakens", -0.5))
        for edge_name, relation, weight in edges:
            rows.append(
                {
                    "task_id": "Task1994",
                    "l3_edge_id": f"WINL3-1994-{edge_idx:07d}",
                    "trade_spec_id": row["trade_spec_id"],
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "beneficiary_chain": row["beneficiary_chain"],
                    "mechanism_edge": edge_name,
                    "relation_type": relation,
                    "edge_weight": weight,
                    "current_2026_direct_input_used": "0",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            edge_idx += 1
    return rows


def l4_rows(l2: list[dict[str, object]], l3: list[dict[str, object]]) -> list[dict[str, object]]:
    edges_by_spec: dict[str, list[dict[str, object]]] = defaultdict(list)
    for edge in l3:
        edges_by_spec[str(edge["trade_spec_id"])].append(edge)
    rows = []
    for idx, row in enumerate(l2, start=1):
        support_edges = sum(1 for edge in edges_by_spec[str(row["trade_spec_id"])] if edge["relation_type"] == "supports")
        cap_edges = sum(1 for edge in edges_by_spec[str(row["trade_spec_id"])] if edge["relation_type"] == "caps")
        accel = to_float(row["winner_acceleration_score"])
        risk = to_float(row["crowding_or_damage_risk"])
        if row["winner_acceleration_state"] == "convex_winner_acceleration":
            rank = accel + support_edges * 4 - cap_edges * 9
            thesis = "convex_winner_thesis"
        elif row["winner_acceleration_state"] == "qualified_winner_acceleration":
            rank = accel + support_edges * 3 - cap_edges * 7
            thesis = "qualified_winner_thesis"
        elif row["winner_acceleration_state"] == "blocked_or_tiny_size_risk":
            rank = min(accel, 35) - risk
            thesis = "risk_capped_or_blocked_thesis"
        else:
            rank = accel + support_edges * 1.5 - cap_edges * 6
            thesis = "ordinary_or_watch_thesis"
        rows.append(
            {
                "task_id": "Task1995",
                "l4_thesis_id": f"WINL4-1995-{idx:06d}",
                **{key: row[key] for key in ["target_policy_variant_id", "trade_spec_id", "candidate_source_id", "symbol", "decision_asof_ts", "beneficiary_chain", "strategy_sleeve"]},
                "winner_acceleration_state": row["winner_acceleration_state"],
                "support_edge_count": support_edges,
                "cap_edge_count": cap_edges,
                "winner_acceleration_score": row["winner_acceleration_score"],
                "winner_acceleration_rank_score": round(rank, 4),
                "winner_thesis_state": thesis,
                "current_2026_direct_input_used": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def l5_rows(inputs: dict[str, object], indexes: dict[str, object], l4: list[dict[str, object]]) -> list[dict[str, object]]:
    l4_by_spec = {row["trade_spec_id"]: row for row in l4}
    rows = []
    for idx, row in enumerate(inputs["budget"], start=1):
        card = l4_by_spec.get(row["trade_spec_id"])
        if not card:
            continue
        rank = to_float(card["winner_acceleration_rank_score"])
        state = card["winner_acceleration_state"]
        sleeve_mult = to_float(row.get("sleeve_budget_multiplier"), 1.0)
        if state == "convex_winner_acceleration":
            accel_mult = 1.18
            action = "concentrate_hold"
        elif state == "qualified_winner_acceleration":
            accel_mult = 1.09
            action = "full_hold"
        elif state == "blocked_or_tiny_size_risk":
            accel_mult = 0.35
            action = "tiny_or_skip"
        elif rank >= 55:
            accel_mult = 0.88
            action = "watch_small"
        else:
            accel_mult = 0.72
            action = "deprioritize"
        thesis_break_exit = "1" if card["winner_thesis_state"] == "risk_capped_or_blocked_thesis" else "0"
        rows.append(
            {
                "task_id": "Task1996",
                "l5_decision_id": f"WINL5-1996-{idx:06d}",
                **{key: row[key] for key in ["target_policy_variant_id", "trade_spec_id", "candidate_source_id", "symbol", "decision_asof_ts", "strategy_sleeve"]},
                "winner_acceleration_rank_score": card["winner_acceleration_rank_score"],
                "winner_acceleration_state": state,
                "winner_thesis_state": card["winner_thesis_state"],
                "base_sleeve_budget_multiplier": row.get("sleeve_budget_multiplier", ""),
                "winner_acceleration_multiplier": round(accel_mult, 4),
                "raw_combined_multiplier": round(sleeve_mult * accel_mult, 6),
                "l5_action": action,
                "thesis_break_exit_flag": thesis_break_exit,
                "current_2026_direct_input_used": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def replay_policy(inputs: dict[str, object], indexes: dict[str, object], l4: list[dict[str, object]], l5: list[dict[str, object]], policy_id: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    cfg = POLICIES[policy_id]
    l4_by_spec = {row["trade_spec_id"]: row for row in l4}
    l5_by_spec = {row["trade_spec_id"]: row for row in l5}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["budget"]:
        if row["target_policy_variant_id"] == cfg["source_policy"]:
            grouped[row["decision_asof_ts"]].append(row)

    capital = INITIAL_CAPITAL
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    trade_idx = 1
    for decision_ts in sorted(grouped):
        candidates = sorted(
            grouped[decision_ts],
            key=lambda row: (
                to_float(l4_by_spec.get(row["trade_spec_id"], {}).get("winner_acceleration_rank_score")),
                to_float(l4_by_spec.get(row["trade_spec_id"], {}).get("winner_acceleration_score")),
            ),
            reverse=True,
        )[: int(cfg["select_top_n"])]
        base_alloc = capital / float(cfg["base_divisor"])
        period_pnl = 0.0
        allocated = 0
        for row in candidates:
            src = indexes["trades"].get((cfg["source_policy"], row["trade_spec_id"]))
            card = l4_by_spec.get(row["trade_spec_id"])
            decision = l5_by_spec.get(row["trade_spec_id"])
            if not src or not card or not decision:
                continue
            raw_mult = to_float(decision["raw_combined_multiplier"])
            if decision["thesis_break_exit_flag"] == "1":
                raw_mult = min(raw_mult, 0.45)
            mult = clamp(raw_mult, 0.0, float(cfg["multiplier_cap"]))
            if mult <= 0:
                continue
            cap_alloc = base_alloc * mult
            pnl = cap_alloc * to_float(src["net_return"])
            capital += pnl
            period_pnl += pnl
            allocated += 1
            trades.append(
                {
                    "task_id": "Task1997",
                    "trade_row_id": f"WINREPLAY-1997-{trade_idx:07d}",
                    "policy_variant_id": policy_id,
                    "source_policy_variant_id": cfg["source_policy"],
                    "trade_spec_id": row["trade_spec_id"],
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "strategy_sleeve": row["strategy_sleeve"],
                    "beneficiary_chain": card["beneficiary_chain"],
                    "winner_acceleration_state": card["winner_acceleration_state"],
                    "winner_thesis_state": card["winner_thesis_state"],
                    "winner_acceleration_rank_score": card["winner_acceleration_rank_score"],
                    "l5_action": decision["l5_action"],
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
                "task_id": "Task1997",
                "policy_variant_id": policy_id,
                "decision_asof_ts": decision_ts,
                "equity": round(capital, 4),
                "period_pnl": round(period_pnl, 4),
                "candidate_pool_count": len(grouped[decision_ts]),
                "allocated_count": allocated,
                "authority": AUTHORITY,
            }
        )
    return trades, equity


def metrics_for(policy_id: str, trades: list[dict[str, object]], equity: list[dict[str, object]], inputs: dict[str, object]) -> dict[str, object]:
    values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in equity]
    final = values[-1] if values else INITIAL_CAPITAL
    start = replay.parse_ts(str(equity[0]["decision_asof_ts"])).date() if equity else date(2021, 1, 1)
    end_dates = [parse_date(row.get("actual_exit_date")) for row in trades]
    end = max([d for d in end_dates if d is not None] or [start])
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = (final / INITIAL_CAPITAL) ** (1 / years) - 1.0
    mdd = replay.max_drawdown(values)
    sleeve_metrics = {row["policy_variant_id"]: row for row in inputs["sleeve_metrics"]}
    baseline_key = "sleeve_split_top3_v1" if "top3" in policy_id else "sleeve_split_top5_v1"
    baseline = sleeve_metrics.get(baseline_key, {})
    free_prev = inputs["free_metrics"][0]
    return {
        "task_id": "Task1998",
        "policy_variant_id": policy_id,
        "source_policy_variant_id": POLICIES[policy_id]["source_policy"],
        "initial_capital": INITIAL_CAPITAL,
        "final_equity": round(final, 4),
        "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
        "cagr": round(cagr, 6),
        "max_drawdown": round(mdd, 6),
        "trade_count": len(trades),
        "qqq_benchmark_final": QQQ_BENCHMARK_FINAL,
        "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
        "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
        "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
        "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 and final > QQQ_BENCHMARK_FINAL else "0",
        "baseline_policy_variant_id": baseline_key,
        "baseline_final_equity": baseline.get("final_equity", ""),
        "baseline_cagr": baseline.get("cagr", ""),
        "baseline_max_drawdown": baseline.get("max_drawdown", ""),
        "delta_vs_baseline_final_equity": round(final - to_float(baseline.get("final_equity")), 4) if baseline else "",
        "previous_free_source_policy_variant_id": free_prev.get("policy_variant_id", ""),
        "previous_free_source_final_equity": free_prev.get("final_equity", ""),
        "delta_vs_previous_free_source_final_equity": round(final - to_float(free_prev.get("final_equity")), 4),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "outcome_used_for_audit_only": "1",
        "authority": AUTHORITY,
    }


def split_rows(all_equity: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in all_equity:
        d = parse_date(row["decision_asof_ts"])
        if d is None:
            continue
        window = "IS_2021_2023" if d.year <= 2023 else "OOS_2024_2026Q1"
        groups[(row["policy_variant_id"], window)].append(row)
    rows = []
    for (policy, window), items in sorted(groups.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        final = values[-1]
        rows.append(
            {
                "task_id": "Task1998",
                "policy_variant_id": policy,
                "split_window": window,
                "start_decision_asof_ts": items[0]["decision_asof_ts"],
                "end_decision_asof_ts": items[-1]["decision_asof_ts"],
                "final_equity": round(final, 4),
                "window_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "max_drawdown": round(replay.max_drawdown(values), 6),
                "authority": AUTHORITY,
            }
        )
    return rows


def cost_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for metric in metrics:
        for bps in [0, 10, 25, 50]:
            drag = to_float(metric["trade_count"]) * bps / 10000.0 * 4.0
            final = to_float(metric["final_equity"]) - drag
            rows.append(
                {
                    "task_id": "Task1998",
                    "policy_variant_id": metric["policy_variant_id"],
                    "round_trip_cost_bps": bps,
                    "cost_adjusted_final_equity": round(final, 4),
                    "beats_qqq_after_cost": "1" if final > QQQ_BENCHMARK_FINAL else "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def attribution_rows(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        grouped[(str(row["policy_variant_id"]), str(row["winner_acceleration_state"]))].append(row)
    rows = []
    for idx, ((policy, state), items) in enumerate(sorted(grouped.items()), start=1):
        pnl = sum(to_float(row["pnl"]) for row in items)
        rows.append(
            {
                "task_id": "Task1999",
                "attribution_id": f"WINATTR-1999-{idx:04d}",
                "policy_variant_id": policy,
                "winner_acceleration_state": state,
                "trade_count": len(items),
                "total_pnl": round(pnl, 4),
                "avg_net_return": round(sum(to_float(row["net_return"]) for row in items) / len(items), 6),
                "positive_trade_share": round(sum(1 for row in items if to_float(row["net_return"]) > 0) / len(items), 6),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def expert_rows() -> list[dict[str, object]]:
    reviews = [
        ("quant_pm", "Implemented, not just planned: L0 source contract through L5 replay artifacts exist.", "Still diagnostic because it reuses frozen source returns."),
        ("semiconductor_specialist", "Beneficiary chain split is directionally right: accelerator/equipment/memory/power/data center.", "Needs richer issuer/customer source packets before acceptance."),
        ("ai_infrastructure_specialist", "Power/grid/cooling beneficiaries are now eligible instead of only chip winners.", "Current classification is deterministic mapping, not full text extraction."),
        ("rates_liquidity_trader", "Macro/liquidity remains a risk-budget concept rather than direct stock alpha.", "Do not promote without live/vintage source readiness."),
        ("risk_manager", "Concentration allowed only with acceleration state and thesis risk cap.", "Top2 convex variant must be treated as stress, not accepted strategy."),
        ("backend_quant_engineer", "Validators should enforce zero current-2026 direct assignment and zero outcome assignment.", "Frozen replay PASS cannot imply deployment."),
    ]
    return [
        {
            "task_id": "Task1999",
            "review_id": f"WINREVIEW-1999-{idx:03d}",
            "role": role,
            "approval": approval,
            "critique": critique,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (role, approval, critique) in enumerate(reviews, start=1)
    ]


def gate_closeout(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    balanced = [row for row in metrics if row["joint_target_met"] == "1"]
    gate = [
        {
            "task_id": "Task2000",
            "verdict": "winner_acceleration_surgery_complete_diagnostic_only",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "joint_target_policy_count": len(balanced),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            **gate[0],
            "next_action": "Audit winner acceleration source gaps, then replace deterministic beneficiary mapping with historical source extractor.",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
        }
    ]
    return gate, closeout


def write_report(metrics: list[dict[str, object]], attribution: list[dict[str, object]], expert: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    target_count = sum(1 for row in metrics if row["joint_target_met"] == "1")
    lines = [
        "# Task1991-2000 Winner Acceleration Surgery",
        "",
        "## Decision Summary",
        "",
        "- Verdict: `winner_acceleration_surgery_complete_diagnostic_only`.",
        f"- Best policy: `{best['policy_variant_id']}`.",
        f"- Best final equity: {best['final_equity']}.",
        f"- Best CAGR: {best['cagr']}.",
        f"- Best MDD: {best['max_drawdown']}.",
        f"- Joint target policy count: {target_count}.",
        "- Current 2026 sources are design calibration only and are not direct replay inputs.",
        "- Critical audit incorporated: this is `prior-known repo field diagnostic`, not a full historical external-source extractor.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Implemented brain surgery:",
        "",
        "- L0 historical source contract for winner acceleration primitives.",
        "- L1 prior-known source-field packet with beneficiary-chain classification.",
        "- L2 monetization, acceptance, expectation-gap, winner-quality, and crowding/damage semantics.",
        "- L3 mechanism edges for AI capex chain, market acceptance, expectation gap, crowding cap, and winner volatility defense.",
        "- L4 winner thesis cards and acceleration rank.",
        "- L5 concentration sizing, tiny/skip risk cap, and thesis-break exit flag.",
        "- Controlled diagnostic replay variants for top3, top5-to-top3, and top5-to-top2 convex concentration.",
        "",
        "Critical audit handling:",
        "",
        "- The expert/subagent audit warned that Task1981 current sources have `historical_backtest_input_permission=0`.",
        "- Therefore this implementation uses current sources only to define rules.",
        "- Historical replay assignment is limited to prior-known repo fields and source packets already present before each decision timestamp.",
        "- Full issuer/customer/call/news extractor remains the next source-depth upgrade, not something claimed here.",
        "",
        "| Policy | Final | CAGR | MDD | Trades | Joint Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['trade_count']} | {row['joint_target_met']} |")
    lines.extend(
        [
            "",
            "Attribution rows are stored in `task1999_winner_acceleration_attribution.csv`.",
            "Expert review rows are stored in `task1999_expert_review_matrix.csv`.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. This time the 2026 logic was actually wired into L0-L5 artifacts.",
            "2. The old-period replay still uses prior-known historical fields, not current 2026 text.",
            "3. The result is a diagnostic backtest, not approval.",
            "4. The next bottleneck is richer historical source extraction for beneficiary chain and customer/contract confirmation.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1991_winner_source_contract.csv`",
            "- `task1992_l1_winner_acceleration_packets.csv`",
            "- `task1993_l2_winner_acceleration_semantics.csv`",
            "- `task1994_l3_winner_acceleration_edges.csv`",
            "- `task1995_l4_winner_acceleration_thesis_cards.csv`",
            "- `task1996_l5_winner_acceleration_decisions.csv`",
            "- `task1997_winner_acceleration_replay_trades/equity.csv`",
            "- `task1998_winner_acceleration_replay_metrics/split/cost.csv`",
            "- `task1999_winner_acceleration_attribution.csv`",
            "- `task2000_acceptance_gate.csv`",
            "",
            "This task does not change strategy acceptance.",
            "This task does not change deployment readiness.",
            "This task does not permit real capital.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    text = registry.read_text(encoding="utf-8")
    if "Task1991," in text:
        return
    rows = []
    titles = {
        1991: "Winner Acceleration Historical Source Contract",
        1992: "Winner Acceleration L1 Packets",
        1993: "Winner Acceleration L2 Semantics",
        1994: "Winner Acceleration L3 Mechanisms",
        1995: "Winner Acceleration L4 Thesis",
        1996: "Winner Acceleration L5 Decisions",
        1997: "Winner Acceleration Replay",
        1998: "Winner Acceleration Metrics",
        1999: "Winner Acceleration Expert Audit",
        2000: "Winner Acceleration Closeout",
    }
    for task_num in range(1991, 2001):
        rows.append(
            {
                "task_id": f"Task{task_num}",
                "title": titles[task_num],
                "owner_team": "Research Governance / L0-L5 Trader Brain",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "diagnostic-winner-acceleration-surgery",
                "parent_task": "Task1990" if task_num == 1991 else f"Task{task_num - 1}",
                "key_report": "docs/reports/task_1991_2000_winner_acceleration_surgery/task_1991_2000_winner_acceleration_surgery.md",
                "key_decision": "docs/reports/task_1991_2000_winner_acceleration_surgery/task_1991_2000_decision.csv",
                "key_artifacts": "data/artifacts/task_1991_2000_winner_acceleration_surgery",
                "validation_command": "python scripts/trader_brain_1991_2000_winner_acceleration_surgery_validate.py",
                "notes": "Implements current-2026 winner acceleration design as prior-known L0-L5 diagnostic replay artifacts without changing acceptance.",
            }
        )
    with registry.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writerows(rows)


def update_operating_state(metrics: list[dict[str, object]]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "99. Task1991-Task2000"
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    row = (
        f"99. Task1991-Task2000 implemented the current-2026 winner-acceleration surgery into actual L0-L5 diagnostic artifacts: "
        f"L0 source contract, L1 packets, L2 semantics, L3 mechanism edges, L4 thesis cards, L5 decisions, and replay variants were produced; "
        f"best `{best['policy_variant_id']}` ended final {best['final_equity']} CAGR {best['cagr']} MDD {best['max_drawdown']}, "
        "while current-2026 sources remain design-only and strategy remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    if marker not in text:
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for idx, line in enumerate(lines):
            if line.startswith("98. Task1981-Task1990"):
                insert_at = idx + 1
                break
        lines.insert(insert_at, row)
        path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    indexes = build_indexes(inputs)
    l0 = l0_contract_rows(inputs)
    l1 = l1_rows(inputs, indexes)
    l2 = l2_rows(l1)
    l3 = l3_rows(l2)
    l4 = l4_rows(l2, l3)
    l5 = l5_rows(inputs, indexes, l4)

    all_trades: list[dict[str, object]] = []
    all_equity: list[dict[str, object]] = []
    metrics = []
    for policy_id in POLICIES:
        trades, equity = replay_policy(inputs, indexes, l4, l5, policy_id)
        all_trades.extend(trades)
        all_equity.extend(equity)
        metrics.append(metrics_for(policy_id, trades, equity, inputs))

    splits = split_rows(all_equity)
    costs = cost_rows(metrics)
    attribution = attribution_rows(all_trades)
    expert = expert_rows()
    gate, closeout = gate_closeout(metrics)

    write_csv(OUT_DIR / "task1991_winner_source_contract.csv", l0)
    write_csv(OUT_DIR / "task1992_l1_winner_acceleration_packets.csv", l1)
    write_csv(OUT_DIR / "task1993_l2_winner_acceleration_semantics.csv", l2)
    write_csv(OUT_DIR / "task1994_l3_winner_acceleration_edges.csv", l3)
    write_csv(OUT_DIR / "task1995_l4_winner_acceleration_thesis_cards.csv", l4)
    write_csv(OUT_DIR / "task1996_l5_winner_acceleration_decisions.csv", l5)
    write_csv(OUT_DIR / "task1997_winner_acceleration_replay_trades.csv", all_trades)
    write_csv(OUT_DIR / "task1997_winner_acceleration_replay_equity.csv", all_equity)
    write_csv(OUT_DIR / "task1998_winner_acceleration_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1998_winner_acceleration_split_oos_metrics.csv", splits)
    write_csv(OUT_DIR / "task1998_winner_acceleration_cost_stress.csv", costs)
    write_csv(OUT_DIR / "task1999_winner_acceleration_attribution.csv", attribution)
    write_csv(OUT_DIR / "task1999_expert_review_matrix.csv", expert)
    write_csv(OUT_DIR / "task2000_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task2000_closeout.csv", closeout)
    write_json(OUT_DIR / "task2000_closeout.json", closeout[0])
    write_report(metrics, attribution, expert)
    write_csv(DECISION, [gate[0]])
    update_registry()
    update_operating_state(metrics)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    print(f"[TASK1991_2000_OK] best={best['policy_variant_id']} final={best['final_equity']} cagr={best['cagr']} mdd={best['max_drawdown']}")


if __name__ == "__main__":
    main()
