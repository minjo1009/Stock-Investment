핵심 3줄 요약

L3의 목표는 “L2 primitive facts를 사람이 검토 가능한 경제적 의미·관계 그래프로 바꾸는 것”입니다. 매수/매도, 랭킹, 사이징, 주문, paper/live 권한은 절대 만들면 안 됩니다.

기존 src/brain/l3 코드는 통째 복구하지 말고, 새 L2 read-view에 맞춘 task-scoped bridge를 먼저 만드는 하이브리드가 맞습니다. 예전 L3 개념은 재사용하되, 예전 src.l2.contracts.L2PrimitiveFact 의존은 위험합니다.

TASK-4149의 1차 구현은 L3 Diagnostic Strategy View Bootstrap으로 제한해야 합니다. 즉, L2 후보 → L3 의미 record → evidence edge → relation graph → blocker/gap ledger → validator까지가 범위입니다.

TASK-4149 L3 Diagnostic Strategy View Bootstrap 검토안

근거 범위: 사용자가 제공한 TASK-4149 L3 Local Context Packet만 사용했습니다. GitHub, 외부 repo, 최신 원격 상태는 판단 근거로 쓰지 않았습니다.

1. L3 목표 정의 — 운영 언어 기준
L3의 목표

L3는 L2에서 검문을 통과한 원시 사실/primitive feature candidate를 읽고, 그것이 어떤 경제적 의미를 갖는지, 어떤 기업·섹터·매크로 주제와 연결되는지, 그 관계가 지지/위험/혼합/문맥/차단 상태인지 정리하는 진단 레이어입니다.

더 쉽게 말하면:

“이 뉴스/매크로/뉴스와이어 조각이 투자 판단에 참고될 수 있는 경제 사건인지, 어떤 대상과 연결되는지, 근거가 충분한지, 모순이나 공백은 없는지를 사람이 볼 수 있게 정리하는 층”

L3가 답해야 하는 질문

L3는 다음 질문에 답해야 합니다.

질문	L3 출력
이 L2 primitive는 경제적으로 어떤 사건인가?	economic_dimension, event_class, reason_codes
어떤 기업/섹터/테마/매크로 변수와 연결되는가?	L3EvidenceEdge
근거 방향은 지지인가, 위험인가, 혼합인가, 단순 문맥인가?	L3RelationGraphState
증거가 충분한가, 막힌 곳은 무엇인가?	critical_blockers, noncritical_gaps, coverage_state
최신성/출처/완전성/모순 상태는 어떤가?	freshness_decay_score, source_reliability_score, evidence_completeness_score, contradiction_flags
L4가 thesis bundle을 만들 수 있는 후보인가?	후보 검토 상태만 제공. L4 생성/승인 아님.
L3가 절대 하면 안 되는 것

L3는 아래를 만들면 안 됩니다.

BUY

SELL

HOLD

REDUCE

EXIT

RERISK

종목 ranking

alpha score

sentiment score

forward return

realized return

expected return

sizing

order intent

broker mutation

paper/live eligibility

strategy acceptance

deployment readiness

L3의 방향성은 “트레이딩 방향”이 아니라 “증거 검토 방향”이어야 합니다.

예:

허용	금지
SUPPORT_DOMINANT_REVIEW	BUY_SIGNAL
RISK_DOMINANT_REVIEW	SELL_SIGNAL
MIXED_REVIEW	HOLD
CONTEXT_ONLY	WATCHLIST_RANK
BLOCKED_CRITICAL	NO_TRADE
INSUFFICIENT_EVIDENCE	REJECTED_ALPHA
2. L3에서 먼저 구현해야 할 핵심 기능

TASK-4149 1차 범위는 L3 전체 완성이 아니라 bootstrap 가능한 최소 안전 뼈대여야 합니다.

P0 기능
2.1 L2 read-view input bridge

현재 L2는 package-level canonical object보다는 artifact/read-view oriented 상태입니다. 따라서 L3는 예전 src.l2.contracts.L2PrimitiveFact를 바로 import하지 말고, 현재 L2 산출물을 읽어 내부 L3 입력 객체로 정규화해야 합니다.

필요 기능:

L2 diagnostic feature candidate artifact 읽기

L1 gate state 확인

L2 admission/review state 확인

mapping 상태 확인

dedupe/canonical 상태 확인

stale/source-time/leakage guard 상태 확인

whitelisted column만 사용

L0 raw 직접 접근 금지

2.2 L3 economic meaning record 생성

L2 primitive 한 건 또는 canonical primitive 묶음에서 아래 형태의 L3 record를 만듭니다.

예시 필드:

l3_meaning_id
l2_row_id
l1_packet_id
source_family
source_time_utc
receipt_time_utc
entity_key
mapping_state
dedupe_state
economic_dimension
event_class
horizon_hint
direction_review
confidence_band
static_confidence_value
calibration_status
calibrated_probability
reason_codes
critical_blockers
noncritical_gaps
authority_flags

중요 규칙:

calibrated_probability는 항상 None

calibration_status는 기본 UNCALIBRATED

