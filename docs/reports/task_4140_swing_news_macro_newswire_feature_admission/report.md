# TASK-4140 Swing News/Macro/Newswire Feature Admission

## 결론

뉴스, 매크로, 뉴스와이어는 trading feature 후보가 맞다. 다만 우리 전략은 평균 보유기간이 약 한 달인 스윙 전략이므로, 분/초 단위 공개시각보다 날짜 기준 as-of, 매핑, 중복 제거, 오래된 정보 처리, 효과기간 검증이 더 중요하다.

| 정리 | 의미 |
|---|---|
| feature 후보 | 뉴스/매크로/뉴스와이어 모두 `swing_feature_candidate_now=1` |
| 분초 집착 제거 | `minute_second_timestamp_required=0` |
| 날짜 기준 허용 | 공개일/발생일이 의사결정 전에 확인되면 스윙 feature 후보 가능 |
| 아직 안 하는 것 | 실제 feature table write, 매매 신호, paper/live/order |

## 소스별 판단

| Source | 스윙 feature 후보 | 쉬운 설명 |
|---|---:|---|
| `public_context_news_feeds` | 1 | 공식 문서/일반 뉴스는 스윙 feature 후보로 살린다. 분초보다 날짜, 매핑, 중복 제거, 효과기간이 중요하다. |
| `public_market_macro_news_feeds` | 1 | 매크로 뉴스는 스윙 feature 후보로 살린다. 종목이 없어도 macro scope와 효과기간이 있으면 후보가 된다. |
| `public_newswire_feeds` | 1 | 뉴스와이어는 스윙 feature 후보로 살린다. 핵심은 티커/엔티티 매핑과 이벤트 중복 제거다. |

## 효과기간

| Window | 용도 |
|---|---|
| `20D` | 평균 보유기간 한 달에 가까운 주 검증 구간 |
| `1D` | 단기 반응 확인용 |
| `5D` | 뉴스 소화 초기 구간 |
| `60D` | 늦게 반영되는 매크로/섹터 효과 확인용 |

## 다음 구현 포인트

1. L2에서 뉴스/매크로/뉴스와이어 row를 이 admission queue 기준으로 받아들인다.
2. L2는 `TICKER`, `ENTITY`, `SECTOR`, `MACRO`, `UNKNOWN` mapping scope를 분리한다.
3. L3 이상에서 5D/20D/60D 효과를 검증한다.
4. 통과 전까지는 feature 후보이지, 매매 신호나 주문 권한이 아니다.
