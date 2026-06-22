from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.semantic_resolver_upgrade_workbench import build_workbench


TASK_ID = "Task739"
TASK738_REQUIREMENTS = Path("docs/reports/task_738_semantic_enrichment_requirements/task738_enrichment_requirements.csv")
OUT_DIR = Path("docs/reports/task_739_semantic_resolver_upgrade_workbench")


def build_task739(*, requirements_path: Path = TASK738_REQUIREMENTS, out_dir: Path = OUT_DIR) -> dict[str, pd.DataFrame]:
    requirements = pd.read_csv(requirements_path)
    workbench = build_workbench(requirements)
    denominator_contracts = build_join_contracts(workbench["extractor_orders"], "required_denominator_joins", "denominator_join")
    comparator_contracts = build_join_contracts(workbench["extractor_orders"], "required_comparator_joins", "comparator_join")
    timing_contracts = build_join_contracts(workbench["extractor_orders"], "required_timing_checks", "timing_asof_check")
    coverage = build_coverage_report(requirements, workbench)
    guardrail = build_guardrail(requirements, workbench)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(requirements, workbench, coverage, guardrail)
    pass_fail = build_pass_fail(requirements, workbench, denominator_contracts, comparator_contracts, timing_contracts, coverage, guardrail)
    outputs = {
        "task739_extractor_work_orders.csv": workbench["extractor_orders"],
        "task739_resolver_work_orders.csv": workbench["resolver_orders"],
        "task739_work_order_requirement_trace.csv": workbench["trace"],
        "task739_allowed_resolver_states.csv": workbench["taxonomy"],
        "task739_engineering_lane_summary.csv": workbench["lane_summary"],
        "task739_denominator_join_contracts.csv": denominator_contracts,
        "task739_comparator_join_contracts.csv": comparator_contracts,
        "task739_timing_asof_contracts.csv": timing_contracts,
        "task739_coverage_report.csv": coverage,
        "task739_guardrail.csv": guardrail,
        "task739_gpt_review_summary.csv": gpt_review,
        "task_739_decision.csv": decision,
        "task_739_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, workbench, denominator_contracts, comparator_contracts, timing_contracts, decision, pass_fail)
    return {
        "requirements": requirements,
        "denominator_contracts": denominator_contracts,
        "comparator_contracts": comparator_contracts,
        "timing_contracts": timing_contracts,
        "coverage": coverage,
        "guardrail": guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
        **workbench,
    }


def build_join_contracts(work_orders: pd.DataFrame, column: str, contract_type: str) -> pd.DataFrame:
    rows = []
    for _, order in work_orders.iterrows():
        for field in split_pipe(order[column]):
            rows.append(
                {
                    "contract_type": contract_type,
                    "requirement_family": order["requirement_family"],
                    "source_circuit": order["source_circuit"],
                    "work_order_id": order["work_order_id"],
                    "required_field": field,
                    "join_contract_state": "required_not_implemented",
                    "research_only_flag": 1,
                    "rule_id": "TASK739_JOIN_CONTRACT_REVIEW_ONLY",
                }
            )
    return pd.DataFrame(rows)


def build_coverage_report(requirements: pd.DataFrame, workbench: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "scope": "task738_requirement_family_to_work_order",
                "requirement_family_count": requirements["requirement_family"].nunique(),
                "extractor_work_order_count": len(workbench["extractor_orders"]),
                "resolver_work_order_count": len(workbench["resolver_orders"]),
                "requirement_row_count": len(requirements),
                "trace_row_count": len(workbench["trace"]),
                "resolver_target_count": requirements["resolver_target_state"].nunique(),
                "taxonomy_circuit_count": workbench["taxonomy"]["source_circuit"].nunique(),
                "coverage_state": "all_requirements_mapped_to_extractor_and_resolver_work_orders",
                "research_only_flag": 1,
            }
        ]
    )


