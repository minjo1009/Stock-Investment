## 핵심 세 줄 요약

* **L2는 “매매 신호 생성층”이 아니라, L1이 허용한 원천을 L3가 안전하게 읽을 수 있는 `swing event primitive / admission view`로 바꾸는 층**이어야 합니다.
* **TASK-4140 이후 뉴스/매크로/뉴스와이어는 swing feature 후보로 볼 수 있지만, 아직 feature materialization은 닫혀 있어야 합니다.** 즉, 먼저 “후보 입장권 + primitive view”까지만 만듭니다.
* **첫 개발은 복잡한 뉴스 점수화가 아니라 `mapping → dedup → stale → effect window → leakage guard`가 붙은 최소 view와 validator**가 맞습니다.

---

# 1. 결론

제공된 로컬 패킷 기준으로 보면, 다음 단계 L2 개발은 **GO**입니다.
단, GO의 의미는 **L2 feature store / signal / score를 만들라는 뜻이 아닙니다.**

정확한 다음 단계는 이것입니다.

> **TASK-4142 또는 유사 태스크에서 `L2 Swing Primitive Admission View`를 만든다.**
> 이 view는 뉴스/매크로/뉴스와이어 raw를 직접 feature로 쓰지 않고, L1 packet을 근거로 “이 이벤트가 L3 feature 연구 후보로 들어올 수 있는가”만 판정한다.

현재 중요한 변화는 TASK-4140입니다.

기존에는 public newswire가 discovery-only에 가까운 보수적 상태였지만, TASK-4140에서 다음처럼 posture가 바뀌었습니다.

| Source family                    | 현재 해석                            |
| -------------------------------- | -------------------------------- |
| `public_context_news_feeds`      | swing/daily feature candidate 가능 |
| `public_market_macro_news_feeds` | swing/daily feature candidate 가능 |
| `public_newswire_feeds`          | swing/daily feature candidate 가능 |
| feature materialization          | 아직 닫힘                            |
| intraday timestamp precision     | 핵심 병목 아님                         |
| daily publication date           | 충분할 수 있음                         |
| activation policy                | 다음 거래 세션 또는 다음 daily decision    |
| primary window                   | 20D                              |
| secondary windows                | 1D, 5D, 60D                      |

따라서 L2의 다음 개발 방향은 다음 한 문장으로 정리됩니다.

> **뉴스를 “점수”로 만들기 전에, 뉴스가 어떤 기업/섹터/매크로 이벤트인지, 중복인지, stale인지, 어느 decision date부터 볼 수 있는지, 어떤 effect window 후보인지 안전하게 정리하는 view를 먼저 만든다.**

---

# 2. L2의 역할

## L2는 무엇인가

이 시스템에서 L2는 **raw evidence와 L3 feature research 사이의 안전한 의미 변환층**입니다.

L0는 수집합니다.
L1은 증거를 검문합니다.
L2는 검문을 통과한 증거를 **L3가 읽기 좋은 primitive 형태**로 바꿉니다.

즉, L2의 책임은 다음입니다.

| L2 책임                | 설명                                                     |
| -------------------- | ------------------------------------------------------ |
| **admission**        | L1 packet이 L2로 들어와도 되는지 재확인                            |
| **normalization**    | 뉴스/매크로/뉴스와이어를 공통 event primitive 형태로 정리                |
| **mapping**          | TICKER / ENTITY / SECTOR / MACRO / UNKNOWN 구분          |
| **dedup**            | 같은 이벤트를 여러 기사/소스가 반복 보도할 때 중복 가중 방지                    |
| **stale 판단**         | 한 달 스윙 전략에 맞게 너무 오래된 이벤트 차단 또는 archive 처리              |
| **effect window 선언** | 1D / 5D / 20D / 60D 후보 window를 부여                      |
| **L3 read view 제공**  | L3가 읽을 수 있는 안전한 테이블/view 제공                            |
| **leakage 차단**       | future outcome, future article, missing-as-negative 차단 |

---

## L2가 만들면 안 되는 것

L2는 아직 다음을 만들면 안 됩니다.

| 금지 항목                          | 이유                                                   |
| ------------------------------ | ---------------------------------------------------- |
| 뉴스 sentiment score             | 긍정/부정 판정은 아직 feature engineering 또는 L3 이후 문제         |
| bullish/bearish label          | missing/stale/news tone이 곧 매매 근거가 되면 leakage/과최적화 위험 |
| alpha score                    | L2가 전략층처럼 동작하면 레이어 경계 붕괴                             |
| realized return / event effect | 1D/5D/20D/60D 수익률 계산은 L3/L4 연구 또는 backtest 쪽 책임      |
| ranking                        | L2가 종목 순위를 만들면 사실상 signal layer가 됨                   |
| sizing / order intent          | hard state 위반                                        |
| paper/live promotion           | 명시적으로 금지                                             |
| legacy L2 news builder 복구      | 지금은 quarantine 유지가 맞음                                |

---

