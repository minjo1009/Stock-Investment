# GPT Response

CAPTURED via ChatGPT Pro Chrome session.

- source_url: https://chatgpt.com/c/6a42fce5-bae4-83ee-9268-7f0471a44735
- capture_status: CAPTURED

## GPT Recommendation

핵심 세 줄 요약

L1은 feature를 만들 단계가 아니라, “넘겨도 되는 후보인지/왜 막혔는지”를 계속 남기는 검문소로 강화해야 합니다.

L2는 뉴스·매크로·Wikimedia·Chrome 데이터를 매매 feature로 쓰기 전, source time·매핑·중복·stale·effect window 입학시험을 담당해야 합니다.

아직 하지 말아야 할 것은 L3 scoring, feature materialization, paper/live promotion, 광범위 Chrome crawling입니다.

1. 전체 결론

전제는 유지해야 합니다.

현재 상태는 DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY이고, 뉴스/매크로/뉴스와이어는 아직 매매 feature가 아닙니다.
L2에서 입학시험을 통과하기 전까지는 “후보” 또는 “문맥”입니다.

L1에서 더 해야 할 것

L1은 지금 방향이 맞습니다. 다만 더 해야 할 일은 feature 개발이 아니라 증거와 차단 사유를 더 선명하게 남기는 것입니다.

L1 보완의 핵심은 아래 5개입니다.

L1 보완 항목	의미
source_time_kind	실제 시각인지, 날짜만 있는지, 정오 보정인지, 기간형인지 구분
source_time_precision	초/분/시/일/월/년 단위 구분
usable_after	이 데이터가 의사결정에 사용 가능해지는 가장 이른 시점
authority_status	STRICT / CONTEXT_ONLY / DISCOVERY_ONLY / BLOCKED / QUARANTINED
block_reason	왜 L2 feature 후보로 못 가는지 명확히 기록

특히 Wikimedia처럼 날짜 정밀도가 애매한 데이터는 source_time처럼 보이게 만들면 안 됩니다. Wikidata는 time datatype에 precision을 둡니다. 예를 들어 year/month/day precision이 각각 다른 값으로 표현되고, day precision이라고 해도 실제 시간대나 정확성에 한계가 있을 수 있습니다. 
위키데이터
 또한 Wikidata 문서 자체도 일부 날짜가 실제로는 year precision인데 day precision처럼 입력된 경우가 있을 수 있다고 경고합니다. 
위키데이터

따라서 L1은 “정오로 보정한 값”을 실제 공개시각이 아니라 보수적 정렬용 시각으로만 저장해야 합니다.

L2에서 해야 할 것

L2는 이제 명확히 feature admission gate가 되어야 합니다.

L2의 역할은 다음입니다.

L2 역할	설명
후보 수용	L1에서 넘어온 context/news/macro/newswire 후보를 받음
입학시험	source time, mapping, dedup, stale, effect window 검증
feature materialization 차단	입학 전에는 실제 feature table/score로 만들지 않음
legacy 경로 격리 확인	기존 L2 news builder가 다시 feature로 섞이지 않게 확인
진단용 승인	통과해도 곧바로 전략/매매 승인 아님. “진단 feature 후보”일 뿐

핵심은 이것입니다.

L2는 “쓸 수 있을지도 모르는 데이터”를 “검증된 진단용 feature 후보”로 바꾸는 곳입니다.

아직 하지 말아야 할 것

아래는 지금 하면 안 됩니다.

