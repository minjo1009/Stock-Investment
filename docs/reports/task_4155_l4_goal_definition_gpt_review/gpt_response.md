Verdict

CONDITIONAL PASS

핵심 3줄 요약

현재 L0-L3 상태는 L4를 진단용 thesis bundle 작업으로 시작하기에는 충분합니다.

다만 L0 백필 미완료, L3 CONTRADICTION / MACRO_SECTOR / SECTOR_THEME 미구현 때문에 기관급 확정 thesis로 통과시키기에는 아직 부족합니다.

L4의 첫 목표는 “좋은 투자 결론”을 내는 것이 아니라, 근거·출처·관계·반증·차단 사유가 명확한 검토용 논지 묶음을 만드는 것입니다.

Plain-language conclusion

L4는 바로 시작해도 됩니다. 단, 시작 범위는 diagnostic thesis bundle bootstrap입니다. 현재 상태에서 L4가 INSTITUTIONAL_PASS, 투자 판단, 정책 액션, 포지션 판단, paper/live 가능 여부를 만들면 안 됩니다.

L4 Goal

One-sentence goal

L4의 목표는 L0-L3에서 올라온 source, feature, relation 후보를 이용해 출처와 근거가 추적 가능하고, 반증·공백·불확실성이 명시된 진단용 thesis bundle을 만드는 것입니다.

What L4 is

L4는 투자 논지 검수 계층입니다.

L2의 경제적 의미 후보와 L3의 관계 그래프를 받아서, “이 종목/섹터/매크로 맥락에 대해 어떤 thesis가 가능한가?”를 검토 가능한 묶음으로 정리합니다.

각 thesis bundle에는 반드시 다음이 있어야 합니다.

thesis statement

supporting evidence

context evidence

source lineage

L1/L2/L3 연결 정보

coverage gap

contradiction status

blocker / mixed / unknown 사유

institutional quality score 또는 quality status

L4는 확정 결론보다 검증 가능성을 우선합니다.

What L4 is not

L4는 전략 채택 계층이 아닙니다.

L4는 매수/매도/보유/비중/진입가/청산가를 만드는 계층이 아닙니다.

L4는 L3 graph count를 근거 품질로 착각해서 ranking을 만드는 계층이 아닙니다.

L4는 누락 데이터를 부정 증거로 해석하는 계층이 아닙니다.

L4는 SOURCE_EVENT_CLUSTER를 확정 same-event로 바꾸는 계층이 아닙니다.

L4는 CONTRADICTION family 부재를 “반증 없음”으로 해석하는 계층이 아닙니다.

L4 Detailed Role And Responsibilities