# 3. L2에서 먼저 만들 view

## 결론: 첫 view는 `L2 Swing Primitive Admission View`

질문에서 제시한 후보를 분류하면 다음과 같습니다.

| 후보                                 | L2에서 필요 여부 |  우선순위 |
| ---------------------------------- | ---------: | ----: |
| Event primitive layer              |         필요 |   2순위 |
| Feature-admission queue            |         필요 |   1순위 |
| Normalized economic meaning layer  |   필요하지만 얇게 |   3순위 |
| L3 read/view layer                 |         필요 | 1~2순위 |
| Full feature materialization layer |      아직 금지 |   후순위 |

따라서 첫 산출물은 단순히 “event primitive table”이 아니라, 다음 성격을 동시에 가져야 합니다.

> **`L2 Swing Primitive Admission View` = feature-admission queue + 최소 event primitive + L3 read view**

이 view는 **한 raw article당 한 row**가 아니라, 가능하면 **하나의 canonical event-mapping 단위당 한 row**가 되어야 합니다.

예를 들어 같은 기업의 같은 guidance 뉴스가 PRNewswire, GlobeNewswire, context news에 반복 등장하면 L3가 그걸 3개의 독립 신호로 보면 안 됩니다. L2는 이를 dedup cluster로 묶고, canonical event 후보로 보여줘야 합니다.

---

## 추천 view 이름

과도한 이름은 피하고, 실무적으로 다음 정도가 적절합니다.

```text
l2_swing_event_admission_view
```

또는 파일 산출물 기준:

```text
data/artifacts/task_4142_l2_swing_event_admission/
  l2_swing_event_admission_view.csv
  l2_swing_event_admission_view.jsonl
  l2_swing_event_admission_validation_report.json
  l2_swing_event_admission_validation_report.md
```

---

## 이 view가 가져야 할 상태값

`admission_status`는 최소한 다음 정도면 충분합니다.

| 상태                                     | 의미                                       |
| -------------------------------------- | ---------------------------------------- |
| `ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE` | L3 연구 후보로 읽을 수 있음. 아직 feature 아님         |
| `BLOCKED_UNKNOWN_MAPPING`              | TICKER/ENTITY/SECTOR/MACRO 매핑 실패         |
| `BLOCKED_STALE`                        | effect window 기준으로 너무 오래됨                |
| `BLOCKED_DUPLICATE_NON_CANONICAL`      | 중복 이벤트의 비대표 row                          |
| `BLOCKED_SOURCE_TIME`                  | L1 source-time/as-of 문제                  |
| `BLOCKED_RAW_INTEGRITY`                | raw path/hash 문제                         |
| `BLOCKED_LEAKAGE_RISK`                 | future outcome 또는 future availability 의심 |
| `BLOCKED_POLICY_MISMATCH`              | TASK-4140 posture와 불일치                   |
| `BLOCKED_LEGACY_PATH`                  | legacy L0→L2 또는 quarantined builder 경유   |

핵심은 `ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE`입니다.
이 명칭 자체가 **아직 feature가 아니라는 사실**을 강제합니다.

---

# 4. 뉴스/매크로/뉴스와이어 primitive 최소 스키마

아래 정도가 **최소 유용 스키마**입니다.
너무 많은 자연어 필드, LLM 요약, 복잡한 topic graph는 아직 필요 없습니다.

## A. 식별자 / lineage

| 컬럼                          | 설명                                                                                     |
| --------------------------- | -------------------------------------------------------------------------------------- |
| `task_id`                   | 예: `TASK-4142`                                                                         |
| `l2_event_id`               | L2 canonical event id                                                                  |
| `l2_event_mapping_id`       | event + mapping scope 단위 id                                                            |
| `source_family`             | `public_context_news_feeds`, `public_market_macro_news_feeds`, `public_newswire_feeds` |
| `source_packet_id`          | L1 packet id                                                                           |
| `raw_path`                  | L1 raw path                                                                            |
| `raw_sha256`                | L1 raw hash                                                                            |
| `provider`                  | 원천 provider                                                                            |
| `endpoint_or_source_family` | L1 source family 계승                                                                    |

---

## B. 시간 / as-of

| 컬럼                            | 설명                                                              |
| ----------------------------- | --------------------------------------------------------------- |
| `source_ts`                   | L1 source timestamp                                             |
| `publication_date`            | 기사/뉴스/매크로 공개일                                                   |
| `publication_time_precision`  | `SECOND`, `MINUTE`, `DAY`, `MONTH`, `YEAR`, `IMPUTED_NOMINAL` 등 |
| `is_publication_time_imputed` | Wikimedia noon 같은 nominal time이면 true                           |
| `available_to_brain_ts`       | brain이 볼 수 있었던 시각                                               |
| `decision_asof_ts`            | decision 기준 시각                                                  |
| `activation_policy`           | `NEXT_TRADING_SESSION_OR_NEXT_DAILY_DECISION`                   |
| `activation_decision_date`    | 이 이벤트가 L3에서 사용 가능해지는 첫 decision date                            |
| `source_time_basis`           | L1 값 계승                                                         |
| `source_time_certified`       | L1 값 계승                                                         |

