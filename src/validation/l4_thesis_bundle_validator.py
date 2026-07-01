from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.brain.l4_thesis_bundle.schema import (
    ALLOWED_BLOCKER_TYPES,
    ALLOWED_BUNDLE_STATUS,
    ALLOWED_QUALITY_STATUS,
    ALLOWED_THESIS_TYPES,
    BLOCKER_REQUIRED_FIELDS,
    BUNDLE_REQUIRED_FIELDS,
    DEPLOYMENT_STATUS,
    EVIDENCE_REQUIRED_FIELDS,
    FORBIDDEN_AUTHORITY_FIELDS,
    REAL_CAPITAL,
    STRATEGY_STATUS,
)


REQUIRED_ARTIFACTS = (
    "l4_thesis_bundles.jsonl",
    "l4_thesis_evidence_links.csv",
    "l4_thesis_blockers.csv",
    "l4_run_manifest.json",
)

AUTHORITY_GRANTING_VALUES = {
    "PASS",
    "ACCEPTED",
    "READY_FOR_TRADING",
    "PAPER_READY",
    "LIVE_READY",
    "STRATEGY_ACCEPTED",
    "DEPLOYMENT_READY",
    "BUY",
    "SELL",
    "HOLD",
    "ORDER_INTENT",
}

FINAL_READY_STATUS_VALUES = {"COMPLETE", "PASSED", "ACCEPTED", "READY", "ACTIONABLE", "ELIGIBLE", "FINAL", "FULL"}
CONTRADICTION_ALLOWED_BUNDLE_STATUS = {"DRAFT_MIXED", "DRAFT_BLOCKED"}
CONTRADICTION_ALLOWED_QUALITY_STATUS = {"MIXED", "BLOCKED"}
CONTRADICTION_ALLOWED_COVERAGE_STATUS = {"INCOMPLETE", "BLOCKED"}


def validate_l4_package(artifact_dir: str | Path = "data/diagnostics/l4") -> dict[str, Any]:
    out = Path(artifact_dir)
    passes: list[str] = []
    failures: list[str] = []

    for artifact in REQUIRED_ARTIFACTS:
        path = out / artifact
        if path.exists():
            passes.append(f"exists: {path}")
        else:
            failures.append(f"missing: {path}")
    if failures:
        return result("FAIL", passes, failures)

    bundles = read_jsonl(out / "l4_thesis_bundles.jsonl")
    evidence = read_csv(out / "l4_thesis_evidence_links.csv")
    blockers = read_csv(out / "l4_thesis_blockers.csv")
    manifest = json.loads((out / "l4_run_manifest.json").read_text(encoding="utf-8"))

    if bundles:
        passes.append(f"bundle rows: {len(bundles)}")
    else:
        failures.append("no thesis bundles created")
    if evidence:
        passes.append(f"evidence link rows: {len(evidence)}")
    else:
        failures.append("no evidence links created")
    if blockers:
        passes.append(f"blocker rows: {len(blockers)}")
    else:
        failures.append("no blockers created")

    validate_bundle_schema(bundles, failures, passes)
    validate_evidence_schema(evidence, failures, passes)
    validate_blocker_schema(blockers, failures, passes)
    validate_manifest(manifest, bundles, evidence, blockers, failures, passes)
    validate_semantics(bundles, evidence, blockers, manifest, failures, passes)

    status = "PASS" if not failures else "FAIL"
    return result(status, passes, failures)


