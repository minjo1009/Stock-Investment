## 핵심 세 줄 요약

* **현재 L2는 방향은 맞지만, 3개 샘플 기반이라 “완성”은 아직 아닙니다.** 지금은 PoC/초기 admission view 통과 수준입니다.
* **L2 완성의 기준은 signal이 아니라, L1을 통과한 뉴스/매크로/뉴스와이어를 L3가 안전하게 읽을 수 있는 admission/read view로 정리하는 것입니다.**
* **지금 Codex가 할 일은 5개 이하로 줄이면 됩니다: 입력 범위 확장, L3 read view, mapping queue, dedup+stale/window, hard validator+QA report.**

---

# 1. 결론

## 현재 판정

| 항목                              |                                          현재 상태 | 판정                       |
| ------------------------------- | ---------------------------------------------: | ------------------------ |
| TASK-4136 L2 intake             | 5 rows, legacy quarantined, materialization 없음 | **PASS**                 |
| TASK-4140 swing posture         |               뉴스/매크로/뉴스와이어를 swing/daily 후보로 인정 | **PASS**                 |
| TASK-4142 admission view        |       input 3, admitted 2, review 1, blocked 0 | **구조 PASS / 범위 PARTIAL** |
| feature materialization         |                                         0 rows | **PASS**                 |
| trading/paper/live/broker/order |                                         0 rows | **PASS**                 |
| L2 완료 여부                        |                           3개 bounded sample 기반 | **NOT COMPLETE**         |

**핵심 판단:**
현재 L2는 **개념과 방향은 맞습니다.** 특히 `UNKNOWN mapping`을 무조건 hard block으로 삭제하지 않고 `mapping review`로 분리한 것, stale historical row를 부정 증거로 쓰지 않고 `archive/context`로 분리한 것은 실무적으로 맞습니다.

다만 **입력 row가 3개뿐**이므로, 이것을 “L2 완성”이라고 부르면 안 됩니다.
정확히는 다음 상태입니다.

> **L2 admission design은 통과.
> L2 completion은 아직 sample-scope 부족으로 미완성.**

---

# 2. 후보 작업 분류

## A~G 판정

| 후보                                    | 필요성 |    지금 할지 | 판단                                                   |
| ------------------------------------- | --: | -------: | ---------------------------------------------------- |
| **A. L2 입력 범위 확장**                    |  필수 | **해야 함** | 단, L0 raw 직접 ingest 금지. 반드시 L1 packet/handoff를 통해 확장 |
| **B. L3 read contract 산출**            |  필수 | **해야 함** | L3가 읽어도 되는 컬럼만 분리해야 L2 경계가 선명해짐                      |
| **C. mapping review queue 고도화**       |  필수 | **해야 함** | UNKNOWN을 줄이되, 강제 ticker 추정은 금지                       |
| **D. dedup QA 고도화**                   |  필수 | **해야 함** | 중복 뉴스가 신호 강도처럼 보이는 것을 막아야 함                          |
| **E. stale/effect-window policy 명확화** |  필수 | **해야 함** | 1개월 스윙 전략에서는 active/archive/context 구분이 중요           |
| **F. validator 상시화**                  |  필수 | **해야 함** | legacy/direct L0-L2/score/return/order를 계속 차단해야 함    |
| **G. L2 완료 QA report**                |  필수 | **해야 함** | 사람이 rows/counts/review/archive 상태를 이해할 수 있어야 함       |

**정리하면 A~G는 방향 자체는 모두 필요합니다.**
다만 각각을 크게 만들면 과합니다. 지금은 **작고 검증 가능한 산출물**로 구현해야 합니다.

---

## 과도하게 보수적인 것과 컷해야 할 것

| 항목                                  | 판정           | 이유                                                       |
| ----------------------------------- | ------------ | -------------------------------------------------------- |
| 전체 L0 backfill 100% 완료 전까지 L2 금지    | **CUT**      | L2는 available L1-gated rows로 bounded view를 만들 수 있음       |
| 모든 뉴스에 분/초 timestamp 요구             | **CUT**      | 1개월 스윙 전략에서는 daily publication date도 충분할 수 있음            |
| stale historical row를 전부 hard block | **CUT**      | stale은 부정 증거가 아니라 archive/context로 보존 가능                 |
| UNKNOWN mapping row를 삭제             | **CUT**      | feature admission은 막되 review queue에는 남겨야 함               |
| 5m bar 완료 전 뉴스 L2 금지                | **CUT**      | 뉴스/매크로 L2와 5m microstructure는 별개                         |
| full DB schema migration            | **CUT**      | 현재 dirty worktree가 크므로 artifact-first가 맞음                |
| LLM sentiment                       | **CUT**      | L2 책임이 아님                                                |
| embedding dedup                     | **CUT**      | deterministic dedup으로 충분히 시작 가능                          |
| full entity resolution system       | **CUT**      | 지금은 deterministic candidate extraction + review queue까지만 |
| return/alpha/impact 계산              | **HARD CUT** | L2 금지 영역                                                 |
| ranking/signal/order intent         | **HARD CUT** | hard boundary 위반                                         |
| broad cleanup/delete/restore        | **CUT**      | TASK-4139상 dirty rows가 많아 위험                             |