responsibility	input	output	guardrail
Thesis candidate assembly	L2 diagnostic feature candidates, L3 relation graphs, L3 event clusters	l4_thesis_bundles.jsonl의 draft bundle	모든 thesis는 diagnostic_only=true; 투자 결론 금지
Evidence linkage	L1 packet IDs, L2 feature IDs, L3 edge/graph IDs, L0 source lineage metadata	l4_thesis_evidence_links.csv	raw L0만 단독 근거로 사용 금지. L1/L2 lineage 없는 evidence는 BLOCKED_LINEAGE_MISSING
Source traceability check	source lane, source id, source timestamp, ingest timestamp, source URL/path	source access status, lineage status	출처 접근 불가 또는 source-time 누락 시 thesis 품질 통과 금지
Thesis specificity review	thesis text, entity/symbol scope, time window, evidence roles	thesis specificity score/status	“AI 좋음”, “금리 영향 있음” 같은 일반론 thesis는 LOW_SPECIFICITY
Relation-quality carryover	L3 graph family, singleton rate, event identity status, same-event assertion flag	relation quality status	PROTO_BUCKET은 proto로 유지. same-event 확정 금지
Coverage gap visibility	L3 coverage gaps, L0 incomplete backfill state, L1/L2 blocked statuses	l4_thesis_blockers.csv	missing/stale/incomplete는 항상 UNKNOWN/BLOCKER; 부정 증거 금지
Contradiction handling	L3 contradiction family status, opposing evidence if available	contradiction status	현재 CONTRADICTION=NOT_IMPLEMENTED이므로 NO_CONTRADICTION 출력 금지
Mixed/context handling	macro context rows, entity dimension rows, source event proto buckets	mixed/context status	macro context를 causal thesis로 승격 금지
Institutional quality scoring	specificity, evidence linkage, traceability, coverage, contradiction, relation quality	diagnostic quality score/status	score는 trading authority가 아님. INSTITUTIONAL_PASS는 P0에서 금지
Validator handoff	L4 artifacts, manifest, schema version, hard-state flags	validation report	hard boundary 위반 시 즉시 FAIL
Audit manifest generation	input artifact counts, run timestamp, output paths, validation status	l4_run_manifest.json	재현 가능한 run metadata 필수
L4가 L0-L3에서 소비해야 하는 것
source layer	consume	purpose
L0	source lane, source id, source timestamp, collector/run id, source URL/path, coverage state	source-time integrity와 coverage blocker 판단
L1	normalized packet id, mapping status, entity/ticker mapping, source lineage, READY/BLOCKED 상태	근거가 검문소를 통과했는지 확인
L2	diagnostic economic meaning candidates, feature family, feature id, admitted/review-ready status	thesis의 의미 후보로 사용
L3	relation edges, event clusters, relation graphs, coverage gaps, graph family, quality guard 결과	thesis bundle의 관계 구조와 blocker 판단
Governance	L4 profile, forbidden intents, project hard state	trading authority 차단
L4가 소비하거나 추론하면 안 되는 것
prohibited input / inference	reason
L1/L2를 우회한 raw L0 단독 근거	lineage 없는 thesis 생성 위험
incomplete L0 coverage를 “해당 이슈 없음”으로 해석	missing data는 negative evidence가 아님
SOURCE_EVENT_CLUSTER를 confirmed same-event로 해석	L3가 PROTO_BUCKET이라고 명시
ENTITY_EVENT를 material event로 확정	L3는 candidate event link만 제공
MACRO_FACTOR를 causal macro thesis로 확정	macro context candidate일 뿐
CONTRADICTION family 부재를 contradiction clear로 해석	현재 미구현
graph count / edge count를 evidence quality로 사용	수량은 품질이 아님
price bars만으로 thesis confirmation 생성	L4는 trading signal 계층이 아님
broker/account/order/position data	L4 범위 밖이며 거래 권한 오픈 위험
ranking, sizing, order intent, paper/live eligibility	명시적 금지 영역

Required L4 Artifact Schema

첫 구현은 작고 검증 가능한 4개 artifact로 충분합니다.

4.1 data/diagnostics/l4/l4_thesis_bundles.jsonl

Purpose: thesis bundle의 주 테이블. 한 줄에 하나의 bundle.