def validate_bundle_schema(bundles: list[dict[str, Any]], failures: list[str], passes: list[str]) -> None:
    for idx, row in enumerate(bundles):
        missing = [field for field in BUNDLE_REQUIRED_FIELDS if field not in row]
        if missing:
            failures.append(f"bundle[{idx}] missing fields: {missing}")
            continue
        if row.get("diagnostic_only") is not True:
            failures.append(f"bundle[{idx}] diagnostic_only is not true")
        if row.get("strategy_status") != STRATEGY_STATUS:
            failures.append(f"bundle[{idx}] strategy_status invalid: {row.get('strategy_status')}")
        if row.get("deployment_status") != DEPLOYMENT_STATUS:
            failures.append(f"bundle[{idx}] deployment_status invalid: {row.get('deployment_status')}")
        if row.get("real_capital") != REAL_CAPITAL:
            failures.append(f"bundle[{idx}] real_capital invalid: {row.get('real_capital')}")
        if row.get("no_broker_mutation") is not True or row.get("no_live_order") is not True or row.get("no_paper_promotion") is not True:
            failures.append(f"bundle[{idx}] hard no-order/no-broker flags invalid")
        if row.get("same_event_assertion") is not False:
            failures.append(f"bundle[{idx}] same_event_assertion is not false")
        if row.get("bundle_status") not in ALLOWED_BUNDLE_STATUS:
            failures.append(f"bundle[{idx}] invalid bundle_status: {row.get('bundle_status')}")
        if row.get("institutional_quality_status") not in ALLOWED_QUALITY_STATUS:
            failures.append(f"bundle[{idx}] invalid institutional_quality_status: {row.get('institutional_quality_status')}")
        if row.get("thesis_type") not in ALLOWED_THESIS_TYPES:
            failures.append(f"bundle[{idx}] invalid thesis_type: {row.get('thesis_type')}")
        if row.get("contradiction_status") == "NO_CONTRADICTION":
            failures.append(f"bundle[{idx}] contradiction_status falsely clears contradiction")
        if forbidden_fields(row):
            failures.append(f"bundle[{idx}] has forbidden authority fields: {forbidden_fields(row)}")
        for score_field in (
            "thesis_specificity_score",
            "evidence_linkage_score",
            "source_traceability_score",
            "contradiction_handling_score",
            "institutional_quality_score",
        ):
            value = row.get(score_field)
            if value is not None and not (0 <= float(value) <= 100):
                failures.append(f"bundle[{idx}] {score_field} out of range: {value}")
    if not any("bundle[" in failure for failure in failures):
        passes.append("bundle schema and hard boundaries valid")


def validate_evidence_schema(evidence: list[dict[str, str]], failures: list[str], passes: list[str]) -> None:
    for idx, row in enumerate(evidence):
        missing = [field for field in EVIDENCE_REQUIRED_FIELDS if field not in row]
        if missing:
            failures.append(f"evidence[{idx}] missing fields: {missing}")
            continue
        if to_bool(row.get("negative_evidence_allowed")):
            failures.append(f"evidence[{idx}] negative_evidence_allowed is true")
        if row.get("evidence_role") in {"supporting", "context"}:
            has_lineage = bool(row.get("l1_packet_id")) and bool(row.get("l2_feature_id"))
            if not has_lineage and row.get("evidence_quality_flag") != "BLOCKED":
                failures.append(f"evidence[{idx}] raw-only support/context evidence not blocked")
        if forbidden_fields(row):
            failures.append(f"evidence[{idx}] has forbidden authority fields: {forbidden_fields(row)}")
    if not any("evidence[" in failure for failure in failures):
        passes.append("evidence schema and negative-evidence rules valid")


def validate_blocker_schema(blockers: list[dict[str, str]], failures: list[str], passes: list[str]) -> None:
    for idx, row in enumerate(blockers):
        missing = [field for field in BLOCKER_REQUIRED_FIELDS if field not in row]
        if missing:
            failures.append(f"blocker[{idx}] missing fields: {missing}")
            continue
        if row.get("blocker_type") not in ALLOWED_BLOCKER_TYPES:
            failures.append(f"blocker[{idx}] invalid blocker_type: {row.get('blocker_type')}")
        if to_bool(row.get("negative_evidence_allowed")):
            failures.append(f"blocker[{idx}] negative_evidence_allowed is true")
        if forbidden_fields(row):
            failures.append(f"blocker[{idx}] has forbidden authority fields: {forbidden_fields(row)}")
    blocker_types = {row.get("blocker_type") for row in blockers}
    if "CONTRADICTION_NOT_SCANNED" not in blocker_types:
        failures.append("CONTRADICTION_NOT_SCANNED blocker missing")
    if not any("blocker[" in failure for failure in failures):
        passes.append("blocker schema and non-negative rules valid")


