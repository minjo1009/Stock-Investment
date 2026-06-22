from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import trader_brain_2191_2200_api_drawdown_sizing_guard as plus8000
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2321_2340_plus8000_brain_newdata_backtest"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2321_2340_plus8000_brain_newdata_backtest.md"
DECISION = REPORT_DIR / "task_2321_2340_decision.csv"

TASK2251 = ROOT / "data/artifacts/task_2251_2280_plus8000_full_source_acquisition"
TASK2191 = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"

AUTHORITY = "DIAGNOSTIC_PLUS8000_BRAIN_NEWDATA_BACKTEST_ONLY"
POLICY_PREFIX = "plus8000_brain_newdata"
POLICY_MAP = {
    "api_dd_guard_soft_boost_cap_top2_v1": f"{POLICY_PREFIX}_soft_boost_cap_top2_v1",
    "api_dd_guard_stress_neutral_top2_v1": f"{POLICY_PREFIX}_stress_neutral_top2_v1",
    "api_dd_guard_winner_preserve_top2_v1": f"{POLICY_PREFIX}_winner_preserve_top2_v1",
}


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


def f(value: object, default: float = 0.0) -> float:
    return plus8000.to_float(value, default)


def key(row: dict[str, object]) -> tuple[str, str, str, str]:
    return (
        str(row.get("candidate_source_id", "")),
        str(row.get("trade_spec_id", "")),
        str(row.get("symbol", "")),
        str(row.get("decision_asof_ts", "")),
    )


def plus_feature_index() -> dict[tuple[str, str, str, str], dict[str, str]]:
    return {key(row): row for row in read_csv(TASK2251 / "task2256_recomputed_plus8000_feature_panel.csv")}


def overlay_adjustment(feature: dict[str, str]) -> tuple[float, float, str, str]:
    state = feature.get("api_proxy_state", "api_proxy_source_gap_neutral")
    score = f(feature.get("api_proxy_score"))
    surprise = f(feature.get("latest_earnings_surprise_pct"))
    rating = f(feature.get("rating_score"))
    if state == "api_proxy_risk_or_weak_quality" or score <= -8:
        return -12.0, 0.72, "api_risk_context_cap_required", "newdata_risk_cap"
    if state == "api_proxy_supportive" and score >= 24:
        return 8.0 + min(4.0, max(surprise, 0.0) * 0.04) + min(2.0, max(rating, 0.0) * 0.1), 1.08, "api_event_context_supportive", "newdata_supportive_boost"
    if state == "api_proxy_supportive" and score >= 18:
        return 4.0, 1.03, "api_event_context_supportive", "newdata_light_support"
    return 0.0, 1.0, "keep_existing_api_state", "newdata_neutral"


