from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2921_2940_l2_l3_mdd_attribution_pack"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2921_2940_l2_l3_mdd_attribution_pack.md"
DECISION = REPORT_DIR / "task_2940_decision.csv"
AUTHORITY = "DIAGNOSTIC_L2_L3_MDD_ATTRIBUTION_ONLY"

MDD_TRADES = ROOT / "data/artifacts/task_2511_2520_kis_mdd_decomposition/task2513_mdd_window_trade_contributors.csv"
KIS_TRADES = ROOT / "data/artifacts/task_2501_2510_kis_cost_basis_test/task2502_kis_repriced_trades.csv"
L2_BRIDGE = ROOT / "data/artifacts/task_2581_2600_source_integrated_selector_diagnostic/task2584_l2_source_feature_bridge.csv"
L3_EDGES = ROOT / "data/artifacts/task_2581_2600_source_integrated_selector_diagnostic/task2585_l3_source_interaction_edges.csv"
RANKS = ROOT / "data/artifacts/task_2581_2600_source_integrated_selector_diagnostic/task2586_source_integrated_selector_ranks.csv"
GUARD_CONTEXT = ROOT / "data/artifacts/task_2521_2530_kis_cost_aware_guard_feasibility/task2526_guard_metrics.csv"


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
        out = float(value)  # type: ignore[arg-type]
        if math.isnan(out):
            return default
        return out
    except Exception:
        return default


def key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        str(row.get("trade_spec_id", "")),
        str(row.get("symbol", "")),
        str(row.get("decision_asof_ts", "")),
    )


def index_one(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {key(row): row for row in rows}


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "mdd": read_csv(MDD_TRADES),
        "kis": read_csv(KIS_TRADES),
        "l2": read_csv(L2_BRIDGE),
        "l3": read_csv(L3_EDGES),
        "ranks": read_csv(RANKS),
        "guard_context": read_csv(GUARD_CONTEXT),
    }


def common_flags() -> dict[str, object]:
    return {
        "outcome_used_for_audit_only": "1",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "missing_source_is_negative": "0",
        "authority": AUTHORITY,
    }


def task2921_scope_freeze(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2921",
            "scope_id": "L2L3MDD2921-0001",
            "objective": "Freeze the KIS MDD-window trade set and join it to existing L2/L3 selector diagnostics without replay or tuning.",
            "mdd_trade_source": MDD_TRADES.as_posix(),
            "mdd_trade_count": len(inputs["mdd"]),
            "l2_source": L2_BRIDGE.as_posix(),
            "l2_row_count": len(inputs["l2"]),
            "l3_source": L3_EDGES.as_posix(),
            "l3_edge_count": len(inputs["l3"]),
            "rank_source": RANKS.as_posix(),
            "rank_row_count": len(inputs["ranks"]),
            "guard_context_source": GUARD_CONTEXT.as_posix(),
            "guard_context_use": "context_only_not_logic_input",
            "replay_performed": "0",
            "selector_tuning_performed": "0",
            "sizing_tuning_performed": "0",
            "exit_tuning_performed": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            **common_flags(),
        }
    ]


def task2922_input_join_audit(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    l2 = index_one(inputs["l2"])
    ranks = index_one(inputs["ranks"])
    kis = index_one(inputs["kis"])
    l3_by_key: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in inputs["l3"]:
        l3_by_key[key(row)].append(row)
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["mdd"], start=1):
        k = key(row)
        rows.append(
            {
                "task_id": "Task2922",
                "join_audit_id": f"L2L3JOIN2922-{idx:05d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "candidate_source_id": row.get("candidate_source_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "l2_match": "1" if k in l2 else "0",
                "rank_match": "1" if k in ranks else "0",
                "kis_trade_match": "1" if k in kis else "0",
                "l3_edge_count": len(l3_by_key.get(k, [])),
                "join_key": "|".join(k),
                **common_flags(),
            }
        )
    return rows


