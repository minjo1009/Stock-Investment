# TASK-4141 L2 GPT Pro Design Review

## 결론

GPT Pro 검수 결과, Layer 2로 넘어가는 것은 맞다. 다만 L2의 첫 작업은 점수화나 매매 신호가 아니다.

| 질문 | GPT Pro 답 |
|---|---|
| L2로 넘어가도 되나 | 가능 |
| L2 첫 view | `L2 Swing Event Admission View` |
| L2의 핵심 역할 | L1 증거를 L3가 읽을 수 있는 안전한 primitive/admission view로 바꾸기 |
| 뉴스/매크로/뉴스와이어 | 스윙 feature 후보가 맞음 |
| 분/초 source time | 핵심 병목 아님 |
| 아직 금지 | feature score, signal, ranking, realized return, sizing, order, paper/live |

## GPT가 본 L2의 역할

L2는 raw data를 바로 feature로 만드는 층이 아니다.

L2는 아래를 담당한다.

| 역할 | 쉬운 의미 |
|---|---|
| admission | 이 row가 L2에 들어와도 되는지 확인 |
| primitive | 뉴스/매크로/뉴스와이어를 공통 이벤트 형태로 정리 |
| mapping | TICKER / ENTITY / SECTOR / MACRO / UNKNOWN 구분 |
| dedup | 같은 이벤트를 여러 기사로 여러 번 세지 않게 함 |
| stale | 너무 오래된 정보는 막거나 context로 내림 |
| effect window | 1D / 5D / 20D / 60D 후보 기간 표시 |
| L3 read view | L3가 안전하게 읽을 수 있는 view 제공 |

## 다음 작업 권고

GPT Pro는 다음 작업을 사실상 `TASK-4142`로 제안했다.

| 순서 | 작업 |
|---:|---|
| 1 | L2 Swing Event Admission View |
| 2 | Mapping/Dedup Validator |
| 3 | Stale/Effect Window Policy |
| 4 | L3 Read Contract Sample |
| 5 | 이후 L3 feature 연구 |

## 최소 스키마 방향

GPT가 제안한 L2 view는 한 raw article row가 아니라, 가능한 한 `canonical event + mapping candidate` 단위여야 한다.

핵심 필드:

- `l2_event_id`
- `l2_event_mapping_id`
- `source_packet_id`
- `source_family`
- `raw_path`
- `raw_sha256`
- `publication_date`
- `publication_time_precision`
- `is_publication_time_imputed`
- `activation_policy`
- `activation_decision_date`
- `mapping_scope`
- `mapping_key`
- `dedup_key`
- `event_cluster_id`
- `is_canonical_event`
- `stale_status`
- `primary_effect_window`
- `secondary_effect_windows`
- `admission_status`
- `feature_materialization_allowed`
- `trading_authority_opened`

## 중요한 금지선

| 금지 | 이유 |
|---|---|
| legacy L2 news builder 복구 | quarantine 상태 유지가 더 안전 |
| L0 raw news 직접 L2 연결 | L1 gate 우회 위험 |
| sentiment/bullish/bearish score | 아직 L3 이상에서 검증할 영역 |
| realized/forward return | L2에 넣으면 leakage 위험 |
| ranking/sizing/order | L2 범위 아님 |
| broad dirty cleanup | TASK-4139상 dirty worktree가 큼 |

## 캡처 정보

| 항목 | 값 |
|---|---|
| relay mode | `single_gpt_consult` |
| GPT mode | ChatGPT Pro 확장 |
| GitHub 사용 | 최신 로컬 상태가 GitHub에 없으므로 prompt에서 GitHub 의존 금지 |
| prompt | `docs/reports/task_4141_l2_gpt_pro_design_review/gpt_prompt.md` |
| response | `docs/reports/task_4141_l2_gpt_pro_design_review/gpt_response.md` |
| capture status | `CAPTURED` |
| tab cleanup | `skipped_preexisting_user_tab` |

## Codex 판단

GPT Pro 의견은 현재 방향과 잘 맞는다. 다음 구현은 `TASK-4142 L2 Swing Event Admission View`로 잡는 것이 맞다.

이 task에서는 feature materialization을 열지 않고, L3가 읽을 수 있는 admission/read view와 validator까지만 만든다.