---

# 3. “완벽한 L2”의 정의

이 프로젝트에서 **완벽한 L2**는 “좋은 매매 신호를 만드는 층”이 아닙니다.

정의는 아래가 맞습니다.

> **L1이 허용한 source packet을 받아서, L3가 안전하게 연구용으로 읽을 수 있는 event primitive / admission / read view를 제공하는 층.**

## L2 완성 기준

| 구분            | 완성 기준                                                        |
| ------------- | ------------------------------------------------------------ |
| 입력            | L0 raw 직접 ingest 없음. 반드시 L1 packet/handoff 기반                |
| 범위            | news/context, market macro, newswire 3개 source family 모두 포함  |
| row 상태        | admitted / review / archive / duplicate / blocked가 명확히 분리    |
| mapping       | TICKER / ENTITY / SECTOR / MACRO / UNKNOWN 구분                |
| UNKNOWN       | feature admission 금지, review queue 허용                        |
| dedup         | canonical event와 duplicate member 분리                         |
| stale         | active / secondary / archive / stale-block 구분                |
| effect window | 1D / 5D / 20D / 60D window 선언                                |
| L3 read       | L3가 읽어도 되는 컬럼만 별도 view로 제공                                   |
| safety        | score, signal, return, ranking, order, broker, paper/live 없음 |
| QA            | 사람이 볼 수 있는 count/report 존재                                   |

---

## L2 완성이 의미하지 않는 것

| 오해                          | 실제 기준                                     |
| --------------------------- | ----------------------------------------- |
| L2가 종목 점수를 만든다              | 아님. 점수는 아직 금지                             |
| L2가 뉴스 감성을 판정한다             | 아님. sentiment는 후순위                        |
| L2가 forward return을 계산한다    | 아님. L2 leakage                            |
| L2가 L3/L4 signal을 만든다       | 아님. L2는 read/admission layer              |
| L2가 full production DB를 만든다 | 아님. 지금은 artifact-first                    |
| L2가 모든 raw를 다 처리해야 완성이다     | 아님. bounded but broader L1-gated view면 충분 |

---

# 4. 지금 바로 구현할 최소-충분 작업 세트

## 전체 순서

| 순서 | 작업명                                          | 목적                                                 |
| -: | -------------------------------------------- | -------------------------------------------------- |
|  1 | **Bounded L1-to-L2 Input Expansion**         | 3개 샘플에서 벗어나되 L1을 우회하지 않음                           |
|  2 | **L3 Read Contract / Read View**             | L3가 읽어도 되는 컬럼만 분리                                  |
|  3 | **Mapping Review Queue v1**                  | UNKNOWN/ambiguous row를 feature가 아닌 review로 관리      |
|  4 | **Dedup + Stale/Effect Window Policy v1**    | 중복, archive, active window를 명확화                    |
|  5 | **L2 Hard Validator + Completion QA Report** | forbidden path/column/action 상시 차단 및 사람이 보는 보고서 생성 |

이 5개면 충분합니다.
이 이상으로 sentiment, embedding, DB migration, return 계산까지 가면 과합니다.

---

# 5. 작업별 산출물과 validator 체크

## 작업 1. Bounded L1-to-L2 Input Expansion

### 목적

현재 TASK-4142는 source family별 1 row, 총 3 row만 들어갔습니다.
다음 단계에서는 **bounded-but-broader** 입력으로 확장해야 합니다.

단, 중요한 조건이 있습니다.

> L2가 L0 raw/cache를 직접 읽어 L2 row를 만들면 안 됩니다.
> 확장은 반드시 L1 normalized packet 또는 L1-to-L2 handoff artifact를 통해 해야 합니다.

### 산출물