Required fields
field	type	required	allowed / note
schema_version	string	yes	예: l4_thesis_bundle.v0.1
task_id	string	yes	예: TASK-4155
bundle_id	string	yes	deterministic hash 권장
created_at_utc	string	yes	ISO timestamp
diagnostic_only	boolean	yes	반드시 true
strategy_status	string	yes	반드시 NOT_ACCEPTED
deployment_status	string	yes	반드시 DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
real_capital	string	yes	반드시 FORBIDDEN
no_broker_mutation	boolean	yes	반드시 true
no_live_order	boolean	yes	반드시 true
no_paper_promotion	boolean	yes	반드시 true
bundle_status	string	yes	DRAFT_BLOCKED, DRAFT_MIXED, ASSEMBLED_FOR_REVIEW, INVALID
institutional_quality_status	string	yes	BLOCKED, MIXED, REVIEW_ONLY_DIAGNOSTIC
thesis_type	string	yes	ENTITY_EVENT, MACRO_CONTEXT, SOURCE_EVENT_PROTO, COVERAGE_GAP, MIXED_CONTEXT
thesis_statement	string	yes	one-sentence candidate thesis
thesis_scope	string	yes	single_entity, entity_group, macro_context, unknown
primary_symbols	array[string]	yes	macro-only면 빈 배열 허용
primary_entity_ids	array[string]	yes	없으면 빈 배열
source_lanes	array[string]	yes	예: public_context_news_feeds
time_window_start_utc	string/null	yes	source-time 기준
time_window_end_utc	string/null	yes	source-time 기준
l3_graph_ids	array[string]	yes	relation 기반이면 필수
l3_graph_families	array[string]	yes	예: SOURCE_EVENT_CLUSTER
l3_event_cluster_ids	array[string]	yes	없으면 빈 배열
event_identity_status	string	yes	현재는 주로 PROTO_BUCKET
same_event_assertion	boolean	yes	반드시 false
supporting_evidence_count	integer	yes	evidence link와 일치해야 함
context_evidence_count	integer	yes	evidence link와 일치해야 함
contradicting_evidence_count	integer	yes	현재 0 가능, 단 clear 아님
coverage_gap_count	integer	yes	gap/blocker와 일치
lineage_status	string	yes	OK, PARTIAL, MISSING, BLOCKED
source_access_status	string	yes	OK, PARTIAL, MISSING, BLOCKED
coverage_status	string	yes	COMPLETE, INCOMPLETE, UNKNOWN, BLOCKED
contradiction_status	string	yes	현재는 NOT_SCANNED_BLOCKER 허용/권장
relation_quality_status	string	yes	PROTO, SPARSE, MIXED, BLOCKED, UNKNOWN
thesis_specificity_score	number/null	yes	0-100, diagnostic
evidence_linkage_score	number/null	yes	0-100, diagnostic
source_traceability_score	number/null	yes	0-100, diagnostic
contradiction_handling_score	number/null	yes	0-100 또는 null
institutional_quality_score	number/null	yes	P0에서는 acceptance score로 쓰지 않음
block_reasons	array[string]	yes	없으면 빈 배열
warnings	array[string]	yes	없으면 빈 배열
Important P0 rule

현재 L3에서 CONTRADICTION family가 NOT_IMPLEMENTED이므로, P0 validator는 다음을 강제해야 합니다.

contradiction_status != "NO_CONTRADICTION"
institutional_quality_status != "PASS"
same_event_assertion == false
diagnostic_only == true
4.2 data/diagnostics/l4/l4_thesis_evidence_links.csv

Purpose: thesis와 근거의 연결 테이블. L4의 핵심은 이 파일입니다.

Required columns
column	required	note
schema_version	yes	l4_evidence_link.v0.1
bundle_id	yes	l4_thesis_bundles.jsonl과 join
evidence_link_id	yes	deterministic id
evidence_role	yes	supporting, context, contradicting, coverage_gap, blocker
evidence_claim	yes	근거가 주장하는 내용. 과도한 요약 금지
source_lane	yes	L0/L1 source lane
source_id	yes	raw source id 또는 source record id
source_url_or_path	no	있으면 기록
publisher_or_origin	no	있으면 기록
source_time_utc	yes	source-time integrity용
ingested_at_utc	no	있으면 기록
l1_packet_id	conditional	supporting/context evidence면 원칙적으로 필수
l1_mapping_status	conditional	예: HIGH_CONFIDENCE_DETERMINISTIC
l2_feature_id	conditional	L2 기반 evidence면 필수
l2_feature_family	conditional	예: MACRO_CONTEXT, NEWSWIRE_DISCOVERY
l3_edge_id	no	relation 기반이면 기록
l3_graph_id	no	relation 기반이면 기록
l3_graph_family	no	예: SOURCE_EVENT_CLUSTER
lineage_status	yes	OK, PARTIAL, MISSING, BLOCKED
source_access_status	yes	OK, PARTIAL, MISSING, BLOCKED
mapping_confidence	no	있으면 기록
evidence_quality_flag	yes	USABLE_DIAGNOSTIC, CONTEXT_ONLY, PROTO_ONLY, BLOCKED
negative_evidence_allowed	yes	반드시 false
P0 semantic rule

supporting evidence인데 l1_packet_id와 l2_feature_id가 모두 없으면 FAIL.

