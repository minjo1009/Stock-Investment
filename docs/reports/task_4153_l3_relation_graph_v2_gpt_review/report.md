# TASK-4153 L3 Relation Graph V2 GPT Pro Review

## 작업 목적

TASK-4152에서 구현한 L3 relation graph v2를 GPT Pro에게 재검수받았다. 검수 목적은 27개 graph에서 5,398개 graph로 늘어난 것이 실제 구조 개선인지, 아니면 중복/노이즈 부풀림인지 확인하는 것이다.

## GPT Pro 판정

`CONDITIONAL PASS`.

TASK-4152는 방향이 맞다. 27개에서 5,398개로 늘어난 것은 단순 count inflation이라기보다, 기존에 너무 굵게 뭉친 관계를 L3 역할에 맞게 풀어낸 structural de-collapse로 보는 것이 맞다.

단, graph count 자체가 품질을 의미하지는 않는다. L4로 넘기기 전에 graph quality, proto event identity, unsupported relation families, coverage gap, L4 forbidden assumptions를 명시해야 한다.

## 검수에 제공한 현재 상태

| 항목 | 값 |
|---|---:|
| TASK-4150 relation graphs | 27 |
| TASK-4152 relation graphs | 5,398 |
| TASK-4152 relation edges | 7,150 |
| TASK-4152 event clusters | 1,850 |
| TASK-4152 coverage gaps | 181 |
| validator | PASS |

## GPT Pro가 인정한 개선

| 개선 | 의미 |
|---|---|
| `SOURCE_EVENT_CLUSTER` 추가 | source와 event 후보를 연결할 수 있게 됨 |
| `ENTITY_EVENT` 추가 | entity/symbol과 event 후보를 연결할 수 있게 됨 |
| `ENTITY_DIMENSION` 추가 | entity/symbol과 economic dimension을 연결할 수 있게 됨 |
| `MACRO_FACTOR` 추가 | macro context를 별도 relation family로 분리 |
| newswire coverage gap 분리 | `SOURCE_FAMILY/UNKNOWN`을 정상 relation처럼 취급하지 않음 |
| lineage validator | L1/L2 traceability 유지 |
| no raw L0 bypass | 레이어 경계 유지 |
| no trading output | L3 안전 경계 유지 |

## GPT Pro가 지적한 부족점

| 우선순위 | 부족점 | 의미 | 제안 조치 |
|---|---|---|---|
| P0 | graph quality metrics 부재 | 5,398개 graph가 sparse/singleton인지 사람이 보기 어렵다 | `l3_graph_quality_summary.csv/json` |
| P0 | event cluster가 proto bucket임을 표시해야 함 | L4가 동일 사건 확정으로 오해할 수 있다 | `event_identity_status=PROTO_BUCKET`, `same_event_assertion=false` |
| P0 | L4 handoff manifest 부재 | L4가 L3를 thesis/causal/signal로 오해할 수 있다 | `l3_l4_diagnostic_handoff_manifest.json` |
| P0 | contradiction 미구현 표시 없음 | 반대 증거가 없다고 오해할 수 있다 | unsupported family로 명시 |
| P0 | coverage gap L4 전달 불명확 | UNKNOWN/BLOCKER가 사라질 수 있다 | coverage gap summary |
| P0 | validator가 count expansion만 보게 될 위험 | graph 수 증가가 품질 검증이 되면 안 된다 | validator guard 추가 |
| P1 | newswire article-level L2 feature gap 181건 | 뉴스와이어가 아직 정상 entity/event relation으로 못 넘어감 | L1/L2 newswire feature 보강 |
| P1 | `MACRO_SECTOR`, `SECTOR_THEME` 미구현 | macro/theme chain이 약함 | diagnostic-only relation 추가 |
| P1 | contradiction candidate lane 부재 | L4 thesis가 한쪽 증거만 모을 위험 | candidate lane 추가 |

## L4 이동 판단

L4가 TASK-4152 L3 v2를 사용할 수는 있다. 단, “diagnostic input only”로만 사용해야 한다.

L4가 절대 하면 안 되는 해석:

- graph count가 evidence quality를 뜻한다고 해석
- `SOURCE_EVENT_CLUSTER`가 확정 동일 사건이라고 해석
- `ENTITY_EVENT`가 material event라고 해석
- `MACRO_FACTOR`가 causal macro thesis라고 해석
- contradiction family가 없으니 반대 증거가 없다고 해석
- coverage gap을 부정 증거로 해석
- L3 output이 ranking/sizing/order/paper/live/strategy/deployment 권한을 연다고 해석

## 다음 작업

GPT Pro는 다음 후속 patch를 제안했다.

TASK-4153 follow-up patch:

1. `l3_graph_quality_summary.csv/json`
2. event cluster limitation fields
3. `l3_unsupported_relation_families.csv`
4. `l3_coverage_gap_summary_by_reason_source_date.csv`
5. `l3_l4_diagnostic_handoff_manifest.json`
6. validator update
7. focused tests

## 안전 경계

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data remains `UNKNOWN/BLOCKER`, not negative evidence

## 산출물

- `context_packet.md`
- `gpt_prompt.md`
- `gpt_response.md`
- `gpt_capture_meta.json`
- `gpt_review_digest_ko.md`
- `report.md`
- `artifact_manifest.csv`
- `validation_results.md`

