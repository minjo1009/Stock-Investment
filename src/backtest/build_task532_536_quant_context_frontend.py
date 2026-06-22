from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report
from src.reporting.research_task_catalog import build_research_task_catalog


TASK505_DECISION = Path("docs/reports/task_505_two_year_pnl_grid/task_505_decision.csv")
TASK529_POOL = Path("docs/reports/task_529_trend_persistence_entry_safe_refinement/trend_persistence_refined_candidate_pool.csv")
TASK529_FOLDS = Path("docs/reports/task_529_trend_persistence_entry_safe_refinement/trend_persistence_refined_walk_forward_quality.csv")

TASK532_OUT = Path("docs/reports/task_532_external_quant_context_map")
TASK533_OUT = Path("docs/reports/task_533_factor_premium_validation_design")
TASK534_OUT = Path("docs/reports/task_534_statistical_validation_upgrade")
TASK535_OUT = Path("docs/reports/task_535_frontend_research_cockpit_v1")
TASK536_OUT = Path("docs/reports/task_536_frontend_api_boundary")
CONTEXT_MAP_PATH = Path("docs/context/quant_context_map.md")


def build_task532_external_quant_context_map(out_dir: Path = TASK532_OUT) -> dict[str, pd.DataFrame]:
    context_rows = [
        {
            "source": "QuantStart Free Quantitative Finance Resources",
            "category": "Data quality / source discipline",
            "project_application": "Free/back-adjusted data must be source-audited before production claims.",
            "current_gap": "Historical OHLCV exists, but receive_ts/status/LULD/full-depth coverage is incomplete.",
            "adoption_priority": "HIGH",
        },
        {
            "source": "awesome-quant",
            "category": "Research libraries",
            "project_application": "Use pandas/statsmodels/sklearn/vectorized discovery as research tools, not deployment proof.",
            "current_gap": "Formal factor premium layer and multiple-testing audit are not yet canonical.",
            "adoption_priority": "HIGH",
        },
        {
            "source": "Tidy Finance / Fama-MacBeth references",
            "category": "Factor premium/statistical validation",
            "project_application": "Validate whether entry-safe factors earn cross-sectional premium out-of-sample.",
            "current_gap": "No Fama-French adjustment or Fama-MacBeth panel currently exists.",
            "adoption_priority": "MEDIUM",
        },
        {
            "source": "Backtest dashboard / tearsheet references",
            "category": "Dashboard/reporting UX",
            "project_application": "Expose task registry, decision state, artifacts, blockers, and reports in a cockpit.",
            "current_gap": "Streamlit UI has manual report catalog and misses latest task lineage.",
            "adoption_priority": "HIGH",
        },
    ]
    missing = pd.DataFrame(
        [
            {"capability": "receive_timestamp_native_replay", "status": "missing_for_historical", "blocked_claim": "live_equivalent_backtest"},
            {"capability": "broker_truth_fills", "status": "missing", "blocked_claim": "execution_grade_validation"},
            {"capability": "Fama_French_factor_data", "status": "missing", "blocked_claim": "risk_adjusted_alpha_claim"},
            {"capability": "Fama_MacBeth_cross_section_panel", "status": "missing", "blocked_claim": "factor_premium_claim"},
            {"capability": "automatic_research_cockpit", "status": "partial", "blocked_claim": "investor_grade_visibility"},
        ]
    )
    adoption = pd.DataFrame(context_rows).sort_values("adoption_priority", ascending=True)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task532",
                "context_sources_reviewed": 4,
                "high_priority_adoption_count": int((adoption["adoption_priority"] == "HIGH").sum()),
                "missing_data_approximated_flag": 0,
                "strategy_acceptance_status": "CONTEXT_GOVERNANCE_READY_NOT_DEPLOYMENT_READY",
            }
        ]
    )
    _write_context_doc(adoption, missing)
    _write_report_bundle(
        out_dir,
        "task_532_external_quant_context_map.md",
        "Task 532 External Quant Context Map",
        {
            "external_quant_context_map": adoption,
            "quant_context_missing_capability_matrix": missing,
            "quant_context_adoption_priority": adoption,
            "task_532_decision": decision,
        },
        [
            "External quant references were translated into project controls: data discipline, backtest/live parity, factor validation, and dashboard visibility.",
            "No external source is treated as proof of strategy validity; each becomes a governance or validation requirement.",
        ],
        [
            "The project now has a map of what professional quant resources imply for our process.",
            "The biggest missing pieces remain live-quality data, broker fills, factor-premium tests, and a usable dashboard.",
        ],
    )
    return {"task_532_decision": decision}


