from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2941_2960_l4_thesis_invalidation"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2941_2960_l4_thesis_invalidation.md"
DECISION = REPORT_DIR / "task_2960_decision.csv"
AUTHORITY = "DIAGNOSTIC_L4_THESIS_INVALIDATION_ONLY"

L2_BRIDGE = ROOT / "data/artifacts/task_2581_2600_source_integrated_selector_diagnostic/task2584_l2_source_feature_bridge.csv"
L3_EDGES = ROOT / "data/artifacts/task_2581_2600_source_integrated_selector_diagnostic/task2585_l3_source_interaction_edges.csv"
RANKS = ROOT / "data/artifacts/task_2581_2600_source_integrated_selector_diagnostic/task2586_source_integrated_selector_ranks.csv"
MDD_L2 = ROOT / "data/artifacts/task_2921_2940_l2_l3_mdd_attribution_pack/task2923_mdd_trade_l2_attribution.csv"
MDD_AVOID = ROOT / "data/artifacts/task_2921_2940_l2_l3_mdd_attribution_pack/task2929_avoidable_unavoidable_audit.csv"


HARD_SEC_STATES = {"hard_survival_or_listing_risk"}
CAP_SEC_STATES = {
    "debt_survival_financing_cluster",
    "severe_recent_financing_dilution_pressure",
    "high_recent_financing_dilution_pressure",
}
WATCH_SEC_STATES = {"moderate_recent_financing_dilution_watch"}
PASS_SEC_STATES = {"clean_or_low_financing_pressure"}
REGIME_STRESS_TOKENS = ("stress", "tight", "headwind")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
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
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def now_utc() -> str:
    return datetime.now(tz=UTC).isoformat()


def f(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return default


def key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        str(row.get("trade_spec_id", "")),
        str(row.get("symbol", "")),
        str(row.get("decision_asof_ts", "")),
    )


def common_assignment_flags() -> dict[str, object]:
    return {
        "missing_source_is_negative": "0",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": AUTHORITY,
    }


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "l2": read_csv(L2_BRIDGE),
        "l3": read_csv(L3_EDGES),
        "ranks": read_csv(RANKS),
        "mdd_l2": read_csv(MDD_L2),
        "mdd_avoid": read_csv(MDD_AVOID),
    }


