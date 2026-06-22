from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2201_2230_latest_brain_full_universe_replay"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2201_2230_latest_brain_full_universe_replay.md"
DECISION = REPORT_DIR / "task_2201_2230_decision.csv"

TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1318 = ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors"
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
TASK1508 = ROOT / "data/artifacts/task_1508_1517_bottleneck_verification"
TASK1518 = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
TASK1698 = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
TASK2151 = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
TASK2191 = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"

AUTHORITY = "DIAGNOSTIC_LATEST_BRAIN_FULL_UNIVERSE_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_FINAL = 1847.0265
QQQ_CAGR = 0.126318
POLICIES = [
    ("latest_brain_full_top3_v1", 3, False),
    ("latest_brain_full_top5_v1", 5, False),
    ("latest_brain_full_top10_v1", 10, False),
    ("latest_brain_full_top3_dd_guard_v1", 3, True),
    ("latest_brain_full_top5_dd_guard_v1", 5, True),
]


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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "None", "nan"}:
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def parse_dt(value: object) -> datetime | None:
    if value in {"", None}:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def parse_date(value: object) -> date | None:
    dt = parse_dt(value)
    return dt.date() if dt else None


def key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("candidate_source_id", ""),
        row.get("trade_spec_id", ""),
        row.get("symbol", ""),
        row.get("decision_asof_ts", ""),
    )


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "specs": read_csv(TASK1201 / "task1203_l5_trade_specs.csv"),
        "readiness": read_csv(TASK1318 / "task1327_full_candidate_readiness_panel.csv"),
        "rank": read_csv(TASK1488 / "task1494_payoff_ranker_v6.csv"),
        "returns": read_csv(TASK1508 / "task1509_candidate_scheduled_return_panel.csv"),
        "l5_state": read_csv(TASK1518 / "task1520_thesis_state_machine.csv"),
        "collapse": read_csv(TASK1698 / "task1699_collapse_risk_v2_panel.csv"),
        "payoff": read_csv(TASK1698 / "task1700_payoff_quality_v2_panel.csv"),
        "api_cards": read_csv(TASK2151 / "task2171_l4_api_score_cards_hardened.csv"),
        "api_decisions": read_csv(TASK2151 / "task2172_l5_api_decisions_hardened.csv"),
    }


