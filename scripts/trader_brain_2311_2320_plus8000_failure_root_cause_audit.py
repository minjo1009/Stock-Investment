from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2311_2320_plus8000_failure_root_cause_audit"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2311_2320_plus8000_failure_root_cause_audit.md"
DECISION = REPORT_DIR / "task_2311_2320_decision.csv"

AUTHORITY = "DIAGNOSTIC_PLUS8000_FAILURE_ROOT_CAUSE_AUDIT_ONLY"

TASK1717 = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
TASK2151 = ROOT / "data/artifacts/task_2151_2180_api_three_loop_hardening"
TASK2191 = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"
TASK2251 = ROOT / "data/artifacts/task_2251_2280_plus8000_full_source_acquisition"
TASK2281 = ROOT / "data/artifacts/task_2281_2290_post_acquisition_parity"
TASK2291 = ROOT / "data/artifacts/task_2291_2310_plus8000_feature_full_universe_backtest"


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
    try:
        if value in {"", None, "None", "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def key(row: dict[str, str]) -> tuple[str, str]:
    return row.get("symbol", ""), row.get("decision_asof_ts", "")[:10]


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "t1717_trades": read_csv(TASK1717 / "task1704_bad_trade_gate_replay_trades.csv"),
        "t1717_metrics": read_csv(TASK1717 / "task1705_bad_trade_gate_replay_metrics.csv"),
        "t2151_trades": read_csv(TASK2151 / "task2173_api_three_loop_replay_trades.csv"),
        "t2151_metrics": read_csv(TASK2151 / "task2175_api_three_loop_replay_metrics.csv"),
        "t2191_trades": read_csv(TASK2191 / "task2194_guard_replay_trades.csv"),
        "t2191_metrics": read_csv(TASK2191 / "task2196_guard_replay_metrics.csv"),
        "t2251_coverage": read_csv(TASK2251 / "task2255_post_acquisition_coverage_summary.csv"),
        "t2281_summary": read_csv(TASK2281 / "task2284_post_acquisition_parity_summary.csv"),
        "t2291_features": read_csv(TASK2291 / "task2296_plus8000_feature_panel.csv"),
        "t2291_trades": read_csv(TASK2291 / "task2298_replay_trades.csv"),
        "t2291_metrics": read_csv(TASK2291 / "task2300_replay_metrics.csv"),
        "t2291_coverage": read_csv(TASK2291 / "task2292_source_proxy_coverage.csv"),
    }


def policy_rows(metrics: list[dict[str, str]], label: str) -> list[dict[str, object]]:
    rows = []
    for row in metrics:
        rows.append(
            {
                "experiment": label,
                "policy_variant_id": row.get("policy_variant_id", ""),
                "source_policy_variant_id": row.get("source_policy_variant_id", ""),
                "baseline_policy_variant_id": row.get("baseline_policy_variant_id", ""),
                "final_equity": row.get("final_equity", ""),
                "cagr": row.get("cagr", ""),
                "max_drawdown": row.get("max_drawdown", ""),
                "trade_count": row.get("trade_count", ""),
                "authority": AUTHORITY,
            }
        )
    return rows


def overlap_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    current_policies = sorted({row["policy_variant_id"] for row in inputs["t2291_trades"]})
    references = [
        ("task1717_bad_trade_gate", inputs["t1717_trades"]),
        ("task2151_api_loop3", inputs["t2151_trades"]),
        ("task2191_api_dd_guard", inputs["t2191_trades"]),
    ]
    out: list[dict[str, object]] = []
    idx = 1
    for cur_policy in current_policies:
        cur_set = {key(row) for row in inputs["t2291_trades"] if row["policy_variant_id"] == cur_policy}
        for ref_name, ref_rows in references:
            for ref_policy in sorted({row["policy_variant_id"] for row in ref_rows}):
                ref_set = {key(row) for row in ref_rows if row["policy_variant_id"] == ref_policy}
                if not cur_set or not ref_set:
                    continue
                inter = cur_set & ref_set
                out.append(
                    {
                        "task_id": "Task2312",
                        "overlap_id": f"ROOTOVERLAP2312-{idx:04d}",
                        "current_policy": cur_policy,
                        "reference_experiment": ref_name,
                        "reference_policy": ref_policy,
                        "current_trade_keys": len(cur_set),
                        "reference_trade_keys": len(ref_set),
                        "overlap_trade_keys": len(inter),
                        "overlap_pct_current": round(len(inter) / len(cur_set), 6),
                        "overlap_pct_reference": round(len(inter) / len(ref_set), 6),
                        "match_method": "symbol_plus_decision_date_for_diagnostic_overlap_only_not_assignment",
                        "authority": AUTHORITY,
                    }
                )
                idx += 1
    return out


