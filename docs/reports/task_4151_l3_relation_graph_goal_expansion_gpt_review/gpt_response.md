결론

27개는 “현재 구현 상태에서는 설명 가능한 숫자”입니다.
다만 최종 L3 relation graph로는 명백히 부족합니다.

현재 L0 원천 수집량은 큽니다. 예를 들어 public_context_news_backfill은 267,885 rows, public_market_macro_news_backfill은 113,492 rows, public_newswire_backfill도 19,562 rows가 있습니다. 

붙여넣은 마크다운(1)

그런데 L3가 실제로 받은 입력은 L3 input primitives 2,780개, relation graphs는 27개입니다. 

붙여넣은 마크다운(1)

즉 문제는 원천 데이터 부족이 아니라 아래 4가지입니다.

1) Graph key가 너무 coarse함

현재 graph key는 대략 다음 수준으로 보입니다.

target_node_type | target_node_key | economic_dimension | swing_1m

문서에도 현재 graph key가 너무 coarse하다고 명시되어 있습니다. 

붙여넣은 마크다운(1)

예시도 다음처럼 대부분 넓은 bucket 단위입니다.

MACRO|cftc_press_releases|CUSTOMER_ORDER|swing_1m
MACRO|cftc_press_releases|REGULATORY|swing_1m
MACRO|public_context_news_feeds|RATES|swing_1m

이 구조에서는 수천 개 evidence edge가 있어도 같은 bucket으로 합쳐집니다. 실제 예시에서도 한 graph key 안에 edge_count가 277개까지 들어갑니다. 

붙여넣은 마크다운(1)

따라서 27개라는 숫자는 “관계가 27개뿐”이라는 뜻이 아니라, 관계들을 27개의 큰 통으로만 집계하고 있다는 뜻에 가깝습니다.

2) Article-level L2 입력이 좁음

현재 L1 article packet artifact는 사실상 public_context_news_feeds 중심이고, source key distribution은 cftc_press_releases: 1093으로 제한되어 있습니다. L2 diagnostic feature도 public_context_news_feeds / cftc_press_releases / official_context_article_presence 중심입니다. 

붙여넣은 마크다운(1)

즉 현재 L3는 “전체 뉴스/매크로/뉴스와이어 세계”를 본 것이 아니라, CFTC press release 중심의 좁은 L2 feature universe를 주로 본 것입니다.

이 상태에서 graph count가 낮은 것은 이상하다기보다 bootstrap 구현의 자연스러운 결과입니다.

3) Newswire가 rich entity graph로 들어오지 못하고 있음

문서상 newswire는 L0 mapped rows 3,212개, mapping review queue 207개가 있지만, 아직 article-level L2 diagnostic feature로 넓게 materialize된 상태가 아닙니다. 

붙여넣은 마크다운(1)

현재 L3 meaning distribution에서도 public_newswire_feeds는 SOURCE_FAMILY / UNKNOWN / CONTEXT_ONLY 181개로 잡힙니다. 

붙여넣은 마크다운(1)

이건 중요한 신호입니다.

현재 newswire는 다음처럼 graph에 들어오고 있습니다.

source_family = public_newswire_feeds
target_node_type = SOURCE_FAMILY
economic_dimension = UNKNOWN
direction_review = CONTEXT_ONLY

이 구조에서는 뉴스와이어가 아무리 많아도 다음 관계를 만들 수 없습니다.

Company A ── announced customer order ── Company B
Company A ── guidance-related event ── Sector X
Company A ── regulatory/approval event ── Theme Y
Company A ── supply-chain relation ── Company B

즉 뉴스와이어가 graph 재료로 들어온 것이 아니라 “뉴스와이어라는 source family가 있다” 수준으로만 들어온 상태입니다.

4) Multi-axis relation graph가 아직 없음

현재 문서도 L3가 아직 다음 축들을 모델링하지 못한다고 정리합니다.

entity-event

entity-sector

macro-sector

macro-factor

source-event-cluster

time-window

contradiction

catalyst-chain

supply-chain/theme graph

붙여넣은 마크다운(1)

이 축들이 없으면 graph count는 낮을 수밖에 없습니다.

2. L3의 명확한 목표 정의
L3 목표

L3는 L1/L2를 통과한 증거를 바탕으로, 시장·기업·섹터·매크로·이벤트 사이의 경제적 관계를 진단용 graph로 구성하는 계층입니다.

더 실무적으로 말하면 L3는 아래 질문에 답해야 합니다.

이 기사/공시/매크로 뉴스는
어떤 기업, 섹터, 테마, 매크로 factor와 연결되는가?

그 연결은
리스크 검토 대상인가,
지원 검토 대상인가,
단순 context인가,
아니면 mapping/coverage가 부족해서 UNKNOWN/BLOCKER인가?

같은 사건을 여러 source가 같은 방향으로 말하는가,
아니면 source 간 충돌/모순이 있는가?

현재 L0-L2 coverage상
관계 판단이 가능한 영역과 불가능한 영역은 어디인가?
L3가 하지 말아야 할 것

L3는 아래 질문에는 답하지 않습니다.

이 종목을 사야 하는가?
팔아야 하는가?
상위 몇 위인가?
비중을 얼마나 둘 것인가?
paper/live로 넘겨도 되는가?
order intent를 만들 것인가?

이 경계는 문서상 하드 state와도 일치합니다. L3는 diagnostic economic meaning과 relation review state만 emit 가능하고, trading authority 계열 output은 금지되어 있습니다. 

붙여넣은 마크다운(1)

3. 무엇을 relation graph로 볼 것인가
Relation graph의 정의

L3에서 relation graph는 단순히 row count가 아닙니다.

