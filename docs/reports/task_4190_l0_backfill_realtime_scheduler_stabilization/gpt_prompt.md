# TASK-4187 GPT Pro Review Prompt

You are reviewing a local, uncommitted working copy of a US equity trading operating-system project.

Role:
- Professional backend engineer
- Data platform architect
- Scheduler / pipeline reliability engineer
- Trading data infrastructure reviewer

Important context:
- Do not read GitHub for this review. The local working copy is newer than GitHub.
- Base your answer only on the detailed local state below.
- Avoid over-engineering. Do not recommend Airflow, Celery, Kubernetes, graph DBs, vector DBs, LLM inference pipelines, or broad rewrites unless absolutely necessary.
- The goal is a durable Layer 0 operating harness: new Codex sessions must know which files are the current L0 truth, which backfill is current, which realtime scheduler is current, and which validators decide whether L0 is healthy.

Hard trading state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing or stale data = UNKNOWN/BLOCKER, never negative evidence

User problem:
The same L0 problems keep repeating across sessions:
- Layer 0 backfill is incomplete or reported as running when dead.
- Layer 0 realtime scheduler is configured in one place but not reliably active.
- Old collectors, old PID files, old validators, and new shard runners coexist.
- New Codex sessions do not know which files are the current L0 standard.
- The project lacks a single “current L0 operating contract” that binds source inventory, latest backfill, realtime scheduler, PID/heartbeat, validator, and closeout gate.
- Work keeps advancing to L1/L2/L3/L4 while L0 still has live blockers.

Current local evidence as of 2026-07-01 Asia/Seoul:

1. Latest audit
- TASK-4183 overall verdict: BLOCKED_NOT_ALL_RUNNING
- L0 status: PARTIAL_RUNNING_WITH_BLOCKER
- Reason: backfill/L0-L2 scheduled tasks are running or recently successful, but public newswire aggregate still records dead active worker PIDs
- L0 public newswire aggregate status: RUNNING
- L0 public newswire aggregate progress: 55.6693%
- Pending units: 1818
- Active workers recorded: 3
- Dead active workers in audit: 3
- Scheduled backfill result: 267009
- Scheduled L0-L2 result: 1

2. Current public newswire aggregate
File:
- data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json

Current summary:
- status: RUNNING
- progress_pct: 55.6693
- completed_units: 2283
- pending_units: 1818
- failed_units: 0
- partial_units: 56
- total_units: 4101
- active_workers: 3
- stale_workers: 58

By source:
- BusinessWire: completed 2141, pending 1693, failed 0, partial 46, unit_vph about 18.5752, row_count 44178
- GlobeNewswire: completed 126, pending 0, failed 0, partial 0, row_count 640970
- PRNewswire: completed 16, pending 125, failed 0, partial 10, row_count 49284

Important interpretation:
- GN is complete.
- BW remains the largest blocker.
- PRN still has pending/partial work.
- aggregate says RUNNING, but background launcher PID is dead.

3. Background process files / PID evidence
- data/artifacts/l0_public_newswire_backfill_shards/background_process.json
  - pid: 16236
  - alive: false
  - started_at: 2026-07-01T09:38:35Z
- data/artifacts/l0_public_market_macro_news_backfill/background_process.json
  - pid: 2924
  - alive: true
  - process: python
  - started_at: 2026-07-01T14:06:02Z
- data/artifacts/l0_bar_full_backfill/background_process_5m.json
  - pid: 34128
  - alive: false
  - started_at: 2026-06-29T12:51:42Z
- data/artifacts/l0_bar_daily_full_backfill/background_process.json
  - pid: 20848
  - alive: false
  - started_at: 2026-06-29T12:51:39Z

4. Scheduler evidence
Windows Task Scheduler:
- TraderBrainL0Backfill: not found in targeted query
- TraderBrainL0PublicNewswireBackfill: not found in targeted query
- TraderBrainL0Realtime: not found in targeted query
- TraderBrainSourceAcquisitionScheduler: not found in targeted query
- TraderBrainL0L2Hardening4147:
  - Status: Ready
  - Last Run Time: 2026-07-01 23:37:11 KST
  - Last Result: 1
  - Next Run Time: 2026-07-01 23:52:10 KST
  - Runs scripts/run_l0_l2_hardening_once_4147.ps1
- TraderBrainL0BackfillWorkerRecovery4148:
  - Status: Running
  - Last Result: -2147020576
  - Runs scripts/run_l0_backfill_worker_recovery_once_4148.ps1

5. Config evidence
File:
- configs/l0_realtime_operational_safe_config_4147.json

