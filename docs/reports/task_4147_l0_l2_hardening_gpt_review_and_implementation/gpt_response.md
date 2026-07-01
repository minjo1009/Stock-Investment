<!-- assistant_message_0 -->
제공된 로컬 TASK-4146 상태만 기준으로, 배치 단위 진단을 row/article 단위 L1/L2 파이프라인으로 확장하는 순서를 잡겠습니다. L2 feature는 실제 스키마에 올리되 signal/order/broker 권한은 계속 닫는 전제로 보겠습니다.

---

<!-- assistant_message_1 -->
핵심 세 줄 요약

현재 숫자상 L0 raw item 380,101건 대비 L1/L2 packet 1,754건이라서, L1/L2가 아직 “기사/row 단위”가 아니라 “batch 단위”로 움직인다는 판단은 맞습니다.

TASK-4147의 본질은 L0 raw item → L1 row/article packet → L2 diagnostic feature schema로 이어지는 lineage를 실제로 만드는 것입니다.

다만 이것은 어디까지나 진단용 feature pipeline입니다. signal, ranking, order, broker, paper promotion은 계속 닫혀 있어야 합니다.

1. 총평

사장님, TASK-4147은 기능을 많이 늘리는 작업이 아니라, 지금 TASK-4146에서 만든 wide handoff를 올바른 단위로 정규화하는 작업으로 봐야 합니다.

현재 제공된 수치가 핵심 근거입니다.

항목	현재
L0 batch rows	1,754
L0 raw item rows reported	380,101
L1 packet rows	1,754
L2 rows	1,754
Feature candidate count	366,781

즉, L1/L2 row 수가 L0 batch row와 같고, raw item 수와는 크게 다릅니다. 그래서 현재 구조는 raw 기사 1건 = L1 packet 1건이 아니라, batch 1건 = L1 packet 1건에 가깝습니다.

따라서 우선순위는 명확합니다.

먼저 L1을 article/row 단위 packet으로 바꾸고, 그 다음 L2 feature를 실제 schema에 materialize해야 합니다.
반대로, L1 batch 구조를 그대로 둔 채 feature schema만 먼저 밀어 넣으면 잘못된 계약을 고착시킬 가능성이 큽니다.

2. 실무 구현 순서
권장 순서
순서	작업	목적	비고
0	TASK-4147 contract 고정	이번 작업의 범위, 금지선, 산출물 정의	signal/order/broker 금지선 명시
1	L0 raw item manifest 만들기	batch 안의 기사/row를 1건 단위로 식별	L1 row-level의 전제
2	L1 row/article-level packet 확장	raw item 1건마다 L1 packet 생성	READY/BLOCKED 모두 packet화
3	L2가 L1 packet만 소비하도록 전환	L2의 L0 직접 참조 차단	L1 gate 우회 방지
4	L2 diagnostic feature를 실제 feature schema에 적재	feature candidate를 durable row로 승격	단, trading-ineligible
5	newswire ticker/entity mapping 개선	feature 품질 개선	L1 hard gate로 만들면 안 됨
6	L0 real-time operating config 분리	L0 수집만 안전하게 켜는 설정	trading 권한과 분리
7	durable 15분 L1/L2 loop 등록	운영 지속성 확보	validator 통과 후 등록
8	backfill completion proof 작성	완료율/공백/UNKNOWN 증거화	“완료”의 정의를 과장하면 안 됨
3. 각 항목별 구현 방향
1) L1을 batch-level에서 row/article-level로 확장
해야 할 일

현재 L1 packet이 batch 기준이면, 다음 구조로 바꿔야 합니다.

L0 batch
  └─ raw item / article 1
       └─ L1 packet 1
  └─ raw item / article 2
       └─ L1 packet 2
  └─ raw item / article N
       └─ L1 packet N

L1 packet의 최소 필드는 아래 정도면 충분합니다.

필드	목적
l1_packet_id	L1 packet 고유 ID
source_lane	public_newswire, macro, context 등
l0_batch_id	원 batch 추적
l0_raw_item_id 또는 raw_item_hash	기사/row 단위 원천 식별자
source_time_utc	source-time audit용
collected_at_utc	수집 시각
title 또는 content_ref	원문/요약 참조
url 또는 source_ref	원천 추적
l1_status	READY / BLOCKED / UNKNOWN
blocker_code	source_time_missing, duplicate, parse_error 등
lineage_hash	재실행 idempotency 확인
중요한 판단

