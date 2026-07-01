# Codex Context Bundle

Task: TASK-4190
Profile: L0_L1_DATA_PIPELINE
Generated At: 2026-07-01T15:16:30+00:00
Token Count: 15494
Token Count Mode: approximate
Max Tokens: 24000

---

## Included Files

| Path | Bytes | Tokens | Reason |
|---|---:|---:|---|
| AGENTS.md | 1380 | 345 | must_include |
| configs/l0_realtime_operational_safe_config_4147.json | 2163 | 540 | must_include |
| data/artifacts/l0_operating_status/current_l0_context.md | 2213 | 553 | must_include |
| data/artifacts/l0_operating_status/current_l0_status.json | 7825 | 1872 | must_include |
| data/artifacts/l0_operating_status/l0_operating_manifest.json | 1513 | 369 | must_include |
| docs/reports/task_4190_l0_backfill_realtime_scheduler_stabilization/gpt_response.md | 31796 | 6864 | optional_include |
| docs/reports/task_4190_l0_backfill_realtime_scheduler_stabilization/report.md | 2654 | 663 | must_include |
| ops/context_bundles.yaml | 7162 | 1790 | must_include |
| ops/l0_operating_contract.yaml | 5578 | 1394 | must_include |
| ops/task_profiles.yaml | 4417 | 1104 | must_include |

---

## Excluded Files

