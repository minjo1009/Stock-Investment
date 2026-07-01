# Codex Context Bundle

Task: TASK-4100
Profile: DOCS_GOVERNANCE
Generated At: 2026-06-29T02:15:29+00:00
Token Count: 4908
Token Count Mode: approximate
Max Tokens: 22000

---

## Included Files

| Path | Bytes | Tokens | Reason |
|---|---:|---:|---|
| AGENTS.md | 1380 | 345 | must_include |
| docs/reports/task_4100_codex_governance_bootstrap/report.md | 3243 | 810 | optional_include |
| ops/context_bundles.yaml | 1695 | 423 | must_include |
| ops/doc_registry.yaml | 6474 | 1618 | must_include |
| ops/operating_state.yaml | 604 | 151 | must_include |
| ops/task_profiles.yaml | 4379 | 1094 | must_include |
| ops/task_registry.yaml | 1870 | 467 | must_include |

---

## Excluded Files

| Pattern/Path | Reason |
|---|---|
| node_modules/** | configured exclude |
| .git/** | configured exclude |
| data/** | configured exclude |
| db/** | configured exclude |
| secrets/** | configured exclude |
| screenshots/** | configured exclude |
| docs/archive/** | configured exclude |

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

## File: docs/reports/task_4100_codex_governance_bootstrap/report.md

```md
# TASK-4100 Codex Governance / Task Operating System Bootstrap

## Goal

Create a repo-level operating layer that limits Codex sprawl, reduces irrelevant context loading, enforces task profiles, and exposes a read-only local dashboard for current Codex work.

## Implemented Files

- `AGENTS.md`
- `ops/*.yaml`
- `.codex/skills/*/SKILL.md`
- `scripts/ops/*.py`
- `docs/generated_context/README.md`
- `ops/dashboard/index.html`
- `docs/reports/task_4100_codex_governance_bootstrap/*`

## Governance Model

TASK-4100 introduces task and document registries, durable operating state, task profiles, context bundle configuration, validators, and a static dashboard. The model keeps trading safety boundaries explicit and makes task closeout depend on registries, artifacts, validators, and scope checks.

## Task Registry Summary

`ops/task_registry.yaml` defines `TASK-4100`, status enums, priority enums, allowed paths, forbidden paths, required artifacts, required validators, and closeout fields.

## Doc Registry Summary

`ops/doc_registry.yaml` registers the new governance documents, task artifacts, and Codex skill documents. Historical repository markdown is intentionally not migrated in this bootstrap and is reported through soft-mode warnings.

## Task Profiles Summary

`ops/task_profiles.yaml` defines `DOCS_GOVERNANCE`, L0-L6 profiles, `UI_STORYBOOK_VISION`, and `TASK_CLOSEOUT`, including required principles, forbidden intents, and checks.

## Context Bundle Summary

`ops/context_bundles.yaml` defines `TASK_4100` plus starter bundles for UI, L4, and L5 work. `build_context_bundle.py` creates deterministic markdown and CSV outputs under `docs/generated_context/`.

## Dashboard Summary

`scripts/ops/render_ops_dashboard.py` generates a read-only static dashboard at `ops/dashboard/index.html` with operating state, task status, validators, artifacts, document status, context token usage, validation reports, and hard boundaries.

## Validators

Validators cover task registry integrity, document registry integrity, context bundles, task scope, required artifacts, and closeout.

## Hard Boundaries Preserved

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains `FORBIDDEN`.
- Live order remains `FORBIDDEN`.
- Paper promotion remains `FORBIDDEN_UNLESS_EXPLICITLY_ACCEPTED`.
- Missing or stale data remains `UNKNOWN_OR_BLOCKER`.

## What This Does Not Do

This task does not implement trading logic, UI screens, broker integration, order execution, DB schema changes, scheduler registration, strategy acceptance, paper promotion, or live trading behavior.

## Known Limitations

- Historical markdown files are not fully registered; `validate_doc_registry.py --soft` reports them as warnings.
- Context token counting falls back to an approximate count when `tiktoken` is not installed.
- Scope validation uses the task artifact manifest as the hard gate when the repo already has unrelated dirty files.

## Next Recommended Tasks

1. TASK-4101 Context Bundle hardening for UI work
2. TASK-4102 L4 profile validator hardening
3. TASK-4103 L5 policy action validator hardening
4. TASK-4104 Mission Control Dashboard v1

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
      - docs/product_mission_v1.md
      - docs/frontend_app_ssot/**
    exclude:
      - docs/archive/**
      - docs/reports/**
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

```
