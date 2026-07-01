# Codex Context Bundle

Task: TASK-4188
Profile: DOCS_GOVERNANCE
Generated At: 2026-07-01T14:46:52+00:00
Token Count: 6329
Token Count Mode: approximate
Max Tokens: 22000

---

## Included Files

| Path | Bytes | Tokens | Reason |
|---|---:|---:|---|
| AGENTS.md | 1380 | 345 | must_include |
| docs/reports/task_4188_project_hygiene_system_and_root_cleanup_governance/report.md | 84 | 21 | optional_include |
| ops/context_bundles.yaml | 5418 | 1354 | must_include |
| ops/operating_state.yaml | 604 | 151 | must_include |
| ops/project_hygiene_policy.yaml | 4773 | 1193 | must_include |
| ops/task_profiles.yaml | 4379 | 1094 | must_include |
| scripts/ops/validate_codex_closeout.py | 2638 | 659 | must_include |
| scripts/ops/validate_project_hygiene.py | 6048 | 1512 | must_include |

---

## Excluded Files

| Pattern/Path | Reason |
|---|---|
| docs/archive/** | configured exclude |
| node_modules/** | configured exclude |
| data/** | configured exclude |
| db/** | configured exclude |

---

## File: AGENTS.md

```md
# AGENTS.md

## Project Identity

This repository is a Trading Operating System for observing, verifying, monitoring, and controlling an automated US equity trading engine.

It is not a retail brokerage UI, stock recommendation app, or chart-first app.

## Mandatory Operating Rules

1. Do not start work without a task id.
2. Do not scan the whole repository by default.
3. Read generated context bundles first when they exist.
4. Follow `ops/task_profiles.yaml`.
5. Respect `ops/doc_registry.yaml`.
6. Never treat archived/superseded docs as active SSOT.
7. Do not create new markdown reports outside the relevant task report folder.
8. All task outputs must update `ops/task_registry.yaml`.
9. All new docs must update `ops/doc_registry.yaml`.
10. Run required validators before closeout.

## Trading Safety

- No real capital.
- No live order.
- No broker mutation.
- No paper promotion unless explicitly accepted.
- Missing or stale data is UNKNOWN/BLOCKER, not negative evidence.

## UI Safety

- No one-off components.
- No business logic in UI.
- No IA redesign without approval.
- Storybook before P0 screens.
- Screenshot/Vision QA required for UI screens.

## Completion Definition

A task is complete only when:

- task registry updated
- doc registry updated
- required validators pass
- artifact manifest exists
- no forbidden files touched
- closeout report exists

```

---

## File: docs/reports/task_4188_project_hygiene_system_and_root_cleanup_governance/report.md

```md
# TASK-4188 Project Hygiene System and Root Cleanup Governance

## Goal

## Results

```

---

## File: ops/context_bundles.yaml

```yaml
version: 1
updated_at: "2026-06-29"

defaults:
  max_tokens: 20000
  tokenizer: tiktoken
  encoding: cl100k_base
  include_file_headers: true
  fail_on_token_budget_exceeded: true
  reject_codex_read_never: true
  reject_superseded_by_default: true

bundles:
  TASK_4100:
    task_id: TASK-4100
    profile: DOCS_GOVERNANCE
    max_tokens: 22000
    must_include:
      - AGENTS.md
      - ops/operating_state.yaml
      - ops/task_registry.yaml
      - ops/doc_registry.yaml
      - ops/task_profiles.yaml
      - ops/context_bundles.yaml
    optional_include:
      - docs/reports/task_4100_codex_governance_bootstrap/report.md
    exclude:
      - node_modules/**
      - .git/**
      - data/**
      - db/**
      - secrets/**
      - screenshots/**
      - docs/archive/**

  UI_STORYBOOK_VISION:
    profile: UI_STORYBOOK_VISION
    max_tokens: 24000
    must_include:
      - AGENTS.md
      - ops/task_profiles.yaml
      - ops/profile_validation_rules.yaml
      - docs/frontend_app_ssot/00_PROJECT_SSOT.md
      - docs/frontend_app_ssot/01_ACTIVE_FRONTEND_TARGET_AND_STACK_DECISION.md
      - docs/frontend_app_ssot/02_INFORMATION_ARCHITECTURE.md
      - docs/frontend_app_ssot/05_ROUTE_MAP_AND_SCREEN_REGISTRY.md
      - docs/frontend_app_ssot/06_DESIGN_SYSTEM.md
      - docs/frontend_app_ssot/07_COMPONENT_CATALOG.md
      - docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md
      - docs/frontend_app_ssot/11_STORYBOOK_AND_QA_PLAN.md
      - docs/frontend_app_ssot/12_SCREENSHOT_QA_PREFLIGHT_PLAN.md
      - docs/frontend_app_ssot/21_SCAFFOLD_ONLY_SCREEN_ASSEMBLY_BOUNDARY.md
    exclude:
      - docs/archive/**
      - docs/reports/**
      - node_modules/**
      - data/**
      - db/**

  TASK_4101:
    task_id: TASK-4101
    profile: UI_STORYBOOK_VISION
    max_tokens: 24000
    must_include:
      - AGENTS.md
      - ops/task_profiles.yaml
      - ops/context_bundles.yaml
      - ops/profile_validation_rules.yaml
      - docs/frontend_app_ssot/00_PROJECT_SSOT.md
      - docs/frontend_app_ssot/07_COMPONENT_CATALOG.md
      - docs/frontend_app_ssot/11_STORYBOOK_AND_QA_PLAN.md
      - docs/frontend_app_ssot/12_SCREENSHOT_QA_PREFLIGHT_PLAN.md
    optional_include:
      - docs/reports/task_4101_context_bundle_hardening/report.md
    exclude:
      - docs/archive/**
      - docs/reports/**
      - node_modules/**
      - data/**
      - db/**

  TASK_4102:
    task_id: TASK-4102
    profile: L4_THESIS_BUNDLE
    max_tokens: 22000
    must_include:
      - AGENTS.md
      - ops/task_profiles.yaml
      - ops/profile_validation_rules.yaml
      - .codex/skills/l4-thesis-bundle/SKILL.md
    optional_include:
      - docs/reports/task_4102_l4_profile_validator_hardening/report.md
    exclude:
      - docs/archive/**
      - node_modules/**
      - data/**
      - db/**

  TASK_4103:
    task_id: TASK-4103
    profile: L5_POLICY_ACTION
    max_tokens: 22000
    must_include:
      - AGENTS.md
      - ops/task_profiles.yaml
      - ops/profile_validation_rules.yaml
      - .codex/skills/l5-policy-action/SKILL.md
    optional_include:
      - docs/reports/task_4103_l5_policy_action_validator_hardening/report.md
    exclude:
      - docs/archive/**
      - node_modules/**
      - data/**
      - db/**

  TASK_4104:
    task_id: TASK-4104
    profile: DOCS_GOVERNANCE
    max_tokens: 22000
    must_include:
      - AGENTS.md
      - ops/task_registry.yaml
      - ops/doc_registry.yaml
      - ops/operating_state.yaml
      - scripts/ops/render_ops_dashboard.py
      - scripts/ops/validate_dashboard.py
    optional_include:
      - docs/reports/task_4104_mission_control_dashboard_v1/report.md
    exclude:
      - docs/archive/**
      - node_modules/**
      - data/**
      - db/**

  TASK_4105:
    task_id: TASK-4105
    profile: DOCS_GOVERNANCE
    max_tokens: 22000
    must_include:
      - AGENTS.md
      - ops/prompt_regression_cases.yaml
      - scripts/ops/validate_prompt_regression.py
      - .codex/skills/task-closeout/SKILL.md
      - .codex/skills/ui-storybook-vision/SKILL.md
      - .codex/skills/l5-policy-action/SKILL.md
    optional_include:
      - docs/reports/task_4105_prompt_regression_eval/report.md
    exclude:
      - docs/archive/**
      - node_modules/**
      - data/**
      - db/**

  TASK_4188:
    task_id: TASK-4188
    profile: DOCS_GOVERNANCE
    max_tokens: 22000
    must_include:
      - AGENTS.md
      - ops/operating_state.yaml
      - ops/task_profiles.yaml
      - ops/context_bundles.yaml
      - ops/project_hygiene_policy.yaml
      - scripts/ops/validate_project_hygiene.py
      - scripts/ops/validate_codex_closeout.py
    optional_include:
      - docs/reports/task_4188_project_hygiene_system_and_root_cleanup_governance/report.md
    exclude:
      - docs/archive/**
      - node_modules/**
      - data/**
      - db/**

  L4_THESIS_BUNDLE:
    profile: L4_THESIS_BUNDLE
    max_tokens: 24000
    must_include:
      - AGENTS.md
      - ops/task_profiles.yaml
      - docs/**/l4*
      - src/**/l4*
      - scripts/**/l4*
    exclude:
      - docs/archive/**
      - node_modules/**
      - data/**
      - db/**

  L5_POLICY_ACTION:
    profile: L5_POLICY_ACTION
    max_tokens: 24000
    must_include:
      - AGENTS.md
      - ops/task_profiles.yaml
      - docs/**/l5*
      - src/**/l5*
      - scripts/**/l5*
    exclude:
      - docs/archive/**
      - node_modules/**
      - data/**
      - db/**

```

---

## File: ops/operating_state.yaml

```yaml
project:
  name: Stock-Investment
  identity: Trading Operating System
  updated_at: "2026-06-29"

hard_boundaries:
  strategy_status: NOT_ACCEPTED
  deployment_status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
  real_capital: FORBIDDEN
  broker_mutation: FORBIDDEN
  live_order: FORBIDDEN
  paper_promotion: FORBIDDEN_UNLESS_EXPLICITLY_ACCEPTED
  missing_or_stale_data: UNKNOWN_OR_BLOCKER

codex_governance:
  task_registry: ops/task_registry.yaml
  doc_registry: ops/doc_registry.yaml
  task_profiles: ops/task_profiles.yaml
  context_bundles: ops/context_bundles.yaml
  dashboard: ops/dashboard/index.html

```

---

## File: ops/project_hygiene_policy.yaml

```yaml
version: 1
updated_at: "2026-07-01"
created_by_task: TASK-4188

purpose:
  - keep the project root readable
  - prevent new unclassified root clutter
  - separate active source-of-truth files from navigation and historical material
  - make cleanup a validator-backed closeout gate instead of an occasional manual sweep

validation:
  root_scan_depth: 1
  fail_on_unclassified_root_entry: true
  warn_on_known_debt: true
  warn_on_sensitive_root_file: true

canonical_surfaces:
  project_entry:
    - AGENTS.md
    - README.md
  governance:
    - ops/operating_state.yaml
    - ops/task_registry.yaml
    - ops/doc_registry.yaml
    - ops/task_profiles.yaml
    - ops/context_bundles.yaml
    - ops/project_hygiene_policy.yaml
  active_operating_docs:
    - docs/operating_system/project_operating_state.md
    - docs/architecture/skill_md_subagent_canonicalization_map.md
  generated_context:
    - docs/generated_context
  task_reports:
    - docs/reports/task_*

root_entries:
  - name: .codex
    kind: directory
    classification: local_codex_state
    action: keep_local_only
  - name: .dvc
    kind: directory
    classification: data_versioning_metadata
    action: keep
  - name: .git
    kind: directory
    classification: vcs_metadata
    action: keep
  - name: .obsidian
    kind: directory
    classification: local_obsidian_state
    action: keep_local_only
  - name: .pytest_cache
    kind: directory
    classification: transient_cache_known_debt
    action: cleanup_candidate
  - name: apps
    kind: directory
    classification: application_surfaces
    action: keep
  - name: config
    kind: directory
    classification: config_alias_known_debt
    action: review_before_move
  - name: configs
    kind: directory
    classification: canonical_config
    action: keep
  - name: data
    kind: directory
    classification: data_artifacts_protected
    action: keep_protected
  - name: docs
    kind: directory
    classification: documentation
    action: keep
  - name: frontend
    kind: directory
    classification: frontend_surface_known_debt
    action: review_against_apps
  - name: logs
    kind: directory
    classification: runtime_logs
    action: keep_local_or_rotate
  - name: ops
    kind: directory
    classification: governance
    action: keep
  - name: prompts
    kind: directory
    classification: prompt_governance
    action: keep
  - name: schemas
    kind: directory
    classification: contracts
    action: keep
  - name: scripts
    kind: directory
    classification: automation_and_validators
    action: keep
  - name: src
    kind: directory
    classification: source_code
    action: keep
  - name: tasks
    kind: directory
    classification: task_local_state_known_debt
    action: review_against_task_registry
  - name: tests
    kind: directory
    classification: tests
    action: keep
  - name: tools
    kind: directory
    classification: tools
    action: keep
  - name: .dvcignore
    kind: file
    classification: data_versioning_config
    action: keep
  - name: .env
    kind: file
    classification: local_secret
    action: keep_local_only_do_not_read
  - name: .gitignore
    kind: file
    classification: vcs_config
    action: keep
  - name: .kis_token_cache.json
    kind: file
    classification: local_secret_token_cache
    action: keep_local_only_do_not_read
  - name: AGENTS.md
    kind: file
    classification: root_agent_rules
    action: keep
  - name: README.md
    kind: file
    classification: project_entry_doc
    action: keep
  - name: trading.db
    kind: file
    classification: local_runtime_db_known_debt
    action: review_before_move_or_delete
  - name: trading-DESKTOP-2R00TB4.db
    kind: file
    classification: machine_conflict_db_known_debt
    action: review_before_move_or_delete

layer_rules:
  L0_L1_DATA_PIPELINE:
    canonical_dirs:
      - src/data
      - tools/db/source_acquisition
      - data/artifacts
      - docs/reports/task_*
    forbidden_cleanup_actions:
      - infer_missing_source_truth
      - delete_raw_data_without_task_artifact
      - move_db_or_source_artifacts_without_owner_review
  L2_L4_ANALYSIS:
    canonical_dirs:
      - src/l2
      - src/brain
      - docs/reports/task_*
    forbidden_cleanup_actions:
      - convert_unknown_to_negative_evidence
      - treat_historical_reports_as_active_ssot
  OPS_GOVERNANCE:
    canonical_dirs:
      - ops
      - scripts/ops
      - docs/generated_context
      - docs/reports/task_*
    required_closeout_gate:
      - python scripts/ops/validate_project_hygiene.py

known_debt_policy:
  meaning: Known debt is allowed to exist only because it is explicitly classified here.
  closeout_behavior: warn
  cleanup_rule: move_or_delete_only_with_task_scope_artifact_and_owner_review

```

---

## File: ops/task_profiles.yaml

```yaml
version: 1
updated_at: "2026-06-29"

profiles:
  DOCS_GOVERNANCE:
    purpose: Maintain task/document registry, context bundles, governance tooling.
    allowed_intents:
      - create_or_update_registries
      - create_validators
      - render_read_only_dashboard
      - create_context_bundles
    forbidden_intents:
      - trading_logic_change
      - broker_mutation
      - live_order
      - db_schema_change
      - scheduler_registration_change
      - strategy_acceptance_change
    required_outputs:
      - task_registry_update
      - doc_registry_update
      - report
      - artifact_manifest
      - validation_results

  L0_L1_DATA_PIPELINE:
    purpose: Raw source acquisition, storage, normalization, source-time integrity.
    required_principles:
      - source_time_must_be_preserved
      - raw_data_integrity_first
      - no_strategy_logic
      - missing_or_stale_data_is_unknown_or_blocker
    forbidden_intents:
      - candidate_promotion
      - policy_action
      - order_intent
      - broker_mutation
      - live_order
    required_checks:
      - storage_contract
      - source_time_audit
      - freshness_status
      - artifact_manifest

  L2_INTERPRETATION:
    purpose: Convert raw/source data into economic meaning without promotion or execution.
    required_principles:
      - actual_vs_inference_separation
      - missing_data_explicit
      - no_unverified_source_claims
    forbidden_intents:
      - portfolio_sizing
      - order_intent
      - broker_mutation
      - live_order

  L3_RELATIONSHIP:
    purpose: Validate economic relationships and chains.
    required_principles:
      - relationship_evidence_required
      - chain_break_conditions_required
      - contradictory_evidence_must_be_visible
    forbidden_intents:
      - order_intent
      - broker_mutation
      - live_order

  L4_THESIS_BUNDLE:
    purpose: Construct and validate thesis bundles at institutional quality.
    required_principles:
      - thesis_specificity
      - evidence_linkage
      - source_traceability
      - contradiction_handling
      - blocked_context_mixed_rate_visibility
    forbidden_intents:
      - final_policy_action
      - broker_mutation
      - live_order
      - paper_promotion
    required_checks:
      - thesis_quality_review
      - evidence_coverage
      - source_access
      - institutional_quality_score

  L5_POLICY_ACTION:
    purpose: Translate thesis state into review-only policy actions.
    required_principles:
      - review_only_boundary
      - sizing_intent_separation
      - order_intent_separation
      - hold_reduce_exit_rerisk_support
    forbidden_intents:
      - broker_mutation
      - live_order
      - auto_approval
      - real_capital
    required_checks:
      - policy_action_schema
      - no_broker_mutation
      - no_live_order

  L6_EXECUTION_SAFETY:
    purpose: Execution safety, order lifecycle visibility, broker truth checks.
    required_principles:
      - user_control_required
      - no_real_capital
      - no_live_order_without_explicit_acceptance
      - broker_truth_separation
      - kill_switch_visibility
    forbidden_intents:
      - hidden_order_mutation
      - bypass_approval
      - live_order_enablement
      - real_capital_enablement
    required_checks:
      - broker_mutation_absent
      - order_control_audit
      - kill_switch_audit
      - execution_permission_audit

  UI_STORYBOOK_VISION:
    purpose: Expo/React Native UI implementation using component-first, Storybook, screenshot QA.
    required_principles:
      - component_first
      - storybook_before_p0_screens
      - screenshot_qa_required
      - ui_is_pure_rendering
      - no_business_logic_in_ui
      - no_chart_first_screens
    forbidden_intents:
      - ia_redesign_without_approval
      - one_off_component
      - promotion_calculation_in_ui
      - risk_calculation_in_ui
      - order_mutation
    required_checks:
      - typecheck
      - lint
      - storybook_story_exists
      - screenshot_exists
      - vision_review_report

  TASK_CLOSEOUT:
    purpose: Close tasks only after registries, artifacts, validators, and reports are complete.
    required_principles:
      - no_done_without_validator_pass
      - artifact_manifest_required
      - doc_registry_update_required
      - task_registry_update_required
      - forbidden_paths_clean

```

---

## File: scripts/ops/validate_codex_closeout.py

```py
from __future__ import annotations

import argparse
import shlex
import sys

from ops_common import context_config, get_task, print_result, run_command


def has_context_bundle(task_id: str) -> bool:
    try:
        return any(bundle.get("task_id") == task_id for bundle in context_config().get("bundles", {}).values())
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    try:
        task = get_task(args.task)
    except Exception as exc:
        return print_result("CODEX CLOSEOUT VALIDATION", [], [], [str(exc)])

    commands = [
        "python scripts/ops/validate_task_registry.py",
        "python scripts/ops/validate_doc_registry.py --soft",
        "python scripts/ops/validate_project_hygiene.py",
        f"python scripts/ops/validate_prime_task_contracts.py --task {args.task}",
        f"python scripts/ops/validate_task_scope.py --task {args.task}",
        f"python scripts/ops/validate_required_artifacts.py --task {args.task}",
    ]
    if has_context_bundle(args.task):
        commands.insert(2, f"python scripts/ops/validate_context_bundle.py --task {args.task}")
    for command in task.get("required_validators", []):
        normalized = command.strip()
        if normalized.startswith("python scripts/ops/validate_codex_closeout.py"):
            continue
        if command not in commands:
            commands.append(command)
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    for command in commands:
        code, output = run_command(shlex.split(command))
        if code == 0:
            if "RESULT: PASS_WITH_WARNINGS" in output:
                warnings.append(f"{command}: PASS_WITH_WARNINGS")
            else:
                passes.append(f"{command}: PASS")
        else:
            failures.append(f"{command}: FAIL\n{output.strip()}")

    closeout = task.get("closeout", {})
    required_flags = [
        "registry_updated",
        "doc_registry_updated",
        "validators_passed",
        "artifact_manifest_exists",
        "forbidden_paths_clean",
    ]
    for flag in required_flags:
        if closeout.get(flag) is True:
            passes.append(f"closeout.{flag}: true")
        else:
            failures.append(f"closeout.{flag} is not true")

    if task.get("status") == "DONE" and failures:
        failures.append("task is DONE but closeout conditions failed")

    return print_result("CODEX CLOSEOUT VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())

```

---

## File: scripts/ops/validate_project_hygiene.py

```py
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

from ops_common import ROOT, load_yaml, print_result


POLICY_PATH = "ops/project_hygiene_policy.yaml"


def normalize(path: Path) -> str:
    return path.name.replace("\\", "/")


def root_entries() -> list[Path]:
    return sorted(ROOT.iterdir(), key=lambda item: item.name.lower())


def policy_entries(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for item in policy.get("root_entries", []):
        name = str(item.get("name") or "").strip()
        if name:
            entries[name] = item
    return entries


def write_inventory(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "name",
                "actual_kind",
                "declared_kind",
                "classification",
                "action",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-out")
    parser.add_argument("--strict-known-debt", action="store_true")
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        policy = load_yaml(POLICY_PATH)
    except Exception as exc:
        return print_result("PROJECT HYGIENE VALIDATION", [], [], [str(exc)])

    declared = policy_entries(policy)
    if not declared:
        failures.append("no root_entries declared in project hygiene policy")

    seen_declared: set[str] = set()
    duplicates: set[str] = set()
    for item in policy.get("root_entries", []):
        name = str(item.get("name") or "").strip()
        if name in seen_declared:
            duplicates.add(name)
        seen_declared.add(name)
    for name in sorted(duplicates):
        failures.append(f"duplicate root entry declaration: {name}")

    inventory_rows: list[dict[str, str]] = []
    unclassified: list[str] = []
    known_debt: list[str] = []
    sensitive: list[str] = []

    for entry in root_entries():
        name = normalize(entry)
        actual_kind = "directory" if entry.is_dir() else "file"
        declared_entry = declared.get(name)
        if declared_entry is None:
            unclassified.append(name)
            inventory_rows.append(
                {
                    "name": name,
                    "actual_kind": actual_kind,
                    "declared_kind": "",
                    "classification": "UNCLASSIFIED",
                    "action": "classify_or_remove",
                    "status": "FAIL",
                }
            )
            continue

        declared_kind = str(declared_entry.get("kind") or "")
        classification = str(declared_entry.get("classification") or "")
        action = str(declared_entry.get("action") or "")
        status = "PASS"
        if declared_kind and declared_kind != actual_kind:
            failures.append(
                f"root entry kind mismatch: {name} actual={actual_kind} declared={declared_kind}"
            )
            status = "FAIL"
        if "known_debt" in classification:
            known_debt.append(name)
            status = "WARN" if status == "PASS" else status
        if "secret" in classification or "token" in classification:
            sensitive.append(name)
            status = "WARN" if status == "PASS" else status
        inventory_rows.append(
            {
                "name": name,
                "actual_kind": actual_kind,
                "declared_kind": declared_kind,
                "classification": classification,
                "action": action,
                "status": status,
            }
        )

    missing = sorted(set(declared) - {normalize(entry) for entry in root_entries()})
    for name in missing:
        warnings.append(f"declared root entry not present: {name}")

    if unclassified and policy.get("validation", {}).get("fail_on_unclassified_root_entry", True):
        failures.extend(f"unclassified root entry: {name}" for name in sorted(unclassified))
    elif unclassified:
        warnings.extend(f"unclassified root entry: {name}" for name in sorted(unclassified))

    if known_debt:
        message = f"known_debt root entries: {', '.join(sorted(known_debt))}"
        if args.strict_known_debt:
            failures.append(message)
        elif policy.get("validation", {}).get("warn_on_known_debt", True):
            warnings.append(message)

    if sensitive and policy.get("validation", {}).get("warn_on_sensitive_root_file", True):
        warnings.append(f"sensitive local root entries classified do-not-read: {', '.join(sorted(sensitive))}")

    for path in policy.get("canonical_surfaces", {}).get("governance", []):
        if not (ROOT / path).exists():
            failures.append(f"missing governance surface: {path}")

    closeout_path = ROOT / "scripts/ops/validate_codex_closeout.py"
    closeout_text = closeout_path.read_text(encoding="utf-8") if closeout_path.exists() else ""
    if "validate_project_hygiene.py" in closeout_text:
        passes.append("closeout_gate_includes_project_hygiene")
    else:
        failures.append("closeout gate does not include validate_project_hygiene.py")

    if args.inventory_out:
        write_inventory(ROOT / args.inventory_out, inventory_rows)
        passes.append(f"inventory_written: {args.inventory_out}")

    passes.append(f"root_entries_seen: {len(inventory_rows)}")
    passes.append(f"root_entries_classified: {len(inventory_rows) - len(unclassified)}")
    if not unclassified:
        passes.append("no_unclassified_root_entries")

    return print_result("PROJECT HYGIENE VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())

```