금지 항목	이유
뉴스/매크로 즉시 매매 feature화	mapping/effect window/stale 검증 전
L3 alpha scoring 연결	L2 admission 전에는 feature가 아님
legacy L2 news builder 재사용	이미 quarantined 상태
Chrome crawling 대량 도입	느리고 불안정하며 L1 evidence 품질이 낮아질 수 있음
paper promotion	trading authority opened = false
stale/missing을 부정 신호로 처리	프로젝트 경계상 UNKNOWN/BLOCKER여야 함
Wikimedia 날짜를 strict source time으로 취급	날짜 precision과 실제 공개시각은 다름
2. 1~6 과제별 검토
요약 표
과제	목적	지금 부족한 점	구체 보완 방법	과도한 구현을 피하는 기준	완료 기준
1. Wikimedia	날짜·이벤트·엔티티 문맥을 보조 데이터로 사용	연/월/일 precision과 실제 공개시각이 섞일 위험	source_time_kind=IMPUTED_DATE_ONLY, precision=day/month/year, usable_after 별도 저장. day precision만 정오 보정 허용. year/month는 trading feature 금지 또는 월간/연간 context만 허용	Wikimedia를 primary market timestamp처럼 쓰지 않기. 정오 보정값을 실제 공개시각으로 취급하지 않기	day/month/year fixture 통과. day precision도 단독으로 feature admit 불가. is_imputed_time=true 필수
2. 매매판단용 trading feature 기준	뉴스/매크로를 feature로 쓸 최소 입학조건 정의	context 후보와 feature의 경계가 아직 완전히 계약화되지 않음	L2 feature admission contract 작성. 필수항목: source time, activation time, mapping confidence, dedup key, stale policy, effect window, raw evidence, leakage check	예측모델/점수화부터 만들지 않기. 먼저 admission gate만 만들기	admitted feature = 0 유지 상태에서 validator가 “왜 아직 못 들어가는지” 정확히 설명
3. 스케줄러 실행/검수	L0 수집 후 L1 검증이 반복적으로 돌게 함	한 번 통과한 smoke pass가 지속 검증인지 불명확	collect → normalize → L1 validate → run_state 기록의 최소 루프. run_id, source_family, row count, latest_source_time, status, blocker_reason 저장	Airflow/대형 orchestration 금지. 기존 scheduler registry + post-run hook 정도만	최근 실행 상태 파일이 남고, 실패 시 BLOCKER/UNKNOWN/QUARANTINE 상태가 남음
4. Validator 분리	L1/L2/admission 검증 책임을 분리	validator가 늘어나면 중복·복잡도 증가 가능	공통 contract/check 함수는 하나. validator는 얇게 3개: L1 evidence, L2 intake, feature admission	같은 검증 로직 복붙 금지. schema/status enum 중복 정의 금지	동일 fixture를 3 validator가 역할별로 다르게 판정. 중복 schema 없음
5. Chrome crawling 추가	API/RSS/HTTP로 안 되는 공식·동적 페이지 보완	Chrome 결과가 raw evidence로는 좋지만 source time 품질이 약할 수 있음	allowlist 기반, source-specific crawler만 허용. HTML snapshot/hash/fetched_at/source_url 저장. publish_time 없으면 L1 STRICT 금지	범용 브라우저 크롤러 만들지 않기. 뉴스 전수 크롤링 금지. paywall/login 우회 금지	Chrome 결과가 L0 raw로만 저장되고, source_time 없으면 L2 feature 후보 차단
6. 티커/뉴스 매핑 고도화	뉴스가 어떤 종목/매크로 요인과 연결되는지 안정화	애매한 기업명, 다중 종목, macro-only 뉴스 처리 기준 필요	mapping scope를 TICKER / ENTITY / SECTOR / MACRO / UNKNOWN로 분리. single ticker feature는 HIGH confidence만 허용. macro는 별도 feature candidate로 처리	모든 뉴스를 억지로 티커에 붙이지 않기. similarity만으로 매핑 확정하지 않기	ambiguous mapping은 CONTEXT_ONLY/BLOCKED. macro 뉴스는 ticker 없이도 scope/effect window가 있으면 후보 가능
3. 과제별 상세 판단
1) Wikimedia 정책
결론

정오 보정은 허용하되, “실제 source time”이 아니라 “imputed nominal time”으로만 써야 합니다.

Wikidata/Wikimedia 계열 날짜는 time precision을 갖습니다. Wikidata 문서 기준으로 year/month/day precision이 구분되며, time datatype은 precision 값을 포함합니다. 
위키데이터
 별도 property 설명에서도 year precision은 9, month는 10으로 표현됩니다. 
위키데이터

따라서 아래처럼 다뤄야 합니다.

Wikimedia 날짜 수준	L1 처리	L2 처리	매매 feature 가능성
초/분/시 precision	거의 드묾. 원문 출처 확인 필요	원문 source time 있으면 검토	가능성 있음
일 precision	YYYY-MM-DD 12:00:00 보정 가능. 단 is_imputed_time=true	같은 날 intraday feature 금지. 보수적으로 next session부터	제한적 가능
월 precision	월 전체 기간으로만 취급	effect window 불명확하면 차단	원칙적 금지
년 precision	연 단위 context만 가능	trading feature 금지	금지
circa / earliest/latest / 불명확	context only	feature 금지	금지
써도 되는 경우

