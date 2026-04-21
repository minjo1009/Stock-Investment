# Task Create Prompt

## Purpose
- 이 문서는 개별 task 생성 규격을 정의한다.
- task는 구현, 수정, 검증, 문서화의 최소 실행 단위다.
- 이 문서는 `skills/skill.md`의 상위 원칙을 따른다.

## When to Create a Task
- 하나의 명확한 목적을 구현해야 할 때 생성한다.
- 변경 범위를 설명할 수 있을 때 생성한다.
- acceptance criteria와 tests를 명시할 수 있을 때 생성한다.
- 문서 수정이라도 영향 범위가 있으면 task로 생성한다.

## When NOT to Create a Task
- 복수 목적을 한 번에 밀어 넣으려는 경우 생성하지 않는다.
- 아직 문제 정의가 불명확한 경우 생성하지 않는다.
- phase 수준의 실행계획이 필요한 경우 task로 시작하지 않는다.
- "전반 개선", "정리", "최적화", "리팩토링"처럼 범위를 닫을 수 없는 경우 생성하지 않는다.

## Task Granularity Rules
- 1 Task = 1 목적 원칙을 따른다.
- task는 한 번의 구현 사이클 안에서 완료 가능해야 한다.
- 변경 파일과 검증 대상을 설명할 수 있어야 한다.
- 범위가 넓어 완료 판정이 불가능하면 더 작은 task로 분해한다.
- phase 목적을 대신하는 task는 금지한다.

## Required Fields
- Title
- Purpose
- Background
- In Scope
- Out of Scope
- Inputs
- Outputs
- Target Files
- Dependencies
- Implementation Notes
- Acceptance Criteria
- Tests
- Risks

## Task Decomposition Rules
- 목적이 둘 이상이면 task를 분리한다.
- 파일군이 분리되고 검증도 독립되면 task를 분리한다.
- 문서 수정과 코드 수정의 완료 기준이 다르면 task를 분리한다.
- 전략 변경, 운영 변경, 리스크 변경이 함께 섞이면 task를 분리한다.
- KR과 US의 가정이 다르면 task를 분리 검토한다.

## Naming Convention
- 파일명은 `task-xxxx-brief-purpose.md` 형식을 권장한다.
- 제목은 결과 중심으로 작성한다.
- 제목에 모호한 단어를 쓰지 않는다.
- 예시: `task-001-bootstrap-phase-0-documents.md`

## Anti-Patterns
- 목적 없는 정리 작업
- acceptance criteria 없는 작업
- tests 없는 변경
- 영향 범위를 설명하지 못하는 리팩토링
- phase 없이 여러 하위 변경을 묶는 작업
- 룰 기반 매매 로직과 LLM 역할을 혼동하는 작업

## Task Template
```md
# Title

## Purpose
- 이 task가 달성할 단일 목적을 적는다.

## Background
- 왜 이 task가 필요한지 적는다.

## In Scope
- 이번 task에서 변경하는 범위를 적는다.

## Out of Scope
- 이번 task에서 하지 않는 것을 적는다.

## Inputs
- 참고 문서, 이슈, phase, context를 적는다.

## Outputs
- 생성 또는 변경되는 산출물을 적는다.

## Target Files
- 직접 변경할 파일 목록을 적는다.

## Dependencies
- 선행 task, phase, 외부 제약을 적는다.

## Implementation Notes
- 구현 시 지켜야 할 규칙과 금지사항을 적는다.

## Acceptance Criteria
- 완료 판정 기준을 명시한다.

## Tests
- 수행할 검증 항목을 적는다.

## Risks
- 예상 리스크와 주의점을 적는다.
```
