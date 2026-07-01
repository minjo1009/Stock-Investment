from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path
from typing import Any

import yaml

from src.validation.prime_layer_outcome_unit_validator import validate_layer_outcome_unit


TASK_TYPES = {
    "OUTCOME_CHANGE",
    "TERMINALIZE",
    "RECLASSIFY",
    "DIAGNOSTIC_ONLY",
    "HARNESS_BOOTSTRAP",
    "EXPLORATORY_RESEARCH",
    "DESIGN_ONLY",
    "REVIEW_ONLY",
}

VERDICTS = {
    "ACTUAL_PROGRESS",
    "ACTUAL_PROGRESS_WITH_RESIDUAL_BLOCKERS",
    "VALID_TERMINALIZATION",
    "VALID_RECLASSIFICATION",
    "VALID_DIAGNOSTIC_ONLY",
    "VALID_DESIGN_ONLY",
    "VALID_REVIEW_ONLY",
    "VALID_HARNESS_BOOTSTRAP",
    "BLOCKED_BY_UPSTREAM",
    "INVALID_CLOSEOUT",
}

VERDICTS_BY_TASK_TYPE = {
    "OUTCOME_CHANGE": {"ACTUAL_PROGRESS", "ACTUAL_PROGRESS_WITH_RESIDUAL_BLOCKERS", "BLOCKED_BY_UPSTREAM"},
    "TERMINALIZE": {"VALID_TERMINALIZATION", "BLOCKED_BY_UPSTREAM"},
    "RECLASSIFY": {"VALID_RECLASSIFICATION", "BLOCKED_BY_UPSTREAM"},
    "DIAGNOSTIC_ONLY": {"VALID_DIAGNOSTIC_ONLY", "BLOCKED_BY_UPSTREAM"},
    "HARNESS_BOOTSTRAP": {"VALID_HARNESS_BOOTSTRAP", "BLOCKED_BY_UPSTREAM"},
    "EXPLORATORY_RESEARCH": {"VALID_DIAGNOSTIC_ONLY", "BLOCKED_BY_UPSTREAM"},
    "DESIGN_ONLY": {"VALID_DESIGN_ONLY", "BLOCKED_BY_UPSTREAM"},
    "REVIEW_ONLY": {"VALID_REVIEW_ONLY", "BLOCKED_BY_UPSTREAM"},
}

REQUIRED_FIELDS = {
    "task_id",
    "task_type",
    "domain",
    "hard_state",
    "scope",
    "outcome_unit",
    "intended_change",
    "measurement_method",
    "allowed_actions",
    "forbidden_actions",
    "evidence_artifacts",
    "validators",
    "progress_claim_policy",
    "closeout_verdict",
    "report",
    "next_target",
}

REQUIRED_HARD_STATE = {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
    "broker_mutation": "FORBIDDEN",
    "live_order": "FORBIDDEN",
    "paper_promotion": "FORBIDDEN",
    "missing_stale_incomplete_data_semantics": "UNKNOWN_OR_BLOCKER_NEVER_NEGATIVE_EVIDENCE",
}

PROGRESS_FORBIDDEN_TASK_TYPES = {
    "DIAGNOSTIC_ONLY",
    "HARNESS_BOOTSTRAP",
    "EXPLORATORY_RESEARCH",
    "DESIGN_ONLY",
    "REVIEW_ONLY",
}

AUTHORITY_GRANTING_TERMS = {
    "STRATEGY_ACCEPTED",
    "DEPLOYMENT_READY",
    "READY_FOR_TRADING",
    "LIVE_READY",
    "PAPER_READY",
    "REAL_CAPITAL",
    "BROKER_MUTATION",
    "LIVE_ORDER",
    "PAPER_PROMOTION",
    "ORDER_INTENT",
    "BUY",
    "SELL",
    "PORTFOLIO_SIZING",
}

UNDERLYING_PROGRESS_TERMS = (
    "l0",
    "l1",
    "l2",
    "l3",
    "l4",
    "blocker",
    "failed",
    "unmapped",
    "unsupported",
    "backfill",
    "coverage",
    "relation",
)

PROGRESS_VERBS = (
    "fixed",
    "resolved",
    "improved",
    "reduced",
    "completed",
    "burned down",
    "burnt down",
    "cleared",
    "solved",
)


