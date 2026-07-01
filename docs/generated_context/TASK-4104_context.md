# Codex Context Bundle

Task: TASK-4104
Profile: DOCS_GOVERNANCE
Generated At: 2026-06-29T02:28:51+00:00
Token Count: 9379
Token Count Mode: approximate
Max Tokens: 22000

---

## Included Files

| Path | Bytes | Tokens | Reason |
|---|---:|---:|---|
| AGENTS.md | 1380 | 345 | must_include |
| docs/reports/task_4104_mission_control_dashboard_v1/report.md | 1037 | 259 | optional_include |
| ops/doc_registry.yaml | 14694 | 3673 | must_include |
| ops/operating_state.yaml | 604 | 151 | must_include |
| ops/task_registry.yaml | 10820 | 2705 | must_include |
| scripts/ops/render_ops_dashboard.py | 7426 | 1856 | must_include |
| scripts/ops/validate_dashboard.py | 1560 | 390 | must_include |

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

## File: docs/reports/task_4104_mission_control_dashboard_v1/report.md

```md
# TASK-4104 Mission Control Dashboard v1

## Decision Summary

- Verdict: PASS
- Strategy acceptance status: `NOT_ACCEPTED`
- Key metrics: dashboard renderer emits static HTML and machine-readable summary JSON
- What changed: dashboard now includes task/document counts and closeout status; dashboard validator added
- Next action: Add richer issue drilldowns only after registry data is stable

## Quant Expert Report

- Data source and source readiness: Ops registries only
- Exact join keys: Task IDs and registered document paths
- Leakage audit: No trading data used
- Split/OOS metrics: Not applicable
- Failure decomposition: Dashboard had no validator and no exported summary
- Cost/slippage stress where PnL changed: Not applicable
- Remaining blockers: Historical doc registry migration remains soft-mode only

## No-Background Decision-Maker Report

TASK-4104 improves the local mission-control page without adding a service, database, JS framework, or frontend app screen.

## Artifact Manifest

See `artifact_manifest.csv`.

```

---

## File: ops/doc_registry.yaml

