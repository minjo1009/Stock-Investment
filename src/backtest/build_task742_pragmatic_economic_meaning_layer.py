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
from src.backtest.pragmatic_economic_meaning_layer import build_pragmatic_economic_meaning_packets


TASK_ID = "Task742"
TASK741_PACKETS = Path("docs/reports/task_741_economic_denominator_meaning_layer/task741_economic_meaning_packets.csv")
TASK740_PRIMITIVES = Path("docs/reports/task_740_engineering_high_resolver_completion/task740_extracted_primitives.csv")
OUT_DIR = Path("docs/reports/task_742_pragmatic_economic_meaning_layer")


def build_task742(
    *,
    task741_packets_path: Path = TASK741_PACKETS,
    task740_primitives_path: Path = TASK740_PRIMITIVES,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    task741_packets = pd.read_csv(task741_packets_path)
    task740_primitives = pd.read_csv(task740_primitives_path)
    packets = build_pragmatic_economic_meaning_packets(task741_packets, task740_primitives)
    metrics = build_quality_metrics(packets)
    distribution = build_distribution(packets)
    reclassification = build_blocker_reclassification(packets)
    guardrail = build_guardrail(packets)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(task741_packets, packets, metrics, guardrail)
    pass_fail = build_pass_fail(task741_packets, packets, metrics, guardrail)
    outputs = {
        "task742_pragmatic_economic_meaning_packets.csv": packets,
        "task742_quality_metrics.csv": metrics,
        "task742_interpretation_distribution.csv": distribution,
        "task742_blocker_reclassification.csv": reclassification,
        "task742_guardrail.csv": guardrail,
        "task742_gpt_review_summary.csv": gpt_review,
        "task_742_decision.csv": decision,
        "task_742_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, packets, decision, pass_fail)
    return {
        "task741_packets": task741_packets,
        "task740_primitives": task740_primitives,
        "packets": packets,
        "metrics": metrics,
        "distribution": distribution,
        "reclassification": reclassification,
        "guardrail": guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_quality_metrics(packets: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            metric("packet_count", len(packets), "count"),
            metric("relation_ready_count", int(packets["relation_ready_flag"].sum()), "count"),
            metric("relation_ready_rate", ratio(int(packets["relation_ready_flag"].sum()), len(packets)), "ratio"),
            metric("usable_without_missing_source_count", int(packets["usable_without_missing_source_flag"].sum()), "count"),
            metric("usable_without_missing_source_rate", ratio(int(packets["usable_without_missing_source_flag"].sum()), len(packets)), "ratio"),
            metric("hard_blocker_count", int(packets["hard_blocker_flags"].astype(str).ne("").sum()), "count"),
            metric("soft_uncertainty_count", int(packets["soft_uncertainty_flags"].astype(str).ne("").sum()), "count"),
            metric("directional_edge_candidate_count", int(packets["can_create_directional_edge_flag"].sum()), "count"),
            metric("structural_edge_candidate_count", int(packets["can_create_structural_edge_flag"].sum()), "count"),
            metric("context_attachment_only_count", int(packets["context_attachment_only_flag"].sum()), "count"),
            metric("not_ready_tier_count", int(packets["relation_ready_tier"].eq("not_ready").sum()), "count"),
            metric("positive_hint_count", int(packets["economic_direction_hint"].eq("positive").sum()), "count"),
            metric("negative_hint_count", int(packets["economic_direction_hint"].eq("negative").sum()), "count"),
            metric("mixed_hint_count", int(packets["economic_direction_hint"].eq("mixed").sum()), "count"),
            metric("neutral_hint_count", int(packets["economic_direction_hint"].eq("neutral").sum()), "count"),
            metric("unknown_hint_count", int(packets["economic_direction_hint"].eq("unknown").sum()), "count"),
            metric("trade_output_violation_count", int(packets["trade_output_flag"].sum() + packets["score_output_flag"].sum() + packets["backtest_eligible_flag"].sum()), "count"),
        ]
    )


def build_distribution(packets: pd.DataFrame) -> pd.DataFrame:
    return (
        packets.groupby(["source_circuit", "interpretation_state", "economic_direction_hint", "confidence_band", "relation_ready_tier"], dropna=False)
        .agg(
            row_count=("interpretation_state", "size"),
            relation_ready_count=("relation_ready_flag", "sum"),
            hard_blocker_count=("hard_blocker_flags", lambda s: int(s.astype(str).ne("").sum())),
            directional_edge_candidate_count=("can_create_directional_edge_flag", "sum"),
            structural_edge_candidate_count=("can_create_structural_edge_flag", "sum"),
            context_attachment_only_count=("context_attachment_only_flag", "sum"),
        )
        .reset_index()
        .sort_values(["row_count", "source_circuit"], ascending=[False, True])
        .reset_index(drop=True)
    )


def build_blocker_reclassification(packets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in packets.iterrows():
        old_blockers = split_pipe(row.get("task741_missing_blocker_states"))
        hard = set(split_pipe(row.get("hard_blocker_flags")))
        soft = set(split_pipe(row.get("soft_uncertainty_flags")))
        for blocker in old_blockers:
            rows.append(
                {
                    "task741_blocker_state": blocker,
                    "source_circuit": row["source_circuit"],
                    "task742_reclassification": classify_old_blocker(blocker, hard, soft),
                    "row_count": 1,
                    "relation_ready_flag": int(row["relation_ready_flag"]),
                    "usable_without_missing_source_flag": int(row["usable_without_missing_source_flag"]),
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=[
                "task741_blocker_state",
                "source_circuit",
                "task742_reclassification",
                "row_count",
                "relation_ready_count",
                "usable_without_missing_source_count",
            ]
        )
    frame = pd.DataFrame(rows)
    return (
        frame.groupby(["task741_blocker_state", "source_circuit", "task742_reclassification"], dropna=False)
        .agg(
            row_count=("row_count", "sum"),
            relation_ready_count=("relation_ready_flag", "sum"),
            usable_without_missing_source_count=("usable_without_missing_source_flag", "sum"),
        )
        .reset_index()
        .sort_values("row_count", ascending=False)
        .reset_index(drop=True)
    )


def classify_old_blocker(blocker: str, hard: set[str], soft: set[str]) -> str:
    if not blocker:
        return "none"
    if blocker in hard:
        return "hard_blocker"
    soft_name = blocker.replace("_missing", "_soft").replace("_blocked", "_soft").replace("_needed", "_soft")
    if blocker in soft or soft_name in soft:
        return "soft_uncertainty"
    if blocker in {
        "exact_person_history_missing",
        "insider_total_holdings_missing",
        "prior_holder_percent_missing",
        "free_float_missing",
        "consensus_estimates_missing",
        "prior_guidance_database_missing",
        "margin_bridge_missing",
        "ownership_percent_missing",
        "dilution_terms_incomplete",
    }:
        return "soft_uncertainty"
    return "not_used_in_pragmatic_judgment"


def build_guardrail(packets: pd.DataFrame) -> pd.DataFrame:
    action = packets[
        (packets["trade_output_flag"] != 0)
        | (packets["score_output_flag"] != 0)
        | (packets["backtest_eligible_flag"] != 0)
        | (packets["outcome_used_for_assignment_flag"] != 0)
    ]
    forbidden_cols = forbidden_columns_found(packets)
    missing_as_negative = packets[
        packets["task741_missing_blocker_states"].astype(str).str.contains("missing|blocked|needed", na=False)
        & packets["hard_blocker_flags"].astype(str).eq("")
        & packets["interpretation_state"].astype(str).str.contains("hard_blocked|unusable", na=False)
    ]
    identity_gap = packets[
        packets["lifecycle_id"].fillna("").astype(str).eq("")
        | packets["source_event_id"].fillna("").astype(str).eq("")
        | packets["rule_id"].fillna("").astype(str).eq("")
    ]
    direction_values = {"positive", "negative", "mixed", "neutral", "unknown"}
    bad_direction = packets[~packets["economic_direction_hint"].isin(direction_values)]
    neutral_unknown_directional = packets[
        packets["economic_direction_hint"].isin({"neutral", "unknown"})
        & packets["can_create_directional_edge_flag"].ne(0)
    ]
    bad_tier = packets[
        packets["relation_ready_tier"].eq("directional")
        & ~packets["economic_direction_hint"].isin({"positive", "negative"})
    ]
    change_inference_gap = packets[packets["asof_change_inference_forbidden_flag"].ne(1)]
    trade_instruction_gap = packets[packets["direction_hint_trade_instruction_flag"].ne(0)]
    return pd.DataFrame(
        [
            gate("no_forbidden_columns_created", not forbidden_cols, "checked", "no forbidden output columns"),
            gate("no_trade_score_backtest_outputs", action.empty, f"rows={len(action)}", "0"),
            gate("missing_not_converted_to_hard_blocker", missing_as_negative.empty, f"rows={len(missing_as_negative)}", "0"),
            gate("identity_trace_present", identity_gap.empty, f"rows={len(identity_gap)}", "0"),
            gate("direction_hint_domain_valid", bad_direction.empty, f"rows={len(bad_direction)}", "0"),
            gate("neutral_unknown_no_directional_edge", neutral_unknown_directional.empty, f"rows={len(neutral_unknown_directional)}", "0"),
            gate("directional_tier_positive_negative_only", bad_tier.empty, f"rows={len(bad_tier)}", "0"),
            gate("asof_snapshot_change_inference_forbidden", change_inference_gap.empty, f"rows={len(change_inference_gap)}", "0"),
            gate("direction_hint_not_trade_instruction", trade_instruction_gap.empty, f"rows={len(trade_instruction_gap)}", "0"),
            gate("relation_ready_is_review_only", packets["backtest_eligible_flag"].sum() == 0, "backtest_eligible_sum=0", "0"),
        ]
    )


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "pragmatic_available_data_economic_meaning_redesign",
                "status": "CHROME_GPT_INSTITUTIONAL_REVIEW_REQUESTED_AND_APPLIED",
                "summary": "Task742 follows the institutional review prompt and follow-up GPT panel critique: keep unavailable high-grade sources as uncertainty, not blanket blockers; split relation readiness into directional, structural mixed, context-only, and not-ready tiers; forbid treating direction hints as trades; and forbid change inference from as-of snapshots.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            }
        ]
    )


def build_decision(task741_packets: pd.DataFrame, packets: pd.DataFrame, metrics: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "PRAGMATIC_ECONOMIC_MEANING_LAYER_BUILT_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_permission": "FORBIDDEN",
                "backtest_permission": "FAIL",
                "input_task741_packet_count": len(task741_packets),
                "output_packet_count": len(packets),
                "relation_ready_count": int(packets["relation_ready_flag"].sum()),
                "directional_edge_candidate_count": int(packets["can_create_directional_edge_flag"].sum()),
                "structural_edge_candidate_count": int(packets["can_create_structural_edge_flag"].sum()),
                "context_attachment_only_count": int(packets["context_attachment_only_flag"].sum()),
                "hard_blocker_count": int(packets["hard_blocker_flags"].astype(str).ne("").sum()),
                "soft_uncertainty_count": int(packets["soft_uncertainty_flags"].astype(str).ne("").sum()),
                "guardrail_pass_flag": int(guardrail["pass_flag"].min()),
                "next_action": "Feed review-only pragmatic meaning packets into relation edge construction after audit, not directly into allocation or backtest.",
            }
        ]
    )