중요한 점은 TASK-4138 반영입니다.

* Wikimedia day-level date를 noon UTC로 표현할 수는 있음.
* 그러나 그것은 **actual publication time이 아님**.
* 따라서 L2는 반드시 `is_publication_time_imputed = true` 또는 동등한 표시를 유지해야 합니다.
* month/year-only 날짜는 feature timing에 쓰면 안 되고, context-only 또는 block이어야 합니다.

---

## C. mapping

| 컬럼                        | 설명                                               |
| ------------------------- | ------------------------------------------------ |
| `mapping_scope`           | `TICKER`, `ENTITY`, `SECTOR`, `MACRO`, `UNKNOWN` |
| `mapping_key`             | scope별 canonical key                             |
| `symbol`                  | TICKER일 때 필수, 그 외 nullable                       |
| `entity_id`               | ENTITY일 때 사용                                     |
| `sector_key`              | SECTOR일 때 사용                                     |
| `macro_key`               | MACRO일 때 사용                                      |
| `mapping_confidence_rule` | 어떤 deterministic rule로 매핑됐는지                     |
| `mapping_status`          | `MAPPED`, `BLOCKED_UNKNOWN`, `AMBIGUOUS_REVIEW`  |

`UNKNOWN`은 feature admission block입니다.
단, review ledger에 남기는 것은 허용됩니다.

---

## D. dedup / cluster

| 컬럼                      | 설명                                                                      |
| ----------------------- | ----------------------------------------------------------------------- |
| `dedup_key`             | deterministic 중복 판단 key                                                 |
| `event_cluster_id`      | 같은 이벤트 cluster id                                                       |
| `is_canonical_event`    | 대표 이벤트 여부                                                               |
| `duplicate_of_event_id` | 비대표 row일 경우 canonical id                                                |
| `cluster_member_count`  | 같은 이벤트로 묶인 raw/source 수                                                 |
| `dedup_status`          | `UNIQUE`, `CANONICAL`, `DUPLICATE_BLOCKED`, `POSSIBLE_DUPLICATE_REVIEW` |

중복 row는 완전히 버리지 말고, **lineage와 cluster member로 보존**해야 합니다.
다만 L3가 중복을 독립 신호로 읽지 못하게 해야 합니다.

---

## E. economic meaning — 얇게만

| 컬럼                        | 설명                                                                                                                   |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `event_domain`            | `COMPANY`, `SECTOR`, `MACRO`, `POLICY`, `GEOPOLITICAL`, `MARKET_STRUCTURE` 등                                         |
| `event_type`              | `EARNINGS`, `GUIDANCE`, `M_AND_A`, `CAPEX`, `PRODUCT`, `REGULATION`, `INFLATION`, `RATES`, `LABOR`, `SUPPLY_CHAIN` 등 |
| `topic_tags`              | 제한된 enum list                                                                                                        |
| `economic_meaning_status` | `TAGGED`, `UNTAGGED_ALLOWED`, `BLOCKED_AMBIGUOUS`                                                                    |

여기서 주의할 점은 **economic meaning은 방향성이 아니라 분류**라는 것입니다.

예를 들어:

* 허용: `event_type = GUIDANCE`
* 아직 금지: `guidance_is_bullish = true`
* 허용: `event_domain = MACRO`, `event_type = INFLATION`
* 아직 금지: `inflation_news_score = -0.7`

---

## F. stale / effect window

| 컬럼                         | 설명                                                                            |
| -------------------------- | ----------------------------------------------------------------------------- |
| `primary_effect_window`    | 기본 `20D`                                                                      |
| `secondary_effect_windows` | `1D,5D,60D`                                                                   |
| `window_1d_start_date`     | 선택. planned window boundary                                                   |
| `window_1d_end_date`       | 선택                                                                            |
| `window_5d_start_date`     | 선택                                                                            |
| `window_5d_end_date`       | 선택                                                                            |
| `window_20d_start_date`    | 선택                                                                            |
| `window_20d_end_date`      | 선택                                                                            |
| `window_60d_start_date`    | 선택                                                                            |
| `window_60d_end_date`      | 선택                                                                            |
| `stale_status`             | `ACTIVE_PRIMARY`, `ACTIVE_SECONDARY`, `STALE_BLOCKED`, `ARCHIVE_CONTEXT_ONLY` |

여기서 window boundary는 허용됩니다.
하지만 window의 **실현 수익률, 승률, impact score**는 L2에서 계산하면 안 됩니다.

---

## G. admission / safety