Relation graph = 특정 경제적 관계 축을 기준으로, L1/L2 evidence edge들을 묶은 typed subgraph입니다.

즉 하나의 graph는 최소한 아래 요소를 가져야 합니다.

구성요소	의미
graph_family	어떤 종류의 관계 graph인가
target_scope	entity, symbol, sector, macro factor, source cluster 중 무엇을 중심으로 보는가
relation_lens	event, economic dimension, factor, theme, contradiction, coverage gap 중 어떤 렌즈인가
time_window	어느 기간의 evidence인가
horizon_label	swing_1m 등 검토 horizon
evidence_edges	L1/L2 lineage가 있는 증거 edge
graph_state	CONTEXT_ONLY, RISK_DOMINANT_REVIEW, SUPPORT_DOMINANT_REVIEW, MIXED_REVIEW, UNKNOWN/BLOCKER 등
coverage_state	충분/부족/blocked/stale/incomplete 여부
forbidden_output_check	BUY/SELL/ranking/sizing/order 등이 없는지

핵심은 관계 graph는 “경제적 해석 단위”이지 “데이터 row 묶음”이 아니라는 점입니다.

4. 추천 relation graph taxonomy

현재 L3는 economic_dimension + target_node + horizon 수준으로 묶여 있습니다. 다음 단계에서는 최소 6개 graph family가 필요합니다.

4.1 Entity-Event Graph
목적

기업/티커/기관/상품이 어떤 사건과 연결되는지 표현합니다.

예시
SYMBOL:A
 └─ EVENT_CLUSTER:customer_order_2026w26_xxx
      ├─ economic_dimension = CUSTOMER_ORDER
      ├─ direction_review = SUPPORT_REVIEW or RISK_REVIEW or CONTEXT_ONLY
      ├─ source_family = public_newswire_feeds
      └─ evidence_count = n
왜 필요한가

Newswire의 본질은 대부분 entity-event 관계입니다.

예를 들어 customer order, guidance, regulatory approval, partnership, financing, product launch 같은 이벤트는 source family 단위로 묶으면 의미가 사라집니다.

현재 newswire가 SOURCE_FAMILY / UNKNOWN으로 들어오는 문제를 해결하려면 이 graph가 P0입니다.

4.2 Entity-Economic Dimension Graph
목적

특정 기업/티커가 어떤 경제 dimension에 반복적으로 노출되는지 보여줍니다.

Dimension 예시
CUSTOMER_ORDER
GUIDANCE
REGULATORY
SUPPLY_CHAIN
CAPEX
DEMAND
MARGIN
FUNDING
LEGAL
MANAGEMENT
PRODUCT
예시 key
rg:v1:entity_dimension:SYMBOL:<ticker>:CUSTOMER_ORDER:2026-W26:swing_1m:mixed_public
주의

이 graph는 좋다/나쁘다를 결론내는 계층이 아닙니다.

허용되는 출력은 다음 정도입니다.

SUPPORT_REVIEW
RISK_REVIEW
MIXED_REVIEW
CONTEXT_ONLY
UNKNOWN/BLOCKER

금지되는 출력은 다음입니다.

BUY
SELL
TOP_PICK
RANK_1
POSITION_SIZE
ORDER_INTENT
4.3 Macro-Factor Graph
목적

macro news를 factor 단위로 정리합니다.

Factor 예시
RATES
INFLATION
GROWTH
EMPLOYMENT
OIL
FX
CREDIT
LIQUIDITY
POLICY
GEOPOLITICAL

현재 L3 meaning distribution에도 RATES, MACRO_CONTEXT가 이미 존재합니다. 

붙여넣은 마크다운(1)

하지만 지금은 이들이 너무 넓게 묶여 있습니다.

개선 방향
MACRO_FACTOR:RATES
 ├─ EVENT_CLUSTER:fed_speech_2026w26_xxx
 ├─ EVENT_CLUSTER:yields_move_2026w26_xxx
 ├─ EVENT_CLUSTER:inflation_expectation_2026w26_xxx
 └─ linked_sector_theme:duration_sensitive, banks, housing, semiconductors

단, 여기서도 “rates 때문에 이 종목 매수/매도”를 만들면 안 됩니다.

4.4 Macro-Sector / Macro-Theme Graph
목적

매크로 factor가 어떤 sector/theme과 연결되는지 표현합니다.

예시
RATES ── duration pressure context ── SOFTWARE
RATES ── funding cost context ── SMALL_CAP_GROWTH
OIL ── input cost context ── AIRLINES
FX ── translation context ── MULTINATIONAL_TECH
트레이더 관점에서 유용한 이유

실제 swing research에서는 단일 기사보다 macro factor가 어떤 sector/theme에 압력을 주는지가 중요합니다.

다만 이것은 “sector rotation signal”이 아니라 research context graph로만 유지해야 합니다.

4.5 Source-Event Cluster Graph
목적

같은 사건을 여러 source가 어떻게 다루는지 묶습니다.

예시
EVENT_CLUSTER:company_guidance_2026w26_xxx
 ├─ PRNewswire article
 ├─ GlobeNewswire article
 ├─ BusinessWire article
 ├─ official source article
 └─ public market/macro article
왜 필요한가

현재 L3는 evidence edge 2,780개가 있어도 relation graph 27개로만 뭉칩니다. 

붙여넣은 마크다운(1)

source-event cluster graph를 만들면 “같은 사건의 중복 기사”와 “실제로 다른 사건”을 구분할 수 있습니다.

이것이 없으면 graph count를 늘려도 noise가 늘어납니다.

4.6 Contradiction / Corroboration Graph
목적

같은 entity/event/factor에 대해 source 간 방향성이 충돌하는지 확인합니다.

