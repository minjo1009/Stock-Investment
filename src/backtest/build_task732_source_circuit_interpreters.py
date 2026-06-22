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
from src.backtest.source_circuit_interpreters import interpret_source_event


TASK_ID = "Task732"
EVENT_DETAIL = Path("docs/reports/task_722_source_attached_review_packets/task722_packet_event_detail.csv")
OUT_DIR = Path("docs/reports/task_732_source_circuit_interpreters")


def build_task732(*, event_detail_path: Path = EVENT_DETAIL, out_dir: Path = OUT_DIR) -> dict[str, pd.DataFrame]:
    events = pd.read_csv(event_detail_path)
    contexts, edges = [], []
    for idx, row in events.iterrows():
        context, edge = interpret_source_event(row, row_index=int(idx))
        contexts.append(context)
        edges.append(edge)
    context_frame = pd.DataFrame(contexts)
    edge_frame = pd.DataFrame(edges)
    coverage = build_circuit_coverage_report(context_frame, edge_frame)
    guardrail = build_forbidden_fact_guardrail(context_frame, edge_frame)
    alive = build_alive_review_states_report(context_frame)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(context_frame, edge_frame, guardrail)
    pass_fail = build_pass_fail(context_frame, edge_frame, coverage, guardrail, alive)
    outputs = {
        "task732_circuit_contexts.csv": context_frame,
        "task732_context_edges.csv": edge_frame,
        "task732_circuit_coverage_report.csv": coverage,
        "task732_forbidden_fact_guardrail.csv": guardrail,
        "task732_alive_review_states_report.csv": alive,
        "task732_gpt_review_summary.csv": gpt_review,
        "task_732_decision.csv": decision,
        "task_732_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, context_frame, edge_frame, decision, pass_fail)
    return {
        "events": events,
        "contexts": context_frame,
        "edges": edge_frame,
        "coverage": coverage,
        "guardrail": guardrail,
        "alive": alive,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_circuit_coverage_report(contexts: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = contexts.groupby(["source_form_family", "context_type", "route_state", "route_circuit"], dropna=False)
    for keys, group in grouped:
        source_family, context_type, route_state, route_circuit = keys
        rows.append(
            {
                "source_form_family": source_family,
                "context_type": context_type,
                "route_state": route_state,
                "route_circuit": route_circuit,
                "event_count": len(group),
                "edge_count": int((edges["source_context_type"] == context_type).sum()),
                "discarded_source_count": int(group["source_is_discarded_flag"].sum()),
                "operating_primitive_created_count": int(group["operating_primitive_created_flag"].sum()),
                "backtest_eligible_count": int(group["backtest_eligible_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["event_count", "source_form_family"], ascending=[False, True]).reset_index(drop=True)


def build_forbidden_fact_guardrail(contexts: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    non_operating = contexts[contexts["source_form_family"].isin(["form4_insider", "schedule_13d_13g", "form_13f", "ownership_or_institutional_filing"])]
    generic = contexts[contexts["source_form_family"] == "generic_8k"]
    macro = contexts[contexts["source_form_family"] == "macro_policy_or_geopolitical_source"]
    return pd.DataFrame(
        [
            gate("all_events_preserved", len(contexts) == 5302, f"rows={len(contexts)}", "5302"),
            gate("all_contexts_have_edges", len(edges) == len(contexts), f"edges={len(edges)}", f"{len(contexts)}"),
            gate("discarded_source_zero", int(contexts["source_is_discarded_flag"].sum()) == 0, str(int(contexts["source_is_discarded_flag"].sum())), "0"),
            gate("non_operating_operating_primitive_zero", int(non_operating["operating_primitive_created_flag"].sum()) == 0, str(int(non_operating["operating_primitive_created_flag"].sum())), "0"),
            gate("generic_8k_operating_primitive_zero", int(generic["operating_primitive_created_flag"].sum()) == 0, str(int(generic["operating_primitive_created_flag"].sum())), "0"),
            gate("macro_operating_primitive_zero", int(macro["operating_primitive_created_flag"].sum()) == 0, str(int(macro["operating_primitive_created_flag"].sum())), "0"),
            gate("no_buy_sell_or_actionability_columns", not forbidden_columns_found([contexts, edges]), "checked", "no actionability/trading columns"),
            gate("backtest_eligible_zero", int(contexts["backtest_eligible_flag"].sum()) == 0 and int(edges["backtest_eligible_flag"].sum()) == 0, f"context={int(contexts['backtest_eligible_flag'].sum())},edge={int(edges['backtest_eligible_flag'].sum())}", "0"),
        ]
    )


def build_alive_review_states_report(contexts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state, group in contexts.groupby("alive_review_state", dropna=False):
        rows.append(
            {
                "alive_review_state": state,
                "event_count": len(group),
                "source_families": "|".join(sorted(group["source_form_family"].dropna().astype(str).unique())),
                "context_types": "|".join(sorted(group["context_type"].dropna().astype(str).unique())),
                "used_for_trading_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("event_count", ascending=False).reset_index(drop=True)


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "overall_strategy",
                "status": "CAPTURED_VIA_CHROME_CHATGPT",
                "summary": "Institutional GPT review said Task732 should promote Task731 from Route to Context Object to Edge, not to actionability. It required all sources to stay alive and all unsafe direct operating facts to remain blocked by extractor guardrails only.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "circuit_detail",
                "status": "CAPTURED_VIA_CHROME_CHATGPT",
                "summary": "Circuit-specific GPT review defined InsiderBehaviorContext, ActivistControlContext, InstitutionalPositioningContext, OwnershipStructureContext, Generic8KClassificationContext, CreditFinancingContext, and MacroPolicyTransmissionContext with alive states, primitive fields, layer links, edge types, and guardrails.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(contexts: pd.DataFrame, edges: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "SOURCE_CIRCUIT_INTERPRETERS_BUILT_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "context_count": len(contexts),
                "edge_count": len(edges),
                "discarded_source_count": int(contexts["source_is_discarded_flag"].sum()),
                "operating_primitive_created_count": int(contexts["operating_primitive_created_flag"].sum()),
                "guardrail_pass": int(guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Review circuit context quality by source family, then build denominator and cross-context interaction checks before any actionability or backtest promotion.",
            }
        ]
    )


def build_pass_fail(
    contexts: pd.DataFrame,
    edges: pd.DataFrame,
    coverage: pd.DataFrame,
    guardrail: pd.DataFrame,
    alive: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("circuit_contexts_created", len(contexts) == 5302, f"rows={len(contexts)}", "5302"),
            gate("context_edges_created", len(edges) == 5302, f"rows={len(edges)}", "5302"),
            gate("coverage_has_seven_families", coverage["source_form_family"].nunique() == 7, f"families={coverage['source_form_family'].nunique()}", "7"),
            gate("alive_states_present", alive["alive_review_state"].nunique() >= 7, f"states={alive['alive_review_state'].nunique()}", ">=7"),
            gate("forbidden_fact_guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "context interpreter only"),
        ]
    )


def forbidden_columns_found(frames: list[pd.DataFrame]) -> bool:
    forbidden = ["buy", "sell", "actionability", "future_return", "winner", "loser", "net_return", "costed_return"]
    for frame in frames:
        for col in frame.columns:
            if any(token in str(col).lower() for token in forbidden):
                return True
    return False


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    contexts: pd.DataFrame,
    edges: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task732_circuit_contexts.jsonl", contexts)
    write_jsonl(out_dir / "task732_context_edges.jsonl", edges)
    (out_dir / "task_732_source_circuit_interpreters.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task732 Source Circuit Interpreters",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        "- Status phrase: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Contexts: {int(d['context_count'])}",
        f"- Edges: {int(d['edge_count'])}",
        f"- Discarded sources: {int(d['discarded_source_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task732 builds circuit-specific context objects on top of Task731 source routes. It keeps all sources alive, separates primitive extraction by circuit, and emits typed review-only edges into the five-layer brain. It does not create final actionability, allocation, or backtest eligibility.",
        "",
        "### Circuit Coverage",
        "",
        frame_to_markdown(outputs["task732_circuit_coverage_report.csv"]),
        "",
        "### Forbidden Fact Guardrail",
        "",
        frame_to_markdown(outputs["task732_forbidden_fact_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task732_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- Conclusion: the sources are alive and now have dedicated interpretation circuits.",
        "- Form4 does insider behavior only.",
        "- 13D/13G does activist/control only.",
        "- 13F does institutional positioning only.",
        "- Ownership filings do float/holder structure only.",
        "- Generic 8-K gets classified before any operating claim.",
        "- Financing 8-K becomes funding/dilution/liquidity context.",
        "- Macro/policy becomes theme or company-link context.",
        "- No circuit creates buy/sell/actionability.",
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
    lines.append("- `task732_circuit_contexts.jsonl`")
    lines.append("- `task732_context_edges.jsonl`")
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
    artifacts = build_task732(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} contexts={decision['context_count']} "
        f"edges={decision['edge_count']} backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