```yaml
version: 1
updated_at: "2026-06-29"

enums:
  document_type:
    - SSOT
    - GOVERNANCE
    - REGISTRY
    - OPERATING_STATE
    - TASK_REPORT
    - VALIDATION_REPORT
    - ARTIFACT_MANIFEST
    - GENERATED_CONTEXT
    - ARCHIVE
    - REFERENCE
  document_status:
    - ACTIVE
    - HISTORICAL
    - SUPERSEDED
    - ARCHIVED
    - DEPRECATED
    - LOCAL_ONLY
    - UNKNOWN
  codex_read:
    - ALWAYS
    - TASK_PROFILE_ONLY
    - ONLY_IF_REFERENCED
    - NEVER

documents:
  - path: AGENTS.md
    type: GOVERNANCE
    domain: GLOBAL
    status: ACTIVE
    priority: P0
    codex_read: ALWAYS
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: ops/README.md
    type: GOVERNANCE
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: ops/operating_state.yaml
    type: OPERATING_STATE
    domain: GLOBAL
    status: ACTIVE
    priority: P0
    codex_read: ALWAYS
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: ops/task_registry.yaml
    type: REGISTRY
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ALWAYS
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: ops/doc_registry.yaml
    type: REGISTRY
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ALWAYS
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: ops/task_profiles.yaml
    type: GOVERNANCE
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ALWAYS
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: ops/context_bundles.yaml
    type: GOVERNANCE
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ALWAYS
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: ops/profile_validation_rules.yaml
    type: GOVERNANCE
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ALWAYS
    owner: codex_governance
    created_by_task: TASK-4102
    supersedes: []
    superseded_by: null

  - path: ops/prompt_regression_cases.yaml
    type: GOVERNANCE
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4105
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/README.md
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4100_context.md
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4100_manifest.csv
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4101_context.md
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4101
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4101_manifest.csv
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4101
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/UI-STORYBOOK-VISION_context.md
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4101
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/UI-STORYBOOK-VISION_manifest.csv
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4101
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4102_context.md
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4102
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4102_manifest.csv
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4102
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4103_context.md
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4103
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4103_manifest.csv
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4103
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4104_context.md
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4104
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4104_manifest.csv
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4104
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4105_context.md
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4105
    supersedes: []
    superseded_by: null

  - path: docs/generated_context/TASK-4105_manifest.csv
    type: GENERATED_CONTEXT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4105
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4100_codex_governance_bootstrap/report.md
    type: TASK_REPORT
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4100_codex_governance_bootstrap/artifact_manifest.csv
    type: ARTIFACT_MANIFEST
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4100_codex_governance_bootstrap/validation_results.md
    type: VALIDATION_REPORT
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4101_context_bundle_hardening/report.md
    type: TASK_REPORT
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4101
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4101_context_bundle_hardening/artifact_manifest.csv
    type: ARTIFACT_MANIFEST
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4101
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4101_context_bundle_hardening/validation_results.md
    type: VALIDATION_REPORT
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4101
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4102_l4_profile_validator_hardening/report.md
    type: TASK_REPORT
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4102
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4102_l4_profile_validator_hardening/artifact_manifest.csv
    type: ARTIFACT_MANIFEST
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4102
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4102_l4_profile_validator_hardening/validation_results.md
    type: VALIDATION_REPORT
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4102
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4103_l5_policy_action_validator_hardening/report.md
    type: TASK_REPORT
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4103
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4103_l5_policy_action_validator_hardening/artifact_manifest.csv
    type: ARTIFACT_MANIFEST
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4103
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4103_l5_policy_action_validator_hardening/validation_results.md
    type: VALIDATION_REPORT
    domain: OPS
    status: ACTIVE
    priority: P0
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4103
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4104_mission_control_dashboard_v1/report.md
    type: TASK_REPORT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4104
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4104_mission_control_dashboard_v1/artifact_manifest.csv
    type: ARTIFACT_MANIFEST
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4104
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4104_mission_control_dashboard_v1/validation_results.md
    type: VALIDATION_REPORT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4104
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4105_prompt_regression_eval/report.md
    type: TASK_REPORT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4105
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4105_prompt_regression_eval/artifact_manifest.csv
    type: ARTIFACT_MANIFEST
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4105
    supersedes: []
    superseded_by: null

  - path: docs/reports/task_4105_prompt_regression_eval/validation_results.md
    type: VALIDATION_REPORT
    domain: OPS
    status: ACTIVE
    priority: P1
    codex_read: ONLY_IF_REFERENCED
    owner: codex_governance
    created_by_task: TASK-4105
    supersedes: []
    superseded_by: null

  - path: .codex/skills/docs-governance/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: .codex/skills/context-bundle-builder/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: .codex/skills/task-closeout/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: .codex/skills/l0-l1-data-pipeline/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: .codex/skills/l2-interpretation/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: .codex/skills/l3-relationship/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: .codex/skills/l4-thesis-bundle/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: .codex/skills/l5-policy-action/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: .codex/skills/l6-execution-safety/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

  - path: .codex/skills/ui-storybook-vision/SKILL.md
    type: GOVERNANCE
    domain: CODEX_SKILL
    status: ACTIVE
    priority: P0
    codex_read: TASK_PROFILE_ONLY
    owner: codex_governance
    created_by_task: TASK-4100
    supersedes: []
    superseded_by: null

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

## File: ops/task_registry.yaml

```yaml
version: 1
updated_at: "2026-06-29"

enums:
  status:
    - BACKLOG
    - IN_PROGRESS
    - BLOCKED
    - REVIEW
    - DONE
    - CANCELLED
  priority:
    - P0
    - P1
    - P2
    - P3

