# TASK-4155 GPT Pro 검수 요약

## 판정

`CONDITIONAL PASS`

현재 L0~L3 상태만으로도 L4를 시작해도 된다. 단, 시작 범위는 `diagnostic thesis bundle bootstrap`이어야 한다.

즉 L4는 매매 결론을 내는 계층이 아니다. L4는 L0~L3에서 올라온 근거를 묶어서 "검토 가능한 투자 논지"로 정리하고, 근거 부족, 출처 공백, 반증 미검토, 관계 그래프 한계를 분명히 표시하는 계층이다.

## L4의 목표

L4의 목표는 L0~L3의 source, feature, relation 후보를 이용해 출처와 근거가 추적 가능하고, 반증/공백/불확실성이 명시된 진단용 thesis bundle을 만드는 것이다.

쉬운 표현으로 말하면:

- L0는 원자료를 모은다.
- L1은 원자료를 쓸 수 있는 packet으로 정리한다.
- L2는 경제적으로 의미 있어 보이는 후보를 만든다.
- L3는 후보들 사이의 관계를 그래프로 묶는다.
- L4는 이 재료들을 이용해 "이 논지를 검토할 수 있는가?"를 판단 가능한 묶음으로 만든다.

## L4가 해야 하는 일

| 역할 | 쉬운 설명 | 산출물 |
|---|---|---|
| Thesis 후보 조립 | L2 의미 후보와 L3 관계 후보를 묶어 검토용 논지를 만든다 | `l4_thesis_bundles.jsonl` |
| 근거 연결 | 논지가 어떤 L1/L2/L3 근거에서 왔는지 연결한다 | `l4_thesis_evidence_links.csv` |
| 출처 추적 | 원 출처, source time, ingest time, source lane을 남긴다 | bundle/evidence link fields |
| 공백 표시 | L0 백필 미완료, L3 coverage gap, source 접근 불가를 blocker로 남긴다 | `l4_thesis_blockers.csv` |
| 반증 상태 표시 | contradiction scan 미구현을 "반증 없음"으로 바꾸지 않는다 | blocker + contradiction status |
| 관계 품질 이월 | L3의 PROTO_BUCKET, sparse/singleton, unsupported family 상태를 그대로 넘긴다 | bundle quality fields |
| 진단 점수 | specificity, linkage, traceability 같은 검토용 점수만 만든다 | diagnostic score fields |
| 검증 | hard boundary, schema, lineage, blocker, count consistency를 validator로 확인한다 | validation report |

## L4가 하면 안 되는 일

| 금지 | 이유 |
|---|---|
| BUY/SELL/HOLD 생성 | L4 권한 밖 |
| 랭킹 생성 | graph count를 품질로 오해할 위험 |
| 비중/진입가/청산가 생성 | 매매 권한 오픈 위험 |
| order intent 생성 | live/paper/order 경계 위반 |
| paper/live 가능 여부 판단 | 명시적으로 금지 |
| strategy accepted 판단 | 현재 전략 상태는 `NOT_ACCEPTED` |
| deployment ready 판단 | 현재 배포 상태는 `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` |
| L0 누락을 부정 증거로 사용 | missing data는 `UNKNOWN/BLOCKER` |
| SOURCE_EVENT_CLUSTER를 confirmed same-event로 승격 | L3 handoff rule 위반 |
| contradiction 미구현을 no contradiction으로 해석 | 가장 위험한 허위 clear |
| vector DB/graph DB/LLM thesis writer부터 구축 | P0 범위 과함 |

## GPT가 제안한 첫 L4 산출물

| 산출물 | 의미 |
|---|---|
| `data/diagnostics/l4/l4_thesis_bundles.jsonl` | thesis bundle 주 테이블 |
| `data/diagnostics/l4/l4_thesis_evidence_links.csv` | thesis와 근거의 연결 테이블 |
| `data/diagnostics/l4/l4_thesis_blockers.csv` | 왜 확정하지 못하는지 보여주는 blocker 테이블 |
| `data/diagnostics/l4/l4_run_manifest.json` | 입력/출력/검증 상태를 남기는 run manifest |

## 구현 우선순위

| 우선순위 | 작업 | 핵심 |
|---|---|---|
| P0 | L4 package skeleton | `src/brain/l4_thesis_bundle` 생성 |
| P0 | schema 정의 | bundle/evidence/blocker/manifest 계약 고정 |
| P0 | deterministic builder | 같은 입력이면 같은 bundle id가 나오게 생성 |
| P0 | hard boundary 주입 | 모든 산출물에 diagnostic-only와 금지 상태 명시 |
| P0 | blocker carryover | L0 incomplete, L3 coverage gap, unsupported family를 blocker로 넘김 |
| P0 | semantic validator | raw-only evidence, no contradiction 허위 clear, trading field를 fail |
| P0 | CLI scripts | build/validate 명령 제공 |
| P0 | unit tests | boundary, lineage, blocker, count consistency 회귀 방지 |
| P1 | quality score v0 | 검토용 점수. trading authority 아님 |
| P1 | thesis templates | ENTITY_EVENT, MACRO_CONTEXT 등 유형별 문장 틀 |
| P1 | blocked/mixed summary | blocker 종류별 요약 |
| P1 | source access checker | 출처 접근 가능 여부 read-only 확인 |

## 현재 기준 결론

L4로 넘어가도 된다. 다만 L4의 첫 구현은 "좋은 투자 결론 만들기"가 아니라 "근거가 추적되고, 한계가 숨겨지지 않는 thesis 검수 패키지 만들기"이다.

현재 L0 백필 일부 미완료와 L3의 CONTRADICTION/MACRO_SECTOR/SECTOR_THEME 미구현 때문에 기관급 확정 thesis pass는 아직 열면 안 된다.