L1은 좋은 기사만 통과시키는 scoring layer가 아닙니다.
L1은 데이터 입구 검문소입니다.

따라서 L1에서 해야 할 판단은 이 정도입니다.

판단	L1에서 가능
source time이 있는가	가능
중복인가	가능
최소 식별자가 있는가	가능
원문/참조가 깨졌는가	가능
ticker가 확실한가	보조 enrichment
투자에 좋은 뉴스인가	금지
매수/매도 신호인가	금지
2) newswire ticker/entity mapping 개선
구현 방향

newswire는 ticker/entity mapping 품질이 중요하지만, 이걸 너무 무겁게 만들 필요는 없습니다.

우선순위는 아래 순서가 좋습니다.

우선순위	mapping 근거	신뢰도
1	source metadata에 ticker/entity가 명시됨	높음
2	issuer/company metadata, CIK, exchange 정보	높음
3	내부 company master의 exact alias match	중간~높음
4	title/body의 정확한 회사명 match	중간
5	fuzzy match	낮음, audit 대상
6	애매한 약어/일반명	UNKNOWN 처리
피해야 할 것

가장 위험한 것은 제목에 나온 단어만 보고 강제로 ticker를 붙이는 것입니다.

예를 들어 “Apple”, “Meta”, “Oracle”, “Target” 같은 단어는 일반명/회사명이 겹칠 수 있습니다. 이런 경우 무리하게 mapping하면 false positive가 생기고, 나중에 feature schema에 잘못된 row가 쌓입니다.

권장 상태값
상태	의미
MAPPED_HIGH_CONFIDENCE	명시적 ticker/CIK/source metadata 기반
MAPPED_MEDIUM_CONFIDENCE	exact company alias 기반
AMBIGUOUS	복수 후보
UNMAPPED	mapping 불가
NOT_APPLICABLE	macro/context 기사라 ticker가 필요 없는 경우

중요한 점은, UNMAPPED를 L1 BLOCKER로 과도하게 처리하면 안 됩니다.
특히 macro/context 뉴스는 애초에 ticker가 없는 것이 정상일 수 있습니다.

3) L0 real-time collection operating config 분리
목표

이 작업의 목적은 L0 수집을 안전하게 켤 수 있는 운영 설정을 분리하는 것입니다.

이 설정은 trading 권한과 완전히 별개여야 합니다.

권장 config 항목

예시는 이런 구조가 적당합니다.

YAML
mode: diagnostic_collection_only

l0_realtime:
  enabled: true
  allowed_lanes:
    - public_newswire_feeds
    - public_market_macro_news_feeds
    - public_context_news_feeds
  interval_seconds: 900
  max_concurrent_collectors: 2
  rate_limit_enabled: true

authority:
  trading_enabled: false
  signal_enabled: false
  order_enabled: false
  broker_mutation_enabled: false
  paper_promotion_enabled: false

stale_data_policy:
  missing_or_stale_is: UNKNOWN_BLOCKER
핵심 원칙

L0 real-time collection을 켠다는 것은 뉴스 수집을 켠다는 뜻입니다.
그것이 L2 signal, paper trading, broker, order 권한을 여는 의미가 되어서는 안 됩니다.

4) durable 15-minute L1/L2 loop 등록
결론

L1/L2 loop는 하나의 durable wrapper로 묶는 것이 좋습니다.

다만 L0 backfill loop와는 분리해야 합니다.

권장 구조는 아래입니다.

L0 collectors / backfill
  - 별도 실행
  - source별 장기 수집
  - 실패/재시작 독립 관리

15분 L1/L2 diagnostic loop
  1. 새 L0 raw item manifest 확인
  2. L1 row/article packet 생성
  3. L1 validator 실행
  4. L2 diagnostic feature materialization
  5. authority-zero validator 실행
  6. heartbeat/status 기록
Windows Task Scheduler vs existing scheduler

둘 다 실제 실행자가 되면 안 됩니다.
실행자는 하나만 있어야 합니다.

권장 방식은 둘 중 하나입니다.

방식	추천도	설명
기존 scheduler가 이미 registry/status를 관리	높음	기존 운영 체계와 연결
Windows Task Scheduler가 PowerShell wrapper 실행	가능	단순하고 안정적
둘 다 독립적으로 15분 실행	금지	중복 실행, race condition 위험

가장 현실적인 방식은:

Windows Task Scheduler는 wrapper를 깨우는 host 역할만 하고, 실제 loop 상태/heartbeat/source of truth는 기존 scheduler registry 또는 TASK-4147 status artifact가 관리한다.

5) backfill completion을 계속 올리고 proof 생산
중요한 전제

public source backfill에서 “완료”라는 말을 과장하면 안 됩니다.

완료의 의미는 다음처럼 정의해야 합니다.

“해당 source/lane/date window/request cursor 기준으로 수집 가능한 범위를 시도했고, 성공/실패/UNKNOWN/BLOCKER를 증거로 남겼다.”

즉, “인터넷 전체 뉴스를 완전 수집했다”가 아닙니다.

completion proof에 필요한 항목
항목	설명
source_lane	newswire, macro, context
window_start_utc	대상 기간 시작
window_end_utc	대상 기간 종료
attempted_pages_or_chunks	시도한 page/chunk
successful_pages_or_chunks	성공한 page/chunk
raw_items_collected	수집 raw item 수
l1_packets_created	L1 packet 수
l1_ready	READY 수
l1_blocked	BLOCKED 수
unknown_or_gap_count	UNKNOWN/gap 수
blocker_reason_rollup	blocker 사유
last_success_at_utc	마지막 성공 시각
현재 상태에서 특히 봐야 할 부분

제공된 rollup에서 public_newswire_feeds는 다음 구조입니다.

항목	public_newswire_feeds
L0 batch rows	189
L0 raw item rows reported	15,970
L1 ready rows	166
feature candidate count	2,650

다른 source는 feature candidate count가 raw item count와 유사한데, newswire는 차이가 큽니다.
이것이 오류라고 단정하면 안 되지만, TASK-4147에서 반드시 설명되어야 합니다.

가능한 원인은 다음입니다.

가능성	해석
batch-level feature 후보만 일부 생성	현재 구조 한계
ticker/entity mapped item만 feature화	mapping coverage 문제
newswire raw item dedup/filter 적용	정상일 수도 있음
source별 feature 생성 규칙 차이	문서화 필요

따라서 TASK-4147 proof에는 source별 raw item → L1 packet → L2 feature row 전환율이 반드시 들어가야 합니다.

6) L2 diagnostic feature candidates를 실제 feature schema로 승격
핵심 결론

이 작업은 해야 합니다.
다만 표현을 정확히 해야 합니다.

“L2 feature를 trading feature로 승격”이 아니라,
“L2 diagnostic feature candidate를 durable diagnostic feature schema row로 materialize” 하는 것입니다.

권장 schema 개념

기존 feature schema가 있다면 그 안에 diagnostic namespace를 두고, 없다면 최소한 아래 같은 형태가 필요합니다.

필드	목적
feature_row_id	feature row 고유 ID
feature_namespace	예: l2_diagnostic_news
feature_family	article_seen, entity_mention, source_metadata 등
feature_name	구체 feature 이름
feature_value	값
value_type	string, numeric, bool, json
l1_packet_id	반드시 존재
l0_raw_item_id	원천 추적
source_lane	source 구분
source_time_utc	source-time 기준
asof_utc	feature 관측 기준
entity_id / ticker	nullable
mapping_confidence	nullable
diagnostic_only	true
trading_eligible	false
run_id	실행 추적
created_at_utc	생성 시각
feature family는 보수적으로 시작

처음부터 alpha-like feature를 만들면 위험합니다.

초기에는 아래 정도가 적절합니다.

feature family	허용 여부	설명
article_seen	허용	기사 존재 증거
source_category	허용	newswire/macro/context 등
source_time_quality	허용	source time 품질
entity_mention	허용	ticker/entity mention
mapping_confidence	허용	mapping 신뢰도
dedup_cluster_id	허용	중복 묶음
event_label_raw	제한적 허용	source가 제공한 이벤트 태그 중심
sentiment_score	보류 권장	signal처럼 오해될 수 있음
alpha_score	금지	L2 권한 초과
rank	금지	L2 권한 초과
expected_return	금지	L2 권한 초과
order_intent	금지	절대 금지
4. 무엇을 묶고, 무엇을 분리할지
권장 grouping
구분	묶을지	이유
L1 row packetization + L2 diagnostic materialization	묶는 것 권장	15분 loop에서 순차 실행하면 운영 단순
L0 real-time collection	분리	수집 실패가 L1/L2를 막지 않게
L0 historical backfill	분리	장시간 실행, retry, source별 차이 큼
ticker/entity mapping	반분리	기본 mapping은 L1/L2 loop에 포함, 재처리/audit는 별도
backfill completion proof	별도 validator/report	loop 본체를 무겁게 만들지 않기
scheduler registration	별도 task/artifact	실행 권한과 검증 증거 분리
추천 subtasks
Subtask	내용
TASK-4147-A	L0 raw item manifest + L1 row/article packet contract
TASK-4147-B	L2 diagnostic feature schema materialization
TASK-4147-C	newswire ticker/entity mapping audit 개선
TASK-4147-D	L0 realtime config + durable 15분 L1/L2 scheduler
TASK-4147-E	backfill completion proof + final validator bundle