tasks:
  - task_id: TASK-4100
    title: Codex Governance / Task Operating System Bootstrap
    status: DONE
    priority: P0
    task_type: OPS_GOVERNANCE
    profile: DOCS_GOVERNANCE
    owner: codex
    branch: null
    created_at: "2026-06-29"
    updated_at: "2026-06-29"

    objective:
      - prevent task/document sprawl
      - reduce token waste
      - enforce task profiles
      - create local mission-control dashboard

    allowed_paths:
      - AGENTS.md
      - .codex/**
      - ops/**
      - scripts/ops/**
      - docs/generated_context/**
      - docs/reports/task_4100_codex_governance_bootstrap/**

    forbidden_paths:
      - broker/**
      - live_trading/**
      - production_orders/**
      - secrets/**
      - configs/broker/**
      - src/**/order_execution/**
      - src/**/broker/**
      - src/**/strategy_live/**
      - data/**
      - db/**

    required_artifacts:
      - docs/reports/task_4100_codex_governance_bootstrap/report.md
      - docs/reports/task_4100_codex_governance_bootstrap/artifact_manifest.csv
      - docs/reports/task_4100_codex_governance_bootstrap/validation_results.md

    required_validators:
      - python scripts/ops/validate_task_registry.py
      - python scripts/ops/validate_doc_registry.py --soft
      - python scripts/ops/validate_context_bundle.py --task TASK-4100
      - python scripts/ops/validate_task_scope.py --task TASK-4100
      - python scripts/ops/validate_codex_closeout.py --task TASK-4100

    closeout:
      registry_updated: true
      doc_registry_updated: true
      validators_passed: true
      artifact_manifest_exists: true
      forbidden_paths_clean: true
      status: CLOSED

  - task_id: TASK-4101
    title: Context Bundle Hardening for UI Work
    status: DONE
    priority: P0
    task_type: OPS_GOVERNANCE
    profile: UI_STORYBOOK_VISION
    owner: codex
    branch: null
    created_at: "2026-06-29"
    updated_at: "2026-06-29"
    objective:
      - make UI Storybook/Vision context bundle buildable from current repo files
      - preserve no whole-repo scan behavior
      - validate UI profile rules before UI work
    allowed_paths:
      - ops/**
      - scripts/ops/**
      - docs/generated_context/**
      - docs/reports/task_4101_context_bundle_hardening/**
    forbidden_paths:
      - broker/**
      - live_trading/**
      - production_orders/**
      - secrets/**
      - configs/broker/**
      - src/**/order_execution/**
      - src/**/broker/**
      - src/**/strategy_live/**
      - data/**
      - db/**
    required_artifacts:
      - docs/reports/task_4101_context_bundle_hardening/report.md
      - docs/reports/task_4101_context_bundle_hardening/artifact_manifest.csv
      - docs/reports/task_4101_context_bundle_hardening/validation_results.md
    required_validators:
      - python scripts/ops/validate_task_registry.py
      - python scripts/ops/validate_doc_registry.py --soft
      - python scripts/ops/validate_context_bundle.py --task TASK-4101
      - python scripts/ops/validate_context_bundle.py --bundle UI_STORYBOOK_VISION
      - python scripts/ops/validate_task_profile_rules.py --profile UI_STORYBOOK_VISION
      - python scripts/ops/validate_task_scope.py --task TASK-4101
      - python scripts/ops/validate_required_artifacts.py --task TASK-4101
      - python scripts/ops/validate_codex_closeout.py --task TASK-4101
    closeout:
      registry_updated: true
      doc_registry_updated: true
      validators_passed: true
      artifact_manifest_exists: true
      forbidden_paths_clean: true
      status: CLOSED

  - task_id: TASK-4102
    title: L4 Profile Validator Hardening
    status: DONE
    priority: P0
    task_type: OPS_GOVERNANCE
    profile: L4_THESIS_BUNDLE
    owner: codex
    branch: null
    created_at: "2026-06-29"
    updated_at: "2026-06-29"
    objective:
      - add config-driven L4 thesis bundle profile validation
      - enforce L4 evidence and no-execution boundaries
    allowed_paths:
      - ops/**
      - scripts/ops/**
      - docs/generated_context/**
      - docs/reports/task_4102_l4_profile_validator_hardening/**
    forbidden_paths:
      - broker/**
      - live_trading/**
      - production_orders/**
      - secrets/**
      - configs/broker/**
      - src/**/order_execution/**
      - src/**/broker/**
      - src/**/strategy_live/**
      - data/**
      - db/**
    required_artifacts:
      - docs/reports/task_4102_l4_profile_validator_hardening/report.md
      - docs/reports/task_4102_l4_profile_validator_hardening/artifact_manifest.csv
      - docs/reports/task_4102_l4_profile_validator_hardening/validation_results.md
    required_validators:
      - python scripts/ops/validate_task_registry.py
      - python scripts/ops/validate_doc_registry.py --soft
      - python scripts/ops/validate_context_bundle.py --task TASK-4102
      - python scripts/ops/validate_task_profile_rules.py --profile L4_THESIS_BUNDLE
      - python scripts/ops/validate_task_scope.py --task TASK-4102
      - python scripts/ops/validate_required_artifacts.py --task TASK-4102
      - python scripts/ops/validate_codex_closeout.py --task TASK-4102
    closeout:
      registry_updated: true
      doc_registry_updated: true
      validators_passed: true
      artifact_manifest_exists: true
      forbidden_paths_clean: true
      status: CLOSED

  - task_id: TASK-4103
    title: L5 Policy Action Validator Hardening
    status: DONE
    priority: P0
    task_type: OPS_GOVERNANCE
    profile: L5_POLICY_ACTION
    owner: codex
    branch: null
    created_at: "2026-06-29"
    updated_at: "2026-06-29"
    objective:
      - add config-driven L5 policy action profile validation
      - preserve review-only and no broker/live order boundaries
    allowed_paths:
      - ops/**
      - scripts/ops/**
      - docs/generated_context/**
      - docs/reports/task_4103_l5_policy_action_validator_hardening/**
    forbidden_paths:
      - broker/**
      - live_trading/**
      - production_orders/**
      - secrets/**
      - configs/broker/**
      - src/**/order_execution/**
      - src/**/broker/**
      - src/**/strategy_live/**
      - data/**
      - db/**
    required_artifacts:
      - docs/reports/task_4103_l5_policy_action_validator_hardening/report.md
      - docs/reports/task_4103_l5_policy_action_validator_hardening/artifact_manifest.csv
      - docs/reports/task_4103_l5_policy_action_validator_hardening/validation_results.md
    required_validators:
      - python scripts/ops/validate_task_registry.py
      - python scripts/ops/validate_doc_registry.py --soft
      - python scripts/ops/validate_context_bundle.py --task TASK-4103
      - python scripts/ops/validate_task_profile_rules.py --profile L5_POLICY_ACTION
      - python scripts/ops/validate_task_scope.py --task TASK-4103
      - python scripts/ops/validate_required_artifacts.py --task TASK-4103
      - python scripts/ops/validate_codex_closeout.py --task TASK-4103
    closeout:
      registry_updated: true
      doc_registry_updated: true
      validators_passed: true
      artifact_manifest_exists: true
      forbidden_paths_clean: true
      status: CLOSED

  - task_id: TASK-4104
    title: Mission Control Dashboard v1
    status: DONE
    priority: P1
    task_type: OPS_GOVERNANCE
    profile: DOCS_GOVERNANCE
    owner: codex
    branch: null
    created_at: "2026-06-29"
    updated_at: "2026-06-29"
    objective:
      - improve read-only static dashboard summary
      - add dashboard validation
      - emit machine-readable dashboard summary
    allowed_paths:
      - ops/**
      - scripts/ops/**
      - docs/generated_context/**
      - docs/reports/task_4104_mission_control_dashboard_v1/**
    forbidden_paths:
      - broker/**
      - live_trading/**
      - production_orders/**
      - secrets/**
      - configs/broker/**
      - src/**/order_execution/**
      - src/**/broker/**
      - src/**/strategy_live/**
      - data/**
      - db/**
    required_artifacts:
      - docs/reports/task_4104_mission_control_dashboard_v1/report.md
      - docs/reports/task_4104_mission_control_dashboard_v1/artifact_manifest.csv
      - docs/reports/task_4104_mission_control_dashboard_v1/validation_results.md
    required_validators:
      - python scripts/ops/validate_task_registry.py
      - python scripts/ops/validate_doc_registry.py --soft
      - python scripts/ops/validate_context_bundle.py --task TASK-4104
      - python scripts/ops/validate_dashboard.py
      - python scripts/ops/validate_task_scope.py --task TASK-4104
      - python scripts/ops/validate_required_artifacts.py --task TASK-4104
      - python scripts/ops/validate_codex_closeout.py --task TASK-4104
    closeout:
      registry_updated: true
      doc_registry_updated: true
      validators_passed: true
      artifact_manifest_exists: true
      forbidden_paths_clean: true
      status: CLOSED

  - task_id: TASK-4105
    title: Prompt Regression Eval
    status: DONE
    priority: P1
    task_type: OPS_GOVERNANCE
    profile: DOCS_GOVERNANCE
    owner: codex
    branch: null
    created_at: "2026-06-29"
    updated_at: "2026-06-29"
    objective:
      - add lightweight prompt regression checks without heavy dependencies
      - protect core Codex safety and closeout prompts
    allowed_paths:
      - AGENTS.md
      - .codex/**
      - ops/**
      - scripts/ops/**
      - docs/generated_context/**
      - docs/reports/task_4105_prompt_regression_eval/**
    forbidden_paths:
      - broker/**
      - live_trading/**
      - production_orders/**
      - secrets/**
      - configs/broker/**
      - src/**/order_execution/**
      - src/**/broker/**
      - src/**/strategy_live/**
      - data/**
      - db/**
    required_artifacts:
      - docs/reports/task_4105_prompt_regression_eval/report.md
      - docs/reports/task_4105_prompt_regression_eval/artifact_manifest.csv
      - docs/reports/task_4105_prompt_regression_eval/validation_results.md
    required_validators:
      - python scripts/ops/validate_task_registry.py
      - python scripts/ops/validate_doc_registry.py --soft
      - python scripts/ops/validate_context_bundle.py --task TASK-4105
      - python scripts/ops/validate_prompt_regression.py
      - python scripts/ops/validate_task_scope.py --task TASK-4105
      - python scripts/ops/validate_required_artifacts.py --task TASK-4105
      - python scripts/ops/validate_codex_closeout.py --task TASK-4105
    closeout:
      registry_updated: true
      doc_registry_updated: true
      validators_passed: true
      artifact_manifest_exists: true
      forbidden_paths_clean: true
      status: CLOSED

```

---

## File: scripts/ops/render_ops_dashboard.py

```py
from __future__ import annotations

import csv
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

from ops_common import ROOT, doc_registry, load_yaml, rel, write_text


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def table(headers: list[str], rows: list[list[object]]) -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def link(path: str) -> str:
    return f'<a href="../../{esc(path)}">{esc(path)}</a>'


def validation_summaries() -> list[list[str]]:
    rows: list[list[str]] = []
    for path in sorted((ROOT / "docs" / "reports").glob("task_*/validation_results.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        result = "UNKNOWN"
        if "FAIL" in text:
            result = "HAS_FAIL"
        elif "PASS_WITH_WARNINGS" in text:
            result = "PASS_WITH_WARNINGS"
        elif "PASS" in text:
            result = "PASS"
        rows.append([rel(path), result])
    return rows