| 산출물                                            | 설명                                                      |
| ---------------------------------------------- | ------------------------------------------------------- |
| `l2_input_scope_audit.csv`                     | source family별 raw/backfill 상태, L1 packet 수, L2 input 수 |
| `l2_input_scope_audit.md`                      | 왜 이 범위까지 처리했는지 사람용 설명                                   |
| `l2_swing_event_admission_view_expanded.csv`   | 확장된 L2 admission view                                   |
| `l2_swing_event_admission_view_expanded.jsonl` | 동일 JSONL                                                |
| `l2_family_count_summary.csv`                  | family별 input/admitted/review/archive/blocked count     |

### validator 체크

| 체크                                     | 기대값                          |
| -------------------------------------- | ---------------------------- |
| L2 row마다 `source_packet_id` 존재         | PASS                         |
| L2 row마다 `raw_path`, `raw_sha256` 존재   | PASS                         |
| L1 gate 통과 정보 존재                       | PASS                         |
| source family 3개 모두 포함                 | PASS 또는 명시적 no-data/block 사유 |
| L0 raw direct ingest 사용                | FAIL                         |
| L1 packet 없는 row 생성                    | FAIL                         |
| input 3 rows만으로 completion claim       | FAIL                         |
| L0 backfill 미완료를 negative evidence로 처리 | FAIL                         |

### 구현 기준

| 항목                | 기준                                                  |
| ----------------- | --------------------------------------------------- |
| 입력 범위             | source family별 configurable limit                   |
| 기본 추천             | family별 50~500 rows 또는 local L1 packet available 범위 |
| L1 packet이 부족한 경우 | `BLOCKED_L1_PACKET_SCOPE_TOO_NARROW` 보고             |
| 전체 backfill 강제    | 금지                                                  |

---

## 작업 2. L3 Read Contract / Read View

### 목적

L2 admission view 전체를 L3가 그대로 읽으면 위험합니다.
L3가 읽어도 되는 컬럼만 별도 view로 분리해야 합니다.

### 산출물

| 산출물                                             | 설명                 |
| ----------------------------------------------- | ------------------ |
| `l2_to_l3_swing_event_read_contract.yaml`       | L3 허용 컬럼 whitelist |
| `l2_to_l3_swing_event_read_view.csv`            | L3 연구용 read view   |
| `l2_to_l3_swing_event_read_view.jsonl`          | 동일 JSONL           |
| `l2_to_l3_read_contract_validation_report.json` | validator 결과       |
| `l2_to_l3_read_contract_validation_report.md`   | 사람용 설명             |

### L3에 허용 가능한 컬럼

| 그룹            | 허용 컬럼 예시                                                                                                    |
| ------------- | ----------------------------------------------------------------------------------------------------------- |
| event id      | `l2_event_id`, `event_cluster_id`                                                                           |
| source trace  | `source_packet_id`, `source_family`, `provider`, `raw_sha256`                                               |
| time          | `publication_date`, `publication_time_precision`, `is_publication_time_imputed`, `activation_decision_date` |
| mapping       | `mapping_scope`, `mapping_key`, `symbol`, `entity_key`, `sector_key`, `macro_key`                           |
| event meaning | `event_domain`, `event_type`, `topic_tags`                                                                  |
| dedup         | `is_canonical_event`, `dedup_status`, `cluster_member_count`                                                |
| stale/window  | `stale_status`, `primary_effect_window`, `secondary_effect_windows`                                         |
| admission     | `admission_status`, `l3_read_mode`                                                                          |

### L3에 금지할 컬럼

| 금지 컬럼 패턴            | 이유                              |
| ------------------- | ------------------------------- |
| `return_*`          | forward/realized return leakage |
| `alpha_*`           | signal 영역                       |
| `score_*`           | L2 점수화 금지                       |
| `rank_*`            | ranking 금지                      |
| `signal_*`          | L2 책임 아님                        |
| `target_*`          | label/target leakage 위험         |
| `pnl_*`             | outcome 정보                      |
| `order_*`           | hard boundary 위반                |
| `broker_*`          | hard boundary 위반                |
| `paper_*`, `live_*` | promotion 금지                    |

### validator 체크

| 체크                                          | 기대값  |
| ------------------------------------------- | ---- |
| read contract에 whitelist 존재                 | PASS |
| L3 read view가 whitelist 컬럼만 포함              | PASS |
| blocked/review row가 active L3 candidate로 노출 | FAIL |
| duplicate non-canonical row가 독립 event로 노출   | FAIL |
| return/alpha/score/rank/order 컬럼 존재         | FAIL |
| feature materialization allowed true        | FAIL |

---

