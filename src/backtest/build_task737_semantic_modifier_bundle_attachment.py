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
from src.backtest.semantic_modifier_bundle_attachment import attach_semantic_modifiers, build_attachment_edges


TASK_ID = "Task737"
TASK723_BUNDLES = Path("docs/reports/task_723_five_stage_decision_contract/task723_candidate_context_bundles.csv")
TASK688_BUNDLES = Path("docs/reports/task_688_context_object_contracts/task688_candidate_context_bundles.csv")
TASK736_TRANSLATIONS = Path("docs/reports/task_736_context_semantic_translator/task736_semantic_translation.csv")
OUT_DIR = Path("docs/reports/task_737_semantic_modifier_bundle_attachment")


def build_task737(
    *,
    task723_bundles_path: Path = TASK723_BUNDLES,
    task688_bundles_path: Path = TASK688_BUNDLES,
    translations_path: Path = TASK736_TRANSLATIONS,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    bundles = pd.read_csv(task723_bundles_path)
    translations = pd.read_csv(translations_path)
    attachment = attach_semantic_modifiers(bundles, translations)
    broader_attachment = build_broader_attachment_attempt(task688_bundles_path, translations)
    edges = build_attachment_edges(attachment)
    queue_summary = build_queue_summary(attachment)
    conflict_summary = build_conflict_summary(attachment)
    coverage = build_coverage_report(bundles, translations, broader_attachment)
    guardrail = build_guardrail(attachment, edges, translations, broader_attachment)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(attachment, edges, coverage, guardrail)
    pass_fail = build_pass_fail(attachment, edges, queue_summary, conflict_summary, coverage, guardrail)
    outputs = {
        "task737_bundle_semantic_modifier_attachment.csv": attachment,
        "task737_task688_semantic_modifier_attach_attempt.csv": broader_attachment,
        "task737_modifier_attachment_edges.csv": edges,
        "task737_queue_transition_summary.csv": queue_summary,
        "task737_conflict_summary.csv": conflict_summary,
        "task737_coverage_report.csv": coverage,
        "task737_guardrail.csv": guardrail,
        "task737_gpt_review_summary.csv": gpt_review,
        "task_737_decision.csv": decision,
        "task_737_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, attachment, edges, decision, pass_fail)
    return {
        "bundles": bundles,
        "translations": translations,
        "attachment": attachment,
        "broader_attachment": broader_attachment,
        "edges": edges,
        "queue_summary": queue_summary,
        "conflict_summary": conflict_summary,
        "coverage": coverage,
        "guardrail": guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_queue_summary(attachment: pd.DataFrame) -> pd.DataFrame:
    grouped = attachment.groupby(["queue_transition_state", "dominant_modifier_state"], dropna=False)
    rows = []
    for keys, group in grouped:
        queue, dominant = keys
        rows.append(
            {
                "queue_transition_state": queue,
                "dominant_modifier_state": dominant,
                "bundle_count": len(group),
                "source_modifier_count": int(group["source_modifier_count"].sum()),
                "direct_score_count": int(group["direct_score_created_flag"].sum()),
                "backtest_eligible_count": int(group["backtest_eligible_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("bundle_count", ascending=False).reset_index(drop=True)


def build_conflict_summary(attachment: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in attachment.iterrows():
        for conflict in split_pipe(row["conflict_state"]):
            rows.append(
                {
                    "conflict_state": conflict,
                    "bundle_count": 1,
                    "source_modifier_count": int(row["source_modifier_count"]),
                    "backtest_eligible_count": int(row["backtest_eligible_flag"]),
                }
            )
    frame = pd.DataFrame(rows)
    grouped = frame.groupby("conflict_state", dropna=False).agg(
        bundle_count=("bundle_count", "sum"),
        source_modifier_count=("source_modifier_count", "sum"),
        backtest_eligible_count=("backtest_eligible_count", "sum"),
    )
    return grouped.reset_index().sort_values("bundle_count", ascending=False).reset_index(drop=True)


def build_broader_attachment_attempt(task688_bundles_path: Path, translations: pd.DataFrame) -> pd.DataFrame:
    if not task688_bundles_path.exists():
        return pd.DataFrame()
    task688 = pd.read_csv(task688_bundles_path)
    return attach_semantic_modifiers(task688, translations)


def build_coverage_report(bundles: pd.DataFrame, translations: pd.DataFrame, broader_attachment: pd.DataFrame) -> pd.DataFrame:
    translation_lifecycles = set(translations["lifecycle_id"].dropna().astype(str))
    rows = [
        {
            "scope": "task723_review_bundles",
            "bundle_count": len(bundles),
            "bundle_with_translation_count": int(bundles["lifecycle_id"].astype(str).isin(translation_lifecycles).sum()),
            "translation_lifecycle_count": len(translation_lifecycles),
            "coverage_state": "covered_by_task736_source_attached_packets",
            "used_for_trading_flag": 0,
        }
    ]
    if not broader_attachment.empty:
        overlap = int((broader_attachment["source_modifier_count"] > 0).sum())
        rows.append(
            {
                "scope": "task688_broader_context_bundles",
                "bundle_count": len(broader_attachment),
                "bundle_with_translation_count": overlap,
                "translation_lifecycle_count": len(translation_lifecycles),
                "coverage_state": "semantic_modifier_absent_not_negative_report_only",
                "used_for_trading_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_guardrail(attachment: pd.DataFrame, edges: pd.DataFrame, translations: pd.DataFrame, broader_attachment: pd.DataFrame) -> pd.DataFrame:
    action = attachment[
        (attachment["direct_score_created_flag"] != 0)
        | (attachment["buy_sell_signal_created_flag"] != 0)
        | (attachment["actionability_created_flag"] != 0)
        | (attachment["backtest_eligible_flag"] != 0)
    ]
    edge_action = edges[(edges["used_for_trading_flag"] != 0) | (edges["backtest_eligible_flag"] != 0)]
    no_modifier = attachment[attachment["source_modifier_count"] <= 0]
    unknown_negative = attachment[(attachment["unknown_count"] > 0) & (attachment["adverse_count"] == attachment["source_modifier_count"])]
    broader_action = broader_attachment[
        (broader_attachment["direct_score_created_flag"] != 0)
        | (broader_attachment["buy_sell_signal_created_flag"] != 0)
        | (broader_attachment["actionability_created_flag"] != 0)
        | (broader_attachment["backtest_eligible_flag"] != 0)
    ] if not broader_attachment.empty else pd.DataFrame()
    broader_absent_negative = broader_attachment[
        (broader_attachment["source_modifier_count"] == 0)
        & ~broader_attachment["queue_transition_state"].eq("semantic_modifier_absent_not_negative")
    ] if not broader_attachment.empty else pd.DataFrame()
    forbidden_cols = forbidden_columns_found([attachment, edges, translations, broader_attachment])
    return pd.DataFrame(
        [
            gate("all_task723_bundles_attached", len(attachment) == 345, f"rows={len(attachment)}", "345"),
            gate("all_bundles_have_source_modifiers", no_modifier.empty, f"rows={len(no_modifier)}", "0"),
            gate("no_direct_score_or_actionability", action.empty, f"rows={len(action)}", "0"),
            gate("edges_review_only", edge_action.empty, f"rows={len(edge_action)}", "0"),
            gate("task688_attach_attempt_review_only", broader_action.empty, f"rows={len(broader_action)}", "0"),
            gate("task688_absent_not_negative", broader_absent_negative.empty, f"rows={len(broader_absent_negative)}", "0"),
            gate("unknown_not_negative", unknown_negative.empty, f"rows={len(unknown_negative)}", "0"),
            gate("no_forbidden_outcome_columns", not forbidden_cols, "checked", "no outcome/PnL/label columns"),
            gate("queue_transitions_present", attachment["queue_transition_state"].nunique() >= 3, f"states={attachment['queue_transition_state'].nunique()}", ">=3"),
        ]
    )


def forbidden_columns_found(frames: list[pd.DataFrame]) -> bool:
    forbidden = ["future_return", "net_return", "pnl", "win_loss", "winner", "loser", "top50", "selection_result", "costed_return"]
    for frame in frames:
        for col in frame.columns:
            lower = str(col).lower()
            if any(token in lower for token in forbidden):
                return True
    return False


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "overall_brain_strategy_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "Institutional GPT review said Task737 should attach semantic translations to candidate bundles as count, conflict, queue transition, and layer modifier explanations, not as direct scores or actionability.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "circuit_detail_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "GPT detail review required constructive/adverse/mixed/conditional/unknown counts, confidence/risk/slot/research modifier counts, explicit conflict states, queue transitions, and guardrails against PnL labels, missing-as-negative, global priority scoring, and buy/sell creation.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(attachment: pd.DataFrame, edges: pd.DataFrame, coverage: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "SEMANTIC_MODIFIERS_ATTACHED_TO_BUNDLES_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "bundle_count": len(attachment),
                "source_modifier_count": int(attachment["source_modifier_count"].sum()),
                "edge_count": len(edges),
                "queue_transition_count": attachment["queue_transition_state"].nunique(),
                "conflict_state_count": attachment["conflict_state"].nunique(),
                "coverage_scope_count": len(coverage),
                "guardrail_pass": int(guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Review queue transition packets and Task688 absent-coverage gap, then design a governed bundle modifier resolver that changes review priority only within same-timestamp cohorts without direct scores or buy/sell outputs.",
            }
        ]
    )


def build_pass_fail(
    attachment: pd.DataFrame,
    edges: pd.DataFrame,
    queue_summary: pd.DataFrame,
    conflict_summary: pd.DataFrame,
    coverage: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("bundle_attachment_created", len(attachment) == 345, f"rows={len(attachment)}", "345"),
            gate("attachment_edges_created", len(edges) >= len(attachment), f"rows={len(edges)}", ">= bundles"),
            gate("queue_summary_created", len(queue_summary) > 0, f"rows={len(queue_summary)}", ">0"),
            gate("conflict_summary_created", len(conflict_summary) > 0, f"rows={len(conflict_summary)}", ">0"),
            gate("coverage_report_created", len(coverage) >= 1, f"rows={len(coverage)}", ">=1"),
            gate("guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "semantic modifier bundle attachment review only"),
        ]
    )


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    attachment: pd.DataFrame,
    edges: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task737_bundle_semantic_modifier_attachment.jsonl", attachment)
    if "task737_task688_semantic_modifier_attach_attempt.csv" in outputs:
        write_jsonl(out_dir / "task737_task688_semantic_modifier_attach_attempt.jsonl", outputs["task737_task688_semantic_modifier_attach_attempt.csv"])
    write_jsonl(out_dir / "task737_modifier_attachment_edges.jsonl", edges)
    (out_dir / "task_737_semantic_modifier_bundle_attachment.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task737 Semantic Modifier Bundle Attachment",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        "- Status phrase: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Bundles: {int(d['bundle_count'])}",
        f"- Source modifiers attached: {int(d['source_modifier_count'])}",
        f"- Modifier edges: {int(d['edge_count'])}",
        f"- Queue transition states: {int(d['queue_transition_count'])}",
        f"- Conflict states: {int(d['conflict_state_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task737 attaches Task736 semantic translations to Task723 candidate bundles. It creates bundle-level modifier counts, conflict states, queue transitions, and review focus fields. It does not create direct scores, buy/sell, actionability, allocation, or backtest eligibility.",
        "",
        "### Queue Transition Summary",
        "",
        frame_to_markdown(outputs["task737_queue_transition_summary.csv"]),
        "",
        "### Conflict Summary",
        "",
        frame_to_markdown(outputs["task737_conflict_summary.csv"]),
        "",
        "### Coverage",
        "",
        frame_to_markdown(outputs["task737_coverage_report.csv"]),
        "",
        "### Guardrail",
        "",
        frame_to_markdown(outputs["task737_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task737_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- Conclusion: semantic translations are now attached to review bundles.",
        "- They explain confidence, risk, slot, and research queue pressure.",
        "- They are not scores.",
        "- They are not buy rules.",
        "- Unknown remains unknown, not negative.",
        "- Task688 broader bundles are attach-attempted; absent semantic modifiers are reported as absent, not negative.",
        "",
        "## Pass/Fail Matrix",
        "",
        frame_to_markdown(pass_fail),
        "",
        "## Artifact Manifest",
        "",
    ]
    for filename in outputs:
        lines.append(f"- `{filename}`")
    lines.append("- `task737_bundle_semantic_modifier_attachment.jsonl`")
    lines.append("- `task737_task688_semantic_modifier_attach_attempt.jsonl`")
    lines.append("- `task737_modifier_attachment_edges.jsonl`")
    lines.append("- `artifact_manifest.csv`")
    return "\n".join(lines)


def frame_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    cols = [str(c) for c in frame.columns]
    rows = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in frame.iterrows():
        rows.append("| " + " | ".join([markdown_cell(row.get(col, "")) for col in frame.columns]) + " |")
    return "\n".join(rows)


def markdown_cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def split_pipe(value: object) -> list[str]:
    text = "" if value is None or pd.isna(value) else str(value)
    return [part for part in text.split("|") if part] or ["no_semantic_conflict_detected"]


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task737(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} bundles={decision['bundle_count']} "
        f"modifiers={decision['source_modifier_count']} backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
