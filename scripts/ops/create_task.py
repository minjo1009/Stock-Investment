from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date

try:
    from ops_common import ROOT, load_yaml, write_text, write_yaml
except ModuleNotFoundError:
    from scripts.ops.ops_common import ROOT, load_yaml, write_text, write_yaml


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug[:80] or "task"


def write_if_allowed(path, content: str, force: bool) -> None:
    if path.exists() and path.stat().st_size > 0 and not force:
        raise FileExistsError(f"refusing to overwrite non-empty file without --force: {path}")
    write_text(path, content)


def starter_contract(task_id: str, title: str, folder: str) -> str:
    return f"""task_id: "{task_id}"
task_type: "DIAGNOSTIC_ONLY"
domain: "task_bootstrap"
hard_state:
  strategy: "NOT_ACCEPTED"
  deployment: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"
  real_capital: "FORBIDDEN"
  broker_mutation: "FORBIDDEN"
  live_order: "FORBIDDEN"
  paper_promotion: "FORBIDDEN"
  missing_stale_incomplete_data_semantics: "UNKNOWN_OR_BLOCKER_NEVER_NEGATIVE_EVIDENCE"
scope:
  allowed_paths:
    - "{folder}/**"
  forbidden_paths:
    - "broker/**"
    - "live_trading/**"
    - "production_orders/**"
    - "secrets/**"
    - "configs/broker/**"
  changed_paths:
    - "{folder}/task_result_contract.yaml"
    - "{folder}/report.md"
    - "{folder}/artifact_manifest.csv"
    - "{folder}/validation_results.md"
outcome_unit:
  name: "diagnostic_task_bootstrap"
  type: "diagnostic"
  direction: "increase"
  problem_progress_claim_allowed: false
  harness_progress_claim_allowed: false
intended_change:
  description: "Bootstrap task contract for {title}."
  target:
    value: 1
measurement_method:
  commands:
    - "python scripts/ops/validate_prime_task_contracts.py --task {task_id}"
  comparison_rule: "contract_presence_and_validation"
  same_method_before_after_required: false
allowed_actions:
  - "edit task-scoped artifacts"
forbidden_actions:
  - "No broker mutation"
  - "No live order"
  - "No paper promotion"
  - "No strategy acceptance"
  - "No deployment readiness claim"
  - "Do not treat missing/stale/incomplete data as negative evidence"
evidence_artifacts:
  required:
    - "{folder}/task_result_contract.yaml"
validators:
  required:
    - "prime_task_contract_validator"
    - "outcome_contract_validator"
progress_claim_policy:
  progress_class: "DIAGNOSTIC_ONLY"
  actual_underlying_progress: false
  allowed_claims:
    - "task contract exists and is valid"
  forbidden_claims:
    - "underlying problem progress"
closeout_verdict:
  selected: "VALID_DIAGNOSTIC_ONLY"
report:
  actual_underlying_progress: false
  progress_class: "DIAGNOSTIC_ONLY"
  summary: "Starter task contract for {task_id}; update before closeout if this task claims actual progress."
  claims:
    - "Task contract scaffolded."
next_target:
  required: true
  task_type: "OUTCOME_CHANGE"
  outcome_unit: "task-specific measured outcome"
  required_baseline: "baseline.value before implementation"
  required_validator: "task-specific validator"
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--priority", default="P1")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    registry = load_yaml("ops/task_registry.yaml")
    profiles = load_yaml("ops/task_profiles.yaml").get("profiles", {})
    if args.profile not in profiles:
        print(f"FAIL unknown profile: {args.profile}")
        return 1

    today = date.today().isoformat()
    folder = f"docs/reports/{args.task_id.lower().replace('-', '_')}_{slugify(args.title)}"
    required_artifacts = [
        f"{folder}/task_result_contract.yaml",
        f"{folder}/report.md",
        f"{folder}/artifact_manifest.csv",
        f"{folder}/validation_results.md",
    ]
    task = {
        "task_id": args.task_id,
        "title": args.title,
        "status": "IN_PROGRESS",
        "priority": args.priority,
        "task_type": "UNCLASSIFIED",
        "profile": args.profile,
        "owner": "codex",
        "branch": None,
        "created_at": today,
        "updated_at": today,
        "objective": [],
        "allowed_paths": [f"{folder}/**"],
        "forbidden_paths": ["data/**", "db/**", "secrets/**"],
        "required_artifacts": required_artifacts,
        "required_validators": [
            "python scripts/ops/validate_task_registry.py",
            f"python scripts/ops/validate_prime_task_contracts.py --task {args.task_id}",
            f"python scripts/ops/validate_task_scope.py --task {args.task_id}",
            f"python scripts/ops/validate_required_artifacts.py --task {args.task_id}",
            f"python scripts/ops/validate_codex_closeout.py --task {args.task_id}",
        ],
        "closeout": {
            "registry_updated": False,
            "doc_registry_updated": False,
            "validators_passed": False,
            "artifact_manifest_exists": False,
            "forbidden_paths_clean": False,
            "status": "OPEN",
        },
    }
    tasks = registry.setdefault("tasks", [])
    for idx, existing in enumerate(tasks):
        if existing.get("task_id") == args.task_id:
            tasks[idx] = task
            break
    else:
        tasks.append(task)
    registry["updated_at"] = today
    write_yaml("ops/task_registry.yaml", registry)

    report_dir = ROOT / folder
    report_dir.mkdir(parents=True, exist_ok=True)
    write_if_allowed(report_dir / "task_result_contract.yaml", starter_contract(args.task_id, args.title, folder), args.force)
    write_if_allowed(report_dir / "report.md", f"# {args.task_id} {args.title}\n\n## Goal\n\n## Results\n", args.force)
    write_if_allowed(report_dir / "validation_results.md", f"# Validation Results - {args.task_id}\n\n| Command | Result | Notes |\n|---|---|---|\n", args.force)
    manifest = report_dir / "artifact_manifest.csv"
    if manifest.exists() and manifest.stat().st_size > 0 and not args.force:
        raise FileExistsError(f"refusing to overwrite non-empty file without --force: {manifest}")
    with manifest.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["path", "type", "purpose", "created_or_modified", "task_id"])
        for path in required_artifacts:
            writer.writerow([path, "TASK_ARTIFACT", "starter task artifact", "created", args.task_id])

    print(f"PASS task registry updated: {args.task_id}")
    print(f"PASS report folder: {folder}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAIL {exc}")
        sys.exit(1)
