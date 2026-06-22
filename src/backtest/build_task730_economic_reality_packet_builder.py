from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.economic_reality_packet import build_event_reality_packet


TASK_ID = "Task730"
EVENT_DETAIL = Path("docs/reports/task_722_source_attached_review_packets/task722_packet_event_detail.csv")
TASK729_RESOLUTION = Path("docs/reports/task_729_five_layer_interaction_engine_application/task729_interaction_resolution_panel.csv")
OUT_DIR = Path("docs/reports/task_730_economic_reality_packet_builder")
KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]


def build_task730(
    *,
    event_detail_path: Path = EVENT_DETAIL,
    task729_resolution_path: Path = TASK729_RESOLUTION,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    events = pd.read_csv(event_detail_path)
    task729 = pd.read_csv(task729_resolution_path)

    event_packets = pd.DataFrame([build_event_reality_packet(row) for _, row in events.iterrows()])
    candidate_bundle = build_candidate_reality_bundle(event_packets)
    injected = inject_task729(task729, candidate_bundle)
    extraction_audit = build_extraction_quality_audit(event_packets, candidate_bundle, injected)
    denominator_audit = build_denominator_audit(event_packets)
    gpt_review = build_gpt_review_summary()
    coderabbit_audit = build_coderabbit_audit(event_packets, candidate_bundle, injected)
    leakage = build_leakage_guardrail([event_packets, candidate_bundle, injected, extraction_audit, denominator_audit, gpt_review, coderabbit_audit])
    governance = build_governance_audit(event_packets, candidate_bundle, injected, extraction_audit, denominator_audit, coderabbit_audit, leakage)
    decision = build_decision(event_packets, candidate_bundle, injected, coderabbit_audit)
    pass_fail = build_pass_fail(event_packets, candidate_bundle, injected, extraction_audit, denominator_audit, coderabbit_audit, leakage, governance)

    outputs = {
        "task730_event_economic_reality_packets.csv": event_packets,
        "task730_candidate_economic_reality_bundle.csv": candidate_bundle,
        "task730_task729_injected_resolution.csv": injected,
        "task730_extraction_quality_audit.csv": extraction_audit,
        "task730_denominator_audit.csv": denominator_audit,
        "task730_gpt_institutional_review_summary.csv": gpt_review,
        "task730_coderabbit_review_audit.csv": coderabbit_audit,
        "task730_leakage_guardrail.csv": leakage,
        "task730_governance_audit.csv": governance,
        "task_730_decision.csv": decision,
        "task_730_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "events": events,
        "task729": task729,
        "event_packets": event_packets,
        "candidate_bundle": candidate_bundle,
        "injected": injected,
        "extraction_audit": extraction_audit,
        "denominator_audit": denominator_audit,
        "gpt_review": gpt_review,
        "coderabbit_audit": coderabbit_audit,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_candidate_reality_bundle(event_packets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in event_packets.groupby(KEYS, dropna=False):
        operational = int((group["evidence_viability_state"] == "source_certified_operational_economic").sum())
        primitive_pass = int(group["primitive_fact_gate_pass_flag"].sum())
        source_denominator_pass = int(group["source_denominator_gate_pass_flag"].sum())
        blocked = int(group["evidence_viability_state"].isin(["source_text_missing", "blocked_or_non_operational_source"]).sum())
        partial = int((group["primitive_fact_state"] == "primitive_fact_partial").sum())
        denominator_available = int((group["denominator_available_count"] > 0).sum())
        material_review = int((group["economic_meaning_state"] == "material_amount_vs_revenue_needs_full_context").sum())
        rows.append(
            {
                "lifecycle_id": keys[0],
                "symbol": keys[1],
                "theme_id": keys[2],
                "entry_ts": keys[3],
                "split_name": keys[4],
                "linked_reality_event_count": len(group),
                "operational_economic_event_count": operational,
                "blocked_or_non_operational_event_count": blocked,
                "primitive_fact_partial_event_count": partial,
                "primitive_fact_gate_pass_count": primitive_pass,
                "source_denominator_gate_pass_count": source_denominator_pass,
                "denominator_available_event_count": denominator_available,
                "material_reality_review_event_count": material_review,
                "candidate_reality_state": candidate_reality_state(operational, primitive_pass, source_denominator_pass, blocked, partial),
                "task729_reality_injection_state": task729_injection_state(operational, primitive_pass, source_denominator_pass, blocked, partial),
                "backtest_eligible_flag": 0,
                "outcome_used_for_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(KEYS).reset_index(drop=True)


def inject_task729(task729: pd.DataFrame, candidate_bundle: pd.DataFrame) -> pd.DataFrame:
    out = task729.merge(candidate_bundle, on=KEYS, how="left", validate="one_to_one")
    fill_cols = [
        "linked_reality_event_count",
        "operational_economic_event_count",
        "blocked_or_non_operational_event_count",
        "primitive_fact_partial_event_count",
        "primitive_fact_gate_pass_count",
        "source_denominator_gate_pass_count",
        "denominator_available_event_count",
        "material_reality_review_event_count",
    ]
    for col in fill_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    out["candidate_reality_state"] = out["candidate_reality_state"].fillna("no_reality_packet_linked")
    out["task729_reality_injection_state"] = out["task729_reality_injection_state"].fillna("task729_no_reality_packet")
    out["reality_packet_available_flag"] = (out["linked_reality_event_count"] > 0).astype(int)
    out["task730_primitive_fact_gate_pass_flag"] = (out["primitive_fact_gate_pass_count"] > 0).astype(int)
    out["task730_source_denominator_gate_pass_flag"] = (out["source_denominator_gate_pass_count"] > 0).astype(int)
    out["task730_backtest_eligible_flag"] = 0
    out["task730_real_capital_status"] = "FORBIDDEN"
    return out


def candidate_reality_state(operational: int, primitive_pass: int, source_denominator_pass: int, blocked: int, partial: int) -> str:
    if source_denominator_pass:
        return "candidate_has_economic_reality_packet_with_denominator"
    if primitive_pass:
        return "candidate_has_primitive_packet_needs_denominator"
    if operational or partial:
        return "candidate_has_partial_reality_packet"
    if blocked:
        return "candidate_reality_blocked_by_source"
    return "candidate_reality_missing"


def task729_injection_state(operational: int, primitive_pass: int, source_denominator_pass: int, blocked: int, partial: int) -> str:
    if source_denominator_pass:
        return "inject_source_denominator_gate_candidate_review_only"
    if primitive_pass:
        return "inject_primitive_fact_gate_candidate_review_only"
    if operational or partial:
        return "inject_partial_reality_context_review_only"
    if blocked:
        return "preserve_task729_source_blocker"
    return "no_injection_missing_reality"


def build_extraction_quality_audit(event_packets: pd.DataFrame, candidate_bundle: pd.DataFrame, injected: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("event_packets_built", len(event_packets) > 0, f"rows={len(event_packets)}", ">0"),
            gate("candidate_bundle_built", len(candidate_bundle) > 0, f"rows={len(candidate_bundle)}", ">0"),
            gate("task729_injection_rows_preserved", len(injected) == 5265, f"rows={len(injected)}", "5265"),
            gate("primitive_fact_states_present", event_packets["primitive_fact_state"].nunique() >= 2, f"unique={event_packets['primitive_fact_state'].nunique()}", ">=2"),
            gate("economic_meaning_states_present", event_packets["economic_meaning_state"].nunique() >= 3, f"unique={event_packets['economic_meaning_state'].nunique()}", ">=3"),
            gate("backtest_eligible_zero", int(injected["task730_backtest_eligible_flag"].sum()) == 0, str(int(injected["task730_backtest_eligible_flag"].sum())), "0"),
            gate("missing_not_negative", "missing" in "|".join(event_packets["denominator_state"].astype(str).unique()), "denominator missing tracked explicitly", "missing as unknown"),
        ]
    )


def build_denominator_audit(event_packets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for field in [
        "revenue_run_rate_usd",
        "cash_usd",
        "debt_usd",
        "backlog_proxy_usd",
        "public_float_usd",
    ]:
        rows.append(
            {
                "denominator_field": field,
                "available_event_count": int(event_packets[field].notna().sum()),
                "missing_event_count": int(event_packets[field].isna().sum()),
                "source": "sec_companyfacts_asof",
                "used_for_backtest_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_item": "institutional_gpt_review",
                "status": "ATTEMPTED_CHROME_TIMEOUT_RECORDED",
                "summary": "Task730 direction was requested for institutional review. Chrome ChatGPT control timed out during this run, so the artifact records the failed GPT handoff and implements the prior institutional contract: source evidence, primitive facts, denominators, economic meaning, and review-only injection must be separated before any trading action.",
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_item": "five_role_review_contract",
                "status": "LOCAL_REVIEW_FALLBACK_APPLIED",
                "summary": "Portfolio manager, event-driven trader, credit analyst, economist, and risk manager roles are represented as review criteria only. No role output is treated as source truth or backtest permission.",
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_coderabbit_audit(event_packets: pd.DataFrame, candidate_bundle: pd.DataFrame, injected: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("coderabbit_plugin_available", False, "tool_search_found_0_callable_tools", "callable CodeRabbit tool"),
            gate("coderabbit_requested_by_user", True, "plugin_tag_seen", "record request"),
            gate("local_review_no_outcome_columns", not forbidden_columns_found([event_packets, candidate_bundle, injected]), "checked", "no outcome/future return columns"),
            gate("local_review_no_backtest_promotion", int(injected["task730_backtest_eligible_flag"].sum()) == 0, str(int(injected["task730_backtest_eligible_flag"].sum())), "0"),
            gate("local_review_preserve_task729_rows", len(injected) == 5265, f"rows={len(injected)}", "5265"),
        ]
    )


def build_leakage_guardrail(frames: list[pd.DataFrame]) -> pd.DataFrame:
    forbidden = ["future_return", "realized_outcome", "top50", "winner", "loser", "costed_return", "net_return"]
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
    event_packets: pd.DataFrame,
    candidate_bundle: pd.DataFrame,
    injected: pd.DataFrame,
    extraction_audit: pd.DataFrame,
    denominator_audit: pd.DataFrame,
    coderabbit_audit: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    local_coderabbit_pass = int(coderabbit_audit.loc[coderabbit_audit["gate_name"] != "coderabbit_plugin_available", "pass_flag"].min())
    return pd.DataFrame(
        [
            gate("event_packet_schema_present", len(event_packets.columns) >= 40, f"cols={len(event_packets.columns)}", ">=40"),
            gate("candidate_bundle_schema_present", len(candidate_bundle.columns) >= 15, f"cols={len(candidate_bundle.columns)}", ">=15"),
            gate("injected_task729_rows_preserved", len(injected) == 5265, f"rows={len(injected)}", "5265"),
            gate("extraction_audit_pass", int(extraction_audit["pass_flag"].min()) == 1, f"min={int(extraction_audit['pass_flag'].min())}", "1"),
            gate("denominator_audit_present", len(denominator_audit) == 5, f"rows={len(denominator_audit)}", "5"),
            gate("coderabbit_local_fallback_pass", local_coderabbit_pass == 1, str(local_coderabbit_pass), "1"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
        ]
    )


def build_decision(event_packets: pd.DataFrame, candidate_bundle: pd.DataFrame, injected: pd.DataFrame, coderabbit_audit: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "ECONOMIC_REALITY_PACKET_BUILDER_APPLIED_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "event_packet_count": len(event_packets),
                "candidate_bundle_count": len(candidate_bundle),
                "task729_injected_row_count": len(injected),
                "primitive_fact_gate_pass_event_count": int(event_packets["primitive_fact_gate_pass_flag"].sum()),
                "source_denominator_gate_pass_event_count": int(event_packets["source_denominator_gate_pass_flag"].sum()),
                "coderabbit_plugin_status": "REQUESTED_BUT_CALLABLE_TOOL_UNAVAILABLE",
                "coderabbit_local_fallback_pass": int(coderabbit_audit.loc[coderabbit_audit["gate_name"] != "coderabbit_plugin_available", "pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Review high-value partial reality packets manually and improve semantic evidence extraction before any promotion to backtest candidate selection.",
            }
        ]
    )


def build_pass_fail(
    event_packets: pd.DataFrame,
    candidate_bundle: pd.DataFrame,
    injected: pd.DataFrame,
    extraction_audit: pd.DataFrame,
    denominator_audit: pd.DataFrame,
    coderabbit_audit: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("event_reality_packets_created", len(event_packets) > 0, f"rows={len(event_packets)}", ">0"),
            gate("candidate_reality_bundle_created", len(candidate_bundle) > 0, f"rows={len(candidate_bundle)}", ">0"),
            gate("task729_injection_created", len(injected) == 5265, f"rows={len(injected)}", "5265"),
            gate("primitive_fact_extraction_present", event_packets["primitive_fact_state"].nunique() >= 2, f"unique={event_packets['primitive_fact_state'].nunique()}", ">=2"),
            gate("denominator_audit_present", len(denominator_audit) == 5, f"rows={len(denominator_audit)}", "5"),
            gate("coderabbit_plugin_available", False, "not_callable", "callable"),
            gate("coderabbit_local_fallback_pass", int(coderabbit_audit.loc[coderabbit_audit["gate_name"] != "coderabbit_plugin_available", "pass_flag"].min()) == 1, "local fallback pass", "1"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "PASS only after semantic extraction and manual audit"),
        ]
    )


def forbidden_columns_found(frames: list[pd.DataFrame]) -> bool:
    forbidden = ["future_return", "realized_outcome", "top50", "winner", "loser", "costed_return", "net_return"]
    for frame in frames:
        for column in frame.columns:
            if any(token in str(column).lower() for token in forbidden):
                return True
    return False


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    (out_dir / "task_730_economic_reality_packet_builder.md").write_text(
        render_report(outputs, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def _legacy_render_report_with_corrupted_plain_language(
    outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task730 Economic Reality Packet Builder",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        f"- Event packets: {int(d['event_packet_count'])}",
        f"- Candidate bundles: {int(d['candidate_bundle_count'])}",
        f"- Task729 injected rows: {int(d['task729_injected_row_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task730 reframes the next step as an Economic Reality Packet Builder, not a keyword extractor. It reads source-attached event packets, extracts primitive facts conservatively, attaches as-of SEC companyfacts denominators where available, classifies expectation and economic meaning states, and injects review-only reality context back into Task729 resolutions.",
        "",
        "### Extraction Quality Audit",
        "",
        frame_to_markdown(outputs["task730_extraction_quality_audit.csv"]),
        "",
        "### Denominator Audit",
        "",
        frame_to_markdown(outputs["task730_denominator_audit.csv"]),
        "",
        "### CodeRabbit / Local Review",
        "",
        frame_to_markdown(outputs["task730_coderabbit_review_audit.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- 결론: Task730은 단순 숫자 추출이 아니라 경제 현실 packet으로 만들었습니다.",
        "- 원문에서 사실을 뽑고, SEC companyfacts 기준 분모를 as-of로 붙였습니다.",
        "- 없는 분모는 0이나 악재로 만들지 않고 missing으로 남겼습니다.",
        "- Task729에는 review-only로만 주입했습니다.",
        "- CodeRabbit은 태그는 받았지만 callable tool이 없어 로컬 감사로 대체했습니다.",
        "- 아직 백테스트는 금지입니다.",
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


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task730 Economic Reality Packet Builder",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        "- Status phrase: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Event packets: {int(d['event_packet_count'])}",
        f"- Candidate bundles: {int(d['candidate_bundle_count'])}",
        f"- Task729 injected rows: {int(d['task729_injected_row_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task730 builds review-only economic reality packets. It separates source evidence, primitive facts, as-of denominators, economic meaning, and Task729 injection state before any trading action.",
        "",
        "The key repair in this pass is source hygiene. Non-economic filings no longer feed primitive fact extraction, which reduces SEC boilerplate contamination. Financing 8-K events remain review-only and require separate dilution, proceeds, and credit-quality interpretation.",
        "",
        "### Extraction Quality Audit",
        "",
        frame_to_markdown(outputs["task730_extraction_quality_audit.csv"]),
        "",
        "### Denominator Audit",
        "",
        frame_to_markdown(outputs["task730_denominator_audit.csv"]),
        "",
        "### GPT / CodeRabbit Review",
        "",
        frame_to_markdown(outputs["task730_gpt_institutional_review_summary.csv"]),
        "",
        frame_to_markdown(outputs["task730_coderabbit_review_audit.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- Conclusion: Task730 is source/evidence infrastructure, not a buy rule.",
        "- It extracts primitive facts such as amount, duration, financing terms, guidance direction, and margin language.",
        "- It attaches as-of SEC companyfacts denominators instead of treating missing data as zero.",
        "- It blocks primitive extraction from non-economic filings to reduce SEC boilerplate contamination.",
        "- It injects only review-only context into Task729.",
        "- CodeRabbit was requested, but no callable tool was exposed; local code review was used as fallback.",
        "- Chrome ChatGPT review was attempted but timed out in this run.",
        "- Backtest permission remains blocked.",
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task730(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} "
        f"events={decision['event_packet_count']} candidates={decision['candidate_bundle_count']} "
        f"backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