def common_trade_bridge(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    current_policy = "plus8000_feature_full_top2_v1"
    cur = {key(row): row for row in inputs["t2291_trades"] if row["policy_variant_id"] == current_policy}
    rows: list[dict[str, object]] = []
    references = [
        ("Task2151_api_loop3_guarded", "api_loop3_guarded_risk_cap_top2_v1", inputs["t2151_trades"]),
        ("Task2191_api_dd_winner_preserve", "api_dd_guard_winner_preserve_top2_v1", inputs["t2191_trades"]),
    ]
    idx = 1
    for reference_experiment, reference_policy, reference_rows in references:
        ref = {key(row): row for row in reference_rows if row["policy_variant_id"] == reference_policy}
        for k in sorted(set(cur) & set(ref)):
            c = cur[k]
            r = ref[k]
            rows.append(
                {
                    "task_id": "Task2313",
                    "bridge_id": f"ROOTBRIDGE2313-{idx:04d}",
                    "symbol": k[0],
                    "decision_date": k[1],
                    "current_policy": current_policy,
                    "reference_experiment": reference_experiment,
                    "reference_policy": reference_policy,
                    "current_capital_allocated": c.get("capital_allocated", ""),
                    "reference_capital_allocated": r.get("capital_allocated", ""),
                    "current_net_return": c.get("net_return", ""),
                    "reference_net_return": r.get("net_return", ""),
                    "current_pnl": c.get("pnl", ""),
                    "reference_pnl": r.get("pnl", ""),
                    "delta_pnl_current_minus_reference": round(f(c.get("pnl")) - f(r.get("pnl")), 6),
                    "delta_capital_current_minus_reference": round(f(c.get("capital_allocated")) - f(r.get("capital_allocated")), 6),
                    "same_trade_key_diagnostic_only": "1",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def selection_failure_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    features = {
        (
            row["candidate_source_id"],
            row["trade_spec_id"],
            row["symbol"],
            row["decision_asof_ts"],
        ): row
        for row in inputs["t2291_features"]
    }
    rows: list[dict[str, object]] = []
    losses = sorted(
        [row for row in inputs["t2291_trades"] if row["policy_variant_id"] == "plus8000_feature_full_top2_v1" and f(row.get("pnl")) < 0],
        key=lambda row: f(row.get("pnl")),
    )[:25]
    for idx, row in enumerate(losses, start=1):
        feat = features.get((row["candidate_source_id"], row["trade_spec_id"], row["symbol"], row["decision_asof_ts"]), {})
        rows.append(
            {
                "task_id": "Task2314",
                "failure_id": f"ROOTFAIL2314-{idx:04d}",
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "rank_within_decision": row.get("latest_brain_rank_within_decision", ""),
                "pnl": row.get("pnl", ""),
                "net_return": row.get("net_return", ""),
                "capital_allocated": row.get("capital_allocated", ""),
                "payoff_quality_bucket": feat.get("payoff_quality_bucket", ""),
                "payoff_quality_score": feat.get("payoff_quality_score", ""),
                "collapse_risk_bucket": feat.get("collapse_risk_bucket", ""),
                "collapse_risk_score": feat.get("collapse_risk_score", ""),
                "thesis_state": feat.get("thesis_state", ""),
                "entry_gate_state": feat.get("entry_gate_state", ""),
                "plus8000_api_proxy_state": feat.get("plus8000_api_proxy_state", ""),
                "plus8000_api_proxy_score": feat.get("plus8000_api_proxy_score", ""),
                "latest_brain_rank_score": feat.get("latest_brain_rank_score", ""),
                "root_cause_tag": "bad_trade_ranked_as_good_before_sizing",
                "authority": AUTHORITY,
            }
        )
    return rows


def coverage_rows(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    for row in inputs["t2291_coverage"]:
        rows.append(
            {
                "task_id": "Task2315",
                "coverage_id": f"ROOTCOVER2315-{idx:04d}",
                "source": "task2291_replay_coverage",
                "metric": row.get("source_family", ""),
                "candidate_rows": row.get("candidate_rows", ""),
                "covered_rows": row.get("exact_covered_rows", ""),
                "coverage_ratio": row.get("coverage_ratio", ""),
                "interpretation": "selection_power_sparse" if row.get("source_family") in {"earnings_surprise_proxy", "rating_proxy", "strict_raw_asof_replay_gate_reference_only"} else "broad_but_low_specificity_proxy",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def cause_rows(inputs: dict[str, list[dict[str, str]]], overlap: list[dict[str, object]], bridge: list[dict[str, object]], failures: list[dict[str, object]]) -> list[dict[str, object]]:
    current_top2 = next(row for row in inputs["t2291_metrics"] if row["policy_variant_id"] == "plus8000_feature_full_top2_v1")
    plus8000 = next(row for row in inputs["t2151_metrics"] if row["policy_variant_id"] == "api_loop3_guarded_risk_cap_top2_v1")
    common_2191 = [row for row in bridge if row["reference_experiment"] == "Task2191_api_dd_winner_preserve"]
    current_common_pnl = sum(f(row["current_pnl"]) for row in common_2191)
    reference_common_pnl = sum(f(row["reference_pnl"]) for row in common_2191)
    bad_good = sum(1 for row in failures if row["payoff_quality_bucket"] in {"top3_payoff_candidate", "eligible_payoff_candidate"} and row["collapse_risk_bucket"] == "ordinary_pass")
    return [
        {
            "task_id": "Task2316",
            "cause_rank": 1,
            "cause": "not_same_experiment",
            "evidence": "Task2151/2191 use SOURCE_POLICY winner_defense_budget_top5_v1 selected-trade universe; Task2291 reselects from 3100 using Task2201-style full replay plus proxy adjustment.",
            "severity": "critical",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2316",
            "cause_rank": 2,
            "cause": "exact_sizing_engine_not_reused",
            "evidence": f"Common Task2191-overlap trades: current pnl {round(current_common_pnl, 4)} vs Task2191 pnl {round(reference_common_pnl, 4)}; capital path, cap multiplier, and exit/return path differ materially.",
            "severity": "critical",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2316",
            "cause_rank": 3,
            "cause": "bad_trades_ranked_good_before_sizing",
            "evidence": f"{bad_good}/{len(failures)} worst top2 losses were marked eligible/top3 payoff and ordinary_pass collapse.",
            "severity": "high",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2316",
            "cause_rank": 4,
            "cause": "broad_proxy_not_selection_power",
            "evidence": "Feature proxy coverage is broad, but earnings_surprise_proxy and rating_proxy coverage are sparse; supportive/mixed proxy states did not distinguish near-term losers.",
            "severity": "high",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task2316",
            "cause_rank": 5,
            "cause": "concentration_amplifies_selector_errors",
            "evidence": f"Task2291 top2 final {current_top2['final_equity']} MDD {current_top2['max_drawdown']} vs Task2151 final {plus8000['final_equity']} MDD {plus8000['max_drawdown']}.",
            "severity": "medium",
            "authority": AUTHORITY,
        },
    ]


def closeout_rows(inputs: dict[str, list[dict[str, str]]], bridge: list[dict[str, object]]) -> list[dict[str, object]]:
    current = next(row for row in inputs["t2291_metrics"] if row["policy_variant_id"] == "plus8000_feature_full_top2_v1")
    ref = next(row for row in inputs["t2191_metrics"] if row["policy_variant_id"] == "api_dd_guard_winner_preserve_top2_v1")
    common_2191 = [row for row in bridge if row["reference_experiment"] == "Task2191_api_dd_winner_preserve"]
    return [
        {
            "task_id": "Task2320",
            "verdict": "root_cause_not_same_experiment_plus_selector_and_sizing_path_break",
            "current_top2_final": current["final_equity"],
            "current_top2_cagr": current["cagr"],
            "current_top2_mdd": current["max_drawdown"],
            "reference_plus8000_final": ref["final_equity"],
            "reference_plus8000_cagr": ref["cagr"],
            "reference_plus8000_mdd": ref["max_drawdown"],
            "common_trade_count": len(common_2191),
            "primary_cause": "Task2291 did not exact-replay the +8000 selector/sizing stack; it ran a new full-universe selector and different capital path.",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], policies: list[dict[str, object]], causes: list[dict[str, object]], coverage: list[dict[str, object]], failures: list[dict[str, object]]) -> None:
    policy_lines = "\n".join(
        f"- `{row['experiment']}` / `{row['policy_variant_id']}`: final {row['final_equity']}, CAGR {row['cagr']}, MDD {row['max_drawdown']}, trades {row['trade_count']}."
        for row in policies
    )
    cause_lines = "\n".join(
        f"- {row['cause_rank']}. `{row['cause']}`: {row['evidence']}"
        for row in causes
    )
    coverage_lines = "\n".join(
        f"- `{row['metric']}`: {row['covered_rows']}/{row['candidate_rows']} ({row['coverage_ratio']}) - {row['interpretation']}."
        for row in coverage
    )
    failure_lines = "\n".join(
        f"- {row['symbol']} {str(row['decision_asof_ts'])[:10]}: rank {row['rank_within_decision']}, pnl {row['pnl']}, payoff `{row['payoff_quality_bucket']}`, collapse `{row['collapse_risk_bucket']}`, proxy `{row['plus8000_api_proxy_state']}`."
        for row in failures[:12]
    )
    REPORT.write_text(
        f"""# Task2311-2320 Plus8000 Failure Root Cause Audit

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Current Task2291 top2: final {closeout['current_top2_final']}, CAGR {closeout['current_top2_cagr']}, MDD {closeout['current_top2_mdd']}.
- Reference Task2151 +8000: final {closeout['reference_plus8000_final']}, CAGR {closeout['reference_plus8000_cagr']}, MDD {closeout['reference_plus8000_mdd']}.
- Common trade count: {closeout['common_trade_count']}.
- Primary cause: {closeout['primary_cause']}.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Experiment metrics:

{policy_lines}

Root-cause ranking:

{cause_lines}

Data coverage interpretation:

{coverage_lines}

Worst top2 selection failures:

{failure_lines}

## No-Background Decision-Maker Report

Conclusion first: the +8000 result and the new full-universe replay are not the same experiment. The old result proved that a prefiltered winner-defense basket plus aggressive sizing could compound well. The new result tested a different full-universe selector and a different capital path. Therefore the failure is not explained by data volume alone; it is a stack mismatch plus unresolved selector weakness.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2311_2320_plus8000_failure_root_cause_audit/`.
- Validator: `python scripts/trader_brain_2311_2320_plus8000_failure_root_cause_audit_validate.py`.

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
    for task_no in range(2311, 2321):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Plus8000 Failure Root Cause Audit Step {task_no}",
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "feature-proxy-ready-raw-asof-incomplete",
                "parent_task": f"Task{task_no - 1}" if task_no > 2311 else "Task2310",
                "key_report": "docs/reports/task_2311_2320_plus8000_failure_root_cause_audit/task_2311_2320_plus8000_failure_root_cause_audit.md",
                "key_decision": "docs/reports/task_2311_2320_plus8000_failure_root_cause_audit/task_2311_2320_decision.csv",
                "key_artifacts": "data/artifacts/task_2311_2320_plus8000_failure_root_cause_audit",
                "validation_command": "python scripts/trader_brain_2311_2320_plus8000_failure_root_cause_audit_validate.py",
                "notes": "Diagnostic root-cause audit separating +8000 selected-trade sizing, full-universe selector, proxy data, and capital path effects.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "114. Task2311-Task2320"
    if marker in text:
        return
    line = (
        f"114. Task2311-Task2320 audited the +8000 vs Task2291 failure. Verdict `{closeout['verdict']}`: "
        f"the old +8000 result and new full-universe replay were not the same experiment; main causes are "
        f"selector/sizing stack mismatch, different capital path, broad low-specificity proxy data, and bad "
        f"trades ranked as good before sizing. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    policies = (
        policy_rows(inputs["t1717_metrics"], "Task1717_full_universe_prior")
        + policy_rows(inputs["t2151_metrics"], "Task2151_selected_trade_plus8000")
        + policy_rows(inputs["t2191_metrics"], "Task2191_selected_trade_dd_guard")
        + policy_rows(inputs["t2291_metrics"], "Task2291_full_universe_proxy")
    )
    overlap = overlap_rows(inputs)
    bridge = common_trade_bridge(inputs)
    failures = selection_failure_rows(inputs)
    coverage = coverage_rows(inputs)
    causes = cause_rows(inputs, overlap, bridge, failures)
    closeout = closeout_rows(inputs, bridge)

    write_csv(OUT_DIR / "task2311_experiment_metric_lineage.csv", policies)
    write_csv(OUT_DIR / "task2312_trade_overlap_matrix.csv", overlap)
    write_csv(OUT_DIR / "task2313_common_trade_pnl_bridge.csv", bridge)
    write_csv(OUT_DIR / "task2314_selection_failure_snapshot.csv", failures)
    write_csv(OUT_DIR / "task2315_data_coverage_signal_quality.csv", coverage)
    write_csv(OUT_DIR / "task2316_root_cause_ranking.csv", causes)
    write_csv(OUT_DIR / "task2320_closeout.csv", closeout)
    write_json(OUT_DIR / "task2320_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(closeout[0], policies, causes, coverage, failures)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2311_2320_PLUS8000_FAILURE_ROOT_CAUSE_AUDIT_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