def validate_manifest(
    manifest: dict[str, Any],
    bundles: list[dict[str, Any]],
    evidence: list[dict[str, str]],
    blockers: list[dict[str, str]],
    failures: list[str],
    passes: list[str],
) -> None:
    if manifest.get("diagnostic_only") is not True:
        failures.append("manifest diagnostic_only is not true")
    boundaries = manifest.get("hard_boundaries", {})
    expected = {
        "strategy_status": STRATEGY_STATUS,
        "deployment_status": DEPLOYMENT_STATUS,
        "real_capital": REAL_CAPITAL,
        "no_broker_mutation": True,
        "no_live_order": True,
        "no_paper_promotion": True,
    }
    for key, value in expected.items():
        if boundaries.get(key) != value:
            failures.append(f"manifest hard boundary invalid: {key}={boundaries.get(key)!r}")
    if manifest.get("bundle_count") != len(bundles):
        failures.append(f"manifest bundle_count mismatch: {manifest.get('bundle_count')} vs {len(bundles)}")
    if manifest.get("evidence_link_count") != len(evidence):
        failures.append(f"manifest evidence_link_count mismatch: {manifest.get('evidence_link_count')} vs {len(evidence)}")
    if manifest.get("blocker_count") != len(blockers):
        failures.append(f"manifest blocker_count mismatch: {manifest.get('blocker_count')} vs {len(blockers)}")
    validate_source_inputs(manifest, failures, passes)
    if forbidden_fields(manifest):
        failures.append(f"manifest has forbidden authority fields: {forbidden_fields(manifest)}")
    if not any("manifest" in failure for failure in failures):
        passes.append("manifest counts and hard boundaries valid")


def validate_source_inputs(manifest: dict[str, Any], failures: list[str], passes: list[str]) -> None:
    source_inputs = manifest.get("source_inputs", [])
    if not source_inputs:
        failures.append("manifest source_inputs missing")
        return
    seen_roles: set[str] = set()
    for idx, row in enumerate(source_inputs):
        role = row.get("role")
        path_value = row.get("path")
        seen_roles.add(str(role))
        if not path_value or not Path(path_value).exists():
            failures.append(f"manifest source_inputs[{idx}] path missing or does not exist: {path_value}")
        if not row.get("sha256"):
            failures.append(f"manifest source_inputs[{idx}] sha256 missing")
        if str(path_value).lower().endswith((".csv", ".jsonl")):
            row_count = row.get("row_count")
            if row_count is None or int(row_count) < 0:
                failures.append(f"manifest source_inputs[{idx}] row_count invalid: {row_count}")
        if not row.get("mtime_utc"):
            failures.append(f"manifest source_inputs[{idx}] mtime_utc missing")
    input_artifact_roles = {row.get("role") for row in manifest.get("input_artifacts", [])}
    missing_roles = input_artifact_roles - seen_roles
    if missing_roles:
        failures.append(f"manifest source_inputs missing roles: {sorted(missing_roles)}")
    if not any("source_inputs" in failure for failure in failures):
        passes.append("manifest source input fingerprints valid")