## 작업 3. Mapping Review Queue v1

### 목적

현재 `UNKNOWN mapping` 1 row가 review로 분리된 것은 맞습니다.
다음은 UNKNOWN을 줄이기 위한 **deterministic 후보 추출**입니다.

단, 강제 매핑은 금지입니다.

### 산출물

| 산출물                                 | 설명                                  |
| ----------------------------------- | ----------------------------------- |
| `l2_mapping_review_queue.csv`       | UNKNOWN/ambiguous mapping 검토 큐      |
| `l2_mapping_candidates.csv`         | deterministic 후보                    |
| `l2_mapping_rules.yaml`             | ticker/entity/sector/macro 후보 추출 규칙 |
| `l2_mapping_issues.csv`             | 기존 mapping issue 확장                 |
| `l2_mapping_validation_report.json` | validator 결과                        |
| `l2_mapping_validation_report.md`   | 사람용 설명                              |

### mapping 상태값

| 상태                                    | 의미            |
| ------------------------------------- | ------------- |
| `MAPPED_TICKER`                       | ticker 확정     |
| `MAPPED_ENTITY`                       | entity 확정     |
| `MAPPED_SECTOR`                       | sector 확정     |
| `MAPPED_MACRO`                        | macro 확정      |
| `MAPPING_REVIEW_REQUIRED_NOT_FEATURE` | 후보는 있으나 확정 불가 |
| `BLOCKED_UNKNOWN_MAPPING_NOT_FEATURE` | 후보도 불충분       |
| `AMBIGUOUS_REVIEW_NOT_FEATURE`        | 여러 후보가 충돌     |

### validator 체크

| 체크                                | 기대값  |
| --------------------------------- | ---- |
| mapping_scope enum 유효             | PASS |
| UNKNOWN이 feature admission으로 들어감  | FAIL |
| UNKNOWN이 review queue로 들어감        | PASS |
| ticker 강제 추정                      | FAIL |
| entity를 ticker로 자동 승격             | FAIL |
| sector event를 개별 ticker에 자동 배분    | FAIL |
| macro event를 개별 ticker signal로 변환 | FAIL |
| mapping rule이 deterministic하지 않음  | FAIL |

### 컷할 구현

| 구현                            | 판정      |
| ----------------------------- | ------- |
| LLM entity extraction         | **CUT** |
| full entity resolution system | **CUT** |
| 모든 company alias 사전 구축        | **CUT** |
| ticker 강제 추론                  | **CUT** |
| sector-to-ticker 자동 확산        | **CUT** |

---

## 작업 4. Dedup + Stale/Effect Window Policy v1

### 목적

뉴스/매크로/뉴스와이어는 중복과 stale 처리가 중요합니다.
특히 한 달 스윙 전략에서는 같은 이벤트가 여러 소스에 반복 노출될 수 있으므로, dedup을 하지 않으면 뉴스량이 신호처럼 보입니다.

### 산출물

| 산출물                                        | 설명                              |
| ------------------------------------------ | ------------------------------- |
| `l2_dedup_rules.yaml`                      | deterministic dedup key 규칙      |
| `l2_dedup_clusters.csv`                    | cluster별 canonical/duplicate 상태 |
| `l2_canonical_events.csv`                  | canonical event만 모은 view        |
| `l2_duplicate_members.csv`                 | duplicate member lineage 보존     |
| `l2_swing_stale_effect_window_policy.yaml` | stale/effect window 정책          |
| `l2_stale_effect_window_report.csv`        | row별 stale/window 결과            |
| `l2_dedup_stale_validation_report.json`    | validator 결과                    |
| `l2_dedup_stale_validation_report.md`      | 사람용 설명                          |

### dedup 기준

| 항목            | 기준                                                                     |
| ------------- | ---------------------------------------------------------------------- |
| 기본 key        | date + mapping_scope + mapping_key + event_type + normalized_title_key |
| newswire      | same day 또는 1 trading day dedup                                        |
| context news  | 1~3 trading days dedup                                                 |
| macro news    | series/period/release date 기준                                          |
| canonical row | L1 gate 완전성, source time 명확성, raw hash 존재, earliest available 기준       |
| duplicate row | 삭제하지 않고 member로 보존                                                     |

### stale/effect window 기준