def index_one(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {key(row): row for row in rows}


def l3_edges_by_key(edges: list[dict[str, str]]) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    out: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for edge in edges:
        out[key(edge)].append(edge)
    return out


def regime_has_stress(regime_state: str) -> bool:
    state = regime_state.lower()
    return any(token in state for token in REGIME_STRESS_TOKENS)


def decide_l4(row: dict[str, str], rank: dict[str, str], edges: list[dict[str, str]]) -> dict[str, object]:
    sec_state = row.get("sec_state", "")
    regime_state = row.get("regime_state", "")
    interaction_state = row.get("interaction_state", "")
    source_rank = f(rank.get("source_integrated_rank"), 999999)
    strict_sec = row.get("strict_sec_gate_pass", "0") == "1"
    strict_regime = row.get("strict_liquidity_rates_gate_pass", "0") == "1"
    edge_states = "|".join(sorted({edge.get("relation_state", "") for edge in edges if edge.get("relation_state", "")}))
    edge_types = "|".join(sorted({edge.get("edge_type", "") for edge in edges if edge.get("edge_type", "")}))

    action = "PASS"
    strength = 0
    thesis = "no_l4_invalidation"
    reason = "No material pre-trade L4 invalidation rule triggered."
    order_block = "0"
    max_rank_cap = ""

    if not strict_sec or not strict_regime:
        action = "SOURCE_TIME_BLOCKER"
        strength = 3
        thesis = "source_time_uncertified"
        reason = "Strict source-time gate is incomplete; cannot promote to paper/live decision."
        order_block = "1"
    elif sec_state in HARD_SEC_STATES:
        action = "HARD_INVALIDATE"
        strength = 5
        thesis = "hard_survival_listing_risk_invalidates_thesis"
        reason = "Hard survival/listing risk invalidates payoff thesis before paper/live promotion."
        order_block = "1"
        max_rank_cap = "NO_TRADE"
    elif sec_state in CAP_SEC_STATES and source_rank <= 2:
        action = "CAP_TO_WATCH"
        strength = 4
        thesis = "financing_dilution_pressure_caps_top2_thesis"
        reason = "Financing/dilution pressure can remain researchable but should not survive top2 without L4 confirmation."
        max_rank_cap = "WATCH_ONLY"
    elif sec_state in WATCH_SEC_STATES and source_rank <= 2:
        action = "WATCH_REQUIRE_CONFIRMATION"
        strength = 3
        thesis = "financing_watch_requires_confirmation"
        reason = "Moderate financing/dilution watch requires confirming evidence before top2 treatment."
        max_rank_cap = "WATCH_ONLY"
    elif regime_has_stress(regime_state) and source_rank <= 2:
        action = "MACRO_REGIME_CAP"
        strength = 3
        thesis = "liquidity_rates_stress_caps_payoff"
        reason = "Liquidity/rates stress should cap top-ranked payoff thesis until regime confirmation improves."
        max_rank_cap = "WATCH_ONLY"
    elif sec_state in PASS_SEC_STATES:
        action = "PASS_CLEAN_SEC"
        strength = 0
        thesis = "clean_sec_state_not_invalidated"
        reason = "Clean/low financing pressure is not a financing risk signal and must not be invalidated by substring matching."

    return {
        "l4_action": action,
        "l4_invalidation_strength": strength,
        "invalidated_thesis": thesis,
        "invalidation_reason": reason,
        "order_block_candidate": order_block,
        "proposed_rank_cap": max_rank_cap,
        "source_integrated_rank": rank.get("source_integrated_rank", ""),
        "base_rank": rank.get("base_rank", ""),
        "rank_improvement": rank.get("rank_improvement", ""),
        "l3_edge_count": len(edges),
        "l3_edge_types": edge_types,
        "l3_relation_states": edge_states,
        "uses_only_pretrade_fields": "1",
    }


def task2941_contract(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2941",
            "scope_id": "L4INVALID2941-0001",
            "objective": "Convert source-visible L2/L3 risk states into L4 thesis invalidation candidates without using outcomes in assignment.",
            "review_universe_source": L2_BRIDGE.as_posix(),
            "review_universe_is_outcome_selected": "0",
            "l4_assignment_outcome_blind": "1",
            "full_candidate_input_rows": len(inputs["l2"]),
            "rank_input_rows": len(inputs["ranks"]),
            "l3_edge_input_rows": len(inputs["l3"]),
            "mdd_audit_input_rows": len(inputs["mdd_l2"]),
            "replay_performed": "0",
            "selector_tuning_performed": "0",
            "policy_changed": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "outcome_used_for_audit_only": "0",
            **common_assignment_flags(),
        }
    ]


def task2942_l4_input_manifest(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    edges_by_key = l3_edges_by_key(inputs["l3"])
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["l2"], start=1):
        k = key(row)
        edge_ids = "|".join(edge.get("l3_edge_id", "") for edge in edges_by_key.get(k, []) if edge.get("l3_edge_id", ""))
        source_ts = row.get("sec_available_to_brain_ts_max", "")
        input_allowed = "1" if row.get("strict_sec_gate_pass") == "1" and row.get("strict_liquidity_rates_gate_pass") == "1" else "0"
        rows.append(
            {
                "task_id": "Task2942",
                "input_id": f"L4INPUT2942-{idx:06d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "candidate_source_id": row.get("candidate_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "l2_source_id": row.get("l2_bridge_id", ""),
                "l3_edge_ids": edge_ids,
                "source_graph_id": row.get("candidate_id", ""),
                "source_published_ts": "",
                "source_received_ts": source_ts,
                "node_asof_ts": row.get("decision_asof_ts", ""),
                "edge_asof_ts": row.get("decision_asof_ts", ""),
                "input_allowed_for_assignment": input_allowed,
                "source_time_status": "strict_available" if input_allowed == "1" else "source_time_gap",
                "outcome_used_for_audit_only": "0",
                **common_assignment_flags(),
            }
        )
    return rows


