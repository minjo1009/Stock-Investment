# GPT Response

CAPTURED via ChatGPT Pro Chrome session.

- source_url: https://chatgpt.com/c/6a42f2e9-36b0-83e8-9ebc-99e7e7e329f6
- capture_status: CAPTURED

## GPT Recommendation

핵심 세 줄 요약

L2는 매매 신호층이 아니라, L1이 인증한 원천을 “안전한 primitive envelope”로 바꾸는 얇은 intake/normalization layer로 시작해야 합니다.

**TASK-4136의 첫 산출물은 L2 feature/materialization이 아니라 L2 Intake Contract + Validator + Intake Manifest**가 맞습니다.

실제 source consumption은 daily_bars → market_bars_5m → macro/context → public_newswire discovery 순서가 가장 안전합니다. 뉴스/매크로는 절대 trading feature로 먼저 쓰면 안 됩니다.

결론 판정

제공된 TASK-4135 패킷 기준으로는 “L2 계약/검증 계층 진입은 GO”, 그러나 “L2 production primitive materialization, signal, scoring, L3 연결은 NO-GO”입니다.

근거는 다음입니다.

항목	패킷상 상태	해석
L1 packet count	5	5개 source family 모두 L1 packet 존재
coverage rows	5	coverage snapshot과 source family 수 일치
gap count	0	현재 보고상 L1 coverage gap 없음
strict gate pass count	2	strict source-time family는 daily/5m 두 개로 보임
L2 materialization written	false	아직 L2 산출물 없음. 오히려 안전한 상태
trading authority opened	false	hard boundary 유지
legacy L0→L2 news ingest	blocked by default	반드시 유지해야 함

즉, 지금 해야 할 일은 L2를 만드는 것이 아니라, 먼저 L2가 무엇을 받을 수 있고, 무엇을 절대 feature로 승격하면 안 되는지 계약화하는 것입니다.

1. L2의 책임과 L1에 남겨야 할 책임
L2가 책임져야 할 것

L2는 certified evidence를 trading-safe primitive envelope로 변환하는 계층이어야 합니다.

정확히는 다음 역할입니다.

L2 책임	설명
Intake contract enforcement	L1 packet의 classification과 handoff contract를 읽고 L2 허용 용도를 결정
Primitive envelope 생성	raw data 자체가 아니라 source_family, asof, lineage, allowed_use, primitive_type을 가진 소비 가능한 wrapper 생성
Allowed-use routing	strict market observation, context-only, discovery-only를 분리
Lineage preservation	source_packet_id, raw_path, raw_sha256, decision_asof_ts, available_to_brain_ts를 잃지 않음
No-future/no-negative guard	future outcome assignment, missing-as-negative를 L2에서도 재차 차단
Downstream contract 제공	L3가 무엇을 사용할 수 있고 무엇은 사용할 수 없는지 명확히 전달

핵심은 L2가 “관측값을 안전하게 포장”하는 계층이라는 점입니다.
아직 score, rank, signal, thesis, action, sizing을 만들면 안 됩니다.

L1에 반드시 남겨야 할 것

L1은 지금처럼 evidence checkpoint로 남아야 합니다.

L1에 남겨야 할 책임	이유
source-time certification	L2가 source time을 재해석하면 leakage 위험 증가
raw integrity / hash 검증	raw file 또는 DB row integrity는 L1의 증거 책임
mapping gate	symbol/candidate/source mapping은 L1에서 확정되어야 함
authority gate	trading authority, feature authority는 L1에서 차단되어야 함
coverage/gap 판단	missing/stale data는 L1에서 UNKNOWN/BLOCKER로 처리
missing_source_is_negative 금지	L2가 missing을 bearish/bullish evidence로 바꾸면 안 됨
future outcome assignment 차단	L2는 outcome-label 생성층이 아님

정리하면, L1은 “이 데이터를 써도 되는가?”를 판정하고, L2는 “허용된 방식으로만 포장한다”가 되어야 합니다.

2. 첫 번째 최소 L2 artifact/schema/contract
추천 산출물

첫 L2 산출물은 다음 3개가 적절합니다.