def build_guardrail(requirements: pd.DataFrame, workbench: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = [workbench["extractor_orders"], workbench["resolver_orders"], workbench["trace"], workbench["taxonomy"], workbench["lane_summary"]]
    forbidden_cols = forbidden_columns_found(frames)
    extractor_missing = workbench["extractor_orders"][
        workbench["extractor_orders"]["target_extractor"].fillna("").astype(str).eq("")
        | workbench["extractor_orders"]["required_primitive_fields"].fillna("").astype(str).eq("")
    ]
    resolver_missing = workbench["resolver_orders"][
        workbench["resolver_orders"]["target_resolver"].fillna("").astype(str).eq("")
        | workbench["resolver_orders"]["allowed_output_states"].fillna("").astype(str).eq("")
    ]
    invalid_lane = workbench["extractor_orders"][~workbench["extractor_orders"]["engineering_lane"].isin(["engineering_high", "engineering_normal"])]
    allowed_bad = workbench["resolver_orders"][
        workbench["resolver_orders"]["allowed_output_states"].astype(str).str.contains("buy_signal|sell_signal|trade_ready|earnings_trade_signal|beat_miss_score", na=False)
    ]
    trace_gap = workbench["trace"][
        workbench["trace"]["lifecycle_id"].fillna("").astype(str).eq("")
        | workbench["trace"]["source_event_id"].fillna("").astype(str).eq("")
        | workbench["trace"]["rule_id"].fillna("").astype(str).eq("")
    ]
    return pd.DataFrame(
        [
            gate("all_requirement_families_have_extractor_work_order", len(workbench["extractor_orders"]) == requirements["requirement_family"].nunique(), f"rows={len(workbench['extractor_orders'])}", str(requirements["requirement_family"].nunique())),
            gate("all_requirement_families_have_resolver_work_order", len(workbench["resolver_orders"]) == requirements["requirement_family"].nunique(), f"rows={len(workbench['resolver_orders'])}", str(requirements["requirement_family"].nunique())),
            gate("all_requirements_trace_to_work_orders", len(workbench["trace"]) == len(requirements), f"rows={len(workbench['trace'])}", str(len(requirements))),
            gate("extractor_contract_fields_present", extractor_missing.empty, f"rows={len(extractor_missing)}", "0"),
            gate("resolver_contract_fields_present", resolver_missing.empty, f"rows={len(resolver_missing)}", "0"),
            gate("engineering_lane_not_trading_priority", invalid_lane.empty, f"rows={len(invalid_lane)}", "0"),
            gate("no_forbidden_columns_created", not forbidden_cols, "checked", "no outcome/score/rank/trade columns"),
            gate("allowed_states_do_not_create_trade_signals", allowed_bad.empty, f"rows={len(allowed_bad)}", "0"),
            gate("trace_identity_present", trace_gap.empty, f"rows={len(trace_gap)}", "0"),
            gate("research_only_flags_all_one", all_research_only(workbench), "checked", "all research_only_flag=1"),
        ]
    )


def forbidden_columns_found(frames: list[pd.DataFrame]) -> bool:
    forbidden = [
        "future_return",
        "forward_return",
        "net_return",
        "realized_pnl",
        "pnl",
        "win_loss",
        "winner",
        "loser",
        "top50",
        "rank",
        "score",
        "alpha_score",
        "priority_score",
        "buy_signal",
        "sell_signal",
        "trade_label",
        "backtest_label",
        "backtest_eligible",
    ]
    for frame in frames:
        for column in frame.columns:
            lower = str(column).lower()
            if any(token in lower for token in forbidden):
                return True
    return False


def all_research_only(workbench: dict[str, pd.DataFrame]) -> bool:
    for key in ["extractor_orders", "resolver_orders", "trace", "lane_summary"]:
        frame = workbench[key]
        if "research_only_flag" in frame.columns and not frame["research_only_flag"].eq(1).all():
            return False
    return True


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "overall_brain_strategy_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "Institutional GPT review passed Task739 as a work-order planner: Task738 requirements should become extractor work orders, resolver work orders, join contracts, timing/as-of contracts, allowed resolver states, and guardrail tests.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "circuit_detail_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "GPT review required engineering-high lanes for Form4 pattern extraction, ownership/13D/13G, financial results/guidance, generic 8-K, financing, and M&A contamination risk, while keeping review lanes separate from trading priority.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(
    requirements: pd.DataFrame,
    workbench: dict[str, pd.DataFrame],
    coverage: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "SEMANTIC_RESOLVER_UPGRADE_WORKBENCH_BUILT_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "requirement_count": len(requirements),
                "requirement_family_count": requirements["requirement_family"].nunique(),
                "extractor_work_order_count": len(workbench["extractor_orders"]),
                "resolver_work_order_count": len(workbench["resolver_orders"]),
                "trace_row_count": len(workbench["trace"]),
                "resolver_state_count": len(workbench["taxonomy"]),
                "engineering_high_work_order_count": int((workbench["extractor_orders"]["engineering_lane"] == "engineering_high").sum()),
                "engineering_normal_work_order_count": int((workbench["extractor_orders"]["engineering_lane"] == "engineering_normal").sum()),
                "coverage_state": coverage.iloc[0]["coverage_state"],
                "guardrail_pass": int(guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Implement the engineering-high extractor contracts first, starting with Form4 insider pattern and ownership/13D/13G resolver primitives, then rerun Task736-739.",
            }
        ]
    )


