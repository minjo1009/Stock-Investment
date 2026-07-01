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