# TASK-4154 L3 Relation Graph V2 Quality Guard And L4 Handoff

## 결론

TASK-4153 GPT Pro가 제시한 조건부 통과 조건을 해소하기 위한 quality guard와 L3-to-L4 diagnostic handoff 산출물을 구현했다.

이번 작업은 TASK-4152 relation graph 자체를 다시 늘리거나 바꾸는 작업이 아니다. L4가 L3 v2를 과하게 해석하지 못하도록 “품질 요약, proto cluster 한계, 미구현 relation family, coverage gap, L4 금지 해석”을 명시하는 작업이다.

## 생성 산출물

| 산출물 | 역할 |
|---|---|
| `l3_graph_quality_summary.csv` | graph family별 sparse/singleton 상태 요약 |
| `l3_graph_quality_summary.json` | 동일 요약의 JSON 버전 |
| `l3_event_clusters_with_limitations.csv` | event cluster가 확정 동일 사건이 아니라 proto bucket임을 명시 |
| `l3_unsupported_relation_families.csv` | `MACRO_SECTOR`, `SECTOR_THEME`, `CONTRADICTION` 미구현 명시 |
| `l3_coverage_gap_summary_by_reason_source_date.csv` | coverage gap을 reason/source/date bucket별로 요약 |
| `l3_l4_diagnostic_handoff_manifest.json` | L4가 따라야 할 diagnostic-only handoff 계약 |
| `l3_quality_guard_validation.json` | TASK-4154 validator 결과 |

## 품질 요약 핵심

| graph family | graph 수 | edge 수 | edge/graph | singleton 비율 | 해석 |
|---|---:|---:|---:|---:|---|
| COVERAGE_GAP | 2 | 181 | 90.50 | 0.00% | 뉴스와이어 gap이 2개 week bucket으로 묶임 |
| ENTITY_DIMENSION | 947 | 1,771 | 1.87 | 53.96% | 일부 반복 근거가 있지만 아직 sparse |
| ENTITY_EVENT | 1,771 | 1,771 | 1.00 | 100.00% | 현재는 event 후보 링크이지 확정 이벤트 아님 |
| MACRO_FACTOR | 828 | 828 | 1.00 | 100.00% | macro context 후보 링크이지 인과 thesis 아님 |
| SOURCE_EVENT_CLUSTER | 1,850 | 2,599 | 1.40 | 65.95% | proto event bucket이며 동일 사건 확정 아님 |

이 수치 때문에 L4는 graph count를 품질로 보면 안 된다. 5,398개 graph는 “관계 후보가 넓게 펼쳐졌다”는 뜻이지, “5,398개의 강한 투자 근거가 생겼다”는 뜻이 아니다.

## Event Cluster Guard

`l3_event_clusters_with_limitations.csv`에 다음 필드를 강제했다.

| 필드 | 값 |
|---|---|
| `cluster_basis` | `l1_packet_id|economic_dimension|event_time_bucket` |
| `event_identity_status` | `PROTO_BUCKET` |
| `same_event_assertion` | `false` |

즉 현재 event cluster는 “같은 사건 후보 묶음”이지 “확정된 동일 사건”이 아니다.

## Unsupported Relation Families

| family | 상태 | L4 해석 |
|---|---|---|
| MACRO_SECTOR | NOT_IMPLEMENTED | macro-sector linkage는 아직 scan/clear되지 않았다 |
| SECTOR_THEME | NOT_IMPLEMENTED | sector-theme linkage는 아직 scan/clear되지 않았다 |
| CONTRADICTION | NOT_IMPLEMENTED | 반대 증거가 없다는 뜻이 아니다 |

특히 `CONTRADICTION`은 full implementation은 P1이어도, “미구현 상태를 L4에 명시”하는 것은 P0였다. 이번 작업으로 그 P0 guard를 추가했다.

## Coverage Gap Guard

뉴스와이어 gap 181건은 L4에서 사라지지 않도록 reason/source/week bucket으로 요약했다.

| reason | bucket | count |
|---|---|---:|
| NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE | 2026-W26 | 166 |
| NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE | 2026-W27 | 15 |

이 gap은 부정 증거가 아니다. `UNKNOWN/BLOCKER`다.

## L4 Handoff Contract

`l3_l4_diagnostic_handoff_manifest.json`에 다음 hard boundary를 명시했다.

- diagnostic_only: true
- strategy_status: `NOT_ACCEPTED`
- deployment_status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- real_capital: `FORBIDDEN`
- no_broker_mutation: true
- no_live_order: true
- no_paper_promotion: true
- event_identity_status: `PROTO_BUCKET`
- same_event_assertion: false

L4가 금지해야 할 해석도 명시했다.

- graph count does not imply evidence quality
- SOURCE_EVENT_CLUSTER does not assert confirmed same event
- ENTITY_EVENT does not assert material event
- MACRO_FACTOR does not assert causal macro thesis
- absence of CONTRADICTION family does not mean no contradiction exists
- coverage gaps are UNKNOWN/BLOCKER, not negative evidence
- L3 output does not authorize ranking, sizing, order intent, paper/live trading, strategy acceptance, or deployment readiness

## 검증 결과

`python scripts/validate_l3_relation_graph_quality_guard_4154.py --artifact-dir data/artifacts/task_4154_l3_relation_graph_v2_quality_guard --source-dir data/artifacts/task_4152_l3_relation_graph_v2`

결과: PASS, failures 0.

검증한 내용:

- required artifacts exist
- quality summary csv/json row counts reconcile
- graph total reconciles to TASK-4152 graphs
- edge total reconciles to TASK-4152 edges
- event cluster limitation rows reconcile
- all event clusters marked `PROTO_BUCKET`
- `same_event_assertion=false` for every cluster
- unsupported relation families declared
- newswire article feature gap remains visible
- coverage gap summary reconciles to source gaps
- L4 handoff hard boundary flags valid
- public newswire UNKNOWN collapse remains outside normal relation graphs
- no forbidden trading output values in TASK-4154 outputs

## 안전 경계

- Strategy remains `NOT_ACCEPTED`
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital remains `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data remains `UNKNOWN/BLOCKER`, not negative evidence

