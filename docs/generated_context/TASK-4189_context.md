# Codex Context Bundle

Task: TASK-4189
Profile: DOCS_GOVERNANCE
Generated At: 2026-07-01T15:03:33+00:00
Token Count: 9267
Token Count Mode: approximate
Max Tokens: 24000

---

## Included Files

| Path | Bytes | Tokens | Reason |
|---|---:|---:|---|
| AGENTS.md | 1380 | 345 | must_include |
| docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/cleanup_summary.json | 515 | 124 | optional_include |
| docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/docs_surface_inventory.csv | 1562 | 384 | optional_include |
| docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/duplicate_axis_review.csv | 660 | 163 | optional_include |
| docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/report.md | 78 | 19 | must_include |
| ops/context_bundles.yaml | 6374 | 1593 | must_include |
| ops/operating_state.yaml | 604 | 151 | must_include |
| ops/project_hygiene_policy.yaml | 4796 | 1199 | must_include |
| ops/project_structure_policy.yaml | 4088 | 1022 | must_include |
| ops/task_profiles.yaml | 4379 | 1094 | must_include |
| scripts/ops/validate_codex_closeout.py | 2705 | 676 | must_include |
| scripts/ops/validate_project_hygiene.py | 6218 | 1554 | must_include |
| scripts/ops/validate_project_structure_policy.py | 3773 | 943 | must_include |

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

## File: docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/cleanup_summary.json

```json
{
  "task_id": "TASK-4189",
  "generated_at": "2026-07-01T14:54:48+00:00",
  "root_entries": 28,
  "docs_surfaces": 23,
  "stale_report_candidates_limited": 0,
  "duplicate_axes": 4,
  "automated_deletions": 1,
  "deletion_status": "DELETED",
  "hard_boundaries": {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
    "broker_mutation": "FORBIDDEN",
    "live_order": "FORBIDDEN",
    "paper_promotion": "FORBIDDEN"
  }
}

```

---

## File: docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/docs_surface_inventory.csv

```csv
path,classification,last_write_utc,decision
docs/acceptance,DOCS_SURFACE_REVIEW,2026-06-03T10:31:28+00:00,REVIEW
docs/active,DOCS_SURFACE_REVIEW,2026-06-27T13:40:57+00:00,REVIEW
docs/architecture,ARCHITECTURE,2026-06-29T06:36:13+00:00,KEEP
docs/archive,ARCHIVE,2026-06-27T15:35:09+00:00,KEEP
docs/audits,DOCS_SURFACE_REVIEW,2026-06-29T03:49:09+00:00,REVIEW
docs/candidate_funnel,DOCS_SURFACE_REVIEW,2026-06-29T03:49:09+00:00,REVIEW
docs/context,DOCS_SURFACE_REVIEW,2026-05-20T13:46:00+00:00,REVIEW
docs/contracts,DOCS_SURFACE_REVIEW,2026-06-24T12:39:04+00:00,REVIEW
docs/db,DOCS_SURFACE_REVIEW,2026-06-20T16:20:49+00:00,REVIEW
docs/execution,DOCS_SURFACE_REVIEW,2026-06-03T11:34:21+00:00,REVIEW
docs/frontend_app_ssot,FRONTEND_SSOT,2026-06-24T10:01:41+00:00,KEEP
docs/frontend_ios,DOCS_SURFACE_REVIEW,2026-06-29T03:49:09+00:00,REVIEW
docs/frontend_web,DOCS_SURFACE_REVIEW,2026-06-23T10:58:49+00:00,REVIEW
docs/generated_context,GENERATED_CONTEXT,2026-07-01T14:46:52+00:00,KEEP
docs/graphify,DISCOVERY_AID_REVIEW,2026-06-29T03:49:09+00:00,REVIEW
docs/harness,HARNESS_DOCS_REVIEW,2026-07-01T12:01:44+00:00,REVIEW
docs/llm_wiki,ROUTING_MEMORY,2026-06-22T14:23:19+00:00,KEEP
docs/logs,DOCS_SURFACE_REVIEW,2026-04-24T11:59:09+00:00,REVIEW
docs/obsidian,HUMAN_COCKPIT,2026-06-29T05:55:26+00:00,KEEP
docs/operating_system,OPERATING_DOCS,2026-06-29T05:55:26+00:00,KEEP
docs/ownership,OWNERSHIP,2026-06-29T05:55:26+00:00,KEEP
docs/reports,TASK_REPORTS,2026-07-01T14:53:04+00:00,KEEP
docs/specs,DOCS_SURFACE_REVIEW,2026-04-24T11:59:16+00:00,REVIEW

```

---

## File: docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/duplicate_axis_review.csv

