# Task 013: Artifact Layout Convention

## Purpose
- 5단계 하네스 결과물을 저장하는 artifact 디렉터리/파일 규약을 도입한다.

## Background
- 단계별 handoff를 재현 가능하게 하려면 파일 경로와 네이밍을 표준화해야 한다.
- artifact 형식이 없으면 sub-agent 간 전달 품질과 감사추적성이 떨어진다.

## In Scope
- `artifacts/<task-id>/` 디렉터리 규약 정의
- 단계 파일(`clarify.md`, `context-gather.md`, `plan.md`, `generate.md`, `evaluate.md`) 규약 정의
- 버전 관리 규칙(v2 suffix 등) 정의

## Out of Scope
- artifact 자동 생성 스크립트 구현
- 외부 저장소 연동

## Inputs
- `skills/skill.md`
- `context/workflow/execution-rules.md`
- `phases/phase-01-repository-foundation.md`

## Outputs
- artifact 규약 문서
- 샘플 task-id 기준 경로 예시

## Target Files
- `context/workflow/execution-rules.md`
- 필요 시 `README.md`

## Dependencies
- 선행: 없음
- 후행 연계: Task 014, Task 011, Task 012

## Implementation Notes
- 규약은 간결하되 단계 누락 검출이 가능해야 한다.
- 단계 파일에는 최소 메타데이터(task id, stage, timestamp, owner)를 포함한다.
- 덮어쓰기 대신 버전 추가를 기본 원칙으로 둔다.

## Acceptance Criteria
- task별 artifact 경로를 즉시 결정할 수 있다.
- 단계 파일 명세가 5단계 하네스와 일치한다.
- artifact 누락 시 blocked 판정 기준이 명확하다.

## Tests
- 임의 task-id 예시로 5개 stage 파일 경로를 생성해도 모호성이 없다.
- 재실행 시 버전 suffix 규칙으로 기존 artifact 보존이 가능하다.

## Risks
- 규약이 과도하게 엄격하면 초기 도입 속도가 느려질 수 있다.
