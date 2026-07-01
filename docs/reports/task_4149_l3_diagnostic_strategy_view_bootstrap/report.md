# TASK-4149 L3 Diagnostic Strategy View Bootstrap

## 결론

Layer 3로 넘어갈 수 있다. 다만 L3는 전략 실행층이 아니라 **진단용 경제 의미/관계 그래프 층**으로 시작해야 한다.

GPT Pro는 `Professional Backend Engineer` 역할로 검토했고, 결론은 `PASS_FOR_DESIGN_DIRECTION`이다.

핵심 권고는 다음과 같다.

1. 기존 `src/brain/l3` 코드를 통째로 복구하지 않는다.
2. 현재 L0-L2 산출물에 맞춘 task-scoped L3 bridge를 먼저 만든다.
3. L3는 L2 read-view/artifact만 읽고, L0 raw를 직접 읽지 않는다.
4. 뉴스/매크로/newswire는 trading feature 후보가 맞지만, L3에서는 signal/order가 아니라 diagnostic evidence candidate로만 처리한다.
5. incomplete backfill, UNKNOWN mapping, stale row, blocked packet은 부정 증거가 아니라 blocker/gap/review queue로 분리한다.

## L3 목표

L3의 목표는 L2가 넘긴 primitive/read-view 후보를 다음 형태로 바꾸는 것이다.

```text
L2 diagnostic/read candidate
-> L3 economic meaning
-> L3 evidence edge
-> L3 relation graph
-> blocker/gap/review queue
```

쉽게 말하면:

**뉴스/매크로/newswire 조각이 어떤 경제적 의미를 갖는지, 어떤 기업/섹터/테마와 연결되는지, 근거가 충분한지, 막힌 부분은 무엇인지를 사람이 검토할 수 있게 정리하는 층**이다.

## L3가 해야 하는 것

| 기능 | 의미 |
|---|---|
| L2 input bridge | L2 산출물만 읽고 L3 입력 객체로 정리 |
| Economic meaning | 사건을 `DEMAND`, `SUPPLY`, `GUIDANCE`, `RATES`, `MACRO_CONTEXT` 같은 경제 차원으로 분류 |
| Evidence edge | 사건과 기업/섹터/테마/매크로 노드의 관계를 만듦 |
| Relation graph | 같은 대상의 여러 evidence를 묶어 review state 생성 |
| Coverage/gap ledger | 백필 미완료, stale, missing, blocked를 명시 |
| Review queue | UNKNOWN mapping, non-canonical duplicate, L1 blocked row 분리 |
| Validator | L0 우회, signal/order, mapping 오염, stale 오해를 차단 |

## L3가 하면 안 되는 것

| 금지 | 이유 |
|---|---|
| BUY/SELL/HOLD/EXIT | L3는 매매 판단층이 아님 |
| rank/alpha/sentiment score | 아직 검증된 trading signal 아님 |
| expected/forward/realized return join | leakage 위험 |
| sizing/order intent | L5/L6 이후 영역 |
| paper/live/broker 권한 | 현재 hard state 위반 |
| old L3/L2 전체 복구 | 현재 L0-L2 산출물과 불일치 위험 |
| L0 raw 직접 소비 | L1/L2 gate 우회 |
| scheduler/DB migration/UI | TASK-4149 범위 초과 |

## 현재 L0-L2 기준

| 항목 | 상태 |
|---|---|
| L0 critical backfill workers | alive, PID owner verified |
| public newswire backfill | running, coverage incomplete |
| public market/macro backfill | running, coverage incomplete |
| L1 packets | 1944 wide packets, 1093 article packets |
| L2 admitted/review rows | 916 wide rows |
| L2 diagnostic feature rows | 1842 |
| newswire mapping queue | 198 |
| trading eligible rows | 0 |
| signal/order allowed rows | 0 |
| broker mutation permitted rows | 0 |

## GPT Pro 검토 결과

| 항목 | 값 |
|---|---|
| relay mode | `single_gpt_consult` |
| GPT role | `Professional Backend Engineer` |
| GitHub 사용 | 금지. 로컬 context packet 기준 |
| capture status | `CAPTURED` |
| response path | `docs/reports/task_4149_l3_diagnostic_strategy_view_bootstrap/gpt_response.md` |
| digest path | `docs/reports/task_4149_l3_diagnostic_strategy_view_bootstrap/gpt_review_digest_ko.md` |
| tab cleanup | `closed_or_released_by_finalize` |

## 다음 구현 범위

다음 task에서 구현할 경우 GPT 권고 범위는 다음이다.

```text
src/brain/l3_diagnostic_strategy_view_bootstrap/
  contracts.py
  l2_read_view_bridge.py
  coverage_policy.py
  economic_meaning_classifier.py
  evidence_edge_builder.py
  relation_graph_aggregator.py
  artifact_writer.py

scripts/build_l3_diagnostic_strategy_view_4149.py
scripts/validate_l3_diagnostic_strategy_view_4149.py
configs/l3_diagnostic_strategy_view_bootstrap_4149.json
tests/test_l3_diagnostic_strategy_view_bootstrap_4149.py
```

## 안전 경계

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation.
- No live order.
- No paper promotion.
- Missing/stale data remains `UNKNOWN/BLOCKER`.
- No signal, rank, sizing, order, broker, paper/live, strategy acceptance, or deployment authority opened.