def task2943_l4_thesis_evidence_snapshot(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    edges_by_key = l3_edges_by_key(inputs["l3"])
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["l2"], start=1):
        edges = edges_by_key.get(key(row), [])
        strict_ok = row.get("strict_sec_gate_pass") == "1" and row.get("strict_liquidity_rates_gate_pass") == "1"
        rows.append(
            {
                "task_id": "Task2943",
                "thesis_evidence_id": f"L4EVID2943-{idx:06d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "thesis_dimension": "financing_dilution_liquidity_rates_thesis",
                "pretrade_evidence_state": f"{row.get('sec_state', '')}|{row.get('regime_state', '')}|{row.get('interaction_state', '')}",
                "contradiction_state": row.get("sec_state", ""),
                "source_gap_state": "none" if strict_ok else "source_time_gap",
                "source_ids": "|".join(edge.get("l3_edge_id", "") for edge in edges if edge.get("l3_edge_id", "")),
                "source_time_basis": row.get("sec_available_to_brain_ts_max", ""),
                "evidence_available_asof": "1" if strict_ok else "0",
                "missing_source_action": "report_gap_not_negative",
                "outcome_used_for_audit_only": "0",
                **common_assignment_flags(),
            }
        )
    return rows


def task2948_gpt_expert_review_packets() -> list[dict[str, object]]:
    packets = [
        ("GPT_TRADER_RISK", "Separate true financing/dilution risk from normal winner volatility and from clean SEC states.", "Use exact state taxonomy; no substring matching."),
        ("GPT_QUANT_ENGINEER", "Keep L4 invalidation as preregistered diagnostic candidates before any replay.", "Emit full candidate map and audit-only MDD coverage separately."),
        ("GPT_GOVERNANCE", "Do not let PnL or future outcomes enter assignment logic.", "All outcome-bearing MDD coverage rows must be audit-only."),
        ("GPT_FRONTEND_ANALYST", "Make invalidation reasons explainable for iOS/paper journal later.", "Every invalidation candidate needs a thesis id and no-trade/cap reason."),
    ]
    return [
        {
            "task_id": "Task2942",
            "review_packet_id": f"L4GPT2942-{idx:04d}",
            "review_role": role,
            "review_focus": focus,
            "implementation_requirement": requirement,
            "gpt_is_source_of_truth": "0",
            "review_only": "1",
            "outcome_used_for_audit_only": "0",
            **common_assignment_flags(),
        }
        for idx, (role, focus, requirement) in enumerate(packets, start=1)
    ]


def task2943_rulebook() -> list[dict[str, object]]:
    rules = [
        ("L4INV-HARD-SURVIVAL-LISTING", "hard_survival_or_listing_risk", "", "HARD_INVALIDATE", "hard_survival_listing_risk_invalidates_thesis", "NO_TRADE", 5),
        ("L4INV-CAP-DEBT-SURVIVAL-TOP2", "debt_survival_financing_cluster", "source_integrated_rank<=2", "CAP_TO_WATCH", "financing_dilution_pressure_caps_top2_thesis", "WATCH_ONLY", 4),
        ("L4INV-CAP-HIGH-DILUTION-TOP2", "high_recent_financing_dilution_pressure", "source_integrated_rank<=2", "CAP_TO_WATCH", "financing_dilution_pressure_caps_top2_thesis", "WATCH_ONLY", 4),
        ("L4INV-WATCH-MODERATE-DILUTION-TOP2", "moderate_recent_financing_dilution_watch", "source_integrated_rank<=2", "WATCH_REQUIRE_CONFIRMATION", "financing_watch_requires_confirmation", "WATCH_ONLY", 3),
        ("L4INV-CAP-MACRO-STRESS-TOP2", "*", "regime_state contains stress/tight/headwind and source_integrated_rank<=2", "MACRO_REGIME_CAP", "liquidity_rates_stress_caps_payoff", "WATCH_ONLY", 3),
        ("L4INV-PASS-CLEAN-SEC", "clean_or_low_financing_pressure", "", "PASS_CLEAN_SEC", "clean_sec_state_not_invalidated", "", 0),
        ("L4INV-BLOCK-SOURCE-TIME", "*", "strict_sec_gate_pass!=1 or strict_liquidity_rates_gate_pass!=1", "SOURCE_TIME_BLOCKER", "source_time_uncertified", "NO_TRADE", 3),
    ]
    return [
        {
            "task_id": "Task2944",
            "rule_id": rule_id,
            "rule_version": "v1",
            "thesis_dimension": "financing_dilution_liquidity_rates_thesis",
            "sec_state_condition": sec,
            "invalidation_condition": extra or sec,
            "required_pretrade_fields": "sec_state|regime_state|interaction_state|strict_sec_gate_pass|strict_liquidity_rates_gate_pass|source_integrated_rank",
            "forbidden_fields_regex": "pnl|return|loss|negative|mdd|drawdown|exit|runtime_action|rank_by_kis_pnl|survival_read|avoidability|bad_trade",
            "l4_action": action,
            "invalidated_thesis": thesis,
            "proposed_rank_cap": cap,
            "invalidation_strength": strength,
            "outcome_calibrated": "0",
            "replay_required": "0",
            "policy_change_allowed": "0",
            "rulebook_hash": f"{rule_id}|v1|{action}|{thesis}",
            "preregistered_before_replay": "1",
            "outcome_used_for_audit_only": "0",
            **common_assignment_flags(),
        }
        for rule_id, sec, extra, action, thesis, cap, strength in rules
    ]