예시
SYMBOL:A / GUIDANCE / 2026-W26
 ├─ source_1: SUPPORT_REVIEW
 ├─ source_2: CONTEXT_ONLY
 ├─ source_3: RISK_REVIEW
 └─ graph_state: MIXED_REVIEW

현재 graph state에도 MIXED_REVIEW가 5개 있습니다. 

붙여넣은 마크다운(1)

다만 지금은 MIXED가 왜 MIXED인지, 어떤 source/evidence가 충돌하는지 충분히 설명되지 않는 구조로 보입니다.

Contradiction graph는 L3의 질을 크게 올릴 수 있습니다.

4.7 Coverage Gap Graph
목적

관계가 없다고 말하는 것이 아니라, 관계 판단을 할 수 없는 이유를 명확히 남깁니다.

현재 L3 coverage gaps는 2개뿐입니다. 

붙여넣은 마크다운(1)

하지만 실제로는 다음 gap들이 더 구조화되어야 합니다.

NEWSWIRE_MAPPED_BUT_NO_ARTICLE_LEVEL_L2_FEATURE
MACRO_NEWS_BACKFILL_INCOMPLETE
SOURCE_FAMILY_COLLAPSED_TO_UNKNOWN
MAPPING_NOT_EVALUATED
SYMBOL_REQUIRED_BUT_MISSING
TIME_WINDOW_INCOMPLETE
STALE_SOURCE_TIME

문서상 missing/stale/incomplete data는 부정 증거가 아니라 UNKNOWN/BLOCKER로 처리해야 합니다. 

붙여넣은 마크다운(1)

Coverage gap graph는 이 원칙을 운영상 보장하는 장치입니다.

5. 구체 graph key / schema 제안
5.1 현재 key의 문제

현재 예시는 다음 형태입니다.

MACRO|cftc_press_releases|CUSTOMER_ORDER|swing_1m
MACRO|public_context_news_feeds|RATES|swing_1m

이 key는 다음 축을 잃습니다.

빠진 축	문제
실제 entity/ticker	어떤 기업 관계인지 모름
event cluster	같은 사건인지 다른 사건인지 모름
source provider	PRNewswire인지 GlobeNewswire인지 구분 어려움
macro factor	RATES 외 세부 factor 구조 약함
sector/theme	macro와 투자 universe 연결이 약함
time bucket	언제 발생한 관계인지 모호
contradiction basis	왜 MIXED인지 설명 약함
coverage state	data 없음과 관계 없음이 혼동될 수 있음
5.2 추천 graph key 구조

문자열 하나로 모든 것을 넣기보다, structured columns + stable hash key가 좋습니다.

Canonical key format
rg:v1:{graph_family}:{target_type}:{target_key}:{relation_lens}:{relation_key}:{time_bucket}:{horizon_label}:{source_scope}
예시
rg:v1:entity_event:SYMBOL:<ticker>:event_cluster:<cluster_key>:2026-W26:swing_1m:public_newswire_feeds
rg:v1:entity_dimension:SYMBOL:<ticker>:economic_dimension:CUSTOMER_ORDER:2026-W26:swing_1m:mixed_public
rg:v1:macro_factor:MACRO:RATES:event_domain:MACRO_CONTEXT:2026-W26:swing_1m:public_market_macro_news_feeds
rg:v1:macro_sector:SECTOR:semiconductors:macro_factor:RATES:2026-W26:swing_1m:mixed_public
rg:v1:source_event_cluster:EVENT_CLUSTER:<cluster_key>:source_family:public_newswire_feeds:2026-W26:swing_1m:provider_scope
rg:v1:coverage_gap:SOURCE_FAMILY:public_newswire_feeds:gap:NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2:2026-W26:swing_1m:diagnostic
5.3 Relation graph table schema
l3_relation_graphs.csv
Column	Type	Required	설명
graph_key	string	Y	canonical graph key
graph_key_hash	string	Y	stable hash
graph_family	enum	Y	entity_event, entity_dimension, macro_factor, macro_sector, source_event_cluster, contradiction, coverage_gap
graph_grain	enum	Y	entity, event_cluster, macro_factor, sector_theme, source_cluster, coverage
target_node_type	enum	Y	SYMBOL, ENTITY, MACRO, SECTOR, THEME, EVENT_CLUSTER, SOURCE_FAMILY
target_node_key	string	Y	canonical key
relation_lens	enum	Y	event_cluster, economic_dimension, macro_factor, sector_theme, contradiction, coverage_gap
relation_key	string	Y	dimension/factor/cluster/gap key
event_domain	enum/string	N	NEWSWIRE_DISCOVERY, MACRO_CONTEXT 등
economic_dimension	enum/string	N	CUSTOMER_ORDER, REGULATORY, RATES 등
macro_factor	enum/string	N	RATES, INFLATION, FX 등
sector_theme	string	N	sector/theme canonical key
source_scope	string	Y	source family/provider aggregation scope
time_bucket	string	Y	YYYY-MM-DD 또는 YYYY-WW
window_start	timestamp/date	Y	evidence window start
window_end	timestamp/date	Y	evidence window end
horizon_label	enum	Y	swing_1m 등
edge_count	int	Y	linked evidence edge count
evidence_count	int	Y	unique evidence count
source_family_count	int	Y	source diversity diagnostic
graph_state	enum	Y	CONTEXT_ONLY, RISK_DOMINANT_REVIEW, SUPPORT_DOMINANT_REVIEW, MIXED_REVIEW, UNKNOWN_BLOCKER
coverage_state	enum	Y	COMPLETE_ENOUGH, PARTIAL, BLOCKED, STALE, INCOMPLETE, UNKNOWN
blocked_reason	string	N	coverage gap reason
lineage_complete	bool	Y	every edge traceable to L1/L2
forbidden_output_present	bool	Y	must be false
created_at	timestamp	Y	artifact time
5.4 Evidence edge schema
l3_relation_edges.csv
Column	설명
edge_id	stable edge id
graph_key	parent graph
source_node_id	source node
target_node_id	target node
edge_type	evidence_to_event, event_to_entity, event_to_factor, factor_to_sector, source_to_event, contradiction_edge
source_artifact	L1/L2 artifact name
source_row_id	lineage id
source_family	public_context_news_feeds 등
source_provider	PRNewswire, CFTC 등 가능 시
mapping_status	L1 mapping status
admission_status	L2 admitted/review status
economic_dimension	dimension
direction_review	RISK_REVIEW, SUPPORT_REVIEW, CONTEXT_ONLY, UNKNOWN
evidence_time	source-time
time_bucket	bucket
dedupe_key	duplicate control
blocked_reason	if blocked
raw_l0_read	must be false
5.5 Event cluster schema
l3_event_clusters.csv
Column	설명
event_cluster_key	stable cluster key
cluster_basis	title_normalized/entity/time_bucket/source_family/dimension 등
event_domain	NEWSWIRE_DISCOVERY, MACRO_CONTEXT 등
economic_dimension	CUSTOMER_ORDER, GUIDANCE 등
primary_target_type	SYMBOL, ENTITY, MACRO, SECTOR 등
primary_target_key	canonical key
source_family_count	source diversity
evidence_count	unique evidence count
first_evidence_time	earliest evidence
last_evidence_time	latest evidence
cluster_state	CONTEXT_ONLY, RISK_REVIEW, SUPPORT_REVIEW, MIXED_REVIEW, UNKNOWN_BLOCKER
lineage_complete	L1/L2 traceability
blocked_reason	if applicable
6. L0-L2 artifact에서 L3 graph를 확장하는 방법
원칙