coverage_gap evidence는 L2 feature가 없어도 되지만, 반드시 gap reason 또는 L3 coverage gap id가 있어야 합니다.

negative_evidence_allowed=true는 무조건 FAIL입니다.

4.3 data/diagnostics/l4/l4_thesis_blockers.csv

Purpose: L4가 thesis를 왜 확정하지 못하는지 명시하는 차단 사유 테이블.

Required columns
column	required	allowed / note
schema_version	yes	l4_blocker.v0.1
bundle_id	yes	관련 bundle
blocker_id	yes	deterministic id
blocker_type	yes	아래 enum
severity	yes	P0, P1, P2
source_layer	yes	L0, L1, L2, L3, L4
related_artifact_id	no	graph id, packet id, feature id 등
reason	yes	plain text
required_action	yes	예: IMPLEMENT_CONTRADICTION_SCAN
is_hard_blocker	yes	boolean
negative_evidence_allowed	yes	반드시 false
Allowed blocker_type
L0_INCOMPLETE_COVERAGE
L1_BLOCKED_UNKNOWN
L2_FEATURE_MISSING
L3_COVERAGE_GAP
UNSUPPORTED_RELATION_FAMILY
CONTRADICTION_NOT_SCANNED
SOURCE_ACCESS_MISSING
LINEAGE_MISSING
MIXED_CONTEXT
PROTO_EVENT_IDENTITY
LOW_THESIS_SPECIFICITY
LOW_EVIDENCE_LINKAGE
SCHEMA_INVALID
Current expected blockers

현재 패킷 기준으로 최소한 다음 blocker는 표현되어야 합니다.

current issue	expected L4 blocker
L0 backfills incomplete	L0_INCOMPLETE_COVERAGE
newswire mapped but no article L2 feature	L3_COVERAGE_GAP
CONTRADICTION not implemented	CONTRADICTION_NOT_SCANNED
MACRO_SECTOR not implemented	UNSUPPORTED_RELATION_FAMILY
SECTOR_THEME not implemented	UNSUPPORTED_RELATION_FAMILY
L3 proto event buckets	PROTO_EVENT_IDENTITY
4.4 data/diagnostics/l4/l4_run_manifest.json

Purpose: run 단위 재현성, 입력/출력/검증 상태 기록.

Required fields
field	required	note
schema_version	yes	l4_run_manifest.v0.1
task_id	yes	TASK-4155
created_at_utc	yes	ISO timestamp
diagnostic_only	yes	반드시 true
hard_boundaries	yes	strategy/deployment/real capital/order/broker flags
input_artifacts	yes	L1/L2/L3 artifact paths, counts if available
l0_coverage_state	yes	incomplete lanes 포함
l3_quality_guard_state	yes	graph families, unsupported families, coverage gap counts
output_artifacts	yes	생성된 L4 files
bundle_count	yes	integer
evidence_link_count	yes	integer
blocker_count	yes	integer
validation_status	yes	PASS, FAIL, NOT_RUN
validation_errors	yes	array
notes	yes	array

L4 Validator Plan

5.1 Validator checks
check group	required checks
File existence	4개 artifact 존재 확인: bundles, evidence links, blockers, manifest
Schema validation	required fields/columns 존재, type, enum 확인
Hard boundary validation	모든 bundle과 manifest에서 diagnostic_only=true, strategy_status=NOT_ACCEPTED, deployment_status=DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY, real_capital=FORBIDDEN
Forbidden authority validation	final_policy_action, order_intent, position_size, target_weight, paper_eligible, live_eligible, broker_mutation, strategy_accepted, deployment_ready 같은 field 존재 시 FAIL
Evidence linkage validation	supporting/context evidence는 L1/L2 lineage 필요. raw-only evidence는 FAIL
Count consistency	bundle의 evidence count와 evidence link table 집계 일치
Coverage gap handling	L3 coverage gap이 관련 bundle에 blocker로 반영되어야 함
Missing-data semantics	negative_evidence_allowed는 모든 row에서 false여야 함
Proto-event preservation	event_identity_status=PROTO_BUCKET이면 same_event_assertion=false 강제
Unsupported relation handling	MACRO_SECTOR, SECTOR_THEME, CONTRADICTION 미구현 상태를 clear로 해석하면 FAIL
Contradiction handling	현재 상태에서 contradiction_status=NO_CONTRADICTION이면 FAIL
Quality status validation	hard blocker가 있으면 institutional_quality_status=BLOCKED 또는 MIXED여야 함
Score validation	score가 있으면 0-100 범위. null 허용
Manifest consistency	manifest count와 실제 artifact count 일치
Determinism smoke check	같은 input으로 2회 실행 시 bundle_id/evidence_link_id 안정성 확인
5.2 Failure conditions