| 상태                                  | 기준                                    |
| ----------------------------------- | ------------------------------------- |
| `ACTIVE_PRIMARY`                    | activation date 이후 20 trading days 이내 |
| `ACTIVE_SECONDARY`                  | 21~60 trading days                    |
| `ARCHIVE_CONTEXT_ONLY`              | feature 후보는 아니지만 과거 맥락으로 보존           |
| `STALE_BLOCKED_NOT_NEGATIVE`        | 너무 오래되어 feature timing 부적합            |
| `BLOCKED_NO_VALID_PUBLICATION_DATE` | 날짜 불충분                                |
| `BLOCKED_MONTH_OR_YEAR_ONLY_TIMING` | month/year-only timing                |

### effect window

| window | L2에서 할 일                     |
| ------ | ---------------------------- |
| `1D`   | window 선언만                   |
| `5D`   | window 선언만                   |
| `20D`  | primary window 선언            |
| `60D`  | secondary/extended window 선언 |

L2는 window를 **선언**만 합니다.
L2가 수익률을 계산하면 안 됩니다.

### validator 체크

| 체크                                          | 기대값  |
| ------------------------------------------- | ---- |
| canonical event가 cluster당 1개 이하             | PASS |
| duplicate row가 L3 active candidate로 노출      | FAIL |
| duplicate count가 score로 사용                  | FAIL |
| stale row가 negative evidence로 사용            | FAIL |
| day-level date 허용                           | PASS |
| imputed nominal time 표시                     | PASS |
| month/year-only timing이 active feature로 들어감 | FAIL |
| 1D/5D/20D/60D realized return 계산            | FAIL |

### 컷할 구현

| 구현                          | 판정           |
| --------------------------- | ------------ |
| embedding dedup             | **CUT**      |
| LLM semantic clustering     | **CUT**      |
| article similarity model    | **CUT**      |
| return-based event impact   | **HARD CUT** |
| news volume intensity score | **CUT**      |

---

## 작업 5. L2 Hard Validator + Completion QA Report

### 목적

L2가 완료되려면 산출물만 있으면 안 됩니다.
계속 깨지지 않도록 validator와 사람이 읽는 QA report가 있어야 합니다.

### 산출물

| 산출물                                        | 설명                              |
| ------------------------------------------ | ------------------------------- |
| `scripts/validate_l2_swing_event_layer.py` | 통합 validator                    |
| `l2_completion_validation_report.json`     | 기계 검증 결과                        |
| `l2_completion_validation_report.md`       | 사람용 검증 보고서                      |
| `l2_block_reason_summary.csv`              | block/review/archive 이유 요약      |
| `l2_family_count_summary.csv`              | source family별 count            |
| `l2_mapping_scope_summary.csv`             | mapping scope별 count            |
| `l2_dedup_summary.csv`                     | dedup/canonical/duplicate count |
| `l2_stale_status_summary.csv`              | stale/window 상태 요약              |
| `l2_sample_admitted_rows.md`               | 대표 admitted row                 |
| `l2_sample_review_rows.md`                 | 대표 review row                   |
| `l2_sample_archive_rows.md`                | 대표 archive/context row          |
| `artifact_manifest.csv`                    | 산출물 목록                          |

### hard validator 체크

| 체크                                          | 기대값  |
| ------------------------------------------- | ---- |
| legacy L2 news builder import 없음            | PASS |
| direct L0-to-L2 news path 없음                | PASS |
| L1 lineage 없는 row 없음                        | PASS |
| raw_path/raw_sha256 없는 row 없음               | PASS |
| feature_materialization_allowed = false     | PASS |
| trading_authority_opened = false            | PASS |
| broker/live/paper/order 관련 row 없음           | PASS |
| return/alpha/score/rank/signal 컬럼 없음        | PASS |
| future outcome assignment 없음                | PASS |
| missing/stale negative evidence 없음          | PASS |
| UNKNOWN mapping active feature admission 없음 | PASS |
| duplicate non-canonical L3 active read 없음   | PASS |
| imputed timestamp가 actual로 취급되지 않음          | PASS |

---

# 6. 현재 TASK-4142 결과에 대한 세부 의견

## 좋은 점

| 항목                                         | 평가       |
| ------------------------------------------ | -------- |
| `feature_materialization_allowed_rows = 0` | 좋음       |
| `trading_authority_opened_rows = 0`        | 좋음       |
| paper/live/broker/order opened rows = 0    | 좋음       |
| legacy L2 news quarantined                 | 좋음       |
| UNKNOWN을 review로 분리                        | 실무적으로 좋음 |
| stale historical을 archive/context로 분리      | 실무적으로 좋음 |
| source family 3개 포함                        | 방향 좋음    |

## 보완할 점

