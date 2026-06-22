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
from src.backtest.source_information_router import SOURCE_ROUTE_MAP, build_cross_circuit_edges, route_source_event


TASK_ID = "Task731"
EVENT_DETAIL = Path("docs/reports/task_722_source_attached_review_packets/task722_packet_event_detail.csv")
OUT_DIR = Path("docs/reports/task_731_source_information_router")
KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]


def build_task731(*, event_detail_path: Path = EVENT_DETAIL, out_dir: Path = OUT_DIR) -> dict[str, pd.DataFrame]:
    events = pd.read_csv(event_detail_path)
    routed_events = build_routed_events(events)
    route_map = build_route_map_frame()
    permission_matrix = build_permission_matrix(route_map)
    non_operating_context = routed_events[routed_events["operating_extractor_permission_state"] != "allowed"].copy()
    cross_edges = build_cross_circuit_edges(routed_events)
    pollution_guardrail = build_pollution_guardrail(routed_events, cross_edges)
    gpt_review = build_gpt_review()
    decision = build_decision(routed_events, cross_edges, pollution_guardrail)
    pass_fail = build_pass_fail(routed_events, route_map, permission_matrix, non_operating_context, cross_edges, pollution_guardrail)

    outputs = {
        "task731_source_route_map.csv": route_map,
        "task731_allowed_fact_family_matrix.csv": permission_matrix,
        "task731_source_routed_events.csv": routed_events,
        "task731_operating_extractor_permission.csv": routed_events[KEYS + ["source_form_family", "source_route_state", "route_circuit", "operating_extractor_permission_state", "operating_fact_creation_allowed_flag", "source_is_discarded_flag"]],
        "task731_non_operating_context_facts.csv": non_operating_context,
        "task731_cross_circuit_edges.csv": cross_edges,
        "task731_pollution_guardrail.csv": pollution_guardrail,
        "task731_gpt_institutional_review_summary.csv": gpt_review,
        "task_731_decision.csv": decision,
        "task_731_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, routed_events, decision, pass_fail)
    return {
        "events": events,
        "routed_events": routed_events,
        "route_map": route_map,
        "permission_matrix": permission_matrix,
        "non_operating_context": non_operating_context,
        "cross_edges": cross_edges,
        "pollution_guardrail": pollution_guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_routed_events(events: pd.DataFrame) -> pd.DataFrame:
    routed = pd.DataFrame([route_source_event(row) for _, row in events.iterrows()])
    base = events[KEYS + ["source_form_family", "interpretation_blocker", "source_text_certified_flag", "economic_evidence_certified_flag"]].copy()
    return pd.concat([base.reset_index(drop=True), routed.drop(columns=["source_form_family"]).reset_index(drop=True)], axis=1)


def build_route_map_frame() -> pd.DataFrame:
    rows = []
    for route in SOURCE_ROUTE_MAP.values():
        item = route_source_event(pd.Series({"source_form_family": route.source_form_family}))
        rows.append(item)
    return pd.DataFrame(rows).sort_values("source_form_family").reset_index(drop=True)


def build_permission_matrix(route_map: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in route_map.iterrows():
        for fact in str(row["allowed_fact_families"]).split("|"):
            if fact:
                rows.append(matrix_row(row, fact, "allowed"))
        for fact in str(row["forbidden_fact_families"]).split("|"):
            if fact:
                rows.append(matrix_row(row, fact, "forbidden"))
    return pd.DataFrame(rows)


def matrix_row(row: pd.Series, fact_family: str, permission: str) -> dict[str, object]:
    return {
        "source_form_family": row["source_form_family"],
        "source_route_state": row["source_route_state"],
        "route_circuit": row["route_circuit"],
        "fact_family": fact_family,
        "permission": permission,
        "used_for_trading_flag": 0,
    }


def build_pollution_guardrail(routed_events: pd.DataFrame, cross_edges: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("all_events_preserved", len(routed_events) == 5302, f"rows={len(routed_events)}", "5302"),
            gate("no_source_discarded", int(routed_events["source_is_discarded_flag"].sum()) == 0, str(int(routed_events["source_is_discarded_flag"].sum())), "0"),
            gate("all_events_have_route", routed_events["source_route_state"].notna().all(), f"missing={int(routed_events['source_route_state'].isna().sum())}", "0 missing"),
            gate("non_operating_cannot_create_operating_catalyst", int(routed_events["operating_fact_creation_allowed_flag"].sum()) == 0, str(int(routed_events["operating_fact_creation_allowed_flag"].sum())), "0"),
            gate("cross_edges_present_for_routed_events", len(cross_edges) == len(routed_events), f"edges={len(cross_edges)}", f"{len(routed_events)}"),
            gate("backtest_eligible_zero", int(routed_events["backtest_eligible_flag"].sum()) == 0, str(int(routed_events["backtest_eligible_flag"].sum())), "0"),
        ]
    )


def build_gpt_review() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_item": "institutional_gpt_review",
                "status": "CAPTURED_VIA_CHROME_CHATGPT",
                "summary": "Institutional-role GPT review rejected the blocked-source framing. It recommended source-specific routing: source_form_family -> source-specific brain circuit -> typed primitive facts -> relation edges -> operating catalyst interaction -> final context bundle.",
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_item": "core_instruction",
                "status": "APPLIED",
                "summary": "Sources are not discarded. Only unsafe extractor permissions are denied. Non-operating sources can modify confidence, risk, slot, or special-situation routing but cannot create revenue/order/backlog/guidance/margin facts.",
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(routed_events: pd.DataFrame, cross_edges: pd.DataFrame, pollution_guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "SOURCE_INFORMATION_ROUTER_BUILT_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "event_count": len(routed_events),
                "discarded_source_count": int(routed_events["source_is_discarded_flag"].sum()),
                "cross_circuit_edge_count": len(cross_edges),
                "pollution_guardrail_pass": int(pollution_guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Build circuit-specific primitive extractors for insider, ownership, institutional positioning, generic 8-K classification, financing, and macro-policy transmission before any trading promotion.",
            }
        ]
    )


def build_pass_fail(
    routed_events: pd.DataFrame,
    route_map: pd.DataFrame,
    permission_matrix: pd.DataFrame,
    non_operating_context: pd.DataFrame,
    cross_edges: pd.DataFrame,
    pollution_guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("source_route_map_created", len(route_map) == 7, f"rows={len(route_map)}", "7"),
            gate("allowed_fact_family_matrix_created", len(permission_matrix) > 0, f"rows={len(permission_matrix)}", ">0"),
            gate("source_routed_events_created", len(routed_events) == 5302, f"rows={len(routed_events)}", "5302"),
            gate("non_operating_context_preserved", len(non_operating_context) == 5302, f"rows={len(non_operating_context)}", "5302 review-only rows"),
            gate("cross_circuit_edges_created", len(cross_edges) == 5302, f"rows={len(cross_edges)}", "5302"),
            gate("pollution_guardrail_all_pass", int(pollution_guardrail["pass_flag"].min()) == 1, f"min={int(pollution_guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "routing only, no trading promotion"),
        ]
    )


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], routed_events: pd.DataFrame, decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task731_source_routed_events.jsonl", routed_events)
    write_jsonl(out_dir / "task731_cross_circuit_edges.jsonl", outputs["task731_cross_circuit_edges.csv"])
    (out_dir / "task_731_source_information_router.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task731 Source Information Router",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        "- Status phrase: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Events routed: {int(d['event_count'])}",
        f"- Discarded sources: {int(d['discarded_source_count'])}",
        f"- Cross-circuit edges: {int(d['cross_circuit_edge_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task731 replaces the Task730 blocked-source framing with a source information router. Every source is preserved and routed to a source-specific brain circuit. Extractor restrictions are recorded separately from source availability.",
        "",
        "Non-operating sources cannot create operating catalyst facts such as revenue, order, backlog, guidance, or margin. They can still modify confidence, risk budget, slot qualification, crowding, special-situation routing, and macro/theme context through typed edges.",
        "",
        "### Route Map",
        "",
        frame_to_markdown(outputs["task731_source_route_map.csv"]),
        "",
        "### Pollution Guardrail",
        "",
        frame_to_markdown(outputs["task731_pollution_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task731_gpt_institutional_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- Conclusion: sources are not thrown away.",
        "- The fix is routing, not blocking.",
        "- Form4 goes to insider behavior.",
        "- 13D/13G goes to activist/control.",
        "- 13F goes to institutional positioning.",
        "- Ownership filings go to ownership structure.",
        "- Financing 8-K goes to credit/financing.",
        "- Macro/policy goes to macro transmission.",
        "- These sources cannot directly create revenue/order/guidance/margin facts.",
        "- They can change confidence, risk, slot, and context after typed interaction edges.",
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
    lines.append("- `task731_source_routed_events.jsonl`")
    lines.append("- `task731_cross_circuit_edges.jsonl`")
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
    artifacts = build_task731(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} events={decision['event_count']} "
        f"discarded={decision['discarded_source_count']} backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