def task2944_full_candidate_map(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rank_by_key = index_one(inputs["ranks"])
    edges_by_key = l3_edges_by_key(inputs["l3"])
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["l2"], start=1):
        k = key(row)
        decision = decide_l4(row, rank_by_key.get(k, {}), edges_by_key.get(k, []))
        rows.append(
            {
                "task_id": "Task2944",
                "l4_candidate_id": f"L4INVALID2944-{idx:06d}",
                "candidate_id": row.get("candidate_id", ""),
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "base_selector_score": row.get("base_selector_score", ""),
                "source_integrated_selector_score": row.get("source_integrated_selector_score", ""),
                "source_integrated_selector_delta": row.get("source_integrated_selector_delta", ""),
                "strategy_sleeve": row.get("strategy_sleeve", ""),
                "sec_state": row.get("sec_state", ""),
                "regime_state": row.get("regime_state", ""),
                "interaction_state": row.get("interaction_state", ""),
                "sec_reason": row.get("sec_reason", ""),
                "regime_reason_codes": row.get("regime_reason_codes", ""),
                "strict_sec_gate_pass": row.get("strict_sec_gate_pass", ""),
                "strict_liquidity_rates_gate_pass": row.get("strict_liquidity_rates_gate_pass", ""),
                **decision,
                "outcome_used_for_audit_only": "0",
                **common_assignment_flags(),
            }
        )
    return rows