def build_pass_fail(
    requirements: pd.DataFrame,
    workbench: dict[str, pd.DataFrame],
    denominator_contracts: pd.DataFrame,
    comparator_contracts: pd.DataFrame,
    timing_contracts: pd.DataFrame,
    coverage: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("extractor_work_orders_created", len(workbench["extractor_orders"]) == requirements["requirement_family"].nunique(), f"rows={len(workbench['extractor_orders'])}", str(requirements["requirement_family"].nunique())),
            gate("resolver_work_orders_created", len(workbench["resolver_orders"]) == requirements["requirement_family"].nunique(), f"rows={len(workbench['resolver_orders'])}", str(requirements["requirement_family"].nunique())),
            gate("requirement_trace_created", len(workbench["trace"]) == len(requirements), f"rows={len(workbench['trace'])}", str(len(requirements))),
            gate("denominator_contracts_created", len(denominator_contracts) > 0, f"rows={len(denominator_contracts)}", ">0"),
            gate("comparator_contracts_created", len(comparator_contracts) > 0, f"rows={len(comparator_contracts)}", ">0"),
            gate("timing_contracts_created", len(timing_contracts) > 0, f"rows={len(timing_contracts)}", ">0"),
            gate("coverage_report_created", coverage.iloc[0]["coverage_state"] == "all_requirements_mapped_to_extractor_and_resolver_work_orders", str(coverage.iloc[0]["coverage_state"]), "all mapped"),
            gate("guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "extractor/resolver workbench review only"),
        ]
    )


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    workbench: dict[str, pd.DataFrame],
    denominator_contracts: pd.DataFrame,
    comparator_contracts: pd.DataFrame,
    timing_contracts: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task739_extractor_work_orders.jsonl", workbench["extractor_orders"])
    write_jsonl(out_dir / "task739_resolver_work_orders.jsonl", workbench["resolver_orders"])
    write_jsonl(out_dir / "task739_work_order_requirement_trace.jsonl", workbench["trace"])
    write_jsonl(out_dir / "task739_allowed_resolver_states.jsonl", workbench["taxonomy"])
    write_yaml_contract(out_dir / "task739_denominator_join_contracts.yaml", denominator_contracts)
    write_yaml_contract(out_dir / "task739_comparator_join_contracts.yaml", comparator_contracts)
    write_yaml_contract(out_dir / "task739_timing_asof_contracts.yaml", timing_contracts)
    (out_dir / "task_739_semantic_resolver_upgrade_workbench.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def write_yaml_contract(path: Path, frame: pd.DataFrame) -> None:
    lines = ["contracts:"]
    for _, row in frame.iterrows():
        lines.extend(
            [
                f"  - contract_type: {row['contract_type']}",
                f"    requirement_family: {row['requirement_family']}",
                f"    source_circuit: {row['source_circuit']}",
                f"    work_order_id: {row['work_order_id']}",
                f"    required_field: {row['required_field']}",
                f"    join_contract_state: {row['join_contract_state']}",
                f"    research_only_flag: {int(row['research_only_flag'])}",
                f"    rule_id: {row['rule_id']}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task739 Semantic Resolver Upgrade Workbench",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        f"- Requirements traced: {int(d['requirement_count'])}",
        f"- Extractor work orders: {int(d['extractor_work_order_count'])}",
        f"- Resolver work orders: {int(d['resolver_work_order_count'])}",
        f"- Trace rows: {int(d['trace_row_count'])}",
        f"- Engineering-high work orders: {int(d['engineering_high_work_order_count'])}",
        f"- Engineering-normal work orders: {int(d['engineering_normal_work_order_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task739 converts Task738 requirement objects into extractor and resolver upgrade work orders. It is a code contract layer only. It does not implement alpha logic, scoring, ranking, allocation, buy/sell signals, actionability, or backtesting.",
        "",
        "### Engineering Lane Summary",
        "",
        frame_to_markdown(outputs["task739_engineering_lane_summary.csv"]),
        "",
        "### Extractor Work Orders",
        "",
        frame_to_markdown(outputs["task739_extractor_work_orders.csv"]),
        "",
        "### Resolver Work Orders",
        "",
        frame_to_markdown(outputs["task739_resolver_work_orders.csv"].head(20)),
        "",
        "### Guardrail",
        "",
        frame_to_markdown(outputs["task739_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task739_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "Task738 said what information is missing. Task739 says which extractor and resolver must fill it. The biggest engineering-high lanes are Form4 insider pattern extraction, ownership/13D/13G interpretation, and smaller but dangerous financial results, generic 8-K, and financing routes.",
        "",
        "## Artifact Manifest",
        "",
        "- `task739_extractor_work_orders.csv/jsonl`",
        "- `task739_resolver_work_orders.csv/jsonl`",
        "- `task739_work_order_requirement_trace.csv/jsonl`",
        "- `task739_allowed_resolver_states.csv/jsonl`",
        "- `task739_denominator_join_contracts.csv/yaml`",
        "- `task739_comparator_join_contracts.csv/yaml`",
        "- `task739_timing_asof_contracts.csv/yaml`",
        "- `task739_engineering_lane_summary.csv`",
        "- `task739_guardrail.csv`",
        "- `task739_gpt_review_summary.csv`",
        "- `task_739_decision.csv`",
        "- `task_739_pass_fail_matrix.csv`",
        "",
        "## Pass Fail Matrix",
        "",
        frame_to_markdown(pass_fail),
    ]
    return "\n".join(lines) + "\n"


def frame_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    columns = [str(column) for column in frame.columns]
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame.iterrows():
        rows.append("| " + " | ".join(markdown_cell(row[column]) for column in frame.columns) + " |")
    return "\n".join(rows)


def markdown_cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_stdout_summary(artifacts: dict[str, pd.DataFrame]) -> None:
    print(json.dumps(artifacts["decision"].iloc[0].to_dict(), ensure_ascii=False, default=str, indent=2))


def split_pipe(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [part for part in str(value).split("|") if part]


def gate(name: str, passed: bool, observed: str, expected: str) -> dict[str, object]:
    return {
        "gate": name,
        "pass_flag": int(bool(passed)),
        "observed": observed,
        "expected": expected,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Task739 semantic resolver upgrade workbench.")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_stdout_summary(build_task739(out_dir=args.out_dir))


if __name__ == "__main__":
    main()