산출물	목적
l2_intake_contract.yaml	source family별 L2 허용 용도 고정
l2_intake_manifest.csv/jsonl	실제 L1 packet을 L2 primitive envelope 후보로 등록
l2_intake_validation_report.json	L1 gate, handoff, stale, authority, legacy import 차단 결과 기록

중요한 점은, 이것은 feature materialization이 아닙니다.
daily_bars나 5m의 실제 OHLCV primitive row를 대량으로 쓰기 전에, 먼저 L2가 어떤 family를 어떤 권한으로 받을지를 검증해야 합니다.

최소 contract 예시

아래 구조가 TASK-4136의 기준 계약으로 적절합니다.

YAML
version: 1
task_id: TASK-4136
contract_name: l2_intake_contract
trading_authority_opened: false
paper_promotion_allowed: false
broker_mutation_allowed: false
missing_source_is_negative_allowed: false
future_outcome_assignment_allowed: false

families:
  daily_bars:
    required_l1_classification: STRICT_SOURCE_TIME_CERTIFIED
    required_l2_allowed_use: L2_PRIMITIVE_INPUT_ALLOWED_MARKET_OBSERVATION_ONLY
    primitive_envelope_type: DAILY_MARKET_OBSERVATION
    feature_materialization_allowed: false
    review_queue_only: false

  market_bars_5m:
    required_l1_classification: STRICT_SOURCE_TIME_CERTIFIED
    required_l2_allowed_use: L2_PRIMITIVE_INPUT_ALLOWED_MARKET_OBSERVATION_ONLY
    primitive_envelope_type: INTRADAY_5M_MARKET_OBSERVATION
    feature_materialization_allowed: false
    review_queue_only: false

  public_context_news_feeds:
    required_l1_classification: CONTEXT_ONLY_CERTIFIED
    required_l2_allowed_use: L2_CONTEXT_INPUT_ALLOWED_NOT_TRADING_FEATURE
    primitive_envelope_type: CONTEXT_REFERENCE
    feature_materialization_allowed: false
    review_queue_only: false

  public_market_macro_news_feeds:
    required_l1_classification: CONTEXT_ONLY_CERTIFIED
    required_l2_allowed_use: L2_CONTEXT_INPUT_ALLOWED_NOT_TRADING_FEATURE
    primitive_envelope_type: MACRO_CONTEXT_REFERENCE
    feature_materialization_allowed: false
    review_queue_only: false

  public_newswire_feeds:
    required_l1_classification: DISCOVERY_ONLY
    required_l2_allowed_use: L2_REVIEW_QUEUE_ONLY_NOT_FEATURE
    primitive_envelope_type: DISCOVERY_REVIEW_REFERENCE
    feature_materialization_allowed: false
    review_queue_only: true

핵심은 feature_materialization_allowed: false입니다.
지금은 L2 primitive envelope만 만들고, L3/L4에서 쓰일 feature나 signal은 만들지 않는 단계가 맞습니다.

l2_intake_manifest 최소 컬럼

l2_intake_manifest는 다음 컬럼을 가져야 합니다.

컬럼	설명
task_id	예: TASK-4136
l2_intake_id	L2 intake row 고유 ID
source_family	daily_bars, market_bars_5m 등
source_packet_id	L1 packet lineage
candidate_id	L1 candidate lineage. 없으면 null 가능
symbol	market source는 필수, context/news는 nullable 가능
decision_asof_ts	decision 기준 시각
source_ts	원천 발생/관측 시각
available_to_brain_ts	brain이 볼 수 있었던 시각
l1_classification	L1 classification
l2_allowed_use	handoff contract 결과
primitive_envelope_type	L2 primitive wrapper type
l2_materialization_state	INTAKE_ONLY_NOT_MATERIALIZED
l2_block_status	PASS, BLOCKED_L1_GATE, BLOCKED_STALE, 등
block_reason	block 사유
raw_path	L1 raw lineage
raw_sha256	L1 raw integrity lineage
authority	trading authority 없음 명시

이 manifest는 “L2가 이 source를 어떤 권한으로 받아들였는가”를 증명하는 장부입니다.

