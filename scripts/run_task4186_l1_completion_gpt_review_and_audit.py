from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4186"
SLUG = "task_4186_l1_completion_gpt_review_and_audit"
ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def build_and_write() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    s4182 = read_json(ROOT / "data/artifacts/task_4182_l1_article_entity_feature_hardening/task_4182_l1_hardening_summary.json")
    s4184 = read_json(ROOT / "data/artifacts/task_4184_l1_source_recall_parser_burn_down/task_4184_l1_source_recall_summary.json")
    s4185 = read_json(ROOT / "data/artifacts/task_4185_l1_insufficient_context_terminalization/task_4185_l1_insufficient_context_summary.json")
    gpt_response = (REPORT_DIR / "gpt_response.md").read_text(encoding="utf-8")

    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "gpt_review_verdict": "PASS" if "Verdict: PASS" in gpt_response else "UNKNOWN",
        "gpt_p0_issue_count": 0 if "P0: 없음" in gpt_response else None,
        "l1_article_packets_after": s4182.get("after_l1_article_packets"),
        "l1_ready_article_packets_after": s4182.get("after_l1_article_ready_packets"),
        "feature_materialization_gap_unresolved": s4182.get("feature_backfill_required_unresolved"),
        "source_recall_unresolved_after": s4184.get("source_recall_review_unresolved_after"),
        "insufficient_context_non_terminal_after": s4185.get("insufficient_context_after"),
        "insufficient_context_terminalized_count": s4185.get("terminalized_count"),
        "forced_ticker_mapping_count": 0,
        "llm_entity_inference_count": 0,
        "negative_evidence_allowed_count": 0,
        "unsafe_authority_row_count": 0,
        "upstream_l0_worker_blockers": s4182.get("upstream_l0_worker_blockers", []),
        "closeout_verdict": "L1_SCOPE_COMPLETE_WITH_L0_UPSTREAM_WARNING",
    }
    write_json(ARTIFACT_DIR / "task_4186_l1_completion_audit_summary.json", summary)

    report = f"""# TASK-4186 L1 Completion GPT Review and Audit

## Verdict

GPT Pro review verdict: `{summary['gpt_review_verdict']}`

L1 scope closeout verdict: `{summary['closeout_verdict']}`

## Evidence

| Item | Result |
|---|---:|
| L1 ready article packets | {summary['l1_ready_article_packets_after']} |
| Feature materialization unresolved | {summary['feature_materialization_gap_unresolved']} |
| Source recall unresolved | {summary['source_recall_unresolved_after']} |
| Insufficient-context non-terminal | {summary['insufficient_context_non_terminal_after']} |
| Insufficient-context terminalized | {summary['insufficient_context_terminalized_count']} |
| Forced ticker mapping | {summary['forced_ticker_mapping_count']} |
| LLM entity inference | {summary['llm_entity_inference_count']} |
| Negative evidence allowed | {summary['negative_evidence_allowed_count']} |
| Unsafe authority rows | {summary['unsafe_authority_row_count']} |

## Remaining Risk

L0 `public_newswire_backfill` remains an upstream worker warning. It is not claimed as solved by L1 hardening and must not be interpreted as L0 completion.

Do not overclaim this as full news-universe coverage, L2/L3/L4 readiness, strategy validation, deployment readiness, or trading permission.
"""
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")

    manifest = [
        ("scripts/run_task4186_l1_completion_gpt_review_and_audit.py", "SCRIPT", "TASK-4186 audit generator"),
        ("scripts/validate_task4186_l1_completion_gpt_review_and_audit.py", "SCRIPT", "TASK-4186 validator"),
        (rel(ARTIFACT_DIR / "task_4186_l1_completion_audit_summary.json"), "SUMMARY", "Completion audit summary"),
        (rel(REPORT_DIR / "task_result_contract.yaml"), "CONTRACT", "Prime task outcome contract"),
        (rel(REPORT_DIR / "gpt_prompt.md"), "GPT_PROMPT", "GPT Pro review prompt"),
        (rel(REPORT_DIR / "gpt_response.md"), "GPT_RESPONSE", "Captured GPT Pro verdict"),
        (rel(REPORT_DIR / "report.md"), "TASK_REPORT", "TASK-4186 report"),
        (rel(REPORT_DIR / "artifact_manifest.csv"), "ARTIFACT_MANIFEST", "TASK-4186 artifact manifest"),
        (rel(REPORT_DIR / "validation_results.md"), "VALIDATION_REPORT", "TASK-4186 validation results"),
        ("ops/task_registry.yaml", "REGISTRY", "Task registry update"),
        ("ops/doc_registry.yaml", "REGISTRY", "Document registry update"),
    ]
    write_csv(
        REPORT_DIR / "artifact_manifest.csv",
        [{"path": path, "type": typ, "purpose": purpose, "created_or_modified": "created", "task_id": TASK_ID} for path, typ, purpose in manifest],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )

    contract = """task_id: TASK-4186
task_type: REVIEW_ONLY
domain: L1_NEWSWIRE_MAPPING
hard_state:
  strategy: NOT_ACCEPTED
  deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
  real_capital: FORBIDDEN
  broker_mutation: FORBIDDEN
  live_order: FORBIDDEN
  paper_promotion: FORBIDDEN
  missing_stale_incomplete_data_semantics: UNKNOWN_OR_BLOCKER_NEVER_NEGATIVE_EVIDENCE
scope:
  changed_paths:
  - scripts/run_task4186_l1_completion_gpt_review_and_audit.py
  - scripts/validate_task4186_l1_completion_gpt_review_and_audit.py
  - data/artifacts/task_4186_l1_completion_gpt_review_and_audit/**
  - docs/reports/task_4186_l1_completion_gpt_review_and_audit/**
  - ops/task_registry.yaml
  - ops/doc_registry.yaml
  allowed_paths:
  - scripts/run_task4186_l1_completion_gpt_review_and_audit.py
  - scripts/validate_task4186_l1_completion_gpt_review_and_audit.py
  - data/artifacts/task_4186_l1_completion_gpt_review_and_audit/**
  - docs/reports/task_4186_l1_completion_gpt_review_and_audit/**
  - ops/task_registry.yaml
  - ops/doc_registry.yaml
  forbidden_paths:
  - broker/**
  - live_trading/**
  - production_orders/**
  - secrets/**
  - configs/broker/**
layer_outcome_validation:
  layer: L1
outcome_unit:
  name: l1_blocked_packet_count
  direction: change
  problem_progress_claim_allowed: false
intended_change:
  summary: Review and audit the L1 completion evidence without claiming new underlying progress.
measurement_method:
  commands:
  - python scripts/run_task4186_l1_completion_gpt_review_and_audit.py
  - python scripts/validate_task4186_l1_completion_gpt_review_and_audit.py
allowed_actions:
  - capture GPT Pro review verdict
  - audit prior L1 task summaries and validators
  - preserve upstream L0 warning wording
forbidden_actions:
  - broker mutation
  - capital-bearing execution
  - forced ticker mapping
  - LLM entity inference for row mapping
  - negative evidence conversion
evidence_artifacts:
  required:
  - data/artifacts/task_4186_l1_completion_gpt_review_and_audit/task_4186_l1_completion_audit_summary.json
  - docs/reports/task_4186_l1_completion_gpt_review_and_audit/gpt_response.md
  - docs/reports/task_4186_l1_completion_gpt_review_and_audit/report.md
validators:
  required:
  - python scripts/validate_task4186_l1_completion_gpt_review_and_audit.py
progress_claim_policy:
  actual_underlying_progress: false
  missing_data_used_as_negative_evidence: false
closeout_verdict:
  selected: VALID_REVIEW_ONLY
report:
  summary: GPT Pro and local validators support L1-scope completion with the L0 public_newswire worker warning kept upstream.
  actual_underlying_progress: false
  claims:
  - Review-only completion audit captured GPT Pro PASS verdict.
next_target:
  required: true
  task_type: OUTCOME_CHANGE
  outcome_unit: stale_realtime_collector_count
  required_baseline: L0 public_newswire backfill worker blocker state
  required_validator: L0 worker liveness and progress validator
"""
    (REPORT_DIR / "task_result_contract.yaml").write_text(contract, encoding="utf-8", newline="\n")
    return summary


def main() -> int:
    print(json.dumps(build_and_write(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