| 항목                                 | 문제                                         | 보완                                     |
| ---------------------------------- | ------------------------------------------ | -------------------------------------- |
| input_rows = 3                     | 너무 작음                                      | bounded-but-broader L1 packet input 필요 |
| admitted_rows = 2가 archive/context | active research 후보와 archive 후보가 섞여 보일 수 있음 | `l3_read_mode` 추가                      |
| blocked_rows = 0                   | 실패는 아니지만 오해 가능                             | block/review/archive/admitted count 분리 |
| mapping_issue_rows = 1             | 정상이나 queue 필요                              | mapping review queue v1                |
| dedup_clusters = 3                 | 샘플이 작아 검증력 낮음                              | 확장 sample에서 dedup QA 필요                |

---

## 추천 상태값 정리

현재처럼 `admission_status` 하나에 모든 의미를 담으면 헷갈릴 수 있습니다.
아래처럼 분리하는 것이 좋습니다.

| 필드                                | 예시                                                                        | 목적            |
| --------------------------------- | ------------------------------------------------------------------------- | ------------- |
| `admission_status`                | `ADMITTED`, `REVIEW_REQUIRED`, `BLOCKED`                                  | L2 입장 상태      |
| `l3_read_mode`                    | `ACTIVE_RESEARCH`, `ARCHIVE_CONTEXT`, `REVIEW_QUEUE_ONLY`, `NOT_READABLE` | L3 읽기 모드      |
| `feature_materialization_allowed` | 항상 false                                                                  | feature 생성 금지 |
| `stale_status`                    | `ACTIVE_PRIMARY`, `ACTIVE_SECONDARY`, `ARCHIVE_CONTEXT_ONLY`              | 시간 상태         |
| `mapping_status`                  | `MAPPED`, `REVIEW_REQUIRED`, `UNKNOWN_BLOCKED`                            | mapping 상태    |

예를 들면:

| 케이스                        | admission_status  | l3_read_mode        | feature_materialization_allowed |
| -------------------------- | ----------------- | ------------------- | ------------------------------- |
| active ticker-mapped event | `ADMITTED`        | `ACTIVE_RESEARCH`   | false                           |
| historical macro row       | `ADMITTED`        | `ARCHIVE_CONTEXT`   | false                           |
| UNKNOWN newswire           | `REVIEW_REQUIRED` | `REVIEW_QUEUE_ONLY` | false                           |
| source-time broken row     | `BLOCKED`         | `NOT_READABLE`      | false                           |

이렇게 하면 “admitted인데 archive” 같은 상태가 더 명확해집니다.

---

# 7. P0/P1 리스크

## P0 리스크

| 리스크                              | 왜 위험한가                     | 검증                                         |
| -------------------------------- | -------------------------- | ------------------------------------------ |
| L0 raw direct ingest             | L1 gate 우회                 | 모든 L2 row에 `source_packet_id` 필수           |
| legacy builder 재유입               | quarantined path가 살아남      | import/static scan                         |
| feature materialization 조기 개방    | L2가 feature layer가 됨       | `feature_materialization_allowed=false` 강제 |
| score/return/ranking 생성          | L2 경계 붕괴 및 leakage         | forbidden column scan                      |
| future outcome 사용                | backtest 오염                | outcome/forward/realized 컬럼 금지             |
| UNKNOWN mapping active admission | 엉뚱한 종목/섹터 연결               | UNKNOWN은 review only                       |
| duplicate 과가중                    | 반복 보도를 강한 신호로 착각           | canonical event만 L3 active                 |
| stale negative evidence          | 데이터 부재/오래됨을 악재로 해석         | stale은 archive/block, never negative       |
| broad cleanup                    | dirty worktree 645 rows 존재 | 신규 좁은 artifact만 생성                         |

---

## P1 리스크

| 리스크                      | 문제                               | 대응                                 |
| ------------------------ | -------------------------------- | ---------------------------------- |
| taxonomy 과복잡             | event type 관리 불가                 | 최소 enum으로 시작                       |
| mapping queue 과대화        | 사람이 볼 수 없음                       | issue reason / candidate reason 요약 |
| dedup false positive     | 다른 이벤트를 하나로 묶음                   | `POSSIBLE_DUPLICATE_REVIEW` 상태     |
| dedup false negative     | 같은 이벤트가 여러 개로 남음                 | cluster count QA                   |
| imputed time 오해          | nominal noon을 실제 시간으로 사용         | `is_publication_time_imputed` 필수   |
| incomplete L0를 부정 증거로 오해 | stopped incomplete가 bearish처럼 쓰임 | coverage limitation report         |
| L3가 review row를 읽음       | 미확정 row가 연구 후보로 섞임               | L3 read mode validator             |
| report가 기계용만 있음          | 사람이 검수 못 함                       | markdown QA 필수                     |

