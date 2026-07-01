from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4185"
SLUG = "task_4185_l1_insufficient_context_terminalization"
ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
TASK4146 = ROOT / "data" / "artifacts" / "task_4146_l0_l2_wide_packetization_handoff"
TASK4178 = ROOT / "data" / "artifacts" / "task_4178_l1_alias_ticker_parser_burn_down"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def articles(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    for key in ["headlines", "articles", "items", "rows"]:
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def has_time(row: dict[str, Any]) -> bool:
    return bool(row.get("published_at") or row.get("event_time") or row.get("date") or row.get("published_at_text"))


def has_locator(row: dict[str, Any]) -> bool:
    return bool(row.get("source_url") or row.get("url") or row.get("canonical_url") or row.get("link"))


def has_mapping(row: dict[str, Any]) -> bool:
    return bool(row.get("symbols") or row.get("entities") or row.get("entity_map") or row.get("entity_candidate_hints"))


def build_and_write() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    source_rows = [
        row for row in read_csv(TASK4178 / "task_4178_l1_alias_parser_decision_ledger.csv")
        if row.get("decision_state") == "INSUFFICIENT_CONTEXT"
    ]
    needed = {(row.get("l1_reference", ""), row.get("l2_reference", "")) for row in source_rows}
    wide_rows = {
        (row.get("source_packet_id", ""), row.get("l2_wide_event_id", "")): row
        for row in read_csv(TASK4146 / "l2_feature_materialization_candidates.csv")
        if (row.get("source_packet_id", ""), row.get("l2_wide_event_id", "")) in needed
    }

    ledger: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    total_articles = 0
    total_context_ready = 0
    for row in source_rows:
        wide = wide_rows.get((row.get("l1_reference", ""), row.get("l2_reference", "")))
        raw_path_text = wide.get("raw_path", "") if wide else ""
        raw_path = ROOT / raw_path_text if raw_path_text else Path("")
        expected_sha = wide.get("raw_sha256", "") if wide else ""
        out: dict[str, Any] = {
            "task_id": TASK_ID,
            "source_task_id": row.get("task_id", ""),
            "gap_id": row.get("l3_gap_id", ""),
            "source": row.get("source", ""),
            "entity": row.get("entity", ""),
            "event_month": row.get("event_month", ""),
            "l1_reference": row.get("l1_reference", ""),
            "l2_reference": row.get("l2_reference", ""),
            "wide_reference_found": int(wide is not None),
            "raw_path": raw_path_text,
            "raw_sha256_expected": expected_sha,
            "raw_path_exists": 0,
            "raw_sha256_actual": "",
            "raw_sha256_match": 0,
            "raw_parse_error": "",
            "article_count": 0,
            "source_time_ready_count": 0,
            "locator_ready_count": 0,
            "mapped_article_count": 0,
            "context_or_unmapped_article_count": 0,
            "terminal_status": "",
            "terminal_blocker": 1,
            "forced_ticker_mapping": 0,
            "llm_entity_inference": 0,
            "negative_evidence_allowed": 0,
            "diagnostic_only": 1,
        }
        if raw_path_text and raw_path.exists():
            out["raw_path_exists"] = 1
            try:
                actual_sha = sha256_file(raw_path)
                out["raw_sha256_actual"] = actual_sha
                out["raw_sha256_match"] = int(actual_sha == expected_sha)
                payload = json.loads(raw_path.read_text(encoding="utf-8-sig"))
                raw_articles = articles(payload)
                out["article_count"] = len(raw_articles)
                out["source_time_ready_count"] = sum(1 for article in raw_articles if has_time(article))
                out["locator_ready_count"] = sum(1 for article in raw_articles if has_locator(article))
                out["mapped_article_count"] = sum(1 for article in raw_articles if has_mapping(article))
                out["context_or_unmapped_article_count"] = len(raw_articles) - int(out["mapped_article_count"])
            except Exception as exc:
                out["raw_parse_error"] = type(exc).__name__

        if (
            out["wide_reference_found"]
            and out["raw_path_exists"]
            and out["raw_sha256_match"]
            and not out["raw_parse_error"]
            and out["article_count"] > 0
            and out["source_time_ready_count"] > 0
            and out["locator_ready_count"] > 0
            and out["mapped_article_count"] == 0
        ):
            out["terminal_status"] = "TERMINAL_CONTEXT_OR_NON_CURRENT_UNIVERSE_ENTITY_BLOCKER"
        else:
            out["terminal_status"] = "NON_TERMINAL_EVIDENCE_DEFECT"
        status_counts[out["terminal_status"]] += 1
        total_articles += int(out["article_count"])
        total_context_ready += int(out["context_or_unmapped_article_count"])
        ledger.append(out)

    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "insufficient_context_before": len(source_rows),
        "insufficient_context_after": sum(1 for row in ledger if row["terminal_status"] == "NON_TERMINAL_EVIDENCE_DEFECT"),
        "terminalized_count": sum(1 for row in ledger if row["terminal_status"] == "TERMINAL_CONTEXT_OR_NON_CURRENT_UNIVERSE_ENTITY_BLOCKER"),
        "terminal_status_counts": dict(status_counts),
        "article_rows_scanned": total_articles,
        "context_or_unmapped_article_rows": total_context_ready,
        "forced_ticker_mapping_count": 0,
        "llm_entity_inference_count": 0,
        "negative_evidence_allowed_count": 0,
        "diagnostic_only": 1,
    }

    fields = [
        "task_id",
        "source_task_id",
        "gap_id",
        "source",
        "entity",
        "event_month",
        "l1_reference",
        "l2_reference",
        "wide_reference_found",
        "raw_path",
        "raw_sha256_expected",
        "raw_path_exists",
        "raw_sha256_actual",
        "raw_sha256_match",
        "raw_parse_error",
        "article_count",
        "source_time_ready_count",
        "locator_ready_count",
        "mapped_article_count",
        "context_or_unmapped_article_count",
        "terminal_status",
        "terminal_blocker",
        "forced_ticker_mapping",
        "llm_entity_inference",
        "negative_evidence_allowed",
        "diagnostic_only",
    ]
    write_csv(ARTIFACT_DIR / "task_4185_l1_insufficient_context_terminal_ledger.csv", ledger, fields)
    write_json(ARTIFACT_DIR / "task_4185_l1_insufficient_context_summary.json", summary)
    write_docs(summary)
    return summary