L3는 L0 raw를 직접 읽어서 graph를 만들면 안 됩니다.

문서에도 L3가 direct raw L0 reads를 피하는 것은 맞지만, 더 넓은 L1/L2 packetization이 필요하다고 되어 있습니다. 

붙여넣은 마크다운(1)

따라서 확장 순서는 다음이어야 합니다.

L0 raw/source
 → L1 packet / mapping / blocker
 → L2 diagnostic feature / admitted-review
 → L3 meaning / edge / graph
6.1 Public newswire 확장

현재 가장 높은 impact는 newswire입니다.

이유는 간단합니다.

Newswire는 mapped rows가 있음.

그런데 L3에서는 SOURCE_FAMILY / UNKNOWN으로 collapse되고 있음.

Newswire는 entity-event graph에 가장 적합한 source임.

문서상 newswire has mapped rows and mapping queue, but not yet broad article-level L2 diagnostic features라고 되어 있습니다. 

붙여넣은 마크다운(1)

구현 방향
public_newswire_feeds
 → L1 article packet
 → L2 diagnostic article feature
 → L3 event_cluster
 → L3 entity_event graph
 → L3 entity_dimension graph
P0로 뽑아야 하는 event dimensions
CUSTOMER_ORDER
GUIDANCE
REGULATORY
PARTNERSHIP
PRODUCT
FINANCING
MANAGEMENT
M&A
SUPPLY_CHAIN
LEGAL

단, dimension은 검토용 라벨이어야 하며 투자 점수로 쓰면 안 됩니다.

6.2 Public market/macro news 확장

현재 public_market_macro_news_feeds는 L2 candidate distribution에서 355개로 보입니다. 

붙여넣은 마크다운(1)

이 lane은 entity보다 macro-factor graph에 적합합니다.

구현 방향
public_market_macro_news_feeds
 → macro article packet
 → macro factor feature
 → macro_factor graph
 → macro_sector/theme graph
P0/P1 factor

P0:

RATES
INFLATION
GROWTH
POLICY
OIL
FX

P1:

CREDIT
LIQUIDITY
EMPLOYMENT
GEOPOLITICAL
VOLATILITY
6.3 Public context news 확장

현재 context news는 CFTC press releases에 강하게 치우쳐 있습니다. 

붙여넣은 마크다운(1)

이 lane은 regulatory, policy, official context graph에 적합합니다.

구현 방향
public_context_news_feeds
 → official/context article feature
 → regulatory/policy factor mapping
 → entity_dimension or macro_factor graph
주의

CFTC는 특정 상품/파생/규제 context가 강합니다.
따라서 모든 것을 equity entity graph로 억지 mapping하면 안 됩니다.

MACRO_CONTEXT_NO_SYMBOL_REQUIRED는 정상적인 상태일 수 있습니다. 실제 L1 mapping distribution에서도 이 값이 766개입니다. 

붙여넣은 마크다운(1)

6.4 Daily bars / five-minute bars 사용 여부
결론

지금 P0에서는 price bars를 L3 graph 생성에 넣지 않는 것이 맞습니다.

L0 상태상 daily bars는 거의 완료에 가깝고 five-minute bars는 16.0901% 진행 중입니다. 

붙여넣은 마크다운(1)

하지만 price bars를 L3에 너무 빨리 넣으면 다음 위험이 있습니다.

뉴스 이후 가격이 올랐다 → 좋은 뉴스
뉴스 이후 가격이 내렸다 → 나쁜 뉴스

이렇게 되면 L3가 사실상 signal/return 해석으로 넘어갑니다.

따라서 price bars는 P2에서만 제한적으로 허용하는 것이 맞습니다.

허용 가능한 형태:

price_context_available = true/false
bar_coverage_state = COMPLETE/PARTIAL/BLOCKED
event_time_alignment_state = VALID/UNKNOWN/BLOCKED