너무 잘게 쪼갤 필요는 없습니다.
다만 L1 row-level 전환과 scheduler 등록은 분리하는 것이 좋습니다.
검증 안 된 loop를 durable scheduler에 먼저 올리면 나중에 중복/오염된 데이터가 쌓일 수 있습니다.

5. 항목별 산출물
항목	필수 산출물
1. L1 row/article packet 확장	l1_row_packet_contract_4147.md, l1_row_packet_inventory.csv, l1_blocker_rollup.csv, l1_lineage_sample.jsonl
2. newswire ticker/entity mapping	newswire_entity_mapping_rules.yaml, newswire_mapping_coverage.csv, newswire_ambiguous_unmapped.csv, newswire_mapping_audit_sample.csv
3. L0 realtime config	l0_realtime_operating_profile.yaml, l0_realtime_config_validation.json, authority_closed_config_proof.json
4. durable 15분 L1/L2 loop	scheduler registration proof, wrapper script, heartbeat/status json, last run/validation report
5. backfill completion proof	backfill_completion_matrix.csv, backfill_gap_unknown_blocker_rollup.csv, source_window_completion_report.md
6. L2 actual feature schema materialization	l2_diagnostic_feature_contract.md, feature schema migration/DDL summary, l2_feature_materialization_summary.csv, l2_feature_lineage_proof.csv, authority_zero_proof.json
전체 TASK-4147	task_4147_final_report.md, artifact_manifest.csv, validate_task_4147_summary.json
6. 최소 validator
최소 validator 목록
Validator	반드시 확인할 것
L0 raw item manifest validator	raw item ID/hash 존재, 중복률, source lane별 count, batch와 raw item 연결
L1 row packet validator	raw item 단위 packet 생성, READY/BLOCKED 상태, blocker code 존재, source time 품질
L1/L2 contract validator	L2가 L1 READY packet만 소비, L0 raw 직접 소비 금지
L2 feature schema validator	feature row가 durable schema에 저장, 모든 row에 l1_packet_id 존재
Feature idempotency validator	같은 run 재실행 시 중복 row 폭증 없음
Entity mapping validator	high-confidence mapping의 근거 존재, ambiguous 강제 mapping 금지
Scheduler validator	15분 interval, overlap lock, heartbeat, last exit 0, validation exit 0
Backfill completion validator	source/window별 success/gap/UNKNOWN/BLOCKER 증거
Authority-zero validator	trading/order/broker/paper/live 관련 opened rows = 0
Sensitive table no-mutation validator	signal/order/broker table count 또는 hash 변화 없음
가장 중요한 validator 3개만 고르면
우선순위	Validator	이유
1	L1/L2 contract validator	L2가 L1 gate를 우회하면 구조가 무너짐
2	Authority-zero validator	trading safety hard boundary
3	Idempotency validator	15분 loop에서 중복 feature row 폭증 방지
7. 과도한 설계로 피해야 할 것

이번 TASK-4147에서 피해야 할 것은 명확합니다.

피해야 할 것	이유
대형 DAG/orchestrator 재작성	현재 필요한 것은 contract 보강이지 플랫폼 재건축이 아님
완전한 feature store 구축	아직 diagnostic v1 단계
복잡한 NLP/NER 모델 도입	mapping audit 이전에 false positive 위험
ticker 미매핑을 전부 L1 BLOCK 처리	macro/context 뉴스가 부당하게 막힘
L2에서 score/rank/return/order intent 생성	L2 권한 초과
backfill “완전 완료” 과장	public source에서는 completion 정의가 제한적이어야 함
scheduler를 2개 경로에서 동시에 실행	중복 실행/race condition 위험
guard 파일만 계속 추가	실제 검증 없이 문서/가드만 늘어남
UI/대시보드 먼저 만들기	지금은 data contract와 lineage가 먼저
feature candidate를 trading feature로 오해하게 명명	safety boundary 흐림
8. signal/order/broker 권한을 닫은 채 실제 feature schema row를 만드는 방법