| 컬럼                                | 설명                   |
| --------------------------------- | -------------------- |
| `swing_feature_candidate_now`     | TASK-4140 posture 계승 |
| `feature_materialization_allowed` | 현재는 false            |
| `admission_status`                | L2 admission 결과      |
| `block_reason`                    | block 사유             |
| `missing_source_is_negative`      | 반드시 false            |
| `assignment_uses_future_outcome`  | 반드시 false            |
| `outcome_used_for_assignment`     | 반드시 false            |
| `legacy_l0_to_l2_path_used`       | 반드시 false            |
| `legacy_builder_used`             | 반드시 false            |
| `trading_authority_opened`        | 반드시 false            |

---

# 5. mapping / dedup / stale / effect window 기준

## 5.1 Mapping 기준

TASK-4140의 mapping scope를 그대로 사용합니다.

| Mapping scope | L2 admission            |
| ------------- | ----------------------- |
| `TICKER`      | 허용                      |
| `ENTITY`      | 허용                      |
| `SECTOR`      | 허용                      |
| `MACRO`       | 허용                      |
| `UNKNOWN`     | feature admission block |

## Scope별 실무 기준

### TICKER

명확한 종목 코드가 있으면 `TICKER`입니다.

예:

```text
AVGO, NVDA, AMD, TSLA
```

필수 조건:

* symbol이 비어 있으면 안 됨
* symbol mapping source가 있어야 함
* ticker 변경/상장폐지/동명이인 위험이 있으면 `AMBIGUOUS_REVIEW`

---

### ENTITY

회사명, issuer, organization은 명확하지만 ticker가 확정되지 않은 경우입니다.

예:

```text
Broadcom Inc.
NVIDIA Corporation
TSMC
OpenAI
U.S. Department of Commerce
```

처리:

* entity-level event로는 허용
* ticker-level feature로 바로 승격 금지
* L3에서 ticker universe와 join할 때 별도 mapping 필요

---

### SECTOR

특정 기업보다 업종/산업에 가까운 이벤트입니다.

예:

```text
semiconductor equipment
memory pricing
AI server supply chain
regional banks
solar installers
```

처리:

* sector/industry context candidate로 허용
* 개별 ticker에 균등 배분하는 방식은 아직 금지
* 나중에 sector exposure model이 생긴 후 L3에서 처리

---

### MACRO

금리, 물가, 고용, 달러, 유가, 정책, 지정학 같은 broad macro입니다.

예:

```text
CPI
PCE
Fed rate decision
Treasury yield
oil supply shock
tariff policy
```

처리:

* macro primitive로 허용
* 개별 ticker signal로 바로 연결 금지
* L3에서 regime/context feature로 읽게 해야 함

---

### UNKNOWN

UNKNOWN은 feature admission block입니다.

허용되는 처리는 다음뿐입니다.

```text
admission_status = BLOCKED_UNKNOWN_MAPPING
review_queue = true
feature_materialization_allowed = false
```

---

## 5.2 Dedup 기준

한 달 스윙 전략에서는 같은 이벤트가 여러 번 보도될 수 있습니다.
중복 제거를 하지 않으면, “많이 보도된 이벤트”가 “강한 이벤트”처럼 보이는 오류가 생깁니다.

## 최소 dedup key

처음에는 복잡한 embedding dedup이 아니라 deterministic key로 충분합니다.

추천 dedup key:

```text
source_family_group
publication_date
mapping_scope
mapping_key
event_type
normalized_title_or_headline_key
```

조금 더 안정적으로 하려면:

```text
dedup_key = sha256(
  normalized_publication_date
  + mapping_scope
  + mapping_key
  + event_type
  + normalized_title_key
)
```

## Dedup window

| Source                         |                                Dedup window 추천 |
| ------------------------------ | ---------------------------------------------: |
| public_newswire_feeds          |                          같은 날 또는 1 trading day |
| public_context_news_feeds      |                               1~3 trading days |
| public_market_macro_news_feeds |  macro series 기준 같은 release date / same period |
| macro recurring data           | `series + period + release_date + revision` 기준 |

초기에는 너무 넓게 잡지 않는 게 좋습니다.
처음부터 20D 전체를 dedup window로 잡으면 서로 다른 후속 이벤트까지 하나로 묶을 위험이 있습니다.

## Canonical row 선택 기준

대표 row는 다음 우선순위로 정합니다.

1. L1 gate가 완전한 row
2. source_time / available_to_brain_ts가 가장 명확한 row
3. raw_path / raw_sha256가 있는 row
4. provider가 더 원천에 가까운 row
5. 가장 이른 `available_to_brain_ts`

단, 주의해야 합니다.

> 중복 cluster의 canonical time을 정할 때, 나중에 발견된 기사 정보를 과거 decision date에 소급하면 안 됩니다.

따라서 cluster-level canonical row는 만들되, **각 member의 available time lineage는 보존**해야 합니다.

---

## 5.3 Stale 기준

스윙 전략 평균 보유기간이 약 한 달이면, L2의 stale 기준은 intraday보다 daily window 중심이어야 합니다.

추천 상태:

