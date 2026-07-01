# Codex Context Bundle

Task: TASK-4103
Profile: L5_POLICY_ACTION
Generated At: 2026-06-29T02:28:30+00:00
Token Count: 2387
Token Count Mode: approximate
Max Tokens: 22000

---

## Included Files

| Path | Bytes | Tokens | Reason |
|---|---:|---:|---|
| .codex/skills/l5-policy-action/SKILL.md | 644 | 161 | must_include |
| AGENTS.md | 1380 | 345 | must_include |
| docs/reports/task_4103_l5_policy_action_validator_hardening/report.md | 1096 | 274 | optional_include |
| ops/profile_validation_rules.yaml | 2054 | 513 | must_include |
| ops/task_profiles.yaml | 4379 | 1094 | must_include |

---

## Excluded Files

| Pattern/Path | Reason |
|---|---|
| docs/archive/** | configured exclude |
| node_modules/** | configured exclude |
| data/** | configured exclude |
| db/** | configured exclude |

---

## File: .codex/skills/l5-policy-action/SKILL.md

```md
# L5 Policy Action Skill

Use this skill to translate thesis state into review-only policy actions without broker or execution mutation.

Profile:
- `L5_POLICY_ACTION` in `ops/task_profiles.yaml`

Hard forbidden actions:
- no broker mutation
- no live order
- no real capital
- no auto approval
- no order execution
- Candidate must not convert directly to Buy

Required checks:
- policy action schema
- no broker mutation
- no live order

Required validators:
- `python scripts/ops/validate_task_registry.py`
- `python scripts/ops/validate_task_scope.py --task <TASK_ID>`
- `python scripts/ops/validate_required_artifacts.py --task <TASK_ID>`

```

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

## File: docs/reports/task_4103_l5_policy_action_validator_hardening/report.md

```md
# TASK-4103 L5 Policy Action Validator Hardening

## Decision Summary

- Verdict: PASS
- Strategy acceptance status: `NOT_ACCEPTED`
- Key metrics: L5 policy action profile rule validator added and passing
- What changed: L5 review-only, sizing/order separation, and no broker/live/real-capital rules are now mechanically checked
- Next action: Add schema validation for actual L5 policy action artifacts in a future task

## Quant Expert Report

- Data source and source readiness: Not applicable; governance tooling only
- Exact join keys: Not applicable
- Leakage audit: No labels, outcomes, or trading assignment logic used
- Split/OOS metrics: Not applicable
- Failure decomposition: L5 profile was readable but not mechanically checked
- Cost/slippage stress where PnL changed: Not applicable
- Remaining blockers: This does not validate runtime policy action payloads

## No-Background Decision-Maker Report

TASK-4103 protects the Candidate lifecycle and review-only boundary. It does not create order execution or paper/live promotion.

## Artifact Manifest

See `artifact_manifest.csv`.

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
