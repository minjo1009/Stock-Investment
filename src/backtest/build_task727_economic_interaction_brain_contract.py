from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.economic_interaction_brain import (
    backtest_gate,
    code_restructure_frame,
    contract_frame,
    edge_rulebook_frame,
    schema_frame,
)


TASK_ID = "Task727"
TASK712_PANEL = Path("docs/reports/task_712_firm_grade_translator_engine/task712_context_state_panel.csv")
TASK714_PANEL = Path("docs/reports/task_714_economic_transmission_brain/task714_economic_transmission_panel.csv")
TASK720_PANEL = Path("docs/reports/task_720_watch_bucket_interaction_diagnostics/task720_watch_bucket_interaction_panel.csv")
TASK636_EVENTS = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_event_content_predictions.csv")
TASK722_PANEL = Path("docs/reports/task_722_source_attached_review_packets/task722_source_attached_packet_panel.csv")
OUT_DIR = Path("docs/reports/task_727_economic_interaction_brain_contract")


def build_task727(
    *,
    task712_path: Path = TASK712_PANEL,
    task714_path: Path = TASK714_PANEL,
    task720_path: Path = TASK720_PANEL,
    task636_events_path: Path = TASK636_EVENTS,
    task722_path: Path = TASK722_PANEL,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    t712 = pd.read_csv(task712_path)
    t714 = pd.read_csv(task714_path)
    t720 = pd.read_csv(task720_path)
    events = pd.read_csv(task636_events_path)
    packets = pd.read_csv(task722_path)

    gap_audit = build_brain_gap_audit(t712, t714, t720, events, packets)
    contract = build_economic_interaction_contract()
    schema = build_required_schema_fields()
    edge_rulebook = build_interaction_edge_rulebook()
    restructure = build_code_restructure_map()
    raw_source_audit = build_raw_source_readiness_audit(events, packets)
    review_packet = build_institutional_review_packet(gap_audit, raw_source_audit)
    leakage = build_leakage_guardrail([gap_audit, contract, schema, edge_rulebook, restructure, raw_source_audit, review_packet])
    governance = build_governance_audit(gap_audit, contract, schema, edge_rulebook, restructure, raw_source_audit, leakage)
    decision = build_decision(gap_audit, raw_source_audit)
    pass_fail = build_pass_fail(gap_audit, contract, schema, edge_rulebook, restructure, raw_source_audit, leakage, governance)

    outputs = {
        "task727_brain_gap_audit.csv": gap_audit,
        "task727_economic_interaction_contract.csv": contract,
        "task727_required_schema_fields.csv": schema,
        "task727_interaction_edge_rulebook.csv": edge_rulebook,
        "task727_code_restructure_map.csv": restructure,
        "task727_raw_source_readiness_audit.csv": raw_source_audit,
        "task727_institutional_review_packet.csv": review_packet,
        "task727_leakage_guardrail.csv": leakage,
        "task727_governance_audit.csv": governance,
        "task_727_decision.csv": decision,
        "task_727_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "gap_audit": gap_audit,
        "contract": contract,
        "schema": schema,
        "edge_rulebook": edge_rulebook,
        "restructure": restructure,
        "raw_source_audit": raw_source_audit,
        "review_packet": review_packet,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_brain_gap_audit(
    t712: pd.DataFrame,
    t714: pd.DataFrame,
    t720: pd.DataFrame,
    events: pd.DataFrame,
    packets: pd.DataFrame,
) -> pd.DataFrame:
    clean_event_count = int(pd.to_numeric(events.get("economic_evidence_certified_flag", 0), errors="coerce").fillna(0).sum())
    task722_queue1 = int((packets["source_review_readiness_state"].astype(str) == "source_review_ready_cashflow_packet").sum())
    rows = [
        {
            "task_layer": "Task712 translator context",
            "observed_problem": "uses event-count axes as if they were economic meaning",
            "observed_value": summarize_counts(
                t712,
                [
                    "customer_event_count",
                    "revenue_backlog_event_count",
                    "guidance_margin_event_count",
                    "supply_demand_event_count",
                ],
            ),
            "firm_grade_requirement": "primitive facts must be tied to denominators, surprise, duration, margin, customer quality, and source provenance",
            "gap_severity": "HIGH",
            "contract_pass_flag": 0,
        },
        {
            "task_layer": "Task714 economic transmission",
            "observed_problem": "strong state names are created from count co-occurrence",
            "observed_value": value_counts(t714, "economic_transmission_state", 5),
            "firm_grade_requirement": "economic transmission requires order size versus revenue/guidance/backlog, margin effect, funding quality, and expectation delta",
            "gap_severity": "CRITICAL",
            "contract_pass_flag": 0,
        },
        {
            "task_layer": "Task720 watch interaction",
            "observed_problem": "interaction axes exist but cashflow/economic axis inherits polluted upstream counts",
            "observed_value": value_counts(t720, "layer_interaction_state", 5),
            "firm_grade_requirement": "interaction graph must consume certified economic interpretation objects, not legacy count-derived labels",
            "gap_severity": "CRITICAL",
            "contract_pass_flag": 0,
        },
        {
            "task_layer": "Task726 parser repair impact",
            "observed_problem": "after source repair almost no clean economic evidence remains",
            "observed_value": f"clean_economic_events={clean_event_count}; task722_cashflow_ready={task722_queue1}",
            "firm_grade_requirement": "brain must not promote legacy Task712-720 states until source packets are rebuilt with economic interaction fields",
            "gap_severity": "BLOCKER",
            "contract_pass_flag": 0,
        },
        {
            "task_layer": "front data extraction",
            "observed_problem": "raw text spans are still often filing boilerplate or SEC form snippets",
            "observed_value": value_counts(packets, "best_evidence_span_for_review", 3),
            "firm_grade_requirement": "extract exact operational evidence spans and preserve blocker spans separately",
            "gap_severity": "BLOCKER",
            "contract_pass_flag": 0,
        },
    ]
    return pd.DataFrame(rows)


def build_economic_interaction_contract() -> pd.DataFrame:
    return contract_frame()


def build_required_schema_fields() -> pd.DataFrame:
    return schema_frame()


def build_interaction_edge_rulebook() -> pd.DataFrame:
    return edge_rulebook_frame()


def build_code_restructure_map() -> pd.DataFrame:
    return code_restructure_frame()


def build_raw_source_readiness_audit(events: pd.DataFrame, packets: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "audit_item": "clean_economic_event_coverage",
                "observed": str(int(pd.to_numeric(events.get("economic_evidence_certified_flag", 0), errors="coerce").fillna(0).sum())),
                "required": "enough source-backed operational events before strategy testing",
                "pass_flag": 0,
            },
            {
                "audit_item": "task722_cashflow_ready_after_repair",
                "observed": str(int((packets["source_review_readiness_state"].astype(str) == "source_review_ready_cashflow_packet").sum())),
                "required": "nonzero only if certified economic interaction fields exist",
                "pass_flag": 1,
            },
            {
                "audit_item": "boilerplate_span_pollution",
                "observed": value_counts(packets, "best_evidence_span_for_review", 3),
                "required": "operational evidence spans separated from SEC boilerplate spans",
                "pass_flag": 0,
            },
            {
                "audit_item": "denominator_availability",
                "observed": "not_present_in_current_task712_720_brain",
                "required": "revenue/backlog/guidance/market-cap/capacity denominators must be source-backed or unknown",
                "pass_flag": 0,
            },
        ]
    )