Wikimedia는 아래 용도에는 유용합니다.

사용 가능 용도	예시
엔티티 보조 정보	회사명, 산업, 국가, 설립연도
티커 매핑 보조	기업명 disambiguation 보조
장기 context	산업 분류, 인수합병 과거 히스토리, 제품 출시연도
진단용 캘린더 보조	“이 이벤트가 대략 언제 있었는가” 수준
막아야 하는 경우

아래는 막아야 합니다.

막아야 하는 사용	이유
earnings/guidance 이벤트의 source time 대체	시장이 언제 알았는지가 핵심
M&A/소송/파산/규제 뉴스의 당일 feature	실제 공개시각이 중요
intraday feature	날짜만으로는 장중 어느 시점에 알려졌는지 모름
단독 source로 feature admit	원문/공식 source time 없음
year/month precision을 day처럼 보정	look-ahead 또는 잘못된 effect window 위험
권장 상태명

Wikimedia에는 아래 상태명을 쓰는 것이 좋습니다.

WIKIMEDIA_DATE_CONTEXT_CERTIFIED
WIKIMEDIA_DATE_IMPUTED_DAY_ONLY
WIKIMEDIA_DATE_PRECISION_INSUFFICIENT
WIKIMEDIA_SOURCE_TIME_NOT_MARKET_USABLE

핵심은 STRICT_SOURCE_TIME_CERTIFIED를 주지 않는 것입니다.
Wikimedia의 날짜는 대부분 “event date”이지 “market learned time”이 아닙니다.

2) 매매판단용 trading feature 기준과 검증
최소 기준

뉴스/매크로가 trading feature가 되려면 최소한 아래 조건을 통과해야 합니다.

기준	설명	미충족 시
source time	데이터가 시장 의사결정 시점 전에 존재했는지 확인	BLOCKER
activation time	언제부터 feature로 써도 되는지 정의	BLOCKER
raw integrity	원본 파일/row/hash/URL/DB id 추적 가능	BLOCKER
mapping	ticker/entity/sector/macro 연결이 명확	CONTEXT_ONLY 또는 BLOCKER
dedup	같은 뉴스가 여러 source에서 중복 계산되지 않음	BLOCKER
stale policy	오래된 뉴스/누락 뉴스 처리 방식 명시	UNKNOWN/BLOCKER
effect window	효과를 볼 기간이 사전 정의됨	BLOCKER
leakage check	미래 정보를 현재 feature에 섞지 않음	BLOCKER
materialization contract	feature table/score 생성 조건 명확	BLOCKER
L1/L2/L3 역할 구분
Layer	해야 할 검증	하지 말아야 할 것
L1	source time, raw evidence, mapping 초안, authority 상태	효과 검증, alpha 판단, feature score 생성
L2	feature admission, dedup, stale, activation time, effect window, leakage check	전략 판단, 포트폴리오 sizing, paper/live 권한 부여
L3	admitted feature만 받아 signal/diagnostic analysis	context-only 데이터를 몰래 feature처럼 사용
절대 admit 금지 조건

아래 하나라도 있으면 L2 feature admit 금지입니다.

- source_time 없음
- source_time이 imputed인데 activation policy 없음
- raw evidence 추적 불가
- ticker/entity/macro mapping 불명확
- dedup key 없음
- stale policy 없음
- effect window 미정
- legacy L2 news path에서 온 데이터
- CONTEXT_ONLY/DISCOVERY_ONLY 상태
- materialization false 계약을 우회
3) 스케줄러 실행/검수
결론

대형 운영 시스템이 필요하지 않습니다.
지금은 기존 scheduler registry + post-run validation hook + run_state 파일이면 충분합니다.

최소 운영 루프
L0 collect
→ normalize
→ L1 validate
→ run_state 기록
→ L2 intake candidate 갱신 여부 확인
→ feature materialization false 확인
남겨야 하는 상태

각 실행마다 아래 정도만 남기면 충분합니다.

