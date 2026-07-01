# TASK-4153 GPT Pro 검수 요약

## 결론

GPT Pro 판정은 `CONDITIONAL PASS`다.

뜻은 단순하다. TASK-4152의 L3 relation graph v2는 방향이 맞고, 27개에서 5,398개로 늘어난 것은 단순한 중복 폭증이라기보다 기존의 과도한 압축을 풀어낸 구조적 개선으로 보는 것이 맞다.

다만 graph 수가 늘었다고 해서 관계 품질, 동일 사건 확정, 인과관계, thesis 검증 완료를 뜻하지는 않는다. L4로 넘기기 전에 graph 품질/한계/미구현 관계/coverage gap을 명시하는 guard가 필요하다.

## 핵심 판단

| 질문 | GPT Pro 의견 |
|---|---|
| 27 -> 5,398 확장은 진짜 개선인가 | 대체로 맞다. 기존 27개는 너무 뭉쳐 있었고, v2는 관계를 더 올바른 단위로 풀었다 |
| 중복/노이즈 부풀림인가 | validator상 dedupe는 통과했지만, sparse/singleton graph 비율을 별도 공개해야 한다 |
| L3 역할에 맞나 | 맞다. L3는 진단용 관계 구조화 레이어로 동작하고 있다 |
| L4로 넘겨도 되나 | 진단 입력으로는 가능하다. 단, L4가 이를 확정 thesis나 매매 신호로 해석하면 안 된다 |
| 뉴스와이어 coverage gap 처리는 맞나 | 맞다. `SOURCE_FAMILY/UNKNOWN`을 정상 relation으로 둔 것보다 훨씬 낫다 |
| 아직 부족한 점 | graph quality summary, proto event identity 표시, unsupported relation family 표시, L4 handoff manifest가 필요하다 |

## GPT Pro가 좋게 본 점

| 항목 | 이유 |
|---|---|
| L1/L2 lineage 유지 | 모든 edge가 어디서 왔는지 추적 가능하다 |
| raw L0 직접 읽기 없음 | 레이어 경계를 지켰다 |
| 뉴스와이어 UNKNOWN collapse 제거 | 모르는 것을 아는 척하지 않게 됐다 |
| coverage gap 분리 | 부족한 데이터가 부정 신호로 오해되지 않는다 |
| forbidden trading output 없음 | L3가 매매 권한을 열지 않았다 |
| event cluster 도입 | L4가 evidence를 찾아갈 시작점이 생겼다 |

## GPT Pro가 걱정한 점

| 리스크 | 쉬운 표현 | 조치 |
|---|---|---|
| graph 수가 품질로 오해될 수 있음 | 많이 생겼다고 좋은 관계라는 뜻은 아님 | graph quality summary 필요 |
| `SOURCE_EVENT_CLUSTER`가 실제 동일 사건처럼 보일 수 있음 | 지금은 진짜 event cluster라기보다 proto bucket | `same_event_assertion=false` 명시 |
| `CONTRADICTION` 미구현 | 반대 증거가 없다는 뜻으로 오해될 수 있음 | unsupported family로 명시 |
| `MACRO_SECTOR`, `SECTOR_THEME` 미구현 | macro가 sector/theme으로 이어지는 설명이 아직 약함 | P1 구현 대상 |
| coverage gap이 L4에서 무시될 수 있음 | UNKNOWN/BLOCKER가 사라질 수 있음 | gap summary와 L4 handoff manifest 필요 |

## P0로 해야 할 일

| P0 작업 | 이유 |
|---|---|
| graph quality summary 생성 | graph 확장이 품질 개선인지 사람이 판단 가능해야 함 |
| event cluster 한계 필드 추가 | 현재 cluster는 확정 동일 사건이 아니라 proto bucket임 |
| L3-to-L4 diagnostic handoff manifest 생성 | L4가 L3를 과해석하지 않도록 막아야 함 |
| unsupported relation families 명시 | 미구현 관계를 “문제 없음”으로 오해하면 안 됨 |
| coverage gap summary 생성 | 뉴스와이어 gap 181건이 L4에서 보이게 해야 함 |
| validator 보강 | count 증가만으로 PASS하지 못하게 해야 함 |

## L4 이동 판단

L4로 완전히 넘어가기 전에 TASK-4153 후속 guard patch가 필요하다.

다만 이건 L3를 다시 크게 갈아엎는 작업이 아니다. 현재 v2 구조는 유지하고, L4가 잘못 읽지 않도록 품질 요약과 한계 표시를 추가하는 작업이다.

## 안전 경계

GPT Pro는 L3가 계속 diagnostic-only로 남아야 한다고 봤다.

- no BUY/SELL
- no ranking
- no sizing
- no order intent
- no broker mutation
- no paper/live eligibility
- no strategy acceptance
- no deployment readiness