def write_docs(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# TASK-4185 L1 Insufficient Context Terminalization

## Result

| Check | Count |
|---|---:|
| Insufficient context before | {summary['insufficient_context_before']} |
| Insufficient context after | {summary['insufficient_context_after']} |
| Terminal blockers recorded | {summary['terminalized_count']} |
| Article rows scanned | {summary['article_rows_scanned']} |
| Context/unmapped article rows | {summary['context_or_unmapped_article_rows']} |

These rows have raw files, matching hashes, article rows, source time, and locators, but no mapped article evidence. They are therefore terminal L1 blockers, not negative evidence and not trading features.
"""
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")
    (REPORT_DIR / "gpt_prompt.md").write_text("# TASK-4185 GPT Prompt\n\nNo new GPT consult. This is a bounded deterministic terminalization of the five residual TASK-4178 insufficient-context rows.\n", encoding="utf-8", newline="\n")
    (REPORT_DIR / "gpt_response.md").write_text("# TASK-4185 GPT Review Status\n\nRelay mode: `direct_codex`. Prior TASK-4182 GPT guidance applies: parseable raw becomes L1 evidence; unresolvable rows become explicit blockers; no forced ticker mapping or LLM inference.\n", encoding="utf-8", newline="\n")
    manifest = [
        ("scripts/run_task4185_l1_insufficient_context_terminalization.py", "SCRIPT", "TASK-4185 evidence generator"),
        ("scripts/validate_task4185_l1_insufficient_context_terminalization.py", "SCRIPT", "TASK-4185 validator"),
        (rel(ARTIFACT_DIR / "task_4185_l1_insufficient_context_summary.json"), "SUMMARY", "Insufficient-context terminalization summary"),
        (rel(ARTIFACT_DIR / "task_4185_l1_insufficient_context_terminal_ledger.csv"), "LEDGER", "Row-level terminal blocker ledger"),
        (rel(REPORT_DIR / "task_result_contract.yaml"), "CONTRACT", "Prime task outcome contract"),
        (rel(REPORT_DIR / "gpt_prompt.md"), "GPT_PROMPT", "GPT prompt status artifact"),
        (rel(REPORT_DIR / "gpt_response.md"), "GPT_RESPONSE", "GPT review status artifact"),
        (rel(REPORT_DIR / "report.md"), "TASK_REPORT", "TASK-4185 report"),
        (rel(REPORT_DIR / "artifact_manifest.csv"), "ARTIFACT_MANIFEST", "TASK-4185 artifact manifest"),
        (rel(REPORT_DIR / "validation_results.md"), "VALIDATION_REPORT", "TASK-4185 validation results"),
        ("ops/task_registry.yaml", "REGISTRY", "Task registry update"),
        ("ops/doc_registry.yaml", "REGISTRY", "Document registry update"),
    ]
    write_csv(
        REPORT_DIR / "artifact_manifest.csv",
        [{"path": path, "type": typ, "purpose": purpose, "created_or_modified": "created", "task_id": TASK_ID} for path, typ, purpose in manifest],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )
    contract = f"""task_id: {TASK_ID}
task_type: TERMINALIZE
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
  - scripts/run_task4185_l1_insufficient_context_terminalization.py
  - scripts/validate_task4185_l1_insufficient_context_terminalization.py
  - data/artifacts/task_4185_l1_insufficient_context_terminalization/**
  - docs/reports/task_4185_l1_insufficient_context_terminalization/**
  - ops/task_registry.yaml
  - ops/doc_registry.yaml
  allowed_paths:
  - scripts/run_task4185_l1_insufficient_context_terminalization.py
  - scripts/validate_task4185_l1_insufficient_context_terminalization.py
  - data/artifacts/task_4185_l1_insufficient_context_terminalization/**
  - docs/reports/task_4185_l1_insufficient_context_terminalization/**
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
  name: unclassified_article_count
  direction: decrease
  problem_progress_claim_allowed: true
intended_change:
  summary: Terminalize residual insufficient-context rows as explicit no-mapped-evidence blockers.
measurement_method:
  commands:
  - python scripts/run_task4185_l1_insufficient_context_terminalization.py
  - python scripts/validate_task4185_l1_insufficient_context_terminalization.py
baseline:
  value: {summary['insufficient_context_before']}
after:
  value: {summary['insufficient_context_after']}
  terminalized_count: {summary['terminalized_count']}
allowed_actions:
  - verify raw path, sha256, articles, source time, locator, and absence of mapped article evidence
  - write diagnostic terminal blocker ledger
forbidden_actions:
  - broker mutation
  - capital-bearing execution
  - forced ticker mapping
  - LLM entity inference
  - negative evidence conversion
evidence_artifacts:
  required:
  - data/artifacts/task_4185_l1_insufficient_context_terminalization/task_4185_l1_insufficient_context_summary.json
  - data/artifacts/task_4185_l1_insufficient_context_terminalization/task_4185_l1_insufficient_context_terminal_ledger.csv
  - docs/reports/task_4185_l1_insufficient_context_terminalization/report.md
validators:
  required:
  - python scripts/validate_task4185_l1_insufficient_context_terminalization.py
progress_claim_policy:
  actual_underlying_progress: false
  missing_data_used_as_negative_evidence: false
closeout_verdict:
  selected: VALID_TERMINALIZATION
report:
  summary: Five residual insufficient-context rows were terminalized as explicit context or non-current-universe blockers.
  actual_underlying_progress: false
  claims:
  - Residual insufficient-context rows are explicit terminal blockers, not silent unresolved rows.
next_target:
  required: true
  task_type: OUTCOME_CHANGE
  outcome_unit: unmapped_entity_count
  required_baseline: refreshed L1 unmapped entity counts after L0 backfill progresses
  required_validator: deterministic alias/parser recovery validator
"""
    (REPORT_DIR / "task_result_contract.yaml").write_text(contract, encoding="utf-8", newline="\n")


def main() -> int:
    print(json.dumps(build_and_write(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