def freeze_contract(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    components = [
        ("canonical_candidate_pool", TASK1488 / "task1494_payoff_ranker_v6.csv", "full_candidate_selection_base", "required_full_3100"),
        ("base_trade_spec", TASK1201 / "task1203_l5_trade_specs.csv", "entry_exit_skeleton", "required_full_3100"),
        ("source_readiness", TASK1318 / "task1327_full_candidate_readiness_panel.csv", "source_family_coverage", "required_full_3100"),
        ("scheduled_return_audit", TASK1508 / "task1509_candidate_scheduled_return_panel.csv", "pnl_audit_only", "required_full_3100"),
        ("l5_thesis_state", TASK1518 / "task1520_thesis_state_machine.csv", "latest_l5_entry_cap_state", "required_full_3100"),
        ("collapse_risk", TASK1698 / "task1699_collapse_risk_v2_panel.csv", "bad_trade_risk_guard", "required_full_3100"),
        ("payoff_quality", TASK1698 / "task1700_payoff_quality_v2_panel.csv", "payoff_quality_rank_guard", "required_full_3100"),
        ("api_hardened_l4", TASK2151 / "task2171_l4_api_score_cards_hardened.csv", "partial_api_overlay_neutral_when_missing", "partial_377_only"),
        ("api_hardened_l5", TASK2151 / "task2172_l5_api_decisions_hardened.csv", "partial_api_budget_neutral_when_missing", "partial_377_only"),
        ("drawdown_guard", TASK2191 / "task2196_guard_replay_metrics.csv", "prior_state_guard_reference_only", "selected_116_reference_only"),
    ]
    rows: list[dict[str, object]] = []
    for idx, (name, path, role, scope) in enumerate(components, start=1):
        rows.append(
            {
                "task_id": "Task2201",
                "brain_contract_component_id": f"LATESTBRAIN2201-{idx:03d}",
                "brain_version_id": "latest_brain_full_universe_v1",
                "component_name": name,
                "component_role": role,
                "scope_state": scope,
                "input_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "input_rows": len(inputs.get({"canonical_candidate_pool": "rank", "base_trade_spec": "specs", "source_readiness": "readiness", "scheduled_return_audit": "returns", "l5_thesis_state": "l5_state", "collapse_risk": "collapse", "payoff_quality": "payoff", "api_hardened_l4": "api_cards", "api_hardened_l5": "api_decisions"}.get(name, ""), [])),
                "sha256": file_hash(path),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def source_family_rows(inputs: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    readiness = inputs["readiness"]
    api_keys = {key(row) for row in inputs["api_cards"]}
    total = len(readiness)
    families = [
        ("sec_candidate_filings", "has_candidate_filings"),
        ("sec_survival", "has_sec_survival"),
        ("ir_ceo_exhibit", "has_ir_ceo_exhibit"),
        ("contract_exhibit", "has_contract_exhibit"),
        ("price_gate", "has_price_gate"),
        ("analyst_pit", "has_analyst_pit"),
    ]
    rows: list[dict[str, object]] = []
    gaps: list[dict[str, object]] = []
    for idx, (family, field) in enumerate(families, start=1):
        covered = sum(1 for row in readiness if row.get(field) == "1")
        rows.append(
            {
                "task_id": "Task2203",
                "source_family_id": f"SOURCEFAMILY2203-{idx:03d}",
                "source_family": family,
                "candidate_rows": total,
                "exact_covered_rows": covered,
                "missing_rows": total - covered,
                "coverage_ratio": round(covered / total, 6) if total else 0.0,
                "assignment_policy": "covered_positive_only_missing_neutral",
                "needs_repeat_acquisition_skill": "1" if covered < total else "0",
                "authority": AUTHORITY,
            }
        )
        if covered < total:
            gaps.append(
                {
                    "task_id": "Task2212",
                    "gap_id": f"SOURCEGAP2212-{len(gaps)+1:04d}",
                    "source_family": family,
                    "candidate_rows_missing": total - covered,
                    "gap_policy": "reported_not_approximated_missing_neutral",
                    "blocks_deployment": "1",
                    "blocks_diagnostic_replay": "0",
                    "authority": AUTHORITY,
                }
            )
    covered_api = sum(1 for row in readiness if key(row) in api_keys)
    rows.append(
        {
            "task_id": "Task2203",
            "source_family_id": "SOURCEFAMILY2203-007",
            "source_family": "api_hardened_overlay",
            "candidate_rows": total,
            "exact_covered_rows": covered_api,
            "missing_rows": total - covered_api,
            "coverage_ratio": round(covered_api / total, 6) if total else 0.0,
            "assignment_policy": "exact_api_rows_only_missing_neutral_no_penalty",
            "needs_repeat_acquisition_skill": "1",
            "authority": AUTHORITY,
        }
    )
    gaps.append(
        {
            "task_id": "Task2212",
            "gap_id": f"SOURCEGAP2212-{len(gaps)+1:04d}",
            "source_family": "api_hardened_overlay",
            "candidate_rows_missing": total - covered_api,
            "gap_policy": "partial_377_selected_trade_overlay_cannot_be_called_full_universe",
            "blocks_deployment": "1",
            "blocks_diagnostic_replay": "0",
            "authority": AUTHORITY,
        }
    )
    return rows, gaps


def feature_score(row: dict[str, object]) -> tuple[float, str]:
    score = to_float(row.get("semantic_v6_rank_score"))
    score += 0.45 * to_float(row.get("payoff_quality_score"))
    score -= 0.9 * to_float(row.get("collapse_risk_score"))
    state = str(row.get("thesis_state", ""))
    entry_gate = str(row.get("entry_gate_state", ""))
    payoff_bucket = str(row.get("payoff_quality_bucket", ""))
    collapse_bucket = str(row.get("collapse_risk_bucket", ""))
    if state == "active_thesis":
        score += 18.0
    elif state == "confirmation_wait":
        score += 8.0
    elif state == "source_gap_watch":
        score -= 12.0
    elif state == "invalidated":
        score -= 80.0
    if entry_gate == "entry_allowed":
        score += 8.0
    elif entry_gate == "entry_allowed_cap_only":
        score -= 5.0
    elif entry_gate == "entry_watch_only":
        score -= 30.0
    elif entry_gate == "entry_block":
        score -= 100.0
    if payoff_bucket == "top3_payoff_candidate":
        score += 20.0
    elif payoff_bucket == "eligible_payoff_candidate":
        score += 10.0
    elif payoff_bucket == "watch_or_cap_candidate":
        score -= 10.0
    elif payoff_bucket == "low_payoff_candidate":
        score -= 22.0
    elif payoff_bucket == "blocked_terminal_or_listing_risk":
        score -= 80.0
    if collapse_bucket == "terminal_business_risk":
        score -= 70.0
    elif collapse_bucket == "dilution_pressure":
        score -= 35.0
    elif collapse_bucket == "ordinary_volatility":
        score -= 8.0
    elif collapse_bucket == "theme_volatility":
        score += 3.0
    source_bonus = 0.0
    for field, bonus in [
        ("has_candidate_filings", 1.0),
        ("has_sec_survival", 1.0),
        ("has_ir_ceo_exhibit", 2.0),
        ("has_contract_exhibit", 2.0),
        ("has_price_gate", 4.0),
    ]:
        if row.get(field) == "1":
            source_bonus += bonus
    score += source_bonus
    api_state = str(row.get("api_l2_state", "api_not_acquired_full_universe_neutral"))
    if api_state in {"api_event_context_supportive", "api_two_family_expectation_support"}:
        score += 4.0 + 0.25 * to_float(row.get("api_l2_score"))
    elif api_state in {"api_financing_or_dilution_risk", "api_expectation_weakening_risk", "api_risk_context_cap_required"}:
        score -= 10.0
    return round(score, 6), "pre_outcome_l0_l5_score"


def cap_multiplier(row: dict[str, object]) -> tuple[float, str]:
    cap = to_float(row.get("position_size_cap_multiplier"), 0.0)
    action = "l5_cap"
    if row.get("pre_entry_gate") == "cap":
        cap = min(cap if cap else 0.5, 0.65)
        action = "risk_gate_cap"
    if row.get("strict_gate_status", "") == "STRICT_TRANSCRIPT_AND_ANALYST_GATES_REMAIN_BLOCKED":
        api_mult = to_float(row.get("api_l5_budget_multiplier"), 1.0)
        cap = min(max(cap, 0.0), max(api_mult, 0.0))
        action = "strict_api_gate_neutral_or_cap"
    return round(max(0.0, min(1.25, cap)), 6), action


def build_feature_panel(inputs: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    maps = {name: {key(row): row for row in rows} for name, rows in inputs.items() if name != "api_decisions"}
    api_decisions = {key(row): row for row in inputs["api_decisions"]}
    join_audit: list[dict[str, object]] = []
    features: list[dict[str, object]] = []
    for idx, rank_row in enumerate(inputs["rank"], start=1):
        k = key(rank_row)
        merged: dict[str, object] = dict(rank_row)
        join_status = {}
        for name in ["specs", "readiness", "returns", "l5_state", "collapse", "payoff"]:
            match = maps[name].get(k)
            join_status[name] = "exact_key_match" if match else "missing_exact_key"
            if match:
                merged.update(match)
        api_card = maps["api_cards"].get(k)
        api_decision = api_decisions.get(k)
        join_status["api_cards"] = "exact_key_match" if api_card else "missing_neutral"
        join_status["api_decisions"] = "exact_key_match" if api_decision else "missing_neutral"
        if api_card:
            merged.update(api_card)
        else:
            merged.update(
                {
                    "api_l2_state": "api_not_acquired_full_universe_neutral",
                    "api_l2_score": "0.0",
                    "api_raw_overlay_score": "0.0",
                    "api_adjusted_rank_score": "",
                    "strict_gate_status": "API_NOT_ACQUIRED_FULL_UNIVERSE_NEUTRAL",
                }
            )
        if api_decision:
            merged.update(api_decision)
        else:
            merged.update({"api_l5_action": "neutral_missing_api_not_negative", "api_l5_budget_multiplier": "1.0"})
        score, score_basis = feature_score(merged)
        cap, cap_action = cap_multiplier(merged)
        return_ok = merged.get("return_state", "") in {"return_available", "available", "price_return_available", ""}
        entry_gate = str(merged.get("entry_gate_state", ""))
        pre_gate = str(merged.get("pre_entry_gate", ""))
        selection_allowed = (
            entry_gate in {"entry_allowed", "entry_allowed_cap_only"}
            and pre_gate in {"allow", "cap"}
            and cap > 0.0
            and return_ok
        )
        features.append(
            {
                "task_id": "Task2205",
                "feature_row_id": f"LATESTFULLFEAT2205-{idx:07d}",
                "candidate_source_id": rank_row["candidate_source_id"],
                "trade_spec_id": rank_row["trade_spec_id"],
                "symbol": rank_row["symbol"],
                "decision_asof_ts": rank_row["decision_asof_ts"],
                "candidate_rank": rank_row.get("candidate_rank", ""),
                "derived_theme": rank_row.get("derived_theme", ""),
                "event_family": merged.get("event_family", ""),
                "expectation_v6_state": merged.get("expectation_v6_state", merged.get("expectation_state", "")),
                "absorption_v6_state": merged.get("absorption_v6_state", merged.get("absorption_state", "")),
                "materiality_v6_state": merged.get("materiality_v6_state", merged.get("materiality_state", "")),
                "semantic_v6_rank_score": merged.get("semantic_v6_rank_score", ""),
                "payoff_quality_score": merged.get("payoff_quality_score", ""),
                "payoff_quality_bucket": merged.get("payoff_quality_bucket", ""),
                "collapse_risk_score": merged.get("collapse_risk_score", ""),
                "collapse_risk_bucket": merged.get("collapse_risk_bucket", ""),
                "pre_entry_gate": merged.get("pre_entry_gate", ""),
                "thesis_state": merged.get("thesis_state", ""),
                "entry_gate_state": merged.get("entry_gate_state", ""),
                "l5_position_size_cap_multiplier": merged.get("position_size_cap_multiplier", ""),
                "api_scope_state": "api_exact_overlay_available" if api_card else "api_not_acquired_full_universe_neutral",
                "api_l2_state": merged.get("api_l2_state", ""),
                "api_l2_score": merged.get("api_l2_score", ""),
                "api_l5_action": merged.get("api_l5_action", ""),
                "api_l5_budget_multiplier": merged.get("api_l5_budget_multiplier", ""),
                "strict_gate_status": merged.get("strict_gate_status", ""),
                "position_size_cap_multiplier": cap,
                "position_size_cap_action": cap_action,
                "latest_brain_rank_score": score,
                "score_basis": score_basis,
                "selection_allowed": "1" if selection_allowed else "0",
                "entry_date": merged.get("entry_date", merged.get("entry_after_date", "")),
                "scheduled_exit_date": merged.get("scheduled_exit_date", merged.get("exit_on_or_before_date", "")),
                "scheduled_net_return": merged.get("scheduled_net_return", ""),
                "return_state": merged.get("return_state", ""),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "0",
                "missing_source_policy": "missing_sources_are_neutral_not_negative",
                "authority": AUTHORITY,
            }
        )
        join_audit.append(
            {
                "task_id": "Task2204",
                "join_audit_id": f"JOINAUDIT2204-{idx:07d}",
                "candidate_source_id": rank_row["candidate_source_id"],
                "trade_spec_id": rank_row["trade_spec_id"],
                "symbol": rank_row["symbol"],
                "decision_asof_ts": rank_row["decision_asof_ts"],
                **{f"{name}_join_status": status for name, status in join_status.items()},
                "join_policy": "exact_candidate_source_trade_spec_symbol_decision_asof_only_no_fallback",
                "authority": AUTHORITY,
            }
        )
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in features:
        grouped[str(row["decision_asof_ts"])].append(row)
    rank_rows: list[dict[str, object]] = []
    rank_idx = 1
    for decision_ts in sorted(grouped):
        ranked = sorted(
            grouped[decision_ts],
            key=lambda row: (int(row["selection_allowed"]), to_float(row["latest_brain_rank_score"]), -to_float(row["candidate_rank"], 999999)),
            reverse=True,
        )
        for rank_within, row in enumerate(ranked, start=1):
            rank_rows.append(
                {
                    "task_id": "Task2206",
                    "rank_row_id": f"LATESTFULLRANK2206-{rank_idx:07d}",
                    "candidate_source_id": row["candidate_source_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "latest_brain_rank_score": row["latest_brain_rank_score"],
                    "latest_brain_rank_within_decision": rank_within,
                    "selection_allowed": row["selection_allowed"],
                    "position_size_cap_multiplier": row["position_size_cap_multiplier"],
                    "score_basis": row["score_basis"],
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            row["latest_brain_rank_within_decision"] = rank_within
            rank_idx += 1
    return join_audit, features, rank_rows


def stress_state(current_drawdown: float, previous_period_pnl: float) -> str:
    if current_drawdown <= -0.18:
        return "portfolio_hard_drawdown"
    if current_drawdown <= -0.10:
        return "portfolio_soft_drawdown"
    if previous_period_pnl < 0 and current_drawdown <= -0.005:
        return "early_stress_after_loss"
    return "normal"


def preserve_winner(row: dict[str, object]) -> bool:
    return (
        row.get("payoff_quality_bucket") == "top3_payoff_candidate"
        and to_float(row.get("payoff_quality_score")) >= 75.0
        and to_float(row.get("collapse_risk_score")) <= 18.0
        and row.get("thesis_state") in {"active_thesis", "confirmation_wait"}
    )


def guard_cap(base_cap: float, row: dict[str, object], state: str, use_guard: bool) -> tuple[float, str]:
    if not use_guard or state == "normal":
        return base_cap, "no_drawdown_guard"
    if preserve_winner(row):
        cap = min(base_cap, 1.0 if state == "portfolio_hard_drawdown" else 1.1)
        return cap, "winner_preserved_under_drawdown_guard"
    if row.get("collapse_risk_bucket") in {"terminal_business_risk", "dilution_pressure"}:
        return min(base_cap, 0.35), "risk_bucket_hard_cap"
    if state == "portfolio_hard_drawdown":
        return min(base_cap, 0.50), "portfolio_hard_drawdown_cap"
    if state == "portfolio_soft_drawdown":
        return min(base_cap, 0.70), "portfolio_soft_drawdown_cap"
    return min(base_cap, 0.80), "early_stress_cap"


def run_replay(features: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in features:
        if row["selection_allowed"] == "1":
            by_decision[str(row["decision_asof_ts"])].append(row)
    trades: list[dict[str, object]] = []
    equity_rows: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    trade_idx = 1
    for policy_id, slots, use_guard in POLICIES:
        capital = INITIAL_CAPITAL
        peak = INITIAL_CAPITAL
        previous_period_pnl = 0.0
        for decision_ts in sorted(by_decision):
            drawdown = capital / peak - 1.0 if peak else 0.0
            state = stress_state(drawdown, previous_period_pnl)
            candidates = sorted(
                by_decision[decision_ts],
                key=lambda row: (to_float(row["latest_brain_rank_score"]), -to_float(row["candidate_rank"], 999999)),
                reverse=True,
            )[:slots]
            base_alloc = capital / slots
            period_pnl = 0.0
            allocated_count = 0
            for row in candidates:
                base_cap = to_float(row["position_size_cap_multiplier"], 0.0)
                final_cap, guard_action = guard_cap(base_cap, row, state, use_guard)
                if final_cap <= 0.0:
                    continue
                net_return = to_float(row["scheduled_net_return"], 0.0)
                allocated = base_alloc * final_cap
                pnl = allocated * net_return
                period_pnl += pnl
                allocated_count += 1
                trades.append(
                    {
                        "task_id": "Task2208",
                        "trade_row_id": f"LATESTFULLTRADE2208-{trade_idx:07d}",
                        "policy_variant_id": policy_id,
                        "candidate_source_id": row["candidate_source_id"],
                        "trade_spec_id": row["trade_spec_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "latest_brain_rank_within_decision": row.get("latest_brain_rank_within_decision", ""),
                        "latest_brain_rank_score": row["latest_brain_rank_score"],
                        "thesis_state": row["thesis_state"],
                        "entry_gate_state": row["entry_gate_state"],
                        "payoff_quality_bucket": row["payoff_quality_bucket"],
                        "collapse_risk_bucket": row["collapse_risk_bucket"],
                        "api_scope_state": row["api_scope_state"],
                        "drawdown_guard_state": state,
                        "guard_action": guard_action,
                        "base_slot_allocation": round(base_alloc, 4),
                        "base_position_size_cap_multiplier": base_cap,
                        "final_position_size_cap_multiplier": round(final_cap, 6),
                        "capital_allocated": round(allocated, 4),
                        "entry_date": row["entry_date"],
                        "scheduled_exit_date": row["scheduled_exit_date"],
                        "net_return": row["scheduled_net_return"],
                        "pnl": round(pnl, 4),
                        "assignment_uses_future_outcome": "0",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
                trade_idx += 1
            capital += period_pnl
            peak = max(peak, capital)
            equity_rows.append(
                {
                    "task_id": "Task2209",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "portfolio_drawdown_before_period": round(drawdown, 6),
                    "drawdown_guard_state": state,
                    "candidate_pool_count": len(by_decision[decision_ts]),
                    "selected_count": len(candidates),
                    "allocated_count": allocated_count,
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            previous_period_pnl = period_pnl
        metrics.append(metrics_for(policy_id, [r for r in trades if r["policy_variant_id"] == policy_id], [r for r in equity_rows if r["policy_variant_id"] == policy_id]))
    return trades, equity_rows, metrics


def metrics_for(policy_id: str, trades: list[dict[str, object]], equity: list[dict[str, object]]) -> dict[str, object]:
    values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in equity]
    final = values[-1] if values else INITIAL_CAPITAL
    start = replay.parse_ts(str(equity[0]["decision_asof_ts"])).date() if equity else date(2021, 1, 1)
    end_dates = [parse_date(row.get("scheduled_exit_date")) for row in trades]
    end = max([d for d in end_dates if d] or [start])
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = (final / INITIAL_CAPITAL) ** (1 / years) - 1.0
    mdd = replay.max_drawdown(values)
    return {
        "task_id": "Task2210",
        "policy_variant_id": policy_id,
        "initial_capital": INITIAL_CAPITAL,
        "final_equity": round(final, 4),
        "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
        "cagr": round(cagr, 6),
        "max_drawdown": round(mdd, 6),
        "trade_count": len(trades),
        "qqq_benchmark_final": QQQ_FINAL,
        "qqq_benchmark_cagr": QQQ_CAGR,
        "beats_qqq": "1" if final > QQQ_FINAL else "0",
        "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
        "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
        "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 and final > QQQ_FINAL else "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "outcome_used_for_audit_only": "1",
        "authority": AUTHORITY,
    }


def comparison_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "task_id": "Task2211",
            "comparison_id": "COMPARE2211-0001",
            "variant": "qqq_buy_hold_benchmark",
            "scope": "benchmark",
            "candidate_selection_scope": "not_applicable",
            "final_equity": QQQ_FINAL,
            "cagr": QQQ_CAGR,
            "max_drawdown": "",
            "trade_count": "",
            "notes": "QQQ benchmark final and CAGR reused from prior harness benchmark.",
            "authority": AUTHORITY,
        }
    ]
    reference_files = [
        ("task1717_bad_trade_gate_top3_full_universe", TASK1698 / "task1705_bad_trade_gate_replay_metrics.csv", "full_universe_prior"),
        ("task2151_api_loop3_guarded_risk_cap_top2", TASK2151 / "task2175_api_three_loop_replay_metrics.csv", "selected_116_sizing_only"),
        ("task2191_api_dd_guard_winner_preserve_top2", TASK2191 / "task2196_guard_replay_metrics.csv", "selected_116_sizing_only"),
    ]
    idx = 2
    for variant, path, scope in reference_files:
        if not path.exists():
            continue
        candidates = read_csv(path)
        if "task1717" in variant:
            target = next((row for row in candidates if row.get("policy_variant_id") == "bad_trade_gate_top3_v1"), candidates[0])
        elif "task2151" in variant:
            target = next((row for row in candidates if row.get("policy_variant_id") == "api_loop3_guarded_risk_cap_top2_v1"), candidates[0])
        else:
            target = next((row for row in candidates if row.get("policy_variant_id") == "api_dd_guard_winner_preserve_top2_v1"), candidates[0])
        rows.append(
            {
                "task_id": "Task2211",
                "comparison_id": f"COMPARE2211-{idx:04d}",
                "variant": variant,
                "scope": scope,
                "candidate_selection_scope": scope,
                "final_equity": target.get("final_equity", ""),
                "cagr": target.get("cagr", ""),
                "max_drawdown": target.get("max_drawdown", ""),
                "trade_count": target.get("trade_count", ""),
                "notes": str(path.relative_to(ROOT)).replace("\\", "/"),
                "authority": AUTHORITY,
            }
        )
        idx += 1
    for row in metrics:
        rows.append(
            {
                "task_id": "Task2211",
                "comparison_id": f"COMPARE2211-{idx:04d}",
                "variant": row["policy_variant_id"],
                "scope": "full_universe_latest_brain_replay",
                "candidate_selection_scope": "3100_candidate_full_pool_selection_recomputed",
                "final_equity": row["final_equity"],
                "cagr": row["cagr"],
                "max_drawdown": row["max_drawdown"],
                "trade_count": row["trade_count"],
                "notes": "new full-candidate replay, not same-trade sizing only",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def selected_trade_breakdown(trades: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_symbol: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"trades": 0.0, "pnl": 0.0, "wins": 0.0, "losses": 0.0})
    for row in trades:
        key_ = (str(row["policy_variant_id"]), str(row["symbol"]))
        pnl = to_float(row["pnl"])
        by_symbol[key_]["trades"] += 1
        by_symbol[key_]["pnl"] += pnl
        by_symbol[key_]["wins"] += 1 if pnl > 0 else 0
        by_symbol[key_]["losses"] += 1 if pnl < 0 else 0
    symbol_rows: list[dict[str, object]] = []
    for idx, ((policy, symbol), vals) in enumerate(sorted(by_symbol.items(), key=lambda item: (item[0][0], item[1]["pnl"])), start=1):
        trades_count = max(vals["trades"], 1.0)
        symbol_rows.append(
            {
                "task_id": "Task2213",
                "symbol_breakdown_id": f"SYMBRK2213-{idx:05d}",
                "policy_variant_id": policy,
                "symbol": symbol,
                "trade_count": int(vals["trades"]),
                "pnl_sum": round(vals["pnl"], 4),
                "win_count": int(vals["wins"]),
                "loss_count": int(vals["losses"]),
                "avg_pnl": round(vals["pnl"] / trades_count, 4),
                "authority": AUTHORITY,
            }
        )
    worst_rows: list[dict[str, object]] = []
    idx = 1
    for policy in sorted({str(row["policy_variant_id"]) for row in trades}):
        rows = [row for row in trades if row["policy_variant_id"] == policy]
        for row in sorted(rows, key=lambda x: to_float(x["pnl"]))[:15]:
            worst_rows.append(
                {
                    "task_id": "Task2214",
                    "worst_trade_id": f"WORST2214-{idx:05d}",
                    "policy_variant_id": policy,
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "latest_brain_rank_within_decision": row["latest_brain_rank_within_decision"],
                    "latest_brain_rank_score": row["latest_brain_rank_score"],
                    "thesis_state": row["thesis_state"],
                    "payoff_quality_bucket": row["payoff_quality_bucket"],
                    "collapse_risk_bucket": row["collapse_risk_bucket"],
                    "drawdown_guard_state": row["drawdown_guard_state"],
                    "guard_action": row["guard_action"],
                    "capital_allocated": row["capital_allocated"],
                    "net_return": row["net_return"],
                    "pnl": row["pnl"],
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return symbol_rows, worst_rows


def closeout_rows(metrics: list[dict[str, object]], source_rows: list[dict[str, object]], features: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: (row["joint_target_met"] == "1", to_float(row["final_equity"])))
    full_api = next(row for row in source_rows if row["source_family"] == "api_hardened_overlay")
    return [
        {
            "task_id": "Task2230",
            "verdict": "latest_brain_full_universe_replay_complete_diagnostic_only",
            "brain_version_id": "latest_brain_full_universe_v1",
            "candidate_rows": len(features),
            "selection_allowed_rows": sum(1 for row in features if row["selection_allowed"] == "1"),
            "api_exact_covered_rows": full_api["exact_covered_rows"],
            "api_missing_neutral_rows": full_api["missing_rows"],
            "policy_variant_count": len(metrics),
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "beats_qqq": best["beats_qqq"],
            "joint_target_met": best["joint_target_met"],
            "same_trade_sizing_only": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], source_rows: list[dict[str, object]], comparison: list[dict[str, object]], worst_rows: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metric_lines = "\n".join(
        f"- `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}, beats QQQ {row['beats_qqq']}, joint {row['joint_target_met']}."
        for row in metrics
    )
    source_lines = "\n".join(
        f"- `{row['source_family']}`: covered {row['exact_covered_rows']}/{row['candidate_rows']}, missing {row['missing_rows']}, policy `{row['assignment_policy']}`."
        for row in source_rows
    )
    comparison_lines = "\n".join(
        f"- `{row['variant']}` ({row['scope']}): final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in comparison
    )
    worst_lines = "\n".join(
        f"- `{row['policy_variant_id']}` {row['symbol']} {str(row['decision_asof_ts'])[:10]}: pnl {row['pnl']}, return {row['net_return']}, guard `{row['guard_action']}`."
        for row in worst_rows[:10]
    )
    text = f"""# Task2201-2230 Latest Brain Full-Universe Replay

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Brain version: `{closeout['brain_version_id']}`.
- Candidate pool: {closeout['candidate_rows']} rows.
- Selection allowed after L5/gates: {closeout['selection_allowed_rows']} rows.
- API exact coverage: {closeout['api_exact_covered_rows']} rows; missing rows are neutral, not negative.
- Best new policy: `{closeout['best_policy_variant_id']}`.
- Best final equity: {closeout['best_final_equity']}.
- Best CAGR: {closeout['best_cagr']}.
- Best MDD: {closeout['best_max_drawdown']}.
- Same-trade sizing only: `{closeout['same_trade_sizing_only']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task freezes the latest usable L0-L5 brain into `latest_brain_full_universe_v1` and applies it to the 3,100-row canonical candidate pool. It reselects trades from the full pool instead of applying sizing to the previous 116 selected trades. Scheduled returns are used only after assignment for diagnostic PnL audit.

Replay results:

{metric_lines}

Source family coverage:

{source_lines}

Comparison:

{comparison_lines}

Worst selected trades:

{worst_lines}

## No-Background Decision-Maker Report

Conclusion first: this is no longer the same 116 trades with different sizing. The brain picked again from the 3,100-candidate pool. The result should therefore be read as a harder and more realistic diagnostic than the previous selected-trade sizing replay.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2201_2230_latest_brain_full_universe_replay/`.
- Skill installed for repeated acquisition: `C:/Users/minjo/.codex/skills/trader-brain-source-acquisition`.
- Validator: `python scripts/trader_brain_2201_2230_latest_brain_full_universe_replay_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(text, encoding="utf-8")


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    existing = {row["task_id"] for row in rows}
    fieldnames = list(rows[0].keys())
    for task_no in range(2201, 2231):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "task_name": f"Latest Brain Full-Universe Replay Step {task_no}",
                "workstream": "Research Governance / Backtest & Simulation Infra",
                "status": "active",
                "validation_tier": "diagnostic-only",
                "acceptance_state": "NOT_ACCEPTED",
                "current_decision": "latest-brain-full-universe-replay-diagnostic-only",
                "upstream_task": f"Task{task_no - 1}" if task_no > 2201 else "Task2200",
                "report_path": "docs/reports/task_2201_2230_latest_brain_full_universe_replay/task_2201_2230_latest_brain_full_universe_replay.md",
                "decision_path": "docs/reports/task_2201_2230_latest_brain_full_universe_replay/task_2201_2230_decision.csv",
                "artifact_path": "data/artifacts/task_2201_2230_latest_brain_full_universe_replay",
                "validation_command": "python scripts/trader_brain_2201_2230_latest_brain_full_universe_replay_validate.py",
                "notes": "Freezes latest L0-L5 brain, reselects from 3100 full candidates, and compares against QQQ and selected-trade aggressive sizing.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "110. Task2201-Task2230"
    if marker in text:
        return
    line = (
        f"110. Task2201-Task2230 froze `latest_brain_full_universe_v1` and replayed selection from the "
        f"3,100-row full candidate pool, not only the prior 116 selected trades. Best "
        f"`{closeout['best_policy_variant_id']}` ended final {closeout['best_final_equity']} with CAGR "
        f"{closeout['best_cagr']} and MDD {closeout['best_max_drawdown']}; API overlay remains partial "
        f"({closeout['api_exact_covered_rows']} exact rows) and missing API is neutral. Status remains "
        f"NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert_at = text.find("\n\n\nTask851-859 data certification status:")
    if insert_at == -1:
        text = text.rstrip() + "\n" + line
    else:
        text = text[:insert_at] + "\n" + line + text[insert_at:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    contract = freeze_contract(inputs)
    source_rows, gap_rows = source_family_rows(inputs)
    join_audit, features, ranks = build_feature_panel(inputs)
    trades, equity, metrics = run_replay(features)
    comparison = comparison_rows(metrics)
    symbol_breakdown, worst_trades = selected_trade_breakdown(trades)
    closeout = closeout_rows(metrics, source_rows, features)

    write_csv(OUT_DIR / "task2201_latest_brain_freeze_contract.csv", contract)
    write_csv(OUT_DIR / "task2202_full_universe_scope.csv", [
        {
            "task_id": "Task2202",
            "scope_id": "FULLUNIVERSE2202-001",
            "candidate_rows": len(inputs["rank"]),
            "unique_symbols": len({row["symbol"] for row in inputs["rank"]}),
            "decision_asof_count": len({row["decision_asof_ts"] for row in inputs["rank"]}),
            "canonical_candidate_pool": "data/artifacts/task_1488_1507_semantic_v6_replay/task1494_payoff_ranker_v6.csv",
            "same_trade_sizing_only": "0",
            "authority": AUTHORITY,
        }
    ])
    write_csv(OUT_DIR / "task2203_source_family_plan.csv", source_rows)
    write_csv(OUT_DIR / "task2204_full_candidate_join_audit.csv", join_audit)
    write_csv(OUT_DIR / "task2205_l2_l5_latest_brain_feature_panel.csv", features)
    write_csv(OUT_DIR / "task2206_full_universe_rank_panel.csv", ranks)
    write_csv(OUT_DIR / "task2207_full_universe_policy_specs.csv", [
        {
            "task_id": "Task2207",
            "policy_variant_id": policy_id,
            "slot_count": slots,
            "drawdown_guard_enabled": "1" if use_guard else "0",
            "assignment_basis": "latest_brain_rank_score_pre_outcome_only",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for policy_id, slots, use_guard in POLICIES
    ])
    write_csv(OUT_DIR / "task2208_full_universe_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task2209_full_universe_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task2210_full_universe_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task2211_comparison_matrix.csv", comparison)
    write_csv(OUT_DIR / "task2212_gap_ledger.csv", gap_rows)
    write_csv(OUT_DIR / "task2213_selected_symbol_breakdown.csv", symbol_breakdown)
    write_csv(OUT_DIR / "task2214_worst_trade_audit.csv", worst_trades)
    write_csv(OUT_DIR / "task2230_closeout.csv", closeout)
    write_json(OUT_DIR / "task2230_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], metrics, source_rows, comparison, worst_trades)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2201_2230_LATEST_BRAIN_FULL_UNIVERSE_REPLAY_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