3. 어떤 source family부터 소비해야 하는가
권장 순서
순서	Source family	판정	이유
0	L1 packet metadata / handoff contract	가장 먼저	raw data보다 먼저 “무엇을 받을 수 있는지” 검증해야 함
1	daily_bars	첫 실제 primitive 후보	strict certified, CSV raw path가 TASK-4134에서 수정됨, row 수 11,964로 검증 부담 적음
2	market_bars_5m	두 번째	strict certified이나 row 수 21,695,078로 크고, microstructure builder가 비어 있음
3	public_market_macro_news_feeds	세 번째	context-only로만 사용. market regime 해석에는 유용하나 feature화 금지
4	public_context_news_feeds	네 번째	context-only. symbol-level trading signal로 쓰면 위험
5	public_newswire_feeds	마지막	discovery-only. review queue 외 사용 금지
실제 개발 순서
먼저 할 것

daily_bars를 첫 primitive 대상으로 삼는 것이 가장 안전합니다.

이유는 명확합니다.

STRICT_SOURCE_TIME_CERTIFIED

real raw CSV path 문제를 TASK-4134에서 이미 고침

5m보다 row volume이 작음

legacy news builder와 무관

L2 market observation schema 검증에 가장 적합

다만 TASK-4136에서는 아직 daily row materialization까지 가지 않는 편이 더 안전합니다.
TASK-4136은 계약과 validator까지, TASK-4137에서 daily market observation primitive v0로 가는 순서가 좋습니다.

4. L2를 차단해야 하는 validators

아래 validator들은 L2 진입 전 필수 block gate입니다.

Validator	Block 조건	이유
validate_required_l1_columns	L1 packet 필수 컬럼 누락	L2가 lineage/asof/authority를 보존할 수 없음
validate_l1_gate_status	source_time, raw_integrity, mapping, authority gate 누락 또는 실패	L1 checkpoint 미통과 source 차단
validate_handoff_contract	L1 classification과 L2 allowed use 불일치	context/news가 feature로 승격되는 것 방지
validate_no_blocked_class	BLOCKED_* classification 존재	blocked source는 L2 intake 금지
validate_source_time_order	source_ts > available_to_brain_ts 또는 available_to_brain_ts > decision_asof_ts	future leakage 차단
validate_strict_source_time_for_market	daily/5m인데 source_time_certified가 true가 아님	market primitive는 strict source-time 필수
validate_raw_lineage_present	raw_path 또는 raw_sha256 누락	primitive lineage 단절 차단
validate_missing_not_negative	missing_source_is_negative != false	missing/stale을 bearish/bullish evidence로 오해하는 것 차단
validate_no_future_outcome_assignment	assignment_uses_future_outcome == true 또는 outcome_used_for_assignment == true	label leakage 차단
validate_l1_coverage_freshness	L1 coverage artifact가 stale 또는 expected window 누락	오래된 L1 결과를 최신인 것처럼 쓰는 것 방지
validate_trading_authority_closed	trading authority, broker mutation, order intent 필드가 열림	hard state 위반 차단
validate_legacy_l2_import_quarantine	TASK-4136 코드가 broken legacy news builder를 import	깨진 L2 surface가 신규 경로를 오염시키는 것 방지
validate_no_l0_direct_to_l2	L0 raw news를 L1 packet 없이 직접 L2로 ingest	기존 legacy bypass 재발 방지
stale/gap 처리 원칙

Stale과 missing은 다음처럼 처리해야 합니다.

상태	처리
source row missing	UNKNOWN/BLOCKER
source stale	BLOCKED_STALE_SOURCE
context/news stale	BLOCKED_CONTEXT_STALE, 절대 negative evidence 아님
newswire 없음	DISCOVERY_UNAVAILABLE, 절대 bearish/bullish evidence 아님
5m 일부 구간 missing	BLOCKED_MARKET_OBSERVATION_GAP, zero volume으로 대체 금지

특히 5m bar는 row 수가 크기 때문에, L2에서 “없는 구간을 0으로 채우는 방식”은 금지해야 합니다.
그건 관측값 보정이 아니라 가짜 market observation 생성입니다.

5. 기존 broken/legacy L2 news builder/import surfaces 처리

패킷상 기존 src/l2/builders/news_event_primitives.py는 다음 문제가 있습니다.

존재는 하지만,

src.l2.contracts, freshness, lineage, runtime_context, news_runtime 등 누락 가능성이 있고,