필드	설명
run_id	실행 단위 id
source_family	daily_bars, market_bars_5m, news 등
collector_version	수집기 버전 또는 git/local hash
started_at, ended_at	실행 시각
raw_rows	수집 row
l1_valid_rows	L1 통과 row
blocked_rows	차단 row
latest_source_time	가장 최신 source time
max_staleness	가장 오래된 gap
authority_status	family 단위 상태
failure_type	실패 유형
block_reason	사람이 읽을 수 있는 차단 사유
artifact_paths	validation report 위치
실패 상태 예시
실패	남길 상태
L0 수집 실패	L0_COLLECT_FAILED
source time 없음	SOURCE_TIME_MISSING_BLOCKER
source time stale	STALE_SOURCE_TIME_UNKNOWN_BLOCKER
raw hash 없음	RAW_INTEGRITY_BLOCKER
mapping 불명확	MAPPING_AMBIGUOUS_CONTEXT_ONLY
legacy 경로 유입	LEGACY_PATH_QUARANTINED
Chrome 결과 publish time 없음	CHROME_SOURCE_TIME_BLOCKED
과도한 구현을 피하는 기준

지금은 아래를 만들 필요가 없습니다.

- Airflow/Prefect급 orchestration
- alert daemon
- dashboard server
- retry queue system
- distributed worker
- crawler farm

지금 필요한 것은 반복 실행 증거와 실패 시 차단 상태입니다.

4) Validator 분리
결론

validator는 3개로 나누되, 검증 로직은 하나의 공통 contract에서 재사용해야 합니다.

Validator	책임	입력	출력
L1 validator	source time/raw/mapping/authority 검문	L0 normalized rows	L1 상태 리포트
L2 intake validator	L1 후보가 L2 intake로 안전하게 들어왔는지 확인	L2 intake rows	intake 승인/차단 리포트
Feature admission validator	실제 feature로 admit 가능한지 최종 검증	feature candidate rows	admit/reject 리포트
중복 방지 구조

중복을 막으려면 아래처럼 가야 합니다.

common_contract
  - required field definitions
  - status enum
  - source_time checks
  - raw integrity checks
  - mapping status checks
  - stale policy checks
  - authority transition rules

l1_validator
  - common_contract 호출
  - L1 관점 결과만 출력

l2_intake_validator
  - common_contract 호출
  - L1→L2 전이만 검증

feature_admission_validator
  - common_contract 호출
  - feature admit 조건만 추가 검증
핵심 규칙

아래는 강제해야 합니다.

L1 CONTEXT_ONLY → L2 candidate 가능
L1 CONTEXT_ONLY → trading feature admit 불가

L1 DISCOVERY_ONLY → L2 discovery candidate 가능
L1 DISCOVERY_ONLY → trading feature admit 불가

L1 STRICT_SOURCE_TIME_CERTIFIED → L2 candidate 가능
L2 admission 통과 전 → feature materialization 불가
5) Chrome crawling 추가
결론

Chrome crawling은 마지막 수단이어야 합니다.
API/RSS/HTTP로 가능한 source는 Chrome을 쓰지 않는 것이 맞습니다.

Chrome crawling이 맞는 경우
경우	설명
JS 렌더링 페이지	HTTP 요청으로 본문/날짜가 안 나오는 경우
공식 사이트인데 RSS/API 없음	회사 IR, regulator page, exchange notice 등
동적 표/캘린더	브라우저 렌더링 후에만 보이는 경우
HTTP extraction이 반복 실패	단, source가 중요하고 allowlist에 있어야 함
Chrome crawling이 맞지 않은 경우
경우	이유
일반 뉴스 대량 수집	느리고 불안정
RSS/API가 있는 source	더 안정적인 경로가 이미 있음
paywall/login 필요	법적/약관 리스크
Bloomberg/Reuters류 유료 source 우회	금지
고빈도 intraday 수집	브라우저 방식은 부적합
feature 직접 생성	Chrome은 raw acquisition일 뿐
L1/L2 제한

Chrome 결과는 아래처럼 제한해야 합니다.

Layer	처리
L0	HTML snapshot, screenshot 선택, extracted text, fetched_at, URL, hash 저장
L1	publish_time/source_time 없으면 STRICT 금지
L2	Chrome 데이터도 일반 뉴스와 동일한 admission gate 통과 필요
L3	admitted feature 아니면 signal로 사용 금지
권장 상태명
CHROME_RAW_CAPTURED
CHROME_SOURCE_TIME_PARSED
CHROME_SOURCE_TIME_MISSING_BLOCKER
CHROME_CONTEXT_ONLY
CHROME_NOT_FEATURE_ADMISSIBLE
6) 티커/뉴스 매핑 고도화
결론