---

# 8. 과도한 구현 컷 목록

| 구현                              | 판정           | 이유                       |
| ------------------------------- | ------------ | ------------------------ |
| LLM sentiment                   | **CUT**      | L2 책임 아님                 |
| LLM bullish/bearish label       | **HARD CUT** | signal/label 영역          |
| embedding dedup                 | **CUT**      | deterministic dedup으로 충분 |
| full entity resolution system   | **CUT**      | 지금은 review queue까지만      |
| DB schema migration             | **CUT**      | artifact-first가 안전       |
| full production materialization | **CUT**      | L0/L1 확장 상태가 아직 불완전      |
| return_1d/5d/20d/60d            | **HARD CUT** | L2 leakage               |
| alpha/event impact score        | **HARD CUT** | L3/L4 이후                 |
| ranking                         | **HARD CUT** | signal layer             |
| order intent                    | **HARD CUT** | hard boundary 위반         |
| paper/live/broker path          | **HARD CUT** | hard boundary 위반         |
| 5m microstructure 결합            | **CUT**      | 현재 L2 뉴스 완성과 무관          |
| broad dirty cleanup             | **CUT**      | TASK-4139상 위험            |

---

# 9. Codex 실행 명세서

아래 정도로 주면 실무적으로 충분합니다.

```text
TASK-4144 — Complete Practical L2 Swing Event Layer

Goal:
Complete L2 for swing news/macro/newswire as an admission/read layer only.
Do not build features, signals, scores, returns, rankings, orders, broker paths, paper/live promotion, or DB migrations.

Use only local worktree state. Do not use GitHub.

Hard state:
- Strategy = NOT_ACCEPTED
- Deployment = DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital = FORBIDDEN
- broker mutation forbidden
- live order forbidden
- paper promotion forbidden
- missing/stale = UNKNOWN/BLOCKER or archive/context, never negative evidence
- L2 must not create signal/score/ranking/return/order

Implement only these 5 work items:

1. Bounded L1-to-L2 Input Expansion
- Expand beyond the current 3-row TASK-4133 sample.
- Consume only L1 normalized packets or L1-to-L2 handoff artifacts.
- Do not directly ingest L0 raw/cache into L2.
- If broader L1 packets are unavailable, emit BLOCKED_L1_PACKET_SCOPE_TOO_NARROW instead of claiming L2 completion.

Outputs:
- l2_input_scope_audit.csv
- l2_input_scope_audit.md
- l2_swing_event_admission_view_expanded.csv
- l2_swing_event_admission_view_expanded.jsonl
- l2_family_count_summary.csv

2. L3 Read Contract / Read View
- Create a whitelist contract for columns L3 may read.
- Create a separate L3 read view.
- Exclude review-only, blocked, duplicate non-canonical rows from active L3 research view.

Outputs:
- l2_to_l3_swing_event_read_contract.yaml
- l2_to_l3_swing_event_read_view.csv
- l2_to_l3_swing_event_read_view.jsonl
- l2_to_l3_read_contract_validation_report.json
- l2_to_l3_read_contract_validation_report.md

3. Mapping Review Queue v1
- Keep mapping scopes: TICKER, ENTITY, SECTOR, MACRO, UNKNOWN.
- UNKNOWN must not become active feature/admission.
- UNKNOWN or ambiguous rows may enter review queue.
- Add deterministic candidate extraction only.
- Do not use LLM sentiment or forced ticker inference.

Outputs:
- l2_mapping_review_queue.csv
- l2_mapping_candidates.csv
- l2_mapping_rules.yaml
- l2_mapping_issues.csv
- l2_mapping_validation_report.json
- l2_mapping_validation_report.md

4. Dedup + Stale/Effect Window Policy v1
- Add deterministic dedup.
- Create canonical event and duplicate member outputs.
- Preserve duplicate lineage.
- Mark stale/archive/context correctly.
- Add 1D, 5D, 20D, 60D effect window declarations only.
- Do not compute realized or forward returns.

Outputs:
- l2_dedup_rules.yaml
- l2_dedup_clusters.csv
- l2_canonical_events.csv
- l2_duplicate_members.csv
- l2_swing_stale_effect_window_policy.yaml
- l2_stale_effect_window_report.csv
- l2_dedup_stale_validation_report.json
- l2_dedup_stale_validation_report.md

5. L2 Hard Validator + Completion QA Report
- Create one integrated validator.
- Block legacy builder, direct L0-L2 path, feature materialization, score, rank, return, signal, order, broker, paper/live, future outcome, missing-as-negative.
- Produce both machine-readable and human-readable QA.

Outputs:
- scripts/validate_l2_swing_event_layer.py
- l2_completion_validation_report.json
- l2_completion_validation_report.md
- l2_block_reason_summary.csv
- l2_family_count_summary.csv
- l2_mapping_scope_summary.csv
- l2_dedup_summary.csv
- l2_stale_status_summary.csv
- l2_sample_admitted_rows.md
- l2_sample_review_rows.md
- l2_sample_archive_rows.md
- artifact_manifest.csv

Acceptance criteria:
- Source families public_context_news_feeds, public_market_macro_news_feeds, public_newswire_feeds are represented or explicitly explained.
- L2 input is broader than the current 3-row sample, or scope is explicitly blocked.
- No L0 direct ingest.
- Every L2 row has source_packet_id, raw_path, raw_sha256.
- Feature materialization remains closed.
- L3 read view has only whitelisted columns.
- UNKNOWN mapping is review-only or blocked, not active feature.
- Duplicate non-canonical rows are not active L3 candidates.
- Stale rows are archive/context/block, never negative evidence.
- No return, alpha, score, rank, signal, target, order, broker, paper, live columns.
- Legacy L2 news builder remains quarantined.
- QA report clearly shows family counts, mapping counts, dedup counts, stale counts, admitted/review/archive/blocked examples.
```