def task2923_mdd_trade_l2_attribution(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    l2 = index_one(inputs["l2"])
    ranks = index_one(inputs["ranks"])
    out: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["mdd"], start=1):
        bridge = l2.get(key(row), {})
        rank = ranks.get(key(row), {})
        kis_pnl = f(row.get("kis_pnl"))
        selector_delta = f(bridge.get("source_integrated_selector_delta"))
        source_rank = f(rank.get("source_integrated_rank"), 999999)
        if kis_pnl < 0 and selector_delta < 0 and source_rank <= 2:
            risk_direction = "loss_survived_despite_l2_l3_risk_penalty"
        elif kis_pnl < 0 and selector_delta > 0:
            risk_direction = "loss_amplified_by_positive_source_delta"
        elif kis_pnl < 0:
            risk_direction = "loss_without_positive_source_delta"
        else:
            risk_direction = "non_loss_trade"
        out.append(
            {
                "task_id": "Task2923",
                "l2_attribution_id": f"L2MDD2923-{idx:05d}",
                "rank_by_kis_pnl": row.get("rank_by_kis_pnl", ""),
                "trade_spec_id": row.get("trade_spec_id", ""),
                "candidate_source_id": row.get("candidate_source_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "kis_pnl": row.get("kis_pnl", ""),
                "kis_net_return": row.get("kis_net_return", ""),
                "runtime_action": row.get("runtime_action", ""),
                "winner_defense_bucket": row.get("winner_defense_bucket", ""),
                "volatility_cause": row.get("volatility_cause", ""),
                "base_selector_score": bridge.get("base_selector_score", ""),
                "source_integrated_selector_score": bridge.get("source_integrated_selector_score", ""),
                "source_integrated_selector_delta": bridge.get("source_integrated_selector_delta", ""),
                "strategy_sleeve": bridge.get("strategy_sleeve", ""),
                "sec_state": bridge.get("sec_state", ""),
                "regime_state": bridge.get("regime_state", ""),
                "interaction_state": bridge.get("interaction_state", ""),
                "sec_reason": bridge.get("sec_reason", ""),
                "regime_reason_codes": bridge.get("regime_reason_codes", ""),
                "base_rank": rank.get("base_rank", ""),
                "source_integrated_rank": rank.get("source_integrated_rank", ""),
                "rank_improvement": rank.get("rank_improvement", ""),
                "risk_direction": risk_direction,
                "strict_sec_gate_pass": bridge.get("strict_sec_gate_pass", ""),
                "strict_liquidity_rates_gate_pass": bridge.get("strict_liquidity_rates_gate_pass", ""),
                **common_flags(),
            }
        )
    return out


def task2924_mdd_trade_l3_edges(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    mdd_keys = {key(row) for row in inputs["mdd"]}
    rows: list[dict[str, object]] = []
    for idx, edge in enumerate([row for row in inputs["l3"] if key(row) in mdd_keys], start=1):
        rows.append(
            {
                "task_id": "Task2924",
                "mdd_l3_edge_audit_id": f"L3MDD2924-{idx:05d}",
                "source_l3_edge_id": edge.get("l3_edge_id", ""),
                "trade_spec_id": edge.get("trade_spec_id", ""),
                "symbol": edge.get("symbol", ""),
                "decision_asof_ts": edge.get("decision_asof_ts", ""),
                "edge_type": edge.get("edge_type", ""),
                "relation_state": edge.get("relation_state", ""),
                "selector_score_contribution": edge.get("selector_score_contribution", ""),
                "strict_gate_pass": edge.get("strict_gate_pass", ""),
                **common_flags(),
            }
        )
    return rows


def group_l2_losses(l2_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in l2_rows:
        groups[
            (
                str(row.get("sec_state", "")),
                str(row.get("regime_state", "")),
                str(row.get("interaction_state", "")),
            )
        ].append(row)
    out: list[dict[str, object]] = []
    for idx, (state, items) in enumerate(sorted(groups.items(), key=lambda kv: sum(f(r.get("kis_pnl")) for r in kv[1])), start=1):
        pnl = sum(f(row.get("kis_pnl")) for row in items)
        delta = sum(f(row.get("source_integrated_selector_delta")) for row in items)
        out.append(
            {
                "task_id": "Task2925",
                "loss_group_id": f"L2L3LOSS2925-{idx:05d}",
                "sec_state": state[0],
                "regime_state": state[1],
                "interaction_state": state[2],
                "trade_count": len(items),
                "symbol_count": len({row.get("symbol", "") for row in items}),
                "kis_pnl_sum": round(pnl, 6),
                "negative_trade_count": sum(1 for row in items if f(row.get("kis_pnl")) < 0),
                "source_integrated_selector_delta_sum": round(delta, 6),
                "avg_source_integrated_selector_delta": round(delta / len(items), 6) if items else 0,
                "diagnostic_read": "positive_l2_l3_bonus_did_not_prevent_mdd_loss" if pnl < 0 and delta > 0 else "mixed_or_unboosted_loss_group",
                **common_flags(),
            }
        )
    return out


def task2926_rank_impact_audit(l2_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(sorted(l2_rows, key=lambda r: f(r.get("kis_pnl"))), start=1):
        source_rank = f(row.get("source_integrated_rank"), 999999)
        base_rank = f(row.get("base_rank"), 999999)
        rows.append(
            {
                "task_id": "Task2926",
                "rank_impact_id": f"L2L3RANK2926-{idx:05d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "kis_pnl": row.get("kis_pnl", ""),
                "base_rank": row.get("base_rank", ""),
                "source_integrated_rank": row.get("source_integrated_rank", ""),
                "rank_improvement": row.get("rank_improvement", ""),
                "source_integrated_selector_delta": row.get("source_integrated_selector_delta", ""),
                "rank_effect_bucket": "source_rank_top2_loss" if source_rank <= 2 and f(row.get("kis_pnl")) < 0 else "not_source_top2_loss",
                "rank_worsened_vs_base": "1" if source_rank > base_rank else "0",
                **common_flags(),
            }
        )
    return rows


def task2927_top2_selection_survival(l2_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(l2_rows, start=1):
        source_rank = f(row.get("source_integrated_rank"), 999999)
        base_rank = f(row.get("base_rank"), 999999)
        rows.append(
            {
                "task_id": "Task2927",
                "survival_id": f"L2L3SURVIVE2927-{idx:05d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "kis_pnl": row.get("kis_pnl", ""),
                "base_top2": "1" if base_rank <= 2 else "0",
                "source_integrated_top2": "1" if source_rank <= 2 else "0",
                "survives_source_integrated_top2": "1" if source_rank <= 2 else "0",
                "excluded_by_source_integrated_top2": "1" if source_rank > 2 else "0",
                "survival_read": "bad_trade_would_survive_l2_l3_top2" if source_rank <= 2 and f(row.get("kis_pnl")) < 0 else "not_top2_or_nonnegative",
                **common_flags(),
            }
        )
    return rows


def task2928_source_gap_proxy_boundary(l2_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(l2_rows, start=1):
        strict_ok = row.get("strict_sec_gate_pass") == "1" and row.get("strict_liquidity_rates_gate_pass") == "1"
        rows.append(
            {
                "task_id": "Task2928",
                "source_boundary_id": f"L2L3SOURCE2928-{idx:05d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "sec_state": row.get("sec_state", ""),
                "regime_state": row.get("regime_state", ""),
                "strict_sec_gate_pass": row.get("strict_sec_gate_pass", ""),
                "strict_liquidity_rates_gate_pass": row.get("strict_liquidity_rates_gate_pass", ""),
                "strict_source_boundary_pass": "1" if strict_ok else "0",
                "source_gap_action": "report_gap_not_negative" if not strict_ok else "strict_boundary_available",
                **common_flags(),
            }
        )
    return rows


def avoidability(row: dict[str, object]) -> tuple[str, str]:
    sec = str(row.get("sec_state", "")).lower()
    regime = str(row.get("regime_state", "")).lower()
    interaction = str(row.get("interaction_state", "")).lower()
    delta = f(row.get("source_integrated_selector_delta"))
    source_rank = f(row.get("source_integrated_rank"), 999999)
    pnl = f(row.get("kis_pnl"))
    risky_sec_states = {
        "debt_survival_financing_cluster",
        "high_recent_financing_dilution_pressure",
        "moderate_recent_financing_dilution_watch",
    }
    risky_regime_tokens = ("stress", "tight", "headwind")
    if pnl >= 0:
        return "not_loss_trade", "Trade did not lose money in the audited MDD window."
    if source_rank <= 2 and sec in risky_sec_states:
        return "l2_l3_signal_seen_but_not_invalidated", "SEC financing/dilution pressure existed, but L2/L3 still let the loss trade survive top2."
    if source_rank <= 2 and any(token in regime for token in risky_regime_tokens):
        return "l2_l3_regime_warning_seen_but_not_capped", "Liquidity/rates warning existed, but L2/L3 still let the loss trade survive top2."
    if source_rank <= 2 and delta > 0 and "benign" in regime and "clean" in sec:
        return "not_flagged_by_current_l2_l3", "Current L2/L3 actively favored the trade; this is the key blind spot."
    if sec in risky_sec_states:
        return "potentially_avoidable_sec_financing_signal", "SEC financing/dilution pressure existed before selection."
    if any(token in regime for token in risky_regime_tokens):
        return "potentially_avoidable_regime_signal", "Liquidity/rates regime had a stress signal before or at selection."
    if "mixed" in interaction or "conflict" in interaction:
        return "potentially_avoidable_interaction_conflict", "L3 interaction state was mixed/conflicted before selection."
    return "not_flagged_by_current_l2_l3", "No current L2/L3 pre-trade warning was strong enough to exclude it."


def task2929_avoidable_unavoidable_audit(l2_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(sorted(l2_rows, key=lambda r: f(r.get("kis_pnl"))), start=1):
        bucket, reason = avoidability(row)
        rows.append(
            {
                "task_id": "Task2929",
                "avoidability_id": f"L2L3AVOID2929-{idx:05d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "kis_pnl": row.get("kis_pnl", ""),
                "sec_state": row.get("sec_state", ""),
                "regime_state": row.get("regime_state", ""),
                "interaction_state": row.get("interaction_state", ""),
                "source_integrated_rank": row.get("source_integrated_rank", ""),
                "source_integrated_selector_delta": row.get("source_integrated_selector_delta", ""),
                "avoidability_bucket": bucket,
                "avoidability_reason": reason,
                "allowed_use": "diagnostic_rule_design_only_not_assignment",
                **common_flags(),
            }
        )
    return rows


def task2940_closeout(
    join_audit: list[dict[str, object]],
    l2_rows: list[dict[str, object]],
    l3_rows: list[dict[str, object]],
    survival: list[dict[str, object]],
    avoidability: list[dict[str, object]],
) -> list[dict[str, object]]:
    l2_match = sum(1 for row in join_audit if row.get("l2_match") == "1")
    l3_edges = sum(int(row.get("l3_edge_count", 0)) for row in join_audit)
    negative = [row for row in l2_rows if f(row.get("kis_pnl")) < 0]
    top2_loss = [row for row in survival if row.get("survives_source_integrated_top2") == "1" and f(row.get("kis_pnl")) < 0]
    blind_spots = [
        row
        for row in avoidability
        if row.get("avoidability_bucket")
        in {
            "not_flagged_by_current_l2_l3",
            "l2_l3_signal_seen_but_not_invalidated",
            "l2_l3_regime_warning_seen_but_not_capped",
        }
    ]
    return [
        {
            "task_id": "Task2940",
            "verdict": "l2_l3_mdd_attribution_pack_completed_diagnostic_only",
            "mdd_trade_count": len(join_audit),
            "l2_match_count": l2_match,
            "l3_edge_count": len(l3_rows),
            "l3_edge_count_from_join": l3_edges,
            "negative_trade_count": len(negative),
            "source_integrated_top2_negative_trade_count": len(top2_loss),
            "current_l2_l3_blind_spot_count": len(blind_spots),
            "primary_read": "Current L2/L3 explains available source states but still lets several MDD-window losers pass as top candidates.",
            "next_action": "Task2941-2960 should convert this audit into L4 thesis invalidation candidates without using outcomes in assignment.",
            "replay_performed": "0",
            "selector_tuning_performed": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            **common_flags(),
        }
    ]


def write_report(closeout: dict[str, object], losses: list[dict[str, object]], avoidability: list[dict[str, object]]) -> None:
    worst_groups = "\n".join(
        f"- `{row['sec_state']}` / `{row['regime_state']}` / `{row['interaction_state']}`: "
        f"{row['trade_count']} trades, KIS PnL {row['kis_pnl_sum']}, read `{row['diagnostic_read']}`."
        for row in losses[:8]
    )
    avoid_lines = "\n".join(
        f"- `{row['symbol']}` {row['decision_asof_ts']}: {row['kis_pnl']} -> `{row['avoidability_bucket']}`. {row['avoidability_reason']}"
        for row in avoidability[:10]
    )
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# Task2921-2940 L2/L3 MDD Attribution Pack

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- MDD trade count: {closeout['mdd_trade_count']}.
- L2 match count: {closeout['l2_match_count']}.
- L3 edge count: {closeout['l3_edge_count']}.
- Negative trade count: {closeout['negative_trade_count']}.
- Source-integrated top2 negative trade count: {closeout['source_integrated_top2_negative_trade_count']}.
- Current L2/L3 blind spot count: {closeout['current_l2_l3_blind_spot_count']}.
- Replay performed: `0`.
- Selector tuning performed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Join keys: `trade_spec_id`, `symbol`, `decision_asof_ts`.

Worst L2/L3 loss groups:

{worst_groups}

Avoidability audit:

{avoid_lines}

This is an attribution pack only. It does not change selector, sizing, exit, paper order, live order, or assignment logic.

## No-Background Decision-Maker Report

Conclusion first: L2/L3 data exists for the MDD-window trades, but some losers still look acceptable under the current source-integrated selector.

The main issue is not missing rows. The issue is judgment quality: clean SEC state plus benign liquidity state can still hide bad trades.

Next step: build L4 thesis invalidation from these specific blind spots. Do not optimize from outcomes directly.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2921_2940_l2_l3_mdd_attribution_pack/`.
- Validator: `python scripts/trader_brain_2921_2940_l2_l3_mdd_attribution_pack_validate.py`.

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
    for task_no in range(2921, 2941):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"L2/L3 MDD Attribution Pack Step {task_no}",
                "owner_team": "Research Governance / Trader Brain L2-L3 / MDD Attribution",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "l2-l3-mdd-attribution-audit-only",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2921_2940_l2_l3_mdd_attribution_pack/task_2921_2940_l2_l3_mdd_attribution_pack.md",
                "key_decision": "docs/reports/task_2921_2940_l2_l3_mdd_attribution_pack/task_2940_decision.csv",
                "key_artifacts": "data/artifacts/task_2921_2940_l2_l3_mdd_attribution_pack",
                "validation_command": "python scripts/trader_brain_2921_2940_l2_l3_mdd_attribution_pack_validate.py",
                "notes": "Joins KIS MDD-window trades to existing L2/L3 source diagnostics without replay or tuning.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "143. Task2921-Task2940"
    line = (
        "143. Task2921-Task2940 built the L2/L3 MDD attribution pack: "
        f"MDD trades {closeout['mdd_trade_count']}, L2 matches {closeout['l2_match_count']}, "
        f"L3 edges {closeout['l3_edge_count']}, negative trades {closeout['negative_trade_count']}, "
        f"source-integrated top2 negative trades {closeout['source_integrated_top2_negative_trade_count']}, "
        f"current L2/L3 blind spots {closeout['current_l2_l3_blind_spot_count']}; "
        "no replay or selector tuning was performed. "
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
    scope = task2921_scope_freeze(inputs)
    join_audit = task2922_input_join_audit(inputs)
    l2_rows = task2923_mdd_trade_l2_attribution(inputs)
    l3_rows = task2924_mdd_trade_l3_edges(inputs)
    losses = group_l2_losses(l2_rows)
    rank_audit = task2926_rank_impact_audit(l2_rows)
    survival = task2927_top2_selection_survival(l2_rows)
    source_boundary = task2928_source_gap_proxy_boundary(l2_rows)
    avoidability_rows = task2929_avoidable_unavoidable_audit(l2_rows)
    closeout = task2940_closeout(join_audit, l2_rows, l3_rows, survival, avoidability_rows)

    outputs = [
        ("task2921_scope_freeze.csv", scope),
        ("task2922_input_join_audit.csv", join_audit),
        ("task2923_mdd_trade_l2_attribution.csv", l2_rows),
        ("task2924_mdd_trade_l3_edges.csv", l3_rows),
        ("task2925_loss_by_sec_regime_state.csv", losses),
        ("task2926_rank_impact_audit.csv", rank_audit),
        ("task2927_top2_selection_survival.csv", survival),
        ("task2928_source_gap_proxy_boundary.csv", source_boundary),
        ("task2929_avoidable_unavoidable_audit.csv", avoidability_rows),
        ("task2940_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2940_closeout.json", closeout[0])
    write_report(closeout[0], losses, avoidability_rows)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2921_2940_L2_L3_MDD_ATTRIBUTION_PACK_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