뉴스를 무조건 ticker에 붙이면 안 됩니다.
먼저 scope를 나눠야 합니다.

Mapping scope	의미	feature 가능성
TICKER	특정 상장 종목에 직접 연결	HIGH confidence만 가능
ENTITY	기업/기관/인물에는 연결되지만 ticker 불명확	context 후보
SECTOR	산업/테마에 연결	sector feature 후보
MACRO	금리, CPI, 유가, 환율, 정책 등	macro feature 후보
UNKNOWN	연결 불명확	feature 금지
ticker 매핑 기준

단일 ticker feature로 인정하려면 아래 중 하나가 필요합니다.

HIGH confidence 근거	예시
공식 IR/SEC/company source	회사 공시, IR 뉴스
뉴스와이어에 ticker/exchange 명시	NASDAQ: NVDA 식 명시
CIK/ISIN/LEI 등 식별자	기업 고유 id
회사명 + 산업 + 문맥이 모두 일치	동명이인/동명기업 위험 없음
기사 제목/본문에서 해당 기업이 주체	“A acquires B”, “A reports earnings”
애매하면 막아야 하는 경우
애매한 경우	처리
같은 이름의 여러 상장사	BLOCKED
ticker가 일반 단어와 충돌	CONTEXT_ONLY
여러 종목이 같은 비중으로 등장	MULTI_ENTITY_CONTEXT
ETF/지수/회사명이 혼재	SCOPE_UNCLEAR
기사 본문에는 기업명 없고 태그만 있음	LOW confidence
source가 syndication이라 원문이 아님	dedup 전 feature 금지
매크로 뉴스 처리

매크로 뉴스는 특정 ticker가 없어도 feature 후보가 될 수 있습니다.
다만 ticker feature가 아니라 macro scope feature여야 합니다.

예시는 아래와 같습니다.

Macro feature 후보	scope	affected universe
CPI surprise	MACRO_US_INFLATION	rates-sensitive equities, QQQ, semis 등 사전 정의
Fed rate decision	MACRO_US_RATES	growth/financials/bonds/FX
oil shock	MACRO_OIL	energy, airlines, chemicals
export control	MACRO_POLICY_SEMIS	semiconductor universe
USD spike	MACRO_FX_USD	exporters/importers/global tech

주의할 점은 이것입니다.

macro 뉴스는 “모든 종목에 다 영향”으로 처리하면 안 됩니다.
affected universe와 effect window가 사전 정의되어야 feature 후보가 됩니다.

3. 우선순위
P0 — 바로 해야 함
우선순위	작업	이유
P0	L2 feature admission contract 작성	뉴스/매크로 feature화의 핵심 관문
P0	L1/L2/admission validator 분리	지금 상태에서 가장 효과적인 안전장치
P0	source_time / activation_time / imputed_time 정책 확정	look-ahead 방지
P0	ticker/macro mapping scope 계약화	애매한 뉴스 매핑 차단
P0	scheduler post-run L1 validation 상태 기록	“한 번 검증”이 아니라 “계속 검증”으로 전환
P1 — P0 이후 해야 함
우선순위	작업	이유
P1	Wikimedia date precision fixture 추가	날짜 보정 정책 검증
P1	news/macro dedup key 최소 구현	중복 뉴스로 feature 과대평가 방지
P1	stale policy family별 정의	missing/stale을 UNKNOWN/BLOCKER로 일관 처리
P1	Chrome crawling allowlist 정책	필요한 곳에만 제한적으로 사용
P1	macro affected universe 정의	macro feature 후보의 범위 명확화
P2 — 아직 급하지 않음
우선순위	작업	이유
P2	고급 entity resolver	지금은 rule + confidence로 충분
P2	crawler framework	과도함
P2	운영 dashboard	run_state/report로 충분
P2	L3 alpha contribution 분석	L2 admission 후
P2	feature scoring/modeling	admission gate 통과 전 금지
4. 다음 Codex 작업안 — TASK-4138

아래는 바로 Codex에 줄 수 있는 작은 작업 단위입니다.

# TASK-4138 — L2 Feature Admission Contract + Minimal Validation Gate

## 목적

