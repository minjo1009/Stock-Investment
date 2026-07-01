# TASK-4193 L0 Overnight Backfill Completion Run

## 결론

이번 작업은 L0를 “보고서상 RUNNING인데 실제로는 죽어 있는 상태”에서 “밤새 감시하면서 죽으면 다시 켜는 상태”로 바꾼 작업이다.

현재 기준:

| 항목 | 상태 | 의미 |
|---|---:|---|
| overnight supervisor | alive | 5분마다 L0 백필 상태를 확인하고 죽은 러너를 재기동 |
| public newswire | alive | BusinessWire 4 lane + PRNewswire 1 lane으로 재기동 |
| market/macro news | alive | 기존 collector PID 확인됨 |
| daily bars | complete | 100%, dead PID는 완료 후 종료라 blocker 아님 |
| 5m bars | alive | 깨진 checkpoint 복구 후 재기동 |
| 4147 realtime hardening scheduler | Last Result 0 | 수동/스케줄러 실행 모두 PASS |
| 4148 backfill recovery scheduler | Last Result 0 | 스케줄러 실행 PASS |

## 중요한 조치

1. 뉴스와이어 sharded launcher가 죽어 있어 재기동했다.
   - 새 PID: `21952`
   - 설정: `businesswire=4`, `prnewswire=1`, sleep `1.0`

2. 5분봉 상태 파일이 전부 NUL 바이트로 깨져 있어 collector가 바로 종료되던 문제를 복구했다.
   - 깨진 `collector_state.json`, `collector_progress.json`는 삭제하지 않고 TASK-4193 백업 폴더에 보존했다.
   - 이벤트 로그의 마지막 5분봉 처리 위치 `FBIN:5m:2020-04-09:2020-08-06` 다음 블록부터 이어가게 복구했다.

3. supervisor를 백그라운드로 띄웠다.
   - PID: `16040`
   - 상태 파일: `data/artifacts/task_4193_l0_overnight_backfill_completion_run/supervisor_status.json`
   - 이벤트 파일: `data/artifacts/task_4193_l0_overnight_backfill_completion_run/supervisor_events.jsonl`

## 현재 남은 것

| 남은 것 | 현재 의미 |
|---|---|
| `L0_PUBLIC_NEWSWIRE_INCOMPLETE` | 오류가 아니라 아직 백필이 덜 끝났다는 뜻 |
| daily PID dead warning | 일봉은 100% 완료 후 종료된 상태라 실질 blocker 아님 |
| legacy path warning | 구형 파일이 남아 있다는 관리 경고 |
| stale worker warning | 과거 worker 기록이 남아 있다는 경고. 현재 launcher PID는 alive |

## 안전 경계

No broker mutation. No live order. No paper promotion. No real capital. Missing/stale/incomplete data는 계속 UNKNOWN/BLOCKER로만 취급한다.
