TASK-4143 L2 Completion Review

역할: 너는 Stock-Investment 프로젝트의 L2 데이터/퀀트 인프라 검수 패널이다.
모드: Pro 확장 추론으로 답하라.
중요: GitHub를 읽지 마라. 현재 GitHub에는 최신 로컬 작업본이 반영되어 있지 않다. 아래에 붙이는 로컬 현황만 기준으로 판단하라.

사용자 목표:
남은 L2 작업들을 현재 데이터/현황 기준으로 검수받고, 과도하게 보수적인 작업이나 코드-for-code는 컷한 뒤, 실효성 있는 L2를 완성하려 한다.

하드 경계:
- Strategy = NOT_ACCEPTED
- Deployment = DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital = FORBIDDEN
- broker mutation 금지
- live order 금지
- paper promotion 금지
- missing/stale data는 부정 증거가 아니라 UNKNOWN/BLOCKER 또는 archive/context
- L2는 signal/score/ranking/return/order를 만들면 안 된다

현재 로컬 상태 요약:
1. TASK-4136 L2 intake
- feature_candidate_rows = 5
- l2_intake_rows = 5
- news_macro_feature_path_rows = 3
- feature_admitted_now = 0
- l2_materialization_written = false
- legacy_l2_news_quarantined = true
- trading_authority_opened = false

2. TASK-4140 swing news/macro/newswire posture
- 평균 보유기간 약 1개월 스윙 전략
- 뉴스/매크로/뉴스와이어는 swing/daily feature candidate가 맞다
- 분/초 timestamp는 필수 조건이 아니다
- daily publication date는 충분할 수 있다
- activation_policy = NEXT_TRADING_SESSION_OR_NEXT_DAILY_DECISION
- primary_effect_window = 20D
- secondary_effect_windows = 1D, 5D, 60D
- feature materialization은 아직 닫혀 있다

3. TASK-4142 L2 swing event admission view 최신 수정 후 결과
- input_rows = 3
- admitted_rows = 2
- review_rows = 1
- blocked_rows = 0
- mapping_issue_rows = 1
- dedup_clusters = 3
- feature_materialization_allowed_rows = 0
- trading_authority_opened_rows = 0
- paper_live_broker_order_opened_rows = 0
- source families: public_context_news_feeds, public_market_macro_news_feeds, public_newswire_feeds
- 2개 historical macro/context row는 ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE + ARCHIVE_CONTEXT_ONLY
- 1개 newswire row는 MAPPING_REVIEW_REQUIRED_NOT_FEATURE + PENDING_NEXT_DAILY_DECISION
- UNKNOWN mapping은 hard block이 아니라 mapping review로 분리했다
- stale historical row는 hard block이 아니라 archive/context로 분리했다

4. L0/L1 데이터 현황
- L0 backfill/orchestration에는 훨씬 많은 진행 단위가 있다.
- latest orchestration snapshot 예시:
  - daily: 99.37% running
  - five_min: 5.69% running
  - public_context_news_backfill: 55.70% running
  - public_newswire_backfill: 42.96% stopped incomplete, restart recommended
  - public_market_macro_news_backfill: 29.11% stopped incomplete, restart recommended
- raw_cache_source_time_audit bounded sample: 각 source family 10 rows 수준
- 현재 TASK-4133 L1 normalized source packet sample은 public_context/newswire/market_macro 각각 1 row만 L2에 들어갔다. 즉 TASK-4142는 아직 bounded sample 기반이다.

현재 L2 산출물/컬럼:
- l2_swing_event_admission_view.csv/jsonl
- l2_mapping_issues.csv
- l2_dedup_clusters.csv
- l2_block_reason_summary.csv
- l2_family_count_summary.csv
- 핵심 컬럼: source_packet_id, raw_path, raw_sha256, source_ts, available_to_brain_ts, decision_asof_ts, publication_time_precision, is_publication_time_imputed, mapping_scope/key, symbol/entity/sector/macro key, dedup_key, event_cluster_id, canonical flag, event_domain/type/topic_tags, primary/secondary effect windows, stale_status, admission_status, l3_read_allowed, feature_materialization_allowed, trading_authority_opened.

내가 보기에 남은 후보 작업:
A. L2 입력 범위를 TASK-4133 샘플 3개에서 실제 L0/L1 available raw/cache/status 기반의 bounded-but-broader packet/view로 확장
B. L3 read contract 산출: L3가 읽어도 되는 컬럼만 별도 view/sample로 분리
C. mapping review queue 고도화: UNKNOWN을 줄이기 위한 deterministic ticker/entity/sector/macro 후보 추출. 단, LLM sentiment/강제 ticker 추정 금지
D. dedup QA 고도화: source_url/title/hash/provider/date 기반 canonical/duplicate/review 상태 강화. embedding/LLM semantic clustering은 아직 금지 또는 후순위
E. stale/effect-window policy를 명확히: active/review/archive/context를 분리. stale을 부정 증거로 쓰지 않음
F. validator 상시화: L2 validator가 legacy builder/direct L0-L2/news score/order/return/ranking 컬럼을 계속 막도록 함
G. L2 완료 보고: 사람이 봐도 rows/counts/block/review/archive/mapping/dedup 상태가 이해되는 QA report

질문:
1. 위 후보 중 L2 완성에 반드시 필요한 것과, 과도하게 보수적이거나 지금 하면 안 되는 것을 나눠라.
2. “완벽한 L2”를 이 프로젝트 맥락에서 어떻게 정의해야 하나? 단, L3/L4/backtest/signal로 넘어가면 안 된다.
3. Codex가 지금 바로 구현해야 할 최소-충분 작업 세트를 5개 이하로 정리하라.
4. 각 작업별 산출물과 validator 체크를 구체적으로 써라.
5. 과도한 구현은 컷 표시를 해라. 예: LLM sentiment, embedding dedup, full entity resolution system, DB schema migration, return/alpha 계산 등.

출력은 한국어, 쉬운 표현, 표 중심으로 하라.