def validate_semantics(
    bundles: list[dict[str, Any]],
    evidence: list[dict[str, str]],
    blockers: list[dict[str, str]],
    manifest: dict[str, Any],
    failures: list[str],
    passes: list[str],
) -> None:
    evidence_by_bundle: dict[str, list[dict[str, str]]] = defaultdict(list)
    blocker_by_bundle: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in evidence:
        evidence_by_bundle[row.get("bundle_id", "")].append(row)
    for row in blockers:
        blocker_by_bundle[row.get("bundle_id", "")].append(row)

    for bundle in bundles:
        bundle_id = bundle.get("bundle_id", "")
        rows = evidence_by_bundle.get(bundle_id, [])
        actual = Counter(row.get("evidence_role") for row in rows)
        if int(bundle.get("supporting_evidence_count", 0)) != actual.get("supporting", 0):
            failures.append(f"bundle {bundle_id} supporting evidence count mismatch")
        if int(bundle.get("context_evidence_count", 0)) != actual.get("context", 0):
            failures.append(f"bundle {bundle_id} context evidence count mismatch")
        coverage_count = actual.get("coverage_gap", 0) + sum(1 for row in blocker_by_bundle.get(bundle_id, []) if row.get("blocker_type") == "L3_COVERAGE_GAP")
        if int(bundle.get("coverage_gap_count", 0)) > 0 and coverage_count == 0:
            failures.append(f"bundle {bundle_id} coverage gap count has no evidence/blocker rows")
        if bundle.get("contradiction_status") == "NO_CONTRADICTION":
            failures.append(f"bundle {bundle_id} contradiction falsely clear")
        if "CONTRADICTION_NOT_SCANNED" not in {row.get("blocker_type") for row in blocker_by_bundle.get(bundle_id, [])}:
            failures.append(f"bundle {bundle_id} missing CONTRADICTION_NOT_SCANNED blocker")
        if "CONTRADICTION_NOT_SCANNED" in {row.get("blocker_type") for row in blocker_by_bundle.get(bundle_id, [])}:
            validate_contradiction_not_scanned_state(bundle, bundle_id, failures)
        if bundle.get("event_identity_status") == "PROTO_BUCKET" and bundle.get("same_event_assertion") is not False:
            failures.append(f"bundle {bundle_id} proto event has same_event_assertion true")
        if l0_incomplete(manifest) and str(bundle.get("coverage_status", "")).upper() in {"COMPLETE", "FULL", "READY", "ACCEPTED"}:
            failures.append(f"bundle {bundle_id} has complete/final coverage_status while L0 is incomplete")
        if string_contains_authority_grant(bundle):
            failures.append(f"bundle {bundle_id} contains authority-granting value")

    if not any("bundle " in failure for failure in failures):
        passes.append("bundle/evidence/blocker semantic consistency valid")


def validate_contradiction_not_scanned_state(bundle: dict[str, Any], bundle_id: str, failures: list[str]) -> None:
    if bundle.get("bundle_status") not in CONTRADICTION_ALLOWED_BUNDLE_STATUS:
        failures.append(f"bundle {bundle_id} invalid bundle_status with CONTRADICTION_NOT_SCANNED: {bundle.get('bundle_status')}")
    if bundle.get("institutional_quality_status") not in CONTRADICTION_ALLOWED_QUALITY_STATUS:
        failures.append(f"bundle {bundle_id} invalid institutional_quality_status with CONTRADICTION_NOT_SCANNED: {bundle.get('institutional_quality_status')}")
    if bundle.get("coverage_status") not in CONTRADICTION_ALLOWED_COVERAGE_STATUS:
        failures.append(f"bundle {bundle_id} invalid coverage_status with CONTRADICTION_NOT_SCANNED: {bundle.get('coverage_status')}")
    for key, value in bundle.items():
        if key.endswith("_status") and str(value).upper() in FINAL_READY_STATUS_VALUES:
            failures.append(f"bundle {bundle_id} has final/ready status value with CONTRADICTION_NOT_SCANNED: {key}={value}")


def l0_incomplete(manifest: dict[str, Any]) -> bool:
    coverage = manifest.get("l0_coverage_state", {})
    if not coverage:
        return True
    for row in coverage.values():
        if row.get("incomplete") is not False:
            return True
    return False


def forbidden_fields(obj: dict[str, Any]) -> list[str]:
    return sorted(set(obj) & FORBIDDEN_AUTHORITY_FIELDS)


def string_contains_authority_grant(obj: dict[str, Any]) -> bool:
    for value in obj.values():
        if isinstance(value, str) and value.upper() in AUTHORITY_GRANTING_VALUES:
            return True
    return False


def to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def result(status: str, passes: list[str], failures: list[str]) -> dict[str, Any]:
    return {"task_id": "TASK-4156", "status": status, "passes": passes, "failures": failures}


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))