| 상태                                  | 기준                                    |
| ----------------------------------- | ------------------------------------- |
| `ACTIVE_PRIMARY`                    | activation date부터 20 trading days 이내  |
| `ACTIVE_SECONDARY`                  | 21~60 trading days                    |
| `STALE_BLOCKED`                     | 60 trading days 초과                    |
| `ARCHIVE_CONTEXT_ONLY`              | 과거 맥락으로는 유용하지만 feature candidate로는 닫힘 |
| `BLOCKED_NO_VALID_PUBLICATION_DATE` | 날짜가 너무 불완전함                           |
| `BLOCKED_MONTH_OR_YEAR_ONLY_TIMING` | month/year-only라 timing feature로 부적합  |

## 날짜 precision별 처리

| 날짜 precision          | 처리                                       |
| --------------------- | ---------------------------------------- |
| second/minute/hour 정확 | 사용 가능                                    |
| day-level only        | swing 전략에서는 사용 가능                        |
| imputed noon UTC      | nominal로만 사용. actual publication time 아님 |
| month-only            | feature timing block 또는 context-only     |
| year-only             | feature timing block                     |
| unknown               | block                                    |

TASK-4138 때문에 이 부분은 반드시 명시해야 합니다.
특히 Wikimedia noon UTC 같은 nominal time은 L2에서 실제 publication time처럼 취급하면 안 됩니다.

---

## 5.4 Effect window 기준

TASK-4140 기준을 그대로 쓰면 됩니다.

| Window | 의미                            |
| ------ | ----------------------------- |
| `1D`   | 단기 반응 확인용                     |
| `5D`   | 짧은 continuation/reversal 후보   |
| `20D`  | 주 primary swing effect window |
| `60D`  | extended/persistence window   |

L2가 해야 할 일은 **window를 선언**하는 것입니다.

L2가 하면 안 되는 일:

```text
return_1d
return_5d
return_20d
return_60d
alpha_20d
hit_rate
forward_return_label
event_impact_score
```

이것들은 L3/L4 연구 또는 diagnostic backtest 영역입니다.

---

# 6. 하지 말아야 할 것

현재 L2에서 명시적으로 금지해야 할 작업입니다.

| 금지 작업                              | 이유                                            |
| ---------------------------------- | --------------------------------------------- |
| legacy L2 news builder 복구          | quarantine 상태 유지가 안전함                         |
| missing module stub 만들기            | import error만 없애고 의미론적 안전성은 없는 위험한 작업         |
| L0 raw news를 L2로 직접 연결             | L1 gate 우회                                    |
| 뉴스 sentiment 모델 붙이기                | 현재 필요한 건 admission과 primitive                 |
| LLM으로 bullish/bearish 분류           | 재현성/누수/과최적화 위험                                |
| 1D/5D/20D/60D 수익률 계산               | L2 책임 아님                                      |
| 종목 ranking                         | 사실상 signal layer                              |
| macro regime score                 | 아직 L2 primitive 이후 단계                         |
| news count를 강도 feature로 사용         | dedup 전에는 중복 보도량 bias 발생                      |
| UNKNOWN mapping을 sector/ticker로 추정 | 잘못된 feature admission 위험                      |
| broad cleanup                      | TASK-4139에서 dirty worktree가 크므로 좁은 범위만 작업해야 함 |
| DVC pointer 삭제/복구                  | TASK-4142 범위 밖                                |
| 5m microstructure와 결합              | 이번 task의 핵심이 아님                               |
| paper/live/broker/order 관련 코드 변경   | hard state 위반                                 |

가장 큰 금지 원칙은 이것입니다.

> **L2는 “이 이벤트가 어떤 의미의 후보인가”까지만 말하고, “그래서 사야 한다/팔아야 한다”는 말은 하지 않는다.**

---

# 7. P0/P1 리스크

## P0 리스크

| 리스크                           | 왜 치명적인가                                                        | 차단 방법                                                      |
| ----------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| L1 bypass                     | L0 raw가 L2로 직접 들어오면 source-time/raw integrity/mapping gate 무력화 | 모든 L2 row에 `source_packet_id`, `raw_path`, `raw_sha256` 필수 |
| legacy builder 재유입            | quarantined path가 몰래 production path가 될 수 있음                   | import block test                                          |
| feature materialization 조기 개방 | TASK-4140은 candidate 허용이지 feature 생성 허용이 아님                    | `feature_materialization_allowed=false` 강제                 |
| future leakage                | 나중 기사/결과를 과거 decision에 소급할 위험                                  | `available_to_brain_ts <= decision_asof_ts` 검증             |
| realized outcome 사용           | 20D 효과를 미리 라벨로 쓰면 백테스트 오염                                      | outcome/return/label 컬럼 금지                                 |
| UNKNOWN mapping 허용            | 엉뚱한 ticker/sector feature 생성                                   | UNKNOWN은 block                                             |
| 중복 뉴스 과가중                     | 같은 이벤트 반복 보도가 강한 signal처럼 보임                                   | canonical cluster + duplicate block                        |
| stale/missing을 negative로 해석   | 데이터 부재가 bearish evidence가 되는 오류                                | missing/stale = UNKNOWN/BLOCKER                            |
| dirty worktree 광범위 cleanup    | TASK-4139상 삭제/변경 위험 파일 많음                                      | 신규 파일/좁은 artifact만 생성                                      |