confidence_band는 high / medium / low / unknown / insufficient

static confidence mapping은 architecture 문서 규칙 유지

high → 0.85

medium → 0.60

low → 0.35

unknown/insufficient → 0.00

2.3 Evidence edge 생성

L3의 핵심은 “사건과 대상 사이의 관계”입니다.

예:

newswire_event -> company_entity
macro_event -> sector_theme
market_news_event -> macro_context
supply_chain_event -> related_industry

edge는 다음 정보를 가져야 합니다.

edge_id
from_l3_meaning_id
to_node_type
to_node_key
economic_dimension
edge_state
review_strength_band
source_reliability_component
freshness_component
evidence_completeness_component
contradiction_flag
critical_blocker_flag
reason_codes

review_strength_band는 허용 가능하지만, 이것을 ranking이나 alpha score로 쓰면 안 됩니다.

2.4 Relation graph aggregation

L3는 개별 record만 만들면 부족합니다. 동일 기업/섹터/테마/매크로 주제별로 evidence edge를 모아 graph state를 만들어야 합니다.

허용 graph state:

SUPPORT_DOMINANT_REVIEW

RISK_DOMINANT_REVIEW

MIXED_REVIEW

CONTEXT_ONLY

BLOCKED_CRITICAL

INSUFFICIENT_EVIDENCE

예시 출력:

graph_key = entity:AAPL | horizon:swing_1m | dimension:pricing_power

support_edge_count = 3
risk_edge_count = 1
context_edge_count = 2
critical_blocker_count = 0
noncritical_gap_count = 1
contradiction_count = 1
graph_state = MIXED_REVIEW

이 graph는 L4 thesis bundle의 입력 후보일 수는 있지만, L4를 직접 만들면 안 됩니다.

2.5 Coverage/blocker/gap ledger

현재 L0 backfill은 살아 있지만, public newswire와 public market/macro news coverage는 아직 incomplete입니다.

따라서 L3는 반드시 별도 ledger를 만들어야 합니다.

필수 분류:

상태	L3 처리
incomplete backfill	coverage_gap 또는 BLOCKED_CRITICAL
L1 blocked packet	L3 active meaning 생성 금지
UNKNOWN mapping	active candidate 금지, review queue로 분리
stale row	stale blocker/gap으로 기록. 부정 증거로 해석 금지
duplicate non-canonical row	독립 L3 candidate 금지
source-time/leakage 불명확	BLOCKED_CRITICAL 또는 INSUFFICIENT_EVIDENCE
3. 추천 architecture 및 file/artifact plan
3.1 권장 구조

권장안: task-scoped L3 bootstrap package + 최소 contract 재정의

기존 src/brain/l3를 바로 복구하지 말고, 아래처럼 TASK-4149 전용 package를 추가하는 방식이 안전합니다.

src/brain/l3_diagnostic_strategy_view_bootstrap/
  __init__.py
  contracts.py
  l2_read_view_bridge.py
  coverage_policy.py
  economic_meaning_classifier.py
  evidence_edge_builder.py
  relation_graph_aggregator.py
  artifact_writer.py
이유

현재 context상 위험이 큽니다.

