# TASK-4142 L2 Swing Event Admission View

## 결론

GPT Pro 설계에 따라 L2의 첫 view를 만들었다. 이 view는 뉴스/매크로/뉴스와이어를 점수화하지 않고, L3가 읽을 수 있는 이벤트 후보인지와 아직 검토가 필요한 이유만 정리한다.

| 원칙 | 결과 |
|---|---|
| 뉴스/매크로/뉴스와이어 | 스윙 event 후보로 처리 |
| 분/초 timestamp | 필수 조건 아님 |
| day-level / imputed time | 명시적으로 표시 |
| mapping unknown | hard block이 아니라 mapping review 상태 |
| stale historical row | active feature가 아니라 archive/context 상태 |
| feature score/signal | 만들지 않음 |
| broker/paper/live/order | 열지 않음 |

## Family Summary

| Source | Input | Admitted | Review | Blocked | Unknown Mapping | Archive Context |
|---|---:|---:|---:|---:|---:|---:|
| `public_context_news_feeds` | 1 | 1 | 0 | 0 | 0 | 1 |
| `public_market_macro_news_feeds` | 1 | 1 | 0 | 0 | 0 | 1 |
| `public_newswire_feeds` | 1 | 0 | 1 | 0 | 1 | 0 |

## Sample Rows

| Source | Mapping | Stale | Admission | Reason |
|---|---|---|---|---|
| `public_context_news_feeds` | `MACRO` | `ARCHIVE_CONTEXT_ONLY` | `ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE` | `` |
| `public_newswire_feeds` | `UNKNOWN` | `PENDING_NEXT_DAILY_DECISION` | `MAPPING_REVIEW_REQUIRED_NOT_FEATURE` | `` |
| `public_market_macro_news_feeds` | `MACRO` | `ARCHIVE_CONTEXT_ONLY` | `ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE` | `` |

## 다음 단계

1. 실제 L0/L1 전체 row로 view 입력 범위를 넓힌다.
2. deterministic mapping rule을 ticker/entity/sector/macro별로 보강한다.
3. dedup cluster를 headline/content hash 기반으로 고도화한다.
4. L3 read contract sample로 넘긴다.
