# TASK-4169 Problem Solution Direction GPT Review

## 결론

GPT 검수 결과, 다음 순서가 맞다.

1. L0 미완료/실패 복구
2. L1 unmapped 회수
3. recall/entity review와 feature gap 정리
4. L4 relation taxonomy와 contradiction scanner 확장
5. event identity 안정화

즉, L4 thesis나 signal로 바로 가는 것이 아니라, `L0/L1/L2가 넓게 먹고 L3/L4가 제대로 해석하는 상태`를 먼저 만드는 방향이다.

## 문제별 해결 방향

| 문제 | 해결 방향 | 우선순위 |
|---|---|---|
| L0 incomplete coverage 11,079 | BW/PRN/context/market macro terminal status 정리 | P0 |
| BW/PRN backfill incomplete | 기존 runner 유지, partial/stale/retry 추적 강화 | P0 |
| public market/macro `FAILED_RETRYABLE` | bounded retry 후 terminal blocker 또는 complete | P0 |
| Federal Register 2020-10 pending offset | offset 32 재요청, pagination proof 저장 | P0-fast |
| L1 blocked unmapped 3,999 | unmapped review pack, 후보 빈도표, deterministic alias/parser 확장 | P0 |
| recall/entity review pending 447 | 명시 decision state로 종료 | P1 |
| mapped but no feature 181 | feature builder/backfill 보강 | P1 |
| unsupported relation family 18,610 | frequency matrix 후 상위 family부터 diagnostic taxonomy 추가 | P1 |
| contradiction not scanned 11,079 | supported family부터 deterministic scanner 추가 | P1 |
| proto event identity 6,913 | deterministic event identity v1, LLM/cluster 병합 금지 | P2 |

## Codex 판단

GPT 의견은 타당하다. 특히 `L0_INCOMPLETE_COVERAGE`와 `L1_BLOCKED_UNMAPPED_ROWS_PRESENT`가 upstream blocker이므로, L4 blocker를 억지로 줄이는 작업보다 먼저 처리해야 한다.

다음 구현 후보는 `TASK-4170 L0 Source Recovery and Terminal Status Cleanup`이다. 이유는 L0 미완료 상태가 남아 있으면 L4 contradiction scan이나 thesis quality를 고쳐도 clean verdict를 만들 수 없기 때문이다.

## Safety

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation.
- No live order.
- No paper promotion.
- Missing/stale/incomplete data remains `UNKNOWN/BLOCKER`, not negative evidence.

## Chrome GPT

- relay mode: `single_gpt_consult`
- GPT capture status: captured
- tab cleanup status: `closed_or_released_by_finalize`