| Pattern/Path | Reason |
|---|---|
| docs/archive/** | configured exclude |
| node_modules/** | configured exclude |
| db/** | configured exclude |
| secrets/** | configured exclude |

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

## File: configs/l0_realtime_operational_safe_config_4147.json

```json
{
  "version": 1,
  "task_id": "TASK-4147",
  "purpose": "safe separated L0 realtime collector config; diagnostic-only; no broker/order/signal authority",
  "based_on": "configs/db_source_acquisition_scheduler.json",
  "activation_posture": "operator_safe_realtime_ready",
  "permissions": {
    "diagnostic_only": true,
    "execution_permitted": 0,
    "broker_mutation_permitted": 0,
    "paper_promotion_permitted": 0,
    "real_capital_permitted": 0,
    "live_order_enabled": 0,
    "buy_sell_signal_generation_permitted": 0
  },
  "jobs": [
    {
      "name": "public_newswire_feeds_realtime_safe",
      "enabled": true,
      "interval_minutes": 30,
      "allow_network": true,
      "provider": "public_newswire_feeds",
      "mode": "realtime_incremental",
      "sources": [
        "prnewswire",
        "globenewswire",
        "businesswire"
      ],
      "max_items_per_source": 50,
      "request_sleep_seconds": 1,
      "diagnostic_only": true
    },
    {
      "name": "public_context_news_feeds_realtime_safe",
      "enabled": true,
      "interval_minutes": 30,
      "allow_network": true,
      "provider": "public_context_news_feeds",
      "mode": "realtime_incremental",
      "sources": [
        "federal_reserve_press_all",
        "cftc_press_releases",
        "federal_register_documents"
      ],
      "max_items_per_source": 50,
      "request_sleep_seconds": 1,
      "diagnostic_only": true
    },
    {
      "name": "public_market_macro_news_feeds_realtime_safe",
      "enabled": true,
      "interval_minutes": 30,
      "allow_network": true,
      "provider": "public_market_macro_news_feeds",
      "mode": "realtime_incremental",
      "sources": [
        "cnbc_public_rss",
        "wikimedia_current_events",
        "nasdaq_trader_notices"
      ],
      "max_items_per_source": 50,
      "request_sleep_seconds": 1,
      "diagnostic_only": true
    }
  ],
  "runtime_boundary": {
    "chrome_crawling": "smoke_only_not_runtime_collection",
    "codex_gpt": "planning_review_recovery_only_not_runtime_collection",
    "l1_l2_loop_minutes": 15,
    "scheduler_task_name": "TraderBrainL0L2Hardening4147"
  }
}
```

---

## File: data/artifacts/l0_operating_status/current_l0_context.md

```md
# Current L0 Operating Context

- Generated at: 2026-07-01T15:16:25+00:00
- Task: TASK-4190
- Verdict: BLOCKED
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN

## Read This First
- ops/l0_operating_contract.yaml
- data/artifacts/l0_operating_status/current_l0_status.json
- data/artifacts/l0_operating_status/current_l0_context.md
- data/artifacts/l0_operating_status/l0_operating_manifest.json

## Public Newswire Backfill
- Aggregate status: RUNNING
- Derived runtime status: BLOCKED_DEAD_PID
- Progress: 55.6693%
- Units: completed=2283 pending=1818 partial=56 failed=0 total=4101
- Launcher PID: 16236 alive=False command_verified=False
- Active workers: recorded=3 alive=0 stale=58

## Source Progress
| source | status | completed | pending | partial | failed | rows |
|---|---:|---:|---:|---:|---:|---:|
| businesswire | INCOMPLETE | 2141 | 1693 | 46 | 0 | 44178 |
| globenewswire | COMPLETE | 126 | 0 | 0 | 0 | 640970 |
| prnewswire | INCOMPLETE | 16 | 125 | 10 | 0 | 49284 |

## Scheduler
- Realtime task: TraderBrainL0L2Hardening4147 exists=True status=Ready last_result=1 classified=FAILED
- Recovery task: TraderBrainL0BackfillWorkerRecovery4148 exists=True status=Ready last_result=267014 classified=FAILED

## Blockers
- L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD
- L0_PUBLIC_NEWSWIRE_INCOMPLETE
- L0_REALTIME_SCHEDULER_LAST_RESULT_FAILED

## Warnings
- L0_BACKGROUND_PID_DEAD:daily_bars_backfill
- L0_BACKGROUND_PID_DEAD:five_min_bars_backfill
- L0_LEGACY_PATH_PRESENT:configs/db_source_acquisition_scheduler.json
- L0_LEGACY_PATH_PRESENT:data/artifacts/l0_public_newswire_backfill/background_process.json
- L0_LEGACY_PATH_PRESENT:scripts/start_l0_prioritized_backfills.ps1
- L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_backfill.ps1
- L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_collector.ps1
- L0_STALE_WORKERS_PRESENT

## Interpretation
- aggregate_progress.json is progress evidence only. It is not runtime health by itself.
- Missing or stale L0 data is UNKNOWN/BLOCKER, never negative evidence.
- Legacy scripts and configs may exist, but they are not current L0 runtime unless named in ops/l0_operating_contract.yaml.

```

---

## File: data/artifacts/l0_operating_status/current_l0_status.json

```json
{
  "schema_version": "l0_operating_status_v1",
  "task_id": "TASK-4190",
  "generated_at": "2026-07-01T15:16:25+00:00",
  "contract_path": "ops/l0_operating_contract.yaml",
  "overall_verdict": "BLOCKED",
  "blockers": [
    "L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD",
    "L0_PUBLIC_NEWSWIRE_INCOMPLETE",
    "L0_REALTIME_SCHEDULER_LAST_RESULT_FAILED"
  ],
  "warnings": [
    "L0_BACKGROUND_PID_DEAD:daily_bars_backfill",
    "L0_BACKGROUND_PID_DEAD:five_min_bars_backfill",
    "L0_LEGACY_PATH_PRESENT:configs/db_source_acquisition_scheduler.json",
    "L0_LEGACY_PATH_PRESENT:data/artifacts/l0_public_newswire_backfill/background_process.json",
    "L0_LEGACY_PATH_PRESENT:scripts/start_l0_prioritized_backfills.ps1",
    "L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_backfill.ps1",
    "L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_collector.ps1",
    "L0_STALE_WORKERS_PRESENT"
  ],
  "hard_state": {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
    "broker_mutation_permitted": 0,
    "live_order_permitted": 0,
    "paper_promotion_permitted": 0,
    "missing_or_stale_data_semantics": "UNKNOWN_OR_BLOCKER_NOT_NEGATIVE"
  },
  "read_first_order": [
    "ops/l0_operating_contract.yaml",
    "data/artifacts/l0_operating_status/current_l0_status.json",
    "data/artifacts/l0_operating_status/current_l0_context.md",
    "data/artifacts/l0_operating_status/l0_operating_manifest.json"
  ],
  "public_newswire": {
    "aggregate_path": "data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json",
    "background_process_path": "data/artifacts/l0_public_newswire_backfill_shards/background_process.json",
    "aggregate_status": "RUNNING",
    "derived_runtime_status": "BLOCKED_DEAD_PID",
    "progress_pct": 55.6693,
    "completed_units": 2283,
    "pending_units": 1818,
    "failed_units": 0,
    "partial_units": 56,
    "total_units": 4101,
    "launcher_pid": 16236,
    "launcher_pid_alive": false,
    "launcher_command_line_verified": false,
    "active_worker_count": 3,
    "active_worker_alive_count": 0,
    "stale_worker_count": 58,
    "by_source": {
      "businesswire": {
        "completed_units": 2141,
        "pending_units": 1693,
        "partial_units": 46,
        "failed_units": 0,
        "row_count": 44178,
        "unit_velocity_per_hour": 18.5752,
        "status": "INCOMPLETE"
      },
      "globenewswire": {
        "completed_units": 126,
        "pending_units": 0,
        "partial_units": 0,
        "failed_units": 0,
        "row_count": 640970,
        "unit_velocity_per_hour": 0.0,
        "status": "COMPLETE"
      },
      "prnewswire": {
        "completed_units": 16,
        "pending_units": 125,
        "partial_units": 10,
        "failed_units": 0,
        "row_count": 49284,
        "unit_velocity_per_hour": 0.0,
        "status": "INCOMPLETE"
      }
    },
    "active_workers": [
      {
        "source": "businesswire",
        "shard_key": "2025-02",
        "worker_pid": null,
        "alive": false,
        "status": null,
        "last_progress_at": "2026-07-01T09:38:14.485830Z"
      },
      {
        "source": "businesswire",
        "shard_key": "2025-03",
        "worker_pid": null,
        "alive": false,
        "status": null,
        "last_progress_at": "2026-07-01T09:36:34.336604Z"
      },
      {
        "source": "businesswire",
        "shard_key": "2025-04",
        "worker_pid": null,
        "alive": false,
        "status": null,
        "last_progress_at": "2026-07-01T09:37:54.436751Z"
      }
    ]
  },
  "lanes": {
    "public_newswire_backfill": {
      "role": "historical_backfill",
      "background_process": "data/artifacts/l0_public_newswire_backfill_shards/background_process.json",
      "pid": 16236,
      "pid_alive": false
    },
    "public_market_macro_news_backfill": {
      "role": "historical_backfill",
      "background_process": "data/artifacts/l0_public_market_macro_news_backfill/background_process.json",
      "pid": 2924,
      "pid_alive": true
    },
    "daily_bars_backfill": {
      "role": "historical_backfill_and_realtime_continuity",
      "background_process": "data/artifacts/l0_bar_daily_full_backfill/background_process.json",
      "pid": 20848,
      "pid_alive": false
    },
    "five_min_bars_backfill": {
      "role": "historical_backfill_and_realtime_continuity",
      "background_process": "data/artifacts/l0_bar_full_backfill/background_process_5m.json",
      "pid": 34128,
      "pid_alive": false
    },
    "realtime_hardening_loop": {
      "role": "realtime_incremental_collection_and_l1_l2_refresh"
    },
    "backfill_recovery_loop": {
      "role": "backfill_worker_recovery_guard"
    }
  },
  "scheduler": {
    "realtime": {
      "name": "TraderBrainL0L2Hardening4147",
      "exists": true,
      "query_returncode": 0,
      "task_name": "\\TraderBrainL0L2Hardening4147",
      "status": "Ready",
      "next_run_time": "2026-07-02 오전 12:22:10",
      "last_run_time": "2026-07-02 오전 12:07:11",
      "last_result": "1",
      "last_result_status": "FAILED",
      "task_to_run": "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\\Users\\minjo\\OneDrive\\바탕 화면\\외국주식 퀀트트레이딩\\scripts\\run_l0_l2_hardening_once_4147.ps1\" -ProjectRoot \"C:\\Users\\minjo\\OneDrive\\바탕 화면\\외국주식 퀀트트레이딩\"\""
    },
    "backfill_recovery": {
      "name": "TraderBrainL0BackfillWorkerRecovery4148",
      "exists": true,
      "query_returncode": 0,
      "task_name": "\\TraderBrainL0BackfillWorkerRecovery4148",
      "status": "Ready",
      "next_run_time": "2026-07-02 오전 12:20:20",
      "last_run_time": "2026-07-02 오전 12:05:21",
      "last_result": "267014",
      "last_result_status": "FAILED",
      "task_to_run": "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\\Users\\minjo\\OneDrive\\바탕 화면\\외국주식 퀀트트레이딩\\scripts\\run_l0_backfill_worker_recovery_once_4148.ps1\" -ProjectRoot \"C:\\Users\\minjo\\OneDrive\\바탕 화면\\외국주식 퀀트트레이딩\"\""
    }
  },
  "config_alignment": {
    "realtime_config_path": "configs/l0_realtime_operational_safe_config_4147.json",
    "config_scheduler_task": "TraderBrainL0L2Hardening4147",
    "contract_scheduler_task": "TraderBrainL0L2Hardening4147",
    "aligned": true
  },
  "legacy_runtime_entrypoints": [
    {
      "path": "configs/db_source_acquisition_scheduler.json",
      "exists": true,
      "reason": "conservative historical scheduler config; not current L0 runtime truth"
    },
    {
      "path": "scripts/start_l0_public_newswire_backfill.ps1",
      "exists": true,
      "reason": "legacy single newswire backfill launcher; superseded by sharded runner"
    },
    {
      "path": "scripts/start_l0_public_newswire_collector.ps1",
      "exists": true,
      "reason": "legacy newswire collector launcher; not current runtime truth"
    },
    {
      "path": "scripts/start_l0_prioritized_backfills.ps1",
      "exists": true,
      "reason": "legacy mixed launcher; not current runtime truth"
    },
    {
      "path": "data/artifacts/l0_public_newswire_backfill/background_process.json",
      "exists": true,
      "reason": "legacy single-run PID artifact; sharded background_process is current"
    }
  ],
  "negative_evidence_conversion": 0,
  "broker_mutation_permitted_flag": 0,
  "live_order_permitted_flag": 0,
  "paper_promotion_permitted_flag": 0,
  "real_capital_permitted_flag": 0
}

```

---

## File: data/artifacts/l0_operating_status/l0_operating_manifest.json

```json
{
  "schema_version": "l0_operating_manifest_v1",
  "task_id": "TASK-4190",
  "generated_at": "2026-07-01T15:16:25+00:00",
  "builder": "scripts/build_l0_operating_status_4190.py",
  "validator": "scripts/validate_l0_operating_contract_4190.py",
  "inputs": [
    "configs/l0_realtime_operational_safe_config_4147.json",
    "data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json",
    "data/artifacts/l0_public_newswire_backfill_shards/background_process.json",
    "ops/l0_operating_contract.yaml"
  ],
  "outputs": [
    "data/artifacts/l0_operating_status/current_l0_status.json",
    "data/artifacts/l0_operating_status/current_l0_context.md",
    "data/artifacts/l0_operating_status/l0_operating_manifest.json"
  ],
  "overall_verdict": "BLOCKED",
  "blockers": [
    "L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD",
    "L0_PUBLIC_NEWSWIRE_INCOMPLETE",
    "L0_REALTIME_SCHEDULER_LAST_RESULT_FAILED"
  ],
  "warnings": [
    "L0_BACKGROUND_PID_DEAD:daily_bars_backfill",
    "L0_BACKGROUND_PID_DEAD:five_min_bars_backfill",
    "L0_LEGACY_PATH_PRESENT:configs/db_source_acquisition_scheduler.json",
    "L0_LEGACY_PATH_PRESENT:data/artifacts/l0_public_newswire_backfill/background_process.json",
    "L0_LEGACY_PATH_PRESENT:scripts/start_l0_prioritized_backfills.ps1",
    "L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_backfill.ps1",
    "L0_LEGACY_PATH_PRESENT:scripts/start_l0_public_newswire_collector.ps1",
    "L0_STALE_WORKERS_PRESENT"
  ]
}

```

---

## File: docs/reports/task_4190_l0_backfill_realtime_scheduler_stabilization/gpt_response.md

```md
사장님, 핵심은 L0 수집기를 더 만드는 것이 아니라 현재 운영상태를 한 계약·상태 스냅샷·검증 게이트로 고정하는 것입니다. SSOT, status builder, validator, legacy 경계를 중심으로 TASK-4187 구현안을 정리하겠습니다.

aggregate_progress.json은 진행률 자료로만 보존하고, 운영 건강도 판단은 별도 SSOT가 맡도록 분리하는 것이 추가 핵심입니다.

8m 5s 동안 생각함

사장님, TASK-4187은 반드시 해야 하는 P0 작업입니다.
현재 문제는 “L0 수집기가 느리다”가 아니라, L0의 현재 진실을 판정하는 운영 계약이 없어서 매 세션마다 서로 다른 파일을 읽고 다른 결론을 내리는 구조적 문제입니다.

현재 로컬 증거 기준 L0는 이렇게 판정해야 합니다.

L0 overall:
BLOCKED

주요 blocker:
1. public_newswire aggregate는 RUNNING이라고 하지만 launcher PID는 dead
2. active worker 3개도 audit상 dead
3. BW/PRN historical backfill 미완료
4. realtime/hardening scheduler는 존재하나 Last Result = 1로 실패
5. recovery scheduler는 Running이지만 과거 Last Result가 non-success
6. current L0 SSOT가 없어 legacy config/script/PID와 current state가 섞임
1. Diagnosis
1) 진짜 구조적 문제

현재 L0에는 진행률 파일은 있지만 운영 상태 파일이 없습니다.

aggregate_progress.json은 다음을 말할 수 있습니다.

몇 개 unit이 완료됐는가
어떤 source가 pending인가
row_count가 얼마인가

하지만 이것만으로는 다음을 말하면 안 됩니다.

L0가 실제로 살아 있는가
현재 launcher가 살아 있는가
worker PID가 유효한가
scheduler가 성공 중인가
realtime loop가 돌고 있는가
이 config가 현재 기준인가

즉, 지금은 progress artifact가 health artifact처럼 오용되고 있습니다.

2) 왜 같은 L0 문제가 반복되는가

반복 원인은 명확합니다.

반복 문제	실제 원인
backfill이 RUNNING으로 보이는데 죽어 있음	progress 상태와 PID/heartbeat 상태가 분리되어 검증되지 않음
realtime scheduler가 있는지 없는지 매번 헷갈림	current scheduler task name이 SSOT에 고정되어 있지 않음
old collector와 new shard runner가 공존	legacy registry가 없어 Codex가 오래된 script도 current로 오해함
old PID file이 current로 읽힘	PID artifact에 current/legacy 구분이 없음
validator가 제각각	L0 전체를 판정하는 단일 builder/validator가 없음
L1/L2/L3/L4로 계속 넘어감	L0 closeout gate가 상위 layer 작업을 막지 못함

결론은 하나입니다.

TASK-4187의 핵심은 collector 개선이 아니라
L0 operating contract + current status builder + closeout validator를 만드는 것

입니다.

2. Proposed L0 Operating Contract / SSOT
결론: “읽을 파일”은 4개로 고정해야 합니다

TASK-4187 이후 새 Codex 세션은 L0 관련 작업 시작 전 아래 순서로 읽어야 합니다.

1. ops/l0_operating_contract.yaml
2. data/artifacts/l0_operating_status/current_l0_status.json
3. data/artifacts/l0_operating_status/current_l0_context.md
4. data/artifacts/l0_operating_status/l0_operating_manifest.json

이 중 수동 관리 SSOT는 1번 하나입니다.
2~4번은 builder가 생성하는 산출물이어야 합니다.

2.1 ops/l0_operating_contract.yaml
역할

L0의 수동 관리 운영 계약입니다.

여기에는 “현재 L0 기준이 무엇인가”가 명시됩니다.

포함 내용
YAML
contract_version: 1
task_id: TASK-4187
last_updated: "2026-07-01"

hard_state:
  strategy: NOT_ACCEPTED
  deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
  real_capital: FORBIDDEN
  missing_or_stale: UNKNOWN_OR_BLOCKER

active_l0_domains:
  public_newswire:
    role: historical_backfill
    current_runner: scripts/run_l0_public_newswire_sharded_backfill.py
    current_aggregator: scripts/aggregate_l0_public_newswire_shards.py
    current_validator: scripts/validate_l0_public_newswire_sharded_backfill.py
    aggregate_progress: data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json
    background_process: data/artifacts/l0_public_newswire_backfill_shards/background_process.json

  realtime:
    role: realtime_safe_collection_and_l0_l2_handoff
    current_config: configs/l0_realtime_operational_safe_config_4147.json
    current_scheduler_task: TraderBrainL0L2Hardening4147
    current_runner: scripts/run_l0_l2_hardening_4147.py
    current_once_wrapper: scripts/run_l0_l2_hardening_once_4147.ps1
    current_validator: scripts/validate_l0_l2_hardening_4147.py

  worker_recovery:
    role: backfill_worker_recovery
    current_scheduler_task: TraderBrainL0BackfillWorkerRecovery4148
    current_runner: scripts/run_l0_backfill_worker_recovery_4148.py
    current_once_wrapper: scripts/run_l0_backfill_worker_recovery_once_4148.ps1
    current_validator: scripts/validate_l0_backfill_worker_recovery_4148.py

health_thresholds:
  worker_heartbeat_stale_minutes: 20
  context_stale_minutes: 60
  scheduler_grace_minutes: 70
  allow_scheduler_running_code: true

legacy_paths:
  configs:
    - configs/db_source_acquisition_scheduler.json
  scripts:
    - scripts/start_l0_public_newswire_backfill.ps1
    - scripts/start_l0_public_newswire_collector.ps1
    - scripts/start_l0_prioritized_backfills.ps1
  non_current_pid_artifacts:
    - data/artifacts/l0_bar_full_backfill/background_process_5m.json
    - data/artifacts/l0_bar_daily_full_backfill/background_process.json

status_semantics:
  aggregate_progress_is_not_health: true
  running_requires_alive_pid_or_valid_scheduler: true
  dead_pid_overrides_running_progress: true
  missing_stale_incomplete_is_blocker_not_negative_evidence: true

핵심은 이겁니다.

aggregate_progress.json은 current progress 파일이다.
하지만 current health 파일은 아니다.
2.2 data/artifacts/l0_operating_status/current_l0_status.json
역할

builder가 생성하는 machine-readable current L0 truth입니다.

포함 내용
JSON
{
  "generated_at": "2026-07-01T...+09:00",
  "contract_path": "ops/l0_operating_contract.yaml",
  "overall_verdict": "BLOCKED",
  "blockers": [
    "PUBLIC_NEWSWIRE_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD",
    "PUBLIC_NEWSWIRE_ACTIVE_WORKERS_DEAD",
    "PUBLIC_NEWSWIRE_BACKFILL_INCOMPLETE",
    "REALTIME_SCHEDULER_LAST_RESULT_FAILED"
  ],
  "warnings": [
    "LEGACY_CONFIG_PRESENT_NOT_CURRENT",
    "RECOVERY_TASK_RUNNING_WITH_PREVIOUS_NON_SUCCESS_RESULT"
  ],
  "public_newswire": {
    "aggregate_status": "RUNNING",
    "derived_runtime_status": "BLOCKED_DEAD_PID",
    "progress_pct": 55.6693,
    "completed_units": 2283,
    "pending_units": 1818,
    "failed_units": 0,
    "partial_units": 56,
    "active_workers_recorded": 3,
    "active_workers_alive": 0,
    "dead_active_workers": 3,
    "stale_workers": 58,
    "sources": {
      "BusinessWire": {
        "completed": 2141,
        "pending": 1693,
        "partial": 46,
        "row_count": 44178
      },
      "GlobeNewswire": {
        "completed": 126,
        "pending": 0,
        "partial": 0,
        "row_count": 640970
      },
      "PRNewswire": {
        "completed": 16,
        "pending": 125,
        "partial": 10,
        "row_count": 49284
      }
    }
  },
  "scheduler": {
    "current_realtime_task": {
      "name": "TraderBrainL0L2Hardening4147",
      "status": "Ready",
      "last_result": 1,
      "verdict": "FAILED"
    },
    "current_recovery_task": {
      "name": "TraderBrainL0BackfillWorkerRecovery4148",
      "status": "Running",
      "last_result": -2147020576,
      "verdict": "DEGRADED_OR_UNKNOWN"
    }
  },
  "config_alignment": {
    "realtime_config_task_name": "TraderBrainL0L2Hardening4147",
    "contract_task_name": "TraderBrainL0L2Hardening4147",
    "aligned": true
  },
  "legacy_runtime_risk": {
    "legacy_collectors_present": true,
    "legacy_paths_are_not_current": true
  }
}

이 파일은 Codex가 “현재 L0 괜찮나?”를 판단할 때 읽는 1차 machine truth입니다.

2.3 data/artifacts/l0_operating_status/current_l0_context.md
역할

새 Codex 세션용 human-readable read-this-first bundle입니다.

포함 내용
# Current L0 Context

Generated At:
...

Overall:
BLOCKED

Do not treat aggregate_progress RUNNING as operationally healthy.

Current active files:
- public_newswire aggregate: ...
- active realtime config: ...
- active scheduler task: ...
- active validators: ...

Current blockers:
1. aggregate says RUNNING but launcher PID is dead
2. BW/PRN backfill incomplete
3. realtime scheduler last result failed

Legacy / do not use as current:
- configs/db_source_acquisition_scheduler.json
- scripts/start_l0_public_newswire_backfill.ps1
- scripts/start_l0_public_newswire_collector.ps1
- scripts/start_l0_prioritized_backfills.ps1

Next allowed work:
- fix L0 runtime/scheduler/backfill blockers
- do not claim L1/L2/L3/L4 global readiness while L0 is blocked

이 파일이 없거나 60분 이상 stale이면 validator가 fail해야 합니다.

2.4 data/artifacts/l0_operating_status/l0_operating_manifest.json
역할

artifact manifest입니다.

포함 내용
JSON
{
  "task_id": "TASK-4187",
  "generated_at": "...",
  "builder": "scripts/build_l0_operating_status_4187.py",
  "validator": "scripts/validate_l0_operating_contract_4187.py",
  "inputs": [
    "ops/l0_operating_contract.yaml",
    "data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json",
    "data/artifacts/l0_public_newswire_backfill_shards/background_process.json",
    "configs/l0_realtime_operational_safe_config_4147.json"
  ],
  "outputs": [
    "data/artifacts/l0_operating_status/current_l0_status.json",
    "data/artifacts/l0_operating_status/current_l0_context.md"
  ],
  "validators_run": [
    "validate_l0_public_newswire_sharded_backfill.py",
    "validate_l0_l2_hardening_4147.py",
    "validate_l0_backfill_worker_recovery_4148.py",
    "validate_l0_operating_contract_4187.py"
  ]
}
3. Active vs Legacy / Deprecated
Active files
구분	Active file	판정
L0 contract	ops/l0_operating_contract.yaml	새 SSOT
L0 current status	data/artifacts/l0_operating_status/current_l0_status.json	새 generated truth
L0 context bundle	data/artifacts/l0_operating_status/current_l0_context.md	새 read-first bundle
public newswire backfill runner	scripts/run_l0_public_newswire_sharded_backfill.py	current
public newswire aggregate	data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json	current progress only
public newswire validator	scripts/validate_l0_public_newswire_sharded_backfill.py	current
public newswire control	scripts/control_l0_public_newswire_acceleration.ps1	current control
realtime config	configs/l0_realtime_operational_safe_config_4147.json	current config, but not SSOT alone
realtime scheduler task	TraderBrainL0L2Hardening4147	current but failing
realtime runner	scripts/run_l0_l2_hardening_4147.py	current
realtime validator	scripts/validate_l0_l2_hardening_4147.py	current
worker recovery task	TraderBrainL0BackfillWorkerRecovery4148	current recovery, degraded/unknown
worker recovery runner	scripts/run_l0_backfill_worker_recovery_4148.py	current
worker recovery validator	scripts/validate_l0_backfill_worker_recovery_4148.py	current
Legacy / deprecated as current operating state
File	처리
configs/db_source_acquisition_scheduler.json	legacy config. 참고 가능하나 current scheduler SSOT 아님
scripts/start_l0_public_newswire_backfill.ps1	legacy single collector
scripts/start_l0_public_newswire_collector.ps1	legacy realtime collector
scripts/start_l0_prioritized_backfills.ps1	legacy mixed launcher
data/artifacts/l0_bar_full_backfill/background_process_5m.json	non-current PID artifact unless explicitly referenced by contract
data/artifacts/l0_bar_daily_full_backfill/background_process.json	non-current PID artifact unless explicitly referenced by contract

중요: raw data는 삭제하지 않습니다.
legacy 처리 대상은 collector, launcher, PID, config의 “current 여부”이지 원천 데이터가 아닙니다.

4. Implementation Plan
최소 구현 단위

TASK-4187은 아래 5개만 만들거나 수정하면 충분합니다.

1. ops/l0_operating_contract.yaml
2. scripts/build_l0_operating_status_4187.py
3. scripts/validate_l0_operating_contract_4187.py
4. data/artifacts/l0_operating_status/*
5. ops/task_registry.yaml + ops/doc_registry.yaml 업데이트

선택적으로 ops/task_profiles.yaml의 L0_L1_DATA_PIPELINE에 이 validator를 required check로 추가합니다.

4.1 Add scripts/build_l0_operating_status_4187.py
역할

여러 파일을 흩어져 읽는 대신, 이 builder 하나가 current L0 status를 생성합니다.

입력
ops/l0_operating_contract.yaml
data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json
data/artifacts/l0_public_newswire_backfill_shards/background_process.json
data/artifacts/l0_public_market_macro_news_backfill/background_process.json
configs/l0_realtime_operational_safe_config_4147.json
Windows Task Scheduler query result
해야 할 일
1. contract 로드
2. active artifact 존재 여부 확인
3. aggregate progress 로드
4. background PID alive/dead 확인
5. active worker PID/heartbeat 확인
6. scheduler task 존재 여부 확인
7. scheduler status / last result / next run time 수집
8. config runtime_boundary.scheduler_task_name과 contract 비교
9. legacy path 존재 여부를 current와 분리 표시
10. derived_runtime_status 계산
11. current_l0_status.json 생성
12. current_l0_context.md 생성
13. l0_operating_manifest.json 생성
핵심 판정 로직
aggregate_status == RUNNING
AND launcher_pid_alive == false
AND active_workers_alive == 0
=> BLOCKED_DEAD_PID
scheduler_task exists
AND status == Ready
AND last_result != 0
=> BLOCKED_SCHEDULER_FAILED

단, Windows Task Scheduler의 267009 / 0x41301 같은 running code는 별도 해석해야 합니다.
즉, 모든 non-zero를 무조건 실패로 보면 안 되고, running/success/failure code를 명시적으로 분리해야 합니다.

4.2 Add scripts/validate_l0_operating_contract_4187.py
역할

L0 closeout gate입니다.

이 validator는 단순히 “파일이 있음”을 보는 것이 아니라, L0가 어떤 상태인지 정확히 말하는지를 검증해야 합니다.

모드 제안
Bash
python scripts/validate_l0_operating_contract_4187.py --mode health
python scripts/validate_l0_operating_contract_4187.py --mode harness --expect-blocked
모드 의미
Mode	목적	현재 상태에서 기대
health	L0가 실제 healthy인지 검증	fail
harness --expect-blocked	harness가 blocker를 정확히 감지하는지 검증	pass 가능

이 구분이 중요합니다.

현재는 BW/PRN pending, dead PID, failed scheduler가 있으므로 health가 통과하면 안 됩니다.
하지만 TASK-4187 자체는 “그 blocker를 정확히 드러내는 harness 구현”이므로 harness --expect-blocked는 통과할 수 있습니다.

4.3 Update existing validators only minimally

기존 validator를 크게 고치기보다, TASK-4187 validator가 이들을 호출하거나 결과를 참조하는 구조가 좋습니다.

재사용 대상:

scripts/validate_l0_public_newswire_sharded_backfill.py
scripts/validate_l0_l2_hardening_4147.py
scripts/validate_l0_backfill_worker_recovery_4148.py

단, 이 세 validator가 각각 PASS/WARN/FAIL을 내더라도 최종 L0 판정은 다음이 합니다.

scripts/validate_l0_operating_contract_4187.py
4.4 Update registries

필수 업데이트:

ops/task_registry.yaml
ops/doc_registry.yaml

권장 업데이트:

ops/task_profiles.yaml

L0_L1_DATA_PIPELINE profile에 다음 required check를 추가합니다.

YAML
required_checks:
  - python scripts/validate_l0_operating_contract_4187.py --mode harness --expect-blocked

또는 health를 요구하는 task에서는:

YAML
required_checks:
  - python scripts/validate_l0_operating_contract_4187.py --mode health
5. Scheduler / Backfill / Realtime Model
5.1 Backfill과 realtime은 분리해야 합니다

현재 L0에는 두 종류의 일이 섞여 있습니다.

구분	목적	실패 의미
Historical backfill	과거 데이터 채우기	coverage blocker
Realtime scheduler	최신 데이터 유지	freshness blocker
Worker recovery	backfill worker 복구	operational support

이 셋을 하나의 “L0 running”으로 표현하면 안 됩니다.

5.2 Backfill model
Current backfill
public_newswire historical backfill
runner: scripts/run_l0_public_newswire_sharded_backfill.py
aggregate: data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json
상태 구분
BACKFILL_COMPLETE
BACKFILL_RUNNING_HEALTHY
BACKFILL_RUNNING_DEGRADED
BACKFILL_BLOCKED_DEAD_PID
BACKFILL_BLOCKED_PENDING_NOT_RUNNING
BACKFILL_BLOCKED_FAILED_UNITS

현재는 다음으로 판정해야 합니다.

BACKFILL_BLOCKED_DEAD_PID
+
BACKFILL_INCOMPLETE

이유:

aggregate status = RUNNING
launcher alive = false
active workers recorded = 3
dead active workers = 3
pending_units = 1818
5.3 Realtime model
Current realtime / L0-L2 scheduled loop
config: configs/l0_realtime_operational_safe_config_4147.json
scheduler task: TraderBrainL0L2Hardening4147
runner: scripts/run_l0_l2_hardening_4147.py

현재 task는 존재하지만:

Last Result = 1
Status = Ready

따라서 건강 상태는:

REALTIME_BLOCKED_SCHEDULER_FAILED

입니다.

TraderBrainL0Realtime 같은 이름의 task가 없다는 사실은 그 자체로 fail이 아닙니다.
다만 contract에 current task로 적힌 이름이 없으면 fail입니다.

5.4 Worker recovery model

현재 recovery task:

TraderBrainL0BackfillWorkerRecovery4148
Status: Running
Last Result: -2147020576

이건 즉시 healthy로 보면 안 됩니다.

판정은 이렇게 해야 합니다.

조건	판정
Running이고 현재 heartbeat/progress가 확인됨	RECOVERY_RUNNING
Running이지만 progress/heartbeat 불명	RECOVERY_DEGRADED
Ready이고 last result non-success	RECOVERY_FAILED
task 없음	RECOVERY_MISSING

현재 제공 증거만 보면:

RECOVERY_DEGRADED_OR_UNKNOWN

으로 두는 것이 안전합니다.

5.5 Dead PID / stale heartbeat 처리

원칙은 단순해야 합니다.

PID file exists ≠ alive
PID alive ≠ correct process
aggregate RUNNING ≠ operationally running

builder는 최소한 아래를 확인해야 합니다.

1. PID 존재 여부
2. OS process alive 여부
3. 가능하면 command/script path 일치 여부
4. heartbeat/update timestamp stale 여부
5. aggregate active worker와 실제 worker alive 수 비교

판정 규칙:

aggregate RUNNING + launcher dead + active worker alive 0
=> hard fail
heartbeat stale but PID alive
=> warning 또는 degraded
PID alive but command line mismatch
=> hard fail 또는 unknown blocker

PID 재사용 가능성이 있으므로, 가능하면 process command line에 expected script name이 포함되는지 확인해야 합니다.

6. Legacy Cleanup Model
6.1 삭제하지 말고 “current 아님”을 명시

TASK-4187에서 raw data를 삭제하면 안 됩니다.

해야 할 일은 삭제가 아니라:

1. legacy path registry에 등록
2. current_l0_context.md에 “do not use as current”로 노출
3. validator가 contract 밖 legacy path를 current로 참조하면 fail
4. 기존 script 상단에 legacy comment 추가 가능
6.2 Legacy script 상단 주석

PowerShell legacy script에는 상단에 다음 주석을 추가할 수 있습니다.

PowerShell
# LEGACY_RUNTIME_ENTRYPOINT
# Superseded by TASK-4187 L0 operating contract.
# Do not treat this script as current L0 runtime unless ops/l0_operating_contract.yaml explicitly references it.

Python legacy script라면:

Python
실행됨
# LEGACY_RUNTIME_ENTRYPOINT
# Superseded by TASK-4187 L0 operating contract.
# Do not treat this script as current L0 runtime unless ops/l0_operating_contract.yaml explicitly references it.

주의: script 동작을 깨지 않도록 주석만 추가합니다.

6.3 Old config 처리

configs/db_source_acquisition_scheduler.json은 삭제하지 않습니다.

다만 contract와 context에 이렇게 명시합니다.

configs/db_source_acquisition_scheduler.json
= legacy/conservative scheduler config
= not current L0 runtime SSOT
= do not use for current enabled/disabled judgment

JSON 구조를 직접 수정하면 기존 reader가 깨질 수 있으므로, 가능하면 외부 contract에서 legacy로 표시하는 방식이 안전합니다.

6.4 Old PID artifact 처리

old PID 파일도 삭제하지 않습니다.

다만 아래 규칙을 적용합니다.

contract에 없는 PID artifact는 current runtime health에 사용 금지

예:

data/artifacts/l0_bar_full_backfill/background_process_5m.json
data/artifacts/l0_bar_daily_full_backfill/background_process.json

이 파일들이 dead라고 해서 current public newswire health를 망치면 안 됩니다.
반대로 이 파일들이 alive라고 해서 current L0가 healthy라고 봐도 안 됩니다.

7. Validator / Closeout Gate
7.1 Hard-fail해야 하는 것

아래는 반드시 hard fail입니다.

Condition	Fail code
ops/l0_operating_contract.yaml 없음	L0_CONTRACT_MISSING
current status/context 생성 실패	L0_STATUS_BUILD_FAILED
current context stale	L0_CONTEXT_STALE
active artifact path 없음	L0_ACTIVE_ARTIFACT_MISSING
aggregate RUNNING인데 launcher PID dead	L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD
aggregate RUNNING인데 active worker 전부 dead	L0_ACTIVE_WORKERS_DEAD
contract scheduler task가 없음	L0_SCHEDULER_TASK_MISSING
scheduler last result failed	L0_SCHEDULER_LAST_RESULT_FAILED
config scheduler name과 contract scheduler name 불일치	L0_CONFIG_SCHEDULER_MISMATCH
active config가 legacy path를 가리킴	L0_ACTIVE_CONFIG_POINTS_TO_LEGACY
public newswire aggregate corrupt/unreadable	L0_AGGREGATE_UNREADABLE
validator가 blocker를 감지하지 못함	L0_FALSE_HEALTH_PASS

현재 상태에서는 최소 아래 fail이 나와야 정상입니다.

L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD
L0_ACTIVE_WORKERS_DEAD
L0_PUBLIC_NEWSWIRE_BACKFILL_INCOMPLETE
L0_SCHEDULER_LAST_RESULT_FAILED
7.2 Warning이어야 하는 것
Condition	Warning
legacy script 존재	warning only
legacy config 존재	warning only
old PID file dead but contract 밖	warning or ignored
stale_workers 존재하지만 active worker는 alive	warning
recovery task running but previous last result non-success	warning/degraded
old expected scheduler names not found but contract에 없음	warning 또는 ignored

예를 들어:

TraderBrainL0Realtime not found

이건 contract에 current task로 지정되어 있지 않다면 hard fail이 아닙니다.

7.3 Explicit blocker로 허용해야 하는 것

아래는 “구현 실패”가 아니라 명시적 L0 blocker 상태로 허용할 수 있습니다.

Blocker	의미
BW pending units	historical backfill incomplete
PRN pending/partial units	historical backfill incomplete
L0 realtime scheduler failed	freshness blocker
worker recovery degraded	operational blocker
context stale	closeout blocker
L0-L2 handoff failed	downstream handoff blocker

중요한 차이는 이것입니다.

허용 가능한 blocker = validator가 정확히 BLOCKED라고 말함
허용 불가능한 blocker = validator가 PASS라고 착각함

TASK-4187의 성공 조건은 L0를 healthy로 만드는 것이 아니라, L0가 blocked이면 blocked라고 일관되게 말하게 만드는 것입니다.

8. Current Expected Verdict After TASK-4187

TASK-4187 구현 직후 기대 상태는 다음이어야 합니다.

TASK-4187 harness implementation:
PASS_WITH_EXPLICIT_BLOCKERS

L0 health:
BLOCKED

L0 public newswire:
BLOCKED_DEAD_PID_AND_INCOMPLETE

GN:
COMPLETE

BW:
INCOMPLETE_BLOCKER

PRN:
INCOMPLETE_BLOCKER

Realtime scheduler:
BLOCKED_LAST_RESULT_FAILED

Legacy confusion:
CONTROLLED_BY_CONTRACT

즉, TASK-4187이 끝났다고 해서 L0가 건강해지는 것은 아닙니다.
대신 더 이상 “죽은 RUNNING”을 healthy로 착각하지 않게 됩니다.

9. Codex Final Implementation Prompt

아래를 Codex에 그대로 주면 됩니다.

TASK-4187 — Durable L0 Operating Harness / Contract / Validator

You are working in the local uncommitted repository. Do not read GitHub as current truth. Do not scan the whole repository by default. Follow AGENTS.md, ops/task_profiles.yaml, ops/doc_registry.yaml, and ops/task_registry.yaml.

Hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- No trading signals, ranking, sizing, order intent, or strategy acceptance
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence

Goal:
Create a durable Layer 0 operating harness so every new Codex session can identify:
1. current L0 operating contract
2. current public newswire backfill state
3. current realtime scheduler state
4. current worker recovery state
5. active vs legacy L0 files
6. validator verdict for L0 health and closeout

Do not delete raw data. Do not rewrite collectors. Do not introduce Airflow, Celery, Kubernetes, graph DB, vector DB, or LLM inference.

Current local evidence:
- public newswire aggregate:
  data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json
  status RUNNING, progress_pct 55.6693, completed 2283, pending 1818, failed 0, partial 56
  BW pending 1693, GN pending 0, PRN pending 125
- public newswire background launcher:
  data/artifacts/l0_public_newswire_backfill_shards/background_process.json
  pid 16236, alive false
- realtime config:
  configs/l0_realtime_operational_safe_config_4147.json
  runtime_boundary.scheduler_task_name = TraderBrainL0L2Hardening4147
- current scheduler tasks:
  TraderBrainL0L2Hardening4147 exists, Status Ready, Last Result 1, Next Run Time present
  TraderBrainL0BackfillWorkerRecovery4148 exists, Status Running, Last Result -2147020576
- legacy/non-current files:
  configs/db_source_acquisition_scheduler.json
  scripts/start_l0_public_newswire_backfill.ps1
  scripts/start_l0_public_newswire_collector.ps1
  scripts/start_l0_prioritized_backfills.ps1
  data/artifacts/l0_bar_full_backfill/background_process_5m.json
  data/artifacts/l0_bar_daily_full_backfill/background_process.json

Implement:

1. Add ops/l0_operating_contract.yaml

It must define:
- contract_version
- task_id TASK-4187
- hard_state
- active public_newswire runner/aggregator/validator/progress/background_process paths
- active realtime config/task/runner/validator paths
- active worker recovery task/runner/validator paths
- health thresholds
- status semantics
- legacy paths that must not be treated as current

2. Add scripts/build_l0_operating_status_4187.py

The builder must:
- load ops/l0_operating_contract.yaml
- read the active aggregate_progress.json
- read active background_process.json
- check PID alive/dead using local OS process inspection
- when possible, check command line/script identity to reduce PID reuse risk
- inspect worker/active/stale state available from aggregate/shard artifacts
- query Windows Task Scheduler for contract scheduler tasks
- decode scheduler success/running/failure clearly; do not treat recognized running code as failure
- compare configs/l0_realtime_operational_safe_config_4147.json runtime_boundary.scheduler_task_name with contract current realtime task
- mark legacy paths as legacy only; do not use them as current health
- write:
  data/artifacts/l0_operating_status/current_l0_status.json
  data/artifacts/l0_operating_status/current_l0_context.md
  data/artifacts/l0_operating_status/l0_operating_manifest.json

The builder must derive:
- overall_verdict
- public_newswire derived_runtime_status
- per-source progress BW/GN/PRN
- pid_status
- scheduler_status
- config_alignment
- blockers
- warnings
- legacy_runtime_risk

Important derived rule:
If aggregate says RUNNING but launcher PID is dead and no active workers are alive, derived runtime status must be BLOCKED_DEAD_PID, not RUNNING.

3. Add scripts/validate_l0_operating_contract_4187.py

The validator must support:
- --mode health
- --mode harness
- --expect-blocked

Behavior:
- health mode exits nonzero if L0 is blocked
- harness --expect-blocked exits zero only if the current known blockers are explicitly detected and reported
- fail if contract missing
- fail if current_l0_status.json missing/corrupt
- fail if current_l0_context.md missing/stale
- fail if aggregate says RUNNING but PID/worker reality is dead
- fail if current scheduler task from contract is missing
- fail if realtime config scheduler task and contract scheduler task disagree
- fail if scheduler last result is failure
- fail if legacy paths are treated as current active paths
- warn, but do not fail, merely because legacy files exist
- do not classify missing/stale/incomplete data as negative evidence

4. Mark legacy runtime entrypoints safely

Do not delete or move raw data.
Add only safe comments to legacy scripts if feasible:
- scripts/start_l0_public_newswire_backfill.ps1
- scripts/start_l0_public_newswire_collector.ps1
- scripts/start_l0_prioritized_backfills.ps1

Comment:
LEGACY_RUNTIME_ENTRYPOINT. Superseded by TASK-4187 L0 operating contract. Do not treat as current L0 runtime unless ops/l0_operating_contract.yaml explicitly references it.

Do not modify configs/db_source_acquisition_scheduler.json if doing so risks breaking readers. Instead mark it legacy in ops/l0_operating_contract.yaml and generated current_l0_context.md.

5. Update registries

Update:
- ops/task_registry.yaml
- ops/doc_registry.yaml

If appropriate, update ops/task_profiles.yaml for L0_L1_DATA_PIPELINE to require:
python scripts/validate_l0_operating_contract_4187.py --mode harness --expect-blocked

Do not create markdown reports outside:
docs/reports/task_4187_l0_operating_harness/

Create a concise implementation report there if the project convention requires it.

Validation commands to run:

python scripts/build_l0_operating_status_4187.py --contract ops/l0_operating_contract.yaml

python scripts/validate_l0_operating_contract_4187.py --mode harness --expect-blocked

python scripts/validate_l0_operating_contract_4187.py --mode health

python scripts/validate_l0_public_newswire_sharded_backfill.py

python scripts/validate_l0_l2_hardening_4147.py

python scripts/validate_l0_backfill_worker_recovery_4148.py

Expected result:
- harness --expect-blocked may pass if blockers are correctly reported
- health must fail or report BLOCKED because current L0 is not healthy
- current_l0_status.json must show public_newswire BLOCKED_DEAD_PID / INCOMPLETE
- GN must be COMPLETE
- BW and PRN must remain explicit incomplete blockers
- realtime scheduler must be BLOCKED or FAILED because Last Result = 1
- legacy scripts/configs must be visible as legacy, not current

Closeout:
- Do not claim L0 healthy.
- Do not claim deployment readiness.
- Do not move to L1/L2/L3/L4 readiness.
- Close only as TASK-4187 operating harness implemented with explicit L0 blockers detected.
Final Review Verdict
항목	판정
TASK-4187 필요성	필수 P0
현재 L0 health	BLOCKED
현재 public newswire backfill	RUNNING으로 표시되지만 운영상 dead/blocker
GN	완료
BW	주요 remaining blocker
PRN	remaining blocker
realtime scheduler	configured but failed
legacy 혼선	심각, contract로 고정 필요
추천 구현 범위	작고 적절함: YAML + Python builder + Python validator + generated JSON/MD
금지해야 할 방향	scheduler 대개편, 새 orchestrator, raw data 삭제, collector rewrite

정리하면, TASK-4187은 L0 문제를 직접 전부 해결하는 작업이 아니라, L0 문제가 다시 숨거나 오판되지 않게 만드는 운영 계층입니다. 이 작업이 끝나야 이후 BW/PRN backfill 재시작, scheduler repair, realtime freshness 복구 같은 작업들이 같은 기준으로 진행됩니다.
```

---

## File: docs/reports/task_4190_l0_backfill_realtime_scheduler_stabilization/report.md

```md
# TASK-4190 L0 Backfill Realtime Scheduler Stabilization

## Conclusion

TASK-4190 installed the L0 operating harness. It does not claim L0 is healthy.

Current L0 verdict is `BLOCKED`.

The important improvement is that the blocker is now explicit and reusable by future Codex sessions:

- `ops/l0_operating_contract.yaml` is the current L0 SSOT.
- `data/artifacts/l0_operating_status/current_l0_status.json` is the current machine-readable state.
- `data/artifacts/l0_operating_status/current_l0_context.md` is the read-first human context.
- `scripts/validate_l0_operating_contract_4190.py` is the L0 closeout gate.

## Current L0 State

| Area | Status | Meaning |
|---|---|---|
| public newswire backfill | `BLOCKED_DEAD_PID` + incomplete | aggregate says RUNNING, but launcher PID is dead |
| GlobeNewswire | complete | no pending units |
| BusinessWire | incomplete | main remaining backfill blocker |
| PRNewswire | incomplete | pending/partial remains |
| realtime scheduler | failed | `TraderBrainL0L2Hardening4147` last result is failure |
| daily/5m backfill PID | warning | PID files exist but processes are dead |
| legacy runtime paths | warning | preserved, but marked non-current |

## What Changed

| Change | Purpose |
|---|---|
| Added `ops/l0_operating_contract.yaml` | Defines active L0 lanes, current files, legacy paths, fail rules, and read-first order |
| Added `scripts/build_l0_operating_status_4190.py` | Builds one current L0 status/context from scattered artifacts |
| Added `scripts/validate_l0_operating_contract_4190.py` | Fails health when L0 is blocked; passes harness when known blockers are correctly detected |
| Marked legacy L0 launchers | Prevents old scripts from being mistaken as current runtime |
| Added context bundle config | Lets future sessions load the current L0 operating context |
| Added `l0_operating_contract_harness` profile check | Makes L0 operating-contract validation part of L0/L1 pipeline expectations |

## GPT Pro Review

GPT Pro agreed the root problem is not lack of another collector. The root problem is that L0 health was split across progress files, PID files, scheduler state, configs, and legacy scripts without one operating contract.

GPT recommended the small repo-native solution implemented here:

1. YAML contract
2. Python status builder
3. Python validator
4. generated JSON/Markdown context
5. legacy marking without deleting raw data

## Safety Boundary

Strategy: `NOT_ACCEPTED`

Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`

Real Capital: `FORBIDDEN`

No broker mutation, live order, paper promotion, trading signal, ranking, sizing, or order logic was added.


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

  TASK_4190:
    task_id: TASK-4190
    profile: L0_L1_DATA_PIPELINE
    max_tokens: 24000
    must_include:
      - AGENTS.md
      - ops/task_profiles.yaml
      - ops/context_bundles.yaml
      - ops/l0_operating_contract.yaml
      - data/artifacts/l0_operating_status/current_l0_status.json
      - data/artifacts/l0_operating_status/current_l0_context.md
      - data/artifacts/l0_operating_status/l0_operating_manifest.json
      - configs/l0_realtime_operational_safe_config_4147.json
      - docs/reports/task_4190_l0_backfill_realtime_scheduler_stabilization/report.md
    optional_include:
      - docs/reports/task_4190_l0_backfill_realtime_scheduler_stabilization/gpt_response.md
    exclude:
      - docs/archive/**
      - node_modules/**
      - db/**
      - secrets/**

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

## File: ops/l0_operating_contract.yaml

```yaml
version: 1
task_id: TASK-4190
title: L0 Backfill Realtime Scheduler Stabilization Contract
status: ACTIVE
profile: L0_L1_DATA_PIPELINE
updated_at: "2026-07-01"
purpose:
  - Define the current Layer 0 operating truth for new Codex sessions.
  - Separate current runtime health from historical progress artifacts.
  - Prevent legacy collectors, stale PID files, or failed schedulers from being treated as healthy.
hard_state:
  strategy: NOT_ACCEPTED
  deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
  real_capital: FORBIDDEN
  broker_mutation_permitted: 0
  live_order_permitted: 0
  paper_promotion_permitted: 0
  missing_or_stale_data_semantics: UNKNOWN_OR_BLOCKER_NOT_NEGATIVE
read_first_order:
  - ops/l0_operating_contract.yaml
  - data/artifacts/l0_operating_status/current_l0_status.json
  - data/artifacts/l0_operating_status/current_l0_context.md
  - data/artifacts/l0_operating_status/l0_operating_manifest.json
current_outputs:
  status_json: data/artifacts/l0_operating_status/current_l0_status.json
  context_markdown: data/artifacts/l0_operating_status/current_l0_context.md
  manifest_json: data/artifacts/l0_operating_status/l0_operating_manifest.json
active_lanes:
  public_newswire_backfill:
    role: historical_backfill
    provider: public_newswire_feeds
    runner: scripts/run_l0_public_newswire_sharded_backfill.py
    aggregate_progress: data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json
    background_process: data/artifacts/l0_public_newswire_backfill_shards/background_process.json
    inventory: data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json
    validator: scripts/validate_l0_public_newswire_sharded_backfill.py
    health_rule: aggregate_progress_is_progress_only_runtime_health_requires_pid_and_worker_reality
  public_market_macro_news_backfill:
    role: historical_backfill
    provider: public_market_macro_news_feeds
    background_process: data/artifacts/l0_public_market_macro_news_backfill/background_process.json
  daily_bars_backfill:
    role: historical_backfill_and_realtime_continuity
    provider: market_bar_daily_proxy
    background_process: data/artifacts/l0_bar_daily_full_backfill/background_process.json
  five_min_bars_backfill:
    role: historical_backfill_and_realtime_continuity
    provider: market_bar_5m_proxy
    background_process: data/artifacts/l0_bar_full_backfill/background_process_5m.json
  realtime_hardening_loop:
    role: realtime_incremental_collection_and_l1_l2_refresh
    config: configs/l0_realtime_operational_safe_config_4147.json
    scheduler_task: TraderBrainL0L2Hardening4147
    scheduler_script: scripts/run_l0_l2_hardening_once_4147.ps1
    runner: scripts/run_l0_l2_hardening_4147.py
    validator: scripts/validate_l0_l2_hardening_4147.py
    expected_interval_minutes: 15
  backfill_recovery_loop:
    role: backfill_worker_recovery_guard
    scheduler_task: TraderBrainL0BackfillWorkerRecovery4148
    scheduler_script: scripts/run_l0_backfill_worker_recovery_once_4148.ps1
    runner: scripts/run_l0_backfill_worker_recovery_4148.py
    validator: scripts/validate_l0_backfill_worker_recovery_4148.py
legacy_runtime_entrypoints:
  - path: configs/db_source_acquisition_scheduler.json
    reason: conservative historical scheduler config; not current L0 runtime truth
  - path: scripts/start_l0_public_newswire_backfill.ps1
    reason: legacy single newswire backfill launcher; superseded by sharded runner
  - path: scripts/start_l0_public_newswire_collector.ps1
    reason: legacy newswire collector launcher; not current runtime truth
  - path: scripts/start_l0_prioritized_backfills.ps1
    reason: legacy mixed launcher; not current runtime truth
  - path: data/artifacts/l0_public_newswire_backfill/background_process.json
    reason: legacy single-run PID artifact; sharded background_process is current
hard_fail_rules:
  - code: L0_CONTRACT_MISSING
    condition: ops/l0_operating_contract.yaml missing or invalid
  - code: L0_STATUS_BUILD_FAILED
    condition: current L0 status cannot be generated
  - code: L0_CONTEXT_STALE
    condition: generated L0 context is missing or stale
  - code: L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD
    condition: public newswire aggregate status is RUNNING but launcher PID is dead
  - code: L0_PUBLIC_NEWSWIRE_INCOMPLETE
    condition: public newswire pending or partial units remain
  - code: L0_REALTIME_SCHEDULER_MISSING
    condition: current realtime scheduler task is missing
  - code: L0_REALTIME_SCHEDULER_LAST_RESULT_FAILED
    condition: current realtime scheduler last result is a failure result
  - code: L0_REALTIME_CONFIG_SCHEDULER_MISMATCH
    condition: realtime config runtime boundary scheduler task differs from contract
  - code: L0_LEGACY_PATH_TREATED_AS_CURRENT
    condition: a legacy runtime entrypoint is used as an active lane
warning_rules:
  - code: L0_LEGACY_PATH_PRESENT
    condition: legacy file exists but is not treated as current
  - code: L0_RECOVERY_TASK_RUNNING_WITH_PREVIOUS_NON_SUCCESS_RESULT
    condition: recovery task is running but last result is non-success
  - code: L0_BACKGROUND_PID_DEAD
    condition: non-critical lane background PID is dead
  - code: L0_STALE_WORKERS_PRESENT
    condition: aggregate records stale workers
validation:
  builder: scripts/build_l0_operating_status_4190.py
  validator: scripts/validate_l0_operating_contract_4190.py
  harness_command: python scripts/validate_l0_operating_contract_4190.py --mode harness --expect-blocked
  health_command: python scripts/validate_l0_operating_contract_4190.py --mode health

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
      - l0_operating_contract_harness

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
