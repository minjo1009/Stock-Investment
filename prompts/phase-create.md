# Phase Create Prompt

## Purpose
- 이 문서는 phase 생성 규격을 정의한다.
- phase는 상위 실행계획이다.
- task는 phase를 구성하는 구현 단위다.
- 이 문서는 `skills/skill.md`의 상위 원칙을 따른다.

## When to Create a Phase
- 복수 task를 순서 있게 관리해야 할 때 생성한다.
- 산출물, 의존성, 종료조건을 상위 수준에서 통제해야 할 때 생성한다.
- 다음 단계로 handoff 가능한 계획이 필요할 때 생성한다.
- 운영체계, 저장소 구조, 아키텍처 기반을 만드는 작업일 때 생성한다.

## Phase vs Task
- phase는 실행계획이다.
- task는 구현단위다.
- phase는 왜, 무엇을, 어떤 순서로 끝낼지를 정의한다.
- task는 어떤 파일을 어떻게 바꾸고 어떻게 검증할지를 정의한다.
- phase는 완료 상태를 판정할 수 있어야 한다.
- task는 개별 acceptance criteria를 판정할 수 있어야 한다.

## Required Fields
- Title
- Objective
- Why This Phase Exists
- Entry Conditions
- Scope
- Out of Scope
- Deliverables
- Task Inventory
- Execution Order
- Exit Criteria
- Risks
- Handoff

## Task Inventory Rules
- task 목록은 phase 목적과 직접 연결되어야 한다.
- 각 task는 단일 목적을 가져야 한다.
- task 설명은 구현 범위와 산출물을 예측 가능하게 해야 한다.
- task 순서는 의존성 기준으로 정한다.
- phase 문서에 task 세부 구현 규칙을 과도하게 반복하지 않는다.

## Execution Rules
- phase는 진입 조건이 충족된 상태에서 시작한다.
- 진행 중 범위 확장이 필요하면 신규 task 또는 신규 phase를 만든다.
- 승인되지 않은 직접 수정은 금지한다.
- 고위험 문서 또는 운영 규칙 변경은 영향 범위를 검토한다.
- 종료 시 exit criteria 충족 여부를 명시적으로 판정한다.

## Naming Convention
- 파일명은 `phase-xx-brief-purpose.md` 형식을 사용한다.
- 제목은 목적과 상태를 설명해야 한다.
- 모호한 운영어 대신 실제 목표를 사용한다.
- 예시: `phase-01-repository-foundation.md`

## Anti-Patterns
- task 집합이 없는 phase
- 종료조건 없는 phase
- 구현 세부사항만 나열한 phase
- task와 phase의 책임이 뒤섞인 문서
- "지속 개선", "전체 정리"처럼 종료 판정이 불가능한 phase

## Phase Template
```md
# Title

## Objective
- phase가 끝났을 때 달성해야 하는 상태를 적는다.

## Why This Phase Exists
- phase가 필요한 이유를 적는다.

## Entry Conditions
- 시작 전에 충족되어야 하는 조건을 적는다.

## Scope
- 이번 phase에서 다루는 범위를 적는다.

## Out of Scope
- 이번 phase에서 다루지 않는 범위를 적는다.

## Deliverables
- 종료 시 존재해야 하는 산출물을 적는다.

## Task Inventory
- 포함되는 task 후보와 목적을 적는다.

## Execution Order
- task 또는 작업 묶음의 선후관계를 적는다.

## Exit Criteria
- 종료 판정 기준을 적는다.

## Risks
- phase 수준 리스크와 대응 방향을 적는다.

## Handoff
- 다음 phase 또는 후속 task로 넘길 내용을 적는다.
```