It says:
- public_newswire_feeds_realtime_safe enabled true, 30m interval
- public_context_news_feeds_realtime_safe enabled true, 30m interval
- public_market_macro_news_feeds_realtime_safe enabled true, 30m interval
- runtime_boundary.scheduler_task_name = TraderBrainL0L2Hardening4147
- chrome_crawling = smoke_only_not_runtime_collection
- codex_gpt = planning_review_recovery_only_not_runtime_collection
- l1_l2_loop_minutes = 15

But:
- scheduler task result is failing
- this config is not yet the single L0 SSOT
- older db_source_acquisition_scheduler.json still has many relevant jobs enabled false

File:
- configs/db_source_acquisition_scheduler.json

It is older/conservative:
- registered_loop_enabled false
- public_newswire_feeds_30m enabled false
- public_context_news_feeds_30m enabled false
- public_market_macro_news_feeds_30m enabled false
- public_newswire backfill historical sections exist but were superseded by sharded runner work

6. Existing important scripts
- scripts/run_l0_public_newswire_sharded_backfill.py
- scripts/aggregate_l0_public_newswire_shards.py
- scripts/validate_l0_public_newswire_sharded_backfill.py
- scripts/control_l0_public_newswire_acceleration.ps1
- scripts/run_l0_l2_hardening_4147.py
- scripts/run_l0_l2_hardening_once_4147.ps1
- scripts/validate_l0_l2_hardening_4147.py
- scripts/run_l0_backfill_worker_recovery_4148.py
- scripts/run_l0_backfill_worker_recovery_once_4148.ps1
- scripts/validate_l0_backfill_worker_recovery_4148.py
- scripts/start_l0_public_newswire_backfill.ps1 (legacy single collector)
- scripts/start_l0_public_newswire_collector.ps1 (legacy realtime collector)
- scripts/start_l0_prioritized_backfills.ps1 (legacy mixed launcher)

7. Governance context
Project AGENTS.md rules:
- Do not start work without a task id.
- Do not scan the whole repository by default.
- Read generated context bundles first when they exist.
- Follow ops/task_profiles.yaml.
- Respect ops/doc_registry.yaml.
- Never treat archived/superseded docs as active SSOT.
- Do not create new markdown reports outside the relevant task report folder.
- All task outputs must update ops/task_registry.yaml.
- All new docs must update ops/doc_registry.yaml.
- Run required validators before closeout.

Relevant profile:
- L0_L1_DATA_PIPELINE
- Required principles: source time preserved, raw data integrity first, no strategy logic, missing/stale is UNKNOWN/BLOCKER
- Forbidden: candidate promotion, policy action, order intent, broker mutation, live order
- Required checks: storage contract, source time audit, freshness status, artifact manifest

8. Desired outcome
Design and review a concrete implementation plan for TASK-4187:

Goal:
Create a durable L0 operating harness so that:
1. Every new Codex session can identify the current L0 SSOT/context in one place.
2. The current L0 backfill state is visible by source/lane with live PID/heartbeat reality.
3. Realtime scheduler status is visible and validated.
4. Old legacy collectors and PID files cannot be mistaken for current operating state.
5. Validators fail or warn correctly when:
   - aggregate says RUNNING but PID is dead
   - scheduler last result failed
   - latest config and scheduled task disagree
   - current L0 context bundle is missing/stale
   - backfill/realtime handoff is broken
6. The solution remains simple: local Python/PowerShell/JSON/YAML/Windows Task Scheduler only.

Please answer:

1. Diagnosis
- What is the real structural problem?
- Why do the same L0 issues keep repeating?

2. Proposed L0 operating contract / SSOT
- What exact files should become the “read this first” L0 truth?
- What should each file contain?
- Which existing files should be active vs legacy/deprecated?

3. Implementation plan
- Concrete files/scripts to add or modify.
- Keep the plan small and repo-native.
- Prefer a single L0 status builder/validator over many scattered checks.

4. Scheduler/backfill/realtime model
- How should backfill and realtime loops be separated?
- How should they be tied together by validator?
- How should dead PID/stale heartbeat be handled?

5. Legacy cleanup model
- How to mark old collectors/schedulers/PID artifacts as legacy without deleting useful raw data?
- How to prevent future tasks from reading old paths as current state?

6. Validator/closeout gate
- What should hard-fail?
- What should warn?
- What should be allowed as an explicit blocker?

7. Codex final implementation prompt
- Give a precise, bounded prompt Codex can execute for TASK-4187.
- Include validation commands.

Do not recommend:
- Airflow/Celery/Kubernetes
- graph DB/vector DB
- LLM-based entity inference
- trading signals, ranking, sizing, orders, paper/live promotion
- broad rewrites
- deleting raw backfill data