---

## P1 리스크

| 리스크                   | 문제                                     | 대응                                                          |
| --------------------- | -------------------------------------- | ----------------------------------------------------------- |
| taxonomy 과복잡          | event type이 너무 많으면 validator와 운영이 무거워짐 | 10~20개 enum으로 시작                                            |
| daily timestamp를 과소평가 | day-level이면 허용하되 imputed 여부를 보존해야 함    | `publication_time_precision` 필수                             |
| day-level을 과대평가       | noon UTC를 실제 시간처럼 쓰면 안 됨               | `is_publication_time_imputed` 필수                            |
| macro revision 미처리    | 같은 지표의 initial/revised가 섞일 수 있음        | `series`, `period`, `release_date`, `revision_status` 추가 가능 |
| sector mapping 남용     | sector event를 모든 종목에 뿌리면 noise 증가      | L3 join 전까지 sector primitive로만 유지                           |
| dedup이 너무 강함          | 다른 이벤트를 하나로 묶을 수 있음                    | `POSSIBLE_DUPLICATE_REVIEW` 상태 둠                            |
| dedup이 너무 약함          | 중복 보도량 bias                            | cluster count report                                        |
| validator만 많고 산출물이 없음 | 실무 진전이 안 됨                             | view CSV/JSONL을 반드시 생성                                      |
| DB schema부터 크게 만듦     | dirty worktree에서 리스크 큼                 | artifact-first, DB-later                                    |

---

# 8. Codex가 다음에 구현할 작업 순서

아래 순서가 가장 안전하고 실용적입니다.

---

## TASK-4142 — L2 Swing Event Admission View

### 목표

뉴스/매크로/뉴스와이어를 대상으로 **L3가 읽을 수 있는 최소 L2 admission view**를 만든다.

### 입력

로컬 L1 packet / handoff / TASK-4140 posture artifact.

### 출력

```text
data/artifacts/task_4142_l2_swing_event_admission/
  l2_swing_event_admission_view.csv
  l2_swing_event_admission_view.jsonl
  l2_swing_event_admission_validation_report.json
  l2_swing_event_admission_validation_report.md
  artifact_manifest.csv
```

### 핵심 규칙

```text
feature_materialization_allowed = false
trading_authority_opened = false
legacy_builder_used = false
legacy_l0_to_l2_path_used = false
```

### 구현 범위

* 세 source family만 대상으로 시작:

  * `public_context_news_feeds`
  * `public_market_macro_news_feeds`
  * `public_newswire_feeds`
* 한 row는 `event + mapping` 단위
* UNKNOWN mapping은 block
* month/year-only timing은 block 또는 context-only
* day-level publication date는 허용 가능
* imputed noon은 actual time이 아님을 표시

---

## TASK-4143 — Mapping & Dedup Validator

### 목표

L2 admission view에서 mapping과 dedup이 제대로 작동하는지 검증한다.

### 출력

```text
l2_mapping_issues.csv
l2_dedup_clusters.csv
l2_dedup_validation_report.json
```

### 구현 범위

* TICKER / ENTITY / SECTOR / MACRO / UNKNOWN enum 검증
* UNKNOWN feature admission block
* deterministic dedup key 생성
* canonical event row 지정
* duplicate row는 L3 read view에서 차단
* cluster member lineage 보존

### 하지 말 것

* embedding dedup
* LLM semantic clustering
* 복잡한 entity resolution system
* sector-to-ticker feature 배분

---

## TASK-4144 — Stale & Effect Window Policy

### 목표

한 달 swing 전략에 맞는 stale/effect window 정책을 L2 view에 붙인다.

### 출력

```text
l2_swing_window_policy.yaml
l2_stale_effect_window_report.json
```

### 정책

```text
primary_effect_window = 20D
secondary_effect_windows = 1D, 5D, 60D
activation_policy = NEXT_TRADING_SESSION_OR_NEXT_DAILY_DECISION
```

### 상태

```text
ACTIVE_PRIMARY
ACTIVE_SECONDARY
STALE_BLOCKED
ARCHIVE_CONTEXT_ONLY
BLOCKED_NO_VALID_PUBLICATION_DATE
BLOCKED_MONTH_OR_YEAR_ONLY_TIMING
```

### 하지 말 것

* realized return 계산
* effect score 계산
* alpha label 생성

---

## TASK-4145 — L3 Read Contract Sample

### 목표

L3가 어떤 컬럼만 읽을 수 있는지 read contract를 만든다.

### 출력

```text
l2_to_l3_swing_event_read_contract.yaml
l2_to_l3_swing_event_sample.csv
l2_to_l3_read_contract_validation_report.json
```

### L3에 노출 가능한 것

