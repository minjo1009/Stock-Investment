# TASK-4155 L4 Goal Definition GPT Review

## 목적

L4의 목표, 역할, 세부 역할, 산출물 구조, validator 방향을 명확히 정의하기 위해 현재 L0~L3 구현 상태와 L4 governance 정보를 GPT Pro에 전달하고 검수받았다.

## GPT 검수 방식

- relay mode: `single_gpt_consult`
- GPT role: professional backend engineer, quant data infrastructure reviewer, institutional equity research PM, systematic PM/trading research reviewer, risk/trading controls reviewer
- GitHub 상태는 최신 local work를 반영하지 못할 수 있으므로, 로컬 context packet을 source of truth로 전달했다.
- GPT tab cleanup: `closed_agent_created_tab`

## GPT 판정

`CONDITIONAL PASS`

L4를 시작해도 되지만, 범위는 `diagnostic thesis bundle bootstrap`으로 제한해야 한다. 현재 상태에서 L4가 투자 판단, 정책 액션, 랭킹, 포지션 판단, paper/live 가능 여부를 만들면 안 된다.

## L4 목표

L4는 L0~L3에서 올라온 source, feature, relation 후보를 이용해 출처와 근거가 추적 가능하고, 반증/공백/불확실성이 명시된 진단용 thesis bundle을 만드는 계층이다.

## L4 역할

| 역할 | 설명 |
|---|---|
| thesis candidate assembly | L2 feature 후보와 L3 relation graph를 묶어 검토용 논지를 만든다 |
| evidence linkage | L1 packet, L2 feature, L3 graph/edge, L0 source lineage를 연결한다 |
| source traceability | source lane, source id, source time, ingest time, URL/path를 남긴다 |
| blocker visibility | L0 incomplete, L3 coverage gap, unsupported relation family를 숨기지 않는다 |
| contradiction handling | contradiction 미구현을 `NO_CONTRADICTION`으로 바꾸지 않는다 |
| proto relation carryover | L3의 `PROTO_BUCKET`, `same_event_assertion=false`를 유지한다 |
| diagnostic quality scoring | 검토용 score만 만든다. 매매 권한이나 전략 승인으로 쓰지 않는다 |
| validator handoff | schema, hard boundary, lineage, blocker, count consistency를 검증한다 |

## L4 필수 산출물 제안

| artifact | 역할 |
|---|---|
| `data/diagnostics/l4/l4_thesis_bundles.jsonl` | thesis bundle 주 테이블 |
| `data/diagnostics/l4/l4_thesis_evidence_links.csv` | thesis와 근거 연결 테이블 |
| `data/diagnostics/l4/l4_thesis_blockers.csv` | thesis 확정을 막는 이유 테이블 |
| `data/diagnostics/l4/l4_run_manifest.json` | run 단위 입력/출력/검증 상태 |

## L4 validator 핵심 규칙

| 검증 | fail 조건 |
|---|---|
| hard boundary | `diagnostic_only`, `NOT_ACCEPTED`, `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, `FORBIDDEN` 누락/변경 |
| forbidden authority | order intent, sizing, ranking, paper/live eligibility, strategy accepted, deployment ready field 존재 |
| evidence linkage | supporting/context evidence가 L1/L2 lineage 없이 raw-only로 사용됨 |
| missing data semantics | coverage gap 또는 incomplete coverage를 negative evidence로 해석 |
| contradiction | contradiction 미구현인데 `NO_CONTRADICTION` 출력 |
| proto event | `SOURCE_EVENT_CLUSTER`를 confirmed same-event로 승격 |
| count consistency | bundle evidence count와 evidence link row 수 불일치 |
| manifest consistency | manifest count와 실제 artifact row 수 불일치 |

## 개발 우선순위

| 우선순위 | 작업 | 구체 내용 |
|---|---|---|
| P0 | L4 package skeleton | `src/brain/l4_thesis_bundle` 생성 |
| P0 | schema contract | bundle/evidence/blocker/manifest 필드 정의 |
| P0 | deterministic builder | L1/L2/L3 artifact에서 L4 산출물 생성 |
| P0 | hard-boundary injection | 모든 artifact에 safety state 명시 |
| P0 | blocker carryover | L0 incomplete, L3 gap, unsupported family 반영 |
| P0 | semantic validator | L4 권한 초과와 허위 clear 차단 |
| P0 | CLI scripts/tests | build/validate/test 재현 가능하게 구성 |
| P1 | quality score v0 | 검토용 점수. trading authority 없음 |
| P1 | thesis templates | thesis type별 문장 템플릿 |
| P1 | blocked/mixed summary | blocker type별 현황 요약 |

## 과도한 구현으로 자를 것

이번 L4 bootstrap에서 graph DB, vector DB, LLM thesis writer, portfolio construction, ranking engine, broker integration, scheduler, UI, paper/live gate, strategy acceptance gate는 만들지 않는다.

## 안전 경계

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real Capital remains `FORBIDDEN`.
- No broker mutation was added.
- No live order path was added.
- No paper promotion was added.
- Missing/stale/incomplete data remains `UNKNOWN/BLOCKER`.

## 산출물

- `context_packet.md`: GPT 전달용 L0~L4 현황 패킷
- `gpt_prompt.md`: GPT Pro 전달 프롬프트
- `gpt_response.md`: GPT Pro 원문 응답
- `gpt_capture_meta.json`: GPT 캡처 메타
- `gpt_review_digest_ko.md`: 한글 핵심 요약
- `artifact_manifest.csv`: TASK-4155 산출물 목록
- `validation_results.md`: 검증 결과

