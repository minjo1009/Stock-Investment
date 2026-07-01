# TASK-4137 GPT Pro 검토 요청

Use Pro-level reasoning.

중요: GitHub를 보지 마세요. 현재 L0/L1/L2 작업본은 로컬에 있고 아직 GitHub에 최신 상태로 반영되어 있지 않을 수 있습니다. 아래에 제공하는 로컬 요약을 기준으로 판단해 주세요.

답변은 한국어로, 실무자가 바로 이해할 수 있게 쉬운 표현으로 작성해 주세요.

과도한 코드를 위한 코드는 지양해 주세요. "가드를 위한 가드", "프로그램을 위한 프로그램" 말고, 실제 효과가 있는 보완만 제안해 주세요.

## 프로젝트 안전 경계

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data = UNKNOWN/BLOCKER, never negative evidence
- GPT 의견은 참고용입니다. 실제 source of truth는 로컬 repo 파일, task registry, validator입니다.

## 현재 L1 상태 요약

L1은 "데이터 입구 검문소" 역할입니다.

L1이 확인하는 것:

1. source time: 이 데이터가 언제 나온 것인지
2. raw integrity: 원본 파일/DB row가 추적 가능한지
3. mapping: 종목/뉴스/매크로 대상 연결이 명확한지
4. authority: 이 데이터를 L2로 넘겨도 되는 권한/상태인지

현재 L1 source family 상태:

| source family | 현재 L1 상태 | 의미 |
|---|---|---|
| daily_bars | STRICT_SOURCE_TIME_CERTIFIED | 일봉은 L2 입구 후보로 볼 수 있음 |
| market_bars_5m | STRICT_SOURCE_TIME_CERTIFIED | 5분봉도 L2 입구 후보로 볼 수 있음 |
| public_context_news_feeds | CONTEXT_ONLY_CERTIFIED | 뉴스/문맥은 매매 feature 후보가 될 수 있지만 매핑/효과 검증 전에는 feature 아님 |
| public_market_macro_news_feeds | CONTEXT_ONLY_CERTIFIED | 매크로도 feature 후보가 될 수 있지만 scope/time/effect 검증 필요 |
| public_newswire_feeds | DISCOVERY_ONLY | 뉴스와이어는 고신뢰 티커 매핑, 중복 제거, 효과 구간 검증 전에는 feature 아님 |

## TASK-4136에서 이미 정리한 방향

뉴스/매크로는 영구적으로 참고자료에만 묶어두지 않습니다.

대신 이렇게 정했습니다:

- 뉴스/매크로도 매매 feature로 사용할 수 있어야 한다.
- 하지만 지금 바로 feature로 쓰면 안 된다.
- 먼저 L2에서 feature 입학시험을 통과해야 한다.
- 입학시험에는 source time, ticker/entity/macro mapping, dedup, stale policy, effect window 검증이 포함된다.
- 기존 L2 뉴스 코드는 새 경로와 분리했다.
- L1 검증은 한 번 하고 끝이 아니라 계속 돌 수 있어야 한다.

TASK-4136 결과:

| 항목 | 상태 |
|---|---|
| L2 intake rows | 5 |
| news/macro future feature path rows | 3 |
| admitted as trading feature now | 0 |
| legacy L2 news builder | quarantined |
| L1 validation hooks | 3 |
| L1 validation smoke pass | 3/3 |
| L2 feature materialization | false |
| trading authority opened | false |

## 사용자가 검토받고 싶은 1~6 과제

아래 6개를 어떻게 구체적으로 디벨롭/보완해야 하는지 검토해 주세요.

1. Wikimedia
   - 연/월/일까지 확인된다면 정오로 반영하는 정책
   - 어떤 경우에 쓰고, 어떤 경우에 막아야 하는지

2. 매매판단용 trading feature 기준과 검증
   - 뉴스/매크로를 매매 feature로 쓰기 위한 최소 기준
   - L1, L2, L3 중 어디에서 무엇을 검증해야 하는지
   - 어떤 검증 전에는 절대 feature로 admit하면 안 되는지

3. 스케줄러 실행/검수
   - L0 수집 후 L1 검증이 계속 돌게 하는 방법
   - 너무 복잡한 운영 시스템 말고, 효과 있는 최소 운영 방식
   - 실패 시 어떤 상태를 남겨야 하는지

4. Validator 분리
   - L1 validator, L2 intake validator, feature admission validator를 어떻게 나눌지
   - 중복이 많아지지 않게 하려면 어떻게 해야 하는지

5. 크롬 크롤링 추가
   - Chrome crawling을 언제 쓰는 게 맞는지
   - API/HTTP/RSS보다 Chrome crawling이 나은 경우와 아닌 경우
   - Chrome crawling 결과를 L1/L2에서 어떻게 제한해야 하는지

6. 티커/뉴스 매핑 고도화
   - 뉴스가 어떤 종목과 연결되는지 판단하는 기준
   - 애매한 매핑을 어떻게 막을지
   - 매크로 뉴스처럼 특정 티커가 없어도 feature 후보가 될 수 있는 경우를 어떻게 구분할지

## 원하는 답변 형식

1. 전체 결론
   - L1에서 더 해야 할 것
   - L2에서 해야 할 것
   - 아직 하지 말아야 할 것

2. 1~6 과제별 표
   - 목적
   - 지금 부족한 점
   - 구체 보완 방법
   - 과도한 구현을 피하는 기준
   - 완료 기준

3. 우선순위
   - P0, P1, P2로 나눠 주세요.

4. 다음 Codex 작업안
   - TASK-4138로 바로 실행 가능한 작은 작업 단위로 제안해 주세요.
   - 코드가 필요 없는 것은 문서/계약/검증 계획으로 끝내도 됩니다.