기존 src/brain/l3/* 다수 파일이 deleted 상태

기존 L3 adapter는 src.l2.contracts.L2PrimitiveFact를 기대

현재 L2는 artifact/read-view oriented

src/l2/*도 삭제된 파일이 있어 import surface 불안정

예전 L3를 통째 restore하면 새 L0-L2 handoff를 우회하거나 깨뜨릴 가능성 있음

따라서 TASK-4149에서는 새 bridge가 현재 L2 artifact/read-view를 읽고, 내부 L3 diagnostic object로 정규화하는 방식이 맞습니다.

3.2 파일 계획
Config
configs/l3_diagnostic_strategy_view_bootstrap_4149.json

역할:

L2 input artifact path

optional L1 packet artifact path

L0 status path

whitelisted input columns

mapping field aliases

source family policy

stale/effect-window policy

output artifact directory

authority hard flags

예시 config 개념:

JSON
{
  "task_id": "TASK-4149",
  "mode": "DIAGNOSTIC_ONLY",
  "input": {
    "l2_diagnostic_feature_candidates": "data/artifacts/.../l2_diagnostic_feature_candidates.jsonl",
    "l1_packets": "data/artifacts/.../l1_packets.jsonl",
    "l0_status": "data/artifacts/l0_collection_status/current_status.json"
  },
  "column_whitelist": [
    "l2_row_id",
    "l1_packet_id",
    "source_family",
    "source_time_utc",
    "receipt_time_utc",
    "mapping_state",
    "entity_key",
    "dedupe_state",
    "is_canonical",
    "primitive_type",
    "primitive_subtype",
    "event_class",
    "effect_window_state",
    "stale_state",
    "lineage_state",
    "leakage_guard_state",
    "reason_codes"
  ],
  "authority": {
    "strategy": "NOT_ACCEPTED",
    "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    "real_capital": "FORBIDDEN",
    "broker_mutation": false,
    "live_order": false,
    "paper_promotion": false,
    "signal_export_allowed": false
  }
}

실제 field명은 Codex가 로컬 artifact를 보고 mapping하면 됩니다. 단, 없는 field는 추정하지 말고 blocker로 처리해야 합니다.

Source package
src/brain/l3_diagnostic_strategy_view_bootstrap/contracts.py

역할:

dataclass / enum 정의

금지 action vocabulary 차단

L3 review state 정의

confidence band 정의

authority flags 정의

핵심 enum:

L3GraphState
L3DirectionReview
L3CalibrationStatus
L3MappingState
L3BlockerSeverity
L3EconomicDimension
src/brain/l3_diagnostic_strategy_view_bootstrap/l2_read_view_bridge.py

역할:

L2 artifact 읽기

whitelist column 검증

L1/L2 gate state 검증

UNKNOWN mapping 분리

duplicate non-canonical 분리

stale/source-time 문제 분리

내부 L3InputPrimitive로 변환

src/brain/l3_diagnostic_strategy_view_bootstrap/coverage_policy.py

역할:

L0 status file 읽기

incomplete backfill lane 확인

coverage gap/blocker 계산

missing/stale를 negative evidence로 바꾸지 않도록 강제

src/brain/l3_diagnostic_strategy_view_bootstrap/economic_meaning_classifier.py

역할:

primitive type/subtype/event_class를 경제 의미로 변환

rule-based deterministic classifier

LLM/embedding/ML 금지

sentiment score 금지

alpha score 금지

경제 dimension 예시:

DEMAND
SUPPLY
PRICING
MARGIN
CAPEX
GUIDANCE
LIQUIDITY
RATES
INFLATION
FX
ENERGY
REGULATORY
GEOPOLITICAL
SUPPLY_CHAIN
CUSTOMER_ORDER
COMPETITION
EARNINGS_CONTEXT
SECTOR_CONTEXT
MACRO_CONTEXT
src/brain/l3_diagnostic_strategy_view_bootstrap/evidence_edge_builder.py

역할:

L3 meaning record에서 edge 생성

entity/theme/macro node 연결

support/risk/context/mixed review만 허용

trading signal vocabulary 차단

src/brain/l3_diagnostic_strategy_view_bootstrap/relation_graph_aggregator.py

역할:

edge를 graph key별 집계

graph state 생성

contradiction/gap/blocker count 생성

ranking 금지

sorting은 deterministic artifact readability 목적만 허용

src/brain/l3_diagnostic_strategy_view_bootstrap/artifact_writer.py

역할:

jsonl/csv/json/md 산출물 저장

row count reconciliation

authority flags 포함

input manifest hash 저장

Scripts
scripts/build_l3_diagnostic_strategy_view_4149.py
scripts/validate_l3_diagnostic_strategy_view_4149.py

build script:

config load

L2 artifact load

L0 coverage context load

bridge normalization

meaning generation

edge generation

graph aggregation

artifacts write

validate script:

output artifact 존재 확인

forbidden vocabulary 확인

no signal/order/broker/paper/live authority 확인

L1/L2 bypass 없음 확인

UNKNOWN mapping active candidate 없음 확인

blocked L1 active candidate 없음 확인

duplicate non-canonical active candidate 없음 확인

calibrated_probability null 확인

coverage gaps explicit 확인

row reconciliation 확인

Tests
tests/test_l3_diagnostic_strategy_view_bootstrap_4149.py

테스트는 fixture 기반 pure unit test로 충분합니다.

필수 테스트:

L1 blocked packet은 active L3 meaning 생성 금지

UNKNOWN mapping은 review queue로 이동

duplicate non-canonical row는 active edge 생성 금지

stale row는 negative evidence가 아니라 blocker/gap으로 기록

incomplete backfill은 coverage gap으로 기록

calibrated_probability는 None

forbidden action vocabulary가 output에 없음

relation graph state는 허용 enum만 사용

L0 raw input path를 사용하지 않음

build output row count reconciliation 정상

3.3 Artifact plan
data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/
  l3_input_manifest.json
  l3_meanings.jsonl
  l3_evidence_edges.jsonl
  l3_relation_graph.json
  l3_blocker_gap_ledger.csv
  l3_review_summary.csv
  l3_rejected_or_review_queue.csv
  l3_validator_report.json
최소 artifact 설명
Artifact	목적
l3_input_manifest.json	어떤 L2/L1/L0 status artifact를 읽었는지, hash/count 기록
l3_meanings.jsonl	L2 primitive → L3 economic meaning 변환 결과
l3_evidence_edges.jsonl	meaning과 entity/theme/macro node 관계
l3_relation_graph.json	graph key별 review state
l3_blocker_gap_ledger.csv	incomplete/blocked/unknown/stale/coverage gap 명시
l3_review_summary.csv	사람이 볼 수 있는 요약
l3_rejected_or_review_queue.csv	active candidate가 되지 못한 row 사유
l3_validator_report.json	hard boundary 검증 결과
Report
docs/reports/task_4149_l3_diagnostic_strategy_view_bootstrap/
  l3_diagnostic_strategy_view_bootstrap_report.md
  artifact_manifest.csv
  validation_output.txt
4. 기존 src/brain/l3 복구 vs 신규 bridge vs hybrid 판단
결론: hybrid가 맞습니다

통째 복구는 금지, 신규 task-scoped bridge를 만들고, 기존 L3 설계의 enum/개념만 선별 재사용하는 hybrid가 가장 안전합니다.

판단
선택지	판단	이유
기존 src/brain/l3 통째 복구	비추천	old adapter가 src.l2.contracts.L2PrimitiveFact를 기대. 현재 L2 surface와 불일치 위험
완전 신규 L3	부분 비추천	기존 architecture 문서의 graph state/contract 개념을 버리면 레이어 일관성 약화
task-scoped bridge + 기존 L3 개념 선별 재사용	추천	현재 L2 artifact/read-view와 맞고, 기존 L3 설계와도 호환 가능
구체 지시

Codex에게는 이렇게 지시하는 것이 좋습니다.

deleted 상태의 기존 src/brain/l3/*를 무조건 restore하지 말 것

기존 architecture 문서의 용어는 유지

기존 old module code는 참고만 할 것

src.l2.contracts import는 금지 또는 optional fallback으로만 둘 것

TASK-4149 전용 package에서 L2 artifact/read-view를 읽는 bridge를 만들 것

추후 compatibility가 확인되면 task-scoped package를 정식 src/brain/l3로 승격할 것

5. L3가 현재 L0-L2 output을 소비하는 방식
5.1 허용 input

L3가 읽을 수 있는 것은 다음입니다.

Source	L3 사용 방식
L2 diagnostic feature candidate artifacts	주 input
L2 read-view / materialized primitive rows	주 input
L1 packet gate state	L2 row 검증용
L0 collection status current_status.json	coverage context only
L0 raw source rows	금지
5.2 금지 input

L3는 아래를 직접 읽으면 안 됩니다.

L0 raw article/news/newswire rows

collector DB raw table

market data raw table

unmapped raw item rows

source text full body, unless L2 whitelisted excerpt/hash로 제공한 경우

broker/order/paper/live table

realized return / forward return / PnL table

5.3 L1/L2 우회 방지 규칙

L3 active candidate가 되려면 최소 조건을 만족해야 합니다.

L1 gate state = READY
L2 admission state = ADMITTED or REVIEW_SAFE
mapping state = KNOWN or CANONICAL_MAPPED
dedupe state = CANONICAL
source-time/leakage guard = PASS or REVIEW_SAFE
stale state = NOT_STALE or REVIEW_SAFE

단, 실제 enum 명칭은 로컬 artifact에 맞춰 mapping하면 됩니다.

중요한 점은:

L2 review라고 해서 자동 active candidate가 되면 안 됨

UNKNOWN mapping은 active graph에 들어가면 안 됨

L1 blocked packet은 L3 meaning을 만들면 안 됨

non-canonical duplicate는 edge를 만들면 안 됨

6. incomplete backfill, blocked packet, UNKNOWN mapping, stale row, coverage gap 처리
6.1 incomplete backfill

현재 L0는 worker가 살아 있지만, public newswire와 public market/macro news의 backfill coverage는 아직 incomplete입니다.

L3 처리:

coverage_state = INCOMPLETE
critical_blocker 또는 noncritical_gap 기록
missing evidence를 negative evidence로 해석 금지

예:

잘못된 처리	올바른 처리
“해당 기업에 뉴스가 없으므로 리스크 없음”	“public newswire coverage incomplete → insufficient evidence”
“macro risk 부재”	“macro backfill incomplete → macro coverage gap”
6.2 L1 blocked packet

L1 blocked packet은 L3 active meaning으로 들어오면 안 됩니다.

처리:

active_l3_candidate = false
queue = l3_rejected_or_review_queue
reason = L1_BLOCKED
graph_state = BLOCKED_CRITICAL or excluded from graph
6.3 UNKNOWN mapping

UNKNOWN mapping은 기업/섹터/테마 edge를 만들면 안 됩니다.

처리:

active_l3_candidate = false
reason = UNKNOWN_MAPPING
route = review_queue

허용되는 것은 source-level context 기록 정도입니다.

6.4 stale row

stale row는 부정 evidence가 아닙니다.

처리:

freshness_component = 0 or decayed
critical_blocker/noncritical_gap 기록
direction_review = CONTEXT_ONLY or INSUFFICIENT_EVIDENCE

금지:

RISK_DOMINANT_REVIEW because stale

stale은 “나쁜 뉴스”가 아니라 “판단에 쓰기 어렵다”입니다.

6.5 coverage gap

coverage gap은 별도 ledger에서 추적해야 합니다.

예시:

coverage_gap_id
lane
source_family
expected_window
observed_window
gap_type
severity
affected_graph_keys
negative_evidence_allowed = false
7. news, macro, newswire를 diagnostic trading-feature candidate로 바꾸는 방식
기본 원칙

뉴스/매크로/뉴스와이어는 L3에서 trading signal이 아니라 economic evidence candidate가 됩니다.

즉:

raw/public item
-> L1 source evidence packet
-> L2 primitive feature candidate
-> L3 economic meaning + relation edge

여기서 끝입니다.

L3가 L4/L5/L6로 넘어갈 수 있는 것은 검토 가능한 의미와 관계 상태이지, trading action이 아닙니다.

7.1 Newswire

뉴스와이어는 보통 기업 event에 강합니다.

예시 dimension:

Newswire 내용	L3 economic dimension
신규 수주	CUSTOMER_ORDER, DEMAND
공장 증설	CAPEX, SUPPLY
제품 출시	PRODUCT, DEMAND
가이던스 발표	GUIDANCE, EARNINGS_CONTEXT
규제 승인	REGULATORY
리콜/소송	REGULATORY, RISK_CONTEXT
자금조달	LIQUIDITY, CAPITAL_STRUCTURE

L3 output은 예를 들어:

entity = company:X
economic_dimension = CUSTOMER_ORDER
direction_review = SUPPORT_REVIEW
graph_state = SUPPORT_DOMINANT_REVIEW

단, 이것은 BUY가 아닙니다.

7.2 Macro news

매크로 뉴스는 기업 직접 signal이 아니라 context edge가 우선입니다.

예:

Macro 내용	L3 edge
금리 상승	macro:rates -> sector:long_duration_growth
유가 상승	macro:energy -> sector:airlines / chemicals / energy
달러 강세	macro:fx_usd -> exporters/importers
인플레이션 둔화	macro:inflation -> margin/rates context

출력은:

to_node_type = MACRO_CONTEXT or SECTOR_THEME
edge_state = CONTEXT_ONLY / RISK_REVIEW / SUPPORT_REVIEW

금지:

macro_score = 0.82 therefore BUY semiconductor
7.3 Public market news

시장 뉴스는 sector/theme context로 처리합니다.

예:

AI infrastructure capex news
-> theme:AI_INFRA
-> related sectors:semiconductor, power, cooling, data_center
-> graph_state: SUPPORT_DOMINANT_REVIEW or MIXED_REVIEW

다만 여기서도 종목 ranking을 만들면 안 됩니다.

8. 최소 output artifacts 및 validators
8.1 최소 output artifacts

TASK-4149에서 반드시 만들어야 하는 artifact는 아래 6개입니다.

1. l3_input_manifest.json
2. l3_meanings.jsonl
3. l3_evidence_edges.jsonl
4. l3_relation_graph.json
5. l3_blocker_gap_ledger.csv
6. l3_validator_report.json

가능하면 추가:

7. l3_review_summary.csv
8. l3_rejected_or_review_queue.csv
9. docs/reports/.../l3_diagnostic_strategy_view_bootstrap_report.md
10. docs/reports/.../artifact_manifest.csv
8.2 Validator 필수 조건

validate_l3_diagnostic_strategy_view_4149.py는 최소한 아래를 검증해야 합니다.

Validator check	Severity
output artifact 존재	P0
모든 active L3 row가 L2 input lineage를 가짐	P0
L1 blocked row가 active L3 candidate에 없음	P0
UNKNOWN mapping row가 active edge/graph에 없음	P0
duplicate non-canonical row가 독립 edge로 없음	P0
stale/incomplete/missing이 negative evidence로 쓰이지 않음	P0
forbidden trading vocabulary 없음	P0
broker/order/paper/live authority flag false	P0
calibrated_probability is None unless CALIBRATED	P0
graph state가 허용 enum 안에 있음	P0
L0 raw input 직접 사용 흔적 없음	P0
row count reconciliation 가능	P1
coverage gap ledger 존재	P1
report와 artifact manifest 존재	P1

Forbidden vocabulary는 단순 문자열 검사만으로 완벽하지 않지만, bootstrap validator에서는 1차 방어로 가치가 있습니다.

금지어 예시:

BUY
SELL
ORDER
LIVE
PAPER_ELIGIBLE
BROKER_MUTATION
POSITION_SIZE
TARGET_WEIGHT
ALPHA_SCORE
RANK
EXPECTED_RETURN
FORWARD_RETURN
REALIZED_RETURN

주의: 문서에서 “금지어 목록 설명” 용도로 등장할 수는 있으므로, validator는 output artifact의 action/state field 중심으로 검사하는 것이 좋습니다. 단순 전체 파일 문자열 scan만 쓰면 false positive가 날 수 있습니다.

9. 구현 순서
Step 1 — Input contract 고정

Codex가 먼저 해야 할 일:

로컬 L2 artifact/read-view 위치 확인

TASK-4146/4147 output 중 L3 input으로 쓸 파일 결정

column whitelist 작성

missing column은 추정하지 않고 blocker 처리

산출:

configs/l3_diagnostic_strategy_view_bootstrap_4149.json
Step 2 — Task-scoped contracts 생성
src/brain/l3_diagnostic_strategy_view_bootstrap/contracts.py

여기서 enum/dataclass를 고정합니다.

핵심:

no dependency on src.l2.contracts

no broker/order/paper/live imports

no L4/L5/L6 imports

pure data objects only

Step 3 — L2 read-view bridge 구현
l2_read_view_bridge.py

기능:

json/jsonl/csv input support

required field mapping

whitelist enforcement

gate/mapping/dedupe/stale classification

active vs review queue 분리

Step 4 — Coverage policy 구현
coverage_policy.py

기능:

data/artifacts/l0_collection_status/current_status.json 읽기

worker alive와 coverage incomplete를 분리

incomplete lane을 gap/blocker로 기록

missing as negative evidence 금지

Step 5 — Economic meaning classifier 구현
economic_meaning_classifier.py

처음에는 deterministic rule table로 충분합니다.

예:

primitive_type=newswire_contract -> CUSTOMER_ORDER / DEMAND
primitive_type=macro_rates -> RATES / MACRO_CONTEXT
primitive_type=earnings_guidance -> GUIDANCE / EARNINGS_CONTEXT

모르는 것은:

economic_dimension = UNKNOWN
direction_review = CONTEXT_ONLY or INSUFFICIENT_EVIDENCE
Step 6 — Evidence edge builder 구현
evidence_edge_builder.py

기능:

active L3 meaning만 edge 생성

entity_key 없으면 entity edge 금지

macro/theme edge는 mapping policy에 맞는 경우만 허용

blocker/gap 포함

Step 7 — Relation graph aggregator 구현
relation_graph_aggregator.py

기능:

graph key별 aggregation

state 결정

contradiction count

blocker count

gap count

no ranking

Step 8 — Artifact writer 구현
artifact_writer.py

기능:

deterministic output

stable sort by source_time / l2_row_id / graph_key

manifest hash

counts summary

authority flags

Step 9 — Build script 구현
scripts/build_l3_diagnostic_strategy_view_4149.py

CLI:

Bash
python scripts/build_l3_diagnostic_strategy_view_4149.py \
  --config configs/l3_diagnostic_strategy_view_bootstrap_4149.json
Step 10 — Validator 구현
scripts/validate_l3_diagnostic_strategy_view_4149.py

CLI:

Bash
python scripts/validate_l3_diagnostic_strategy_view_4149.py \
  --artifact-dir data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap
Step 11 — Unit test 구현
Bash
python -m unittest tests.test_l3_diagnostic_strategy_view_bootstrap_4149
Step 12 — Report 작성
docs/reports/task_4149_l3_diagnostic_strategy_view_bootstrap/
  l3_diagnostic_strategy_view_bootstrap_report.md
  artifact_manifest.csv
  validation_output.txt

보고서에는 반드시 다음을 넣습니다.

local-only 기준

GitHub 미사용

L3 goal

input artifacts

output artifacts

row counts

blocker/gap counts

forbidden authority all false

validator result

known limitations

next step: L4 handoff는 아직 하지 않음

10. 잘라야 할 overengineering / unsafe scope creep

TASK-4149에서 하면 안 되는 것들입니다.

항목	판단
기존 src/brain/l3 전체 restore	cut
기존 src/l2 전체 restore	cut
DB schema migration	cut
graph database 도입	cut
realtime scheduler 추가	cut
L4 thesis bundle 자동 생성	cut
L5 policy/action 연결	cut
L6 replay/paper/shadow 연결	cut
paper eligibility 생성	cut
broker/order table 접근	cut
alpha/sentiment/ranking score	cut
expected return / forward return 계산	cut
realized return join	cut
ML/embedding/LLM classifier	cut
UI/L7 frontend 작업	cut
calibration 구현	cut
minute/second precision 보강	cut
source crawler 수정	cut

TASK-4149의 목표는 “L3가 안전하게 L2 output을 읽고 경제 의미·관계·차단상태를 진단 artifact로 만드는 최소 시스템”입니다.

11. Risk list
Risk	Severity	설명	대응
L3가 L0 raw를 직접 읽음	P0	L1/L2 gate 우회	L3 input을 L2 read-view artifact로 제한. validator로 raw path 차단
old L3 통째 restore로 import 깨짐	P0	src.l2.contracts 삭제/불일치 가능	task-scoped bridge 사용
UNKNOWN mapping이 active graph에 들어감	P0	잘못된 기업/섹터 연결	UNKNOWN은 review queue로만 이동
incomplete coverage를 negative evidence로 해석	P0	“뉴스 없음 = 리스크 없음” 오류	coverage gap ledger 필수
L3 output이 signal/ranking처럼 보임	P0	hard boundary 위반	naming을 review_state, evidence_edge, diagnostic으로 제한
stale row가 risk/support로 변환	P0	시간 신뢰성 오류	stale은 blocker/gap/context 처리
duplicate non-canonical row가 독립 edge 생성	P0	같은 뉴스 중복 증거화	canonical only active rule
calibrated probability 오용	P0	정적 confidence를 확률처럼 사용	calibrated_probability=None 강제
L4/L5/L6 coupling 발생	P1	bootstrap 범위 초과	output artifact까지만 생성
artifact path 불명확	P1	build 재현성 저하	config + input manifest hash
field name 불일치	P1	로컬 artifact마다 schema 차이	alias mapping + missing field blocker
forbidden vocabulary validator false positive	P2	보고서 금지어 설명까지 실패 가능	action/state field 중심 검사
경제 meaning rule table 과단순	P2	초반 의미 분류 품질 제한	unknown/context 처리 우선, 이후 확장
12. Final Codex patch prompt

아래를 그대로 Codex에게 전달하면 됩니다.

Markdown
# TASK-4149 L3 Diagnostic Strategy View Bootstrap

You are working on the local uncommitted repository state. Do not use GitHub as current state. The local repo has important uncommitted L0-L2 work and dirty/deleted L2/L3 files. Use local files only.

## Hard boundaries

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data = UNKNOWN/BLOCKER, never negative evidence
- L3 may produce diagnostic economic meaning and review-only relation states only.
- L3 must not produce BUY/SELL, ranking, sizing, order intent, paper eligibility, live eligibility, broker mutation, strategy acceptance, or deployment readiness.

## Goal

Implement a minimal safe Layer 3 bootstrap named:

`TASK-4149 L3 Diagnostic Strategy View Bootstrap`

L3 should consume current L2 diagnostic/read-view artifacts and produce review-only economic meaning, evidence edges, relation graph state, and blocker/gap ledgers.

L3 must not bypass L1/L2. L3 must not directly read L0 raw source rows. It may read `data/artifacts/l0_collection_status/current_status.json` only as coverage context.

## Important current state facts

- L0 public_newswire_backfill and public_market_macro_news_backfill are RUNNING with verified live PIDs.
- However, public newswire and public market/macro backfill coverage is still incomplete.
- Missing/incomplete coverage must be explicit coverage/blocker state, never negative evidence.
- Recent L2 is artifact/read-view oriented.
- Existing old L3 modules from Git HEAD expected canonical `src.l2.contracts.L2PrimitiveFact`.
- Many tracked `src/brain/l3/*` and `src/l2/*` files are currently deleted in the worktree.
- Do not blindly restore old L3 or L2 modules.
- Use a hybrid approach: create a task-scoped L3 bridge/package, while preserving old L3 architecture vocabulary such as `L3EconomicMeaningV2`, `L3EvidenceEdge`, and `L3RelationGraph` conceptually.

## Required implementation approach

Do not restore old `src/brain/l3` wholesale.

Create a new task-scoped package:

```text
src/brain/l3_diagnostic_strategy_view_bootstrap/
  __init__.py
  contracts.py
  l2_read_view_bridge.py
  coverage_policy.py
  economic_meaning_classifier.py
  evidence_edge_builder.py
  relation_graph_aggregator.py
  artifact_writer.py

Create scripts:

scripts/build_l3_diagnostic_strategy_view_4149.py
scripts/validate_l3_diagnostic_strategy_view_4149.py

Create tests:

tests/test_l3_diagnostic_strategy_view_bootstrap_4149.py

Create config:

configs/l3_diagnostic_strategy_view_bootstrap_4149.json

Create artifacts under:

data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/

Create report files under:

docs/reports/task_4149_l3_diagnostic_strategy_view_bootstrap/
  l3_diagnostic_strategy_view_bootstrap_report.md
  artifact_manifest.csv
  validation_output.txt
Input rules

The build script must read current local L2 diagnostic/read-view artifacts. Find the best current Task4146/Task4147 L2 artifact locally and configure it in configs/l3_diagnostic_strategy_view_bootstrap_4149.json.

Allowed inputs:

L2 diagnostic feature candidates / L2 read-view materialized rows

L1 packet state only for gate verification

data/artifacts/l0_collection_status/current_status.json only for coverage context

Forbidden inputs:

L0 raw article/news/newswire rows

collector raw tables

broker/order/paper/live tables

realized return, forward return, expected return, PnL tables

any direct L4/L5/L6 action/policy inputs

If required input columns are missing, do not infer. Emit explicit blocker/gap state.

Required L3 contract behavior

Implement review-only objects with fields equivalent to:

L3 input primitive

L3 economic meaning

L3 evidence edge

L3 relation graph

blocker/gap ledger rows

rejected/review queue rows

Allowed graph states only:

SUPPORT_DOMINANT_REVIEW
RISK_DOMINANT_REVIEW
MIXED_REVIEW
CONTEXT_ONLY
BLOCKED_CRITICAL
INSUFFICIENT_EVIDENCE

These are review states only, not trading signals.

Confidence rule:

high -> 0.85
medium -> 0.60
low -> 0.35
insufficient/unknown -> 0.00

calibrated_probability must remain None unless calibration status is CALIBRATED. For TASK-4149, do not implement calibration; keep it None.

Authority flags must remain false:

broker_mutation_allowed = false
live_order_allowed = false
paper_promotion_allowed = false
signal_export_allowed = false
trading_eligible = false
Required processing rules

L1 blocked packets must not become active L3 meanings.

UNKNOWN mapping must go to rejected/review queue, not active relation graph.

Duplicate non-canonical rows must not become independent L3 evidence candidates.

Stale rows must become blocker/gap/context, never negative evidence.

Incomplete backfill lanes must appear in coverage gap ledger.

Missing evidence must not become support/risk evidence.

L3 must not create sentiment score, alpha score, ranking, expected return, realized return, forward return, sizing, order intent, or action.

L3 may produce diagnostic economic dimensions, reason codes, evidence completeness, freshness component, source reliability component, contradiction flags, critical blockers, noncritical gaps, and review-only relation graph state.

Suggested economic dimensions

Use deterministic rule-based classification only. No LLM, no ML, no embedding pipeline.

Initial dimensions may include:

DEMAND
SUPPLY
PRICING
MARGIN
CAPEX
GUIDANCE
LIQUIDITY
RATES
INFLATION
FX
ENERGY
REGULATORY
GEOPOLITICAL
SUPPLY_CHAIN
CUSTOMER_ORDER
COMPETITION
EARNINGS_CONTEXT
SECTOR_CONTEXT
MACRO_CONTEXT
UNKNOWN

Unknown cases should become UNKNOWN, CONTEXT_ONLY, or INSUFFICIENT_EVIDENCE, not guessed support/risk.

Required output artifacts

Write at minimum:

data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/l3_input_manifest.json
data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/l3_meanings.jsonl
data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/l3_evidence_edges.jsonl
data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/l3_relation_graph.json
data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/l3_blocker_gap_ledger.csv
data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/l3_validator_report.json

Recommended additional artifacts:

data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/l3_review_summary.csv
data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap/l3_rejected_or_review_queue.csv
Validator requirements

python scripts/validate_l3_diagnostic_strategy_view_4149.py must check:

required artifacts exist

active L3 rows have L2 lineage

no active L3 row from L1 blocked input

no UNKNOWN mapping in active edges/graphs

no duplicate non-canonical row as independent active edge

stale/incomplete/missing rows are not converted into negative evidence

no forbidden action/signal/order/paper/live/broker authority

all authority flags remain false

calibrated_probability is None

graph states are from allowed enum only

coverage gap ledger exists and includes incomplete L0 coverage where applicable

row count reconciliation is present

L3 does not directly consume L0 raw source rows

Tests

Add unit tests with small fixtures covering:

L1 blocked row excluded from active L3 meanings

UNKNOWN mapping routed to review queue

duplicate non-canonical row suppressed

stale row becomes gap/blocker/context, not risk/support

incomplete L0 backfill creates coverage gap

calibrated_probability remains None

forbidden action vocabulary cannot appear in action/state fields

relation graph state uses allowed enum only

build output has row reconciliation

no dependency on src.l2.contracts.L2PrimitiveFact

Validation commands

Run and capture output:

Bash
python -m py_compile \
  src/brain/l3_diagnostic_strategy_view_bootstrap/*.py \
  scripts/build_l3_diagnostic_strategy_view_4149.py \
  scripts/validate_l3_diagnostic_strategy_view_4149.py

python -m unittest tests.test_l3_diagnostic_strategy_view_bootstrap_4149

python scripts/build_l3_diagnostic_strategy_view_4149.py \
  --config configs/l3_diagnostic_strategy_view_bootstrap_4149.json

python scripts/validate_l3_diagnostic_strategy_view_4149.py \
  --artifact-dir data/artifacts/task_4149_l3_diagnostic_strategy_view_bootstrap

If local L2 artifact paths are not discoverable, the build script may emit a BLOCKED_CRITICAL bootstrap report with zero active rows, but the blocker must be explicit and the validator must confirm no unsafe rows were created.

Report requirements

Create:

docs/reports/task_4149_l3_diagnostic_strategy_view_bootstrap/l3_diagnostic_strategy_view_bootstrap_report.md
docs/reports/task_4149_l3_diagnostic_strategy_view_bootstrap/artifact_manifest.csv
docs/reports/task_4149_l3_diagnostic_strategy_view_bootstrap/validation_output.txt

The report must include:

local-only basis

no GitHub reliance

L3 goal

input artifacts used

output artifacts generated

row counts

active/review/blocked counts

coverage gap counts

authority flags

validator result

known limitations

explicit statement that no signal, ranking, order, broker mutation, paper/live permission, strategy acceptance, or deployment readiness was opened

Scope cuts

Do not implement:

old L3 wholesale restore

old L2 wholesale restore

DB migrations

scheduler

graph database

L4 thesis bundle

L5 policy/action

L6 replay/paper/live/broker integration

alpha/sentiment/ranking score

realized/forward/expected returns

sizing/order intent

calibration

UI/frontend

End state should be a deterministic, review-only L3 diagnostic artifact pipeline that safely bridges current L2 outputs into economic meaning and relation graph review state.

Pro 확장
ChatGPT는 실수를 할 수 있습니다. 중요한 정보는 재차 확인하세요.