아직 금지해야 할 형태:

post_event_return
alpha
abnormal_return
price_reaction_score
entry_quality
BUY/SELL implication
7. P0 / P1 / P2 구현 로드맵
P0. Graph taxonomy와 newswire collapse 해결
목표

현재 27개 graph를 억지로 늘리는 것이 아니라, SOURCE_FAMILY / UNKNOWN으로 collapse되는 rows를 실제 relation graph 후보로 변환합니다.

구현 항목
1) relation_graph_taxonomy.py
GraphFamily enum
- ENTITY_EVENT
- ENTITY_DIMENSION
- MACRO_FACTOR
- MACRO_SECTOR
- SOURCE_EVENT_CLUSTER
- CONTRADICTION
- COVERAGE_GAP
GraphState enum
- CONTEXT_ONLY
- RISK_DOMINANT_REVIEW
- SUPPORT_DOMINANT_REVIEW
- MIXED_REVIEW
- UNKNOWN_BLOCKER
CoverageState enum
- COMPLETE_ENOUGH
- PARTIAL
- INCOMPLETE
- STALE
- BLOCKED
- UNKNOWN
2) relation_graph_keys.py

structured key builder 추가

old graph key와 backward compatibility 유지

graph_key_hash 생성

unknown target은 relation graph로 억지 생성하지 않고 coverage gap으로 분리

3) event_cluster_builder.py

같은 사건의 중복 기사 묶기

최소 cluster basis:

source_family
source_provider
normalized_title_or_event_text_hash
mapped_target_key
economic_dimension
time_bucket

title/text가 없으면 source row id 기반 fallback 가능

fallback은 반드시 cluster_basis = FALLBACK_LOW_CONFIDENCE로 표시

4) newswire_l3_adapter.py

public_newswire_feeds를 SOURCE_FAMILY / UNKNOWN에서 꺼내기

L1/L2에서 mapping된 symbol/entity가 있으면 ENTITY_EVENT graph 생성

mapping 불충분하면 COVERAGE_GAP으로 보냄

review queue row는 negative evidence로 처리 금지

5) coverage_gap_builder.py

최소 gap reason:

NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE
SOURCE_FAMILY_COLLAPSED_TO_UNKNOWN
MAPPING_NOT_EVALUATED
SYMBOL_REQUIRED_BUT_MISSING
MACRO_FACTOR_NOT_MAPPED
EVENT_CLUSTER_LOW_CONFIDENCE
SOURCE_TIME_MISSING_OR_STALE
6) Artifact outputs
data/artifacts/task_4152_l3_relation_graph_expansion/
  l3_relation_graphs.csv
  l3_relation_edges.csv
  l3_event_clusters.csv
  l3_relation_nodes.csv
  l3_coverage_gaps.csv
  l3_rejected_review_queue.csv
  l3_relation_graph_summary.json
  l3_relation_graph_validation.json
P0 성공 기준

P0 성공 기준은 “graph count 몇 개 이상”이 아닙니다.

성공 기준은 다음입니다.

1. public_newswire_feeds가 SOURCE_FAMILY / UNKNOWN으로만 collapse되지 않는다.
2. entity_event graph와 coverage_gap graph가 분리된다.
3. 모든 graph/edge가 L1/L2 lineage를 가진다.
4. forbidden output이 없다.
5. duplicate row 증가가 graph count 증가로 오인되지 않는다.
6. current 27 graph와 새 taxonomy graph의 reconciliation이 가능하다.
P1. Macro-factor / sector-theme / contradiction graph 추가
목표

L3를 “기사 bucket”에서 “경제 관계 지도”로 확장합니다.

구현 항목
1) Macro factor mapping
RATES
INFLATION
GROWTH
POLICY
OIL
FX
CREDIT
LIQUIDITY
EMPLOYMENT
GEOPOLITICAL
2) Sector/theme bridge

초기에는 hard-coded dictionary로 충분합니다.

예시:

RATES → banks, housing, software, small_cap_growth
OIL → energy, airlines, chemicals, transportation
FX → multinational_tech, exporters, importers
POLICY → defense, healthcare, financials, energy

주의: 이것은 signal이 아니라 relation context입니다.

3) Contradiction/corroboration graph

같은 target/dimension/window에서 direction_review가 섞이면:

MIXED_REVIEW

단, source가 하나뿐이면 contradiction graph를 만들지 않습니다.

4) Source diversity diagnostics
source_family_count
source_provider_count
unique_evidence_count
duplicate_evidence_count

이 값은 graph quality 진단용이지 score/rank가 아닙니다.

P2. Price context / calibration artifact
목표

L3 graph에 가격 정보를 직접 결론으로 넣지 않고, coverage와 time alignment 확인용 context로만 붙입니다.

허용
daily_bar_coverage_state
five_min_bar_coverage_state
event_time_alignment_state
price_context_available
금지
post_event_return
abnormal_return
price_reaction_score
alpha
rank
entry_score
buy/sell implication

P2에서도 validator가 leakage와 forbidden output을 막아야 합니다.

8. Validator checklist
8.1 Hard boundary validator

다음 column/value가 artifact 어디에도 있으면 FAIL.

BUY
SELL
HOLD as action
REDUCE
EXIT
RERISK
ORDER
ORDER_INTENT
POSITION_SIZE
SIZING
RANK
TOP_PICK
PAPER_ELIGIBLE
LIVE_ELIGIBLE
BROKER_MUTATION
STRATEGY_ACCEPTED
DEPLOYMENT_READY

주의: HOLD라는 단어도 action 의미라면 금지입니다.
L3 graph_state에는 쓰지 않는 편이 안전합니다.

8.2 No direct L0 bypass validator