아래 중 하나라도 발생하면 validator는 FAIL이어야 합니다.

failure	reason
L4 artifact에 trading action field 존재	L4 권한 초과
diagnostic_only 누락 또는 false	hard boundary 위반
strategy_status != NOT_ACCEPTED	전략 승인 오인 위험
deployment_status != DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY	배포 가능 오인 위험
real_capital != FORBIDDEN	real capital boundary 위반
evidence가 L1/L2 lineage 없이 supporting evidence로 사용됨	source traceability 실패
coverage gap을 negative evidence로 해석	프로젝트 hard rule 위반
contradiction 미구현인데 NO_CONTRADICTION 출력	반증 검토 허위 clear
SOURCE_EVENT_CLUSTER를 confirmed same-event로 출력	L3 handoff rule 위반
blocker가 있는데 quality status가 pass/clear	institutional quality 오인
manifest와 실제 artifact count 불일치	재현성 실패
bundle_id가 비결정적으로 바뀜	audit/replay 불가

L4 Development Plan

P0/P1 prioritized table
priority	task	concrete implementation	expected output	acceptance condition
P0	L4 package skeleton	src/brain/l4_thesis_bundle/ 생성. schema.py, builder.py, __init__.py	import 가능한 L4 package	python -m py_compile PASS
P0	Artifact schema definition	위 4개 artifact schema를 코드 상수/TypedDict/dataclass로 정의	schema contract	validator가 schema를 기준으로 검사
P0	Deterministic bundle builder	L2/L3 artifact를 읽어 thesis bundle 초안 생성. relation family별 최소 template 적용	l4_thesis_bundles.jsonl, l4_thesis_evidence_links.csv, l4_thesis_blockers.csv, l4_run_manifest.json	L4 artifact 생성 성공
P0	Hard-boundary injection	모든 artifact에 diagnostic/hard-state fields 강제	hard boundary visible	누락/변경 시 validator FAIL
P0	Proto/unknown/blocker preservation	L3의 PROTO_BUCKET, coverage gaps, unsupported families를 L4 blocker로 carryover	blocker rows	contradiction/coverage/missing이 clear로 바뀌지 않음
P0	L4 semantic validator	src/validation/l4_thesis_bundle_validator.py 구현	validation result	forbidden authority, lineage, proto, contradiction checks PASS
P0	CLI scripts	scripts/build_l4_thesis_bundles.py, scripts/validate_l4_thesis_bundle_package.py	reproducible commands	로컬에서 builder→validator 순서 실행 가능
P0	Unit tests	tests/test_l4_thesis_bundle_package.py	semantic regression tests	contradiction 미구현 clear 금지, raw-only evidence 금지, trading field 금지
P0	Task report / manifest	docs/reports/task_4155_l4_thesis_bundle_bootstrap/	report, artifact manifest, validation summary	사람이 현재 상태를 바로 이해 가능
P1	Quality score v0	specificity, evidence linkage, source traceability, coverage, contradiction, relation quality component score	diagnostic score fields	score가 action/acceptance로 사용되지 않음
P1	Thesis type templates	ENTITY_EVENT, MACRO_CONTEXT, SOURCE_EVENT_PROTO, COVERAGE_GAP, MIXED_CONTEXT별 thesis statement template	more readable bundles	generic thesis 감소
P1	Blocked/mixed summary report	bundle status별 count, blocker type별 count	l4_summary.md 또는 csv	운영자가 다음 blocker를 볼 수 있음
P1	Source access checker	source URL/path/readability read-only check	source access status 개선	inaccessible source가 BLOCKED로 표시
P1	L3 dependency feedback	L4가 요구하는 L3 relation families 명세화	L3 follow-up ticket	CONTRADICTION, MACRO_SECTOR, SECTOR_THEME 구현 필요성 명확화
Recommended execution order

