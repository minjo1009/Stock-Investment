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
from src.backtest.operating_candidate_deep_dive import review_operating_candidate


TASK_ID = "Task734"
OPERATING_EDGES = Path("docs/reports/task_733_circuit_quality_operating_connection/task733_operating_connection_edges.csv")
EVENT_DETAIL = Path("docs/reports/task_722_source_attached_review_packets/task722_packet_event_detail.csv")
OUT_DIR = Path("docs/reports/task_734_operating_connection_candidate_deep_dive")
KEYS = ["event_id", "lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]


def build_task734(
    *,
    operating_edges_path: Path = OPERATING_EDGES,
    event_detail_path: Path = EVENT_DETAIL,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    operating_edges = pd.read_csv(operating_edges_path)
    events = pd.read_csv(event_detail_path)
    candidates = operating_edges.merge(
        events[KEYS + ["source_form_family", "content_interpretation_evidence_span", "raw_text_path"]],
        on=KEYS,
        how="left",
        validate="many_to_one",
    )
    review = pd.DataFrame([review_operating_candidate(row) for _, row in candidates.iterrows()])
    summary = build_summary(review)
    guardrail = build_guardrail(review)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(review, guardrail)
    pass_fail = build_pass_fail(review, summary, guardrail)
    outputs = {
        "task734_candidate_deep_dive.csv": review,
        "task734_candidate_summary.csv": summary,
        "task734_guardrail.csv": guardrail,
        "task734_gpt_review_summary.csv": gpt_review,
        "task_734_decision.csv": decision,
        "task_734_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, review, decision, pass_fail)
    return {
        "operating_edges": operating_edges,
        "events": events,
        "candidates": candidates,
        "review": review,
        "summary": summary,
        "guardrail": guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_summary(review: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = review.groupby(["refined_context_family", "refined_permission_state", "refined_rule_id"], dropna=False)
    for keys, group in grouped:
        family, permission, rule = keys
        rows.append(
            {
                "refined_context_family": family,
                "refined_permission_state": permission,
                "refined_rule_id": rule,
                "candidate_count": len(group),
                "false_positive_count": int(group["false_positive_flag"].sum()),
                "operating_candidate_after_review_count": int(group["operating_connection_candidate_after_review_flag"].sum()),
                "operating_supported_after_review_count": int(group["operating_connection_supported_after_review_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("candidate_count", ascending=False).reset_index(drop=True)


def build_guardrail(review: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("nine_candidates_reviewed", len(review) == 9, f"rows={len(review)}", "9"),
            gate("compensation_not_operating", not_bad(review, "compensation_context"), str(count_family(review, "compensation_context")), "not operating"),
            gate("governance_not_operating", not_bad(review, "governance_board_context") and not_bad(review, "governance_compensation_context"), str(count_family(review, "governance_board_context") + count_family(review, "governance_compensation_context")), "not operating"),
            gate("investment_not_operating_by_default", not_bad(review, "strategic_transaction_context"), str(count_family(review, "strategic_transaction_context")), "review_required"),
            gate("mna_candidate_not_supported", int(review["operating_connection_supported_after_review_flag"].sum()) == 0, str(int(review["operating_connection_supported_after_review_flag"].sum())), "0 supported until transmission evidence"),
            gate("at_least_one_candidate_survives_as_review", int(review["operating_connection_candidate_after_review_flag"].sum()) >= 1, str(int(review["operating_connection_candidate_after_review_flag"].sum())), ">=1"),
            gate("false_positive_detected", int(review["false_positive_flag"].sum()) >= 1, str(int(review["false_positive_flag"].sum())), ">=1"),
            gate("trading_flags_zero", int(review["used_for_trading_flag"].sum()) == 0 and int(review["backtest_eligible_flag"].sum()) == 0, f"trading={int(review['used_for_trading_flag'].sum())},backtest={int(review['backtest_eligible_flag'].sum())}", "0"),
        ]
    )


def not_bad(review: pd.DataFrame, family: str) -> bool:
    subset = review[review["refined_context_family"] == family]
    return int(subset["operating_connection_candidate_after_review_flag"].sum()) == 0 if not subset.empty else True


def count_family(review: pd.DataFrame, family: str) -> int:
    return int((review["refined_context_family"] == family).sum())


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "candidate_deep_dive",
                "status": "CAPTURED_VIA_CHROME_CHATGPT",
                "summary": "Institutional GPT review judged 8 of 9 Task733 operating connection candidates as false positives and kept only the RKLB GEOST acquisition as a strategic M&A review candidate, not an operating-supported catalyst.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "generic_8k_classifier_repair",
                "status": "CAPTURED_VIA_CHROME_CHATGPT",
                "summary": "GPT review recommended splitting generic 8-K agreement family before operating permission: compensation, governance, financing, investment, M&A, and operating transmission.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(review: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "OPERATING_CONNECTION_CANDIDATE_DEEP_DIVE_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "prior_candidate_count": len(review),
                "false_positive_count": int(review["false_positive_flag"].sum()),
                "candidate_after_review_count": int(review["operating_connection_candidate_after_review_flag"].sum()),
                "supported_after_review_count": int(review["operating_connection_supported_after_review_flag"].sum()),
                "guardrail_pass": int(guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Repair generic 8-K classifier upstream with agreement-family classification and inspect RKLB GEOST acquisition for operating transmission evidence before any bundle promotion.",
            }
        ]
    )


def build_pass_fail(review: pd.DataFrame, summary: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("candidate_deep_dive_created", len(review) == 9, f"rows={len(review)}", "9"),
            gate("summary_created", len(summary) > 0, f"rows={len(summary)}", ">0"),
            gate("guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("false_positive_count_expected", int(review["false_positive_flag"].sum()) == 8, str(int(review["false_positive_flag"].sum())), "8"),
            gate("one_candidate_survives", int(review["operating_connection_candidate_after_review_flag"].sum()) == 1, str(int(review["operating_connection_candidate_after_review_flag"].sum())), "1"),
            gate("zero_supported", int(review["operating_connection_supported_after_review_flag"].sum()) == 0, str(int(review["operating_connection_supported_after_review_flag"].sum())), "0"),
            gate("backtest_permission", False, "FAIL", "deep dive review only"),
        ]
    )


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], review: pd.DataFrame, decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task734_candidate_deep_dive.jsonl", review)
    (out_dir / "task_734_operating_connection_candidate_deep_dive.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task734 Operating Connection Candidate Deep Dive",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        "- Status phrase: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Prior candidates: {int(d['prior_candidate_count'])}",
        f"- False positives: {int(d['false_positive_count'])}",
        f"- Candidates after review: {int(d['candidate_after_review_count'])}",
        f"- Supported after review: {int(d['supported_after_review_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task734 manually deep-dives the 9 Task733 operating connection candidates using source text windows. It classifies agreement family before operating permission and keeps all outputs review-only.",
        "",
        "### Candidate Summary",
        "",
        frame_to_markdown(outputs["task734_candidate_summary.csv"]),
        "",
        "### Guardrail",
        "",
        frame_to_markdown(outputs["task734_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task734_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- Conclusion: 8 of 9 operating candidates were false positives.",
        "- Compensation, director appointment, severance, and investment-agreement boilerplate should not be operating catalysts.",
        "- RKLB GEOST survives only as a strategic M&A review candidate.",
        "- It is not operating-supported yet.",
        "- Backtest remains blocked.",
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
    lines.append("- `task734_candidate_deep_dive.jsonl`")
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
    artifacts = build_task734(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} prior={decision['prior_candidate_count']} "
        f"false_positive={decision['false_positive_count']} survivors={decision['candidate_after_review_count']} "
        f"backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
