# Codex Context Bundle

Task: TASK-4101
Profile: UI_STORYBOOK_VISION
Generated At: 2026-06-29T02:28:55+00:00
Token Count: 5300
Token Count Mode: approximate
Max Tokens: 24000

---

## Included Files

| Path | Bytes | Tokens | Reason |
|---|---:|---:|---|
| AGENTS.md | 1380 | 345 | must_include |
| docs/frontend_app_ssot/00_PROJECT_SSOT.md | 1604 | 401 | must_include |
| docs/frontend_app_ssot/07_COMPONENT_CATALOG.md | 986 | 246 | must_include |
| docs/frontend_app_ssot/11_STORYBOOK_AND_QA_PLAN.md | 788 | 197 | must_include |
| docs/frontend_app_ssot/12_SCREENSHOT_QA_PREFLIGHT_PLAN.md | 5160 | 1290 | must_include |
| ops/context_bundles.yaml | 4857 | 1214 | must_include |
| ops/profile_validation_rules.yaml | 2054 | 513 | must_include |
| ops/task_profiles.yaml | 4379 | 1094 | must_include |

---

## Excluded Files

| Pattern/Path | Reason |
|---|---|
| docs/archive/** | configured exclude |
| docs/reports/** | configured exclude |
| node_modules/** | configured exclude |
| data/** | configured exclude |
| db/** | configured exclude |
| docs/reports/task_4101_context_bundle_hardening/report.md | matched exclude pattern |

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

## File: docs/frontend_app_ssot/00_PROJECT_SSOT.md

```md
# Frontend App SSOT

## Authority

This pack is the current frontend/app planning authority for future implementation work.
It does not grant strategy acceptance, paper permission, deployment readiness, broker mutation, live order permission, or real-capital permission.

Standing project status:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`
- Frontend mode: read-only L7 observation surface

## Active Target

The active frontend target is an Expo Development Build, iOS-first mobile app.

The near-term operator preview target is mobile-web-first phone preview because
the project currently has no paid Apple Developer Program and no Mac operator
path. This does not replace the later native iOS app path; it only defines the
current phone-visible implementation route.

The app must preserve:

- `decision -> reason/thesis -> evidence -> source`
- explicit source freshness
- blockers and missing evidence
- provenance for decision-support content
- read-only controls unless a future operating-state document changes permission

## Supersession

The prior React plus TypeScript web architecture pack is retained as design input only.
It is not the active implementation stack.

The prior Expo Go 3052 DOM cockpit is retained as historical UI evidence and migration reference only.
It is not the final route authority.

The mobile web preview path is governed by `23_MOBILE_WEB_PWA_BOUNDARY.md`.

Backtest, paper, and live are lifecycle states. They are not top-level navigation tabs.

```

---

## File: docs/frontend_app_ssot/07_COMPONENT_CATALOG.md

```md
# Component Catalog

## Required Component Families

| Component | Purpose |
| --- | --- |
| `DecisionHeader` | decision state, authority, timestamp, gate status |
| `SourceFreshnessBadge` | fresh/stale/missing/source-not-attached display |
| `BlockerList` | blockers and unknown states |
| `EvidenceList` | source-backed observations with provenance |
| `ValidationReadinessPanel` | split/OOS, leakage, cost/slippage, source gate state |
| `RiskPanel` | exposure, stale source, kill-switch, control-state evidence |
| `DisabledActionBar` | disabled approve/reject/cancel/execute affordances with governance reason |
| `ProvenanceLink` | source or artifact pointer |
| `ChartWithSourceState` | chart plus source attachment/freshness status |
| `LifecycleStatePill` | candidate/paper/live/shadow lifecycle display only |

## Storybook Minimum

Each component must have stories for:

- fresh source
- stale source
- missing source
- blocked state
- unknown state
- disabled action state


```

---

## File: docs/frontend_app_ssot/11_STORYBOOK_AND_QA_PLAN.md

```md
# Storybook And QA Plan

## Storybook Coverage

Storybook must cover:

- five top-level IA tabs
- universal detail frame V2
- source freshness badges
- blocker states
- disabled action controls
- chart missing/source not attached states
- governance status panels

## Screenshot QA

Screenshot QA must capture:

- `HOME`
- `BRAIN`
- candidate detail
- `PORTFOLIO`
- position detail
- `ORDERS`
- order detail
- `SYSTEM`
- stale source state
- disabled action state

## Validator Targets

Frontend validation should include:

- no live order text or handlers that imply permission
- no broker mutation controls with active handlers
- no synthetic chart fallback for source-required charts
- required freshness and provenance fields visible
- backtest/paper/live not used as top-level tabs


```

---

## File: docs/frontend_app_ssot/12_SCREENSHOT_QA_PREFLIGHT_PLAN.md

```md
# Screenshot QA Preflight Plan

## Purpose

Define the future visual QA evidence contract before product screens are implemented.

This is a preflight plan only. It does not install screenshot tooling, run captures, implement screens, or prove UI quality.

## Current Status

- Screenshot QA remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- Current frontend fixtures are scaffold-only and `NOT_AUTHORITY`.
- No product screen, Candidate Detail screen, DB connection, runtime API connection, broker connection, paper/live path, deployment readiness, or real-capital path is authorized by this document.

## Non-Authorization Rule

Screenshot QA evidence can show what is visible. It must not be treated as strategy acceptance, deployment readiness, paper readiness, live readiness, broker readiness, source truth, backend truth, broker truth, order execution permission, or real-capital permission.

## Target Surfaces

| Surface ID | Surface | Current Status | Required State Coverage |
| --- | --- | --- | --- |
| SS-001 | Home | future required | normal, stale source, blocked |
| SS-002 | Brain Overview | future required | normal, missing source, unknown |
| SS-003 | Candidate Detail | future required | decision summary, evidence, disabled action |
| SS-004 | Portfolio Overview | future required | normal, stale or missing source |
| SS-005 | Position Detail | future required | position verdict, risk, source state |
| SS-006 | Orders Overview | future required | read-only order states |
| SS-007 | Order Detail | future required | disabled approve/reject/cancel |
| SS-008 | System Overview | future required | system health, blockers |
| SS-009 | Stale Source State | required special state | stale visible above fold |
| SS-010 | Disabled Action State | required special state | disabled reason plus governance change visible |

## Device / Browser Matrix

Required baseline:

| Axis | Required Value |
| --- | --- |
| Device | iPhone 15 Pro |
| Theme | Light |
| Scale | 100% |
| Orientation | Portrait |

Future optional matrix:

| Tier | Target |
| --- | --- |
| P0 | iPhone 15 Pro, Light, Portrait |
| P1 | iPhone SE width stress, Light, Portrait |
| P1 | iPhone 15 Pro Max, Light, Portrait |
| P2 | Dark theme, only after theme support is explicitly selected |
| P2 | Android, only after iOS-first baseline is stable |

## State Matrix

| State | Required Visual Evidence |
| --- | --- |
| `fresh` | source freshness visible |
| `stale` | stale badge/warning visible |
| `missing` | missing source visible, not hidden |
| `unknown` | unknown state visible as blocker/unknown |
| `blocked` | blocker reason visible |
| `disabled_action` | disabled action plus reason and required governance change visible |
| `chart_missing` | chart unavailable state visible |
| `source_not_attached` | source-not-attached visible |
| `read_only` | no active trading action affordance |
| `safety_boundary` | `NOT_ACCEPTED` / `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` / `FORBIDDEN` visible where relevant |

## Artifact Naming Policy

Future screenshot files must use deterministic names:

`` `text
<surface_id>__<surface_slug>__<state>__<device>__<theme>__<orientation>__<yyyymmdd>.png
`` `

Example:

`` `text
SS-003__candidate-detail__disabled-action__iphone-15-pro__light__portrait__20260622.png
`` `

## Storage Locations

| Artifact Type | Path |
| --- | --- |
| Preflight plan | `docs/frontend_app_ssot/12_SCREENSHOT_QA_PREFLIGHT_PLAN.md` |
| Future screenshot outputs | `docs/reports/task_<id>_screenshot_qa_run/screenshots/` |
| Screenshot manifest | `docs/reports/task_<id>_screenshot_qa_run/screenshot_manifest.csv` |
| Vision review notes | `docs/reports/task_<id>_screenshot_qa_run/vision_review.md` |

## Future Run Manifest Fields

`screenshot_id,surface_id,surface_name,route_or_story,state,fixture_or_source_artifact,device,theme,orientation,scale,captured_at,capture_command,pass_fail,failure_reason,reviewer,notes`

## Acceptance Criteria

Future screenshot QA can pass only if:

1. Required surfaces are captured or explicitly blocked with reason.
2. Device preset matches iPhone 15 Pro / Light / 100% / Portrait.
3. Stale/missing/unknown/source-not-attached states are visible.
4. Disabled actions show `actionState = disabled`, `disabledReason`, `requiredGovernanceChange`, and current hard boundary.
5. No active BUY/SELL/EXECUTE/LIVE/PLACE ORDER affordance appears.
6. Charts do not silently use synthetic source-free fallback.
7. Every image maps to surface, state, fixture/source, device, date, and pass/fail.
8. Missing/stale remains `UNKNOWN/BLOCKER`.

## Failure Criteria

Screenshot QA must fail or block if required surfaces are unavailable without explicit blocker evidence, forbidden active trading affordances appear, source-free charts are treated as evidence, stale/missing/unknown states are hidden, or screenshots are used to imply trading/deployment readiness.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, DB/runtime connection, or product screen implementation is authorized.

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

## File: ops/profile_validation_rules.yaml

```yaml
version: 1
updated_at: "2026-06-29"

rules:
  L4_THESIS_BUNDLE:
    must_include:
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
    hard_boundaries:
      strategy_status: NOT_ACCEPTED
      deployment_status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
      real_capital: FORBIDDEN
      live_order: FORBIDDEN

  L5_POLICY_ACTION:
    must_include:
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
    hard_boundaries:
      strategy_status: NOT_ACCEPTED
      deployment_status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
      real_capital: FORBIDDEN
      broker_mutation: FORBIDDEN
      live_order: FORBIDDEN

  UI_STORYBOOK_VISION:
    must_include:
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
    hard_boundaries:
      live_order: FORBIDDEN
      broker_mutation: FORBIDDEN

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