* event id
* mapping scope/key
* event type/domain
* activation date
* effect window declarations
* stale status
* source lineage
* canonical event 여부

### L3에 노출 금지

* forward return
* realized return
* hit/miss
* alpha score
* ranking
* order intent
* broker state

---

## TASK-4146 — Small End-to-End Diagnostic Sample

### 목표

실제 local rows 일부를 사용해 L1 → L2 admission → L3 read sample까지 연결이 되는지 확인한다.

### 범위

* 전체 production materialization 금지
* sample row 수 제한 가능
* source family별 count report 필수
* block reason별 count 필수
* 사람이 읽을 수 있는 QA markdown 필수

### 출력 예시

```text
l2_swing_event_admission_sample_qa.md
l2_family_count_summary.csv
l2_block_reason_summary.csv
l2_canonical_event_examples.md
```

---

# 9. 검증 체크리스트

## A. 필수 구조 검증

| 체크                               | 기대값  |
| -------------------------------- | ---- |
| L2 row마다 `source_packet_id` 존재   | PASS |
| L2 row마다 `raw_path` 존재           | PASS |
| L2 row마다 `raw_sha256` 존재         | PASS |
| L1 gate 실패 row admission 차단      | PASS |
| legacy builder import 없음         | PASS |
| direct L0-to-L2 path 없음          | PASS |
| feature materialization 없음       | PASS |
| broker/order/paper/live 관련 변경 없음 | PASS |

---

## B. TASK-4140 posture 검증

| 체크                                   | 기대값  |
| ------------------------------------ | ---- |
| context news swing candidate 허용      | PASS |
| market/macro news swing candidate 허용 | PASS |
| public newswire swing candidate 허용   | PASS |
| minute/second timestamp 필수 요구 없음     | PASS |
| daily publication date 허용 가능         | PASS |
| activation policy 반영                 | PASS |
| primary window 20D                   | PASS |
| secondary windows 1D/5D/60D          | PASS |
| feature materialization closed       | PASS |

---

## C. TASK-4138 timestamp precision 검증

| 케이스                                | 기대값                  |
| ---------------------------------- | -------------------- |
| exact publication timestamp        | admit 가능             |
| day-level publication date         | swing candidate 가능   |
| Wikimedia noon UTC nominal         | actual time으로 취급 금지  |
| `is_publication_time_imputed=true` | 필수                   |
| month-only date                    | feature timing block |
| year-only date                     | feature timing block |
| unknown date                       | block                |

---

## D. Mapping 검증

| 케이스                         | 기대값                     |
| --------------------------- | ----------------------- |
| TICKER mapping              | admit 가능                |
| ENTITY mapping              | admit 가능                |
| SECTOR mapping              | admit 가능                |
| MACRO mapping               | admit 가능                |
| UNKNOWN mapping             | feature admission block |
| ambiguous ticker/entity     | review 또는 block         |
| sector event를 ticker로 자동 배분 | 금지                      |

---

## E. Dedup 검증

| 케이스                                     | 기대값          |
| --------------------------------------- | ------------ |
| 동일 source_url/title/hash                | duplicate 처리 |
| 같은 기업/같은 이벤트/같은 날 반복 보도                 | cluster 처리   |
| canonical row 하나만 L3 read 가능            | PASS         |
| duplicate member lineage 보존             | PASS         |
| duplicate count가 signal strength로 사용됨   | FAIL         |
| later article 정보가 earlier decision에 소급됨 | FAIL         |

---

## F. Stale / effect window 검증

| 케이스                                | 기대값                                       |
| ---------------------------------- | ----------------------------------------- |
| activation 후 20D 이내                | `ACTIVE_PRIMARY`                          |
| 21~60D                             | `ACTIVE_SECONDARY`                        |
| 60D 초과                             | `STALE_BLOCKED` 또는 `ARCHIVE_CONTEXT_ONLY` |
| missing date                       | block                                     |
| stale event를 negative evidence로 사용 | FAIL                                      |
| planned window boundary 생성         | 허용                                        |
| realized return 계산                 | FAIL                                      |

---

## G. Leakage 검증

| 체크                                                       | 기대값  |
| -------------------------------------------------------- | ---- |
| `source_ts <= available_to_brain_ts <= decision_asof_ts` | PASS |
| future outcome assignment 없음                             | PASS |
| outcome label 컬럼 없음                                      | PASS |
| forward return 컬럼 없음                                     | PASS |
| post-event price move를 L2에서 읽지 않음                        | PASS |
| missing/stale을 bearish/bullish로 해석하지 않음                  | PASS |

---

## H. 산출물 QA

Codex는 validator만 만들고 끝내면 안 됩니다.
최소한 아래 요약을 남겨야 합니다.

```text
source_family별 input row count
source_family별 admitted row count
source_family별 blocked row count
block_reason별 count
mapping_scope별 count
dedup cluster count
canonical event count
duplicate blocked count
stale_status별 count
sample admitted rows
sample blocked rows
```