모든 l3_relation_edges는 다음 중 하나를 가져야 합니다.

source_artifact = L1 packet artifact
source_artifact = L2 diagnostic feature artifact
source_artifact = prior L3 primitive/meaning artifact with L1/L2 lineage

다음은 FAIL입니다.

source_artifact = raw L0 table
raw_l0_read = true
missing lineage
8.3 Lineage completeness validator

각 graph에 대해:

edge_count >= 1
evidence_count >= 1
all edges have source_row_id
all edges have source_artifact
all edges have mapping/admission state

Coverage gap graph는 예외적으로 evidence edge가 아니라 blocker lineage를 가져도 됩니다.

8.4 Graph key uniqueness validator

FAIL 조건:

same graph_key + same evidence_id duplicated
same event_cluster_key generated from identical fallback without dedupe
target_node_key null but graph_family != COVERAGE_GAP
relation_key UNKNOWN but graph_family != COVERAGE_GAP
8.5 Unknown collapse validator

현재 핵심 문제를 막는 validator입니다.

WARN 또는 FAIL 기준:

public_newswire_feeds rows collapse into SOURCE_FAMILY / UNKNOWN above threshold
mapped newswire rows not represented in ENTITY_EVENT or COVERAGE_GAP
NEWSWIRE_MAPPED_BY_L0_COLLECTOR rows missing from L3 expansion audit

정확한 threshold는 초기에 hard fail보다 audit warning이 낫습니다.
다만 P0 이후에는 “mapped newswire가 전부 SOURCE_FAMILY/UNKNOWN으로만 남는 상태”는 FAIL 처리해야 합니다.

8.6 Coverage semantics validator

다음 원칙을 강제합니다.

missing/stale/incomplete ≠ negative evidence
blocked mapping ≠ risk evidence
no source ≠ no relation
no graph ≠ no economic event

문서상 missing/stale/incomplete data는 UNKNOWN/BLOCKER이지 negative evidence가 아닙니다. 

붙여넣은 마크다운(1)

8.7 Direction review enum validator

허용:

RISK_REVIEW
SUPPORT_REVIEW
CONTEXT_ONLY
MIXED_REVIEW
UNKNOWN_BLOCKER

금지:

BULLISH
BEARISH
LONG
SHORT
BUY
SELL
OUTPERFORM
UNDERPERFORM

bullish/bearish도 trading signal로 오해될 수 있으므로 L3에서는 피하는 것이 좋습니다.

8.8 Price leakage validator

Price bars를 P2에서 붙일 경우:

FAIL 조건:

future bar joined into event-time graph
post-event return calculated
abnormal return calculated
price reaction direction emitted
price context used to set SUPPORT/RISK

허용:

bar coverage state
event-time alignment state
bar availability
8.9 Reconciliation validator

기존 bootstrap과 새 taxonomy 간 reconciliation 필요.

old_l3_input_primitives
old_l3_meanings
old_l3_edges
old_l3_relation_graphs

new_l3_event_clusters
new_l3_relation_edges
new_l3_relation_graphs
new_l3_coverage_gaps

다만 기존처럼 primitives = meanings = edges = 1:1일 필요는 없습니다.

새 구조에서는 하나의 evidence가 여러 typed edge를 만들 수 있습니다.

예:

article evidence
 → source_to_event edge
 → event_to_entity edge
 → event_to_dimension edge
 → event_to_macro_factor edge

따라서 validator는 row equality가 아니라 lineage completeness와 dedupe correctness를 봐야 합니다.

9. 지금 만들지 말아야 할 것
9.1 Trading signal 계열

금지:

BUY/SELL
ranking
score
sizing
order intent
paper/live eligibility
broker path
strategy acceptance
deployment readiness

문서상 이 경계는 명확합니다. 

붙여넣은 마크다운(1)

9.2 Graph count 늘리기용 raw L0 direct read

현재 L0 raw item rows는 400,939로 크지만, L3가 이를 직접 읽어서 graph를 늘리면 L1/L2 gate를 우회하게 됩니다. L1/L2 상태에서도 ready/admitted row와 blocked row가 분리되어 있습니다. 

붙여넣은 마크다운(1)

따라서 L3의 graph count 증가 경로는 반드시:

L1 packet 확장
L2 diagnostic feature 확장
L3 graph expansion

이어야 합니다.

9.3 Neo4j / vector KG / 대형 graph DB

지금은 과합니다.

현재 필요한 것은 graph database가 아니라:

stable schema
typed graph family
lineage
dedupe
coverage gap
validator

입니다.

CSV/JSON artifact로 충분합니다.

9.4 Price reaction model

아직 금지하는 편이 맞습니다.

이유:

1. five-minute bars coverage가 아직 낮음
2. news source-time alignment 검증이 먼저 필요
3. return/price reaction을 붙이면 L3가 signal처럼 작동할 위험이 있음
9.5 ML 기반 event classifier

초기에는 rule-based taxonomy로 충분합니다.

지금 필요한 것은 모델 성능이 아니라 관계 schema의 정확성입니다.

10. 최종 판단
10.1 27개는 너무 낮은가?

현재 구현 조건에서는 예상 가능한 숫자입니다.

이유:

1. L3 input 자체가 2,780 primitives로 제한됨.
2. Article-level L2 feature가 CFTC/public_context 쪽에 치우침.
3. Newswire가 entity/event graph가 아니라 SOURCE_FAMILY/UNKNOWN으로 collapse됨.
4. Graph key가 coarse해서 많은 edge가 적은 graph로 합쳐짐.

문서도 현재 27개가 graph key coarse, L2 input narrow, newswire UNKNOWN collapse, multi-axis graph 부재 때문이라고 정리합니다. 

