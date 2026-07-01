# TASK-4168 L3 Coverage Gap Reason Narrowing & Newswire Recall Traceability

## 결론

TASK-4168은 L3/L4가 왜 막혔는지 “큰 이유”를 “다음 조치가 보이는 작은 이유”로 쪼개는 작업이다.

L3 coverage gap `4,627`개는 전부 L0/L1/L2 참조까지 추적 가능해졌다. L4의 `L3_COVERAGE_GAP` blocker가 `4,630`개인 것은 오류가 아니라, L3 row-level gap `4,627`개에 coverage-gap graph-level blocker `3`개가 추가된 정상 차이다.

## P0 결과

| 항목 | 결과 | 의미 |
|---|---:|---|
| L3 gap triage rows | 4,627 | 모든 L3 gap을 개별 행으로 정리 |
| TRACE_OK | 4,627 | L0/L1/L2 참조가 모두 연결됨 |
| L3/L4 count 차이 | 3 | coverage gap graph-level blocker 3개로 설명됨 |
| 뉴스와이어 failed units | 0 | failed shard는 현재 없음 |
| GN backfill | 126/126 | GlobeNewswire는 완료 |

## Gap Subreason

| 막힌 이유 | 수 | 쉬운 해석 |
|---|---:|---|
| `L1_BLOCKED_UNMAPPED_ROWS_PRESENT` | 3,999 | L1에서 아직 매핑 안 된 뉴스/소스 행이 남아 L2/L3가 막힘 |
| `RECALL_AND_ENTITY_REVIEW_PENDING` | 447 | recall review와 entity review가 둘 다 남아 feature 확정 전 |
| `NEWSWIRE_ENTITY_OR_ARTICLE_FEATURE_MISSING` | 181 | 뉴스와이어는 매핑됐지만 article/entity feature로 아직 못 올라감 |

## P1/P2 처리

| 우선순위 | 항목 | 처리 |
|---:|---|---|
| P1 | event identity audit | gap id 중복 0으로 audit pass. schema rewrite는 하지 않음 |
| P1 | L4 blocker taxonomy | global/local scope로 별도 taxonomy 산출 |
| P1 | macro/sector relation support | L2 feature admission 기준이 먼저라 deferred |
| P2 | contradiction scanner | event identity와 feature admission 안정화 전이라 deferred |
| P2 | five-minute downstream integration | L0 coverage 안정화 후 별도 작업 |
| P2 | collector speed retuning | TASK-4168 범위 밖. failed 0 상태라 별도 운영 task로 분리 |

## L0 상태 스냅샷

| 소스 | 현재 상태 | 조치 판단 |
|---|---|---|
| public newswire | RUNNING, 52.5482%, failed 0 | 계속 백그라운드 수집 |
| BusinessWire | 2013/3834 completed, pending 1821, partial 52 | 장기 병목. 별도 L0 운영 과제 |
| GlobeNewswire | 126/126 completed | 완료 |
| PRNewswire | 16/141 completed, pending 125, partial 11 | 계속 수집 |
| public context news | federal register 2020-10 pending offset 32 | explicit blocker로 기록 |
| public market/macro news | FAILED_RETRYABLE | 별도 운영 복구 과제 |

## 산출물

- `data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_l3_gap_triage.csv`
- `data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_l3_gap_triage.json`
- `data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_l3_l4_gap_reconciliation.json`
- `data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_l3_l4_gap_reconciliation_detail.csv`
- `data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_l4_blocker_taxonomy.csv`
- `data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_event_identity_audit.json`
- `data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_l0_status_snapshot.json`
- `data/artifacts/task_4168_l3_gap_reason_narrowing_recall_traceability/task_4168_p1_p2_priority_ledger.json`

## Safety

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation, no live order, no paper promotion.
- Missing or stale data remains `UNKNOWN/BLOCKER`, not negative evidence.
