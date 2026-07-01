# TASK-4149 GPT Pro 검토 요약

## 결론

GPT Pro의 결론은 명확하다.

Layer 3는 **매매 신호를 만드는 층이 아니라, L2가 넘긴 후보를 경제적 의미와 관계 그래프로 정리하는 진단 층**으로 시작해야 한다.

## GPT가 권고한 방향

| 항목 | 결론 |
|---|---|
| L3 목표 | L2 primitive/read-view를 사람이 검토 가능한 경제 의미, evidence edge, relation graph로 바꾸기 |
| 구현 방식 | 기존 `src/brain/l3` 전체 복구 금지. 새 L2 산출물에 맞춘 task-scoped bridge 우선 |
| 기존 L3 재사용 | 개념/용어는 재사용. old code wholesale restore는 금지 |
| L0 직접 읽기 | 금지. L3는 L2 산출물을 통해서만 읽어야 함 |
| L0 상태 사용 | `current_status.json`은 coverage context로만 사용 |
| 뉴스/매크로/newswire | trading feature 후보가 맞지만 signal/order가 아니라 diagnostic evidence candidate로 처리 |
| incomplete backfill | 부정 증거가 아니라 coverage gap/blocker |
| UNKNOWN mapping | active graph 금지. review queue로 분리 |
| stale row | risk/support가 아니라 blocker/gap/context |
| duplicate non-canonical | 독립 evidence edge 금지 |

## L3 핵심 기능

1. L2 read-view/artifact input bridge
2. L3 economic meaning record 생성
3. Evidence edge 생성
4. Relation graph aggregation
5. Coverage/blocker/gap ledger
6. Rejected/review queue
7. Validator로 L1/L2 우회, UNKNOWN mapping, stale/coverage 오해, order/signal 권한 개방 차단

## Codex 자체 검수

GPT 권고는 현재 repo 상태와 맞다.

- 현재 `src/brain/l3/*`, `src/l2/*`는 tracked deletion 상태가 많다.
- 예전 L3 adapter는 `src.l2.contracts.L2PrimitiveFact`에 기대고 있는데, 현재 L2는 artifact/read-view 중심으로 보강됐다.
- 따라서 old L3를 통째 복구하면 새 L0-L2 handoff를 우회하거나 깨뜨릴 수 있다.
- 우선은 `TASK-4149` 또는 다음 구현 task에서 task-scoped L3 bridge를 만드는 것이 더 안전하다.

## 이번 task의 범위

이번 task는 **L3 목표와 핵심 기능 정의 + GPT Pro 검수**까지로 닫는다.

실제 구현은 다음 task에서 다음 범위로 진행하는 것이 맞다.

- `src/brain/l3_diagnostic_strategy_view_bootstrap/`
- `scripts/build_l3_diagnostic_strategy_view_4149.py`
- `scripts/validate_l3_diagnostic_strategy_view_4149.py`
- `configs/l3_diagnostic_strategy_view_bootstrap_4149.json`
- `data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/`

## 안전 경계

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation.
- No live order.
- No paper promotion.
- Missing/stale data remains `UNKNOWN/BLOCKER`.
- No signal, rank, sizing, order, paper/live, broker, strategy acceptance, or deployment authority opened.
