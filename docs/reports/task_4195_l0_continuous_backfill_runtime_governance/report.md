# TASK-4195 L0 Continuous Backfill Runtime Governance

## 결론

사용자 의도는 “오늘 밤만 백필”이 아니라 “백필은 끝날 때까지 계속 돌고, 실시간은 계속 돌며, 옛 스케줄러/죽은 PID/중복 런처가 운영을 흐리지 않게 하는 것”이었다. TASK-4195는 이 기준으로 L0 운영 구조를 다시 맞춘 작업이다.

## 현재 운영 구조

| 역할 | 현재 task | 주기 | 상태 |
|---|---|---:|---|
| 백필 지속 guard | `TraderBrainL0ContinuousBackfillGuard4195` | 5분 | Enabled, Last Result 0 |
| 실시간/L1-L2 refresh | `TraderBrainL0L2Hardening4147` | 15분 | Enabled, Last Result 0 |
| 구형 recovery | `TraderBrainL0BackfillWorkerRecovery4148` | disabled | Superseded |
| 구형 official loop | `Task3893OfficialBackfillAutoLoop` | disabled | Superseded |
| 구형 official worker/report | `Task3899FullOfficialBackfillWorker`, `Task3899FullOfficialBackfillProgressReport` | disabled | Superseded |

## 한 일

- `TASK-4193`의 12시간 임시 루프를 중지했다.
- `TASK-4195` one-shot guard wrapper와 installer를 추가했다.
- Windows Task Scheduler에 `TraderBrainL0ContinuousBackfillGuard4195`를 5분 주기로 등록했다.
- 4148/3893/3899 구형 스케줄러를 disabled로 내렸다.
- `ops/l0_operating_contract.yaml`의 current recovery loop를 4195로 교체했다.
- `scripts/build_l0_operating_status_4190.py`가 current backfill guard scheduler를 4195로 읽도록 갱신했다.

## 현재 백필 상태

| 소스 | 상태 |
|---|---:|
| public newswire | running, pending remains |
| market/macro news | running |
| daily bars | complete |
| 5m bars | running |

남은 `L0_PUBLIC_NEWSWIRE_INCOMPLETE`는 런타임 오류가 아니라 아직 백필이 덜 끝났다는 blocker다. 완료될 때까지 4195 guard가 런처/PID 상태를 계속 확인한다.

## 안전 경계

No broker mutation. No live order. No paper promotion. No real capital. Missing/stale/incomplete data는 UNKNOWN/BLOCKER로만 취급한다.
