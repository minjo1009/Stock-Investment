# Task 005: Context Index Build

## Purpose
- context 폴더 전체 인덱스와 하위 README 체계를 구축/정비한다.

## Background
- 분류 체계가 없으면 근거 문서가 산재되어 탐색 비용이 급격히 증가한다.
- Phase 02 종료 조건에는 4분류 기반 탐색 체계의 가시화가 포함된다.

## In Scope
- `context/README.md` 갱신
- `context/product/README.md` 정비
- `context/architecture/README.md` 정비
- `context/codebase/README.md` 정비
- `context/workflow/README.md` 정비
- facts vs interpretation 구분 규칙 반영
- context 읽기 우선순위 반영

## Out of Scope
- 하위 상세 문서 대량 작성
- 구현 코드/테스트 코드 변경
- phase/task 외 문서 체계 변경

## Inputs
- `phases/phase-02-context-inventory.md`
- `tasks/task-001-product-context-definition.md`
- `tasks/task-002-architecture-context-definition.md`
- `tasks/task-003-codebase-context-scan.md`
- `tasks/task-004-workflow-context-definition.md`

## Outputs
- `context/README.md`와 하위 README 4개의 인덱스 체계 완성

## Target Files
- `context/README.md`
- `context/product/README.md`
- `context/architecture/README.md`
- `context/codebase/README.md`
- `context/workflow/README.md`

## Dependencies
- 선행: Task 001, 002, 003, 004 결과
- 후행: Phase 02 종료 판정

## Implementation Notes
- 4분류 역할이 중복되지 않게 작성한다.
- 하위 README는 “폴더 사용법/문서 종류/관리 규칙” 중심으로 작성한다.
- 향후 세부 문서가 증가해도 인덱스 구조가 유지되도록 단순하고 확장 가능하게 설계한다.

## Acceptance Criteria
- context 폴더가 확장 가능한 인덱스 체계를 가진다.
- 하위 분류 목적이 명확히 구분된다.
- 중복 없이 탐색 가능한 구조가 된다.

## Tests
- README들만 읽고 context 전체 구조를 설명할 수 있다.
- 신규 세부 문서를 어느 하위 분류에 배치할지 즉시 판단할 수 있다.

## Risks
- 분류 경계가 약하면 동일 내용이 여러 폴더에 중복될 수 있다.
- 읽기 우선순위가 없으면 운영자가 잘못된 문맥에서 작업을 시작할 수 있다.