```csv
left_path,right_path,issue,left_exists,right_exists,decision,recommendation
config,configs,config/configs duplicate root axis,true,true,REVIEW_MERGE_OR_ARCHIVE,configs should remain canonical until imports prove otherwise
apps,frontend,apps/frontend duplicate app root axis,true,true,REVIEW_MERGE_OR_ARCHIVE,apps likely canonical for mobile; frontend needs owner review
.obsidian,docs/obsidian,obsidian local/app cockpit split,true,true,REVIEW_MERGE_OR_ARCHIVE,.obsidian is local app state; docs/obsidian is repo cockpit
tasks,ops/task_registry.yaml,legacy tasks directory vs registry,true,true,REVIEW_MERGE_OR_ARCHIVE,ops/task_registry.yaml is canonical

```

---

## File: docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/report.md

```md
# TASK-4189 Project Structure Cleanup and GPT Pro Review

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

  TASK_4189:
    task_id: TASK-4189
    profile: DOCS_GOVERNANCE
    max_tokens: 24000
    must_include:
      - AGENTS.md
      - ops/operating_state.yaml
      - ops/task_profiles.yaml
      - ops/context_bundles.yaml
      - ops/project_hygiene_policy.yaml
      - ops/project_structure_policy.yaml
      - scripts/ops/validate_project_hygiene.py
      - scripts/ops/validate_project_structure_policy.py
      - scripts/ops/validate_codex_closeout.py
      - docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/report.md
    optional_include:
      - docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/cleanup_summary.json
      - docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/duplicate_axis_review.csv
      - docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/docs_surface_inventory.csv
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
    presence: optional
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

## File: ops/project_structure_policy.yaml

```yaml
version: 1
updated_at: "2026-07-01"
created_by_task: TASK-4189

purpose:
  - define durable repository structure
  - keep root axes non-overlapping
  - classify docs surfaces by authority and lifecycle
  - define delete/archive/local-trash rules before physical cleanup

target_root:
  keep:
    - AGENTS.md
    - README.md
    - apps
    - configs
    - data
    - docs
    - ops
    - prompts
    - schemas
    - scripts
    - src
    - tests
    - tools
  local_only:
    - .codex
    - .dvc
    - .obsidian
    - logs
  sensitive_local_only:
    - .env
    - .kis_token_cache.json
  review_before_move_or_delete:
    - config
    - frontend
    - tasks
    - trading.db
    - trading-DESKTOP-2R00TB4.db

layer_tree:
  L0_L1_DATA_PIPELINE:
    code:
      - src/data
      - tools/db/source_acquisition
    automation:
      - scripts/run_l0_*
      - scripts/validate_l0_*
      - scripts/run_l1_*
      - scripts/validate_l1_*
    artifacts:
      - data/artifacts/task_*
    reports:
      - docs/reports/task_*
  L2_INTERPRETATION:
    code:
      - src/l2
    automation:
      - scripts/run_l2_*
      - scripts/validate_l2_*
  L3_L4_BRAIN:
    code:
      - src/brain
    automation:
      - scripts/build_l3_*
      - scripts/validate_l3_*
      - scripts/build_l4_*
      - scripts/validate_l4_*
  UI:
    code:
      - apps/ios-trader-brain
    ssot:
      - docs/frontend_app_ssot
  OPS_GOVERNANCE:
    code:
      - scripts/ops
    policy:
      - ops
    context:
      - docs/generated_context
    reports:
      - docs/reports/task_*

duplicate_axis_decisions:
  - axis: config_vs_configs
    canonical: configs
    noncanonical: config
    current_action: REVIEW_IMPORTS_BEFORE_MOVE
    target_action: archive_or_delete_if_no_references
  - axis: apps_vs_frontend
    canonical: apps
    noncanonical: frontend
    current_action: REVIEW_APP_OWNERSHIP_BEFORE_MOVE
    target_action: migrate_or_archive_frontend_after_catalog
  - axis: obsidian_local_vs_repo
    canonical: docs/obsidian
    local_state: .obsidian
    current_action: KEEP_SPLIT
    target_action: keep_.obsidian_local_and_docs_obsidian_repo_cockpit
  - axis: tasks_vs_registry
    canonical: ops/task_registry.yaml
    noncanonical: tasks
    current_action: REVIEW_LEGACY_TASKS_BEFORE_ARCHIVE
    target_action: migrate_index_then_archive_or_delete_legacy_tasks

