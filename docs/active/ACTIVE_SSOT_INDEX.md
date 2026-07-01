# Active SSOT Index

This index separates current source-of-truth files from navigation and historical material.

## Classification Taxonomy

| Class | Meaning |
|---|---|
| `ACTIVE` | Currently used for ongoing work. |
| `CANONICAL` | Source of truth for a domain. |
| `DIAGNOSTIC` | Research-only or validation-only. Not accepted. |
| `SUPERSEDED` | Replaced by a newer artifact, but useful for history. |
| `ARCHIVE` | Preserved but excluded from default Codex workflow. |
| `DELETE_CANDIDATE` | Likely safe to delete after explicit confirmation. |
| `UNKNOWN_NEEDS_REVIEW` | Do not delete. Requires owner review. |

## Current Active and Canonical Sources

| Path | Class | Purpose |
|---|---|---|
| `docs/active/README_ACTIVE.md` | `ACTIVE` | Default entry point. |
| `docs/active/PROJECT_STATUS.md` | `ACTIVE` | Condensed current status. |
| `docs/active/CODEX_READ_SCOPE.md` | `ACTIVE` | Default Codex context rules. |
| `docs/active/CURRENT_TASKS.md` | `ACTIVE` | Lightweight active queue. |
| `tasks/active_task_registry.csv` | `ACTIVE` | Lightweight active task registry. |
| `scripts/active_task_registry_validate.py` | `ACTIVE` | Validator for active task registry shape, statuses, and report links. |
| `scripts/project_file_inventory_audit.py` | `ACTIVE` | Full file inventory classifier for cleanup and retention decisions. |
| `scripts/project_artifact_guard_validate.py` | `ACTIVE` | Guardrail against unmanaged large payloads. |
| `docs/reports/A005_full_file_inventory_audit/` | `ACTIVE` | Current full-file inventory audit and cleanup candidate manifests. |
| `docs/reports/A007_dvc_lfs_artifact_management/` | `ACTIVE` | DVC artifact tracking plan, move log, and post-cleanup inventory. |
| `docs/reports/A008_path_by_path_owner_review/` | `ACTIVE` | Path-by-path owner review matrix for A005 `NEEDS_REVIEW` rows. |
| `docs/ownership/current_operating_model.md` | `CANONICAL` | Paper-trading governance and acceptance-board truth. |
| `docs/ownership/readiness_registry.yaml` | `CANONICAL` | Machine-readable readiness and blocker state. |
| `tasks/task_registry.csv` | `CANONICAL` | Historical/canonical task registry evidence. |
| `docs/acceptance/strategy_acceptance_contract.md` | `CANONICAL` | Strategy acceptance contract. |
| `docs/acceptance/deployment_acceptance_contract.md` | `CANONICAL` | Deployment readiness contract. |
| `docs/reports/task_599_strategy_acceptance_program/` | `CANONICAL` | Current strategy acceptance program. |
| `docs/reports/task_598_paper_week_feedback_operating_plan/` | `CANONICAL` | Current paper-week diagnosis. |
| `docs/reports/task_597_frontend_backend_paper_ops_triage/` | `ACTIVE` | Supporting owner remediation board. |
| `docs/reports/task_600_4_broker_truth_exit_lifecycle/` | `ACTIVE` | P0 broker-truth blocker evidence. |
| `docs/reports/task_602_4_order_replay_recovery/` | `ACTIVE` | P0 replay blocker evidence. |
| `docs/reports/task_601_4_concentration_stability/` | `ACTIVE` | P0 candidate-funnel evidence. |
| `docs/architecture/l0_source_acquisition_project_management_plan.md` | `CANONICAL` | Active L0/L1 source acquisition staged roadmap and project-management rule. |
| `configs/db_source_acquisition_scheduler.json` | `CANONICAL` | Conservative L0 source acquisition scheduler baseline and embedded management plan. |
| `docs/reports/task_4116_l0_l1_source_acquisition_stash_recovery/` | `ACTIVE` | Recovered L0/L1 source acquisition code, scheduler, and validation evidence. |
| `docs/reports/task_4117_l0_source_acquisition_project_management_integration/` | `ACTIVE` | L0 source acquisition project-management integration report and validation evidence. |
| `docs/reports/task_4118_l0_stage_1_official_core_api_smoke_stabilization/` | `ACTIVE` | Stage 1 official/core API smoke preflight evidence; network smoke remains pending. |
| `docs/reports/task_4119_l0_stage_1_bounded_network_smoke_execution/` | `ACTIVE` | Stage 1 bounded network smoke evidence for official, GDELT, Marketaux, and Alpaca microstructure. |
| `docs/reports/task_4120_l0_stage_2_realtime_source_budget_optimization/` | `ACTIVE` | Stage 2 real-time source budget evidence and Marketaux 16-minute cadence plan. |
| `docs/reports/task_4121_l0_stage_3_realtime_scheduler_setup_and_execution/` | `ACTIVE` | Stage 3 task-local scheduler setup/execution proof with 6/6 audit-only recurrence artifacts. |
| `docs/reports/task_4122_l0_stage_4_historical_backfill_optimization/` | `ACTIVE` | Stage 4 historical backfill optimization plan, blocker ledger, and coverage audit plan. |
| `docs/reports/task_4123_l0_stage_5_background_historical_backfill_from_2016/` | `ACTIVE` | Stage 5 bounded 2016-baseline background backfill proof and raw/cache ledgers. |
| `docs/reports/task_4124_l0_stage_6_l1_quality_coverage_audit_l2_handoff/` | `ACTIVE` | Stage 6 L1 quality/coverage audit and blocked L2 handoff decision. |
| `docs/reports/task_4125_l0_stage_5_full_2016_to_present_backfill_continuation/` | `ACTIVE` | Stage 5 full 2016-to-present backfill continuation state, raw/cache ledgers, and coverage progress. |
| `docs/reports/task_4126_l0_stage_6_full_backfill_l1_quality_coverage_reaudit/` | `ACTIVE` | Stage 6 full-backfill L1 quality/coverage reaudit and blocked L2 handoff decision. |
| `docs/reports/task_4127_l0_stage_6_source_time_feature_admission_l2_context_handoff/` | `ACTIVE` | Stage 6 source-time feature admission and partial L2 context-only handoff decision. |
| `docs/reports/task_4128_l0_l1_six_stage_end_to_end_closeout_audit/` | `ACTIVE` | Final L0/L1 six-stage end-to-end closeout audit for the current management plan state. |
| `docs/reports/task_4129_l0_l1_risk_burn_down_wikimedia_trading_scheduler_validator_chrome_mapping/` | `ACTIVE` | L0/L1 risk burn-down for Wikimedia noon context policy, trading-feature gates, scheduler QA, validator split, Chrome smoke-only posture, and mapping hardening. |
| `docs/reports/task_4130_l0_public_page_collection_effective_hardening/` | `ACTIVE` | Effective L0 public page collection hardening: static HTML fallback, failure reasons, fallback order, candidate hints, and Chrome smoke-only selector drift posture. |
| `docs/reports/task_4131_l0_prioritized_backfill_background_orchestration/` | `ACTIVE` | L0 prioritized background backfill start ledger, hourly progress tracking, alerts, and public newswire hardening smoke evidence. |
| `docs/reports/task_4132_l0_backfill_stall_detection_supervisor_hardening/` | `ACTIVE` | L0 backfill reliability hardening: stall detection, actionable alerts, stopped-lane supervisor, 5m checkpoint visibility, source failure summary, and bounded raw/cache/source-time audit. |
| `docs/reports/task_4133_l1_development_plan/` | `ACTIVE` | L1 normalized source packet contract and gate validator bootstrap: source-time, raw-integrity, mapping, authority, gap, and diagnostic-only handoff candidate samples. |
| `docs/reports/task_4134_l1_data_present_risk_burn_down/` | `ACTIVE` | L1 data-present risk burn-down: daily raw CSV sampling, false daily gap removal, public newswire discovery-only guard, DB-resident bar hash proof, and legacy L0-to-L2 bypass guard. |
| `docs/reports/task_4135_l1_final_hardening_l2_gpt_consult/` | `ACTIVE` | L1 final handoff hardening and L2 GPT consult packet: L1-to-L2 handoff contract, data-present coverage audit, remaining-risk register, and local-only GPT prompt that forbids GitHub. |
| `docs/reports/task_4136_l2_intake_feature_admission/` | `ACTIVE` | L2 intake and feature-admission checkpoint: news/macro future trading-feature path, ticker/news mapping gates, legacy L2 news quarantine, and continuous L1 validation hooks. |
| `docs/reports/task_4137_l1_1to6_gpt_pro_review/` | `ACTIVE` | GPT Pro practical review of six L1/L2 improvement items: Wikimedia date policy, trading-feature criteria, scheduler audit, validator split, Chrome crawling, and ticker/news mapping. |
| `docs/reports/task_4138_l1_practical_hardening/` | `ACTIVE` | L1 practical hardening from GPT Pro design: source-time precision policy, Wikimedia imputed-noon rule, source-family block reasons, and repeated validation evidence. |
| `docs/reports/task_4139_dirty_worktree_artifact_reconciliation/` | `ACTIVE` | Dirty worktree and artifact reconciliation: classification-only inventory, P0 owner-review queue, and no automatic cleanup decision. |
| `docs/reports/task_4140_swing_news_macro_newswire_feature_admission/` | `ACTIVE` | L2 swing feature admission posture for news, macro, and newswire: active feature candidates, daily/as-of timing, mapping scope, dedup, stale, and effect-window gates. |
| `docs/reports/task_4141_l2_gpt_pro_design_review/` | `ACTIVE` | GPT Pro review of current local L1/L2 state and next L2 direction: build L2 Swing Event Admission View before scoring or feature materialization. |
| `docs/reports/task_4142_l2_swing_event_admission/` | `ACTIVE` | L2 Swing Event Admission View: diagnostic-only admission/read view for news, macro, and newswire with lineage, mapping, dedup, stale/effect-window, source-time, and leakage guards. |
| `docs/reports/task_4143_l2_completion_gpt_review_and_read_contract/` | `ACTIVE` | L2 completion checkpoint from GPT Pro review: L3 whitelist read contract/view, mapping review queue, input-scope audit, dedup/stale summaries, and hard validator/QA without scoring or trading authority. |
| `docs/reports/task_4144_l1_l2_compatibility_bridge/` | `ACTIVE` | L1/L2 compatibility bridge: separates L1 packet-derived L2 handoff/review rows from L0 audit-only gap candidates, blocks direct L0-to-L2 bypass, and keeps capture time from being promoted to source/publication time. |
| `docs/reports/task_4146_l0_l2_wide_packetization_handoff/` | `ACTIVE` | L0-L2 wide handoff: converts broad L0 collector event-ledger evidence into wide L1 packets and L2 diagnostic feature-candidate materialization rows while keeping score, signal, order, broker, paper/live, and real-capital gates closed. |
| `docs/reports/task_4147_l0_l2_hardening_gpt_review_and_implementation/` | `ACTIVE` | L0-L2 hardening from GPT Pro review: article-level L1 packets, newswire mapping proof, separated L0 realtime config, durable 15-minute L1/L2 scheduler, backfill proof, and diagnostic feature schema rows with signal/order/broker gates closed. |
| `docs/reports/task_4148_l0_backfill_worker_recovery_health_gate/` | `ACTIVE` | L0 backfill worker recovery and health gate: restores stopped critical public newswire and public market/macro workers and requires pid-alive proof for L1/L2 coverage claims. |

## Navigation-Only Sources

| Path | Class | Purpose |
|---|---|---|
| `README.md` | `NAVIGATION_ONLY` | Repository-level orientation, older than current active layer. |
| `docs/INDEX.md` | `NAVIGATION_ONLY` | Broad docs index. Superseded for default Codex startup by `docs/active/`. |
| `docs/obsidian/` | `NAVIGATION_ONLY` | Human Obsidian navigation and boards. |
| `graphify-out/` | `DIAGNOSTIC` | Stale 2026-04-25 discovery output; not current state. |

## Missing Historical Layers

| Path | Class | Note |
|---|---|---|
| `docs/llm_wiki/` | `SUPERSEDED` | Not present in this checkout; active layer replaces it for default startup. |
| `docs/frontend_app_ssot/` | `SUPERSEDED` | Not present in this checkout; use `docs/frontend_data_contract.md`, frontend task reports, and current active pointers. |