def context_usage() -> list[list[str]]:
    rows: list[list[str]] = []
    for manifest in sorted((ROOT / "docs" / "generated_context").glob("*_manifest.csv")):
        token_sum = 0
        file_count = 0
        with manifest.open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                file_count += 1
                try:
                    token_sum += int(row.get("tokens") or 0)
                except ValueError:
                    pass
        rows.append([rel(manifest), file_count, token_sum])
    return rows


def main() -> int:
    try:
        tasks = load_yaml("ops/task_registry.yaml").get("tasks", [])
        docs = doc_registry().get("documents", [])
        operating = load_yaml("ops/operating_state.yaml")
    except Exception as exc:
        print(f"FAIL {exc}")
        return 1

    active = [t for t in tasks if t.get("status") == "IN_PROGRESS"]
    blocked = [t for t in tasks if t.get("status") == "BLOCKED"]
    review = [t for t in tasks if t.get("status") == "REVIEW"]
    done = [t for t in tasks if t.get("status") == "DONE"][-10:]
    doc_counts = Counter(d.get("status", "UNKNOWN") for d in docs)
    hard = operating.get("hard_boundaries", {})

    task_rows = [
        [
            t.get("task_id"),
            t.get("title"),
            t.get("status"),
            t.get("priority"),
            t.get("profile"),
            t.get("closeout", {}).get("status"),
            t.get("updated_at"),
        ]
        for t in tasks
    ]
    validator_rows = [
        [t.get("task_id"), validator]
        for t in tasks
        for validator in t.get("required_validators", [])
    ]
    artifact_rows = [
        [t.get("task_id"), artifact]
        for t in tasks
        for artifact in t.get("required_artifacts", [])
    ]

    summary = {
        "project": operating.get("project", {}),
        "task_counts": Counter(t.get("status", "UNKNOWN") for t in tasks),
        "document_counts": doc_counts,
        "hard_boundaries": hard,
    }
    summary_path = ROOT / "ops" / "dashboard" / "dashboard_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Codex Ops Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Arial, sans-serif;
      background: #f6f7f9;
      color: #17202a;
    }}
    body {{ margin: 0; }}
    header {{ background: #17202a; color: white; padding: 24px 32px; }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    section {{ margin: 0 0 28px; }}
    h1 {{ margin: 0; font-size: 28px; }}
    h2 {{ font-size: 18px; margin: 0 0 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .metric {{ background: white; border: 1px solid #d7dce2; border-radius: 6px; padding: 14px; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #d7dce2; }}
    th, td {{ padding: 8px 10px; border-bottom: 1px solid #e6e9ed; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ background: #edf1f5; font-weight: 700; }}
    a {{ color: #0b5cad; }}
    code {{ font-family: Consolas, monospace; }}
  </style>
</head>
<body>
  <header>
    <h1>Codex Ops Dashboard</h1>
    <p>{esc(operating.get('project', {}).get('identity'))} / read-only static dashboard</p>
  </header>
  <main>
    <section>
      <h2>Operating State</h2>
      <div class="grid">
        <div class="metric">Project<strong>{esc(operating.get('project', {}).get('name'))}</strong></div>
        <div class="metric">Identity<strong>{esc(operating.get('project', {}).get('identity'))}</strong></div>
        <div class="metric">Updated<strong>{esc(operating.get('project', {}).get('updated_at'))}</strong></div>
        <div class="metric">Tasks<strong>{esc(len(tasks))}</strong></div>
        <div class="metric">Documents<strong>{esc(len(docs))}</strong></div>
      </div>
    </section>
    <section><h2>Active Tasks</h2>{table(['Task', 'Title', 'Priority', 'Profile'], [[t.get('task_id'), t.get('title'), t.get('priority'), t.get('profile')] for t in active])}</section>
    <section><h2>Blocked Tasks</h2>{table(['Task', 'Title', 'Priority', 'Profile'], [[t.get('task_id'), t.get('title'), t.get('priority'), t.get('profile')] for t in blocked])}</section>
    <section><h2>Review Tasks</h2>{table(['Task', 'Title', 'Priority', 'Profile'], [[t.get('task_id'), t.get('title'), t.get('priority'), t.get('profile')] for t in review])}</section>
    <section><h2>Recently Done Tasks</h2>{table(['Task', 'Title', 'Priority', 'Profile'], [[t.get('task_id'), t.get('title'), t.get('priority'), t.get('profile')] for t in done])}</section>
    <section><h2>Task Detail Table</h2>{table(['Task', 'Title', 'Status', 'Priority', 'Profile', 'Closeout', 'Updated'], task_rows)}</section>
    <section><h2>Required Validators</h2>{table(['Task', 'Validator'], validator_rows)}</section>
    <section><h2>Artifact Links</h2>{table(['Task', 'Artifact'], [[task, link(path)] for task, path in artifact_rows])}</section>
    <section><h2>Document Status Summary</h2>{table(['Status', 'Count'], [[k, v] for k, v in sorted(doc_counts.items())])}</section>
    <section><h2>Context Bundle Token Usage</h2>{table(['Manifest', 'Files', 'Tokens'], context_usage())}</section>
    <section><h2>Validation Reports</h2>{table(['Report', 'Result'], validation_summaries())}</section>
    <section><h2>Hard Boundaries</h2>{table(['Boundary', 'State'], [[k, v] for k, v in hard.items()])}</section>
  </main>
</body>
</html>
"""
    output = ROOT / "ops" / "dashboard" / "index.html"
    write_text(output, html_doc)
    print(f"PASS dashboard: {rel(output)}")
    print(f"PASS dashboard_summary: {rel(summary_path)}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

```

---

## File: scripts/ops/validate_dashboard.py

```py
from __future__ import annotations

import argparse
import re
import sys

from ops_common import ROOT, print_result


REQUIRED_SECTIONS = [
    "Operating State",
    "Active Tasks",
    "Blocked Tasks",
    "Review Tasks",
    "Recently Done Tasks",
    "Task Detail Table",
    "Required Validators",
    "Artifact Links",
    "Document Status Summary",
    "Context Bundle Token Usage",
    "Hard Boundaries",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="ops/dashboard/index.html")
    args = parser.parse_args()

    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    path = ROOT / args.path
    if not path.exists():
        return print_result("DASHBOARD VALIDATION", [], [], [f"dashboard missing: {args.path}"])
    text = path.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            failures.append(f"missing section: {section}")
        else:
            passes.append(f"section: {section}")
    if re.search(r"https?://|<script\s+src=|<link\s+[^>]*href=[\"']https?", text, re.IGNORECASE):
        failures.append("network dependency detected")
    else:
        passes.append("no_network_dependency")
    if "<form" in text.lower() or "contenteditable" in text.lower():
        failures.append("editable control detected")
    else:
        passes.append("read_only_static")
    return print_result("DASHBOARD VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())

```
