# Task 014: Sub-Agent Handoff Template

## Purpose
- 단계별 sub-agent가 동일 형식으로 artifact를 작성하도록 handoff 템플릿을 정의한다.

## Background
- 동일 단계라도 작성자마다 산출물 형식이 달라지면 다음 단계 품질이 흔들린다.
- handoff 템플릿은 실행 표준과 리뷰 표준을 동시에 고정하는 역할을 가진다.

## In Scope
- Clarify/Context Gather/Plan/Generate/Evaluate 템플릿 섹션 정의
- 단계별 필수 필드(입력, 관찰, 판정, 다음 단계 입력) 정의
- blocked 상황 템플릿 정의

## Out of Scope
- multi-agent 오케스트레이터 코드 구현
- 템플릿 자동 렌더러 구현

## Inputs
- `skills/skill.md`
- `context/workflow/execution-rules.md`
- `tasks/task-013-artifact-layout-convention.md`

## Outputs
- 단계별 handoff 템플릿 초안
- blocked handoff 예시

## Target Files
- `templates/`
- 필요 시 `context/workflow/README.md`

## Dependencies
- 선행: Task 013(artifact 레이아웃)
- 후행 연계: Task 011, Task 012

## Implementation Notes
- 템플릿은 자유서술보다 체크 가능한 필드 중심으로 구성한다.
- 사실(Facts)과 판단(Assessment) 항목을 분리한다.
- 다음 단계 입력 섹션을 필수로 둔다.

## Acceptance Criteria
- 모든 단계가 동일한 최소 필드 집합을 가진다.
- 다음 단계 sub-agent가 추가 질의 없이 artifact를 해석할 수 있다.
- blocked 시 필요한 복구 행동이 명시된다.

## Tests
- 샘플 task에 템플릿을 적용했을 때 단계 누락 없이 handoff가 완료된다.
- Evaluate artifact만 보고 done/blocked 판정을 재현할 수 있다.

## Risks
- 템플릿이 과도하게 길면 실제 사용성이 저하될 수 있다.
