# TASK-4151 GPT Pro 검수 요약

## 결론

사용자의 의심이 맞다. 현재 L3 relation graph 27개는 초기 단계로 봐야 한다. “데이터가 원래 적어서 정상”이라기보다, L3가 관계를 너무 굵은 단위로 묶고 있어서 실제 관계를 충분히 펼치지 못한 상태다.

L3의 목표는 매매 신호를 만드는 것이 아니다. L0/L1/L2에서 올라온 뉴스, 뉴스와이어, 매크로, 공시성 문맥을 “어떤 종목/섹터/거시요인/이벤트와 연결되는지” 설명 가능한 관계망으로 정리하는 것이다.

## 왜 27개밖에 안 나왔나

| 원인 | 쉬운 표현 | 영향 |
|---|---|---|
| graph key가 너무 큼 | 여러 관계를 한 바구니에 넣었다 | 관계 수가 실제보다 작게 보인다 |
| 뉴스와이어가 SOURCE_FAMILY/UNKNOWN으로 뭉침 | PRNewswire/BusinessWire/GlobeNewswire가 실제 기업/이벤트 관계로 풀리지 않았다 | 매핑된 뉴스가 그래프에서 힘을 못 쓴다 |
| L1/L2 입력이 좁음 | 현재 기사 단위 feature가 CFTC 쪽에 치우쳤다 | 기업 뉴스/뉴스와이어 관계가 부족하다 |
| 이벤트 클러스터가 없음 | 같은 사건을 묶는 중간 노드가 없다 | “A회사 실적가이던스”, “금리 이벤트” 같은 관계가 안 보인다 |
| 매크로 factor/섹터/theme 축이 약함 | 금리, 물가, FX, 섹터 테마로 연결하는 구조가 부족하다 | 매크로 뉴스가 trading feature 재료로 이동하기 어렵다 |
| coverage gap이 관계 그래프와 섞임 | 못 먹은 데이터와 실제 관계가 분리되지 않았다 | 부족한 부분을 고치기 어렵다 |

## GPT Pro가 제안한 L3 목표

L3는 다음을 해야 한다.

1. L1/L2에서 승인되거나 검토 가능한 row만 받아야 한다.
2. raw L0를 직접 읽지 않아야 한다.
3. 종목, 기업, 이벤트, 매크로 factor, 섹터, theme 사이의 관계를 만들어야 한다.
4. 관계가 부족한 경우에는 부정 신호가 아니라 coverage gap/blocker로 남겨야 한다.
5. BUY/SELL, ranking, sizing, order intent, paper/live eligibility, broker mutation은 절대 만들지 않아야 한다.

## relation graph v2에서 늘려야 할 그래프 종류

| 그래프 종류 | 뜻 | 예시 |
|---|---|---|
| ENTITY_EVENT | 종목/기업과 이벤트 연결 | NVDA - guidance event |
| ENTITY_DIMENSION | 종목/기업과 경제 의미 연결 | AAPL - regulatory risk |
| MACRO_FACTOR | 금리/물가/FX/고용 등 거시 요인 연결 | RATES - Fed speech |
| MACRO_SECTOR | 거시 요인과 섹터 연결 | RATES - semiconductors |
| SECTOR_THEME | 섹터와 테마 연결 | semiconductors - AI capex |
| SOURCE_EVENT_CLUSTER | 같은 사건을 여러 소스에서 묶음 | PRNewswire + context news cluster |
| CONTRADICTION | 서로 반대되는 근거 노출 | guidance positive vs margin risk |
| COVERAGE_GAP | 못 먹은 데이터/미매핑/미완료 백필 | newswire mapped but no L2 feature |

## 새 산출물 제안

| 산출물 | 역할 |
|---|---|
| `l3_relation_graphs.csv/json` | 그래프 단위 요약 |
| `l3_relation_edges.csv` | 실제 관계 edge 목록 |
| `l3_event_clusters.csv` | 같은 사건을 묶은 이벤트 클러스터 |
| `l3_coverage_gaps.csv` | 부족하거나 막힌 데이터 이유 |
| `l3_relation_graph_validation.json` | validator 결과 |

## 중요한 검증 조건

| 검증 | 목적 |
|---|---|
| no forbidden trading output | L3가 매매 권한을 열지 않는지 확인 |
| no direct L0 bypass | L3가 raw L0를 직접 읽지 않는지 확인 |
| lineage completeness | 모든 edge가 L1/L2 출처를 갖는지 확인 |
| graph key uniqueness | 중복 row로 그래프 수를 부풀리지 않는지 확인 |
| unknown collapse audit | 매핑된 뉴스와이어가 SOURCE_FAMILY/UNKNOWN에 갇히지 않는지 확인 |
| coverage semantics | 부족/미완료/오래된 데이터가 부정 신호로 쓰이지 않는지 확인 |
| price leakage check | 가격 반응/수익률/알파 계산이 L3에 섞이지 않는지 확인 |

## 다음 작업 판단

다음 작업은 L3 relation graph v2 구현이다. 핵심은 “그래프 개수 늘리기”가 아니라, L0/L1/L2의 정보를 더 넓고 정확하게 관계로 펼치는 것이다.

우선순위는 다음이 맞다.

1. 뉴스와이어 SOURCE_FAMILY/UNKNOWN collapse를 없애거나 coverage gap으로 분리한다.
2. event cluster를 만든다.
3. ENTITY_EVENT, ENTITY_DIMENSION, MACRO_FACTOR, MACRO_SECTOR 그래프를 추가한다.
4. 모든 edge에 L1/L2 lineage를 강제한다.
5. validator로 duplicate inflate, raw L0 bypass, trading output leakage를 막는다.

## 안전 경계

이번 검수는 설계 검수다. strategy acceptance, deployment readiness, paper/live eligibility, broker mutation, order intent는 열지 않는다. L3는 진단/관계 해석 레이어로만 유지한다.
