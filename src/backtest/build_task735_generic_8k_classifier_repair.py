from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.generic_8k_classifier import classify_generic_8k_text


TASK_ID = "Task735"
EVENT_DETAIL = Path("docs/reports/task_722_source_attached_review_packets/task722_packet_event_detail.csv")
TASK734_REVIEW = Path("docs/reports/task_734_operating_connection_candidate_deep_dive/task734_candidate_deep_dive.csv")
OUT_DIR = Path("docs/reports/task_735_generic_8k_classifier_repair")
TAG_RE = re.compile(r"<[^>]+>")
KEYS = ["event_id", "lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]


def build_task735(
    *,
    event_detail_path: Path = EVENT_DETAIL,
    task734_review_path: Path = TASK734_REVIEW,
    out_dir: Path = OUT_DIR,
) -> dict[str, pd.DataFrame]:
    events = pd.read_csv(event_detail_path)
    generic_events = events[events["source_form_family"] == "generic_8k"].copy()
    classification = classify_events(generic_events)
    distribution = build_distribution(classification)
    prior_reclass = reclassify_task734_prior_candidates(classification, task734_review_path)
    guardrail = build_guardrail(classification, prior_reclass)
    gpt_review = build_gpt_review_summary()
    decision = build_decision(classification, prior_reclass, guardrail)
    pass_fail = build_pass_fail(classification, distribution, prior_reclass, guardrail)
    outputs = {
        "task735_generic_8k_classification.csv": classification,
        "task735_agreement_family_distribution.csv": distribution,
        "task735_task734_prior_candidate_reclassification.csv": prior_reclass,
        "task735_guardrail.csv": guardrail,
        "task735_gpt_review_summary.csv": gpt_review,
        "task_735_decision.csv": decision,
        "task_735_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, classification, prior_reclass, decision, pass_fail)
    return {
        "events": events,
        "classification": classification,
        "distribution": distribution,
        "prior_reclass": prior_reclass,
        "guardrail": guardrail,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def classify_events(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in events.iterrows():
        text = source_text(row)
        classification = classify_generic_8k_text(text)
        record = {col: row.get(col, "") for col in KEYS}
        record.update(
            {
                "source_form_family": row.get("source_form_family", ""),
                "event_title": row.get("event_title", ""),
                "event_date": row.get("event_date", ""),
                "source_text_available_flag": int(bool(text)),
                "source_text_window": text_window(text),
                **classification.to_primitive(),
                "used_for_trading_flag": 0,
                "backtest_eligible_flag": 0,
                "outcome_used_for_assignment_flag": 0,
            }
        )
        rows.append(record)
    return pd.DataFrame(rows)


def build_distribution(classification: pd.DataFrame) -> pd.DataFrame:
    grouped = classification.groupby(["agreement_family_state", "operating_transmission_state", "permission_state"], dropna=False)
    rows = []
    for keys, group in grouped:
        family, transmission, permission = keys
        rows.append(
            {
                "agreement_family_state": family,
                "operating_transmission_state": transmission,
                "permission_state": permission,
                "event_count": len(group),
                "operating_candidate_count": int(group["operating_candidate_flag"].sum()),
                "operating_supported_count": int(group["operating_supported_flag"].sum()),
                "backtest_eligible_count": int(group["backtest_eligible_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["event_count", "agreement_family_state"], ascending=[False, True]).reset_index(drop=True)


def reclassify_task734_prior_candidates(classification: pd.DataFrame, task734_review_path: Path) -> pd.DataFrame:
    prior = pd.read_csv(task734_review_path)
    cols = KEYS + [
        "agreement_family_state",
        "operating_transmission_state",
        "permission_state",
        "connection_rule_id",
        "required_next_evidence",
        "operating_candidate_flag",
        "operating_supported_flag",
        "subtype_trace",
    ]
    merged = prior.merge(classification[cols], on=KEYS, how="left", validate="one_to_one", suffixes=("_task734", ""))
    merged["task735_repair_state"] = merged.apply(task735_repair_state, axis=1)
    merged["backtest_eligible_flag"] = 0
    merged["used_for_trading_flag"] = 0
    merged["outcome_used_for_assignment_flag"] = 0
    return merged[
        KEYS
        + [
            "prior_rule_id",
            "refined_context_family",
            "refined_permission_state",
            "agreement_family_state",
            "operating_transmission_state",
            "permission_state",
            "connection_rule_id",
            "operating_candidate_flag",
            "operating_supported_flag",
            "task735_repair_state",
            "required_next_evidence",
            "subtype_trace",
            "used_for_trading_flag",
            "backtest_eligible_flag",
            "outcome_used_for_assignment_flag",
        ]
    ]


def task735_repair_state(row: pd.Series) -> str:
    family = str(row.get("agreement_family_state", ""))
    supported = int(row.get("operating_supported_flag") or 0)
    candidate = int(row.get("operating_candidate_flag") or 0)
    if family in {"compensation_award_context", "governance_board_context", "severance_or_change_in_control_context"}:
        return "false_positive_repaired_to_non_operating_context"
    if family in {"strategic_investment_context", "financing_credit_context"}:
        return "false_positive_repaired_to_review_circuit"
    if family == "strategic_mna_context" and supported == 0:
        return "mna_preserved_without_operating_support"
    if supported:
        return "operating_supported_after_repair"
    if candidate:
        return "operating_candidate_after_repair"
    return "review_required_after_repair"


def build_guardrail(classification: pd.DataFrame, prior_reclass: pd.DataFrame) -> pd.DataFrame:
    compensation_governance = classification[
        classification["agreement_family_state"].isin(
            {"compensation_award_context", "governance_board_context", "severance_or_change_in_control_context"}
        )
    ]
    financing = classification[classification["agreement_family_state"] == "financing_credit_context"]
    weak_agreement = classification[
        ((classification["material_definitive_agreement_flag"] == 1) | (classification["purchase_agreement_flag"] == 1))
        & (classification["operating_primitive_count"] == 0)
    ]
    return pd.DataFrame(
        [
            gate("all_generic_8k_classified", len(classification) == 95, f"rows={len(classification)}", "95"),
            gate("all_have_family_state", no_blank(classification, "agreement_family_state"), "checked", "no blank"),
            gate("all_have_transmission_state", no_blank(classification, "operating_transmission_state"), "checked", "no blank"),
            gate("all_have_permission_rule", no_blank(classification, "permission_state") and no_blank(classification, "connection_rule_id"), "checked", "no blank permission/rule"),
            gate("agreement_alone_not_supported", int(weak_agreement["operating_supported_flag"].sum()) == 0, str(int(weak_agreement["operating_supported_flag"].sum())), "0"),
            gate("compensation_governance_not_operating", int(compensation_governance["operating_candidate_flag"].sum()) == 0, str(int(compensation_governance["operating_candidate_flag"].sum())), "0"),
            gate("financing_routed_not_operating", int(financing["operating_candidate_flag"].sum()) == 0, str(int(financing["operating_candidate_flag"].sum())), "0"),
            gate("task734_prior_nine_reclassified", len(prior_reclass) == 9, f"rows={len(prior_reclass)}", "9"),
            gate("task734_prior_zero_supported", int(prior_reclass["operating_supported_flag"].fillna(0).sum()) == 0, str(int(prior_reclass["operating_supported_flag"].fillna(0).sum())), "0"),
            gate("task734_false_positives_repaired", int(prior_reclass["task735_repair_state"].str.contains("false_positive_repaired", na=False).sum()) >= 8, str(int(prior_reclass["task735_repair_state"].str.contains("false_positive_repaired", na=False).sum())), ">=8"),
            gate("trading_flags_zero", int(classification["used_for_trading_flag"].sum()) == 0 and int(classification["backtest_eligible_flag"].sum()) == 0, f"trading={int(classification['used_for_trading_flag'].sum())},backtest={int(classification['backtest_eligible_flag'].sum())}", "0"),
        ]
    )


def no_blank(frame: pd.DataFrame, column: str) -> bool:
    return bool(frame[column].fillna("").astype(str).str.len().min() > 0)


def build_gpt_review_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_scope": "overall_brain_strategy_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "Institutional GPT review with five roles approved Task735 as an upstream generic 8-K classifier repair, not a PnL or allocation task. It said item 1.01 and material definitive agreement are classifier inputs only, not operating evidence.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
            {
                "review_scope": "circuit_detail_review",
                "status": "EXISTING_TAB_CAPTURED",
                "summary": "GPT detail review required agreement_family_state, operating_transmission_state, permission_state, traceable rule_id, and guardrails that prevent agreement/purchase-agreement wording, governance, compensation, severance, financing, or M&A boilerplate from becoming operating-supported without explicit transmission evidence.",
                "applied_to_code_flag": 1,
                "gpt_is_source_of_truth_flag": 0,
            },
        ]
    )


def build_decision(classification: pd.DataFrame, prior_reclass: pd.DataFrame, guardrail: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "verdict": "GENERIC_8K_CLASSIFIER_REPAIRED_REVIEW_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "generic_8k_count": len(classification),
                "agreement_family_count": classification["agreement_family_state"].nunique(),
                "operating_candidate_count": int(classification["operating_candidate_flag"].sum()),
                "operating_supported_count": int(classification["operating_supported_flag"].sum()),
                "task734_prior_count": len(prior_reclass),
                "task734_prior_supported_count": int(prior_reclass["operating_supported_flag"].fillna(0).sum()),
                "guardrail_pass": int(guardrail["pass_flag"].min()),
                "backtest_permission": "FAIL",
                "next_action": "Rebuild Task732/733 with repaired generic 8-K states, then inspect remaining operating candidates for denominator, expectations, and price absorption before any allocation or PnL test.",
            }
        ]
    )


def build_pass_fail(
    classification: pd.DataFrame,
    distribution: pd.DataFrame,
    prior_reclass: pd.DataFrame,
    guardrail: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("classification_created", len(classification) == 95, f"rows={len(classification)}", "95"),
            gate("distribution_created", len(distribution) > 0, f"rows={len(distribution)}", ">0"),
            gate("prior_reclass_created", len(prior_reclass) == 9, f"rows={len(prior_reclass)}", "9"),
            gate("guardrail_all_pass", int(guardrail["pass_flag"].min()) == 1, f"min={int(guardrail['pass_flag'].min())}", "1"),
            gate("backtest_permission", False, "FAIL", "classifier repair only"),
        ]
    )


def write_outputs(
    out_dir: Path,
    outputs: dict[str, pd.DataFrame],
    classification: pd.DataFrame,
    prior_reclass: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in outputs.items():
        frame.to_csv(out_dir / filename, index=False)
    write_jsonl(out_dir / "task735_generic_8k_classification.jsonl", classification)
    write_jsonl(out_dir / "task735_task734_prior_candidate_reclassification.jsonl", prior_reclass)
    (out_dir / "task_735_generic_8k_classifier_repair.md").write_text(render_report(outputs, decision, pass_fail), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in frame.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def render_report(outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task735 Generic 8-K Classifier Repair",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['verdict']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Backtest permission: `FAIL`",
        "- Status phrase: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Generic 8-K rows: {int(d['generic_8k_count'])}",
        f"- Agreement families: {int(d['agreement_family_count'])}",
        f"- Operating candidates: {int(d['operating_candidate_count'])}",
        f"- Operating supported: {int(d['operating_supported_count'])}",
        f"- Task734 prior candidates checked: {int(d['task734_prior_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "Task735 repairs the upstream generic 8-K classifier. Agreement, purchase agreement, material definitive agreement, and item 1.01 are no longer sufficient for operating support. The source remains alive, but operating permission requires agreement-family classification and operating transmission evidence.",
        "",
        "### Agreement Family Distribution",
        "",
        frame_to_markdown(outputs["task735_agreement_family_distribution.csv"]),
        "",
        "### Task734 Prior Candidate Reclassification",
        "",
        frame_to_markdown(outputs["task735_task734_prior_candidate_reclassification.csv"]),
        "",
        "### Guardrail",
        "",
        frame_to_markdown(outputs["task735_guardrail.csv"]),
        "",
        "### GPT Review",
        "",
        frame_to_markdown(outputs["task735_gpt_review_summary.csv"]),
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- Conclusion: generic 8-K agreement wording is now split before any operating claim.",
        "- Compensation, governance, severance, financing, and investment agreement sources stay alive but do not create operating candidates.",
        "- M&A stays as strategic review unless operating transmission is visible.",
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
    lines.append("- `task735_generic_8k_classification.jsonl`")
    lines.append("- `task735_task734_prior_candidate_reclassification.jsonl`")
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


def source_text(row: pd.Series) -> str:
    raw_path = clean_missing(row.get("raw_text_path"))
    if raw_path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            return normalize(path.read_text(encoding="utf-8", errors="ignore")[:50000])
    return normalize(clean_missing(row.get("content_interpretation_evidence_span")))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", html.unescape(text))).strip()


def text_window(text: str, limit: int = 1000) -> str:
    if not text:
        return ""
    match = re.search(
        r"material definitive agreement|purchase agreement|securities purchase|investment agreement|director|severance|restricted stock|customer|backlog|guidance|acquire|merger",
        text,
        re.IGNORECASE,
    )
    start = max(0, (match.start() if match else 0) - 250)
    return text[start : start + limit]


def clean_missing(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "nat"} else text


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
    artifacts = build_task735(out_dir=args.out_dir)
    decision = artifacts["decision"].iloc[0]
    print(
        f"[{TASK_ID}] verdict={decision['verdict']} generic_8k={decision['generic_8k_count']} "
        f"operating_candidates={decision['operating_candidate_count']} supported={decision['operating_supported_count']} "
        f"backtest_permission={decision['backtest_permission']}"
    )


if __name__ == "__main__":
    main()
