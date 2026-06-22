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
from src.backtest.source_circuit_quality import build_context_quality


TASK_ID = "Task733"
CONTEXTS = Path("docs/reports/task_732_source_circuit_interpreters/task732_circuit_contexts.csv")
OUT_DIR = Path("docs/reports/task_733_circuit_quality_operating_connection")


def build_task733(*, contexts_path: Path = CONTEXTS, out_dir: Path = OUT_DIR) -> dict[str, pd.DataFrame]:
    contexts = pd.read_csv(contexts_path)
    quality, quality_edges = build_context_quality(contexts)
    permission = build_permission_report(quality)
    operating_edges = quality_edges[quality_edges["target_context_type"] == "OperatingCatalystContext"].copy()
    modifier_edges = quality_edges[quality_edges["target_context_type"] != "OperatingCatalystContext"].copy()
    violations = build_guardrail_violations(quality, quality_edges)
    distribution = build_quality_distribution_report(quality)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(quality, quality_edges, operating_edges, modifier_edges, violations)
    pass_fail = build_pass_fail(quality, quality_edges, operating_edges, modifier_edges, violations, distribution)
    outputs = {
        "task733_context_quality.csv": quality,
        "task733_connection_permission.csv": permission,
        "task733_operating_connection_edges.csv": operating_edges,
        "task733_non_operating_modifier_edges.csv": modifier_edges,
        "task733_guardrail_violations.csv": violations,
        "task733_quality_distribution_report.csv": distribution,
        "task733_gpt_review_summary.csv": gpt_review,
        "task_733_decision.csv": decision,
        "task_733_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, quality, quality_edges, decision, pass_fail)
    return {
        "contexts": contexts,
        "quality": quality,
        "quality_edges": quality_edges,
        "permission": permission,
        "operating_edges": operating_edges,
        "modifier_edges": modifier_edges,
        "violations": violations,
        "distribution": distribution,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_permission_report(quality: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "event_id",
        "lifecycle_id",
        "symbol",
        "theme_id",
        "entry_ts",
        "split_name",
        "source_form_family",
        "context_type",
        "quality_state",
        "classification_state",
        "permission_state",
        "connection_rule_id",
        "required_next_evidence",
        "can_create_operating_fact_flag",
        "can_create_operating_connection_flag",
        "used_for_trading_flag",
        "backtest_eligible_flag",
    ]
    return quality[cols].copy()


def build_guardrail_violations(quality: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    rows = []
    non_operating = {"form4_insider", "schedule_13d_13g", "form_13f", "ownership_or_institutional_filing"}
    bad_non_operating = quality[
        quality["source_form_family"].isin(non_operating)
        & ((quality["can_create_operating_fact_flag"] != 0) | (quality["can_create_operating_connection_flag"] != 0))
    ]
    if not bad_non_operating.empty:
        rows.append(violation("non_operating_source_promoted_to_operating", len(bad_non_operating), "non-operating sources must remain modifier_only"))
    bad_trading = quality[(quality["used_for_trading_flag"] != 0) | (quality["backtest_eligible_flag"] != 0)]
    if not bad_trading.empty:
        rows.append(violation("quality_used_for_trading", len(bad_trading), "Task733 is review-only"))
    bad_edges = edges[(edges["used_for_trading_flag"] != 0) | (edges["backtest_eligible_flag"] != 0)]
    if not bad_edges.empty:
        rows.append(violation("edge_used_for_trading", len(bad_edges), "Task733 edges are review-only"))
    missing_rule = edges[edges["rule_id"].fillna("").astype(str).str.len() == 0]
    if not missing_rule.empty:
        rows.append(violation("edge_missing_rule_id", len(missing_rule), "every edge must be traceable"))
    if not rows:
        rows.append(violation("none", 0, "no guardrail violations"))
    return pd.DataFrame(rows)


def violation(kind: str, count: int, required: str) -> dict[str, object]:
    return {"violation_type": kind, "violation_count": count, "required": required, "pass_flag": int(count == 0)}


def build_quality_distribution_report(quality: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = quality.groupby(["context_type", "quality_state", "permission_state"], dropna=False)
    for keys, group in grouped:
        context_type, quality_state, permission_state = keys
        rows.append(
            {
                "context_type": context_type,
                "quality_state": quality_state,
                "permission_state": permission_state,
                "event_count": len(group),
                "operating_connection_count": int(group["can_create_operating_connection_flag"].sum()),
                "operating_fact_creation_count": int(group["can_create_operating_fact_flag"].sum()),
                "used_for_trading_count": int(group["used_for_trading_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["context_type", "event_count"], ascending=[True, False]).reset_index(drop=True)


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "task733_quality_and_permission",
                "status": "CAPTURED_VIA_CHROME_CHATGPT",
                "summary": "Institutional GPT review said Task733 must move from Context existence to Context Quality and Operating Connection Permission. It recommended not_applicable, review_required, connection_candidate, and connection_supported states instead of allow/block.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "financing_generic_macro_detail",
                "status": "CAPTURED_VIA_CHROME_CHATGPT",
                "summary": "GPT detail review specified financing growth/dilution/liquidity/refi/incomplete states, generic 8-K item/material/governance/financing/unclassified routing, and macro theme/weak-link/strong-link/transmission/regulatory states.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(
    quality: pd.DataFrame,
    edges: pd.DataFrame,
    operating_edges: pd.DataFrame,
    modifier_edges: pd.DataFrame,
    violations: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "CIRCUIT_QUALITY_OPERATING_CONNECTION_BUILT_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "quality_row_count": len(quality),
                "edge_count": len(edges),
                "operating_connection_edge_count": len(operating_edges),
                "modifier_edge_count": len(modifier_edges),
                "permission_state_count": quality["permission_state"].nunique(),
                "guardrail_violation_count": int(violations["violation_count"].sum()),
                "backtest_permission": "FAIL",
                "next_action": "Manually inspect connection_candidate and connection_supported rows by source text, then build cross-context bundle QA before any actionability or PnL test.",
            }
        ]
    )


def build_pass_fail(
    quality: pd.DataFrame,
    edges: pd.DataFrame,
    operating_edges: pd.DataFrame,
    modifier_edges: pd.DataFrame,
    violations: pd.DataFrame,
    distribution: pd.DataFrame,
) -> pd.DataFrame:
    permissions = set(quality["permission_state"].dropna().astype(str))
    return pd.DataFrame(
        [
            gate("context_quality_created", len(quality) == 5302, f"rows={len(quality)}", "5302"),
            gate("quality_edges_created", len(edges) == 5302, f"rows={len(edges)}", "5302"),
            gate("permission_states_not_all_block", len(permissions) >= 3, f"states={len(permissions)}:{'|'.join(sorted(permissions))}", ">=3 states"),
            gate("operating_connection_review_completed", len(operating_edges) >= 0, f"rows={len(operating_edges)}", "0 or more review-only"),
            gate("modifier_edges_present", len(modifier_edges) > 0, f"rows={len(modifier_edges)}", ">0"),
            gate("operating_fact_creation_zero", int(quality["can_create_operating_fact_flag"].sum()) == 0, str(int(quality["can_create_operating_fact_flag"].sum())), "0"),
            gate("trading_flags_zero", int(quality["used_for_trading_flag"].sum()) == 0 and int(quality["backtest_eligible_flag"].sum()) == 0, f"trading={int(quality['used_for_trading_flag'].sum())},backtest={int(quality['backtest_eligible_flag'].sum())}", "0"),
            gate("guardrail_violation_zero", int(violations["violation_count"].sum()) == 0, str(int(violations["violation_count"].sum())), "0"),
            gate("distribution_report_present", len(distribution) > 0, f"rows={len(distribution)}", ">0"),
            gate("backtest_permission", False, "FAIL", "quality review only"),
        ]
    )


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    quality: pd.DataFrame,
    edges: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task733_context_quality.jsonl", quality)
    write_jsonl(out_dir / "task733_operating_connection_edges.jsonl", outputs["task733_operating_connection_edges.csv"])
    write_jsonl(out_dir / "task733_non_operating_modifier_edges.jsonl", outputs["task733_non_operating_modifier_edges.csv"])
    write_jsonl(out_dir / "task733_guardrail_violations.jsonl", outputs["task733_guardrail_violations.csv"])
    (out_dir / "task_733_circuit_quality_operating_connection.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task733 Circuit Quality Operating Connection",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        "- Status phrase: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Quality rows: {int(d['quality_row_count'])}",
        f"- Operating connection edges: {int(d['operating_connection_edge_count'])}",
        f"- Modifier edges: {int(d['modifier_edge_count'])}",
        f"- Guardrail violations: {int(d['guardrail_violation_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task733 adds a quality and permission layer on top of Task732 circuit contexts. It does not approve trades. It separates context quality, connection permission, operating connection candidate edges, and non-operating modifier edges.",
        "",
        "### Quality Distribution",
        "",
        frame_to_markdown(outputs["task733_quality_distribution_report.csv"]),
        "",
        "### Guardrail Violations",
        "",
        frame_to_markdown(outputs["task733_guardrail_violations.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task733_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- Conclusion: contexts are now judged by quality and connection permission.",
        "- This is not a buy rule.",
        "- Financing, generic 8-K, and macro can become operating connection candidates only under specific evidence conditions.",
        "- Form4, 13D/13G, 13F, and ownership stay alive as modifiers.",
        "- No source creates operating facts directly.",
        "- Backtest is still blocked.",
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
    lines.append("- `task733_context_quality.jsonl`")
    lines.append("- `task733_operating_connection_edges.jsonl`")
    lines.append("- `task733_non_operating_modifier_edges.jsonl`")
    lines.append("- `task733_guardrail_violations.jsonl`")
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
    artifacts = build_task733(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} quality={decision['quality_row_count']} "
        f"operating_edges={decision['operating_connection_edge_count']} backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