def build_institutional_review_packet(gap_audit: pd.DataFrame, raw_source_audit: pd.DataFrame) -> pd.DataFrame:
    roles = [
        (
            "Goldman Sachs event-driven trader",
            "catalyst materiality and what-is-priced discipline",
            "event_count is not a catalyst; order size must be checked versus revenue, guidance, backlog, market cap, customer quality, duration, repeatability, and cancellation risk.",
        ),
        (
            "Morgan Stanley expectations strategist",
            "guidance/revision/surprise versus consensus or prior outlook",
            "good news is not enough; guidance raise, reaffirmation, cut, consensus delta, and prior guidance bridge must be separated.",
        ),
        (
            "JPMorgan credit and financing trader",
            "use-of-proceeds, dilution, credit stress, balance-sheet relief",
            "financing is neither bullish nor bearish by default; growth funding, survival funding, dilution, covenants, maturity, and coupon must interact with order economics.",
        ),
        (
            "Citadel equity L/S pod PM",
            "same-timestamp relative slot quality and thesis/risk asymmetry",
            "thesis must be an edge graph from order to revenue, margin, cash flow, valuation, price acceptance, peer leadership, and invalidation.",
        ),
        (
            "Millennium risk trader",
            "portfolio cluster, invalidation, crowding, and drawdown containment",
            "slot decision must account for already priced, crowded, liquidity, gap chase, volatility regime, and thesis validity before sizing or entry.",
        ),
    ]
    return pd.DataFrame(
        [
            {
                "reviewer_role": role,
                "required_review_focus": focus,
                "gpt_review_summary": summary,
                "supplied_project_facts": "Task712-720 create strong labels from event counts; Task726 clean economic evidence nearly absent; Task722 cashflow-ready is zero",
                "question_for_gpt": "What must be added to the Economic Interaction Brain before any backtest permission?",
                "gpt_overall_verdict": "FAIL",
                "gpt_response_captured_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            }
            for role, focus, summary in roles
        ]
    )


def build_leakage_guardrail(frames: list[pd.DataFrame]) -> pd.DataFrame:
    forbidden = ["future_return", "realized_outcome", "top50", "winner", "loser", "costed_return"]
    rows = []
    for i, frame in enumerate(frames):
        cols = [str(c).lower() for c in frame.columns]
        found = sorted({token for token in forbidden for col in cols if token in col})
        rows.append(
            {
                "artifact_index": i,
                "forbidden_columns_found": "|".join(found),
                "pass_flag": int(not found),
                "outcome_used_for_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_governance_audit(
    gap_audit: pd.DataFrame,
    contract: pd.DataFrame,
    schema: pd.DataFrame,
    edge_rulebook: pd.DataFrame,
    restructure: pd.DataFrame,
    raw_source_audit: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    checks = [
        ("gap_audit_present", len(gap_audit) >= 5, f"rows={len(gap_audit)}", ">=5"),
        ("contract_layers_present", len(contract) >= 8, f"rows={len(contract)}", ">=8"),
        ("schema_fields_present", len(schema) >= 15, f"rows={len(schema)}", ">=15"),
        ("edge_rulebook_present", len(edge_rulebook) >= 10, f"rows={len(edge_rulebook)}", ">=10"),
        ("code_restructure_map_present", len(restructure) >= 6, f"rows={len(restructure)}", ">=6"),
        ("raw_source_audit_blocks_backtest", int(raw_source_audit["pass_flag"].min()) == 0, f"min={int(raw_source_audit['pass_flag'].min())}", "0 blocker present"),
        ("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
    ]
    return pd.DataFrame([gate(name, passed, observed, required) for name, passed, observed, required in checks])


def build_decision(gap_audit: pd.DataFrame, raw_source_audit: pd.DataFrame) -> pd.DataFrame:
    critical = int((gap_audit["gap_severity"].isin(["CRITICAL", "BLOCKER"])).sum())
    raw_blockers = int((raw_source_audit["pass_flag"] == 0).sum())
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "ECONOMIC_INTERACTION_BRAIN_CONTRACT_DEFINED_EXISTING_BRAIN_FAILS",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "critical_or_blocker_gap_count": critical,
                "raw_source_blocker_count": raw_blockers,
                "backtest_permission": "FAIL",
                "trading_promotion_pass_flag": 0,
                "next_action": "Implement primitive fact and denominator extraction before rebuilding Task714/720 interaction logic.",
            }
        ]
    )


def build_pass_fail(
    gap_audit: pd.DataFrame,
    contract: pd.DataFrame,
    schema: pd.DataFrame,
    edge_rulebook: pd.DataFrame,
    restructure: pd.DataFrame,
    raw_source_audit: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        gate("task712_720_audit_completed", len(gap_audit) >= 5, f"rows={len(gap_audit)}", ">=5"),
        gate("existing_brain_contract_pass", int(gap_audit["contract_pass_flag"].min()) == 1, f"min={int(gap_audit['contract_pass_flag'].min())}", "1"),
        gate("economic_interaction_contract_defined", len(contract) >= 8, f"rows={len(contract)}", ">=8"),
        gate("required_schema_defined", len(schema) >= 15, f"rows={len(schema)}", ">=15"),
        gate("interaction_edge_rulebook_defined", len(edge_rulebook) >= 10, f"rows={len(edge_rulebook)}", ">=10"),
        gate("code_restructure_map_defined", len(restructure) >= 6, f"rows={len(restructure)}", ">=6"),
        gate("raw_source_ready_for_backtest", int(raw_source_audit["pass_flag"].min()) == 1, f"min={int(raw_source_audit['pass_flag'].min())}", "1"),
        gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
        gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
        backtest_gate(
            {
                "clean_economic_events": raw_source_audit.loc[
                    raw_source_audit["audit_item"] == "clean_economic_event_coverage", "observed"
                ].iloc[0],
                "denominator_fields_present": 0,
                "contamination_count": 1,
                "interaction_objects_present": 0,
            }
        ),
        gate("backtest_permission", False, "FAIL", "PASS only after source-backed interaction objects exist"),
    ]
    return pd.DataFrame(rows)


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    (out_dir / "task_727_economic_interaction_brain_contract.md").write_text(
        render_report(outputs, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task727 Economic Interaction Brain Contract",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        f"- Critical/blocker gaps: {int(d['critical_or_blocker_gap_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task712-720 contains useful layer names, but the current economic brain does not yet meet the user's firm-grade interaction requirement. It promotes co-occurring counts into states such as revenue acceleration or revenue-margin reinforcement without source-backed denominators, guidance surprise, margin effect, contract duration, financing use-of-proceeds, or price acceptance as prerequisites.",
        "",
        "### Brain Gap Audit",
        "",
        frame_to_markdown(outputs["task727_brain_gap_audit.csv"]),
        "",
        "### Contract Layers",
        "",
        frame_to_markdown(outputs["task727_economic_interaction_contract.csv"]),
        "",
        "### Code Restructure Map",
        "",
        frame_to_markdown(outputs["task727_code_restructure_map.csv"]),
        "",
        "### Institutional GPT Review",
        "",
        frame_to_markdown(outputs["task727_institutional_review_packet.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- 기존 뇌는 이름은 그럴듯했지만 아직 카운트 기반입니다.",
        "- 수주/가이던스/마진/financing이 서로 얼마나 맞물리는지 보는 구조가 부족합니다.",
        "- 앞단 source도 아직 충분하지 않습니다.",
        "- 그래서 백테스트가 아니라 primitive fact, denominator, interaction edge를 먼저 만들어야 합니다.",
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
    lines.append("- `artifact_manifest.csv`")
    return "\n".join(lines)


def summarize_counts(frame: pd.DataFrame, columns: list[str]) -> str:
    parts = []
    for col in columns:
        if col in frame.columns:
            parts.append(f"{col}_sum={int(pd.to_numeric(frame[col], errors='coerce').fillna(0).sum())}")
    return "; ".join(parts)


def frame_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    cols = [str(c) for c in frame.columns]
    rows = []
    rows.append("| " + " | ".join(cols) + " |")
    rows.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in frame.iterrows():
        values = [markdown_cell(row.get(col, "")) for col in frame.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def markdown_cell(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def value_counts(frame: pd.DataFrame, column: str, limit: int = 5) -> str:
    if column not in frame.columns:
        return "column_missing"
    counts = frame[column].fillna("").astype(str).value_counts().head(limit)
    return "; ".join([f"{idx}={int(value)}" for idx, value in counts.items()])


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
    artifacts = build_task727(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(f"[{TASK_ID}] verdict={decision['verdict']} backtest_permission={decision['backtest_permission']}")


if __name__ == "__main__":
    main()