L1에서 넘어온 뉴스/매크로/Wikimedia/Chrome 후보 데이터를 곧바로 trading feature로 쓰지 않도록,
L2 feature admission contract와 최소 validator를 만든다.

현재 안전 경계는 유지한다.

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data = UNKNOWN/BLOCKER
- L2 feature materialization = false 유지
- trading authority opened = false 유지

## 범위

1. L2 feature admission contract 문서 작성
   - source_time
   - source_time_precision
   - source_time_kind
   - is_imputed_time
   - activation_time / usable_after
   - raw evidence
   - mapping scope
   - mapping confidence
   - dedup key
   - stale policy
   - effect window
   - authority transition
   - forbidden admission states

2. Wikimedia date policy 문서화
   - day precision: 정오 보정 가능, 단 imputed 표시 필수
   - month/year precision: trading feature 금지 또는 context only
   - Wikimedia 날짜를 STRICT_SOURCE_TIME_CERTIFIED로 올리지 않음
   - source_time과 event_time을 분리

3. mapping scope contract 작성
   - TICKER
   - ENTITY
   - SECTOR
   - MACRO
   - UNKNOWN
   - single ticker feature는 HIGH confidence만 허용
   - ambiguous mapping은 CONTEXT_ONLY/BLOCKED

4. validator 구조 정리
   - L1 validator
   - L2 intake validator
   - feature admission validator
   - 공통 contract/check는 중복 구현하지 않음

5. 최소 fixture 추가
   - PASS: daily_bars strict source time
   - PASS: market_bars_5m strict source time
   - BLOCK: Wikimedia year/month precision
   - BLOCK: Wikimedia day precision but no activation policy
   - BLOCK: news article with ambiguous ticker mapping
   - BLOCK: macro news without affected universe/effect window
   - BLOCK: Chrome crawl result without publish_time
   - BLOCK: newswire discovery row without dedup/mapping
   - PASS_AS_CONTEXT_ONLY: context news with source_time but no effect window

6. scheduler run_state contract 추가
   - L0 수집 후 L1 validation 결과를 남기는 최소 run_state 형식 정의
   - run_id, source_family, row_count, latest_source_time, status, blocker_reason, artifact_paths 포함

## 명시적 금지

- L3 signal 연결 금지
- feature table materialization 금지
- trading score 생성 금지
- backtest 성능 주장 금지
- paper/live 권한 변경 금지
- broker/order 관련 파일 변경 금지
- legacy L2 news builder 복구 금지
- 범용 Chrome crawler framework 구현 금지

## 완료 기준

1. 기존 TASK-4136 상태가 유지되어야 한다.
   - L2 intake rows: 5
   - news/macro future feature path rows: 3
   - admitted as trading feature now: 0
   - legacy L2 news builder: quarantined
   - L1 validation hooks: 3
   - L1 validation smoke pass: 3/3
   - L2 feature materialization: false
   - trading authority opened: false

2. 새 validator가 아래를 증명해야 한다.
   - CONTEXT_ONLY는 L2 candidate가 될 수 있지만 trading feature admit은 불가
   - DISCOVERY_ONLY는 discovery candidate까지만 가능
   - imputed source time은 activation policy 없으면 feature admit 불가
   - ambiguous ticker mapping은 feature admit 불가
   - macro feature는 affected universe와 effect window 없으면 admit 불가
   - Chrome crawl 결과는 publish_time/source_time 없으면 STRICT 불가

3. 산출물
   - L2 feature admission contract 문서
   - Wikimedia date policy 문서
   - mapping scope contract 문서
   - validator 분리 계획 또는 최소 구현
   - fixture 기반 validation evidence
   - TASK-4138 report
   - artifact manifest
최종 판단

현재 로컬 요약 기준으로 보면, 방향은 좋습니다.
다만 다음 단계에서 가장 위험한 지점은 “context 후보가 어느 순간 feature처럼 섞이는 것”입니다.

따라서 TASK-4138의 핵심은 새 기능을 많이 만드는 것이 아니라, 아래 3개를 확정하는 것입니다.

L2 feature admission contract

source time / imputed time / activation time 정책

mapping scope + confidence 기준

이 3개가 잡히면 뉴스/매크로/Wikimedia/Chrome을 “영구 참고자료”로 묶지 않으면서도, 아직 검증되지 않은 데이터를 매매 판단에 섞는 사고를 막을 수 있습니다.