legacy direct L0→L2 news ingest는 이미 blocked by default 상태입니다.

따라서 권장 처리는 수리보다 격리입니다.

해야 할 처리
조치	설명
Quarantine	기존 news builder를 TASK-4136 runtime path에서 제외
No semantic stub	누락 모듈을 빈 파일로 만들어 import만 통과시키는 것 금지
No production repair	TASK-4136에서 legacy news builder를 생산 경로로 되살리지 않음
Static audit	어떤 import가 깨져 있는지 local file 기준으로 문서화
Blocklist test	신규 L2 intake 코드가 legacy builder를 import하면 test fail
Future adapter only	나중에 필요하면 legacy builder를 새 L2 contract에 맞는 adapter로 재작성

가장 위험한 작업은 contracts.py, freshness.py, lineage.py 등을 대충 만들어 import error만 없애는 것입니다.
그렇게 하면 broken legacy path가 “작동하는 것처럼” 보이면서, L1 gate를 우회할 가능성이 생깁니다.

권장 구조

신규 경로는 기존 builder와 분리하는 것이 좋습니다.

예시:

src/l2/intake/
  __init__.py
  contract.py
  manifest.py
  validate.py

scripts/
  validate_l2_intake_contract.py

tests/
  test_l2_intake_contract.py
  test_l2_legacy_quarantine.py

단, local src/l2/__init__.py 자체가 broken import를 유발한다면 Codex는 다음 중 하나를 선택해야 합니다.

src/l2/__init__.py에서 side-effect import 제거

또는 임시로 src/l2_intake/ 별도 package 사용 후, 추후 정식 src/l2/로 이전

둘 중 무엇을 택하든 핵심은 같습니다.

TASK-4136의 신규 L2 intake path는 legacy news builder를 절대 import하지 않는다.

6. 지금 명시적으로 만들면 안 되는 것

현재 상태에서 아래는 모두 금지해야 합니다.

만들면 안 되는 것	이유
L2 trading feature store	L1→L2 contract가 아직 고정되지 않음
news sentiment score	public news/context는 context-only 또는 discovery-only
newswire 기반 종목 점수화	newswire는 L2_REVIEW_QUEUE_ONLY_NOT_FEATURE
macro regime score	macro/context는 아직 trading feature가 아님
L3 signal 연결	L2 primitive contract 검증 전 premature
entry/exit/sizing/order intent	hard state상 real/paper promotion 금지
strategy acceptance 변경	Strategy는 여전히 NOT_ACCEPTED
deployment readiness 승격	Deployment는 DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
paper/live broker mutation	명시적으로 금지
microstructure alpha	5m builder가 비어 있고 row volume이 큼
missing data imputation	missing/stale은 UNKNOWN/BLOCKER
L0 raw news direct ingest	legacy bypass 재발
legacy L2 news builder 광범위 수리	import 통과와 의미론적 안전성은 다름

특히 뉴스 쪽은 조심해야 합니다.
현재 handoff상 public newswire는 discovery-only입니다. 즉, “후보 검토 큐에 올릴 수는 있지만, feature나 signal로 쓰면 안 되는 상태”입니다.

7. Codex-executable TASK-4136 plan

아래는 Codex에게 바로 줄 수 있는 작업 명세서입니다.

TASK-4136 — L2 Intake Contract & Gate Validator
Objective

Implement the first minimal L2 layer as an intake contract and validator only.

This task must not create production L2 primitive materialization, trading features, scores, signals, rankings, policy actions, paper orders, live orders, broker mutations, or strategy/deployment promotion.

Source of truth

Use only local worktree files and local TASK-4135 artifacts.

Do not use GitHub.

If a required local artifact path is ambiguous, inspect local files and provide local excerpts or local path inventory. Do not infer from GitHub.

Hard boundaries

Keep the following states unchanged:

Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
No broker mutation
No live order
No paper promotion
Missing/stale data is UNKNOWN/BLOCKER, never negative evidence
Scope
1. Add L2 intake contract

Create a contract artifact equivalent to:

configs/l2_intake_contract.yaml

or, if config directory conventions differ locally, place it under the existing local config/artifact convention and document the path.

The contract must include all five current source families:

daily_bars
market_bars_5m
public_context_news_feeds
public_market_macro_news_feeds
public_newswire_feeds

