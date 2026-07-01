# TASK-4159 L0 Public Newswire Controlled Acceleration

## 목적

BusinessWire / GlobeNewswire / PRNewswire 뉴스와이어 백필이 순차 병목과 stale worker 오판에 막히지 않도록 L0 sharded backfill 런처를 보강했다.

이번 작업은 수집 운영 개선이다. trading signal, order, broker mutation, paper/live promotion은 열지 않았다.

## 구현 내용

| 영역 | 적용 내용 |
|---|---|
| source lane | `source_base_lanes`와 `source_lane_caps`를 분리했다. 기본은 BW 2 / GN 1 / PR 1, cap은 BW 4 / GN 1 / PR 1이다. |
| 동적 재배분 | pending/running source가 없으면 lane을 반환하고, 반환 lane은 BusinessWire에 우선 배정되도록 했다. |
| source별 예산 | BW/GN/PR별 `max_fetches`, `max_items`, `request_sleep_seconds`, `max_worker_seconds`를 따로 받도록 했다. |
| stale 판단 | 단순 파일 mtime 대신 completed unit, active offset, row count, raw bytes, last successful fetch 변화를 progress로 본다. |
| dead lock 복구 | 죽은 PID가 RUNNING lock으로 남으면 `STALE_DEAD_PID_RECOVERED`로 닫고 새 worker를 띄울 수 있게 했다. |
| live lock 방어 | 이미 살아 있는 worker lock을 만나도 launcher 전체가 죽지 않고 해당 shard를 건너뛰도록 했다. |
| aggregate | source별 velocity/ETA, long-tail ETA, active/stale worker, partial shard, active offsets를 집계한다. |
| validator | dead PID RUNNING lock, active offset completed 오판, aggregate 필드 누락, safety flag nonzero 등을 검증한다. |
| controller | 매시간 BW4 승격 가능 여부를 판단하는 `controlled_acceleration_decision.json`을 남긴다. 기본은 dry-run이며 `-Apply` 없이는 런처를 바꾸지 않는다. |

## 현재 운영 상태

| 항목 | 값 |
|---|---:|
| aggregate status | RUNNING |
| progress | 45.8912% |
| completed / total | 1,882 / 4,101 |
| pending | 2,219 |
| rows | 140,664 |
| launcher PID | 25580 |
| monitor PID | 32548 |
| lane 상태 | BW 2 / GN 1 / PR 1 |

2026-07-01T01:03Z 기준 monitor PID는 `18404`로 재시작했다. 새 monitor는 controller 판단 파일도 매시간 갱신한다.

## 현재 source별 상태

| source | completed / total | pending | 현재 lane |
|---|---:|---:|---:|
| BusinessWire | 1,851 / 3,834 | 1,983 | 2 |
| GlobeNewswire | 15 / 126 | 111 | 1 |
| PRNewswire | 16 / 141 | 125 | 1 |

## 유지한 제한

| 제한 | 상태 |
|---|---|
| PRNewswire range split | 미구현. 아직 row progress 관찰이 우선이다. |
| sleep 0.5 | 미적용. 모든 source sleep 1.0 유지. |
| BusinessWire 6+ lane | 미적용. cap 4까지만 허용. |
| PRNewswire 2+ lane | 미적용. cap 1 유지. |
| BusinessWire daily split default | 미적용. 이번 작업에서는 기본 shard 구조를 바꾸지 않았다. |

## 남은 운영 판단

1. GlobeNewswire가 완료되면 dynamic rebalance에 의해 빈 lane이 BusinessWire로 넘어가야 한다.
2. 2시간 이상 429/timeout/empty/raw integrity 문제가 없으면 총 concurrency 5, BusinessWire 4 lane 구성을 별도 운영 조치로 열 수 있다.
3. PRNewswire는 unit completion보다 row/offset progress를 먼저 본다. range split은 아직 금지다.
4. 현재 controller 판단은 `BW4_BLOCKED`다. 이유는 `globenewswire_not_complete,stable_minutes_below_threshold`이며, failed shard는 validator가 PASS하는 한 절대 차단 조건이 아니라 경고로 둔다.