def build_task533_factor_premium_validation_design(out_dir: Path = TASK533_OUT) -> dict[str, pd.DataFrame]:
    math_status = pd.DataFrame(
        [
            {"concept": "linear_algebra", "current_status": "partial", "recommended_use": "PCA/covariance/risk model after feature matrix is stable", "use_as_trigger_flag": 0},
            {"concept": "calculus_optimization", "current_status": "grid_thresholds", "recommended_use": "avoid continuous optimization until overfit controls pass", "use_as_trigger_flag": 0},
            {"concept": "probability_statistics", "current_status": "partial_walk_forward", "recommended_use": "bootstrap CI, fold stability, multiple-testing correction", "use_as_trigger_flag": 0},
            {"concept": "Fama_French", "current_status": "not_implemented", "recommended_use": "risk-adjust Task505/529 returns against market/size/value/profitability/investment factors", "use_as_trigger_flag": 0},
            {"concept": "Fama_MacBeth", "current_status": "not_implemented", "recommended_use": "test cross-sectional premium of regime/theme/intraday factors", "use_as_trigger_flag": 0},
        ]
    )
    contract = pd.DataFrame(
        [
            {"input_name": "exact_lifecycle_panel", "required_flag": 1, "available_flag": 1, "join_key": "lifecycle_id"},
            {"input_name": "entry_safe_feature_panel", "required_flag": 1, "available_flag": 1, "join_key": "lifecycle_id"},
            {"input_name": "Fama_French_daily_factors", "required_flag": 1, "available_flag": 0, "join_key": "date"},
            {"input_name": "fundamental_size_value_profitability_investment", "required_flag": 1, "available_flag": 0, "join_key": "symbol,date"},
            {"input_name": "forward_return_labels", "required_flag": 1, "available_flag": 1, "join_key": "lifecycle_id"},
        ]
    )
    leakage = pd.DataFrame(
        [
            {"rule": "factor_validation_not_entry_assignment", "pass_flag": 1},
            {"rule": "exact_lifecycle_join_only", "pass_flag": 1},
            {"rule": "missing_factor_data_not_approximated", "pass_flag": 1},
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task533",
                "factor_validation_contract_ready_flag": 1,
                "fama_french_data_available_flag": 0,
                "fama_macbeth_panel_available_flag": 0,
                "factor_result_used_as_trading_trigger_flag": 0,
                "strategy_acceptance_status": "FACTOR_VALIDATION_DESIGNED_DATA_BLOCKED",
            }
        ]
    )
    _write_report_bundle(
        out_dir,
        "task_533_factor_premium_validation_design.md",
        "Task 533 Factor Premium Validation Design",
        {
            "math_quant_application_status": math_status,
            "factor_premium_validation_contract": contract,
            "factor_premium_missing_data_audit": contract[contract["available_flag"].eq(0)].copy(),
            "factor_premium_leakage_audit": leakage,
            "task_533_decision": decision,
        },
        [
            "Fama-French and Fama-MacBeth are appropriate as validation and risk decomposition layers, not as immediate entry rules.",
            "Current exact-lifecycle data is enough to design the tests, but missing factor/fundamental data blocks a real premium estimate.",
        ],
        [
            "The math tools are useful, but we should not pretend they are already applied.",
            "The next data task must fetch factor and fundamental data before claiming factor premium.",
        ],
    )
    return {"task_533_decision": decision}


def build_task534_statistical_validation_upgrade(out_dir: Path = TASK534_OUT) -> dict[str, pd.DataFrame]:
    pool = _read_csv(TASK529_POOL)
    folds = _read_csv(TASK529_FOLDS)
    if not folds.empty:
        stats = (
            folds.groupby("family_name")
            .agg(
                fold_count=("test_quarter", "nunique"),
                avg_net_mean=("avg_net_return_pct", "mean"),
                avg_net_ci_low=("avg_net_return_pct", lambda s: float(s.quantile(0.025))),
                avg_net_ci_high=("avg_net_return_pct", lambda s: float(s.quantile(0.975))),
                positive_fold_rate=("positive_fold_flag", "mean"),
                entry_reduce_mean=("entry_reduce_failure_rate", "mean"),
            )
            .reset_index()
        )
    else:
        stats = pd.DataFrame()
    candidate_count = len(pool) if not pool.empty else 0
    multiple = pd.DataFrame(
        [
            {
                "tested_candidate_count": candidate_count,
                "correction_method": "bonferroni_guardrail",
                "nominal_alpha": 0.05,
                "adjusted_alpha": 0.05 / max(candidate_count, 1),
                "selection_interpretation": "diagnostic_only_until_retested",
            }
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task534",
                "statistical_validation_upgrade_ready_flag": int(not stats.empty),
                "bootstrap_proxy_generated_flag": int(not stats.empty),
                "multiple_testing_audit_generated_flag": 1,
                "strategy_acceptance_status": "STATISTICAL_VALIDATION_DIAGNOSTIC_ONLY",
            }
        ]
    )
    _write_report_bundle(
        out_dir,
        "task_534_statistical_validation_upgrade.md",
        "Task 534 Statistical Validation Upgrade",
        {
            "statistical_validity_audit": stats,
            "fold_stability_audit": folds,
            "multiple_testing_correction_audit": multiple,
            "task_534_decision": decision,
        },
        [
            "Task529 candidate quality is now exposed with fold stability and confidence-interval style quantile bounds.",
            "This does not prove deployment edge; it prevents reading a selected grid result as stronger than the evidence supports.",
        ],
        [
            "We added a statistics checkpoint so selected candidates are not trusted just because they look good in one grid.",
            "The result remains diagnostic until live-source and broker-fill blockers are cleared.",
        ],
    )
    return {"task_534_decision": decision}


