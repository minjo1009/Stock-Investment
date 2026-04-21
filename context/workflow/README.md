# Workflow Context Index

## 목적
- 인간과 AI가 동일한 순서와 규칙으로 작업하도록 표준 흐름을 고정한다.
- 문서 변경을 포함한 모든 변경을 거버넌스 안에서 관리한다.

## 포함할 문서 유형
- 표준 작업 흐름(Clarify -> Context Gather -> Plan -> Taskize -> Implement -> Test -> Report)
- phase/task 기반 운영 규칙
- 작업 전 필독 문서 순서
- 변경관리 규칙(고위험 문서 수정, 무규칙 수정 금지, silent refactor 금지)
- STOP 규칙과 재개 조건

## 상세 실행 문서
- 실행 규칙: `context/workflow/execution-rules.md`
- 상태 관리: `context/workflow/state-management.md`

## 작성/관리 규칙
- 작업 순서와 승인 경계를 구체적으로 명시한다.
- “예외 처리”는 문서화된 경우만 허용한다.
- 실제 실행 과정에서 발견된 워크플로 리스크를 분리 기록한다.

## 연계
- 상위 인덱스: `context/README.md`
- 관련 분류: `skills/skill.md`, `phases/*.md`, `tasks/*.md`