docs_surface_policy:
  keep_canonical:
    - docs/architecture
    - docs/frontend_app_ssot
    - docs/generated_context
    - docs/llm_wiki
    - docs/obsidian
    - docs/operating_system
    - docs/ownership
    - docs/reports
  review_surfaces:
    - docs/acceptance
    - docs/active
    - docs/audits
    - docs/candidate_funnel
    - docs/context
    - docs/contracts
    - docs/db
    - docs/execution
    - docs/frontend_ios
    - docs/frontend_web
    - docs/graphify
    - docs/harness
    - docs/logs
    - docs/specs
  archive_rule:
    docs_only_archive_root: docs/archive
    archive_requires:
      - task_id
      - artifact_manifest_row
      - doc_registry_update
      - source_path
      - reason
  delete_rule:
    allowed_without_owner_review:
      - transient caches
      - generated build caches
      - empty temp folders
    owner_review_required:
      - task reports
      - docs surfaces
      - DB files
      - source data
      - source code
      - scripts referenced by registry
    always_blocked:
      - secrets
      - token caches unless user explicitly asks and path is verified
      - raw/source data without source-acquisition owner review
      - broker/order/live/paper artifacts

closeout_requirements:
  validators:
    - python scripts/ops/validate_project_hygiene.py
    - python scripts/ops/validate_project_structure_policy.py
  future_task_rule:
    - every new root entry must be classified
    - every new docs surface must be classified or live under an approved docs surface
    - every physical cleanup must write a cleanup_execution_log.csv
    - DB, source data, secrets, broker, live, paper, and strategy logic cleanup must be blocked unless task profile explicitly allows it

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
        "python scripts/ops/validate_project_structure_policy.py",
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
        if str(declared.get(name, {}).get("presence") or "required") == "optional":
            passes.append(f"optional root entry absent: {name}")
            continue
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

---

## File: scripts/ops/validate_project_structure_policy.py

```py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ops_common import ROOT, load_yaml, print_result


POLICY = "ops/project_structure_policy.yaml"


def as_list(node: Any) -> list[str]:
    if isinstance(node, list):
        return [str(item) for item in node]
    return []


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    try:
        policy = load_yaml(POLICY)
    except Exception as exc:
        return print_result("PROJECT STRUCTURE POLICY VALIDATION", [], [], [str(exc)])

    target_root = policy.get("target_root") or {}
    keep = set(as_list(target_root.get("keep")))
    local_only = set(as_list(target_root.get("local_only")))
    sensitive = set(as_list(target_root.get("sensitive_local_only")))
    review = set(as_list(target_root.get("review_before_move_or_delete")))
    declared = keep | local_only | sensitive | review
    if not declared:
        failures.append("target_root has no declared entries")

    actual = {path.name for path in ROOT.iterdir()}
    unclassified = sorted(actual - declared - {".git", ".gitignore", ".dvcignore"})
    if unclassified:
        failures.append(f"root entries missing from structure policy: {', '.join(unclassified)}")
    else:
        passes.append("all root entries covered by structure policy")

    for path in keep:
        if not (ROOT / path).exists():
            warnings.append(f"target keep path absent: {path}")

    duplicate_axes = policy.get("duplicate_axis_decisions") or []
    if duplicate_axes:
        passes.append(f"duplicate axes declared: {len(duplicate_axes)}")
    else:
        failures.append("duplicate_axis_decisions is empty")
    for row in duplicate_axes:
        if not row.get("canonical") or not row.get("current_action"):
            failures.append(f"duplicate axis missing canonical/current_action: {row}")

    docs_policy = policy.get("docs_surface_policy") or {}
    keep_docs = as_list(docs_policy.get("keep_canonical"))
    review_docs = as_list(docs_policy.get("review_surfaces"))
    if not keep_docs:
        failures.append("docs_surface_policy.keep_canonical is empty")
    if not review_docs:
        warnings.append("docs_surface_policy.review_surfaces is empty")
    docs_dir = ROOT / "docs"
    if docs_dir.exists():
        actual_docs = {f"docs/{item.name}" for item in docs_dir.iterdir() if item.is_dir()}
        classified_docs = set(keep_docs) | set(review_docs) | {"docs/archive"}
        missing_docs = sorted(actual_docs - classified_docs)
        if missing_docs:
            failures.append(f"docs surfaces missing policy classification: {', '.join(missing_docs)}")
        else:
            passes.append("all docs surfaces classified")

    closeout = policy.get("closeout_requirements") or {}
    validators = as_list(closeout.get("validators"))
    for command in [
        "python scripts/ops/validate_project_hygiene.py",
        "python scripts/ops/validate_project_structure_policy.py",
    ]:
        if command in validators:
            passes.append(f"closeout validator declared: {command}")
        else:
            failures.append(f"missing closeout validator declaration: {command}")

    closeout_path = ROOT / "scripts/ops/validate_codex_closeout.py"
    closeout_text = closeout_path.read_text(encoding="utf-8") if closeout_path.exists() else ""
    if "validate_project_structure_policy.py" in closeout_text:
        passes.append("codex closeout runs structure policy validator")
    else:
        failures.append("codex closeout does not run structure policy validator")

    return print_result("PROJECT STRUCTURE POLICY VALIDATION", passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())

```
