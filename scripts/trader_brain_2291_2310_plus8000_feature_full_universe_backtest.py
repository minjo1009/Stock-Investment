from __future__ import annotations

import csv
import json
from pathlib import Path

import trader_brain_2201_2230_latest_brain_full_universe_replay as base
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2291_2310_plus8000_feature_full_universe_backtest"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2291_2310_plus8000_feature_full_universe_backtest.md"
DECISION = REPORT_DIR / "task_2291_2310_decision.csv"

TASK2251 = ROOT / "data/artifacts/task_2251_2280_plus8000_full_source_acquisition"
TASK2281 = ROOT / "data/artifacts/task_2281_2290_post_acquisition_parity"

AUTHORITY = "DIAGNOSTIC_PLUS8000_FEATURE_FULL_UNIVERSE_BACKTEST_ONLY"
POLICIES = [
    ("plus8000_feature_full_top2_v1", 2, True),
    ("plus8000_feature_full_top3_v1", 3, True),
    ("plus8000_feature_full_top5_v1", 5, True),
    ("plus8000_feature_full_top10_v1", 10, True),
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


def key(row: dict[str, object]) -> tuple[str, str, str, str]:
    return (
        str(row.get("candidate_source_id", "")),
        str(row.get("trade_spec_id", "")),
        str(row.get("symbol", "")),
        str(row.get("decision_asof_ts", "")),
    )


def to_float(value: object, default: float = 0.0) -> float:
    return base.to_float(value, default)


def map_proxy_state(state: str, score: float) -> str:
    if state == "api_proxy_supportive":
        return "api_event_context_supportive"
    if state == "api_proxy_risk_or_weak_quality" or score <= -8:
        return "api_risk_context_cap_required"
    if state == "api_proxy_source_gap_neutral":
        return "api_source_gap_neutral"
    return "api_mixed_or_light_neutral"


def map_budget_multiplier(state: str, score: float, row: dict[str, str]) -> tuple[float, str]:
    financial_source = row.get("financial_source", "")
    if state == "api_proxy_risk_or_weak_quality" or score <= -8:
        return 0.45, "plus8000_proxy_quality_risk_cap"
    if financial_source == "financial_source_gap":
        return 0.85, "plus8000_proxy_source_gap_soft_cap"
    if state == "api_proxy_supportive" and score >= 24:
        return 1.25, "plus8000_proxy_supportive_boost"
    if state == "api_proxy_supportive":
        return 1.10, "plus8000_proxy_supportive"
    return 1.00, "plus8000_proxy_neutral"


def build_plus8000_api_inputs(features: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    cards: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    for idx, row in enumerate(features, start=1):
        score = to_float(row.get("api_proxy_score"))
        state = row.get("api_proxy_state", "")
        api_state = map_proxy_state(state, score)
        budget, action = map_budget_multiplier(state, score, row)
        common = {
            "trade_spec_id": row["trade_spec_id"],
            "candidate_source_id": row["candidate_source_id"],
            "symbol": row["symbol"],
            "decision_asof_ts": row["decision_asof_ts"],
        }
        cards.append(
            {
                "task_id": "Task2292",
                "api_l4_score_card_id": f"PLUS8000FULLL4-2292-{idx:07d}",
                **common,
                "api_l2_state": api_state,
                "api_l2_score": score,
                "api_raw_overlay_score": score,
                "api_cohort_overlay_score": score,
                "api_adjusted_rank_score": "",
                "strict_gate_status": "PLUS8000_FEATURE_PROXY_GATE_NOT_STRICT_RAW_COMPLETE",
                "plus8000_api_proxy_state": state,
                "plus8000_api_proxy_score": score,
                "financial_source": row.get("financial_source", ""),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        decisions.append(
            {
                "task_id": "Task2293",
                "api_l5_decision_id": f"PLUS8000FULLL5-2293-{idx:07d}",
                **common,
                "api_l5_action": action,
                "api_l5_budget_multiplier": budget,
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return cards, decisions


def proxy_score_adjustment(row: dict[str, object]) -> tuple[float, str]:
    score = to_float(row.get("plus8000_api_proxy_score"))
    state = str(row.get("plus8000_api_proxy_state", ""))
    if state == "api_proxy_supportive":
        return min(18.0, max(4.0, score * 0.45)), "supportive_proxy_rank_boost_capped"
    if state == "api_proxy_risk_or_weak_quality":
        return max(-28.0, score * 0.75), "weak_quality_proxy_rank_penalty_capped"
    if state == "api_proxy_source_gap_neutral":
        return 0.0, "source_gap_neutral_not_negative"
    return max(-4.0, min(6.0, score * 0.15)), "mixed_proxy_small_adjustment"


def rebuild_ranks(features: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in features:
        grouped.setdefault(str(row["decision_asof_ts"]), []).append(row)
    rows: list[dict[str, object]] = []
    idx = 1
    for decision_ts in sorted(grouped):
        ranked = sorted(
            grouped[decision_ts],
            key=lambda row: (
                int(row["selection_allowed"]),
                to_float(row["latest_brain_rank_score"]),
                -to_float(row["candidate_rank"], 999999),
            ),
            reverse=True,
        )
        for rank_within, row in enumerate(ranked, start=1):
            row["latest_brain_rank_within_decision"] = rank_within
            rows.append(
                {
                    "task_id": "Task2295",
                    "rank_row_id": f"PLUS8000FULLRANK-2295-{idx:07d}",
                    "candidate_source_id": row["candidate_source_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "latest_brain_rank_score": row["latest_brain_rank_score"],
                    "latest_brain_rank_within_decision": rank_within,
                    "selection_allowed": row["selection_allowed"],
                    "position_size_cap_multiplier": row["position_size_cap_multiplier"],
                    "plus8000_api_proxy_state": row.get("plus8000_api_proxy_state", ""),
                    "plus8000_api_proxy_score": row.get("plus8000_api_proxy_score", ""),
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def build_feature_panel() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    inputs = base.load_inputs()
    plus8000_features = read_csv(TASK2251 / "task2256_recomputed_plus8000_feature_panel.csv")
    api_cards, api_decisions = build_plus8000_api_inputs(plus8000_features)
    inputs["api_cards"] = [dict(row) for row in api_cards]
    inputs["api_decisions"] = [dict(row) for row in api_decisions]
    join_audit, features, _ = base.build_feature_panel(inputs)
    proxy_by_key = {key(row): row for row in plus8000_features}
    for row in features:
        proxy = proxy_by_key.get(key(row), {})
        row["task_id"] = "Task2294"
        row["feature_row_id"] = str(row["feature_row_id"]).replace("LATESTFULLFEAT2205", "PLUS8000FULLFEAT2294")
        row["authority"] = AUTHORITY
        row["api_scope_state"] = "plus8000_feature_proxy_available" if proxy else "plus8000_feature_proxy_missing_neutral"
        row["plus8000_api_proxy_state"] = proxy.get("api_proxy_state", "api_proxy_source_gap_neutral")
        row["plus8000_api_proxy_score"] = proxy.get("api_proxy_score", "0.0")
        row["latest_earnings_surprise_pct"] = proxy.get("latest_earnings_surprise_pct", "0.0")
        row["latest_revenue"] = proxy.get("latest_revenue", "0.0")
        row["latest_net_income"] = proxy.get("latest_net_income", "0.0")
        row["latest_free_cash_flow"] = proxy.get("latest_free_cash_flow", "0.0")
        row["latest_cash"] = proxy.get("latest_cash", "0.0")
        row["latest_debt"] = proxy.get("latest_debt", "0.0")
        row["rating_score"] = proxy.get("rating_score", "0.0")
        row["financial_source"] = proxy.get("financial_source", "financial_source_gap")
        adjustment, reason = proxy_score_adjustment(row)
        row["plus8000_proxy_rank_adjustment"] = round(adjustment, 6)
        row["plus8000_proxy_rank_adjustment_reason"] = reason
        row["latest_brain_rank_score"] = round(to_float(row["latest_brain_rank_score"]) + adjustment, 6)
        if row["plus8000_api_proxy_state"] == "api_proxy_risk_or_weak_quality":
            row["position_size_cap_multiplier"] = min(to_float(row["position_size_cap_multiplier"]), 0.45)
            row["position_size_cap_action"] = "plus8000_proxy_quality_risk_cap"
        elif row["financial_source"] == "financial_source_gap":
            row["position_size_cap_multiplier"] = min(to_float(row["position_size_cap_multiplier"]), 0.85)
            row["position_size_cap_action"] = "plus8000_proxy_source_gap_soft_cap"
        row["missing_source_policy"] = "plus8000_feature_missing_neutral_not_negative"
    ranks = rebuild_ranks(features)
    for row in join_audit:
        row["task_id"] = "Task2293"
        row["join_audit_id"] = str(row["join_audit_id"]).replace("JOINAUDIT2204", "PLUS8000JOIN2293")
        row["authority"] = AUTHORITY
    return api_cards, api_decisions, join_audit, features, ranks


def source_rows(features: list[dict[str, object]]) -> list[dict[str, object]]:
    metrics = [
        ("feature_schema_parity", len(features)),
        ("api_proxy_not_source_gap", sum(1 for row in features if row.get("plus8000_api_proxy_state") != "api_proxy_source_gap_neutral")),
        ("financial_statement_proxy", sum(1 for row in features if row.get("financial_source") != "financial_source_gap")),
        ("earnings_surprise_proxy", sum(1 for row in features if to_float(row.get("latest_earnings_surprise_pct")) != 0.0)),
        ("rating_proxy", sum(1 for row in features if to_float(row.get("rating_score")) != 0.0)),
    ]
    rows: list[dict[str, object]] = []
    for idx, (name, covered) in enumerate(metrics, start=1):
        rows.append(
            {
                "task_id": "Task2292",
                "source_family_id": f"PLUS8000SOURCE2292-{idx:03d}",
                "source_family": name,
                "candidate_rows": len(features),
                "exact_covered_rows": covered,
                "missing_rows": len(features) - covered,
                "coverage_ratio": round(covered / len(features), 6) if features else 0.0,
                "assignment_policy": "feature_proxy_available_missing_neutral_not_strict_raw_complete",
                "authority": AUTHORITY,
            }
        )
    if (TASK2281 / "task2290_closeout.csv").exists():
        closeout = read_csv(TASK2281 / "task2290_closeout.csv")[0]
        rows.append(
            {
                "task_id": "Task2292",
                "source_family_id": "PLUS8000SOURCE2292-RAW",
                "source_family": "strict_raw_asof_replay_gate_reference_only",
                "candidate_rows": closeout.get("candidate_rows", len(features)),
                "exact_covered_rows": closeout.get("replay_gate_candidate_rows", ""),
                "missing_rows": "",
                "coverage_ratio": closeout.get("replay_gate_candidate_ratio", ""),
                "assignment_policy": "reference_only_not_used_for_feature_proxy_backtest",
                "authority": AUTHORITY,
            }
        )
    return rows


def run_replay(features: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    old_policies = base.POLICIES
    old_authority = base.AUTHORITY
    try:
        base.POLICIES = POLICIES
        base.AUTHORITY = AUTHORITY
        trades, equity, metrics = base.run_replay(features)
    finally:
        base.POLICIES = old_policies
        base.AUTHORITY = old_authority
    feature_by_key = {key(row): row for row in features}
    for row in trades:
        feature = feature_by_key.get(key(row), {})
        row["task_id"] = "Task2297"
        row["trade_row_id"] = str(row["trade_row_id"]).replace("LATESTFULLTRADE2208", "PLUS8000FULLTRADE2297")
        row["plus8000_api_proxy_state"] = feature.get("plus8000_api_proxy_state", "")
        row["plus8000_api_proxy_score"] = feature.get("plus8000_api_proxy_score", "")
        row["plus8000_proxy_rank_adjustment"] = feature.get("plus8000_proxy_rank_adjustment", "")
        row["financial_source"] = feature.get("financial_source", "")
        row["authority"] = AUTHORITY
    for row in equity:
        row["task_id"] = "Task2298"
        row["authority"] = AUTHORITY
    for row in metrics:
        row["task_id"] = "Task2299"
        row["authority"] = AUTHORITY
    return trades, equity, metrics


def comparison_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = base.comparison_rows(metrics)
    for idx, row in enumerate(rows, start=1):
        row["task_id"] = "Task2300"
        row["comparison_id"] = f"PLUS8000COMPARE2300-{idx:04d}"
        if row.get("scope") == "full_universe_latest_brain_replay":
            row["scope"] = "plus8000_feature_full_universe_replay"
            row["candidate_selection_scope"] = "3100_candidate_full_pool_recomputed_with_plus8000_feature_proxy"
            row["notes"] = "full 3100 replay using +8000-level feature/proxy panel, not strict raw/as-of complete"
        row["authority"] = AUTHORITY
    return rows


def selected_trade_breakdown(trades: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    symbols, worst = base.selected_trade_breakdown(trades)
    for idx, row in enumerate(symbols, start=1):
        row["task_id"] = "Task2301"
        row["symbol_breakdown_id"] = f"PLUS8000SYMBRK2301-{idx:05d}"
        row["authority"] = AUTHORITY
    for idx, row in enumerate(worst, start=1):
        row["task_id"] = "Task2302"
        row["worst_trade_id"] = f"PLUS8000WORST2302-{idx:05d}"
        match = next(
            (
                trade
                for trade in trades
                if trade["policy_variant_id"] == row["policy_variant_id"]
                and trade["symbol"] == row["symbol"]
                and trade["decision_asof_ts"] == row["decision_asof_ts"]
                and str(trade["pnl"]) == str(row["pnl"])
            ),
            {},
        )
        row["plus8000_api_proxy_state"] = match.get("plus8000_api_proxy_state", "")
        row["plus8000_api_proxy_score"] = match.get("plus8000_api_proxy_score", "")
        row["financial_source"] = match.get("financial_source", "")
        row["authority"] = AUTHORITY
    return symbols, worst


def closeout_rows(metrics: list[dict[str, object]], sources: list[dict[str, object]], features: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: (row["joint_target_met"] == "1", to_float(row["final_equity"])))
    non_gap = next(row for row in sources if row["source_family"] == "api_proxy_not_source_gap")
    return [
        {
            "task_id": "Task2310",
            "verdict": "plus8000_feature_full_universe_backtest_complete_diagnostic_only",
            "brain_version_id": "latest_brain_plus8000_feature_proxy_full_universe_v1",
            "candidate_rows": len(features),
            "selection_allowed_rows": sum(1 for row in features if row["selection_allowed"] == "1"),
            "plus8000_non_gap_feature_rows": non_gap["exact_covered_rows"],
            "policy_variant_count": len(metrics),
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "beats_qqq": best["beats_qqq"],
            "joint_target_met": best["joint_target_met"],
            "same_trade_sizing_only": "0",
            "strict_raw_asof_complete": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], sources: list[dict[str, object]], comparison: list[dict[str, object]], worst: list[dict[str, object]]) -> None:
    metric_lines = "\n".join(
        f"- `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}, beats QQQ {row['beats_qqq']}, joint {row['joint_target_met']}."
        for row in metrics
    )
    source_lines = "\n".join(
        f"- `{row['source_family']}`: covered {row['exact_covered_rows']}/{row['candidate_rows']}, ratio {row['coverage_ratio']}, policy `{row['assignment_policy']}`."
        for row in sources
    )
    comparison_lines = "\n".join(
        f"- `{row['variant']}` ({row['scope']}): final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in comparison
    )
    worst_lines = "\n".join(
        f"- `{row['policy_variant_id']}` {row['symbol']} {str(row['decision_asof_ts'])[:10]}: pnl {row['pnl']}, return {row['net_return']}, guard `{row['guard_action']}`."
        for row in worst[:12]
    )
    REPORT.write_text(
        f"""# Task2291-2310 Plus8000 Feature Full-Universe Backtest

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Brain version: `{closeout['brain_version_id']}`.
- Candidate pool: {closeout['candidate_rows']} rows.
- Selection allowed after L5/gates: {closeout['selection_allowed_rows']} rows.
- +8000 non-gap feature rows: {closeout['plus8000_non_gap_feature_rows']}.
- Best policy: `{closeout['best_policy_variant_id']}`.
- Best final equity: {closeout['best_final_equity']}.
- Best CAGR: {closeout['best_cagr']}.
- Best MDD: {closeout['best_max_drawdown']}.
- Same-trade sizing only: `{closeout['same_trade_sizing_only']}`.
- Strict raw/as-of complete: `{closeout['strict_raw_asof_complete']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task runs the user-authorized diagnostic replay using the +8000-level feature/proxy panel across the full 3,100-candidate pool. It is not a strict raw/as-of-complete replay. Missing feature sources are neutral, not negative. Scheduled returns are used only after assignment for diagnostic PnL audit.

Replay results:

{metric_lines}

Source and proxy coverage:

{source_lines}

Comparison:

{comparison_lines}

Worst selected trades:

{worst_lines}

## No-Background Decision-Maker Report

Conclusion first: this is the fairer comparison to the +8000 selected-trade experiment because the same feature/proxy level is now applied to the full 3,100-candidate pool. It still does not prove deployment readiness because strict raw/as-of completeness is not solved.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2291_2310_plus8000_feature_full_universe_backtest/`.
- Validator: `python scripts/trader_brain_2291_2310_plus8000_feature_full_universe_backtest_validate.py`.

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
    existing = {row["task_id"] for row in rows}
    fieldnames = list(rows[0].keys())
    for task_no in range(2291, 2311):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Plus8000 Feature Full-Universe Backtest Step {task_no}",
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "feature-proxy-ready-raw-asof-incomplete",
                "parent_task": f"Task{task_no - 1}" if task_no > 2291 else "Task2290",
                "key_report": "docs/reports/task_2291_2310_plus8000_feature_full_universe_backtest/task_2291_2310_plus8000_feature_full_universe_backtest.md",
                "key_decision": "docs/reports/task_2291_2310_plus8000_feature_full_universe_backtest/task_2291_2310_decision.csv",
                "key_artifacts": "data/artifacts/task_2291_2310_plus8000_feature_full_universe_backtest",
                "validation_command": "python scripts/trader_brain_2291_2310_plus8000_feature_full_universe_backtest_validate.py",
                "notes": "Diagnostic full-universe replay using Task2251 +8000 feature/proxy panel; not strict raw/as-of complete.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "113. Task2291-Task2310"
    if marker in text:
        return
    line = (
        f"113. Task2291-Task2310 ran the user-authorized +8000 feature/proxy full-universe backtest on the "
        f"3,100-candidate pool. Best `{closeout['best_policy_variant_id']}` ended final {closeout['best_final_equity']} "
        f"with CAGR {closeout['best_cagr']} and MDD {closeout['best_max_drawdown']}; this is feature/proxy comparable, "
        f"not strict raw/as-of complete. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    api_cards, api_decisions, join_audit, features, ranks = build_feature_panel()
    sources = source_rows(features)
    trades, equity, metrics = run_replay(features)
    comparison = comparison_rows(metrics)
    symbols, worst = selected_trade_breakdown(trades)
    closeout = closeout_rows(metrics, sources, features)

    write_csv(OUT_DIR / "task2291_scope.csv", [
        {
            "task_id": "Task2291",
            "scope_id": "PLUS8000FULLSCOPE2291-001",
            "candidate_rows": len(features),
            "same_trade_sizing_only": "0",
            "feature_proxy_standard": "plus8000_level",
            "strict_raw_asof_complete": "0",
            "authority": AUTHORITY,
        }
    ])
    write_csv(OUT_DIR / "task2292_source_proxy_coverage.csv", sources)
    write_csv(OUT_DIR / "task2293_plus8000_api_l4_cards.csv", api_cards)
    write_csv(OUT_DIR / "task2294_plus8000_api_l5_decisions.csv", api_decisions)
    write_csv(OUT_DIR / "task2295_plus8000_join_audit.csv", join_audit)
    write_csv(OUT_DIR / "task2296_plus8000_feature_panel.csv", features)
    write_csv(OUT_DIR / "task2297_plus8000_rank_panel.csv", ranks)
    write_csv(OUT_DIR / "task2297_policy_specs.csv", [
        {
            "task_id": "Task2297",
            "policy_variant_id": policy_id,
            "slot_count": slots,
            "drawdown_guard_enabled": "1" if use_guard else "0",
            "assignment_basis": "latest_brain_rank_score_plus8000_feature_proxy_pre_outcome_only",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for policy_id, slots, use_guard in POLICIES
    ])
    write_csv(OUT_DIR / "task2298_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task2299_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task2300_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task2301_comparison_matrix.csv", comparison)
    write_csv(OUT_DIR / "task2302_selected_symbol_breakdown.csv", symbols)
    write_csv(OUT_DIR / "task2303_worst_trade_audit.csv", worst)
    write_csv(OUT_DIR / "task2310_closeout.csv", closeout)
    write_json(OUT_DIR / "task2310_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], metrics, sources, comparison, worst)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2291_2310_PLUS8000_FEATURE_FULL_UNIVERSE_BACKTEST_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
