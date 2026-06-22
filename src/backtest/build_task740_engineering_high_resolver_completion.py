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
from src.backtest.engineering_high_semantic_completion import complete_engineering_high_requirement


TASK_ID = "Task740"
TASK739_TRACE = Path("docs/reports/task_739_semantic_resolver_upgrade_workbench/task739_work_order_requirement_trace.csv")
TASK722_EVENT_DETAIL = Path("docs/reports/task_722_source_attached_review_packets/task722_packet_event_detail.csv")
OUT_DIR = Path("docs/reports/task_740_engineering_high_resolver_completion")


def build_task740(
    *,
    trace_path: Path = TASK739_TRACE,
    event_detail_path: Path = TASK722_EVENT_DETAIL,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    trace = pd.read_csv(trace_path)
    events = pd.read_csv(event_detail_path)
    high_trace = trace[trace["engineering_lane"].astype(str).eq("engineering_high")].copy()
    event_map = {str(row["event_id"]): row for _, row in events.iterrows()}
    primitive_rows = []
    resolver_rows = []
    blocker_rows = []
    for _, row in high_trace.iterrows():
        event = event_map.get(str(row["source_event_id"]), pd.Series(dtype=object))
        primitive, resolver, blockers = complete_engineering_high_requirement(row, event)
        primitive_rows.append(primitive)
        resolver_rows.append(resolver)
        blocker_rows.extend(blockers)
    primitives = pd.DataFrame(primitive_rows)
    resolvers = pd.DataFrame(resolver_rows)
    blockers = pd.DataFrame(blocker_rows)
    metrics = build_quality_metrics(high_trace, primitives, resolvers, blockers)
    resolver_distribution = build_resolver_distribution(resolvers)
    completion_distribution = build_completion_distribution(resolvers)
    coverage = build_coverage_report(high_trace, primitives, resolvers, blockers)
    guardrail = build_guardrail(primitives, resolvers, blockers)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(high_trace, primitives, resolvers, blockers, metrics, guardrail)
    pass_fail = build_pass_fail(high_trace, primitives, resolvers, blockers, metrics, coverage, guardrail)
    outputs = {
        "task740_extracted_primitives.csv": primitives,
        "task740_resolver_outputs.csv": resolvers,
        "task740_unresolved_join_blockers.csv": blockers,
        "task740_quality_metrics.csv": metrics,
        "task740_resolver_distribution.csv": resolver_distribution,
        "task740_completion_distribution.csv": completion_distribution,
        "task740_coverage_report.csv": coverage,
        "task740_guardrail.csv": guardrail,
        "task740_gpt_review_summary.csv": gpt_review,
        "task_740_decision.csv": decision,
        "task_740_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, primitives, resolvers, blockers, decision, pass_fail)
    return {
        "trace": trace,
        "high_trace": high_trace,
        "events": events,
        "primitives": primitives,
        "resolvers": resolvers,
        "blockers": blockers,
        "metrics": metrics,
        "resolver_distribution": resolver_distribution,
        "completion_distribution": completion_distribution,
        "coverage": coverage,
        "guardrail": guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_quality_metrics(high_trace: pd.DataFrame, primitives: pd.DataFrame, resolvers: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    rows = [
        metric("engineering_high_requirement_count", len(high_trace), "count"),
        metric("primitive_extraction_coverage", ratio((primitives["raw_text_available_flag"] == 1).sum(), len(primitives)), "ratio"),
        metric("source_only_or_join_closed_rate", ratio(resolvers["completion_state"].isin(["source_only_resolved", "unresolved_join_needed"]).sum(), len(resolvers)), "ratio"),
        metric("unresolved_join_needed_rate", ratio((resolvers["completion_state"] == "unresolved_join_needed").sum(), len(resolvers)), "ratio"),
        metric("unknown_resolver_state_rate", ratio(resolvers["resolver_state"].astype(str).str.contains("unknown").sum(), len(resolvers)), "ratio"),
        metric("guardrail_trade_output_count", int(resolvers["buy_sell_signal_created_flag"].sum() + resolvers["actionability_created_flag"].sum() + resolvers["used_for_trading_flag"].sum() + resolvers["backtest_eligible_flag"].sum()), "count"),
    ]
    form4 = primitives[primitives["source_circuit"].eq("form4_insider_behavior")]
    if not form4.empty:
        fields = form4["primitive_fields_json"].apply(json.loads)
        rows.extend(
            [
                metric("transaction_code_resolution_rate", ratio(sum(bool(item.get("primary_transaction_code")) for item in fields), len(form4)), "ratio"),
                metric("form4_10b5_1_strict_classification_rate", ratio(sum(int(item.get("planned_10b5_1_flag", 0)) for item in fields), len(form4)), "ratio"),
                metric("open_market_vs_award_split_rate", ratio(sum(bool(item.get("open_market_buy_flag") or item.get("open_market_sale_flag") or item.get("award_grant_flag") or item.get("option_exercise_flag")) for item in fields), len(form4)), "ratio"),
            ]
        )
    ownership = primitives[primitives["source_circuit"].isin(["ownership_float_structure", "activist_control"])]
    if not ownership.empty:
        fields = ownership["primitive_fields_json"].apply(json.loads)
        rows.extend(
            [
                metric("ownership_percent_extraction_rate", ratio(sum(int(item.get("ownership_percent_present_flag", 0)) for item in fields), len(ownership)), "ratio"),
                metric("active_passive_resolution_rate", ratio(sum(bool(item.get("active_13d_flag") or item.get("passive_13g_flag")) for item in fields), len(ownership)), "ratio"),
            ]
        )
    generic_8k = primitives[primitives["source_circuit"].eq("generic_8k_classifier")]
    if not generic_8k.empty:
        fields = generic_8k["primitive_fields_json"].apply(json.loads)
        rows.append(metric("generic_8k_family_classification_rate", ratio(sum(bool(item.get("agreement_family_state")) for item in fields), len(generic_8k)), "ratio"))
    financing = primitives[primitives["source_circuit"].eq("credit_financing")]
    if not financing.empty:
        fields = financing["primitive_fields_json"].apply(json.loads)
        rows.append(metric("financing_instrument_resolution_rate", ratio(sum(any(item.get(key) for key in item if str(key).startswith("instrument_")) for item in fields), len(financing)), "ratio"))
    results = primitives[primitives["source_circuit"].eq("financial_results_guidance")]
    if not results.empty:
        fields = results["primitive_fields_json"].apply(json.loads)
        rows.append(metric("financial_guidance_language_detection_rate", ratio(sum(bool(item.get("guidance_language_flag") or item.get("revenue_language_flag") or item.get("margin_language_flag")) for item in fields), len(results)), "ratio"))
    rows.append(metric("unresolved_join_blocker_count", len(blockers), "count"))
    return pd.DataFrame(rows)


def build_resolver_distribution(resolvers: pd.DataFrame) -> pd.DataFrame:
    return (
        resolvers.groupby(["source_circuit", "requirement_family", "resolver_state", "completion_state"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .sort_values("row_count", ascending=False)
        .reset_index(drop=True)
    )


def build_completion_distribution(resolvers: pd.DataFrame) -> pd.DataFrame:
    return (
        resolvers.groupby(["completion_state"], dropna=False)
        .agg(row_count=("completion_state", "size"), backtest_eligible_count=("backtest_eligible_flag", "sum"))
        .reset_index()
        .sort_values("row_count", ascending=False)
        .reset_index(drop=True)
    )


def build_coverage_report(high_trace: pd.DataFrame, primitives: pd.DataFrame, resolvers: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "scope": "engineering_high_requirements",
                "expected_requirement_count": len(high_trace),
                "primitive_row_count": len(primitives),
                "resolver_row_count": len(resolvers),
                "blocker_row_count": len(blockers),
                "covered_lifecycle_count": high_trace["lifecycle_id"].nunique(),
                "covered_source_event_count": high_trace["source_event_id"].nunique(),
                "coverage_state": "all_engineering_high_requirements_processed" if len(high_trace) == len(primitives) == len(resolvers) else "coverage_gap",
                "research_only_flag": 1,
            }
        ]
    )


def build_guardrail(primitives: pd.DataFrame, resolvers: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    forbidden_cols = forbidden_columns_found([primitives, resolvers, blockers])
    action = resolvers[
        (resolvers["buy_sell_signal_created_flag"] != 0)
        | (resolvers["actionability_created_flag"] != 0)
        | (resolvers["used_for_trading_flag"] != 0)
        | (resolvers["backtest_eligible_flag"] != 0)
        | (resolvers["operating_supported_created_flag"] != 0)
        | (resolvers["outcome_used_for_assignment_flag"] != 0)
    ]
    primitive_action = primitives[
        (primitives["backtest_eligible_flag"] != 0)
        | (primitives["outcome_used_for_assignment_flag"] != 0)
    ]
    blocker_action = blockers[(blockers["backtest_eligible_flag"] != 0)] if not blockers.empty else pd.DataFrame()
    unknown_negative = resolvers[
        resolvers["resolver_state"].astype(str).str.contains("unknown", na=False)
        & resolvers["resolver_detail_state"].astype(str).str.contains("adverse|bearish", na=False)
    ]
    item101_supported = resolvers[
        resolvers["resolver_state"].astype(str).eq("operating_supported")
        | resolvers["resolver_state"].astype(str).eq("operating_catalyst_supported")
    ]
    return pd.DataFrame(
        [
            gate("no_forbidden_columns_created", not forbidden_cols, "checked", "no score/rank/trade/outcome columns"),
            gate("resolver_outputs_review_only", action.empty, f"rows={len(action)}", "0"),
            gate("primitive_outputs_review_only", primitive_action.empty, f"rows={len(primitive_action)}", "0"),
            gate("blockers_review_only", blocker_action.empty, f"rows={len(blocker_action)}", "0"),
            gate("unknown_not_bearish", unknown_negative.empty, f"rows={len(unknown_negative)}", "0"),
            gate("generic_8k_not_operating_supported_by_default", item101_supported.empty, f"rows={len(item101_supported)}", "0"),
            gate("all_resolvers_have_completion_state", resolvers["completion_state"].fillna("").astype(str).str.len().gt(0).all(), "checked", "all non-empty"),
        ]
    )


def forbidden_columns_found(frames: list[pd.DataFrame]) -> bool:
    allowed_guardrail_columns = {
        "buy_sell_signal_created_flag",
        "actionability_created_flag",
        "used_for_trading_flag",
        "backtest_eligible_flag",
        "outcome_used_for_assignment_flag",
        "operating_supported_created_flag",
    }
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
    ]
    for frame in frames:
        for column in frame.columns:
            if str(column) in allowed_guardrail_columns:
                continue
            lower = str(column).lower()
            if any(token in lower for token in forbidden):
                return True
    return False


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "overall_brain_strategy_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "Institutional GPT review said Task740 can conditionally close the source-semantic layer by extracting available primitives, emitting source-only resolver states, and explicitly preserving denominator/join blockers.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "circuit_detail_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "GPT required Form4 open-market/10b5-1/award splits, ownership 13D/13G active/passive/control splits, financial results language extraction, generic 8-K routing, and financing term resolution without bullish/bearish or trade-ready outputs.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(
    high_trace: pd.DataFrame,
    primitives: pd.DataFrame,
    resolvers: pd.DataFrame,
    blockers: pd.DataFrame,
    metrics: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "ENGINEERING_HIGH_SOURCE_SEMANTIC_LAYER_CONDITIONALLY_CLOSED_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "engineering_high_requirement_count": len(high_trace),
                "primitive_row_count": len(primitives),
                "resolver_row_count": len(resolvers),
                "unresolved_join_blocker_count": len(blockers),
                "source_semantic_layer_status": "CONDITIONALLY_CLOSED_SOURCE_ONLY",
                "economic_denominator_layer_status": "OPEN_JOIN_BLOCKED",
                "guardrail_pass": int(guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Implement denominator and comparator joins for Form4 pattern, ownership materiality, financial expectations, and capital structure before any trading or backtest promotion.",
            }
        ]
    )


def build_pass_fail(
    high_trace: pd.DataFrame,
    primitives: pd.DataFrame,
    resolvers: pd.DataFrame,
    blockers: pd.DataFrame,
    metrics: pd.DataFrame,
    coverage: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("engineering_high_requirements_processed", len(high_trace) == len(primitives) == len(resolvers), f"trace={len(high_trace)}, primitives={len(primitives)}, resolvers={len(resolvers)}", "all equal"),
            gate("coverage_report_created", coverage.iloc[0]["coverage_state"] == "all_engineering_high_requirements_processed", str(coverage.iloc[0]["coverage_state"]), "all processed"),
            gate("quality_metrics_created", len(metrics) >= 8, f"rows={len(metrics)}", ">=8"),
            gate("unresolved_join_blockers_created", len(blockers) > 0, f"rows={len(blockers)}", ">0"),
            gate("completion_states_valid", set(resolvers["completion_state"]).issubset({"source_only_resolved", "unresolved_join_needed", "raw_text_missing"}), "|".join(sorted(set(resolvers["completion_state"]))), "valid states"),
            gate("guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "source semantic closure only"),
        ]
    )


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    primitives: pd.DataFrame,
    resolvers: pd.DataFrame,
    blockers: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task740_extracted_primitives.jsonl", primitives)
    write_jsonl(out_dir / "task740_resolver_outputs.jsonl", resolvers)
    write_jsonl(out_dir / "task740_unresolved_join_blockers.jsonl", blockers)
    (out_dir / "task_740_engineering_high_resolver_completion.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task740 Engineering-High Resolver Completion",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        f"- Engineering-high requirements: {int(d['engineering_high_requirement_count'])}",
        f"- Primitive rows: {int(d['primitive_row_count'])}",
        f"- Resolver rows: {int(d['resolver_row_count'])}",
        f"- Unresolved join blockers: {int(d['unresolved_join_blocker_count'])}",
        f"- Source semantic layer: `{d['source_semantic_layer_status']}`",
        f"- Economic denominator layer: `{d['economic_denominator_layer_status']}`",
        "",
        "## Quant Expert Report",
        "",
        "Task740 processes every Task739 engineering-high requirement through source-text primitive extraction and source-only resolver states. It explicitly preserves unresolved denominator, comparator, timing, and economic-join blockers. It does not create scores, ranks, trading actions, allocation, or backtest eligibility.",
        "",
        "### Quality Metrics",
        "",
        frame_to_markdown(outputs["task740_quality_metrics.csv"]),
        "",
        "### Resolver Distribution",
        "",
        frame_to_markdown(outputs["task740_resolver_distribution.csv"].head(30)),
        "",
        "### Completion Distribution",
        "",
        frame_to_markdown(outputs["task740_completion_distribution.csv"]),
        "",
        "### Guardrail",
        "",
        frame_to_markdown(outputs["task740_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task740_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "The source-semantic part is now conditionally closed for engineering-high circuits. The code can read available raw text and separate Form4, ownership, 13D/13G, financing, 8-K, and results/guidance states. What remains open is the economic denominator layer: holdings history, float, market cap, cash/debt, prior guidance, consensus, and price absorption.",
        "",
        "## Artifact Manifest",
        "",
        "- `task740_extracted_primitives.csv/jsonl`",
        "- `task740_resolver_outputs.csv/jsonl`",
        "- `task740_unresolved_join_blockers.csv/jsonl`",
        "- `task740_quality_metrics.csv`",
        "- `task740_resolver_distribution.csv`",
        "- `task740_completion_distribution.csv`",
        "- `task740_coverage_report.csv`",
        "- `task740_guardrail.csv`",
        "- `task740_gpt_review_summary.csv`",
        "- `task_740_decision.csv`",
        "- `task_740_pass_fail_matrix.csv`",
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


def metric(name: str, value: float | int, unit: str) -> dict[str, object]:
    return {"metric": name, "value": value, "unit": unit}


def ratio(numerator: int | float, denominator: int | float) -> float:
    return round(float(numerator) / float(denominator), 6) if denominator else 0.0


def gate(name: str, passed: bool, observed: str, expected: str) -> dict[str, object]:
    return {
        "gate": name,
        "pass_flag": int(bool(passed)),
        "observed": observed,
        "expected": expected,
    }


def write_stdout_summary(artifacts: dict[str, pd.DataFrame]) -> None:
    print(json.dumps(artifacts["decision"].iloc[0].to_dict(), ensure_ascii=False, default=str, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Task740 engineering-high resolver completion.")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_stdout_summary(build_task740(out_dir=args.out_dir))


if __name__ == "__main__":
    main()