붙여넣은 마크다운(1)

10.2 최우선 개선은?

P0는 newswire entity-event graph + structured graph taxonomy + coverage gap graph입니다.

이유:

뉴스와이어는 기업 이벤트 관계를 만들기에 가장 좋은 source인데,
현재 L3에서는 SOURCE_FAMILY/UNKNOWN으로 손실되고 있기 때문입니다.
10.3 price bars는 지금 넣어야 하나?

아니요. P0에서는 넣지 않는 것이 맞습니다.

P2에서 coverage/time-alignment context로만 붙이고, return/price reaction/alpha로 해석하면 안 됩니다.

11. Codex에게 줄 최종 patch prompt

아래를 그대로 Codex 작업명세로 사용하면 됩니다.

Markdown
# TASK-4152 L3 Relation Graph Taxonomy Expansion

You are working on the local, uncommitted trading-system repository state.

Do not rely on GitHub as current state. Recent L0-L3 work is local and uncommitted.

## Hard State

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence
- L3 may emit diagnostic economic meaning and relation review state only
- L3 must not emit BUY/SELL, ranking, sizing, order intent, paper/live eligibility, broker mutation, strategy acceptance, or deployment readiness

## Background

Current TASK-4150 L3 bootstrap produced:

- L3 input primitives: 2780
- L3 meanings: 2780
- L3 evidence edges: 2780
- L3 relation graphs: 27
- L3 coverage gaps: 2
- validator: PASS

The graph count is low because current graph keys are too coarse and current L2 article-level input is too narrow. Newswire rows are currently collapsing into SOURCE_FAMILY / UNKNOWN / CONTEXT_ONLY instead of becoming entity-event or coverage-gap graphs.

Do not increase graph count by reading raw L0 directly or duplicating rows. Increase graph coverage only through gated L1/L2 artifacts and complete lineage.

## Objective

Implement the next L3 relation graph expansion so that L3 becomes a diagnostic economic relation map, not a trading signal engine.

The implementation must:

1. Add a structured L3 relation graph taxonomy.
2. Add stable graph key generation.
3. Add event cluster construction.
4. Convert mapped newswire evidence into entity-event and entity-dimension graphs when L1/L2 lineage allows it.
5. Route unknown/incomplete/missing/stale cases into explicit coverage-gap graphs.
6. Preserve all hard trading boundaries.
7. Add validators proving that graph count increases because meaningful relationship coverage improved, not because duplicate/noisy rows were counted.

## Required Graph Families

Implement these graph families as enums or equivalent constants:

- ENTITY_EVENT
- ENTITY_DIMENSION
- MACRO_FACTOR
- MACRO_SECTOR
- SOURCE_EVENT_CLUSTER
- CONTRADICTION
- COVERAGE_GAP

## Required Graph States

Allowed graph states:

- CONTEXT_ONLY
- RISK_DOMINANT_REVIEW
- SUPPORT_DOMINANT_REVIEW
- MIXED_REVIEW
- UNKNOWN_BLOCKER

Do not use BUY, SELL, bullish, bearish, long, short, rank, score, sizing, or order language.

## Required Coverage States

Allowed coverage states:

- COMPLETE_ENOUGH
- PARTIAL
- INCOMPLETE
- STALE
- BLOCKED
- UNKNOWN

Missing/stale/incomplete must never be interpreted as negative evidence.

## Recommended Files

Add or update files similar to the following, adapting to the existing repo structure:

- src/brain/l3/relation_graph_taxonomy.py
- src/brain/l3/relation_graph_keys.py
- src/brain/l3/event_cluster_builder.py
- src/brain/l3/relation_edge_builder.py
- src/brain/l3/coverage_gap_builder.py
- src/brain/l3/newswire_l3_adapter.py
- scripts/run_l3_relation_graph_expansion.py
- scripts/validate_l3_relation_graphs.py
- tests/test_l3_relation_graph_taxonomy_expansion.py

Avoid overengineering. Do not add a graph database, embeddings, ML classifiers, price reaction models, order logic, broker logic, or paper/live pathways.

## Graph Key Format

Use structured columns plus a stable canonical key.

Canonical graph key format:

rg:v1:{graph_family}:{target_type}:{target_key}:{relation_lens}:{relation_key}:{time_bucket}:{horizon_label}:{source_scope}

Examples:

- rg:v1:entity_event:SYMBOL:<ticker>:event_cluster:<cluster_key>:2026-W26:swing_1m:public_newswire_feeds
- rg:v1:entity_dimension:SYMBOL:<ticker>:economic_dimension:CUSTOMER_ORDER:2026-W26:swing_1m:mixed_public
- rg:v1:macro_factor:MACRO:RATES:event_domain:MACRO_CONTEXT:2026-W26:swing_1m:public_market_macro_news_feeds
- rg:v1:macro_sector:SECTOR:semiconductors:macro_factor:RATES:2026-W26:swing_1m:mixed_public
- rg:v1:coverage_gap:SOURCE_FAMILY:public_newswire_feeds:gap:NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2:2026-W26:swing_1m:diagnostic

If target_node_key or relation_key is UNKNOWN, do not create a normal relation graph. Route it to COVERAGE_GAP unless there is a valid diagnostic reason to keep it as context-only with complete lineage.

## Required Output Artifacts

Create artifacts under a task-specific directory, for example:

data/artifacts/task_4152_l3_relation_graph_expansion/

Required outputs:

- l3_relation_graphs.csv
- l3_relation_edges.csv
- l3_event_clusters.csv
- l3_relation_nodes.csv
- l3_coverage_gaps.csv
- l3_rejected_review_queue.csv
- l3_relation_graph_summary.json
- l3_relation_graph_validation.json