def load_contract(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    validate_required_fields(contract, failures, passes)
    if failures:
        return result(failures, warnings, passes)

    task_type = contract.get("task_type")
    verdict = nested_get(contract, "closeout_verdict", "selected")

    validate_task_type_and_verdict(task_type, verdict, failures, passes)
    validate_hard_state(contract, failures, passes)
    validate_scope(contract, failures, passes)
    validate_forbidden_missing_data_semantics(contract, failures, passes)
    validate_authority_claims(contract, failures, passes)
    validate_progress_claim_policy(contract, task_type, failures, passes)
    validate_layer_outcome_unit(contract, failures, passes)
    validate_outcome_measurement(contract, task_type, verdict, failures, passes)
    validate_evidence_and_validators(contract, task_type, failures, warnings, passes)
    validate_report_claims(contract, task_type, failures, warnings, passes)
    validate_next_target(contract, warnings, passes)

    return result(failures, warnings, passes)


def validate_required_fields(contract: dict[str, Any], failures: list[str], passes: list[str]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(contract))
    if missing:
        failures.append(f"missing required fields: {missing}")
    else:
        passes.append("required fields present")


def validate_task_type_and_verdict(
    task_type: Any,
    verdict: Any,
    failures: list[str],
    passes: list[str],
) -> None:
    if task_type not in TASK_TYPES:
        failures.append(f"invalid task_type: {task_type}")
        return
    passes.append(f"task_type valid: {task_type}")

    if verdict not in VERDICTS:
        failures.append(f"invalid closeout verdict: {verdict}")
        return
    if verdict == "INVALID_CLOSEOUT":
        failures.append("closeout verdict selected INVALID_CLOSEOUT")
        return
    if verdict not in VERDICTS_BY_TASK_TYPE[task_type]:
        failures.append(f"verdict {verdict} is not compatible with task_type {task_type}")
    else:
        passes.append(f"verdict compatible: {verdict}")


def validate_hard_state(contract: dict[str, Any], failures: list[str], passes: list[str]) -> None:
    hard_state = contract.get("hard_state") or {}
    for key, expected in REQUIRED_HARD_STATE.items():
        actual = hard_state.get(key)
        if actual != expected:
            failures.append(f"hard_state.{key} must be {expected}, got {actual}")
    if not any(item.startswith("hard_state.") for item in failures):
        passes.append("hard safety state closed")


def validate_scope(contract: dict[str, Any], failures: list[str], passes: list[str]) -> None:
    scope = contract.get("scope") or {}
    changed_paths = normalize_patterns(scope.get("changed_paths") or [])
    allowed_paths = normalize_patterns(scope.get("allowed_paths") or [])
    forbidden_paths = normalize_patterns(scope.get("forbidden_paths") or [])

    for path in changed_paths:
        if matches_any(path, forbidden_paths):
            failures.append(f"changed path violates forbidden scope: {path}")
        if allowed_paths and not matches_any(path, allowed_paths):
            failures.append(f"changed path is outside allowed scope: {path}")
    if changed_paths:
        passes.append(f"scope changed_paths checked: {len(changed_paths)}")
    else:
        warnings.append("scope.changed_paths is empty")


def validate_forbidden_missing_data_semantics(
    node: Any,
    failures: list[str],
    passes: list[str],
    path: str = "",
) -> None:
    found = False
    for key_path, value in walk(node, path):
        if key_path.endswith("missing_data_used_as_negative_evidence") and value is True:
            failures.append(f"missing/stale/incomplete data used as negative evidence at {key_path}")
            found = True
    if not found and path == "":
        passes.append("missing/stale/incomplete data semantics preserved")


def validate_authority_claims(contract: dict[str, Any], failures: list[str], passes: list[str]) -> None:
    claim_texts = collect_claim_text(contract)
    normalized = "\n".join(claim_texts).upper().replace(" ", "_").replace("-", "_")
    for term in sorted(AUTHORITY_GRANTING_TERMS):
        if re.search(rf"(^|[^A-Z0-9]){re.escape(term)}([^A-Z0-9]|$)", normalized):
            failures.append(f"forbidden authority claim appears in report/claims: {term}")
    if not any("forbidden authority claim" in item for item in failures):
        passes.append("no forbidden trading authority claims")


def validate_progress_claim_policy(
    contract: dict[str, Any],
    task_type: str,
    failures: list[str],
    passes: list[str],
) -> None:
    actual_progress = nested_get(contract, "progress_claim_policy", "actual_underlying_progress")
    outcome_allows_problem_progress = nested_get(contract, "outcome_unit", "problem_progress_claim_allowed")
    report_progress = nested_get(contract, "report", "actual_underlying_progress")

    if task_type in PROGRESS_FORBIDDEN_TASK_TYPES:
        if actual_progress is True:
            failures.append(f"{task_type} cannot set actual_underlying_progress true")
        if outcome_allows_problem_progress is True:
            failures.append(f"{task_type} cannot allow underlying problem progress claim")
        if report_progress is True:
            failures.append(f"{task_type} report cannot claim actual underlying progress")
    elif task_type == "OUTCOME_CHANGE":
        if actual_progress is not True:
            failures.append("OUTCOME_CHANGE must explicitly allow actual_underlying_progress")
        if outcome_allows_problem_progress is not True:
            failures.append("OUTCOME_CHANGE outcome_unit must allow problem progress claim")

    passes.append("progress claim policy checked")


def validate_outcome_measurement(
    contract: dict[str, Any],
    task_type: str,
    verdict: str,
    failures: list[str],
    passes: list[str],
) -> None:
    if verdict == "BLOCKED_BY_UPSTREAM":
        passes.append("outcome delta not required for BLOCKED_BY_UPSTREAM")
        return

    if task_type == "OUTCOME_CHANGE":
        validate_delta(contract, failures, passes)
        return

    if task_type == "TERMINALIZE":
        count = nested_get(contract, "after", "terminalized_count")
        if not positive_number(count):
            failures.append("TERMINALIZE requires after.terminalized_count > 0")
        else:
            passes.append(f"terminalized_count positive: {count}")
        return

    if task_type == "RECLASSIFY":
        count = nested_get(contract, "after", "reclassified_count")
        if not positive_number(count):
            failures.append("RECLASSIFY requires after.reclassified_count > 0")
        else:
            passes.append(f"reclassified_count positive: {count}")
        return

    if task_type == "HARNESS_BOOTSTRAP":
        harness_progress = nested_get(contract, "outcome_unit", "harness_progress_claim_allowed")
        if harness_progress is not True:
            failures.append("HARNESS_BOOTSTRAP requires harness_progress_claim_allowed true")
        validate_delta(contract, failures, passes, allow_equal=False)


def validate_delta(
    contract: dict[str, Any],
    failures: list[str],
    passes: list[str],
    allow_equal: bool = False,
) -> None:
    baseline_value = nested_get(contract, "baseline", "value")
    after_value = nested_get(contract, "after", "value")
    if baseline_value is None:
        failures.append("baseline.value is required for measured progress")
        return
    if after_value is None:
        failures.append("after.value is required for measured progress")
        return
    if not is_number(baseline_value) or not is_number(after_value):
        failures.append("baseline.value and after.value must be numeric")
        return

    direction = nested_get(contract, "outcome_unit", "direction")
    if direction == "decrease":
        moved = after_value < baseline_value or (allow_equal and after_value == baseline_value)
    elif direction == "increase":
        moved = after_value > baseline_value or (allow_equal and after_value == baseline_value)
    elif direction == "change":
        moved = after_value != baseline_value or allow_equal
    else:
        failures.append(f"unsupported outcome_unit.direction: {direction}")
        return

    if moved:
        passes.append(f"outcome moved: {baseline_value} -> {after_value} ({direction})")
    else:
        failures.append(f"outcome did not move in required direction: {baseline_value} -> {after_value} ({direction})")


def validate_evidence_and_validators(
    contract: dict[str, Any],
    task_type: str,
    failures: list[str],
    warnings: list[str],
    passes: list[str],
) -> None:
    evidence = nested_get(contract, "evidence_artifacts", "required") or []
    validators = nested_get(contract, "validators", "required") or []
    commands = nested_get(contract, "measurement_method", "commands") or []

    if not evidence:
        failures.append("evidence_artifacts.required must not be empty")
    else:
        passes.append(f"evidence artifacts declared: {len(evidence)}")

    if not validators:
        failures.append("validators.required must not be empty")
    else:
        passes.append(f"validators declared: {len(validators)}")

    if task_type in {"OUTCOME_CHANGE", "TERMINALIZE", "RECLASSIFY", "HARNESS_BOOTSTRAP"} and not commands:
        failures.append(f"{task_type} requires measurement_method.commands")
    elif not commands:
        warnings.append("measurement_method.commands is empty")
    else:
        passes.append(f"measurement commands declared: {len(commands)}")


def validate_report_claims(
    contract: dict[str, Any],
    task_type: str,
    failures: list[str],
    warnings: list[str],
    passes: list[str],
) -> None:
    report = contract.get("report") or {}
    report_claims = "\n".join(stringify(item) for item in [report.get("summary"), *(report.get("claims") or [])])
    progress_class = report.get("progress_class")
    if task_type == "HARNESS_BOOTSTRAP" and progress_class != "HARNESS_PROGRESS_ONLY":
        failures.append("HARNESS_BOOTSTRAP report.progress_class must be HARNESS_PROGRESS_ONLY")

    if task_type in PROGRESS_FORBIDDEN_TASK_TYPES and looks_like_underlying_progress_claim(report_claims):
        failures.append(f"{task_type} report appears to claim underlying domain progress")
    elif not report_claims.strip():
        warnings.append("report summary/claims are empty")
    else:
        passes.append("report claims checked")


def validate_next_target(contract: dict[str, Any], warnings: list[str], passes: list[str]) -> None:
    next_target = contract.get("next_target") or {}
    if next_target.get("required") is not True:
        warnings.append("next_target.required is not true")
        return
    required_keys = {"task_type", "outcome_unit", "required_baseline", "required_validator"}
    missing = [key for key in required_keys if not next_target.get(key)]
    if missing:
        warnings.append(f"next_target missing recommended fields: {missing}")
    else:
        passes.append("next target declared")


def result(failures: list[str], warnings: list[str], passes: list[str]) -> dict[str, Any]:
    status = "FAIL" if failures else "PASS"
    return {"status": status, "passes": passes, "warnings": warnings, "failures": failures}


def nested_get(node: dict[str, Any], *keys: str) -> Any:
    current: Any = node
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def normalize_patterns(patterns: list[str]) -> list[str]:
    return [pattern.replace("\\", "/") for pattern in patterns]


def matches_any(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def walk(node: Any, path: str = ""):
    if isinstance(node, dict):
        for key, value in node.items():
            next_path = f"{path}.{key}" if path else str(key)
            yield from walk(value, next_path)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            next_path = f"{path}[{index}]"
            yield from walk(value, next_path)
    else:
        yield path, node


def collect_claim_text(contract: dict[str, Any]) -> list[str]:
    report = contract.get("report") or {}
    progress_policy = contract.get("progress_claim_policy") or {}
    text: list[str] = []
    for key in ("summary", "claims", "claimed_capabilities", "closeout_claims"):
        text.extend(flatten_strings(report.get(key)))
        text.extend(flatten_strings(progress_policy.get(key)))
    text.extend(flatten_strings(contract.get("claimed_capabilities")))
    return text


def flatten_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            output.extend(flatten_strings(item))
        return output
    if isinstance(value, dict):
        output: list[str] = []
        for item in value.values():
            output.extend(flatten_strings(item))
        return output
    return [str(value)]


def looks_like_underlying_progress_claim(text: str) -> bool:
    normalized = text.lower()
    return any(noun in normalized for noun in UNDERLYING_PROGRESS_TERMS) and any(
        verb in normalized for verb in PROGRESS_VERBS
    )


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def positive_number(value: Any) -> bool:
    return is_number(value) and value > 0


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Prime task_result_contract YAML files.")
    parser.add_argument("contracts", nargs="+", help="Contract YAML file paths")
    parser.add_argument("--json", action="store_true", help="Print full JSON validation result")
    args = parser.parse_args(argv)

    exit_code = 0
    for contract_path in args.contracts:
        validation = validate_contract(load_contract(contract_path))
        if args.json:
            print(json.dumps({"path": contract_path, **validation}, ensure_ascii=False, indent=2))
        else:
            print(f"{validation['status']} {contract_path}")
            for failure in validation["failures"]:
                print(f"  FAIL: {failure}")
            for warning in validation["warnings"]:
                print(f"  WARN: {warning}")
        if validation["status"] != "PASS":
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
