# TASK-4151 L3 Relation Graph Goal Expansion GPT Pro Review

## 작업 목적

L3 relation graph가 27개뿐인 현재 상태가 정상인지 검수했다. GPT Pro에게 현재 L0/L1/L2/L3 산출물 수치, source별 상태, L3 산출물 구조, 안전 경계를 제공하고, professional backend engineer 및 professional trader 관점으로 L3 relation graph를 어떻게 고도화해야 하는지 검토받았다.

## 제공한 현재 상태

| 구분 | 현재 상태 |
|---|---|
| L0 public newswire backfill | RUNNING, 약 42.96% |
| L0 public market/macro news backfill | RUNNING, 약 33.78% |
| L0 public context news backfill | RUNNING, 약 99.33% |
| L1 article packets | 1,093 |
| L2 diagnostic feature rows | 1,842 |
| TASK-4150 L3 meanings | 2,780 |
| TASK-4150 L3 evidence edges | 2,780 |
| TASK-4150 L3 relation graphs | 27 |
| TASK-4150 L3 validator | PASS |

## GPT Pro 검수 결론

현재 27개 relation graph는 L3가 아직 초기 단계라는 해석이 맞다. 문제는 단순히 데이터 부족만이 아니다. 현재 L3는 graph key와 taxonomy가 너무 굵어서, 뉴스와이어/매크로/종목/섹터/이벤트 관계를 충분히 펼치지 못한다.

특히 public newswire가 SOURCE_FAMILY/UNKNOWN으로 뭉친 부분이 핵심 병목이다. 매핑된 뉴스와이어 row는 ENTITY_EVENT, ENTITY_DIMENSION, EVENT_CLUSTER 또는 COVERAGE_GAP으로 분리되어야 한다.

또한 L3는 raw L0를 직접 읽지 않는다. 모든 graph와 edge는 L1/L2 산출물의 lineage를 통해서만 만들어야 한다.

## L3 목표 재정의

L3는 매매 실행 레이어가 아니다. L3는 L1/L2가 넘긴 자료를 바탕으로 다음을 만드는 진단/관계 레이어다.

| 목표 | 설명 |
|---|---|
| 관계 설명 | 어떤 종목/기업/섹터/매크로 factor/이벤트가 연결되는지 보여준다 |
| 근거 추적 | 모든 graph/edge가 L1/L2 lineage를 가진다 |
| coverage gap 분리 | 데이터 부족/미완료/미매핑을 부정 신호가 아니라 blocker/gap으로 둔다 |
| 모순 노출 | risk/support/context가 섞이는 경우 review 상태로 드러낸다 |
| 안전 경계 유지 | signal/order/broker/paper/live 권한을 열지 않는다 |

## relation graph v2 방향

| 추가해야 할 그래프 family | 의미 |
|---|---|
| ENTITY_EVENT | 종목/기업과 이벤트 관계 |
| ENTITY_DIMENSION | 종목/기업과 경제 의미 관계 |
| MACRO_FACTOR | 금리, 물가, FX, 고용 등 매크로 factor 관계 |
| MACRO_SECTOR | 매크로 factor와 섹터 관계 |
| SECTOR_THEME | 섹터와 테마 관계 |
| SOURCE_EVENT_CLUSTER | 여러 소스에서 같은 사건을 묶은 관계 |
| CONTRADICTION | 상반된 근거 관계 |
| COVERAGE_GAP | 막히거나 부족한 데이터 관계 |

## 다음 구현 작업

다음 구현 태스크는 L3 relation graph v2가 되어야 한다.

| 우선순위 | 작업 | 이유 |
|---|---|---|
| P0 | `l3_relation_edges.csv` 추가 | graph 요약만으로는 실제 관계를 검증하기 어렵다 |
| P0 | `l3_event_clusters.csv` 추가 | 같은 사건을 묶어야 뉴스/매크로/뉴스와이어가 연결된다 |
| P0 | newswire UNKNOWN collapse audit | 매핑된 뉴스와이어가 SOURCE_FAMILY/UNKNOWN에 갇히면 L3가 넓게 못 먹는다 |
| P0 | graph family taxonomy 추가 | ENTITY_EVENT, MACRO_FACTOR 같은 관계 축이 필요하다 |
| P0 | L1/L2 lineage validator 강화 | raw L0 bypass를 막고 추적성을 보장한다 |
| P1 | coverage gap reason code 표준화 | 안 먹은 데이터와 실제 관계를 분리한다 |
| P1 | price leakage validator | L3에서 수익률/알파/매매 판단 계산이 섞이지 않게 한다 |

## 안전 경계

이번 작업은 GPT Pro 검수와 설계 정리다. 다음 단계 구현에서도 L3는 진단/관계 레이어로 유지한다.

금지 상태는 그대로다.

- no BUY/SELL output
- no ranking or trading score
- no sizing
- no order intent
- no paper/live eligibility
- no broker mutation
- no strategy acceptance
- no deployment readiness

## 산출물

- GPT Pro 프롬프트: `gpt_prompt.md`
- GPT Pro 응답 캡처: `gpt_response.md`
- GPT 응답 메타: `gpt_capture_meta.json`
- GPT 전달용 컨텍스트 패킷: `l3_relation_graph_gpt_context_packet.md`
- 한국어 요약: `gpt_review_digest_ko.md`
- 검증 결과: `validation_results.md`

## 결론

L3는 넘어가도 되는 상태가 아니라, relation graph v2로 한 번 더 고도화해야 한다. 다만 이 고도화는 과도한 코드가 아니라 실효성이 있는 작업이다. 지금 가장 큰 개선 포인트는 “L0/L1/L2의 자료를 L3가 더 넓게 관계로 먹게 만드는 것”이다.