Also add a short report:

docs/reports/task_4152_l3_relation_graph_expansion/l3_relation_graph_expansion_report.md

## l3_relation_graphs.csv Required Columns

- graph_key
- graph_key_hash
- graph_family
- graph_grain
- target_node_type
- target_node_key
- relation_lens
- relation_key
- event_domain
- economic_dimension
- macro_factor
- sector_theme
- source_scope
- time_bucket
- window_start
- window_end
- horizon_label
- edge_count
- evidence_count
- source_family_count
- graph_state
- coverage_state
- blocked_reason
- lineage_complete
- forbidden_output_present
- created_at

## l3_relation_edges.csv Required Columns

- edge_id
- graph_key
- source_node_id
- target_node_id
- edge_type
- source_artifact
- source_row_id
- source_family
- source_provider
- mapping_status
- admission_status
- economic_dimension
- direction_review
- evidence_time
- time_bucket
- dedupe_key
- blocked_reason
- raw_l0_read

raw_l0_read must always be false.

## l3_event_clusters.csv Required Columns

- event_cluster_key
- cluster_basis
- event_domain
- economic_dimension
- primary_target_type
- primary_target_key
- source_family_count
- evidence_count
- first_evidence_time
- last_evidence_time
- cluster_state
- lineage_complete
- blocked_reason

## Coverage Gap Reasons

Implement at least these reason codes:

- NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE
- SOURCE_FAMILY_COLLAPSED_TO_UNKNOWN
- MAPPING_NOT_EVALUATED
- SYMBOL_REQUIRED_BUT_MISSING
- MACRO_FACTOR_NOT_MAPPED
- EVENT_CLUSTER_LOW_CONFIDENCE
- SOURCE_TIME_MISSING_OR_STALE
- L1_BLOCKED
- L2_NOT_ADMITTED

## Data Use Rules

Allowed inputs:

- Existing L1 packet artifacts
- Existing L2 diagnostic feature artifacts
- Existing L3 primitive/meaning artifacts if they retain L1/L2 lineage

Forbidden inputs:

- Direct raw L0 reads for the purpose of creating L3 graphs
- Broker/order/paper/live files
- Strategy acceptance/deployment readiness files as permissions

## Price Bars

Do not use daily bars or five-minute bars to calculate returns, price reaction, abnormal return, alpha, entry score, or direction.

For this task, price bars should not be required. If any price context is added, it must be limited to coverage/time-alignment fields only:

- price_context_available
- bar_coverage_state
- event_time_alignment_state

No post-event return or reaction direction is allowed.

## Validators

Add or update validators to check:

1. No forbidden trading outputs:
   - BUY
   - SELL
   - RANK
   - SCORE as trading score
   - SIZING
   - ORDER
   - ORDER_INTENT
   - PAPER_ELIGIBLE
   - LIVE_ELIGIBLE
   - BROKER_MUTATION
   - STRATEGY_ACCEPTED
   - DEPLOYMENT_READY

2. No direct L0 bypass:
   - every edge must have source_artifact and source_row_id from L1/L2 lineage
   - raw_l0_read must be false

3. Graph key uniqueness:
   - no duplicate graph_key + evidence_id
   - no normal relation graph with UNKNOWN target/relation key unless explicitly context-only and lineaged
   - coverage gaps must be separated from relation graphs

4. Newswire collapse audit:
   - mapped public_newswire_feeds rows should not remain only SOURCE_FAMILY / UNKNOWN
   - mapped rows must become ENTITY_EVENT, ENTITY_DIMENSION, or COVERAGE_GAP

5. Coverage semantics:
   - missing/stale/incomplete must become UNKNOWN/BLOCKER or coverage gap
   - missing data must never become risk/support/negative evidence

6. Direction review enum:
   - allowed only:
     - RISK_REVIEW
     - SUPPORT_REVIEW
     - CONTEXT_ONLY
     - MIXED_REVIEW
     - UNKNOWN_BLOCKER

7. Reconciliation:
   - report old TASK-4150 graph count and new graph count
   - explain count changes by graph_family
   - verify count increase is not duplicate-driven

8. Validator output:
   - write l3_relation_graph_validation.json
   - script must exit non-zero on hard failures

## Tests

Add unit tests covering:

- graph key stability
- graph taxonomy enum validity
- unknown target routing to coverage gap
- newswire mapped row does not collapse to SOURCE_FAMILY / UNKNOWN
- forbidden output detection
- no direct L0 read
- duplicate evidence does not inflate graph count
- missing/stale/incomplete treated as UNKNOWN/BLOCKER
- price return/reaction fields are absent

## Expected Report Content

The report should include:

1. Previous TASK-4150 baseline:
   - primitives
   - meanings
   - edges
   - relation graphs
   - coverage gaps

2. New output summary:
   - relation graphs by graph_family
   - relation graphs by graph_state
   - coverage gaps by reason
   - rejected/review queue count
   - newswire collapse audit
   - lineage completeness result
   - forbidden output result

3. Interpretation:
   - graph count increased/decreased because of real relation coverage changes
   - not because of duplicate rows
   - no trading authority opened

## Acceptance Criteria

The task is complete only if:

- validator passes
- tests pass
- all output artifacts are created
- every graph/edge has L1/L2 lineage
- no forbidden trading output exists
- newswire SOURCE_FAMILY/UNKNOWN collapse is reduced or explicitly converted into coverage gaps
- report clearly explains why graph count changed
- no broker/order/paper/live/strategy/deployment permission is opened

Do not claim strategy acceptance, deployment readiness, paper readiness, live readiness, or real capital readiness.
출처

Pro 확장
ChatGPT는 실수를 할 수 있습니다. 중요한 정보는 재차 확인하세요.