사람이 볼 수 있는 markdown도 필요합니다.

```text
l2_swing_event_admission_qa_report.md
```

이 report에는 최소한 다음이 들어가야 합니다.

* 대표 admitted row 5개
* 대표 blocked row 5개
* UNKNOWN mapping 예시
* duplicate cluster 예시
* imputed timestamp 예시
* stale blocked 예시
* legacy path 미사용 확인

---

# Codex에게 줄 수 있는 실행 명세서

아래를 그대로 다음 작업 지시로 써도 됩니다.

```text
TASK-4142 — Build Minimal L2 Swing Event Admission View

Objective:
Build the first practical Layer 2 view for swing-strategy news/macro/newswire primitives.
This is an admission/read view only, not feature materialization.

Use only local worktree state. Do not use GitHub.

Hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data = UNKNOWN/BLOCKER, never negative evidence
- GPT advice is review-only

Inputs:
- Local L1 normalized source packets
- Local L1 gates
- Local L1-to-L2 handoff artifacts
- Local TASK-4138 timestamp precision policy
- Local TASK-4140 swing news/macro/newswire posture artifacts

Target source families:
- public_context_news_feeds
- public_market_macro_news_feeds
- public_newswire_feeds

Build:
1. Create a minimal L2 swing event admission schema.
2. Generate l2_swing_event_admission_view.csv and .jsonl.
3. One row should represent an event + mapping candidate, not a trading signal.
4. Include mapping_scope: TICKER, ENTITY, SECTOR, MACRO, UNKNOWN.
5. UNKNOWN must block feature admission.
6. Include dedup_key, event_cluster_id, is_canonical_event, duplicate status.
7. Include publication_time_precision and is_publication_time_imputed.
8. Day-level publication date can be sufficient for swing candidates.
9. Wikimedia noon UTC or other nominal imputed time must not be treated as actual publication time.
10. Month/year-only timing must be context-only or blocked for feature timing.
11. Add activation_policy = NEXT_TRADING_SESSION_OR_NEXT_DAILY_DECISION.
12. Add primary_effect_window = 20D.
13. Add secondary_effect_windows = 1D, 5D, 60D.
14. Add stale_status: ACTIVE_PRIMARY, ACTIVE_SECONDARY, STALE_BLOCKED, ARCHIVE_CONTEXT_ONLY, or timing block.
15. Set feature_materialization_allowed = false for all rows.
16. Set trading_authority_opened = false for all rows.
17. Ensure legacy L2 news builder is not imported.
18. Ensure direct legacy L0-to-L2 news path is not used.

Do not build:
- sentiment score
- bullish/bearish label
- event impact score
- alpha score
- ranking
- realized return
- forward return
- hit rate
- sizing
- order intent
- paper/live/broker mutation
- broad cleanup of dirty worktree

Outputs:
data/artifacts/task_4142_l2_swing_event_admission/
- l2_swing_event_admission_view.csv
- l2_swing_event_admission_view.jsonl
- l2_swing_event_admission_validation_report.json
- l2_swing_event_admission_validation_report.md
- l2_mapping_issues.csv
- l2_dedup_clusters.csv
- l2_block_reason_summary.csv
- l2_family_count_summary.csv
- artifact_manifest.csv

Validator checks:
- required L1 lineage columns present
- source_packet_id present
- raw_path present
- raw_sha256 present
- L1 gates passed
- TASK-4140 posture respected
- feature_materialization_allowed remains false
- mapping_scope valid
- UNKNOWN mapping blocks admission
- dedup canonical row selected
- duplicate non-canonical row not exposed as independent L3 candidate
- day-level timing allowed for swing
- imputed nominal time marked as imputed
- month/year-only timing blocked or context-only
- source_ts <= available_to_brain_ts <= decision_asof_ts where applicable
- no future outcome assignment
- no outcome/return/alpha/ranking/order columns
- no missing/stale negative evidence
- no legacy builder import
- no direct L0-to-L2 path
- no broker/paper/live path touched

Acceptance:
Pass only if the produced report clearly shows:
- input/admitted/blocked counts by source family
- block reasons
- mapping scope counts
- duplicate cluster counts
- stale status counts
- sample admitted rows
- sample blocked rows
- zero feature materialization
- zero trading authority changes
```

---

## 최종 권고

사장님, 지금 L2에서 가장 중요한 것은 **“뉴스를 똑똑하게 해석하는 것”이 아니라 “뉴스가 L3로 들어갈 자격이 있는지 안전하게 정리하는 것”**입니다.

따라서 다음 개발은 아래 순서가 맞습니다.

1. **L2 Swing Event Admission View**
2. **Mapping/Dedup Validator**
3. **Stale/Effect Window Policy**
4. **L3 Read Contract Sample**
5. 그 다음에야 L3 feature 연구

이 순서를 지키면 TASK-4140의 실용적 방향 전환을 반영하면서도, 기존 hard boundary와 leakage safety를 유지할 수 있습니다.
