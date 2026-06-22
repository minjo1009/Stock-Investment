from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task635"
REPORT_DIR = Path("docs/reports/task_635_content_interpretation_readiness_audit")
TASK623_SCORES = Path("docs/reports/task_623_big_event_interpretation_scoring_sidecar/event_interpretation_scores.csv")
TASK625_CERT = Path("docs/reports/task_625_big_event_perfection_criteria_source_certification/task_625_source_certification_matrix.csv")
TASK634_DECISION = Path("docs/reports/task_634_information_predictive_value_audit/task_634_decision.csv")

REQUIRED_CONTENT_FIELDS = [
    "content_prediction_direction",
    "content_prediction_magnitude_score",
    "content_stock_specific_causal_link",
    "content_named_customer_or_counterparty",
    "content_revenue_or_backlog_signal",
    "content_guidance_or_margin_signal",
    "content_supply_demand_signal",
    "content_regulatory_or_policy_transmission",
    "content_priced_in_risk_score",
    "content_interpretation_evidence_span",
    "content_prediction_certified_flag",
]


def build_task635_content_interpretation_readiness_audit(
    *,
    scores_path: Path = TASK623_SCORES,
    certification_path: Path = TASK625_CERT,
    task634_decision_path: Path = TASK634_DECISION,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    scores = pd.read_csv(scores_path)
    certification = pd.read_csv(certification_path)
    task634 = pd.read_csv(task634_decision_path) if task634_decision_path.exists() else pd.DataFrame()
    readiness = build_readiness_audit(scores, certification, task634)
    blocked_fields = build_blocked_field_policy(scores)
    required_schema = build_required_schema()
    pass_fail = build_pass_fail(readiness)
    decision = build_decision(readiness, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    readiness.to_csv(out_dir / "task_635_content_readiness_audit.csv", index=False)
    blocked_fields.to_csv(out_dir / "task_635_presence_field_block_policy.csv", index=False)
    required_schema.to_csv(out_dir / "task_635_required_content_prediction_schema.csv", index=False)
    pass_fail.to_csv(out_dir / "task_635_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_635_decision.csv", index=False)
    (out_dir / "task_635_content_interpretation_readiness_audit.md").write_text(
        render_report(readiness, blocked_fields, required_schema, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_635_content_readiness_audit": readiness,
        "task_635_presence_field_block_policy": blocked_fields,
        "task_635_required_content_prediction_schema": required_schema,
        "task_635_pass_fail_matrix": pass_fail,
        "task_635_decision": decision,
    }


def build_readiness_audit(scores: pd.DataFrame, certification: pd.DataFrame, task634: pd.DataFrame) -> pd.DataFrame:
    missing_content_fields = [field for field in REQUIRED_CONTENT_FIELDS if field not in scores.columns]
    certified_text_count = int(pd.to_numeric(certification.get("source_text_certified_flag", 0), errors="coerce").fillna(0).sum())
    raw_text_path_count = int(certification.get("raw_text_path", pd.Series(dtype=str)).astype(str).str.len().gt(0).sum())
    scoring_has_raw_text_path_flag = int("raw_text_path" in scores.columns)
    scoring_has_source_text_hash_flag = int("source_text_hash" in scores.columns)
    stable_predictive_features = (
        int(task634.iloc[0]["stable_predictive_feature_count"])
        if not task634.empty and "stable_predictive_feature_count" in task634.columns
        else 0
    )
    title_or_presence_score_rows = int(
        scores.get("evidence_quality", pd.Series(dtype=str)).astype(str).isin(
            ["title_only", "generic_filing_or_ownership_only", "generic_filing_only"]
        ).sum()
    )
    support_without_content_cert = int(
        pd.to_numeric(scores.get("support_entry_certified_flag", 0), errors="coerce").fillna(0).astype(int).sum()
    )
    return pd.DataFrame(
        [
            {
                "event_score_rows": int(len(scores)),
                "source_certification_rows": int(len(certification)),
                "source_text_certified_count": certified_text_count,
                "raw_text_path_count": raw_text_path_count,
                "scoring_has_raw_text_path_flag": scoring_has_raw_text_path_flag,
                "scoring_has_source_text_hash_flag": scoring_has_source_text_hash_flag,
                "required_content_field_count": len(REQUIRED_CONTENT_FIELDS),
                "missing_content_field_count": len(missing_content_fields),
                "missing_content_fields": "|".join(missing_content_fields),
                "title_or_presence_score_rows": title_or_presence_score_rows,
                "support_without_content_certified_count": support_without_content_cert,
                "stable_predictive_feature_count": stable_predictive_features,
                "content_prediction_ready_flag": 0,
                "assignment_allowed_flag": 0,
            }
        ]
    )


def build_blocked_field_policy(scores: pd.DataFrame) -> pd.DataFrame:
    blocked = [
        "political_statement_pre7d_flag",
        "geopolitical_event_pre7d_flag",
        "institution_ownership_pre30d_flag",
        "ceo_ir_proxy_pre14d_flag",
        "p0_source_event_density_ge2_flag",
        "temporal_political_fresh_pre72h_flag",
        "temporal_geopolitical_fresh_pre72h_flag",
        "temporal_institution_pre30d_flag",
        "temporal_passive_13g_pre30d_flag",
        "temporal_insider_form4_or_144_pre30d_flag",
        "temporal_ceo_ir_proxy_pre14d_flag",
        "temporal_source_event_density",
        "tq_intelligence_support_score",
        "tq_temporal_intelligence_support_score",
    ]
    return pd.DataFrame(
        [
            {
                "field": field,
                "assignment_use_allowed_flag": 0,
                "reason": "presence or density field is not content prediction",
            }
            for field in blocked
        ]
    )


def build_required_schema() -> pd.DataFrame:
    descriptions = {
        "content_prediction_direction": "expected stock move from source content: bullish bearish neutral mixed",
        "content_prediction_magnitude_score": "expected price impact strength from 0 to 3",
        "content_stock_specific_causal_link": "direct reason this source should affect this exact symbol",
        "content_named_customer_or_counterparty": "named customer supplier regulator counterparty or program when present",
        "content_revenue_or_backlog_signal": "orders revenue backlog demand or contract signal",
        "content_guidance_or_margin_signal": "guidance margin earnings cash burn dilution or liquidity signal",
        "content_supply_demand_signal": "capacity supply constraint demand acceleration inventory pricing signal",
        "content_regulatory_or_policy_transmission": "how macro policy transmits to this company or theme",
        "content_priced_in_risk_score": "risk that the market already priced the information",
        "content_interpretation_evidence_span": "short source-text evidence span used for classification",
        "content_prediction_certified_flag": "1 only when source text and relevance are sufficient for validation",
    }
    return pd.DataFrame(
        [
            {
                "field": field,
                "required_for_assignment_flag": 1,
                "description": descriptions[field],
            }
            for field in REQUIRED_CONTENT_FIELDS
        ]
    )


def build_pass_fail(readiness: pd.DataFrame) -> pd.DataFrame:
    row = readiness.iloc[0]
    return pd.DataFrame(
        [
            {
                "gate": "source_text_exists",
                "pass_flag": int(int(row["source_text_certified_count"]) > 0),
                "observed_value": f"certified_text={int(row['source_text_certified_count'])}",
                "required_value": "certified source text must exist before content interpretation",
            },
            {
                "gate": "scoring_uses_source_text_content",
                "pass_flag": int(int(row["scoring_has_raw_text_path_flag"]) == 1 and int(row["scoring_has_source_text_hash_flag"]) == 1),
                "observed_value": f"raw_text_path_in_scores={int(row['scoring_has_raw_text_path_flag'])}; text_hash_in_scores={int(row['scoring_has_source_text_hash_flag'])}",
                "required_value": "event scoring must carry raw text path and source hash",
            },
            {
                "gate": "content_prediction_schema_complete",
                "pass_flag": int(int(row["missing_content_field_count"]) == 0),
                "observed_value": f"missing_content_fields={int(row['missing_content_field_count'])}",
                "required_value": "all required content prediction fields must exist",
            },
            {
                "gate": "presence_fields_blocked_from_assignment",
                "pass_flag": 1,
                "observed_value": "presence fields explicitly blocked",
                "required_value": "presence and density fields cannot drive assignment",
            },
            {
                "gate": "predictive_validation_ready",
                "pass_flag": int(int(row["stable_predictive_feature_count"]) > 0 and int(row["content_prediction_ready_flag"]) == 1),
                "observed_value": f"stable_predictive_features={int(row['stable_predictive_feature_count'])}; content_ready={int(row['content_prediction_ready_flag'])}",
                "required_value": "content prediction fields must prove validation and recent OOS predictive value",
            },
            {
                "gate": "assignment_allowed",
                "pass_flag": 0,
                "observed_value": "content interpretation not ready",
                "required_value": "assignment allowed only after content prediction schema and predictive validation pass",
            },
        ]
    )


def build_decision(readiness: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    row = readiness.iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "FAIL_CONTENT_INTERPRETATION_NOT_READY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "source_text_certified_count": int(row["source_text_certified_count"]),
                "missing_content_field_count": int(row["missing_content_field_count"]),
                "assignment_allowed_flag": 0,
                "trading_promotion_pass_flag": 0,
                "next_action": "Build content prediction extraction from source text then validate those predictions against validation and recent OOS returns before any information field can affect entries.",
            }
        ]
    )


def render_report(
    readiness: pd.DataFrame,
    blocked_fields: pd.DataFrame,
    required_schema: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    r = readiness.iloc[0]
    lines = [
        "# Task635 Content Interpretation Readiness Audit",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Certified source text rows: {int(d['source_text_certified_count'])}",
        f"- Missing content prediction fields: {int(d['missing_content_field_count'])}",
        "- Assignment from information fields: `FORBIDDEN`",
        "",
        "## Quant Expert Report",
        "",
        "The project has source text, but the current scoring layer does not yet use source text content as a predictive model. It still relies on title, tag, lane, presence, and density style fields. Those fields must not drive entries.",
        "",
        "### Readiness Audit",
        "",
        "| Certified Text | Raw Text In Scores | Text Hash In Scores | Missing Content Fields | Stable Predictive Features |",
        "|---:|---:|---:|---:|---:|",
        f"| {int(r['source_text_certified_count'])} | {int(r['scoring_has_raw_text_path_flag'])} | {int(r['scoring_has_source_text_hash_flag'])} | {int(r['missing_content_field_count'])} | {int(r['stable_predictive_feature_count'])} |",
        "",
        "### Required Content Prediction Schema",
        "",
        "| Field | Required | Description |",
        "|---|---:|---|",
    ]
    for _, row in required_schema.iterrows():
        lines.append(f"| `{row['field']}` | {int(row['required_for_assignment_flag'])} | {row['description']} |")
    lines.extend(
        [
            "",
            "### Blocked Presence Fields",
            "",
            "| Field | Assignment Allowed | Reason |",
            "|---|---:|---|",
        ]
    )
    for _, row in blocked_fields.iterrows():
        lines.append(f"| `{row['field']}` | {int(row['assignment_use_allowed_flag'])} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- The current project has collected source text, but has not converted it into stock-specific predictive meaning.",
            "- Information presence, source count, and source type are blocked from trading use.",
            "- Next work must read source content and produce a tested prediction field before information can affect entries.",
            "",
            "## Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task_635_content_readiness_audit.csv`",
            "- `task_635_presence_field_block_policy.csv`",
            "- `task_635_required_content_prediction_schema.csv`",
            "- `task_635_pass_fail_matrix.csv`",
            "- `task_635_decision.csv`",
            "- `artifact_manifest.csv`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task635_content_interpretation_readiness_audit(out_dir=args.out_dir)
    decision = artifacts["task_635_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"source_text={int(decision['source_text_certified_count'])} "
        f"missing_content_fields={int(decision['missing_content_field_count'])}"
    )


if __name__ == "__main__":
    main()
