# TASK-4148 L0 Backfill Worker Recovery And Health Gate

## 결론

TASK-4148은 public newswire와 public market/macro news 백필 worker가 죽어 있는데도 L1/L2가 L0를 건강하다고 볼 수 있는 문제를 막기 위한 작업이다.

현재 기준으로 두 critical lane은 모두 살아 있고, PID가 실제 해당 collector인지 command line 기준으로도 확인된다. Windows Task Scheduler guard도 등록만 된 상태가 아니라 수동 실행 `Last Result=0`까지 확인됐다.

| lane | pid alive | pid owner verified | progress age min | blocker |
|---|---:|---:|---:|---|
| `public_market_macro_news_backfill` | 1 | 1 | 1 |  |

## 보강한 점

- `pid_recorded`만 믿지 않고 OS 기준 `pid_alive`를 확인한다.
- `pid_owner_verified`를 추가해 해당 PID가 실제 collector script인지 확인한다.
- 미완료 worker가 죽어 있으면 recovery guard가 기존 start script로 재기동한다.
- 오래 살아만 있고 진행 증거가 멈춘 worker는 stale-progress 후보로 잡는다.
- `current_status.json`의 critical lane 항목도 `pid_alive`, `pid_checked_at`, `worker_gate_state` 기준으로 갱신한다.
- synthetic stale-pid fixture를 추가해 실제 worker를 죽이지 않고 회귀 검증한다.
- Windows Task Scheduler `TraderBrainL0BackfillWorkerRecovery4148`를 15분 주기로 등록하고, wrapper 기반 실행으로 한글/공백 경로 quoting 문제를 제거했다.

## 최신 요약

- generated_at: `2026-07-01T15:28:28Z`
- after_pid_alive_lanes: `1`
- incomplete_dead_lanes: `[]`
- stale_progress_lanes: `[]`
- authority_flags_opened: `0`
- current_status_update: `{'updated': 1, 'path': 'data/artifacts/l0_collection_status/current_status.json', 'lanes': ['public_market_macro_news_backfill']}`

## GPT Pro 검토

- GPT Pro 응답 캡처 완료.
- GPT 판정: `PASS`, P0 없음.
- GPT P1 권고였던 stale-pid fixture, current_status 보강, PID ownership proof를 반영했다.
- GPT는 검토 의견이며 최종 source of truth는 로컬 validator와 산출물이다.

## 안전 경계

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation.
- No live order.
- No paper promotion.
- Missing/stale data remains `UNKNOWN/BLOCKER`, not negative evidence.
