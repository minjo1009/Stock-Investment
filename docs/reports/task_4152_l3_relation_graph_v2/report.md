# TASK-4152 L3 Relation Graph V2 Implementation

## 결론

L3 relation graph v2를 구현했다. 기존 TASK-4150의 27개 graph 요약을 유지하지 않고, L1/L2/L3 lineage를 가진 edge, event cluster, coverage gap, graph family로 더 넓게 펼쳤다.

핵심 변화는 public newswire가 더 이상 일반 relation graph 안에서 `SOURCE_FAMILY/UNKNOWN`으로 뭉치지 않는다는 점이다. 현재 데이터 기준 public newswire 181건은 `NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE` coverage gap으로 분리된다. 이것은 부정 신호가 아니라 “뉴스와이어는 들어왔지만 article/entity event feature로 아직 못 풀었다”는 blocker/gap이다.

## 산출물 수치

| 항목 | TASK-4150 | TASK-4152 |
|---|---:|---:|
| relation graphs | 27 | 5,398 |
| relation edges | 2,780 | 7,150 |
| event clusters | 없음 | 1,850 |
| coverage gaps | 2 | 181 |

## graph family 분포

| graph family | graph 수 | 의미 |
|---|---:|---|
| SOURCE_EVENT_CLUSTER | 1,850 | 소스와 이벤트 클러스터 연결 |
| ENTITY_EVENT | 1,771 | 종목/기업과 이벤트 연결 |
| ENTITY_DIMENSION | 947 | 종목/기업과 경제 의미 연결 |
| MACRO_FACTOR | 828 | 매크로 factor와 이벤트 연결 |
| COVERAGE_GAP | 2 | 막힌/부족한 데이터 묶음 |

## 구현한 코드

| 파일 | 역할 |
|---|---|
| `src/brain/l3_relation_graph_v2_4152/contracts.py` | graph family, edge, cluster, gap 계약 |
| `src/brain/l3_relation_graph_v2_4152/builder.py` | L3 v2 산출물 생성 |
| `src/brain/l3_relation_graph_v2_4152/validator.py` | no raw L0 bypass, lineage, unknown collapse, forbidden output 검증 |
| `scripts/build_l3_relation_graph_v2_4152.py` | 빌드 실행 |
| `scripts/validate_l3_relation_graph_v2_4152.py` | validator 실행 |
| `tests/test_l3_relation_graph_v2_4152.py` | 핵심 동작 테스트 |

## 생성 산출물

| 산출물 | 역할 |
|---|---|
| `l3_relation_edges.csv` | 실제 관계 edge 목록 |
| `l3_event_clusters.csv` | 같은 사건을 묶은 이벤트 클러스터 |
| `l3_relation_graphs.csv` | relation graph 요약 |
| `l3_coverage_gaps.csv` | 부족/차단/미완료 상태 |
| `l3_relation_graph_v2_manifest.json` | 입력/출력/안전 상태 manifest |
| `l3_relation_graph_validation.json` | validator 결과 |

## 검증 결과

`python scripts/validate_l3_relation_graph_v2_4152.py --artifact-dir data/artifacts/task_4152_l3_relation_graph_v2` 결과 PASS.

확인한 내용:

- edge dedupe key unique
- graph key unique
- 모든 edge가 L1/L2 lineage 보유
- raw L0 직접 읽기 없음
- public newswire `SOURCE_FAMILY/UNKNOWN` collapse가 일반 graph에서 제거됨
- `NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE` coverage gap 명시
- coverage gap은 negative evidence가 아님
- price reaction/return/alpha 필드 없음
- BUY/SELL, ranking, sizing, order intent, broker mutation 없음

## 안전 경계

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- No signal export
- No order intent
- No strategy acceptance
- Missing/stale/incomplete data remains `UNKNOWN/BLOCKER`, not negative evidence

## 남은 점

이번 v2는 현재 존재하는 L1/L2/L3 산출물을 더 잘 펼친 것이다. 다음 개선은 L1/L2 쪽에서 뉴스와이어 article/entity-level feature가 더 많이 생기면, 현재 coverage gap으로 빠진 뉴스와이어가 `ENTITY_EVENT`와 `ENTITY_DIMENSION`으로 이동하도록 하는 것이다.