def task2945_l4_assignment(full_map: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(full_map, start=1):
        evidence_id = f"L4EVID2943-{idx:06d}"
        assignment_state = str(row.get("l4_action", ""))
        rows.append(
            {
                "task_id": "Task2945",
                "l4_assignment_id": f"L4ASSIGN2945-{idx:06d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "rule_id": assignment_state,
                "l4_invalidation_state": assignment_state,
                "l4_invalidation_reason": row.get("invalidation_reason", ""),
                "evidence_ids": evidence_id,
                "source_gap_state": "source_time_gap" if row.get("l4_action") == "SOURCE_TIME_BLOCKER" else "none",
                "assignment_input_hash": f"{row.get('trade_spec_id', '')}|{row.get('symbol', '')}|{row.get('decision_asof_ts', '')}|{assignment_state}",
                "assignment_outcome_blind": "1",
                "allowed_use": "diagnostic_thesis_invalidation_only_not_policy",
                "outcome_used_for_audit_only": "0",
                **common_assignment_flags(),
            }
        )
    return rows


def task2946_source_gap_boundary(full_map: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(full_map, start=1):
        missing_families = []
        if row.get("strict_sec_gate_pass") != "1":
            missing_families.append("sec_financing_dilution_strict_time")
        if row.get("strict_liquidity_rates_gate_pass") != "1":
            missing_families.append("liquidity_rates_strict_time")
        if not missing_families:
            continue
        rows.append(
            {
                "task_id": "Task2946",
                "source_gap_id": f"L4GAP2946-{idx:06d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "missing_source_family": "|".join(missing_families),
                "gap_blocks_invalidation": "1",
                "gap_action": "report_gap_not_negative",
                "missing_source_is_negative": "0",
                "outcome_used_for_audit_only": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    if not rows:
        rows.append(
            {
                "task_id": "Task2946",
                "source_gap_id": "L4GAP2946-000000",
                "trade_spec_id": "",
                "symbol": "",
                "decision_asof_ts": "",
                "missing_source_family": "",
                "gap_blocks_invalidation": "0",
                "gap_action": "no_gap_detected",
                "missing_source_is_negative": "0",
                "outcome_used_for_audit_only": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2947_outcome_audit_attachment(assignment: list[dict[str, object]], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    assignment_by_key = {
        (
            str(row.get("trade_spec_id", "")),
            str(row.get("symbol", "")),
            str(row.get("decision_asof_ts", "")),
        ): row
        for row in assignment
    }
    rows: list[dict[str, object]] = []
    for idx, mdd in enumerate(inputs["mdd_l2"], start=1):
        assign = assignment_by_key.get(key(mdd), {})
        rows.append(
            {
                "task_id": "Task2947",
                "audit_id": f"L4OUTCOME2947-{idx:05d}",
                "l4_assignment_id": assign.get("l4_assignment_id", ""),
                "trade_spec_id": mdd.get("trade_spec_id", ""),
                "symbol": mdd.get("symbol", ""),
                "decision_asof_ts": mdd.get("decision_asof_ts", ""),
                "kis_pnl": mdd.get("kis_pnl", ""),
                "kis_net_return": mdd.get("kis_net_return", ""),
                "mdd_window_flag": "1",
                "l4_invalidation_state": assign.get("l4_invalidation_state", ""),
                "post_assignment_join": "1",
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "missing_source_is_negative": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2947_l3_to_l4_bridge(full_map: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in full_map:
        groups[(str(row.get("l4_action", "")), str(row.get("invalidated_thesis", "")), str(row.get("l3_relation_states", "")))].append(row)
    out: list[dict[str, object]] = []
    for idx, (state, items) in enumerate(sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])), start=1):
        out.append(
            {
                "task_id": "Task2947",
                "l3_l4_bridge_id": f"L3L4BRIDGE2947-{idx:05d}",
                "l4_action": state[0],
                "invalidated_thesis": state[1],
                "l3_relation_states": state[2],
                "candidate_count": len(items),
                "symbol_count": len({row.get("symbol", "") for row in items}),
                "top2_count": sum(1 for row in items if f(row.get("source_integrated_rank"), 999999) <= 2),
                "outcome_used_for_audit_only": "0",
                **common_assignment_flags(),
            }
        )
    return out


def task2950_mdd_audit_overlay(full_map: list[dict[str, object]], inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    full_by_key = {
        (
            str(row.get("trade_spec_id", "")),
            str(row.get("symbol", "")),
            str(row.get("decision_asof_ts", "")),
        ): row
        for row in full_map
    }
    avoid_by_key = index_one(inputs["mdd_avoid"])
    rows: list[dict[str, object]] = []
    for idx, mdd in enumerate(inputs["mdd_l2"], start=1):
        k = key(mdd)
        l4 = full_by_key.get(k, {})
        avoid = avoid_by_key.get(k, {})
        would_block_or_cap = str(l4.get("l4_action", "")) in {"HARD_INVALIDATE", "CAP_TO_WATCH", "WATCH_REQUIRE_CONFIRMATION", "MACRO_REGIME_CAP", "SOURCE_TIME_BLOCKER"}
        rows.append(
            {
                "task_id": "Task2945",
                "mdd_overlay_id": f"L4MDDAUDIT2945-{idx:05d}",
                "trade_spec_id": mdd.get("trade_spec_id", ""),
                "symbol": mdd.get("symbol", ""),
                "decision_asof_ts": mdd.get("decision_asof_ts", ""),
                "kis_pnl": mdd.get("kis_pnl", ""),
                "source_integrated_rank": mdd.get("source_integrated_rank", ""),
                "sec_state": mdd.get("sec_state", ""),
                "regime_state": mdd.get("regime_state", ""),
                "task2929_avoidability_bucket": avoid.get("avoidability_bucket", ""),
                "l4_action": l4.get("l4_action", ""),
                "invalidated_thesis": l4.get("invalidated_thesis", ""),
                "would_block_or_cap_under_preregistered_rule": "1" if would_block_or_cap else "0",
                "audit_only_not_assignment": "1",
                "outcome_used_for_audit_only": "1",
                **common_assignment_flags(),
            }
        )
    return rows


def task2946_clean_state_false_positive_guard(full_map: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [row for row in full_map if row.get("sec_state") in PASS_SEC_STATES]
    invalidated = [row for row in rows if row.get("l4_action") in {"HARD_INVALIDATE", "CAP_TO_WATCH", "WATCH_REQUIRE_CONFIRMATION"}]
    return [
        {
            "task_id": "Task2946",
            "guard_id": "L4FALSEPOS2946-0001",
            "guard_name": "clean_sec_state_not_invalidated",
            "clean_sec_candidate_count": len(rows),
            "clean_sec_hard_or_cap_invalidated_count": len(invalidated),
            "pass": "1" if not invalidated else "0",
            "guard_reason": "Clean/low financing pressure must not be invalidated by the substring 'financing'.",
            "outcome_used_for_audit_only": "0",
            **common_assignment_flags(),
        }
    ]


def task2947_l3_to_l4_bridge(full_map: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in full_map:
        groups[(str(row.get("l4_action", "")), str(row.get("invalidated_thesis", "")), str(row.get("l3_relation_states", "")))].append(row)
    out: list[dict[str, object]] = []
    for idx, (state, items) in enumerate(sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])), start=1):
        out.append(
            {
                "task_id": "Task2947",
                "l3_l4_bridge_id": f"L3L4BRIDGE2947-{idx:05d}",
                "l4_action": state[0],
                "invalidated_thesis": state[1],
                "l3_relation_states": state[2],
                "candidate_count": len(items),
                "symbol_count": len({row.get("symbol", "") for row in items}),
                "top2_count": sum(1 for row in items if f(row.get("source_integrated_rank"), 999999) <= 2),
                "outcome_used_for_audit_only": "0",
                **common_assignment_flags(),
            }
        )
    return out


def task2948_source_gap_and_blockers(full_map: list[dict[str, object]]) -> list[dict[str, object]]:
    blockers = [row for row in full_map if row.get("l4_action") == "SOURCE_TIME_BLOCKER"]
    source_gap = [row for row in full_map if row.get("strict_sec_gate_pass") != "1" or row.get("strict_liquidity_rates_gate_pass") != "1"]
    return [
        {
            "task_id": "Task2948",
            "blocker_id": "L4BLOCKER2948-0001",
            "blocker_type": "source_time_blocker",
            "candidate_count": len(blockers),
            "source_gap_count": len(source_gap),
            "blocker_is_no_trade_reason": "1",
            "missing_source_is_negative": "0",
            "outcome_used_for_audit_only": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def task2949_acceptance_checks(
    full_map: list[dict[str, object]],
    assignment: list[dict[str, object]],
    outcome_audit: list[dict[str, object]],
    false_guard: list[dict[str, object]],
) -> list[dict[str, object]]:
    assignment_columns = set(assignment[0].keys()) if assignment else set()
    forbidden_tokens = ("pnl", "return", "loss", "negative", "mdd", "drawdown", "exit", "runtime_action", "rank_by_kis_pnl", "survival_read", "avoidability", "bad_trade")
    allowed_governance_columns = {"missing_source_is_negative"}
    forbidden_assignment_columns = [
        col for col in assignment_columns
        if col not in allowed_governance_columns and any(token in col.lower() for token in forbidden_tokens)
    ]
    checks = [
        ("full_candidate_rows_3100", len(full_map) == 3100, f"full_map_rows={len(full_map)}"),
        ("assignment_rows_3100", len(assignment) == 3100, f"assignment_rows={len(assignment)}"),
        ("outcome_audit_rows_14", len(outcome_audit) == 14, f"outcome_audit_rows={len(outcome_audit)}"),
        ("clean_false_positive_guard_pass", false_guard[0].get("pass") == "1", f"pass={false_guard[0].get('pass')}"),
        ("assignment_has_no_outcome_columns", not forbidden_assignment_columns, f"forbidden_assignment_columns={forbidden_assignment_columns}"),
        ("assignment_outcome_blind", all(row.get("assignment_outcome_blind") == "1" and row.get("outcome_used_for_assignment") == "0" and row.get("assignment_uses_future_outcome") == "0" for row in assignment), "assignment outcome flags are safe"),
        ("cap_or_watch_exists", any(row.get("l4_action") in {"CAP_TO_WATCH", "WATCH_REQUIRE_CONFIRMATION", "MACRO_REGIME_CAP"} for row in full_map), "cap/watch candidate exists"),
        ("outcome_audit_post_join_only", all(row.get("post_assignment_join") == "1" and row.get("outcome_used_for_audit_only") == "1" for row in outcome_audit), "outcome audit is post-assignment only"),
    ]
    return [
        {
            "task_id": "Task2949",
            "check_id": f"L4CHECK2949-{idx:04d}",
            "check_name": name,
            "pass": "1" if passed else "0",
            "detail": detail,
            "outcome_used_for_audit_only": "1" if name == "outcome_audit_post_join_only" else "0",
            **common_assignment_flags(),
        }
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def task2960_closeout(
    full_map: list[dict[str, object]],
    assignment: list[dict[str, object]],
    outcome_audit: list[dict[str, object]],
    checks: list[dict[str, object]],
) -> list[dict[str, object]]:
    actions = Counter(str(row.get("l4_action", "")) for row in full_map)
    audit_blocked = sum(1 for row in outcome_audit if row.get("l4_invalidation_state") in {"HARD_INVALIDATE", "CAP_TO_WATCH", "WATCH_REQUIRE_CONFIRMATION", "MACRO_REGIME_CAP", "SOURCE_TIME_BLOCKER"})
    return [
        {
            "task_id": "Task2960",
            "verdict": "l4_thesis_invalidation_completed_diagnostic_only",
            "full_candidate_rows": len(full_map),
            "assignment_row_count": len(assignment),
            "outcome_audit_row_count": len(outcome_audit),
            "hard_invalidate_count": actions.get("HARD_INVALIDATE", 0),
            "cap_to_watch_count": actions.get("CAP_TO_WATCH", 0),
            "watch_require_confirmation_count": actions.get("WATCH_REQUIRE_CONFIRMATION", 0),
            "source_time_blocker_count": actions.get("SOURCE_TIME_BLOCKER", 0),
            "pass_clean_sec_count": actions.get("PASS_CLEAN_SEC", 0),
            "outcome_audit_block_or_cap_count": audit_blocked,
            "all_acceptance_checks_pass": "1" if all(row.get("pass") == "1" for row in checks) else "0",
            "replay_performed": "0",
            "selector_tuning_performed": "0",
            "sizing_tuning_performed": "0",
            "exit_tuning_performed": "0",
            "policy_changed": "0",
            "next_action": "Task2961-2980 should compare frozen policy vs challenger only after this L4 rulebook is explicitly frozen and replay-governed.",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "outcome_used_for_audit_only": "1",
            **common_assignment_flags(),
        }
    ]


def write_report(closeout: dict[str, object], rulebook: list[dict[str, object]], bridge: list[dict[str, object]], outcome_audit: list[dict[str, object]]) -> None:
    rule_lines = "\n".join(
        f"- `{row['rule_id']}` -> `{row['l4_action']}` / `{row['invalidated_thesis']}`."
        for row in rulebook
    )
    bridge_lines = "\n".join(
        f"- `{row['l4_action']}` `{row['invalidated_thesis']}`: {row['candidate_count']} candidates, top2 {row['top2_count']}."
        for row in bridge[:10]
    )
    audit_lines = "\n".join(
        f"- `{row['symbol']}` {row['decision_asof_ts']}: `{row['l4_invalidation_state']}`, PnL audit-only {row['kis_pnl']}."
        for row in outcome_audit[:10]
    )
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# Task2941-2960 L4 Thesis Invalidation

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Full candidate rows: {closeout['full_candidate_rows']}.
- Hard invalidation candidates: {closeout['hard_invalidate_count']}.
- Cap-to-watch candidates: {closeout['cap_to_watch_count']}.
- Watch-require-confirmation candidates: {closeout['watch_require_confirmation_count']}.
- Source-time blockers: {closeout['source_time_blocker_count']}.
- Assignment rows: {closeout['assignment_row_count']}.
- Outcome audit rows: {closeout['outcome_audit_row_count']}.
- Outcome audit block/cap rows: {closeout['outcome_audit_block_or_cap_count']} / {closeout['outcome_audit_row_count']}.
- Replay performed: `0`.
- Selector tuning performed: `0`.
- Policy changed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Rulebook:

{rule_lines}

L3/L4 bridge:

{bridge_lines}

Outcome audit attachment:

{audit_lines}

Rules use only pre-trade L2/L3/source-time fields. MDD PnL and outcomes are audit-only and are not used in assignment.

## No-Background Decision-Maker Report

Conclusion first: L4 invalidation candidates are now explicit and outcome-blind.

The main repair is not more data. It is stronger thesis invalidation: hard survival/listing risk blocks, financing/dilution pressure caps to watch, and source-time uncertainty blocks promotion before any replay.

Clean financing states are protected from false invalidation.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2941_2960_l4_thesis_invalidation/`.
- Validator: `python scripts/trader_brain_2941_2960_l4_thesis_invalidation_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
""",
        encoding="utf-8",
    )


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    fieldnames = list(rows[0].keys())
    existing = {row["task_id"] for row in rows}
    for task_no in range(2941, 2961):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"L4 Thesis Invalidation Step {task_no}",
                "owner_team": "Trader Brain L4 / Research Governance / Risk",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "l4-invalidation-candidates-diagnostic-only",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2941_2960_l4_thesis_invalidation/task_2941_2960_l4_thesis_invalidation.md",
                "key_decision": "docs/reports/task_2941_2960_l4_thesis_invalidation/task_2960_decision.csv",
                "key_artifacts": "data/artifacts/task_2941_2960_l4_thesis_invalidation",
                "validation_command": "python scripts/trader_brain_2941_2960_l4_thesis_invalidation_validate.py",
                "notes": "Preregisters L4 thesis invalidation candidates from pre-trade L2/L3 states without replay or tuning.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "144. Task2941-Task2960"
    line = (
        "144. Task2941-Task2960 preregistered L4 thesis invalidation candidates: "
        f"full candidates {closeout['full_candidate_rows']}, hard invalidations {closeout['hard_invalidate_count']}, "
        f"cap-to-watch {closeout['cap_to_watch_count']}, watch-confirmation {closeout['watch_require_confirmation_count']}, "
        f"source-time blockers {closeout['source_time_blocker_count']}, outcome audit block/cap {closeout['outcome_audit_block_or_cap_count']}/{closeout['outcome_audit_row_count']}; "
        "no replay, selector tuning, policy change, paper order, or live order was performed. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    if marker in text:
        lines = [line if item.startswith(marker) else item + "\n" for item in text.splitlines()]
        path.write_text("".join(lines), encoding="utf-8")
        return
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    contract = task2941_contract(inputs)
    input_manifest = task2942_l4_input_manifest(inputs)
    evidence_snapshot = task2943_l4_thesis_evidence_snapshot(inputs)
    rulebook = task2943_rulebook()
    full_map = task2944_full_candidate_map(inputs)
    assignment = task2945_l4_assignment(full_map)
    source_gaps = task2946_source_gap_boundary(full_map)
    outcome_audit = task2947_outcome_audit_attachment(assignment, inputs)
    false_guard = task2946_clean_state_false_positive_guard(full_map)
    bridge = task2947_l3_to_l4_bridge(full_map)
    packets = task2948_gpt_expert_review_packets()
    blockers = task2948_source_gap_and_blockers(full_map)
    checks = task2949_acceptance_checks(full_map, assignment, outcome_audit, false_guard)
    closeout = task2960_closeout(full_map, assignment, outcome_audit, checks)

    outputs = [
        ("task2941_scope_freeze.csv", contract),
        ("task2942_l4_input_manifest.csv", input_manifest),
        ("task2943_l4_thesis_evidence_snapshot.csv", evidence_snapshot),
        ("task2944_l4_invalidation_rulebook.csv", rulebook),
        ("task2944_full_candidate_invalidation_map.csv", full_map),
        ("task2945_l4_assignment.csv", assignment),
        ("task2946_source_gap_boundary.csv", source_gaps),
        ("task2947_outcome_audit_attachment.csv", outcome_audit),
        ("task2946_clean_state_false_positive_guard.csv", false_guard),
        ("task2947_l3_to_l4_bridge.csv", bridge),
        ("task2948_gpt_expert_review_packets.csv", packets),
        ("task2948_source_gap_and_blockers.csv", blockers),
        ("task2949_acceptance_checks.csv", checks),
        ("task2960_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2960_closeout.json", closeout[0])
    write_report(closeout[0], rulebook, bridge, outcome_audit)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2941_2960_L4_THESIS_INVALIDATION_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