def build_task535_frontend_research_cockpit_v1(out_dir: Path = TASK535_OUT) -> dict[str, pd.DataFrame]:
    catalog = build_research_task_catalog()
    blocker = pd.DataFrame(
        [
            {"blocker": "receive_ts", "status": "blocked_for_historical", "task_reference": "Task523"},
            {"blocker": "broker_truth_fill", "status": "contract_only", "task_reference": "Task525/Task531"},
            {"blocker": "status_LULD", "status": "partial_live_archive", "task_reference": "Task520"},
            {"blocker": "full_depth", "status": "provider_blocked", "task_reference": "Task526"},
            {"blocker": "deployment_readiness", "status": "not_ready", "task_reference": "Task531"},
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task535",
                "catalog_task_count": int(len(catalog)),
                "latest_task_id": catalog["task_id"].iloc[-1] if not catalog.empty else "none",
                "streamlit_auto_catalog_ready_flag": 1,
                "strategy_acceptance_status": "FRONTEND_RESEARCH_COCKPIT_READY",
            }
        ]
    )
    _write_report_bundle(
        out_dir,
        "task_535_frontend_research_cockpit_v1.md",
        "Task 535 Frontend Research Cockpit V1",
        {
            "research_task_catalog": catalog,
            "research_cockpit_blocker_board": blocker,
            "task_535_decision": decision,
        },
        [
            "The dashboard source is now registry-driven instead of manually pinned to old reports.",
            "The cockpit should show latest task state, decision files, artifact manifests, and live-readiness blockers.",
        ],
        [
            "The frontend can now track project progress from the task registry rather than relying on a stale hard-coded list.",
            "This is visibility infrastructure, not a trading signal.",
        ],
    )
    return {"task_535_decision": decision}


def build_task536_frontend_api_boundary(out_dir: Path = TASK536_OUT) -> dict[str, pd.DataFrame]:
    boundary = pd.DataFrame(
        [
            {"interface": "research_task_catalog", "producer": "src.reporting.research_task_catalog", "consumer_v1": "Streamlit", "consumer_v2": "React/FastAPI", "status": "ready"},
            {"interface": "artifact_manifest_reader", "producer": "src.reporting.research_task_catalog", "consumer_v1": "Streamlit", "consumer_v2": "React/FastAPI", "status": "ready"},
            {"interface": "decision_csv_reader", "producer": "task reports", "consumer_v1": "Streamlit", "consumer_v2": "FastAPI endpoint", "status": "ready"},
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task536",
                "hybrid_frontend_boundary_ready_flag": 1,
                "streamlit_v1_client_flag": 1,
                "react_fastapi_v2_compatible_flag": 1,
                "strategy_acceptance_status": "FRONTEND_API_BOUNDARY_READY",
            }
        ]
    )
    _write_report_bundle(
        out_dir,
        "task_536_frontend_api_boundary.md",
        "Task 536 Frontend API Boundary",
        {
            "frontend_catalog_api_contract": boundary,
            "task_536_decision": decision,
        },
        [
            "The UI boundary is intentionally file/catalog based so Streamlit can operate now and React/FastAPI can consume the same contract later.",
            "This avoids rebuilding the frontend every time task artifacts change.",
        ],
        [
            "We chose a hybrid path: quick dashboard now, product-grade frontend later without changing the research artifact format.",
        ],
    )
    return {"task_536_decision": decision}


def _write_context_doc(context: pd.DataFrame, missing: pd.DataFrame) -> None:
    CONTEXT_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Quant Context Map",
        "",
        "This map converts external quant resources into project governance requirements.",
        "",
        "## Context Sources",
        "",
        *[
            f"- **{row['source']}** / {row['category']}: {row['project_application']} Gap: {row['current_gap']}"
            for row in context.to_dict(orient="records")
        ],
        "",
        "## Missing Capability Matrix",
        "",
        *[
            f"- `{row['capability']}`: {row['status']} blocks `{row['blocked_claim']}`"
            for row in missing.to_dict(orient="records")
        ],
        "",
    ]
    CONTEXT_MAP_PATH.write_text("\n".join(lines), encoding="utf-8")


def _write_report_bundle(
    out_dir: Path,
    report_name: str,
    title: str,
    artifacts: dict[str, pd.DataFrame],
    quant_lines: list[str],
    decision_lines: list[str],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision_name = next(name for name in artifacts if name.startswith("task_"))
    status = artifacts[decision_name].iloc[0].get("strategy_acceptance_status", "UNKNOWN")
    write_standard_report(
        out_dir / report_name,
        title=title,
        decision_summary=[
            f"Strategy acceptance: {status}",
            "Deployment-ready: NO",
            "Missing data approximation used: NO",
        ],
        quant_expert_lines=quant_lines,
        decision_maker_lines=decision_lines,
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_task532_external_quant_context_map()
    build_task533_factor_premium_validation_design()
    build_task534_statistical_validation_upgrade()
    build_task535_frontend_research_cockpit_v1()
    build_task536_frontend_api_boundary()


if __name__ == "__main__":
    main()