핵심은 schema materialization과 trading authority를 분리하는 것입니다.

원칙
허용:
L0 raw item
  → L1 row/article packet
  → L2 diagnostic feature schema row

금지:
L2 diagnostic feature
  → signal
  → score/ranking
  → order intent
  → paper/live/broker mutation
구체 규칙
구분	규칙
schema namespace	l2_diagnostic_news 같은 별도 namespace 사용
trading eligibility	모든 row에 trading_eligible = false
authority flag	diagnostic_only = true
downstream registration	strategy/signal consumer에 등록하지 않음
feature 이름	alpha, signal, rank, expected_return, order 계열 금지
DB write allowlist	feature schema와 diagnostic artifact만 write
sensitive table proof	signal/order/broker/paper/live table mutation 없음 증명
validator	materialization 전후 authority rows = 0 확인
중요한 표현

“feature schema에 넣는다”는 말은 괜찮습니다.
하지만 “trading feature로 승격한다”는 표현은 피해야 합니다.

정확한 표현은 이것입니다.

L2 diagnostic feature candidates are materialized into durable diagnostic feature schema rows, with no trading eligibility and no downstream signal/order authority.

한국어로는:

L2 진단용 feature 후보를 실제 feature schema에 저장하되, trading eligible은 false로 고정하고 signal/order 소비 경로에는 연결하지 않는다.

9. TASK-4147 Done Definition

TASK-4147은 아래 조건을 모두 만족해야 done으로 보는 것이 맞습니다.

TASK-4147 완료 기준
번호	Done 조건
1	L0 batch 내부 raw item/article이 고유 ID 또는 hash로 식별된다
2	L1 packet이 batch 단위가 아니라 row/article 단위로 생성된다
3	L1 packet은 READY/BLOCKED/UNKNOWN 상태와 blocker reason을 가진다
4	L2는 L1 READY packet만 소비한다
5	L2가 L0 raw를 직접 읽어 L1 gate를 우회하지 않는다
6	L2 diagnostic feature candidate가 durable feature schema row로 저장된다
7	모든 feature row에 l1_packet_id, source_time, run_id, diagnostic_only, trading_eligible=false가 존재한다
8	newswire ticker/entity mapping coverage와 ambiguous/unmapped report가 생성된다
9	L0 realtime operating config가 trading/order/broker 권한과 분리되어 있다
10	15분 L1/L2 loop가 durable scheduler에 등록되어 있고 heartbeat/status proof가 있다
11	backfill completion matrix가 source/window별로 생성된다
12	missing/stale/gap은 negative evidence가 아니라 UNKNOWN/BLOCKER로 표시된다
13	authority-zero validator에서 trading/order/broker/paper/live opened rows가 0이다
14	idempotency validator에서 같은 run 재실행 시 중복 feature row가 폭증하지 않는다
15	task_4147_final_report.md와 artifact_manifest.csv가 생성된다
10. 최종 권고

TASK-4147의 성공 기준은 “많은 기능 추가”가 아닙니다.

성공 기준은 이 한 문장입니다.

L0의 실제 기사/row가 L1에서 1건 단위로 검문되고, L2는 그 L1 READY packet만 읽어 진단용 feature schema row를 만들며, 그 과정에서 signal/order/broker 권한은 0으로 유지된다.

따라서 구현 우선순위는 다음처럼 잡는 것이 가장 안전합니다.

1. L0 raw item manifest
2. L1 row/article packet
3. L1/L2 contract validator
4. L2 diagnostic feature schema materialization
5. authority-zero validator
6. ticker/entity mapping audit 개선
7. realtime config 분리
8. durable 15분 loop 등록
9. backfill completion proof

가장 조심해야 할 실패 패턴은 두 가지입니다.

L1이 아직 batch 단위인데 L2 feature schema만 먼저 실제화하는 것

diagnostic feature를 만들었다는 이유로 signal/order/paper 쪽 권한이 암묵적으로 열리는 것

이 두 가지만 피하면, TASK-4147은 현재 TASK-4146의 working diagnostic pipeline v1을 실질적으로 한 단계 올리는 작업이 됩니다.