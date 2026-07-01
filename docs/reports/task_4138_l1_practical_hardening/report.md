# TASK-4138 L1 Practical Hardening

## 결론

L1은 feature를 직접 만들지 않는다. 대신 아래 세 가지를 더 명확히 남기도록 보강했다.

| 보강 항목 | 이번 작업 결과 |
|---|---|
| 시간 정밀도 | source family별로 실제 시각, 날짜 보정, 정밀도 부족을 분리했다. |
| Wikimedia 정오 정책 | 연/월/일 중 일 단위만 정오 UTC로 둘 수 있지만, 이것은 실제 공개시각이 아니라 보정 시각이다. |
| 막힌 이유 | 각 소스가 왜 아직 trading feature가 아닌지 L1 block reason으로 남겼다. |
| 반복 검증 | 기존 L1/L2 경계 validator를 한 번에 다시 돌린 ledger를 남겼다. |

## 소스별 현재 판단

| Source | 지금 L1 판단 | 쉬운 설명 |
|---|---|---|
| `market_bars_5m` | `STRICT_SOURCE_TIME_CANDIDATE` | 5분봉은 시간 자체는 믿을 수 있지만, 아직 L2 feature 테이블로 만들 검증은 끝나지 않았다. |
| `daily_bars` | `STRICT_SOURCE_TIME_CANDIDATE` | 일봉은 시간 자체는 믿을 수 있지만, 아직 L2 feature 테이블로 만들 검증은 끝나지 않았다. |
| `public_context_news_feeds` | `CONTEXT_OR_FEATURE_CANDIDATE_ONLY` | 뉴스/공식 문서는 후보가 될 수 있지만, 종목 연결과 중복 제거, 오래된 뉴스 처리, 효과 기간 검증이 먼저다. |
| `public_market_macro_news_feeds` | `MACRO_CONTEXT_OR_FEATURE_CANDIDATE_ONLY` | 매크로 뉴스는 후보가 될 수 있지만, 실제 공개시각과 효과 기간이 불명확하면 매매 feature로 쓰면 안 된다. |
| `public_newswire_feeds` | `DISCOVERY_OR_FEATURE_CANDIDATE_ONLY` | 뉴스와이어는 후보가 될 수 있지만, 티커 매핑 신뢰도와 이벤트 효과 검증 전에는 feature가 아니다. |

## Wikimedia 규칙

| 정밀도 | 처리 | feature 가능 |
|---|---|---|
| `second_or_minute_or_hour` | Use only if the source explicitly provides an actual timestamp. | `0` |
| `day` | Represent YYYY-MM-DD as YYYY-MM-DDT12:00:00Z only as imputed nominal time. | `0` |
| `month` | Keep as month-level context. Do not convert to a specific trading timestamp. | `0` |
| `year` | Keep as year-level context. Do not convert to a specific trading timestamp. | `0` |
| `unknown_or_circa` | Keep as context only or block. | `0` |

## 검증 결과

| 항목 | 값 |
|---|---|
| 실행 validator 수 | 3 |
| 통과 validator 수 | 3 |
| trading authority | 열지 않음 |
| paper/live/broker/order | 열지 않음 |

## 산출물

- `configs/l1_source_time_precision_policy.yaml`
- `data/artifacts/task_4138_l1_practical_hardening/l1_source_time_precision_policy.csv`
- `data/artifacts/task_4138_l1_practical_hardening/l1_wikimedia_noon_policy.csv`
- `data/artifacts/task_4138_l1_practical_hardening/l1_feature_block_reason_matrix.csv`
- `data/artifacts/task_4138_l1_practical_hardening/l1_repeated_validation_run_state.csv`

## 남은 일

L1 기준에서 더 할 일은 broad crawler나 feature 생성이 아니다. 다음은 L2에서 mapping, dedup, stale policy, effect window, leakage check를 붙여서 뉴스/매크로가 실제 매매 feature 후보가 될 수 있는지 입학 심사를 하는 것이다.