---

# 10. 최종 검증 체크리스트

## 완료 인정 조건

| 체크                | 완료 기준                                   |
| ----------------- | --------------------------------------- |
| 입력 범위             | 현재 3-row sample보다 넓거나, 부족 사유가 명시됨       |
| L1 경유             | 모든 row가 L1 packet/handoff 기반            |
| source family     | context / macro / newswire 3개 모두 처리     |
| mapping           | TICKER/ENTITY/SECTOR/MACRO/UNKNOWN 구분   |
| UNKNOWN           | active feature/read 금지, review queue 허용 |
| dedup             | canonical/duplicate 분리                  |
| stale             | active/archive/context/block 분리         |
| effect window     | 1D/5D/20D/60D 선언                        |
| L3 read           | whitelist view 별도 존재                    |
| forbidden columns | return/alpha/score/rank/signal/order 없음 |
| hard boundary     | trading/paper/live/broker 변화 없음         |
| QA                | 사람이 이해 가능한 report 존재                    |

---

## 실패 처리 기준

| 상황                                 | 처리                                   |
| ---------------------------------- | ------------------------------------ |
| broader L1 packet 없음               | `BLOCKED_L1_PACKET_SCOPE_TOO_NARROW` |
| L0 raw 직접 사용                       | FAIL                                 |
| legacy builder import              | FAIL                                 |
| UNKNOWN을 active feature로 admission | FAIL                                 |
| stale을 negative evidence로 사용       | FAIL                                 |
| duplicate를 독립 L3 candidate로 노출     | FAIL                                 |
| forward/realized return 계산         | FAIL                                 |
| score/ranking/signal 생성            | FAIL                                 |
| order/broker/paper/live 관련 코드 변경   | FAIL                                 |
| broad cleanup 수행                   | FAIL                                 |

---

# 최종 권고

사장님, 지금 L2에서 **더 보수적으로 막아야 할 부분**과 **그만 막아도 되는 부분**을 나누면 이렇습니다.

| 구분             | 결론                                                                                                                |
| -------------- | ----------------------------------------------------------------------------------------------------------------- |
| 계속 강하게 막을 것    | L0 direct ingest, legacy builder, feature materialization, return/score/rank/order, future leakage                |
| 이제 과도하게 막지 말 것 | daily publication date, historical archive/context, UNKNOWN review queue, incomplete backfill 상태에서의 bounded L2 QA |
| 지금 완성해야 할 것    | admission view 확장, L3 read contract, mapping review, dedup/stale/window, hard validator/QA                        |
| 아직 하지 말 것      | sentiment, alpha, full entity system, embedding dedup, DB migration, backtest/signal                              |

**한 줄 결론:**
L2 완성은 “뉴스로 돈 버는 로직”을 만드는 게 아니라, **뉴스/매크로/뉴스와이어가 L3 연구 대상으로 들어가도 안전한지 증명하는 read/admission layer를 완성하는 것**입니다.
