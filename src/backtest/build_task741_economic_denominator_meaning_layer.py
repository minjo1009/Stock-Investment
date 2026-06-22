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
from src.backtest.economic_denominator_meaning_layer import build_economic_meaning_packets


TASK_ID = "Task741"
TASK740_PRIMITIVES = Path("docs/reports/task_740_engineering_high_resolver_completion/task740_extracted_primitives.csv")
TASK740_RESOLVERS = Path("docs/reports/task_740_engineering_high_resolver_completion/task740_resolver_outputs.csv")
TASK722_EVENT_DETAIL = Path("docs/reports/task_722_source_attached_review_packets/task722_packet_event_detail.csv")
OUT_DIR = Path("docs/reports/task_741_economic_denominator_meaning_layer")


def build_task741(
    *,
    primitives_path: Path = TASK740_PRIMITIVES,
    resolvers_path: Path = TASK740_RESOLVERS,
    event_detail_path: Path = TASK722_EVENT_DETAIL,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    primitives = pd.read_csv(primitives_path)
    resolvers = pd.read_csv(resolvers_path)
    event_detail = pd.read_csv(event_detail_path)
    packets, blockers = build_economic_meaning_packets(primitives, resolvers, event_detail)
    metrics = build_quality_metrics(packets, blockers)
    meaning_distribution = build_meaning_distribution(packets)
    availability = build_availability_summary(packets)
    blocker_summary = build_blocker_summary(blockers)
    coverage = build_coverage_report(resolvers, packets, blockers)
    guardrail = build_guardrail(packets, blockers)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(resolvers, packets, blockers, metrics, guardrail)
    pass_fail = build_pass_fail(resolvers, packets, blockers, metrics, coverage, guardrail)
    outputs = {
        "task741_economic_meaning_packets.csv": packets,
        "task741_missing_source_blockers.csv": blockers,
        "task741_quality_metrics.csv": metrics,
        "task741_meaning_distribution.csv": meaning_distribution,
        "task741_source_availability_summary.csv": availability,
        "task741_blocker_summary.csv": blocker_summary,
        "task741_coverage_report.csv": coverage,
        "task741_guardrail.csv": guardrail,
        "task741_gpt_review_summary.csv": gpt_review,
        "task_741_decision.csv": decision,
        "task_741_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, packets, blockers, decision, pass_fail)
    return {
        "primitives": primitives,
        "resolvers": resolvers,
        "event_detail": event_detail,
        "packets": packets,
        "blockers": blockers,
        "metrics": metrics,
        "meaning_distribution": meaning_distribution,
        "availability": availability,
        "blocker_summary": blocker_summary,
        "coverage": coverage,
        "guardrail": guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_quality_metrics(packets: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    availability = packets["source_availability_json"].apply(json.loads)
    denom = packets["attached_denominators_json"].apply(json.loads)
    timing = packets["timing_asof_checks_json"].apply(json.loads)
    return pd.DataFrame(
        [
            metric("packet_coverage_count", len(packets), "count"),
            metric("task722_event_detail_join_rate", ratio(sum(item.get("has_task722_event_detail") for item in availability), len(packets)), "ratio"),
            metric("sec_companyfacts_join_rate", ratio(sum(item.get("has_sec_companyfacts") for item in availability), len(packets)), "ratio"),
            metric("daily_price_join_rate", ratio(sum(item.get("has_daily_price") for item in availability), len(packets)), "ratio"),
            metric("market_cap_proxy_attach_rate", ratio(sum(item.get("has_market_cap_proxy") for item in availability), len(packets)), "ratio"),
            metric("revenue_baseline_attach_rate", ratio(sum(item.get("has_revenue_fact") for item in availability), len(packets)), "ratio"),
            metric("cash_debt_attach_rate", ratio(sum(item.get("has_cash_fact") or item.get("has_debt_fact") for item in availability), len(packets)), "ratio"),
            metric("ownership_percent_attach_rate", ratio(sum("ownership_percent_source_attached" == state for state in packets["meaning_state"]), len(packets)), "ratio"),
            metric("financing_principal_attach_rate", ratio(sum((item.get("market_cap_proxy") is not None) for item in denom), len(packets)), "ratio"),
            metric("missing_blocker_emit_rate", ratio(len(blockers), len(packets)), "ratio"),
            metric("future_data_violation_count", sum(not item.get("no_future_data_used") for item in timing), "count"),
            metric("trade_output_violation_count", int(packets["trade_output_flag"].sum() + packets["score_output_flag"].sum() + packets["backtest_eligible_flag"].sum()), "count"),
        ]
    )


def build_meaning_distribution(packets: pd.DataFrame) -> pd.DataFrame:
    return (
        packets.groupby(["source_circuit", "meaning_state"], dropna=False)
        .agg(row_count=("meaning_state", "size"), backtest_eligible_count=("backtest_eligible_flag", "sum"))
        .reset_index()
        .sort_values("row_count", ascending=False)
        .reset_index(drop=True)
    )


def build_availability_summary(packets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    availability = packets["source_availability_json"].apply(json.loads)
    for key in sorted({key for item in availability for key in item}):
        rows.append(
            {
                "availability_flag": key,
                "true_count": sum(bool(item.get(key)) for item in availability),
                "packet_count": len(packets),
                "true_rate": ratio(sum(bool(item.get(key)) for item in availability), len(packets)),
            }
        )
    return pd.DataFrame(rows)


def build_blocker_summary(blockers: pd.DataFrame) -> pd.DataFrame:
    if blockers.empty:
        return pd.DataFrame(columns=["blocker_state", "source_circuit", "row_count", "backtest_eligible_count"])
    return (
        blockers.groupby(["blocker_state", "source_circuit"], dropna=False)
        .agg(row_count=("blocker_state", "size"), backtest_eligible_count=("backtest_eligible_flag", "sum"))
        .reset_index()
        .sort_values("row_count", ascending=False)
        .reset_index(drop=True)
    )


def build_coverage_report(resolvers: pd.DataFrame, packets: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "scope": "task740_resolver_to_economic_meaning_packet",
                "resolver_row_count": len(resolvers),
                "packet_row_count": len(packets),
                "missing_blocker_row_count": len(blockers),
                "covered_lifecycle_count": packets["lifecycle_id"].nunique(),
                "covered_source_event_count": packets["source_event_id"].nunique(),
                "coverage_state": "all_task740_resolvers_have_economic_meaning_packet" if len(resolvers) == len(packets) else "coverage_gap",
                "research_only_flag": 1,
            }
        ]
    )


def build_guardrail(packets: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    forbidden_cols = forbidden_columns_found([packets, blockers])
    timing = packets["timing_asof_checks_json"].apply(json.loads)
    future = [item for item in timing if not item.get("no_future_data_used")]
    action = packets[
        (packets["trade_output_flag"] != 0)
        | (packets["score_output_flag"] != 0)
        | (packets["backtest_eligible_flag"] != 0)
        | (packets["outcome_used_for_assignment_flag"] != 0)
    ]
    negative_missing = packets[
        packets["missing_blocker_states"].astype(str).str.contains("missing|blocked|needed", na=False)
        & packets["meaning_state"].astype(str).str.contains("bearish|adverse", na=False)
    ]
    bad_financing = packets[
        packets["source_circuit"].eq("credit_financing")
        & packets["meaning_state"].astype(str).str.contains("bullish|bearish", na=False)
    ]
    bad_generic = packets[
        packets["source_circuit"].eq("generic_8k_classifier")
        & packets["meaning_state"].astype(str).str.contains("operating_supported", na=False)
    ]
    trace_gap = packets[
        packets["lifecycle_id"].fillna("").astype(str).eq("")
        | packets["source_event_id"].fillna("").astype(str).eq("")
        | packets["rule_id"].fillna("").astype(str).eq("")
    ]
    return pd.DataFrame(
        [
            gate("no_forbidden_columns_created", not forbidden_cols, "checked", "no forbidden output columns"),
            gate("no_future_denominator_or_price", len(future) == 0, f"rows={len(future)}", "0"),
            gate("missing_is_blocker_not_negative", negative_missing.empty, f"rows={len(negative_missing)}", "0"),
            gate("no_bullish_bearish_financing", bad_financing.empty, f"rows={len(bad_financing)}", "0"),
            gate("generic_8k_item101_not_operating_supported", bad_generic.empty, f"rows={len(bad_generic)}", "0"),
            gate("no_trade_score_backtest_outputs", action.empty, f"rows={len(action)}", "0"),
            gate("all_packets_trace_identity", trace_gap.empty, f"rows={len(trace_gap)}", "0"),
        ]
    )


def forbidden_columns_found(frames: list[pd.DataFrame]) -> bool:
    allowed = {"trade_output_flag", "score_output_flag", "backtest_eligible_flag", "outcome_used_for_assignment_flag"}
    forbidden = [
        "future_return",
        "forward_return",
        "net_return",
        "pnl",
        "realized_pnl",
        "win_loss",
        "label",
        "top50",
        "rank",
        "score",
        "alpha_score",
        "priority_score",
        "buy_signal",
        "sell_signal",
        "trade_ready",
        "backtest_ready",
        "backtest_eligible_1",
    ]
    for frame in frames:
        for column in frame.columns:
            if str(column) in allowed:
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
                "summary": "Institutional GPT review passed Task741 as an economic denominator/comparator meaning layer that attaches available local denominators and emits explicit missing-source blockers without trading, scoring, ranking, or backtest promotion.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "circuit_detail_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "GPT required Form4 transaction size context, ownership/13D/13G percent and float blockers, financing principal versus market/cash/debt context, financial results baseline and expectation blockers, and generic 8-K route guardrails.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(
    resolvers: pd.DataFrame,
    packets: pd.DataFrame,
    blockers: pd.DataFrame,
    metrics: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "ECONOMIC_DENOMINATOR_MEANING_LAYER_CONDITIONALLY_CLOSED_WITH_BLOCKERS",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "resolver_row_count": len(resolvers),
                "economic_packet_count": len(packets),
                "missing_source_blocker_count": len(blockers),
                "meaning_state_count": packets["meaning_state"].nunique(),
                "economic_meaning_layer_status": "CONDITIONALLY_CLOSED_WITH_EXPLICIT_JOIN_BLOCKERS",
                "guardrail_pass": int(guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Only after sourcing consensus, prior guidance, exact insider history, and free-float shares should these economic meaning packets be promoted into relationship-edge validation.",
            }
        ]
    )


def build_pass_fail(
    resolvers: pd.DataFrame,
    packets: pd.DataFrame,
    blockers: pd.DataFrame,
    metrics: pd.DataFrame,
    coverage: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("all_task740_resolvers_have_packets", len(resolvers) == len(packets), f"resolvers={len(resolvers)}, packets={len(packets)}", "equal"),
            gate("coverage_report_created", coverage.iloc[0]["coverage_state"] == "all_task740_resolvers_have_economic_meaning_packet", str(coverage.iloc[0]["coverage_state"]), "all covered"),
            gate("quality_metrics_created", len(metrics) >= 10, f"rows={len(metrics)}", ">=10"),
            gate("missing_source_blockers_emitted", len(blockers) > 0, f"rows={len(blockers)}", ">0"),
            gate("guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "economic meaning packets review only"),
        ]
    )


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    packets: pd.DataFrame,
    blockers: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task741_economic_meaning_packets.jsonl", packets)
    write_jsonl(out_dir / "task741_missing_source_blockers.jsonl", blockers)
    (out_dir / "task_741_economic_denominator_meaning_layer.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task741 Economic Denominator Meaning Layer",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        f"- Economic packets: {int(d['economic_packet_count'])}",
        f"- Missing source blockers: {int(d['missing_source_blocker_count'])}",
        f"- Meaning states: {int(d['meaning_state_count'])}",
        f"- Layer status: `{d['economic_meaning_layer_status']}`",
        "",
        "## Quant Expert Report",
        "",
        "Task741 attaches available economic denominators and comparators to Task740 source-semantic resolver outputs. It uses local SEC companyfacts and daily price sources when they are as-of valid, and emits explicit blockers for missing free float, prior holder percent, exact insider history, consensus, prior guidance, and margin bridge sources.",
        "",
        "### Quality Metrics",
        "",
        frame_to_markdown(outputs["task741_quality_metrics.csv"]),
        "",
        "### Meaning Distribution",
        "",
        frame_to_markdown(outputs["task741_meaning_distribution.csv"].head(30)),
        "",
        "### Source Availability",
        "",
        frame_to_markdown(outputs["task741_source_availability_summary.csv"]),
        "",
        "### Blocker Summary",
        "",
        frame_to_markdown(outputs["task741_blocker_summary.csv"].head(30)),
        "",
        "### Guardrail",
        "",
        frame_to_markdown(outputs["task741_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task741_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "The economic meaning layer is conditionally closed. Local denominators such as SEC companyfacts, public float USD, shares outstanding, cash, debt, revenue, and daily price are attached when available. Missing higher-grade sources remain explicit blockers, not negative signals.",
        "",
        "## Artifact Manifest",
        "",
        "- `task741_economic_meaning_packets.csv/jsonl`",
        "- `task741_missing_source_blockers.csv/jsonl`",
        "- `task741_quality_metrics.csv`",
        "- `task741_meaning_distribution.csv`",
        "- `task741_source_availability_summary.csv`",
        "- `task741_blocker_summary.csv`",
        "- `task741_coverage_report.csv`",
        "- `task741_guardrail.csv`",
        "- `task741_gpt_review_summary.csv`",
        "- `task_741_decision.csv`",
        "- `task_741_pass_fail_matrix.csv`",
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
    parser = argparse.ArgumentParser(description="Build Task741 economic denominator meaning layer.")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_stdout_summary(build_task741(out_dir=args.out_dir))


if __name__ == "__main__":
    main()
