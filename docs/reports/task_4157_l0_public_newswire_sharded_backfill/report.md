# TASK-4157 L0 Public Newswire Sharded Parallel Backfill

## 결론

Public newswire 백필을 기존 순차 처리에서 shard 병렬 처리 구조로 바꿨다. 기존 legacy 완료분은 유지하고, 남은 archive 단위만 BusinessWire/GlobeNewswire/PRNewswire shard로 나눠 병렬 백그라운드 수집하도록 구성했다.

현재 상태:

- 수집 런처 PID: `34700`
- 진행률 모니터 PID: `22868`
- 실행 모드: `stable`, concurrency `4`
- 전체 archive 단위: `4,101`
- 완료 archive 단위: `1,771`
- 잔여 archive 단위: `2,330`
- 진행률: `43.1846%`
- raw/L1 event 집계: `32,073`
- 상태: `RUNNING`

## 왜 고쳤나

기존 구조는 `prnewswire -> globenewswire -> businesswire`처럼 사실상 한 줄로 오래 도는 구조라 BusinessWire 월/일 단위에서 막히면 전체 백필이 매우 느렸다. 이번 수정은 아래 방향이다.

- BusinessWire는 연/월 shard 안에서 일별 sitemap을 처리한다.
- GlobeNewswire는 월 shard로 처리한다.
- PRNewswire는 `recent` 페이지와 과거 월 archive를 분리한다.
- 각 shard는 state/progress/event/raw 경로를 따로 가져 서로 덮어쓰지 않는다.
- aggregate progress는 기존 완료분과 신규 shard 진행분을 같이 읽는다.
- short smoke는 완료로 오인하지 않고 `PARTIAL`로 남긴다.

## 백그라운드 실행

실제 수집:

```powershell
python scripts/run_l0_public_newswire_sharded_backfill.py --start-month 2016-01 --end-month 2026-06 --sources businesswire,globenewswire,prnewswire --mode stable --concurrency 4 --poll-seconds 10
```

진행률 모니터:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_l0_public_newswire_sharded_progress_monitor.ps1 -IntervalSeconds 3600 -MaxIterations 0
```

확인 위치:

- 수집 프로세스: `data/artifacts/l0_public_newswire_backfill_shards/background_process.json`
- 진행률: `data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json`
- 1시간 스냅샷: `data/artifacts/task_4157_l0_public_newswire_sharded_backfill/progress_snapshots/`
- 1시간 validator 결과: `data/artifacts/task_4157_l0_public_newswire_sharded_backfill/validation_snapshots/`
- monitor 상태: `data/artifacts/task_4157_l0_public_newswire_sharded_backfill/progress_monitor_status.json`

## 남은 리스크

BusinessWire 일부 sitemap은 빈 응답이나 느린 응답이 있다. 이것은 코드가 멈춘 것과 다르며, 현재는 shard별 state에 offset/완료 단위가 남는다. 완료율은 raw 파일이 생성되는 순간마다 오르지 않고, archive 단위가 끝날 때 올라간다.

`l1_unclassified_or_pending_count > 0` 경고는 남아 있다. 이 작업의 목적은 L0 수집 병렬화와 증거 남기기이므로, 뉴스/티커 의미 분류 품질 개선은 L1/L2 mapping 작업에서 이어서 처리해야 한다.

## 안전 경계

이 작업은 진단/수집 전용이다.

- real capital: forbidden
- broker mutation: forbidden
- live order: forbidden
- trade authority: none
- strategy acceptance: not accepted