def build_pass_fail(task741_packets: pd.DataFrame, packets: pd.DataFrame, metrics: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("all_task741_packets_reinterpreted", len(task741_packets) == len(packets), f"task741={len(task741_packets)}, task742={len(packets)}", "equal"),
            gate("some_relation_ready_packets_created", packets["relation_ready_flag"].sum() > 0, f"rows={int(packets['relation_ready_flag'].sum())}", ">0"),
            gate("relation_ready_tier_created", packets["relation_ready_tier"].nunique() >= 3, f"tiers={packets['relation_ready_tier'].nunique()}", ">=3"),
            gate("neutral_unknown_not_directional", packets[packets["economic_direction_hint"].isin({"neutral", "unknown"}) & packets["can_create_directional_edge_flag"].ne(0)].empty, "checked", "0 rows"),
            gate("hard_blockers_not_dominant", packets["hard_blocker_flags"].astype(str).ne("").mean() < 0.05, f"rate={packets['hard_blocker_flags'].astype(str).ne('').mean():.6f}", "<0.05"),
            gate("guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "pragmatic meaning packets are review-only"),
        ]
    )


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    packets: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task742_pragmatic_economic_meaning_packets.jsonl", packets)
    (out_dir / "task_742_pragmatic_economic_meaning_layer.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task742 Pragmatic Economic Meaning Layer",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        f"- Output packets: {int(d['output_packet_count'])}",
        f"- Relation-ready review packets: {int(d['relation_ready_count'])}",
        f"- Directional edge candidates: {int(d['directional_edge_candidate_count'])}",
        f"- Structural mixed edge candidates: {int(d['structural_edge_candidate_count'])}",
        f"- Context-only attachments: {int(d['context_attachment_only_count'])}",
        f"- Hard blockers: {int(d['hard_blocker_count'])}",
        f"- Soft uncertainty packets: {int(d['soft_uncertainty_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task742 supersedes the Task741 blocker-heavy interpretation for economic meaning review. It does not delete Task741 denominators. It reclassifies unavailable high-grade sources as soft uncertainty unless the row lacks primitive identity, raw source trace, or as-of safety. Available source primitives, SEC companyfacts, and as-of price context are used to create direction hints, confidence bands, ambiguity flags, needed confirmations, and relation-readiness tiers. Directional, structural mixed, and context-only packets are separated so neutral or unknown rows cannot become directional edges. These are research objects only, not trade instructions.",
        "",
        "### Quality Metrics",
        "",
        frame_to_markdown(outputs["task742_quality_metrics.csv"]),
        "",
        "### Interpretation Distribution",
        "",
        frame_to_markdown(outputs["task742_interpretation_distribution.csv"].head(30)),
        "",
        "### Blocker Reclassification",
        "",
        frame_to_markdown(outputs["task742_blocker_reclassification.csv"].head(30)),
        "",
        "### Guardrail",
        "",
        frame_to_markdown(outputs["task742_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task742_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "Task741 was too strict: too many rows became blocker-heavy even when current data still allowed a useful economic read. Task742 keeps missing data visible, but it does not let missing perfect data kill every judgment. The result is still not a buy/sell model. It is a cleaner bridge into the relation engine.",
        "",
        "## Artifact Manifest",
        "",
        "- `task742_pragmatic_economic_meaning_packets.csv/jsonl`",
        "- `task742_quality_metrics.csv`",
        "- `task742_interpretation_distribution.csv`",
        "- `task742_blocker_reclassification.csv`",
        "- `task742_guardrail.csv`",
        "- `task742_gpt_review_summary.csv`",
        "- `task_742_decision.csv`",
        "- `task_742_pass_fail_matrix.csv`",
        "",
        "## Pass Fail Matrix",
        "",
        frame_to_markdown(pass_fail),
    ]
    return "\n".join(lines) + "\n"


def forbidden_columns_found(frame: pd.DataFrame) -> bool:
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
    for column in frame.columns:
        if str(column) in allowed:
            continue
        lower = str(column).lower()
        if any(token in lower for token in forbidden):
            return True
    return False


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


def split_pipe(value: object) -> list[str]:
    text_value = "" if value is None or pd.isna(value) else str(value)
    return [item for item in text_value.split("|") if item]


def metric(name: str, value: float | int, unit: str) -> dict[str, object]:
    return {"metric": name, "value": value, "unit": unit}


def ratio(numerator: int | float, denominator: int | float) -> float:
    return round(float(numerator) / float(denominator), 6) if denominator else 0.0


def gate(name: str, passed: bool, observed: str, expected: str) -> dict[str, object]:
    return {"gate": name, "pass_flag": int(bool(passed)), "observed": observed, "expected": expected}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task742(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] packets={int(decision['output_packet_count'])} "
        f"relation_ready={int(decision['relation_ready_count'])} "
        f"guardrail={int(decision['guardrail_pass_flag'])}"
    )


if __name__ == "__main__":
    main()