The mapping must match:

Source family	Required L1 class	Required L2 allowed use
daily_bars	STRICT_SOURCE_TIME_CERTIFIED	L2_PRIMITIVE_INPUT_ALLOWED_MARKET_OBSERVATION_ONLY
market_bars_5m	STRICT_SOURCE_TIME_CERTIFIED	L2_PRIMITIVE_INPUT_ALLOWED_MARKET_OBSERVATION_ONLY
public_context_news_feeds	CONTEXT_ONLY_CERTIFIED	L2_CONTEXT_INPUT_ALLOWED_NOT_TRADING_FEATURE
public_market_macro_news_feeds	CONTEXT_ONLY_CERTIFIED	L2_CONTEXT_INPUT_ALLOWED_NOT_TRADING_FEATURE
public_newswire_feeds	DISCOVERY_ONLY	L2_REVIEW_QUEUE_ONLY_NOT_FEATURE

All five must have:

feature_materialization_allowed = false
trading_authority_opened = false
missing_source_is_negative_allowed = false
future_outcome_assignment_allowed = false
2. Add isolated L2 intake package

Preferred path:

src/l2/intake/
  __init__.py
  contract.py
  manifest.py
  validate.py

If local src/l2/__init__.py or package import behavior triggers broken legacy imports, use this fallback:

src/l2_intake/
  __init__.py
  contract.py
  manifest.py
  validate.py

Do not import:

src/l2/builders/news_event_primitives.py

Do not create semantic stubs for missing legacy modules such as:

src.l2.contracts
freshness
lineage
runtime_context
news_runtime

unless they are fully implemented according to the new L2 intake contract. Import-only dummy modules are not allowed.

3. Generate L2 intake manifest

Create:

data/artifacts/task_4136_l2_intake_contract/l2_intake_manifest.csv
data/artifacts/task_4136_l2_intake_contract/l2_intake_manifest.jsonl

The manifest should contain one row per accepted L1 packet/source family, not one row per market bar.

Minimum columns:

task_id
l2_intake_id
source_family
source_packet_id
candidate_id
symbol
decision_asof_ts
source_ts
available_to_brain_ts
l1_classification
l2_allowed_use
primitive_envelope_type
l2_materialization_state
l2_block_status
block_reason
raw_path
raw_sha256
authority

For TASK-4136, l2_materialization_state must be:

INTAKE_ONLY_NOT_MATERIALIZED

No OHLCV primitive rows, news primitive rows, sentiment rows, regime rows, or trading feature rows should be written.

4. Add validator script

Create:

scripts/validate_l2_intake_contract.py

The script should accept local artifact paths as CLI inputs rather than hardcoding TASK-4135 paths.

Required inputs:

--l1-packets
--coverage-snapshot
--handoff-contract
--output-dir

If the local TASK-4135 artifacts use different names, Codex should adapt the parser but keep the semantic validation unchanged.

The validator must produce:

data/artifacts/task_4136_l2_intake_contract/l2_intake_validation_report.json
data/artifacts/task_4136_l2_intake_contract/l2_intake_validation_report.md
5. Required validator checks

Implement hard-fail checks for:

required_l1_columns_present
all_expected_source_families_present
no_unexpected_source_family_without_contract
no_BLOCKED_classification
handoff_classification_matches_allowed_use
source_time_order_valid
strict_market_sources_are_source_time_certified
raw_path_present
raw_sha256_present
missing_source_is_negative_is_false
assignment_uses_future_outcome_is_false
outcome_used_for_assignment_is_false
trading_authority_opened_is_false
no_broker_mutation_fields
no_order_intent_fields
no_l0_direct_to_l2_news_ingest
legacy_news_builder_not_imported

For source-time ordering, enforce:

source_ts <= available_to_brain_ts <= decision_asof_ts

If any timestamp is missing, mark the row as blocked unless the contract explicitly permits null for that source family. For current TASK-4136, do not silently permit null timestamps.

6. Add stale/gap policy hook

Add a small stale policy config, but do not overfit.

Suggested artifact:

configs/l2_staleness_policy.yaml

Minimum fields:

YAML
version: 1
mode: diagnostic_contract_only
missing_data_policy: UNKNOWN_BLOCKER_NEVER_NEGATIVE
families:
  daily_bars:
    stale_policy_required: true
  market_bars_5m:
    stale_policy_required: true
  public_context_news_feeds:
    stale_policy_required: true
  public_market_macro_news_feeds:
    stale_policy_required: true
  public_newswire_feeds:
    stale_policy_required: true

The validator should require that a stale policy exists for each family, but TASK-4136 does not need to implement exchange-calendar-level freshness logic yet.

If the existing L1 artifacts already include stale/gap status, consume that status.
If they do not, report:

BLOCKED_STALENESS_POLICY_NOT_ENFORCEABLE

rather than assuming freshness.

7. Legacy L2 surface audit

Create:

data/artifacts/task_4136_l2_intake_contract/legacy_l2_surface_audit.md

It should document:

- existing src/l2/builders/news_event_primitives.py status
- missing/broken imports observed locally
- whether TASK-4136 imports it: must be false
- whether legacy direct L0-to-L2 news ingest remains blocked: must be true
- recommendation: quarantine until rewritten against new intake contract

Do not repair the legacy builder in this task.

8. Tests

Add tests:

tests/test_l2_intake_contract.py
tests/test_l2_legacy_quarantine.py

Minimum test cases:

Test	Expected
daily bars strict class maps to market observation only	PASS
5m bars strict class maps to market observation only	PASS
context news cannot become feature	FAIL if feature attempted
macro/context cannot become feature	FAIL if feature attempted
newswire cannot become feature	FAIL if feature attempted
newswire can only become review queue reference	PASS
BLOCKED classification blocks intake	PASS
missing raw hash blocks intake	PASS
future outcome assignment blocks intake	PASS
missing source as negative blocks intake	PASS
legacy news builder imported by new path	FAIL
9. Validation commands

Codex should run at minimum:

Bash
python -m py_compile scripts/validate_l2_intake_contract.py
python -m unittest tests.test_l2_intake_contract
python -m unittest tests.test_l2_legacy_quarantine

Then run the validator using the actual local TASK-4135 artifact paths:

Bash
python scripts/validate_l2_intake_contract.py \
  --l1-packets <LOCAL_TASK_4135_L1_PACKET_PATH> \
  --coverage-snapshot <LOCAL_TASK_4135_COVERAGE_SNAPSHOT_PATH> \
  --handoff-contract <LOCAL_TASK_4135_HANDOFF_CONTRACT_PATH> \
  --output-dir data/artifacts/task_4136_l2_intake_contract

If any input path is missing, the validator must produce a BLOCKED report rather than fabricating input rows.

10. Acceptance criteria

TASK-4136 is accepted only if all are true:

- 5 expected source families are represented.
- 0 unexpected source families are admitted.
- 0 BLOCKED_* L1 classifications are admitted.
- daily_bars and market_bars_5m are allowed only as market observation primitive envelopes.
- public_context_news_feeds and public_market_macro_news_feeds are context-only, not features.
- public_newswire_feeds is review-queue-only, not feature.
- no L2 feature materialization is written.
- no signal, score, rank, alpha, label, return target, expected return, sizing, order intent, or policy action is written.
- no broker mutation path is touched.
- no paper/live promotion occurs.
- legacy L2 news builder is not imported by the new TASK-4136 path.
- validator emits PASS/BLOCKED with explicit reasons.
- artifact manifest is written.
Recommended next sequence after TASK-4136
Next task	Scope	GO condition
TASK-4137	daily_bars → DAILY_MARKET_OBSERVATION primitive v0	TASK-4136 validator PASS
TASK-4138	market_bars_5m intake sample/partition validator	daily primitive path stable
TASK-4139	macro/context reference envelope only	context cannot become feature
TASK-4140	public newswire review queue only	discovery-only guard proven
Later	L3 feature derivation	L2 lineage/asof/allowed-use proven stable

My strongest recommendation is: TASK-4136에서 L2를 “많이 만들지 말고”, L2가 절대 잘못된 것을 받지 못하게 만드는 validator를 먼저 완성하는 것입니다. 지금 프로젝트의 가장 큰 위험은 데이터 부족이 아니라, context/discovery/news가 너무 일찍 feature나 signal로 승격되는 것입니다.