def overlay_inputs(inputs: dict[str, list[dict[str, str]]]) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    features = plus_feature_index()
    old_cards = {row["trade_spec_id"]: row for row in inputs["cards"]}
    old_decisions = {row["trade_spec_id"]: row for row in inputs["decisions"]}
    overlay_cards: list[dict[str, object]] = []
    overlay_decisions: list[dict[str, object]] = []
    audit: list[dict[str, object]] = []
    changed_cards: list[dict[str, str]] = []
    changed_decisions: list[dict[str, str]] = []
    for idx, l5 in enumerate(inputs["l5"], start=1):
        spec_id = l5["trade_spec_id"]
        old_card = dict(old_cards.get(spec_id, {}))
        old_decision = dict(old_decisions.get(spec_id, {}))
        feature = features.get(key(l5), {})
        adjustment, api_mult_floor, new_state, action = overlay_adjustment(feature) if feature else (0.0, 1.0, "keep_existing_api_state", "newdata_feature_missing_neutral")
        base_score = f(old_card.get("api_adjusted_rank_score"), f(old_card.get("base_winner_acceleration_rank_score"), f(l5.get("winner_acceleration_rank_score"))))
        old_api_state = old_card.get("api_l2_state", "api_source_gap_neutral")
        old_api_mult = f(old_decision.get("api_l5_budget_multiplier"), 1.0)
        final_state = old_api_state if new_state == "keep_existing_api_state" else new_state
        final_mult = min(old_api_mult, api_mult_floor) if "risk" in final_state else max(old_api_mult, api_mult_floor)
        card = {
            **old_card,
            "task_id": "Task2322",
            "api_l4_score_card_id": f"PLUS8000NEWDATAL4-2322-{idx:07d}",
            "trade_spec_id": spec_id,
            "candidate_source_id": l5["candidate_source_id"],
            "symbol": l5["symbol"],
            "decision_asof_ts": l5["decision_asof_ts"],
            "base_winner_acceleration_rank_score": old_card.get("base_winner_acceleration_rank_score", l5.get("winner_acceleration_rank_score", "")),
            "api_l2_state": final_state,
            "api_l2_score": round(f(old_card.get("api_l2_score")) + adjustment, 6),
            "api_raw_overlay_score": old_card.get("api_raw_overlay_score", ""),
            "strict_gate_status": "PLUS8000_BRAIN_NEWDATA_FEATURE_PROXY_NOT_STRICT_RAW_COMPLETE",
            "newdata_api_proxy_state": feature.get("api_proxy_state", "api_proxy_source_gap_neutral" if feature else "newdata_feature_missing_neutral"),
            "newdata_api_proxy_score": feature.get("api_proxy_score", "0.0"),
            "newdata_financial_source": feature.get("financial_source", "financial_source_gap"),
            "newdata_rank_adjustment": round(adjustment, 6),
            "newdata_overlay_action": action,
            "api_adjusted_rank_score": round(base_score + adjustment, 6),
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        decision = {
            **old_decision,
            "task_id": "Task2323",
            "api_l5_decision_id": f"PLUS8000NEWDATAL5-2323-{idx:07d}",
            "trade_spec_id": spec_id,
            "candidate_source_id": l5["candidate_source_id"],
            "symbol": l5["symbol"],
            "decision_asof_ts": l5["decision_asof_ts"],
            "api_l2_state": final_state,
            "api_l5_action": action if action != "newdata_neutral" else old_decision.get("api_l5_action", "neutral_hold_existing_brain"),
            "api_l5_budget_multiplier": round(final_mult, 6),
            "newdata_overlay_action": action,
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        overlay_cards.append(card)
        overlay_decisions.append(decision)
        audit.append(
            {
                "task_id": "Task2324",
                "overlay_audit_id": f"PLUS8000NEWDATAAUDIT-2324-{idx:07d}",
                "trade_spec_id": spec_id,
                "candidate_source_id": l5["candidate_source_id"],
                "symbol": l5["symbol"],
                "decision_asof_ts": l5["decision_asof_ts"],
                "old_api_l2_state": old_api_state,
                "new_api_l2_state": final_state,
                "old_api_l5_budget_multiplier": old_api_mult,
                "new_api_l5_budget_multiplier": round(final_mult, 6),
                "old_api_adjusted_rank_score": old_card.get("api_adjusted_rank_score", ""),
                "new_api_adjusted_rank_score": round(base_score + adjustment, 6),
                "newdata_api_proxy_state": card["newdata_api_proxy_state"],
                "newdata_api_proxy_score": card["newdata_api_proxy_score"],
                "newdata_overlay_action": action,
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        changed_cards.append({str(k): str(v) for k, v in card.items()})
        changed_decisions.append({str(k): str(v) for k, v in decision.items()})
    new_inputs = dict(inputs)
    new_inputs["cards"] = changed_cards
    new_inputs["decisions"] = changed_decisions
    return new_inputs, overlay_cards, overlay_decisions, audit


def run_plus8000_guard(inputs: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    old_auth = plus8000.AUTHORITY
    try:
        plus8000.AUTHORITY = AUTHORITY
        guard_rows, trades, equity, metrics = plus8000.replay_guard(inputs)
    finally:
        plus8000.AUTHORITY = old_auth
    for row in guard_rows:
        row["task_id"] = "Task2325"
        row["guard_id"] = str(row.get("guard_id", "")).replace("APIDDGUARD-2192", "PLUS8000NEWDATAGUARD-2325")
        row["policy_variant_id"] = POLICY_MAP.get(str(row["policy_variant_id"]), str(row["policy_variant_id"]))
        row["authority"] = AUTHORITY
    for row in trades:
        row["task_id"] = "Task2326"
        row["trade_row_id"] = str(row.get("trade_row_id", "")).replace("APIDDTRADE-2194", "PLUS8000NEWDATATRADE-2326")
        row["policy_variant_id"] = POLICY_MAP.get(str(row["policy_variant_id"]), str(row["policy_variant_id"]))
        row["authority"] = AUTHORITY
    for row in equity:
        row["task_id"] = "Task2327"
        row["policy_variant_id"] = POLICY_MAP.get(str(row["policy_variant_id"]), str(row["policy_variant_id"]))
        row["authority"] = AUTHORITY
    for row in metrics:
        row["task_id"] = "Task2328"
        row["policy_variant_id"] = POLICY_MAP.get(str(row["policy_variant_id"]), str(row["policy_variant_id"]))
        row["authority"] = AUTHORITY
    return guard_rows, trades, equity, metrics


def coverage_rows(audit: list[dict[str, object]]) -> list[dict[str, object]]:
    counts = Counter(str(row["newdata_overlay_action"]) for row in audit)
    states = Counter(str(row["newdata_api_proxy_state"]) for row in audit)
    rows: list[dict[str, object]] = []
    idx = 1
    for action, count in sorted(counts.items()):
        rows.append(
            {
                "task_id": "Task2329",
                "coverage_id": f"PLUS8000NEWDATACOVER-2329-{idx:04d}",
                "metric_type": "overlay_action",
                "metric": action,
                "rows": count,
                "total_rows": len(audit),
                "ratio": round(count / len(audit), 6) if audit else 0.0,
                "authority": AUTHORITY,
            }
        )
        idx += 1
    for state, count in sorted(states.items()):
        rows.append(
            {
                "task_id": "Task2329",
                "coverage_id": f"PLUS8000NEWDATACOVER-2329-{idx:04d}",
                "metric_type": "proxy_state",
                "metric": state,
                "rows": count,
                "total_rows": len(audit),
                "ratio": round(count / len(audit), 6) if audit else 0.0,
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def comparison_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    old_metrics = read_csv(TASK2191 / "task2196_guard_replay_metrics.csv")
    rows: list[dict[str, object]] = []
    idx = 1
    for row in old_metrics:
        rows.append(
            {
                "task_id": "Task2330",
                "comparison_id": f"PLUS8000NEWDATACOMP-2330-{idx:04d}",
                "variant": row["policy_variant_id"],
                "scope": "original_plus8000_brain_task2191",
                "final_equity": row.get("final_equity", ""),
                "cagr": row.get("cagr", ""),
                "max_drawdown": row.get("max_drawdown", ""),
                "trade_count": row.get("trade_count", ""),
                "authority": AUTHORITY,
            }
        )
        idx += 1
    for row in metrics:
        rows.append(
            {
                "task_id": "Task2330",
                "comparison_id": f"PLUS8000NEWDATACOMP-2330-{idx:04d}",
                "variant": row["policy_variant_id"],
                "scope": "plus8000_brain_newdata_overlay",
                "final_equity": row.get("final_equity", ""),
                "cagr": row.get("cagr", ""),
                "max_drawdown": row.get("max_drawdown", ""),
                "trade_count": row.get("trade_count", ""),
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def closeout_rows(metrics: list[dict[str, object]], coverage: list[dict[str, object]], audit: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: f(row.get("final_equity")))
    old_best = next(row for row in read_csv(TASK2191 / "task2196_guard_replay_metrics.csv") if row["policy_variant_id"] == "api_dd_guard_winner_preserve_top2_v1")
    changed = sum(1 for row in audit if row["newdata_overlay_action"] not in {"newdata_neutral", "newdata_feature_missing_neutral"})
    return [
        {
            "task_id": "Task2340",
            "verdict": "plus8000_brain_newdata_overlay_backtest_complete_diagnostic_only",
            "brain_reference": "Task2191_api_dd_guard_winner_preserve_top2_v1",
            "candidate_decision_rows": len(audit),
            "overlay_changed_rows": changed,
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "reference_plus8000_final": old_best["final_equity"],
            "reference_plus8000_cagr": old_best["cagr"],
            "reference_plus8000_mdd": old_best["max_drawdown"],
            "same_selector_stack_as_plus8000": "1",
            "same_replay_capital_path_as_plus8000": "1",
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


def write_report(closeout: dict[str, object], metrics: list[dict[str, object]], comparison: list[dict[str, object]], coverage: list[dict[str, object]]) -> None:
    metric_lines = "\n".join(
        f"- `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in metrics
    )
    comparison_lines = "\n".join(
        f"- `{row['variant']}` ({row['scope']}): final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in comparison
    )
    coverage_lines = "\n".join(
        f"- `{row['metric_type']}` / `{row['metric']}`: {row['rows']}/{row['total_rows']} ({row['ratio']})."
        for row in coverage
    )
    REPORT.write_text(
        f"""# Task2321-2340 Plus8000 Brain Newdata Backtest

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Brain reference: `{closeout['brain_reference']}`.
- Candidate decision rows: {closeout['candidate_decision_rows']}.
- Overlay changed rows: {closeout['overlay_changed_rows']}.
- Best policy: `{closeout['best_policy_variant_id']}`.
- Best final equity: {closeout['best_final_equity']}.
- Best CAGR: {closeout['best_cagr']}.
- Best MDD: {closeout['best_max_drawdown']}.
- Reference +8000 final: {closeout['reference_plus8000_final']}.
- Same selector stack as +8000: `{closeout['same_selector_stack_as_plus8000']}`.
- Same replay capital path as +8000: `{closeout['same_replay_capital_path_as_plus8000']}`.
- Strict raw/as-of complete: `{closeout['strict_raw_asof_complete']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task keeps the Task2191 +8000 selector/sizing/capital path and replaces only the API card/decision overlay with Task2251 full-source feature/proxy data. It does not rerun a new 3,100-candidate selector. Missing new data remains neutral, not negative.

Replay results:

{metric_lines}

Comparison:

{comparison_lines}

Overlay coverage:

{coverage_lines}

## No-Background Decision-Maker Report

Conclusion first: this is the intended test shape. It uses the +8000 brain and only changes the data overlay. It is still diagnostic because strict raw/as-of complete data is not solved.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2321_2340_plus8000_brain_newdata_backtest/`.
- Validator: `python scripts/trader_brain_2321_2340_plus8000_brain_newdata_backtest_validate.py`.

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
    for task_no in range(2321, 2341):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Plus8000 Brain Newdata Backtest Step {task_no}",
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "feature-proxy-ready-raw-asof-incomplete",
                "parent_task": f"Task{task_no - 1}" if task_no > 2321 else "Task2320",
                "key_report": "docs/reports/task_2321_2340_plus8000_brain_newdata_backtest/task_2321_2340_plus8000_brain_newdata_backtest.md",
                "key_decision": "docs/reports/task_2321_2340_plus8000_brain_newdata_backtest/task_2321_2340_decision.csv",
                "key_artifacts": "data/artifacts/task_2321_2340_plus8000_brain_newdata_backtest",
                "validation_command": "python scripts/trader_brain_2321_2340_plus8000_brain_newdata_backtest_validate.py",
                "notes": "Keeps Task2191 +8000 selector/sizing/capital path and applies Task2251 new feature/proxy overlay.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "115. Task2321-Task2340"
    if marker in text:
        return
    line = (
        f"115. Task2321-Task2340 ran the intended +8000-brain plus new-data diagnostic: Task2191 selector/sizing/capital "
        f"path kept fixed, Task2251 feature/proxy overlay applied. Best `{closeout['best_policy_variant_id']}` final "
        f"{closeout['best_final_equity']} CAGR {closeout['best_cagr']} MDD {closeout['best_max_drawdown']}; strict raw/as-of "
        f"complete remains 0. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    old_inputs = plus8000.load_inputs()
    new_inputs, cards, decisions, audit = overlay_inputs(old_inputs)
    guard_rows, trades, equity, metrics = run_plus8000_guard(new_inputs)
    coverage = coverage_rows(audit)
    comparison = comparison_rows(metrics)
    closeout = closeout_rows(metrics, coverage, audit)

    write_csv(OUT_DIR / "task2321_experiment_contract.csv", [
        {
            "task_id": "Task2321",
            "brain_reference": "Task2191_api_dd_guard_winner_preserve_top2_v1",
            "source_selector_policy": plus8000.SOURCE_POLICY,
            "candidate_decision_rows": len(audit),
            "same_selector_stack_as_plus8000": "1",
            "same_replay_capital_path_as_plus8000": "1",
            "new_data_source": "data/artifacts/task_2251_2280_plus8000_full_source_acquisition/task2256_recomputed_plus8000_feature_panel.csv",
            "strict_raw_asof_complete": "0",
            "authority": AUTHORITY,
        }
    ])
    write_csv(OUT_DIR / "task2322_newdata_l4_cards.csv", cards)
    write_csv(OUT_DIR / "task2323_newdata_l5_decisions.csv", decisions)
    write_csv(OUT_DIR / "task2324_overlay_audit.csv", audit)
    write_csv(OUT_DIR / "task2325_guard_rows.csv", guard_rows)
    write_csv(OUT_DIR / "task2326_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task2327_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task2328_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task2329_overlay_coverage.csv", coverage)
    write_csv(OUT_DIR / "task2330_comparison_matrix.csv", comparison)
    write_csv(OUT_DIR / "task2340_closeout.csv", closeout)
    write_json(OUT_DIR / "task2340_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], metrics, comparison, coverage)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2321_2340_PLUS8000_BRAIN_NEWDATA_BACKTEST_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