P0-1: schema + skeleton

P0-2: deterministic builder

P0-3: validator

P0-4: tests

P0-5: report/manifest

P1: quality score와 thesis templates 개선

현재 가장 중요한 것은 thesis quality를 화려하게 만드는 것이 아니라, 허위 확정·허위 반증 clear·거래 권한 오픈을 막는 L4 계약을 먼저 세우는 것입니다.

What L4 Must Not Do

Explicit cut list
cut item	reason
BUY/SELL/HOLD 생성	L4 권한 밖
ranking 생성	L4 권한 밖. L5/L6도 현재 금지 상태
sizing, target weight, position size 생성	trading authority 오픈 위험
order intent 생성	명시적 금지
paper/live eligibility 생성	paper promotion/live order 금지
broker/account/order/position mutation	hard boundary 위반
strategy acceptance 판단	Strategy=NOT_ACCEPTED 고정
deployment readiness 판단	DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY 고정
L0 incomplete coverage를 negative evidence로 사용	missing data rule 위반
L3 cluster를 confirmed event로 승격	L3 handoff rule 위반
graph count를 thesis quality로 사용	수량과 품질 혼동
contradiction 미구현을 no contradiction으로 출력	가장 위험한 허위 clear
macro context를 causal macro thesis로 단정	L3 MACRO_FACTOR는 candidate only
macro-sector/sector-theme absence를 부정 증거로 사용	relation family 미구현 상태
LLM free-form thesis generation부터 도입	재현성/검증성 약함
vector DB, graph DB, ontology 대공사	P0 범위 초과
UI/dashboard 먼저 개발	검증 계약 전 UI는 과속
실시간 scheduler 연결	L4 bootstrap에서는 불필요
가격/기술적 지표 기반 entry thesis	trading signal과 혼선
portfolio construction	L4 범위 밖
Current state sufficiency answer

현재 L0-L3 상태는 L4 diagnostic bootstrap을 시작하기에는 충분합니다.

다만 충분한 것은 아래 범위입니다.

scope	sufficient?	reason
L4 schema 설계	yes	L3 handoff rule과 L4 governance가 이미 명확
L4 artifact builder 시작	yes	L1/L2/L3 row와 graph artifact가 존재
L4 blocker/mixed visibility	yes	coverage gap과 unsupported family 정보가 있음
L4 validator 시작	yes	금지사항과 required checks가 명확
institutional-quality thesis pass	no	contradiction/macro-sector/sector-theme 미구현, L0 incomplete
strategy/paper/live 판단	no	hard boundary상 명시 금지

Codex Patch Prompt

Markdown
# TASK-4155 L4 Diagnostic Thesis Bundle Bootstrap

You are working on the local repository state. Do not assume GitHub has the latest L0-L3 work.

## Hard boundaries

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data is UNKNOWN/BLOCKER, never negative evidence
- L4 must not produce final policy actions, order intent, sizing, ranking, live/paper eligibility, broker mutation, strategy acceptance, or deployment readiness.

## Goal

Implement the first practical L4 package for diagnostic-only thesis bundles.

L4 should construct reviewable thesis bundles from existing L1/L2/L3 artifacts and explicitly preserve:
- source traceability
- L1/L2/L3 lineage
- L3 proto relation status
- coverage gaps
- contradiction-not-scanned blockers
- unsupported relation family blockers
- mixed/context status

Do not build a trading model. Do not create BUY/SELL/HOLD. Do not create ranking, sizing, order intent, paper/live readiness, broker integration, or strategy acceptance.

## Required files

Create or update:

- `src/brain/l4_thesis_bundle/__init__.py`
- `src/brain/l4_thesis_bundle/schema.py`
- `src/brain/l4_thesis_bundle/builder.py`
- `scripts/build_l4_thesis_bundles.py`
- `src/validation/l4_thesis_bundle_validator.py`
- `scripts/validate_l4_thesis_bundle_package.py`
- `tests/test_l4_thesis_bundle_package.py`
- `docs/reports/task_4155_l4_thesis_bundle_bootstrap/task_4155_report.md`
- `docs/reports/task_4155_l4_thesis_bundle_bootstrap/artifact_manifest.csv`

## Required output artifacts

The builder must write:

- `data/diagnostics/l4/l4_thesis_bundles.jsonl`
- `data/diagnostics/l4/l4_thesis_evidence_links.csv`
- `data/diagnostics/l4/l4_thesis_blockers.csv`
- `data/diagnostics/l4/l4_run_manifest.json`

If the exact local L1/L2/L3 artifact paths differ, discover and use the current local project paths. Do not invent data. If an input artifact is missing, fail closed and write a manifest with validation status `FAIL` or blocker status, not fake bundles.

## L4 bundle schema requirements

Each row/object in `l4_thesis_bundles.jsonl` must include at least:

- `schema_version`
- `task_id`
- `bundle_id`
- `created_at_utc`
- `diagnostic_only`
- `strategy_status`
- `deployment_status`
- `real_capital`
- `no_broker_mutation`
- `no_live_order`
- `no_paper_promotion`
- `bundle_status`
- `institutional_quality_status`
- `thesis_type`
- `thesis_statement`
- `thesis_scope`
- `primary_symbols`
- `primary_entity_ids`
- `source_lanes`
- `time_window_start_utc`
- `time_window_end_utc`
- `l3_graph_ids`
- `l3_graph_families`
- `l3_event_cluster_ids`
- `event_identity_status`
- `same_event_assertion`
- `supporting_evidence_count`
- `context_evidence_count`
- `contradicting_evidence_count`
- `coverage_gap_count`
- `lineage_status`
- `source_access_status`
- `coverage_status`
- `contradiction_status`
- `relation_quality_status`
- `thesis_specificity_score`
- `evidence_linkage_score`
- `source_traceability_score`
- `contradiction_handling_score`
- `institutional_quality_score`
- `block_reasons`
- `warnings`

Required hard values:

- `diagnostic_only == true`
- `strategy_status == "NOT_ACCEPTED"`
- `deployment_status == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"`
- `real_capital == "FORBIDDEN"`
- `no_broker_mutation == true`
- `no_live_order == true`
- `no_paper_promotion == true`
- `same_event_assertion == false`

Allowed `bundle_status`:

- `DRAFT_BLOCKED`
- `DRAFT_MIXED`
- `ASSEMBLED_FOR_REVIEW`
- `INVALID`

Allowed `institutional_quality_status`:

- `BLOCKED`
- `MIXED`
- `REVIEW_ONLY_DIAGNOSTIC`

Do not output `PASS`, `ACCEPTED`, `READY_FOR_TRADING`, `PAPER_READY`, or similar authority-granting statuses.

## Evidence links schema requirements

`l4_thesis_evidence_links.csv` must include at least:

- `schema_version`
- `bundle_id`
- `evidence_link_id`
- `evidence_role`
- `evidence_claim`
- `source_lane`
- `source_id`
- `source_url_or_path`
- `publisher_or_origin`
- `source_time_utc`
- `ingested_at_utc`
- `l1_packet_id`
- `l1_mapping_status`
- `l2_feature_id`
- `l2_feature_family`
- `l3_edge_id`
- `l3_graph_id`
- `l3_graph_family`
- `lineage_status`
- `source_access_status`
- `mapping_confidence`
- `evidence_quality_flag`
- `negative_evidence_allowed`

`negative_evidence_allowed` must always be false.

Supporting/context evidence should not be raw-only. It must carry L1/L2 lineage when available. If lineage is unavailable, mark it blocked instead of treating it as usable evidence.

## Blockers schema requirements

`l4_thesis_blockers.csv` must include at least:

- `schema_version`
- `bundle_id`
- `blocker_id`
- `blocker_type`
- `severity`
- `source_layer`
- `related_artifact_id`
- `reason`
- `required_action`
- `is_hard_blocker`
- `negative_evidence_allowed`

Allowed blocker types:

- `L0_INCOMPLETE_COVERAGE`
- `L1_BLOCKED_UNKNOWN`
- `L2_FEATURE_MISSING`
- `L3_COVERAGE_GAP`
- `UNSUPPORTED_RELATION_FAMILY`
- `CONTRADICTION_NOT_SCANNED`
- `SOURCE_ACCESS_MISSING`
- `LINEAGE_MISSING`
- `MIXED_CONTEXT`
- `PROTO_EVENT_IDENTITY`
- `LOW_THESIS_SPECIFICITY`
- `LOW_EVIDENCE_LINKAGE`
- `SCHEMA_INVALID`

Current L3 unsupported families must be represented as blockers where relevant:

- `MACRO_SECTOR = NOT_IMPLEMENTED`
- `SECTOR_THEME = NOT_IMPLEMENTED`
- `CONTRADICTION = NOT_IMPLEMENTED`

Current L3 proto event rule must be preserved:

- `event_identity_status = PROTO_BUCKET`
- `same_event_assertion = false`

## Validator requirements

Implement `src/validation/l4_thesis_bundle_validator.py` and CLI script.

Validator must fail if:

- required artifacts are missing
- required fields/columns are missing
- hard boundary fields are absent or changed
- any forbidden trading authority field appears
- `diagnostic_only` is not true
- `strategy_status` is not `NOT_ACCEPTED`
- `deployment_status` is not `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- `real_capital` is not `FORBIDDEN`
- `same_event_assertion` is true
- `contradiction_status` says `NO_CONTRADICTION` while contradiction family is not implemented
- `negative_evidence_allowed` is true anywhere
- supporting evidence has no L1/L2 lineage and is not marked blocked
- bundle evidence counts do not match evidence link rows
- manifest counts do not match actual artifacts
- quality status implies institutional pass, strategy acceptance, deployment readiness, or trading permission

## Tests

Add unit tests that verify:

1. Hard boundary fields are mandatory.
2. Forbidden trading fields are rejected.
3. Raw-only supporting evidence fails.
4. Coverage gap is treated as blocker, not negative evidence.
5. `CONTRADICTION_NOT_SCANNED` is required when contradiction family is not implemented.
6. `SOURCE_EVENT_CLUSTER` does not become confirmed same-event.
7. Bundle/evidence count mismatches fail.
8. Manifest/artifact count mismatches fail.
9. Builder output is deterministic for the same fixture input.
10. P0 output can be blocked/mixed and still be valid as diagnostic artifact output.

## Validation commands

Run at minimum:

```bash
python -m py_compile src/brain/l4_thesis_bundle/schema.py src/brain/l4_thesis_bundle/builder.py src/validation/l4_thesis_bundle_validator.py
python scripts/build_l4_thesis_bundles.py
python scripts/validate_l4_thesis_bundle_package.py
python -m unittest tests.test_l4_thesis_bundle_package

If local project test conventions differ, use the closest existing validator/test style.

Report

Create:

docs/reports/task_4155_l4_thesis_bundle_bootstrap/task_4155_report.md

docs/reports/task_4155_l4_thesis_bundle_bootstrap/artifact_manifest.csv

The report must clearly state:

L4 is diagnostic-only.

Strategy remains NOT_ACCEPTED.

Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.

Real capital remains FORBIDDEN.

No broker mutation, no live order, no paper promotion.

Current L0 incomplete coverage is UNKNOWN/BLOCKER.

Current L3 contradiction/macro-sector/sector-theme gaps are not negative evidence.

L4 artifacts are thesis review artifacts, not trading decisions.

Do not over-engineer

Do not implement:

graph database

vector database

LLM thesis writer

portfolio construction

price-based signal model

ranking engine

broker integration

scheduler

UI

paper/live gate

strategy acceptance gate

Keep this patch bounded to L4 schema, deterministic builder, validator, tests, and report.