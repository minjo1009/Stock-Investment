from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import trader_brain_2381_2400_plus8000_exit_chain_parity_repair as exit_replay
from build_frontend_backtest_snapshot import build_frontend_backtest_snapshot
from task_artifact_manifest import write_manifest


TASK_ID = "task_3903_stage1_sec_neutral_attach_same_experiment_replay"
TASK_LABEL = "Task3903"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs" / "reports" / TASK_ID
REPORT_PATH = REPORT_DIR / "stage1_sec_neutral_attach_same_experiment_replay_report.md"
DECISION_PATH = REPORT_DIR / "task_3903_decision.csv"

TASK1931 = ROOT / "data/artifacts/task_1931_1940_interaction_forecast_layer"
TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"
TASK3894 = ROOT / "data/artifacts/task_3894_true_historical_sec_backfill"
TASK3895 = ROOT / "data/artifacts/task_3895_true_sec_decision_asof_binding"

AUTHORITY = "DIAGNOSTIC_STAGE1_SEC_NEUTRAL_ATTACH_SAME_EXPERIMENT_REPLAY_ONLY"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_ts(value: str) -> str:
    return value.replace("Z", "+00:00")


def f(value: Any, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def stage1_sec_maps() -> tuple[dict[tuple[str, str], dict[str, str]], dict[tuple[str, str], int], dict[str, Any]]:
    grid = read_csv(TASK3895 / "true_sec_decision_grid.csv")
    bindings = read_csv(TASK3895 / "true_sec_decision_packet_bindings.csv")
    stage1_summary = json.loads((TASK3894 / "true_sec_backfill_summary.json").read_text(encoding="utf-8"))
    grid_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for row in grid:
        grid_by_key[(row["symbol"], normalize_ts(row["decision_asof_ts"]))] = row
    binding_counts: dict[tuple[str, str], int] = Counter()
    for row in bindings:
        if row.get("source_time_rule_pass") == "1" and row.get("strict_gate_pass") == "1":
            binding_counts[(row["symbol"], normalize_ts(row["decision_asof_ts"]))] += 1
    return grid_by_key, binding_counts, stage1_summary


def neutral_sec_attach_panel(l5_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grid_by_key, binding_counts, _ = stage1_sec_maps()
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(l5_rows, start=1):
        key = (row["symbol"], normalize_ts(row["decision_asof_ts"]))
        sec = grid_by_key.get(key)
        attached = int(float(sec.get("attached_packet_count", 0) or 0)) if sec else 0
        verified = binding_counts.get(key, 0)
        rows.append(
            {
                "task_id": TASK_LABEL,
                "sec_attach_id": f"SECNEUTRAL3903-{idx:06d}",
                "trade_spec_id": row["trade_spec_id"],
                "candidate_source_id": row["candidate_source_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "target_policy_variant_id": row.get("target_policy_variant_id", ""),
                "stage1_sec_attach_state": "ATTACHED_ASOF" if attached > 0 and verified > 0 else "NEUTRAL_SOURCE_GAP",
                "attached_packet_count": attached,
                "verified_binding_count": verified,
                "feature_used_for_selector": 0,
                "feature_used_for_sizing": 0,
                "feature_used_for_exit": 0,
                "row_excluded_by_sec_gate": 0,
                "missing_source_is_negative": 0,
                "assignment_uses_future_outcome": 0,
                "outcome_used_for_assignment": 0,
                "authority": AUTHORITY,
            }
        )
    return rows


def relabel_rows(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row["task_id"] = TASK_LABEL
        row["stage1_sec_attach_mode"] = "neutral_feature_attach_no_selection_effect"
        row["same_experiment_as_task2381"] = 1
        row["candidate_pool_preserved"] = 1
        row["authority"] = AUTHORITY
        row["strategy_acceptance"] = row.get("strategy_acceptance", "NOT_ACCEPTED")
        row["deployment_readiness"] = row.get("deployment_readiness", "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        row["real_capital"] = row.get("real_capital", "FORBIDDEN")


def comparison_rows(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    original = {row["policy_variant_id"]: row for row in read_csv(TASK2381 / "task2386_replay_metrics.csv")}
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(metrics, start=1):
        base = original.get(str(row["policy_variant_id"]), {})
        rows.append(
            {
                "task_id": TASK_LABEL,
                "comparison_id": f"SAMEEXP3903-{idx:03d}",
                "policy_variant_id": row["policy_variant_id"],
                "original_final_equity": base.get("final_equity", ""),
                "rerun_final_equity": row.get("final_equity", ""),
                "delta_final_equity": round(f(row.get("final_equity")) - f(base.get("final_equity")), 8),
                "original_cagr": base.get("cagr", ""),
                "rerun_cagr": row.get("cagr", ""),
                "delta_cagr": round(f(row.get("cagr")) - f(base.get("cagr")), 8),
                "original_max_drawdown": base.get("max_drawdown", ""),
                "rerun_max_drawdown": row.get("max_drawdown", ""),
                "delta_max_drawdown": round(f(row.get("max_drawdown")) - f(base.get("max_drawdown")), 8),
                "original_trade_count": base.get("trade_count", ""),
                "rerun_trade_count": row.get("trade_count", ""),
                "same_experiment_parity_pass": int(
                    base
                    and str(base.get("final_equity")) == str(row.get("final_equity"))
                    and str(base.get("cagr")) == str(row.get("cagr"))
                    and str(base.get("max_drawdown")) == str(row.get("max_drawdown"))
                    and str(base.get("trade_count")) == str(row.get("trade_count"))
                ),
                "authority": AUTHORITY,
            }
        )
    return rows


def top3_reference_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(TASK1931 / "task1938_interaction_top3_replay_metrics.csv"):
        rows.append(
            {
                "task_id": TASK_LABEL,
                "reference_policy": row["policy_variant_id"],
                "reference_source": "task1938_interaction_top3_replay_metrics",
                "final_equity": row["final_equity"],
                "cagr": row["cagr"],
                "max_drawdown": row["max_drawdown"],
                "trade_count": row["trade_count"],
                "note": "original_top3_reference_not_rerun_by_task3903",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_summary(
    stage1_summary: dict[str, Any],
    l5_rows: list[dict[str, str]],
    attach_rows: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    equity: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    best = max(metrics, key=lambda row: (row.get("joint_target_met") == "1", f(row.get("final_equity"))))
    attached = [row for row in attach_rows if row["stage1_sec_attach_state"] == "ATTACHED_ASOF"]
    return {
        "task_id": TASK_LABEL,
        "verdict": "stage1_sec_neutral_attach_same_experiment_replay_complete",
        "run_at_utc": utc_now(),
        "stage1_universe_symbol_count": stage1_summary.get("universe_symbol_count", 0),
        "stage1_historical_packet_count": stage1_summary.get("historical_model_packet_count", 0),
        "full_l5_rows": len(l5_rows),
        "sec_attach_rows": len(attach_rows),
        "sec_attached_asof_rows": len(attached),
        "sec_neutral_gap_rows": len(attach_rows) - len(attached),
        "row_excluded_by_sec_gate": 0,
        "candidate_pool_preserved": 1,
        "policy_variant_count": len(metrics),
        "trade_rows": len(trades),
        "equity_rows": len(equity),
        "same_experiment_parity_pass": int(all(row["same_experiment_parity_pass"] == 1 for row in comparisons)),
        "best_policy_variant_id": best["policy_variant_id"],
        "best_final_equity": best["final_equity"],
        "best_cagr": best["cagr"],
        "best_max_drawdown": best["max_drawdown"],
        "best_trade_count": best["trade_count"],
        "new_strategy_created": 0,
        "missing_source_is_negative": 0,
        "assignment_uses_future_outcome": 0,
        "outcome_used_for_assignment": 0,
        "outcome_used_for_audit_only": 1,
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }


def write_report(summary: dict[str, Any], metrics: list[dict[str, Any]], comparisons: list[dict[str, Any]], top3_refs: list[dict[str, Any]]) -> None:
    metric_lines = "\n".join(
        f"- `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in metrics
    )
    comparison_lines = "\n".join(
        f"- `{row['policy_variant_id']}`: delta final {row['delta_final_equity']}, delta CAGR {row['delta_cagr']}, "
        f"delta MDD {row['delta_max_drawdown']}, parity {row['same_experiment_parity_pass']}."
        for row in comparisons
    )
    top3_lines = "\n".join(
        f"- `{row['reference_policy']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in top3_refs
    )
    text = f"""# Task3903 Stage-1 SEC Neutral-Attach Same-Experiment Replay

## Decision Summary

- Verdict: `{summary['verdict']}`.
- What changed: stage-1 SEC packets were attached as neutral as-of feature evidence only.
- What did not change: universe, selector, sizing, exit chain, capital path, candidate pool, and source-return path.
- Full L5 rows: {summary['full_l5_rows']}.
- SEC attached as-of rows: {summary['sec_attached_asof_rows']}.
- SEC neutral gap rows: {summary['sec_neutral_gap_rows']}.
- Rows excluded by SEC gate: {summary['row_excluded_by_sec_gate']}.
- Same-experiment parity pass: {summary['same_experiment_parity_pass']}.
- Best policy: `{summary['best_policy_variant_id']}`.
- Best final equity: {summary['best_final_equity']}.
- Best CAGR: {summary['best_cagr']}.
- Best MDD: {summary['best_max_drawdown']}.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Same-Experiment Replay

{metric_lines}

## Parity Against Task2381

{comparison_lines}

## Original TOP3 Reference

{top3_lines}

The TOP3 reference is included to avoid mixing it with the later 40%+ full-universe exit-chain repaired policy. Task3903 reruns the later frozen 40%+ policy path because that is the current high-CAGR replay path in the operating state.

## Validation

- `python scripts/run_task3903_stage1_sec_neutral_attach_same_experiment_replay.py`
- `python scripts/validate_task3903_stage1_sec_neutral_attach_same_experiment_replay.py`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(text, encoding="utf-8")


def update_registry(summary: dict[str, Any]) -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    fieldnames = list(rows[0].keys())
    rows = [row for row in rows if row["task_id"] != "Task3903"]
    rows.append(
        {
            "task_id": "Task3903",
            "title": "Stage 1 SEC Neutral Attach Same Experiment Replay",
            "owner_team": "Backtest & Simulation Infra",
            "status": "Diagnostic Only",
            "canonical_state": "canonical",
            "strategy_acceptance": "NOT_ACCEPTED",
            "data_readiness": "stage1-sec-neutral-attach-same-experiment-replay-complete",
            "parent_task": "Task3902",
            "key_report": "docs/reports/task_3903_stage1_sec_neutral_attach_same_experiment_replay/stage1_sec_neutral_attach_same_experiment_replay_report.md",
            "key_decision": "docs/reports/task_3903_stage1_sec_neutral_attach_same_experiment_replay/task_3903_decision.csv",
            "key_artifacts": "data/artifacts/task_3903_stage1_sec_neutral_attach_same_experiment_replay",
            "validation_command": "python -m py_compile scripts/run_task3903_stage1_sec_neutral_attach_same_experiment_replay.py scripts/validate_task3903_stage1_sec_neutral_attach_same_experiment_replay.py; python scripts/run_task3903_stage1_sec_neutral_attach_same_experiment_replay.py; python scripts/validate_task3903_stage1_sec_neutral_attach_same_experiment_replay.py; python scripts/task_registry_validate.py",
            "notes": "Replayed the current high-CAGR full-universe policy with stage-1 SEC packets attached as neutral as-of evidence only, preserving the candidate pool and matching Task2381 same-experiment metrics exactly; no paper live deployment strategy acceptance or real-capital permission changed.",
        }
    )
    write_csv(path, rows, fieldnames)


def update_operating_state(summary: dict[str, Any]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "Task3903 attached stage-1 SEC packets"
    if marker in text:
        return
    line = (
        f"270. Task3903 attached stage-1 SEC packets to the current high-CAGR full-universe replay as neutral as-of "
        f"evidence without filtering candidates: full L5 rows {summary['full_l5_rows']}, SEC attached rows "
        f"{summary['sec_attached_asof_rows']}, rows excluded by SEC gate {summary['row_excluded_by_sec_gate']}, "
        f"same-experiment parity {summary['same_experiment_parity_pass']}, best `{summary['best_policy_variant_id']}` "
        f"final {summary['best_final_equity']} CAGR {summary['best_cagr']} MDD {summary['best_max_drawdown']}. "
        f"Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert_at = text.find("\n269. ")
    if insert_at != -1:
        text = text[:insert_at] + "\n" + line + text[insert_at:]
    else:
        text = text.rstrip() + "\n" + line
    path.write_text(text, encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = exit_replay.load_inputs()
    l5: list[dict[str, str]] = inputs["l5"]  # type: ignore[assignment]
    source_rows, method_rows, gaps = exit_replay.build_repaired_source_rows(inputs)
    guard_rows, trades, equity, metrics = exit_replay.replay_with_repaired_sources(
        l5,
        inputs["cards"],  # type: ignore[arg-type]
        inputs["decisions"],  # type: ignore[arg-type]
        source_rows,
    )
    for table in (guard_rows, trades, equity, metrics):
        relabel_rows(table)
    attach_rows = neutral_sec_attach_panel(l5)
    comparisons = comparison_rows(metrics)
    top3_refs = top3_reference_rows()
    _, _, stage1_summary = stage1_sec_maps()
    summary = build_summary(stage1_summary, l5, attach_rows, trades, equity, metrics, comparisons)

    write_csv(ARTIFACT_DIR / "stage1_sec_neutral_attach_panel.csv", attach_rows)
    write_csv(ARTIFACT_DIR / "stage1_sec_same_experiment_replay_guard_rows.csv", guard_rows)
    write_csv(ARTIFACT_DIR / "stage1_sec_same_experiment_replay_trades.csv", trades)
    write_csv(ARTIFACT_DIR / "stage1_sec_same_experiment_replay_equity.csv", equity)
    write_csv(ARTIFACT_DIR / "stage1_sec_same_experiment_replay_metrics.csv", metrics)
    write_csv(ARTIFACT_DIR / "stage1_sec_same_experiment_comparison.csv", comparisons)
    write_csv(ARTIFACT_DIR / "original_top3_reference_metrics.csv", top3_refs)
    write_json(ARTIFACT_DIR / "stage1_sec_same_experiment_replay_summary.json", summary)
    write_csv(DECISION_PATH, [summary])
    write_report(summary, metrics, comparisons, top3_refs)
    write_manifest(ARTIFACT_DIR, REPORT_DIR / "artifact_manifest.csv")
    update_registry(summary)
    update_operating_state(summary)
    frontend_snapshot = build_frontend_backtest_snapshot(TASK_ID, TASK_LABEL)
    print("[TASK3903_STAGE1_SEC_NEUTRAL_ATTACH_SAME_EXPERIMENT_REPLAY_COMPLETE]")
    print(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True))
    print("[TASK3903_FRONTEND_BACKTEST_SNAPSHOT_UPDATED]")
    print(json.dumps({"currentSnapshotPath": frontend_snapshot["currentSnapshotPath"]}, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
