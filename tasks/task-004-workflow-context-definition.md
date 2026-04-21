# Task 004: Workflow Context Definition

## Purpose
- 표준 작업 흐름과 변경관리 원칙을 workflow context로 정리한다.

## Background
- 동일 요청이라도 작업 순서와 승인 경계가 다르면 결과 품질이 흔들린다.
- 문서 변경도 거버넌스 안에서 관리되어야 silent refactor를 방지할 수 있다.

## In Scope
- Clarify -> Context Gather -> Plan -> Taskize -> Implement -> Test -> Report 흐름 정의
- phase/task 기반 운영 규칙 정의
- 작업 전 필독 문서 순서 정의
- 고위험 문서 수정 시 Task 필수 원칙 정의
- STOP 규칙 정의

## Out of Scope
- CI/CD 파이프라인 구현
- 협업 툴 연동 구현
- 자동화 스크립트 구현

## Inputs
- `skills/skill.md`
- `prompts/task-create.md`
- `prompts/phase-create.md`
- `phases/phase-00-project-operating-system.md`
- `context/workflow/README.md`

## Outputs
- `context/workflow/README.md` 갱신
- 작업 순서/변경관리/STOP 규칙 인덱스 확정

## Target Files
- `context/workflow/README.md`

## Dependencies
- 선행: Phase 00 규칙 이해
- 후행 연계: Task 005

## Implementation Notes
- AI와 인간이 동일하게 해석 가능한 문장을 사용한다.
- 임의 수정 금지 이유와 승인 경계를 명확히 쓴다.
- 문서 변경도 Task 체계 안에 들어온다는 점을 분명히 한다.

## Acceptance Criteria
- 새 작업자와 AI가 같은 순서로 작업을 시작할 수 있다.
- 임의 수정 금지와 STOP 규칙이 명확히 드러난다.
- 문서 변경 거버넌스가 분리 없이 기록된다.

## Tests
- 본 문서만 읽고 작업 시작 순서와 중단 조건을 설명할 수 있다.
- 고위험 문서 변경 요청 시 Task 선행 필요 여부를 즉시 판단할 수 있다.

## Risks
- 흐름 정의가 추상적이면 실행 단계에서 해석 편차가 커진다.
- STOP 규칙 누락 시 무규칙 수정이 재발한다.
